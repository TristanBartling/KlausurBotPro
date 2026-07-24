"""Immutable public results for Hurwitz analysis."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from klausurbotpro.domain.expression import ExactExpression
from klausurbotpro.domain.parameter_core_contracts import (
    AtomicParameterCondition,
    CanonicalCharacteristicPolynomial,
    ConditionOrigin,
    ParameterRegion,
    PolynomialDegreeCase,
    SolveStatus,
)
from klausurbotpro.domain.stability_contracts import NumericalCheckStatus, NumericalPoleCheck


class HurwitzConditionStatus(StrEnum):
    ACTIVE = "active"
    ALREADY_SATISFIED = "already_satisfied"
    REDUNDANT_EQUIVALENT = "redundant_equivalent"
    REDUNDANT_WEAKER = "redundant_weaker"
    CONTRADICTORY = "contradictory"
    UNRESOLVED_SAFE = "unresolved_safe"


@dataclass(frozen=True, slots=True)
class HurwitzConditionStep:
    label: str
    origin: ConditionOrigin
    expression: ExactExpression
    expanded_expression: ExactExpression
    factored_expression: ExactExpression
    solved_expression: ExactExpression
    solved_text: str
    solved_latex: str
    status: HurwitzConditionStatus
    reference_label: str = ""
    reason: str = ""


@dataclass(frozen=True, slots=True)
class HurwitzDeterminant:
    order: int
    expression: ExactExpression
    factored_expression: ExactExpression


@dataclass(frozen=True, slots=True)
class HurwitzDegreeCaseResult:
    degree_case: PolynomialDegreeCase
    matrix: tuple[tuple[ExactExpression, ...], ...]
    determinants: tuple[HurwitzDeterminant, ...]
    full_conditions: tuple[AtomicParameterCondition, ...]
    solver_conditions: tuple[AtomicParameterCondition, ...]
    necessary_condition_steps: tuple[HurwitzConditionStep, ...]
    sufficient_condition_steps: tuple[HurwitzConditionStep, ...]
    minimal_condition_steps: tuple[HurwitzConditionStep, ...]
    parameter_region: ParameterRegion
    numerical_check: NumericalPoleCheck | None
    statement: str
    status: SolveStatus
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class HurwitzAnalysisResult:
    canonical_polynomial: CanonicalCharacteristicPolynomial
    case_results: tuple[HurwitzDegreeCaseResult, ...]
    stability_concept: str
    combined_region: str
    statement: str
    cancellation_notice: str
    worked_steps: tuple[tuple[str, str], ...]
    latex_source: str
    diagnostics: tuple[str, ...] = ()


__all__ = [
    "HurwitzAnalysisResult",
    "HurwitzConditionStatus",
    "HurwitzConditionStep",
    "HurwitzDegreeCaseResult",
    "HurwitzDeterminant",
    "NumericalCheckStatus",
    "NumericalPoleCheck",
]
