"""Presenter for direct Laplace/PBZ/time-response requests."""

from PySide6.QtCore import QObject, Signal

from klausurbotpro.application.time_domain_workflow import (
    TimeDomainInputDraft,
    run_time_domain_workflow,
)
from klausurbotpro.ui.time_domain_view_state import TimeDomainViewState


class TimeDomainPresenter(QObject):
    state_changed = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self.state = TimeDomainViewState()

    def calculate(self, draft: TimeDomainInputDraft) -> None:
        result = run_time_domain_workflow(draft)
        presentation = result.presentation
        self._set_state(
            TimeDomainViewState(
                summary=presentation.summary,
                rational_analysis=presentation.rational_analysis,
                partial_fractions=presentation.partial_fractions,
                time_function=presentation.time_function,
                verifications=presentation.verifications,
                short_solution=presentation.short_solution,
                worked_steps=presentation.worked_steps,
                latex_source=presentation.latex_source,
                diagnostics=presentation.diagnostics,
                ode_and_initials=presentation.ode_and_initials,
                laplace_transformation=presentation.laplace_transformation,
                image_equation=presentation.image_equation,
                free_and_forced=presentation.free_and_forced,
                failed=result.solution is None
                or result.solution.status.value in {"FAILED", "UNSUPPORTED"},
            )
        )

    def reset(self) -> None:
        self._set_state(TimeDomainViewState())

    def _set_state(self, state: TimeDomainViewState) -> None:
        self.state = state
        self.state_changed.emit(state)


__all__ = ["TimeDomainPresenter"]
