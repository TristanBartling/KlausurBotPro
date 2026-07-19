"""Internal exact and certified real-part classification."""

from __future__ import annotations

from dataclasses import dataclass

import sympy as sp

from klausurbotpro.domain._exact_polynomial_root_solver import (
    exact_root_as_sympy,
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


class RealPartClassificationLimitError(ValueError):
    """A configured classification resource boundary was exceeded."""


@dataclass(frozen=True, slots=True)
class ExactRealPartClassification:
    """Internal bridge from SymPy evidence to public SymPy-free values."""

    exact_real_part: ExactExpression | None
    sign: RealPartSign
    evidence_kind: StabilityEvidenceKind
    evidence_nodes: int


def classify_exact_real_part(
    value: ExplicitExactRootValue | RootOfValue,
    limits: StabilityAnalysisLimits,
) -> ExactRealPartClassification:
    """Classify a trusted exact root without tolerance-based numerics."""

    if type(value) is ExplicitExactRootValue:
        root = value.expression._as_sympy()
        source_nodes = _bounded_node_count(root, limits.max_expression_nodes)
        try:
            real_part = sp.simplify(sp.re(root))
        except (ArithmeticError, NotImplementedError, ValueError):
            return ExactRealPartClassification(
                None,
                RealPartSign.UNDETERMINED,
                StabilityEvidenceKind.EXPLICIT_EXACT_REAL_PART,
                source_nodes,
            )
        nodes = _bounded_node_count(real_part, limits.max_expression_nodes)
        sign = _predicate_sign(real_part)
        return ExactRealPartClassification(
            ExactExpression._from_sympy(real_part),
            sign,
            StabilityEvidenceKind.EXPLICIT_EXACT_REAL_PART,
            source_nodes + nodes,
        )
    if type(value) is not RootOfValue:
        raise TypeError("Unsupported exact root value.")

    root = exact_root_as_sympy(value)
    real_part = sp.re(root)
    nodes = _bounded_node_count(real_part, limits.max_expression_nodes)
    predicate_sign = _predicate_sign(real_part)
    if predicate_sign is not RealPartSign.UNDETERMINED:
        return ExactRealPartClassification(
            ExactExpression._from_sympy(sp.simplify(real_part)),
            predicate_sign,
            StabilityEvidenceKind.ROOTOF_EXACT_PREDICATE,
            nodes,
        )

    try:
        for refinement in range(1, limits.max_rootof_refinements + 1):
            error_bound = sp.Rational(1, 2 ** (refinement + 1))
            approximation = root.eval_rational(
                dx=error_bound,
                dy=error_bound,
            )
            approximate_real = sp.re(approximation)
            if approximate_real - error_bound > 0:
                return ExactRealPartClassification(
                    None,
                    RealPartSign.POSITIVE,
                    StabilityEvidenceKind.ROOTOF_CERTIFIED_INTERVAL,
                    nodes + refinement,
                )
            if approximate_real + error_bound < 0:
                return ExactRealPartClassification(
                    None,
                    RealPartSign.NEGATIVE,
                    StabilityEvidenceKind.ROOTOF_CERTIFIED_INTERVAL,
                    nodes + refinement,
                )
    except (ArithmeticError, NotImplementedError, ValueError):
        pass

    return ExactRealPartClassification(
        None,
        RealPartSign.UNDETERMINED,
        StabilityEvidenceKind.ROOTOF_CERTIFIED_INTERVAL,
        nodes + limits.max_rootof_refinements,
    )


def _predicate_sign(expression: sp.Expr) -> RealPartSign:
    if expression.is_negative is True:
        return RealPartSign.NEGATIVE
    if expression.is_zero is True:
        return RealPartSign.ZERO
    if expression.is_positive is True:
        return RealPartSign.POSITIVE
    return RealPartSign.UNDETERMINED


def _bounded_node_count(expression: sp.Expr, limit: int) -> int:
    count = 0
    for _ in sp.preorder_traversal(expression):
        count += 1
        if count > limit:
            raise RealPartClassificationLimitError("max_expression_nodes")
    return count


__all__ = [
    "ExactRealPartClassification",
    "RealPartClassificationLimitError",
    "classify_exact_real_part",
]
