"""Qt presenter coordinating request creation and immutable UI state."""

from __future__ import annotations

from dataclasses import replace

from PySide6.QtCore import QObject, Signal, Slot

from klausurbotpro.application import (
    SolutionReportStatus,
    TransferFunctionInputDraft,
    TransferFunctionRequestFactory,
)
from klausurbotpro.ui.transfer_function_view_state import (
    TransferFunctionReportView,
    TransferFunctionUiRunStatus,
    TransferFunctionViewState,
)
from klausurbotpro.ui.workflow_worker import (
    TransferFunctionWorkflowExecutionResult,
    WorkflowWorkerFailure,
)


class TransferFunctionPresenter(QObject):
    """Own presentation state without performing mathematical operations."""

    execution_requested = Signal(object)
    state_changed = Signal(object)

    def __init__(
        self,
        request_factory: TransferFunctionRequestFactory,
    ) -> None:
        super().__init__()
        if type(request_factory) is not TransferFunctionRequestFactory:
            raise TypeError("request_factory has an invalid type.")
        self._request_factory = request_factory
        self._state = TransferFunctionViewState()

    @property
    def state(self) -> TransferFunctionViewState:
        """Return the current immutable presentation state."""

        return self._state

    def submit(self, draft: TransferFunctionInputDraft) -> bool:
        """Validate and dispatch a draft unless a run is already active."""

        if type(draft) is not TransferFunctionInputDraft:
            raise TypeError("draft must be a TransferFunctionInputDraft.")
        if self._state.run_status is TransferFunctionUiRunStatus.RUNNING:
            return False
        creation = self._request_factory.create(draft)
        if not creation.succeeded:
            has_previous = self._state.solution_report is not None
            self._set_state(
                replace(
                    self._state,
                    request_errors=creation.errors,
                    focused_field=creation.errors[0].field,
                    general_message=(
                        "Eingabe ungültig; das angezeigte Ergebnis stammt "
                        "aus der vorherigen Berechnung."
                        if has_previous
                        else "Eingabe ungültig."
                    ),
                )
            )
            return False
        assert creation.request is not None
        self._set_state(
            replace(
                self._state,
                run_status=TransferFunctionUiRunStatus.RUNNING,
                request_errors=(),
                focused_field=None,
                general_message="Berechnung läuft …",
            )
        )
        self.execution_requested.emit(creation.request)
        return True

    @Slot(object)
    def accept_result(self, value: object) -> None:
        """Accept one immutable worker result on the GUI thread."""

        if type(value) is not TransferFunctionWorkflowExecutionResult:
            raise TypeError("value must be a workflow execution result.")
        status = {
            SolutionReportStatus.COMPLETE: TransferFunctionUiRunStatus.COMPLETE,
            SolutionReportStatus.PARTIAL: TransferFunctionUiRunStatus.PARTIAL,
            SolutionReportStatus.FAILED: TransferFunctionUiRunStatus.FAILED,
        }[value.solution_report.status]
        self._set_state(
            TransferFunctionViewState(
                status,
                value.workflow_state,
                value.solution_report,
                value.plaintext_report,
                value.latex_report,
                self._state.active_report_view,
                (),
                None,
                {
                    TransferFunctionUiRunStatus.COMPLETE: (
                        "Berechnung vollständig abgeschlossen."
                    ),
                    TransferFunctionUiRunStatus.PARTIAL: (
                        "Teilresultat: Eine spätere Workflowstufe ist fehlgeschlagen."
                    ),
                    TransferFunctionUiRunStatus.FAILED: (
                        "Die Berechnung ist fehlgeschlagen."
                    ),
                }[status],
            )
        )

    @Slot(object)
    def accept_failure(self, value: object) -> None:
        """Turn an unexpected worker failure into safe presentation state."""

        if type(value) is not WorkflowWorkerFailure:
            raise TypeError("value must be a WorkflowWorkerFailure.")
        self._set_state(
            replace(
                self._state,
                run_status=TransferFunctionUiRunStatus.FAILED,
                request_errors=(),
                focused_field=None,
                general_message=value.message,
            )
        )

    def select_report_view(self, view: TransferFunctionReportView) -> None:
        """Select the active report representation."""

        if type(view) is not TransferFunctionReportView:
            raise TypeError("view must be a TransferFunctionReportView.")
        self._set_state(replace(self._state, active_report_view=view))

    def active_report_text(self) -> str:
        """Return the active renderer output without altering it."""

        if self._state.active_report_view is TransferFunctionReportView.LATEX:
            return self._state.latex_report
        return self._state.plaintext_report

    def report_copied(self) -> None:
        """Publish a short non-modal copy confirmation."""

        if self.active_report_text():
            self._set_state(
                replace(
                    self._state,
                    general_message="Bericht in die Zwischenablage kopiert.",
                )
            )

    def reset(self) -> bool:
        """Clear the current result only while no run is active."""

        if self._state.run_status is TransferFunctionUiRunStatus.RUNNING:
            return False
        self._set_state(TransferFunctionViewState())
        return True

    def set_general_message(self, message: str) -> None:
        """Set one visible non-technical lifecycle message."""

        if type(message) is not str or not message:
            raise ValueError("message must be a non-empty string.")
        self._set_state(replace(self._state, general_message=message))

    def _set_state(self, state: TransferFunctionViewState) -> None:
        self._state = state
        self.state_changed.emit(state)


__all__ = ["TransferFunctionPresenter"]
