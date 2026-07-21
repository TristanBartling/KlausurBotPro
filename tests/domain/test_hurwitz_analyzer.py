"""Focused official and contract reference tests for Hurwitz."""

import sympy as sp

from klausurbotpro.application.stability_workflow import (
    AnalysisTarget,
    PolynomialRole,
    StabilityInputDraft,
    run_stability_workflow,
)
from klausurbotpro.domain.hurwitz_contracts import HurwitzAnalysisResult, NumericalCheckStatus
from klausurbotpro.domain.parameter_core_contracts import SolveStatus


def _analysis(draft: StabilityInputDraft) -> HurwitzAnalysisResult:
    result = run_stability_workflow(draft)
    assert not result.errors
    assert result.analysis is not None
    return result.analysis


def test_parameter_free_stable_and_unstable_decisions() -> None:
    stable = _analysis(StabilityInputDraft("s^3+4*s^2+5*s+8"))
    unstable = _analysis(StabilityInputDraft("s^2+0*s+3"))
    assert stable.case_results[0].parameter_region.status is SolveStatus.SOLVED_EXACT
    assert stable.case_results[0].numerical_check is not None
    assert stable.case_results[0].numerical_check.status is NumericalCheckStatus.CONSISTENT
    assert unstable.case_results[0].parameter_region.status is SolveStatus.EMPTY


def test_exercise_09_has_strict_open_interval() -> None:
    analysis = _analysis(
        StabilityInputDraft(
            "s^3+4*s^2+5*s+K_P",
            decision_parameters_text="K_P",
        )
    )
    assert analysis.combined_region == "(0 < K_P) & (K_P < 20)"
    assert "K_P < 20" in analysis.case_results[0].parameter_region.exact_text


def test_ss2025_exact_two_parameter_region() -> None:
    analysis = _analysis(
        StabilityInputDraft(
            "s^3+(9+a)*s^2+(20+9*a)*s+(20*a+9*K)",
            decision_parameters_text="a,K",
        )
    )
    region = analysis.case_results[0].parameter_region
    a = sp.Symbol("a")
    assert region.status is SolveStatus.SOLVED_EXACT
    assert sp.simplify(sp.sympify(region.lower_bound) + sp.Rational(20, 9) * a) == 0
    assert sp.simplify(sp.sympify(region.upper_bound) - (a**2 + 9 * a + 20)) == 0


def test_quartic_tutorial_and_ws_reduced_role_contract() -> None:
    quartic = _analysis(
        StabilityInputDraft(
            "T1^3*TI*s^4+3*T1^2*TI*s^3+3*T1*TI*s^2+TI*s+4",
            decision_parameters_text="T1,TI",
            assumptions_text="T1>0; TI>0",
        )
    )
    assert quartic.case_results[0].parameter_region.lower_bound == "9*T1/2"
    assert (
        sp.simplify(
            quartic.case_results[0].determinants[3].expression._as_sympy()
            - (
                quartic.case_results[0].degree_case.coefficients[0]._as_sympy()
                * quartic.case_results[0].determinants[2].expression._as_sympy()
            )
        )
        == 0
    )

    reduced = _analysis(
        StabilityInputDraft(
            "s^3+(8+2*a)*s^2+(15+16*a)*s+(30*a+8*K)",
            decision_parameters_text="a,K",
            role=PolynomialRole.REDUCED_TRANSFER_DENOMINATOR,
            analysis_target=AnalysisTarget.EXTERNAL_BIBO,
            cancellation_note="Gemeinsamer Faktor s+K wurde entfernt.",
        )
    )
    region = reduced.case_results[0].parameter_region
    assert "keine interne Stabilität" in reduced.cancellation_notice
    assert region.lower_bound == "-15*a/4"
    assert (
        sp.expand(sp.sympify(region.upper_bound))
        == 4 * sp.Symbol("a") ** 2 + 16 * sp.Symbol("a") + 15
    )
