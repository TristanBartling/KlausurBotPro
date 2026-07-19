"""Public contracts for the frequency-domain Application workflow."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

import klausurbotpro.application as application
from klausurbotpro.application import (
    FrequencyDomainWorkflowLimits,
    FrequencyDomainWorkflowMode,
    FrequencyDomainWorkflowResult,
    FrequencyDomainWorkflowStage,
    FrequencyDomainWorkflowStageRecord,
    FrequencyDomainWorkflowStageStatus,
    FrequencyDomainWorkflowStatus,
    FrequencyPhasePresentation,
)


def test_required_frequency_workflow_api_is_public() -> None:
    names = (
        "FrequencyDomainWorkflowDiagnosticCode",
        "FrequencyDomainWorkflowLimits",
        "FrequencyDomainWorkflowMode",
        "FrequencyDomainWorkflowRequest",
        "FrequencyDomainWorkflowResult",
        "FrequencyDomainWorkflowService",
        "FrequencyDomainWorkflowStage",
        "FrequencyDomainWorkflowStageRecord",
        "FrequencyDomainWorkflowStageStatus",
        "FrequencyDomainWorkflowStatus",
        "FrequencyPhasePresentation",
    )
    assert all(name in application.__all__ for name in names)


def test_modes_presentations_stages_and_statuses_are_explicit_enums() -> None:
    assert tuple(FrequencyDomainWorkflowMode) == (
        FrequencyDomainWorkflowMode.SINGLE_POINT,
        FrequencyDomainWorkflowMode.BODE,
    )
    assert tuple(FrequencyPhasePresentation) == (
        FrequencyPhasePresentation.PRINCIPAL_ONLY,
        FrequencyPhasePresentation.PRINCIPAL_AND_UNWRAPPED,
    )
    assert tuple(FrequencyDomainWorkflowStage) == (
        FrequencyDomainWorkflowStage.PREPARATION,
        FrequencyDomainWorkflowStage.SINGLE_POINT_RESPONSE,
        FrequencyDomainWorkflowStage.LOG_FREQUENCY_GRID,
        FrequencyDomainWorkflowStage.BODE_DATA,
        FrequencyDomainWorkflowStage.PHASE_UNWRAP,
    )
    assert set(FrequencyDomainWorkflowStageStatus) == {
        FrequencyDomainWorkflowStageStatus.SUCCEEDED,
        FrequencyDomainWorkflowStageStatus.FAILED,
        FrequencyDomainWorkflowStageStatus.BLOCKED,
        FrequencyDomainWorkflowStageStatus.NOT_APPLICABLE,
    }
    assert set(FrequencyDomainWorkflowStatus) == {
        FrequencyDomainWorkflowStatus.COMPLETE,
        FrequencyDomainWorkflowStatus.PARTIAL,
        FrequencyDomainWorkflowStatus.FAILED,
    }


def test_limits_require_exact_nested_types_and_positive_real_int() -> None:
    with pytest.raises(TypeError):
        FrequencyDomainWorkflowLimits(preparation=object())  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        FrequencyDomainWorkflowLimits(frequency_response=object())  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        FrequencyDomainWorkflowLimits(grid=object())  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        FrequencyDomainWorkflowLimits(bode=object())  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        FrequencyDomainWorkflowLimits(phase_unwrap=object())  # type: ignore[arg-type]
    for invalid in (0, -1, True):
        with pytest.raises(ValueError):
            FrequencyDomainWorkflowLimits(
                max_aggregated_diagnostics=invalid
            )


def test_stage_records_are_frozen_and_unavailable_records_are_empty() -> None:
    record = FrequencyDomainWorkflowStageRecord(
        FrequencyDomainWorkflowStage.BODE_DATA,
        FrequencyDomainWorkflowStageStatus.NOT_APPLICABLE,
    )
    with pytest.raises(FrozenInstanceError):
        record.status = FrequencyDomainWorkflowStageStatus.SUCCEEDED  # type: ignore[misc]
    with pytest.raises(TypeError):
        FrequencyDomainWorkflowStageRecord(
            FrequencyDomainWorkflowStage.BODE_DATA,
            FrequencyDomainWorkflowStageStatus.BLOCKED,
            (object(),),  # type: ignore[arg-type]
        )


def test_result_is_service_controlled() -> None:
    with pytest.raises(TypeError):
        FrequencyDomainWorkflowResult()


def test_frequency_workflow_core_has_no_forbidden_dependencies() -> None:
    directory = Path(application.__file__).parent
    for name in (
        "frequency_domain_workflow_contracts.py",
        "frequency_domain_workflow_service.py",
        "_frequency_domain_workflow_validation.py",
        "_frequency_domain_workflow_diagnostics.py",
    ):
        source = (directory / name).read_text(encoding="utf-8")
        assert all(
            forbidden not in source
            for forbidden in (
                "klausurbotpro.ui",
                "solution_report",
                "matplotlib",
                "PySide6",
                "TransferFunctionRootAnalyzer",
                "TransferFunctionStabilityAnalyzer",
            )
        )
