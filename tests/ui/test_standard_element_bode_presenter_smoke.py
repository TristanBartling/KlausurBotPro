"""One compact smoke test for Worked Steps and LaTeX integration."""

from klausurbotpro.application import (
    FrequencyDomainInputDraft,
    FrequencyDomainRequestFactory,
    FrequencyDomainWorkflowMode,
    FrequencyDomainWorkflowRequest,
    FrequencyDomainWorkflowService,
    TransferFunctionInputDraft,
    WorkflowInputForm,
)
from klausurbotpro.ui import FrequencyDomainPresenter


def test_supported_standard_elements_appear_in_existing_outputs() -> None:
    presenter = FrequencyDomainPresenter(FrequencyDomainRequestFactory())
    dispatched: list[object] = []
    presenter.execution_requested.connect(dispatched.append)
    draft = FrequencyDomainInputDraft(
        TransferFunctionInputDraft(
            WorkflowInputForm.COMMON,
            "100/(s*(10*s+1))",
            "",
            "",
            "s",
            (),
            "frequency",
        ),
        FrequencyDomainWorkflowMode.BODE,
        "",
        "1/100",
        "10",
        "2",
        "",
    )

    assert presenter.submit(draft)
    request = dispatched[0]
    assert type(request) is FrequencyDomainWorkflowRequest
    presenter.accept_result(FrequencyDomainWorkflowService().run(request))

    worked = dict(presenter.state.worked_steps.general_lines)
    assert "100" in worked["Standardgliederzerlegung"]
    assert worked["Gesamtfaktor K"] == "100"
    assert worked["Anfangssteigung"] == "-20 dB/Dekade"
    assert "omega_k=1/10" in worked["Knickereignisse"]
    assert "L_a(omega)" in worked["Globale Betragsasymptote"]
    assert worked["Exakte Rekonstruktion"] == "best\u00e4tigt"
    assert r"\section*{Standardglieder und asymptotischer Betrag}" in (
        presenter.state.latex_report
    )
    assert r"L_a(\omega)" in presenter.state.latex_report
