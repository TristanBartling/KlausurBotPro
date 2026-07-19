"""Deterministic finite segmentation without interpolation or phase unwrapping."""

from __future__ import annotations

from collections.abc import Callable

from klausurbotpro.domain.bode_data_contracts import (
    BodeMagnitudeSegment,
    BodePhaseSegment,
    BodePlotPoint,
)


def build_bode_segments(
    points: tuple[BodePlotPoint, ...],
) -> tuple[
    tuple[BodeMagnitudeSegment, ...],
    tuple[BodePhaseSegment, ...],
]:
    return (
        _build_magnitude_segments(points),
        _build_phase_segments(points),
    )


def _build_magnitude_segments(
    points: tuple[BodePlotPoint, ...],
) -> tuple[BodeMagnitudeSegment, ...]:
    ranges = _contiguous_ranges(points, lambda point: point.magnitude_plottable)
    return tuple(
        BodeMagnitudeSegment._create(index, points[start : end + 1], start, end)
        for index, (start, end) in enumerate(ranges)
    )


def _build_phase_segments(
    points: tuple[BodePlotPoint, ...],
) -> tuple[BodePhaseSegment, ...]:
    ranges = _contiguous_ranges(points, lambda point: point.phase_plottable)
    return tuple(
        BodePhaseSegment._create(index, points[start : end + 1], start, end)
        for index, (start, end) in enumerate(ranges)
    )


def _contiguous_ranges(
    points: tuple[BodePlotPoint, ...],
    is_plottable: Callable[[BodePlotPoint], bool],
) -> tuple[tuple[int, int], ...]:
    ranges: list[tuple[int, int]] = []
    start: int | None = None
    for index, point in enumerate(points):
        if is_plottable(point):
            if start is None:
                start = index
        elif start is not None:
            ranges.append((start, index - 1))
            start = None
    if start is not None:
        ranges.append((start, len(points) - 1))
    return tuple(ranges)


__all__ = ["build_bode_segments"]
