"""Defensive tests for untrusted raw expression trees."""

from __future__ import annotations

import pytest

from klausurbotpro.domain._raw_expression_validator import (
    RawExpressionValidator,
    RawTreeValidationError,
)
from klausurbotpro.domain.raw_algebraic_expression import (
    Add,
    ExactNumber,
    Power,
    Symbol,
)
from klausurbotpro.domain.raw_transfer_function_contracts import (
    RawTransferFunctionLimits,
)


def _validator(
    limits: RawTransferFunctionLimits | None = None,
) -> RawExpressionValidator:
    return RawExpressionValidator(
        variable_name="s",
        allowed_parameter_names=frozenset({"K"}),
        limits=limits or RawTransferFunctionLimits(),
    )


def test_snapshot_has_no_alias_to_any_source_node() -> None:
    shared = Add(Symbol("K"), ExactNumber(1))
    source = Add(shared, shared)

    snapshot = _validator().validate_and_snapshot(source)

    assert snapshot == source
    assert snapshot is not source
    assert isinstance(snapshot, Add)
    assert snapshot.left is not shared
    assert snapshot.right is not shared
    assert snapshot.left is not snapshot.right


def test_unknown_exact_type_and_subclass_are_rejected() -> None:
    class Unknown:
        pass

    class SymbolSubclass(Symbol):
        pass

    with pytest.raises(RawTreeValidationError, match="unknown node"):
        _validator().validate_and_snapshot(Unknown())  # type: ignore[arg-type]
    with pytest.raises(RawTreeValidationError, match="unknown node"):
        _validator().validate_and_snapshot(SymbolSubclass("K"))


def test_cycle_and_invalid_child_are_rejected() -> None:
    cyclic = Add(ExactNumber(1), ExactNumber(2))
    object.__setattr__(cyclic, "left", cyclic)
    invalid_child = Add(ExactNumber(1), ExactNumber(2))
    object.__setattr__(invalid_child, "right", 3)

    with pytest.raises(RawTreeValidationError) as cycle_error:
        _validator().validate_and_snapshot(cyclic)
    with pytest.raises(RawTreeValidationError, match="child"):
        _validator().validate_and_snapshot(invalid_child)

    assert cycle_error.value.cyclic


@pytest.mark.parametrize(
    ("attribute", "value"),
    [
        ("numerator", True),
        ("denominator", False),
        ("denominator", -1),
        ("numerator", 2),
    ],
)
def test_manipulated_exact_number_is_revalidated(
    attribute: str,
    value: object,
) -> None:
    number = ExactNumber(1)
    object.__setattr__(number, attribute, value)
    if attribute == "numerator" and value == 2:
        object.__setattr__(number, "denominator", 4)

    with pytest.raises(RawTreeValidationError, match="exact number"):
        _validator().validate_and_snapshot(number)


def test_manipulated_symbol_and_undeclared_symbol_are_rejected() -> None:
    manipulated = Symbol("K")
    object.__setattr__(manipulated, "name", "__class__")

    with pytest.raises(RawTreeValidationError, match="invalid symbol"):
        _validator().validate_and_snapshot(manipulated)
    with pytest.raises(RawTreeValidationError) as error:
        _validator().validate_and_snapshot(Symbol("T"))

    assert error.value.undeclared_symbol == "T"


def test_raw_node_and_depth_limits_count_shared_occurrences_and_pairs() -> None:
    validator = _validator(
        RawTransferFunctionLimits(max_raw_nodes=3, max_raw_depth=2)
    )
    validator.validate_and_snapshot(Add(Symbol("K"), ExactNumber(1)))

    with pytest.raises(RawTreeValidationError) as pair_error:
        validator.validate_and_snapshot(ExactNumber(1))
    assert pair_error.value.limit_name == "max_raw_nodes"

    deep = Add(Add(ExactNumber(1), ExactNumber(2)), ExactNumber(3))
    with pytest.raises(RawTreeValidationError) as depth_error:
        _validator(
            RawTransferFunctionLimits(max_raw_depth=2)
        ).validate_and_snapshot(deep)
    assert depth_error.value.limit_name == "max_raw_depth"


def test_integer_digit_and_exponent_limits_apply_before_translation() -> None:
    with pytest.raises(RawTreeValidationError) as digits:
        _validator(
            RawTransferFunctionLimits(max_integer_digits=2)
        ).validate_and_snapshot(ExactNumber(100))
    assert digits.value.limit_name == "max_integer_digits"

    with pytest.raises(RawTreeValidationError) as exponent:
        _validator(
            RawTransferFunctionLimits(max_exponent_abs=2)
        ).validate_and_snapshot(Power(Symbol("s"), ExactNumber(3)))
    assert exponent.value.limit_name == "max_exponent_abs"


@pytest.mark.parametrize(
    "exponent",
    [
        Symbol("K"),
        ExactNumber(1, 2),
    ],
)
def test_exponents_must_be_purely_numeric_integers(exponent: object) -> None:
    with pytest.raises(RawTreeValidationError):
        _validator().validate_and_snapshot(
            Power(Symbol("s"), exponent)  # type: ignore[arg-type]
        )
