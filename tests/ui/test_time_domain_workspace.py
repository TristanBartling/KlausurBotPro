"""One real offscreen click path through the visible time-domain workspace."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from klausurbotpro.application import InputSignalType, TimeDomainTaskType
from klausurbotpro.ui import TimeDomainPresenter, TimeDomainWorkspace


def _app() -> QApplication:
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    assert isinstance(application, QApplication)
    return application


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
