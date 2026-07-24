"""Exact Hurwitz consumer for canonical polynomial degree cases 1 through 4."""

from __future__ import annotations

from dataclasses import replace
from typing import cast

import sympy as sp

from klausurbotpro.domain.expression import ExactExpression
from klausurbotpro.domain.hurwitz_contracts import (
    HurwitzAnalysisResult,
    HurwitzConditionStatus,
    HurwitzConditionStep,
    HurwitzDegreeCaseResult,
    HurwitzDeterminant,
    NumericalCheckStatus,
    NumericalPoleCheck,
)
from klausurbotpro.domain.parameter_core import (
    canonicalize_characteristic_polynomial,
    solve_parameter_conditions,
)
from klausurbotpro.domain.parameter_core_contracts import (
    AnalysisTarget,
    AtomicParameterCondition,
    CancellationStatus,
    CanonicalCharacteristicPolynomial,
    CharacteristicPolynomialInput,
    ConditionOrigin,
    DegreeCaseKind,
    ParameterConditionProblem,
    ParameterRegion,
    PolynomialRole,
    Relation,
    SolveStatus,
    SourceProvenance,
)
from klausurbotpro.domain.stability_numeric import check_numeric_poles
from klausurbotpro.domain.stability_presentation import (
    display_math,
    format_parameter_region_plain,
    latex_additive_equation,
    latex_numerical_check,
    latex_parameter_region,
    paragraph,
)

_NUMERICAL_CHECK_LABELS = {
    "consistent": "konsistent",
    "inconsistent": "widersprüchlich",
    "numerically_inconclusive": "numerisch nicht entscheidbar",
    "not_performed": "nicht durchgeführt",
}


def _exact(value: sp.Expr) -> ExactExpression:
    return ExactExpression._from_sympy(sp.sympify(value))


def analyze_hurwitz(
    canonical: CanonicalCharacteristicPolynomial,
) -> HurwitzAnalysisResult:
    """Generate Hurwitz conditions and delegate only their solution to the core."""
    if canonical.status is not SolveStatus.SOLVED_EXACT:
        return HurwitzAnalysisResult(
            canonical,
            (),
            _concept(canonical),
            "",
            "Analyse ungültig.",
            "",
            (),
            "",
            canonical.diagnostics,
        )
    results = tuple(_analyze_case(canonical, case) for case in canonical.degree_cases)
    results = _complete_exact_internal_factorization(canonical, results)
    trusted = all(
        result.status not in (SolveStatus.INVALID_INPUT, SolveStatus.UNSUPPORTED)
        and not (
            result.numerical_check is not None
            and result.numerical_check.status is NumericalCheckStatus.INCONSISTENT
        )
        for result in results
    )
    combined_region = _combined_region(results, canonical.input.decision_parameters)
    statement = (
        _overall_statement(
            results,
            canonical,
            combined_region,
            canonical.input.decision_parameters,
        )
        if trusted
        else ("Kein vertrauenswürdiges Endergebnis wegen einer schweren Diagnose.")
    )
    notice = ""
    if (
        canonical.input.role is PolynomialRole.REDUCED_TRANSFER_DENOMINATOR
        and canonical.input.cancellation_report is not None
        and canonical.input.cancellation_report.status
        is CancellationStatus.FACTORS_REMOVED
    ):
        notice = (
            "Der reduzierte E/A-Nenner beweist keine interne Stabilität. "
            "Entfernte instabile Dynamik kann verdeckt sein."
        )
    steps = _worked_steps(canonical, results, statement, notice)
    return HurwitzAnalysisResult(
        canonical,
        results,
        _concept(canonical),
        combined_region,
        statement,
        notice,
        steps,
        _latex(canonical, results, notice) if trusted else "",
        tuple(item for result in results for item in result.diagnostics),
    )


def _complete_exact_internal_factorization(
    canonical: CanonicalCharacteristicPolynomial,
    results: tuple[HurwitzDegreeCaseResult, ...],
) -> tuple[HurwitzDegreeCaseResult, ...]:
    cancellation = canonical.input.cancellation_report
    if (
        canonical.input.role is not PolynomialRole.RAW_CLOSED_LOOP_CHARACTERISTIC
        or canonical.input.analysis_target
        is not AnalysisTarget.INTERNAL_CLOSED_LOOP_ASYMPTOTIC
        or cancellation is None
        or cancellation.status is not CancellationStatus.FACTORS_REMOVED
        or not cancellation.removed_factors
        or len(results) != 1
    ):
        return results
    variable = sp.Symbol(canonical.input.variable)
    factor_expressions = tuple(
        factor._as_sympy() for factor in cancellation.removed_factors
    )
    factor_conditions = tuple(
        condition
        for factor in factor_expressions
        if (
            condition := _stable_linear_factor_condition(
                factor,
                variable,
                canonical.input.decision_parameters,
            )
        )
        is not None
    )
    if len(factor_conditions) != len(factor_expressions):
        return results
    factor_product = sp.expand(sp.Mul(*factor_expressions))
    try:
        quotient, remainder = sp.div(
            sp.Poly(canonical.expanded_polynomial._as_sympy(), variable),
            sp.Poly(factor_product, variable),
        )
    except sp.PolynomialError:
        return results
    if not remainder.is_zero or quotient.degree() < 1:
        return results
    reduced_input = CharacteristicPolynomialInput(
        _exact(quotient.as_expr()),
        canonical.input.variable,
        canonical.input.decision_parameters,
        canonical.input.fixed_symbols,
        canonical.input.assumptions,
        canonical.input.exclusions,
        PolynomialRole.DIRECT_CHARACTERISTIC_POLYNOMIAL,
        AnalysisTarget.INTERNAL_CLOSED_LOOP_ASYMPTOTIC,
        SourceProvenance(
            "Exakte Faktorprovenienz",
            canonical.input.provenance.source_reference,
            "Verbleibender Nenner nach exakt protokollierter Kürzung",
        ),
    )
    reduced = analyze_hurwitz(canonicalize_characteristic_polynomial(reduced_input))
    if len(reduced.case_results) != 1:
        return results
    reduced_case = reduced.case_results[0]
    if reduced_case.parameter_region.status is not SolveStatus.SOLVED_EXACT:
        return results
    try:
        reduced_formula = sp.sympify(reduced_case.parameter_region.exact_text)
    except (TypeError, ValueError):
        return results
    factor_relations = tuple(
        sp.Gt(condition.expression._as_sympy(), 0)
        for condition in factor_conditions
    )
    exact_formula = sp.And(reduced_formula, *factor_relations)
    exact_text = reduced_case.parameter_region.exact_text + " & " + " & ".join(
        f"({condition.expression.canonical_text} > 0)"
        for condition in factor_conditions
    )
    control_points = _factorized_control_points(
        reduced_case.parameter_region.control_points,
        canonical.input.decision_parameters,
        factor_relations,
    )
    exact_region = ParameterRegion(
        SolveStatus.SOLVED_EXACT,
        exact_text,
        sp.latex(exact_formula),
        x_domain=reduced_case.parameter_region.x_domain,
        control_points=control_points,
    )
    positive_symbols = _positive_symbols(
        canonical.input.assumptions + results[0].degree_case.guard,
        canonical.input.exclusions,
    )
    factor_steps = tuple(
        _condition_step(
            label=f"Faktor {factor.canonical_text}",
            origin=ConditionOrigin.CANCELLATION_FACTOR,
            expression=condition.expression._as_sympy(),
            parameters=canonical.input.decision_parameters,
            assumptions=canonical.input.assumptions,
            positive_symbols=positive_symbols,
        )
        for factor, condition in zip(
            cancellation.removed_factors,
            factor_conditions,
            strict=True,
        )
    )
    original = results[0]
    factorized_necessary = tuple(
        _resolved_by_factorization(item)
        for item in original.necessary_condition_steps
    )
    factorized_sufficient = tuple(
        _resolved_by_factorization(item)
        for item in original.sufficient_condition_steps
    )
    numerical = _numeric_check(
        original.degree_case,
        canonical.input.decision_parameters,
        exact_region,
    )
    diagnostics = (
        ("SYMBOLIC_NUMERIC_MISMATCH",)
        if numerical is not None
        and numerical.status is NumericalCheckStatus.INCONSISTENT
        else ()
    )
    completed = replace(
        original,
        solver_conditions=(*reduced_case.solver_conditions, *factor_conditions),
        necessary_condition_steps=factorized_necessary,
        sufficient_condition_steps=factorized_sufficient,
        minimal_condition_steps=(*reduced_case.minimal_condition_steps, *factor_steps),
        parameter_region=exact_region,
        numerical_check=numerical,
        statement=_case_statement(
            original.degree_case.degree,
            exact_region,
            _concept(canonical),
            canonical.input.decision_parameters,
        ),
        status=SolveStatus.SOLVED_EXACT,
        diagnostics=diagnostics,
    )
    return (completed,)


def _resolved_by_factorization(
    step: HurwitzConditionStep,
) -> HurwitzConditionStep:
    if step.status is HurwitzConditionStatus.ALREADY_SATISFIED:
        return step
    return replace(
        step,
        solved_text="",
        solved_latex="",
        status=HurwitzConditionStatus.RESOLVED_BY_FACTORIZATION,
        reference_label="exakte Faktorzerlegung",
        reason=(
            "Die Bedingung ist durch die exakte Stabilität des verbleibenden "
            "Nenners und aller protokollierten Faktoren abgedeckt."
        ),
    )


def _stable_linear_factor_condition(
    factor: sp.Expr,
    variable: sp.Symbol,
    parameters: tuple[str, ...],
) -> AtomicParameterCondition | None:
    try:
        polynomial = sp.Poly(sp.expand(factor), variable)
    except sp.PolynomialError:
        return None
    if polynomial.degree() != 1 or sp.simplify(polynomial.LC() - 1) != 0:
        return None
    constant = sp.simplify(polynomial.TC())
    declared = {sp.Symbol(name) for name in parameters}
    if not constant.free_symbols <= declared:
        return None
    return AtomicParameterCondition(
        _exact(constant),
        Relation.GT,
        ConditionOrigin.CANCELLATION_FACTOR,
        parameters,
        f"Faktor {sp.sstr(factor)} stabil",
    )


def _factorized_control_points(
    points: tuple[tuple[str, ...], ...],
    parameters: tuple[str, ...],
    relations: tuple[sp.Rel, ...],
) -> tuple[tuple[str, ...], ...]:
    valid: list[tuple[str, ...]] = []
    for point in points:
        substitutions = {
            sp.Symbol(name): sp.sympify(value)
            for name, value in zip(parameters, point, strict=True)
        }
        if all(bool(relation.subs(substitutions)) for relation in relations):
            valid.append(point)
    return tuple(valid)


def _analyze_case(
    canonical: CanonicalCharacteristicPolynomial,
    case: object,
) -> HurwitzDegreeCaseResult:
    from klausurbotpro.domain.parameter_core_contracts import PolynomialDegreeCase

    assert isinstance(case, PolynomialDegreeCase)
    if case.kind in (DegreeCaseKind.ZERO_POLYNOMIAL, DegreeCaseKind.CONSTANT_NONZERO):
        empty = solve_parameter_conditions(ParameterConditionProblem((), ()))
        return HurwitzDegreeCaseResult(
            case,
            (),
            (),
            (),
            (),
            (),
            (),
            (),
            empty,
            None,
            "Hurwitz ist für Grad 0 beziehungsweise das Nullpolynom nicht anwendbar.",
            SolveStatus.INVALID_INPUT,
        )
    if case.degree not in (1, 2, 3, 4):
        empty = solve_parameter_conditions(ParameterConditionProblem((), ()))
        return HurwitzDegreeCaseResult(
            case,
            (),
            (),
            (),
            (),
            (),
            (),
            (),
            empty,
            None,
            f"Grad {case.degree} wird nicht unterstützt.",
            SolveStatus.UNSUPPORTED,
        )
    coefficients_desc = tuple(value._as_sympy() for value in case.coefficients)
    by_power = {power: coefficients_desc[case.degree - power] for power in range(case.degree + 1)}
    matrix_expr = tuple(
        tuple(_matrix_entry(by_power, case.degree, row, column) for column in range(case.degree))
        for row in range(case.degree)
    )
    matrix = sp.Matrix(matrix_expr)
    determinants = tuple(
        HurwitzDeterminant(
            order,
            _exact(sp.expand(matrix[:order, :order].det())),
            _exact(sp.factor(matrix[:order, :order].det())),
        )
        for order in range(1, case.degree + 1)
    )
    parameters = canonical.input.decision_parameters
    full = tuple(
        AtomicParameterCondition(
            _exact(coefficient),
            Relation.GT,
            ConditionOrigin.COEFFICIENT,
            parameters,
            f"a_{power} > 0",
        )
        for power, coefficient in sorted(by_power.items(), reverse=True)
    ) + tuple(
        AtomicParameterCondition(
            item.expression,
            Relation.GT,
            ConditionOrigin.HURWITZ_DETERMINANT,
            parameters,
            f"Delta_{item.order} > 0",
        )
        for item in determinants
    )
    active_expressions = _minimal_expressions(case.degree, by_power, determinants)
    assumptions = canonical.input.assumptions
    positive_symbols = _positive_symbols(
        assumptions + case.guard, canonical.input.exclusions
    )
    solver = tuple(
        AtomicParameterCondition(
            _exact(_strip_positive_factors(expression, positive_symbols)),
            Relation.GT,
            origin,
            parameters,
            label,
        )
        for expression, origin, label in active_expressions
    )
    problem = ParameterConditionProblem(
        parameters,
        case.guard + solver,
        assumptions,
        canonical.input.exclusions,
    )
    region = solve_parameter_conditions(problem)
    condition_context = assumptions + case.guard
    necessary_steps = _classify_condition_steps(
        tuple(
            _condition_step(
                label=f"a_{power}",
                origin=ConditionOrigin.COEFFICIENT,
                expression=coefficient,
                parameters=parameters,
                assumptions=condition_context,
                positive_symbols=positive_symbols,
            )
            for power, coefficient in sorted(by_power.items(), reverse=True)
        ),
        parameters,
        condition_context,
    )
    sufficient_steps = _classify_condition_steps(
        tuple(
            _condition_step(
                label=f"Delta_{item.order}",
                origin=ConditionOrigin.HURWITZ_DETERMINANT,
                expression=item.expression._as_sympy(),
                parameters=parameters,
                assumptions=condition_context,
                positive_symbols=positive_symbols,
            )
            for item in determinants
        ),
        parameters,
        condition_context,
        prior=necessary_steps,
        positive_symbols=positive_symbols,
    )
    minimal_steps = tuple(
        item
        for item in (*necessary_steps, *sufficient_steps)
        if item.status
        in (HurwitzConditionStatus.ACTIVE, HurwitzConditionStatus.UNRESOLVED_SAFE)
    )
    numerical = _numeric_check(case, parameters, region)
    diagnostics: tuple[str, ...] = ()
    if numerical is not None and numerical.status is NumericalCheckStatus.INCONSISTENT:
        diagnostics = ("SYMBOLIC_NUMERIC_MISMATCH",)
    statement = _case_statement(
        case.degree,
        region,
        _concept(canonical),
        canonical.input.decision_parameters,
    )
    return HurwitzDegreeCaseResult(
        case,
        tuple(tuple(_exact(value) for value in row) for row in matrix_expr),
        determinants,
        full,
        solver,
        necessary_steps,
        sufficient_steps,
        minimal_steps,
        region,
        numerical,
        statement,
        region.status,
        diagnostics,
    )


def _condition_step(
    *,
    label: str,
    origin: ConditionOrigin,
    expression: sp.Expr,
    parameters: tuple[str, ...],
    assumptions: tuple[AtomicParameterCondition, ...],
    positive_symbols: frozenset[sp.Symbol],
) -> HurwitzConditionStep:
    expanded = sp.expand(expression)
    factored = sp.factor(expression)
    solved_expression = _strip_positive_factors(expression, positive_symbols)
    simplified = sp.simplify(solved_expression)
    if not simplified.free_symbols:
        if bool(simplified > 0):
            status = HurwitzConditionStatus.ALREADY_SATISFIED
            reason = "Die positive Konstante erfüllt die strikte Bedingung bereits."
        else:
            status = HurwitzConditionStatus.CONTRADICTORY
            reason = "Die konstante strikte Bedingung ist nicht erfüllt."
        return HurwitzConditionStep(
            label,
            origin,
            _exact(expression),
            _exact(expanded),
            _exact(factored),
            _exact(solved_expression),
            "",
            "",
            status,
            reason=reason,
        )
    relevant = tuple(
        name for name in parameters if sp.Symbol(name) in solved_expression.free_symbols
    )
    condition = AtomicParameterCondition(
        _exact(solved_expression),
        Relation.GT,
        origin,
        relevant,
        f"{label} > 0",
    )
    region = solve_parameter_conditions(
        ParameterConditionProblem(relevant, (condition,))
    )
    if region.status is SolveStatus.SOLVED_EXACT:
        status = HurwitzConditionStatus.ACTIVE
        solved_text = format_parameter_region_plain(region, relevant)
        solved_latex = (
            _affine_condition_latex(solved_expression, relevant)
            or _region_latex_body(region, relevant)
        )
        reason = ""
    elif region.status is SolveStatus.EMPTY:
        status = HurwitzConditionStatus.CONTRADICTORY
        solved_text = "keine Lösung"
        solved_latex = r"\varnothing"
        reason = "Die strikte Bedingung ist widersprüchlich."
    else:
        status = HurwitzConditionStatus.UNRESOLVED_SAFE
        solved_text = region.exact_text
        solved_latex = region.latex
        reason = "Die Bedingung bleibt erhalten, weil keine sichere Reduktion bewiesen ist."
    return HurwitzConditionStep(
        label,
        origin,
        _exact(expression),
        _exact(expanded),
        _exact(factored),
        _exact(solved_expression),
        solved_text,
        solved_latex,
        status,
        reason=reason,
    )


def _region_latex_body(
    region: ParameterRegion,
    parameters: tuple[str, ...],
) -> str:
    rendered = latex_parameter_region(region, parameters)
    body = rendered.removeprefix("\\[\n").removesuffix("\n\\]")
    if body.startswith(r"\begin{aligned}") and body.endswith(r"\end{aligned}"):
        body = body.removeprefix(r"\begin{aligned}").removesuffix(r"\end{aligned}")
        body = body.replace(r"\\", r",\quad ").replace("&", "")
    return body


def _affine_condition_latex(
    expression: sp.Expr,
    parameters: tuple[str, ...],
) -> str:
    bound = _affine_bound(expression, parameters)
    if bound is None:
        return ""
    name, direction, value = bound
    relation = ">" if direction == "lower" else "<"
    return rf"{_latex_parameter(name)} {relation} {_latex_factored_scalar(value)}"


def _latex_parameter(name: str) -> str:
    if "_" not in name:
        return name
    base, suffix = name.split("_", 1)
    return rf"{base}_{{{suffix}}}"


def _latex_factored_scalar(value: sp.Expr) -> str:
    coefficient, remainder = sp.factor(value).as_coeff_Mul()
    if remainder == 1 or not isinstance(coefficient, sp.Rational):
        return cast(str, sp.latex(value))
    sign = "-" if coefficient < 0 else ""
    magnitude = abs(coefficient)
    if magnitude == 1:
        coefficient_latex = ""
    elif magnitude.q == 1:
        coefficient_latex = str(magnitude.p)
    else:
        coefficient_latex = rf"\frac{{{magnitude.p}}}{{{magnitude.q}}}"
    remainder_latex = cast(str, sp.latex(remainder))
    if remainder.is_Add:
        remainder_latex = r"\left(" + remainder_latex + r"\right)"
    separator = r"\," if coefficient_latex else ""
    return sign + coefficient_latex + separator + remainder_latex


def _classify_condition_steps(
    steps: tuple[HurwitzConditionStep, ...],
    parameters: tuple[str, ...],
    assumptions: tuple[AtomicParameterCondition, ...],
    *,
    prior: tuple[HurwitzConditionStep, ...] = (),
    positive_symbols: frozenset[sp.Symbol] = frozenset(),
) -> tuple[HurwitzConditionStep, ...]:
    classified = list(steps)
    references = list(prior)
    for index, item in enumerate(classified):
        if item.status is not HurwitzConditionStatus.ACTIVE:
            references.append(item)
            continue
        equivalent = next(
            (
                other
                for other in references
                if other.status
                not in (
                    HurwitzConditionStatus.CONTRADICTORY,
                    HurwitzConditionStatus.UNRESOLVED_SAFE,
                )
                and _positive_proportional(
                    item.expression._as_sympy(),
                    other.expression._as_sympy(),
                    positive_symbols,
                )
            ),
            None,
        )
        if equivalent is not None:
            classified[index] = replace(
                item,
                status=HurwitzConditionStatus.REDUNDANT_EQUIVALENT,
                reference_label=equivalent.label,
                reason=(
                    f"Bereits durch {equivalent.label} abgedeckt; beide Bedingungen "
                    "sind unter den gesicherten positiven Faktoren äquivalent."
                ),
            )
        references.append(classified[index])

    for left_index, left in enumerate(classified):
        if left.status is not HurwitzConditionStatus.ACTIVE:
            continue
        for right_index, right in enumerate(classified):
            if left_index == right_index or right.status is not HurwitzConditionStatus.ACTIVE:
                continue
            if _is_weaker_bound(left, right, parameters, assumptions):
                classified[left_index] = replace(
                    left,
                    status=HurwitzConditionStatus.REDUNDANT_WEAKER,
                    reference_label=right.label,
                    reason=(
                        f"Schwächer als {right.label}; die stärkere gleichgerichtete "
                        "Grenze deckt diese Bedingung ab."
                    ),
                )
                break
    return tuple(classified)


def _positive_proportional(
    left: sp.Expr,
    right: sp.Expr,
    positive_symbols: frozenset[sp.Symbol],
) -> bool:
    if right == 0:
        return False
    ratio = sp.factor(sp.cancel(left / right))
    return _known_positive_expression(ratio, positive_symbols)


def _known_positive_expression(
    expression: sp.Expr,
    positive_symbols: frozenset[sp.Symbol],
) -> bool:
    if expression.is_number:
        return bool(expression.is_positive)
    numerator, denominator = sp.fraction(sp.factor(expression))
    return _known_positive_product(numerator, positive_symbols) and _known_positive_product(
        denominator, positive_symbols
    )


def _known_positive_product(
    expression: sp.Expr,
    positive_symbols: frozenset[sp.Symbol],
) -> bool:
    coefficient, factors = sp.factor_list(expression)
    if coefficient <= 0:
        return False
    return all(
        factor in positive_symbols
        or (
            factor.is_Pow
            and factor.base in positive_symbols
            and factor.exp.is_integer
        )
        for factor, _power in factors
    )


def _is_weaker_bound(
    candidate: HurwitzConditionStep,
    stronger: HurwitzConditionStep,
    parameters: tuple[str, ...],
    assumptions: tuple[AtomicParameterCondition, ...],
) -> bool:
    candidate_bound = _affine_bound(candidate.solved_expression._as_sympy(), parameters)
    stronger_bound = _affine_bound(stronger.solved_expression._as_sympy(), parameters)
    if candidate_bound is None or stronger_bound is None:
        return False
    candidate_name, candidate_direction, candidate_value = candidate_bound
    stronger_name, stronger_direction, stronger_value = stronger_bound
    if candidate_name != stronger_name or candidate_direction != stronger_direction:
        return False
    if sp.simplify(candidate_value - stronger_value) == 0:
        return False
    relation = (
        sp.Le(candidate_value, stronger_value)
        if candidate_direction == "lower"
        else sp.Ge(candidate_value, stronger_value)
    )
    symbols = candidate_value.free_symbols | stronger_value.free_symbols
    return _prove_relation(relation, assumptions, symbols)


def _affine_bound(
    expression: sp.Expr,
    parameters: tuple[str, ...],
) -> tuple[str, str, sp.Expr] | None:
    for name in reversed(parameters):
        symbol = sp.Symbol(name)
        try:
            polynomial = sp.Poly(sp.expand(expression), symbol)
        except sp.PolynomialError:
            continue
        if polynomial.degree() != 1:
            continue
        coefficient, constant = polynomial.all_coeffs()
        if not coefficient.is_number or coefficient == 0:
            continue
        boundary = sp.factor(-constant / coefficient)
        return name, ("lower" if coefficient > 0 else "upper"), boundary
    return None


def _prove_relation(
    relation: sp.Rel,
    assumptions: tuple[AtomicParameterCondition, ...],
    symbols: set[sp.Symbol],
) -> bool:
    if relation is sp.true:
        return True
    if relation is sp.false or len(symbols) > 1:
        return False
    if not symbols:
        return bool(relation)
    symbol = next(iter(symbols))
    relevant = tuple(
        _sympy_relation(item)
        for item in assumptions
        if item.expression._as_sympy().free_symbols <= {symbol}
    )
    try:
        counterexample = sp.reduce_inequalities(
            (*relevant, sp.Not(relation)), symbol
        )
    except (NotImplementedError, TypeError, ValueError):
        return False
    return counterexample is sp.false


def _sympy_relation(condition: AtomicParameterCondition) -> sp.Rel:
    expression = condition.expression._as_sympy()
    constructors = {
        Relation.EQ: sp.Eq,
        Relation.NE: sp.Ne,
        Relation.LT: sp.Lt,
        Relation.LE: sp.Le,
        Relation.GT: sp.Gt,
        Relation.GE: sp.Ge,
    }
    return constructors[condition.relation](expression, 0)


def _matrix_entry(coefficients: dict[int, sp.Expr], degree: int, row: int, column: int) -> sp.Expr:
    pair = row % 2
    shift = row // 2
    power = (1 - pair) + 2 * (column - shift)
    return coefficients.get(power, sp.Integer(0)) if 0 <= power <= degree else sp.Integer(0)


def _minimal_expressions(
    degree: int,
    by_power: dict[int, sp.Expr],
    determinants: tuple[HurwitzDeterminant, ...],
) -> tuple[tuple[sp.Expr, ConditionOrigin, str], ...]:
    coefficients = tuple(
        (by_power[power], ConditionOrigin.COEFFICIENT, f"a_{power} > 0")
        for power in range(degree - 1, -1, -1)
    )
    if degree == 1:
        return coefficients
    extra_orders = () if degree == 2 else ((2,) if degree == 3 else (2, 3))
    extras = tuple(
        (
            determinants[order - 1].expression._as_sympy(),
            ConditionOrigin.HURWITZ_DETERMINANT,
            f"Delta_{order} > 0",
        )
        for order in extra_orders
    )
    return coefficients + extras


def _positive_symbols(
    assumptions: tuple[AtomicParameterCondition, ...],
    exclusions: tuple[AtomicParameterCondition, ...],
) -> frozenset[sp.Symbol]:
    strict = {
        condition.expression._as_sympy()
        for condition in assumptions
        if condition.relation is Relation.GT
        and isinstance(condition.expression._as_sympy(), sp.Symbol)
    }
    nonnegative = {
        condition.expression._as_sympy()
        for condition in assumptions
        if condition.relation is Relation.GE
        and isinstance(condition.expression._as_sympy(), sp.Symbol)
    }
    nonzero = {
        condition.expression._as_sympy()
        for condition in (*assumptions, *exclusions)
        if condition.relation is Relation.NE
        and isinstance(condition.expression._as_sympy(), sp.Symbol)
    }
    return frozenset(strict | (nonnegative & nonzero))


def _strip_positive_factors(expression: sp.Expr, positive: frozenset[sp.Symbol]) -> sp.Expr:
    if expression == 0:
        return sp.Integer(0)
    coefficient, factors = sp.factor_list(expression)
    retained: list[sp.Expr] = []
    sign = sp.sign(coefficient)
    if sign == -1:
        retained.append(sp.Integer(-1))
    for factor, power in factors:
        if factor in positive or (
            factor.is_Pow and factor.base in positive and factor.exp.is_integer and factor.exp > 0
        ):
            continue
        retained.append(factor**power)
    return sp.factor(sp.Mul(*retained)) if retained else sp.Integer(1)


def _numeric_check(
    case: object,
    parameters: tuple[str, ...],
    region: object,
) -> NumericalPoleCheck | None:
    from klausurbotpro.domain.parameter_core_contracts import ParameterRegion, PolynomialDegreeCase

    assert isinstance(case, PolynomialDegreeCase)
    assert isinstance(region, ParameterRegion)
    if region.status is not SolveStatus.SOLVED_EXACT:
        return None
    if parameters and not region.control_points:
        return NumericalPoleCheck(
            NumericalCheckStatus.NUMERICALLY_INCONCLUSIVE,
            (),
            (),
            "",
        )
    point_pairs: tuple[tuple[str, str], ...] = ()
    if parameters:
        values = region.control_points[0]
        point_pairs = tuple((name, value) for name, value in zip(parameters, values, strict=True))
    check, _ = check_numeric_poles(case, point_pairs, expected_rhp_roots=0)
    return check


def _concept(canonical: CanonicalCharacteristicPolynomial) -> str:
    labels = {
        AnalysisTarget.INTERNAL_CLOSED_LOOP_ASYMPTOTIC: "interne asymptotische Stabilität",
        AnalysisTarget.EXTERNAL_BIBO: "E/A-asymptotische (BIBO-)Stabilität",
        AnalysisTarget.STATE_ASYMPTOTIC: "asymptotische Zustandsstabilität",
    }
    return labels[canonical.input.analysis_target]


def _case_statement(
    degree: int,
    region: ParameterRegion,
    concept: str,
    parameters: tuple[str, ...],
) -> str:
    if region.status is SolveStatus.EMPTY:
        return f"Grad {degree}: keine zulässige Einstellung für {concept}."
    if region.status is SolveStatus.SOLVED_EXACT:
        if not parameters:
            return f"Grad {degree}: {concept} ist nachgewiesen."
        return (
            f"Grad {degree}: {concept} genau für "
            f"{format_parameter_region_plain(region, parameters)}."
        )
    status = {
        SolveStatus.PARTIALLY_SOLVED_SAFE: "teilweise gelöst",
        SolveStatus.UNSUPPORTED: "nicht unterstützt",
        SolveStatus.INVALID_INPUT: "ungültige Eingabe",
        SolveStatus.INDETERMINATE: "nicht entscheidbar",
    }.get(region.status, "nicht vollständig gelöst")
    return f"Grad {degree}: {concept} nicht vollständig entscheidbar ({status})."


def _overall_statement(
    results: tuple[HurwitzDegreeCaseResult, ...],
    canonical: CanonicalCharacteristicPolynomial,
    combined_region: str,
    parameters: tuple[str, ...],
) -> str:
    concept = _concept(canonical)
    solved = tuple(
        item.parameter_region
        for item in results
        if item.parameter_region.status is SolveStatus.SOLVED_EXACT
    )
    if not parameters and len(solved) == len(results):
        return _stable_latex_text(canonical)
    if combined_region and len(solved) == 1:
        return f"{concept} genau für {format_parameter_region_plain(solved[0], parameters)}."
    statements = " ".join(result.statement for result in results)
    return f"{concept}: {statements}"


def _combined_region(
    results: tuple[HurwitzDegreeCaseResult, ...], parameters: tuple[str, ...]
) -> str:
    solved = tuple(
        item.parameter_region
        for item in results
        if item.status is SolveStatus.SOLVED_EXACT
        and item.parameter_region.status is SolveStatus.SOLVED_EXACT
    )
    if not solved:
        return "∅" if results and all(item.status is SolveStatus.EMPTY for item in results) else ""
    if len(parameters) != 1:
        return solved[0].exact_text if len(solved) == 1 else ""
    symbol = sp.Symbol(parameters[0])
    union: sp.Set = sp.S.EmptySet
    for region in solved:
        try:
            union = union.union(sp.sympify(region.exact_text).as_set())
        except (TypeError, ValueError, AttributeError):
            return ""
    return str(union.as_relational(symbol))


def _worked_steps(
    canonical: CanonicalCharacteristicPolynomial,
    results: tuple[HurwitzDegreeCaseResult, ...],
    statement: str,
    notice: str,
) -> tuple[tuple[str, str], ...]:
    direct = canonical.input.provenance.producer == "Direkteingabe"
    steps: list[tuple[str, str]] = []
    if direct:
        steps.extend(
            (
                (
                    "Gegeben",
                    f"N({canonical.input.variable})=p({canonical.input.variable})="
                    f"{canonical.input.polynomial.canonical_text}",
                ),
                ("Gesucht", _concept(canonical)),
                ("Methode und Stabilitätsbegriff", f"Hurwitz-Kriterium; {_concept(canonical)}"),
                ("Polynomrolle", _role_text(canonical)),
                (
                    "Voraussetzungen und Annahmen",
                    ", ".join(
                        item.label or _relation_text(item)
                        for item in canonical.input.assumptions
                    )
                    or "keine zusätzlichen Parameterannahmen",
                ),
            )
        )
    steps.append(
        (
            "Charakteristisches Polynom",
            f"N({canonical.input.variable})="
            f"{canonical.expanded_polynomial.canonical_text}",
        )
    )
    if direct:
        steps.append(
            (
                "Kursnotation",
                f"N({canonical.input.variable})=p({canonical.input.variable}) bezeichnet "
                "das analysierte charakteristische Polynom.",
            )
        )
    for result in results:
        guard = ", ".join(item.label for item in result.degree_case.guard) or "kein Gradfall-Guard"
        steps.append(
            (
                "Gradfall und Voraussetzungen",
                f"Grad {result.degree_case.degree}; {guard}; "
                "der Leitkoeffizient ist sicher positiv orientiert.",
            )
        )
        for power, coefficient in zip(
            range(result.degree_case.degree, -1, -1),
            result.degree_case.coefficients,
            strict=True,
        ):
            steps.append((f"Koeffizient a_{power}", coefficient.canonical_text))
        steps.append(
            (
                "Notwendige Bedingungen",
                "Nach positiver Orientierung gilt a_i>0 für alle Koeffizienten.",
            )
        )
        steps.extend(
            (f"Notwendige Bedingung {item.label}", _condition_step_text(item))
            for item in result.necessary_condition_steps
        )
        steps.extend(
            (f"Redundanzhinweis {item.label}", item.reason)
            for item in result.necessary_condition_steps
            if item.status
            in (
                HurwitzConditionStatus.REDUNDANT_EQUIVALENT,
                HurwitzConditionStatus.REDUNDANT_WEAKER,
            )
        )
        steps.append(("Hurwitz-Matrix", _matrix_text(result.matrix)))
        steps.append(
            (
                "Hinreichende Bedingungen",
                "Für alle Hurwitz-Determinanten gilt Delta_i>0.",
            )
        )
        steps.extend(
            (f"Hinreichende Bedingung {item.label}", _condition_step_text(item))
            for item in result.sufficient_condition_steps
        )
        steps.extend(
            (f"Redundanzhinweis {item.label}", item.reason)
            for item in result.sufficient_condition_steps
            if item.status
            in (
                HurwitzConditionStatus.REDUNDANT_EQUIVALENT,
                HurwitzConditionStatus.REDUNDANT_WEAKER,
            )
        )
        minimal = ", ".join(
            item.solved_text or f"{item.expression.canonical_text}>0"
            for item in result.minimal_condition_steps
        ) or "keine zusätzliche aktive Bedingung"
        region = _hurwitz_region_plain(
            result.parameter_region, canonical.input.decision_parameters
        )
        steps.extend(
            (
                ("Verbleibendes minimales Bedingungssystem", minimal),
                ("Schnittmenge", region),
                ("Exaktes Stabilitätsgebiet", region),
                ("Offene Grenzen", "Alle Hurwitz-Gleichheitsränder sind ausgeschlossen."),
                ("Numerische Gegenkontrolle", _numeric_text(result.numerical_check)),
            )
        )
    if notice:
        steps.append(("Kürzungswarnung", notice))
    steps.append(("Endaussage", statement))
    return tuple(steps)


def _condition_step_text(step: HurwitzConditionStep) -> str:
    base = f"{step.label}={step.expression.canonical_text}>0"
    if step.solved_text and step.solved_text not in ("wahr", "falsch"):
        base += f" ⇔ {step.solved_text}"
    status = {
        HurwitzConditionStatus.ACTIVE: "bleibt aktiv",
        HurwitzConditionStatus.ALREADY_SATISFIED: "bereits erfüllt",
        HurwitzConditionStatus.REDUNDANT_EQUIVALENT: "äquivalent abgedeckt",
        HurwitzConditionStatus.REDUNDANT_WEAKER: "als schwächere Grenze redundant",
        HurwitzConditionStatus.RESOLVED_BY_FACTORIZATION: (
            "durch exakte Faktorzerlegung abgedeckt"
        ),
        HurwitzConditionStatus.CONTRADICTORY: "widersprüchlich",
        HurwitzConditionStatus.UNRESOLVED_SAFE: "sicher ungelöst und weiterhin aktiv",
    }[step.status]
    return f"{base}; {status}" + (f"; {step.reason}" if step.reason else "")


def _relation_text(condition: AtomicParameterCondition) -> str:
    symbols = {
        Relation.GT: ">",
        Relation.GE: ">=",
        Relation.LT: "<",
        Relation.LE: "<=",
        Relation.EQ: "=",
        Relation.NE: "!=",
    }
    return f"{condition.expression.canonical_text} {symbols[condition.relation]} 0"


def _matrix_text(matrix: tuple[tuple[ExactExpression, ...], ...]) -> str:
    return "[" + "; ".join(", ".join(item.canonical_text for item in row) for row in matrix) + "]"


def _numeric_text(check: NumericalPoleCheck | None) -> str:
    if check is None:
        return "nicht verfügbar"
    status = _NUMERICAL_CHECK_LABELS.get(check.status.value, "nicht verfügbar")
    point = ", ".join(f"{name}={value}" for name, value in check.parameter_point)
    prefix = f"Kontrollpunkt {point}; " if point else ""
    return f"{prefix}{status}; Pole: {', '.join(check.poles) or 'nicht verfügbar'}"


def _latex(
    canonical: CanonicalCharacteristicPolynomial,
    results: tuple[HurwitzDegreeCaseResult, ...],
    notice: str,
) -> str:
    direct = canonical.input.provenance.producer == "Direkteingabe"
    blocks: list[str] = []
    if direct:
        blocks.extend(
            (
                paragraph("Gegeben", "Direkte Eingabe eines charakteristischen Polynoms."),
                latex_additive_equation(
                    f"p({canonical.input.variable})",
                    canonical.input.polynomial,
                    variable=canonical.input.variable,
                ),
                display_math(
                    f"N({canonical.input.variable})=p({canonical.input.variable})"
                ),
                paragraph("Gesucht", _concept(canonical)),
                paragraph("Methode", f"Hurwitz-Kriterium für {_concept(canonical)}."),
                paragraph(
                    "Voraussetzungen",
                    "Der Leitkoeffizient wird sicher positiv orientiert; "
                    + (
                        ", ".join(
                            item.label or _relation_text(item)
                            for item in canonical.input.assumptions
                        )
                        or "keine zusätzlichen Parameterannahmen"
                    )
                    + ".",
                ),
            )
        )
    blocks.extend(
        (
            paragraph("Charakteristisches Polynom", "Analysiert wird:"),
            latex_additive_equation(
                f"N({canonical.input.variable})",
                canonical.expanded_polynomial,
                variable=canonical.input.variable,
            ),
        )
    )
    for result in results:
        matrix_latex = sp.latex(
            sp.Matrix([[item._as_sympy() for item in row] for row in result.matrix])
        )
        coefficient_lines = tuple(
            rf"a_{{{power}}}&={coefficient.latex}"
            for power, coefficient in zip(
                range(result.degree_case.degree, -1, -1),
                result.degree_case.coefficients,
                strict=True,
            )
        )
        blocks.append(paragraph("Koeffizienten", f"Für Grad {result.degree_case.degree} gilt:"))
        blocks.append(
            display_math(r"\begin{aligned}" + r"\\".join(coefficient_lines) + r"\end{aligned}")
        )
        blocks.append(
            paragraph("Notwendige Bedingungen", r"Für alle Koeffizienten gilt \(a_i>0\).")
        )
        blocks.extend(_latex_condition_step(item) for item in result.necessary_condition_steps)
        blocks.append(
            paragraph(
                "Reduzierte notwendige Bedingungen",
                _reduced_condition_text(result.necessary_condition_steps),
            )
        )
        blocks.append(
            paragraph(
                "Hurwitz-Matrix",
                "Hurwitz-Matrix nach der Konvention des Vorlesungsskripts: "
                "erste Zeile a_1, a_3, a_5, ...",
            )
        )
        blocks.append(display_math(r"H=" + matrix_latex))
        blocks.append(
            paragraph("Hinreichende Bedingungen", r"Für alle Determinanten gilt \(\Delta_i>0\).")
        )
        blocks.extend(_latex_condition_step(item) for item in result.sufficient_condition_steps)
        blocks.append(
            paragraph(
                "Reduzierte hinreichende Bedingungen",
                _reduced_condition_text(result.sufficient_condition_steps),
            )
        )
        blocks.append(
            paragraph(
                "Bedingungssystem",
                "Die aktiven notwendigen und hinreichenden Bedingungen werden geschnitten.",
            )
        )
        blocks.append(
            paragraph("Schnittmenge", "Minimales Bedingungssystem und exaktes Gebiet:")
        )
        blocks.append(_latex_case_region(canonical, result))
        blocks.append(latex_numerical_check(result.numerical_check))
    if notice:
        blocks.append(paragraph("Warnung", notice))
    blocks.append(paragraph("Ergebnis", "Das exakte Stabilitätsgebiet lautet:"))
    blocks.append(_latex_final_box(canonical, results))
    return "\n\n".join(blocks)


def _latex_condition_step(step: HurwitzConditionStep) -> str:
    status = {
        HurwitzConditionStatus.ACTIVE: "bleibt aktiv",
        HurwitzConditionStatus.ALREADY_SATISFIED: "bereits erfüllt",
        HurwitzConditionStatus.REDUNDANT_EQUIVALENT: "bereits äquivalent abgedeckt",
        HurwitzConditionStatus.REDUNDANT_WEAKER: "schwächer und redundant",
        HurwitzConditionStatus.RESOLVED_BY_FACTORIZATION: (
            "durch exakte Faktorzerlegung abgedeckt"
        ),
        HurwitzConditionStatus.CONTRADICTORY: "widersprüchlich",
        HurwitzConditionStatus.UNRESOLVED_SAFE: "sicher ungelöst; bleibt aktiv",
    }[step.status]
    label = _latex_label(step.label)
    if len(step.expression.latex) > 85:
        definition = latex_additive_equation(label, step.expression, terms_per_line=2)
        lines = [rf"{label}&>0"]
        if step.solved_latex and step.solved_text not in ("wahr", "falsch"):
            lines.append(rf"&\Longleftrightarrow {step.solved_latex}")
        lines.append(rf"&\quad\text{{{_escape_latex_text(status)}}}")
        condition = display_math(
            r"\begin{aligned}" + r"\\".join(lines) + r"\end{aligned}"
        )
        return definition + "\n\n" + condition
    lines = [rf"{label}&={step.expression.latex}>0"]
    if step.expanded_expression != step.expression:
        lines.append(rf"&={step.expanded_expression.latex}>0")
    if step.factored_expression not in (step.expression, step.expanded_expression):
        lines.append(rf"&={step.factored_expression.latex}>0")
    if step.solved_latex and step.solved_text not in ("wahr", "falsch"):
        lines.append(rf"&\Longleftrightarrow {step.solved_latex}")
    lines.append(rf"&\quad\text{{{_escape_latex_text(status)}}}")
    return display_math(r"\begin{aligned}" + r"\\".join(lines) + r"\end{aligned}")


def _latex_label(label: str) -> str:
    if label.startswith("Delta_"):
        return rf"\Delta_{{{label.removeprefix('Delta_')}}}"
    if label.startswith("a_"):
        return rf"a_{{{label.removeprefix('a_')}}}"
    return _escape_latex_text(label)


def _reduced_condition_text(steps: tuple[HurwitzConditionStep, ...]) -> str:
    active = tuple(
        item.solved_text or f"{item.expression.canonical_text}>0"
        for item in steps
        if item.status
        in (HurwitzConditionStatus.ACTIVE, HurwitzConditionStatus.UNRESOLVED_SAFE)
    )
    redundant = tuple(
        f"{item.label} gegenüber {item.reference_label}"
        for item in steps
        if item.status
        in (
            HurwitzConditionStatus.REDUNDANT_EQUIVALENT,
            HurwitzConditionStatus.REDUNDANT_WEAKER,
        )
    )
    factorized = tuple(
        item.label
        for item in steps
        if item.status is HurwitzConditionStatus.RESOLVED_BY_FACTORIZATION
    )
    text = "Aktiv: " + (", ".join(active) or "keine zusätzliche Bedingung")
    if redundant:
        text += ". Redundant: " + ", ".join(redundant)
    if factorized:
        text += ". Durch exakte Faktorzerlegung abgedeckt: " + ", ".join(factorized)
    return text


def _hurwitz_region_plain(
    region: ParameterRegion,
    parameters: tuple[str, ...],
) -> str:
    if not parameters and region.status is SolveStatus.SOLVED_EXACT:
        return "Keine zusätzlichen Parameterbedingungen."
    return format_parameter_region_plain(region, parameters)


def _latex_case_region(
    canonical: CanonicalCharacteristicPolynomial,
    result: HurwitzDegreeCaseResult,
) -> str:
    if (
        not canonical.input.decision_parameters
        and result.parameter_region.status is SolveStatus.SOLVED_EXACT
    ):
        return paragraph(
            "Parameterbedingungen",
            "Keine zusätzlichen Parameterbedingungen.",
        )
    active = tuple(
        item
        for item in result.minimal_condition_steps
        if item.status is HurwitzConditionStatus.ACTIVE and item.solved_latex
    )
    if len(active) == 1:
        return display_math(active[0].solved_latex)
    return latex_parameter_region(
        result.parameter_region,
        canonical.input.decision_parameters,
    )


def _latex_final_box(
    canonical: CanonicalCharacteristicPolynomial,
    results: tuple[HurwitzDegreeCaseResult, ...],
) -> str:
    if canonical.input.decision_parameters:
        if len(results) == 1:
            active = tuple(
                item
                for item in results[0].minimal_condition_steps
                if item.status is HurwitzConditionStatus.ACTIVE
                and item.solved_latex
            )
            if len(active) == 1:
                return display_math(r"\boxed{" + active[0].solved_latex + "}")
            return latex_parameter_region(
                results[0].parameter_region,
                canonical.input.decision_parameters,
                boxed=True,
            )
        return "\n\n".join(
            latex_parameter_region(
                item.parameter_region,
                canonical.input.decision_parameters,
                boxed=True,
            )
            for item in results
        )
    stable = all(
        item.parameter_region.status is SolveStatus.SOLVED_EXACT
        and item.numerical_check is not None
        and item.numerical_check.status is NumericalCheckStatus.CONSISTENT
        for item in results
    )
    text = _stable_latex_text(canonical) if stable else _not_stable_latex_text(canonical)
    return display_math(r"\boxed{\text{" + _escape_latex_text(text) + "}}")


def _role_text(canonical: CanonicalCharacteristicPolynomial) -> str:
    return {
        PolynomialRole.DIRECT_CHARACTERISTIC_POLYNOMIAL: "direktes charakteristisches Polynom",
        PolynomialRole.RAW_CLOSED_LOOP_CHARACTERISTIC: "rohes geschlossenes Polynom",
        PolynomialRole.REDUCED_TRANSFER_DENOMINATOR: "reduzierter E/A-Nenner",
        PolynomialRole.STATE_CHARACTERISTIC_POLYNOMIAL: "Zustandsraum-Charakteristik",
    }[canonical.input.role]


def _stable_latex_text(canonical: CanonicalCharacteristicPolynomial) -> str:
    return {
        AnalysisTarget.INTERNAL_CLOSED_LOOP_ASYMPTOTIC: "intern asymptotisch stabil",
        AnalysisTarget.EXTERNAL_BIBO: "E/A-asymptotisch (BIBO-)stabil",
        AnalysisTarget.STATE_ASYMPTOTIC: "asymptotisch zustandsstabil",
    }[canonical.input.analysis_target]


def _not_stable_latex_text(canonical: CanonicalCharacteristicPolynomial) -> str:
    return {
        AnalysisTarget.INTERNAL_CLOSED_LOOP_ASYMPTOTIC: (
            "nicht intern asymptotisch stabil"
        ),
        AnalysisTarget.EXTERNAL_BIBO: "nicht E/A-asymptotisch (BIBO-)stabil",
        AnalysisTarget.STATE_ASYMPTOTIC: "nicht asymptotisch zustandsstabil",
    }[canonical.input.analysis_target]


def _escape_latex_text(value: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "{": r"\{",
        "}": r"\}",
        "$": r"\$",
        "&": r"\&",
        "#": r"\#",
        "%": r"\%",
        "_": r"\_",
        "^": r"\textasciicircum{}",
        "~": r"\textasciitilde{}",
    }
    return "".join(replacements.get(character, character) for character in value)


__all__ = ["analyze_hurwitz"]
