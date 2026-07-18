"""Rule tests for non-cancelling raw rationalization."""

import pytest

from klausurbotpro.domain._raw_expression_validator import (
    RawExpressionValidator,
)
from klausurbotpro.domain._raw_rationalizer import (
    RawRationalizationError,
    RawRationalizer,
    RawRationalPair,
)
from klausurbotpro.domain.raw_algebraic_expression import (
    Add,
    Divide,
    ExactNumber,
    Multiply,
    Power,
    Subtract,
    Symbol,
)
from klausurbotpro.domain.raw_transfer_function_contracts import (
    RawTransferFunctionLimits,
)


def _rationalize(
    expression: object,
    limits: RawTransferFunctionLimits | None = None,
) -> RawRationalPair:
    selected = limits or RawTransferFunctionLimits()
    validator = RawExpressionValidator(
        variable_name="s",
        allowed_parameter_names=frozenset({"K", "T"}),
        limits=selected,
    )
    snapshot = validator.validate_and_snapshot(expression)  # type: ignore[arg-type]
    return RawRationalizer(validator=validator, limits=selected).rationalize(
        snapshot,
        origin="expression",
    )


@pytest.mark.parametrize(
    ("expression", "numerator", "denominator"),
    [
        (Symbol("s"), "symbol(s)", "number(1/1)"),
        (
            Add(Divide(ExactNumber(1), Symbol("s")), ExactNumber(1)),
            "add(multiply(multiply(number(1/1),number(1/1)),number(1/1)),"
            "multiply(number(1/1),multiply(number(1/1),symbol(s))))",
            "multiply(multiply(number(1/1),symbol(s)),number(1/1))",
        ),
        (
            Divide(Divide(Symbol("K"), Symbol("T")), Symbol("s")),
            "multiply(multiply(symbol(K),number(1/1)),number(1/1))",
            "multiply(multiply(number(1/1),symbol(T)),symbol(s))",
        ),
        (
            Subtract(Symbol("s"), Divide(ExactNumber(1), Symbol("T"))),
            "subtract(multiply(symbol(s),multiply(number(1/1),symbol(T))),"
            "multiply(multiply(number(1/1),number(1/1)),number(1/1)))",
            "multiply(number(1/1),multiply(number(1/1),symbol(T)))",
        ),
    ],
)
def test_rationalization_rules_preserve_unreduced_structure(
    expression: object,
    numerator: str,
    denominator: str,
) -> None:
    pair = _rationalize(expression)

    assert pair.numerator_tree.canonical_tree == numerator
    assert pair.denominator_tree.canonical_tree == denominator


def test_divisions_and_negative_powers_record_original_divisors() -> None:
    expression = Multiply(
        Divide(Symbol("K"), Symbol("T")),
        Power(Symbol("s"), ExactNumber(-2)),
    )

    pair = _rationalize(expression)

    assert tuple(
        record.numerator_tree.canonical_tree
        for record in pair.divisor_records
    ) == ("symbol(T)", "symbol(s)")


def test_zero_power_keeps_base_divisor_records_without_pair_content() -> None:
    pair = _rationalize(
        Power(Divide(Symbol("K"), Symbol("T")), ExactNumber(0))
    )

    assert pair.numerator_tree == ExactNumber(1)
    assert pair.denominator_tree == ExactNumber(1)
    assert tuple(
        record.numerator_tree.canonical_tree
        for record in pair.divisor_records
    ) == ("symbol(T)",)


def test_k_over_k_is_not_cancelled() -> None:
    pair = _rationalize(Divide(Symbol("K"), Symbol("K")))

    assert pair.numerator_tree.canonical_tree == (
        "multiply(symbol(K),number(1/1))"
    )
    assert pair.denominator_tree.canonical_tree == (
        "multiply(number(1/1),symbol(K))"
    )


@pytest.mark.parametrize(
    "limits",
    [
        RawTransferFunctionLimits(max_rationalized_occurrences=2),
        RawTransferFunctionLimits(max_intermediate_expressions=1),
        RawTransferFunctionLimits(max_translation_steps=1),
    ],
)
def test_rationalization_growth_is_rejected_before_large_result(
    limits: RawTransferFunctionLimits,
) -> None:
    with pytest.raises(RawRationalizationError):
        _rationalize(Add(Symbol("s"), ExactNumber(1)), limits)
