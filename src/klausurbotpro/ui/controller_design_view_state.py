"""Immutable controller-design presentation state."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from klausurbotpro.application import ControllerDesignResult


class ControllerDesignUiRunStatus(StrEnum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class ControllerDesignViewState:
    run_status: ControllerDesignUiRunStatus = ControllerDesignUiRunStatus.IDLE
    result: ControllerDesignResult | None = None
    message: str = ""


__all__ = ["ControllerDesignUiRunStatus", "ControllerDesignViewState"]
