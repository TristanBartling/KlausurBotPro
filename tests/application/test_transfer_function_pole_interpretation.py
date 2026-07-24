"""Acceptance tests for rounded poles and qualitative E/A interpretation."""

from __future__ import annotations

import re

import pytest

from klausurbotpro.application import (
    ApproximationLine,
    OverrideProvenance,
    ResultLine,
    SolutionSectionKind,
    TransferFunctionSolutionReport,
    TransferFunctionSolutionReportBuilder,
    TransferFunctionWorkflowRequest,
    TransferFunctionWorkflowService,
    TransferFunctionWorkflowState,
    WorkflowDiagnosticEntry,
    WorkflowInputForm,
    WorkflowOverrideOriginKind,
    WorkflowStage,
    render_solution_report_latex,
    render_solution_report_plaintext,
)
from klausurbotpro.application._solution_report_formatting import (
    compact_decimal_text,
)
from klausurbotpro.application.transfer_function_solution_report_builder import (
    _deduplicated_notice_entries,
)
from klausurbotpro.domain import (
    Diagnostic,
    DiagnosticCode,
    DiagnosticSeverity,
    PoleDynamicsClassification,
    PoleDynamicsModelBasis,
)


def _result(
    expression: str,
    *,
    parameters: tuple[str, ...] = (),
) -> tuple[TransferFunctionWorkflowState, TransferFunctionSolutionReport, str, str]:
    state = TransferFunctionWorkflowService().run(
        TransferFunctionWorkflowRequest(
            WorkflowInputForm.COMMON,
            common_expression_text=expression,
            allowed_parameter_names=parameters,
        )
    )
    report = TransferFunctionSolutionReportBuilder().build(state)
    return (
        state,
        report,
        render_solution_report_plaintext(report),
        render_solution_report_latex(report),
    )


def _lines(
    report: TransferFunctionSolutionReport,
    kind: SolutionSectionKind,
) -> tuple[object, ...]:
    section = report.section(kind)
    assert section is not None
    return section.lines


def _classification(expression: str) -> PoleDynamicsClassification:
    state, _report, _plain, _latex = _result(expression)
    stability = state.stability_analysis_result
    assert stability is not None
    return stability.pole_dynamics.classification


def test_ref_tf_01a_keeps_exact_poles_before_compact_approximations() -> None:
    state, report, plaintext, latex = _result("s/(2*s^2+4*s+6)")
    pole_lines = _lines(report, SolutionSectionKind.POLES)
    exact_lines = [line for line in pole_lines if type(line) is ResultLine]
    approximate_lines = [
        line for line in pole_lines if type(line) is ApproximationLine
    ]

    assert {line.exact_value.plaintext for line in exact_lines} >= {
        "-1 - sqrt(2)*I",
        "-1 + sqrt(2)*I",
    }
    assert {line.value.plaintext for line in approximate_lines} == {
        "-1 - j*1.41421",
        "-1 + j*1.41421",
    }
    assert max(
        index for index, line in enumerate(pole_lines) if type(line) is ResultLine
    ) < min(
        index
        for index, line in enumerate(pole_lines)
        if type(line) is ApproximationLine
    )
    assert plaintext.index("p_2 = -1 + sqrt(2)*I") < plaintext.index(
        "p_1 ≈ -1 - j*1.41421"
    )
    assert latex.index(r"p_{2} = -1 + \sqrt{2} \mathrm{j}") < latex.index(
        r"p_{1} \approx -1 - \mathrm{j}\,1.41421"
    )
    stability = state.stability_analysis_result
    assert stability is not None
    assert stability.pole_dynamics.classification is (
        PoleDynamicsClassification.DAMPED_OSCILLATORY_COMPONENT
    )
    assert stability.pole_dynamics.model_basis is (
        PoleDynamicsModelBasis.REDUCED_EA_TRANSFER_FUNCTION
    )
    assert stability.pole_dynamics.is_available


def test_ref_tf_01b_has_exact_integer_poles_without_decimal_noise() -> None:
    state, report, plaintext, latex = _result("4*s/(2*s^2+8*s+6)")
    pole_lines = _lines(report, SolutionSectionKind.POLES)

    assert {line.exact_value.plaintext for line in pole_lines if type(line) is ResultLine} >= {
        "-1",
        "-3",
    }
    assert not any(type(line) is ApproximationLine for line in pole_lines)
    assert "N(s) = 2*s**2 + 8*s + 6" in plaintext
    assert "p_1 = -1" in plaintext
    assert "p_2 = -3" in plaintext
    assert "-1.0" not in plaintext
    assert "-3.0" not in plaintext
    assert r"2 s^{2} + 8 s + 6" in latex
    stability = state.stability_analysis_result
    assert stability is not None
    assert stability.pole_dynamics.classification is (
        PoleDynamicsClassification.APERIODIC
    )


@pytest.mark.parametrize(
    ("value", "expected"),
    (
        ("1.4142135623730951", "1.41421"),
        ("-1.000000000000", "-1"),
        ("-0.000000000000", "0"),
        ("123456789", "1.23457e+8"),
        ("0.00000123456789", "0.00000123457"),
    ),
)
def test_decimal_formatter_uses_at_most_six_significant_digits(
    value: str,
    expected: str,
) -> None:
    assert compact_decimal_text(value) == expected


@pytest.mark.parametrize(
    ("expression", "classification"),
    (
        ("1/(s+2)^2", PoleDynamicsClassification.APERIODIC),
        (
            "1/((s+5)*(s^2+2*s+5))",
            PoleDynamicsClassification.DAMPED_OSCILLATORY_COMPONENT,
        ),
        ("1/(s^2-2*s+5)", PoleDynamicsClassification.UNCLASSIFIED),
        ("1/(s^2+1)", PoleDynamicsClassification.UNCLASSIFIED),
        ("1/(s*(s+1))", PoleDynamicsClassification.UNCLASSIFIED),
    ),
)
def test_safety_cases_receive_only_supported_classifications(
    expression: str,
    classification: PoleDynamicsClassification,
) -> None:
    assert _classification(expression) is classification


def test_mixed_stable_poles_claim_only_an_oscillatory_component() -> None:
    state, report, plaintext, _latex = _result(
        "1/((s+5)*(s^2+2*s+5))"
    )

    assert (
        "Das E/A-Verhalten enthält einen gedämpft schwingenden Anteil."
        in plaintext
    )
    assert "reine Zweipolschwingung" not in plaintext
    assert not state.aggregated_diagnostics
    assert not any(
        type(line) is ApproximationLine
        for line in _lines(report, SolutionSectionKind.POLES)
    )


def test_unstable_gaussian_integer_poles_have_no_false_numeric_warning() -> None:
    state, report, plaintext, latex = _result("1/(s^2-2*s+5)")

    assert not state.aggregated_diagnostics
    assert not any(
        type(line) is ApproximationLine
        for line in _lines(report, SolutionSectionKind.POLES)
    )
    assert "numerische Prüfung ist jedoch fehlgeschlagen" not in plaintext
    assert "numerische Prüfung ist jedoch fehlgeschlagen" not in latex


def test_unassigned_parameter_has_no_invented_numeric_or_qualitative_result() -> None:
    state, report, plaintext, _latex = _result(
        "1/(s+a)",
        parameters=("a",),
    )

    assert not any(
        type(line) is ApproximationLine
        for line in _lines(report, SolutionSectionKind.POLES)
    )
    stability = state.stability_analysis_result
    assert stability is not None
    assert not stability.pole_dynamics.is_available
    assert (
        "Keine sichere qualitative Standardaussage im unterstützten Umfang."
        in plaintext
    )
    assert "gedämpft schwingenden Anteil" not in plaintext
    assert "ist aperiodisch" not in plaintext


def test_cancellation_interpretation_uses_reduced_ea_model_and_keeps_provenance() -> None:
    state, report, plaintext, latex = _result("(s+1)/((s+1)*(s+2))")
    stability = state.stability_analysis_result
    assert stability is not None

    assert stability.pole_dynamics.classification is (
        PoleDynamicsClassification.APERIODIC
    )
    assert "p_1 = -2" in plaintext
    assert "Gekürzte Stelle s_1 = -1" in plaintext
    notice = (
        "Die qualitative Aussage bezieht sich auf die reduzierte "
        "E/A-Übertragungsfunktion"
    )
    assert notice in plaintext
    assert notice in latex
    assert "Warnung" not in notice
    pole = next(
        line
        for line in _lines(report, SolutionSectionKind.POLES)
        if type(line) is ResultLine and line.label == "p_1"
    )
    assert pole.multiplicity == 1


def test_numeric_factor_reduction_does_not_claim_removed_dynamics() -> None:
    _state, report, plaintext, latex = _result("4*s/(2*s^2+8*s+6)")
    dynamics = _lines(report, SolutionSectionKind.DYNAMIC_BEHAVIOR)

    assert not any(
        type(line) is ResultLine
        and line.source_role == "reduced_model_notice"
        for line in dynamics
    )
    assert "entfernte Faktoren bleiben im Kürzungsprotokoll" not in plaintext
    assert "entfernte Faktoren bleiben im Kürzungsprotokoll" not in latex


def test_sign_normalization_does_not_claim_removed_dynamics() -> None:
    state, report, plaintext, latex = _result("-s/(-s^2-4*s-3)")
    reduction = state.reduction_result
    assert reduction is not None
    assert reduction.report is not None

    assert [step.kind.value for step in reduction.report.steps] == [
        "normalize_sign"
    ]
    assert not any(
        type(line) is ResultLine
        and line.source_role == "reduced_model_notice"
        for line in _lines(report, SolutionSectionKind.DYNAMIC_BEHAVIOR)
    )
    assert "entfernte Faktoren bleiben im Kürzungsprotokoll" not in plaintext
    assert "entfernte Faktoren bleiben im Kürzungsprotokoll" not in latex


def test_repeated_real_pole_keeps_multiplicity_and_is_aperiodic() -> None:
    state, report, plaintext, latex = _result("1/(s+2)^2")
    pole = next(
        line
        for line in _lines(report, SolutionSectionKind.POLES)
        if type(line) is ResultLine and line.label == "p_1"
    )

    assert pole.exact_value.plaintext == "-2"
    assert pole.multiplicity == 2
    assert "Das E/A-Verhalten ist aperiodisch." in plaintext
    assert len(state.aggregated_diagnostics) == 2
    notice = "Mehrfachwurzeln können numerisch schlecht konditioniert sein."
    assert plaintext.count(notice) == 1
    assert latex.count(notice) == 1


def test_notice_deduplication_preserves_stage_field_and_override_provenance() -> None:
    base = Diagnostic(
        DiagnosticSeverity.WARNING,
        DiagnosticCode.ROOT_ANALYSIS_ILL_CONDITIONED,
        "Hinweis",
        "Nenner",
        (("root_index", "0"),),
    )
    same_visible_identity = Diagnostic(
        DiagnosticSeverity.WARNING,
        DiagnosticCode.ROOT_ANALYSIS_ILL_CONDITIONED,
        "Hinweis",
        "Nenner",
        (("root_index", "1"),),
    )
    other_field = Diagnostic(
        DiagnosticSeverity.WARNING,
        DiagnosticCode.ROOT_ANALYSIS_ILL_CONDITIONED,
        "Hinweis",
        "Zähler",
    )
    other_diagnostic = Diagnostic(
        DiagnosticSeverity.WARNING,
        DiagnosticCode.ROOT_ANALYSIS_CONJUGATE_MISMATCH,
        "Hinweis",
        "Nenner",
    )
    provenance = OverrideProvenance(
        WorkflowOverrideOriginKind.MANUAL,
        "Geprüfte Vorgabe",
        1,
        WorkflowStage.ROOT_ANALYSIS,
    )
    entries = (
        WorkflowDiagnosticEntry(WorkflowStage.ROOT_ANALYSIS, 0, base, 1),
        WorkflowDiagnosticEntry(
            WorkflowStage.ROOT_ANALYSIS,
            1,
            same_visible_identity,
            1,
        ),
        WorkflowDiagnosticEntry(
            WorkflowStage.STABILITY_ANALYSIS,
            0,
            base,
            1,
        ),
        WorkflowDiagnosticEntry(
            WorkflowStage.ROOT_ANALYSIS,
            2,
            other_field,
            1,
        ),
        WorkflowDiagnosticEntry(
            WorkflowStage.ROOT_ANALYSIS,
            3,
            other_diagnostic,
            1,
        ),
        WorkflowDiagnosticEntry(
            WorkflowStage.ROOT_ANALYSIS,
            4,
            base,
            1,
            provenance,
        ),
    )

    assert _deduplicated_notice_entries(entries) == (
        entries[0],
        entries[2],
        entries[3],
        entries[4],
        entries[5],
    )


def test_plaintext_and_latex_prioritize_primary_results_before_technical_sections() -> None:
    _state, _report, plaintext, latex = _result("s/(2*s^2+4*s+6)")
    primary_plain = (
        plaintext.index("Nullstellen\n"),
        plaintext.index("Pole\n"),
        plaintext.index("Stabilität\n"),
        plaintext.index("Dynamisches Verhalten\n"),
    )
    technical_plain = (
        plaintext.index("Reduktion\n"),
        plaintext.index("Definitionsausschlüsse\n"),
        plaintext.index("Voraussetzungen\n"),
        plaintext.index("Quellen\n"),
    )
    primary_latex = (
        latex.index(r"\textbf{Nullstellen}"),
        latex.index(r"\textbf{Pole}"),
        latex.index(r"\textbf{Stabilität}"),
        latex.index(r"\textbf{Dynamisches Verhalten}"),
    )
    technical_latex = (
        latex.index(r"\textbf{Reduktion}"),
        latex.index(r"\textbf{Definitionsausschlüsse}"),
        latex.index(r"\textbf{Voraussetzungen}"),
        latex.index(r"\textbf{Quellen}"),
    )

    assert primary_plain == tuple(sorted(primary_plain))
    assert max(primary_plain) < min(technical_plain)
    assert primary_latex == tuple(sorted(primary_latex))
    assert max(primary_latex) < min(technical_latex)


def test_each_rendered_numeric_component_has_at_most_six_significant_digits() -> None:
    _state, _report, plaintext, _latex = _result("s/(2*s^2+4*s+6)")
    numeric_lines = [line for line in plaintext.splitlines() if " ≈ " in line]

    assert numeric_lines
    for line in numeric_lines:
        components = re.findall(r"(?<![_\w])\d+(?:\.\d+)?", line.split("≈", 1)[1])
        assert components
        for component in components:
            assert len(component.replace(".", "").lstrip("0")) <= 6
