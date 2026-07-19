"""Integration behavior of optional Bode phase unwrapping."""

from __future__ import annotations

import pytest
import sympy as sp

import klausurbotpro.domain._frequency_response_evaluator as evaluator_module
from klausurbotpro.domain import (
    BodePhaseUnwrapAnalyzer,
    BodePhaseUnwrapLimits,
    BodePhaseUnwrapStatus,
    DiagnosticCode,
    ExactExpression,
    ExactRationalValue,
    FrequencyResponsePointStatus,
    LogFrequencyGridGenerator,
    LogFrequencyGridRequest,
    PolynomialFactory,
    ReducedTransferFunction,
    TransferFunctionBodeDataAnalyzer,
    TransferFunctionBodeDataResult,
    TransferFunctionFrequencyResponseAnalyzer,
)
from klausurbotpro.domain._frequency_response_numeric import (
    FrequencyResponseNumericError,
)


def _reduced(numerator: sp.Expr, denominator: sp.Expr) -> ReducedTransferFunction:
    s = sp.Symbol("s")
    numerator = sp.sympify(numerator)
    denominator = sp.sympify(denominator)
    parameters = frozenset(
        str(symbol)
        for symbol in numerator.free_symbols | denominator.free_symbols
        if symbol != s
    )
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
    return ReducedTransferFunction._create(
        variable_name="s",
        numerator=numerator_value,
        denominator=denominator_value,
        prerequisites=(),
        domain_exclusions=(),
    )


def _bode(
    numerator: sp.Expr,
    denominator: sp.Expr,
    *,
    minimum: int = 1,
    maximum: int = 10,
    points_per_decade: int = 2,
    explicit: tuple[ExactRationalValue, ...] = (),
) -> TransferFunctionBodeDataResult:
    grid = LogFrequencyGridGenerator().generate(
        LogFrequencyGridRequest(
            ExactRationalValue(minimum),
            ExactRationalValue(maximum),
            points_per_decade,
            explicit,
        )
    )
    return TransferFunctionBodeDataAnalyzer().analyze(
        _reduced(numerator, denominator),
        grid,
    )


def test_pt1_is_complete_and_preserves_every_source_identity_and_phase() -> None:
    s = sp.Symbol("s")
    source = _bode(sp.Integer(1), s + 1)
    result = BodePhaseUnwrapAnalyzer().analyze(source)

    assert result.status is BodePhaseUnwrapStatus.COMPLETE
    assert result.source_bode_data is source
    assert len(result.segments) == 1
    segment = result.segments[0]
    assert segment.source_segment is source.phase_segments[0]
    assert segment.points[0].phase_offset_turns == 0
    for point, source_point in zip(
        segment.points,
        source.phase_segments[0].points,
        strict=True,
    ):
        assert point.source_point is source_point
        assert point.principal_phase_degrees == (
            source_point.principal_phase_degrees
        )


def test_negative_gain_and_complex_poles_are_unwrapped_deterministically() -> None:
    s = sp.Symbol("s")
    negative = BodePhaseUnwrapAnalyzer().analyze(
        _bode(sp.Integer(-2), sp.Integer(1))
    )
    complex_poles_source = _bode(
        sp.Integer(1),
        (s + 1) ** 3,
        maximum=100,
        points_per_decade=4,
    )
    first = BodePhaseUnwrapAnalyzer().analyze(complex_poles_source)
    second = BodePhaseUnwrapAnalyzer().analyze(complex_poles_source)

    assert {
        point.unwrapped_phase_degrees
        for point in negative.segments[0].points
    } == {"180"}
    assert first == second
    assert any(
        point.phase_offset_turns != 0 for point in first.segments[0].points
    )


def test_singularity_keeps_segments_separate_and_resets_each_offset() -> None:
    s = sp.Symbol("s")
    source = _bode(
        sp.Integer(1),
        s**2 + 4,
        explicit=(ExactRationalValue(2),),
    )
    result = BodePhaseUnwrapAnalyzer().analyze(source)

    assert result.status is BodePhaseUnwrapStatus.PARTIAL
    assert len(result.segments) == 2
    assert len(result.segments[0].points) == 1
    assert all(
        segment.points[0].phase_offset_turns == 0
        for segment in result.segments
    )
    assert source.points[1].frequency_response_point.status is (
        FrequencyResponsePointStatus.SINGULAR
    )
    assert all(
        point.grid_index != 1
        for segment in result.segments
        for point in segment.points
    )


def test_zero_and_symbolic_sources_return_no_phase_data() -> None:
    s, K = sp.symbols("s K")
    for source in (
        _bode(sp.Integer(0), s + 1),
        _bode(K, s + 1),
    ):
        result = BodePhaseUnwrapAnalyzer().analyze(source)
        assert result.status is BodePhaseUnwrapStatus.NO_PHASE_DATA
        assert result.source_bode_data is source
        assert not result.segments
        assert result.metadata is not None
        assert result.diagnostics[-1].code is (
            DiagnosticCode.BODE_PHASE_UNWRAP_NO_PHASE_DATA
        )


def test_numeric_undetermined_source_returns_no_phase_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_numeric(*args: object, **kwargs: object) -> object:
        raise FrequencyResponseNumericError

    monkeypatch.setattr(
        evaluator_module,
        "numerical_frequency_response",
        fail_numeric,
    )
    s = sp.Symbol("s")
    source = _bode(sp.Integer(1), s + 1)
    result = BodePhaseUnwrapAnalyzer().analyze(source)
    assert result.status is BodePhaseUnwrapStatus.NO_PHASE_DATA


def test_projection_does_not_invoke_frequency_response_analysis(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    s = sp.Symbol("s")
    source = _bode(sp.Integer(1), s + 1)

    def forbidden(*args: object, **kwargs: object) -> object:
        raise AssertionError("frequency response must not be recalculated")

    monkeypatch.setattr(
        TransferFunctionFrequencyResponseAnalyzer,
        "analyze",
        forbidden,
    )
    assert BodePhaseUnwrapAnalyzer().analyze(source).succeeded


def test_source_and_unwrap_limits_produce_value_free_failures() -> None:
    s = sp.Symbol("s")
    singular = _bode(
        sp.Integer(1),
        s**2 + 4,
        explicit=(ExactRationalValue(2),),
    )
    pt1 = _bode(sp.Integer(1), s + 1)
    high_order = _bode(
        sp.Integer(1),
        (s + 1) ** 20,
        maximum=100,
        points_per_decade=20,
    )
    cases = (
        (singular, BodePhaseUnwrapLimits(max_phase_segments=1)),
        (pt1, BodePhaseUnwrapLimits(max_points=1)),
        (pt1, BodePhaseUnwrapLimits(max_decimal_digits=2)),
        (high_order, BodePhaseUnwrapLimits(max_absolute_phase_turns=1)),
        (
            _bode(sp.Integer(0), s + 1),
            BodePhaseUnwrapLimits(max_diagnostics=1),
        ),
    )
    for source, limits in cases:
        result = BodePhaseUnwrapAnalyzer(unwrap_limits=limits).analyze(source)
        assert result.status is BodePhaseUnwrapStatus.FAILED
        assert result.source_bode_data is None
        assert not result.segments
        assert result.metadata is None
        assert result.diagnostics[0].code is (
            DiagnosticCode.BODE_PHASE_UNWRAP_LIMIT_EXCEEDED
        )
