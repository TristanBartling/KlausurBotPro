"""Public SymPy- and float-free contracts for logarithmic frequency grids."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from math import gcd

from klausurbotpro.domain.diagnostics import Diagnostic, DiagnosticSeverity
from klausurbotpro.domain.parameter_substitutions import ExactRationalValue


class LogFrequencyPointOrigin(StrEnum):
    """Deterministically ordered origin of one grid evaluation frequency."""

    LOWER_BOUND = "lower_bound"
    GENERATED = "generated"
    UPPER_BOUND = "upper_bound"
    EXPLICIT = "explicit"


class LogFrequencyGridStatus(StrEnum):
    """Outcome of one bounded logarithmic grid generation."""

    COMPLETE = "complete"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class ScientificDecimal:
    """Canonical positive finite decimal as ``significand * 10**exponent10``."""

    significand: int
    exponent10: int

    def __post_init__(self) -> None:
        if (
            type(self.significand) is not int
            or type(self.exponent10) is not int
        ):
            raise TypeError("ScientificDecimal fields must be real integers.")
        if self.significand <= 0:
            raise ValueError("ScientificDecimal must be positive and finite.")
        significand = self.significand
        exponent = self.exponent10
        while significand % 10 == 0:
            significand //= 10
            exponent += 1
        object.__setattr__(self, "significand", significand)
        object.__setattr__(self, "exponent10", exponent)

    @property
    def decimal_text(self) -> str:
        """Return a deterministic non-scientific decimal representation."""

        digits = str(self.significand)
        decimal_position = len(digits) + self.exponent10
        if decimal_position <= 0:
            return f"0.{('0' * -decimal_position)}{digits}"
        if decimal_position >= len(digits):
            return f"{digits}{'0' * (decimal_position - len(digits))}"
        return f"{digits[:decimal_position]}.{digits[decimal_position:]}"

    @property
    def scientific_text(self) -> str:
        """Return a deterministic normalized scientific representation."""

        digits = str(self.significand)
        mantissa = digits if len(digits) == 1 else f"{digits[0]}.{digits[1:]}"
        exponent = self.exponent10 + len(digits) - 1
        return f"{mantissa}e{exponent:+d}"


@dataclass(frozen=True, slots=True)
class LogFrequencyGridRequest:
    """Untrusted exact user inputs for one positive logarithmic grid."""

    omega_min: ExactRationalValue
    omega_max: ExactRationalValue
    points_per_decade: int
    explicit_frequencies: tuple[ExactRationalValue, ...] = ()


@dataclass(frozen=True, slots=True)
class LogFrequencyGridLimits:
    """Finite in-process grid limits; no hard timeout is implied."""

    max_decades: int = 24
    max_points_per_decade: int = 64
    max_total_points: int = 2048
    max_explicit_points: int = 256
    grid_precision_digits: int = 24
    grid_guard_digits: int = 12
    max_certification_attempts: int = 3
    max_certification_steps: int = 16_384
    max_rational_integer_digits: int = 256
    max_diagnostics: int = 16

    def __post_init__(self) -> None:
        for name in self.__dataclass_fields__:
            value = getattr(self, name)
            if type(value) is not int or value <= 0:
                raise ValueError(f"{name} must be a positive int.")
        if self.grid_precision_digits < 2:
            raise ValueError("grid_precision_digits must be at least 2.")


_ORIGIN_ORDER = {
    LogFrequencyPointOrigin.LOWER_BOUND: 0,
    LogFrequencyPointOrigin.GENERATED: 1,
    LogFrequencyPointOrigin.UPPER_BOUND: 2,
    LogFrequencyPointOrigin.EXPLICIT: 3,
}


@dataclass(frozen=True, slots=True, init=False)
class LogFrequencyGridPoint:
    """Generator-controlled target description and rational evaluation point."""

    evaluation_frequency: ExactRationalValue
    target_decimal: ScientificDecimal
    target_index: int | None
    target_interval_count: int | None
    origins: tuple[LogFrequencyPointOrigin, ...]
    maximum_relative_error: ExactRationalValue
    diagnostics: tuple[Diagnostic, ...]

    def __new__(
        cls,
        *args: object,
        **kwargs: object,
    ) -> LogFrequencyGridPoint:
        raise TypeError(
            "Logarithmic frequency-grid points must be created by "
            "LogFrequencyGridGenerator."
        )

    @classmethod
    def _create(
        cls,
        *,
        evaluation_frequency: ExactRationalValue,
        target_decimal: ScientificDecimal,
        target_index: int | None,
        target_interval_count: int | None,
        origins: tuple[LogFrequencyPointOrigin, ...],
        maximum_relative_error: ExactRationalValue,
        diagnostics: tuple[Diagnostic, ...] = (),
    ) -> LogFrequencyGridPoint:
        instance = object.__new__(cls)
        object.__setattr__(
            instance,
            "evaluation_frequency",
            evaluation_frequency,
        )
        object.__setattr__(instance, "target_decimal", target_decimal)
        object.__setattr__(instance, "target_index", target_index)
        object.__setattr__(
            instance,
            "target_interval_count",
            target_interval_count,
        )
        object.__setattr__(instance, "origins", origins)
        object.__setattr__(
            instance,
            "maximum_relative_error",
            maximum_relative_error,
        )
        object.__setattr__(instance, "diagnostics", diagnostics)
        instance._validate()
        return instance

    def _validate(self) -> None:
        _validate_exact_rational(
            self.evaluation_frequency,
            positive=True,
            label="evaluation frequency",
        )
        if type(self.target_decimal) is not ScientificDecimal:
            raise TypeError("A grid point requires a ScientificDecimal target.")
        if (self.target_index is None) != (self.target_interval_count is None):
            raise ValueError("Target index and interval count must occur together.")
        if self.target_index is not None and (
            type(self.target_index) is not int
            or type(self.target_interval_count) is not int
            or self.target_interval_count <= 0
            or not 0 <= self.target_index <= self.target_interval_count
        ):
            raise ValueError("The logarithmic target coordinates are invalid.")
        if type(self.origins) is not tuple or not self.origins or any(
            type(origin) is not LogFrequencyPointOrigin for origin in self.origins
        ):
            raise TypeError("Grid-point origins must be a non-empty exact tuple.")
        expected_origins = tuple(
            sorted(set(self.origins), key=_ORIGIN_ORDER.__getitem__)
        )
        if self.origins != expected_origins:
            raise ValueError("Grid-point origins must be unique and canonical.")
        allowed_origins: tuple[
            tuple[LogFrequencyPointOrigin, ...],
            ...,
        ]
        if self.target_index is None:
            allowed_origins = ((LogFrequencyPointOrigin.EXPLICIT,),)
        elif self.target_index == 0:
            allowed_origins = (
                (LogFrequencyPointOrigin.LOWER_BOUND,),
                (
                    LogFrequencyPointOrigin.LOWER_BOUND,
                    LogFrequencyPointOrigin.EXPLICIT,
                ),
            )
        elif self.target_index == self.target_interval_count:
            allowed_origins = (
                (LogFrequencyPointOrigin.UPPER_BOUND,),
                (
                    LogFrequencyPointOrigin.UPPER_BOUND,
                    LogFrequencyPointOrigin.EXPLICIT,
                ),
            )
        else:
            allowed_origins = (
                (LogFrequencyPointOrigin.GENERATED,),
                (
                    LogFrequencyPointOrigin.GENERATED,
                    LogFrequencyPointOrigin.EXPLICIT,
                ),
            )
        if self.origins not in allowed_origins:
            raise ValueError("Grid-point origins contradict the target coordinate.")
        _validate_exact_rational(
            self.maximum_relative_error,
            positive=False,
            label="relative error",
        )
        if self.maximum_relative_error.numerator < 0 or (
            self.maximum_relative_error.numerator
            >= self.maximum_relative_error.denominator
        ):
            raise ValueError("A relative error bound must lie in [0, 1).")
        is_inner = (
            self.target_index is not None
            and self.target_interval_count is not None
            and 0 < self.target_index < self.target_interval_count
        )
        has_explicit_origin = LogFrequencyPointOrigin.EXPLICIT in self.origins
        if (
            is_inner
            and not has_explicit_origin
            and self.maximum_relative_error.numerator == 0
        ):
            raise ValueError("An approximated inner target needs a positive error bound.")
        if (
            is_inner
            and has_explicit_origin
            and self.maximum_relative_error.numerator != 0
        ):
            raise ValueError("An exact explicit target match needs zero error.")
        if not is_inner and self.maximum_relative_error.numerator != 0:
            raise ValueError("Exact boundaries and explicit points need zero error.")
        if type(self.diagnostics) is not tuple or any(
            type(item) is not Diagnostic for item in self.diagnostics
        ):
            raise TypeError("Grid-point diagnostics must be an exact tuple.")
        if any(
            item.severity is DiagnosticSeverity.ERROR for item in self.diagnostics
        ):
            raise ValueError("A completed grid point must not contain errors.")


@dataclass(frozen=True, slots=True, init=False)
class LogFrequencyGridResult:
    """Generator-controlled complete grid or value-free diagnostic failure."""

    request: LogFrequencyGridRequest | None
    interval_count: int | None
    status: LogFrequencyGridStatus
    points: tuple[LogFrequencyGridPoint, ...]
    diagnostics: tuple[Diagnostic, ...]

    def __new__(
        cls,
        *args: object,
        **kwargs: object,
    ) -> LogFrequencyGridResult:
        raise TypeError(
            "Logarithmic frequency-grid results must be created by "
            "LogFrequencyGridGenerator."
        )

    @classmethod
    def _create(
        cls,
        *,
        request: LogFrequencyGridRequest | None,
        interval_count: int | None,
        status: LogFrequencyGridStatus,
        points: tuple[LogFrequencyGridPoint, ...] = (),
        diagnostics: tuple[Diagnostic, ...] = (),
    ) -> LogFrequencyGridResult:
        instance = object.__new__(cls)
        object.__setattr__(instance, "request", request)
        object.__setattr__(instance, "interval_count", interval_count)
        object.__setattr__(instance, "status", status)
        object.__setattr__(instance, "points", points)
        object.__setattr__(instance, "diagnostics", diagnostics)
        instance._validate()
        return instance

    def _validate(self) -> None:
        if type(self.status) is not LogFrequencyGridStatus:
            raise TypeError("A logarithmic grid result has an invalid status.")
        if type(self.points) is not tuple or any(
            type(point) is not LogFrequencyGridPoint for point in self.points
        ):
            raise TypeError("Grid-result points must be an exact point tuple.")
        for point in self.points:
            point._validate()
        if type(self.diagnostics) is not tuple or any(
            type(item) is not Diagnostic for item in self.diagnostics
        ):
            raise TypeError("Grid-result diagnostics must be an exact tuple.")
        has_error = any(
            item.severity is DiagnosticSeverity.ERROR for item in self.diagnostics
        )
        if self.status is LogFrequencyGridStatus.FAILED:
            if (
                self.request is not None
                or self.interval_count is not None
                or self.points
                or not has_error
            ):
                raise ValueError(
                    "A failed logarithmic grid retains no request or partial points."
                )
            return
        if (
            type(self.request) is not LogFrequencyGridRequest
            or type(self.interval_count) is not int
            or self.interval_count <= 0
            or not self.points
            or has_error
        ):
            raise ValueError("A complete logarithmic grid has invalid context.")
        expected_diagnostics = tuple(
            diagnostic
            for point in self.points
            for diagnostic in point.diagnostics
        )
        if self.diagnostics != expected_diagnostics:
            raise ValueError(
                "Grid diagnostics must exactly concatenate point diagnostics."
            )
        if self.points[0].evaluation_frequency != self.request.omega_min:
            raise ValueError("A complete grid must start at omega_min.")
        if self.points[-1].evaluation_frequency != self.request.omega_max:
            raise ValueError("A complete grid must end at omega_max.")
        target_points = tuple(
            point for point in self.points if point.target_index is not None
        )
        if tuple(point.target_index for point in target_points) != tuple(
            range(self.interval_count + 1)
        ) or any(
            point.target_interval_count != self.interval_count
            for point in target_points
        ):
            raise ValueError(
                "A complete grid requires every target index exactly once."
            )
        previous: ExactRationalValue | None = None
        for point in self.points:
            current = point.evaluation_frequency
            if previous is not None and (
                previous.numerator * current.denominator
                >= current.numerator * previous.denominator
            ):
                raise ValueError("Grid evaluation frequencies must strictly increase.")
            previous = current

    @property
    def succeeded(self) -> bool:
        """Return whether the complete bounded grid was generated."""

        return self.status is LogFrequencyGridStatus.COMPLETE


def _validate_exact_rational(
    value: ExactRationalValue,
    *,
    positive: bool,
    label: str,
) -> None:
    if type(value) is not ExactRationalValue:
        raise TypeError(f"The {label} must be an ExactRationalValue.")
    if (
        type(value.numerator) is not int
        or type(value.denominator) is not int
        or value.denominator <= 0
        or gcd(abs(value.numerator), value.denominator) != 1
    ):
        raise ValueError(f"The {label} must be a canonical rational value.")
    if positive and value.numerator <= 0:
        raise ValueError(f"The {label} must be positive.")


__all__ = [
    "LogFrequencyGridLimits",
    "LogFrequencyGridPoint",
    "LogFrequencyGridRequest",
    "LogFrequencyGridResult",
    "LogFrequencyGridStatus",
    "LogFrequencyPointOrigin",
    "ScientificDecimal",
]
