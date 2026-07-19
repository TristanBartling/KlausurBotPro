"""Defensive result-boundary tests for structured Bode data."""

from __future__ import annotations

import pytest
import sympy as sp

from klausurbotpro.domain import (
    BodeDataLimits,
    BodeDataStatus,
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
