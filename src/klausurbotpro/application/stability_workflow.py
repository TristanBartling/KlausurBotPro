"""Safe orchestration for polynomial and transfer-function stability input."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

import sympy as sp

from klausurbotpro.application.transfer_function_preparation_contracts import (
    TransferFunctionPreparationResult,
)
from klausurbotpro.application.transfer_function_preparation_service import (
    TransferFunctionPreparationService,
)
from klausurbotpro.application.transfer_function_workflow_contracts import (
    TransferFunctionWorkflowRequest,
    WorkflowInputForm,
)
from klausurbotpro.domain.expression import ExactExpression
from klausurbotpro.domain.hurwitz_analyzer import analyze_hurwitz
from klausurbotpro.domain.hurwitz_contracts import HurwitzAnalysisResult
from klausurbotpro.domain.parameter_core import canonicalize_characteristic_polynomial
from klausurbotpro.domain.parameter_core_contracts import (
    AnalysisTarget,
    AtomicParameterCondition,
    CancellationReport,
    CancellationStatus,
    CharacteristicPolynomialInput,
    ConditionOrigin,
    PolynomialRole,
    Relation,
    SourceProvenance,
)
from klausurbotpro.domain.routh_analyzer import analyze_routh
from klausurbotpro.domain.routh_contracts import RouthAnalysisResult
from klausurbotpro.domain.stability_presentation import (
    display_math,
    format_parameter_region_plain,
    latex_additive_equation,
    latex_transfer_function,
    paragraph,
)
from klausurbotpro.domain.transfer_function_reduction_contracts import (
    TransferFunctionReductionStepKind,
)
from klausurbotpro.parsing import ParserConfig, SafeExpressionParser

_RELATION_PATTERN = re.compile(r"(<=|>=|!=|=|<|>)")
_RELATIONS = {
    "=": Relation.EQ,
    "!=": Relation.NE,
    "<": Relation.LT,
    "<=": Relation.LE,
    ">": Relation.GT,
    ">=": Relation.GE,
}


class StabilityMethod(StrEnum):
    HURWITZ = "hurwitz"
    ROUTH = "routh"


class StabilityInputMode(StrEnum):
    CHARACTERISTIC_POLYNOMIAL = "characteristic_polynomial"
    TRANSFER_FUNCTION = "transfer_function"


@dataclass(frozen=True, slots=True)
class StabilityInputDraft:
    polynomial_text: str = ""
    variable_name: str = "s"
    decision_parameters_text: str = ""
    assumptions_text: str = ""
    role: PolynomialRole = PolynomialRole.DIRECT_CHARACTERISTIC_POLYNOMIAL
    analysis_target: AnalysisTarget = AnalysisTarget.INTERNAL_CLOSED_LOOP_ASYMPTOTIC
    provenance_note: str = ""
    cancellation_note: str = ""
    method: StabilityMethod = StabilityMethod.HURWITZ
    input_mode: StabilityInputMode = StabilityInputMode.CHARACTERISTIC_POLYNOMIAL
    transfer_function_text: str = ""


@dataclass(frozen=True, slots=True)
class StabilityWorkflowResult:
    analysis: HurwitzAnalysisResult | RouthAnalysisResult | None
    errors: tuple[str, ...] = ()
    source_steps: tuple[tuple[str, str], ...] = ()
    latex_preamble: str = ""
    transfer_preparation: TransferFunctionPreparationResult | None = None


def run_stability_workflow(draft: StabilityInputDraft) -> StabilityWorkflowResult:
    """Prepare one safe input and run the unchanged Hurwitz/Routh consumers."""
    variable = draft.variable_name.strip()
    parameters = tuple(
        item.strip() for item in draft.decision_parameters_text.split(",") if item.strip()
    )
    if (
        not variable.isidentifier()
        or len(parameters) > 2
        or any(not item.isidentifier() or item == variable for item in parameters)
        or len(set(parameters)) != len(parameters)
    ):
        return StabilityWorkflowResult(
            None, ("Variable oder Entscheidungsparameter sind ungültig.",)
        )
    allowed = frozenset((variable, *parameters))
    parser = SafeExpressionParser(ParserConfig(allowed_symbols=allowed))
    assumptions, errors = _parse_assumptions(draft.assumptions_text, parameters, parser)
    if errors:
        return StabilityWorkflowResult(None, errors)

    if draft.input_mode is StabilityInputMode.TRANSFER_FUNCTION:
        return _run_transfer_function(draft, variable, parameters, assumptions)
    return _run_polynomial(draft, variable, parameters, assumptions, parser)


def _run_polynomial(
    draft: StabilityInputDraft,
    variable: str,
    parameters: tuple[str, ...],
    assumptions: tuple[AtomicParameterCondition, ...],
    parser: SafeExpressionParser,
) -> StabilityWorkflowResult:
    parsed = parser.parse(draft.polynomial_text, "polynomial")
    if not parsed.succeeded or parsed.value is None:
        return StabilityWorkflowResult(None, tuple(item.message for item in parsed.diagnostics))
    cancellation = None
    if draft.role is PolynomialRole.REDUCED_TRANSFER_DENOMINATOR:
        cancellation = CancellationReport(
            CancellationStatus.FACTORS_REMOVED
            if draft.cancellation_note.strip()
            else CancellationStatus.NONE,
            draft.cancellation_note.strip(),
        )
    value = CharacteristicPolynomialInput(
        parsed.value,
        variable,
        parameters,
        (),
        assumptions,
        (),
        draft.role,
        draft.analysis_target,
        SourceProvenance(
            "Direkteingabe", draft.provenance_note.strip(), draft.provenance_note.strip()
        ),
        cancellation,
    )
    return StabilityWorkflowResult(_analyze(value, draft.method))


def _run_transfer_function(
    draft: StabilityInputDraft,
    variable: str,
    parameters: tuple[str, ...],
    assumptions: tuple[AtomicParameterCondition, ...],
) -> StabilityWorkflowResult:
    if draft.analysis_target is AnalysisTarget.STATE_ASYMPTOTIC:
        return StabilityWorkflowResult(
            None,
            (
                "Eine Führungsübertragungsfunktion reicht für den Nachweis der "
                "Zustandsstabilität nicht aus.",
            ),
        )
    source_text = draft.transfer_function_text or draft.polynomial_text
    preparation = TransferFunctionPreparationService().prepare(
        TransferFunctionWorkflowRequest(
            WorkflowInputForm.COMMON,
            common_expression_text=source_text,
            variable_name=variable,
            allowed_parameter_names=tuple(sorted(parameters)),
            field="transfer_function",
        )
    )
    if not preparation.succeeded:
        return StabilityWorkflowResult(
            None, tuple(item.message for item in preparation.diagnostics)
        )
    raw = preparation.raw_value
    reduced = preparation.reduced_value
    reduction = preparation.reduction_result
    assert raw is not None and reduced is not None and reduction is not None
    assert reduction.report is not None

    factors = tuple(
        step.factor
        for step in reduction.report.steps
        if step.factor is not None
        and step.kind
        in (
            TransferFunctionReductionStepKind.REMOVE_COMMON_NUMERIC_FACTOR,
            TransferFunctionReductionStepKind.REMOVE_COMMON_POLYNOMIAL_FACTOR,
        )
    )
    was_reduced = reduction.report.was_reduced
    cancellation = CancellationReport(
        CancellationStatus.FACTORS_REMOVED if factors else CancellationStatus.NONE,
        _cancellation_note(factors, was_reduced),
        factors,
    )
    external = draft.analysis_target is AnalysisTarget.EXTERNAL_BIBO
    selected = reduced.denominator if external else raw.denominator
    role = (
        PolynomialRole.REDUCED_TRANSFER_DENOMINATOR
        if external
        else PolynomialRole.RAW_CLOSED_LOOP_CHARACTERISTIC
    )
    value = CharacteristicPolynomialInput(
        selected.expression,
        variable,
        parameters,
        (),
        assumptions,
        (),
        role,
        draft.analysis_target,
        SourceProvenance(
            "Rationalfunktionspipeline",
            draft.provenance_note.strip(),
            "Vollständige Führungsübertragungsfunktion",
        ),
        cancellation,
    )
    analysis = _analyze(value, draft.method)
    steps = (
        _hurwitz_transfer_steps(
            source_text,
            raw,
            reduced,
            factors,
            external,
            selected.expression,
            analysis,
        )
        if isinstance(analysis, HurwitzAnalysisResult)
        else _transfer_steps(
            source_text, raw, reduced, factors, external, selected.expression
        )
    )
    latex = _transfer_latex(
        raw, reduced, factors, external, selected.expression, analysis
    )
    return StabilityWorkflowResult(
        analysis,
        source_steps=steps,
        latex_preamble=latex,
        transfer_preparation=preparation,
    )


def _analyze(
    value: CharacteristicPolynomialInput, method: StabilityMethod
) -> HurwitzAnalysisResult | RouthAnalysisResult:
    canonical = canonicalize_characteristic_polynomial(value)
    return (
        analyze_hurwitz(canonical)
        if method is StabilityMethod.HURWITZ
        else analyze_routh(canonical)
    )


def format_stability_expression(value: object) -> str:
    """Render an exact rational Routh entry without leaking CAS work into UI."""
    if type(value) is not ExactExpression:
        raise TypeError("value must be ExactExpression.")
    numerator, denominator = value._as_sympy().as_numer_denom()
    if denominator != 1:
        return f"({str(sp.expand(numerator)).replace(' ', '')})/{denominator}"
    return value.canonical_text


def format_stability_region(value: object, parameters: tuple[str, ...]) -> str:
    """Project one exact region into the normal user-facing representation."""
    from klausurbotpro.domain.parameter_core_contracts import ParameterRegion

    if type(value) is not ParameterRegion:
        raise TypeError("value must be ParameterRegion.")
    return format_parameter_region_plain(value, parameters)


def _cancellation_note(
    factors: tuple[ExactExpression, ...], was_reduced: bool
) -> str:
    if factors:
        return "Entfernte gemeinsame Faktoren: " + ", ".join(
            item.canonical_text for item in factors
        )
    return "Algebraisch reduziert." if was_reduced else "Keine gemeinsamen Faktoren entfernt."


def _transfer_steps(
    source_text: str,
    raw: object,
    reduced: object,
    factors: tuple[ExactExpression, ...],
    external: bool,
    selected: ExactExpression,
) -> tuple[tuple[str, str], ...]:
    from klausurbotpro.domain.raw_transfer_function import RawTransferFunction
    from klausurbotpro.domain.reduced_transfer_function import ReducedTransferFunction

    assert isinstance(raw, RawTransferFunction)
    assert isinstance(reduced, ReducedTransferFunction)
    factor_text = ", ".join(item.canonical_text for item in factors) or "keine"
    target = "E/A-asymptotische Stabilität" if external else "Interne asymptotische Stabilität"
    selection = "reduzierter Nenner" if external else "roher Nenner"
    return (
        ("1. Eingegebene Führungsübertragungsfunktion", " ".join(source_text.split())),
        ("2. Roher Zähler", raw.numerator.expression.canonical_text),
        ("3. Roher Nenner", raw.denominator.expression.canonical_text),
        ("4. Erkannte gemeinsame Faktoren", factor_text),
        ("5. Reduzierte Führungsübertragungsfunktion", _fraction_text(reduced)),
        ("6. Gewähltes Analyseziel", target),
        ("7. Auswahl des Analyseobjekts", f"{selection}: {selected.canonical_text}"),
    )


def _hurwitz_transfer_steps(
    source_text: str,
    raw: object,
    reduced: object,
    factors: tuple[ExactExpression, ...],
    external: bool,
    selected: ExactExpression,
    analysis: HurwitzAnalysisResult,
) -> tuple[tuple[str, str], ...]:
    from klausurbotpro.domain.raw_transfer_function import RawTransferFunction
    from klausurbotpro.domain.reduced_transfer_function import ReducedTransferFunction

    assert isinstance(raw, RawTransferFunction)
    assert isinstance(reduced, ReducedTransferFunction)
    factor_text = ", ".join(item.canonical_text for item in factors) or "keine"
    target = "E/A-asymptotische Stabilität" if external else "Interne asymptotische Stabilität"
    assumptions = ", ".join(
        item.label for item in analysis.canonical_polynomial.input.assumptions
    ) or "keine zusätzlichen Parameterannahmen"
    prefix = (
        (
            "Gegeben – Eingegebene Führungsübertragungsfunktion",
            f"G_W(s)={_fraction_text_raw(raw)}",
        ),
        ("Gesucht", target),
        ("Methode und Stabilitätsbegriff", f"Hurwitz-Kriterium; {target}"),
        (
            "Voraussetzungen und Annahmen",
            f"{assumptions}; der Leitkoeffizient wird sicher positiv orientiert.",
        ),
        (
            "Charakteristisches Polynom",
            f"N_{'red' if external else 'roh'}(s)={selected.canonical_text}; "
            f"analysiert wird der {'reduzierte E/A-Nenner' if external else 'roher Nenner'}, "
            f"weil das Analyseziel {target} lautet.",
        ),
        (
            "Kursnotation Z(s) und N(s)",
            "Z(s) bezeichnet den Zähler, N(s) den Nenner. "
            f"Z_roh(s)={raw.numerator.expression.canonical_text}; "
            f"N_roh(s)={raw.denominator.expression.canonical_text}; "
            f"Z_red(s)={reduced.numerator.expression.canonical_text}; "
            f"N_red(s)={reduced.denominator.expression.canonical_text}.",
        ),
        ("Kürzungsprotokoll", f"Entfernte gemeinsame Faktoren: {factor_text}."),
    )
    remainder = tuple(
        step for step in analysis.worked_steps if step[0] != "Charakteristisches Polynom"
    )
    return (*prefix, *remainder)


def _fraction_text_raw(value: object) -> str:
    from klausurbotpro.domain.raw_transfer_function import RawTransferFunction

    assert isinstance(value, RawTransferFunction)
    return (
        f"({value.numerator.expression.canonical_text}) / "
        f"({value.denominator.expression.canonical_text})"
    )


def _fraction_text(value: object) -> str:
    from klausurbotpro.domain.reduced_transfer_function import ReducedTransferFunction

    assert isinstance(value, ReducedTransferFunction)
    return (
        f"({value.numerator.expression.canonical_text}) / "
        f"({value.denominator.expression.canonical_text})"
    )


def _transfer_latex(
    raw: object,
    reduced: object,
    factors: tuple[ExactExpression, ...],
    external: bool,
    selected: ExactExpression,
    analysis: HurwitzAnalysisResult | RouthAnalysisResult,
) -> str:
    from klausurbotpro.domain.raw_transfer_function import RawTransferFunction
    from klausurbotpro.domain.reduced_transfer_function import ReducedTransferFunction

    assert isinstance(raw, RawTransferFunction)
    assert isinstance(reduced, ReducedTransferFunction)
    raw_num = raw.numerator.expression
    raw_den = raw.denominator.expression
    reduced_num = reduced.numerator.expression
    reduced_den = reduced.denominator.expression
    factored_num = ExactExpression._from_sympy(sp.factor(raw_num._as_sympy()))
    factored_den = ExactExpression._from_sympy(sp.factor(raw_den._as_sympy()))
    factored_reduced_num = ExactExpression._from_sympy(sp.factor(reduced_num._as_sympy()))
    factored_reduced_den = ExactExpression._from_sympy(sp.factor(reduced_den._as_sympy()))
    factor_latex = r",\;".join(item.latex for item in factors) or r"\mathrm{keine}"
    target = (
        "E/A-asymptotische Stabilität; analysiert wird der reduzierte Nenner."
        if external
        else "Interne asymptotische Stabilität; analysiert wird der rohe Nenner."
    )
    blocks: tuple[str, ...]
    if isinstance(analysis, HurwitzAnalysisResult):
        assumptions = ", ".join(
            item.label for item in analysis.canonical_polynomial.input.assumptions
        ) or "keine zusätzlichen Parameterannahmen"
        selected_name = r"N_{\mathrm{red}}(s)" if external else r"N_{\mathrm{roh}}(s)"
        blocks = (
            paragraph("Gegeben", "Führungsübertragungsfunktion in Kursnotation:"),
            latex_additive_equation(r"Z_{\mathrm{roh}}(s)", factored_num),
            latex_additive_equation(r"N_{\mathrm{roh}}(s)", factored_den),
            display_math(
                r"G_W(s)=\frac{Z_{\mathrm{roh}}(s)}{N_{\mathrm{roh}}(s)}"
            ),
            paragraph("Gesucht", target),
            paragraph("Methode", f"Hurwitz-Kriterium für {target}."),
            paragraph(
                "Voraussetzungen",
                "Der Leitkoeffizient wird sicher positiv orientiert; "
                f"{assumptions}.",
            ),
            paragraph("Charakteristisches Polynom", "Analysiert wird:"),
            latex_additive_equation(selected_name, selected, variable=raw.variable_name),
            latex_additive_equation("p(s)", selected, variable=raw.variable_name),
            paragraph(
                "Kursnotation",
                "Z(s) bezeichnet den Zähler und N(s) den Nenner. "
                "Zähler und Nenner werden zur besseren Lesbarkeit getrennt dargestellt.",
            ),
            paragraph(
                "Bezeichnungsabgrenzung",
                "Die missverständliche ältere N(s)/D(s)-Darstellung wird nicht verwendet.",
            ),
            paragraph("Kürzung", "Entfernte gemeinsame Faktoren:"),
            display_math(factor_latex),
            latex_additive_equation(r"Z_{\mathrm{red}}(s)", factored_reduced_num),
            latex_additive_equation(r"N_{\mathrm{red}}(s)", factored_reduced_den),
            display_math(
                r"G_W^{\mathrm{red}}(s)="
                r"\frac{Z_{\mathrm{red}}(s)}{N_{\mathrm{red}}(s)}"
            ),
        )
    else:
        blocks = (
            paragraph("Gegeben", "Führungsübertragungsfunktion:"),
            latex_transfer_function(
                raw_num,
                raw_den,
                symbol="G_w(s)",
                variable=raw.variable_name,
            ),
            paragraph("Zählerfaktorisierung", "Exakte algebraische Form:"),
            latex_additive_equation("N(s)", factored_num),
            paragraph("Kürzung", "Entfernte gemeinsame Faktoren:"),
            display_math(factor_latex),
            paragraph("Reduzierte Führungsübertragungsfunktion", "Nach der Kürzung:"),
            latex_transfer_function(
                reduced_num,
                reduced_den,
                symbol=r"G_{w,\mathrm{red}}(s)",
                component_subscript="red",
                variable=raw.variable_name,
            ),
            paragraph("Gesucht", target),
            paragraph("Analyseobjekt", "Ausgewähltes charakteristisches Polynom:"),
            latex_additive_equation("p(s)", selected, variable=raw.variable_name),
        )
    return "\n\n".join((*blocks, analysis.latex_source))


def _parse_assumptions(
    text: str,
    parameters: tuple[str, ...],
    parser: SafeExpressionParser,
) -> tuple[tuple[AtomicParameterCondition, ...], tuple[str, ...]]:
    result: list[AtomicParameterCondition] = []
    errors: list[str] = []
    for line_number, raw in enumerate(re.split(r"[;\n]+", text), start=1):
        line = raw.strip()
        if not line:
            continue
        parts = _RELATION_PATTERN.split(line)
        if len(parts) not in (3, 5):
            errors.append(f"Annahme {line_number}: Relation nicht unterstützt.")
            continue
        for index in range(0, len(parts) - 2, 2):
            left = parser.parse(parts[index].strip(), "assumptions")
            right = parser.parse(parts[index + 2].strip(), "assumptions")
            if (
                not left.succeeded
                or left.value is None
                or not right.succeeded
                or right.value is None
            ):
                errors.append(f"Annahme {line_number}: Ausdruck ungültig.")
                continue
            expression = sp.expand(left.value._as_sympy() - right.value._as_sympy())
            result.append(
                AtomicParameterCondition(
                    ExactExpression._from_sympy(expression),
                    _RELATIONS[parts[index + 1]],
                    ConditionOrigin.USER_ASSUMPTION,
                    parameters,
                    line,
                )
            )
    return tuple(result), tuple(errors)


__all__ = [
    "AnalysisTarget",
    "PolynomialRole",
    "StabilityInputMode",
    "StabilityMethod",
    "StabilityInputDraft",
    "StabilityWorkflowResult",
    "format_stability_expression",
    "format_stability_region",
    "run_stability_workflow",
]
