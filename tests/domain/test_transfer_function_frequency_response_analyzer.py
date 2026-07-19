"""Analyzer context, prerequisite, precision, and public behavior tests."""

from decimal import Decimal

import sympy as sp

from klausurbotpro.domain import (
    DiagnosticCode,
    ExactExpression,
    ExactRationalValue,
    FrequencyResponseLimits,
    FrequencyResponsePointStatus,
    FrequencySampleSet,
    ParameterAssignment,
    ParameterSubstitutions,
    PolynomialFactory,
    ReducedTransferFunction,
    TransferFunctionFrequencyResponseAnalyzer,
    TransferFunctionFrequencyResponseStatus,
    TransferFunctionPrerequisite,
    TransferFunctionPrerequisiteKind,
)


def _reduced_with_prerequisite(
    prerequisite: TransferFunctionPrerequisite,
) -> ReducedTransferFunction:
    s, K, T = sp.symbols("s K T")
    factory = PolynomialFactory()
    numerator = factory.create(
        ExactExpression._from_sympy(sp.Integer(1)),
        declared_parameter_names=frozenset({"K", "T"}),
    ).value
    denominator = factory.create(
        ExactExpression._from_sympy(K * s + T),
        declared_parameter_names=frozenset({"K", "T"}),
    ).value
    assert numerator is not None
    assert denominator is not None
    return ReducedTransferFunction._create(
        variable_name="s",
        numerator=numerator,
        denominator=denominator,
        prerequisites=(prerequisite,),
        domain_exclusions=(),
    )


def test_expression_nonzero_prerequisite_is_enforced_exactly() -> None:
    K = sp.Symbol("K")
    prerequisite = TransferFunctionPrerequisite(
        TransferFunctionPrerequisiteKind.EXPRESSION_NONZERO,
        (ExactExpression._from_sympy(K),),
        ("test",),
    )
    value = _reduced_with_prerequisite(prerequisite)
    result = TransferFunctionFrequencyResponseAnalyzer().analyze(
        value,
        FrequencySampleSet((ExactRationalValue(1),)),
        ParameterSubstitutions(
            (
                ParameterAssignment("K", ExactRationalValue(0)),
                ParameterAssignment("T", ExactRationalValue(1)),
            )
        ),
    )

    assert result.status is TransferFunctionFrequencyResponseStatus.FAILED
    assert result.diagnostics[0].code is (
        DiagnosticCode.FREQUENCY_RESPONSE_CONTEXT_MISMATCH
    )


def test_not_all_zero_prerequisite_remains_compound_and_can_be_satisfied() -> None:
    K, T = sp.symbols("K T")
    prerequisite = TransferFunctionPrerequisite(
        TransferFunctionPrerequisiteKind.NOT_ALL_ZERO,
        (
            ExactExpression._from_sympy(K - 1),
            ExactExpression._from_sympy(T),
        ),
        ("test",),
    )
    value = _reduced_with_prerequisite(prerequisite)
    analyzer = TransferFunctionFrequencyResponseAnalyzer()
    violated = analyzer.analyze(
        value,
        FrequencySampleSet((ExactRationalValue(1),)),
        ParameterSubstitutions(
            (
                ParameterAssignment("K", ExactRationalValue(1)),
                ParameterAssignment("T", ExactRationalValue(0)),
            )
        ),
    )
    satisfied = analyzer.analyze(
        value,
        FrequencySampleSet((ExactRationalValue(1),)),
        ParameterSubstitutions(
            (
                ParameterAssignment("K", ExactRationalValue(1)),
                ParameterAssignment("T", ExactRationalValue(2)),
            )
        ),
    )

    assert violated.status is TransferFunctionFrequencyResponseStatus.FAILED
    assert violated.diagnostics[0].code is (
        DiagnosticCode.FREQUENCY_RESPONSE_CONTEXT_MISMATCH
    )
    assert satisfied.points[0].status is FrequencyResponsePointStatus.DEFINED


def test_numeric_precision_is_configurable_and_deterministic() -> None:
    s = sp.Symbol("s")
    factory = PolynomialFactory()
    numerator = factory.create(ExactExpression._from_sympy(sp.Integer(1))).value
    denominator = factory.create(ExactExpression._from_sympy(s + 1)).value
    assert numerator is not None
    assert denominator is not None
    value = ReducedTransferFunction._create(
        variable_name="s",
        numerator=numerator,
        denominator=denominator,
        prerequisites=(),
        domain_exclusions=(),
    )
    samples = FrequencySampleSet((ExactRationalValue(1),))
    low = TransferFunctionFrequencyResponseAnalyzer(
        FrequencyResponseLimits(numerical_precision_digits=12)
    ).analyze(value, samples)
    high = TransferFunctionFrequencyResponseAnalyzer(
        FrequencyResponseLimits(numerical_precision_digits=40)
    ).analyze(value, samples)
    repeated = TransferFunctionFrequencyResponseAnalyzer(
        FrequencyResponseLimits(numerical_precision_digits=40)
    ).analyze(value, samples)

    assert low.points[0].numerical_magnitude != high.points[0].numerical_magnitude
    assert Decimal(low.points[0].numerical_magnitude) == Decimal(  # type: ignore[arg-type]
        "0.707106781187"
    )
    assert high == repeated
