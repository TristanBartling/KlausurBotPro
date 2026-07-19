"""Defensive trust boundary for shared transfer-function preparation."""

from __future__ import annotations

from typing import NoReturn

from klausurbotpro.application._transfer_function_preparation_steps import (
    parse_request,
    raw_factory_for,
)
from klausurbotpro.application._workflow_diagnostics import (
    failure_code_for_diagnostics,
)
from klausurbotpro.application._workflow_validation import validate_request
from klausurbotpro.application.transfer_function_preparation_contracts import (
    PREPARATION_STAGE_ORDER,
    TransferFunctionPreparationResult,
    TransferFunctionPreparationStage,
    TransferFunctionPreparationStageRecord,
    TransferFunctionPreparationStageStatus,
    TransferFunctionPreparationStatus,
)
from klausurbotpro.application.transfer_function_workflow_contracts import (
    TransferFunctionWorkflowLimits,
    WorkflowDiagnosticCode,
)
from klausurbotpro.domain import (
    CommonTransferFunctionInput,
    Diagnostic,
    DiagnosticCode,
    DiagnosticSeverity,
    RawAlgebraicExpression,
    RawTransferFunction,
    RawTransferFunctionCreationResult,
    ReducedTransferFunction,
    SeparatedTransferFunctionInput,
    TransferFunctionDomainExclusion,
    TransferFunctionInput,
    TransferFunctionPrerequisite,
    TransferFunctionReducer,
    TransferFunctionReductionReport,
    TransferFunctionReductionResult,
    TransferFunctionReductionStep,
)

_NESTED_ERRORS = (AttributeError, AssertionError, IndexError, TypeError, ValueError)
_MISSING_FAILURE_CODES = {
    WorkflowDiagnosticCode.WORKFLOW_LIMIT_EXCEEDED.value,
    WorkflowDiagnosticCode.WORKFLOW_RESOURCE_LIMIT_EXCEEDED.value,
}
_STAGE_FAILURE_CODE = {
    TransferFunctionPreparationStage.PARSE: (
        WorkflowDiagnosticCode.WORKFLOW_PARSE_FAILED
    ),
    TransferFunctionPreparationStage.RAW_TRANSFER_FUNCTION: (
        WorkflowDiagnosticCode.WORKFLOW_RAW_FAILED
    ),
    TransferFunctionPreparationStage.REDUCTION: (
        WorkflowDiagnosticCode.WORKFLOW_REDUCTION_FAILED
    ),
}


class TransferFunctionPreparationFailure(ValueError):
    """A preparation result violates its defensive contract."""


def validate_transfer_function_preparation_result(
    result: TransferFunctionPreparationResult,
    limits: TransferFunctionWorkflowLimits,
) -> None:
    if type(result) is not TransferFunctionPreparationResult:
        raise TypeError("result must be TransferFunctionPreparationResult.")
    if type(limits) is not TransferFunctionWorkflowLimits:
        raise TypeError("limits must be TransferFunctionWorkflowLimits.")
    try:
        _validate_result(result, limits)
    except TransferFunctionPreparationFailure:
        raise
    except _NESTED_ERRORS as error:
        raise TransferFunctionPreparationFailure(
            f"Manipulated preparation result: {type(error).__name__}."
        ) from error


def _validate_result(
    result: TransferFunctionPreparationResult,
    limits: TransferFunctionWorkflowLimits,
) -> None:
    result._validate_local()
    records = result.stage_records
    if len(records) != len(PREPARATION_STAGE_ORDER):
        _fail("Preparation requires exactly three stage records.")
    for record in records:
        _validate_record(record)
    _validate_stage_chain(records)
    expected_diagnostics = tuple(
        diagnostic
        for record in records
        for diagnostic in record.diagnostics
    )
    if result.diagnostics != expected_diagnostics:
        _fail("Preparation diagnostics are not the fixed-order aggregation.")
    if len(result.diagnostics) > limits.max_aggregated_diagnostics:
        _fail("Preparation diagnostics exceed their workflow limit.")
    request_errors = validate_request(result.request, limits)
    if request_errors:
        _validate_invalid_request_result(result, request_errors)
        return

    parsed = _validate_parse_stage(result, limits)
    raw = _validate_raw_stage(result, parsed, limits)
    reduced = _validate_reduction_stage(result, raw, limits)
    expected_status = _derive_status(records)
    if result.status is not expected_status:
        _fail("Preparation status does not match its stage results.")
    if (
        result.status is TransferFunctionPreparationStatus.COMPLETE
        and (
            reduced is None
            or any(
                item.severity is DiagnosticSeverity.ERROR
                for item in result.diagnostics
            )
        )
    ):
        _fail("A complete preparation requires a reduced value without errors.")


def _validate_record(record: TransferFunctionPreparationStageRecord) -> None:
    if type(record) is not TransferFunctionPreparationStageRecord:
        _fail("A preparation stage record has an invalid type.")
    if (
        type(record.stage) is not TransferFunctionPreparationStage
        or type(record.status) is not TransferFunctionPreparationStageStatus
        or type(record.diagnostics) is not tuple
        or any(type(item) is not Diagnostic for item in record.diagnostics)
    ):
        _fail("A preparation stage record is structurally invalid.")
    for diagnostic in record.diagnostics:
        _validate_diagnostic(diagnostic)
    has_error = any(
        item.severity is DiagnosticSeverity.ERROR
        for item in record.diagnostics
    )
    if record.status is TransferFunctionPreparationStageStatus.SUCCEEDED:
        if has_error:
            _fail("A successful preparation stage cannot contain an error.")
    elif record.status is TransferFunctionPreparationStageStatus.FAILED:
        if not has_error:
            _fail("A failed preparation stage requires an error.")
    elif record.diagnostics:
        _fail("A blocked preparation stage cannot contain diagnostics.")


def _validate_diagnostic(diagnostic: Diagnostic) -> None:
    if (
        type(diagnostic.severity) is not DiagnosticSeverity
        or type(diagnostic.code) not in (
            DiagnosticCode,
            WorkflowDiagnosticCode,
        )
        or type(diagnostic.message) is not str
        or not diagnostic.message.strip()
        or (
            diagnostic.field is not None
            and type(diagnostic.field) is not str
        )
        or type(diagnostic.technical_details) is not tuple
        or any(
            type(detail) is not tuple
            or len(detail) != 2
            or any(type(value) is not str for value in detail)
            for detail in diagnostic.technical_details
        )
    ):
        _fail("A preparation diagnostic is structurally invalid.")


def _validate_stage_chain(
    records: tuple[TransferFunctionPreparationStageRecord, ...],
) -> None:
    failed_seen = False
    for record in records:
        if failed_seen:
            if (
                record.status
                is not TransferFunctionPreparationStageStatus.BLOCKED
                or record.diagnostics
            ):
                _fail("Every stage after a failure must be empty and blocked.")
            continue
        if record.status is TransferFunctionPreparationStageStatus.BLOCKED:
            _fail("A blocked stage requires an earlier failure.")
        if record.status is TransferFunctionPreparationStageStatus.FAILED:
            failed_seen = True


def _validate_invalid_request_result(
    result: TransferFunctionPreparationResult,
    request_errors: tuple[tuple[str, str], ...],
) -> None:
    records = result.stage_records
    if (
        result.status is not TransferFunctionPreparationStatus.FAILED
        or result.parsed_input is not None
        or result.raw_result is not None
        or result.reduction_result is not None
        or records[0].status
        is not TransferFunctionPreparationStageStatus.FAILED
        or not _has_application_code(
            records[0],
            WorkflowDiagnosticCode.WORKFLOW_INVALID_REQUEST,
        )
        or records[0].diagnostics[0].technical_details != request_errors
    ):
        _fail("An invalid request requires a value-free failed preparation.")


def _validate_parse_stage(
    result: TransferFunctionPreparationResult,
    limits: TransferFunctionWorkflowLimits,
) -> TransferFunctionInput | None:
    record = result.stage_records[0]
    parsed = result.parsed_input
    if record.status is TransferFunctionPreparationStageStatus.FAILED:
        if parsed is not None:
            _fail("A failed parse stage cannot retain a parsed value.")
        if _is_missing_result_failure(record):
            return None
        expected = parse_request(result.request, limits)
        if not expected.succeeded:
            _validate_failure_diagnostics(record, expected.diagnostics)
        else:
            _fail("A failed parse stage cannot be independently reproduced.")
        return None
    if record.status is not TransferFunctionPreparationStageStatus.SUCCEEDED:
        if parsed is not None:
            _fail("An unavailable parse stage cannot retain a value.")
        return None
    expected = parse_request(result.request, limits)
    if (
        not expected.succeeded
        or expected.value is None
        or type(parsed) not in (
            CommonTransferFunctionInput,
            SeparatedTransferFunctionInput,
        )
        or record.diagnostics != expected.diagnostics
    ):
        _fail("The parsed input cannot be independently reproduced.")
    assert parsed is not None
    if not _strict_input_matches(parsed, expected.value):
        _fail("The parsed input provenance cannot be independently reproduced.")
    return parsed


def _validate_raw_stage(
    result: TransferFunctionPreparationResult,
    parsed: TransferFunctionInput | None,
    limits: TransferFunctionWorkflowLimits,
) -> RawTransferFunction | None:
    record = result.stage_records[1]
    raw_result = result.raw_result
    if record.status is TransferFunctionPreparationStageStatus.BLOCKED:
        if raw_result is not None:
            _fail("A blocked raw stage cannot retain a result.")
        return None
    if parsed is None:
        _fail("A raw stage requires a successful parse stage.")
    if raw_result is None:
        if not _is_missing_result_failure(record):
            _fail("A missing raw result requires a resource or limit failure.")
        return None
    expected = raw_factory_for(result.request, limits).create(
        parsed,
        field=result.request.field,
    )
    if not _strict_raw_result_matches(raw_result, expected, parsed):
        _fail("The raw result cannot be independently reproduced.")
    if record.status is TransferFunctionPreparationStageStatus.FAILED:
        if raw_result.succeeded:
            _fail("A failed raw stage cannot contain a value.")
        _validate_failure_diagnostics(record, raw_result.diagnostics)
        return None
    if (
        record.status is not TransferFunctionPreparationStageStatus.SUCCEEDED
        or not raw_result.succeeded
        or type(raw_result.value) is not RawTransferFunction
        or record.diagnostics != raw_result.diagnostics
    ):
        _fail("The successful raw stage is inconsistent.")
    return raw_result.value


def _validate_reduction_stage(
    result: TransferFunctionPreparationResult,
    raw: RawTransferFunction | None,
    limits: TransferFunctionWorkflowLimits,
) -> ReducedTransferFunction | None:
    record = result.stage_records[2]
    reduction = result.reduction_result
    if record.status is TransferFunctionPreparationStageStatus.BLOCKED:
        if reduction is not None:
            _fail("A blocked reduction stage cannot retain a result.")
        return None
    if raw is None:
        _fail("A reduction stage requires a successful raw stage.")
    if reduction is None:
        if not _is_missing_result_failure(record):
            _fail("A missing reduction result requires a resource or limit failure.")
        return None
    expected = TransferFunctionReducer(limits.reduction).reduce(
        raw,
        field=result.request.field,
    )
    if not _strict_reduction_result_matches(reduction, expected, raw):
        _fail("The reduction result has a foreign or irreproducible raw value.")
    if record.status is TransferFunctionPreparationStageStatus.FAILED:
        if reduction.succeeded:
            _fail("A failed reduction stage cannot contain a value.")
        _validate_failure_diagnostics(record, reduction.diagnostics)
        return None
    if (
        record.status is not TransferFunctionPreparationStageStatus.SUCCEEDED
        or not reduction.succeeded
        or type(reduction.reduced) is not ReducedTransferFunction
        or record.diagnostics != reduction.diagnostics
    ):
        _fail("The successful reduction stage is inconsistent.")
    return reduction.reduced


def _strict_input_matches(
    actual: TransferFunctionInput,
    expected: TransferFunctionInput,
) -> bool:
    if type(actual) is not type(expected):
        return False
    if (
        type(actual.variable_name) is not str
        or actual.variable_name != expected.variable_name
        or type(actual.allowed_symbol_names) is not frozenset
        or actual.allowed_symbol_names != expected.allowed_symbol_names
        or actual.used_symbol_names != expected.used_symbol_names
    ):
        return False
    if (
        type(actual) is CommonTransferFunctionInput
        and type(expected) is CommonTransferFunctionInput
    ):
        return (
            type(actual.original_text) is str
            and actual.original_text == expected.original_text
            and type(actual.normalized_text) is str
            and actual.normalized_text == expected.normalized_text
            and _strict_expression_matches(
                actual.expression,
                expected.expression,
            )
        )
    if (
        type(actual) is SeparatedTransferFunctionInput
        and type(expected) is SeparatedTransferFunctionInput
    ):
        return (
            type(actual.original_numerator_text) is str
            and actual.original_numerator_text
            == expected.original_numerator_text
            and type(actual.original_denominator_text) is str
            and actual.original_denominator_text
            == expected.original_denominator_text
            and type(actual.normalized_numerator_text) is str
            and actual.normalized_numerator_text
            == expected.normalized_numerator_text
            and type(actual.normalized_denominator_text) is str
            and actual.normalized_denominator_text
            == expected.normalized_denominator_text
            and _strict_expression_matches(
                actual.numerator,
                expected.numerator,
            )
            and _strict_expression_matches(
                actual.denominator,
                expected.denominator,
            )
        )
    return False


def _strict_expression_matches(
    actual: RawAlgebraicExpression,
    expected: RawAlgebraicExpression,
) -> bool:
    return (
        type(actual) is type(expected)
        and actual == expected
        and actual.canonical_tree == expected.canonical_tree
        and actual.symbol_names == expected.symbol_names
        and actual.node_count == expected.node_count
        and actual.depth == expected.depth
    )


def _strict_raw_result_matches(
    actual: RawTransferFunctionCreationResult,
    expected: RawTransferFunctionCreationResult,
    parsed: TransferFunctionInput,
) -> bool:
    if (
        type(actual) is not RawTransferFunctionCreationResult
        or type(expected) is not RawTransferFunctionCreationResult
        or actual.diagnostics != expected.diagnostics
    ):
        return False
    if expected.value is None:
        return actual.value is None
    return (
        actual.value is not None
        and actual.value.input_snapshot is parsed
        and _strict_raw_matches(actual.value, expected.value)
    )


def _strict_raw_matches(
    actual: RawTransferFunction,
    expected: RawTransferFunction,
) -> bool:
    return (
        type(actual) is RawTransferFunction
        and type(expected) is RawTransferFunction
        and type(actual.variable_name) is str
        and actual.variable_name == expected.variable_name
        and actual.numerator == expected.numerator
        and actual.denominator == expected.denominator
        and type(actual.used_parameter_names) is frozenset
        and actual.used_parameter_names == expected.used_parameter_names
        and _strict_input_matches(
            actual.input_snapshot,
            expected.input_snapshot,
        )
        and _strict_prerequisites_match(
            actual.prerequisites,
            expected.prerequisites,
        )
        and _strict_domain_exclusions_match(
            actual.domain_exclusions,
            expected.domain_exclusions,
        )
        and actual.numerator_conditions == expected.numerator_conditions
        and actual.denominator_conditions == expected.denominator_conditions
        and type(actual.is_zero) is bool
        and actual.is_zero is expected.is_zero
    )


def _strict_prerequisites_match(
    actual: tuple[TransferFunctionPrerequisite, ...],
    expected: tuple[TransferFunctionPrerequisite, ...],
) -> bool:
    return (
        type(actual) is tuple
        and len(actual) == len(expected)
        and all(
            type(left) is TransferFunctionPrerequisite
            and left.kind is right.kind
            and left.expressions == right.expressions
            and type(left.origins) is tuple
            and left.origins == right.origins
            for left, right in zip(actual, expected, strict=True)
        )
    )


def _strict_domain_exclusions_match(
    actual: tuple[TransferFunctionDomainExclusion, ...],
    expected: tuple[TransferFunctionDomainExclusion, ...],
) -> bool:
    return (
        type(actual) is tuple
        and len(actual) == len(expected)
        and all(
            type(left) is TransferFunctionDomainExclusion
            and left.polynomial == right.polynomial
            and type(left.origins) is tuple
            and left.origins == right.origins
            for left, right in zip(actual, expected, strict=True)
        )
    )


def _strict_reduction_result_matches(
    actual: TransferFunctionReductionResult,
    expected: TransferFunctionReductionResult,
    raw: RawTransferFunction,
) -> bool:
    if (
        type(actual) is not TransferFunctionReductionResult
        or type(expected) is not TransferFunctionReductionResult
        or actual.raw is not raw
        or expected.raw is not raw
        or actual.diagnostics != expected.diagnostics
    ):
        return False
    if expected.reduced is None or expected.report is None:
        return actual.reduced is None and actual.report is None
    return (
        actual.reduced is not None
        and actual.report is not None
        and _strict_reduced_matches(actual.reduced, expected.reduced)
        and _strict_reduction_report_matches(
            actual.report,
            expected.report,
        )
    )


def _strict_reduced_matches(
    actual: ReducedTransferFunction,
    expected: ReducedTransferFunction,
) -> bool:
    return (
        type(actual) is ReducedTransferFunction
        and type(expected) is ReducedTransferFunction
        and type(actual.variable_name) is str
        and actual.variable_name == expected.variable_name
        and actual.numerator == expected.numerator
        and actual.denominator == expected.denominator
        and _strict_prerequisites_match(
            actual.prerequisites,
            expected.prerequisites,
        )
        and _strict_domain_exclusions_match(
            actual.domain_exclusions,
            expected.domain_exclusions,
        )
        and type(actual.used_parameter_names) is frozenset
        and actual.used_parameter_names == expected.used_parameter_names
        and type(actual.is_zero) is bool
        and actual.is_zero is expected.is_zero
    )


def _strict_reduction_report_matches(
    actual: TransferFunctionReductionReport,
    expected: TransferFunctionReductionReport,
) -> bool:
    return (
        type(actual) is TransferFunctionReductionReport
        and type(actual.steps) is tuple
        and len(actual.steps) == len(expected.steps)
        and all(
            _strict_reduction_step_matches(left, right)
            for left, right in zip(
                actual.steps,
                expected.steps,
                strict=True,
            )
        )
    )


def _strict_reduction_step_matches(
    actual: TransferFunctionReductionStep,
    expected: TransferFunctionReductionStep,
) -> bool:
    return (
        type(actual) is TransferFunctionReductionStep
        and actual.kind is expected.kind
        and actual.numerator_before == expected.numerator_before
        and actual.denominator_before == expected.denominator_before
        and actual.numerator_after == expected.numerator_after
        and actual.denominator_after == expected.denominator_after
        and actual.factor == expected.factor
        and _strict_prerequisites_match(
            actual.prerequisites_used,
            expected.prerequisites_used,
        )
    )


def _validate_failure_diagnostics(
    record: TransferFunctionPreparationStageRecord,
    source_diagnostics: tuple[Diagnostic, ...],
) -> None:
    if (
        record.diagnostics[: len(source_diagnostics)] != source_diagnostics
        or len(record.diagnostics) != len(source_diagnostics) + 1
        or record.diagnostics[-1].severity is not DiagnosticSeverity.ERROR
        or record.diagnostics[-1].code.value
        != failure_code_for_diagnostics(
            source_diagnostics,
            _STAGE_FAILURE_CODE[record.stage],
        ).value
    ):
        _fail("A failed stage does not preserve source diagnostics.")


def _is_missing_result_failure(
    record: TransferFunctionPreparationStageRecord,
) -> bool:
    return (
        record.status is TransferFunctionPreparationStageStatus.FAILED
        and len(record.diagnostics) == 1
        and record.diagnostics[0].severity is DiagnosticSeverity.ERROR
        and record.diagnostics[0].code.value in _MISSING_FAILURE_CODES
    )


def _has_application_code(
    record: TransferFunctionPreparationStageRecord,
    code: WorkflowDiagnosticCode,
) -> bool:
    return (
        len(record.diagnostics) == 1
        and record.diagnostics[0].severity is DiagnosticSeverity.ERROR
        and record.diagnostics[0].code.value == code.value
    )


def _derive_status(
    records: tuple[TransferFunctionPreparationStageRecord, ...],
) -> TransferFunctionPreparationStatus:
    if all(
        item.status is TransferFunctionPreparationStageStatus.SUCCEEDED
        for item in records
    ):
        return TransferFunctionPreparationStatus.COMPLETE
    if (
        records[0].status
        is TransferFunctionPreparationStageStatus.SUCCEEDED
    ):
        return TransferFunctionPreparationStatus.PARTIAL
    return TransferFunctionPreparationStatus.FAILED


def _fail(message: str) -> NoReturn:
    raise TransferFunctionPreparationFailure(message)


__all__ = [
    "TransferFunctionPreparationFailure",
    "validate_transfer_function_preparation_result",
]
