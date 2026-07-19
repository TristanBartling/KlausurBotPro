"""Defensive result revalidation for the frequency-domain workflow."""

from __future__ import annotations

from copy import copy

import pytest

from klausurbotpro.application import (
    FrequencyDomainWorkflowDiagnosticCode,
    FrequencyDomainWorkflowLimits,
    FrequencyDomainWorkflowMode,
    FrequencyDomainWorkflowRequest,
    FrequencyDomainWorkflowResult,
    FrequencyDomainWorkflowService,
    FrequencyDomainWorkflowStageStatus,
    FrequencyDomainWorkflowStatus,
    FrequencyPhasePresentation,
    TransferFunctionWorkflowRequest,
    WorkflowInputForm,
)
from klausurbotpro.application._frequency_domain_workflow_validation import (
    FrequencyDomainWorkflowFailure,
    validate_frequency_domain_workflow_result,
)
from klausurbotpro.domain import (
    DiagnosticCode,
    DiagnosticSeverity,
    ExactRationalValue,
    LogFrequencyGridRequest,
)


def _preparation(expression: str = "1/(s+1)") -> TransferFunctionWorkflowRequest:
    return TransferFunctionWorkflowRequest(
        WorkflowInputForm.COMMON,
        common_expression_text=expression,
    )


def _single() -> FrequencyDomainWorkflowResult:
    request = FrequencyDomainWorkflowRequest(
        _preparation(),
        FrequencyDomainWorkflowMode.SINGLE_POINT,
        single_angular_frequency=ExactRationalValue(1),
    )
    return FrequencyDomainWorkflowService().run(request)


def _bode(*, unwrap: bool = False) -> FrequencyDomainWorkflowResult:
    request = FrequencyDomainWorkflowRequest(
        _preparation(),
        FrequencyDomainWorkflowMode.BODE,
        grid_request=LogFrequencyGridRequest(
            ExactRationalValue(1, 10),
            ExactRationalValue(10),
            2,
        ),
        phase_presentation=(
            FrequencyPhasePresentation.PRINCIPAL_AND_UNWRAPPED
            if unwrap
            else FrequencyPhasePresentation.PRINCIPAL_ONLY
        ),
    )
    return FrequencyDomainWorkflowService().run(request)


def _invalid_request() -> FrequencyDomainWorkflowResult:
    return FrequencyDomainWorkflowService().run(
        FrequencyDomainWorkflowRequest(
            _preparation(),
            FrequencyDomainWorkflowMode.SINGLE_POINT,
        )
    )


def _validate(result: object) -> None:
    validate_frequency_domain_workflow_result(
        result,  # type: ignore[arg-type]
        FrequencyDomainWorkflowLimits(),
    )


def _reject(result: FrequencyDomainWorkflowResult) -> None:
    with pytest.raises(FrequencyDomainWorkflowFailure):
        _validate(result)


def _clone_controlled[T](value: T) -> T:
    clone = object.__new__(type(value))
    fields = type(value).__dataclass_fields__  # type: ignore[attr-defined]
    for name in fields:
        object.__setattr__(clone, name, getattr(value, name))
    return clone


def test_complete_single_bode_and_unwrap_results_revalidate() -> None:
    _validate(_single())
    _validate(_bode())
    _validate(_bode(unwrap=True))


def test_wrong_top_level_result_type_raises_type_error() -> None:
    with pytest.raises(TypeError):
        _validate(object())


@pytest.mark.parametrize(
    ("attribute", "replacement"),
    [
        ("severity", DiagnosticSeverity.INFO),
        (
            "code",
            FrequencyDomainWorkflowDiagnosticCode.PREPARATION_FAILED,
        ),
        ("code", DiagnosticCode.LOG_FREQUENCY_GRID_INVALID_REQUEST),
        ("message", " "),
        ("field", "frequency"),
        ("technical_details", ()),
        ("technical_details", (("", "invalid"),)),
    ],
)
def test_manipulated_invalid_request_diagnostic_is_rejected(
    attribute: str,
    replacement: object,
) -> None:
    result = _invalid_request()
    diagnostic = result.diagnostics[0]
    object.__setattr__(diagnostic, attribute, replacement)

    _reject(result)


def test_invalid_request_rejects_additional_diagnostics() -> None:
    result = _invalid_request()
    object.__setattr__(
        result,
        "diagnostics",
        (result.diagnostics[0], result.diagnostics[0]),
    )
    _reject(result)


@pytest.mark.parametrize(
    ("attribute", "replacement"),
    [
        ("status", FrequencyDomainWorkflowStatus.PARTIAL),
        ("preparation_result", None),
        ("single_point_result", None),
        ("diagnostics", (object(),)),
    ],
)
def test_manipulated_single_result_is_rejected(
    attribute: str,
    replacement: object,
) -> None:
    result = _single()
    object.__setattr__(result, attribute, replacement)
    _reject(result)


def test_manipulated_request_and_preparation_are_rejected() -> None:
    result = _single()
    assert result.request is not None
    object.__setattr__(
        result.request,
        "single_angular_frequency",
        ExactRationalValue(2),
    )
    _reject(result)

    result = _single()
    assert result.preparation_result is not None
    object.__setattr__(
        result.preparation_result,
        "parsed_input",
        None,
    )
    _reject(result)


def test_manipulated_single_point_context_is_rejected() -> None:
    result = _single()
    assert result.single_point_result is not None
    assert result.single_point_result.frequencies is not None
    object.__setattr__(
        result.single_point_result.frequencies,
        "frequencies",
        (ExactRationalValue(2),),
    )
    _reject(result)


def test_manipulated_grid_and_bode_handoffs_are_rejected() -> None:
    result = _bode()
    assert result.grid_result is not None
    assert result.bode_data_result is not None
    object.__setattr__(
        result.grid_result,
        "interval_count",
        result.grid_result.interval_count + 1,  # type: ignore[operator]
    )
    _reject(result)

    result = _bode()
    assert result.grid_result is not None
    assert result.bode_data_result is not None
    foreign_grid = _clone_controlled(result.grid_result)
    object.__setattr__(result.bode_data_result, "grid", foreign_grid)
    _reject(result)


def test_manipulated_unwrap_source_is_rejected() -> None:
    result = _bode(unwrap=True)
    assert result.bode_data_result is not None
    assert result.phase_unwrap_result is not None
    foreign_bode = _clone_controlled(result.bode_data_result)
    object.__setattr__(
        result.phase_unwrap_result,
        "source_bode_data",
        foreign_bode,
    )
    _reject(result)


def test_foreign_cloned_reduced_handoff_is_rejected() -> None:
    result = _single()
    assert result.single_point_result is not None
    assert result.single_point_result.reduced_transfer_function is not None
    clone = _clone_controlled(
        result.single_point_result.reduced_transfer_function
    )
    assert clone == result.reduced_value
    object.__setattr__(
        result.single_point_result,
        "reduced_transfer_function",
        clone,
    )
    _reject(result)


def test_stage_order_status_and_aggregation_are_rejected() -> None:
    result = _bode()
    object.__setattr__(
        result,
        "stage_records",
        tuple(reversed(result.stage_records)),
    )
    _reject(result)

    result = _bode()
    object.__setattr__(
        result.stage_records[2],
        "status",
        FrequencyDomainWorkflowStageStatus.FAILED,
    )
    _reject(result)

    result = _bode()
    diagnostic = copy(result.bode_data_result.diagnostics[0]) if (
        result.bode_data_result is not None
        and result.bode_data_result.diagnostics
    ) else None
    if diagnostic is None:
        object.__setattr__(result, "diagnostics", (object(),))
    else:
        object.__setattr__(diagnostic, "message", "Fremd.")
        object.__setattr__(result, "diagnostics", (diagnostic,))
    _reject(result)


def test_repeated_workflows_are_deterministic() -> None:
    request = FrequencyDomainWorkflowRequest(
        _preparation("1/(s^2+s+1)"),
        FrequencyDomainWorkflowMode.BODE,
        grid_request=LogFrequencyGridRequest(
            ExactRationalValue(1, 10),
            ExactRationalValue(10),
            2,
        ),
    )
    service = FrequencyDomainWorkflowService()
    assert service.run(request) == service.run(request)
