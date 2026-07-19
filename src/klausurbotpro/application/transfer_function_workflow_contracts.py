"""Immutable contracts for the transfer-function application workflow."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from klausurbotpro.domain import (
    CommonTransferFunctionInput,
    Diagnostic,
    ParameterSubstitutions,
    RawTransferFunction,
    RawTransferFunctionCreationResult,
    RawTransferFunctionLimits,
    ReducedTransferFunction,
    RootAnalysisLimits,
    SeparatedTransferFunctionInput,
    StabilityAnalysisLimits,
    TransferFunctionInput,
    TransferFunctionReductionLimits,
    TransferFunctionReductionResult,
    TransferFunctionRootAnalysisResult,
    TransferFunctionStabilityAnalysisResult,
)
from klausurbotpro.parsing import ParserLimits


class WorkflowInputForm(StrEnum):
    """User-facing input layouts supported by the workflow."""

    COMMON = "common"
    SEPARATED = "separated"


class WorkflowStage(StrEnum):
    """Ordered processing stages."""

    PARSE = "parse"
    RAW_TRANSFER_FUNCTION = "raw_transfer_function"
    REDUCTION = "reduction"
    ROOT_ANALYSIS = "root_analysis"
    STABILITY_ANALYSIS = "stability_analysis"


WORKFLOW_STAGE_ORDER = (
    WorkflowStage.PARSE,
    WorkflowStage.RAW_TRANSFER_FUNCTION,
    WorkflowStage.REDUCTION,
    WorkflowStage.ROOT_ANALYSIS,
    WorkflowStage.STABILITY_ANALYSIS,
)


class WorkflowStageStatus(StrEnum):
    """Terminal state of one stage for the current operation."""

    NOT_EVALUATED = "not_evaluated"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    BLOCKED = "blocked"


class WorkflowValueOrigin(StrEnum):
    """Origin of a successfully available stage value."""

    COMPUTED = "computed"
    OVERRIDDEN = "overridden"


class WorkflowOverrideOriginKind(StrEnum):
    """Declared source of a manual intermediate value."""

    MANUAL = "manual"
    IMPORT = "import"
    TEST = "test"


class WorkflowDiagnosticCode(StrEnum):
    """Stable application-level diagnostic codes."""

    WORKFLOW_INVALID_REQUEST = "workflow.invalid_request"
    WORKFLOW_PARSE_FAILED = "workflow.parse_failed"
    WORKFLOW_RAW_FAILED = "workflow.raw_failed"
    WORKFLOW_REDUCTION_FAILED = "workflow.reduction_failed"
    WORKFLOW_ROOT_ANALYSIS_FAILED = "workflow.root_analysis_failed"
    WORKFLOW_STABILITY_ANALYSIS_FAILED = "workflow.stability_analysis_failed"
    WORKFLOW_INVALID_OVERRIDE = "workflow.invalid_override"
    WORKFLOW_OVERRIDE_CONTEXT_MISMATCH = "workflow.override_context_mismatch"
    WORKFLOW_INVALID_SUBSTITUTIONS = "workflow.invalid_substitutions"
    WORKFLOW_LIMIT_EXCEEDED = "workflow.limit_exceeded"
    WORKFLOW_RESOURCE_LIMIT_EXCEEDED = "workflow.resource_limit_exceeded"


@dataclass(frozen=True, slots=True)
class TransferFunctionWorkflowRequest:
    """Complete, UI-independent input for a new workflow."""

    input_form: WorkflowInputForm
    common_expression_text: str | None = None
    numerator_expression_text: str | None = None
    denominator_expression_text: str | None = None
    variable_name: str = "s"
    allowed_parameter_names: tuple[str, ...] = ()
    substitutions: ParameterSubstitutions | None = None
    field: str | None = None


@dataclass(frozen=True, slots=True)
class TransferFunctionWorkflowLimits:
    """Existing layer limits plus application-specific bounds."""

    parser: ParserLimits = ParserLimits()
    raw: RawTransferFunctionLimits = RawTransferFunctionLimits()
    reduction: TransferFunctionReductionLimits = TransferFunctionReductionLimits()
    root_analysis: RootAnalysisLimits = RootAnalysisLimits()
    stability_analysis: StabilityAnalysisLimits = StabilityAnalysisLimits()
    max_aggregated_diagnostics: int = 512
    max_override_reason_length: int = 1_000
    max_operation_sequence: int = 1_000_000

    def __post_init__(self) -> None:
        expected = (
            (self.parser, ParserLimits, "parser"),
            (self.raw, RawTransferFunctionLimits, "raw"),
            (
                self.reduction,
                TransferFunctionReductionLimits,
                "reduction",
            ),
            (self.root_analysis, RootAnalysisLimits, "root_analysis"),
            (
                self.stability_analysis,
                StabilityAnalysisLimits,
                "stability_analysis",
            ),
        )
        for value, value_type, name in expected:
            if type(value) is not value_type:
                raise TypeError(f"{name} has an invalid limits type.")
        for name in (
            "max_aggregated_diagnostics",
            "max_override_reason_length",
            "max_operation_sequence",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer.")


@dataclass(frozen=True, slots=True)
class OverrideProvenance:
    """Deterministic provenance attached to an accepted override."""

    origin_kind: WorkflowOverrideOriginKind
    reason: str
    sequence_number: int
    target_stage: WorkflowStage


@dataclass(frozen=True, slots=True)
class RawTransferFunctionOverride:
    value: RawTransferFunction
    provenance: OverrideProvenance


@dataclass(frozen=True, slots=True)
class ReducedTransferFunctionOverride:
    value: ReducedTransferFunction
    provenance: OverrideProvenance


@dataclass(frozen=True, slots=True)
class RootAnalysisOverride:
    value: TransferFunctionRootAnalysisResult
    provenance: OverrideProvenance


type TransferFunctionWorkflowOverride = (
    RawTransferFunctionOverride
    | ReducedTransferFunctionOverride
    | RootAnalysisOverride
)


@dataclass(frozen=True, slots=True)
class WorkflowStageRecord:
    """Terminal stage status, diagnostics, and active value provenance."""

    stage: WorkflowStage
    status: WorkflowStageStatus
    value_origin: WorkflowValueOrigin | None = None
    diagnostics: tuple[Diagnostic, ...] = ()
    override_provenance: OverrideProvenance | None = None
    diagnostic_provenances: tuple[OverrideProvenance | None, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "diagnostics", tuple(self.diagnostics))
        if type(self.stage) is not WorkflowStage:
            raise TypeError("stage must be a WorkflowStage.")
        if type(self.status) is not WorkflowStageStatus:
            raise TypeError("status must be a WorkflowStageStatus.")
        if self.value_origin is not None and (
            type(self.value_origin) is not WorkflowValueOrigin
        ):
            raise TypeError("value_origin must be a WorkflowValueOrigin or None.")
        if any(type(item) is not Diagnostic for item in self.diagnostics):
            raise TypeError("diagnostics must contain only Diagnostic values.")
        if self.status is WorkflowStageStatus.SUCCEEDED:
            if self.value_origin is None:
                raise ValueError("A successful stage requires a value origin.")
        elif self.value_origin is not None:
            raise ValueError("Only a successful stage can have a value origin.")
        if self.value_origin is WorkflowValueOrigin.OVERRIDDEN:
            if self.override_provenance is None:
                raise ValueError("An overridden value requires provenance.")
            if self.override_provenance.target_stage is not self.stage:
                raise ValueError("Override provenance targets another stage.")
        elif self.override_provenance is not None:
            raise ValueError("Computed or unavailable values have no override provenance.")
        diagnostic_provenances = tuple(self.diagnostic_provenances)
        if not diagnostic_provenances:
            diagnostic_provenances = tuple(
                self.override_provenance for _ in self.diagnostics
            )
        if len(diagnostic_provenances) != len(self.diagnostics):
            raise ValueError("Every diagnostic requires one provenance entry.")
        if any(
            item is not None and type(item) is not OverrideProvenance
            for item in diagnostic_provenances
        ):
            raise TypeError("Diagnostic provenance has an invalid type.")
        object.__setattr__(
            self,
            "diagnostic_provenances",
            diagnostic_provenances,
        )


@dataclass(frozen=True, slots=True)
class WorkflowDiagnosticEntry:
    """One unchanged diagnostic in deterministic workflow order."""

    stage: WorkflowStage
    local_index: int
    diagnostic: Diagnostic
    operation_sequence: int
    override_provenance: OverrideProvenance | None = None


@dataclass(frozen=True, slots=True)
class TransferFunctionWorkflowState:
    """Immutable snapshot after one complete workflow operation."""

    request: TransferFunctionWorkflowRequest
    substitutions: ParameterSubstitutions | None
    parsed_input: TransferFunctionInput | None
    raw_result: RawTransferFunctionCreationResult | None
    reduction_result: TransferFunctionReductionResult | None
    root_analysis_result: TransferFunctionRootAnalysisResult | None
    stability_analysis_result: TransferFunctionStabilityAnalysisResult | None
    stage_records: tuple[WorkflowStageRecord, ...]
    aggregated_diagnostics: tuple[WorkflowDiagnosticEntry, ...]
    operation_sequence: int
    active_reduced_value: ReducedTransferFunction | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "stage_records", tuple(self.stage_records))
        object.__setattr__(
            self,
            "aggregated_diagnostics",
            tuple(self.aggregated_diagnostics),
        )
        if tuple(record.stage for record in self.stage_records) != (
            WORKFLOW_STAGE_ORDER
        ):
            raise ValueError("stage_records must use the fixed workflow order.")
        if type(self.request) is not TransferFunctionWorkflowRequest:
            raise TypeError("request has an invalid type.")
        if self.substitutions is not None and (
            type(self.substitutions) is not ParameterSubstitutions
        ):
            raise TypeError("substitutions has an invalid type.")
        if self.parsed_input is not None and type(self.parsed_input) not in (
            CommonTransferFunctionInput,
            SeparatedTransferFunctionInput,
        ):
            raise TypeError("parsed_input has an invalid type.")
        if any(type(record) is not WorkflowStageRecord for record in self.stage_records):
            raise TypeError("stage_records contain an invalid type.")
        if (
            isinstance(self.operation_sequence, bool)
            or not isinstance(self.operation_sequence, int)
            or self.operation_sequence < 0
        ):
            raise ValueError("operation_sequence must be a nonnegative integer.")
        expected_entries = tuple(
            (
                record.stage,
                index,
                diagnostic,
                self.operation_sequence,
                record.diagnostic_provenances[index],
            )
            for record in self.stage_records
            for index, diagnostic in enumerate(record.diagnostics)
        )
        actual_entries = tuple(
            (
                entry.stage,
                entry.local_index,
                entry.diagnostic,
                entry.operation_sequence,
                entry.override_provenance,
            )
            for entry in self.aggregated_diagnostics
        )
        if actual_entries != expected_entries:
            raise ValueError(
                "aggregated_diagnostics must be derived from stage_records."
            )

    @property
    def raw_value(self) -> RawTransferFunction | None:
        return None if self.raw_result is None else self.raw_result.value

    @property
    def reduced_value(self) -> ReducedTransferFunction | None:
        if self.active_reduced_value is not None:
            return self.active_reduced_value
        if self.reduction_result is None:
            return None
        return self.reduction_result.reduced


__all__ = [
    "OverrideProvenance",
    "RawTransferFunctionOverride",
    "ReducedTransferFunctionOverride",
    "RootAnalysisOverride",
    "TransferFunctionWorkflowLimits",
    "TransferFunctionWorkflowOverride",
    "TransferFunctionWorkflowRequest",
    "TransferFunctionWorkflowState",
    "WorkflowDiagnosticCode",
    "WorkflowDiagnosticEntry",
    "WorkflowInputForm",
    "WorkflowOverrideOriginKind",
    "WorkflowStage",
    "WorkflowStageRecord",
    "WorkflowStageStatus",
    "WorkflowValueOrigin",
]
