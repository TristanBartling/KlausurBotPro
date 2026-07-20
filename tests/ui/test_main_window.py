"""MainWindow lifecycle, shortcuts, and real end-to-end GUI smoke tests."""

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEventLoop, Qt, QTimer
from PySide6.QtGui import QShortcut
from PySide6.QtTest import QSignalSpy, QTest
from PySide6.QtWidgets import QApplication

from klausurbotpro.app import APP_NAME, MainWindow
from klausurbotpro.ui import (
    FrequencyDomainUiRunStatus,
    TransferFunctionUiRunStatus,
    WorkflowWorkerFailure,
)


def _app() -> QApplication:
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    assert isinstance(application, QApplication)
    return application


def test_main_window_structure_shortcuts_and_idle_shutdown() -> None:
    _app()
    window = MainWindow()
    window.show()
    _app().processEvents()

    assert window.windowTitle() == APP_NAME
    assert window.centralWidget() is window.workspace_tabs
    assert window.workspace_tabs.widget(0) is window.workspace
    assert window.workspace_tabs.widget(1) is window.frequency_workspace
    assert window.workspace_tabs.tabText(1) == "Frequenzbereich"
    assert window.width() >= 1100
    sequences = {
        shortcut.key().toString()
        for shortcut in window.findChildren(QShortcut)
    }
    assert {"Ctrl+Return", "Ctrl+R", "Ctrl+Shift+C", "Alt+P", "Alt+L"} <= sequences
    assert window.worker_thread.isRunning()
    assert window.shutdown()
    assert not window.worker_thread.isRunning()
    window.close()


def test_real_common_end_to_end_offscreen() -> None:
    application = _app()
    window = MainWindow()
    window.show()
    completed = QSignalSpy(window.worker.completed)
    loop = QEventLoop()
    window.worker.completed.connect(loop.quit)
    window.workspace.common_expression_edit.setPlainText("1/(s+1)")

    QTest.mouseClick(
        window.workspace.calculate_button,
        Qt.MouseButton.LeftButton,
    )

    assert (
        window.presenter.state.run_status
        is TransferFunctionUiRunStatus.RUNNING
    )
    assert not window.workspace.common_expression_edit.isEnabled()
    assert not window.workspace.copy_button.isEnabled()
    assert window.workspace.plaintext_report_edit.toPlainText() == ""
    for index in range(window.workspace.stage_tree.topLevelItemCount()):
        item = window.workspace.stage_tree.topLevelItem(index)
        assert item is not None
        assert item.text(1) == "Berechnung läuft"

    QTimer.singleShot(15_000, loop.quit)
    loop.exec()
    application.processEvents()
    assert completed.count() == 1
    assert window.presenter.state.run_status.value == (
        TransferFunctionUiRunStatus.COMPLETE.value
    )
    assert "-1" in window.workspace.summary_edits[
        next(
            kind
            for kind in window.workspace.summary_edits
            if kind.value == "poles"
        )
    ].toPlainText()
    assert "System ist E/A-stabil." in window.workspace.summary_edits[
        next(
            kind
            for kind in window.workspace.summary_edits
            if kind.value == "stability"
        )
    ].toPlainText()
    plaintext = window.workspace.plaintext_report_edit.toPlainText()
    latex = window.workspace.latex_report_edit.toPlainText()
    assert plaintext
    assert latex
    for internal_value in (
        "stable",
        "numerator",
        "retained_domain_exclusion",
    ):
        assert internal_value not in plaintext
    assert window.workspace.common_expression_edit.isEnabled()
    assert window.shutdown()
    window.close()


def test_close_during_running_is_deferred_then_clean() -> None:
    _app()
    window = MainWindow()
    window.presenter.execution_requested.disconnect()
    window.workspace.common_expression_edit.setPlainText("1/(s+1)")
    window.workspace.calculate()
    assert (
        window.presenter.state.run_status
        is TransferFunctionUiRunStatus.RUNNING
    )

    assert not window.shutdown()
    assert window.worker_thread.isRunning()
    assert "Schließen" in window.presenter.state.general_message
    window.presenter.accept_failure(WorkflowWorkerFailure("Test beendet."))
    _app().processEvents()
    _app().processEvents()

    assert not window.worker_thread.isRunning()


def test_real_frequency_single_point_end_to_end_offscreen() -> None:
    application = _app()
    window = MainWindow()
    window.show()
    window.workspace_tabs.setCurrentIndex(1)
    completed = QSignalSpy(window.frequency_worker.completed)
    loop = QEventLoop()
    window.frequency_worker.completed.connect(loop.quit)
    workspace = window.frequency_workspace
    workspace.common_expression_edit.setPlainText("1/(s+1)")
    workspace.single_frequency_edit.setText("1")

    QTest.mouseClick(workspace.calculate_button, Qt.MouseButton.LeftButton)

    assert window.frequency_presenter.state.run_status is (
        FrequencyDomainUiRunStatus.RUNNING
    )
    assert not workspace.common_expression_edit.isEnabled()
    assert not workspace.calculate_button.isEnabled()
    QTimer.singleShot(15_000, loop.quit)
    loop.exec()
    application.processEvents()

    assert completed.count() == 1
    assert window.frequency_presenter.state.run_status.value == (
        FrequencyDomainUiRunStatus.COMPLETE.value
    )
    assert workspace.single_labels["omega"].text() == "1"
    assert workspace.single_labels["status"].text() == "Definiert"
    assert workspace.single_labels["complex_value"].text() == "1/2 - I/2"
    assert workspace.common_expression_edit.isEnabled()
    assert window.shutdown()
    window.close()


def test_close_during_frequency_run_is_deferred_then_clean() -> None:
    _app()
    window = MainWindow()
    window.frequency_presenter.execution_requested.disconnect()
    window.frequency_workspace.common_expression_edit.setPlainText("1/(s+1)")
    window.frequency_workspace.calculate()
    assert window.frequency_presenter.state.run_status is (
        FrequencyDomainUiRunStatus.RUNNING
    )

    assert not window.shutdown()
    assert window.worker_thread.isRunning()
    window.frequency_presenter.accept_failure(
        WorkflowWorkerFailure("Test beendet.")
    )
    _app().processEvents()
    _app().processEvents()

    assert not window.worker_thread.isRunning()


def test_widgets_import_only_public_application_not_domain_analyzers() -> None:
    root = Path(__file__).parents[2]
    ui_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((root / "src/klausurbotpro/ui").glob("*.py"))
    )

    assert "klausurbotpro.domain" not in ui_text
    assert "klausurbotpro.parsing" not in ui_text
    assert "sympy" not in ui_text.lower()
    for forbidden in (
        "TransferFunctionReducer",
        "TransferFunctionRootAnalyzer",
        "TransferFunctionStabilityAnalyzer",
    ):
        assert forbidden not in ui_text
    worker_text = (
        root / "src/klausurbotpro/ui/workflow_worker.py"
    ).read_text(encoding="utf-8")
    assert "from klausurbotpro.application import" in worker_text
