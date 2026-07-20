"""Pure LaTeX rendering of validated frequency-domain workflow results."""

from __future__ import annotations

import re

from klausurbotpro.application._frequency_domain_workflow_validation import (
    validate_frequency_domain_workflow_result,
)
from klausurbotpro.application._solution_report_formatting import (
    compact_decimal_text,
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
from klausurbotpro.domain import (
    DecibelValueKind,
    ExactExpression,
    ExactRationalValue,
    FrequencyResponsePoint,
    FrequencyResponsePointStatus,
)

_STATUS_LATEX = {
    FrequencyResponsePointStatus.DEFINED: r"\text{definiert}",
    FrequencyResponsePointStatus.ZERO_RESPONSE: r"\text{Nullantwort}",
    FrequencyResponsePointStatus.SINGULAR: r"\text{singulär}",
    FrequencyResponsePointStatus.SYMBOLIC_UNDETERMINED: (
        r"\text{symbolisch unbestimmt}"
    ),
    FrequencyResponsePointStatus.NUMERIC_UNDETERMINED: (
        r"\text{numerisch unbestimmt}"
    ),
}


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
        value
        for value in grid_request.explicit_frequencies
        if value not in added
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
    return "\n\n".join(
        (
            *given_lines,
            r"\section*{Wertetabelle}",
            table,
            *selected,
            *_unwrap_explanation(result, selected_index),
            *_singularity_lines(result, added_frequencies),
            *_workflow_notices(result),
        )
    )


def _transfer_function_equation(
    result: FrequencyDomainWorkflowResult,
    *,
    reduced: bool,
) -> str:
    assert result.preparation_result is not None
    value = (
        result.preparation_result.reduced_value
        if reduced
        else result.preparation_result.raw_value
    )
    label = (
        r"G_{\mathrm{red}}(s)"
        if reduced
        else r"G_{\mathrm{Eingabe}}(s)"
    )
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
        (
            f"{literal_text(assignment.parameter_name).latex}="
            f"{_rational_latex(assignment.value)}"
        )
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
            rf"\[\varphi({omega})={phase}^\circ\]",
            (
                rf"\[\boxed{{G({argument})={exact_value},\quad "
                rf"|G({argument})|\approx {magnitude},\quad "
                rf"L({omega})\approx {decibel}\,\mathrm{{dB}},\quad "
                rf"\varphi({omega})={phase}^\circ}}\]"
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
            _rational_latex(bode_point.evaluation_frequency),
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
        lines.append(
            rf"\[k(\omega_{{\mathrm{{ausgewählt}}}})={offset}\]"
        )
    return tuple(lines)


def _singularity_lines(
    result: FrequencyDomainWorkflowResult,
    added: tuple[ExactRationalValue, ...],
) -> tuple[str, ...]:
    assert result.bode_data_result is not None
    singular = tuple(
        point
        for point in result.bode_data_result.points
        if point.frequency_response_point.status
        is FrequencyResponsePointStatus.SINGULAR
    )
    if not singular and not added:
        return ()
    lines = [r"\section*{Singularitäten und Stützstellen}"]
    for point in singular:
        omega = _rational_latex(point.evaluation_frequency)
        denominator = _exact_latex(
            point.frequency_response_point.specialized_denominator
        )
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
    lines.extend(
        (
            r"\[\text{Hinweis:}\quad "
            rf"{literal_text(diagnostic.message).latex}\]"
        )
        for diagnostic in result.diagnostics
    )
    return tuple(lines)


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
        else r",\quad ".join(
            rf"{_rational_latex(value)}\,\mathrm{{rad/s}}"
            for value in values
        )
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
        and point.numerical_decibel.kind
        is DecibelValueKind.NEGATIVE_INFINITY
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
