"""Main desktop window and explicit worker-thread lifecycle."""

from __future__ import annotations

from PySide6.QtCore import QThread, QTimer, Slot
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QMainWindow

from klausurbotpro.application import (
    SolutionReportLimits,
    TransferFunctionRequestFactory,
    TransferFunctionWorkflowLimits,
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
from klausurbotpro.ui.workflow_worker import TransferFunctionWorkflowWorker

APP_NAME = "KlausurBotPro"
_DEFAULT_WORKFLOW_LIMITS = TransferFunctionWorkflowLimits()
_DEFAULT_REPORT_LIMITS = SolutionReportLimits()


class MainWindow(QMainWindow):
    """Own the one Phase-2D.1 workspace and its persistent worker thread."""

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
        self.setObjectName("mainWindow")
        self.setWindowTitle(APP_NAME)
        self.resize(1100, 750)
        self.setMinimumSize(760, 560)

        self.presenter = TransferFunctionPresenter(
            TransferFunctionRequestFactory(workflow_limits)
        )
        self.workspace = TransferFunctionWorkspace(self.presenter)
        self.setCentralWidget(self.workspace)

        self.worker_thread = QThread(self)
        self.worker_thread.setObjectName("transferFunctionWorkerThread")
        self.worker = TransferFunctionWorkflowWorker(
            workflow_limits,
            report_limits,
        )
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.finished.connect(self.worker.deleteLater)
        self.presenter.execution_requested.connect(self.worker.execute)
        self.worker.completed.connect(self.presenter.accept_result)
        self.worker.failed.connect(self.presenter.accept_failure)
        self.presenter.state_changed.connect(self._state_changed)
        self.worker_thread.start()
        self._close_pending = False
        self._shutdown_complete = False

    def shutdown(self) -> bool:
        """Stop the idle persistent worker thread without terminating work."""

        if self._shutdown_complete:
            return True
        if (
            self.presenter.state.run_status
            is TransferFunctionUiRunStatus.RUNNING
        ):
            self._close_pending = True
            self.presenter.set_general_message(
                "Schließen wird nach Abschluss der laufenden Berechnung fortgesetzt."
            )
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
        if type(value) is not TransferFunctionViewState:
            return
        if (
            self._close_pending
            and value.run_status is not TransferFunctionUiRunStatus.RUNNING
        ):
            self._close_pending = False
            QTimer.singleShot(0, self.close)


__all__ = ["APP_NAME", "MainWindow"]
