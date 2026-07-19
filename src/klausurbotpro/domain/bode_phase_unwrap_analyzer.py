"""Optional deterministic projection of existing principal-phase segments."""

from __future__ import annotations

from klausurbotpro.domain._bode_phase_unwrap_algorithm import (
    PhaseUnwrapAlgorithmLimit,
    unwrap_principal_phase_sequence,
)
from klausurbotpro.domain._bode_phase_unwrap_status import (
    derive_bode_phase_unwrap_status,
)
from klausurbotpro.domain._bode_phase_unwrap_validation import (
    BodePhaseUnwrapFailure,
    validate_bode_phase_unwrap_result,
    validate_bode_phase_unwrap_source,
)
from klausurbotpro.domain.bode_data_contracts import (
    BodeDataLimits,
    BodePhaseSegment,
    TransferFunctionBodeDataResult,
)
from klausurbotpro.domain.bode_phase_unwrap_contracts import (
    BodePhaseUnwrapLimits,
    BodePhaseUnwrapMetadata,
    BodePhaseUnwrapResult,
    BodePhaseUnwrapStatus,
    BodeUnwrappedPhasePoint,
    BodeUnwrappedPhaseSegment,
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

_DEFAULT_FREQUENCY_LIMITS = FrequencyResponseLimits()
_DEFAULT_GRID_LIMITS = LogFrequencyGridLimits()
_DEFAULT_BODE_LIMITS = BodeDataLimits()
_DEFAULT_UNWRAP_LIMITS = BodePhaseUnwrapLimits()
_RESOURCE_ERRORS = (MemoryError, RecursionError, OverflowError)


class BodePhaseUnwrapAnalyzer:
    """Unwrap existing phase segments without changing principal phases."""

    def __init__(
        self,
        frequency_limits: FrequencyResponseLimits = _DEFAULT_FREQUENCY_LIMITS,
        grid_limits: LogFrequencyGridLimits = _DEFAULT_GRID_LIMITS,
        bode_limits: BodeDataLimits = _DEFAULT_BODE_LIMITS,
        unwrap_limits: BodePhaseUnwrapLimits = _DEFAULT_UNWRAP_LIMITS,
    ) -> None:
        if type(frequency_limits) is not FrequencyResponseLimits:
            raise TypeError("frequency_limits must be FrequencyResponseLimits.")
        if type(grid_limits) is not LogFrequencyGridLimits:
            raise TypeError("grid_limits must be LogFrequencyGridLimits.")
        if type(bode_limits) is not BodeDataLimits:
            raise TypeError("bode_limits must be BodeDataLimits.")
        if type(unwrap_limits) is not BodePhaseUnwrapLimits:
            raise TypeError("unwrap_limits must be BodePhaseUnwrapLimits.")
        self._frequency_limits = frequency_limits
        self._grid_limits = grid_limits
        self._bode_limits = bode_limits
        self._unwrap_limits = unwrap_limits

    def analyze(
        self,
        bode_data: TransferFunctionBodeDataResult,
        *,
        field: str | None = None,
    ) -> BodePhaseUnwrapResult:
        if type(bode_data) is not TransferFunctionBodeDataResult:
            raise TypeError("bode_data must be TransferFunctionBodeDataResult.")
        if field is not None and type(field) is not str:
            raise TypeError("field must be str or None.")
        try:
            validate_bode_phase_unwrap_source(
                bode_data,
                frequency_limits=self._frequency_limits,
                grid_limits=self._grid_limits,
                bode_limits=self._bode_limits,
                unwrap_limits=self._unwrap_limits,
            )
            status = derive_bode_phase_unwrap_status(
                bode_data.status,
                len(bode_data.phase_segments),
            )
            global_diagnostics: tuple[Diagnostic, ...] = ()
            if status is BodePhaseUnwrapStatus.NO_PHASE_DATA:
                global_diagnostics = (
                    Diagnostic(
                        DiagnosticSeverity.INFO,
                        DiagnosticCode.BODE_PHASE_UNWRAP_NO_PHASE_DATA,
                        "Die Bode-Quelle enthält keine entfaltbaren Phasensegmente.",
                        field,
                    ),
                )
            segments = tuple(
                self._unwrap_segment(source_segment)
                for source_segment in bode_data.phase_segments
            )
            diagnostics = (
                bode_data.diagnostics
                + tuple(
                    diagnostic
                    for segment in segments
                    for point in segment.points
                    for diagnostic in point.diagnostics
                )
                + global_diagnostics
            )
            if len(diagnostics) > self._unwrap_limits.max_diagnostics:
                raise BodePhaseUnwrapFailure(
                    DiagnosticCode.BODE_PHASE_UNWRAP_LIMIT_EXCEEDED,
                    "Das Ergebnis enthält zu viele Diagnosen.",
                    (("limit", "max_diagnostics"),),
                )
            result = BodePhaseUnwrapResult._create(
                status=status,
                source_bode_data=bode_data,
                segments=segments,
                metadata=BodePhaseUnwrapMetadata._create(),
                diagnostics=diagnostics,
            )
            self._validate_result(result)
            return result
        except BodePhaseUnwrapFailure as failure:
            return self._failure(failure, field)
        except _RESOURCE_ERRORS as error:
            return self._failure(
                BodePhaseUnwrapFailure(
                    DiagnosticCode.BODE_PHASE_UNWRAP_RESOURCE_LIMIT_EXCEEDED,
                    "Die Phasenentfaltung überschreitet verfügbare Ressourcen.",
                    (("exception", type(error).__name__),),
                ),
                field,
            )

    def _unwrap_segment(
        self,
        source_segment: BodePhaseSegment,
    ) -> BodeUnwrappedPhaseSegment:
        principal_phases = tuple(
            point.principal_phase_degrees for point in source_segment.points
        )
        if any(value is None for value in principal_phases):
            raise BodePhaseUnwrapFailure(
                DiagnosticCode.BODE_PHASE_UNWRAP_INVALID_SOURCE,
                "Ein Quellsegment enthält einen Punkt ohne Hauptphase.",
            )
        try:
            values = unwrap_principal_phase_sequence(
                tuple(value for value in principal_phases if value is not None),
                max_absolute_phase_turns=(
                    self._unwrap_limits.max_absolute_phase_turns
                ),
                max_decimal_digits=self._unwrap_limits.max_decimal_digits,
            )
        except PhaseUnwrapAlgorithmLimit as error:
            raise BodePhaseUnwrapFailure(
                DiagnosticCode.BODE_PHASE_UNWRAP_LIMIT_EXCEEDED,
                "Eine Grenze der Phasenentfaltung wurde überschritten.",
                (("limit", error.limit_name),),
            ) from error
        points = tuple(
            BodeUnwrappedPhasePoint._create(
                source_point=source_point,
                phase_offset_turns=value.phase_offset_turns,
                unwrapped_phase_degrees=value.unwrapped_phase_degrees,
                source_segment_index=source_segment.segment_index,
                grid_index=source_segment.start_grid_index + local_index,
            )
            for local_index, (source_point, value) in enumerate(
                zip(source_segment.points, values, strict=True)
            )
        )
        return BodeUnwrappedPhaseSegment._create(
            source_segment=source_segment,
            points=points,
        )

    def _validate_result(self, result: BodePhaseUnwrapResult) -> None:
        validate_bode_phase_unwrap_result(
            result,
            frequency_limits=self._frequency_limits,
            grid_limits=self._grid_limits,
            bode_limits=self._bode_limits,
            unwrap_limits=self._unwrap_limits,
        )

    def _failure(
        self,
        failure: BodePhaseUnwrapFailure,
        field: str | None,
    ) -> BodePhaseUnwrapResult:
        result = BodePhaseUnwrapResult._create(
            status=BodePhaseUnwrapStatus.FAILED,
            diagnostics=(
                Diagnostic(
                    DiagnosticSeverity.ERROR,
                    failure.code,
                    failure.message,
                    field,
                    failure.details,
                ),
            ),
        )
        self._validate_result(result)
        return result


__all__ = ["BodePhaseUnwrapAnalyzer"]
