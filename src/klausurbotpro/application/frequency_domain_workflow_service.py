"""UI-independent orchestration of frequency-domain analyses."""

from __future__ import annotations

from klausurbotpro.application._frequency_domain_workflow_diagnostics import (
    frequency_workflow_diagnostic,
    owned_diagnostics,
)
from klausurbotpro.application._frequency_domain_workflow_validation import (
    validate_frequency_domain_request,
    validate_frequency_domain_workflow_result,
)
from klausurbotpro.application.frequency_domain_workflow_contracts import (
    FREQUENCY_DOMAIN_STAGE_ORDER,
    FrequencyDomainWorkflowDiagnosticCode,
    FrequencyDomainWorkflowLimits,
    FrequencyDomainWorkflowMode,
    FrequencyDomainWorkflowRequest,
    FrequencyDomainWorkflowResult,
    FrequencyDomainWorkflowStage,
    FrequencyDomainWorkflowStageRecord,
    FrequencyDomainWorkflowStageStatus,
    FrequencyDomainWorkflowStatus,
    FrequencyPhasePresentation,
)
from klausurbotpro.application.transfer_function_preparation_contracts import (
    TransferFunctionPreparationResult,
    TransferFunctionPreparationStatus,
)
from klausurbotpro.application.transfer_function_preparation_service import (
    TransferFunctionPreparationService,
)
from klausurbotpro.domain import (
    BodePhaseUnwrapAnalyzer,
    BodePhaseUnwrapResult,
    Diagnostic,
    FrequencySampleSet,
    FrequencyReserveAnalyzer,
    FrequencyCrossoverAnalysis,
    LogFrequencyGridGenerator,
    LogFrequencyGridResult,
    ParameterSubstitutions,
    StandardElementBodeAnalyzer,
    StandardElementBodeResult,
    StabilityReserveAnalysis,
    TransferFunctionBodeDataAnalyzer,
    TransferFunctionBodeDataResult,
    TransferFunctionFrequencyResponseAnalyzer,
    TransferFunctionFrequencyResponseResult,
)

_DEFAULT_LIMITS = FrequencyDomainWorkflowLimits()
_RESOURCE_ERRORS = (MemoryError, RecursionError, OverflowError)


class FrequencyDomainWorkflowService:
    """Run one requested frequency workflow without downstream analyses."""

    def __init__(
        self,
        limits: FrequencyDomainWorkflowLimits = _DEFAULT_LIMITS,
    ) -> None:
        if type(limits) is not FrequencyDomainWorkflowLimits:
            raise TypeError("limits must be FrequencyDomainWorkflowLimits.")
        self._limits = limits

    def run(
        self,
        request: FrequencyDomainWorkflowRequest,
    ) -> FrequencyDomainWorkflowResult:
        if type(request) is not FrequencyDomainWorkflowRequest:
            raise TypeError("request must be FrequencyDomainWorkflowRequest.")
        request_errors = validate_frequency_domain_request(
            request,
            self._limits,
        )
        if request_errors:
            return self._invalid_request(request_errors)
        try:
            preparation = TransferFunctionPreparationService(
                self._limits.preparation
            ).prepare(request.preparation_request)
        except _RESOURCE_ERRORS as error:
            return self._resource_failure(
                request,
                FrequencyDomainWorkflowStage.PREPARATION,
                error,
            )
        if not preparation.succeeded:
            records = (
                self._failed_record(
                    FrequencyDomainWorkflowStage.PREPARATION,
                    preparation.diagnostics,
                    FrequencyDomainWorkflowDiagnosticCode.PREPARATION_FAILED,
                    request,
                ),
                *self._remaining_records(
                    request,
                    FrequencyDomainWorkflowStage.PREPARATION,
                    failed=True,
                ),
            )
            return self._finish(
                request=request,
                preparation_result=preparation,
                records=records,
            )
        assert preparation.reduced_value is not None
        preparation_record = self._success_record(
            FrequencyDomainWorkflowStage.PREPARATION,
            preparation.diagnostics,
        )
        if request.mode is FrequencyDomainWorkflowMode.SINGLE_POINT:
            return self._run_single_point(
                request,
                preparation,
                preparation_record,
            )
        return self._run_bode(request, preparation, preparation_record)

    def _run_single_point(
        self,
        request: FrequencyDomainWorkflowRequest,
        preparation: TransferFunctionPreparationResult,
        preparation_record: FrequencyDomainWorkflowStageRecord,
    ) -> FrequencyDomainWorkflowResult:
        assert request.single_angular_frequency is not None
        reduced = preparation.reduced_value
        substitutions = preparation.request.substitutions
        assert reduced is not None
        try:
            response = TransferFunctionFrequencyResponseAnalyzer(
                self._limits.frequency_response
            ).analyze(
                reduced,
                FrequencySampleSet((request.single_angular_frequency,)),
                substitutions,
                field=request.preparation_request.field,
            )
        except _RESOURCE_ERRORS as error:
            return self._resource_failure(
                request,
                FrequencyDomainWorkflowStage.SINGLE_POINT_RESPONSE,
                error,
                preparation_result=preparation,
                prefix=(preparation_record,),
            )
        if not response.succeeded:
            records = (
                preparation_record,
                self._failed_record(
                    FrequencyDomainWorkflowStage.SINGLE_POINT_RESPONSE,
                    response.diagnostics,
                    FrequencyDomainWorkflowDiagnosticCode.SINGLE_POINT_FAILED,
                    request,
                ),
                *self._remaining_records(
                    request,
                    FrequencyDomainWorkflowStage.SINGLE_POINT_RESPONSE,
                    failed=True,
                ),
            )
        else:
            records = (
                preparation_record,
                self._success_record(
                    FrequencyDomainWorkflowStage.SINGLE_POINT_RESPONSE,
                    response.diagnostics,
                ),
                *self._remaining_records(
                    request,
                    FrequencyDomainWorkflowStage.SINGLE_POINT_RESPONSE,
                    failed=False,
                ),
            )
        return self._finish(
            request=request,
            preparation_result=preparation,
            single_point_result=response,
            records=records,
        )

    def _run_bode(
        self,
        request: FrequencyDomainWorkflowRequest,
        preparation: TransferFunctionPreparationResult,
        preparation_record: FrequencyDomainWorkflowStageRecord,
    ) -> FrequencyDomainWorkflowResult:
        assert request.grid_request is not None
        try:
            grid = LogFrequencyGridGenerator(self._limits.grid).generate(
                request.grid_request,
                field=request.preparation_request.field,
            )
        except _RESOURCE_ERRORS as error:
            return self._resource_failure(
                request,
                FrequencyDomainWorkflowStage.LOG_FREQUENCY_GRID,
                error,
                preparation_result=preparation,
                prefix=(
                    preparation_record,
                    self._not_applicable(
                        FrequencyDomainWorkflowStage.SINGLE_POINT_RESPONSE
                    ),
                ),
            )
        grid_prefix = (
            preparation_record,
            self._not_applicable(
                FrequencyDomainWorkflowStage.SINGLE_POINT_RESPONSE
            ),
        )
        if not grid.succeeded:
            records = (
                *grid_prefix,
                self._failed_record(
                    FrequencyDomainWorkflowStage.LOG_FREQUENCY_GRID,
                    grid.diagnostics,
                    FrequencyDomainWorkflowDiagnosticCode.GRID_FAILED,
                    request,
                ),
                *self._remaining_records(
                    request,
                    FrequencyDomainWorkflowStage.LOG_FREQUENCY_GRID,
                    failed=True,
                ),
            )
            return self._finish(
                request=request,
                preparation_result=preparation,
                grid_result=grid,
                records=records,
            )
        grid_record = self._success_record(
            FrequencyDomainWorkflowStage.LOG_FREQUENCY_GRID,
            grid.diagnostics,
        )
        reduced = preparation.reduced_value
        assert reduced is not None
        try:
            bode = TransferFunctionBodeDataAnalyzer(
                self._limits.frequency_response,
                self._limits.grid,
                self._limits.bode,
            ).analyze(
                reduced,
                grid,
                preparation.request.substitutions,
                field=request.preparation_request.field,
            )
        except _RESOURCE_ERRORS as error:
            return self._resource_failure(
                request,
                FrequencyDomainWorkflowStage.BODE_DATA,
                error,
                preparation_result=preparation,
                grid_result=grid,
                prefix=(*grid_prefix, grid_record),
            )
        bode_owned = (
            bode.diagnostics
            if not bode.succeeded
            else owned_diagnostics(bode.diagnostics, grid.diagnostics)
        )
        if not bode.succeeded:
            records = (
                *grid_prefix,
                grid_record,
                self._failed_record(
                    FrequencyDomainWorkflowStage.BODE_DATA,
                    bode_owned,
                    FrequencyDomainWorkflowDiagnosticCode.BODE_DATA_FAILED,
                    request,
                ),
                *self._remaining_records(
                    request,
                    FrequencyDomainWorkflowStage.BODE_DATA,
                    failed=True,
                ),
            )
            return self._finish(
                request=request,
                preparation_result=preparation,
                grid_result=grid,
                bode_data_result=bode,
                records=records,
            )
        standard_elements = StandardElementBodeAnalyzer(
            self._limits.preparation.root_analysis
        ).analyze(
            reduced,
            field=request.preparation_request.field,
        )
        bode_record = self._success_record(
            FrequencyDomainWorkflowStage.BODE_DATA,
            bode_owned,
        )
        if (
            request.phase_presentation
            is FrequencyPhasePresentation.PRINCIPAL_ONLY
        ):
            return self._finish(
                request=request,
                preparation_result=preparation,
                grid_result=grid,
                bode_data_result=bode,
                standard_element_bode_result=standard_elements,
                records=(
                    *grid_prefix,
                    grid_record,
                    bode_record,
                    self._not_applicable(
                        FrequencyDomainWorkflowStage.PHASE_UNWRAP
                    ),
                ),
            )
        try:
            unwrap = BodePhaseUnwrapAnalyzer(
                self._limits.frequency_response,
                self._limits.grid,
                self._limits.bode,
                self._limits.phase_unwrap,
            ).analyze(
                bode,
                field=request.preparation_request.field,
            )
        except _RESOURCE_ERRORS as error:
            return self._resource_failure(
                request,
                FrequencyDomainWorkflowStage.PHASE_UNWRAP,
                error,
                preparation_result=preparation,
                grid_result=grid,
                bode_data_result=bode,
                standard_element_bode_result=standard_elements,
                prefix=(*grid_prefix, grid_record, bode_record),
            )
        unwrap_owned = (
            unwrap.diagnostics
            if not unwrap.succeeded
            else owned_diagnostics(unwrap.diagnostics, bode.diagnostics)
        )
        unwrap_record = (
            self._success_record(
                FrequencyDomainWorkflowStage.PHASE_UNWRAP,
                unwrap_owned,
            )
            if unwrap.succeeded
            else self._failed_record(
                FrequencyDomainWorkflowStage.PHASE_UNWRAP,
                unwrap_owned,
                FrequencyDomainWorkflowDiagnosticCode.PHASE_UNWRAP_FAILED,
                request,
            )
        )
        return self._finish(
            request=request,
            preparation_result=preparation,
            grid_result=grid,
            bode_data_result=bode,
            standard_element_bode_result=standard_elements,
            phase_unwrap_result=unwrap,
            crossover_analysis=(
                analyses := FrequencyReserveAnalyzer().analyze(
                    reduced,
                    preparation.request.substitutions or ParameterSubstitutions(),
                    bode,
                    unwrap,
                    field=request.preparation_request.field,
                )
            )[0] if unwrap.succeeded else None,
            reserve_analysis=analyses[1] if unwrap.succeeded else None,
            records=(
                *grid_prefix,
                grid_record,
                bode_record,
                unwrap_record,
            ),
        )

    def _invalid_request(
        self,
        errors: tuple[tuple[str, str], ...],
    ) -> FrequencyDomainWorkflowResult:
        diagnostic = frequency_workflow_diagnostic(
            FrequencyDomainWorkflowDiagnosticCode.INVALID_REQUEST,
            "Der Frequenzbereichsauftrag ist ungültig.",
            details=errors,
        )
        result = FrequencyDomainWorkflowResult._create(
            request=None,
            status=FrequencyDomainWorkflowStatus.FAILED,
            diagnostics=(diagnostic,),
        )
        validate_frequency_domain_workflow_result(result, self._limits)
        return result

    def _resource_failure(
        self,
        request: FrequencyDomainWorkflowRequest,
        stage: FrequencyDomainWorkflowStage,
        error: BaseException,
        *,
        preparation_result: TransferFunctionPreparationResult | None = None,
        grid_result: LogFrequencyGridResult | None = None,
        bode_data_result: TransferFunctionBodeDataResult | None = None,
        standard_element_bode_result: StandardElementBodeResult | None = None,
        prefix: tuple[FrequencyDomainWorkflowStageRecord, ...] = (),
    ) -> FrequencyDomainWorkflowResult:
        record = FrequencyDomainWorkflowStageRecord(
            stage,
            FrequencyDomainWorkflowStageStatus.FAILED,
            (
                frequency_workflow_diagnostic(
                    FrequencyDomainWorkflowDiagnosticCode.RESOURCE_LIMIT_EXCEEDED,
                    "Die Frequenzworkflow-Stufe überschreitet Ressourcen.",
                    field=request.preparation_request.field,
                    details=(("exception", type(error).__name__),),
                ),
            ),
        )
        return self._finish(
            request=request,
            preparation_result=preparation_result,
            grid_result=grid_result,
            bode_data_result=bode_data_result,
            standard_element_bode_result=standard_element_bode_result,
            records=(
                *prefix,
                record,
                *self._remaining_records(request, stage, failed=True),
            ),
        )

    def _finish(
        self,
        *,
        request: FrequencyDomainWorkflowRequest,
        preparation_result: TransferFunctionPreparationResult | None,
        records: tuple[FrequencyDomainWorkflowStageRecord, ...],
        single_point_result: (
            TransferFunctionFrequencyResponseResult | None
        ) = None,
        grid_result: LogFrequencyGridResult | None = None,
        bode_data_result: TransferFunctionBodeDataResult | None = None,
        standard_element_bode_result: StandardElementBodeResult | None = None,
        phase_unwrap_result: BodePhaseUnwrapResult | None = None,
        crossover_analysis: FrequencyCrossoverAnalysis | None = None,
        reserve_analysis: StabilityReserveAnalysis | None = None,
    ) -> FrequencyDomainWorkflowResult:
        (
            records,
            preparation_result,
            single_point_result,
            grid_result,
            bode_data_result,
            standard_element_bode_result,
            phase_unwrap_result,
        ) = self._enforce_diagnostic_limit(
            request,
            records,
            preparation_result,
            single_point_result,
            grid_result,
            bode_data_result,
            standard_element_bode_result,
            phase_unwrap_result,
        )
        diagnostics = tuple(
            diagnostic
            for record in records
            for diagnostic in record.diagnostics
        )
        status = self._derive_status(records, preparation_result)
        result = FrequencyDomainWorkflowResult._create(
            request=request,
            status=status,
            preparation_result=preparation_result,
            single_point_result=single_point_result,
            grid_result=grid_result,
            bode_data_result=bode_data_result,
            standard_element_bode_result=standard_element_bode_result,
            phase_unwrap_result=phase_unwrap_result,
            crossover_analysis=crossover_analysis,
            reserve_analysis=reserve_analysis,
            stage_records=records,
            diagnostics=diagnostics,
        )
        validate_frequency_domain_workflow_result(result, self._limits)
        return result

    def _enforce_diagnostic_limit(
        self,
        request: FrequencyDomainWorkflowRequest,
        records: tuple[FrequencyDomainWorkflowStageRecord, ...],
        preparation_result: TransferFunctionPreparationResult | None,
        single_point_result: TransferFunctionFrequencyResponseResult | None,
        grid_result: LogFrequencyGridResult | None,
        bode_data_result: TransferFunctionBodeDataResult | None,
        standard_element_bode_result: StandardElementBodeResult | None,
        phase_unwrap_result: BodePhaseUnwrapResult | None,
    ) -> tuple[
        tuple[FrequencyDomainWorkflowStageRecord, ...],
        TransferFunctionPreparationResult | None,
        TransferFunctionFrequencyResponseResult | None,
        LogFrequencyGridResult | None,
        TransferFunctionBodeDataResult | None,
        StandardElementBodeResult | None,
        BodePhaseUnwrapResult | None,
    ]:
        if sum(len(item.diagnostics) for item in records) <= (
            self._limits.max_aggregated_diagnostics
        ):
            return (
                records,
                preparation_result,
                single_point_result,
                grid_result,
                bode_data_result,
                standard_element_bode_result,
                phase_unwrap_result,
            )
        capacity = self._limits.max_aggregated_diagnostics - 1
        used = 0
        for index, record in enumerate(records):
            if used + len(record.diagnostics) <= capacity:
                used += len(record.diagnostics)
                continue
            stage = record.stage
            limited = FrequencyDomainWorkflowStageRecord(
                stage,
                FrequencyDomainWorkflowStageStatus.FAILED,
                (
                    frequency_workflow_diagnostic(
                        FrequencyDomainWorkflowDiagnosticCode.LIMIT_EXCEEDED,
                        "Das aggregierte Diagnoselimit wurde überschritten.",
                        field=request.preparation_request.field,
                        details=(
                            ("limit", "max_aggregated_diagnostics"),
                        ),
                    ),
                ),
            )
            bounded = (
                *records[:index],
                limited,
                *self._remaining_records(request, stage, failed=True),
            )
            if index == 0:
                preparation_result = None
            if index <= 1:
                single_point_result = None
            if index <= 2:
                grid_result = None
            if index <= 3:
                bode_data_result = None
                standard_element_bode_result = None
            phase_unwrap_result = None
            return (
                bounded,
                preparation_result,
                single_point_result,
                grid_result,
                bode_data_result,
                standard_element_bode_result,
                phase_unwrap_result,
            )
        raise AssertionError("A diagnostic overflow must identify a stage.")

    @staticmethod
    def _derive_status(
        records: tuple[FrequencyDomainWorkflowStageRecord, ...],
        preparation_result: TransferFunctionPreparationResult | None,
    ) -> FrequencyDomainWorkflowStatus:
        if not any(
            item.status is FrequencyDomainWorkflowStageStatus.FAILED
            for item in records
        ):
            return FrequencyDomainWorkflowStatus.COMPLETE
        if (
            preparation_result is None
            or preparation_result.status
            is TransferFunctionPreparationStatus.FAILED
        ):
            return FrequencyDomainWorkflowStatus.FAILED
        return FrequencyDomainWorkflowStatus.PARTIAL

    @staticmethod
    def _success_record(
        stage: FrequencyDomainWorkflowStage,
        diagnostics: tuple[Diagnostic, ...],
    ) -> FrequencyDomainWorkflowStageRecord:
        return FrequencyDomainWorkflowStageRecord(
            stage,
            FrequencyDomainWorkflowStageStatus.SUCCEEDED,
            diagnostics,
        )

    @staticmethod
    def _failed_record(
        stage: FrequencyDomainWorkflowStage,
        diagnostics: tuple[Diagnostic, ...],
        code: FrequencyDomainWorkflowDiagnosticCode,
        request: FrequencyDomainWorkflowRequest,
    ) -> FrequencyDomainWorkflowStageRecord:
        return FrequencyDomainWorkflowStageRecord(
            stage,
            FrequencyDomainWorkflowStageStatus.FAILED,
            (
                *diagnostics,
                frequency_workflow_diagnostic(
                    code,
                    f"Die Frequenzworkflow-Stufe '{stage.value}' ist fehlgeschlagen.",
                    field=request.preparation_request.field,
                ),
            ),
        )

    @staticmethod
    def _not_applicable(
        stage: FrequencyDomainWorkflowStage,
    ) -> FrequencyDomainWorkflowStageRecord:
        return FrequencyDomainWorkflowStageRecord(
            stage,
            FrequencyDomainWorkflowStageStatus.NOT_APPLICABLE,
        )

    @classmethod
    def _remaining_records(
        cls,
        request: FrequencyDomainWorkflowRequest,
        stage: FrequencyDomainWorkflowStage,
        *,
        failed: bool,
    ) -> tuple[FrequencyDomainWorkflowStageRecord, ...]:
        start = FREQUENCY_DOMAIN_STAGE_ORDER.index(stage) + 1
        return tuple(
            FrequencyDomainWorkflowStageRecord(
                later,
                (
                    FrequencyDomainWorkflowStageStatus.BLOCKED
                    if failed and cls._is_requested(request, later)
                    else FrequencyDomainWorkflowStageStatus.NOT_APPLICABLE
                ),
            )
            for later in FREQUENCY_DOMAIN_STAGE_ORDER[start:]
        )

    @staticmethod
    def _is_requested(
        request: FrequencyDomainWorkflowRequest,
        stage: FrequencyDomainWorkflowStage,
    ) -> bool:
        if stage is FrequencyDomainWorkflowStage.PREPARATION:
            return True
        if request.mode is FrequencyDomainWorkflowMode.SINGLE_POINT:
            return stage is FrequencyDomainWorkflowStage.SINGLE_POINT_RESPONSE
        if stage in (
            FrequencyDomainWorkflowStage.LOG_FREQUENCY_GRID,
            FrequencyDomainWorkflowStage.BODE_DATA,
        ):
            return True
        return (
            stage is FrequencyDomainWorkflowStage.PHASE_UNWRAP
            and request.phase_presentation
            is FrequencyPhasePresentation.PRINCIPAL_AND_UNWRAPPED
        )


__all__ = ["FrequencyDomainWorkflowService"]
