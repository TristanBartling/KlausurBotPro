"""Regressions for the real GUI/PDF acceptance findings on PR #21."""

import re

from klausurbotpro.application.stability_workflow import (
    StabilityInputDraft,
    StabilityInputMode,
    StabilityMethod,
    run_stability_workflow,
)
from klausurbotpro.domain.hurwitz_contracts import HurwitzAnalysisResult
from klausurbotpro.domain.parameter_core_contracts import AnalysisTarget, SolveStatus
from klausurbotpro.domain.routh_contracts import RouthAnalysisResult

_TRANSFER = "(s+K)^2 / (((s+3)*(s+2*a)*(s+5)+8*K)*(s+K))"


def _transfer(target: AnalysisTarget):
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

    assert r"\boxed{TI > \frac{9}{2}\,T_{1}}" in final_box
    assert "T_{1} < \\infty" not in final_box
    assert ",," not in final_box
    assert r"\Delta_{2}" in latex and r"TI > 4\,T_{1}" in latex
    assert r"\Delta_{3}" in latex and r"TI > \frac{9}{2}\,T_{1}" in latex
    assert r"\Delta_{4}" in latex
    assert latex.count(r"\boxed") == 1


def test_parameter_free_hurwitz_hides_cas_truth_word() -> None:
    result = run_stability_workflow(StabilityInputDraft("s^3+4*s^2+5*s+8"))
    assert isinstance(result.analysis, HurwitzAnalysisResult)
    visible = result.analysis.statement + "\n" + result.analysis.latex_source

    assert "wahr" not in visible
    assert "Keine zusätzlichen Parameterbedingungen." in visible
    assert "intern asymptotisch stabil" in visible


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

    first = ref_01.analysis.case_results[0].parameter_region
    second = ref_02.analysis.case_results[0].parameter_region
    assert first.lower_bound == "-20*a/9"
    assert first.upper_bound == "(a + 4)*(a + 5)"
    assert second.lower_bound == "-15*a/4"
    assert second.upper_bound == "(2*a + 3)*(2*a + 5)"
