"""Partial workflow, invalid state, and report-limit acceptance tests."""

from dataclasses import replace

import pytest

from klausurbotpro.application import (
    ReportDiagnosticCode,
    SolutionReportLimits,
    SolutionReportStatus,
    SolutionSectionKind,
    SolutionSectionStatus,
    TransferFunctionSolutionReportBuilder,
    TransferFunctionWorkflowLimits,
    TransferFunctionWorkflowRequest,
    TransferFunctionWorkflowService,
    TransferFunctionWorkflowState,
    WarningLine,
    WorkflowInputForm,
)
from klausurbotpro.domain import (
    DiagnosticSeverity,
    ParameterSubstitutions,
    StabilityAnalysisLimits,
    StabilityStatus,
    TransferFunctionReductionLimits,
)


def _request(expression: str) -> TransferFunctionWorkflowRequest:
    return TransferFunctionWorkflowRequest(
        WorkflowInputForm.COMMON,
        common_expression_text=expression,
    )


def test_parser_failure_produces_failed_report_without_mathematics() -> None:
    state = TransferFunctionWorkflowService().run(_request("open('x')"))
    report = TransferFunctionSolutionReportBuilder().build(state)

    assert report.status is SolutionReportStatus.FAILED
    transfer = report.section(SolutionSectionKind.TRANSFER_FUNCTION)
    assert transfer is not None
    assert transfer.status is SolutionSectionStatus.BLOCKED
    assert not transfer.lines
    assert report.section(SolutionSectionKind.PREREQUISITES).status is (  # type: ignore[union-attr]
        SolutionSectionStatus.BLOCKED
    )
    assert report.section(SolutionSectionKind.DOMAIN_EXCLUSIONS).status is (  # type: ignore[union-attr]
        SolutionSectionStatus.BLOCKED
    )
    notices = report.section(SolutionSectionKind.WORKFLOW_NOTICES)
    assert notices is not None
    assert notices.lines


def test_reduction_failure_retains_raw_report_part() -> None:
    workflow_limits = TransferFunctionWorkflowLimits(
        reduction=TransferFunctionReductionLimits(max_input_terms=1)
    )
    state = TransferFunctionWorkflowService(workflow_limits).run(
        _request("(s+1)/(s+2)")
    )

    report = TransferFunctionSolutionReportBuilder(
        workflow_limits=workflow_limits
    ).build(state)

    assert report.status is SolutionReportStatus.PARTIAL
    raw = report.section(SolutionSectionKind.NUMERATOR_DENOMINATOR)
    assert raw is not None
    assert raw.lines
    reduction = report.section(SolutionSectionKind.REDUCTION)
    assert reduction is not None
    assert reduction.status is SolutionSectionStatus.FAILED


def test_root_failure_retains_reduced_report_part() -> None:
    state = TransferFunctionWorkflowService().run(
        TransferFunctionWorkflowRequest(
            WorkflowInputForm.COMMON,
            common_expression_text="1/(T*s+1)",
            allowed_parameter_names=("T",),
            substitutions=ParameterSubstitutions(),
        )
    )
    report = TransferFunctionSolutionReportBuilder().build(state)

    assert report.status is SolutionReportStatus.PARTIAL
    assert report.section(SolutionSectionKind.REDUCTION).lines  # type: ignore[union-attr]
    assert report.section(SolutionSectionKind.ZEROS).status is (  # type: ignore[union-attr]
        SolutionSectionStatus.FAILED
    )
    assert report.section(SolutionSectionKind.SOURCES).status is (  # type: ignore[union-attr]
        SolutionSectionStatus.BLOCKED
    )


def test_stability_failure_retains_poles() -> None:
    workflow_limits = TransferFunctionWorkflowLimits(
        stability_analysis=StabilityAnalysisLimits(max_poles=1)
    )
    state = TransferFunctionWorkflowService(workflow_limits).run(
        _request("1/(s^2+3*s+2)")
    )
    report = TransferFunctionSolutionReportBuilder(
        workflow_limits=workflow_limits
    ).build(state)

    assert report.status is SolutionReportStatus.PARTIAL
    assert report.section(SolutionSectionKind.POLES).lines  # type: ignore[union-attr]
    assert report.section(SolutionSectionKind.STABILITY).status is (  # type: ignore[union-attr]
        SolutionSectionStatus.FAILED
    )
    sources = report.section(SolutionSectionKind.SOURCES)
    assert sources is not None
    assert sources.status is SolutionSectionStatus.FAILED
    assert len(sources.lines) == 1
    assert type(sources.lines[0]) is WarningLine
    assert sources.lines[0].severity is DiagnosticSeverity.ERROR


def test_wrong_top_level_state_types_raise_type_error() -> None:
    class StateSubclass(TransferFunctionWorkflowState):
        pass

    builder = TransferFunctionSolutionReportBuilder()
    valid = TransferFunctionWorkflowService().run(_request("1/(s+1)"))
    with pytest.raises(TypeError, match="TransferFunctionWorkflowState"):
        builder.build(object())  # type: ignore[arg-type]
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
        builder.build(subclass)


@pytest.mark.parametrize(
    "manipulation",
    [
        "raw_result",
        "stage_order",
        "diagnostic_aggregation",
        "operation_sequence",
    ],
)
def test_manipulated_state_fails_without_reusing_mathematics(
    manipulation: str,
) -> None:
    state = TransferFunctionWorkflowService().run(_request("1/(s+1)"))
    if manipulation == "raw_result":
        object.__setattr__(state, "raw_result", object())
    elif manipulation == "stage_order":
        object.__setattr__(
            state,
            "stage_records",
            tuple(reversed(state.stage_records)),
        )
    elif manipulation == "diagnostic_aggregation":
        object.__setattr__(state, "aggregated_diagnostics", (object(),))
    else:
        object.__setattr__(state, "operation_sequence", 1_000_001)

    report = TransferFunctionSolutionReportBuilder().build(state)

    assert report.status is SolutionReportStatus.FAILED
    assert len(report.sections) == 1
    assert report.sections[0].kind is SolutionSectionKind.WORKFLOW_NOTICES
    assert report.diagnostics[0].code is (
        ReportDiagnosticCode.REPORT_INVALID_WORKFLOW_STATE
    )
    assert all(
        type(line) is WarningLine for line in report.sections[0].lines
    )
    assert all(
        line.severity is DiagnosticSeverity.ERROR
        for line in report.sections[0].lines
        if type(line) is WarningLine
    )


def test_builder_uses_its_workflow_limits_exclusively() -> None:
    state = TransferFunctionWorkflowService().run(_request("1/(s+1)"))
    later = replace(state, operation_sequence=1_000_001)
    permissive = TransferFunctionWorkflowLimits(
        max_operation_sequence=1_000_001
    )

    accepted = TransferFunctionSolutionReportBuilder(
        workflow_limits=permissive
    ).build(later)
    rejected = TransferFunctionSolutionReportBuilder().build(later)

    assert accepted.status is SolutionReportStatus.COMPLETE
    assert rejected.status is SolutionReportStatus.FAILED
    assert rejected.diagnostics[0].code is (
        ReportDiagnosticCode.REPORT_INVALID_WORKFLOW_STATE
    )
    assert all(
        section.kind is SolutionSectionKind.WORKFLOW_NOTICES
        for section in rejected.sections
    )


def test_workflow_limit_configuration_is_not_report_identity() -> None:
    state = TransferFunctionWorkflowService().run(_request("1/(s+1)"))
    first = TransferFunctionSolutionReportBuilder(
        workflow_limits=TransferFunctionWorkflowLimits(
            max_operation_sequence=10
        )
    ).build(state)
    second = TransferFunctionSolutionReportBuilder(
        workflow_limits=TransferFunctionWorkflowLimits(
            max_operation_sequence=20
        )
    ).build(state)

    assert first == second
    assert hash(first) == hash(second)


def test_manipulated_failed_root_result_is_rejected_without_mathematics() -> None:
    state = TransferFunctionWorkflowService().run(
        TransferFunctionWorkflowRequest(
            WorkflowInputForm.COMMON,
            common_expression_text="1/(T*s+1)",
            allowed_parameter_names=("T",),
            substitutions=ParameterSubstitutions(),
        )
    )
    assert state.root_analysis_result is not None
    object.__setattr__(
        state.root_analysis_result,
        "reduced_transfer_function",
        state.reduced_value,
    )

    report = TransferFunctionSolutionReportBuilder().build(state)

    assert report.status is SolutionReportStatus.FAILED
    assert tuple(section.kind for section in report.sections) == (
        SolutionSectionKind.WORKFLOW_NOTICES,
    )


def test_manipulated_failed_stability_result_is_rejected_without_math() -> None:
    workflow_limits = TransferFunctionWorkflowLimits(
        stability_analysis=StabilityAnalysisLimits(max_poles=1)
    )
    state = TransferFunctionWorkflowService(workflow_limits).run(
        _request("1/(s^2+3*s+2)")
    )
    assert state.stability_analysis_result is not None
    object.__setattr__(
        state.stability_analysis_result,
        "status",
        StabilityStatus.STABLE,
    )

    report = TransferFunctionSolutionReportBuilder(
        workflow_limits=workflow_limits
    ).build(state)

    assert report.status is SolutionReportStatus.FAILED
    assert tuple(section.kind for section in report.sections) == (
        SolutionSectionKind.WORKFLOW_NOTICES,
    )


def test_operation_sequence_is_not_part_of_report_identity() -> None:
    state = TransferFunctionWorkflowService().run(_request("1/(s+1)"))
    assert not state.aggregated_diagnostics
    later = replace(state, operation_sequence=42)
    builder = TransferFunctionSolutionReportBuilder()

    assert builder.build(state) == builder.build(later)
    assert hash(builder.build(state)) == hash(builder.build(later))


def test_diagnostic_provenance_sequence_is_not_report_identity() -> None:
    state = TransferFunctionWorkflowService().run(
        TransferFunctionWorkflowRequest(
            WorkflowInputForm.COMMON,
            common_expression_text="1/(T*s+1)",
            allowed_parameter_names=("T",),
        )
    )
    assert state.aggregated_diagnostics
    later = replace(
        state,
        operation_sequence=42,
        aggregated_diagnostics=tuple(
            replace(entry, operation_sequence=42)
            for entry in state.aggregated_diagnostics
        ),
    )
    builder = TransferFunctionSolutionReportBuilder()

    assert builder.build(state) == builder.build(later)


@pytest.mark.parametrize(
    ("limits", "expression", "parameters"),
    [
        (SolutionReportLimits(max_sections=1), "1/(s+1)", ()),
        (SolutionReportLimits(max_total_lines=1), "1/(s+1)", ()),
        (SolutionReportLimits(max_lines_per_section=1), "1/(s+1)", ()),
        (SolutionReportLimits(max_expression_length=1), "1/(s+1)", ()),
        (
            SolutionReportLimits(max_reduction_steps=1),
            "2*(s+1)/(4*(s+1))",
            (),
        ),
        (
            SolutionReportLimits(max_roots=1),
            "(s^2+1)/(s^2+3*s+2)",
            (),
        ),
        (
            SolutionReportLimits(max_conditions=1),
            "1/((K-1)*s+T)",
            ("K", "T"),
        ),
        (
            SolutionReportLimits(max_source_references=1),
            "1/(s+1)",
            (),
        ),
        (
            SolutionReportLimits(max_warning_lines=1),
            "1/(T*s+1)",
            ("T",),
        ),
    ],
)
def test_report_limits_are_structured_and_never_complete(
    limits: SolutionReportLimits,
    expression: str,
    parameters: tuple[str, ...],
) -> None:
    state = TransferFunctionWorkflowService().run(
        TransferFunctionWorkflowRequest(
            WorkflowInputForm.COMMON,
            common_expression_text=expression,
            allowed_parameter_names=parameters,
        )
    )
    report = TransferFunctionSolutionReportBuilder(limits).build(state)

    assert report.status is not SolutionReportStatus.COMPLETE
    assert any(
        diagnostic.code is ReportDiagnosticCode.REPORT_LIMIT_EXCEEDED
        for diagnostic in report.diagnostics
    )
    assert all(
        diagnostic.severity is DiagnosticSeverity.ERROR
        for diagnostic in report.diagnostics
        if diagnostic.code is ReportDiagnosticCode.REPORT_LIMIT_EXCEEDED
    )
    assert any(
        type(line) is WarningLine
        and line.code == ReportDiagnosticCode.REPORT_LIMIT_EXCEEDED.value
        for section in report.sections
        for line in section.lines
    )
