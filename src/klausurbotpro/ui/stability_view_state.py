"""Widget-free state for the direct stability workspace."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StabilityViewState:
    summary: str = "Bereit."
    canonical_cases: str = ""
    hurwitz_details: str = ""
    parameter_region: str = ""
    short_solution: str = ""
    worked_steps: str = ""
    latex_source: str = ""
    diagnostics: str = ""
    failed: bool = False


__all__ = ["StabilityViewState"]
