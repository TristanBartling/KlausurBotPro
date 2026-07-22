"""Exactly two real state-space click paths."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from klausurbotpro.ui.main_window import MainWindow


def _app() -> QApplication:
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    assert isinstance(application, QApplication)
    return application


def test_s1_real_click_opens_latex_and_enables_copy() -> None:
    _app()
    window = MainWindow()
    workspace = window.state_space_workspace
    workspace.order_combo.setCurrentIndex(2)
    for edit, value in zip(workspace.coefficient_edits, ("4", "-8", "0", "2"), strict=False):
        edit.setText(value)
    workspace.input_factor_edit.setText("2")

    QTest.mouseClick(workspace.calculate_button, Qt.MouseButton.LeftButton)
    _app().processEvents()

    assert "[-2, 4, 0]" in workspace.result_edits["matrices"].toPlainText()
    assert "1/(s**3 - 4*s + 2)" in workspace.result_edits["transfer"].toPlainText()
    assert "nicht asymptotisch stabil" in workspace.result_edits["eigen"].toPlainText()
    assert workspace.result_edits["latex"].toPlainText()
    assert workspace.result_tabs.currentWidget() is workspace.result_edits["latex"]
    assert workspace.copy_latex_button.isEnabled()
    assert window.shutdown()
    window.close()


def test_s5_real_click_exposes_hidden_unstable_mode() -> None:
    _app()
    window = MainWindow()
    workspace = window.state_space_workspace
    workspace.task_combo.setCurrentIndex(1)
    workspace.matrix_a_edit.setPlainText("-1, 0; 0, 1")
    workspace.vector_b_edit.setPlainText("1; 0")
    workspace.vector_c_edit.setPlainText("1, 0")
    workspace.scalar_d_edit.setText("0")

    QTest.mouseClick(workspace.calculate_button, Qt.MouseButton.LeftButton)
    _app().processEvents()

    transfer = workspace.result_edits["transfer"].toPlainText()
    assert "1/(s + 1)" in transfer
    assert "versteckte instabile Mode bei s=1" in transfer
    assert "1" in workspace.result_edits["eigen"].toPlainText()
    assert workspace.result_tabs.currentWidget() is workspace.result_edits["latex"]
    assert window.shutdown()
    window.close()
