"""Primitive Bode contributions derived from a verified standard-element result."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from math import atan, atan2, degrees, log10

from klausurbotpro.domain.standard_element_bode_contracts import (
    StandardElementBodeResult,
    StandardElementFactor,
    StandardElementFactorKind,
    StandardElementFactorRole,
)


class BodeSketchMode(StrEnum):
    EXACT = "exact"
    ASYMPTOTIC = "asymptotic"
    ROUGH_EXAM = "rough_exam"


@dataclass(frozen=True, slots=True)
class StandardElementContribution:
    label: str
    factor: str
    element_type: str
    gain_share: str
    time_constant: str
    corner_frequency: str
    slope_change: str
    phase_change: str
    support: str
    magnitudes_db: tuple[float, ...]
    phases_degrees: tuple[float, ...]


def standard_element_contributions(
    result: StandardElementBodeResult,
    frequencies: tuple[float, ...],
    mode: BodeSketchMode,
) -> tuple[StandardElementContribution, ...]:
    """Evaluate primitive factors only; the total remains the existing Bode result."""
    if not result.supported or result.gain is None:
        return ()
    if not frequencies or any(value <= 0 for value in frequencies):
        raise ValueError("Positive frequencies are required.")
    gain = float(result.gain._as_sympy())
    rows = [
        StandardElementContribution(
            f"K = {result.gain.canonical_text}",
            result.gain.canonical_text,
            "P-Faktor",
            f"{20 * log10(abs(gain)):.12g} dB",
            "—",
            "keine Knickfrequenz",
            "0 dB/Dek",
            "0°" if gain > 0 else "-180°",
            "exakt" if mode is BodeSketchMode.EXACT else "näherungsweise",
            tuple(20 * log10(abs(gain)) for _ in frequencies),
            tuple(0.0 if gain > 0 else -180.0 for _ in frequencies),
        )
    ]
    exponent = result.origin_zero_multiplicity - result.origin_pole_multiplicity
    if exponent:
        is_integrator = exponent < 0
        count = abs(exponent)
        name = "I-Glied" if is_integrator else "D-Glied"
        label = name if count == 1 else f"{name} × {count}"
        rows.append(
            StandardElementContribution(
                label,
                f"s^{exponent}",
                name,
                "0 dB bei ω = 1 rad/s",
                "—",
                "keine Knickfrequenz",
                f"{20 * exponent:+d} dB/Dek",
                f"{90 * exponent:+d}°",
                "exakt" if mode is BodeSketchMode.EXACT else "näherungsweise",
                tuple(20 * exponent * log10(value) for value in frequencies),
                tuple(90.0 * exponent for _ in frequencies),
            )
        )
    for factor in (*result.zero_factors, *result.pole_factors):
        rows.append(_factor_contribution(factor, frequencies, mode))
    return tuple(rows)


def _factor_contribution(
    factor: StandardElementFactor,
    frequencies: tuple[float, ...],
    mode: BodeSketchMode,
) -> StandardElementContribution:
    omega = float(factor.corner_frequency._as_sympy())
    multiplicity = factor.multiplicity
    pole = factor.role is StandardElementFactorRole.POLE
    sign = -1 if pole else 1
    omega_text = factor.corner_frequency.canonical_text
    suffix = "" if multiplicity == 1 else f" × {multiplicity}"
    if factor.kind is StandardElementFactorKind.PT2:
        assert factor.damping_ratio is not None
        damping = float(factor.damping_ratio._as_sympy())
        label = f"PT2: ω₀ = {omega_text} rad/s, D = {factor.damping_ratio.canonical_text}{suffix}"
        magnitudes = tuple(
            _pt2_magnitude(value / omega, damping, multiplicity, mode)
            for value in frequencies
        )
        phases = tuple(
            _phase_second_order(value / omega, multiplicity, mode, damping)
            for value in frequencies
        )
        return StandardElementContribution(
            label,
            f"1/(1 + 2D·s/ω₀ + (s/ω₀)²)^{multiplicity}",
            "PT2-Glied",
            "0 dB (Tieffrequenz)",
            "—",
            f"ω₀ = {omega_text} rad/s",
            f"{-40 * multiplicity:+d} dB/Dek",
            f"{-180 * multiplicity:+d}°",
            "exakt" if mode is BodeSketchMode.EXACT else "näherungsweise",
            magnitudes,
            phases,
        )
    element_type = "PT1-Pol" if pole else "reelle Nullstelle / PD-Faktor"
    label = (
        f"PT1: ω_k = {omega_text} rad/s{suffix}"
        if pole
        else f"Nullstelle: ω_k = {omega_text} rad/s{suffix}"
    )
    magnitudes = tuple(
        _first_order_magnitude(value / omega, sign, multiplicity, mode)
        for value in frequencies
    )
    phases = tuple(
        _phase_first_order(value / omega, sign, multiplicity, mode)
        for value in frequencies
    )
    return StandardElementContribution(
        label,
        f"(1 + s/{omega_text})^{multiplicity}" + (" im Nenner" if pole else ""),
        element_type,
        "0 dB (Tieffrequenz)",
        f"T = 1/({omega_text}) s",
        f"ω_k = {omega_text} rad/s",
        f"{sign * 20 * multiplicity:+d} dB/Dek",
        f"{sign * 90 * multiplicity:+d}°",
        "exakt" if mode is BodeSketchMode.EXACT else "näherungsweise",
        magnitudes,
        phases,
    )


def _first_order_magnitude(x: float, sign: int, count: int, mode: BodeSketchMode) -> float:
    if mode is BodeSketchMode.EXACT:
        return sign * 10.0 * count * log10(1.0 + x * x)
    return sign * 20.0 * count * log10(max(1.0, x))


def _pt2_magnitude(x: float, damping: float, count: int, mode: BodeSketchMode) -> float:
    if mode is BodeSketchMode.EXACT:
        return -10.0 * count * log10((1.0 - x * x) ** 2 + (2.0 * damping * x) ** 2)
    return -40.0 * count * log10(max(1.0, x))


def _phase_first_order(x: float, sign: int, count: int, mode: BodeSketchMode) -> float:
    if mode is BodeSketchMode.EXACT:
        return sign * count * degrees(atan(x))
    if mode is BodeSketchMode.ROUGH_EXAM:
        return sign * 90.0 * count if x >= 1.0 else 0.0
    return sign * 45.0 * count * min(2.0, max(0.0, log10(x) + 1.0))


def _phase_second_order(x: float, count: int, mode: BodeSketchMode, damping: float) -> float:
    if mode is BodeSketchMode.EXACT:
        return -count * degrees(atan2(2.0 * damping * x, 1.0 - x * x))
    if mode is BodeSketchMode.ROUGH_EXAM:
        return -180.0 * count if x >= 1.0 else 0.0
    return -90.0 * count * min(2.0, max(0.0, log10(x) + 1.0))


__all__ = ["BodeSketchMode", "StandardElementContribution", "standard_element_contributions"]
