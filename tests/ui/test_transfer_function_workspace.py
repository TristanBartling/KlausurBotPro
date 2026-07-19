"""Offscreen interaction tests for the transfer-function workspace."""

import os
from dataclasses import replace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QTableWidgetItem

from klausurbotpro.application import (
    TransferFunctionRequestFactory,
    TransferFunctionSolutionReportBuilder,
    TransferFunctionWorkflowRequest,
    TransferFunctionWorkflowService,
    WorkflowDiagnosticEntry,
    WorkflowInputForm,
    WorkflowStageRecord,
    WorkflowStageStatus,
    render_solution_report_latex,
    render_solution_report_plaintext,
)
from klausurbotpro.domain import (
    Diagnostic,
    DiagnosticCode,
    DiagnosticSeverity,
)
from klausurbotpro.ui import (
    TransferFunctionPresenter,
    TransferFunctionUiRunStatus,
    TransferFunctionViewState,
    TransferFunctionWorkflowExecutionResult,
    TransferFunctionWorkspace,
)


def _app() -> QApplication:
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    assert isinstance(application, QApplication)
    return application


def _workspace() -> tuple[
    TransferFunctionWorkspace,
    list[object],
    QApplication,
]:
    application = _app()
    presenter = TransferFunctionPresenter(TransferFunctionRequestFactory())
    requests: list[object] = []
    presenter.execution_requested.connect(requests.append)
    workspace = TransferFunctionWorkspace(presenter)
    workspace.show()
    application.processEvents()
    return workspace, requests, application


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
    workspace, requests, _application = _workspace()
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
    workspace, requests, _application = _workspace()
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
    workspace, requests, _application = _workspace()
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
    workspace, requests, _application = _workspace()
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


def test_stage_message_belongs_to_first_highest_severity_diagnostic() -> None:
    workspace, requests, _application = _workspace()
    workspace.common_expression_edit.setPlainText("1/(s+1)")
    QTest.mouseClick(workspace.calculate_button, Qt.MouseButton.LeftButton)
    request = requests[0]
    assert type(request) is TransferFunctionWorkflowRequest
    result = _complete(workspace, request)
    info = Diagnostic(
        DiagnosticSeverity.INFO,
        DiagnosticCode.PARSE_INVALID_SYNTAX,
        "Info-Meldung",
    )
    first_warning = Diagnostic(
        DiagnosticSeverity.WARNING,
        DiagnosticCode.PARSE_INVALID_SYNTAX,
        "Erste Warnung",
    )
    second_warning = Diagnostic(
        DiagnosticSeverity.WARNING,
        DiagnosticCode.PARSE_INVALID_SYNTAX,
        "Zweite Warnung",
    )
    error = Diagnostic(
        DiagnosticSeverity.ERROR,
        DiagnosticCode.PARSE_INVALID_SYNTAX,
        "Fehler-Meldung",
    )

    error_state = _state_with_parse_diagnostics(
        result,
        (info, first_warning, error),
    )
    workspace.render_state(error_state)
    parse = workspace.stage_tree.topLevelItem(0)
    assert parse is not None
    assert "FEHLER" in parse.text(2)
    assert parse.text(3) == "Fehler-Meldung"

    warning_state = _state_with_parse_diagnostics(
        result,
        (info, first_warning, second_warning),
    )
    workspace.render_state(warning_state)
    assert "WARNUNG" in parse.text(2)
    assert parse.text(3) == "Erste Warnung"
    workspace.close()


def test_later_domain_failure_keeps_previous_structured_results_visible() -> None:
    workspace, requests, _application = _workspace()
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


def test_unexpected_worker_failure_removes_old_math_and_copy_action() -> None:
    workspace, requests, _application = _workspace()
    workspace.common_expression_edit.setPlainText("1/(s+1)")
    QTest.mouseClick(workspace.calculate_button, Qt.MouseButton.LeftButton)
    first_request = requests[0]
    assert type(first_request) is TransferFunctionWorkflowRequest
    _complete(workspace, first_request)
    assert workspace.copy_button.isEnabled()
    assert any(
        edit.toPlainText() for edit in workspace.summary_edits.values()
    )

    workspace.common_expression_edit.setPlainText("1/(s+2)")
    QTest.mouseClick(workspace.calculate_button, Qt.MouseButton.LeftButton)
    assert len(requests) == 2
    workspace.presenter.accept_failure(_safe_failure())
    _app().processEvents()

    assert all(
        not edit.toPlainText() for edit in workspace.summary_edits.values()
    )
    assert workspace.plaintext_report_edit.toPlainText() == ""
    assert workspace.latex_report_edit.toPlainText() == ""
    assert not workspace.copy_button.isEnabled()
    for index in range(workspace.stage_tree.topLevelItemCount()):
        item = workspace.stage_tree.topLevelItem(index)
        assert item is not None
        assert item.text(1) == "Nicht ausgewertet"
    workspace.close()


def _state_with_parse_diagnostics(
    result: TransferFunctionWorkflowExecutionResult,
    diagnostics: tuple[Diagnostic, ...],
) -> TransferFunctionViewState:
    original = result.workflow_state
    parse_record = WorkflowStageRecord(
        original.stage_records[0].stage,
        WorkflowStageStatus.FAILED,
        diagnostics=diagnostics,
    )
    records = (parse_record, *original.stage_records[1:])
    entries = tuple(
        WorkflowDiagnosticEntry(
            record.stage,
            index,
            diagnostic,
            original.operation_sequence,
            record.diagnostic_provenances[index],
        )
        for record in records
        for index, diagnostic in enumerate(record.diagnostics)
    )
    workflow_state = replace(
        original,
        stage_records=records,
        aggregated_diagnostics=entries,
    )
    return TransferFunctionViewState(workflow_state=workflow_state)


def _safe_failure() -> object:
    from klausurbotpro.ui import WorkflowWorkerFailure

    return WorkflowWorkerFailure("Testfehler.")
