"""Public SymPy- and float-free contracts for structured Bode plot data."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from klausurbotpro.domain.diagnostics import Diagnostic, DiagnosticSeverity
from klausurbotpro.domain.frequency_response_contracts import (
    DecibelValueKind,
    FrequencyResponsePoint,
    FrequencyResponsePointStatus,
    NumericalDecibelValue,
    TransferFunctionFrequencyResponseResult,
)
from klausurbotpro.domain.log_frequency_grid_contracts import (
    LogFrequencyGridPoint,
    LogFrequencyGridResult,
    ScientificDecimal,
)
from klausurbotpro.domain.parameter_substitutions import ExactRationalValue


class BodeDataStatus(StrEnum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    NO_PLOTTABLE_DATA = "no_plottable_data"
    SYMBOLIC_UNDETERMINED = "symbolic_undetermined"
    FAILED = "failed"


class BodeFrequencyQuantity(StrEnum):
    ANGULAR_FREQUENCY = "angular_frequency"


class BodeFrequencyUnit(StrEnum):
    RAD_PER_SECOND = "rad_per_second"


class BodeFrequencyScale(StrEnum):
    LOGARITHMIC = "logarithmic"


class BodeMagnitudeQuantity(StrEnum):
    DECIBEL = "decibel"


class BodePhaseUnit(StrEnum):
    DEGREE = "degree"


class BodePhaseConvention(StrEnum):
    PRINCIPAL_MINUS_180_EXCLUSIVE_TO_180_INCLUSIVE = (
        "principal_minus_180_exclusive_to_180_inclusive"
    )


@dataclass(frozen=True, slots=True)
class BodeDataLimits:
    """Finite projection and segmentation limits; no hard timeout is implied."""

    max_grid_points: int = 256
    max_magnitude_segments: int = 256
    max_phase_segments: int = 256
    max_diagnostics: int = 1024
    max_plot_decimal_digits: int = 40

    def __post_init__(self) -> None:
        for name in self.__dataclass_fields__:
            value = getattr(self, name)
            if type(value) is not int or value <= 0:
                raise ValueError(f"{name} must be a positive int.")


@dataclass(frozen=True, slots=True, init=False)
class BodeAxisMetadata:
    frequency_quantity: BodeFrequencyQuantity
    frequency_unit: BodeFrequencyUnit
    frequency_scale: BodeFrequencyScale
    magnitude_quantity: BodeMagnitudeQuantity
    phase_unit: BodePhaseUnit
    phase_convention: BodePhaseConvention

    def __new__(cls, *args: object, **kwargs: object) -> BodeAxisMetadata:
        raise TypeError("Bode axis metadata must be created by the analyzer.")

    @classmethod
    def _create(cls) -> BodeAxisMetadata:
        instance = object.__new__(cls)
        object.__setattr__(
            instance,
            "frequency_quantity",
            BodeFrequencyQuantity.ANGULAR_FREQUENCY,
        )
        object.__setattr__(
            instance,
            "frequency_unit",
            BodeFrequencyUnit.RAD_PER_SECOND,
        )
        object.__setattr__(
            instance,
            "frequency_scale",
            BodeFrequencyScale.LOGARITHMIC,
        )
        object.__setattr__(
            instance,
            "magnitude_quantity",
            BodeMagnitudeQuantity.DECIBEL,
        )
        object.__setattr__(instance, "phase_unit", BodePhaseUnit.DEGREE)
        object.__setattr__(
            instance,
            "phase_convention",
            BodePhaseConvention.PRINCIPAL_MINUS_180_EXCLUSIVE_TO_180_INCLUSIVE,
        )
        return instance


@dataclass(frozen=True, slots=True, init=False)
class BodePlotPoint:
    grid_point: LogFrequencyGridPoint
    frequency_response_point: FrequencyResponsePoint
    evaluation_frequency: ExactRationalValue
    target_decimal: ScientificDecimal
    numerical_decibel: NumericalDecibelValue | None
    principal_phase_degrees: str | None
    magnitude_plottable: bool
    phase_plottable: bool
    diagnostics: tuple[Diagnostic, ...]

    def __new__(cls, *args: object, **kwargs: object) -> BodePlotPoint:
        raise TypeError("Bode plot points must be created by the analyzer.")

    @classmethod
    def _create(
        cls,
        *,
        grid_point: LogFrequencyGridPoint,
        frequency_response_point: FrequencyResponsePoint,
        diagnostics: tuple[Diagnostic, ...] = (),
    ) -> BodePlotPoint:
        instance = object.__new__(cls)
        status = frequency_response_point.status
        is_defined = status is FrequencyResponsePointStatus.DEFINED
        object.__setattr__(instance, "grid_point", grid_point)
        object.__setattr__(
            instance,
            "frequency_response_point",
            frequency_response_point,
        )
        object.__setattr__(
            instance,
            "evaluation_frequency",
            grid_point.evaluation_frequency,
        )
        object.__setattr__(instance, "target_decimal", grid_point.target_decimal)
        object.__setattr__(
            instance,
            "numerical_decibel",
            frequency_response_point.numerical_decibel,
        )
        object.__setattr__(
            instance,
            "principal_phase_degrees",
            frequency_response_point.numerical_phase_degrees,
        )
        object.__setattr__(instance, "magnitude_plottable", is_defined)
        object.__setattr__(instance, "phase_plottable", is_defined)
        object.__setattr__(instance, "diagnostics", diagnostics)
        instance._validate()
        return instance

    def _validate(self) -> None:
        if (
            type(self.grid_point) is not LogFrequencyGridPoint
            or type(self.frequency_response_point) is not FrequencyResponsePoint
            or type(self.evaluation_frequency) is not ExactRationalValue
            or type(self.target_decimal) is not ScientificDecimal
        ):
            raise TypeError("A Bode plot point contains invalid contracts.")
        self.grid_point._validate()
        self.frequency_response_point._validate()
        if (
            self.evaluation_frequency
            != self.grid_point.evaluation_frequency
            or self.evaluation_frequency != self.frequency_response_point.omega
            or self.target_decimal != self.grid_point.target_decimal
            or self.numerical_decibel
            is not self.frequency_response_point.numerical_decibel
            or self.principal_phase_degrees
            != self.frequency_response_point.numerical_phase_degrees
        ):
            raise ValueError("Bode point and source contracts do not match.")
        if (
            type(self.magnitude_plottable) is not bool
            or type(self.phase_plottable) is not bool
            or type(self.diagnostics) is not tuple
            or any(type(item) is not Diagnostic for item in self.diagnostics)
            or any(
                item.severity is DiagnosticSeverity.ERROR
                for item in self.diagnostics
            )
        ):
            raise ValueError("Bode point flags or diagnostics are invalid.")
        status = self.frequency_response_point.status
        if status is FrequencyResponsePointStatus.DEFINED:
            if (
                not self.magnitude_plottable
                or not self.phase_plottable
                or self.numerical_decibel is None
                or self.numerical_decibel.kind is not DecibelValueKind.FINITE
                or self.principal_phase_degrees is None
            ):
                raise ValueError("A defined Bode point must be fully plottable.")
        elif status is FrequencyResponsePointStatus.ZERO_RESPONSE:
            if (
                self.magnitude_plottable
                or self.phase_plottable
                or self.numerical_decibel is None
                or self.numerical_decibel.kind
                is not DecibelValueKind.NEGATIVE_INFINITY
                or self.principal_phase_degrees is not None
            ):
                raise ValueError("A zero response must interrupt both Bode series.")
        elif (
            self.magnitude_plottable
            or self.phase_plottable
            or self.numerical_decibel is not None
            or self.principal_phase_degrees is not None
        ):
            raise ValueError("An undefined response must not invent Bode values.")


@dataclass(frozen=True, slots=True, init=False)
class BodeMagnitudeSegment:
    segment_index: int
    points: tuple[BodePlotPoint, ...]
    start_grid_index: int
    end_grid_index: int

    def __new__(cls, *args: object, **kwargs: object) -> BodeMagnitudeSegment:
        raise TypeError("Bode magnitude segments must be created by the analyzer.")

    @classmethod
    def _create(
        cls,
        segment_index: int,
        points: tuple[BodePlotPoint, ...],
        start_grid_index: int,
        end_grid_index: int,
    ) -> BodeMagnitudeSegment:
        instance = object.__new__(cls)
        for name, value in (
            ("segment_index", segment_index),
            ("points", points),
            ("start_grid_index", start_grid_index),
            ("end_grid_index", end_grid_index),
        ):
            object.__setattr__(instance, name, value)
        instance._validate()
        return instance

    def _validate(self) -> None:
        _validate_segment_fields(self)
        if any(
            not point.magnitude_plottable
            or point.numerical_decibel is None
            or point.numerical_decibel.kind is not DecibelValueKind.FINITE
            for point in self.points
        ):
            raise ValueError("Magnitude segments require finite plottable points.")


@dataclass(frozen=True, slots=True, init=False)
class BodePhaseSegment:
    segment_index: int
    points: tuple[BodePlotPoint, ...]
    start_grid_index: int
    end_grid_index: int

    def __new__(cls, *args: object, **kwargs: object) -> BodePhaseSegment:
        raise TypeError("Bode phase segments must be created by the analyzer.")

    @classmethod
    def _create(
        cls,
        segment_index: int,
        points: tuple[BodePlotPoint, ...],
        start_grid_index: int,
        end_grid_index: int,
    ) -> BodePhaseSegment:
        instance = object.__new__(cls)
        for name, value in (
            ("segment_index", segment_index),
            ("points", points),
            ("start_grid_index", start_grid_index),
            ("end_grid_index", end_grid_index),
        ):
            object.__setattr__(instance, name, value)
        instance._validate()
        return instance

    def _validate(self) -> None:
        _validate_segment_fields(self)
        if any(
            not point.phase_plottable
            or point.principal_phase_degrees is None
            for point in self.points
        ):
            raise ValueError("Phase segments require plottable principal phases.")


@dataclass(frozen=True, slots=True, init=False)
class TransferFunctionBodeDataResult:
    status: BodeDataStatus
    grid: LogFrequencyGridResult | None
    frequency_response_result: TransferFunctionFrequencyResponseResult | None
    points: tuple[BodePlotPoint, ...]
    magnitude_segments: tuple[BodeMagnitudeSegment, ...]
    phase_segments: tuple[BodePhaseSegment, ...]
    axis_metadata: BodeAxisMetadata | None
    diagnostics: tuple[Diagnostic, ...]

    def __new__(
        cls,
        *args: object,
        **kwargs: object,
    ) -> TransferFunctionBodeDataResult:
        raise TypeError("Bode data results must be created by the analyzer.")

    @classmethod
    def _create(
        cls,
        *,
        status: BodeDataStatus,
        grid: LogFrequencyGridResult | None = None,
        frequency_response_result: (
            TransferFunctionFrequencyResponseResult | None
        ) = None,
        points: tuple[BodePlotPoint, ...] = (),
        magnitude_segments: tuple[BodeMagnitudeSegment, ...] = (),
        phase_segments: tuple[BodePhaseSegment, ...] = (),
        axis_metadata: BodeAxisMetadata | None = None,
        diagnostics: tuple[Diagnostic, ...] = (),
    ) -> TransferFunctionBodeDataResult:
        instance = object.__new__(cls)
        for name, value in (
            ("status", status),
            ("grid", grid),
            ("frequency_response_result", frequency_response_result),
            ("points", points),
            ("magnitude_segments", magnitude_segments),
            ("phase_segments", phase_segments),
            ("axis_metadata", axis_metadata),
            ("diagnostics", diagnostics),
        ):
            object.__setattr__(instance, name, value)
        instance._validate()
        return instance

    def _validate(self) -> None:
        if type(self.status) is not BodeDataStatus:
            raise TypeError("A Bode result requires a supported status.")
        tuple_contracts = (
            (self.points, BodePlotPoint),
            (self.magnitude_segments, BodeMagnitudeSegment),
            (self.phase_segments, BodePhaseSegment),
            (self.diagnostics, Diagnostic),
        )
        if any(
            type(values) is not tuple
            or any(type(value) is not expected for value in values)
            for values, expected in tuple_contracts
        ):
            raise TypeError("A Bode result contains invalid tuple contracts.")
        has_error = any(
            diagnostic.severity is DiagnosticSeverity.ERROR
            for diagnostic in self.diagnostics
        )
        if self.status is BodeDataStatus.FAILED:
            if (
                self.grid is not None
                or self.frequency_response_result is not None
                or self.points
                or self.magnitude_segments
                or self.phase_segments
                or self.axis_metadata is not None
                or not has_error
            ):
                raise ValueError("A failed Bode result must be value-free.")
            return
        if (
            type(self.grid) is not LogFrequencyGridResult
            or type(self.frequency_response_result)
            is not TransferFunctionFrequencyResponseResult
            or not self.points
            or type(self.axis_metadata) is not BodeAxisMetadata
            or has_error
        ):
            raise ValueError("A successful Bode result requires complete context.")

    @property
    def succeeded(self) -> bool:
        return self.status is not BodeDataStatus.FAILED


def _validate_segment_fields(
    segment: BodeMagnitudeSegment | BodePhaseSegment,
) -> None:
    if (
        type(segment.segment_index) is not int
        or segment.segment_index < 0
        or type(segment.start_grid_index) is not int
        or type(segment.end_grid_index) is not int
        or segment.start_grid_index < 0
        or segment.end_grid_index < segment.start_grid_index
        or type(segment.points) is not tuple
        or not segment.points
        or any(type(point) is not BodePlotPoint for point in segment.points)
        or len(segment.points)
        != segment.end_grid_index - segment.start_grid_index + 1
    ):
        raise ValueError("A Bode segment has invalid bounds or points.")


__all__ = [
    "BodeAxisMetadata",
    "BodeDataLimits",
    "BodeDataStatus",
    "BodeFrequencyQuantity",
    "BodeFrequencyScale",
    "BodeFrequencyUnit",
    "BodeMagnitudeQuantity",
    "BodeMagnitudeSegment",
    "BodePhaseConvention",
    "BodePhaseSegment",
    "BodePhaseUnit",
    "BodePlotPoint",
    "TransferFunctionBodeDataResult",
]
