"""Deterministic exact nearest-continuation phase unwrapping."""

from __future__ import annotations

from dataclasses import dataclass

from klausurbotpro.domain._finite_decimal_exact import (
    FiniteDecimal,
    FiniteDecimalError,
)

_PHASE_PERIOD_DEGREES = 360


@dataclass(frozen=True, slots=True)
class PhaseUnwrapAlgorithmLimit(ValueError):
    limit_name: str


@dataclass(frozen=True, slots=True)
class UnwrappedPhaseValue:
    phase_offset_turns: int
    unwrapped_phase_degrees: str


def unwrap_principal_phase_sequence(
    principal_phases: tuple[str, ...],
    *,
    max_absolute_phase_turns: int,
    max_decimal_digits: int,
) -> tuple[UnwrappedPhaseValue, ...]:
    if type(principal_phases) is not tuple or not principal_phases:
        raise ValueError("A phase segment requires a non-empty exact tuple.")
    if (
        type(max_absolute_phase_turns) is not int
        or max_absolute_phase_turns <= 0
        or type(max_decimal_digits) is not int
        or max_decimal_digits <= 0
    ):
        raise ValueError("Phase-unwrapping limits must be positive ints.")
    parsed = tuple(
        _parse_limited(value, max_decimal_digits) for value in principal_phases
    )
    result: list[UnwrappedPhaseValue] = [
        UnwrappedPhaseValue(0, parsed[0].canonical_text())
    ]
    previous_unwrapped = parsed[0]
    previous_offset = 0
    for principal in parsed[1:]:
        delta = previous_unwrapped - principal
        candidates = {
            delta.floor_divide_by_positive_int(_PHASE_PERIOD_DEGREES),
            delta.ceil_divide_by_positive_int(_PHASE_PERIOD_DEGREES),
            previous_offset,
        }
        offset = _nearest_offset(
            principal,
            previous_unwrapped,
            previous_offset,
            candidates,
        )
        if abs(offset) > max_absolute_phase_turns:
            raise PhaseUnwrapAlgorithmLimit("max_absolute_phase_turns")
        unwrapped = principal.add_integer(_PHASE_PERIOD_DEGREES * offset)
        try:
            unwrapped.validate_size(max_decimal_digits)
        except FiniteDecimalError as error:
            raise PhaseUnwrapAlgorithmLimit("max_decimal_digits") from error
        result.append(UnwrappedPhaseValue(offset, unwrapped.canonical_text()))
        previous_unwrapped = unwrapped
        previous_offset = offset
    return tuple(result)


def _parse_limited(value: str, max_decimal_digits: int) -> FiniteDecimal:
    try:
        return FiniteDecimal.parse(value, max_decimal_digits)
    except FiniteDecimalError as error:
        raise PhaseUnwrapAlgorithmLimit("max_decimal_digits") from error


def _nearest_offset(
    principal: FiniteDecimal,
    previous_unwrapped: FiniteDecimal,
    previous_offset: int,
    candidates: set[int],
) -> int:
    distances = {
        candidate: (
            principal.add_integer(_PHASE_PERIOD_DEGREES * candidate)
            - previous_unwrapped
        ).absolute()
        for candidate in candidates
    }
    first = next(iter(candidates))
    minimum = distances[first]
    minimal: list[int] = []
    for candidate in sorted(candidates):
        comparison = distances[candidate].compare(minimum)
        if comparison < 0:
            minimum = distances[candidate]
            minimal = [candidate]
        elif comparison == 0:
            minimal.append(candidate)
    if previous_offset in minimal:
        return previous_offset
    return min(minimal, key=lambda candidate: (abs(candidate), candidate))


__all__ = [
    "PhaseUnwrapAlgorithmLimit",
    "UnwrappedPhaseValue",
    "unwrap_principal_phase_sequence",
]
