"""Contract invariants for exact pointwise frequency responses."""

from dataclasses import FrozenInstanceError

import pytest
import sympy as sp

from klausurbotpro.domain import (
    DecibelValueKind,
    Diagnostic,
    DiagnosticCode,
    DiagnosticSeverity,
    ExactExpression,
    ExactRationalValue,
    FrequencyResponseLimits,
    FrequencyResponsePoint,
    FrequencyResponsePointStatus,
    FrequencySampleSet,
    NumericalDecibelValue,
    PolynomialFactory,
    ReducedTransferFunction,
    TransferFunctionFrequencyResponseAnalyzer,
    TransferFunctionFrequencyResponseResult,
    TransferFunctionFrequencyResponseStatus,
)
from klausurbotpro.domain.frequency_response_contracts import (
    _aggregate_frequency_response_status,
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


def _constant_reduced(value: int) -> ReducedTransferFunction:
    factory = PolynomialFactory()
    numerator = factory.create(_exact(value)).value
    denominator = factory.create(_exact(1)).value
    assert numerator is not None
    assert denominator is not None
    return ReducedTransferFunction._create(
        variable_name="s",
        numerator=numerator,
        denominator=denominator,
        prerequisites=(),
        domain_exclusions=(),
    )


def test_points_are_analyzer_controlled_and_immutable() -> None:
    result = TransferFunctionFrequencyResponseAnalyzer().analyze(
        _constant_reduced(0),
        FrequencySampleSet((ExactRationalValue(0),)),
    )
    point = result.points[0]

    with pytest.raises(FrozenInstanceError):
        point.status = FrequencyResponsePointStatus.DEFINED  # type: ignore[misc]
    with pytest.raises(TypeError, match="must be created"):
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


@pytest.mark.parametrize(
    ("statuses", "expected"),
    [
        (
            (FrequencyResponsePointStatus.DEFINED,),
            TransferFunctionFrequencyResponseStatus.COMPLETE,
        ),
        (
            (
                FrequencyResponsePointStatus.DEFINED,
                FrequencyResponsePointStatus.ZERO_RESPONSE,
            ),
            TransferFunctionFrequencyResponseStatus.COMPLETE,
        ),
        (
            (
                FrequencyResponsePointStatus.DEFINED,
                FrequencyResponsePointStatus.SINGULAR,
            ),
            TransferFunctionFrequencyResponseStatus.PARTIAL,
        ),
        (
            (
                FrequencyResponsePointStatus.DEFINED,
                FrequencyResponsePointStatus.SYMBOLIC_UNDETERMINED,
            ),
            TransferFunctionFrequencyResponseStatus.PARTIAL,
        ),
        (
            (FrequencyResponsePointStatus.SYMBOLIC_UNDETERMINED,),
            TransferFunctionFrequencyResponseStatus.SYMBOLIC_UNDETERMINED,
        ),
        (
            (
                FrequencyResponsePointStatus.SYMBOLIC_UNDETERMINED,
                FrequencyResponsePointStatus.SINGULAR,
            ),
            TransferFunctionFrequencyResponseStatus.SYMBOLIC_UNDETERMINED,
        ),
        (
            (FrequencyResponsePointStatus.SINGULAR,),
            TransferFunctionFrequencyResponseStatus.PARTIAL,
        ),
        (
            (FrequencyResponsePointStatus.NUMERIC_UNDETERMINED,),
            TransferFunctionFrequencyResponseStatus.PARTIAL,
        ),
        (
            (
                FrequencyResponsePointStatus.SYMBOLIC_UNDETERMINED,
                FrequencyResponsePointStatus.NUMERIC_UNDETERMINED,
            ),
            TransferFunctionFrequencyResponseStatus.PARTIAL,
        ),
    ],
)
def test_aggregate_status_matrix_has_one_authoritative_derivation(
    statuses: tuple[FrequencyResponsePointStatus, ...],
    expected: TransferFunctionFrequencyResponseStatus,
) -> None:
    assert _aggregate_frequency_response_status(statuses) is expected


def _zero_result(
    *frequencies: ExactRationalValue,
) -> TransferFunctionFrequencyResponseResult:
    return TransferFunctionFrequencyResponseAnalyzer().analyze(
        _constant_reduced(0),
        FrequencySampleSet(frequencies),
    )


def _recreate_result(
    source: TransferFunctionFrequencyResponseResult,
    *,
    points: tuple[FrequencyResponsePoint, ...] | None = None,
    diagnostics: tuple[Diagnostic, ...] | None = None,
) -> TransferFunctionFrequencyResponseResult:
    assert source.reduced_transfer_function is not None
    assert source.frequencies is not None
    return TransferFunctionFrequencyResponseResult._create(
        reduced_transfer_function=source.reduced_transfer_function,
        frequencies=source.frequencies,
        substitutions=source.substitutions,
        status=source.status,
        points=source.points if points is None else points,
        diagnostics=source.diagnostics if diagnostics is None else diagnostics,
    )


def test_result_revalidates_missing_and_wrong_point_diagnostics() -> None:
    missing = _zero_result(ExactRationalValue(0))
    object.__setattr__(missing.points[0], "diagnostics", ())
    with pytest.raises(ValueError, match="corresponding structured diagnostic"):
        _recreate_result(missing, diagnostics=())

    wrong = _zero_result(ExactRationalValue(0))
    object.__setattr__(
        wrong.points[0],
        "diagnostics",
        (
            Diagnostic(
                DiagnosticSeverity.WARNING,
                DiagnosticCode.FREQUENCY_RESPONSE_SINGULAR,
                "wrong",
            ),
        ),
    )
    with pytest.raises(ValueError, match="different status"):
        _recreate_result(wrong, diagnostics=wrong.points[0].diagnostics)

    conflicting = _zero_result(ExactRationalValue(0))
    object.__setattr__(
        conflicting.points[0],
        "diagnostics",
        conflicting.points[0].diagnostics
        + (
            Diagnostic(
                DiagnosticSeverity.WARNING,
                DiagnosticCode.FREQUENCY_RESPONSE_SINGULAR,
                "conflicting",
            ),
        ),
    )
    with pytest.raises(ValueError, match="different status"):
        _recreate_result(
            conflicting,
            diagnostics=conflicting.points[0].diagnostics,
        )


def test_result_diagnostics_must_be_exact_ordered_point_concatenation() -> None:
    source = _zero_result(ExactRationalValue(0), ExactRationalValue(1))
    extra = Diagnostic(
        DiagnosticSeverity.INFO,
        DiagnosticCode.FREQUENCY_RESPONSE_ZERO_RESPONSE,
        "extra",
    )

    with pytest.raises(ValueError, match="exactly concatenate"):
        _recreate_result(source, diagnostics=source.diagnostics + (extra,))
    with pytest.raises(ValueError, match="exactly concatenate"):
        _recreate_result(source, diagnostics=tuple(reversed(source.diagnostics)))


def test_result_rejects_foreign_frequency_and_manipulated_point_status() -> None:
    foreign_frequency = _zero_result(ExactRationalValue(0))
    object.__setattr__(
        foreign_frequency.points[0],
        "omega",
        ExactRationalValue(1),
    )
    with pytest.raises(ValueError, match="sample order"):
        _recreate_result(foreign_frequency)

    wrong_status = _zero_result(ExactRationalValue(0))
    object.__setattr__(
        wrong_status.points[0],
        "status",
        FrequencyResponsePointStatus.DEFINED,
    )
    with pytest.raises(ValueError, match="defined point"):
        _recreate_result(wrong_status)


def test_result_rejects_error_diagnostics_and_foreign_points() -> None:
    error_point = _zero_result(ExactRationalValue(0))
    error = Diagnostic(
        DiagnosticSeverity.ERROR,
        DiagnosticCode.FREQUENCY_RESPONSE_ZERO_RESPONSE,
        "error",
    )
    object.__setattr__(
        error_point.points[0],
        "diagnostics",
        error_point.points[0].diagnostics + (error,),
    )
    with pytest.raises(ValueError, match="must not contain errors"):
        _recreate_result(error_point, diagnostics=error_point.points[0].diagnostics)

    source = _zero_result(ExactRationalValue(0))
    with pytest.raises(TypeError, match="Invalid frequency-response point"):
        TransferFunctionFrequencyResponseResult._create(
            reduced_transfer_function=source.reduced_transfer_function,
            frequencies=source.frequencies,
            substitutions=None,
            status=source.status,
            points=(object(),),  # type: ignore[arg-type]
            diagnostics=(),
        )
