"""Adversarial tests proving the parser's default-deny AST policy."""

import pytest
from sympy.core.parameters import global_parameters

from klausurbotpro.domain import DiagnosticCode
from klausurbotpro.parsing import ParserConfig, SafeExpressionParser


def _parser() -> SafeExpressionParser:
    return SafeExpressionParser(ParserConfig(frozenset({"s", "K"})))


@pytest.mark.parametrize(
    "source",
    [
        '__import__("os")',
        'open("datei")',
        'eval("1+1")',
        "globals()",
        "locals()",
        "s.__class__",
        "().__class__",
        "s[0]",
        "[1, 2]",
        "(1, 2)",
        '{"s": 1}',
        "{1, 2}",
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
    ],
)
def test_forbidden_python_constructs_are_rejected(source: str) -> None:
    result = _parser().parse(source)

    assert not result.succeeded
    assert result.diagnostics[0].code is DiagnosticCode.PARSE_FORBIDDEN_NODE


@pytest.mark.parametrize(
    "source",
    [
        "1+2j",
        "import os",
        "s = 1",
        "yield s",
    ],
)
def test_other_non_math_syntax_is_rejected_without_exception(source: str) -> None:
    result = _parser().parse(source)

    assert not result.succeeded
    assert result.diagnostics[0].severity.value == "error"


@pytest.mark.parametrize("source", ["__import__", "__class__", "__dict__"])
def test_dunder_names_are_always_forbidden(source: str) -> None:
    result = _parser().parse(source)

    assert not result.succeeded
    assert result.diagnostics[0].code is DiagnosticCode.PARSE_FORBIDDEN_NODE


@pytest.mark.parametrize("source", ["2s", "2(s+1)"])
def test_implicit_multiplication_is_rejected_safely(source: str) -> None:
    result = _parser().parse(source)

    assert not result.succeeded
    assert (
        result.diagnostics[0].code
        is DiagnosticCode.PARSE_IMPLICIT_MULTIPLICATION
    )


def test_parser_does_not_change_global_sympy_evaluation_configuration() -> None:
    before = global_parameters.evaluate

    _parser().parse("(s + 1)/(K*s + 1)")

    assert global_parameters.evaluate is before
