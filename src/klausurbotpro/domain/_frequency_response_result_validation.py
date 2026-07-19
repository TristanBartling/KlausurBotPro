"""Reusable defensive boundary for completed frequency-response results."""

from __future__ import annotations

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
    FrequencyResponsePoint,
    TransferFunctionFrequencyResponseResult,
    TransferFunctionFrequencyResponseStatus,
    _aggregate_frequency_response_status,
)

_NESTED_ERRORS = (AttributeError, IndexError, TypeError, ValueError)


def validate_frequency_response_result(
    result: TransferFunctionFrequencyResponseResult,
    limits: FrequencyResponseLimits,
) -> None:
    """Revalidate a Phase-3A.1 result without repeating point evaluation."""

    if type(result) is not TransferFunctionFrequencyResponseResult:
        raise TypeError(
            "result must be TransferFunctionFrequencyResponseResult."
        )
    if type(limits) is not FrequencyResponseLimits:
        raise TypeError("limits must be FrequencyResponseLimits.")
    try:
        _validate_result(result, limits)
    except FrequencyResponseFailure:
        raise
    except _NESTED_ERRORS as error:
        raise FrequencyResponseFailure(
            DiagnosticCode.FREQUENCY_RESPONSE_INVALID_INPUT,
            "Das Frequenzgangergebnis ist manipuliert.",
            (("exception", type(error).__name__),),
        ) from error


def _validate_result(
    result: TransferFunctionFrequencyResponseResult,
    limits: FrequencyResponseLimits,
) -> None:
    if type(result.status) is not TransferFunctionFrequencyResponseStatus:
        raise ValueError("Invalid frequency-response result status.")
    _validate_diagnostics(result.diagnostics)
    if result.status is TransferFunctionFrequencyResponseStatus.FAILED:
        result._validate()
        return
    if result.reduced_transfer_function is None or result.frequencies is None:
        raise ValueError("Successful frequency response lacks context.")
    normalized, _, _ = validate_frequency_response_context(
        result.reduced_transfer_function,
        result.frequencies,
        result.substitutions,
        limits,
    )
    if normalized != result.substitutions:
        raise ValueError("Frequency-response substitutions are not normalized.")
    result._validate()
    if any(type(point) is not FrequencyResponsePoint for point in result.points):
        raise TypeError("Invalid frequency-response point type.")
    expected_status = _aggregate_frequency_response_status(
        tuple(point.status for point in result.points)
    )
    if result.status is not expected_status:
        raise ValueError("Frequency-response status is inconsistent.")
    expected_diagnostics = tuple(
        diagnostic for point in result.points for diagnostic in point.diagnostics
    )
    if result.diagnostics != expected_diagnostics:
        raise ValueError("Frequency-response diagnostics are inconsistent.")


def _validate_diagnostics(diagnostics: tuple[Diagnostic, ...]) -> None:
    if type(diagnostics) is not tuple or any(
        type(item) is not Diagnostic for item in diagnostics
    ):
        raise TypeError("Frequency-response diagnostics are invalid.")
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
            raise ValueError("A frequency-response diagnostic is manipulated.")


__all__ = ["validate_frequency_response_result"]
