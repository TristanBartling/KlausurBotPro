"""Tests for the discriminated raw rational-input contracts."""

from dataclasses import FrozenInstanceError

import pytest

from klausurbotpro.domain import (
    CommonTransferFunctionInput,
    Divide,
    ExactNumber,
    SeparatedTransferFunctionInput,
    Symbol,
    TransferFunctionInputForm,
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
