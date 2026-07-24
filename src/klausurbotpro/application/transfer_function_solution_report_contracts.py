"""Immutable, SymPy-free contracts for transfer-function solution reports."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from klausurbotpro.application.transfer_function_workflow_contracts import (
    WorkflowOverrideOriginKind,
    WorkflowStage,
)
from klausurbotpro.domain import DiagnosticSeverity


class SolutionReportStatus(StrEnum):
    """Completeness of the whole paper-oriented report."""

    COMPLETE = "complete"
    PARTIAL = "partial"
    FAILED = "failed"


class SolutionSectionStatus(StrEnum):
    """Completeness of one report section."""

    COMPLETE = "complete"
    PARTIAL = "partial"
    FAILED = "failed"
    BLOCKED = "blocked"
    NOT_APPLICABLE = "not_applicable"


class SolutionSectionKind(StrEnum):
    """Fixed paper-oriented section order."""

    GIVEN = "given"
    TRANSFER_FUNCTION = "transfer_function"
    NUMERATOR_DENOMINATOR = "numerator_denominator"
    ZEROS = "zeros"
    POLES = "poles"
    POLE_REAL_PARTS = "pole_real_parts"
    STABILITY = "stability"
    DYNAMIC_BEHAVIOR = "dynamic_behavior"
    REDUCTION = "reduction"
    DOMAIN_EXCLUSIONS = "domain_exclusions"
    PREREQUISITES = "prerequisites"
    PARAMETER_SUBSTITUTIONS = "parameter_substitutions"
    SOURCES = "sources"
    WORKFLOW_NOTICES = "workflow_notices"


SOLUTION_SECTION_ORDER = tuple(SolutionSectionKind)


class ReportDiagnosticCode(StrEnum):
    """Stable report-level diagnostic codes."""

    REPORT_INVALID_WORKFLOW_STATE = "report.invalid_workflow_state"
    REPORT_LIMIT_EXCEEDED = "report.limit_exceeded"
    REPORT_UNSUPPORTED_VALUE = "report.unsupported_value"
    REPORT_MISSING_STAGE_RESULT = "report.missing_stage_result"
    REPORT_INCONSISTENT_STAGE = "report.inconsistent_stage"
    REPORT_RENDER_FAILED = "report.render_failed"


@dataclass(frozen=True, slots=True)
class ReportMathExpression:
    """One exact mathematical display value in both supported formats."""

    plaintext: str
    latex: str

    def __post_init__(self) -> None:
        if type(self.plaintext) is not str or not self.plaintext:
            raise ValueError("plaintext must be a non-empty exact string.")
        if type(self.latex) is not str or not self.latex:
            raise ValueError("latex must be a non-empty exact string.")


@dataclass(frozen=True, slots=True)
class TransferFunctionExpressionPair:
    """Exact numerator and denominator used by one reduction state."""

    numerator: ReportMathExpression
    denominator: ReportMathExpression

    def __post_init__(self) -> None:
        if type(self.numerator) is not ReportMathExpression:
            raise TypeError("numerator must be a ReportMathExpression.")
        if type(self.denominator) is not ReportMathExpression:
            raise TypeError("denominator must be a ReportMathExpression.")


@dataclass(frozen=True, slots=True)
class EquationLine:
    """A directly copyable mathematical equation."""

    left: ReportMathExpression
    relation: str
    right: ReportMathExpression
    identifier: str | None = None

    def __post_init__(self) -> None:
        _require_math(self.left, "left")
        _require_text(self.relation, "relation")
        _require_math(self.right, "right")
        _require_optional_text(self.identifier, "identifier")


@dataclass(frozen=True, slots=True)
class ConditionLine:
    """A structured prerequisite, exclusion, or criterion."""

    condition_kind: str
    expressions: tuple[ReportMathExpression, ...]
    relation: str

    def __post_init__(self) -> None:
        _require_text(self.condition_kind, "condition_kind")
        expressions = tuple(self.expressions)
        if not expressions or any(
            type(value) is not ReportMathExpression for value in expressions
        ):
            raise ValueError("A condition requires exact report expressions.")
        _require_text(self.relation, "relation")
        object.__setattr__(self, "expressions", expressions)


@dataclass(frozen=True, slots=True)
class TransformationLine:
    """One existing structured reduction step translated for paper."""

    before: TransferFunctionExpressionPair
    operation_kind: str
    factor_or_operation: ReportMathExpression | None
    after: TransferFunctionExpressionPair
    retained_prerequisites: tuple[ConditionLine, ...] = ()
    retained_domain_exclusions: tuple[ConditionLine, ...] = ()

    def __post_init__(self) -> None:
        if type(self.before) is not TransferFunctionExpressionPair:
            raise TypeError("before must be a transfer-function pair.")
        _require_text(self.operation_kind, "operation_kind")
        if self.factor_or_operation is not None:
            _require_math(self.factor_or_operation, "factor_or_operation")
        if type(self.after) is not TransferFunctionExpressionPair:
            raise TypeError("after must be a transfer-function pair.")
        prerequisites = _condition_tuple(
            self.retained_prerequisites,
            "retained_prerequisites",
        )
        exclusions = _condition_tuple(
            self.retained_domain_exclusions,
            "retained_domain_exclusions",
        )
        object.__setattr__(self, "retained_prerequisites", prerequisites)
        object.__setattr__(self, "retained_domain_exclusions", exclusions)


@dataclass(frozen=True, slots=True)
class ResultLine:
    """One exact result with optional non-authoritative approximation."""

    label: str
    exact_value: ReportMathExpression
    numerical_approximation: str | None = None
    multiplicity: int | None = None
    source_role: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.label, "label")
        _require_math(self.exact_value, "exact_value")
        _require_optional_text(
            self.numerical_approximation,
            "numerical_approximation",
        )
        if self.multiplicity is not None and (
            type(self.multiplicity) is not int or self.multiplicity <= 0
        ):
            raise ValueError("multiplicity must be a positive real int.")
        _require_optional_text(self.source_role, "source_role")


@dataclass(frozen=True, slots=True)
class ApproximationLine:
    """One presentation-only numerical approximation of an exact result."""

    label: str
    value: ReportMathExpression

    def __post_init__(self) -> None:
        _require_text(self.label, "label")
        _require_math(self.value, "value")


@dataclass(frozen=True, slots=True)
class OverrideLine:
    """Visible provenance for an active overridden workflow value."""

    target_stage: WorkflowStage
    origin_kind: WorkflowOverrideOriginKind
    reason: str

    def __post_init__(self) -> None:
        if type(self.target_stage) is not WorkflowStage:
            raise TypeError("target_stage must be a WorkflowStage.")
        if type(self.origin_kind) is not WorkflowOverrideOriginKind:
            raise TypeError("origin_kind must be an override origin.")
        _require_text(self.reason, "reason")


@dataclass(frozen=True, slots=True)
class WarningLine:
    """A classified workflow or report notice."""

    code: str
    severity: DiagnosticSeverity
    affected_stage: WorkflowStage | None
    statement: str

    def __post_init__(self) -> None:
        _require_text(self.code, "code")
        if type(self.severity) is not DiagnosticSeverity:
            raise TypeError("severity must be a DiagnosticSeverity.")
        if self.affected_stage is not None and (
            type(self.affected_stage) is not WorkflowStage
        ):
            raise TypeError("affected_stage must be a WorkflowStage or None.")
        _require_text(self.statement, "statement")


@dataclass(frozen=True, slots=True)
class SourceReferenceLine:
    """An existing structured official source reference."""

    document_name: str
    page: int | None
    location: str
    claim: str

    def __post_init__(self) -> None:
        _require_text(self.document_name, "document_name")
        if self.page is not None and (
            type(self.page) is not int or self.page <= 0
        ):
            raise ValueError("page must be a positive real int or None.")
        _require_text(self.location, "location")
        _require_text(self.claim, "claim")


type SolutionLine = (
    EquationLine
    | TransformationLine
    | ResultLine
    | ApproximationLine
    | ConditionLine
    | OverrideLine
    | WarningLine
    | SourceReferenceLine
)

_SOLUTION_LINE_TYPES = (
    EquationLine,
    TransformationLine,
    ResultLine,
    ApproximationLine,
    ConditionLine,
    OverrideLine,
    WarningLine,
    SourceReferenceLine,
)


@dataclass(frozen=True, slots=True)
class SolutionSection:
    """One deterministically positioned report section."""

    kind: SolutionSectionKind
    status: SolutionSectionStatus
    lines: tuple[SolutionLine, ...] = ()
    workflow_stage: WorkflowStage | None = None

    def __post_init__(self) -> None:
        if type(self.kind) is not SolutionSectionKind:
            raise TypeError("kind must be a SolutionSectionKind.")
        if type(self.status) is not SolutionSectionStatus:
            raise TypeError("status must be a SolutionSectionStatus.")
        lines = tuple(self.lines)
        if any(type(line) not in _SOLUTION_LINE_TYPES for line in lines):
            raise TypeError("A section contains an unsupported line type.")
        if self.workflow_stage is not None and (
            type(self.workflow_stage) is not WorkflowStage
        ):
            raise TypeError("workflow_stage must be a WorkflowStage or None.")
        if self.status in (
            SolutionSectionStatus.COMPLETE,
            SolutionSectionStatus.PARTIAL,
            SolutionSectionStatus.FAILED,
        ) and not lines:
            raise ValueError("An evaluated section requires at least one line.")
        if self.status in (
            SolutionSectionStatus.BLOCKED,
            SolutionSectionStatus.NOT_APPLICABLE,
        ) and lines:
            raise ValueError("An unavailable section cannot contain lines.")
        object.__setattr__(self, "lines", lines)


@dataclass(frozen=True, slots=True)
class ReportDiagnostic:
    """A report construction diagnostic separate from workflow diagnostics."""

    code: ReportDiagnosticCode
    severity: DiagnosticSeverity
    message: str
    affected_section: SolutionSectionKind | None = None
    details: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if type(self.code) is not ReportDiagnosticCode:
            raise TypeError("code must be a ReportDiagnosticCode.")
        if type(self.severity) is not DiagnosticSeverity:
            raise TypeError("severity must be a DiagnosticSeverity.")
        _require_text(self.message, "message")
        if self.affected_section is not None and (
            type(self.affected_section) is not SolutionSectionKind
        ):
            raise TypeError(
                "affected_section must be a SolutionSectionKind or None."
            )
        details = tuple(self.details)
        if any(
            type(item) is not tuple
            or len(item) != 2
            or any(type(value) is not str for value in item)
            for item in details
        ):
            raise TypeError("details must contain string pairs.")
        object.__setattr__(self, "details", details)


@dataclass(frozen=True, slots=True)
class SolutionReportLimits:
    """Finite presentation limits; no process timeout is implied."""

    max_sections: int = 14
    max_total_lines: int = 512
    max_lines_per_section: int = 128
    max_expression_length: int = 4096
    max_reduction_steps: int = 32
    max_roots: int = 128
    max_conditions: int = 128
    max_source_references: int = 32
    max_warning_lines: int = 256

    def __post_init__(self) -> None:
        for name in self.__dataclass_fields__:
            value = getattr(self, name)
            if type(value) is not int or value <= 0:
                raise ValueError(f"{name} must be a positive real int.")


@dataclass(frozen=True, slots=True)
class TransferFunctionSolutionReport:
    """A deterministic, paper-oriented view of one workflow state."""

    status: SolutionReportStatus
    sections: tuple[SolutionSection, ...]
    diagnostics: tuple[ReportDiagnostic, ...] = ()

    def __post_init__(self) -> None:
        if type(self.status) is not SolutionReportStatus:
            raise TypeError("status must be a SolutionReportStatus.")
        sections = tuple(self.sections)
        if any(type(section) is not SolutionSection for section in sections):
            raise TypeError("sections must contain SolutionSection values.")
        kinds = tuple(section.kind for section in sections)
        positions = tuple(SOLUTION_SECTION_ORDER.index(kind) for kind in kinds)
        if len(set(kinds)) != len(kinds) or positions != tuple(
            sorted(positions)
        ):
            raise ValueError("sections must follow the fixed unique order.")
        diagnostics = tuple(self.diagnostics)
        if any(
            type(diagnostic) is not ReportDiagnostic
            for diagnostic in diagnostics
        ):
            raise TypeError("diagnostics contain an invalid value.")
        if self.status is SolutionReportStatus.COMPLETE and diagnostics:
            raise ValueError("A complete report cannot have report errors.")
        object.__setattr__(self, "sections", sections)
        object.__setattr__(self, "diagnostics", diagnostics)

    def section(self, kind: SolutionSectionKind) -> SolutionSection | None:
        """Return a section by its stable kind."""

        return next(
            (section for section in self.sections if section.kind is kind),
            None,
        )


def _require_text(value: object, name: str) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{name} must be a non-empty string.")


def _require_optional_text(value: object, name: str) -> None:
    if value is not None:
        _require_text(value, name)


def _require_math(value: object, name: str) -> None:
    if type(value) is not ReportMathExpression:
        raise TypeError(f"{name} must be a ReportMathExpression.")


def _condition_tuple(
    values: object,
    name: str,
) -> tuple[ConditionLine, ...]:
    result: tuple[object, ...] = tuple(values)  # type: ignore[arg-type]
    if any(type(value) is not ConditionLine for value in result):
        raise TypeError(f"{name} must contain ConditionLine values.")
    return result  # type: ignore[return-value]


__all__ = [
    "ApproximationLine",
    "ConditionLine",
    "EquationLine",
    "OverrideLine",
    "ReportDiagnostic",
    "ReportDiagnosticCode",
    "ReportMathExpression",
    "ResultLine",
    "SOLUTION_SECTION_ORDER",
    "SolutionLine",
    "SolutionReportLimits",
    "SolutionReportStatus",
    "SolutionSection",
    "SolutionSectionKind",
    "SolutionSectionStatus",
    "SourceReferenceLine",
    "TransferFunctionExpressionPair",
    "TransferFunctionSolutionReport",
    "TransformationLine",
    "WarningLine",
]
