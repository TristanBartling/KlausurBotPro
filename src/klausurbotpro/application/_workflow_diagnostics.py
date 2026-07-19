"""Deterministic diagnostic construction and aggregation."""

from __future__ import annotations

from typing import cast

from klausurbotpro.application.transfer_function_workflow_contracts import (
    WorkflowDiagnosticCode,
    WorkflowDiagnosticEntry,
    WorkflowStage,
    WorkflowStageRecord,
)
from klausurbotpro.domain import (
    Diagnostic,
    DiagnosticCode,
    DiagnosticSeverity,
)


def application_diagnostic(
    code: WorkflowDiagnosticCode,
    message: str,
    *,
    field: str | None = None,
    details: tuple[tuple[str, str], ...] = (),
) -> Diagnostic:
    """Create a Diagnostic while retaining an application-owned stable code."""

    return Diagnostic(
        DiagnosticSeverity.ERROR,
        cast(DiagnosticCode, code),
        message,
        field,
        details,
    )


def aggregate_diagnostics(
    records: tuple[WorkflowStageRecord, ...],
    operation_sequence: int,
) -> tuple[WorkflowDiagnosticEntry, ...]:
    """Derive entries solely from fixed-order stage records."""

    return tuple(
        WorkflowDiagnosticEntry(
            stage=record.stage,
            local_index=index,
            diagnostic=diagnostic,
            operation_sequence=operation_sequence,
            override_provenance=record.diagnostic_provenances[index],
        )
        for record in records
        for index, diagnostic in enumerate(record.diagnostics)
    )


def failure_code_for_diagnostics(
    diagnostics: tuple[Diagnostic, ...],
    stage_code: WorkflowDiagnosticCode,
) -> WorkflowDiagnosticCode:
    values = tuple(item.code.value for item in diagnostics)
    if any(value.endswith("resource_limit_exceeded") for value in values):
        return WorkflowDiagnosticCode.WORKFLOW_RESOURCE_LIMIT_EXCEEDED
    if any(value.endswith("limit_exceeded") for value in values):
        return WorkflowDiagnosticCode.WORKFLOW_LIMIT_EXCEEDED
    return stage_code


def stage_failure_diagnostics(
    stage: WorkflowStage,
    diagnostics: tuple[Diagnostic, ...],
    stage_code: WorkflowDiagnosticCode,
    *,
    field: str | None,
) -> tuple[Diagnostic, ...]:
    code = failure_code_for_diagnostics(diagnostics, stage_code)
    application = application_diagnostic(
        code,
        f"Die Workflow-Stufe '{stage.value}' ist fehlgeschlagen.",
        field=field,
    )
    return (*diagnostics, application)


__all__ = [
    "aggregate_diagnostics",
    "application_diagnostic",
    "stage_failure_diagnostics",
]
