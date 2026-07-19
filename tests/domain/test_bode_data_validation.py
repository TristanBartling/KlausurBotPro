"""Defensive result-boundary tests for structured Bode data."""

from __future__ import annotations

import pytest
import sympy as sp

from klausurbotpro.domain import (
    BodeDataLimits,
    BodeDataStatus,
    BodePlotPoint,
    ExactExpression,
    ExactRationalValue,
    FrequencyResponseLimits,
    LogFrequencyGridGenerator,
    LogFrequencyGridLimits,
    LogFrequencyGridRequest,
    PolynomialFactory,
    ReducedTransferFunction,
    TransferFunctionBodeDataAnalyzer,
    TransferFunctionBodeDataResult,
)
from klausurbotpro.domain._bode_data_validation import (
    BodeDataFailure,
    validate_bode_data_result,
)


def _result() -> TransferFunctionBodeDataResult:
    s = sp.Symbol("s")
    factory = PolynomialFactory()
    numerator = factory.create(
        ExactExpression._from_sympy(sp.Integer(1))
    ).value
    denominator = factory.create(ExactExpression._from_sympy(s**2 + 1)).value
    assert numerator is not None
    assert denominator is not None
    reduced = ReducedTransferFunction._create(
        variable_name="s",
        numerator=numerator,
        denominator=denominator,
        prerequisites=(),
        domain_exclusions=(),
    )
    grid = LogFrequencyGridGenerator().generate(
        LogFrequencyGridRequest(
            ExactRationalValue(1),
            ExactRationalValue(100),
            2,
        )
    )
    return TransferFunctionBodeDataAnalyzer().analyze(reduced, grid)


def _validate(result: object) -> None:
    validate_bode_data_result(
        result,  # type: ignore[arg-type]
        frequency_limits=FrequencyResponseLimits(),
        grid_limits=LogFrequencyGridLimits(),
        bode_limits=BodeDataLimits(),
    )


def test_unmodified_result_passes_independent_revalidation() -> None:
    _validate(_result())


@pytest.mark.parametrize(
    ("attribute", "value"),
    [
        ("status", BodeDataStatus.COMPLETE),
        ("points", ()),
        ("magnitude_segments", ()),
        ("phase_segments", ()),
        ("axis_metadata", None),
        ("diagnostics", ()),
    ],
)
def test_manipulated_result_is_rejected(
    attribute: str,
    value: object,
) -> None:
    result = _result()
    object.__setattr__(result, attribute, value)

    with pytest.raises(BodeDataFailure):
        _validate(result)


def test_reordered_bode_points_are_rejected() -> None:
    result = _result()
    object.__setattr__(result, "points", tuple(reversed(result.points)))

    with pytest.raises(BodeDataFailure):
        _validate(result)


@pytest.mark.parametrize(
    ("attribute", "value"),
    [
        ("magnitude_plottable", False),
        ("phase_plottable", False),
        ("evaluation_frequency", ExactRationalValue(2)),
        ("target_decimal", object()),
        ("frequency_response_point", object()),
    ],
)
def test_manipulated_bode_point_is_rejected(
    attribute: str,
    value: object,
) -> None:
    result = _result()
    point = result.points[1]
    object.__setattr__(point, attribute, value)

    with pytest.raises(BodeDataFailure):
        _validate(result)


@pytest.mark.parametrize(
    ("attribute", "value"),
    [
        ("segment_index", 4),
        ("start_grid_index", 0),
        ("end_grid_index", 99),
        ("points", ()),
    ],
)
def test_manipulated_segment_is_rejected(
    attribute: str,
    value: object,
) -> None:
    result = _result()
    segment = result.magnitude_segments[0]
    object.__setattr__(segment, attribute, value)

    with pytest.raises(BodeDataFailure):
        _validate(result)


@pytest.mark.parametrize("segment_attribute", ["magnitude_segments", "phase_segments"])
@pytest.mark.parametrize(
    "manipulation",
    [
        "equal_clone",
        "foreign_point",
        "repeated_point",
        "swapped_points",
        "foreign_points_same_bounds",
        "shared_between_segments",
        "skipped_plottable_point",
        "connected_over_singularity",
    ],
)
def test_segment_points_must_be_identical_maximal_source_ranges(
    segment_attribute: str,
    manipulation: str,
) -> None:
    result = _result()
    segments = getattr(result, segment_attribute)
    segment = segments[0]

    if manipulation == "equal_clone":
        source = segment.points[0]
        clone = BodePlotPoint._create(
            grid_point=source.grid_point,
            frequency_response_point=source.frequency_response_point,
        )
        object.__setattr__(
            segment,
            "points",
            (clone,) + segment.points[1:],
        )
    elif manipulation in ("foreign_point", "foreign_points_same_bounds"):
        foreign_result = _result()
        foreign_points = getattr(
            foreign_result,
            segment_attribute,
        )[0].points
        replacement = (
            (foreign_points[0],) + segment.points[1:]
            if manipulation == "foreign_point"
            else foreign_points
        )
        object.__setattr__(segment, "points", replacement)
    elif manipulation == "repeated_point":
        object.__setattr__(
            segment,
            "points",
            (segment.points[0], segment.points[0]) + segment.points[2:],
        )
    elif manipulation == "swapped_points":
        object.__setattr__(
            segment,
            "points",
            (
                segment.points[1],
                segment.points[0],
            )
            + segment.points[2:],
        )
    elif manipulation == "shared_between_segments":
        duplicate = type(segment)._create(
            1,
            (segment.points[0],),
            segment.start_grid_index,
            segment.start_grid_index,
        )
        object.__setattr__(
            result,
            segment_attribute,
            (segment, duplicate),
        )
    elif manipulation == "skipped_plottable_point":
        object.__setattr__(segment, "start_grid_index", segment.start_grid_index + 1)
        object.__setattr__(segment, "points", segment.points[1:])
    else:
        object.__setattr__(segment, "start_grid_index", 0)
        object.__setattr__(
            segment,
            "points",
            (result.points[0],) + segment.points,
        )

    with pytest.raises(BodeDataFailure):
        _validate(result)


def test_revalidation_applies_current_projection_limits_without_rounding() -> None:
    result = _result()

    with pytest.raises(BodeDataFailure):
        validate_bode_data_result(
            result,
            frequency_limits=FrequencyResponseLimits(),
            grid_limits=LogFrequencyGridLimits(),
            bode_limits=BodeDataLimits(max_plot_decimal_digits=2),
        )


def test_wrong_result_top_level_type_raises_type_error() -> None:
    with pytest.raises(TypeError):
        _validate(object())
