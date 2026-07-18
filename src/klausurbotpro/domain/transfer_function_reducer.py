"""Public facade for exact, semantics-preserving transfer-function reduction."""

from __future__ import annotations

from dataclasses import dataclass

import sympy as sp

from klausurbotpro.domain._exact_transfer_reduction import (
    ExactReductionFailure,
    ExactTransferReduction,
)
from klausurbotpro.domain._raw_transfer_conditions import (
    RawTransferConditionCollector,
)
from klausurbotpro.domain.diagnostics import (
    Diagnostic,
    DiagnosticCode,
    DiagnosticSeverity,
)
from klausurbotpro.domain.expression import ExactExpression
from klausurbotpro.domain.polynomial import Polynomial
from klausurbotpro.domain.polynomial_factory import PolynomialFactory
from klausurbotpro.domain.raw_transfer_function import RawTransferFunction
from klausurbotpro.domain.raw_transfer_function_contracts import (
    RawTransferFunctionLimits,
    TransferFunctionDomainExclusion,
    TransferFunctionPrerequisite,
)
from klausurbotpro.domain.reduced_transfer_function import (
    ReducedTransferFunction,
)
from klausurbotpro.domain.transfer_function_reduction_contracts import (
    TransferFunctionReductionLimits,
    TransferFunctionReductionReport,
    TransferFunctionReductionResult,
)

_RESOURCE_ERRORS = (MemoryError, RecursionError, OverflowError)
_DEFAULT_LIMITS = TransferFunctionReductionLimits()


@dataclass(frozen=True, slots=True)
class _InvalidRawValue(Exception):
    message: str


class TransferFunctionReducer:
    """Reduce validated raw transfer functions using bounded exact arithmetic."""

    def __init__(
        self,
        limits: TransferFunctionReductionLimits = _DEFAULT_LIMITS,
    ) -> None:
        self._limits = limits
        self._polynomial_factory = PolynomialFactory()

    def reduce(
        self,
        raw: RawTransferFunction,
        *,
        field: str | None = None,
    ) -> TransferFunctionReductionResult:
        """Return an exact reduced value while retaining the raw domain."""
        if not isinstance(raw, RawTransferFunction):
            raise TypeError("TransferFunctionReducer requires a RawTransferFunction.")
        try:
            self._validate_raw(raw)
            outcome = ExactTransferReduction(self._limits).reduce(raw)
            numerator = self._create_polynomial(
                outcome.numerator,
                raw,
                field or "numerator",
            )
            denominator = self._create_polynomial(
                outcome.denominator,
                raw,
                field or "denominator",
            )
            if denominator.is_zero:
                raise _InvalidRawValue("The reduced denominator is zero.")
            reduced = ReducedTransferFunction._create(
                variable_name=raw.variable_name,
                numerator=numerator,
                denominator=denominator,
                prerequisites=raw.prerequisites,
                domain_exclusions=raw.domain_exclusions,
            )
            diagnostics = (
                (
                    Diagnostic(
                        DiagnosticSeverity.WARNING,
                        DiagnosticCode.TRANSFER_REDUCTION_NORMALIZATION_SKIPPED,
                        "Eine symbolische Normierung wurde ohne "
                        "Nichtnull-Nachweis konservativ ausgelassen.",
                        field,
                    ),
                )
                if outcome.normalization_skipped
                else ()
            )
            return TransferFunctionReductionResult(
                raw=raw,
                reduced=reduced,
                report=TransferFunctionReductionReport(outcome.steps),
                diagnostics=diagnostics,
            )
        except _InvalidRawValue as failure:
            return self._failure(
                raw,
                DiagnosticCode.TRANSFER_REDUCTION_INVALID_RAW_VALUE,
                "Der Raw-Wert verletzt die erwarteten Domain-Invarianten.",
                field,
                (("reason", failure.message),),
            )
        except ExactReductionFailure as failure:
            return self._failure(
                raw,
                failure.code,
                failure.message,
                field,
                failure.details,
            )
        except _RESOURCE_ERRORS as error:
            return self._failure(
                raw,
                DiagnosticCode.TRANSFER_REDUCTION_RESOURCE_LIMIT_EXCEEDED,
                "Die Transferfunktionsreduktion überschreitet Ressourcen.",
                field,
                (("exception", type(error).__name__),),
            )

    def _create_polynomial(
        self,
        expression: sp.Expr,
        raw: RawTransferFunction,
        field: str,
    ) -> Polynomial:
        result = self._polynomial_factory.create(
            ExactExpression._from_sympy(expression),
            variable_name=raw.variable_name,
            declared_parameter_names=raw.used_parameter_names,
            field=field,
        )
        if result.value is None:
            details = ", ".join(item.code.value for item in result.diagnostics)
            raise ExactReductionFailure(
                DiagnosticCode.TRANSFER_REDUCTION_RESULT_INVALID,
                "Das reduzierte Ergebnis ist kein gültiges exaktes Polynom-Paar.",
                (("cause", details),),
            )
        return result.value

    def _validate_raw(self, raw: RawTransferFunction) -> None:
        if type(raw) is not RawTransferFunction:
            raise _InvalidRawValue("Subclasses are not accepted.")
        if (
            not isinstance(raw.variable_name, str)
            or not isinstance(raw.numerator, Polynomial)
            or not isinstance(raw.denominator, Polynomial)
        ):
            raise _InvalidRawValue("Core raw fields have invalid types.")
        if (
            raw.numerator.variable_name != raw.variable_name
            or raw.denominator.variable_name != raw.variable_name
        ):
            raise _InvalidRawValue("Polynomial variables do not match.")
        if raw.denominator.is_zero:
            raise _InvalidRawValue("The raw denominator is zero.")
        if raw.is_zero is not raw.numerator.is_zero:
            raise _InvalidRawValue("The zero flag is inconsistent.")
        if raw.numerator_conditions != raw.numerator.conditions:
            raise _InvalidRawValue("Numerator conditions are inconsistent.")
        if raw.denominator_conditions != raw.denominator.conditions:
            raise _InvalidRawValue("Denominator conditions are inconsistent.")
        if any(
            not isinstance(item, TransferFunctionPrerequisite)
            for item in raw.prerequisites
        ) or any(
            not isinstance(item, TransferFunctionDomainExclusion)
            for item in raw.domain_exclusions
        ):
            raise _InvalidRawValue("Domain conditions have invalid types.")
        expected_names = _used_parameter_names(raw)
        if raw.used_parameter_names != expected_names:
            raise _InvalidRawValue("Used parameter names are inconsistent.")
        if len(raw.used_parameter_names) > self._limits.max_parameters:
            raise ExactReductionFailure(
                DiagnosticCode.TRANSFER_REDUCTION_LIMIT_EXCEEDED,
                "Die exakte Transferfunktionsreduktion überschreitet ein Limit.",
                (("limit", "max_parameters"),),
            )
        self._revalidate_polynomial(raw.numerator, raw)
        self._revalidate_polynomial(raw.denominator, raw)
        for prerequisite in raw.prerequisites:
            for expression in prerequisite.expressions:
                result = self._polynomial_factory.create(
                    expression,
                    variable_name=raw.variable_name,
                    declared_parameter_names=raw.used_parameter_names,
                )
                if result.value is None or raw.variable_name in (
                    expression.symbol_names
                ):
                    raise _InvalidRawValue(
                        "A prerequisite expression is not a valid "
                        "parameter-only polynomial."
                    )
        for exclusion in raw.domain_exclusions:
            self._revalidate_polynomial(exclusion.polynomial, raw)

        collector = RawTransferConditionCollector(
            variable_name=raw.variable_name,
            limits=RawTransferFunctionLimits(),
        )
        collector.add(raw.denominator, origin="revalidation")
        required_prerequisites, required_exclusions = collector.normalized()
        if any(
            item not in raw.prerequisites for item in required_prerequisites
        ):
            raise _InvalidRawValue(
                "A final-denominator prerequisite is missing."
            )
        if any(item not in raw.domain_exclusions for item in required_exclusions):
            raise _InvalidRawValue(
                "The final-denominator domain exclusion is missing."
            )

    def _revalidate_polynomial(
        self,
        polynomial: Polynomial,
        raw: RawTransferFunction,
    ) -> None:
        result = self._polynomial_factory.create(
            polynomial.expression,
            variable_name=raw.variable_name,
            declared_parameter_names=raw.used_parameter_names,
        )
        if result.value is None or result.value != polynomial:
            raise _InvalidRawValue(
                "A polynomial does not match independent revalidation."
            )

    @staticmethod
    def _failure(
        raw: RawTransferFunction,
        code: DiagnosticCode,
        message: str,
        field: str | None,
        details: tuple[tuple[str, str], ...] = (),
    ) -> TransferFunctionReductionResult:
        return TransferFunctionReductionResult(
            raw=raw,
            reduced=None,
            report=None,
            diagnostics=(
                Diagnostic(
                    DiagnosticSeverity.ERROR,
                    code,
                    message,
                    field,
                    details,
                ),
            ),
        )


def _used_parameter_names(raw: RawTransferFunction) -> frozenset[str]:
    names = set(raw.numerator.used_parameter_names)
    names.update(raw.denominator.used_parameter_names)
    for prerequisite in raw.prerequisites:
        for expression in prerequisite.expressions:
            names.update(expression.symbol_names)
    for exclusion in raw.domain_exclusions:
        names.update(exclusion.polynomial.used_parameter_names)
    names.discard(raw.variable_name)
    return frozenset(names)


__all__ = ["TransferFunctionReducer"]
