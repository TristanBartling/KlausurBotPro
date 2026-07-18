"""Functional and diagnostic tests for RawTransferFunctionFactory."""

from __future__ import annotations

import pytest

import klausurbotpro.domain._raw_expression_to_exact as translator_module
import klausurbotpro.domain._raw_expression_validator as validator_module
import klausurbotpro.domain._raw_rationalizer as rationalizer_module
from klausurbotpro.domain import (
    CommonTransferFunctionInput,
    DiagnosticCode,
    RawTransferFunctionFactory,
    RawTransferFunctionLimits,
    SeparatedTransferFunctionInput,
    TransferFunctionPrerequisiteKind,
)
from klausurbotpro.domain._raw_expression_validator import RawTreeValidationError
from klausurbotpro.domain.raw_algebraic_expression import (
    Add,
    Divide,
    ExactNumber,
    Multiply,
    Power,
    RawAlgebraicExpression,
    Subtract,
    Symbol,
)


def _common(
    expression: object,
    *,
    variable: str = "s",
    allowed: frozenset[str] = frozenset({"s", "K", "T"}),
) -> CommonTransferFunctionInput:
    return CommonTransferFunctionInput(
        expression=expression,  # type: ignore[arg-type]
        variable_name=variable,
        allowed_symbol_names=allowed,
        original_text="not trusted",
        normalized_text="also not trusted",
    )


def _factory(
    *,
    variable: str = "s",
    parameters: frozenset[str] = frozenset({"K", "T"}),
    limits: RawTransferFunctionLimits | None = None,
) -> RawTransferFunctionFactory:
    return RawTransferFunctionFactory(
        expected_variable_name=variable,
        allowed_parameter_names=parameters,
        limits=limits or RawTransferFunctionLimits(),
    )


@pytest.mark.parametrize(
    ("expression", "numerator", "denominator"),
    [
        (
            Divide(ExactNumber(1), Add(Symbol("s"), ExactNumber(1))),
            "1",
            "s + 1",
        ),
        (Divide(Symbol("K"), Symbol("K")), "K", "K"),
        (
            Divide(
                Multiply(Symbol("K"), Add(Symbol("s"), ExactNumber(1))),
                Multiply(Symbol("K"), Add(Symbol("s"), ExactNumber(2))),
            ),
            "K*s + K",
            "K*s + 2*K",
        ),
        (
            Divide(
                Divide(
                    Symbol("K"),
                    Add(Multiply(Symbol("T"), Symbol("s")), ExactNumber(1)),
                ),
                Add(Symbol("s"), ExactNumber(2)),
            ),
            "K",
            "T*s**2 + s*(2*T + 1) + 2",
        ),
        (
            Add(
                Divide(ExactNumber(1), Add(Symbol("s"), ExactNumber(1))),
                Divide(ExactNumber(1), Add(Symbol("s"), ExactNumber(2))),
            ),
            "2*s + 3",
            "s**2 + 3*s + 2",
        ),
        (Add(Symbol("s"), ExactNumber(1)), "s + 1", "1"),
        (Power(Add(Symbol("s"), ExactNumber(1)), ExactNumber(2)), "s**2 + 2*s + 1", "1"),
        (Power(Add(Symbol("s"), ExactNumber(1)), ExactNumber(-1)), "1", "s + 1"),
        (Power(Divide(Symbol("K"), Symbol("T")), ExactNumber(0)), "1", "1"),
    ],
)
def test_valid_common_inputs_are_rationalized_without_pair_reduction(
    expression: object,
    numerator: str,
    denominator: str,
) -> None:
    result = _factory().create(_common(expression))

    assert result.value is not None, result.diagnostics
    assert result.value.numerator.expression.canonical_text == numerator
    assert result.value.denominator.expression.canonical_text == denominator


@pytest.mark.parametrize(
    ("numerator_tree", "denominator_tree"),
    [
        (ExactNumber(1), Add(Symbol("s"), ExactNumber(1))),
        (
            Multiply(Symbol("K"), Add(Symbol("s"), ExactNumber(1))),
            Multiply(Symbol("K"), Add(Symbol("s"), ExactNumber(2))),
        ),
        (Divide(Symbol("K"), Symbol("T")), Add(Symbol("s"), ExactNumber(1))),
        (ExactNumber(0), Add(Symbol("s"), ExactNumber(1))),
        (
            Divide(ExactNumber(1), Add(Symbol("s"), ExactNumber(1))),
            Divide(Symbol("K"), Symbol("T")),
        ),
    ],
)
def test_valid_separated_inputs_support_internal_fractions(
    numerator_tree: object,
    denominator_tree: object,
) -> None:
    value = SeparatedTransferFunctionInput(
        numerator=numerator_tree,  # type: ignore[arg-type]
        denominator=denominator_tree,  # type: ignore[arg-type]
        variable_name="s",
        allowed_symbol_names=frozenset({"s", "K", "T"}),
        original_numerator_text="ignored",
        original_denominator_text="ignored",
        normalized_numerator_text="ignored",
        normalized_denominator_text="ignored",
    )

    result = _factory().create(value)

    assert result.succeeded, result.diagnostics


@pytest.mark.parametrize(
    ("divisor", "prerequisites", "exclusions"),
    [
        (
            Add(Symbol("s"), ExactNumber(1)),
            (),
            ("s + 1 != 0",),
        ),
        (Symbol("K"), ("K != 0",), ()),
        (
            Multiply(Symbol("K"), Symbol("s")),
            ("K != 0",),
            ("K*s != 0",),
        ),
        (
            Add(Multiply(Symbol("K"), Symbol("s")), ExactNumber(1)),
            (),
            ("K*s + 1 != 0",),
        ),
        (
            Add(
                Multiply(
                    Subtract(Symbol("K"), ExactNumber(1)),
                    Symbol("s"),
                ),
                Symbol("T"),
            ),
            ("NOT_ALL_ZERO(K - 1, T)",),
            ("T + s*(K - 1) != 0",),
        ),
    ],
)
def test_divisors_are_classified_into_parameter_and_variable_conditions(
    divisor: RawAlgebraicExpression,
    prerequisites: tuple[str, ...],
    exclusions: tuple[str, ...],
) -> None:
    result = _factory().create(_common(Divide(ExactNumber(1), divisor)))
    assert result.value is not None, result.diagnostics

    assert tuple(
        item.description for item in result.value.prerequisites
    ) == prerequisites
    assert tuple(
        item.description for item in result.value.domain_exclusions
    ) == exclusions


def test_nested_and_repeated_divisors_are_deduplicated_with_origins() -> None:
    repeated = Add(
        Divide(ExactNumber(1), Symbol("K")),
        Divide(ExactNumber(1), Symbol("K")),
    )
    nested = Divide(ExactNumber(1), Divide(Symbol("K"), Symbol("T")))

    repeated_result = _factory().create(_common(repeated))
    nested_result = _factory().create(_common(nested))
    assert repeated_result.value is not None
    assert nested_result.value is not None

    assert tuple(
        item.description for item in repeated_result.value.prerequisites
    ) == ("K != 0",)
    assert len(repeated_result.value.prerequisites[0].origins) >= 2
    assert tuple(
        item.description for item in nested_result.value.prerequisites
    ) == ("K != 0", "T != 0")


def test_repeated_product_divisor_multiplicities_are_normalized() -> None:
    divisor = Multiply(Symbol("K"), Symbol("T"))
    repeated = Add(
        Divide(ExactNumber(1), divisor),
        Divide(ExactNumber(1), divisor),
    )

    result = _factory().create(_common(repeated))
    assert result.value is not None

    assert tuple(
        item.description for item in result.value.prerequisites
    ) == ("K*T != 0",)


@pytest.mark.parametrize(
    "denominator",
    [
        ExactNumber(0),
        Subtract(Symbol("s"), Symbol("s")),
    ],
)
def test_zero_final_denominator_is_rejected(
    denominator: RawAlgebraicExpression,
) -> None:
    result = _factory().create(
        _common(Divide(ExactNumber(1), denominator))
    )

    assert result.value is None
    assert result.diagnostics[0].code is (
        DiagnosticCode.RAW_TRANSFER_ZERO_DENOMINATOR
    )


def test_zero_separated_denominator_is_final_zero_denominator() -> None:
    input_value = SeparatedTransferFunctionInput(
        numerator=ExactNumber(1),
        denominator=ExactNumber(0),
        variable_name="s",
        allowed_symbol_names=frozenset({"s"}),
        original_numerator_text="1",
        original_denominator_text="0",
        normalized_numerator_text="1",
        normalized_denominator_text="0",
    )

    result = _factory(parameters=frozenset()).create(input_value)

    assert result.diagnostics[0].code is (
        DiagnosticCode.RAW_TRANSFER_ZERO_DENOMINATOR
    )


def test_zero_original_divisor_is_detected_even_if_zero_power_removes_pair() -> None:
    result = _factory().create(
        _common(
            Power(
                Divide(ExactNumber(1), ExactNumber(0)),
                ExactNumber(0),
            )
        )
    )

    assert result.diagnostics[0].code is DiagnosticCode.RAW_TRANSFER_ZERO_DIVISOR


def test_final_denominator_degree_condition_is_not_a_prerequisite() -> None:
    result = _factory().create(
        _common(
            Divide(
                ExactNumber(1),
                Add(Multiply(Symbol("K"), Symbol("s")), ExactNumber(1)),
            )
        )
    )
    assert result.value is not None

    assert result.value.prerequisites == ()
    assert result.value.denominator.degree_info.guaranteed_degree is None
    assert result.value.denominator_conditions


def test_numerator_polynomial_conditions_are_exposed_but_not_prerequisites() -> None:
    result = _factory().create(
        _common(Add(Multiply(Symbol("K"), Symbol("s")), ExactNumber(1)))
    )
    assert result.value is not None

    assert result.value.prerequisites == ()
    assert result.value.numerator_conditions


def test_custom_variable_and_factory_configuration_are_authoritative() -> None:
    valid = _factory(variable="z", parameters=frozenset({"K"})).create(
        _common(
            Divide(ExactNumber(1), Add(Symbol("z"), ExactNumber(1))),
            variable="z",
            allowed=frozenset({"z", "K", "unused"}),
        )
    )
    mismatch = _factory().create(
        _common(ExactNumber(1), variable="z", allowed=frozenset({"z"}))
    )
    undeclared = _factory(parameters=frozenset()).create(
        _common(Symbol("K"))
    )

    assert valid.value is not None
    assert valid.value.variable_name == "z"
    assert mismatch.diagnostics[0].code is (
        DiagnosticCode.RAW_TRANSFER_VARIABLE_MISMATCH
    )
    assert undeclared.diagnostics[0].code is (
        DiagnosticCode.RAW_TRANSFER_UNDECLARED_SYMBOL
    )


def test_input_metadata_is_not_a_mathematical_source() -> None:
    input_value = _common(ExactNumber(1))
    object.__setattr__(input_value, "original_text", "1/0")
    object.__setattr__(input_value, "normalized_text", "evil(s)")
    object.__setattr__(input_value, "allowed_symbol_names", frozenset({"anything"}))

    result = _factory().create(input_value)

    assert result.value is not None
    assert result.value.numerator.expression.canonical_text == "1"
    assert result.value.denominator.expression.canonical_text == "1"


def test_factory_configuration_rejects_variable_parameter_conflict() -> None:
    with pytest.raises(ValueError, match="cannot also"):
        RawTransferFunctionFactory(
            expected_variable_name="s",
            allowed_parameter_names=frozenset({"s"}),
        )


def test_input_subclasses_and_object_setattr_manipulation_are_rejected() -> None:
    class InputSubclass(CommonTransferFunctionInput):
        pass

    with pytest.raises(TypeError, match="supported"):
        _factory().create(
            InputSubclass(
                expression=ExactNumber(1),
                variable_name="s",
                allowed_symbol_names=frozenset({"s"}),
                original_text="1",
                normalized_text="1",
            )
        )

    manipulated = _common(ExactNumber(1))
    object.__setattr__(manipulated, "expression", object())
    result = _factory().create(manipulated)
    assert result.diagnostics[0].code is DiagnosticCode.RAW_TRANSFER_INVALID_TREE


@pytest.mark.parametrize(
    ("limits", "expression"),
    [
        (
            RawTransferFunctionLimits(max_numerator_degree=1),
            Power(Symbol("s"), ExactNumber(2)),
        ),
        (
            RawTransferFunctionLimits(max_denominator_degree=1),
            Divide(ExactNumber(1), Power(Symbol("s"), ExactNumber(2))),
        ),
        (
            RawTransferFunctionLimits(max_prerequisites=1),
            Add(
                Divide(ExactNumber(1), Symbol("K")),
                Divide(ExactNumber(1), Symbol("T")),
            ),
        ),
        (
            RawTransferFunctionLimits(max_domain_exclusions=1),
            Add(
                Divide(
                    ExactNumber(1),
                    Add(Symbol("s"), ExactNumber(1)),
                ),
                Divide(
                    ExactNumber(1),
                    Add(Symbol("s"), ExactNumber(2)),
                ),
            ),
        ),
    ],
)
def test_post_rationalization_limits_have_stable_diagnostic(
    limits: RawTransferFunctionLimits,
    expression: RawAlgebraicExpression,
) -> None:
    result = _factory(limits=limits).create(_common(expression))

    assert result.diagnostics[0].code is DiagnosticCode.RAW_TRANSFER_LIMIT_EXCEEDED


@pytest.mark.parametrize(
    "stage",
    ["validation", "rationalization", "translation"],
)
@pytest.mark.parametrize(
    "error_type",
    [MemoryError, RecursionError, OverflowError],
)
def test_resource_errors_at_each_stage_are_structured(
    stage: str,
    error_type: type[MemoryError | RecursionError | OverflowError],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def raise_resource_error(*args: object, **kwargs: object) -> None:
        raise error_type

    if stage == "validation":
        monkeypatch.setattr(
            validator_module.RawExpressionValidator,
            "validate_and_snapshot",
            raise_resource_error,
        )
    elif stage == "rationalization":
        monkeypatch.setattr(
            rationalizer_module.RawRationalizer,
            "rationalize",
            raise_resource_error,
        )
    else:
        monkeypatch.setattr(
            translator_module.RawExpressionToExact,
            "translate",
            raise_resource_error,
        )

    result = _factory().create(_common(ExactNumber(1)))

    assert result.diagnostics[0].code is (
        DiagnosticCode.RAW_TRANSFER_RESOURCE_LIMIT_EXCEEDED
    )
    assert result.diagnostics[0].technical_details == (
        ("exception", error_type.__name__),
    )


def test_cyclic_factory_input_has_specific_diagnostic() -> None:
    tree = Add(ExactNumber(1), ExactNumber(2))
    input_value = _common(tree)
    object.__setattr__(tree, "left", tree)

    result = _factory().create(input_value)

    assert result.diagnostics[0].code is DiagnosticCode.RAW_TRANSFER_CYCLIC_TREE


def test_validator_failure_is_not_reconstructed_from_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def reject(*args: object, **kwargs: object) -> None:
        raise RawTreeValidationError("forged")

    monkeypatch.setattr(
        validator_module.RawExpressionValidator,
        "validate_and_snapshot",
        reject,
    )
    result = _factory().create(_common(ExactNumber(1)))

    assert result.diagnostics[0].code is DiagnosticCode.RAW_TRANSFER_INVALID_TREE


def test_is_zero_and_used_parameters_are_derived() -> None:
    result = _factory().create(
        _common(
            Divide(
                ExactNumber(0),
                Add(Multiply(Symbol("K"), Symbol("s")), ExactNumber(1)),
            )
        )
    )
    assert result.value is not None

    assert result.value.is_zero
    assert result.value.used_parameter_names == frozenset({"K"})
    assert all(
        item.kind is not TransferFunctionPrerequisiteKind.EXPRESSION_NONZERO
        or item.description != "K != 0"
        for item in result.value.prerequisites
    )
