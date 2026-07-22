"""Widget-free state for the direct stability workspace."""

from dataclasses import dataclass
from enum import StrEnum


class StabilityUiRunStatus(StrEnum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class StabilityViewState:
    run_status: StabilityUiRunStatus = StabilityUiRunStatus.IDLE
    method: str = "hurwitz"
    summary: str = "Bereit."
    canonical_cases: str = ""
    hurwitz_details: str = ""
    routh_details: str = ""
    parameter_region: str = ""
    short_solution: str = ""
    worked_steps: str = ""
    latex_source: str = ""
    diagnostics: str = ""
    failed: bool = False


__all__ = ["StabilityUiRunStatus", "StabilityViewState"]
