"""Contract invariants for paper-oriented solution reports."""

from dataclasses import FrozenInstanceError

import pytest

from klausurbotpro.application import (
    EquationLine,
    ReportDiagnostic,
    ReportDiagnosticCode,
    ReportMathExpression,
    SolutionReportLimits,
    SolutionReportStatus,
    SolutionSection,
    SolutionSectionKind,
    SolutionSectionStatus,
    TransferFunctionSolutionReport,
    TransferFunctionSolutionReportBuilder,
    TransferFunctionWorkflowLimits,
    WarningLine,
)
from klausurbotpro.domain import DiagnosticSeverity


def _equation() -> EquationLine:
    return EquationLine(
        ReportMathExpression("G(s)", "G(s)"),
        "=",
        ReportMathExpression("1/(s+1)", r"\frac{1}{s+1}"),
    )


def test_contracts_are_immutable_hashable_and_sympy_free() -> None:
    section = SolutionSection(
        SolutionSectionKind.TRANSFER_FUNCTION,
        SolutionSectionStatus.COMPLETE,
        (_equation(),),
    )
    first = TransferFunctionSolutionReport(
        SolutionReportStatus.COMPLETE,
        (section,),
    )
    second = TransferFunctionSolutionReport(
        SolutionReportStatus.COMPLETE,
        (section,),
    )

    assert first == second
    assert hash(first) == hash(second)
    assert {first: "report"}[second] == "report"
    assert "sympy" not in type(_equation().right).__module__
    with pytest.raises(FrozenInstanceError):
        first.status = SolutionReportStatus.FAILED  # type: ignore[misc]


@pytest.mark.parametrize("name", SolutionReportLimits.__dataclass_fields__)
@pytest.mark.parametrize("value", [0, -1, True])
def test_limits_require_positive_real_ints(name: str, value: int) -> None:
    with pytest.raises(ValueError, match="positive real int"):
        SolutionReportLimits(**{name: value})


def test_sections_require_fixed_unique_order() -> None:
    given = SolutionSection(
        SolutionSectionKind.GIVEN,
        SolutionSectionStatus.COMPLETE,
        (_equation(),),
    )
    transfer = SolutionSection(
        SolutionSectionKind.TRANSFER_FUNCTION,
        SolutionSectionStatus.COMPLETE,
        (_equation(),),
    )
    with pytest.raises(ValueError, match="fixed unique order"):
        TransferFunctionSolutionReport(
            SolutionReportStatus.COMPLETE,
            (transfer, given),
        )
    with pytest.raises(ValueError, match="fixed unique order"):
        TransferFunctionSolutionReport(
            SolutionReportStatus.COMPLETE,
            (given, given),
        )


def test_unavailable_sections_cannot_hide_lines() -> None:
    with pytest.raises(ValueError, match="cannot contain lines"):
        SolutionSection(
            SolutionSectionKind.POLES,
            SolutionSectionStatus.BLOCKED,
            (_equation(),),
        )


def test_warning_and_report_diagnostic_require_exact_severity() -> None:
    warning = WarningLine(
        "workflow.hint",
        DiagnosticSeverity.INFO,
        None,
        "Hinweis",
    )
    diagnostic = ReportDiagnostic(
        ReportDiagnosticCode.REPORT_INVALID_WORKFLOW_STATE,
        DiagnosticSeverity.ERROR,
        "Ungültig",
    )

    assert warning.severity is DiagnosticSeverity.INFO
    assert diagnostic.severity is DiagnosticSeverity.ERROR
    with pytest.raises(TypeError, match="DiagnosticSeverity"):
        WarningLine("workflow.hint", "info", None, "Hinweis")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="DiagnosticSeverity"):
        ReportDiagnostic(
            ReportDiagnosticCode.REPORT_INVALID_WORKFLOW_STATE,
            "error",  # type: ignore[arg-type]
            "Ungültig",
        )


def test_builder_requires_exact_limit_contract_types() -> None:
    class ReportLimitsSubclass(SolutionReportLimits):
        pass

    class WorkflowLimitsSubclass(TransferFunctionWorkflowLimits):
        pass

    with pytest.raises(TypeError, match="SolutionReportLimits"):
        TransferFunctionSolutionReportBuilder(object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="SolutionReportLimits"):
        TransferFunctionSolutionReportBuilder(ReportLimitsSubclass())
    with pytest.raises(TypeError, match="TransferFunctionWorkflowLimits"):
        TransferFunctionSolutionReportBuilder(
            workflow_limits=object(),  # type: ignore[arg-type]
        )
    with pytest.raises(TypeError, match="TransferFunctionWorkflowLimits"):
        TransferFunctionSolutionReportBuilder(
            workflow_limits=WorkflowLimitsSubclass()
        )
