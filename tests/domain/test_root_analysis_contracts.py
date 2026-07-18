"""Invariant tests for the public SymPy-free root-analysis contracts."""

import pytest
import sympy as sp

from klausurbotpro.domain import (
    ConjugateStatus,
    ExactExpression,
    ExplicitExactRootValue,
    NumericalRootEstimate,
    PolynomialRootAnalysis,
    PolynomialRootStatus,
    RootOccurrence,
    RootOfValue,
    RootSource,
)


def test_exact_root_occurrences_have_structural_equality_and_hash() -> None:
    value = ExplicitExactRootValue(ExactExpression._from_sympy(sp.Integer(-1)))
    first = RootOccurrence(value, 2, RootSource.NUMERATOR, 0)
    second = RootOccurrence(value, 2, RootSource.NUMERATOR, 0)

    assert first == second
    assert hash(first) == hash(second)
    assert {first: "root"}[second] == "root"


def test_rootof_contract_requires_a_canonical_addressable_polynomial() -> None:
    assert RootOfValue((1, 0, 1), 1).root_index == 1
    with pytest.raises(ValueError, match="positive-leading"):
        RootOfValue((-1, 0, -1), 0)
    with pytest.raises(ValueError, match="primitive"):
        RootOfValue((2, 0, 2), 0)
    with pytest.raises(ValueError, match="address"):
        RootOfValue((1, 1), 1)


def test_numerical_estimates_are_immutable_structural_and_unhashable() -> None:
    estimate = NumericalRootEstimate(
        0,
        "-1",
        "0",
        40,
        "0",
        "0",
        ConjugateStatus.REAL,
    )
    assert estimate == estimate
    with pytest.raises(TypeError, match="unhashable"):
        hash(estimate)


def test_polynomial_root_analysis_rejects_invalid_multiplicity() -> None:
    value = ExplicitExactRootValue(ExactExpression._from_sympy(sp.Integer(0)))
    with pytest.raises(ValueError, match="positive"):
        RootOccurrence(value, 0, RootSource.NUMERATOR, 0)
    analysis = PolynomialRootAnalysis(
        PolynomialRootStatus.CONSTANT_NONZERO,
        RootSource.NUMERATOR,
        ExactExpression._from_sympy(sp.Integer(1)),
        actual_degree=0,
    )
    assert analysis.roots == ()
