"""Focused five-workspace heading and asynchronous snapshot checks."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEventLoop, Qt, QTimer
from PySide6.QtTest import QSignalSpy, QTest
from PySide6.QtWidgets import QApplication

from klausurbotpro.ui.main_window import MainWindow


def _app() -> QApplication:
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    assert isinstance(application, QApplication)
    return application


def _wait(spy: QSignalSpy, loop: QEventLoop) -> None:
    QTimer.singleShot(15_000, loop.quit)
    loop.exec()
    _app().processEvents()
    assert spy.count() == 1


def test_async_transfer_heading_uses_click_snapshot_and_copies_displayed_text() -> None:
    _app()
    window = MainWindow()
    workspace = window.workspace
    workspace.report_tabs.setCurrentIndex(1)
    workspace.common_expression_edit.setPlainText("1/(s+1)")
    workspace.task_title_edit.setText("Aufgabe A")
    completed = QSignalSpy(window.worker.completed)
    loop = QEventLoop()
    window.worker.completed.connect(loop.quit)

    QTest.mouseClick(workspace.calculate_button, Qt.MouseButton.LeftButton)
    workspace.task_title_edit.setText("Aufgabe B")
    _wait(completed, loop)

    latex = workspace.latex_report_edit.toPlainText()
    assert latex.startswith(r"\section*{Aufgabe A}")
    assert "Aufgabe B" not in latex
    assert latex.count(r"\section*{") == 1
    workspace.render_state(window.presenter.state)
    assert workspace.latex_report_edit.toPlainText().count(
        r"\section*{Aufgabe A}"
    ) == 1
    QTest.mouseClick(workspace.copy_button, Qt.MouseButton.LeftButton)
    assert QApplication.clipboard().text() == latex
    assert window.shutdown()
    window.close()


def test_frequency_heading_is_displayed_and_copied_once() -> None:
    _app()
    window = MainWindow()
    workspace = window.frequency_workspace
    workspace.common_expression_edit.setPlainText("1/(s+1)")
    workspace.task_title_edit.setText("Aufgabe Frequenz")
    completed = QSignalSpy(window.frequency_worker.completed)
    loop = QEventLoop()
    window.frequency_worker.completed.connect(loop.quit)

    QTest.mouseClick(workspace.calculate_button, Qt.MouseButton.LeftButton)
    _wait(completed, loop)

    latex = workspace.latex_report_edit.toPlainText()
    assert latex.startswith(r"\section*{Aufgabe Frequenz}")
    assert latex.count(r"\section*{Aufgabe Frequenz}") == 1
    QTest.mouseClick(workspace.copy_latex_button, Qt.MouseButton.LeftButton)
    assert QApplication.clipboard().text() == latex
    assert window.shutdown()
    window.close()


def test_sync_workspaces_capture_heading_and_error_does_not_leave_heading() -> None:
    _app()
    window = MainWindow()

    stability = window.stability_workspace
    stability.task_title_edit.setText("Aufgabe Stabilität")
    stability.polynomial_edit.setPlainText("s+1")
    QTest.mouseClick(stability.analyze_button, Qt.MouseButton.LeftButton)
    stability_latex = stability.result_edits["latex"].toPlainText()
    assert stability_latex.startswith(r"\section*{Aufgabe Stabilität}")
    QTest.mouseClick(stability.copy_latex_button, Qt.MouseButton.LeftButton)
    assert QApplication.clipboard().text() == stability_latex

    time_domain = window.time_domain_workspace
    time_domain.task_title_edit.setText("Aufgabe Zeitbereich")
    time_domain.time_edit.setPlainText("1")
    QTest.mouseClick(time_domain.calculate_button, Qt.MouseButton.LeftButton)
    time_latex = time_domain.result_edits["latex"].toPlainText()
    assert time_latex.startswith(r"\section*{Aufgabe Zeitbereich}")
    QTest.mouseClick(time_domain.copy_latex_button, Qt.MouseButton.LeftButton)
    assert QApplication.clipboard().text() == time_latex

    state_space = window.state_space_workspace
    state_space.task_title_edit.setText("Aufgabe Zustandsraum")
    state_space.task_combo.setCurrentIndex(1)
    QTest.mouseClick(state_space.calculate_button, Qt.MouseButton.LeftButton)
    state_latex = state_space.result_edits["latex"].toPlainText()
    assert state_latex.startswith(r"\section*{Aufgabe Zustandsraum}")
    QTest.mouseClick(state_space.copy_latex_button, Qt.MouseButton.LeftButton)
    assert QApplication.clipboard().text() == state_latex

    state_space.matrix_a_edit.setPlainText("1,2,3;4,5,6")
    state_space.task_title_edit.setText("Fehlerüberschrift")
    QTest.mouseClick(state_space.calculate_button, Qt.MouseButton.LeftButton)
    assert state_space.result_edits["latex"].toPlainText() == ""
    assert not state_space.copy_latex_button.isEnabled()

    assert window.shutdown()
    window.close()


def test_reset_clears_task_titles_and_disables_copy_buttons() -> None:
    _app()
    window = MainWindow()
    workspaces = (
        (window.workspace, window.workspace.reset_workspace, window.workspace.copy_button),
        (
            window.frequency_workspace,
            window.frequency_workspace.reset_workspace,
            window.frequency_workspace.copy_latex_button,
        ),
        (
            window.stability_workspace,
            window.stability_workspace.reset,
            window.stability_workspace.copy_latex_button,
        ),
        (
            window.time_domain_workspace,
            window.time_domain_workspace.reset,
            window.time_domain_workspace.copy_latex_button,
        ),
        (
            window.state_space_workspace,
            window.state_space_workspace.reset,
            window.state_space_workspace.copy_latex_button,
        ),
    )
    for workspace, reset, copy_button in workspaces:
        workspace.task_title_edit.setText("Alte Aufgabe")
        copy_button.setEnabled(True)
        reset()
        assert workspace.task_title_edit.text() == ""
        assert not copy_button.isEnabled()
    assert window.shutdown()
    window.close()
