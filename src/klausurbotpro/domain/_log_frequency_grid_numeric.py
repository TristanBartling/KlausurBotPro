"""Deterministic local-Decimal approximation for logarithmic grid targets."""

from __future__ import annotations

from decimal import (
    ROUND_HALF_EVEN,
    Context,
    Decimal,
    DecimalException,
    localcontext,
)
from fractions import Fraction

from klausurbotpro.domain.log_frequency_grid_contracts import ScientificDecimal


class LogFrequencyGridNumericError(ArithmeticError):
    """A finite positive Decimal candidate could not be produced."""


def approximate_logarithmic_target(
    omega_min: Fraction,
    ratio: Fraction,
    target_index: int,
    interval_count: int,
    *,
    precision_digits: int,
    guard_digits: int,
) -> tuple[ScientificDecimal, Fraction]:
    """Round one positive algebraic target to significant decimal digits."""

    try:
        with localcontext(
            Context(
                prec=precision_digits + guard_digits,
                rounding=ROUND_HALF_EVEN,
            )
        ):
            minimum = Decimal(omega_min.numerator) / Decimal(omega_min.denominator)
            ratio_decimal = Decimal(ratio.numerator) / Decimal(ratio.denominator)
            exponent = Decimal(target_index) / Decimal(interval_count)
            raw = minimum * (ratio_decimal**exponent)
            rounded = _round_significant(raw, precision_digits)
    except (DecimalException, ValueError) as error:
        raise LogFrequencyGridNumericError from error
    if not rounded.is_finite() or rounded <= 0:
        raise LogFrequencyGridNumericError
    scientific = scientific_decimal_from_decimal(rounded)
    return scientific, fraction_from_scientific_decimal(scientific)


def approximate_rational_for_display(
    value: Fraction,
    *,
    precision_digits: int,
    guard_digits: int,
) -> ScientificDecimal:
    """Return a deterministic display decimal without changing exact identity."""

    try:
        with localcontext(
            Context(
                prec=precision_digits + guard_digits,
                rounding=ROUND_HALF_EVEN,
            )
        ):
            raw = Decimal(value.numerator) / Decimal(value.denominator)
            rounded = _round_significant(raw, precision_digits)
    except (DecimalException, ValueError) as error:
        raise LogFrequencyGridNumericError from error
    if not rounded.is_finite() or rounded <= 0:
        raise LogFrequencyGridNumericError
    return scientific_decimal_from_decimal(rounded)


def scientific_decimal_from_decimal(value: Decimal) -> ScientificDecimal:
    """Convert one positive finite Decimal without a string or float round-trip."""

    if not value.is_finite() or value <= 0:
        raise LogFrequencyGridNumericError
    sign, digits, exponent = value.as_tuple()
    if sign != 0 or not isinstance(exponent, int):
        raise LogFrequencyGridNumericError
    significand = 0
    for digit in digits:
        significand = significand * 10 + digit
    return ScientificDecimal(significand, exponent)


def fraction_from_scientific_decimal(value: ScientificDecimal) -> Fraction:
    """Interpret a finite ScientificDecimal as its exact rational value."""

    if value.exponent10 >= 0:
        return Fraction(value.significand * 10**value.exponent10)
    return Fraction(value.significand, 10 ** (-value.exponent10))


def _round_significant(value: Decimal, precision_digits: int) -> Decimal:
    if not value.is_finite() or value <= 0:
        raise LogFrequencyGridNumericError
    quantum = Decimal(1).scaleb(value.adjusted() - precision_digits + 1)
    return value.quantize(quantum, rounding=ROUND_HALF_EVEN)


__all__ = [
    "LogFrequencyGridNumericError",
    "approximate_logarithmic_target",
    "approximate_rational_for_display",
    "fraction_from_scientific_decimal",
]
