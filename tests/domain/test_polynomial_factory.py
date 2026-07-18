"""Functional, validation, and resource tests for PolynomialFactory."""

from __future__ import annotations

import pytest
import sympy as sp
from sympy.core.parameters import global_parameters
from sympy.polys.polyerrors import PolynomialError

import klausurbotpro.domain.polynomial_factory as factory_module
from klausurbotpro.domain import (
    DiagnosticCode,
    ExactExpression,
    PolynomialConditionKind,
    PolynomialCreationResult,
    PolynomialFactory,
    PolynomialLimits,
)


def _exact(expression: sp.Expr) -> ExactExpression:
    return ExactExpression._from_sympy(expression)


def _create(
    expression: sp.Expr,
    *,
    parameters: frozenset[str] = frozenset(),
    limits: PolynomialLimits | None = None,
) -> PolynomialCreationResult:
    return PolynomialFactory(limits or PolynomialLimits()).create(
        _exact(expression),
        declared_parameter_names=parameters,
    )


@pytest.mark.parametrize(
    ("expression", "parameters", "canonical", "coefficients"),
    [
        (sp.Integer(0), frozenset(), "0", ("0",)),
        (sp.Integer(1), frozenset(), "1", ("1",)),
        (sp.Integer(-3), frozenset(), "-3", ("-3",)),
        (sp.Symbol("s"), frozenset(), "s", ("1", "0")),
        (
            sp.Symbol("s") + 1,
            frozenset(),
            "s + 1",
            ("1", "1"),
        ),
        (
            sp.Symbol("s") ** 2 + 3 * sp.Symbol("s") + 2,
            frozenset(),
            "s**2 + 3*s + 2",
            ("1", "3", "2"),
        ),
        (
            sp.Symbol("s") ** 3 + 2,
            frozenset(),
            "s**3 + 2",
            ("1", "0", "0", "2"),
        ),
        (
            -(sp.Symbol("s") ** 2) + 1,
            frozenset(),
            "-s**2 + 1",
            ("-1", "0", "1"),
        ),
        (
            sp.Symbol("K") * sp.Symbol("s") + 1,
            frozenset({"K"}),
            "K*s + 1",
            ("K", "1"),
        ),
        (
            sp.Symbol("T") * sp.Symbol("s") ** 2
            + sp.Symbol("d") * sp.Symbol("s")
            + sp.Symbol("K"),
            frozenset({"T", "d", "K"}),
            "K + T*s**2 + d*s",
            ("T", "d", "K"),
        ),
        (
            sp.Symbol("K") / sp.Symbol("T") * sp.Symbol("s") + 1,
            frozenset({"K", "T"}),
            "K*s/T + 1",
            ("K/T", "1"),
        ),
        (
            (sp.Symbol("s") + 1) * (sp.Symbol("s") + 2),
            frozenset(),
            "s**2 + 3*s + 2",
            ("1", "3", "2"),
        ),
        (
            sp.Add(sp.Symbol("s"), -sp.Symbol("s"), evaluate=False),
            frozenset(),
            "0",
            ("0",),
        ),
        (
            sp.Mul(0, sp.Symbol("s") ** 4, evaluate=False)
            + sp.Symbol("s")
            + 1,
            frozenset(),
            "s + 1",
            ("1", "1"),
        ),
    ],
)
def test_valid_polynomials_are_canonical_and_exact(
    expression: sp.Expr,
    parameters: frozenset[str],
    canonical: str,
    coefficients: tuple[str, ...],
) -> None:
    result = _create(expression, parameters=parameters)

    assert result.succeeded, result.diagnostics
    assert result.value is not None
    assert result.value.expression.canonical_text == canonical
    assert tuple(
        item.canonical_text for item in result.value.coefficients
    ) == coefficients
    assert not result.value.expression._as_sympy().atoms(sp.Float)


def test_used_parameters_exclude_variable_and_unused_declarations() -> None:
    s, K, d = sp.symbols("s K d")
    result = _create(
        K * s + 1,
        parameters=frozenset({"K", "d"}),
    )

    assert result.value is not None
    assert result.value.used_parameter_names == frozenset({"K"})


def test_custom_main_variable_and_field_are_preserved() -> None:
    z, K = sp.symbols("z K")
    success = PolynomialFactory().create(
        _exact(K * z + 1),
        variable_name="z",
        declared_parameter_names=frozenset({"K"}),
        field="polynomial",
    )
    failure = PolynomialFactory().create(
        _exact(z + sp.Symbol("x")),
        variable_name="z",
        field="polynomial",
    )

    assert success.value is not None
    assert success.value.variable_name == "z"
    assert success.value.used_parameter_names == frozenset({"K"})
    assert all(
        diagnostic.field == "polynomial"
        for diagnostic in success.diagnostics
    )
    assert failure.diagnostics[0].field == "polynomial"


@pytest.mark.parametrize(
    ("expression", "parameters", "generic", "guaranteed", "condition"),
    [
        (sp.Symbol("s") ** 2 + 1, frozenset(), 2, 2, None),
        (
            sp.Symbol("K") * sp.Symbol("s") + 1,
            frozenset({"K"}),
            1,
            None,
            "K",
        ),
        (
            sp.Symbol("T") * sp.Symbol("s") ** 2 + sp.Symbol("s") + 1,
            frozenset({"T"}),
            2,
            None,
            "T",
        ),
        (
            (sp.Symbol("K") - 1) * sp.Symbol("s") ** 2 + sp.Symbol("s"),
            frozenset({"K"}),
            2,
            None,
            "K - 1",
        ),
        (
            sp.Symbol("K"),
            frozenset({"K"}),
            0,
            None,
            "K",
        ),
        (sp.Integer(-3), frozenset(), 0, 0, None),
        (
            sp.Mul(0, sp.Symbol("s") ** 4, evaluate=False)
            + sp.Symbol("s")
            + 1,
            frozenset(),
            1,
            1,
            None,
        ),
    ],
)
def test_degree_information_is_conservative(
    expression: sp.Expr,
    parameters: frozenset[str],
    generic: int,
    guaranteed: int | None,
    condition: str | None,
) -> None:
    result = _create(expression, parameters=parameters)
    assert result.value is not None
    info = result.value.degree_info

    assert info.generic_degree == generic
    assert info.guaranteed_degree == guaranteed
    assert (
        tuple(item.expression.canonical_text for item in info.conditions)
        == (() if condition is None else (condition,))
    )
    if condition is None:
        assert all(
            diagnostic.code is not DiagnosticCode.POLYNOMIAL_CONDITIONAL_DEGREE
            for diagnostic in result.diagnostics
        )
    else:
        assert result.diagnostics[-1].code is (
            DiagnosticCode.POLYNOMIAL_CONDITIONAL_DEGREE
        )


def test_definition_and_degree_conditions_are_separate_and_reduced() -> None:
    s, K, T = sp.symbols("s K T")
    result = _create(
        (K / T) * s + 1,
        parameters=frozenset({"K", "T"}),
    )
    assert result.value is not None

    assert tuple(
        (condition.kind, condition.expression.canonical_text)
        for condition in result.value.conditions
    ) == (
        (PolynomialConditionKind.DEFINITION_NONZERO, "T"),
        (PolynomialConditionKind.LEADING_COEFFICIENT_NONZERO, "K"),
    )
    assert tuple(diagnostic.code for diagnostic in result.diagnostics) == (
        DiagnosticCode.POLYNOMIAL_PARAMETER_DENOMINATOR_NONZERO,
        DiagnosticCode.POLYNOMIAL_CONDITIONAL_DEGREE,
    )


def test_numeric_rational_denominator_needs_no_definition_condition() -> None:
    s, K, T = sp.symbols("s K T")
    rational = _create(sp.Rational(1, 2) * s + sp.Rational(3, 4))
    scaled = _create(
        (2 * K) / (2 * T) * s + 1,
        parameters=frozenset({"K", "T"}),
    )

    assert rational.succeeded
    assert rational.diagnostics == ()
    assert scaled.value is not None
    assert tuple(
        condition.expression.canonical_text
        for condition in scaled.value.conditions
    ) == ("T", "K")


def test_composite_fraction_conditions_use_denominator_and_numerator() -> None:
    s, K, T = sp.symbols("s K T")
    result = _create(
        ((K - 1) / (T + 1)) * s**2 + 1,
        parameters=frozenset({"K", "T"}),
    )
    assert result.value is not None

    assert tuple(
        (condition.kind, condition.expression.canonical_text)
        for condition in result.value.conditions
    ) == (
        (PolynomialConditionKind.DEFINITION_NONZERO, "T + 1"),
        (
            PolynomialConditionKind.LEADING_COEFFICIENT_NONZERO,
            "K - 1",
        ),
    )


def test_conditions_are_deduplicated_and_deterministically_sorted() -> None:
    s, K, T = sp.symbols("s K T")
    expression = s**2 / T + s / T + 1 / K

    first = _create(expression, parameters=frozenset({"K", "T"}))
    second = _create(expression, parameters=frozenset({"T", "K"}))
    assert first == second
    assert first.value is not None

    assert tuple(
        (condition.kind.value, condition.expression.canonical_text)
        for condition in first.value.conditions
    ) == (
        ("definition_nonzero", "K"),
        ("definition_nonzero", "T"),
    )


@pytest.mark.parametrize(
    ("expression", "parameters", "expected_code"),
    [
        (
            sp.Symbol("s") ** -1,
            frozenset(),
            DiagnosticCode.POLYNOMIAL_NEGATIVE_EXPONENT,
        ),
        (
            sp.Symbol("K") / (sp.Symbol("s") + 1),
            frozenset({"K"}),
            DiagnosticCode.POLYNOMIAL_VARIABLE_IN_DENOMINATOR,
        ),
        (
            sp.Pow(
                sp.Symbol("s"),
                sp.Symbol("K"),
                evaluate=False,
            ),
            frozenset({"K"}),
            DiagnosticCode.POLYNOMIAL_SYMBOLIC_EXPONENT,
        ),
        (
            sp.Pow(
                sp.Symbol("s"),
                sp.Rational(1, 2),
                evaluate=False,
            ),
            frozenset(),
            DiagnosticCode.POLYNOMIAL_NONINTEGER_EXPONENT,
        ),
        (
            sp.sin(sp.Symbol("s")),
            frozenset(),
            DiagnosticCode.POLYNOMIAL_NOT_POLYNOMIAL,
        ),
        (
            sp.exp(sp.Symbol("s")),
            frozenset(),
            DiagnosticCode.POLYNOMIAL_NOT_POLYNOMIAL,
        ),
        (
            sp.log(sp.Symbol("s")),
            frozenset(),
            DiagnosticCode.POLYNOMIAL_NOT_POLYNOMIAL,
        ),
        (
            sp.sin(sp.Symbol("K")) * sp.Symbol("s"),
            frozenset({"K"}),
            DiagnosticCode.POLYNOMIAL_NOT_POLYNOMIAL,
        ),
        (
            sp.sqrt(2) * sp.Symbol("s"),
            frozenset(),
            DiagnosticCode.POLYNOMIAL_NOT_POLYNOMIAL,
        ),
        (
            sp.Symbol("x") + sp.Symbol("s"),
            frozenset(),
            DiagnosticCode.POLYNOMIAL_UNDECLARED_SYMBOL,
        ),
    ],
)
def test_invalid_domain_expressions_have_specific_diagnostics(
    expression: sp.Expr,
    parameters: frozenset[str],
    expected_code: DiagnosticCode,
) -> None:
    result = _create(expression, parameters=parameters)

    assert not result.succeeded
    assert result.diagnostics[0].code is expected_code


@pytest.mark.parametrize(
    "variable_name",
    ["class", "__s__", "s.x", "x-y", ""],
)
def test_invalid_variable_names_are_diagnostics(variable_name: str) -> None:
    result = PolynomialFactory().create(
        _exact(sp.Integer(1)),
        variable_name=variable_name,
    )

    assert result.diagnostics[0].code is (
        DiagnosticCode.POLYNOMIAL_INVALID_VARIABLE
    )


def test_invalid_parameter_name_and_variable_conflict_are_diagnostics() -> None:
    factory = PolynomialFactory()

    invalid = factory.create(
        _exact(sp.Integer(1)),
        declared_parameter_names=frozenset({"class"}),
    )
    conflict = factory.create(
        _exact(sp.Symbol("s")),
        declared_parameter_names=frozenset({"s"}),
    )

    assert invalid.diagnostics[0].code is (
        DiagnosticCode.POLYNOMIAL_INVALID_VARIABLE
    )
    assert conflict.diagnostics[0].code is (
        DiagnosticCode.POLYNOMIAL_VARIABLE_CONFLICT
    )


def test_wrong_python_inputs_raise_type_error() -> None:
    factory = PolynomialFactory()

    with pytest.raises(TypeError, match="ExactExpression"):
        factory.create("s + 1")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="ExactExpression"):
        factory.create(sp.Matrix([[1]]))
    with pytest.raises(TypeError, match="ExactExpression"):
        factory.create(sp.Symbol("s") < 1)


def test_forged_internal_float_is_rejected_defensively() -> None:
    forged = object.__new__(ExactExpression)
    object.__setattr__(forged, "_expression", sp.Float(0.5) * sp.Symbol("s"))

    result = PolynomialFactory().create(forged)

    assert result.diagnostics[0].code is (
        DiagnosticCode.POLYNOMIAL_FLOAT_NOT_ALLOWED
    )


def test_hidden_symbol_assumptions_are_rejected() -> None:
    symbol = sp.Symbol("K", positive=True)
    result = _create(symbol, parameters=frozenset({"K"}))

    assert result.diagnostics[0].code is (
        DiagnosticCode.POLYNOMIAL_SYMBOL_ASSUMPTION_NOT_ALLOWED
    )


def test_noncanonical_dummy_symbol_is_rejected() -> None:
    symbol = sp.Dummy("K")
    result = _create(symbol, parameters=frozenset({"K"}))

    assert result.diagnostics[0].code is (
        DiagnosticCode.POLYNOMIAL_SYMBOL_ASSUMPTION_NOT_ALLOWED
    )


def test_distinct_symbols_with_same_name_are_rejected() -> None:
    plain = sp.Symbol("K")
    assumed = sp.Symbol("K", positive=True)
    expression = sp.Add(plain, assumed, evaluate=False)
    result = _create(expression, parameters=frozenset({"K"}))

    assert result.diagnostics[0].code is (
        DiagnosticCode.POLYNOMIAL_SYMBOL_ASSUMPTION_NOT_ALLOWED
    )


def test_declared_parameter_limit_is_checked_before_domain_creation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    domain_calls = 0

    def count_domain_calls(*args: object, **kwargs: object) -> object:
        nonlocal domain_calls
        domain_calls += 1
        return object()

    monkeypatch.setattr(sp.QQ, "frac_field", count_domain_calls)
    result = PolynomialFactory(
        PolynomialLimits(max_parameters=1)
    ).create(
        _exact(sp.Integer(1)),
        declared_parameter_names=frozenset({"K", "T"}),
    )

    assert result.diagnostics[0].code is (
        DiagnosticCode.POLYNOMIAL_PARAMETER_LIMIT_EXCEEDED
    )
    assert domain_calls == 0


@pytest.mark.parametrize(
    ("expression", "limits", "expected_code"),
    [
        (
            sp.Symbol("s") ** 3,
            PolynomialLimits(max_degree=2),
            DiagnosticCode.POLYNOMIAL_DEGREE_LIMIT_EXCEEDED,
        ),
        (
            sp.Symbol("s") ** 2 + 1,
            PolynomialLimits(max_coefficients=2),
            DiagnosticCode.POLYNOMIAL_COEFFICIENT_LIMIT_EXCEEDED,
        ),
        (
            sp.Symbol("s") ** 2 + sp.Symbol("s") + 1,
            PolynomialLimits(max_structural_terms=2),
            DiagnosticCode.POLYNOMIAL_TERM_LIMIT_EXCEEDED,
        ),
        (
            (sp.Symbol("K") + sp.Symbol("T") + 1) * sp.Symbol("s"),
            PolynomialLimits(max_coefficient_operations=1),
            DiagnosticCode.POLYNOMIAL_COMPLEXITY_LIMIT_EXCEEDED,
        ),
        (
            sp.Symbol("s") + 1,
            PolynomialLimits(max_expression_nodes=2),
            DiagnosticCode.POLYNOMIAL_COMPLEXITY_LIMIT_EXCEEDED,
        ),
    ],
)
def test_domain_limits_have_specific_diagnostics(
    expression: sp.Expr,
    limits: PolynomialLimits,
    expected_code: DiagnosticCode,
) -> None:
    parameters = frozenset(
        symbol.name
        for symbol in expression.free_symbols
        if symbol.name != "s"
    )
    result = _create(expression, parameters=parameters, limits=limits)

    assert result.diagnostics[0].code is expected_code


def test_univariate_power_is_not_rejected_by_exponential_term_estimate() -> None:
    s = sp.Symbol("s")
    result = _create((s + 1) ** 32)

    assert result.succeeded
    assert result.value is not None
    assert len(result.value.coefficients) == 33
    assert result.value.degree_info.generic_degree == 32


@pytest.mark.parametrize(
    "error_type",
    [MemoryError, RecursionError, OverflowError],
)
def test_resource_errors_are_structured_and_deterministic(
    error_type: type[MemoryError | RecursionError | OverflowError],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def raise_resource_error(*args: object, **kwargs: object) -> None:
        raise error_type

    monkeypatch.setattr(factory_module, "_node_count", raise_resource_error)
    factory = PolynomialFactory()
    expression = _exact(sp.Symbol("s") + 1)

    first = factory.create(expression)
    second = factory.create(expression)

    assert first == second
    assert first.diagnostics[0].code is (
        DiagnosticCode.POLYNOMIAL_RESOURCE_LIMIT_EXCEEDED
    )
    assert first.diagnostics[0].technical_details == (
        ("exception", error_type.__name__),
    )


def test_sympy_polynomial_error_is_not_exposed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def raise_polynomial_error(*args: object, **kwargs: object) -> None:
        raise PolynomialError("controlled")

    monkeypatch.setattr(sp, "Poly", raise_polynomial_error)

    result = PolynomialFactory().create(_exact(sp.Symbol("s") + 1))

    assert result.diagnostics[0].code is (
        DiagnosticCode.POLYNOMIAL_NOT_POLYNOMIAL
    )
    assert result.diagnostics[0].technical_details == (
        ("exception", "PolynomialError"),
    )


def test_unexpected_programming_errors_are_not_hidden(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def raise_runtime_error(*args: object, **kwargs: object) -> None:
        raise RuntimeError("programming defect")

    monkeypatch.setattr(factory_module, "_node_count", raise_runtime_error)

    with pytest.raises(RuntimeError, match="programming defect"):
        PolynomialFactory().create(_exact(sp.Symbol("s") + 1))


def test_global_sympy_configuration_is_not_changed() -> None:
    before = global_parameters.evaluate

    _create(
        sp.Symbol("K") / sp.Symbol("T") * sp.Symbol("s") + 1,
        parameters=frozenset({"K", "T"}),
    )

    assert global_parameters.evaluate is before
