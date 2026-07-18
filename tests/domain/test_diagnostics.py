"""Tests for stable immutable diagnostics."""

from dataclasses import FrozenInstanceError

import pytest
import sympy as sp

from klausurbotpro.domain import (
    Diagnostic,
    DiagnosticCode,
    DiagnosticSeverity,
    ExactExpression,
)
from klausurbotpro.parsing import ParseResult


def test_diagnostic_codes_are_stable_machine_values() -> None:
    assert DiagnosticSeverity.ERROR.value == "error"
    assert DiagnosticCode.PARSE_EMPTY_INPUT.value == "parse.empty_input"
    assert DiagnosticCode.MATH_DIVISION_BY_ZERO.value == "math.division_by_zero"


def test_diagnostic_is_immutable_and_copies_details_to_tuple() -> None:
    diagnostic = Diagnostic(
        severity=DiagnosticSeverity.WARNING,
        code=DiagnosticCode.PARSE_LIMIT_EXCEEDED,
        message="Grenze erreicht.",
        field="expression",
        technical_details=(("limit", "max_ast_nodes"),),
    )

    assert diagnostic.technical_details == (("limit", "max_ast_nodes"),)
    with pytest.raises(FrozenInstanceError):
        diagnostic.message = "Geändert."  # type: ignore[misc]


def test_diagnostic_rejects_empty_message() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        Diagnostic(
            severity=DiagnosticSeverity.ERROR,
            code=DiagnosticCode.PARSE_INVALID_SYNTAX,
            message=" ",
        )


def test_successful_parse_result_may_contain_warnings() -> None:
    warning = Diagnostic(
        severity=DiagnosticSeverity.WARNING,
        code=DiagnosticCode.PARSE_LIMIT_EXCEEDED,
        message="Hinweis.",
    )

    result = ParseResult(
        value=ExactExpression._from_sympy(sp.Integer(1)),
        diagnostics=(warning,),
    )

    assert result.succeeded
    assert result.diagnostics == (warning,)
