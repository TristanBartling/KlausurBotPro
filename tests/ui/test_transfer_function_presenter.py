"""Deterministic presenter and immutable view-state tests."""

from dataclasses import FrozenInstanceError

import pytest

from klausurbotpro.application import (
    ParameterInputDraft,
    TransferFunctionInputDraft,
    TransferFunctionRequestFactory,
    TransferFunctionSolutionReportBuilder,
    TransferFunctionWorkflowRequest,
    TransferFunctionWorkflowService,
    WorkflowInputForm,
    render_solution_report_latex,
    render_solution_report_plaintext,
)
from klausurbotpro.ui import (
    TransferFunctionPresenter,
    TransferFunctionReportView,
    TransferFunctionUiRunStatus,
    TransferFunctionViewState,
    TransferFunctionWorkflowExecutionResult,
    WorkflowWorkerFailure,
)


def _draft(
    expression: str = "1/(s+1)",
    rows: tuple[ParameterInputDraft, ...] = (),
) -> TransferFunctionInputDraft:
    return TransferFunctionInputDraft(
        WorkflowInputForm.COMMON,
        expression,
        "",
        "",
        "s",
        rows,
        "transfer_function",
    )


def _execution(
    request: TransferFunctionWorkflowRequest,
) -> TransferFunctionWorkflowExecutionResult:
    state = TransferFunctionWorkflowService().run(request)
    report = TransferFunctionSolutionReportBuilder().build(state)
    return TransferFunctionWorkflowExecutionResult(
        state,
        report,
        render_solution_report_plaintext(report),
        render_solution_report_latex(report),
    )


def test_view_state_is_immutable_and_widget_free() -> None:
    state = TransferFunctionViewState()

    with pytest.raises(FrozenInstanceError):
        state.general_message = "changed"  # type: ignore[misc]
    assert "PySide6" not in type(state).__module__


def test_presenter_dispatches_once_and_ignores_second_run() -> None:
    presenter = TransferFunctionPresenter(TransferFunctionRequestFactory())
    requests: list[object] = []
    presenter.execution_requested.connect(requests.append)

    assert presenter.submit(_draft())
    assert presenter.state.run_status is TransferFunctionUiRunStatus.RUNNING
    assert len(requests) == 1
    assert not presenter.submit(_draft("1/(s+2)"))
    assert len(requests) == 1


def test_request_error_focus_is_structured_and_previous_result_remains() -> None:
    presenter = TransferFunctionPresenter(TransferFunctionRequestFactory())
    requests: list[object] = []
    presenter.execution_requested.connect(requests.append)
    presenter.submit(_draft())
    request = requests[0]
    assert type(request) is TransferFunctionWorkflowRequest
    presenter.accept_result(_execution(request))

    invalid = _draft(
        rows=(ParameterInputDraft("T", "0.5", ""),),
    )
    assert not presenter.submit(invalid)

    assert presenter.state.focused_field == "parameter_rows"
    assert presenter.state.request_errors[0].code == "invalid_numerator"
    assert presenter.state.solution_report is not None
    assert "vorherigen Berechnung" in presenter.state.general_message


def test_result_views_clipboard_text_and_reset_are_exact() -> None:
    presenter = TransferFunctionPresenter(TransferFunctionRequestFactory())
    requests: list[object] = []
    presenter.execution_requested.connect(requests.append)
    presenter.submit(_draft())
    request = requests[0]
    assert type(request) is TransferFunctionWorkflowRequest
    result = _execution(request)
    presenter.accept_result(result)

    assert presenter.state.run_status is TransferFunctionUiRunStatus.COMPLETE
    assert presenter.active_report_text() == result.plaintext_report
    presenter.select_report_view(TransferFunctionReportView.LATEX)
    assert presenter.active_report_text() == result.latex_report
    presenter.report_copied()
    assert "Zwischenablage" in presenter.state.general_message
    assert presenter.reset()
    assert presenter.state == TransferFunctionViewState()


def test_unexpected_worker_failure_is_safe_and_keeps_gui_state() -> None:
    presenter = TransferFunctionPresenter(TransferFunctionRequestFactory())
    presenter.submit(_draft())

    presenter.accept_failure(WorkflowWorkerFailure("Sicherer Fehlerhinweis."))

    assert presenter.state.run_status is TransferFunctionUiRunStatus.FAILED
    assert presenter.state.general_message == "Sicherer Fehlerhinweis."
    assert "Traceback" not in presenter.state.general_message
