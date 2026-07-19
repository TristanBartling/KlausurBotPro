"""Exact pole, zero, retained-domain, and cancellation-location analysis."""

from __future__ import annotations

from dataclasses import replace

import sympy as sp
from sympy.core.evalf import PrecisionExhausted
from sympy.polys.polyerrors import BasePolynomialError

from klausurbotpro.domain._exact_polynomial_root_solver import (
    solve_exact_polynomial_roots,
)
from klausurbotpro.domain._numeric_root_verifier import (
    verify_numerical_roots,
)
from klausurbotpro.domain._reduction_location_analyzer import (
    cancelled_factor_expressions,
)
from klausurbotpro.domain._root_analysis_validation import (
    RootAnalysisFailure,
    specialize_expression_as_polynomial,
    specialize_polynomial,
    validate_prerequisites,
    validate_reduced_transfer_function,
    validate_substitutions,
)
from klausurbotpro.domain.diagnostics import (
    Diagnostic,
    DiagnosticCode,
    DiagnosticSeverity,
)
from klausurbotpro.domain.expression import ExactExpression
from klausurbotpro.domain.parameter_substitutions import (
    ParameterSubstitutions,
)
from klausurbotpro.domain.polynomial import Polynomial
from klausurbotpro.domain.reduced_transfer_function import (
    ReducedTransferFunction,
)
from klausurbotpro.domain.root_analysis_contracts import (
    PolynomialRootAnalysis,
    PolynomialRootStatus,
    RootAnalysisGroup,
    RootAnalysisLimits,
    RootOfValue,
    RootSource,
    TransferFunctionRootAnalysisResult,
)
from klausurbotpro.domain.transfer_function_reduction_contracts import (
    TransferFunctionReductionResult,
)

_RESOURCE_ERRORS = (MemoryError, RecursionError, OverflowError)
_DEFAULT_LIMITS = RootAnalysisLimits()


class TransferFunctionRootAnalyzer:
    """Analyze exact roots without changing reduced transfer-function semantics."""

    def __init__(self, limits: RootAnalysisLimits = _DEFAULT_LIMITS) -> None:
        if type(limits) is not RootAnalysisLimits:
            raise TypeError("limits must be RootAnalysisLimits.")
        self._limits = limits

    def analyze(
        self,
        reduced: ReducedTransferFunction,
        substitutions: ParameterSubstitutions | None = None,
        *,
        field: str | None = None,
    ) -> TransferFunctionRootAnalysisResult:
        """Analyze a reduced value; cancelled locations remain not evaluated."""

        return self._run(
            reduced,
            substitutions,
            cancelled_factors=None,
            field=field,
        )

    def analyze_reduction(
        self,
        reduction: TransferFunctionReductionResult,
        substitutions: ParameterSubstitutions | None = None,
        *,
        field: str | None = None,
    ) -> TransferFunctionRootAnalysisResult:
        """Also analyze locations proven cancelled by polynomial reduction steps."""

        try:
            factors = cancelled_factor_expressions(reduction, self._limits)
        except RootAnalysisFailure as failure:
            return self._failure(None, substitutions, failure, field)
        except _RESOURCE_ERRORS as error:
            return self._resource_failure(None, substitutions, error, field)
        assert reduction.reduced is not None
        return self._run(
            reduction.reduced,
            substitutions,
            cancelled_factors=factors,
            field=field,
        )

    def _run(
        self,
        reduced: ReducedTransferFunction,
        substitutions: ParameterSubstitutions | None,
        *,
        cancelled_factors: tuple[ExactExpression, ...] | None,
        field: str | None,
    ) -> TransferFunctionRootAnalysisResult:
        diagnostics: list[Diagnostic] = []
        try:
            validate_reduced_transfer_function(reduced, self._limits)
            normalized_substitutions, mapping = validate_substitutions(
                reduced, substitutions, self._limits
            )
            if mapping is None:
                diagnostics.append(
                    Diagnostic(
                        DiagnosticSeverity.WARNING,
                        DiagnosticCode.ROOT_ANALYSIS_SYMBOLIC_UNDETERMINED,
                        "Ohne vollständige Parameterbelegung bleiben symbolische "
                        "Wurzeln unbestimmt.",
                        field,
                    )
                )
            else:
                validate_prerequisites(reduced, mapping, self._limits)

            zeros, zero_diagnostics = self._analyze_polynomial(
                reduced.numerator,
                RootSource.NUMERATOR,
                mapping,
                field=field,
            )
            diagnostics.extend(zero_diagnostics)
            poles, pole_diagnostics = self._analyze_polynomial(
                reduced.denominator,
                RootSource.DENOMINATOR,
                mapping,
                field=field,
            )
            diagnostics.extend(pole_diagnostics)
            if poles.status is PolynomialRootStatus.ZERO_POLYNOMIAL:
                raise RootAnalysisFailure(
                    DiagnosticCode.ROOT_ANALYSIS_INVALID_TRANSFER_FUNCTION,
                    "Der Nenner wird unter der Substitution zum Nullpolynom.",
                )

            exclusions = self._analyze_domain_exclusions(
                reduced, mapping, diagnostics, field
            )
            cancelled = self._analyze_cancelled_factors(
                reduced,
                cancelled_factors,
                mapping,
                diagnostics,
                field,
            )
            self._enforce_result_limits(zeros, poles, exclusions, cancelled)
            return TransferFunctionRootAnalysisResult(
                reduced,
                normalized_substitutions,
                zeros,
                poles,
                exclusions,
                cancelled,
                tuple(diagnostics),
            )
        except RootAnalysisFailure as failure:
            return self._failure(reduced, substitutions, failure, field)
        except _RESOURCE_ERRORS as error:
            return self._resource_failure(reduced, substitutions, error, field)
        except BasePolynomialError as error:
            return self._failure(
                reduced,
                substitutions,
                RootAnalysisFailure(
                    DiagnosticCode.ROOT_ANALYSIS_EXACT_SOLVER_FAILED,
                    "Der exakte Polynomlöser konnte die Wurzeln nicht bestimmen.",
                    (("exception", type(error).__name__),),
                ),
                field,
            )

    def _analyze_polynomial(
        self,
        polynomial: Polynomial,
        source: RootSource,
        mapping: dict[sp.Symbol, sp.Rational] | None,
        *,
        field: str | None,
        origins: tuple[str, ...] = (),
    ) -> tuple[PolynomialRootAnalysis, tuple[Diagnostic, ...]]:
        original_degree = polynomial.degree_info.generic_degree
        if mapping is None and polynomial.used_parameter_names:
            return (
                PolynomialRootAnalysis(
                    PolynomialRootStatus.SYMBOLIC_UNDETERMINED,
                    source,
                    polynomial.expression,
                    original_degree=original_degree,
                    origins=origins,
                ),
                (),
            )
        specialized = specialize_polynomial(
            polynomial, {} if mapping is None else mapping, self._limits
        )
        try:
            analysis = solve_exact_polynomial_roots(
                specialized._as_sympy_poly(),
                source=source,
                source_expression=specialized.expression,
                original_degree=original_degree,
                limits=self._limits,
                origins=origins,
            )
        except ValueError as error:
            raise RootAnalysisFailure(
                DiagnosticCode.ROOT_ANALYSIS_LIMIT_EXCEEDED,
                "Eine konfigurierte Grenze der exakten Wurzellösung wurde überschritten.",
                (("limit", str(error)),),
            ) from error
        except ArithmeticError as error:
            raise RootAnalysisFailure(
                DiagnosticCode.ROOT_ANALYSIS_EXACT_SOLVER_FAILED,
                "Der exakte Polynomlöser lieferte keine vollständige Wurzelmenge.",
                (("exception", type(error).__name__),),
            ) from error

        local_diagnostics: list[Diagnostic] = []
        degree_dropped = original_degree is not None and (
            analysis.status is PolynomialRootStatus.ZERO_POLYNOMIAL
            or (
                analysis.actual_degree is not None
                and analysis.actual_degree < original_degree
            )
        )
        if degree_dropped:
            local_diagnostics.append(
                Diagnostic(
                    DiagnosticSeverity.WARNING,
                    DiagnosticCode.ROOT_ANALYSIS_DEGREE_DROPPED,
                    "Die Parameterbelegung senkt den tatsächlichen Polynomgrad.",
                    field,
                    (
                        ("original_degree", str(original_degree)),
                        (
                            "actual_degree",
                            (
                                "zero_polynomial"
                                if analysis.actual_degree is None
                                else str(analysis.actual_degree)
                            ),
                        ),
                    ),
                )
            )
        if analysis.status is PolynomialRootStatus.ZERO_POLYNOMIAL:
            local_diagnostics.append(
                Diagnostic(
                    DiagnosticSeverity.INFO,
                    DiagnosticCode.ROOT_ANALYSIS_ZERO_POLYNOMIAL,
                    "Das analysierte Zählerpolynom ist identisch null.",
                    field,
                )
            )
            return analysis, tuple(local_diagnostics)
        try:
            verified, numeric_diagnostics = verify_numerical_roots(
                specialized._as_sympy_poly(),
                analysis,
                self._limits,
                field=field,
            )
            local_diagnostics.extend(numeric_diagnostics)
            return verified, tuple(local_diagnostics)
        except (ArithmeticError, PrecisionExhausted, ValueError) as error:
            local_diagnostics.append(
                Diagnostic(
                    DiagnosticSeverity.WARNING,
                    DiagnosticCode.ROOT_ANALYSIS_NUMERIC_SOLVER_FAILED,
                    "Die exakten Wurzeln liegen vor, ihre numerische Prüfung ist "
                    "jedoch fehlgeschlagen.",
                    field,
                    (("exception", type(error).__name__),),
                )
            )
            local_diagnostics.append(
                Diagnostic(
                    DiagnosticSeverity.INFO,
                    DiagnosticCode.ROOT_ANALYSIS_NUMERIC_CHECK_SKIPPED,
                    "Für mindestens eine exakte Wurzel fehlt die numerische Prüfung.",
                    field,
                )
            )
            return analysis, tuple(local_diagnostics)

    def _analyze_domain_exclusions(
        self,
        reduced: ReducedTransferFunction,
        mapping: dict[sp.Symbol, sp.Rational] | None,
        diagnostics: list[Diagnostic],
        field: str | None,
    ) -> RootAnalysisGroup:
        analyses: list[PolynomialRootAnalysis] = []
        keys: dict[str, int] = {}
        for exclusion in reduced.domain_exclusions:
            analysis, local = self._analyze_polynomial(
                exclusion.polynomial,
                RootSource.DOMAIN_EXCLUSION,
                mapping,
                field=field,
                origins=exclusion.origins,
            )
            diagnostics.extend(local)
            if analysis.status is PolynomialRootStatus.ZERO_POLYNOMIAL:
                raise RootAnalysisFailure(
                    DiagnosticCode.ROOT_ANALYSIS_DOMAIN_EMPTY,
                    "Ein Definitionsausschluss wird identisch null; der "
                    "Definitionsbereich ist leer.",
                    (("exclusion", exclusion.description),),
                )
            key = _location_key(analysis)
            if key in keys:
                position = keys[key]
                previous = analyses[position]
                analyses[position] = replace(
                    previous,
                    origins=tuple(sorted(set(previous.origins + analysis.origins))),
                )
            else:
                keys[key] = len(analyses)
                analyses.append(analysis)
        status = _group_status(analyses)
        return RootAnalysisGroup(status, tuple(analyses))

    def _analyze_cancelled_factors(
        self,
        reduced: ReducedTransferFunction,
        factors: tuple[ExactExpression, ...] | None,
        mapping: dict[sp.Symbol, sp.Rational] | None,
        diagnostics: list[Diagnostic],
        field: str | None,
    ) -> RootAnalysisGroup:
        if factors is None:
            return RootAnalysisGroup(PolynomialRootStatus.NOT_EVALUATED)
        analyses: list[PolynomialRootAnalysis] = []
        for factor in factors:
            if reduced.variable_name not in factor.symbol_names:
                analyses.append(
                    PolynomialRootAnalysis(
                        PolynomialRootStatus.CONSTANT_NONZERO,
                        RootSource.CANCELLED_FACTOR,
                        factor,
                        actual_degree=0,
                    )
                )
                continue
            if mapping is None and (
                factor.symbol_names - frozenset({reduced.variable_name})
            ):
                analyses.append(
                    PolynomialRootAnalysis(
                        PolynomialRootStatus.SYMBOLIC_UNDETERMINED,
                        RootSource.CANCELLED_FACTOR,
                        factor,
                    )
                )
                continue
            polynomial = specialize_expression_as_polynomial(
                factor,
                variable_name=reduced.variable_name,
                mapping={} if mapping is None else mapping,
                limits=self._limits,
            )
            analysis, local = self._analyze_polynomial(
                polynomial,
                RootSource.CANCELLED_FACTOR,
                {},
                field=field,
            )
            diagnostics.extend(local)
            analyses.append(analysis)
        return RootAnalysisGroup(_group_status(analyses), tuple(analyses))

    def _enforce_result_limits(
        self,
        zeros: PolynomialRootAnalysis,
        poles: PolynomialRootAnalysis,
        exclusions: RootAnalysisGroup,
        cancelled: RootAnalysisGroup,
    ) -> None:
        analyses = (
            zeros,
            poles,
            *exclusions.analyses,
            *cancelled.analyses,
        )
        result_count = sum(len(item.roots) for item in analyses)
        if result_count > self._limits.max_results:
            raise RootAnalysisFailure(
                DiagnosticCode.ROOT_ANALYSIS_LIMIT_EXCEEDED,
                "Die Wurzelanalyse erzeugt zu viele Ergebniswerte.",
                (("limit", "max_results"),),
            )
        rootof_count = sum(
            occurrence.multiplicity
            for analysis in analyses
            for occurrence in analysis.roots
            if isinstance(occurrence.value, RootOfValue)
        )
        if rootof_count > self._limits.max_exact_rootof_count:
            raise RootAnalysisFailure(
                DiagnosticCode.ROOT_ANALYSIS_LIMIT_EXCEEDED,
                "Die Wurzelanalyse erzeugt zu viele RootOf-Werte.",
                (("limit", "max_exact_rootof_count"),),
            )

    @staticmethod
    def _failure(
        reduced: ReducedTransferFunction | None,
        substitutions: ParameterSubstitutions | None,
        failure: RootAnalysisFailure,
        field: str | None,
    ) -> TransferFunctionRootAnalysisResult:
        diagnostic = Diagnostic(
            DiagnosticSeverity.ERROR,
            failure.code,
            failure.message,
            field,
            failure.details,
        )
        return TransferFunctionRootAnalysisResult(
            None,
            substitutions,
            None,
            None,
            RootAnalysisGroup(PolynomialRootStatus.NOT_EVALUATED),
            RootAnalysisGroup(PolynomialRootStatus.NOT_EVALUATED),
            (diagnostic,),
        )

    @classmethod
    def _resource_failure(
        cls,
        reduced: ReducedTransferFunction | None,
        substitutions: ParameterSubstitutions | None,
        error: BaseException,
        field: str | None,
    ) -> TransferFunctionRootAnalysisResult:
        return cls._failure(
            reduced,
            substitutions,
            RootAnalysisFailure(
                DiagnosticCode.ROOT_ANALYSIS_RESOURCE_LIMIT_EXCEEDED,
                "Die Wurzelanalyse überschreitet verfügbare Ressourcen.",
                (("exception", type(error).__name__),),
            ),
            field,
        )


def _location_key(analysis: PolynomialRootAnalysis) -> str:
    if analysis.status is PolynomialRootStatus.SYMBOLIC_UNDETERMINED:
        return f"symbolic:{analysis.source_expression.canonical_text}"
    if analysis.status is PolynomialRootStatus.CONSTANT_NONZERO:
        return "constant"
    values = tuple(item.value for item in analysis.roots)
    return repr(values)


def _group_status(
    analyses: list[PolynomialRootAnalysis],
) -> PolynomialRootStatus:
    if any(
        item.status is PolynomialRootStatus.SYMBOLIC_UNDETERMINED
        for item in analyses
    ):
        return PolynomialRootStatus.SYMBOLIC_UNDETERMINED
    return PolynomialRootStatus.COMPLETE


__all__ = ["TransferFunctionRootAnalyzer"]
