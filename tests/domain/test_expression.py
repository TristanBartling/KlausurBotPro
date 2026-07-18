"""Tests for the exact-expression value object."""

from dataclasses import FrozenInstanceError

import pytest
import sympy as sp

from klausurbotpro.domain import ExactExpression


def test_exact_expression_has_value_equality_and_stable_hash() -> None:
    symbol = sp.Symbol("s")
    first = ExactExpression._from_sympy(symbol + 1)
    second = ExactExpression._from_sympy(symbol + 1)

    assert first == second
    assert hash(first) == hash(second)
    assert {first, second} == {first}


def test_exact_expression_exposes_safe_representations_and_used_symbols() -> None:
    expression = ExactExpression._from_sympy(
        sp.Symbol("K") * sp.Symbol("s") + 1
    )

    assert expression.symbol_names == frozenset({"K", "s"})
    assert expression.canonical_text == "K*s + 1"
    assert expression.latex == "K s + 1"


def test_exact_expression_rejects_float_atoms() -> None:
    with pytest.raises(ValueError, match="Float"):
        ExactExpression._from_sympy(sp.Float(0.5) + sp.Symbol("s"))


def test_exact_expression_rejects_non_expression() -> None:
    with pytest.raises(TypeError, match="SymPy Expr"):
        ExactExpression._from_sympy("s + 1")


def test_exact_expression_is_immutable_and_has_no_string_parser() -> None:
    expression = ExactExpression._from_sympy(sp.Integer(1))

    assert not hasattr(expression, "from_string")
    assert not hasattr(expression, "parse")
    with pytest.raises(FrozenInstanceError):
        expression._expression = sp.Integer(2)  # type: ignore[misc]
