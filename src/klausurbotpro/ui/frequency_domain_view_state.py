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

    def __post_init__(self) -> None:
        if any(
            type(getattr(self, field)) is not str
            for field in self.__dataclass_fields__
        ):
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
        if any(
            type(getattr(self, field)) is not str
            for field in self.__dataclass_fields__
        ):
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

    def __post_init__(self) -> None:
        if any(
            type(getattr(self, field)) is not str
            for field in self.__dataclass_fields__
        ):
            raise TypeError("Frequency table rows may contain only strings.")


@dataclass(frozen=True, slots=True)
class FrequencyDomainDiagnosticView:
    severity: str
    message: str
    field: str

    def __post_init__(self) -> None:
        if any(
            type(getattr(self, name)) is not str
            for name in ("severity", "message", "field")
        ):
            raise TypeError("Diagnostic views may contain only strings.")


@dataclass(frozen=True, slots=True)
class FrequencyDomainViewState:
    run_status: FrequencyDomainUiRunStatus = FrequencyDomainUiRunStatus.IDLE
    summary: FrequencyDomainSummaryView = FrequencyDomainSummaryView()
    single_point: FrequencyDomainSinglePointView = (
        FrequencyDomainSinglePointView()
    )
    rows: tuple[FrequencyDomainTableRow, ...] = ()
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
        for values, value_type, name in (
            (self.rows, FrequencyDomainTableRow, "rows"),
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
            if type(values) is not tuple or any(
                type(value) is not value_type for value in values
            ):
                raise TypeError(f"{name} have an invalid type.")
        if self.focused_field is not None and (
            type(self.focused_field) is not str
        ):
            raise TypeError("focused_field must be str or None.")
        if type(self.general_message) is not str:
            raise TypeError("general_message must be a string.")


__all__ = [
    "FrequencyDomainDiagnosticView",
    "FrequencyDomainSummaryView",
    "FrequencyDomainSinglePointView",
    "FrequencyDomainTableRow",
    "FrequencyDomainUiRunStatus",
    "FrequencyDomainViewState",
]
