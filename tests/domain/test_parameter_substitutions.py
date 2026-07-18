"""Tests for canonical exact parameter substitutions."""

import pytest

from klausurbotpro.domain import (
    ExactRationalValue,
    ParameterAssignment,
    ParameterSubstitutions,
)


def test_exact_rational_values_require_canonical_integer_form() -> None:
    assert ExactRationalValue(-1, 2) == ExactRationalValue(-1, 2)
    with pytest.raises(ValueError, match="fully reduced"):
        ExactRationalValue(2, 4)
    with pytest.raises(ValueError, match="positive"):
        ExactRationalValue(1, -2)
    with pytest.raises(TypeError, match="integers"):
        ExactRationalValue(True)


def test_substitutions_are_unique_sorted_and_hashable() -> None:
    substitutions = ParameterSubstitutions(
        (
            ParameterAssignment("T", ExactRationalValue(3)),
            ParameterAssignment("K", ExactRationalValue(1, 2)),
        )
    )

    assert tuple(item.parameter_name for item in substitutions.assignments) == (
        "K",
        "T",
    )
    assert substitutions.parameter_names == frozenset({"K", "T"})
    assert hash(substitutions) == hash(
        ParameterSubstitutions(tuple(reversed(substitutions.assignments)))
    )


def test_duplicate_or_invalid_parameter_names_are_rejected() -> None:
    assignment = ParameterAssignment("K", ExactRationalValue(1))
    with pytest.raises(ValueError, match="only be assigned once"):
        ParameterSubstitutions((assignment, assignment))
    with pytest.raises(ValueError, match="identifier"):
        ParameterAssignment("K+1", ExactRationalValue(1))
