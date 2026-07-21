"""Focused F1B Nyquist reference regressions."""

from __future__ import annotations

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
    ClosedLoopStabilityStatus,
    ExactRationalValue,
    LogFrequencyGridRequest,
    NyquistAnalysisResult,
    ScalarGainDomain,
)


def _analyze(expression: str, domain: ScalarGainDomain | None = None) -> NyquistAnalysisResult:
    request = FrequencyDomainWorkflowRequest(
        TransferFunctionWorkflowRequest(
            WorkflowInputForm.COMMON,
            common_expression_text=expression,
            field="frequency",
        ),
        FrequencyDomainWorkflowMode.BODE,
        grid_request=LogFrequencyGridRequest(
            ExactRationalValue(1, 1000), ExactRationalValue(1000), 16
        ),
        phase_presentation=FrequencyPhasePresentation.PRINCIPAL_AND_UNWRAPPED,
        include_reserves=True,
        include_nyquist=True,
        scalar_gain_domain=domain,
    )
    result = FrequencyDomainWorkflowService().run(request)
    assert result.nyquist_analysis is not None
    return result.nyquist_analysis


@pytest.mark.parametrize(
    ("expression", "p", "n_cw", "z", "status"),
    (
        ("2.5*(1-s)/(s^2+3*s+2)", 0, 0, 0, ClosedLoopStabilityStatus.ASYMPTOTICALLY_STABLE),
        ("6*s/((s-1)*(s-2))", 2, -2, 0, ClosedLoopStabilityStatus.ASYMPTOTICALLY_STABLE),
        ("2/(s^3+2.3*s^2+1.6*s+2)", 0, 2, 2, ClosedLoopStabilityStatus.UNSTABLE),
    ),
)
def test_nyquist_reference_decisions(
    expression: str, p: int, n_cw: int, z: int, status: ClosedLoopStabilityStatus
) -> None:
    result = _analyze(expression)
    assert result.pole_classification.rhp_pole_count == p
    assert result.winding.clockwise_encirclements == n_cw
    assert result.stability.rhp_closed_poles == z
    assert result.stability.status is status


def test_origin_pole_rejects_standard_count() -> None:
    result = _analyze("(25*s+60)/(10*s^3+10*s^2+25*s)")
    assert result.pole_classification.origin_poles
    assert result.winding.clockwise_encirclements is None
    assert result.stability.status is ClosedLoopStabilityStatus.NOT_DETERMINED


def test_scalar_gain_full_and_positive_domains() -> None:
    expression = "3/(9*s^3+27*s^2+19*s+1)"
    full = _analyze(expression, ScalarGainDomain(None, None)).scalar_gain_range
    positive = _analyze(expression, ScalarGainDomain(0.0, None)).scalar_gain_range
    assert full is not None and positive is not None
    assert full.critical_gains == pytest.approx((-1 / 3, 56 / 3))
    assert [(item.lower, item.upper) for item in full.stable_intervals] == pytest.approx(
        [(-1 / 3, 56 / 3)]
    )
    assert [(item.lower, item.upper) for item in positive.stable_intervals] == pytest.approx(
        [(0, 56 / 3)]
    )
