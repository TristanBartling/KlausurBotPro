"""Defensive validation for Bode projection inputs and completed results."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from klausurbotpro.domain._bode_data_segmentation import build_bode_segments
from klausurbotpro.domain._bode_data_status import derive_bode_data_status
from klausurbotpro.domain._frequency_response_result_validation import (
    validate_frequency_response_result,
)
from klausurbotpro.domain._frequency_response_validation import (
    FrequencyResponseFailure,
    validate_frequency_response_context,
)
from klausurbotpro.domain._log_frequency_grid_result_validation import (
    validate_log_frequency_grid_result,
)
from klausurbotpro.domain._log_frequency_grid_validation import (
    LogFrequencyGridFailure,
)
from klausurbotpro.domain.bode_data_contracts import (
    BodeAxisMetadata,
    BodeDataLimits,
    BodeDataStatus,
    BodeMagnitudeSegment,
    BodePhaseSegment,
    BodePlotPoint,
    TransferFunctionBodeDataResult,
)
from klausurbotpro.domain.diagnostics import (
    Diagnostic,
    DiagnosticCode,
    DiagnosticSeverity,
)
from klausurbotpro.domain.frequency_response_contracts import (
    FrequencyResponseLimits,
    FrequencySampleSet,
    TransferFunctionFrequencyResponseResult,
    TransferFunctionFrequencyResponseStatus,
)
from klausurbotpro.domain.log_frequency_grid_contracts import (
    LogFrequencyGridLimits,
    LogFrequencyGridResult,
    LogFrequencyGridStatus,
)
from klausurbotpro.domain.parameter_substitutions import ParameterSubstitutions
from klausurbotpro.domain.reduced_transfer_function import (
    ReducedTransferFunction,
)

_NESTED_ERRORS = (AttributeError, IndexError, TypeError, ValueError)


@dataclass(frozen=True, slots=True)
class BodeDataFailure(ValueError):
    code: DiagnosticCode
    message: str
    details: tuple[tuple[str, str], ...] = ()


def validate_bode_input_grid(
    grid: LogFrequencyGridResult,
    *,
    grid_limits: LogFrequencyGridLimits,
    frequency_limits: FrequencyResponseLimits,
    bode_limits: BodeDataLimits,
) -> None:
    try:
        validate_log_frequency_grid_result(grid, grid_limits)
    except (LogFrequencyGridFailure, TypeError) as error:
        raise BodeDataFailure(
            DiagnosticCode.BODE_DATA_INVALID_GRID,
            "Das logarithmische Raster ist ungültig.",
            (("cause", type(error).__name__),),
        ) from error
    if grid.status is not LogFrequencyGridStatus.COMPLETE:
        raise BodeDataFailure(
            DiagnosticCode.BODE_DATA_INVALID_GRID,
            "Ein Bode-Datensatz benötigt ein vollständiges Raster.",
        )
    active_limit_name, active_limit_value = min(
        (
            ("max_grid_points", bode_limits.max_grid_points),
            (
                "max_frequency_points",
                frequency_limits.max_frequency_points,
            ),
        ),
        key=lambda item: item[1],
    )
    if len(grid.points) > active_limit_value:
        raise BodeDataFailure(
            DiagnosticCode.BODE_DATA_LIMIT_EXCEEDED,
            "Das Raster enthält zu viele Bode-Punkte.",
            (("limit", active_limit_name),),
        )


def validate_frequency_handoff(
    result: TransferFunctionFrequencyResponseResult,
    *,
    reduced: ReducedTransferFunction,
    sample_set: FrequencySampleSet,
    substitutions: ParameterSubstitutions | None,
    limits: FrequencyResponseLimits,
) -> None:
    try:
        validate_frequency_response_result(result, limits)
        if result.status is TransferFunctionFrequencyResponseStatus.FAILED:
            return
        normalized, _, _ = validate_frequency_response_context(
            reduced,
            sample_set,
            substitutions,
            limits,
        )
    except (FrequencyResponseFailure, TypeError) as error:
        raise BodeDataFailure(
            DiagnosticCode.BODE_DATA_CONTEXT_MISMATCH,
            "Die Phase-3A.1-Übergabe ist ungültig.",
            (("cause", type(error).__name__),),
        ) from error
    if (
        result.reduced_transfer_function is not reduced
        or result.frequencies is not sample_set
        or result.substitutions != normalized
        or len(result.points) != len(sample_set.frequencies)
        or tuple(point.omega for point in result.points)
        != sample_set.frequencies
    ):
        raise BodeDataFailure(
            DiagnosticCode.BODE_DATA_CONTEXT_MISMATCH,
            "Raster und Phase-3A.1-Ergebnis passen nicht exakt zusammen.",
        )


def validate_plot_decimal_limits(
    points: tuple[BodePlotPoint, ...],
    limits: BodeDataLimits,
) -> None:
    for point in points:
        if point.target_decimal.significand >= 10**limits.max_plot_decimal_digits:
            raise _plot_decimal_limit()
        values = (
            (
                point.numerical_decibel.decimal_value
                if point.numerical_decibel is not None
                else None
            ),
            point.principal_phase_degrees,
        )
        for value in values:
            if value is not None and _decimal_digit_count(value) > (
                limits.max_plot_decimal_digits
            ):
                raise _plot_decimal_limit()


def validate_bode_data_result(
    result: TransferFunctionBodeDataResult,
    *,
    frequency_limits: FrequencyResponseLimits,
    grid_limits: LogFrequencyGridLimits,
    bode_limits: BodeDataLimits,
) -> None:
    if type(result) is not TransferFunctionBodeDataResult:
        raise TypeError("result must be TransferFunctionBodeDataResult.")
    try:
        _validate_bode_result(
            result,
            frequency_limits=frequency_limits,
            grid_limits=grid_limits,
            bode_limits=bode_limits,
        )
    except BodeDataFailure:
        raise
    except _NESTED_ERRORS as error:
        raise BodeDataFailure(
            DiagnosticCode.BODE_DATA_INVALID_INPUT,
            "Das Bode-Datenergebnis ist manipuliert.",
            (("exception", type(error).__name__),),
        ) from error


def _validate_bode_result(
    result: TransferFunctionBodeDataResult,
    *,
    frequency_limits: FrequencyResponseLimits,
    grid_limits: LogFrequencyGridLimits,
    bode_limits: BodeDataLimits,
) -> None:
    result._validate()
    _validate_diagnostics(
        result.diagnostics,
        bode_limits,
        allow_errors=result.status is BodeDataStatus.FAILED,
    )
    if result.status is BodeDataStatus.FAILED:
        return
    if result.grid is None or result.frequency_response_result is None:
        raise BodeDataFailure(
            DiagnosticCode.BODE_DATA_INVALID_INPUT,
            "Ein erfolgreiches Bode-Ergebnis benötigt vollständigen Kontext.",
        )
    validate_bode_input_grid(
        result.grid,
        grid_limits=grid_limits,
        frequency_limits=frequency_limits,
        bode_limits=bode_limits,
    )
    validate_frequency_response_result(
        result.frequency_response_result,
        frequency_limits,
    )
    expected_frequencies = tuple(
        point.evaluation_frequency for point in result.grid.points
    )
    response = result.frequency_response_result
    if (
        response.frequencies is None
        or response.frequencies.frequencies != expected_frequencies
        or len(result.points) != len(result.grid.points)
        or len(result.points) != len(response.points)
    ):
        raise BodeDataFailure(
            DiagnosticCode.BODE_DATA_CONTEXT_MISMATCH,
            "Das Bode-Ergebnis besitzt keine vollständige Punktzuordnung.",
        )
    for index, point in enumerate(result.points):
        point._validate()
        if (
            point.grid_point is not result.grid.points[index]
            or point.frequency_response_point is not response.points[index]
            or point.diagnostics
        ):
            raise BodeDataFailure(
                DiagnosticCode.BODE_DATA_CONTEXT_MISMATCH,
                "Ein Bode-Punkt stammt nicht aus der geordneten Übergabe.",
            )
    validate_plot_decimal_limits(result.points, bode_limits)
    _validate_segment_origins(
        result.magnitude_segments,
        result.points,
    )
    _validate_segment_origins(
        result.phase_segments,
        result.points,
    )
    magnitude, phase = build_bode_segments(result.points)
    if (
        result.magnitude_segments != magnitude
        or result.phase_segments != phase
        or len(magnitude) > bode_limits.max_magnitude_segments
        or len(phase) > bode_limits.max_phase_segments
    ):
        raise BodeDataFailure(
            DiagnosticCode.BODE_DATA_LIMIT_EXCEEDED,
            "Bode-Segmente sind inkonsistent oder überschreiten Grenzen.",
        )
    expected_status = derive_bode_data_status(
        tuple(point.status for point in response.points)
    )
    if result.status is not expected_status:
        raise BodeDataFailure(
            DiagnosticCode.BODE_DATA_CONTEXT_MISMATCH,
            "Der Bode-Gesamtstatus ist inkonsistent.",
        )
    _validate_status_shape(result, expected_status)
    if result.axis_metadata != BodeAxisMetadata._create():
        raise BodeDataFailure(
            DiagnosticCode.BODE_DATA_CONTEXT_MISMATCH,
            "Die Bode-Achsenmetadaten sind inkonsistent.",
        )
    prefix = result.grid.diagnostics + response.diagnostics
    if result.diagnostics[: len(prefix)] != prefix:
        raise BodeDataFailure(
            DiagnosticCode.BODE_DATA_CONTEXT_MISMATCH,
            "Die Bode-Diagnoseaggregation ist inkonsistent.",
        )
    tail = result.diagnostics[len(prefix) :]
    if expected_status is BodeDataStatus.NO_PLOTTABLE_DATA:
        if (
            len(tail) != 1
            or tail[0].code is not DiagnosticCode.BODE_DATA_NO_PLOTTABLE_DATA
            or tail[0].severity is DiagnosticSeverity.ERROR
        ):
            raise BodeDataFailure(
                DiagnosticCode.BODE_DATA_CONTEXT_MISMATCH,
                "Der Hinweis auf nicht plotbare Daten fehlt.",
            )
    elif tail:
        raise BodeDataFailure(
            DiagnosticCode.BODE_DATA_CONTEXT_MISMATCH,
            "Das Bode-Ergebnis enthält fremde globale Diagnosen.",
        )


def _validate_diagnostics(
    diagnostics: tuple[Diagnostic, ...],
    limits: BodeDataLimits,
    *,
    allow_errors: bool,
) -> None:
    if type(diagnostics) is not tuple or any(
        type(item) is not Diagnostic for item in diagnostics
    ):
        raise BodeDataFailure(
            DiagnosticCode.BODE_DATA_INVALID_INPUT,
            "Bode-Diagnosen müssen ein exaktes Tupel bilden.",
        )
    if len(diagnostics) > limits.max_diagnostics:
        raise BodeDataFailure(
            DiagnosticCode.BODE_DATA_LIMIT_EXCEEDED,
            "Das Bode-Ergebnis enthält zu viele Diagnosen.",
            (("limit", "max_diagnostics"),),
        )
    for diagnostic in diagnostics:
        if (
            type(diagnostic.severity) is not DiagnosticSeverity
            or type(diagnostic.code) is not DiagnosticCode
            or type(diagnostic.message) is not str
            or not diagnostic.message.strip()
            or (
                diagnostic.field is not None
                and type(diagnostic.field) is not str
            )
            or type(diagnostic.technical_details) is not tuple
            or any(
                type(detail) is not tuple
                or len(detail) != 2
                or any(type(value) is not str for value in detail)
                for detail in diagnostic.technical_details
            )
        ):
            raise BodeDataFailure(
                DiagnosticCode.BODE_DATA_INVALID_INPUT,
                "Eine Bode-Diagnose ist manipuliert.",
            )
    if not allow_errors and any(
        diagnostic.severity is DiagnosticSeverity.ERROR
        for diagnostic in diagnostics
    ):
        raise BodeDataFailure(
            DiagnosticCode.BODE_DATA_INVALID_INPUT,
            "Ein erfolgreiches Bode-Ergebnis darf keinen Fehler enthalten.",
        )


def _validate_segment_origins(
    segments: tuple[BodeMagnitudeSegment | BodePhaseSegment, ...],
    points: tuple[BodePlotPoint, ...],
) -> None:
    seen_point_ids: set[int] = set()
    for expected_segment_index, segment in enumerate(segments):
        try:
            segment._validate()
            segment_index = segment.segment_index
            start = segment.start_grid_index
            end = segment.end_grid_index
            segment_points = segment.points
        except (AttributeError, IndexError, TypeError, ValueError) as error:
            raise BodeDataFailure(
                DiagnosticCode.BODE_DATA_CONTEXT_MISMATCH,
                "Ein Bode-Segment ist manipuliert.",
                (("exception", type(error).__name__),),
            ) from error
        if (
            segment_index != expected_segment_index
            or start < 0
            or end < start
            or end >= len(points)
            or len(segment_points) != end - start + 1
        ):
            raise BodeDataFailure(
                DiagnosticCode.BODE_DATA_CONTEXT_MISMATCH,
                "Bode-Segmentindizes oder -grenzen sind inkonsistent.",
            )
        for local_index, segment_point in enumerate(segment_points):
            source_point = points[start + local_index]
            point_id = id(segment_point)
            if segment_point is not source_point or point_id in seen_point_ids:
                raise BodeDataFailure(
                    DiagnosticCode.BODE_DATA_CONTEXT_MISMATCH,
                    "Bode-Segmentpunkte stammen nicht identisch aus der "
                    "geordneten Ergebnisfolge.",
                )
            seen_point_ids.add(point_id)


def _validate_status_shape(
    result: TransferFunctionBodeDataResult,
    status: BodeDataStatus,
) -> None:
    if status is BodeDataStatus.COMPLETE and (
        len(result.magnitude_segments) != 1
        or len(result.phase_segments) != 1
        or result.magnitude_segments[0].points != result.points
        or result.phase_segments[0].points != result.points
    ):
        raise BodeDataFailure(
            DiagnosticCode.BODE_DATA_CONTEXT_MISMATCH,
            "Vollständige Bode-Daten benötigen zwei vollständige Segmente.",
        )
    if status in (
        BodeDataStatus.NO_PLOTTABLE_DATA,
        BodeDataStatus.SYMBOLIC_UNDETERMINED,
    ) and (result.magnitude_segments or result.phase_segments):
        raise BodeDataFailure(
            DiagnosticCode.BODE_DATA_CONTEXT_MISMATCH,
            "Nicht plotbare Bode-Daten dürfen keine Segmente enthalten.",
        )
    if status is BodeDataStatus.PARTIAL and (
        not result.magnitude_segments
        or not result.phase_segments
        or all(point.magnitude_plottable for point in result.points)
        or all(point.phase_plottable for point in result.points)
    ):
        raise BodeDataFailure(
            DiagnosticCode.BODE_DATA_CONTEXT_MISMATCH,
            "Partielle Bode-Daten benötigen endliche und unterbrochene "
            "Segmente.",
        )


def _decimal_digit_count(value: str) -> int:
    try:
        decimal = Decimal(value)
    except (InvalidOperation, ValueError) as error:
        raise BodeDataFailure(
            DiagnosticCode.BODE_DATA_INVALID_INPUT,
            "Ein Bode-Dezimalwert ist ungültig.",
        ) from error
    if not decimal.is_finite():
        raise BodeDataFailure(
            DiagnosticCode.BODE_DATA_INVALID_INPUT,
            "Ein Bode-Dezimalwert muss endlich sein.",
        )
    return len(decimal.as_tuple().digits)


def _plot_decimal_limit() -> BodeDataFailure:
    return BodeDataFailure(
        DiagnosticCode.BODE_DATA_LIMIT_EXCEEDED,
        "Eine vorhandene Plotdarstellung überschreitet die Dezimalgrenze.",
        (("limit", "max_plot_decimal_digits"),),
    )


__all__ = [
    "BodeDataFailure",
    "validate_bode_data_result",
    "validate_bode_input_grid",
    "validate_frequency_handoff",
    "validate_plot_decimal_limits",
]
