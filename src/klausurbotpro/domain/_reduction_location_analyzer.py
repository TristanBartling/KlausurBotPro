"""Validation and cancelled-location extraction from a reduction report."""

from __future__ import annotations

import sympy as sp

from klausurbotpro.domain._root_analysis_validation import RootAnalysisFailure
from klausurbotpro.domain.diagnostics import DiagnosticCode
from klausurbotpro.domain.expression import ExactExpression
from klausurbotpro.domain.raw_transfer_function import RawTransferFunction
from klausurbotpro.domain.reduced_transfer_function import (
    ReducedTransferFunction,
)
from klausurbotpro.domain.root_analysis_contracts import RootAnalysisLimits
from klausurbotpro.domain.transfer_function_reducer import (
    TransferFunctionReducer,
)
from klausurbotpro.domain.transfer_function_reduction_contracts import (
    TransferFunctionReductionReport,
    TransferFunctionReductionResult,
    TransferFunctionReductionStep,
    TransferFunctionReductionStepKind,
)


def cancelled_factor_expressions(
    reduction: TransferFunctionReductionResult,
    limits: RootAnalysisLimits,
) -> tuple[ExactExpression, ...]:
    """Return only proven common polynomial factors from a valid report."""

    if type(reduction) is not TransferFunctionReductionResult:
        raise TypeError(
            "analyze_reduction requires a TransferFunctionReductionResult."
        )
    if (
        type(reduction.raw) is not RawTransferFunction
        or type(reduction.reduced) is not ReducedTransferFunction
        or type(reduction.report) is not TransferFunctionReductionReport
    ):
        raise RootAnalysisFailure(
            DiagnosticCode.ROOT_ANALYSIS_INVALID_TRANSFER_FUNCTION,
            "Nur eine erfolgreiche Reduktion kann analysiert werden.",
        )
    if reduction.raw.variable_name != reduction.reduced.variable_name:
        _invalid_report()
    recomputed = TransferFunctionReducer().reduce(reduction.raw)
    if (
        not recomputed.succeeded
        or recomputed.reduced != reduction.reduced
        or recomputed.report != reduction.report
    ):
        _invalid_report()
    steps = reduction.report.steps
    if not steps or any(type(step) is not TransferFunctionReductionStep for step in steps):
        _invalid_report()
    for step in steps:
        exact_values = (
            step.numerator_before,
            step.denominator_before,
            step.numerator_after,
            step.denominator_after,
        )
        if any(type(value) is not ExactExpression for value in exact_values):
            _invalid_report()
    first = steps[0]
    if (
        first.numerator_before != reduction.raw.numerator.expression
        or first.denominator_before != reduction.raw.denominator.expression
    ):
        _invalid_report()
    for previous, current in zip(steps, steps[1:], strict=False):
        if (
            previous.numerator_after != current.numerator_before
            or previous.denominator_after != current.denominator_before
        ):
            _invalid_report()
    last = steps[-1]
    if (
        last.numerator_after != reduction.reduced.numerator.expression
        or last.denominator_after != reduction.reduced.denominator.expression
    ):
        _invalid_report()

    factors: list[ExactExpression] = []
    for step in steps:
        if type(step.kind) is not TransferFunctionReductionStepKind:
            _invalid_report()
        if step.kind is TransferFunctionReductionStepKind.REMOVE_COMMON_POLYNOMIAL_FACTOR:
            if type(step.factor) is not ExactExpression:
                _invalid_report()
            assert step.factor is not None
            factor = step.factor._as_sympy()
            if (
                factor == 0
                or sp.cancel(
                    step.numerator_before._as_sympy()
                    - step.numerator_after._as_sympy() * factor
                )
                != 0
                or sp.cancel(
                    step.denominator_before._as_sympy()
                    - step.denominator_after._as_sympy() * factor
                )
                != 0
            ):
                _invalid_report()
            factors.append(step.factor)
    if len(factors) > limits.max_cancelled_factors:
        raise RootAnalysisFailure(
            DiagnosticCode.ROOT_ANALYSIS_LIMIT_EXCEEDED,
            "Es wurden zu viele gekürzte Faktoren dokumentiert.",
            (("limit", "max_cancelled_factors"),),
        )
    return tuple(factors)


def _invalid_report() -> None:
    raise RootAnalysisFailure(
        DiagnosticCode.ROOT_ANALYSIS_INVALID_TRANSFER_FUNCTION,
        "Der Reduktionsbericht ist nicht lückenlos konsistent.",
    )
