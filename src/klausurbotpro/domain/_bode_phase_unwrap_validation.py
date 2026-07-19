"""Defensive trust boundaries for optional Bode phase unwrapping."""

from __future__ import annotations

from dataclasses import dataclass

from klausurbotpro.domain._bode_data_validation import (
    BodeDataFailure,
    validate_bode_data_result,
)
from klausurbotpro.domain._bode_phase_unwrap_algorithm import (
    PhaseUnwrapAlgorithmLimit,
    UnwrappedPhaseValue,
    unwrap_principal_phase_sequence,
)
from klausurbotpro.domain._bode_phase_unwrap_status import (
    derive_bode_phase_unwrap_status,
)
from klausurbotpro.domain._finite_decimal_exact import (
    FiniteDecimal,
    FiniteDecimalError,
)
from klausurbotpro.domain.bode_data_contracts import (
    BodeDataLimits,
    BodeDataStatus,
    TransferFunctionBodeDataResult,
)
from klausurbotpro.domain.bode_phase_unwrap_contracts import (
    BodePhaseUnwrapLimits,
    BodePhaseUnwrapMetadata,
    BodePhaseUnwrapResult,
    BodePhaseUnwrapStatus,
)
from klausurbotpro.domain.diagnostics import (
    Diagnostic,
    DiagnosticCode,
    DiagnosticSeverity,
)
from klausurbotpro.domain.frequency_response_contracts import (
    FrequencyResponseLimits,
)
from klausurbotpro.domain.log_frequency_grid_contracts import (
    LogFrequencyGridLimits,
)

_NESTED_ERRORS = (AttributeError, IndexError, TypeError, ValueError)


@dataclass(frozen=True, slots=True)
class BodePhaseUnwrapFailure(ValueError):
    code: DiagnosticCode
    message: str
    details: tuple[tuple[str, str], ...] = ()


def validate_bode_phase_unwrap_source(
    source: TransferFunctionBodeDataResult,
    *,
    frequency_limits: FrequencyResponseLimits,
    grid_limits: LogFrequencyGridLimits,
    bode_limits: BodeDataLimits,
    unwrap_limits: BodePhaseUnwrapLimits,
) -> None:
    try:
        validate_bode_data_result(
            source,
            frequency_limits=frequency_limits,
            grid_limits=grid_limits,
            bode_limits=bode_limits,
        )
        if source.status is BodeDataStatus.FAILED:
            raise BodePhaseUnwrapFailure(
                DiagnosticCode.BODE_PHASE_UNWRAP_INVALID_SOURCE,
                "Fehlgeschlagene Bode-Daten besitzen keine entfaltbare Phase.",
            )
        _validate_source_limits(source, unwrap_limits)
    except BodePhaseUnwrapFailure:
        raise
    except (BodeDataFailure, AttributeError, IndexError, TypeError, ValueError) as error:
        raise BodePhaseUnwrapFailure(
            DiagnosticCode.BODE_PHASE_UNWRAP_INVALID_SOURCE,
            "Die Bode-Quelle ist ungültig oder manipuliert.",
            (("cause", type(error).__name__),),
        ) from error


def validate_bode_phase_unwrap_result(
    result: BodePhaseUnwrapResult,
    *,
    frequency_limits: FrequencyResponseLimits,
    grid_limits: LogFrequencyGridLimits,
    bode_limits: BodeDataLimits,
    unwrap_limits: BodePhaseUnwrapLimits,
) -> None:
    if type(result) is not BodePhaseUnwrapResult:
        raise TypeError("result must be BodePhaseUnwrapResult.")
    try:
        _validate_result(
            result,
            frequency_limits=frequency_limits,
            grid_limits=grid_limits,
            bode_limits=bode_limits,
            unwrap_limits=unwrap_limits,
        )
    except BodePhaseUnwrapFailure:
        raise
    except _NESTED_ERRORS as error:
        raise BodePhaseUnwrapFailure(
            DiagnosticCode.BODE_PHASE_UNWRAP_INVALID_INPUT,
            "Das Phasenentfaltungsergebnis ist manipuliert.",
            (("exception", type(error).__name__),),
        ) from error


def _validate_result(
    result: BodePhaseUnwrapResult,
    *,
    frequency_limits: FrequencyResponseLimits,
    grid_limits: LogFrequencyGridLimits,
    bode_limits: BodeDataLimits,
    unwrap_limits: BodePhaseUnwrapLimits,
) -> None:
    result._validate()
    _validate_diagnostics(
        result.diagnostics,
        unwrap_limits,
        allow_errors=result.status is BodePhaseUnwrapStatus.FAILED,
    )
    if result.status is BodePhaseUnwrapStatus.FAILED:
        return
    source = result.source_bode_data
    if source is None:
        raise BodePhaseUnwrapFailure(
            DiagnosticCode.BODE_PHASE_UNWRAP_CONTEXT_MISMATCH,
            "Ein erfolgreiches Ergebnis benötigt seine Bode-Quelle.",
        )
    validate_bode_phase_unwrap_source(
        source,
        frequency_limits=frequency_limits,
        grid_limits=grid_limits,
        bode_limits=bode_limits,
        unwrap_limits=unwrap_limits,
    )
    expected_status = derive_bode_phase_unwrap_status(
        source.status,
        len(source.phase_segments),
    )
    if result.status is not expected_status:
        raise BodePhaseUnwrapFailure(
            DiagnosticCode.BODE_PHASE_UNWRAP_CONTEXT_MISMATCH,
            "Der Status der Phasenentfaltung ist inkonsistent.",
        )
    if result.metadata != BodePhaseUnwrapMetadata._create():
        raise BodePhaseUnwrapFailure(
            DiagnosticCode.BODE_PHASE_UNWRAP_CONTEXT_MISMATCH,
            "Die Phasenentfaltungsmetadaten sind inkonsistent.",
        )
    if expected_status is BodePhaseUnwrapStatus.NO_PHASE_DATA:
        _validate_no_phase_data(result, source)
        return
    if len(result.segments) != len(source.phase_segments):
        raise BodePhaseUnwrapFailure(
            DiagnosticCode.BODE_PHASE_UNWRAP_CONTEXT_MISMATCH,
            "Die entfaltete Segmentfolge ist unvollständig.",
        )
    for segment_index, segment in enumerate(result.segments):
        segment._validate()
        source_segment = source.phase_segments[segment_index]
        if (
            segment.source_segment is not source_segment
            or segment.segment_index != segment_index
            or segment.start_grid_index != source_segment.start_grid_index
            or segment.end_grid_index != source_segment.end_grid_index
            or len(segment.points) != len(source_segment.points)
        ):
            raise BodePhaseUnwrapFailure(
                DiagnosticCode.BODE_PHASE_UNWRAP_CONTEXT_MISMATCH,
                "Ein entfaltetes Segment stimmt nicht mit seinem Quellsegment überein.",
            )
        principals = tuple(
            point.principal_phase_degrees for point in source_segment.points
        )
        if any(value is None for value in principals):
            raise BodePhaseUnwrapFailure(
                DiagnosticCode.BODE_PHASE_UNWRAP_CONTEXT_MISMATCH,
                "Ein Quellsegment enthält keine vollständigen Hauptphasen.",
            )
        expected_values = _unwrap_limited(
            tuple(value for value in principals if value is not None),
            unwrap_limits,
        )
        for local_index, point in enumerate(segment.points):
            point._validate()
            source_point = source_segment.points[local_index]
            expected = expected_values[local_index]
            if (
                point.source_point is not source_point
                or point.source_segment_index != segment_index
                or point.grid_index != segment.start_grid_index + local_index
                or point.principal_phase_degrees
                != source_point.principal_phase_degrees
                or point.phase_offset_turns != expected.phase_offset_turns
                or point.unwrapped_phase_degrees
                != expected.unwrapped_phase_degrees
                or point.diagnostics
            ):
                raise BodePhaseUnwrapFailure(
                    DiagnosticCode.BODE_PHASE_UNWRAP_CONTEXT_MISMATCH,
                    "Ein entfalteter Phasenpunkt ist nicht exakt reproduzierbar.",
                )
    expected_diagnostics = source.diagnostics + tuple(
        diagnostic
        for segment in result.segments
        for point in segment.points
        for diagnostic in point.diagnostics
    )
    if result.diagnostics != expected_diagnostics:
        raise BodePhaseUnwrapFailure(
            DiagnosticCode.BODE_PHASE_UNWRAP_CONTEXT_MISMATCH,
            "Die Diagnoseaggregation der Phasenentfaltung ist inkonsistent.",
        )
    if expected_status is BodePhaseUnwrapStatus.COMPLETE and (
        len(result.segments) != 1
        or result.segments[0].start_grid_index != 0
        or len(result.segments[0].points) != len(source.points)
    ):
        raise BodePhaseUnwrapFailure(
            DiagnosticCode.BODE_PHASE_UNWRAP_CONTEXT_MISMATCH,
            "Eine vollständige Entfaltung benötigt ein vollständiges Segment.",
        )


def _validate_source_limits(
    source: TransferFunctionBodeDataResult,
    limits: BodePhaseUnwrapLimits,
) -> None:
    if len(source.phase_segments) > limits.max_phase_segments:
        raise _limit_failure("max_phase_segments")
    point_count = sum(len(segment.points) for segment in source.phase_segments)
    if point_count > limits.max_points:
        raise _limit_failure("max_points")
    if len(source.diagnostics) > limits.max_diagnostics:
        raise _limit_failure("max_diagnostics")
    for segment in source.phase_segments:
        for point in segment.points:
            phase = point.principal_phase_degrees
            if phase is None:
                raise BodePhaseUnwrapFailure(
                    DiagnosticCode.BODE_PHASE_UNWRAP_INVALID_SOURCE,
                    "Ein Phasensegment enthält einen Punkt ohne Hauptphase.",
                )
            try:
                FiniteDecimal.parse(phase, limits.max_decimal_digits)
            except (FiniteDecimalError, TypeError, ValueError) as error:
                raise _limit_failure("max_decimal_digits") from error


def _validate_no_phase_data(
    result: BodePhaseUnwrapResult,
    source: TransferFunctionBodeDataResult,
) -> None:
    expected = source.diagnostics
    tail = result.diagnostics[len(expected) :]
    if (
        result.diagnostics[: len(expected)] != expected
        or len(tail) != 1
        or tail[0].code is not DiagnosticCode.BODE_PHASE_UNWRAP_NO_PHASE_DATA
        or tail[0].severity is not DiagnosticSeverity.INFO
    ):
        raise BodePhaseUnwrapFailure(
            DiagnosticCode.BODE_PHASE_UNWRAP_CONTEXT_MISMATCH,
            "Der Hinweis auf fehlende Phasendaten ist inkonsistent.",
        )


def _validate_diagnostics(
    diagnostics: tuple[Diagnostic, ...],
    limits: BodePhaseUnwrapLimits,
    *,
    allow_errors: bool,
) -> None:
    if type(diagnostics) is not tuple or any(
        type(item) is not Diagnostic for item in diagnostics
    ):
        raise BodePhaseUnwrapFailure(
            DiagnosticCode.BODE_PHASE_UNWRAP_INVALID_INPUT,
            "Unwrap-Diagnosen müssen ein exaktes Tupel bilden.",
        )
    if len(diagnostics) > limits.max_diagnostics:
        raise _limit_failure("max_diagnostics")
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
            raise BodePhaseUnwrapFailure(
                DiagnosticCode.BODE_PHASE_UNWRAP_INVALID_INPUT,
                "Eine Unwrap-Diagnose ist manipuliert.",
            )
    if not allow_errors and any(
        item.severity is DiagnosticSeverity.ERROR for item in diagnostics
    ):
        raise BodePhaseUnwrapFailure(
            DiagnosticCode.BODE_PHASE_UNWRAP_INVALID_INPUT,
            "Ein erfolgreiches Unwrap-Ergebnis darf keinen Fehler enthalten.",
        )


def _unwrap_limited(
    principal_phases: tuple[str, ...],
    limits: BodePhaseUnwrapLimits,
) -> tuple[UnwrappedPhaseValue, ...]:
    try:
        return unwrap_principal_phase_sequence(
            principal_phases,
            max_absolute_phase_turns=limits.max_absolute_phase_turns,
            max_decimal_digits=limits.max_decimal_digits,
        )
    except PhaseUnwrapAlgorithmLimit as error:
        raise _limit_failure(error.limit_name) from error


def _limit_failure(limit_name: str) -> BodePhaseUnwrapFailure:
    return BodePhaseUnwrapFailure(
        DiagnosticCode.BODE_PHASE_UNWRAP_LIMIT_EXCEEDED,
        "Eine Grenze der Phasenentfaltung wurde überschritten.",
        (("limit", limit_name),),
    )


__all__ = [
    "BodePhaseUnwrapFailure",
    "validate_bode_phase_unwrap_result",
    "validate_bode_phase_unwrap_source",
]
