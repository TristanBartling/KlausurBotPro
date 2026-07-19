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
    approximations = [
        _evalf(value, working_digits, limits)
        for value in exact_values
    ]
    threshold = sp.Rational(1, 10) ** max(4, limits.numeric_precision_digits // 2)
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
            and _evalf(
                abs(approximation - other), working_digits, limits
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

        evaluated = polynomial.as_expr().subs(
            polynomial.gens[0], approximation
        )
        absolute_residual = _evalf(
            sp.re(
                _evalf(sp.Abs(evaluated), working_digits, limits)
            ),
            working_digits,
            limits,
        )
        magnitude = _evalf(
            sp.re(
                _evalf(sp.Abs(approximation), working_digits, limits)
            ),
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
        if scaled_residual > threshold:
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
                and _evalf(
                    abs(other - conjugate), working_digits, limits
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
