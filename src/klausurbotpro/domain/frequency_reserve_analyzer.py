"""Segment-local numerical crossover detection using existing response data."""

from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal
from fractions import Fraction
from math import floor, isfinite, log10

import sympy as sp
from scipy.optimize import brentq, minimize_scalar

from klausurbotpro.domain.bode_data_contracts import TransferFunctionBodeDataResult
from klausurbotpro.domain.bode_phase_unwrap_contracts import BodePhaseUnwrapResult
from klausurbotpro.domain.frequency_reserve_contracts import (
    BandCompletenessStatus,
    CrossoverDetectionMethod,
    CrossoverDirection,
    FrequencyCrossover,
    FrequencyCrossoverAnalysis,
    FrequencyCrossoverType,
    NumericalQuality,
    ReserveInterpretationStatus,
    StabilityReserve,
    StabilityReserveAnalysis,
    StabilityReserveType,
)
from klausurbotpro.domain.frequency_response_contracts import FrequencySampleSet
from klausurbotpro.domain.parameter_substitutions import ExactRationalValue, ParameterSubstitutions
from klausurbotpro.domain.reduced_transfer_function import ReducedTransferFunction
from klausurbotpro.domain.transfer_function_frequency_response_analyzer import (
    TransferFunctionFrequencyResponseAnalyzer,
)

_GRID_TOL = 1e-8
_DB_TOL = 2e-6
_MAG_TOL = 2e-7
_PHASE_TOL = 2e-4
_AXIS_TOL = 2e-7


class FrequencyReserveAnalyzer:
    """Find and verify all sampled-band crossovers without crossing gaps."""

    def analyze(
        self,
        transfer_function: ReducedTransferFunction,
        substitutions: ParameterSubstitutions,
        bode: TransferFunctionBodeDataResult,
        unwrapped: BodePhaseUnwrapResult,
        *,
        field: str = "transfer_function",
    ) -> tuple[FrequencyCrossoverAnalysis, StabilityReserveAnalysis]:
        if unwrapped.source_bode_data is not bode:
            raise ValueError("Unwrapped phases must belong to the supplied Bode data.")
        evaluator = _Evaluator(transfer_function, substitutions, field)
        gains: list[FrequencyCrossover] = []
        phases: list[FrequencyCrossover] = []
        incomplete: set[int] = set()
        for segment in unwrapped.segments:
            samples = tuple(
                (
                    float(point.source_point.evaluation_frequency.numerator)
                    / point.source_point.evaluation_frequency.denominator,
                    float(point.source_point.numerical_decibel.decimal_value or "nan"),
                    float(point.unwrapped_phase_degrees),
                )
                for point in segment.points
                if point.source_point.numerical_decibel is not None
            )
            if len(samples) < 2 or any(not all(isfinite(v) for v in row) for row in samples):
                incomplete.add(segment.segment_index)
                continue
            gains.extend(
                self._gain_crossovers(
                    samples,
                    segment.segment_index,
                    evaluator,
                    transfer_function,
                    substitutions,
                )
            )
            phases.extend(self._phase_crossovers(samples, segment.segment_index, evaluator))
        gains = _deduplicate(gains)
        phases = _deduplicate(phases)
        if incomplete or len(unwrapped.segments) != 1:
            completeness = BandCompletenessStatus.SEGMENT_INCOMPLETE
        else:
            only_segment = unwrapped.segments[0]
            lower = (
                float(only_segment.points[0].source_point.evaluation_frequency.numerator)
                / only_segment.points[0].source_point.evaluation_frequency.denominator
            )
            upper = (
                float(only_segment.points[-1].source_point.evaluation_frequency.numerator)
                / only_segment.points[-1].source_point.evaluation_frequency.denominator
            )
            completeness = (
                BandCompletenessStatus.COMPLETE_IN_PROVEN_RANGE
                if _all_algebraic_candidates_in_band(transfer_function, substitutions, lower, upper)
                else BandCompletenessStatus.BAND_LIMITED
            )
        crossover_analysis = FrequencyCrossoverAnalysis(
            tuple(sorted(gains, key=lambda item: item.frequency)),
            tuple(sorted(phases, key=lambda item: item.frequency)),
            tuple(segment.segment_index for segment in unwrapped.segments),
            tuple(sorted(incomplete)),
            completeness,
        )
        return crossover_analysis, _reserves(crossover_analysis)

    def _gain_crossovers(
        self,
        samples: tuple[tuple[float, float, float], ...],
        segment_index: int,
        evaluator: _Evaluator,
        transfer_function: ReducedTransferFunction,
        substitutions: ParameterSubstitutions,
    ) -> list[FrequencyCrossover]:
        candidates: list[tuple[float, tuple[float, float], CrossoverDetectionMethod]] = []
        for index, (omega, db, _) in enumerate(samples):
            if abs(db) <= _GRID_TOL:
                candidates.append((omega, (omega, omega), CrossoverDetectionMethod.GRID_HIT))
            if index + 1 < len(samples):
                nxt = samples[index + 1]
                if db * nxt[1] < 0:
                    root = brentq(lambda value: evaluator.at(value)[3], omega, nxt[0], xtol=1e-12)
                    candidates.append(
                        (root, (omega, nxt[0]), CrossoverDetectionMethod.BRACKETED_SIGN_CHANGE)
                    )
        for index in range(1, len(samples) - 1):
            sample_left = samples[index - 1]
            middle = samples[index]
            sample_right = samples[index + 1]
            if abs(middle[1]) < abs(sample_left[1]) and abs(middle[1]) < abs(sample_right[1]):
                fit = minimize_scalar(
                    lambda value: evaluator.at(value)[3] ** 2,
                    bounds=(sample_left[0], sample_right[0]),
                    method="bounded",
                    options={"xatol": 1e-13},
                )
                if fit.success and abs(evaluator.at(float(fit.x))[3]) <= _DB_TOL:
                    candidates.append(
                        (
                            float(fit.x),
                            (sample_left[0], sample_right[0]),
                            CrossoverDetectionMethod.TANGENTIAL_CANDIDATE,
                        )
                    )
        for root in _algebraic_gain_seeds(
            transfer_function,
            substitutions,
            samples[0][0],
            samples[-1][0],
        ):
            interval_left, interval_right = _containing_interval(root, samples)
            if abs(evaluator.at(root)[3]) <= _DB_TOL:
                delta = max(root * 1e-6, 1e-9)
                sign_change = (
                    evaluator.at(max(interval_left, root - delta))[3]
                    * evaluator.at(min(interval_right, root + delta))[3]
                    < 0
                )
                candidates.append(
                    (
                        root,
                        (interval_left, interval_right),
                        CrossoverDetectionMethod.BRACKETED_SIGN_CHANGE
                        if sign_change
                        else CrossoverDetectionMethod.TANGENTIAL_CANDIDATE,
                    )
                )
        return [
            _crossover(
                FrequencyCrossoverType.GAIN,
                omega,
                segment_index,
                interval,
                method,
                evaluator,
                unwrapped_hint=_phase_hint(samples, omega),
            )
            for omega, interval, method in candidates
            if _valid_gain(evaluator.at(omega))
        ]

    def _phase_crossovers(
        self,
        samples: tuple[tuple[float, float, float], ...],
        segment_index: int,
        evaluator: _Evaluator,
    ) -> list[FrequencyCrossover]:
        low = min(value[2] for value in samples)
        high = max(value[2] for value in samples)
        m_min = floor((-180.0 - high) / 360.0)
        m_max = floor((-180.0 - low) / 360.0)
        results: list[FrequencyCrossover] = []
        for branch in range(m_min, m_max + 1):
            target = -180.0 - 360.0 * branch
            candidates: list[tuple[float, tuple[float, float], CrossoverDetectionMethod]] = []
            for index, (omega, _, phase) in enumerate(samples):
                residual = phase - target
                if abs(residual) <= _GRID_TOL:
                    candidates.append((omega, (omega, omega), CrossoverDetectionMethod.GRID_HIT))
                if index + 1 < len(samples):
                    nxt = samples[index + 1]
                    next_residual = nxt[2] - target
                    if residual * next_residual < 0:
                        root = brentq(
                            lambda value, target=target: evaluator.phase_at(value, target) - target,
                            omega,
                            nxt[0],
                            xtol=1e-12,
                        )
                        candidates.append(
                            (root, (omega, nxt[0]), CrossoverDetectionMethod.BRACKETED_SIGN_CHANGE)
                        )
            for index in range(1, len(samples) - 1):
                left, middle, right = samples[index - 1], samples[index], samples[index + 1]
                if abs(middle[2] - target) < abs(left[2] - target) and abs(
                    middle[2] - target
                ) < abs(right[2] - target):
                    fit = minimize_scalar(
                        lambda value, target=target: (
                            (evaluator.phase_at(value, target) - target) ** 2
                        ),
                        bounds=(left[0], right[0]),
                        method="bounded",
                    )
                    if (
                        fit.success
                        and abs(evaluator.phase_at(float(fit.x), target) - target) <= _PHASE_TOL
                    ):
                        candidates.append(
                            (
                                float(fit.x),
                                (left[0], right[0]),
                                CrossoverDetectionMethod.TANGENTIAL_CANDIDATE,
                            )
                        )
            for omega, interval, method in candidates:
                values = evaluator.at(omega)
                phase = evaluator.phase_at(omega, target)
                if (
                    abs(phase - target) <= _PHASE_TOL
                    and abs(values[1]) <= _AXIS_TOL * max(1.0, values[2])
                    and values[0] < 0
                ):
                    results.append(
                        _crossover(
                            FrequencyCrossoverType.PHASE,
                            omega,
                            segment_index,
                            interval,
                            method,
                            evaluator,
                            branch,
                            target,
                        )
                    )
        return results


class _Evaluator:
    def __init__(
        self,
        transfer_function: ReducedTransferFunction,
        substitutions: ParameterSubstitutions,
        field: str,
    ) -> None:
        self._transfer_function = transfer_function
        self._substitutions = substitutions
        self._field = field
        self._analyzer = TransferFunctionFrequencyResponseAnalyzer()
        self._cache: dict[float, tuple[float, float, float, float, float]] = {}

    def at(self, omega: float) -> tuple[float, float, float, float, float]:
        key = float(f"{omega:.14g}")
        if key not in self._cache:
            rational = _rational(key)
            result = self._analyzer.analyze(
                self._transfer_function,
                FrequencySampleSet((rational,)),
                self._substitutions,
                field=self._field,
            )
            point = result.points[0]
            if (
                point.numerical_real is None
                or point.numerical_imaginary is None
                or point.numerical_magnitude is None
                or point.numerical_decibel is None
                or point.numerical_phase_degrees is None
            ):
                raise ValueError("A local crossover evaluation is not numerically defined.")
            self._cache[key] = (
                float(point.numerical_real),
                float(point.numerical_imaginary),
                float(point.numerical_magnitude),
                float(point.numerical_decibel.decimal_value or "nan"),
                float(point.numerical_phase_degrees),
            )
        return self._cache[key]

    def phase_at(self, omega: float, target: float) -> float:
        principal = self.at(omega)[4]
        return principal + 360.0 * round((target - principal) / 360.0)


def _rational(value: float) -> ExactRationalValue:
    fraction = Fraction(Decimal(format(value, ".14g")))
    return ExactRationalValue(fraction.numerator, fraction.denominator)


def _algebraic_gain_seeds(
    transfer_function: ReducedTransferFunction,
    substitutions: ParameterSubstitutions,
    lower: float,
    upper: float,
) -> tuple[float, ...]:
    """Return bounded candidate seeds; the frequency evaluator remains authoritative."""
    s = sp.Symbol(transfer_function.variable_name)
    omega = sp.Symbol("_omega", real=True)
    mapping = {
        sp.Symbol(item.parameter_name): sp.Rational(item.value.numerator, item.value.denominator)
        for item in substitutions.assignments
    }
    numerator = transfer_function.numerator.expression._as_sympy().subs(mapping)
    denominator = transfer_function.denominator.expression._as_sympy().subs(mapping)
    if numerator.free_symbols - {s} or denominator.free_symbols - {s}:
        return ()
    n_jw = sp.expand(numerator.subs(s, sp.I * omega))
    d_jw = sp.expand(denominator.subs(s, sp.I * omega))
    equation = sp.Poly(
        sp.expand(n_jw * sp.conjugate(n_jw) - d_jw * sp.conjugate(d_jw)),
        omega,
    )
    if equation.is_zero:
        return ()
    roots: list[float] = []
    for root in sp.nroots(equation, maxsteps=100):
        value = complex(root)
        if abs(value.imag) <= 1e-9 and lower <= value.real <= upper and value.real > 0:
            roots.append(float(value.real))
    return tuple(sorted(set(round(value, 12) for value in roots)))


def _all_algebraic_candidates_in_band(
    transfer_function: ReducedTransferFunction,
    substitutions: ParameterSubstitutions,
    lower: float,
    upper: float,
) -> bool:
    expressions = _specialized_frequency_expressions(transfer_function, substitutions)
    if expressions is None:
        return False
    omega, n_jw, d_jw = expressions
    equations = (
        sp.expand(n_jw * sp.conjugate(n_jw) - d_jw * sp.conjugate(d_jw)),
        sp.expand(sp.im(n_jw * sp.conjugate(d_jw))),
    )
    for equation in equations:
        polynomial = sp.Poly(equation, omega)
        if polynomial.is_zero:
            return False
        for root in sp.nroots(polynomial, maxsteps=100):
            value = complex(root)
            if abs(value.imag) <= 1e-9 and value.real > 0 and not (lower <= value.real <= upper):
                return False
    return True


def _specialized_frequency_expressions(
    transfer_function: ReducedTransferFunction,
    substitutions: ParameterSubstitutions,
) -> tuple[sp.Symbol, sp.Expr, sp.Expr] | None:
    s = sp.Symbol(transfer_function.variable_name)
    omega = sp.Symbol("_omega", real=True)
    mapping = {
        sp.Symbol(item.parameter_name): sp.Rational(item.value.numerator, item.value.denominator)
        for item in substitutions.assignments
    }
    numerator = transfer_function.numerator.expression._as_sympy().subs(mapping)
    denominator = transfer_function.denominator.expression._as_sympy().subs(mapping)
    if numerator.free_symbols - {s} or denominator.free_symbols - {s}:
        return None
    return (
        omega,
        sp.expand(numerator.subs(s, sp.I * omega)),
        sp.expand(denominator.subs(s, sp.I * omega)),
    )


def _containing_interval(
    omega: float,
    samples: tuple[tuple[float, float, float], ...],
) -> tuple[float, float]:
    for left, right in zip(samples, samples[1:], strict=False):
        if left[0] <= omega <= right[0]:
            return left[0], right[0]
    return omega, omega


def _phase_hint(
    samples: tuple[tuple[float, float, float], ...],
    omega: float,
) -> float:
    left, right = _containing_interval(omega, samples)
    left_phase = next(row[2] for row in samples if row[0] == left)
    right_phase = next(row[2] for row in samples if row[0] == right)
    if left == right:
        return left_phase
    fraction = (log10(omega) - log10(left)) / (log10(right) - log10(left))
    return left_phase + fraction * (right_phase - left_phase)


def _valid_gain(values: tuple[float, float, float, float, float]) -> bool:
    return abs(values[3]) <= _DB_TOL and abs(values[2] - 1.0) <= _MAG_TOL


def _crossover(
    kind: FrequencyCrossoverType,
    omega: float,
    segment: int,
    interval: tuple[float, float],
    method: CrossoverDetectionMethod,
    evaluator: _Evaluator,
    branch: int | None = None,
    target: float | None = None,
    unwrapped_hint: float | None = None,
) -> FrequencyCrossover:
    real, imag, magnitude, db, principal = evaluator.at(omega)
    phase_target = 0.0 if target is None else target
    if target is None and unwrapped_hint is None:
        unwrapped = principal
    else:
        phase_reference = target if target is not None else unwrapped_hint
        assert phase_reference is not None
        unwrapped = evaluator.phase_at(omega, phase_reference)
    residual = (
        max(abs(db), abs(magnitude - 1.0))
        if kind is FrequencyCrossoverType.GAIN
        else abs(unwrapped - phase_target)
    )
    probe = max(omega * 1e-5, 1e-8)
    lower = max(interval[0], omega - probe)
    upper = min(interval[1], omega + probe)
    fn: Callable[[float], float] = (
        (lambda value: evaluator.at(value)[3])
        if kind is FrequencyCrossoverType.GAIN
        else (lambda value: evaluator.phase_at(value, phase_target) - phase_target)
    )
    if method is CrossoverDetectionMethod.TANGENTIAL_CANDIDATE:
        direction = CrossoverDirection.TANGENTIAL
    elif lower < upper:
        delta = fn(upper) - fn(lower)
        direction = (
            CrossoverDirection.RISING
            if delta > 0
            else CrossoverDirection.FALLING
            if delta < 0
            else CrossoverDirection.NUMERICALLY_AMBIGUOUS
        )
    else:
        direction = CrossoverDirection.NUMERICALLY_AMBIGUOUS
    return FrequencyCrossover(
        kind,
        float(omega),
        segment,
        complex(real, imag),
        magnitude,
        db,
        principal,
        unwrapped,
        direction,
        method,
        float(residual),
        (float(interval[0]), float(interval[1])),
        NumericalQuality.VERIFIED
        if residual <= (_DB_TOL if kind is FrequencyCrossoverType.GAIN else _PHASE_TOL)
        else NumericalQuality.AMBIGUOUS,
        ("existing_bode_segment", "local_frequency_response_recheck"),
        branch,
        target,
    )


def _deduplicate(values: list[FrequencyCrossover]) -> list[FrequencyCrossover]:
    result: list[FrequencyCrossover] = []
    priority = {
        CrossoverDetectionMethod.GRID_HIT: 0,
        CrossoverDetectionMethod.BRACKETED_SIGN_CHANGE: 1,
        CrossoverDetectionMethod.TANGENTIAL_CANDIDATE: 2,
    }
    for value in sorted(values, key=lambda item: (item.frequency, priority[item.detection_method])):
        match = next(
            (
                index
                for index, old in enumerate(result)
                if old.segment_index == value.segment_index
                and old.crossover_type is value.crossover_type
                and old.phase_branch_index == value.phase_branch_index
                and abs(old.frequency - value.frequency) <= 1e-6 * max(1.0, value.frequency)
            ),
            None,
        )
        if match is None:
            result.append(value)
        elif priority[value.detection_method] < priority[result[match].detection_method] or (
            priority[value.detection_method] == priority[result[match].detection_method]
            and value.residual < result[match].residual
        ):
            result[match] = value
    return result


def _reserves(crossovers: FrequencyCrossoverAnalysis) -> StabilityReserveAnalysis:
    phase = tuple(
        StabilityReserve(
            StabilityReserveType.PHASE_MARGIN,
            item,
            float(180.0 + item.unwrapped_phase_degrees),
            "°",
            item.numerical_quality,
            ReserveInterpretationStatus.NEGATIVE
            if 180.0 + item.unwrapped_phase_degrees < 0
            else ReserveInterpretationStatus.FINITE,
        )
        for item in crossovers.gain_crossovers
    )
    gain_db = tuple(
        StabilityReserve(
            StabilityReserveType.GAIN_MARGIN_DB,
            item,
            float(-item.decibel),
            "dB",
            item.numerical_quality,
            ReserveInterpretationStatus.NEGATIVE
            if -item.decibel < 0
            else ReserveInterpretationStatus.FINITE,
        )
        for item in crossovers.phase_crossovers
    )
    gain_factor = tuple(
        StabilityReserve(
            StabilityReserveType.GAIN_MARGIN_FACTOR,
            item,
            float(10 ** (-item.decibel / 20.0)),
            "factor",
            item.numerical_quality,
            ReserveInterpretationStatus.FINITE,
        )
        for item in crossovers.phase_crossovers
    )
    if not phase:
        phase = (
            StabilityReserve(
                StabilityReserveType.PHASE_MARGIN,
                None,
                None,
                "°",
                NumericalQuality.VERIFIED,
                ReserveInterpretationStatus.NOT_DEFINED,
            ),
        )
    if not gain_db:
        interpretation = (
            ReserveInterpretationStatus.FORMALLY_UNBOUNDED
            if crossovers.completeness is BandCompletenessStatus.COMPLETE_IN_PROVEN_RANGE
            else ReserveInterpretationStatus.NOT_DETERMINED
        )
        gain_db = (
            StabilityReserve(
                StabilityReserveType.GAIN_MARGIN_DB,
                None,
                None,
                "dB",
                NumericalQuality.VERIFIED,
                interpretation,
            ),
        )
        gain_factor = (
            StabilityReserve(
                StabilityReserveType.GAIN_MARGIN_FACTOR,
                None,
                None,
                "factor",
                NumericalQuality.VERIFIED,
                interpretation,
            ),
        )
    return StabilityReserveAnalysis(
        phase,
        gain_db,
        gain_factor,
        len(crossovers.gain_crossovers) > 1 or len(crossovers.phase_crossovers) > 1,
        crossovers.completeness,
    )


__all__ = ["FrequencyReserveAnalyzer"]
