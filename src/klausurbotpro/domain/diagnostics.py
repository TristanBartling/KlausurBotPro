"""Structured diagnostics shared by parsers and later application services."""

from dataclasses import dataclass
from enum import StrEnum


class DiagnosticSeverity(StrEnum):
    """Severity understood by application and presentation layers."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class DiagnosticCode(StrEnum):
    """Stable, machine-readable codes for expected parser failures."""

    PARSE_EMPTY_INPUT = "parse.empty_input"
    PARSE_INVALID_SYNTAX = "parse.invalid_syntax"
    PARSE_INVALID_NUMBER = "parse.invalid_number"
    PARSE_UNKNOWN_SYMBOL = "parse.unknown_symbol"
    PARSE_FORBIDDEN_NODE = "parse.forbidden_node"
    PARSE_IMPLICIT_MULTIPLICATION = "parse.implicit_multiplication"
    PARSE_LIMIT_EXCEEDED = "parse.limit_exceeded"
    PARSE_INVALID_EXPONENT = "parse.invalid_exponent"
    MATH_DIVISION_BY_ZERO = "math.division_by_zero"


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
