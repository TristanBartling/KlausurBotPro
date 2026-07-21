"""Compact presenter/view-state integration for F1B."""

from __future__ import annotations

from klausurbotpro.application import (
    FrequencyDomainInputDraft,
    FrequencyDomainRequestFactory,
    FrequencyDomainWorkflowMode,
    FrequencyDomainWorkflowRequest,
    FrequencyDomainWorkflowService,
    FrequencyPhasePresentation,
    TransferFunctionInputDraft,
    WorkflowInputForm,
)
from klausurbotpro.ui import FrequencyDomainPresenter


def test_nyquist_presenter_exposes_plot_summary_steps_and_latex() -> None:
    presenter = FrequencyDomainPresenter(FrequencyDomainRequestFactory())
    dispatched: list[object] = []
    presenter.execution_requested.connect(dispatched.append)
    draft = FrequencyDomainInputDraft(
        TransferFunctionInputDraft(
            WorkflowInputForm.COMMON,
            "6*s/((s-1)*(s-2))",
            "",
            "",
            "s",
            (),
            "frequency",
        ),
        FrequencyDomainWorkflowMode.BODE,
        "",
        "1/100",
        "100",
        "12",
        "",
        FrequencyPhasePresentation.PRINCIPAL_AND_UNWRAPPED,
    )
    assert presenter.submit(draft)
    request = dispatched[0]
    assert type(request) is FrequencyDomainWorkflowRequest
    presenter.accept_result(FrequencyDomainWorkflowService().run(request))
    state = presenter.state
    assert state.nyquist.visible
    assert (state.nyquist.p, state.nyquist.n_cw, state.nyquist.z) == ("2", "-2", "0")
    assert state.nyquist.positive_segments and state.nyquist.negative_segments
    worked = dict(state.worked_steps.general_lines)
    assert worked["Nyquist-Konvention"] == "Uhrzeigersinn positiv; Z=P+N_cw"
    assert "N_cw=-2" in worked["Umschlingungszahl"]
    assert r"Z=P+N_{\mathrm{cw}}" in state.latex_report
    assert "asymptotisch stabil" in state.latex_report
