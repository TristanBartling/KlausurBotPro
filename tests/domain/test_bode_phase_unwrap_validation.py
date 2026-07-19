"""Defensive trust-boundary tests for Bode phase unwrapping."""

from __future__ import annotations

import pytest
import sympy as sp

import klausurbotpro.domain.bode_phase_unwrap_analyzer as analyzer_module
from klausurbotpro.domain import (
    BodeDataLimits,
    BodeDataStatus,
    BodePhaseUnwrapAnalyzer,
    BodePhaseUnwrapLimits,
    BodePhaseUnwrapStatus,
    BodePlotPoint,
    Diagnostic,
    DiagnosticCode,
    DiagnosticSeverity,
    ExactExpression,
    ExactRationalValue,
    FrequencyResponseLimits,
    LogFrequencyGridGenerator,
    LogFrequencyGridLimits,
    LogFrequencyGridRequest,
    PolynomialFactory,
    ReducedTransferFunction,
    TransferFunctionBodeDataAnalyzer,
    TransferFunctionBodeDataResult,
)
from klausurbotpro.domain._bode_phase_unwrap_validation import (
    BodePhaseUnwrapFailure,
    validate_bode_phase_unwrap_result,
)
from klausurbotpro.domain.bode_phase_unwrap_contracts import (
    BodePhaseUnwrapResult,
)


def _source() -> TransferFunctionBodeDataResult:
    s = sp.Symbol("s")
    factory = PolynomialFactory()
    numerator = factory.create(ExactExpression._from_sympy(sp.Integer(1))).value
    denominator = factory.create(ExactExpression._from_sympy((s + 1) ** 3)).value
    assert numerator is not None
    assert denominator is not None
    reduced = ReducedTransferFunction._create(
        variable_name="s",
        numerator=numerator,
        denominator=denominator,
        prerequisites=(),
        domain_exclusions=(),
    )
    grid = LogFrequencyGridGenerator().generate(
        LogFrequencyGridRequest(
            ExactRationalValue(1),
            ExactRationalValue(100),
            4,
        )
    )
    return TransferFunctionBodeDataAnalyzer().analyze(reduced, grid)


def _validate(result: BodePhaseUnwrapResult) -> None:
    validate_bode_phase_unwrap_result(
        result,
        frequency_limits=FrequencyResponseLimits(),
        grid_limits=LogFrequencyGridLimits(),
        bode_limits=BodeDataLimits(),
        unwrap_limits=BodePhaseUnwrapLimits(),
    )


def test_unmodified_result_passes_independent_revalidation() -> None:
    _validate(BodePhaseUnwrapAnalyzer().analyze(_source()))


def test_manipulated_bode_source_returns_value_free_failed_result() -> None:
    source = _source()
    object.__setattr__(source.points[0], "principal_phase_degrees", "0")
    result = BodePhaseUnwrapAnalyzer().analyze(source)
    assert result.status is BodePhaseUnwrapStatus.FAILED
    assert result.source_bode_data is None
    assert result.diagnostics[0].code is (
        DiagnosticCode.BODE_PHASE_UNWRAP_INVALID_SOURCE
    )


@pytest.mark.parametrize(
    ("attribute", "replacement"),
    [
        ("phase_offset_turns", 99),
        ("unwrapped_phase_degrees", "123"),
        ("principal_phase_degrees", "0"),
        ("source_segment_index", 99),
        ("grid_index", 99),
    ],
)
def test_manipulated_unwrapped_point_is_rejected(
    attribute: str,
    replacement: object,
) -> None:
    result = BodePhaseUnwrapAnalyzer().analyze(_source())
    object.__setattr__(result.segments[0].points[1], attribute, replacement)
    with pytest.raises(BodePhaseUnwrapFailure):
        _validate(result)


def test_manipulated_segment_start_offset_and_tie_recurrence_are_rejected() -> None:
    result = BodePhaseUnwrapAnalyzer().analyze(_source())
    object.__setattr__(result.segments[0].points[0], "phase_offset_turns", 1)
    with pytest.raises(BodePhaseUnwrapFailure):
        _validate(result)


def test_cloned_and_foreign_source_points_are_rejected() -> None:
    result = BodePhaseUnwrapAnalyzer().analyze(_source())
    point = result.segments[0].points[0]
    source_point = point.source_point
    clone = BodePlotPoint._create(
        grid_point=source_point.grid_point,
        frequency_response_point=source_point.frequency_response_point,
        diagnostics=source_point.diagnostics,
    )
    object.__setattr__(point, "source_point", clone)
    with pytest.raises(BodePhaseUnwrapFailure):
        _validate(result)


@pytest.mark.parametrize(
    ("attribute", "replacement"),
    [
        ("segment_index", 99),
        ("start_grid_index", 99),
        ("end_grid_index", 99),
        ("source_segment", object()),
    ],
)
def test_manipulated_unwrapped_segment_is_rejected(
    attribute: str,
    replacement: object,
) -> None:
    result = BodePhaseUnwrapAnalyzer().analyze(_source())
    object.__setattr__(result.segments[0], attribute, replacement)
    with pytest.raises(BodePhaseUnwrapFailure):
        _validate(result)


@pytest.mark.parametrize(
    ("attribute", "replacement"),
    [
        ("status", BodePhaseUnwrapStatus.PARTIAL),
        ("source_bode_data", None),
        ("segments", ()),
        ("metadata", None),
        ("diagnostics", (object(),)),
    ],
)
def test_manipulated_result_is_rejected(
    attribute: str,
    replacement: object,
) -> None:
    result = BodePhaseUnwrapAnalyzer().analyze(_source())
    object.__setattr__(result, attribute, replacement)
    with pytest.raises(BodePhaseUnwrapFailure):
        _validate(result)


def test_failed_bode_source_is_rejected_without_retaining_it() -> None:
    source = TransferFunctionBodeDataResult._create(
        status=BodeDataStatus.FAILED,
        diagnostics=(
            Diagnostic(
                DiagnosticSeverity.ERROR,
                DiagnosticCode.BODE_DATA_INVALID_INPUT,
                "invalid",
            ),
        ),
    )
    result = BodePhaseUnwrapAnalyzer().analyze(source)
    assert result.status is BodePhaseUnwrapStatus.FAILED
    assert result.source_bode_data is None


def _failed_result(diagnostics: tuple[Diagnostic, ...]) -> BodePhaseUnwrapResult:
    result = BodePhaseUnwrapResult._create(
        status=BodePhaseUnwrapStatus.FAILED,
        diagnostics=(
            Diagnostic(
                DiagnosticSeverity.ERROR,
                DiagnosticCode.BODE_PHASE_UNWRAP_INVALID_SOURCE,
                "valid failure",
            ),
        ),
    )
    object.__setattr__(result, "diagnostics", diagnostics)
    return result


@pytest.mark.parametrize(
    "diagnostics",
    [
        (
            Diagnostic(
                DiagnosticSeverity.ERROR,
                DiagnosticCode.BODE_DATA_INVALID_INPUT,
                "foreign code",
            ),
        ),
        (
            Diagnostic(
                DiagnosticSeverity.ERROR,
                DiagnosticCode.BODE_PHASE_UNWRAP_NO_PHASE_DATA,
                "not an error code",
            ),
        ),
        (
            Diagnostic(
                DiagnosticSeverity.ERROR,
                DiagnosticCode.BODE_PHASE_UNWRAP_INVALID_SOURCE,
                "first",
            ),
            Diagnostic(
                DiagnosticSeverity.ERROR,
                DiagnosticCode.BODE_PHASE_UNWRAP_LIMIT_EXCEEDED,
                "second",
            ),
        ),
        (
            Diagnostic(
                DiagnosticSeverity.ERROR,
                DiagnosticCode.BODE_PHASE_UNWRAP_INVALID_SOURCE,
                "error",
            ),
            Diagnostic(
                DiagnosticSeverity.WARNING,
                DiagnosticCode.BODE_PHASE_UNWRAP_CONTEXT_MISMATCH,
                "warning",
            ),
        ),
        (
            Diagnostic(
                DiagnosticSeverity.WARNING,
                DiagnosticCode.BODE_PHASE_UNWRAP_INVALID_SOURCE,
                "warning only",
            ),
        ),
        (),
    ],
)
def test_failed_result_rejects_noncanonical_diagnostics(
    diagnostics: tuple[Diagnostic, ...],
) -> None:
    with pytest.raises(BodePhaseUnwrapFailure):
        _validate(_failed_result(diagnostics))


@pytest.mark.parametrize(
    "code",
    [
        DiagnosticCode.BODE_PHASE_UNWRAP_INVALID_SOURCE,
        DiagnosticCode.BODE_PHASE_UNWRAP_LIMIT_EXCEEDED,
        DiagnosticCode.BODE_PHASE_UNWRAP_RESOURCE_LIMIT_EXCEEDED,
    ],
)
def test_failed_result_accepts_supported_error_diagnostics(
    code: DiagnosticCode,
) -> None:
    result = _failed_result(
        (
            Diagnostic(
                DiagnosticSeverity.ERROR,
                code,
                "arbitrary nonempty message",
                technical_details=(("source", "test"),),
            ),
        )
    )
    _validate(result)


def test_manipulated_failed_result_is_independently_rejected() -> None:
    result = _failed_result(
        (
            Diagnostic(
                DiagnosticSeverity.ERROR,
                DiagnosticCode.BODE_PHASE_UNWRAP_INVALID_SOURCE,
                "valid",
            ),
        )
    )
    object.__setattr__(
        result,
        "diagnostics",
        (
            Diagnostic(
                DiagnosticSeverity.INFO,
                DiagnosticCode.BODE_PHASE_UNWRAP_NO_PHASE_DATA,
                "manipulated",
            ),
        ),
    )
    with pytest.raises(BodePhaseUnwrapFailure):
        _validate(result)


@pytest.mark.parametrize("error", [TypeError("bug"), ValueError("bug")])
def test_internal_programming_errors_are_not_masked(
    monkeypatch: pytest.MonkeyPatch,
    error: Exception,
) -> None:
    def broken(*args: object, **kwargs: object) -> object:
        raise error

    monkeypatch.setattr(
        analyzer_module,
        "unwrap_principal_phase_sequence",
        broken,
    )
    with pytest.raises(type(error), match="bug"):
        BodePhaseUnwrapAnalyzer().analyze(_source())


@pytest.mark.parametrize("error", [MemoryError(), RecursionError(), OverflowError()])
def test_resource_errors_become_structured_failures(
    monkeypatch: pytest.MonkeyPatch,
    error: BaseException,
) -> None:
    def exhausted(*args: object, **kwargs: object) -> object:
        raise error

    monkeypatch.setattr(
        analyzer_module,
        "validate_bode_phase_unwrap_source",
        exhausted,
    )
    result = BodePhaseUnwrapAnalyzer().analyze(_source())
    assert result.status is BodePhaseUnwrapStatus.FAILED
    assert result.diagnostics[0].code is (
        DiagnosticCode.BODE_PHASE_UNWRAP_RESOURCE_LIMIT_EXCEEDED
    )
