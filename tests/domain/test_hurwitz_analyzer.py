"""Focused official and contract reference tests for Hurwitz."""

import re

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
    case = analysis.case_results[0]
    assert "K_P < 20" in case.parameter_region.exact_text
    assert [[item.canonical_text for item in row] for row in case.matrix] == [
        ["5", "1", "0"],
        ["K_P", "4", "0"],
        ["0", "5", "1"],
    ]
    assert [item.expression.canonical_text for item in case.solver_conditions] == [
        "1",
        "1",
        "K_P",
        "-K_P + 20",
    ]
    assert r"\boxed{0 < K_{P} < 20}" in analysis.latex_source
    assert r"\textbf{Numerische Kontrolle.}" in analysis.latex_source
    assert r"\(K_{P}=10\)" in analysis.latex_source
    assert r"s_{1} &\approx" in analysis.latex_source
    assert "consistent" not in analysis.latex_source
    final_box = analysis.latex_source.rsplit(r"\boxed", maxsplit=1)[-1]
    assert " & " not in final_box
    assert re.search(r"\\text\{[^}]*K_P", final_box) is None


def test_even_power_coefficient_keeps_zero_excluded() -> None:
    analysis = _analysis(
        StabilityInputDraft(
            "s^2+K^2*s+1",
            decision_parameters_text="K",
        )
    )
    region = analysis.case_results[0].parameter_region
    assert region.status is SolveStatus.SOLVED_EXACT
    assert "Ne(K, 0)" in region.exact_text
    assert not bool(sp.sympify(region.exact_text).subs(sp.Symbol("K"), 0))


def test_direct_polynomial_cannot_claim_state_stability() -> None:
    result = run_stability_workflow(
        StabilityInputDraft(
            "s^2+2*s+1",
            analysis_target=AnalysisTarget.STATE_ASYMPTOTIC,
        )
    )
    assert result.analysis is not None
    assert result.analysis.canonical_polynomial.status is SolveStatus.INVALID_INPUT
    assert not result.analysis.case_results
    assert result.analysis.statement == "Analyse ungültig."


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


def test_degree_drop_combined_region_remains_closed_at_zero() -> None:
    analysis = _analysis(
        StabilityInputDraft(
            "q*s^3+s^2+2*s+1",
            decision_parameters_text="q",
            assumptions_text="q>=0",
        )
    )
    assert analysis.combined_region == "(0 <= q) & (q < 2)"
    assert tuple(item.degree_case.degree for item in analysis.case_results) == (3, 2)


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
