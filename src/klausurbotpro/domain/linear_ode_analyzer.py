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
    normalized = format_ode_plain(
        output_name,
        output_terms,
        input_name,
        input_terms,
    )
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


def transform_ode_equation(
    ode: LinearOdeInput,
    output_ics: InitialConditionSet,
    input_ics: InitialConditionSet | None,
) -> tuple[tuple[TransformedOdeTerm, ...], OdeImageEquation]:
    """Apply the unilateral derivative theorem without solving for the output."""
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
            rule, latex_rule = _derivative_rule(
                ode.output_name if side == "output" else ode.input_name or "u",
                order,
                coefficient_expr,
                values,
            )
            transformed.append(
                TransformedOdeTerm(
                    side,
                    order,
                    coefficient,
                    exact(transformed_expr),
                    exact(coefficient_expr * initial),
                    rule,
                    latex_rule,
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
        _image_equation_plain(
            a_polynomial,
            output_initial,
            b_polynomial,
            input_initial,
        ),
    )
    return tuple(transformed), equation


def solve_ode_image_equation(
    equation: OdeImageEquation,
) -> tuple[ExactExpression, ExactExpression]:
    """Solve the already transformed equation into free and forced image parts."""
    u_image = sp.Symbol("U")
    a_polynomial = equation.a_polynomial._as_sympy()
    return (
        exact(equation.output_initial_part._as_sympy() / a_polynomial),
        exact(
            (
                equation.b_polynomial._as_sympy() * u_image
                - equation.input_initial_part._as_sympy()
            )
            / a_polynomial
        ),
    )


def transform_ode(
    ode: LinearOdeInput,
    output_ics: InitialConditionSet,
    input_ics: InitialConditionSet | None,
) -> tuple[tuple[TransformedOdeTerm, ...], OdeImageEquation, ExactExpression, ExactExpression]:
    """Compatibility wrapper for callers that require the complete image solution."""
    transformed, equation = transform_ode_equation(ode, output_ics, input_ics)
    free_laplace, forced_laplace = solve_ode_image_equation(equation)
    return transformed, equation, free_laplace, forced_laplace


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


def format_ode_plain(
    output_name: str,
    output_terms: tuple[tuple[int, ExactExpression], ...],
    input_name: str,
    input_terms: tuple[tuple[int, ExactExpression], ...],
) -> str:
    """Format a structured ODE without global string replacement."""
    return (
        f"{_side_plain(output_name, output_terms)} = "
        f"{_side_plain(input_name, input_terms)}"
    )


def format_ode_latex(ode: LinearOdeInput) -> str:
    """Return mathematical LaTeX for a normalized structured ODE."""
    return (
        f"{_side_latex(ode.output_name, ode.output_terms)}="
        f"{_side_latex(ode.input_name or 'u', ode.input_terms)}"
    )


def _side_plain(name: str, terms: tuple[tuple[int, ExactExpression], ...]) -> str:
    return _join_signed_terms(
        tuple(
            (
                coefficient._as_sympy(),
                _derivative_plain(name, order),
            )
            for order, coefficient in reversed(terms)
        ),
        latex=False,
    )


def _side_latex(name: str, terms: tuple[tuple[int, ExactExpression], ...]) -> str:
    return _join_signed_terms(
        tuple(
            (
                coefficient._as_sympy(),
                _derivative_latex(name, order),
            )
            for order, coefficient in reversed(terms)
        ),
        latex=True,
    )


def _join_signed_terms(
    terms: tuple[tuple[sp.Expr, str], ...],
    *,
    latex: bool,
) -> str:
    if not terms:
        return "0"
    pieces: list[str] = []
    for index, (coefficient, variable) in enumerate(terms):
        negative = coefficient.could_extract_minus_sign()
        magnitude = -coefficient if negative else coefficient
        if magnitude == 1:
            body = variable
        elif latex:
            body = rf"{sp.latex(magnitude)}\,{variable}"
        else:
            body = f"{_plain(magnitude)}*{variable}"
        if index == 0:
            pieces.append(f"-{body}" if negative else body)
        else:
            pieces.append((" - " if negative else " + ") + body)
    return "".join(pieces)


def _derivative_plain(name: str, order: int) -> str:
    if order == 0:
        return f"{name}(t)"
    if order <= 3:
        return f"{name}{chr(39) * order}(t)"
    return f"{name}^({order})(t)"


def _function_latex(name: str) -> str:
    return r"\varphi_G" if name == "phi_G" else sp.latex(sp.Symbol(name))


def _derivative_latex(name: str, order: int) -> str:
    function = _function_latex(name)
    if order == 0:
        return rf"{function}(t)"
    if order == 1:
        return rf"\dot{{{function}}}(t)"
    if order == 2:
        return rf"\ddot{{{function}}}(t)"
    return rf"{function}^{{({order})}}(t)"


def _derivative_rule(
    name: str,
    order: int,
    coefficient: sp.Expr,
    values: dict[int, sp.Expr],
) -> tuple[str, str]:
    image_name = "Y" if name in {"y", "phi_G"} else "U"
    source = _coefficient_term_plain(coefficient, _derivative_plain(name, order))
    source_latex = _coefficient_term_latex(
        coefficient,
        _derivative_latex(name, order),
    )
    if order == 0:
        actual = sp.expand(coefficient * sp.Symbol(image_name))
        return (
            f"L{{{source}}} = {_image_plain(actual)}",
            rf"\mathcal{{L}}\{{{source_latex}\}}={_image_latex(actual)}",
        )
    image_factor_plain = "s" if order == 1 else f"s^{order}"
    image_factor_latex = "s" if order == 1 else rf"s^{{{order}}}"
    inner_plain = f"{image_factor_plain}*{image_name}(s)" + "".join(
        _initial_plain_part(name, order, derivative_order)
        for derivative_order in range(order)
    )
    inner_latex = rf"{image_factor_latex}{image_name}(s)" + "".join(
        _initial_latex_part(name, order, derivative_order)
        for derivative_order in range(order)
    )
    actual = coefficient * (
        sp.Symbol("s") ** order * sp.Symbol(image_name)
        - sum(
            (
                sp.Symbol("s") ** (order - 1 - derivative_order)
                * values[derivative_order]
                for derivative_order in range(order)
            ),
            sp.Integer(0),
        )
    )
    if coefficient == 1:
        middle_plain = inner_plain
        middle_latex = inner_latex
    else:
        middle_plain = f"{_plain(coefficient)}*({inner_plain})"
        middle_latex = rf"{sp.latex(coefficient)}\left({inner_latex}\right)"
    return (
        f"L{{{source}}} = {middle_plain} = {_image_plain(sp.expand(actual))}",
        rf"\mathcal{{L}}\{{{source_latex}\}}={middle_latex}"
        rf"={_image_latex(sp.expand(actual))}",
    )


def _coefficient_term_plain(coefficient: sp.Expr, variable: str) -> str:
    return _join_signed_terms(((coefficient, variable),), latex=False)


def _coefficient_term_latex(coefficient: sp.Expr, variable: str) -> str:
    return _join_signed_terms(((coefficient, variable),), latex=True)


def _initial_plain_part(name: str, order: int, derivative_order: int) -> str:
    power = order - 1 - derivative_order
    power_text = "" if power == 0 else "s*" if power == 1 else f"s^{power}*"
    initial = (
        f"{name}(0+)"
        if derivative_order == 0
        else f"{name}{chr(39) * derivative_order}(0+)"
    )
    return f" - {power_text}{initial}"


def _initial_latex_part(name: str, order: int, derivative_order: int) -> str:
    power = order - 1 - derivative_order
    power_latex = "" if power == 0 else r"s\," if power == 1 else rf"s^{{{power}}}\,"
    return rf"-{power_latex}{_initial_latex(name, derivative_order)}"


def _initial_latex(name: str, order: int) -> str:
    function = _function_latex(name)
    if order == 0:
        return rf"{function}(0^+)"
    if order == 1:
        return rf"\dot{{{function}}}(0^+)"
    if order == 2:
        return rf"\ddot{{{function}}}(0^+)"
    return rf"{function}^{{({order})}}(0^+)"


def _image_plain(expression: sp.Expr) -> str:
    expanded = sp.expand(expression)
    for symbol_name in ("Y", "U"):
        symbol = sp.Symbol(symbol_name)
        coefficient = sp.expand(expanded.coeff(symbol))
        if coefficient == 0:
            continue
        remainder = sp.expand(expanded - coefficient * symbol)
        if coefficient == 1:
            main = f"{symbol_name}(s)"
        elif coefficient == -1:
            main = f"-{symbol_name}(s)"
        else:
            main = f"{_plain(coefficient)}*{symbol_name}(s)"
        if remainder == 0:
            return main
        return _append_plain_terms(main, remainder)
    return _plain(expanded)


def _image_latex(expression: sp.Expr) -> str:
    expanded = sp.expand(expression)
    for symbol_name in ("Y", "U"):
        symbol = sp.Symbol(symbol_name)
        coefficient = sp.expand(expanded.coeff(symbol))
        if coefficient == 0:
            continue
        remainder = sp.expand(expanded - coefficient * symbol)
        if coefficient == 1:
            main = f"{symbol_name}(s)"
        elif coefficient == -1:
            main = f"-{symbol_name}(s)"
        else:
            coefficient_latex = sp.latex(coefficient)
            if isinstance(coefficient, sp.Add):
                coefficient_latex = rf"\left({coefficient_latex}\right)"
            main = rf"{coefficient_latex}{symbol_name}(s)"
        if remainder == 0:
            return main
        return _append_latex_terms(main, remainder)
    return str(sp.latex(expanded))


def _append_plain_terms(main: str, remainder: sp.Expr) -> str:
    result = main
    for term in _ordered_image_terms(remainder):
        if term.could_extract_minus_sign():
            result += f" - {_plain(-term)}"
        else:
            result += f" + {_plain(term)}"
    return result


def _append_latex_terms(main: str, remainder: sp.Expr) -> str:
    result = main
    for term in _ordered_image_terms(remainder):
        if term.could_extract_minus_sign():
            result += rf"-{sp.latex(-term)}"
        else:
            result += rf"+{sp.latex(term)}"
    return result


def _ordered_image_terms(expression: sp.Expr) -> tuple[sp.Expr, ...]:
    s = sp.Symbol("s")
    return tuple(
        sorted(
            sp.Add.make_args(sp.expand(expression)),
            key=lambda term: int(sp.Poly(term, s).degree()),
            reverse=True,
        )
    )


def _image_equation_plain(
    a_polynomial: sp.Expr,
    output_initial: sp.Expr,
    b_polynomial: sp.Expr,
    input_initial: sp.Expr,
) -> str:
    left = _grouped_image_plain(a_polynomial, "Y", output_initial)
    right = _grouped_image_plain(b_polynomial, "U", input_initial)
    return f"{left} = {right}"


def _grouped_image_plain(
    polynomial: sp.Expr,
    image_name: str,
    initial_part: sp.Expr,
) -> str:
    expanded = sp.expand(polynomial)
    if expanded == 1:
        main = f"{image_name}(s)"
    elif expanded == -1:
        main = f"-{image_name}(s)"
    else:
        main = f"({_plain_expanded(expanded)})*{image_name}(s)"
    if initial_part == 0:
        return main
    if initial_part.could_extract_minus_sign():
        return f"{main} + {_plain(-initial_part)}"
    return f"{main} - {_plain(initial_part)}"


def _plain(expression: sp.Expr) -> str:
    return str(sp.sstr(sp.factor(expression))).replace("**", "^")


def _plain_expanded(expression: sp.Expr) -> str:
    return str(sp.sstr(sp.expand(expression))).replace("**", "^")


def _error(code: DiagnosticCode, message: str) -> Diagnostic:
    return Diagnostic(DiagnosticSeverity.ERROR, code, message)


__all__ = [
    "build_initial_conditions",
    "build_linear_ode",
    "format_ode_latex",
    "format_ode_plain",
    "solve_ode_image_equation",
    "transform_ode",
    "transform_ode_equation",
    "verify_ode_solution",
]
