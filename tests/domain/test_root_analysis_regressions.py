"""Reduction integration, defensive validation, and limit regressions."""

from __future__ import annotations

import inspect

import pytest
import sympy as sp

import klausurbotpro.domain.transfer_function_root_analyzer as analyzer_module
from klausurbotpro.domain import (
    CommonTransferFunctionInput,
    DiagnosticCode,
    ExactExpression,
    ExplicitExactRootValue,
    PolynomialFactory,
    PolynomialRootStatus,
    RawTransferFunctionFactory,
    ReducedTransferFunction,
    RootAnalysisLimits,
    TransferFunctionReducer,
    TransferFunctionReductionResult,
    TransferFunctionRootAnalyzer,
)
from klausurbotpro.domain.raw_algebraic_expression import (
    Add,
    Divide,
    ExactNumber,
    Multiply,
    Symbol,
)


def _plain_reduced(expression: sp.Expr | None = None) -> ReducedTransferFunction:
    factory = PolynomialFactory()
    numerator = factory.create(
        ExactExpression._from_sympy(
            sp.Symbol("s") + 1 if expression is None else expression
        )
    ).value
    denominator = factory.create(
        ExactExpression._from_sympy(sp.Integer(1))
    ).value
    assert numerator is not None
    assert denominator is not None
    return ReducedTransferFunction._create(
        variable_name="s",
        numerator=numerator,
        denominator=denominator,
        prerequisites=(),
        domain_exclusions=(),
    )


def _cancelled_reduction() -> TransferFunctionReductionResult:
    expression = Divide(
        Add(Symbol("s"), ExactNumber(1)),
        Add(Symbol("s"), ExactNumber(1)),
    )
    created = RawTransferFunctionFactory(
        allowed_parameter_names=frozenset()
    ).create(
        CommonTransferFunctionInput(
            expression=expression,
            variable_name="s",
            allowed_symbol_names=frozenset({"s"}),
            original_text="not mathematical",
            normalized_text="not mathematical",
        )
    )
    assert created.value is not None
    return TransferFunctionReducer().reduce(created.value)


def test_plain_analysis_keeps_cancellations_not_evaluated_but_domain_visible() -> None:
    reduction = _cancelled_reduction()
    assert reduction.reduced is not None
    result = TransferFunctionRootAnalyzer().analyze(reduction.reduced)

    assert result.reduced_zeros is not None
    assert result.reduced_poles is not None
    assert result.reduced_zeros.roots == result.reduced_poles.roots == ()
    assert result.cancelled_locations.status is PolynomialRootStatus.NOT_EVALUATED
    exclusion = result.retained_domain_exclusions.analyses[0]
    value = exclusion.roots[0].value
    assert isinstance(value, ExplicitExactRootValue)
    assert value.expression.canonical_text == "-1"


def test_reduction_analysis_reports_only_proven_polynomial_cancellations() -> None:
    reduction = _cancelled_reduction()
    result = TransferFunctionRootAnalyzer().analyze_reduction(
        reduction
    )

    assert result.cancelled_locations.status is PolynomialRootStatus.COMPLETE
    assert len(result.cancelled_locations.analyses) == 1
    root = result.cancelled_locations.analyses[0].roots[0]
    assert isinstance(root.value, ExplicitExactRootValue)
    assert root.value.expression.canonical_text == "-1"


def test_parameter_only_cancelled_factor_creates_no_main_variable_location() -> None:
    expression = Divide(
        Multiply(Symbol("K"), Add(Symbol("s"), ExactNumber(1))),
        Multiply(Symbol("K"), Add(Symbol("s"), ExactNumber(2))),
    )
    created = RawTransferFunctionFactory(
        allowed_parameter_names=frozenset({"K"})
    ).create(
        CommonTransferFunctionInput(
            expression=expression,
            variable_name="s",
            allowed_symbol_names=frozenset({"K", "s"}),
            original_text="not mathematical",
            normalized_text="not mathematical",
        )
    )
    assert created.value is not None
    reduction = TransferFunctionReducer().reduce(created.value)

    result = TransferFunctionRootAnalyzer().analyze_reduction(reduction)

    assert result.cancelled_locations.analyses
    assert result.cancelled_locations.analyses[0].status is (
        PolynomialRootStatus.CONSTANT_NONZERO
    )
    assert result.cancelled_locations.analyses[0].roots == ()


def test_manipulated_reduction_report_is_rejected() -> None:
    reduction = _cancelled_reduction()
    assert reduction.report is not None
    object.__setattr__(
        reduction.report.steps[0],
        "factor",
        ExactExpression._from_sympy(sp.Integer(2)),
    )

    result = TransferFunctionRootAnalyzer().analyze_reduction(reduction)

    assert result.diagnostics[0].code is (
        DiagnosticCode.ROOT_ANALYSIS_INVALID_TRANSFER_FUNCTION
    )


def test_forged_reduced_value_is_rejected_defensively() -> None:
    value = _plain_reduced()
    object.__setattr__(value, "used_parameter_names", frozenset({"forged"}))

    result = TransferFunctionRootAnalyzer().analyze(value)

    assert result.diagnostics[0].code is (
        DiagnosticCode.ROOT_ANALYSIS_INVALID_TRANSFER_FUNCTION
    )


def test_public_methods_reject_wrong_python_types() -> None:
    analyzer = TransferFunctionRootAnalyzer()
    with pytest.raises(TypeError, match="ReducedTransferFunction"):
        analyzer.analyze(object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="TransferFunctionReductionResult"):
        analyzer.analyze_reduction(object())  # type: ignore[arg-type]


def test_limits_and_resource_errors_are_structured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    limited = TransferFunctionRootAnalyzer(
        RootAnalysisLimits(max_polynomial_degree=1)
    ).analyze(_plain_reduced(sp.Symbol("s") ** 2 + 1))

    def fail(*args: object, **kwargs: object) -> None:
        raise MemoryError

    monkeypatch.setattr(analyzer_module, "validate_reduced_transfer_function", fail)
    exhausted = TransferFunctionRootAnalyzer().analyze(_plain_reduced())

    assert limited.diagnostics[0].code is (
        DiagnosticCode.ROOT_ANALYSIS_LIMIT_EXCEEDED
    )
    assert exhausted.diagnostics[0].code is (
        DiagnosticCode.ROOT_ANALYSIS_RESOURCE_LIMIT_EXCEEDED
    )


def test_rootof_limit_is_checked_before_algebraic_approximations() -> None:
    s = sp.Symbol("s")
    result = TransferFunctionRootAnalyzer(
        RootAnalysisLimits(max_exact_rootof_count=4)
    ).analyze(_plain_reduced(s**5 - s + 1))

    assert result.diagnostics[0].code is (
        DiagnosticCode.ROOT_ANALYSIS_LIMIT_EXCEEDED
    )
    assert result.diagnostics[0].technical_details == (
        ("limit", "max_exact_rootof_count"),
    )


def test_public_analyzer_has_no_parsing_dependency_or_sympy_contract_value() -> None:
    result = TransferFunctionRootAnalyzer().analyze(_plain_reduced())
    source = inspect.getsource(analyzer_module)

    assert "klausurbotpro.parsing" not in source
    assert result.reduced_zeros is not None
    assert not isinstance(result.reduced_zeros, (sp.Expr, sp.Poly))
