"""Presenter for the small frequency-domain GUI workflow."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Slot

from klausurbotpro.application import (
    FrequencyDomainInputDraft,
    FrequencyDomainRequestFactory,
    FrequencyDomainWorkflowResult,
    FrequencyDomainWorkflowStatus,
)
from klausurbotpro.ui.frequency_domain_view_state import (
    FrequencyDomainDiagnosticView,
    FrequencyDomainSinglePointView,
    FrequencyDomainSummaryView,
    FrequencyDomainTableRow,
    FrequencyDomainUiRunStatus,
    FrequencyDomainViewState,
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


class FrequencyDomainPresenter(QObject):
    """Create one request and project validated results into display strings."""

    execution_requested = Signal(object)
    state_changed = Signal(object)

    def __init__(self, request_factory: FrequencyDomainRequestFactory) -> None:
        super().__init__()
        if type(request_factory) is not FrequencyDomainRequestFactory:
            raise TypeError("request_factory has an invalid type.")
        self._request_factory = request_factory
        self._state = FrequencyDomainViewState()

    @property
    def state(self) -> FrequencyDomainViewState:
        return self._state

    def submit(self, draft: FrequencyDomainInputDraft) -> bool:
        if type(draft) is not FrequencyDomainInputDraft:
            raise TypeError("draft must be FrequencyDomainInputDraft.")
        if self._state.run_status is FrequencyDomainUiRunStatus.RUNNING:
            return False
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
        self._set_state(
            FrequencyDomainViewState(
                run_status=status,
                summary=_summary(value),
                single_point=_single_point(value),
                rows=_rows(value),
                diagnostics=tuple(
                    FrequencyDomainDiagnosticView(
                        diagnostic.severity.value,
                        diagnostic.message,
                        "" if diagnostic.field is None else diagnostic.field,
                    )
                    for diagnostic in value.diagnostics
                ),
                focused_field=_diagnostic_focus(value),
                general_message={
                    FrequencyDomainUiRunStatus.COMPLETE: (
                        "Frequenzberechnung vollständig abgeschlossen."
                    ),
                    FrequencyDomainUiRunStatus.PARTIAL: (
                        "Frequenzberechnung mit Teilresultat abgeschlossen."
                    ),
                    FrequencyDomainUiRunStatus.FAILED: (
                        "Frequenzberechnung fehlgeschlagen."
                    ),
                }[status],
            )
        )

    @Slot(object)
    def accept_failure(self, value: object) -> None:
        if type(value) is not WorkflowWorkerFailure:
            raise TypeError("value must be WorkflowWorkerFailure.")
        self._set_state(
            FrequencyDomainViewState(
                run_status=FrequencyDomainUiRunStatus.FAILED,
                general_message=value.message,
            )
        )

    def reset(self) -> bool:
        if self._state.run_status is FrequencyDomainUiRunStatus.RUNNING:
            return False
        self._set_state(FrequencyDomainViewState())
        return True

    def set_general_message(self, message: str) -> None:
        if type(message) is not str or not message:
            raise ValueError("message must be a non-empty string.")
        self._set_state(
            FrequencyDomainViewState(
                run_status=self._state.run_status,
                summary=self._state.summary,
                single_point=self._state.single_point,
                rows=self._state.rows,
                diagnostics=self._state.diagnostics,
                request_errors=self._state.request_errors,
                focused_field=self._state.focused_field,
                general_message=message,
            )
        )

    def _set_state(self, state: FrequencyDomainViewState) -> None:
        self._state = state
        self.state_changed.emit(state)


def _summary(result: FrequencyDomainWorkflowResult) -> FrequencyDomainSummaryView:
    if result.request is None:
        return FrequencyDomainSummaryView(workflow_status=result.status.value)
    response = result.active_frequency_response_result
    frequency_count = 0 if response is None else len(response.points)
    bode = result.bode_data_result
    single = result.single_point_result
    domain_status = (
        bode.status.value
        if bode is not None
        else (
            ""
            if single is None or not single.points
            else single.points[0].status.value
        )
    )
    return FrequencyDomainSummaryView(
        workflow_status=result.status.value,
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
        real_part=_expression_text(point.exact_real_part),
        imaginary_part=_expression_text(point.exact_imaginary_part),
        magnitude="" if point.numerical_magnitude is None else point.numerical_magnitude,
        decibel=_decibel_text(point.numerical_decibel),
        principal_phase=(
            "nicht definiert"
            if zero
            else (
                ""
                if point.numerical_phase_degrees is None
                else point.numerical_phase_degrees
            )
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
    return tuple(
        FrequencyDomainTableRow(
            index=str(index + 1),
            target_omega=point.target_decimal.decimal_text,
            evaluation_omega=_rational_text(point.evaluation_frequency),
            status=_POINT_STATUS_LABELS[
                point.frequency_response_point.status.value
            ],
            real_part=_optional(point.frequency_response_point.numerical_real),
            imaginary_part=_optional(
                point.frequency_response_point.numerical_imaginary
            ),
            magnitude=_optional(
                point.frequency_response_point.numerical_magnitude
            ),
            decibel=_decibel_text(point.numerical_decibel),
            principal_phase=_optional(point.principal_phase_degrees),
            unwrapped_phase=unwrapped.get(index, ""),
        )
        for index, point in enumerate(bode.points)
    )


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


def _diagnostic_focus(result: FrequencyDomainWorkflowResult) -> str | None:
    if result.request is not None or not result.diagnostics:
        return None
    details = result.diagnostics[0].technical_details
    if not details:
        return None
    return details[0][0].removeprefix("preparation_request.")


__all__ = ["FrequencyDomainPresenter"]
