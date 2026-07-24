"""Exactly two real controller-design click paths."""

from dataclasses import replace

from PySide6.QtCore import QEventLoop, Qt, QTimer
from PySide6.QtTest import QSignalSpy, QTest
from PySide6.QtWidgets import QApplication

from klausurbotpro.application import (
    ControllerDesignInputDraft,
    ControllerDesignMethod,
    ControllerDesignWorkflowService,
    ControllerType,
)
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


def test_g1_real_click_opens_frequency_result_and_enables_copy() -> None:
    _app()
    window = MainWindow()
    workspace = window.controller_design_workspace
    assert window.workspace_tabs.tabText(5) == "Reglerauslegung"
    workspace.task_name_edit.setText("SS 2025 Aufgabe 2e")
    _click_and_wait(window)
    frequency = workspace.outputs["frequency"].toPlainText()
    overview = workspace.outputs["overview"].toPlainText()
    assert "ω_* = 0.274747741945" in frequency
    assert "φ_ziel = -160°" in frequency
    assert "|G_0(jω_*)| = 124.48515169" in frequency
    assert "k_P = 1/|G_0(jω_*)| = 0.00803308656835" in frequency
    assert "G_0,neu(s)=k_PG_0(s)" in frequency
    assert "Durchtrittskontrolle: |k_P G_0|=1" in frequency
    assert "Φ_R,ist=20° >= Φ_R,soll=20°" in frequency
    assert "Globale Reservenprüfung: bestanden" in frequency
    assert "Nyquist-Nachprüfung: bestanden" in frequency
    assert "G_R(s)=0.00803308656835" in overview
    assert "0.008033086568345291" not in overview
    assert workspace.result_tabs.currentWidget() is workspace.outputs["frequency"]
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
    assert workspace.result_tabs.currentWidget() is workspace.outputs["parameters"]
    assert workspace.copy_button.isEnabled()
    assert window.shutdown()
    window.close()


def test_course_notation_formula_projection_and_overview_are_visible() -> None:
    _app()
    window = MainWindow()
    workspace = window.controller_design_workspace
    workspace.method_combo.setCurrentIndex(1)
    _app().processEvents()
    assert workspace.rows["dead_time"][0].text() == "K_T [s]:"
    assert workspace.result_tabs.tabText(2) == "Formel und Einsetzen"
    _click_and_wait(window)
    formula = workspace.outputs["formula"].toPlainText()
    overview = workspace.outputs["overview"].toPlainText()
    steps = workspace.outputs["steps"].toPlainText()
    assert formula.index("Allgemeine Formel:") < formula.index("Einsetzen:")
    assert "K_S" in formula and "k_P" in formula
    assert "Primäres Ergebnis: G_R(s)=" in overview
    assert "Gültigkeitsstatus: erfüllt" in overview
    assert "r=L/T" not in formula + steps
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
    assert (
        "P-Verstärkung für gewünschte Phasenreserve" in workspace.outputs["overview"].toPlainText()
    )
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


def test_source_domain_failure_hides_internal_code_in_diagnostics_tab() -> None:
    _app()
    window = MainWindow()
    workspace = window.controller_design_workspace
    workspace.method_combo.setCurrentIndex(1)
    workspace.controller_type_combo.setCurrentIndex(1)
    workspace.dead_time_edit.setText("36")
    _click_and_wait(window)
    assert workspace.latex_output.toPlainText() == ""
    assert not workspace.copy_button.isEnabled()
    diagnostics = workspace.outputs["diagnostics"].toPlainText()
    assert "K_T: Die strikte Bedingung K_T/T < 0,5 ist nicht erfüllt" in diagnostics
    assert "OUTSIDE_SOURCE_DOMAIN" not in diagnostics
    assert "OUTSIDE_SOURCE_DOMAIN" not in workspace.outputs["overview"].toPlainText()
    assert workspace.result_tabs.currentWidget() is workspace.outputs["diagnostics"]
    assert window.shutdown()
    window.close()


def test_unit_failure_hides_internal_code_and_disables_copy() -> None:
    _app()
    window = MainWindow()
    workspace = window.controller_design_workspace
    workspace.method_combo.setCurrentIndex(3)
    workspace.dead_time_edit.setText("12 ms")
    _click_and_wait(window)
    diagnostics = workspace.outputs["diagnostics"].toPlainText()
    assert diagnostics == "Zeitwerte müssen als reine Zahlen in Sekunden eingegeben werden."
    assert "UNIT_MISMATCH" not in diagnostics
    assert workspace.result_tabs.currentWidget() is workspace.outputs["diagnostics"]
    assert not workspace.copy_button.isEnabled()
    assert window.shutdown()
    window.close()


def test_frequency_tab_projects_precomputed_contract_without_recalculation() -> None:
    _app()
    window = MainWindow()
    result = ControllerDesignWorkflowService().run(
        ControllerDesignInputDraft(
            ControllerDesignMethod.P_PHASE_MARGIN,
            ControllerType.P,
            "Projektionsprüfung",
            "100",
            "s*(10*s+1)",
            (),
            "20",
            "1e-4",
            "1e2",
            "32",
        )
    )
    projection = replace(
        result.frequency_presentations[0],
        target_frequency="SENTINEL_OMEGA",
        original_magnitude="SENTINEL_MAGNITUDE",
        positive_k_p="SENTINEL_GAIN",
    )
    window.controller_design_presenter.accept_result(
        replace(result, frequency_presentations=(projection,))
    )
    frequency = window.controller_design_workspace.outputs["frequency"].toPlainText()
    assert "SENTINEL_OMEGA" in frequency
    assert "SENTINEL_MAGNITUDE" in frequency
    assert "SENTINEL_GAIN" in frequency
    assert window.shutdown()
    window.close()
