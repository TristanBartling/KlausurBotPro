"""Immutable public contracts for Laplace, PBZ and time responses."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from klausurbotpro.domain.diagnostics import Diagnostic
from klausurbotpro.domain.expression import ExactExpression


class TimeDomainTaskType(StrEnum):
    DIRECT_LAPLACE = "direct_laplace"
    INVERSE_LAPLACE = "inverse_laplace"
    STEP_RESPONSE = "step_response"
    GENERAL_RESPONSE = "general_response"
    EXPONENTIAL_INPUT = "exponential_input"


class RationalClassificationKind(StrEnum):
    STRICTLY_PROPER = "STRICTLY_PROPER"
    EQUAL_DEGREE = "EQUAL_DEGREE"
    IMPROPER = "IMPROPER"


class ComputationStatus(StrEnum):
    SUCCESS = "SUCCESS"
    INCONCLUSIVE = "INCONCLUSIVE"
    UNSUPPORTED = "UNSUPPORTED"
    FAILED = "FAILED"


class PolynomialDivisionStatus(StrEnum):
    NOT_REQUIRED = "NOT_REQUIRED"
    SUCCESS = "SUCCESS"


class FactorType(StrEnum):
    LINEAR = "LINEAR"
    IRREDUCIBLE_QUADRATIC = "IRREDUCIBLE_QUADRATIC"


class PoleHalfPlane(StrEnum):
    LEFT = "LEFT"
    IMAGINARY_AXIS = "IMAGINARY_AXIS"
    RIGHT = "RIGHT"
    INCONCLUSIVE = "INCONCLUSIVE"


class PoleRole(StrEnum):
    SYSTEM = "SYSTEM"
    INPUT = "INPUT"
    OUTPUT = "OUTPUT"
    CANCELLED = "CANCELLED"


class EndValueStatus(StrEnum):
    VALID = "VALID"
    END_VALUE_THEOREM_INVALID = "END_VALUE_THEOREM_INVALID"
    INCONCLUSIVE = "INCONCLUSIVE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class VerificationStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass(frozen=True, slots=True)
class RationalClassification:
    numerator_degree: int
    denominator_degree: int
    kind: RationalClassificationKind
    requires_division: bool


@dataclass(frozen=True, slots=True)
class PolynomialDivisionResult:
    dividend: ExactExpression
    divisor: ExactExpression
    quotient: ExactExpression
    remainder: ExactExpression
    proper_fraction: ExactExpression
    reconstruction_residual: ExactExpression
    status: PolynomialDivisionStatus


@dataclass(frozen=True, slots=True)
class RealFactor:
    factor_id: str
    factor: ExactExpression
    factor_type: FactorType
    multiplicity: int
    discriminant: ExactExpression | None = None


@dataclass(frozen=True, slots=True)
class RealFactorStructure:
    denominator: ExactExpression
    leading_factor: ExactExpression
    factors: tuple[RealFactor, ...]
    reconstruction_residual: ExactExpression
    status: ComputationStatus


@dataclass(frozen=True, slots=True)
class PartialFractionTerm:
    factor_id: str
    factor: ExactExpression
    factor_type: FactorType
    power: int
    numerator: ExactExpression
    coefficients: tuple[ExactExpression, ...]
    ansatz_term: str
    inverse_pattern: str
    origin: str


@dataclass(frozen=True, slots=True)
class PartialFractionResult:
    proper_fraction: ExactExpression
    factor_structure: RealFactorStructure
    ansatz: str
    terms: tuple[PartialFractionTerm, ...]
    recomposed: ExactExpression
    reconstruction_residual: ExactExpression
    status: ComputationStatus


@dataclass(frozen=True, slots=True)
class DirectLaplaceRule:
    source_term: ExactExpression
    image_term: ExactExpression
    rule_id: str
    table_pair: str
    shift: ExactExpression


@dataclass(frozen=True, slots=True)
class InverseLaplaceMapping:
    image_term: ExactExpression
    time_term: ExactExpression
    rule_id: str
    explanation: str


@dataclass(frozen=True, slots=True)
class TimeFunction:
    expression: ExactExpression
    variable_name: str = "t"
    causal_for_nonnegative_time: bool = True


@dataclass(frozen=True, slots=True)
class ExponentialInputSignal:
    amplitude: ExactExpression
    exponent: ExactExpression
    time_function: TimeFunction
    laplace_expression: ExactExpression


@dataclass(frozen=True, slots=True)
class PoleRecord:
    value: ExactExpression
    multiplicity: int
    role: PoleRole
    half_plane: PoleHalfPlane


@dataclass(frozen=True, slots=True)
class VerificationItem:
    check_id: str
    status: VerificationStatus
    residual: ExactExpression | None
    explanation: str
    numerical_values: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True, slots=True)
class VerificationReport:
    items: tuple[VerificationItem, ...]
    initial_value: ExactExpression | None
    end_value_status: EndValueStatus
    end_value: ExactExpression | None


@dataclass(frozen=True, slots=True)
class RationalAnalysis:
    raw_expression: ExactExpression
    reduced_expression: ExactExpression
    raw_numerator: ExactExpression
    raw_denominator: ExactExpression
    reduced_numerator: ExactExpression
    reduced_denominator: ExactExpression
    classification: RationalClassification
    division: PolynomialDivisionResult
    cancellation_factors: tuple[ExactExpression, ...]


@dataclass(frozen=True, slots=True)
class TimeDomainSolution:
    task_type: TimeDomainTaskType
    status: ComputationStatus
    source_expression: ExactExpression | None
    input_laplace: ExactExpression | None
    system_laplace: ExactExpression | None
    output_laplace: ExactExpression | None
    rational_analysis: RationalAnalysis | None
    factor_structure: RealFactorStructure | None
    partial_fractions: PartialFractionResult | None
    direct_rules: tuple[DirectLaplaceRule, ...]
    inverse_mappings: tuple[InverseLaplaceMapping, ...]
    time_function: TimeFunction | None
    poles: tuple[PoleRecord, ...]
    verification: VerificationReport
    diagnostics: tuple[Diagnostic, ...]
    input_signal: ExponentialInputSignal | None = None


__all__ = [
    "ComputationStatus",
    "DirectLaplaceRule",
    "EndValueStatus",
    "ExponentialInputSignal",
    "FactorType",
    "InverseLaplaceMapping",
    "PartialFractionResult",
    "PartialFractionTerm",
    "PoleHalfPlane",
    "PoleRecord",
    "PoleRole",
    "PolynomialDivisionResult",
    "PolynomialDivisionStatus",
    "RationalAnalysis",
    "RationalClassification",
    "RationalClassificationKind",
    "RealFactor",
    "RealFactorStructure",
    "TimeDomainSolution",
    "TimeDomainTaskType",
    "TimeFunction",
    "VerificationItem",
    "VerificationReport",
    "VerificationStatus",
]
