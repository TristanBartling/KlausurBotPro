"""Regression tests for the task-specific state-stability projection."""

from __future__ import annotations

import re

from klausurbotpro.application import (
    StateSpaceAnalysisTarget,
    StateSpaceInputDraft,
    StateSpaceTaskType,
    run_state_space_workflow,
)
from klausurbotpro.ui.state_space_presenter import StateSpacePresenter


def _stability_matrix(
    a: str,
    *,
    b: str = "0;1",
    c: str = "1,0",
    d: str = "0",
    parameters: str = "",
) -> StateSpaceInputDraft:
    return StateSpaceInputDraft(
        StateSpaceTaskType.STATE_SPACE_TO_TRANSFER_FUNCTION,
        analysis_target=StateSpaceAnalysisTarget.STATE_STABILITY,
        matrix_a_text=a,
        vector_b_text=b,
        vector_c_text=c,
        scalar_d_text=d,
        decision_parameters_text=parameters,
    )


def _reference_draft() -> StateSpaceInputDraft:
    return _stability_matrix(
        "0,1;-5/2,-1/6",
        b="0;1/12",
        c="1,0",
    )


def test_analysis_target_is_typed_and_full_analysis_is_default() -> None:
    draft = StateSpaceInputDraft(StateSpaceTaskType.STATE_SPACE_TO_TRANSFER_FUNCTION)

    assert draft.analysis_target is StateSpaceAnalysisTarget.FULL_ANALYSIS
    assert StateSpaceAnalysisTarget.STATE_STABILITY.value == "state_stability"


def test_ref_ss_01_has_exact_determinant_derivation_and_eigenvalues() -> None:
    result = run_state_space_workflow(_reference_draft())

    assert result.succeeded
    assert result.si_minus_a is not None
    assert result.si_minus_a.canonical_text == "[[s, -1], [5/2, s + 1/6]]"
    assert any(
        "s*(s + 1/6) - (-1)*5/2" in step for step in result.determinant_steps
    )
    assert result.determinant_steps[-1] == "p_A(s) = s^2 + s/6 + 5/2"
    assert {value.canonical_text for value, _ in result.exact_eigenvalues} == {
        "-1/12 - sqrt(359)*I/12",
        "-1/12 + sqrt(359)*I/12",
    }


def test_ref_ss_01_projects_real_parts_and_one_primary_stability_result() -> None:
    result = run_state_space_workflow(_reference_draft())
    presenter = StateSpacePresenter()
    presenter.calculate(_reference_draft())

    assert {item.real_part_text for item in result.real_part_checks} == {"-1/12"}
    assert {item.comparison for item in result.real_part_checks} == {"< 0"}
    assert result.state_stability == "Das Zustandsmodell ist asymptotisch stabil."
    assert presenter.state.summary.endswith("Das Zustandsmodell ist asymptotisch stabil.")
    assert "G(s)" not in presenter.state.summary
    assert presenter.state.transfer_function == ""


def test_ref_ss_01_latex_has_stability_sought_and_no_transfer_function() -> None:
    latex = run_state_space_workflow(_reference_draft()).latex_source

    sought = latex[latex.index(r"\textbf{Gesucht}") : latex.index(r"\textbf{Lösung}")]
    assert r"\operatorname{Re}(\lambda_i)" in sought
    assert "G(s)" not in sought
    assert r"sI-A=\left[\begin{matrix}s & -1\\\frac{5}{2} & s + \frac{1}{6}" in latex
    assert (
        r"s\cdot \left(s + \frac{1}{6}\right)"
        r"-\left(-1\right)\cdot \frac{5}{2}"
    ) in latex
    assert r"&=s^{2}+\frac{1}{6} s+\frac{5}{2}" in latex
    assert r"\lambda_{1,2}=- \frac{1}{12}\pm j\frac{\sqrt{359}}{12}" in latex
    assert latex.count(
        r"\boxed{\text{Das Zustandsmodell ist asymptotisch stabil.}}"
    ) == 1
    assert "G(s)" not in latex
    assert r"G_{\mathrm{red}}" not in latex


def test_positive_real_eigenvalue_is_named_as_violation() -> None:
    result = run_state_space_workflow(_stability_matrix("-1,0;0,1"))
    presenter = StateSpacePresenter()
    presenter.calculate(_stability_matrix("-1,0;0,1"))

    assert result.state_stability.startswith("Das Zustandsmodell ist nicht asymptotisch stabil")
    assert {(item.real_part_text, item.comparison) for item in result.real_part_checks} == {
        ("-1", "< 0"),
        ("1", "> 0"),
    }
    assert any("Re(1) = 1 > 0" in step for step in result.worked_steps)
    assert any(
        "lambda=1 verletzt das Kriterium Re(lambda) < 0" in step
        for step in result.worked_steps
    )
    assert "(s + 1)*(s - 1) - 0*0" in presenter.state.characteristic
    assert (
        r"\left(s + 1\right)\cdot \left(s - 1\right)-0\cdot 0"
        in result.latex_source
    )
    assert (
        r"\lambda=1\text{ verletzt das Kriterium }\operatorname{Re}(\lambda)<0."
        in result.latex_source
    )
    assert "lambda=1 verletzt das Kriterium" in presenter.state.eigenvalues_stability
    assert presenter.state.eigenvalues_stability.count(
        "Das Zustandsmodell ist nicht asymptotisch stabil"
    ) == 1
    assert re.search(r"\\\[\s*1\s*\\\]", result.latex_source) is None


def test_imaginary_axis_is_not_called_marginally_stable() -> None:
    result = run_state_space_workflow(_stability_matrix("0,-1;1,0"))
    presenter = StateSpacePresenter()
    presenter.calculate(_stability_matrix("0,-1;1,0"))

    assert result.state_stability.startswith("Das Zustandsmodell ist nicht asymptotisch stabil")
    assert {item.real_part_text for item in result.real_part_checks} == {"0"}
    assert {item.comparison for item in result.real_part_checks} == {r"\nless 0"}
    assert "grenzstabil" not in result.latex_source.lower()
    assert r"\nless0" in result.latex_source
    assert r"s\cdot s-1\cdot \left(-1\right)" in result.latex_source
    assert r"\lambda_{1,2}=\pm j" in result.latex_source
    assert r"\lambda_{1,2}=0\pm j1" not in result.latex_source
    assert presenter.state.eigenvalues_stability.find("0-1i") == -1
    assert presenter.state.eigenvalues_stability.find("0+1i") == -1
    assert "Numerische Eigenwerte: -i, +i" in presenter.state.eigenvalues_stability


def test_parameter_case_uses_hurwitz_conditions_without_numeric_eigenvalues() -> None:
    draft = _stability_matrix("0,1;-k,-eta", parameters="eta,k")
    result = run_state_space_workflow(draft)
    presenter = StateSpacePresenter()
    presenter.calculate(draft)

    assert result.succeeded
    assert result.exact_eigenvalues == ()
    assert result.numerical_eigenvalues == ()
    assert result.real_part_checks == ()
    assert result.hurwitz_analysis is not None
    assert "k > 0" in result.hurwitz_analysis.combined_region
    assert "0 < eta" in result.hurwitz_analysis.combined_region
    assert "G(s)" not in result.latex_source
    assert result.characteristic_polynomial_text == "s^2 + eta*s + k"
    assert result.determinant_steps[-1] == "p_A(s) = s^2 + eta*s + k"
    assert presenter.state.summary.startswith("Charakteristisches Polynom: s^2 + eta*s + k")
    assert "Eigenwerte parameterabhängig" in presenter.state.eigenvalues_stability
    assert "Hurwitz-Kriterium verwendet" in presenter.state.eigenvalues_stability
    assert presenter.state.eigenvalues_stability.count(
        "asymptotische Zustandsstabilität genau für"
    ) == 1
    assert "Eigenwerte parameterabhängig" in "\n".join(result.worked_steps)
    assert "Hurwitz-Kriterium verwendet" in "\n".join(result.worked_steps)
    assert r"&=s^{2}+\eta s+k" in result.latex_source
    assert r"\eta&>0" in result.latex_source
    assert "eta > 0" not in result.latex_source
    assert "keine kompakte exakte Darstellung verfügbar" not in result.latex_source
    assert "Eigenwerte parameterabhängig" in result.latex_source
    assert "Hurwitz-Kriterium verwendet" in result.latex_source


def test_ode_stability_target_ends_without_transfer_steps() -> None:
    draft = StateSpaceInputDraft(
        StateSpaceTaskType.ODE_TO_CONTROLLABLE_CANONICAL,
        analysis_target=StateSpaceAnalysisTarget.STATE_STABILITY,
        output_order=2,
        output_coefficient_texts=("5/2", "1/6", "1"),
        input_coefficient_texts=("1/12",),
    )
    result = run_state_space_workflow(draft)

    assert result.succeeded
    assert any("A_R=" in step for step in result.worked_steps)
    assert all("G(s)" not in step for step in result.worked_steps)
    assert "G(s)" not in result.latex_source
    sought = result.latex_source[
        result.latex_source.index(r"\textbf{Gesucht}") :
        result.latex_source.index(r"\textbf{Lösung}")
    ]
    assert "A_R" in sought


def test_ode_stability_uses_ar_in_determinant_labels() -> None:
    draft = StateSpaceInputDraft(
        StateSpaceTaskType.ODE_TO_CONTROLLABLE_CANONICAL,
        analysis_target=StateSpaceAnalysisTarget.STATE_STABILITY,
        output_order=2,
        output_coefficient_texts=("2", "3", "1"),
        input_coefficient_texts=("1",),
    )
    result = run_state_space_workflow(draft)
    presenter = StateSpacePresenter()
    presenter.calculate(draft)

    assert result.determinant_steps[0] == "sI-A_R = [[s, -1], [2, s + 3]]"
    assert "s*(s + 3) - (-1)*2" in presenter.state.characteristic
    assert presenter.state.characteristic.startswith("sI-A_R")
    assert any(step.startswith("sI-A_R") for step in result.worked_steps)
    assert r"sI-A_R=\left[\begin{matrix}s & -1\\2 & s + 3" in result.latex_source
    assert (
        r"s\cdot \left(s + 3\right)-\left(-1\right)\cdot 2"
        in result.latex_source
    )
    assert "G(s)" not in result.latex_source


def test_full_analysis_keeps_hidden_unstable_mode_and_transfer_output() -> None:
    result = run_state_space_workflow(
        StateSpaceInputDraft(
            StateSpaceTaskType.STATE_SPACE_TO_TRANSFER_FUNCTION,
            matrix_a_text="-1,0;0,1",
            vector_b_text="1;0",
            vector_c_text="1,0",
        )
    )

    assert result.analysis_target is StateSpaceAnalysisTarget.FULL_ANALYSIS
    assert result.reduced_transfer_function is not None
    assert result.reduced_transfer_function.canonical_text == "1/(s + 1)"
    assert "versteckte instabile Mode bei s=1" in result.cancellation_report
    assert r"\boxed{G(s)=\frac{1}{s + 1}}" in result.latex_source
