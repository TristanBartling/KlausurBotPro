"""End-to-end acceptance tests for normal workflow execution."""

from klausurbotpro.application import (
    TransferFunctionWorkflowRequest,
    TransferFunctionWorkflowService,
    WorkflowDiagnosticCode,
    WorkflowInputForm,
    WorkflowStageStatus,
)
from klausurbotpro.domain import (
    ExactRationalValue,
    ParameterAssignment,
    ParameterSubstitutions,
    PolynomialRootStatus,
    StabilityStatus,
)


def _common(
    text: str,
    *,
    parameters: tuple[str, ...] = (),
    substitutions: ParameterSubstitutions | None = None,
) -> TransferFunctionWorkflowRequest:
    return TransferFunctionWorkflowRequest(
        WorkflowInputForm.COMMON,
        common_expression_text=text,
        allowed_parameter_names=parameters,
        substitutions=substitutions,
        field="transfer_function",
    )


def test_common_and_separated_forms_reach_same_end_value() -> None:
    service = TransferFunctionWorkflowService()
    common = service.run(_common("(s+1)/(s^2+3*s+2)"))
    separated = service.run(
        TransferFunctionWorkflowRequest(
            WorkflowInputForm.SEPARATED,
            numerator_expression_text="s+1",
            denominator_expression_text="s^2+3*s+2",
        )
    )

    assert common.reduced_value == separated.reduced_value
    assert common.root_analysis_result is not None
    assert separated.root_analysis_result is not None
    assert common.root_analysis_result.reduced_zeros == (
        separated.root_analysis_result.reduced_zeros
    )
    assert common.root_analysis_result.reduced_poles == (
        separated.root_analysis_result.reduced_poles
    )
    assert common.stability_analysis_result is not None
    assert separated.stability_analysis_result is not None
    assert common.stability_analysis_result.status is StabilityStatus.STABLE
    assert separated.stability_analysis_result.status is StabilityStatus.STABLE


def test_parameter_without_assignment_is_successfully_undetermined() -> None:
    state = TransferFunctionWorkflowService().run(
        _common("1/(T*s+1)", parameters=("T",))
    )

    assert all(
        record.status is WorkflowStageStatus.SUCCEEDED
        for record in state.stage_records
    )
    assert state.root_analysis_result is not None
    assert state.root_analysis_result.reduced_poles is not None
    assert state.root_analysis_result.reduced_poles.status is (
        PolynomialRootStatus.SYMBOLIC_UNDETERMINED
    )
    assert state.stability_analysis_result is not None
    assert state.stability_analysis_result.status is (
        StabilityStatus.SYMBOLIC_UNDETERMINED
    )


def test_parameter_assignment_is_exact_and_stable() -> None:
    substitutions = ParameterSubstitutions(
        (ParameterAssignment("T", ExactRationalValue(2)),)
    )
    state = TransferFunctionWorkflowService().run(
        _common(
            "1/(T*s+1)",
            parameters=("T",),
            substitutions=substitutions,
        )
    )

    assert state.root_analysis_result is not None
    assert state.root_analysis_result.reduced_poles is not None
    pole = state.root_analysis_result.reduced_poles.roots[0]
    assert pole.value.expression.canonical_text == "-1/2"  # type: ignore[union-attr]
    assert state.stability_analysis_result is not None
    assert state.stability_analysis_result.status is StabilityStatus.STABLE


def test_parser_failure_blocks_every_later_stage() -> None:
    state = TransferFunctionWorkflowService().run(_common("open('x')"))

    assert state.stage_records[0].status is WorkflowStageStatus.FAILED
    assert all(
        record.status is WorkflowStageStatus.BLOCKED
        for record in state.stage_records[1:]
    )
    assert state.parsed_input is None
    assert state.raw_result is None
    assert state.aggregated_diagnostics[-1].diagnostic.code.value == (
        WorkflowDiagnosticCode.WORKFLOW_PARSE_FAILED.value
    )


def test_raw_failure_retains_parser_result_and_blocks_later_stages() -> None:
    state = TransferFunctionWorkflowService().run(_common("1/0"))

    assert state.parsed_input is not None
    assert state.raw_result is not None
    assert not state.raw_result.succeeded
    assert state.stage_records[1].status is WorkflowStageStatus.FAILED
    assert all(
        record.status is WorkflowStageStatus.BLOCKED
        for record in state.stage_records[2:]
    )


def test_domain_diagnostics_remain_unchanged_and_ordered() -> None:
    state = TransferFunctionWorkflowService().run(
        _common("1/(T*s+1)", parameters=("T",))
    )
    expected = tuple(
        diagnostic
        for record in state.stage_records
        for diagnostic in record.diagnostics
    )

    assert tuple(
        entry.diagnostic for entry in state.aggregated_diagnostics
    ) == expected
    assert tuple(
        (entry.stage, entry.local_index)
        for entry in state.aggregated_diagnostics
    ) == tuple(
        (record.stage, index)
        for record in state.stage_records
        for index, _ in enumerate(record.diagnostics)
    )
    assert all(
        entry.operation_sequence == state.operation_sequence
        for entry in state.aggregated_diagnostics
    )


def test_equal_runs_are_deterministic() -> None:
    service = TransferFunctionWorkflowService()
    request = _common("(s+1)/(s^2+3*s+2)")

    first = service.run(request)
    second = service.run(request)

    assert first == second
    assert first.operation_sequence == second.operation_sequence == 0
