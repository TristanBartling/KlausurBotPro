"""Tests for token-based input normalization."""

import pytest

from klausurbotpro.domain import DiagnosticCode
from klausurbotpro.parsing import ParserLimits
from klausurbotpro.parsing.normalization import normalize_expression


def _normalize(text: str, limits: ParserLimits | None = None) -> str:
    result = normalize_expression(
        text,
        limits=limits or ParserLimits(),
        allowed_symbols=frozenset({"s", "K", "T"}),
    )
    assert result.succeeded
    assert result.value is not None
    return result.value


@pytest.mark.parametrize(
    ("source", "expected_fragment"),
    [
        ("1,5", "1.5"),
        ("(1,5)", "(1.5 )"),
        ("0,125", "0.125"),
        ("1,5+2", "1.5 +2"),
        ("1.5", "1.5"),
        ("s^2", "s **2"),
        ("s**2", "s **2"),
    ],
)
def test_normalization_uses_tokens(source: str, expected_fragment: str) -> None:
    assert expected_fragment in _normalize(source)


def test_caret_inside_string_is_not_rewritten_naively() -> None:
    assert '"^"' in _normalize('"^"')


@pytest.mark.parametrize(
    "source",
    [
        "1,",
        "1,,",
        ",5",
        "1, 5",
        "(1, 5)",
        "1,2,3",
        "(1,2,3)",
        "(s,K)",
        "1,\t5",
        "1,\n5",
    ],
)
def test_ambiguous_decimal_comma_is_rejected(source: str) -> None:
    result = normalize_expression(
        source,
        limits=ParserLimits(),
        allowed_symbols=frozenset({"s", "K"}),
    )

    assert not result.succeeded
    assert result.diagnostics[0].code is DiagnosticCode.PARSE_INVALID_NUMBER


@pytest.mark.parametrize("source", ["1e3", "1E3", "1e-3", ".5", "1."])
def test_unsupported_number_formats_are_rejected(source: str) -> None:
    result = normalize_expression(source, limits=ParserLimits())

    assert not result.succeeded
    assert result.diagnostics[0].code is DiagnosticCode.PARSE_INVALID_NUMBER


@pytest.mark.parametrize(
    "source",
    [
        "2s",
        "2(s+1)",
        "s(s+1)",
        "K T",
        "s K",
        "(s+1)(s+2)",
        "(s+1)2",
        "2K",
        "2x",
        "2 3",
    ],
)
def test_implicit_multiplication_is_rejected(source: str) -> None:
    result = normalize_expression(
        source,
        limits=ParserLimits(),
        allowed_symbols=frozenset({"s", "K", "T"}),
    )

    assert not result.succeeded
    assert (
        result.diagnostics[0].code
        is DiagnosticCode.PARSE_IMPLICIT_MULTIPLICATION
    )


def test_empty_and_too_long_inputs_have_distinct_codes() -> None:
    empty = normalize_expression("  ", limits=ParserLimits())
    too_long = normalize_expression(
        "1" * 6,
        limits=ParserLimits(max_input_length=5),
    )

    assert empty.diagnostics[0].code is DiagnosticCode.PARSE_EMPTY_INPUT
    assert too_long.diagnostics[0].code is DiagnosticCode.PARSE_LIMIT_EXCEEDED


def test_integer_digit_limit_is_checked_before_ast() -> None:
    result = normalize_expression(
        "12345",
        limits=ParserLimits(max_integer_digits=4),
    )

    assert result.diagnostics[0].code is DiagnosticCode.PARSE_LIMIT_EXCEEDED
