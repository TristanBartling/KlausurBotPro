"""Synchronous presenter for the bounded state-space workflow."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from klausurbotpro.application import (
    StateSpaceAnalysisTarget,
    StateSpaceInputDraft,
    preview_matrix_dimensions,
    preview_structured_ode,
    run_state_space_workflow,
)
from klausurbotpro.ui.state_space_view_state import StateSpaceViewState


class StateSpacePresenter(QObject):
    state_changed = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self.state = StateSpaceViewState()

    def calculate(self, draft: StateSpaceInputDraft) -> None:
        result = run_state_space_workflow(draft)
        if not result.succeeded or result.input_model is None:
            self.state = StateSpaceViewState(
                summary="Die Zustandsraumanalyse wurde nicht ausgeführt.",
                diagnostics="\n".join(result.diagnostics),
                failed=True,
                analysis_target=draft.analysis_target,
            )
            self.state_changed.emit(self.state)
            return
        model = result.input_model
        canonical_mode = result.normalized_ode is not None
        normalized = ""
        if result.normalized_ode is not None:
            normalized = (
                f"Normierte DGL: {result.normalized_ode.normalized_ode}\n\n"
                + "Zustandswahl:\n"
                + "\n".join(result.state_definitions)
                + "\n\nZustandsgleichungen:\n"
                + "\n".join(result.state_equations)
            )
        counts = result.half_plane_counts
        count_text = (
            "parameterabhängig"
            if counts is None
            else (
                f"linke Halbebene: {counts[0]}, imaginäre Achse: {counts[1]}, "
                f"rechte Halbebene: {counts[2]}"
            )
        )
        exact_values = ", ".join(
            value.canonical_text + (f" (m={multiplicity})" if multiplicity > 1 else "")
            for value, multiplicity in result.exact_eigenvalues
        )
        exact_line = (
            f"Exakte Eigenwerte: {exact_values}"
            if exact_values
            else (
                "Eigenwerte parameterabhängig; für die Stabilitätsentscheidung wird das "
                "Hurwitz-Kriterium verwendet."
                if counts is None
                else "Keine kompakte exakte Eigenwertdarstellung verfügbar."
            )
        )
        real_parts = "\n".join(
            f"Re({item.eigenvalue_text})"
            f"{' ≈' if item.approximate else ' ='} {item.real_part_text} {item.comparison}"
            for item in result.real_part_checks
        )
        violations = "\n".join(
            f"lambda={item.eigenvalue_text} verletzt das Kriterium Re(lambda) < 0."
            for item in result.real_part_checks
            if item.comparison != "< 0"
        )
        reduced = result.reduced_transfer_function
        raw = result.raw_transfer_function
        diagnostics = "\n".join(result.diagnostics)
        if result.cancellation_report and not result.cancellation_report.startswith("Keine"):
            diagnostics = "\n".join(
                item for item in (diagnostics, result.cancellation_report) if item
            )
        stability_target = result.analysis_target is StateSpaceAnalysisTarget.STATE_STABILITY
        stability_summary = (
            "Charakteristisches Polynom: "
            + (
                result.characteristic_polynomial_text
                if result.characteristic_polynomial
                else ""
            )
            + f"\n{exact_line}\n{result.state_stability}"
        )
        self.state = StateSpaceViewState(
            summary=(
                stability_summary
                if stability_target
                else (
                    f"Zustandsdimension: {model.state_dimension}\n"
                    f"Zustandsstabilität: {result.state_stability}\n"
                    f"G(s) = {reduced.canonical_text if reduced else 'nicht verfügbar'}"
                )
            ),
            normalized_ode=normalized,
            matrices=(
                (
                    f"A_R = {model.matrix_a.canonical_text}\n"
                    f"b_R = {model.vector_b.canonical_text}\n"
                    f"c_R^T = {model.vector_c.canonical_text}\n"
                    f"d = {model.scalar_d.canonical_text}\n\n"
                    "A=A_R, B=b_R, C=c_R^T, D=d"
                )
                if canonical_mode
                else (
                    f"A = {model.matrix_a.canonical_text}\n"
                    f"b = {model.vector_b.canonical_text}\n"
                    f"c^T = {model.vector_c.canonical_text}\n"
                    f"d = {model.scalar_d.canonical_text}"
                )
            ),
            characteristic="\n".join(result.determinant_steps),
            eigenvalues_stability=(
                f"{exact_line}\n"
                "Numerische Eigenwerte: "
                f"{', '.join(result.numerical_eigenvalues) or 'parameterabhängig'}\n"
                f"{count_text}\n\n"
                "Allgemeines Stabilitätskriterium:\n"
                "A asymptotisch stabil genau dann, wenn für alle i gilt: Re(lambda_i) < 0.\n\n"
                f"{real_parts}\n"
                f"{violations}\n"
                f"{result.state_stability}"
            ),
            transfer_function=("" if stability_target else (
                f"Rohe Übertragungsfunktion: {raw.canonical_text if raw else ''}\n"
                f"Reduzierte Übertragungsfunktion: {reduced.canonical_text if reduced else ''}\n"
                + "\n".join(result.transfer_details)
                + "\n"
                f"{result.cancellation_report}"
            )),
            checks="\n".join(
                f"{'BESTANDEN' if item.passed else 'FEHLER'} – {item.name}: {item.explanation}"
                for item in result.visible_checks
            ),
            worked_steps="\n".join(
                f"{index}. {step}" for index, step in enumerate(result.worked_steps, 1)
            ),
            latex_source=result.latex_source,
            diagnostics=diagnostics or "Keine Diagnosen.",
            analysis_target=result.analysis_target,
        )
        self.state_changed.emit(self.state)

    def reset(self) -> None:
        self.state = StateSpaceViewState()
        self.state_changed.emit(self.state)

    @staticmethod
    def ode_preview(draft: StateSpaceInputDraft) -> str:
        return preview_structured_ode(draft)

    @staticmethod
    def matrix_preview(a: str, b: str, c: str) -> str:
        return preview_matrix_dimensions(a, b, c)


__all__ = ["StateSpacePresenter"]
