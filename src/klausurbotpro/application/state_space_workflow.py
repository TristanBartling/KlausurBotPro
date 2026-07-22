"""Safe, exact application workflow for the bounded SISO state-space bridge."""

from __future__ import annotations

import re
from dataclasses import replace

import sympy as sp

from klausurbotpro.application.stability_workflow import (
    StabilityInputDraft,
    run_stability_workflow,
)
from klausurbotpro.domain.expression import ExactExpression
from klausurbotpro.domain.hurwitz_contracts import HurwitzAnalysisResult
from klausurbotpro.domain.linear_ode_analyzer import build_linear_ode, format_ode_latex
from klausurbotpro.domain.parameter_core_contracts import AnalysisTarget, PolynomialRole
from klausurbotpro.domain.raw_transfer_function_factory import RawTransferFunctionFactory
from klausurbotpro.domain.root_analysis_contracts import (
    ExplicitExactRootValue,
    RootOccurrence,
    RootOfValue,
)
from klausurbotpro.domain.state_space_contracts import (
    ExactMatrix,
    StateSpaceAnalysisResult,
    StateSpaceCheck,
    StateSpaceInputDraft,
    StateSpaceModel,
    StateSpaceStatus,
    StateSpaceTaskType,
)
from klausurbotpro.domain.time_domain_contracts import LinearOdeInput
from klausurbotpro.domain.transfer_function_reducer import TransferFunctionReducer
from klausurbotpro.domain.transfer_function_reduction_contracts import (
    TransferFunctionReductionResult,
)
from klausurbotpro.domain.transfer_function_root_analyzer import TransferFunctionRootAnalyzer
from klausurbotpro.parsing import ParserConfig, SafeExpressionParser, SafeRationalExpressionParser

_IDENTIFIER = re.compile(r"[A-Za-z_]\w*")


def run_state_space_workflow(draft: StateSpaceInputDraft) -> StateSpaceAnalysisResult:
    """Run one complete state-space task without evaluating user code."""
    try:
        parameters = _parameters(draft.decision_parameters_text)
        _validate_names(draft, parameters)
        if draft.task_type is StateSpaceTaskType.ODE_TO_CONTROLLABLE_CANONICAL:
            return _from_ode(draft, parameters)
        if draft.task_type is StateSpaceTaskType.STATE_SPACE_TO_TRANSFER_FUNCTION:
            return _from_matrices(draft, parameters)
        return _failure("Der Aufgabentyp wird nicht unterstützt.", StateSpaceStatus.UNSUPPORTED)
    except ValueError as error:
        return _failure(str(error))
    except (ArithmeticError, TypeError, sp.PolynomialError) as error:
        return _failure(
            f"Die exakte Zustandsraumrechnung ist fehlgeschlagen: {type(error).__name__}."
        )


def preview_structured_ode(draft: StateSpaceInputDraft) -> str:
    try:
        parameters = _parameters(draft.decision_parameters_text)
        ode = _parse_ode(draft, parameters)
        return ode.normalized_ode if ode.valid else "\n".join(d.message for d in ode.diagnostics)
    except ValueError as error:
        return str(error)


def preview_matrix_dimensions(a_text: str, b_text: str, c_text: str) -> str:
    def size(text: str) -> tuple[int, int]:
        rows = [row for row in re.split(r"[;\n]+", text.strip()) if row.strip()]
        columns = [len([cell for cell in row.split(",") if cell.strip()]) for row in rows]
        return len(rows), columns[0] if columns and len(set(columns)) == 1 else 0

    a, b, c = size(a_text), size(b_text), size(c_text)
    return f"A: {a[0]}×{a[1]}, b: {b[0]}×{b[1]}, c^T: {c[0]}×{c[1]}, d: 1×1"


def _from_ode(draft: StateSpaceInputDraft, parameters: tuple[str, ...]) -> StateSpaceAnalysisResult:
    if len(draft.input_coefficient_texts) > 1 and any(
        _nonzero_text(value) for value in draft.input_coefficient_texts[1:]
    ):
        raise ValueError(
            "Die direkte Regelungsnormalform dieses MVP unterstützt nur den nicht "
            "abgeleiteten Eingang u(t)."
        )
    ode = _parse_ode(draft, parameters)
    if not ode.valid:
        raise ValueError("\n".join(item.message for item in ode.diagnostics))
    n = draft.output_order
    leading = ode.leading_coefficient._as_sympy()
    coefficients = dict((order, value._as_sympy()) for order, value in ode.output_terms)
    input_coefficients = dict((order, value._as_sympy()) for order, value in ode.input_terms)
    alpha = tuple(sp.cancel(coefficients.get(k, sp.Integer(0)) / leading) for k in range(n))
    beta = sp.cancel(input_coefficients.get(0, sp.Integer(0)) / leading)
    normalized_coefficients = tuple(_exact(value) for value in (*alpha, sp.Integer(1)))
    normalized = build_linear_ode(
        output_name=draft.output_name.strip(),
        input_name=draft.input_name.strip(),
        output_coefficients=normalized_coefficients,
        input_coefficients=(_exact(beta),),
        output_order=n,
        input_order=0,
        assumptions=tuple(
            item.strip() for item in re.split(r"[;\n]+", draft.assumptions_text) if item.strip()
        ),
    )
    a = sp.zeros(n)
    for row in range(n - 1):
        a[row, row + 1] = 1
    for column, coefficient in enumerate(alpha):
        a[n - 1, column] = -coefficient
    b = sp.zeros(n, 1)
    b[n - 1, 0] = beta
    c = sp.zeros(1, n)
    c[0, 0] = 1
    model = _model(a, b, c, sp.Integer(0), draft)
    definitions = tuple(
        f"x_{index + 1}(t)={_derivative_plain(draft.output_name.strip(), index)}"
        for index in range(n)
    )
    state_symbols = sp.Matrix(
        sp.symbols(" ".join(f"x_{index + 1}" for index in range(n)), seq=True)
    )
    equations = tuple(
        [f"dot(x_{index + 1}) = x_{index + 2}" for index in range(n - 1)]
        + [
            f"dot(x_{n}) = "
            + _plain(a.row(n - 1).dot(state_symbols) + beta * sp.Symbol(draft.input_name.strip()))
        ]
    )
    return _analyze(model, draft, normalized, definitions, equations)


def _from_matrices(
    draft: StateSpaceInputDraft, parameters: tuple[str, ...]
) -> StateSpaceAnalysisResult:
    parser = SafeExpressionParser(ParserConfig(allowed_symbols=frozenset(parameters)))
    a = _parse_matrix(draft.matrix_a_text, "A", parser)
    b = _parse_matrix(draft.vector_b_text, "b", parser)
    c = _parse_matrix(draft.vector_c_text, "c^T", parser)
    d_matrix = _parse_matrix(draft.scalar_d_text, "d", parser)
    if a.rows != a.cols:
        raise ValueError(f"A muss quadratisch sein; erhalten: {a.rows}×{a.cols}.")
    n = a.rows
    if n > 4:
        return _failure(
            "Zustandsdimension größer als 4 wird nicht unterstützt.", StateSpaceStatus.UNSUPPORTED
        )
    if n < 1:
        raise ValueError("Die Zustandsdimension muss mindestens 1 sein.")
    if b.shape != (n, 1):
        raise ValueError(f"b muss die Dimension {n}×1 haben; erhalten: {b.rows}×{b.cols}.")
    if c.shape != (1, n):
        raise ValueError(f"c^T muss die Dimension 1×{n} haben; erhalten: {c.rows}×{c.cols}.")
    if d_matrix.shape != (1, 1):
        raise ValueError(f"d muss skalar (1×1) sein; erhalten: {d_matrix.rows}×{d_matrix.cols}.")
    model = _model(a, b, c, d_matrix[0, 0], draft)
    state_vector = sp.Matrix(sp.symbols(" ".join(f"x_{index + 1}" for index in range(n)), seq=True))
    derivative = a * state_vector + b * sp.Symbol(draft.input_name.strip())
    equations = tuple(f"dot(x_{row + 1}) = {_plain(derivative[row])}" for row in range(n))
    definitions = tuple(f"x_{index + 1}" for index in range(n))
    return _analyze(model, draft, None, definitions, equations)


def _analyze(
    model: StateSpaceModel,
    draft: StateSpaceInputDraft,
    normalized_ode: LinearOdeInput | None,
    definitions: tuple[str, ...],
    equations: tuple[str, ...],
) -> StateSpaceAnalysisResult:
    a, b, c = (_sympy_matrix(item) for item in (model.matrix_a, model.vector_b, model.vector_c))
    d = model.scalar_d._as_sympy()
    s = sp.Symbol("s")
    si_minus_a = s * sp.eye(model.state_dimension) - a
    characteristic = sp.Poly(sp.expand(si_minus_a.det()), s).as_expr()
    adjugate_expression = sp.cancel((c * si_minus_a.adjugate() * b)[0] / characteristic + d)
    raw_numerator = sp.expand((c * si_minus_a.adjugate() * b)[0] + d * characteristic)
    raw_expression = raw_numerator / characteristic
    reduction = _reduce_transfer(
        raw_expression, tuple(draft.decision_parameters_text.replace(" ", "").split(","))
    )
    if reduction.reduced is None:
        raise ValueError("Die vorhandene Rationalfunktionsreduktion ist fehlgeschlagen.")
    reduced_expression = sp.cancel(
        reduction.reduced.numerator.expression._as_sympy()
        / reduction.reduced.denominator.expression._as_sympy()
    )
    transfer_details = _transfer_details(reduction)
    stability = run_stability_workflow(
        StabilityInputDraft(
            polynomial_text=str(characteristic),
            decision_parameters_text=draft.decision_parameters_text,
            assumptions_text=draft.assumptions_text,
            role=PolynomialRole.STATE_CHARACTERISTIC_POLYNOMIAL,
            analysis_target=AnalysisTarget.STATE_ASYMPTOTIC,
            provenance_note=draft.provenance,
        )
    )
    if stability.analysis is None or not isinstance(stability.analysis, HurwitzAnalysisResult):
        raise ValueError(
            "Die Zustandsstabilität konnte nicht analysiert werden: " + " ".join(stability.errors)
        )
    exact_eigenvalues, numerical, counts = _eigenvalues(
        characteristic, draft.decision_parameters_text
    )
    hidden_factor = sp.cancel(characteristic / reduction.reduced.denominator.expression._as_sympy())
    hidden = _factor_roots(hidden_factor, s) if sp.degree(hidden_factor, s) > 0 else ()
    hidden_unstable = any(_root_is_unstable(item._as_sympy()) for item in hidden)
    assert reduction.report is not None
    cancellation = _cancellation_text(reduction.report.was_reduced, hidden, hidden_unstable)
    inverse_check = sp.simplify(
        si_minus_a * si_minus_a.inv() - sp.eye(model.state_dimension)
    ) == sp.zeros(model.state_dimension)
    expression_check = sp.simplify(adjugate_expression - reduced_expression) == 0
    determinant_check = sp.simplify(si_minus_a.det() - characteristic) == 0
    rational_check = sp.simplify(raw_numerator - reduced_expression * characteristic) == 0
    eigen_check = _numeric_roots_match(characteristic, numerical)
    stability_check = counts is None or _stability_consistent(stability.analysis.statement, counts)
    hidden_check = (
        sp.simplify(
            characteristic - hidden_factor * reduction.reduced.denominator.expression._as_sympy()
        )
        == 0
    )
    checks: tuple[StateSpaceCheck, ...] = (
        StateSpaceCheck(
            "Dimensionen", True, "A, b, c^T und d besitzen konsistente SISO-Dimensionen."
        ),
        StateSpaceCheck(
            "Determinante", determinant_check, "det(sI-A) wurde symbolisch rückgeprüft."
        ),
        StateSpaceCheck("Resolvente", inverse_check, "(sI-A)(sI-A)^(-1)=I."),
        StateSpaceCheck("Übertragungsfunktion", expression_check, "G(s)=c^T(sI-A)^(-1)b+d."),
        StateSpaceCheck(
            "Rückmultiplikation",
            rational_check,
            "Die reduzierte Rationalfunktion wurde rückmultipliziert.",
        ),
        StateSpaceCheck(
            "Eigenwertkontrolle",
            eigen_check,
            "Numerische Eigenwerte erfüllen das charakteristische Polynom.",
        ),
        StateSpaceCheck(
            "Stabilitätskonsistenz",
            stability_check,
            "Hurwitz-Aussage und Eigenwertkontrolle sind konsistent.",
        ),
        StateSpaceCheck(
            "Versteckte Moden",
            hidden_check,
            "Interne und reduzierte E/A-Moden wurden getrennt verglichen.",
        ),
    )
    if normalized_ode is not None:
        ode = normalized_ode
        ode_poly = sum(value._as_sympy() * s**order for order, value in ode.output_terms)
        ode_tf = sp.cancel(ode.input_terms[0][1]._as_sympy() / ode_poly)
        checks += (
            StateSpaceCheck(
                "Normierte DGL",
                sp.simplify(characteristic - ode_poly) == 0,
                "det(sI-A) stimmt mit dem normierten DGL-Polynom überein.",
            ),
            StateSpaceCheck(
                "DGL-Übertragungsfunktion",
                sp.simplify(ode_tf - reduced_expression) == 0,
                "Die Nullzustandsübertragungsfunktion stimmt überein.",
            ),
        )
    if not all(item.passed for item in checks):
        return replace(
            _failure(
                "Mindestens eine verpflichtende Kontrolle ist widersprüchlich.",
                StateSpaceStatus.VERIFICATION_FAILED,
            ),
            input_model=model,
            checks=checks,
        )
    state_stability = _state_stability_text(stability.analysis.statement, counts)
    steps = _worked_steps(
        draft.task_type, model, characteristic, raw_expression, reduced_expression, checks
    )
    latex = _latex(
        draft,
        model,
        normalized_ode,
        si_minus_a,
        characteristic,
        exact_eigenvalues,
        numerical,
        state_stability,
        raw_expression,
        reduced_expression,
        cancellation,
        checks,
    )
    return StateSpaceAnalysisResult(
        model,
        normalized_ode,
        definitions,
        equations,
        _exact(characteristic),
        exact_eigenvalues,
        numerical,
        counts,
        state_stability,
        stability.analysis,
        _exact(raw_expression),
        _exact(reduced_expression),
        reduction,
        transfer_details,
        cancellation,
        hidden,
        checks,
        steps,
        latex,
        StateSpaceStatus.SOLVED,
    )


def _parse_ode(draft: StateSpaceInputDraft, parameters: tuple[str, ...]) -> LinearOdeInput:
    parser = SafeExpressionParser(ParserConfig(allowed_symbols=frozenset(parameters)))
    if draft.output_order not in range(1, 5):
        raise ValueError("Unterstützt werden Ausgangsordnungen 1 bis 4.")
    if len(draft.output_coefficient_texts) != draft.output_order + 1:
        raise ValueError(
            f"Für Ordnung {draft.output_order} werden "
            f"{draft.output_order + 1} Ausgangskoeffizienten erwartet."
        )
    output = tuple(
        _parse_cell(value, f"a_{index}", parser)
        for index, value in enumerate(draft.output_coefficient_texts)
    )
    inputs = draft.input_coefficient_texts or ("0",)
    parsed_inputs = tuple(
        _parse_cell(value, f"b_{index}", parser) for index, value in enumerate(inputs)
    )
    return build_linear_ode(
        output_name=draft.output_name.strip(),
        input_name=draft.input_name.strip(),
        output_coefficients=output,
        input_coefficients=parsed_inputs,
        output_order=draft.output_order,
        input_order=len(parsed_inputs) - 1,
        assumptions=tuple(
            item.strip() for item in re.split(r"[;\n]+", draft.assumptions_text) if item.strip()
        ),
    )


def _parse_matrix(text: str, name: str, parser: SafeExpressionParser) -> sp.Matrix:
    rows = [row.strip() for row in re.split(r"[;\n]+", _minus(text).strip()) if row.strip()]
    if not rows:
        raise ValueError(f"{name} darf nicht leer sein.")
    parsed: list[list[sp.Expr]] = []
    width: int | None = None
    for row_index, row in enumerate(rows, start=1):
        cells = [cell.strip() for cell in row.split(",")]
        if any(not cell for cell in cells):
            raise ValueError(f"{name}, Zeile {row_index}: leere Matrixzelle.")
        if width is None:
            width = len(cells)
        elif width != len(cells):
            raise ValueError(
                f"{name} besitzt unterschiedlich lange Zeilen ({width} und {len(cells)} Einträge)."
            )
        parsed.append(
            [
                _parse_cell(cell, f"{name}[{row_index},{column}]", parser)._as_sympy()
                for column, cell in enumerate(cells, start=1)
            ]
        )
    return sp.Matrix(parsed)


def _parse_cell(text: str, field: str, parser: SafeExpressionParser) -> ExactExpression:
    result = parser.parse(_minus(text), field)
    if result.value is None:
        raise ValueError(f"{field}: " + " ".join(item.message for item in result.diagnostics))
    return result.value


def _reduce_transfer(
    expression: sp.Expr, parameters: tuple[str, ...]
) -> TransferFunctionReductionResult:
    names = frozenset(("s", *(item for item in parameters if item)))
    parsed = SafeRationalExpressionParser(ParserConfig(allowed_symbols=names)).parse_common(
        str(expression), variable_name="s", field="G(s)"
    )
    if parsed.value is None:
        raise ValueError("Die erzeugte Übertragungsfunktion konnte nicht sicher geparst werden.")
    raw = RawTransferFunctionFactory(
        expected_variable_name="s", allowed_parameter_names=names - {"s"}
    ).create(parsed.value, field="G(s)")
    if raw.value is None:
        raise ValueError("Die erzeugte Übertragungsfunktion ist keine zulässige Rationalfunktion.")
    return TransferFunctionReducer().reduce(raw.value, field="G(s)")


def _model(
    a: sp.Matrix, b: sp.Matrix, c: sp.Matrix, d: sp.Expr, draft: StateSpaceInputDraft
) -> StateSpaceModel:
    n = a.rows
    return StateSpaceModel(
        _matrix(a),
        _matrix(b),
        _matrix(c),
        _exact(d),
        n,
        tuple(f"x_{i + 1}" for i in range(n)),
        draft.input_name.strip(),
        draft.output_name.strip(),
        draft.provenance,
        StateSpaceStatus.SOLVED,
    )


def _matrix(value: sp.Matrix) -> ExactMatrix:
    entries = tuple(
        tuple(_exact(value[row, column]) for column in range(value.cols))
        for row in range(value.rows)
    )
    return ExactMatrix(value.rows, value.cols, entries, str(value.tolist()), sp.latex(value))


def _sympy_matrix(value: ExactMatrix) -> sp.Matrix:
    return sp.Matrix([[item._as_sympy() for item in row] for row in value.entries])


def _eigenvalues(
    polynomial: sp.Expr, parameter_text: str
) -> tuple[tuple[tuple[ExactExpression, int], ...], tuple[str, ...], tuple[int, int, int] | None]:
    s = sp.Symbol("s")
    if parameter_text.strip():
        return (), (), None
    poly = sp.Poly(polynomial, s)
    numerical_values = tuple(complex(value) for value in sp.nroots(poly, maxsteps=200))
    numerical = tuple(_format_complex(value) for value in numerical_values)
    counts = (
        sum(value.real < -1e-9 for value in numerical_values),
        sum(abs(value.real) <= 1e-9 for value in numerical_values),
        sum(value.real > 1e-9 for value in numerical_values),
    )
    roots = sp.roots(poly)
    exact = (
        ()
        if any(sp.count_ops(root) > 24 for root in roots)
        else tuple((_exact(root), int(multiplicity)) for root, multiplicity in roots.items())
    )
    return exact, numerical, counts


def _factor_roots(expression: sp.Expr, variable: sp.Symbol) -> tuple[ExactExpression, ...]:
    return tuple(
        _exact(root)
        for root, multiplicity in sp.roots(sp.Poly(expression, variable)).items()
        for _ in range(int(multiplicity))
    )


def _transfer_details(reduction: TransferFunctionReductionResult) -> tuple[str, ...]:
    assert reduction.reduced is not None
    reduced = reduction.reduced
    numerator_degree = reduced.numerator.degree_info.generic_degree
    denominator_degree = reduced.denominator.degree_info.generic_degree
    properness = (
        "streng echt"
        if numerator_degree is not None
        and denominator_degree is not None
        and numerator_degree < denominator_degree
        else "gleichgradig mit Durchgriff"
        if numerator_degree == denominator_degree
        else "unecht"
    )
    roots = TransferFunctionRootAnalyzer().analyze_reduction(reduction)
    zeros = _root_texts(roots.reduced_zeros.roots) if roots.reduced_zeros is not None else ()
    poles = _root_texts(roots.reduced_poles.roots) if roots.reduced_poles is not None else ()
    return (
        f"Zähler: {reduced.numerator.expression.canonical_text}",
        f"Nenner: {reduced.denominator.expression.canonical_text}",
        f"Grade: Zähler {numerator_degree}, Nenner {denominator_degree} ({properness})",
        "Nullstellen: " + (", ".join(zeros) if zeros else "keine"),
        "Pole: " + (", ".join(poles) if poles else "keine oder parameterabhängig"),
        "Kürzungen: "
        + ("vorhanden" if reduction.report and reduction.report.was_reduced else "keine"),
    )


def _root_texts(roots: tuple[RootOccurrence, ...]) -> tuple[str, ...]:
    result: list[str] = []
    for occurrence in roots:
        value = occurrence.value
        multiplicity = occurrence.multiplicity
        if isinstance(value, ExplicitExactRootValue):
            text = value.expression.canonical_text
        elif isinstance(value, RootOfValue):
            text = f"RootOf{value.defining_coefficients}[{value.root_index}]"
        else:
            continue
        result.append(text + (f" (m={multiplicity})" if multiplicity > 1 else ""))
    return tuple(result)


def _root_is_unstable(root: sp.Expr) -> bool:
    value = complex(sp.N(root, 15))
    return value.real > 1e-9


def _numeric_roots_match(polynomial: sp.Expr, roots: tuple[str, ...]) -> bool:
    if not roots:
        return True
    s = sp.Symbol("s")
    return all(
        abs(complex(sp.N(polynomial.subs(s, complex(root.replace("i", "j"))), 15))) < 1e-6
        for root in roots
    )


def _stability_consistent(statement: str, counts: tuple[int, int, int]) -> bool:
    stable = counts == (sum(counts), 0, 0)
    lowered = statement.lower()
    says_unstable = any(marker in lowered for marker in ("nicht", "keine", "∅"))
    return stable != says_unstable


def _state_stability_text(hurwitz_statement: str, counts: tuple[int, int, int] | None) -> str:
    if counts is None:
        return hurwitz_statement
    left, axis, right = counts
    if axis == 0 and right == 0:
        return "Das Zustandsmodell ist asymptotisch stabil."
    details = []
    if right:
        details.append(f"{right} Eigenwert(e) in der rechten Halbebene")
    if axis:
        details.append(f"{axis} Eigenwert(e) auf der imaginären Achse")
    suffix = ": " + ", ".join(details) if details else ""
    return "Das Zustandsmodell ist nicht asymptotisch stabil" + suffix + "."


def _cancellation_text(
    was_reduced: bool, hidden: tuple[ExactExpression, ...], unstable: bool
) -> str:
    if not hidden:
        return (
            "Keine internen Zustandsmoden wurden in der reduzierten "
            "E/A-Übertragungsfunktion entfernt."
        )
    modes = ", ".join(item.canonical_text for item in hidden)
    text = (
        "Die reduzierte E/A-Übertragungsfunktion enthält nicht alle internen "
        f"Zustandsmoden. Entfernt: {modes}."
    )
    if unstable:
        text += (
            " Die reduzierte E/A-Übertragungsfunktion erscheint stabil, das "
            "Zustandsmodell besitzt jedoch eine versteckte instabile Mode bei s=" + modes + "."
        )
    elif was_reduced:
        text += (
            " Die E/A-Übertragungsfunktion darf nicht zur Aussage über interne "
            "Stabilität verwendet werden."
        )
    return text


def _worked_steps(
    task: StateSpaceTaskType,
    model: StateSpaceModel,
    characteristic: sp.Expr,
    raw: sp.Expr,
    reduced: sp.Expr,
    checks: tuple[StateSpaceCheck, ...],
) -> tuple[str, ...]:
    common = [
        "Gegebene Matrizen: "
        f"A={model.matrix_a.canonical_text}, b={model.vector_b.canonical_text}, "
        f"c^T={model.vector_c.canonical_text}, d={model.scalar_d.canonical_text}.",
        "Dimensionsprüfung bestanden.",
        "sI-A gebildet.",
        f"Charakteristisches Polynom: {_plain(characteristic)}.",
        "Eigenwerte bestimmt und numerisch kontrolliert.",
        "Zustandsstabilität mit dem vorhandenen Hurwitz-Kern analysiert.",
        "Resolvente gebildet.",
        f"G(s)=c^T(sI-A)^(-1)b+d={_plain(raw)}.",
        f"Reduzierte Übertragungsfunktion: {_plain(reduced)}.",
        "Interne Moden und E/A-Pole verglichen.",
        "Kontrollen: " + ", ".join(item.name for item in checks if item.passed) + ".",
        f"Ergebnis: A={model.matrix_a.canonical_text}, G(s)={_plain(reduced)}.",
    ]
    if task is StateSpaceTaskType.ODE_TO_CONTROLLABLE_CANONICAL:
        steps = [
            "Gegebene strukturierte DGL.",
            "Leitkoeffizient geprüft und DGL normiert.",
            "Koeffizienten identifiziert.",
            "Zustandswahl x_1=y bis x_n=y^(n-1).",
            "Ableitungskette und letzte Zustandsgleichung aufgebaut.",
            "A_R, b_R, c_R^T und d aufgebaut.",
        ] + common[3:]
        return tuple(
            (*steps[:-1], f"Ergebnis: A_R={model.matrix_a.canonical_text}, G(s)={_plain(reduced)}.")
        )
    return tuple(common)


def _latex(
    draft: StateSpaceInputDraft,
    model: StateSpaceModel,
    normalized_ode: LinearOdeInput | None,
    si_minus_a: sp.Matrix,
    characteristic: sp.Expr,
    exact_eigenvalues: tuple[tuple[ExactExpression, int], ...],
    numerical: tuple[str, ...],
    stability: str,
    raw: sp.Expr,
    reduced: sp.Expr,
    cancellation: str,
    checks: tuple[StateSpaceCheck, ...],
) -> str:
    canonical_mode = normalized_ode is not None
    given = (
        rf"A={model.matrix_a.latex},\quad b={model.vector_b.latex},\quad "
        rf"c^T={model.vector_c.latex},\quad d={model.scalar_d.latex}"
    )
    ode_lines: tuple[str, ...] = ()
    if normalized_ode is not None:
        original_ode = _parse_ode(draft, _parameters(draft.decision_parameters_text))
        given = format_ode_latex(original_ode)
        definitions = r"\\".join(
            rf"x_{{{index + 1}}}(t)={_derivative_latex(draft.output_name.strip(), index)}"
            for index in range(model.state_dimension)
        )
        a = _sympy_matrix(model.matrix_a)
        b = _sympy_matrix(model.vector_b)
        state_symbols = sp.Matrix(
            sp.symbols(
                " ".join(f"x_{index + 1}" for index in range(model.state_dimension)),
                seq=True,
            )
        )
        derivative = a * state_symbols + b * sp.Symbol(draft.input_name.strip())
        state_equations = r"\\".join(
            rf"\dot{{x}}_{{{index + 1}}}(t)={sp.latex(derivative[index])}"
            for index in range(model.state_dimension)
        )
        ode_lines = (
            rf"\[\text{{Normierte DGL:}}\quad {format_ode_latex(normalized_ode)}\]",
            rf"\[\begin{{aligned}}{definitions}\end{{aligned}}\]",
            rf"\[\begin{{aligned}}{state_equations}\end{{aligned}}\]",
        )
    exact_text = (
        r",\ ".join(
            item.latex if multiplicity == 1 else rf"{item.latex}\ (m={multiplicity})"
            for item, multiplicity in exact_eigenvalues
        )
        or r"\text{siehe numerische Kontrolle}"
    )
    numeric_text = (
        r",\ ".join(value.replace("i", r"\,\mathrm{i}") for value in numerical)
        or r"\text{parameterabhängig}"
    )
    check_lines = r"\\".join(
        rf"\text{{{_escape_text(item.name)}: {'bestanden' if item.passed else 'fehlgeschlagen'}}}"
        for item in checks
    )
    warning_lines = (
        ()
        if cancellation.startswith("Keine")
        else (
            r"\textbf{Hinweis:}\par",
            _escape_text(cancellation),
        )
    )
    matrix_line = (
        rf"\[A_R={model.matrix_a.latex},\quad b_R={model.vector_b.latex},"
        rf"\quad c_R^T={model.vector_c.latex},\quad d={model.scalar_d.latex}\]"
        if canonical_mode
        else (
            rf"\[A={model.matrix_a.latex},\quad b={model.vector_b.latex},"
            rf"\quad c^T={model.vector_c.latex},\quad d={model.scalar_d.latex}\]"
        )
    )
    short_stability = (
        "nicht asymptotisch stabil"
        if "nicht asymptotisch stabil" in stability
        else "asymptotisch stabil"
    )
    end_lines = (
        (
            rf"\[\boxed{{A_R={model.matrix_a.latex}}}\qquad"
            rf"\boxed{{b_R={model.vector_b.latex}}}\]",
            rf"\[\boxed{{c_R^T={model.vector_c.latex}}}\qquad"
            rf"\boxed{{d={model.scalar_d.latex}}}\]",
            rf"\[\boxed{{G(s)={sp.latex(reduced)}}}\]",
        )
        if canonical_mode
        else (
            rf"\[\boxed{{\text{{{short_stability}}}}}\]",
            rf"\[\boxed{{G(s)={sp.latex(reduced)}}}\]",
        )
    )
    return "\n".join(
        (
            r"\textbf{Gegeben}",
            rf"\[{given}\]",
            r"\textbf{Gesucht}",
            r"\[A,B,C,D,\quad p_A(s),\quad \lambda_i,\quad G(s),\quad \text{Zustandsstabilität}\]",
            r"\textbf{Lösung}",
            *ode_lines,
            matrix_line,
            rf"\[sI-A={sp.latex(si_minus_a)},\qquad p_A(s)=\det(sI-A)={sp.latex(characteristic)}\]",
            rf"\[\lambda_i\in\left\{{{exact_text}\right\}},\qquad "
            rf"\lambda_i\approx\left\{{{numeric_text}\right\}}\]",
            rf"\[\text{{{_escape_text(stability)}}}\]",
            rf"\[G(s)=c^T(sI-A)^{{-1}}b+d={sp.latex(raw)}\]",
            rf"\[G_{{\mathrm{{red}}}}(s)={sp.latex(reduced)}\]",
            *warning_lines,
            rf"\[\begin{{aligned}}{check_lines}\end{{aligned}}\]",
            *end_lines,
        )
    )


def _failure(
    message: str, status: StateSpaceStatus = StateSpaceStatus.INVALID_INPUT
) -> StateSpaceAnalysisResult:
    return StateSpaceAnalysisResult(
        None,
        None,
        (),
        (),
        None,
        (),
        (),
        None,
        "Keine vertrauenswürdige Stabilitätsaussage.",
        None,
        None,
        None,
        None,
        (),
        "",
        (),
        (),
        (),
        "",
        status,
        (message,),
    )


def _parameters(text: str) -> tuple[str, ...]:
    values = tuple(item.strip() for item in text.split(",") if item.strip())
    if (
        len(values) > 2
        or len(set(values)) != len(values)
        or any(not value.isidentifier() for value in values)
    ):
        raise ValueError(
            "Es sind höchstens zwei unterschiedliche gültige Entscheidungsparameter erlaubt."
        )
    return values


def _validate_names(draft: StateSpaceInputDraft, parameters: tuple[str, ...]) -> None:
    for label, name in (
        ("Ausgang", draft.output_name.strip()),
        ("Eingang", draft.input_name.strip()),
    ):
        if not name.isidentifier() or name in parameters or name in {"s", "t"}:
            raise ValueError(f"{label}sname ist ungültig.")


def _nonzero_text(text: str) -> bool:
    return text.strip() not in {"", "0", "+0", "-0"}


def _minus(text: str) -> str:
    return text.replace("−", "-").replace("–", "-")


def _exact(value: sp.Expr) -> ExactExpression:
    return ExactExpression._from_sympy(sp.cancel(value))


def _plain(value: sp.Expr) -> str:
    return str(sp.factor(value)).replace("**", "^")


def _derivative_plain(name: str, order: int) -> str:
    if order == 0:
        return f"{name}(t)"
    if order <= 3:
        return f"{name}{chr(39) * order}(t)"
    return f"{name}^({order})(t)"


def _derivative_latex(name: str, order: int) -> str:
    function = r"\varphi_G" if name == "phi_G" else sp.latex(sp.Symbol(name))
    if order == 0:
        return rf"{function}(t)"
    if order == 1:
        return rf"\dot{{{function}}}(t)"
    if order == 2:
        return rf"\ddot{{{function}}}(t)"
    return rf"{function}^{{({order})}}(t)"


def _format_complex(value: complex) -> str:
    if abs(value.imag) < 1e-12:
        return f"{value.real:.9g}"
    return f"{value.real:.9g}{value.imag:+.9g}i"


def _escape_text(text: str) -> str:
    return "".join(
        {"_": r"\_", "%": r"\%", "&": r"\&", "#": r"\#", "{": r"\{", "}": r"\}"}.get(char, char)
        for char in text
    )


__all__ = ["preview_matrix_dimensions", "preview_structured_ode", "run_state_space_workflow"]
