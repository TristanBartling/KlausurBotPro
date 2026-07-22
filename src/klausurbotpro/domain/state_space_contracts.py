"""Immutable public contracts for the bounded SISO state-space bridge."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from klausurbotpro.domain.expression import ExactExpression
from klausurbotpro.domain.hurwitz_contracts import HurwitzAnalysisResult
from klausurbotpro.domain.time_domain_contracts import LinearOdeInput
from klausurbotpro.domain.transfer_function_reduction_contracts import (
    TransferFunctionReductionResult,
)


class StateSpaceTaskType(StrEnum):
    ODE_TO_CONTROLLABLE_CANONICAL = "ode_to_controllable_canonical"
    STATE_SPACE_TO_TRANSFER_FUNCTION = "state_space_to_transfer_function"


class StateSpaceStatus(StrEnum):
    SOLVED = "solved"
    INVALID_INPUT = "invalid_input"
    UNSUPPORTED = "unsupported"
    VERIFICATION_FAILED = "verification_failed"


@dataclass(frozen=True, slots=True)
class StateSpaceInputDraft:
    task_type: StateSpaceTaskType
    output_name: str = "y"
    input_name: str = "u"
    output_order: int = 2
    output_coefficient_texts: tuple[str, ...] = ()
    input_coefficient_texts: tuple[str, ...] = ()
    matrix_a_text: str = ""
    vector_b_text: str = ""
    vector_c_text: str = ""
    scalar_d_text: str = "0"
    decision_parameters_text: str = ""
    assumptions_text: str = ""
    provenance: str = "Direkteingabe Zustandsraum"


@dataclass(frozen=True, slots=True)
class ExactMatrix:
    row_count: int
    column_count: int
    entries: tuple[tuple[ExactExpression, ...], ...]
    canonical_text: str
    latex: str


@dataclass(frozen=True, slots=True)
class StateSpaceModel:
    matrix_a: ExactMatrix
    vector_b: ExactMatrix
    vector_c: ExactMatrix
    scalar_d: ExactExpression
    state_dimension: int
    state_names: tuple[str, ...]
    input_name: str
    output_name: str
    provenance: str
    status: StateSpaceStatus
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class StateSpaceCheck:
    name: str
    passed: bool
    explanation: str


@dataclass(frozen=True, slots=True)
class StateSpaceAnalysisResult:
    input_model: StateSpaceModel | None
    normalized_ode: LinearOdeInput | None
    state_definitions: tuple[str, ...]
    state_equations: tuple[str, ...]
    characteristic_polynomial: ExactExpression | None
    exact_eigenvalues: tuple[tuple[ExactExpression, int], ...]
    numerical_eigenvalues: tuple[str, ...]
    half_plane_counts: tuple[int, int, int] | None
    state_stability: str
    hurwitz_analysis: HurwitzAnalysisResult | None
    raw_transfer_function: ExactExpression | None
    reduced_transfer_function: ExactExpression | None
    transfer_reduction: TransferFunctionReductionResult | None
    transfer_details: tuple[str, ...]
    cancellation_report: str
    hidden_state_modes: tuple[ExactExpression, ...]
    checks: tuple[StateSpaceCheck, ...]
    worked_steps: tuple[str, ...]
    latex_source: str
    status: StateSpaceStatus
    diagnostics: tuple[str, ...] = ()

    @property
    def succeeded(self) -> bool:
        return self.status is StateSpaceStatus.SOLVED


__all__ = [
    "ExactMatrix",
    "StateSpaceAnalysisResult",
    "StateSpaceCheck",
    "StateSpaceInputDraft",
    "StateSpaceModel",
    "StateSpaceStatus",
    "StateSpaceTaskType",
]
