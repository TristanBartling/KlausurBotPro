"""Offscreen interaction tests for the frequency workspace."""

import os

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
