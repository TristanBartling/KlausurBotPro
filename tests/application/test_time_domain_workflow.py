"""Reference workflows RF-01, RF-02 and RF-06 through RF-13."""

import sympy as sp

from klausurbotpro.application import (
    TimeDomainInputDraft,
    TimeDomainTaskType,
    run_time_domain_workflow,
)
from klausurbotpro.domain import (
    ComputationStatus,
    DiagnosticCode,
    EndValueStatus,
    RationalClassificationKind,
    TimeDomainSolution,
)

t = sp.Symbol("t")
s = sp.Symbol("s")


def _assert_time(
    draft: TimeDomainInputDraft, expected: sp.Expr
) -> TimeDomainSolution:
    result = run_time_domain_workflow(draft)
    assert result.solution is not None
    assert result.solution.status is ComputationStatus.SUCCESS
    assert result.solution.time_function is not None
    assert sp.simplify(
        result.solution.time_function.expression._as_sympy() - expected
    ) == 0
    assert result.presentation.worked_steps
    assert result.presentation.latex_source
    return result.solution


def test_rf01_direct_laplace() -> None:
    result = run_time_domain_workflow(
        TimeDomainInputDraft(
            TimeDomainTaskType.DIRECT_LAPLACE,
            time_expression_text="2*t*exp(-4*t)",
        )
    )
    assert result.solution is not None
    assert result.solution.output_laplace is not None
    assert sp.simplify(
        result.solution.output_laplace._as_sympy() - 2 / (s + 4) ** 2
    ) == 0
    assert "Dämpfung" not in result.presentation.diagnostics
    assert result.solution.direct_rules


def test_direct_standard_pairs_and_supported_combinations() -> None:
    cases = (
        ("3", 3 / s),
        ("t^2", 2 / s**3),
        ("exp(2*t)", 1 / (s - 2)),
        ("t^2*exp(-3*t)", 2 / (s + 3) ** 3),
        ("sin(5*t)", 5 / (s**2 + 25)),
        ("cos(5*t)", s / (s**2 + 25)),
        ("exp(-t)*sin(2*t)", 2 / ((s + 1) ** 2 + 4)),
        ("2 + 3*t*exp(-t)", 2 / s + 3 / (s + 1) ** 2),
    )
    for source, expected in cases:
        result = run_time_domain_workflow(
            TimeDomainInputDraft(
                TimeDomainTaskType.DIRECT_LAPLACE,
                time_expression_text=source,
            )
        )
        assert result.solution is not None
        assert result.solution.output_laplace is not None
        assert sp.simplify(
            result.solution.output_laplace._as_sympy() - expected
        ) == 0


def test_rf02_growing_real_quadratic_pair() -> None:
    solution = _assert_time(
        TimeDomainInputDraft(
            TimeDomainTaskType.INVERSE_LAPLACE,
            image_expression_text="(s-4)/((s-4)^2+4)",
        ),
        sp.exp(4 * t) * sp.cos(2 * t),
    )
    assert any("wachsenden Modus" in item.message for item in solution.diagnostics)


def test_rf06_pt1_step_response() -> None:
    solution = _assert_time(
        TimeDomainInputDraft(
            TimeDomainTaskType.STEP_RESPONSE,
            system_expression_text="1/(2*s+1)",
            step_amplitude_text="0.1",
        ),
        sp.Rational(1, 10) * (1 - sp.exp(-t / 2)),
    )
    assert solution.verification.end_value is not None
    assert solution.verification.end_value.canonical_text == "1/10"
    assert solution.verification.end_value_status is EndValueStatus.VALID


def test_rf07_complete_repeated_pole_ansatz() -> None:
    solution = _assert_time(
        TimeDomainInputDraft(
            TimeDomainTaskType.INVERSE_LAPLACE,
            image_expression_text="(s+7)/((s+1)^2*(s-2))",
        ),
        -sp.exp(-t) - 2 * t * sp.exp(-t) + sp.exp(2 * t),
    )
    assert solution.partial_fractions is not None
    actual_terms = {
        (item.factor.canonical_text, item.power)
        for item in solution.partial_fractions.terms
    }
    assert actual_terms >= {
        ("s + 1", 1),
        ("s + 1", 2),
        ("s - 2", 1),
    }


def test_rf08_real_oscillation_and_invalid_end_value() -> None:
    solution = _assert_time(
        TimeDomainInputDraft(
            TimeDomainTaskType.STEP_RESPONSE,
            system_expression_text="s/(s^2+pi/4)",
            step_amplitude_text="pi/2",
        ),
        sp.sqrt(sp.pi) * sp.sin(sp.sqrt(sp.pi) * t / 2),
    )
    assert solution.verification.end_value_status is (
        EndValueStatus.END_VALUE_THEOREM_INVALID
    )
    assert solution.verification.end_value is None


def test_rf06_display_is_exam_ready_and_hides_internal_terms() -> None:
    result = run_time_domain_workflow(
        TimeDomainInputDraft(
            TimeDomainTaskType.STEP_RESPONSE,
            system_expression_text="1/(2*s+1)",
            step_amplitude_text="0.1",
        )
    )
    assert result.presentation.time_function == "y(t) = (1 - exp(-t/2))/10"
    latex = result.presentation.latex_source
    assert r"A=\frac{1}{10}" in latex
    assert r"B=- \frac{1}{10}" in latex
    assert r"Y_{\mathrm{PBZ}}(s)" in latex
    assert r"\boxed{y(t)=" in latex
    normal_output = "\n".join(
        (
            result.presentation.short_solution,
            result.presentation.worked_steps,
            latex,
        )
    )
    for internal_term in (
        "step_response",
        "STRICTLY_PROPER",
        "PASS",
        "A_1",
        "F_roh",
        "F_red",
        "**",
    ):
        assert internal_term not in normal_output


def test_rf07_display_has_complete_repeated_pole_ansatz_and_values() -> None:
    result = run_time_domain_workflow(
        TimeDomainInputDraft(
            TimeDomainTaskType.INVERSE_LAPLACE,
            image_expression_text="(s+7)/((s+1)^2*(s-2))",
        )
    )
    partial = result.presentation.partial_fractions
    assert "A/(s + 1)" in partial
    assert "B/((s + 1)^2)" in partial
    assert "C/(s - 2)" in partial
    assert "A = -1, B = -2, C = 1" in partial


def test_rf08_display_uses_real_sine_and_explains_end_value_rejection() -> None:
    result = run_time_domain_workflow(
        TimeDomainInputDraft(
            TimeDomainTaskType.STEP_RESPONSE,
            system_expression_text="s/(s^2+pi/4)",
            step_amplitude_text="pi/2",
        )
    )
    assert result.presentation.time_function == (
        "y(t) = sqrt(pi)*sin(sqrt(pi)*t/2)"
    )
    assert "Y(s) = (pi/2)/(s^2 + pi/4)" in result.presentation.summary
    assert "nicht anwendbar" in result.presentation.verifications
    assert "imaginären Achse" in result.presentation.latex_source
    assert "END_VALUE_THEOREM_INVALID" not in result.presentation.latex_source


def test_rf09_improper_inverse_is_stopped_after_division() -> None:
    result = run_time_domain_workflow(
        TimeDomainInputDraft(
            TimeDomainTaskType.INVERSE_LAPLACE,
            image_expression_text="(s^2+1)/(s+1)",
        )
    )
    assert result.solution is not None
    assert result.solution.status is ComputationStatus.UNSUPPORTED
    assert result.solution.rational_analysis is not None
    assert result.solution.rational_analysis.classification.kind is (
        RationalClassificationKind.IMPROPER
    )
    assert result.solution.time_function is None


def test_rf10_general_exponential_input() -> None:
    _assert_time(
        TimeDomainInputDraft(
            TimeDomainTaskType.GENERAL_RESPONSE,
            system_expression_text="1/(s+1)^2",
            input_expression_text="9/(s-2)",
        ),
        -sp.exp(-t) - 3 * t * sp.exp(-t) + sp.exp(2 * t),
    )


def test_rf11_valid_end_value_is_one_twenty_fifth() -> None:
    solution = _assert_time(
        TimeDomainInputDraft(
            TimeDomainTaskType.STEP_RESPONSE,
            system_expression_text="1/((s+1)^2+24*(s+1))",
            step_amplitude_text="1",
        ),
        sp.Rational(1, 25)
        - sp.exp(-t) / 24
        + sp.exp(-25 * t) / 600,
    )
    assert solution.verification.end_value is not None
    assert solution.verification.end_value.canonical_text == "1/25"


def test_rf12_invalid_end_value_has_structured_diagnostic() -> None:
    solution = _assert_time(
        TimeDomainInputDraft(
            TimeDomainTaskType.STEP_RESPONSE,
            system_expression_text="s/(s^2+pi/4)",
            step_amplitude_text="pi/2",
        ),
        sp.sqrt(sp.pi) * sp.sin(sp.sqrt(sp.pi) * t / 2),
    )
    assert any(
        item.code is DiagnosticCode.END_VALUE_THEOREM_INVALID
        for item in solution.diagnostics
    )


def test_rf13_cancellation_keeps_raw_reduced_and_both_warnings() -> None:
    solution = _assert_time(
        TimeDomainInputDraft(
            TimeDomainTaskType.INVERSE_LAPLACE,
            image_expression_text="(s+1)/((s+1)*(s+2))",
        ),
        sp.exp(-2 * t),
    )
    assert solution.rational_analysis is not None
    assert solution.rational_analysis.reduced_expression.canonical_text == "1/(s + 2)"
    codes = {item.code for item in solution.diagnostics}
    assert DiagnosticCode.CANCELLED_COMMON_FACTOR in codes
    assert DiagnosticCode.HIDDEN_MODE_POSSIBLE in codes


def test_typed_exponential_input_builds_u_and_same_response() -> None:
    solution = _assert_time(
        TimeDomainInputDraft(
            TimeDomainTaskType.EXPONENTIAL_INPUT,
            system_expression_text="1/(s+1)^2",
            exponential_amplitude_text="9",
            exponential_exponent_text="2",
        ),
        -sp.exp(-t) - 3 * t * sp.exp(-t) + sp.exp(2 * t),
    )
    assert solution.input_laplace is not None
    assert sp.simplify(solution.input_laplace._as_sympy() - 9 / (s - 2)) == 0
    assert solution.input_signal is not None
    assert sp.simplify(
        solution.input_signal.time_function.expression._as_sympy()
        - 9 * sp.exp(2 * t)
    ) == 0


def test_mixed_time_image_variables_are_visible_input_error() -> None:
    result = run_time_domain_workflow(
        TimeDomainInputDraft(
            TimeDomainTaskType.DIRECT_LAPLACE,
            time_expression_text="t+s",
        )
    )
    assert result.solution is None
    assert "Gemischte Verwendung" in result.presentation.diagnostics
