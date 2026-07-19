"""Tests for numerical checks subordinate to exact roots."""

from decimal import Decimal

import pytest
import sympy as sp
from sympy.core.evalf import PrecisionExhausted

import klausurbotpro.domain._numeric_root_verifier as numeric_module
from klausurbotpro.domain import (
    ConjugateStatus,
    DiagnosticCode,
    ExactExpression,
    NumericalRootWarning,
    PolynomialFactory,
    ReducedTransferFunction,
    RootAnalysisLimits,
    TransferFunctionRootAnalyzer,
)


def _value(expression: sp.Expr) -> ReducedTransferFunction:
    factory = PolynomialFactory()
    numerator = factory.create(ExactExpression._from_sympy(expression)).value
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


def test_every_exact_root_has_a_small_checked_residual() -> None:
    s = sp.Symbol("s")
    result = TransferFunctionRootAnalyzer().analyze(_value(s**5 - s + 1))
    assert result.reduced_zeros is not None

    assert len(result.reduced_zeros.numerical_estimates) == 5
    assert all(
        Decimal(item.scaled_residual) < Decimal("1e-20")
        for item in result.reduced_zeros.numerical_estimates
    )


def test_real_coefficient_complex_roots_have_confirmed_conjugates() -> None:
    s = sp.Symbol("s")
    result = TransferFunctionRootAnalyzer().analyze(_value(s**2 + 1))
    assert result.reduced_zeros is not None

    assert {
        item.conjugate_status
        for item in result.reduced_zeros.numerical_estimates
    } == {ConjugateStatus.CONFIRMED}
    assert DiagnosticCode.ROOT_ANALYSIS_CONJUGATE_MISMATCH not in {
        item.code for item in result.diagnostics
    }


def test_multiple_and_close_roots_produce_structured_warnings() -> None:
    s = sp.Symbol("s")
    repeated = TransferFunctionRootAnalyzer().analyze(_value((s + 1) ** 2))
    scale = 10**20
    clustered = TransferFunctionRootAnalyzer(
        RootAnalysisLimits(numeric_precision_digits=40)
    ).analyze(
        _value((scale * s - scale) * (scale * s - scale - 1))
    )
    assert repeated.reduced_zeros is not None
    assert clustered.reduced_zeros is not None

    assert NumericalRootWarning.MULTIPLE_ROOT in (
        repeated.reduced_zeros.numerical_estimates[0].warnings
    )
    assert any(
        NumericalRootWarning.CLOSE_CLUSTER in item.warnings
        for item in clustered.reduced_zeros.numerical_estimates
    )
    assert DiagnosticCode.ROOT_ANALYSIS_ILL_CONDITIONED in {
        item.code for item in repeated.diagnostics + clustered.diagnostics
    }


def test_root_and_estimate_order_is_deterministic() -> None:
    s = sp.Symbol("s")
    analyzer = TransferFunctionRootAnalyzer()
    first = analyzer.analyze(_value(s**4 + s + 1))
    second = analyzer.analyze(_value(s**4 + s + 1))

    assert first.reduced_zeros == second.reduced_zeros
    assert first.diagnostics == second.diagnostics


def test_precision_exhaustion_keeps_exact_roots_and_is_structured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class ExhaustedExpression:
        def evalf(
            self,
            digits: int,
            *,
            maxn: int,
            strict: bool,
        ) -> sp.Expr:
            assert digits == 52
            assert maxn == 160
            assert strict is True
            raise PrecisionExhausted

    def exhausted_root(value: object) -> ExhaustedExpression:
        return ExhaustedExpression()

    monkeypatch.setattr(
        numeric_module,
        "exact_root_as_sympy",
        exhausted_root,
    )
    result = TransferFunctionRootAnalyzer().analyze(
        _value(sp.Symbol("s") + 1)
    )

    assert result.succeeded
    assert result.reduced_zeros is not None
    assert len(result.reduced_zeros.roots) == 1
    assert result.reduced_zeros.numerical_estimates == ()
    assert DiagnosticCode.ROOT_ANALYSIS_NUMERIC_SOLVER_FAILED in {
        item.code for item in result.diagnostics
    }
    assert DiagnosticCode.ROOT_ANALYSIS_NUMERIC_CHECK_SKIPPED in {
        item.code for item in result.diagnostics
    }
