"""Single authoritative status derivation for phase unwrapping."""

from klausurbotpro.domain.bode_data_contracts import BodeDataStatus
from klausurbotpro.domain.bode_phase_unwrap_contracts import (
    BodePhaseUnwrapStatus,
)


def derive_bode_phase_unwrap_status(
    source_status: BodeDataStatus,
    source_phase_segment_count: int,
) -> BodePhaseUnwrapStatus:
    if type(source_status) is not BodeDataStatus:
        raise TypeError("source_status must be BodeDataStatus.")
    if (
        type(source_phase_segment_count) is not int
        or source_phase_segment_count < 0
    ):
        raise ValueError("source_phase_segment_count must be non-negative.")
    if source_status is BodeDataStatus.FAILED:
        raise ValueError("A failed Bode result has no unwrap status.")
    if source_phase_segment_count == 0:
        return BodePhaseUnwrapStatus.NO_PHASE_DATA
    if source_status is BodeDataStatus.COMPLETE:
        return BodePhaseUnwrapStatus.COMPLETE
    if source_status is BodeDataStatus.PARTIAL:
        return BodePhaseUnwrapStatus.PARTIAL
    raise ValueError("A Bode status without phase data is inconsistent.")


__all__ = ["derive_bode_phase_unwrap_status"]
