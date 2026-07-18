"""Tests for the immutable, input-faithful algebraic syntax tree."""

import inspect
from dataclasses import FrozenInstanceError

import pytest

import klausurbotpro.domain.raw_algebraic_expression as raw_expression_module
from klausurbotpro.domain import (
    Add,
    Divide,
    ExactNumber,
    Multiply,
    Power,
    Subtract,
    Symbol,
    UnaryMinus,
    UnaryPlus,
)


def test_raw_tree_exposes_deterministic_structure_metrics_and_symbols() -> None:
    tree = Add(
        Multiply(Symbol("K"), Power(Symbol("s"), ExactNumber(2))),
        UnaryMinus(ExactNumber(3, 2)),
    )

    assert tree.canonical_tree == (
        "add(multiply(symbol(K),power(symbol(s),number(2/1))),"
        "unary_minus(number(3/2)))"
    )
    assert tree.symbol_names == frozenset({"K", "s"})
    assert tree.node_count == 8
    assert tree.depth == 4


@pytest.mark.parametrize(
    ("first", "second"),
    [
        (Divide(Symbol("K"), Symbol("K")), ExactNumber(1)),
        (Subtract(Symbol("K"), Symbol("K")), ExactNumber(0)),
        (
            Multiply(
                Subtract(Symbol("K"), ExactNumber(1)),
                Add(Symbol("T"), ExactNumber(1)),
            ),
            Multiply(
                Add(Symbol("T"), ExactNumber(1)),
                Subtract(Symbol("K"), ExactNumber(1)),
            ),
        ),
        (
            Divide(Divide(Symbol("K"), Symbol("T")), Symbol("s")),
            Divide(
                Symbol("K"),
                Divide(Symbol("T"), Symbol("s")),
            ),
        ),
        (
            Add(Add(Symbol("K"), Symbol("T")), Symbol("s")),
            Add(Symbol("K"), Add(Symbol("T"), Symbol("s"))),
        ),
        (UnaryPlus(Symbol("s")), Symbol("s")),
    ],
)
def test_algebraically_related_but_structurally_distinct_trees_stay_distinct(
    first: object,
    second: object,
) -> None:
    assert first != second
    assert hash(first) != hash(second)


def test_structural_equality_and_hash_support_dictionary_keys() -> None:
    first = Divide(Symbol("K"), Add(Symbol("T"), ExactNumber(1)))
    second = Divide(Symbol("K"), Add(Symbol("T"), ExactNumber(1)))

    assert first == second
    assert hash(first) == hash(second)
    assert {first: "raw"}[second] == "raw"


def test_nodes_are_immutable_and_validate_construction() -> None:
    number = ExactNumber(3, 2)

    with pytest.raises(FrozenInstanceError):
        number.numerator = 4  # type: ignore[misc]
    with pytest.raises(ValueError, match="reduced"):
        ExactNumber(2, 4)
    with pytest.raises(ValueError, match="greater than zero"):
        ExactNumber(1, 0)
    with pytest.raises(TypeError, match="RawAlgebraicExpression"):
        Add(Symbol("s"), 1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Invalid symbol"):
        Symbol("__class__")


def test_unary_and_power_nodes_retain_their_complete_operands() -> None:
    tree = UnaryMinus(
        Power(
            Symbol("s"),
            Power(ExactNumber(2), ExactNumber(3)),
        )
    )

    assert tree.canonical_tree == (
        "unary_minus(power(symbol(s),power(number(2/1),number(3/1))))"
    )


def test_raw_tree_module_has_no_sympy_or_parsing_dependency() -> None:
    source = inspect.getsource(raw_expression_module).lower()

    assert "sympy" not in source
    assert "klausurbotpro.parsing" not in source
