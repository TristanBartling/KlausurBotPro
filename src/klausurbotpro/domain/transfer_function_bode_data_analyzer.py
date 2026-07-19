"""Structured Bode projection using exactly one Phase-3A.1 analysis."""

from __future__ import annotations

from klausurbotpro.domain._bode_data_segmentation import build_bode_segments
from klausurbotpro.domain._bode_data_status import derive_bode_data_status
from klausurbotpro.domain._bode_data_validation import (
    BodeDataFailure,
    validate_bode_data_result,
    validate_bode_input_grid,
    validate_frequency_handoff,
    validate_plot_decimal_limits,
)
from klausurbotpro.domain.bode_data_contracts import (
    BodeAxisMetadata,
    BodeDataLimits,
    BodeDataStatus,
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
    TransferFunctionFrequencyResponseStatus,
)
from klausurbotpro.domain.log_frequency_grid_contracts import (
    LogFrequencyGridLimits,
    LogFrequencyGridResult,
)
from klausurbotpro.domain.parameter_substitutions import ParameterSubstitutions
from klausurbotpro.domain.reduced_transfer_function import (
    ReducedTransferFunction,
)
from klausurbotpro.domain.transfer_function_frequency_response_analyzer import (
    TransferFunctionFrequencyResponseAnalyzer,
)

_DEFAULT_FREQUENCY_LIMITS = FrequencyResponseLimits()
_DEFAULT_GRID_LIMITS = LogFrequencyGridLimits()
_DEFAULT_BODE_LIMITS = BodeDataLimits()
_RESOURCE_ERRORS = (MemoryError, RecursionError, OverflowError)


class TransferFunctionBodeDataAnalyzer:
    """Project validated point responses into finite Bode plot segments."""

    def __init__(
        self,
        frequency_limits: FrequencyResponseLimits = _DEFAULT_FREQUENCY_LIMITS,
        grid_limits: LogFrequencyGridLimits = _DEFAULT_GRID_LIMITS,
        bode_limits: BodeDataLimits = _DEFAULT_BODE_LIMITS,
    ) -> None:
        if type(frequency_limits) is not FrequencyResponseLimits:
            raise TypeError("frequency_limits must be FrequencyResponseLimits.")
        if type(grid_limits) is not LogFrequencyGridLimits:
            raise TypeError("grid_limits must be LogFrequencyGridLimits.")
        if type(bode_limits) is not BodeDataLimits:
            raise TypeError("bode_limits must be BodeDataLimits.")
        self._frequency_limits = frequency_limits
        self._grid_limits = grid_limits
        self._bode_limits = bode_limits

    def analyze(
        self,
        reduced: ReducedTransferFunction,
        grid: LogFrequencyGridResult,
        substitutions: ParameterSubstitutions | None = None,
        *,
        field: str | None = None,
    ) -> TransferFunctionBodeDataResult:
        if type(reduced) is not ReducedTransferFunction:
            raise TypeError("reduced must be ReducedTransferFunction.")
        if type(grid) is not LogFrequencyGridResult:
            raise TypeError("grid must be LogFrequencyGridResult.")
        if substitutions is not None and type(
            substitutions
        ) is not ParameterSubstitutions:
            raise TypeError("substitutions must be ParameterSubstitutions or None.")
        if field is not None and type(field) is not str:
            raise TypeError("field must be str or None.")
        try:
            validate_bode_input_grid(
                grid,
                grid_limits=self._grid_limits,
                frequency_limits=self._frequency_limits,
                bode_limits=self._bode_limits,
            )
            sample_set = FrequencySampleSet(
                tuple(
                    point.evaluation_frequency
                    for point in grid.points
                )
            )
            response = TransferFunctionFrequencyResponseAnalyzer(
                self._frequency_limits
            ).analyze(
                reduced,
                sample_set,
                substitutions,
                field=field,
            )
            validate_frequency_handoff(
                response,
                reduced=reduced,
                sample_set=sample_set,
                substitutions=substitutions,
                limits=self._frequency_limits,
            )
            if response.status is TransferFunctionFrequencyResponseStatus.FAILED:
                return self._failure(
                    BodeDataFailure(
                        DiagnosticCode.BODE_DATA_FREQUENCY_ANALYSIS_FAILED,
                        "Die punktweise Frequenzganganalyse ist fehlgeschlagen.",
                    ),
                    field,
                    retained=response.diagnostics,
                )
            points = tuple(
                BodePlotPoint._create(
                    grid_point=grid_point,
                    frequency_response_point=response_point,
                )
                for grid_point, response_point in zip(
                    grid.points,
                    response.points,
                    strict=True,
                )
            )
            validate_plot_decimal_limits(points, self._bode_limits)
            magnitude_segments, phase_segments = build_bode_segments(points)
            if len(magnitude_segments) > self._bode_limits.max_magnitude_segments:
                raise BodeDataFailure(
                    DiagnosticCode.BODE_DATA_LIMIT_EXCEEDED,
                    "Es entstehen zu viele Betragssegmente.",
                    (("limit", "max_magnitude_segments"),),
                )
            if len(phase_segments) > self._bode_limits.max_phase_segments:
                raise BodeDataFailure(
                    DiagnosticCode.BODE_DATA_LIMIT_EXCEEDED,
                    "Es entstehen zu viele Phasensegmente.",
                    (("limit", "max_phase_segments"),),
                )
            status = derive_bode_data_status(
                tuple(point.status for point in response.points)
            )
            global_diagnostics: tuple[Diagnostic, ...] = ()
            if status is BodeDataStatus.NO_PLOTTABLE_DATA:
                global_diagnostics = (
                    Diagnostic(
                        DiagnosticSeverity.INFO,
                        DiagnosticCode.BODE_DATA_NO_PLOTTABLE_DATA,
                        "Es liegen keine endlichen Bode-Plotsegmente vor.",
                        field,
                    ),
                )
            diagnostics = (
                grid.diagnostics
                + response.diagnostics
                + tuple(
                    diagnostic
                    for point in points
                    for diagnostic in point.diagnostics
                )
                + global_diagnostics
            )
            if len(diagnostics) > self._bode_limits.max_diagnostics:
                raise BodeDataFailure(
                    DiagnosticCode.BODE_DATA_LIMIT_EXCEEDED,
                    "Das Bode-Ergebnis enthält zu viele Diagnosen.",
                    (("limit", "max_diagnostics"),),
                )
            result = TransferFunctionBodeDataResult._create(
                status=status,
                grid=grid,
                frequency_response_result=response,
                points=points,
                magnitude_segments=magnitude_segments,
                phase_segments=phase_segments,
                axis_metadata=BodeAxisMetadata._create(),
                diagnostics=diagnostics,
            )
            validate_bode_data_result(
                result,
                frequency_limits=self._frequency_limits,
                grid_limits=self._grid_limits,
                bode_limits=self._bode_limits,
            )
            return result
        except BodeDataFailure as failure:
            return self._failure(failure, field)
        except (AttributeError, IndexError, TypeError, ValueError) as error:
            return self._failure(
                BodeDataFailure(
                    DiagnosticCode.BODE_DATA_CONTEXT_MISMATCH,
                    "Die erzeugten Bode-Daten verletzen den erwarteten Kontext.",
                    (("exception", type(error).__name__),),
                ),
                field,
            )
        except _RESOURCE_ERRORS as error:
            return self._failure(
                BodeDataFailure(
                    DiagnosticCode.BODE_DATA_RESOURCE_LIMIT_EXCEEDED,
                    "Die Bode-Datenprojektion überschreitet verfügbare Ressourcen.",
                    (("exception", type(error).__name__),),
                ),
                field,
            )

    def _failure(
        self,
        failure: BodeDataFailure,
        field: str | None,
        *,
        retained: tuple[Diagnostic, ...] = (),
    ) -> TransferFunctionBodeDataResult:
        diagnostic = Diagnostic(
            DiagnosticSeverity.ERROR,
            failure.code,
            failure.message,
            field,
            failure.details,
        )
        diagnostics = retained + (diagnostic,)
        if len(diagnostics) > self._bode_limits.max_diagnostics:
            diagnostics = (
                Diagnostic(
                    DiagnosticSeverity.ERROR,
                    DiagnosticCode.BODE_DATA_LIMIT_EXCEEDED,
                    "Die Bode-Diagnosegrenze wurde überschritten.",
                    field,
                    (("limit", "max_diagnostics"),),
                ),
            )
        result = TransferFunctionBodeDataResult._create(
            status=BodeDataStatus.FAILED,
            diagnostics=diagnostics,
        )
        validate_bode_data_result(
            result,
            frequency_limits=self._frequency_limits,
            grid_limits=self._grid_limits,
            bode_limits=self._bode_limits,
        )
        return result


__all__ = ["TransferFunctionBodeDataAnalyzer"]
