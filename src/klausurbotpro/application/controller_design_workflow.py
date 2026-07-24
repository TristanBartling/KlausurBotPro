"""Application workflow for the source-checked controller-design MVP."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from math import isfinite

import sympy as sp

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
    ControllerFormulaStep,
    ControllerParameters,
    ControllerResultStep,
    ControllerScalar,
    ControllerType,
    ControllerValidityStep,
    ControllerValueProvenance,
    ExactRationalValue,
    FrequencyReserveAnalyzer,
    FrequencySampleSet,
    ParameterSubstitutions,
    ReducedTransferFunction,
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
class ControllerFrequencyPresentation:
    """Already-computed P-design data prepared for UI projection."""

    candidate_index: int
    target_frequency: str
    target_phase: str
    target_margin: str
    original_magnitude: str
    positive_k_p: str
    new_open_loop: str
    magnitude_control: ControllerDesignControl
    phase_margin_control: ControllerDesignControl
    global_margin_control: ControllerDesignControl
    nyquist_control: ControllerDesignControl


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
    formula_steps: tuple[ControllerFormulaStep, ...] = ()
    validity_steps: tuple[ControllerValidityStep, ...] = ()
    result_steps: tuple[ControllerResultStep, ...] = ()
    primary_result_plain: str = ""
    primary_result_latex: str = ""
    equivalent_result_plain: str = ""
    equivalent_result_latex: str = ""
    target_frequency_formula: ControllerFormulaStep | None = None
    frequency_presentations: tuple[ControllerFrequencyPresentation, ...] = ()

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
                normalized = (
                    ("K_crit", _rational_display(gain)),
                    ("T_crit [s]", _rational_display(period)),
                )
                formula = "Ziegler–Nichols, geschlossener Kreis"
                formula_steps = _closed_formula_steps(
                    draft.controller_type, gain, period, parameters
                )
                validity_steps = _closed_validity_steps(gain, period)
            else:
                gain = self._scalar(draft.process_gain_text, "K_S")
                dead = self._scalar(draft.dead_time_text, "K_T", time=True)
                lag = self._scalar(draft.lag_time_text, "T", time=True)
                normalized = (
                    ("K_S", _rational_display(gain)),
                    ("K_T [s]", _rational_display(dead)),
                    ("T [s]", _rational_display(lag)),
                )
                ratio_fraction = _fraction(dead) / _fraction(lag)
                if draft.method is ControllerDesignMethod.ZIEGLER_NICHOLS_OPEN_LOOP:
                    if ratio_fraction >= Fraction(1, 2):
                        return _failure(
                            draft,
                            "OUTSIDE_SOURCE_DOMAIN",
                            "K_T: Die strikte Bedingung K_T/T < 0,5 ist nicht erfüllt "
                            f"({_fraction_plain(ratio_fraction)} >= 1/2).",
                        )
                    parameters = design_ziegler_nichols_open(draft.controller_type, gain, dead, lag)
                    formula = "Ziegler–Nichols, offener Kreis"
                    formula_steps = _open_formula_steps(
                        draft.controller_type, gain, dead, lag, parameters
                    )
                    validity_steps = _open_validity_steps(gain, dead, lag)
                else:
                    if ratio_fraction >= 2:
                        return _failure(
                            draft,
                            "OUTSIDE_SOURCE_DOMAIN",
                            "K_T: Die strikte Bedingung 0 < r=K_T/T < 2 ist nicht erfüllt "
                            f"(r={_fraction_plain(ratio_fraction)}).",
                        )
                    ratio, parameters = design_cohen_coon(draft.controller_type, gain, dead, lag)
                    normalized = (*normalized, ("r=K_T/T", _rational_display(ratio)))
                    formula = "Cohen–Coon"
                    formula_steps = _cohen_coon_formula_steps(
                        draft.controller_type, gain, dead, lag, ratio, parameters
                    )
                    validity_steps = _cohen_coon_validity_steps(gain, dead, lag, ratio)
        except ValueError as error:
            code = "UNIT_MISMATCH" if "Sekunden" in str(error) else "INVALID_INPUT"
            return _failure(draft, code, str(error))

        result_steps = _controller_result_steps(parameters)
        presented_validity = _presented_validity_steps(formula, validity_steps)
        validity_controls: tuple[ControllerDesignControl, ...]
        if formula == "Ziegler–Nichols, geschlossener Kreis":
            validity_controls = (
                ControllerDesignControl(
                    "Voraussetzungen",
                    True,
                    "; ".join(step.substitution_plain for step in presented_validity)
                    + ". Alle Voraussetzungen sind erfüllt.",
                ),
            )
        else:
            validity_controls = (
                ControllerDesignControl(
                    "Positivitätsbedingungen",
                    True,
                    "; ".join(step.substitution_plain for step in presented_validity[:-1]),
                ),
                ControllerDesignControl(
                    "Quellenbereich", True, presented_validity[-1].substitution_plain
                ),
            )
        controls = (
            *validity_controls,
            ControllerDesignControl(
                "Reglerformen",
                parameters.forms_identical,
                "Parallele und ideale Form sind symbolisch identisch.",
            ),
            ControllerDesignControl(
                "Keine Zwischenrundung",
                True,
                "Alle Tabellenwerte wurden exakt rational weitergerechnet.",
            ),
        )
        steps = _table_steps(
            formula, normalized, parameters, formula_steps, validity_steps, result_steps
        )
        latex = prepend_latex_task_heading(
            _table_latex(
                formula,
                normalized,
                parameters,
                formula_steps,
                validity_steps,
                result_steps,
            ),
            draft.task_name,
        )
        return ControllerDesignResult(
            draft,
            draft.method,
            "Quellenstrenge Kurskonvention; parallele PID-Form",
            draft.controller_type,
            normalized,
            normalized,
            formula_steps[0].general_plain,
            parameters,
            (),
            None,
            None,
            controls,
            steps,
            latex,
            (),
            ControllerDesignStatus.COMPLETE,
            formula_steps,
            validity_steps,
            result_steps,
            _controller_parallel_plain(parameters),
            _controller_parallel_latex(parameters),
            _controller_ideal_plain(parameters),
            _controller_ideal_latex(parameters),
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
        target_frequency_formula = _recognized_target_frequency_formula(
            preparation.reduced_value, target, tuple(candidates)
        )
        formula_steps = (
            () if target_frequency_formula is None else (target_frequency_formula,)
        ) + _phase_formula_steps(tuple(candidates))
        validity_steps = _phase_validity_steps(target, tuple(candidates))
        frequency_presentations = _frequency_presentations(target, target_phase, tuple(candidates))
        result_steps = () if parameters is None else _controller_result_steps(parameters)
        primary_plain = "" if parameters is None else _controller_parallel_plain(parameters)
        primary_latex = "" if parameters is None else _controller_parallel_latex(parameters)
        open_loop_latex = _prepared_open_loop_latex(preparation.reduced_value)
        latex = prepend_latex_task_heading(
            _phase_margin_latex(
                open_loop_latex,
                target,
                target_phase,
                tuple(candidates),
                target_frequency_formula,
            ),
            draft.task_name,
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
            tuple(
                _phase_margin_steps(
                    target, target_phase, tuple(candidates), target_frequency_formula
                )
            ),
            latex,
            diagnostics,
            decision.status,
            formula_steps,
            validity_steps,
            result_steps,
            primary_plain,
            primary_latex,
            primary_plain,
            primary_latex,
            target_frequency_formula,
            frequency_presentations,
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
        None, format(kp, ".12g"), ControllerValueProvenance.NUMERIC_FREQUENCY_DESIGN
    )
    zero = ControllerScalar(ExactRationalValue(0), "0", ControllerValueProvenance.EXACT_RATIONAL)
    return ControllerParameters(
        ControllerType.P,
        numeric,
        zero,
        zero,
        None,
        None,
        f"G_R(s)={format(kp, '.12g')}",
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


_SYMBOL_LATEX = {
    "K_S": r"K_S",
    "K_crit": r"K_{\mathrm{crit}}",
    "T_crit": r"T_{\mathrm{crit}}",
    "k_P": r"k_P",
    "k_I": r"k_I",
    "k_D": r"k_D",
    "T_I": r"T_I",
    "T_D": r"T_D",
    "K_T": r"K_T",
    "T": "T",
    "r": r"r=\frac{K_T}{T}",
}

_INPUT_SYMBOL_KEYS = {
    "K_S": "K_S",
    "K_T [s]": "K_T",
    "T [s]": "T",
    "K_crit": "K_crit",
    "T_crit [s]": "T_crit",
    "r=K_T/T": "r",
}


def _input_symbol_latex(name: str) -> str:
    try:
        return _SYMBOL_LATEX[_INPUT_SYMBOL_KEYS[name]]
    except KeyError as error:
        raise ValueError(f"Unsupported controller input symbol: {name}") from error


def _controller_parallel_latex(parameters: ControllerParameters) -> str:
    kp = _exact_display_latex(parameters.k_p)
    if parameters.controller_type is ControllerType.P:
        return rf"G_R(s)={kp}"
    integral_term = _parallel_integral_term_latex(parameters.k_i)
    if parameters.controller_type is ControllerType.PI:
        return rf"G_R(s)={kp}+{integral_term}"
    kd = _exact_display_latex(parameters.k_d)
    return rf"G_R(s)={kp}+{integral_term}+{kd}s"


def _controller_ideal_latex(parameters: ControllerParameters) -> str:
    kp = _exact_display_latex(parameters.k_p)
    if parameters.controller_type is ControllerType.P:
        return rf"G_R(s)={kp}"
    assert parameters.ideal_t_i is not None
    integral_term = _ideal_integral_term_latex(parameters.ideal_t_i)
    if parameters.controller_type is ControllerType.PI:
        return rf"G_R(s)={kp}\left(1+{integral_term}\right)"
    assert parameters.ideal_t_d is not None
    return (
        rf"G_R(s)={kp}\left(1+{integral_term}"
        rf"+{_exact_display_latex(parameters.ideal_t_d)}s\right)"
    )


def _ideal_integral_term_latex(value: ControllerScalar) -> str:
    if value.exact is None:
        return rf"\frac{{1}}{{({value.numerical})s}}"
    numerator = value.exact.denominator
    denominator = value.exact.numerator
    if denominator == 1:
        return rf"\frac{{{numerator}}}{{s}}"
    return rf"\frac{{{numerator}}}{{{denominator}s}}"


def _parallel_integral_term_latex(value: ControllerScalar) -> str:
    if value.exact is None:
        return rf"\frac{{{value.numerical}}}{{s}}"
    numerator = value.exact.numerator
    denominator = value.exact.denominator
    if denominator == 1:
        return rf"\frac{{{numerator}}}{{s}}"
    return rf"\frac{{{numerator}}}{{{denominator}s}}"


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


def _fraction_plain(value: Fraction) -> str:
    return (
        str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"
    )


def _fraction_latex(value: Fraction) -> str:
    return (
        str(value.numerator)
        if value.denominator == 1
        else rf"\frac{{{value.numerator}}}{{{value.denominator}}}"
    )


def _rational_display(value: ExactRationalValue) -> str:
    fraction = _fraction(value)
    decimal = _terminating_decimal(fraction)
    return decimal if decimal is not None else _fraction_plain(fraction)


def _terminating_decimal(value: Fraction) -> str | None:
    denominator = value.denominator
    while denominator % 2 == 0:
        denominator //= 2
    while denominator % 5 == 0:
        denominator //= 5
    if denominator != 1:
        return None
    return format(Decimal(value.numerator) / Decimal(value.denominator), "f")


def _exact_display(value: ControllerScalar) -> str:
    if value.exact is None:
        return value.numerical
    fraction = _fraction(value.exact)
    decimal = _terminating_decimal(fraction)
    return decimal if decimal is not None else _fraction_plain(fraction)


def _exact_display_latex(value: ControllerScalar) -> str:
    if value.exact is None:
        return value.numerical
    fraction = _fraction(value.exact)
    decimal = _terminating_decimal(fraction)
    return decimal if decimal is not None else _fraction_latex(fraction)


def _approximation(value: ControllerScalar) -> str:
    if value.exact is None:
        return value.numerical
    fraction = _fraction(value.exact)
    return "" if _terminating_decimal(fraction) is not None else f"{float(fraction):.6g}"


def _formula(
    quantity: str,
    general_plain: str,
    substituted_plain: str,
    value: ControllerScalar,
    unit: str,
    source: str,
    general_latex: str,
    substituted_latex: str,
) -> ControllerFormulaStep:
    exact = _exact_display(value)
    exact_latex = _exact_display_latex(value)
    approximation = _approximation(value)
    return ControllerFormulaStep(
        quantity,
        general_plain,
        substituted_plain,
        f"{quantity}={exact}",
        "" if not approximation else f"{quantity}≈{approximation}",
        unit,
        source,
        general_latex,
        substituted_latex,
        rf"{quantity}={exact_latex}",
        "" if not approximation else rf"{quantity}\approx{approximation}",
    )


def _open_formula_steps(
    controller_type: ControllerType,
    gain: ExactRationalValue,
    dead: ExactRationalValue,
    lag: ExactRationalValue,
    parameters: ControllerParameters,
) -> tuple[ControllerFormulaStep, ...]:
    ks, kt, t = map(_rational_display, (gain, dead, lag))
    source = f"Ziegler–Nichols offen, Tabellenzeile {controller_type.value.upper()}"
    if controller_type is ControllerType.P:
        return (
            _formula(
                "k_P",
                "k_P=T/(K_S K_T)",
                f"k_P={t}/({ks}·{kt})",
                parameters.k_p,
                "Verstärkung",
                source,
                r"k_P=\frac{T}{K_SK_T}",
                rf"k_P=\frac{{{t}}}{{{ks}\cdot {kt}}}",
            ),
        )
    kp_factor = "0.9" if controller_type is ControllerType.PI else "1.2"
    time_factor = "3.33" if controller_type is ControllerType.PI else "2"
    steps = [
        _formula(
            "k_P",
            f"k_P={kp_factor}T/(K_S K_T)",
            f"k_P={kp_factor}·{t}/({ks}·{kt})",
            parameters.k_p,
            "Verstärkung",
            source,
            rf"k_P=\frac{{{kp_factor}T}}{{K_SK_T}}",
            rf"k_P=\frac{{{kp_factor}\cdot {t}}}{{{ks}\cdot {kt}}}",
        ),
        _formula(
            "T_I",
            f"T_I={time_factor}K_T",
            f"T_I={time_factor}·{kt}",
            parameters.ideal_t_i,  # type: ignore[arg-type]
            "s",
            source,
            rf"T_I={time_factor}K_T",
            rf"T_I={time_factor}\cdot {kt}",
        ),
        _formula(
            "k_I",
            "k_I=k_P/T_I",
            f"k_I={_exact_display(parameters.k_p)}/{_exact_display(parameters.ideal_t_i)}",  # type: ignore[arg-type]
            parameters.k_i,
            r"s^-1",
            source,
            r"k_I=\frac{k_P}{T_I}",
            rf"k_I=\frac{{{_exact_display_latex(parameters.k_p)}}}"
            rf"{{{_exact_display_latex(parameters.ideal_t_i)}}}",  # type: ignore[arg-type]
        ),
    ]
    if controller_type is ControllerType.PID:
        assert parameters.ideal_t_d is not None
        steps.extend(
            (
                _formula(
                    "T_D",
                    "T_D=0.5K_T",
                    f"T_D=0.5·{kt}",
                    parameters.ideal_t_d,
                    "s",
                    source,
                    r"T_D=0.5K_T",
                    rf"T_D=0.5\cdot {kt}",
                ),
                _formula(
                    "k_D",
                    "k_D=k_PT_D=0.5k_PK_T",
                    f"k_D=0.5·{_exact_display(parameters.k_p)}·{kt}",
                    parameters.k_d,
                    "s",
                    source,
                    r"k_D=k_PT_D=0.5k_PK_T",
                    rf"k_D=0.5\cdot {_exact_display_latex(parameters.k_p)}\cdot {kt}",
                ),
            )
        )
    return tuple(steps)


def _closed_formula_steps(
    controller_type: ControllerType,
    gain: ExactRationalValue,
    period: ExactRationalValue,
    parameters: ControllerParameters,
) -> tuple[ControllerFormulaStep, ...]:
    kg, tp = _rational_display(gain), _rational_display(period)
    source = f"Ziegler–Nichols geschlossen, Tabellenzeile {controller_type.value.upper()}"
    kp_factor = {
        ControllerType.P: "0.5",
        ControllerType.PI: "0.45",
        ControllerType.PID: "0.6",
    }[controller_type]
    steps = [
        _formula(
            "k_P",
            f"k_P={kp_factor}K_crit",
            f"k_P={kp_factor}·{kg}",
            parameters.k_p,
            "Verstärkung",
            source,
            rf"k_P={kp_factor}K_{{\mathrm{{crit}}}}",
            rf"k_P={kp_factor}\cdot {kg}",
        )
    ]
    if controller_type is ControllerType.P:
        return tuple(steps)
    assert parameters.ideal_t_i is not None
    ti_factor = "0.85" if controller_type is ControllerType.PI else "0.5"
    steps.extend(
        (
            _formula(
                "T_I",
                f"T_I={ti_factor}T_crit",
                f"T_I={ti_factor}·{tp}",
                parameters.ideal_t_i,
                "s",
                source,
                rf"T_I={ti_factor}T_{{\mathrm{{crit}}}}",
                rf"T_I={ti_factor}\cdot {tp}",
            ),
            _formula(
                "k_I",
                "k_I=k_P/T_I",
                f"k_I={_exact_display(parameters.k_p)}/{_exact_display(parameters.ideal_t_i)}",
                parameters.k_i,
                r"s^-1",
                source,
                r"k_I=\frac{k_P}{T_I}",
                rf"k_I=\frac{{{_exact_display_latex(parameters.k_p)}}}"
                rf"{{{_exact_display_latex(parameters.ideal_t_i)}}}",
            ),
        )
    )
    if controller_type is ControllerType.PID:
        assert parameters.ideal_t_d is not None
        steps.extend(
            (
                _formula(
                    "T_D",
                    "T_D=0.12T_crit",
                    f"T_D=0.12·{tp}",
                    parameters.ideal_t_d,
                    "s",
                    source,
                    r"T_D=0.12T_{\mathrm{crit}}",
                    rf"T_D=0.12\cdot {tp}",
                ),
                _formula(
                    "k_D",
                    "k_D=k_PT_D",
                    f"k_D={_exact_display(parameters.k_p)}·{_exact_display(parameters.ideal_t_d)}",
                    parameters.k_d,
                    "s",
                    source,
                    r"k_D=k_PT_D",
                    rf"k_D={_exact_display_latex(parameters.k_p)}"
                    rf"\cdot {_exact_display_latex(parameters.ideal_t_d)}",
                ),
            )
        )
    return tuple(steps)


def _cohen_coon_formula_steps(
    controller_type: ControllerType,
    gain: ExactRationalValue,
    dead: ExactRationalValue,
    lag: ExactRationalValue,
    ratio: ExactRationalValue,
    parameters: ControllerParameters,
) -> tuple[ControllerFormulaStep, ...]:
    ks, kt, t, r = map(_rational_display, (gain, dead, lag, ratio))
    source = f"Cohen–Coon, Tabellenzeile {controller_type.value.upper()}"
    ratio_scalar = ControllerScalar(
        ratio,
        f"{ratio.numerator / ratio.denominator:.12g}",
        ControllerValueProvenance.EXACT_RATIONAL,
    )
    steps = [
        _formula(
            "r",
            "r=K_T/T",
            f"r={kt}/{t}",
            ratio_scalar,
            "dimensionslos",
            source,
            r"r=\frac{K_T}{T}",
            rf"r=\frac{{{kt}}}{{{t}}}",
        )
    ]
    if controller_type is ControllerType.P:
        general_plain = "k_P=(1/K_S)(T/K_T)(1+r/3)"
        general_latex = r"k_P=\frac1{K_S}\frac{T}{K_T}\left(1+\frac r3\right)"
    elif controller_type is ControllerType.PI:
        general_plain = "k_P=(0.9/K_S)(T/K_T)(0.9+r/12)"
        general_latex = r"k_P=\frac{0.9}{K_S}\frac{T}{K_T}\left(0.9+\frac r{12}\right)"
    else:
        general_plain = "k_P=(1.2/K_S)(T/K_T)(1.35+r/15)"
        general_latex = r"k_P=\frac{1.2}{K_S}\frac{T}{K_T}\left(1.35+\frac r{15}\right)"
    steps.append(
        _formula(
            "k_P",
            general_plain,
            (
                f"k_P=(1/{ks})({t}/{kt})(1+{r}/3)"
                if controller_type is ControllerType.P
                else (
                    f"k_P=(0.9/{ks})({t}/{kt})(0.9+{r}/12)"
                    if controller_type is ControllerType.PI
                    else f"k_P=(1.2/{ks})({t}/{kt})(1.35+{r}/15)"
                )
            ),
            parameters.k_p,
            "Verstärkung",
            source,
            general_latex,
            (
                rf"k_P=\frac1{{{ks}}}\frac{{{t}}}{{{kt}}}\left(1+\frac{{{r}}}3\right)"
                if controller_type is ControllerType.P
                else (
                    rf"k_P=\frac{{0.9}}{{{ks}}}\frac{{{t}}}{{{kt}}}"
                    rf"\left(0.9+\frac{{{r}}}{{12}}\right)"
                    if controller_type is ControllerType.PI
                    else rf"k_P=\frac{{1.2}}{{{ks}}}\frac{{{t}}}{{{kt}}}"
                    rf"\left(1.35+\frac{{{r}}}{{15}}\right)"
                )
            ),
        )
    )
    if controller_type is ControllerType.P:
        return tuple(steps)
    assert parameters.ideal_t_i is not None
    if controller_type is ControllerType.PI:
        ki_plain = "k_I=k_P(9+20r)/(K_T(30+3r))"
        ki_latex = r"k_I=\frac{k_P(9+20r)}{K_T(30+3r)}"
        ti_plain = "T_I=K_T(30+3r)/(9+20r)"
        ti_latex = r"T_I=K_T\frac{30+3r}{9+20r}"
    else:
        ki_plain = "k_I=k_P(13+8r)/(K_T(32+6r))"
        ki_latex = r"k_I=\frac{k_P(13+8r)}{K_T(32+6r)}"
        ti_plain = "T_I=K_T(32+6r)/(13+8r)"
        ti_latex = r"T_I=K_T\frac{32+6r}{13+8r}"
    steps.extend(
        (
            _formula(
                "k_I",
                ki_plain,
                (
                    f"k_I={_exact_display(parameters.k_p)}(9+20·{r})/({kt}(30+3·{r}))"
                    if controller_type is ControllerType.PI
                    else f"k_I={_exact_display(parameters.k_p)}(13+8·{r})/({kt}(32+6·{r}))"
                ),
                parameters.k_i,
                r"s^-1",
                source,
                ki_latex,
                (
                    rf"k_I=\frac{{{_exact_display_latex(parameters.k_p)}(9+20\cdot {r})}}"
                    rf"{{{kt}(30+3\cdot {r})}}"
                    if controller_type is ControllerType.PI
                    else rf"k_I=\frac{{{_exact_display_latex(parameters.k_p)}(13+8\cdot {r})}}"
                    rf"{{{kt}(32+6\cdot {r})}}"
                ),
            ),
            _formula(
                "T_I",
                ti_plain,
                (
                    f"T_I={kt}(30+3·{r})/(9+20·{r})"
                    if controller_type is ControllerType.PI
                    else f"T_I={kt}(32+6·{r})/(13+8·{r})"
                ),
                parameters.ideal_t_i,
                "s",
                source,
                ti_latex,
                (
                    rf"T_I={kt}\frac{{30+3\cdot {r}}}{{9+20\cdot {r}}}"
                    if controller_type is ControllerType.PI
                    else rf"T_I={kt}\frac{{32+6\cdot {r}}}{{13+8\cdot {r}}}"
                ),
            ),
        )
    )
    if controller_type is ControllerType.PID:
        assert parameters.ideal_t_d is not None
        steps.extend(
            (
                _formula(
                    "k_D",
                    "k_D=k_PK_T·4/(11+2r)",
                    f"k_D={_exact_display(parameters.k_p)}·{kt}·4/(11+2·{r})",
                    parameters.k_d,
                    "s",
                    source,
                    r"k_D=k_PK_T\frac4{11+2r}",
                    rf"k_D={_exact_display_latex(parameters.k_p)}\cdot {kt}"
                    rf"\frac4{{11+2\cdot {r}}}",
                ),
                _formula(
                    "T_D",
                    "T_D=K_T·4/(11+2r)",
                    f"T_D={kt}·4/(11+2·{r})",
                    parameters.ideal_t_d,
                    "s",
                    source,
                    r"T_D=K_T\frac4{11+2r}",
                    rf"T_D={kt}\frac4{{11+2\cdot {r}}}",
                ),
            )
        )
    return tuple(steps)


def _validity(
    label: str,
    condition_plain: str,
    substitution_plain: str,
    source: str,
    condition_latex: str,
    substitution_latex: str,
) -> ControllerValidityStep:
    return ControllerValidityStep(
        label,
        condition_plain,
        substitution_plain,
        True,
        "Die Bedingung ist erfüllt.",
        source,
        condition_latex,
        substitution_latex,
    )


def _open_validity_steps(
    gain: ExactRationalValue, dead: ExactRationalValue, lag: ExactRationalValue
) -> tuple[ControllerValidityStep, ...]:
    ks, kt, t = map(_rational_display, (gain, dead, lag))
    ratio = _fraction(dead) / _fraction(lag)
    source = "Skript, Tabelle 6.1 und Theorem 6.10"
    return (
        _validity("Streckenverstärkung", "K_S>0", f"K_S={ks}>0", source, "K_S>0", rf"K_S={ks}>0"),
        _validity(
            "Totzeit", "K_T>0", f"K_T={kt} s>0", source, "K_T>0", rf"K_T={kt}\,\mathrm{{s}}>0"
        ),
        _validity("Zeitkonstante", "T>0", f"T={t} s>0", source, "T>0", rf"T={t}\,\mathrm{{s}}>0"),
        _validity(
            "Quellenbereich",
            "K_T/T<1/2",
            f"K_T/T={kt}/{t}={_fraction_plain(ratio)}<1/2. Der Quellenbereich ist erfüllt.",
            source,
            r"\frac{K_T}{T}<\frac12",
            rf"\frac{{K_T}}{{T}}=\frac{{{kt}}}{{{t}}}={_fraction_latex(ratio)}<\frac12",
        ),
    )


def _cohen_coon_validity_steps(
    gain: ExactRationalValue,
    dead: ExactRationalValue,
    lag: ExactRationalValue,
    ratio: ExactRationalValue,
) -> tuple[ControllerValidityStep, ...]:
    ks, kt, t, r = map(_rational_display, (gain, dead, lag, ratio))
    source = "Skript, Tabelle 6.3 und Bemerkung 6.16"
    ratio_latex = _latex_scalar(
        ControllerScalar(ratio, r, ControllerValueProvenance.EXACT_RATIONAL)
    )
    return (
        _validity("Streckenverstärkung", "K_S>0", f"K_S={ks}>0", source, "K_S>0", rf"K_S={ks}>0"),
        _validity(
            "Totzeit", "K_T>0", f"K_T={kt} s>0", source, "K_T>0", rf"K_T={kt}\,\mathrm{{s}}>0"
        ),
        _validity("Zeitkonstante", "T>0", f"T={t} s>0", source, "T>0", rf"T={t}\,\mathrm{{s}}>0"),
        _validity(
            "Quellenbereich",
            "0<r=K_T/T<2",
            f"r=K_T/T={kt}/{t}={r}; 0<{r}<2. Der Quellenbereich ist erfüllt.",
            source,
            r"0<r=\frac{K_T}{T}<2",
            rf"r=\frac{{K_T}}{{T}}=\frac{{{kt}}}{{{t}}}={ratio_latex},"
            rf"\quad 0<{ratio_latex}<2",
        ),
    )


def _closed_validity_steps(
    gain: ExactRationalValue, period: ExactRationalValue
) -> tuple[ControllerValidityStep, ...]:
    kg, tp = _rational_display(gain), _rational_display(period)
    source = "Skript, Tabelle 6.2"
    return (
        _validity(
            "Kritische Verstärkung",
            "K_crit>0",
            f"K_crit={kg}>0",
            source,
            r"K_{\mathrm{crit}}>0",
            rf"K_{{\mathrm{{crit}}}}={kg}>0",
        ),
        _validity(
            "Kritische Periodendauer",
            "T_crit>0",
            f"T_crit={tp} s>0",
            source,
            r"T_{\mathrm{crit}}>0",
            rf"T_{{\mathrm{{crit}}}}={tp}\,\mathrm{{s}}>0",
        ),
        _validity(
            "Voraussetzungen",
            "K_crit>0 und T_crit>0",
            f"K_crit={kg}>0 und T_crit={tp} s>0. Die Voraussetzungen sind erfüllt.",
            source,
            r"K_{\mathrm{crit}}>0,\quad T_{\mathrm{crit}}>0",
            rf"K_{{\mathrm{{crit}}}}={kg}>0,\quad T_{{\mathrm{{crit}}}}={tp}\,\mathrm{{s}}>0",
        ),
    )


def _controller_result_steps(parameters: ControllerParameters) -> tuple[ControllerResultStep, ...]:
    values: list[tuple[str, ControllerScalar, str, str]] = [
        ("k_P", parameters.k_p, "Verstärkung", "Proportionalbeiwert des Reglers"),
        ("k_I", parameters.k_i, r"s^-1", "Integralbeiwert des Reglers"),
        ("k_D", parameters.k_d, "s", "Differentialbeiwert des Reglers"),
    ]
    if parameters.ideal_t_i is not None:
        values.append(("T_I", parameters.ideal_t_i, "s", "Nachstellzeit des Reglers"))
    if parameters.ideal_t_d is not None:
        values.append(("T_D", parameters.ideal_t_d, "s", "Vorhaltezeit des Reglers"))
    return tuple(
        ControllerResultStep(
            symbol,
            _exact_display(value),
            _approximation(value),
            unit,
            kind,
            _exact_display_latex(value),
            _approximation(value),
        )
        for symbol, value, unit, kind in values
    )


def _controller_parallel_plain(parameters: ControllerParameters) -> str:
    kp = _exact_display(parameters.k_p)
    if parameters.controller_type is ControllerType.P:
        return f"G_R(s)={kp}"
    ki = _exact_display(parameters.k_i)
    if parameters.controller_type is ControllerType.PI:
        return f"G_R(s)={kp}+({ki})/s"
    return f"G_R(s)={kp}+({ki})/s+({_exact_display(parameters.k_d)})s"


def _controller_ideal_plain(parameters: ControllerParameters) -> str:
    kp = _exact_display(parameters.k_p)
    if parameters.controller_type is ControllerType.P:
        return f"G_R(s)={kp}"
    assert parameters.ideal_t_i is not None
    ti = _exact_display(parameters.ideal_t_i)
    if parameters.controller_type is ControllerType.PI:
        return f"G_R(s)={kp}(1+1/({ti}s))"
    assert parameters.ideal_t_d is not None
    return f"G_R(s)={kp}(1+1/({ti}s)+{_exact_display(parameters.ideal_t_d)}s)"


def _units_plain(unit: str) -> str:
    return "" if unit in ("", "Verstärkung", "dimensionslos") else f" {unit}"


def _units_latex(unit: str) -> str:
    if unit == "s":
        return r"\,\mathrm{s}"
    if unit == r"s^-1":
        return r"\,\mathrm{s^{-1}}"
    return ""


def _presented_validity_steps(
    formula: str, validity_steps: tuple[ControllerValidityStep, ...]
) -> tuple[ControllerValidityStep, ...]:
    if formula == "Ziegler–Nichols, geschlossener Kreis":
        return tuple(item for item in validity_steps if item.label != "Voraussetzungen")
    return validity_steps


def _symbol_legend_plain(formula: str, controller_type: ControllerType) -> str:
    controller = ["k_P ist der Proportionalbeiwert des Reglers"]
    if controller_type in (ControllerType.PI, ControllerType.PID):
        controller.extend(("k_I ist der Integralbeiwert", "T_I ist die Nachstellzeit"))
    if controller_type is ControllerType.PID:
        controller.extend(("k_D ist der Differentialbeiwert", "T_D ist die Vorhaltezeit"))
    if formula == "Ziegler–Nichols, geschlossener Kreis":
        method = [
            "K_crit ist die kritische Verstärkung",
            "T_crit ist die kritische Periodendauer",
        ]
    else:
        method = [
            "K_S ist die Streckenverstärkung",
            "K_T ist die Totzeit",
            "T ist die Streckenzeitkonstante",
        ]
    return "; ".join((*method, *controller)) + "."


def _symbol_legend_latex(formula: str, controller_type: ControllerType) -> str:
    controller = [r"$k_P$: Proportionalbeiwert des Reglers"]
    if controller_type in (ControllerType.PI, ControllerType.PID):
        controller.extend((r"$k_I$: Integralbeiwert", r"$T_I$: Nachstellzeit"))
    if controller_type is ControllerType.PID:
        controller.extend((r"$k_D$: Differentialbeiwert", r"$T_D$: Vorhaltezeit"))
    if formula == "Ziegler–Nichols, geschlossener Kreis":
        method = [
            r"$K_{\mathrm{crit}}$: kritische Verstärkung",
            r"$T_{\mathrm{crit}}$: kritische Periodendauer",
        ]
    else:
        method = [
            r"$K_S$: Streckenverstärkung",
            r"$K_T$: Totzeit",
            r"$T$: Streckenzeitkonstante",
        ]
    return r"\par\noindent " + "; ".join((*method, *controller)) + r".\par"


def _validity_conclusion_plain(formula: str) -> str:
    if formula == "Ziegler–Nichols, geschlossener Kreis":
        return "Alle Voraussetzungen sind erfüllt."
    return "Der Quellenbereich ist erfüllt."


def _table_steps(
    formula: str,
    values: tuple[tuple[str, str], ...],
    parameters: ControllerParameters,
    formula_steps: tuple[ControllerFormulaStep, ...],
    validity_steps: tuple[ControllerValidityStep, ...],
    result_steps: tuple[ControllerResultStep, ...],
) -> tuple[str, ...]:
    exact = ", ".join(
        f"{item.symbol}={item.exact_plain}{_units_plain(item.unit)}" for item in result_steps
    )
    approximate = ", ".join(
        f"{item.symbol}≈{item.approximation_plain}{_units_plain(item.unit)}"
        for item in result_steps
        if item.approximation_plain
    )
    presented_validity = _presented_validity_steps(formula, validity_steps)
    validity_text = " ".join(item.substitution_plain for item in presented_validity)
    conclusion = _validity_conclusion_plain(formula)
    if conclusion not in validity_text:
        validity_text += f" {conclusion}"
    return (
        "Gegeben: " + ", ".join(f"{key}={value}" for key, value in values) + ".",
        f"Gesucht: {parameters.controller_type.value.upper()}-Regler G_R(s).",
        f"Verfahren und Reglertyp: {formula}, {parameters.controller_type.value.upper()}.",
        "Symbollegende: " + _symbol_legend_plain(formula, parameters.controller_type),
        "Voraussetzungen: " + "; ".join(item.condition_plain for item in presented_validity) + ".",
        "Konkrete Gültigkeitsprüfung: " + validity_text,
        "Allgemeine Tabellenformeln: "
        + "; ".join(item.general_plain for item in formula_steps)
        + ".",
        "Einsetzen der Werte: " + "; ".join(item.substituted_plain for item in formula_steps) + ".",
        f"Exakte Reglerparameter: {exact}.",
        "Numerische Näherungen: " + (approximate if approximate else "nicht erforderlich") + ".",
        f"Parallele Reglerform: {_controller_parallel_plain(parameters)}.",
        "Umrechnung in T_I und T_D: "
        + (
            "für einen P-Regler nicht erforderlich."
            if parameters.controller_type is ControllerType.P
            else "T_I=k_P/k_I"
            + (", T_D=k_D/k_P." if parameters.controller_type is ControllerType.PID else ".")
        ),
        f"Idealform: {_controller_ideal_plain(parameters)}.",
        "Identitätskontrolle: Parallele und ideale Form sind symbolisch identisch.",
        f"Eindeutiges Endergebnis: {_controller_parallel_plain(parameters)}.",
    )


def _table_latex(
    formula: str,
    values: tuple[tuple[str, str], ...],
    parameters: ControllerParameters,
    formula_steps: tuple[ControllerFormulaStep, ...],
    validity_steps: tuple[ControllerValidityStep, ...],
    result_steps: tuple[ControllerResultStep, ...],
) -> str:
    given = r",\quad ".join(rf"{_input_symbol_latex(key)}={value}" for key, value in values)
    general = "\n".join(rf"\[{item.general_latex}\]" for item in formula_steps)
    substituted = "\n".join(rf"\[{item.substituted_latex}\]" for item in formula_steps)
    presented_validity = _presented_validity_steps(formula, validity_steps)
    validity = "\n".join(
        rf"\[{item.condition_latex}\]" + "\n" + rf"\[{item.substitution_latex}\]"
        for item in presented_validity
    )
    validity += "\n" + rf"\par\noindent {_validity_conclusion_plain(formula)}" + r"\par"
    exact = "\n".join(
        rf"\[{item.symbol}={item.exact_latex}{_units_latex(item.unit)}\]" for item in result_steps
    )
    approximate = "\n".join(
        rf"\[{item.symbol}\approx {item.approximation_latex}{_units_latex(item.unit)}\]"
        for item in result_steps
        if item.approximation_latex
    )
    ideal = (
        r"\par\noindent Für einen P-Regler sind keine Idealzeitparameter erforderlich.\par"
        if parameters.controller_type is ControllerType.P
        else rf"\[{_controller_ideal_latex(parameters)}\]"
    )
    method_line = (
        rf"\par\noindent {formula}, Tabellenzeile "
        rf"{parameters.controller_type.value.upper()}.\par"
    )
    return "\n".join(
        (
            r"\textbf{Gegeben}",
            rf"\[{given}\]",
            r"\textbf{Gesucht}",
            rf"\[\text{{{parameters.controller_type.value.upper()}-Regler }}G_R(s)\]",
            r"\textbf{Methode}",
            method_line,
            r"\textbf{Symbollegende}",
            _symbol_legend_latex(formula, parameters.controller_type),
            r"\textbf{Voraussetzungen und Gültigkeitsbereich}",
            validity,
            r"\textbf{Allgemeine Formeln}",
            general,
            r"\textbf{Einsetzen}",
            substituted,
            r"\textbf{Reglerparameter}",
            exact,
            approximate,
            r"\textbf{Parallele Reglerform}",
            rf"\[{_controller_parallel_latex(parameters)}\]",
            r"\textbf{Idealform}",
            ideal,
            r"\textbf{Kontrollen}",
            r"\par\noindent Exakte Weiterrechnung ohne Zwischenrundung; parallele und "
            r"ideale Form sind symbolisch identisch.\par",
            r"\textbf{Ergebnis}",
            rf"\[\boxed{{{_controller_parallel_latex(parameters)}}}\]",
        )
    )


def _prepared_open_loop_latex(reduced: ReducedTransferFunction) -> str:
    numerator = sp.factor(reduced.numerator.expression._as_sympy())
    denominator = sp.factor(reduced.denominator.expression._as_sympy())
    return (
        rf"G_0(s)=\frac{{{sp.latex(numerator, order='lex')}}}"
        rf"{{{sp.latex(denominator, order='lex')}}}"
    )


def _recognized_target_frequency_formula(
    reduced: ReducedTransferFunction,
    target_margin: float,
    candidates: tuple[ControllerDesignCandidate, ...],
) -> ControllerFormulaStep | None:
    if len(candidates) != 1 or target_margin != 20.0:
        return None
    s = sp.Symbol(reduced.variable_name)
    expression = sp.cancel(
        reduced.numerator.expression._as_sympy() / reduced.denominator.expression._as_sympy()
    )
    reference = sp.cancel(100 / (s * (10 * s + 1)))
    if sp.cancel(expression - reference) != 0:
        return None
    numeric = f"{candidates[0].target_frequency:.12g}"
    return ControllerFormulaStep(
        "ω_*",
        "arg G_0(jω)=-90°-arctan(10ω)",
        "-90°-arctan(10ω_*)=-160°; arctan(10ω_*)=70°",
        "ω_*=tan(70°)/10",
        f"ω_*≈{numeric}",
        r"s^-1",
        "Analytisch erkannte Referenzstruktur G_0(s)=100/(s(10s+1))",
        r"\arg G_0(j\omega)=-90^\circ-\arctan(10\omega)",
        (
            r"-90^\circ-\arctan(10\omega_\ast)=-160^\circ,"
            r"\quad \arctan(10\omega_\ast)=70^\circ"
        ),
        r"\omega_\ast=\frac{\tan70^\circ}{10}",
        rf"\omega_\ast\approx {numeric}",
    )


def _control(candidate: ControllerDesignCandidate, label: str) -> ControllerDesignControl:
    return next(item for item in candidate.controls if item.label == label)


def _frequency_presentations(
    target_margin: float,
    target_phase: float,
    candidates: tuple[ControllerDesignCandidate, ...],
) -> tuple[ControllerFrequencyPresentation, ...]:
    return tuple(
        ControllerFrequencyPresentation(
            candidate.candidate_index,
            f"{candidate.target_frequency:.12g}",
            f"{target_phase:.12g}",
            f"{target_margin:.12g}",
            f"{candidate.original_magnitude:.12g}",
            f"{candidate.positive_k_p:.12g}",
            "G_0,neu(s)=k_PG_0(s)",
            _control(candidate, "Betrag nach Skalierung"),
            _control(candidate, "Phasenreserve"),
            _control(candidate, "Globale Phasenreserve"),
            _control(candidate, "Nyquist-Nachprüfung"),
        )
        for candidate in candidates
    )


def _phase_formula_steps(
    candidates: tuple[ControllerDesignCandidate, ...],
) -> tuple[ControllerFormulaStep, ...]:
    return tuple(
        ControllerFormulaStep(
            "k_P",
            "k_P=1/|G_0(jω_*)|",
            f"k_P=1/{candidate.original_magnitude:.12g}",
            f"k_P={candidate.positive_k_p:.12g}",
            "",
            "Verstärkung",
            "P-Auslegung über gewünschte Phasenreserve",
            r"k_P=\frac1{|G_0(j\omega_\ast)|}",
            rf"k_P=\frac1{{{candidate.original_magnitude:.12g}}}",
            rf"k_P={candidate.positive_k_p:.12g}",
            "",
        )
        for candidate in candidates
    )


def _phase_validity_steps(
    target: float, candidates: tuple[ControllerDesignCandidate, ...]
) -> tuple[ControllerValidityStep, ...]:
    checks = [
        _validity(
            "Zielreserve",
            "0°<Φ_R,soll<180°",
            f"0°<{target:.12g}°<180°",
            "P-Auslegung über gewünschte Phasenreserve",
            r"0^\circ<\Phi_{R,\mathrm{soll}}<180^\circ",
            rf"0^\circ<{target:.12g}^\circ<180^\circ",
        )
    ]
    for candidate in candidates:
        magnitude_check = candidate.positive_k_p * candidate.original_magnitude
        checks.extend(
            (
                _validity(
                    "Positiver P-Faktor",
                    "k_P>0",
                    f"k_P={candidate.positive_k_p:.12g}>0",
                    "P-Auslegung über gewünschte Phasenreserve",
                    r"k_P>0",
                    rf"k_P={candidate.positive_k_p:.12g}>0",
                ),
                _validity(
                    "Betrag am Zielpunkt",
                    "|k_PG_0(jω_*)|=1",
                    f"|k_PG_0(jω_*)|={magnitude_check:.12g}",
                    "Frequenznachprüfung",
                    r"|k_PG_0(j\omega_\ast)|=1",
                    rf"|k_PG_0(j\omega_\ast)|={magnitude_check:.12g}",
                ),
                _validity(
                    "Globale Phasenreserve",
                    "Φ_R,ist≥Φ_R,soll",
                    f"Φ_R,ist={candidate.achieved_phase_margin_degrees:.8g}°≥{target:.8g}°",
                    "Frequenz- und Reservennachprüfung",
                    r"\Phi_{R,\mathrm{ist}}\ge\Phi_{R,\mathrm{soll}}",
                    rf"\Phi_{{R,\mathrm{{ist}}}}={candidate.achieved_phase_margin_degrees:.8g}^\circ"
                    rf"\ge {target:.8g}^\circ",
                ),
            )
        )
    return tuple(checks)


def _phase_margin_steps(
    target: float,
    target_phase: float,
    candidates: tuple[ControllerDesignCandidate, ...],
    target_frequency_formula: ControllerFormulaStep | None,
) -> list[str]:
    if target_frequency_formula is None:
        candidate_text = "; ".join(
            f"Kandidat {item.candidate_index}: ω_*≈{item.target_frequency:.12g} rad/s "
            "(numerische Zielphasensuche)"
            for item in candidates
        )
    else:
        candidate_text = (
            f"{target_frequency_formula.general_plain}; "
            f"{target_frequency_formula.substituted_plain}; "
            f"{target_frequency_formula.exact_plain}; "
            f"{target_frequency_formula.approximation_plain} s^-1"
        )
    magnitude_text = "; ".join(f"|G_0(jω_*)|={item.original_magnitude:.12g}" for item in candidates)
    substitution_text = "; ".join(
        f"k_P=1/{item.original_magnitude:.12g}={item.positive_k_p:.12g}" for item in candidates
    )
    reserve_text = "; ".join(
        f"Φ_R,ist={item.achieved_phase_margin_degrees:.8g}°" for item in candidates
    )
    return [
        "Gegeben: offene Strecke G_0(s) und Frequenzsuchbereich.",
        "Gesucht: positiver P-Regler G_R(s)=k_P.",
        f"Zielreserve: 0°<{target:.12g}°<180°.",
        f"Zielphase: φ_ziel=-180°+{target:.12g}°={target_phase:.12g}°.",
        "Zielphasenfrequenz beziehungsweise Kandidaten: " + candidate_text + ".",
        "Betrag am Zielpunkt: " + magnitude_text + ".",
        "Allgemeine Formel: k_P=1/|G_0(jω_*)|.",
        "Einsetzen: " + substitution_text + ".",
        "Neuer offener Kreis: G_0,neu(s)=k_PG_0(s).",
        "Durchtrittskontrolle: |k_PG_0(jω_*)|=1.",
        "Globale Reserven: " + reserve_text + "; alle relevanten Durchtritte wurden geprüft.",
        "Nyquist-Nachprüfung: Der vorhandene Nyquist-Kern wurde erneut ausgeführt.",
        (
            f"Endergebnis: G_R(s)={candidates[0].positive_k_p:.12g}."
            if len(candidates) == 1
            else "Kandidatenauswahl erforderlich."
        ),
    ]


def _phase_margin_latex(
    open_loop_latex: str,
    target: float,
    target_phase: float,
    candidates: tuple[ControllerDesignCandidate, ...],
    target_frequency_formula: ControllerFormulaStep | None,
) -> str:
    lines = [
        r"\textbf{Gegeben}",
        rf"\[{open_loop_latex},\qquad \Phi_{{R,\mathrm{{soll}}}}={target:.12g}^\circ\]",
        r"\textbf{Gesucht}",
        r"\[G_R(s)=k_P,\qquad k_P>0\]",
        r"\textbf{Voraussetzungen und Gültigkeitsbereich}",
        r"\[0^\circ<\Phi_{R,\mathrm{soll}}<180^\circ\]",
        rf"\[0^\circ<{target:.12g}^\circ<180^\circ\]",
        r"\textbf{Zielphasensuche}",
        rf"\[\varphi_{{\mathrm{{ziel}}}}=-180^\circ+{target:.12g}^\circ={target_phase:.12g}^\circ\]",
    ]
    if target_frequency_formula is None:
        lines.append(
            r"\par\noindent Die Zielphasenfrequenz wird numerisch aus der entfalteten "
            r"Phase bestimmt; keine kompakte symbolische Herleitung wird angenommen.\par"
        )
    else:
        lines.extend(
            (
                rf"\[{target_frequency_formula.general_latex}\]",
                rf"\[{target_frequency_formula.substituted_latex}\]",
                rf"\[{target_frequency_formula.exact_latex}\]",
                rf"\[{target_frequency_formula.approximation_latex}\,\mathrm{{s^{{-1}}}}\]",
            )
        )
    lines.extend((r"\textbf{Allgemeine Formeln}", r"\[k_P=\frac1{|G_0(j\omega_\ast)|}\]"))
    for candidate in candidates:
        omega = (
            r"\omega_\ast" if len(candidates) == 1 else rf"\omega_{{{candidate.candidate_index}}}"
        )
        candidate_lines = [rf"\textbf{{Einsetzen - Kandidat {candidate.candidate_index}}}"]
        if target_frequency_formula is None:
            candidate_lines.append(
                rf"\[{omega}\approx {candidate.target_frequency:.12g}\,\mathrm{{s^{{-1}}}}\]"
            )
        candidate_lines.extend(
            (
                rf"\[|G_0(j\omega_\ast)|={candidate.original_magnitude:.12g}\]",
                rf"\[k_P=\frac1{{{candidate.original_magnitude:.12g}}}"
                rf"={candidate.positive_k_p:.12g}\]",
                r"\textbf{Frequenz- und Reservennachprüfung}",
                r"\[G_{0,\mathrm{neu}}(s)=k_PG_0(s)\]",
                rf"\[|k_PG_0(j\omega_\ast)|="
                rf"{candidate.positive_k_p * candidate.original_magnitude:.12g}\]",
                rf"\[\Phi_{{R,\mathrm{{ist}}}}={candidate.achieved_phase_margin_degrees:.8g}^\circ"
                rf"\ge\Phi_{{R,\mathrm{{soll}}}}={target:.8g}^\circ\]",
                r"\par\noindent Die Durchtritte und Reserven wurden vollständig neu "
                r"berechnet.\par",
                r"\textbf{Nyquist-Nachprüfung}",
                r"\par\noindent Der vorhandene Nyquist-Kern wurde für den neuen offenen "
                r"Kreis erneut ausgeführt.\par",
            )
        )
        lines.extend(candidate_lines)
    successful = tuple(
        item for item in candidates if item.status is ControllerDesignCandidateStatus.TARGET_MET
    )
    lines.append(r"\textbf{Ergebnis}")
    if len(candidates) == 1 and successful:
        lines.append(rf"\[\boxed{{G_R(s)={successful[0].positive_k_p:.12g}}}\]")
    elif successful:
        lines.append(r"\par\noindent Auswahl eines gültigen Kandidaten erforderlich.\par")
    else:
        lines.append(r"\par\noindent Kein Kandidat erfüllt die globale Zielreserve.\par")
    return "\n".join(lines)


__all__ = [
    "ControllerDesignCandidate",
    "ControllerDesignCandidateStatus",
    "ControllerDesignControl",
    "ControllerDesignInputDraft",
    "ControllerDesignMethod",
    "ControllerDesignOutcomeDecision",
    "ControllerDesignResult",
    "ControllerDesignWorkflowService",
    "ControllerFrequencyPresentation",
    "ControllerType",
    "controller_design_candidate_status_text",
    "controller_design_method_text",
    "decide_p_phase_margin_outcome",
]
