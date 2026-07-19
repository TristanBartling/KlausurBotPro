"""Public SymPy-free contracts for exact pointwise frequency responses."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import StrEnum

from klausurbotpro.domain.diagnostics import Diagnostic, DiagnosticSeverity
from klausurbotpro.domain.expression import ExactExpression
from klausurbotpro.domain.parameter_substitutions import (
    ExactRationalValue,
    ParameterSubstitutions,
)
from klausurbotpro.domain.reduced_transfer_function import (
    ReducedTransferFunction,
)


class FrequencyResponsePointStatus(StrEnum):
    """Outcome of evaluating one exact non-negative angular frequency."""

    DEFINED = "defined"
    ZERO_RESPONSE = "zero_response"
    SINGULAR = "singular"
    SYMBOLIC_UNDETERMINED = "symbolic_undetermined"
    NUMERIC_UNDETERMINED = "numeric_undetermined"


class TransferFunctionFrequencyResponseStatus(StrEnum):
    """Aggregate state of one ordered pointwise frequency analysis."""

    COMPLETE = "complete"
    PARTIAL = "partial"
    SYMBOLIC_UNDETERMINED = "symbolic_undetermined"
    FAILED = "failed"


class DecibelValueKind(StrEnum):
    """Finite level or the exact zero-response limit of minus infinity."""

    FINITE = "finite"
    NEGATIVE_INFINITY = "negative_infinity"


@dataclass(frozen=True, slots=True)
class NumericalDecibelValue:
    """Structured numerical dB value without non-finite float sentinels."""

    kind: DecibelValueKind
    decimal_value: str | None = None

    def __post_init__(self) -> None:
        if type(self.kind) is not DecibelValueKind:
            raise TypeError("A dB value requires a supported kind.")
        if self.kind is DecibelValueKind.NEGATIVE_INFINITY:
            if self.decimal_value is not None:
                raise ValueError("Minus infinity must not contain a decimal value.")
            return
        if self.decimal_value is None:
            raise ValueError("A finite dB value requires a decimal value.")
        object.__setattr__(
            self,
            "decimal_value",
            _canonical_finite_decimal(self.decimal_value),
        )


@dataclass(frozen=True, slots=True)
class FrequencySampleSet:
    """Ordered exact angular frequencies in radians per second."""

    frequencies: tuple[ExactRationalValue, ...]

    def __post_init__(self) -> None:
        if type(self.frequencies) is not tuple:
            raise TypeError("Frequency samples must be stored in a tuple.")
        if any(type(value) is not ExactRationalValue for value in self.frequencies):
            raise TypeError("Every frequency must be an ExactRationalValue.")


@dataclass(frozen=True, slots=True)
class FrequencyResponseLimits:
    """Finite in-process limits; no hard process timeout is implied."""

    max_frequency_points: int = 256
    max_substitution_integer_digits: int = 256
    max_expression_nodes: int = 2048
    max_intermediate_operations: int = 16_384
    numerical_precision_digits: int = 40
    max_numeric_exponent_abs: int = 1024
    max_frequency_integer_digits: int = 256
    max_polynomial_degree: int = 64
    max_parameters: int = 16
    max_domain_exclusions: int = 64

    def __post_init__(self) -> None:
        for name in self.__dataclass_fields__:
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive int.")


@dataclass(frozen=True, slots=True)
class FrequencyResponsePoint:
    """Exact frequency-response value and subordinate numerical presentation."""

    omega: ExactRationalValue
    status: FrequencyResponsePointStatus
    specialized_numerator: ExactExpression
    specialized_denominator: ExactExpression
    exact_complex_value: ExactExpression | None = None
    exact_real_part: ExactExpression | None = None
    exact_imaginary_part: ExactExpression | None = None
    exact_magnitude_squared: ExactExpression | None = None
    numerical_real: str | None = None
    numerical_imaginary: str | None = None
    numerical_magnitude: str | None = None
    numerical_decibel: NumericalDecibelValue | None = None
    numerical_phase_degrees: str | None = None
    diagnostics: tuple[Diagnostic, ...] = ()

    def __post_init__(self) -> None:
        if type(self.omega) is not ExactRationalValue:
            raise TypeError("A frequency-response point requires an exact omega.")
        if type(self.status) is not FrequencyResponsePointStatus:
            raise TypeError("A frequency-response point requires a supported status.")
        if (
            type(self.specialized_numerator) is not ExactExpression
            or type(self.specialized_denominator) is not ExactExpression
        ):
            raise TypeError("Specialized numerator and denominator must be exact.")
        exact_values = (
            self.exact_complex_value,
            self.exact_real_part,
            self.exact_imaginary_part,
            self.exact_magnitude_squared,
        )
        if any(
            value is not None and type(value) is not ExactExpression
            for value in exact_values
        ):
            raise TypeError("Exact frequency-response values have invalid types.")
        diagnostics = tuple(self.diagnostics)
        if any(type(item) is not Diagnostic for item in diagnostics):
            raise TypeError("Point diagnostics must be structured diagnostics.")
        object.__setattr__(self, "diagnostics", diagnostics)

        numerical_names = (
            "numerical_real",
            "numerical_imaginary",
            "numerical_magnitude",
            "numerical_phase_degrees",
        )
        for name in numerical_names:
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, _canonical_finite_decimal(value))
        if self.numerical_decibel is not None and type(
            self.numerical_decibel
        ) is not NumericalDecibelValue:
            raise TypeError("The numerical dB value has an invalid type.")

        has_all_exact = all(value is not None for value in exact_values)
        if self.status is FrequencyResponsePointStatus.DEFINED:
            if (
                not has_all_exact
                or self.numerical_real is None
                or self.numerical_imaginary is None
                or self.numerical_magnitude is None
                or self.numerical_decibel is None
                or self.numerical_decibel.kind is not DecibelValueKind.FINITE
                or self.numerical_phase_degrees is None
            ):
                raise ValueError("A defined point requires complete exact and numeric values.")
        elif self.status is FrequencyResponsePointStatus.ZERO_RESPONSE:
            if (
                not has_all_exact
                or self.numerical_real != "0"
                or self.numerical_imaginary != "0"
                or self.numerical_magnitude != "0"
                or self.numerical_decibel is None
                or self.numerical_decibel.kind
                is not DecibelValueKind.NEGATIVE_INFINITY
                or self.numerical_phase_degrees is not None
            ):
                raise ValueError("A zero response requires zero values and minus infinity.")
        elif self.status is FrequencyResponsePointStatus.NUMERIC_UNDETERMINED:
            if not has_all_exact or any(
                getattr(self, name) is not None for name in numerical_names
            ) or self.numerical_decibel is not None:
                raise ValueError(
                    "A numerically undetermined point retains only exact values."
                )
        elif any(value is not None for value in exact_values) or any(
            getattr(self, name) is not None for name in numerical_names
        ) or self.numerical_decibel is not None:
            raise ValueError(
                "Singular and symbolic points must not invent response values."
            )
        if has_all_exact and any(
            value is not None and value.symbol_names for value in exact_values
        ):
            raise ValueError("Evaluated exact response values must be parameter-free.")
        if self.status in (
            FrequencyResponsePointStatus.DEFINED,
            FrequencyResponsePointStatus.ZERO_RESPONSE,
            FrequencyResponsePointStatus.NUMERIC_UNDETERMINED,
        ) and (
            self.specialized_numerator.symbol_names
            or self.specialized_denominator.symbol_names
        ):
            raise ValueError("Evaluated specialized values must be parameter-free.")
        if self.status is FrequencyResponsePointStatus.ZERO_RESPONSE and any(
            value is None or value.canonical_text != "0" for value in exact_values
        ):
            raise ValueError("A zero response requires exact zero response values.")
        if self.numerical_magnitude is not None and Decimal(
            self.numerical_magnitude
        ) < 0:
            raise ValueError("A numerical magnitude must be non-negative.")
        if self.numerical_phase_degrees is not None:
            phase = Decimal(self.numerical_phase_degrees)
            if phase <= -180 or phase > 180:
                raise ValueError("The principal phase must lie in (-180, 180].")


@dataclass(frozen=True, slots=True, init=False)
class TransferFunctionFrequencyResponseResult:
    """Controlled result of one defensive pointwise analysis attempt."""

    reduced_transfer_function: ReducedTransferFunction | None
    frequencies: FrequencySampleSet | None
    substitutions: ParameterSubstitutions | None
    status: TransferFunctionFrequencyResponseStatus
    points: tuple[FrequencyResponsePoint, ...]
    diagnostics: tuple[Diagnostic, ...]

    def __new__(cls) -> TransferFunctionFrequencyResponseResult:
        raise TypeError(
            "Frequency-response results must be created by "
            "TransferFunctionFrequencyResponseAnalyzer."
        )

    @classmethod
    def _create(
        cls,
        *,
        reduced_transfer_function: ReducedTransferFunction | None,
        frequencies: FrequencySampleSet | None,
        substitutions: ParameterSubstitutions | None,
        status: TransferFunctionFrequencyResponseStatus,
        points: tuple[FrequencyResponsePoint, ...] = (),
        diagnostics: tuple[Diagnostic, ...] = (),
    ) -> TransferFunctionFrequencyResponseResult:
        instance = object.__new__(cls)
        object.__setattr__(
            instance,
            "reduced_transfer_function",
            reduced_transfer_function,
        )
        object.__setattr__(instance, "frequencies", frequencies)
        object.__setattr__(instance, "substitutions", substitutions)
        object.__setattr__(instance, "status", status)
        object.__setattr__(instance, "points", tuple(points))
        object.__setattr__(instance, "diagnostics", tuple(diagnostics))
        instance._validate()
        return instance

    def _validate(self) -> None:
        if type(self.status) is not TransferFunctionFrequencyResponseStatus:
            raise TypeError("Invalid aggregate frequency-response status.")
        if self.substitutions is not None and type(
            self.substitutions
        ) is not ParameterSubstitutions:
            raise TypeError("Invalid parameter substitutions.")
        if any(type(item) is not FrequencyResponsePoint for item in self.points):
            raise TypeError("Invalid frequency-response point.")
        if any(type(item) is not Diagnostic for item in self.diagnostics):
            raise TypeError("Invalid frequency-response diagnostic.")
        has_error = any(
            item.severity is DiagnosticSeverity.ERROR for item in self.diagnostics
        )
        if self.status is TransferFunctionFrequencyResponseStatus.FAILED:
            if (
                self.points
                or not has_error
                or self.reduced_transfer_function is not None
                or self.frequencies is not None
            ):
                raise ValueError("A failed analysis requires no points and an error.")
            return
        if (
            type(self.reduced_transfer_function) is not ReducedTransferFunction
            or type(self.frequencies) is not FrequencySampleSet
            or len(self.points) != len(self.frequencies.frequencies)
            or has_error
        ):
            raise ValueError(
                "A successful frequency response requires complete context and no error."
            )
        if tuple(point.omega for point in self.points) != self.frequencies.frequencies:
            raise ValueError("Frequency-response points must preserve sample order.")
        point_statuses = tuple(point.status for point in self.points)
        complete = all(
            status
            in (
                FrequencyResponsePointStatus.DEFINED,
                FrequencyResponsePointStatus.ZERO_RESPONSE,
            )
            for status in point_statuses
        )
        symbolic = all(
            status is FrequencyResponsePointStatus.SYMBOLIC_UNDETERMINED
            for status in point_statuses
        )
        if (
            self.status is TransferFunctionFrequencyResponseStatus.COMPLETE
            and not complete
        ) or (
            self.status
            is TransferFunctionFrequencyResponseStatus.SYMBOLIC_UNDETERMINED
            and not symbolic
        ) or (
            self.status is TransferFunctionFrequencyResponseStatus.PARTIAL
            and (complete or symbolic)
        ):
            raise ValueError("Aggregate and point statuses are inconsistent.")

    @property
    def succeeded(self) -> bool:
        """Return whether validation produced structured point outcomes."""

        return self.status is not TransferFunctionFrequencyResponseStatus.FAILED


def _canonical_finite_decimal(value: str) -> str:
    if type(value) is not str:
        raise TypeError("Numerical values must be decimal strings.")
    try:
        decimal = Decimal(value)
    except (InvalidOperation, ValueError) as error:
        raise ValueError("Numerical values must be decimal strings.") from error
    if not decimal.is_finite():
        raise ValueError("Numerical values must be finite.")
    if decimal.is_zero():
        return "0"
    sign, digits, exponent = decimal.as_tuple()
    if not isinstance(exponent, int):
        raise ValueError("Numerical values must be finite.")
    normalized_digits = list(digits)
    while len(normalized_digits) > 1 and normalized_digits[-1] == 0:
        normalized_digits.pop()
        exponent += 1
    normalized = Decimal((sign, tuple(normalized_digits), exponent))
    if normalized == normalized.to_integral():
        return format(normalized, "f")
    return str(normalized)


__all__ = [
    "DecibelValueKind",
    "FrequencyResponseLimits",
    "FrequencyResponsePoint",
    "FrequencyResponsePointStatus",
    "FrequencySampleSet",
    "NumericalDecibelValue",
    "TransferFunctionFrequencyResponseResult",
    "TransferFunctionFrequencyResponseStatus",
]
