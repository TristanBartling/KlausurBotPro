"""Acceptance tests for frequency-domain workflow orchestration."""

from __future__ import annotations

import pytest

import klausurbotpro.domain._frequency_response_evaluator as evaluator_module
from klausurbotpro.application import (
    FrequencyDomainWorkflowMode,
    FrequencyDomainWorkflowRequest,
    FrequencyDomainWorkflowService,
    FrequencyDomainWorkflowStageStatus,
    FrequencyDomainWorkflowStatus,
    FrequencyPhasePresentation,
    TransferFunctionPreparationService,
    TransferFunctionWorkflowRequest,
    WorkflowInputForm,
)
from klausurbotpro.domain import (
    BodeDataStatus,
    BodePhaseUnwrapAnalyzer,
    BodePhaseUnwrapStatus,
    ExactRationalValue,
    FrequencyResponsePointStatus,
    LogFrequencyGridGenerator,
    LogFrequencyGridRequest,
    ParameterAssignment,
    ParameterSubstitutions,
    TransferFunctionBodeDataAnalyzer,
    TransferFunctionFrequencyResponseAnalyzer,
    TransferFunctionRootAnalyzer,
    TransferFunctionStabilityAnalyzer,
)
from klausurbotpro.domain._frequency_response_numeric import (
    FrequencyResponseNumericError,
)


def _preparation(
    expression: str = "1/(s+1)",
    *,
    parameters: tuple[str, ...] = (),
    substitutions: ParameterSubstitutions | None = None,
) -> TransferFunctionWorkflowRequest:
    return TransferFunctionWorkflowRequest(
        WorkflowInputForm.COMMON,
        common_expression_text=expression,
        allowed_parameter_names=parameters,
        substitutions=substitutions,
        field="frequency",
    )


def _grid(
    *,
    explicit: tuple[ExactRationalValue, ...] = (),
) -> LogFrequencyGridRequest:
    return LogFrequencyGridRequest(
        ExactRationalValue(1, 10),
        ExactRationalValue(10),
        2,
        explicit,
    )


def _single(
    expression: str = "1/(s+1)",
    omega: ExactRationalValue | None = None,
    *,
    parameters: tuple[str, ...] = (),
    substitutions: ParameterSubstitutions | None = None,
) -> FrequencyDomainWorkflowRequest:
    return FrequencyDomainWorkflowRequest(
        _preparation(
            expression,
            parameters=parameters,
            substitutions=substitutions,
        ),
        FrequencyDomainWorkflowMode.SINGLE_POINT,
        single_angular_frequency=(
            ExactRationalValue(0) if omega is None else omega
        ),
    )


def _bode(
    expression: str = "1/(s+1)",
    *,
    grid: LogFrequencyGridRequest | None = None,
    presentation: FrequencyPhasePresentation = (
        FrequencyPhasePresentation.PRINCIPAL_ONLY
    ),
    parameters: tuple[str, ...] = (),
) -> FrequencyDomainWorkflowRequest:
    return FrequencyDomainWorkflowRequest(
        _preparation(expression, parameters=parameters),
        FrequencyDomainWorkflowMode.BODE,
        grid_request=_grid() if grid is None else grid,
        phase_presentation=presentation,
    )


def test_single_point_pt1_at_zero_and_positive_rational_frequency() -> None:
    request = _single()
    zero = FrequencyDomainWorkflowService().run(request)
    positive = FrequencyDomainWorkflowService().run(
        _single(omega=ExactRationalValue(3, 2))
    )
    assert zero.status is FrequencyDomainWorkflowStatus.COMPLETE
    assert zero.request is request
    assert zero.preparation_result is not None
    assert zero.preparation_result.request is request.preparation_request
    assert zero.single_point_result is not None
    assert zero.single_point_result.points[0].omega == ExactRationalValue(0)
    assert positive.single_point_result is not None
    assert positive.single_point_result.points[0].omega == ExactRationalValue(
        3, 2
    )
    assert tuple(item.status for item in zero.stage_records) == (
        FrequencyDomainWorkflowStageStatus.SUCCEEDED,
        FrequencyDomainWorkflowStageStatus.SUCCEEDED,
        FrequencyDomainWorkflowStageStatus.NOT_APPLICABLE,
        FrequencyDomainWorkflowStageStatus.NOT_APPLICABLE,
        FrequencyDomainWorkflowStageStatus.NOT_APPLICABLE,
    )


def test_single_point_uses_exact_parameter_substitutions() -> None:
    substitutions = ParameterSubstitutions(
        (ParameterAssignment("T", ExactRationalValue(2)),)
    )
    result = FrequencyDomainWorkflowService().run(
        _single(
            "1/(T*s+1)",
            ExactRationalValue(1),
            parameters=("T",),
            substitutions=substitutions,
        )
    )
    assert result.status is FrequencyDomainWorkflowStatus.COMPLETE
    assert result.substitutions is substitutions
    assert result.single_point_result is not None
    assert result.single_point_result.substitutions == substitutions


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("1/s", FrequencyResponsePointStatus.SINGULAR),
        (
            "1/(T*s+1)",
            FrequencyResponsePointStatus.SYMBOLIC_UNDETERMINED,
        ),
    ],
)
def test_single_point_domain_outcomes_remain_application_complete(
    expression: str,
    expected: FrequencyResponsePointStatus,
) -> None:
    parameters = ("T",) if "T" in expression else ()
    result = FrequencyDomainWorkflowService().run(
        _single(
            expression,
            ExactRationalValue(0 if expected is FrequencyResponsePointStatus.SINGULAR else 1),
            parameters=parameters,
        )
    )
    assert result.status is FrequencyDomainWorkflowStatus.COMPLETE
    assert result.single_point_result is not None
    assert result.single_point_result.points[0].status is expected


def test_numeric_undetermined_single_point_remains_complete(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(*args: object, **kwargs: object) -> object:
        raise FrequencyResponseNumericError

    monkeypatch.setattr(evaluator_module, "numerical_frequency_response", fail)
    result = FrequencyDomainWorkflowService().run(
        _single(omega=ExactRationalValue(1))
    )
    assert result.status is FrequencyDomainWorkflowStatus.COMPLETE
    assert result.single_point_result is not None
    assert result.single_point_result.points[0].status is (
        FrequencyResponsePointStatus.NUMERIC_UNDETERMINED
    )


@pytest.mark.parametrize(
    "expression",
    [
        "1/(s+1)",
        "1/s",
        "s",
        "-1",
        "1/(s^2+s+1)",
    ],
)
def test_bode_representative_systems_are_orchestrated(expression: str) -> None:
    result = FrequencyDomainWorkflowService().run(_bode(expression))
    assert result.status is FrequencyDomainWorkflowStatus.COMPLETE
    assert result.grid_result is not None
    assert result.bode_data_result is not None
    assert result.bode_data_result.succeeded
    assert result.single_point_result is None


def test_bode_preserves_explicit_frequency_and_splits_singularity() -> None:
    explicit = ExactRationalValue(2)
    result = FrequencyDomainWorkflowService().run(
        _bode("1/(s^2+4)", grid=_grid(explicit=(explicit,)))
    )
    assert result.status is FrequencyDomainWorkflowStatus.COMPLETE
    assert result.grid_result is not None
    assert any(
        point.evaluation_frequency == explicit
        for point in result.grid_result.points
    )
    assert result.bode_data_result is not None
    assert any(
        point.frequency_response_point.status
        is FrequencyResponsePointStatus.SINGULAR
        for point in result.bode_data_result.points
    )
    assert len(result.bode_data_result.magnitude_segments) == 2


def test_zero_and_symbolic_bode_statuses_remain_complete() -> None:
    zero = FrequencyDomainWorkflowService().run(_bode("0/(s+1)"))
    symbolic = FrequencyDomainWorkflowService().run(
        _bode("K/(s+1)", parameters=("K",))
    )
    assert zero.status is FrequencyDomainWorkflowStatus.COMPLETE
    assert zero.bode_data_result is not None
    assert zero.bode_data_result.status is BodeDataStatus.NO_PLOTTABLE_DATA
    assert symbolic.status is FrequencyDomainWorkflowStatus.COMPLETE
    assert symbolic.bode_data_result is not None
    assert symbolic.bode_data_result.status is (
        BodeDataStatus.SYMBOLIC_UNDETERMINED
    )


def test_optional_phase_unwrap_is_mode_controlled() -> None:
    principal = FrequencyDomainWorkflowService().run(_bode())
    unwrapped = FrequencyDomainWorkflowService().run(
        _bode(
            presentation=(
                FrequencyPhasePresentation.PRINCIPAL_AND_UNWRAPPED
            )
        )
    )
    assert principal.phase_unwrap_result is None
    assert principal.stage_records[4].status is (
        FrequencyDomainWorkflowStageStatus.NOT_APPLICABLE
    )
    assert unwrapped.phase_unwrap_result is not None
    assert unwrapped.phase_unwrap_result.succeeded


def test_diagnostic_ownership_avoids_bode_and_unwrap_duplicates() -> None:
    result = FrequencyDomainWorkflowService().run(
        _bode(
            "K/(s+1)",
            parameters=("K",),
            presentation=(
                FrequencyPhasePresentation.PRINCIPAL_AND_UNWRAPPED
            ),
        )
    )
    assert result.bode_data_result is not None
    assert result.phase_unwrap_result is not None
    assert result.diagnostics == tuple(
        diagnostic
        for record in result.stage_records
        for diagnostic in record.diagnostics
    )
    assert result.stage_records[3].diagnostics == (
        result.bode_data_result.diagnostics
    )
    assert result.stage_records[4].diagnostics == (
        result.phase_unwrap_result.diagnostics[
            len(result.bode_data_result.diagnostics) :
        ]
    )
    assert result.preparation_result is not None
    assert len(result.diagnostics) == (
        len(result.preparation_result.diagnostics)
        + len(result.phase_unwrap_result.diagnostics)
    )


def test_no_phase_data_from_zero_response_remains_complete() -> None:
    result = FrequencyDomainWorkflowService().run(
        _bode(
            "0/(s+1)",
            presentation=(
                FrequencyPhasePresentation.PRINCIPAL_AND_UNWRAPPED
            ),
        )
    )
    assert result.status is FrequencyDomainWorkflowStatus.COMPLETE
    assert result.phase_unwrap_result is not None
    assert result.phase_unwrap_result.status is BodePhaseUnwrapStatus.NO_PHASE_DATA


def test_orchestration_call_counts_and_absent_downstream_analysis(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    counts = {"prepare": 0, "response": 0, "grid": 0, "bode": 0, "unwrap": 0}

    def count(cls: type, name: str) -> None:
        original = cls.__dict__[name]

        def counted(self: object, *args: object, **kwargs: object) -> object:
            counts[
                {
                    TransferFunctionPreparationService: "prepare",
                    TransferFunctionFrequencyResponseAnalyzer: "response",
                    LogFrequencyGridGenerator: "grid",
                    TransferFunctionBodeDataAnalyzer: "bode",
                    BodePhaseUnwrapAnalyzer: "unwrap",
                }[cls]
            ] += 1
            return original(self, *args, **kwargs)

        monkeypatch.setattr(cls, name, counted)

    count(TransferFunctionPreparationService, "prepare")
    count(TransferFunctionFrequencyResponseAnalyzer, "analyze")
    count(LogFrequencyGridGenerator, "generate")
    count(TransferFunctionBodeDataAnalyzer, "analyze")
    count(BodePhaseUnwrapAnalyzer, "analyze")

    def forbidden(*args: object, **kwargs: object) -> object:
        raise AssertionError("root and stability analysis are forbidden")

    monkeypatch.setattr(TransferFunctionRootAnalyzer, "analyze", forbidden)
    monkeypatch.setattr(TransferFunctionStabilityAnalyzer, "analyze", forbidden)

    single = FrequencyDomainWorkflowService().run(_single())
    assert single.succeeded
    assert counts == {
        "prepare": 1,
        "response": 1,
        "grid": 0,
        "bode": 0,
        "unwrap": 0,
    }

    counts.update({name: 0 for name in counts})
    principal = FrequencyDomainWorkflowService().run(_bode())
    assert principal.succeeded
    assert counts == {
        "prepare": 1,
        "response": 1,
        "grid": 1,
        "bode": 1,
        "unwrap": 0,
    }

    counts.update({name: 0 for name in counts})
    bode = FrequencyDomainWorkflowService().run(
        _bode(
            presentation=(
                FrequencyPhasePresentation.PRINCIPAL_AND_UNWRAPPED
            )
        )
    )
    assert bode.succeeded
    assert counts == {
        "prepare": 1,
        "response": 1,
        "grid": 1,
        "bode": 1,
        "unwrap": 1,
    }
