"""Widget-independent presenter for controller design."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Slot

from klausurbotpro.application import ControllerDesignInputDraft, ControllerDesignResult
from klausurbotpro.ui.controller_design_view_state import (
    ControllerDesignUiRunStatus,
    ControllerDesignViewState,
)
from klausurbotpro.ui.workflow_worker import WorkflowWorkerFailure


class ControllerDesignPresenter(QObject):
    execution_requested = Signal(object)
    state_changed = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self.state = ControllerDesignViewState()

    def calculate(self, draft: ControllerDesignInputDraft) -> None:
        if self.state.run_status is ControllerDesignUiRunStatus.RUNNING:
            return
        self.state = ControllerDesignViewState(ControllerDesignUiRunStatus.RUNNING)
        self.state_changed.emit(self.state)
        self.execution_requested.emit(draft)

    @Slot(object)
    def accept_result(self, value: object) -> None:
        if type(value) is not ControllerDesignResult:
            return
        status = (
            ControllerDesignUiRunStatus.COMPLETE
            if value.has_copyable_solution
            else ControllerDesignUiRunStatus.FAILED
        )
        message = "" if not value.diagnostics else value.diagnostics[0].message
        self.state = ControllerDesignViewState(status, value, message)
        self.state_changed.emit(self.state)

    @Slot(object)
    def accept_failure(self, value: object) -> None:
        if type(value) is not WorkflowWorkerFailure:
            return
        self.state = ControllerDesignViewState(
            ControllerDesignUiRunStatus.FAILED, message=value.message
        )
        self.state_changed.emit(self.state)

    def reset(self) -> None:
        if self.state.run_status is ControllerDesignUiRunStatus.RUNNING:
            return
        self.state = ControllerDesignViewState()
        self.state_changed.emit(self.state)

    def set_general_message(self, message: str) -> None:
        self.state = ControllerDesignViewState(self.state.run_status, self.state.result, message)
        self.state_changed.emit(self.state)


__all__ = ["ControllerDesignPresenter"]
