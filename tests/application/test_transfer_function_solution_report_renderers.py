"""Plaintext and LaTeX rendering of the same structured report."""

from dataclasses import replace

import pytest

from klausurbotpro.application import (
    ConditionLine,
    EquationLine,
    OverrideProvenance,
    RawTransferFunctionOverride,
    ResultLine,
    SolutionSectionKind,
    SolutionSectionStatus,
    SourceReferenceLine,
    TransferFunctionSolutionReportBuilder,
    TransferFunctionWorkflowRequest,
    TransferFunctionWorkflowService,
    TransferFunctionWorkflowState,
    TransformationLine,
    WarningLine,
    WorkflowInputForm,
    WorkflowOverrideOriginKind,
    WorkflowStage,
    render_solution_report_latex,
    render_solution_report_plaintext,
)
from klausurbotpro.application import (
    transfer_function_solution_report_builder as report_builder_module,
)
from klausurbotpro.domain import (
    ExactRationalValue,
    ParameterAssignment,
    ParameterSubstitutions,
)


def _state(expression: str) -> TransferFunctionWorkflowState:
    return TransferFunctionWorkflowService().run(
        TransferFunctionWorkflowRequest(
            WorkflowInputForm.COMMON,
            common_expression_text=expression,
        )
    )


def _parameterized_state(
    expression: str,
    *parameters: str,
) -> TransferFunctionWorkflowState:
    return TransferFunctionWorkflowService().run(
        TransferFunctionWorkflowRequest(
            WorkflowInputForm.COMMON,
            common_expression_text=expression,
            allowed_parameter_names=parameters,
        )
    )


def _separated_state(
    numerator: str,
    denominator: str,
) -> TransferFunctionWorkflowState:
    return TransferFunctionWorkflowService().run(
        TransferFunctionWorkflowRequest(
            WorkflowInputForm.SEPARATED,
            numerator_expression_text=numerator,
            denominator_expression_text=denominator,
        )
    )


_INTERNAL_OUTPUT_TOKENS = (
    "not_applicable",
    "blocked",
    "stable",
    "borderline_stable",
    "unstable",
    "symbolic_undetermined",
    "numerator",
    "denominator",
    "retained_domain_exclusion",
    "cancelled_location",
    "NOT_ALL_ZERO",
    "common",
    "separated",
)


def test_renderers_are_deterministic_and_do_not_mutate_report() -> None:
    report = TransferFunctionSolutionReportBuilder().build(_state("1/(s+1)"))
    before_hash = hash(report)

    first_plain = render_solution_report_plaintext(report)
    second_plain = render_solution_report_plaintext(report)
    first_latex = render_solution_report_latex(report)
    second_latex = render_solution_report_latex(report)

    assert first_plain == second_plain
    assert first_latex == second_latex
    assert hash(report) == before_hash
    assert "\x1b[" not in first_plain
    assert "\\begin{document}" not in first_latex
    assert "\\xRightarrow" not in first_latex
    assert "p_{1}" in first_latex
    assert r"\operatorname{Re}(p_{1})" in first_latex
    for internal_value in _INTERNAL_OUTPUT_TOKENS:
        assert internal_value not in first_plain
        assert internal_value not in first_latex


def test_retained_not_all_zero_condition_is_german_in_both_formats() -> None:
    report = TransferFunctionSolutionReportBuilder().build(
        _parameterized_state("1/((K-1)*s+T)", "K", "T")
    )
    prerequisites = report.section(SolutionSectionKind.PREREQUISITES)
    reduction = report.section(SolutionSectionKind.REDUCTION)
    assert prerequisites is not None
    assert reduction is not None
    condition = next(
        line for line in prerequisites.lines if type(line) is ConditionLine
    )
    transformation = next(
        line for line in reduction.lines if type(line) is TransformationLine
    )
    assert condition.relation == "NOT_ALL_ZERO"
    assert tuple(
        expression.plaintext for expression in condition.expressions
    ) == ("K - 1", "T")
    retained_transformation = replace(
        transformation,
        retained_prerequisites=(condition,),
    )
    retained_reduction = replace(
        reduction,
        lines=tuple(
            retained_transformation if line is transformation else line
            for line in reduction.lines
        ),
    )
    report = replace(
        report,
        sections=tuple(
            retained_reduction if section is reduction else section
            for section in report.sections
        ),
    )

    plaintext = render_solution_report_plaintext(report)
    latex = render_solution_report_latex(report)

    assert "Nicht alle gleichzeitig null: K - 1, T" in plaintext
    assert (
        r"\mathrm{nicht\ alle\ gleichzeitig\ null}"
        r"\left(K - 1, T\right)"
    ) in latex
    assert "NOT_ALL_ZERO" not in plaintext
    assert "NOT_ALL_ZERO" not in latex


def test_representative_complete_outputs_hide_internal_contract_tokens() -> None:
    service = TransferFunctionWorkflowService()
    base = _state("1/(s+1)")
    override_source = _state("1/(s+2)")
    assert override_source.raw_value is not None
    overridden = service.apply_override(
        base,
        RawTransferFunctionOverride(
            override_source.raw_value,
            OverrideProvenance(
                WorkflowOverrideOriginKind.MANUAL,
                "Geprüfte Vorgabe",
                1,
                WorkflowStage.RAW_TRANSFER_FUNCTION,
            ),
        ),
    )
    states = (
        base,
        _separated_state("1", "s+1"),
        _parameterized_state("1/(T*s+1)", "T"),
        _parameterized_state("1/((K-1)*s+T)", "K", "T"),
        _state("open('x')"),
        _state("1/s"),
        _state("1/(s-1)"),
        _state("(s+1)/(s+1)"),
        overridden,
    )

    for state in states:
        report = TransferFunctionSolutionReportBuilder().build(state)
        outputs = (
            render_solution_report_plaintext(report),
            render_solution_report_latex(report),
        )
        for output in outputs:
            for internal_value in _INTERNAL_OUTPUT_TOKENS:
                assert internal_value not in output


def test_renderers_include_every_structured_equation_and_result() -> None:
    report = TransferFunctionSolutionReportBuilder().build(
        _state("1/(s^2+3*s+2)")
    )
    plaintext = render_solution_report_plaintext(report)
    latex = render_solution_report_latex(report)

    for section in report.sections:
        for line in section.lines:
            if type(line) is EquationLine:
                assert line.left.plaintext in plaintext
                assert line.left.latex in latex
                assert line.right.plaintext in plaintext
                assert line.right.latex in latex
            elif type(line) is ResultLine:
                assert line.exact_value.plaintext in plaintext
                assert line.exact_value.latex in latex


def test_override_reason_is_safely_escaped_in_both_formats() -> None:
    service = TransferFunctionWorkflowService()
    base = _state("1/(s+1)")
    source = _state("1/(s+2)")
    assert source.raw_value is not None
    changed = service.apply_override(
        base,
        RawTransferFunctionOverride(
            source.raw_value,
            OverrideProvenance(
                WorkflowOverrideOriginKind.MANUAL,
                "Grund_%{x}\nzweite Zeile",
                1,
                WorkflowStage.RAW_TRANSFER_FUNCTION,
            ),
        ),
    )
    report = TransferFunctionSolutionReportBuilder().build(changed)

    plaintext = render_solution_report_plaintext(report)
    latex = render_solution_report_latex(report)

    assert "Grund_%{x}\\nzweite Zeile" in plaintext
    assert r"Grund\_\%\{x\}\textbackslash{}nzweite Zeile" in latex


def test_sources_are_copied_only_from_structured_stability_result() -> None:
    state = _state("1/(s+1)")
    assert state.stability_analysis_result is not None
    report = TransferFunctionSolutionReportBuilder().build(state)
    sources = report.section(SolutionSectionKind.SOURCES)
    assert sources is not None
    assert sources.status is SolutionSectionStatus.COMPLETE

    actual = tuple(
        (
            line.document_name,
            line.page,
            line.location,
            line.claim,
        )
        for line in sources.lines
        if type(line) is SourceReferenceLine
    )
    expected = tuple(
        (
            reference.document_name,
            reference.page,
            reference.location,
            reference.claim,
        )
        for reference in state.stability_analysis_result.source_references
    )
    assert actual == expected


def test_succeeded_stability_without_sources_is_not_applicable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = _state("1/(s+1)")
    assert state.stability_analysis_result is not None
    object.__setattr__(
        state.stability_analysis_result,
        "source_references",
        (),
    )
    monkeypatch.setattr(
        report_builder_module,
        "validate_workflow_state",
        lambda state, limits: (),
    )

    report = TransferFunctionSolutionReportBuilder().build(state)
    sources = report.section(SolutionSectionKind.SOURCES)

    assert sources is not None
    assert sources.status is SolutionSectionStatus.NOT_APPLICABLE
    assert not sources.lines
    assert "Quellen\nkeine" in render_solution_report_plaintext(report)
    assert "not_applicable" not in render_solution_report_plaintext(report)
    assert "not\\_applicable" not in render_solution_report_latex(report)


def test_root_equations_and_blocked_sections_are_labeled_in_german() -> None:
    complete = TransferFunctionSolutionReportBuilder().build(
        _state("1/(s+1)")
    )
    failed = TransferFunctionSolutionReportBuilder().build(
        _state("open('x')")
    )

    complete_plain = render_solution_report_plaintext(complete)
    complete_latex = render_solution_report_latex(complete)
    failed_plain = render_solution_report_plaintext(failed)
    failed_latex = render_solution_report_latex(failed)

    assert "Nullstellenbedingung: Z(s) = 0" in complete_plain
    assert "Polgleichung: N(s) = 0" in complete_plain
    assert "Nullstellenbedingung" in complete_latex
    assert "Polgleichung" in complete_latex
    blocked = (
        "nicht berechnet, da eine vorherige Stufe fehlgeschlagen ist"
    )
    assert blocked in failed_plain
    assert blocked in failed_latex
    assert "[blocked]" not in failed_plain
    assert "blocked" not in failed_latex


def test_warning_severities_are_preserved_and_rendered() -> None:
    info_report = TransferFunctionSolutionReportBuilder().build(
        _state("0/(s+1)")
    )
    warning_state = TransferFunctionWorkflowService().run(
        TransferFunctionWorkflowRequest(
            WorkflowInputForm.COMMON,
            common_expression_text="1/(T*s+1)",
            allowed_parameter_names=("T",),
        )
    )
    warning_report = TransferFunctionSolutionReportBuilder().build(
        warning_state
    )
    error_report = TransferFunctionSolutionReportBuilder().build(
        _state("open('x')")
    )

    for state, report in (
        (
            TransferFunctionWorkflowService().run(
                TransferFunctionWorkflowRequest(
                    WorkflowInputForm.COMMON,
                    common_expression_text="0/(s+1)",
                )
            ),
            info_report,
        ),
        (warning_state, warning_report),
    ):
        notices = report.section(SolutionSectionKind.WORKFLOW_NOTICES)
        assert notices is not None
        actual = tuple(
            line.severity
            for line in notices.lines
            if type(line) is WarningLine
        )
        expected = tuple(
            entry.diagnostic.severity
            for entry in state.aggregated_diagnostics
        )
        assert actual == expected

    assert "[INFO]" in render_solution_report_plaintext(info_report)
    assert "[WARNUNG]" in render_solution_report_plaintext(warning_report)
    assert "[FEHLER]" in render_solution_report_plaintext(error_report)
    assert r"[INFO]" in render_solution_report_latex(info_report)
    assert r"[WARNUNG]" in render_solution_report_latex(warning_report)
    assert r"[FEHLER]" in render_solution_report_latex(error_report)


def test_renderers_reject_wrong_top_level_types() -> None:
    with pytest.raises(TypeError, match="TransferFunctionSolutionReport"):
        render_solution_report_plaintext(object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="TransferFunctionSolutionReport"):
        render_solution_report_latex(object())  # type: ignore[arg-type]


def test_unstable_report_quantifies_only_one_right_half_plane_pole() -> None:
    report = TransferFunctionSolutionReportBuilder().build(
        _state("(s+3)/(s^2-s-2)")
    )

    latex = render_solution_report_latex(report)

    assert r"\[z_{1} = -3" in latex
    assert r"\[p_{1} = 2" in latex
    assert r"\[p_{2} = -1" in latex
    assert r"\operatorname{Re}(p_{1}) = 2" in latex
    assert r"\exists i:\operatorname{Re}(p_i) > 0" in latex
    assert r"\operatorname{Re}(p_i) > 0" in latex
    assert r"\[\operatorname{Re}(p_i) > 0\]" not in latex
    assert r"\Longrightarrow \boxed{\mbox{System ist instabil.}}" in latex


def test_parameter_substitution_shows_existing_specialized_transfer_value() -> None:
    substitutions = ParameterSubstitutions(
        (
            ParameterAssignment("K", ExactRationalValue(2)),
            ParameterAssignment("T", ExactRationalValue(1, 5)),
        )
    )
    state = TransferFunctionWorkflowService().run(
        TransferFunctionWorkflowRequest(
            WorkflowInputForm.COMMON,
            common_expression_text="K/(T*s+1)",
            allowed_parameter_names=("K", "T"),
            substitutions=substitutions,
        )
    )

    latex = render_solution_report_latex(
        TransferFunctionSolutionReportBuilder().build(state)
    )

    assert (
        r"\left.G(s)\right|_{K=2,\,T=\frac{1}{5}}"
        r" = \frac{2}{\frac{s}{5} + 1}"
    ) in latex
    assert r"\[p_{1} = -5" in latex
    assert r"\operatorname{Re}(p_{1}) = -5" in latex
    assert r"\Longrightarrow \boxed{\mbox{System ist E/A-stabil.}}" in latex


def test_complex_poles_use_control_engineering_j_in_latex() -> None:
    report = TransferFunctionSolutionReportBuilder().build(
        _state("1/(s^2+4*s+13)")
    )

    latex = render_solution_report_latex(report)

    assert r"\[p_{1} = -2 - 3 \mathrm{j}" in latex
    assert r"\[p_{2} = -2 + 3 \mathrm{j}" in latex
    assert r"3 i" not in latex
