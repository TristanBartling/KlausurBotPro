"""Exact structured constant-coefficient ODE transformation and verification."""

from __future__ import annotations

import sympy as sp

from klausurbotpro.domain.diagnostics import Diagnostic, DiagnosticCode, DiagnosticSeverity
from klausurbotpro.domain.expression import ExactExpression
from klausurbotpro.domain.time_domain_analyzer import exact
from klausurbotpro.domain.time_domain_contracts import (
    InitialConditionOrigin,
    InitialConditionSet,
    InitialConditionValue,
    LinearOdeInput,
    OdeImageEquation,
    OdeVerificationReport,
    TransformedOdeTerm,
)


def build_linear_ode(
    *,
    output_name: str,
    input_name: str,
    output_coefficients: tuple[ExactExpression, ...],
    input_coefficients: tuple[ExactExpression, ...],
    output_order: int,
    input_order: int,
    assumptions: tuple[str, ...],
) -> LinearOdeInput:
    """Validate and normalize a structured SISO ODE of order one through four."""
    diagnostics: list[Diagnostic] = []
    if output_order not in range(1, 5) or len(output_coefficients) != output_order + 1:
        diagnostics.append(
            _error(
                DiagnosticCode.ODE_ORDER_UNSUPPORTED,
                "Unterstützt werden Ausgangsordnungen 1 bis 4.",
            )
        )
    if input_order not in range(0, 5) or len(input_coefficients) != input_order + 1:
        diagnostics.append(
            _error(
                DiagnosticCode.ODE_ORDER_UNSUPPORTED,
                "Unterstützt werden Eingangsordnungen 0 bis 4.",
            )
        )
    leading = output_coefficients[-1] if output_coefficients else exact(sp.Integer(0))
    leading_expr = leading._as_sympy()
    if leading_expr == 0:
        diagnostics.append(
            _error(
                DiagnosticCode.ODE_LEADING_COEFFICIENT_INVALID,
                "Der Leitkoeffizient darf nicht null sein.",
            )
        )
    elif leading_expr.free_symbols and not _is_proven_nonzero(leading_expr, assumptions):
        names = ", ".join(sorted(str(item) for item in leading_expr.free_symbols))
        diagnostics.append(
            _error(
                DiagnosticCode.PARAMETER_ASSUMPTIONS_INSUFFICIENT,
                f"Für den Leitkoeffizienten fehlt eine Nichtnullannahme: {names} != 0.",
            )
        )
    output_terms = tuple(
        (index, value) for index, value in enumerate(output_coefficients) if value._as_sympy() != 0
    )
    input_terms = tuple(
        (index, value) for index, value in enumerate(input_coefficients) if value._as_sympy() != 0
    )
    if not output_terms:
        diagnostics.append(
            _error(
                DiagnosticCode.ODE_LEADING_COEFFICIENT_INVALID,
                "Mindestens ein Ausgangsterm ist erforderlich.",
            )
        )
    normalized = f"{_side_text(output_name, output_terms)} = {_side_text(input_name, input_terms)}"
    return LinearOdeInput(
        output_name,
        input_name,
        output_terms,
        input_terms,
        output_order,
        input_order,
        assumptions,
        normalized,
        normalized,
        leading,
        not diagnostics,
        tuple(diagnostics),
    )


def build_initial_conditions(
    variable: str,
    required_count: int,
    supplied: tuple[ExactExpression | None, ...],
    *,
    explicit_zero_policy: bool,
    derived: bool = False,
) -> InitialConditionSet:
    values: list[InitialConditionValue] = []
    missing: list[int] = []
    for order in range(required_count):
        value = supplied[order] if order < len(supplied) else None
        if value is None and explicit_zero_policy:
            value = exact(sp.Integer(0))
            origin = InitialConditionOrigin.EXPLICIT_ZERO_POLICY
        elif value is None:
            missing.append(order)
            continue
        else:
            origin = (
                InitialConditionOrigin.DERIVED if derived else InitialConditionOrigin.USER_PROVIDED
            )
        values.append(InitialConditionValue(order, value, origin))
    return InitialConditionSet(
        variable, tuple(range(required_count)), tuple(values), not missing, tuple(missing)
    )


def transform_ode(
    ode: LinearOdeInput,
    output_ics: InitialConditionSet,
    input_ics: InitialConditionSet | None,
) -> tuple[tuple[TransformedOdeTerm, ...], OdeImageEquation, ExactExpression, ExactExpression]:
    """Apply the unilateral derivative theorem term by term."""
    s, y_image, u_image = sp.symbols("s Y U")
    output_values = {item.derivative_order: item.value._as_sympy() for item in output_ics.values}
    input_values = (
        {}
        if input_ics is None
        else {item.derivative_order: item.value._as_sympy() for item in input_ics.values}
    )
    a_polynomial = sum(
        (coefficient._as_sympy() * s**order for order, coefficient in ode.output_terms),
        sp.Integer(0),
    )
    b_polynomial = sum(
        (coefficient._as_sympy() * s**order for order, coefficient in ode.input_terms),
        sp.Integer(0),
    )
    output_initial = sp.Integer(0)
    input_initial = sp.Integer(0)
    transformed: list[TransformedOdeTerm] = []
    for side, terms, image, values in (
        ("output", ode.output_terms, y_image, output_values),
        ("input", ode.input_terms, u_image, input_values),
    ):
        for order, coefficient in terms:
            initial = sum((s ** (order - 1 - r) * values[r] for r in range(order)), sp.Integer(0))
            coefficient_expr = coefficient._as_sympy()
            transformed_expr = coefficient_expr * (s**order * image - initial)
            if side == "output":
                output_initial += coefficient_expr * initial
            else:
                input_initial += coefficient_expr * initial
            rule = _derivative_rule(
                ode.output_name if side == "output" else ode.input_name or "u", order, values
            )
            transformed.append(
                TransformedOdeTerm(
                    side,
                    order,
                    coefficient,
                    exact(transformed_expr),
                    exact(coefficient_expr * initial),
                    rule,
                )
            )
    left = a_polynomial * y_image - output_initial
    right = b_polynomial * u_image - input_initial
    equation = OdeImageEquation(
        exact(a_polynomial),
        exact(b_polynomial),
        exact(output_initial),
        exact(input_initial),
        exact(left),
        exact(right),
        f"({_plain(a_polynomial)})*Y(s) - ({_plain(output_initial)}) = "
        f"({_plain(b_polynomial)})*U(s) - ({_plain(input_initial)})",
    )
    return (
        tuple(transformed),
        equation,
        exact(output_initial / a_polynomial),
        exact((b_polynomial * u_image - input_initial) / a_polynomial),
    )


def verify_ode_solution(
    ode: LinearOdeInput,
    output_ics: InitialConditionSet,
    input_time: ExactExpression,
    total_time: ExactExpression,
    total_laplace: ExactExpression,
    free_laplace: ExactExpression,
    forced_laplace: ExactExpression,
    image_equation: OdeImageEquation,
) -> OdeVerificationReport:
    t, s = sp.symbols("t s")
    y = total_time._as_sympy()
    u = input_time._as_sympy()
    y_image = total_laplace._as_sympy()
    image_residual = sp.simplify(
        image_equation.a_polynomial._as_sympy() * y_image
        - image_equation.output_initial_part._as_sympy()
        - image_equation.b_polynomial._as_sympy() * sp.laplace_transform(u, t, s, noconds=True)
        + image_equation.input_initial_part._as_sympy()
    )
    decomposition = sp.simplify(free_laplace._as_sympy() + forced_laplace._as_sympy() - y_image)
    forward = sp.simplify(sp.laplace_transform(y, t, s, noconds=True) - y_image)
    expected = {item.derivative_order: item.value._as_sympy() for item in output_ics.values}
    ic_residuals = tuple(
        (order, exact(sp.simplify(sp.limit(sp.diff(y, t, order), t, 0, dir="+") - value)))
        for order, value in sorted(expected.items())
    )
    residual = sum(
        (coefficient._as_sympy() * sp.diff(y, t, order) for order, coefficient in ode.output_terms),
        sp.Integer(0),
    ) - sum(
        (coefficient._as_sympy() * sp.diff(u, t, order) for order, coefficient in ode.input_terms),
        sp.Integer(0),
    )
    residual = sp.simplify(sp.expand_trig(residual))
    trusted = all(
        sp.simplify(item) == 0 for item in (image_residual, decomposition, forward, residual)
    ) and all(item[1]._as_sympy() == 0 for item in ic_residuals)
    return OdeVerificationReport(
        exact(image_residual),
        exact(decomposition),
        exact(forward),
        ic_residuals,
        exact(residual),
        trusted,
    )


def _is_proven_nonzero(expression: sp.Expr, assumptions: tuple[str, ...]) -> bool:
    if expression.is_nonzero:
        return True
    joined = ";".join(item.replace(" ", "") for item in assumptions)
    return all(
        f"{symbol}!=0" in joined or f"{symbol}>0" in joined or f"{symbol}<0" in joined
        for symbol in expression.free_symbols
    )


def _side_text(name: str, terms: tuple[tuple[int, ExactExpression], ...]) -> str:
    if not terms:
        return "0"
    pieces = []
    for order, coefficient in reversed(terms):
        derivative = (
            f"{name}(t)"
            if order == 0
            else f"{name}{chr(39) * order}(t)"
            if order <= 3
            else f"{name}^(4)(t)"
        )
        pieces.append(f"{coefficient.canonical_text}*{derivative}")
    return " + ".join(pieces).replace("1*", "")


def _derivative_rule(name: str, order: int, values: dict[int, sp.Expr]) -> str:
    if order == 0:
        return f"L{{{name}(t)}} = {name.upper()}(s)"
    initial = " - ".join(
        _plain(sp.Symbol("s") ** (order - 1 - r) * values[r]) for r in range(order)
    )
    return f"L{{{name}^({order})(t)}} = s^{order} {name.upper()}(s) - {initial}"


def _plain(expression: sp.Expr) -> str:
    return str(sp.sstr(sp.factor(expression))).replace("**", "^")


def _error(code: DiagnosticCode, message: str) -> Diagnostic:
    return Diagnostic(DiagnosticSeverity.ERROR, code, message)


__all__ = ["build_initial_conditions", "build_linear_ode", "transform_ode", "verify_ode_solution"]
