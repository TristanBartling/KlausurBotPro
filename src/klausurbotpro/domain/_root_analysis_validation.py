"""Defensive validation and exact specialization for root analysis."""

from __future__ import annotations

from dataclasses import dataclass
from keyword import iskeyword
from math import gcd
from typing import NoReturn

import sympy as sp

from klausurbotpro.domain.diagnostics import DiagnosticCode
from klausurbotpro.domain.expression import ExactExpression
from klausurbotpro.domain.parameter_substitutions import (
    ExactRationalValue,
    ParameterAssignment,
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


_MISSING = object()


def validate_reduced_transfer_function(
    reduced: ReducedTransferFunction,
    limits: RootAnalysisLimits,
) -> None:
    """Reject forged or inconsistent reduced values before algebra."""

    if type(reduced) is not ReducedTransferFunction:
        raise TypeError("Root analysis requires a ReducedTransferFunction.")
    if (
        type(reduced.variable_name) is not str
        or not reduced.variable_name.isidentifier()
        or iskeyword(reduced.variable_name)
        or type(reduced.used_parameter_names) is not frozenset
        or any(
            type(name) is not str
            or not name.isidentifier()
            or iskeyword(name)
            or name == reduced.variable_name
            for name in reduced.used_parameter_names
        )
        or type(reduced.prerequisites) is not tuple
        or type(reduced.domain_exclusions) is not tuple
        or type(reduced.is_zero) is not bool
    ):
        _invalid("Das reduzierte Übertragungsfunktionsobjekt ist inkonsistent.")
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

    _revalidate_polynomial(reduced.numerator, reduced.variable_name, limits)
    _revalidate_polynomial(reduced.denominator, reduced.variable_name, limits)

    derived_names = set(reduced.numerator.used_parameter_names)
    derived_names.update(reduced.denominator.used_parameter_names)
    derived_names.update(_validate_prerequisites(reduced, limits))
    derived_names.update(_validate_domain_exclusions(reduced, limits))
    derived_names.discard(reduced.variable_name)
    if frozenset(derived_names) != reduced.used_parameter_names:
        _invalid("Die abgeleitete Parametermenge ist inkonsistent.")


def _validate_prerequisites(
    reduced: ReducedTransferFunction,
    limits: RootAnalysisLimits,
) -> set[str]:
    used_names: set[str] = set()
    keys: list[tuple[str, tuple[str, ...]]] = []
    for prerequisite in reduced.prerequisites:
        if type(prerequisite) is not TransferFunctionPrerequisite:
            _invalid("Eine Voraussetzung hat einen ungültigen Typ.")
        kind = getattr(prerequisite, "kind", _MISSING)
        expressions = getattr(prerequisite, "expressions", _MISSING)
        origins = getattr(prerequisite, "origins", _MISSING)
        if type(kind) is not TransferFunctionPrerequisiteKind:
            _invalid("Eine Voraussetzung hat eine ungültige Art.")
        if type(expressions) is not tuple or not expressions:
            _invalid("Eine Voraussetzung benötigt strukturierte Ausdrücke.")
        if (
            kind is TransferFunctionPrerequisiteKind.EXPRESSION_NONZERO
            and len(expressions) != 1
        ):
            _invalid("EXPRESSION_NONZERO benötigt genau einen Ausdruck.")
        if (
            kind is TransferFunctionPrerequisiteKind.NOT_ALL_ZERO
            and len(expressions) < 2
        ):
            _invalid("NOT_ALL_ZERO benötigt mindestens zwei Ausdrücke.")
        _validate_origins(origins, "Voraussetzung")

        expression_keys: list[str] = []
        for expression in expressions:
            if type(expression) is not ExactExpression:
                _invalid("Eine Voraussetzung enthält keinen exakten Ausdruck.")
            if reduced.variable_name in expression.symbol_names:
                _invalid("Eine Voraussetzung darf die Hauptvariable nicht enthalten.")
            result = _polynomial_factory(limits).create(
                expression,
                variable_name=reduced.variable_name,
                declared_parameter_names=expression.symbol_names,
            )
            if result.value is None:
                _invalid("Eine Voraussetzung besteht die Revalidierung nicht.")
            _check_node_limit(expression._as_sympy(), limits.max_expression_nodes)
            expression_keys.append(expression.canonical_text)
            used_names.update(expression.symbol_names)
        if (
            kind is TransferFunctionPrerequisiteKind.NOT_ALL_ZERO
            and (
                tuple(expression_keys) != tuple(sorted(expression_keys))
                or len(expression_keys) != len(set(expression_keys))
            )
        ):
            _invalid("NOT_ALL_ZERO-Ausdrücke sind nicht kanonisch geordnet.")
        keys.append((kind.value, tuple(expression_keys)))

    if keys != sorted(keys) or len(keys) != len(set(keys)):
        _invalid("Voraussetzungen sind nicht deterministisch dedupliziert.")
    return used_names


def _validate_domain_exclusions(
    reduced: ReducedTransferFunction,
    limits: RootAnalysisLimits,
) -> set[str]:
    used_names: set[str] = set()
    keys: list[str] = []
    polynomials: list[Polynomial] = []
    for exclusion in reduced.domain_exclusions:
        if type(exclusion) is not TransferFunctionDomainExclusion:
            _invalid("Ein Definitionsausschluss hat einen ungültigen Typ.")
        polynomial = getattr(exclusion, "polynomial", _MISSING)
        origins = getattr(exclusion, "origins", _MISSING)
        if type(polynomial) is not Polynomial:
            _invalid("Ein Definitionsausschluss benötigt ein exaktes Polynom.")
        _validate_origins(origins, "Definitionsausschluss")
        _revalidate_polynomial(polynomial, reduced.variable_name, limits)
        if reduced.variable_name not in polynomial.expression.symbol_names:
            _invalid(
                "Ein Definitionsausschluss muss die Hauptvariable enthalten."
            )
        keys.append(polynomial.expression.canonical_text)
        polynomials.append(polynomial)
        used_names.update(polynomial.used_parameter_names)
    if keys != sorted(keys) or len(polynomials) != len(set(polynomials)):
        _invalid(
            "Definitionsausschlüsse sind nicht deterministisch dedupliziert."
        )
    return used_names


def _validate_origins(origins: object, subject: str) -> None:
    if (
        type(origins) is not tuple
        or not origins
        or any(type(origin) is not str or not origin for origin in origins)
        or origins != tuple(sorted(set(origins)))
    ):
        _invalid(f"{subject}-Herkünfte sind nicht kanonisch.")


def _revalidate_polynomial(
    polynomial: Polynomial,
    variable_name: str,
    limits: RootAnalysisLimits,
) -> None:
    if type(polynomial) is not Polynomial:
        _invalid("Ein enthaltenes Polynom hat einen ungültigen Typ.")
    polynomial_variable = getattr(polynomial, "variable_name", _MISSING)
    expression = getattr(polynomial, "expression", _MISSING)
    used_parameter_names = getattr(
        polynomial, "used_parameter_names", _MISSING
    )
    degree_info = getattr(polynomial, "degree_info", _MISSING)
    generic_degree = getattr(degree_info, "generic_degree", _MISSING)
    if (
        type(polynomial_variable) is not str
        or polynomial_variable != variable_name
        or type(expression) is not ExactExpression
        or type(used_parameter_names) is not frozenset
        or any(type(name) is not str for name in used_parameter_names)
        or (
            generic_degree is not None
            and (
                isinstance(generic_degree, bool)
                or type(generic_degree) is not int
                or generic_degree < 0
            )
        )
    ):
        _invalid("Ein enthaltenes Polynom verwendet eine falsche Variable.")
    if (
        generic_degree is not None
        and generic_degree > limits.max_polynomial_degree
    ):
        _limit("max_polynomial_degree")
    rebuilt = _polynomial_factory(limits).create(
        expression,
        variable_name=variable_name,
        declared_parameter_names=used_parameter_names,
    )
    try:
        matches = rebuilt.value == polynomial
    except (AttributeError, TypeError):
        matches = False
    if not matches:
        _invalid("Ein enthaltenes Polynom besteht die Revalidierung nicht.")


def _polynomial_factory(limits: RootAnalysisLimits) -> PolynomialFactory:
    return PolynomialFactory(
        PolynomialLimits(
            max_degree=limits.max_polynomial_degree,
            max_coefficients=limits.max_polynomial_degree + 1,
            max_structural_terms=limits.max_polynomial_degree + 1,
            max_parameters=limits.max_parameters,
            max_expression_nodes=limits.max_expression_nodes,
        )
    )


def validate_substitutions(
    reduced: ReducedTransferFunction,
    substitutions: ParameterSubstitutions | None,
    limits: RootAnalysisLimits,
) -> tuple[ParameterSubstitutions | None, dict[sp.Symbol, sp.Rational] | None]:
    """Validate completeness and return an internal exact SymPy mapping."""

    expected = reduced.used_parameter_names
    if substitutions is not None and type(substitutions) is not ParameterSubstitutions:
        raise TypeError("substitutions must be ParameterSubstitutions or None.")
    if substitutions is None:
        if expected:
            return None, None
        substitutions = ParameterSubstitutions()
    assignments = getattr(substitutions, "assignments", _MISSING)
    if type(assignments) is not tuple:
        _invalid_substitution("Die Substitutionsliste ist nicht kanonisch.")
    names: list[str] = []
    rational_values: list[tuple[str, int, int]] = []
    for assignment in assignments:
        if type(assignment) is not ParameterAssignment:
            _invalid_substitution("Eine Parameterzuweisung hat einen ungültigen Typ.")
        parameter_name = getattr(assignment, "parameter_name", _MISSING)
        value = getattr(assignment, "value", _MISSING)
        if (
            type(parameter_name) is not str
            or not parameter_name.isidentifier()
            or iskeyword(parameter_name)
        ):
            _invalid_substitution("Ein Parametername ist nicht sicher.")
        if type(value) is not ExactRationalValue:
            _invalid_substitution("Ein Parameterwert ist nicht exakt rational.")
        numerator = getattr(value, "numerator", _MISSING)
        denominator = getattr(value, "denominator", _MISSING)
        if (
            isinstance(numerator, bool)
            or type(numerator) is not int
            or isinstance(denominator, bool)
            or type(denominator) is not int
            or denominator <= 0
            or gcd(abs(numerator), denominator) != 1
        ):
            _invalid_substitution("Ein rationaler Parameterwert ist nicht kanonisch.")
        if (
            _integer_exceeds_digits(
                numerator, limits.max_substitution_integer_digits
            )
            or _integer_exceeds_digits(
                denominator, limits.max_substitution_integer_digits
            )
        ):
            _limit("max_substitution_integer_digits")
        names.append(parameter_name)
        rational_values.append((parameter_name, numerator, denominator))
    if len(names) != len(set(names)):
        _invalid_substitution("Ein Parameter wurde mehrfach belegt.")
    if tuple(names) != tuple(sorted(names)):
        _invalid_substitution("Parameterbelegungen sind nicht deterministisch sortiert.")
    provided = frozenset(names)
    if reduced.variable_name in provided:
        _invalid_substitution("Die Hauptvariable darf nicht substituiert werden.")
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
        sp.Symbol(parameter_name): sp.Rational(numerator, denominator)
        for parameter_name, numerator, denominator in rational_values
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


def _integer_exceeds_digits(value: int, maximum_digits: int) -> bool:
    magnitude = value if value >= 0 else -value
    if magnitude == 0 or magnitude.bit_length() <= maximum_digits:
        return False
    threshold: int = pow(10, maximum_digits)
    return bool(magnitude >= threshold)


def _invalid_substitution(message: str) -> NoReturn:
    raise RootAnalysisFailure(
        DiagnosticCode.ROOT_ANALYSIS_INVALID_SUBSTITUTION,
        message,
    )


def _invalid(message: str) -> NoReturn:
    raise RootAnalysisFailure(
        DiagnosticCode.ROOT_ANALYSIS_INVALID_TRANSFER_FUNCTION,
        message,
    )


def _limit(name: str) -> NoReturn:
    raise RootAnalysisFailure(
        DiagnosticCode.ROOT_ANALYSIS_LIMIT_EXCEEDED,
        "Eine konfigurierte Grenze der Wurzelanalyse wurde überschritten.",
        (("limit", name),),
    )
