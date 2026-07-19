"""Independent grid-result revalidation against post-construction manipulation."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from klausurbotpro.domain import (
    Diagnostic,
    DiagnosticCode,
    DiagnosticSeverity,
    ExactRationalValue,
    LogFrequencyGridGenerator,
    LogFrequencyGridLimits,
    LogFrequencyGridRequest,
    LogFrequencyGridStatus,
    LogFrequencyPointOrigin,
    ScientificDecimal,
)
from klausurbotpro.domain._log_frequency_grid_result_validation import (
    validate_log_frequency_grid_result,
)
from klausurbotpro.domain._log_frequency_grid_validation import (
    LogFrequencyGridFailure,
)
from klausurbotpro.domain.log_frequency_grid_contracts import (
    LogFrequencyGridResult,
)


def _request(
    *,
    explicit: tuple[ExactRationalValue, ...] = (),
) -> LogFrequencyGridRequest:
    return LogFrequencyGridRequest(
        ExactRationalValue(1),
        ExactRationalValue(10),
        2,
        explicit,
    )


def _complete(
    *,
    explicit: tuple[ExactRationalValue, ...] = (),
) -> LogFrequencyGridResult:
    result = LogFrequencyGridGenerator().generate(_request(explicit=explicit))
    assert result.status is LogFrequencyGridStatus.COMPLETE
    return result


def _assert_rejected(
    result: LogFrequencyGridResult,
    mutate: Callable[[LogFrequencyGridResult], None],
) -> None:
    mutate(result)
    with pytest.raises(LogFrequencyGridFailure):
        validate_log_frequency_grid_result(result, LogFrequencyGridLimits())


def test_validator_accepts_complete_and_failed_generator_results() -> None:
    complete = _complete()
    failed = LogFrequencyGridGenerator().generate(
        LogFrequencyGridRequest(
            ExactRationalValue(0),
            ExactRationalValue(10),
            2,
        )
    )

    validate_log_frequency_grid_result(complete, LogFrequencyGridLimits())
    validate_log_frequency_grid_result(failed, LogFrequencyGridLimits())


def test_wrong_top_level_result_type_raises_type_error() -> None:
    with pytest.raises(TypeError, match="LogFrequencyGridResult"):
        validate_log_frequency_grid_result(
            object(),  # type: ignore[arg-type]
            LogFrequencyGridLimits(),
        )


def test_wrong_interval_count_is_recomputed_exactly() -> None:
    _assert_rejected(
        _complete(),
        lambda result: object.__setattr__(result, "interval_count", 3),
    )


@pytest.mark.parametrize(
    "attribute",
    ["omega_max", "points_per_decade"],
)
def test_manipulated_request_context_is_revalidated(attribute: str) -> None:
    result = _complete()
    assert result.request is not None
    replacement: object = (
        ExactRationalValue(20) if attribute == "omega_max" else 3
    )

    _assert_rejected(
        result,
        lambda value: object.__setattr__(
            value.request,
            attribute,
            replacement,
        ),
    )


def test_missing_explicit_point_is_rejected() -> None:
    result = _complete(explicit=(ExactRationalValue(3, 2),))
    explicit_index = next(
        index
        for index, point in enumerate(result.points)
        if point.target_index is None
    )
    _assert_rejected(
        result,
        lambda value: object.__setattr__(
            value,
            "points",
            value.points[:explicit_index] + value.points[explicit_index + 1 :],
        ),
    )


def test_foreign_explicit_origin_is_rejected() -> None:
    result = _complete()
    point = result.points[1]

    def mutate(value: LogFrequencyGridResult) -> None:
        object.__setattr__(
            point,
            "origins",
            (
                LogFrequencyPointOrigin.GENERATED,
                LogFrequencyPointOrigin.EXPLICIT,
            ),
        )
        object.__setattr__(
            point,
            "maximum_relative_error",
            ExactRationalValue(0),
        )

    _assert_rejected(result, mutate)


def test_explicit_target_without_explicit_origin_is_rejected() -> None:
    result = LogFrequencyGridGenerator().generate(
        LogFrequencyGridRequest(
            ExactRationalValue(1),
            ExactRationalValue(100),
            5,
            (ExactRationalValue(10),),
        )
    )
    point = next(point for point in result.points if point.target_index == 5)

    def mutate(value: LogFrequencyGridResult) -> None:
        object.__setattr__(
            point,
            "origins",
            (LogFrequencyPointOrigin.GENERATED,),
        )
        object.__setattr__(
            point,
            "maximum_relative_error",
            ExactRationalValue(1, 2 * 10**23),
        )

    _assert_rejected(result, mutate)


@pytest.mark.parametrize(
    ("attribute", "replacement"),
    [("target_index", 2), ("target_interval_count", 3)],
)
def test_wrong_target_coordinates_are_rejected(
    attribute: str,
    replacement: int,
) -> None:
    result = _complete()
    point = result.points[1]
    _assert_rejected(
        result,
        lambda value: object.__setattr__(point, attribute, replacement),
    )


def test_uncertified_generated_evaluation_frequency_is_rejected() -> None:
    result = _complete()
    point = result.points[1]

    def mutate(value: LogFrequencyGridResult) -> None:
        object.__setattr__(
            point,
            "evaluation_frequency",
            ExactRationalValue(2),
        )
        object.__setattr__(point, "target_decimal", ScientificDecimal(2, 0))

    _assert_rejected(result, mutate)


def test_manipulated_relative_error_is_rejected() -> None:
    result = _complete()
    point = result.points[1]
    _assert_rejected(
        result,
        lambda value: object.__setattr__(
            point,
            "maximum_relative_error",
            ExactRationalValue(1, 100),
        ),
    )


def test_manipulated_target_decimal_is_rejected() -> None:
    result = _complete()
    point = result.points[1]
    _assert_rejected(
        result,
        lambda value: object.__setattr__(
            point,
            "target_decimal",
            ScientificDecimal(32, -1),
        ),
    )


def test_additional_and_reordered_diagnostics_are_rejected() -> None:
    diagnostic = Diagnostic(
        DiagnosticSeverity.WARNING,
        DiagnosticCode.LOG_FREQUENCY_GRID_PRECISION_COLLISION,
        "manipulated",
    )
    additional = _complete()
    object.__setattr__(additional.points[0], "diagnostics", (diagnostic,))
    object.__setattr__(additional, "diagnostics", (diagnostic,))
    with pytest.raises(LogFrequencyGridFailure):
        validate_log_frequency_grid_result(additional, LogFrequencyGridLimits())

    reordered = _complete()
    first = Diagnostic(
        DiagnosticSeverity.INFO,
        DiagnosticCode.LOG_FREQUENCY_GRID_INVALID_REQUEST,
        "first",
    )
    second = Diagnostic(
        DiagnosticSeverity.WARNING,
        DiagnosticCode.LOG_FREQUENCY_GRID_INVALID_BOUNDS,
        "second",
    )
    object.__setattr__(reordered.points[0], "diagnostics", (first, second))
    object.__setattr__(reordered, "diagnostics", (second, first))
    with pytest.raises(LogFrequencyGridFailure):
        validate_log_frequency_grid_result(reordered, LogFrequencyGridLimits())


def test_max_diagnostics_is_enforced_for_failed_results() -> None:
    result = LogFrequencyGridGenerator().generate(
        LogFrequencyGridRequest(
            ExactRationalValue(0),
            ExactRationalValue(10),
            2,
        )
    )
    object.__setattr__(
        result,
        "diagnostics",
        result.diagnostics + result.diagnostics,
    )

    with pytest.raises(
        LogFrequencyGridFailure,
        match="zu viele Diagnosen",
    ):
        validate_log_frequency_grid_result(
            result,
            LogFrequencyGridLimits(max_diagnostics=1),
        )


def test_manipulated_failed_diagnostic_is_rejected() -> None:
    result = LogFrequencyGridGenerator().generate(
        LogFrequencyGridRequest(
            ExactRationalValue(0),
            ExactRationalValue(10),
            2,
        )
    )
    object.__setattr__(result.diagnostics[0], "code", object())

    with pytest.raises(LogFrequencyGridFailure):
        validate_log_frequency_grid_result(result, LogFrequencyGridLimits())


def test_nonmonotone_points_are_rejected() -> None:
    result = _complete()
    _assert_rejected(
        result,
        lambda value: object.__setattr__(
            value,
            "points",
            (value.points[1], value.points[0], *value.points[2:]),
        ),
    )


def test_foreign_point_outside_bounds_is_rejected() -> None:
    result = _complete(explicit=(ExactRationalValue(3, 2),))
    point = next(point for point in result.points if point.target_index is None)

    def mutate(value: LogFrequencyGridResult) -> None:
        object.__setattr__(
            point,
            "evaluation_frequency",
            ExactRationalValue(20),
        )
        object.__setattr__(point, "target_decimal", ScientificDecimal(2, 1))

    _assert_rejected(result, mutate)


def test_directly_manipulated_result_status_is_rejected() -> None:
    _assert_rejected(
        _complete(),
        lambda result: object.__setattr__(
            result,
            "status",
            LogFrequencyGridStatus.FAILED,
        ),
    )


def test_nested_invalid_types_are_normalized_to_grid_failure() -> None:
    result = _complete()
    assert result.request is not None
    object.__setattr__(result.request, "omega_min", object())

    with pytest.raises(LogFrequencyGridFailure):
        validate_log_frequency_grid_result(result, LogFrequencyGridLimits())


def test_generated_scientific_decimal_size_is_bounded_before_text_rendering() -> None:
    result = _complete()
    point = result.points[1]
    object.__setattr__(point.target_decimal, "exponent10", 10_000)

    with pytest.raises(LogFrequencyGridFailure):
        validate_log_frequency_grid_result(result, LogFrequencyGridLimits())
