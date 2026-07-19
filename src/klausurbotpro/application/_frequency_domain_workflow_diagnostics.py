"""Application-owned diagnostics for the frequency-domain workflow."""

from __future__ import annotations

from typing import cast

from klausurbotpro.application.frequency_domain_workflow_contracts import (
    FrequencyDomainWorkflowDiagnosticCode,
)
from klausurbotpro.domain import Diagnostic, DiagnosticCode, DiagnosticSeverity


def frequency_workflow_diagnostic(
    code: FrequencyDomainWorkflowDiagnosticCode,
    message: str,
    *,
    field: str | None = None,
    details: tuple[tuple[str, str], ...] = (),
) -> Diagnostic:
    return Diagnostic(
        DiagnosticSeverity.ERROR,
        cast(DiagnosticCode, code),
        message,
        field,
        details,
    )


def owned_diagnostics(
    diagnostics: tuple[Diagnostic, ...],
    upstream: tuple[Diagnostic, ...],
) -> tuple[Diagnostic, ...]:
    """Remove one exact embedded upstream prefix from a domain aggregate."""

    if diagnostics[: len(upstream)] != upstream:
        raise ValueError("Embedded upstream diagnostics are inconsistent.")
    return diagnostics[len(upstream) :]


__all__ = ["frequency_workflow_diagnostic", "owned_diagnostics"]
