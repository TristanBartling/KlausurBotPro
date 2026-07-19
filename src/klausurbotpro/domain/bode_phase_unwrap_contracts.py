"""Public float- and SymPy-free contracts for optional phase unwrapping."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from klausurbotpro.domain.bode_data_contracts import (
    BodePhaseSegment,
    BodePlotPoint,
    TransferFunctionBodeDataResult,
)
from klausurbotpro.domain.diagnostics import Diagnostic, DiagnosticSeverity


class BodePhaseUnwrapStatus(StrEnum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    NO_PHASE_DATA = "no_phase_data"
    FAILED = "failed"


class BodePhaseUnwrapMethod(StrEnum):
    NEAREST_CONTINUATION = "nearest_continuation"


class BodePhaseUnwrapSegmentBehavior(StrEnum):
    RESET_AT_EACH_SOURCE_SEGMENT = "reset_at_each_source_segment"


class BodePhaseUnwrapTieBreak(StrEnum):
    KEEP_PREVIOUS_OFFSET = "keep_previous_offset"


class BodePhasePrincipalHandling(StrEnum):
    UNCHANGED = "unchanged"


class BodePhaseInterpolation(StrEnum):
    NONE = "none"


@dataclass(frozen=True, slots=True)
class BodePhaseUnwrapLimits:
    max_phase_segments: int = 256
    max_points: int = 256
    max_absolute_phase_turns: int = 256
    max_decimal_digits: int = 64
    max_diagnostics: int = 2048

    def __post_init__(self) -> None:
        for name in self.__dataclass_fields__:
            value = getattr(self, name)
            if type(value) is not int or value <= 0:
                raise ValueError(f"{name} must be a positive int.")


@dataclass(frozen=True, slots=True, init=False)
class BodePhaseUnwrapMetadata:
    phase_period_degrees: int
    method: BodePhaseUnwrapMethod
    segment_behavior: BodePhaseUnwrapSegmentBehavior
    tie_break: BodePhaseUnwrapTieBreak
    principal_phase_handling: BodePhasePrincipalHandling
    interpolation: BodePhaseInterpolation

    def __new__(cls, *args: object, **kwargs: object) -> BodePhaseUnwrapMetadata:
        raise TypeError("Phase-unwrapping metadata is analyzer-controlled.")

    @classmethod
    def _create(cls) -> BodePhaseUnwrapMetadata:
        instance = object.__new__(cls)
        object.__setattr__(instance, "phase_period_degrees", 360)
        object.__setattr__(
            instance,
            "method",
            BodePhaseUnwrapMethod.NEAREST_CONTINUATION,
        )
        object.__setattr__(
            instance,
            "segment_behavior",
            BodePhaseUnwrapSegmentBehavior.RESET_AT_EACH_SOURCE_SEGMENT,
        )
        object.__setattr__(
            instance,
            "tie_break",
            BodePhaseUnwrapTieBreak.KEEP_PREVIOUS_OFFSET,
        )
        object.__setattr__(
            instance,
            "principal_phase_handling",
            BodePhasePrincipalHandling.UNCHANGED,
        )
        object.__setattr__(
            instance,
            "interpolation",
            BodePhaseInterpolation.NONE,
        )
        return instance

    def _validate(self) -> None:
        if self != BodePhaseUnwrapMetadata._create():
            raise ValueError("Phase-unwrapping metadata is not canonical.")


@dataclass(frozen=True, slots=True, init=False)
class BodeUnwrappedPhasePoint:
    source_point: BodePlotPoint
    principal_phase_degrees: str
    phase_offset_turns: int
    unwrapped_phase_degrees: str
    source_segment_index: int
    grid_index: int
    diagnostics: tuple[Diagnostic, ...]

    def __new__(cls, *args: object, **kwargs: object) -> BodeUnwrappedPhasePoint:
        raise TypeError("Unwrapped phase points are analyzer-controlled.")

    @classmethod
    def _create(
        cls,
        *,
        source_point: BodePlotPoint,
        phase_offset_turns: int,
        unwrapped_phase_degrees: str,
        source_segment_index: int,
        grid_index: int,
        diagnostics: tuple[Diagnostic, ...] = (),
    ) -> BodeUnwrappedPhasePoint:
        instance = object.__new__(cls)
        object.__setattr__(instance, "source_point", source_point)
        object.__setattr__(
            instance,
            "principal_phase_degrees",
            source_point.principal_phase_degrees,
        )
        object.__setattr__(instance, "phase_offset_turns", phase_offset_turns)
        object.__setattr__(
            instance,
            "unwrapped_phase_degrees",
            unwrapped_phase_degrees,
        )
        object.__setattr__(
            instance,
            "source_segment_index",
            source_segment_index,
        )
        object.__setattr__(instance, "grid_index", grid_index)
        object.__setattr__(instance, "diagnostics", diagnostics)
        instance._validate()
        return instance

    def _validate(self) -> None:
        if type(self.source_point) is not BodePlotPoint:
            raise TypeError("An unwrapped point requires a BodePlotPoint.")
        if (
            self.source_point.principal_phase_degrees is None
            or self.principal_phase_degrees
            != self.source_point.principal_phase_degrees
            or type(self.principal_phase_degrees) is not str
            or type(self.unwrapped_phase_degrees) is not str
            or type(self.phase_offset_turns) is not int
            or type(self.source_segment_index) is not int
            or self.source_segment_index < 0
            or type(self.grid_index) is not int
            or self.grid_index < 0
            or type(self.diagnostics) is not tuple
            or any(type(item) is not Diagnostic for item in self.diagnostics)
            or any(
                item.severity is DiagnosticSeverity.ERROR
                for item in self.diagnostics
            )
        ):
            raise ValueError("An unwrapped phase point is inconsistent.")


@dataclass(frozen=True, slots=True, init=False)
class BodeUnwrappedPhaseSegment:
    source_segment: BodePhaseSegment
    segment_index: int
    start_grid_index: int
    end_grid_index: int
    points: tuple[BodeUnwrappedPhasePoint, ...]

    def __new__(
        cls,
        *args: object,
        **kwargs: object,
    ) -> BodeUnwrappedPhaseSegment:
        raise TypeError("Unwrapped phase segments are analyzer-controlled.")

    @classmethod
    def _create(
        cls,
        *,
        source_segment: BodePhaseSegment,
        points: tuple[BodeUnwrappedPhasePoint, ...],
    ) -> BodeUnwrappedPhaseSegment:
        instance = object.__new__(cls)
        object.__setattr__(instance, "source_segment", source_segment)
        object.__setattr__(
            instance,
            "segment_index",
            source_segment.segment_index,
        )
        object.__setattr__(
            instance,
            "start_grid_index",
            source_segment.start_grid_index,
        )
        object.__setattr__(
            instance,
            "end_grid_index",
            source_segment.end_grid_index,
        )
        object.__setattr__(instance, "points", points)
        instance._validate()
        return instance

    def _validate(self) -> None:
        if type(self.source_segment) is not BodePhaseSegment:
            raise TypeError("An unwrapped segment requires a BodePhaseSegment.")
        if (
            type(self.segment_index) is not int
            or self.segment_index != self.source_segment.segment_index
            or type(self.start_grid_index) is not int
            or self.start_grid_index != self.source_segment.start_grid_index
            or type(self.end_grid_index) is not int
            or self.end_grid_index != self.source_segment.end_grid_index
            or type(self.points) is not tuple
            or not self.points
            or len(self.points) != len(self.source_segment.points)
            or any(
                type(point) is not BodeUnwrappedPhasePoint
                for point in self.points
            )
        ):
            raise ValueError("An unwrapped phase segment is inconsistent.")


@dataclass(frozen=True, slots=True, init=False)
class BodePhaseUnwrapResult:
    status: BodePhaseUnwrapStatus
    source_bode_data: TransferFunctionBodeDataResult | None
    segments: tuple[BodeUnwrappedPhaseSegment, ...]
    metadata: BodePhaseUnwrapMetadata | None
    diagnostics: tuple[Diagnostic, ...]

    def __new__(cls, *args: object, **kwargs: object) -> BodePhaseUnwrapResult:
        raise TypeError("Phase-unwrapping results are analyzer-controlled.")

    @classmethod
    def _create(
        cls,
        *,
        status: BodePhaseUnwrapStatus,
        source_bode_data: TransferFunctionBodeDataResult | None = None,
        segments: tuple[BodeUnwrappedPhaseSegment, ...] = (),
        metadata: BodePhaseUnwrapMetadata | None = None,
        diagnostics: tuple[Diagnostic, ...] = (),
    ) -> BodePhaseUnwrapResult:
        instance = object.__new__(cls)
        object.__setattr__(instance, "status", status)
        object.__setattr__(instance, "source_bode_data", source_bode_data)
        object.__setattr__(instance, "segments", segments)
        object.__setattr__(instance, "metadata", metadata)
        object.__setattr__(instance, "diagnostics", diagnostics)
        instance._validate()
        return instance

    def _validate(self) -> None:
        if type(self.status) is not BodePhaseUnwrapStatus:
            raise TypeError("An unwrap result requires a supported status.")
        if (
            type(self.segments) is not tuple
            or any(
                type(segment) is not BodeUnwrappedPhaseSegment
                for segment in self.segments
            )
            or type(self.diagnostics) is not tuple
            or any(type(item) is not Diagnostic for item in self.diagnostics)
        ):
            raise TypeError("An unwrap result contains invalid tuple contracts.")
        has_error = any(
            item.severity is DiagnosticSeverity.ERROR
            for item in self.diagnostics
        )
        if self.status is BodePhaseUnwrapStatus.FAILED:
            if (
                self.source_bode_data is not None
                or self.segments
                or self.metadata is not None
                or not has_error
            ):
                raise ValueError("A failed unwrap result must be value-free.")
            return
        if (
            type(self.source_bode_data) is not TransferFunctionBodeDataResult
            or type(self.metadata) is not BodePhaseUnwrapMetadata
            or has_error
        ):
            raise ValueError("A successful unwrap result needs validated context.")
        if self.status is BodePhaseUnwrapStatus.NO_PHASE_DATA:
            if self.segments:
                raise ValueError("NO_PHASE_DATA must not contain segments.")
        elif not self.segments:
            raise ValueError("A plottable unwrap result requires segments.")

    @property
    def succeeded(self) -> bool:
        return self.status is not BodePhaseUnwrapStatus.FAILED


__all__ = [
    "BodePhaseInterpolation",
    "BodePhasePrincipalHandling",
    "BodePhaseUnwrapLimits",
    "BodePhaseUnwrapMetadata",
    "BodePhaseUnwrapMethod",
    "BodePhaseUnwrapResult",
    "BodePhaseUnwrapSegmentBehavior",
    "BodePhaseUnwrapStatus",
    "BodePhaseUnwrapTieBreak",
    "BodeUnwrappedPhasePoint",
    "BodeUnwrappedPhaseSegment",
]
