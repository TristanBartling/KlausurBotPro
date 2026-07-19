"""Immutable widget-free state for the transfer-function workspace."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from klausurbotpro.application import (
    TransferFunctionRequestFieldError,
    TransferFunctionSolutionReport,
    TransferFunctionWorkflowState,
)


class TransferFunctionUiRunStatus(StrEnum):
    """Lifecycle state visible to the desktop workspace."""

    IDLE = "idle"
    RUNNING = "running"
    COMPLETE = "complete"
    PARTIAL = "partial"
    FAILED = "failed"


class TransferFunctionReportView(StrEnum):
    """Available exact report representations."""

    PLAINTEXT = "plaintext"
    LATEX = "latex"


@dataclass(frozen=True, slots=True)
class TransferFunctionViewState:
    """Complete deterministic presentation state without Qt widgets."""

    run_status: TransferFunctionUiRunStatus = TransferFunctionUiRunStatus.IDLE
    workflow_state: TransferFunctionWorkflowState | None = None
    solution_report: TransferFunctionSolutionReport | None = None
    plaintext_report: str = ""
    latex_report: str = ""
    active_report_view: TransferFunctionReportView = (
        TransferFunctionReportView.PLAINTEXT
    )
    request_errors: tuple[TransferFunctionRequestFieldError, ...] = ()
    focused_field: str | None = None
    general_message: str = "Bereit."

    def __post_init__(self) -> None:
        if type(self.run_status) is not TransferFunctionUiRunStatus:
            raise TypeError("run_status must be a TransferFunctionUiRunStatus.")
        if self.workflow_state is not None and (
            type(self.workflow_state) is not TransferFunctionWorkflowState
        ):
            raise TypeError("workflow_state has an invalid type.")
        if self.solution_report is not None and (
            type(self.solution_report) is not TransferFunctionSolutionReport
        ):
            raise TypeError("solution_report has an invalid type.")
        for name in ("plaintext_report", "latex_report", "general_message"):
            if type(getattr(self, name)) is not str:
                raise TypeError(f"{name} must be a string.")
        if type(self.active_report_view) is not TransferFunctionReportView:
            raise TypeError("active_report_view has an invalid type.")
        errors = tuple(self.request_errors)
        if any(
            type(error) is not TransferFunctionRequestFieldError
            for error in errors
        ):
            raise TypeError("request_errors contain an invalid value.")
        if self.focused_field is not None and (
            type(self.focused_field) is not str
        ):
            raise TypeError("focused_field must be a string or None.")
        object.__setattr__(self, "request_errors", errors)


__all__ = [
    "TransferFunctionReportView",
    "TransferFunctionUiRunStatus",
    "TransferFunctionViewState",
]
