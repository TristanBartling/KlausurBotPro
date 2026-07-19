"""Defensive revalidation tests for follow-up workflow operations."""

import pytest

from klausurbotpro.application import (
    OverrideProvenance,
    RawTransferFunctionOverride,
    TransferFunctionWorkflowRequest,
    TransferFunctionWorkflowService,
    TransferFunctionWorkflowState,
    WorkflowDiagnosticCode,
    WorkflowInputForm,
    WorkflowOverrideOriginKind,
    WorkflowStage,
    WorkflowStageRecord,
    WorkflowStageStatus,
)


def _state(
    expression: str = "1/(s+1)",
    *,
    variable_name: str = "s",
) -> TransferFunctionWorkflowState:
    return TransferFunctionWorkflowService().run(
        TransferFunctionWorkflowRequest(
            WorkflowInputForm.COMMON,
            common_expression_text=expression,
            variable_name=variable_name,
        )
    )


def _assert_structured_invalid_state(
    state: TransferFunctionWorkflowState,
) -> None:
    result = TransferFunctionWorkflowService().update_substitutions(
        state,
        None,
    )

    assert result.parsed_input is None
    assert result.raw_result is None
    assert result.reduction_result is None
    assert result.active_reduced_value is None
    assert result.root_analysis_result is None
    assert result.stability_analysis_result is None
    assert result.stage_records[0].status is WorkflowStageStatus.FAILED
    assert all(
        record.status is WorkflowStageStatus.BLOCKED
        for record in result.stage_records[1:]
    )
    assert WorkflowDiagnosticCode.WORKFLOW_INVALID_STATE.value in {
        entry.diagnostic.code.value
        for entry in result.aggregated_diagnostics
    }


def test_wrong_top_level_state_types_raise_type_error() -> None:
    class StateSubclass(TransferFunctionWorkflowState):
        pass

    service = TransferFunctionWorkflowService()
    valid = _state()
    with pytest.raises(TypeError, match="TransferFunctionWorkflowState"):
        service.update_substitutions(object(), None)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="TransferFunctionWorkflowState"):
        service.apply_override(object(), object())  # type: ignore[arg-type]
    subclass = StateSubclass(
        valid.request,
        valid.substitutions,
        valid.parsed_input,
        valid.raw_result,
        valid.reduction_result,
        valid.root_analysis_result,
        valid.stability_analysis_result,
        valid.stage_records,
        valid.aggregated_diagnostics,
        valid.operation_sequence,
        valid.active_reduced_value,
    )
    with pytest.raises(TypeError, match="TransferFunctionWorkflowState"):
        service.update_substitutions(subclass, None)


@pytest.mark.parametrize(
    "manipulation",
    [
        "request",
        "parsed_input",
        "substitutions",
        "raw_result",
        "foreign_reduction",
        "foreign_active_reduced",
        "foreign_root",
        "foreign_stability",
        "stage_order",
        "succeeded_without_value",
        "blocked_with_result",
        "operation_sequence",
        "diagnostic_aggregation",
    ],
)
def test_manipulated_states_are_rejected_before_follow_up(
    manipulation: str,
) -> None:
    state = _state()
    foreign = _state("1/(s+2)")
    foreign_variable = _state("1/(z+1)", variable_name="z")

    if manipulation == "request":
        object.__setattr__(state, "request", object())
    elif manipulation == "parsed_input":
        object.__setattr__(
            state,
            "parsed_input",
            foreign_variable.parsed_input,
        )
    elif manipulation == "substitutions":
        object.__setattr__(state, "substitutions", object())
    elif manipulation == "raw_result":
        object.__setattr__(state, "raw_result", object())
    elif manipulation == "foreign_reduction":
        object.__setattr__(
            state,
            "reduction_result",
            foreign.reduction_result,
        )
    elif manipulation == "foreign_active_reduced":
        object.__setattr__(
            state,
            "active_reduced_value",
            foreign_variable.reduced_value,
        )
    elif manipulation == "foreign_root":
        object.__setattr__(
            state,
            "root_analysis_result",
            foreign.root_analysis_result,
        )
    elif manipulation == "foreign_stability":
        object.__setattr__(
            state,
            "stability_analysis_result",
            foreign.stability_analysis_result,
        )
    elif manipulation == "stage_order":
        object.__setattr__(
            state,
            "stage_records",
            tuple(reversed(state.stage_records)),
        )
    elif manipulation == "succeeded_without_value":
        object.__setattr__(state, "raw_result", None)
    elif manipulation == "blocked_with_result":
        records = list(state.stage_records)
        records[1] = WorkflowStageRecord(
            WorkflowStage.RAW_TRANSFER_FUNCTION,
            WorkflowStageStatus.BLOCKED,
        )
        object.__setattr__(state, "stage_records", tuple(records))
    elif manipulation == "operation_sequence":
        object.__setattr__(state, "operation_sequence", 1_000_001)
    else:
        object.__setattr__(state, "aggregated_diagnostics", (object(),))

    _assert_structured_invalid_state(state)


def test_apply_override_does_not_use_invalid_state_values() -> None:
    service = TransferFunctionWorkflowService()
    state = _state()
    source = _state("1/(s+2)")
    assert source.raw_value is not None
    object.__setattr__(state, "raw_result", object())
    override = RawTransferFunctionOverride(
        source.raw_value,
        OverrideProvenance(
            WorkflowOverrideOriginKind.TEST,
            "must not be applied",
            1,
            WorkflowStage.RAW_TRANSFER_FUNCTION,
        ),
    )

    result = service.apply_override(state, override)

    assert result.raw_result is None
    assert result.reduced_value is None
    assert WorkflowDiagnosticCode.WORKFLOW_INVALID_STATE.value in {
        entry.diagnostic.code.value
        for entry in result.aggregated_diagnostics
    }


def test_manipulated_provenance_and_diagnostic_entry_are_rejected() -> None:
    service = TransferFunctionWorkflowService()
    base = _state()
    source = _state("1/(s+2)")
    assert source.raw_value is not None
    overridden = service.apply_override(
        base,
        RawTransferFunctionOverride(
            source.raw_value,
            OverrideProvenance(
                WorkflowOverrideOriginKind.TEST,
                "valid",
                1,
                WorkflowStage.RAW_TRANSFER_FUNCTION,
            ),
        ),
    )
    provenance = overridden.stage_records[1].override_provenance
    assert provenance is not None
    object.__setattr__(provenance, "reason", object())
    _assert_structured_invalid_state(overridden)

    state = _state("1/(T*s+1)")
    assert state.aggregated_diagnostics
    entry = state.aggregated_diagnostics[0]
    object.__setattr__(entry, "local_index", True)
    _assert_structured_invalid_state(state)
