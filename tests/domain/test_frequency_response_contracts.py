"""Contract invariants for exact pointwise frequency responses."""

from dataclasses import FrozenInstanceError

import pytest
import sympy as sp

from klausurbotpro.domain import (
    DecibelValueKind,
    ExactExpression,
    ExactRationalValue,
    FrequencyResponseLimits,
    FrequencyResponsePoint,
    FrequencyResponsePointStatus,
    FrequencySampleSet,
    NumericalDecibelValue,
    TransferFunctionFrequencyResponseAnalyzer,
    TransferFunctionFrequencyResponseResult,
    TransferFunctionFrequencyResponseStatus,
)


def _exact(value: int) -> ExactExpression:
    return ExactExpression._from_sympy(sp.Integer(value))


def test_frequency_samples_require_an_exact_tuple_container() -> None:
    samples = FrequencySampleSet(
        (ExactRationalValue(0), ExactRationalValue(1, 2))
    )

    assert samples.frequencies[1] == ExactRationalValue(1, 2)
    with pytest.raises(TypeError, match="tuple"):
        FrequencySampleSet([])  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="ExactRationalValue"):
        FrequencySampleSet((object(),))  # type: ignore[arg-type]


@pytest.mark.parametrize("name", FrequencyResponseLimits.__dataclass_fields__)
@pytest.mark.parametrize("value", [0, -1, True])
def test_limits_require_positive_real_integers(name: str, value: int) -> None:
    with pytest.raises(ValueError, match="positive int"):
        FrequencyResponseLimits(**{name: value})


def test_decibel_contract_distinguishes_finite_and_minus_infinity() -> None:
    finite = NumericalDecibelValue(DecibelValueKind.FINITE, "-3.0100")
    minus_infinity = NumericalDecibelValue(
        DecibelValueKind.NEGATIVE_INFINITY
    )

    assert finite.decimal_value == "-3.01"
    assert minus_infinity.decimal_value is None
    with pytest.raises(ValueError, match="must not"):
        NumericalDecibelValue(
            DecibelValueKind.NEGATIVE_INFINITY,
            "-Infinity",
        )
    with pytest.raises(ValueError, match="finite"):
        NumericalDecibelValue(DecibelValueKind.FINITE, "NaN")


def test_points_are_immutable_and_require_status_consistent_values() -> None:
    point = FrequencyResponsePoint(
        ExactRationalValue(0),
        FrequencyResponsePointStatus.ZERO_RESPONSE,
        _exact(0),
        _exact(1),
        _exact(0),
        _exact(0),
        _exact(0),
        _exact(0),
        "0",
        "0",
        "0",
        NumericalDecibelValue(DecibelValueKind.NEGATIVE_INFINITY),
    )

    with pytest.raises(FrozenInstanceError):
        point.status = FrequencyResponsePointStatus.DEFINED  # type: ignore[misc]
    with pytest.raises(ValueError, match="defined point"):
        FrequencyResponsePoint(
            ExactRationalValue(1),
            FrequencyResponsePointStatus.DEFINED,
            _exact(1),
            _exact(1),
        )


def test_result_is_analyzer_controlled_and_public_api_is_exported() -> None:
    with pytest.raises(TypeError, match="must be created"):
        TransferFunctionFrequencyResponseResult()

    assert all(
        value is not None
        for value in (
            TransferFunctionFrequencyResponseAnalyzer,
            TransferFunctionFrequencyResponseResult,
            TransferFunctionFrequencyResponseStatus,
            FrequencyResponseLimits,
            FrequencyResponsePoint,
            FrequencyResponsePointStatus,
            FrequencySampleSet,
            NumericalDecibelValue,
            DecibelValueKind,
        )
    )
