"""Exact bounded planning around singular Bode grid points."""

from dataclasses import replace

from klausurbotpro.application import (
    FrequencyDomainInputDraft,
    FrequencyDomainRequestFactory,
    FrequencyDomainSingularityRefinementPlanner,
    FrequencyDomainSingularityRefinementReason,
    FrequencyDomainWorkflowLimits,
    FrequencyDomainWorkflowMode,
    FrequencyDomainWorkflowResult,
    FrequencyDomainWorkflowService,
    FrequencyPhasePresentation,
    TransferFunctionInputDraft,
    WorkflowInputForm,
)
from klausurbotpro.domain import ExactRationalValue


def _result(
    expression: str = "1/(s^2+1)",
    *,
    omega_min: str = "1/10",
    omega_max: str = "10",
    explicit: str = "",
    limits: FrequencyDomainWorkflowLimits | None = None,
) -> FrequencyDomainWorkflowResult:
    if limits is None:
        limits = FrequencyDomainWorkflowLimits()
    draft = FrequencyDomainInputDraft(
        TransferFunctionInputDraft(
            WorkflowInputForm.COMMON,
            expression,
            "",
            "",
            "s",
            (),
            "frequency",
        ),
        FrequencyDomainWorkflowMode.BODE,
        omega_min_text=omega_min,
        omega_max_text=omega_max,
        points_per_decade_text="4",
        explicit_frequencies_text=explicit,
        phase_presentation=FrequencyPhasePresentation.PRINCIPAL_ONLY,
    )
    creation = FrequencyDomainRequestFactory(limits).create(draft)
    assert creation.request is not None
    return FrequencyDomainWorkflowService(limits).run(creation.request)


def test_singularity_at_one_adds_exact_symmetric_rationals() -> None:
    limits = FrequencyDomainWorkflowLimits()
    result = _result(limits=limits)

    plan = FrequencyDomainSingularityRefinementPlanner().plan(result, limits)

    assert plan.added_frequencies == (
        ExactRationalValue(99, 100),
        ExactRationalValue(101, 100),
    )
    assert plan.refined_request is not None
    assert plan.reason is None


def test_refined_request_preserves_user_request_and_explicit_frequencies() -> None:
    limits = FrequencyDomainWorkflowLimits()
    result = _result(explicit="1/2", limits=limits)
    assert result.request is not None
    original = result.request
    assert original.grid_request is not None

    plan = FrequencyDomainSingularityRefinementPlanner().plan(result, limits)

    assert plan.refined_request is not None
    refined = plan.refined_request
    assert refined.preparation_request is original.preparation_request
    assert refined.mode is original.mode
    assert refined.single_angular_frequency is original.single_angular_frequency
    assert refined.phase_presentation is original.phase_presentation
    assert refined.grid_request is not None
    assert refined.grid_request.omega_min == original.grid_request.omega_min
    assert refined.grid_request.omega_max == original.grid_request.omega_max
    assert (
        refined.grid_request.points_per_decade
        == original.grid_request.points_per_decade
    )
    assert refined.grid_request.explicit_frequencies == (
        ExactRationalValue(1, 2),
        ExactRationalValue(99, 100),
        ExactRationalValue(101, 100),
    )


def test_existing_explicit_point_is_not_duplicated() -> None:
    limits = FrequencyDomainWorkflowLimits()
    result = _result(explicit="99/100", limits=limits)

    plan = FrequencyDomainSingularityRefinementPlanner().plan(result, limits)

    assert plan.added_frequencies == (ExactRationalValue(101, 100),)
    assert plan.refined_request is not None
    assert plan.refined_request.grid_request is not None
    assert plan.refined_request.grid_request.explicit_frequencies == (
        ExactRationalValue(99, 100),
        ExactRationalValue(101, 100),
    )


def test_refinement_respects_existing_grid_bounds() -> None:
    limits = FrequencyDomainWorkflowLimits()
    result = _result(omega_min="1", omega_max="10", limits=limits)

    plan = FrequencyDomainSingularityRefinementPlanner().plan(result, limits)

    assert plan.added_frequencies == (ExactRationalValue(101, 100),)


def test_refinement_limit_returns_structured_skip_without_partial_request() -> None:
    defaults = FrequencyDomainWorkflowLimits()
    limits = replace(
        defaults,
        grid=replace(defaults.grid, max_explicit_points=1),
    )
    result = _result(limits=limits)

    plan = FrequencyDomainSingularityRefinementPlanner().plan(result, limits)

    assert plan.refined_request is None
    assert not plan.added_frequencies
    assert plan.reason is (
        FrequencyDomainSingularityRefinementReason.LIMIT_EXCEEDED
    )
    assert "Frequenzlimit" in plan.message


def test_regular_bode_result_requires_no_refinement() -> None:
    limits = FrequencyDomainWorkflowLimits()
    result = _result("1/(s+1)", limits=limits)

    plan = FrequencyDomainSingularityRefinementPlanner().plan(result, limits)

    assert plan.refined_request is None
    assert plan.reason is (
        FrequencyDomainSingularityRefinementReason.NO_SINGULARITY
    )
