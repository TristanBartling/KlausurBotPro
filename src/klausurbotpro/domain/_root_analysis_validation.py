"""Defensive validation and exact specialization for root analysis."""

from __future__ import annotations

from dataclasses import dataclass

import sympy as sp

from klausurbotpro.domain.diagnostics import DiagnosticCode
from klausurbotpro.domain.expression import ExactExpression
from klausurbotpro.domain.parameter_substitutions import (
    ParameterSubstitutions,
)
from klausurbotpro.domain.polynomial import Polynomial
from klausurbotpro.domain.polynomial_contracts import PolynomialLimits
from klausurbotpro.domain.polynomial_factory import PolynomialFactory
from klausurbotpro.domain.raw_transfer_function_contracts import (
    TransferFunctionDomainExclusion,
    TransferFunctionPrerequisite,
    TransferFunctionPrerequisiteKind,
)
from klausurbotpro.domain.reduced_transfer_function import (
    ReducedTransferFunction,
)
from klausurbotpro.domain.root_analysis_contracts import RootAnalysisLimits


@dataclass(frozen=True, slots=True)
class RootAnalysisFailure(Exception):
    """Expected validation or analysis failure."""

    code: DiagnosticCode
    message: str
    details: tuple[tuple[str, str], ...] = ()


def validate_reduced_transfer_function(
    reduced: ReducedTransferFunction,
    limits: RootAnalysisLimits,
) -> None:
    """Reject forged or inconsistent reduced values before algebra."""

    if type(reduced) is not ReducedTransferFunction:
        raise TypeError("Root analysis requires a ReducedTransferFunction.")
    if (
        type(reduced.numerator) is not Polynomial
        or type(reduced.denominator) is not Polynomial
        or reduced.variable_name != reduced.numerator.variable_name
        or reduced.variable_name != reduced.denominator.variable_name
        or reduced.denominator.is_zero
        or reduced.is_zero is not reduced.numerator.is_zero
    ):
        _invalid("Das reduzierte Übertragungsfunktionsobjekt ist inkonsistent.")
    if len(reduced.used_parameter_names) > limits.max_parameters:
        _limit("max_parameters")
    if len(reduced.domain_exclusions) > limits.max_domain_exclusions:
        _limit("max_domain_exclusions")
    if any(type(item) is not TransferFunctionPrerequisite for item in reduced.prerequisites):
        _invalid("Die Voraussetzungen sind nicht strukturell gültig.")
    if any(type(item) is not TransferFunctionDomainExclusion for item in reduced.domain_exclusions):
        _invalid("Die Definitionsausschlüsse sind nicht strukturell gültig.")

    polynomials = [
        reduced.numerator,
        reduced.denominator,
        *(item.polynomial for item in reduced.domain_exclusions),
    ]
    for polynomial in polynomials:
        if type(polynomial) is not Polynomial or polynomial.variable_name != reduced.variable_name:
            _invalid("Ein enthaltenes Polynom verwendet eine falsche Variable.")
        generic_degree = polynomial.degree_info.generic_degree
        if (
            generic_degree is not None
            and generic_degree > limits.max_polynomial_degree
        ):
            _limit("max_polynomial_degree")
        rebuilt = PolynomialFactory(
            PolynomialLimits(
                max_degree=limits.max_polynomial_degree,
                max_coefficients=limits.max_polynomial_degree + 1,
                max_structural_terms=limits.max_polynomial_degree + 1,
                max_parameters=limits.max_parameters,
                max_expression_nodes=limits.max_expression_nodes,
            )
        ).create(
            polynomial.expression,
            variable_name=reduced.variable_name,
            declared_parameter_names=polynomial.used_parameter_names,
        )
        if rebuilt.value != polynomial:
            _invalid("Ein enthaltenes Polynom besteht die Revalidierung nicht.")

    derived_names = set(reduced.numerator.used_parameter_names)
    derived_names.update(reduced.denominator.used_parameter_names)
    for prerequisite in reduced.prerequisites:
        if type(prerequisite.kind) is not TransferFunctionPrerequisiteKind:
            _invalid("Eine Voraussetzung hat eine ungültige Art.")
        for expression in prerequisite.expressions:
            if type(expression) is not ExactExpression:
                _invalid("Eine Voraussetzung enthält keinen exakten Ausdruck.")
            if reduced.variable_name in expression.symbol_names:
                _invalid("Eine Voraussetzung darf die Hauptvariable nicht enthalten.")
            prerequisite_result = PolynomialFactory(
                PolynomialLimits(
                    max_degree=limits.max_polynomial_degree,
                    max_coefficients=limits.max_polynomial_degree + 1,
                    max_structural_terms=limits.max_polynomial_degree + 1,
                    max_parameters=limits.max_parameters,
                    max_expression_nodes=limits.max_expression_nodes,
                )
            ).create(
                expression,
                variable_name=reduced.variable_name,
                declared_parameter_names=expression.symbol_names,
            )
            if prerequisite_result.value is None:
                _invalid("Eine Voraussetzung besteht die Revalidierung nicht.")
            derived_names.update(expression.symbol_names)
            _check_node_limit(expression._as_sympy(), limits.max_expression_nodes)
    for exclusion in reduced.domain_exclusions:
        derived_names.update(exclusion.polynomial.used_parameter_names)
    derived_names.discard(reduced.variable_name)
    if frozenset(derived_names) != reduced.used_parameter_names:
        _invalid("Die abgeleitete Parametermenge ist inkonsistent.")


def validate_substitutions(
    reduced: ReducedTransferFunction,
    substitutions: ParameterSubstitutions | None,
) -> tuple[ParameterSubstitutions | None, dict[sp.Symbol, sp.Rational] | None]:
    """Validate completeness and return an internal exact SymPy mapping."""

    expected = reduced.used_parameter_names
    if substitutions is not None and type(substitutions) is not ParameterSubstitutions:
        raise TypeError("substitutions must be ParameterSubstitutions or None.")
    if substitutions is None:
        if expected:
            return None, None
        substitutions = ParameterSubstitutions()
    provided = substitutions.parameter_names
    extra = provided - expected
    if extra:
        raise RootAnalysisFailure(
            DiagnosticCode.ROOT_ANALYSIS_INVALID_SUBSTITUTION,
            "Die Substitution enthält unbekannte oder unzulässige Parameter.",
            (("parameters", ",".join(sorted(extra))),),
        )
    missing = expected - provided
    if missing:
        raise RootAnalysisFailure(
            DiagnosticCode.ROOT_ANALYSIS_MISSING_PARAMETERS,
            "Für die exakte Analyse fehlen Parameterwerte.",
            (("parameters", ",".join(sorted(missing))),),
        )
    mapping = {
        sp.Symbol(item.parameter_name): sp.Rational(
            item.value.numerator, item.value.denominator
        )
        for item in substitutions.assignments
    }
    return substitutions, mapping


def validate_prerequisites(
    reduced: ReducedTransferFunction,
    mapping: dict[sp.Symbol, sp.Rational],
    limits: RootAnalysisLimits,
) -> None:
    """Evaluate every retained parameter-only prerequisite exactly."""

    for prerequisite in reduced.prerequisites:
        values = []
        for expression in prerequisite.expressions:
            specialized = sp.cancel(expression._as_sympy().subs(mapping))
            _check_node_limit(
                specialized,
                limits.max_substitution_nodes,
                "max_substitution_nodes",
            )
            if specialized.free_symbols:
                _invalid("Eine Voraussetzung blieb nach Substitution symbolisch.")
            values.append(specialized)
        satisfied = (
            values[0] != 0
            if prerequisite.kind is TransferFunctionPrerequisiteKind.EXPRESSION_NONZERO
            else any(value != 0 for value in values)
        )
        if not satisfied:
            raise RootAnalysisFailure(
                DiagnosticCode.ROOT_ANALYSIS_PREREQUISITE_VIOLATED,
                "Eine Definitionsvoraussetzung ist unter der Substitution verletzt.",
                (("prerequisite", prerequisite.description),),
            )


def specialize_polynomial(
    polynomial: Polynomial,
    mapping: dict[sp.Symbol, sp.Rational],
    limits: RootAnalysisLimits,
) -> Polynomial:
    """Substitute all parameters and revalidate over the exact rational field."""

    expression = sp.cancel(polynomial.expression._as_sympy().subs(mapping))
    _check_node_limit(
        expression, limits.max_substitution_nodes, "max_substitution_nodes"
    )
    result = PolynomialFactory(
        PolynomialLimits(
            max_degree=limits.max_polynomial_degree,
            max_coefficients=limits.max_polynomial_degree + 1,
            max_structural_terms=limits.max_polynomial_degree + 1,
            max_parameters=limits.max_parameters,
            max_expression_nodes=limits.max_expression_nodes,
        )
    ).create(
        ExactExpression._from_sympy(expression),
        variable_name=polynomial.variable_name,
    )
    if result.value is None:
        raise RootAnalysisFailure(
            DiagnosticCode.ROOT_ANALYSIS_INVALID_SUBSTITUTION,
            "Die Substitution erzeugt kein unterstütztes rationales Polynom.",
            tuple(
                ("diagnostic", diagnostic.code.value)
                for diagnostic in result.diagnostics
            ),
        )
    return result.value


def specialize_expression_as_polynomial(
    expression: ExactExpression,
    *,
    variable_name: str,
    mapping: dict[sp.Symbol, sp.Rational],
    limits: RootAnalysisLimits,
) -> Polynomial:
    """Specialize and validate a cancelled-factor expression."""

    _check_node_limit(
        expression._as_sympy(), limits.max_factor_nodes, "max_factor_nodes"
    )
    specialized = sp.cancel(expression._as_sympy().subs(mapping))
    _check_node_limit(
        specialized, limits.max_substitution_nodes, "max_substitution_nodes"
    )
    _check_node_limit(
        specialized, limits.max_factor_nodes, "max_factor_nodes"
    )
    result = PolynomialFactory(
        PolynomialLimits(
            max_degree=limits.max_polynomial_degree,
            max_coefficients=limits.max_polynomial_degree + 1,
            max_structural_terms=limits.max_polynomial_degree + 1,
            max_parameters=limits.max_parameters,
            max_expression_nodes=limits.max_factor_nodes,
        )
    ).create(
        ExactExpression._from_sympy(specialized),
        variable_name=variable_name,
    )
    if result.value is None:
        raise RootAnalysisFailure(
            DiagnosticCode.ROOT_ANALYSIS_INVALID_TRANSFER_FUNCTION,
            "Ein dokumentierter Kürzungsfaktor ist kein gültiges Polynom.",
        )
    return result.value


def _check_node_limit(
    expression: sp.Basic,
    maximum: int,
    limit_name: str = "max_expression_nodes",
) -> None:
    for count, _ in enumerate(sp.preorder_traversal(expression), start=1):
        if count > maximum:
            _limit(limit_name)


def _invalid(message: str) -> None:
    raise RootAnalysisFailure(
        DiagnosticCode.ROOT_ANALYSIS_INVALID_TRANSFER_FUNCTION,
        message,
    )


def _limit(name: str) -> None:
    raise RootAnalysisFailure(
        DiagnosticCode.ROOT_ANALYSIS_LIMIT_EXCEEDED,
        "Eine konfigurierte Grenze der Wurzelanalyse wurde überschritten.",
        (("limit", name),),
    )
