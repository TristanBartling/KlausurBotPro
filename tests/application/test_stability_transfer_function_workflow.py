"""Focused integration tests for stability input via a complete transfer function."""

import sympy as sp

from klausurbotpro.application.stability_workflow import (
    StabilityInputDraft,
    StabilityInputMode,
    StabilityMethod,
    run_stability_workflow,
)
from klausurbotpro.domain.parameter_core_contracts import (
    AnalysisTarget,
    CancellationStatus,
    PolynomialRole,
    SolveStatus,
)

_GOLDEN = """
(s^2 + 2*K*s + K^2) /
(((s+3)*(s+2*a)*(s+5)+8*K)*(s+K))
"""


def _draft(
    target: AnalysisTarget = AnalysisTarget.EXTERNAL_BIBO,
    *,
    method: StabilityMethod = StabilityMethod.HURWITZ,
    text: str = _GOLDEN,
) -> StabilityInputDraft:
    return StabilityInputDraft(
        variable_name="s",
        decision_parameters_text="a,K",
        analysis_target=target,
        method=method,
        input_mode=StabilityInputMode.TRANSFER_FUNCTION,
        transfer_function_text=text,
    )


def test_official_golden_case_uses_reduced_denominator_and_exact_region() -> None:
    result = run_stability_workflow(_draft())

    assert result.errors == ()
    assert result.transfer_preparation is not None
    assert result.transfer_preparation.parsed_input is not None
    assert result.transfer_preparation.reduction_result is not None
    assert result.transfer_preparation.reduction_result.report is not None
    assert result.analysis is not None
    canonical = result.analysis.canonical_polynomial
    assert canonical.input.role is PolynomialRole.REDUCED_TRANSFER_DENOMINATOR
    assert canonical.input.analysis_target is AnalysisTarget.EXTERNAL_BIBO
    assert sp.expand(canonical.expanded_polynomial._as_sympy()) == sp.expand(
        sp.sympify("s**3+(8+2*a)*s**2+(15+16*a)*s+30*a+8*K")
    )
    cancellation = canonical.input.cancellation_report
    assert cancellation is not None
    assert cancellation.status is CancellationStatus.FACTORS_REMOVED
    assert tuple(item.canonical_text for item in cancellation.removed_factors) == ("K + s",)
    case = result.analysis.case_results[0]
    assert [[item.canonical_text for item in row] for row in case.matrix] == [
        ["16*a + 15", "1", "0"],
        ["8*K + 30*a", "2*a + 8", "0"],
        ["0", "16*a + 15", "1"],
    ]
    region = case.parameter_region
    assert region.status is SolveStatus.SOLVED_EXACT
    a = sp.Symbol("a")
    assert "-15/16 < a" in region.x_domain
    assert region.lower_bound == "-15*a/4"
    assert sp.expand(sp.sympify(region.upper_bound) - (4 * a**2 + 16 * a + 15)) == 0
    assert "Eingegebene Führungsübertragungsfunktion" in str(result.source_steps)
    assert "K + s" in str(result.source_steps)
    assert "Hurwitz-Matrix nach der Konvention" in result.analysis.latex_source


def test_internal_variant_keeps_raw_quartic_and_reports_full_conditions() -> None:
    result = run_stability_workflow(
        _draft(AnalysisTarget.INTERNAL_CLOSED_LOOP_ASYMPTOTIC)
    )

    assert result.analysis is not None
    canonical = result.analysis.canonical_polynomial
    assert canonical.input.role is PolynomialRole.RAW_CLOSED_LOOP_CHARACTERISTIC
    assert canonical.nominal_degree == 4
    polynomial = canonical.expanded_polynomial._as_sympy()
    assert sp.rem(
        sp.Poly(polynomial, sp.Symbol("s")),
        sp.Poly(sp.Symbol("s") + sp.Symbol("K"), sp.Symbol("s")),
    ).is_zero
    case = result.analysis.case_results[0]
    assert len(case.full_conditions) == 9
    assert case.parameter_region.status is SolveStatus.SOLVED_EXACT
    assert "K > 0" in case.parameter_region.exact_text
    assert "roher Nenner" in str(result.source_steps)
    assert "K + s" in str(result.source_steps)


def test_no_cancellation_and_routh_share_the_selected_canonical_polynomial() -> None:
    text = "(s+1)/(s^3+4*s^2+5*s+K)"
    hurwitz = run_stability_workflow(_draft(text=text))
    routh = run_stability_workflow(_draft(text=text, method=StabilityMethod.ROUTH))

    assert hurwitz.analysis is not None and routh.analysis is not None
    assert (
        hurwitz.analysis.canonical_polynomial.expanded_polynomial
        == routh.analysis.canonical_polynomial.expanded_polynomial
    )
    report = hurwitz.analysis.canonical_polynomial.input.cancellation_report
    assert report is not None
    assert report.status is CancellationStatus.NONE


def test_transfer_function_rejects_non_rational_input_and_state_target() -> None:
    invalid = run_stability_workflow(_draft(text="sin(s)/(s+1)"))
    state = run_stability_workflow(_draft(AnalysisTarget.STATE_ASYMPTOTIC))

    assert invalid.analysis is None
    assert invalid.errors
    assert state.analysis is None
    assert "Zustandsstabilität" in state.errors[0]


def test_more_than_two_decision_parameters_is_rejected_before_preparation() -> None:
    result = run_stability_workflow(
        StabilityInputDraft(
            decision_parameters_text="a,K,T",
            input_mode=StabilityInputMode.TRANSFER_FUNCTION,
            transfer_function_text="1/(s+1)",
        )
    )

    assert result.analysis is None
    assert result.errors == ("Variable oder Entscheidungsparameter sind ungültig.",)
