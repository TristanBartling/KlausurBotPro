"""Presentation-only helpers for readable stability text and LaTeX."""

from __future__ import annotations

import re

import sympy as sp

from klausurbotpro.domain.expression import ExactExpression
from klausurbotpro.domain.parameter_core_contracts import ParameterRegion
from klausurbotpro.domain.stability_contracts import NumericalPoleCheck

_PLAIN_INFINITY = re.compile(
    r"^(?:[A-Za-z_]\w*\s*(?:<|<=)\s*oo|-oo\s*(?:<|<=)\s*[A-Za-z_]\w*)$"
)
_LATEX_INFINITY = re.compile(
    r"^(?:[A-Za-z_{}]+\s*(?:<|\\leq?)\s*\\infty|"
    r"-\s*\\infty\s*(?:<|\\leq?)\s*[A-Za-z_{}]+)$"
)
_RATIONAL = re.compile(r"^(-?)(\d+)/(\d+)$")


def format_parameter_region_plain(
    region: ParameterRegion,
    parameters: tuple[str, ...],
) -> str:
    """Hide only trivial infinite bounds and render conjunctions for people."""
    if region.exact_text in ("wahr", "falsch", "∅"):
        return region.exact_text
    parts = _plain_parts(region.exact_text)
    parts = _combine_plain_bounds(parts, parameters)
    return " und ".join(_compact_plain(item) for item in parts) or region.exact_text


def latex_parameter_region(
    region: ParameterRegion,
    parameters: tuple[str, ...],
    *,
    boxed: bool = False,
) -> str:
    """Render a solved region as a short equation or a multiline alignment."""
    parts = _latex_parts(region.latex)
    parts = _combine_latex_bounds(parts, parameters)
    if not parts:
        parts = (region.latex,)
    body = _aligned_relations(parts)
    if boxed:
        body = r"\boxed{" + body + "}"
    return display_math(body)


def latex_additive_equation(
    lhs: str,
    expression: ExactExpression,
    *,
    terms_per_line: int = 2,
    variable: str | None = None,
) -> str:
    """Render an exact additive expression without changing its value."""
    terms = _ordered_terms(expression, variable)
    if len(terms) <= terms_per_line:
        return display_math(lhs + "=" + expression.latex)
    chunks = tuple(
        terms[index : index + terms_per_line]
        for index in range(0, len(terms), terms_per_line)
    )
    lines: list[str] = []
    for index, chunk in enumerate(chunks):
        rendered = _signed_terms(chunk, first=index == 0)
        lines.append((lhs + "={}&" if index == 0 else r"&\quad{}") + rendered)
    return display_math(r"\begin{aligned}" + r"\\".join(lines) + r"\end{aligned}")


def latex_conditions(expressions: tuple[ExactExpression, ...]) -> str:
    """Render stability conditions vertically when more than one exists."""
    groups: list[str] = []
    for expression in expressions:
        terms = _ordered_terms(expression, None)
        if len(expression.latex) <= 85 or len(terms) == 1:
            groups.append(expression.latex + " &> 0")
            continue
        chunks = tuple(
            terms[index : index + 2] for index in range(0, len(terms), 2)
        )
        condition_lines: list[str] = []
        for index, chunk in enumerate(chunks):
            line = ("{}&" if index == 0 else r"&\quad{}") + _signed_terms(
                chunk, first=index == 0
            )
            if index == len(chunks) - 1:
                line += " > 0"
            condition_lines.append(line)
        groups.append(r"\\".join(condition_lines))
    return display_math(r"\begin{aligned}" + r",\\".join(groups) + r"\end{aligned}")


def latex_numerical_check(check: NumericalPoleCheck | None) -> str:
    """Render the actual control point and poles in separate readable lines."""
    if check is None:
        return paragraph("Numerische Kontrolle", "Nicht verfügbar.")
    status = {
        "consistent": "Das symbolische Ergebnis ist konsistent.",
        "inconsistent": "Das symbolische Ergebnis ist widersprüchlich.",
        "numerically_inconclusive": "Die numerische Kontrolle ist nicht entscheidbar.",
    }.get(check.status.value, "Die numerische Kontrolle ist nicht entscheidbar.")
    point = ""
    if check.parameter_point:
        assignments = " und ".join(
            rf"\({latex_identifier(name)}={latex_scalar(value)}\)"
            for name, value in check.parameter_point
        )
        point = f" Für den Kontrollpunkt {assignments} gilt:"
    text = r"\par\noindent" + "\n" + r"\textbf{Numerische Kontrolle.}" + "\n"
    if point:
        text += point.strip() + " " + status
    else:
        text += status
    if not check.poles:
        return text
    pole_lines = tuple(
        rf"s_{{{index}}} &\approx {_latex_pole(pole)}"
        for index, pole in enumerate(check.poles, 1)
    )
    return text + "\n\n" + display_math(_aligned_relations(pole_lines))


def latex_transfer_function(
    numerator: ExactExpression,
    denominator: ExactExpression,
    *,
    symbol: str,
    force_components: bool = False,
    component_subscript: str = "",
    variable: str = "s",
) -> str:
    """Render a rational function directly or through explained N/D components."""
    direct = rf"{symbol}=\frac{{{numerator.latex}}}{{{denominator.latex}}}"
    if not force_components and len(direct) <= 80:
        return display_math(r"\begin{aligned}" + direct + r"\end{aligned}")
    intro = paragraph(
        "Darstellung",
        "Zähler und Nenner werden zur besseren Lesbarkeit getrennt dargestellt.",
    )
    tag = rf"_{{\mathrm{{{component_subscript}}}}}" if component_subscript else ""
    numerator_symbol = rf"N{tag}(s)"
    denominator_symbol = rf"D{tag}(s)"
    equations = (
        latex_additive_equation(numerator_symbol, numerator, variable=variable),
        latex_additive_equation(denominator_symbol, denominator, variable=variable),
        display_math(rf"{symbol}=\frac{{{numerator_symbol}}}{{{denominator_symbol}}}"),
    )
    return intro + "\n\n" + "\n\n".join(equations)


def paragraph(title: str, text: str) -> str:
    """Return ordinary, line-breakable LaTeX prose."""
    return (
        r"\par\noindent" + "\n" + rf"\textbf{{{escape_latex_text(title)}.}}" + "\n"
        + escape_latex_text(text)
    )


def display_math(body: str) -> str:
    return "\\[\n" + body + "\n\\]"


def escape_latex_text(value: str) -> str:
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


def latex_identifier(value: str) -> str:
    if "_" not in value:
        return value
    base, suffix = value.split("_", 1)
    return rf"{base}_{{{suffix}}}"


def latex_scalar(value: str) -> str:
    match = _RATIONAL.fullmatch(value.strip())
    if match is None:
        return value.replace("*", r"\,")
    sign, numerator, denominator = match.groups()
    return sign + rf"\frac{{{numerator}}}{{{denominator}}}"


def _plain_parts(text: str) -> tuple[str, ...]:
    parts = tuple(_strip_outer(item.strip()) for item in text.split("&"))
    return tuple(
        _flip_plain(item)
        for item in parts
        if item and not _PLAIN_INFINITY.fullmatch(item)
    )


def _latex_parts(text: str) -> tuple[str, ...]:
    parts = tuple(item.strip() for item in text.split(r"\wedge"))
    return tuple(item for item in parts if item and not _LATEX_INFINITY.fullmatch(item))


def _strip_outer(value: str) -> str:
    while value.startswith("(") and value.endswith(")"):
        value = value[1:-1].strip()
    return value


def _flip_plain(value: str) -> str:
    match = re.fullmatch(r"(.+?)\s*(<|<=)\s*([A-Za-z_]\w*)", value)
    if match is None:
        return value
    left, relation, variable = match.groups()
    return f"{variable} {'>' if relation == '<' else '>='} {left.strip()}"


def _combine_plain_bounds(
    parts: tuple[str, ...], parameters: tuple[str, ...]
) -> tuple[str, ...]:
    if len(parameters) < 2:
        return _combine_same_variable(parts, parameters[0] if parameters else "")
    return _combine_same_variable(parts, parameters[-1])


def _combine_same_variable(parts: tuple[str, ...], variable: str) -> tuple[str, ...]:
    lower = next((item for item in parts if item.startswith(variable + " > ")), None)
    upper = next((item for item in parts if item.startswith(variable + " < ")), None)
    if lower is None or upper is None:
        return parts
    lower_bound = lower.removeprefix(variable + " > ")
    upper_bound = upper.removeprefix(variable + " < ")
    chain = f"{lower_bound} < {variable} < {upper_bound}"
    remaining = tuple(item for item in parts if item not in (lower, upper))
    return (*remaining, chain)


def _combine_latex_bounds(
    parts: tuple[str, ...], parameters: tuple[str, ...]
) -> tuple[str, ...]:
    latex_parameters = tuple(latex_identifier(item) for item in parameters)
    variable = latex_parameters[-1] if latex_parameters else ""
    left_lower = next((item for item in parts if item.endswith(" < " + variable)), None)
    right_lower = next((item for item in parts if item.startswith(variable + " > ")), None)
    upper = next((item for item in parts if item.startswith(variable + " < ")), None)
    lower = left_lower or right_lower
    if lower is None or upper is None:
        return tuple(
            _align_relation(_flip_latex(item, latex_parameters)) for item in parts
        )
    if left_lower is not None:
        lower_bound = left_lower.removesuffix(" < " + variable)
    else:
        assert right_lower is not None
        lower_bound = right_lower.removeprefix(variable + " > ")
    chain = lower_bound + " &< " + variable + " < " + upper.removeprefix(variable + " < ")
    remaining = tuple(
        _align_relation(_flip_latex(item, latex_parameters))
        for item in parts
        if item not in (lower, upper)
    )
    return (*remaining, chain)


def _align_relation(value: str) -> str:
    if "&" in value:
        return value
    for relation in (r"\leq", r"\geq", "<", ">", "="):
        if relation in value:
            return value.replace(relation, "&" + relation, 1)
    return value


def _flip_latex(value: str, parameters: tuple[str, ...]) -> str:
    for variable in parameters:
        suffix = " < " + variable
        if value.endswith(suffix):
            return variable + " &> " + value.removesuffix(suffix)
    return value


def _compact_plain(value: str) -> str:
    return re.sub(r"\s*([+*/])\s*", r"\1", value)


def _aligned_relations(parts: tuple[str, ...]) -> str:
    if len(parts) == 1:
        return parts[0].replace("&", "")
    return r"\begin{aligned}" + r",\\".join(parts) + r"\end{aligned}"


def _signed_terms(terms: tuple[sp.Expr, ...], *, first: bool) -> str:
    rendered: list[str] = []
    for index, term in enumerate(terms):
        negative = term.could_extract_minus_sign()
        body = sp.latex(-term if negative else term)
        prefix = (
            ("-" if negative else "")
            if first and index == 0
            else "-" if negative else "+"
        )
        rendered.append(prefix + body)
    return "".join(rendered)


def _ordered_terms(
    expression: ExactExpression, variable: str | None
) -> tuple[sp.Expr, ...]:
    if variable is None:
        return tuple(expression._as_sympy().as_ordered_terms())
    symbol = sp.Symbol(variable)
    polynomial = sp.Poly(expression._as_sympy(), symbol)
    return tuple(
        coefficient * symbol ** powers[0]
        for powers, coefficient in polynomial.terms()
    )


def _latex_pole(value: str) -> str:
    compact = value.replace(" ", "")
    compact = re.sub(r"\+0(?:\.0+)?j$", "", compact)
    compact = compact.replace("j", r"\,\mathrm{i}")
    return compact


__all__ = [
    "display_math",
    "escape_latex_text",
    "format_parameter_region_plain",
    "latex_additive_equation",
    "latex_conditions",
    "latex_numerical_check",
    "latex_parameter_region",
    "latex_transfer_function",
    "paragraph",
]
