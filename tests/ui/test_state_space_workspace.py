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
    workspace.task_title_edit.setText("Aufgabe 1a – Regelungsnormalform")
    workspace.order_combo.setCurrentIndex(2)
    for edit, value in zip(workspace.coefficient_edits, ("4", "-8", "0", "2"), strict=False):
        edit.setText(value)
    workspace.input_factor_edit.setText("2")

    QTest.mouseClick(workspace.calculate_button, Qt.MouseButton.LeftButton)
    _app().processEvents()

    assert "[-2, 4, 0]" in workspace.result_edits["matrices"].toPlainText()
    assert "A_R" in workspace.result_edits["matrices"].toPlainText()
    definitions = workspace.result_edits["ode"].toPlainText()
    assert "x_1(t)=y(t)" in definitions
    assert "x_2(t)=y'(t)" in definitions
    assert "x_3(t)=y''(t)" in definitions
    assert "1/(s**3 - 4*s + 2)" in workspace.result_edits["transfer"].toPlainText()
    assert "nicht asymptotisch stabil" in workspace.result_edits["eigen"].toPlainText()
    latex = workspace.result_edits["latex"].toPlainText()
    assert latex.startswith(r"\section*{Aufgabe 1a – Regelungsnormalform}")
    assert latex.count(r"\section*{") == 1
    assert r"x_{1}(t)=y(t)" in latex
    assert r"x_{2}(t)=\dot{y}(t)" in latex
    assert r"x_{3}(t)=\ddot{y}(t)" in latex
    assert workspace.result_tabs.currentWidget() is workspace.result_edits["latex"]
    assert workspace.copy_latex_button.isEnabled()
    assert window.shutdown()
    window.close()


def test_s5_real_click_exposes_hidden_unstable_mode() -> None:
    _app()
    window = MainWindow()
    workspace = window.state_space_workspace
    workspace.task_title_edit.setText("Aufgabe 1b – Zustandsraum")
    workspace.task_combo.setCurrentIndex(1)
    workspace.matrix_a_edit.setPlainText("-1, 0; 0, 1")
    workspace.vector_b_edit.setPlainText("1; 0")
    workspace.vector_c_edit.setPlainText("1, 0")
    workspace.scalar_d_edit.setText("0")

    QTest.mouseClick(workspace.calculate_button, Qt.MouseButton.LeftButton)
    _app().processEvents()

    transfer = workspace.result_edits["transfer"].toPlainText()
    matrices = workspace.result_edits["matrices"].toPlainText()
    assert "A_R" not in matrices
    assert "b_R" not in matrices
    assert "c_R^T" not in matrices
    assert matrices.startswith("A = [[-1, 0], [0, 1]]")
    assert "1/(s + 1)" in transfer
    assert "versteckte instabile Mode bei s=1" in transfer
    assert "1" in workspace.result_edits["eigen"].toPlainText()
    latex = workspace.result_edits["latex"].toPlainText()
    assert latex.count(r"\section*{") == 1
    assert "A_R" not in latex
    assert "b_R" not in latex
    assert "c_R^T" not in latex
    reduced_start = latex.index(r"\[G_{\mathrm{red}}(s)")
    reduced_end = latex.index(r"\]", reduced_start)
    warning_start = latex.index(r"\textbf{Hinweis:}")
    assert warning_start > reduced_end
    assert r"\boxed{A=" not in latex
    assert workspace.result_tabs.currentWidget() is workspace.result_edits["latex"]
    assert window.shutdown()
    window.close()


def test_stability_target_hides_transfer_and_opens_stability_tab() -> None:
    _app()
    window = MainWindow()
    workspace = window.state_space_workspace
    workspace.task_combo.setCurrentIndex(1)
    workspace.analysis_target_combo.setCurrentIndex(1)
    workspace.matrix_a_edit.setPlainText("0,1;-5/2,-1/6")
    workspace.vector_b_edit.setPlainText("0;1/12")
    workspace.vector_c_edit.setPlainText("1,0")

    QTest.mouseClick(workspace.calculate_button, Qt.MouseButton.LeftButton)
    _app().processEvents()

    transfer_index = workspace.result_tabs.indexOf(workspace.result_edits["transfer"])
    assert not workspace.result_tabs.isTabVisible(transfer_index)
    assert workspace.result_tabs.currentWidget() is workspace.result_edits["eigen"]
    assert "-1/12 < 0" in workspace.result_edits["eigen"].toPlainText()
    assert "G(s)" not in workspace.result_edits["summary"].toPlainText()
    assert "G(s)" not in workspace.result_edits["latex"].toPlainText()
    assert window.shutdown()
    window.close()


def test_stability_target_renders_polished_matrix_outputs() -> None:
    _app()
    window = MainWindow()
    workspace = window.state_space_workspace
    workspace.task_combo.setCurrentIndex(1)
    workspace.analysis_target_combo.setCurrentIndex(1)
    workspace.matrix_a_edit.setPlainText("0,-1;1,0")
    workspace.vector_b_edit.setPlainText("1;0")
    workspace.vector_c_edit.setPlainText("1,0")

    QTest.mouseClick(workspace.calculate_button, Qt.MouseButton.LeftButton)
    _app().processEvents()

    characteristic = workspace.result_edits["characteristic"].toPlainText()
    eigen = workspace.result_edits["eigen"].toPlainText()
    latex = workspace.result_edits["latex"].toPlainText()
    assert "s*s - 1*(-1)" in characteristic
    assert "Numerische Eigenwerte: -i, +i" in eigen
    assert r"\lambda_{1,2}=\pm j" in latex
    assert r"s\cdot s-1\cdot \left(-1\right)" in latex
    assert window.shutdown()
    window.close()


def test_dgl_stability_target_renders_si_minus_ar() -> None:
    _app()
    window = MainWindow()
    workspace = window.state_space_workspace
    workspace.analysis_target_combo.setCurrentIndex(1)
    workspace.order_combo.setCurrentIndex(1)
    for edit, value in zip(workspace.coefficient_edits, ("2", "3", "1"), strict=False):
        edit.setText(value)
    workspace.input_factor_edit.setText("1")

    QTest.mouseClick(workspace.calculate_button, Qt.MouseButton.LeftButton)
    _app().processEvents()

    assert workspace.result_edits["characteristic"].toPlainText().startswith("sI-A_R")
    assert "sI-A_R" in workspace.result_edits["steps"].toPlainText()
    assert r"sI-A_R=" in workspace.result_edits["latex"].toPlainText()
    assert window.shutdown()
    window.close()


def test_reset_restores_full_analysis_target_and_transfer_tab() -> None:
    _app()
    window = MainWindow()
    workspace = window.state_space_workspace
    workspace.analysis_target_combo.setCurrentIndex(1)

    QTest.mouseClick(workspace.reset_button, Qt.MouseButton.LeftButton)
    _app().processEvents()

    assert workspace.analysis_target_combo.currentText() == "Vollständige Analyse"
    transfer_index = workspace.result_tabs.indexOf(workspace.result_edits["transfer"])
    assert workspace.result_tabs.isTabVisible(transfer_index)
    assert window.shutdown()
    window.close()
