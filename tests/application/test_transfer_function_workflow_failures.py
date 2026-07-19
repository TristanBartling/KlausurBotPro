"""Partial-result, limit, and operation failure tests."""

from dataclasses import replace

import pytest

from klausurbotpro.application import (
    OverrideProvenance,
    RawTransferFunctionOverride,
    TransferFunctionWorkflowLimits,
    TransferFunctionWorkflowRequest,
    TransferFunctionWorkflowService,
    WorkflowDiagnosticCode,
    WorkflowInputForm,
    WorkflowOverrideOriginKind,
    WorkflowStage,
    WorkflowStageStatus,
)
from klausurbotpro.domain import (
    Diagnostic,
    DiagnosticCode,
    DiagnosticSeverity,
    ExactRationalValue,
    ParameterAssignment,
    ParameterSubstitutions,
    StabilityAnalysisLimits,
    TransferFunctionReductionLimits,
    TransferFunctionRootAnalyzer,
    TransferFunctionStabilityAnalyzer,
)


def _request(
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
    )


def test_reduction_failure_retains_raw_result() -> None:
    service = TransferFunctionWorkflowService(
        TransferFunctionWorkflowLimits(
            reduction=TransferFunctionReductionLimits(max_input_terms=1)
        )
    )
    state = service.run(_request("(s+1)/(s+2)"))

    assert state.parsed_input is not None
    assert state.raw_result is not None and state.raw_result.succeeded
    assert state.reduction_result is not None
    assert not state.reduction_result.succeeded
    assert state.stage_records[2].status is WorkflowStageStatus.FAILED
    assert all(
        record.status is WorkflowStageStatus.BLOCKED
        for record in state.stage_records[3:]
    )


def test_root_failure_retains_reduced_result() -> None:
    state = TransferFunctionWorkflowService().run(
        _request(
            "1/(T*s+1)",
            parameters=("T",),
            substitutions=ParameterSubstitutions(),
        )
    )

    assert state.reduction_result is not None
    assert state.reduction_result.succeeded
    assert state.root_analysis_result is not None
    assert not state.root_analysis_result.succeeded
    assert state.stage_records[3].status is WorkflowStageStatus.FAILED
    assert state.stage_records[4].status is WorkflowStageStatus.BLOCKED


def test_stability_failure_retains_root_result() -> None:
    service = TransferFunctionWorkflowService(
        TransferFunctionWorkflowLimits(
            stability_analysis=StabilityAnalysisLimits(max_poles=1)
        )
    )
    state = service.run(_request("1/(s^2+3*s+2)"))

    assert state.root_analysis_result is not None
    assert state.root_analysis_result.succeeded
    assert state.stability_analysis_result is not None
    assert not state.stability_analysis_result.succeeded
    assert state.stage_records[4].status is WorkflowStageStatus.FAILED


def test_invalid_substitution_update_preserves_existing_results() -> None:
    service = TransferFunctionWorkflowService()
    state = service.run(_request("1/(T*s+1)", parameters=("T",)))
    invalid = ParameterSubstitutions(
        (ParameterAssignment("X", ExactRationalValue(2)),)
    )

    rejected = service.update_substitutions(state, invalid)

    assert rejected.substitutions is state.substitutions
    assert rejected.root_analysis_result is state.root_analysis_result
    assert rejected.stability_analysis_result is state.stability_analysis_result
    assert WorkflowDiagnosticCode.WORKFLOW_INVALID_SUBSTITUTIONS.value in {
        entry.diagnostic.code.value
        for entry in rejected.aggregated_diagnostics
    }


def test_aggregated_diagnostic_limit_is_structured() -> None:
    service = TransferFunctionWorkflowService(
        TransferFunctionWorkflowLimits(max_aggregated_diagnostics=1)
    )
    state = service.run(_request("1/(T*s+1)", parameters=("T",)))

    assert len(state.aggregated_diagnostics) == 1
    assert state.aggregated_diagnostics[0].diagnostic.code.value == (
        WorkflowDiagnosticCode.WORKFLOW_LIMIT_EXCEEDED.value
    )
    failed = tuple(
        record.stage
        for record in state.stage_records
        if record.status is WorkflowStageStatus.FAILED
    )
    assert failed != (WorkflowStage.PARSE,)


def test_parse_diagnostic_overflow_marks_parse_only() -> None:
    state = TransferFunctionWorkflowService(
        TransferFunctionWorkflowLimits(max_aggregated_diagnostics=1)
    ).run(_request("open('x')"))

    assert len(state.aggregated_diagnostics) == 1
    assert state.stage_records[0].status is WorkflowStageStatus.FAILED
    assert all(
        record.status is WorkflowStageStatus.BLOCKED
        for record in state.stage_records[1:]
    )
    assert state.aggregated_diagnostics[0].diagnostic.code.value == (
        WorkflowDiagnosticCode.WORKFLOW_LIMIT_EXCEEDED.value
    )


def test_root_diagnostic_overflow_retains_parser_raw_and_reduction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = TransferFunctionRootAnalyzer.analyze_reduction

    def analyze_with_diagnostic(
        analyzer: TransferFunctionRootAnalyzer,
        *args: object,
        **kwargs: object,
    ) -> object:
        result = original(analyzer, *args, **kwargs)  # type: ignore[arg-type]
        return replace(
            result,
            diagnostics=(
                *result.diagnostics,
                Diagnostic(
                    DiagnosticSeverity.WARNING,
                    DiagnosticCode.ROOT_ANALYSIS_DEGREE_DROPPED,
                    "controlled root diagnostic",
                ),
            ),
        )

    monkeypatch.setattr(
        TransferFunctionRootAnalyzer,
        "analyze_reduction",
        analyze_with_diagnostic,
    )
    state = TransferFunctionWorkflowService(
        TransferFunctionWorkflowLimits(max_aggregated_diagnostics=1)
    ).run(_request("1/(s+1)"))

    assert state.parsed_input is not None
    assert state.raw_result is not None and state.raw_result.succeeded
    assert state.reduction_result is not None
    assert state.stage_records[2].status is WorkflowStageStatus.SUCCEEDED
    assert state.stage_records[3].status is WorkflowStageStatus.FAILED
    assert state.stage_records[4].status is WorkflowStageStatus.BLOCKED
    assert state.root_analysis_result is None
    assert len(state.aggregated_diagnostics) == 1


def test_stability_diagnostic_overflow_retains_root_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = TransferFunctionStabilityAnalyzer.analyze

    def analyze_with_diagnostic(
        analyzer: TransferFunctionStabilityAnalyzer,
        *args: object,
        **kwargs: object,
    ) -> object:
        result = original(analyzer, *args, **kwargs)  # type: ignore[arg-type]
        object.__setattr__(
            result,
            "diagnostics",
            (
                *result.diagnostics,
                Diagnostic(
                    DiagnosticSeverity.WARNING,
                    DiagnosticCode.STABILITY_ANALYSIS_NUMERIC_CONTRADICTION,
                    "controlled stability diagnostic",
                ),
            ),
        )
        return result

    monkeypatch.setattr(
        TransferFunctionStabilityAnalyzer,
        "analyze",
        analyze_with_diagnostic,
    )
    state = TransferFunctionWorkflowService(
        TransferFunctionWorkflowLimits(max_aggregated_diagnostics=1)
    ).run(_request("1/(s+1)"))

    assert state.parsed_input is not None
    assert state.raw_result is not None
    assert state.reduction_result is not None
    assert state.root_analysis_result is not None
    assert state.stage_records[3].status is WorkflowStageStatus.SUCCEEDED
    assert state.stage_records[4].status is WorkflowStageStatus.FAILED
    assert state.stability_analysis_result is None
    assert len(state.aggregated_diagnostics) == 1


def test_invalid_override_overflow_preserves_active_mathematical_values() -> None:
    service = TransferFunctionWorkflowService(
        TransferFunctionWorkflowLimits(max_aggregated_diagnostics=1)
    )
    state = service.run(_request("1/(s+1)"))
    assert state.raw_value is not None
    rejected = service.apply_override(
        state,
        RawTransferFunctionOverride(
            state.raw_value,
            OverrideProvenance(
                WorkflowOverrideOriginKind.TEST,
                "wrong sequence",
                99,
                WorkflowStage.RAW_TRANSFER_FUNCTION,
            ),
        ),
    )

    assert rejected.parsed_input is state.parsed_input
    assert rejected.raw_result is state.raw_result
    assert rejected.reduction_result is state.reduction_result
    assert rejected.root_analysis_result is state.root_analysis_result
    assert rejected.stability_analysis_result is state.stability_analysis_result
    assert all(
        record.status is WorkflowStageStatus.SUCCEEDED
        for record in rejected.stage_records
    )
    assert len(rejected.aggregated_diagnostics) == 1
    assert rejected.aggregated_diagnostics[0].diagnostic.code.value == (
        WorkflowDiagnosticCode.WORKFLOW_LIMIT_EXCEEDED.value
    )


def test_unexpected_resource_error_is_structured_with_partial_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def exhaust(*args: object, **kwargs: object) -> None:
        raise MemoryError

    monkeypatch.setattr(
        (
            "klausurbotpro.application.transfer_function_workflow_service."
            "TransferFunctionReducer.reduce"
        ),
        exhaust,
    )
    state = TransferFunctionWorkflowService().run(_request("1/(s+1)"))

    assert state.parsed_input is not None
    assert state.raw_result is not None and state.raw_result.succeeded
    assert state.stage_records[2].status is WorkflowStageStatus.FAILED
    assert WorkflowDiagnosticCode.WORKFLOW_RESOURCE_LIMIT_EXCEEDED.value in {
        entry.diagnostic.code.value
        for entry in state.aggregated_diagnostics
    }
