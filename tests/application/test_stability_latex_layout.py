"""Structural regressions for the page-safe stability LaTeX renderer."""

import re

from klausurbotpro.application.stability_workflow import (
    StabilityInputDraft,
    StabilityInputMode,
    StabilityMethod,
    format_stability_region,
    run_stability_workflow,
)
from klausurbotpro.domain.parameter_core_contracts import AnalysisTarget

_GOLDEN = """
(s^2 + 2*K*s + K^2) /
(((s+3)*(s+2*a)*(s+5)+8*K)*(s+K))
"""


def _transfer(
    target: AnalysisTarget = AnalysisTarget.EXTERNAL_BIBO,
    method: StabilityMethod = StabilityMethod.HURWITZ,
    text: str = _GOLDEN,
):
    result = run_stability_workflow(
        StabilityInputDraft(
            decision_parameters_text="a,K",
            analysis_target=target,
            input_mode=StabilityInputMode.TRANSFER_FUNCTION,
            transfer_function_text=text,
            method=method,
        )
    )
    assert result.analysis is not None
    return result


def _assert_balanced(latex: str) -> None:
    assert latex.count(r"\[") == latex.count(r"\]")
    assert latex.count(r"\begin{aligned}") == latex.count(r"\end{aligned}")
    assert "None" not in latex
    assert "ROUTH_NUMERIC_POLE_MISMATCH" not in latex
    visual_segments = latex.replace(r"\\", "\n").splitlines()
    assert max(map(len, visual_segments), default=0) <= 120


def test_golden_plain_and_latex_hide_infinity_and_wrap_all_major_sections() -> None:
    result = _transfer()
    analysis = result.analysis
    assert analysis is not None
    region = format_stability_region(
        analysis.case_results[0].parameter_region,
        analysis.canonical_polynomial.input.decision_parameters,
    )

    assert region == "a > -15/16 und -15*a/4 < K < (2*a+3)*(2*a+5)"
    assert "&" not in analysis.statement
    assert "oo" not in analysis.statement
    latex = result.latex_preamble
    assert r"\infty" not in latex
    assert "a < oo" not in latex
    assert latex.count("Der reduzierte E/A-Nenner beweist keine interne") == 1
    assert r"\textbf{Warnung.}" in latex
    assert r"\[\textbf{Warnung" not in latex
    assert r"a &> - \frac{15}{16}" in latex
    assert r"- \frac{15 a}{4} &< K <" in latex
    assert r"\(a=\frac{1}{16}\)" in latex
    assert r"\(K=\frac{505}{64}\)" in latex
    assert latex.count(r"s_{1} &\approx") == 1
    assert r"\mathrm{i}" in latex
    assert re.search(r"\d(?:\.\d+)?j", latex) is None
    assert "Zähler und Nenner werden zur besseren Lesbarkeit" in latex
    assert "N(s)" in latex and "D(s)" in latex
    assert r"\begin{aligned}p(s)=" in latex
    assert r"\textbf{Bedingungssystem.}" in latex
    _assert_balanced(latex)


def test_long_quartic_direct_polynomial_and_internal_conditions_are_multiline() -> None:
    direct = run_stability_workflow(
        StabilityInputDraft(
            "((s+3)*(s+2*a)*(s+5)+8*K)*(s+K)",
            decision_parameters_text="a,K",
        )
    )
    internal = _transfer(AnalysisTarget.INTERNAL_CLOSED_LOOP_ASYMPTOTIC)
    assert direct.analysis is not None

    latex = direct.analysis.latex_source
    assert r"\begin{aligned}p(s)={}&s^{4}" in latex
    assert latex.count(r"\\&\quad{}") >= 2
    assert "30 K a" in latex
    assert "8 K^{2}" in latex
    assert r"\begin{aligned}" in internal.latex_preamble
    assert internal.analysis is not None
    assert "teilweise gelöst" in internal.analysis.statement
    _assert_balanced(latex)
    _assert_balanced(internal.latex_preamble)


def test_parameter_free_case_has_no_artificial_control_point() -> None:
    result = run_stability_workflow(StabilityInputDraft("s^3+4*s^2+5*s+8"))
    assert result.analysis is not None
    latex = result.analysis.latex_source

    assert "Für den Kontrollpunkt" not in latex
    assert r"\mathrm{i}" in latex
    _assert_balanced(latex)


def test_uncancelled_transfer_has_no_warning_and_routh_uses_real_fractions() -> None:
    no_cancel = _transfer(text="(s+1)/(s^3+(8+2*a)*s^2+(15+16*a)*s+30*a+8*K)")
    routh = _transfer(method=StabilityMethod.ROUTH)

    assert r"\textbf{Warnung.}" not in no_cancel.latex_preamble
    assert r"\frac{" in routh.latex_preamble
    assert " / " not in routh.analysis.latex_source
    assert r"\textbf{Stabilitätsbedingungen.}" in routh.latex_preamble
    _assert_balanced(no_cancel.latex_preamble)
    _assert_balanced(routh.latex_preamble)


def test_short_single_parameter_result_stays_on_one_boxed_line() -> None:
    result = run_stability_workflow(
        StabilityInputDraft(
            "s^3+4*s^2+5*s+K_P",
            decision_parameters_text="K_P",
        )
    )
    assert result.analysis is not None

    assert result.analysis.statement.endswith("0 < K_P < 20.")
    assert r"\boxed{0 < K_{P} < 20}" in result.analysis.latex_source
