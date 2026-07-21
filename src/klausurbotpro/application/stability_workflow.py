"""Direct safe-input workflow for the Hurwitz stability workspace."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

import sympy as sp

from klausurbotpro.domain.expression import ExactExpression
from klausurbotpro.domain.hurwitz_analyzer import analyze_hurwitz
from klausurbotpro.domain.hurwitz_contracts import HurwitzAnalysisResult
from klausurbotpro.domain.parameter_core import canonicalize_characteristic_polynomial
from klausurbotpro.domain.parameter_core_contracts import (
    AnalysisTarget,
    AtomicParameterCondition,
    CancellationReport,
    CancellationStatus,
    CharacteristicPolynomialInput,
    ConditionOrigin,
    PolynomialRole,
    Relation,
    SourceProvenance,
)
from klausurbotpro.domain.routh_analyzer import analyze_routh
from klausurbotpro.domain.routh_contracts import RouthAnalysisResult
from klausurbotpro.parsing import ParserConfig, SafeExpressionParser

_RELATION_PATTERN = re.compile(r"(<=|>=|!=|=|<|>)")
_RELATIONS = {
    "=": Relation.EQ,
    "!=": Relation.NE,
    "<": Relation.LT,
    "<=": Relation.LE,
    ">": Relation.GT,
    ">=": Relation.GE,
}


class StabilityMethod(StrEnum):
    HURWITZ = "hurwitz"
    ROUTH = "routh"


@dataclass(frozen=True, slots=True)
class StabilityInputDraft:
    polynomial_text: str
    variable_name: str = "s"
    decision_parameters_text: str = ""
    assumptions_text: str = ""
    role: PolynomialRole = PolynomialRole.DIRECT_CHARACTERISTIC_POLYNOMIAL
    analysis_target: AnalysisTarget = AnalysisTarget.INTERNAL_CLOSED_LOOP_ASYMPTOTIC
    provenance_note: str = ""
    cancellation_note: str = ""
    method: StabilityMethod = StabilityMethod.HURWITZ


@dataclass(frozen=True, slots=True)
class StabilityWorkflowResult:
    analysis: HurwitzAnalysisResult | RouthAnalysisResult | None
    errors: tuple[str, ...] = ()


def run_stability_workflow(draft: StabilityInputDraft) -> StabilityWorkflowResult:
    """Parse a direct request without eval and run the vertical Hurwitz workflow."""
    variable = draft.variable_name.strip()
    parameters = tuple(
        item.strip() for item in draft.decision_parameters_text.split(",") if item.strip()
    )
    if (
        not variable.isidentifier()
        or len(parameters) > 2
        or any(not item.isidentifier() or item == variable for item in parameters)
        or len(set(parameters)) != len(parameters)
    ):
        return StabilityWorkflowResult(
            None, ("Variable oder Entscheidungsparameter sind ungültig.",)
        )
    allowed = frozenset((variable, *parameters))
    parser = SafeExpressionParser(ParserConfig(allowed_symbols=allowed))
    parsed = parser.parse(draft.polynomial_text, "polynomial")
    if not parsed.succeeded or parsed.value is None:
        return StabilityWorkflowResult(None, tuple(item.message for item in parsed.diagnostics))
    assumptions, errors = _parse_assumptions(draft.assumptions_text, parameters, parser)
    if errors:
        return StabilityWorkflowResult(None, errors)
    cancellation = None
    if draft.role is PolynomialRole.REDUCED_TRANSFER_DENOMINATOR:
        cancellation = CancellationReport(
            CancellationStatus.FACTORS_REMOVED
            if draft.cancellation_note.strip()
            else CancellationStatus.NONE,
            draft.cancellation_note.strip(),
        )
    value = CharacteristicPolynomialInput(
        parsed.value,
        variable,
        parameters,
        (),
        assumptions,
        (),
        draft.role,
        draft.analysis_target,
        SourceProvenance(
            "Direkteingabe", draft.provenance_note.strip(), draft.provenance_note.strip()
        ),
        cancellation,
    )
    canonical = canonicalize_characteristic_polynomial(value)
    analysis = (
        analyze_hurwitz(canonical)
        if draft.method is StabilityMethod.HURWITZ
        else analyze_routh(canonical)
    )
    return StabilityWorkflowResult(analysis)


def _parse_assumptions(
    text: str,
    parameters: tuple[str, ...],
    parser: SafeExpressionParser,
) -> tuple[tuple[AtomicParameterCondition, ...], tuple[str, ...]]:
    result: list[AtomicParameterCondition] = []
    errors: list[str] = []
    for line_number, raw in enumerate(re.split(r"[;\n]+", text), start=1):
        line = raw.strip()
        if not line:
            continue
        parts = _RELATION_PATTERN.split(line)
        if len(parts) not in (3, 5):
            errors.append(f"Annahme {line_number}: Relation nicht unterstützt.")
            continue
        for index in range(0, len(parts) - 2, 2):
            left = parser.parse(parts[index].strip(), "assumptions")
            right = parser.parse(parts[index + 2].strip(), "assumptions")
            if (
                not left.succeeded
                or left.value is None
                or not right.succeeded
                or right.value is None
            ):
                errors.append(f"Annahme {line_number}: Ausdruck ungültig.")
                continue
            expression = sp.expand(left.value._as_sympy() - right.value._as_sympy())
            result.append(
                AtomicParameterCondition(
                    ExactExpression._from_sympy(expression),
                    _RELATIONS[parts[index + 1]],
                    ConditionOrigin.USER_ASSUMPTION,
                    parameters,
                    line,
                )
            )
    return tuple(result), tuple(errors)


__all__ = [
    "AnalysisTarget",
    "PolynomialRole",
    "StabilityMethod",
    "StabilityInputDraft",
    "StabilityWorkflowResult",
    "run_stability_workflow",
]
