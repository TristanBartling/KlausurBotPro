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
    workspace.method_combo.setCurrentIndex(3)
    workspace.controller_type_combo.setCurrentIndex(2)
    _click_and_wait(window)
    parameters = workspace.outputs["parameters"].toPlainText()
    latex = workspace.latex_output.toPlainText()
    assert "49/9" in parameters
    assert "2107/10692" in parameters
    assert "G_R(s)" in parameters
    assert "49}{9" in latex
    assert r"\section*{" not in latex
    assert workspace.result_tabs.currentWidget() is workspace.latex_output
    assert workspace.copy_button.isEnabled()
    assert window.shutdown()
    window.close()


def test_running_uses_input_snapshot_and_reset_restores_every_default() -> None:
    _app()
    window = MainWindow()
    workspace = window.controller_design_workspace
    completed = QSignalSpy(window.controller_design_worker.completed)
    loop = QEventLoop()
    window.controller_design_worker.completed.connect(loop.quit)
    workspace.task_name_edit.setText("Snapshot-Aufgabe")
    QTest.mouseClick(workspace.calculate_button, Qt.MouseButton.LeftButton)
    assert not workspace.method_combo.isEnabled()
    assert not workspace.controller_type_combo.isEnabled()
    assert not workspace.reset_button.isEnabled()
    assert not workspace.calculate_button.isEnabled()
    assert all(not row[1].isEnabled() for row in workspace.rows.values())
    workspace.method_combo.setCurrentIndex(3)
    QTimer.singleShot(20_000, loop.quit)
    loop.exec()
    _app().processEvents()
    assert completed.count() == 1
    assert "P-Verstärkung für gewünschte Phasenreserve" in workspace.outputs[
        "overview"
    ].toPlainText()
    assert workspace.method_combo.isEnabled()

    workspace.parameters_edit.setText("a=2")
    workspace.process_gain_edit.setText("99")
    workspace.dead_time_edit.setText("98")
    workspace.lag_time_edit.setText("97")
    workspace.critical_gain_edit.setText("96")
    workspace.critical_period_edit.setText("95")
    QTest.mouseClick(workspace.reset_button, Qt.MouseButton.LeftButton)
    assert workspace.task_name_edit.text() == ""
    assert workspace.method_combo.currentIndex() == 0
    assert workspace.controller_type_combo.currentIndex() == 2
    assert workspace.numerator_edit.text() == "100"
    assert workspace.denominator_edit.text() == "s*(10*s+1)"
    assert workspace.parameters_edit.text() == ""
    assert workspace.target_margin_edit.text() == "20"
    assert workspace.omega_min_edit.text() == "1e-4"
    assert workspace.omega_max_edit.text() == "1e2"
    assert workspace.points_per_decade_edit.text() == "32"
    assert workspace.process_gain_edit.text() == "1.8"
    assert workspace.dead_time_edit.text() == "12"
    assert workspace.lag_time_edit.text() == "72"
    assert workspace.critical_gain_edit.text() == "1.62"
    assert workspace.critical_period_edit.text() == "3"
    assert all(not output.toPlainText() for output in workspace.outputs.values())
    assert not workspace.copy_button.isEnabled()
    assert not workspace.rows["numerator"][1].isHidden()
    assert workspace.rows["process_gain"][1].isHidden()
    assert workspace.controller_type_combo.isHidden()
    assert window.shutdown()
    window.close()


def test_source_domain_failure_keeps_code_only_in_diagnostics_tab() -> None:
    _app()
    window = MainWindow()
    workspace = window.controller_design_workspace
    workspace.method_combo.setCurrentIndex(1)
    workspace.controller_type_combo.setCurrentIndex(1)
    workspace.dead_time_edit.setText("36")
    _click_and_wait(window)
    assert workspace.latex_output.toPlainText() == ""
    assert not workspace.copy_button.isEnabled()
    assert "OUTSIDE_SOURCE_DOMAIN" in workspace.outputs["diagnostics"].toPlainText()
    assert "OUTSIDE_SOURCE_DOMAIN" not in workspace.outputs["overview"].toPlainText()
    assert window.shutdown()
    window.close()
