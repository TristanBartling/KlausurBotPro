"""Pure presentation helpers for an existing standard-element result."""

from __future__ import annotations

from klausurbotpro.application._solution_report_formatting import exact_expression
from klausurbotpro.domain import (
    ExactExpression,
    StandardElementBodeResult,
    StandardElementFactor,
    StandardElementFactorKind,
)


def exact_expression_decimal_text(value: ExactExpression) -> str:
    """Format one exact scalar for a plot marker outside the widget layer."""
    if type(value) is not ExactExpression:
        raise TypeError("value must be ExactExpression.")
    return f"{float(value._as_sympy()):.12g}"


def standard_element_decomposition_plain(result: StandardElementBodeResult) -> str:
    _require_supported(result)
    assert result.gain is not None
    exponent = result.origin_zero_multiplicity - result.origin_pole_multiplicity
    numerator = [result.gain.canonical_text]
    denominator: list[str] = []
    if exponent > 0:
        numerator.append(_power("s", exponent))
    elif exponent < 0:
        denominator.append(_power("s", -exponent))
    numerator.extend(_factor_plain(item) for item in result.zero_factors)
    denominator.extend(_factor_plain(item) for item in result.pole_factors)
    expression = " * ".join(numerator)
    if denominator:
        expression = f"({expression}) / ({' * '.join(denominator)})"
    return f"G_red(s) = {expression}"


def standard_element_decomposition_latex(result: StandardElementBodeResult) -> str:
    _require_supported(result)
    assert result.gain is not None
    exponent = result.origin_zero_multiplicity - result.origin_pole_multiplicity
    numerator = [exact_expression(result.gain).latex]
    denominator: list[str] = []
    if exponent > 0:
        numerator.append(_power_latex("s", exponent))
    elif exponent < 0:
        denominator.append(_power_latex("s", -exponent))
    numerator.extend(_factor_latex(item) for item in result.zero_factors)
    denominator.extend(_factor_latex(item) for item in result.pole_factors)
    top = r"\,".join(numerator)
    body = top if not denominator else rf"\frac{{{top}}}{{{r'\,'.join(denominator)}}}"
    return rf"G_{{\mathrm{{red}}}}(s)={body}"


def standard_element_asymptote_plain(result: StandardElementBodeResult) -> str:
    _require_supported(result)
    assert result.gain is not None
    exponent = result.origin_zero_multiplicity - result.origin_pole_multiplicity
    terms = [f"20*log10(abs({result.gain.canonical_text}))"]
    if exponent:
        terms.append(f"{20 * exponent:+d}*log10(omega)")
    terms.extend(_asymptote_term_plain(item, sign=1) for item in result.zero_factors)
    terms.extend(_asymptote_term_plain(item, sign=-1) for item in result.pole_factors)
    return "L_a(omega) = " + " ".join(terms) + ", omega > 0"


def standard_element_asymptote_latex(result: StandardElementBodeResult) -> str:
    _require_supported(result)
    assert result.gain is not None
    exponent = result.origin_zero_multiplicity - result.origin_pole_multiplicity
    gain = exact_expression(result.gain).latex
    terms = [rf"20\log_{{10}}\!\left(\left|{gain}\right|\right)"]
    if exponent:
        terms.append(rf"{_signed(20 * exponent)}\log_{{10}}(\omega)")
    terms.extend(_asymptote_term_latex(item, sign=1) for item in result.zero_factors)
    terms.extend(_asymptote_term_latex(item, sign=-1) for item in result.pole_factors)
    return rf"L_a(\omega)={' '.join(terms)},\qquad \omega>0"


def standard_element_events_plain(result: StandardElementBodeResult) -> str:
    _require_supported(result)
    if not result.corner_events:
        return "keine"
    return "; ".join(
        (
            f"omega_k={event.corner_frequency.canonical_text} rad/s: "
            f"Delta={event.slope_change_db_per_decade:+d} dB/Dekade, "
            f"danach {event.slope_after_db_per_decade:+d} dB/Dekade"
        )
        for event in result.corner_events
    )


def _factor_plain(factor: StandardElementFactor) -> str:
    omega = factor.corner_frequency.canonical_text
    if factor.kind is StandardElementFactorKind.PT2:
        assert factor.damping_ratio is not None
        damping = factor.damping_ratio.canonical_text
        return _power(
            f"(1 + 2*({damping})*s/({omega}) + (s/({omega}))^2)",
            factor.multiplicity,
        )
    return _power(f"(1 + s/({omega}))", factor.multiplicity)


def _factor_latex(factor: StandardElementFactor) -> str:
    omega = exact_expression(factor.corner_frequency).latex
    if factor.kind is StandardElementFactorKind.PT2:
        assert factor.damping_ratio is not None
        damping = exact_expression(factor.damping_ratio).latex
        body = (
            rf"\left(1+2\,{damping}\frac{{s}}{{{omega}}}"
            rf"+\left(\frac{{s}}{{{omega}}}\right)^2\right)"
        )
        return _power_latex(body, factor.multiplicity)
    body = rf"\left(1+\frac{{s}}{{{omega}}}\right)"
    return _power_latex(body, factor.multiplicity)


def _asymptote_term_plain(factor: StandardElementFactor, *, sign: int) -> str:
    order = 2 if factor.kind is StandardElementFactorKind.PT2 else 1
    coefficient = sign * 20 * order * factor.multiplicity
    omega = factor.corner_frequency.canonical_text
    return f"{coefficient:+d}*log10(max(1, omega/({omega})))"


def _asymptote_term_latex(factor: StandardElementFactor, *, sign: int) -> str:
    order = 2 if factor.kind is StandardElementFactorKind.PT2 else 1
    coefficient = sign * 20 * order * factor.multiplicity
    omega = exact_expression(factor.corner_frequency).latex
    return (
        rf"{_signed(coefficient)}\log_{{10}}\!\left("
        rf"\max\!\left\{{1,\frac{{\omega}}{{{omega}}}\right\}}\right)"
    )


def _power(value: str, exponent: int) -> str:
    return value if exponent == 1 else f"{value}^{exponent}"


def _power_latex(value: str, exponent: int) -> str:
    return value if exponent == 1 else rf"{value}^{{{exponent}}}"


def _signed(value: int) -> str:
    return f"+{value}" if value >= 0 else str(value)


def _require_supported(result: StandardElementBodeResult) -> None:
    if type(result) is not StandardElementBodeResult or not result.supported:
        raise ValueError("A supported StandardElementBodeResult is required.")


__all__ = [
    "exact_expression_decimal_text",
    "standard_element_asymptote_latex",
    "standard_element_asymptote_plain",
    "standard_element_decomposition_latex",
    "standard_element_decomposition_plain",
    "standard_element_events_plain",
]
