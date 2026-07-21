"""Method-neutral immutable stability-analysis contracts."""

from dataclasses import dataclass
from enum import StrEnum


class NumericalCheckStatus(StrEnum):
    CONSISTENT = "consistent"
    INCONSISTENT = "inconsistent"
    NUMERICALLY_INCONCLUSIVE = "numerically_inconclusive"


@dataclass(frozen=True, slots=True)
class NumericalPoleCheck:
    status: NumericalCheckStatus
    parameter_point: tuple[tuple[str, str], ...]
    poles: tuple[str, ...]
    maximum_real_part: str


__all__ = ["NumericalCheckStatus", "NumericalPoleCheck"]
