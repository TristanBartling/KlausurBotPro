"""Visible workspace projection of qualitative transfer-function results."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from klausurbotpro.application import (
    SolutionSectionKind,
    TransferFunctionRequestFactory,
    TransferFunctionSolutionReportBuilder,
    TransferFunctionWorkflowRequest,
    TransferFunctionWorkflowService,
    WorkflowInputForm,
    render_solution_report_latex,
    render_solution_report_plaintext,
)
from klausurbotpro.ui import (
    TransferFunctionPresenter,
    TransferFunctionViewState,
    TransferFunctionWorkflowExecutionResult,
    TransferFunctionWorkspace,
)


def test_gui_summary_matches_plaintext_and_latex_interpretation() -> None:
    application = QApplication.instance() or QApplication([])
    presenter = TransferFunctionPresenter(TransferFunctionRequestFactory())
    workspace = TransferFunctionWorkspace(presenter)
    state = TransferFunctionWorkflowService().run(
        TransferFunctionWorkflowRequest(
            WorkflowInputForm.COMMON,
            common_expression_text="s/(2*s^2+4*s+6)",
        )
    )
    report = TransferFunctionSolutionReportBuilder().build(state)
    plaintext = render_solution_report_plaintext(report)
    latex = render_solution_report_latex(report)
    presenter.accept_result(
        TransferFunctionWorkflowExecutionResult(
            state,
            report,
            plaintext,
            latex,
        )
    )
    application.processEvents()

    statement = (
        "Das E/A-Verhalten enthält einen gedämpft schwingenden Anteil."
    )
    assert statement in workspace.summary_edits[
        SolutionSectionKind.DYNAMIC_BEHAVIOR
    ].toPlainText()
    assert statement in plaintext
    assert statement in latex
    assert "p_1 ≈ -1 - j*1.41421" in workspace.summary_edits[
        SolutionSectionKind.POLES
    ].toPlainText()
    assert type(presenter.state) is TransferFunctionViewState
    workspace.close()
