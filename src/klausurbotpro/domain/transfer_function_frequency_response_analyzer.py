"""Defensive exact pointwise frequency-response analysis."""

from __future__ import annotations

from klausurbotpro.domain._frequency_response_evaluator import (
    FrequencyResponseBudget,
    evaluate_frequency_point,
)
from klausurbotpro.domain._frequency_response_validation import (
    FrequencyResponseFailure,
    validate_frequency_response_context,
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
    _aggregate_frequency_response_status,
)
from klausurbotpro.domain.parameter_substitutions import ParameterSubstitutions
from klausurbotpro.domain.reduced_transfer_function import (
    ReducedTransferFunction,
)

_DEFAULT_LIMITS = FrequencyResponseLimits()
_RESOURCE_ERRORS = (MemoryError, RecursionError, OverflowError)


class TransferFunctionFrequencyResponseAnalyzer:
    """Evaluate ``G(I*omega)`` exactly at an ordered finite sample set."""

    def __init__(self, limits: FrequencyResponseLimits = _DEFAULT_LIMITS) -> None:
        if type(limits) is not FrequencyResponseLimits:
            raise TypeError("limits must be FrequencyResponseLimits.")
        self._limits = limits

    def analyze(
        self,
        reduced: ReducedTransferFunction,
        frequencies: FrequencySampleSet,
        substitutions: ParameterSubstitutions | None = None,
        *,
        field: str | None = None,
    ) -> TransferFunctionFrequencyResponseResult:
        """Return exact point values and subordinate numerical presentations."""

        if type(reduced) is not ReducedTransferFunction:
            raise TypeError("reduced must be ReducedTransferFunction.")
        if type(frequencies) is not FrequencySampleSet:
            raise TypeError("frequencies must be FrequencySampleSet.")
        if substitutions is not None and type(
            substitutions
        ) is not ParameterSubstitutions:
            raise TypeError("substitutions must be ParameterSubstitutions or None.")
        if field is not None and type(field) is not str:
            raise TypeError("field must be str or None.")
        try:
            (
                normalized_substitutions,
                mapping,
                prerequisites_resolved,
            ) = validate_frequency_response_context(
                reduced,
                frequencies,
                substitutions,
                self._limits,
            )
            budget = FrequencyResponseBudget(self._limits)
            points = tuple(
                evaluate_frequency_point(
                    reduced,
                    omega,
                    mapping,
                    prerequisites_resolved=prerequisites_resolved,
                    limits=self._limits,
                    budget=budget,
                    field=field,
                )
                for omega in frequencies.frequencies
            )
            diagnostics = tuple(
                diagnostic
                for point in points
                for diagnostic in point.diagnostics
            )
            return TransferFunctionFrequencyResponseResult._create(
                reduced_transfer_function=reduced,
                frequencies=frequencies,
                substitutions=normalized_substitutions,
                status=_aggregate_frequency_response_status(
                    tuple(point.status for point in points)
                ),
                points=points,
                diagnostics=diagnostics,
            )
        except FrequencyResponseFailure as failure:
            return self._failure(failure, field)
        except _RESOURCE_ERRORS as error:
            return self._failure(
                FrequencyResponseFailure(
                    DiagnosticCode.FREQUENCY_RESPONSE_RESOURCE_LIMIT_EXCEEDED,
                    "Die Frequenzganganalyse überschreitet verfügbare Ressourcen.",
                    (("exception", type(error).__name__),),
                ),
                field,
            )

    @staticmethod
    def _failure(
        failure: FrequencyResponseFailure,
        field: str | None,
    ) -> TransferFunctionFrequencyResponseResult:
        return TransferFunctionFrequencyResponseResult._create(
            reduced_transfer_function=None,
            frequencies=None,
            substitutions=None,
            status=TransferFunctionFrequencyResponseStatus.FAILED,
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


__all__ = ["TransferFunctionFrequencyResponseAnalyzer"]
