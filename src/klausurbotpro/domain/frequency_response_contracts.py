"""Public SymPy-free contracts for exact pointwise frequency responses."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import StrEnum

from klausurbotpro.domain.diagnostics import (
    Diagnostic,
    DiagnosticCode,
    DiagnosticSeverity,
)
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


@dataclass(frozen=True, slots=True, init=False)
class FrequencyResponsePoint:
    """Analyzer-controlled exact point and subordinate numerical presentation."""

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

    def __new__(
        cls,
        *args: object,
        **kwargs: object,
    ) -> FrequencyResponsePoint:
        raise TypeError(
            "Frequency-response points must be created by the frequency-response "
            "analyzer."
        )

    @classmethod
    def _create(
        cls,
        *,
        omega: ExactRationalValue,
        status: FrequencyResponsePointStatus,
        specialized_numerator: ExactExpression,
        specialized_denominator: ExactExpression,
        exact_complex_value: ExactExpression | None = None,
        exact_real_part: ExactExpression | None = None,
        exact_imaginary_part: ExactExpression | None = None,
        exact_magnitude_squared: ExactExpression | None = None,
        numerical_real: str | None = None,
        numerical_imaginary: str | None = None,
        numerical_magnitude: str | None = None,
        numerical_decibel: NumericalDecibelValue | None = None,
        numerical_phase_degrees: str | None = None,
        diagnostics: tuple[Diagnostic, ...] = (),
    ) -> FrequencyResponsePoint:
        instance = object.__new__(cls)
        object.__setattr__(instance, "omega", omega)
        object.__setattr__(instance, "status", status)
        object.__setattr__(instance, "specialized_numerator", specialized_numerator)
        object.__setattr__(
            instance,
            "specialized_denominator",
            specialized_denominator,
        )
        object.__setattr__(instance, "exact_complex_value", exact_complex_value)
        object.__setattr__(instance, "exact_real_part", exact_real_part)
        object.__setattr__(instance, "exact_imaginary_part", exact_imaginary_part)
        object.__setattr__(
            instance,
            "exact_magnitude_squared",
            exact_magnitude_squared,
        )
        object.__setattr__(instance, "numerical_real", numerical_real)
        object.__setattr__(instance, "numerical_imaginary", numerical_imaginary)
        object.__setattr__(instance, "numerical_magnitude", numerical_magnitude)
        object.__setattr__(instance, "numerical_decibel", numerical_decibel)
        object.__setattr__(
            instance,
            "numerical_phase_degrees",
            numerical_phase_degrees,
        )
        object.__setattr__(instance, "diagnostics", diagnostics)
        instance._validate()
        return instance

    def _validate(self) -> None:
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
        if type(self.diagnostics) is not tuple or any(
            type(item) is not Diagnostic for item in self.diagnostics
        ):
            raise TypeError("Point diagnostics must be structured diagnostics.")
        if any(
            item.severity is DiagnosticSeverity.ERROR for item in self.diagnostics
        ):
            raise ValueError("A frequency-response point must not contain errors.")

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
            if Decimal(self.numerical_magnitude) <= 0:
                raise ValueError("A defined point requires a positive magnitude.")
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
        required_code = {
            FrequencyResponsePointStatus.ZERO_RESPONSE: (
                DiagnosticCode.FREQUENCY_RESPONSE_ZERO_RESPONSE
            ),
            FrequencyResponsePointStatus.SINGULAR: (
                DiagnosticCode.FREQUENCY_RESPONSE_SINGULAR
            ),
            FrequencyResponsePointStatus.SYMBOLIC_UNDETERMINED: (
                DiagnosticCode.FREQUENCY_RESPONSE_SYMBOLIC_UNDETERMINED
            ),
            FrequencyResponsePointStatus.NUMERIC_UNDETERMINED: (
                DiagnosticCode.FREQUENCY_RESPONSE_NUMERIC_UNDETERMINED
            ),
        }.get(self.status)
        point_status_codes = frozenset(
            (
                DiagnosticCode.FREQUENCY_RESPONSE_ZERO_RESPONSE,
                DiagnosticCode.FREQUENCY_RESPONSE_SINGULAR,
                DiagnosticCode.FREQUENCY_RESPONSE_SYMBOLIC_UNDETERMINED,
                DiagnosticCode.FREQUENCY_RESPONSE_NUMERIC_UNDETERMINED,
            )
        )
        if any(
            diagnostic.code in point_status_codes
            and diagnostic.code is not required_code
            for diagnostic in self.diagnostics
        ):
            raise ValueError("A point contains a diagnostic for a different status.")
        if required_code is not None and not any(
            diagnostic.code is required_code for diagnostic in self.diagnostics
        ):
            raise ValueError(
                "The point status requires its corresponding structured diagnostic."
            )


@dataclass(frozen=True, slots=True, init=False)
class TransferFunctionFrequencyResponseResult:
    """Controlled result of one defensive pointwise analysis attempt."""

    reduced_transfer_function: ReducedTransferFunction | None
    frequencies: FrequencySampleSet | None
    substitutions: ParameterSubstitutions | None
    status: TransferFunctionFrequencyResponseStatus
    points: tuple[FrequencyResponsePoint, ...]
    diagnostics: tuple[Diagnostic, ...]

    def __new__(
        cls,
        *args: object,
        **kwargs: object,
    ) -> TransferFunctionFrequencyResponseResult:
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
        object.__setattr__(instance, "points", points)
        object.__setattr__(instance, "diagnostics", diagnostics)
        instance._validate()
        return instance

    def _validate(self) -> None:
        if type(self.status) is not TransferFunctionFrequencyResponseStatus:
            raise TypeError("Invalid aggregate frequency-response status.")
        if type(self.points) is not tuple:
            raise TypeError("Frequency-response points must be stored in a tuple.")
        if type(self.diagnostics) is not tuple:
            raise TypeError("Frequency-response diagnostics must be stored in a tuple.")
        if self.substitutions is not None and type(
            self.substitutions
        ) is not ParameterSubstitutions:
            raise TypeError("Invalid parameter substitutions.")
        if any(type(item) is not FrequencyResponsePoint for item in self.points):
            raise TypeError("Invalid frequency-response point.")
        for point in self.points:
            point._validate()
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
                or self.substitutions is not None
            ):
                raise ValueError(
                    "A failed analysis retains no input values and requires an error."
                )
            return
        if (
            type(self.reduced_transfer_function) is not ReducedTransferFunction
            or type(self.frequencies) is not FrequencySampleSet
            or not self.points
            or len(self.points) != len(self.frequencies.frequencies)
            or has_error
        ):
            raise ValueError(
                "A successful frequency response requires complete context and no error."
            )
        if tuple(point.omega for point in self.points) != self.frequencies.frequencies:
            raise ValueError("Frequency-response points must preserve sample order.")
        expected_diagnostics = tuple(
            diagnostic
            for point in self.points
            for diagnostic in point.diagnostics
        )
        if self.diagnostics != expected_diagnostics:
            raise ValueError(
                "Result diagnostics must exactly concatenate point diagnostics."
            )
        expected_status = _aggregate_frequency_response_status(
            tuple(point.status for point in self.points)
        )
        if self.status is not expected_status:
            raise ValueError("Aggregate and point statuses are inconsistent.")

    @property
    def succeeded(self) -> bool:
        """Return whether validation produced structured point outcomes."""

        return self.status is not TransferFunctionFrequencyResponseStatus.FAILED


def _aggregate_frequency_response_status(
    statuses: tuple[FrequencyResponsePointStatus, ...],
) -> TransferFunctionFrequencyResponseStatus:
    """Derive the one authoritative non-failed aggregate status."""

    if type(statuses) is not tuple or not statuses or any(
        type(status) is not FrequencyResponsePointStatus for status in statuses
    ):
        raise ValueError("Aggregate status requires valid point statuses.")
    if all(
        status
        in (
            FrequencyResponsePointStatus.DEFINED,
            FrequencyResponsePointStatus.ZERO_RESPONSE,
        )
        for status in statuses
    ):
        return TransferFunctionFrequencyResponseStatus.COMPLETE
    if (
        FrequencyResponsePointStatus.SYMBOLIC_UNDETERMINED in statuses
        and not any(
            status
            in (
                FrequencyResponsePointStatus.DEFINED,
                FrequencyResponsePointStatus.ZERO_RESPONSE,
                FrequencyResponsePointStatus.NUMERIC_UNDETERMINED,
            )
            for status in statuses
        )
    ):
        return TransferFunctionFrequencyResponseStatus.SYMBOLIC_UNDETERMINED
    return TransferFunctionFrequencyResponseStatus.PARTIAL


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
