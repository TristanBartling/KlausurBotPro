"""Exact, source-bound stability classification of already analyzed poles."""

from __future__ import annotations

from decimal import Decimal

from klausurbotpro.domain._cancelled_location_stability import (
    analyze_cancelled_locations,
)
from klausurbotpro.domain._exact_real_part_classifier import (
    RealPartClassificationLimitError,
    classify_exact_real_part,
)
from klausurbotpro.domain._stability_analysis_validation import (
    StabilityLimitError,
    StabilityValidationError,
    validate_root_analysis,
)
from klausurbotpro.domain.diagnostics import (
    Diagnostic,
    DiagnosticCode,
    DiagnosticSeverity,
)
from klausurbotpro.domain.root_analysis_contracts import (
    NumericalRootEstimate,
    PolynomialRootStatus,
    TransferFunctionRootAnalysisResult,
)
from klausurbotpro.domain.stability_analysis_contracts import (
    CancelledLocationNotice,
    PoleStabilityContribution,
    PoleStabilityContributionKind,
    RealPartSign,
    StabilityAnalysisLimits,
    StabilityReason,
    StabilityReasonCode,
    StabilitySourceReference,
    StabilityStatus,
    TransferFunctionStabilityAnalysisResult,
)

_RESOURCE_ERRORS = (MemoryError, RecursionError, OverflowError)
_DEFAULT_LIMITS = StabilityAnalysisLimits()
_SOURCE_REFERENCES = (
    StabilitySourceReference(
        document_name="skript.pdf",
        page=107,
        location="Theorem 5.12",
        claim="E/A-Stabilität genau dann, wenn alle Pole Re(s_j) < 0 erfüllen.",
    ),
    StabilitySourceReference(
        document_name="skript.pdf",
        page=102,
        location="Korollar 5.5",
        claim=(
            "Stabilität bei Re(lambda)<=0 verlangt Jordanblöcke der Länge 1."
        ),
    ),
    StabilitySourceReference(
        document_name="Regelungstechnik_Tutorium_komplett.pdf",
        location="Tutorium 09 – Stabilität I, Aufgabe 2",
        claim=(
            "Einfache Pole bei 0 bzw. auf der imaginären Achse werden "
            "grenzstabil genannt."
        ),
    ),
)


class TransferFunctionStabilityAnalyzer:
    """Classify reduced exact poles without computing or changing roots."""

    def __init__(
        self,
        limits: StabilityAnalysisLimits = _DEFAULT_LIMITS,
    ) -> None:
        if type(limits) is not StabilityAnalysisLimits:
            raise TypeError("limits must be StabilityAnalysisLimits.")
        self._limits = limits

    def analyze(
        self,
        root_analysis: TransferFunctionRootAnalysisResult,
        *,
        field: str | None = None,
    ) -> TransferFunctionStabilityAnalysisResult:
        """Return a source-bound classification or a structured failure."""

        try:
            validate_root_analysis(root_analysis, self._limits)
            assert root_analysis.reduced_poles is not None
            poles = root_analysis.reduced_poles
            notices, cancelled_diagnostics, cancelled_evidence = (
                analyze_cancelled_locations(
                    root_analysis.cancelled_locations,
                    self._limits,
                    field=field,
                )
            )
            if poles.status is PolynomialRootStatus.SYMBOLIC_UNDETERMINED:
                symbolic_diagnostics = (
                    Diagnostic(
                        DiagnosticSeverity.WARNING,
                        DiagnosticCode.STABILITY_ANALYSIS_SYMBOLIC_UNDETERMINED,
                        "Die reduzierten Pole sind symbolisch unbestimmt.",
                        field,
                    ),
                    *cancelled_diagnostics,
                )
                self._enforce_output_limits(
                    root_analysis,
                    (),
                    notices,
                    symbolic_diagnostics,
                    cancelled_evidence,
                )
                return self._success(
                    root_analysis,
                    StabilityStatus.SYMBOLIC_UNDETERMINED,
                    (),
                    notices,
                    symbolic_diagnostics,
                )

            contributions: list[PoleStabilityContribution] = []
            diagnostics: list[Diagnostic] = []
            evidence_nodes = 0
            for occurrence in poles.roots:
                classified = classify_exact_real_part(
                    occurrence.value,
                    self._limits,
                )
                evidence_nodes += classified.evidence_nodes
                contribution = _contribution_for(
                    occurrence.multiplicity,
                    classified.sign,
                )
                reason = _reason_for(
                    occurrence.multiplicity,
                    classified.sign,
                )
                contributions.append(
                    PoleStabilityContribution(
                        occurrence,
                        classified.exact_real_part,
                        classified.sign,
                        classified.evidence_kind,
                        occurrence.multiplicity,
                        contribution,
                        reason,
                    )
                )
                if classified.sign is RealPartSign.UNDETERMINED:
                    diagnostics.append(
                        Diagnostic(
                            DiagnosticSeverity.WARNING,
                            DiagnosticCode.STABILITY_ANALYSIS_REAL_PART_UNDETERMINED,
                            "Das Vorzeichen des Polrealteils ist nicht exakt "
                            "oder zertifiziert entscheidbar.",
                            field,
                            (("root_index", str(occurrence.index)),),
                        )
                    )
                contradiction = _numeric_contradiction(
                    classified.sign,
                    poles.numerical_estimates,
                    occurrence.index,
                )
                if contradiction:
                    diagnostics.append(
                        Diagnostic(
                            DiagnosticSeverity.WARNING,
                            DiagnosticCode.STABILITY_ANALYSIS_NUMERIC_CONTRADICTION,
                            "Die numerische Gegenprüfung widerspricht dem "
                            "autoritativen exakten Realteilzeichen.",
                            field,
                            (("root_index", str(occurrence.index)),),
                        )
                    )

            status = _aggregate(tuple(contributions))
            if not contributions:
                diagnostics.append(
                    Diagnostic(
                        DiagnosticSeverity.INFO,
                        DiagnosticCode.STABILITY_ANALYSIS_NO_POLES,
                        "Die reduzierte Übertragungsfunktion besitzt keine Pole.",
                        field,
                    )
                )
            if status is StabilityStatus.BORDERLINE_STABLE:
                diagnostics.append(
                    Diagnostic(
                        DiagnosticSeverity.INFO,
                        DiagnosticCode.STABILITY_ANALYSIS_BORDERLINE_NOT_EA_STABLE,
                        "Grenzstabilität ist ausdrücklich keine E/A-/BIBO-Stabilität.",
                        field,
                    )
                )
            if status is StabilityStatus.SYMBOLIC_UNDETERMINED:
                diagnostics.append(
                    Diagnostic(
                        DiagnosticSeverity.WARNING,
                        DiagnosticCode.STABILITY_ANALYSIS_SYMBOLIC_UNDETERMINED,
                        "Mindestens ein erforderliches Realteilzeichen ist "
                        "nicht entscheidbar.",
                        field,
                    )
                )

            evidence_nodes += cancelled_evidence
            diagnostics.extend(cancelled_diagnostics)
            self._enforce_output_limits(
                root_analysis,
                tuple(contributions),
                notices,
                tuple(diagnostics),
                evidence_nodes,
            )
            return self._success(
                root_analysis,
                status,
                tuple(contributions),
                notices,
                tuple(diagnostics),
            )
        except TypeError:
            if type(root_analysis) is not TransferFunctionRootAnalysisResult:
                return self._failure(
                    None,
                    DiagnosticCode.STABILITY_ANALYSIS_INVALID_ROOT_ANALYSIS,
                    "Die Wurzelanalyse besitzt einen ungültigen Typ.",
                    field,
                )
            raise
        except StabilityValidationError as error:
            return self._failure(
                root_analysis,
                DiagnosticCode.STABILITY_ANALYSIS_INVALID_ROOT_ANALYSIS,
                "Das Wurzelanalyseergebnis ist fehlgeschlagen oder manipuliert.",
                field,
                error,
            )
        except (StabilityLimitError, RealPartClassificationLimitError) as error:
            return self._failure(
                root_analysis,
                DiagnosticCode.STABILITY_ANALYSIS_LIMIT_EXCEEDED,
                "Eine konfigurierte Grenze der Stabilitätsanalyse wurde überschritten.",
                field,
                error,
            )
        except _RESOURCE_ERRORS as error:
            return self._failure(
                root_analysis,
                DiagnosticCode.STABILITY_ANALYSIS_RESOURCE_LIMIT_EXCEEDED,
                "Die Stabilitätsanalyse überschreitet verfügbare Ressourcen.",
                field,
                error,
            )

    def _enforce_output_limits(
        self,
        root_analysis: TransferFunctionRootAnalysisResult,
        contributions: tuple[PoleStabilityContribution, ...],
        notices: tuple[CancelledLocationNotice, ...],
        diagnostics: tuple[Diagnostic, ...],
        evidence_nodes: int,
    ) -> None:
        if evidence_nodes > self._limits.max_evidence_nodes:
            raise StabilityLimitError("max_evidence_nodes")
        result_items = (
            len(contributions)
            + len(notices)
            + len(root_analysis.retained_domain_exclusions.analyses)
            + len(_SOURCE_REFERENCES)
        )
        if result_items > self._limits.max_result_items:
            raise StabilityLimitError("max_result_items")
        if len(diagnostics) > self._limits.max_diagnostics:
            raise StabilityLimitError("max_diagnostics")

    def _success(
        self,
        root_analysis: TransferFunctionRootAnalysisResult,
        status: StabilityStatus,
        contributions: tuple[PoleStabilityContribution, ...],
        notices: tuple[CancelledLocationNotice, ...],
        diagnostics: tuple[Diagnostic, ...],
    ) -> TransferFunctionStabilityAnalysisResult:
        return TransferFunctionStabilityAnalysisResult._create(
            root_analysis=root_analysis,
            status=status,
            pole_contributions=contributions,
            cancelled_location_notices=notices,
            retained_domain_exclusions=root_analysis.retained_domain_exclusions,
            source_references=_SOURCE_REFERENCES,
            diagnostics=diagnostics,
        )

    @staticmethod
    def _failure(
        root_analysis: TransferFunctionRootAnalysisResult | None,
        code: DiagnosticCode,
        message: str,
        field: str | None,
        error: BaseException | None = None,
    ) -> TransferFunctionStabilityAnalysisResult:
        details = () if error is None else (("detail", str(error)),)
        return TransferFunctionStabilityAnalysisResult._create(
            root_analysis=root_analysis,
            status=None,
            diagnostics=(
                Diagnostic(
                    DiagnosticSeverity.ERROR,
                    code,
                    message,
                    field,
                    details,
                ),
            ),
        )


def _contribution_for(
    multiplicity: int,
    sign: RealPartSign,
) -> PoleStabilityContributionKind:
    if sign is RealPartSign.NEGATIVE:
        return PoleStabilityContributionKind.SUPPORTS_STABLE
    if sign is RealPartSign.POSITIVE or (
        sign is RealPartSign.ZERO and multiplicity > 1
    ):
        return PoleStabilityContributionKind.CAUSES_UNSTABLE
    if sign is RealPartSign.ZERO:
        return PoleStabilityContributionKind.SUPPORTS_BORDERLINE
    return PoleStabilityContributionKind.CAUSES_UNDETERMINED


def _reason_for(multiplicity: int, sign: RealPartSign) -> StabilityReason:
    if sign is RealPartSign.NEGATIVE:
        return StabilityReason(
            StabilityReasonCode.STRICTLY_LEFT_HALF_PLANE,
            "Der Pol liegt strikt in der linken Halbebene.",
        )
    if sign is RealPartSign.POSITIVE:
        return StabilityReason(
            StabilityReasonCode.RIGHT_HALF_PLANE_POLE,
            "Der Pol liegt in der rechten Halbebene.",
        )
    if sign is RealPartSign.ZERO and multiplicity > 1:
        return StabilityReason(
            StabilityReasonCode.REPEATED_IMAGINARY_AXIS_POLE,
            "Der Pol liegt auf der imaginären Achse und besitzt algebraische "
            "Multiplizität größer als 1. Der entsprechende Zeitanteil enthält "
            "einen polynomialen Faktor in t; dies ist nicht der einfache "
            "grenzstabile Fall.",
        )
    if sign is RealPartSign.ZERO:
        return StabilityReason(
            StabilityReasonCode.SIMPLE_IMAGINARY_AXIS_POLE,
            "Der einfache Pol liegt auf der imaginären Achse.",
        )
    return StabilityReason(
        StabilityReasonCode.REAL_PART_UNDETERMINED,
        "Das Realteilzeichen ist nicht exakt oder zertifiziert entscheidbar.",
    )


def _aggregate(
    contributions: tuple[PoleStabilityContribution, ...],
) -> StabilityStatus:
    if any(
        item.contribution is PoleStabilityContributionKind.CAUSES_UNSTABLE
        for item in contributions
    ):
        return StabilityStatus.UNSTABLE
    if any(
        item.contribution is PoleStabilityContributionKind.CAUSES_UNDETERMINED
        for item in contributions
    ):
        return StabilityStatus.SYMBOLIC_UNDETERMINED
    if not contributions or all(
        item.real_part_sign is RealPartSign.NEGATIVE for item in contributions
    ):
        return StabilityStatus.STABLE
    return StabilityStatus.BORDERLINE_STABLE


def _numeric_contradiction(
    sign: RealPartSign,
    estimates: tuple[NumericalRootEstimate, ...],
    index: int,
) -> bool:
    if sign not in (RealPartSign.NEGATIVE, RealPartSign.POSITIVE):
        return False
    if not estimates:
        return False
    value = Decimal(estimates[index].real)
    return (sign is RealPartSign.NEGATIVE and value > 0) or (
        sign is RealPartSign.POSITIVE and value < 0
    )


__all__ = ["TransferFunctionStabilityAnalyzer"]
