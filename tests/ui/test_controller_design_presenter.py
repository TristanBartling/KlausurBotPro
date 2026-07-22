"""Focused presenter state tests for controller design."""

from PySide6.QtTest import QSignalSpy

from klausurbotpro.application import (
    ControllerDesignInputDraft,
    ControllerDesignMethod,
    ControllerType,
)
from klausurbotpro.ui.controller_design_presenter import ControllerDesignPresenter
from klausurbotpro.ui.controller_design_view_state import ControllerDesignUiRunStatus


def _draft() -> ControllerDesignInputDraft:
    return ControllerDesignInputDraft(
        ControllerDesignMethod.P_PHASE_MARGIN,
        ControllerType.P,
        "Snapshot-Aufgabe",
        "100",
        "s*(10*s+1)",
        target_phase_margin_text="20",
        omega_min_text="1e-4",
        omega_max_text="1e2",
        points_per_decade_text="32",
    )


def test_calculate_emits_the_immutable_input_snapshot_once() -> None:
    presenter = ControllerDesignPresenter()
    requested = QSignalSpy(presenter.execution_requested)
    draft = _draft()
    presenter.calculate(draft)
    presenter.calculate(_draft())
    assert presenter.state.run_status is ControllerDesignUiRunStatus.RUNNING
    assert requested.count() == 1
    assert requested.at(0)[0] == draft


def test_reset_does_not_replace_running_snapshot_state() -> None:
    presenter = ControllerDesignPresenter()
    presenter.calculate(_draft())
    presenter.reset()
    assert presenter.state.run_status is ControllerDesignUiRunStatus.RUNNING
