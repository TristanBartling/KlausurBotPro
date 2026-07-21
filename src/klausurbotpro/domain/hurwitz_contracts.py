"""Immutable public results for Hurwitz analysis."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from klausurbotpro.domain.expression import ExactExpression
from klausurbotpro.domain.parameter_core_contracts import (
    AtomicParameterCondition,
    CanonicalCharacteristicPolynomial,
    ParameterRegion,
    PolynomialDegreeCase,
    SolveStatus,
)


class NumericalCheckStatus(StrEnum):
    CONSISTENT = "consistent"
    INCONSISTENT = "inconsistent"
    NUMERICALLY_INCONCLUSIVE = "numerically_inconclusive"


@dataclass(frozen=True, slots=True)
class HurwitzDeterminant:
    order: int
    expression: ExactExpression
    factored_expression: ExactExpression


@dataclass(frozen=True, slots=True)
class NumericalPoleCheck:
    status: NumericalCheckStatus
    parameter_point: tuple[tuple[str, str], ...]
    poles: tuple[str, ...]
    maximum_real_part: str


@dataclass(frozen=True, slots=True)
class HurwitzDegreeCaseResult:
    degree_case: PolynomialDegreeCase
    matrix: tuple[tuple[ExactExpression, ...], ...]
    determinants: tuple[HurwitzDeterminant, ...]
    full_conditions: tuple[AtomicParameterCondition, ...]
    solver_conditions: tuple[AtomicParameterCondition, ...]
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
    "HurwitzDegreeCaseResult",
    "HurwitzDeterminant",
    "NumericalCheckStatus",
    "NumericalPoleCheck",
]
