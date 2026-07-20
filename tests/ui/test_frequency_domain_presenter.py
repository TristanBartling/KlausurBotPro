"""Frequency presenter request and display projections."""

from dataclasses import FrozenInstanceError

import pytest

from klausurbotpro.application import (
    FrequencyDomainInputDraft,
    FrequencyDomainRequestFactory,
    FrequencyDomainWorkflowMode,
    FrequencyDomainWorkflowRequest,
    FrequencyDomainWorkflowService,
    FrequencyPhasePresentation,
    ParameterInputDraft,
    TransferFunctionInputDraft,
    WorkflowInputForm,
)
from klausurbotpro.ui import (
    FrequencyDomainPresenter,
    FrequencyDomainUiRunStatus,
    FrequencyDomainViewState,
)


def _draft(
    expression: str,
    *,
    mode: FrequencyDomainWorkflowMode,
    single: str = "",
    omega_min: str = "",
    omega_max: str = "",
    points: str = "",
    unwrap: bool = False,
    parameters: tuple[ParameterInputDraft, ...] = (),
) -> FrequencyDomainInputDraft:
    return FrequencyDomainInputDraft(
        TransferFunctionInputDraft(
            WorkflowInputForm.COMMON,
            expression,
            "",
            "",
            "s",
            parameters,
            "frequency",
        ),
        mode,
        single,
        omega_min,
        omega_max,
        points,
        "",
        (
            FrequencyPhasePresentation.PRINCIPAL_AND_UNWRAPPED
            if unwrap
            else FrequencyPhasePresentation.PRINCIPAL_ONLY
        ),
    )


def _execute(
    presenter: FrequencyDomainPresenter,
    draft: FrequencyDomainInputDraft,
) -> FrequencyDomainWorkflowRequest:
    requests: list[object] = []
    presenter.execution_requested.connect(requests.append)
    assert presenter.submit(draft)
    assert len(requests) == 1
    request = requests[0]
    assert type(request) is FrequencyDomainWorkflowRequest
    presenter.accept_result(FrequencyDomainWorkflowService().run(request))
    return request


def test_frequency_view_state_is_immutable_widget_free_and_string_only() -> None:
    state = FrequencyDomainViewState()

    with pytest.raises(FrozenInstanceError):
        state.general_message = "changed"  # type: ignore[misc]
    assert "PySide6" not in type(state).__module__
    assert all(
        type(getattr(state.summary, name)) is str
        for name in state.summary.__dataclass_fields__
    )


def test_presenter_dispatches_one_exact_single_point_request() -> None:
    presenter = FrequencyDomainPresenter(FrequencyDomainRequestFactory())
    request = _execute(
        presenter,
        _draft(
            "1/(s+1)",
            mode=FrequencyDomainWorkflowMode.SINGLE_POINT,
            single="1",
        ),
    )

    assert request.mode is FrequencyDomainWorkflowMode.SINGLE_POINT
    assert presenter.state.run_status is FrequencyDomainUiRunStatus.COMPLETE
    assert presenter.state.summary.mode == "Einzelpunkt"
    assert presenter.state.summary.frequency_count == "1"
    assert presenter.state.single_point.omega == "1"
    assert presenter.state.single_point.status == "Definiert"
    assert presenter.state.single_point.complex_value == "1/2 - I/2"
    assert presenter.state.single_point.real_part == "1/2"
    assert presenter.state.single_point.imaginary_part == "-1/2"
    assert presenter.state.single_point.magnitude
    assert presenter.state.single_point.decibel
    assert presenter.state.single_point.principal_phase


def test_zero_response_and_singularity_have_no_invented_values() -> None:
    zero = FrequencyDomainPresenter(FrequencyDomainRequestFactory())
    _execute(
        zero,
        _draft(
            "0/(s+1)",
            mode=FrequencyDomainWorkflowMode.SINGLE_POINT,
            single="1",
        ),
    )
    assert zero.state.single_point.status == "Nullantwort"
    assert zero.state.single_point.decibel == "−∞"
    assert zero.state.single_point.principal_phase == "nicht definiert"

    singular = FrequencyDomainPresenter(FrequencyDomainRequestFactory())
    _execute(
        singular,
        _draft(
            "1/s",
            mode=FrequencyDomainWorkflowMode.SINGLE_POINT,
            single="0",
        ),
    )
    assert singular.state.single_point.status == "Singularität"
    assert singular.state.single_point.complex_value == ""
    assert singular.state.single_point.magnitude == ""


def test_bode_rows_preserve_order_and_fill_unwrap_only_when_present() -> None:
    principal = FrequencyDomainPresenter(FrequencyDomainRequestFactory())
    _execute(
        principal,
        _draft(
            "1/(s+1)",
            mode=FrequencyDomainWorkflowMode.BODE,
            omega_min="1/10",
            omega_max="10",
            points="4",
        ),
    )
    assert principal.state.rows
    assert all(not row.unwrapped_phase for row in principal.state.rows)
    assert tuple(int(row.index) for row in principal.state.rows) == tuple(
        range(1, len(principal.state.rows) + 1)
    )
    assert principal.state.summary.magnitude_segment_count == "1"
    assert principal.state.summary.phase_segment_count == "1"

    unwrapped = FrequencyDomainPresenter(FrequencyDomainRequestFactory())
    _execute(
        unwrapped,
        _draft(
            "1/(s+1)^3",
            mode=FrequencyDomainWorkflowMode.BODE,
            omega_min="1/10",
            omega_max="100",
            points="4",
            unwrap=True,
        ),
    )
    assert unwrapped.state.summary.phase_unwrap == "aktiv"
    assert any(row.unwrapped_phase for row in unwrapped.state.rows)


def test_zero_response_bode_rows_show_negative_infinity_without_phase() -> None:
    presenter = FrequencyDomainPresenter(FrequencyDomainRequestFactory())
    _execute(
        presenter,
        _draft(
            "0/(s+1)",
            mode=FrequencyDomainWorkflowMode.BODE,
            omega_min="1/10",
            omega_max="10",
            points="2",
        ),
    )

    assert presenter.state.rows
    assert all(row.decibel == "−∞" for row in presenter.state.rows)
    assert all(not row.principal_phase for row in presenter.state.rows)
    assert all(not row.unwrapped_phase for row in presenter.state.rows)


def test_diagnostics_are_projected_once_in_original_order() -> None:
    presenter = FrequencyDomainPresenter(FrequencyDomainRequestFactory())
    requests: list[object] = []
    presenter.execution_requested.connect(requests.append)
    assert presenter.submit(
        _draft(
            "K/(s+1)",
            mode=FrequencyDomainWorkflowMode.BODE,
            omega_min="1/10",
            omega_max="10",
            points="2",
            parameters=(ParameterInputDraft("K", "", ""),),
        )
    )
    request = requests[0]
    assert type(request) is FrequencyDomainWorkflowRequest
    result = FrequencyDomainWorkflowService().run(request)
    presenter.accept_result(result)

    assert len(presenter.state.diagnostics) == len(result.diagnostics)
    assert tuple(item.message for item in presenter.state.diagnostics) == tuple(
        item.message for item in result.diagnostics
    )
