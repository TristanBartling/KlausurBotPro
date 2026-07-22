"""Exact Routh consumer for canonical polynomial degree cases 1 through 4."""

from __future__ import annotations

import math

import sympy as sp

from klausurbotpro.domain.expression import ExactExpression
from klausurbotpro.domain.parameter_core import solve_parameter_conditions
from klausurbotpro.domain.parameter_core_contracts import (
    AnalysisTarget,
    AtomicParameterCondition,
    CancellationStatus,
    CanonicalCharacteristicPolynomial,
    ConditionOrigin,
    DegreeCaseKind,
    ParameterConditionProblem,
    ParameterRegion,
    PolynomialDegreeCase,
    PolynomialRole,
    Relation,
    SolveStatus,
)
from klausurbotpro.domain.routh_contracts import (
    RouthAnalysisResult,
    RouthCell,
    RouthDegreeCaseResult,
    RouthRow,
    RouthRowType,
    RouthSpecialCase,
)
from klausurbotpro.domain.stability_contracts import NumericalCheckStatus, NumericalPoleCheck
from klausurbotpro.domain.stability_numeric import check_numeric_poles
from klausurbotpro.domain.stability_presentation import (
    display_math,
    format_parameter_region_plain,
    latex_additive_equation,
    latex_conditions,
    latex_numerical_check,
    latex_parameter_region,
    paragraph,
)


def _exact(value: sp.Expr) -> ExactExpression:
    return ExactExpression._from_sympy(sp.sympify(value))


def analyze_routh(canonical: CanonicalCharacteristicPolynomial) -> RouthAnalysisResult:
    """Build Routh tables and delegate only generated conditions to the parameter core."""
    if canonical.status is not SolveStatus.SOLVED_EXACT:
        return RouthAnalysisResult(
            canonical,
            (),
            _concept(canonical),
            "",
            "Analyse ungültig.",
            "",
            (),
            "",
            canonical.diagnostics,
        )
    results = tuple(_analyze_case(canonical, case) for case in canonical.degree_cases)
    trusted = all(
        item.status not in (SolveStatus.INVALID_INPUT, SolveStatus.UNSUPPORTED)
        and not (
            item.numerical_check is not None
            and item.numerical_check.status is NumericalCheckStatus.INCONSISTENT
        )
        for item in results
    )
    combined = _combined_region(results, canonical.input.decision_parameters)
    statement = _overall_statement(canonical, results, combined, trusted)
    notice = ""
    if (
        canonical.input.role is PolynomialRole.REDUCED_TRANSFER_DENOMINATOR
        and canonical.input.cancellation_report is not None
        and canonical.input.cancellation_report.status
        is CancellationStatus.FACTORS_REMOVED
    ):
        notice = (
            "Der reduzierte E/A-Nenner beweist keine interne Stabilität. "
            "Entfernte instabile Dynamik kann verdeckt sein."
        )
    latex_source = _latex(canonical, results, notice) if trusted else ""
    return RouthAnalysisResult(
        canonical,
        results,
        _concept(canonical),
        combined,
        statement,
        notice,
        _worked_steps(canonical, results, statement, notice),
        latex_source,
        tuple(diagnostic for item in results for diagnostic in item.diagnostics),
    )


def _analyze_case(
    canonical: CanonicalCharacteristicPolynomial, case: PolynomialDegreeCase
) -> RouthDegreeCaseResult:
    empty = ParameterRegion(
        SolveStatus.UNSUPPORTED, "nicht unterstützt", r"\text{nicht unterstützt}"
    )
    if case.kind in (DegreeCaseKind.ZERO_POLYNOMIAL, DegreeCaseKind.CONSTANT_NONZERO):
        return _unsupported(case, empty, "Routh ist für Grad 0 nicht anwendbar.")
    if case.degree not in (1, 2, 3, 4):
        return _unsupported(case, empty, f"Grad {case.degree} wird nicht unterstützt.")

    rows, special = _build_rows(case)
    first_column = tuple(row.first_column for row in rows)
    parameters = canonical.input.decision_parameters
    full = tuple(
        AtomicParameterCondition(
            value,
            Relation.GT,
            ConditionOrigin.ROUTH_FIRST_COLUMN,
            parameters,
            f"{rows[index].power_label}: {value.canonical_text} > 0",
        )
        for index, value in enumerate(first_column)
    )
    solver = tuple(
        AtomicParameterCondition(
            _exact(_solver_first_column_expression(row)),
            Relation.GT,
            ConditionOrigin.ROUTH_FIRST_COLUMN,
            parameters,
            f"{row.power_label}: {_solver_first_column_expression(row)} > 0",
        )
        for row in rows
    )
    denominator_conditions = _denominator_conditions(rows, parameters)
    if special is not RouthSpecialCase.NONE:
        message = (
            "Null in der ersten Routh-Spalte; ε-Verfahren in diesem MVP nicht unterstützt."
            if special is RouthSpecialCase.ZERO_FIRST_COLUMN
            else "Vollständige Nullzeile; Hilfspolynomverfahren in diesem MVP nicht unterstützt."
        )
        return RouthDegreeCaseResult(
            case,
            rows,
            first_column,
            full + denominator_conditions,
            solver,
            empty,
            special,
            (),
            (),
            None,
            None,
            None,
            None,
            message,
            SolveStatus.UNSUPPORTED,
            (message,),
        )

    problem = ParameterConditionProblem(
        parameters,
        case.guard + solver,
        canonical.input.assumptions,
        canonical.input.exclusions + denominator_conditions,
    )
    region = solve_parameter_conditions(problem)
    point = _control_point(parameters, region)
    signs, changes = _signs(first_column, point) if (not parameters or point) else ((), None)
    numerical = None
    numerical_rhp = None
    diagnostics: tuple[str, ...] = ()
    if not parameters and changes is not None:
        numerical, numerical_rhp = check_numeric_poles(case, expected_rhp_roots=changes)
    elif point and region.status is SolveStatus.SOLVED_EXACT:
        numerical, numerical_rhp = check_numeric_poles(case, point, expected_rhp_roots=0)
    if numerical is not None and numerical.status is NumericalCheckStatus.INCONSISTENT:
        diagnostics = ("ROUTH_NUMERIC_POLE_MISMATCH",)
    if region.status is SolveStatus.EMPTY:
        statement = f"Grad {case.degree}: keine zulässige Einstellung für {_concept(canonical)}."
    elif region.status is SolveStatus.SOLVED_EXACT:
        statement = (
            f"Grad {case.degree}: {_concept(canonical)} genau für "
            f"{format_parameter_region_plain(region, parameters)}."
        )
    else:
        statement = f"Grad {case.degree}: Stabilitätsbereich nicht vollständig entscheidbar."
    return RouthDegreeCaseResult(
        case,
        rows,
        first_column,
        full + denominator_conditions,
        solver,
        region,
        special,
        point,
        signs,
        changes,
        changes,
        numerical,
        numerical_rhp,
        statement,
        region.status,
        diagnostics,
    )


def _unsupported(
    case: PolynomialDegreeCase, region: ParameterRegion, message: str
) -> RouthDegreeCaseResult:
    return RouthDegreeCaseResult(
        case,
        (),
        (),
        (),
        (),
        region,
        RouthSpecialCase.NONE,
        (),
        (),
        None,
        None,
        None,
        None,
        message,
        SolveStatus.INVALID_INPUT if case.degree == 0 else SolveStatus.UNSUPPORTED,
        (message,),
    )


def _build_rows(
    case: PolynomialDegreeCase,
) -> tuple[tuple[RouthRow, ...], RouthSpecialCase]:
    coefficients = [item._as_sympy() for item in case.coefficients]
    columns = math.ceil((case.degree + 1) / 2)
    even = [coefficients[index] for index in range(0, len(coefficients), 2)]
    odd = [coefficients[index] for index in range(1, len(coefficients), 2)]
    values = [even + [sp.Integer(0)] * (columns - len(even))]
    if case.degree >= 1:
        values.append(odd + [sp.Integer(0)] * (columns - len(odd)))
    rows: list[RouthRow] = [
        _initial_row(
            case.degree,
            values[0],
            RouthRowType.INITIAL_EVEN if case.degree % 2 == 0 else RouthRowType.INITIAL_ODD,
            0,
        ),
        _initial_row(
            case.degree - 1,
            values[1],
            RouthRowType.INITIAL_ODD if case.degree % 2 == 0 else RouthRowType.INITIAL_EVEN,
            1,
        ),
    ]
    special = _row_special(values[1])
    if special is not RouthSpecialCase.NONE:
        return tuple(rows), special
    for row_index in range(2, case.degree + 1):
        upper, lower = values[row_index - 2], values[row_index - 1]
        if sp.simplify(lower[0]) == 0:
            return tuple(rows), _row_special(lower)
        current: list[sp.Expr] = []
        cells: list[RouthCell] = []
        for column in range(columns):
            upper_next = upper[column + 1] if column + 1 < columns else sp.Integer(0)
            lower_next = lower[column + 1] if column + 1 < columns else sp.Integer(0)
            numerator = sp.expand(lower[0] * upper_next - upper[0] * lower_next)
            denominator = lower[0]
            value = sp.factor(sp.cancel(numerator / denominator))
            current.append(value)
            cells.append(
                RouthCell(
                    row_index,
                    column,
                    _exact(value),
                    _exact(numerator),
                    _exact(denominator),
                    f"[{lower[0]}*{upper_next} - {upper[0]}*{lower_next}]/{lower[0]} = {value}",
                    column == 0,
                )
            )
        values.append(current)
        rows.append(
            RouthRow(
                f"s^{case.degree - row_index}",
                case.degree - row_index,
                tuple(_exact(value) for value in current),
                _exact(current[0]),
                RouthRowType.RECURSIVE,
                tuple(cells),
            )
        )
        special = _row_special(current)
        if special is not RouthSpecialCase.NONE:
            return tuple(rows), special
    return tuple(rows), RouthSpecialCase.NONE


def _initial_row(power: int, values: list[sp.Expr], kind: RouthRowType, index: int) -> RouthRow:
    cells = tuple(
        RouthCell(
            index,
            column,
            _exact(value),
            _exact(value),
            _exact(1),
            "aus Koeffizientenfolge",
            column == 0,
        )
        for column, value in enumerate(values)
    )
    return RouthRow(
        f"s^{power}",
        power,
        tuple(_exact(value) for value in values),
        _exact(values[0]),
        kind,
        cells,
    )


def _row_special(values: list[sp.Expr]) -> RouthSpecialCase:
    zero = tuple(sp.simplify(value) == 0 for value in values)
    if all(zero):
        return RouthSpecialCase.COMPLETE_ZERO_ROW
    if zero[0]:
        return RouthSpecialCase.ZERO_FIRST_COLUMN
    return RouthSpecialCase.NONE


def _denominator_conditions(
    rows: tuple[RouthRow, ...], parameters: tuple[str, ...]
) -> tuple[AtomicParameterCondition, ...]:
    expressions: dict[str, sp.Expr] = {}
    for row in rows:
        for cell in row.cells:
            value_denominator = sp.denom(sp.together(cell.value._as_sympy()))
            if value_denominator.free_symbols and value_denominator != 1:
                expressions[str(value_denominator)] = value_denominator
    return tuple(
        AtomicParameterCondition(
            _exact(value),
            Relation.NE,
            ConditionOrigin.ROUTH_DENOMINATOR_EXCLUSION,
            parameters,
            f"Routh-Nenner {value} != 0",
        )
        for value in expressions.values()
    )


def _solver_first_column_expression(row: RouthRow) -> sp.Expr:
    if row.row_type is not RouthRowType.RECURSIVE:
        return row.first_column._as_sympy()
    return sp.factor(row.first_column._as_sympy().as_numer_denom()[0])


def _control_point(
    parameters: tuple[str, ...], region: ParameterRegion
) -> tuple[tuple[str, str], ...]:
    if not parameters or not region.control_points:
        return ()
    return tuple(zip(parameters, region.control_points[0], strict=True))


def _signs(
    first_column: tuple[ExactExpression, ...], point: tuple[tuple[str, str], ...]
) -> tuple[tuple[str, ...], int | None]:
    substitutions = {sp.Symbol(name): sp.sympify(value) for name, value in point}
    signs: list[str] = []
    for item in first_column:
        value = sp.simplify(item._as_sympy().subs(substitutions))
        if value == 0:
            return tuple(signs + ["0"]), None
        if value.is_positive:
            signs.append("+")
        elif value.is_negative:
            signs.append("-")
        else:
            return tuple(signs), None
    return tuple(signs), sum(left != right for left, right in zip(signs, signs[1:], strict=False))


def _worked_steps(
    canonical: CanonicalCharacteristicPolynomial,
    results: tuple[RouthDegreeCaseResult, ...],
    statement: str,
    notice: str,
) -> tuple[tuple[str, str], ...]:
    steps: list[tuple[str, str]] = [
        ("1. Gegebenes charakteristisches Polynom", canonical.input.polynomial.canonical_text),
        ("2. Polynomrolle und Analyseziel", f"{_role_text(canonical)}; {_concept(canonical)}"),
        (
            "3. Entscheidungsparameter und Annahmen",
            "Parameter: "
            + (", ".join(canonical.input.decision_parameters) or "keine")
            + "; Annahmen: "
            + _conditions_text(canonical.input.assumptions)
            + "; Ausschlüsse: "
            + _conditions_text(canonical.input.exclusions),
        ),
        (
            "4. Kanonische Koeffizientenfolge",
            ", ".join(item.canonical_text for item in canonical.coefficients),
        ),
        (
            "Hurwitz-Skriptkonvention",
            "Bei einer Hurwitz-Gegenkontrolle beginnt die erste Matrixzeile "
            "mit a_1, a_3, a_5, ...",
        ),
    ]
    for result in results:
        steps.append(
            (
                "5. Aktiver Gradfall",
                f"Grad {result.degree_case.degree}; "
                + ", ".join(item.label for item in result.degree_case.guard),
            )
        )
        steps.append(("6. Erste zwei Routh-Zeilen", _rows_text(result.rows[:2])))
        for row in result.rows[2:]:
            steps.append(
                (
                    f"7. Berechnung {row.power_label}",
                    "; ".join(cell.derivation for cell in row.cells),
                )
            )
        steps.extend(
            (
                ("8. Erste Spalte", ", ".join(item.canonical_text for item in result.first_column)),
                (
                    "9. Strikte Stabilitätsbedingungen",
                    ", ".join(
                        item.label for item in result.full_conditions[: len(result.first_column)]
                    ),
                ),
                (
                    "10. Übergabe an den Parameterkern",
                    "Gradfall, Annahmen, Ausschlüsse und Routh-Bedingungen",
                ),
                (
                    "11. Exakter Parameterbereich",
                    format_parameter_region_plain(
                        result.parameter_region, canonical.input.decision_parameters
                    ),
                ),
                (
                    "12. Vorzeichenwechsel / Kontrollpunkt",
                    _sign_change_text(result),
                ),
                (
                    "13. Numerische Polkontrolle",
                    _numeric_text(result.numerical_check),
                ),
            )
        )
    if notice:
        steps.append(("14. Kürzungshinweis", notice))
    steps.append(("15. Endaussage", statement))
    return tuple(steps)


def _concept(canonical: CanonicalCharacteristicPolynomial) -> str:
    labels = {
        AnalysisTarget.INTERNAL_CLOSED_LOOP_ASYMPTOTIC: "interne asymptotische Stabilität",
        AnalysisTarget.EXTERNAL_BIBO: "E/A-asymptotische (BIBO-)Stabilität",
        AnalysisTarget.STATE_ASYMPTOTIC: "asymptotische Zustandsstabilität",
    }
    return labels[canonical.input.analysis_target]


def _overall_statement(
    canonical: CanonicalCharacteristicPolynomial,
    results: tuple[RouthDegreeCaseResult, ...],
    combined_region: str,
    trusted: bool,
) -> str:
    if not trusted:
        return " ".join(item.statement for item in results) or (
            "Kein vertrauenswürdiges Endergebnis wegen einer schweren Diagnose."
        )
    if canonical.input.decision_parameters:
        solved = tuple(
            item.parameter_region
            for item in results
            if item.parameter_region.status is SolveStatus.SOLVED_EXACT
        )
        return (
            f"{_concept(canonical)} genau für "
            f"{format_parameter_region_plain(solved[0], canonical.input.decision_parameters)}."
            if combined_region and len(solved) == 1
            else " ".join(item.statement for item in results)
        )
    rhp_counts = tuple(item.rhp_roots_routh for item in results)
    if not rhp_counts or any(value is None for value in rhp_counts):
        return "Keine Stabilitätsendaussage bestimmbar."
    total = sum(value for value in rhp_counts if value is not None)
    root_text = "Nullstelle" if total == 1 else "Nullstellen"
    if total == 0:
        concept = _concept(canonical)
        return (
            f"{concept[0].upper() + concept[1:]}: stabil; "
            f"0 {root_text} in der rechten Halbebene."
        )
    return (
        f"{_not_stable_text(canonical)}; "
        f"{total} {root_text} in der rechten Halbebene."
    )


def _not_stable_text(canonical: CanonicalCharacteristicPolynomial) -> str:
    return {
        AnalysisTarget.INTERNAL_CLOSED_LOOP_ASYMPTOTIC: (
            "Nicht intern asymptotisch stabil"
        ),
        AnalysisTarget.EXTERNAL_BIBO: "Nicht E/A-asymptotisch (BIBO-)stabil",
        AnalysisTarget.STATE_ASYMPTOTIC: "Nicht asymptotisch zustandsstabil",
    }[canonical.input.analysis_target]


def _conditions_text(conditions: tuple[AtomicParameterCondition, ...]) -> str:
    return "; ".join(_relation_text(item) for item in conditions) or "keine"


def _relation_text(condition: AtomicParameterCondition) -> str:
    symbols = {
        Relation.GT: ">",
        Relation.GE: ">=",
        Relation.LT: "<",
        Relation.LE: "<=",
        Relation.EQ: "=",
        Relation.NE: "!=",
    }
    return f"{condition.expression.canonical_text} {symbols[condition.relation]} 0"


def _sign_change_text(result: RouthDegreeCaseResult) -> str:
    point = ", ".join(f"{name}={value}" for name, value in result.control_point)
    signs = ", ".join(result.sign_sequence) or "nicht bestimmbar"
    changes = str(result.sign_changes) if result.sign_changes is not None else "nicht bestimmbar"
    return f"{point or 'parameterfrei'}: {signs}; Wechsel={changes}"


def _numeric_text(check: NumericalPoleCheck | None) -> str:
    if check is None:
        return "nicht verfügbar"
    point = ", ".join(f"{name}={value}" for name, value in check.parameter_point)
    prefix = f"Kontrollpunkt {point}; " if point else ""
    status = {
        NumericalCheckStatus.CONSISTENT: "konsistent",
        NumericalCheckStatus.INCONSISTENT: "widersprüchlich",
        NumericalCheckStatus.NUMERICALLY_INCONCLUSIVE: "numerisch nicht entscheidbar",
    }[check.status]
    return f"{prefix}{status}; Pole: {', '.join(check.poles)}"


def _role_text(canonical: CanonicalCharacteristicPolynomial) -> str:
    labels = {
        PolynomialRole.DIRECT_CHARACTERISTIC_POLYNOMIAL: "direktes charakteristisches Polynom",
        PolynomialRole.RAW_CLOSED_LOOP_CHARACTERISTIC: "rohes geschlossenes Polynom",
        PolynomialRole.REDUCED_TRANSFER_DENOMINATOR: "reduzierter E/A-Nenner",
        PolynomialRole.STATE_CHARACTERISTIC_POLYNOMIAL: "Zustandsraum-Charakteristik",
    }
    return labels[canonical.input.role]


def _combined_region(
    results: tuple[RouthDegreeCaseResult, ...], parameters: tuple[str, ...]
) -> str:
    solved = tuple(
        item.parameter_region
        for item in results
        if item.status is SolveStatus.SOLVED_EXACT
        and item.parameter_region.status is SolveStatus.SOLVED_EXACT
    )
    if not solved:
        return "∅" if results and all(item.status is SolveStatus.EMPTY for item in results) else ""
    if len(parameters) != 1:
        return solved[0].exact_text if len(solved) == 1 else ""
    symbol = sp.Symbol(parameters[0])
    union: sp.Set = sp.S.EmptySet
    for region in solved:
        try:
            union = union.union(sp.sympify(region.exact_text).as_set())
        except (TypeError, ValueError, AttributeError):
            return ""
    return str(union.as_relational(symbol))


def _rows_text(rows: tuple[RouthRow, ...]) -> str:
    return "; ".join(
        f"{row.power_label}: [{', '.join(item.canonical_text for item in row.entries)}]"
        for row in rows
    )


def _latex(
    canonical: CanonicalCharacteristicPolynomial,
    results: tuple[RouthDegreeCaseResult, ...],
    notice: str,
) -> str:
    blocks = [
        paragraph("Gegeben", "Charakteristisches Polynom:"),
        latex_additive_equation(
            f"p({canonical.input.variable})",
            canonical.expanded_polynomial,
            variable=canonical.input.variable,
        ),
        paragraph("Gesucht", _concept(canonical)),
        paragraph(
            "Hurwitz-Skriptkonvention",
            "Bei einer Gegenkontrolle beginnt die erste Matrixzeile mit a_1, a_3, a_5, ...",
        ),
    ]
    for result in results:
        if result.rows:
            for row in result.rows:
                blocks.append(paragraph("Routh-Zeile", row.power_label))
                blocks.extend(
                    latex_additive_equation(
                        rf"r_{{{row.power},{index}}}", entry
                    )
                    for index, entry in enumerate(row.entries, 1)
                )
            recursive_cells = [cell for row in result.rows[2:] for cell in row.cells]
            for cell in recursive_cells:
                label = rf"r_{{{cell.row_index},{cell.column_index}}}"
                if len(cell.raw_numerator.latex) > 75:
                    helper = rf"Z_{{{cell.row_index},{cell.column_index}}}"
                    blocks.append(paragraph("Routh-Rekursion", "Additive Zwischengröße:"))
                    blocks.append(latex_additive_equation(helper, cell.raw_numerator))
                    blocks.append(
                        display_math(
                            label
                            + rf"=\frac{{{helper}}}{{{cell.raw_denominator.latex}}}"
                        )
                    )
                    blocks.append(latex_additive_equation(label, cell.value))
                else:
                    blocks.append(
                        display_math(
                            r"\begin{aligned}"
                            + label
                            + rf"&=\frac{{{cell.raw_numerator.latex}}}"
                            + rf"{{{cell.raw_denominator.latex}}}\\"
                            + rf"&={cell.value.latex}"
                            + r"\end{aligned}"
                        )
                    )
            blocks.append(paragraph("Stabilitätsbedingungen", "Erste Spalte strikt positiv:"))
            blocks.append(
                latex_conditions(
                    tuple(
                        item.expression
                        for item in result.full_conditions[: len(result.first_column)]
                    )
                )
            )
            blocks.append(paragraph("Parametergebiet", "Exaktes Ergebnis:"))
            blocks.append(
                latex_parameter_region(
                    result.parameter_region,
                    canonical.input.decision_parameters,
                )
            )
            blocks.append(latex_numerical_check(result.numerical_check))
            if result.sign_changes is not None:
                blocks.append(
                    paragraph(
                        "Vorzeichenwechsel",
                        f"Folge {', '.join(result.sign_sequence)}; "
                        f"{result.sign_changes} Pole in der rechten Halbebene.",
                    )
                )
    if notice:
        blocks.append(paragraph("Warnung", notice))
    blocks.append(_latex_final_box(canonical, results))
    return "\n\n".join(blocks)


def _latex_final_box(
    canonical: CanonicalCharacteristicPolynomial,
    results: tuple[RouthDegreeCaseResult, ...],
) -> str:
    if canonical.input.decision_parameters:
        if len(results) == 1:
            return latex_parameter_region(
                results[0].parameter_region,
                canonical.input.decision_parameters,
                boxed=True,
            )
        return "\n\n".join(
            latex_parameter_region(
                item.parameter_region,
                canonical.input.decision_parameters,
                boxed=True,
            )
            for item in results
        )
    total = sum(item.rhp_roots_routh or 0 for item in results)
    text = (
        _stable_latex_text(canonical)
        if total == 0
        else _not_stable_latex_text(canonical)
    )
    return display_math(r"\boxed{\text{" + _escape_latex_text(text) + "}}")


def _stable_latex_text(canonical: CanonicalCharacteristicPolynomial) -> str:
    return {
        AnalysisTarget.INTERNAL_CLOSED_LOOP_ASYMPTOTIC: "intern asymptotisch stabil",
        AnalysisTarget.EXTERNAL_BIBO: "E/A-asymptotisch (BIBO-)stabil",
        AnalysisTarget.STATE_ASYMPTOTIC: "asymptotisch zustandsstabil",
    }[canonical.input.analysis_target]


def _not_stable_latex_text(canonical: CanonicalCharacteristicPolynomial) -> str:
    return {
        AnalysisTarget.INTERNAL_CLOSED_LOOP_ASYMPTOTIC: (
            "nicht intern asymptotisch stabil"
        ),
        AnalysisTarget.EXTERNAL_BIBO: "nicht E/A-asymptotisch (BIBO-)stabil",
        AnalysisTarget.STATE_ASYMPTOTIC: "nicht asymptotisch zustandsstabil",
    }[canonical.input.analysis_target]


def _escape_latex_text(value: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "{": r"\{",
        "}": r"\}",
        "$": r"\$",
        "&": r"\&",
        "#": r"\#",
        "%": r"\%",
        "_": r"\_",
        "^": r"\textasciicircum{}",
        "~": r"\textasciitilde{}",
    }
    return "".join(replacements.get(character, character) for character in value)


__all__ = ["analyze_routh"]
