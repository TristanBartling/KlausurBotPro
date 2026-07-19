"""Exact interval sizing and deterministic logarithmic target generation."""

from decimal import ROUND_DOWN, Inexact, localcontext
from fractions import Fraction

import pytest

from klausurbotpro.domain import (
    ExactRationalValue,
    LogFrequencyGridGenerator,
    LogFrequencyGridRequest,
    LogFrequencyGridStatus,
    LogFrequencyPointOrigin,
)


@pytest.mark.parametrize(
    ("omega_min", "omega_max", "points_per_decade", "intervals"),
    [
        (ExactRationalValue(1), ExactRationalValue(10), 10, 10),
        (ExactRationalValue(1), ExactRationalValue(100), 5, 10),
        (ExactRationalValue(1), ExactRationalValue(20), 10, 14),
        (ExactRationalValue(1), ExactRationalValue(3), 7, 4),
    ],
)
def test_interval_count_is_exact_for_integer_and_partial_decades(
    omega_min: ExactRationalValue,
    omega_max: ExactRationalValue,
    points_per_decade: int,
    intervals: int,
) -> None:
    result = LogFrequencyGridGenerator().generate(
        LogFrequencyGridRequest(
            omega_min,
            omega_max,
            points_per_decade,
        )
    )

    assert result.status is LogFrequencyGridStatus.COMPLETE
    assert result.interval_count == intervals
    assert len(result.points) == intervals + 1


def test_rational_bounds_are_exact_and_grid_is_strictly_monotone() -> None:
    request = LogFrequencyGridRequest(
        ExactRationalValue(1, 10),
        ExactRationalValue(10),
        5,
    )
    result = LogFrequencyGridGenerator().generate(request)

    assert result.points[0].evaluation_frequency == request.omega_min
    assert result.points[-1].evaluation_frequency == request.omega_max
    assert result.points[0].origins == (
        LogFrequencyPointOrigin.LOWER_BOUND,
    )
    assert result.points[-1].origins == (
        LogFrequencyPointOrigin.UPPER_BOUND,
    )
    assert result.points[0].target_index == 0
    assert result.points[-1].target_index == result.interval_count
    assert result.points[0].maximum_relative_error == ExactRationalValue(0)
    assert result.points[-1].maximum_relative_error == ExactRationalValue(0)
    values = tuple(
        Fraction(
            point.evaluation_frequency.numerator,
            point.evaluation_frequency.denominator,
        )
        for point in result.points
    )
    assert all(
        left < right for left, right in zip(values, values[1:], strict=False)
    )


def test_inner_sqrt_ten_target_is_rationalized_and_structurally_described() -> None:
    result = LogFrequencyGridGenerator().generate(
        LogFrequencyGridRequest(
            ExactRationalValue(1),
            ExactRationalValue(10),
            2,
        )
    )
    point = result.points[1]

    assert result.interval_count == 2
    assert point.target_index == 1
    assert point.target_interval_count == 2
    assert point.origins == (LogFrequencyPointOrigin.GENERATED,)
    assert point.target_decimal.scientific_text.startswith("3.162277660168")
    assert point.evaluation_frequency == ExactRationalValue(
        point.target_decimal.significand,
        10 ** (-point.target_decimal.exponent10),
    )
    assert point.maximum_relative_error.numerator > 0


def test_repeated_generation_is_fully_deterministic() -> None:
    request = LogFrequencyGridRequest(
        ExactRationalValue(1, 10),
        ExactRationalValue(20),
        7,
        (ExactRationalValue(1), ExactRationalValue(2)),
    )
    generator = LogFrequencyGridGenerator()

    assert generator.generate(request) == generator.generate(request)


def test_generation_is_independent_of_global_decimal_context() -> None:
    request = LogFrequencyGridRequest(
        ExactRationalValue(1),
        ExactRationalValue(10),
        3,
    )
    generator = LogFrequencyGridGenerator()
    expected = generator.generate(request)

    with localcontext() as context:
        context.prec = 3
        context.rounding = ROUND_DOWN
        context.traps[Inexact] = True
        actual = generator.generate(request)

    assert actual == expected


def test_successful_result_owns_a_disjoint_validated_request_snapshot() -> None:
    lower = ExactRationalValue(1)
    request = LogFrequencyGridRequest(
        lower,
        ExactRationalValue(10),
        2,
    )
    result = LogFrequencyGridGenerator().generate(request)
    assert result.request is not None
    assert result.request is not request
    assert result.request.omega_min is not lower

    object.__setattr__(lower, "numerator", 2)

    assert result.request.omega_min == ExactRationalValue(1)
