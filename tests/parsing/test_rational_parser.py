"""Functional tests for input-faithful rational parsing."""

import ast
import inspect

import pytest

import klausurbotpro.parsing.rational_parser as rational_parser_module
from klausurbotpro.domain import (
    Add,
    CommonTransferFunctionInput,
    DiagnosticCode,
    Divide,
    ExactNumber,
    SeparatedTransferFunctionInput,
    UnaryMinus,
)
from klausurbotpro.parsing import (
    ParserConfig,
    ParserLimits,
    SafeRationalExpressionParser,
)


def _parser(
    limits: ParserLimits | None = None,
) -> SafeRationalExpressionParser:
    return SafeRationalExpressionParser(
        ParserConfig(
            frozenset({"s", "K", "T", "T1", "T2"}),
            limits=limits or ParserLimits(),
        )
    )


def _common(source: str) -> CommonTransferFunctionInput:
    result = _parser().parse_common(source)
    assert result.succeeded, result.diagnostics
    assert isinstance(result.value, CommonTransferFunctionInput)
    return result.value


@pytest.mark.parametrize(
    ("source", "canonical"),
    [
        ("K/K", "divide(symbol(K),symbol(K))"),
        ("K-K", "subtract(symbol(K),symbol(K))"),
        (
            "(K-1)*(T+1)",
            "multiply(subtract(symbol(K),number(1/1)),"
            "add(symbol(T),number(1/1)))",
        ),
        (
            "(K-1)*(T+1)/(T+1)",
            "divide(multiply(subtract(symbol(K),number(1/1)),"
            "add(symbol(T),number(1/1))),add(symbol(T),number(1/1)))",
        ),
        (
            "K/(T*T)",
            "divide(symbol(K),multiply(symbol(T),symbol(T)))",
        ),
        (
            "K/(T1*T2)",
            "divide(symbol(K),multiply(symbol(T1),symbol(T2)))",
        ),
        (
            "(K/T)/s",
            "divide(divide(symbol(K),symbol(T)),symbol(s))",
        ),
        (
            "K/(T/s)",
            "divide(symbol(K),divide(symbol(T),symbol(s)))",
        ),
        (
            "(K/s)/(T/s)",
            "divide(divide(symbol(K),symbol(s)),"
            "divide(symbol(T),symbol(s)))",
        ),
        (
            "(K+1)/(T+1) + (K-1)/(T-1)",
            "add(divide(add(symbol(K),number(1/1)),"
            "add(symbol(T),number(1/1))),"
            "divide(subtract(symbol(K),number(1/1)),"
            "subtract(symbol(T),number(1/1))))",
        ),
    ],
)
def test_common_form_preserves_required_raw_structures(
    source: str,
    canonical: str,
) -> None:
    assert _common(source).expression.canonical_tree == canonical


def test_common_form_does_not_require_a_top_level_division() -> None:
    value = _common("K*s + 1")

    assert isinstance(value.expression, Add)


def test_pair_form_retains_both_fields_without_constructing_a_quotient() -> None:
    result = _parser().parse_pair("K-K", "T/T")

    assert result.succeeded
    assert isinstance(result.value, SeparatedTransferFunctionInput)
    assert result.value.numerator.canonical_tree == (
        "subtract(symbol(K),symbol(K))"
    )
    assert result.value.denominator.canonical_tree == (
        "divide(symbol(T),symbol(T))"
    )


@pytest.mark.parametrize(
    ("numerator", "denominator", "used_symbols"),
    [
        ("1", "s+1", frozenset({"s"})),
        ("K*(s+1)", "K*(s+2)", frozenset({"K", "s"})),
        ("0", "s+1", frozenset({"s"})),
        ("K/T", "s+1", frozenset({"K", "T", "s"})),
        ("(K/T)/s", "K/(T/s)", frozenset({"K", "T", "s"})),
        ("K+s", "T+1", frozenset({"K", "T", "s"})),
    ],
)
def test_required_pair_cases_expose_structure_metadata_and_metrics(
    numerator: str,
    denominator: str,
    used_symbols: frozenset[str],
) -> None:
    first = _parser().parse_pair(numerator, denominator)
    second = _parser().parse_pair(numerator, denominator)

    assert first.succeeded
    assert isinstance(first.value, SeparatedTransferFunctionInput)
    assert first.value.original_numerator_text == numerator
    assert first.value.original_denominator_text == denominator
    assert first.value.normalized_numerator_text
    assert first.value.normalized_denominator_text
    assert first.value.used_symbol_names == used_symbols
    assert first.value.total_node_count >= 2
    assert first.value.numerator.depth >= 1
    assert first.value.denominator.depth >= 1
    assert first == second
    assert hash(first.value) == hash(second.value)


@pytest.mark.parametrize(
    "source",
    [
        "1/(s+1)",
        "s/(s+1)",
        "(s+1)/(s+2)",
        "K/K",
        "K*(s+1)/(K*(s+2))",
        "(K/(T*s+1))/(s+2)",
        "1/(s+1)+1/(s+2)",
        "K*s+1",
        "(((K+s)))",
    ],
)
def test_required_common_cases_expose_structure_metadata_and_metrics(
    source: str,
) -> None:
    first = _parser().parse_common(source)
    second = _parser().parse_common(source)

    assert isinstance(first.value, CommonTransferFunctionInput)
    assert first.value.original_text == source
    assert first.value.normalized_text
    assert first.value.total_node_count == first.value.expression.node_count
    assert first.value.expression.depth >= 1
    assert first.value.used_symbol_names == first.value.expression.symbol_names
    assert first == second
    assert hash(first.value) == hash(second.value)


@pytest.mark.parametrize(
    ("first_source", "second_source"),
    [
        ("K/K", "1"),
        ("K*(s+1)", "K*s+K"),
        ("(s+1)/(s+1)", "1"),
        ("(K*T)/K", "T"),
        ("(K-1)/(K-1)", "1"),
        (
            "1/(s+1)+1/(s+2)",
            "(2*s+3)/((s+1)*(s+2))",
        ),
    ],
)
def test_required_algebraic_equivalences_remain_structurally_distinct(
    first_source: str,
    second_source: str,
) -> None:
    first = _common(first_source).expression
    second = _common(second_source).expression

    assert first != second
    assert first.canonical_tree != second.canonical_tree


@pytest.mark.parametrize(
    ("source", "canonical"),
    [
        ("1.5", "number(3/2)"),
        ("1,5", "number(3/2)"),
        ("0.125", "number(1/8)"),
        ("0,125", "number(1/8)"),
        ("-s^2", "unary_minus(power(symbol(s),number(2/1)))"),
        ("(-s)^2", "power(unary_minus(symbol(s)),number(2/1))"),
        (
            "s^2^3",
            "power(symbol(s),power(number(2/1),number(3/1)))",
        ),
    ],
)
def test_exact_numbers_precedence_and_associativity_are_preserved(
    source: str,
    canonical: str,
) -> None:
    assert _common(source).expression.canonical_tree == canonical


def test_zero_denominators_are_syntactically_accepted_for_later_domain_checks() -> None:
    pair = _parser().parse_pair("K", "0")
    common = _common("K/0")

    assert isinstance(pair.value, SeparatedTransferFunctionInput)
    assert pair.value.denominator == ExactNumber(0)
    assert isinstance(common.expression, Divide)
    assert common.expression.right == ExactNumber(0)


def test_original_and_normalized_text_and_used_symbols_are_recorded() -> None:
    value = _common("  K / (T + 1)  ")

    assert value.original_text == "  K / (T + 1)  "
    assert value.normalized_text
    assert value.used_symbol_names == frozenset({"K", "T"})
    assert value.variable_name == "s"
    assert value.allowed_symbol_names == frozenset(
        {"s", "K", "T", "T1", "T2"}
    )


@pytest.mark.parametrize(
    ("numerator", "denominator", "code"),
    [
        (" ", "1", DiagnosticCode.RATIONAL_INPUT_EMPTY_NUMERATOR),
        ("1", "\t", DiagnosticCode.RATIONAL_INPUT_EMPTY_DENOMINATOR),
    ],
)
def test_pair_empty_fields_have_specific_diagnostics(
    numerator: str,
    denominator: str,
    code: DiagnosticCode,
) -> None:
    result = _parser().parse_pair(numerator, denominator, field="tf")

    assert not result.succeeded
    assert result.diagnostics[0].code is code
    assert result.diagnostics[0].field == "tf"


def test_variable_must_be_allowed() -> None:
    result = _parser().parse_common("K/s", variable_name="z", field="tf")

    assert result.diagnostics[0].code is (
        DiagnosticCode.RATIONAL_INPUT_VARIABLE_NOT_ALLOWED
    )
    assert result.diagnostics[0].field == "tf"


def test_wrong_common_python_types_raise_type_error() -> None:
    with pytest.raises(TypeError):
        _parser().parse_common(1)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        _parser().parse_common("s", variable_name=1)  # type: ignore[arg-type]


def test_wrong_pair_python_types_raise_type_error() -> None:
    with pytest.raises(TypeError):
        _parser().parse_pair("1", object())  # type: ignore[arg-type]


def test_combined_pair_length_uses_one_shared_parser_budget() -> None:
    result = _parser(
        ParserLimits(max_input_length=5),
    ).parse_pair("s+s", "K+K")

    assert result.diagnostics[0].code is (
        DiagnosticCode.RATIONAL_INPUT_LIMIT_EXCEEDED
    )
    assert result.diagnostics[0].technical_details == (
        ("limit", "max_combined_input_length"),
    )


def test_each_pair_field_retains_its_individual_length_limit() -> None:
    result = _parser(
        ParserLimits(max_input_length=3),
    ).parse_pair("s+s+s", "1")

    assert result.diagnostics[0].code is DiagnosticCode.PARSE_LIMIT_EXCEEDED
    assert result.diagnostics[0].field == "numerator"
    assert result.diagnostics[0].technical_details == (
        ("limit", "max_input_length"),
    )


def test_total_pair_ast_nodes_use_one_shared_parser_budget() -> None:
    result = _parser(
        ParserLimits(max_ast_nodes=9),
    ).parse_pair("s+1", "K+1")

    assert result.diagnostics[0].code is (
        DiagnosticCode.RATIONAL_INPUT_LIMIT_EXCEEDED
    )
    assert result.diagnostics[0].technical_details == (
        ("limit", "max_total_ast_nodes"),
    )


def test_parser_module_has_no_sympy_dependency_or_translation() -> None:
    source = inspect.getsource(rational_parser_module)

    assert "sympy" not in source.lower()
    assert "ExactExpression" not in source


def test_same_input_and_failure_are_deterministic() -> None:
    parser = _parser()

    assert parser.parse_common("K/K") == parser.parse_common("K/K")
    assert parser.parse_common("s^K") == parser.parse_common("s^K")


def test_unary_nodes_are_not_collapsed() -> None:
    value = _common("-(-(+s))")

    assert isinstance(value.expression, UnaryMinus)


@pytest.mark.parametrize(
    ("stage", "error_type"),
    [
        ("normalization", MemoryError),
        ("ast", RecursionError),
        ("validation", OverflowError),
        ("translation", MemoryError),
    ],
)
def test_resource_errors_become_deterministic_limit_diagnostics(
    stage: str,
    error_type: type[MemoryError | RecursionError | OverflowError],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parser = _parser()

    def raise_resource_error(*args: object, **kwargs: object) -> None:
        raise error_type

    if stage == "normalization":
        monkeypatch.setattr(
            rational_parser_module,
            "normalize_expression",
            raise_resource_error,
        )
    elif stage == "ast":
        monkeypatch.setattr(ast, "parse", raise_resource_error)
    elif stage == "validation":
        monkeypatch.setattr(
            rational_parser_module,
            "validate_safe_ast",
            raise_resource_error,
        )
    else:
        monkeypatch.setattr(
            SafeRationalExpressionParser,
            "_translate",
            raise_resource_error,
        )

    first = parser.parse_common("s+1")
    second = parser.parse_common("s+1")

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
        SafeRationalExpressionParser,
        "_translate",
        raise_runtime_error,
    )

    with pytest.raises(RuntimeError, match="programming defect"):
        _parser().parse_common("s+1")
