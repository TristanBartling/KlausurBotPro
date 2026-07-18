"""Controlled raw-tree translation to exact SymPy-backed expressions."""

from __future__ import annotations

import sympy as sp

from klausurbotpro.domain.expression import ExactExpression
from klausurbotpro.domain.raw_algebraic_expression import (
    Add,
    Divide,
    ExactNumber,
    Multiply,
    Power,
    RawAlgebraicExpression,
    Subtract,
    Symbol,
    UnaryMinus,
    UnaryPlus,
)
from klausurbotpro.domain.raw_transfer_function_contracts import (
    RawTransferFunctionLimits,
)


class RawExpressionToExact:
    """Translate validated nodes without parsing strings."""

    def __init__(
        self,
        *,
        symbol_names: frozenset[str],
        limits: RawTransferFunctionLimits,
    ) -> None:
        self._symbols = {
            name: sp.Symbol(name) for name in sorted(symbol_names)
        }
        self._limits = limits
        self._steps = 0

    def translate(self, root: RawAlgebraicExpression) -> ExactExpression:
        """Construct a controlled exact expression."""
        rendered: dict[int, sp.Expr] = {}
        stack: list[tuple[RawAlgebraicExpression, bool]] = [(root, False)]
        while stack:
            node, visited = stack.pop()
            if visited:
                self._steps += 1
                if self._steps > self._limits.max_translation_steps:
                    raise OverflowError("max_translation_steps")
                rendered[id(node)] = self._render(
                    node,
                    tuple(rendered[id(child)] for child in self._children(node)),
                )
                continue
            stack.append((node, True))
            stack.extend(
                (child, False) for child in reversed(self._children(node))
            )
        return ExactExpression._from_sympy(rendered[id(root)])

    def _render(
        self,
        node: RawAlgebraicExpression,
        children: tuple[sp.Expr, ...],
    ) -> sp.Expr:
        if isinstance(node, ExactNumber):
            return sp.Rational(node.numerator, node.denominator)
        if isinstance(node, Symbol):
            return self._symbols[node.name]
        if isinstance(node, UnaryPlus):
            return children[0]
        if isinstance(node, UnaryMinus):
            return -children[0]
        if isinstance(node, Add):
            return children[0] + children[1]
        if isinstance(node, Subtract):
            return children[0] - children[1]
        if isinstance(node, Multiply):
            return children[0] * children[1]
        if isinstance(node, Divide):
            return children[0] / children[1]
        if isinstance(node, Power):
            return sp.Pow(children[0], children[1])
        raise TypeError(f"Unsupported validated node: {type(node).__name__}")

    @staticmethod
    def _children(
        node: RawAlgebraicExpression,
    ) -> tuple[RawAlgebraicExpression, ...]:
        if isinstance(node, (ExactNumber, Symbol)):
            return ()
        if isinstance(node, (UnaryPlus, UnaryMinus)):
            return (node.operand,)
        if isinstance(node, (Add, Subtract, Multiply, Divide, Power)):
            return (node.left, node.right)
        raise TypeError(f"Unsupported validated node: {type(node).__name__}")


__all__ = ["RawExpressionToExact"]
