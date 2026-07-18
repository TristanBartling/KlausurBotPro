"""Immutable exact-expression value object backed internally by SymPy."""

from dataclasses import dataclass
from hashlib import sha256

import sympy as sp


@dataclass(frozen=True, slots=True, init=False)
class ExactExpression:
    """An exact symbolic value without exposing raw-string evaluation.

    Instances are created only by trusted fachkern code through
    :meth:`_from_sympy`. The underscored :meth:`_as_sympy` method is the
    internal boundary for later mathematical domain modules; it must never be
    used to evaluate user input.
    """

    _expression: sp.Expr

    @classmethod
    def _from_sympy(cls, expression: sp.Expr) -> "ExactExpression":
        """Create an instance from an already controlled SymPy expression."""
        if not isinstance(expression, sp.Expr):
            raise TypeError("ExactExpression requires a SymPy Expr.")
        if expression.has(sp.Float):
            raise ValueError("ExactExpression must not contain Float atoms.")

        instance = object.__new__(cls)
        object.__setattr__(instance, "_expression", expression)
        return instance

    @property
    def symbol_names(self) -> frozenset[str]:
        """Return the names of symbols that actually occur in the value."""
        return frozenset(symbol.name for symbol in self._expression.free_symbols)

    @property
    def canonical_text(self) -> str:
        """Return a deterministic plain mathematical representation."""
        return str(sp.sstr(self._expression, order="lex"))

    @property
    def latex(self) -> str:
        """Return a LaTeX representation suitable for later presentation."""
        return str(sp.latex(self._expression, order="lex"))

    def _as_sympy(self) -> sp.Expr:
        """Return the internal value for trusted mathematical domain modules."""
        return self._expression

    def __hash__(self) -> int:
        """Return a stable structural hash for the exact expression."""
        canonical_structure = sp.srepr(self._expression).encode("utf-8")
        digest = sha256(canonical_structure).digest()[:8]
        return int.from_bytes(digest, byteorder="big", signed=True)
