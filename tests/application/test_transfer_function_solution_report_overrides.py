"""Visible override provenance without invented derivation."""

from klausurbotpro.application import (
    OverrideLine,
    OverrideProvenance,
    RawTransferFunctionOverride,
    ReducedTransferFunctionOverride,
    RootAnalysisOverride,
    SolutionSectionKind,
    SolutionSectionStatus,
    TransferFunctionSolutionReportBuilder,
    TransferFunctionWorkflowRequest,
    TransferFunctionWorkflowService,
    TransferFunctionWorkflowState,
    TransformationLine,
    WorkflowInputForm,
    WorkflowOverrideOriginKind,
    WorkflowStage,
    render_solution_report_latex,
    render_solution_report_plaintext,
)


def _state(expression: str) -> TransferFunctionWorkflowState:
    return TransferFunctionWorkflowService().run(
        TransferFunctionWorkflowRequest(
            WorkflowInputForm.COMMON,
            common_expression_text=expression,
        )
    )


def _provenance(stage: WorkflowStage) -> OverrideProvenance:
    return OverrideProvenance(
        WorkflowOverrideOriginKind.MANUAL,
        "fachlich kontrolliert gesetzt",
        1,
        stage,
    )


def test_raw_override_is_visible() -> None:
    service = TransferFunctionWorkflowService()
    base = service.run(
        TransferFunctionWorkflowRequest(
            WorkflowInputForm.COMMON,
            common_expression_text="1/(s+1)",
        )
    )
    source = _state("1/(s+2)")
    assert source.raw_value is not None
    changed = service.apply_override(
        base,
        RawTransferFunctionOverride(
            source.raw_value,
            _provenance(WorkflowStage.RAW_TRANSFER_FUNCTION),
        ),
    )

    report = TransferFunctionSolutionReportBuilder().build(changed)
    section = report.section(SolutionSectionKind.TRANSFER_FUNCTION)
    assert section is not None
    override = next(line for line in section.lines if type(line) is OverrideLine)
    assert override.target_stage is WorkflowStage.RAW_TRANSFER_FUNCTION
    assert override.origin_kind is WorkflowOverrideOriginKind.MANUAL
    assert override.reason == "fachlich kontrolliert gesetzt"
    assert not hasattr(override, "operation_sequence")


def test_reduced_override_has_no_invented_reduction_steps() -> None:
    service = TransferFunctionWorkflowService()
    base = _state("1/(s+1)")
    source = _state("1/(s-1)")
    assert source.reduced_value is not None
    changed = service.apply_override(
        base,
        ReducedTransferFunctionOverride(
            source.reduced_value,
            _provenance(WorkflowStage.REDUCTION),
        ),
    )

    report = TransferFunctionSolutionReportBuilder().build(changed)
    section = report.section(SolutionSectionKind.REDUCTION)
    assert section is not None
    assert section.status is SolutionSectionStatus.PARTIAL
    assert any(type(line) is OverrideLine for line in section.lines)
    assert not any(type(line) is TransformationLine for line in section.lines)


def test_root_override_is_visible_without_claiming_recomputation() -> None:
    service = TransferFunctionWorkflowService()
    state = _state("1/(s+1)")
    assert state.root_analysis_result is not None
    changed = service.apply_override(
        state,
        RootAnalysisOverride(
            state.root_analysis_result,
            _provenance(WorkflowStage.ROOT_ANALYSIS),
        ),
    )

    report = TransferFunctionSolutionReportBuilder().build(changed)
    zeros = report.section(SolutionSectionKind.ZEROS)
    poles = report.section(SolutionSectionKind.POLES)
    assert zeros is not None
    assert poles is not None
    assert type(zeros.lines[0]) is OverrideLine
    assert type(poles.lines[0]) is OverrideLine
    assert zeros.lines[0] == poles.lines[0]
    assert zeros.lines[0].target_stage is WorkflowStage.ROOT_ANALYSIS
    plaintext = render_solution_report_plaintext(report)
    latex = render_solution_report_latex(report)
    assert plaintext.count("[manuelle Vorgabe – Wurzelanalyse]") == 2
    assert latex.count("manuelle Vorgabe – Wurzelanalyse") == 2
    assert "root_analysis" not in plaintext
    assert "root\\_analysis" not in latex
