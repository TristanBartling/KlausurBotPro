"""Pure exact table rules and canonical parallel-controller conversion."""

from __future__ import annotations

from fractions import Fraction

from klausurbotpro.domain.controller_design_contracts import (
    ControllerParameters,
    ControllerType,
    exact_scalar,
)
from klausurbotpro.domain.parameter_substitutions import ExactRationalValue


def design_ziegler_nichols_open(
    controller_type: ControllerType,
    process_gain: ExactRationalValue,
    dead_time: ExactRationalValue,
    lag_time: ExactRationalValue,
) -> ControllerParameters:
    ks, dead, lag = map(_fraction, (process_gain, dead_time, lag_time))
    _positive(ks, dead, lag)
    if dead * 2 >= lag:
        raise ValueError("outside_source_domain")
    if controller_type is ControllerType.P:
        return _parameters(controller_type, lag / (ks * dead), Fraction(0), Fraction(0))
    if controller_type is ControllerType.PI:
        kp = Fraction(9, 10) * lag / (ks * dead)
        return _parameters(controller_type, kp, kp / (Fraction(333, 100) * dead), Fraction(0))
    kp = Fraction(6, 5) * lag / (ks * dead)
    return _parameters(controller_type, kp, kp / (2 * dead), Fraction(1, 2) * kp * dead)


def design_ziegler_nichols_closed(
    controller_type: ControllerType,
    critical_gain: ExactRationalValue,
    critical_period: ExactRationalValue,
) -> ControllerParameters:
    gain, period = map(_fraction, (critical_gain, critical_period))
    _positive(gain, period)
    if controller_type is ControllerType.P:
        return _parameters(controller_type, Fraction(1, 2) * gain, Fraction(0), Fraction(0))
    if controller_type is ControllerType.PI:
        kp = Fraction(9, 20) * gain
        return _parameters(controller_type, kp, kp / (Fraction(17, 20) * period), Fraction(0))
    kp = Fraction(3, 5) * gain
    return _parameters(
        controller_type,
        kp,
        kp / (Fraction(1, 2) * period),
        Fraction(3, 25) * kp * period,
    )


def design_cohen_coon(
    controller_type: ControllerType,
    process_gain: ExactRationalValue,
    dead_time: ExactRationalValue,
    lag_time: ExactRationalValue,
) -> tuple[ExactRationalValue, ControllerParameters]:
    ks, dead, lag = map(_fraction, (process_gain, dead_time, lag_time))
    _positive(ks, dead, lag)
    ratio = dead / lag
    if ratio >= 2:
        raise ValueError("outside_source_domain")
    if controller_type is ControllerType.P:
        kp = lag / (ks * dead) * (1 + ratio / 3)
        parameters = _parameters(controller_type, kp, Fraction(0), Fraction(0))
    elif controller_type is ControllerType.PI:
        kp = Fraction(9, 10) / ks * lag / dead * (Fraction(9, 10) + ratio / 12)
        ki = kp * (9 + 20 * ratio) / (dead * (30 + 3 * ratio))
        parameters = _parameters(controller_type, kp, ki, Fraction(0))
    else:
        kp = Fraction(6, 5) / ks * lag / dead * (Fraction(27, 20) + ratio / 15)
        ki = kp * (13 + 8 * ratio) / (dead * (32 + 6 * ratio))
        kd = kp * dead * 4 / (11 + 2 * ratio)
        parameters = _parameters(controller_type, kp, ki, kd)
    return _exact(ratio), parameters


def _parameters(
    controller_type: ControllerType, kp: Fraction, ki: Fraction, kd: Fraction
) -> ControllerParameters:
    if kp <= 0 or ki < 0 or kd < 0:
        raise ValueError("Controller coefficients must satisfy the course convention.")
    ti = None if ki == 0 else kp / ki
    td = None if kd == 0 else kd / kp
    kp_text, ki_text, kd_text = map(_plain, (kp, ki, kd))
    parallel = rf"G_R(s)={_latex(kp)}+{_latex(ki)}\frac{{1}}{{s}}+{_latex(kd)}s"
    if controller_type is ControllerType.P:
        canonical = kp_text
        parallel = rf"G_R(s)={_latex(kp)}"
        ideal = parallel
    else:
        assert ti is not None
        canonical = f"{kp_text}+({ki_text})/s+({kd_text})*s"
        derivative = "" if td is None else rf"+{_latex(td)}s"
        ideal = (
            rf"G_R(s)={_latex(kp)}\left(1+"
            rf"\frac{{1}}{{\left({_latex(ti)}\right)s}}{derivative}\right)"
        )
    return ControllerParameters(
        controller_type,
        exact_scalar(_exact(kp)),
        exact_scalar(_exact(ki)),
        exact_scalar(_exact(kd)),
        None if ti is None else exact_scalar(_exact(ti)),
        None if td is None else exact_scalar(_exact(td)),
        canonical,
        parallel,
        ideal,
        True,
    )


def _positive(*values: Fraction) -> None:
    if any(value <= 0 for value in values):
        raise ValueError("invalid_input")


def _fraction(value: ExactRationalValue) -> Fraction:
    if type(value) is not ExactRationalValue:
        raise TypeError("Table values must be ExactRationalValue values.")
    return Fraction(value.numerator, value.denominator)


def _exact(value: Fraction) -> ExactRationalValue:
    return ExactRationalValue(value.numerator, value.denominator)


def _plain(value: Fraction) -> str:
    return (
        str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"
    )


def _latex(value: Fraction) -> str:
    return (
        str(value.numerator)
        if value.denominator == 1
        else rf"\frac{{{value.numerator}}}{{{value.denominator}}}"
    )


__all__ = [
    "design_cohen_coon",
    "design_ziegler_nichols_closed",
    "design_ziegler_nichols_open",
]
