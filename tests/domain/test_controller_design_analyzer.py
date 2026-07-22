"""Exact source-table tests for controller design."""

from __future__ import annotations

import pytest

from klausurbotpro.domain import (
    ControllerType,
    ExactRationalValue,
    design_cohen_coon,
    design_ziegler_nichols_closed,
    design_ziegler_nichols_open,
)


def q(numerator: int, denominator: int = 1) -> ExactRationalValue:
    return ExactRationalValue(numerator, denominator)


def exacts(parameters: object) -> tuple[ExactRationalValue, ...]:
    return (parameters.k_p.exact, parameters.k_i.exact, parameters.k_d.exact)  # type: ignore[attr-defined,return-value]


def test_g2_ziegler_nichols_open_pid_is_exact() -> None:
    parameters = design_ziegler_nichols_open(ControllerType.PID, q(9, 5), q(12), q(72))
    assert exacts(parameters) == (q(4), q(1, 6), q(24))
    assert parameters.ideal_t_i.exact == q(24)  # type: ignore[union-attr]
    assert parameters.ideal_t_d.exact == q(6)  # type: ignore[union-attr]
    assert parameters.forms_identical


def test_g3_cohen_coon_pid_has_no_intermediate_rounding() -> None:
    ratio, parameters = design_cohen_coon(ControllerType.PID, q(9, 5), q(12), q(72))
    assert ratio == q(1, 6)
    assert exacts(parameters) == (q(49, 9), q(2107, 10692), q(392, 17))
    assert parameters.ideal_t_i.exact == q(1188, 43)  # type: ignore[union-attr]
    assert parameters.ideal_t_d.exact == q(72, 17)  # type: ignore[union-attr]


def test_g4_ziegler_nichols_closed_pid_is_exact() -> None:
    parameters = design_ziegler_nichols_closed(ControllerType.PID, q(81, 50), q(3))
    assert exacts(parameters) == (q(243, 250), q(81, 125), q(2187, 6250))
    assert parameters.ideal_t_i.exact == q(3, 2)  # type: ignore[union-attr]
    assert parameters.ideal_t_d.exact == q(9, 25)  # type: ignore[union-attr]


@pytest.mark.parametrize("controller_type", tuple(ControllerType))
def test_all_open_loop_table_rows_are_positive(controller_type: ControllerType) -> None:
    parameters = design_ziegler_nichols_open(controller_type, q(2), q(1), q(4))
    assert parameters.k_p.exact.numerator > 0  # type: ignore[union-attr]
    assert parameters.forms_identical


@pytest.mark.parametrize("controller_type", tuple(ControllerType))
def test_all_closed_loop_table_rows_are_positive(controller_type: ControllerType) -> None:
    parameters = design_ziegler_nichols_closed(controller_type, q(2), q(5))
    assert parameters.k_p.exact.numerator > 0  # type: ignore[union-attr]
    assert parameters.forms_identical


@pytest.mark.parametrize("controller_type", tuple(ControllerType))
def test_all_cohen_coon_rows_are_positive(controller_type: ControllerType) -> None:
    _, parameters = design_cohen_coon(controller_type, q(2), q(1), q(4))
    assert parameters.k_p.exact.numerator > 0  # type: ignore[union-attr]
    assert parameters.forms_identical


def test_zn_open_pi_keeps_course_decimal_333() -> None:
    parameters = design_ziegler_nichols_open(ControllerType.PI, q(1), q(2), q(10))
    assert parameters.ideal_t_i.exact == q(333, 50)  # type: ignore[union-attr]


@pytest.mark.parametrize("dead,lag", ((q(1), q(2)), (q(3), q(5))))
def test_zn_open_rejects_source_boundary_and_beyond(
    dead: ExactRationalValue, lag: ExactRationalValue
) -> None:
    with pytest.raises(ValueError, match="outside_source_domain"):
        design_ziegler_nichols_open(ControllerType.PID, q(1), dead, lag)


def test_cohen_coon_accepts_just_below_two() -> None:
    ratio, _ = design_cohen_coon(ControllerType.PI, q(1), q(1999, 1000), q(1))
    assert ratio == q(1999, 1000)


def test_cohen_coon_rejects_ratio_two() -> None:
    with pytest.raises(ValueError, match="outside_source_domain"):
        design_cohen_coon(ControllerType.PID, q(1), q(2), q(1))


@pytest.mark.parametrize("method", (design_ziegler_nichols_open, design_cohen_coon))
def test_table_methods_reject_zero(method: object) -> None:
    with pytest.raises(ValueError, match="invalid_input"):
        method(ControllerType.P, q(0), q(1), q(4))  # type: ignore[operator]
