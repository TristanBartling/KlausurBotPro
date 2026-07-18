"""Acceptance, invariant, and resource tests for exact pair reduction."""

from __future__ import annotations

import inspect

import pytest
import sympy as sp
from sympy.core.parameters import global_parameters

import klausurbotpro.domain._exact_transfer_reduction as exact_module
import klausurbotpro.domain.transfer_function_reducer as reducer_module
from klausurbotpro.domain import (
    CommonTransferFunctionInput,
    DiagnosticCode,
    ExactExpression,
    PolynomialFactory,
    RawTransferFunction,
    RawTransferFunctionFactory,
    TransferFunctionDomainExclusion,
    TransferFunctionPrerequisite,
    TransferFunctionPrerequisiteKind,
    TransferFunctionReducer,
    TransferFunctionReductionLimits,
    TransferFunctionReductionStepKind,
)
from klausurbotpro.domain.raw_algebraic_expression import (
    Add,
    Divide,
    ExactNumber,
    Multiply,
    RawAlgebraicExpression,
    Subtract,
    Symbol,
)


def _add(
    *values: RawAlgebraicExpression,
) -> RawAlgebraicExpression:
    result = values[0]
    for value in values[1:]:
        result = Add(result, value)
    return result


def _multiply(
    *values: RawAlgebraicExpression,
) -> RawAlgebraicExpression:
    result = values[0]
    for value in values[1:]:
        result = Multiply(result, value)
    return result


def _raw(
    expression: object,
    *,
    parameters: frozenset[str] = frozenset({"K", "T"}),
) -> RawTransferFunction:
    input_value = CommonTransferFunctionInput(
        expression=expression,  # type: ignore[arg-type]
        variable_name="s",
        allowed_symbol_names=parameters | {"s"},
        original_text="not mathematical",
        normalized_text="not mathematical",
    )
    result = RawTransferFunctionFactory(
        allowed_parameter_names=parameters
    ).create(input_value)
    assert result.value is not None, result.diagnostics
    return result.value


def _reduced_pair(
    expression: object,
    *,
    parameters: frozenset[str] = frozenset({"K", "T"}),
) -> tuple[str, str]:
    result = TransferFunctionReducer().reduce(
        _raw(expression, parameters=parameters)
    )
    assert result.reduced is not None, result.diagnostics
    return (
        result.reduced.numerator.expression.canonical_text,
        result.reduced.denominator.expression.canonical_text,
    )


@pytest.mark.parametrize(
    ("expression", "parameters", "expected"),
    [
        (
            Divide(
                Add(Symbol("s"), ExactNumber(1)),
                Add(Symbol("s"), ExactNumber(1)),
            ),
            frozenset(),
            ("1", "1"),
        ),
        (
            Divide(
                _multiply(
                    Add(Symbol("s"), ExactNumber(1)),
                    Add(Symbol("s"), ExactNumber(2)),
                ),
                Add(Symbol("s"), ExactNumber(1)),
            ),
            frozenset(),
            ("s + 2", "1"),
        ),
        (
            Divide(
                _multiply(Symbol("K"), Add(Symbol("s"), ExactNumber(1))),
                _multiply(Symbol("K"), Add(Symbol("s"), ExactNumber(2))),
            ),
            frozenset({"K"}),
            ("s + 1", "s + 2"),
        ),
        (
            Divide(
                Add(Multiply(Symbol("K"), Symbol("s")), Symbol("K")),
                Add(
                    Multiply(Symbol("K"), Symbol("s")),
                    Multiply(ExactNumber(2), Symbol("K")),
                ),
            ),
            frozenset({"K"}),
            ("s + 1", "s + 2"),
        ),
        (
            Divide(
                _multiply(
                    Subtract(Symbol("K"), ExactNumber(1)),
                    Add(Symbol("s"), ExactNumber(1)),
                ),
                _multiply(
                    Subtract(Symbol("K"), ExactNumber(1)),
                    Add(Symbol("s"), ExactNumber(2)),
                ),
            ),
            frozenset({"K"}),
            ("s + 1", "s + 2"),
        ),
        (
            Divide(
                Add(Multiply(Symbol("K"), Symbol("s")), ExactNumber(1)),
                Add(Multiply(Symbol("K"), Symbol("s")), ExactNumber(1)),
            ),
            frozenset({"K"}),
            ("1", "1"),
        ),
        (
            Divide(
                Add(Multiply(Symbol("T"), Symbol("s")), ExactNumber(1)),
                Add(Multiply(Symbol("T"), Symbol("s")), ExactNumber(1)),
            ),
            frozenset({"T"}),
            ("1", "1"),
        ),
        (
            Divide(
                ExactNumber(1),
                Add(Multiply(Symbol("T"), Symbol("s")), ExactNumber(1)),
            ),
            frozenset({"T"}),
            ("1", "T*s + 1"),
        ),
        (
            Divide(
                ExactNumber(1),
                Add(Multiply(Symbol("K"), Symbol("s")), Symbol("K")),
            ),
            frozenset({"K"}),
            ("1/K", "s + 1"),
        ),
        (
            Divide(
                Divide(
                    _multiply(Symbol("K"), Add(Symbol("s"), ExactNumber(1))),
                    Symbol("T"),
                ),
                Divide(
                    _multiply(Symbol("K"), Add(Symbol("s"), ExactNumber(2))),
                    Symbol("T"),
                ),
            ),
            frozenset({"K", "T"}),
            ("s + 1", "s + 2"),
        ),
        (
            Divide(ExactNumber(0), Add(Symbol("s"), ExactNumber(1))),
            frozenset(),
            ("0", "1"),
        ),
        (
            Add(Symbol("s"), ExactNumber(1)),
            frozenset(),
            ("s + 1", "1"),
        ),
        (
            Divide(
                _multiply(ExactNumber(2), Add(Symbol("s"), ExactNumber(1))),
                _multiply(ExactNumber(4), Add(Symbol("s"), ExactNumber(2))),
            ),
            frozenset(),
            ("s + 1", "2*s + 4"),
        ),
    ],
)
def test_exact_reduction_acceptance_cases(
    expression: object,
    parameters: frozenset[str],
    expected: tuple[str, str],
) -> None:
    assert _reduced_pair(expression, parameters=parameters) == expected


def test_exact_decimals_do_not_trigger_near_cancellation() -> None:
    expression = Divide(
        Add(Symbol("s"), ExactNumber(10000001, 10000000)),
        Add(
            Symbol("s"),
            ExactNumber(1),
        ),
    )

    assert _reduced_pair(expression, parameters=frozenset()) == (
        "10000000*s + 10000001",
        "10000000*s + 10000000",
    )


def test_cancelled_raw_exclusions_and_prerequisites_are_preserved_exactly() -> None:
    expression = Divide(
        _multiply(Symbol("K"), Add(Symbol("s"), ExactNumber(1))),
        _multiply(Symbol("K"), Add(Symbol("s"), ExactNumber(1))),
    )
    raw = _raw(expression, parameters=frozenset({"K"}))
    result = TransferFunctionReducer().reduce(raw)
    assert result.reduced is not None

    assert result.reduced.prerequisites == raw.prerequisites
    assert result.reduced.domain_exclusions == raw.domain_exclusions
    assert tuple(item.description for item in result.reduced.prerequisites) == (
        "K != 0",
    )
    assert tuple(item.description for item in result.reduced.domain_exclusions) == (
        "K*s + K != 0",
    )


@pytest.mark.parametrize(
    ("expression", "parameters", "prerequisites", "exclusions"),
    [
        (
            Divide(
                Add(Symbol("s"), ExactNumber(1)),
                Add(Symbol("s"), ExactNumber(1)),
            ),
            frozenset(),
            (),
            ("s + 1 != 0",),
        ),
        (
            Divide(
                _multiply(
                    Subtract(Symbol("K"), ExactNumber(1)),
                    Add(Symbol("s"), ExactNumber(1)),
                ),
                _multiply(
                    Subtract(Symbol("K"), ExactNumber(1)),
                    Add(Symbol("s"), ExactNumber(2)),
                ),
            ),
            frozenset({"K"}),
            ("K - 1 != 0",),
            ("2*K + s*(K - 1) - 2 != 0",),
        ),
        (
            Divide(
                Add(Multiply(Symbol("K"), Symbol("s")), ExactNumber(1)),
                Add(Multiply(Symbol("K"), Symbol("s")), ExactNumber(1)),
            ),
            frozenset({"K"}),
            (),
            ("K*s + 1 != 0",),
        ),
        (
            Divide(
                Divide(
                    _multiply(Symbol("K"), Add(Symbol("s"), ExactNumber(1))),
                    Symbol("T"),
                ),
                Divide(
                    _multiply(Symbol("K"), Add(Symbol("s"), ExactNumber(2))),
                    Symbol("T"),
                ),
            ),
            frozenset({"K", "T"}),
            ("K != 0", "K*T != 0", "T != 0"),
            ("K*T*s + 2*K*T != 0", "K*s + 2*K != 0"),
        ),
        (
            Divide(ExactNumber(0), Add(Symbol("s"), ExactNumber(1))),
            frozenset(),
            (),
            ("s + 1 != 0",),
        ),
    ],
)
def test_acceptance_cases_retain_the_complete_raw_domain(
    expression: object,
    parameters: frozenset[str],
    prerequisites: tuple[str, ...],
    exclusions: tuple[str, ...],
) -> None:
    raw = _raw(expression, parameters=parameters)
    result = TransferFunctionReducer().reduce(raw)
    assert result.reduced is not None

    assert result.reduced.prerequisites == raw.prerequisites
    assert result.reduced.domain_exclusions == raw.domain_exclusions
    assert tuple(
        item.description for item in result.reduced.prerequisites
    ) == prerequisites
    assert tuple(
        item.description for item in result.reduced.domain_exclusions
    ) == exclusions


def test_symbolic_leading_scale_without_proof_is_not_divided() -> None:
    raw = _raw(
        Divide(
            ExactNumber(1),
            Add(Multiply(Symbol("T"), Symbol("s")), ExactNumber(1)),
        ),
        parameters=frozenset({"T"}),
    )
    result = TransferFunctionReducer().reduce(raw, field="transfer_function")
    assert result.reduced is not None
    assert result.report is not None

    assert result.reduced.denominator.expression.canonical_text == "T*s + 1"
    assert result.report.steps[0].kind is TransferFunctionReductionStepKind.NO_REDUCTION
    assert result.diagnostics[0].code is (
        DiagnosticCode.TRANSFER_REDUCTION_NORMALIZATION_SKIPPED
    )
    assert result.diagnostics[0].field == "transfer_function"


def test_report_is_exact_ordered_and_deterministic() -> None:
    raw = _raw(
        Divide(
            _multiply(ExactNumber(-2), Add(Symbol("s"), ExactNumber(1))),
            _multiply(ExactNumber(-4), Add(Symbol("s"), ExactNumber(2))),
        ),
        parameters=frozenset(),
    )

    first = TransferFunctionReducer().reduce(raw)
    second = TransferFunctionReducer().reduce(raw)

    assert first.report == second.report
    assert first.report is not None
    assert tuple(step.kind for step in first.report.steps) == (
        TransferFunctionReductionStepKind.REMOVE_COMMON_NUMERIC_FACTOR,
        TransferFunctionReductionStepKind.NORMALIZE_SIGN,
    )
    assert tuple(
        step.factor.canonical_text if step.factor is not None else None
        for step in first.report.steps
    ) == ("2", "-1")


def test_parameter_denominator_clearing_is_reported_with_its_proof() -> None:
    s, K, T = sp.symbols("s K T")
    factory = PolynomialFactory()
    numerator = factory.create(
        ExactExpression._from_sympy(K / T * (s + 1)),
        declared_parameter_names=frozenset({"K", "T"}),
    ).value
    denominator = factory.create(
        ExactExpression._from_sympy(K / T * (s + 2)),
        declared_parameter_names=frozenset({"K", "T"}),
    ).value
    assert numerator is not None
    assert denominator is not None
    prerequisites = (
        TransferFunctionPrerequisite(
            TransferFunctionPrerequisiteKind.EXPRESSION_NONZERO,
            (ExactExpression._from_sympy(K),),
            ("test",),
        ),
        TransferFunctionPrerequisite(
            TransferFunctionPrerequisiteKind.EXPRESSION_NONZERO,
            (ExactExpression._from_sympy(T),),
            ("test",),
        ),
    )
    raw = RawTransferFunction._create(
        variable_name="s",
        numerator=numerator,
        denominator=denominator,
        input_snapshot=CommonTransferFunctionInput(
            expression=ExactNumber(1),
            variable_name="s",
            allowed_symbol_names=frozenset({"s"}),
            original_text="provenance only",
            normalized_text="provenance only",
        ),
        prerequisites=prerequisites,
        domain_exclusions=(
            TransferFunctionDomainExclusion(denominator, ("test",)),
        ),
    )

    result = TransferFunctionReducer().reduce(raw)
    assert result.reduced is not None, result.diagnostics
    assert result.report is not None

    assert (
        result.reduced.numerator.expression.canonical_text,
        result.reduced.denominator.expression.canonical_text,
    ) == ("s + 1", "s + 2")
    first_step = result.report.steps[0]
    assert first_step.kind is (
        TransferFunctionReductionStepKind.CLEAR_PARAMETER_DENOMINATORS
    )
    assert tuple(
        item.description for item in first_step.prerequisites_used
    ) == ("T != 0",)


@pytest.mark.parametrize(
    ("limits", "expected_limit"),
    [
        (TransferFunctionReductionLimits(max_parameters=1), "max_parameters"),
        (TransferFunctionReductionLimits(max_input_terms=1), "max_input_terms"),
        (
            TransferFunctionReductionLimits(max_input_expression_nodes=1),
            "max_input_expression_nodes",
        ),
        (
            TransferFunctionReductionLimits(max_multivariate_total_degree=1),
            "max_multivariate_total_degree",
        ),
        (
            TransferFunctionReductionLimits(max_multivariate_terms=1),
            "max_multivariate_terms",
        ),
        (
            TransferFunctionReductionLimits(max_coefficient_digits=1),
            "max_coefficient_digits",
        ),
        (
            TransferFunctionReductionLimits(max_common_factor_nodes=1),
            "max_common_factor_nodes",
        ),
        (
            TransferFunctionReductionLimits(max_result_nodes=1),
            "max_result_nodes",
        ),
        (
            TransferFunctionReductionLimits(max_reduction_steps=1),
            "max_reduction_steps",
        ),
    ],
)
def test_resource_limits_have_stable_diagnostics(
    limits: TransferFunctionReductionLimits,
    expected_limit: str,
) -> None:
    expression: RawAlgebraicExpression
    if expected_limit == "max_parameters":
        expression = Add(Symbol("K"), Symbol("T"))
        parameters = frozenset({"K", "T"})
    elif expected_limit in (
        "max_input_terms",
        "max_input_expression_nodes",
    ):
        expression = Add(Symbol("s"), ExactNumber(1))
        parameters = frozenset()
    elif expected_limit == "max_multivariate_total_degree":
        expression = Divide(
            Add(_multiply(Symbol("s"), Symbol("s")), ExactNumber(1)),
            Add(Symbol("s"), ExactNumber(1)),
        )
        parameters = frozenset()
    elif expected_limit == "max_multivariate_terms":
        expression = Add(Symbol("s"), ExactNumber(1))
        parameters = frozenset()
    elif expected_limit == "max_coefficient_digits":
        expression = Multiply(ExactNumber(99), Symbol("s"))
        parameters = frozenset()
    elif expected_limit == "max_common_factor_nodes":
        common = Add(Symbol("s"), ExactNumber(1))
        expression = Divide(
            _multiply(common, Add(Symbol("s"), ExactNumber(2))),
            _multiply(common, Add(Symbol("s"), ExactNumber(3))),
        )
        parameters = frozenset()
    elif expected_limit == "max_result_nodes":
        expression = Add(Symbol("s"), ExactNumber(1))
        parameters = frozenset()
    else:
        expression = Divide(
            _multiply(ExactNumber(-2), Add(Symbol("s"), ExactNumber(1))),
            _multiply(ExactNumber(-4), Add(Symbol("s"), ExactNumber(2))),
        )
        parameters = frozenset()
    result = TransferFunctionReducer(limits).reduce(
        _raw(expression, parameters=parameters)
    )

    assert result.reduced is None
    assert result.diagnostics[0].code is (
        DiagnosticCode.TRANSFER_REDUCTION_LIMIT_EXCEEDED
    )
    assert result.diagnostics[0].technical_details == (
        ("limit", expected_limit),
    )


def test_manipulated_raw_value_is_rejected_defensively() -> None:
    raw = _raw(ExactNumber(1), parameters=frozenset())
    object.__setattr__(raw, "used_parameter_names", frozenset({"forged"}))

    result = TransferFunctionReducer().reduce(raw)

    assert result.diagnostics[0].code is (
        DiagnosticCode.TRANSFER_REDUCTION_INVALID_RAW_VALUE
    )


def test_manipulated_raw_cannot_remove_required_denominator_prerequisite() -> None:
    raw = _raw(
        Divide(
            ExactNumber(1),
            Multiply(Symbol("K"), Add(Symbol("s"), ExactNumber(1))),
        ),
        parameters=frozenset({"K"}),
    )
    object.__setattr__(raw, "prerequisites", ())

    result = TransferFunctionReducer().reduce(raw)

    assert result.diagnostics[0].code is (
        DiagnosticCode.TRANSFER_REDUCTION_INVALID_RAW_VALUE
    )


@pytest.mark.parametrize(
    "error_type",
    [MemoryError, RecursionError, OverflowError],
)
def test_resource_errors_are_wrapped(
    error_type: type[MemoryError | RecursionError | OverflowError],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(*args: object, **kwargs: object) -> None:
        raise error_type

    monkeypatch.setattr(exact_module, "_node_count", fail)
    result = TransferFunctionReducer().reduce(
        _raw(Add(Symbol("s"), ExactNumber(1)), parameters=frozenset())
    )

    assert result.diagnostics[0].code is (
        DiagnosticCode.TRANSFER_REDUCTION_RESOURCE_LIMIT_EXCEEDED
    )
    assert result.diagnostics[0].technical_details == (
        ("exception", error_type.__name__),
    )


def test_public_reducer_rejects_wrong_python_type() -> None:
    with pytest.raises(TypeError, match="RawTransferFunction"):
        TransferFunctionReducer().reduce(object())  # type: ignore[arg-type]


def test_public_contracts_contain_no_sympy_and_domain_has_no_parsing_dependency() -> None:
    raw = _raw(
        Divide(
            Add(Symbol("s"), ExactNumber(1)),
            Add(Symbol("s"), ExactNumber(1)),
        ),
        parameters=frozenset(),
    )
    result = TransferFunctionReducer().reduce(raw)
    assert result.report is not None
    assert result.reduced is not None

    public_values = (
        result.reduced,
        result.report,
        result.report.steps,
        result.report.steps[0].factor,
        result.diagnostics,
    )
    assert not any(isinstance(value, (sp.Expr, sp.Poly)) for value in public_values)
    source = inspect.getsource(reducer_module) + inspect.getsource(exact_module)
    assert "klausurbotpro.parsing" not in source


def test_reduction_does_not_change_global_sympy_configuration() -> None:
    before = global_parameters.evaluate

    _reduced_pair(
        Divide(
            Add(Symbol("s"), ExactNumber(1)),
            Add(Symbol("s"), ExactNumber(1)),
        ),
        parameters=frozenset(),
    )

    assert global_parameters.evaluate is before
