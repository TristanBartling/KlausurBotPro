"""Exam-facing regressions for explicit Hurwitz condition derivations."""

import sympy as sp

from klausurbotpro.application.stability_workflow import (
    StabilityInputDraft,
    StabilityInputMode,
    run_stability_workflow,
)
from klausurbotpro.domain.hurwitz_contracts import (
    HurwitzAnalysisResult,
    HurwitzConditionStatus,
)
from klausurbotpro.domain.parameter_core_contracts import AnalysisTarget, SolveStatus


def _analysis(draft: StabilityInputDraft) -> HurwitzAnalysisResult:
    result = run_stability_workflow(draft)
    assert result.errors == ()
    assert isinstance(result.analysis, HurwitzAnalysisResult)
    return result.analysis


def test_ref_hur_01_has_typed_necessary_and_sufficient_derivation() -> None:
    analysis = _analysis(
        StabilityInputDraft(
            "s^3+(9+a)*s^2+(20+9*a)*s+(20*a+9*K)",
            decision_parameters_text="a,K",
        )
    )
    case = analysis.case_results[0]

    assert tuple(item.label for item in case.necessary_condition_steps) == (
        "a_3",
        "a_2",
        "a_1",
        "a_0",
    )
    assert case.necessary_condition_steps[0].status is HurwitzConditionStatus.ALREADY_SATISFIED
    assert case.necessary_condition_steps[1].solved_text == "a > -9"
    assert case.necessary_condition_steps[1].status is HurwitzConditionStatus.REDUNDANT_WEAKER
    assert case.necessary_condition_steps[1].reference_label == "a_1"
    assert case.necessary_condition_steps[2].solved_text == "a > -20/9"
    assert case.necessary_condition_steps[3].solved_text == "K > -20*a/9"

    assert tuple(item.label for item in case.sufficient_condition_steps) == (
        "Delta_1",
        "Delta_2",
        "Delta_3",
    )
    assert case.sufficient_condition_steps[0].status is HurwitzConditionStatus.REDUNDANT_EQUIVALENT
    assert case.sufficient_condition_steps[0].reference_label == "a_1"
    assert case.sufficient_condition_steps[1].solved_text == "K < (a+4)*(a+5)"
    assert case.sufficient_condition_steps[2].status is HurwitzConditionStatus.REDUNDANT_EQUIVALENT
    assert case.sufficient_condition_steps[2].reference_label == "Delta_2"
    assert case.parameter_region.status is SolveStatus.SOLVED_EXACT
    assert case.parameter_region.lower_bound == "-20*a/9"
    assert case.parameter_region.upper_bound == "(a + 4)*(a + 5)"


def test_ref_hur_02_uses_course_notation_and_distinguishes_external_internal() -> None:
    text = "(s+K)^2 / (((s+3)*(s+2*a)*(s+5)+8*K)*(s+K))"
    external_result = run_stability_workflow(
        StabilityInputDraft(
            decision_parameters_text="a,K",
            input_mode=StabilityInputMode.TRANSFER_FUNCTION,
            transfer_function_text=text,
            analysis_target=AnalysisTarget.EXTERNAL_BIBO,
        )
    )
    internal_result = run_stability_workflow(
        StabilityInputDraft(
            decision_parameters_text="a,K",
            input_mode=StabilityInputMode.TRANSFER_FUNCTION,
            transfer_function_text=text,
            analysis_target=AnalysisTarget.INTERNAL_CLOSED_LOOP_ASYMPTOTIC,
        )
    )
    assert isinstance(external_result.analysis, HurwitzAnalysisResult)
    assert isinstance(internal_result.analysis, HurwitzAnalysisResult)
    external = external_result.analysis
    internal = internal_result.analysis
    source_text = "\n".join(value for _title, value in external_result.source_steps)

    assert "Z_roh(s)" in source_text
    assert "N_roh(s)" in source_text
    assert "Z_red(s)=K + s" in source_text
    assert "N_red(s)=" in source_text
    assert external.canonical_polynomial.nominal_degree == 3
    assert internal.canonical_polynomial.nominal_degree == 4
    external_region = external.case_results[0].parameter_region
    assert external_region.lower_bound == "-15*a/4"
    assert sp.expand(sp.sympify(external_region.upper_bound)) == (
        4 * sp.Symbol("a") ** 2 + 16 * sp.Symbol("a") + 15
    )
    assert internal.case_results[0].parameter_region.exact_text != external_region.exact_text


def test_single_parameter_quartic_and_parameter_free_regressions() -> None:
    single = _analysis(
        StabilityInputDraft(
            "s^3+4*s^2+5*s+K_P",
            decision_parameters_text="K_P",
        )
    )
    single_case = single.case_results[0]
    assert single.combined_region == "(0 < K_P) & (K_P < 20)"
    assert any(
        item.solved_text == "K_P > 0"
        for item in single_case.necessary_condition_steps
    )
    assert any(
        item.solved_text == "K_P < 20"
        for item in single_case.sufficient_condition_steps
    )

    quartic = _analysis(
        StabilityInputDraft(
            "T1^3*TI*s^4+3*T1^2*TI*s^3+3*T1*TI*s^2+TI*s+4",
            decision_parameters_text="T1,TI",
            assumptions_text="T1>0; TI>0",
        )
    )
    quartic_steps = quartic.case_results[0].sufficient_condition_steps
    assert quartic_steps[1].solved_expression.canonical_text == "-4*T1 + TI"
    assert quartic_steps[1].status is HurwitzConditionStatus.REDUNDANT_WEAKER
    assert quartic_steps[1].reference_label == "Delta_3"
    assert quartic_steps[2].solved_expression.canonical_text == "-9*T1 + 2*TI"
    assert quartic.case_results[0].parameter_region.lower_bound == "9*T1/2"

    parameter_free = _analysis(StabilityInputDraft("s^3+4*s^2+5*s+8"))
    all_steps = (
        *parameter_free.case_results[0].necessary_condition_steps,
        *parameter_free.case_results[0].sufficient_condition_steps,
    )
    assert all(
        item.status
        in (
            HurwitzConditionStatus.ALREADY_SATISFIED,
            HurwitzConditionStatus.REDUNDANT_EQUIVALENT,
        )
        for item in all_steps
    )
    assert parameter_free.case_results[0].parameter_region.exact_text == "wahr"
    assert "stabil" in parameter_free.statement.lower()


def test_worked_steps_and_latex_follow_exam_order_without_internal_names() -> None:
    analysis = _analysis(
        StabilityInputDraft(
            "s^3+(9+a)*s^2+(20+9*a)*s+(20*a+9*K)",
            decision_parameters_text="a,K",
        )
    )
    titles = tuple(title for title, _value in analysis.worked_steps)
    required = (
        "Gegeben",
        "Gesucht",
        "Methode und Stabilitätsbegriff",
        "Voraussetzungen und Annahmen",
        "Charakteristisches Polynom",
        "Kursnotation",
        "Notwendige Bedingungen",
        "Hurwitz-Matrix",
        "Hinreichende Bedingungen",
        "Verbleibendes minimales Bedingungssystem",
        "Schnittmenge",
        "Exaktes Stabilitätsgebiet",
        "Numerische Gegenkontrolle",
        "Endaussage",
    )
    positions = tuple(titles.index(title) for title in required)
    assert positions == tuple(sorted(positions))

    latex = analysis.latex_source
    headings = (
        r"\textbf{Gegeben.}",
        r"\textbf{Gesucht.}",
        r"\textbf{Methode.}",
        r"\textbf{Voraussetzungen.}",
        r"\textbf{Charakteristisches Polynom.}",
        r"\textbf{Koeffizienten.}",
        r"\textbf{Notwendige Bedingungen.}",
        r"\textbf{Reduzierte notwendige Bedingungen.}",
        r"\textbf{Hurwitz-Matrix.}",
        r"\textbf{Hinreichende Bedingungen.}",
        r"\textbf{Reduzierte hinreichende Bedingungen.}",
        r"\textbf{Schnittmenge.}",
        r"\textbf{Numerische Kontrolle.}",
        r"\textbf{Ergebnis.}",
    )
    heading_positions = tuple(latex.index(heading) for heading in headings)
    assert heading_positions == tuple(sorted(heading_positions))
    assert latex.count(r"\boxed") == 1
    assert "solver_conditions" not in latex
    assert "full_conditions" not in latex
    assert "REDUNDANT_" not in latex
