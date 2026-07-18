"""Immutable, non-executable syntax trees for algebraic user input."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from keyword import iskeyword
from math import gcd


class RawAlgebraicExpression:
    """Base contract for an input-faithful algebraic syntax tree."""

    __slots__ = ()

    @property
    def canonical_tree(self) -> str:
        """Return a deterministic prefix representation of the complete tree."""
        rendered: dict[int, str] = {}
        pending: list[tuple[RawAlgebraicExpression, bool]] = [(self, False)]
        while pending:
            node, visited = pending.pop()
            if visited:
                children = _children(node)
                rendered[id(node)] = _render_node(
                    node,
                    tuple(rendered[id(child)] for child in children),
                )
                continue
            pending.append((node, True))
            pending.extend(
                (child, False) for child in reversed(_children(node))
            )
        return rendered[id(self)]

    @property
    def symbol_names(self) -> frozenset[str]:
        """Return every symbol occurring in the tree."""
        names: set[str] = set()
        pending = [self]
        while pending:
            node = pending.pop()
            if isinstance(node, Symbol):
                names.add(node.name)
            pending.extend(_children(node))
        return frozenset(names)

    @property
    def node_count(self) -> int:
        """Return the number of expression nodes."""
        count = 0
        pending = [self]
        while pending:
            count += 1
            pending.extend(_children(pending.pop()))
        return count

    @property
    def depth(self) -> int:
        """Return the tree depth, counting the root as depth one."""
        maximum = 0
        pending = [(self, 1)]
        while pending:
            node, depth = pending.pop()
            maximum = max(maximum, depth)
            pending.extend(
                (child, depth + 1) for child in _children(node)
            )
        return maximum

    def __eq__(self, other: object) -> bool:
        """Compare the complete input structure, including operator order."""
        return (
            type(self) is type(other)
            and isinstance(other, RawAlgebraicExpression)
            and self.canonical_tree == other.canonical_tree
        )

    def __hash__(self) -> int:
        """Return a stable structural hash independent of Python hash seeding."""
        digest = hashlib.sha256(self.canonical_tree.encode("utf-8")).digest()
        return int.from_bytes(digest[:8], byteorder="big", signed=True)


@dataclass(frozen=True, slots=True, eq=False)
class ExactNumber(RawAlgebraicExpression):
    """An exact, reduced rational literal with a positive denominator."""

    numerator: int
    denominator: int = 1

    def __post_init__(self) -> None:
        if isinstance(self.numerator, bool) or not isinstance(
            self.numerator, int
        ):
            raise TypeError("numerator must be an int.")
        if isinstance(self.denominator, bool) or not isinstance(
            self.denominator, int
        ):
            raise TypeError("denominator must be an int.")
        if self.denominator <= 0:
            raise ValueError("denominator must be greater than zero.")
        if gcd(self.numerator, self.denominator) != 1:
            raise ValueError("ExactNumber must be reduced.")


@dataclass(frozen=True, slots=True, eq=False)
class Symbol(RawAlgebraicExpression):
    """A validated symbolic name."""

    name: str

    def __post_init__(self) -> None:
        if not isinstance(self.name, str):
            raise TypeError("name must be a str.")
        if (
            not self.name.isidentifier()
            or iskeyword(self.name)
            or self.name.startswith("__")
            or self.name.endswith("__")
        ):
            raise ValueError(f"Invalid symbol name: {self.name!r}")


@dataclass(frozen=True, slots=True, eq=False)
class UnaryPlus(RawAlgebraicExpression):
    """An explicitly entered unary plus."""

    operand: RawAlgebraicExpression

    def __post_init__(self) -> None:
        _require_expression(self.operand, "operand")


@dataclass(frozen=True, slots=True, eq=False)
class UnaryMinus(RawAlgebraicExpression):
    """An explicitly entered unary minus."""

    operand: RawAlgebraicExpression

    def __post_init__(self) -> None:
        _require_expression(self.operand, "operand")


@dataclass(frozen=True, slots=True, eq=False)
class Add(RawAlgebraicExpression):
    """An addition retaining its entered operand order."""

    left: RawAlgebraicExpression
    right: RawAlgebraicExpression

    def __post_init__(self) -> None:
        _require_binary_operands(self.left, self.right)


@dataclass(frozen=True, slots=True, eq=False)
class Subtract(RawAlgebraicExpression):
    """A subtraction retaining its entered operand order."""

    left: RawAlgebraicExpression
    right: RawAlgebraicExpression

    def __post_init__(self) -> None:
        _require_binary_operands(self.left, self.right)


@dataclass(frozen=True, slots=True, eq=False)
class Multiply(RawAlgebraicExpression):
    """A multiplication retaining its entered operand order."""

    left: RawAlgebraicExpression
    right: RawAlgebraicExpression

    def __post_init__(self) -> None:
        _require_binary_operands(self.left, self.right)


@dataclass(frozen=True, slots=True, eq=False)
class Divide(RawAlgebraicExpression):
    """A division retained without denominator evaluation."""

    left: RawAlgebraicExpression
    right: RawAlgebraicExpression

    def __post_init__(self) -> None:
        _require_binary_operands(self.left, self.right)


@dataclass(frozen=True, slots=True, eq=False)
class Power(RawAlgebraicExpression):
    """A power retaining both operand trees."""

    left: RawAlgebraicExpression
    right: RawAlgebraicExpression

    def __post_init__(self) -> None:
        _require_binary_operands(self.left, self.right)


def _require_expression(
    value: RawAlgebraicExpression,
    field_name: str,
) -> None:
    if not isinstance(value, RawAlgebraicExpression):
        raise TypeError(f"{field_name} must be a RawAlgebraicExpression.")


def _require_binary_operands(
    left: RawAlgebraicExpression,
    right: RawAlgebraicExpression,
) -> None:
    _require_expression(left, "left")
    _require_expression(right, "right")


def _children(
    node: RawAlgebraicExpression,
) -> tuple[RawAlgebraicExpression, ...]:
    if isinstance(node, (ExactNumber, Symbol)):
        return ()
    if isinstance(node, (UnaryPlus, UnaryMinus)):
        return (node.operand,)
    if isinstance(node, (Add, Subtract, Multiply, Divide, Power)):
        return (node.left, node.right)
    raise TypeError(f"Unsupported raw expression node: {type(node).__name__}")


def _render_node(
    node: RawAlgebraicExpression,
    children: tuple[str, ...],
) -> str:
    if isinstance(node, ExactNumber):
        return f"number({node.numerator}/{node.denominator})"
    if isinstance(node, Symbol):
        return f"symbol({node.name})"
    names = {
        UnaryPlus: "unary_plus",
        UnaryMinus: "unary_minus",
        Add: "add",
        Subtract: "subtract",
        Multiply: "multiply",
        Divide: "divide",
        Power: "power",
    }
    name = names.get(type(node))
    if name is None:
        raise TypeError(f"Unsupported raw expression node: {type(node).__name__}")
    return f"{name}({','.join(children)})"


__all__ = [
    "Add",
    "Divide",
    "ExactNumber",
    "Multiply",
    "Power",
    "RawAlgebraicExpression",
    "Subtract",
    "Symbol",
    "UnaryMinus",
    "UnaryPlus",
]
