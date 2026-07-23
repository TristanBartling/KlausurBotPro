"""Widget-free view state for the time-domain workspace."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TimeDomainViewState:
    summary: str = "Bereit."
    rational_analysis: str = ""
    partial_fractions: str = ""
    time_function: str = ""
    verifications: str = ""
    short_solution: str = ""
    worked_steps: str = ""
    latex_source: str = ""
    diagnostics: str = ""
    ode_and_initials: str = ""
    laplace_transformation: str = ""
    image_equation: str = ""
    free_and_forced: str = ""
    visible_result_tabs: tuple[str, ...] = ()
    failed: bool = False


__all__ = ["TimeDomainViewState"]
