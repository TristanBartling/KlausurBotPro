"""Public contracts for validated, unreduced transfer functions."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING

from klausurbotpro.domain.diagnostics import Diagnostic, DiagnosticSeverity
from klausurbotpro.domain.expression import ExactExpression

if TYPE_CHECKING:
    from klausurbotpro.domain.polynomial import Polynomial
    from klausurbotpro.domain.raw_transfer_function import RawTransferFunction


class TransferFunctionPrerequisiteKind(StrEnum):
    """Kinds of parameter-only validity prerequisites."""

    EXPRESSION_NONZERO = "expression_nonzero"
    NOT_ALL_ZERO = "not_all_zero"


@dataclass(frozen=True, slots=True)
class TransferFunctionPrerequisite:
    """A structured parameter-only predicate."""

    kind: TransferFunctionPrerequisiteKind
    expressions: tuple[ExactExpression, ...]
    origins: tuple[str, ...] = field(compare=False, hash=False)

    def __post_init__(self) -> None:
        expressions = tuple(self.expressions)
        origins = tuple(sorted(set(self.origins)))
        if not expressions:
            raise ValueError("A prerequisite requires at least one expression.")
        if any(
            not isinstance(expression, ExactExpression)
            for expression in expressions
        ):
            raise TypeError("Prerequisite expressions must be ExactExpression values.")
        if not origins or any(not origin for origin in origins):
            raise ValueError("A prerequisite requires nonempty origins.")
        if (
            self.kind is TransferFunctionPrerequisiteKind.EXPRESSION_NONZERO
            and len(expressions) != 1
        ):
            raise ValueError("EXPRESSION_NONZERO requires exactly one expression.")
        object.__setattr__(self, "expressions", expressions)
        object.__setattr__(self, "origins", origins)

    @property
    def description(self) -> str:
        """Return a deterministic human-readable predicate."""
        if self.kind is TransferFunctionPrerequisiteKind.EXPRESSION_NONZERO:
            return f"{self.expressions[0].canonical_text} != 0"
        arguments = ", ".join(
            expression.canonical_text for expression in self.expressions
        )
        return f"NOT_ALL_ZERO({arguments})"


@dataclass(frozen=True, slots=True)
class TransferFunctionDomainExclusion:
    """A main-variable polynomial that must not vanish."""

    polynomial: Polynomial
    origins: tuple[str, ...] = field(compare=False, hash=False)

    def __post_init__(self) -> None:
        from klausurbotpro.domain.polynomial import Polynomial

        if not isinstance(self.polynomial, Polynomial):
            raise TypeError("A domain exclusion requires a Polynomial.")
        origins = tuple(sorted(set(self.origins)))
        if not origins or any(not origin for origin in origins):
            raise ValueError("A domain exclusion requires nonempty origins.")
        object.__setattr__(self, "origins", origins)

    @property
    def description(self) -> str:
        """Return a deterministic human-readable exclusion."""
        from klausurbotpro.domain.polynomial import Polynomial

        polynomial = self.polynomial
        assert isinstance(polynomial, Polynomial)
        return f"{polynomial.expression.canonical_text} != 0"


@dataclass(frozen=True, slots=True)
class RawTransferFunctionLimits:
    """Resource limits for defensive raw transfer-function construction."""

    max_raw_nodes: int = 512
    max_raw_depth: int = 64
    max_integer_digits: int = 128
    max_exponent_abs: int = 32
    max_rationalized_occurrences: int = 4096
    max_intermediate_expressions: int = 2048
    max_translation_steps: int = 4096
    max_numerator_degree: int = 32
    max_denominator_degree: int = 32
    max_parameters: int = 16
    max_prerequisites: int = 64
    max_domain_exclusions: int = 64

    def __post_init__(self) -> None:
        for name in self.__dataclass_fields__:
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive int.")


@dataclass(frozen=True, slots=True)
class RawTransferFunctionCreationResult:
    """A raw transfer function or expected structured diagnostics."""

    value: RawTransferFunction | None
    diagnostics: tuple[Diagnostic, ...] = ()

    def __post_init__(self) -> None:
        diagnostics = tuple(self.diagnostics)
        object.__setattr__(self, "diagnostics", diagnostics)
        has_error = any(
            diagnostic.severity is DiagnosticSeverity.ERROR
            for diagnostic in diagnostics
        )
        if self.value is None and not has_error:
            raise ValueError("A failed result requires an error diagnostic.")
        if self.value is not None and has_error:
            raise ValueError("A successful result cannot contain an error.")

    @property
    def succeeded(self) -> bool:
        """Return whether construction produced a value."""
        return self.value is not None


__all__ = [
    "RawTransferFunctionCreationResult",
    "RawTransferFunctionLimits",
    "TransferFunctionDomainExclusion",
    "TransferFunctionPrerequisite",
    "TransferFunctionPrerequisiteKind",
]
