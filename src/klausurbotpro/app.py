"""PySide6 application composition root."""

import sys
from collections.abc import Sequence

from PySide6.QtWidgets import QApplication

from klausurbotpro.ui import MainWindow
from klausurbotpro.ui.main_window import APP_NAME


def create_main_window() -> MainWindow:
    """Create the first usable transfer-function desktop window."""

    return MainWindow()


def main(argv: Sequence[str] | None = None) -> int:
    """Start the minimal desktop application and return its exit code."""
    application = QApplication(list(argv) if argv is not None else sys.argv)
    window = create_main_window()
    window.show()
    exit_code = application.exec()
    window.shutdown()
    return exit_code


__all__ = ["APP_NAME", "MainWindow", "create_main_window", "main"]
