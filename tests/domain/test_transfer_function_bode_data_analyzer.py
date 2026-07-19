"""End-to-end behavior of the structured Bode-data projection."""

from __future__ import annotations

from decimal import Decimal
from importlib import import_module

import pytest
import sympy as sp

import klausurbotpro.domain._frequency_response_evaluator as evaluator_module
from klausurbotpro.domain import (
    BodeDataLimits,
    BodeDataStatus,
    DecibelValueKind,
    DiagnosticCode,
    ExactExpression,
    ExactRationalValue,
    FrequencyResponseLimits,
    FrequencyResponsePointStatus,
    FrequencySampleSet,
    LogFrequencyGridGenerator,
    LogFrequencyGridLimits,
    LogFrequencyGridRequest,
    LogFrequencyGridResult,
    ParameterAssignment,
    ParameterSubstitutions,
    PolynomialFactory,
    ReducedTransferFunction,
    TransferFunctionBodeDataAnalyzer,
    TransferFunctionFrequencyResponseAnalyzer,
    TransferFunctionFrequencyResponseResult,
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


def _grid(
    minimum: int = 1,
    maximum: int = 10,
    points_per_decade: int = 2,
    explicit: tuple[ExactRationalValue, ...] = (),
) -> LogFrequencyGridResult:
    return LogFrequencyGridGenerator().generate(
        LogFrequencyGridRequest(
            ExactRationalValue(minimum),
            ExactRationalValue(maximum),
            points_per_decade,
            explicit,
        )
    )


@pytest.mark.parametrize(
    ("numerator", "denominator", "expected_phase"),
    [
        (sp.Integer(1), sp.Symbol("s"), Decimal("-90")),
        (sp.Symbol("s"), sp.Integer(1), Decimal("90")),
        (sp.Integer(-2), sp.Integer(1), Decimal("180")),
    ],
)
def test_standard_elements_preserve_principal_phase(
    numerator: sp.Expr,
    denominator: sp.Expr,
    expected_phase: Decimal,
) -> None:
    result = TransferFunctionBodeDataAnalyzer().analyze(
        _reduced(numerator, denominator),
        _grid(),
    )

    assert result.status is BodeDataStatus.COMPLETE
    assert all(
        Decimal(point.principal_phase_degrees or "nan") == expected_phase
        for point in result.points
    )


def test_pt1_is_complete_and_reuses_all_phase_3a1_values() -> None:
    s = sp.Symbol("s")
    grid = _grid()
    result = TransferFunctionBodeDataAnalyzer().analyze(
        _reduced(sp.Integer(1), s + 1),
        grid,
    )

    assert result.status is BodeDataStatus.COMPLETE
    assert len(result.magnitude_segments) == 1
    assert len(result.phase_segments) == 1
    assert tuple(point.grid_point for point in result.points) == grid.points
    for point, response in zip(
        result.points,
        result.frequency_response_result.points,  # type: ignore[union-attr]
        strict=True,
    ):
        assert point.frequency_response_point is response
        assert point.evaluation_frequency == response.omega
        assert point.target_decimal is point.grid_point.target_decimal
        assert point.numerical_decibel is response.numerical_decibel
        assert point.principal_phase_degrees == response.numerical_phase_degrees


def test_complex_poles_multiple_decades_and_explicit_point_preserve_order() -> None:
    s = sp.Symbol("s")
    explicit = ExactRationalValue(3, 2)
    exact_inner = ExactRationalValue(10)
    grid = _grid(1, 100, 2, (explicit, exact_inner))
    result = TransferFunctionBodeDataAnalyzer().analyze(
        _reduced(sp.Integer(1), s**2 + s + 1),
        grid,
    )

    assert result.status is BodeDataStatus.COMPLETE
    assert tuple(point.evaluation_frequency for point in result.points) == tuple(
        point.evaluation_frequency for point in grid.points
    )
    explicit_point = next(
        point for point in result.points
        if point.evaluation_frequency == explicit
    )
    assert explicit_point.target_decimal.decimal_text == "1.5"
    assert explicit_point.grid_point.maximum_relative_error == ExactRationalValue(0)
    exact_matches = [
        point
        for point in result.points
        if point.evaluation_frequency == exact_inner
    ]
    assert len(exact_matches) == 1
    assert exact_matches[0].grid_point.maximum_relative_error == (
        ExactRationalValue(0)
    )


def test_zero_response_retains_negative_infinity_without_segments() -> None:
    s = sp.Symbol("s")
    result = TransferFunctionBodeDataAnalyzer().analyze(
        _reduced(sp.Integer(0), s + 1),
        _grid(),
    )

    assert result.status is BodeDataStatus.NO_PLOTTABLE_DATA
    assert not result.magnitude_segments
    assert not result.phase_segments
    assert all(
        point.frequency_response_point.status
        is FrequencyResponsePointStatus.ZERO_RESPONSE
        and point.numerical_decibel is not None
        and point.numerical_decibel.kind is DecibelValueKind.NEGATIVE_INFINITY
        and not point.magnitude_plottable
        and not point.phase_plottable
        for point in result.points
    )
    assert result.diagnostics[-1].code is (
        DiagnosticCode.BODE_DATA_NO_PLOTTABLE_DATA
    )


def test_singularity_splits_both_series_without_interpolation() -> None:
    s = sp.Symbol("s")
    result = TransferFunctionBodeDataAnalyzer().analyze(
        _reduced(sp.Integer(1), s**2 + 4),
        _grid(1, 10, 2, (ExactRationalValue(2),)),
    )

    assert result.status is BodeDataStatus.PARTIAL
    assert result.points[1].frequency_response_point.status is (
        FrequencyResponsePointStatus.SINGULAR
    )
    assert [(item.start_grid_index, item.end_grid_index) for item in (
        result.magnitude_segments
    )] == [(0, 0), (2, 3)]
    assert [(item.start_grid_index, item.end_grid_index) for item in (
        result.phase_segments
    )] == [(0, 0), (2, 3)]


def test_multiple_singularities_create_deterministic_segments() -> None:
    s = sp.Symbol("s")
    grid = _grid(
        1,
        10,
        4,
        (ExactRationalValue(2),),
    )
    result = TransferFunctionBodeDataAnalyzer().analyze(
        _reduced(sp.Integer(1), (s**2 + 1) * (s**2 + 4)),
        grid,
    )

    singular_indices = [
        index
        for index, point in enumerate(result.points)
        if point.frequency_response_point.status
        is FrequencyResponsePointStatus.SINGULAR
    ]
    assert singular_indices == [0, 2]
    assert result.status is BodeDataStatus.PARTIAL
    assert [
        (segment.start_grid_index, segment.end_grid_index)
        for segment in result.magnitude_segments
    ] == [(1, 1), (3, 5)]


def test_symbolic_and_mixed_statuses_follow_authoritative_matrix() -> None:
    s, K = sp.symbols("s K")
    symbolic = TransferFunctionBodeDataAnalyzer().analyze(
        _reduced(K, s + 1),
        _grid(),
    )
    mixed = TransferFunctionBodeDataAnalyzer().analyze(
        _reduced(K * (s**2 + 1) + 1, sp.Integer(1)),
        _grid(),
    )
    zero_mixed = TransferFunctionBodeDataAnalyzer().analyze(
        _reduced(s**2 + 1, sp.Integer(1)),
        _grid(),
    )

    assert symbolic.status is BodeDataStatus.SYMBOLIC_UNDETERMINED
    assert not symbolic.magnitude_segments
    assert mixed.status is BodeDataStatus.PARTIAL
    assert mixed.points[0].frequency_response_point.status is (
        FrequencyResponsePointStatus.DEFINED
    )
    assert any(
        point.frequency_response_point.status
        is FrequencyResponsePointStatus.SYMBOLIC_UNDETERMINED
        for point in mixed.points
    )
    assert zero_mixed.status is BodeDataStatus.PARTIAL


def test_only_numeric_undetermined_has_no_plottable_data(
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
    result = TransferFunctionBodeDataAnalyzer().analyze(
        _reduced(sp.Integer(1), s + 1),
        _grid(),
    )

    assert result.status is BodeDataStatus.NO_PLOTTABLE_DATA
    assert {
        point.frequency_response_point.status for point in result.points
    } == {FrequencyResponsePointStatus.NUMERIC_UNDETERMINED}
    assert not result.magnitude_segments


def test_phase_3a1_analyzer_is_called_exactly_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0
    original = TransferFunctionFrequencyResponseAnalyzer.analyze

    def counted(
        self: TransferFunctionFrequencyResponseAnalyzer,
        reduced: ReducedTransferFunction,
        frequencies: FrequencySampleSet,
        substitutions: ParameterSubstitutions | None = None,
        *,
        field: str | None = None,
    ) -> TransferFunctionFrequencyResponseResult:
        nonlocal calls
        calls += 1
        return original(
            self,
            reduced,
            frequencies,
            substitutions,
            field=field,
        )

    monkeypatch.setattr(
        TransferFunctionFrequencyResponseAnalyzer,
        "analyze",
        counted,
    )
    s = sp.Symbol("s")

    result = TransferFunctionBodeDataAnalyzer().analyze(
        _reduced(sp.Integer(1), s + 1),
        _grid(1, 100, 4),
    )

    assert result.succeeded
    assert len(result.points) > 2
    assert calls == 1


@pytest.mark.parametrize(
    ("argument", "replacement"),
    [
        ("reduced", object()),
        ("grid", object()),
        ("substitutions", object()),
        ("field", 3),
    ],
)
def test_wrong_top_level_types_raise_type_error(
    argument: str,
    replacement: object,
) -> None:
    s = sp.Symbol("s")
    values: dict[str, object] = {
        "reduced": _reduced(sp.Integer(1), s + 1),
        "grid": _grid(),
        "substitutions": None,
        "field": None,
    }
    values[argument] = replacement

    with pytest.raises(TypeError):
        TransferFunctionBodeDataAnalyzer().analyze(
            values["reduced"],  # type: ignore[arg-type]
            values["grid"],  # type: ignore[arg-type]
            values["substitutions"],  # type: ignore[arg-type]
            field=values["field"],  # type: ignore[arg-type]
        )


def test_invalid_substitution_and_phase_failure_are_value_free() -> None:
    s = sp.Symbol("s")
    result = TransferFunctionBodeDataAnalyzer().analyze(
        _reduced(sp.Integer(1), s + 1),
        _grid(),
        ParameterSubstitutions(
            (ParameterAssignment("unknown", ExactRationalValue(1)),)
        ),
        field="transfer_function",
    )

    assert result.status is BodeDataStatus.FAILED
    assert result.grid is None
    assert result.frequency_response_result is None
    assert not result.points
    assert result.diagnostics[-1].code is (
        DiagnosticCode.BODE_DATA_FREQUENCY_ANALYSIS_FAILED
    )


def test_grid_frequency_segment_diagnostic_and_decimal_limits_fail_structured() -> None:
    s = sp.Symbol("s")
    grid = _grid(1, 100, 4)
    too_many_points = TransferFunctionBodeDataAnalyzer(
        bode_limits=BodeDataLimits(max_grid_points=2)
    ).analyze(_reduced(sp.Integer(1), s + 1), grid)
    wrong_grid_limits = TransferFunctionBodeDataAnalyzer(
        grid_limits=LogFrequencyGridLimits(max_points_per_decade=1)
    ).analyze(_reduced(sp.Integer(1), s + 1), grid)
    segment_limit = TransferFunctionBodeDataAnalyzer(
        bode_limits=BodeDataLimits(max_magnitude_segments=1)
    ).analyze(
        _reduced(sp.Integer(1), (s**2 + 1) * (s**2 + 4)),
        _grid(1, 10, 4, (ExactRationalValue(2),)),
    )
    diagnostic_limit = TransferFunctionBodeDataAnalyzer(
        bode_limits=BodeDataLimits(max_diagnostics=1)
    ).analyze(_reduced(sp.Integer(0), s + 1), _grid())
    decimal_limit = TransferFunctionBodeDataAnalyzer(
        bode_limits=BodeDataLimits(max_plot_decimal_digits=2)
    ).analyze(_reduced(sp.Integer(1), s + 1), _grid())

    assert too_many_points.diagnostics[0].code is (
        DiagnosticCode.BODE_DATA_LIMIT_EXCEEDED
    )
    assert wrong_grid_limits.diagnostics[0].code is (
        DiagnosticCode.BODE_DATA_INVALID_GRID
    )
    assert segment_limit.diagnostics[0].code is (
        DiagnosticCode.BODE_DATA_LIMIT_EXCEEDED
    )
    assert diagnostic_limit.diagnostics[0].code is (
        DiagnosticCode.BODE_DATA_LIMIT_EXCEEDED
    )
    assert decimal_limit.diagnostics[0].code is (
        DiagnosticCode.BODE_DATA_LIMIT_EXCEEDED
    )


@pytest.mark.parametrize(
    ("bode_maximum", "frequency_maximum", "expected_limit"),
    [
        (2, 256, "max_grid_points"),
        (256, 2, "max_frequency_points"),
        (3, 2, "max_frequency_points"),
        (2, 2, "max_grid_points"),
    ],
)
def test_active_preanalysis_point_limit_is_reported_and_skips_phase_3a1(
    monkeypatch: pytest.MonkeyPatch,
    bode_maximum: int,
    frequency_maximum: int,
    expected_limit: str,
) -> None:
    calls = 0

    def forbidden_analysis(
        self: TransferFunctionFrequencyResponseAnalyzer,
        reduced: ReducedTransferFunction,
        frequencies: FrequencySampleSet,
        substitutions: ParameterSubstitutions | None = None,
        *,
        field: str | None = None,
    ) -> TransferFunctionFrequencyResponseResult:
        nonlocal calls
        calls += 1
        raise AssertionError("Phase 3A.1 must not run after a limit failure.")

    monkeypatch.setattr(
        TransferFunctionFrequencyResponseAnalyzer,
        "analyze",
        forbidden_analysis,
    )
    s = sp.Symbol("s")
    result = TransferFunctionBodeDataAnalyzer(
        frequency_limits=FrequencyResponseLimits(
            max_frequency_points=frequency_maximum
        ),
        bode_limits=BodeDataLimits(max_grid_points=bode_maximum),
    ).analyze(
        _reduced(sp.Integer(1), s + 1),
        _grid(1, 100, 2),
    )

    assert result.status is BodeDataStatus.FAILED
    assert result.diagnostics[0].code is DiagnosticCode.BODE_DATA_LIMIT_EXCEEDED
    assert result.diagnostics[0].technical_details == (
        ("limit", expected_limit),
    )
    assert calls == 0


def test_manipulated_reduced_and_handoff_fail_structured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    s = sp.Symbol("s")
    reduced = _reduced(sp.Integer(1), s + 1)
    object.__setattr__(reduced, "variable_name", "x")
    manipulated_reduced = TransferFunctionBodeDataAnalyzer().analyze(
        reduced,
        _grid(),
    )

    original = TransferFunctionFrequencyResponseAnalyzer.analyze

    def manipulated_response(
        self: TransferFunctionFrequencyResponseAnalyzer,
        value: ReducedTransferFunction,
        frequencies: FrequencySampleSet,
        substitutions: ParameterSubstitutions | None = None,
        *,
        field: str | None = None,
    ) -> TransferFunctionFrequencyResponseResult:
        response = original(
            self,
            value,
            frequencies,
            substitutions,
            field=field,
        )
        object.__setattr__(response, "points", tuple(reversed(response.points)))
        return response

    monkeypatch.setattr(
        TransferFunctionFrequencyResponseAnalyzer,
        "analyze",
        manipulated_response,
    )
    handoff = TransferFunctionBodeDataAnalyzer().analyze(
        _reduced(sp.Integer(1), s + 1),
        _grid(),
    )

    assert manipulated_reduced.status is BodeDataStatus.FAILED
    assert handoff.status is BodeDataStatus.FAILED
    assert handoff.diagnostics[0].code is DiagnosticCode.BODE_DATA_CONTEXT_MISMATCH


def test_equal_but_foreign_frequency_sample_set_fails_handoff(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = TransferFunctionFrequencyResponseAnalyzer.analyze

    def copied_sample_set(
        self: TransferFunctionFrequencyResponseAnalyzer,
        value: ReducedTransferFunction,
        frequencies: FrequencySampleSet,
        substitutions: ParameterSubstitutions | None = None,
        *,
        field: str | None = None,
    ) -> TransferFunctionFrequencyResponseResult:
        response = original(
            self,
            value,
            frequencies,
            substitutions,
            field=field,
        )
        assert response.frequencies is not None
        object.__setattr__(
            response,
            "frequencies",
            FrequencySampleSet(response.frequencies.frequencies),
        )
        return response

    monkeypatch.setattr(
        TransferFunctionFrequencyResponseAnalyzer,
        "analyze",
        copied_sample_set,
    )
    s = sp.Symbol("s")
    result = TransferFunctionBodeDataAnalyzer().analyze(
        _reduced(sp.Integer(1), s + 1),
        _grid(),
    )

    assert result.status is BodeDataStatus.FAILED
    assert result.diagnostics[0].code is DiagnosticCode.BODE_DATA_CONTEXT_MISMATCH


def test_manipulated_grid_and_resource_error_fail_structured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    s = sp.Symbol("s")
    grid = _grid()
    object.__setattr__(grid, "points", tuple(reversed(grid.points)))
    manipulated = TransferFunctionBodeDataAnalyzer().analyze(
        _reduced(sp.Integer(1), s + 1),
        grid,
    )

    module = import_module(
        "klausurbotpro.domain.transfer_function_bode_data_analyzer"
    )

    def exhaust_resources(*args: object, **kwargs: object) -> None:
        raise MemoryError

    monkeypatch.setattr(module, "validate_bode_input_grid", exhaust_resources)
    exhausted = TransferFunctionBodeDataAnalyzer().analyze(
        _reduced(sp.Integer(1), s + 1),
        _grid(),
    )

    assert manipulated.status is BodeDataStatus.FAILED
    assert manipulated.diagnostics[0].code is DiagnosticCode.BODE_DATA_INVALID_GRID
    assert exhausted.status is BodeDataStatus.FAILED
    assert exhausted.diagnostics[0].code is (
        DiagnosticCode.BODE_DATA_RESOURCE_LIMIT_EXCEEDED
    )


@pytest.mark.parametrize(
    ("function_name", "error_type"),
    [
        ("build_bode_segments", ValueError),
        ("derive_bode_data_status", TypeError),
    ],
)
def test_internal_programming_errors_are_not_masked_as_context_failures(
    monkeypatch: pytest.MonkeyPatch,
    function_name: str,
    error_type: type[Exception],
) -> None:
    module = import_module(
        "klausurbotpro.domain.transfer_function_bode_data_analyzer"
    )

    def fail_internally(*args: object, **kwargs: object) -> None:
        raise error_type("synthetic internal defect")

    monkeypatch.setattr(module, function_name, fail_internally)
    s = sp.Symbol("s")

    with pytest.raises(error_type, match="synthetic internal defect"):
        TransferFunctionBodeDataAnalyzer().analyze(
            _reduced(sp.Integer(1), s + 1),
            _grid(),
        )


def test_identical_inputs_are_deterministic() -> None:
    s = sp.Symbol("s")
    reduced = _reduced(sp.Integer(1), s + 1)
    grid = _grid(1, 100, 2)
    analyzer = TransferFunctionBodeDataAnalyzer()

    assert analyzer.analyze(reduced, grid) == analyzer.analyze(reduced, grid)


def test_constructor_requires_exact_limit_contracts() -> None:
    with pytest.raises(TypeError):
        TransferFunctionBodeDataAnalyzer(object())  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        TransferFunctionBodeDataAnalyzer(
            FrequencyResponseLimits(),
            object(),  # type: ignore[arg-type]
        )
    with pytest.raises(TypeError):
        TransferFunctionBodeDataAnalyzer(
            FrequencyResponseLimits(),
            LogFrequencyGridLimits(),
            object(),  # type: ignore[arg-type]
        )
