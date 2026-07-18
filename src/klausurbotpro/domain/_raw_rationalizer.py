"""Non-cancelling rationalization of validated raw algebraic trees."""

from __future__ import annotations

from dataclasses import dataclass

from klausurbotpro.domain._raw_expression_validator import (
    RawExpressionValidator,
)
from klausurbotpro.domain.raw_algebraic_expression import (
    Add,
    Divide,
    ExactNumber,
    Multiply,
    Power,
    RawAlgebraicExpression,
    Subtract,
    UnaryMinus,
    UnaryPlus,
)
from klausurbotpro.domain.raw_transfer_function_contracts import (
    RawTransferFunctionLimits,
)


@dataclass(frozen=True, slots=True)
class DivisorRecord:
    """A rationalized divisor numerator and deterministic raw origin."""

    numerator_tree: RawAlgebraicExpression
    origin: str


@dataclass(frozen=True, slots=True)
class RawRationalPair:
    """An unreduced numerator/denominator tree pair."""

    numerator_tree: RawAlgebraicExpression
    denominator_tree: RawAlgebraicExpression
    divisor_records: tuple[DivisorRecord, ...]
    numerator_occurrences: int
    denominator_occurrences: int


@dataclass(frozen=True, slots=True)
class RawRationalizationError(Exception):
    """Expected rationalization growth or resource failure."""

    reason: str
    limit_name: str


class RawRationalizer:
    """Translate raw algebra into a rational pair without cancellation."""

    def __init__(
        self,
        *,
        validator: RawExpressionValidator,
        limits: RawTransferFunctionLimits,
    ) -> None:
        self._validator = validator
        self._limits = limits
        self._intermediates = 0
        self._steps = 0

    def rationalize(
        self,
        expression: RawAlgebraicExpression,
        *,
        origin: str,
    ) -> RawRationalPair:
        """Rationalize one validated tree."""
        return self._visit(expression, origin, ())

    def combine_separated(
        self,
        numerator: RawRationalPair,
        denominator: RawRationalPair,
    ) -> RawRationalPair:
        """Combine separately entered numerator and denominator fields."""
        numerator_tree, numerator_count = self._multiply(
            numerator.numerator_tree,
            numerator.numerator_occurrences,
            denominator.denominator_tree,
            denominator.denominator_occurrences,
        )
        denominator_tree, denominator_count = self._multiply(
            numerator.denominator_tree,
            numerator.denominator_occurrences,
            denominator.numerator_tree,
            denominator.numerator_occurrences,
        )
        records = (
            *numerator.divisor_records,
            *denominator.divisor_records,
            DivisorRecord(
                denominator.numerator_tree,
                "denominator:field",
            ),
        )
        return self._pair(
            numerator_tree,
            numerator_count,
            denominator_tree,
            denominator_count,
            records,
        )

    def _visit(
        self,
        node: RawAlgebraicExpression,
        origin: str,
        path: tuple[int, ...],
    ) -> RawRationalPair:
        self._step()
        node_origin = f"{origin}:{'.'.join(map(str, path)) or 'root'}"
        if isinstance(node, (ExactNumber,)) or not self._children(node):
            return self._pair(node, 1, ExactNumber(1), 1, ())
        if isinstance(node, (UnaryPlus, UnaryMinus)):
            operand = self._visit(node.operand, origin, (*path, 0))
            if isinstance(node, UnaryPlus):
                return operand
            numerator, count = self._unary_minus(
                operand.numerator_tree,
                operand.numerator_occurrences,
            )
            return self._pair(
                numerator,
                count,
                operand.denominator_tree,
                operand.denominator_occurrences,
                operand.divisor_records,
            )

        assert isinstance(node, (Add, Subtract, Multiply, Divide, Power))
        if isinstance(node, Power):
            left = self._visit(node.left, origin, (*path, 0))
            exponent = self._validator.evaluate_integer(node.right)
            records = left.divisor_records
            if exponent == 0:
                return self._pair(
                    ExactNumber(1),
                    1,
                    ExactNumber(1),
                    1,
                    records,
                )
            absolute = abs(exponent)
            powered_numerator, numerator_count = self._power(
                left.numerator_tree,
                left.numerator_occurrences,
                absolute,
            )
            powered_denominator, denominator_count = self._power(
                left.denominator_tree,
                left.denominator_occurrences,
                absolute,
            )
            if exponent > 0:
                return self._pair(
                    powered_numerator,
                    numerator_count,
                    powered_denominator,
                    denominator_count,
                    records,
                )
            return self._pair(
                powered_denominator,
                denominator_count,
                powered_numerator,
                numerator_count,
                (*records, DivisorRecord(left.numerator_tree, node_origin)),
            )

        left = self._visit(node.left, origin, (*path, 0))
        right = self._visit(node.right, origin, (*path, 1))
        records = (*left.divisor_records, *right.divisor_records)
        if isinstance(node, (Add, Subtract)):
            left_term, left_count = self._multiply(
                left.numerator_tree,
                left.numerator_occurrences,
                right.denominator_tree,
                right.denominator_occurrences,
            )
            right_term, right_count = self._multiply(
                right.numerator_tree,
                right.numerator_occurrences,
                left.denominator_tree,
                left.denominator_occurrences,
            )
            numerator, numerator_count = self._binary(
                Add if isinstance(node, Add) else Subtract,
                left_term,
                left_count,
                right_term,
                right_count,
            )
            denominator, denominator_count = self._multiply(
                left.denominator_tree,
                left.denominator_occurrences,
                right.denominator_tree,
                right.denominator_occurrences,
            )
            return self._pair(
                numerator,
                numerator_count,
                denominator,
                denominator_count,
                records,
            )
        if isinstance(node, Multiply):
            numerator, numerator_count = self._multiply(
                left.numerator_tree,
                left.numerator_occurrences,
                right.numerator_tree,
                right.numerator_occurrences,
            )
            denominator, denominator_count = self._multiply(
                left.denominator_tree,
                left.denominator_occurrences,
                right.denominator_tree,
                right.denominator_occurrences,
            )
            return self._pair(
                numerator,
                numerator_count,
                denominator,
                denominator_count,
                records,
            )
        if isinstance(node, Divide):
            numerator, numerator_count = self._multiply(
                left.numerator_tree,
                left.numerator_occurrences,
                right.denominator_tree,
                right.denominator_occurrences,
            )
            denominator, denominator_count = self._multiply(
                left.denominator_tree,
                left.denominator_occurrences,
                right.numerator_tree,
                right.numerator_occurrences,
            )
            return self._pair(
                numerator,
                numerator_count,
                denominator,
                denominator_count,
                (*records, DivisorRecord(right.numerator_tree, node_origin)),
            )
        raise AssertionError(f"Validated node was not handled: {type(node).__name__}")

    @staticmethod
    def _children(
        node: RawAlgebraicExpression,
    ) -> tuple[RawAlgebraicExpression, ...]:
        if isinstance(node, (ExactNumber,)):
            return ()
        if isinstance(node, (UnaryPlus, UnaryMinus)):
            return (node.operand,)
        if isinstance(node, (Add, Subtract, Multiply, Divide, Power)):
            return (node.left, node.right)
        return ()

    def _pair(
        self,
        numerator: RawAlgebraicExpression,
        numerator_count: int,
        denominator: RawAlgebraicExpression,
        denominator_count: int,
        records: tuple[DivisorRecord, ...],
    ) -> RawRationalPair:
        self._intermediate()
        self._check_occurrences(numerator_count)
        self._check_occurrences(denominator_count)
        return RawRationalPair(
            numerator,
            denominator,
            tuple(records),
            numerator_count,
            denominator_count,
        )

    def _multiply(
        self,
        left: RawAlgebraicExpression,
        left_count: int,
        right: RawAlgebraicExpression,
        right_count: int,
    ) -> tuple[RawAlgebraicExpression, int]:
        return self._binary(Multiply, left, left_count, right, right_count)

    def _binary(
        self,
        node_type: type[Add] | type[Subtract] | type[Multiply],
        left: RawAlgebraicExpression,
        left_count: int,
        right: RawAlgebraicExpression,
        right_count: int,
    ) -> tuple[RawAlgebraicExpression, int]:
        count = self._sum_occurrences(1, left_count, right_count)
        self._intermediate()
        return node_type(left, right), count

    def _unary_minus(
        self,
        operand: RawAlgebraicExpression,
        operand_count: int,
    ) -> tuple[RawAlgebraicExpression, int]:
        count = self._sum_occurrences(1, operand_count)
        self._intermediate()
        return UnaryMinus(operand), count

    def _power(
        self,
        base: RawAlgebraicExpression,
        base_count: int,
        exponent: int,
    ) -> tuple[RawAlgebraicExpression, int]:
        count = self._sum_occurrences(2, base_count)
        self._intermediate()
        return Power(base, ExactNumber(exponent)), count

    def _sum_occurrences(self, *values: int) -> int:
        total = 0
        for value in values:
            if value > self._limits.max_rationalized_occurrences - total:
                raise RawRationalizationError(
                    "rationalized occurrence limit exceeded",
                    "max_rationalized_occurrences",
                )
            total += value
        return total

    def _check_occurrences(self, value: int) -> None:
        if value > self._limits.max_rationalized_occurrences:
            raise RawRationalizationError(
                "rationalized occurrence limit exceeded",
                "max_rationalized_occurrences",
            )

    def _intermediate(self) -> None:
        self._intermediates += 1
        if self._intermediates > self._limits.max_intermediate_expressions:
            raise RawRationalizationError(
                "intermediate expression limit exceeded",
                "max_intermediate_expressions",
            )

    def _step(self) -> None:
        self._steps += 1
        if self._steps > self._limits.max_translation_steps:
            raise RawRationalizationError(
                "rationalization step limit exceeded",
                "max_translation_steps",
            )


__all__ = [
    "DivisorRecord",
    "RawRationalPair",
    "RawRationalizationError",
    "RawRationalizer",
]
