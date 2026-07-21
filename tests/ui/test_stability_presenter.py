"""One compact presenter/GUI-data end-to-end test."""

from PySide6.QtWidgets import QApplication

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
