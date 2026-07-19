"""Defensive validation and exact interval sizing for logarithmic grids."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from math import gcd

from klausurbotpro.domain.diagnostics import DiagnosticCode
from klausurbotpro.domain.log_frequency_grid_contracts import (
    LogFrequencyGridLimits,
    LogFrequencyGridRequest,
)
from klausurbotpro.domain.parameter_substitutions import ExactRationalValue


@dataclass(frozen=True, slots=True)
class LogFrequencyGridFailure(ValueError):
    """Expected invalid, limited, colliding, or uncertifiable grid."""

    code: DiagnosticCode
    message: str
    details: tuple[tuple[str, str], ...] = ()


class CertificationBudget:
    """Bound exact comparison work shared by sizing, matching, and proof."""

    def __init__(self, maximum_steps: int) -> None:
        self._maximum_steps = maximum_steps
        self.steps = 0

    def step(self) -> None:
        self.steps += 1
        if self.steps > self._maximum_steps:
            raise LogFrequencyGridFailure(
                DiagnosticCode.LOG_FREQUENCY_GRID_LIMIT_EXCEEDED,
                "Das logarithmische Raster überschreitet das Zertifizierungsbudget.",
                (("limit", "max_certification_steps"),),
            )


@dataclass(frozen=True, slots=True)
class ValidatedLogFrequencyGridRequest:
    """Internal exact snapshot of a fully revalidated request."""

    request: LogFrequencyGridRequest
    omega_min: Fraction
    omega_max: Fraction
    ratio: Fraction
    explicit_frequencies: tuple[Fraction, ...]


def validate_log_frequency_grid_request(
    request: LogFrequencyGridRequest,
    limits: LogFrequencyGridLimits,
) -> ValidatedLogFrequencyGridRequest:
    """Revalidate every nested request value before mathematical generation."""

    if type(request.omega_min) is not ExactRationalValue or type(
        request.omega_max
    ) is not ExactRationalValue:
        raise LogFrequencyGridFailure(
            DiagnosticCode.LOG_FREQUENCY_GRID_INVALID_REQUEST,
            "Die Rastergrenzen müssen exakte rationale Werte sein.",
        )
    _validate_rational(
        request.omega_min,
        limits,
        "omega_min",
        DiagnosticCode.LOG_FREQUENCY_GRID_INVALID_REQUEST,
    )
    _validate_rational(
        request.omega_max,
        limits,
        "omega_max",
        DiagnosticCode.LOG_FREQUENCY_GRID_INVALID_REQUEST,
    )
    omega_min = Fraction(
        request.omega_min.numerator,
        request.omega_min.denominator,
    )
    omega_max = Fraction(
        request.omega_max.numerator,
        request.omega_max.denominator,
    )
    if omega_min <= 0 or omega_max <= omega_min:
        raise LogFrequencyGridFailure(
            DiagnosticCode.LOG_FREQUENCY_GRID_INVALID_BOUNDS,
            "Es gilt zwingend 0 < omega_min < omega_max.",
        )
    if (
        type(request.points_per_decade) is not int
        or request.points_per_decade <= 0
    ):
        raise LogFrequencyGridFailure(
            DiagnosticCode.LOG_FREQUENCY_GRID_INVALID_REQUEST,
            "Punkte pro Dekade müssen eine positive ganze Zahl sein.",
        )
    if request.points_per_decade > limits.max_points_per_decade:
        raise LogFrequencyGridFailure(
            DiagnosticCode.LOG_FREQUENCY_GRID_LIMIT_EXCEEDED,
            "Die Anzahl der Punkte pro Dekade überschreitet die Grenze.",
            (("limit", "max_points_per_decade"),),
        )
    explicit = request.explicit_frequencies
    if type(explicit) is not tuple or any(
        type(value) is not ExactRationalValue for value in explicit
    ):
        raise LogFrequencyGridFailure(
            DiagnosticCode.LOG_FREQUENCY_GRID_INVALID_EXPLICIT_FREQUENCIES,
            "Explizite Frequenzen müssen als exaktes Tupel vorliegen.",
        )
    if len(explicit) > limits.max_explicit_points:
        raise LogFrequencyGridFailure(
            DiagnosticCode.LOG_FREQUENCY_GRID_LIMIT_EXCEEDED,
            "Es wurden zu viele explizite Frequenzen angegeben.",
            (("limit", "max_explicit_points"),),
        )
    explicit_values: list[Fraction] = []
    previous: Fraction | None = None
    for value in explicit:
        _validate_rational(
            value,
            limits,
            "explicit_frequency",
            DiagnosticCode.LOG_FREQUENCY_GRID_INVALID_EXPLICIT_FREQUENCIES,
        )
        rational = Fraction(value.numerator, value.denominator)
        if (
            rational <= 0
            or rational < omega_min
            or rational > omega_max
            or (previous is not None and previous >= rational)
        ):
            raise LogFrequencyGridFailure(
                DiagnosticCode.LOG_FREQUENCY_GRID_INVALID_EXPLICIT_FREQUENCIES,
                "Explizite Frequenzen müssen positiv, eindeutig, streng "
                "aufsteigend und innerhalb der Rastergrenzen sein.",
            )
        explicit_values.append(rational)
        previous = rational
    ratio = omega_max / omega_min
    if ratio > Fraction(10**limits.max_decades):
        raise LogFrequencyGridFailure(
            DiagnosticCode.LOG_FREQUENCY_GRID_LIMIT_EXCEEDED,
            "Die logarithmische Dekadenspanne überschreitet die Grenze.",
            (("limit", "max_decades"),),
        )
    request_snapshot = LogFrequencyGridRequest(
        ExactRationalValue(omega_min.numerator, omega_min.denominator),
        ExactRationalValue(omega_max.numerator, omega_max.denominator),
        request.points_per_decade,
        tuple(
            ExactRationalValue(value.numerator, value.denominator)
            for value in explicit_values
        ),
    )
    return ValidatedLogFrequencyGridRequest(
        request_snapshot,
        omega_min,
        omega_max,
        ratio,
        tuple(explicit_values),
    )


def determine_interval_count(
    validated: ValidatedLogFrequencyGridRequest,
    limits: LogFrequencyGridLimits,
    budget: CertificationBudget,
) -> int:
    """Return exact ``ceil(m * log10(r))`` using rational comparisons only."""

    powered_ratio = validated.ratio ** validated.request.points_per_decade
    maximum = limits.max_decades * validated.request.points_per_decade
    power_of_ten = 1
    for interval_count in range(1, maximum + 1):
        budget.step()
        power_of_ten *= 10
        if powered_ratio <= power_of_ten:
            return interval_count
    raise LogFrequencyGridFailure(
        DiagnosticCode.LOG_FREQUENCY_GRID_LIMIT_EXCEEDED,
        "Die benötigte Intervallzahl überschreitet die konfigurierte Grenze.",
        (("limit", "max_decades"),),
    )


def find_exact_target_index(
    explicit: Fraction,
    validated: ValidatedLogFrequencyGridRequest,
    interval_count: int,
    budget: CertificationBudget,
) -> int | None:
    """Find whether an explicit rational is exactly one algebraic target."""

    if explicit == validated.omega_min:
        return 0
    if explicit == validated.omega_max:
        return interval_count
    normalized_power = (explicit / validated.omega_min) ** interval_count
    ratio_power = Fraction(1)
    for target_index in range(interval_count + 1):
        budget.step()
        if normalized_power == ratio_power:
            return target_index
        ratio_power *= validated.ratio
    return None


def validate_total_points(
    interval_count: int,
    exact_target_indices: tuple[int | None, ...],
    limits: LogFrequencyGridLimits,
) -> None:
    """Bound the final point count before any irrational approximation."""

    additional = sum(index is None for index in exact_target_indices)
    if interval_count + 1 + additional > limits.max_total_points:
        raise LogFrequencyGridFailure(
            DiagnosticCode.LOG_FREQUENCY_GRID_LIMIT_EXCEEDED,
            "Das vollständige Raster enthält zu viele Punkte.",
            (("limit", "max_total_points"),),
        )


def validate_output_rational(
    value: Fraction,
    limits: LogFrequencyGridLimits,
) -> None:
    """Bound a rationalized candidate before its public construction."""

    if _integer_exceeds_digits(
        value.numerator,
        limits.max_rational_integer_digits,
    ) or _integer_exceeds_digits(
        value.denominator,
        limits.max_rational_integer_digits,
    ):
        raise LogFrequencyGridFailure(
            DiagnosticCode.LOG_FREQUENCY_GRID_LIMIT_EXCEEDED,
            "Eine rationalisierte Frequenz überschreitet die Zifferngrenze.",
            (("limit", "max_rational_integer_digits"),),
        )


def _validate_rational(
    value: ExactRationalValue,
    limits: LogFrequencyGridLimits,
    field: str,
    invalid_code: DiagnosticCode,
) -> None:
    numerator = value.numerator
    denominator = value.denominator
    if (
        type(numerator) is not int
        or type(denominator) is not int
        or denominator <= 0
        or gcd(abs(numerator), denominator) != 1
    ):
        raise LogFrequencyGridFailure(
            invalid_code,
            "Ein rationaler Rasterwert ist nicht kanonisch.",
            (("field", field),),
        )
    if _integer_exceeds_digits(
        numerator,
        limits.max_rational_integer_digits,
    ) or _integer_exceeds_digits(
        denominator,
        limits.max_rational_integer_digits,
    ):
        raise LogFrequencyGridFailure(
            DiagnosticCode.LOG_FREQUENCY_GRID_LIMIT_EXCEEDED,
            "Ein rationaler Rasterwert überschreitet die Zifferngrenze.",
            (("limit", "max_rational_integer_digits"), ("field", field)),
        )


def _integer_exceeds_digits(value: int, maximum_digits: int) -> bool:
    magnitude = abs(value)
    if magnitude == 0 or magnitude.bit_length() <= maximum_digits:
        return False
    return bool(magnitude >= 10**maximum_digits)


__all__ = [
    "CertificationBudget",
    "LogFrequencyGridFailure",
    "ValidatedLogFrequencyGridRequest",
    "determine_interval_count",
    "find_exact_target_index",
    "validate_log_frequency_grid_request",
    "validate_output_rational",
    "validate_total_points",
]
