"""Exact contracts for the small standard-element Bode analysis."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from klausurbotpro.domain.diagnostics import Diagnostic
from klausurbotpro.domain.expression import ExactExpression
from klausurbotpro.domain.reduced_transfer_function import ReducedTransferFunction


class StandardElementBodeStatus(StrEnum):
    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"


class StandardElementUnsupportedReason(StrEnum):
    ZERO_TRANSFER_FUNCTION = "zero_transfer_function"
    ROOT_ANALYSIS_FAILED = "root_analysis_failed"
    SYMBOLIC_OR_UNCLASSIFIABLE_ROOT = "symbolic_or_unclassifiable_root"
    COMPLEX_ROOT = "complex_root"
    RIGHT_HALF_PLANE_ROOT = "right_half_plane_root"
    INCOMPLETE_RECONSTRUCTION = "incomplete_reconstruction"


class StandardElementFactorRole(StrEnum):
    ZERO = "zero"
    POLE = "pole"


@dataclass(frozen=True, slots=True)
class StandardElementFactor:
    role: StandardElementFactorRole
    root: ExactExpression
    corner_frequency: ExactExpression
    multiplicity: int

    def __post_init__(self) -> None:
        if type(self.role) is not StandardElementFactorRole:
            raise TypeError("role must be StandardElementFactorRole.")
        if type(self.root) is not ExactExpression:
            raise TypeError("root must be an ExactExpression.")
        if type(self.corner_frequency) is not ExactExpression:
            raise TypeError("corner_frequency must be an ExactExpression.")
        if type(self.multiplicity) is not int or self.multiplicity <= 0:
            raise ValueError("multiplicity must be a positive int.")


@dataclass(frozen=True, slots=True)
class StandardElementCornerEvent:
    corner_frequency: ExactExpression
    zero_multiplicity: int
    pole_multiplicity: int
    slope_change_db_per_decade: int
    slope_after_db_per_decade: int

    def __post_init__(self) -> None:
        if type(self.corner_frequency) is not ExactExpression:
            raise TypeError("corner_frequency must be an ExactExpression.")
        for name in (
            "zero_multiplicity",
            "pole_multiplicity",
            "slope_change_db_per_decade",
            "slope_after_db_per_decade",
        ):
            if type(getattr(self, name)) is not int:
                raise TypeError(f"{name} must be an int.")
        if self.zero_multiplicity < 0 or self.pole_multiplicity < 0:
            raise ValueError("Event multiplicities must be nonnegative.")
        if self.zero_multiplicity + self.pole_multiplicity == 0:
            raise ValueError("A corner event requires at least one factor.")
        expected_change = 20 * (
            self.zero_multiplicity - self.pole_multiplicity
        )
        if self.slope_change_db_per_decade != expected_change:
            raise ValueError("The event slope change contradicts its factors.")


@dataclass(frozen=True, slots=True, init=False)
class StandardElementBodeResult:
    reduced_transfer_function: ReducedTransferFunction
    status: StandardElementBodeStatus
    gain: ExactExpression | None
    origin_zero_multiplicity: int
    origin_pole_multiplicity: int
    zero_factors: tuple[StandardElementFactor, ...]
    pole_factors: tuple[StandardElementFactor, ...]
    corner_events: tuple[StandardElementCornerEvent, ...]
    initial_slope_db_per_decade: int | None
    reconstruction_verified: bool
    unsupported_reason: StandardElementUnsupportedReason | None
    diagnostics: tuple[Diagnostic, ...]

    def __new__(cls, *args: object, **kwargs: object) -> StandardElementBodeResult:
        raise TypeError("Standard-element Bode results are analyzer-controlled.")

    @classmethod
    def _create(
        cls,
        *,
        reduced_transfer_function: ReducedTransferFunction,
        status: StandardElementBodeStatus,
        gain: ExactExpression | None = None,
        origin_zero_multiplicity: int = 0,
        origin_pole_multiplicity: int = 0,
        zero_factors: tuple[StandardElementFactor, ...] = (),
        pole_factors: tuple[StandardElementFactor, ...] = (),
        corner_events: tuple[StandardElementCornerEvent, ...] = (),
        initial_slope_db_per_decade: int | None = None,
        reconstruction_verified: bool = False,
        unsupported_reason: StandardElementUnsupportedReason | None = None,
        diagnostics: tuple[Diagnostic, ...] = (),
    ) -> StandardElementBodeResult:
        instance = object.__new__(cls)
        for name, value in (
            ("reduced_transfer_function", reduced_transfer_function),
            ("status", status),
            ("gain", gain),
            ("origin_zero_multiplicity", origin_zero_multiplicity),
            ("origin_pole_multiplicity", origin_pole_multiplicity),
            ("zero_factors", zero_factors),
            ("pole_factors", pole_factors),
            ("corner_events", corner_events),
            ("initial_slope_db_per_decade", initial_slope_db_per_decade),
            ("reconstruction_verified", reconstruction_verified),
            ("unsupported_reason", unsupported_reason),
            ("diagnostics", diagnostics),
        ):
            object.__setattr__(instance, name, value)
        instance._validate_local()
        return instance

    def _validate_local(self) -> None:
        if type(self.reduced_transfer_function) is not ReducedTransferFunction:
            raise TypeError("A reduced transfer function is required.")
        if type(self.status) is not StandardElementBodeStatus:
            raise TypeError("status must be StandardElementBodeStatus.")
        for name in ("origin_zero_multiplicity", "origin_pole_multiplicity"):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise ValueError(f"{name} must be a nonnegative int.")
        if type(self.zero_factors) is not tuple or any(
            type(item) is not StandardElementFactor
            or item.role is not StandardElementFactorRole.ZERO
            for item in self.zero_factors
        ):
            raise TypeError("zero_factors must contain exact zero factors.")
        if type(self.pole_factors) is not tuple or any(
            type(item) is not StandardElementFactor
            or item.role is not StandardElementFactorRole.POLE
            for item in self.pole_factors
        ):
            raise TypeError("pole_factors must contain exact pole factors.")
        if type(self.corner_events) is not tuple or any(
            type(item) is not StandardElementCornerEvent
            for item in self.corner_events
        ):
            raise TypeError("corner_events must contain exact corner events.")
        if type(self.diagnostics) is not tuple or any(
            type(item) is not Diagnostic for item in self.diagnostics
        ):
            raise TypeError("diagnostics must be an exact Diagnostic tuple.")
        if type(self.reconstruction_verified) is not bool:
            raise TypeError("reconstruction_verified must be bool.")
        if self.status is StandardElementBodeStatus.SUPPORTED:
            if (
                type(self.gain) is not ExactExpression
                or type(self.initial_slope_db_per_decade) is not int
                or not self.reconstruction_verified
                or self.unsupported_reason is not None
                or self.diagnostics
            ):
                raise ValueError("A supported result requires a verified decomposition.")
            expected_initial = 20 * (
                self.origin_zero_multiplicity - self.origin_pole_multiplicity
            )
            if self.initial_slope_db_per_decade != expected_initial:
                raise ValueError("The initial slope contradicts the origin factors.")
            slope = expected_initial
            for event in self.corner_events:
                slope += event.slope_change_db_per_decade
                if event.slope_after_db_per_decade != slope:
                    raise ValueError("A corner-event slope is inconsistent.")
            return
        if type(self.unsupported_reason) is not StandardElementUnsupportedReason:
            raise ValueError("An unsupported result requires a structured reason.")
        if (
            self.gain is not None
            or self.origin_zero_multiplicity
            or self.origin_pole_multiplicity
            or self.zero_factors
            or self.pole_factors
            or self.corner_events
            or self.initial_slope_db_per_decade is not None
            or self.reconstruction_verified
            or len(self.diagnostics) != 1
        ):
            raise ValueError("An unsupported result must not expose a partial decomposition.")

    @property
    def supported(self) -> bool:
        return self.status is StandardElementBodeStatus.SUPPORTED


__all__ = [
    "StandardElementBodeResult",
    "StandardElementBodeStatus",
    "StandardElementCornerEvent",
    "StandardElementFactor",
    "StandardElementFactorRole",
    "StandardElementUnsupportedReason",
]
