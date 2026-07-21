"""Focused presenter and LaTeX smoke tests for F1A."""

from __future__ import annotations

from klausurbotpro.application import (
    FrequencyDomainInputDraft,
    FrequencyDomainRequestFactory,
    FrequencyDomainWorkflowMode,
    FrequencyDomainWorkflowRequest,
    FrequencyDomainWorkflowService,
    FrequencyPhasePresentation,
    TransferFunctionInputDraft,
    WorkflowInputForm,
)
from klausurbotpro.ui import FrequencyDomainPresenter


def _present(expression: str) -> FrequencyDomainPresenter:
    presenter = FrequencyDomainPresenter(FrequencyDomainRequestFactory())
    dispatched: list[object] = []
    presenter.execution_requested.connect(dispatched.append)
    draft = FrequencyDomainInputDraft(
        TransferFunctionInputDraft(
            WorkflowInputForm.COMMON,
            expression,
            "",
            "",
            "s",
            (),
            "frequency",
        ),
        FrequencyDomainWorkflowMode.BODE,
        "",
        "1/100",
        "100",
        "8",
        "",
        FrequencyPhasePresentation.PRINCIPAL_AND_UNWRAPPED,
    )
    assert presenter.submit(draft)
    request = dispatched[0]
    assert type(request) is FrequencyDomainWorkflowRequest
    presenter.accept_result(FrequencyDomainWorkflowService().run(request))
    return presenter


def test_r1_presenter_plot_worked_steps_and_latex_are_integrated() -> None:
    state = _present("2.5*(1-s)/(s^2+3*s+2)").state
    assert [row.index for row in state.reserve_rows] == ["G1", "P1"]
    assert "PM = 30.5102" in state.reserve_rows[0].reserve
    assert "Faktor 1.2" in state.reserve_rows[1].reserve
    assert state.plot.gain_crossover_markers[0].label == "ωg1"
    assert state.plot.phase_crossover_markers[0].label == "ωp1"
    worked = dict(state.worked_steps.general_lines)
    assert "PM=180°+φentf" in worked["G1: PM"]
    assert "1/|G(jωp)|" in worked["P1: GM"]
    assert r"\section*{Durchtritte und Reserven}" in state.latex_report
    assert r"\varphi_{\mathrm{entf}}" in state.latex_report


def test_r3_non_applicable_values_are_readable_not_nan_or_zero() -> None:
    state = _present("0.5/(1+s)").state
    assert state.reserve_rows[0].crossover == "Keine Durchtritte"
    assert "formal unbeschränkt" in state.reserve_rows[0].reserve
    assert "Phasenreserve nicht definiert" in state.latex_report
    assert "formal unbeschränkt" in state.latex_report
    assert "NaN" not in state.latex_report


def test_r4_negative_margin_keeps_minus_sign() -> None:
    state = _present("(25*s+60)/(10*s^3+10*s^2+25*s)").state
    assert "PM = -6.706" in state.reserve_rows[0].reserve
    assert "-6.706" in state.latex_report


def test_r2_multiple_gain_crossovers_are_tabulated() -> None:
    state = _present("0.5/(s^2+0.5*s+1)").state
    assert [row.index for row in state.reserve_rows[:2]] == ["G1", "G2"]
    assert "120" in state.reserve_rows[0].reserve
    assert "90" in state.reserve_rows[1].reserve
    assert state.latex_report.count(r"\omega_g") >= 3


def test_r5_source_correction_is_presented_near_ninety_degrees() -> None:
    state = _present("100/(1+2*s)").state
    assert "90.573" in state.reserve_rows[0].reserve
    assert "270" not in state.reserve_rows[0].reserve
