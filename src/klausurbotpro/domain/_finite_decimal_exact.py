"""Exact finite-decimal arithmetic without context-dependent rounding."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from re import compile as compile_pattern

_DECIMAL_PATTERN = compile_pattern(
    r"(?P<sign>[+-]?)(?P<integer>\d+)"
    r"(?:\.(?P<fraction>\d*))?"
    r"(?:[eE](?P<exponent>[+-]?\d+))?"
)


class FiniteDecimalError(ValueError):
    """A finite decimal string or operation violates its exact contract."""


@dataclass(frozen=True, slots=True)
class FiniteDecimal:
    coefficient: int
    exponent10: int

    def __post_init__(self) -> None:
        if type(self.coefficient) is not int or type(self.exponent10) is not int:
            raise TypeError("FiniteDecimal fields must be exact integers.")
        coefficient = self.coefficient
        exponent = self.exponent10
        if coefficient == 0:
            object.__setattr__(self, "exponent10", 0)
            return
        while coefficient % 10 == 0:
            coefficient //= 10
            exponent += 1
        object.__setattr__(self, "coefficient", coefficient)
        object.__setattr__(self, "exponent10", exponent)

    @classmethod
    def parse(cls, text: str, max_digits: int) -> FiniteDecimal:
        if type(text) is not str:
            raise TypeError("A finite decimal must be an exact string.")
        if type(max_digits) is not int or max_digits <= 0:
            raise ValueError("max_digits must be a positive int.")
        if len(text) > 4 * max_digits + 16:
            raise FiniteDecimalError("Decimal input exceeds its size limit.")
        match = _DECIMAL_PATTERN.fullmatch(text)
        if match is None:
            raise FiniteDecimalError("Invalid finite decimal string.")
        integer = match.group("integer")
        fraction = match.group("fraction") or ""
        digits = integer + fraction
        if len(digits) > max_digits:
            raise FiniteDecimalError("Decimal significand exceeds its digit limit.")
        try:
            exponent = int(match.group("exponent") or "0") - len(fraction)
            coefficient = int(digits)
        except ValueError as error:
            raise FiniteDecimalError("Invalid finite decimal integer fields.") from error
        if match.group("sign") == "-":
            coefficient = -coefficient
        value = cls(coefficient, exponent)
        value.validate_size(max_digits)
        return value

    @classmethod
    def from_int(cls, value: int) -> FiniteDecimal:
        if type(value) is not int:
            raise TypeError("An exact decimal integer must be an int.")
        return cls(value, 0)

    def validate_size(self, max_digits: int) -> None:
        if type(max_digits) is not int or max_digits <= 0:
            raise ValueError("max_digits must be a positive int.")
        coefficient_digits = len(str(abs(self.coefficient)))
        if (
            coefficient_digits > max_digits
            or abs(self.exponent10) > max_digits
            or coefficient_digits + max(0, self.exponent10) > max_digits
        ):
            raise FiniteDecimalError("Decimal value exceeds its digit limit.")

    def add_integer(self, value: int) -> FiniteDecimal:
        if type(value) is not int:
            raise TypeError("An exact decimal offset must be an int.")
        return self + FiniteDecimal.from_int(value)

    def __add__(self, other: FiniteDecimal) -> FiniteDecimal:
        if type(other) is not FiniteDecimal:
            return NotImplemented
        exponent = min(self.exponent10, other.exponent10)
        left = self.coefficient * 10 ** (self.exponent10 - exponent)
        right = other.coefficient * 10 ** (other.exponent10 - exponent)
        return FiniteDecimal(left + right, exponent)

    def __sub__(self, other: FiniteDecimal) -> FiniteDecimal:
        if type(other) is not FiniteDecimal:
            return NotImplemented
        return self + FiniteDecimal(-other.coefficient, other.exponent10)

    def absolute(self) -> FiniteDecimal:
        return FiniteDecimal(abs(self.coefficient), self.exponent10)

    def compare(self, other: FiniteDecimal) -> int:
        if type(other) is not FiniteDecimal:
            raise TypeError("Finite decimals can only be compared exactly.")
        exponent = min(self.exponent10, other.exponent10)
        left = self.coefficient * 10 ** (self.exponent10 - exponent)
        right = other.coefficient * 10 ** (other.exponent10 - exponent)
        if left < right:
            return -1
        if left > right:
            return 1
        return 0

    def floor_divide_by_positive_int(self, divisor: int) -> int:
        numerator, denominator = self._fraction_parts()
        if type(divisor) is not int or divisor <= 0:
            raise ValueError("The decimal divisor must be a positive int.")
        return numerator // (denominator * divisor)

    def ceil_divide_by_positive_int(self, divisor: int) -> int:
        numerator, denominator = self._fraction_parts()
        if type(divisor) is not int or divisor <= 0:
            raise ValueError("The decimal divisor must be a positive int.")
        scaled_denominator = denominator * divisor
        return int(-((-numerator) // scaled_denominator))

    def canonical_text(self) -> str:
        if self.coefficient == 0:
            return "0"
        sign = 1 if self.coefficient < 0 else 0
        digits = tuple(int(character) for character in str(abs(self.coefficient)))
        decimal = Decimal((sign, digits, self.exponent10))
        if self.exponent10 >= 0:
            return format(decimal, "f")
        return str(decimal)

    def _fraction_parts(self) -> tuple[int, int]:
        if self.exponent10 >= 0:
            return self.coefficient * 10**self.exponent10, 1
        return self.coefficient, 10 ** (-self.exponent10)


__all__ = ["FiniteDecimal", "FiniteDecimalError"]
