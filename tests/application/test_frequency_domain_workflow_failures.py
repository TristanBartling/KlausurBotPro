"""Failure, resource, and request-boundary tests."""

from __future__ import annotations

from typing import cast

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
    TransferFunctionPreparationService,
    TransferFunctionPreparationStatus,
    TransferFunctionWorkflowLimits,
    TransferFunctionWorkflowRequest,
    WorkflowInputForm,
)
from klausurbotpro.domain import (
    BodeDataLimits,
    BodePhaseUnwrapAnalyzer,
    BodePhaseUnwrapLimits,
    ExactRationalValue,
    LogFrequencyGridGenerator,
    LogFrequencyGridRequest,
    TransferFunctionBodeDataAnalyzer,
    TransferFunctionFrequencyResponseAnalyzer,
    TransferFunctionReductionLimits,
)
from klausurbotpro.parsing import ParserLimits


def _preparation(expression: str = "1/(s+1)") -> TransferFunctionWorkflowRequest:
    return TransferFunctionWorkflowRequest(
        WorkflowInputForm.COMMON,
        common_expression_text=expression,
        field="frequency",
    )


def _grid() -> LogFrequencyGridRequest:
    return LogFrequencyGridRequest(
        ExactRationalValue(1, 10),
        ExactRationalValue(10),
        2,
    )


def _single(expression: str = "1/(s+1)") -> FrequencyDomainWorkflowRequest:
    return FrequencyDomainWorkflowRequest(
        _preparation(expression),
        FrequencyDomainWorkflowMode.SINGLE_POINT,
        single_angular_frequency=ExactRationalValue(1),
    )


def _bode(
    expression: str = "1/(s+1)",
    *,
    grid: LogFrequencyGridRequest | None = None,
    unwrap: bool = False,
) -> FrequencyDomainWorkflowRequest:
    return FrequencyDomainWorkflowRequest(
        _preparation(expression),
        FrequencyDomainWorkflowMode.BODE,
        grid_request=_grid() if grid is None else grid,
        phase_presentation=(
            FrequencyPhasePresentation.PRINCIPAL_AND_UNWRAPPED
            if unwrap
            else FrequencyPhasePresentation.PRINCIPAL_ONLY
        ),
    )


def _assert_value_free_invalid(result: FrequencyDomainWorkflowResult) -> None:
    assert result.status is FrequencyDomainWorkflowStatus.FAILED
    assert result.request is None
    assert result.stage_records == ()
    assert result.preparation_result is None
    assert result.single_point_result is None
    assert result.grid_result is None
    assert result.bode_data_result is None
    assert result.phase_unwrap_result is None
    assert len(result.diagnostics) == 1
    diagnostic = result.diagnostics[0]
    assert cast(object, diagnostic.code) is (
        FrequencyDomainWorkflowDiagnosticCode.INVALID_REQUEST
    )
    assert diagnostic.field is None
    assert diagnostic.technical_details


@pytest.mark.parametrize(
    "workflow_request",
    [
        FrequencyDomainWorkflowRequest(
            _preparation(),
            FrequencyDomainWorkflowMode.SINGLE_POINT,
        ),
        FrequencyDomainWorkflowRequest(
            _preparation(),
            FrequencyDomainWorkflowMode.SINGLE_POINT,
            single_angular_frequency=ExactRationalValue(-1),
        ),
        FrequencyDomainWorkflowRequest(
            _preparation(),
            FrequencyDomainWorkflowMode.SINGLE_POINT,
            single_angular_frequency=ExactRationalValue(1),
            grid_request=_grid(),
        ),
        FrequencyDomainWorkflowRequest(
            _preparation(),
            FrequencyDomainWorkflowMode.SINGLE_POINT,
            single_angular_frequency=ExactRationalValue(1),
            phase_presentation=(
                FrequencyPhasePresentation.PRINCIPAL_AND_UNWRAPPED
            ),
        ),
        FrequencyDomainWorkflowRequest(
            _preparation(),
            FrequencyDomainWorkflowMode.BODE,
        ),
        FrequencyDomainWorkflowRequest(
            _preparation(),
            FrequencyDomainWorkflowMode.BODE,
            single_angular_frequency=ExactRationalValue(1),
            grid_request=_grid(),
        ),
    ],
)
def test_invalid_mode_combinations_return_value_free_failure(
    workflow_request: FrequencyDomainWorkflowRequest,
) -> None:
    result = FrequencyDomainWorkflowService().run(workflow_request)
    _assert_value_free_invalid(result)


def test_wrong_top_level_request_type_raises_type_error() -> None:
    with pytest.raises(TypeError):
        FrequencyDomainWorkflowService().run(object())  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("workflow_request", "target", "field", "value"),
    [
        (_single(), "frequency", "numerator", True),
        (
            _bode(),
            "grid",
            "explicit_frequencies",
            [ExactRationalValue(1)],
        ),
    ],
)
def test_structurally_manipulated_nested_request_is_value_free(
    workflow_request: FrequencyDomainWorkflowRequest,
    target: str,
    field: str,
    value: object,
) -> None:
    nested = (
        workflow_request.single_angular_frequency
        if target == "frequency"
        else workflow_request.grid_request
    )
    assert nested is not None
    object.__setattr__(nested, field, value)

    result = FrequencyDomainWorkflowService().run(workflow_request)

    _assert_value_free_invalid(result)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("input_form", "common"),
        ("variable_name", "__unsafe__"),
        ("common_expression_text", 7),
        ("allowed_parameter_names", ["K"]),
        ("substitutions", object()),
        ("field", 42),
    ],
)
def test_manipulated_preparation_request_is_value_free(
    field: str,
    value: object,
) -> None:
    request = _single()
    object.__setattr__(request.preparation_request, field, value)

    _assert_value_free_invalid(FrequencyDomainWorkflowService().run(request))


def test_preparation_request_is_validated_against_active_limits() -> None:
    preparation = TransferFunctionWorkflowRequest(
        WorkflowInputForm.COMMON,
        common_expression_text="K/(T*s+1)",
        allowed_parameter_names=("K", "T"),
    )
    request = FrequencyDomainWorkflowRequest(
        preparation,
        FrequencyDomainWorkflowMode.SINGLE_POINT,
        single_angular_frequency=ExactRationalValue(1),
    )
    limits = FrequencyDomainWorkflowLimits(
        preparation=TransferFunctionWorkflowLimits(
            parser=ParserLimits(max_symbols=2)
        )
    )

    _assert_value_free_invalid(
        FrequencyDomainWorkflowService(limits).run(request)
    )


@pytest.mark.parametrize(
    ("expression", "expected_status", "retains_parsed_input"),
    [
        (
            "open('x')",
            FrequencyDomainWorkflowStatus.FAILED,
            False,
        ),
        (
            "1/0",
            FrequencyDomainWorkflowStatus.PARTIAL,
            True,
        ),
    ],
)
def test_preparation_failures_block_only_requested_followers(
    expression: str,
    expected_status: FrequencyDomainWorkflowStatus,
    retains_parsed_input: bool,
) -> None:
    result = FrequencyDomainWorkflowService().run(_single(expression))
    assert result.request is not None
    assert result.preparation_result is not None
    assert result.status is expected_status
    assert result.stage_records[0].status is (
        FrequencyDomainWorkflowStageStatus.FAILED
    )
    assert result.stage_records[1].status is (
        FrequencyDomainWorkflowStageStatus.BLOCKED
    )
    assert all(
        item.status is FrequencyDomainWorkflowStageStatus.NOT_APPLICABLE
        for item in result.stage_records[2:]
    )
    if retains_parsed_input:
        assert result.preparation_result.status is (
            TransferFunctionPreparationStatus.PARTIAL
        )
        assert result.preparation_result.parsed_input is not None
        assert result.preparation_result.raw_result is not None
        assert not result.preparation_result.raw_result.succeeded
    else:
        assert result.preparation_result.status is (
            TransferFunctionPreparationStatus.FAILED
        )
        assert result.preparation_result.parsed_input is None


def test_preparation_reduction_failure_is_partial() -> None:
    limits = FrequencyDomainWorkflowLimits(
        preparation=TransferFunctionWorkflowLimits(
            reduction=TransferFunctionReductionLimits(max_input_terms=1)
        )
    )
    result = FrequencyDomainWorkflowService(limits).run(
        _single("(s+1)/(s+2)")
    )
    assert result.status is FrequencyDomainWorkflowStatus.PARTIAL
    assert result.preparation_result is not None
    assert result.request is not None
    assert result.preparation_result.request is result.request.preparation_request
    assert result.preparation_result.raw_result is not None
    assert result.stage_records[0].status is (
        FrequencyDomainWorkflowStageStatus.FAILED
    )


def test_grid_bode_and_unwrap_failures_retain_predecessors() -> None:
    invalid_grid = LogFrequencyGridRequest(
        ExactRationalValue(0),
        ExactRationalValue(10),
        2,
    )
    grid_failed = FrequencyDomainWorkflowService().run(
        _bode(grid=invalid_grid)
    )
    assert grid_failed.status is FrequencyDomainWorkflowStatus.PARTIAL
    assert grid_failed.request is not None
    assert grid_failed.preparation_result is not None
    assert grid_failed.preparation_result.succeeded
    assert grid_failed.grid_result is not None
    assert grid_failed.stage_records[2].status is (
        FrequencyDomainWorkflowStageStatus.FAILED
    )

    bode_failed = FrequencyDomainWorkflowService(
        FrequencyDomainWorkflowLimits(
            bode=BodeDataLimits(max_grid_points=1)
        )
    ).run(_bode())
    assert bode_failed.status is FrequencyDomainWorkflowStatus.PARTIAL
    assert bode_failed.grid_result is not None
    assert bode_failed.bode_data_result is not None
    assert bode_failed.stage_records[3].status is (
        FrequencyDomainWorkflowStageStatus.FAILED
    )

    unwrap_failed = FrequencyDomainWorkflowService(
        FrequencyDomainWorkflowLimits(
            phase_unwrap=BodePhaseUnwrapLimits(max_points=1)
        )
    ).run(_bode(unwrap=True))
    assert unwrap_failed.status is FrequencyDomainWorkflowStatus.PARTIAL
    assert unwrap_failed.bode_data_result is not None
    assert unwrap_failed.phase_unwrap_result is not None
    assert unwrap_failed.stage_records[4].status is (
        FrequencyDomainWorkflowStageStatus.FAILED
    )


@pytest.mark.parametrize(
    ("target", "method", "workflow_request", "stage_index"),
    [
        (
            TransferFunctionPreparationService,
            "prepare",
            _single(),
            0,
        ),
        (
            TransferFunctionFrequencyResponseAnalyzer,
            "analyze",
            _single(),
            1,
        ),
        (
            LogFrequencyGridGenerator,
            "generate",
            _bode(),
            2,
        ),
        (
            TransferFunctionBodeDataAnalyzer,
            "analyze",
            _bode(),
            3,
        ),
        (
            BodePhaseUnwrapAnalyzer,
            "analyze",
            _bode(unwrap=True),
            4,
        ),
    ],
)
@pytest.mark.parametrize("error_type", [MemoryError, RecursionError, OverflowError])
def test_resource_errors_are_structured_at_each_application_boundary(
    target: type,
    method: str,
    workflow_request: FrequencyDomainWorkflowRequest,
    stage_index: int,
    error_type: type[BaseException],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def exhaust(*args: object, **kwargs: object) -> object:
        raise error_type

    monkeypatch.setattr(target, method, exhaust)
    result = FrequencyDomainWorkflowService().run(workflow_request)
    assert result.stage_records[stage_index].status is (
        FrequencyDomainWorkflowStageStatus.FAILED
    )
    assert result.stage_records[stage_index].diagnostics[-1].code.value == (
        FrequencyDomainWorkflowDiagnosticCode.RESOURCE_LIMIT_EXCEEDED.value
    )


def test_diagnostic_limit_replaces_first_overflowing_stage() -> None:
    result = FrequencyDomainWorkflowService(
        FrequencyDomainWorkflowLimits(max_aggregated_diagnostics=1)
    ).run(_bode(grid=LogFrequencyGridRequest(
        ExactRationalValue(0),
        ExactRationalValue(10),
        2,
    )))
    assert result.status is FrequencyDomainWorkflowStatus.PARTIAL
    assert len(result.diagnostics) == 1
    assert result.diagnostics[0].code.value == (
        FrequencyDomainWorkflowDiagnosticCode.LIMIT_EXCEEDED.value
    )
    assert result.grid_result is None


def test_internal_programming_errors_are_not_masked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def broken(*args: object, **kwargs: object) -> object:
        raise TypeError("programming bug")

    monkeypatch.setattr(
        TransferFunctionPreparationService,
        "prepare",
        broken,
    )
    with pytest.raises(TypeError, match="programming bug"):
        FrequencyDomainWorkflowService().run(_single())
