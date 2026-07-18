"""Internal bounded exact arithmetic for transfer-function reduction."""

from __future__ import annotations

from dataclasses import dataclass
from functools import reduce
from math import gcd, lcm
from typing import NoReturn

import sympy as sp
from sympy.polys.polyerrors import BasePolynomialError, ExactQuotientFailed

from klausurbotpro.domain.diagnostics import DiagnosticCode
from klausurbotpro.domain.expression import ExactExpression
from klausurbotpro.domain.raw_transfer_function import RawTransferFunction
from klausurbotpro.domain.raw_transfer_function_contracts import (
    TransferFunctionPrerequisite,
    TransferFunctionPrerequisiteKind,
)
from klausurbotpro.domain.transfer_function_reduction_contracts import (
    TransferFunctionReductionLimits,
    TransferFunctionReductionStep,
    TransferFunctionReductionStepKind,
)


@dataclass(frozen=True, slots=True)
class ExactReductionFailure(Exception):
    """Expected internal reduction failure translated by the public facade."""

    code: DiagnosticCode
    message: str
    details: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True, slots=True)
class ExactReductionOutcome:
    """Internal exact pair, ordered evidence, and conservative skip flag."""

    numerator: sp.Expr
    denominator: sp.Expr
    steps: tuple[TransferFunctionReductionStep, ...]
    normalization_skipped: bool = False


class ExactTransferReduction:
    """Perform bounded multivariate polynomial reduction over ``QQ``."""

    def __init__(self, limits: TransferFunctionReductionLimits) -> None:
        self._limits = limits

    def reduce(self, raw: RawTransferFunction) -> ExactReductionOutcome:
        """Reduce a defensively validated raw pair without changing its domain."""
        numerator = raw.numerator.expression._as_sympy()
        denominator = raw.denominator.expression._as_sympy()
        self._check_input_limits(raw, numerator, denominator)

        steps: list[TransferFunctionReductionStep] = []
        if raw.numerator.is_zero:
            self._append_step(
                steps,
                TransferFunctionReductionStepKind.REDUCE_ZERO_NUMERATOR,
                numerator,
                denominator,
                sp.Integer(0),
                sp.Integer(1),
            )
            return ExactReductionOutcome(
                sp.Integer(0),
                sp.Integer(1),
                tuple(steps),
            )

        numerator, denominator = self._clear_parameter_denominators(
            raw,
            numerator,
            denominator,
            steps,
        )
        parameters = sorted(
            (
                numerator.free_symbols | denominator.free_symbols
            )
            - {sp.Symbol(raw.variable_name)},
            key=lambda value: value.name,
        )
        variable = sp.Symbol(raw.variable_name)
        generators = (variable, *parameters)
        try:
            numerator_poly = sp.Poly(numerator, *generators, domain=sp.QQ)
            denominator_poly = sp.Poly(denominator, *generators, domain=sp.QQ)
        except BasePolynomialError as error:
            self._fail(
                DiagnosticCode.TRANSFER_REDUCTION_COMMON_FACTOR_FAILED,
                "Das Polynom-Paar konnte nicht multivariat dargestellt werden.",
                (("exception", type(error).__name__),),
            )
        self._check_multivariate_limits(numerator_poly, denominator_poly)

        common_numeric = _common_rational_content(
            numerator_poly,
            denominator_poly,
        )
        if common_numeric != 1:
            before_numerator = numerator
            before_denominator = denominator
            numerator = sp.expand(numerator / common_numeric)
            denominator = sp.expand(denominator / common_numeric)
            numerator_poly = sp.Poly(numerator, *generators, domain=sp.QQ)
            denominator_poly = sp.Poly(denominator, *generators, domain=sp.QQ)
            self._append_step(
                steps,
                TransferFunctionReductionStepKind.REMOVE_COMMON_NUMERIC_FACTOR,
                before_numerator,
                before_denominator,
                numerator,
                denominator,
                common_numeric,
            )

        try:
            common_factor_poly = sp.gcd(numerator_poly, denominator_poly)
        except BasePolynomialError as error:
            self._fail(
                DiagnosticCode.TRANSFER_REDUCTION_COMMON_FACTOR_FAILED,
                "Der exakte gemeinsame Polynomfaktor konnte nicht bestimmt werden.",
                (("exception", type(error).__name__),),
            )
        common_factor = common_factor_poly.as_expr()
        if (
            not common_factor_poly.is_zero
            and common_factor_poly.total_degree() > 0
        ):
            if _node_count(
                common_factor,
                self._limits.max_common_factor_nodes,
            ) > self._limits.max_common_factor_nodes:
                self._limit("max_common_factor_nodes")
            before_numerator = numerator
            before_denominator = denominator
            try:
                numerator_poly = numerator_poly.exquo(common_factor_poly)
                denominator_poly = denominator_poly.exquo(common_factor_poly)
            except ExactQuotientFailed as error:
                self._fail(
                    DiagnosticCode.TRANSFER_REDUCTION_EXACT_DIVISION_FAILED,
                    "Ein gemeinsamer Faktor ließ sich nicht exakt dividieren.",
                    (("exception", type(error).__name__),),
                )
            numerator = numerator_poly.as_expr()
            denominator = denominator_poly.as_expr()
            self._append_step(
                steps,
                TransferFunctionReductionStepKind.REMOVE_COMMON_POLYNOMIAL_FACTOR,
                before_numerator,
                before_denominator,
                numerator,
                denominator,
                common_factor,
            )

        denominator_poly = sp.Poly(denominator, *generators, domain=sp.QQ)
        if denominator_poly.LC() < 0:
            before_numerator = numerator
            before_denominator = denominator
            numerator = -numerator
            denominator = -denominator
            self._append_step(
                steps,
                TransferFunctionReductionStepKind.NORMALIZE_SIGN,
                before_numerator,
                before_denominator,
                numerator,
                denominator,
                sp.Integer(-1),
            )

        normalization_skipped = False
        scale = _leading_scale(denominator, variable, parameters)
        if scale.free_symbols:
            proof = _nonzero_proof(scale, raw.prerequisites)
            if proof is None:
                normalization_skipped = True
            elif scale != 1:
                before_numerator = numerator
                before_denominator = denominator
                numerator = sp.cancel(numerator / scale)
                denominator = sp.cancel(denominator / scale)
                self._append_step(
                    steps,
                    TransferFunctionReductionStepKind.NORMALIZE_SAFE_SYMBOLIC_SCALE,
                    before_numerator,
                    before_denominator,
                    numerator,
                    denominator,
                    scale,
                    (proof,),
                )

        self._check_result_limits(numerator, denominator)
        if not steps:
            self._append_step(
                steps,
                TransferFunctionReductionStepKind.NO_REDUCTION,
                numerator,
                denominator,
                numerator,
                denominator,
            )
        return ExactReductionOutcome(
            numerator,
            denominator,
            tuple(steps),
            normalization_skipped,
        )

    def _check_input_limits(
        self,
        raw: RawTransferFunction,
        numerator: sp.Expr,
        denominator: sp.Expr,
    ) -> None:
        if len(raw.used_parameter_names) > self._limits.max_parameters:
            self._limit("max_parameters")
        if (
            raw.numerator.structural_term_count
            + raw.denominator.structural_term_count
            > self._limits.max_input_terms
        ):
            self._limit("max_input_terms")
        for expression in (numerator, denominator):
            if _node_count(
                expression,
                self._limits.max_input_expression_nodes,
            ) > self._limits.max_input_expression_nodes:
                self._limit("max_input_expression_nodes")

    def _clear_parameter_denominators(
        self,
        raw: RawTransferFunction,
        numerator: sp.Expr,
        denominator: sp.Expr,
        steps: list[TransferFunctionReductionStep],
    ) -> tuple[sp.Expr, sp.Expr]:
        numerator_top, numerator_bottom = sp.fraction(sp.cancel(numerator))
        denominator_top, denominator_bottom = sp.fraction(sp.cancel(denominator))
        proofs: list[TransferFunctionPrerequisite] = []
        for value in (numerator_bottom, denominator_bottom):
            if value.free_symbols:
                proof = _nonzero_proof(value, raw.prerequisites)
                if proof is None:
                    self._fail(
                        DiagnosticCode.TRANSFER_REDUCTION_INVALID_RAW_VALUE,
                        "Eine Koeffizientendefinition ist nicht durch die "
                        "Raw-Voraussetzungen abgesichert.",
                        (("condition", f"{sp.sstr(value, order='lex')} != 0"),),
                    )
                if proof not in proofs:
                    proofs.append(proof)
        if numerator_bottom == 1 and denominator_bottom == 1:
            return numerator, denominator
        after_numerator = sp.expand(numerator_top * denominator_bottom)
        after_denominator = sp.expand(denominator_top * numerator_bottom)
        self._append_step(
            steps,
            TransferFunctionReductionStepKind.CLEAR_PARAMETER_DENOMINATORS,
            numerator,
            denominator,
            after_numerator,
            after_denominator,
            sp.expand(numerator_bottom * denominator_bottom),
            tuple(proofs),
        )
        return after_numerator, after_denominator

    def _check_multivariate_limits(
        self,
        numerator: sp.Poly,
        denominator: sp.Poly,
    ) -> None:
        for polynomial in (numerator, denominator):
            if polynomial.total_degree() > self._limits.max_multivariate_total_degree:
                self._limit("max_multivariate_total_degree")
            if len(polynomial.terms()) > self._limits.max_multivariate_terms:
                self._limit("max_multivariate_terms")
            for coefficient in polynomial.coeffs():
                rational = sp.Rational(coefficient)
                digits = max(
                    len(str(abs(int(rational.p)))),
                    len(str(abs(int(rational.q)))),
                )
                if digits > self._limits.max_coefficient_digits:
                    self._limit("max_coefficient_digits")

    def _check_result_limits(
        self,
        numerator: sp.Expr,
        denominator: sp.Expr,
    ) -> None:
        for expression in (numerator, denominator):
            if _node_count(
                expression,
                self._limits.max_result_nodes,
            ) > self._limits.max_result_nodes:
                self._limit("max_result_nodes")

    def _append_step(
        self,
        steps: list[TransferFunctionReductionStep],
        kind: TransferFunctionReductionStepKind,
        before_numerator: sp.Expr,
        before_denominator: sp.Expr,
        after_numerator: sp.Expr,
        after_denominator: sp.Expr,
        factor: sp.Expr | None = None,
        prerequisites_used: tuple[TransferFunctionPrerequisite, ...] = (),
    ) -> None:
        if len(steps) >= self._limits.max_reduction_steps:
            self._limit("max_reduction_steps")
        steps.append(
            TransferFunctionReductionStep(
                kind=kind,
                numerator_before=ExactExpression._from_sympy(before_numerator),
                denominator_before=ExactExpression._from_sympy(before_denominator),
                numerator_after=ExactExpression._from_sympy(after_numerator),
                denominator_after=ExactExpression._from_sympy(after_denominator),
                factor=(
                    None
                    if factor is None
                    else ExactExpression._from_sympy(factor)
                ),
                prerequisites_used=prerequisites_used,
            )
        )

    def _limit(self, name: str) -> NoReturn:
        self._fail(
            DiagnosticCode.TRANSFER_REDUCTION_LIMIT_EXCEEDED,
            "Die exakte Transferfunktionsreduktion überschreitet ein Limit.",
            (("limit", name),),
        )

    @staticmethod
    def _fail(
        code: DiagnosticCode,
        message: str,
        details: tuple[tuple[str, str], ...] = (),
    ) -> NoReturn:
        raise ExactReductionFailure(code, message, details)


def _node_count(expression: sp.Expr, cap: int) -> int:
    count = 0
    for _ in sp.preorder_traversal(expression):
        count += 1
        if count > cap:
            break
    return count


def _rational_content(polynomial: sp.Poly) -> sp.Rational:
    coefficients = tuple(sp.Rational(value) for value in polynomial.coeffs())
    numerator_gcd = reduce(gcd, (abs(int(value.p)) for value in coefficients))
    denominator_lcm = reduce(lcm, (int(value.q) for value in coefficients))
    return sp.Rational(numerator_gcd, denominator_lcm)


def _common_rational_content(
    numerator: sp.Poly,
    denominator: sp.Poly,
) -> sp.Rational:
    first = _rational_content(numerator)
    second = _rational_content(denominator)
    common_numerator = gcd(abs(int(first.p)), abs(int(second.p)))
    common_denominator = lcm(int(first.q), int(second.q))
    return sp.Rational(common_numerator, common_denominator)


def _leading_scale(
    denominator: sp.Expr,
    variable: sp.Symbol,
    parameters: list[sp.Symbol],
) -> sp.Expr:
    domain = sp.QQ if not parameters else sp.QQ.frac_field(*parameters)
    polynomial = sp.Poly(denominator, variable, domain=domain)
    return sp.cancel(domain.to_sympy(polynomial.LC()))


def _nonzero_proof(
    expression: sp.Expr,
    prerequisites: tuple[TransferFunctionPrerequisite, ...],
) -> TransferFunctionPrerequisite | None:
    target = _primitive_polynomial(expression)
    if target is None:
        return None
    for prerequisite in prerequisites:
        if (
            prerequisite.kind
            is not TransferFunctionPrerequisiteKind.EXPRESSION_NONZERO
        ):
            continue
        candidate = _primitive_polynomial(
            prerequisite.expressions[0]._as_sympy()
        )
        if candidate is None:
            continue
        generators = sorted(
            target.free_symbols | candidate.free_symbols,
            key=lambda value: value.name,
        )
        if not generators:
            if candidate.is_zero is False:
                return prerequisite
            continue
        try:
            target_poly = sp.Poly(target, *generators, domain=sp.QQ)
            candidate_poly = sp.Poly(candidate, *generators, domain=sp.QQ)
            if candidate_poly.rem(target_poly).is_zero:
                return prerequisite
        except BasePolynomialError:
            continue
    return None


def _primitive_polynomial(expression: sp.Expr) -> sp.Expr | None:
    numerator, denominator = sp.fraction(sp.cancel(expression))
    if denominator.free_symbols:
        return None
    _, primitive = numerator.as_content_primitive()
    if primitive.could_extract_minus_sign():
        primitive = -primitive
    return primitive


__all__ = [
    "ExactReductionFailure",
    "ExactReductionOutcome",
    "ExactTransferReduction",
]
