"""One compact presenter/GUI-data end-to-end test."""

from PySide6.QtCore import QEventLoop, Qt, QTimer
from PySide6.QtTest import QSignalSpy, QTest
from PySide6.QtWidgets import QApplication

from klausurbotpro.application.stability_workflow import (
    StabilityInputDraft,
    StabilityInputMode,
    StabilityMethod,
)
from klausurbotpro.domain.parameter_core_contracts import AnalysisTarget
from klausurbotpro.ui.main_window import MainWindow
from klausurbotpro.ui.stability_presenter import StabilityPresenter
from klausurbotpro.ui.stability_workspace import StabilityWorkspace


def test_presenter_and_workspace_expose_complete_hurwitz_outputs() -> None:
    application = QApplication.instance() or QApplication([])
    assert isinstance(application, QApplication)
    presenter = StabilityPresenter()
    workspace = StabilityWorkspace(presenter)
    workspace.polynomial_edit.setPlainText("s^3+4*s^2+5*s+K_P")
    workspace.parameters_edit.setText("K_P")
    workspace.role_combo.setCurrentIndex(
        workspace.role_combo.findText("Rohes charakteristisches Polynom")
    )
    workspace.target_combo.setCurrentIndex(
        workspace.target_combo.findText("Interne asymptotische Stabilität")
    )

    workspace.analyze_button.click()

    assert not presenter.state.failed
    assert "0 < K_P" in workspace.result_edits["summary"].toPlainText()
    assert "K_P < 20" in workspace.result_edits["summary"].toPlainText()
    workspace.close()


def test_real_routh_click_path_and_method_tab_switching() -> None:
    application = QApplication.instance() or QApplication([])
    assert isinstance(application, QApplication)
    presenter = StabilityPresenter()
    workspace = StabilityWorkspace(presenter)
    workspace.method_combo.setCurrentIndex(workspace.method_combo.findText("Routh"))
    workspace.polynomial_edit.setPlainText("s^3+4*s^2+5*s+K_P")
    workspace.parameters_edit.setText("K_P")

    QTest.mouseClick(workspace.analyze_button, Qt.MouseButton.LeftButton)

    routh_index = workspace.result_tabs.indexOf(workspace.result_edits["routh"])
    hurwitz_index = workspace.result_tabs.indexOf(workspace.result_edits["hurwitz"])
    assert not presenter.state.failed
    assert workspace.result_tabs.isTabVisible(routh_index)
    assert not workspace.result_tabs.isTabVisible(hurwitz_index)
    assert "(20-K_P)/4" in workspace.result_edits["routh"].toPlainText()
    assert "0 < K_P" in workspace.result_edits["region"].toPlainText()
    assert presenter.state.latex_source
    assert workspace.copy_latex_button.isEnabled()

    workspace.method_combo.setCurrentIndex(workspace.method_combo.findText("Hurwitz"))
    QTest.mouseClick(workspace.analyze_button, Qt.MouseButton.LeftButton)
    assert workspace.result_tabs.isTabVisible(hurwitz_index)
    assert not workspace.result_tabs.isTabVisible(routh_index)
    assert presenter.state.hurwitz_details
    workspace.close()


def test_r3_short_solution_reports_both_rhp_counts_in_german() -> None:
    presenter = StabilityPresenter()
    presenter.analyze(
        StabilityInputDraft(
            "s^3+2*s^2-s+2",
            method=StabilityMethod.ROUTH,
        )
    )

    assert "Nicht intern asymptotisch stabil" in presenter.state.short_solution
    assert "Vorzeichenwechsel: 2" in presenter.state.short_solution
    assert "Routh-RHP-Polzahl: 2" in presenter.state.short_solution
    assert "Numerische RHP-Polzahl: 2" in presenter.state.short_solution
    assert "Numerische Kontrolle: konsistent" in presenter.state.short_solution


def test_r7_special_case_has_no_python_none_and_disables_latex_copy() -> None:
    application = QApplication.instance() or QApplication([])
    assert isinstance(application, QApplication)
    presenter = StabilityPresenter()
    workspace = StabilityWorkspace(presenter)
    workspace.method_combo.setCurrentIndex(workspace.method_combo.findText("Routh"))
    workspace.polynomial_edit.setPlainText("s^3+2*s^2+s+2")

    QTest.mouseClick(workspace.analyze_button, Qt.MouseButton.LeftButton)

    normal_output = "\n".join(
        edit.toPlainText()
        for name, edit in workspace.result_edits.items()
        if name != "diagnostics"
    )
    assert "Vollständige Nullzeile" in normal_output
    assert "Hilfspolynomverfahren" in normal_output
    assert "None" not in normal_output
    assert presenter.state.latex_source == ""
    assert not workspace.copy_latex_button.isEnabled()
    workspace.close()


def test_transfer_input_mode_switches_label_and_reset_clears_all_results() -> None:
    application = QApplication.instance() or QApplication([])
    assert isinstance(application, QApplication)
    presenter = StabilityPresenter()
    workspace = StabilityWorkspace(presenter)
    workspace.input_mode_combo.setCurrentIndex(
        workspace.input_mode_combo.findText("Führungsübertragungsfunktion")
    )
    workspace.polynomial_edit.setPlainText("(s+1)/(s+2)")
    workspace.task_title_edit.setText("Aufgabe Transfer")
    workspace.target_combo.setCurrentIndex(
        workspace.target_combo.findText("E/A-asymptotische Stabilität")
    )

    workspace.analyze_button.click()

    assert workspace.input_label.text() == "Führungsübertragungsfunktion:"
    assert presenter.state.latex_source
    assert workspace.copy_latex_button.isEnabled()
    assert workspace.result_edits["latex"].toPlainText().count(
        r"\section*{Aufgabe Transfer}"
    ) == 1
    workspace.reset()
    assert workspace.input_mode_combo.currentIndex() == 0
    assert workspace.variable_edit.text() == "s"
    assert workspace.polynomial_edit.toPlainText() == ""
    assert workspace.result_edits["summary"].toPlainText() == "Bereit."
    assert all(
        not edit.toPlainText()
        for name, edit in workspace.result_edits.items()
        if name != "summary"
    )
    assert not workspace.copy_latex_button.isEnabled()
    workspace.close()


def test_transfer_input_is_locked_during_persistent_worker_run() -> None:
    application = QApplication.instance() or QApplication([])
    assert isinstance(application, QApplication)
    window = MainWindow()
    workspace = window.stability_workspace
    workspace.input_mode_combo.setCurrentIndex(
        workspace.input_mode_combo.findText("Führungsübertragungsfunktion")
    )
    workspace.polynomial_edit.setPlainText("(s+K)/(s^2+3*s+K)")
    workspace.parameters_edit.setText("K")
    workspace.target_combo.setCurrentIndex(
        workspace.target_combo.findText("E/A-asymptotische Stabilität")
    )
    completed = QSignalSpy(window.stability_worker.completed)
    loop = QEventLoop()
    window.stability_worker.completed.connect(loop.quit)

    QTest.mouseClick(workspace.analyze_button, Qt.MouseButton.LeftButton)

    assert not workspace.polynomial_edit.isEnabled()
    assert not workspace.input_mode_combo.isEnabled()
    assert not workspace.reset_button.isEnabled()
    QTimer.singleShot(15_000, loop.quit)
    loop.exec()
    application.processEvents()
    assert completed.count() == 1
    assert workspace.polynomial_edit.isEnabled()
    assert workspace.copy_latex_button.isEnabled()
    assert window.shutdown()
    window.close()


def test_golden_user_tabs_do_not_expose_sympy_relations_or_enum_values() -> None:
    presenter = StabilityPresenter()
    presenter.analyze(
        StabilityInputDraft(
            decision_parameters_text="a,K",
            analysis_target=AnalysisTarget.EXTERNAL_BIBO,
            input_mode=StabilityInputMode.TRANSFER_FUNCTION,
            transfer_function_text=(
                "(s^2+2*K*s+K^2)/"
                "(((s+3)*(s+2*a)*(s+5)+8*K)*(s+K))"
            ),
        )
    )

    user_text = "\n".join(
        (
            presenter.state.summary,
            presenter.state.parameter_region,
            presenter.state.worked_steps,
        )
    )
    assert "a > -15/16" in user_text
    assert "-15*a/4 < K < (2*a+3)*(2*a+5)" in user_text
    assert " & " not in user_text
    assert "oo" not in user_text
    assert "reduced_transfer_denominator" not in user_text
