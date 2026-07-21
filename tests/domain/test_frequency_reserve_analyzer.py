"""Focused regression tests for crossovers and frequency reserves."""

from __future__ import annotations

from math import sqrt

import pytest

from klausurbotpro.application import (
    FrequencyDomainWorkflowMode,
    FrequencyDomainWorkflowRequest,
    FrequencyDomainWorkflowService,
    FrequencyPhasePresentation,
    TransferFunctionWorkflowRequest,
    WorkflowInputForm,
)
from klausurbotpro.domain import (
    BandCompletenessStatus,
    CrossoverDetectionMethod,
    ExactRationalValue,
    FrequencyCrossoverAnalysis,
    LogFrequencyGridRequest,
    ReserveInterpretationStatus,
    StabilityReserveAnalysis,
)


def _analyze(
    expression: str,
    *,
    explicit: tuple[ExactRationalValue, ...] = (),
) -> tuple[FrequencyCrossoverAnalysis, StabilityReserveAnalysis]:
    request = FrequencyDomainWorkflowRequest(
        TransferFunctionWorkflowRequest(
            WorkflowInputForm.COMMON,
            common_expression_text=expression,
            field="frequency",
        ),
        FrequencyDomainWorkflowMode.BODE,
        grid_request=LogFrequencyGridRequest(
            ExactRationalValue(1, 100),
            ExactRationalValue(100),
            8,
            explicit,
        ),
        phase_presentation=FrequencyPhasePresentation.PRINCIPAL_AND_UNWRAPPED,
    )
    result = FrequencyDomainWorkflowService().run(request)
    assert result.crossover_analysis is not None
    assert result.reserve_analysis is not None
    return result.crossover_analysis, result.reserve_analysis


def test_r1_complete_gain_phase_and_reserves() -> None:
    crossovers, reserves = _analyze("2.5*(1-s)/(s^2+3*s+2)")
    assert crossovers.gain_crossovers[0].frequency == pytest.approx(1.5)
    phase = crossovers.phase_crossovers[0]
    assert phase.frequency == pytest.approx(sqrt(5))
    assert phase.complex_value.real == pytest.approx(-5 / 6)
    assert reserves.phase_margins[0].value == pytest.approx(30.5102, abs=1e-3)
    assert reserves.gain_margins_db[0].value == pytest.approx(1.5836, abs=1e-3)
    assert reserves.gain_margin_factors[0].value == pytest.approx(6 / 5)
    gain_margin_db = reserves.gain_margins_db[0].value
    assert gain_margin_db is not None
    assert 10 ** (gain_margin_db / 20) == pytest.approx(reserves.gain_margin_factors[0].value)


def test_r2_retains_both_gain_crossovers() -> None:
    crossovers, reserves = _analyze("0.5/(s^2+0.5*s+1)")
    assert [item.frequency for item in crossovers.gain_crossovers] == pytest.approx(
        [sqrt(3) / 2, 1.0]
    )
    assert [item.value for item in reserves.phase_margins] == pytest.approx([120.0, 90.0])
    assert not crossovers.phase_crossovers
    assert reserves.multiple_crossovers


def test_r3_missing_crossovers_have_textual_semantics() -> None:
    crossovers, reserves = _analyze("0.5/(1+s)")
    assert not crossovers.gain_crossovers
    assert not crossovers.phase_crossovers
    assert crossovers.completeness is BandCompletenessStatus.COMPLETE_IN_PROVEN_RANGE
    assert reserves.phase_margins[0].value is None
    assert reserves.phase_margins[0].interpretation is ReserveInterpretationStatus.NOT_DEFINED
    assert (
        reserves.gain_margins_db[0].interpretation is ReserveInterpretationStatus.FORMALLY_UNBOUNDED
    )


def test_r4_negative_phase_margin_is_not_wrapped() -> None:
    crossovers, reserves = _analyze("(25*s+60)/(10*s^3+10*s^2+25*s)")
    assert crossovers.phase_crossovers[0].frequency == pytest.approx(sqrt(30 / 7))
    assert crossovers.phase_crossovers[0].complex_value.real == pytest.approx(-1.4)
    assert reserves.gain_margin_factors[0].value == pytest.approx(5 / 7)
    assert reserves.gain_margins_db[0].value == pytest.approx(-2.92256, abs=1e-4)
    assert crossovers.gain_crossovers[0].frequency == pytest.approx(2.29948, abs=1e-4)
    assert reserves.phase_margins[0].value == pytest.approx(-6.706, abs=1e-3)


def test_r5_corrected_source_value_is_near_ninety_degrees() -> None:
    _, reserves = _analyze("100/(1+2*s)")
    assert reserves.phase_margins[0].value == pytest.approx(90.573, abs=1e-3)


def test_r6_singularity_segments_remain_distinct_and_visible() -> None:
    crossovers, _ = _analyze("1/(s^2+4)", explicit=(ExactRationalValue(2),))
    assert len(crossovers.evaluated_segments) == 2
    assert crossovers.completeness is BandCompletenessStatus.SEGMENT_INCOMPLETE


def test_tangential_gain_touch_is_accepted_but_near_miss_is_rejected() -> None:
    accepted, _ = _analyze("(24/25)/(s^2+(6/5)*s+1)")
    rejected, _ = _analyze("(23/25)/(s^2+(6/5)*s+1)")
    assert accepted.gain_crossovers[0].frequency == pytest.approx(sqrt(7) / 5)
    assert accepted.gain_crossovers[0].detection_method is (
        CrossoverDetectionMethod.TANGENTIAL_CANDIDATE
    )
    assert not rejected.gain_crossovers


def test_nonzero_phase_branch_is_preserved() -> None:
    crossovers, _ = _analyze("1/(s+1)^8")
    assert any(item.phase_branch_index == 1 for item in crossovers.phase_crossovers)
