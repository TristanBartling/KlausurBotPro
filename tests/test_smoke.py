"""Smoke tests for the phase-0 package."""

from PySide6.QtWidgets import QApplication, QLabel

import klausurbotpro
from klausurbotpro.app import APP_NAME, FOUNDATION_MESSAGE, create_main_window


def test_package_metadata() -> None:
    assert klausurbotpro.__version__ == "0.1.0"
    assert APP_NAME == "KlausurBotPro"
    assert FOUNDATION_MESSAGE == "Projektfundament – noch keine Fachmodule"


def test_minimal_window_has_expected_content() -> None:
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    assert isinstance(application, QApplication)

    window = create_main_window()
    label = window.centralWidget()

    assert window.windowTitle() == APP_NAME
    assert isinstance(label, QLabel)
    assert label.text() == FOUNDATION_MESSAGE

    window.close()
