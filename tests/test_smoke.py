"""Smoke tests for the desktop package."""

import tomllib
from pathlib import Path

from PySide6.QtWidgets import QApplication

import klausurbotpro
from klausurbotpro.app import APP_NAME, MainWindow, create_main_window


def test_package_metadata() -> None:
    pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    project_version = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))["project"][
        "version"
    ]

    assert klausurbotpro.__version__ == project_version
    assert APP_NAME == "KlausurBotPro"


def test_main_window_has_expected_content_and_shutdown() -> None:
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    assert isinstance(application, QApplication)

    window = create_main_window()

    assert window.windowTitle() == APP_NAME
    assert isinstance(window, MainWindow)
    assert window.centralWidget() is window.workspace_tabs
    assert window.workspace_tabs.widget(0) is window.workspace
    assert window.workspace_tabs.widget(1) is window.frequency_workspace
    assert window.workspace_tabs.tabText(0) == "Transferfunktion"
    assert window.workspace_tabs.tabText(1) == "Frequenzbereich"
    assert window.worker_thread.isRunning()

    assert window.shutdown()
    window.close()
