"""Offscreen interaction tests for the transfer-function workspace."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QTableWidgetItem

from klausurbotpro.application import (
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
    TransferFunctionUiRunStatus,
    TransferFunctionWorkflowExecutionResult,
    TransferFunctionWorkspace,
)


def _app() -> QApplication:
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    assert isinstance(application, QApplication)
    return application


def _workspace() -> tuple[TransferFunctionWorkspace, list[object]]:
    presenter = TransferFunctionPresenter(TransferFunctionRequestFactory())
    requests: list[object] = []
    presenter.execution_requested.connect(requests.append)
    workspace = TransferFunctionWorkspace(presenter)
    workspace.show()
    _app().processEvents()
    return workspace, requests


def _complete(
    workspace: TransferFunctionWorkspace,
    request: TransferFunctionWorkflowRequest,
) -> TransferFunctionWorkflowExecutionResult:
    state = TransferFunctionWorkflowService().run(request)
    report = TransferFunctionSolutionReportBuilder().build(state)
    result = TransferFunctionWorkflowExecutionResult(
        state,
        report,
        render_solution_report_plaintext(report),
        render_solution_report_latex(report),
    )
    workspace.presenter.accept_result(result)
    _app().processEvents()
    return result


def test_input_form_switch_preserves_text_and_uses_only_active_form() -> None:
    workspace, requests = _workspace()
    workspace.common_expression_edit.setPlainText("1/(s+1)")
    workspace.numerator_edit.setPlainText("1")
    workspace.denominator_edit.setPlainText("s+2")

    QTest.mouseClick(workspace.separated_radio, Qt.MouseButton.LeftButton)
    assert workspace.common_expression_edit.toPlainText() == "1/(s+1)"
    assert workspace.input_stack.currentIndex() == 1
    QTest.mouseClick(workspace.calculate_button, Qt.MouseButton.LeftButton)

    request = requests[0]
    assert type(request) is TransferFunctionWorkflowRequest
    assert request.input_form is WorkflowInputForm.SEPARATED
    assert request.common_expression_text is None
    assert request.numerator_expression_text == "1"
    assert request.denominator_expression_text == "s+2"
    workspace.presenter.accept_failure(_safe_failure())
    workspace.close()


def test_parameter_rows_exact_error_focus_and_running_lock() -> None:
    workspace, requests = _workspace()
    workspace.common_expression_edit.setPlainText("1/(T*s+1)")
    workspace.add_parameter_row()
    workspace.parameter_table.setItem(0, 0, QTableWidgetItem("T"))
    workspace.parameter_table.setItem(0, 1, QTableWidgetItem("0.5"))

    QTest.mouseClick(workspace.calculate_button, Qt.MouseButton.LeftButton)

    assert not requests
    assert workspace.parameter_table.hasFocus()
    assert "Eingabe ungültig" in workspace.status_label.text()
    workspace.parameter_table.setItem(0, 1, QTableWidgetItem("2"))
    QTest.mouseClick(workspace.calculate_button, Qt.MouseButton.LeftButton)
    assert len(requests) == 1
    assert not workspace.calculate_button.isEnabled()
    assert not workspace.reset_button.isEnabled()
    QTest.mouseClick(workspace.calculate_button, Qt.MouseButton.LeftButton)
    assert len(requests) == 1
    workspace.presenter.accept_failure(_safe_failure())
    workspace.close()


def test_summary_reports_clipboard_tabs_and_reset() -> None:
    workspace, requests = _workspace()
    workspace.common_expression_edit.setPlainText("1/(s+1)")
    QTest.mouseClick(workspace.calculate_button, Qt.MouseButton.LeftButton)
    request = requests[0]
    assert type(request) is TransferFunctionWorkflowRequest
    result = _complete(workspace, request)

    assert "-1" in workspace.summary_edits[
        next(
            kind
            for kind in workspace.summary_edits
            if kind.value == "poles"
        )
    ].toPlainText()
    assert "[stable]" in workspace.summary_edits[
        next(
            kind
            for kind in workspace.summary_edits
            if kind.value == "stability"
        )
    ].toPlainText()
    assert workspace.plaintext_report_edit.toPlainText() == result.plaintext_report
    assert workspace.latex_report_edit.toPlainText() == result.latex_report
    QTest.mouseClick(workspace.copy_button, Qt.MouseButton.LeftButton)
    assert QApplication.clipboard().text() == result.plaintext_report
    workspace.report_tabs.setCurrentIndex(1)
    QTest.mouseClick(workspace.copy_button, Qt.MouseButton.LeftButton)
    assert QApplication.clipboard().text() == result.latex_report

    QTest.mouseClick(workspace.reset_button, Qt.MouseButton.LeftButton)
    assert workspace.common_radio.isChecked()
    assert workspace.common_expression_edit.toPlainText() == ""
    assert workspace.variable_edit.text() == "s"
    assert workspace.parameter_table.rowCount() == 0
    assert workspace.presenter.state.run_status is TransferFunctionUiRunStatus.IDLE
    assert not workspace.copy_button.isEnabled()
    workspace.close()


def test_stage_status_and_severity_are_textual() -> None:
    workspace, requests = _workspace()
    workspace.common_expression_edit.setPlainText("open('x')")
    QTest.mouseClick(workspace.calculate_button, Qt.MouseButton.LeftButton)
    request = requests[0]
    assert type(request) is TransferFunctionWorkflowRequest
    _complete(workspace, request)

    parse = workspace.stage_tree.topLevelItem(0)
    blocked = workspace.stage_tree.topLevelItem(1)
    assert parse is not None and blocked is not None
    assert parse.text(1) == "Fehlgeschlagen"
    assert "FEHLER" in parse.text(2)
    assert blocked.text(1) == "Blockiert"
    assert blocked.text(2) == "—"
    assert workspace.plaintext_report_edit.toPlainText()
    workspace.close()


def test_later_domain_failure_keeps_previous_structured_results_visible() -> None:
    workspace, requests = _workspace()
    workspace.common_expression_edit.setPlainText("1/(K*s+T)")
    workspace.add_parameter_row()
    workspace.parameter_table.setItem(0, 0, QTableWidgetItem("K"))
    workspace.parameter_table.setItem(0, 1, QTableWidgetItem("1"))
    workspace.add_parameter_row()
    workspace.parameter_table.setItem(1, 0, QTableWidgetItem("T"))
    QTest.mouseClick(workspace.calculate_button, Qt.MouseButton.LeftButton)
    request = requests[0]
    assert type(request) is TransferFunctionWorkflowRequest

    _complete(workspace, request)

    assert (
        workspace.presenter.state.run_status
        is TransferFunctionUiRunStatus.PARTIAL
    )
    assert workspace.summary_edits[
        next(
            kind
            for kind in workspace.summary_edits
            if kind.value == "transfer_function"
        )
    ].toPlainText()
    assert workspace.plaintext_report_edit.toPlainText()
    workspace.close()


def _safe_failure() -> object:
    from klausurbotpro.ui import WorkflowWorkerFailure

    return WorkflowWorkerFailure("Testfehler.")
