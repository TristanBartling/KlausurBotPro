"""Focused Routh MVP reference and integration tests."""

import re

import sympy as sp

from klausurbotpro.application.stability_workflow import (
    AnalysisTarget,
    PolynomialRole,
    StabilityInputDraft,
    StabilityMethod,
    run_stability_workflow,
)
from klausurbotpro.domain.hurwitz_contracts import HurwitzAnalysisResult
from klausurbotpro.domain.parameter_core_contracts import ConditionOrigin
from klausurbotpro.domain.routh_contracts import RouthAnalysisResult, RouthSpecialCase


def _routh(
    polynomial: str,
    parameters: str = "",
    *,
    assumptions_text: str = "",
    role: PolynomialRole = PolynomialRole.DIRECT_CHARACTERISTIC_POLYNOMIAL,
    analysis_target: AnalysisTarget = AnalysisTarget.INTERNAL_CLOSED_LOOP_ASYMPTOTIC,
    cancellation_note: str = "",
) -> RouthAnalysisResult:
    result = run_stability_workflow(
        StabilityInputDraft(
            polynomial,
            decision_parameters_text=parameters,
            method=StabilityMethod.ROUTH,
            assumptions_text=assumptions_text,
            role=role,
            analysis_target=analysis_target,
            cancellation_note=cancellation_note,
        )
    )
    assert not result.errors
    assert isinstance(result.analysis, RouthAnalysisResult)
    return result.analysis


def _values(analysis: RouthAnalysisResult) -> list[list[sp.Expr]]:
    return [[entry._as_sympy() for entry in row.entries] for row in analysis.case_results[0].rows]


def test_r1_exact_table_open_region_and_cell_derivation() -> None:
    analysis = _routh("s^3+4*s^2+5*s+K_P", "K_P")
    k_p = sp.Symbol("K_P")
    expected = [[1, 5], [4, k_p], [(20 - k_p) / 4, 0], [k_p, 0]]
    assert all(
        sp.simplify(actual - wanted) == 0
        for actual_row, expected_row in zip(_values(analysis), expected, strict=True)
        for actual, wanted in zip(actual_row, expected_row, strict=True)
    )
    assert analysis.combined_region == "(0 < K_P) & (K_P < 20)"
    assert "4*5" in analysis.case_results[0].rows[2].cells[0].derivation
    assert "K_P" in analysis.case_results[0].rows[2].cells[0].derivation
    assert r"\boxed{0 < K_{P} \wedge K_{P} < 20}" in analysis.latex_source
    final_box = analysis.latex_source.rsplit(r"\boxed", maxsplit=1)[-1]
    assert " & " not in final_box
    assert re.search(r"\\text\{[^}]*K_P", final_box) is None


def test_r2_r3_sign_changes_and_numeric_cross_check() -> None:
    stable_analysis = _routh("s^3+4*s^2+5*s+2")
    unstable_analysis = _routh("s^3+2*s^2-s+2")
    stable = stable_analysis.case_results[0]
    unstable = unstable_analysis.case_results[0]
    assert stable.first_column == tuple(row.first_column for row in stable.rows)
    assert stable.sign_sequence == ("+", "+", "+", "+")
    assert stable.sign_changes == stable.numerical_rhp_roots == 0
    assert unstable.sign_sequence == ("+", "+", "-", "+")
    assert unstable.sign_changes == unstable.numerical_rhp_roots == 2
    assert "stabil; 0 Nullstellen in der rechten Halbebene" in stable_analysis.statement
    assert "Nicht intern asymptotisch stabil" in unstable_analysis.statement
    assert "2 Nullstellen in der rechten Halbebene" in unstable_analysis.statement
    assert "genau für ∅" not in unstable_analysis.statement


def test_degree_two_four_and_missing_power_rows() -> None:
    quadratic = _routh("s^2+3*s+2")
    quartic = _routh("s^4+4*s^3+6*s^2+4*s+1")
    missing = _routh("s^3+2*s+1")
    assert _values(quadratic) == [[1, 2], [3, 0], [2, 0]]
    assert _values(quartic) == [
        [1, 6, 1],
        [4, 4, 0],
        [5, 1, 0],
        [sp.Rational(16, 5), 0, 0],
        [1, 0, 0],
    ]
    assert _values(missing)[:2] == [[1, 2], [0, 1]]


def test_safe_special_case_detection() -> None:
    zero_first_analysis = _routh("s^3+2*s+1")
    zero_row_analysis = _routh("s^3+2*s^2+s+2")
    zero_first = zero_first_analysis.case_results[0]
    zero_row = zero_row_analysis.case_results[0]
    assert zero_first.special_case is RouthSpecialCase.ZERO_FIRST_COLUMN
    assert "ε-Verfahren" in zero_first.statement
    assert zero_row.special_case is RouthSpecialCase.COMPLETE_ZERO_ROW
    assert "Hilfspolynomverfahren" in zero_row.statement
    assert zero_first_analysis.latex_source == ""
    assert zero_row_analysis.latex_source == ""


def test_worked_steps_show_parameters_assumptions_and_exclusions_readably() -> None:
    analysis = _routh(
        "s^3+4*s^2+5*s+K_P",
        "K_P",
        assumptions_text="K_P>0",
    )

    assert analysis.worked_steps[2] == (
        "3. Entscheidungsparameter und Annahmen",
        "Parameter: K_P; Annahmen: K_P > 0; Ausschlüsse: keine",
    )


def test_degree_cases_and_reduced_denominator_semantics_are_reused() -> None:
    degree_drop = _routh("q*s^3+s^2+2*s+1", "q")
    assert tuple(item.degree_case.degree for item in degree_drop.case_results) == (3, 3, 2)
    reduced = _routh(
        "s^3+(8+2*a)*s^2+(15+16*a)*s+(30*a+8*K)",
        "a,K",
        role=PolynomialRole.REDUCED_TRANSFER_DENOMINATOR,
        analysis_target=AnalysisTarget.EXTERNAL_BIBO,
        cancellation_note="Gemeinsamer Faktor s+K wurde entfernt.",
    )
    assert "keine interne Stabilität" in reduced.cancellation_notice
    assert "BIBO" in reduced.stability_concept
    assert reduced.case_results[0].parameter_region.lower_bound == "-15*a/4"


def test_symbolic_routh_denominator_remains_explicitly_excluded() -> None:
    analysis = _routh("s^3+K*s^2+5*s+1", "K")
    exclusions = tuple(
        condition
        for condition in analysis.case_results[0].full_conditions
        if condition.origin is ConditionOrigin.ROUTH_DENOMINATOR_EXCLUSION
    )
    assert exclusions
    assert any(condition.expression.canonical_text == "K" for condition in exclusions)


def test_hurwitz_cross_checks_one_parameter_and_quartic() -> None:
    for polynomial, parameters in (
        ("s^3+4*s^2+5*s+K_P", "K_P"),
        ("s^3+4*s^2+5*s+2", ""),
        ("s^4+4*s^3+6*s^2+4*s+1", ""),
    ):
        hurwitz_result = run_stability_workflow(
            StabilityInputDraft(polynomial, decision_parameters_text=parameters)
        )
        routh = _routh(polynomial, parameters)
        assert isinstance(hurwitz_result.analysis, HurwitzAnalysisResult)
        assert hurwitz_result.analysis.combined_region == routh.combined_region


def test_existing_two_parameter_graph_band_matches_hurwitz() -> None:
    polynomial = "s^3+(9+a)*s^2+(20+9*a)*s+(20*a+9*K)"
    hurwitz_result = run_stability_workflow(
        StabilityInputDraft(polynomial, decision_parameters_text="a,K")
    )
    routh = _routh(polynomial, "a,K")
    assert isinstance(hurwitz_result.analysis, HurwitzAnalysisResult)
    hurwitz_region = hurwitz_result.analysis.case_results[0].parameter_region
    routh_region = routh.case_results[0].parameter_region
    assert routh_region.x_domain == hurwitz_region.x_domain
    assert (
        sp.simplify(sp.sympify(routh_region.lower_bound) - sp.sympify(hurwitz_region.lower_bound))
        == 0
    )
    assert (
        sp.simplify(sp.sympify(routh_region.upper_bound) - sp.sympify(hurwitz_region.upper_bound))
        == 0
    )
