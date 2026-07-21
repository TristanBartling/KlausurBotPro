"""Method-neutral presenter for direct stability requests."""

from __future__ import annotations

from typing import Protocol

import sympy as sp
from PySide6.QtCore import QObject, Signal

from klausurbotpro.application.stability_workflow import (
    StabilityInputDraft,
    StabilityMethod,
    run_stability_workflow,
)
from klausurbotpro.domain.hurwitz_contracts import HurwitzAnalysisResult
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
                    method=draft.method.value,
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
        hurwitz_details = ""
        routh_details = ""
        if isinstance(analysis, HurwitzAnalysisResult):
            hurwitz_details = "\n\n".join(
                f"Grad {item.degree_case.degree}\nH={_matrix(item.matrix)}\n"
                + ", ".join(
                    f"Delta_{value.order}={value.expression.canonical_text}"
                    for value in item.determinants
                )
                for item in analysis.case_results
            )
            checks = "\n".join(
                _check_status(item.numerical_check.status.value)
                if item.numerical_check is not None
                else "keine"
                for item in analysis.case_results
            )
        else:
            routh_details = "\n\n".join(_routh_case(item) for item in analysis.case_results)
            checks = "\n".join(
                _routh_check(item) for item in analysis.case_results
            )
        regions = "\n".join(item.parameter_region.exact_text for item in analysis.case_results)
        diagnostics = "\n".join((*analysis.diagnostics, analysis.cancellation_notice))
        steps = "\n".join(f"{name}: {value}" for name, value in analysis.worked_steps)
        self._set_state(
            StabilityViewState(
                method=(
                    StabilityMethod.HURWITZ.value
                    if isinstance(analysis, HurwitzAnalysisResult)
                    else StabilityMethod.ROUTH.value
                ),
                summary=analysis.statement,
                canonical_cases=cases,
                hurwitz_details=hurwitz_details,
                routh_details=routh_details,
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


def _routh_case(item: object) -> str:
    from klausurbotpro.domain.routh_contracts import RouthDegreeCaseResult

    assert isinstance(item, RouthDegreeCaseResult)
    if not item.rows:
        return item.statement
    headers = ["Zeile", "1. Spalte (erste Spalte)"] + [
        f"{index}. Spalte" for index in range(2, len(item.rows[0].entries) + 1)
    ]
    rows = [" | ".join(headers)]
    rows.extend(
        " | ".join((row.power_label, *(_routh_expression(value) for value in row.entries)))
        for row in item.rows
    )
    conditions = ", ".join(
        condition.label for condition in item.full_conditions[: len(item.first_column)]
    )
    point = ", ".join(f"{name}={value}" for name, value in item.control_point) or "parameterfrei"
    rows.extend(
        (
            "Erste Spalte: " + ", ".join(_routh_expression(value) for value in item.first_column),
            "Strikte Bedingungen: " + conditions,
            f"Vorzeichenfolge bei {point}: " + ", ".join(item.sign_sequence),
            "Vorzeichenwechsel: "
            + (str(item.sign_changes) if item.sign_changes is not None else "nicht bestimmbar"),
            "RHP-Polzahl: "
            + (
                str(item.rhp_roots_routh)
                if item.rhp_roots_routh is not None
                else "nicht bestimmbar"
            ),
        )
    )
    if item.special_case.value != "none":
        rows.append("Sonderfall: " + item.statement)
    return "\n".join(rows)


def _routh_check(item: object) -> str:
    from klausurbotpro.domain.routh_contracts import RouthDegreeCaseResult

    assert isinstance(item, RouthDegreeCaseResult)
    status = _check_status(item.numerical_check.status.value) if item.numerical_check else "keine"
    return f"{status}; Routh-RHP={item.rhp_roots_routh}; numerisch-RHP={item.numerical_rhp_roots}"


def _routh_expression(value: object) -> str:
    from klausurbotpro.domain.expression import ExactExpression

    assert isinstance(value, ExactExpression)
    numerator, denominator = value._as_sympy().as_numer_denom()
    if denominator != 1:
        return f"({str(sp.expand(numerator)).replace(' ', '')})/{denominator}"
    return value.canonical_text


def _check_status(value: str) -> str:
    return {
        "consistent": "konsistent",
        "inconsistent": "widersprüchlich",
        "numerically_inconclusive": "numerisch nicht entscheidbar",
    }.get(value, value)


__all__ = ["StabilityPresenter"]
