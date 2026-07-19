"""UI-independent orchestration of the complete transfer-function workflow."""

from __future__ import annotations

from dataclasses import replace

from klausurbotpro.application._workflow_diagnostics import (
    aggregate_diagnostics,
    application_diagnostic,
    stage_failure_diagnostics,
)
from klausurbotpro.application._workflow_invalidation import (
    blocked_records_after,
)
from klausurbotpro.application._workflow_validation import (
    next_sequence,
    validate_provenance,
    validate_request,
)
from klausurbotpro.application.transfer_function_workflow_contracts import (
    OverrideProvenance,
    RawTransferFunctionOverride,
    ReducedTransferFunctionOverride,
    RootAnalysisOverride,
    TransferFunctionWorkflowLimits,
    TransferFunctionWorkflowOverride,
    TransferFunctionWorkflowRequest,
    TransferFunctionWorkflowState,
    WorkflowDiagnosticCode,
    WorkflowInputForm,
    WorkflowStage,
    WorkflowStageRecord,
    WorkflowStageStatus,
    WorkflowValueOrigin,
)
from klausurbotpro.domain import (
    Diagnostic,
    ParameterSubstitutions,
    RawTransferFunction,
    RawTransferFunctionCreationResult,
    RawTransferFunctionFactory,
    ReducedTransferFunction,
    TransferFunctionInput,
    TransferFunctionReducer,
    TransferFunctionReductionResult,
    TransferFunctionRootAnalysisResult,
    TransferFunctionRootAnalyzer,
    TransferFunctionStabilityAnalysisResult,
    TransferFunctionStabilityAnalyzer,
)
from klausurbotpro.parsing import (
    ParserConfig,
    SafeRationalExpressionParser,
)

_RESOURCE_ERRORS = (MemoryError, RecursionError, OverflowError)
_DEFAULT_LIMITS = TransferFunctionWorkflowLimits()


class TransferFunctionWorkflowService:
    """Run and update one deterministic, immutable workflow snapshot."""

    def __init__(
        self,
        limits: TransferFunctionWorkflowLimits = _DEFAULT_LIMITS,
    ) -> None:
        if type(limits) is not TransferFunctionWorkflowLimits:
            raise TypeError("limits must be TransferFunctionWorkflowLimits.")
        self._limits = limits

    def run(
        self,
        request: TransferFunctionWorkflowRequest,
    ) -> TransferFunctionWorkflowState:
        """Execute all supported stages strictly in order."""

        errors = validate_request(request, self._limits)
        if errors:
            return self._invalid_request_state(request, errors)
        try:
            parser = self._parser_for(request)
            if request.input_form is WorkflowInputForm.COMMON:
                assert request.common_expression_text is not None
                parsed = parser.parse_common(
                    request.common_expression_text,
                    variable_name=request.variable_name,
                    field=request.field,
                )
            else:
                assert request.numerator_expression_text is not None
                assert request.denominator_expression_text is not None
                parsed = parser.parse_pair(
                    request.numerator_expression_text,
                    request.denominator_expression_text,
                    variable_name=request.variable_name,
                    field=request.field,
                )
        except _RESOURCE_ERRORS as error:
            return self._resource_failure_state(
                request,
                WorkflowStage.PARSE,
                error,
            )
        if not parsed.succeeded:
            records = (
                self._failed_record(
                    WorkflowStage.PARSE,
                    parsed.diagnostics,
                    WorkflowDiagnosticCode.WORKFLOW_PARSE_FAILED,
                    request.field,
                ),
                *blocked_records_after(WorkflowStage.PARSE),
            )
            return self._state(
                request=request,
                substitutions=request.substitutions,
                parsed_input=None,
                records=records,
                operation_sequence=0,
            )
        assert parsed.value is not None
        return self._run_from_parsed(
            request=request,
            parsed_input=parsed.value,
            substitutions=request.substitutions,
            parse_record=self._success_record(
                WorkflowStage.PARSE,
                parsed.diagnostics,
            ),
            operation_sequence=0,
        )

    def update_substitutions(
        self,
        state: TransferFunctionWorkflowState,
        substitutions: ParameterSubstitutions | None,
    ) -> TransferFunctionWorkflowState:
        """Recompute only root and stability stages with an exact assignment."""

        self._require_state(state)
        sequence = next_sequence(state.operation_sequence, self._limits)
        if sequence is None:
            return self._operation_error(
                state,
                WorkflowStage.ROOT_ANALYSIS,
                WorkflowDiagnosticCode.WORKFLOW_LIMIT_EXCEEDED,
                "Die maximale Operationssequenz ist erreicht.",
                state.operation_sequence,
            )
        if substitutions is not None and type(substitutions) is not ParameterSubstitutions:
            return self._operation_error(
                state,
                WorkflowStage.ROOT_ANALYSIS,
                WorkflowDiagnosticCode.WORKFLOW_INVALID_SUBSTITUTIONS,
                "Die Parametersubstitution besitzt einen ungültigen Typ.",
                sequence,
            )
        reduced = state.reduced_value
        if reduced is None:
            return self._operation_error(
                state,
                WorkflowStage.ROOT_ANALYSIS,
                WorkflowDiagnosticCode.WORKFLOW_INVALID_SUBSTITUTIONS,
                "Ohne aktiven reduzierten Wert sind keine Substitutionen möglich.",
                sequence,
            )

        try:
            root_result = self._analyze_active_reduced(
                reduced,
                state.reduction_result,
                substitutions,
                field=state.request.field,
            )
        except _RESOURCE_ERRORS as error:
            return self._partial_resource_failure(
                request=state.request,
                substitutions=substitutions,
                parsed_input=state.parsed_input,
                raw_result=state.raw_result,
                reduction_result=state.reduction_result,
                active_reduced_value=state.active_reduced_value,
                prefix_records=state.stage_records[:3],
                failed_stage=WorkflowStage.ROOT_ANALYSIS,
                operation_sequence=sequence,
                error=error,
            )
        if not root_result.succeeded and _is_invalid_substitution(root_result):
            return self._operation_error(
                state,
                WorkflowStage.ROOT_ANALYSIS,
                WorkflowDiagnosticCode.WORKFLOW_INVALID_SUBSTITUTIONS,
                "Die exakte Parametersubstitution ist ungültig.",
                sequence,
                domain_diagnostics=root_result.diagnostics,
            )
        prefix = state.stage_records[:3]
        if not root_result.succeeded:
            records = (
                *prefix,
                self._failed_record(
                    WorkflowStage.ROOT_ANALYSIS,
                    root_result.diagnostics,
                    WorkflowDiagnosticCode.WORKFLOW_ROOT_ANALYSIS_FAILED,
                    state.request.field,
                ),
                WorkflowStageRecord(
                    WorkflowStage.STABILITY_ANALYSIS,
                    WorkflowStageStatus.BLOCKED,
                ),
            )
            return self._state(
                request=state.request,
                substitutions=substitutions,
                parsed_input=state.parsed_input,
                raw_result=state.raw_result,
                reduction_result=state.reduction_result,
                root_analysis_result=root_result,
                active_reduced_value=state.active_reduced_value,
                records=records,
                operation_sequence=sequence,
            )
        return self._finish_stability(
            request=state.request,
            substitutions=substitutions,
            parsed_input=state.parsed_input,
            raw_result=state.raw_result,
            reduction_result=state.reduction_result,
            active_reduced_value=state.active_reduced_value,
            prefix_records=prefix,
            root_result=root_result,
            root_origin=WorkflowValueOrigin.COMPUTED,
            operation_sequence=sequence,
        )

    def apply_override(
        self,
        state: TransferFunctionWorkflowState,
        override: TransferFunctionWorkflowOverride,
    ) -> TransferFunctionWorkflowState:
        """Apply a defensively validated intermediate value and recompute dependents."""

        self._require_state(state)
        sequence = next_sequence(state.operation_sequence, self._limits)
        if sequence is None:
            return self._operation_error(
                state,
                WorkflowStage.RAW_TRANSFER_FUNCTION,
                WorkflowDiagnosticCode.WORKFLOW_LIMIT_EXCEEDED,
                "Die maximale Operationssequenz ist erreicht.",
                state.operation_sequence,
            )
        if type(override) is RawTransferFunctionOverride:
            return self._apply_raw_override(state, override, sequence)
        if type(override) is ReducedTransferFunctionOverride:
            return self._apply_reduced_override(state, override, sequence)
        if type(override) is RootAnalysisOverride:
            return self._apply_root_override(state, override, sequence)
        return self._operation_error(
            state,
            WorkflowStage.RAW_TRANSFER_FUNCTION,
            WorkflowDiagnosticCode.WORKFLOW_INVALID_OVERRIDE,
            "Der Override-Typ wird nicht unterstützt.",
            sequence,
        )

    def _run_from_parsed(
        self,
        *,
        request: TransferFunctionWorkflowRequest,
        parsed_input: TransferFunctionInput,
        substitutions: ParameterSubstitutions | None,
        parse_record: WorkflowStageRecord,
        operation_sequence: int,
    ) -> TransferFunctionWorkflowState:
        factory = self._raw_factory_for(request)
        try:
            raw_result = factory.create(parsed_input, field=request.field)
        except _RESOURCE_ERRORS as error:
            return self._partial_resource_failure(
                request=request,
                substitutions=substitutions,
                parsed_input=parsed_input,
                prefix_records=(parse_record,),
                failed_stage=WorkflowStage.RAW_TRANSFER_FUNCTION,
                operation_sequence=operation_sequence,
                error=error,
            )
        if not raw_result.succeeded:
            records = (
                parse_record,
                self._failed_record(
                    WorkflowStage.RAW_TRANSFER_FUNCTION,
                    raw_result.diagnostics,
                    WorkflowDiagnosticCode.WORKFLOW_RAW_FAILED,
                    request.field,
                ),
                *blocked_records_after(WorkflowStage.RAW_TRANSFER_FUNCTION),
            )
            return self._state(
                request=request,
                substitutions=substitutions,
                parsed_input=parsed_input,
                raw_result=raw_result,
                records=records,
                operation_sequence=operation_sequence,
            )
        assert raw_result.value is not None
        return self._run_from_raw(
            request=request,
            parsed_input=parsed_input,
            substitutions=substitutions,
            raw_result=raw_result,
            prefix_records=(
                parse_record,
                self._success_record(
                    WorkflowStage.RAW_TRANSFER_FUNCTION,
                    raw_result.diagnostics,
                ),
            ),
            operation_sequence=operation_sequence,
        )

    def _run_from_raw(
        self,
        *,
        request: TransferFunctionWorkflowRequest,
        parsed_input: TransferFunctionInput | None,
        substitutions: ParameterSubstitutions | None,
        raw_result: RawTransferFunctionCreationResult,
        prefix_records: tuple[WorkflowStageRecord, ...],
        operation_sequence: int,
    ) -> TransferFunctionWorkflowState:
        raw = raw_result.value
        assert isinstance(raw, RawTransferFunction)
        try:
            reduction = TransferFunctionReducer(self._limits.reduction).reduce(
                raw,
                field=request.field,
            )
        except _RESOURCE_ERRORS as error:
            return self._partial_resource_failure(
                request=request,
                substitutions=substitutions,
                parsed_input=parsed_input,
                raw_result=raw_result,
                prefix_records=prefix_records,
                failed_stage=WorkflowStage.REDUCTION,
                operation_sequence=operation_sequence,
                error=error,
            )
        if not reduction.succeeded:
            records = (
                *prefix_records,
                self._failed_record(
                    WorkflowStage.REDUCTION,
                    reduction.diagnostics,
                    WorkflowDiagnosticCode.WORKFLOW_REDUCTION_FAILED,
                    request.field,
                ),
                *blocked_records_after(WorkflowStage.REDUCTION),
            )
            return self._state(
                request=request,
                substitutions=substitutions,
                parsed_input=parsed_input,
                raw_result=raw_result,
                reduction_result=reduction,
                records=records,
                operation_sequence=operation_sequence,
            )
        assert reduction.reduced is not None
        reduction_record = self._success_record(
            WorkflowStage.REDUCTION,
            reduction.diagnostics,
        )
        try:
            root_result = TransferFunctionRootAnalyzer(
                self._limits.root_analysis
            ).analyze_reduction(
                reduction,
                substitutions,
                field=request.field,
            )
        except _RESOURCE_ERRORS as error:
            return self._partial_resource_failure(
                request=request,
                substitutions=substitutions,
                parsed_input=parsed_input,
                raw_result=raw_result,
                reduction_result=reduction,
                prefix_records=(*prefix_records, reduction_record),
                failed_stage=WorkflowStage.ROOT_ANALYSIS,
                operation_sequence=operation_sequence,
                error=error,
            )
        if not root_result.succeeded:
            code = (
                WorkflowDiagnosticCode.WORKFLOW_INVALID_SUBSTITUTIONS
                if _is_invalid_substitution(root_result)
                else WorkflowDiagnosticCode.WORKFLOW_ROOT_ANALYSIS_FAILED
            )
            records = (
                *prefix_records,
                reduction_record,
                self._failed_record(
                    WorkflowStage.ROOT_ANALYSIS,
                    root_result.diagnostics,
                    code,
                    request.field,
                ),
                WorkflowStageRecord(
                    WorkflowStage.STABILITY_ANALYSIS,
                    WorkflowStageStatus.BLOCKED,
                ),
            )
            return self._state(
                request=request,
                substitutions=substitutions,
                parsed_input=parsed_input,
                raw_result=raw_result,
                reduction_result=reduction,
                root_analysis_result=root_result,
                records=records,
                operation_sequence=operation_sequence,
            )
        return self._finish_stability(
            request=request,
            substitutions=substitutions,
            parsed_input=parsed_input,
            raw_result=raw_result,
            reduction_result=reduction,
            active_reduced_value=None,
            prefix_records=(*prefix_records, reduction_record),
            root_result=root_result,
            root_origin=WorkflowValueOrigin.COMPUTED,
            operation_sequence=operation_sequence,
        )

    def _finish_stability(
        self,
        *,
        request: TransferFunctionWorkflowRequest,
        substitutions: ParameterSubstitutions | None,
        parsed_input: TransferFunctionInput | None,
        raw_result: RawTransferFunctionCreationResult | None,
        reduction_result: TransferFunctionReductionResult | None,
        active_reduced_value: ReducedTransferFunction | None,
        prefix_records: tuple[WorkflowStageRecord, ...],
        root_result: TransferFunctionRootAnalysisResult,
        root_origin: WorkflowValueOrigin,
        operation_sequence: int,
        root_provenance: OverrideProvenance | None = None,
    ) -> TransferFunctionWorkflowState:
        root_record = WorkflowStageRecord(
            WorkflowStage.ROOT_ANALYSIS,
            WorkflowStageStatus.SUCCEEDED,
            root_origin,
            root_result.diagnostics,
            root_provenance,
        )
        try:
            stability = TransferFunctionStabilityAnalyzer(
                self._limits.stability_analysis
            ).analyze(root_result, field=request.field)
        except _RESOURCE_ERRORS as error:
            return self._partial_resource_failure(
                request=request,
                substitutions=substitutions,
                parsed_input=parsed_input,
                raw_result=raw_result,
                reduction_result=reduction_result,
                root_analysis_result=root_result,
                active_reduced_value=active_reduced_value,
                prefix_records=(*prefix_records, root_record),
                failed_stage=WorkflowStage.STABILITY_ANALYSIS,
                operation_sequence=operation_sequence,
                error=error,
            )
        if not stability.succeeded:
            records = (
                *prefix_records,
                root_record,
                self._failed_record(
                    WorkflowStage.STABILITY_ANALYSIS,
                    stability.diagnostics,
                    WorkflowDiagnosticCode.WORKFLOW_STABILITY_ANALYSIS_FAILED,
                    request.field,
                ),
            )
        else:
            records = (
                *prefix_records,
                root_record,
                self._success_record(
                    WorkflowStage.STABILITY_ANALYSIS,
                    stability.diagnostics,
                ),
            )
        return self._state(
            request=request,
            substitutions=substitutions,
            parsed_input=parsed_input,
            raw_result=raw_result,
            reduction_result=reduction_result,
            root_analysis_result=root_result,
            stability_analysis_result=stability,
            active_reduced_value=active_reduced_value,
            records=records,
            operation_sequence=operation_sequence,
        )

    def _apply_raw_override(
        self,
        state: TransferFunctionWorkflowState,
        override: RawTransferFunctionOverride,
        sequence: int,
    ) -> TransferFunctionWorkflowState:
        provenance_errors = validate_provenance(
            override.provenance,
            expected_stage=WorkflowStage.RAW_TRANSFER_FUNCTION,
            expected_sequence=sequence,
            limits=self._limits,
        )
        if provenance_errors or type(override.value) is not RawTransferFunction:
            return self._invalid_override(
                state,
                WorkflowStage.RAW_TRANSFER_FUNCTION,
                sequence,
                provenance_errors,
            )
        try:
            revalidated = self._raw_factory_for(state.request).create(
                override.value.input_snapshot,
                field=state.request.field,
            )
        except _RESOURCE_ERRORS as error:
            return self._operation_error(
                state,
                WorkflowStage.RAW_TRANSFER_FUNCTION,
                WorkflowDiagnosticCode.WORKFLOW_RESOURCE_LIMIT_EXCEEDED,
                "Die defensive Raw-Revalidierung überschreitet Ressourcen.",
                sequence,
                details=(("exception", type(error).__name__),),
            )
        if not revalidated.succeeded or revalidated.value != override.value:
            return self._invalid_override(
                state,
                WorkflowStage.RAW_TRANSFER_FUNCTION,
                sequence,
                (("raw_value", "independent_revalidation_failed"),),
                domain_diagnostics=revalidated.diagnostics,
                mismatch=revalidated.succeeded,
            )
        parse_record = state.stage_records[0]
        raw_record = WorkflowStageRecord(
            WorkflowStage.RAW_TRANSFER_FUNCTION,
            WorkflowStageStatus.SUCCEEDED,
            WorkflowValueOrigin.OVERRIDDEN,
            revalidated.diagnostics,
            override.provenance,
        )
        return self._run_from_raw(
            request=state.request,
            parsed_input=state.parsed_input,
            substitutions=state.substitutions,
            raw_result=revalidated,
            prefix_records=(parse_record, raw_record),
            operation_sequence=sequence,
        )

    def _apply_reduced_override(
        self,
        state: TransferFunctionWorkflowState,
        override: ReducedTransferFunctionOverride,
        sequence: int,
    ) -> TransferFunctionWorkflowState:
        provenance_errors = validate_provenance(
            override.provenance,
            expected_stage=WorkflowStage.REDUCTION,
            expected_sequence=sequence,
            limits=self._limits,
        )
        if (
            provenance_errors
            or type(override.value) is not ReducedTransferFunction
            or state.raw_value is None
        ):
            return self._invalid_override(
                state,
                WorkflowStage.REDUCTION,
                sequence,
                provenance_errors
                or (("reduced_value", "missing_raw_context"),),
            )
        if (
            override.value.variable_name != state.request.variable_name
            or not override.value.used_parameter_names.issubset(
                state.request.allowed_parameter_names
            )
        ):
            return self._invalid_override(
                state,
                WorkflowStage.REDUCTION,
                sequence,
                (("reduced_value", "request_context_mismatch"),),
                mismatch=True,
            )
        try:
            validation = TransferFunctionRootAnalyzer(
                self._limits.root_analysis
            ).analyze(override.value, None, field=state.request.field)
        except _RESOURCE_ERRORS as error:
            return self._operation_error(
                state,
                WorkflowStage.REDUCTION,
                WorkflowDiagnosticCode.WORKFLOW_RESOURCE_LIMIT_EXCEEDED,
                "Die defensive Reduced-Revalidierung überschreitet Ressourcen.",
                sequence,
                details=(("exception", type(error).__name__),),
            )
        if not validation.succeeded:
            return self._invalid_override(
                state,
                WorkflowStage.REDUCTION,
                sequence,
                (("reduced_value", "independent_revalidation_failed"),),
                domain_diagnostics=validation.diagnostics,
            )
        prefix = (
            state.stage_records[0],
            state.stage_records[1],
            WorkflowStageRecord(
                WorkflowStage.REDUCTION,
                WorkflowStageStatus.SUCCEEDED,
                WorkflowValueOrigin.OVERRIDDEN,
                (),
                override.provenance,
            ),
        )
        try:
            root_result = TransferFunctionRootAnalyzer(
                self._limits.root_analysis
            ).analyze(
                override.value,
                state.substitutions,
                field=state.request.field,
            )
        except _RESOURCE_ERRORS as error:
            return self._partial_resource_failure(
                request=state.request,
                substitutions=state.substitutions,
                parsed_input=state.parsed_input,
                raw_result=state.raw_result,
                active_reduced_value=override.value,
                prefix_records=prefix,
                failed_stage=WorkflowStage.ROOT_ANALYSIS,
                operation_sequence=sequence,
                error=error,
            )
        if not root_result.succeeded:
            records = (
                *prefix,
                self._failed_record(
                    WorkflowStage.ROOT_ANALYSIS,
                    root_result.diagnostics,
                    WorkflowDiagnosticCode.WORKFLOW_ROOT_ANALYSIS_FAILED,
                    state.request.field,
                ),
                WorkflowStageRecord(
                    WorkflowStage.STABILITY_ANALYSIS,
                    WorkflowStageStatus.BLOCKED,
                ),
            )
            return self._state(
                request=state.request,
                substitutions=state.substitutions,
                parsed_input=state.parsed_input,
                raw_result=state.raw_result,
                active_reduced_value=override.value,
                root_analysis_result=root_result,
                records=records,
                operation_sequence=sequence,
            )
        return self._finish_stability(
            request=state.request,
            substitutions=state.substitutions,
            parsed_input=state.parsed_input,
            raw_result=state.raw_result,
            reduction_result=None,
            active_reduced_value=override.value,
            prefix_records=prefix,
            root_result=root_result,
            root_origin=WorkflowValueOrigin.COMPUTED,
            operation_sequence=sequence,
        )

    def _apply_root_override(
        self,
        state: TransferFunctionWorkflowState,
        override: RootAnalysisOverride,
        sequence: int,
    ) -> TransferFunctionWorkflowState:
        provenance_errors = validate_provenance(
            override.provenance,
            expected_stage=WorkflowStage.ROOT_ANALYSIS,
            expected_sequence=sequence,
            limits=self._limits,
        )
        reduced = state.reduced_value
        if (
            provenance_errors
            or type(override.value) is not TransferFunctionRootAnalysisResult
            or reduced is None
            or not override.value.succeeded
        ):
            return self._invalid_override(
                state,
                WorkflowStage.ROOT_ANALYSIS,
                sequence,
                provenance_errors
                or (("root_analysis", "invalid_or_missing_context"),),
            )
        if (
            override.value.reduced_transfer_function != reduced
            or not _substitutions_match(
                override.value.substitutions,
                state.substitutions,
            )
        ):
            return self._invalid_override(
                state,
                WorkflowStage.ROOT_ANALYSIS,
                sequence,
                (("root_analysis", "active_context_mismatch"),),
                mismatch=True,
            )
        try:
            stability = TransferFunctionStabilityAnalyzer(
                self._limits.stability_analysis
            ).analyze(override.value, field=state.request.field)
        except _RESOURCE_ERRORS as error:
            return self._operation_error(
                state,
                WorkflowStage.ROOT_ANALYSIS,
                WorkflowDiagnosticCode.WORKFLOW_RESOURCE_LIMIT_EXCEEDED,
                "Die defensive Root-Revalidierung überschreitet Ressourcen.",
                sequence,
                details=(("exception", type(error).__name__),),
            )
        if not stability.succeeded:
            return self._invalid_override(
                state,
                WorkflowStage.ROOT_ANALYSIS,
                sequence,
                (("root_analysis", "defensive_revalidation_failed"),),
                domain_diagnostics=stability.diagnostics,
            )
        records = (
            *state.stage_records[:3],
            WorkflowStageRecord(
                WorkflowStage.ROOT_ANALYSIS,
                WorkflowStageStatus.SUCCEEDED,
                WorkflowValueOrigin.OVERRIDDEN,
                override.value.diagnostics,
                override.provenance,
            ),
            self._success_record(
                WorkflowStage.STABILITY_ANALYSIS,
                stability.diagnostics,
            ),
        )
        return self._state(
            request=state.request,
            substitutions=state.substitutions,
            parsed_input=state.parsed_input,
            raw_result=state.raw_result,
            reduction_result=state.reduction_result,
            root_analysis_result=override.value,
            stability_analysis_result=stability,
            active_reduced_value=state.active_reduced_value,
            records=records,
            operation_sequence=sequence,
        )

    def _analyze_active_reduced(
        self,
        reduced: ReducedTransferFunction,
        reduction_result: TransferFunctionReductionResult | None,
        substitutions: ParameterSubstitutions | None,
        *,
        field: str | None,
    ) -> TransferFunctionRootAnalysisResult:
        analyzer = TransferFunctionRootAnalyzer(self._limits.root_analysis)
        if (
            reduction_result is not None
            and reduction_result.reduced == reduced
        ):
            return analyzer.analyze_reduction(
                reduction_result,
                substitutions,
                field=field,
            )
        return analyzer.analyze(reduced, substitutions, field=field)

    def _invalid_override(
        self,
        state: TransferFunctionWorkflowState,
        stage: WorkflowStage,
        sequence: int,
        details: tuple[tuple[str, str], ...],
        *,
        domain_diagnostics: tuple[Diagnostic, ...] = (),
        mismatch: bool = False,
    ) -> TransferFunctionWorkflowState:
        code = (
            WorkflowDiagnosticCode.WORKFLOW_OVERRIDE_CONTEXT_MISMATCH
            if mismatch
            else WorkflowDiagnosticCode.WORKFLOW_INVALID_OVERRIDE
        )
        return self._operation_error(
            state,
            stage,
            code,
            "Der Override wurde abgelehnt; der aktive mathematische Wert bleibt erhalten.",
            sequence,
            details=details,
            domain_diagnostics=domain_diagnostics,
        )

    def _operation_error(
        self,
        state: TransferFunctionWorkflowState,
        stage: WorkflowStage,
        code: WorkflowDiagnosticCode,
        message: str,
        sequence: int,
        *,
        details: tuple[tuple[str, str], ...] = (),
        domain_diagnostics: tuple[Diagnostic, ...] = (),
    ) -> TransferFunctionWorkflowState:
        records = list(state.stage_records)
        index = tuple(record.stage for record in records).index(stage)
        current = records[index]
        records[index] = replace(
            current,
            diagnostics=(
                *current.diagnostics,
                *domain_diagnostics,
                application_diagnostic(
                    code,
                    message,
                    field=state.request.field,
                    details=details,
                ),
            ),
            diagnostic_provenances=(
                *current.diagnostic_provenances,
                *tuple(None for _ in domain_diagnostics),
                None,
            ),
        )
        return self._state(
            request=state.request,
            substitutions=state.substitutions,
            parsed_input=state.parsed_input,
            raw_result=state.raw_result,
            reduction_result=state.reduction_result,
            root_analysis_result=state.root_analysis_result,
            stability_analysis_result=state.stability_analysis_result,
            active_reduced_value=state.active_reduced_value,
            records=tuple(records),
            operation_sequence=sequence,
        )

    def _invalid_request_state(
        self,
        request: TransferFunctionWorkflowRequest,
        errors: tuple[tuple[str, str], ...],
    ) -> TransferFunctionWorkflowState:
        diagnostic = application_diagnostic(
            WorkflowDiagnosticCode.WORKFLOW_INVALID_REQUEST,
            "Der Workflow-Request ist ungültig.",
            field=request.field if isinstance(request.field, str) else None,
            details=errors,
        )
        records = (
            WorkflowStageRecord(
                WorkflowStage.PARSE,
                WorkflowStageStatus.FAILED,
                diagnostics=(diagnostic,),
            ),
            *blocked_records_after(WorkflowStage.PARSE),
        )
        return self._state(
            request=request,
            substitutions=(
                request.substitutions
                if type(request.substitutions) is ParameterSubstitutions
                else None
            ),
            parsed_input=None,
            records=records,
            operation_sequence=0,
        )

    def _resource_failure_state(
        self,
        request: TransferFunctionWorkflowRequest,
        stage: WorkflowStage,
        error: BaseException,
    ) -> TransferFunctionWorkflowState:
        diagnostic = application_diagnostic(
            WorkflowDiagnosticCode.WORKFLOW_RESOURCE_LIMIT_EXCEEDED,
            "Der Workflow überschreitet verfügbare Ressourcen.",
            field=request.field,
            details=(("exception", type(error).__name__),),
        )
        records = tuple(
            WorkflowStageRecord(
                item,
                (
                    WorkflowStageStatus.FAILED
                    if item is stage
                    else WorkflowStageStatus.BLOCKED
                ),
                diagnostics=(diagnostic,) if item is stage else (),
            )
            for item in (
                WorkflowStage.PARSE,
                WorkflowStage.RAW_TRANSFER_FUNCTION,
                WorkflowStage.REDUCTION,
                WorkflowStage.ROOT_ANALYSIS,
                WorkflowStage.STABILITY_ANALYSIS,
            )
        )
        return self._state(
            request=request,
            substitutions=request.substitutions,
            parsed_input=None,
            records=records,
            operation_sequence=0,
        )

    def _partial_resource_failure(
        self,
        *,
        request: TransferFunctionWorkflowRequest,
        substitutions: ParameterSubstitutions | None,
        parsed_input: TransferFunctionInput | None,
        prefix_records: tuple[WorkflowStageRecord, ...],
        failed_stage: WorkflowStage,
        operation_sequence: int,
        error: BaseException,
        raw_result: RawTransferFunctionCreationResult | None = None,
        reduction_result: TransferFunctionReductionResult | None = None,
        root_analysis_result: TransferFunctionRootAnalysisResult | None = None,
        active_reduced_value: ReducedTransferFunction | None = None,
    ) -> TransferFunctionWorkflowState:
        diagnostic = application_diagnostic(
            WorkflowDiagnosticCode.WORKFLOW_RESOURCE_LIMIT_EXCEEDED,
            "Die Workflow-Stufe überschreitet verfügbare Ressourcen.",
            field=request.field,
            details=(("exception", type(error).__name__),),
        )
        records = (
            *prefix_records,
            WorkflowStageRecord(
                failed_stage,
                WorkflowStageStatus.FAILED,
                diagnostics=(diagnostic,),
            ),
            *blocked_records_after(failed_stage),
        )
        return self._state(
            request=request,
            substitutions=substitutions,
            parsed_input=parsed_input,
            raw_result=raw_result,
            reduction_result=reduction_result,
            root_analysis_result=root_analysis_result,
            active_reduced_value=active_reduced_value,
            records=records,
            operation_sequence=operation_sequence,
        )

    def _state(
        self,
        *,
        request: TransferFunctionWorkflowRequest,
        substitutions: ParameterSubstitutions | None,
        parsed_input: TransferFunctionInput | None,
        records: tuple[WorkflowStageRecord, ...],
        operation_sequence: int,
        raw_result: RawTransferFunctionCreationResult | None = None,
        reduction_result: TransferFunctionReductionResult | None = None,
        root_analysis_result: TransferFunctionRootAnalysisResult | None = None,
        stability_analysis_result: TransferFunctionStabilityAnalysisResult
        | None = None,
        active_reduced_value: ReducedTransferFunction | None = None,
    ) -> TransferFunctionWorkflowState:
        aggregated = aggregate_diagnostics(records, operation_sequence)
        if len(aggregated) > self._limits.max_aggregated_diagnostics:
            diagnostic = application_diagnostic(
                WorkflowDiagnosticCode.WORKFLOW_LIMIT_EXCEEDED,
                "Die aggregierten Workflow-Diagnosen überschreiten das Limit.",
                field=request.field,
                details=(("limit", "max_aggregated_diagnostics"),),
            )
            records = (
                WorkflowStageRecord(
                    WorkflowStage.PARSE,
                    WorkflowStageStatus.FAILED,
                    diagnostics=(diagnostic,),
                ),
                *blocked_records_after(WorkflowStage.PARSE),
            )
            aggregated = aggregate_diagnostics(records, operation_sequence)
            parsed_input = None
            raw_result = None
            reduction_result = None
            root_analysis_result = None
            stability_analysis_result = None
            active_reduced_value = None
        return TransferFunctionWorkflowState(
            request=request,
            substitutions=substitutions,
            parsed_input=parsed_input,
            raw_result=raw_result,
            reduction_result=reduction_result,
            root_analysis_result=root_analysis_result,
            stability_analysis_result=stability_analysis_result,
            stage_records=records,
            aggregated_diagnostics=aggregated,
            operation_sequence=operation_sequence,
            active_reduced_value=active_reduced_value,
        )

    @staticmethod
    def _success_record(
        stage: WorkflowStage,
        diagnostics: tuple[Diagnostic, ...],
    ) -> WorkflowStageRecord:
        return WorkflowStageRecord(
            stage,
            WorkflowStageStatus.SUCCEEDED,
            WorkflowValueOrigin.COMPUTED,
            diagnostics,
        )

    @staticmethod
    def _failed_record(
        stage: WorkflowStage,
        diagnostics: tuple[Diagnostic, ...],
        code: WorkflowDiagnosticCode,
        field: str | None,
    ) -> WorkflowStageRecord:
        return WorkflowStageRecord(
            stage,
            WorkflowStageStatus.FAILED,
            diagnostics=stage_failure_diagnostics(
                stage,
                diagnostics,
                code,
                field=field,
            ),
        )

    def _parser_for(
        self,
        request: TransferFunctionWorkflowRequest,
    ) -> SafeRationalExpressionParser:
        return SafeRationalExpressionParser(
            ParserConfig(
                frozenset(
                    (*request.allowed_parameter_names, request.variable_name)
                ),
                self._limits.parser,
            )
        )

    def _raw_factory_for(
        self,
        request: TransferFunctionWorkflowRequest,
    ) -> RawTransferFunctionFactory:
        return RawTransferFunctionFactory(
            expected_variable_name=request.variable_name,
            allowed_parameter_names=frozenset(request.allowed_parameter_names),
            limits=self._limits.raw,
        )

    @staticmethod
    def _require_state(state: TransferFunctionWorkflowState) -> None:
        if type(state) is not TransferFunctionWorkflowState:
            raise TypeError("state must be a TransferFunctionWorkflowState.")


def _is_invalid_substitution(
    result: TransferFunctionRootAnalysisResult,
) -> bool:
    return any(
        diagnostic.code.value
        in {
            "root_analysis.invalid_substitution",
            "root_analysis.missing_parameters",
        }
        for diagnostic in result.diagnostics
    )


def _substitutions_match(
    first: ParameterSubstitutions | None,
    second: ParameterSubstitutions | None,
) -> bool:
    if first == second:
        return True
    return (
        first is None
        and second is not None
        and second.assignments == ()
    ) or (
        second is None
        and first is not None
        and first.assignments == ()
    )


__all__ = ["TransferFunctionWorkflowService"]
