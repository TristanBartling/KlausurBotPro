"""Focused T2 ODE workflow reference and signal tests."""

import pytest
import sympy as sp

from klausurbotpro.application import TimeDomainInputDraft, run_time_domain_workflow
from klausurbotpro.application.time_domain_workflow import format_ode_preview
from klausurbotpro.domain.time_domain_contracts import (
    ComputationStatus,
    InputSignalType,
    OdeAnalysisGoal,
    TimeDomainTaskType,
)


def _rf03(**changes: object) -> TimeDomainInputDraft:
    values: dict[str, object] = dict(
        task_type=TimeDomainTaskType.SOLVE_ODE,
        output_order=2,
        input_order=0,
        output_coefficient_texts=("1", "2", "1"),
        input_coefficient_texts=("1",),
        output_initial_texts=("0", "1"),
        ode_input_signal_type=InputSignalType.EXPONENTIAL,
        ode_signal_amplitude_text="9",
        ode_signal_rate_text="2",
    )
    values.update(changes)
    return TimeDomainInputDraft(**values)


def _reference_ode(**changes: object) -> TimeDomainInputDraft:
    values: dict[str, object] = dict(
        task_type=TimeDomainTaskType.SOLVE_ODE,
        output_order=2,
        input_order=0,
        output_coefficient_texts=("0", "4", "2"),
        input_coefficient_texts=("1",),
        output_initial_texts=("y0", "v0"),
        ode_input_signal_type=InputSignalType.IMAGE_EXPRESSION,
        input_expression_text="1/(s-8)^2",
    )
    values.update(changes)
    return TimeDomainInputDraft(**values)


def test_rf03_free_forced_pbz_and_all_ode_checks_pass() -> None:
    result = run_time_domain_workflow(_rf03())
    assert result.solution is not None and result.solution.ode_solution is not None
    data = result.solution.ode_solution
    s, t = sp.symbols("s t")
    assert sp.simplify(data.total_laplace._as_sympy() - (s + 7) / ((s + 1) ** 2 * (s - 2))) == 0
    assert (
        sp.simplify(
            data.total_time.expression._as_sympy()
            - (-sp.exp(-t) - 2 * t * sp.exp(-t) + sp.exp(2 * t))
        )
        == 0
    )
    assert data.verification.trusted
    assert result.solution.partial_fractions is not None
    assert "L{2*y'(t)} = 2*(s*Y(s) - y(0+)) = 2*s*Y(s)" in (
        result.presentation.laplace_transformation
    )
    assert "s*y(0+) - y'(0+)" in result.presentation.laplace_transformation
    assert "(s^2 + 2*s + 1)*Y(s) - 1 = U(s)" in result.presentation.image_equation
    assert r"\mathcal{L}\{2\,\dot{y}(t)\}" in result.presentation.latex_source
    _assert_no_internal_origin_names(result)


def test_default_ode_goal_preserves_complete_time_response() -> None:
    draft = _rf03()
    assert draft.ode_analysis_goal is OdeAnalysisGoal.TIME_RESPONSE
    result = run_time_domain_workflow(draft)
    assert result.solution is not None
    assert result.solution.time_function is not None
    assert result.solution.ode_solution is not None
    assert result.solution.ode_solution.analysis_goal is OdeAnalysisGoal.TIME_RESPONSE


def test_reference_image_equation_is_algebraically_correct() -> None:
    result = run_time_domain_workflow(
        _reference_ode(ode_analysis_goal=OdeAnalysisGoal.OUTPUT_LAPLACE)
    )
    assert result.solution is not None and result.solution.ode_solution is not None
    data = result.solution.ode_solution
    s, u = sp.symbols("s U")
    expected_generic = (
        u
        + 2 * s * sp.Symbol("y0")
        + 2 * sp.Symbol("v0")
        + 4 * sp.Symbol("y0")
    ) / (2 * s**2 + 4 * s)
    free = data.free_laplace
    forced = data.forced_laplace
    assert free is not None and forced is not None
    expected_concrete = expected_generic.subs(u, 1 / (s - 8) ** 2)
    assert (
        sp.simplify(
            free._as_sympy() + forced._as_sympy() - expected_concrete
        )
        == 0
    )
    assert (
        "2*s^2*Y(s) - 2*s*y0 - 2*v0"
        in result.presentation.laplace_transformation
    )
    image = data.image_equation
    y = sp.Symbol("Y")
    assert sp.simplify(
        image.left_expression._as_sympy()
        - ((2 * s**2 + 4 * s) * y - 2 * s * sp.Symbol("y0")
           - 2 * sp.Symbol("v0") - 4 * sp.Symbol("y0"))
    ) == 0
    assert sp.simplify(
        image.right_expression._as_sympy() - u
    ) == 0


def test_reference_image_equation_rendering_preserves_all_initial_value_signs() -> None:
    result = run_time_domain_workflow(
        _reference_ode(ode_analysis_goal=OdeAnalysisGoal.IMAGE_EQUATION)
    )
    expected_plain = (
        "(2*s^2 + 4*s)*Y(s) - 2*s*y0 - 2*v0 - 4*y0 = U(s)"
    )
    expected_latex = (
        r"\left(2 s^{2} + 4 s\right)Y(s)"
        r" - 2 s y_{0} - 2 v_{0} - 4 y_{0}=U(s)"
    )

    assert result.presentation.image_equation.splitlines()[0] == expected_plain
    assert rf"\[{expected_latex}\]" in result.presentation.latex_source
    assert rf"\[\boxed{{{expected_latex}}}\]" in result.presentation.latex_source
    assert "+ 2 v_{0} + 4 y_{0}" not in result.presentation.latex_source


def test_multiple_output_initial_values_use_aligned_latex() -> None:
    result = run_time_domain_workflow(
        _reference_ode(ode_analysis_goal=OdeAnalysisGoal.IMAGE_EQUATION)
    )

    assert r"\begin{aligned}" in result.presentation.latex_source
    assert r"y(0^+) &= y_{0} \\" in result.presentation.latex_source
    assert r"\dot{y}(0^+) &= v_{0}" in result.presentation.latex_source
    assert r"\end{aligned}" in result.presentation.latex_source


def test_single_output_initial_value_remains_compact_latex() -> None:
    result = run_time_domain_workflow(
        TimeDomainInputDraft(
            task_type=TimeDomainTaskType.SOLVE_ODE,
            output_order=1,
            input_order=0,
            output_coefficient_texts=("1", "1"),
            input_coefficient_texts=("1",),
            output_initial_texts=("y0",),
            ode_input_signal_type=InputSignalType.ZERO,
            ode_analysis_goal=OdeAnalysisGoal.IMAGE_EQUATION,
        )
    )

    assert r"\[y(0^+)=y_{0}\]" in result.presentation.latex_source
    assert r"\begin{aligned}" not in result.presentation.latex_source


def test_image_equation_goal_stops_before_solving_for_y(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_called(*args: object, **kwargs: object) -> object:
        raise AssertionError("solve_ode_image_equation must not be called")

    monkeypatch.setattr(
        "klausurbotpro.application.time_domain_workflow.solve_ode_image_equation",
        fail_if_called,
    )
    result = run_time_domain_workflow(
        _reference_ode(ode_analysis_goal=OdeAnalysisGoal.IMAGE_EQUATION)
    )
    assert result.solution is not None
    assert result.solution.output_laplace is None
    assert result.solution.rational_analysis is None
    assert result.solution.partial_fractions is None
    assert result.solution.time_function is None
    assert "Auflösen nach Y(s)" not in result.presentation.worked_steps
    assert r"\boxed{" in result.presentation.latex_source
    assert "transformierte Bildgleichung" in result.presentation.latex_source


def test_output_laplace_goal_stops_before_rational_pipeline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_called(*args: object, **kwargs: object) -> object:
        raise AssertionError("inverse_rational must not be called")

    monkeypatch.setattr(
        "klausurbotpro.application.time_domain_workflow.inverse_rational",
        fail_if_called,
    )
    result = run_time_domain_workflow(
        _reference_ode(ode_analysis_goal=OdeAnalysisGoal.OUTPUT_LAPLACE)
    )
    assert result.solution is not None and result.solution.output_laplace is not None
    assert result.solution.rational_analysis is None
    assert result.solution.partial_fractions is None
    assert result.solution.time_function is None
    assert "Partialbruchzerlegung" not in result.presentation.worked_steps
    assert r"\boxed{Y(s)=" in result.presentation.latex_source
    assert "time" not in result.presentation.visible_result_tabs


def test_partial_fraction_goal_stops_before_inverse_laplace(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_called(*args: object, **kwargs: object) -> object:
        raise AssertionError("_inverse_terms must not be called")

    monkeypatch.setattr(
        "klausurbotpro.domain.time_domain_analyzer._inverse_terms",
        fail_if_called,
    )
    result = run_time_domain_workflow(
        _reference_ode(ode_analysis_goal=OdeAnalysisGoal.PARTIAL_FRACTIONS)
    )
    assert result.solution is not None
    assert result.solution.partial_fractions is not None
    assert result.solution.inverse_mappings == ()
    assert result.solution.time_function is None
    assert "Inverse Laplace" not in result.presentation.worked_steps
    assert "time" not in result.presentation.visible_result_tabs
    assert "partial" in result.presentation.visible_result_tabs


def test_partial_fraction_goal_does_not_promote_y_when_pbz_is_unsupported() -> None:
    result = run_time_domain_workflow(
        TimeDomainInputDraft(
            task_type=TimeDomainTaskType.SOLVE_ODE,
            output_order=1,
            input_order=0,
            output_coefficient_texts=("1", "1"),
            input_coefficient_texts=("1",),
            output_initial_texts=("0",),
            ode_input_signal_type=InputSignalType.IMAGE_EXPRESSION,
            input_expression_text="s^2",
            ode_analysis_goal=OdeAnalysisGoal.PARTIAL_FRACTIONS,
        )
    )

    assert result.solution is not None
    assert result.solution.status is ComputationStatus.UNSUPPORTED
    assert result.solution.partial_fractions is None
    assert "Endergebnis: Y(s)" not in result.presentation.summary
    assert "Endaussage: Die verlangte Partialbruchzerlegung" in (
        result.presentation.summary
    )
    assert r"\boxed{Y(s)=" not in result.presentation.latex_source
    assert "nicht fertiggestellt" in result.presentation.latex_source
    assert "distributional_inverse_unsupported" in result.presentation.diagnostics


@pytest.mark.parametrize(
    ("signal_type", "changes"),
    (
        (
            InputSignalType.ZERO,
            {"ode_signal_amplitude_text": "ungültig(", "ode_signal_rate_text": "ungültig("},
        ),
        (
            InputSignalType.POLYNOMIAL,
            {
                "ode_signal_amplitude_text": "ungültig(",
                "ode_signal_rate_text": "ungültig(",
                "polynomial_coefficient_texts": ("1",),
            },
        ),
        (
            InputSignalType.IMAGE_EXPRESSION,
            {
                "ode_signal_amplitude_text": "ungültig(",
                "ode_signal_rate_text": "ungültig(",
                "input_expression_text": "1/(s+1)",
            },
        ),
    ),
)
def test_irrelevant_hidden_signal_fields_are_not_parsed(
    signal_type: InputSignalType, changes: dict[str, object]
) -> None:
    result = run_time_domain_workflow(
        _rf03(
            output_order=1,
            output_coefficient_texts=("1", "1"),
            output_initial_texts=("0",),
            ode_input_signal_type=signal_type,
            ode_analysis_goal=OdeAnalysisGoal.OUTPUT_LAPLACE,
            **changes,
        )
    )
    assert result.solution is not None
    assert result.solution.status.value == "SUCCESS"


def test_invalid_direct_image_input_has_field_specific_diagnostic() -> None:
    result = run_time_domain_workflow(
        _reference_ode(
            ode_analysis_goal=OdeAnalysisGoal.OUTPUT_LAPLACE,
            input_expression_text="exp(s)",
        )
    )
    assert result.solution is None
    assert "Bildbereichseingang U(s)" in result.presentation.diagnostics
    assert "1/(s+2)" in result.presentation.diagnostics


def test_invalid_ode_coefficient_has_field_specific_diagnostic() -> None:
    result = run_time_domain_workflow(
        _reference_ode(output_coefficient_texts=("0", "4", "sin("))
    )
    assert result.solution is None
    assert "Koeffizient vor y''(t)" in result.presentation.diagnostics
    assert "z. B. 2 oder k" in result.presentation.diagnostics


def test_rf04_transfer_function_preserves_negative_sign() -> None:
    result = run_time_domain_workflow(
        TimeDomainInputDraft(
            task_type=TimeDomainTaskType.TRANSFER_FUNCTION_FROM_ODE,
            output_name="phi_G",
            input_name="F_A",
            output_order=2,
            input_order=0,
            output_coefficient_texts=("g*(m_K+m_G)", "-d_K", "m_K*l"),
            input_coefficient_texts=("-1",),
            assumptions_text="m_K > 0; l > 0",
            zero_state_confirmed=True,
        )
    )
    assert result.solution is not None and result.solution.ode_transfer_function is not None
    s = sp.Symbol("s")
    expected = -1 / (
        sp.Symbol("m_K") * sp.Symbol("l") * s**2
        - sp.Symbol("d_K") * s
        + sp.Symbol("g") * (sp.Symbol("m_K") + sp.Symbol("m_G"))
    )
    assert (
        sp.simplify(
            result.solution.ode_transfer_function.reduced_transfer_function._as_sympy() - expected
        )
        == 0
    )
    assert "+ -" not in result.presentation.ode_and_initials
    assert "= -F_A(t)" in result.presentation.ode_and_initials
    assert r"\ddot{\varphi_G}(t)" in result.presentation.latex_source
    assert r"G_S(s)=\frac{\Phi_G(s)}{F_{A}(s)}=- \frac{1}" in (
        result.presentation.latex_source
    )
    visible_derivation = "\n".join(
        (
            result.presentation.laplace_transformation,
            result.presentation.image_equation,
            result.presentation.worked_steps,
            result.presentation.latex_source,
        )
    )
    assert "Phi_G(s)" in visible_derivation
    assert "F_A(s)" in visible_derivation
    assert "phi_G(0+)" in visible_derivation
    assert "Y(s)" not in visible_derivation
    assert "U(s)" not in visible_derivation
    assert (
        result.presentation.image_equation
        == "[l*m_K*s^2 - d_K*s + g*(m_G + m_K)]*Phi_G(s) = -F_A(s)"
    )
    assert result.presentation.short_solution.startswith(
        "G_S(s) = Phi_G(s)/F_A(s) = -1/"
    )
    denominator = result.presentation.short_solution.split("/", maxsplit=2)[-1]
    assert denominator.index("s^2") < denominator.index("- d_K*s")
    assert "g*(m_G + m_K)" in denominator
    _assert_no_internal_origin_names(result)


@pytest.mark.parametrize("minus", ("-", "−", "–"))
def test_rf04_accepts_supported_minus_variants_in_numeric_and_symbolic_fields(
    minus: str,
) -> None:
    result = run_time_domain_workflow(
        TimeDomainInputDraft(
            task_type=TimeDomainTaskType.TRANSFER_FUNCTION_FROM_ODE,
            output_name="phi_G",
            input_name="F_A",
            output_order=2,
            input_order=0,
            output_coefficient_texts=(
                "g*(m_K+m_G)",
                f"{minus}d_K",
                "m_K*l",
            ),
            input_coefficient_texts=(f"{minus}1",),
            assumptions_text="m_K > 0; l > 0",
            zero_state_confirmed=True,
        )
    )

    assert result.solution is not None
    assert result.solution.ode_transfer_function is not None
    assert "G_S(s) = Phi_G(s)/F_A(s) = -1/" in result.presentation.summary


def test_rf04_rejection_latex_requests_transfer_function_without_pseudo_solution() -> None:
    result = run_time_domain_workflow(
        TimeDomainInputDraft(
            task_type=TimeDomainTaskType.TRANSFER_FUNCTION_FROM_ODE,
            output_name="phi_G",
            input_name="F_A",
            output_order=1,
            input_order=0,
            output_coefficient_texts=("1", "1"),
            input_coefficient_texts=("1",),
            zero_state_confirmed=False,
        )
    )

    assert result.solution is not None
    assert result.solution.ode_transfer_function is None
    assert r"G_S(s)=\frac{\Phi_G(s)}{F_{A}(s)}" in result.presentation.latex_source
    assert "y(t)" not in result.presentation.latex_source
    assert r"\textbf{Lösung}" not in result.presentation.latex_source
    assert result.presentation.short_solution == ""


def test_rf05_missing_initial_value_stops_before_y_of_s() -> None:
    result = run_time_domain_workflow(_rf03(output_initial_texts=("0", "")))
    assert result.solution is not None
    assert result.solution.output_laplace is None
    assert result.solution.time_function is None
    assert any(
        item.code.value.endswith("missing_initial_condition")
        for item in result.solution.diagnostics
    )
    assert "y'(0+)" in result.presentation.diagnostics
    assert "z. B. 0 oder y0" in result.presentation.diagnostics


def test_rf14_parameter_pt2_step_has_exact_zero_residual() -> None:
    result = run_time_domain_workflow(
        TimeDomainInputDraft(
            task_type=TimeDomainTaskType.SOLVE_ODE,
            output_order=2,
            input_order=0,
            output_coefficient_texts=("k", "eta", "M"),
            input_coefficient_texts=("1",),
            output_initial_texts=("0", "0"),
            ode_input_signal_type=InputSignalType.STEP,
            ode_signal_amplitude_text="F_ext",
            assumptions_text="M > 0; eta > 0; k > 0; 4*M*k-eta^2 > 0",
        )
    )
    assert result.solution is not None and result.solution.ode_solution is not None
    assert result.solution.ode_solution.verification.trusted
    assert result.solution.ode_solution.verification.ode_residual._as_sympy() == 0


def test_polynomial_sinus_and_cosinus_inputs_are_exactly_verified() -> None:
    cases = (
        (InputSignalType.POLYNOMIAL, "1", ("0", "1", "0", "0", "0")),
        (InputSignalType.SINUS, "2", ()),
        (InputSignalType.COSINUS, "2", ()),
    )
    for signal_type, rate, polynomial in cases:
        result = run_time_domain_workflow(
            TimeDomainInputDraft(
                task_type=TimeDomainTaskType.SOLVE_ODE,
                output_order=1,
                input_order=0,
                output_coefficient_texts=("1", "1"),
                input_coefficient_texts=("1",),
                output_initial_texts=("0",),
                ode_input_signal_type=signal_type,
                ode_signal_amplitude_text="1",
                ode_signal_rate_text=rate,
                polynomial_coefficient_texts=polynomial,
            )
        )
        assert result.solution is not None and result.solution.ode_solution is not None
        assert result.solution.ode_solution.verification.ode_residual._as_sympy() == 0


def test_transfer_function_rejects_nonzero_initial_state() -> None:
    result = run_time_domain_workflow(
        TimeDomainInputDraft(
            task_type=TimeDomainTaskType.TRANSFER_FUNCTION_FROM_ODE,
            output_order=1,
            output_coefficient_texts=("1", "1"),
            input_coefficient_texts=("1",),
            output_initial_texts=("1",),
            zero_state_confirmed=True,
        )
    )
    assert result.solution is not None and result.solution.ode_transfer_function is None
    assert any(
        item.code.value.endswith("transfer_function_requires_zero_initial_state")
        for item in result.solution.diagnostics
    )


def test_input_derivative_uses_derived_initial_value() -> None:
    result = run_time_domain_workflow(
        TimeDomainInputDraft(
            task_type=TimeDomainTaskType.SOLVE_ODE,
            output_order=1,
            input_order=1,
            output_coefficient_texts=("1", "1"),
            input_coefficient_texts=("0", "1"),
            output_initial_texts=("0",),
            ode_input_signal_type=InputSignalType.SINUS,
            ode_signal_amplitude_text="1",
            ode_signal_rate_text="2",
        )
    )
    assert result.solution is not None and result.solution.ode_solution is not None
    input_conditions = result.solution.ode_solution.input_initial_conditions
    assert input_conditions is not None and input_conditions.complete
    assert input_conditions.values[0].origin.value == "DERIVED"
    assert "aus dem Eingangssignal abgeleitet" in result.presentation.ode_and_initials
    _assert_no_internal_origin_names(result)


def test_preview_hides_zero_terms_and_preserves_eleven() -> None:
    preview = format_ode_preview("y", "u", ("11", "1"), ("0",))
    assert preview == "y'(t) + 11*y(t) = 0"
    assert "u(t)" not in preview


def test_explicit_zero_policy_uses_only_german_origin_label() -> None:
    result = run_time_domain_workflow(
        _rf03(output_initial_texts=("0", ""), missing_initials_are_zero=True)
    )
    assert "ausdrücklich als 0 gesetzt" in result.presentation.ode_and_initials
    _assert_no_internal_origin_names(result)


def _assert_no_internal_origin_names(result: object) -> None:
    presentation = result.presentation
    normal_output = "\n".join(
        (
            presentation.summary,
            presentation.ode_and_initials,
            presentation.laplace_transformation,
            presentation.image_equation,
            presentation.free_and_forced,
            presentation.short_solution,
            presentation.worked_steps,
            presentation.latex_source,
        )
    )
    for forbidden in ("USER_PROVIDED", "DERIVED", "EXPLICIT_ZERO_POLICY"):
        assert forbidden not in normal_output
