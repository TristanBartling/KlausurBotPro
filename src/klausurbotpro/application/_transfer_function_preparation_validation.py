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
    RawTransferFunction,
    ReducedTransferFunction,
    SeparatedTransferFunctionInput,
    TransferFunctionInput,
    TransferFunctionReducer,
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
        or expected.value != parsed
        or type(parsed) not in (
            CommonTransferFunctionInput,
            SeparatedTransferFunctionInput,
        )
        or record.diagnostics != expected.diagnostics
    ):
        _fail("The parsed input cannot be independently reproduced.")
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
    if raw_result != expected:
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
    if reduction != expected or reduction.raw is not raw:
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
