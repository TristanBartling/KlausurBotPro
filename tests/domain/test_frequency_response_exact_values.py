"""Exact and numerical acceptance values for pointwise frequency response."""

from decimal import Decimal

import pytest
import sympy as sp

from klausurbotpro.domain import (
    DecibelValueKind,
    ExactExpression,
    ExactRationalValue,
    FrequencyResponsePointStatus,
    FrequencySampleSet,
    ParameterAssignment,
    ParameterSubstitutions,
    PolynomialFactory,
    ReducedTransferFunction,
    TransferFunctionFrequencyResponseAnalyzer,
    TransferFunctionFrequencyResponseStatus,
)


def _reduced(
    numerator: sp.Expr,
    denominator: sp.Expr | None = None,
    *,
    parameters: frozenset[str] = frozenset(),
) -> ReducedTransferFunction:
    factory = PolynomialFactory()
    numerator_value = factory.create(
        ExactExpression._from_sympy(numerator),
        declared_parameter_names=parameters,
    ).value
    denominator_value = factory.create(
        ExactExpression._from_sympy(
            sp.Integer(1) if denominator is None else denominator
        ),
        declared_parameter_names=parameters,
    ).value
    assert numerator_value is not None
    assert denominator_value is not None
    return ReducedTransferFunction._create(
        variable_name="s",
        numerator=numerator_value,
        denominator=denominator_value,
        prerequisites=(),
        domain_exclusions=(),
    )


def _analyze(
    value: ReducedTransferFunction,
    *frequencies: ExactRationalValue,
    substitutions: ParameterSubstitutions | None = None,
) -> object:
    return TransferFunctionFrequencyResponseAnalyzer().analyze(
        value,
        FrequencySampleSet(frequencies),
        substitutions,
    )


def test_pt1_at_zero_is_exact_unity_zero_db_and_zero_phase() -> None:
    s = sp.Symbol("s")
    result = _analyze(
        _reduced(sp.Integer(1), 2 * s + 1),
        ExactRationalValue(0),
    )
    point = result.points[0]  # type: ignore[attr-defined]

    assert result.status is TransferFunctionFrequencyResponseStatus.COMPLETE  # type: ignore[attr-defined]
    assert point.status is FrequencyResponsePointStatus.DEFINED
    assert point.exact_complex_value.canonical_text == "1"
    assert point.exact_real_part.canonical_text == "1"
    assert point.exact_imaginary_part.canonical_text == "0"
    assert point.exact_magnitude_squared.canonical_text == "1"
    assert point.numerical_magnitude == "1"
    assert point.numerical_decibel.decimal_value == "0"
    assert point.numerical_phase_degrees == "0"


def test_pt1_at_half_has_exact_complex_value_and_expected_numerics() -> None:
    s = sp.Symbol("s")
    result = _analyze(
        _reduced(sp.Integer(1), 2 * s + 1),
        ExactRationalValue(1, 2),
    )
    point = result.points[0]  # type: ignore[attr-defined]

    assert point.specialized_denominator.canonical_text == "1 + I"
    assert point.exact_complex_value.canonical_text == "1/2 - I/2"
    assert point.exact_real_part.canonical_text == "1/2"
    assert point.exact_imaginary_part.canonical_text == "-1/2"
    assert point.exact_magnitude_squared.canonical_text == "1/2"
    assert Decimal(point.numerical_magnitude) == pytest.approx(
        Decimal(2).sqrt() / 2,
        rel=Decimal("1e-35"),
    )
    assert Decimal(point.numerical_decibel.decimal_value) == pytest.approx(
        Decimal("-3.010299956639811952137388947244930267681"),
        rel=Decimal("1e-35"),
    )
    assert point.numerical_phase_degrees == "-45"


@pytest.mark.parametrize(
    ("numerator", "denominator", "complex_text", "phase"),
    [
        (
            sp.Integer(1),
            sp.Symbol("s"),
            "-I",
            "-90",
        ),
        (
            sp.Symbol("s"),
            sp.Integer(1),
            "I",
            "90",
        ),
        (
            sp.Integer(-1),
            sp.Integer(1),
            "-1",
            "180",
        ),
    ],
)
def test_integrator_differentiator_and_negative_gain_have_correct_phase(
    numerator: sp.Expr,
    denominator: sp.Expr,
    complex_text: str,
    phase: str,
) -> None:
    result = _analyze(
        _reduced(numerator, denominator),
        ExactRationalValue(1),
    )
    point = result.points[0]  # type: ignore[attr-defined]

    assert point.exact_complex_value.canonical_text == complex_text
    assert point.numerical_magnitude == "1"
    assert point.numerical_phase_degrees == phase


@pytest.mark.parametrize(
    ("numerator", "expected_phase"),
    [
        (sp.Symbol("s") - 1, "135"),
        (-sp.Symbol("s") - 1, "-135"),
        (1 - sp.Symbol("s"), "-45"),
    ],
)
def test_principal_phase_is_quadrant_correct(
    numerator: sp.Expr,
    expected_phase: str,
) -> None:
    result = _analyze(_reduced(numerator), ExactRationalValue(1))

    assert result.points[0].numerical_phase_degrees == expected_phase  # type: ignore[attr-defined]


def test_tutorium_pt1_i_and_d_reference_formulas_are_not_hardcoded() -> None:
    s, T = sp.symbols("s T")
    substitution = ParameterSubstitutions(
        (ParameterAssignment("T", ExactRationalValue(2)),)
    )
    omega = ExactRationalValue(3)
    pt1 = _analyze(
        _reduced(sp.Integer(1), T * s + 1, parameters=frozenset({"T"})),
        omega,
        substitutions=substitution,
    ).points[0]  # type: ignore[attr-defined]
    integrator = _analyze(
        _reduced(sp.Integer(1), T * s, parameters=frozenset({"T"})),
        omega,
        substitutions=substitution,
    ).points[0]  # type: ignore[attr-defined]
    differentiator = _analyze(
        _reduced(T * s, parameters=frozenset({"T"})),
        omega,
        substitutions=substitution,
    ).points[0]  # type: ignore[attr-defined]

    assert pt1.exact_magnitude_squared.canonical_text == "1/37"
    assert integrator.exact_magnitude_squared.canonical_text == "1/36"
    assert Decimal(integrator.numerical_magnitude) == pytest.approx(
        Decimal(1) / 6,
        rel=Decimal("1e-35"),
    )
    assert integrator.numerical_phase_degrees == "-90"
    assert differentiator.exact_magnitude_squared.canonical_text == "36"
    assert differentiator.numerical_magnitude == "6"
    assert differentiator.numerical_phase_degrees == "90"


def test_multiple_samples_preserve_exact_input_order_and_determinism() -> None:
    s = sp.Symbol("s")
    frequencies = (
        ExactRationalValue(0),
        ExactRationalValue(1, 2),
        ExactRationalValue(2),
    )
    analyzer = TransferFunctionFrequencyResponseAnalyzer()
    samples = FrequencySampleSet(frequencies)
    value = _reduced(sp.Integer(1), 2 * s + 1)

    first = analyzer.analyze(value, samples)
    second = analyzer.analyze(value, samples)

    assert tuple(point.omega for point in first.points) == frequencies
    assert first == second
    assert all(
        point.numerical_decibel is not None
        and point.numerical_decibel.kind is DecibelValueKind.FINITE
        for point in first.points
    )
