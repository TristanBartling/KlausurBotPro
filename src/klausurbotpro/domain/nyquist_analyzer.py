"""Nyquist analysis over existing Bode segments and local evaluations."""

from __future__ import annotations

from contextlib import suppress
from math import atan2, pi

import numpy as np
import sympy as sp
from scipy.optimize import minimize_scalar

from klausurbotpro.domain.bode_data_contracts import TransferFunctionBodeDataResult
from klausurbotpro.domain.diagnostics import Diagnostic, DiagnosticCode, DiagnosticSeverity
from klausurbotpro.domain.frequency_reserve_contracts import FrequencyCrossoverAnalysis
from klausurbotpro.domain.nyquist_contracts import (
    ClassifiedPole,
    ClosedLoopStabilityStatus,
    CriticalPointStatus,
    NyquistAnalysisResult,
    NyquistClosureStatus,
    NyquistCriterion,
    NyquistCriticalPoint,
    NyquistCurveSegment,
    NyquistNumericalQuality,
    NyquistStabilityStatement,
    NyquistWindingResult,
    OpenLoopPoleClassification,
    PoleClassificationStatus,
    ScalarGainDomain,
    ScalarGainIntervalResult,
    ScalarGainRangeResult,
)
from klausurbotpro.domain.parameter_substitutions import ParameterSubstitutions
from klausurbotpro.domain.reduced_transfer_function import ReducedTransferFunction
from klausurbotpro.domain.transfer_function_root_analyzer import TransferFunctionRootAnalyzer

_AXIS_TOL = 1e-8
_CRITICAL_HIT = 1e-7
_CRITICAL_NEAR = 1e-4


class NyquistAnalyzer:
    """Classify poles, construct the full contour, and apply ``Z=P+N_cw``."""

    def analyze(
        self,
        transfer_function: ReducedTransferFunction,
        substitutions: ParameterSubstitutions,
        bode: TransferFunctionBodeDataResult,
        crossovers: FrequencyCrossoverAnalysis | None = None,
        *,
        scalar_gain_domain: ScalarGainDomain | None = None,
    ) -> NyquistAnalysisResult:
        evaluator = _ComplexEvaluator(transfer_function, substitutions)
        poles = _classify_poles(transfer_function, substitutions)
        proper = _degree(transfer_function.numerator) < _degree(transfer_function.denominator)
        unsupported = (
            poles.imaginary_axis_poles
            or poles.status is PoleClassificationStatus.AMBIGUOUS
            or not proper
        )
        if unsupported:
            code = (
                DiagnosticCode.IMAG_AXIS_POLE_MODIFIED_CONTOUR_REQUIRED
                if poles.imaginary_axis_poles
                else DiagnosticCode.BIPROPER_OR_IMPROPER_NYQUIST_UNSUPPORTED
            )
            winding = _unsupported_winding(bode, evaluator, code)
            statement = NyquistStabilityStatement(
                poles.rhp_pole_count,
                None,
                None,
                NyquistCriterion.NOT_APPLICABLE,
                False,
                False,
                ClosedLoopStabilityStatus.NOT_DETERMINED,
                "Keine Nyquist-Stabilitätsaussage: Eine modifizierte oder "
                "erweiterte Kontur ist erforderlich.",
            )
        else:
            winding = _winding(bode, evaluator, gain=1.0)
            statement = _stability(poles, winding)
        gain_range = (
            self._gain_range(transfer_function, substitutions, bode, poles, scalar_gain_domain)
            if scalar_gain_domain is not None and proper and not poles.imaginary_axis_poles
            else None
        )
        return NyquistAnalysisResult(poles, winding, statement, gain_range)

    def _gain_range(
        self,
        transfer_function: ReducedTransferFunction,
        substitutions: ParameterSubstitutions,
        bode: TransferFunctionBodeDataResult,
        poles: OpenLoopPoleClassification,
        domain: ScalarGainDomain,
    ) -> ScalarGainRangeResult:
        evaluator = _ComplexEvaluator(transfer_function, substitutions)
        critical = _critical_gains(transfer_function, substitutions, domain)
        bounds = [domain.lower, *critical, domain.upper]
        intervals: list[ScalarGainIntervalResult] = []
        stable: list[ScalarGainDomain] = []
        for lower, upper in zip(bounds, bounds[1:], strict=False):
            test = _test_gain(lower, upper)
            winding = _winding(bode, evaluator, gain=test)
            if winding.clockwise_encirclements is None:
                continue
            z = poles.rhp_pole_count + winding.clockwise_encirclements
            interval = ScalarGainDomain(lower, upper)
            item = ScalarGainIntervalResult(
                interval, test, poles.rhp_pole_count, winding.clockwise_encirclements, z, z == 0
            )
            intervals.append(item)
            if item.stable:
                stable.append(interval)
        return ScalarGainRangeResult(domain, critical, tuple(intervals), tuple(stable), True)


def _classify_poles(
    transfer_function: ReducedTransferFunction,
    substitutions: ParameterSubstitutions,
) -> OpenLoopPoleClassification:
    roots = TransferFunctionRootAnalyzer().analyze(transfer_function, substitutions)
    occurrences = () if roots.reduced_poles is None else roots.reduced_poles.roots
    lhp: list[ClassifiedPole] = []
    rhp: list[ClassifiedPole] = []
    imag: list[ClassifiedPole] = []
    origin: list[ClassifiedPole] = []
    estimates = {
        estimate.root_index: estimate
        for estimate in (
            ()
            if roots.reduced_poles is None
            else roots.reduced_poles.numerical_estimates
        )
    }
    ambiguous = roots.reduced_poles is None
    distances: list[float] = []
    for occurrence in occurrences:
        estimate = estimates.get(occurrence.index)
        if estimate is not None:
            value = complex(float(estimate.real), float(estimate.imaginary))
        elif hasattr(occurrence.value, "expression"):
            numeric = complex(sp.N(occurrence.value.expression._as_sympy(), 30))
            value = complex(float(numeric.real), float(numeric.imag))
        else:
            ambiguous = True
            continue
        pole = ClassifiedPole(value, occurrence.multiplicity)
        distances.append(abs(value.real))
        tolerance = _AXIS_TOL * max(1.0, abs(value))
        if abs(value.real) <= tolerance:
            imag.append(pole)
            if abs(value) <= tolerance:
                origin.append(pole)
        elif value.real > 0:
            rhp.append(pole)
        else:
            lhp.append(pole)
    return OpenLoopPoleClassification(
        tuple(lhp), tuple(rhp), tuple(imag), tuple(origin),
        sum(item.multiplicity for item in rhp),
        PoleClassificationStatus.AMBIGUOUS if ambiguous else PoleClassificationStatus.UNIQUE,
        min(distances, default=0.0),
        tuple(
            "Gekürzte Stelle aus dem Rohmodell; interne Stabilität separat prüfen."
            for _ in transfer_function.domain_exclusions
        ),
    )


def _positive_samples(
    bode: TransferFunctionBodeDataResult,
    evaluator: _ComplexEvaluator,
) -> tuple[tuple[float, complex], ...]:
    samples: list[tuple[float, complex]] = []
    with suppress(ZeroDivisionError, ValueError, OverflowError):
        samples.append((0.0, evaluator.at(0.0)))
    for segment in bode.magnitude_segments:
        for point in segment.points:
            response = point.frequency_response_point
            if response.numerical_real is None or response.numerical_imaginary is None:
                continue
            omega = (
                float(point.evaluation_frequency.numerator)
                / point.evaluation_frequency.denominator
            )
            samples.append(
                (
                    omega,
                    complex(
                        float(response.numerical_real),
                        float(response.numerical_imaginary),
                    ),
                )
            )
    samples = sorted(dict(samples).items())
    omega = max(samples[-1][0], 1.0)
    while abs(evaluator.at(omega)) > 1e-7 and omega < 1e12:
        omega *= 10.0
        samples.append((omega, evaluator.at(omega)))
    samples.append((float("inf"), 0j))
    return tuple(samples)


def _winding(
    bode: TransferFunctionBodeDataResult,
    evaluator: _ComplexEvaluator,
    *,
    gain: float,
) -> NyquistWindingResult:
    positive = _positive_samples(bode, evaluator)
    frequencies = [item[0] for item in positive]
    values = [gain * item[1] for item in positive]
    # Refine the minimum of |1 + K G| on every finite frequency interval.
    min_distance = float("inf")
    min_frequency = 0.0
    for left, right in zip(frequencies, frequencies[1:], strict=False):
        if not np.isfinite(right) or left == right:
            continue
        fit = minimize_scalar(
            lambda omega: abs(1.0 + gain * evaluator.at(float(omega))),
            bounds=(left, right), method="bounded",
        )
        candidates = ((left, abs(1 + gain * evaluator.at(left))), (float(fit.x), float(fit.fun)))
        omega, distance = min(candidates, key=lambda item: item[1])
        if distance < min_distance:
            min_frequency, min_distance = omega, distance
    critical_status = (
        CriticalPointStatus.HIT if min_distance <= _CRITICAL_HIT
        else CriticalPointStatus.NEAR if min_distance <= _CRITICAL_NEAR
        else CriticalPointStatus.CLEAR
    )
    negative_values = [value.conjugate() for value in reversed(values[1:])]
    contour = negative_values + values
    negative_frequencies = tuple(-value for value in reversed(frequencies[1:]))
    curve_segments = (
        NyquistCurveSegment(0, -1, negative_frequencies, tuple(negative_values)),
        NyquistCurveSegment(1, 1, tuple(frequencies), tuple(values)),
    )
    critical = NyquistCriticalPoint(-1 + 0j, min_distance, min_frequency, critical_status)
    if critical_status is not CriticalPointStatus.CLEAR:
        return NyquistWindingResult(
            curve_segments, critical, None, None, None, NyquistClosureStatus.CLOSED,
            True, NyquistNumericalQuality.AMBIGUOUS,
        )
    q = [1.0 + value for value in contour]
    angle_sum = sum(
        atan2((a.conjugate() * b).imag, (a.conjugate() * b).real)
        for a, b in zip(q, q[1:], strict=False)
    )
    raw_ccw = angle_sum / (2 * pi)
    ccw = round(raw_ccw)
    polygon_ccw = _ray_winding(q)
    quality = (
        NyquistNumericalQuality.VERIFIED
        if abs(raw_ccw - ccw) <= 1e-4 and ccw == polygon_ccw
        else NyquistNumericalQuality.AMBIGUOUS
    )
    public = -ccw if quality is NyquistNumericalQuality.VERIFIED else None
    polygon_public = -polygon_ccw if quality is NyquistNumericalQuality.VERIFIED else None
    return NyquistWindingResult(
        curve_segments, critical, ccw if public is not None else None, public,
        polygon_public, NyquistClosureStatus.CLOSED, True, quality,
    )


def _ray_winding(points: list[complex]) -> int:
    winding = 0
    for first, second in zip(points, points[1:], strict=False):
        if first.imag <= 0 < second.imag and (first.conjugate() * second).imag > 0:
            winding += 1
        elif second.imag <= 0 < first.imag and (first.conjugate() * second).imag < 0:
            winding -= 1
    return winding


def _stability(
    poles: OpenLoopPoleClassification,
    winding: NyquistWindingResult,
) -> NyquistStabilityStatement:
    n_cw = winding.clockwise_encirclements
    if n_cw is None or winding.quality is not NyquistNumericalQuality.VERIFIED:
        return NyquistStabilityStatement(
            poles.rhp_pole_count, None, None, NyquistCriterion.NOT_APPLICABLE,
            False, False, ClosedLoopStabilityStatus.NOT_DETERMINED,
            "Keine belastbare Stabilitätsaussage möglich.",
        )
    z = poles.rhp_pole_count + n_cw
    if z < 0:
        return NyquistStabilityStatement(
            poles.rhp_pole_count, n_cw, None, NyquistCriterion.NOT_APPLICABLE,
            False, False, ClosedLoopStabilityStatus.NOT_DETERMINED,
            "Die numerische Zählung ist mit Z ≥ 0 unvereinbar.",
        )
    stable = z == 0
    simplified = poles.rhp_pole_count == 0
    status = (
        ClosedLoopStabilityStatus.ASYMPTOTICALLY_STABLE
        if stable
        else ClosedLoopStabilityStatus.UNSTABLE
    )
    statement = (
        "Der geschlossene Kreis ist asymptotisch stabil."
        if stable
        else f"Der geschlossene Kreis ist instabil und besitzt {z} RHP-Pol(e)."
    )
    return NyquistStabilityStatement(
        poles.rhp_pole_count, n_cw, z,
        NyquistCriterion.SIMPLIFIED if simplified else NyquistCriterion.COMPLETE,
        simplified, True,
        status,
        statement,
    )


def _unsupported_winding(
    bode: TransferFunctionBodeDataResult,
    evaluator: _ComplexEvaluator,
    code: DiagnosticCode,
) -> NyquistWindingResult:
    positive = _positive_samples(bode, evaluator)
    segment = NyquistCurveSegment(
        0,
        1,
        tuple(item[0] for item in positive),
        tuple(item[1] for item in positive),
    )
    distances = tuple((omega, abs(1 + value)) for omega, value in positive)
    omega, distance = min(distances, key=lambda item: item[1])
    return NyquistWindingResult(
        (segment,), NyquistCriticalPoint(-1 + 0j, distance, omega, CriticalPointStatus.CLEAR),
        None,
        None,
        None,
        NyquistClosureStatus.UNSUPPORTED,
        False,
        NyquistNumericalQuality.NOT_APPLICABLE,
        (
            Diagnostic(
                DiagnosticSeverity.WARNING,
                code,
                "Standard-Nyquistzählung ohne modifizierte beziehungsweise "
                "erweiterte Kontur nicht zulässig.",
            ),
        ),
    )


def _critical_gains(
    transfer_function: ReducedTransferFunction,
    substitutions: ParameterSubstitutions,
    domain: ScalarGainDomain,
) -> tuple[float, ...]:
    s = sp.Symbol(transfer_function.variable_name)
    omega = sp.Symbol("omega", real=True)
    expression = _specialized_expression(transfer_function, substitutions)
    response = sp.cancel(expression.subs(s, sp.I * omega))
    imaginary = sp.together(sp.im(response)).as_numer_denom()[0]
    candidates = set()
    for root in sp.solve(imaginary, omega):
        if root.is_real and root.is_nonnegative:
            real = sp.re(response.subs(omega, root))
            if real != 0:
                candidates.add(float(sp.N(-1 / real, 16)))
    values = tuple(sorted(value for value in candidates if _in_domain(value, domain)))
    return values


def _in_domain(value: float, domain: ScalarGainDomain) -> bool:
    return (domain.lower is None or value > domain.lower) and (
        domain.upper is None or value < domain.upper
    )


def _test_gain(lower: float | None, upper: float | None) -> float:
    if lower is None and upper is None:
        return 1.0
    if lower is None:
        assert upper is not None
        return upper - max(1.0, abs(upper))
    if upper is None:
        return lower + max(1.0, abs(lower))
    return (lower + upper) / 2.0


def _degree(polynomial: object) -> int:
    degree = polynomial.degree_info.guaranteed_degree  # type: ignore[attr-defined]
    return 0 if degree is None else degree


def _specialized_expression(
    transfer_function: ReducedTransferFunction,
    substitutions: ParameterSubstitutions,
) -> sp.Expr:
    replacements = {
        sp.Symbol(item.parameter_name): sp.Rational(
            item.value.numerator,
            item.value.denominator,
        )
        for item in substitutions.assignments
    }
    numerator = transfer_function.numerator._as_sympy_poly().as_expr()
    denominator = transfer_function.denominator._as_sympy_poly().as_expr()
    return numerator.subs(replacements) / denominator.subs(replacements)


class _ComplexEvaluator:
    def __init__(
        self,
        transfer_function: ReducedTransferFunction,
        substitutions: ParameterSubstitutions,
    ) -> None:
        s = sp.Symbol(transfer_function.variable_name)
        expression = _specialized_expression(transfer_function, substitutions)
        self._function = sp.lambdify(s, expression, "numpy")

    def at(self, omega: float) -> complex:
        return complex(self._function(1j * omega))


__all__ = ["NyquistAnalyzer"]
