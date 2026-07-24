"""SymPy-free public contracts for characteristic-polynomial parameter work."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from klausurbotpro.domain.expression import ExactExpression


class PolynomialRole(StrEnum):
    DIRECT_CHARACTERISTIC_POLYNOMIAL = "direct_characteristic_polynomial"
    REDUCED_TRANSFER_DENOMINATOR = "reduced_transfer_denominator"
    RAW_CLOSED_LOOP_CHARACTERISTIC = "raw_closed_loop_characteristic"
    STATE_CHARACTERISTIC_POLYNOMIAL = "state_characteristic_polynomial"


class AnalysisTarget(StrEnum):
    INTERNAL_CLOSED_LOOP_ASYMPTOTIC = "internal_closed_loop_asymptotic"
    EXTERNAL_BIBO = "external_bibo"
    STATE_ASYMPTOTIC = "state_asymptotic"


class CancellationStatus(StrEnum):
    NOT_APPLICABLE = "not_applicable"
    NONE = "none"
    FACTORS_REMOVED = "factors_removed"


class Relation(StrEnum):
    EQ = "eq"
    NE = "ne"
    LT = "lt"
    LE = "le"
    GT = "gt"
    GE = "ge"


class ConditionOrigin(StrEnum):
    COEFFICIENT = "coefficient"
    HURWITZ_DETERMINANT = "hurwitz_determinant"
    CANCELLATION_FACTOR = "cancellation_factor"
    ROUTH_FIRST_COLUMN = "routh_first_column"
    ROUTH_DENOMINATOR_EXCLUSION = "routh_denominator_exclusion"
    DEGREE_CASE_GUARD = "degree_case_guard"
    DENOMINATOR_EXCLUSION = "denominator_exclusion"
    USER_ASSUMPTION = "user_assumption"


class DegreeCaseKind(StrEnum):
    REGULAR = "regular"
    DEGREE_REDUCED = "degree_reduced"
    CONSTANT_NONZERO = "constant_nonzero"
    ZERO_POLYNOMIAL = "zero_polynomial"


class SolveStatus(StrEnum):
    SOLVED_EXACT = "solved_exact"
    EMPTY = "empty"
    PARTIALLY_SOLVED_SAFE = "partially_solved_safe"
    UNSUPPORTED = "unsupported"
    INVALID_INPUT = "invalid_input"
    INDETERMINATE = "indeterminate"


@dataclass(frozen=True, slots=True)
class SourceProvenance:
    producer: str
    source_reference: str = ""
    description: str = ""


@dataclass(frozen=True, slots=True)
class CancellationReport:
    status: CancellationStatus
    note: str = ""
    removed_factors: tuple[ExactExpression, ...] = ()


@dataclass(frozen=True, slots=True)
class AtomicParameterCondition:
    expression: ExactExpression
    relation: Relation
    origin: ConditionOrigin
    parameters: tuple[str, ...]
    label: str = ""


@dataclass(frozen=True, slots=True)
class CharacteristicPolynomialInput:
    polynomial: ExactExpression
    variable: str
    decision_parameters: tuple[str, ...]
    fixed_symbols: tuple[str, ...]
    assumptions: tuple[AtomicParameterCondition, ...]
    exclusions: tuple[AtomicParameterCondition, ...]
    role: PolynomialRole
    analysis_target: AnalysisTarget
    provenance: SourceProvenance
    cancellation_report: CancellationReport | None = None


@dataclass(frozen=True, slots=True)
class TransformationRecord:
    operation: str
    before: ExactExpression
    after: ExactExpression
    guard: str


@dataclass(frozen=True, slots=True)
class PolynomialDegreeCase:
    case_id: str
    guard: tuple[AtomicParameterCondition, ...]
    polynomial: ExactExpression
    coefficients: tuple[ExactExpression, ...]
    degree: int
    kind: DegreeCaseKind
    transformations: tuple[TransformationRecord, ...] = ()


@dataclass(frozen=True, slots=True)
class CanonicalCharacteristicPolynomial:
    input: CharacteristicPolynomialInput
    expanded_polynomial: ExactExpression
    coefficients: tuple[ExactExpression, ...]
    nominal_degree: int
    degree_cases: tuple[PolynomialDegreeCase, ...]
    status: SolveStatus
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ParameterConditionProblem:
    parameters: tuple[str, ...]
    conditions: tuple[AtomicParameterCondition, ...]
    assumptions: tuple[AtomicParameterCondition, ...] = ()
    exclusions: tuple[AtomicParameterCondition, ...] = ()


@dataclass(frozen=True, slots=True)
class ParameterRegion:
    status: SolveStatus
    exact_text: str
    latex: str
    intervals: tuple[str, ...] = ()
    x_domain: str = ""
    lower_bound: str = ""
    upper_bound: str = ""
    lower_open: bool = True
    upper_open: bool = True
    control_points: tuple[tuple[str, ...], ...] = ()
    residual_conditions: tuple[str, ...] = ()
    diagnostics: tuple[str, ...] = ()


__all__ = [
    "AnalysisTarget",
    "AtomicParameterCondition",
    "CancellationReport",
    "CancellationStatus",
    "CanonicalCharacteristicPolynomial",
    "CharacteristicPolynomialInput",
    "ConditionOrigin",
    "DegreeCaseKind",
    "ParameterConditionProblem",
    "ParameterRegion",
    "PolynomialDegreeCase",
    "PolynomialRole",
    "Relation",
    "SolveStatus",
    "SourceProvenance",
    "TransformationRecord",
]
