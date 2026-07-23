"""One real offscreen click path through the visible time-domain workspace."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from klausurbotpro.application import (
    InputSignalType,
    OdeAnalysisGoal,
    TimeDomainInputDraft,
    TimeDomainTaskType,
)
from klausurbotpro.ui import TimeDomainPresenter, TimeDomainWorkspace


def _app() -> QApplication:
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    assert isinstance(application, QApplication)
    return application


class _RecordingTimeDomainPresenter(TimeDomainPresenter):
    def __init__(self) -> None:
        super().__init__()
        self.last_draft: TimeDomainInputDraft | None = None

    def calculate(self, draft: TimeDomainInputDraft) -> None:
        self.last_draft = draft
        super().calculate(draft)


def test_rf06_real_calculate_button_click_updates_time_and_end_value() -> None:
    application = _app()
    presenter = TimeDomainPresenter()
    workspace = TimeDomainWorkspace(presenter)
    workspace.show()
    index = workspace.task_combo.findData(TimeDomainTaskType.STEP_RESPONSE.value)
    workspace.task_combo.setCurrentIndex(index)
    workspace.system_edit.setPlainText("1/(2*s+1)")
    workspace.step_amplitude_edit.setText("0.1")

    QTest.mouseClick(workspace.calculate_button, Qt.MouseButton.LeftButton)
    application.processEvents()

    assert not presenter.state.failed
    assert "exp(-t/2)" in workspace.result_edits["time"].toPlainText()
    assert "Stationärer Endwert: 1/10" in workspace.result_edits[
        "summary"
    ].toPlainText()
    assert "Traceback" not in workspace.result_edits["diagnostics"].toPlainText()
    workspace.close()


def test_rf03_real_calculate_button_click_solves_structured_ode() -> None:
    application = _app()
    presenter = TimeDomainPresenter()
    workspace = TimeDomainWorkspace(presenter)
    workspace.show()
    workspace.task_combo.setCurrentIndex(workspace.task_combo.findData(TimeDomainTaskType.SOLVE_ODE.value))
    workspace.output_order_combo.setCurrentIndex(workspace.output_order_combo.findData(2))
    workspace.input_order_combo.setCurrentIndex(workspace.input_order_combo.findData(0))
    for edit, text in zip(workspace.output_coefficient_edits, ("1", "2", "1"), strict=False):
        edit.setText(text)
    workspace.input_coefficient_edits[0].setText("1")
    workspace.output_initial_edits[0].setText("0")
    workspace.output_initial_edits[1].setText("1")
    workspace.ode_signal_combo.setCurrentIndex(workspace.ode_signal_combo.findData(InputSignalType.EXPONENTIAL.value))
    workspace.ode_amplitude_edit.setText("9")
    workspace.ode_rate_edit.setText("2")

    assert "0*y" not in workspace.ode_preview.text()
    assert workspace.ode_preview.text() == "y''(t) + 2*y'(t) + y(t) = u(t)"

    QTest.mouseClick(workspace.calculate_button, Qt.MouseButton.LeftButton)
    application.processEvents()

    assert not presenter.state.failed
    assert "exp(2*t)" in workspace.result_edits["summary"].toPlainText()
    assert "DGL-Residuum" in workspace.result_edits["checks"].toPlainText()
    assert "Traceback" not in workspace.result_edits["diagnostics"].toPlainText()
    workspace.close()


def test_ode_analysis_goal_is_visible_only_for_solve_ode_and_defaults_to_time() -> None:
    _app()
    workspace = TimeDomainWorkspace(TimeDomainPresenter())
    workspace.show()
    workspace.task_combo.setCurrentIndex(
        workspace.task_combo.findData(TimeDomainTaskType.SOLVE_ODE.value)
    )
    assert workspace.ode_analysis_goal_combo.isVisible()
    assert (
        workspace.ode_analysis_goal_combo.currentData()
        == OdeAnalysisGoal.TIME_RESPONSE.value
    )

    workspace.task_combo.setCurrentIndex(
        workspace.task_combo.findData(
            TimeDomainTaskType.TRANSFER_FUNCTION_FROM_ODE.value
        )
    )
    assert not workspace.ode_analysis_goal_combo.isVisible()
    workspace.close()


def test_ode_signal_fields_are_visible_only_when_relevant() -> None:
    _app()
    workspace = TimeDomainWorkspace(TimeDomainPresenter())
    workspace.show()
    workspace.task_combo.setCurrentIndex(
        workspace.task_combo.findData(TimeDomainTaskType.SOLVE_ODE.value)
    )
    expected = {
        InputSignalType.ZERO: (False, False, False, False),
        InputSignalType.STEP: (True, False, False, False),
        InputSignalType.EXPONENTIAL: (True, True, False, False),
        InputSignalType.POLYNOMIAL: (False, False, True, False),
        InputSignalType.SINUS: (True, True, False, False),
        InputSignalType.COSINUS: (True, True, False, False),
        InputSignalType.IMAGE_EXPRESSION: (False, False, False, True),
    }
    for signal_type, visibility in expected.items():
        workspace.ode_signal_combo.setCurrentIndex(
            workspace.ode_signal_combo.findData(signal_type.value)
        )
        actual = (
            workspace.ode_amplitude_edit.isVisible(),
            workspace.ode_rate_edit.isVisible(),
            workspace._rows["polynomial"][1].isVisible(),
            workspace.input_edit.isVisible(),
        )
        assert actual == visibility
    assert workspace._rows["input"][0].text() == "Bildbereichseingang U(s):"
    workspace.close()


def test_ode_coefficient_and_initial_labels_are_readable() -> None:
    _app()
    workspace = TimeDomainWorkspace(TimeDomainPresenter())
    output_layout = workspace.output_coefficient_edits[0].parentWidget().layout()
    initial_layout = workspace.output_initial_edits[0].parentWidget().layout()
    assert output_layout.labelForField(workspace.output_coefficient_edits[0]).text() == (
        "a_0 · y(t)"
    )
    assert output_layout.labelForField(workspace.output_coefficient_edits[2]).text() == (
        "a_2 · y''(t)"
    )
    assert output_layout.labelForField(workspace.output_coefficient_edits[4]).text() == (
        "a_4 · y^(4)(t)"
    )
    assert initial_layout.labelForField(workspace.output_initial_edits[0]).text() == (
        "y(0+):"
    )
    assert initial_layout.labelForField(workspace.output_initial_edits[1]).text() == (
        "y'(0+):"
    )
    workspace.close()


def test_ode_result_tabs_follow_selected_goal() -> None:
    _app()
    workspace = TimeDomainWorkspace(TimeDomainPresenter())
    workspace.show()
    workspace.task_combo.setCurrentIndex(
        workspace.task_combo.findData(TimeDomainTaskType.SOLVE_ODE.value)
    )

    workspace.ode_analysis_goal_combo.setCurrentIndex(
        workspace.ode_analysis_goal_combo.findData(
            OdeAnalysisGoal.IMAGE_EQUATION.value
        )
    )
    assert workspace.result_tabs.isTabVisible(
        workspace.result_tabs.indexOf(workspace.result_edits["equation"])
    )
    assert not workspace.result_tabs.isTabVisible(
        workspace.result_tabs.indexOf(workspace.result_edits["partial"])
    )
    assert not workspace.result_tabs.isTabVisible(
        workspace.result_tabs.indexOf(workspace.result_edits["time"])
    )

    workspace.ode_analysis_goal_combo.setCurrentIndex(
        workspace.ode_analysis_goal_combo.findData(
            OdeAnalysisGoal.PARTIAL_FRACTIONS.value
        )
    )
    assert workspace.result_tabs.isTabVisible(
        workspace.result_tabs.indexOf(workspace.result_edits["partial"])
    )
    assert not workspace.result_tabs.isTabVisible(
        workspace.result_tabs.indexOf(workspace.result_edits["time"])
    )
    workspace.close()


def test_direct_image_input_output_goal_click_ends_at_y_of_s() -> None:
    application = _app()
    presenter = TimeDomainPresenter()
    workspace = TimeDomainWorkspace(presenter)
    workspace.show()
    workspace.task_combo.setCurrentIndex(
        workspace.task_combo.findData(TimeDomainTaskType.SOLVE_ODE.value)
    )
    workspace.ode_analysis_goal_combo.setCurrentIndex(
        workspace.ode_analysis_goal_combo.findData(
            OdeAnalysisGoal.OUTPUT_LAPLACE.value
        )
    )
    workspace.output_order_combo.setCurrentIndex(
        workspace.output_order_combo.findData(2)
    )
    for edit, text in zip(
        workspace.output_coefficient_edits, ("0", "4", "2"), strict=False
    ):
        edit.setText(text)
    workspace.input_coefficient_edits[0].setText("1")
    workspace.output_initial_edits[0].setText("y0")
    workspace.output_initial_edits[1].setText("v0")
    workspace.ode_signal_combo.setCurrentIndex(
        workspace.ode_signal_combo.findData(
            InputSignalType.IMAGE_EXPRESSION.value
        )
    )
    workspace.input_edit.setPlainText("1/(s-8)^2")

    assert not workspace.ode_amplitude_edit.isVisible()
    QTest.mouseClick(workspace.calculate_button, Qt.MouseButton.LeftButton)
    application.processEvents()

    assert not presenter.state.failed
    assert "Endergebnis: Y(s) =" in workspace.result_edits[
        "summary"
    ].toPlainText()
    assert not workspace.result_tabs.isTabVisible(
        workspace.result_tabs.indexOf(workspace.result_edits["partial"])
    )
    assert not workspace.result_tabs.isTabVisible(
        workspace.result_tabs.indexOf(workspace.result_edits["time"])
    )
    assert "inverse Laplace" not in workspace.result_edits[
        "steps"
    ].toPlainText().lower()
    workspace.close()


def test_rf04_real_checkbox_click_replaces_error_with_transfer_function() -> None:
    application = _app()
    presenter = _RecordingTimeDomainPresenter()
    workspace = TimeDomainWorkspace(presenter)
    workspace.show()
    workspace.task_combo.setCurrentIndex(
        workspace.task_combo.findData(TimeDomainTaskType.SOLVE_ODE.value)
    )
    workspace.output_initial_edits[1].setText("1")
    workspace.task_combo.setCurrentIndex(
        workspace.task_combo.findData(
            TimeDomainTaskType.TRANSFER_FUNCTION_FROM_ODE.value
        )
    )
    workspace.output_name_edit.setText("phi_G")
    workspace.input_name_edit.setText("F_A")
    workspace.output_order_combo.setCurrentIndex(
        workspace.output_order_combo.findData(2)
    )
    workspace.input_order_combo.setCurrentIndex(workspace.input_order_combo.findData(0))
    for edit, text in zip(
        workspace.output_coefficient_edits,
        ("g*(m_K+m_G)", "-d_K", "m_K*l"),
        strict=False,
    ):
        edit.setText(text)
    workspace.input_coefficient_edits[0].setText("-1")
    workspace.assumptions_edit.setText("m_K > 0; l > 0")

    assert workspace.zero_state_checkbox.isChecked() is False
    QTest.mouseClick(workspace.calculate_button, Qt.MouseButton.LeftButton)
    application.processEvents()
    assert "sichtbare Bestätigung" in workspace.result_edits[
        "diagnostics"
    ].toPlainText()

    QTest.mouseClick(workspace.zero_state_checkbox, Qt.MouseButton.LeftButton)
    assert workspace.zero_state_checkbox.isChecked() is True
    QTest.mouseClick(workspace.calculate_button, Qt.MouseButton.LeftButton)
    application.processEvents()

    assert presenter.last_draft is not None
    assert presenter.last_draft.zero_state_confirmed is True
    assert presenter.last_draft.output_initial_texts == ()
    assert not presenter.state.failed
    assert "G_S(s) = Phi_G(s)/F_A(s) = -1/" in workspace.result_edits[
        "summary"
    ].toPlainText()
    assert "sichtbare Bestätigung" not in workspace.result_edits[
        "diagnostics"
    ].toPlainText()
    assert "Traceback" not in workspace.result_edits["diagnostics"].toPlainText()
    workspace.close()
