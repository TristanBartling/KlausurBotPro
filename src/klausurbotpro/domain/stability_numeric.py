"""Method-neutral numerical pole control for symbolic stability methods."""

from __future__ import annotations

import sympy as sp
from mpmath.libmp.libhyper import NoConvergence  # type: ignore[import-untyped]

from klausurbotpro.domain.parameter_core_contracts import PolynomialDegreeCase
from klausurbotpro.domain.stability_contracts import (
    NumericalCheckStatus,
    NumericalPoleCheck,
)


def check_numeric_poles(
    case: PolynomialDegreeCase,
    parameter_point: tuple[tuple[str, str], ...] = (),
    *,
    expected_rhp_roots: int = 0,
) -> tuple[NumericalPoleCheck, int | None]:
    """Evaluate roots once and compare their RHP count with a method result."""
    substitutions = {sp.Symbol(name): sp.sympify(value) for name, value in parameter_point}
    variable = next(iter(case.polynomial._as_sympy().free_symbols - set(substitutions)), None)
    if variable is None:
        return NumericalPoleCheck(
            NumericalCheckStatus.NUMERICALLY_INCONCLUSIVE, parameter_point, (), ""
        ), None
    try:
        polynomial = sp.Poly(case.polynomial._as_sympy().subs(substitutions), variable)
        try:
            values = sp.nroots(polynomial, n=30, maxsteps=100)
        except NoConvergence:
            values = sp.nroots(polynomial, n=15, maxsteps=500)
        roots = tuple(complex(value) for value in values)
    except (sp.PolynomialError, ValueError, TypeError, NoConvergence):
        return NumericalPoleCheck(
            NumericalCheckStatus.NUMERICALLY_INCONCLUSIVE, parameter_point, (), ""
        ), None
    rhp_count = sum(value.real > 1e-9 for value in roots)
    has_axis_root = any(abs(value.real) <= 1e-9 for value in roots)
    maximum = max(value.real for value in roots)
    consistent = rhp_count == expected_rhp_roots and not (
        expected_rhp_roots == 0 and has_axis_root
    )
    check = NumericalPoleCheck(
        NumericalCheckStatus.CONSISTENT if consistent else NumericalCheckStatus.INCONSISTENT,
        parameter_point,
        tuple(f"{value.real:.10g}{value.imag:+.10g}j" for value in roots),
        f"{maximum:.10g}",
    )
    return check, rhp_count


__all__ = ["check_numeric_poles"]
