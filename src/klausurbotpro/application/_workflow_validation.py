"""Validation helpers for workflow requests, substitutions, and overrides."""

from __future__ import annotations

from keyword import iskeyword

from klausurbotpro.application.transfer_function_workflow_contracts import (
    WORKFLOW_STAGE_ORDER,
    OverrideProvenance,
    TransferFunctionWorkflowLimits,
    TransferFunctionWorkflowRequest,
    TransferFunctionWorkflowState,
    WorkflowDiagnosticEntry,
    WorkflowInputForm,
    WorkflowOverrideOriginKind,
    WorkflowStage,
    WorkflowStageRecord,
    WorkflowStageStatus,
    WorkflowValueOrigin,
)
from klausurbotpro.domain import (
    CommonTransferFunctionInput,
    Diagnostic,
    ParameterSubstitutions,
    RawTransferFunction,
    RawTransferFunctionCreationResult,
    RawTransferFunctionFactory,
    ReducedTransferFunction,
    SeparatedTransferFunctionInput,
    TransferFunctionReducer,
    TransferFunctionReductionResult,
    TransferFunctionRootAnalysisResult,
    TransferFunctionRootAnalyzer,
    TransferFunctionStabilityAnalysisResult,
    TransferFunctionStabilityAnalyzer,
)

_RESOURCE_ERRORS = (MemoryError, RecursionError, OverflowError)


def validate_request(
    request: TransferFunctionWorkflowRequest,
    limits: TransferFunctionWorkflowLimits,
) -> tuple[tuple[str, str], ...]:
    errors: list[tuple[str, str]] = []
    if type(request) is not TransferFunctionWorkflowRequest:
        return (("request", "invalid_type"),)
    if type(request.input_form) is not WorkflowInputForm:
        errors.append(("input_form", "invalid"))
    if not _safe_name(request.variable_name):
        errors.append(("variable_name", "invalid"))
    if request.field is not None and type(request.field) is not str:
        errors.append(("field", "invalid"))
    names = request.allowed_parameter_names
    if type(names) is not tuple or any(
        type(name) is not str for name in names
    ):
        errors.append(("allowed_parameter_names", "invalid_type"))
    else:
        if names != tuple(sorted(set(names))):
            errors.append(("allowed_parameter_names", "not_sorted_unique"))
        if any(not _safe_name(name) for name in names):
            errors.append(("allowed_parameter_names", "unsafe_identifier"))
        if request.variable_name in names:
            errors.append(("allowed_parameter_names", "contains_variable"))
        if len(names) > limits.parser.max_symbols - 1:
            errors.append(("allowed_parameter_names", "parser_limit"))
        if len(names) > limits.raw.max_parameters:
            errors.append(("allowed_parameter_names", "raw_limit"))

    common_set = request.common_expression_text is not None
    numerator_set = request.numerator_expression_text is not None
    denominator_set = request.denominator_expression_text is not None
    if request.input_form is WorkflowInputForm.COMMON:
        if not common_set or numerator_set or denominator_set:
            errors.append(("input_form", "common_fields_mismatch"))
    elif (
        request.input_form is WorkflowInputForm.SEPARATED
        and (common_set or not numerator_set or not denominator_set)
    ):
        errors.append(("input_form", "separated_fields_mismatch"))
    for name, value in (
        ("common_expression_text", request.common_expression_text),
        ("numerator_expression_text", request.numerator_expression_text),
        ("denominator_expression_text", request.denominator_expression_text),
    ):
        if value is not None and type(value) is not str:
            errors.append((name, "invalid_type"))
    if request.substitutions is not None and (
        type(request.substitutions) is not ParameterSubstitutions
    ):
        errors.append(("substitutions", "invalid_type"))
    return tuple(errors)


def validate_provenance(
    provenance: OverrideProvenance,
    *,
    expected_stage: WorkflowStage,
    expected_sequence: int,
    limits: TransferFunctionWorkflowLimits,
) -> tuple[tuple[str, str], ...]:
    errors: list[tuple[str, str]] = []
    if type(provenance) is not OverrideProvenance:
        return (("provenance", "invalid_type"),)
    if provenance.target_stage is not expected_stage:
        errors.append(("target_stage", "mismatch"))
    if type(provenance.origin_kind) is not WorkflowOverrideOriginKind:
        errors.append(("origin_kind", "invalid"))
    if (
        isinstance(provenance.sequence_number, bool)
        or provenance.sequence_number != expected_sequence
    ):
        errors.append(("sequence_number", "mismatch"))
    if type(provenance.reason) is not str or not provenance.reason.strip():
        errors.append(("reason", "empty_or_invalid"))
    elif len(provenance.reason) > limits.max_override_reason_length:
        errors.append(("reason", "max_override_reason_length"))
    return tuple(errors)


def next_sequence(
    current: int,
    limits: TransferFunctionWorkflowLimits,
) -> int | None:
    value = current + 1
    return value if value <= limits.max_operation_sequence else None


def validate_workflow_state(
    state: TransferFunctionWorkflowState,
    limits: TransferFunctionWorkflowLimits,
) -> tuple[tuple[str, str], ...]:
    """Defensively revalidate a state before any follow-up computation."""

    if type(state) is not TransferFunctionWorkflowState:
        raise TypeError("state must be a TransferFunctionWorkflowState.")
    try:
        return _validate_workflow_state(state, limits)
    except _RESOURCE_ERRORS as error:
        return (("state", f"resource_error:{type(error).__name__}"),)
    except (AttributeError, AssertionError, IndexError, TypeError, ValueError) as error:
        return (("state", f"invalid_structure:{type(error).__name__}"),)


def _validate_workflow_state(
    state: TransferFunctionWorkflowState,
    limits: TransferFunctionWorkflowLimits,
) -> tuple[tuple[str, str], ...]:
    errors: list[tuple[str, str]] = []
    request = state.request
    if type(request) is not TransferFunctionWorkflowRequest:
        return (("request", "invalid_type"),)
    request_errors = validate_request(request, limits)
    if request_errors:
        errors.extend(
            (f"request.{name}", reason) for name, reason in request_errors
        )

    sequence = state.operation_sequence
    if (
        type(sequence) is not int
        or sequence < 0
        or sequence > limits.max_operation_sequence
    ):
        errors.append(("operation_sequence", "invalid"))
    if state.substitutions is not None and (
        type(state.substitutions) is not ParameterSubstitutions
    ):
        errors.append(("substitutions", "invalid_type"))

    records = state.stage_records
    if type(records) is not tuple:
        errors.append(("stage_records", "invalid_type"))
        return tuple(errors)
    if len(records) != len(WORKFLOW_STAGE_ORDER):
        errors.append(("stage_records", "invalid_length"))
        return tuple(errors)
    for index, record in enumerate(records):
        errors.extend(_validate_stage_record(record, index, state, limits))
    if any(
        type(record) is not WorkflowStageRecord for record in records
    ):
        return tuple(errors)
    if tuple(record.stage for record in records) != WORKFLOW_STAGE_ORDER:
        errors.append(("stage_records", "invalid_order"))

    aggregated = state.aggregated_diagnostics
    if type(aggregated) is not tuple:
        errors.append(("aggregated_diagnostics", "invalid_type"))
    elif len(aggregated) > limits.max_aggregated_diagnostics:
        errors.append(("aggregated_diagnostics", "limit_exceeded"))
    elif not _diagnostics_match(records, aggregated, sequence):
        errors.append(("aggregated_diagnostics", "inconsistent"))

    errors.extend(_validate_parsed_input(state))
    if errors:
        return tuple(errors)
    errors.extend(_validate_results(state, limits))
    return tuple(errors)


def _validate_stage_record(
    record: object,
    index: int,
    state: TransferFunctionWorkflowState,
    limits: TransferFunctionWorkflowLimits,
) -> tuple[tuple[str, str], ...]:
    field = f"stage_records[{index}]"
    if type(record) is not WorkflowStageRecord:
        return ((field, "invalid_type"),)
    errors: list[tuple[str, str]] = []
    if type(record.stage) is not WorkflowStage:
        errors.append((field, "invalid_stage"))
    if type(record.status) is not WorkflowStageStatus:
        errors.append((field, "invalid_status"))
    if record.value_origin is not None and (
        type(record.value_origin) is not WorkflowValueOrigin
    ):
        errors.append((field, "invalid_value_origin"))
    if type(record.diagnostics) is not tuple or any(
        type(item) is not Diagnostic for item in record.diagnostics
    ):
        errors.append((field, "invalid_diagnostics"))
    if type(record.diagnostic_provenances) is not tuple or len(
        record.diagnostic_provenances
    ) != len(record.diagnostics):
        errors.append((field, "invalid_diagnostic_provenances"))
    elif any(
        item is not None
        and _validate_override_provenance(
            item,
            state.operation_sequence,
            limits,
            expected_stage=record.stage,
        )
        for item in record.diagnostic_provenances
    ):
        errors.append((field, "invalid_diagnostic_provenance"))

    if record.status is WorkflowStageStatus.SUCCEEDED:
        if record.value_origin is None:
            errors.append((field, "succeeded_without_origin"))
    elif record.value_origin is not None:
        errors.append((field, "unavailable_with_origin"))
    if record.value_origin is WorkflowValueOrigin.OVERRIDDEN:
        if _validate_override_provenance(
            record.override_provenance,
            state.operation_sequence,
            limits,
            expected_stage=record.stage,
        ):
            errors.append((field, "invalid_override_provenance"))
    elif record.override_provenance is not None:
        errors.append((field, "unexpected_override_provenance"))
    return tuple(errors)


def _validate_override_provenance(
    provenance: object,
    operation_sequence: int,
    limits: TransferFunctionWorkflowLimits,
    *,
    expected_stage: object,
) -> bool:
    return (
        type(provenance) is not OverrideProvenance
        or type(provenance.origin_kind) is not WorkflowOverrideOriginKind
        or type(provenance.reason) is not str
        or not provenance.reason.strip()
        or len(provenance.reason) > limits.max_override_reason_length
        or type(provenance.sequence_number) is not int
        or provenance.sequence_number <= 0
        or provenance.sequence_number > operation_sequence
        or type(provenance.target_stage) is not WorkflowStage
        or provenance.target_stage is not expected_stage
    )


def _diagnostics_match(
    records: tuple[WorkflowStageRecord, ...],
    entries: tuple[WorkflowDiagnosticEntry, ...],
    operation_sequence: object,
) -> bool:
    expected = tuple(
        (
            record.stage,
            index,
            diagnostic,
            operation_sequence,
            record.diagnostic_provenances[index],
        )
        for record in records
        for index, diagnostic in enumerate(record.diagnostics)
    )
    actual: list[tuple[object, ...]] = []
    for entry in entries:
        if (
            type(entry) is not WorkflowDiagnosticEntry
            or type(entry.stage) is not WorkflowStage
            or type(entry.local_index) is not int
            or entry.local_index < 0
            or type(entry.diagnostic) is not Diagnostic
            or type(entry.operation_sequence) is not int
            or (
                entry.override_provenance is not None
                and type(entry.override_provenance) is not OverrideProvenance
            )
        ):
            return False
        actual.append(
            (
                entry.stage,
                entry.local_index,
                entry.diagnostic,
                entry.operation_sequence,
                entry.override_provenance,
            )
        )
    return tuple(actual) == expected


def _validate_parsed_input(
    state: TransferFunctionWorkflowState,
) -> tuple[tuple[str, str], ...]:
    parsed = state.parsed_input
    parse_record = state.stage_records[0]
    if parse_record.status is WorkflowStageStatus.SUCCEEDED:
        if type(parsed) not in (
            CommonTransferFunctionInput,
            SeparatedTransferFunctionInput,
        ):
            return (("parsed_input", "missing_or_invalid"),)
    elif parsed is not None:
        return (("parsed_input", "present_for_unavailable_stage"),)
    if parsed is None:
        return ()
    expected_type = (
        CommonTransferFunctionInput
        if state.request.input_form is WorkflowInputForm.COMMON
        else SeparatedTransferFunctionInput
    )
    expected_symbols = frozenset(
        (*state.request.allowed_parameter_names, state.request.variable_name)
    )
    if (
        type(parsed) is not expected_type
        or parsed.variable_name != state.request.variable_name
        or parsed.allowed_symbol_names != expected_symbols
    ):
        return (("parsed_input", "request_context_mismatch"),)
    return ()


def _validate_results(
    state: TransferFunctionWorkflowState,
    limits: TransferFunctionWorkflowLimits,
) -> tuple[tuple[str, str], ...]:
    errors: list[tuple[str, str]] = []
    records = state.stage_records
    raw_record, reduction_record, root_record, stability_record = records[1:]
    raw = _validate_raw_result(state, raw_record, limits, errors)
    reduced = _validate_reduction_result(
        state,
        raw,
        reduction_record,
        limits,
        errors,
    )
    root = _validate_root_result(
        state,
        reduced,
        root_record,
        limits,
        errors,
    )
    _validate_stability_result(
        state,
        root,
        stability_record,
        limits,
        errors,
    )
    _validate_dependencies(state, errors)
    return tuple(errors)


def _validate_raw_result(
    state: TransferFunctionWorkflowState,
    record: WorkflowStageRecord,
    limits: TransferFunctionWorkflowLimits,
    errors: list[tuple[str, str]],
) -> RawTransferFunction | None:
    result = state.raw_result
    if record.status in (
        WorkflowStageStatus.BLOCKED,
        WorkflowStageStatus.NOT_EVALUATED,
    ):
        if result is not None:
            errors.append(("raw_result", "present_for_unavailable_stage"))
        return None
    if result is None:
        if record.status is WorkflowStageStatus.SUCCEEDED:
            errors.append(("raw_result", "missing_for_succeeded_stage"))
        return None
    if type(result) is not RawTransferFunctionCreationResult:
        errors.append(("raw_result", "invalid_type"))
        return None
    if not _record_preserves_diagnostics(record, result.diagnostics):
        errors.append(("raw_result", "diagnostics_mismatch"))
    factory = RawTransferFunctionFactory(
        expected_variable_name=state.request.variable_name,
        allowed_parameter_names=frozenset(
            state.request.allowed_parameter_names
        ),
        limits=limits.raw,
    )
    if record.value_origin is WorkflowValueOrigin.OVERRIDDEN:
        if type(result.value) is not RawTransferFunction:
            errors.append(("raw_result", "invalid_override_value"))
            return None
        expected = factory.create(
            result.value.input_snapshot,
            field=state.request.field,
        )
    elif state.parsed_input is not None:
        expected = factory.create(
            state.parsed_input,
            field=state.request.field,
        )
    else:
        errors.append(("raw_result", "missing_input_context"))
        return None
    if expected != result:
        errors.append(("raw_result", "independent_revalidation_failed"))
    if record.status is WorkflowStageStatus.SUCCEEDED:
        if not result.succeeded or type(result.value) is not RawTransferFunction:
            errors.append(("raw_result", "status_mismatch"))
            return None
        if (
            result.value.variable_name != state.request.variable_name
            or not result.value.used_parameter_names.issubset(
                state.request.allowed_parameter_names
            )
        ):
            errors.append(("raw_result", "request_context_mismatch"))
        return result.value
    if result.succeeded:
        errors.append(("raw_result", "failed_stage_has_value"))
    return None


def _validate_reduction_result(
    state: TransferFunctionWorkflowState,
    raw: RawTransferFunction | None,
    record: WorkflowStageRecord,
    limits: TransferFunctionWorkflowLimits,
    errors: list[tuple[str, str]],
) -> ReducedTransferFunction | None:
    result = state.reduction_result
    active = state.active_reduced_value
    if record.status in (
        WorkflowStageStatus.BLOCKED,
        WorkflowStageStatus.NOT_EVALUATED,
    ):
        if result is not None or active is not None:
            errors.append(("reduction_result", "present_for_unavailable_stage"))
        return None
    if record.value_origin is WorkflowValueOrigin.OVERRIDDEN:
        if result is not None or type(active) is not ReducedTransferFunction:
            errors.append(("active_reduced_value", "invalid_override_shape"))
            return None
        if not _reduced_context_matches(active, state):
            errors.append(("active_reduced_value", "request_context_mismatch"))
            return None
        validation = TransferFunctionRootAnalyzer(
            limits.root_analysis
        ).analyze(active, None, field=state.request.field)
        if not validation.succeeded:
            errors.append(
                ("active_reduced_value", "independent_revalidation_failed")
            )
        return active
    if active is not None:
        errors.append(("active_reduced_value", "unexpected_without_override"))
    if result is None:
        if record.status is WorkflowStageStatus.SUCCEEDED:
            errors.append(("reduction_result", "missing_for_succeeded_stage"))
        return None
    if type(result) is not TransferFunctionReductionResult or raw is None:
        errors.append(("reduction_result", "invalid_type_or_raw_context"))
        return None
    if not _record_preserves_diagnostics(record, result.diagnostics):
        errors.append(("reduction_result", "diagnostics_mismatch"))
    expected = TransferFunctionReducer(limits.reduction).reduce(
        raw,
        field=state.request.field,
    )
    if expected != result:
        errors.append(
            ("reduction_result", "independent_revalidation_failed")
        )
    if result.raw != raw:
        errors.append(("reduction_result", "foreign_raw_value"))
    if record.status is WorkflowStageStatus.SUCCEEDED:
        if not result.succeeded or type(result.reduced) is not ReducedTransferFunction:
            errors.append(("reduction_result", "status_mismatch"))
            return None
        if not _reduced_context_matches(result.reduced, state):
            errors.append(("reduction_result", "request_context_mismatch"))
        return result.reduced
    if result.succeeded:
        errors.append(("reduction_result", "failed_stage_has_value"))
    return None


def _validate_root_result(
    state: TransferFunctionWorkflowState,
    reduced: ReducedTransferFunction | None,
    record: WorkflowStageRecord,
    limits: TransferFunctionWorkflowLimits,
    errors: list[tuple[str, str]],
) -> TransferFunctionRootAnalysisResult | None:
    result = state.root_analysis_result
    if record.status in (
        WorkflowStageStatus.BLOCKED,
        WorkflowStageStatus.NOT_EVALUATED,
    ):
        if result is not None:
            errors.append(
                ("root_analysis_result", "present_for_unavailable_stage")
            )
        return None
    if result is None and _stage_allows_missing_failure_result(record):
        return None
    if result is None or type(result) is not TransferFunctionRootAnalysisResult:
        errors.append(("root_analysis_result", "missing_or_invalid"))
        return None
    if not _record_preserves_diagnostics(record, result.diagnostics):
        errors.append(("root_analysis_result", "diagnostics_mismatch"))
    if reduced is None or result.reduced_transfer_function != reduced:
        errors.append(("root_analysis_result", "foreign_reduced_value"))
        return None
    if not _substitutions_match(result.substitutions, state.substitutions):
        errors.append(("root_analysis_result", "substitution_mismatch"))
    if record.status is WorkflowStageStatus.SUCCEEDED and not result.succeeded:
        errors.append(("root_analysis_result", "status_mismatch"))
    if record.status is WorkflowStageStatus.FAILED and result.succeeded:
        errors.append(("root_analysis_result", "failed_stage_has_value"))
    if record.value_origin is WorkflowValueOrigin.OVERRIDDEN:
        validation = TransferFunctionStabilityAnalyzer(
            limits.stability_analysis
        ).analyze(result, field=state.request.field)
        if not validation.succeeded:
            errors.append(
                ("root_analysis_result", "mathematical_revalidation_failed")
            )
    else:
        analyzer = TransferFunctionRootAnalyzer(limits.root_analysis)
        expected = (
            analyzer.analyze_reduction(
                state.reduction_result,
                state.substitutions,
                field=state.request.field,
            )
            if state.reduction_result is not None
            else analyzer.analyze(
                reduced,
                state.substitutions,
                field=state.request.field,
            )
        )
        if expected != result:
            errors.append(
                ("root_analysis_result", "independent_revalidation_failed")
            )
    return result


def _validate_stability_result(
    state: TransferFunctionWorkflowState,
    root: TransferFunctionRootAnalysisResult | None,
    record: WorkflowStageRecord,
    limits: TransferFunctionWorkflowLimits,
    errors: list[tuple[str, str]],
) -> None:
    result = state.stability_analysis_result
    if record.status in (
        WorkflowStageStatus.BLOCKED,
        WorkflowStageStatus.NOT_EVALUATED,
    ):
        if result is not None:
            errors.append(
                ("stability_analysis_result", "present_for_unavailable_stage")
            )
        return
    if result is None and _stage_allows_missing_failure_result(record):
        return
    if (
        result is None
        or type(result) is not TransferFunctionStabilityAnalysisResult
        or root is None
    ):
        errors.append(("stability_analysis_result", "missing_or_invalid"))
        return
    if not _record_preserves_diagnostics(record, result.diagnostics):
        errors.append(("stability_analysis_result", "diagnostics_mismatch"))
    if result.root_analysis != root:
        errors.append(("stability_analysis_result", "foreign_root_result"))
        return
    expected = TransferFunctionStabilityAnalyzer(
        limits.stability_analysis
    ).analyze(root, field=state.request.field)
    if expected != result:
        errors.append(
            ("stability_analysis_result", "independent_revalidation_failed")
        )
    if record.status is WorkflowStageStatus.SUCCEEDED and not result.succeeded:
        errors.append(("stability_analysis_result", "status_mismatch"))
    if record.status is WorkflowStageStatus.FAILED and result.succeeded:
        errors.append(
            ("stability_analysis_result", "failed_stage_has_value")
        )


def _validate_dependencies(
    state: TransferFunctionWorkflowState,
    errors: list[tuple[str, str]],
) -> None:
    records = state.stage_records
    for index, record in enumerate(records):
        if record.status is WorkflowStageStatus.FAILED and any(
            later.status is not WorkflowStageStatus.BLOCKED
            for later in records[index + 1 :]
        ):
            errors.append(("stage_records", "failure_does_not_block_followers"))
        if record.status is WorkflowStageStatus.BLOCKED and any(
            later.status is not WorkflowStageStatus.BLOCKED
            for later in records[index + 1 :]
        ):
            errors.append(("stage_records", "blocked_chain_is_inconsistent"))
    if state.root_analysis_result is not None and state.reduced_value is None:
        errors.append(("root_analysis_result", "missing_reduced_context"))
    if (
        state.stability_analysis_result is not None
        and state.root_analysis_result is None
    ):
        errors.append(("stability_analysis_result", "missing_root_context"))


def _stage_allows_missing_failure_result(
    record: WorkflowStageRecord,
) -> bool:
    return (
        record.status is WorkflowStageStatus.FAILED
        and any(
            diagnostic.code.value
            in {
                "workflow.limit_exceeded",
                "workflow.resource_limit_exceeded",
                "workflow.invalid_state",
            }
            for diagnostic in record.diagnostics
        )
    )


def _record_preserves_diagnostics(
    record: WorkflowStageRecord,
    diagnostics: object,
) -> bool:
    return (
        type(diagnostics) is tuple
        and record.diagnostics[: len(diagnostics)] == diagnostics
    )


def _reduced_context_matches(
    value: ReducedTransferFunction,
    state: TransferFunctionWorkflowState,
) -> bool:
    return (
        value.variable_name == state.request.variable_name
        and value.used_parameter_names.issubset(
            state.request.allowed_parameter_names
        )
    )


def _substitutions_match(
    first: ParameterSubstitutions | None,
    second: ParameterSubstitutions | None,
) -> bool:
    if first == second:
        return True
    return (
        first is None
        and second is not None
        and second.assignments == ()
    ) or (
        second is None
        and first is not None
        and first.assignments == ()
    )


def _safe_name(value: object) -> bool:
    return (
        type(value) is str
        and value.isidentifier()
        and not iskeyword(value)
        and not value.startswith("__")
        and not value.endswith("__")
    )


__all__ = [
    "next_sequence",
    "validate_provenance",
    "validate_request",
    "validate_workflow_state",
]
