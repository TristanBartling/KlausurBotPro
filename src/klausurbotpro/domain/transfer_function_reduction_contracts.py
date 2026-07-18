"""Public immutable contracts for exact transfer-function reduction."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

from klausurbotpro.domain.diagnostics import Diagnostic, DiagnosticSeverity
from klausurbotpro.domain.expression import ExactExpression
from klausurbotpro.domain.raw_transfer_function_contracts import (
    TransferFunctionPrerequisite,
)

if TYPE_CHECKING:
    from klausurbotpro.domain.raw_transfer_function import RawTransferFunction
    from klausurbotpro.domain.reduced_transfer_function import (
        ReducedTransferFunction,
    )


class TransferFunctionReductionStepKind(StrEnum):
    """Stable kinds of exact, semantics-preserving reduction steps."""

    CLEAR_PARAMETER_DENOMINATORS = "clear_parameter_denominators"
    REMOVE_COMMON_NUMERIC_FACTOR = "remove_common_numeric_factor"
    REMOVE_COMMON_POLYNOMIAL_FACTOR = "remove_common_polynomial_factor"
    NORMALIZE_SAFE_SYMBOLIC_SCALE = "normalize_safe_symbolic_scale"
    NORMALIZE_SIGN = "normalize_sign"
    REDUCE_ZERO_NUMERATOR = "reduce_zero_numerator"
    NO_REDUCTION = "no_reduction"


@dataclass(frozen=True, slots=True)
class TransferFunctionReductionStep:
    """One deterministic exact transformation of numerator and denominator."""

    kind: TransferFunctionReductionStepKind
    numerator_before: ExactExpression
    denominator_before: ExactExpression
    numerator_after: ExactExpression
    denominator_after: ExactExpression
    factor: ExactExpression | None = None
    prerequisites_used: tuple[TransferFunctionPrerequisite, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.kind, TransferFunctionReductionStepKind):
            raise TypeError("A reduction step requires a supported kind.")
        exact_values = (
            self.numerator_before,
            self.denominator_before,
            self.numerator_after,
            self.denominator_after,
        )
        if any(not isinstance(value, ExactExpression) for value in exact_values):
            raise TypeError("Reduction step values must be ExactExpression values.")
        if self.factor is not None and not isinstance(
            self.factor, ExactExpression
        ):
            raise TypeError("A reduction factor must be an ExactExpression.")
        prerequisites = tuple(self.prerequisites_used)
        if any(
            not isinstance(value, TransferFunctionPrerequisite)
            for value in prerequisites
        ):
            raise TypeError("Used prerequisites must be structured prerequisites.")
        object.__setattr__(self, "prerequisites_used", prerequisites)


@dataclass(frozen=True, slots=True)
class TransferFunctionReductionReport:
    """Ordered structured evidence for one reduction."""

    steps: tuple[TransferFunctionReductionStep, ...]

    def __post_init__(self) -> None:
        steps = tuple(self.steps)
        if not steps:
            raise ValueError("A reduction report requires at least one step.")
        if any(
            not isinstance(step, TransferFunctionReductionStep)
            for step in steps
        ):
            raise TypeError("A reduction report requires structured steps.")
        object.__setattr__(self, "steps", steps)

    @property
    def was_reduced(self) -> bool:
        """Return whether at least one mathematical transformation occurred."""
        return any(
            step.kind is not TransferFunctionReductionStepKind.NO_REDUCTION
            for step in self.steps
        )


@dataclass(frozen=True, slots=True)
class TransferFunctionReductionLimits:
    """Resource limits applied before and during multivariate reduction."""

    max_parameters: int = 16
    max_input_terms: int = 128
    max_input_expression_nodes: int = 1024
    max_multivariate_total_degree: int = 64
    max_multivariate_terms: int = 4096
    max_coefficient_digits: int = 256
    max_common_factor_nodes: int = 512
    max_result_nodes: int = 1024
    max_reduction_steps: int = 16

    def __post_init__(self) -> None:
        for name in self.__dataclass_fields__:
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive int.")


@dataclass(frozen=True, slots=True)
class TransferFunctionReductionResult:
    """A reduced value and report, or expected structured diagnostics."""

    raw: RawTransferFunction
    reduced: ReducedTransferFunction | None
    report: TransferFunctionReductionReport | None
    diagnostics: tuple[Diagnostic, ...] = ()

    def __post_init__(self) -> None:
        from klausurbotpro.domain.raw_transfer_function import RawTransferFunction
        from klausurbotpro.domain.reduced_transfer_function import (
            ReducedTransferFunction,
        )

        if not isinstance(self.raw, RawTransferFunction):
            raise TypeError("A reduction result requires a RawTransferFunction.")
        if self.reduced is not None and not isinstance(
            self.reduced, ReducedTransferFunction
        ):
            raise TypeError("A reduced value has an invalid type.")
        if self.report is not None and not isinstance(
            self.report, TransferFunctionReductionReport
        ):
            raise TypeError("A reduction report has an invalid type.")
        diagnostics = tuple(self.diagnostics)
        object.__setattr__(self, "diagnostics", diagnostics)
        has_error = any(
            diagnostic.severity is DiagnosticSeverity.ERROR
            for diagnostic in diagnostics
        )
        if self.reduced is not None and self.report is None:
            raise ValueError("A successful reduced value requires a report.")
        if self.report is not None and self.reduced is None:
            raise ValueError("A report requires a successful reduced value.")
        if (self.reduced is None or self.report is None) and not has_error:
            raise ValueError("A failed reduction result requires an error.")
        if self.reduced is not None and has_error:
            raise ValueError("A successful reduction cannot contain an error.")

    @property
    def succeeded(self) -> bool:
        """Return whether exact reduction produced a value."""
        return self.reduced is not None


__all__ = [
    "TransferFunctionReductionLimits",
    "TransferFunctionReductionReport",
    "TransferFunctionReductionResult",
    "TransferFunctionReductionStep",
    "TransferFunctionReductionStepKind",
]
