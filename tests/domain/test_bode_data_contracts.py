"""Public Bode contract, immutability, and architecture invariants."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from pathlib import Path

import pytest
import sympy as sp

import klausurbotpro.domain as domain
from klausurbotpro.domain import (
    BodeAxisMetadata,
    BodeDataLimits,
    BodeFrequencyQuantity,
    BodeFrequencyScale,
    BodeFrequencyUnit,
    BodeMagnitudeQuantity,
    BodeMagnitudeSegment,
    BodePhaseConvention,
    BodePhaseSegment,
    BodePhaseUnit,
    BodePlotPoint,
    ExactExpression,
    ExactRationalValue,
    LogFrequencyGridGenerator,
    LogFrequencyGridRequest,
    PolynomialFactory,
    ReducedTransferFunction,
    TransferFunctionBodeDataAnalyzer,
    TransferFunctionBodeDataResult,
)


def _result() -> TransferFunctionBodeDataResult:
    s = sp.Symbol("s")
    factory = PolynomialFactory()
    numerator = factory.create(
        ExactExpression._from_sympy(sp.Integer(1))
    ).value
    denominator = factory.create(ExactExpression._from_sympy(s + 1)).value
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
            ExactRationalValue(10),
            1,
        )
    )
    return TransferFunctionBodeDataAnalyzer().analyze(reduced, grid)


@pytest.mark.parametrize(
    "contract",
    [
        BodeAxisMetadata,
        BodePlotPoint,
        BodeMagnitudeSegment,
        BodePhaseSegment,
        TransferFunctionBodeDataResult,
    ],
)
def test_analyzer_controlled_contracts_reject_public_construction(
    contract: type[object],
) -> None:
    with pytest.raises(TypeError):
        contract()


@pytest.mark.parametrize("name", [field.name for field in fields(BodeDataLimits)])
@pytest.mark.parametrize("value", [0, -1, True])
def test_every_bode_limit_requires_a_positive_real_int(
    name: str,
    value: object,
) -> None:
    with pytest.raises(ValueError):
        BodeDataLimits(**{name: value})  # type: ignore[arg-type]


def test_axis_metadata_is_structured_and_canonical() -> None:
    metadata = _result().axis_metadata

    assert metadata is not None
    assert metadata.frequency_quantity is BodeFrequencyQuantity.ANGULAR_FREQUENCY
    assert metadata.frequency_unit is BodeFrequencyUnit.RAD_PER_SECOND
    assert metadata.frequency_scale is BodeFrequencyScale.LOGARITHMIC
    assert metadata.magnitude_quantity is BodeMagnitudeQuantity.DECIBEL
    assert metadata.phase_unit is BodePhaseUnit.DEGREE
    assert metadata.phase_convention is (
        BodePhaseConvention.PRINCIPAL_MINUS_180_EXCLUSIVE_TO_180_INCLUSIVE
    )


def test_public_contracts_are_frozen_and_contain_no_float_or_sympy_value() -> None:
    result = _result()
    point = result.points[0]

    with pytest.raises(FrozenInstanceError):
        point.phase_plottable = False  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.status = "failed"  # type: ignore[assignment,misc]

    def walk(value: object) -> None:
        assert type(value) is not float
        if isinstance(value, tuple):
            for item in value:
                walk(item)
        elif hasattr(value, "__dataclass_fields__"):
            if type(value).__module__.endswith("frequency_response_contracts"):
                return
            for field in fields(value):  # type: ignore[arg-type]
                walk(getattr(value, field.name))

    walk(result)


def test_all_public_bode_contracts_are_exported() -> None:
    names = {
        "BodeAxisMetadata",
        "BodeDataLimits",
        "BodeDataStatus",
        "BodeFrequencyQuantity",
        "BodeFrequencyScale",
        "BodeFrequencyUnit",
        "BodeMagnitudeQuantity",
        "BodeMagnitudeSegment",
        "BodePhaseConvention",
        "BodePhaseSegment",
        "BodePhaseUnit",
        "BodePlotPoint",
        "TransferFunctionBodeDataAnalyzer",
        "TransferFunctionBodeDataResult",
    }

    assert names <= set(domain.__all__)
    assert all(hasattr(domain, name) for name in names)


def test_bode_domain_has_no_application_ui_plot_or_reference_dependency() -> None:
    source_root = Path(__file__).parents[2] / "src" / "klausurbotpro" / "domain"
    files = (
        "bode_data_contracts.py",
        "transfer_function_bode_data_analyzer.py",
        "_bode_data_validation.py",
        "_bode_data_segmentation.py",
        "_bode_data_status.py",
    )
    combined = "\n".join(
        (source_root / filename).read_text(encoding="utf-8") for filename in files
    ).lower()

    for forbidden in (
        "klausurbotpro.application",
        "klausurbotpro.ui",
        "matplotlib",
        "docs/reference",
        "numpy.unwrap",
        "scipy",
    ):
        assert forbidden not in combined
