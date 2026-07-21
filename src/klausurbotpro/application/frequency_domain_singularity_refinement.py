"""Exact one-round sampling refinement around observed Bode singularities."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from functools import cmp_to_key
from math import gcd

from klausurbotpro.application._frequency_domain_workflow_validation import (
    validate_frequency_domain_workflow_result,
)
from klausurbotpro.application.frequency_domain_workflow_contracts import (
    FrequencyDomainWorkflowLimits,
    FrequencyDomainWorkflowMode,
    FrequencyDomainWorkflowRequest,
    FrequencyDomainWorkflowResult,
)
from klausurbotpro.domain import (
    ExactRationalValue,
    FrequencyResponsePointStatus,
    LogFrequencyGridRequest,
)


class FrequencyDomainSingularityRefinementReason(StrEnum):
    """Structured reason why no optional refinement request was produced."""

    NOT_APPLICABLE = "not_applicable"
    NO_SINGULARITY = "no_singularity"
    NO_ELIGIBLE_FREQUENCIES = "no_eligible_frequencies"
    LIMIT_EXCEEDED = "limit_exceeded"


@dataclass(frozen=True, slots=True)
class FrequencyDomainSingularityRefinementPlan:
    """One immutable optional follow-up request."""

    refined_request: FrequencyDomainWorkflowRequest | None
    added_frequencies: tuple[ExactRationalValue, ...] = ()
    reason: FrequencyDomainSingularityRefinementReason | None = None
    message: str = ""

    def __post_init__(self) -> None:
        if self.refined_request is not None and (
            type(self.refined_request) is not FrequencyDomainWorkflowRequest
        ):
            raise TypeError("refined_request has an invalid type.")
        if type(self.added_frequencies) is not tuple or any(
            type(value) is not ExactRationalValue
            for value in self.added_frequencies
        ):
            raise TypeError("added_frequencies must contain exact rationals.")
        if self.reason is not None and (
            type(self.reason) is not FrequencyDomainSingularityRefinementReason
        ):
            raise TypeError("reason has an invalid type.")
        if type(self.message) is not str:
            raise TypeError("message must be a string.")
        if self.refined_request is None:
            if self.added_frequencies or self.reason is None or not self.message:
                raise ValueError("A skipped refinement requires one reason.")
        elif not self.added_frequencies or self.reason is not None or self.message:
            raise ValueError("A refinement request requires only added frequencies.")


class FrequencyDomainSingularityRefinementPlanner:
    """Plan one bounded exact follow-up run from validated Bode points."""

    def plan(
        self,
        result: FrequencyDomainWorkflowResult,
        limits: FrequencyDomainWorkflowLimits,
    ) -> FrequencyDomainSingularityRefinementPlan:
        if type(result) is not FrequencyDomainWorkflowResult:
            raise TypeError("result must be FrequencyDomainWorkflowResult.")
        if type(limits) is not FrequencyDomainWorkflowLimits:
            raise TypeError("limits must be FrequencyDomainWorkflowLimits.")
        validate_frequency_domain_workflow_result(result, limits)
        request = result.request
        if (
            request is None
            or request.mode is not FrequencyDomainWorkflowMode.BODE
            or request.grid_request is None
            or result.grid_result is None
            or result.bode_data_result is None
        ):
            return _skipped(
                FrequencyDomainSingularityRefinementReason.NOT_APPLICABLE,
                "Für diesen Lauf ist keine Bode-Verfeinerung anwendbar.",
            )

        singularities = tuple(
            point.evaluation_frequency
            for point in result.bode_data_result.points
            if point.frequency_response_point.status
            is FrequencyResponsePointStatus.SINGULAR
            and point.evaluation_frequency.numerator > 0
        )
        if not singularities:
            return _skipped(
                FrequencyDomainSingularityRefinementReason.NO_SINGULARITY,
                "Im vorhandenen Raster wurde keine Singularität getroffen.",
            )

        grid_request = request.grid_request
        existing_keys = {
            _key(point.evaluation_frequency)
            for point in result.grid_result.points
        }
        existing_keys.update(
            _key(value) for value in grid_request.explicit_frequencies
        )
        candidates: dict[tuple[int, int], ExactRationalValue] = {}
        for singularity in singularities:
            for numerator in (99, 101):
                candidate = _scaled(singularity, numerator, 100)
                candidate_key = _key(candidate)
                if (
                    _within(
                        candidate,
                        grid_request.omega_min,
                        grid_request.omega_max,
                    )
                    and candidate_key not in existing_keys
                ):
                    candidates[candidate_key] = candidate
        added = tuple(
            sorted(candidates.values(), key=cmp_to_key(_compare_rationals))
        )
        if not added:
            return _skipped(
                (
                    FrequencyDomainSingularityRefinementReason.NO_ELIGIBLE_FREQUENCIES
                ),
                "Die lokalen Prüffrequenzen liegen außerhalb der Grenzen "
                "oder sind bereits im Raster enthalten.",
            )
        if not _within_limits(result, added, limits):
            return _skipped(
                FrequencyDomainSingularityRefinementReason.LIMIT_EXCEEDED,
                "Die optionale Singularitätsverfeinerung würde ein "
                "konfiguriertes Frequenzlimit überschreiten.",
            )

        refined_grid = LogFrequencyGridRequest(
            grid_request.omega_min,
            grid_request.omega_max,
            grid_request.points_per_decade,
            tuple(
                sorted(
                    grid_request.explicit_frequencies + added,
                    key=cmp_to_key(_compare_rationals),
                )
            ),
        )
        refined_request = FrequencyDomainWorkflowRequest(
            request.preparation_request,
            request.mode,
            single_angular_frequency=request.single_angular_frequency,
            grid_request=refined_grid,
            phase_presentation=request.phase_presentation,
            include_reserves=request.include_reserves,
        )
        return FrequencyDomainSingularityRefinementPlan(
            refined_request,
            added,
        )


def _scaled(
    value: ExactRationalValue,
    numerator: int,
    denominator: int,
) -> ExactRationalValue:
    scaled_numerator = value.numerator * numerator
    scaled_denominator = value.denominator * denominator
    divisor = gcd(abs(scaled_numerator), scaled_denominator)
    return ExactRationalValue(
        scaled_numerator // divisor,
        scaled_denominator // divisor,
    )


def _within(
    value: ExactRationalValue,
    lower: ExactRationalValue,
    upper: ExactRationalValue,
) -> bool:
    return (
        lower.numerator * value.denominator
        <= value.numerator * lower.denominator
        and value.numerator * upper.denominator
        <= upper.numerator * value.denominator
    )


def _compare_rationals(
    left: ExactRationalValue,
    right: ExactRationalValue,
) -> int:
    difference = (
        left.numerator * right.denominator
        - right.numerator * left.denominator
    )
    return (difference > 0) - (difference < 0)


def _within_limits(
    result: FrequencyDomainWorkflowResult,
    added: tuple[ExactRationalValue, ...],
    limits: FrequencyDomainWorkflowLimits,
) -> bool:
    assert result.request is not None
    assert result.request.grid_request is not None
    assert result.grid_result is not None
    final_explicit_count = (
        len(result.request.grid_request.explicit_frequencies) + len(added)
    )
    final_point_count = len(result.grid_result.points) + len(added)
    point_limits: tuple[int, ...] = (
        limits.grid.max_total_points,
        limits.frequency_response.max_frequency_points,
        limits.bode.max_grid_points,
    )
    if result.request.phase_presentation.value == "principal_and_unwrapped":
        point_limits += (limits.phase_unwrap.max_points,)
    digit_limit = min(
        limits.grid.max_rational_integer_digits,
        limits.frequency_response.max_frequency_integer_digits,
    )
    return (
        final_explicit_count <= limits.grid.max_explicit_points
        and final_point_count <= min(point_limits)
        and all(
            len(str(abs(value.numerator))) <= digit_limit
            and len(str(value.denominator)) <= digit_limit
            for value in added
        )
    )


def _key(value: ExactRationalValue) -> tuple[int, int]:
    return value.numerator, value.denominator


def _skipped(
    reason: FrequencyDomainSingularityRefinementReason,
    message: str,
) -> FrequencyDomainSingularityRefinementPlan:
    return FrequencyDomainSingularityRefinementPlan(
        None,
        reason=reason,
        message=message,
    )


__all__ = [
    "FrequencyDomainSingularityRefinementPlan",
    "FrequencyDomainSingularityRefinementPlanner",
    "FrequencyDomainSingularityRefinementReason",
]
