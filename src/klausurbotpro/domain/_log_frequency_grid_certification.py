"""Exact rational certification of logarithmic grid approximations."""

from __future__ import annotations

from fractions import Fraction

from klausurbotpro.domain._log_frequency_grid_validation import (
    CertificationBudget,
)


def relative_error_limit(precision_digits: int) -> Fraction:
    """Return exact ``5 * 10**(-precision_digits)``."""

    return Fraction(5, 10**precision_digits)


def certifies_relative_error(
    *,
    candidate: Fraction,
    omega_min: Fraction,
    ratio: Fraction,
    target_index: int,
    interval_count: int,
    epsilon: Fraction,
    budget: CertificationBudget,
) -> bool:
    """Prove the requested relative error using rational powers only."""

    if (
        candidate <= 0
        or omega_min <= 0
        or ratio <= 1
        or not 0 < target_index < interval_count
        or not 0 < epsilon < 1
    ):
        return False
    target_power = ratio**target_index
    lower_base = candidate / (omega_min * (1 + epsilon))
    upper_base = candidate / (omega_min * (1 - epsilon))
    budget.step()
    lower_holds = lower_base**interval_count <= target_power
    budget.step()
    upper_holds = target_power <= upper_base**interval_count
    return lower_holds and upper_holds


__all__ = ["certifies_relative_error", "relative_error_limit"]
