"""Tests for the discriminated raw rational-input contracts."""

from dataclasses import FrozenInstanceError

import pytest

from klausurbotpro.domain import (
    CommonTransferFunctionInput,
    SeparatedTransferFunctionInput,
    TransferFunctionInputForm,
)
from klausurbotpro.domain.raw_algebraic_expression import (
    Add,
    Divide,
    ExactNumber,
    Symbol,
)


def _separated(
    original_numerator: str = "K",
) -> SeparatedTransferFunctionInput:
    return SeparatedTransferFunctionInput(
        numerator=Symbol("K"),
        denominator=Symbol("s"),
        variable_name="s",
        allowed_symbol_names=frozenset({"K", "s"}),
        original_numerator_text=original_numerator,
        original_denominator_text="s",
        normalized_numerator_text="K",
        normalized_denominator_text="s",
    )


def test_separated_input_has_explicit_form_and_derived_facts() -> None:
    value = _separated()

    assert value.input_form is TransferFunctionInputForm.SEPARATED
    assert value.used_symbol_names == frozenset({"K", "s"})
    assert value.total_node_count == 2


def test_common_input_keeps_one_complete_tree() -> None:
    expression = Divide(Symbol("K"), Symbol("s"))
    value = CommonTransferFunctionInput(
        expression=expression,
        variable_name="s",
        allowed_symbol_names=frozenset({"K", "s"}),
        original_text="K / s",
        normalized_text="K /s",
    )

    assert value.input_form is TransferFunctionInputForm.COMMON
    assert value.expression is expression
    assert value.used_symbol_names == frozenset({"K", "s"})


def test_source_text_is_not_part_of_structural_value_equality() -> None:
    first = _separated("K")
    second = _separated(" K ")

    assert first == second
    assert hash(first) == hash(second)
    assert {first: "input"}[second] == "input"


def test_common_allowed_symbol_context_does_not_affect_identity() -> None:
    expression = Add(Symbol("K"), Symbol("s"))
    first = CommonTransferFunctionInput(
        expression=expression,
        variable_name="s",
        allowed_symbol_names=frozenset({"K", "s"}),
        original_text="K+s",
        normalized_text="K +s",
    )
    second = CommonTransferFunctionInput(
        expression=expression,
        variable_name="s",
        allowed_symbol_names=frozenset({"K", "s", "T", "d"}),
        original_text=" K + s ",
        normalized_text="K +s ",
    )

    assert first.allowed_symbol_names != second.allowed_symbol_names
    assert first == second
    assert hash(first) == hash(second)
    assert {first: "common"}[second] == "common"


def test_separated_allowed_symbol_context_does_not_affect_identity() -> None:
    first = _separated()
    second = SeparatedTransferFunctionInput(
        numerator=Symbol("K"),
        denominator=Symbol("s"),
        variable_name="s",
        allowed_symbol_names=frozenset({"K", "s", "T"}),
        original_numerator_text=" K ",
        original_denominator_text=" s ",
        normalized_numerator_text="K ",
        normalized_denominator_text="s ",
    )

    assert first.allowed_symbol_names != second.allowed_symbol_names
    assert first == second
    assert hash(first) == hash(second)
    assert {first: "separated"}[second] == "separated"


def test_main_variable_remains_part_of_structural_identity() -> None:
    expression = Symbol("K")
    with_s = CommonTransferFunctionInput(
        expression=expression,
        variable_name="s",
        allowed_symbol_names=frozenset({"K", "s", "z"}),
        original_text="K",
        normalized_text="K",
    )
    with_z = CommonTransferFunctionInput(
        expression=expression,
        variable_name="z",
        allowed_symbol_names=frozenset({"K", "s", "z"}),
        original_text="K",
        normalized_text="K",
    )

    assert with_s != with_z


def test_different_raw_tree_remains_structurally_unequal() -> None:
    symbol = CommonTransferFunctionInput(
        expression=Symbol("K"),
        variable_name="s",
        allowed_symbol_names=frozenset({"K", "s"}),
        original_text="K",
        normalized_text="K",
    )
    addition = CommonTransferFunctionInput(
        expression=Add(Symbol("K"), ExactNumber(0)),
        variable_name="s",
        allowed_symbol_names=frozenset({"K", "s"}),
        original_text="K+0",
        normalized_text="K +0",
    )

    assert symbol != addition


def test_input_forms_are_not_interchangeable() -> None:
    separated = _separated()
    common = CommonTransferFunctionInput(
        expression=Divide(Symbol("K"), Symbol("s")),
        variable_name="s",
        allowed_symbol_names=frozenset({"K", "s"}),
        original_text="K/s",
        normalized_text="K /s",
    )

    assert separated != common


def test_input_contracts_are_immutable_and_validate_context() -> None:
    value = _separated()

    with pytest.raises(FrozenInstanceError):
        value.variable_name = "z"  # type: ignore[misc]
    with pytest.raises(ValueError, match="allowed symbol"):
        CommonTransferFunctionInput(
            expression=ExactNumber(1),
            variable_name="s",
            allowed_symbol_names=frozenset({"K"}),
            original_text="1",
            normalized_text="1",
        )
    with pytest.raises(TypeError, match="frozenset"):
        CommonTransferFunctionInput(
            expression=ExactNumber(1),
            variable_name="s",
            allowed_symbol_names={"s"},  # type: ignore[arg-type]
            original_text="1",
            normalized_text="1",
        )
