"""Defensive validation of Phase-2A values consumed by stability analysis."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from math import gcd

import sympy as sp

from klausurbotpro.domain._exact_polynomial_root_solver import (
    exact_root_as_sympy,
)
from klausurbotpro.domain._root_analysis_validation import (
    RootAnalysisFailure,
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
) -> None:
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

    root_limits = RootAnalysisLimits()
    try:
        validate_reduced_transfer_function(reduced, root_limits)
        normalized, _ = validate_substitutions(
            reduced,
            root_analysis.substitutions,
            root_limits,
        )
    except (RootAnalysisFailure, AttributeError, TypeError, ValueError) as error:
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
        _validate_occurrence(item, source)
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


def _validate_occurrence(item: RootOccurrence, source: RootSource) -> None:
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
        try:
            exact_root_as_sympy(item.value)
        except (ArithmeticError, NotImplementedError, TypeError, ValueError) as error:
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


__all__ = [
    "StabilityLimitError",
    "StabilityValidationError",
    "expression_node_count",
    "validate_root_analysis",
]
