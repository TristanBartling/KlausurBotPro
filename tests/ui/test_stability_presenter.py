"""One compact presenter/GUI-data end-to-end test."""

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from klausurbotpro.application.stability_workflow import (
    StabilityInputDraft,
    StabilityMethod,
)
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
