"""Focused exact tests for classification, PBZ, inverse rules and guards."""

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
    FactorType,
    RationalClassificationKind,
    TimeDomainSolution,
    VerificationStatus,
)


def _inverse(text: str) -> TimeDomainSolution:
    result = run_time_domain_workflow(
        TimeDomainInputDraft(
            TimeDomainTaskType.INVERSE_LAPLACE,
            image_expression_text=text,
        )
    )
    assert result.solution is not None
    return result.solution


def test_rational_classification_covers_all_three_degree_relations() -> None:
    expected = (
        ("1/(s+1)", RationalClassificationKind.STRICTLY_PROPER),
        ("s/(s+1)", RationalClassificationKind.EQUAL_DEGREE),
        ("(s^2+1)/(s+1)", RationalClassificationKind.IMPROPER),
    )
    for text, kind in expected:
        solution = _inverse(text)
        assert solution.rational_analysis is not None
        assert solution.rational_analysis.classification.kind is kind


def test_polynomial_division_reconstructs_improper_input() -> None:
    solution = _inverse("(s^2+1)/(s+1)")
    assert solution.rational_analysis is not None
    division = solution.rational_analysis.division

    assert division.quotient.canonical_text == "s - 1"
    assert division.remainder.canonical_text == "2"
    assert division.reconstruction_residual.canonical_text == "0"
    assert solution.time_function is None


def test_multiple_linear_factor_builds_complete_ansatz_and_factorial_rule() -> None:
    solution = _inverse("1/(s+1)^3")
    assert solution.partial_fractions is not None
    assert [term.power for term in solution.partial_fractions.terms] == [1, 2, 3]
    assert solution.time_function is not None
    t = sp.Symbol("t")
    assert sp.simplify(
        solution.time_function.expression._as_sympy()
        - t**2 * sp.exp(-t) / 2
    ) == 0


def test_irreducible_quadratic_is_real_and_forward_checked() -> None:
    solution = _inverse("(s-4)/((s-4)^2+4)")
    assert solution.factor_structure is not None
    assert solution.factor_structure.factors[0].factor_type is (
        FactorType.IRREDUCIBLE_QUADRATIC
    )
    assert solution.time_function is not None
    t = sp.Symbol("t")
    assert sp.simplify(
        solution.time_function.expression._as_sympy()
        - sp.exp(4 * t) * sp.cos(2 * t)
    ) == 0
    assert solution.verification.items[-1].status is VerificationStatus.PASS


def test_pbz_recomposition_has_symbolic_proof_and_two_numeric_samples() -> None:
    solution = _inverse("(s+7)/((s+1)^2*(s-2))")
    check = next(
        item
        for item in solution.verification.items
        if item.check_id == "pbz_recomposition"
    )

    assert check.status is VerificationStatus.PASS
    assert check.residual is not None
    assert check.residual.canonical_text == "0"
    assert len(check.numerical_values) == 2


def test_end_value_guard_rejects_imaginary_axis_pair() -> None:
    result = run_time_domain_workflow(
        TimeDomainInputDraft(
            TimeDomainTaskType.STEP_RESPONSE,
            system_expression_text="s/(s^2+pi/4)",
            step_amplitude_text="pi/2",
        )
    )
    assert result.solution is not None
    assert result.solution.verification.end_value_status is (
        EndValueStatus.END_VALUE_THEOREM_INVALID
    )
    assert result.solution.verification.end_value is None


def test_parameter_dependent_discriminant_is_inconclusive_not_guessed() -> None:
    solution = _inverse("1/(s^2+a*s+1)")

    assert solution.status is ComputationStatus.INCONCLUSIVE
    assert any(
        item.code is DiagnosticCode.PARAMETER_ASSUMPTIONS_INSUFFICIENT
        for item in solution.diagnostics
    )
