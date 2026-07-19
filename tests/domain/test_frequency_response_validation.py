"""Defensive validation, resource limits, and architecture boundaries."""

from __future__ import annotations

import inspect

import pytest
import sympy as sp

import klausurbotpro.domain._frequency_response_evaluator as evaluator_module
import klausurbotpro.domain.transfer_function_frequency_response_analyzer as analyzer_module
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
)
from klausurbotpro.domain._frequency_response_numeric import (
    FrequencyResponseNumericError,
)


def _reduced(
    numerator: sp.Expr | None = None,
    denominator: sp.Expr | None = None,
    *,
    parameters: frozenset[str] = frozenset(),
) -> ReducedTransferFunction:
    factory = PolynomialFactory()
    numerator_value = factory.create(
        ExactExpression._from_sympy(
            sp.Integer(1) if numerator is None else numerator
        ),
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


def _analyze_samples(
    samples: FrequencySampleSet,
    *,
    limits: FrequencyResponseLimits | None = None,
) -> object:
    analyzer = (
        TransferFunctionFrequencyResponseAnalyzer()
        if limits is None
        else TransferFunctionFrequencyResponseAnalyzer(limits)
    )
    return analyzer.analyze(_reduced(), samples)


@pytest.mark.parametrize(
    "values",
    [
        (),
        (ExactRationalValue(-1),),
        (ExactRationalValue(1), ExactRationalValue(1)),
        (ExactRationalValue(2), ExactRationalValue(1)),
    ],
)
def test_invalid_frequency_sets_fail_before_partial_evaluation(
    values: tuple[ExactRationalValue, ...],
) -> None:
    result = _analyze_samples(FrequencySampleSet(values))

    assert result.status is TransferFunctionFrequencyResponseStatus.FAILED  # type: ignore[attr-defined]
    assert result.points == ()  # type: ignore[attr-defined]
    assert result.diagnostics[0].code is (  # type: ignore[attr-defined]
        DiagnosticCode.FREQUENCY_RESPONSE_INVALID_FREQUENCIES
    )


def test_frequency_count_and_integer_size_limits_are_structured() -> None:
    too_many = _analyze_samples(
        FrequencySampleSet(
            (ExactRationalValue(0), ExactRationalValue(1))
        ),
        limits=FrequencyResponseLimits(max_frequency_points=1),
    )
    too_large = _analyze_samples(
        FrequencySampleSet((ExactRationalValue(1000),)),
        limits=FrequencyResponseLimits(max_frequency_integer_digits=3),
    )

    for result, limit in (
        (too_many, "max_frequency_points"),
        (too_large, "max_frequency_integer_digits"),
    ):
        assert result.diagnostics[0].code is (  # type: ignore[attr-defined]
            DiagnosticCode.FREQUENCY_RESPONSE_LIMIT_EXCEEDED
        )
        assert result.diagnostics[0].technical_details == (("limit", limit),)  # type: ignore[attr-defined]


def test_unknown_and_manipulated_substitutions_are_rejected() -> None:
    s, T = sp.symbols("s T")
    value = _reduced(
        sp.Integer(1),
        T * s + 1,
        parameters=frozenset({"T"}),
    )
    samples = FrequencySampleSet((ExactRationalValue(1),))
    unknown = ParameterSubstitutions(
        (ParameterAssignment("K", ExactRationalValue(1)),)
    )
    assignment = ParameterAssignment("T", ExactRationalValue(1))
    manipulated = ParameterSubstitutions((assignment,))
    object.__setattr__(assignment.value, "numerator", 2)
    object.__setattr__(assignment.value, "denominator", 2)

    for substitutions in (unknown, manipulated):
        result = TransferFunctionFrequencyResponseAnalyzer().analyze(
            value,
            samples,
            substitutions,
        )
        assert result.status is TransferFunctionFrequencyResponseStatus.FAILED
        assert result.diagnostics[0].code is (
            DiagnosticCode.FREQUENCY_RESPONSE_INVALID_SUBSTITUTIONS
        )


def test_partial_exact_substitution_remains_pointwise_symbolic() -> None:
    s, K, T = sp.symbols("s K T")
    result = TransferFunctionFrequencyResponseAnalyzer().analyze(
        _reduced(
            K,
            T * s + 1,
            parameters=frozenset({"K", "T"}),
        ),
        FrequencySampleSet((ExactRationalValue(1),)),
        ParameterSubstitutions(
            (ParameterAssignment("K", ExactRationalValue(2)),)
        ),
    )

    assert result.status is (
        TransferFunctionFrequencyResponseStatus.SYMBOLIC_UNDETERMINED
    )


def test_manipulated_reduced_value_is_rejected_defensively() -> None:
    value = _reduced()
    object.__setattr__(value, "used_parameter_names", frozenset({"forged"}))

    result = TransferFunctionFrequencyResponseAnalyzer().analyze(
        value,
        FrequencySampleSet((ExactRationalValue(1),)),
    )

    assert result.status is TransferFunctionFrequencyResponseStatus.FAILED
    assert result.diagnostics[0].code is (
        DiagnosticCode.FREQUENCY_RESPONSE_INVALID_INPUT
    )


def test_expression_and_operation_limits_are_enforced() -> None:
    s = sp.Symbol("s")
    samples = FrequencySampleSet((ExactRationalValue(1),))
    expression_limited = TransferFunctionFrequencyResponseAnalyzer(
        FrequencyResponseLimits(max_expression_nodes=1)
    ).analyze(_reduced(s + 1), samples)
    operation_limited = TransferFunctionFrequencyResponseAnalyzer(
        FrequencyResponseLimits(max_intermediate_operations=1)
    ).analyze(_reduced(), samples)

    for result in (expression_limited, operation_limited):
        assert result.status is TransferFunctionFrequencyResponseStatus.FAILED
        assert result.diagnostics[0].code is (
            DiagnosticCode.FREQUENCY_RESPONSE_LIMIT_EXCEEDED
        )


def test_numeric_exponent_limit_is_a_structured_limit_failure() -> None:
    result = TransferFunctionFrequencyResponseAnalyzer(
        FrequencyResponseLimits(max_numeric_exponent_abs=1)
    ).analyze(
        _reduced(sp.Integer(100)),
        FrequencySampleSet((ExactRationalValue(1),)),
    )

    assert result.status is TransferFunctionFrequencyResponseStatus.FAILED
    assert result.diagnostics[0].code is (
        DiagnosticCode.FREQUENCY_RESPONSE_LIMIT_EXCEEDED
    )
    assert result.diagnostics[0].technical_details == (
        ("limit", "max_numeric_exponent_abs"),
    )


def test_numeric_failure_retains_exact_values_without_nan(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(*args: object, **kwargs: object) -> object:
        raise FrequencyResponseNumericError

    monkeypatch.setattr(
        evaluator_module,
        "numerical_frequency_response",
        fail,
    )
    result = TransferFunctionFrequencyResponseAnalyzer().analyze(
        _reduced(),
        FrequencySampleSet((ExactRationalValue(1),)),
    )
    point = result.points[0]

    assert result.status is TransferFunctionFrequencyResponseStatus.PARTIAL
    assert point.status is FrequencyResponsePointStatus.NUMERIC_UNDETERMINED
    assert point.exact_complex_value is not None
    assert point.numerical_magnitude is None
    assert point.diagnostics[0].code is (
        DiagnosticCode.FREQUENCY_RESPONSE_NUMERIC_UNDETERMINED
    )


@pytest.mark.parametrize("error_type", [MemoryError, RecursionError, OverflowError])
def test_resource_errors_are_structured(
    error_type: type[MemoryError | RecursionError | OverflowError],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(*args: object, **kwargs: object) -> object:
        raise error_type

    monkeypatch.setattr(
        analyzer_module,
        "validate_frequency_response_context",
        fail,
    )
    result = TransferFunctionFrequencyResponseAnalyzer().analyze(
        _reduced(),
        FrequencySampleSet((ExactRationalValue(1),)),
    )

    assert result.diagnostics[0].code is (
        DiagnosticCode.FREQUENCY_RESPONSE_RESOURCE_LIMIT_EXCEEDED
    )


def test_wrong_top_level_types_raise_type_error() -> None:
    analyzer = TransferFunctionFrequencyResponseAnalyzer()
    samples = FrequencySampleSet((ExactRationalValue(1),))
    value = _reduced()
    with pytest.raises(TypeError, match="ReducedTransferFunction"):
        analyzer.analyze(object(), samples)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="FrequencySampleSet"):
        analyzer.analyze(value, object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="ParameterSubstitutions"):
        analyzer.analyze(value, samples, object())  # type: ignore[arg-type]


def test_public_results_are_sympy_free_and_domain_only() -> None:
    result = TransferFunctionFrequencyResponseAnalyzer().analyze(
        _reduced(),
        FrequencySampleSet((ExactRationalValue(1),)),
    )
    point = result.points[0]
    public_values = (
        result,
        result.points,
        point,
        point.specialized_numerator,
        point.specialized_denominator,
        point.exact_complex_value,
        point.exact_real_part,
        point.exact_imaginary_part,
        point.exact_magnitude_squared,
    )
    source = inspect.getsource(analyzer_module) + inspect.getsource(
        evaluator_module
    )

    assert not any(isinstance(value, (sp.Basic, sp.Poly)) for value in public_values)
    assert "klausurbotpro.application" not in source
    assert "klausurbotpro.ui" not in source
    assert "klausurbotpro.parsing" not in source
    assert "sympify" not in source
    assert "parse_expr" not in source
