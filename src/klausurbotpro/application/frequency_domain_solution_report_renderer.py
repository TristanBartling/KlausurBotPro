"""Pure LaTeX rendering of validated frequency-domain workflow results."""

from __future__ import annotations

import re
from decimal import ROUND_HALF_EVEN, Decimal

from klausurbotpro.application._frequency_domain_workflow_validation import (
    validate_frequency_domain_workflow_result,
)
from klausurbotpro.application._solution_report_formatting import (
    compact_decimal_text,
    descriptive_math,
    exact_expression,
    exact_rational,
    fraction,
    literal_text,
    transfer_pair,
)
from klausurbotpro.application.frequency_domain_workflow_contracts import (
    FrequencyDomainWorkflowLimits,
    FrequencyDomainWorkflowMode,
    FrequencyDomainWorkflowResult,
    FrequencyPhasePresentation,
)
from klausurbotpro.application.standard_element_bode_formatting import (
    standard_element_asymptote_latex,
    standard_element_decomposition_latex,
)
from klausurbotpro.domain import (
    DecibelValueKind,
    ExactExpression,
    ExactRationalValue,
    FrequencyResponsePoint,
    FrequencyResponsePointStatus,
    StandardElementBodeResult,
)

_STATUS_LATEX = {
    FrequencyResponsePointStatus.DEFINED: r"\text{definiert}",
    FrequencyResponsePointStatus.ZERO_RESPONSE: r"\text{Nullantwort}",
    FrequencyResponsePointStatus.SINGULAR: r"\text{singulär}",
    FrequencyResponsePointStatus.SYMBOLIC_UNDETERMINED: (r"\text{symbolisch unbestimmt}"),
    FrequencyResponsePointStatus.NUMERIC_UNDETERMINED: (r"\text{numerisch unbestimmt}"),
}

_PRESENTATION_STATUS_LABELS = {
    "complete_in_proven_range": "vollständig im nachgewiesenen Frequenzbereich",
    "band_limited": "auf den untersuchten Frequenzbereich begrenzt",
    "segment_incomplete": "mindestens ein Frequenzsegment ist unvollständig",
    "numerically_ambiguous": "numerisch nicht eindeutig",
    "complete": "vollständiges Nyquist-Kriterium",
    "simplified": "vereinfachtes Standard-Nyquist-Kriterium",
    "not_applicable": "nicht anwendbar",
}

_DEDUPLICATED_MESSAGE_MARKERS = (
    "Voraussetzungen des Standard-Nyquist-Kriteriums",
    "Das Kriterium ist für diesen Fall nicht direkt anwendbar",
    r"\text{Hinweis:}",
)


def render_frequency_domain_solution_latex(
    result: FrequencyDomainWorkflowResult,
    limits: FrequencyDomainWorkflowLimits,
    *,
    selected_bode_index: int = 0,
    added_frequencies: tuple[ExactRationalValue, ...] = (),
) -> str:
    """Render existing exact and numerical values without analyzing them again."""

    if type(result) is not FrequencyDomainWorkflowResult:
        raise TypeError("result must be a FrequencyDomainWorkflowResult.")
    if type(limits) is not FrequencyDomainWorkflowLimits:
        raise TypeError("limits must be FrequencyDomainWorkflowLimits.")
    if type(selected_bode_index) is not int or selected_bode_index < 0:
        raise ValueError("selected_bode_index must be a nonnegative int.")
    if type(added_frequencies) is not tuple or any(
        type(value) is not ExactRationalValue for value in added_frequencies
    ):
        raise TypeError("added_frequencies must contain exact rationals.")
    validate_frequency_domain_workflow_result(result, limits)
    if (
        result.request is None
        or result.preparation_result is None
        or result.preparation_result.raw_value is None
    ):
        return _unavailable_report(result)
    if result.request.mode is FrequencyDomainWorkflowMode.SINGLE_POINT:
        return _single_point_report(result)
    return _bode_report(
        result,
        selected_bode_index,
        added_frequencies,
    )


def _single_point_report(result: FrequencyDomainWorkflowResult) -> str:
    response = result.single_point_result
    if response is None or not response.points:
        return _unavailable_report(result)
    point = response.points[0]
    given = (
        r"\section*{Gegeben}",
        _transfer_function_equation(result, reduced=False),
        _substitutions_equation(result),
        rf"\[\omega={_rational_latex(point.omega)}\,\mathrm{{rad/s}}\]",
    )
    solution = (
        r"\section*{Lösung}",
        *_point_solution(point, numbered=True),
        *_workflow_notices(result),
    )
    return "\n\n".join((*given, *solution))


def _bode_report(
    result: FrequencyDomainWorkflowResult,
    selected_index: int,
    added_frequencies: tuple[ExactRationalValue, ...],
) -> str:
    assert result.request is not None
    grid_request = result.request.grid_request
    bode = result.bode_data_result
    if grid_request is None or bode is None:
        return _unavailable_report(result)
    if bode.points and selected_index >= len(bode.points):
        raise ValueError("selected_bode_index exceeds the Bode table.")
    added = frozenset(added_frequencies)
    original_explicit = tuple(
        value for value in grid_request.explicit_frequencies if value not in added
    )
    given_lines = (
        r"\section*{Numerische Bode-Auswertung}",
        r"\section*{Gegeben}",
        _transfer_function_equation(result, reduced=False),
        _transfer_function_equation(result, reduced=True),
        _substitutions_equation(result),
        (
            rf"\[\omega_{{\min}}={_rational_latex(grid_request.omega_min)},\quad "
            rf"\omega_{{\max}}={_rational_latex(grid_request.omega_max)}"
            r"\,\mathrm{rad/s}\]"
        ),
        rf"\[\text{{Punkte pro Dekade}}={grid_request.points_per_decade}\]",
        _frequency_list(
            "Explizite Frequenzen",
            original_explicit,
        ),
        _frequency_list(
            "Automatisch ergänzte Stützstellen",
            added_frequencies,
        ),
        (
            r"\[\text{Phasendarstellung: Hauptphase und entfaltete Phase}\]"
            if result.request.phase_presentation
            is FrequencyPhasePresentation.PRINCIPAL_AND_UNWRAPPED
            else r"\[\text{Phasendarstellung: Hauptphase}\]"
        ),
        r"\section*{Ansatz}",
        r"\[s=\mathrm{j}\omega\]",
        r"\[G(\mathrm{j}\omega)=G(s)\big|_{s=\mathrm{j}\omega}\]",
    )
    table = _bode_table(result)
    selected = (
        ()
        if not bode.points
        else (
            r"\section*{Ausgewählter Tabellenpunkt}",
            *_point_solution(
                bode.points[selected_index].frequency_response_point,
                numbered=True,
            ),
        )
    )
    report_lines = (
        *given_lines,
        *_standard_element_section(result),
        r"\section*{Wertetabelle}",
        table,
        *selected,
        *_unwrap_explanation(result, selected_index),
        *_reserve_section(result),
        *_nyquist_section(result),
        *_singularity_lines(result, added_frequencies),
        *_workflow_notices(result),
    )
    return "\n\n".join(_deduplicate_normal_messages(report_lines))


def _standard_element_section(
    result: FrequencyDomainWorkflowResult,
) -> tuple[str, ...]:
    analysis = result.standard_element_bode_result
    if analysis is None:
        return ()
    heading = r"\section*{Standardglieder und asymptotischer Betrag}"
    if not analysis.supported:
        message = analysis.diagnostics[0].message
        return (
            heading,
            ("\\[\\text{Standardglieder-MVP: nicht unterst\u00fctzt}\\]"),
            rf"\[{descriptive_math(f'Grund: {message}').latex}\]",
            descriptive_math(
                "Die vollständige Standardgliederanalyse wurde deshalb nicht "
                "fortgesetzt.",
                latex=(
                    r"\noindent Die vollständige Standardgliederanalyse wurde "
                    r"deshalb nicht fortgesetzt.\par"
                ),
            ).latex,
            descriptive_math(
                "Weiter verwendbar bleiben die numerische Wertetabelle, der exakte "
                "Bode-Verlauf und die bereits bestimmten Frequenzgangwerte.",
                latex=(
                    r"\noindent Weiter verwendbar bleiben die numerische "
                    r"Wertetabelle, der exakte Bode-Verlauf und die bereits "
                    r"bestimmten Frequenzgangwerte.\par"
                ),
            ).latex,
        )
    assert analysis.gain is not None
    assert analysis.initial_slope_db_per_decade is not None
    gain = exact_expression(analysis.gain).latex
    lines = [
        heading,
        rf"\[{standard_element_decomposition_latex(analysis)}\]",
        rf"\[K={gain}\]",
        (
            r"\[n_{z0}="
            f"{analysis.origin_zero_multiplicity}"
            r",\quad n_{p0}="
            f"{analysis.origin_pole_multiplicity}"
            r"\]"
        ),
        (
            r"\[m_{\mathrm{Start}}="
            f"{analysis.initial_slope_db_per_decade}"
            r"\,\mathrm{dB/Dekade}\]"
        ),
        *_standard_element_event_table(analysis),
        rf"\[{standard_element_asymptote_latex(analysis)}\]",
        "\\[\\text{Exakte Rekonstruktion: best\u00e4tigt}\\]",
    ]
    return tuple(lines)


def _standard_element_event_table(
    analysis: StandardElementBodeResult,
) -> tuple[str, ...]:
    if not analysis.corner_events:
        return (r"\[\text{Knickereignisse: keine}\]",)
    rows = [
        r"\[",
        r"\begin{array}{r r r r r}",
        (
            r"\omega_k\,[\mathrm{rad/s}] & m_z & m_p & "
            r"\Delta m\,[\mathrm{dB/Dekade}] & "
            r"m_{\mathrm{danach}}\,[\mathrm{dB/Dekade}]\\"
        ),
        r"\hline",
    ]
    rows.extend(
        (
            f"{exact_expression(event.corner_frequency).latex} & "
            f"{event.zero_multiplicity} & {event.pole_multiplicity} & "
            f"{event.slope_change_db_per_decade} & "
            f"{event.slope_after_db_per_decade}\\\\"
        )
        for event in analysis.corner_events
    )
    rows.extend((r"\end{array}", r"\]"))
    return ("\n".join(rows),)


def _transfer_function_equation(
    result: FrequencyDomainWorkflowResult,
    *,
    reduced: bool,
) -> str:
    assert result.preparation_result is not None
    value = (
        result.preparation_result.reduced_value if reduced else result.preparation_result.raw_value
    )
    label = r"G_{\mathrm{red}}(s)" if reduced else r"G_{\mathrm{Eingabe}}(s)"
    if value is None:
        return rf"\[{label}=\text{{nicht verfügbar}}\]"
    pair = transfer_pair(
        value.numerator.expression,
        value.denominator.expression,
    )
    return rf"\[{label}={fraction(pair).latex}\]"


def _substitutions_equation(result: FrequencyDomainWorkflowResult) -> str:
    substitutions = result.substitutions
    if substitutions is None or not substitutions.assignments:
        return r"\[\text{Parameterbelegungen: keine}\]"
    values = r",\quad ".join(
        (f"{literal_text(assignment.parameter_name).latex}={_rational_latex(assignment.value)}")
        for assignment in substitutions.assignments
    )
    return rf"\[\text{{Parameterbelegungen:}}\quad {values}\]"


def _point_solution(
    point: FrequencyResponsePoint,
    *,
    numbered: bool,
) -> tuple[str, ...]:
    omega = _rational_latex(point.omega)
    argument = (
        r"\mathrm{j}"
        if point.omega == ExactRationalValue(1)
        else rf"\mathrm{{j}}\cdot {_rational_latex(point.omega)}"
    )
    prefix = "1. " if numbered else ""
    lines: list[str] = [
        rf"\textbf{{{prefix}Einsetzen von $s=\mathrm{{j}}\omega$:}}",
        (
            rf"\[G({argument})="
            rf"\frac{{{_exact_latex(point.specialized_numerator)}}}"
            rf"{{{_exact_latex(point.specialized_denominator)}}}\]"
        ),
    ]
    status = point.status
    if status is FrequencyResponsePointStatus.SINGULAR:
        lines.extend(
            (
                r"\textbf{2. Singularität:}",
                (
                    rf"\[N({argument})="
                    rf"{_exact_latex(point.specialized_denominator)}=0\]"
                ),
                (
                    rf"\[\omega_s={omega}\,\mathrm{{rad/s}}"
                    rf"\Rightarrow G({argument})\text{{ ist singulär.}}\]"
                ),
                r"\[\boxed{\text{Keine endlichen Frequenzgangwerte definiert.}}\]",
            )
        )
        return tuple(lines)
    if status in (
        FrequencyResponsePointStatus.SYMBOLIC_UNDETERMINED,
        FrequencyResponsePointStatus.NUMERIC_UNDETERMINED,
    ):
        lines.extend(
            (
                r"\textbf{2. Auswertungsstatus:}",
                rf"\[\text{{Punktstatus: }}{_STATUS_LATEX[status]}\]",
                (
                    r"\[\boxed{\text{Fehlende Werte sind nicht eindeutig "
                    r"bestimmbar; es werden keine Ersatzwerte gesetzt.}}\]"
                ),
            )
        )
        return tuple(lines)
    if status is FrequencyResponsePointStatus.ZERO_RESPONSE:
        lines.extend(
            (
                r"\textbf{2. Nullantwort:}",
                rf"\[G({argument})=0\]",
                rf"\[|G({argument})|=0,\qquad L({omega})=-\infty\,\mathrm{{dB}}\]",
                r"\[\varphi(\omega)\text{ ist nicht definiert.}\]",
                (
                    rf"\[\boxed{{G({argument})=0,\quad "
                    rf"L({omega})=-\infty\,\mathrm{{dB}},\quad "
                    r"\varphi\text{ nicht definiert}}\]"
                ),
            )
        )
        return tuple(lines)
    assert status is FrequencyResponsePointStatus.DEFINED
    exact_value = _optional_exact(point.exact_complex_value)
    real = _optional_exact(point.exact_real_part)
    imaginary = _optional_exact(point.exact_imaginary_part)
    magnitude_squared = _optional_exact(point.exact_magnitude_squared)
    magnitude = _compact(point.numerical_magnitude)
    decibel = _decibel_latex(point)
    phase = _compact(point.numerical_phase_degrees)
    lines.extend(
        (
            r"\textbf{2. Komplexen Wert darstellen:}",
            rf"\[G({argument})={exact_value}\]",
            (
                rf"\[\operatorname{{Re}}\{{G({argument})\}}={real},\qquad "
                rf"\operatorname{{Im}}\{{G({argument})\}}={imaginary}\]"
            ),
            r"\textbf{3. Betrag:}",
            rf"\[|G({argument})|^2={magnitude_squared}\]",
            rf"\[|G({argument})|\approx {magnitude}\]",
            r"\textbf{4. Dezibelwert:}",
            (
                rf"\[L({omega})=20\log_{{10}}|G({argument})|"
                rf"\approx {decibel}\,\mathrm{{dB}}\]"
            ),
            r"\textbf{5. Phase:}",
            rf"\[\varphi({omega})\approx {phase}^\circ\]",
            (
                rf"\[\boxed{{G({argument})={exact_value},\quad "
                rf"|G({argument})|\approx {magnitude},\quad "
                rf"L({omega})\approx {decibel}\,\mathrm{{dB}},\quad "
                rf"\varphi({omega})\approx {phase}^\circ}}\]"
            ),
        )
    )
    return tuple(lines)


def _bode_table(result: FrequencyDomainWorkflowResult) -> str:
    assert result.bode_data_result is not None
    unwrapped = _unwrapped_values(result)
    include_unwrapped = result.phase_unwrap_result is not None
    columns = "rlllll" if include_unwrapped else "rllll"
    header = (
        r"\omega\,[\mathrm{rad/s}] & \text{Status} & "
        r"|G(\mathrm{j}\omega)| & L(\omega)\,[\mathrm{dB}] & "
        r"\varphi_{\mathrm{H}}(\omega)\,[^\circ]"
    )
    if include_unwrapped:
        header += r" & \varphi_{\mathrm{entf}}(\omega)\,[^\circ]"
    rows = [
        r"\[",
        rf"\begin{{array}}{{{columns}}}",
        r"\hline",
        header + r"\\",
        r"\hline",
    ]
    for index, bode_point in enumerate(result.bode_data_result.points):
        point = bode_point.frequency_response_point
        values = (
            _table_frequency(bode_point.target_decimal.decimal_text),
            _STATUS_LATEX[point.status],
            _table_magnitude(point),
            _table_decibel(point),
            _table_phase(point.numerical_phase_degrees),
        )
        row = " & ".join(values)
        if include_unwrapped:
            row += " & " + _table_phase(unwrapped.get(index))
        rows.append(row + r"\\")
    rows.extend((r"\hline", r"\end{array}", r"\]"))
    return "\n".join(rows)


def _table_frequency(decimal_text: str) -> str:
    """Render one Bode-table target frequency with three significant digits."""

    number = Decimal(decimal_text)
    exponent = number.adjusted()
    quantum = Decimal(1).scaleb(exponent - 2)
    rounded = number.quantize(quantum, rounding=ROUND_HALF_EVEN)
    display_exponent = rounded.adjusted()
    if display_exponent >= 6 or display_exponent <= -4:
        mantissa, scientific_exponent = f"{rounded:.2E}".split("E")
        mantissa = mantissa.rstrip("0").rstrip(".")
        return rf"{mantissa}\cdot 10^{{{int(scientific_exponent)}}}"
    decimal_places = max(0, 2 - display_exponent)
    rendered = f"{rounded:.{decimal_places}f}"
    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")
    return rendered


def _unwrap_explanation(
    result: FrequencyDomainWorkflowResult,
    selected_index: int,
) -> tuple[str, ...]:
    unwrap = result.phase_unwrap_result
    if unwrap is None:
        return ()
    offsets = {
        point.grid_index: point.phase_offset_turns
        for segment in unwrap.segments
        for point in segment.points
    }
    lines = [
        r"\section*{Phasenentfaltung}",
        (
            r"\[\varphi_{\mathrm{entf}}(\omega)="
            r"\varphi_{\mathrm{H}}(\omega)+k(\omega)\cdot360^\circ\]"
        ),
        (
            r"\textit{Die entfaltete Phase ist dieselbe Winkelinformation "
            r"mit einem stetigkeitsgerechten Vielfachen von $360^\circ$; "
            r"sie ist keine zweite physikalische Phase.}"
        ),
    ]
    offset = offsets.get(selected_index, 0)
    if offset:
        lines.append(rf"\[k(\omega_{{\mathrm{{ausgewählt}}}})={offset}\]")
    return tuple(lines)


def _reserve_section(
    result: FrequencyDomainWorkflowResult,
) -> tuple[str, ...]:
    crossovers = result.crossover_analysis
    reserves = result.reserve_analysis
    if crossovers is None or reserves is None:
        return ()
    lines = [
        r"\section*{Durchtritte und Reserven}",
        rf"\[\mbox{{Bandstatus: {_presentation_status(crossovers.completeness.value)}}}\]",
        r"\[L(\omega_g)=0\,\mathrm{dB},\qquad "
        r"\mathrm{PM}=180^\circ+\varphi_{\mathrm{entf}}(\omega_g)\]",
    ]
    if crossovers.gain_crossovers:
        table = [
            r"\[\begin{array}{rllll}",
            r"\hline",
            r"\# & \omega_g & \varphi_{\mathrm{entf}}(\omega_g) & L(\omega_g) & \mathrm{PM}\\",
            r"\hline",
        ]
        for index, (item, reserve) in enumerate(
            zip(crossovers.gain_crossovers, reserves.phase_margins, strict=True), 1
        ):
            table.append(
                rf"{index} & {_table_frequency(str(item.frequency))} & "
                rf"{item.unwrapped_phase_degrees:.6g}^\circ & {item.decibel:.6g}\,\mathrm{{dB}} & "
                rf"{reserve.value:.6g}^\circ\\"
            )
        table.extend((r"\hline", r"\end{array}\]"))
        lines.append("\n".join(table))
    else:
        lines.append(r"\[\text{Phasenreserve nicht definiert: kein Amplitudendurchtritt.}\]")
    lines.append(
        r"\[\varphi_{\mathrm{entf}}(\omega_p)=-180^\circ-360^\circ m,\qquad "
        r"\mathrm{GM}_{\mathrm{dB}}=-L(\omega_p),\qquad "
        r"\mathrm{GM}=10^{\mathrm{GM}_{\mathrm{dB}}/20}=1/|G(\mathrm{j}\omega_p)|\]"
    )
    if crossovers.phase_crossovers:
        table = [
            r"\[\begin{array}{rrllll}",
            r"\hline",
            r"\# & m & \omega_p & \varphi_{\mathrm{entf}}(\omega_p) & "
            r"\mathrm{GM}_{\mathrm{dB}} & \mathrm{GM}\\",
            r"\hline",
        ]
        for index, item in enumerate(crossovers.phase_crossovers, 1):
            reserve_db = reserves.gain_margins_db[index - 1]
            factor = reserves.gain_margin_factors[index - 1]
            table.append(
                rf"{index} & {item.phase_branch_index} & {_table_frequency(str(item.frequency))} & "
                rf"{item.unwrapped_phase_degrees:.6g}^\circ & "
                rf"{reserve_db.value:.6g}\,\mathrm{{dB}} & "
                rf"{factor.value:.6g}\\"
            )
        table.extend((r"\hline", r"\end{array}\]"))
        lines.append("\n".join(table))
    else:
        interpretation = reserves.gain_margins_db[0].interpretation.value
        text = (
            "formal unbeschränkt: kein endlicher Phasendurchtritt"
            if interpretation == "formally_unbounded"
            else "nicht bestimmt: im untersuchten Band kein Phasendurchtritt"
        )
        lines.append(rf"\[\text{{Amplitudenreserve {text}.}}\]")
    if reserves.multiple_crossovers:
        lines.append(r"\[\text{Mehrere Durchtritte: alle Einzelreserven sind maßgeblich.}\]")
    return tuple(lines)


def _nyquist_section(result: FrequencyDomainWorkflowResult) -> tuple[str, ...]:
    analysis = result.nyquist_analysis
    if analysis is None:
        return ()
    poles = analysis.pole_classification
    winding = analysis.winding
    stability = analysis.stability
    n_cw = (
        r"\text{nicht bestimmt}"
        if stability.clockwise_encirclements is None
        else str(stability.clockwise_encirclements)
    )
    z = (
        r"\text{nicht bestimmt}"
        if stability.rhp_closed_poles is None
        else str(stability.rhp_closed_poles)
    )
    lhp_count = sum(item.multiplicity for item in poles.lhp_poles)
    imag_count = sum(item.multiplicity for item in poles.imaginary_axis_poles)
    prerequisites = "erfüllt" if stability.prerequisites_met else "nicht erfüllt"
    criterion = _presentation_status(stability.criterion.value)
    criterion_statement = (
        "Das Kriterium ist für diesen Fall nicht direkt anwendbar."
        if stability.criterion.value == "not_applicable"
        else f"Verwendetes Kriterium: {criterion}."
    )
    lines = [
        r"\section*{Nyquist-Analyse}",
        r"\[\text{Konvention: Uhrzeigersinn positiv,}\qquad Z=P+N_{\mathrm{cw}}\]",
        rf"\[P={stability.rhp_open_poles},\qquad N_{{\mathrm{{cw}}}}={n_cw},"
        rf"\qquad Z=P+N_{{\mathrm{{cw}}}}={z}\]",
        rf"\[\text{{Polklassifikation: LHP={lhp_count}, "
        rf"RHP={poles.rhp_pole_count}, j-Achse={imag_count}}}\]",
        rf"\[d_{{\min}}=\min_\omega |1+G(\mathrm{{j}}\omega)|="
        rf"{winding.critical_point.minimum_distance:.8g},\quad "
        rf"\omega={winding.critical_point.frequency:.8g}\,\mathrm{{rad/s}}\]",
        rf"\[\mbox{{Voraussetzungen des Standard-Nyquist-Kriteriums: "
        rf"{prerequisites}.}}\]",
        rf"\[\mbox{{{criterion_statement}}}\]",
        rf"\[\boxed{{\text{{{literal_text(stability.statement).latex}}}}}\]",
    ]
    gain = analysis.scalar_gain_range
    if gain is not None:
        interval_parts = []
        for item in gain.stable_intervals:
            lower = r"-\infty" if item.lower is None else f"{item.lower:.8g}"
            upper = r"\infty" if item.upper is None else f"{item.upper:.8g}"
            interval_parts.append(rf"\left({lower},{upper}\right)")
        intervals = r"\cup".join(interval_parts) or r"\varnothing"
        lines.extend((r"\section*{Skalarverstärkungsbereich}", rf"\[K\in {intervals}\]"))
    return tuple(lines)


def _singularity_lines(
    result: FrequencyDomainWorkflowResult,
    added: tuple[ExactRationalValue, ...],
) -> tuple[str, ...]:
    assert result.bode_data_result is not None
    singular = tuple(
        point
        for point in result.bode_data_result.points
        if point.frequency_response_point.status is FrequencyResponsePointStatus.SINGULAR
    )
    if not singular and not added:
        return ()
    lines = [r"\section*{Singularitäten und Stützstellen}"]
    for point in singular:
        omega = _rational_latex(point.evaluation_frequency)
        denominator = _exact_latex(point.frequency_response_point.specialized_denominator)
        lines.extend(
            (
                rf"\[\omega_s={omega}\,\mathrm{{rad/s}}\]",
                (
                    rf"\[N(\mathrm{{j}}\omega_s)={denominator}=0"
                    r"\Rightarrow G(\mathrm{j}\omega_s)"
                    r"\text{ ist singulär.}\]"
                ),
            )
        )
    if added:
        lines.append(
            _frequency_list(
                "Automatisch ergänzte numerische Stützstellen",
                added,
            )
        )
    return tuple(lines)


def _workflow_notices(
    result: FrequencyDomainWorkflowResult,
) -> tuple[str, ...]:
    if not result.diagnostics:
        return ()
    lines = [r"\section*{Workflow-Hinweise}"]
    messages = tuple(dict.fromkeys(diagnostic.message for diagnostic in result.diagnostics))
    lines.extend(
        (
            r"\[\text{Hinweis:}\quad "
            rf"{literal_text(message).latex}\]"
        )
        for message in messages
    )
    return tuple(lines)


def _presentation_status(value: str) -> str:
    return _PRESENTATION_STATUS_LABELS.get(value, "Status nicht verfügbar")


def _deduplicate_normal_messages(lines: tuple[str, ...]) -> tuple[str, ...]:
    unique: list[str] = []
    seen: set[str] = set()
    for line in lines:
        is_message = any(marker in line for marker in _DEDUPLICATED_MESSAGE_MARKERS)
        if is_message and line in seen:
            continue
        if is_message:
            seen.add(line)
        unique.append(line)
    return tuple(unique)


def _unavailable_report(result: FrequencyDomainWorkflowResult) -> str:
    notices = _workflow_notices(result)
    fallback = (
        r"\section*{Frequenzbereichslösung}",
        r"\[\text{Keine validierten Frequenzresultate verfügbar.}\]",
    )
    return "\n\n".join((*fallback, *notices))


def _frequency_list(
    label: str,
    values: tuple[ExactRationalValue, ...],
) -> str:
    rendered = (
        r"\text{keine}"
        if not values
        else r",\quad ".join(rf"{_rational_latex(value)}\,\mathrm{{rad/s}}" for value in values)
    )
    return rf"\[\text{{{label}:}}\quad {rendered}\]"


def _unwrapped_values(result: FrequencyDomainWorkflowResult) -> dict[int, str]:
    if result.phase_unwrap_result is None:
        return {}
    return {
        point.grid_index: point.unwrapped_phase_degrees
        for segment in result.phase_unwrap_result.segments
        for point in segment.points
    }


def _table_magnitude(point: FrequencyResponsePoint) -> str:
    if point.status is FrequencyResponsePointStatus.ZERO_RESPONSE:
        return "0"
    return _compact(point.numerical_magnitude) or "--"


def _table_decibel(point: FrequencyResponsePoint) -> str:
    if (
        point.numerical_decibel is not None
        and point.numerical_decibel.kind is DecibelValueKind.NEGATIVE_INFINITY
    ):
        return r"-\infty"
    return _decibel_latex(point) or "--"


def _table_phase(value: str | None) -> str:
    return _compact(value) or "--"


def _decibel_latex(point: FrequencyResponsePoint) -> str:
    value = point.numerical_decibel
    if value is None:
        return ""
    if value.kind is DecibelValueKind.NEGATIVE_INFINITY:
        return r"-\infty"
    return _compact(value.decimal_value)


def _rational_latex(value: ExactRationalValue) -> str:
    return exact_rational(value).latex


def _optional_exact(value: ExactExpression | None) -> str:
    if value is None:
        return r"\text{nicht definiert}"
    return _exact_latex(value)


def _exact_latex(value: ExactExpression) -> str:
    rendered = exact_expression(value).latex
    return re.sub(
        r"(?<![A-Za-z])i(?![A-Za-z])",
        r"\\mathrm{j}",
        rendered,
    )


def _compact(value: str | None) -> str:
    return "" if value is None else compact_decimal_text(value)


__all__ = ["render_frequency_domain_solution_latex"]
