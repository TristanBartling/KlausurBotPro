"""Exact, immutable parameter substitutions for domain analyses."""

from __future__ import annotations

from dataclasses import dataclass
from keyword import iskeyword
from math import gcd


@dataclass(frozen=True, slots=True)
class ExactRationalValue:
    """A canonical rational number without a SymPy object in the public API."""

    numerator: int
    denominator: int = 1

    def __post_init__(self) -> None:
        if (
            isinstance(self.numerator, bool)
            or not isinstance(self.numerator, int)
            or isinstance(self.denominator, bool)
            or not isinstance(self.denominator, int)
        ):
            raise TypeError("Rational numerator and denominator must be integers.")
        if self.denominator <= 0:
            raise ValueError("A rational denominator must be positive.")
        if gcd(abs(self.numerator), self.denominator) != 1:
            raise ValueError("A rational value must be fully reduced.")


@dataclass(frozen=True, slots=True)
class ParameterAssignment:
    """One exact value assigned to a parameter name."""

    parameter_name: str
    value: ExactRationalValue

    def __post_init__(self) -> None:
        if (
            type(self.parameter_name) is not str
            or not self.parameter_name.isidentifier()
            or iskeyword(self.parameter_name)
        ):
            raise ValueError("A parameter name must be a valid identifier.")
        if type(self.value) is not ExactRationalValue:
            raise TypeError("A parameter value must be an ExactRationalValue.")


@dataclass(frozen=True, slots=True)
class ParameterSubstitutions:
    """A deterministic set of unique exact parameter assignments."""

    assignments: tuple[ParameterAssignment, ...] = ()

    def __post_init__(self) -> None:
        values = tuple(self.assignments)
        if any(type(item) is not ParameterAssignment for item in values):
            raise TypeError("All substitutions must be ParameterAssignment values.")
        names = tuple(item.parameter_name for item in values)
        if len(names) != len(set(names)):
            raise ValueError("A parameter may only be assigned once.")
        object.__setattr__(
            self,
            "assignments",
            tuple(sorted(values, key=lambda item: item.parameter_name)),
        )

    @property
    def parameter_names(self) -> frozenset[str]:
        """Return all assigned parameter names."""

        return frozenset(item.parameter_name for item in self.assignments)
