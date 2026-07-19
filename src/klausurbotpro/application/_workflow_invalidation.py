"""Small helpers for fixed-order downstream invalidation."""

from __future__ import annotations

from klausurbotpro.application.transfer_function_workflow_contracts import (
    WORKFLOW_STAGE_ORDER,
    WorkflowStage,
    WorkflowStageRecord,
    WorkflowStageStatus,
)


def blocked_records_after(
    stage: WorkflowStage,
) -> tuple[WorkflowStageRecord, ...]:
    """Return terminal BLOCKED records after a failed stage."""

    index = WORKFLOW_STAGE_ORDER.index(stage)
    return tuple(
        WorkflowStageRecord(item, WorkflowStageStatus.BLOCKED)
        for item in WORKFLOW_STAGE_ORDER[index + 1 :]
    )


__all__ = ["blocked_records_after"]
