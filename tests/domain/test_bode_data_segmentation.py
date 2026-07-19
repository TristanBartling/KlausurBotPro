"""Finite contiguous Bode-segment construction."""

from __future__ import annotations

import sympy as sp

from klausurbotpro.domain import (
    BodeDataStatus,
    ExactExpression,
    ExactRationalValue,
    LogFrequencyGridGenerator,
    LogFrequencyGridRequest,
    PolynomialFactory,
    ReducedTransferFunction,
    TransferFunctionBodeDataAnalyzer,
    TransferFunctionBodeDataResult,
)
from klausurbotpro.domain._bode_data_segmentation import build_bode_segments


def _analyze(
    numerator: sp.Expr,
    denominator: sp.Expr,
) -> TransferFunctionBodeDataResult:
    factory = PolynomialFactory()
    numerator_value = factory.create(
        ExactExpression._from_sympy(numerator)
    ).value
    denominator_value = factory.create(
        ExactExpression._from_sympy(denominator)
    ).value
    assert numerator_value is not None
    assert denominator_value is not None
    reduced = ReducedTransferFunction._create(
        variable_name="s",
        numerator=numerator_value,
        denominator=denominator_value,
        prerequisites=(),
        domain_exclusions=(),
    )
    grid = LogFrequencyGridGenerator().generate(
        LogFrequencyGridRequest(
            ExactRationalValue(1),
            ExactRationalValue(100),
            2,
            (ExactRationalValue(2),),
        )
    )
    return TransferFunctionBodeDataAnalyzer().analyze(reduced, grid)


def test_segment_builder_uses_only_contiguous_plottable_runs() -> None:
    s = sp.Symbol("s")
    result = _analyze(
        sp.Integer(1),
        (s**2 + 1) * (s**2 + 4),
    )

    magnitude, phase = build_bode_segments(result.points)

    assert result.status is BodeDataStatus.PARTIAL
    assert magnitude == result.magnitude_segments
    assert phase == result.phase_segments
    assert [segment.segment_index for segment in magnitude] == list(
        range(len(magnitude))
    )
    for segment in magnitude:
        assert segment.points == result.points[
            segment.start_grid_index : segment.end_grid_index + 1
        ]
        assert all(point.magnitude_plottable for point in segment.points)
    for phase_segment in phase:
        assert phase_segment.points == result.points[
            phase_segment.start_grid_index : phase_segment.end_grid_index + 1
        ]
        assert all(point.phase_plottable for point in phase_segment.points)


def test_zero_response_is_an_interruption_and_not_a_replacement_coordinate() -> None:
    s = sp.Symbol("s")
    result = _analyze(s**2 + 1, sp.Integer(1))
    zero_index = next(
        index
        for index, point in enumerate(result.points)
        if not point.magnitude_plottable
    )

    covered_indices = {
        index
        for segment in result.magnitude_segments
        for index in range(segment.start_grid_index, segment.end_grid_index + 1)
    }
    assert zero_index not in covered_indices
    assert all(
        segment.end_grid_index < zero_index
        or segment.start_grid_index > zero_index
        for segment in result.magnitude_segments
    )
