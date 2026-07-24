"""Focused exact tests for the structured unilateral-Laplace ODE core."""

import sympy as sp

from klausurbotpro.domain.expression import ExactExpression
from klausurbotpro.domain.linear_ode_analyzer import (
    build_initial_conditions,
    build_linear_ode,
    solve_ode_image_equation,
    transform_ode,
    transform_ode_equation,
)
from klausurbotpro.domain.time_domain_analyzer import exact


def _coefficient(value: sp.Expr | int) -> ExactExpression:
    return exact(sp.sympify(value))


def test_normalization_preserves_order_and_signed_input() -> None:
    ode = build_linear_ode(
        output_name="phi_G",
        input_name="F_A",
        output_coefficients=(
            _coefficient(sp.Symbol("g") * (sp.Symbol("m_K") + sp.Symbol("m_G"))),
            _coefficient(-sp.Symbol("d_K")),
            _coefficient(sp.Symbol("m_K") * sp.Symbol("l")),
        ),
        input_coefficients=(_coefficient(-1),),
        output_order=2,
        input_order=0,
        assumptions=("m_K > 0", "l > 0"),
    )
    assert ode.valid
    assert "-F_A(t)" in ode.normalized_ode
    assert ode.output_terms[-1][0] == 2


def test_initial_condition_completeness_never_implies_zero() -> None:
    conditions = build_initial_conditions(
        "y", 2, (_coefficient(0), None), explicit_zero_policy=False
    )
    assert not conditions.complete
    assert conditions.missing_orders == (1,)
    explicit = build_initial_conditions("y", 2, (_coefficient(0), None), explicit_zero_policy=True)
    assert explicit.complete
    assert explicit.values[1].origin.value == "EXPLICIT_ZERO_POLICY"


def test_derivative_theorem_is_visible_for_orders_one_through_four() -> None:
    ode = build_linear_ode(
        output_name="y",
        input_name="u",
        output_coefficients=tuple(_coefficient(1) for _ in range(5)),
        input_coefficients=(_coefficient(1),),
        output_order=4,
        input_order=0,
        assumptions=(),
    )
    conditions = build_initial_conditions(
        "y", 4, tuple(_coefficient(index + 1) for index in range(4)), explicit_zero_policy=False
    )
    transformed, equation, _, _ = transform_ode(ode, conditions, None)
    rules = {
        item.derivative_order: item.display_rule for item in transformed if item.side == "output"
    }
    assert rules[2].endswith("s^2*Y(s) - s - 2")
    assert rules[4].endswith("s^4*Y(s) - s^3 - 2*s^2 - 3*s - 4")
    assert sp.expand(equation.a_polynomial._as_sympy()) == sum(
        sp.Symbol("s") ** k for k in range(5)
    )


def test_image_equation_and_solving_are_separate_exact_stages() -> None:
    ode = build_linear_ode(
        output_name="y",
        input_name="u",
        output_coefficients=(
            _coefficient(0),
            _coefficient(4),
            _coefficient(2),
        ),
        input_coefficients=(_coefficient(1),),
        output_order=2,
        input_order=0,
        assumptions=(),
    )
    y0, v0 = sp.symbols("y0 v0")
    conditions = build_initial_conditions(
        "y",
        2,
        (_coefficient(y0), _coefficient(v0)),
        explicit_zero_policy=False,
    )
    transformed, equation = transform_ode_equation(ode, conditions, None)
    assert len(transformed) == 3
    free, forced = solve_ode_image_equation(equation)
    s, u = sp.symbols("s U")
    expected = (u + 2 * s * y0 + 2 * v0 + 4 * y0) / (
        2 * s**2 + 4 * s
    )
    assert sp.simplify(free._as_sympy() + forced._as_sympy() - expected) == 0


def test_symbolic_leading_coefficient_requires_nonzero_assumption() -> None:
    coefficient = _coefficient(sp.Symbol("M"))
    rejected = build_linear_ode(
        output_name="y",
        input_name="u",
        output_coefficients=(_coefficient(1), coefficient),
        input_coefficients=(_coefficient(1),),
        output_order=1,
        input_order=0,
        assumptions=(),
    )
    accepted = build_linear_ode(
        output_name="y",
        input_name="u",
        output_coefficients=(_coefficient(1), coefficient),
        input_coefficients=(_coefficient(1),),
        output_order=1,
        input_order=0,
        assumptions=("M > 0",),
    )
    assert not rejected.valid
    assert accepted.valid


def test_safe_coefficient_formatting_preserves_one_minus_one_and_eleven() -> None:
    ode = build_linear_ode(
        output_name="y",
        input_name="u",
        output_coefficients=(_coefficient(11), _coefficient(1)),
        input_coefficients=(_coefficient(-1),),
        output_order=1,
        input_order=0,
        assumptions=(),
    )
    assert ode.normalized_ode == "y'(t) + 11*y(t) = -u(t)"
    assert "1y(t)" not in ode.normalized_ode

    signed = build_linear_ode(
        output_name="y",
        input_name="u",
        output_coefficients=(_coefficient(11), _coefficient(-2)),
        input_coefficients=(_coefficient(sp.Rational(1, 2)),),
        output_order=1,
        input_order=0,
        assumptions=(),
    )
    assert "+ -" not in signed.normalized_ode
    assert signed.normalized_ode == "-2*y'(t) + 11*y(t) = 1/2*u(t)"
