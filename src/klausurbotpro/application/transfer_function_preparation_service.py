"""Shared parse-to-reduction transfer-function preparation pipeline."""

from __future__ import annotations

from klausurbotpro.application._transfer_function_preparation_steps import (
    parse_request,
    raw_factory_for,
)
from klausurbotpro.application._transfer_function_preparation_validation import (
    validate_transfer_function_preparation_result,
)
from klausurbotpro.application._workflow_diagnostics import (
    application_diagnostic,
    stage_failure_diagnostics,
)
from klausurbotpro.application._workflow_validation import validate_request
from klausurbotpro.application.transfer_function_preparation_contracts import (
    PREPARATION_STAGE_ORDER,
    TransferFunctionPreparationResult,
    TransferFunctionPreparationStage,
    TransferFunctionPreparationStageRecord,
    TransferFunctionPreparationStageStatus,
    TransferFunctionPreparationStatus,
)
from klausurbotpro.application.transfer_function_workflow_contracts import (
    TransferFunctionWorkflowLimits,
    TransferFunctionWorkflowRequest,
    WorkflowDiagnosticCode,
    WorkflowStage,
)
from klausurbotpro.domain import (
    Diagnostic,
    RawTransferFunctionCreationResult,
    TransferFunctionInput,
    TransferFunctionReducer,
    TransferFunctionReductionResult,
)

_DEFAULT_LIMITS = TransferFunctionWorkflowLimits()
_RESOURCE_ERRORS = (MemoryError, RecursionError, OverflowError)
_WORKFLOW_STAGE = {
    TransferFunctionPreparationStage.PARSE: WorkflowStage.PARSE,
    TransferFunctionPreparationStage.RAW_TRANSFER_FUNCTION: (
        WorkflowStage.RAW_TRANSFER_FUNCTION
    ),
    TransferFunctionPreparationStage.REDUCTION: WorkflowStage.REDUCTION,
}
_FAILURE_CODE = {
    TransferFunctionPreparationStage.PARSE: (
        WorkflowDiagnosticCode.WORKFLOW_PARSE_FAILED
    ),
    TransferFunctionPreparationStage.RAW_TRANSFER_FUNCTION: (
        WorkflowDiagnosticCode.WORKFLOW_RAW_FAILED
    ),
    TransferFunctionPreparationStage.REDUCTION: (
        WorkflowDiagnosticCode.WORKFLOW_REDUCTION_FAILED
    ),
}


class TransferFunctionPreparationService:
    """Validate, parse, create a raw value, and reduce it exactly once."""

    def __init__(
        self,
        limits: TransferFunctionWorkflowLimits = _DEFAULT_LIMITS,
    ) -> None:
        if type(limits) is not TransferFunctionWorkflowLimits:
            raise TypeError("limits must be TransferFunctionWorkflowLimits.")
        self._limits = limits

    def prepare(
        self,
        request: TransferFunctionWorkflowRequest,
    ) -> TransferFunctionPreparationResult:
        if type(request) is not TransferFunctionWorkflowRequest:
            raise TypeError(
                "request must be a TransferFunctionWorkflowRequest."
            )
        request_errors = validate_request(request, self._limits)
        if request_errors:
            return self._finish(
                request=request,
                parsed_input=None,
                raw_result=None,
                reduction_result=None,
                records=(
                    self._failed_application_record(
                        TransferFunctionPreparationStage.PARSE,
                        WorkflowDiagnosticCode.WORKFLOW_INVALID_REQUEST,
                        "Der Workflow-Request ist ungültig.",
                        request,
                        details=request_errors,
                    ),
                    *self._blocked_after(
                        TransferFunctionPreparationStage.PARSE
                    ),
                ),
            )

        try:
            parsed = parse_request(request, self._limits)
        except _RESOURCE_ERRORS as error:
            return self._resource_failure(
                request,
                TransferFunctionPreparationStage.PARSE,
                error,
            )
        if not parsed.succeeded:
            return self._finish(
                request=request,
                parsed_input=None,
                raw_result=None,
                reduction_result=None,
                records=(
                    self._failed_domain_record(
                        TransferFunctionPreparationStage.PARSE,
                        parsed.diagnostics,
                        request,
                    ),
                    *self._blocked_after(
                        TransferFunctionPreparationStage.PARSE
                    ),
                ),
            )
        assert parsed.value is not None
        parse_record = self._success_record(
            TransferFunctionPreparationStage.PARSE,
            parsed.diagnostics,
        )
        try:
            raw_result = raw_factory_for(request, self._limits).create(
                parsed.value,
                field=request.field,
            )
        except _RESOURCE_ERRORS as error:
            return self._resource_failure(
                request,
                TransferFunctionPreparationStage.RAW_TRANSFER_FUNCTION,
                error,
                parsed_input=parsed.value,
                prefix=(parse_record,),
            )
        if not raw_result.succeeded:
            return self._finish(
                request=request,
                parsed_input=parsed.value,
                raw_result=raw_result,
                reduction_result=None,
                records=(
                    parse_record,
                    self._failed_domain_record(
                        TransferFunctionPreparationStage.RAW_TRANSFER_FUNCTION,
                        raw_result.diagnostics,
                        request,
                    ),
                    *self._blocked_after(
                        TransferFunctionPreparationStage.RAW_TRANSFER_FUNCTION
                    ),
                ),
            )
        assert raw_result.value is not None
        raw_record = self._success_record(
            TransferFunctionPreparationStage.RAW_TRANSFER_FUNCTION,
            raw_result.diagnostics,
        )
        try:
            reduction = TransferFunctionReducer(
                self._limits.reduction
            ).reduce(raw_result.value, field=request.field)
        except _RESOURCE_ERRORS as error:
            return self._resource_failure(
                request,
                TransferFunctionPreparationStage.REDUCTION,
                error,
                parsed_input=parsed.value,
                raw_result=raw_result,
                prefix=(parse_record, raw_record),
            )
        if not reduction.succeeded:
            return self._finish(
                request=request,
                parsed_input=parsed.value,
                raw_result=raw_result,
                reduction_result=reduction,
                records=(
                    parse_record,
                    raw_record,
                    self._failed_domain_record(
                        TransferFunctionPreparationStage.REDUCTION,
                        reduction.diagnostics,
                        request,
                    ),
                ),
            )
        return self._finish(
            request=request,
            parsed_input=parsed.value,
            raw_result=raw_result,
            reduction_result=reduction,
            records=(
                parse_record,
                raw_record,
                self._success_record(
                    TransferFunctionPreparationStage.REDUCTION,
                    reduction.diagnostics,
                ),
            ),
        )

    def _resource_failure(
        self,
        request: TransferFunctionWorkflowRequest,
        stage: TransferFunctionPreparationStage,
        error: BaseException,
        *,
        parsed_input: TransferFunctionInput | None = None,
        raw_result: RawTransferFunctionCreationResult | None = None,
        prefix: tuple[TransferFunctionPreparationStageRecord, ...] = (),
    ) -> TransferFunctionPreparationResult:
        return self._finish(
            request=request,
            parsed_input=parsed_input,
            raw_result=raw_result,
            reduction_result=None,
            records=(
                *prefix,
                self._failed_application_record(
                    stage,
                    WorkflowDiagnosticCode.WORKFLOW_RESOURCE_LIMIT_EXCEEDED,
                    "Die Preparation-Stufe überschreitet verfügbare Ressourcen.",
                    request,
                    details=(("exception", type(error).__name__),),
                ),
                *self._blocked_after(stage),
            ),
        )

    def _finish(
        self,
        *,
        request: TransferFunctionWorkflowRequest,
        parsed_input: TransferFunctionInput | None,
        raw_result: RawTransferFunctionCreationResult | None,
        reduction_result: TransferFunctionReductionResult | None,
        records: tuple[TransferFunctionPreparationStageRecord, ...],
    ) -> TransferFunctionPreparationResult:
        (
            records,
            parsed_input,
            raw_result,
            reduction_result,
        ) = self._enforce_diagnostic_limit(
            request,
            records,
            parsed_input,
            raw_result,
            reduction_result,
        )
        status = self._derive_status(records)
        diagnostics = tuple(
            diagnostic
            for record in records
            for diagnostic in record.diagnostics
        )
        result = TransferFunctionPreparationResult._create(
            request=request,
            status=status,
            parsed_input=parsed_input,
            raw_result=raw_result,
            reduction_result=reduction_result,
            stage_records=records,
            diagnostics=diagnostics,
        )
        validate_transfer_function_preparation_result(result, self._limits)
        return result

    def _enforce_diagnostic_limit(
        self,
        request: TransferFunctionWorkflowRequest,
        records: tuple[TransferFunctionPreparationStageRecord, ...],
        parsed_input: TransferFunctionInput | None,
        raw_result: RawTransferFunctionCreationResult | None,
        reduction_result: TransferFunctionReductionResult | None,
    ) -> tuple[
        tuple[TransferFunctionPreparationStageRecord, ...],
        TransferFunctionInput | None,
        RawTransferFunctionCreationResult | None,
        TransferFunctionReductionResult | None,
    ]:
        count = sum(len(record.diagnostics) for record in records)
        if count <= self._limits.max_aggregated_diagnostics:
            return records, parsed_input, raw_result, reduction_result
        capacity = self._limits.max_aggregated_diagnostics - 1
        used = 0
        for index, record in enumerate(records):
            if used + len(record.diagnostics) <= capacity:
                used += len(record.diagnostics)
                continue
            stage = record.stage
            limited = self._failed_application_record(
                stage,
                WorkflowDiagnosticCode.WORKFLOW_LIMIT_EXCEEDED,
                "Die Preparation-Stufe überschreitet das Diagnoselimit.",
                request,
                details=(("limit", "max_aggregated_diagnostics"),),
            )
            bounded = (
                *records[:index],
                limited,
                *self._blocked_after(stage),
            )
            if index == 0:
                parsed_input = None
            if index <= 1:
                raw_result = None
            reduction_result = None
            return bounded, parsed_input, raw_result, reduction_result
        raise AssertionError("Diagnostic overflow must identify a stage.")

    @staticmethod
    def _derive_status(
        records: tuple[TransferFunctionPreparationStageRecord, ...],
    ) -> TransferFunctionPreparationStatus:
        if all(
            record.status
            is TransferFunctionPreparationStageStatus.SUCCEEDED
            for record in records
        ):
            return TransferFunctionPreparationStatus.COMPLETE
        if (
            records[0].status
            is TransferFunctionPreparationStageStatus.SUCCEEDED
        ):
            return TransferFunctionPreparationStatus.PARTIAL
        return TransferFunctionPreparationStatus.FAILED

    @staticmethod
    def _success_record(
        stage: TransferFunctionPreparationStage,
        diagnostics: tuple[Diagnostic, ...],
    ) -> TransferFunctionPreparationStageRecord:
        return TransferFunctionPreparationStageRecord(
            stage,
            TransferFunctionPreparationStageStatus.SUCCEEDED,
            diagnostics,
        )

    @staticmethod
    def _failed_domain_record(
        stage: TransferFunctionPreparationStage,
        diagnostics: tuple[Diagnostic, ...],
        request: TransferFunctionWorkflowRequest,
    ) -> TransferFunctionPreparationStageRecord:
        return TransferFunctionPreparationStageRecord(
            stage,
            TransferFunctionPreparationStageStatus.FAILED,
            stage_failure_diagnostics(
                _WORKFLOW_STAGE[stage],
                diagnostics,
                _FAILURE_CODE[stage],
                field=request.field,
            ),
        )

    @staticmethod
    def _failed_application_record(
        stage: TransferFunctionPreparationStage,
        code: WorkflowDiagnosticCode,
        message: str,
        request: TransferFunctionWorkflowRequest,
        *,
        details: tuple[tuple[str, str], ...] = (),
    ) -> TransferFunctionPreparationStageRecord:
        return TransferFunctionPreparationStageRecord(
            stage,
            TransferFunctionPreparationStageStatus.FAILED,
            (
                application_diagnostic(
                    code,
                    message,
                    field=(
                        request.field
                        if request.field is None
                        or type(request.field) is str
                        else None
                    ),
                    details=details,
                ),
            ),
        )

    @staticmethod
    def _blocked_after(
        stage: TransferFunctionPreparationStage,
    ) -> tuple[TransferFunctionPreparationStageRecord, ...]:
        index = PREPARATION_STAGE_ORDER.index(stage)
        return tuple(
            TransferFunctionPreparationStageRecord(
                later,
                TransferFunctionPreparationStageStatus.BLOCKED,
            )
            for later in PREPARATION_STAGE_ORDER[index + 1 :]
        )


__all__ = ["TransferFunctionPreparationService"]
