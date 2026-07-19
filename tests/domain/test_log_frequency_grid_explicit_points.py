"""Exact explicit-point insertion, provenance merging, and collisions."""

import pytest

from klausurbotpro.domain import (
    DiagnosticCode,
    ExactRationalValue,
    LogFrequencyGridGenerator,
    LogFrequencyGridLimits,
    LogFrequencyGridRequest,
    LogFrequencyGridStatus,
    LogFrequencyPointOrigin,
)


def test_explicit_inner_frequency_is_inserted_exactly_in_order() -> None:
    explicit = ExactRationalValue(3, 2)
    result = LogFrequencyGridGenerator().generate(
        LogFrequencyGridRequest(
            ExactRationalValue(1),
            ExactRationalValue(10),
            2,
            (explicit,),
        )
    )

    point = next(
        point for point in result.points if point.evaluation_frequency == explicit
    )
    assert point.target_index is None
    assert point.origins == (LogFrequencyPointOrigin.EXPLICIT,)
    assert point.maximum_relative_error == ExactRationalValue(0)


@pytest.mark.parametrize(
    ("explicit", "origins"),
    [
        (
            ExactRationalValue(1),
            (
                LogFrequencyPointOrigin.LOWER_BOUND,
                LogFrequencyPointOrigin.EXPLICIT,
            ),
        ),
        (
            ExactRationalValue(100),
            (
                LogFrequencyPointOrigin.UPPER_BOUND,
                LogFrequencyPointOrigin.EXPLICIT,
            ),
        ),
    ],
)
def test_explicit_bound_merges_origin_without_duplicate(
    explicit: ExactRationalValue,
    origins: tuple[LogFrequencyPointOrigin, ...],
) -> None:
    result = LogFrequencyGridGenerator().generate(
        LogFrequencyGridRequest(
            ExactRationalValue(1),
            ExactRationalValue(100),
            5,
            (explicit,),
        )
    )

    matches = tuple(
        point for point in result.points if point.evaluation_frequency == explicit
    )
    assert len(matches) == 1
    assert matches[0].origins == origins


def test_explicit_exact_inner_target_merges_generated_origin() -> None:
    result = LogFrequencyGridGenerator().generate(
        LogFrequencyGridRequest(
            ExactRationalValue(1),
            ExactRationalValue(100),
            5,
            (ExactRationalValue(10),),
        )
    )
    point = next(
        point
        for point in result.points
        if point.evaluation_frequency == ExactRationalValue(10)
    )

    assert len(result.points) == 11
    assert point.target_index == 5
    assert point.origins == (
        LogFrequencyPointOrigin.GENERATED,
        LogFrequencyPointOrigin.EXPLICIT,
    )


def test_exact_target_merge_is_counted_before_total_point_limit() -> None:
    result = LogFrequencyGridGenerator(
        LogFrequencyGridLimits(max_total_points=11)
    ).generate(
        LogFrequencyGridRequest(
            ExactRationalValue(1),
            ExactRationalValue(100),
            5,
            (ExactRationalValue(10),),
        )
    )

    assert result.status is LogFrequencyGridStatus.COMPLETE
    assert len(result.points) == 11


@pytest.mark.parametrize(
    "explicit",
    [
        (ExactRationalValue(2), ExactRationalValue(3, 2)),
        (ExactRationalValue(2), ExactRationalValue(2)),
        (ExactRationalValue(1, 2),),
        (ExactRationalValue(20),),
    ],
)
def test_invalid_explicit_sequences_are_structured_failures(
    explicit: tuple[ExactRationalValue, ...],
) -> None:
    result = LogFrequencyGridGenerator().generate(
        LogFrequencyGridRequest(
            ExactRationalValue(1),
            ExactRationalValue(10),
            2,
            explicit,
        )
    )

    assert result.status is LogFrequencyGridStatus.FAILED
    assert result.diagnostics[0].code is (
        DiagnosticCode.LOG_FREQUENCY_GRID_INVALID_EXPLICIT_FREQUENCIES
    )


def test_nonidentical_explicit_point_colliding_with_rounded_target_fails() -> None:
    result = LogFrequencyGridGenerator(
        LogFrequencyGridLimits(grid_precision_digits=2)
    ).generate(
        LogFrequencyGridRequest(
            ExactRationalValue(1),
            ExactRationalValue(2),
            10,
            (ExactRationalValue(6, 5),),
        )
    )

    assert result.status is LogFrequencyGridStatus.FAILED
    assert result.diagnostics[0].code is (
        DiagnosticCode.LOG_FREQUENCY_GRID_PRECISION_COLLISION
    )


def test_manipulated_noncanonical_explicit_value_has_specific_diagnostic() -> None:
    explicit = ExactRationalValue(2)
    request = LogFrequencyGridRequest(
        ExactRationalValue(1),
        ExactRationalValue(10),
        2,
        (explicit,),
    )
    object.__setattr__(explicit, "numerator", 2)
    object.__setattr__(explicit, "denominator", 2)

    result = LogFrequencyGridGenerator().generate(request)

    assert result.status is LogFrequencyGridStatus.FAILED
    assert result.diagnostics[0].code is (
        DiagnosticCode.LOG_FREQUENCY_GRID_INVALID_EXPLICIT_FREQUENCIES
    )
