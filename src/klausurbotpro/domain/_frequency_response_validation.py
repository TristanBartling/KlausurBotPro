"""Defensive validation for exact pointwise frequency-response analysis."""

from __future__ import annotations

from dataclasses import dataclass
from keyword import iskeyword
from math import gcd

import sympy as sp

from klausurbotpro.domain._root_analysis_validation import (
    RootAnalysisFailure,
    validate_reduced_transfer_function,
)
from klausurbotpro.domain.diagnostics import DiagnosticCode
from klausurbotpro.domain.expression import ExactExpression
from klausurbotpro.domain.frequency_response_contracts import (
    FrequencyResponseLimits,
    FrequencySampleSet,
)
from klausurbotpro.domain.parameter_substitutions import (
    ExactRationalValue,
    ParameterAssignment,
    ParameterSubstitutions,
)
from klausurbotpro.domain.raw_transfer_function_contracts import (
    TransferFunctionPrerequisiteKind,
)
from klausurbotpro.domain.reduced_transfer_function import (
    ReducedTransferFunction,
)
from klausurbotpro.domain.root_analysis_contracts import RootAnalysisLimits


@dataclass(frozen=True, slots=True)
class FrequencyResponseFailure(ValueError):
    """Expected validation or bounded-analysis failure."""

    code: DiagnosticCode
    message: str
    details: tuple[tuple[str, str], ...] = ()


def validate_frequency_response_context(
    reduced: ReducedTransferFunction,
    frequencies: FrequencySampleSet,
    substitutions: ParameterSubstitutions | None,
    limits: FrequencyResponseLimits,
) -> tuple[
    ParameterSubstitutions | None,
    dict[sp.Symbol, sp.Rational],
    bool,
]:
    """Validate all inputs before any point is mathematically evaluated."""

    try:
        _precheck_expression_limits(reduced, limits)
        validate_reduced_transfer_function(reduced, _root_limits(limits))
        validate_frequency_samples(frequencies, limits)
        normalized, mapping = validate_frequency_substitutions(
            reduced,
            substitutions,
            limits,
        )
        prerequisites_resolved = validate_prerequisites_partially(
            reduced,
            mapping,
        )
        return normalized, mapping, prerequisites_resolved
    except FrequencyResponseFailure:
        raise
    except RootAnalysisFailure as error:
        code = (
            DiagnosticCode.FREQUENCY_RESPONSE_LIMIT_EXCEEDED
            if error.code is DiagnosticCode.ROOT_ANALYSIS_LIMIT_EXCEEDED
            else DiagnosticCode.FREQUENCY_RESPONSE_INVALID_INPUT
        )
        details = (
            error.details
            if code is DiagnosticCode.FREQUENCY_RESPONSE_LIMIT_EXCEEDED
            else (("cause", error.code.value),)
        )
        raise FrequencyResponseFailure(
            code,
            (
                "Eine konfigurierte Grenze der Frequenzganganalyse wurde überschritten."
                if code is DiagnosticCode.FREQUENCY_RESPONSE_LIMIT_EXCEEDED
                else "Die reduzierte Übertragungsfunktion ist ungültig."
            ),
            details,
        ) from error
    except (AttributeError, IndexError, TypeError, ValueError) as error:
        raise FrequencyResponseFailure(
            DiagnosticCode.FREQUENCY_RESPONSE_INVALID_INPUT,
            "Die reduzierte Übertragungsfunktion ist ungültig.",
            (("exception", type(error).__name__),),
        ) from error


def _precheck_expression_limits(
    reduced: ReducedTransferFunction,
    limits: FrequencyResponseLimits,
) -> None:
    expressions: list[object] = [
        getattr(getattr(reduced, "numerator", None), "expression", None),
        getattr(getattr(reduced, "denominator", None), "expression", None),
    ]
    prerequisites = getattr(reduced, "prerequisites", ())
    if type(prerequisites) is tuple:
        for prerequisite in prerequisites:
            local = getattr(prerequisite, "expressions", ())
            if type(local) is tuple:
                expressions.extend(local)
    exclusions = getattr(reduced, "domain_exclusions", ())
    if type(exclusions) is tuple:
        expressions.extend(
            getattr(getattr(exclusion, "polynomial", None), "expression", None)
            for exclusion in exclusions
        )
    for expression in expressions:
        if type(expression) is not ExactExpression:
            continue
        count = 0
        for count, _ in enumerate(
            sp.preorder_traversal(expression._as_sympy()),
            start=1,
        ):
            if count > limits.max_expression_nodes:
                raise FrequencyResponseFailure(
                    DiagnosticCode.FREQUENCY_RESPONSE_LIMIT_EXCEEDED,
                    "Ein Eingangsausdruck ist zu komplex.",
                    (("limit", "max_expression_nodes"),),
                )


def validate_frequency_samples(
    frequencies: FrequencySampleSet,
    limits: FrequencyResponseLimits,
) -> None:
    """Validate the complete ordered sample contract before evaluation."""

    values = frequencies.frequencies
    if type(values) is not tuple or any(
        type(value) is not ExactRationalValue for value in values
    ):
        raise FrequencyResponseFailure(
            DiagnosticCode.FREQUENCY_RESPONSE_INVALID_FREQUENCIES,
            "Die Frequenzliste besitzt einen ungültigen Vertrag.",
        )
    if not values:
        raise FrequencyResponseFailure(
            DiagnosticCode.FREQUENCY_RESPONSE_INVALID_FREQUENCIES,
            "Mindestens eine Frequenz ist erforderlich.",
        )
    if len(values) > limits.max_frequency_points:
        raise FrequencyResponseFailure(
            DiagnosticCode.FREQUENCY_RESPONSE_LIMIT_EXCEEDED,
            "Die Frequenzliste enthält zu viele Punkte.",
            (("limit", "max_frequency_points"),),
        )
    previous: ExactRationalValue | None = None
    for value in values:
        _validate_rational(
            value,
            maximum_digits=limits.max_frequency_integer_digits,
            invalid_code=DiagnosticCode.FREQUENCY_RESPONSE_INVALID_FREQUENCIES,
            limit_name="max_frequency_integer_digits",
        )
        if value.numerator < 0:
            raise FrequencyResponseFailure(
                DiagnosticCode.FREQUENCY_RESPONSE_INVALID_FREQUENCIES,
                "Frequenzen müssen nichtnegativ sein.",
            )
        if previous is not None and (
            previous.numerator * value.denominator
            >= value.numerator * previous.denominator
        ):
            raise FrequencyResponseFailure(
                DiagnosticCode.FREQUENCY_RESPONSE_INVALID_FREQUENCIES,
                "Frequenzen müssen streng aufsteigend und eindeutig sein.",
            )
        previous = value


def validate_frequency_substitutions(
    reduced: ReducedTransferFunction,
    substitutions: ParameterSubstitutions | None,
    limits: FrequencyResponseLimits,
) -> tuple[ParameterSubstitutions | None, dict[sp.Symbol, sp.Rational]]:
    """Validate exact complete or partial substitutions without guessing values."""

    if substitutions is None:
        return None, {}
    assignments = substitutions.assignments
    if type(assignments) is not tuple or any(
        type(item) is not ParameterAssignment for item in assignments
    ):
        raise FrequencyResponseFailure(
            DiagnosticCode.FREQUENCY_RESPONSE_INVALID_SUBSTITUTIONS,
            "Die Parametersubstitutionen besitzen einen ungültigen Vertrag.",
        )
    names = tuple(item.parameter_name for item in assignments)
    if (
        names != tuple(sorted(names))
        or len(names) != len(set(names))
        or any(
            type(name) is not str
            or not name.isidentifier()
            or iskeyword(name)
            or name == reduced.variable_name
            for name in names
        )
    ):
        raise FrequencyResponseFailure(
            DiagnosticCode.FREQUENCY_RESPONSE_INVALID_SUBSTITUTIONS,
            "Die Parametersubstitutionen sind nicht kanonisch.",
        )
    unknown = frozenset(names) - reduced.used_parameter_names
    if unknown:
        raise FrequencyResponseFailure(
            DiagnosticCode.FREQUENCY_RESPONSE_INVALID_SUBSTITUTIONS,
            "Eine Parametersubstitution gehört nicht zur Übertragungsfunktion.",
            (("parameter", sorted(unknown)[0]),),
        )
    if len(assignments) > limits.max_parameters:
        raise FrequencyResponseFailure(
            DiagnosticCode.FREQUENCY_RESPONSE_LIMIT_EXCEEDED,
            "Die Parametersubstitution enthält zu viele Werte.",
            (("limit", "max_parameters"),),
        )
    mapping: dict[sp.Symbol, sp.Rational] = {}
    for assignment in assignments:
        value = assignment.value
        if type(value) is not ExactRationalValue:
            raise FrequencyResponseFailure(
                DiagnosticCode.FREQUENCY_RESPONSE_INVALID_SUBSTITUTIONS,
                "Ein Parameterwert ist nicht exakt rational.",
            )
        _validate_rational(
            value,
            maximum_digits=limits.max_substitution_integer_digits,
            invalid_code=DiagnosticCode.FREQUENCY_RESPONSE_INVALID_SUBSTITUTIONS,
            limit_name="max_substitution_integer_digits",
        )
        mapping[sp.Symbol(assignment.parameter_name)] = sp.Rational(
            value.numerator,
            value.denominator,
        )
    return substitutions, mapping


def validate_prerequisites_partially(
    reduced: ReducedTransferFunction,
    mapping: dict[sp.Symbol, sp.Rational],
) -> bool:
    """Reject proven violations and report whether every prerequisite is decided."""

    all_resolved = True
    for prerequisite in reduced.prerequisites:
        values = tuple(
            sp.cancel(expression._as_sympy().subs(mapping))
            for expression in prerequisite.expressions
        )
        truths = tuple(_exact_zero_truth(value) for value in values)
        if prerequisite.kind is TransferFunctionPrerequisiteKind.EXPRESSION_NONZERO:
            truth = truths[0]
            if truth is True:
                raise FrequencyResponseFailure(
                    DiagnosticCode.FREQUENCY_RESPONSE_CONTEXT_MISMATCH,
                    "Eine Voraussetzung der Übertragungsfunktion ist verletzt.",
                    (("prerequisite", prerequisite.description),),
                )
            if truth is None:
                all_resolved = False
        elif prerequisite.kind is TransferFunctionPrerequisiteKind.NOT_ALL_ZERO:
            if any(truth is False for truth in truths):
                continue
            if all(truth is True for truth in truths):
                raise FrequencyResponseFailure(
                    DiagnosticCode.FREQUENCY_RESPONSE_CONTEXT_MISMATCH,
                    "Eine Voraussetzung der Übertragungsfunktion ist verletzt.",
                    (("prerequisite", prerequisite.description),),
                )
            all_resolved = False
        else:
            raise FrequencyResponseFailure(
                DiagnosticCode.FREQUENCY_RESPONSE_INVALID_INPUT,
                "Die reduzierte Übertragungsfunktion enthält eine unbekannte Voraussetzung.",
            )
    return all_resolved


def _root_limits(limits: FrequencyResponseLimits) -> RootAnalysisLimits:
    return RootAnalysisLimits(
        max_polynomial_degree=limits.max_polynomial_degree,
        max_parameters=limits.max_parameters,
        max_expression_nodes=limits.max_expression_nodes,
        max_exact_rootof_count=limits.max_expression_nodes,
        max_results=limits.max_expression_nodes,
        max_factor_nodes=limits.max_expression_nodes,
        max_substitution_nodes=limits.max_expression_nodes,
        max_substitution_integer_digits=limits.max_substitution_integer_digits,
        max_domain_exclusions=limits.max_domain_exclusions,
        max_cancelled_factors=limits.max_domain_exclusions,
    )


def _validate_rational(
    value: ExactRationalValue,
    *,
    maximum_digits: int,
    invalid_code: DiagnosticCode,
    limit_name: str,
) -> None:
    numerator = value.numerator
    denominator = value.denominator
    if (
        isinstance(numerator, bool)
        or not isinstance(numerator, int)
        or isinstance(denominator, bool)
        or not isinstance(denominator, int)
        or denominator <= 0
        or gcd(abs(numerator), denominator) != 1
    ):
        raise FrequencyResponseFailure(
            invalid_code,
            "Ein rationaler Wert ist nicht kanonisch.",
        )
    if _integer_exceeds_digits(numerator, maximum_digits) or _integer_exceeds_digits(
        denominator,
        maximum_digits,
    ):
        raise FrequencyResponseFailure(
            DiagnosticCode.FREQUENCY_RESPONSE_LIMIT_EXCEEDED,
            "Ein rationaler Wert überschreitet die konfigurierte Zifferngrenze.",
            (("limit", limit_name),),
        )


def _exact_zero_truth(expression: sp.Expr) -> bool | None:
    if expression.is_zero is True:
        return True
    if expression.is_zero is False:
        return False
    if expression.free_symbols:
        return None
    equals_zero = expression.equals(sp.Integer(0))
    return equals_zero if type(equals_zero) is bool else None


def _integer_exceeds_digits(value: int, maximum_digits: int) -> bool:
    magnitude = value if value >= 0 else -value
    if magnitude == 0 or magnitude.bit_length() <= maximum_digits:
        return False
    return bool(magnitude >= pow(10, maximum_digits))


__all__ = ["FrequencyResponseFailure", "validate_frequency_response_context"]
