"""Focused F2 checks for primitive Bode contributions and PT2."""

from math import atan, degrees, hypot, log10

import pytest

from klausurbotpro.application import (
    TransferFunctionPreparationService,
    TransferFunctionWorkflowRequest,
    WorkflowInputForm,
)
from klausurbotpro.domain import (
    BodeSketchMode,
    ReducedTransferFunction,
    StandardElementBodeAnalyzer,
    StandardElementFactorKind,
    StandardElementUnsupportedReason,
    standard_element_contributions,
)


def _reduced(expression: str) -> ReducedTransferFunction:
    prepared = TransferFunctionPreparationService().prepare(
        TransferFunctionWorkflowRequest(
            WorkflowInputForm.COMMON,
            common_expression_text=expression,
            field="frequency",
        )
    )
    assert prepared.reduced_value is not None
    return prepared.reduced_value


def test_case_1_exact_primitive_sum_matches_total() -> None:
    result = StandardElementBodeAnalyzer().analyze(_reduced("100/(s*(10*s+1))"))
    frequencies = (0.01, 0.1, 1.0, 10.0)
    contributions = standard_element_contributions(
        result, frequencies, BodeSketchMode.EXACT
    )

    for index, omega in enumerate(frequencies):
        magnitude = sum(row.magnitudes_db[index] for row in contributions)
        phase = sum(row.phases_degrees[index] for row in contributions)
        expected_magnitude = 20 * log10(100 / (omega * hypot(1, 10 * omega)))
        expected_phase = -90 - degrees(atan(10 * omega))
        assert magnitude == pytest.approx(expected_magnitude, abs=1e-10)
        assert phase == pytest.approx(expected_phase, abs=1e-10)


def test_case_2_has_two_distinct_corner_frequencies() -> None:
    result = StandardElementBodeAnalyzer().analyze(
        _reduced("1000*(1+0.002*s)/(1+2*s)")
    )
    assert tuple(
        float(event.corner_frequency._as_sympy()) for event in result.corner_events
    ) == (0.5, 500.0)


def test_case_3_pt2_parameters_and_exact_reconstruction() -> None:
    result = StandardElementBodeAnalyzer().analyze(_reduced("1/(s^2+0.4*s+1)"))
    assert result.supported and result.reconstruction_verified
    assert len(result.pole_factors) == 1
    factor = result.pole_factors[0]
    assert factor.kind is StandardElementFactorKind.PT2
    assert float(factor.corner_frequency._as_sympy()) == pytest.approx(1.0)
    assert factor.damping_ratio is not None
    assert float(factor.damping_ratio._as_sympy()) == pytest.approx(0.2)


def test_unclassified_complex_numerator_stays_safely_unsupported() -> None:
    result = StandardElementBodeAnalyzer().analyze(_reduced("(s^2+s+1)/(s+1)"))
    assert not result.supported
    assert result.unsupported_reason is StandardElementUnsupportedReason.COMPLEX_ROOT
    assert result.gain is None
