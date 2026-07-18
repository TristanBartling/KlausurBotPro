"""Minimal PySide6 application for the technology-validation phase."""

import sys
from collections.abc import Sequence

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow

APP_NAME = "KlausurBotPro"
FOUNDATION_MESSAGE = "Projektfundament – noch keine Fachmodule"


def create_main_window() -> QMainWindow:
    """Create the minimal phase-0.5 main window."""
    window = QMainWindow()
    window.setWindowTitle(APP_NAME)
    message = QLabel(FOUNDATION_MESSAGE)
    message.setAlignment(Qt.AlignmentFlag.AlignCenter)
    window.setCentralWidget(message)
    window.resize(640, 360)
    return window


def main(argv: Sequence[str] | None = None) -> int:
    """Start the minimal desktop application and return its exit code."""
    application = QApplication(list(argv) if argv is not None else sys.argv)
    window = create_main_window()
    window.show()
    return application.exec()
