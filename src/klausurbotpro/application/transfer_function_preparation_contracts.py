"""Immutable contracts for shared transfer-function preparation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from klausurbotpro.application.transfer_function_workflow_contracts import (
    TransferFunctionWorkflowRequest,
)
from klausurbotpro.domain import (
    CommonTransferFunctionInput,
    Diagnostic,
    DiagnosticSeverity,
    RawTransferFunction,
    RawTransferFunctionCreationResult,
    ReducedTransferFunction,
    SeparatedTransferFunctionInput,
    TransferFunctionInput,
    TransferFunctionReductionResult,
)


class TransferFunctionPreparationStatus(StrEnum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    FAILED = "failed"


class TransferFunctionPreparationStage(StrEnum):
    PARSE = "parse"
    RAW_TRANSFER_FUNCTION = "raw_transfer_function"
    REDUCTION = "reduction"


PREPARATION_STAGE_ORDER = (
    TransferFunctionPreparationStage.PARSE,
    TransferFunctionPreparationStage.RAW_TRANSFER_FUNCTION,
    TransferFunctionPreparationStage.REDUCTION,
)


class TransferFunctionPreparationStageStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class TransferFunctionPreparationStageRecord:
    stage: TransferFunctionPreparationStage
    status: TransferFunctionPreparationStageStatus
    diagnostics: tuple[Diagnostic, ...] = ()

    def __post_init__(self) -> None:
        if type(self.stage) is not TransferFunctionPreparationStage:
            raise TypeError("stage must be TransferFunctionPreparationStage.")
        if type(self.status) is not TransferFunctionPreparationStageStatus:
            raise TypeError(
                "status must be TransferFunctionPreparationStageStatus."
            )
        if type(self.diagnostics) is not tuple or any(
            type(item) is not Diagnostic for item in self.diagnostics
        ):
            raise TypeError("diagnostics must be an exact Diagnostic tuple.")


@dataclass(frozen=True, slots=True, init=False)
class TransferFunctionPreparationResult:
    request: TransferFunctionWorkflowRequest
    status: TransferFunctionPreparationStatus
    parsed_input: TransferFunctionInput | None
    raw_result: RawTransferFunctionCreationResult | None
    reduction_result: TransferFunctionReductionResult | None
    stage_records: tuple[TransferFunctionPreparationStageRecord, ...]
    diagnostics: tuple[Diagnostic, ...]

    def __new__(
        cls,
        *args: object,
        **kwargs: object,
    ) -> TransferFunctionPreparationResult:
        raise TypeError("Preparation results are service-controlled.")

    @classmethod
    def _create(
        cls,
        *,
        request: TransferFunctionWorkflowRequest,
        status: TransferFunctionPreparationStatus,
        parsed_input: TransferFunctionInput | None,
        raw_result: RawTransferFunctionCreationResult | None,
        reduction_result: TransferFunctionReductionResult | None,
        stage_records: tuple[TransferFunctionPreparationStageRecord, ...],
        diagnostics: tuple[Diagnostic, ...],
    ) -> TransferFunctionPreparationResult:
        instance = object.__new__(cls)
        object.__setattr__(instance, "request", request)
        object.__setattr__(instance, "status", status)
        object.__setattr__(instance, "parsed_input", parsed_input)
        object.__setattr__(instance, "raw_result", raw_result)
        object.__setattr__(instance, "reduction_result", reduction_result)
        object.__setattr__(instance, "stage_records", stage_records)
        object.__setattr__(instance, "diagnostics", diagnostics)
        instance._validate_local()
        return instance

    def _validate_local(self) -> None:
        if type(self.request) is not TransferFunctionWorkflowRequest:
            raise TypeError("request has an invalid type.")
        if type(self.status) is not TransferFunctionPreparationStatus:
            raise TypeError("status has an invalid type.")
        if type(self.parsed_input) not in (
            CommonTransferFunctionInput,
            SeparatedTransferFunctionInput,
            type(None),
        ):
            raise TypeError("parsed_input has an invalid type.")
        if self.raw_result is not None and (
            type(self.raw_result) is not RawTransferFunctionCreationResult
        ):
            raise TypeError("raw_result has an invalid type.")
        if self.reduction_result is not None and (
            type(self.reduction_result) is not TransferFunctionReductionResult
        ):
            raise TypeError("reduction_result has an invalid type.")
        if (
            type(self.stage_records) is not tuple
            or any(
                type(item) is not TransferFunctionPreparationStageRecord
                for item in self.stage_records
            )
            or tuple(item.stage for item in self.stage_records)
            != PREPARATION_STAGE_ORDER
        ):
            raise ValueError("stage_records must use the fixed stage order.")
        if type(self.diagnostics) is not tuple or any(
            type(item) is not Diagnostic for item in self.diagnostics
        ):
            raise TypeError("diagnostics has an invalid type.")

    @property
    def raw_value(self) -> RawTransferFunction | None:
        return None if self.raw_result is None else self.raw_result.value

    @property
    def reduced_value(self) -> ReducedTransferFunction | None:
        return (
            None
            if self.reduction_result is None
            else self.reduction_result.reduced
        )

    @property
    def succeeded(self) -> bool:
        return self.status is TransferFunctionPreparationStatus.COMPLETE

    @property
    def has_errors(self) -> bool:
        return any(
            item.severity is DiagnosticSeverity.ERROR
            for item in self.diagnostics
        )


__all__ = [
    "PREPARATION_STAGE_ORDER",
    "TransferFunctionPreparationResult",
    "TransferFunctionPreparationStage",
    "TransferFunctionPreparationStageRecord",
    "TransferFunctionPreparationStageStatus",
    "TransferFunctionPreparationStatus",
]
