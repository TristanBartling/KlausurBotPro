"""Exact rule-driven Laplace, PBZ and ordinary time-response analysis."""

from __future__ import annotations

from math import factorial

import sympy as sp

from klausurbotpro.domain.diagnostics import (
    Diagnostic,
    DiagnosticCode,
    DiagnosticSeverity,
)
from klausurbotpro.domain.expression import ExactExpression
from klausurbotpro.domain.root_analysis_contracts import (
    ExplicitExactRootValue,
    PolynomialRootStatus,
)
from klausurbotpro.domain.time_domain_contracts import (
    ComputationStatus,
    DirectLaplaceRule,
    EndValueStatus,
    FactorType,
    InverseLaplaceMapping,
    PartialFractionResult,
    PartialFractionTerm,
    PoleHalfPlane,
    PoleRecord,
    PoleRole,
    PolynomialDivisionResult,
    PolynomialDivisionStatus,
    RationalAnalysis,
    RationalClassification,
    RationalClassificationKind,
    RealFactor,
    RealFactorStructure,
    TimeDomainSolution,
    TimeDomainTaskType,
    TimeFunction,
    VerificationItem,
    VerificationReport,
    VerificationStatus,
)
from klausurbotpro.domain.transfer_function_reduction_contracts import (
    TransferFunctionReductionResult,
    TransferFunctionReductionStepKind,
)
from klausurbotpro.domain.transfer_function_root_analyzer import (
    TransferFunctionRootAnalyzer,
)


def exact(expression: sp.Expr) -> ExactExpression:
    """Cross the controlled internal SymPy boundary."""
    return ExactExpression._from_sympy(sp.factor(sp.cancel(expression)))


def direct_laplace(
    source: ExactExpression,
    *,
    task_type: TimeDomainTaskType = TimeDomainTaskType.DIRECT_LAPLACE,
) -> TimeDomainSolution:
    """Apply only the explicitly supported standard pairs term by term."""
    t, s = sp.symbols("t s")
    expression = source._as_sympy()
    if sp.Symbol("s") in expression.free_symbols:
        return _failed_solution(
            task_type,
            DiagnosticCode.TIME_IMAGE_VARIABLE_MIXED,
            "Zeit- und Bildvariable dürfen nicht gemischt werden.",
            source=source,
        )
    rules: list[DirectLaplaceRule] = []
    image_terms: list[sp.Expr] = []
    try:
        for term in sp.expand(expression).as_ordered_terms():
            image, rule_id, table_pair, shift = _direct_term(term, t, s)
            image_terms.append(image)
            rules.append(
                DirectLaplaceRule(
                    exact(term), exact(image), rule_id, table_pair, exact(shift)
                )
            )
    except ValueError as error:
        return _failed_solution(
            task_type,
            DiagnosticCode.UNSUPPORTED_TIME_FUNCTION,
            str(error),
            source=source,
        )
    image = sp.factor(sum(image_terms, sp.Integer(0)))
    inverse_check = sp.simplify(
        sp.inverse_laplace_transform(image, s, t).replace(sp.Heaviside, lambda *_: 1)
        - expression
    )
    verification = VerificationReport(
        (
            VerificationItem(
                "inverse_rule_check",
                _residual_status(inverse_check),
                exact(inverse_check),
                "Die inverse Tabellenkontrolle rekonstruiert f(t).",
            ),
        ),
        exact(sp.limit(expression, t, 0, dir="+")),
        EndValueStatus.NOT_APPLICABLE,
        None,
    )
    return TimeDomainSolution(
        task_type,
        ComputationStatus.SUCCESS,
        source,
        None,
        None,
        exact(image),
        None,
        None,
        None,
        tuple(rules),
        (),
        TimeFunction(source),
        (),
        verification,
        (),
    )


def inverse_rational(
    reduction: TransferFunctionReductionResult,
    *,
    task_type: TimeDomainTaskType,
    source_expression: ExactExpression | None = None,
    input_laplace: ExactExpression | None = None,
    system_laplace: ExactExpression | None = None,
    system_poles: tuple[PoleRecord, ...] = (),
    input_poles: tuple[PoleRecord, ...] = (),
    calculate_end_value: bool = False,
    stop_after_partial_fractions: bool = False,
) -> TimeDomainSolution:
    """Run exact division, real-factor PBZ, inverse mapping and checks."""
    if not reduction.succeeded or reduction.reduced is None or reduction.report is None:
        return _failed_solution(
            task_type,
            DiagnosticCode.NON_RATIONAL_IMAGE_EXPRESSION,
            "Die Bildfunktion ist keine unterstützte rationale Funktion.",
            source=source_expression,
            diagnostics=reduction.diagnostics,
        )
    s, t = sp.symbols("s t")
    raw = reduction.raw
    reduced = reduction.reduced
    pi_substitution = {sp.Symbol("pi"): sp.pi}
    raw_num = raw.numerator.expression._as_sympy().subs(pi_substitution)
    raw_den = raw.denominator.expression._as_sympy().subs(pi_substitution)
    num = reduced.numerator.expression._as_sympy().subs(pi_substitution)
    den = reduced.denominator.expression._as_sympy().subs(pi_substitution)
    raw_expression = sp.Mul(raw_num, sp.Pow(raw_den, -1, evaluate=False), evaluate=False)
    reduced_expression = sp.cancel(num / den)
    num_degree = int(sp.Poly(num, s).degree()) if num else 0
    den_degree = int(sp.Poly(den, s).degree())
    if num_degree < den_degree:
        kind = RationalClassificationKind.STRICTLY_PROPER
    elif num_degree == den_degree:
        kind = RationalClassificationKind.EQUAL_DEGREE
    else:
        kind = RationalClassificationKind.IMPROPER
    classification = RationalClassification(
        num_degree, den_degree, kind, num_degree >= den_degree
    )
    quotient, remainder = sp.div(sp.Poly(num, s), sp.Poly(den, s))
    q_expr = quotient.as_expr()
    r_expr = remainder.as_expr()
    division_residual = sp.expand(num - (q_expr * den + r_expr))
    division = PolynomialDivisionResult(
        exact(num),
        exact(den),
        exact(q_expr),
        exact(r_expr),
        exact(sp.cancel(r_expr / den)),
        exact(division_residual),
        (
            PolynomialDivisionStatus.NOT_REQUIRED
            if q_expr == 0
            else PolynomialDivisionStatus.SUCCESS
        ),
    )
    cancellation_factors = tuple(
        step.factor
        for step in reduction.report.steps
        if step.kind
        is TransferFunctionReductionStepKind.REMOVE_COMMON_POLYNOMIAL_FACTOR
        and step.factor is not None
    )
    rational = RationalAnalysis(
        exact(raw_expression),
        exact(reduced_expression),
        exact(raw_num),
        exact(raw_den),
        exact(num),
        exact(den),
        classification,
        division,
        cancellation_factors,
    )
    diagnostics = list(reduction.diagnostics)
    if cancellation_factors:
        diagnostics.extend(
            (
                _diagnostic(
                    DiagnosticSeverity.WARNING,
                    DiagnosticCode.CANCELLED_COMMON_FACTOR,
                    "Gemeinsame Faktoren wurden exakt gekürzt; Rohform bleibt erhalten.",
                ),
                _diagnostic(
                    DiagnosticSeverity.WARNING,
                    DiagnosticCode.HIDDEN_MODE_POSSIBLE,
                    "Die Kürzung kann interne Dynamik verdecken.",
                ),
            )
        )
    base_checks = [
        VerificationItem(
            "polynomial_division",
            _residual_status(division_residual),
            exact(division_residual),
            "Z(s)=Q(s)N(s)+R(s) wurde exakt geprüft.",
        )
    ]
    if q_expr != 0:
        diagnostics.append(
            _diagnostic(
                DiagnosticSeverity.ERROR,
                DiagnosticCode.DISTRIBUTIONAL_INVERSE_UNSUPPORTED,
                "Der Polynomanteil erfordert Distributionen; die gewöhnliche inverse "
                "Laplace-Transformation wird sicher abgebrochen.",
            )
        )
        verification = VerificationReport(
            tuple(base_checks), None, EndValueStatus.NOT_APPLICABLE, None
        )
        return TimeDomainSolution(
            task_type,
            ComputationStatus.UNSUPPORTED,
            source_expression,
            input_laplace,
            system_laplace,
            exact(reduced_expression),
            rational,
            None,
            None,
            (),
            (),
            None,
            (*system_poles, *input_poles),
            verification,
            tuple(diagnostics),
        )
    factor_structure = _factor_structure(den, s)
    if factor_structure.status is not ComputationStatus.SUCCESS:
        factor_code = (
            DiagnosticCode.PARAMETER_ASSUMPTIONS_INSUFFICIENT
            if factor_structure.status is ComputationStatus.INCONCLUSIVE
            else DiagnosticCode.FACTORIZATION_INCOMPLETE
        )
        diagnostics.append(
            _diagnostic(
                DiagnosticSeverity.ERROR,
                factor_code,
                "Die Faktorart ist ohne zusätzliche Parameterannahmen nicht eindeutig."
                if factor_structure.status is ComputationStatus.INCONCLUSIVE
                else "Der Nenner besitzt keine vollständig unterstützte reelle Faktorstruktur.",
            )
        )
        return TimeDomainSolution(
            task_type,
            factor_structure.status,
            source_expression,
            input_laplace,
            system_laplace,
            exact(reduced_expression),
            rational,
            factor_structure,
            None,
            (),
            (),
            None,
            (*system_poles, *input_poles),
            VerificationReport(tuple(base_checks), None, EndValueStatus.INCONCLUSIVE, None),
            tuple(diagnostics),
        )
    partial = _partial_fractions(sp.cancel(r_expr / den), factor_structure, s)
    if partial.status is not ComputationStatus.SUCCESS:
        diagnostics.append(
            _diagnostic(
                DiagnosticSeverity.ERROR,
                DiagnosticCode.PBZ_COEFFICIENT_SYSTEM_SINGULAR,
                "Das exakte PBZ-Koeffizientensystem konnte nicht eindeutig gelöst werden.",
            )
        )
        return TimeDomainSolution(
            task_type,
            ComputationStatus.FAILED,
            source_expression,
            input_laplace,
            system_laplace,
            exact(reduced_expression),
            rational,
            factor_structure,
            partial,
            (),
            (),
            None,
            (*system_poles, *input_poles),
            VerificationReport(tuple(base_checks), None, EndValueStatus.INCONCLUSIVE, None),
            tuple(diagnostics),
        )
    if stop_after_partial_fractions:
        base_checks.extend(
            (
                VerificationItem(
                    "factor_reconstruction",
                    _residual_status(
                        factor_structure.reconstruction_residual._as_sympy()
                    ),
                    factor_structure.reconstruction_residual,
                    "Das Faktorprodukt rekonstruiert den Nenner.",
                ),
                VerificationItem(
                    "pbz_recomposition",
                    _residual_status(partial.reconstruction_residual._as_sympy()),
                    partial.reconstruction_residual,
                    "Original minus Summe der PBZ-Terme ist exakt null.",
                    _numeric_samples(
                        partial.proper_fraction._as_sympy(),
                        partial.recomposed._as_sympy(),
                        s,
                    ),
                ),
            )
        )
        return TimeDomainSolution(
            task_type,
            ComputationStatus.SUCCESS,
            source_expression,
            input_laplace,
            system_laplace,
            exact(reduced_expression),
            rational,
            factor_structure,
            partial,
            (),
            (),
            None,
            (*system_poles, *input_poles),
            VerificationReport(
                tuple(base_checks), None, EndValueStatus.NOT_APPLICABLE, None
            ),
            tuple(diagnostics),
        )
    mappings, time_expression = _inverse_terms(partial.terms, s, t)
    time_expression = sp.simplify(time_expression)
    forward = sp.simplify(
        sp.laplace_transform(time_expression, t, s, noconds=True)
        - reduced_expression
    )
    initial = sp.limit(time_expression, t, 0, dir="+")
    output_poles = classify_reduction_poles(reduction, PoleRole.OUTPUT)
    if not output_poles:
        output_poles = _poles_from_factor_structure(
            factor_structure, PoleRole.OUTPUT, s
        )
    if any(item.half_plane is PoleHalfPlane.RIGHT for item in output_poles):
        diagnostics.append(
            _diagnostic(
                DiagnosticSeverity.WARNING,
                DiagnosticCode.UNSTABLE_SYSTEM_POLE,
                "Die Zeitfunktion enthält einen wachsenden Modus (Pol in der rechten Halbebene).",
            )
        )
    imaginary_axis_sources = (
        system_poles
        if system_poles
        else output_poles
        if task_type is TimeDomainTaskType.INVERSE_LAPLACE
        else ()
    )
    if any(
        item.half_plane is PoleHalfPlane.IMAGINARY_AXIS
        for item in imaginary_axis_sources
    ):
        diagnostics.append(
            _diagnostic(
                DiagnosticSeverity.WARNING,
                DiagnosticCode.IMAGINARY_AXIS_SYSTEM_POLE,
                "Mindestens ein relevanter Pol liegt auf der imaginären Achse.",
            )
        )
    end_status, end_value = (
        _guarded_end_value(reduced_expression, s, output_poles)
        if calculate_end_value
        else (EndValueStatus.NOT_APPLICABLE, None)
    )
    if end_status is EndValueStatus.END_VALUE_THEOREM_INVALID:
        diagnostics.append(
            _diagnostic(
                DiagnosticSeverity.WARNING,
                DiagnosticCode.END_VALUE_THEOREM_INVALID,
                "Der Endwertsatz ist wegen nicht strikt linker Pole von sY(s) ungültig.",
            )
        )
    base_checks.extend(
        (
            VerificationItem(
                "factor_reconstruction",
                _residual_status(factor_structure.reconstruction_residual._as_sympy()),
                factor_structure.reconstruction_residual,
                "Das Faktorprodukt rekonstruiert den Nenner.",
            ),
            VerificationItem(
                "pbz_recomposition",
                _residual_status(partial.reconstruction_residual._as_sympy()),
                partial.reconstruction_residual,
                "Original minus Summe der PBZ-Terme ist exakt null.",
                _numeric_samples(
                    partial.proper_fraction._as_sympy(),
                    partial.recomposed._as_sympy(),
                    s,
                ),
            ),
            VerificationItem(
                "forward_transform",
                _residual_status(forward),
                exact(forward),
                "Die Vorwärtstransformation rekonstruiert die reduzierte Bildfunktion.",
            ),
        )
    )
    if forward != 0:
        diagnostics.append(
            _diagnostic(
                DiagnosticSeverity.ERROR,
                DiagnosticCode.FORWARD_TRANSFORM_CHECK_FAILED,
                "Die Vorwärtstransformationskontrolle ist fehlgeschlagen.",
            )
        )
    verification = VerificationReport(
        tuple(base_checks),
        exact(initial),
        end_status,
        exact(end_value) if end_value is not None else None,
    )
    return TimeDomainSolution(
        task_type,
        ComputationStatus.SUCCESS if forward == 0 else ComputationStatus.FAILED,
        source_expression,
        input_laplace,
        system_laplace,
        exact(reduced_expression),
        rational,
        factor_structure,
        partial,
        (),
        tuple(mappings),
        TimeFunction(exact(time_expression)),
        (*system_poles, *input_poles, *output_poles),
        verification,
        tuple(diagnostics),
    )


def classify_reduction_poles(
    reduction: TransferFunctionReductionResult, role: PoleRole
) -> tuple[PoleRecord, ...]:
    """Adapt the existing exact transfer-function root analysis to pole roles."""
    if reduction.reduced is None:
        return ()
    root_analysis = TransferFunctionRootAnalyzer().analyze_reduction(reduction)
    poles = root_analysis.reduced_poles
    if poles is None or poles.status is not PolynomialRootStatus.COMPLETE:
        if reduction.reduced.used_parameter_names == frozenset({"pi"}):
            s = sp.Symbol("s")
            denominator = reduction.reduced.denominator.expression._as_sympy().subs(
                {sp.Symbol("pi"): sp.pi}
            )
            return _poles_from_factor_structure(
                _factor_structure(denominator, s), role, s
            )
        return ()
    records: list[PoleRecord] = []
    for occurrence in poles.roots:
        if not isinstance(occurrence.value, ExplicitExactRootValue):
            continue
        value = occurrence.value.expression._as_sympy()
        real_part = sp.simplify(sp.re(value))
        if real_part.is_negative:
            half_plane = PoleHalfPlane.LEFT
        elif real_part.is_positive:
            half_plane = PoleHalfPlane.RIGHT
        elif real_part.is_zero:
            half_plane = PoleHalfPlane.IMAGINARY_AXIS
        else:
            half_plane = PoleHalfPlane.INCONCLUSIVE
        records.append(
            PoleRecord(exact(value), occurrence.multiplicity, role, half_plane)
        )
    return tuple(records)


def _poles_from_factor_structure(
    structure: RealFactorStructure, role: PoleRole, s: sp.Symbol
) -> tuple[PoleRecord, ...]:
    records: list[PoleRecord] = []
    if structure.status is not ComputationStatus.SUCCESS:
        return ()
    for factor in structure.factors:
        expression = factor.factor._as_sympy()
        values: tuple[sp.Expr, ...]
        if factor.factor_type is FactorType.LINEAR:
            values = (sp.solve(expression, s)[0],)
        else:
            polynomial = sp.Poly(expression, s)
            alpha = sp.simplify(-polynomial.nth(1) / 2)
            omega = sp.sqrt(sp.simplify(polynomial.nth(0) - alpha**2))
            values = (alpha - sp.I * omega, alpha + sp.I * omega)
        for value in values:
            real_part = sp.simplify(sp.re(value))
            if real_part.is_negative:
                half_plane = PoleHalfPlane.LEFT
            elif real_part.is_positive:
                half_plane = PoleHalfPlane.RIGHT
            elif real_part.is_zero:
                half_plane = PoleHalfPlane.IMAGINARY_AXIS
            else:
                half_plane = PoleHalfPlane.INCONCLUSIVE
            records.append(
                PoleRecord(exact(value), factor.multiplicity, role, half_plane)
            )
    return tuple(records)


def _direct_term(
    term: sp.Expr, t: sp.Symbol, s: sp.Symbol
) -> tuple[sp.Expr, str, str, sp.Expr]:
    coefficient, dependent = term.as_independent(t, as_Add=False)
    factors = list(sp.Mul.make_args(dependent))
    shift = sp.Integer(0)
    trig: sp.Expr | None = None
    power = 0
    for factor in factors:
        if factor.func is sp.exp:
            candidate = sp.simplify(factor.args[0] / t)
            if sp.simplify(factor.args[0] - candidate * t) != 0 or t in candidate.free_symbols:
                raise ValueError("Nur exp(a*t) wird unterstützt.")
            shift += candidate
        elif factor.func in (sp.sin, sp.cos):
            if trig is not None:
                raise ValueError(
                    "Produkte mehrerer trigonometrischer Funktionen sind nicht unterstützt."
                )
            trig = factor
        elif factor == t:
            power += 1
        elif isinstance(factor, sp.Pow) and factor.base == t and factor.exp.is_Integer:
            exponent = int(factor.exp)
            if exponent < 0:
                raise ValueError("Negative Zeitpotenzen sind nicht unterstützt.")
            power += exponent
        elif factor != 1:
            raise ValueError(f"Nicht unterstützter Zeitfaktor: {factor}")
    shifted_s = s - shift
    if trig is None:
        image = coefficient * factorial(power) / shifted_s ** (power + 1)
        pair = "t^n <-> n!/s^(n+1)"
        return image, "POWER_EXP_SHIFT", pair, shift
    if power:
        raise ValueError("Zeitpotenzen mit Sinus/Kosinus sind in diesem PR nicht unterstützt.")
    omega = sp.simplify(trig.args[0] / t)
    if sp.simplify(trig.args[0] - omega * t) != 0 or t in omega.free_symbols:
        raise ValueError("Sinus/Kosinus benötigt ein lineares Argument omega*t.")
    if trig.func is sp.sin:
        image = coefficient * omega / (shifted_s**2 + omega**2)
        pair = "sin(omega*t) <-> omega/(s^2+omega^2)"
        rule = "SIN_EXP_SHIFT"
    else:
        image = coefficient * shifted_s / (shifted_s**2 + omega**2)
        pair = "cos(omega*t) <-> s/(s^2+omega^2)"
        rule = "COS_EXP_SHIFT"
    return image, rule, pair, shift


def _factor_structure(denominator: sp.Expr, s: sp.Symbol) -> RealFactorStructure:
    leading, raw_factors = sp.factor_list(denominator, s)
    normalized: list[RealFactor] = []
    scalar = leading
    status = ComputationStatus.SUCCESS
    for index, (factor, multiplicity) in enumerate(raw_factors, start=1):
        poly = sp.Poly(factor, s)
        degree = int(poly.degree())
        scalar *= poly.LC() ** multiplicity
        monic = sp.expand(factor / poly.LC())
        if degree == 1:
            factor_type = FactorType.LINEAR
            discriminant = None
        elif degree == 2:
            discriminant_expr = sp.discriminant(monic, s)
            discriminant = exact(discriminant_expr)
            if not discriminant_expr.is_negative:
                status = ComputationStatus.INCONCLUSIVE
            factor_type = FactorType.IRREDUCIBLE_QUADRATIC
        else:
            status = ComputationStatus.UNSUPPORTED
            factor_type = FactorType.IRREDUCIBLE_QUADRATIC
            discriminant = None
        normalized.append(
            RealFactor(
                f"factor_{index}",
                exact(monic),
                factor_type,
                int(multiplicity),
                discriminant,
            )
        )
    product = scalar
    for item in normalized:
        product *= item.factor._as_sympy() ** item.multiplicity
    residual = sp.expand(denominator - product)
    return RealFactorStructure(
        exact(denominator), exact(scalar), tuple(normalized), exact(residual), status
    )


def _partial_fractions(
    proper: sp.Expr, structure: RealFactorStructure, s: sp.Symbol
) -> PartialFractionResult:
    unknowns: list[sp.Symbol] = []
    templates: list[tuple[RealFactor, int, tuple[sp.Symbol, ...], sp.Expr]] = []
    for factor in structure.factors:
        for power in range(1, factor.multiplicity + 1):
            coeffs: tuple[sp.Symbol, ...]
            if factor.factor_type is FactorType.LINEAR:
                coefficient = sp.Symbol(f"A_{len(unknowns) + 1}")
                unknowns.append(coefficient)
                numerator = coefficient
                coeffs = (coefficient,)
            else:
                first = sp.Symbol(f"A_{len(unknowns) + 1}")
                second = sp.Symbol(f"B_{len(unknowns) + 2}")
                unknowns.extend((first, second))
                numerator = first * s + second
                coeffs = (first, second)
            templates.append(
                (
                    factor,
                    power,
                    coeffs,
                    numerator / factor.factor._as_sympy() ** power,
                )
            )
    template_sum = sum((item[3] for item in templates), sp.Integer(0))
    numerator = sp.Poly(sp.together(proper - template_sum).as_numer_denom()[0], s)
    equations = [coefficient for coefficient in numerator.all_coeffs()]
    solutions = sp.solve(equations, unknowns, dict=True)
    if len(solutions) != 1 or any(symbol not in solutions[0] for symbol in unknowns):
        empty = exact(sp.Integer(0))
        return PartialFractionResult(
            exact(proper),
            structure,
            str(template_sum),
            (),
            empty,
            exact(proper),
            ComputationStatus.FAILED,
        )
    solution = solutions[0]
    terms: list[PartialFractionTerm] = []
    solved_terms: list[sp.Expr] = []
    ansatz_parts: list[str] = []
    for factor, power, coefficient_symbols, template in templates:
        solved = sp.factor(template.subs(solution))
        solved_terms.append(solved)
        if len(coefficient_symbols) == 1:
            numerator_expr = solution[coefficient_symbols[0]]
        else:
            numerator_expr = (
                solution[coefficient_symbols[0]] * s
                + solution[coefficient_symbols[1]]
            )
        coefficients = tuple(exact(solution[item]) for item in coefficient_symbols)
        ansatz = str(template)
        ansatz_parts.append(ansatz)
        terms.append(
            PartialFractionTerm(
                factor.factor_id,
                factor.factor,
                factor.factor_type,
                power,
                exact(numerator_expr),
                coefficients,
                ansatz,
                (
                    "LINEAR_MULTIPLE_POLE"
                    if factor.factor_type is FactorType.LINEAR
                    else "REAL_QUADRATIC_PAIR"
                ),
                "exaktes Koeffizientensystem",
            )
        )
    recomposed = sp.factor(sum(solved_terms, sp.Integer(0)))
    residual = sp.factor(sp.cancel(proper - recomposed))
    return PartialFractionResult(
        exact(proper),
        structure,
        " + ".join(ansatz_parts),
        tuple(terms),
        exact(recomposed),
        exact(residual),
        ComputationStatus.SUCCESS if residual == 0 else ComputationStatus.FAILED,
    )


def _inverse_terms(
    terms: tuple[PartialFractionTerm, ...], s: sp.Symbol, t: sp.Symbol
) -> tuple[list[InverseLaplaceMapping], sp.Expr]:
    mappings: list[InverseLaplaceMapping] = []
    time_terms: list[sp.Expr] = []
    for term in terms:
        factor = term.factor._as_sympy()
        numerator = term.numerator._as_sympy()
        image = numerator / factor**term.power
        if term.factor_type is FactorType.LINEAR:
            root = sp.solve(factor, s)[0]
            coefficient = sp.simplify(numerator)
            time_term = (
                coefficient
                * t ** (term.power - 1)
                * sp.exp(root * t)
                / factorial(term.power - 1)
            )
            explanation = "A/(s-p)^k -> A*t^(k-1)*exp(p*t)/(k-1)!"
        else:
            if term.power != 1:
                raise ValueError(
                    "Mehrfache quadratische Faktoren sind noch nicht rücktransformierbar."
                )
            poly = sp.Poly(factor, s)
            alpha = sp.simplify(-poly.nth(1) / 2)
            omega_squared = sp.simplify(poly.nth(0) - alpha**2)
            omega = sp.sqrt(omega_squared)
            numerator_poly = sp.Poly(numerator, s)
            cosine_coefficient = numerator_poly.nth(1)
            constant = sp.simplify(numerator_poly.nth(0) + cosine_coefficient * alpha)
            time_term = sp.exp(alpha * t) * (
                cosine_coefficient * sp.cos(omega * t)
                + constant / omega * sp.sin(omega * t)
            )
            explanation = "Quadrat vervollständigen und reelles Sinus-/Kosinus-Paar verwenden."
        time_terms.append(time_term)
        mappings.append(
            InverseLaplaceMapping(exact(image), exact(time_term), term.inverse_pattern, explanation)
        )
    return mappings, sum(time_terms, sp.Integer(0))


def _guarded_end_value(
    expression: sp.Expr,
    s: sp.Symbol,
    output_poles: tuple[PoleRecord, ...],
) -> tuple[EndValueStatus, sp.Expr | None]:
    guarded = sp.cancel(s * expression)
    poles: list[PoleRecord] = []
    for pole in output_poles:
        if sp.simplify(pole.value._as_sympy()) == 0:
            if pole.multiplicity > 1:
                poles.append(
                    PoleRecord(
                        pole.value,
                        pole.multiplicity - 1,
                        pole.role,
                        pole.half_plane,
                    )
                )
        else:
            poles.append(pole)
    if any(item.half_plane is PoleHalfPlane.INCONCLUSIVE for item in poles):
        return EndValueStatus.INCONCLUSIVE, None
    if any(item.half_plane is not PoleHalfPlane.LEFT for item in poles):
        return EndValueStatus.END_VALUE_THEOREM_INVALID, None
    return EndValueStatus.VALID, sp.limit(guarded, s, 0)


def _numeric_samples(
    left: sp.Expr, right: sp.Expr, s: sp.Symbol
) -> tuple[tuple[str, str], ...]:
    samples: list[tuple[str, str]] = []
    for point in (sp.Rational(1, 2), sp.Integer(1), sp.Integer(2), sp.Integer(3)):
        try:
            difference = sp.N(left.subs(s, point) - right.subs(s, point), 12)
        except (ArithmeticError, ValueError, TypeError):
            continue
        if difference.is_finite:
            samples.append((str(point), str(difference)))
        if len(samples) == 2:
            break
    return tuple(samples)


def _residual_status(residual: sp.Expr) -> VerificationStatus:
    return VerificationStatus.PASS if sp.simplify(residual) == 0 else VerificationStatus.FAIL


def _diagnostic(
    severity: DiagnosticSeverity, code: DiagnosticCode, message: str
) -> Diagnostic:
    return Diagnostic(severity, code, message)


def _failed_solution(
    task_type: TimeDomainTaskType,
    code: DiagnosticCode,
    message: str,
    *,
    source: ExactExpression | None = None,
    diagnostics: tuple[Diagnostic, ...] = (),
) -> TimeDomainSolution:
    return TimeDomainSolution(
        task_type,
        ComputationStatus.FAILED,
        source,
        None,
        None,
        None,
        None,
        None,
        None,
        (),
        (),
        None,
        (),
        VerificationReport((), None, EndValueStatus.NOT_APPLICABLE, None),
        (*diagnostics, _diagnostic(DiagnosticSeverity.ERROR, code, message)),
    )


__all__ = [
    "classify_reduction_poles",
    "direct_laplace",
    "exact",
    "inverse_rational",
]
