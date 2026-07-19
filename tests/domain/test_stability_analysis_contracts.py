"""Contract invariants for source-bound stability analysis."""

from dataclasses import FrozenInstanceError

import pytest
import sympy as sp

from klausurbotpro.domain.expression import ExactExpression
from klausurbotpro.domain.root_analysis_contracts import (
    ExplicitExactRootValue,
    RootOccurrence,
    RootSource,
)
from klausurbotpro.domain.stability_analysis_contracts import (
    PoleStabilityContribution,
    PoleStabilityContributionKind,
    RealPartSign,
    StabilityAnalysisLimits,
    StabilityEvidenceKind,
    StabilityReason,
    StabilityReasonCode,
    StabilitySourceReference,
    TransferFunctionStabilityAnalysisResult,
)


def _contribution(message: str) -> PoleStabilityContribution:
    value = ExplicitExactRootValue(
        ExactExpression._from_sympy(sp.Integer(-1))
    )
    pole = RootOccurrence(value, 1, RootSource.DENOMINATOR, 0)
    return PoleStabilityContribution(
        pole,
        ExactExpression._from_sympy(sp.Integer(-1)),
        RealPartSign.NEGATIVE,
        StabilityEvidenceKind.EXPLICIT_EXACT_REAL_PART,
        1,
        PoleStabilityContributionKind.SUPPORTS_STABLE,
        StabilityReason(
            StabilityReasonCode.STRICTLY_LEFT_HALF_PLANE,
            message,
        ),
    )


def test_limits_require_positive_real_ints() -> None:
    for field_name in StabilityAnalysisLimits.__dataclass_fields__:
        with pytest.raises(ValueError, match="positive int"):
            StabilityAnalysisLimits(**{field_name: False})
        with pytest.raises(ValueError, match="positive int"):
            StabilityAnalysisLimits(**{field_name: 0})


def test_contribution_identity_excludes_display_reason_and_is_hash_consistent() -> None:
    first = _contribution("first display text")
    second = _contribution("second display text")

    assert first == second
    assert hash(first) == hash(second)
    assert {first: "pole"}[second] == "pole"


def test_contracts_are_immutable_and_results_are_controlled() -> None:
    reference = StabilitySourceReference(
        "skript.pdf",
        "Theorem 5.12",
        "claim",
        107,
    )
    with pytest.raises(FrozenInstanceError):
        reference.page = 1  # type: ignore[misc]
    with pytest.raises(TypeError, match="Stability results"):
        TransferFunctionStabilityAnalysisResult()


def test_contribution_multiplicity_must_match_pole() -> None:
    contribution = _contribution("reason")
    with pytest.raises(ValueError, match="match"):
        PoleStabilityContribution(
            contribution.pole,
            contribution.exact_real_part,
            contribution.real_part_sign,
            contribution.evidence_kind,
            2,
            contribution.contribution,
            contribution.reason,
        )
