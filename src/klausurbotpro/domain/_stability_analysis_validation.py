"""Defensive validation of Phase-2A values consumed by stability analysis."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from math import gcd

import sympy as sp
from sympy.polys.polyerrors import BasePolynomialError

from klausurbotpro.domain._exact_polynomial_root_solver import (
    exact_root_as_sympy,
)
from klausurbotpro.domain._root_analysis_validation import (
    RootAnalysisFailure,
    specialize_polynomial,
    validate_reduced_transfer_function,
    validate_substitutions,
)
from klausurbotpro.domain.diagnostics import (
    Diagnostic,
    DiagnosticCode,
    DiagnosticSeverity,
)
from klausurbotpro.domain.expression import ExactExpression
from klausurbotpro.domain.root_analysis_contracts import (
    ConjugateStatus,
    ExplicitExactRootValue,
    NumericalRootEstimate,
    NumericalRootWarning,
    PolynomialRootAnalysis,
    PolynomialRootStatus,
    RootAnalysisGroup,
    RootAnalysisLimits,
    RootOccurrence,
    RootOfValue,
    RootSource,
    TransferFunctionRootAnalysisResult,
)
from klausurbotpro.domain.stability_analysis_contracts import (
    StabilityAnalysisLimits,
)


class StabilityValidationError(ValueError):
    """A manipulated or inconsistent Phase-2A value was detected."""


class StabilityLimitError(ValueError):
    """A configured stability-analysis limit was exceeded."""


def validate_root_analysis(
    root_analysis: TransferFunctionRootAnalysisResult,
    limits: StabilityAnalysisLimits,
) -> int:
    """Revalidate every consumed structural invariant independently."""

    if type(root_analysis) is not TransferFunctionRootAnalysisResult:
        raise TypeError(
            "root_analysis must be TransferFunctionRootAnalysisResult."
        )
    if not _valid_diagnostics(root_analysis.diagnostics):
        raise StabilityValidationError("Invalid root-analysis diagnostics.")
    if not root_analysis.succeeded:
        raise StabilityValidationError("Root analysis did not succeed.")
    reduced = root_analysis.reduced_transfer_function
    zeros = root_analysis.reduced_zeros
    poles = root_analysis.reduced_poles
    if reduced is None or zeros is None or poles is None:
        raise StabilityValidationError("Successful root analysis is incomplete.")

    root_limits = _derived_root_limits(limits)
    try:
        validate_reduced_transfer_function(reduced, root_limits)
        normalized, mapping = validate_substitutions(
            reduced,
            root_analysis.substitutions,
            root_limits,
        )
        expected_denominator = (
            reduced.denominator
            if mapping is None
            else specialize_polynomial(
                reduced.denominator,
                mapping,
                root_limits,
            )
        )
    except RootAnalysisFailure as error:
        if error.code is DiagnosticCode.ROOT_ANALYSIS_LIMIT_EXCEEDED:
            limit_name = (
                error.details[0][1]
                if error.details and error.details[0][0] == "limit"
                else "phase_2a_revalidation"
            )
            raise StabilityLimitError(limit_name) from error
        raise StabilityValidationError(
            "Reduced value or substitutions are invalid."
        ) from error
    except (AttributeError, IndexError, TypeError, ValueError) as error:
        raise StabilityValidationError(
            "Reduced value or substitutions are invalid."
        ) from error
    if normalized != root_analysis.substitutions:
        raise StabilityValidationError("Substitutions are not canonical.")

    _validate_analysis(zeros, RootSource.NUMERATOR, limits)
    _validate_analysis(poles, RootSource.DENOMINATOR, limits)
    if poles.status not in (
        PolynomialRootStatus.COMPLETE,
        PolynomialRootStatus.CONSTANT_NONZERO,
        PolynomialRootStatus.SYMBOLIC_UNDETERMINED,
    ):
        raise StabilityValidationError("Reduced-pole status is invalid.")
    _validate_group(
        root_analysis.retained_domain_exclusions,
        RootSource.DOMAIN_EXCLUSION,
        limits,
        allow_not_evaluated=False,
    )
    _validate_group(
        root_analysis.cancelled_locations,
        RootSource.CANCELLED_FACTOR,
        limits,
        allow_not_evaluated=True,
    )

    pole_count = sum(item.multiplicity for item in poles.roots)
    cancelled_count = sum(
        item.multiplicity
        for analysis in root_analysis.cancelled_locations.analyses
        for item in analysis.roots
    )
    if pole_count > limits.max_poles:
        raise StabilityLimitError("max_poles")
    if cancelled_count > limits.max_cancelled_locations:
        raise StabilityLimitError("max_cancelled_locations")
    try:
        return _validate_reduced_pole_mathematics(
            poles,
            expected_denominator,
            original_degree=reduced.denominator.degree_info.generic_degree,
            denominator_remains_symbolic=(
                mapping is None
                and bool(reduced.denominator.used_parameter_names)
            ),
            limits=limits,
        )
    except (StabilityLimitError, StabilityValidationError):
        raise
    except (
        AttributeError,
        IndexError,
        ArithmeticError,
        TypeError,
        ValueError,
        BasePolynomialError,
        sp.SympifyError,
    ) as error:
        raise StabilityValidationError(
            "The reduced-pole mathematics cannot be verified exactly."
        ) from error


def _derived_root_limits(
    limits: StabilityAnalysisLimits,
) -> RootAnalysisLimits:
    """Map stability limits without imposing unrelated Phase-2A defaults."""

    return RootAnalysisLimits(
        max_polynomial_degree=limits.max_source_polynomial_degree,
        max_parameters=limits.max_expression_nodes,
        max_expression_nodes=limits.max_expression_nodes,
        max_exact_rootof_count=limits.max_poles,
        max_results=limits.max_result_items,
        max_factor_nodes=limits.max_expression_nodes,
        max_substitution_nodes=limits.max_expression_nodes,
        max_substitution_integer_digits=(
            limits.max_substitution_integer_digits
        ),
        max_domain_exclusions=limits.max_result_items,
        max_cancelled_factors=limits.max_cancelled_locations,
    )


def _validate_reduced_pole_mathematics(
    poles: PolynomialRootAnalysis,
    expected_denominator: object,
    *,
    original_degree: int | None,
    denominator_remains_symbolic: bool,
    limits: StabilityAnalysisLimits,
) -> int:
    """Prove source, roots, multiplicities, and distinctness exactly."""

    expression = getattr(expected_denominator, "expression", None)
    as_poly = getattr(expected_denominator, "_as_sympy_poly", None)
    if type(expression) is not ExactExpression or not callable(as_poly):
        raise StabilityValidationError("Expected denominator is invalid.")
    if poles.source_expression != expression:
        raise StabilityValidationError(
            "Reduced-pole source does not match the expected denominator."
        )
    if poles.original_degree != original_degree:
        raise StabilityValidationError(
            "Reduced-pole original degree does not match the denominator."
        )
    if denominator_remains_symbolic:
        if (
            poles.status is not PolynomialRootStatus.SYMBOLIC_UNDETERMINED
            or poles.roots
            or poles.numerical_estimates
        ):
            raise StabilityValidationError(
                "A parameter-dependent denominator must remain undetermined."
            )
        return expression_node_count(expression, limits)

    polynomial = as_poly()
    if not isinstance(polynomial, sp.Poly) or polynomial.is_zero:
        raise StabilityValidationError(
            "The specialized denominator must be nonzero."
        )
    degree = int(polynomial.degree())
    if degree > limits.max_source_polynomial_degree:
        raise StabilityLimitError("max_source_polynomial_degree")
    for coefficient in polynomial.all_coeffs():
        numerator, denominator = coefficient.as_numer_denom()
        if (
            _integer_exceeds_digits(
                int(numerator),
                limits.max_source_integer_digits,
            )
            or _integer_exceeds_digits(
                int(denominator),
                limits.max_source_integer_digits,
            )
        ):
            raise StabilityLimitError("max_source_integer_digits")
    if degree == 0:
        if (
            poles.status is not PolynomialRootStatus.CONSTANT_NONZERO
            or poles.actual_degree != 0
            or poles.roots
        ):
            raise StabilityValidationError(
                "A constant denominator requires a constant root result."
            )
        return expression_node_count(expression, limits)
    if (
        poles.status is not PolynomialRootStatus.COMPLETE
        or poles.actual_degree != degree
        or sum(item.multiplicity for item in poles.roots) != degree
    ):
        raise StabilityValidationError(
            "A positive-degree denominator requires complete exact poles."
        )

    budget = _EvidenceBudget(limits)
    polynomial_expression = polynomial.as_expr()
    budget.add(polynomial_expression)
    variable = polynomial.gens[0]
    maximum_multiplicity = max(item.multiplicity for item in poles.roots)
    derivatives = [polynomial_expression]
    for _ in range(maximum_multiplicity):
        derivatives.append(sp.diff(derivatives[-1], variable))
        budget.add(derivatives[-1])

    exact_roots: list[sp.Expr] = []
    for occurrence in poles.roots:
        root = exact_root_as_sympy(occurrence.value)
        budget.add(root)
        exact_roots.append(root)
        for order in range(occurrence.multiplicity):
            if (
                _derivative_zero_truth(
                    derivatives[order],
                    variable,
                    occurrence.value,
                    root,
                    budget,
                )
                is not True
            ):
                raise StabilityValidationError(
                    "A reported pole or multiplicity is mathematically false."
                )
        if (
            _derivative_zero_truth(
                derivatives[occurrence.multiplicity],
                variable,
                occurrence.value,
                root,
                budget,
            )
            is not False
        ):
            raise StabilityValidationError(
                "A reported pole multiplicity is not exact."
            )

    for left_index, left in enumerate(exact_roots):
        left_value = poles.roots[left_index].value
        for right_index, right in enumerate(
            exact_roots[left_index + 1 :],
            start=left_index + 1,
        ):
            right_value = poles.roots[right_index].value
            if (
                type(left_value) is RootOfValue
                and type(right_value) is RootOfValue
            ):
                if left_value == right_value:
                    raise StabilityValidationError(
                        "Distinct root entries represent the same algebraic root."
                    )
                if (
                    left_value.defining_coefficients
                    == right_value.defining_coefficients
                ):
                    continue
                left_polynomial = _rootof_polynomial(left_value, variable)
                right_polynomial = _rootof_polynomial(right_value, variable)
                if left_polynomial != right_polynomial:
                    continue
            difference = sp.cancel(left - right)
            budget.add(difference)
            if _exact_zero_truth(difference) is not False:
                raise StabilityValidationError(
                    "Distinct root entries represent the same algebraic root."
                )
    return budget.count


def _derivative_zero_truth(
    derivative: sp.Expr,
    variable: sp.Symbol,
    value: ExplicitExactRootValue | RootOfValue,
    root: sp.Expr,
    budget: _EvidenceBudget,
) -> bool | None:
    if type(value) is RootOfValue:
        defining = _rootof_polynomial(value, variable)
        remainder = sp.Poly(
            derivative,
            variable,
            domain=sp.QQ,
        ).rem(defining)
        budget.add(remainder.as_expr())
        return bool(remainder.is_zero)
    evaluated = sp.cancel(derivative.subs(variable, root))
    budget.add(evaluated)
    return _exact_zero_truth(evaluated)


def _rootof_polynomial(
    value: RootOfValue,
    variable: sp.Symbol,
) -> sp.Poly:
    return sp.Poly.from_list(
        value.defining_coefficients,
        gens=variable,
        domain=sp.QQ,
    )


def _exact_zero_truth(expression: sp.Expr) -> bool | None:
    """Return only an exact zero decision, never a tolerance decision."""

    if expression.is_zero is True:
        return True
    if expression.is_zero is False:
        return False
    equals_zero = expression.equals(sp.Integer(0))
    return equals_zero if type(equals_zero) is bool else None


class _EvidenceBudget:
    """Count exact algebraic evidence under both configured node limits."""

    def __init__(self, limits: StabilityAnalysisLimits) -> None:
        self._limits = limits
        self.count = 0

    def add(self, expression: sp.Expr) -> None:
        for local_count, _ in enumerate(
            sp.preorder_traversal(expression),
            start=1,
        ):
            self.count += 1
            if local_count > self._limits.max_expression_nodes:
                raise StabilityLimitError("max_expression_nodes")
            if self.count > self._limits.max_evidence_nodes:
                raise StabilityLimitError("max_evidence_nodes")


def expression_node_count(
    expression: ExactExpression,
    limits: StabilityAnalysisLimits,
) -> int:
    """Count trusted expression nodes under the configured bound."""

    if type(expression) is not ExactExpression:
        raise StabilityValidationError("Expected an exact expression.")
    count = 0
    for _ in sp.preorder_traversal(expression._as_sympy()):
        count += 1
        if count > limits.max_expression_nodes:
            raise StabilityLimitError("max_expression_nodes")
    return count


def _validate_group(
    group: RootAnalysisGroup,
    source: RootSource,
    limits: StabilityAnalysisLimits,
    *,
    allow_not_evaluated: bool,
) -> None:
    if type(group) is not RootAnalysisGroup or type(group.analyses) is not tuple:
        raise StabilityValidationError("Invalid root-analysis group.")
    if any(type(item) is not PolynomialRootAnalysis for item in group.analyses):
        raise StabilityValidationError("Invalid root-analysis group member.")
    if group.status is PolynomialRootStatus.NOT_EVALUATED:
        if not allow_not_evaluated or group.analyses:
            raise StabilityValidationError("Invalid not-evaluated group.")
        return
    for analysis in group.analyses:
        _validate_analysis(analysis, source, limits)
        if analysis.status not in (
            PolynomialRootStatus.COMPLETE,
            PolynomialRootStatus.CONSTANT_NONZERO,
            PolynomialRootStatus.SYMBOLIC_UNDETERMINED,
        ):
            raise StabilityValidationError("Invalid grouped analysis status.")
    expected = (
        PolynomialRootStatus.SYMBOLIC_UNDETERMINED
        if any(
            item.status is PolynomialRootStatus.SYMBOLIC_UNDETERMINED
            for item in group.analyses
        )
        else PolynomialRootStatus.COMPLETE
    )
    if group.status is not expected:
        raise StabilityValidationError("Root group status is inconsistent.")


def _validate_analysis(
    analysis: PolynomialRootAnalysis,
    source: RootSource,
    limits: StabilityAnalysisLimits,
) -> None:
    if type(analysis) is not PolynomialRootAnalysis:
        raise StabilityValidationError("Invalid polynomial root analysis.")
    if (
        type(analysis.status) is not PolynomialRootStatus
        or analysis.source is not source
        or type(analysis.source_expression) is not ExactExpression
        or type(analysis.roots) is not tuple
        or type(analysis.numerical_estimates) is not tuple
        or type(analysis.origins) is not tuple
    ):
        raise StabilityValidationError("Root-analysis source or containers invalid.")
    for degree in (analysis.original_degree, analysis.actual_degree):
        if degree is not None and (
            isinstance(degree, bool)
            or not isinstance(degree, int)
            or degree < 0
        ):
            raise StabilityValidationError("Invalid polynomial degree.")
    expression_node_count(analysis.source_expression, limits)
    if any(type(origin) is not str or not origin for origin in analysis.origins):
        raise StabilityValidationError("Invalid root-analysis origin.")
    if analysis.origins != tuple(sorted(set(analysis.origins))):
        raise StabilityValidationError("Root-analysis origins are not canonical.")
    if any(type(item) is not RootOccurrence for item in analysis.roots):
        raise StabilityValidationError("Invalid root occurrence.")
    if tuple(item.index for item in analysis.roots) != tuple(
        range(len(analysis.roots))
    ):
        raise StabilityValidationError("Root indices are not contiguous.")
    for item in analysis.roots:
        _validate_occurrence(item, source, limits)
    if analysis.status is PolynomialRootStatus.COMPLETE:
        if (
            analysis.actual_degree is None
            or analysis.actual_degree <= 0
            or sum(item.multiplicity for item in analysis.roots)
            != analysis.actual_degree
            or (
                analysis.original_degree is not None
                and analysis.actual_degree > analysis.original_degree
            )
        ):
            raise StabilityValidationError("Complete root list is incomplete.")
    elif analysis.roots or analysis.numerical_estimates:
        raise StabilityValidationError("Non-complete analysis contains roots.")
    elif (
        analysis.status is PolynomialRootStatus.CONSTANT_NONZERO
        and analysis.actual_degree != 0
    ):
        raise StabilityValidationError("Constant analysis requires degree zero.")
    elif (
        analysis.status
        in (
            PolynomialRootStatus.ZERO_POLYNOMIAL,
            PolynomialRootStatus.SYMBOLIC_UNDETERMINED,
            PolynomialRootStatus.NOT_EVALUATED,
        )
        and analysis.actual_degree is not None
    ):
        raise StabilityValidationError(
            "An unevaluated degree must not be invented."
        )
    if analysis.numerical_estimates:
        if len(analysis.numerical_estimates) != len(analysis.roots):
            raise StabilityValidationError("Numerical estimates are incomplete.")
        for estimate, root in zip(
            analysis.numerical_estimates, analysis.roots, strict=True
        ):
            _validate_estimate(estimate, root.index)


def _validate_occurrence(
    item: RootOccurrence,
    source: RootSource,
    limits: StabilityAnalysisLimits,
) -> None:
    if (
        item.source is not source
        or isinstance(item.multiplicity, bool)
        or not isinstance(item.multiplicity, int)
        or item.multiplicity <= 0
        or isinstance(item.index, bool)
        or not isinstance(item.index, int)
        or item.index < 0
    ):
        raise StabilityValidationError("Invalid root occurrence fields.")
    if type(item.value) is ExplicitExactRootValue:
        if (
            type(item.value.expression) is not ExactExpression
            or item.value.expression.symbol_names
        ):
            raise StabilityValidationError("Invalid explicit exact root.")
    elif type(item.value) is RootOfValue:
        coefficients = item.value.defining_coefficients
        common = 0
        if type(coefficients) is tuple:
            for coefficient in coefficients:
                if isinstance(coefficient, int) and not isinstance(
                    coefficient, bool
                ):
                    common = gcd(common, abs(coefficient))
        if (
            type(coefficients) is not tuple
            or len(coefficients) < 2
            or len(coefficients) - 1
            > limits.max_source_polynomial_degree
            or any(
                isinstance(value, bool) or not isinstance(value, int)
                for value in coefficients
            )
            or coefficients[0] <= 0
            or common != 1
            or isinstance(item.value.root_index, bool)
            or not isinstance(item.value.root_index, int)
            or not 0 <= item.value.root_index < len(coefficients) - 1
        ):
            raise StabilityValidationError("Invalid RootOf value.")
        if any(
            _integer_exceeds_digits(
                coefficient,
                limits.max_source_integer_digits,
            )
            for coefficient in coefficients
        ):
            raise StabilityLimitError("max_source_integer_digits")
        try:
            defining = _rootof_polynomial(
                item.value,
                sp.Symbol("_stability_root"),
            )
            if defining.is_irreducible is not True:
                raise StabilityValidationError(
                    "RootOf defining polynomial must be irreducible."
                )
            exact_root_as_sympy(item.value)
        except (
            AttributeError,
            IndexError,
            ArithmeticError,
            NotImplementedError,
            TypeError,
            ValueError,
            BasePolynomialError,
            sp.SympifyError,
        ) as error:
            raise StabilityValidationError(
                "RootOf value cannot be reconstructed."
            ) from error
    else:
        raise StabilityValidationError("Unsupported exact root value.")


def _validate_estimate(estimate: NumericalRootEstimate, index: int) -> None:
    if (
        type(estimate) is not NumericalRootEstimate
        or estimate.root_index != index
        or isinstance(estimate.precision_digits, bool)
        or not isinstance(estimate.precision_digits, int)
        or estimate.precision_digits < 2
        or type(estimate.conjugate_status) is not ConjugateStatus
        or type(estimate.warnings) is not tuple
        or any(type(item) is not NumericalRootWarning for item in estimate.warnings)
        or len(set(estimate.warnings)) != len(estimate.warnings)
    ):
        raise StabilityValidationError("Invalid numerical estimate.")
    for text in (
        estimate.real,
        estimate.imaginary,
        estimate.absolute_residual,
        estimate.scaled_residual,
    ):
        if type(text) is not str:
            raise StabilityValidationError("Invalid numerical estimate text.")
        try:
            value = Decimal(text)
        except (InvalidOperation, ValueError) as error:
            raise StabilityValidationError("Invalid numerical estimate.") from error
        if not value.is_finite():
            raise StabilityValidationError("Non-finite numerical estimate.")


def _valid_diagnostics(diagnostics: object) -> bool:
    if type(diagnostics) is not tuple:
        return False
    for item in diagnostics:
        if (
            type(item) is not Diagnostic
            or type(item.severity) is not DiagnosticSeverity
            or type(item.code) is not DiagnosticCode
            or type(item.message) is not str
            or not item.message.strip()
            or (item.field is not None and type(item.field) is not str)
            or type(item.technical_details) is not tuple
            or any(
                type(pair) is not tuple
                or len(pair) != 2
                or any(type(value) is not str for value in pair)
                for pair in item.technical_details
            )
        ):
            return False
    return True


def _integer_exceeds_digits(value: int, maximum_digits: int) -> bool:
    magnitude = value if value >= 0 else -value
    if magnitude == 0 or magnitude.bit_length() <= maximum_digits:
        return False
    return bool(magnitude >= pow(10, maximum_digits))


__all__ = [
    "StabilityLimitError",
    "StabilityValidationError",
    "expression_node_count",
    "validate_root_analysis",
]
