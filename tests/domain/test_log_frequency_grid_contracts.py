"""Contract invariants for certified logarithmic frequency grids."""

from dataclasses import FrozenInstanceError
from decimal import ROUND_DOWN, localcontext

import pytest

from klausurbotpro.domain import (
    ExactRationalValue,
    LogFrequencyGridGenerator,
    LogFrequencyGridLimits,
    LogFrequencyGridPoint,
    LogFrequencyGridRequest,
    LogFrequencyGridResult,
    LogFrequencyGridStatus,
    LogFrequencyPointOrigin,
    ScientificDecimal,
)


def test_scientific_decimal_is_positive_canonical_and_deterministic() -> None:
    value = ScientificDecimal(12_300, -4)

    assert value.significand == 123
    assert value.exponent10 == -2
    assert value.decimal_text == "1.23"
    assert value.scientific_text == "1.23e+0"
    assert value == ScientificDecimal(123, -2)
    assert hash(value) == hash(ScientificDecimal(123, -2))


def test_scientific_decimal_text_is_independent_of_decimal_context() -> None:
    value = ScientificDecimal(12345678901234567890123456789, -28)

    with localcontext() as context:
        context.prec = 2
        context.rounding = ROUND_DOWN
        decimal_text = value.decimal_text

    assert decimal_text == "1.2345678901234567890123456789"


@pytest.mark.parametrize(
    ("significand", "exponent", "error_type"),
    [
        (True, 0, TypeError),
        (1, False, TypeError),
        (0, 0, ValueError),
        (-1, 0, ValueError),
    ],
)
def test_scientific_decimal_rejects_invalid_direct_contracts(
    significand: int,
    exponent: int,
    error_type: type[Exception],
) -> None:
    with pytest.raises(error_type):
        ScientificDecimal(significand, exponent)


@pytest.mark.parametrize("name", LogFrequencyGridLimits.__dataclass_fields__)
@pytest.mark.parametrize("value", [0, -1, True])
def test_grid_limits_require_positive_real_integers(
    name: str,
    value: int,
) -> None:
    with pytest.raises(ValueError, match="positive int"):
        LogFrequencyGridLimits(**{name: value})


def test_precision_limit_requires_at_least_two_digits() -> None:
    with pytest.raises(ValueError, match="at least 2"):
        LogFrequencyGridLimits(grid_precision_digits=1)


def test_points_and_results_are_generator_controlled_and_immutable() -> None:
    request = LogFrequencyGridRequest(
        ExactRationalValue(1),
        ExactRationalValue(10),
        2,
    )
    result = LogFrequencyGridGenerator().generate(request)
    point = result.points[0]

    with pytest.raises(TypeError, match="must be created"):
        LogFrequencyGridPoint()
    with pytest.raises(TypeError, match="must be created"):
        LogFrequencyGridResult()
    with pytest.raises(FrozenInstanceError):
        point.origins = (LogFrequencyPointOrigin.EXPLICIT,)  # type: ignore[misc]
    assert result.status is LogFrequencyGridStatus.COMPLETE


def test_public_grid_api_is_exported() -> None:
    assert all(
        value is not None
        for value in (
            LogFrequencyGridGenerator,
            LogFrequencyGridLimits,
            LogFrequencyGridPoint,
            LogFrequencyGridRequest,
            LogFrequencyGridResult,
            LogFrequencyGridStatus,
            LogFrequencyPointOrigin,
            ScientificDecimal,
        )
    )
