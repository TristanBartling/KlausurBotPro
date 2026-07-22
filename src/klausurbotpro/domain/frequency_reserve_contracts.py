"""Immutable contracts for frequency crossovers and stability reserves."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from math import isfinite

from klausurbotpro.domain.diagnostics import Diagnostic


class FrequencyCrossoverType(StrEnum):
    GAIN = "gain"
    PHASE = "phase"


class CrossoverDirection(StrEnum):
    RISING = "rising"
    FALLING = "falling"
    TANGENTIAL = "tangential"
    NUMERICALLY_AMBIGUOUS = "numerically_ambiguous"


class CrossoverDetectionMethod(StrEnum):
    GRID_HIT = "grid_hit"
    BRACKETED_SIGN_CHANGE = "bracketed_sign_change"
    TANGENTIAL_CANDIDATE = "tangential_candidate"


class NumericalQuality(StrEnum):
    VERIFIED = "verified"
    AMBIGUOUS = "ambiguous"


@dataclass(frozen=True, slots=True)
class UnwrappedPhaseTargetRoot:
    """One locally verified root of an arbitrary unwrapped-phase target."""

    frequency: float
    target_phase_degrees: float
    actual_phase_degrees: float
    segment_index: int
    bracket: tuple[float, float]
    detection_method: CrossoverDetectionMethod
    residual_degrees: float

    def __post_init__(self) -> None:
        values = (
            self.frequency,
            self.target_phase_degrees,
            self.actual_phase_degrees,
            self.residual_degrees,
            *self.bracket,
        )
        if any(type(value) is not float or not isfinite(value) for value in values):
            raise ValueError("Phase-target root values must be finite floats.")
        if self.frequency <= 0 or self.residual_degrees < 0:
            raise ValueError("A phase-target root must be positive and verified.")
        if type(self.segment_index) is not int or self.segment_index < 0:
            raise ValueError("segment_index must be nonnegative.")
        if self.bracket[0] > self.frequency or self.frequency > self.bracket[1]:
            raise ValueError("The root must lie inside its bracket.")
        if type(self.detection_method) is not CrossoverDetectionMethod:
            raise TypeError("detection_method has an invalid type.")


class BandCompletenessStatus(StrEnum):
    COMPLETE_IN_PROVEN_RANGE = "complete_in_proven_range"
    BAND_LIMITED = "band_limited"
    SEGMENT_INCOMPLETE = "segment_incomplete"
    NUMERICALLY_AMBIGUOUS = "numerically_ambiguous"


class StabilityReserveType(StrEnum):
    PHASE_MARGIN = "phase_margin"
    GAIN_MARGIN_DB = "gain_margin_db"
    GAIN_MARGIN_FACTOR = "gain_margin_factor"


class ReserveInterpretationStatus(StrEnum):
    FINITE = "finite"
    NEGATIVE = "negative"
    FORMALLY_UNBOUNDED = "formally_unbounded"
    NOT_DEFINED = "not_defined"
    NOT_DETERMINED = "not_determined"


@dataclass(frozen=True, slots=True)
class FrequencyCrossover:
    crossover_type: FrequencyCrossoverType
    frequency: float
    segment_index: int
    complex_value: complex
    magnitude: float
    decibel: float
    principal_phase_degrees: float
    unwrapped_phase_degrees: float
    direction: CrossoverDirection
    detection_method: CrossoverDetectionMethod
    residual: float
    refinement_interval: tuple[float, float]
    numerical_quality: NumericalQuality
    provenance: tuple[str, ...]
    phase_branch_index: int | None = None
    phase_target_degrees: float | None = None

    def __post_init__(self) -> None:
        numeric = (
            self.frequency,
            self.magnitude,
            self.decibel,
            self.principal_phase_degrees,
            self.unwrapped_phase_degrees,
            self.residual,
            *self.refinement_interval,
        )
        if not all(type(value) is float and isfinite(value) for value in numeric):
            raise ValueError("Crossover values must be finite floats.")
        if self.frequency <= 0 or self.magnitude <= 0 or self.segment_index < 0:
            raise ValueError("Crossover frequency, magnitude, and segment are invalid.")
        if len(self.refinement_interval) != 2 or (
            self.refinement_interval[0] > self.frequency
            or self.frequency > self.refinement_interval[1]
        ):
            raise ValueError("The refinement interval must contain the crossover.")
        if not self.provenance or any(type(value) is not str for value in self.provenance):
            raise ValueError("A crossover requires textual provenance.")
        phase_fields = self.phase_branch_index, self.phase_target_degrees
        if self.crossover_type is FrequencyCrossoverType.PHASE:
            if type(phase_fields[0]) is not int or type(phase_fields[1]) is not float:
                raise ValueError("A phase crossover requires branch and target.")
        elif any(value is not None for value in phase_fields):
            raise ValueError("Gain crossovers cannot carry phase-branch fields.")


@dataclass(frozen=True, slots=True)
class FrequencyCrossoverAnalysis:
    gain_crossovers: tuple[FrequencyCrossover, ...]
    phase_crossovers: tuple[FrequencyCrossover, ...]
    evaluated_segments: tuple[int, ...]
    incomplete_segments: tuple[int, ...]
    completeness: BandCompletenessStatus
    diagnostics: tuple[Diagnostic, ...] = ()

    def __post_init__(self) -> None:
        all_crossovers = self.gain_crossovers + self.phase_crossovers
        if any(type(value) is not FrequencyCrossover for value in all_crossovers):
            raise TypeError("Crossover lists contain invalid values.")
        if (
            tuple(sorted(self.gain_crossovers, key=lambda item: item.frequency))
            != self.gain_crossovers
        ):
            raise ValueError("Gain crossovers must be frequency ordered.")
        if (
            tuple(sorted(self.phase_crossovers, key=lambda item: item.frequency))
            != self.phase_crossovers
        ):
            raise ValueError("Phase crossovers must be frequency ordered.")


@dataclass(frozen=True, slots=True)
class StabilityReserve:
    reserve_type: StabilityReserveType
    crossover: FrequencyCrossover | None
    value: float | None
    unit: str
    quality: NumericalQuality
    interpretation: ReserveInterpretationStatus

    def __post_init__(self) -> None:
        if self.value is not None and (type(self.value) is not float or not isfinite(self.value)):
            raise ValueError("A finite reserve value must be a finite float.")
        if not self.unit:
            raise ValueError("A reserve requires a unit.")
        if self.interpretation in (
            ReserveInterpretationStatus.FINITE,
            ReserveInterpretationStatus.NEGATIVE,
        ) and (self.value is None or self.crossover is None):
            raise ValueError("A finite reserve requires value and crossover.")


@dataclass(frozen=True, slots=True)
class StabilityReserveAnalysis:
    phase_margins: tuple[StabilityReserve, ...]
    gain_margins_db: tuple[StabilityReserve, ...]
    gain_margin_factors: tuple[StabilityReserve, ...]
    multiple_crossovers: bool
    completeness: BandCompletenessStatus
    diagnostics: tuple[Diagnostic, ...] = ()


__all__ = [
    "BandCompletenessStatus",
    "CrossoverDetectionMethod",
    "CrossoverDirection",
    "FrequencyCrossover",
    "FrequencyCrossoverAnalysis",
    "FrequencyCrossoverType",
    "NumericalQuality",
    "ReserveInterpretationStatus",
    "StabilityReserve",
    "StabilityReserveAnalysis",
    "StabilityReserveType",
]
