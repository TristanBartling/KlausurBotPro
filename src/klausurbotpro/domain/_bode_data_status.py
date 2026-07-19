"""Single authoritative status derivation for structured Bode data."""

from __future__ import annotations

from klausurbotpro.domain.bode_data_contracts import BodeDataStatus
from klausurbotpro.domain.frequency_response_contracts import (
    FrequencyResponsePointStatus,
)


def derive_bode_data_status(
    statuses: tuple[FrequencyResponsePointStatus, ...],
) -> BodeDataStatus:
    if type(statuses) is not tuple or not statuses or any(
        type(status) is not FrequencyResponsePointStatus for status in statuses
    ):
        raise ValueError("Bode status requires an exact non-empty status tuple.")
    defined_count = statuses.count(FrequencyResponsePointStatus.DEFINED)
    if defined_count == len(statuses):
        return BodeDataStatus.COMPLETE
    if defined_count:
        return BodeDataStatus.PARTIAL
    if FrequencyResponsePointStatus.SYMBOLIC_UNDETERMINED in statuses:
        return BodeDataStatus.SYMBOLIC_UNDETERMINED
    return BodeDataStatus.NO_PLOTTABLE_DATA


__all__ = ["derive_bode_data_status"]
