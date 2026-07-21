"""One real offscreen click path through the visible time-domain workspace."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from klausurbotpro.application import TimeDomainTaskType
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
