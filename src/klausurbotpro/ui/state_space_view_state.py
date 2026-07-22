"""Rendered state for the state-space workspace."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StateSpaceViewState:
    summary: str = "Noch keine Zustandsraumanalyse ausgeführt."
    normalized_ode: str = ""
    matrices: str = ""
    characteristic: str = ""
    eigenvalues_stability: str = ""
    transfer_function: str = ""
    checks: str = ""
    worked_steps: str = ""
    latex_source: str = ""
    diagnostics: str = ""
    failed: bool = False


__all__ = ["StateSpaceViewState"]
