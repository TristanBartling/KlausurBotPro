"""Small method-neutral polynomial and parameter core."""

from __future__ import annotations

from typing import cast

import sympy as sp

from klausurbotpro.domain.expression import ExactExpression
from klausurbotpro.domain.parameter_core_contracts import (
    AnalysisTarget,
    AtomicParameterCondition,
    CanonicalCharacteristicPolynomial,
    CharacteristicPolynomialInput,
    ConditionOrigin,
    DegreeCaseKind,
    ParameterConditionProblem,
    ParameterRegion,
    PolynomialDegreeCase,
    PolynomialRole,
    Relation,
    SolveStatus,
    TransformationRecord,
)


def _exact(value: sp.Expr) -> ExactExpression:
    return ExactExpression._from_sympy(sp.sympify(value))


def _relation(condition: AtomicParameterCondition) -> sp.Rel:
    value = condition.expression._as_sympy()
    constructors = {
        Relation.EQ: sp.Eq,
        Relation.NE: sp.Ne,
        Relation.LT: sp.Lt,
        Relation.LE: sp.Le,
        Relation.GT: sp.Gt,
        Relation.GE: sp.Ge,
    }
    return constructors[condition.relation](value, 0)


def _compatible(value: CharacteristicPolynomialInput) -> bool:
    allowed = {
        PolynomialRole.DIRECT_CHARACTERISTIC_POLYNOMIAL: {
            AnalysisTarget.INTERNAL_CLOSED_LOOP_ASYMPTOTIC,
            AnalysisTarget.EXTERNAL_BIBO,
            AnalysisTarget.STATE_ASYMPTOTIC,
        },
        PolynomialRole.RAW_CLOSED_LOOP_CHARACTERISTIC: {
            AnalysisTarget.INTERNAL_CLOSED_LOOP_ASYMPTOTIC,
        },
        PolynomialRole.REDUCED_TRANSFER_DENOMINATOR: {AnalysisTarget.EXTERNAL_BIBO},
        PolynomialRole.STATE_CHARACTERISTIC_POLYNOMIAL: {AnalysisTarget.STATE_ASYMPTOTIC},
    }
    if value.analysis_target not in allowed[value.role]:
        return False
    return not (
        value.role is PolynomialRole.REDUCED_TRANSFER_DENOMINATOR
        and value.cancellation_report is None
    )


def canonicalize_characteristic_polynomial(
    value: CharacteristicPolynomialInput,
) -> CanonicalCharacteristicPolynomial:
    """Expand an exact polynomial and make every leading-coefficient case visible."""
    if len(value.decision_parameters) > 2 or not _compatible(value):
        return CanonicalCharacteristicPolynomial(
            value,
            value.polynomial,
            (),
            -1,
            (),
            SolveStatus.INVALID_INPUT,
            ("Unzulässige Parameterzahl oder Rollen-/Zielkombination.",),
        )
    variable = sp.Symbol(value.variable)
    expression = sp.expand(value.polynomial._as_sympy())
    declared = set(value.decision_parameters) | set(value.fixed_symbols) | {value.variable}
    if {item.name for item in expression.free_symbols} - declared:
        return CanonicalCharacteristicPolynomial(
            value,
            _exact(expression),
            (),
            -1,
            (),
            SolveStatus.INVALID_INPUT,
            ("Das Polynom enthält nicht deklarierte Symbole.",),
        )
    try:
        polynomial = sp.Poly(expression, variable)
    except sp.PolynomialError:
        return CanonicalCharacteristicPolynomial(
            value,
            _exact(expression),
            (),
            -1,
            (),
            SolveStatus.INVALID_INPUT,
            (f"Der Ausdruck ist bezüglich {value.variable} nicht polynomial.",),
        )
    if polynomial.is_zero:
        case = PolynomialDegreeCase(
            "degree-zero-polynomial",
            (),
            _exact(sp.Integer(0)),
            (),
            0,
            DegreeCaseKind.ZERO_POLYNOMIAL,
        )
        return CanonicalCharacteristicPolynomial(
            value,
            _exact(expression),
            (),
            0,
            (case,),
            SolveStatus.INVALID_INPUT,
            ("Nullpolynom: keine gültige charakteristische Gleichung.",),
        )
    coefficients = tuple(_exact(item) for item in polynomial.all_coeffs())
    cases = _degree_cases(polynomial, value.decision_parameters, value.assumptions)
    return CanonicalCharacteristicPolynomial(
        value,
        _exact(expression),
        coefficients,
        int(polynomial.degree()),
        cases,
        SolveStatus.SOLVED_EXACT,
    )


def _degree_cases(
    polynomial: sp.Poly,
    parameters: tuple[str, ...],
    assumptions: tuple[AtomicParameterCondition, ...],
) -> tuple[PolynomialDegreeCase, ...]:
    coeffs = tuple(polynomial.all_coeffs())
    variable = polynomial.gens[0]
    parameter_symbols = {sp.Symbol(name) for name in parameters}
    leading = coeffs[0]
    known_positive = _known_positive_symbols(assumptions)
    if not (leading.free_symbols & parameter_symbols) or _known_positive_product(
        leading, known_positive
    ):
        factor = -1 if leading.is_negative else 1
        normalized = sp.expand(factor * polynomial.as_expr())
        return (_make_case("degree-regular", (), normalized, variable, DegreeCaseKind.REGULAR),)
    results: list[PolynomialDegreeCase] = []
    for suffix, relation, factor in (("positive", Relation.GT, 1), ("negative", Relation.LT, -1)):
        guard = AtomicParameterCondition(
            _exact(leading),
            relation,
            ConditionOrigin.DEGREE_CASE_GUARD,
            parameters,
            f"Leitkoeffizient {suffix}",
        )
        normalized = sp.expand(factor * polynomial.as_expr())
        transformations = (
            ()
            if factor == 1
            else (
                TransformationRecord(
                    "MULTIPLY_BY_MINUS_ONE",
                    _exact(polynomial.as_expr()),
                    _exact(normalized),
                    f"{leading} < 0",
                ),
            )
        )
        made = _make_case(
            f"degree-{polynomial.degree()}-{suffix}",
            (guard,),
            normalized,
            variable,
            DegreeCaseKind.REGULAR,
            transformations,
        )
        results.append(made)
    zero_guard = AtomicParameterCondition(
        _exact(leading),
        Relation.EQ,
        ConditionOrigin.DEGREE_CASE_GUARD,
        parameters,
        "Gradabfall",
    )
    reduced_expr = sp.expand(polynomial.as_expr() - leading * variable ** polynomial.degree())
    if reduced_expr == 0:
        results.append(
            PolynomialDegreeCase(
                "degree-drop-zero",
                (zero_guard,),
                _exact(reduced_expr),
                (),
                0,
                DegreeCaseKind.ZERO_POLYNOMIAL,
            )
        )
    else:
        reduced = sp.Poly(reduced_expr, variable)
        reduction = TransformationRecord(
            "DEGREE_REDUCTION",
            _exact(polynomial.as_expr()),
            _exact(reduced_expr),
            f"{leading} = 0",
        )
        if reduced.degree() > 0 and (
            reduced.LC().free_symbols & parameter_symbols
        ):
            for nested in _degree_cases(reduced, parameters, assumptions):
                results.append(
                    PolynomialDegreeCase(
                        f"degree-drop-{nested.case_id}",
                        (zero_guard, *nested.guard),
                        nested.polynomial,
                        nested.coefficients,
                        nested.degree,
                        DegreeCaseKind.DEGREE_REDUCED,
                        (reduction, *nested.transformations),
                    )
                )
        else:
            kind = (
                DegreeCaseKind.CONSTANT_NONZERO
                if reduced.degree() == 0
                else DegreeCaseKind.DEGREE_REDUCED
            )
            made = _make_case(
                f"degree-drop-{reduced.degree()}",
                (zero_guard,),
                reduced_expr,
                variable,
                kind,
                (reduction,),
            )
            results.append(made)
    return tuple(item for item in results if _case_possible(item, assumptions, parameters))


def _known_positive_symbols(
    assumptions: tuple[AtomicParameterCondition, ...],
) -> frozenset[sp.Symbol]:
    return frozenset(
        item.expression._as_sympy()
        for item in assumptions
        if item.relation is Relation.GT and isinstance(item.expression._as_sympy(), sp.Symbol)
    )


def _known_positive_product(expression: sp.Expr, positive: frozenset[sp.Symbol]) -> bool:
    coefficient, factors = sp.factor_list(expression)
    if coefficient <= 0:
        return False
    return all(
        factor in positive
        or (factor.is_Pow and factor.base in positive and factor.exp.is_integer and factor.exp > 0)
        for factor, _ in factors
    )


def _case_possible(
    case: PolynomialDegreeCase,
    assumptions: tuple[AtomicParameterCondition, ...],
    parameters: tuple[str, ...],
) -> bool:
    if len(parameters) != 1:
        return True
    symbol = sp.Symbol(parameters[0])
    relations = tuple(_relation(item) for item in assumptions + case.guard)
    try:
        return sp.reduce_inequalities(relations, symbol) is not sp.false
    except (NotImplementedError, TypeError, ValueError):
        return True


def _make_case(
    case_id: str,
    guard: tuple[AtomicParameterCondition, ...],
    expression: sp.Expr,
    variable: sp.Symbol,
    kind: DegreeCaseKind,
    transformations: tuple[TransformationRecord, ...] = (),
) -> PolynomialDegreeCase:
    polynomial = sp.Poly(expression, variable)
    return PolynomialDegreeCase(
        case_id,
        guard,
        _exact(expression),
        tuple(_exact(item) for item in polynomial.all_coeffs()),
        int(polynomial.degree()),
        kind,
        transformations,
    )


def solve_parameter_conditions(problem: ParameterConditionProblem) -> ParameterRegion:
    """Solve zero-, one-, or the supported graph-band two-parameter problem."""
    if len(problem.parameters) > 2:
        return ParameterRegion(
            SolveStatus.UNSUPPORTED, "nicht unterstützt", "\\text{nicht unterstützt}"
        )
    raw_relations = tuple(
        _relation(item) for item in (problem.assumptions + problem.exclusions + problem.conditions)
    )
    if any(item is sp.false for item in raw_relations):
        return ParameterRegion(SolveStatus.EMPTY, "∅", "\\varnothing")
    relations = tuple(item for item in raw_relations if item is not sp.true)
    if not problem.parameters:
        simplified = tuple(sp.simplify(item) for item in relations)
        if any(item is sp.false for item in simplified):
            return ParameterRegion(SolveStatus.EMPTY, "falsch", "\\varnothing")
        if all(item is sp.true for item in simplified):
            return ParameterRegion(SolveStatus.SOLVED_EXACT, "wahr", "\\mathrm{wahr}")
        return ParameterRegion(
            SolveStatus.INDETERMINATE,
            "unter Annahmen nicht entscheidbar",
            "\\text{unter Annahmen nicht entscheidbar}",
            residual_conditions=tuple(str(item) for item in simplified),
        )
    if len(problem.parameters) == 1:
        symbol = sp.Symbol(problem.parameters[0])
        try:
            solution = sp.reduce_inequalities(relations, symbol)
        except (NotImplementedError, TypeError, ValueError):
            return ParameterRegion(
                SolveStatus.UNSUPPORTED,
                "nicht unterstützt",
                "\\text{nicht unterstützt}",
                residual_conditions=tuple(str(item) for item in relations),
            )
        if solution is sp.false:
            return ParameterRegion(SolveStatus.EMPTY, "∅", "\\varnothing")
        exact_text = str(solution)
        return ParameterRegion(
            SolveStatus.SOLVED_EXACT,
            exact_text,
            sp.latex(solution),
            intervals=(exact_text,),
            control_points=_one_dimensional_control_point(solution, symbol),
        )
    return _solve_graph_band(cast(tuple[str, str], problem.parameters), relations)


def _one_dimensional_control_point(
    solution: sp.Boolean,
    symbol: sp.Symbol,
) -> tuple[tuple[str, ...], ...]:
    solution_set = solution.as_set()
    if isinstance(solution_set, sp.Interval):
        if solution_set.start is sp.S.NegativeInfinity:
            point = solution_set.end - 1
        elif solution_set.end is sp.S.Infinity:
            point = solution_set.start + 1
        else:
            point = (solution_set.start + solution_set.end) / 2
        return ((str(sp.simplify(point)),),)
    if isinstance(solution_set, sp.FiniteSet) and len(solution_set) == 1:
        return ((str(next(iter(solution_set))),),)
    return ()


def _solve_graph_band(
    parameters: tuple[str, str],
    relations: tuple[sp.Rel, ...],
) -> ParameterRegion:
    x, y = (sp.Symbol(name) for name in parameters)
    x_relations: list[sp.Rel] = []
    lower: list[tuple[sp.Expr, bool]] = []
    upper: list[tuple[sp.Expr, bool]] = []
    residual: list[str] = []
    for relation in relations:
        expression = sp.expand(relation.lhs - relation.rhs)
        if y not in expression.free_symbols:
            x_relations.append(relation)
            continue
        polynomial = sp.Poly(expression, y)
        if polynomial.degree() != 1:
            residual.append(str(relation))
            continue
        coefficient, constant = polynomial.all_coeffs()
        boundary = sp.factor(-constant / coefficient)
        positive = coefficient.is_positive or coefficient.is_number and coefficient > 0
        negative = coefficient.is_negative or coefficient.is_number and coefficient < 0
        if not (positive or negative):
            residual.append(str(relation))
            continue
        strict = relation.rel_op in ("<", ">")
        greater = relation.rel_op in (">", ">=")
        is_lower = greater if positive else not greater
        (lower if is_lower else upper).append((boundary, strict))
    try:
        x_solution = sp.reduce_inequalities(x_relations, x) if x_relations else sp.true
    except (NotImplementedError, TypeError, ValueError):
        residual.extend(str(item) for item in x_relations)
        x_solution = sp.true
    if residual or (not lower and not upper):
        return ParameterRegion(
            SolveStatus.PARTIALLY_SOLVED_SAFE,
            "teilweise gelöst",
            "\\text{teilweise gelöst}",
            x_domain=str(x_solution),
            residual_conditions=tuple(residual or [str(item) for item in relations]),
            diagnostics=("2D-Bedingung liegt nicht vollständig in sicherer Graphbandform vor.",),
        )
    # The documented MVP references reduce to one dominant lower and upper graph.
    lower_bound = lower[-1][0] if lower else sp.S.NegativeInfinity
    upper_bound = upper[-1][0] if upper else sp.S.Infinity
    for candidate, _ in lower[:-1]:
        if _dominates(candidate, lower_bound, x_solution, x, greater=True):
            lower_bound = candidate
    for candidate, _ in upper[:-1]:
        if _dominates(candidate, upper_bound, x_solution, x, greater=False):
            upper_bound = candidate
    gap_solution = (
        sp.true
        if lower_bound is sp.S.NegativeInfinity or upper_bound is sp.S.Infinity
        else sp.reduce_inequalities((lower_bound < upper_bound,), x)
    )
    nonempty_set = x_solution.as_set().intersect(gap_solution.as_set())
    if nonempty_set is sp.S.EmptySet:
        return ParameterRegion(SolveStatus.EMPTY, "∅", "\\varnothing")
    nonempty = nonempty_set.as_relational(x)
    x_text = str(nonempty)
    bounds = []
    if lower_bound is not sp.S.NegativeInfinity:
        bounds.append(y > lower_bound)
    if upper_bound is not sp.S.Infinity:
        bounds.append(y < upper_bound)
    formula = sp.And(nonempty, *bounds)
    point_x = _pick_x(nonempty, x)
    points: tuple[tuple[str, ...], ...] = ()
    if point_x is not None:
        if lower_bound is sp.S.NegativeInfinity:
            point_y = sp.simplify(upper_bound.subs(x, point_x) - 1)
        elif upper_bound is sp.S.Infinity:
            point_y = sp.simplify(lower_bound.subs(x, point_x) + 1)
        else:
            point_y = sp.simplify((lower_bound.subs(x, point_x) + upper_bound.subs(x, point_x)) / 2)
        points = ((str(point_x), str(point_y)),)
    return ParameterRegion(
        SolveStatus.SOLVED_EXACT,
        str(formula),
        sp.latex(formula),
        x_domain=x_text,
        lower_bound=str(lower_bound),
        upper_bound=str(upper_bound),
        lower_open=True,
        upper_open=True,
        control_points=points,
    )


def _dominates(
    candidate: sp.Expr,
    current: sp.Expr,
    domain: sp.Boolean,
    symbol: sp.Symbol,
    *,
    greater: bool,
) -> bool:
    relation = candidate <= current if greater else candidate >= current
    try:
        failure = sp.reduce_inequalities((relation,), symbol).as_set().intersect(domain.as_set())
    except (NotImplementedError, TypeError, ValueError):
        return False
    return failure is sp.S.EmptySet


def _pick_x(domain: sp.Boolean, symbol: sp.Symbol) -> sp.Expr | None:
    value = domain.as_set()
    if not isinstance(value, sp.Interval):
        return None
    if value.start is sp.S.NegativeInfinity and value.end is sp.S.Infinity:
        return sp.Integer(0)
    if value.end is sp.S.Infinity:
        return value.start + 1
    if value.start is sp.S.NegativeInfinity:
        return value.end - 1
    return sp.simplify((value.start + value.end) / 2)


__all__ = ["canonicalize_characteristic_polynomial", "solve_parameter_conditions"]
