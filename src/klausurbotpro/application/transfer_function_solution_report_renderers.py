"""Pure renderers for structured transfer-function solution reports."""

from __future__ import annotations

import re

from klausurbotpro.application.transfer_function_solution_report_contracts import (
    ApproximationLine,
    ConditionLine,
    EquationLine,
    OverrideLine,
    ResultLine,
    SolutionLine,
    SolutionSectionKind,
    SolutionSectionStatus,
    SourceReferenceLine,
    TransferFunctionExpressionPair,
    TransferFunctionSolutionReport,
    TransformationLine,
    WarningLine,
)
from klausurbotpro.application.transfer_function_workflow_contracts import (
    WorkflowOverrideOriginKind,
    WorkflowStage,
)
from klausurbotpro.domain import DiagnosticSeverity

_HEADINGS = {
    SolutionSectionKind.GIVEN: "Gegeben",
    SolutionSectionKind.TRANSFER_FUNCTION: "Übertragungsfunktion",
    SolutionSectionKind.NUMERATOR_DENOMINATOR: "Zähler und Nenner",
    SolutionSectionKind.REDUCTION: "Reduktion",
    SolutionSectionKind.PREREQUISITES: "Voraussetzungen",
    SolutionSectionKind.DOMAIN_EXCLUSIONS: "Definitionsausschlüsse",
    SolutionSectionKind.PARAMETER_SUBSTITUTIONS: "Parametersubstitutionen",
    SolutionSectionKind.ZEROS: "Nullstellen",
    SolutionSectionKind.POLES: "Pole",
    SolutionSectionKind.POLE_REAL_PARTS: "Realteile der Pole",
    SolutionSectionKind.STABILITY: "Stabilität",
    SolutionSectionKind.DYNAMIC_BEHAVIOR: "Dynamisches Verhalten",
    SolutionSectionKind.SOURCES: "Quellen",
    SolutionSectionKind.WORKFLOW_NOTICES: "Workflow-Hinweise",
}

_OPERATION_LABELS = {
    "clear_parameter_denominators": "Parameternenner beseitigen",
    "remove_common_numeric_factor": "gemeinsamen Zahlenfaktor kürzen",
    "remove_common_polynomial_factor": "gemeinsamen Polynomfaktor kürzen",
    "normalize_safe_symbolic_scale": "sichere symbolische Skala normieren",
    "normalize_sign": "Vorzeichen normieren",
    "reduce_zero_numerator": "Nullzähler reduzieren",
    "no_reduction": "keine Reduktion erforderlich",
}

_SEVERITY_LABELS = {
    DiagnosticSeverity.INFO: "INFO",
    DiagnosticSeverity.WARNING: "WARNUNG",
    DiagnosticSeverity.ERROR: "FEHLER",
}

_SECTION_STATUS_LABELS = {
    SolutionSectionStatus.COMPLETE: "vollständig",
    SolutionSectionStatus.PARTIAL: "teilweise verfügbar",
    SolutionSectionStatus.FAILED: "fehlgeschlagen",
    SolutionSectionStatus.BLOCKED: (
        "nicht berechnet, da eine vorherige Stufe fehlgeschlagen ist"
    ),
    SolutionSectionStatus.NOT_APPLICABLE: "nicht erforderlich",
}

_EMPTY_SECTION_LABELS = {
    SolutionSectionKind.PREREQUISITES: "keine",
    SolutionSectionKind.DOMAIN_EXCLUSIONS: "keine",
    SolutionSectionKind.PARAMETER_SUBSTITUTIONS: "keine",
    SolutionSectionKind.SOURCES: "keine",
    SolutionSectionKind.WORKFLOW_NOTICES: "keine",
}

_WORKFLOW_STAGE_LABELS = {
    WorkflowStage.PARSE: "Parse",
    WorkflowStage.RAW_TRANSFER_FUNCTION: "Raw-Transferfunktion",
    WorkflowStage.REDUCTION: "Reduktion",
    WorkflowStage.ROOT_ANALYSIS: "Wurzelanalyse",
    WorkflowStage.STABILITY_ANALYSIS: "Stabilitätsanalyse",
}

_OVERRIDE_ORIGIN_LABELS = {
    WorkflowOverrideOriginKind.MANUAL: "manuelle Vorgabe",
    WorkflowOverrideOriginKind.IMPORT: "importierte Vorgabe",
    WorkflowOverrideOriginKind.TEST: "Testvorgabe",
}

_PLAIN_RELATION_LABELS = {
    "not assigned": "nicht belegt",
    "not fully decidable": "nicht vollständig entscheidbar",
}


def render_solution_report_plaintext(
    report: TransferFunctionSolutionReport,
) -> str:
    """Render deterministic copyable Unicode text."""

    _require_report(report)
    blocks: list[str] = []
    for section in report.sections:
        heading = _HEADINGS[section.kind]
        lines = [heading]
        if not section.lines:
            lines.append(_empty_section_label(section.kind, section.status))
        else:
            lines.extend(
                _render_plain_line(line, section.kind)
                for line in section.lines
            )
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def render_solution_report_latex(
    report: TransferFunctionSolutionReport,
) -> str:
    """Render a deterministic LaTeX fragment without external packages."""

    _require_report(report)
    blocks: list[str] = []
    for section in report.sections:
        heading = _escape_latex_text(_HEADINGS[section.kind])
        lines = [rf"\textbf{{{heading}}}"]
        if not section.lines:
            lines.append(
                rf"\textit{{{_escape_latex_text(
                    _empty_section_label(section.kind, section.status)
                )}}}"
            )
        else:
            lines.extend(
                _render_latex_line(line, section.kind)
                for line in section.lines
            )
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def _require_report(report: object) -> None:
    if type(report) is not TransferFunctionSolutionReport:
        raise TypeError("report must be a TransferFunctionSolutionReport.")


def _render_plain_line(
    line: SolutionLine,
    section_kind: SolutionSectionKind | None = None,
) -> str:
    if type(line) is EquationLine:
        equation = (
            f"{line.left.plaintext} {line.relation} "
            f"{line.right.plaintext}"
        )
        root_label = _root_equation_label(section_kind, line)
        return equation if root_label is None else f"{root_label}: {equation}"
    if type(line) is ResultLine:
        if section_kind is SolutionSectionKind.DYNAMIC_BEHAVIOR:
            if line.label == "Aussage":
                return line.exact_value.plaintext
            return f"{line.label}: {line.exact_value.plaintext}"
        if line.label == "Stabilitätsaussage":
            return f"⇒ {line.exact_value.plaintext}"
        if (
            line.label == "Ergebnis"
            and section_kind in (
                SolutionSectionKind.ZEROS,
                SolutionSectionKind.POLES,
            )
        ):
            return f"⇒ {line.exact_value.plaintext}"
        value = (
            f"{_plain_result_label(line.label)} = "
            f"{line.exact_value.plaintext}"
        )
        if line.numerical_approximation is not None:
            value += f" ≈ {line.numerical_approximation}"
        if line.multiplicity is not None:
            value += f"  (Multiplizität {line.multiplicity})"
        return value
    if type(line) is ApproximationLine:
        return (
            f"{_plain_result_label(line.label)} ≈ "
            f"{line.value.plaintext}"
        )
    if type(line) is ConditionLine:
        if line.relation == "NOT_ALL_ZERO":
            values = ", ".join(
                expression.plaintext for expression in line.expressions
            )
            return f"Nicht alle gleichzeitig null: {values}"
        values = ", ".join(
            expression.plaintext for expression in line.expressions
        )
        relation = _PLAIN_RELATION_LABELS.get(
            line.relation,
            line.relation,
        )
        return f"{values} {relation}"
    if type(line) is TransformationLine:
        before = _plain_pair(line.before)
        after = _plain_pair(line.after)
        operation = _OPERATION_LABELS.get(
            line.operation_kind,
            line.operation_kind,
        )
        factor = (
            ""
            if line.factor_or_operation is None
            else f" [{line.factor_or_operation.plaintext}]"
        )
        conditions = _plain_transformation_conditions(line)
        return f"{before}  -- {operation}{factor} ⇒  {after}{conditions}"
    if type(line) is OverrideLine:
        stage = _WORKFLOW_STAGE_LABELS[line.target_stage]
        origin = _OVERRIDE_ORIGIN_LABELS[line.origin_kind]
        return (
            f"[{origin} – {stage}] "
            f"{_escape_plain_text(line.reason)}"
        )
    if type(line) is WarningLine:
        severity = _SEVERITY_LABELS[line.severity]
        stage = "" if line.affected_stage is None else (
            f" ({_WORKFLOW_STAGE_LABELS[line.affected_stage]})"
        )
        return (
            f"[{severity}]{stage} "
            f"{_escape_plain_text(line.statement)}"
        )
    if type(line) is SourceReferenceLine:
        page = "" if line.page is None else f", Seite {line.page}"
        return (
            f"{_escape_plain_text(line.document_name)}{page}, "
            f"{_escape_plain_text(line.location)}: "
            f"{_escape_plain_text(line.claim)}"
        )
    raise TypeError("Unsupported solution line.")


def _render_latex_line(
    line: SolutionLine,
    section_kind: SolutionSectionKind | None = None,
) -> str:
    if type(line) is EquationLine:
        relation = _latex_relation(line.relation)
        equation = rf"\[{line.left.latex} {relation} {line.right.latex}\]"
        root_label = _root_equation_label(section_kind, line)
        if root_label is None:
            return equation
        return (
            rf"\textit{{{_escape_latex_text(root_label)}:}}"
            f"\n{equation}"
        )
    if type(line) is ResultLine:
        if section_kind is SolutionSectionKind.DYNAMIC_BEHAVIOR:
            if line.label == "Aussage":
                return _escape_latex_text(line.exact_value.plaintext)
            return (
                rf"\textit{{{_escape_latex_text(line.label)}:}} "
                rf"{_escape_latex_text(line.exact_value.plaintext)}"
            )
        if line.label == "Stabilitätsaussage":
            return (
                rf"\[\Longrightarrow "
                rf"\boxed{{{line.exact_value.latex}}}\]"
            )
        if (
            line.label == "Ergebnis"
            and section_kind in (
                SolutionSectionKind.ZEROS,
                SolutionSectionKind.POLES,
            )
        ):
            return rf"\[\Longrightarrow {line.exact_value.latex}\]"
        approximation = (
            ""
            if line.numerical_approximation is None
            else rf" \approx \mbox{{{_escape_latex_text(line.numerical_approximation)}}}"
        )
        multiplicity = (
            ""
            if line.multiplicity is None
            else rf"\quad\mbox{{Multiplizität {line.multiplicity}}}"
        )
        exact_latex = line.exact_value.latex
        if (
            section_kind is SolutionSectionKind.POLES
            or line.label.startswith(("s_excluded,", "s_cancelled,"))
        ):
            exact_latex = _engineering_complex_latex(exact_latex)
        return (
            rf"\[{_latex_result_label(line.label)} = "
            rf"{exact_latex}{approximation}{multiplicity}\]"
        )
    if type(line) is ApproximationLine:
        return (
            rf"\[{_latex_result_label(line.label)} \approx "
            rf"{line.value.latex}\]"
        )
    if type(line) is ConditionLine:
        values = ", ".join(
            expression.latex for expression in line.expressions
        )
        if line.relation == "NOT_ALL_ZERO":
            return (
                r"\[\mbox{Nicht alle gleichzeitig null: }\;"
                rf"{values}\]"
            )
        return rf"\[{values} {_latex_relation(line.relation)}\]"
    if type(line) is TransformationLine:
        operation = _OPERATION_LABELS.get(
            line.operation_kind,
            line.operation_kind,
        )
        factor = (
            ""
            if line.factor_or_operation is None
            else rf"\;[{line.factor_or_operation.latex}]"
        )
        conditions = _latex_transformation_conditions(line)
        return (
            rf"\[{_latex_pair(line.before)} "
            rf"\mathop{{\Longrightarrow}}^{{"
            rf"\mbox{{{_escape_latex_text(operation)}}}{factor}}} "
            rf"{_latex_pair(line.after)}{conditions}\]"
        )
    if type(line) is OverrideLine:
        stage = _WORKFLOW_STAGE_LABELS[line.target_stage]
        origin = _OVERRIDE_ORIGIN_LABELS[line.origin_kind]
        text = (
            f"{origin} – {stage}: "
            f"{line.reason}"
        )
        return rf"\textit{{{_escape_latex_text(text)}}}"
    if type(line) is WarningLine:
        severity = _SEVERITY_LABELS[line.severity]
        stage = "" if line.affected_stage is None else (
            f" ({_WORKFLOW_STAGE_LABELS[line.affected_stage]})"
        )
        text = f"[{severity}]{stage} {line.statement}"
        return rf"\textit{{{_escape_latex_text(text)}}}"
    if type(line) is SourceReferenceLine:
        page = "" if line.page is None else f", Seite {line.page}"
        text = (
            f"{line.document_name}{page}, {line.location}: {line.claim}"
        )
        return _escape_latex_text(text)
    raise TypeError("Unsupported solution line.")


def _plain_pair(pair: TransferFunctionExpressionPair) -> str:
    return f"({pair.numerator.plaintext})/({pair.denominator.plaintext})"


def _latex_pair(pair: TransferFunctionExpressionPair) -> str:
    return rf"\frac{{{pair.numerator.latex}}}{{{pair.denominator.latex}}}"


def _latex_relation(relation: str) -> str:
    relations = {
        "=": "=",
        "!= 0": r"\neq 0",
        "< 0": "< 0",
        "<= 0": r"\leq 0",
        "> 0": "> 0",
        "= 0, multiplicity = 1": r"= 0,\ \mathrm{mult}=1",
        "= 0, multiplicity > 1": r"= 0,\ \mathrm{mult}>1",
        "not assigned": r"\mbox{nicht belegt}",
        "not fully decidable": r"\mbox{nicht vollständig entscheidbar}",
    }
    try:
        return relations[relation]
    except KeyError as error:
        raise ValueError(f"Unsupported mathematical relation: {relation}") from error


def _latex_result_label(label: str) -> str:
    if (
        label.startswith(("Re(s_", "Re(p_"))
        and label.endswith(")")
    ):
        index = label[5:-1]
        if index.isdigit():
            symbol = label[3]
            return rf"\operatorname{{Re}}({symbol}_{{{index}}})"
    for prefix in ("z_", "s_", "p_"):
        if label.startswith(prefix) and label[len(prefix) :].isdigit():
            return rf"{prefix[0]}_{{{label[len(prefix):]}}}"
    for prefix in ("s_excluded,", "s_cancelled,"):
        if label.startswith(prefix) and label[len(prefix) :].isdigit():
            role = (
                "ausgeschlossen"
                if prefix == "s_excluded,"
                else "gekürzt"
            )
            return rf"s_{{\mathrm{{{role}}},{label[len(prefix):]}}}"
    return rf"\mbox{{{_escape_latex_text(label)}}}"


def _plain_result_label(label: str) -> str:
    for prefix, replacement in (
        ("s_excluded,", "Ausgeschlossene Stelle s_"),
        ("s_cancelled,", "Gekürzte Stelle s_"),
    ):
        if label.startswith(prefix) and label[len(prefix) :].isdigit():
            return f"{replacement}{label[len(prefix):]}"
    return label


def _root_equation_label(
    section_kind: SolutionSectionKind | None,
    line: EquationLine,
) -> str | None:
    if line.identifier != "root_equation":
        return None
    if section_kind is SolutionSectionKind.ZEROS:
        return "Nullstellenbedingung"
    if section_kind is SolutionSectionKind.POLES:
        return "Polgleichung"
    return None


def _empty_section_label(
    kind: SolutionSectionKind,
    status: SolutionSectionStatus,
) -> str:
    if status is SolutionSectionStatus.NOT_APPLICABLE:
        return _EMPTY_SECTION_LABELS.get(
            kind,
            _SECTION_STATUS_LABELS[status],
        )
    return _SECTION_STATUS_LABELS[status]


def _plain_transformation_conditions(line: TransformationLine) -> str:
    conditions = (
        *line.retained_prerequisites,
        *line.retained_domain_exclusions,
    )
    if not conditions:
        return ""
    rendered = "; ".join(_render_plain_line(condition) for condition in conditions)
    return f"  | erhalten: {rendered}"


def _latex_transformation_conditions(line: TransformationLine) -> str:
    conditions = (
        *line.retained_prerequisites,
        *line.retained_domain_exclusions,
    )
    if not conditions:
        return ""
    rendered = r";\ ".join(
        _latex_condition_inline(condition) for condition in conditions
    )
    return rf"\quad\mathrm{{erhalten:}}\ {rendered}"


def _latex_condition_inline(line: ConditionLine) -> str:
    values = ", ".join(expression.latex for expression in line.expressions)
    if line.relation == "NOT_ALL_ZERO":
        return (
            r"\mathrm{nicht\ alle\ gleichzeitig\ null}"
            rf"\left({values}\right)"
        )
    return rf"{values} {_latex_relation(line.relation)}"


def _escape_plain_text(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("\r", "\\r")
        .replace("\n", "\\n")
        .replace("\t", "\\t")
    )


def _escape_latex_text(value: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "{": r"\{",
        "}": r"\}",
        "$": r"\$",
        "&": r"\&",
        "#": r"\#",
        "%": r"\%",
        "_": r"\_",
        "^": r"\textasciicircum{}",
        "~": r"\textasciitilde{}",
        "\r": r"\textbackslash{}r",
        "\n": r"\textbackslash{}n",
        "\t": r"\textbackslash{}t",
    }
    return "".join(replacements.get(character, character) for character in value)


def _engineering_complex_latex(value: str) -> str:
    return re.sub(
        r"(?<![A-Za-z])i(?![A-Za-z])",
        lambda _match: r"\mathrm{j}",
        value,
    )


__all__ = [
    "render_solution_report_latex",
    "render_solution_report_plaintext",
]
