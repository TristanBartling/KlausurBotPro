"""Contracts and limits for exact transfer-function reduction."""

from dataclasses import FrozenInstanceError

import pytest
import sympy as sp

from klausurbotpro.domain import (
    CommonTransferFunctionInput,
    Diagnostic,
    DiagnosticCode,
    DiagnosticSeverity,
    ExactExpression,
    RawTransferFunctionFactory,
    TransferFunctionReducer,
    TransferFunctionReductionLimits,
    TransferFunctionReductionReport,
    TransferFunctionReductionResult,
    TransferFunctionReductionStep,
    TransferFunctionReductionStepKind,
)
from klausurbotpro.domain.raw_algebraic_expression import ExactNumber


def _exact(value: int) -> ExactExpression:
    return ExactExpression._from_sympy(sp.Integer(value))


def _raw() -> object:
    input_value = CommonTransferFunctionInput(
        expression=ExactNumber(1),
        variable_name="s",
        allowed_symbol_names=frozenset({"s"}),
        original_text="1",
        normalized_text="1",
    )
    result = RawTransferFunctionFactory().create(input_value)
    assert result.value is not None
    return result.value


def test_limits_are_explicit_positive_and_immutable() -> None:
    limits = TransferFunctionReductionLimits()

    assert limits.max_parameters == 16
    assert limits.max_input_terms == 128
    assert limits.max_input_expression_nodes == 1024
    assert limits.max_multivariate_total_degree == 64
    assert limits.max_multivariate_terms == 4096
    assert limits.max_coefficient_digits == 256
    assert limits.max_common_factor_nodes == 512
    assert limits.max_result_nodes == 1024
    assert limits.max_reduction_steps == 16
    with pytest.raises(FrozenInstanceError):
        limits.max_parameters = 1  # type: ignore[misc]


@pytest.mark.parametrize("name", TransferFunctionReductionLimits.__dataclass_fields__)
@pytest.mark.parametrize("value", [0, -1, True])
def test_limits_reject_nonpositive_values(name: str, value: int) -> None:
    with pytest.raises(ValueError, match="positive int"):
        TransferFunctionReductionLimits(**{name: value})


def test_step_and_report_are_structured_deterministic_values() -> None:
    step = TransferFunctionReductionStep(
        TransferFunctionReductionStepKind.REMOVE_COMMON_NUMERIC_FACTOR,
        _exact(2),
        _exact(4),
        _exact(1),
        _exact(2),
        _exact(2),
    )
    report = TransferFunctionReductionReport((step,))

    assert report.was_reduced
    assert report.steps == (step,)
    assert step.factor is not None
    assert step.factor.canonical_text == "2"
    with pytest.raises(FrozenInstanceError):
        step.factor = None  # type: ignore[misc]
    with pytest.raises(ValueError, match="at least one"):
        TransferFunctionReductionReport(())
    with pytest.raises(TypeError, match="supported kind"):
        TransferFunctionReductionStep(
            "invalid",  # type: ignore[arg-type]
            _exact(1),
            _exact(1),
            _exact(1),
            _exact(1),
        )


def test_no_reduction_report_is_not_marked_as_reduced() -> None:
    step = TransferFunctionReductionStep(
        TransferFunctionReductionStepKind.NO_REDUCTION,
        _exact(1),
        _exact(1),
        _exact(1),
        _exact(1),
    )

    assert not TransferFunctionReductionReport((step,)).was_reduced


def test_result_contract_enforces_success_and_failure_invariants() -> None:
    raw = _raw()
    assert hasattr(raw, "numerator")
    success = TransferFunctionReducer().reduce(raw)  # type: ignore[arg-type]
    assert success.reduced is not None
    assert success.report is not None
    assert success.succeeded

    error = Diagnostic(
        DiagnosticSeverity.ERROR,
        DiagnosticCode.TRANSFER_REDUCTION_INVALID_RAW_VALUE,
        "Ungültig.",
    )
    failure = TransferFunctionReductionResult(
        raw=raw,  # type: ignore[arg-type]
        reduced=None,
        report=None,
        diagnostics=(error,),
    )
    assert not failure.succeeded
    with pytest.raises(ValueError, match="requires an error"):
        TransferFunctionReductionResult(
            raw=raw,  # type: ignore[arg-type]
            reduced=None,
            report=None,
        )
    with pytest.raises(ValueError, match="requires a report"):
        TransferFunctionReductionResult(
            raw=raw,  # type: ignore[arg-type]
            reduced=success.reduced,
            report=None,
        )
