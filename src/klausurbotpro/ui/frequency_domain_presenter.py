"""Presenter for the small frequency-domain GUI workflow."""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from typing import Any

from PySide6.QtCore import QObject, Signal, Slot

from klausurbotpro.application import (
    FrequencyDomainInputDraft,
    FrequencyDomainRequestFactory,
    FrequencyDomainSingularityRefinementPlanner,
    FrequencyDomainSingularityRefinementReason,
    FrequencyDomainWorkflowLimits,
    FrequencyDomainWorkflowResult,
    FrequencyDomainWorkflowStatus,
    render_frequency_domain_solution_latex,
)
from klausurbotpro.ui.frequency_domain_view_state import (
    FrequencyDomainDiagnosticView,
    FrequencyDomainSinglePointView,
    FrequencyDomainSummaryView,
    FrequencyDomainTableRow,
    FrequencyDomainUiRunStatus,
    FrequencyDomainViewState,
    FrequencyPointDetailView,
    PlotMarkerView,
    PlotSegmentView,
    PlotView,
    WorkedStepsView,
)
from klausurbotpro.ui.workflow_worker import WorkflowWorkerFailure

_MODE_LABELS = {
    "single_point": "Einzelpunkt",
    "bode": "Bode",
}
_POINT_STATUS_LABELS = {
    "defined": "Definiert",
    "zero_response": "Nullantwort",
    "singular": "Singularität",
    "symbolic_undetermined": "Symbolisch unbestimmt",
    "numeric_undetermined": "Numerisch unbestimmt",
}
_STATUS_LABELS = {
    "complete": "Vollständig",
    "partial": "Teilresultat",
    "failed": "Fehlgeschlagen",
    "no_plottable_data": "Keine darstellbaren Daten",
    "symbolic_undetermined": "Symbolisch unbestimmt",
    "no_phase_data": "Keine Phasendaten",
}


class FrequencyDomainPresenter(QObject):
    """Create one request and project validated results into display strings."""

    execution_requested = Signal(object)
    state_changed = Signal(object)

    def __init__(self, request_factory: FrequencyDomainRequestFactory) -> None:
        super().__init__()
        if type(request_factory) is not FrequencyDomainRequestFactory:
            raise TypeError("request_factory has an invalid type.")
        self._request_factory = request_factory
        self._limits: FrequencyDomainWorkflowLimits = request_factory.limits
        self._refinement_planner = (
            FrequencyDomainSingularityRefinementPlanner()
        )
        self._refinement_attempted = False
        self._base_result: FrequencyDomainWorkflowResult | None = None
        self._added_frequencies: tuple[Any, ...] = ()
        self._displayed_result: FrequencyDomainWorkflowResult | None = None
        self._displayed_added_frequencies: tuple[Any, ...] = ()
        self._state = FrequencyDomainViewState()

    @property
    def state(self) -> FrequencyDomainViewState:
        return self._state

    def submit(self, draft: FrequencyDomainInputDraft) -> bool:
        if type(draft) is not FrequencyDomainInputDraft:
            raise TypeError("draft must be FrequencyDomainInputDraft.")
        if self._state.run_status is FrequencyDomainUiRunStatus.RUNNING:
            return False
        self._reset_refinement()
        creation = self._request_factory.create(draft)
        if not creation.succeeded:
            self._set_state(
                FrequencyDomainViewState(
                    run_status=FrequencyDomainUiRunStatus.FAILED,
                    request_errors=creation.errors,
                    focused_field=creation.errors[0].field,
                    general_message="Eingabe ungültig.",
                )
            )
            return False
        assert creation.request is not None
        self._set_state(
            FrequencyDomainViewState(
                run_status=FrequencyDomainUiRunStatus.RUNNING,
                general_message="Frequenzberechnung läuft …",
            )
        )
        self.execution_requested.emit(creation.request)
        return True

    @Slot(object)
    def accept_result(self, value: object) -> None:
        if type(value) is not FrequencyDomainWorkflowResult:
            raise TypeError("value must be FrequencyDomainWorkflowResult.")
        if not self._refinement_attempted:
            plan = self._refinement_planner.plan(value, self._limits)
            self._refinement_attempted = True
            if plan.refined_request is not None:
                self._base_result = value
                self._added_frequencies = plan.added_frequencies
                self._set_state(
                    FrequencyDomainViewState(
                        run_status=FrequencyDomainUiRunStatus.RUNNING,
                        general_message=(
                            "Singularitätsumgebung wird automatisch "
                            "verfeinert …"
                        ),
                    )
                )
                self.execution_requested.emit(plan.refined_request)
                return
            notice = (
                ""
                if plan.reason
                in (
                    FrequencyDomainSingularityRefinementReason.NOT_APPLICABLE,
                    FrequencyDomainSingularityRefinementReason.NO_SINGULARITY,
                )
                else f"{plan.message} Das Basisergebnis wird angezeigt."
            )
            self._finish_result(value, notice=notice)
            return
        if self._base_result is not None and (
            value.status is not FrequencyDomainWorkflowStatus.COMPLETE
            or value.bode_data_result is None
        ):
            base = self._base_result
            self._base_result = None
            self._added_frequencies = ()
            self._finish_result(
                base,
                notice=(
                    "Die optionale Singularitätsverfeinerung konnte nicht "
                    "abgeschlossen werden. Das Basisergebnis wird angezeigt."
                ),
            )
            return
        self._base_result = None
        self._finish_result(
            value,
            added_frequencies=self._added_frequencies,
        )

    def _finish_result(
        self,
        value: FrequencyDomainWorkflowResult,
        *,
        added_frequencies: tuple[Any, ...] = (),
        notice: str = "",
    ) -> None:
        status = {
            FrequencyDomainWorkflowStatus.COMPLETE: (
                FrequencyDomainUiRunStatus.COMPLETE
            ),
            FrequencyDomainWorkflowStatus.PARTIAL: (
                FrequencyDomainUiRunStatus.PARTIAL
            ),
            FrequencyDomainWorkflowStatus.FAILED: (
                FrequencyDomainUiRunStatus.FAILED
            ),
        }[value.status]
        added_text = _added_frequencies_text(added_frequencies)
        message = {
            FrequencyDomainUiRunStatus.COMPLETE: (
                "Frequenzberechnung vollständig abgeschlossen."
            ),
            FrequencyDomainUiRunStatus.PARTIAL: (
                "Frequenzberechnung mit Teilresultat abgeschlossen."
            ),
            FrequencyDomainUiRunStatus.FAILED: (
                "Frequenzberechnung fehlgeschlagen."
            ),
        }[status]
        if added_text:
            message = f"{message} Automatisch ergänzte Frequenzen: {added_text}."
        elif notice:
            message = f"{message} {notice}"
        self._displayed_result = value
        self._displayed_added_frequencies = added_frequencies
        latex_report = render_frequency_domain_solution_latex(
            value,
            self._limits,
            added_frequencies=added_frequencies,
        )
        self._set_state(
            FrequencyDomainViewState(
                run_status=status,
                summary=_summary(value, added_text),
                single_point=_single_point(value),
                rows=_rows(value),
                plot=_plot(value),
                worked_steps=_worked_steps(value),
                latex_report=latex_report,
                diagnostics=tuple(
                    FrequencyDomainDiagnosticView(
                        diagnostic.severity.value,
                        diagnostic.message,
                        "" if diagnostic.field is None else diagnostic.field,
                    )
                    for diagnostic in value.diagnostics
                ),
                focused_field=_diagnostic_focus(value),
                general_message=message,
            )
        )

    @Slot(object)
    def accept_failure(self, value: object) -> None:
        if type(value) is not WorkflowWorkerFailure:
            raise TypeError("value must be WorkflowWorkerFailure.")
        if self._base_result is not None:
            base = self._base_result
            self._base_result = None
            self._added_frequencies = ()
            self._finish_result(
                base,
                notice=(
                    "Die optionale Singularitätsverfeinerung ist unerwartet "
                    "fehlgeschlagen. Das Basisergebnis wird angezeigt."
                ),
            )
            return
        self._set_state(
            FrequencyDomainViewState(
                run_status=FrequencyDomainUiRunStatus.FAILED,
                general_message=value.message,
            )
        )

    def reset(self) -> bool:
        if self._state.run_status is FrequencyDomainUiRunStatus.RUNNING:
            return False
        self._reset_refinement()
        self._set_state(FrequencyDomainViewState())
        return True

    def _reset_refinement(self) -> None:
        self._refinement_attempted = False
        self._base_result = None
        self._added_frequencies = ()
        self._displayed_result = None
        self._displayed_added_frequencies = ()

    def select_bode_row(self, index: int) -> None:
        """Synchronize the selected Bode point with the LaTeX solution."""

        if type(index) is not int or index < 0:
            raise ValueError("index must be a nonnegative int.")
        if self._displayed_result is None or not self._state.rows:
            return
        if index >= len(self._state.rows):
            raise ValueError("index exceeds the available Bode rows.")
        if index == self._state.selected_bode_index:
            return
        latex_report = render_frequency_domain_solution_latex(
            self._displayed_result,
            self._limits,
            selected_bode_index=index,
            added_frequencies=self._displayed_added_frequencies,
        )
        self._set_state(
            replace(
                self._state,
                latex_report=latex_report,
                selected_bode_index=index,
            )
        )

    def set_general_message(self, message: str) -> None:
        if type(message) is not str or not message:
            raise ValueError("message must be a non-empty string.")
        self._set_state(
            FrequencyDomainViewState(
                run_status=self._state.run_status,
                summary=self._state.summary,
                single_point=self._state.single_point,
                rows=self._state.rows,
                plot=self._state.plot,
                worked_steps=self._state.worked_steps,
                latex_report=self._state.latex_report,
                selected_bode_index=self._state.selected_bode_index,
                diagnostics=self._state.diagnostics,
                request_errors=self._state.request_errors,
                focused_field=self._state.focused_field,
                general_message=message,
            )
        )

    def _set_state(self, state: FrequencyDomainViewState) -> None:
        self._state = state
        self.state_changed.emit(state)


def _summary(
    result: FrequencyDomainWorkflowResult,
    added_frequencies: str = "",
) -> FrequencyDomainSummaryView:
    if result.request is None:
        return FrequencyDomainSummaryView(
            workflow_status=_status_text(result.status.value)
        )
    response = result.active_frequency_response_result
    frequency_count = 0 if response is None else len(response.points)
    bode = result.bode_data_result
    single = result.single_point_result
    domain_status = (
        _status_text(bode.status.value)
        if bode is not None
        else (
            ""
            if single is None or not single.points
            else _POINT_STATUS_LABELS[single.points[0].status.value]
        )
    )
    return FrequencyDomainSummaryView(
        workflow_status=_status_text(result.status.value),
        mode=_MODE_LABELS[result.request.mode.value],
        reduced_transfer_function=_reduced_text(result),
        substitutions=_substitutions_text(result),
        frequency_count=str(frequency_count),
        domain_status=domain_status,
        magnitude_segment_count=(
            "" if bode is None else str(len(bode.magnitude_segments))
        ),
        phase_segment_count=(
            "" if bode is None else str(len(bode.phase_segments))
        ),
        phase_unwrap=(
            "aktiv" if result.phase_unwrap_result is not None else "nicht aktiv"
        ),
        added_frequencies=added_frequencies,
    )


def _single_point(
    result: FrequencyDomainWorkflowResult,
) -> FrequencyDomainSinglePointView:
    response = result.single_point_result
    if response is None or not response.points:
        return FrequencyDomainSinglePointView()
    point = response.points[0]
    zero = point.status.value == "zero_response"
    return FrequencyDomainSinglePointView(
        omega=_rational_text(point.omega),
        status=_POINT_STATUS_LABELS[point.status.value],
        complex_value=_expression_text(point.exact_complex_value),
        real_part=_summary_number(
            point.exact_real_part,
            point.numerical_real,
        ),
        imaginary_part=_summary_number(
            point.exact_imaginary_part,
            point.numerical_imaginary,
        ),
        magnitude=_short_number(_optional(point.numerical_magnitude)),
        decibel=_short_decibel(point.numerical_decibel),
        principal_phase=(
            "nicht definiert"
            if zero
            else _short_number(_optional(point.numerical_phase_degrees))
        ),
    )


def _rows(
    result: FrequencyDomainWorkflowResult,
) -> tuple[FrequencyDomainTableRow, ...]:
    bode = result.bode_data_result
    if bode is None:
        return ()
    unwrapped = (
        {}
        if result.phase_unwrap_result is None
        else {
            point.grid_index: point.unwrapped_phase_degrees
            for segment in result.phase_unwrap_result.segments
            for point in segment.points
        }
    )
    rows: list[FrequencyDomainTableRow] = []
    for index, point in enumerate(bode.points):
        full_values = (
            str(index + 1),
            point.target_decimal.decimal_text,
            _rational_text(point.evaluation_frequency),
            _POINT_STATUS_LABELS[
                point.frequency_response_point.status.value
            ],
            _optional(point.frequency_response_point.numerical_real),
            _optional(point.frequency_response_point.numerical_imaginary),
            _optional(point.frequency_response_point.numerical_magnitude),
            _decibel_text(point.numerical_decibel),
            _optional(point.principal_phase_degrees),
            unwrapped.get(index, ""),
        )
        displayed = (
            full_values[0],
            _short_number(full_values[1]),
            _short_rational(point.evaluation_frequency),
            full_values[3],
            _short_number(full_values[4]),
            _short_number(full_values[5]),
            _short_number(full_values[6]),
            _short_number(full_values[7]),
            _short_number(full_values[8]),
            _short_number(full_values[9]),
        )
        rows.append(FrequencyDomainTableRow(*displayed, full_values))
    return tuple(rows)


def _plot(result: FrequencyDomainWorkflowResult) -> PlotView:
    request = result.request
    if request is None or request.mode.value != "bode":
        return PlotView()
    bode = result.bode_data_result
    if bode is None:
        return PlotView(
            visible=True,
            no_data_message="Für diesen Bode-Lauf liegen keine Diagrammdaten vor.",
        )
    magnitude_segments = tuple(
        PlotSegmentView(
            tuple(point.target_decimal.decimal_text for point in segment.points),
            tuple(
                point.numerical_decibel.decimal_value or ""
                for point in segment.points
                if point.numerical_decibel is not None
            ),
        )
        for segment in bode.magnitude_segments
    )
    principal_segments = tuple(
        PlotSegmentView(
            tuple(point.target_decimal.decimal_text for point in segment.points),
            tuple(point.principal_phase_degrees or "" for point in segment.points),
        )
        for segment in bode.phase_segments
    )
    unwrap = result.phase_unwrap_result
    unwrapped_segments = (
        ()
        if unwrap is None
        else tuple(
            PlotSegmentView(
                tuple(
                    point.source_point.target_decimal.decimal_text
                    for point in segment.points
                ),
                tuple(
                    point.unwrapped_phase_degrees for point in segment.points
                ),
            )
            for segment in unwrap.segments
        )
    )
    no_data_message = (
        ""
        if magnitude_segments or principal_segments
        else "Keine darstellbaren Bode-Daten vorhanden."
    )
    markers = tuple(
        PlotMarkerView(
            point.target_decimal.decimal_text,
            (
                "Singularität"
                if point.frequency_response_point.status.value == "singular"
                else "nicht darstellbar"
            ),
        )
        for point in bode.points
        if point.frequency_response_point.status.value
        not in ("defined", "zero_response")
    )
    return PlotView(
        visible=True,
        magnitude_segments=magnitude_segments,
        principal_phase_segments=principal_segments,
        unwrapped_phase_segments=unwrapped_segments,
        interruption_markers=markers,
        no_data_message=no_data_message,
    )


def _worked_steps(result: FrequencyDomainWorkflowResult) -> WorkedStepsView:
    if result.request is None:
        return WorkedStepsView()
    general_lines = (
        ("Übertragungsfunktion (Eingabe)", _input_expression_text(result)),
        ("Reduzierte Übertragungsfunktion", _reduced_text(result)),
        ("Ansatz", "s = jω"),
        ("Parameterbelegungen", _substitutions_text(result)),
        ("Frequenzdefinition", _frequency_definition_text(result)),
    )
    response = result.active_frequency_response_result
    if response is None:
        return WorkedStepsView(general_lines=general_lines)

    bode = result.bode_data_result
    unwrapped_by_grid: dict[int, Any] = {}
    magnitude_segments: dict[int, int] = {}
    phase_segments: dict[int, int] = {}
    if bode is not None:
        for magnitude_segment in bode.magnitude_segments:
            for grid_index in range(
                magnitude_segment.start_grid_index,
                magnitude_segment.end_grid_index + 1,
            ):
                magnitude_segments[grid_index] = (
                    magnitude_segment.segment_index + 1
                )
        for phase_segment in bode.phase_segments:
            for grid_index in range(
                phase_segment.start_grid_index,
                phase_segment.end_grid_index + 1,
            ):
                phase_segments[grid_index] = phase_segment.segment_index + 1
    if result.phase_unwrap_result is not None:
        unwrapped_by_grid = {
            point.grid_index: point
            for segment in result.phase_unwrap_result.segments
            for point in segment.points
        }

    details: list[FrequencyPointDetailView] = []
    short_solutions: list[str] = []
    for index, point in enumerate(response.points):
        target = ""
        if bode is not None:
            target = bode.points[index].target_decimal.decimal_text
        lines: list[tuple[str, str]] = [
            ("ω", f"{_rational_text(point.omega)} rad/s"),
            (
                "Spezialisierter Zähler",
                point.specialized_numerator.canonical_text,
            ),
            (
                "Spezialisierter Nenner",
                point.specialized_denominator.canonical_text,
            ),
            ("G(jω)", _expression_text(point.exact_complex_value)),
            ("Realteil (exakt)", _expression_text(point.exact_real_part)),
            ("Realteil (numerisch)", _optional(point.numerical_real)),
            (
                "Imaginärteil (exakt)",
                _expression_text(point.exact_imaginary_part),
            ),
            (
                "Imaginärteil (numerisch)",
                _optional(point.numerical_imaginary),
            ),
            (
                "Betragsquadrat",
                _expression_text(point.exact_magnitude_squared),
            ),
            ("Betrag", _optional(point.numerical_magnitude)),
            (
                "L(ω) = 20 log10(|G(jω)|)",
                _decibel_text(point.numerical_decibel),
            ),
            (
                "Hauptphase",
                _degree_text(point.numerical_phase_degrees),
            ),
            ("Punktstatus", _POINT_STATUS_LABELS[point.status.value]),
            (
                "Diagnosen",
                "keine"
                if not point.diagnostics
                else " | ".join(item.message for item in point.diagnostics),
            ),
        ]
        if bode is not None:
            lines[0:0] = [
                ("Ziel-ω", f"{target} rad/s"),
                (
                    "Auswertungs-ω",
                    f"{_rational_text(point.omega)} rad/s",
                ),
            ]
            unwrap_point = unwrapped_by_grid.get(index)
            lines.extend(
                (
                    (
                        "Entfaltete Phase",
                        ""
                        if unwrap_point is None
                        else _degree_text(
                            unwrap_point.unwrapped_phase_degrees
                        ),
                    ),
                    (
                        "360°-Offset",
                        ""
                        if unwrap_point is None
                        else f"{unwrap_point.phase_offset_turns} × 360°",
                    ),
                    (
                        "Plotsegment",
                        _segment_text(
                            magnitude_segments.get(index),
                            phase_segments.get(index),
                        ),
                    ),
                )
            )
        details.append(
            FrequencyPointDetailView(
                (
                    "Einzelpunkt"
                    if bode is None
                    else f"Bode-Tabellenzeile {index + 1}"
                ),
                tuple(lines),
            )
        )
        short_solutions.append(
            _single_point_short_solution(result, point)
            if bode is None
            else _bode_point_short_solution(
                result,
                bode.points[index],
                unwrapped_by_grid.get(index),
            )
        )
    return WorkedStepsView(
        general_lines,
        tuple(details),
        tuple(short_solutions),
    )


def _single_point_short_solution(
    result: FrequencyDomainWorkflowResult,
    point: Any,
) -> str:
    omega = _short_rational(point.omega)
    argument = "j" if omega == "1" else f"j·{omega}"
    complex_value = _short_exact(point.exact_complex_value)
    real_part = _short_exact(point.exact_real_part, point.numerical_real)
    imaginary_part = _short_exact(
        point.exact_imaginary_part,
        point.numerical_imaginary,
    )
    magnitude_squared = _short_exact(point.exact_magnitude_squared)
    magnitude = _short_number(_optional(point.numerical_magnitude))
    decibel = _short_decibel(point.numerical_decibel)
    phase = _short_phase(point.numerical_phase_degrees)
    diagnostics = (
        "keine"
        if not point.diagnostics
        else " | ".join(item.message for item in point.diagnostics)
    )
    numerator = _short_exact(point.specialized_numerator)
    denominator = _short_exact(point.specialized_denominator)
    lines = [
        "Gegeben:",
        f"G(s) = {_input_expression_text(result)}",
        f"ω = {omega} rad/s",
        "",
        "1. Einsetzen von s = jω",
        f"G({argument}) = ({numerator}) / ({denominator})",
        "",
        "2. Komplexer Wert",
        f"G({argument}) = {_available(complex_value)}",
        f"Re{{G({argument})}} = {_available(real_part)}",
        f"Im{{G({argument})}} = {_available(imaginary_part)}",
        "",
        "3. Betrag",
        f"|G({argument})|² = {_available(magnitude_squared)}",
        (
            f"|G({argument})| ≈ {magnitude}"
            if magnitude
            else f"|G({argument})|: nicht verfügbar"
        ),
        "",
        "4. Dezibelwert",
        f"L({omega}) = 20 log10(|G({argument})|)",
        (
            f"L({omega}) = {decibel} dB"
            if decibel == "−∞"
            else (
                f"L({omega}) ≈ {decibel} dB"
                if decibel
                else f"L({omega}): nicht verfügbar"
            )
        ),
        "",
        "5. Phase",
        (
            f"φ({omega}) = {phase}"
            if phase
            else f"φ({omega}): nicht definiert"
        ),
        "",
        f"Status: {_POINT_STATUS_LABELS[point.status.value]}",
        f"Diagnosen: {diagnostics}",
    ]
    return "\n".join(lines)


def _bode_point_short_solution(
    result: FrequencyDomainWorkflowResult,
    bode_point: Any,
    unwrap_point: Any | None,
) -> str:
    point = bode_point.frequency_response_point
    target = _short_number(bode_point.target_decimal.decimal_text)
    evaluation = _short_rational(bode_point.evaluation_frequency)
    complex_value = _short_exact(point.exact_complex_value)
    real_part = _short_exact(point.exact_real_part, point.numerical_real)
    imaginary_part = _short_exact(
        point.exact_imaginary_part,
        point.numerical_imaginary,
    )
    magnitude = _short_number(_optional(point.numerical_magnitude))
    decibel = _short_decibel(point.numerical_decibel)
    phase = _short_phase(point.numerical_phase_degrees)
    lines = [
        "Gegeben:",
        f"G(s) = {_reduced_text(result)}",
        f"Raster: {_short_frequency_definition_text(result)}",
        f"Ziel-ω = {target} rad/s",
    ]
    relative_error = bode_point.grid_point.maximum_relative_error
    if relative_error.numerator != 0:
        lines.append(f"Auswertungs-ω = {evaluation} rad/s")
    lines.extend(
        (
            "",
            "Auswertung:",
            f"1. s = j·{evaluation}",
            f"2. G(jω) = {_available(complex_value)}",
            (
                "3. "
                f"Re{{G(jω)}} = {_available(real_part)}; "
                f"Im{{G(jω)}} = {_available(imaginary_part)}"
            ),
            (
                f"4. |G(jω)| ≈ {magnitude}"
                if magnitude
                else "4. |G(jω)|: nicht verfügbar"
            ),
            (
                f"5. L(ω) = {decibel} dB"
                if decibel == "−∞"
                else (
                    f"5. L(ω) ≈ {decibel} dB"
                    if decibel
                    else "5. L(ω): nicht verfügbar"
                )
            ),
            (
                f"6. Hauptphase: {phase}"
                if phase
                else "6. Hauptphase: nicht definiert"
            ),
        )
    )
    if unwrap_point is not None:
        lines.append(
            "7. Entfaltete Phase: "
            f"{_short_phase(unwrap_point.unwrapped_phase_degrees)}"
        )
    lines.append(
        f"{8 if unwrap_point is not None else 7}. "
        f"Punktstatus: {_POINT_STATUS_LABELS[point.status.value]}"
    )
    interruption = _interruption_text(point.status.value, target)
    if interruption:
        lines.append(
            f"{9 if unwrap_point is not None else 8}. {interruption}"
        )
    diagnostics = (
        "keine"
        if not point.diagnostics
        else " | ".join(item.message for item in point.diagnostics)
    )
    lines.append(f"Diagnosen: {diagnostics}")
    return "\n".join(lines)


def _short_exact(value: Any | None, numerical: str | None = None) -> str:
    text = _expression_text(value)
    if not text:
        return ""
    if len(text) <= 24:
        return text
    if numerical is not None:
        return f"≈ {_short_number(numerical)}"
    return "siehe technische Details"


def _summary_number(value: Any | None, numerical: str | None) -> str:
    exact = _expression_text(value)
    if exact and len(exact) <= 12:
        return exact
    return _short_number(_optional(numerical))


def _short_decibel(value: Any | None) -> str:
    full = _decibel_text(value)
    return full if full == "−∞" else _short_number(full)


def _short_phase(value: str | None) -> str:
    short = _short_number(_optional(value))
    return "" if not short else f"{short}°"


def _available(value: str) -> str:
    return value if value else "nicht verfügbar"


def _interruption_text(status: str, target: str) -> str:
    if status == "singular":
        return f"Unterbrechung: Singularität bei ω = {target} rad/s"
    if status not in ("defined", "zero_response"):
        return f"Unterbrechung bei ω = {target} rad/s: nicht darstellbar"
    if status == "zero_response":
        return "Unterbrechung: Nullantwort wird nicht als Plotpunkt erfunden"
    return ""


def _short_frequency_definition_text(
    result: FrequencyDomainWorkflowResult,
) -> str:
    assert result.request is not None
    grid = result.request.grid_request
    if grid is None:
        return ""
    explicit = (
        "keine"
        if not grid.explicit_frequencies
        else ", ".join(
            _short_rational(value) for value in grid.explicit_frequencies
        )
    )
    return (
        f"ω_min={_short_rational(grid.omega_min)} rad/s; "
        f"ω_max={_short_rational(grid.omega_max)} rad/s; "
        f"{grid.points_per_decade} Punkte/Dekade; "
        f"explizit: {explicit}"
    )


def _input_expression_text(result: FrequencyDomainWorkflowResult) -> str:
    assert result.request is not None
    preparation = result.request.preparation_request
    if preparation.input_form.value == "common":
        return preparation.common_expression_text or ""
    return (
        f"({preparation.numerator_expression_text}) / "
        f"({preparation.denominator_expression_text})"
    )


def _frequency_definition_text(result: FrequencyDomainWorkflowResult) -> str:
    assert result.request is not None
    request = result.request
    if request.single_angular_frequency is not None:
        return f"ω = {_rational_text(request.single_angular_frequency)} rad/s"
    grid = request.grid_request
    if grid is None:
        return ""
    explicit = (
        "keine"
        if not grid.explicit_frequencies
        else ", ".join(
            _rational_text(value) for value in grid.explicit_frequencies
        )
    )
    return (
        f"ω_min={_rational_text(grid.omega_min)} rad/s; "
        f"ω_max={_rational_text(grid.omega_max)} rad/s; "
        f"{grid.points_per_decade} Punkte pro Dekade; "
        f"explizite Frequenzen: {explicit}"
    )


def _segment_text(
    magnitude_segment: int | None,
    phase_segment: int | None,
) -> str:
    if magnitude_segment is None and phase_segment is None:
        return "Unterbrechung – kein darstellbares Segment"
    magnitude = (
        "Unterbrechung"
        if magnitude_segment is None
        else str(magnitude_segment)
    )
    phase = "Unterbrechung" if phase_segment is None else str(phase_segment)
    return f"Betrag: {magnitude}; Phase: {phase}"


def _reduced_text(result: FrequencyDomainWorkflowResult) -> str:
    reduced = result.reduced_value
    if reduced is None:
        return ""
    return (
        f"({reduced.numerator.expression.canonical_text}) / "
        f"({reduced.denominator.expression.canonical_text})"
    )


def _substitutions_text(result: FrequencyDomainWorkflowResult) -> str:
    substitutions = result.substitutions
    if substitutions is None or not substitutions.assignments:
        return "keine"
    return ", ".join(
        f"{assignment.parameter_name}={_rational_text(assignment.value)}"
        for assignment in substitutions.assignments
    )


def _rational_text(value: object) -> str:
    numerator = value.numerator  # type: ignore[attr-defined]
    denominator = value.denominator  # type: ignore[attr-defined]
    return str(numerator) if denominator == 1 else f"{numerator}/{denominator}"


def _expression_text(value: object | None) -> str:
    return "" if value is None else value.canonical_text  # type: ignore[attr-defined]


def _decibel_text(value: object | None) -> str:
    if value is None:
        return ""
    if value.kind.value == "negative_infinity":  # type: ignore[attr-defined]
        return "−∞"
    return value.decimal_value  # type: ignore[attr-defined,no-any-return]


def _optional(value: str | None) -> str:
    return "" if value is None else value


def _degree_text(value: str | None) -> str:
    return "" if value is None else f"{value}°"


def _status_text(value: str) -> str:
    return _STATUS_LABELS.get(value, _POINT_STATUS_LABELS.get(value, value))


def _short_number(value: str) -> str:
    if not value or value == "−∞":
        return value
    try:
        number = Decimal(value)
    except ValueError:
        return value
    if not number.is_finite() or number.is_zero():
        return value
    exponent = number.adjusted()
    if exponent >= 6 or exponent <= -4:
        return f"{number:.5E}".replace("E+", "e+").replace("E-", "e-")
    decimal_places = max(0, 5 - exponent)
    formatted = f"{number:.{decimal_places}f}"
    if "." in formatted:
        formatted = formatted.rstrip("0").rstrip(".")
    return formatted


def _short_rational(value: object) -> str:
    full = _rational_text(value)
    if len(full) <= 12:
        return full
    numerator = value.numerator  # type: ignore[attr-defined]
    denominator = value.denominator  # type: ignore[attr-defined]
    return _short_number(str(Decimal(numerator) / Decimal(denominator)))


def _added_frequencies_text(values: tuple[Any, ...]) -> str:
    if not values:
        return ""
    frequencies = "; ".join(
        _short_number(
            str(
                Decimal(value.numerator)
                / Decimal(value.denominator)
            )
        )
        for value in values
    )
    return f"{frequencies} rad/s"


def _diagnostic_focus(result: FrequencyDomainWorkflowResult) -> str | None:
    if result.request is not None or not result.diagnostics:
        return None
    details = result.diagnostics[0].technical_details
    if not details:
        return None
    return details[0][0].removeprefix("preparation_request.")


__all__ = ["FrequencyDomainPresenter"]
