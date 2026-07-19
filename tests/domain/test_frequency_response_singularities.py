"""Singular, zero, and symbolically undetermined frequency points."""

import sympy as sp

from klausurbotpro.domain import (
    DecibelValueKind,
    DiagnosticCode,
    ExactExpression,
    ExactRationalValue,
    FrequencyResponsePointStatus,
    FrequencySampleSet,
    ParameterAssignment,
    ParameterSubstitutions,
    PolynomialFactory,
    ReducedTransferFunction,
    TransferFunctionDomainExclusion,
    TransferFunctionFrequencyResponseAnalyzer,
    TransferFunctionFrequencyResponseStatus,
)


def _reduced(
    numerator: sp.Expr,
    denominator: sp.Expr,
    *,
    parameters: frozenset[str] = frozenset(),
    exclusion: sp.Expr | None = None,
) -> ReducedTransferFunction:
    factory = PolynomialFactory()
    numerator_value = factory.create(
        ExactExpression._from_sympy(numerator),
        declared_parameter_names=parameters,
    ).value
    denominator_value = factory.create(
        ExactExpression._from_sympy(denominator),
        declared_parameter_names=parameters,
    ).value
    assert numerator_value is not None
    assert denominator_value is not None
    exclusions: tuple[TransferFunctionDomainExclusion, ...] = ()
    if exclusion is not None:
        exclusion_value = factory.create(
            ExactExpression._from_sympy(exclusion),
            declared_parameter_names=parameters,
        ).value
        assert exclusion_value is not None
        exclusions = (TransferFunctionDomainExclusion(exclusion_value, ("test",)),)
    return ReducedTransferFunction._create(
        variable_name="s",
        numerator=numerator_value,
        denominator=denominator_value,
        prerequisites=(),
        domain_exclusions=exclusions,
    )


def test_zero_response_has_zero_magnitude_minus_infinity_and_no_phase() -> None:
    s = sp.Symbol("s")
    result = TransferFunctionFrequencyResponseAnalyzer().analyze(
        _reduced(sp.Integer(0), s + 1),
        FrequencySampleSet((ExactRationalValue(1),)),
    )
    point = result.points[0]

    assert result.status is TransferFunctionFrequencyResponseStatus.COMPLETE
    assert point.status is FrequencyResponsePointStatus.ZERO_RESPONSE
    assert point.numerical_magnitude == "0"
    assert point.numerical_decibel is not None
    assert point.numerical_decibel.kind is DecibelValueKind.NEGATIVE_INFINITY
    assert point.numerical_phase_degrees is None
    assert point.diagnostics[0].code is (
        DiagnosticCode.FREQUENCY_RESPONSE_ZERO_RESPONSE
    )


def test_resonance_is_one_structured_singularity_between_finite_points() -> None:
    s = sp.Symbol("s")
    result = TransferFunctionFrequencyResponseAnalyzer().analyze(
        _reduced(sp.Integer(1), s**2 + 1),
        FrequencySampleSet(
            (
                ExactRationalValue(0),
                ExactRationalValue(1),
                ExactRationalValue(2),
            )
        ),
    )

    assert result.status is TransferFunctionFrequencyResponseStatus.PARTIAL
    assert tuple(point.status for point in result.points) == (
        FrequencyResponsePointStatus.DEFINED,
        FrequencyResponsePointStatus.SINGULAR,
        FrequencyResponsePointStatus.DEFINED,
    )
    singular = result.points[1]
    assert singular.exact_complex_value is None
    assert singular.numerical_magnitude is None
    assert singular.numerical_decibel is None
    assert singular.numerical_phase_degrees is None
    assert singular.diagnostics[0].code is DiagnosticCode.FREQUENCY_RESPONSE_SINGULAR


def test_retained_domain_exclusion_makes_cancelled_frequency_undefined() -> None:
    s = sp.Symbol("s")
    result = TransferFunctionFrequencyResponseAnalyzer().analyze(
        _reduced(sp.Integer(1), sp.Integer(1), exclusion=s),
        FrequencySampleSet((ExactRationalValue(0),)),
    )

    assert result.points[0].status is FrequencyResponsePointStatus.SINGULAR


def test_missing_parameter_is_symbolic_but_can_disappear_at_one_point() -> None:
    s, T = sp.symbols("s T")
    value = _reduced(
        sp.Integer(1),
        T * s + 1,
        parameters=frozenset({"T"}),
    )
    analyzer = TransferFunctionFrequencyResponseAnalyzer()
    symbolic = analyzer.analyze(
        value,
        FrequencySampleSet((ExactRationalValue(1, 2),)),
    )
    mixed = analyzer.analyze(
        value,
        FrequencySampleSet(
            (ExactRationalValue(0), ExactRationalValue(1, 2))
        ),
    )
    defined = analyzer.analyze(
        value,
        FrequencySampleSet((ExactRationalValue(1, 2),)),
        ParameterSubstitutions(
            (ParameterAssignment("T", ExactRationalValue(2)),)
        ),
    )

    assert symbolic.status is (
        TransferFunctionFrequencyResponseStatus.SYMBOLIC_UNDETERMINED
    )
    assert symbolic.points[0].status is (
        FrequencyResponsePointStatus.SYMBOLIC_UNDETERMINED
    )
    assert symbolic.diagnostics[0].code is (
        DiagnosticCode.FREQUENCY_RESPONSE_SYMBOLIC_UNDETERMINED
    )
    assert mixed.status is TransferFunctionFrequencyResponseStatus.PARTIAL
    assert mixed.points[0].exact_complex_value is not None
    assert mixed.points[0].exact_complex_value.canonical_text == "1"
    assert defined.points[0].exact_complex_value is not None
    assert defined.points[0].exact_complex_value.canonical_text == "1/2 - I/2"
