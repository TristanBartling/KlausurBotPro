"""Defensive validation and copying of untrusted raw expression trees."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from keyword import iskeyword
from math import gcd
from typing import cast

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

_LEAVES = (ExactNumber, Symbol)
_UNARY = (UnaryPlus, UnaryMinus)
_BINARY = (Add, Subtract, Multiply, Divide, Power)
_KNOWN_TYPES = frozenset((*_LEAVES, *_UNARY, *_BINARY))


@dataclass(frozen=True, slots=True)
class RawTreeValidationError(Exception):
    """Expected invalid-tree or resource-limit failure."""

    reason: str
    limit_name: str | None = None
    cyclic: bool = False
    undeclared_symbol: str | None = None


class RawExpressionValidator:
    """Validate exact node types and return a node-disjoint snapshot."""

    def __init__(
        self,
        *,
        variable_name: str,
        allowed_parameter_names: frozenset[str],
        limits: RawTransferFunctionLimits,
    ) -> None:
        self._variable_name = variable_name
        self._allowed_names = allowed_parameter_names | {variable_name}
        self._limits = limits
        self._validated_occurrences = 0

    def validate_and_snapshot(
        self,
        root: RawAlgebraicExpression,
    ) -> RawAlgebraicExpression:
        """Validate every logical occurrence and clone the complete tree."""
        if type(root) not in _KNOWN_TYPES:
            raise RawTreeValidationError("unknown node type")

        completed: dict[tuple[int, tuple[int, ...]], RawAlgebraicExpression] = {}
        stack: list[
            tuple[
                RawAlgebraicExpression,
                int,
                tuple[int, ...],
                tuple[int, ...],
                bool,
            ]
        ] = [(root, 1, (), (), False)]
        occurrences = 0

        while stack:
            node, depth, path, ancestors, visited = stack.pop()
            node_id = id(node)
            key = (node_id, path)
            if visited:
                children = self._children(node)
                if type(node) is Power:
                    exponent = self.evaluate_integer(node.right)
                    if abs(exponent) > self._limits.max_exponent_abs:
                        raise RawTreeValidationError(
                            "exponent limit exceeded",
                            limit_name="max_exponent_abs",
                        )
                copies = tuple(
                    completed[(id(child), (*path, index))]
                    for index, child in enumerate(children)
                )
                completed[key] = self._copy_node(node, copies)
                continue

            if node_id in ancestors:
                raise RawTreeValidationError(
                    "cyclic raw expression",
                    cyclic=True,
                )
            occurrences += 1
            if (
                occurrences
                > self._limits.max_raw_nodes - self._validated_occurrences
            ):
                raise RawTreeValidationError(
                    "raw node limit exceeded",
                    limit_name="max_raw_nodes",
                )
            if depth > self._limits.max_raw_depth:
                raise RawTreeValidationError(
                    "raw depth limit exceeded",
                    limit_name="max_raw_depth",
                )

            children = self._children(node)
            self._validate_leaf(node)

            stack.append((node, depth, path, ancestors, True))
            next_ancestors = (*ancestors, node_id)
            for index in range(len(children) - 1, -1, -1):
                child = children[index]
                stack.append(
                    (
                        child,
                        depth + 1,
                        (*path, index),
                        next_ancestors,
                        False,
                    )
                )

        self._validated_occurrences += occurrences
        return completed[(id(root), ())]

    def evaluate_integer(self, root: RawAlgebraicExpression) -> int:
        """Evaluate a purely numeric exponent without strings or SymPy."""
        result = self._evaluate_numeric(root, ())
        if result.denominator != 1:
            raise RawTreeValidationError("exponent must be an integer")
        return result.numerator

    def _evaluate_numeric(
        self,
        node: RawAlgebraicExpression,
        ancestors: tuple[int, ...],
    ) -> Fraction:
        node_id = id(node)
        if node_id in ancestors:
            raise RawTreeValidationError("cyclic exponent", cyclic=True)
        if type(node) is Symbol:
            raise RawTreeValidationError("exponent must be purely numeric")
        operands = tuple(
            self._evaluate_numeric(child, (*ancestors, node_id))
            for child in self._children(node)
        )
        if type(node) is Power:
            exponent = operands[1]
            if (
                exponent.denominator != 1
                or abs(exponent.numerator) > self._limits.max_exponent_abs
            ):
                raise RawTreeValidationError(
                    "numeric exponent limit exceeded",
                    limit_name="max_exponent_abs",
                )
        try:
            value = self._numeric_value(node, operands)
        except (ZeroDivisionError, OverflowError) as error:
            raise RawTreeValidationError("invalid numeric exponent") from error
        if (
            len(str(abs(value.numerator))) > self._limits.max_integer_digits
            or len(str(value.denominator)) > self._limits.max_integer_digits
        ):
            raise RawTreeValidationError(
                "numeric exponent digit limit exceeded",
                limit_name="max_integer_digits",
            )
        return value

    def _validate_leaf(self, node: RawAlgebraicExpression) -> None:
        if type(node) is ExactNumber:
            numerator = self._safe_attribute(node, "numerator")
            denominator = self._safe_attribute(node, "denominator")
            if (
                isinstance(numerator, bool)
                or not isinstance(numerator, int)
                or isinstance(denominator, bool)
                or not isinstance(denominator, int)
                or denominator <= 0
                or gcd(numerator, denominator) != 1
            ):
                raise RawTreeValidationError("invalid exact number")
            if (
                len(str(abs(numerator))) > self._limits.max_integer_digits
                or len(str(denominator)) > self._limits.max_integer_digits
            ):
                raise RawTreeValidationError(
                    "integer digit limit exceeded",
                    limit_name="max_integer_digits",
                )
        elif type(node) is Symbol:
            name = self._safe_attribute(node, "name")
            if not self._safe_name(name):
                raise RawTreeValidationError("invalid symbol")
            if name not in self._allowed_names:
                raise RawTreeValidationError(
                    "undeclared symbol",
                    undeclared_symbol=cast(str, name),
                )

    def _children(
        self,
        node: RawAlgebraicExpression,
    ) -> tuple[RawAlgebraicExpression, ...]:
        if type(node) not in _KNOWN_TYPES:
            raise RawTreeValidationError("unknown node type")
        if type(node) in _LEAVES:
            return ()
        names = ("operand",) if type(node) in _UNARY else ("left", "right")
        children = tuple(self._safe_attribute(node, name) for name in names)
        if any(type(child) not in _KNOWN_TYPES for child in children):
            raise RawTreeValidationError("invalid child field")
        return cast(tuple[RawAlgebraicExpression, ...], children)

    @staticmethod
    def _safe_attribute(node: object, name: str) -> object:
        try:
            return object.__getattribute__(node, name)
        except (AttributeError, TypeError) as error:
            raise RawTreeValidationError("missing or unsafe field") from error

    @staticmethod
    def _safe_name(name: object) -> bool:
        return (
            isinstance(name, str)
            and name.isidentifier()
            and not iskeyword(name)
            and not name.startswith("__")
            and not name.endswith("__")
        )

    @staticmethod
    def _copy_node(
        node: RawAlgebraicExpression,
        children: tuple[RawAlgebraicExpression, ...],
    ) -> RawAlgebraicExpression:
        if type(node) is ExactNumber:
            return ExactNumber(node.numerator, node.denominator)
        if type(node) is Symbol:
            return Symbol(node.name)
        if type(node) is UnaryPlus:
            return UnaryPlus(children[0])
        if type(node) is UnaryMinus:
            return UnaryMinus(children[0])
        if type(node) is Add:
            return Add(children[0], children[1])
        if type(node) is Subtract:
            return Subtract(children[0], children[1])
        if type(node) is Multiply:
            return Multiply(children[0], children[1])
        if type(node) is Divide:
            return Divide(children[0], children[1])
        if type(node) is Power:
            return Power(children[0], children[1])
        raise RawTreeValidationError("unknown node type")

    @staticmethod
    def _numeric_value(
        node: RawAlgebraicExpression,
        operands: tuple[Fraction, ...],
    ) -> Fraction:
        if type(node) is ExactNumber:
            return Fraction(node.numerator, node.denominator)
        if type(node) is UnaryPlus:
            return operands[0]
        if type(node) is UnaryMinus:
            return -operands[0]
        if type(node) is Add:
            return operands[0] + operands[1]
        if type(node) is Subtract:
            return operands[0] - operands[1]
        if type(node) is Multiply:
            return operands[0] * operands[1]
        if type(node) is Divide:
            return operands[0] / operands[1]
        if type(node) is Power:
            exponent = operands[1]
            if exponent.denominator != 1:
                raise OverflowError
            return operands[0] ** exponent.numerator
        raise RawTreeValidationError("exponent must be purely numeric")


__all__ = ["RawExpressionValidator", "RawTreeValidationError"]
