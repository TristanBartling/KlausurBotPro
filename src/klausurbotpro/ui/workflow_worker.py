"""Persistent widget-free Qt worker for the application workflow."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal, Slot

from klausurbotpro.application import (
    ControllerDesignInputDraft,
    ControllerDesignWorkflowService,
    FrequencyDomainWorkflowLimits,
    FrequencyDomainWorkflowRequest,
    FrequencyDomainWorkflowService,
    SolutionReportLimits,
    TransferFunctionSolutionReport,
    TransferFunctionSolutionReportBuilder,
    TransferFunctionWorkflowLimits,
    TransferFunctionWorkflowRequest,
    TransferFunctionWorkflowService,
    TransferFunctionWorkflowState,
    render_solution_report_latex,
    render_solution_report_plaintext,
)
from klausurbotpro.application.stability_workflow import (
    StabilityInputDraft,
    StabilityWorkflowResult,
    run_stability_workflow,
)

_LOGGER = logging.getLogger(__name__)
_DEFAULT_WORKFLOW_LIMITS = TransferFunctionWorkflowLimits()
_DEFAULT_REPORT_LIMITS = SolutionReportLimits()
_DEFAULT_FREQUENCY_LIMITS = FrequencyDomainWorkflowLimits()


@dataclass(frozen=True, slots=True)
class TransferFunctionWorkflowExecutionResult:
    """Immutable cross-thread result made only from public Application values."""

    workflow_state: TransferFunctionWorkflowState
    solution_report: TransferFunctionSolutionReport
    plaintext_report: str
    latex_report: str

    def __post_init__(self) -> None:
        if type(self.workflow_state) is not TransferFunctionWorkflowState:
            raise TypeError("workflow_state has an invalid type.")
        if type(self.solution_report) is not TransferFunctionSolutionReport:
            raise TypeError("solution_report has an invalid type.")
        if type(self.plaintext_report) is not str:
            raise TypeError("plaintext_report must be a string.")
        if type(self.latex_report) is not str:
            raise TypeError("latex_report must be a string.")


@dataclass(frozen=True, slots=True)
class WorkflowWorkerFailure:
    """Safe UI-facing representation of one unexpected worker failure."""

    message: str

    def __post_init__(self) -> None:
        if type(self.message) is not str or not self.message:
            raise ValueError("message must be a non-empty string.")


class TransferFunctionWorkflowWorker(QObject):
    """Execute one request at a time without owning or mutating widgets."""

    completed = Signal(object)
    failed = Signal(object)

    def __init__(
        self,
        workflow_limits: TransferFunctionWorkflowLimits = _DEFAULT_WORKFLOW_LIMITS,
        report_limits: SolutionReportLimits = _DEFAULT_REPORT_LIMITS,
    ) -> None:
        super().__init__()
        if type(workflow_limits) is not TransferFunctionWorkflowLimits:
            raise TypeError("workflow_limits has an invalid type.")
        if type(report_limits) is not SolutionReportLimits:
            raise TypeError("report_limits has an invalid type.")
        self._workflow_limits = workflow_limits
        self._report_limits = report_limits
        self._service = TransferFunctionWorkflowService(workflow_limits)
        self._builder = TransferFunctionSolutionReportBuilder(
            report_limits,
            workflow_limits=workflow_limits,
        )
        self._running = False

    @Slot(object)
    def execute(self, request: object) -> None:
        """Run one complete Application workflow and emit a structured result."""

        if self._running:
            return
        self._running = True
        try:
            if type(request) is not TransferFunctionWorkflowRequest:
                raise TypeError("request must be a TransferFunctionWorkflowRequest.")
            state = self._service.run(request)
            report = self._builder.build(state)
            result = TransferFunctionWorkflowExecutionResult(
                state,
                report,
                render_solution_report_plaintext(report),
                render_solution_report_latex(report),
            )
        except Exception:
            _LOGGER.exception("Unexpected transfer-function worker failure.")
            self.failed.emit(
                WorkflowWorkerFailure(
                    "Die Berechnung ist unerwartet fehlgeschlagen. "
                    "Technische Details wurden protokolliert."
                )
            )
        else:
            self.completed.emit(result)
        finally:
            self._running = False


class FrequencyDomainWorkflowWorker(QObject):
    """Run the existing frequency Application service outside the UI thread."""

    completed = Signal(object)
    failed = Signal(object)

    def __init__(
        self,
        limits: FrequencyDomainWorkflowLimits = _DEFAULT_FREQUENCY_LIMITS,
    ) -> None:
        super().__init__()
        if type(limits) is not FrequencyDomainWorkflowLimits:
            raise TypeError("limits must be FrequencyDomainWorkflowLimits.")
        self._limits = limits
        self._service = FrequencyDomainWorkflowService(limits)
        self._running = False

    @Slot(object)
    def execute(self, request: object) -> None:
        if self._running:
            return
        self._running = True
        try:
            if type(request) is not FrequencyDomainWorkflowRequest:
                raise TypeError("request must be FrequencyDomainWorkflowRequest.")
            result = self._service.run(request)
        except Exception:
            _LOGGER.exception("Unexpected frequency-domain worker failure.")
            self.failed.emit(
                WorkflowWorkerFailure(
                    "Die Frequenzberechnung ist unerwartet fehlgeschlagen. "
                    "Technische Details wurden protokolliert."
                )
            )
        else:
            self.completed.emit(result)
        finally:
            self._running = False


class StabilityWorkflowWorker(QObject):
    """Run stability preparation and analysis in the persistent worker thread."""

    completed = Signal(object)
    failed = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self._running = False

    @Slot(object)
    def execute(self, request: object) -> None:
        if self._running:
            return
        self._running = True
        try:
            if type(request) is not StabilityInputDraft:
                raise TypeError("request must be StabilityInputDraft.")
            result = run_stability_workflow(request)
            if type(result) is not StabilityWorkflowResult:
                raise TypeError("stability workflow returned an invalid result.")
        except Exception:
            _LOGGER.exception("Unexpected stability worker failure.")
            self.failed.emit(
                WorkflowWorkerFailure(
                    "Die Stabilitätsberechnung ist unerwartet fehlgeschlagen. "
                    "Technische Details wurden protokolliert."
                )
            )
        else:
            self.completed.emit(result)
        finally:
            self._running = False


class ControllerDesignWorkflowWorker(QObject):
    """Run controller design in the existing persistent worker thread."""

    completed = Signal(object)
    failed = Signal(object)

    def __init__(self, limits: FrequencyDomainWorkflowLimits = _DEFAULT_FREQUENCY_LIMITS) -> None:
        super().__init__()
        self._service = ControllerDesignWorkflowService(limits)
        self._running = False

    @Slot(object)
    def execute(self, request: object) -> None:
        if self._running:
            return
        self._running = True
        try:
            if type(request) is not ControllerDesignInputDraft:
                raise TypeError("request must be ControllerDesignInputDraft.")
            result = self._service.run(request)
        except Exception:
            _LOGGER.exception("Unexpected controller-design worker failure.")
            self.failed.emit(
                WorkflowWorkerFailure(
                    "Die Reglerauslegung ist unerwartet fehlgeschlagen. "
                    "Technische Details wurden protokolliert."
                )
            )
        else:
            self.completed.emit(result)
        finally:
            self._running = False


__all__ = [
    "ControllerDesignWorkflowWorker",
    "FrequencyDomainWorkflowWorker",
    "StabilityWorkflowWorker",
    "TransferFunctionWorkflowExecutionResult",
    "TransferFunctionWorkflowWorker",
    "WorkflowWorkerFailure",
]
