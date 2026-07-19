"""Acceptance tests for exact transfer-function stability classification."""

from __future__ import annotations

import inspect
from dataclasses import replace

import pytest
import sympy as sp

import klausurbotpro.domain.transfer_function_stability_analyzer as stability_module
from klausurbotpro.domain.diagnostics import Diagnostic, DiagnosticCode, DiagnosticSeverity
from klausurbotpro.domain.expression import ExactExpression
from klausurbotpro.domain.parameter_substitutions import (
    ExactRationalValue,
    ParameterAssignment,
    ParameterSubstitutions,
)
from klausurbotpro.domain.polynomial_contracts import PolynomialLimits
from klausurbotpro.domain.polynomial_factory import PolynomialFactory
from klausurbotpro.domain.raw_transfer_function_contracts import (
    TransferFunctionDomainExclusion,
)
from klausurbotpro.domain.reduced_transfer_function import (
    ReducedTransferFunction,
)
from klausurbotpro.domain.root_analysis_contracts import (
    ExplicitExactRootValue,
    PolynomialRootAnalysis,
    PolynomialRootStatus,
    RootAnalysisGroup,
    RootAnalysisLimits,
    RootOccurrence,
    RootOfValue,
    RootSource,
    TransferFunctionRootAnalysisResult,
)
from klausurbotpro.domain.stability_analysis_contracts import (
    PoleStabilityContributionKind,
    RealPartSign,
    StabilityAnalysisLimits,
    StabilityStatus,
)
from klausurbotpro.domain.transfer_function_root_analyzer import (
    TransferFunctionRootAnalyzer,
)
from klausurbotpro.domain.transfer_function_stability_analyzer import (
    TransferFunctionStabilityAnalyzer,
)


def _reduced(
    denominator: sp.Expr,
    *,
    numerator: sp.Expr | None = None,
    parameters: frozenset[str] = frozenset(),
    exclusions: tuple[sp.Expr, ...] = (),
    maximum_degree: int = 32,
) -> ReducedTransferFunction:
    factory = PolynomialFactory(
        PolynomialLimits(
            max_degree=maximum_degree,
            max_coefficients=maximum_degree + 1,
            max_structural_terms=maximum_degree + 1,
        )
    )
    numerator_value = factory.create(
        ExactExpression._from_sympy(
            sp.Integer(1) if numerator is None else numerator
        ),
        declared_parameter_names=parameters,
    ).value
    denominator_value = factory.create(
        ExactExpression._from_sympy(denominator),
        declared_parameter_names=parameters,
    ).value
    assert numerator_value is not None
    assert denominator_value is not None
    domain_exclusions = []
    for expression in exclusions:
        polynomial = factory.create(
            ExactExpression._from_sympy(expression),
            declared_parameter_names=parameters,
        ).value
        assert polynomial is not None
        domain_exclusions.append(
            TransferFunctionDomainExclusion(polynomial, ("test",))
        )
    return ReducedTransferFunction._create(
        variable_name="s",
        numerator=numerator_value,
        denominator=denominator_value,
        prerequisites=(),
        domain_exclusions=tuple(domain_exclusions),
    )


def _root_analysis(
    denominator: sp.Expr,
    *,
    numerator: sp.Expr | None = None,
    parameters: frozenset[str] = frozenset(),
    substitutions: ParameterSubstitutions | None = None,
    exclusions: tuple[sp.Expr, ...] = (),
    root_limits: RootAnalysisLimits | None = None,
    maximum_degree: int = 32,
) -> TransferFunctionRootAnalysisResult:
    analyzer = (
        TransferFunctionRootAnalyzer()
        if root_limits is None
        else TransferFunctionRootAnalyzer(root_limits)
    )
    return analyzer.analyze(
        _reduced(
            denominator,
            numerator=numerator,
            parameters=parameters,
            exclusions=exclusions,
            maximum_degree=maximum_degree,
        ),
        substitutions,
    )


def _cancelled_group(*values: sp.Expr) -> RootAnalysisGroup:
    roots = tuple(
        RootOccurrence(
            ExplicitExactRootValue(ExactExpression._from_sympy(value)),
            1,
            RootSource.CANCELLED_FACTOR,
            index,
        )
        for index, value in enumerate(values)
    )
    analysis = PolynomialRootAnalysis(
        PolynomialRootStatus.COMPLETE,
        RootSource.CANCELLED_FACTOR,
        ExactExpression._from_sympy(
            sp.prod(sp.Symbol("s") - value for value in values)
        ),
        roots,
        original_degree=len(roots),
        actual_degree=len(roots),
    )
    return RootAnalysisGroup(PolynomialRootStatus.COMPLETE, (analysis,))


def _rootof_denominator_analysis(
    defining_coefficients: tuple[int, ...],
) -> TransferFunctionRootAnalysisResult:
    s = sp.Symbol("s")
    denominator_expression = sp.Poly.from_list(
        defining_coefficients,
        gens=s,
    ).as_expr()
    reduced = _reduced(denominator_expression)
    degree = len(defining_coefficients) - 1
    poles = PolynomialRootAnalysis(
        PolynomialRootStatus.COMPLETE,
        RootSource.DENOMINATOR,
        reduced.denominator.expression,
        tuple(
            RootOccurrence(
                RootOfValue(defining_coefficients, index),
                1,
                RootSource.DENOMINATOR,
                index,
            )
            for index in range(degree)
        ),
        original_degree=degree,
        actual_degree=degree,
    )
    zeros = PolynomialRootAnalysis(
        PolynomialRootStatus.CONSTANT_NONZERO,
        RootSource.NUMERATOR,
        reduced.numerator.expression,
        original_degree=0,
        actual_degree=0,
    )
    return TransferFunctionRootAnalysisResult(
        reduced,
        ParameterSubstitutions(),
        zeros,
        poles,
        RootAnalysisGroup(PolynomialRootStatus.COMPLETE),
        RootAnalysisGroup(PolynomialRootStatus.NOT_EVALUATED),
    )


@pytest.mark.parametrize(
    ("denominator", "status", "is_ea_stable"),
    [
        ((sp.Symbol("s") + 1) * (sp.Symbol("s") + 2), StabilityStatus.STABLE, True),
        (
            (sp.Symbol("s") + 1) ** 2 + 4,
            StabilityStatus.STABLE,
            True,
        ),
        (
            (sp.Symbol("s") + 1) * (sp.Symbol("s") - 1),
            StabilityStatus.UNSTABLE,
            False,
        ),
        (sp.Symbol("s"), StabilityStatus.BORDERLINE_STABLE, False),
        (sp.Symbol("s") ** 2 + 1, StabilityStatus.BORDERLINE_STABLE, False),
        (sp.Symbol("s") ** 2, StabilityStatus.UNSTABLE, False),
        ((sp.Symbol("s") ** 2 + 1) ** 2, StabilityStatus.UNSTABLE, False),
        (sp.Integer(1), StabilityStatus.STABLE, True),
        (
            sp.Symbol("s") ** 2 + 4 * sp.Symbol("s") + 2,
            StabilityStatus.STABLE,
            True,
        ),
        (
            sp.Symbol("s") ** 2 - 4 * sp.Symbol("s") + 2,
            StabilityStatus.UNSTABLE,
            False,
        ),
    ],
)
def test_status_acceptance_matrix(
    denominator: sp.Expr,
    status: StabilityStatus,
    is_ea_stable: bool,
) -> None:
    result = TransferFunctionStabilityAnalyzer().analyze(
        _root_analysis(denominator)
    )

    assert result.status is status
    assert result.is_ea_stable is is_ea_stable


def test_zeros_never_determine_stability() -> None:
    s = sp.Symbol("s")
    result = TransferFunctionStabilityAnalyzer().analyze(
        _root_analysis(s + 1, numerator=s - 100)
    )
    assert result.status is StabilityStatus.STABLE
    assert all(
        item.pole.source is RootSource.DENOMINATOR
        for item in result.pole_contributions
    )


def test_symbolic_phase_2a_poles_produce_successful_undetermined_result() -> None:
    s, T = sp.symbols("s T")
    result = TransferFunctionStabilityAnalyzer().analyze(
        _root_analysis(T * s + 1, parameters=frozenset({"T"}))
    )

    assert result.succeeded
    assert result.status is StabilityStatus.SYMBOLIC_UNDETERMINED
    assert result.is_ea_stable is None
    assert result.pole_contributions == ()
    assert result.diagnostics[0].code is (
        DiagnosticCode.STABILITY_ANALYSIS_SYMBOLIC_UNDETERMINED
    )


def test_parameter_substitutions_are_retained_as_root_analysis_context() -> None:
    s, T = sp.symbols("s T")
    substitutions = ParameterSubstitutions(
        (ParameterAssignment("T", ExactRationalValue(2)),)
    )
    root_analysis = _root_analysis(
        T * s + 1,
        parameters=frozenset({"T"}),
        substitutions=substitutions,
    )
    result = TransferFunctionStabilityAnalyzer().analyze(root_analysis)

    assert result.root_analysis is root_analysis
    assert result.root_analysis.substitutions == substitutions
    assert result.status is StabilityStatus.STABLE


def test_secure_instability_has_priority_over_an_undetermined_pole(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = stability_module.classify_exact_real_part  # type: ignore[attr-defined]
    def classify(
        value: ExplicitExactRootValue | RootOfValue,
        limits: StabilityAnalysisLimits,
    ) -> object:
        result = original(value, limits)
        if (
            isinstance(value, ExplicitExactRootValue)
            and value.expression.canonical_text == "-1"
        ):
            return replace(result, sign=RealPartSign.UNDETERMINED)
        return result

    monkeypatch.setattr(stability_module, "classify_exact_real_part", classify)
    s = sp.Symbol("s")
    result = TransferFunctionStabilityAnalyzer().analyze(
        _root_analysis((s + 1) * (s - 1))
    )

    assert result.status is StabilityStatus.UNSTABLE


def test_only_undetermined_pole_produces_symbolic_undetermined(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = stability_module.classify_exact_real_part  # type: ignore[attr-defined]

    def classify(
        value: ExplicitExactRootValue | RootOfValue,
        limits: StabilityAnalysisLimits,
    ) -> object:
        return replace(
            original(value, limits),
            sign=RealPartSign.UNDETERMINED,
        )

    monkeypatch.setattr(stability_module, "classify_exact_real_part", classify)
    result = TransferFunctionStabilityAnalyzer().analyze(
        _root_analysis(sp.Symbol("s") + 1)
    )

    assert result.status is StabilityStatus.SYMBOLIC_UNDETERMINED
    assert result.is_ea_stable is None


def test_repeated_imaginary_pole_has_structured_unstable_reason() -> None:
    result = TransferFunctionStabilityAnalyzer().analyze(
        _root_analysis(sp.Symbol("s") ** 2)
    )
    contribution = result.pole_contributions[0]

    assert contribution.contribution is (
        PoleStabilityContributionKind.CAUSES_UNSTABLE
    )
    assert "polynomialen Faktor in t" in contribution.reason.message
    assert "I-Stabil" not in contribution.reason.message


def test_domain_exclusion_on_right_does_not_change_status() -> None:
    s = sp.Symbol("s")
    root_analysis = _root_analysis(s + 1, exclusions=(s - 1,))
    result = TransferFunctionStabilityAnalyzer().analyze(root_analysis)

    assert result.status is StabilityStatus.STABLE
    assert result.retained_domain_exclusions is (
        root_analysis.retained_domain_exclusions
    )
    assert all(
        item.code is not DiagnosticCode.STABILITY_ANALYSIS_CANCELLED_LOCATION_NONNEGATIVE
        for item in result.diagnostics
    )


@pytest.mark.parametrize("location", [sp.Integer(1), sp.Integer(0)])
def test_nonnegative_cancelled_location_warns_without_changing_status(
    location: sp.Expr,
) -> None:
    root_analysis = _root_analysis(sp.Symbol("s") + 1)
    object.__setattr__(
        root_analysis,
        "cancelled_locations",
        _cancelled_group(location),
    )
    result = TransferFunctionStabilityAnalyzer().analyze(root_analysis)

    assert result.status is StabilityStatus.STABLE
    assert len(result.cancelled_location_notices) == 1
    assert result.cancelled_location_notices[0].possible_hidden_internal_dynamics
    assert DiagnosticCode.STABILITY_ANALYSIS_CANCELLED_LOCATION_NONNEGATIVE in {
        item.code for item in result.diagnostics
    }


def test_not_evaluated_cancelled_locations_produce_information() -> None:
    result = TransferFunctionStabilityAnalyzer().analyze(
        _root_analysis(sp.Symbol("s") + 1)
    )
    assert DiagnosticCode.STABILITY_ANALYSIS_CANCELLED_LOCATIONS_NOT_EVALUATED in {
        item.code for item in result.diagnostics
    }


def test_symbolically_undetermined_cancelled_locations_only_warn() -> None:
    root_analysis = _root_analysis(sp.Symbol("s") + 1)
    symbolic = PolynomialRootAnalysis(
        PolynomialRootStatus.SYMBOLIC_UNDETERMINED,
        RootSource.CANCELLED_FACTOR,
        ExactExpression._from_sympy(sp.Symbol("K") * sp.Symbol("s") + 1),
    )
    object.__setattr__(
        root_analysis,
        "cancelled_locations",
        RootAnalysisGroup(
            PolynomialRootStatus.SYMBOLIC_UNDETERMINED,
            (symbolic,),
        ),
    )

    result = TransferFunctionStabilityAnalyzer().analyze(root_analysis)

    assert result.status is StabilityStatus.STABLE
    assert DiagnosticCode.STABILITY_ANALYSIS_CANCELLED_LOCATION_UNDETERMINED in {
        item.code for item in result.diagnostics
    }


def test_numeric_estimate_never_decides_and_can_only_warn() -> None:
    root_analysis = _root_analysis(sp.Symbol("s") + 1)
    assert root_analysis.reduced_poles is not None
    estimate = root_analysis.reduced_poles.numerical_estimates[0]
    object.__setattr__(estimate, "real", "1")

    result = TransferFunctionStabilityAnalyzer().analyze(root_analysis)

    assert result.status is StabilityStatus.STABLE
    assert DiagnosticCode.STABILITY_ANALYSIS_NUMERIC_CONTRADICTION in {
        item.code for item in result.diagnostics
    }


def test_exact_zero_ignores_small_numeric_remainder() -> None:
    root_analysis = _root_analysis(sp.Symbol("s"))
    assert root_analysis.reduced_poles is not None
    estimate = root_analysis.reduced_poles.numerical_estimates[0]
    object.__setattr__(estimate, "real", "-1E-30")

    result = TransferFunctionStabilityAnalyzer().analyze(root_analysis)

    assert result.status is StabilityStatus.BORDERLINE_STABLE
    assert DiagnosticCode.STABILITY_ANALYSIS_NUMERIC_CONTRADICTION not in {
        item.code for item in result.diagnostics
    }


def test_sources_match_the_official_locations_exactly() -> None:
    result = TransferFunctionStabilityAnalyzer().analyze(
        _root_analysis(sp.Symbol("s") + 1)
    )
    references = {
        (item.document_name, item.page, item.location)
        for item in result.source_references
    }
    assert references == {
        ("skript.pdf", 107, "Theorem 5.12"),
        ("skript.pdf", 102, "Korollar 5.5"),
        (
            "Regelungstechnik_Tutorium_komplett.pdf",
            None,
            "Tutorium 09 – Stabilität I, Aufgabe 2",
        ),
    }


def test_manipulated_and_failed_root_analysis_are_structured() -> None:
    manipulated = _root_analysis(sp.Symbol("s") + 1)
    assert manipulated.reduced_poles is not None
    object.__setattr__(
        manipulated.reduced_poles.roots[0],
        "source",
        RootSource.NUMERATOR,
    )
    failed = TransferFunctionRootAnalysisResult(
        None,
        None,
        None,
        None,
        RootAnalysisGroup(PolynomialRootStatus.NOT_EVALUATED),
        RootAnalysisGroup(PolynomialRootStatus.NOT_EVALUATED),
        (
            Diagnostic(
                DiagnosticSeverity.ERROR,
                DiagnosticCode.ROOT_ANALYSIS_INVALID_TRANSFER_FUNCTION,
                "failed",
            ),
        ),
    )

    for value in (manipulated, failed):
        result = TransferFunctionStabilityAnalyzer().analyze(value)
        assert not result.succeeded
        assert result.diagnostics[0].code is (
            DiagnosticCode.STABILITY_ANALYSIS_INVALID_ROOT_ANALYSIS
        )


def test_false_reported_pole_is_rejected_mathematically() -> None:
    root_analysis = _root_analysis(sp.Symbol("s") + 1)
    assert root_analysis.reduced_poles is not None
    occurrence = root_analysis.reduced_poles.roots[0]
    object.__setattr__(
        occurrence,
        "value",
        ExplicitExactRootValue(ExactExpression._from_sympy(sp.Integer(1))),
    )

    result = TransferFunctionStabilityAnalyzer().analyze(root_analysis)

    assert result.diagnostics[0].code is (
        DiagnosticCode.STABILITY_ANALYSIS_INVALID_ROOT_ANALYSIS
    )


def test_false_pole_source_expression_is_rejected_mathematically() -> None:
    s = sp.Symbol("s")
    root_analysis = _root_analysis(s + 1)
    assert root_analysis.reduced_poles is not None
    object.__setattr__(
        root_analysis.reduced_poles,
        "source_expression",
        ExactExpression._from_sympy(s - 1),
    )

    result = TransferFunctionStabilityAnalyzer().analyze(root_analysis)

    assert result.diagnostics[0].code is (
        DiagnosticCode.STABILITY_ANALYSIS_INVALID_ROOT_ANALYSIS
    )


def test_duplicate_reported_roots_are_rejected_mathematically() -> None:
    s = sp.Symbol("s")
    root_analysis = _root_analysis((s + 1) * (s + 2))
    assert root_analysis.reduced_poles is not None
    first, second = root_analysis.reduced_poles.roots
    object.__setattr__(second, "value", first.value)

    result = TransferFunctionStabilityAnalyzer().analyze(root_analysis)

    assert result.diagnostics[0].code is (
        DiagnosticCode.STABILITY_ANALYSIS_INVALID_ROOT_ANALYSIS
    )


def test_false_reported_multiplicity_is_rejected_mathematically() -> None:
    s = sp.Symbol("s")
    root_analysis = _root_analysis((s + 1) * (s + 2))
    assert root_analysis.reduced_poles is not None
    first = root_analysis.reduced_poles.roots[0]
    forged = RootOccurrence(
        first.value,
        2,
        RootSource.DENOMINATOR,
        0,
    )
    object.__setattr__(root_analysis.reduced_poles, "roots", (forged,))
    object.__setattr__(
        root_analysis.reduced_poles,
        "numerical_estimates",
        (),
    )

    result = TransferFunctionStabilityAnalyzer().analyze(root_analysis)

    assert result.diagnostics[0].code is (
        DiagnosticCode.STABILITY_ANALYSIS_INVALID_ROOT_ANALYSIS
    )


def test_unrelated_rootof_is_rejected_mathematically() -> None:
    root_analysis = _root_analysis(sp.Symbol("s") + 1)
    assert root_analysis.reduced_poles is not None
    occurrence = root_analysis.reduced_poles.roots[0]
    object.__setattr__(
        occurrence,
        "value",
        RootOfValue((1, 0, 0, 0, -1, 1), 0),
    )

    result = TransferFunctionStabilityAnalyzer().analyze(root_analysis)

    assert result.diagnostics[0].code is (
        DiagnosticCode.STABILITY_ANALYSIS_INVALID_ROOT_ANALYSIS
    )


def test_correct_explicit_and_rootof_poles_pass_independent_validation() -> None:
    s = sp.Symbol("s")
    mixed = _root_analysis(s**2 - 2)
    assert mixed.reduced_poles is not None
    positive = mixed.reduced_poles.roots[1]
    object.__setattr__(
        positive,
        "value",
        RootOfValue((1, 0, -2), 1),
    )
    rootof = _rootof_denominator_analysis((1, 0, 0, -2))

    mixed_result = TransferFunctionStabilityAnalyzer().analyze(mixed)
    rootof_result = TransferFunctionStabilityAnalyzer().analyze(rootof)

    assert mixed_result.succeeded
    assert rootof_result.succeeded


def test_cross_representation_duplicate_root_is_rejected() -> None:
    s = sp.Symbol("s")
    root_analysis = _root_analysis(s**2 - 2)
    assert root_analysis.reduced_poles is not None
    second = root_analysis.reduced_poles.roots[1]
    object.__setattr__(
        second,
        "value",
        RootOfValue((1, 0, -2), 0),
    )

    result = TransferFunctionStabilityAnalyzer().analyze(root_analysis)

    assert result.diagnostics[0].code is (
        DiagnosticCode.STABILITY_ANALYSIS_INVALID_ROOT_ANALYSIS
    )


def test_custom_phase_2a_degree_limit_is_accepted_within_stability_limit() -> None:
    s = sp.Symbol("s")
    root_analysis = _root_analysis(
        s**33,
        root_limits=RootAnalysisLimits(max_polynomial_degree=33),
        maximum_degree=33,
    )

    result = TransferFunctionStabilityAnalyzer(
        StabilityAnalysisLimits(max_source_polynomial_degree=33)
    ).analyze(root_analysis)

    assert result.succeeded
    assert result.status is StabilityStatus.UNSTABLE


def test_source_degree_limit_precedes_exact_pole_validation() -> None:
    s = sp.Symbol("s")
    root_analysis = _root_analysis(
        s**33,
        root_limits=RootAnalysisLimits(max_polynomial_degree=33),
        maximum_degree=33,
    )

    result = TransferFunctionStabilityAnalyzer(
        StabilityAnalysisLimits(max_source_polynomial_degree=32)
    ).analyze(root_analysis)

    assert result.diagnostics[0].code is (
        DiagnosticCode.STABILITY_ANALYSIS_LIMIT_EXCEEDED
    )


def test_large_substitution_is_limited_before_sympy_reconstruction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    s, K = sp.symbols("s K")
    large_value = 10**300
    substitutions = ParameterSubstitutions(
        (ParameterAssignment("K", ExactRationalValue(large_value)),)
    )
    root_analysis = _root_analysis(
        K * s + 1,
        parameters=frozenset({"K"}),
        substitutions=substitutions,
        root_limits=RootAnalysisLimits(
            max_substitution_integer_digits=301
        ),
    )
    original_rational = sp.Rational

    def guarded_rational(
        numerator: object,
        denominator: object = 1,
    ) -> sp.Expr:
        if numerator == large_value:
            raise AssertionError("Oversized value reached SymPy.")
        return original_rational(numerator, denominator)

    monkeypatch.setattr(
        "klausurbotpro.domain._root_analysis_validation.sp.Rational",
        guarded_rational,
    )
    result = TransferFunctionStabilityAnalyzer(
        StabilityAnalysisLimits(max_substitution_integer_digits=256)
    ).analyze(root_analysis)

    assert result.diagnostics[0].code is (
        DiagnosticCode.STABILITY_ANALYSIS_LIMIT_EXCEEDED
    )


def test_large_valid_substitution_uses_stability_limit_not_phase_2a_default() -> None:
    s, K = sp.symbols("s K")
    substitutions = ParameterSubstitutions(
        (ParameterAssignment("K", ExactRationalValue(10**300)),)
    )
    root_analysis = _root_analysis(
        K * s + 1,
        parameters=frozenset({"K"}),
        substitutions=substitutions,
        root_limits=RootAnalysisLimits(
            max_substitution_integer_digits=301
        ),
    )

    result = TransferFunctionStabilityAnalyzer(
        StabilityAnalysisLimits(max_substitution_integer_digits=301)
    ).analyze(root_analysis)

    assert result.succeeded
    assert result.status is StabilityStatus.STABLE


def test_wrong_root_analysis_type_is_a_structured_error() -> None:
    result = TransferFunctionStabilityAnalyzer().analyze(object())  # type: ignore[arg-type]
    assert result.diagnostics[0].code is (
        DiagnosticCode.STABILITY_ANALYSIS_INVALID_ROOT_ANALYSIS
    )


def test_limits_and_resource_errors_are_structured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    limited = TransferFunctionStabilityAnalyzer(
        StabilityAnalysisLimits(max_poles=1)
    ).analyze(_root_analysis((sp.Symbol("s") + 1) * (sp.Symbol("s") + 2)))

    def exhaust(*args: object, **kwargs: object) -> None:
        raise MemoryError

    monkeypatch.setattr(stability_module, "validate_root_analysis", exhaust)
    exhausted = TransferFunctionStabilityAnalyzer().analyze(
        _root_analysis(sp.Symbol("s") + 1)
    )

    assert limited.diagnostics[0].code is (
        DiagnosticCode.STABILITY_ANALYSIS_LIMIT_EXCEEDED
    )
    assert exhausted.diagnostics[0].code is (
        DiagnosticCode.STABILITY_ANALYSIS_RESOURCE_LIMIT_EXCEEDED
    )


@pytest.mark.parametrize(
    "limits",
    [
        StabilityAnalysisLimits(max_result_items=1),
        StabilityAnalysisLimits(max_diagnostics=1),
        StabilityAnalysisLimits(max_evidence_nodes=1),
    ],
)
def test_output_limits_are_enforced(limits: StabilityAnalysisLimits) -> None:
    result = TransferFunctionStabilityAnalyzer(limits).analyze(
        _root_analysis(sp.Symbol("s"))
    )
    assert result.diagnostics[0].code is (
        DiagnosticCode.STABILITY_ANALYSIS_LIMIT_EXCEEDED
    )


def test_cancelled_location_limit_is_enforced() -> None:
    root_analysis = _root_analysis(sp.Symbol("s") + 1)
    object.__setattr__(
        root_analysis,
        "cancelled_locations",
        _cancelled_group(sp.Integer(0), sp.Integer(1)),
    )
    result = TransferFunctionStabilityAnalyzer(
        StabilityAnalysisLimits(max_cancelled_locations=1)
    ).analyze(root_analysis)
    assert result.diagnostics[0].code is (
        DiagnosticCode.STABILITY_ANALYSIS_LIMIT_EXCEEDED
    )


def test_public_results_contain_no_sympy_instances_or_parsing_dependency() -> None:
    result = TransferFunctionStabilityAnalyzer().analyze(
        _root_analysis(sp.Symbol("s") + 1)
    )
    assert not isinstance(result, (sp.Basic, sp.Poly))
    assert all(
        not isinstance(value, (sp.Basic, sp.Poly))
        for contribution in result.pole_contributions
        for value in (
            contribution.pole,
            contribution.exact_real_part,
            contribution.real_part_sign,
            contribution.reason,
        )
    )
    source = inspect.getsource(stability_module)
    assert "klausurbotpro.parsing" not in source
    assert "sympify" not in source
    assert "parse_expr" not in source


def test_no_future_stability_methods_are_exposed() -> None:
    analyzer = TransferFunctionStabilityAnalyzer()
    for name in ("hurwitz", "routh", "nyquist", "properness"):
        assert not hasattr(analyzer, name)
