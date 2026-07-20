"""LaTeX solutions projected only from validated frequency results."""

import re
from pathlib import Path

from klausurbotpro.application import (
    FrequencyDomainInputDraft,
    FrequencyDomainRequestFactory,
    FrequencyDomainSingularityRefinementPlanner,
    FrequencyDomainWorkflowLimits,
    FrequencyDomainWorkflowMode,
    FrequencyDomainWorkflowResult,
    FrequencyDomainWorkflowService,
    FrequencyPhasePresentation,
    ParameterInputDraft,
    TransferFunctionInputDraft,
    WorkflowInputForm,
    render_frequency_domain_solution_latex,
)
from klausurbotpro.application._solution_report_formatting import (
    compact_decimal_text,
)
from klausurbotpro.domain import FrequencyResponsePointStatus


def _result(
    expression: str,
    mode: FrequencyDomainWorkflowMode,
    *,
    single: str = "1",
    omega_min: str = "1/10",
    omega_max: str = "10",
    points: str = "4",
    explicit: str = "",
    unwrap: bool = False,
    parameters: tuple[ParameterInputDraft, ...] = (),
) -> tuple[FrequencyDomainWorkflowResult, FrequencyDomainWorkflowLimits]:
    limits = FrequencyDomainWorkflowLimits()
    draft = FrequencyDomainInputDraft(
        TransferFunctionInputDraft(
            WorkflowInputForm.COMMON,
            expression,
            "",
            "",
            "s",
            parameters,
            "frequency",
        ),
        mode,
        single,
        omega_min,
        omega_max,
        points,
        explicit,
        (
            FrequencyPhasePresentation.PRINCIPAL_AND_UNWRAPPED
            if unwrap
            else FrequencyPhasePresentation.PRINCIPAL_ONLY
        ),
    )
    creation = FrequencyDomainRequestFactory(limits).create(draft)
    assert creation.request is not None
    return FrequencyDomainWorkflowService(limits).run(creation.request), limits


def test_single_point_pt1_is_copyable_compact_and_uses_engineering_j() -> None:
    result, limits = _result(
        "1/(s+1)",
        FrequencyDomainWorkflowMode.SINGLE_POINT,
    )

    latex = render_frequency_domain_solution_latex(result, limits)

    assert r"\section*{Gegeben}" in latex
    assert r"G_{\mathrm{Eingabe}}(s)=\frac{1}{s + 1}" in latex
    assert r"G(\mathrm{j})=\frac{1}{1 + \mathrm{j}}" in latex
    assert (
        r"G(\mathrm{j})=\frac{1}{2} - \frac{\mathrm{j}}{2}"
        in latex
    )
    assert r"\operatorname{Re}\{G(\mathrm{j})\}=\frac{1}{2}" in latex
    assert r"|G(\mathrm{j})|^2=\frac{1}{2}" in latex
    assert r"|G(\mathrm{j})|\approx 0.707107" in latex
    assert r"L(1)=20\log_{10}|G(\mathrm{j})|\approx -3.0103" in latex
    assert r"\varphi(1)\approx -45^\circ" in latex
    assert r"\varphi(1)=-45^\circ" not in latex
    assert r"\boxed{" in latex
    assert re.search(r"\d+\.\d{12,}", latex) is None


def test_single_point_parameter_assignments_are_visible() -> None:
    result, limits = _result(
        "K/(T*s+1)",
        FrequencyDomainWorkflowMode.SINGLE_POINT,
        parameters=(
            ParameterInputDraft("K", "2", "1"),
            ParameterInputDraft("T", "1", "5"),
        ),
    )

    latex = render_frequency_domain_solution_latex(result, limits)

    assert (
        r"\text{Parameterbelegungen:}\quad "
        r"\mathtt{K}=2,\quad \mathtt{T}=\frac{1}{5}"
    ) in latex


def test_single_point_singularity_keeps_denominator_and_invents_no_values() -> None:
    result, limits = _result(
        "1/(s^2+1)",
        FrequencyDomainWorkflowMode.SINGLE_POINT,
    )

    latex = render_frequency_domain_solution_latex(result, limits)

    assert r"N(\mathrm{j})=0=0" in latex
    assert r"\omega_s=1\,\mathrm{rad/s}" in latex
    assert r"\text{ ist singulär.}" in latex
    assert "Keine endlichen Frequenzgangwerte definiert" in latex
    assert r"\approx 0" not in latex


def test_single_point_zero_response_marks_phase_undefined() -> None:
    result, limits = _result(
        "0/(s+1)",
        FrequencyDomainWorkflowMode.SINGLE_POINT,
    )

    latex = render_frequency_domain_solution_latex(result, limits)

    assert r"|G(\mathrm{j})|=0" in latex
    assert r"L(1)=-\infty\,\mathrm{dB}" in latex
    assert r"\varphi(\omega)\text{ ist nicht definiert.}" in latex


def test_bode_report_contains_every_row_without_asymptotic_claims() -> None:
    result, limits = _result(
        "1/(s+1)",
        FrequencyDomainWorkflowMode.BODE,
    )
    assert result.bode_data_result is not None

    latex = render_frequency_domain_solution_latex(result, limits)
    table_rows = tuple(
        line
        for line in latex.splitlines()
        if line.endswith(r"\\")
    )

    assert r"\section*{Numerische Bode-Auswertung}" in latex
    assert r"s=\mathrm{j}\omega" in latex
    assert r"\begin{array}" in latex
    assert len(table_rows) == len(result.bode_data_result.points) + 1
    assert "asymptot" not in latex.lower()
    assert re.search(r"\d+\.\d{12,}", latex) is None


def test_unwrapped_phase_explains_only_a_real_nonzero_selected_offset() -> None:
    result, limits = _result(
        "1/(s/10+1)^3",
        FrequencyDomainWorkflowMode.BODE,
        omega_min="1/100",
        omega_max="1000",
        unwrap=True,
    )
    assert result.phase_unwrap_result is not None
    selected = next(
        point.grid_index
        for segment in result.phase_unwrap_result.segments
        for point in segment.points
        if point.phase_offset_turns != 0
    )

    latex = render_frequency_domain_solution_latex(
        result,
        limits,
        selected_bode_index=selected,
    )

    assert r"\varphi_{\mathrm{entf}}(\omega)=" in latex
    assert r"\varphi_{\mathrm{H}}(\omega)+k(\omega)\cdot360^\circ" in latex
    assert "keine zweite physikalische Phase" in latex
    assert r"k(\omega_{\mathrm{ausgewählt}})=" in latex


def test_refined_bode_marks_exact_support_points_and_singularity() -> None:
    base, limits = _result(
        "1/(s^2+1)",
        FrequencyDomainWorkflowMode.BODE,
        explicit="1",
    )
    plan = FrequencyDomainSingularityRefinementPlanner().plan(base, limits)
    assert plan.refined_request is not None
    refined = FrequencyDomainWorkflowService(limits).run(plan.refined_request)

    latex = render_frequency_domain_solution_latex(
        refined,
        limits,
        added_frequencies=plan.added_frequencies,
    )

    assert r"\frac{99}{100}\,\mathrm{rad/s}" in latex
    assert r"1\,\mathrm{rad/s}" in latex
    assert r"\frac{101}{100}\,\mathrm{rad/s}" in latex
    assert "Automatisch ergänzte numerische Stützstellen" in latex
    assert r"\omega_s=1\,\mathrm{rad/s}" in latex
    assert r"\text{ ist singulär.}" in latex


def test_selected_bode_row_changes_only_the_point_solution() -> None:
    result, limits = _result(
        "1/(s+1)",
        FrequencyDomainWorkflowMode.BODE,
    )
    assert result.bode_data_result is not None
    first = render_frequency_domain_solution_latex(
        result,
        limits,
        selected_bode_index=0,
    )
    second = render_frequency_domain_solution_latex(
        result,
        limits,
        selected_bode_index=1,
    )

    first_point = first.split(
        r"\section*{Ausgewählter Tabellenpunkt}",
        maxsplit=1,
    )[1]
    second_point = second.split(
        r"\section*{Ausgewählter Tabellenpunkt}",
        maxsplit=1,
    )[1]
    assert first_point != second_point
    assert (
        result.bode_data_result.points[0].frequency_response_point.status
        is FrequencyResponsePointStatus.DEFINED
    )


def test_renderer_source_contains_no_analysis_or_workflow_execution() -> None:
    source = (
        Path(__file__).parents[2]
        / "src/klausurbotpro/application/"
        "frequency_domain_solution_report_renderer.py"
    ).read_text(encoding="utf-8")

    for forbidden in (
        "Analyzer",
        "Parser",
        "GridGenerator",
        "WorkflowService",
        "log10(",
        "float(",
    ):
        assert forbidden not in source


def test_compact_decimal_text_keeps_invalid_decimal_text_safe() -> None:
    assert compact_decimal_text("not-a-decimal") == "not-a-decimal"
    assert compact_decimal_text("0.7071067811865475") == "0.707107"
