"""Defensive request, limit, collision, resource, and architecture tests."""

from __future__ import annotations

import inspect

import pytest
import sympy as sp

import klausurbotpro.domain._log_frequency_grid_validation as validation_module
import klausurbotpro.domain.log_frequency_grid_generator as generator_module
from klausurbotpro.domain import (
    DiagnosticCode,
    ExactRationalValue,
    LogFrequencyGridGenerator,
    LogFrequencyGridLimits,
    LogFrequencyGridRequest,
    LogFrequencyGridStatus,
)


@pytest.mark.parametrize(
    ("grid_request", "code"),
    [
        (
            LogFrequencyGridRequest(
                ExactRationalValue(0),
                ExactRationalValue(10),
                2,
            ),
            DiagnosticCode.LOG_FREQUENCY_GRID_INVALID_BOUNDS,
        ),
        (
            LogFrequencyGridRequest(
                ExactRationalValue(2),
                ExactRationalValue(1),
                2,
            ),
            DiagnosticCode.LOG_FREQUENCY_GRID_INVALID_BOUNDS,
        ),
        (
            LogFrequencyGridRequest(
                ExactRationalValue(1),
                ExactRationalValue(10),
                True,
            ),
            DiagnosticCode.LOG_FREQUENCY_GRID_INVALID_REQUEST,
        ),
    ],
)
def test_invalid_bounds_and_density_are_value_free_failures(
    grid_request: LogFrequencyGridRequest,
    code: DiagnosticCode,
) -> None:
    result = LogFrequencyGridGenerator().generate(grid_request)

    assert result.status is LogFrequencyGridStatus.FAILED
    assert result.request is None
    assert result.interval_count is None
    assert result.points == ()
    assert result.diagnostics[0].code is code


def test_wrong_top_level_types_raise_type_error() -> None:
    generator = LogFrequencyGridGenerator()
    request = LogFrequencyGridRequest(
        ExactRationalValue(1),
        ExactRationalValue(10),
        2,
    )
    with pytest.raises(TypeError, match="LogFrequencyGridRequest"):
        generator.generate(object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="field"):
        generator.generate(request, field=object())  # type: ignore[arg-type]


def test_decade_limit_is_checked_before_grid_generation() -> None:
    result = LogFrequencyGridGenerator(
        LogFrequencyGridLimits(max_decades=1)
    ).generate(
        LogFrequencyGridRequest(
            ExactRationalValue(1),
            ExactRationalValue(101),
            2,
        )
    )

    assert result.diagnostics[0].code is (
        DiagnosticCode.LOG_FREQUENCY_GRID_LIMIT_EXCEEDED
    )
    assert result.diagnostics[0].technical_details[0] == (
        "limit",
        "max_decades",
    )
    assert "mehr als 1 Dekaden" in result.diagnostics[0].message
    assert "Verkleinere den Frequenzbereich" in result.diagnostics[0].message


@pytest.mark.parametrize(
    ("limits", "grid_request", "limit_name"),
    [
        (
            LogFrequencyGridLimits(max_points_per_decade=1),
            LogFrequencyGridRequest(
                ExactRationalValue(1),
                ExactRationalValue(10),
                2,
            ),
            "max_points_per_decade",
        ),
        (
            LogFrequencyGridLimits(max_explicit_points=1),
            LogFrequencyGridRequest(
                ExactRationalValue(1),
                ExactRationalValue(10),
                2,
                (ExactRationalValue(2), ExactRationalValue(3)),
            ),
            "max_explicit_points",
        ),
        (
            LogFrequencyGridLimits(max_rational_integer_digits=3),
            LogFrequencyGridRequest(
                ExactRationalValue(1000),
                ExactRationalValue(2000),
                2,
            ),
            "max_rational_integer_digits",
        ),
    ],
)
def test_request_limits_are_structured_before_generation(
    limits: LogFrequencyGridLimits,
    grid_request: LogFrequencyGridRequest,
    limit_name: str,
) -> None:
    result = LogFrequencyGridGenerator(limits).generate(grid_request)

    assert result.status is LogFrequencyGridStatus.FAILED
    assert result.diagnostics[0].code is (
        DiagnosticCode.LOG_FREQUENCY_GRID_LIMIT_EXCEEDED
    )
    assert result.diagnostics[0].technical_details[0] == (
        "limit",
        limit_name,
    )


def test_points_per_decade_limit_names_input_limit_and_safe_correction() -> None:
    result = LogFrequencyGridGenerator(
        LogFrequencyGridLimits(max_points_per_decade=4)
    ).generate(
        LogFrequencyGridRequest(
            ExactRationalValue(1),
            ExactRationalValue(100),
            5,
        )
    )

    message = result.diagnostics[0].message
    assert "5 Punkte pro Dekade" in message
    assert "1 bis 100 rad/s" in message
    assert "maximal 4 Punkte pro Dekade" in message
    assert "Verwende höchstens 4" in message


def test_explicit_frequency_limit_names_count_limit_and_correction() -> None:
    result = LogFrequencyGridGenerator(
        LogFrequencyGridLimits(max_explicit_points=2)
    ).generate(
        LogFrequencyGridRequest(
            ExactRationalValue(1),
            ExactRationalValue(10),
            2,
            (
                ExactRationalValue(2),
                ExactRationalValue(3),
                ExactRationalValue(4),
            ),
        )
    )

    message = result.diagnostics[0].message
    assert "3 explizite Frequenzen" in message
    assert "maximal 2 explizite Frequenzen" in message
    assert "entferne nicht benötigte Stützstellen" in message


def test_combined_limit_failure_reports_all_problematic_inputs() -> None:
    result = LogFrequencyGridGenerator(
        LogFrequencyGridLimits(max_points_per_decade=4, max_decades=1)
    ).generate(
        LogFrequencyGridRequest(
            ExactRationalValue(1),
            ExactRationalValue(1000),
            5,
            (ExactRationalValue(2), ExactRationalValue(3)),
        )
    )

    message = result.diagnostics[0].message
    assert "5 Punkte pro Dekade" in message
    assert "1 bis 1000 rad/s" in message
    assert "2 expliziten Frequenzen" in message
    assert "höchstens 4" in message
    assert "bode_data" not in message


def test_total_point_limit_precedes_target_approximation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called = False

    def forbidden(*args: object, **kwargs: object) -> object:
        nonlocal called
        called = True
        raise AssertionError

    monkeypatch.setattr(
        generator_module,
        "approximate_logarithmic_target",
        forbidden,
    )
    result = LogFrequencyGridGenerator(
        LogFrequencyGridLimits(max_total_points=10)
    ).generate(
        LogFrequencyGridRequest(
            ExactRationalValue(1),
            ExactRationalValue(10),
            10,
        )
    )

    assert not called
    assert result.diagnostics[0].code is (
        DiagnosticCode.LOG_FREQUENCY_GRID_LIMIT_EXCEEDED
    )
    assert result.diagnostics[0].technical_details[0] == (
        "limit",
        "max_total_points",
    )
    assert "11 Punkte angefordert" in result.diagnostics[0].message
    assert "maximal 10" in result.diagnostics[0].message
    assert "höchstens 9 Punkte pro Dekade" in result.diagnostics[0].message


def test_generated_precision_collision_is_not_silently_deduplicated() -> None:
    result = LogFrequencyGridGenerator(
        LogFrequencyGridLimits(
            grid_precision_digits=2,
            max_points_per_decade=64,
        )
    ).generate(
        LogFrequencyGridRequest(
            ExactRationalValue(1),
            ExactRationalValue(2),
            64,
        )
    )

    assert result.status is LogFrequencyGridStatus.FAILED
    assert result.diagnostics[0].code is (
        DiagnosticCode.LOG_FREQUENCY_GRID_PRECISION_COLLISION
    )


def test_rounded_target_outside_exact_bounds_is_a_precision_collision() -> None:
    result = LogFrequencyGridGenerator(
        LogFrequencyGridLimits(
            grid_precision_digits=2,
            max_points_per_decade=1000,
        )
    ).generate(
        LogFrequencyGridRequest(
            ExactRationalValue(26, 25),
            ExactRationalValue(53, 50),
            1000,
        )
    )

    assert result.status is LogFrequencyGridStatus.FAILED
    assert result.diagnostics[0].code is (
        DiagnosticCode.LOG_FREQUENCY_GRID_PRECISION_COLLISION
    )


def test_manipulated_nested_request_is_rejected_structurally() -> None:
    request = LogFrequencyGridRequest(
        ExactRationalValue(1),
        ExactRationalValue(10),
        2,
    )
    object.__setattr__(request.omega_min, "numerator", 2)
    object.__setattr__(request.omega_min, "denominator", 2)

    result = LogFrequencyGridGenerator().generate(request)

    assert result.status is LogFrequencyGridStatus.FAILED
    assert result.request is None
    assert result.diagnostics[0].code is (
        DiagnosticCode.LOG_FREQUENCY_GRID_INVALID_REQUEST
    )


@pytest.mark.parametrize("error_type", [MemoryError, RecursionError, OverflowError])
def test_resource_errors_are_structured(
    error_type: type[MemoryError | RecursionError | OverflowError],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(*args: object, **kwargs: object) -> object:
        raise error_type

    monkeypatch.setattr(
        generator_module,
        "validate_log_frequency_grid_request",
        fail,
    )
    result = LogFrequencyGridGenerator().generate(
        LogFrequencyGridRequest(
            ExactRationalValue(1),
            ExactRationalValue(10),
            2,
        )
    )

    assert result.diagnostics[0].code is (
        DiagnosticCode.LOG_FREQUENCY_GRID_RESOURCE_LIMIT_EXCEEDED
    )


def test_public_values_have_no_float_or_sympy_and_module_is_domain_only() -> None:
    result = LogFrequencyGridGenerator().generate(
        LogFrequencyGridRequest(
            ExactRationalValue(1),
            ExactRationalValue(10),
            2,
        )
    )
    public_values = (
        result,
        result.request,
        result.points,
        result.points[1],
        result.points[1].target_decimal,
        result.points[1].evaluation_frequency,
        result.points[1].maximum_relative_error,
    )
    source = inspect.getsource(generator_module)

    assert not any(isinstance(value, (float, sp.Basic)) for value in public_values)
    assert "klausurbotpro.application" not in source
    assert "klausurbotpro.ui" not in source
    assert "klausurbotpro.parsing" not in source
    assert "ReducedTransferFunction" not in source
    assert "TransferFunctionFrequencyResponseAnalyzer" not in source


def test_interval_decision_source_uses_only_exact_rational_comparisons() -> None:
    function = validation_module.determine_interval_count
    source = inspect.getsource(function)
    referenced_names = frozenset(function.__code__.co_names)

    assert "Decimal" not in source
    assert "float" not in source
    assert referenced_names.isdisjoint({"Decimal", "float", "log", "log10"})
