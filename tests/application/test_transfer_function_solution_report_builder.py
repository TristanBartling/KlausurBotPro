"""Acceptance tests for complete transfer-function solution reports."""

import pytest

from klausurbotpro.application import (
    ConditionLine,
    EquationLine,
    ResultLine,
    SolutionReportStatus,
    SolutionSectionKind,
    TransferFunctionSolutionReport,
    TransferFunctionSolutionReportBuilder,
    TransferFunctionWorkflowRequest,
    TransferFunctionWorkflowService,
    TransformationLine,
    WorkflowInputForm,
)
from klausurbotpro.domain import (
    ExactRationalValue,
    ParameterAssignment,
    ParameterSubstitutions,
    StabilityStatus,
)


def _report(
    expression: str,
    *,
    parameters: tuple[str, ...] = (),
    substitutions: ParameterSubstitutions | None = None,
) -> TransferFunctionSolutionReport:
    state = TransferFunctionWorkflowService().run(
        TransferFunctionWorkflowRequest(
            WorkflowInputForm.COMMON,
            common_expression_text=expression,
            allowed_parameter_names=parameters,
            substitutions=substitutions,
        )
    )
    return TransferFunctionSolutionReportBuilder().build(state)


def _result_values(
    report: TransferFunctionSolutionReport,
    section_kind: SolutionSectionKind,
) -> tuple[str, ...]:
    section = report.section(section_kind)
    assert section is not None
    return tuple(
        line.exact_value.plaintext
        for line in section.lines
        if type(line) is ResultLine
    )


def test_stable_first_order_report_is_complete_and_fixed_order() -> None:
    report = _report("1/(s+1)")

    assert report.status is SolutionReportStatus.COMPLETE
    assert tuple(section.kind for section in report.sections) == tuple(
        SolutionSectionKind
    )
    assert "-1" in _result_values(report, SolutionSectionKind.POLES)
    assert "System ist E/A-stabil." in _result_values(
        report,
        SolutionSectionKind.STABILITY,
    )


def test_separated_original_inputs_remain_text_not_math_results() -> None:
    state = TransferFunctionWorkflowService().run(
        TransferFunctionWorkflowRequest(
            WorkflowInputForm.SEPARATED,
            numerator_expression_text="s + 1",
            denominator_expression_text="s + 2",
        )
    )
    report = TransferFunctionSolutionReportBuilder().build(state)
    given = report.section(SolutionSectionKind.GIVEN)
    transfer = report.section(SolutionSectionKind.TRANSFER_FUNCTION)
    assert given is not None
    assert transfer is not None

    original_values = {
        line.exact_value.plaintext
        for line in given.lines
        if type(line) is ResultLine
        and line.source_role in ("original_numerator", "original_denominator")
    }
    assert original_values == {"s + 1", "s + 2"}
    equation = next(
        line for line in transfer.lines if type(line) is EquationLine
    )
    assert equation.right.plaintext == "(s + 1)/(s + 2)"


def test_two_real_poles_are_reported_exactly() -> None:
    report = _report("1/(s^2+3*s+2)")

    values = _result_values(report, SolutionSectionKind.POLES)
    assert "-1" in values
    assert "-2" in values


def test_complete_cancellation_retains_domain_exclusion() -> None:
    report = _report("(s+1)/(s+1)")
    section = report.section(SolutionSectionKind.DOMAIN_EXCLUSIONS)
    assert section is not None

    conditions = [
        line
        for line in section.lines
        if type(line) is ConditionLine
    ]
    assert any(
        line.expressions[0].plaintext == "s + 1"
        and line.relation == "!= 0"
        for line in conditions
    )
    pair_section = report.section(
        SolutionSectionKind.NUMERATOR_DENOMINATOR
    )
    assert pair_section is not None
    equations = [
        line
        for line in pair_section.lines
        if type(line) is EquationLine
    ]
    assert any(
        line.identifier == "reduced_numerator"
        and line.right.plaintext == "1"
        for line in equations
    )


def test_partial_cancellation_has_structured_transformation() -> None:
    report = _report("((s+1)*(s+2))/(s+1)")
    section = report.section(SolutionSectionKind.REDUCTION)
    assert section is not None
    transformations = [
        line for line in section.lines if type(line) is TransformationLine
    ]

    assert len(transformations) == 1
    assert transformations[0].operation_kind == (
        "remove_common_polynomial_factor"
    )
    assert transformations[0].factor_or_operation is not None
    assert transformations[0].factor_or_operation.plaintext == "s + 1"
    assert transformations[0].retained_domain_exclusions


@pytest.mark.parametrize(
    ("expression", "parameters", "expected_kind"),
    [
        (
            "(2*s+2)/(4*s+8)",
            (),
            "remove_common_numeric_factor",
        ),
        ("(s+1)/(s+1)", (), "remove_common_polynomial_factor"),
        ("1/(K*s+K)", ("K",), "normalize_safe_symbolic_scale"),
        ("1/(-s-1)", (), "normalize_sign"),
        ("0/(s+1)", (), "reduce_zero_numerator"),
        ("1/(s+1)", (), "no_reduction"),
    ],
)
def test_existing_reduction_step_kinds_are_translated_without_recalculation(
    expression: str,
    parameters: tuple[str, ...],
    expected_kind: str,
) -> None:
    report = _report(expression, parameters=parameters)
    section = report.section(SolutionSectionKind.REDUCTION)
    assert section is not None

    steps = [
        line for line in section.lines if type(line) is TransformationLine
    ]
    assert any(line.operation_kind == expected_kind for line in steps)


def test_prerequisite_kinds_remain_structured_and_not_split() -> None:
    report = _report(
        "1/((K-1)*s+T)",
        parameters=("K", "T"),
    )
    section = report.section(SolutionSectionKind.PREREQUISITES)
    assert section is not None
    conditions = [
        line for line in section.lines if type(line) is ConditionLine
    ]

    assert len(conditions) == 1
    assert conditions[0].relation == "NOT_ALL_ZERO"
    assert tuple(
        expression.plaintext for expression in conditions[0].expressions
    ) == ("K - 1", "T")


def test_zero_numerator_is_not_described_as_all_individual_zeros() -> None:
    report = _report("0/(s+1)")
    values = _result_values(report, SolutionSectionKind.ZEROS)

    assert "Nullpolynom: keine endliche Einzelliste" in values
    assert not any("alle Nullstellen" in value for value in values)


@pytest.mark.parametrize(
    (
        "expression",
        "expected_status",
        "expected_text",
        "expected_condition",
    ),
    [
        (
            "1/s",
            StabilityStatus.BORDERLINE_STABLE.value,
            "System ist grenzstabil, aber nicht E/A-stabil.",
            "simple_imaginary_axis_pole",
        ),
        (
            "1/s^2",
            StabilityStatus.UNSTABLE.value,
            "System ist instabil.",
            "repeated_imaginary_axis_pole_exists",
        ),
        (
            "1/(s-1)",
            StabilityStatus.UNSTABLE.value,
            "System ist instabil.",
            "right_half_plane_pole_exists",
        ),
        (
            "1/(s^2+1)",
            StabilityStatus.BORDERLINE_STABLE.value,
            "System ist grenzstabil, aber nicht E/A-stabil.",
            "simple_imaginary_axis_pole",
        ),
    ],
)
def test_stability_acceptance_cases(
    expression: str,
    expected_status: str,
    expected_text: str,
    expected_condition: str,
) -> None:
    report = _report(expression)
    section = report.section(SolutionSectionKind.STABILITY)
    assert section is not None

    result = next(line for line in section.lines if type(line) is ResultLine)
    assert result.source_role == expected_status
    assert result.exact_value.plaintext == expected_text
    assert any(
        type(line) is ConditionLine
        and line.condition_kind == expected_condition
        for line in section.lines
    )


def test_symbolically_undetermined_is_a_complete_mathematical_report() -> None:
    report = _report("1/(T*s+1)", parameters=("T",))

    assert report.status is SolutionReportStatus.COMPLETE
    assert "nicht eindeutig bestimmbar" in _result_values(
        report,
        SolutionSectionKind.POLES,
    )
    assert "Stabilität nicht eindeutig bestimmbar." in _result_values(
        report,
        SolutionSectionKind.STABILITY,
    )
    substitutions = report.section(
        SolutionSectionKind.PARAMETER_SUBSTITUTIONS
    )
    assert substitutions is not None
    assert any(type(line) is ConditionLine for line in substitutions.lines)


def test_exact_parameter_assignment_and_specialized_pole_are_visible() -> None:
    substitutions = ParameterSubstitutions(
        (ParameterAssignment("T", ExactRationalValue(2)),)
    )
    report = _report(
        "1/(T*s+1)",
        parameters=("T",),
        substitutions=substitutions,
    )

    assert "-1/2" in _result_values(report, SolutionSectionKind.POLES)
    given = report.section(SolutionSectionKind.GIVEN)
    assert given is not None
    assert any(
        type(line) is EquationLine
        and line.identifier == "active_parameter_substitution"
        and line.right.plaintext == "2"
        for line in given.lines
    )
    poles = report.section(SolutionSectionKind.POLES)
    assert poles is not None
    assert any(
        type(line) is EquationLine
        and line.identifier == "specialized_polynomial"
        and line.right.plaintext == "2*s + 1"
        for line in poles.lines
    )


def test_complex_roots_keep_exact_values_before_approximations() -> None:
    report = _report("1/(s^2+2*s+2)")
    poles = report.section(SolutionSectionKind.POLES)
    assert poles is not None
    roots = [line for line in poles.lines if type(line) is ResultLine]

    assert {line.exact_value.plaintext for line in roots} == {
        "-1 - I",
        "-1 + I",
    }
    assert all(line.exact_value.plaintext for line in roots)


def test_rootof_values_have_deterministic_structured_display() -> None:
    report = _report("1/(s^5-s+1)")
    values = _result_values(report, SolutionSectionKind.POLES)

    assert any(value.startswith("RootOf(") for value in values)
