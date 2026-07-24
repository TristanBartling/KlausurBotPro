"""Numerical verification subordinate to an authoritative exact root list."""

from __future__ import annotations

import sympy as sp

from klausurbotpro.domain._exact_polynomial_root_solver import (
    exact_root_as_sympy,
)
from klausurbotpro.domain.diagnostics import (
    Diagnostic,
    DiagnosticCode,
    DiagnosticSeverity,
)
from klausurbotpro.domain.root_analysis_contracts import (
    ConjugateStatus,
    NumericalRootEstimate,
    NumericalRootWarning,
    PolynomialRootAnalysis,
    RootAnalysisLimits,
)


def verify_numerical_roots(
    polynomial: sp.Poly,
    analysis: PolynomialRootAnalysis,
    limits: RootAnalysisLimits,
    *,
    field: str | None,
) -> tuple[PolynomialRootAnalysis, tuple[Diagnostic, ...]]:
    """Approximate every exact root and check residuals and conjugate pairing."""

    if not analysis.roots:
        return analysis, ()
    working_digits = limits.numeric_precision_digits + limits.numeric_guard_digits
    exact_values = [exact_root_as_sympy(item.value) for item in analysis.roots]
    candidates = [
        _evalf(value, working_digits, limits)
        for value in exact_values
    ]
    threshold = sp.Rational(1, 10) ** max(4, limits.numeric_precision_digits // 2)
    matches = _match_numerical_candidates(
        tuple(_evalf(value, working_digits, limits) for value in exact_values),
        tuple(item.multiplicity for item in analysis.roots),
        tuple(candidates),
        tuple(item.multiplicity for item in analysis.roots),
        threshold,
        working_digits,
        limits,
    )
    approximations = [candidates[index] for index in matches]
    cluster_threshold = sp.Rational(1, 10) ** max(
        3, limits.numeric_precision_digits // 3
    )
    diagnostics: list[Diagnostic] = []
    estimates: list[NumericalRootEstimate] = []

    for occurrence, approximation in zip(
        analysis.roots, approximations, strict=True
    ):
        warnings: list[NumericalRootWarning] = []
        if occurrence.multiplicity > 1:
            warnings.append(NumericalRootWarning.MULTIPLE_ROOT)
            diagnostics.append(
                _warning(
                    DiagnosticCode.ROOT_ANALYSIS_ILL_CONDITIONED,
                    "Mehrfachwurzeln können numerisch schlecht konditioniert sein.",
                    field,
                    ("root_index", str(occurrence.index)),
                )
            )
        if any(
            other_index != occurrence.index
            and _absolute_numeric(
                approximation - other, working_digits, limits
            )
            < cluster_threshold
            for other_index, other in enumerate(approximations)
        ):
            warnings.append(NumericalRootWarning.CLOSE_CLUSTER)
            diagnostics.append(
                _warning(
                    DiagnosticCode.ROOT_ANALYSIS_ILL_CONDITIONED,
                    "Nahe beieinanderliegende Wurzeln können numerisch instabil sein.",
                    field,
                    ("root_index", str(occurrence.index)),
                )
            )

        evaluated = _evaluate_polynomial(
            polynomial,
            approximation,
            working_digits,
            limits,
        )
        absolute_residual = _absolute_numeric(
            evaluated,
            working_digits,
            limits,
        )
        magnitude = _absolute_numeric(
            approximation,
            working_digits,
            limits,
        )
        scale = sp.Integer(0)
        degree = int(polynomial.degree())
        for position, coefficient in enumerate(polynomial.all_coeffs()):
            power = degree - position
            scale += sp.Abs(_evalf(coefficient, working_digits, limits)) * max(
                sp.Integer(1), magnitude
            ) ** power
        scaled_residual = _evalf(
            absolute_residual / max(sp.Integer(1), scale),
            working_digits,
            limits,
        )
        residual_limit = threshold + threshold * max(sp.Integer(1), scale)
        if absolute_residual > residual_limit:
            warnings.append(NumericalRootWarning.RESIDUAL_TOO_LARGE)
            diagnostics.append(
                _warning(
                    DiagnosticCode.ROOT_ANALYSIS_RESIDUAL_TOO_LARGE,
                    "Die numerische Wurzelprüfung weist ein zu großes Residuum auf.",
                    field,
                    ("root_index", str(occurrence.index)),
                )
            )

        real = _evalf(
            sp.re(approximation),
            limits.numeric_precision_digits,
            limits,
        )
        imaginary = _evalf(
            sp.im(approximation),
            limits.numeric_precision_digits,
            limits,
        )
        exact_is_real = exact_values[occurrence.index].is_real
        if exact_is_real is True:
            conjugate_status = ConjugateStatus.REAL
        else:
            conjugate = sp.conjugate(approximation)
            has_partner = any(
                other_index != occurrence.index
                and analysis.roots[other_index].multiplicity
                == occurrence.multiplicity
                and _absolute_numeric(
                    other - conjugate, working_digits, limits
                )
                <= threshold
                for other_index, other in enumerate(approximations)
            )
            conjugate_status = (
                ConjugateStatus.CONFIRMED
                if has_partner
                else ConjugateStatus.MISSING
            )
            if not has_partner:
                warnings.append(NumericalRootWarning.CONJUGATE_MISMATCH)
                diagnostics.append(
                    _warning(
                        DiagnosticCode.ROOT_ANALYSIS_CONJUGATE_MISMATCH,
                        "Für eine komplexe Wurzel fehlt das konjugierte Gegenstück.",
                        field,
                        ("root_index", str(occurrence.index)),
                    )
                )
        estimates.append(
            NumericalRootEstimate(
                occurrence.index,
                str(real),
                str(imaginary),
                limits.numeric_precision_digits,
                str(
                    _evalf(
                        absolute_residual,
                        limits.numeric_precision_digits,
                        limits,
                    )
                ),
                str(
                    _evalf(
                        scaled_residual,
                        limits.numeric_precision_digits,
                        limits,
                    )
                ),
                conjugate_status,
                tuple(warnings),
            )
        )

    return (
        PolynomialRootAnalysis(
            analysis.status,
            analysis.source,
            analysis.source_expression,
            analysis.roots,
            tuple(estimates),
            analysis.original_degree,
            analysis.actual_degree,
            analysis.origins,
        ),
        tuple(diagnostics),
    )


def _evalf(
    value: sp.Expr,
    digits: int,
    limits: RootAnalysisLimits,
) -> sp.Expr:
    return value.evalf(
        digits,
        maxn=limits.max_evalf_working_digits,
        strict=True,
    )


def _match_numerical_candidates(
    exact_values: tuple[sp.Expr, ...],
    exact_multiplicities: tuple[int, ...],
    candidates: tuple[sp.Expr, ...],
    candidate_multiplicities: tuple[int, ...],
    tolerance: sp.Expr,
    digits: int,
    limits: RootAnalysisLimits,
) -> tuple[int, ...]:
    """Match a numerical multiset without relying on solver output order."""

    if (
        len(exact_values) != len(exact_multiplicities)
        or len(candidates) != len(candidate_multiplicities)
        or len(exact_values) != len(candidates)
    ):
        raise ValueError("Numerical root candidates do not match exact roots.")
    unmatched = set(range(len(candidates)))
    matches: list[int] = []
    for exact_value, multiplicity in zip(
        exact_values, exact_multiplicities, strict=True
    ):
        compatible: list[tuple[sp.Expr, int]] = []
        exact_magnitude = _absolute_numeric(exact_value, digits, limits)
        for index in unmatched:
            if candidate_multiplicities[index] != multiplicity:
                continue
            candidate = candidates[index]
            distance = _absolute_numeric(
                exact_value - candidate,
                digits,
                limits,
            )
            scale = max(
                sp.Integer(1),
                exact_magnitude,
                _absolute_numeric(candidate, digits, limits),
            )
            if distance <= tolerance + tolerance * scale:
                compatible.append((distance, index))
        if not compatible:
            raise ValueError("No valid numerical candidate matches an exact root.")
        _, matched_index = min(compatible, key=lambda item: (item[0], item[1]))
        unmatched.remove(matched_index)
        matches.append(matched_index)
    return tuple(matches)


def _evaluate_polynomial(
    polynomial: sp.Poly,
    value: sp.Expr,
    digits: int,
    limits: RootAnalysisLimits,
) -> sp.Expr:
    """Evaluate by Horner's rule while retaining guard-digit precision."""

    result: sp.Expr = sp.Integer(0)
    for coefficient in polynomial.all_coeffs():
        result = sp.expand(
            result * value + _evalf(coefficient, digits, limits)
        )
    return result


def _absolute_numeric(
    value: sp.Expr,
    digits: int,
    limits: RootAnalysisLimits,
) -> sp.Expr:
    """Return a finite real magnitude without strict zero certification."""

    expanded = sp.expand(value)
    real = sp.re(expanded).evalf(
        digits,
        maxn=limits.max_evalf_working_digits,
        strict=False,
    )
    imaginary = sp.im(expanded).evalf(
        digits,
        maxn=limits.max_evalf_working_digits,
        strict=False,
    )
    magnitude = sp.sqrt(real**2 + imaginary**2).evalf(
        digits,
        maxn=limits.max_evalf_working_digits,
        strict=False,
    )
    if magnitude.is_real is not True or magnitude.is_finite is not True:
        raise ValueError("Numerical root verification produced no finite magnitude.")
    return magnitude


def _warning(
    code: DiagnosticCode,
    message: str,
    field: str | None,
    *details: tuple[str, str],
) -> Diagnostic:
    return Diagnostic(
        DiagnosticSeverity.WARNING,
        code,
        message,
        field,
        details,
    )
