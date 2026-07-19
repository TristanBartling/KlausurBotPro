"""Immutable contracts for the UI-independent frequency-domain workflow."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from klausurbotpro.application.transfer_function_preparation_contracts import (
    TransferFunctionPreparationResult,
)
from klausurbotpro.application.transfer_function_workflow_contracts import (
    TransferFunctionWorkflowLimits,
    TransferFunctionWorkflowRequest,
)
from klausurbotpro.domain import (
    BodeDataLimits,
    BodePhaseUnwrapLimits,
    BodePhaseUnwrapResult,
    Diagnostic,
    ExactRationalValue,
    FrequencyResponseLimits,
    LogFrequencyGridLimits,
    LogFrequencyGridRequest,
    LogFrequencyGridResult,
    ParameterSubstitutions,
    ReducedTransferFunction,
    TransferFunctionBodeDataResult,
    TransferFunctionFrequencyResponseResult,
)


class FrequencyDomainWorkflowMode(StrEnum):
    SINGLE_POINT = "single_point"
    BODE = "bode"


class FrequencyPhasePresentation(StrEnum):
    PRINCIPAL_ONLY = "principal_only"
    PRINCIPAL_AND_UNWRAPPED = "principal_and_unwrapped"


class FrequencyDomainWorkflowStatus(StrEnum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    FAILED = "failed"


class FrequencyDomainWorkflowStage(StrEnum):
    PREPARATION = "preparation"
    SINGLE_POINT_RESPONSE = "single_point_response"
    LOG_FREQUENCY_GRID = "log_frequency_grid"
    BODE_DATA = "bode_data"
    PHASE_UNWRAP = "phase_unwrap"


FREQUENCY_DOMAIN_STAGE_ORDER = (
    FrequencyDomainWorkflowStage.PREPARATION,
    FrequencyDomainWorkflowStage.SINGLE_POINT_RESPONSE,
    FrequencyDomainWorkflowStage.LOG_FREQUENCY_GRID,
    FrequencyDomainWorkflowStage.BODE_DATA,
    FrequencyDomainWorkflowStage.PHASE_UNWRAP,
)


class FrequencyDomainWorkflowStageStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    BLOCKED = "blocked"
    NOT_APPLICABLE = "not_applicable"


class FrequencyDomainWorkflowDiagnosticCode(StrEnum):
    INVALID_REQUEST = "frequency_domain_workflow.invalid_request"
    PREPARATION_FAILED = "frequency_domain_workflow.preparation_failed"
    SINGLE_POINT_FAILED = "frequency_domain_workflow.single_point_failed"
    GRID_FAILED = "frequency_domain_workflow.grid_failed"
    BODE_DATA_FAILED = "frequency_domain_workflow.bode_data_failed"
    PHASE_UNWRAP_FAILED = "frequency_domain_workflow.phase_unwrap_failed"
    CONTEXT_MISMATCH = "frequency_domain_workflow.context_mismatch"
    LIMIT_EXCEEDED = "frequency_domain_workflow.limit_exceeded"
    RESOURCE_LIMIT_EXCEEDED = (
        "frequency_domain_workflow.resource_limit_exceeded"
    )


@dataclass(frozen=True, slots=True)
class FrequencyDomainWorkflowRequest:
    preparation_request: TransferFunctionWorkflowRequest
    mode: FrequencyDomainWorkflowMode
    single_angular_frequency: ExactRationalValue | None = None
    grid_request: LogFrequencyGridRequest | None = None
    phase_presentation: FrequencyPhasePresentation = (
        FrequencyPhasePresentation.PRINCIPAL_ONLY
    )


@dataclass(frozen=True, slots=True)
class FrequencyDomainWorkflowLimits:
    preparation: TransferFunctionWorkflowLimits = (
        TransferFunctionWorkflowLimits()
    )
    frequency_response: FrequencyResponseLimits = FrequencyResponseLimits()
    grid: LogFrequencyGridLimits = LogFrequencyGridLimits()
    bode: BodeDataLimits = BodeDataLimits()
    phase_unwrap: BodePhaseUnwrapLimits = BodePhaseUnwrapLimits()
    max_aggregated_diagnostics: int = 4096

    def __post_init__(self) -> None:
        expected = (
            (
                self.preparation,
                TransferFunctionWorkflowLimits,
                "preparation",
            ),
            (
                self.frequency_response,
                FrequencyResponseLimits,
                "frequency_response",
            ),
            (self.grid, LogFrequencyGridLimits, "grid"),
            (self.bode, BodeDataLimits, "bode"),
            (
                self.phase_unwrap,
                BodePhaseUnwrapLimits,
                "phase_unwrap",
            ),
        )
        for value, expected_type, name in expected:
            if type(value) is not expected_type:
                raise TypeError(f"{name} has an invalid limits type.")
        diagnostic_limit = self.max_aggregated_diagnostics
        if type(diagnostic_limit) is not int or diagnostic_limit <= 0:
            raise ValueError(
                "max_aggregated_diagnostics must be a positive int."
            )


@dataclass(frozen=True, slots=True)
class FrequencyDomainWorkflowStageRecord:
    stage: FrequencyDomainWorkflowStage
    status: FrequencyDomainWorkflowStageStatus
    diagnostics: tuple[Diagnostic, ...] = ()

    def __post_init__(self) -> None:
        if type(self.stage) is not FrequencyDomainWorkflowStage:
            raise TypeError("stage must be FrequencyDomainWorkflowStage.")
        if type(self.status) is not FrequencyDomainWorkflowStageStatus:
            raise TypeError(
                "status must be FrequencyDomainWorkflowStageStatus."
            )
        if type(self.diagnostics) is not tuple or any(
            type(item) is not Diagnostic for item in self.diagnostics
        ):
            raise TypeError("diagnostics must be an exact Diagnostic tuple.")
        if self.status in (
            FrequencyDomainWorkflowStageStatus.BLOCKED,
            FrequencyDomainWorkflowStageStatus.NOT_APPLICABLE,
        ) and self.diagnostics:
            raise ValueError(
                "Blocked and inapplicable stages cannot contain diagnostics."
            )


@dataclass(frozen=True, slots=True, init=False)
class FrequencyDomainWorkflowResult:
    request: FrequencyDomainWorkflowRequest | None
    status: FrequencyDomainWorkflowStatus
    preparation_result: TransferFunctionPreparationResult | None
    single_point_result: TransferFunctionFrequencyResponseResult | None
    grid_result: LogFrequencyGridResult | None
    bode_data_result: TransferFunctionBodeDataResult | None
    phase_unwrap_result: BodePhaseUnwrapResult | None
    stage_records: tuple[FrequencyDomainWorkflowStageRecord, ...]
    diagnostics: tuple[Diagnostic, ...]

    def __new__(
        cls,
        *args: object,
        **kwargs: object,
    ) -> FrequencyDomainWorkflowResult:
        raise TypeError("Frequency-domain workflow results are service-controlled.")

    @classmethod
    def _create(
        cls,
        *,
        request: FrequencyDomainWorkflowRequest | None,
        status: FrequencyDomainWorkflowStatus,
        preparation_result: TransferFunctionPreparationResult | None = None,
        single_point_result: (
            TransferFunctionFrequencyResponseResult | None
        ) = None,
        grid_result: LogFrequencyGridResult | None = None,
        bode_data_result: TransferFunctionBodeDataResult | None = None,
        phase_unwrap_result: BodePhaseUnwrapResult | None = None,
        stage_records: tuple[FrequencyDomainWorkflowStageRecord, ...] = (),
        diagnostics: tuple[Diagnostic, ...] = (),
    ) -> FrequencyDomainWorkflowResult:
        instance = object.__new__(cls)
        for name, value in (
            ("request", request),
            ("status", status),
            ("preparation_result", preparation_result),
            ("single_point_result", single_point_result),
            ("grid_result", grid_result),
            ("bode_data_result", bode_data_result),
            ("phase_unwrap_result", phase_unwrap_result),
            ("stage_records", stage_records),
            ("diagnostics", diagnostics),
        ):
            object.__setattr__(instance, name, value)
        instance._validate_local()
        return instance

    def _validate_local(self) -> None:
        if self.request is not None and (
            type(self.request) is not FrequencyDomainWorkflowRequest
        ):
            raise TypeError("request has an invalid type.")
        if type(self.status) is not FrequencyDomainWorkflowStatus:
            raise TypeError("status has an invalid type.")
        optional_contracts = (
            (
                self.preparation_result,
                TransferFunctionPreparationResult,
                "preparation_result",
            ),
            (
                self.single_point_result,
                TransferFunctionFrequencyResponseResult,
                "single_point_result",
            ),
            (self.grid_result, LogFrequencyGridResult, "grid_result"),
            (
                self.bode_data_result,
                TransferFunctionBodeDataResult,
                "bode_data_result",
            ),
            (
                self.phase_unwrap_result,
                BodePhaseUnwrapResult,
                "phase_unwrap_result",
            ),
        )
        for value, expected_type, name in optional_contracts:
            if value is not None and type(value) is not expected_type:
                raise TypeError(f"{name} has an invalid type.")
        if type(self.stage_records) is not tuple or any(
            type(item) is not FrequencyDomainWorkflowStageRecord
            for item in self.stage_records
        ):
            raise TypeError("stage_records has an invalid type.")
        if type(self.diagnostics) is not tuple or any(
            type(item) is not Diagnostic for item in self.diagnostics
        ):
            raise TypeError("diagnostics has an invalid type.")

    @property
    def reduced_value(self) -> ReducedTransferFunction | None:
        return (
            None
            if self.preparation_result is None
            else self.preparation_result.reduced_value
        )

    @property
    def substitutions(self) -> ParameterSubstitutions | None:
        return (
            None
            if self.preparation_result is None
            else self.preparation_result.request.substitutions
        )

    @property
    def succeeded(self) -> bool:
        return self.status is FrequencyDomainWorkflowStatus.COMPLETE

    @property
    def active_frequency_response_result(
        self,
    ) -> TransferFunctionFrequencyResponseResult | None:
        if self.single_point_result is not None:
            return self.single_point_result
        if self.bode_data_result is None:
            return None
        return self.bode_data_result.frequency_response_result


__all__ = [
    "FREQUENCY_DOMAIN_STAGE_ORDER",
    "FrequencyDomainWorkflowDiagnosticCode",
    "FrequencyDomainWorkflowLimits",
    "FrequencyDomainWorkflowMode",
    "FrequencyDomainWorkflowRequest",
    "FrequencyDomainWorkflowResult",
    "FrequencyDomainWorkflowStage",
    "FrequencyDomainWorkflowStageRecord",
    "FrequencyDomainWorkflowStageStatus",
    "FrequencyDomainWorkflowStatus",
    "FrequencyPhasePresentation",
]
