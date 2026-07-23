"""Exact standard-element decomposition for the deliberately small Bode MVP."""

from __future__ import annotations

from dataclasses import dataclass
from functools import cmp_to_key

import sympy as sp

from klausurbotpro.domain._exact_polynomial_root_solver import exact_root_as_sympy
from klausurbotpro.domain.diagnostics import Diagnostic, DiagnosticCode, DiagnosticSeverity
from klausurbotpro.domain.expression import ExactExpression
from klausurbotpro.domain.reduced_transfer_function import ReducedTransferFunction
from klausurbotpro.domain.root_analysis_contracts import (
    PolynomialRootAnalysis,
    PolynomialRootStatus,
    RootAnalysisLimits,
)
from klausurbotpro.domain.standard_element_bode_contracts import (
    StandardElementBodeResult,
    StandardElementBodeStatus,
    StandardElementCornerEvent,
    StandardElementFactor,
    StandardElementFactorKind,
    StandardElementFactorRole,
    StandardElementUnsupportedReason,
)
from klausurbotpro.domain.transfer_function_root_analyzer import TransferFunctionRootAnalyzer

_DEFAULT_LIMITS = RootAnalysisLimits()
_RESOURCE_ERRORS = (MemoryError, RecursionError, OverflowError)


class _UnsupportedDecomposition(Exception):
    def __init__(
        self,
        reason: StandardElementUnsupportedReason,
        message: str,
    ) -> None:
        super().__init__(message)
        self.reason = reason
        self.message = message


@dataclass(slots=True)
class _EventAccumulator:
    omega: sp.Expr
    zero_multiplicity: int = 0
    pole_multiplicity: int = 0


class StandardElementBodeAnalyzer:
    """Recognize primitive real factors and safe stable denominator PT2 factors."""

    def __init__(self, limits: RootAnalysisLimits = _DEFAULT_LIMITS) -> None:
        if type(limits) is not RootAnalysisLimits:
            raise TypeError("limits must be RootAnalysisLimits.")
        self._limits = limits

    def analyze(
        self,
        reduced: ReducedTransferFunction,
        *,
        field: str | None = None,
    ) -> StandardElementBodeResult:
        if type(reduced) is not ReducedTransferFunction:
            raise TypeError("reduced must be ReducedTransferFunction.")
        if field is not None and type(field) is not str:
            raise TypeError("field must be a string or None.")
        try:
            return self._analyze(reduced, field=field)
        except _UnsupportedDecomposition as unsupported:
            return self._unsupported(
                reduced,
                unsupported.reason,
                unsupported.message,
                field,
            )
        except _RESOURCE_ERRORS as error:
            return self._unsupported(
                reduced,
                StandardElementUnsupportedReason.ROOT_ANALYSIS_FAILED,
                "Die Standardgliederanalyse wurde wegen einer Ressourcengrenze "
                "nicht unterst\u00fctzt.",
                field,
                details=(("exception", type(error).__name__),),
            )

    def _analyze(
        self,
        reduced: ReducedTransferFunction,
        *,
        field: str | None,
    ) -> StandardElementBodeResult:
        if reduced.numerator.is_zero:
            raise _UnsupportedDecomposition(
                StandardElementUnsupportedReason.ZERO_TRANSFER_FUNCTION,
                "Die identisch verschwindende \u00dcbertragungsfunktion wird vom "
                "Standardglieder-MVP nicht unterst\u00fctzt.",
            )
        if reduced.used_parameter_names:
            raise _UnsupportedDecomposition(
                StandardElementUnsupportedReason.SYMBOLIC_OR_UNCLASSIFIABLE_ROOT,
                "Die Standardgliederanalyse erfordert eine parameterfreie, exakt "
                "klassifizierbare reduzierte \u00dcbertragungsfunktion.",
            )
        roots = TransferFunctionRootAnalyzer(self._limits).analyze(
            reduced,
            field=field,
        )
        if not roots.succeeded or roots.reduced_zeros is None or roots.reduced_poles is None:
            raise _UnsupportedDecomposition(
                StandardElementUnsupportedReason.ROOT_ANALYSIS_FAILED,
                "Die Pole und Nullstellen konnten nicht vollst\u00e4ndig exakt bestimmt werden.",
            )
        origin_zeros, zero_factors = self._classify_roots(
            roots.reduced_zeros,
            StandardElementFactorRole.ZERO,
        )
        origin_poles, pole_factors = self._classify_roots(
            roots.reduced_poles,
            StandardElementFactorRole.POLE,
        )
        variable = sp.Symbol(reduced.variable_name)
        source = sp.cancel(
            reduced.numerator.expression._as_sympy()
            / reduced.denominator.expression._as_sympy()
        )
        normalized = variable ** (origin_zeros - origin_poles)
        for factor in zero_factors:
            normalized *= (
                1 + variable / factor.corner_frequency._as_sympy()
            ) ** factor.multiplicity
        for factor in pole_factors:
            omega = factor.corner_frequency._as_sympy()
            if factor.kind is StandardElementFactorKind.PT2:
                assert factor.damping_ratio is not None
                damping = factor.damping_ratio._as_sympy()
                normalized /= (
                    1 + 2 * damping * variable / omega + (variable / omega) ** 2
                ) ** factor.multiplicity
            else:
                normalized /= (1 + variable / omega) ** factor.multiplicity
        gain = sp.cancel(source / normalized)
        if variable in gain.free_symbols or gain.is_real is not True or gain.is_zero is True:
            raise _UnsupportedDecomposition(
                StandardElementUnsupportedReason.INCOMPLETE_RECONSTRUCTION,
                "Der Gesamtfaktor K konnte nicht exakt und reell bestimmt werden.",
            )
        reconstructed = sp.cancel(gain * normalized)
        if sp.cancel(sp.together(reconstructed - source)) != 0:
            raise _UnsupportedDecomposition(
                StandardElementUnsupportedReason.INCOMPLETE_RECONSTRUCTION,
                "Die erkannte Faktorisierung rekonstruiert G_reduziert(s) nicht exakt.",
            )
        initial_slope = 20 * (origin_zeros - origin_poles)
        events = self._corner_events(zero_factors, pole_factors, initial_slope)
        final_slope = initial_slope + sum(
            event.slope_change_db_per_decade for event in events
        )
        numerator_degree = reduced.numerator.degree_info.generic_degree
        denominator_degree = reduced.denominator.degree_info.generic_degree
        if (
            numerator_degree is None
            or denominator_degree is None
            or final_slope != 20 * (numerator_degree - denominator_degree)
        ):
            raise _UnsupportedDecomposition(
                StandardElementUnsupportedReason.INCOMPLETE_RECONSTRUCTION,
                "Die Hochfrequenzsteigung widerspricht dem Relativgrad.",
            )
        return StandardElementBodeResult._create(
            reduced_transfer_function=reduced,
            status=StandardElementBodeStatus.SUPPORTED,
            gain=ExactExpression._from_sympy(gain),
            origin_zero_multiplicity=origin_zeros,
            origin_pole_multiplicity=origin_poles,
            zero_factors=zero_factors,
            pole_factors=pole_factors,
            corner_events=events,
            initial_slope_db_per_decade=initial_slope,
            reconstruction_verified=True,
        )

    @classmethod
    def _classify_roots(
        cls,
        analysis: PolynomialRootAnalysis,
        role: StandardElementFactorRole,
    ) -> tuple[int, tuple[StandardElementFactor, ...]]:
        if analysis.status is PolynomialRootStatus.CONSTANT_NONZERO:
            return 0, ()
        if analysis.status is not PolynomialRootStatus.COMPLETE:
            raise _UnsupportedDecomposition(
                StandardElementUnsupportedReason.SYMBOLIC_OR_UNCLASSIFIABLE_ROOT,
                "Mindestens eine Pol- oder Nullstelle ist nicht exakt klassifizierbar.",
            )
        origin_multiplicity = 0
        factors: list[StandardElementFactor] = []
        occurrences = list(analysis.roots)
        consumed: set[int] = set()
        for index, occurrence in enumerate(occurrences):
            if index in consumed:
                continue
            root = exact_root_as_sympy(occurrence.value)
            if root.is_real is False:
                if role is StandardElementFactorRole.ZERO:
                    raise _UnsupportedDecomposition(
                        StandardElementUnsupportedReason.COMPLEX_ROOT,
                        "Ein komplexes Nullstellenpaar wird vom "
                        "Standardglieder-MVP nicht unterstützt.",
                    )
                partner_index = next(
                    (
                        other_index
                        for other_index, other in enumerate(occurrences)
                        if other_index != index
                        and other_index not in consumed
                        and other.multiplicity == occurrence.multiplicity
                        and cls._exactly_equal(
                            exact_root_as_sympy(other.value), sp.conjugate(root)
                        )
                    ),
                    None,
                )
                if partner_index is None:
                    raise _UnsupportedDecomposition(
                        StandardElementUnsupportedReason.COMPLEX_ROOT,
                        "Das komplexe Polpaar ist nicht sicher konjugiert klassifizierbar.",
                    )
                real_part = sp.re(root)
                omega = sp.sqrt(sp.simplify(root * sp.conjugate(root)))
                damping = sp.simplify(-real_part / omega)
                if (
                    real_part.is_negative is not True
                    or omega.is_positive is not True
                    or damping.is_positive is not True
                    or damping.is_real is not True
                ):
                    raise _UnsupportedDecomposition(
                        StandardElementUnsupportedReason.RIGHT_HALF_PLANE_ROOT,
                        "Das quadratische Polpaar ist kein sicher stabiles PT2-Glied.",
                    )
                consumed.add(partner_index)
                factors.append(
                    StandardElementFactor(
                        role,
                        ExactExpression._from_sympy(root),
                        ExactExpression._from_sympy(omega),
                        occurrence.multiplicity,
                        StandardElementFactorKind.PT2,
                        ExactExpression._from_sympy(damping),
                    )
                )
                continue
            if root.is_real is not True:
                raise _UnsupportedDecomposition(
                    StandardElementUnsupportedReason.SYMBOLIC_OR_UNCLASSIFIABLE_ROOT,
                    "Mindestens eine Pol- oder Nullstelle ist nicht exakt reell klassifizierbar.",
                )
            if root.is_zero is True:
                origin_multiplicity += occurrence.multiplicity
                continue
            if root.is_positive is True:
                kind = "Nullstelle" if role is StandardElementFactorRole.ZERO else "Polstelle"
                raise _UnsupportedDecomposition(
                    StandardElementUnsupportedReason.RIGHT_HALF_PLANE_ROOT,
                    f"Eine RHP-{kind} wird vom Standardglieder-MVP nicht unterst\u00fctzt.",
                )
            if root.is_negative is not True:
                raise _UnsupportedDecomposition(
                    StandardElementUnsupportedReason.SYMBOLIC_OR_UNCLASSIFIABLE_ROOT,
                    "Mindestens eine Pol- oder Nullstelle ist nicht exakt als "
                    "LHP-Lage best\u00e4tigt.",
                )
            omega = -root
            factors.append(
                StandardElementFactor(
                    role,
                    ExactExpression._from_sympy(root),
                    ExactExpression._from_sympy(omega),
                    occurrence.multiplicity,
                )
            )
        factors.sort(
            key=cmp_to_key(
                lambda left, right: cls._compare_frequencies(
                    left.corner_frequency._as_sympy(),
                    right.corner_frequency._as_sympy(),
                )
            )
        )
        return origin_multiplicity, tuple(factors)

    @classmethod
    def _corner_events(
        cls,
        zero_factors: tuple[StandardElementFactor, ...],
        pole_factors: tuple[StandardElementFactor, ...],
        initial_slope: int,
    ) -> tuple[StandardElementCornerEvent, ...]:
        accumulators: list[_EventAccumulator] = []
        for factor in (*zero_factors, *pole_factors):
            omega = factor.corner_frequency._as_sympy()
            accumulator = next(
                (
                    item
                    for item in accumulators
                    if cls._exactly_equal(item.omega, omega)
                ),
                None,
            )
            if accumulator is None:
                accumulator = _EventAccumulator(omega)
                accumulators.append(accumulator)
            if factor.role is StandardElementFactorRole.ZERO:
                accumulator.zero_multiplicity += factor.multiplicity
            else:
                order = 2 if factor.kind is StandardElementFactorKind.PT2 else 1
                accumulator.pole_multiplicity += order * factor.multiplicity
        accumulators.sort(
            key=cmp_to_key(
                lambda left, right: cls._compare_frequencies(
                    left.omega,
                    right.omega,
                )
            )
        )
        events: list[StandardElementCornerEvent] = []
        slope = initial_slope
        for item in accumulators:
            change = 20 * (item.zero_multiplicity - item.pole_multiplicity)
            slope += change
            events.append(
                StandardElementCornerEvent(
                    ExactExpression._from_sympy(item.omega),
                    item.zero_multiplicity,
                    item.pole_multiplicity,
                    change,
                    slope,
                )
            )
        return tuple(events)

    @staticmethod
    def _exactly_equal(left: sp.Expr, right: sp.Expr) -> bool:
        return bool(sp.cancel(sp.together(left - right)) == 0)

    @classmethod
    def _compare_frequencies(cls, left: sp.Expr, right: sp.Expr) -> int:
        if cls._exactly_equal(left, right):
            return 0
        difference = sp.simplify(left - right)
        if difference.is_negative is True:
            return -1
        if difference.is_positive is True:
            return 1
        less = sp.StrictLessThan(left, right)
        if less is sp.true:
            return -1
        if less is sp.false:
            return 1
        raise _UnsupportedDecomposition(
            StandardElementUnsupportedReason.SYMBOLIC_OR_UNCLASSIFIABLE_ROOT,
            "Knickfrequenzen konnten nicht exakt sortiert werden.",
        )

    @staticmethod
    def _unsupported(
        reduced: ReducedTransferFunction,
        reason: StandardElementUnsupportedReason,
        message: str,
        field: str | None,
        *,
        details: tuple[tuple[str, str], ...] = (),
    ) -> StandardElementBodeResult:
        diagnostic = Diagnostic(
            DiagnosticSeverity.WARNING,
            DiagnosticCode.STANDARD_ELEMENT_BODE_UNSUPPORTED,
            message,
            field,
            (("reason", reason.value), *details),
        )
        return StandardElementBodeResult._create(
            reduced_transfer_function=reduced,
            status=StandardElementBodeStatus.UNSUPPORTED,
            unsupported_reason=reason,
            diagnostics=(diagnostic,),
        )


__all__ = ["StandardElementBodeAnalyzer"]
