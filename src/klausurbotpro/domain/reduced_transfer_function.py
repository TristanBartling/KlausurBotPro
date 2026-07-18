"""Immutable semantically constrained reduced transfer function."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

from klausurbotpro.domain.polynomial import Polynomial
from klausurbotpro.domain.raw_transfer_function_contracts import (
    TransferFunctionDomainExclusion,
    TransferFunctionPrerequisite,
)


@dataclass(frozen=True, slots=True, init=False)
class ReducedTransferFunction:
    """A reduced polynomial pair retaining the complete raw-domain contract."""

    variable_name: str
    numerator: Polynomial
    denominator: Polynomial
    prerequisites: tuple[TransferFunctionPrerequisite, ...]
    domain_exclusions: tuple[TransferFunctionDomainExclusion, ...]
    used_parameter_names: frozenset[str]
    is_zero: bool

    def __new__(cls) -> ReducedTransferFunction:
        """Prevent construction outside the controlled reducer."""
        raise TypeError(
            "ReducedTransferFunction values must be created by "
            "TransferFunctionReducer."
        )

    @classmethod
    def _create(
        cls,
        *,
        variable_name: str,
        numerator: Polynomial,
        denominator: Polynomial,
        prerequisites: tuple[TransferFunctionPrerequisite, ...],
        domain_exclusions: tuple[TransferFunctionDomainExclusion, ...],
    ) -> ReducedTransferFunction:
        """Create a value from a fully validated reduced pair."""
        instance = object.__new__(cls)
        object.__setattr__(instance, "variable_name", variable_name)
        object.__setattr__(instance, "numerator", numerator)
        object.__setattr__(instance, "denominator", denominator)
        object.__setattr__(instance, "prerequisites", tuple(prerequisites))
        object.__setattr__(instance, "domain_exclusions", tuple(domain_exclusions))
        object.__setattr__(
            instance,
            "used_parameter_names",
            _used_parameter_names(
                variable_name,
                numerator,
                denominator,
                prerequisites,
                domain_exclusions,
            ),
        )
        object.__setattr__(instance, "is_zero", numerator.is_zero)
        return instance

    def __eq__(self, other: object) -> bool:
        """Compare reduced mathematical identity and retained domain."""
        return (
            isinstance(other, ReducedTransferFunction)
            and self.variable_name == other.variable_name
            and self.numerator == other.numerator
            and self.denominator == other.denominator
            and self.prerequisites == other.prerequisites
            and self.domain_exclusions == other.domain_exclusions
        )

    def __hash__(self) -> int:
        """Return a stable hash matching reduced mathematical identity."""
        parts = (
            self.variable_name,
            str(hash(self.numerator)),
            str(hash(self.denominator)),
            *(f"p:{item.kind.value}:{item.description}" for item in self.prerequisites),
            *(
                f"d:{item.polynomial.expression.canonical_text}"
                for item in self.domain_exclusions
            ),
        )
        digest = sha256("\0".join(parts).encode("utf-8")).digest()[:8]
        return int.from_bytes(digest, byteorder="big", signed=True)


def _used_parameter_names(
    variable_name: str,
    numerator: Polynomial,
    denominator: Polynomial,
    prerequisites: tuple[TransferFunctionPrerequisite, ...],
    domain_exclusions: tuple[TransferFunctionDomainExclusion, ...],
) -> frozenset[str]:
    names = set(numerator.used_parameter_names)
    names.update(denominator.used_parameter_names)
    for prerequisite in prerequisites:
        for expression in prerequisite.expressions:
            names.update(expression.symbol_names)
    for exclusion in domain_exclusions:
        names.update(exclusion.polynomial.used_parameter_names)
    names.discard(variable_name)
    return frozenset(names)


__all__ = ["ReducedTransferFunction"]
