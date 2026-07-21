"""Application orchestration and presentation for the time-domain workspace."""

from __future__ import annotations

import re
from dataclasses import dataclass, replace

import sympy as sp

from klausurbotpro.domain.expression import ExactExpression
from klausurbotpro.domain.raw_transfer_function_factory import RawTransferFunctionFactory
from klausurbotpro.domain.time_domain_analyzer import (
    classify_reduction_poles,
    direct_laplace,
    exact,
    inverse_rational,
)
from klausurbotpro.domain.time_domain_contracts import (
    ExponentialInputSignal,
    PoleRole,
    TimeDomainSolution,
    TimeDomainTaskType,
    TimeFunction,
)
from klausurbotpro.domain.transfer_function_reducer import TransferFunctionReducer
from klausurbotpro.domain.transfer_function_reduction_contracts import (
    TransferFunctionReductionResult,
)
from klausurbotpro.parsing import (
    ParserConfig,
    ParserProfile,
    SafeExpressionParser,
    SafeRationalExpressionParser,
)

_IDENTIFIER = re.compile(r"\b[A-Za-z_]\w*\b")
_RESERVED = frozenset({"s", "t", "pi", "exp", "sin", "cos"})


@dataclass(frozen=True, slots=True)
class TimeDomainInputDraft:
    task_type: TimeDomainTaskType
    time_expression_text: str = ""
    image_expression_text: str = ""
    system_expression_text: str = ""
    input_expression_text: str = ""
    step_amplitude_text: str = "1"
    exponential_amplitude_text: str = "1"
    exponential_exponent_text: str = "0"
    assumptions_text: str = ""


@dataclass(frozen=True, slots=True)
class TimeDomainPresentation:
    summary: str
    rational_analysis: str
    partial_fractions: str
    time_function: str
    verifications: str
    short_solution: str
    worked_steps: str
    latex_source: str
    diagnostics: str


@dataclass(frozen=True, slots=True)
class TimeDomainWorkflowResult:
    solution: TimeDomainSolution | None
    presentation: TimeDomainPresentation
    errors: tuple[str, ...] = ()


def run_time_domain_workflow(draft: TimeDomainInputDraft) -> TimeDomainWorkflowResult:
    """Run one complete visible workflow without allowing UI-side mathematics."""
    try:
        solution = _compute(draft)
    except (TypeError, ValueError, ArithmeticError) as error:
        message = str(error) or "Die Eingabe konnte nicht verarbeitet werden."
        return TimeDomainWorkflowResult(None, _error_presentation(message), (message,))
    return TimeDomainWorkflowResult(solution, _present(solution))


def _compute(draft: TimeDomainInputDraft) -> TimeDomainSolution:
    if type(draft.task_type) is not TimeDomainTaskType:
        raise TypeError("Der Aufgabentyp ist ungültig.")
    if draft.task_type is TimeDomainTaskType.DIRECT_LAPLACE:
        source = _parse_time(draft.time_expression_text)
        return direct_laplace(source)
    if draft.task_type is TimeDomainTaskType.INVERSE_LAPLACE:
        reduction = _parse_reduction(draft.image_expression_text)
        source = _reduced_expression(reduction)
        return inverse_rational(
            reduction,
            task_type=draft.task_type,
            source_expression=source,
        )
    system_reduction = _parse_reduction(draft.system_expression_text)
    system = _reduced_expression(system_reduction)
    if draft.task_type is TimeDomainTaskType.STEP_RESPONSE:
        amplitude = _parse_coefficient(draft.step_amplitude_text)
        input_expression = exact(amplitude._as_sympy() / sp.Symbol("s"))
        input_reduction = _parse_reduction(input_expression.canonical_text)
    elif draft.task_type is TimeDomainTaskType.GENERAL_RESPONSE:
        input_reduction = _parse_reduction(draft.input_expression_text)
        input_expression = _reduced_expression(input_reduction)
    elif draft.task_type is TimeDomainTaskType.EXPONENTIAL_INPUT:
        amplitude = _parse_coefficient(draft.exponential_amplitude_text)
        exponent = _parse_coefficient(draft.exponential_exponent_text)
        input_expression = exact(
            amplitude._as_sympy() / (sp.Symbol("s") - exponent._as_sympy())
        )
        input_reduction = _parse_reduction(input_expression.canonical_text)
    else:
        raise ValueError("Der gewählte Aufgabentyp wird nicht unterstützt.")
    output_text = (
        f"({system.canonical_text})*({input_expression.canonical_text})"
    )
    output_reduction = _parse_reduction(output_text)
    solution = inverse_rational(
        output_reduction,
        task_type=draft.task_type,
        input_laplace=input_expression,
        system_laplace=system,
        system_poles=classify_reduction_poles(
            system_reduction, PoleRole.SYSTEM
        ),
        input_poles=classify_reduction_poles(input_reduction, PoleRole.INPUT),
        calculate_end_value=True,
    )
    if draft.task_type is TimeDomainTaskType.EXPONENTIAL_INPUT:
        input_time = exact(
            amplitude._as_sympy()
            * sp.exp(exponent._as_sympy() * sp.Symbol("t"))
        )
        return replace(
            solution,
            input_signal=ExponentialInputSignal(
                amplitude,
                exponent,
                TimeFunction(input_time),
                input_expression,
            ),
        )
    return solution


def _parse_time(text: str) -> ExactExpression:
    _reject_mixed_variables(text, expected="t")
    parameters = _parameter_names(text)
    parser = SafeExpressionParser(
        ParserConfig.for_profile(ParserProfile.TIME_T, parameter_names=parameters)
    )
    result = parser.parse(text, "f(t)")
    if result.value is None:
        raise ValueError("\n".join(item.message for item in result.diagnostics))
    return result.value


def _parse_coefficient(text: str) -> ExactExpression:
    _reject_mixed_variables(text, expected=None)
    parameters = _parameter_names(text)
    parser = SafeExpressionParser(
        ParserConfig(
            allowed_symbols=parameters,
            exact_constants=frozenset({"pi"}),
        )
    )
    result = parser.parse(text, "coefficient")
    if result.value is None:
        raise ValueError("\n".join(item.message for item in result.diagnostics))
    return result.value


def _parse_reduction(text: str) -> TransferFunctionReductionResult:
    _reject_mixed_variables(text, expected="s")
    parameters = _parameter_names(text)
    allowed = frozenset(("s", "pi", *parameters))
    parsed = SafeRationalExpressionParser(
        ParserConfig(allowed_symbols=allowed)
    ).parse_common(text, variable_name="s", field="image")
    if parsed.value is None:
        raise ValueError("\n".join(item.message for item in parsed.diagnostics))
    created = RawTransferFunctionFactory(
        expected_variable_name="s",
        allowed_parameter_names=frozenset(("pi", *parameters)),
    ).create(parsed.value, field="image")
    if created.value is None:
        raise ValueError("\n".join(item.message for item in created.diagnostics))
    return TransferFunctionReducer().reduce(created.value, field="image")


def _reduced_expression(reduction: TransferFunctionReductionResult) -> ExactExpression:
    if reduction.reduced is None:
        raise ValueError("Die rationale Reduktion ist fehlgeschlagen.")
    return exact(
        (
            reduction.reduced.numerator.expression._as_sympy()
            / reduction.reduced.denominator.expression._as_sympy()
        ).subs({sp.Symbol("pi"): sp.pi})
    )


def _parameter_names(text: str) -> frozenset[str]:
    return frozenset(_IDENTIFIER.findall(text)) - _RESERVED


def _reject_mixed_variables(text: str, *, expected: str | None) -> None:
    names = frozenset(_IDENTIFIER.findall(text))
    forbidden = {"s", "t"} - ({expected} if expected is not None else set())
    if names & forbidden:
        raise ValueError("Gemischte Verwendung von s und t ist nicht erlaubt.")


def _present(solution: TimeDomainSolution) -> TimeDomainPresentation:
    summary_lines = [
        f"Aufgabentyp: {solution.task_type.value}",
        f"Status: {solution.status.value}",
    ]
    if solution.output_laplace is not None:
        summary_lines.append(f"Bildfunktion: {solution.output_laplace.canonical_text}")
    if solution.input_signal is not None:
        summary_lines.append(
            "Exponentialeingang: u(t)="
            f"{solution.input_signal.time_function.expression.canonical_text}; "
            f"U(s)={solution.input_signal.laplace_expression.canonical_text}"
        )
    if solution.time_function is not None:
        summary_lines.append(
            f"Zeitfunktion: {solution.time_function.expression.canonical_text}"
        )
    if solution.verification.end_value is not None:
        summary_lines.append(
            f"Stationärer Endwert: {solution.verification.end_value.canonical_text}"
        )
    elif solution.verification.end_value_status.value != "NOT_APPLICABLE":
        summary_lines.append(
            f"Endwertstatus: {solution.verification.end_value_status.value}"
        )
    rational_text = _rational_text(solution)
    partial_text = _partial_text(solution)
    time_text = (
        solution.time_function.expression.canonical_text
        if solution.time_function is not None
        else "Keine gewöhnliche Zeitfunktion verfügbar."
    )
    checks = "\n".join(
        f"{item.check_id}: {item.status.value} – {item.explanation}"
        for item in solution.verification.items
    )
    if solution.verification.initial_value is not None:
        checks += f"\nAnfangswert: {solution.verification.initial_value.canonical_text}"
    checks += f"\nEndwertsatz: {solution.verification.end_value_status.value}"
    diagnostics = "\n".join(
        f"{item.severity.value.upper()} {item.code.value}: {item.message}"
        for item in solution.diagnostics
    )
    steps = _worked_steps(solution)
    latex = _latex(solution, steps)
    short_lines = list(summary_lines[-3:])
    if solution.time_function is not None:
        numeric = sp.N(
            solution.time_function.expression._as_sympy().subs(sp.Symbol("t"), 1),
            8,
        )
        short_lines.append(f"Numerische Kontrolle y(1) ≈ {numeric}")
    short = "\n".join(short_lines)
    return TimeDomainPresentation(
        "\n".join(summary_lines),
        rational_text,
        partial_text,
        time_text,
        checks.strip(),
        short,
        steps,
        latex,
        diagnostics,
    )


def _rational_text(solution: TimeDomainSolution) -> str:
    analysis = solution.rational_analysis
    if analysis is None:
        return "Für diesen Workflow nicht erforderlich."
    division = analysis.division
    lines = [
        f"Rohform: {analysis.raw_expression.canonical_text}",
        f"Reduzierte Form: {analysis.reduced_expression.canonical_text}",
        f"Grad Z/N: {analysis.classification.numerator_degree}/"
        f"{analysis.classification.denominator_degree}",
        f"Klassifikation: {analysis.classification.kind.value}",
        f"Polynomquotient: {division.quotient.canonical_text}",
        f"Restbruch: {division.proper_fraction.canonical_text}",
        f"Rekonstruktionsresiduum: {division.reconstruction_residual.canonical_text}",
    ]
    if analysis.cancellation_factors:
        lines.append(
            "Gekürzte Faktoren: "
            + ", ".join(item.canonical_text for item in analysis.cancellation_factors)
        )
    if solution.factor_structure is not None:
        lines.append(
            "Faktorstruktur: "
            + " * ".join(
                f"({item.factor.canonical_text})^{item.multiplicity}"
                for item in solution.factor_structure.factors
            )
        )
    return "\n".join(lines)


def _partial_text(solution: TimeDomainSolution) -> str:
    partial = solution.partial_fractions
    if partial is None:
        return "Keine Partialbruchzerlegung verfügbar."
    lines = [f"Vollständiger Ansatz: {partial.ansatz}"]
    lines.extend(
        f"{term.factor_id}, Potenz {term.power}: "
        f"Zähler={term.numerator.canonical_text}; "
        f"Koeffizienten={', '.join(value.canonical_text for value in term.coefficients)}"
        for term in partial.terms
    )
    lines.extend(
        (
            "PBZ-Ergebnis: "
            + " + ".join(
                f"({term.numerator.canonical_text})/"
                f"({term.factor.canonical_text})^{term.power}"
                for term in partial.terms
            ),
            f"Rückzusammenfassung: {partial.reconstruction_residual.canonical_text}",
        )
    )
    return "\n".join(lines)


def _worked_steps(solution: TimeDomainSolution) -> str:
    values: list[tuple[str, str]] = [
        ("1. Eingabe und Aufgabentyp", solution.task_type.value),
    ]
    if solution.output_laplace is not None:
        values.append(("2. Bildung der Bildfunktion", solution.output_laplace.canonical_text))
    if solution.rational_analysis is not None:
        analysis = solution.rational_analysis
        values.extend(
            (
                (
                    "3. Roh- und Reduktionsform",
                    f"{analysis.raw_expression.canonical_text} -> "
                    f"{analysis.reduced_expression.canonical_text}",
                ),
                (
                    "4. Klassifikation und Polynomdivision",
                    f"{analysis.classification.kind.value}; "
                    f"Q={analysis.division.quotient.canonical_text}, "
                    f"R={analysis.division.remainder.canonical_text}",
                ),
            )
        )
    if solution.factor_structure is not None:
        values.append(
            (
                "5. Nennerfaktorisierung",
                " * ".join(
                    item.factor.canonical_text
                    for item in solution.factor_structure.factors
                ),
            )
        )
    if solution.partial_fractions is not None:
        values.extend(
            (
                ("6. Vollständiger PBZ-Ansatz", solution.partial_fractions.ansatz),
                (
                    "7. Koeffizienten",
                    "; ".join(
                        ", ".join(
                            value.canonical_text for value in item.coefficients
                        )
                        for item in solution.partial_fractions.terms
                    ),
                ),
                (
                    "8. PBZ-Ergebnis",
                    " + ".join(
                        f"({item.numerator.canonical_text})/"
                        f"({item.factor.canonical_text})^{item.power}"
                        for item in solution.partial_fractions.terms
                    ),
                ),
            )
        )
    if solution.inverse_mappings:
        values.append(
            (
                "9. Inverse Termabbildung",
                "; ".join(item.explanation for item in solution.inverse_mappings),
            )
        )
    elif solution.direct_rules:
        values.append(
            (
                "9. Verwendete Tabellenpaare",
                "; ".join(item.table_pair for item in solution.direct_rules),
            )
        )
    time_text = (
        solution.time_function.expression.canonical_text
        if solution.time_function
        else "nicht verfügbar"
    )
    values.append(("10. Zeitfunktion", time_text))
    values.append(
        (
            "11. Symbolische Kontrollen",
            "; ".join(
                f"{item.check_id}={item.status.value}"
                for item in solution.verification.items
            ),
        )
    )
    pole_text = ", ".join(
        f"{item.role.value}:{item.value.canonical_text}:{item.half_plane.value}"
        for item in solution.poles
    )
    values.append(
        (
            "12. Anfangs-/Endwert- und Polhinweise",
            f"Endwertstatus={solution.verification.end_value_status.value}; "
            f"Pole={pole_text}",
        )
    )
    values.append(("13. Endaussage", solution.status.value))
    return "\n\n".join(f"{title}\n{value}" for title, value in values)


def _latex(solution: TimeDomainSolution, steps: str) -> str:
    problem = solution.source_expression or solution.system_laplace or solution.output_laplace
    result = (
        solution.time_function.expression.latex
        if solution.time_function is not None
        else r"\text{keine gewöhnliche Zeitfunktion}"
    )
    del steps
    items: list[str] = [
        rf"\item \text{{Aufgabentyp: {_latex_escape(solution.task_type.value)}}}"
    ]
    if solution.direct_rules:
        rules = r"\\".join(
            rf"\mathcal{{L}}\{{{item.source_term.latex}\}}"
            rf"={item.image_term.latex}\quad"
            rf"\text{{({_latex_escape(item.table_pair)})}}"
            for item in solution.direct_rules
        )
        items.append(rf"\item \text{{Tabellenpaare und Dämpfung: }}\[{rules}\]")
    if solution.input_laplace is not None:
        items.append(rf"\item \[U(s)={solution.input_laplace.latex}\]")
    if solution.output_laplace is not None:
        items.append(rf"\item \[Y(s)={solution.output_laplace.latex}\]")
    if solution.rational_analysis is not None:
        analysis = solution.rational_analysis
        items.append(
            rf"\item \[F_{{\mathrm{{roh}}}}(s)={analysis.raw_expression.latex},"
            rf"\qquad F_{{\mathrm{{red}}}}(s)={analysis.reduced_expression.latex}\]"
        )
        division = analysis.division
        items.append(
            rf"\item \text{{Polynomdivision ({analysis.classification.kind.value}): }}"
            rf"\[{division.dividend.latex}=({division.quotient.latex})"
            rf"({division.divisor.latex})+{division.remainder.latex}\]"
        )
    if solution.factor_structure is not None:
        factors = " ".join(
            rf"\left({item.factor.latex}\right)^{{{item.multiplicity}}}"
            for item in solution.factor_structure.factors
        )
        items.append(rf"\item \text{{Faktorstruktur: }}\[{factors}\]")
    if solution.partial_fractions is not None:
        partial = solution.partial_fractions
        items.append(
            rf"\item \text{{Vollständiger PBZ-Ansatz: }}"
            rf"\texttt{{{_latex_escape(partial.ansatz)}}}"
        )
        coefficient_lines = r",\;".join(
            value.latex
            for item in partial.terms
            for value in item.coefficients
        )
        items.append(rf"\item \text{{Exakte Koeffizienten: }}\[{coefficient_lines}\]")
        decomposition = "+".join(
            rf"\frac{{{item.numerator.latex}}}"
            rf"{{\left({item.factor.latex}\right)^{{{item.power}}}}}"
            for item in partial.terms
        )
        items.append(rf"\item \text{{PBZ-Ergebnis: }}\[{decomposition}\]")
    if solution.inverse_mappings:
        mappings = r"\\".join(
            rf"\mathcal{{L}}^{{-1}}\!\left\{{{item.image_term.latex}\right\}}"
            rf"={item.time_term.latex}"
            for item in solution.inverse_mappings
        )
        items.append(rf"\item \text{{Inverse Termabbildungen: }}\[{mappings}\]")
    check_lines = r"\\".join(
        rf"\text{{{_latex_escape(item.check_id)}: {item.status.value}}}"
        for item in solution.verification.items
    )
    items.append(rf"\item \text{{Symbolische Kontrollen: }}\[{check_lines}\]")
    body = "\n".join(items)
    warnings = "\\\n".join(
        rf"\text{{{_latex_escape(item.code.value)}: {_latex_escape(item.message)}}}"
        for item in solution.diagnostics
    ) or r"\text{keine}"
    problem_latex = problem.latex if problem is not None else r"\text{Eingabe}"
    return (
        r"\section*{Zeitbereichslösung}" "\n"
        rf"\textbf{{Problem: }} ${problem_latex}$" "\n"
        r"\begin{enumerate}" "\n" + body + "\n" + r"\end{enumerate}" "\n"
        r"\textbf{Kontrollen: }"
        + _latex_escape(solution.verification.end_value_status.value)
        + r"\\"
        "\n"
        r"\textbf{Warnungen: }" + warnings + "\n"
        rf"\[\boxed{{{result}}}\]"
    )


def _latex_escape(text: str) -> str:
    return text.replace("_", r"\_").replace("%", r"\%")


def _error_presentation(message: str) -> TimeDomainPresentation:
    return TimeDomainPresentation(
        "Eingabe ungültig.", "", "", "", "", "", "", "", message
    )


__all__ = [
    "TimeDomainInputDraft",
    "TimeDomainPresentation",
    "TimeDomainWorkflowResult",
    "run_time_domain_workflow",
]
