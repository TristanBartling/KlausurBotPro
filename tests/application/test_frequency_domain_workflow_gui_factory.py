"""Exact GUI-input preparation for the frequency workflow."""

from klausurbotpro.application import (
    FrequencyDomainInputDraft,
    FrequencyDomainRequestFactory,
    FrequencyDomainWorkflowMode,
    FrequencyPhasePresentation,
    ParameterInputDraft,
    TransferFunctionInputDraft,
    WorkflowInputForm,
)
from klausurbotpro.domain import ExactRationalValue


def _preparation(
    *,
    form: WorkflowInputForm = WorkflowInputForm.COMMON,
) -> TransferFunctionInputDraft:
    return TransferFunctionInputDraft(
        form,
        "1/(T*s+1)",
        "1",
        "T*s+1",
        "s",
        (ParameterInputDraft("T", "3", "2"),),
        "frequency",
    )


def test_single_point_request_reuses_exact_preparation_factory() -> None:
    result = FrequencyDomainRequestFactory().create(
        FrequencyDomainInputDraft(
            _preparation(),
            FrequencyDomainWorkflowMode.SINGLE_POINT,
            single_angular_frequency_text=" 6/4 ",
        )
    )

    assert result.succeeded
    assert result.request is not None
    assert result.request.mode is FrequencyDomainWorkflowMode.SINGLE_POINT
    assert result.request.single_angular_frequency == ExactRationalValue(3, 2)
    assert result.request.grid_request is None
    assert result.request.preparation_request.allowed_parameter_names == ("T",)
    assert result.request.preparation_request.substitutions is not None
    assert (
        result.request.preparation_request.substitutions.assignments[0].value
        == ExactRationalValue(3, 2)
    )


def test_bode_request_supports_separated_input_grid_and_unwrap() -> None:
    result = FrequencyDomainRequestFactory().create(
        FrequencyDomainInputDraft(
            _preparation(form=WorkflowInputForm.SEPARATED),
            FrequencyDomainWorkflowMode.BODE,
            omega_min_text="1/10",
            omega_max_text="10",
            points_per_decade_text="4",
            explicit_frequencies_text="1/2, 1; 2",
            phase_presentation=(
                FrequencyPhasePresentation.PRINCIPAL_AND_UNWRAPPED
            ),
        )
    )

    assert result.request is not None
    assert result.request.preparation_request.input_form is (
        WorkflowInputForm.SEPARATED
    )
    assert result.request.grid_request is not None
    assert result.request.grid_request.omega_min == ExactRationalValue(1, 10)
    assert result.request.grid_request.omega_max == ExactRationalValue(10)
    assert result.request.grid_request.points_per_decade == 4
    assert result.request.grid_request.explicit_frequencies == (
        ExactRationalValue(1, 2),
        ExactRationalValue(1),
        ExactRationalValue(2),
    )
    assert result.request.phase_presentation is (
        FrequencyPhasePresentation.PRINCIPAL_AND_UNWRAPPED
    )


def test_invalid_rational_input_is_structured_and_value_free() -> None:
    result = FrequencyDomainRequestFactory().create(
        FrequencyDomainInputDraft(
            _preparation(),
            FrequencyDomainWorkflowMode.SINGLE_POINT,
            single_angular_frequency_text="0.5",
        )
    )

    assert not result.succeeded
    assert result.request is None
    assert result.errors[0].field == "single_angular_frequency"
    assert result.errors[0].code == "invalid_rational"
