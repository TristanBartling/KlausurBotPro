"""Classification and normalization of raw transfer-function conditions."""

from __future__ import annotations

from dataclasses import dataclass

import sympy as sp

from klausurbotpro.domain.expression import ExactExpression
from klausurbotpro.domain.polynomial import Polynomial
from klausurbotpro.domain.polynomial_contracts import PolynomialConditionKind
from klausurbotpro.domain.raw_transfer_function_contracts import (
    RawTransferFunctionLimits,
    TransferFunctionDomainExclusion,
    TransferFunctionPrerequisite,
    TransferFunctionPrerequisiteKind,
)


@dataclass(frozen=True, slots=True)
class RawConditionLimitError(Exception):
    """An expected condition-count limit failure."""

    limit_name: str


class RawTransferConditionCollector:
    """Collect parameter predicates separately from variable exclusions."""

    def __init__(
        self,
        *,
        variable_name: str,
        limits: RawTransferFunctionLimits,
    ) -> None:
        self._variable_name = variable_name
        self._limits = limits
        self._prerequisites: list[TransferFunctionPrerequisite] = []
        self._exclusions: list[TransferFunctionDomainExclusion] = []

    def add(self, polynomial: Polynomial, *, origin: str) -> bool:
        """Classify one nonzero polynomial and return conditional validity."""
        conditional = False
        for condition in polynomial.conditions:
            if condition.kind is PolynomialConditionKind.DEFINITION_NONZERO:
                self._prerequisites.append(
                    TransferFunctionPrerequisite(
                        TransferFunctionPrerequisiteKind.EXPRESSION_NONZERO,
                        (condition.expression,),
                        (origin,),
                    )
                )
                conditional = True

        nonzero_arguments = _possible_nonzero_coefficient_numerators(polynomial)
        certainly_nonzero = any(
            argument._as_sympy().is_zero is False
            and not argument.symbol_names
            for argument in nonzero_arguments
        )
        if not certainly_nonzero:
            kind = (
                TransferFunctionPrerequisiteKind.EXPRESSION_NONZERO
                if polynomial.is_constant or len(nonzero_arguments) == 1
                else TransferFunctionPrerequisiteKind.NOT_ALL_ZERO
            )
            self._prerequisites.append(
                TransferFunctionPrerequisite(
                    kind,
                    (
                        (nonzero_arguments[0],)
                        if kind
                        is TransferFunctionPrerequisiteKind.EXPRESSION_NONZERO
                        else nonzero_arguments
                    ),
                    (origin,),
                )
            )
            conditional = True

        if self._variable_name in polynomial.expression.symbol_names:
            self._exclusions.append(
                TransferFunctionDomainExclusion(polynomial, (origin,))
            )
        return conditional

    def normalized(
        self,
    ) -> tuple[
        tuple[TransferFunctionPrerequisite, ...],
        tuple[TransferFunctionDomainExclusion, ...],
    ]:
        """Return deterministically deduplicated conditions."""
        prerequisites = self._normalize_prerequisites()
        exclusions = self._normalize_exclusions()
        return prerequisites, exclusions

    def _normalize_prerequisites(
        self,
    ) -> tuple[TransferFunctionPrerequisite, ...]:
        grouped: dict[
            tuple[str, tuple[str, ...]],
            tuple[TransferFunctionPrerequisite, set[str]],
        ] = {}
        for value in self._prerequisites:
            key = (
                value.kind.value,
                tuple(item.canonical_text for item in value.expressions),
            )
            existing = grouped.get(key)
            if existing is None:
                grouped[key] = (value, set(value.origins))
            else:
                existing[1].update(value.origins)
        if len(grouped) > self._limits.max_prerequisites:
            raise RawConditionLimitError("max_prerequisites")
        return tuple(
            TransferFunctionPrerequisite(value.kind, value.expressions, tuple(origins))
            for _, (value, origins) in sorted(grouped.items())
        )

    def _normalize_exclusions(
        self,
    ) -> tuple[TransferFunctionDomainExclusion, ...]:
        grouped: dict[
            tuple[str, str],
            tuple[TransferFunctionDomainExclusion, set[str]],
        ] = {}
        for value in self._exclusions:
            key = (
                value.polynomial.variable_name,
                value.polynomial.expression.canonical_text,
            )
            existing = grouped.get(key)
            if existing is None:
                grouped[key] = (value, set(value.origins))
            else:
                existing[1].update(value.origins)
        if len(grouped) > self._limits.max_domain_exclusions:
            raise RawConditionLimitError("max_domain_exclusions")
        return tuple(
            TransferFunctionDomainExclusion(value.polynomial, tuple(origins))
            for _, (value, origins) in sorted(grouped.items())
        )


def _possible_nonzero_coefficient_numerators(
    polynomial: Polynomial,
) -> tuple[ExactExpression, ...]:
    values: dict[str, ExactExpression] = {}
    for coefficient in polynomial.coefficients:
        numerator, _ = sp.fraction(coefficient._as_sympy())
        _, primitive = numerator.as_content_primitive()
        if primitive.could_extract_minus_sign():
            primitive = -primitive
        primitive = _without_integer_multiplicities(primitive)
        if primitive.is_zero is not True:
            exact = ExactExpression._from_sympy(primitive)
            values[exact.canonical_text] = exact
    return tuple(values[key] for key in sorted(values))


def _without_integer_multiplicities(expression: sp.Expr) -> sp.Expr:
    powers = expression.as_powers_dict()
    factors = tuple(
        (
            base
            if exponent.is_Integer and exponent != 0
            else sp.Pow(base, exponent)
        )
        for base, exponent in sorted(
            powers.items(),
            key=lambda item: sp.sstr(item[0], order="lex"),
        )
    )
    return sp.Mul(*factors)


__all__ = [
    "RawConditionLimitError",
    "RawTransferConditionCollector",
]
