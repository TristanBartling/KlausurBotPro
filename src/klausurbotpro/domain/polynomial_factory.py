"""Controlled ExactExpression-to-Polynomial domain validation."""

from __future__ import annotations

from dataclasses import dataclass
from keyword import iskeyword
from typing import NoReturn

import sympy as sp
from sympy.polys.polyerrors import BasePolynomialError

from klausurbotpro.domain.diagnostics import (
    Diagnostic,
    DiagnosticCode,
    DiagnosticSeverity,
)
from klausurbotpro.domain.expression import ExactExpression
from klausurbotpro.domain.polynomial import Polynomial
from klausurbotpro.domain.polynomial_contracts import (
    PolynomialCondition,
    PolynomialConditionKind,
    PolynomialCreationResult,
    PolynomialDegreeInfo,
    PolynomialLimits,
)

_RESOURCE_ERRORS = (MemoryError, RecursionError, OverflowError)
_ASSUMPTION_FREE_SYMBOL = {"commutative": True}
_DEFAULT_LIMITS = PolynomialLimits()


@dataclass(frozen=True, slots=True)
class _PolynomialFailure(Exception):
    code: DiagnosticCode
    message: str
    details: tuple[tuple[str, str], ...] = ()


class PolynomialFactory:
    """Build exact polynomials without accepting or parsing raw strings."""

    def __init__(self, limits: PolynomialLimits = _DEFAULT_LIMITS) -> None:
        self._limits = limits

    def create(
        self,
        expression: ExactExpression,
        *,
        variable_name: str = "s",
        declared_parameter_names: frozenset[str] = frozenset(),
        field: str | None = None,
    ) -> PolynomialCreationResult:
        """Validate and construct one exact univariate polynomial."""
        if not isinstance(expression, ExactExpression):
            raise TypeError("PolynomialFactory requires an ExactExpression.")

        try:
            return self._create(
                expression,
                variable_name=variable_name,
                declared_parameter_names=declared_parameter_names,
                field=field,
            )
        except _RESOURCE_ERRORS as error:
            return self._failure_result(
                DiagnosticCode.POLYNOMIAL_RESOURCE_LIMIT_EXCEEDED,
                "Die Polynomialvalidierung überschreitet verfügbare Ressourcen.",
                field,
                (("exception", type(error).__name__),),
            )
        except _PolynomialFailure as failure:
            return self._failure_result(
                failure.code,
                failure.message,
                field,
                failure.details,
            )
        except BasePolynomialError as error:
            return self._failure_result(
                DiagnosticCode.POLYNOMIAL_NOT_POLYNOMIAL,
                "Der Ausdruck ist kein unterstütztes exaktes Polynom.",
                field,
                (("exception", type(error).__name__),),
            )

    def _create(
        self,
        expression: ExactExpression,
        *,
        variable_name: str,
        declared_parameter_names: frozenset[str],
        field: str | None,
    ) -> PolynomialCreationResult:
        parameters = frozenset(declared_parameter_names)
        self._validate_names(variable_name, parameters)
        if len(parameters) > self._limits.max_parameters:
            self._fail(
                DiagnosticCode.POLYNOMIAL_PARAMETER_LIMIT_EXCEEDED,
                "Es wurden zu viele Parameter deklariert.",
                (("limit", "max_parameters"),),
            )

        source = expression._as_sympy()
        if not isinstance(source, sp.Expr):
            self._fail(
                DiagnosticCode.POLYNOMIAL_NOT_POLYNOMIAL,
                "Der interne Ausdruck ist kein skalarer SymPy-Ausdruck.",
            )
        if _node_count(source, self._limits.max_expression_nodes) > (
            self._limits.max_expression_nodes
        ):
            self._fail(
                DiagnosticCode.POLYNOMIAL_COMPLEXITY_LIMIT_EXCEEDED,
                "Der Ausdruck enthält zu viele interne Knoten.",
                (("limit", "max_expression_nodes"),),
            )
        if source.has(sp.Float):
            self._fail(
                DiagnosticCode.POLYNOMIAL_FLOAT_NOT_ALLOWED,
                "Polynome dürfen keine binären Float-Atome enthalten.",
            )

        symbols = _validate_symbols(source)
        names = frozenset(symbols)
        allowed_names = parameters | {variable_name}
        undeclared = sorted(names - allowed_names)
        if undeclared:
            self._fail(
                DiagnosticCode.POLYNOMIAL_UNDECLARED_SYMBOL,
                "Der Ausdruck enthält nicht deklarierte Symbole.",
                tuple(("symbol", name) for name in undeclared),
            )

        variable = symbols.get(variable_name, sp.Symbol(variable_name))
        if source.atoms(sp.Function):
            self._fail(
                DiagnosticCode.POLYNOMIAL_NOT_POLYNOMIAL,
                "Funktionen sind in Polynomen und Koeffizienten nicht erlaubt.",
            )

        estimated_degree = self._estimate_degree(source, variable)
        if estimated_degree > self._limits.max_degree:
            self._fail(
                DiagnosticCode.POLYNOMIAL_DEGREE_LIMIT_EXCEEDED,
                "Der strukturell geschätzte Polynomgrad ist zu hoch.",
                (("limit", "max_degree"),),
            )
        if estimated_degree + 1 > self._limits.max_coefficients:
            self._fail(
                DiagnosticCode.POLYNOMIAL_COEFFICIENT_LIMIT_EXCEEDED,
                "Das Polynom würde zu viele dichte Koeffizienten benötigen.",
                (("limit", "max_coefficients"),),
            )

        used_parameter_names = names - {variable_name}
        parameter_symbols = tuple(
            sp.Symbol(name) for name in sorted(used_parameter_names)
        )
        coefficient_domain = (
            sp.QQ
            if not parameter_symbols
            else sp.QQ.frac_field(*parameter_symbols)
        )
        polynomial = sp.Poly(source, variable, domain=coefficient_domain)
        canonical_source = polynomial.as_expr()
        canonical_used_parameter_names = frozenset(
            symbol.name
            for symbol in canonical_source.free_symbols
            if symbol.name != variable_name
        )
        if canonical_used_parameter_names != used_parameter_names:
            canonical_parameter_symbols = tuple(
                sp.Symbol(name)
                for name in sorted(canonical_used_parameter_names)
            )
            coefficient_domain = (
                sp.QQ
                if not canonical_parameter_symbols
                else sp.QQ.frac_field(*canonical_parameter_symbols)
            )
            polynomial = sp.Poly(
                canonical_source,
                variable,
                domain=coefficient_domain,
            )

        generic_degree = _generic_degree(polynomial)
        if (
            generic_degree is not None
            and generic_degree > self._limits.max_degree
        ):
            self._fail(
                DiagnosticCode.POLYNOMIAL_DEGREE_LIMIT_EXCEEDED,
                "Der kanonische Polynomgrad ist zu hoch.",
                (("limit", "max_degree"),),
            )

        coefficient_values = tuple(
            coefficient_domain.to_sympy(value)
            for value in polynomial.all_coeffs()
        )
        if len(coefficient_values) > self._limits.max_coefficients:
            self._fail(
                DiagnosticCode.POLYNOMIAL_COEFFICIENT_LIMIT_EXCEEDED,
                "Das Polynom benötigt zu viele dichte Koeffizienten.",
                (("limit", "max_coefficients"),),
            )

        structural_term_count = (
            0 if generic_degree is None else len(polynomial.terms())
        )
        if structural_term_count > self._limits.max_structural_terms:
            self._fail(
                DiagnosticCode.POLYNOMIAL_TERM_LIMIT_EXCEEDED,
                "Das Polynom enthält zu viele strukturelle Terme.",
                (("limit", "max_structural_terms"),),
            )

        for coefficient in coefficient_values:
            operations = int(sp.count_ops(coefficient, visual=False))
            if operations > self._limits.max_coefficient_operations:
                self._fail(
                    DiagnosticCode.POLYNOMIAL_COMPLEXITY_LIMIT_EXCEEDED,
                    "Ein Koeffizient ist symbolisch zu komplex.",
                    (("limit", "max_coefficient_operations"),),
                )

        definitions = _definition_conditions(coefficient_values)
        degree_info = _degree_info(generic_degree, coefficient_values[0])
        conditions = _sorted_conditions((*definitions, *degree_info.conditions))
        diagnostics = _condition_diagnostics(conditions, field)

        exact_coefficients = tuple(
            ExactExpression._from_sympy(value)
            for value in coefficient_values
        )
        canonical_expression = ExactExpression._from_sympy(polynomial.as_expr())
        value = Polynomial._create(
            variable_name=variable_name,
            used_parameter_names=canonical_used_parameter_names,
            expression=canonical_expression,
            coefficients=exact_coefficients,
            degree_info=degree_info,
            structural_term_count=structural_term_count,
            conditions=conditions,
            polynomial=polynomial,
        )
        return PolynomialCreationResult(value=value, diagnostics=diagnostics)

    def _validate_names(
        self,
        variable_name: str,
        parameters: frozenset[str],
    ) -> None:
        if not _is_valid_name(variable_name):
            self._fail(
                DiagnosticCode.POLYNOMIAL_INVALID_VARIABLE,
                "Der Name der Hauptvariable ist ungültig.",
                (("name", variable_name),),
            )
        invalid_parameters = sorted(
            name for name in parameters if not _is_valid_name(name)
        )
        if invalid_parameters:
            self._fail(
                DiagnosticCode.POLYNOMIAL_INVALID_VARIABLE,
                "Mindestens ein Parametername ist ungültig.",
                tuple(("name", name) for name in invalid_parameters),
            )
        if variable_name in parameters:
            self._fail(
                DiagnosticCode.POLYNOMIAL_VARIABLE_CONFLICT,
                "Hauptvariable und Parameter müssen disjunkt sein.",
                (("name", variable_name),),
            )

    def _estimate_degree(self, expression: sp.Expr, variable: sp.Symbol) -> int:
        if not expression.has(variable):
            return 0
        if expression == variable:
            return 1
        if expression.is_Add:
            return max(
                self._estimate_degree(argument, variable)
                for argument in expression.args
            )
        if expression.is_Mul:
            degree = 0
            for argument in expression.args:
                degree += self._estimate_degree(argument, variable)
                if degree > self._limits.max_degree:
                    return degree
            return degree
        if expression.is_Pow:
            base, exponent = expression.as_base_exp()
            if not base.has(variable):
                return 0
            if exponent.free_symbols:
                self._fail(
                    DiagnosticCode.POLYNOMIAL_SYMBOLIC_EXPONENT,
                    "Die Hauptvariable darf keinen symbolischen Exponenten haben.",
                )
            if exponent.is_integer is not True:
                self._fail(
                    DiagnosticCode.POLYNOMIAL_NONINTEGER_EXPONENT,
                    "Die Hauptvariable benötigt einen ganzzahligen Exponenten.",
                )
            integer_exponent = int(exponent)
            if integer_exponent < 0:
                code = (
                    DiagnosticCode.POLYNOMIAL_NEGATIVE_EXPONENT
                    if base == variable
                    else DiagnosticCode.POLYNOMIAL_VARIABLE_IN_DENOMINATOR
                )
                self._fail(
                    code,
                    "Die Hauptvariable darf nicht im Nenner auftreten.",
                )
            base_degree = self._estimate_degree(base, variable)
            return base_degree * integer_exponent

        self._fail(
            DiagnosticCode.POLYNOMIAL_NOT_POLYNOMIAL,
            "Der Ausdruck enthält eine nichtpolynomiale Struktur.",
            (("node", type(expression).__name__),),
        )

    @staticmethod
    def _fail(
        code: DiagnosticCode,
        message: str,
        details: tuple[tuple[str, str], ...] = (),
    ) -> NoReturn:
        raise _PolynomialFailure(code, message, details)

    @staticmethod
    def _failure_result(
        code: DiagnosticCode,
        message: str,
        field: str | None,
        details: tuple[tuple[str, str], ...] = (),
    ) -> PolynomialCreationResult:
        return PolynomialCreationResult(
            value=None,
            diagnostics=(
                Diagnostic(
                    severity=DiagnosticSeverity.ERROR,
                    code=code,
                    message=message,
                    field=field,
                    technical_details=details,
                ),
            ),
        )


def _is_valid_name(name: object) -> bool:
    return (
        isinstance(name, str)
        and name.isidentifier()
        and not iskeyword(name)
        and not name.startswith("__")
        and not name.endswith("__")
    )


def _node_count(expression: sp.Expr, cap: int) -> int:
    count = 0
    for _ in sp.preorder_traversal(expression):
        count += 1
        if count > cap:
            break
    return count


def _validate_symbols(expression: sp.Expr) -> dict[str, sp.Symbol]:
    by_name: dict[str, sp.Symbol] = {}
    for symbol in sorted(
        expression.free_symbols,
        key=lambda item: (item.name, sp.srepr(item)),
    ):
        if type(symbol) is not sp.Symbol:
            raise _PolynomialFailure(
                DiagnosticCode.POLYNOMIAL_SYMBOL_ASSUMPTION_NOT_ALLOWED,
                "Nur kanonische annahmenfreie Symbole sind erlaubt.",
                (("symbol", symbol.name),),
            )
        existing = by_name.get(symbol.name)
        if existing is not None and existing != symbol:
            raise _PolynomialFailure(
                DiagnosticCode.POLYNOMIAL_SYMBOL_ASSUMPTION_NOT_ALLOWED,
                "Mehrere unterschiedliche Symbole verwenden denselben Namen.",
                (("symbol", symbol.name),),
            )
        if symbol.assumptions0 != _ASSUMPTION_FREE_SYMBOL:
            raise _PolynomialFailure(
                DiagnosticCode.POLYNOMIAL_SYMBOL_ASSUMPTION_NOT_ALLOWED,
                "Versteckte SymPy-Symbolannahmen sind nicht erlaubt.",
                (("symbol", symbol.name),),
            )
        by_name[symbol.name] = symbol
    return by_name


def _generic_degree(polynomial: sp.Poly) -> int | None:
    if polynomial.is_zero:
        return None
    return int(polynomial.degree())


def _normalized_fraction(expression: sp.Expr) -> tuple[sp.Expr, sp.Expr]:
    normalized = sp.cancel(expression)
    numerator, denominator = sp.fraction(normalized)
    if denominator.could_extract_minus_sign():
        numerator = -numerator
        denominator = -denominator
    return numerator, denominator


def _symbolic_nonzero_part(expression: sp.Expr) -> sp.Expr:
    _, primitive = expression.as_content_primitive()
    if primitive.could_extract_minus_sign():
        primitive = -primitive
    return primitive


def _definition_conditions(
    coefficients: tuple[sp.Expr, ...],
) -> tuple[PolynomialCondition, ...]:
    conditions: list[PolynomialCondition] = []
    for coefficient in coefficients:
        _, denominator = _normalized_fraction(coefficient)
        symbolic_denominator = _symbolic_nonzero_part(denominator)
        if symbolic_denominator != 1:
            conditions.append(
                PolynomialCondition(
                    PolynomialConditionKind.DEFINITION_NONZERO,
                    ExactExpression._from_sympy(symbolic_denominator),
                )
            )
    return _sorted_conditions(tuple(conditions))


def _degree_info(
    generic_degree: int | None,
    leading_coefficient: sp.Expr,
) -> PolynomialDegreeInfo:
    if generic_degree is None:
        return PolynomialDegreeInfo(None, None)

    numerator, _ = _normalized_fraction(leading_coefficient)
    numerator = _symbolic_nonzero_part(numerator)
    if numerator.is_zero is False:
        return PolynomialDegreeInfo(generic_degree, generic_degree)
    if numerator.is_zero is True:
        raise _PolynomialFailure(
            DiagnosticCode.POLYNOMIAL_NOT_POLYNOMIAL,
            "Der kanonische führende Koeffizient ist unerwartet null.",
        )
    condition = PolynomialCondition(
        PolynomialConditionKind.LEADING_COEFFICIENT_NONZERO,
        ExactExpression._from_sympy(numerator),
    )
    return PolynomialDegreeInfo(
        generic_degree,
        None,
        (condition,),
    )


def _sorted_conditions(
    conditions: tuple[PolynomialCondition, ...],
) -> tuple[PolynomialCondition, ...]:
    unique = {
        (condition.kind.value, condition.expression.canonical_text): condition
        for condition in conditions
    }
    return tuple(unique[key] for key in sorted(unique))


def _condition_diagnostics(
    conditions: tuple[PolynomialCondition, ...],
    field: str | None,
) -> tuple[Diagnostic, ...]:
    diagnostics: list[Diagnostic] = []
    for condition in conditions:
        if condition.kind is PolynomialConditionKind.DEFINITION_NONZERO:
            code = DiagnosticCode.POLYNOMIAL_PARAMETER_DENOMINATOR_NONZERO
            message = "Ein Parameternenner muss ungleich null sein."
        else:
            code = DiagnosticCode.POLYNOMIAL_CONDITIONAL_DEGREE
            message = "Der generische Polynomgrad gilt nur unter einer Bedingung."
        diagnostics.append(
            Diagnostic(
                DiagnosticSeverity.WARNING,
                code,
                message,
                field,
                (("condition", condition.description),),
            )
        )
    return tuple(diagnostics)
