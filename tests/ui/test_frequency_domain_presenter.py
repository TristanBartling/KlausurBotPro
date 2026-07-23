"""Frequency presenter request and display projections."""

import re
from dataclasses import FrozenInstanceError, replace

import pytest

from klausurbotpro.application import (
    FrequencyDomainInputDraft,
    FrequencyDomainRequestFactory,
    FrequencyDomainWorkflowLimits,
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
    if len(requests) == 2:
        refined_request = requests[1]
        assert type(refined_request) is FrequencyDomainWorkflowRequest
        presenter.accept_result(
            FrequencyDomainWorkflowService().run(refined_request)
        )
    assert len(requests) <= 2
    final_request = requests[-1]
    assert type(final_request) is FrequencyDomainWorkflowRequest
    return final_request


def _run_all_requests(
    presenter: FrequencyDomainPresenter,
    draft: FrequencyDomainInputDraft,
    limits: FrequencyDomainWorkflowLimits | None = None,
) -> tuple[FrequencyDomainWorkflowRequest, ...]:
    if limits is None:
        limits = FrequencyDomainWorkflowLimits()
    dispatched: list[object] = []
    presenter.execution_requested.connect(dispatched.append)
    assert presenter.submit(draft)
    handled = 0
    while handled < len(dispatched):
        request = dispatched[handled]
        assert type(request) is FrequencyDomainWorkflowRequest
        handled += 1
        presenter.accept_result(
            FrequencyDomainWorkflowService(limits).run(request)
        )
    requests: list[FrequencyDomainWorkflowRequest] = []
    for request in dispatched:
        assert type(request) is FrequencyDomainWorkflowRequest
        requests.append(request)
    return tuple(requests)


def test_frequency_view_state_is_immutable_widget_free_and_string_only() -> None:
    state = FrequencyDomainViewState()

    with pytest.raises(FrozenInstanceError):
        state.general_message = "changed"  # type: ignore[misc]
    assert "PySide6" not in type(state).__module__
    assert all(
        type(getattr(state.summary, name)) is str
        for name in state.summary.__dataclass_fields__
    )


def test_oversized_bode_grid_focuses_points_per_decade_field() -> None:
    presenter = FrequencyDomainPresenter(FrequencyDomainRequestFactory())

    _execute(
        presenter,
        _draft(
            "1/(s+1)",
            mode=FrequencyDomainWorkflowMode.BODE,
            omega_min="1/1000",
            omega_max="1000",
            points="64",
        ),
    )

    assert presenter.state.focused_field == "points_per_decade"
    assert any(
        "385 Punkte angefordert" in diagnostic.message
        for diagnostic in presenter.state.diagnostics
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
    assert presenter.state.single_point.magnitude == "0.707107"
    assert presenter.state.single_point.decibel == "-3.0103"
    assert presenter.state.single_point.principal_phase == "-45"
    assert r"\section*{Lösung}" in presenter.state.latex_report
    assert r"G(\mathrm{j})=\frac{1}{1 + \mathrm{j}}" in (
        presenter.state.latex_report
    )


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

    assert result.nyquist_analysis is None
    assert not presenter.state.nyquist.visible
    assert "Belege K numerisch" in presenter.state.latex_report
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
    assert len(plot.magnitude_segments[0].x_values) > len(presenter.state.rows)


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
    assert all(len(segment.x_values) == 9 for segment in plot.magnitude_segments)
    singular_row = next(
        index
        for index, row in enumerate(presenter.state.rows)
        if row.status == "Singularität"
    )
    singular_index = presenter.state.bode_indices[singular_row]
    detail = dict(
        presenter.state.worked_steps.point_details[singular_index].lines
    )
    assert "Unterbrechung" in detail["Plotsegment"]
    assert presenter.state.rows[singular_row].target_omega not in {
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
    assert {
        row.evaluation_omega for row in presenter.state.rows
    } >= {"99/100", "101/100"}
    assert presenter.state.summary.added_frequencies == "0.99; 1.01 rad/s"


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


def test_regular_bode_and_single_point_each_dispatch_exactly_once() -> None:
    bode = FrequencyDomainPresenter(FrequencyDomainRequestFactory())
    bode_requests = _run_all_requests(
        bode,
        _draft(
            "1/(s+1)",
            mode=FrequencyDomainWorkflowMode.BODE,
            omega_min="1/10",
            omega_max="10",
            points="4",
        ),
    )
    single = FrequencyDomainPresenter(FrequencyDomainRequestFactory())
    single_requests = _run_all_requests(
        single,
        _draft(
            "1/(s+1)",
            mode=FrequencyDomainWorkflowMode.SINGLE_POINT,
            single="1",
        ),
    )

    assert len(bode_requests) == 1
    assert len(single_requests) == 1


def test_singular_bode_dispatches_one_refinement_and_never_a_third_run() -> None:
    presenter = FrequencyDomainPresenter(FrequencyDomainRequestFactory())
    dispatched: list[object] = []
    presenter.execution_requested.connect(dispatched.append)
    assert presenter.submit(
        _draft(
            "1/(s^2+1)",
            mode=FrequencyDomainWorkflowMode.BODE,
            omega_min="1/10",
            omega_max="10",
            points="4",
        )
    )
    first = dispatched[0]
    assert type(first) is FrequencyDomainWorkflowRequest
    presenter.accept_result(FrequencyDomainWorkflowService().run(first))

    assert len(dispatched) == 2
    assert presenter.state.run_status is FrequencyDomainUiRunStatus.RUNNING
    assert "automatisch verfeinert" in presenter.state.general_message
    second = dispatched[1]
    assert type(second) is FrequencyDomainWorkflowRequest
    assert second.grid_request is not None
    assert tuple(
        (value.numerator, value.denominator)
        for value in second.grid_request.explicit_frequencies
    ) == (
        (99, 100),
        (101, 100),
    )
    presenter.accept_result(FrequencyDomainWorkflowService().run(second))

    assert len(dispatched) == 2
    assert presenter.state.run_status.value == (
        FrequencyDomainUiRunStatus.COMPLETE.value
    )
    assert "0.99; 1.01 rad/s" in presenter.state.general_message


def test_new_submit_and_reset_each_reenable_one_refinement_round() -> None:
    presenter = FrequencyDomainPresenter(FrequencyDomainRequestFactory())
    draft = _draft(
        "1/(s^2+1)",
        mode=FrequencyDomainWorkflowMode.BODE,
        omega_min="1/10",
        omega_max="10",
        points="4",
    )

    assert len(_run_all_requests(presenter, draft)) == 2
    assert len(_run_all_requests(presenter, draft)) == 2
    assert presenter.reset()
    assert len(_run_all_requests(presenter, draft)) == 2


def test_refinement_limit_keeps_complete_base_result_with_hint() -> None:
    defaults = FrequencyDomainWorkflowLimits()
    limits = replace(
        defaults,
        grid=replace(defaults.grid, max_explicit_points=1),
    )
    presenter = FrequencyDomainPresenter(FrequencyDomainRequestFactory(limits))

    requests = _run_all_requests(
        presenter,
        _draft(
            "1/(s^2+1)",
            mode=FrequencyDomainWorkflowMode.BODE,
            omega_min="1/10",
            omega_max="10",
            points="4",
        ),
        limits,
    )

    assert len(requests) == 1
    assert presenter.state.run_status is FrequencyDomainUiRunStatus.COMPLETE
    assert presenter.state.rows
    assert "Frequenzlimit" in presenter.state.general_message
    assert "Basisergebnis" in presenter.state.general_message


def test_bode_selection_updates_latex_point_without_recomputing_workflow() -> None:
    presenter = FrequencyDomainPresenter(FrequencyDomainRequestFactory())
    requests = _run_all_requests(
        presenter,
        _draft(
            "1/(s+1)",
            mode=FrequencyDomainWorkflowMode.BODE,
            omega_min="1/10",
            omega_max="10",
            points="4",
        ),
    )
    initial = presenter.state.latex_report

    presenter.select_bode_row(2)

    assert len(requests) == 1
    assert presenter.state.selected_bode_index == 2
    assert presenter.state.latex_report != initial
    assert r"\section*{Ausgewählter Tabellenpunkt}" in (
        presenter.state.latex_report
    )


def test_new_calculation_resets_selected_bode_row() -> None:
    presenter = FrequencyDomainPresenter(FrequencyDomainRequestFactory())
    draft = _draft(
        "1/(s+1)",
        mode=FrequencyDomainWorkflowMode.BODE,
        omega_min="1/10",
        omega_max="10",
        points="4",
    )
    _run_all_requests(presenter, draft)
    presenter.select_bode_row(2)
    assert presenter.state.selected_bode_index == 2

    _run_all_requests(presenter, draft)

    assert presenter.state.selected_bode_index == 0


def test_refined_bode_latex_names_only_added_support_frequencies() -> None:
    presenter = FrequencyDomainPresenter(FrequencyDomainRequestFactory())
    _run_all_requests(
        presenter,
        _draft(
            "1/(s^2+1)",
            mode=FrequencyDomainWorkflowMode.BODE,
            omega_min="1/10",
            omega_max="10",
            points="4",
        ),
    )

    latex = presenter.state.latex_report
    assert "Automatisch ergänzte Stützstellen" in latex
    assert r"\frac{99}{100}\,\mathrm{rad/s}" in latex
    assert r"\frac{101}{100}\,\mathrm{rad/s}" in latex
