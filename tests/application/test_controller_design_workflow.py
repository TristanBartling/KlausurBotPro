"""Focused application tests for controller-design orchestration."""

import pytest

from klausurbotpro.application import ControllerDesignInputDraft, ControllerDesignWorkflowService
from klausurbotpro.domain import (
    ControllerDesignMethod,
    ControllerDesignStatus,
    ControllerType,
    ExactRationalValue,
)


def draft(method: ControllerDesignMethod, **values: str) -> ControllerDesignInputDraft:
    defaults = dict(
        task_name="Aufgabe Reglerauslegung",
        process_gain_text="1.8",
        dead_time_text="12",
        lag_time_text="72",
        critical_gain_text="1.62",
        critical_period_text="3",
    )
    defaults.update(values)
    return ControllerDesignInputDraft(method, ControllerType.PID, **defaults)


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
    assert result.latex.count(r"\section*{") == 1


def test_g2_workflow_exact_values_and_latex() -> None:
    result = ControllerDesignWorkflowService().run(
        draft(ControllerDesignMethod.ZIEGLER_NICHOLS_OPEN_LOOP)
    )
    assert result.status is ControllerDesignStatus.COMPLETE
    assert result.controller_parameters.k_i.exact == ExactRationalValue(1, 6)  # type: ignore[union-attr]
    assert "Keine Zwischenrundung" not in result.latex
    assert "Zwischenrundung" in result.latex


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
