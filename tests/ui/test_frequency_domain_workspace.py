"""Offscreen interaction tests for the frequency workspace."""

import os
import tomllib
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from klausurbotpro.application import (
    FrequencyDomainRequestFactory,
    FrequencyDomainWorkflowRequest,
    FrequencyDomainWorkflowService,
)
from klausurbotpro.ui import (
    FrequencyDomainPresenter,
    FrequencyDomainWorkspace,
)


def _app() -> QApplication:
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    assert isinstance(application, QApplication)
    return application


def _workspace() -> tuple[FrequencyDomainWorkspace, list[object]]:
    application = _app()
    presenter = FrequencyDomainPresenter(FrequencyDomainRequestFactory())
    requests: list[object] = []
    presenter.execution_requested.connect(requests.append)
    workspace = FrequencyDomainWorkspace(presenter)
    workspace.show()
    application.processEvents()
    return workspace, requests


def test_mode_controls_only_relevant_fields_and_unwrap() -> None:
    workspace, _requests = _workspace()

    assert workspace.single_frequency_edit.isEnabled()
    assert not workspace.omega_min_edit.isEnabled()
    assert not workspace.phase_combo.isEnabled()
    assert workspace.phase_combo.currentIndex() == 0

    workspace.mode_combo.setCurrentIndex(1)
    _app().processEvents()
    assert not workspace.single_frequency_edit.isEnabled()
    assert workspace.omega_min_edit.isEnabled()
    assert workspace.omega_max_edit.isEnabled()
    assert workspace.points_per_decade_edit.isEnabled()
    assert workspace.explicit_frequencies_edit.isEnabled()
    assert workspace.phase_combo.isEnabled()

    workspace.phase_combo.setCurrentIndex(1)
    workspace.mode_combo.setCurrentIndex(0)
    assert workspace.phase_combo.currentIndex() == 0
    assert not workspace.phase_combo.isEnabled()
    workspace.close()


def test_pt1_bode_renders_one_visible_row_per_domain_point() -> None:
    workspace, requests = _workspace()
    workspace.common_expression_edit.setPlainText("1/(s+1)")
    workspace.mode_combo.setCurrentIndex(1)

    QTest.mouseClick(workspace.calculate_button, Qt.MouseButton.LeftButton)

    request = requests[0]
    assert type(request) is FrequencyDomainWorkflowRequest
    assert not workspace.calculate_button.isEnabled()
    assert workspace.value_table.rowCount() == 0
    workspace.presenter.accept_result(FrequencyDomainWorkflowService().run(request))
    _app().processEvents()
    result = FrequencyDomainWorkflowService().run(request)
    assert result.bode_data_result is not None
    assert workspace.value_table.rowCount() == len(result.bode_data_result.points)
    assert workspace.value_table.isRowHidden(0) is False
    target_item = workspace.value_table.item(0, 1)
    evaluation_item = workspace.value_table.item(0, 2)
    assert target_item is not None and target_item.text()
    assert evaluation_item is not None and evaluation_item.text()
    assert workspace.calculate_button.isEnabled()
    workspace.close()


def test_invalid_rational_is_visible_focused_and_does_not_dispatch() -> None:
    workspace, requests = _workspace()
    workspace.common_expression_edit.setPlainText("1/(s+1)")
    workspace.single_frequency_edit.setText("0.5")

    QTest.mouseClick(workspace.calculate_button, Qt.MouseButton.LeftButton)
    _app().processEvents()

    assert not requests
    assert workspace.single_frequency_edit.hasFocus()
    assert workspace.diagnostic_table.rowCount() == 1
    message_item = workspace.diagnostic_table.item(0, 1)
    assert message_item is not None
    assert "rationale" in message_item.text()
    assert "ungültig" in workspace.status_label.text()
    workspace.close()


def test_input_help_explains_required_optional_and_advanced_grid_fields() -> None:
    workspace, _requests = _workspace()
    help_text = workspace.input_help_label.text()

    assert "Aufgabenstellung oder Blockschaltbild" in help_text
    assert "ω_min und ω_max" in help_text
    assert "Standardwert 4" in help_text
    assert "optional" in help_text
    assert "Hauptphase" in help_text
    assert "±360°" in help_text
    assert workspace.advanced_grid_group.title() == (
        "Erweiterte Rastereinstellungen"
    )
    assert workspace.points_per_decade_edit.text() == "4"
    workspace.close()


def test_table_shows_short_values_and_preserves_full_values_in_tooltips() -> None:
    workspace, requests = _workspace()
    workspace.common_expression_edit.setPlainText("1/(s+1)")
    workspace.mode_combo.setCurrentIndex(1)
    QTest.mouseClick(workspace.calculate_button, Qt.MouseButton.LeftButton)
    request = requests[0]
    assert type(request) is FrequencyDomainWorkflowRequest
    workspace.presenter.accept_result(FrequencyDomainWorkflowService().run(request))
    _app().processEvents()

    real_item = workspace.value_table.item(1, 4)
    assert real_item is not None
    assert len(real_item.text()) <= 12
    assert real_item.toolTip()
    assert real_item.toolTip() != real_item.text()
    evaluation_item = workspace.value_table.item(1, 2)
    assert evaluation_item is not None
    assert len(evaluation_item.text()) <= 12
    assert evaluation_item.toolTip() != evaluation_item.text()
    target_header = workspace.value_table.horizontalHeaderItem(1)
    evaluation_header = workspace.value_table.horizontalHeaderItem(2)
    assert target_header is not None
    assert evaluation_header is not None
    assert "gewünschte" in target_header.toolTip()
    assert "zertifizierte" in evaluation_header.toolTip()
    workspace.close()


def test_bode_row_selection_updates_numerical_worked_steps() -> None:
    workspace, requests = _workspace()
    workspace.common_expression_edit.setPlainText("1/(s+1)")
    workspace.mode_combo.setCurrentIndex(1)
    QTest.mouseClick(workspace.calculate_button, Qt.MouseButton.LeftButton)
    request = requests[0]
    assert type(request) is FrequencyDomainWorkflowRequest
    workspace.presenter.accept_result(FrequencyDomainWorkflowService().run(request))
    _app().processEvents()

    workspace.value_table.setCurrentCell(2, 0)
    _app().processEvents()
    text = workspace.worked_steps_edit.toPlainText()
    assert "Numerische Kurzlösung" not in text
    assert "Gegeben:" in text
    assert "Ziel-ω =" in text
    assert "Auswertung:" in text
    assert "Spezialisierter Zähler:" not in text
    assert "Plotsegment:" not in text
    assert not workspace.technical_details_checkbox.isChecked()

    workspace.technical_details_checkbox.setChecked(True)
    _app().processEvents()
    details = workspace.worked_steps_edit.toPlainText()
    assert "Technische Details" in details
    assert "Bode-Tabellenzeile 3" in details
    assert "Spezialisierter Zähler:" in details
    assert "Plotsegment:" in details

    workspace.value_table.setCurrentCell(3, 0)
    _app().processEvents()
    updated = workspace.worked_steps_edit.toPlainText()
    assert "Bode-Tabellenzeile 4" in updated
    assert "Bode-Tabellenzeile 3" not in updated
    workspace.close()


def test_plot_canvas_draws_each_singularity_segment_as_a_separate_line() -> None:
    workspace, requests = _workspace()
    workspace.common_expression_edit.setPlainText("1/(s^2+1)")
    workspace.mode_combo.setCurrentIndex(1)
    workspace.omega_min_edit.setText("1/100")
    workspace.omega_max_edit.setText("100")
    QTest.mouseClick(workspace.calculate_button, Qt.MouseButton.LeftButton)
    request = requests[0]
    assert type(request) is FrequencyDomainWorkflowRequest
    workspace.presenter.accept_result(FrequencyDomainWorkflowService().run(request))
    _app().processEvents()

    magnitude_lines = workspace.magnitude_axes.get_lines()
    phase_lines = workspace.phase_axes.get_lines()
    assert len(magnitude_lines) == 2
    assert len(phase_lines) == 2
    assert all(len(line.get_xdata()) == 8 for line in magnitude_lines)
    magnitude_markers = tuple(
        collection
        for collection in workspace.magnitude_axes.collections
        if collection.get_gid() == "frequency-interruption"
    )
    phase_markers = tuple(
        collection
        for collection in workspace.phase_axes.collections
        if collection.get_gid() == "frequency-interruption"
    )
    assert len(magnitude_markers) == 1
    assert len(phase_markers) == 1
    assert all(
        segment[0][0] == segment[1][0] == 1
        for collection in magnitude_markers + phase_markers
        for segment in collection.get_segments()
    )
    assert all(
        1 not in line.get_xdata()
        for line in magnitude_lines + phase_lines
    )
    assert sum(
        text.get_text() == "Singularität"
        for text in workspace.magnitude_axes.texts
    ) == 1
    assert sum(
        text.get_text() == "Singularität"
        for text in workspace.phase_axes.texts
    ) == 1
    assert "Rasterauflösung" in workspace.plot_gap_hint_label.text()
    assert "markierten Frequenz" in workspace.plot_gap_hint_label.text()
    assert workspace.magnitude_axes.get_xscale() == "log"
    assert workspace.phase_axes.get_xscale() == "log"
    workspace.close()


def test_unwrapped_plot_is_additional_and_single_point_hides_diagrams() -> None:
    workspace, requests = _workspace()
    assert not workspace.result_tabs.isTabVisible(workspace.plot_tab_index)
    workspace.common_expression_edit.setPlainText("1/(s/10+1)^3")
    workspace.mode_combo.setCurrentIndex(1)
    workspace.omega_min_edit.setText("1/100")
    workspace.omega_max_edit.setText("1000")
    workspace.phase_combo.setCurrentIndex(1)
    QTest.mouseClick(workspace.calculate_button, Qt.MouseButton.LeftButton)
    request = requests[0]
    assert type(request) is FrequencyDomainWorkflowRequest
    workspace.presenter.accept_result(FrequencyDomainWorkflowService().run(request))
    _app().processEvents()

    assert workspace.result_tabs.isTabVisible(workspace.plot_tab_index)
    assert len(workspace.phase_axes.get_lines()) == 2
    assert {
        line.get_label() for line in workspace.phase_axes.get_lines()
    } == {"Hauptphase", "Entfaltete Phase"}
    assert workspace.phase_axes.get_legend() is not None
    workspace.close()


def test_no_plottable_data_is_rendered_as_stable_empty_axes() -> None:
    workspace, requests = _workspace()
    workspace.common_expression_edit.setPlainText("0/(s+1)")
    workspace.mode_combo.setCurrentIndex(1)
    QTest.mouseClick(workspace.calculate_button, Qt.MouseButton.LeftButton)
    request = requests[0]
    assert type(request) is FrequencyDomainWorkflowRequest
    workspace.presenter.accept_result(FrequencyDomainWorkflowService().run(request))
    _app().processEvents()

    assert not workspace.magnitude_axes.get_lines()
    assert not workspace.phase_axes.get_lines()
    assert any(
        "Keine darstellbaren" in text.get_text()
        for text in workspace.magnitude_axes.texts
    )
    workspace.close()


def test_frequency_ui_contains_no_analyzer_calls_or_new_dependency() -> None:
    root = Path(__file__).parents[2]
    for relative in (
        "src/klausurbotpro/ui/frequency_domain_presenter.py",
        "src/klausurbotpro/ui/frequency_domain_view_state.py",
        "src/klausurbotpro/ui/frequency_domain_workspace.py",
    ):
        source = (root / relative).read_text(encoding="utf-8")
        assert "Analyzer" not in source
        assert "klausurbotpro.domain" not in source

    project = tomllib.loads(
        (root / "pyproject.toml").read_text(encoding="utf-8")
    )
    dependencies = {
        dependency.split(">=", maxsplit=1)[0]
        for dependency in project["project"]["dependencies"]
    }
    assert dependencies == {
        "control",
        "matplotlib",
        "numpy",
        "PySide6",
        "scipy",
        "sympy",
    }
