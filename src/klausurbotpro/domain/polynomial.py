"""Immutable exact univariate polynomial value object."""

from dataclasses import dataclass, field
from hashlib import sha256

import sympy as sp

from klausurbotpro.domain.expression import ExactExpression
from klausurbotpro.domain.polynomial_contracts import (
    PolynomialCondition,
    PolynomialDegreeInfo,
)


@dataclass(frozen=True, slots=True, init=False)
class Polynomial:
    """Canonical polynomial value created only by the domain factory."""

    variable_name: str
    used_parameter_names: frozenset[str]
    expression: ExactExpression
    coefficients: tuple[ExactExpression, ...]
    degree_info: PolynomialDegreeInfo
    leading_coefficient: ExactExpression
    constant_coefficient: ExactExpression
    structural_term_count: int
    is_zero: bool
    is_constant: bool
    conditions: tuple[PolynomialCondition, ...]
    _polynomial: sp.Poly = field(compare=False, hash=False, repr=False)

    def __new__(cls) -> "Polynomial":
        """Prevent construction outside the controlled internal factory."""
        raise TypeError("Polynomial values must be created by PolynomialFactory.")

    @classmethod
    def _create(
        cls,
        *,
        variable_name: str,
        used_parameter_names: frozenset[str],
        expression: ExactExpression,
        coefficients: tuple[ExactExpression, ...],
        degree_info: PolynomialDegreeInfo,
        structural_term_count: int,
        conditions: tuple[PolynomialCondition, ...],
        polynomial: sp.Poly,
    ) -> "Polynomial":
        """Create a value from an already validated canonical polynomial."""
        if not coefficients:
            raise ValueError("A Polynomial requires at least one coefficient.")

        instance = object.__new__(cls)
        object.__setattr__(instance, "variable_name", variable_name)
        object.__setattr__(
            instance,
            "used_parameter_names",
            frozenset(used_parameter_names),
        )
        object.__setattr__(instance, "expression", expression)
        object.__setattr__(instance, "coefficients", tuple(coefficients))
        object.__setattr__(instance, "degree_info", degree_info)
        object.__setattr__(
            instance,
            "leading_coefficient",
            coefficients[0],
        )
        object.__setattr__(
            instance,
            "constant_coefficient",
            coefficients[-1],
        )
        object.__setattr__(
            instance,
            "structural_term_count",
            structural_term_count,
        )
        is_zero = degree_info.generic_degree is None
        object.__setattr__(instance, "is_zero", is_zero)
        object.__setattr__(
            instance,
            "is_constant",
            is_zero or degree_info.generic_degree == 0,
        )
        object.__setattr__(instance, "conditions", tuple(conditions))
        object.__setattr__(instance, "_polynomial", polynomial)
        return instance

    def _as_sympy_poly(self) -> sp.Poly:
        """Return the internal value for trusted mathematical domain modules."""
        return self._polynomial

    def __hash__(self) -> int:
        """Return a deterministic hash independent of validation context."""
        parts = [
            self.variable_name,
            self.expression.canonical_text,
            *sorted(self.used_parameter_names),
            *(coefficient.canonical_text for coefficient in self.coefficients),
            str(self.degree_info.generic_degree),
            str(self.degree_info.guaranteed_degree),
            *(
                f"{condition.kind.value}:{condition.expression.canonical_text}"
                for condition in self.conditions
            ),
        ]
        digest = sha256("\0".join(parts).encode("utf-8")).digest()[:8]
        return int.from_bytes(digest, byteorder="big", signed=True)
