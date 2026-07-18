"""Value semantics of semantically constrained reduced transfer functions."""

import inspect
from dataclasses import FrozenInstanceError

import pytest
import sympy as sp

import klausurbotpro.domain.reduced_transfer_function as reduced_module
import klausurbotpro.domain.transfer_function_reducer as reducer_module
from klausurbotpro.domain import (
    CommonTransferFunctionInput,
    RawTransferFunctionFactory,
    ReducedTransferFunction,
    TransferFunctionReducer,
)
from klausurbotpro.domain.raw_algebraic_expression import (
    Add,
    Divide,
    ExactNumber,
    Multiply,
    Symbol,
)


def _reduce(
    expression: object,
    *,
    text: str = "",
    parameters: frozenset[str] = frozenset({"K", "T"}),
) -> ReducedTransferFunction:
    input_value = CommonTransferFunctionInput(
        expression=expression,  # type: ignore[arg-type]
        variable_name="s",
        allowed_symbol_names=parameters | {"s"},
        original_text=text,
        normalized_text=text,
    )
    raw_result = RawTransferFunctionFactory(
        allowed_parameter_names=parameters
    ).create(input_value)
    assert raw_result.value is not None, raw_result.diagnostics
    result = TransferFunctionReducer().reduce(raw_result.value)
    assert result.reduced is not None, result.diagnostics
    return result.reduced


def test_value_is_factory_only_immutable_and_exposes_no_sympy() -> None:
    value = _reduce(Divide(ExactNumber(1), Add(Symbol("s"), ExactNumber(1))))

    with pytest.raises(TypeError):
        ReducedTransferFunction()
    with pytest.raises(FrozenInstanceError):
        value.variable_name = "z"  # type: ignore[misc]
    public_values = (
        value.variable_name,
        value.numerator,
        value.denominator,
        value.prerequisites,
        value.domain_exclusions,
        value.used_parameter_names,
        value.is_zero,
    )
    assert not any(isinstance(item, (sp.Expr, sp.Poly)) for item in public_values)


def test_scalar_multiples_with_distinct_retained_exclusions_remain_unequal() -> None:
    scaled = _reduce(
        Divide(
            Multiply(
                ExactNumber(2),
                Add(Symbol("s"), ExactNumber(1)),
            ),
            Multiply(
                ExactNumber(2),
                Add(Symbol("s"), ExactNumber(2)),
            ),
        )
    )
    plain = _reduce(
        Divide(
            Add(Symbol("s"), ExactNumber(1)),
            Add(Symbol("s"), ExactNumber(2)),
        )
    )

    assert scaled.numerator == plain.numerator
    assert scaled.denominator == plain.denominator
    assert scaled.domain_exclusions != plain.domain_exclusions
    assert scaled != plain


def test_raw_text_and_report_are_not_part_of_reduced_identity() -> None:
    expression = Divide(
        Add(Symbol("s"), ExactNumber(1)),
        Add(Symbol("s"), ExactNumber(2)),
    )
    first = _reduce(expression, text="first")
    second = _reduce(expression, text="second")

    assert first == second
    assert hash(first) == hash(second)
    assert {first: "reduced"}[second] == "reduced"


def test_declaration_sets_and_algebraic_input_form_do_not_change_identity() -> None:
    factored = _reduce(
        Divide(
            Multiply(
                Add(Symbol("s"), ExactNumber(1)),
                Add(Symbol("s"), ExactNumber(2)),
            ),
            Add(Symbol("s"), ExactNumber(3)),
        ),
        parameters=frozenset(),
    )
    expanded = _reduce(
        Divide(
            Add(
                Multiply(Symbol("s"), Symbol("s")),
                Add(Multiply(ExactNumber(3), Symbol("s")), ExactNumber(2)),
            ),
            Add(Symbol("s"), ExactNumber(3)),
        ),
        parameters=frozenset({"unused"}),
    )

    assert factored == expanded
    assert hash(factored) == hash(expanded)
    assert factored.used_parameter_names == frozenset()


def test_retained_domain_conditions_are_part_of_identity() -> None:
    plain = _reduce(ExactNumber(1))
    with_gap = _reduce(
        Divide(
            Add(Symbol("s"), ExactNumber(1)),
            Add(Symbol("s"), ExactNumber(1)),
        )
    )

    assert plain.numerator == with_gap.numerator
    assert plain.denominator == with_gap.denominator
    assert plain != with_gap
    assert with_gap.used_parameter_names == frozenset()


def test_used_parameters_and_zero_are_derived_from_mathematical_fields() -> None:
    value = _reduce(
        Divide(
            ExactNumber(0),
            Add(Multiply(Symbol("K"), Symbol("s")), ExactNumber(1)),
        )
    )

    assert value.is_zero
    assert value.numerator.expression.canonical_text == "0"
    assert value.denominator.expression.canonical_text == "1"
    assert value.used_parameter_names == frozenset({"K"})


def test_domain_reduction_modules_do_not_depend_on_parsing() -> None:
    source = inspect.getsource(reduced_module) + inspect.getsource(reducer_module)

    assert "klausurbotpro.parsing" not in source
