"""Immutable public contracts for course-conform controller design."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from klausurbotpro.domain.parameter_substitutions import ExactRationalValue


class ControllerDesignMethod(StrEnum):
    P_PHASE_MARGIN = "p_phase_margin"
    ZIEGLER_NICHOLS_OPEN_LOOP = "ziegler_nichols_open_loop"
    ZIEGLER_NICHOLS_CLOSED_LOOP = "ziegler_nichols_closed_loop"
    COHEN_COON = "cohen_coon"


class ControllerType(StrEnum):
    P = "p"
    PI = "pi"
    PID = "pid"


class ControllerDesignStatus(StrEnum):
    COMPLETE = "complete"
    SELECTION_REQUIRED = "selection_required"
    FAILED = "failed"
    UNSUPPORTED = "unsupported"


class ControllerDesignCandidateStatus(StrEnum):
    TARGET_MET = "target_met"
    TARGET_CROSSING_MET_GLOBAL_MARGIN_NOT_MET = "target_crossing_met_global_margin_not_met"
    TARGET_NOT_MET = "target_not_met"


class ControllerValueProvenance(StrEnum):
    EXACT_RATIONAL = "exact_rational"
    NUMERIC_FREQUENCY_DESIGN = "numeric_frequency_design"


@dataclass(frozen=True, slots=True)
class ControllerFormulaStep:
    """One exam-ready formula step, independent of any UI renderer."""

    quantity: str
    general_plain: str
    substituted_plain: str
    exact_plain: str
    approximation_plain: str
    unit: str
    source: str
    general_latex: str
    substituted_latex: str
    exact_latex: str
    approximation_latex: str


@dataclass(frozen=True, slots=True)
class ControllerValidityStep:
    """A concrete applicability check with values and a decision."""

    label: str
    condition_plain: str
    substitution_plain: str
    passed: bool
    conclusion: str
    source: str
    condition_latex: str
    substitution_latex: str


@dataclass(frozen=True, slots=True)
class ControllerResultStep:
    """An exact result followed by its optional numerical projection."""

    symbol: str
    exact_plain: str
    approximation_plain: str
    unit: str
    quantity_kind: str
    exact_latex: str
    approximation_latex: str


@dataclass(frozen=True, slots=True)
class ControllerScalar:
    exact: ExactRationalValue | None
    numerical: str
    provenance: ControllerValueProvenance

    def __post_init__(self) -> None:
        if self.exact is not None and type(self.exact) is not ExactRationalValue:
            raise TypeError("exact must be ExactRationalValue or None.")
        if type(self.numerical) is not str or not self.numerical:
            raise ValueError("numerical must be non-empty text.")
        if type(self.provenance) is not ControllerValueProvenance:
            raise TypeError("provenance has an invalid type.")
        if (self.exact is None) != (
            self.provenance is ControllerValueProvenance.NUMERIC_FREQUENCY_DESIGN
        ):
            raise ValueError("Scalar exactness and provenance disagree.")


@dataclass(frozen=True, slots=True)
class ControllerParameters:
    controller_type: ControllerType
    k_p: ControllerScalar
    k_i: ControllerScalar
    k_d: ControllerScalar
    ideal_t_i: ControllerScalar | None
    ideal_t_d: ControllerScalar | None
    canonical_transfer_function: str
    parallel_latex: str
    ideal_latex: str
    forms_identical: bool

    def __post_init__(self) -> None:
        if type(self.controller_type) is not ControllerType:
            raise TypeError("controller_type has an invalid type.")
        for value in (self.k_p, self.k_i, self.k_d):
            if type(value) is not ControllerScalar:
                raise TypeError("Controller coefficients must be ControllerScalar values.")
        if self.controller_type is ControllerType.P and (
            self.ideal_t_i is not None or self.ideal_t_d is not None
        ):
            raise ValueError("A P controller has no ideal time parameters.")
        if self.controller_type is ControllerType.PI and self.ideal_t_d is not None:
            raise ValueError("A PI controller has no derivative time.")
        if type(self.forms_identical) is not bool:
            raise TypeError("forms_identical must be bool.")


@dataclass(frozen=True, slots=True)
class ControllerDesignControl:
    label: str
    passed: bool
    message: str


@dataclass(frozen=True, slots=True)
class ControllerDesignDiagnostic:
    code: str
    message: str


def exact_scalar(value: ExactRationalValue) -> ControllerScalar:
    return ControllerScalar(
        value,
        f"{value.numerator / value.denominator:.12g}",
        ControllerValueProvenance.EXACT_RATIONAL,
    )


__all__ = [
    "ControllerDesignControl",
    "ControllerDesignCandidateStatus",
    "ControllerDesignDiagnostic",
    "ControllerDesignMethod",
    "ControllerDesignStatus",
    "ControllerFormulaStep",
    "ControllerParameters",
    "ControllerResultStep",
    "ControllerScalar",
    "ControllerType",
    "ControllerValidityStep",
    "ControllerValueProvenance",
    "exact_scalar",
]
