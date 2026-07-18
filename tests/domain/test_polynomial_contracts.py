"""Tests for immutable polynomial conditions, limits, and result contracts."""

from dataclasses import FrozenInstanceError

import pytest
import sympy as sp

from klausurbotpro.domain import (
    Diagnostic,
    DiagnosticCode,
    DiagnosticSeverity,
    ExactExpression,
    PolynomialCondition,
    PolynomialConditionKind,
    PolynomialCreationResult,
    PolynomialDegreeInfo,
    PolynomialFactory,
    PolynomialLimits,
)


def _exact(expression: sp.Expr) -> ExactExpression:
    return ExactExpression._from_sympy(expression)


def test_default_polynomial_limits_are_the_documented_start_values() -> None:
    limits = PolynomialLimits()

    assert limits.max_degree == 32
    assert limits.max_coefficients == 33
    assert limits.max_structural_terms == 33
    assert limits.max_parameters == 16
    assert limits.max_coefficient_operations == 128
    assert limits.max_expression_nodes == 512


@pytest.mark.parametrize(
    "override",
    [
        {"max_degree": 0},
        {"max_coefficients": 0},
        {"max_structural_terms": 0},
        {"max_parameters": 0},
        {"max_coefficient_operations": 0},
        {"max_expression_nodes": 0},
    ],
)
def test_polynomial_limits_reject_nonpositive_values(
    override: dict[str, int],
) -> None:
    with pytest.raises(ValueError, match="greater than zero"):
        PolynomialLimits(**override)


def test_condition_has_stable_kind_and_description() -> None:
    condition = PolynomialCondition(
        PolynomialConditionKind.DEFINITION_NONZERO,
        _exact(sp.Symbol("T") + 1),
    )

    assert condition.kind.value == "definition_nonzero"
    assert condition.description == "T + 1 != 0"
    invalid_expression = "T"
    with pytest.raises(TypeError, match="ExactExpression"):
        PolynomialCondition(
            PolynomialConditionKind.DEFINITION_NONZERO,
            invalid_expression,  # type: ignore[arg-type]
        )


def test_degree_info_validates_its_invariants() -> None:
    condition = PolynomialCondition(
        PolynomialConditionKind.LEADING_COEFFICIENT_NONZERO,
        _exact(sp.Symbol("K")),
    )

    assert PolynomialDegreeInfo(2, 2).guaranteed_degree == 2
    assert PolynomialDegreeInfo(2, None, (condition,)).conditions == (
        condition,
    )
    with pytest.raises(ValueError, match="nonnegative"):
        PolynomialDegreeInfo(-1, None)
    with pytest.raises(ValueError, match="degree-less"):
        PolynomialDegreeInfo(None, None, (condition,))
    with pytest.raises(ValueError, match="must equal"):
        PolynomialDegreeInfo(2, 1)
    with pytest.raises(ValueError, match="cannot require"):
        PolynomialDegreeInfo(2, 2, (condition,))
    definition = PolynomialCondition(
        PolynomialConditionKind.DEFINITION_NONZERO,
        _exact(sp.Symbol("T")),
    )
    with pytest.raises(ValueError, match="leading-coefficient"):
        PolynomialDegreeInfo(2, None, (definition,))


def test_creation_result_allows_warnings_with_value() -> None:
    polynomial = PolynomialFactory().create(
        _exact(sp.Symbol("K")),
        declared_parameter_names=frozenset({"K"}),
    ).value
    assert polynomial is not None
    warning = Diagnostic(
        DiagnosticSeverity.WARNING,
        DiagnosticCode.POLYNOMIAL_CONDITIONAL_DEGREE,
        "Bedingter Grad.",
    )

    result = PolynomialCreationResult(polynomial, (warning,))

    assert result.succeeded
    assert result.diagnostics == (warning,)


def test_creation_result_rejects_invalid_value_error_combinations() -> None:
    error = Diagnostic(
        DiagnosticSeverity.ERROR,
        DiagnosticCode.POLYNOMIAL_NOT_POLYNOMIAL,
        "Kein Polynom.",
    )
    polynomial = PolynomialFactory().create(_exact(sp.Integer(1))).value
    assert polynomial is not None

    with pytest.raises(ValueError, match="requires an error"):
        PolynomialCreationResult(None)
    with pytest.raises(ValueError, match="cannot contain an error"):
        PolynomialCreationResult(polynomial, (error,))


def test_contracts_are_immutable() -> None:
    limits = PolynomialLimits()
    degree_info = PolynomialDegreeInfo(1, 1)

    with pytest.raises(FrozenInstanceError):
        limits.max_degree = 1  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        degree_info.generic_degree = 2  # type: ignore[misc]
