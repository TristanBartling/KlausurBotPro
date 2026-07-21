"""One compact presenter/GUI-data end-to-end test."""

from PySide6.QtWidgets import QApplication

from klausurbotpro.application.stability_workflow import StabilityInputDraft
from klausurbotpro.ui.stability_presenter import StabilityPresenter
from klausurbotpro.ui.stability_workspace import StabilityWorkspace


def test_presenter_and_workspace_expose_complete_hurwitz_outputs() -> None:
    application = QApplication.instance() or QApplication([])
    assert isinstance(application, QApplication)
    presenter = StabilityPresenter()
    workspace = StabilityWorkspace(presenter)
    presenter.analyze(
        StabilityInputDraft(
            "s^3+4*s^2+5*s+K_P",
            decision_parameters_text="K_P",
        )
    )
    workspace.render_state(presenter.state)
    assert "0 < K_P" in presenter.state.summary
    assert "Delta_2" in presenter.state.hurwitz_details
    assert "Numerische Kontrolle" in presenter.state.short_solution
    assert "\\boxed" in presenter.state.latex_source
    assert workspace.result_edits["steps"].toPlainText()
    workspace.close()
