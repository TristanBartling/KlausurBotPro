"""Exact Hurwitz consumer for canonical polynomial degree cases 1 through 4."""

from __future__ import annotations

import sympy as sp

from klausurbotpro.domain.expression import ExactExpression
from klausurbotpro.domain.hurwitz_contracts import (
    HurwitzAnalysisResult,
    HurwitzDegreeCaseResult,
    HurwitzDeterminant,
    NumericalCheckStatus,
    NumericalPoleCheck,
)
from klausurbotpro.domain.parameter_core import solve_parameter_conditions
from klausurbotpro.domain.parameter_core_contracts import (
    AnalysisTarget,
    AtomicParameterCondition,
    CanonicalCharacteristicPolynomial,
    ConditionOrigin,
    DegreeCaseKind,
    ParameterConditionProblem,
    PolynomialRole,
    Relation,
    SolveStatus,
)


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
        _overall_statement(results, _concept(canonical), combined_region)
        if trusted
        else ("Kein vertrauenswürdiges Endergebnis wegen einer schweren Diagnose.")
    )
    notice = ""
    if canonical.input.role is PolynomialRole.REDUCED_TRANSFER_DENOMINATOR:
        notice = (
            "Kürzungshinweis: Der reduzierte E/A-Nenner beweist keine interne "
            "Stabilität; entfernte instabile Dynamik kann verdeckt sein."
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
        _latex(canonical, results, statement, notice),
        tuple(item for result in results for item in result.diagnostics),
    )


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
    positive_symbols = _positive_symbols(assumptions, canonical.input.exclusions)
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
    numerical = _numeric_check(case, parameters, region)
    diagnostics: tuple[str, ...] = ()
    if numerical is not None and numerical.status is NumericalCheckStatus.INCONSISTENT:
        diagnostics = ("SYMBOLIC_NUMERIC_MISMATCH",)
    statement = _case_statement(case.degree, region, _concept(canonical))
    return HurwitzDegreeCaseResult(
        case,
        tuple(tuple(_exact(value) for value in row) for row in matrix_expr),
        determinants,
        full,
        solver,
        region,
        numerical,
        statement,
        region.status,
        diagnostics,
    )


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
    substitutions: dict[sp.Symbol, sp.Expr] = {}
    point_pairs: tuple[tuple[str, str], ...] = ()
    if parameters:
        values = region.control_points[0]
        substitutions = {
            sp.Symbol(name): sp.sympify(value)
            for name, value in zip(parameters, values, strict=True)
        }
        point_pairs = tuple((name, value) for name, value in zip(parameters, values, strict=True))
    variable = next(iter(case.polynomial._as_sympy().free_symbols - set(substitutions)), None)
    if variable is None:
        return None
    try:
        polynomial = sp.Poly(case.polynomial._as_sympy().subs(substitutions), variable)
        roots = tuple(complex(value) for value in sp.nroots(polynomial, n=30, maxsteps=100))
    except (sp.PolynomialError, ValueError, TypeError):
        return NumericalPoleCheck(
            NumericalCheckStatus.NUMERICALLY_INCONCLUSIVE,
            point_pairs,
            (),
            "",
        )
    maximum = max(value.real for value in roots)
    status = (
        NumericalCheckStatus.CONSISTENT if maximum < -1e-9 else NumericalCheckStatus.INCONSISTENT
    )
    return NumericalPoleCheck(
        status,
        point_pairs,
        tuple(f"{value.real:.10g}{value.imag:+.10g}j" for value in roots),
        f"{maximum:.10g}",
    )


def _concept(canonical: CanonicalCharacteristicPolynomial) -> str:
    labels = {
        AnalysisTarget.INTERNAL_CLOSED_LOOP_ASYMPTOTIC: "interne asymptotische Stabilität",
        AnalysisTarget.EXTERNAL_BIBO: "E/A-asymptotische (BIBO-)Stabilität",
        AnalysisTarget.STATE_ASYMPTOTIC: "asymptotische Zustandsstabilität",
    }
    return labels[canonical.input.analysis_target]


def _case_statement(degree: int, region: object, concept: str) -> str:
    from klausurbotpro.domain.parameter_core_contracts import ParameterRegion

    assert isinstance(region, ParameterRegion)
    if region.status is SolveStatus.EMPTY:
        return f"Grad {degree}: keine zulässige Einstellung für {concept}."
    if region.status is SolveStatus.SOLVED_EXACT:
        return f"Grad {degree}: {concept} genau für {region.exact_text}."
    return f"Grad {degree}: {concept} nicht vollständig entscheidbar ({region.status.value})."


def _overall_statement(
    results: tuple[HurwitzDegreeCaseResult, ...], concept: str, combined_region: str
) -> str:
    if combined_region:
        return f"{concept} genau für {combined_region}."
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
    steps: list[tuple[str, str]] = [
        ("1. Eingabepolynom", canonical.input.polynomial.canonical_text),
        ("2. Rolle und Analyseziel", f"{canonical.input.role.value}; {_concept(canonical)}"),
        (
            "3. Annahmen",
            ", ".join(
                item.label or str(_relation_text(item)) for item in canonical.input.assumptions
            )
            or "keine",
        ),
        ("4. Kanonisierung", canonical.expanded_polynomial.canonical_text),
    ]
    for result in results:
        steps.extend(
            (
                (
                    "5. Gradfall und Guard",
                    f"Grad {result.degree_case.degree}; "
                    + ", ".join(item.label for item in result.degree_case.guard),
                ),
                (
                    "6. Koeffizienten",
                    ", ".join(item.canonical_text for item in result.degree_case.coefficients),
                ),
                ("7. Hurwitz-Matrix", _matrix_text(result.matrix)),
                (
                    "8. Determinanten",
                    ", ".join(
                        f"Delta_{item.order}={item.expression.canonical_text}"
                        for item in result.determinants
                    ),
                ),
                ("9. Bedingungen", ", ".join(item.label for item in result.solver_conditions)),
                ("10. Parametergebiet", result.parameter_region.exact_text),
                ("11. Offene Grenzen", "Hurwitz-Gleichheitsränder sind ausgeschlossen."),
                ("12. Numerische Gegenkontrolle", _numeric_text(result.numerical_check)),
            )
        )
    if notice:
        steps.append(("Kürzungswarnung", notice))
    steps.append(("13. Endaussage", statement))
    return tuple(steps)


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
        return "keine Kontrolle verfügbar"
    return f"{check.status.value}; Pole: {', '.join(check.poles) or 'nicht verfügbar'}"


def _latex(
    canonical: CanonicalCharacteristicPolynomial,
    results: tuple[HurwitzDegreeCaseResult, ...],
    statement: str,
    notice: str,
) -> str:
    lines = [
        r"\text{Charakteristisches Polynom:}\quad p(s)="
        + canonical.expanded_polynomial.latex
        + r".",
        r"\text{Stabilitätsbegriff:}\quad \text{" + _concept(canonical) + r"}.",
    ]
    for result in results:
        matrix_latex = sp.latex(
            sp.Matrix([[item._as_sympy() for item in row] for row in result.matrix])
        )
        lines.append(rf"\text{{Gradfall: }}\deg p={result.degree_case.degree}.")
        lines.append(r"H=" + matrix_latex + r".")
        lines.extend(
            rf"\Delta_{{{item.order}}}={item.expression.latex}." for item in result.determinants
        )
        conditions = r",\quad ".join(
            item.expression.latex + r">0" for item in result.solver_conditions
        )
        lines.append(r"\text{Bedingungssystem:}\quad " + conditions + r".")
        lines.append(r"\text{Parametergebiet:}\quad " + result.parameter_region.latex + r".")
        lines.append(
            r"\text{Numerische Kontrolle:}\quad \text{"
            + _numeric_text(result.numerical_check).replace("_", r"\_")
            + r"}."
        )
    if notice:
        lines.append(r"\textbf{Warnung: }\text{" + notice + r"}")
    lines.append(r"\boxed{\text{" + statement + r"}}")
    return "\n\n".join(r"\[" + line + r"\]" for line in lines)


__all__ = ["analyze_hurwitz"]
