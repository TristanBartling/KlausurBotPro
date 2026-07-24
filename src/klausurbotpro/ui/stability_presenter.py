"""Method-neutral presenter for direct stability requests."""

from __future__ import annotations

from typing import Protocol

from PySide6.QtCore import QObject, Signal, Slot

from klausurbotpro.application import (
    HurwitzAnalysisResult,
    HurwitzConditionStatus,
    HurwitzConditionStep,
    HurwitzDegreeCaseResult,
    RouthDegreeCaseResult,
)
from klausurbotpro.application.stability_workflow import (
    StabilityInputDraft,
    StabilityInputMode,
    StabilityMethod,
    format_stability_expression,
    format_stability_region,
    run_stability_workflow,
)
from klausurbotpro.ui.stability_view_state import StabilityUiRunStatus, StabilityViewState
from klausurbotpro.ui.workflow_worker import WorkflowWorkerFailure


class _DisplayExpression(Protocol):
    @property
    def canonical_text(self) -> str: ...


class StabilityPresenter(QObject):
    execution_requested = Signal(object)
    state_changed = Signal(object)

    def __init__(self, *, asynchronous: bool = False) -> None:
        super().__init__()
        self._asynchronous = asynchronous
        self.state = StabilityViewState()

    def submit(self, draft: StabilityInputDraft) -> bool:
        if self.state.run_status is StabilityUiRunStatus.RUNNING:
            return False
        if (
            not self._asynchronous
            or draft.input_mode is StabilityInputMode.CHARACTERISTIC_POLYNOMIAL
        ):
            self.analyze(draft)
            return True
        self._set_state(
            StabilityViewState(
                run_status=StabilityUiRunStatus.RUNNING,
                method=draft.method.value,
                summary="Berechnung läuft …",
            )
        )
        self.execution_requested.emit(draft)
        return True

    def analyze(self, draft: StabilityInputDraft) -> None:
        self.accept_result(run_stability_workflow(draft), method=draft.method)

    @Slot(object)
    def accept_result(
        self, value: object, *, method: StabilityMethod | None = None
    ) -> None:
        from klausurbotpro.application.stability_workflow import StabilityWorkflowResult

        if type(value) is not StabilityWorkflowResult:
            raise TypeError("value must be a StabilityWorkflowResult.")
        result = value
        if result.analysis is None:
            self._set_state(
                StabilityViewState(
                    run_status=StabilityUiRunStatus.FAILED,
                    method=(method.value if method is not None else self.state.method),
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
        parameters = analysis.canonical_polynomial.input.decision_parameters
        if isinstance(analysis, HurwitzAnalysisResult):
            hurwitz_details = "\n\n".join(
                _hurwitz_case(
                    item,
                    analysis.canonical_polynomial.input.variable,
                    parameters,
                )
                for item in analysis.case_results
            )
            checks = "\n".join(
                _check_status(item.numerical_check.status.value)
                if item.numerical_check is not None
                else "keine"
                for item in analysis.case_results
            )
            regions = "\n\nund\n\n".join(
                _hurwitz_region(item, parameters) for item in analysis.case_results
            )
            short_solution = "\n\n".join(
                _hurwitz_short(item, parameters) for item in analysis.case_results
            )
        else:
            routh_details = "\n\n".join(_routh_case(item) for item in analysis.case_results)
            checks = "\n".join(
                _routh_check(item) for item in analysis.case_results
            )
            regions = "\n\nund\n\n".join(
                format_stability_region(item.parameter_region, parameters)
                for item in analysis.case_results
            )
            short_solution = f"{analysis.statement}\nNumerische Kontrolle: {checks}"
        diagnostics = "\n".join((*analysis.diagnostics, analysis.cancellation_notice))
        projected_steps = (
            result.source_steps
            if isinstance(analysis, HurwitzAnalysisResult) and result.source_steps
            else (*result.source_steps, *analysis.worked_steps)
        )
        steps = "\n".join(
            f"{name}: {item_value}" for name, item_value in projected_steps
        )
        self._set_state(
            StabilityViewState(
                run_status=StabilityUiRunStatus.COMPLETE,
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
                short_solution=short_solution,
                worked_steps=steps,
                latex_source=result.latex_preamble or analysis.latex_source,
                diagnostics=diagnostics.strip(),
                failed=False,
            )
        )

    @Slot(object)
    def accept_failure(self, value: object) -> None:
        if type(value) is not WorkflowWorkerFailure:
            raise TypeError("value must be WorkflowWorkerFailure.")
        self._set_state(
            StabilityViewState(
                run_status=StabilityUiRunStatus.FAILED,
                method=self.state.method,
                summary="Berechnung fehlgeschlagen.",
                diagnostics=value.message,
                failed=True,
            )
        )

    def reset(self) -> None:
        if self.state.run_status is StabilityUiRunStatus.RUNNING:
            return
        self._set_state(StabilityViewState())

    def _set_state(self, state: StabilityViewState) -> None:
        self.state = state
        self.state_changed.emit(state)


def _matrix(matrix: tuple[tuple[_DisplayExpression, ...], ...]) -> str:
    rows = matrix
    return "[" + "; ".join(", ".join(value.canonical_text for value in row) for row in rows) + "]"


def _hurwitz_case(
    item: HurwitzDegreeCaseResult,
    variable: str,
    parameters: tuple[str, ...],
) -> str:
    coefficients = "\n".join(
        f"a_{power} = {coefficient.canonical_text}"
        for power, coefficient in zip(
            range(item.degree_case.degree, -1, -1),
            item.degree_case.coefficients,
            strict=True,
        )
    )
    necessary = "\n".join(
        _condition_plain(condition) for condition in item.necessary_condition_steps
    )
    reduced_necessary = _reduced_plain(item.necessary_condition_steps)
    sufficient = "\n".join(
        _condition_plain(condition) for condition in item.sufficient_condition_steps
    )
    reduced_sufficient = _reduced_plain(item.sufficient_condition_steps)
    region = format_stability_region(item.parameter_region, parameters)
    return "\n".join(
        (
            "Charakteristisches Polynom",
            f"N({variable}) = {item.degree_case.polynomial.canonical_text}",
            "",
            "Koeffizienten",
            coefficients,
            "",
            "Notwendige Bedingungen",
            necessary,
            "",
            "Reduzierte notwendige Bedingungen",
            reduced_necessary,
            "",
            "Hurwitz-Matrix",
            f"H = {_matrix(item.matrix)}",
            "",
            "Hinreichende Bedingungen",
            sufficient,
            "",
            "Reduzierte hinreichende Bedingungen",
            reduced_sufficient,
            "",
            "Schnittmenge",
            region,
            "",
            "Exaktes Stabilitätsgebiet",
            region,
        )
    )


def _condition_plain(item: HurwitzConditionStep) -> str:
    line = f"{item.label} = {item.expression.canonical_text} > 0"
    if item.solved_text and item.solved_text not in ("wahr", "falsch"):
        line += f"  ⇔  {item.solved_text}"
    status = {
        HurwitzConditionStatus.ACTIVE: "aktiv",
        HurwitzConditionStatus.ALREADY_SATISFIED: "bereits erfüllt",
        HurwitzConditionStatus.REDUNDANT_EQUIVALENT: "äquivalent abgedeckt",
        HurwitzConditionStatus.REDUNDANT_WEAKER: "schwächer und redundant",
        HurwitzConditionStatus.CONTRADICTORY: "widersprüchlich",
        HurwitzConditionStatus.UNRESOLVED_SAFE: "sicher ungelöst; bleibt aktiv",
    }[item.status]
    return f"{line}  —  {status}" + (f"\n  {item.reason}" if item.reason else "")


def _reduced_plain(steps: tuple[HurwitzConditionStep, ...]) -> str:
    active = tuple(
        item.solved_text or f"{item.expression.canonical_text} > 0"
        for item in steps
        if item.status
        in (HurwitzConditionStatus.ACTIVE, HurwitzConditionStatus.UNRESOLVED_SAFE)
    )
    return "\n".join(active) or "Keine zusätzliche aktive Bedingung."


def _hurwitz_region(
    item: HurwitzDegreeCaseResult,
    parameters: tuple[str, ...],
) -> str:
    minimal = "\n".join(
        condition.solved_text or f"{condition.expression.canonical_text} > 0"
        for condition in item.minimal_condition_steps
    ) or "Keine zusätzliche aktive Bedingung."
    region = format_stability_region(item.parameter_region, parameters)
    return "\n".join(
        (
            "Aktives minimales Bedingungssystem",
            minimal,
            "",
            "Schnittmenge",
            region,
            "",
            "Exaktes Stabilitätsgebiet",
            region,
            "",
            "Offene Grenzen",
            "Alle Gleichheitsränder der asymptotischen Stabilität sind ausgeschlossen.",
        )
    )


def _hurwitz_short(
    item: HurwitzDegreeCaseResult,
    parameters: tuple[str, ...],
) -> str:
    necessary = _reduced_plain(item.necessary_condition_steps)
    sufficient = _reduced_plain(item.sufficient_condition_steps)
    region = format_stability_region(item.parameter_region, parameters)
    check = (
        _check_status(item.numerical_check.status.value)
        if item.numerical_check is not None
        else "nicht verfügbar"
    )
    return "\n".join(
        (
            "Notwendige Bedingungen",
            necessary,
            "",
            "Hinreichende Zusatzbedingungen",
            sufficient,
            "",
            "Exaktes Stabilitätsgebiet",
            region,
            "",
            f"Numerische Kontrolle (nachrangig): {check}",
        )
    )


def _routh_case(item: object) -> str:
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
    assert isinstance(item, RouthDegreeCaseResult)
    changes = str(item.sign_changes) if item.sign_changes is not None else "nicht bestimmbar"
    routh_count = (
        str(item.rhp_roots_routh)
        if item.rhp_roots_routh is not None
        else "nicht bestimmbar"
    )
    numeric_count = (
        str(item.numerical_rhp_roots)
        if item.numerical_rhp_roots is not None
        else "nicht bestimmt"
    )
    numerical = (
        "Numerische Kontrolle: " + _check_status(item.numerical_check.status.value)
        if item.numerical_check is not None
        else "Keine numerische Kontrolle verfügbar"
    )
    return (
        f"Vorzeichenwechsel: {changes}; Routh-RHP-Polzahl: {routh_count}; "
        f"Numerische RHP-Polzahl: {numeric_count}; {numerical}"
    )


def _routh_expression(value: object) -> str:
    return format_stability_expression(value)


def _check_status(value: str) -> str:
    return {
        "consistent": "konsistent",
        "inconsistent": "widersprüchlich",
        "numerically_inconclusive": "numerisch nicht entscheidbar",
    }.get(value, value)


__all__ = ["StabilityPresenter"]
