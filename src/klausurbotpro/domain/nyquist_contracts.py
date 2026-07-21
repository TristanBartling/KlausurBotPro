"""Immutable contracts for Nyquist analysis and scalar-gain ranges."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from math import isfinite

from klausurbotpro.domain.diagnostics import Diagnostic


class PoleClassificationStatus(StrEnum):
    UNIQUE = "unique"
    AMBIGUOUS = "ambiguous"


class NyquistClosureStatus(StrEnum):
    CLOSED = "closed"
    OPEN = "open"
    UNSUPPORTED = "unsupported"


class CriticalPointStatus(StrEnum):
    CLEAR = "clear"
    NEAR = "near_critical"
    HIT = "critical_hit"


class NyquistNumericalQuality(StrEnum):
    VERIFIED = "verified"
    AMBIGUOUS = "numerically_ambiguous"
    NOT_APPLICABLE = "not_applicable"


class ClosedLoopStabilityStatus(StrEnum):
    ASYMPTOTICALLY_STABLE = "asymptotically_stable"
    UNSTABLE = "unstable"
    CRITICAL = "critical"
    NOT_DETERMINED = "not_determined"


class NyquistCriterion(StrEnum):
    COMPLETE = "complete"
    SIMPLIFIED = "simplified"
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True, slots=True)
class ClassifiedPole:
    value: complex
    multiplicity: int


@dataclass(frozen=True, slots=True)
class OpenLoopPoleClassification:
    lhp_poles: tuple[ClassifiedPole, ...]
    rhp_poles: tuple[ClassifiedPole, ...]
    imaginary_axis_poles: tuple[ClassifiedPole, ...]
    origin_poles: tuple[ClassifiedPole, ...]
    rhp_pole_count: int
    status: PoleClassificationStatus
    minimum_real_axis_distance: float
    cancellation_warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class NyquistCurveSegment:
    segment_index: int
    frequency_sign: int
    frequencies: tuple[float, ...]
    values: tuple[complex, ...]

    def __post_init__(self) -> None:
        if self.frequency_sign not in (-1, 1) or not self.values:
            raise ValueError("A Nyquist segment requires one frequency half.")
        if len(self.frequencies) != len(self.values):
            raise ValueError("Nyquist frequencies and values must align.")


@dataclass(frozen=True, slots=True)
class NyquistCriticalPoint:
    value: complex
    minimum_distance: float
    frequency: float
    status: CriticalPointStatus


@dataclass(frozen=True, slots=True)
class NyquistWindingResult:
    curve_segments: tuple[NyquistCurveSegment, ...]
    critical_point: NyquistCriticalPoint
    internal_ccw_winding: int | None
    clockwise_encirclements: int | None
    polygon_clockwise_encirclements: int | None
    closure_status: NyquistClosureStatus
    band_complete: bool
    quality: NyquistNumericalQuality
    diagnostics: tuple[Diagnostic, ...] = ()


@dataclass(frozen=True, slots=True)
class NyquistStabilityStatement:
    rhp_open_poles: int
    clockwise_encirclements: int | None
    rhp_closed_poles: int | None
    criterion: NyquistCriterion
    simplified_applicable: bool
    prerequisites_met: bool
    status: ClosedLoopStabilityStatus
    statement: str


@dataclass(frozen=True, slots=True)
class ScalarGainDomain:
    lower: float | None
    upper: float | None
    lower_inclusive: bool = False
    upper_inclusive: bool = False

    def __post_init__(self) -> None:
        for value in (self.lower, self.upper):
            if value is not None and not isfinite(value):
                raise ValueError("Gain-domain bounds must be finite or absent.")
        if self.lower is not None and self.upper is not None and self.lower >= self.upper:
            raise ValueError("The gain-domain lower bound must precede the upper bound.")


@dataclass(frozen=True, slots=True)
class ScalarGainIntervalResult:
    domain: ScalarGainDomain
    test_gain: float
    rhp_open_poles: int
    clockwise_encirclements: int
    rhp_closed_poles: int
    stable: bool


@dataclass(frozen=True, slots=True)
class ScalarGainRangeResult:
    requested_domain: ScalarGainDomain
    critical_gains: tuple[float, ...]
    intervals: tuple[ScalarGainIntervalResult, ...]
    stable_intervals: tuple[ScalarGainDomain, ...]
    complete: bool
    diagnostics: tuple[Diagnostic, ...] = ()


@dataclass(frozen=True, slots=True)
class NyquistAnalysisResult:
    pole_classification: OpenLoopPoleClassification
    winding: NyquistWindingResult
    stability: NyquistStabilityStatement
    scalar_gain_range: ScalarGainRangeResult | None = None


__all__ = [name for name in globals() if not name.startswith("_")]
