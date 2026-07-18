"""Structured diagnostics shared by parsers and later application services."""

from dataclasses import dataclass
from enum import StrEnum


class DiagnosticSeverity(StrEnum):
    """Severity understood by application and presentation layers."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class DiagnosticCode(StrEnum):
    """Stable, machine-readable codes for expected validation failures."""

    PARSE_EMPTY_INPUT = "parse.empty_input"
    PARSE_INVALID_SYNTAX = "parse.invalid_syntax"
    PARSE_INVALID_NUMBER = "parse.invalid_number"
    PARSE_UNKNOWN_SYMBOL = "parse.unknown_symbol"
    PARSE_FORBIDDEN_NODE = "parse.forbidden_node"
    PARSE_IMPLICIT_MULTIPLICATION = "parse.implicit_multiplication"
    PARSE_LIMIT_EXCEEDED = "parse.limit_exceeded"
    PARSE_INVALID_EXPONENT = "parse.invalid_exponent"
    MATH_DIVISION_BY_ZERO = "math.division_by_zero"
    POLYNOMIAL_INVALID_VARIABLE = "polynomial.invalid_variable"
    POLYNOMIAL_VARIABLE_CONFLICT = "polynomial.variable_conflict"
    POLYNOMIAL_UNDECLARED_SYMBOL = "polynomial.undeclared_symbol"
    POLYNOMIAL_NOT_POLYNOMIAL = "polynomial.not_polynomial"
    POLYNOMIAL_NEGATIVE_EXPONENT = "polynomial.negative_exponent"
    POLYNOMIAL_SYMBOLIC_EXPONENT = "polynomial.symbolic_exponent"
    POLYNOMIAL_NONINTEGER_EXPONENT = "polynomial.noninteger_exponent"
    POLYNOMIAL_VARIABLE_IN_DENOMINATOR = (
        "polynomial.variable_in_denominator"
    )
    POLYNOMIAL_FLOAT_NOT_ALLOWED = "polynomial.float_not_allowed"
    POLYNOMIAL_PARAMETER_LIMIT_EXCEEDED = (
        "polynomial.parameter_limit_exceeded"
    )
    POLYNOMIAL_DEGREE_LIMIT_EXCEEDED = "polynomial.degree_limit_exceeded"
    POLYNOMIAL_TERM_LIMIT_EXCEEDED = "polynomial.term_limit_exceeded"
    POLYNOMIAL_COEFFICIENT_LIMIT_EXCEEDED = (
        "polynomial.coefficient_limit_exceeded"
    )
    POLYNOMIAL_COMPLEXITY_LIMIT_EXCEEDED = (
        "polynomial.complexity_limit_exceeded"
    )
    POLYNOMIAL_RESOURCE_LIMIT_EXCEEDED = (
        "polynomial.resource_limit_exceeded"
    )
    POLYNOMIAL_CONDITIONAL_DEGREE = "polynomial.conditional_degree"
    POLYNOMIAL_PARAMETER_DENOMINATOR_NONZERO = (
        "polynomial.parameter_denominator_nonzero"
    )
    POLYNOMIAL_SYMBOL_ASSUMPTION_NOT_ALLOWED = (
        "polynomial.symbol_assumption_not_allowed"
    )


@dataclass(frozen=True, slots=True)
class Diagnostic:
    """An immutable user-facing error or warning with optional log context."""

    severity: DiagnosticSeverity
    code: DiagnosticCode
    message: str
    field: str | None = None
    technical_details: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not self.message.strip():
            raise ValueError("A diagnostic message must not be empty.")

        immutable_details = tuple(
            (str(key), str(value)) for key, value in self.technical_details
        )
        object.__setattr__(self, "technical_details", immutable_details)
