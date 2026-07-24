"""Focused application tests for controller-design orchestration."""

from dataclasses import replace

import pytest

from klausurbotpro.application import (
    ControllerDesignInputDraft,
    ControllerDesignWorkflowService,
    decide_p_phase_margin_outcome,
)
from klausurbotpro.domain import (
    ControllerDesignCandidateStatus,
    ControllerDesignMethod,
    ControllerDesignStatus,
    ControllerType,
    ExactRationalValue,
)


def draft(method: ControllerDesignMethod, **values: str) -> ControllerDesignInputDraft:
    return ControllerDesignInputDraft(
        method,
        ControllerType.PID,
        values.get("task_name", "Aufgabe Reglerauslegung"),
        process_gain_text=values.get("process_gain_text", "1.8"),
        dead_time_text=values.get("dead_time_text", "12"),
        lag_time_text=values.get("lag_time_text", "72"),
        critical_gain_text=values.get("critical_gain_text", "1.62"),
        critical_period_text=values.get("critical_period_text", "3"),
    )


def test_g1_uses_reused_frequency_reserve_and_nyquist_kernels() -> None:
    result = ControllerDesignWorkflowService().run(
        ControllerDesignInputDraft(
            ControllerDesignMethod.P_PHASE_MARGIN,
            ControllerType.P,
            "SS 2025 Aufgabe 2e",
            "100",
            "s*(10*s+1)",
            (),
            "20",
            "1e-4",
            "1e2",
            "32",
        )
    )
    assert result.status is ControllerDesignStatus.COMPLETE
    candidate = result.candidates[0]
    assert candidate.target_frequency == pytest.approx(0.2747477419, rel=1e-8)
    assert candidate.positive_k_p == pytest.approx(0.008033086568, rel=1e-8)
    assert candidate.achieved_phase_margin_degrees == pytest.approx(20, abs=0.1)
    assert candidate.frequency_analysis.crossover_analysis is not None
    assert candidate.frequency_analysis.reserve_analysis is not None
    assert candidate.frequency_analysis.nyquist_analysis is not None
    assert candidate.status is ControllerDesignCandidateStatus.TARGET_MET
    assert result.input.task_name == "SS 2025 Aufgabe 2e"
    assert result.latex.count(r"\section*{") == 1
    assert r"\omega_\ast=0.274747741945" in result.latex
    assert r"G_{0,\mathrm{neu}}(s)=k_PG_0(s)" in result.latex
    assert "L_mathrm" not in result.latex
    assert result.latex.count(r"\[") == result.latex.count(r"\]")
    explanation = "Die Durchtritte und Reserven wurden vollständig neu berechnet."
    explanation_position = result.latex.index(explanation)
    assert result.latex.rfind(r"\]", 0, explanation_position) > result.latex.rfind(
        r"\[", 0, explanation_position
    )
    assert r"\par\noindent " + explanation in result.latex


def test_g2_workflow_exact_values_and_latex() -> None:
    result = ControllerDesignWorkflowService().run(
        draft(ControllerDesignMethod.ZIEGLER_NICHOLS_OPEN_LOOP)
    )
    assert result.status is ControllerDesignStatus.COMPLETE
    assert result.controller_parameters.k_i.exact == ExactRationalValue(1, 6)  # type: ignore[union-attr]
    assert "Keine Zwischenrundung" not in result.latex
    assert "Zwischenrundung" in result.latex


def test_blank_task_name_is_optional_and_adds_no_latex_heading() -> None:
    result = ControllerDesignWorkflowService().run(
        draft(ControllerDesignMethod.ZIEGLER_NICHOLS_OPEN_LOOP, task_name="   ")
    )
    assert result.status is ControllerDesignStatus.COMPLETE
    assert result.has_copyable_solution
    assert r"\section*{" not in result.latex


@pytest.mark.parametrize(
    "method",
    (ControllerDesignMethod.ZIEGLER_NICHOLS_OPEN_LOOP, ControllerDesignMethod.COHEN_COON),
)
def test_pi_latex_contains_no_derivative_zero_terms(method: ControllerDesignMethod) -> None:
    result = ControllerDesignWorkflowService().run(
        replace(draft(method), controller_type=ControllerType.PI)
    )
    assert result.status is ControllerDesignStatus.COMPLETE
    assert r"\[k_D=0\,\mathrm{s}\]" in result.latex
    assert "T_D" not in result.latex
    assert "+0" not in result.latex


def test_zn_open_pi_latex_uses_single_symbols_and_simplified_forms() -> None:
    result = ControllerDesignWorkflowService().run(
        replace(
            draft(ControllerDesignMethod.ZIEGLER_NICHOLS_OPEN_LOOP),
            controller_type=ControllerType.PI,
        )
    )
    assert r"\[K_S=1.8,\quad K_T=12,\quad T=72\]" in result.latex
    assert "K_SK_S" not in result.latex
    assert r"\[k_P=3\]" in result.latex
    assert r"\[k_I=\frac{25}{333}\,\mathrm{s^{-1}}\]" in result.latex
    assert r"\[T_I=39.96\,\mathrm{s}\]" in result.latex
    assert r"G_R(s)=3+\frac{25}{333s}" in result.latex
    assert r"G_R(s)=3\left(1+\frac{25}{999s}\right)" in result.latex
    assert "None" not in result.latex
    assert result.latex.count(r"\[") == result.latex.count(r"\]")


def test_cohen_coon_pid_latex_has_readable_exact_forms() -> None:
    result = ControllerDesignWorkflowService().run(draft(ControllerDesignMethod.COHEN_COON))
    assert r"\[K_S=1.8,\quad K_T=12,\quad T=72" in result.latex
    assert "K_SK_S" not in result.latex
    assert r"k_P=\frac{49}{9}" in result.latex
    assert r"k_I=\frac{2107}{10692}" in result.latex
    assert r"k_D=\frac{392}{17}" in result.latex
    assert r"T_I=\frac{1188}{43}\,\mathrm{s}" in result.latex
    assert r"T_D=\frac{72}{17}\,\mathrm{s}" in result.latex
    assert r"\frac{2107}{10692s}" in result.latex
    assert r"\frac{43}{1188s}" in result.latex
    assert "None" not in result.latex
    assert result.latex.count(r"\[") == result.latex.count(r"\]")


def test_closed_loop_symbols_use_braced_crit_subscripts() -> None:
    result = ControllerDesignWorkflowService().run(
        draft(ControllerDesignMethod.ZIEGLER_NICHOLS_CLOSED_LOOP)
    )
    assert r"K_{\mathrm{crit}}=1.62" in result.latex
    assert r"T_{\mathrm{crit}}=3" in result.latex
    assert "K_crit" not in result.latex
    assert "T_crit" not in result.latex


@pytest.mark.parametrize(
    ("statuses", "expected"),
    (
        ((ControllerDesignCandidateStatus.TARGET_NOT_MET,), ControllerDesignStatus.FAILED),
        (
            (
                ControllerDesignCandidateStatus.TARGET_MET,
                ControllerDesignCandidateStatus.TARGET_NOT_MET,
            ),
            ControllerDesignStatus.SELECTION_REQUIRED,
        ),
        (
            (
                ControllerDesignCandidateStatus.TARGET_NOT_MET,
                ControllerDesignCandidateStatus.TARGET_CROSSING_MET_GLOBAL_MARGIN_NOT_MET,
            ),
            ControllerDesignStatus.FAILED,
        ),
    ),
)
def test_p_outcome_decision_uses_successful_candidate_statuses(
    statuses: tuple[ControllerDesignCandidateStatus, ...],
    expected: ControllerDesignStatus,
) -> None:
    decision = decide_p_phase_margin_outcome(statuses)
    assert decision.status is expected
    assert decision.selected_candidate_index is None
    assert decision.diagnostic is not None


def test_p_outcome_decision_selects_only_successful_single_candidate() -> None:
    decision = decide_p_phase_margin_outcome((ControllerDesignCandidateStatus.TARGET_MET,))
    assert decision.status is ControllerDesignStatus.COMPLETE
    assert decision.selected_candidate_index == 0
    assert decision.diagnostic is None


def test_g3_workflow_preserves_exact_fractions() -> None:
    result = ControllerDesignWorkflowService().run(draft(ControllerDesignMethod.COHEN_COON))
    assert result.controller_parameters.k_p.exact == ExactRationalValue(49, 9)  # type: ignore[union-attr]
    assert result.controller_parameters.k_i.exact == ExactRationalValue(2107, 10692)  # type: ignore[union-attr]
    assert result.latex.count(r"\section*{") == 1
    assert "49}{9" in result.latex


def test_g4_workflow_exact_values() -> None:
    result = ControllerDesignWorkflowService().run(
        draft(ControllerDesignMethod.ZIEGLER_NICHOLS_CLOSED_LOOP)
    )
    assert result.controller_parameters.k_p.exact == ExactRationalValue(243, 250)  # type: ignore[union-attr]
    assert result.controller_parameters.k_d.exact == ExactRationalValue(2187, 6250)  # type: ignore[union-attr]


def test_no_phase_target_root_has_no_stale_latex() -> None:
    result = ControllerDesignWorkflowService().run(
        ControllerDesignInputDraft(
            ControllerDesignMethod.P_PHASE_MARGIN,
            ControllerType.P,
            "Keine Wurzel",
            "1",
            "s+1",
            (),
            "10",
            "1e-4",
            "1e2",
            "32",
        )
    )
    assert result.status is ControllerDesignStatus.FAILED
    assert result.diagnostics[0].code == "NO_PHASE_TARGET_ROOT"
    assert result.latex == ""
    assert not result.has_copyable_solution


def test_time_unit_text_is_rejected() -> None:
    result = ControllerDesignWorkflowService().run(
        draft(ControllerDesignMethod.COHEN_COON, dead_time_text="12 s")
    )
    assert result.diagnostics[0].code == "UNIT_MISMATCH"
    assert result.latex == ""


def test_source_boundaries_are_rejected() -> None:
    zn = ControllerDesignWorkflowService().run(
        draft(ControllerDesignMethod.ZIEGLER_NICHOLS_OPEN_LOOP, dead_time_text="36")
    )
    cc = ControllerDesignWorkflowService().run(
        draft(ControllerDesignMethod.COHEN_COON, dead_time_text="144")
    )
    assert zn.diagnostics[0].code == "OUTSIDE_SOURCE_DOMAIN"
    assert cc.diagnostics[0].code == "OUTSIDE_SOURCE_DOMAIN"
    assert zn.latex == ""
    assert "OUTSIDE_SOURCE_DOMAIN" not in zn.diagnostics[0].message


def test_g2_contract_orders_formula_substitution_exact_and_approximation() -> None:
    result = ControllerDesignWorkflowService().run(
        draft(ControllerDesignMethod.ZIEGLER_NICHOLS_OPEN_LOOP)
    )
    integral = next(item for item in result.formula_steps if item.quantity == "k_I")
    assert integral.general_plain == "k_I=k_P/T_I"
    assert integral.substituted_plain == "k_I=4/24"
    assert integral.exact_plain == "k_I=1/6"
    assert integral.approximation_plain == "k_I≈0.166667"
    joined = "\n".join(result.worked_steps)
    assert joined.index("Allgemeine Tabellenformeln") < joined.index("Einsetzen der Werte")
    assert joined.index("Exakte Reglerparameter") < joined.index("Numerische Näherungen")


def test_g2_validity_uses_course_dead_time_notation_and_concrete_values() -> None:
    result = ControllerDesignWorkflowService().run(
        draft(ControllerDesignMethod.ZIEGLER_NICHOLS_OPEN_LOOP)
    )
    validity = result.validity_steps[-1]
    assert validity.condition_plain == "K_T/T<1/2"
    assert "K_T/T=12/72=1/6<1/2" in validity.substitution_plain
    visible = "\n".join(result.worked_steps) + result.latex
    assert "r=L/T" not in visible
    assert r"\frac{K_T}{T}" in result.latex


def test_g3_exact_values_precede_numerical_approximations_and_no_5_4_rounding() -> None:
    result = ControllerDesignWorkflowService().run(draft(ControllerDesignMethod.COHEN_COON))
    assert tuple(item.exact_plain for item in result.result_steps) == (
        "49/9",
        "2107/10692",
        "392/17",
        "1188/43",
        "72/17",
    )
    assert "k_P=5.4" not in result.latex
    assert result.latex.index(r"k_P=\frac{49}{9}") < result.latex.index(
        r"k_P\approx 5.44444"
    )
    assert result.latex.count(r"\boxed") == 1


def test_g4_shows_both_positive_inputs_and_exact_terminating_decimals() -> None:
    result = ControllerDesignWorkflowService().run(
        draft(ControllerDesignMethod.ZIEGLER_NICHOLS_CLOSED_LOOP)
    )
    validity = " ".join(item.substitution_plain for item in result.validity_steps)
    assert "K_crit=1.62>0" in validity
    assert "T_crit=3 s>0" in validity
    assert tuple(item.exact_plain for item in result.result_steps) == (
        "0.972",
        "0.648",
        "0.34992",
        "1.5",
        "0.36",
    )


@pytest.mark.parametrize(
    ("method", "dead_time"),
    (
        (ControllerDesignMethod.ZIEGLER_NICHOLS_OPEN_LOOP, "4.99"),
        (ControllerDesignMethod.COHEN_COON, "19.99"),
    ),
)
def test_strict_source_ranges_accept_just_below_boundary(
    method: ControllerDesignMethod, dead_time: str
) -> None:
    result = ControllerDesignWorkflowService().run(
        draft(method, process_gain_text="1", dead_time_text=dead_time, lag_time_text="10")
    )
    assert result.status is ControllerDesignStatus.COMPLETE


def test_boundary_diagnostics_are_field_related_and_use_k_t() -> None:
    zn = ControllerDesignWorkflowService().run(
        draft(
            ControllerDesignMethod.ZIEGLER_NICHOLS_OPEN_LOOP,
            process_gain_text="1",
            dead_time_text="5",
            lag_time_text="10",
        )
    )
    cc = ControllerDesignWorkflowService().run(
        draft(
            ControllerDesignMethod.COHEN_COON,
            process_gain_text="1",
            dead_time_text="20",
            lag_time_text="10",
        )
    )
    assert "K_T/T < 0,5" in zn.diagnostics[0].message
    assert "K_T" in cc.diagnostics[0].message
    assert not zn.has_copyable_solution
    assert not cc.has_copyable_solution


def test_worked_steps_follow_required_table_order_and_separate_symbols() -> None:
    result = ControllerDesignWorkflowService().run(draft(ControllerDesignMethod.COHEN_COON))
    prefixes = tuple(step.split(":", 1)[0] for step in result.worked_steps)
    assert prefixes == (
        "Gegeben",
        "Gesucht",
        "Verfahren und Reglertyp",
        "Symbollegende",
        "Voraussetzungen",
        "Konkrete Gültigkeitsprüfung",
        "Allgemeine Tabellenformeln",
        "Einsetzen der Werte",
        "Exakte Reglerparameter",
        "Numerische Näherungen",
        "Parallele Reglerform",
        "Umrechnung in T_I und T_D",
        "Idealform",
        "Identitätskontrolle",
        "Eindeutiges Endergebnis",
    )
    assert "K_S ist die Streckenverstärkung" in result.worked_steps[3]
    assert "k_P ist der Proportionalbeiwert des Reglers" in result.worked_steps[3]
