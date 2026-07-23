"""Pure table projections for already computed frequency-domain results."""

from __future__ import annotations

from enum import StrEnum
from math import log

from klausurbotpro.application.frequency_domain_workflow_contracts import (
    FrequencyDomainWorkflowResult,
)
from klausurbotpro.domain import ExactRationalValue, FrequencyResponsePointStatus

COMPACT_FREQUENCY_TABLE_TARGET_SIZE = 12


class FrequencyTableScope(StrEnum):
    """Visible/exported extent of an already computed Bode table."""

    COMPACT = "compact"
    FULL_GRID = "full_grid"


def select_frequency_table_indices(
    result: FrequencyDomainWorkflowResult,
    *,
    scope: FrequencyTableScope = FrequencyTableScope.COMPACT,
    selected_bode_index: int = 0,
    added_frequencies: tuple[ExactRationalValue, ...] = (),
) -> tuple[int, ...]:
    """Select original Bode indices without evaluating another frequency."""

    if type(result) is not FrequencyDomainWorkflowResult:
        raise TypeError("result must be a FrequencyDomainWorkflowResult.")
    if type(scope) is not FrequencyTableScope:
        raise TypeError("scope must be a FrequencyTableScope.")
    if type(selected_bode_index) is not int or selected_bode_index < 0:
        raise ValueError("selected_bode_index must be a nonnegative int.")
    if type(added_frequencies) is not tuple or any(
        type(value) is not ExactRationalValue for value in added_frequencies
    ):
        raise TypeError("added_frequencies must contain exact rationals.")
    bode = result.bode_data_result
    if bode is None or not bode.points:
        return ()
    point_count = len(bode.points)
    if selected_bode_index >= point_count:
        raise ValueError("selected_bode_index exceeds the Bode table.")
    if scope is FrequencyTableScope.FULL_GRID:
        return tuple(range(point_count))

    mandatory = {0, point_count - 1, selected_bode_index}
    requested_frequencies = set(added_frequencies)
    if result.request is not None and result.request.grid_request is not None:
        requested_frequencies.update(
            result.request.grid_request.explicit_frequencies
        )
    mandatory.update(
        index
        for index, point in enumerate(bode.points)
        if point.evaluation_frequency in requested_frequencies
        or point.frequency_response_point.status
        is not FrequencyResponsePointStatus.DEFINED
    )
    crossover = result.crossover_analysis
    if crossover is not None:
        for item in (*crossover.gain_crossovers, *crossover.phase_crossovers):
            mandatory.add(_nearest_frequency_index(result, item.frequency))

    selected = set(mandatory)
    target_size = min(COMPACT_FREQUENCY_TABLE_TARGET_SIZE, point_count)
    while len(selected) < target_size:
        remaining = (index for index in range(point_count) if index not in selected)
        next_index = max(
            remaining,
            key=lambda index: (
                min(abs(index - chosen) for chosen in selected),
                -index,
            ),
        )
        selected.add(next_index)
    return tuple(sorted(selected))


def _nearest_frequency_index(
    result: FrequencyDomainWorkflowResult,
    target_frequency: float,
) -> int:
    """Return the existing point with minimum logarithmic frequency distance."""

    bode = result.bode_data_result
    assert bode is not None
    target_log = log(target_frequency)
    return min(
        range(len(bode.points)),
        key=lambda index: (
            abs(
                log(
                    bode.points[index].evaluation_frequency.numerator
                    / bode.points[index].evaluation_frequency.denominator
                )
                - target_log
            ),
            index,
        ),
    )


__all__ = [
    "COMPACT_FREQUENCY_TABLE_TARGET_SIZE",
    "FrequencyTableScope",
    "select_frequency_table_indices",
]
