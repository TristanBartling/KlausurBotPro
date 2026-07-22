"""Exactly two real controller-design click paths."""

from PySide6.QtCore import QEventLoop, Qt, QTimer
from PySide6.QtTest import QSignalSpy, QTest
from PySide6.QtWidgets import QApplication

from klausurbotpro.ui.main_window import MainWindow


def _app() -> QApplication:
    application = QApplication.instance() or QApplication([])
    assert isinstance(application, QApplication)
    return application


def _click_and_wait(window: MainWindow) -> None:
    completed = QSignalSpy(window.controller_design_worker.completed)
    loop = QEventLoop()
    window.controller_design_worker.completed.connect(loop.quit)
    QTest.mouseClick(window.controller_design_workspace.calculate_button, Qt.MouseButton.LeftButton)
    QTimer.singleShot(20_000, loop.quit)
    loop.exec()
    _app().processEvents()
    assert completed.count() == 1


def test_g1_real_click_opens_latex_and_enables_copy() -> None:
    _app()
    window = MainWindow()
    workspace = window.controller_design_workspace
    assert window.workspace_tabs.tabText(5) == "Reglerauslegung"
    workspace.task_name_edit.setText("SS 2025 Aufgabe 2e")
    _click_and_wait(window)
    frequency = workspace.outputs["frequency"].toPlainText()
    assert "0.008033086" in frequency
    assert "Φ_R=20" in frequency
    assert workspace.result_tabs.currentWidget() is workspace.latex_output
    assert workspace.latex_output.toPlainText().count(r"\section*{") == 1
    assert workspace.copy_button.isEnabled()
    assert window.shutdown()
    window.close()


def test_g3_real_click_shows_exact_parallel_and_ideal_forms() -> None:
    _app()
    window = MainWindow()
    workspace = window.controller_design_workspace
    workspace.task_name_edit.setText("WS 2025/26 Aufgabe 4c")
    workspace.method_combo.setCurrentIndex(3)
    workspace.controller_type_combo.setCurrentIndex(2)
    _click_and_wait(window)
    parameters = workspace.outputs["parameters"].toPlainText()
    latex = workspace.latex_output.toPlainText()
    assert "49/9" in parameters
    assert "2107/10692" in parameters
    assert "G_R(s)" in parameters
    assert "49}{9" in latex
    assert workspace.result_tabs.currentWidget() is workspace.latex_output
    assert workspace.copy_button.isEnabled()
    assert window.shutdown()
    window.close()
