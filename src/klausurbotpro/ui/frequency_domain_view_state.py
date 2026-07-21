"""Immutable widget-free presentation state for the frequency GUI."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from klausurbotpro.application import FrequencyDomainRequestFieldError


class FrequencyDomainUiRunStatus(StrEnum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETE = "complete"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class FrequencyDomainSummaryView:
    workflow_status: str = ""
    mode: str = ""
    reduced_transfer_function: str = ""
    substitutions: str = ""
    frequency_count: str = ""
    domain_status: str = ""
    magnitude_segment_count: str = ""
    phase_segment_count: str = ""
    phase_unwrap: str = ""
    added_frequencies: str = ""

    def __post_init__(self) -> None:
        if any(type(getattr(self, field)) is not str for field in self.__dataclass_fields__):
            raise TypeError("Frequency summaries may contain only strings.")


@dataclass(frozen=True, slots=True)
class FrequencyDomainSinglePointView:
    omega: str = ""
    status: str = ""
    complex_value: str = ""
    real_part: str = ""
    imaginary_part: str = ""
    magnitude: str = ""
    decibel: str = ""
    principal_phase: str = ""

    def __post_init__(self) -> None:
        if any(type(getattr(self, field)) is not str for field in self.__dataclass_fields__):
            raise TypeError("Single-point views may contain only strings.")


@dataclass(frozen=True, slots=True)
class FrequencyDomainTableRow:
    index: str
    target_omega: str
    evaluation_omega: str
    status: str
    real_part: str
    imaginary_part: str
    magnitude: str
    decibel: str
    principal_phase: str
    unwrapped_phase: str
    tooltips: tuple[str, ...]

    def __post_init__(self) -> None:
        if any(
            type(getattr(self, field)) is not str
            for field in self.__dataclass_fields__
            if field != "tooltips"
        ):
            raise TypeError("Frequency table rows may contain only strings.")
        if (
            type(self.tooltips) is not tuple
            or len(self.tooltips) != 10
            or any(type(value) is not str for value in self.tooltips)
        ):
            raise TypeError("Frequency table tooltips must contain ten strings.")


@dataclass(frozen=True, slots=True)
class FrequencyReserveTableRow:
    index: str
    crossover: str
    omega: str
    phase_branch: str
    unwrapped_phase: str
    decibel: str
    reserve: str
    quality: str

    def __post_init__(self) -> None:
        if any(type(getattr(self, field)) is not str for field in self.__dataclass_fields__):
            raise TypeError("Reserve table rows may contain only strings.")


@dataclass(frozen=True, slots=True)
class PlotSegmentView:
    x_values: tuple[str, ...]
    y_values: tuple[str, ...]

    def __post_init__(self) -> None:
        if (
            type(self.x_values) is not tuple
            or type(self.y_values) is not tuple
            or not self.x_values
            or len(self.x_values) != len(self.y_values)
            or any(type(value) is not str for value in self.x_values)
            or any(type(value) is not str for value in self.y_values)
        ):
            raise TypeError("Plot segments require equally sized string tuples.")


@dataclass(frozen=True, slots=True)
class PlotMarkerView:
    x_value: str
    label: str
    y_value: str = ""

    def __post_init__(self) -> None:
        if (
            type(self.x_value) is not str
            or not self.x_value
            or type(self.label) is not str
            or not self.label
            or type(self.y_value) is not str
        ):
            raise TypeError("Plot markers require non-empty display strings.")


@dataclass(frozen=True, slots=True)
class StandardElementTableRow:
    number: str
    element_type: str
    factor: str
    gain_share: str
    time_constant: str
    corner_frequency: str
    slope_change: str
    phase_change: str
    support: str


@dataclass(frozen=True, slots=True)
class PlotComponentView:
    label: str
    exact_magnitude: PlotSegmentView
    exact_phase: PlotSegmentView
    asymptotic_magnitude: PlotSegmentView
    asymptotic_phase: PlotSegmentView
    rough_magnitude: PlotSegmentView
    rough_phase: PlotSegmentView


@dataclass(frozen=True, slots=True)
class PlotView:
    visible: bool = False
    magnitude_segments: tuple[PlotSegmentView, ...] = ()
    principal_phase_segments: tuple[PlotSegmentView, ...] = ()
    unwrapped_phase_segments: tuple[PlotSegmentView, ...] = ()
    interruption_markers: tuple[PlotMarkerView, ...] = ()
    gain_crossover_markers: tuple[PlotMarkerView, ...] = ()
    phase_crossover_markers: tuple[PlotMarkerView, ...] = ()
    corner_frequency_markers: tuple[PlotMarkerView, ...] = ()
    component_curves: tuple[PlotComponentView, ...] = ()
    standard_element_rows: tuple[StandardElementTableRow, ...] = ()
    decomposition_message: str = ""
    no_data_message: str = ""

    def __post_init__(self) -> None:
        if type(self.visible) is not bool:
            raise TypeError("Plot visibility must be a bool.")
        for name in (
            "magnitude_segments",
            "principal_phase_segments",
            "unwrapped_phase_segments",
        ):
            values = getattr(self, name)
            if type(values) is not tuple or any(
                type(value) is not PlotSegmentView for value in values
            ):
                raise TypeError(f"{name} must contain plot segment views.")
        if type(self.interruption_markers) is not tuple or any(
            type(value) is not PlotMarkerView for value in self.interruption_markers
        ):
            raise TypeError("interruption_markers must contain plot markers.")
        for name in (
            "gain_crossover_markers",
            "phase_crossover_markers",
            "corner_frequency_markers",
        ):
            values = getattr(self, name)
            if type(values) is not tuple or any(
                type(value) is not PlotMarkerView for value in values
            ):
                raise TypeError(f"{name} must contain plot markers.")
        if any(type(value) is not PlotComponentView for value in self.component_curves):
            raise TypeError("component_curves must contain component views.")
        if any(
            type(value) is not StandardElementTableRow
            for value in self.standard_element_rows
        ):
            raise TypeError("standard_element_rows must contain table rows.")
        if type(self.no_data_message) is not str:
            raise TypeError("The plot message must be a string.")


@dataclass(frozen=True, slots=True)
class NyquistView:
    visible: bool = False
    positive_segments: tuple[PlotSegmentView, ...] = ()
    negative_segments: tuple[PlotSegmentView, ...] = ()
    crossover_markers: tuple[PlotMarkerView, ...] = ()
    p: str = "—"
    n_cw: str = "—"
    z: str = "—"
    criterion: str = ""
    prerequisites: str = ""
    status: str = ""
    minimum_distance: str = ""
    critical_frequency: str = ""
    scalar_gain_intervals: str = ""

    def __post_init__(self) -> None:
        if type(self.visible) is not bool:
            raise TypeError("Nyquist visibility must be a bool.")
        for values in (self.positive_segments, self.negative_segments):
            if type(values) is not tuple or any(
                type(value) is not PlotSegmentView for value in values
            ):
                raise TypeError("Nyquist segments must be plot segment views.")
        if type(self.crossover_markers) is not tuple or any(
            type(value) is not PlotMarkerView for value in self.crossover_markers
        ):
            raise TypeError("Nyquist crossover markers are invalid.")


@dataclass(frozen=True, slots=True)
class FrequencyPointDetailView:
    heading: str = ""
    lines: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if type(self.heading) is not str or type(self.lines) is not tuple:
            raise TypeError("Point details require a heading and line tuple.")
        if any(
            type(line) is not tuple
            or len(line) != 2
            or any(type(value) is not str for value in line)
            for line in self.lines
        ):
            raise TypeError("Point detail lines must be string pairs.")


@dataclass(frozen=True, slots=True)
class WorkedStepsView:
    general_lines: tuple[tuple[str, str], ...] = ()
    point_details: tuple[FrequencyPointDetailView, ...] = ()
    short_solutions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if type(self.general_lines) is not tuple or any(
            type(line) is not tuple
            or len(line) != 2
            or any(type(value) is not str for value in line)
            for line in self.general_lines
        ):
            raise TypeError("Worked-step lines must be string pairs.")
        if type(self.point_details) is not tuple or any(
            type(value) is not FrequencyPointDetailView for value in self.point_details
        ):
            raise TypeError("Worked steps require point detail views.")
        if (
            type(self.short_solutions) is not tuple
            or any(type(value) is not str for value in self.short_solutions)
            or (self.short_solutions and len(self.short_solutions) != len(self.point_details))
        ):
            raise TypeError("Short solutions must align with point details.")


@dataclass(frozen=True, slots=True)
class FrequencyDomainDiagnosticView:
    severity: str
    message: str
    field: str

    def __post_init__(self) -> None:
        if any(type(getattr(self, name)) is not str for name in ("severity", "message", "field")):
            raise TypeError("Diagnostic views may contain only strings.")


@dataclass(frozen=True, slots=True)
class FrequencyDomainViewState:
    run_status: FrequencyDomainUiRunStatus = FrequencyDomainUiRunStatus.IDLE
    summary: FrequencyDomainSummaryView = FrequencyDomainSummaryView()
    single_point: FrequencyDomainSinglePointView = FrequencyDomainSinglePointView()
    rows: tuple[FrequencyDomainTableRow, ...] = ()
    reserve_rows: tuple[FrequencyReserveTableRow, ...] = ()
    plot: PlotView = PlotView()
    nyquist: NyquistView = NyquistView()
    worked_steps: WorkedStepsView = WorkedStepsView()
    latex_report: str = ""
    selected_bode_index: int = 0
    diagnostics: tuple[FrequencyDomainDiagnosticView, ...] = ()
    request_errors: tuple[FrequencyDomainRequestFieldError, ...] = ()
    focused_field: str | None = None
    general_message: str = "Bereit."

    def __post_init__(self) -> None:
        if type(self.run_status) is not FrequencyDomainUiRunStatus:
            raise TypeError("run_status has an invalid type.")
        if type(self.summary) is not FrequencyDomainSummaryView:
            raise TypeError("summary has an invalid type.")
        if type(self.single_point) is not FrequencyDomainSinglePointView:
            raise TypeError("single_point has an invalid type.")
        if type(self.plot) is not PlotView:
            raise TypeError("plot has an invalid type.")
        if type(self.nyquist) is not NyquistView:
            raise TypeError("nyquist has an invalid type.")
        if type(self.worked_steps) is not WorkedStepsView:
            raise TypeError("worked_steps has an invalid type.")
        if type(self.latex_report) is not str:
            raise TypeError("latex_report must be a string.")
        if type(self.selected_bode_index) is not int or self.selected_bode_index < 0:
            raise ValueError("selected_bode_index must be nonnegative.")
        for values, value_type, name in (
            (self.rows, FrequencyDomainTableRow, "rows"),
            (self.reserve_rows, FrequencyReserveTableRow, "reserve_rows"),
            (
                self.diagnostics,
                FrequencyDomainDiagnosticView,
                "diagnostics",
            ),
            (
                self.request_errors,
                FrequencyDomainRequestFieldError,
                "request_errors",
            ),
        ):
            if type(values) is not tuple or any(type(value) is not value_type for value in values):
                raise TypeError(f"{name} have an invalid type.")
        if self.focused_field is not None and (type(self.focused_field) is not str):
            raise TypeError("focused_field must be str or None.")
        if type(self.general_message) is not str:
            raise TypeError("general_message must be a string.")


__all__ = [
    "FrequencyPointDetailView",
    "FrequencyDomainDiagnosticView",
    "FrequencyDomainSummaryView",
    "FrequencyDomainSinglePointView",
    "FrequencyDomainTableRow",
    "FrequencyReserveTableRow",
    "FrequencyDomainUiRunStatus",
    "FrequencyDomainViewState",
    "PlotMarkerView",
    "PlotComponentView",
    "StandardElementTableRow",
    "NyquistView",
    "PlotSegmentView",
    "PlotView",
    "WorkedStepsView",
]
