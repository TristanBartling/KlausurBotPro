"""Focused tests for the small method-neutral parameter core."""

import sympy as sp

from klausurbotpro.domain.expression import ExactExpression
from klausurbotpro.domain.parameter_core import (
    canonicalize_characteristic_polynomial,
    solve_parameter_conditions,
)
from klausurbotpro.domain.parameter_core_contracts import (
    AnalysisTarget,
    AtomicParameterCondition,
    CharacteristicPolynomialInput,
    ConditionOrigin,
    ParameterConditionProblem,
    PolynomialRole,
    Relation,
    SolveStatus,
    SourceProvenance,
)


def _condition(expression: sp.Expr, relation: Relation) -> AtomicParameterCondition:
    return AtomicParameterCondition(
        ExactExpression._from_sympy(expression),
        relation,
        ConditionOrigin.USER_ASSUMPTION,
        tuple(item.name for item in expression.free_symbols),
    )


def test_zero_dimensional_condition_result() -> None:
    result = solve_parameter_conditions(
        ParameterConditionProblem((), (_condition(sp.Integer(2), Relation.GT),))
    )
    assert result.status is SolveStatus.SOLVED_EXACT
    assert result.exact_text == "wahr"


def test_one_dimensional_interval_and_empty_result() -> None:
    parameter = sp.Symbol("K")
    interval = solve_parameter_conditions(
        ParameterConditionProblem(
            ("K",),
            (_condition(parameter, Relation.GT), _condition(20 - parameter, Relation.GT)),
        )
    )
    empty = solve_parameter_conditions(
        ParameterConditionProblem(
            ("K",),
            (_condition(parameter, Relation.GT), _condition(parameter + 40, Relation.LT)),
        )
    )
    assert interval.status is SolveStatus.SOLVED_EXACT
    assert interval.control_points == (("10",),)
    assert empty.status is SolveStatus.EMPTY


def test_parameter_dependent_leading_coefficient_keeps_degree_drop() -> None:
    s, q = sp.symbols("s q")
    value = CharacteristicPolynomialInput(
        ExactExpression._from_sympy(q * s**3 + s**2 + 2 * s + 1),
        "s",
        ("q",),
        (),
        (_condition(q, Relation.GE),),
        (),
        PolynomialRole.DIRECT_CHARACTERISTIC_POLYNOMIAL,
        AnalysisTarget.INTERNAL_CLOSED_LOOP_ASYMPTOTIC,
        SourceProvenance("test"),
    )
    result = canonicalize_characteristic_polynomial(value)
    assert tuple(item.degree for item in result.degree_cases) == (3, 2)
    assert result.degree_cases[1].guard[0].relation is Relation.EQ


def test_limited_two_dimensional_graph_band() -> None:
    a, gain = sp.symbols("a K")
    result = solve_parameter_conditions(
        ParameterConditionProblem(
            ("a", "K"),
            (
                _condition(a + sp.Rational(20, 9), Relation.GT),
                _condition(gain + sp.Rational(20, 9) * a, Relation.GT),
                _condition(a**2 + 9 * a + 20 - gain, Relation.GT),
            ),
        )
    )
    assert result.status is SolveStatus.SOLVED_EXACT
    assert sp.simplify(sp.sympify(result.lower_bound) + sp.Rational(20, 9) * a) == 0
    assert sp.simplify(sp.sympify(result.upper_bound) - (a**2 + 9 * a + 20)) == 0
    assert result.lower_open and result.upper_open
