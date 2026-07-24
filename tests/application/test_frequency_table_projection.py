"""Compact projections of already computed Bode tables."""

from math import log

from klausurbotpro.application import (
    FrequencyDomainInputDraft,
    FrequencyDomainRequestFactory,
    FrequencyDomainWorkflowMode,
    FrequencyDomainWorkflowResult,
    FrequencyDomainWorkflowService,
    FrequencyTableScope,
    TransferFunctionInputDraft,
    WorkflowInputForm,
    select_frequency_table_indices,
)


def _result(
    expression: str,
    *,
    omega_min: str = "1/1000",
    omega_max: str = "1000",
    points: str = "8",
    explicit: str = "",
) -> FrequencyDomainWorkflowResult:
    factory = FrequencyDomainRequestFactory()
    creation = factory.create(
        FrequencyDomainInputDraft(
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
            "1",
            omega_min,
            omega_max,
            points,
            explicit,
        )
    )
    assert creation.request is not None
    return FrequencyDomainWorkflowService(factory.limits).run(creation.request)


def test_compact_indices_are_deterministic_sorted_unique_and_bounded() -> None:
    result = _result("100/(s*(10*s+1))")

    first = select_frequency_table_indices(result, selected_bode_index=7)
    second = select_frequency_table_indices(result, selected_bode_index=7)

    assert first == second
    assert first == tuple(sorted(set(first)))
    assert len(first) <= 12
    assert first[0] == 0
    assert result.bode_data_result is not None
    assert first[-1] == len(result.bode_data_result.points) - 1
    assert 7 in first


def test_compact_indices_keep_explicit_added_singular_and_crossover_points() -> None:
    result = _result(
        "100/(s*(10*s+1)*(s^2+1))",
        omega_min="1/10",
        omega_max="100",
        explicit="99/100, 1, 101/100, 2",
    )
    assert result.request is not None
    assert result.request.grid_request is not None
    assert result.bode_data_result is not None
    assert result.crossover_analysis is not None
    bode_data = result.bode_data_result
    added = result.request.grid_request.explicit_frequencies[:2]

    indices = select_frequency_table_indices(
        result,
        added_frequencies=added,
    )
    frequencies = {
        bode_data.points[index].evaluation_frequency
        for index in indices
    }

    assert set(result.request.grid_request.explicit_frequencies) <= frequencies
    singular = next(
        index
        for index, point in enumerate(bode_data.points)
        if point.frequency_response_point.status.value == "singular"
    )
    assert singular in indices
    for crossover in (
        *result.crossover_analysis.gain_crossovers,
        *result.crossover_analysis.phase_crossovers,
    ):
        expected = min(
            range(len(bode_data.points)),
            key=lambda index: (
                abs(
                    log(
                        bode_data.points[index].evaluation_frequency.numerator
                        / bode_data.points[index].evaluation_frequency.denominator
                    )
                    - log(crossover.frequency)
                ),
                index,
            ),
        )
        assert expected in indices


def test_more_than_twelve_mandatory_points_are_all_preserved() -> None:
    explicit = ", ".join(str(value) for value in range(2, 16))
    result = _result(
        "1/(s+1)",
        omega_min="1",
        omega_max="20",
        points="2",
        explicit=explicit,
    )
    assert result.request is not None
    assert result.request.grid_request is not None
    assert result.bode_data_result is not None

    indices = select_frequency_table_indices(result)
    frequencies = {
        result.bode_data_result.points[index].evaluation_frequency
        for index in indices
    }

    assert len(indices) > 12
    assert set(result.request.grid_request.explicit_frequencies) <= frequencies


def test_full_scope_returns_every_original_index() -> None:
    result = _result("1/(s+1)")
    assert result.bode_data_result is not None

    indices = select_frequency_table_indices(
        result,
        scope=FrequencyTableScope.FULL_GRID,
    )

    assert indices == tuple(range(len(result.bode_data_result.points)))
