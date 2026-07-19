"""Exact deterministic phase-unwrapping algorithm tests."""

from __future__ import annotations

from decimal import ROUND_UP, localcontext

import pytest

from klausurbotpro.domain._bode_phase_unwrap_algorithm import (
    PhaseUnwrapAlgorithmLimit,
    unwrap_principal_phase_sequence,
)


def _unwrap(values: tuple[str, ...]) -> tuple[tuple[int, str], ...]:
    result = unwrap_principal_phase_sequence(
        values,
        max_absolute_phase_turns=20,
        max_decimal_digits=64,
    )
    return tuple(
        (value.phase_offset_turns, value.unwrapped_phase_degrees)
        for value in result
    )


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (("30", "30", "30"), ((0, "30"), (0, "30"), (0, "30"))),
        (("170", "-170"), ((0, "170"), (1, "190"))),
        (("-170", "170"), ((0, "-170"), (-1, "-190"))),
        (("170", "-10"), ((0, "170"), (0, "-10"))),
        (("-170", "10"), ((0, "-170"), (0, "10"))),
        (("170", "-170", "10"), ((0, "170"), (1, "190"), (1, "370"))),
        (
            ("-170", "170", "-10"),
            ((0, "-170"), (-1, "-190"), (-1, "-370")),
        ),
        (
            ("0", "120", "-120", "0", "120", "-120", "0"),
            ((0, "0"), (0, "120"), (1, "240"), (1, "360"), (1, "480"), (2, "600"), (2, "720")),
        ),
        (
            ("0", "-120", "120", "0", "-120", "120", "0"),
            (
                (0, "0"),
                (0, "-120"),
                (-1, "-240"),
                (-1, "-360"),
                (-1, "-480"),
                (-2, "-600"),
                (-2, "-720"),
            ),
        ),
        (("1.7E+2", "-1.7E+2"), ((0, "170"), (1, "190"))),
    ],
)
def test_exact_nearest_continuation_and_tie_break(
    source: tuple[str, ...],
    expected: tuple[tuple[int, str], ...],
) -> None:
    assert _unwrap(source) == expected


def test_result_is_independent_of_global_decimal_context() -> None:
    expected = _unwrap(("1.234567890123456789E+2", "-179.125"))
    with localcontext() as context:
        context.prec = 2
        context.rounding = ROUND_UP
        actual = _unwrap(("1.234567890123456789E+2", "-179.125"))
    assert actual == expected


def test_algorithm_is_deterministic() -> None:
    source = ("0", "120", "-120", "0")
    assert _unwrap(source) == _unwrap(source)


def test_offset_and_decimal_limits_are_structured() -> None:
    with pytest.raises(
        PhaseUnwrapAlgorithmLimit,
        match="max_absolute_phase_turns",
    ):
        unwrap_principal_phase_sequence(
            ("0", "120", "-120", "0", "120", "-120"),
            max_absolute_phase_turns=1,
            max_decimal_digits=64,
        )
    with pytest.raises(PhaseUnwrapAlgorithmLimit, match="max_decimal_digits"):
        unwrap_principal_phase_sequence(
            ("170",),
            max_absolute_phase_turns=1,
            max_decimal_digits=2,
        )


@pytest.mark.parametrize("bad_limit", [0, -1, True])
def test_algorithm_rejects_invalid_limits(bad_limit: object) -> None:
    with pytest.raises(ValueError):
        unwrap_principal_phase_sequence(
            ("0",),
            max_absolute_phase_turns=bad_limit,  # type: ignore[arg-type]
            max_decimal_digits=8,
        )
