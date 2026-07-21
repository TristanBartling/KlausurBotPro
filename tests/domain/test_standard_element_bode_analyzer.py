"""Targeted tests for the exact standard-element Bode MVP."""

from klausurbotpro.application import (
    TransferFunctionPreparationService,
    TransferFunctionWorkflowRequest,
    WorkflowInputForm,
)
from klausurbotpro.domain import (
    DiagnosticCode,
    ReducedTransferFunction,
    StandardElementBodeAnalyzer,
    StandardElementBodeStatus,
    StandardElementUnsupportedReason,
)


def _reduced(expression: str) -> ReducedTransferFunction:
    prepared = TransferFunctionPreparationService().prepare(
        TransferFunctionWorkflowRequest(
            WorkflowInputForm.COMMON,
            common_expression_text=expression,
            field="frequency",
        )
    )
    assert prepared.reduced_value is not None, prepared.diagnostics
    return prepared.reduced_value


def test_integrator_and_lhp_pole_are_reconstructed_exactly() -> None:
    result = StandardElementBodeAnalyzer().analyze(
        _reduced("100/(s*(10*s+1))")
    )

    assert result.status is StandardElementBodeStatus.SUPPORTED
    assert result.gain is not None
    assert result.gain.canonical_text == "100"
    assert result.origin_zero_multiplicity == 0
    assert result.origin_pole_multiplicity == 1
    assert tuple(
        (factor.root.canonical_text, factor.corner_frequency.canonical_text)
        for factor in result.pole_factors
    ) == (("-1/10", "1/10"),)
    assert result.initial_slope_db_per_decade == -20
    assert tuple(
        (
            event.corner_frequency.canonical_text,
            event.slope_change_db_per_decade,
            event.slope_after_db_per_decade,
        )
        for event in result.corner_events
    ) == (("1/10", -20, -40),)
    assert result.reconstruction_verified


def test_lhp_pole_and_zero_have_sorted_corner_events() -> None:
    result = StandardElementBodeAnalyzer().analyze(
        _reduced("1000*(1+0.002*s)/(1+2*s)")
    )

    assert result.status is StandardElementBodeStatus.SUPPORTED
    assert result.gain is not None
    assert result.gain.canonical_text == "1000"
    assert tuple(
        (factor.root.canonical_text, factor.corner_frequency.canonical_text)
        for factor in result.pole_factors
    ) == (("-1/2", "1/2"),)
    assert tuple(
        (factor.root.canonical_text, factor.corner_frequency.canonical_text)
        for factor in result.zero_factors
    ) == (("-500", "500"),)
    assert result.initial_slope_db_per_decade == 0
    assert tuple(
        (
            event.corner_frequency.canonical_text,
            event.slope_after_db_per_decade,
        )
        for event in result.corner_events
    ) == (("1/2", -20), ("500", 0))
    assert result.reconstruction_verified


def test_complex_pole_pair_returns_no_partial_decomposition() -> None:
    result = StandardElementBodeAnalyzer().analyze(
        _reduced("1/(s^2+s+1)")
    )

    assert result.status is StandardElementBodeStatus.UNSUPPORTED
    assert result.unsupported_reason is StandardElementUnsupportedReason.COMPLEX_ROOT
    assert result.gain is None
    assert result.origin_zero_multiplicity == 0
    assert result.origin_pole_multiplicity == 0
    assert not result.zero_factors
    assert not result.pole_factors
    assert not result.corner_events
    assert result.initial_slope_db_per_decade is None
    assert not result.reconstruction_verified
    assert result.diagnostics[0].code is DiagnosticCode.STANDARD_ELEMENT_BODE_UNSUPPORTED
    assert "komplexe Polstelle" in result.diagnostics[0].message
