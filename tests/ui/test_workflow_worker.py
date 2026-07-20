"""Real QThread integration tests for the widget-free worker."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import QEventLoop, QObject, QThread, QTimer, Signal
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication

from klausurbotpro.application import (
    FrequencyDomainWorkflowMode,
    FrequencyDomainWorkflowRequest,
    FrequencyDomainWorkflowResult,
    FrequencyDomainWorkflowService,
    SolutionReportLimits,
    TransferFunctionWorkflowLimits,
    TransferFunctionWorkflowRequest,
    WorkflowInputForm,
)
from klausurbotpro.domain import ExactRationalValue
from klausurbotpro.ui import (
    FrequencyDomainWorkflowWorker,
    TransferFunctionWorkflowExecutionResult,
    TransferFunctionWorkflowWorker,
    WorkflowWorkerFailure,
)


def _app() -> QApplication:
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    assert isinstance(application, QApplication)
    return application


def test_worker_uses_identical_limits_and_returns_structured_result() -> None:
    application = _app()
    workflow_limits = TransferFunctionWorkflowLimits()
    report_limits = SolutionReportLimits()
    thread = QThread()
    worker = TransferFunctionWorkflowWorker(workflow_limits, report_limits)
    worker.moveToThread(thread)
    completed = QSignalSpy(worker.completed)
    trigger = _Trigger()
    trigger.requested.connect(worker.execute)
    thread.start()

    assert worker._workflow_limits is workflow_limits  # noqa: SLF001
    assert worker._service._limits is workflow_limits  # noqa: SLF001
    assert worker._builder._workflow_limits is workflow_limits  # noqa: SLF001
    assert worker._report_limits is report_limits  # noqa: SLF001
    loop = QEventLoop()
    worker.completed.connect(loop.quit)
    trigger.requested.emit(
        TransferFunctionWorkflowRequest(
            WorkflowInputForm.COMMON,
            common_expression_text="1/(s+1)",
        )
    )
    QTimer.singleShot(15_000, loop.quit)
    loop.exec()
    application.processEvents()
    assert completed.count() == 1
    result = completed.at(0)[0]
    assert type(result) is TransferFunctionWorkflowExecutionResult
    assert "System ist E/A-stabil." in result.plaintext_report

    thread.quit()
    assert thread.wait(10_000)


def test_worker_reports_unexpected_failure_without_traceback_text() -> None:
    _app()
    worker = TransferFunctionWorkflowWorker()
    failed = QSignalSpy(worker.failed)

    worker.execute(object())

    assert failed.count() == 1
    failure = failed.at(0)[0]
    assert type(failure) is WorkflowWorkerFailure
    assert "Traceback" not in failure.message


def test_frequency_worker_runs_existing_service_once_in_qthread(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    application = _app()
    calls = 0
    original = FrequencyDomainWorkflowService.run

    def counted(
        self: FrequencyDomainWorkflowService,
        request: FrequencyDomainWorkflowRequest,
    ) -> FrequencyDomainWorkflowResult:
        nonlocal calls
        calls += 1
        return original(self, request)

    monkeypatch.setattr(FrequencyDomainWorkflowService, "run", counted)
    thread = QThread()
    worker = FrequencyDomainWorkflowWorker()
    worker.moveToThread(thread)
    completed = QSignalSpy(worker.completed)
    trigger = _Trigger()
    trigger.requested.connect(worker.execute)
    thread.start()
    loop = QEventLoop()
    worker.completed.connect(loop.quit)
    trigger.requested.emit(
        FrequencyDomainWorkflowRequest(
            TransferFunctionWorkflowRequest(
                WorkflowInputForm.COMMON,
                common_expression_text="1/(s+1)",
            ),
            FrequencyDomainWorkflowMode.SINGLE_POINT,
            single_angular_frequency=ExactRationalValue(1),
        )
    )
    QTimer.singleShot(15_000, loop.quit)
    loop.exec()
    application.processEvents()

    assert completed.count() == 1
    assert calls == 1
    assert type(completed.at(0)[0]) is FrequencyDomainWorkflowResult
    thread.quit()
    assert thread.wait(10_000)


class _Trigger(QObject):
    requested = Signal(object)
