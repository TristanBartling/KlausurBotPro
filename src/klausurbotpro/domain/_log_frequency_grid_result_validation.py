"""Independent defensive revalidation of logarithmic frequency-grid results."""

from __future__ import annotations

from fractions import Fraction

from klausurbotpro.domain._log_frequency_grid_certification import (
    certifies_relative_error,
    relative_error_limit,
)
from klausurbotpro.domain._log_frequency_grid_numeric import (
    LogFrequencyGridNumericError,
    approximate_rational_for_display,
    fraction_from_scientific_decimal,
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

_NESTED_VALIDATION_ERRORS = (
    AttributeError,
    IndexError,
    TypeError,
    ValueError,
)


def validate_log_frequency_grid_result(
    result: LogFrequencyGridResult,
    limits: LogFrequencyGridLimits,
) -> None:
    """Revalidate a complete grid independently of its generator run."""

    if type(result) is not LogFrequencyGridResult:
        raise TypeError("result must be LogFrequencyGridResult.")
    if type(limits) is not LogFrequencyGridLimits:
        raise TypeError("limits must be LogFrequencyGridLimits.")
    try:
        _validate_result(result, limits)
    except LogFrequencyGridFailure:
        raise
    except _NESTED_VALIDATION_ERRORS as error:
        raise _invalid_result(
            "Das logarithmische Rasterergebnis enthält ungültige Werte.",
            exception=error,
        ) from error


def _validate_result(
    result: LogFrequencyGridResult,
    limits: LogFrequencyGridLimits,
) -> None:
    if type(result.status) is not LogFrequencyGridStatus:
        raise _invalid_result("Der Rasterstatus ist ungültig.")
    diagnostics = _validated_diagnostics(result.diagnostics, limits)
    if result.status is LogFrequencyGridStatus.FAILED:
        if (
            result.request is not None
            or result.interval_count is not None
            or result.points != ()
            or not any(
                diagnostic.severity is DiagnosticSeverity.ERROR
                for diagnostic in diagnostics
            )
        ):
            raise _invalid_result(
                "Ein fehlgeschlagenes Raster darf keine Eingangswerte behalten."
            )
        return
    if any(
        diagnostic.severity is DiagnosticSeverity.ERROR
        for diagnostic in diagnostics
    ):
        raise _invalid_result("Ein vollständiges Raster darf keinen Fehler enthalten.")
    if type(result.request) is not LogFrequencyGridRequest:
        raise _invalid_result("Ein vollständiges Raster benötigt einen Request.")
    validated = validate_log_frequency_grid_request(result.request, limits)
    budget = CertificationBudget(limits.max_certification_steps)
    expected_interval_count = determine_interval_count(validated, limits, budget)
    if (
        type(result.interval_count) is not int
        or result.interval_count != expected_interval_count
    ):
        raise _invalid_result("Die gespeicherte Intervallzahl ist nicht exakt.")
    exact_target_indices = tuple(
        find_exact_target_index(
            explicit,
            validated,
            expected_interval_count,
            budget,
        )
        for explicit in validated.explicit_frequencies
    )
    validate_total_points(
        expected_interval_count,
        exact_target_indices,
        limits,
        validated,
    )
    if type(result.points) is not tuple or any(
        type(point) is not LogFrequencyGridPoint for point in result.points
    ):
        raise _invalid_result("Rasterpunkte müssen als exaktes Tupel vorliegen.")
    expected_point_count = expected_interval_count + 1 + sum(
        index is None for index in exact_target_indices
    )
    if (
        len(result.points) != expected_point_count
        or len(result.points) > limits.max_total_points
    ):
        raise _invalid_result("Die Anzahl der Rasterpunkte ist inkonsistent.")
    explicit_by_target = {
        index: explicit
        for explicit, index in zip(
            validated.explicit_frequencies,
            exact_target_indices,
            strict=True,
        )
        if index is not None
    }
    standalone_explicit = frozenset(
        explicit
        for explicit, index in zip(
            validated.explicit_frequencies,
            exact_target_indices,
            strict=True,
        )
        if index is None
    )
    seen_targets: set[int] = set()
    seen_standalone_explicit: set[Fraction] = set()
    previous: Fraction | None = None
    for point in result.points:
        point._validate()
        if point.diagnostics:
            raise _invalid_result(
                "Rasterpunkte der aktuellen Phase besitzen keine Diagnosen."
            )
        evaluation = _validated_point_rational(point.evaluation_frequency, limits)
        if (
            evaluation < validated.omega_min
            or evaluation > validated.omega_max
            or (previous is not None and evaluation <= previous)
        ):
            raise _invalid_result(
                "Rasterfrequenzen müssen innerhalb der Grenzen streng steigen."
            )
        previous = evaluation
        if point.target_index is None:
            _validate_standalone_explicit(
                point,
                evaluation,
                standalone_explicit,
                seen_standalone_explicit,
                limits,
            )
            continue
        target_index = point.target_index
        if (
            type(target_index) is not int
            or target_index in seen_targets
            or point.target_interval_count != expected_interval_count
        ):
            raise _invalid_result("Zielindizes oder Intervallbezüge sind inkonsistent.")
        seen_targets.add(target_index)
        _validate_target_point(
            point,
            evaluation,
            target_index,
            expected_interval_count,
            validated,
            explicit_by_target.get(target_index),
            limits,
            budget,
        )
    if seen_targets != set(range(expected_interval_count + 1)):
        raise _invalid_result("Das Raster enthält nicht jeden Zielindex genau einmal.")
    if seen_standalone_explicit != standalone_explicit:
        raise _invalid_result("Explizite Zusatzfrequenzen fehlen im Raster.")
    if diagnostics:
        raise _invalid_result(
            "Ein vollständiges Raster der aktuellen Phase besitzt keine Diagnosen."
        )


def _validate_target_point(
    point: LogFrequencyGridPoint,
    evaluation: Fraction,
    target_index: int,
    interval_count: int,
    validated: ValidatedLogFrequencyGridRequest,
    exact_explicit: Fraction | None,
    limits: LogFrequencyGridLimits,
    budget: CertificationBudget,
) -> None:
    expected_evaluation: Fraction | None
    expected_origins: tuple[LogFrequencyPointOrigin, ...]
    if target_index == 0:
        expected_evaluation = validated.omega_min
        expected_origins = (LogFrequencyPointOrigin.LOWER_BOUND,)
    elif target_index == interval_count:
        expected_evaluation = validated.omega_max
        expected_origins = (LogFrequencyPointOrigin.UPPER_BOUND,)
    else:
        expected_evaluation = exact_explicit
        expected_origins = (LogFrequencyPointOrigin.GENERATED,)
    if exact_explicit is not None:
        expected_origins += (LogFrequencyPointOrigin.EXPLICIT,)
    if point.origins != expected_origins:
        raise _invalid_result("Die Herkunft eines Rasterzielpunkts ist inkonsistent.")
    if target_index in (0, interval_count) or exact_explicit is not None:
        if evaluation != expected_evaluation:
            raise _invalid_result("Ein exakter Rasterzielpunkt wurde verändert.")
        if point.maximum_relative_error != ExactRationalValue(0):
            raise _invalid_result("Ein exakter Rasterzielpunkt benötigt Fehler null.")
        _validate_display_decimal(point.target_decimal, evaluation, limits)
        return
    error = _validated_error(point.maximum_relative_error, limits)
    epsilon = relative_error_limit(limits.grid_precision_digits)
    if error != epsilon:
        raise _invalid_result("Die gespeicherte Approximationsgrenze ist inkonsistent.")
    _validate_scientific_decimal(point.target_decimal, limits)
    if fraction_from_scientific_decimal(point.target_decimal) != evaluation:
        raise _invalid_result(
            "Zieldezimalwert und rationale Auswertungsfrequenz widersprechen sich."
        )
    if not certifies_relative_error(
        candidate=evaluation,
        omega_min=validated.omega_min,
        ratio=validated.ratio,
        target_index=target_index,
        interval_count=interval_count,
        epsilon=epsilon,
        budget=budget,
    ):
        raise _invalid_result("Eine generierte Rasterfrequenz ist nicht zertifiziert.")


def _validate_standalone_explicit(
    point: LogFrequencyGridPoint,
    evaluation: Fraction,
    expected: frozenset[Fraction],
    seen: set[Fraction],
    limits: LogFrequencyGridLimits,
) -> None:
    if (
        evaluation not in expected
        or evaluation in seen
        or point.origins != (LogFrequencyPointOrigin.EXPLICIT,)
        or point.maximum_relative_error != ExactRationalValue(0)
    ):
        raise _invalid_result("Ein expliziter Rasterpunkt ist inkonsistent.")
    _validate_display_decimal(point.target_decimal, evaluation, limits)
    seen.add(evaluation)


def _validate_display_decimal(
    value: ScientificDecimal,
    exact_value: Fraction,
    limits: LogFrequencyGridLimits,
) -> None:
    _validate_scientific_decimal(value, limits)
    try:
        expected = approximate_rational_for_display(
            exact_value,
            precision_digits=limits.grid_precision_digits,
            guard_digits=limits.grid_guard_digits,
        )
    except LogFrequencyGridNumericError as error:
        raise _invalid_result(
            "Die deterministische Dezimalanzeige konnte nicht geprüft werden.",
            exception=error,
        ) from error
    if value != expected:
        raise _invalid_result("Die Dezimalanzeige eines exakten Punkts ist verändert.")


def _validate_scientific_decimal(
    value: ScientificDecimal,
    limits: LogFrequencyGridLimits,
) -> None:
    if type(value) is not ScientificDecimal:
        raise _invalid_result("Ein Zieldezimalwert besitzt den falschen Typ.")
    if (
        type(value.significand) is not int
        or type(value.exponent10) is not int
        or value.significand <= 0
        or value.significand % 10 == 0
        or value.significand >= 10**limits.grid_precision_digits
        or abs(value.exponent10)
        > limits.max_rational_integer_digits + limits.grid_precision_digits
    ):
        raise _invalid_result(
            "Ein Zieldezimalwert ist nicht kanonisch oder überschreitet Grenzen."
        )


def _validated_point_rational(
    value: ExactRationalValue,
    limits: LogFrequencyGridLimits,
) -> Fraction:
    if type(value) is not ExactRationalValue:
        raise _invalid_result("Eine Auswertungsfrequenz ist nicht exakt rational.")
    rational = Fraction(value.numerator, value.denominator)
    if (
        rational <= 0
        or rational.numerator != value.numerator
        or rational.denominator != value.denominator
    ):
        raise _invalid_result("Eine Auswertungsfrequenz ist nicht kanonisch.")
    validate_output_rational(rational, limits)
    return rational


def _validated_error(
    value: ExactRationalValue,
    limits: LogFrequencyGridLimits,
) -> Fraction:
    if type(value) is not ExactRationalValue:
        raise _invalid_result("Eine Fehlergrenze ist nicht exakt rational.")
    rational = Fraction(value.numerator, value.denominator)
    if (
        rational <= 0
        or rational >= 1
        or rational.numerator != value.numerator
        or rational.denominator != value.denominator
    ):
        raise _invalid_result("Eine Fehlergrenze ist nicht kanonisch.")
    validate_output_rational(rational, limits)
    return rational


def _validated_diagnostics(
    diagnostics: tuple[Diagnostic, ...],
    limits: LogFrequencyGridLimits,
) -> tuple[Diagnostic, ...]:
    if type(diagnostics) is not tuple or any(
        type(diagnostic) is not Diagnostic for diagnostic in diagnostics
    ):
        raise _invalid_result("Rasterdiagnosen müssen ein exaktes Tupel bilden.")
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
                or any(type(item) is not str for item in detail)
                for detail in diagnostic.technical_details
            )
        ):
            raise _invalid_result("Eine Rasterdiagnose ist manipuliert.")
    if len(diagnostics) > limits.max_diagnostics:
        raise LogFrequencyGridFailure(
            DiagnosticCode.LOG_FREQUENCY_GRID_LIMIT_EXCEEDED,
            "Das Raster enthält zu viele Diagnosen.",
            (("limit", "max_diagnostics"),),
        )
    return diagnostics


def _invalid_result(
    message: str,
    *,
    exception: BaseException | None = None,
) -> LogFrequencyGridFailure:
    details = (
        (("exception", type(exception).__name__),)
        if exception is not None
        else ()
    )
    return LogFrequencyGridFailure(
        DiagnosticCode.LOG_FREQUENCY_GRID_INVALID_REQUEST,
        message,
        details,
    )


__all__ = ["validate_log_frequency_grid_result"]
