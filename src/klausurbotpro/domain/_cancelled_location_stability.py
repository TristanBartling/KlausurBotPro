"""Separate, non-status-changing classification of cancelled locations."""

from __future__ import annotations

from klausurbotpro.domain._exact_real_part_classifier import (
    classify_exact_real_part,
)
from klausurbotpro.domain.diagnostics import (
    Diagnostic,
    DiagnosticCode,
    DiagnosticSeverity,
)
from klausurbotpro.domain.root_analysis_contracts import (
    PolynomialRootStatus,
    RootAnalysisGroup,
)
from klausurbotpro.domain.stability_analysis_contracts import (
    CancelledLocationNotice,
    RealPartSign,
    StabilityAnalysisLimits,
    StabilityReason,
    StabilityReasonCode,
)

_NOTICE_TEXT = (
    "Die Stelle ist kein reduzierter Pol und verändert die "
    "E/A-Stabilitätsklassifikation der reduzierten Übertragungsfunktion nicht. "
    "Möglicher Hinweis auf verborgene interne Dynamik; I-Stabilität ist aus "
    "diesem Ergebnis nicht ableitbar."
)


def analyze_cancelled_locations(
    group: RootAnalysisGroup,
    limits: StabilityAnalysisLimits,
    *,
    field: str | None,
) -> tuple[
    tuple[CancelledLocationNotice, ...],
    tuple[Diagnostic, ...],
    int,
]:
    """Classify proven locations separately from reduced-pole aggregation."""

    diagnostics: list[Diagnostic] = []
    notices: list[CancelledLocationNotice] = []
    evidence_nodes = 0
    if group.status is PolynomialRootStatus.NOT_EVALUATED:
        diagnostics.append(
            Diagnostic(
                DiagnosticSeverity.INFO,
                DiagnosticCode.STABILITY_ANALYSIS_CANCELLED_LOCATIONS_NOT_EVALUATED,
                "Gekürzte Stellen wurden in der Wurzelanalyse nicht ausgewertet.",
                field,
            )
        )
        return (), tuple(diagnostics), 0
    if group.status is PolynomialRootStatus.SYMBOLIC_UNDETERMINED:
        diagnostics.append(
            Diagnostic(
                DiagnosticSeverity.WARNING,
                DiagnosticCode.STABILITY_ANALYSIS_CANCELLED_LOCATION_UNDETERMINED,
                "Mindestens eine gekürzte Stelle ist symbolisch unbestimmt.",
                field,
            )
        )

    for analysis in group.analyses:
        for occurrence in analysis.roots:
            classified = classify_exact_real_part(occurrence.value, limits)
            evidence_nodes += classified.evidence_nodes
            if classified.sign is RealPartSign.NEGATIVE:
                continue
            reason = StabilityReason(
                StabilityReasonCode.REAL_PART_UNDETERMINED
                if classified.sign is RealPartSign.UNDETERMINED
                else StabilityReasonCode.SIMPLE_IMAGINARY_AXIS_POLE
                if classified.sign is RealPartSign.ZERO
                else StabilityReasonCode.RIGHT_HALF_PLANE_POLE,
                _NOTICE_TEXT,
            )
            notices.append(
                CancelledLocationNotice(
                    occurrence,
                    classified.exact_real_part,
                    classified.sign,
                    classified.evidence_kind,
                    reason,
                )
            )
            diagnostics.append(
                Diagnostic(
                    DiagnosticSeverity.WARNING,
                    (
                        DiagnosticCode.STABILITY_ANALYSIS_CANCELLED_LOCATION_UNDETERMINED
                        if classified.sign is RealPartSign.UNDETERMINED
                        else DiagnosticCode.STABILITY_ANALYSIS_CANCELLED_LOCATION_NONNEGATIVE
                    ),
                    _NOTICE_TEXT,
                    field,
                    (("root_index", str(occurrence.index)),),
                )
            )
    return tuple(notices), tuple(diagnostics), evidence_nodes


__all__ = ["analyze_cancelled_locations"]
