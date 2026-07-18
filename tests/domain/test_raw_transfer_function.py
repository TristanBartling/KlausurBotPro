"""Value semantics for validated raw transfer functions."""

import inspect
from dataclasses import FrozenInstanceError

import pytest
import sympy as sp

import klausurbotpro.domain as domain_api
import klausurbotpro.domain._raw_transfer_conditions as conditions_module
import klausurbotpro.domain.raw_transfer_function_factory as factory_module
from klausurbotpro.domain import (
    CommonTransferFunctionInput,
    RawTransferFunction,
    RawTransferFunctionFactory,
    SeparatedTransferFunctionInput,
)
from klausurbotpro.domain.raw_algebraic_expression import (
    Add,
    Divide,
    ExactNumber,
    Multiply,
    Power,
    Symbol,
)


def _common(expression: object, *, text: str = "") -> CommonTransferFunctionInput:
    return CommonTransferFunctionInput(
        expression=expression,  # type: ignore[arg-type]
        variable_name="s",
        allowed_symbol_names=frozenset({"s", "K"}),
        original_text=text,
        normalized_text=text,
    )


def _create(expression: object, *, text: str = "") -> RawTransferFunction:
    result = RawTransferFunctionFactory(
        allowed_parameter_names=frozenset({"K"})
    ).create(_common(expression, text=text))
    assert result.value is not None, result.diagnostics
    return result.value


def test_value_is_factory_only_immutable_and_has_no_reduced_value() -> None:
    value = _create(Divide(ExactNumber(1), Add(Symbol("s"), ExactNumber(1))))

    with pytest.raises(TypeError):
        RawTransferFunction()
    with pytest.raises(FrozenInstanceError):
        value.variable_name = "z"  # type: ignore[misc]
    assert not hasattr(value, "reduced_transfer_function")
    assert not hasattr(domain_api, "ReducedTransferFunction")


def test_scalar_multiples_remain_unequal_before_reduction() -> None:
    scaled = _create(
        Divide(
            Add(Multiply(Symbol("K"), Symbol("s")), Symbol("K")),
            Add(
                Multiply(Symbol("K"), Symbol("s")),
                Multiply(ExactNumber(2), Symbol("K")),
            ),
        )
    )
    plain = _create(
        Divide(
            Add(Symbol("s"), ExactNumber(1)),
            Add(Symbol("s"), ExactNumber(2)),
        )
    )

    assert scaled != plain


def test_common_and_separated_forms_can_produce_equal_dictionary_keys() -> None:
    common = _create(Divide(Symbol("K"), Add(Symbol("s"), ExactNumber(1))))
    separated_input = SeparatedTransferFunctionInput(
        numerator=Symbol("K"),
        denominator=Add(Symbol("s"), ExactNumber(1)),
        variable_name="s",
        allowed_symbol_names=frozenset({"s", "K"}),
        original_numerator_text="K",
        original_denominator_text="s+1",
        normalized_numerator_text="K",
        normalized_denominator_text="s+1",
    )
    separated_result = RawTransferFunctionFactory(
        allowed_parameter_names=frozenset({"K"})
    ).create(separated_input)
    assert separated_result.value is not None
    separated = separated_result.value

    assert common == separated
    assert hash(common) == hash(separated)
    assert {common: "raw"}[separated] == "raw"


def test_text_and_unused_input_metadata_do_not_affect_identity() -> None:
    first = _create(Divide(Symbol("K"), Symbol("K")), text="K/K")
    second = _create(Divide(Symbol("K"), Symbol("K")), text="manipulated")

    assert first == second
    assert hash(first) == hash(second)


def test_snapshot_is_disjoint_and_keeps_k_over_k_visible() -> None:
    tree = Divide(Symbol("K"), Symbol("K"))
    value = _create(tree)
    snapshot = value.input_snapshot

    assert isinstance(snapshot, CommonTransferFunctionInput)
    assert snapshot.expression == tree
    assert snapshot.expression is not tree
    assert snapshot.expression.canonical_tree == (
        "divide(symbol(K),symbol(K))"
    )
    assert value.numerator.expression.canonical_text == "K"
    assert value.denominator.expression.canonical_text == "K"


def test_used_parameters_come_from_validated_input_snapshot() -> None:
    value = _create(
        Power(Divide(Symbol("K"), ExactNumber(2)), ExactNumber(0))
    )

    assert value.numerator.expression.canonical_text == "1"
    assert value.denominator.expression.canonical_text == "1"
    assert value.used_parameter_names == frozenset({"K"})


def test_prerequisites_and_exclusions_are_part_of_value_identity() -> None:
    plain = _create(ExactNumber(1))
    with_parameter_gap = _create(
        Power(Divide(Symbol("K"), Symbol("K")), ExactNumber(0))
    )
    with_variable_gap = _create(
        Power(
            Divide(
                Add(Symbol("s"), ExactNumber(1)),
                Add(Symbol("s"), ExactNumber(1)),
            ),
            ExactNumber(0),
        )
    )

    assert plain.numerator == with_parameter_gap.numerator
    assert plain.denominator == with_parameter_gap.denominator
    assert plain != with_parameter_gap
    assert plain != with_variable_gap


def test_public_values_expose_no_sympy_objects() -> None:
    value = _create(Divide(ExactNumber(1), Add(Symbol("s"), ExactNumber(1))))
    public_values = (
        value.variable_name,
        value.numerator,
        value.denominator,
        value.used_parameter_names,
        value.input_snapshot,
        value.prerequisites,
        value.domain_exclusions,
        value.numerator_conditions,
        value.denominator_conditions,
        value.is_zero,
    )

    assert not any(isinstance(item, (sp.Expr, sp.Poly)) for item in public_values)


def test_factory_has_no_parsing_dependency_or_pair_cancellation_call() -> None:
    source = inspect.getsource(factory_module) + inspect.getsource(
        conditions_module
    )

    assert "klausurbotpro.parsing" not in source
    assert "sp.cancel" not in source
    assert "sp.together" not in source
