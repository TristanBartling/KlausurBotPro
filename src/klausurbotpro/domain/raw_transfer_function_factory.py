"""Defensive factory for validated, unreduced transfer functions."""

from __future__ import annotations

from dataclasses import dataclass
from keyword import iskeyword
from typing import NoReturn, cast

from klausurbotpro.domain._raw_expression_to_exact import RawExpressionToExact
from klausurbotpro.domain._raw_expression_validator import (
    RawExpressionValidator,
    RawTreeValidationError,
)
from klausurbotpro.domain._raw_rationalizer import (
    DivisorRecord,
    RawRationalizationError,
    RawRationalizer,
)
from klausurbotpro.domain._raw_transfer_conditions import (
    RawConditionLimitError,
    RawTransferConditionCollector,
)
from klausurbotpro.domain.diagnostics import (
    Diagnostic,
    DiagnosticCode,
    DiagnosticSeverity,
)
from klausurbotpro.domain.polynomial import Polynomial
from klausurbotpro.domain.polynomial_contracts import PolynomialLimits
from klausurbotpro.domain.polynomial_factory import PolynomialFactory
from klausurbotpro.domain.raw_algebraic_expression import RawAlgebraicExpression
from klausurbotpro.domain.raw_transfer_function import RawTransferFunction
from klausurbotpro.domain.raw_transfer_function_contracts import (
    RawTransferFunctionCreationResult,
    RawTransferFunctionLimits,
)
from klausurbotpro.domain.transfer_function_input import (
    CommonTransferFunctionInput,
    SeparatedTransferFunctionInput,
    TransferFunctionInput,
)

_RESOURCE_ERRORS = (MemoryError, RecursionError, OverflowError)
_DEFAULT_LIMITS = RawTransferFunctionLimits()
_DEFAULT_POLYNOMIAL_LIMITS = PolynomialLimits()


@dataclass(frozen=True, slots=True)
class _RawTransferFailure(Exception):
    code: DiagnosticCode
    message: str
    details: tuple[tuple[str, str], ...] = ()


class RawTransferFunctionFactory:
    """Build validated transfer functions from untrusted raw input contracts."""

    def __init__(
        self,
        *,
        expected_variable_name: str = "s",
        allowed_parameter_names: frozenset[str] = frozenset(),
        limits: RawTransferFunctionLimits = _DEFAULT_LIMITS,
        polynomial_limits: PolynomialLimits = _DEFAULT_POLYNOMIAL_LIMITS,
    ) -> None:
        if not _safe_name(expected_variable_name):
            raise ValueError("expected_variable_name must be a safe identifier.")
        if not isinstance(allowed_parameter_names, frozenset):
            raise TypeError("allowed_parameter_names must be a frozenset.")
        if any(not _safe_name(name) for name in allowed_parameter_names):
            raise ValueError("Every parameter name must be a safe identifier.")
        if expected_variable_name in allowed_parameter_names:
            raise ValueError("The main variable cannot also be a parameter.")
        if len(allowed_parameter_names) > limits.max_parameters:
            raise ValueError("allowed_parameter_names exceeds max_parameters.")
        self._variable_name = expected_variable_name
        self._parameters = frozenset(allowed_parameter_names)
        self._limits = limits
        self._polynomial_factory = PolynomialFactory(polynomial_limits)

    def create(
        self,
        input_value: TransferFunctionInput,
        *,
        field: str | None = None,
    ) -> RawTransferFunctionCreationResult:
        """Defensively validate, rationalize, and construct one raw value."""
        if type(input_value) not in (
            SeparatedTransferFunctionInput,
            CommonTransferFunctionInput,
        ):
            raise TypeError("A supported TransferFunctionInput is required.")
        try:
            return self._create(input_value, field=field)
        except RawTreeValidationError as failure:
            if failure.cyclic:
                code = DiagnosticCode.RAW_TRANSFER_CYCLIC_TREE
            elif failure.undeclared_symbol is not None:
                code = DiagnosticCode.RAW_TRANSFER_UNDECLARED_SYMBOL
            elif failure.limit_name is not None:
                code = DiagnosticCode.RAW_TRANSFER_LIMIT_EXCEEDED
            else:
                code = DiagnosticCode.RAW_TRANSFER_INVALID_TREE
            details = (
                (("limit", failure.limit_name),)
                if failure.limit_name is not None
                else (
                    (("symbol", failure.undeclared_symbol),)
                    if failure.undeclared_symbol is not None
                    else ()
                )
            )
            return self._failure(code, "Der rohe Ausdruck ist ungültig.", field, details)
        except RawRationalizationError as failure:
            return self._failure(
                DiagnosticCode.RAW_TRANSFER_LIMIT_EXCEEDED,
                "Die nicht kürzende Rationalisierung überschreitet ein Limit.",
                field,
                (("limit", failure.limit_name),),
            )
        except RawConditionLimitError as failure:
            return self._failure(
                DiagnosticCode.RAW_TRANSFER_LIMIT_EXCEEDED,
                "Die Anzahl strukturierter Bedingungen überschreitet ein Limit.",
                field,
                (("limit", failure.limit_name),),
            )
        except _RawTransferFailure as failure:
            return self._failure(
                failure.code,
                failure.message,
                field,
                failure.details,
            )
        except _RESOURCE_ERRORS as error:
            return self._failure(
                DiagnosticCode.RAW_TRANSFER_RESOURCE_LIMIT_EXCEEDED,
                "Die Raw-Transferfunktionsvalidierung überschreitet Ressourcen.",
                field,
                (("exception", type(error).__name__),),
            )

    def _create(
        self,
        input_value: TransferFunctionInput,
        *,
        field: str | None,
    ) -> RawTransferFunctionCreationResult:
        variable_name = self._safe_input_variable(input_value)
        if variable_name != self._variable_name:
            self._fail(
                DiagnosticCode.RAW_TRANSFER_VARIABLE_MISMATCH,
                "Die Eingabe verwendet nicht die erwartete Hauptvariable.",
                (("expected", self._variable_name), ("actual", variable_name)),
            )

        validator = RawExpressionValidator(
            variable_name=self._variable_name,
            allowed_parameter_names=self._parameters,
            limits=self._limits,
        )
        rationalizer = RawRationalizer(
            validator=validator,
            limits=self._limits,
        )
        if isinstance(input_value, CommonTransferFunctionInput):
            expression = validator.validate_and_snapshot(
                self._safe_tree(input_value, "expression")
            )
            snapshot: TransferFunctionInput = CommonTransferFunctionInput(
                expression=expression,
                variable_name=self._variable_name,
                allowed_symbol_names=self._parameters | {self._variable_name},
                original_text=self._safe_text(input_value, "original_text"),
                normalized_text=self._safe_text(input_value, "normalized_text"),
            )
            pair = rationalizer.rationalize(expression, origin="expression")
        else:
            numerator_tree = validator.validate_and_snapshot(
                self._safe_tree(input_value, "numerator")
            )
            denominator_tree = validator.validate_and_snapshot(
                self._safe_tree(input_value, "denominator")
            )
            snapshot = SeparatedTransferFunctionInput(
                numerator=numerator_tree,
                denominator=denominator_tree,
                variable_name=self._variable_name,
                allowed_symbol_names=self._parameters | {self._variable_name},
                original_numerator_text=self._safe_text(
                    input_value, "original_numerator_text"
                ),
                original_denominator_text=self._safe_text(
                    input_value, "original_denominator_text"
                ),
                normalized_numerator_text=self._safe_text(
                    input_value, "normalized_numerator_text"
                ),
                normalized_denominator_text=self._safe_text(
                    input_value, "normalized_denominator_text"
                ),
            )
            numerator_pair = rationalizer.rationalize(
                numerator_tree,
                origin="numerator",
            )
            denominator_pair = rationalizer.rationalize(
                denominator_tree,
                origin="denominator",
            )
            pair = rationalizer.combine_separated(
                numerator_pair,
                denominator_pair,
            )

        translator = RawExpressionToExact(
            symbol_names=self._parameters | {self._variable_name},
            limits=self._limits,
        )
        numerator_result = self._polynomial_factory.create(
            translator.translate(pair.numerator_tree),
            variable_name=self._variable_name,
            declared_parameter_names=self._parameters,
            field="numerator" if field is None else field,
        )
        if numerator_result.value is None:
            self._fail(
                DiagnosticCode.RAW_TRANSFER_NONPOLYNOMIAL_NUMERATOR,
                "Der rationalisierte Zähler ist kein unterstütztes Polynom.",
                _nested_diagnostic_details(numerator_result.diagnostics),
            )
        denominator_result = self._polynomial_factory.create(
            translator.translate(pair.denominator_tree),
            variable_name=self._variable_name,
            declared_parameter_names=self._parameters,
            field="denominator" if field is None else field,
        )
        if denominator_result.value is None:
            self._fail(
                DiagnosticCode.RAW_TRANSFER_NONPOLYNOMIAL_DENOMINATOR,
                "Der rationalisierte Nenner ist kein unterstütztes Polynom.",
                _nested_diagnostic_details(denominator_result.diagnostics),
            )
        numerator = numerator_result.value
        denominator = denominator_result.value
        assert numerator is not None and denominator is not None
        self._check_degree_limits(numerator, denominator)

        conditions = RawTransferConditionCollector(
            variable_name=self._variable_name,
            limits=self._limits,
        )
        diagnostics: list[Diagnostic] = []
        if denominator.is_zero:
            self._fail(
                DiagnosticCode.RAW_TRANSFER_ZERO_DENOMINATOR,
                "Der finale Nenner ist die Nullfunktion.",
            )
        for record in pair.divisor_records:
            divisor = self._polynomial_from_record(record, translator)
            if divisor.is_zero:
                self._fail(
                    DiagnosticCode.RAW_TRANSFER_ZERO_DIVISOR,
                    "Ein ursprünglicher Divisor ist die Nullfunktion.",
                    (("origin", record.origin),),
                )
            conditional = conditions.add(divisor, origin=record.origin)
            if conditional:
                diagnostics.append(
                    self._warning(
                        DiagnosticCode.RAW_TRANSFER_CONDITIONAL_DIVISOR,
                        "Ein ursprünglicher Divisor benötigt eine "
                        "Parameter-Voraussetzung.",
                        field,
                        (("origin", record.origin),),
                    )
                )

        final_conditional = conditions.add(
            denominator,
            origin="denominator:final",
        )
        if final_conditional:
            diagnostics.append(
                self._warning(
                    DiagnosticCode.RAW_TRANSFER_CONDITIONAL_DENOMINATOR,
                    "Der finale Nenner benötigt eine Parameter-Voraussetzung.",
                    field,
                )
            )

        normalized_prerequisites, normalized_exclusions = conditions.normalized()
        value = RawTransferFunction._create(
            variable_name=self._variable_name,
            numerator=numerator,
            denominator=denominator,
            input_snapshot=snapshot,
            prerequisites=normalized_prerequisites,
            domain_exclusions=normalized_exclusions,
        )
        unique_diagnostics = _deduplicate_diagnostics(
            (
                *numerator_result.diagnostics,
                *denominator_result.diagnostics,
                *diagnostics,
            )
        )
        return RawTransferFunctionCreationResult(value, unique_diagnostics)

    def _polynomial_from_record(
        self,
        record: DivisorRecord,
        translator: RawExpressionToExact,
    ) -> Polynomial:
        result = self._polynomial_factory.create(
            translator.translate(record.numerator_tree),
            variable_name=self._variable_name,
            declared_parameter_names=self._parameters,
            field=record.origin,
        )
        if result.value is None:
            self._fail(
                DiagnosticCode.RAW_TRANSFER_RATIONALIZATION_FAILED,
                "Ein ursprünglicher Divisor konnte nicht polynomial validiert werden.",
                _nested_diagnostic_details(result.diagnostics),
            )
        return result.value

    def _check_degree_limits(
        self,
        numerator: Polynomial,
        denominator: Polynomial,
    ) -> None:
        numerator_degree = numerator.degree_info.generic_degree
        denominator_degree = denominator.degree_info.generic_degree
        if (
            numerator_degree is not None
            and numerator_degree > self._limits.max_numerator_degree
        ):
            self._fail(
                DiagnosticCode.RAW_TRANSFER_LIMIT_EXCEEDED,
                "Der Zählergrad überschreitet das Raw-Limit.",
                (("limit", "max_numerator_degree"),),
            )
        if (
            denominator_degree is not None
            and denominator_degree > self._limits.max_denominator_degree
        ):
            self._fail(
                DiagnosticCode.RAW_TRANSFER_LIMIT_EXCEEDED,
                "Der Nennergrad überschreitet das Raw-Limit.",
                (("limit", "max_denominator_degree"),),
            )

    @staticmethod
    def _safe_input_variable(input_value: TransferFunctionInput) -> str:
        try:
            value = object.__getattribute__(input_value, "variable_name")
        except (AttributeError, TypeError) as error:
            raise RawTreeValidationError("invalid input metadata") from error
        if not _safe_name(value):
            raise RawTreeValidationError("invalid input variable")
        return cast(str, value)

    @staticmethod
    def _safe_tree(
        input_value: TransferFunctionInput,
        name: str,
    ) -> RawAlgebraicExpression:
        try:
            value = object.__getattribute__(input_value, name)
        except (AttributeError, TypeError) as error:
            raise RawTreeValidationError("invalid input tree field") from error
        return cast(RawAlgebraicExpression, value)

    @staticmethod
    def _safe_text(input_value: TransferFunctionInput, name: str) -> str:
        try:
            value = object.__getattribute__(input_value, name)
        except (AttributeError, TypeError) as error:
            raise RawTreeValidationError("invalid input metadata") from error
        if not isinstance(value, str):
            raise RawTreeValidationError("invalid input metadata")
        return value

    @staticmethod
    def _warning(
        code: DiagnosticCode,
        message: str,
        field: str | None,
        details: tuple[tuple[str, str], ...] = (),
    ) -> Diagnostic:
        return Diagnostic(
            DiagnosticSeverity.WARNING,
            code,
            message,
            field,
            details,
        )

    @staticmethod
    def _failure(
        code: DiagnosticCode,
        message: str,
        field: str | None,
        details: tuple[tuple[str, str], ...] = (),
    ) -> RawTransferFunctionCreationResult:
        return RawTransferFunctionCreationResult(
            None,
            (
                Diagnostic(
                    DiagnosticSeverity.ERROR,
                    code,
                    message,
                    field,
                    details,
                ),
            ),
        )

    @staticmethod
    def _fail(
        code: DiagnosticCode,
        message: str,
        details: tuple[tuple[str, str], ...] = (),
    ) -> NoReturn:
        raise _RawTransferFailure(code, message, details)


def _safe_name(value: object) -> bool:
    return (
        isinstance(value, str)
        and value.isidentifier()
        and not iskeyword(value)
        and not value.startswith("__")
        and not value.endswith("__")
    )


def _nested_diagnostic_details(
    diagnostics: tuple[Diagnostic, ...],
) -> tuple[tuple[str, str], ...]:
    return tuple(("cause", diagnostic.code.value) for diagnostic in diagnostics)


def _deduplicate_diagnostics(
    diagnostics: tuple[Diagnostic, ...],
) -> tuple[Diagnostic, ...]:
    unique = {
        (
            diagnostic.severity.value,
            diagnostic.code.value,
            diagnostic.field or "",
            diagnostic.technical_details,
        ): diagnostic
        for diagnostic in diagnostics
    }
    return tuple(unique[key] for key in sorted(unique))


__all__ = ["RawTransferFunctionFactory"]
