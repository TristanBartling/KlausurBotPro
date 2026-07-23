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
    SOLVE_ODE = "solve_ode"
    TRANSFER_FUNCTION_FROM_ODE = "transfer_function_from_ode"


class OdeAnalysisGoal(StrEnum):
    IMAGE_EQUATION = "image_equation"
    OUTPUT_LAPLACE = "output_laplace"
    PARTIAL_FRACTIONS = "partial_fractions"
    TIME_RESPONSE = "time_response"


class InitialConditionOrigin(StrEnum):
    USER_PROVIDED = "USER_PROVIDED"
    EXPLICIT_ZERO_POLICY = "EXPLICIT_ZERO_POLICY"
    DERIVED = "DERIVED"


class InputSignalType(StrEnum):
    ZERO = "zero"
    STEP = "step"
    EXPONENTIAL = "exponential"
    POLYNOMIAL = "polynomial"
    SINUS = "sinus"
    COSINUS = "cosinus"
    IMAGE_EXPRESSION = "image_expression"


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
class TypedInputSignal:
    signal_type: InputSignalType
    parameters: tuple[ExactExpression, ...]
    time_function: TimeFunction | None
    laplace_expression: ExactExpression
    transform_rule: str
    raw_input: str


@dataclass(frozen=True, slots=True)
class InitialConditionValue:
    derivative_order: int
    value: ExactExpression
    origin: InitialConditionOrigin


@dataclass(frozen=True, slots=True)
class InitialConditionSet:
    variable: str
    required_orders: tuple[int, ...]
    values: tuple[InitialConditionValue, ...]
    complete: bool
    missing_orders: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class LinearOdeInput:
    output_name: str
    input_name: str | None
    output_terms: tuple[tuple[int, ExactExpression], ...]
    input_terms: tuple[tuple[int, ExactExpression], ...]
    output_order: int
    input_order: int
    parameter_assumptions: tuple[str, ...]
    raw_provenance: str
    normalized_ode: str
    leading_coefficient: ExactExpression
    valid: bool
    diagnostics: tuple[Diagnostic, ...] = ()


@dataclass(frozen=True, slots=True)
class TransformedOdeTerm:
    side: str
    derivative_order: int
    coefficient: ExactExpression
    transformed_expression: ExactExpression
    initial_value_part: ExactExpression
    display_rule: str
    latex_rule: str


@dataclass(frozen=True, slots=True)
class OdeImageEquation:
    a_polynomial: ExactExpression
    b_polynomial: ExactExpression
    output_initial_part: ExactExpression
    input_initial_part: ExactExpression
    left_expression: ExactExpression
    right_expression: ExactExpression
    display_equation: str


@dataclass(frozen=True, slots=True)
class OdeVerificationReport:
    image_equation_residual: ExactExpression
    decomposition_residual: ExactExpression
    forward_transform_residual: ExactExpression
    initial_condition_residuals: tuple[tuple[int, ExactExpression], ...]
    ode_residual: ExactExpression
    trusted: bool


@dataclass(frozen=True, slots=True)
class OdeSolutionData:
    ode: LinearOdeInput
    output_initial_conditions: InitialConditionSet
    input_initial_conditions: InitialConditionSet | None
    input_signal: TypedInputSignal
    transformed_terms: tuple[TransformedOdeTerm, ...]
    image_equation: OdeImageEquation
    analysis_goal: OdeAnalysisGoal
    free_laplace: ExactExpression | None = None
    forced_laplace: ExactExpression | None = None
    total_laplace: ExactExpression | None = None
    free_time: TimeFunction | None = None
    forced_time: TimeFunction | None = None
    total_time: TimeFunction | None = None
    verification: OdeVerificationReport | None = None

    def __post_init__(self) -> None:
        laplace_values = (self.free_laplace, self.forced_laplace, self.total_laplace)
        time_values = (self.free_time, self.forced_time, self.total_time)
        if self.analysis_goal is OdeAnalysisGoal.IMAGE_EQUATION and (
            any(item is not None for item in (*laplace_values, *time_values))
            or self.verification is not None
        ):
            raise ValueError("Die Bildgleichungsstufe darf keine späteren Ergebnisse enthalten.")
        if self.analysis_goal is not OdeAnalysisGoal.IMAGE_EQUATION and any(
            item is None for item in laplace_values
        ):
            raise ValueError("Das Analyseziel erfordert vollständige Bildbereichswerte.")
        if self.analysis_goal in {
            OdeAnalysisGoal.OUTPUT_LAPLACE,
            OdeAnalysisGoal.PARTIAL_FRACTIONS,
        } and (
            any(item is not None for item in time_values)
            or self.verification is not None
        ):
            raise ValueError("Die gewählte Bildbereichsstufe darf keine Zeitantwort enthalten.")
        if self.analysis_goal is OdeAnalysisGoal.TIME_RESPONSE and (
            any(item is None for item in time_values) or self.verification is None
        ):
            raise ValueError(
                "Die vollständige Zeitantwort erfordert Zeitfunktionen und Verifikation."
            )


@dataclass(frozen=True, slots=True)
class OdeTransferFunctionResult:
    ode: LinearOdeInput
    zero_state_confirmed: bool
    raw_transfer_function: ExactExpression
    reduced_transfer_function: ExactExpression
    numerator: ExactExpression
    denominator: ExactExpression
    multiplication_residual: ExactExpression
    transformed_terms: tuple[TransformedOdeTerm, ...] = ()


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
    input_signal: ExponentialInputSignal | TypedInputSignal | None = None
    ode_solution: OdeSolutionData | None = None
    ode_transfer_function: OdeTransferFunctionResult | None = None


__all__ = [
    "ComputationStatus",
    "DirectLaplaceRule",
    "EndValueStatus",
    "ExponentialInputSignal",
    "InitialConditionOrigin",
    "InitialConditionSet",
    "InitialConditionValue",
    "InputSignalType",
    "LinearOdeInput",
    "OdeAnalysisGoal",
    "OdeImageEquation",
    "OdeSolutionData",
    "OdeTransferFunctionResult",
    "OdeVerificationReport",
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
    "TransformedOdeTerm",
    "TypedInputSignal",
    "VerificationItem",
    "VerificationReport",
    "VerificationStatus",
]
