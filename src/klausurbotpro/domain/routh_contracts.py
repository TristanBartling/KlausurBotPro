"""Immutable, SymPy-free public results for Routh analysis."""

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
from klausurbotpro.domain.stability_contracts import NumericalPoleCheck


class RouthRowType(StrEnum):
    INITIAL_EVEN = "initial_even"
    INITIAL_ODD = "initial_odd"
    RECURSIVE = "recursive"


class RouthSpecialCase(StrEnum):
    NONE = "none"
    ZERO_FIRST_COLUMN = "zero_first_column"
    COMPLETE_ZERO_ROW = "complete_zero_row"


@dataclass(frozen=True, slots=True)
class RouthCell:
    row_index: int
    column_index: int
    value: ExactExpression
    raw_numerator: ExactExpression
    raw_denominator: ExactExpression
    derivation: str
    is_first_column: bool
    calculation_latex: str = ""


@dataclass(frozen=True, slots=True)
class RouthRow:
    power_label: str
    power: int
    entries: tuple[ExactExpression, ...]
    first_column: ExactExpression
    row_type: RouthRowType
    cells: tuple[RouthCell, ...]


@dataclass(frozen=True, slots=True)
class RouthDegreeCaseResult:
    degree_case: PolynomialDegreeCase
    rows: tuple[RouthRow, ...]
    first_column: tuple[ExactExpression, ...]
    full_conditions: tuple[AtomicParameterCondition, ...]
    solver_conditions: tuple[AtomicParameterCondition, ...]
    parameter_region: ParameterRegion
    special_case: RouthSpecialCase
    control_point: tuple[tuple[str, str], ...]
    sign_sequence: tuple[str, ...]
    sign_changes: int | None
    rhp_roots_routh: int | None
    numerical_check: NumericalPoleCheck | None
    numerical_rhp_roots: int | None
    statement: str
    status: SolveStatus
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class RouthAnalysisResult:
    canonical_polynomial: CanonicalCharacteristicPolynomial
    case_results: tuple[RouthDegreeCaseResult, ...]
    stability_concept: str
    combined_region: str
    statement: str
    cancellation_notice: str
    worked_steps: tuple[tuple[str, str], ...]
    latex_source: str
    diagnostics: tuple[str, ...] = ()


__all__ = [
    "RouthAnalysisResult",
    "RouthCell",
    "RouthDegreeCaseResult",
    "RouthRow",
    "RouthRowType",
    "RouthSpecialCase",
]
