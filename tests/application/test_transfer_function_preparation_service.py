"""Acceptance tests for the shared parse-to-reduction pipeline."""

from __future__ import annotations

import pytest

import klausurbotpro.application.transfer_function_preparation_service as service_module
from klausurbotpro.application import (
    TransferFunctionPreparationResult,
    TransferFunctionPreparationService,
    TransferFunctionPreparationStageStatus,
    TransferFunctionPreparationStatus,
    TransferFunctionWorkflowLimits,
    TransferFunctionWorkflowRequest,
    TransferFunctionWorkflowService,
    WorkflowInputForm,
)
from klausurbotpro.domain import (
    ExactRationalValue,
    ParameterAssignment,
    ParameterSubstitutions,
    TransferFunctionReducer,
    TransferFunctionReductionLimits,
    TransferFunctionRootAnalyzer,
    TransferFunctionStabilityAnalyzer,
)


def _common(
    text: str,
    *,
    parameters: tuple[str, ...] = (),
    substitutions: ParameterSubstitutions | None = None,
) -> TransferFunctionWorkflowRequest:
    return TransferFunctionWorkflowRequest(
        WorkflowInputForm.COMMON,
        common_expression_text=text,
        allowed_parameter_names=parameters,
        substitutions=substitutions,
        field="transfer_function",
    )


def test_common_and_separated_requests_produce_the_same_reduced_value() -> None:
    service = TransferFunctionPreparationService()
    common = service.prepare(_common("1/(s+1)"))
    separated = service.prepare(
        TransferFunctionWorkflowRequest(
            WorkflowInputForm.SEPARATED,
            numerator_expression_text="1",
            denominator_expression_text="s+1",
        )
    )
    assert common.status is TransferFunctionPreparationStatus.COMPLETE
    assert len(common.stage_records) == 3
    assert common.raw_value is not None
    assert common.raw_value.input_snapshot is common.parsed_input
    assert common.reduced_value == separated.reduced_value
    assert common.raw_value is common.raw_result.value  # type: ignore[union-attr]
    assert common.reduced_value is common.reduction_result.reduced  # type: ignore[union-attr]
    assert common.succeeded


def test_symbolic_parameters_and_exact_substitutions_remain_in_request() -> None:
    substitutions = ParameterSubstitutions(
        (ParameterAssignment("T", ExactRationalValue(3, 2)),)
    )
    request = _common(
        "1/(T*s+1)",
        parameters=("T",),
        substitutions=substitutions,
    )
    result = TransferFunctionPreparationService().prepare(request)
    assert result.request is request
    assert result.request.substitutions is substitutions
    assert result.reduced_value is not None
    assert result.reduced_value.used_parameter_names == frozenset({"T"})


@pytest.mark.parametrize("text", ["open('x')", "s[0]", "s if s else 1"])
def test_parse_failures_are_value_free_and_block_followers(text: str) -> None:
    result = TransferFunctionPreparationService().prepare(_common(text))
    assert result.status is TransferFunctionPreparationStatus.FAILED
    assert result.parsed_input is None
    assert result.raw_result is None
    assert result.reduction_result is None
    assert result.stage_records[0].status is (
        TransferFunctionPreparationStageStatus.FAILED
    )
    assert all(
        item.status is TransferFunctionPreparationStageStatus.BLOCKED
        for item in result.stage_records[1:]
    )
    assert (
        sum(item.code.value.startswith("workflow.") for item in result.diagnostics)
        == 1
    )


def test_structurally_invalid_request_returns_a_valid_failed_envelope() -> None:
    request = _common("1/(s+1)")
    object.__setattr__(request, "variable_name", "__unsafe__")
    result = TransferFunctionPreparationService().prepare(request)
    assert result.status is TransferFunctionPreparationStatus.FAILED
    assert result.request is request
    assert result.parsed_input is None
    assert result.diagnostics[0].code.value == "workflow.invalid_request"


def test_raw_failure_retains_only_the_parsed_input() -> None:
    result = TransferFunctionPreparationService().prepare(_common("1/0"))
    assert result.status is TransferFunctionPreparationStatus.PARTIAL
    assert result.parsed_input is not None
    assert result.raw_result is not None and not result.raw_result.succeeded
    assert result.reduction_result is None
    assert tuple(item.status for item in result.stage_records) == (
        TransferFunctionPreparationStageStatus.SUCCEEDED,
        TransferFunctionPreparationStageStatus.FAILED,
        TransferFunctionPreparationStageStatus.BLOCKED,
    )


def test_reduction_failure_retains_parsed_and_raw_results() -> None:
    result = TransferFunctionPreparationService(
        TransferFunctionWorkflowLimits(
            reduction=TransferFunctionReductionLimits(max_input_terms=1)
        )
    ).prepare(_common("(s+1)/(s+2)"))
    assert result.status is TransferFunctionPreparationStatus.PARTIAL
    assert result.parsed_input is not None
    assert result.raw_result is not None and result.raw_result.succeeded
    assert result.reduction_result is not None
    assert not result.reduction_result.succeeded
    assert result.stage_records[2].status is (
        TransferFunctionPreparationStageStatus.FAILED
    )


@pytest.mark.parametrize("error_type", [MemoryError, RecursionError, OverflowError])
@pytest.mark.parametrize(
    ("stage", "patch_name"),
    [
        ("parse", "parse_request"),
        ("raw", "raw_factory_for"),
        ("reduction", "reduce"),
    ],
)
def test_resource_errors_are_attached_to_the_affected_stage(
    monkeypatch: pytest.MonkeyPatch,
    error_type: type[BaseException],
    stage: str,
    patch_name: str,
) -> None:
    class ExhaustedFactory:
        def create(self, *args: object, **kwargs: object) -> object:
            raise error_type

    def exhaust(*args: object, **kwargs: object) -> object:
        raise error_type

    if patch_name == "parse_request":
        monkeypatch.setattr(service_module, patch_name, exhaust)
    elif patch_name == "raw_factory_for":
        monkeypatch.setattr(
            service_module,
            patch_name,
            lambda *args, **kwargs: ExhaustedFactory(),
        )
    else:
        monkeypatch.setattr(
            TransferFunctionReducer,
            patch_name,
            exhaust,
        )
    result = TransferFunctionPreparationService().prepare(_common("1/(s+1)"))
    index = {"parse": 0, "raw": 1, "reduction": 2}[stage]
    assert result.stage_records[index].status is (
        TransferFunctionPreparationStageStatus.FAILED
    )
    assert result.diagnostics[-1].code.value == (
        "workflow.resource_limit_exceeded"
    )
    if index == 0:
        assert result.parsed_input is None
    else:
        assert result.parsed_input is not None
    if index <= 1:
        assert result.raw_result is None
    else:
        assert result.raw_result is not None


def test_diagnostics_are_aggregated_in_fixed_stage_order() -> None:
    result = TransferFunctionPreparationService().prepare(_common("1/0"))
    assert result.diagnostics == tuple(
        diagnostic
        for record in result.stage_records
        for diagnostic in record.diagnostics
    )
    assert result.diagnostics[-1].code.value == "workflow.raw_failed"


def test_diagnostic_limit_is_structured_and_preserves_valid_prefix() -> None:
    result = TransferFunctionPreparationService(
        TransferFunctionWorkflowLimits(max_aggregated_diagnostics=1)
    ).prepare(_common("1/0"))
    assert result.status is TransferFunctionPreparationStatus.PARTIAL
    assert result.parsed_input is not None
    assert result.raw_result is None
    assert len(result.diagnostics) == 1
    assert result.diagnostics[0].code.value == "workflow.limit_exceeded"


def test_repeated_preparation_is_deterministic() -> None:
    service = TransferFunctionPreparationService()
    request = _common("(s+1)/(s^2+3*s+2)")
    assert service.prepare(request) == service.prepare(request)


def test_internal_programming_errors_are_not_masked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def broken(*args: object, **kwargs: object) -> object:
        raise TypeError("programming bug")

    monkeypatch.setattr(service_module, "parse_request", broken)
    with pytest.raises(TypeError, match="programming bug"):
        TransferFunctionPreparationService().prepare(_common("1/(s+1)"))


def test_preparation_never_invokes_root_or_stability_analysis(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*args: object, **kwargs: object) -> object:
        raise AssertionError("downstream analysis must not run")

    monkeypatch.setattr(TransferFunctionRootAnalyzer, "analyze", forbidden)
    monkeypatch.setattr(
        TransferFunctionRootAnalyzer,
        "analyze_reduction",
        forbidden,
    )
    monkeypatch.setattr(
        TransferFunctionStabilityAnalyzer,
        "analyze",
        forbidden,
    )
    assert TransferFunctionPreparationService().prepare(
        _common("1/(s+1)")
    ).succeeded


def test_full_workflow_uses_preparation_exactly_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0
    original = TransferFunctionPreparationService.prepare

    def counted(
        self: TransferFunctionPreparationService,
        request: TransferFunctionWorkflowRequest,
    ) -> TransferFunctionPreparationResult:
        nonlocal calls
        calls += 1
        return original(self, request)

    monkeypatch.setattr(
        TransferFunctionPreparationService,
        "prepare",
        counted,
    )
    state = TransferFunctionWorkflowService().run(_common("1/(s+1)"))
    assert calls == 1
    assert state.reduced_value is not None
    assert state.root_analysis_result is not None
    assert state.stability_analysis_result is not None
