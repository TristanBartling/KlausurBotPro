"""Tests for the exact immutable Polynomial value object."""

from dataclasses import FrozenInstanceError

import pytest
import sympy as sp

from klausurbotpro.domain import ExactExpression, Polynomial, PolynomialFactory


def _exact(expression: sp.Expr) -> ExactExpression:
    return ExactExpression._from_sympy(expression)


def _polynomial(
    expression: sp.Expr,
    *,
    parameters: frozenset[str] = frozenset(),
) -> Polynomial:
    result = PolynomialFactory().create(
        _exact(expression),
        declared_parameter_names=parameters,
    )
    assert result.succeeded, result.diagnostics
    assert result.value is not None
    return result.value


def test_polynomial_cannot_be_freely_constructed() -> None:
    with pytest.raises(TypeError):
        Polynomial()


def test_polynomial_exposes_no_public_sympy_values() -> None:
    s, K = sp.symbols("s K")
    polynomial = _polynomial(K * s + 1, parameters=frozenset({"K"}))

    public_values = (
        polynomial.variable_name,
        polynomial.used_parameter_names,
        polynomial.expression,
        polynomial.coefficients,
        polynomial.degree_info,
        polynomial.leading_coefficient,
        polynomial.constant_coefficient,
        polynomial.structural_term_count,
        polynomial.is_zero,
        polynomial.is_constant,
        polynomial.conditions,
    )

    assert not any(
        isinstance(value, (sp.Expr, sp.Poly))
        for value in public_values
    )


def test_polynomial_is_immutable_hashable_and_a_dictionary_key() -> None:
    s = sp.Symbol("s")
    first = _polynomial(s**2 + 3 * s + 2)
    second = _polynomial((s + 1) * (s + 2))

    assert first == second
    assert hash(first) == hash(second)
    assert {first: "value"}[second] == "value"
    with pytest.raises(FrozenInstanceError):
        first.variable_name = "z"  # type: ignore[misc]


def test_declared_but_unused_parameters_do_not_affect_value_identity() -> None:
    s = sp.Symbol("s")

    plain = _polynomial(s + 1)
    with_k = _polynomial(s + 1, parameters=frozenset({"K"}))
    with_k_t = _polynomial(s + 1, parameters=frozenset({"K", "T"}))

    assert plain == with_k == with_k_t
    assert hash(plain) == hash(with_k) == hash(with_k_t)
    assert plain.used_parameter_names == frozenset()
    assert (
        plain._as_sympy_poly().domain
        == with_k._as_sympy_poly().domain
        == with_k_t._as_sympy_poly().domain
        == sp.QQ
    )


@pytest.mark.parametrize(
    "expression",
    [
        sp.Integer(0),
        sp.Add(sp.Symbol("s"), -sp.Symbol("s"), evaluate=False),
        sp.Add(sp.Symbol("K"), -sp.Symbol("K"), evaluate=False),
        sp.Mul(0, sp.Symbol("s") ** 5, evaluate=False),
    ],
)
def test_zero_polynomial_has_canonical_semantics(
    expression: sp.Expr,
) -> None:
    parameters = (
        frozenset({"K"}) if expression.has(sp.Symbol("K")) else frozenset()
    )
    polynomial = _polynomial(expression, parameters=parameters)

    assert tuple(
        coefficient.canonical_text for coefficient in polynomial.coefficients
    ) == ("0",)
    assert polynomial.expression.canonical_text == "0"
    assert polynomial.degree_info.generic_degree is None
    assert polynomial.degree_info.guaranteed_degree is None
    assert polynomial.is_zero
    assert polynomial.is_constant
    assert polynomial.structural_term_count == 0
    assert polynomial.leading_coefficient.canonical_text == "0"
    assert polynomial.constant_coefficient.canonical_text == "0"
    assert polynomial.conditions == ()
    assert polynomial.used_parameter_names == frozenset()
    assert polynomial._as_sympy_poly().domain == sp.QQ


def test_dense_coefficients_and_summary_properties_are_exact() -> None:
    s = sp.Symbol("s")
    polynomial = _polynomial(s**3 + 2)

    assert tuple(
        coefficient.canonical_text for coefficient in polynomial.coefficients
    ) == ("1", "0", "0", "2")
    assert polynomial.leading_coefficient.canonical_text == "1"
    assert polynomial.constant_coefficient.canonical_text == "2"
    assert polynomial.structural_term_count == 2
    assert polynomial.degree_info.generic_degree == 3
    assert polynomial.degree_info.guaranteed_degree == 3
    assert not polynomial.is_zero
    assert not polynomial.is_constant
