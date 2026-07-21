"""One real offscreen click path through the visible time-domain workspace."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from klausurbotpro.application import (
    InputSignalType,
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
