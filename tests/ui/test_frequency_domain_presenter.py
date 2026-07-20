"""Frequency presenter request and display projections."""

import re
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


def test_visible_statuses_are_german_and_long_values_keep_full_tooltips() -> None:
    presenter = FrequencyDomainPresenter(FrequencyDomainRequestFactory())
    _execute(
        presenter,
        _draft(
            "1/(s+1)",
            mode=FrequencyDomainWorkflowMode.BODE,
            omega_min="1/100",
            omega_max="100",
            points="4",
        ),
    )

    assert presenter.state.summary.workflow_status == "Vollständig"
    assert presenter.state.summary.domain_status == "Vollständig"
    assert "complete" not in tuple(
        getattr(presenter.state.summary, name)
        for name in presenter.state.summary.__dataclass_fields__
    )
    row = presenter.state.rows[1]
    assert len(row.real_part) <= 12
    assert row.tooltips[4]
    assert row.tooltips[4] != row.real_part


def test_single_point_worked_steps_use_existing_exact_and_numeric_values() -> None:
    presenter = FrequencyDomainPresenter(FrequencyDomainRequestFactory())
    _execute(
        presenter,
        _draft(
            "1/(s+1)",
            mode=FrequencyDomainWorkflowMode.SINGLE_POINT,
            single="1",
        ),
    )

    assert not presenter.state.plot.visible
    assert len(presenter.state.worked_steps.point_details) == 1
    general = dict(presenter.state.worked_steps.general_lines)
    detail = dict(presenter.state.worked_steps.point_details[0].lines)
    assert general["Ansatz"] == "s = jω"
    assert general["Reduzierte Übertragungsfunktion"] == "(1) / (s + 1)"
    assert detail["ω"] == "1 rad/s"
    assert detail["Spezialisierter Zähler"] == "1"
    assert detail["Spezialisierter Nenner"] == "1 + I"
    assert detail["G(jω)"] == "1/2 - I/2"
    assert detail["Betragsquadrat"] == "1/2"
    assert detail["L(ω) = 20 log10(|G(jω)|)"]
    assert detail["Hauptphase"].endswith("°")
    assert detail["Punktstatus"] == "Definiert"

    short = presenter.state.worked_steps.short_solutions[0]
    ordered_steps = (
        "1. Einsetzen von s = jω",
        "2. Komplexer Wert",
        "3. Betrag",
        "4. Dezibelwert",
        "5. Phase",
    )
    assert tuple(short.index(step) for step in ordered_steps) == tuple(
        sorted(short.index(step) for step in ordered_steps)
    )
    assert "1/2 - I/2" in short
    assert "|G(j)| ≈ 0.707107" in short
    assert "L(1) ≈ -3.0103 dB" in short
    assert "φ(1) = -45°" in short
    assert re.search(r"\d{15}", short) is None
    assert "0.707106781186547" in detail["Betrag"]


def test_pt1_plot_projection_preserves_principal_domain_segments() -> None:
    presenter = FrequencyDomainPresenter(FrequencyDomainRequestFactory())
    _execute(
        presenter,
        _draft(
            "1/(s+1)",
            mode=FrequencyDomainWorkflowMode.BODE,
            omega_min="1/100",
            omega_max="100",
            points="4",
        ),
    )

    plot = presenter.state.plot
    assert plot.visible
    assert len(plot.magnitude_segments) == 1
    assert len(plot.principal_phase_segments) == 1
    assert not plot.unwrapped_phase_segments
    assert plot.magnitude_segments[0].x_values == (
        plot.principal_phase_segments[0].x_values
    )
    assert plot.magnitude_segments[0].x_values == tuple(
        row.tooltips[1] for row in presenter.state.rows
    )
    assert len(plot.magnitude_segments[0].x_values) == len(
        presenter.state.rows
    )


def test_three_pt1_factors_keep_principal_and_add_unwrapped_phase() -> None:
    presenter = FrequencyDomainPresenter(FrequencyDomainRequestFactory())
    _execute(
        presenter,
        _draft(
            "1/(s/10+1)^3",
            mode=FrequencyDomainWorkflowMode.BODE,
            omega_min="1/100",
            omega_max="1000",
            points="4",
            unwrap=True,
        ),
    )

    plot = presenter.state.plot
    assert len(plot.principal_phase_segments) == 1
    assert len(plot.unwrapped_phase_segments) == 1
    assert plot.principal_phase_segments[0].x_values == (
        plot.unwrapped_phase_segments[0].x_values
    )
    assert any(
        dict(detail.lines)["360°-Offset"] != "0 × 360°"
        for detail in presenter.state.worked_steps.point_details
    )


def test_singularity_keeps_segments_separate_and_marks_interruption() -> None:
    presenter = FrequencyDomainPresenter(FrequencyDomainRequestFactory())
    _execute(
        presenter,
        _draft(
            "1/(s^2+1)",
            mode=FrequencyDomainWorkflowMode.BODE,
            omega_min="1/100",
            omega_max="100",
            points="4",
        ),
    )

    plot = presenter.state.plot
    assert len(plot.magnitude_segments) == 2
    assert len(plot.principal_phase_segments) == 2
    assert all(len(segment.x_values) == 8 for segment in plot.magnitude_segments)
    singular_index = next(
        index
        for index, row in enumerate(presenter.state.rows)
        if row.status == "Singularität"
    )
    detail = dict(
        presenter.state.worked_steps.point_details[singular_index].lines
    )
    assert "Unterbrechung" in detail["Plotsegment"]
    assert presenter.state.rows[singular_index].target_omega not in {
        value
        for segment in plot.magnitude_segments
        for value in segment.x_values
    }
    assert tuple(
        (marker.x_value, marker.label)
        for marker in plot.interruption_markers
    ) == (("1", "Singularität"),)
    assert "Singularität bei ω = 1 rad/s" in (
        presenter.state.worked_steps.short_solutions[singular_index]
    )


def test_zero_response_has_stable_empty_plot_without_invented_points() -> None:
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

    assert presenter.state.summary.domain_status == (
        "Keine darstellbaren Daten"
    )
    assert presenter.state.plot.visible
    assert not presenter.state.plot.magnitude_segments
    assert not presenter.state.plot.principal_phase_segments
    assert not presenter.state.plot.unwrapped_phase_segments
    assert presenter.state.plot.no_data_message
    assert all(row.decibel == "−∞" for row in presenter.state.rows)
