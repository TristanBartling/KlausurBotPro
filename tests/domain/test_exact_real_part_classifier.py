"""Exact and certified tests for real-part classification."""

import pytest
import sympy as sp

import klausurbotpro.domain._exact_real_part_classifier as classifier_module
from klausurbotpro.domain._exact_real_part_classifier import (
    classify_exact_real_part,
)
from klausurbotpro.domain.expression import ExactExpression
from klausurbotpro.domain.root_analysis_contracts import (
    ExplicitExactRootValue,
    RootOfValue,
)
from klausurbotpro.domain.stability_analysis_contracts import (
    RealPartSign,
    StabilityAnalysisLimits,
    StabilityEvidenceKind,
)


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        (sp.Integer(-2), RealPartSign.NEGATIVE),
        (-1 + sp.I, RealPartSign.NEGATIVE),
        (sp.I, RealPartSign.ZERO),
        (sp.Integer(0), RealPartSign.ZERO),
        (3 - 2 * sp.I, RealPartSign.POSITIVE),
        (sp.sqrt(2) - 2, RealPartSign.NEGATIVE),
    ],
)
def test_explicit_exact_real_parts_use_only_exact_predicates(
    expression: sp.Expr,
    expected: RealPartSign,
) -> None:
    result = classify_exact_real_part(
        ExplicitExactRootValue(ExactExpression._from_sympy(expression)),
        StabilityAnalysisLimits(),
    )

    assert result.sign is expected
    assert result.evidence_kind is (
        StabilityEvidenceKind.EXPLICIT_EXACT_REAL_PART
    )
    assert result.exact_real_part is not None


def test_rootof_exact_predicates_certify_left_and_right_half_planes() -> None:
    left = classify_exact_real_part(
        RootOfValue((1, 0, 0, 0, -1, 1), 0),
        StabilityAnalysisLimits(),
    )
    right = classify_exact_real_part(
        RootOfValue((1, 0, 0, 0, -1, -1), 0),
        StabilityAnalysisLimits(),
    )

    assert left.sign is RealPartSign.NEGATIVE
    assert right.sign is RealPartSign.POSITIVE
    assert left.evidence_kind is StabilityEvidenceKind.ROOTOF_EXACT_PREDICATE


def test_rootof_public_certified_interval_is_used_without_tolerance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        classifier_module,
        "_predicate_sign",
        lambda expression: RealPartSign.UNDETERMINED,
    )
    certified = classify_exact_real_part(
        RootOfValue((1, 0, 0, 0, -1, -1), 0),
        StabilityAnalysisLimits(max_rootof_refinements=4),
    )

    assert certified.sign is RealPartSign.POSITIVE
    assert certified.evidence_kind is (
        StabilityEvidenceKind.ROOTOF_CERTIFIED_INTERVAL
    )


def test_rootof_axis_crossing_after_bound_is_conservatively_undetermined(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        classifier_module,
        "_predicate_sign",
        lambda expression: RealPartSign.UNDETERMINED,
    )
    result = classify_exact_real_part(
        RootOfValue((1, 0, 0, 0, -1, -1), 3),
        StabilityAnalysisLimits(max_rootof_refinements=1),
    )

    assert result.sign is RealPartSign.UNDETERMINED
    assert result.exact_real_part is None


def test_classifier_does_not_change_global_sympy_configuration() -> None:
    before = sp.SYMPY_DEBUG
    classify_exact_real_part(
        ExplicitExactRootValue(ExactExpression._from_sympy(-1 + sp.I)),
        StabilityAnalysisLimits(),
    )
    assert sp.SYMPY_DEBUG is before
