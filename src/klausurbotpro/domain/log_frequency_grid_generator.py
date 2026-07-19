"""Deterministic bounded generation of certified logarithmic frequency grids."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from klausurbotpro.domain._log_frequency_grid_certification import (
    certifies_relative_error,
    relative_error_limit,
)
from klausurbotpro.domain._log_frequency_grid_numeric import (
    LogFrequencyGridNumericError,
    approximate_logarithmic_target,
    approximate_rational_for_display,
)
from klausurbotpro.domain._log_frequency_grid_result_validation import (
    validate_log_frequency_grid_result,
)
from klausurbotpro.domain._log_frequency_grid_validation import (
    CertificationBudget,
    LogFrequencyGridFailure,
    ValidatedLogFrequencyGridRequest,
    determine_interval_count,
    find_exact_target_index,
    validate_log_frequency_grid_request,
    validate_output_rational,
    validate_total_points,
)
from klausurbotpro.domain.diagnostics import (
    Diagnostic,
    DiagnosticCode,
    DiagnosticSeverity,
)
from klausurbotpro.domain.log_frequency_grid_contracts import (
    LogFrequencyGridLimits,
    LogFrequencyGridPoint,
    LogFrequencyGridRequest,
    LogFrequencyGridResult,
    LogFrequencyGridStatus,
    LogFrequencyPointOrigin,
    ScientificDecimal,
)
from klausurbotpro.domain.parameter_substitutions import ExactRationalValue

_DEFAULT_LIMITS = LogFrequencyGridLimits()
_RESOURCE_ERRORS = (MemoryError, RecursionError, OverflowError)
_EXPECTED_VALIDATION_ERRORS = (AttributeError, IndexError, TypeError, ValueError)
_ORIGIN_ORDER = {
    LogFrequencyPointOrigin.LOWER_BOUND: 0,
    LogFrequencyPointOrigin.GENERATED: 1,
    LogFrequencyPointOrigin.UPPER_BOUND: 2,
    LogFrequencyPointOrigin.EXPLICIT: 3,
}


@dataclass(frozen=True, slots=True)
class _GridPointData:
    evaluation_frequency: Fraction
    target_decimal: ScientificDecimal
    target_index: int | None
    origins: tuple[LogFrequencyPointOrigin, ...]
    maximum_relative_error: Fraction


class LogFrequencyGridGenerator:
    """Generate rational evaluation points for exact logarithmic targets."""

    def __init__(self, limits: LogFrequencyGridLimits = _DEFAULT_LIMITS) -> None:
        if type(limits) is not LogFrequencyGridLimits:
            raise TypeError("limits must be LogFrequencyGridLimits.")
        self._limits = limits

    def generate(
        self,
        request: LogFrequencyGridRequest,
        *,
        field: str | None = None,
    ) -> LogFrequencyGridResult:
        """Return a complete certified grid or one value-free failure."""

        if type(request) is not LogFrequencyGridRequest:
            raise TypeError("request must be LogFrequencyGridRequest.")
        if field is not None and type(field) is not str:
            raise TypeError("field must be str or None.")
        try:
            validated = self._validate_request(request)
            return self._generate_validated(validated, field)
        except LogFrequencyGridFailure as failure:
            return self._failure(failure, field)
        except _RESOURCE_ERRORS as error:
            return self._failure(
                LogFrequencyGridFailure(
                    DiagnosticCode.LOG_FREQUENCY_GRID_RESOURCE_LIMIT_EXCEEDED,
                    "Die Rastererzeugung überschreitet verfügbare Ressourcen.",
                    (("exception", type(error).__name__),),
                ),
                field,
            )

    def _validate_request(
        self,
        request: LogFrequencyGridRequest,
    ) -> ValidatedLogFrequencyGridRequest:
        try:
            return validate_log_frequency_grid_request(request, self._limits)
        except LogFrequencyGridFailure:
            raise
        except _EXPECTED_VALIDATION_ERRORS as error:
            raise LogFrequencyGridFailure(
                DiagnosticCode.LOG_FREQUENCY_GRID_INVALID_REQUEST,
                "Der logarithmische Rasterauftrag ist ungültig.",
                (("exception", type(error).__name__),),
            ) from error

    def _generate_validated(
        self,
        validated: ValidatedLogFrequencyGridRequest,
        field: str | None,
    ) -> LogFrequencyGridResult:
        budget = CertificationBudget(self._limits.max_certification_steps)
        interval_count = determine_interval_count(
            validated,
            self._limits,
            budget,
        )
        exact_target_indices = tuple(
            find_exact_target_index(
                explicit,
                validated,
                interval_count,
                budget,
            )
            for explicit in validated.explicit_frequencies
        )
        validate_total_points(
            interval_count,
            exact_target_indices,
            self._limits,
        )
        explicit_by_target = {
            index: explicit
            for explicit, index in zip(
                validated.explicit_frequencies,
                exact_target_indices,
                strict=True,
            )
            if index is not None
        }
        epsilon = relative_error_limit(self._limits.grid_precision_digits)
        generated: dict[Fraction, _GridPointData] = {}
        for target_index in range(interval_count + 1):
            data = self._generated_point(
                validated,
                target_index,
                interval_count,
                explicit_by_target.get(target_index),
                epsilon,
                budget,
            )
            if data.evaluation_frequency in generated:
                raise self._precision_collision()
            generated[data.evaluation_frequency] = data

        for explicit, target_match in zip(
            validated.explicit_frequencies,
            exact_target_indices,
            strict=True,
        ):
            if target_match is not None:
                continue
            if explicit in generated:
                raise self._precision_collision()
            generated[explicit] = _GridPointData(
                explicit,
                self._display_decimal(explicit),
                None,
                (LogFrequencyPointOrigin.EXPLICIT,),
                Fraction(0),
            )
        ordered_data = tuple(
            generated[value] for value in sorted(generated)
        )
        target_sequence = tuple(
            data.target_index
            for data in ordered_data
            if data.target_index is not None
        )
        if (
            ordered_data[0].evaluation_frequency != validated.omega_min
            or ordered_data[-1].evaluation_frequency != validated.omega_max
            or target_sequence != tuple(range(interval_count + 1))
        ):
            raise self._precision_collision()
        points = tuple(
            self._public_point(data, interval_count) for data in ordered_data
        )
        result = LogFrequencyGridResult._create(
            request=validated.request,
            interval_count=interval_count,
            status=LogFrequencyGridStatus.COMPLETE,
            points=points,
            diagnostics=tuple(
                diagnostic
                for point in points
                for diagnostic in point.diagnostics
            ),
        )
        validate_log_frequency_grid_result(result, self._limits)
        return result

    def _generated_point(
        self,
        validated: ValidatedLogFrequencyGridRequest,
        target_index: int,
        interval_count: int,
        exact_explicit: Fraction | None,
        epsilon: Fraction,
        budget: CertificationBudget,
    ) -> _GridPointData:
        if target_index == 0:
            origins = [LogFrequencyPointOrigin.LOWER_BOUND]
            if exact_explicit is not None:
                origins.append(LogFrequencyPointOrigin.EXPLICIT)
            return _GridPointData(
                validated.omega_min,
                self._display_decimal(validated.omega_min),
                target_index,
                _canonical_origins(origins),
                Fraction(0),
            )
        if target_index == interval_count:
            origins = [LogFrequencyPointOrigin.UPPER_BOUND]
            if exact_explicit is not None:
                origins.append(LogFrequencyPointOrigin.EXPLICIT)
            return _GridPointData(
                validated.omega_max,
                self._display_decimal(validated.omega_max),
                target_index,
                _canonical_origins(origins),
                Fraction(0),
            )
        origins = [LogFrequencyPointOrigin.GENERATED]
        if exact_explicit is not None:
            origins.append(LogFrequencyPointOrigin.EXPLICIT)
            return _GridPointData(
                exact_explicit,
                self._display_decimal(exact_explicit),
                target_index,
                _canonical_origins(origins),
                Fraction(0),
            )
        target_decimal, candidate = self._certified_candidate(
            validated,
            target_index,
            interval_count,
            epsilon,
            budget,
        )
        return _GridPointData(
            candidate,
            target_decimal,
            target_index,
            _canonical_origins(origins),
            epsilon,
        )

    def _certified_candidate(
        self,
        validated: ValidatedLogFrequencyGridRequest,
        target_index: int,
        interval_count: int,
        epsilon: Fraction,
        budget: CertificationBudget,
    ) -> tuple[ScientificDecimal, Fraction]:
        for attempt in range(1, self._limits.max_certification_attempts + 1):
            try:
                target_decimal, candidate = approximate_logarithmic_target(
                    validated.omega_min,
                    validated.ratio,
                    target_index,
                    interval_count,
                    precision_digits=self._limits.grid_precision_digits,
                    guard_digits=self._limits.grid_guard_digits * attempt,
                )
            except LogFrequencyGridNumericError:
                continue
            validate_output_rational(candidate, self._limits)
            if certifies_relative_error(
                candidate=candidate,
                omega_min=validated.omega_min,
                ratio=validated.ratio,
                target_index=target_index,
                interval_count=interval_count,
                epsilon=epsilon,
                budget=budget,
            ):
                return target_decimal, candidate
        raise LogFrequencyGridFailure(
            DiagnosticCode.LOG_FREQUENCY_GRID_CERTIFICATION_FAILED,
            "Eine logarithmische Zielfrequenz konnte nicht zertifiziert werden.",
            (
                ("target_index", str(target_index)),
                ("attempts", str(self._limits.max_certification_attempts)),
            ),
        )

    def _display_decimal(self, value: Fraction) -> ScientificDecimal:
        try:
            return approximate_rational_for_display(
                value,
                precision_digits=self._limits.grid_precision_digits,
                guard_digits=self._limits.grid_guard_digits,
            )
        except LogFrequencyGridNumericError as error:
            raise LogFrequencyGridFailure(
                DiagnosticCode.LOG_FREQUENCY_GRID_CERTIFICATION_FAILED,
                "Eine Frequenz besitzt keine endliche Dezimaldarstellung.",
            ) from error

    def _public_point(
        self,
        data: _GridPointData,
        interval_count: int,
    ) -> LogFrequencyGridPoint:
        validate_output_rational(data.evaluation_frequency, self._limits)
        return LogFrequencyGridPoint._create(
            evaluation_frequency=_exact_rational(data.evaluation_frequency),
            target_decimal=data.target_decimal,
            target_index=data.target_index,
            target_interval_count=(
                interval_count if data.target_index is not None else None
            ),
            origins=data.origins,
            maximum_relative_error=_exact_rational(
                data.maximum_relative_error
            ),
        )

    @staticmethod
    def _precision_collision() -> LogFrequencyGridFailure:
        return LogFrequencyGridFailure(
            DiagnosticCode.LOG_FREQUENCY_GRID_PRECISION_COLLISION,
            "Verschiedene Zielpunkte fallen auf dieselbe Auswertungsfrequenz.",
        )

    def _failure(
        self,
        failure: LogFrequencyGridFailure,
        field: str | None,
    ) -> LogFrequencyGridResult:
        result = LogFrequencyGridResult._create(
            request=None,
            interval_count=None,
            status=LogFrequencyGridStatus.FAILED,
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
        validate_log_frequency_grid_result(result, self._limits)
        return result


def _canonical_origins(
    origins: list[LogFrequencyPointOrigin],
) -> tuple[LogFrequencyPointOrigin, ...]:
    return tuple(sorted(set(origins), key=_ORIGIN_ORDER.__getitem__))


def _exact_rational(value: Fraction) -> ExactRationalValue:
    return ExactRationalValue(value.numerator, value.denominator)


__all__ = ["LogFrequencyGridGenerator"]
