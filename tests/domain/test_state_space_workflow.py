"""Focused exact and safety tests for the state-space bridge."""

from __future__ import annotations

import pytest

from klausurbotpro.application import (
    StateSpaceInputDraft,
    StateSpaceStatus,
    StateSpaceTaskType,
    run_state_space_workflow,
)


def _matrix(
    a: str,
    b: str = "0;1",
    c: str = "1,0",
    d: str = "0",
    *,
    decision_parameters_text: str = "",
) -> StateSpaceInputDraft:
    return StateSpaceInputDraft(
        StateSpaceTaskType.STATE_SPACE_TO_TRANSFER_FUNCTION,
        matrix_a_text=a,
        vector_b_text=b,
        vector_c_text=c,
        scalar_d_text=d,
        decision_parameters_text=decision_parameters_text,
    )


@pytest.mark.parametrize(
    ("order", "coefficients", "expected_a"),
    [
        (1, ("2", "4"), "[[-1/2]]"),
        (2, ("2", "-3", "1"), "[[0, 1], [-2, 3]]"),
        (3, ("4", "-8", "0", "2"), "[[0, 1, 0], [0, 0, 1], [-2, 4, 0]]"),
        (
            4,
            ("1", "2", "3", "4", "5"),
            "[[0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1], [-1/5, -2/5, -3/5, -4/5]]",
        ),
    ],
)
def test_controllable_canonical_form_orders_one_to_four(
    order: int, coefficients: tuple[str, ...], expected_a: str
) -> None:
    result = run_state_space_workflow(
        StateSpaceInputDraft(
            StateSpaceTaskType.ODE_TO_CONTROLLABLE_CANONICAL,
            output_order=order,
            output_coefficient_texts=coefficients,
            input_coefficient_texts=("1",),
        )
    )

    assert result.succeeded, result.diagnostics
    assert result.input_model is not None
    assert result.input_model.matrix_a.canonical_text == expected_a
    assert all(check.passed for check in result.checks)


def test_s1_official_case_preserves_zero_coefficient_and_instability() -> None:
    result = run_state_space_workflow(
        StateSpaceInputDraft(
            StateSpaceTaskType.ODE_TO_CONTROLLABLE_CANONICAL,
            output_order=3,
            output_coefficient_texts=("4", "-8", "0", "2"),
            input_coefficient_texts=("2",),
        )
    )

    assert result.succeeded
    assert result.characteristic_polynomial is not None
    assert result.characteristic_polynomial.canonical_text == "s**3 - 4*s + 2"
    assert result.reduced_transfer_function is not None
    assert result.reduced_transfer_function.canonical_text == "1/(s**3 - 4*s + 2)"
    assert result.half_plane_counts == (1, 0, 2)
    assert "nicht asymptotisch stabil" in result.state_stability


@pytest.mark.parametrize(
    ("draft", "polynomial", "transfer", "stable"),
    [
        (
            StateSpaceInputDraft(
                StateSpaceTaskType.ODE_TO_CONTROLLABLE_CANONICAL,
                output_order=2,
                output_coefficient_texts=("2", "-3", "1"),
                input_coefficient_texts=("1",),
            ),
            "s**2 - 3*s + 2",
            "1/(s**2 - 3*s + 2)",
            False,
        ),
        (_matrix("0,1;-2,-3"), "s**2 + 3*s + 2", "1/(s**2 + 3*s + 2)", True),
        (_matrix("-1", "2", "3", "4"), "s + 1", "(4*s + 10)/(s + 1)", True),
    ],
)
def test_reference_cases_s2_to_s4(
    draft: StateSpaceInputDraft, polynomial: str, transfer: str, stable: bool
) -> None:
    result = run_state_space_workflow(draft)
    assert result.succeeded, result.diagnostics
    assert result.characteristic_polynomial is not None
    assert result.reduced_transfer_function is not None
    assert result.characteristic_polynomial.canonical_text == polynomial
    assert result.reduced_transfer_function.canonical_text == transfer
    assert ("nicht asymptotisch stabil" not in result.state_stability) is stable


def test_s5_reports_hidden_unstable_mode() -> None:
    result = run_state_space_workflow(_matrix("-1,0;0,1", "1;0"))

    assert result.succeeded
    assert result.reduced_transfer_function is not None
    assert result.reduced_transfer_function.canonical_text == "1/(s + 1)"
    assert tuple(value.canonical_text for value in result.hidden_state_modes) == ("1",)
    assert "versteckte instabile Mode bei s=1" in result.cancellation_report


def test_s6_uses_existing_hurwitz_parameter_region() -> None:
    result = run_state_space_workflow(_matrix("0,1;-k,-eta", decision_parameters_text="eta,k"))

    assert result.succeeded
    assert result.hurwitz_analysis is not None
    assert "k > 0" in result.hurwitz_analysis.combined_region
    assert "0 < eta" in result.hurwitz_analysis.combined_region


@pytest.mark.parametrize(
    ("draft", "message"),
    [
        (_matrix("1,2,3;4,5,6"), "quadratisch"),
        (_matrix("0,1;-2,-3", "1"), "2×1"),
        (_matrix("0,1;-2,-3", c="1"), "1×2"),
        (_matrix("-1", "2", "3", "4,5"), "skalar"),
    ],
)
def test_dimension_errors_are_safe_and_specific(draft: StateSpaceInputDraft, message: str) -> None:
    result = run_state_space_workflow(draft)
    assert result.status is StateSpaceStatus.INVALID_INPUT
    assert message in result.diagnostics[0]
    assert result.input_model is None
    assert not result.latex_source


def test_input_derivative_and_uncertain_leading_coefficient_are_rejected() -> None:
    derivative = run_state_space_workflow(
        StateSpaceInputDraft(
            StateSpaceTaskType.ODE_TO_CONTROLLABLE_CANONICAL,
            output_order=2,
            output_coefficient_texts=("1", "2", "3"),
            input_coefficient_texts=("1", "1"),
        )
    )
    uncertain = run_state_space_workflow(
        StateSpaceInputDraft(
            StateSpaceTaskType.ODE_TO_CONTROLLABLE_CANONICAL,
            output_order=2,
            output_coefficient_texts=("1", "2", "k"),
            input_coefficient_texts=("1",),
            decision_parameters_text="k",
        )
    )
    assert "nicht abgeleiteten Eingang" in derivative.diagnostics[0]
    assert "Nichtnullannahme" in uncertain.diagnostics[0]


def test_unsafe_cell_is_never_executed() -> None:
    result = run_state_space_workflow(_matrix("__import__('os'),1;-2,-3"))
    assert not result.succeeded
    assert "nicht erlaubt" in result.diagnostics[0] or "syntaktisch" in result.diagnostics[0]
