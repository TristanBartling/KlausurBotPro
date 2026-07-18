"""Functional and resource-limit tests for the safe AST parser."""

import ast
from dataclasses import FrozenInstanceError

import pytest
import sympy as sp

import klausurbotpro.parsing.ast_parser as ast_parser_module
from klausurbotpro.domain import (
    Diagnostic,
    DiagnosticCode,
    DiagnosticSeverity,
    ExactExpression,
)
from klausurbotpro.parsing import (
    ParserConfig,
    ParseResult,
    ParserLimits,
    SafeExpressionParser,
)


def _parser(
    *,
    symbols: frozenset[str] = frozenset({"s", "K", "T", "m", "d"}),
    limits: ParserLimits | None = None,
) -> SafeExpressionParser:
    return SafeExpressionParser(
        ParserConfig(
            allowed_symbols=symbols,
            limits=limits or ParserLimits(),
        )
    )


def _parse(source: str) -> ExactExpression:
    result = _parser().parse(source)
    assert result.succeeded, result.diagnostics
    assert result.value is not None
    return result.value


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("3", "3"),
        ("0", "0"),
        ("-7", "-7"),
        ("+7", "7"),
        ("1/3", "1/3"),
        ("-1/3", "-1/3"),
        ("1.5", "3/2"),
        ("1,5", "3/2"),
        ("0.125", "1/8"),
        ("0,125", "1/8"),
        ("s", "s"),
        ("K*s + 1", "K*s + 1"),
        ("(s+1)/(T*s+1)", "(s + 1)/(T*s + 1)"),
        ("-(-(+s))", "s"),
        ("m*s + d + K", "K + d + m*s"),
    ],
)
def test_valid_expressions_are_exact(source: str, expected: str) -> None:
    expression = _parse(source)

    assert expression.canonical_text == expected
    assert not expression._as_sympy().atoms(sp.Float)


def test_decimal_point_and_comma_are_exactly_equal() -> None:
    point = _parse("1.5")
    comma = _parse("1,5")

    assert point == comma
    assert point._as_sympy() == sp.Rational(3, 2)


def test_operator_precedence_and_associativity() -> None:
    symbol = sp.Symbol("s")

    assert _parse("-s^2")._as_sympy() == -(symbol**2)
    assert _parse("(-s)^2")._as_sympy() == symbol**2
    assert _parse("s^2^3")._as_sympy() == symbol**8


def test_only_actually_used_symbols_are_reported() -> None:
    expression = _parse("K*s + 1")

    assert expression.symbol_names == frozenset({"K", "s"})


def test_unknown_symbol_and_field_are_reported() -> None:
    result = _parser(symbols=frozenset({"s"})).parse("s + x", field="input")

    assert not result.succeeded
    assert result.diagnostics[0].code is DiagnosticCode.PARSE_UNKNOWN_SYMBOL
    assert result.diagnostics[0].field == "input"


@pytest.mark.parametrize(
    ("source", "expected_code"),
    [
        ("1/0", DiagnosticCode.MATH_DIVISION_BY_ZERO),
        ("1/(s-s)", DiagnosticCode.MATH_DIVISION_BY_ZERO),
        ("0^-1", DiagnosticCode.MATH_DIVISION_BY_ZERO),
        ("s^K", DiagnosticCode.PARSE_INVALID_EXPONENT),
        ("s^(1/2)", DiagnosticCode.PARSE_INVALID_EXPONENT),
        ("s^33", DiagnosticCode.PARSE_LIMIT_EXCEEDED),
        ("s^-33", DiagnosticCode.PARSE_LIMIT_EXCEEDED),
    ],
)
def test_controlled_math_failures(
    source: str,
    expected_code: DiagnosticCode,
) -> None:
    result = _parser().parse(source)

    assert not result.succeeded
    assert result.diagnostics[0].code is expected_code


def test_negative_exponent_within_limit_is_allowed() -> None:
    symbol = sp.Symbol("s")
    assert _parse("s^-2")._as_sympy() == symbol**-2


def test_ast_node_limit_is_enforced() -> None:
    result = _parser(
        limits=ParserLimits(max_ast_nodes=5),
    ).parse("s + 1")

    assert result.diagnostics[0].code is DiagnosticCode.PARSE_LIMIT_EXCEEDED
    assert result.diagnostics[0].technical_details == (
        ("limit", "max_ast_nodes"),
    )


def test_ast_depth_limit_is_enforced() -> None:
    result = _parser(
        limits=ParserLimits(max_ast_depth=4),
    ).parse("-(-(-s))")

    assert result.diagnostics[0].code is DiagnosticCode.PARSE_LIMIT_EXCEEDED


def test_deep_input_returns_diagnostic_instead_of_recursion_error() -> None:
    result = _parser().parse("-" * 100 + "s")

    assert not result.succeeded
    assert result.diagnostics[0].code is DiagnosticCode.PARSE_LIMIT_EXCEEDED
    assert result.diagnostics[0].technical_details == (
        ("limit", "max_ast_depth"),
    )


def test_parser_config_accepts_exact_symbol_limit() -> None:
    config = ParserConfig(
        frozenset({"s", "K"}),
        limits=ParserLimits(max_symbols=2),
    )

    assert config.allowed_symbols == frozenset({"s", "K"})


def test_parser_config_rejects_more_than_symbol_limit() -> None:
    with pytest.raises(ValueError, match="exceeds limits.max_symbols"):
        ParserConfig(
            frozenset({"s", "K"}),
            limits=ParserLimits(max_symbols=1),
        )


def test_invalid_config_creates_no_sympy_symbols(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    symbol_calls = 0

    def count_symbol_calls(name: str) -> sp.Symbol:
        nonlocal symbol_calls
        symbol_calls += 1
        return sp.Symbol(name)

    monkeypatch.setattr(sp, "Symbol", count_symbol_calls)

    with pytest.raises(ValueError, match="exceeds limits.max_symbols"):
        SafeExpressionParser(
            ParserConfig(
                frozenset({"s", "K"}),
                limits=ParserLimits(max_symbols=1),
            )
        )

    assert symbol_calls == 0


def test_estimated_term_limit_prevents_expansion_risk() -> None:
    result = _parser().parse("(s + 1)^12")

    assert result.diagnostics[0].code is DiagnosticCode.PARSE_LIMIT_EXCEEDED
    assert result.diagnostics[0].technical_details == (
        ("limit", "max_estimated_terms"),
    )


@pytest.mark.parametrize("invalid_name", ["__class__", "class", "s.x", "x-y"])
def test_parser_config_rejects_invalid_symbol_names(invalid_name: str) -> None:
    with pytest.raises(ValueError, match="Invalid allowed symbol"):
        ParserConfig(frozenset({invalid_name}))


def test_parser_contracts_are_immutable_and_validate_invariants() -> None:
    limits = ParserLimits()
    config = ParserConfig({"s"})  # type: ignore[arg-type]
    success = ParseResult(value=_parse("1"))
    failure = ParseResult[ExactExpression](
        value=None,
        diagnostics=(
            Diagnostic(
                DiagnosticSeverity.ERROR,
                DiagnosticCode.PARSE_INVALID_SYNTAX,
                "Ungültig.",
            ),
        ),
    )

    assert config.allowed_symbols == frozenset({"s"})
    assert success.succeeded
    assert not failure.succeeded
    with pytest.raises(FrozenInstanceError):
        limits.max_ast_nodes = 1  # type: ignore[misc]
    with pytest.raises(ValueError, match="requires an error"):
        ParseResult[ExactExpression](value=None)
    with pytest.raises(ValueError, match="cannot contain an error"):
        ParseResult(
            value=_parse("1"),
            diagnostics=failure.diagnostics,
        )


def test_parser_limits_reject_nonpositive_values() -> None:
    with pytest.raises(ValueError, match="greater than zero"):
        ParserLimits(max_ast_nodes=0)


def test_same_failure_is_deterministic() -> None:
    parser = _parser()

    first = parser.parse("s^K")
    second = parser.parse("s^K")

    assert first == second
    assert first.diagnostics[0].message == second.diagnostics[0].message


def test_same_success_is_deterministic() -> None:
    parser = _parser()

    assert parser.parse("(s + 1)/(K*s + 1)") == parser.parse(
        "(s + 1)/(K*s + 1)"
    )


@pytest.mark.parametrize(
    ("stage", "error_type"),
    [
        ("normalization", MemoryError),
        ("ast", RecursionError),
        ("validation", OverflowError),
        ("translation", MemoryError),
        ("sympy_operation", OverflowError),
        ("exact_expression", RecursionError),
    ],
)
def test_resource_errors_are_deterministic_limit_diagnostics(
    stage: str,
    error_type: type[MemoryError | RecursionError | OverflowError],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parser = _parser()

    def raise_resource_error(*args: object, **kwargs: object) -> None:
        raise error_type

    if stage == "normalization":
        monkeypatch.setattr(
            ast_parser_module,
            "normalize_expression",
            raise_resource_error,
        )
    elif stage == "ast":
        monkeypatch.setattr(
            ast,
            "parse",
            raise_resource_error,
        )
    elif stage == "validation":
        monkeypatch.setattr(
            SafeExpressionParser,
            "_validate_tree",
            raise_resource_error,
        )
    elif stage == "translation":
        monkeypatch.setattr(
            SafeExpressionParser,
            "_translate",
            raise_resource_error,
        )
    elif stage == "sympy_operation":
        monkeypatch.setattr(
            sp,
            "Integer",
            raise_resource_error,
        )
    else:
        monkeypatch.setattr(
            ExactExpression,
            "_from_sympy",
            raise_resource_error,
        )

    source = "1" if stage == "sympy_operation" else "s + 1"
    first = parser.parse(source)
    second = parser.parse(source)

    assert first == second
    assert first.diagnostics[0].code is DiagnosticCode.PARSE_LIMIT_EXCEEDED
    assert first.diagnostics[0].technical_details == (
        ("exception", error_type.__name__),
    )


def test_unexpected_programming_errors_are_not_hidden(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def raise_runtime_error(*args: object, **kwargs: object) -> None:
        raise RuntimeError("programming defect")

    monkeypatch.setattr(
        SafeExpressionParser,
        "_translate",
        raise_runtime_error,
    )

    with pytest.raises(RuntimeError, match="programming defect"):
        _parser().parse("s + 1")
