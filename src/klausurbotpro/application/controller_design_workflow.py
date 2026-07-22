"""Application workflow for the source-checked controller-design MVP."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from math import isfinite

from klausurbotpro.application.frequency_domain_request_factory import (
    FrequencyDomainInputDraft,
    FrequencyDomainRequestFactory,
)
from klausurbotpro.application.frequency_domain_workflow_contracts import (
    FrequencyDomainWorkflowLimits,
    FrequencyDomainWorkflowMode,
    FrequencyDomainWorkflowResult,
    FrequencyDomainWorkflowStatus,
    FrequencyPhasePresentation,
)
from klausurbotpro.application.frequency_domain_workflow_service import (
    FrequencyDomainWorkflowService,
)
from klausurbotpro.application.latex_task_heading import prepend_latex_task_heading
from klausurbotpro.application.transfer_function_preparation_service import (
    TransferFunctionPreparationService,
)
from klausurbotpro.application.transfer_function_request_factory import (
    ParameterInputDraft,
    TransferFunctionInputDraft,
    TransferFunctionRequestFactory,
)
from klausurbotpro.application.transfer_function_workflow_contracts import WorkflowInputForm
from klausurbotpro.domain import (
    ControllerDesignCandidateStatus,
    ControllerDesignControl,
    ControllerDesignDiagnostic,
    ControllerDesignMethod,
    ControllerDesignStatus,
    ControllerParameters,
    ControllerScalar,
    ControllerType,
    ControllerValueProvenance,
    ExactRationalValue,
    FrequencyReserveAnalyzer,
    FrequencySampleSet,
    ParameterSubstitutions,
    StabilityReserve,
    TransferFunctionFrequencyResponseAnalyzer,
    design_cohen_coon,
    design_ziegler_nichols_closed,
    design_ziegler_nichols_open,
)

_DEFAULT_LIMITS = FrequencyDomainWorkflowLimits()
_UNIT_PATTERN = re.compile(r"(?:^|[^A-Za-z_])(ms|min|s)(?:$|[^A-Za-z_])", re.IGNORECASE)
_SCIENTIFIC_PATTERN = re.compile(r"[+]?(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)[eE][+-]?[0-9]+\Z")


@dataclass(frozen=True, slots=True)
class ControllerDesignInputDraft:
    method: ControllerDesignMethod
    controller_type: ControllerType
    task_name: str
    numerator_text: str = ""
    denominator_text: str = ""
    parameter_rows: tuple[ParameterInputDraft, ...] = ()
    target_phase_margin_text: str = ""
    omega_min_text: str = ""
    omega_max_text: str = ""
    points_per_decade_text: str = ""
    process_gain_text: str = ""
    dead_time_text: str = ""
    lag_time_text: str = ""
    critical_gain_text: str = ""
    critical_period_text: str = ""


@dataclass(frozen=True, slots=True)
class ControllerDesignCandidate:
    candidate_index: int
    target_frequency: float
    target_phase_residual_degrees: float
    original_magnitude: float
    positive_k_p: float
    resulting_open_loop: str
    frequency_analysis: FrequencyDomainWorkflowResult
    achieved_phase_margin_degrees: float
    controls: tuple[ControllerDesignControl, ...]
    status: ControllerDesignCandidateStatus
    diagnostics: tuple[ControllerDesignDiagnostic, ...] = ()

    def __post_init__(self) -> None:
        if type(self.status) is not ControllerDesignCandidateStatus:
            raise TypeError("status must be ControllerDesignCandidateStatus.")


@dataclass(frozen=True, slots=True)
class ControllerDesignResult:
    input: ControllerDesignInputDraft
    method: ControllerDesignMethod
    source_convention: str
    controller_type: ControllerType
    input_parameters: tuple[tuple[str, str], ...]
    normalized_parameters: tuple[tuple[str, str], ...]
    formula_or_target: str
    controller_parameters: ControllerParameters | None
    candidates: tuple[ControllerDesignCandidate, ...]
    frequency_analysis_before: FrequencyDomainWorkflowResult | None
    frequency_analysis_after: FrequencyDomainWorkflowResult | None
    controls: tuple[ControllerDesignControl, ...]
    worked_steps: tuple[str, ...]
    latex: str
    diagnostics: tuple[ControllerDesignDiagnostic, ...]
    status: ControllerDesignStatus

    @property
    def has_copyable_solution(self) -> bool:
        return bool(self.latex) and (
            self.status is ControllerDesignStatus.COMPLETE
            or (
                self.status is ControllerDesignStatus.SELECTION_REQUIRED
                and any(
                    candidate.status is ControllerDesignCandidateStatus.TARGET_MET
                    for candidate in self.candidates
                )
            )
        )


@dataclass(frozen=True, slots=True)
class ControllerDesignOutcomeDecision:
    status: ControllerDesignStatus
    selected_candidate_index: int | None
    diagnostic: ControllerDesignDiagnostic | None


def decide_p_phase_margin_outcome(
    candidate_statuses: tuple[ControllerDesignCandidateStatus, ...],
) -> ControllerDesignOutcomeDecision:
    """Decide the P-design outcome independently of numerical analysis."""
    successful = tuple(
        index
        for index, status in enumerate(candidate_statuses)
        if status is ControllerDesignCandidateStatus.TARGET_MET
    )
    if len(candidate_statuses) == 1 and successful:
        return ControllerDesignOutcomeDecision(ControllerDesignStatus.COMPLETE, 0, None)
    if len(candidate_statuses) > 1 and successful:
        return ControllerDesignOutcomeDecision(
            ControllerDesignStatus.SELECTION_REQUIRED,
            None,
            ControllerDesignDiagnostic(
                "SELECTION_REQUIRED",
                "Mehrere Zielphasenfrequenzen wurden gefunden und mindestens ein Kandidat "
                "erfüllt die geforderte globale Phasenreserve. Bitte wähle einen Kandidaten aus.",
            ),
        )
    return ControllerDesignOutcomeDecision(
        ControllerDesignStatus.FAILED,
        None,
        ControllerDesignDiagnostic(
            "PHASE_MARGIN_TARGET_NOT_MET",
            "Kein berechneter Kandidat erfüllt die geforderte globale Phasenreserve.",
        ),
    )


def controller_design_candidate_status_text(status: ControllerDesignCandidateStatus) -> str:
    return {
        ControllerDesignCandidateStatus.TARGET_MET: "Ziel vollständig erfüllt",
        ControllerDesignCandidateStatus.TARGET_CROSSING_MET_GLOBAL_MARGIN_NOT_MET: (
            "Zieldurchtritt erreicht, globale Phasenreserve nicht erfüllt"
        ),
        ControllerDesignCandidateStatus.TARGET_NOT_MET: "Ziel nicht erfüllt",
    }[status]


def controller_design_method_text(method: ControllerDesignMethod) -> str:
    return {
        ControllerDesignMethod.P_PHASE_MARGIN: "P-Verstärkung für gewünschte Phasenreserve",
        ControllerDesignMethod.ZIEGLER_NICHOLS_OPEN_LOOP: "Ziegler–Nichols – offener Kreis",
        ControllerDesignMethod.ZIEGLER_NICHOLS_CLOSED_LOOP: (
            "Ziegler–Nichols – geschlossener Kreis"
        ),
        ControllerDesignMethod.COHEN_COON: "Cohen–Coon",
    }[method]


class ControllerDesignWorkflowService:
    """Orchestrate exact table methods and reused frequency analyses."""

    def __init__(self, limits: FrequencyDomainWorkflowLimits = _DEFAULT_LIMITS) -> None:
        self._limits = limits
        self._frequency_factory = FrequencyDomainRequestFactory(limits)
        self._frequency_service = FrequencyDomainWorkflowService(limits)

    def run(self, draft: ControllerDesignInputDraft) -> ControllerDesignResult:
        if type(draft) is not ControllerDesignInputDraft:
            raise TypeError("draft must be ControllerDesignInputDraft.")
        if draft.method is ControllerDesignMethod.P_PHASE_MARGIN:
            return self._run_phase_margin(draft)
        return self._run_table(draft)

    def _run_table(self, draft: ControllerDesignInputDraft) -> ControllerDesignResult:
        normalized: tuple[tuple[str, str], ...]
        try:
            if draft.method is ControllerDesignMethod.ZIEGLER_NICHOLS_CLOSED_LOOP:
                gain = self._scalar(draft.critical_gain_text, "K_crit")
                period = self._scalar(draft.critical_period_text, "T_crit", time=True)
                parameters = design_ziegler_nichols_closed(draft.controller_type, gain, period)
                normalized = (("K_crit", _plain(gain)), ("T_crit [s]", _plain(period)))
                formula = "Ziegler–Nichols, geschlossener Kreis"
            else:
                gain = self._scalar(draft.process_gain_text, "K_S")
                dead = self._scalar(draft.dead_time_text, "L", time=True)
                lag = self._scalar(draft.lag_time_text, "T", time=True)
                normalized = (
                    ("K_S", _plain(gain)),
                    ("L [s]", _plain(dead)),
                    ("T [s]", _plain(lag)),
                )
                if draft.method is ControllerDesignMethod.ZIEGLER_NICHOLS_OPEN_LOOP:
                    parameters = design_ziegler_nichols_open(draft.controller_type, gain, dead, lag)
                    formula = "Ziegler–Nichols, offener Kreis"
                else:
                    ratio, parameters = design_cohen_coon(draft.controller_type, gain, dead, lag)
                    normalized = (*normalized, ("r=L/T", _plain(ratio)))
                    formula = "Cohen–Coon"
        except ValueError as error:
            if str(error) == "outside_source_domain":
                message = (
                    "Ziegler–Nichols für den offenen Kreis ist nach der "
                    "verwendeten Kursregel nur für L < 0,5 T vorgesehen."
                    if draft.method is ControllerDesignMethod.ZIEGLER_NICHOLS_OPEN_LOOP
                    else "Cohen–Coon ist nach der verwendeten Kursregel nur für L < 2 T vorgesehen."
                )
                return _failure(draft, "OUTSIDE_SOURCE_DOMAIN", message)
            code = "UNIT_MISMATCH" if "Sekunden" in str(error) else "INVALID_INPUT"
            return _failure(draft, code, str(error))
        controls = (
            ControllerDesignControl(
                "Positivitätsbedingungen", True, "Alle Eingabewerte sind positiv."
            ),
            ControllerDesignControl("Quellenbereich", True, "Der Quellenbereich ist erfüllt."),
            ControllerDesignControl(
                "PID-Form", parameters.forms_identical, "Parallele und ideale Form sind identisch."
            ),
            ControllerDesignControl(
                "Keine Zwischenrundung",
                True,
                "Alle Tabellenwerte wurden exakt rational weitergerechnet.",
            ),
        )
        steps = _table_steps(formula, normalized, parameters)
        latex = prepend_latex_task_heading(
            _table_latex(formula, normalized, parameters), draft.task_name
        )
        return ControllerDesignResult(
            draft,
            draft.method,
            "Quellenstrenge Kurskonvention; parallele PID-Form",
            draft.controller_type,
            normalized,
            normalized,
            formula,
            parameters,
            (),
            None,
            None,
            controls,
            steps,
            latex,
            (),
            ControllerDesignStatus.COMPLETE,
        )

    def _run_phase_margin(self, draft: ControllerDesignInputDraft) -> ControllerDesignResult:
        try:
            margin_value = self._scalar(draft.target_phase_margin_text, "Phasenreserve")
            target = margin_value.numerator / margin_value.denominator
            omega_min = self._scalar(draft.omega_min_text, "omega_min")
            omega_max = self._scalar(draft.omega_max_text, "omega_max")
            points = int(draft.points_per_decade_text.strip())
        except (ValueError, TypeError):
            return _failure(draft, "INVALID_INPUT", "Frequenz- und Reservewerte sind ungültig.")
        if not 0 < target < 180 or _fraction(omega_min) >= _fraction(omega_max) or points <= 0:
            return _failure(draft, "INVALID_INPUT", "Es gilt 0 < Φ_R < 180° und 0 < ω_min < ω_max.")
        before_creation = self._frequency_factory.create(
            self._frequency_draft(draft, draft.numerator_text, omega_min, omega_max, points)
        )
        if not before_creation.succeeded or before_creation.request is None:
            message = " ".join(error.message for error in before_creation.errors)
            code = "UNRESOLVED_PARAMETERS" if "Parameter" in message else "INVALID_INPUT"
            return _failure(draft, code, message)
        before = self._frequency_service.run(before_creation.request)
        if before.status is not FrequencyDomainWorkflowStatus.COMPLETE:
            return _failure(
                draft,
                "FREQUENCY_REANALYSIS_FAILED",
                "Die Frequenzanalyse der Strecke ist fehlgeschlagen.",
            )
        preparation, bode, unwrap = (
            before.preparation_result,
            before.bode_data_result,
            before.phase_unwrap_result,
        )
        assert preparation is not None and preparation.reduced_value is not None
        assert bode is not None and unwrap is not None
        substitutions = preparation.request.substitutions or ParameterSubstitutions()
        target_phase = -180.0 + target
        roots = FrequencyReserveAnalyzer().find_unwrapped_phase_target_roots(
            preparation.reduced_value,
            substitutions,
            bode,
            unwrap,
            float(target_phase),
            field=draft.task_name,
        )
        candidates: list[ControllerDesignCandidate] = []
        for index, root in enumerate(roots, 1):
            frequency = _exact_from_decimal(format(root.frequency, ".16g"))
            response = TransferFunctionFrequencyResponseAnalyzer().analyze(
                preparation.reduced_value,
                FrequencySampleSet((frequency,)),
                substitutions,
                field=draft.task_name,
            )
            magnitude = float(response.points[0].numerical_magnitude or "nan")
            if not isfinite(magnitude) or magnitude <= 0:
                continue
            kp = 1.0 / magnitude
            scaled = f"({format(kp, '.17g')})*({draft.numerator_text})"
            after_creation = self._frequency_factory.create(
                self._frequency_draft(draft, scaled, omega_min, omega_max, points)
            )
            if not after_creation.succeeded or after_creation.request is None:
                continue
            after = self._frequency_service.run(after_creation.request)
            if after.status is not FrequencyDomainWorkflowStatus.COMPLETE:
                continue
            achieved = _nearest_phase_margin(after, root.frequency)
            phase_margins = _finite_phase_margins(after)
            global_margin_met = bool(phase_margins) and min(phase_margins) >= target - 0.1
            controls = (
                ControllerDesignControl(
                    "Zielphase",
                    root.residual_degrees <= 0.05,
                    f"Residuum {root.residual_degrees:.6g}°",
                ),
                ControllerDesignControl("Positiver P-Faktor", kp > 0, f"k_P={kp:.12g}"),
                ControllerDesignControl(
                    "Betrag nach Skalierung",
                    abs(kp * magnitude - 1) <= 2e-7,
                    f"|k_P G_0|={kp * magnitude:.12g}",
                ),
                ControllerDesignControl(
                    "Phasenreserve", abs(achieved - target) <= 0.1, f"Φ_R,ist={achieved:.8g}°"
                ),
                ControllerDesignControl(
                    "Globale Phasenreserve",
                    global_margin_met,
                    (
                        f"Kleinste nachgerechnete Reserve: {min(phase_margins):.8g}°."
                        if phase_margins
                        else "Keine endliche Phasenreserve verfügbar."
                    ),
                ),
                ControllerDesignControl(
                    "Nyquist-Nachprüfung",
                    after.nyquist_analysis is not None,
                    "Vorhandener Nyquist-Kern wurde erneut ausgeführt.",
                ),
            )
            crossing_met = all(item.passed for item in controls[:4])
            candidate_status = (
                ControllerDesignCandidateStatus.TARGET_MET
                if crossing_met and global_margin_met
                else (
                    ControllerDesignCandidateStatus.TARGET_CROSSING_MET_GLOBAL_MARGIN_NOT_MET
                    if crossing_met
                    else ControllerDesignCandidateStatus.TARGET_NOT_MET
                )
            )
            candidates.append(
                ControllerDesignCandidate(
                    index,
                    root.frequency,
                    root.residual_degrees,
                    magnitude,
                    kp,
                    f"({format(kp, '.17g')})*({draft.numerator_text})/({draft.denominator_text})",
                    after,
                    achieved,
                    controls,
                    candidate_status,
                )
            )
        if not candidates:
            return _failure(
                draft,
                "NO_PHASE_TARGET_ROOT",
                "Die Zielphase wird im untersuchten Frequenzbereich nicht erreicht.",
                before=before,
            )
        decision = decide_p_phase_margin_outcome(tuple(item.status for item in candidates))
        diagnostics = () if decision.diagnostic is None else (decision.diagnostic,)
        parameters = (
            _numeric_p_parameters(candidates[decision.selected_candidate_index].positive_k_p)
            if decision.selected_candidate_index is not None
            else None
        )
        latex = prepend_latex_task_heading(
            _phase_margin_latex(draft, target, target_phase, tuple(candidates)), draft.task_name
        )
        return ControllerDesignResult(
            draft,
            draft.method,
            "Positive P-Skalierung mit entfalteter Phase",
            ControllerType.P,
            (("G_0(s)", f"({draft.numerator_text})/({draft.denominator_text})"),),
            (("Zielphase [deg]", f"{target_phase:.12g}"),),
            f"φ_entf(ω)={target_phase:.12g}°",
            parameters,
            tuple(candidates),
            before,
            (
                candidates[decision.selected_candidate_index].frequency_analysis
                if decision.selected_candidate_index is not None
                else None
            ),
            tuple(item for candidate in candidates for item in candidate.controls),
            tuple(_phase_margin_steps(target, target_phase, tuple(candidates))),
            latex,
            diagnostics,
            decision.status,
        )

    def _frequency_draft(
        self,
        draft: ControllerDesignInputDraft,
        numerator: str,
        omega_min: ExactRationalValue,
        omega_max: ExactRationalValue,
        points: int,
        explicit: str = "",
    ) -> FrequencyDomainInputDraft:
        return FrequencyDomainInputDraft(
            TransferFunctionInputDraft(
                WorkflowInputForm.SEPARATED,
                "",
                numerator,
                draft.denominator_text,
                "s",
                draft.parameter_rows,
                "controller_design",
            ),
            FrequencyDomainWorkflowMode.BODE,
            omega_min_text=_plain(omega_min),
            omega_max_text=_plain(omega_max),
            points_per_decade_text=str(points),
            explicit_frequencies_text=explicit,
            phase_presentation=FrequencyPhasePresentation.PRINCIPAL_AND_UNWRAPPED,
        )

    def _scalar(self, text: str, field: str, *, time: bool = False) -> ExactRationalValue:
        if type(text) is not str or not text.strip():
            raise ValueError(f"{field}: Ein Wert ist erforderlich.")
        if time and _UNIT_PATTERN.search(text):
            raise ValueError("Zeitwerte müssen als reine Zahlen in Sekunden eingegeben werden.")
        normalized = text.strip().replace("−", "-").replace("–", "-")
        if _SCIENTIFIC_PATTERN.fullmatch(normalized):
            value = _exact_from_decimal(normalized)
            if value.numerator <= 0:
                raise ValueError(f"{field} muss positiv sein.")
            return value
        creation = TransferFunctionRequestFactory(self._limits.preparation).create(
            TransferFunctionInputDraft(WorkflowInputForm.COMMON, normalized, "", "", "s", (), field)
        )
        if not creation.succeeded or creation.request is None:
            raise ValueError(f"{field}: ungültiger mathematischer Wert.")
        prepared = TransferFunctionPreparationService(self._limits.preparation).prepare(
            creation.request
        )
        if not prepared.succeeded or prepared.reduced_value is None:
            raise ValueError(f"{field}: ungültiger mathematischer Wert.")
        expression = (
            prepared.reduced_value.numerator.expression._as_sympy()
            / prepared.reduced_value.denominator.expression._as_sympy()
        )
        if expression.free_symbols or not expression.is_Rational:
            raise ValueError(f"{field}: ungelöste Parameter sind nicht zulässig.")
        value = ExactRationalValue(int(expression.p), int(expression.q))
        if value.numerator <= 0:
            raise ValueError(f"{field} muss positiv sein.")
        return value


def _failure(
    draft: ControllerDesignInputDraft,
    code: str,
    message: str,
    *,
    before: FrequencyDomainWorkflowResult | None = None,
) -> ControllerDesignResult:
    return ControllerDesignResult(
        draft,
        draft.method,
        "Quellenstrenge Kurskonvention",
        draft.controller_type,
        (),
        (),
        "",
        None,
        (),
        before,
        None,
        (),
        (),
        "",
        (ControllerDesignDiagnostic(code, message),),
        ControllerDesignStatus.FAILED,
    )


def _numeric_p_parameters(kp: float) -> ControllerParameters:
    numeric = ControllerScalar(
        None, format(kp, ".16g"), ControllerValueProvenance.NUMERIC_FREQUENCY_DESIGN
    )
    zero = ControllerScalar(ExactRationalValue(0), "0", ControllerValueProvenance.EXACT_RATIONAL)
    return ControllerParameters(
        ControllerType.P,
        numeric,
        zero,
        zero,
        None,
        None,
        f"G_R(s)={format(kp, '.16g')}",
        rf"G_R(s)={kp:.12g}",
        rf"G_R(s)={kp:.12g}",
        True,
    )


def _nearest_phase_margin(result: FrequencyDomainWorkflowResult, target_frequency: float) -> float:
    if result.reserve_analysis is None:
        return float("nan")
    values = [
        item
        for item in result.reserve_analysis.phase_margins
        if item.crossover is not None and item.value is not None
    ]
    if not values:
        return float("nan")

    def distance(item: StabilityReserve) -> float:
        crossover = item.crossover
        assert crossover is not None
        return abs(crossover.frequency - target_frequency)

    nearest = min(values, key=distance)
    assert nearest.value is not None
    return float(nearest.value)


def _finite_phase_margins(result: FrequencyDomainWorkflowResult) -> tuple[float, ...]:
    if result.reserve_analysis is None:
        return ()
    return tuple(
        float(item.value)
        for item in result.reserve_analysis.phase_margins
        if item.value is not None
    )


def _table_steps(
    formula: str, values: tuple[tuple[str, str], ...], parameters: ControllerParameters
) -> tuple[str, ...]:
    return (
        f"Verfahren: {formula}.",
        "Gegebene Werte: " + ", ".join(f"{key}={value}" for key, value in values) + ".",
        "Quellenbereich geprüft.",
        f"Tabellenzeile {parameters.controller_type.value.upper()} exakt eingesetzt.",
        _parameter_summary_plain(parameters),
        _ideal_summary_plain(parameters),
        "Parallele und ideale Reglerform symbolisch rekonstruiert.",
        "Keine Zwischenrundung verwendet.",
    )


def _parameter_summary_plain(parameters: ControllerParameters) -> str:
    values = [f"k_P={_display(parameters.k_p)}"]
    if parameters.controller_type in (ControllerType.PI, ControllerType.PID):
        values.append(f"k_I={_display(parameters.k_i)}")
    if parameters.controller_type is ControllerType.PID:
        values.append(f"k_D={_display(parameters.k_d)}")
    return ", ".join(values) + "."


def _ideal_summary_plain(parameters: ControllerParameters) -> str:
    if parameters.controller_type is ControllerType.P:
        return "Der P-Regler benötigt keine Idealparameter."
    if parameters.controller_type is ControllerType.PI:
        return "Idealparameter aus T_I=k_P/k_I bestimmt."
    return "Idealparameter aus T_I=k_P/k_I und T_D=k_D/k_P bestimmt."


def _table_latex(
    formula: str, values: tuple[tuple[str, str], ...], parameters: ControllerParameters
) -> str:
    given = r",\quad ".join(rf"\text{{{key}}}={value}" for key, value in values)
    parameter_lines: tuple[str, ...]
    if parameters.controller_type is ControllerType.P:
        parameter_lines = (
            rf"\[k_P={_latex_scalar(parameters.k_p)}\]",
            rf"\[{parameters.parallel_latex}\]",
        )
    elif parameters.controller_type is ControllerType.PI:
        assert parameters.ideal_t_i is not None
        parameter_lines = (
            rf"\[k_P={_latex_scalar(parameters.k_p)},\quad "
            rf"k_I={_latex_scalar(parameters.k_i)}\]",
            rf"\[T_I={_latex_scalar(parameters.ideal_t_i)}\]",
            rf"\[{parameters.parallel_latex}\]",
            rf"\[{parameters.ideal_latex}\]",
            r"\[k_P+\frac{k_I}{s}\equiv k_P\left(1+\frac{1}{T_Is}\right)\]",
        )
    else:
        assert parameters.ideal_t_i is not None and parameters.ideal_t_d is not None
        parameter_lines = (
            rf"\[k_P={_latex_scalar(parameters.k_p)},\quad "
            rf"k_I={_latex_scalar(parameters.k_i)},\quad "
            rf"k_D={_latex_scalar(parameters.k_d)}\]",
            rf"\[T_I={_latex_scalar(parameters.ideal_t_i)},\qquad "
            rf"T_D={_latex_scalar(parameters.ideal_t_d)}\]",
            rf"\[{parameters.parallel_latex}\]",
            rf"\[{parameters.ideal_latex}\]",
            r"\[k_P+\frac{k_I}{s}+k_Ds\equiv "
            r"k_P\left(1+\frac{1}{T_Is}+T_Ds\right)\]",
        )
    return "\n".join(
        (
            r"\textbf{Gegeben}",
            rf"\[{given}\]",
            r"\textbf{Gesucht}",
            rf"\[\text{{Parameter des {parameters.controller_type.value.upper()}-Reglers "
            r"und seine Übertragungsfunktion}}\]",
            r"\textbf{Lösung}",
            rf"\text{{Verfahren: {formula}; Quellenbereich erfüllt.}}",
            rf"\text{{Tabellenzeile: {parameters.controller_type.value.upper()}.}}",
            _selected_formula_latex(formula, parameters.controller_type),
            *parameter_lines,
            r"\text{Kontrolle: exakte Weiterrechnung ohne Zwischenrundung; Formen identisch.}",
            rf"\[\boxed{{{parameters.parallel_latex}}}\]",
            r"\text{Verstärkungsdimension gemäß Aufgabenstellung; nicht separat angegeben.}",
        )
    )


def _selected_formula_latex(formula: str, controller_type: ControllerType) -> str:
    rows = {
        (
            "Ziegler–Nichols, offener Kreis",
            ControllerType.P,
        ): r"\[k_P=\frac{T}{K_SL}\]",
        (
            "Ziegler–Nichols, offener Kreis",
            ControllerType.PI,
        ): r"\[k_P=\frac{0.9T}{K_SL},\quad T_I=3.33L,\quad k_I=\frac{k_P}{3.33L}\]",
        (
            "Ziegler–Nichols, offener Kreis",
            ControllerType.PID,
        ): r"\[k_P=\frac{1.2T}{K_SL},\quad k_I=\frac{k_P}{2L},\quad k_D=0.5k_PL\]",
        (
            "Ziegler–Nichols, geschlossener Kreis",
            ControllerType.P,
        ): r"\[k_P=0.5K_{\mathrm{crit}}\]",
        (
            "Ziegler–Nichols, geschlossener Kreis",
            ControllerType.PI,
        ): (
            r"\[k_P=0.45K_{\mathrm{crit}},\quad T_I=0.85T_{\mathrm{crit}},"
            r"\quad k_I=\frac{k_P}{T_I}\]"
        ),
        (
            "Ziegler–Nichols, geschlossener Kreis",
            ControllerType.PID,
        ): (
            r"\[k_P=0.6K_{\mathrm{crit}},\quad "
            r"k_I=\frac{k_P}{0.5T_{\mathrm{crit}}},\quad "
            r"k_D=0.12k_PT_{\mathrm{crit}}\]"
        ),
        (
            "Cohen–Coon",
            ControllerType.P,
        ): r"\[r=\frac{L}{T},\quad k_P=\frac{1}{K_S}\frac{T}{L}\left(1+\frac{r}{3}\right)\]",
        (
            "Cohen–Coon",
            ControllerType.PI,
        ): (
            r"\[k_P=\frac{0.9}{K_S}\frac{T}{L}"
            r"\left(0.9+\frac{r}{12}\right),\quad "
            r"k_I=\frac{k_P(9+20r)}{L(30+3r)}\]"
        ),
        (
            "Cohen–Coon",
            ControllerType.PID,
        ): (
            r"\[k_P=\frac{1.2}{K_S}\frac{T}{L}"
            r"\left(1.35+\frac{r}{15}\right),\quad "
            r"k_I=\frac{k_P(13+8r)}{L(32+6r)},\quad "
            r"k_D=k_PL\frac{4}{11+2r}\]"
        ),
    }
    return rows[(formula, controller_type)]


def _phase_margin_steps(
    target: float, target_phase: float, candidates: tuple[ControllerDesignCandidate, ...]
) -> list[str]:
    steps = [
        f"Gewünschte Phasenreserve: {target:.12g}°.",
        f"Zielphase: -180°+{target:.12g}°={target_phase:.12g}°.",
        "Entfaltete Phase segmentweise durchsucht; Singularitätslücken wurden nicht verbunden.",
    ]
    for candidate in candidates:
        steps.extend(
            (
                f"Kandidat {candidate.candidate_index}: ω={candidate.target_frequency:.12g} rad/s.",
                f"|G_0(jω)|={candidate.original_magnitude:.12g}; "
                f"k_P={candidate.positive_k_p:.12g}.",
                "Vollständige Frequenz-, Reserven- und Nyquist-Nachrechnung: "
                f"Φ_R,ist={candidate.achieved_phase_margin_degrees:.8g}°.",
                f"Kandidatenstatus: {controller_design_candidate_status_text(candidate.status)}.",
            )
        )
    return steps


def _phase_margin_latex(
    draft: ControllerDesignInputDraft,
    target: float,
    target_phase: float,
    candidates: tuple[ControllerDesignCandidate, ...],
) -> str:
    lines = [
        r"\textbf{Gegeben}",
        rf"\[G_0(s)=\frac{{{draft.numerator_text}}}{{{draft.denominator_text}}},"
        rf"\qquad \Phi_{{R,\mathrm{{soll}}}}={target:.12g}^\circ\]",
        r"\textbf{Gesucht}",
        r"\[G_R(s)=k_P,\qquad k_P>0\]",
        r"\textbf{Lösung}",
        rf"\[\varphi_{{\mathrm{{ziel}}}}=-180^\circ+{target:.12g}^\circ={target_phase:.12g}^\circ\]",
        r"\text{Die entfaltete Phase wird in jedem regulären Frequenzsegment getrennt durchsucht.}",
    ]
    for candidate in candidates:
        lines.extend(
            (
                rf"\textbf{{Kandidat {candidate.candidate_index}}}",
                rf"\[\omega_{{{candidate.candidate_index}}}="
                rf"{candidate.target_frequency:.12g}\,\mathrm{{rad/s}},\quad "
                rf"|G_0(j\omega)|={candidate.original_magnitude:.12g}\]",
                rf"\[k_{{P,{candidate.candidate_index}}}="
                rf"\frac{{1}}{{|G_0(j\omega)|}}={candidate.positive_k_p:.12g}\]",
                rf"\[G_R(s)={candidate.positive_k_p:.12g},\qquad "
                r"L_{mathrm{neu}}(s)=k_PG_0(s)\]",
                rf"\[|k_PG_0(j\omega)|\approx1,\qquad "
                rf"\Phi_{{R,\mathrm{{ist}}}}="
                rf"{candidate.achieved_phase_margin_degrees:.8g}^\circ\]",
                r"\text{Durchtritte und Reserven wurden vollständig neu berechnet; "
                r"der vorhandene Nyquist-Kern wurde erneut ausgeführt.}",
                rf"\text{{Status: {controller_design_candidate_status_text(candidate.status)}.}}",
            )
        )
    successful = tuple(
        candidate
        for candidate in candidates
        if candidate.status is ControllerDesignCandidateStatus.TARGET_MET
    )
    if len(candidates) == 1 and successful:
        lines.append(rf"\[\boxed{{G_R(s)={successful[0].positive_k_p:.12g}}}\]")
    elif len(candidates) > 1 and successful:
        lines.append(
            r"\text{Mindestens ein gültiger Kandidat ist vorhanden; eine Auswahl ist erforderlich.}"
        )
    else:
        lines.append(r"\text{Kein Kandidat erfüllt die geforderte globale Phasenreserve.}")
    return "\n".join(lines)


def _display(value: ControllerScalar) -> str:
    return _plain(value.exact) if value.exact is not None else value.numerical


def _latex_scalar(value: ControllerScalar) -> str:
    if value.exact is None:
        return value.numerical
    return (
        str(value.exact.numerator)
        if value.exact.denominator == 1
        else rf"\frac{{{value.exact.numerator}}}{{{value.exact.denominator}}}"
    )


def _plain(value: ExactRationalValue) -> str:
    return (
        str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"
    )


def _fraction(value: ExactRationalValue) -> Fraction:
    return Fraction(value.numerator, value.denominator)


def _exact_from_decimal(text: str) -> ExactRationalValue:
    value = Fraction(Decimal(text))
    return ExactRationalValue(value.numerator, value.denominator)


__all__ = [
    "ControllerDesignCandidate",
    "ControllerDesignCandidateStatus",
    "ControllerDesignInputDraft",
    "ControllerDesignOutcomeDecision",
    "ControllerDesignResult",
    "ControllerDesignWorkflowService",
    "controller_design_candidate_status_text",
    "controller_design_method_text",
    "decide_p_phase_margin_outcome",
]
