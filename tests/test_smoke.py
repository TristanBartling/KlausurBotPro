"""Smoke tests for the desktop package."""

from PySide6.QtWidgets import QApplication

import klausurbotpro
from klausurbotpro.app import APP_NAME, MainWindow, create_main_window


def test_package_metadata() -> None:
    assert klausurbotpro.__version__ == "0.1.0"
    assert APP_NAME == "KlausurBotPro"


def test_main_window_has_expected_content_and_shutdown() -> None:
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    assert isinstance(application, QApplication)

    window = create_main_window()

    assert window.windowTitle() == APP_NAME
    assert isinstance(window, MainWindow)
    assert window.centralWidget() is window.workspace
    assert window.worker_thread.isRunning()

    assert window.shutdown()
    window.close()
