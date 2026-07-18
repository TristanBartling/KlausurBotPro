"""Immutable validated transfer function before pairwise reduction."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

from klausurbotpro.domain.polynomial import Polynomial
from klausurbotpro.domain.polynomial_contracts import PolynomialCondition
from klausurbotpro.domain.raw_transfer_function_contracts import (
    TransferFunctionDomainExclusion,
    TransferFunctionPrerequisite,
)
from klausurbotpro.domain.transfer_function_input import TransferFunctionInput


@dataclass(frozen=True, slots=True, init=False)
class RawTransferFunction:
    """A validated numerator/denominator pair with raw-domain restrictions."""

    variable_name: str
    numerator: Polynomial
    denominator: Polynomial
    used_parameter_names: frozenset[str]
    input_snapshot: TransferFunctionInput
    prerequisites: tuple[TransferFunctionPrerequisite, ...]
    domain_exclusions: tuple[TransferFunctionDomainExclusion, ...]
    numerator_conditions: tuple[PolynomialCondition, ...]
    denominator_conditions: tuple[PolynomialCondition, ...]
    is_zero: bool

    def __new__(cls) -> RawTransferFunction:
        """Prevent construction outside the controlled factory."""
        raise TypeError(
            "RawTransferFunction values must be created by "
            "RawTransferFunctionFactory."
        )

    @classmethod
    def _create(
        cls,
        *,
        variable_name: str,
        numerator: Polynomial,
        denominator: Polynomial,
        input_snapshot: TransferFunctionInput,
        prerequisites: tuple[TransferFunctionPrerequisite, ...],
        domain_exclusions: tuple[TransferFunctionDomainExclusion, ...],
    ) -> RawTransferFunction:
        """Create a value after complete validation."""
        instance = object.__new__(cls)
        object.__setattr__(instance, "variable_name", variable_name)
        object.__setattr__(instance, "numerator", numerator)
        object.__setattr__(instance, "denominator", denominator)
        object.__setattr__(
            instance,
            "used_parameter_names",
            input_snapshot.used_symbol_names - {variable_name},
        )
        object.__setattr__(instance, "input_snapshot", input_snapshot)
        object.__setattr__(instance, "prerequisites", tuple(prerequisites))
        object.__setattr__(
            instance,
            "domain_exclusions",
            tuple(domain_exclusions),
        )
        object.__setattr__(
            instance,
            "numerator_conditions",
            numerator.conditions,
        )
        object.__setattr__(
            instance,
            "denominator_conditions",
            denominator.conditions,
        )
        object.__setattr__(instance, "is_zero", numerator.is_zero)
        return instance

    def __eq__(self, other: object) -> bool:
        """Compare the mathematical unreduced identity only."""
        return (
            isinstance(other, RawTransferFunction)
            and self.variable_name == other.variable_name
            and self.numerator == other.numerator
            and self.denominator == other.denominator
            and self.prerequisites == other.prerequisites
            and self.domain_exclusions == other.domain_exclusions
        )

    def __hash__(self) -> int:
        """Return a stable hash matching mathematical raw identity."""
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


__all__ = ["RawTransferFunction"]
