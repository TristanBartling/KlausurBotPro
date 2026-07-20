"""Main desktop window and explicit worker-thread lifecycle."""

from __future__ import annotations

from PySide6.QtCore import QThread, QTimer, Slot
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QMainWindow, QTabWidget

from klausurbotpro.application import (
    FrequencyDomainRequestFactory,
    FrequencyDomainWorkflowLimits,
    SolutionReportLimits,
    TransferFunctionRequestFactory,
    TransferFunctionWorkflowLimits,
)
from klausurbotpro.ui.frequency_domain_presenter import (
    FrequencyDomainPresenter,
)
from klausurbotpro.ui.frequency_domain_view_state import (
    FrequencyDomainUiRunStatus,
    FrequencyDomainViewState,
)
from klausurbotpro.ui.frequency_domain_workspace import (
    FrequencyDomainWorkspace,
)
from klausurbotpro.ui.transfer_function_presenter import (
    TransferFunctionPresenter,
)
from klausurbotpro.ui.transfer_function_view_state import (
    TransferFunctionUiRunStatus,
    TransferFunctionViewState,
)
from klausurbotpro.ui.transfer_function_workspace import (
    TransferFunctionWorkspace,
)
from klausurbotpro.ui.workflow_worker import (
    FrequencyDomainWorkflowWorker,
    TransferFunctionWorkflowWorker,
)

APP_NAME = "KlausurBotPro"
_DEFAULT_WORKFLOW_LIMITS = TransferFunctionWorkflowLimits()
_DEFAULT_REPORT_LIMITS = SolutionReportLimits()
_DEFAULT_FREQUENCY_LIMITS = FrequencyDomainWorkflowLimits()


class MainWindow(QMainWindow):
    """Own the one Phase-2D.1 workspace and its persistent worker thread."""

    def __init__(
        self,
        workflow_limits: TransferFunctionWorkflowLimits = _DEFAULT_WORKFLOW_LIMITS,
        report_limits: SolutionReportLimits = _DEFAULT_REPORT_LIMITS,
        frequency_limits: FrequencyDomainWorkflowLimits = _DEFAULT_FREQUENCY_LIMITS,
    ) -> None:
        super().__init__()
        if type(workflow_limits) is not TransferFunctionWorkflowLimits:
            raise TypeError("workflow_limits has an invalid type.")
        if type(report_limits) is not SolutionReportLimits:
            raise TypeError("report_limits has an invalid type.")
        if type(frequency_limits) is not FrequencyDomainWorkflowLimits:
            raise TypeError("frequency_limits has an invalid type.")
        self.setObjectName("mainWindow")
        self.setWindowTitle(APP_NAME)
        self.resize(1200, 780)
        self.setMinimumSize(760, 560)

        self.presenter = TransferFunctionPresenter(
            TransferFunctionRequestFactory(workflow_limits)
        )
        self.workspace = TransferFunctionWorkspace(self.presenter)
        self.frequency_presenter = FrequencyDomainPresenter(
            FrequencyDomainRequestFactory(frequency_limits)
        )
        self.frequency_workspace = FrequencyDomainWorkspace(
            self.frequency_presenter
        )
        self.workspace_tabs = QTabWidget()
        self.workspace_tabs.setObjectName("mainWorkspaceTabs")
        self.workspace_tabs.addTab(self.workspace, "Transferfunktion")
        self.workspace_tabs.addTab(
            self.frequency_workspace,
            "Frequenzbereich",
        )
        self.setCentralWidget(self.workspace_tabs)

        self.worker_thread = QThread(self)
        self.worker_thread.setObjectName("transferFunctionWorkerThread")
        self.worker = TransferFunctionWorkflowWorker(
            workflow_limits,
            report_limits,
        )
        self.worker.moveToThread(self.worker_thread)
        self.frequency_worker = FrequencyDomainWorkflowWorker(frequency_limits)
        self.frequency_worker.moveToThread(self.worker_thread)
        self.worker_thread.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.frequency_worker.deleteLater)
        self.presenter.execution_requested.connect(self.worker.execute)
        self.frequency_presenter.execution_requested.connect(
            self.frequency_worker.execute
        )
        self.worker.completed.connect(self.presenter.accept_result)
        self.worker.failed.connect(self.presenter.accept_failure)
        self.frequency_worker.completed.connect(
            self.frequency_presenter.accept_result
        )
        self.frequency_worker.failed.connect(
            self.frequency_presenter.accept_failure
        )
        self.presenter.state_changed.connect(self._state_changed)
        self.frequency_presenter.state_changed.connect(self._state_changed)
        self.worker_thread.start()
        self._close_pending = False
        self._shutdown_complete = False

    def shutdown(self) -> bool:
        """Stop the idle persistent worker thread without terminating work."""

        if self._shutdown_complete:
            return True
        if self._is_running():
            self._close_pending = True
            message = (
                "Schließen wird nach Abschluss der laufenden Berechnung fortgesetzt."
            )
            if (
                self.presenter.state.run_status
                is TransferFunctionUiRunStatus.RUNNING
            ):
                self.presenter.set_general_message(message)
            if (
                self.frequency_presenter.state.run_status
                is FrequencyDomainUiRunStatus.RUNNING
            ):
                self.frequency_presenter.set_general_message(message)
            return False
        self.worker_thread.quit()
        stopped = self.worker_thread.wait(10_000)
        if stopped:
            self._shutdown_complete = True
        return stopped

    def closeEvent(self, event: QCloseEvent) -> None:
        """Defer close during work and otherwise perform a clean shutdown."""

        if self.shutdown():
            event.accept()
        else:
            event.ignore()

    @Slot(object)
    def _state_changed(self, value: object) -> None:
        if type(value) not in (
            TransferFunctionViewState,
            FrequencyDomainViewState,
        ):
            return
        if self._close_pending and not self._is_running():
            self._close_pending = False
            QTimer.singleShot(0, self.close)

    def _is_running(self) -> bool:
        return (
            self.presenter.state.run_status
            is TransferFunctionUiRunStatus.RUNNING
            or self.frequency_presenter.state.run_status
            is FrequencyDomainUiRunStatus.RUNNING
        )


__all__ = ["APP_NAME", "MainWindow"]
