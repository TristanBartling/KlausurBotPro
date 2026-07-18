"""Adversarial tests for both rational-input forms and pair fields."""

import pytest
from sympy.core.parameters import global_parameters

from klausurbotpro.domain import DiagnosticCode
from klausurbotpro.parsing import (
    ParserConfig,
    SafeRationalExpressionParser,
)

_FORBIDDEN_SOURCES = [
    '__import__("os")',
    'open("datei")',
    'eval("1+1")',
    "globals()",
    "locals()",
    "hash(s)",
    "sin(s)",
    "s.__class__",
    "().__class__",
    "s[0]",
    "[1]",
    '{"s": 1}',
    "{s: 1}",
    "{1}",
    "[x for x in s]",
    "(x for x in s)",
    "(lambda: 1)()",
    '"s"',
    'b"s"',
    "None",
    "True",
    "False",
    "s < 1",
    "s and K",
    "s if K else 0",
    "(s := 1)",
]


def _parser() -> SafeRationalExpressionParser:
    return SafeRationalExpressionParser(
        ParserConfig(frozenset({"s", "K"}))
    )


@pytest.mark.parametrize("source", _FORBIDDEN_SOURCES)
def test_common_form_rejects_full_attack_matrix(source: str) -> None:
    result = _parser().parse_common(source)

    assert not result.succeeded
    assert result.diagnostics[0].code is DiagnosticCode.PARSE_FORBIDDEN_NODE


@pytest.mark.parametrize("source", _FORBIDDEN_SOURCES)
@pytest.mark.parametrize("attacked_part", ["numerator", "denominator"])
def test_each_pair_field_rejects_full_attack_matrix(
    source: str,
    attacked_part: str,
) -> None:
    numerator = source if attacked_part == "numerator" else "1"
    denominator = source if attacked_part == "denominator" else "1"

    result = _parser().parse_pair(
        numerator,
        denominator,
        field="transfer",
    )

    assert not result.succeeded
    assert result.diagnostics[0].code is DiagnosticCode.PARSE_FORBIDDEN_NODE
    assert result.diagnostics[0].field == f"transfer.{attacked_part}"


@pytest.mark.parametrize(
    "source",
    [
        "2s",
        "2(s+1)",
        "s(s+1)",
        "K s",
        "(s+1)(s+2)",
        "(s+1)2",
        "2K",
        "2 3",
    ],
)
def test_implicit_multiplication_is_rejected_in_common_form(
    source: str,
) -> None:
    result = _parser().parse_common(source)

    assert result.diagnostics[0].code is (
        DiagnosticCode.PARSE_IMPLICIT_MULTIPLICATION
    )


@pytest.mark.parametrize(
    ("source", "expected_code"),
    [
        ("[1, 2]", DiagnosticCode.PARSE_INVALID_NUMBER),
        ("(1, 2)", DiagnosticCode.PARSE_INVALID_NUMBER),
        ("{1, 2}", DiagnosticCode.PARSE_INVALID_NUMBER),
        ("1+2j", None),
        ("import os", None),
        ("s = 1", None),
        ("yield s", None),
    ],
)
def test_common_form_handles_remaining_attack_matrix_without_raw_exceptions(
    source: str,
    expected_code: DiagnosticCode | None,
) -> None:
    result = _parser().parse_common(source)

    assert not result.succeeded
    assert result.diagnostics[0].severity.value == "error"
    if expected_code is not None:
        assert result.diagnostics[0].code is expected_code


@pytest.mark.parametrize(
    ("source", "expected_code"),
    [
        ("[1, 2]", DiagnosticCode.PARSE_INVALID_NUMBER),
        ("(1, 2)", DiagnosticCode.PARSE_INVALID_NUMBER),
        ("{1, 2}", DiagnosticCode.PARSE_INVALID_NUMBER),
        ("1+2j", None),
        ("import os", None),
        ("s = 1", None),
        ("yield s", None),
        ("2s", DiagnosticCode.PARSE_IMPLICIT_MULTIPLICATION),
        ("2(s+1)", DiagnosticCode.PARSE_IMPLICIT_MULTIPLICATION),
        ("s(s+1)", DiagnosticCode.PARSE_IMPLICIT_MULTIPLICATION),
        ("K s", DiagnosticCode.PARSE_IMPLICIT_MULTIPLICATION),
        ("(s+1)(s+2)", DiagnosticCode.PARSE_IMPLICIT_MULTIPLICATION),
        ("(s+1)2", DiagnosticCode.PARSE_IMPLICIT_MULTIPLICATION),
        ("2K", DiagnosticCode.PARSE_IMPLICIT_MULTIPLICATION),
        ("2 3", DiagnosticCode.PARSE_IMPLICIT_MULTIPLICATION),
    ],
)
@pytest.mark.parametrize("attacked_part", ["numerator", "denominator"])
def test_each_pair_field_handles_remaining_attack_matrix(
    source: str,
    expected_code: DiagnosticCode | None,
    attacked_part: str,
) -> None:
    numerator = source if attacked_part == "numerator" else "1"
    denominator = source if attacked_part == "denominator" else "1"

    result = _parser().parse_pair(numerator, denominator)

    assert not result.succeeded
    assert result.diagnostics[0].severity.value == "error"
    if expected_code is not None:
        assert result.diagnostics[0].code is expected_code


@pytest.mark.parametrize(
    ("source", "code"),
    [
        ("s^K", DiagnosticCode.PARSE_INVALID_EXPONENT),
        ("s^(1/2)", DiagnosticCode.PARSE_INVALID_EXPONENT),
        ("s^33", DiagnosticCode.PARSE_LIMIT_EXCEEDED),
        ("__class__", DiagnosticCode.PARSE_FORBIDDEN_NODE),
        ("x+1", DiagnosticCode.PARSE_UNKNOWN_SYMBOL),
    ],
)
def test_shared_ast_rules_keep_diagnostic_codes_consistent(
    source: str,
    code: DiagnosticCode,
) -> None:
    result = _parser().parse_common(source)

    assert not result.succeeded
    assert result.diagnostics[0].code is code


def test_rational_parser_does_not_change_global_sympy_configuration() -> None:
    before = global_parameters.evaluate

    _parser().parse_common("(s+1)/(K*s+1)")
    _parser().parse_pair("s+1", "K*s+1")

    assert global_parameters.evaluate is before
