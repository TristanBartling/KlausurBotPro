"""Override provenance, context, and invalidation tests."""

from klausurbotpro.application import (
    OverrideProvenance,
    RawTransferFunctionOverride,
    ReducedTransferFunctionOverride,
    RootAnalysisOverride,
    TransferFunctionWorkflowLimits,
    TransferFunctionWorkflowRequest,
    TransferFunctionWorkflowService,
    WorkflowDiagnosticCode,
    WorkflowInputForm,
    WorkflowOverrideOriginKind,
    WorkflowStage,
    WorkflowStageStatus,
    WorkflowValueOrigin,
)
from klausurbotpro.domain import (
    ExactRationalValue,
    ParameterAssignment,
    ParameterSubstitutions,
    StabilityStatus,
)


def _request(text: str) -> TransferFunctionWorkflowRequest:
    return TransferFunctionWorkflowRequest(
        WorkflowInputForm.COMMON,
        common_expression_text=text,
    )


def _provenance(
    stage: WorkflowStage,
    sequence: int,
) -> OverrideProvenance:
    return OverrideProvenance(
        WorkflowOverrideOriginKind.TEST,
        "controlled test override",
        sequence,
        stage,
    )


def test_raw_override_revalidates_and_recomputes_all_dependents() -> None:
    service = TransferFunctionWorkflowService()
    original = service.run(_request("1/(s+1)"))
    alternate = service.run(_request("1/(s+2)"))
    parsed_before = original.parsed_input
    assert alternate.raw_value is not None

    changed = service.apply_override(
        original,
        RawTransferFunctionOverride(
            alternate.raw_value,
            _provenance(WorkflowStage.RAW_TRANSFER_FUNCTION, 1),
        ),
    )

    assert changed.parsed_input is parsed_before
    assert changed.raw_value == alternate.raw_value
    assert changed.reduced_value == alternate.reduced_value
    assert changed.stage_records[1].value_origin is WorkflowValueOrigin.OVERRIDDEN
    assert changed.stage_records[2].value_origin is WorkflowValueOrigin.COMPUTED
    assert changed.stage_records[3].value_origin is WorkflowValueOrigin.COMPUTED
    assert changed.operation_sequence == 1


def test_reduced_override_is_independent_and_recomputes_roots_and_stability() -> None:
    service = TransferFunctionWorkflowService()
    original = service.run(_request("1/(s+1)"))
    alternate = service.run(_request("1/(s-1)"))
    assert alternate.reduced_value is not None

    changed = service.apply_override(
        original,
        ReducedTransferFunctionOverride(
            alternate.reduced_value,
            _provenance(WorkflowStage.REDUCTION, 1),
        ),
    )

    assert changed.raw_value == original.raw_value
    assert changed.reduction_result is None
    assert changed.reduced_value == alternate.reduced_value
    assert changed.stage_records[2].value_origin is WorkflowValueOrigin.OVERRIDDEN
    assert changed.stage_records[3].value_origin is WorkflowValueOrigin.COMPUTED
    assert changed.stability_analysis_result is not None
    assert changed.stability_analysis_result.status is StabilityStatus.UNSTABLE


def test_root_override_recomputes_only_stability() -> None:
    service = TransferFunctionWorkflowService()
    state = service.run(_request("1/(s+1)"))
    assert state.root_analysis_result is not None

    changed = service.apply_override(
        state,
        RootAnalysisOverride(
            state.root_analysis_result,
            _provenance(WorkflowStage.ROOT_ANALYSIS, 1),
        ),
    )

    assert changed.raw_result is state.raw_result
    assert changed.reduction_result is state.reduction_result
    assert changed.root_analysis_result is state.root_analysis_result
    assert changed.stage_records[3].value_origin is WorkflowValueOrigin.OVERRIDDEN
    assert changed.stage_records[4].value_origin is WorkflowValueOrigin.COMPUTED


def test_root_override_for_other_reduced_value_is_rejected() -> None:
    service = TransferFunctionWorkflowService()
    state = service.run(_request("1/(s+1)"))
    other = service.run(_request("1/(s+2)"))
    assert other.root_analysis_result is not None

    rejected = service.apply_override(
        state,
        RootAnalysisOverride(
            other.root_analysis_result,
            _provenance(WorkflowStage.ROOT_ANALYSIS, 1),
        ),
    )

    assert rejected.root_analysis_result is state.root_analysis_result
    assert rejected.stability_analysis_result is state.stability_analysis_result
    assert rejected.aggregated_diagnostics[-1].diagnostic.code.value == (
        WorkflowDiagnosticCode.WORKFLOW_OVERRIDE_CONTEXT_MISMATCH.value
    )


def test_substitution_update_recomputes_only_roots_and_stability() -> None:
    service = TransferFunctionWorkflowService()
    state = service.run(
        TransferFunctionWorkflowRequest(
            WorkflowInputForm.COMMON,
            common_expression_text="1/(T*s+1)",
            allowed_parameter_names=("T",),
        )
    )
    substitutions = ParameterSubstitutions(
        (ParameterAssignment("T", ExactRationalValue(2)),)
    )

    changed = service.update_substitutions(state, substitutions)

    assert changed.parsed_input is state.parsed_input
    assert changed.raw_result is state.raw_result
    assert changed.reduction_result is state.reduction_result
    assert changed.substitutions == substitutions
    assert changed.stage_records[3].value_origin is WorkflowValueOrigin.COMPUTED
    assert changed.operation_sequence == 1
    assert changed.stability_analysis_result is not None
    assert changed.stability_analysis_result.status is StabilityStatus.STABLE


def test_downstream_override_invalidation_follows_dependency_table() -> None:
    service = TransferFunctionWorkflowService()
    base = service.run(_request("1/(s+1)"))
    raw_source = service.run(_request("1/(s+2)"))
    reduced_source = service.run(_request("1/(s-1)"))
    assert raw_source.raw_value is not None
    assert reduced_source.reduced_value is not None

    with_raw = service.apply_override(
        base,
        RawTransferFunctionOverride(
            raw_source.raw_value,
            _provenance(WorkflowStage.RAW_TRANSFER_FUNCTION, 1),
        ),
    )
    with_reduced = service.apply_override(
        with_raw,
        ReducedTransferFunctionOverride(
            reduced_source.reduced_value,
            _provenance(WorkflowStage.REDUCTION, 2),
        ),
    )
    assert with_reduced.root_analysis_result is not None
    with_root = service.apply_override(
        with_reduced,
        RootAnalysisOverride(
            with_reduced.root_analysis_result,
            _provenance(WorkflowStage.ROOT_ANALYSIS, 3),
        ),
    )
    substitutions_updated = service.update_substitutions(with_root, None)

    assert with_reduced.stage_records[1].value_origin is WorkflowValueOrigin.OVERRIDDEN
    assert with_root.stage_records[1].value_origin is WorkflowValueOrigin.OVERRIDDEN
    assert with_root.stage_records[2].value_origin is WorkflowValueOrigin.OVERRIDDEN
    assert with_root.stage_records[3].value_origin is WorkflowValueOrigin.OVERRIDDEN
    assert substitutions_updated.stage_records[1].value_origin is (
        WorkflowValueOrigin.OVERRIDDEN
    )
    assert substitutions_updated.stage_records[2].value_origin is (
        WorkflowValueOrigin.OVERRIDDEN
    )
    assert substitutions_updated.stage_records[3].value_origin is (
        WorkflowValueOrigin.COMPUTED
    )


def test_invalid_override_preserves_mathematical_state() -> None:
    service = TransferFunctionWorkflowService()
    state = service.run(_request("1/(s+1)"))
    assert state.raw_value is not None
    wrong_sequence = RawTransferFunctionOverride(
        state.raw_value,
        _provenance(WorkflowStage.RAW_TRANSFER_FUNCTION, 99),
    )

    rejected = service.apply_override(state, wrong_sequence)

    assert rejected.raw_result is state.raw_result
    assert rejected.reduction_result is state.reduction_result
    assert rejected.root_analysis_result is state.root_analysis_result
    assert rejected.stability_analysis_result is state.stability_analysis_result
    assert all(
        record.status is WorkflowStageStatus.SUCCEEDED
        for record in rejected.stage_records
    )
    assert rejected.aggregated_diagnostics[-1].diagnostic.code.value == (
        WorkflowDiagnosticCode.WORKFLOW_INVALID_OVERRIDE.value
    )


def test_rejected_override_diagnostic_is_not_attributed_to_active_override() -> None:
    service = TransferFunctionWorkflowService()
    base = service.run(_request("1/(s+1)"))
    source = service.run(_request("1/(s+2)"))
    assert source.raw_value is not None
    active = service.apply_override(
        base,
        RawTransferFunctionOverride(
            source.raw_value,
            _provenance(WorkflowStage.RAW_TRANSFER_FUNCTION, 1),
        ),
    )
    rejected = service.apply_override(
        active,
        RawTransferFunctionOverride(
            source.raw_value,
            _provenance(WorkflowStage.RAW_TRANSFER_FUNCTION, 99),
        ),
    )

    entry = next(
        item
        for item in rejected.aggregated_diagnostics
        if item.diagnostic.code.value
        == WorkflowDiagnosticCode.WORKFLOW_INVALID_OVERRIDE.value
    )
    assert entry.override_provenance is None


def test_override_reason_and_operation_sequence_limits_are_structured() -> None:
    reason_limited = TransferFunctionWorkflowService(
        TransferFunctionWorkflowLimits(max_override_reason_length=3)
    )
    state = reason_limited.run(_request("1/(s+1)"))
    assert state.raw_value is not None
    rejected = reason_limited.apply_override(
        state,
        RawTransferFunctionOverride(
            state.raw_value,
            _provenance(WorkflowStage.RAW_TRANSFER_FUNCTION, 1),
        ),
    )
    assert WorkflowDiagnosticCode.WORKFLOW_INVALID_OVERRIDE.value in {
        item.diagnostic.code.value for item in rejected.aggregated_diagnostics
    }

    sequence_limited = TransferFunctionWorkflowService(
        TransferFunctionWorkflowLimits(max_operation_sequence=1)
    )
    initial = sequence_limited.run(_request("1/(s+1)"))
    first = sequence_limited.update_substitutions(initial, None)
    second = sequence_limited.update_substitutions(first, None)
    assert first.operation_sequence == second.operation_sequence == 1
    assert WorkflowDiagnosticCode.WORKFLOW_LIMIT_EXCEEDED.value in {
        item.diagnostic.code.value for item in second.aggregated_diagnostics
    }
