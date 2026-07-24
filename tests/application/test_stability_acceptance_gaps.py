"""Regressions for the real GUI/PDF acceptance findings on PR #21."""

import re

from klausurbotpro.application.stability_workflow import (
    StabilityInputDraft,
    StabilityInputMode,
    StabilityMethod,
    StabilityWorkflowResult,
    run_stability_workflow,
)
from klausurbotpro.domain.hurwitz_contracts import HurwitzAnalysisResult
from klausurbotpro.domain.parameter_core_contracts import AnalysisTarget, SolveStatus
from klausurbotpro.domain.routh_contracts import RouthAnalysisResult

_TRANSFER = "(s+K)^2 / (((s+3)*(s+2*a)*(s+5)+8*K)*(s+K))"


def _transfer(target: AnalysisTarget) -> StabilityWorkflowResult:
    result = run_stability_workflow(
        StabilityInputDraft(
            decision_parameters_text="a,K",
            input_mode=StabilityInputMode.TRANSFER_FUNCTION,
            transfer_function_text=_TRANSFER,
            analysis_target=target,
        )
    )
    assert isinstance(result.analysis, HurwitzAnalysisResult)
    return result


def test_internal_factor_provenance_closes_exact_region_with_k_positive() -> None:
    internal = _transfer(AnalysisTarget.INTERNAL_CLOSED_LOOP_ASYMPTOTIC)
    external = _transfer(AnalysisTarget.EXTERNAL_BIBO)
    assert isinstance(internal.analysis, HurwitzAnalysisResult)
    assert isinstance(external.analysis, HurwitzAnalysisResult)
    internal_case = internal.analysis.case_results[0]
    external_case = external.analysis.case_results[0]
    user_text = "\n".join(
        (
            internal.analysis.statement,
            str(internal.source_steps),
            internal.latex_preamble,
        )
    )

    assert internal_case.parameter_region.status is SolveStatus.SOLVED_EXACT
    assert "K > 0" in internal.analysis.statement
    assert "teilweise gelöst" not in user_text
    assert "rohe Nenner" in user_text or "roher Nenner" in user_text
    assert "Interne asymptotische Stabilität" in user_text
    assert internal_case.parameter_region.exact_text != external_case.parameter_region.exact_text
    assert "K > 0" not in external.analysis.statement
    assert "Nenner.." not in internal.latex_preamble
    assert (
        "Hurwitz-Kriterium für interne asymptotische Stabilität; "
        "analysiert wird der rohe Nenner."
    ) in internal.latex_preamble


def test_quartic_primary_box_contains_only_remaining_stability_condition() -> None:
    result = run_stability_workflow(
        StabilityInputDraft(
            "T1^3*TI*s^4+3*T1^2*TI*s^3+3*T1*TI*s^2+TI*s+4",
            decision_parameters_text="T1,TI",
            assumptions_text="T1>0; TI>0",
        )
    )
    assert isinstance(result.analysis, HurwitzAnalysisResult)
    latex = result.analysis.latex_source
    final_box = latex[latex.rindex(r"\boxed") :]

    assert r"\boxed{T_{I} > \frac{9}{2}\,T_{1}}" in final_box
    assert "T_{1} < \\infty" not in final_box
    assert ",," not in final_box
    assert r"\Delta_{2}" in latex and r"T_{I} > 4\,T_{1}" in latex
    assert r"\Delta_{3}" in latex and r"T_{I} > \frac{9}{2}\,T_{1}" in latex
    assert r"\Delta_{4}" in latex
    assert latex.count(r"\boxed") == 1
    assert "TI > 9*T1/2" not in latex
    assert (
        r"\text{Aktiv: }T_{I} > \frac{9}{2}\,T_{1}"
        r"\\\Delta_{2}\text{ ist gegenüber }\Delta_{3}\text{ redundant.}"
    ) in latex


def test_parameter_free_hurwitz_hides_cas_truth_word() -> None:
    result = run_stability_workflow(StabilityInputDraft("s^3+4*s^2+5*s+8"))
    assert isinstance(result.analysis, HurwitzAnalysisResult)
    visible = result.analysis.statement + "\n" + result.analysis.latex_source

    assert "wahr" not in visible
    assert "Keine zusätzlichen Parameterbedingungen." in visible
    assert "intern asymptotisch stabil" in visible
    result_start = result.analysis.latex_source.index(r"\begin{samepage}")
    intro_start = result.analysis.latex_source.index(r"\textbf{Ergebnis.}")
    box_start = result.analysis.latex_source.index(r"\boxed{\text{intern asymptotisch stabil}}")
    result_end = result.analysis.latex_source.index(r"\end{samepage}")
    assert result_start < intro_start < box_start < result_end


def test_hurwitz_prose_and_reduced_summaries_use_real_latex_math() -> None:
    result = run_stability_workflow(
        StabilityInputDraft(
            "s^3+(9+a)*s^2+(20+9*a)*s+(20*a+9*K)",
            decision_parameters_text="a,K",
        )
    )
    assert isinstance(result.analysis, HurwitzAnalysisResult)
    latex = result.analysis.latex_source

    assert r"Für alle Koeffizienten gilt \(a_i>0\)." in latex
    assert r"Für alle Determinanten gilt \(\Delta_i>0\)." in latex
    assert r"\textbackslash{}(" not in latex
    assert (
        r"a_{2}\text{ ist gegenüber }a_{1}\text{ redundant.}"
    ) in latex
    assert (
        r"\Delta_{3}\text{ ist gegenüber }\Delta_{2}\text{ redundant.}"
    ) in latex
    assert "Delta_2 gegenüber Delta_3" not in latex
    assert "a_2 gegenüber a_1" not in latex
    assert r"\begin{samepage}" not in latex


def test_single_parameter_hurwitz_summary_uses_subscripted_parameter() -> None:
    result = run_stability_workflow(
        StabilityInputDraft(
            "s^3+4*s^2+5*s+K_P",
            decision_parameters_text="K_P",
        )
    )
    assert isinstance(result.analysis, HurwitzAnalysisResult)
    latex = result.analysis.latex_source

    assert r"\text{Aktiv: }K_{P} > 0" in latex
    assert r"\text{Aktiv: }K_{P} < 20" in latex
    assert "K_P < 20" not in latex


def test_routh_main_latex_is_compact_table_without_internal_cell_indices() -> None:
    result = run_stability_workflow(
        StabilityInputDraft(
            "s^3+4*s^2+5*s+K_P",
            decision_parameters_text="K_P",
            method=StabilityMethod.ROUTH,
        )
    )
    assert isinstance(result.analysis, RouthAnalysisResult)
    latex = result.analysis.latex_source

    assert r"\begin{array}{c|cc}" in latex
    assert all(rf"s^{{{power}}}" in latex for power in (3, 2, 1, 0))
    assert r"\dfrac{4\cdot 5-1\cdot K_{P}}{4}" in latex
    assert not re.search(r"r_\{\d+,\d+\}", latex)
    assert "Hurwitz-Skriptkonvention" not in latex
    assert r"\boxed{0 < K_{P} < 20}" in latex
    assert latex.count(r"\boxed") == 1


def test_hurwitz_reference_regions_remain_exact() -> None:
    ref_01 = run_stability_workflow(
        StabilityInputDraft(
            "s^3+(9+a)*s^2+(20+9*a)*s+(20*a+9*K)",
            decision_parameters_text="a,K",
        )
    )
    ref_02 = _transfer(AnalysisTarget.EXTERNAL_BIBO)
    assert isinstance(ref_01.analysis, HurwitzAnalysisResult)
    assert isinstance(ref_02.analysis, HurwitzAnalysisResult)

    first = ref_01.analysis.case_results[0].parameter_region
    second = ref_02.analysis.case_results[0].parameter_region
    assert first.lower_bound == "-20*a/9"
    assert first.upper_bound == "(a + 4)*(a + 5)"
    assert second.lower_bound == "-15*a/4"
    assert second.upper_bound == "(2*a + 3)*(2*a + 5)"


def test_internal_transfer_region_remains_complete_in_latex_box() -> None:
    internal = _transfer(AnalysisTarget.INTERNAL_CLOSED_LOOP_ASYMPTOTIC)
    assert isinstance(internal.analysis, HurwitzAnalysisResult)
    latex = internal.analysis.latex_source
    final_box = latex[latex.rindex(r"\boxed") :]

    assert r"a &> - \frac{15}{16}" in final_box
    assert r"K &> - \frac{15 a}{4}" in final_box
    assert r"0 &< K < \left(2 a + 3\right) \left(2 a + 5\right)" in final_box
    assert latex.count(r"\boxed") == 1
