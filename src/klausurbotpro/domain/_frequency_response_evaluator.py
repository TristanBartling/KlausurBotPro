"""Exact bounded evaluation of reduced transfer functions at ``s = I*omega``."""

from __future__ import annotations

import sympy as sp

from klausurbotpro.domain._frequency_response_numeric import (
    FrequencyResponseNumericError,
    FrequencyResponseNumericLimitError,
    numerical_frequency_response,
)
from klausurbotpro.domain._frequency_response_validation import (
    FrequencyResponseFailure,
)
from klausurbotpro.domain.diagnostics import (
    Diagnostic,
    DiagnosticCode,
    DiagnosticSeverity,
)
from klausurbotpro.domain.expression import ExactExpression
from klausurbotpro.domain.frequency_response_contracts import (
    DecibelValueKind,
    FrequencyResponseLimits,
    FrequencyResponsePoint,
    FrequencyResponsePointStatus,
    NumericalDecibelValue,
)
from klausurbotpro.domain.parameter_substitutions import ExactRationalValue
from klausurbotpro.domain.reduced_transfer_function import (
    ReducedTransferFunction,
)


class FrequencyResponseBudget:
    """Bound every exact intermediate expression and their cumulative work."""

    def __init__(self, limits: FrequencyResponseLimits) -> None:
        self._limits = limits
        self.operations = 0

    def add(self, expression: sp.Expr) -> sp.Expr:
        for local, _ in enumerate(sp.preorder_traversal(expression), start=1):
            self.operations += 1
            if local > self._limits.max_expression_nodes:
                raise FrequencyResponseFailure(
                    DiagnosticCode.FREQUENCY_RESPONSE_LIMIT_EXCEEDED,
                    "Ein Zwischenausdruck ist zu komplex.",
                    (("limit", "max_expression_nodes"),),
                )
            if self.operations > self._limits.max_intermediate_operations:
                raise FrequencyResponseFailure(
                    DiagnosticCode.FREQUENCY_RESPONSE_LIMIT_EXCEEDED,
                    "Die Frequenzganganalyse erzeugt zu viele Zwischenoperationen.",
                    (("limit", "max_intermediate_operations"),),
                )
        return expression


def evaluate_frequency_point(
    reduced: ReducedTransferFunction,
    omega: ExactRationalValue,
    mapping: dict[sp.Symbol, sp.Rational],
    *,
    prerequisites_resolved: bool,
    limits: FrequencyResponseLimits,
    budget: FrequencyResponseBudget,
    field: str | None,
) -> FrequencyResponsePoint:
    """Evaluate one point exactly before deriving finite decimal strings."""

    variable = sp.Symbol(reduced.variable_name)
    omega_value = sp.Rational(omega.numerator, omega.denominator)
    frequency_value = sp.I * omega_value
    numerator = _specialize(
        reduced.numerator.expression._as_sympy(),
        mapping,
        variable,
        frequency_value,
        budget,
    )
    denominator = _specialize(
        reduced.denominator.expression._as_sympy(),
        mapping,
        variable,
        frequency_value,
        budget,
    )
    numerator_value = ExactExpression._from_sympy(numerator)
    denominator_value = ExactExpression._from_sympy(denominator)

    exclusions_resolved, excluded = _domain_status(
        reduced,
        mapping,
        variable,
        frequency_value,
        budget,
    )
    denominator_zero = _exact_zero_truth(denominator)
    if excluded or denominator_zero is True:
        diagnostic = _point_diagnostic(
            DiagnosticSeverity.WARNING,
            DiagnosticCode.FREQUENCY_RESPONSE_SINGULAR,
            "Der Frequenzgang ist an dieser Frequenz singulär.",
            omega,
            field,
        )
        return FrequencyResponsePoint._create(
            omega=omega,
            status=FrequencyResponsePointStatus.SINGULAR,
            specialized_numerator=numerator_value,
            specialized_denominator=denominator_value,
            diagnostics=(diagnostic,),
        )
    if (
        not prerequisites_resolved
        or not exclusions_resolved
        or denominator_zero is None
        or numerator.free_symbols
        or denominator.free_symbols
    ):
        return _symbolic_point(
            omega,
            numerator_value,
            denominator_value,
            field,
        )

    response = budget.add(sp.cancel(numerator / denominator))
    if response.free_symbols:
        return _symbolic_point(
            omega,
            numerator_value,
            denominator_value,
            field,
        )
    expanded = budget.add(sp.expand_complex(response))
    real, imaginary = expanded.as_real_imag()
    real = budget.add(sp.cancel(real))
    imaginary = budget.add(sp.cancel(imaginary))
    magnitude_squared = budget.add(sp.cancel(real**2 + imaginary**2))
    response_value = ExactExpression._from_sympy(response)
    real_value = ExactExpression._from_sympy(real)
    imaginary_value = ExactExpression._from_sympy(imaginary)
    magnitude_squared_value = ExactExpression._from_sympy(magnitude_squared)

    response_zero = _exact_zero_truth(response)
    if response_zero is True:
        diagnostic = _point_diagnostic(
            DiagnosticSeverity.INFO,
            DiagnosticCode.FREQUENCY_RESPONSE_ZERO_RESPONSE,
            "Der Frequenzgang ist an dieser Frequenz exakt null.",
            omega,
            field,
        )
        return FrequencyResponsePoint._create(
            omega=omega,
            status=FrequencyResponsePointStatus.ZERO_RESPONSE,
            specialized_numerator=numerator_value,
            specialized_denominator=denominator_value,
            exact_complex_value=response_value,
            exact_real_part=real_value,
            exact_imaginary_part=imaginary_value,
            exact_magnitude_squared=magnitude_squared_value,
            numerical_real="0",
            numerical_imaginary="0",
            numerical_magnitude="0",
            numerical_decibel=NumericalDecibelValue(
                DecibelValueKind.NEGATIVE_INFINITY
            ),
            diagnostics=(diagnostic,),
        )
    if response_zero is None:
        return _symbolic_point(
            omega,
            numerator_value,
            denominator_value,
            field,
        )

    try:
        (
            numerical_real,
            numerical_imaginary,
            numerical_magnitude,
            numerical_decibel,
            numerical_phase,
        ) = numerical_frequency_response(
            real,
            imaginary,
            magnitude_squared,
            limits,
        )
    except FrequencyResponseNumericLimitError as error:
        raise FrequencyResponseFailure(
            DiagnosticCode.FREQUENCY_RESPONSE_LIMIT_EXCEEDED,
            "Die numerische Darstellung überschreitet den Exponentenbereich.",
            (("limit", "max_numeric_exponent_abs"),),
        ) from error
    except FrequencyResponseNumericError:
        diagnostic = _point_diagnostic(
            DiagnosticSeverity.WARNING,
            DiagnosticCode.FREQUENCY_RESPONSE_NUMERIC_UNDETERMINED,
            "Die exakten Werte liegen vor, die numerische Darstellung ist unbestimmt.",
            omega,
            field,
        )
        return FrequencyResponsePoint._create(
            omega=omega,
            status=FrequencyResponsePointStatus.NUMERIC_UNDETERMINED,
            specialized_numerator=numerator_value,
            specialized_denominator=denominator_value,
            exact_complex_value=response_value,
            exact_real_part=real_value,
            exact_imaginary_part=imaginary_value,
            exact_magnitude_squared=magnitude_squared_value,
            diagnostics=(diagnostic,),
        )
    return FrequencyResponsePoint._create(
        omega=omega,
        status=FrequencyResponsePointStatus.DEFINED,
        specialized_numerator=numerator_value,
        specialized_denominator=denominator_value,
        exact_complex_value=response_value,
        exact_real_part=real_value,
        exact_imaginary_part=imaginary_value,
        exact_magnitude_squared=magnitude_squared_value,
        numerical_real=numerical_real,
        numerical_imaginary=numerical_imaginary,
        numerical_magnitude=numerical_magnitude,
        numerical_decibel=numerical_decibel,
        numerical_phase_degrees=numerical_phase,
    )


def _specialize(
    expression: sp.Expr,
    mapping: dict[sp.Symbol, sp.Rational],
    variable: sp.Symbol,
    frequency_value: sp.Expr,
    budget: FrequencyResponseBudget,
) -> sp.Expr:
    budget.add(expression)
    substituted = budget.add(expression.subs(mapping))
    return budget.add(sp.cancel(substituted.subs(variable, frequency_value)))


def _domain_status(
    reduced: ReducedTransferFunction,
    mapping: dict[sp.Symbol, sp.Rational],
    variable: sp.Symbol,
    frequency_value: sp.Expr,
    budget: FrequencyResponseBudget,
) -> tuple[bool, bool]:
    resolved = True
    for exclusion in reduced.domain_exclusions:
        value = _specialize(
            exclusion.polynomial.expression._as_sympy(),
            mapping,
            variable,
            frequency_value,
            budget,
        )
        truth = _exact_zero_truth(value)
        if truth is True:
            return True, True
        if truth is None:
            resolved = False
    return resolved, False


def _symbolic_point(
    omega: ExactRationalValue,
    numerator: ExactExpression,
    denominator: ExactExpression,
    field: str | None,
) -> FrequencyResponsePoint:
    diagnostic = _point_diagnostic(
        DiagnosticSeverity.WARNING,
        DiagnosticCode.FREQUENCY_RESPONSE_SYMBOLIC_UNDETERMINED,
        "Der Frequenzpunkt ist mit den vorliegenden exakten Angaben nicht "
        "eindeutig bestimmbar.",
        omega,
        field,
    )
    return FrequencyResponsePoint._create(
        omega=omega,
        status=FrequencyResponsePointStatus.SYMBOLIC_UNDETERMINED,
        specialized_numerator=numerator,
        specialized_denominator=denominator,
        diagnostics=(diagnostic,),
    )


def _point_diagnostic(
    severity: DiagnosticSeverity,
    code: DiagnosticCode,
    message: str,
    omega: ExactRationalValue,
    field: str | None,
) -> Diagnostic:
    text = (
        str(omega.numerator)
        if omega.denominator == 1
        else f"{omega.numerator}/{omega.denominator}"
    )
    return Diagnostic(
        severity,
        code,
        message,
        field,
        (("omega", text),),
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


__all__ = ["FrequencyResponseBudget", "evaluate_frequency_point"]
