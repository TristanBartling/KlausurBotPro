"""Public contracts for shared transfer-function preparation."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

import klausurbotpro.application as application
from klausurbotpro.application import (
    TransferFunctionPreparationResult,
    TransferFunctionPreparationService,
    TransferFunctionPreparationStage,
    TransferFunctionPreparationStageRecord,
    TransferFunctionPreparationStageStatus,
    TransferFunctionPreparationStatus,
)


def test_required_preparation_api_is_publicly_exported() -> None:
    for name in (
        "TransferFunctionPreparationStatus",
        "TransferFunctionPreparationStage",
        "TransferFunctionPreparationStageStatus",
        "TransferFunctionPreparationStageRecord",
        "TransferFunctionPreparationResult",
        "TransferFunctionPreparationService",
    ):
        assert name in application.__all__
        assert getattr(application, name) is not None


def test_stage_enums_are_exact_and_complete() -> None:
    assert tuple(TransferFunctionPreparationStage) == (
        TransferFunctionPreparationStage.PARSE,
        TransferFunctionPreparationStage.RAW_TRANSFER_FUNCTION,
        TransferFunctionPreparationStage.REDUCTION,
    )
    assert set(TransferFunctionPreparationStageStatus) == {
        TransferFunctionPreparationStageStatus.SUCCEEDED,
        TransferFunctionPreparationStageStatus.FAILED,
        TransferFunctionPreparationStageStatus.BLOCKED,
    }
    assert set(TransferFunctionPreparationStatus) == {
        TransferFunctionPreparationStatus.COMPLETE,
        TransferFunctionPreparationStatus.PARTIAL,
        TransferFunctionPreparationStatus.FAILED,
    }


def test_stage_records_are_frozen_and_strictly_typed() -> None:
    record = TransferFunctionPreparationStageRecord(
        TransferFunctionPreparationStage.PARSE,
        TransferFunctionPreparationStageStatus.BLOCKED,
    )
    with pytest.raises(FrozenInstanceError):
        record.status = (  # type: ignore[misc]
            TransferFunctionPreparationStageStatus.SUCCEEDED
        )
    with pytest.raises(TypeError):
        TransferFunctionPreparationStageRecord(
            "parse",  # type: ignore[arg-type]
            TransferFunctionPreparationStageStatus.SUCCEEDED,
        )


def test_result_direct_construction_is_locked() -> None:
    with pytest.raises(TypeError):
        TransferFunctionPreparationResult()


def test_service_and_result_reject_wrong_top_level_types() -> None:
    with pytest.raises(TypeError):
        TransferFunctionPreparationService(object())  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        TransferFunctionPreparationService().prepare(object())  # type: ignore[arg-type]


def test_preparation_service_has_no_downstream_or_presentation_dependencies() -> None:
    application_directory = Path(application.__file__).parent
    for name in (
        "transfer_function_preparation_service.py",
        "transfer_function_preparation_contracts.py",
        "_transfer_function_preparation_validation.py",
        "_transfer_function_preparation_steps.py",
    ):
        source = (application_directory / name).read_text(encoding="utf-8")
        assert all(
            forbidden not in source
            for forbidden in (
                "TransferFunctionRootAnalyzer",
                "TransferFunctionStabilityAnalyzer",
                "klausurbotpro.ui",
                "solution_report",
                "matplotlib",
                "PySide6",
            )
        )
