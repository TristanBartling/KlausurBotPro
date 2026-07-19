"""Numerical presentation derived only from exact frequency-response values."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

import sympy as sp
from sympy.core.evalf import PrecisionExhausted

from klausurbotpro.domain.frequency_response_contracts import (
    DecibelValueKind,
    FrequencyResponseLimits,
    NumericalDecibelValue,
)


class FrequencyResponseNumericError(ArithmeticError):
    """A finite deterministic numerical presentation could not be produced."""


class FrequencyResponseNumericLimitError(FrequencyResponseNumericError):
    """The configured decimal exponent bound was exceeded."""


def numerical_frequency_response(
    real: sp.Expr,
    imaginary: sp.Expr,
    magnitude_squared: sp.Expr,
    limits: FrequencyResponseLimits,
) -> tuple[str, str, str, NumericalDecibelValue, str]:
    """Return finite decimal strings and the principal phase in degrees."""

    magnitude = sp.sqrt(magnitude_squared)
    decibel = 20 * sp.log(magnitude, 10)
    phase = sp.atan2(imaginary, real) * 180 / sp.pi
    return (
        _decimal_text(real, limits),
        _decimal_text(imaginary, limits),
        _decimal_text(magnitude, limits),
        NumericalDecibelValue(
            DecibelValueKind.FINITE,
            _decimal_text(decibel, limits),
        ),
        _decimal_text(phase, limits),
    )


def _decimal_text(
    expression: sp.Expr,
    limits: FrequencyResponseLimits,
) -> str:
    if expression.is_zero is True:
        return "0"
    try:
        evaluated = expression.evalf(
            limits.numerical_precision_digits,
            strict=True,
        )
    except (ArithmeticError, PrecisionExhausted, ValueError) as error:
        raise FrequencyResponseNumericError from error
    if evaluated.is_real is not True or evaluated.is_finite is not True:
        raise FrequencyResponseNumericError
    try:
        decimal = Decimal(str(evaluated))
    except (InvalidOperation, ValueError) as error:
        raise FrequencyResponseNumericError from error
    if not decimal.is_finite():
        raise FrequencyResponseNumericError
    if decimal.is_zero():
        return "0"
    if abs(decimal.adjusted()) > limits.max_numeric_exponent_abs:
        raise FrequencyResponseNumericLimitError
    sign, digits, exponent = decimal.as_tuple()
    if not isinstance(exponent, int):
        raise FrequencyResponseNumericError
    normalized_digits = list(digits)
    while len(normalized_digits) > 1 and normalized_digits[-1] == 0:
        normalized_digits.pop()
        exponent += 1
    normalized = Decimal((sign, tuple(normalized_digits), exponent))
    if normalized == normalized.to_integral():
        return format(normalized, "f")
    return str(normalized)


__all__ = [
    "FrequencyResponseNumericError",
    "FrequencyResponseNumericLimitError",
    "numerical_frequency_response",
]
