"""Immutable contracts for exact polynomial construction and conditions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

from klausurbotpro.domain.diagnostics import Diagnostic, DiagnosticSeverity
from klausurbotpro.domain.expression import ExactExpression

if TYPE_CHECKING:
    from klausurbotpro.domain.polynomial import Polynomial


class PolynomialConditionKind(StrEnum):
    """Stable kinds of explicit mathematical polynomial prerequisites."""

    DEFINITION_NONZERO = "definition_nonzero"
    LEADING_COEFFICIENT_NONZERO = "leading_coefficient_nonzero"


@dataclass(frozen=True, slots=True)
class PolynomialCondition:
    """A normalized exact expression that must be nonzero."""

    kind: PolynomialConditionKind
    expression: ExactExpression

    def __post_init__(self) -> None:
        if not isinstance(self.expression, ExactExpression):
            raise TypeError(
                "PolynomialCondition requires an ExactExpression."
            )

    @property
    def description(self) -> str:
        """Return a deterministic human-readable prerequisite."""
        return f"{self.expression.canonical_text} != 0"


@dataclass(frozen=True, slots=True)
class PolynomialDegreeInfo:
    """Separate generic polynomial degree from an unconditional degree."""

    generic_degree: int | None
    guaranteed_degree: int | None
    conditions: tuple[PolynomialCondition, ...] = ()

    def __post_init__(self) -> None:
        conditions = tuple(self.conditions)
        object.__setattr__(self, "conditions", conditions)
        if any(
            condition.kind
            is not PolynomialConditionKind.LEADING_COEFFICIENT_NONZERO
            for condition in conditions
        ):
            raise ValueError(
                "PolynomialDegreeInfo accepts only leading-coefficient "
                "conditions."
            )
        for name in ("generic_degree", "guaranteed_degree"):
            value = getattr(self, name)
            if value is not None and value < 0:
                raise ValueError(f"{name} must be nonnegative or None.")
        if self.generic_degree is None:
            if self.guaranteed_degree is not None or conditions:
                raise ValueError(
                    "A degree-less polynomial cannot have a guaranteed degree "
                    "or degree conditions."
                )
        elif (
            self.guaranteed_degree is not None
            and self.guaranteed_degree != self.generic_degree
        ):
            raise ValueError(
                "guaranteed_degree must equal generic_degree when present."
            )
        if self.guaranteed_degree is not None and conditions:
            raise ValueError(
                "An unconditional degree cannot require degree conditions."
            )


@dataclass(frozen=True, slots=True)
class PolynomialLimits:
    """Resource limits for domain validation, separate from parser limits."""

    max_degree: int = 32
    max_coefficients: int = 33
    max_structural_terms: int = 33
    max_parameters: int = 16
    max_coefficient_operations: int = 128
    max_expression_nodes: int = 512

    def __post_init__(self) -> None:
        for name in self.__dataclass_fields__:
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be greater than zero.")


@dataclass(frozen=True, slots=True)
class PolynomialCreationResult:
    """A polynomial value or structured expected domain diagnostics."""

    value: Polynomial | None
    diagnostics: tuple[Diagnostic, ...] = ()

    def __post_init__(self) -> None:
        diagnostics = tuple(self.diagnostics)
        object.__setattr__(self, "diagnostics", diagnostics)
        has_error = any(
            diagnostic.severity is DiagnosticSeverity.ERROR
            for diagnostic in diagnostics
        )
        if self.value is None and not has_error:
            raise ValueError(
                "A failed PolynomialCreationResult requires an error diagnostic."
            )
        if self.value is not None and has_error:
            raise ValueError(
                "A successful PolynomialCreationResult cannot contain an error."
            )

    @property
    def succeeded(self) -> bool:
        """Return whether validation produced a polynomial."""
        return self.value is not None
