"""Presenter for direct Hurwitz requests."""

from __future__ import annotations

from typing import Protocol

from PySide6.QtCore import QObject, Signal

from klausurbotpro.application.stability_workflow import (
    StabilityInputDraft,
    run_stability_workflow,
)
from klausurbotpro.ui.stability_view_state import StabilityViewState


class _DisplayExpression(Protocol):
    @property
    def canonical_text(self) -> str: ...


class StabilityPresenter(QObject):
    state_changed = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self.state = StabilityViewState()

    def analyze(self, draft: StabilityInputDraft) -> None:
        result = run_stability_workflow(draft)
        if result.analysis is None:
            self._set_state(
                StabilityViewState(
                    summary="Eingabe ungültig.",
                    diagnostics="\n".join(result.errors),
                    failed=True,
                )
            )
            return
        analysis = result.analysis
        cases = "\n".join(
            f"{item.degree_case.case_id}: Grad {item.degree_case.degree}, "
            f"p={item.degree_case.polynomial.canonical_text}"
            for item in analysis.case_results
        )
        details = "\n\n".join(
            f"Grad {item.degree_case.degree}\nH={_matrix(item.matrix)}\n"
            + ", ".join(
                f"Delta_{value.order}={value.expression.canonical_text}"
                for value in item.determinants
            )
            for item in analysis.case_results
        )
        regions = "\n".join(item.parameter_region.exact_text for item in analysis.case_results)
        checks = "\n".join(
            item.numerical_check.status.value if item.numerical_check is not None else "keine"
            for item in analysis.case_results
        )
        diagnostics = "\n".join((*analysis.diagnostics, analysis.cancellation_notice))
        steps = "\n".join(f"{name}: {value}" for name, value in analysis.worked_steps)
        self._set_state(
            StabilityViewState(
                summary=analysis.statement,
                canonical_cases=cases,
                hurwitz_details=details,
                parameter_region=regions,
                short_solution=f"{analysis.statement}\nNumerische Kontrolle: {checks}",
                worked_steps=steps,
                latex_source=analysis.latex_source,
                diagnostics=diagnostics.strip(),
                failed=False,
            )
        )

    def reset(self) -> None:
        self._set_state(StabilityViewState())

    def _set_state(self, state: StabilityViewState) -> None:
        self.state = state
        self.state_changed.emit(state)


def _matrix(matrix: tuple[tuple[_DisplayExpression, ...], ...]) -> str:
    rows = matrix
    return "[" + "; ".join(", ".join(value.canonical_text for value in row) for row in rows) + "]"


__all__ = ["StabilityPresenter"]
