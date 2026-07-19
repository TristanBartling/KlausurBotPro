"""Defensive revalidation tests for preparation results."""

from __future__ import annotations

import pytest

from klausurbotpro.application import (
    TransferFunctionPreparationResult,
    TransferFunctionPreparationService,
    TransferFunctionPreparationStageStatus,
    TransferFunctionPreparationStatus,
    TransferFunctionWorkflowLimits,
    TransferFunctionWorkflowRequest,
    WorkflowInputForm,
)
from klausurbotpro.application._transfer_function_preparation_validation import (
    TransferFunctionPreparationFailure,
    validate_transfer_function_preparation_result,
)
from klausurbotpro.domain import TransferFunctionReductionLimits


def _request(text: str = "1/(s+1)") -> TransferFunctionWorkflowRequest:
    return TransferFunctionWorkflowRequest(
        WorkflowInputForm.COMMON,
        common_expression_text=text,
    )


def _result(
    text: str = "1/(s+1)",
) -> TransferFunctionPreparationResult:
    return TransferFunctionPreparationService().prepare(_request(text))


def _validate(result: object) -> None:
    validate_transfer_function_preparation_result(
        result,  # type: ignore[arg-type]
        TransferFunctionWorkflowLimits(),
    )


def test_unmodified_complete_and_partial_results_revalidate() -> None:
    _validate(_result())
    _validate(_result("1/0"))


def test_wrong_top_level_result_type_raises_type_error() -> None:
    with pytest.raises(TypeError):
        _validate(object())


@pytest.mark.parametrize(
    ("attribute", "replacement"),
    [
        ("status", TransferFunctionPreparationStatus.PARTIAL),
        ("parsed_input", None),
        ("raw_result", None),
        ("reduction_result", None),
        ("diagnostics", (object(),)),
    ],
)
def test_manipulated_complete_result_is_rejected(
    attribute: str,
    replacement: object,
) -> None:
    result = _result()
    object.__setattr__(result, attribute, replacement)
    with pytest.raises(TransferFunctionPreparationFailure):
        _validate(result)


def test_manipulated_request_is_rejected() -> None:
    result = _result()
    object.__setattr__(
        result.request,
        "common_expression_text",
        "1/(s+2)",
    )
    with pytest.raises(TransferFunctionPreparationFailure):
        _validate(result)


def test_foreign_raw_and_reduction_results_are_rejected() -> None:
    first = _result("1/(s+1)")
    second = _result("1/(s+2)")
    object.__setattr__(first, "raw_result", second.raw_result)
    with pytest.raises(TransferFunctionPreparationFailure):
        _validate(first)

    first = _result("1/(s+1)")
    object.__setattr__(first, "reduction_result", second.reduction_result)
    with pytest.raises(TransferFunctionPreparationFailure):
        _validate(first)


def test_manipulated_stage_order_and_status_are_rejected() -> None:
    result = _result()
    object.__setattr__(
        result,
        "stage_records",
        tuple(reversed(result.stage_records)),
    )
    with pytest.raises(TransferFunctionPreparationFailure):
        _validate(result)

    result = _result()
    object.__setattr__(
        result.stage_records[1],
        "status",
        TransferFunctionPreparationStageStatus.FAILED,
    )
    with pytest.raises(TransferFunctionPreparationFailure):
        _validate(result)


def test_result_after_blocked_stage_cannot_retain_values() -> None:
    result = _result("1/0")
    object.__setattr__(result, "reduction_result", _result().reduction_result)
    with pytest.raises(TransferFunctionPreparationFailure):
        _validate(result)


def test_validation_uses_explicit_limits() -> None:
    result = _result()
    with pytest.raises(TransferFunctionPreparationFailure):
        validate_transfer_function_preparation_result(
            result,
            TransferFunctionWorkflowLimits(
                reduction=TransferFunctionReductionLimits(max_input_terms=1)
            ),
        )
