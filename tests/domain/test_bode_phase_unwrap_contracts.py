"""Public contract tests for optional Bode phase unwrapping."""

from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields
from pathlib import Path

import pytest

import klausurbotpro.domain as domain
from klausurbotpro.domain import (
    BodePhaseInterpolation,
    BodePhasePrincipalHandling,
    BodePhaseUnwrapAnalyzer,
    BodePhaseUnwrapLimits,
    BodePhaseUnwrapMetadata,
    BodePhaseUnwrapMethod,
    BodePhaseUnwrapResult,
    BodePhaseUnwrapSegmentBehavior,
    BodePhaseUnwrapStatus,
    BodePhaseUnwrapTieBreak,
    BodeUnwrappedPhasePoint,
    BodeUnwrappedPhaseSegment,
)


def test_required_contracts_are_exported_from_domain_facade() -> None:
    for name in (
        "BodePhaseUnwrapAnalyzer",
        "BodePhaseUnwrapLimits",
        "BodePhaseUnwrapStatus",
        "BodePhaseUnwrapMetadata",
        "BodeUnwrappedPhasePoint",
        "BodeUnwrappedPhaseSegment",
        "BodePhaseUnwrapResult",
    ):
        assert name in domain.__all__
        assert getattr(domain, name) is not None


@pytest.mark.parametrize(
    "contract",
    [
        BodePhaseUnwrapMetadata,
        BodeUnwrappedPhasePoint,
        BodeUnwrappedPhaseSegment,
        BodePhaseUnwrapResult,
    ],
)
def test_analyzer_controlled_contracts_lock_direct_construction(
    contract: type[object],
) -> None:
    with pytest.raises(TypeError):
        contract()


@pytest.mark.parametrize("name", [item.name for item in fields(BodePhaseUnwrapLimits)])
@pytest.mark.parametrize("value", [0, -1, True])
def test_every_limit_requires_a_positive_exact_int(name: str, value: object) -> None:
    with pytest.raises(ValueError):
        BodePhaseUnwrapLimits(**{name: value})  # type: ignore[arg-type]


def test_limits_are_frozen() -> None:
    limits = BodePhaseUnwrapLimits()
    with pytest.raises(FrozenInstanceError):
        limits.max_points = 1  # type: ignore[misc]


def test_metadata_is_exact_and_structured() -> None:
    metadata = BodePhaseUnwrapMetadata._create()
    assert metadata.phase_period_degrees == 360
    assert metadata.method is BodePhaseUnwrapMethod.NEAREST_CONTINUATION
    assert metadata.segment_behavior is (
        BodePhaseUnwrapSegmentBehavior.RESET_AT_EACH_SOURCE_SEGMENT
    )
    assert metadata.tie_break is BodePhaseUnwrapTieBreak.KEEP_PREVIOUS_OFFSET
    assert metadata.principal_phase_handling is (
        BodePhasePrincipalHandling.UNCHANGED
    )
    assert metadata.interpolation is BodePhaseInterpolation.NONE
    assert set(BodePhaseUnwrapStatus) == {
        BodePhaseUnwrapStatus.COMPLETE,
        BodePhaseUnwrapStatus.PARTIAL,
        BodePhaseUnwrapStatus.NO_PHASE_DATA,
        BodePhaseUnwrapStatus.FAILED,
    }


def test_analyzer_rejects_wrong_top_level_type() -> None:
    with pytest.raises(TypeError):
        BodePhaseUnwrapAnalyzer().analyze(object())  # type: ignore[arg-type]


def test_new_domain_modules_have_no_forbidden_layer_dependencies() -> None:
    domain_directory = Path(domain.__file__).parent
    module_names = (
        "_finite_decimal_exact.py",
        "_bode_phase_unwrap_algorithm.py",
        "_bode_phase_unwrap_status.py",
        "_bode_phase_unwrap_validation.py",
        "bode_phase_unwrap_contracts.py",
        "bode_phase_unwrap_analyzer.py",
    )
    forbidden = (
        "klausurbotpro.application",
        "klausurbotpro.ui",
        "matplotlib",
        "docs.reference",
        "TransferFunctionFrequencyResponseAnalyzer",
        "sympy",
    )
    for module_name in module_names:
        source = (domain_directory / module_name).read_text(encoding="utf-8")
        assert all(item not in source for item in forbidden)


def test_public_contract_module_contains_no_binary_float_literals() -> None:
    contract_path = (
        Path(domain.__file__).parent / "bode_phase_unwrap_contracts.py"
    )
    tree = ast.parse(contract_path.read_text(encoding="utf-8"))
    assert not any(
        isinstance(node, ast.Constant) and isinstance(node.value, float)
        for node in ast.walk(tree)
    )
