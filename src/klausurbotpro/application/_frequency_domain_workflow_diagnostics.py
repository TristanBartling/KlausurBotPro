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


def nyquist_parameters_required_diagnostic(
    parameter_names: tuple[str, ...],
    *,
    field: str | None,
) -> Diagnostic:
    """Explain why an optional numerical Nyquist evaluation was skipped."""

    if not parameter_names:
        raise ValueError("parameter_names must not be empty.")
    joined = ", ".join(parameter_names)
    missing_clause = (
        f"der Parameter {joined} nicht numerisch belegt ist"
        if len(parameter_names) == 1
        else f"die Parameter {joined} nicht numerisch belegt sind"
    )
    return Diagnostic(
        DiagnosticSeverity.WARNING,
        cast(
            DiagnosticCode,
            FrequencyDomainWorkflowDiagnosticCode.NYQUIST_NUMERIC_PARAMETERS_REQUIRED,
        ),
        (
            f"Die numerische Nyquist-Auswertung wurde nicht gestartet, weil "
            f"{missing_clause}. Belege {joined} numerisch, um den "
            "Nyquist-Plot und Zahlenwerte zu berechnen. Es wurde kein Ersatzwert "
            "angenommen; bereits bestimmte symbolische Teilresultate bleiben verwendbar."
        ),
        field,
        (("parameters", joined),),
    )


__all__ = [
    "frequency_workflow_diagnostic",
    "nyquist_parameters_required_diagnostic",
    "owned_diagnostics",
]
