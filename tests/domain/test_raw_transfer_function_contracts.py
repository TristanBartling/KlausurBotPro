"""Tests for raw transfer-function limits, predicates, and results."""

from dataclasses import FrozenInstanceError

import pytest
import sympy as sp

from klausurbotpro.domain import (
    Diagnostic,
    DiagnosticCode,
    DiagnosticSeverity,
    ExactExpression,
    RawTransferFunctionCreationResult,
    RawTransferFunctionLimits,
    TransferFunctionPrerequisite,
    TransferFunctionPrerequisiteKind,
)


def _exact(value: sp.Expr) -> ExactExpression:
    return ExactExpression._from_sympy(value)


def test_default_limits_are_explicit_and_positive() -> None:
    limits = RawTransferFunctionLimits()

    assert limits.max_raw_nodes == 512
    assert limits.max_raw_depth == 64
    assert limits.max_integer_digits == 128
    assert limits.max_exponent_abs == 32
    assert limits.max_rationalized_occurrences == 4096
    assert limits.max_intermediate_expressions == 2048
    assert limits.max_translation_steps == 4096
    assert limits.max_numerator_degree == 32
    assert limits.max_denominator_degree == 32
    assert limits.max_parameters == 16
    assert limits.max_prerequisites == 64
    assert limits.max_domain_exclusions == 64


@pytest.mark.parametrize("name", RawTransferFunctionLimits.__dataclass_fields__)
@pytest.mark.parametrize("value", [0, -1, True])
def test_limits_reject_nonpositive_and_bool_values(name: str, value: int) -> None:
    with pytest.raises(ValueError, match="positive int"):
        RawTransferFunctionLimits(**{name: value})


def test_prerequisites_are_structured_immutable_and_deterministic() -> None:
    K, T = sp.symbols("K T")
    single = TransferFunctionPrerequisite(
        TransferFunctionPrerequisiteKind.EXPRESSION_NONZERO,
        (_exact(K),),
        ("z", "a", "a"),
    )
    multiple = TransferFunctionPrerequisite(
        TransferFunctionPrerequisiteKind.NOT_ALL_ZERO,
        (_exact(K - 1), _exact(T)),
        ("divisor",),
    )

    assert single.description == "K != 0"
    assert single.origins == ("a", "z")
    assert multiple.description == "NOT_ALL_ZERO(K - 1, T)"
    with pytest.raises(FrozenInstanceError):
        single.kind = TransferFunctionPrerequisiteKind.NOT_ALL_ZERO  # type: ignore[misc]


def test_prerequisite_contract_rejects_invalid_arguments() -> None:
    with pytest.raises(ValueError, match="at least one"):
        TransferFunctionPrerequisite(
            TransferFunctionPrerequisiteKind.NOT_ALL_ZERO,
            (),
            ("test",),
        )
    with pytest.raises(ValueError, match="exactly one"):
        TransferFunctionPrerequisite(
            TransferFunctionPrerequisiteKind.EXPRESSION_NONZERO,
            (_exact(sp.Integer(1)), _exact(sp.Integer(2))),
            ("test",),
        )
    with pytest.raises(ValueError, match="nonempty origins"):
        TransferFunctionPrerequisite(
            TransferFunctionPrerequisiteKind.EXPRESSION_NONZERO,
            (_exact(sp.Integer(1)),),
            (),
        )


def test_failed_creation_result_requires_an_error() -> None:
    error = Diagnostic(
        DiagnosticSeverity.ERROR,
        DiagnosticCode.RAW_TRANSFER_INVALID_TREE,
        "Ungültiger Baum.",
    )

    result = RawTransferFunctionCreationResult(None, (error,))

    assert not result.succeeded
    with pytest.raises(ValueError, match="requires an error"):
        RawTransferFunctionCreationResult(None)
