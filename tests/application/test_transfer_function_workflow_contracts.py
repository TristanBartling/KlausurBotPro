"""Contract and architecture tests for the application workflow."""

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from klausurbotpro.application import (
    TransferFunctionWorkflowLimits,
    TransferFunctionWorkflowRequest,
    TransferFunctionWorkflowService,
    WorkflowDiagnosticCode,
    WorkflowInputForm,
    WorkflowStage,
    WorkflowStageStatus,
    WorkflowValueOrigin,
)


def _request() -> TransferFunctionWorkflowRequest:
    return TransferFunctionWorkflowRequest(
        WorkflowInputForm.COMMON,
        common_expression_text="1/(s+1)",
    )


def test_public_contracts_are_immutable_and_stage_order_is_fixed() -> None:
    request = _request()
    state = TransferFunctionWorkflowService().run(request)

    with pytest.raises(FrozenInstanceError):
        request.variable_name = "z"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        state.operation_sequence = 2  # type: ignore[misc]
    assert tuple(record.stage for record in state.stage_records) == tuple(
        WorkflowStage
    )
    assert all(
        record.status is WorkflowStageStatus.SUCCEEDED
        for record in state.stage_records
    )
    assert all(
        record.value_origin is WorkflowValueOrigin.COMPUTED
        for record in state.stage_records
    )


def test_limits_validate_application_bounds() -> None:
    with pytest.raises(ValueError, match="max_aggregated_diagnostics"):
        TransferFunctionWorkflowLimits(max_aggregated_diagnostics=0)
    with pytest.raises(ValueError, match="max_override_reason_length"):
        TransferFunctionWorkflowLimits(max_override_reason_length=0)
    with pytest.raises(ValueError, match="max_operation_sequence"):
        TransferFunctionWorkflowLimits(max_operation_sequence=0)


@pytest.mark.parametrize(
    "workflow_request",
    [
        TransferFunctionWorkflowRequest(
            WorkflowInputForm.COMMON,
            common_expression_text="1",
            numerator_expression_text="1",
        ),
        TransferFunctionWorkflowRequest(
            WorkflowInputForm.SEPARATED,
            numerator_expression_text="1",
        ),
        TransferFunctionWorkflowRequest(
            WorkflowInputForm.COMMON,
            common_expression_text="1",
            variable_name="unsafe-name",
        ),
        TransferFunctionWorkflowRequest(
            WorkflowInputForm.COMMON,
            common_expression_text="1",
            allowed_parameter_names=("T", "K"),
        ),
        TransferFunctionWorkflowRequest(
            WorkflowInputForm.COMMON,
            common_expression_text="1",
            allowed_parameter_names=("s",),
        ),
    ],
)
def test_invalid_requests_are_structured(
    workflow_request: TransferFunctionWorkflowRequest,
) -> None:
    state = TransferFunctionWorkflowService().run(workflow_request)

    assert state.stage_records[0].status is WorkflowStageStatus.FAILED
    assert all(
        record.status is WorkflowStageStatus.BLOCKED
        for record in state.stage_records[1:]
    )
    assert state.aggregated_diagnostics[-1].diagnostic.code.value == (
        WorkflowDiagnosticCode.WORKFLOW_INVALID_REQUEST.value
    )


def test_wrong_top_level_request_types_raise_type_error() -> None:
    class RequestSubclass(TransferFunctionWorkflowRequest):
        pass

    service = TransferFunctionWorkflowService()
    with pytest.raises(TypeError, match="TransferFunctionWorkflowRequest"):
        service.run(object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="TransferFunctionWorkflowRequest"):
        service.run(
            RequestSubclass(
                WorkflowInputForm.COMMON,
                common_expression_text="1",
            )
        )


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("field", object()),
        ("input_form", object()),
        ("allowed_parameter_names", ("K", object())),
    ],
)
def test_manipulated_request_fields_remain_structured(
    field_name: str,
    value: object,
) -> None:
    request = _request()
    object.__setattr__(request, field_name, value)

    state = TransferFunctionWorkflowService().run(request)

    assert state.stage_records[0].status is WorkflowStageStatus.FAILED
    assert WorkflowDiagnosticCode.WORKFLOW_INVALID_REQUEST.value in {
        entry.diagnostic.code.value
        for entry in state.aggregated_diagnostics
    }


def test_request_identifier_string_subclasses_are_rejected() -> None:
    class MutableString(str):
        pass

    request = _request()
    object.__setattr__(request, "variable_name", MutableString("s"))

    state = TransferFunctionWorkflowService().run(request)

    assert state.stage_records[0].status is WorkflowStageStatus.FAILED


def test_application_import_direction_and_ui_independence() -> None:
    root = Path(__file__).parents[2]
    application_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((root / "src/klausurbotpro/application").glob("*.py"))
    )
    domain_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((root / "src/klausurbotpro/domain").glob("*.py"))
    )

    assert "PySide6" not in application_text
    assert "from klausurbotpro.app import" not in application_text
    assert "import klausurbotpro.app\n" not in application_text
    assert "sympify" not in application_text
    assert "parse_expr" not in application_text
    assert "klausurbotpro.application" not in domain_text
