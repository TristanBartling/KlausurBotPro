"""Internal complete exact solver for parameter-free rational polynomials."""

from __future__ import annotations

from math import gcd

import sympy as sp
from sympy.polys.rootoftools import ComplexRootOf

from klausurbotpro.domain.expression import ExactExpression
from klausurbotpro.domain.root_analysis_contracts import (
    ExplicitExactRootValue,
    PolynomialRootAnalysis,
    PolynomialRootStatus,
    RootAnalysisLimits,
    RootOccurrence,
    RootOfValue,
    RootSource,
)


def solve_exact_polynomial_roots(
    polynomial: sp.Poly,
    *,
    source: RootSource,
    source_expression: ExactExpression,
    original_degree: int | None,
    limits: RootAnalysisLimits,
    origins: tuple[str, ...] = (),
) -> PolynomialRootAnalysis:
    """Return every exact root, preserving exact multiplicities."""

    if polynomial.is_zero:
        return PolynomialRootAnalysis(
            PolynomialRootStatus.ZERO_POLYNOMIAL,
            source,
            source_expression,
            original_degree=original_degree,
            origins=origins,
        )
    actual_degree = int(polynomial.degree())
    if actual_degree == 0:
        return PolynomialRootAnalysis(
            PolynomialRootStatus.CONSTANT_NONZERO,
            source,
            source_expression,
            original_degree=original_degree,
            actual_degree=0,
            origins=origins,
        )
    if actual_degree > limits.max_polynomial_degree:
        raise ValueError("max_polynomial_degree")

    raw_roots: list[tuple[sp.Expr, int]] = []
    _, factors = polynomial.factor_list()
    distinct_root_count = sum(int(factor.degree()) for factor, _ in factors)
    if distinct_root_count > limits.max_results:
        raise ValueError("max_results")
    expected_rootof_count = sum(
        int(factor.degree()) * int(multiplicity)
        for factor, multiplicity in factors
        if int(factor.degree()) > 2
    )
    if expected_rootof_count > limits.max_exact_rootof_count:
        raise ValueError("max_exact_rootof_count")
    for factor, factor_multiplicity in factors:
        factor_roots = factor.all_roots(
            multiple=False,
            radicals=int(factor.degree()) <= 2,
        )
        raw_roots.extend(
            (root, int(root_multiplicity) * int(factor_multiplicity))
            for root, root_multiplicity in factor_roots
        )
    rootof_count = sum(
        multiplicity
        for root, multiplicity in raw_roots
        if isinstance(root, ComplexRootOf)
    )
    if rootof_count > limits.max_exact_rootof_count:
        raise ValueError("max_exact_rootof_count")
    if sum(int(multiplicity) for _, multiplicity in raw_roots) != actual_degree:
        raise ArithmeticError("The exact solver did not return a complete root set.")

    occurrences: list[RootOccurrence] = []
    for index, (root, multiplicity) in enumerate(raw_roots):
        if isinstance(root, ComplexRootOf):
            coefficients = _primitive_integer_coefficients(root.poly)
            value: ExplicitExactRootValue | RootOfValue = RootOfValue(
                coefficients, int(root.index)
            )
        else:
            value = ExplicitExactRootValue(ExactExpression._from_sympy(root))
        occurrences.append(
            RootOccurrence(value, int(multiplicity), source, index)
        )
    return PolynomialRootAnalysis(
        PolynomialRootStatus.COMPLETE,
        source,
        source_expression,
        tuple(occurrences),
        original_degree=original_degree,
        actual_degree=actual_degree,
        origins=origins,
    )


def exact_root_as_sympy(value: ExplicitExactRootValue | RootOfValue) -> sp.Expr:
    """Reconstruct a trusted internal exact root from its public contract."""

    if isinstance(value, ExplicitExactRootValue):
        return value.expression._as_sympy()
    assert isinstance(value, RootOfValue)
    symbol = sp.Symbol("_root")
    polynomial = sp.Poly.from_list(value.defining_coefficients, gens=symbol)
    return sp.CRootOf(polynomial, value.root_index)


def _primitive_integer_coefficients(polynomial: sp.Poly) -> tuple[int, ...]:
    _, cleared = polynomial.clear_denoms(convert=True)
    _, primitive = cleared.primitive()
    coefficients = tuple(int(value) for value in primitive.all_coeffs())
    if coefficients[0] < 0:
        coefficients = tuple(-value for value in coefficients)
    common = 0
    for coefficient in coefficients:
        common = gcd(common, abs(coefficient))
    if common > 1:
        coefficients = tuple(value // common for value in coefficients)
    return coefficients
