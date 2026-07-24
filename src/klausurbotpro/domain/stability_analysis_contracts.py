"""Public, SymPy-free contracts for exact transfer-function stability analysis."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256

from klausurbotpro.domain.diagnostics import Diagnostic, DiagnosticSeverity
from klausurbotpro.domain.expression import ExactExpression
from klausurbotpro.domain.root_analysis_contracts import (
    RootAnalysisGroup,
    RootOccurrence,
    TransferFunctionRootAnalysisResult,
)


class StabilityStatus(StrEnum):
    """Source-bound stability classification of the reduced poles."""

    STABLE = "stable"
    BORDERLINE_STABLE = "borderline_stable"
    UNSTABLE = "unstable"
    SYMBOLIC_UNDETERMINED = "symbolic_undetermined"


class RealPartSign(StrEnum):
    """Exactly or certifiably established sign of a root's real part."""

    NEGATIVE = "negative"
    ZERO = "zero"
    POSITIVE = "positive"
    UNDETERMINED = "undetermined"


class StabilityEvidenceKind(StrEnum):
    """Kind of authoritative evidence used for a pole classification."""

    EXPLICIT_EXACT_REAL_PART = "explicit_exact_real_part"
    ROOTOF_EXACT_PREDICATE = "rootof_exact_predicate"
    ROOTOF_CERTIFIED_INTERVAL = "rootof_certified_interval"
    NO_POLES = "no_poles"
    SYMBOLIC_ROOT_ANALYSIS = "symbolic_root_analysis"


class PoleStabilityContributionKind(StrEnum):
    """Effect of one reduced pole on the aggregate status."""

    SUPPORTS_STABLE = "supports_stable"
    SUPPORTS_BORDERLINE = "supports_borderline"
    CAUSES_UNSTABLE = "causes_unstable"
    CAUSES_UNDETERMINED = "causes_undetermined"


class StabilityReasonCode(StrEnum):
    """Stable structured reason independent of presentation prose."""

    STRICTLY_LEFT_HALF_PLANE = "strictly_left_half_plane"
    SIMPLE_IMAGINARY_AXIS_POLE = "simple_imaginary_axis_pole"
    RIGHT_HALF_PLANE_POLE = "right_half_plane_pole"
    REPEATED_IMAGINARY_AXIS_POLE = "repeated_imaginary_axis_pole"
    REAL_PART_UNDETERMINED = "real_part_undetermined"


class PoleDynamicsClassification(StrEnum):
    """Supported qualitative interpretation of the reduced E/A poles."""

    APERIODIC = "aperiodic"
    DAMPED_OSCILLATORY_COMPONENT = "damped_oscillatory_component"
    UNCLASSIFIED = "unclassified"


class PoleDynamicsModelBasis(StrEnum):
    """Model basis on which a qualitative interpretation is founded."""

    REDUCED_EA_TRANSFER_FUNCTION = "reduced_ea_transfer_function"
    SAFELY_UNCLASSIFIED = "safely_unclassified"


@dataclass(frozen=True, slots=True)
class PoleDynamicsInterpretation:
    """Immutable qualitative statement derived from an existing pole result."""

    classification: PoleDynamicsClassification
    statement: str
    reason: str
    model_basis: PoleDynamicsModelBasis
    is_available: bool

    def __post_init__(self) -> None:
        if type(self.classification) is not PoleDynamicsClassification:
            raise TypeError("Invalid pole-dynamics classification.")
        if type(self.statement) is not str or not self.statement.strip():
            raise ValueError("A pole-dynamics interpretation needs a statement.")
        if type(self.reason) is not str or not self.reason.strip():
            raise ValueError("A pole-dynamics interpretation needs a reason.")
        if type(self.model_basis) is not PoleDynamicsModelBasis:
            raise TypeError("Invalid pole-dynamics model basis.")
        if type(self.is_available) is not bool:
            raise TypeError("is_available must be bool.")
        if self.is_available != (
            self.classification is not PoleDynamicsClassification.UNCLASSIFIED
        ):
            raise ValueError(
                "Availability must agree with the qualitative classification."
            )
        expected_basis = (
            PoleDynamicsModelBasis.REDUCED_EA_TRANSFER_FUNCTION
            if self.is_available
            else PoleDynamicsModelBasis.SAFELY_UNCLASSIFIED
        )
        if self.model_basis is not expected_basis:
            raise ValueError("The model basis does not match availability.")


@dataclass(frozen=True, slots=True)
class StabilityReason:
    """Machine-readable reason with optional non-identifying display text."""

    code: StabilityReasonCode
    message: str

    def __post_init__(self) -> None:
        if type(self.code) is not StabilityReasonCode:
            raise TypeError("A stability reason requires a supported code.")
        if type(self.message) is not str or not self.message.strip():
            raise ValueError("A stability reason requires display text.")


@dataclass(frozen=True, slots=True)
class StabilitySourceReference:
    """An official source location supporting the classification semantics."""

    document_name: str
    location: str
    claim: str
    page: int | None = None

    def __post_init__(self) -> None:
        for value in (self.document_name, self.location, self.claim):
            if type(value) is not str or not value.strip():
                raise ValueError("Source-reference text must not be empty.")
        if self.page is not None and (
            isinstance(self.page, bool)
            or not isinstance(self.page, int)
            or self.page <= 0
        ):
            raise ValueError("A source page must be a positive integer.")


@dataclass(frozen=True, slots=True)
class StabilityAnalysisLimits:
    """Bounded in-process work; no hard process timeout is implied."""

    max_poles: int = 64
    max_cancelled_locations: int = 64
    max_source_polynomial_degree: int = 64
    max_source_integer_digits: int = 512
    max_substitution_integer_digits: int = 256
    max_expression_nodes: int = 2048
    max_rootof_refinements: int = 32
    max_evidence_nodes: int = 4096
    max_diagnostics: int = 128
    max_result_items: int = 256

    def __post_init__(self) -> None:
        for name in self.__dataclass_fields__:
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive int.")


@dataclass(frozen=True, slots=True, eq=False)
class PoleStabilityContribution:
    """Exact contribution of one reduced pole to the aggregate status."""

    pole: RootOccurrence
    exact_real_part: ExactExpression | None
    real_part_sign: RealPartSign
    evidence_kind: StabilityEvidenceKind
    multiplicity: int
    contribution: PoleStabilityContributionKind
    reason: StabilityReason

    def __post_init__(self) -> None:
        if type(self.pole) is not RootOccurrence:
            raise TypeError("A pole contribution requires a RootOccurrence.")
        if self.exact_real_part is not None and type(
            self.exact_real_part
        ) is not ExactExpression:
            raise TypeError("An exact real part must be an ExactExpression.")
        if type(self.real_part_sign) is not RealPartSign:
            raise TypeError("A pole contribution requires a real-part sign.")
        if type(self.evidence_kind) is not StabilityEvidenceKind:
            raise TypeError("A pole contribution requires structured evidence.")
        if (
            isinstance(self.multiplicity, bool)
            or not isinstance(self.multiplicity, int)
            or self.multiplicity <= 0
            or self.multiplicity != self.pole.multiplicity
        ):
            raise ValueError("Contribution multiplicity must match the pole.")
        if type(self.contribution) is not PoleStabilityContributionKind:
            raise TypeError("A pole contribution requires a supported effect.")
        if type(self.reason) is not StabilityReason:
            raise TypeError("A pole contribution requires a structured reason.")

    def _identity(self) -> tuple[object, ...]:
        return (
            self.pole.value,
            self.multiplicity,
            self.real_part_sign,
            self.contribution,
        )

    def __eq__(self, other: object) -> bool:
        if type(other) is not PoleStabilityContribution:
            return NotImplemented
        return self._identity() == other._identity()

    def __hash__(self) -> int:
        digest = sha256(repr(self._identity()).encode("utf-8")).digest()[:8]
        return int.from_bytes(digest, byteorder="big", signed=True)


@dataclass(frozen=True, slots=True)
class CancelledLocationNotice:
    """Non-status-changing evidence about a proven cancelled location."""

    location: RootOccurrence
    exact_real_part: ExactExpression | None
    real_part_sign: RealPartSign
    evidence_kind: StabilityEvidenceKind
    reason: StabilityReason
    possible_hidden_internal_dynamics: bool = True

    def __post_init__(self) -> None:
        if type(self.location) is not RootOccurrence:
            raise TypeError("A cancelled-location notice requires a root.")
        if self.exact_real_part is not None and type(
            self.exact_real_part
        ) is not ExactExpression:
            raise TypeError("An exact real part must be an ExactExpression.")
        if type(self.real_part_sign) is not RealPartSign:
            raise TypeError("A cancelled location requires a real-part sign.")
        if type(self.evidence_kind) is not StabilityEvidenceKind:
            raise TypeError("A cancelled location requires structured evidence.")
        if type(self.reason) is not StabilityReason:
            raise TypeError("A cancelled location requires a structured reason.")
        if type(self.possible_hidden_internal_dynamics) is not bool:
            raise TypeError("The internal-dynamics flag must be bool.")


@dataclass(frozen=True, slots=True, init=False)
class TransferFunctionStabilityAnalysisResult:
    """Controlled result of one source-bound stability analysis attempt."""

    root_analysis: TransferFunctionRootAnalysisResult | None
    status: StabilityStatus | None
    is_ea_stable: bool | None
    pole_contributions: tuple[PoleStabilityContribution, ...]
    cancelled_location_notices: tuple[CancelledLocationNotice, ...]
    retained_domain_exclusions: RootAnalysisGroup | None
    pole_dynamics: PoleDynamicsInterpretation
    source_references: tuple[StabilitySourceReference, ...]
    diagnostics: tuple[Diagnostic, ...]

    def __new__(cls) -> TransferFunctionStabilityAnalysisResult:
        raise TypeError(
            "Stability results must be created by "
            "TransferFunctionStabilityAnalyzer."
        )

    @classmethod
    def _create(
        cls,
        *,
        root_analysis: TransferFunctionRootAnalysisResult | None,
        status: StabilityStatus | None,
        pole_contributions: tuple[PoleStabilityContribution, ...] = (),
        cancelled_location_notices: tuple[CancelledLocationNotice, ...] = (),
        retained_domain_exclusions: RootAnalysisGroup | None = None,
        pole_dynamics: PoleDynamicsInterpretation,
        source_references: tuple[StabilitySourceReference, ...] = (),
        diagnostics: tuple[Diagnostic, ...] = (),
    ) -> TransferFunctionStabilityAnalysisResult:
        instance = object.__new__(cls)
        object.__setattr__(instance, "root_analysis", root_analysis)
        object.__setattr__(instance, "status", status)
        object.__setattr__(
            instance,
            "is_ea_stable",
            (
                True
                if status is StabilityStatus.STABLE
                else None
                if status is None
                or status is StabilityStatus.SYMBOLIC_UNDETERMINED
                else False
            ),
        )
        object.__setattr__(instance, "pole_contributions", tuple(pole_contributions))
        object.__setattr__(
            instance,
            "cancelled_location_notices",
            tuple(cancelled_location_notices),
        )
        object.__setattr__(
            instance, "retained_domain_exclusions", retained_domain_exclusions
        )
        if type(pole_dynamics) is not PoleDynamicsInterpretation:
            raise TypeError("Invalid pole-dynamics interpretation.")
        object.__setattr__(instance, "pole_dynamics", pole_dynamics)
        object.__setattr__(instance, "source_references", tuple(source_references))
        object.__setattr__(instance, "diagnostics", tuple(diagnostics))
        return instance

    @property
    def succeeded(self) -> bool:
        """Whether a stability status was produced without an error."""

        return self.status is not None and all(
            item.severity is not DiagnosticSeverity.ERROR
            for item in self.diagnostics
        )


__all__ = [
    "CancelledLocationNotice",
    "PoleDynamicsClassification",
    "PoleDynamicsInterpretation",
    "PoleDynamicsModelBasis",
    "PoleStabilityContribution",
    "PoleStabilityContributionKind",
    "RealPartSign",
    "StabilityAnalysisLimits",
    "StabilityEvidenceKind",
    "StabilityReason",
    "StabilityReasonCode",
    "StabilitySourceReference",
    "StabilityStatus",
    "TransferFunctionStabilityAnalysisResult",
]
