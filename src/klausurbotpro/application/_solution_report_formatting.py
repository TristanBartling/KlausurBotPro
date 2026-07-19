"""Private, non-evaluating formatting helpers for solution reports."""

from __future__ import annotations

from klausurbotpro.application.transfer_function_solution_report_contracts import (
    ReportMathExpression,
    TransferFunctionExpressionPair,
)
from klausurbotpro.domain import (
    ExactExpression,
    ExactRationalValue,
    ExplicitExactRootValue,
    RootOfValue,
)


def exact_expression(value: ExactExpression) -> ReportMathExpression:
    """Copy the two existing exact domain representations."""

    if type(value) is not ExactExpression:
        raise TypeError("value must be an ExactExpression.")
    return ReportMathExpression(value.canonical_text, value.latex)


def exact_rational(value: ExactRationalValue) -> ReportMathExpression:
    """Format an existing reduced rational value without evaluating it."""

    if type(value) is not ExactRationalValue:
        raise TypeError("value must be an ExactRationalValue.")
    if value.denominator == 1:
        text = str(value.numerator)
        return ReportMathExpression(text, text)
    return ReportMathExpression(
        f"{value.numerator}/{value.denominator}",
        rf"\frac{{{value.numerator}}}{{{value.denominator}}}",
    )


def exact_root(
    value: ExplicitExactRootValue | RootOfValue,
    variable_name: str,
) -> ReportMathExpression:
    """Translate an existing exact root value deterministically."""

    if type(value) is ExplicitExactRootValue:
        return exact_expression(value.expression)
    if type(value) is not RootOfValue:
        raise TypeError("value must be a supported exact root.")
    polynomial = _rootof_polynomial(value.defining_coefficients, variable_name)
    latex_polynomial = _rootof_polynomial_latex(
        value.defining_coefficients,
        variable_name,
    )
    return ReportMathExpression(
        f"RootOf({polynomial}, {value.root_index})",
        rf"\mathrm{{RootOf}}\left({latex_polynomial}, "
        rf"{value.root_index}\right)",
    )


def transfer_pair(
    numerator: ExactExpression,
    denominator: ExactExpression,
) -> TransferFunctionExpressionPair:
    """Copy an existing exact numerator/denominator pair."""

    return TransferFunctionExpressionPair(
        exact_expression(numerator),
        exact_expression(denominator),
    )


def fraction(
    pair: TransferFunctionExpressionPair,
) -> ReportMathExpression:
    """Render an already structured pair as one quotient."""

    return ReportMathExpression(
        f"({pair.numerator.plaintext})/({pair.denominator.plaintext})",
        rf"\frac{{{pair.numerator.latex}}}{{{pair.denominator.latex}}}",
    )


def identifier(value: str) -> ReportMathExpression:
    """Create a safely escaped mathematical identifier."""

    if type(value) is not str or not value:
        raise ValueError("An identifier must be a non-empty exact string.")
    return ReportMathExpression(value, _escape_latex_identifier(value))


def literal_text(value: str) -> ReportMathExpression:
    """Escape user-provided or descriptive text without interpreting it."""

    if type(value) is not str:
        raise TypeError("value must be a string.")
    escaped_plain = _escape_plain_text(value)
    return ReportMathExpression(
        escaped_plain or '""',
        rf"\mathtt{{{_escape_latex_text(escaped_plain)}}}",
    )


def descriptive_math(plaintext: str, latex: str | None = None) -> ReportMathExpression:
    """Create controlled report wording, never user-derived mathematics."""

    if type(plaintext) is not str or not plaintext:
        raise ValueError("plaintext must be a non-empty string.")
    latex_value = (
        rf"\mbox{{{_escape_latex_text(plaintext)}}}"
        if latex is None
        else latex
    )
    return ReportMathExpression(plaintext, latex_value)


def numerical_root_text(real: str, imaginary: str) -> str:
    """Join existing numerical root components without changing precision."""

    if imaginary == "0":
        return real
    sign = "+" if not imaginary.startswith("-") else "-"
    magnitude = imaginary.removeprefix("-")
    return f"{real} {sign} {magnitude}*i"


def _rootof_polynomial(
    coefficients: tuple[int, ...],
    variable_name: str,
) -> str:
    degree = len(coefficients) - 1
    terms: list[str] = []
    for position, coefficient in enumerate(coefficients):
        exponent = degree - position
        if coefficient == 0:
            continue
        magnitude = abs(coefficient)
        if exponent == 0:
            body = str(magnitude)
        elif exponent == 1:
            body = variable_name if magnitude == 1 else f"{magnitude}*{variable_name}"
        else:
            power = f"{variable_name}**{exponent}"
            body = power if magnitude == 1 else f"{magnitude}*{power}"
        if not terms:
            terms.append(body if coefficient > 0 else f"-{body}")
        else:
            terms.append(f"{'+' if coefficient > 0 else '-'} {body}")
    return " ".join(terms)


def _rootof_polynomial_latex(
    coefficients: tuple[int, ...],
    variable_name: str,
) -> str:
    degree = len(coefficients) - 1
    variable = _escape_latex_identifier(variable_name)
    terms: list[str] = []
    for position, coefficient in enumerate(coefficients):
        exponent = degree - position
        if coefficient == 0:
            continue
        magnitude = abs(coefficient)
        if exponent == 0:
            body = str(magnitude)
        elif exponent == 1:
            body = variable if magnitude == 1 else f"{magnitude} {variable}"
        else:
            power = rf"{variable}^{{{exponent}}}"
            body = power if magnitude == 1 else f"{magnitude} {power}"
        if not terms:
            terms.append(body if coefficient > 0 else f"-{body}")
        else:
            terms.append(f"{'+' if coefficient > 0 else '-'} {body}")
    return " ".join(terms)


def _escape_plain_text(value: str) -> str:
    escaped: list[str] = []
    for character in value:
        if character == "\\":
            escaped.append("\\\\")
        elif character == "\n":
            escaped.append("\\n")
        elif character == "\r":
            escaped.append("\\r")
        elif character == "\t":
            escaped.append("\\t")
        elif ord(character) < 32 or ord(character) == 127:
            escaped.append(f"\\u{ord(character):04x}")
        else:
            escaped.append(character)
    return "".join(escaped)


def _escape_latex_identifier(value: str) -> str:
    if value.endswith(")") and "(" in value:
        name, arguments = value[:-1].split("(", 1)
        return (
            f"{_latex_identifier_name(name)}"
            f"({_latex_identifier_name(arguments)})"
        )
    return _latex_identifier_name(value)


def _latex_identifier_name(value: str) -> str:
    if "_" not in value:
        return _escape_latex_text(value)
    base, suffix = value.split("_", 1)
    return (
        f"{_escape_latex_text(base)}"
        rf"_{{\mathrm{{{_escape_latex_text(suffix)}}}}}"
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
    }
    return "".join(replacements.get(character, character) for character in value)


__all__ = [
    "descriptive_math",
    "exact_expression",
    "exact_rational",
    "exact_root",
    "fraction",
    "identifier",
    "literal_text",
    "numerical_root_text",
    "transfer_pair",
]
