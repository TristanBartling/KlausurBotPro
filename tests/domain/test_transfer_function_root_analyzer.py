"""Acceptance tests for exact reduced transfer-function root analysis."""

from __future__ import annotations

import sympy as sp

from klausurbotpro.domain import (
    DiagnosticCode,
    ExactExpression,
    ExactRationalValue,
    ExplicitExactRootValue,
    ParameterAssignment,
    ParameterSubstitutions,
    PolynomialFactory,
    PolynomialRootAnalysis,
    PolynomialRootStatus,
    ReducedTransferFunction,
    RootOfValue,
    TransferFunctionDomainExclusion,
    TransferFunctionPrerequisite,
    TransferFunctionPrerequisiteKind,
    TransferFunctionRootAnalyzer,
)


def _reduced(
    numerator: sp.Expr,
    denominator: sp.Expr | None = None,
    *,
    parameters: frozenset[str] = frozenset(),
    prerequisites: tuple[TransferFunctionPrerequisite, ...] = (),
    exclusions: tuple[tuple[sp.Expr, tuple[str, ...]], ...] = (),
) -> ReducedTransferFunction:
    factory = PolynomialFactory()
    numerator_value = factory.create(
        ExactExpression._from_sympy(numerator),
        declared_parameter_names=parameters,
    ).value
    denominator_value = factory.create(
        ExactExpression._from_sympy(
            sp.Integer(1) if denominator is None else denominator
        ),
        declared_parameter_names=parameters,
    ).value
    assert numerator_value is not None
    assert denominator_value is not None
    exclusion_values = []
    for expression, origins in exclusions:
        polynomial = factory.create(
            ExactExpression._from_sympy(expression),
            declared_parameter_names=parameters,
        ).value
        assert polynomial is not None
        exclusion_values.append(TransferFunctionDomainExclusion(polynomial, origins))
    return ReducedTransferFunction._create(
        variable_name="s",
        numerator=numerator_value,
        denominator=denominator_value,
        prerequisites=prerequisites,
        domain_exclusions=tuple(exclusion_values),
    )


def _explicit_texts(
    analysis: PolynomialRootAnalysis | None,
) -> list[tuple[str, int]]:
    assert analysis is not None
    result = []
    for occurrence in analysis.roots:
        assert isinstance(occurrence.value, ExplicitExactRootValue)
        result.append(
            (occurrence.value.expression.canonical_text, occurrence.multiplicity)
        )
    return result


def test_linear_quadratic_multiplicity_and_complex_roots_are_exact() -> None:
    s = sp.Symbol("s")
    analyzer = TransferFunctionRootAnalyzer()

    linear = analyzer.analyze(_reduced(s + 1))
    quadratic = analyzer.analyze(_reduced(s**2 + 3 * s + 2))
    repeated = analyzer.analyze(_reduced((s + 1) ** 2))
    complex_pair = analyzer.analyze(_reduced(s**2 + 1))

    assert _explicit_texts(linear.reduced_zeros) == [("-1", 1)]
    assert set(_explicit_texts(quadratic.reduced_zeros)) == {
        ("-2", 1),
        ("-1", 1),
    }
    assert _explicit_texts(repeated.reduced_zeros) == [("-1", 2)]
    assert set(_explicit_texts(complex_pair.reduced_zeros)) == {
        ("-I", 1),
        ("I", 1),
    }


def test_cubic_rational_roots_and_higher_irreducible_rootof_are_complete() -> None:
    s = sp.Symbol("s")
    analyzer = TransferFunctionRootAnalyzer()

    cubic = analyzer.analyze(_reduced(s**3 - s))
    higher = analyzer.analyze(_reduced(s**5 - s + 1))

    assert set(_explicit_texts(cubic.reduced_zeros)) == {
        ("-1", 1),
        ("0", 1),
        ("1", 1),
    }
    assert higher.reduced_zeros is not None
    assert higher.reduced_zeros.status is PolynomialRootStatus.COMPLETE
    assert len(higher.reduced_zeros.roots) == 5
    assert all(isinstance(item.value, RootOfValue) for item in higher.reduced_zeros.roots)
    assert sum(item.multiplicity for item in higher.reduced_zeros.roots) == 5


def test_zero_and_nonzero_constant_statuses_are_distinct() -> None:
    s = sp.Symbol("s")
    constant = TransferFunctionRootAnalyzer().analyze(_reduced(sp.Integer(7)))
    zero = TransferFunctionRootAnalyzer().analyze(_reduced(sp.Integer(0), s + 1))
    unity = TransferFunctionRootAnalyzer().analyze(_reduced(sp.Integer(1)))

    assert constant.reduced_zeros is not None
    assert constant.reduced_zeros.status is PolynomialRootStatus.CONSTANT_NONZERO
    assert zero.reduced_zeros is not None
    assert zero.reduced_zeros.status is PolynomialRootStatus.ZERO_POLYNOMIAL
    assert zero.reduced_poles is not None
    assert _explicit_texts(zero.reduced_poles) == [("-1", 1)]
    assert unity.reduced_zeros is not None
    assert unity.reduced_poles is not None
    assert unity.reduced_zeros.roots == unity.reduced_poles.roots == ()


def test_zeros_and_poles_remain_separate_for_basic_pairs() -> None:
    s = sp.Symbol("s")
    analyzer = TransferFunctionRootAnalyzer()
    value = analyzer.analyze(_reduced(s + 1, s**2 + 3 * s + 2))
    reciprocal = analyzer.analyze(_reduced(sp.Integer(1), s + 1))
    oscillator = analyzer.analyze(_reduced(s, s**2 + 1))

    assert _explicit_texts(value.reduced_zeros) == [("-1", 1)]
    assert set(_explicit_texts(value.reduced_poles)) == {
        ("-2", 1),
        ("-1", 1),
    }
    assert reciprocal.reduced_zeros is not None
    assert reciprocal.reduced_zeros.roots == ()
    assert _explicit_texts(reciprocal.reduced_poles) == [("-1", 1)]
    assert _explicit_texts(oscillator.reduced_zeros) == [("0", 1)]
    assert set(_explicit_texts(oscillator.reduced_poles)) == {
        ("-I", 1),
        ("I", 1),
    }


def test_full_exact_substitution_and_symbolic_undetermined_behavior() -> None:
    s, T, K = sp.symbols("s T K")
    analyzer = TransferFunctionRootAnalyzer()
    parameterized = _reduced(
        sp.Integer(1),
        T * s + 1,
        parameters=frozenset({"T"}),
    )
    complete = analyzer.analyze(
        parameterized,
        ParameterSubstitutions(
            (ParameterAssignment("T", ExactRationalValue(2)),)
        ),
    )
    symbolic = analyzer.analyze(parameterized)
    zero_pole = analyzer.analyze(
        _reduced(sp.Integer(1), K * s, parameters=frozenset({"K"})),
        ParameterSubstitutions(
            (ParameterAssignment("K", ExactRationalValue(2)),)
        ),
    )

    assert _explicit_texts(complete.reduced_poles) == [("-1/2", 1)]
    assert symbolic.succeeded
    assert symbolic.reduced_poles is not None
    assert symbolic.reduced_poles.status is PolynomialRootStatus.SYMBOLIC_UNDETERMINED
    assert symbolic.diagnostics[0].code is DiagnosticCode.ROOT_ANALYSIS_SYMBOLIC_UNDETERMINED
    assert _explicit_texts(zero_pole.reduced_poles) == [("0", 1)]


def test_degree_drop_and_prerequisite_violations_are_structured() -> None:
    s, K, T = sp.symbols("s K T")
    analyzer = TransferFunctionRootAnalyzer()
    substitution = ParameterSubstitutions(
        (ParameterAssignment("K", ExactRationalValue(0)),)
    )
    dropped = analyzer.analyze(
        _reduced(K * s**2 + s + 1, parameters=frozenset({"K"})),
        substitution,
    )
    prerequisite = TransferFunctionPrerequisite(
        TransferFunctionPrerequisiteKind.EXPRESSION_NONZERO,
        (ExactExpression._from_sympy(K),),
        ("test",),
    )
    violated = analyzer.analyze(
        _reduced(
            K * s + 1,
            parameters=frozenset({"K"}),
            prerequisites=(prerequisite,),
        ),
        substitution,
    )
    not_all = TransferFunctionPrerequisite(
        TransferFunctionPrerequisiteKind.NOT_ALL_ZERO,
        (
            ExactExpression._from_sympy(K - 1),
            ExactExpression._from_sympy(T),
        ),
        ("test",),
    )
    both_zero = analyzer.analyze(
        _reduced(
            s + 1,
            parameters=frozenset({"K", "T"}),
            prerequisites=(not_all,),
        ),
        ParameterSubstitutions(
            (
                ParameterAssignment("K", ExactRationalValue(1)),
                ParameterAssignment("T", ExactRationalValue(0)),
            )
        ),
    )

    assert dropped.reduced_zeros is not None
    assert dropped.reduced_zeros.actual_degree == 1
    assert DiagnosticCode.ROOT_ANALYSIS_DEGREE_DROPPED in {
        item.code for item in dropped.diagnostics
    }
    assert violated.diagnostics[0].code is DiagnosticCode.ROOT_ANALYSIS_PREREQUISITE_VIOLATED
    assert both_zero.diagnostics[0].code is DiagnosticCode.ROOT_ANALYSIS_PREREQUISITE_VIOLATED


def test_missing_and_extra_substitutions_are_errors() -> None:
    s, K = sp.symbols("s K")
    value = _reduced(K * s + 1, parameters=frozenset({"K"}))
    analyzer = TransferFunctionRootAnalyzer()

    missing = analyzer.analyze(value, ParameterSubstitutions())
    extra = analyzer.analyze(
        value,
        ParameterSubstitutions(
            (
                ParameterAssignment("K", ExactRationalValue(1)),
                ParameterAssignment("T", ExactRationalValue(1)),
            )
        ),
    )

    assert missing.diagnostics[0].code is DiagnosticCode.ROOT_ANALYSIS_MISSING_PARAMETERS
    assert extra.diagnostics[0].code is DiagnosticCode.ROOT_ANALYSIS_INVALID_SUBSTITUTION


def test_retained_domain_exclusions_are_analyzed_separately() -> None:
    s, K = sp.symbols("s K")
    analyzer = TransferFunctionRootAnalyzer()
    direct = analyzer.analyze(
        _reduced(
            sp.Integer(1),
            exclusions=((s + 1, ("raw denominator",)),),
        )
    )
    constant = analyzer.analyze(
        _reduced(
            sp.Integer(1),
            parameters=frozenset({"K"}),
            exclusions=(((K - 1) * s + 1, ("conditional",)),),
        ),
        ParameterSubstitutions(
            (ParameterAssignment("K", ExactRationalValue(1)),)
        ),
    )
    empty = analyzer.analyze(
        _reduced(
            sp.Integer(1),
            parameters=frozenset({"K"}),
            exclusions=((K * s, ("empty",)),),
        ),
        ParameterSubstitutions(
            (ParameterAssignment("K", ExactRationalValue(0)),)
        ),
    )

    assert _explicit_texts(direct.retained_domain_exclusions.analyses[0]) == [
        ("-1", 1)
    ]
    assert direct.retained_domain_exclusions.analyses[0].origins == (
        "raw denominator",
    )
    assert constant.retained_domain_exclusions.analyses[0].status is (
        PolynomialRootStatus.CONSTANT_NONZERO
    )
    assert empty.diagnostics[0].code is DiagnosticCode.ROOT_ANALYSIS_DOMAIN_EMPTY


def test_equal_exclusion_locations_are_deduplicated_with_all_origins() -> None:
    s = sp.Symbol("s")
    result = TransferFunctionRootAnalyzer().analyze(
        _reduced(
            sp.Integer(1),
            exclusions=(
                (s + 1, ("first",)),
                (2 * s + 2, ("second",)),
            ),
        )
    )

    assert len(result.retained_domain_exclusions.analyses) == 1
    assert result.retained_domain_exclusions.analyses[0].origins == (
        "first",
        "second",
    )
