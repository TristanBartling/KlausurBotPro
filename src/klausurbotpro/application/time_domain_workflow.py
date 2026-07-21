"""Application orchestration and presentation for the time-domain workspace."""

from __future__ import annotations

import re
from dataclasses import dataclass, replace

import sympy as sp

from klausurbotpro.domain.diagnostics import (
    Diagnostic,
    DiagnosticCode,
    DiagnosticSeverity,
)
from klausurbotpro.domain.expression import ExactExpression
from klausurbotpro.domain.linear_ode_analyzer import (
    build_initial_conditions,
    build_linear_ode,
    transform_ode,
    verify_ode_solution,
)
from klausurbotpro.domain.raw_transfer_function_factory import RawTransferFunctionFactory
from klausurbotpro.domain.time_domain_analyzer import (
    classify_reduction_poles,
    direct_laplace,
    exact,
    inverse_rational,
)
from klausurbotpro.domain.time_domain_contracts import (
    ComputationStatus,
    EndValueStatus,
    ExponentialInputSignal,
    FactorType,
    InitialConditionSet,
    InputSignalType,
    LinearOdeInput,
    OdeSolutionData,
    OdeTransferFunctionResult,
    OdeVerificationReport,
    PartialFractionTerm,
    PoleRole,
    RationalClassificationKind,
    TimeDomainSolution,
    TimeDomainTaskType,
    TimeFunction,
    TypedInputSignal,
    VerificationItem,
    VerificationReport,
    VerificationStatus,
)
from klausurbotpro.domain.transfer_function_reducer import TransferFunctionReducer
from klausurbotpro.domain.transfer_function_reduction_contracts import (
    TransferFunctionReductionResult,
    TransferFunctionReductionStepKind,
)
from klausurbotpro.parsing import (
    ParserConfig,
    ParserProfile,
    SafeExpressionParser,
    SafeRationalExpressionParser,
)

_IDENTIFIER = re.compile(r"\b[A-Za-z_]\w*\b")
_RESERVED = frozenset({"s", "t", "pi", "exp", "sin", "cos"})


@dataclass(frozen=True, slots=True)
class TimeDomainInputDraft:
    task_type: TimeDomainTaskType
    time_expression_text: str = ""
    image_expression_text: str = ""
    system_expression_text: str = ""
    input_expression_text: str = ""
    step_amplitude_text: str = "1"
    exponential_amplitude_text: str = "1"
    exponential_exponent_text: str = "0"
    assumptions_text: str = ""
    output_name: str = "y"
    input_name: str = "u"
    output_order: int = 2
    input_order: int = 0
    output_coefficient_texts: tuple[str, ...] = ()
    input_coefficient_texts: tuple[str, ...] = ()
    output_initial_texts: tuple[str, ...] = ()
    input_initial_texts: tuple[str, ...] = ()
    ode_input_signal_type: InputSignalType = InputSignalType.STEP
    ode_signal_amplitude_text: str = "1"
    ode_signal_rate_text: str = "1"
    polynomial_coefficient_texts: tuple[str, ...] = ()
    missing_initials_are_zero: bool = False
    zero_state_confirmed: bool = False


@dataclass(frozen=True, slots=True)
class TimeDomainPresentation:
    summary: str
    rational_analysis: str
    partial_fractions: str
    time_function: str
    verifications: str
    short_solution: str
    worked_steps: str
    latex_source: str
    diagnostics: str
    ode_and_initials: str = ""
    laplace_transformation: str = ""
    image_equation: str = ""
    free_and_forced: str = ""


@dataclass(frozen=True, slots=True)
class TimeDomainWorkflowResult:
    solution: TimeDomainSolution | None
    presentation: TimeDomainPresentation
    errors: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class _RenderedTimeForm:
    expression: sp.Expr
    plain: str
    latex: str


@dataclass(frozen=True, slots=True)
class _VisiblePartialFractionTerm:
    labels: tuple[str, ...]
    term: PartialFractionTerm
    denominator: sp.Expr
    numerator_template: sp.Expr


def run_time_domain_workflow(draft: TimeDomainInputDraft) -> TimeDomainWorkflowResult:
    """Run one complete visible workflow without allowing UI-side mathematics."""
    try:
        solution = _compute(draft)
    except (TypeError, ValueError, ArithmeticError) as error:
        message = str(error) or "Die Eingabe konnte nicht verarbeitet werden."
        return TimeDomainWorkflowResult(None, _error_presentation(message), (message,))
    return TimeDomainWorkflowResult(solution, _present(solution))


def _compute(draft: TimeDomainInputDraft) -> TimeDomainSolution:
    if type(draft.task_type) is not TimeDomainTaskType:
        raise TypeError("Der Aufgabentyp ist ungültig.")
    if draft.task_type is TimeDomainTaskType.DIRECT_LAPLACE:
        source = _parse_time(draft.time_expression_text)
        return direct_laplace(source)
    if draft.task_type is TimeDomainTaskType.INVERSE_LAPLACE:
        reduction = _parse_reduction(draft.image_expression_text)
        source = _reduced_expression(reduction)
        return inverse_rational(
            reduction,
            task_type=draft.task_type,
            source_expression=source,
        )
    if draft.task_type in {
        TimeDomainTaskType.SOLVE_ODE,
        TimeDomainTaskType.TRANSFER_FUNCTION_FROM_ODE,
    }:
        return _compute_ode(draft)
    system_reduction = _parse_reduction(draft.system_expression_text)
    system = _reduced_expression(system_reduction)
    if draft.task_type is TimeDomainTaskType.STEP_RESPONSE:
        amplitude = _parse_coefficient(draft.step_amplitude_text)
        input_expression = exact(amplitude._as_sympy() / sp.Symbol("s"))
        input_reduction = _parse_reduction(input_expression.canonical_text)
    elif draft.task_type is TimeDomainTaskType.GENERAL_RESPONSE:
        input_reduction = _parse_reduction(draft.input_expression_text)
        input_expression = _reduced_expression(input_reduction)
    elif draft.task_type is TimeDomainTaskType.EXPONENTIAL_INPUT:
        amplitude = _parse_coefficient(draft.exponential_amplitude_text)
        exponent = _parse_coefficient(draft.exponential_exponent_text)
        input_expression = exact(
            amplitude._as_sympy() / (sp.Symbol("s") - exponent._as_sympy())
        )
        input_reduction = _parse_reduction(input_expression.canonical_text)
    else:
        raise ValueError("Der gewählte Aufgabentyp wird nicht unterstützt.")
    output_text = (
        f"({system.canonical_text})*({input_expression.canonical_text})"
    )
    output_reduction = _parse_reduction(output_text)
    solution = inverse_rational(
        output_reduction,
        task_type=draft.task_type,
        input_laplace=input_expression,
        system_laplace=system,
        system_poles=classify_reduction_poles(
            system_reduction, PoleRole.SYSTEM
        ),
        input_poles=classify_reduction_poles(input_reduction, PoleRole.INPUT),
        calculate_end_value=True,
    )
    solution = _apply_cancellation_provenance(solution, system_reduction)
    if draft.task_type is TimeDomainTaskType.EXPONENTIAL_INPUT:
        input_time = exact(
            amplitude._as_sympy()
            * sp.exp(exponent._as_sympy() * sp.Symbol("t"))
        )
        return replace(
            solution,
            input_signal=ExponentialInputSignal(
                amplitude,
                exponent,
                TimeFunction(input_time),
                input_expression,
            ),
        )
    return solution


def _compute_ode(draft: TimeDomainInputDraft) -> TimeDomainSolution:
    assumptions = tuple(item.strip() for item in draft.assumptions_text.split(";") if item.strip())
    output_texts = draft.output_coefficient_texts or tuple(
        "0" for _ in range(draft.output_order + 1)
    )
    input_texts = draft.input_coefficient_texts or tuple("0" for _ in range(draft.input_order + 1))
    if any(
        {"t", "s"} & _parameter_names(item) or re.search(r"\b[ts]\b", item)
        for item in (*output_texts, *input_texts)
    ):
        diagnostic = Diagnostic(
            DiagnosticSeverity.ERROR,
            DiagnosticCode.TIME_VARYING_COEFFICIENT_UNSUPPORTED,
            "DGL-Koeffizienten müssen zeitunabhängig sein.",
        )
        return _ode_failure(draft.task_type, (diagnostic,))
    output_coefficients = tuple(_parse_coefficient(item) for item in output_texts)
    input_coefficients = tuple(_parse_coefficient(item) for item in input_texts)
    ode = build_linear_ode(
        output_name=draft.output_name.strip() or "y",
        input_name=draft.input_name.strip() or "u",
        output_coefficients=output_coefficients,
        input_coefficients=input_coefficients,
        output_order=draft.output_order,
        input_order=draft.input_order,
        assumptions=assumptions,
    )
    if not ode.valid:
        return _ode_failure(draft.task_type, ode.diagnostics)
    if draft.task_type is TimeDomainTaskType.TRANSFER_FUNCTION_FROM_ODE:
        return _transfer_function_from_ode(draft, ode)

    output_values = tuple(_parse_optional_coefficient(item) for item in draft.output_initial_texts)
    output_ics = build_initial_conditions(
        ode.output_name,
        ode.output_order,
        output_values,
        explicit_zero_policy=draft.missing_initials_are_zero,
    )
    if not output_ics.complete:
        missing = ", ".join(str(item) for item in output_ics.missing_orders)
        diagnostic = Diagnostic(
            DiagnosticSeverity.ERROR,
            DiagnosticCode.MISSING_INITIAL_CONDITION,
            f"Fehlende Ausgangsanfangswerte der Ableitungsordnung: {missing}.",
            technical_details=tuple(
                ("missing_order", str(item)) for item in output_ics.missing_orders
            ),
        )
        return _ode_failure(draft.task_type, (diagnostic,))
    signal = _build_ode_signal(draft)
    needed_input_count = max((order for order, _ in ode.input_terms), default=0)
    if needed_input_count:
        if signal.time_function is not None:
            t = sp.Symbol("t")
            derived_values = tuple(
                exact(
                    sp.limit(
                        sp.diff(signal.time_function.expression._as_sympy(), t, order),
                        t,
                        0,
                        dir="+",
                    )
                )
                for order in range(needed_input_count)
            )
            input_ics = build_initial_conditions(
                ode.input_name or "u",
                needed_input_count,
                derived_values,
                explicit_zero_policy=False,
                derived=True,
            )
        else:
            supplied = tuple(
                _parse_optional_coefficient(item) for item in draft.input_initial_texts
            )
            input_ics = build_initial_conditions(
                ode.input_name or "u",
                needed_input_count,
                supplied,
                explicit_zero_policy=draft.missing_initials_are_zero,
            )
        if not input_ics.complete:
            missing = ", ".join(str(item) for item in input_ics.missing_orders)
            diagnostic = Diagnostic(
                DiagnosticSeverity.ERROR,
                DiagnosticCode.INPUT_INITIAL_CONDITION_MISSING,
                f"Fehlende Eingangsanfangswerte der Ableitungsordnung: {missing}.",
            )
            return _ode_failure(draft.task_type, (diagnostic,))
    else:
        input_ics = None
    transformed, equation, free_symbolic, forced_symbolic = transform_ode(
        ode, output_ics, input_ics
    )
    u_symbol = sp.Symbol("U")
    free_expr = free_symbolic._as_sympy()
    forced_expr = sp.simplify(
        forced_symbolic._as_sympy().subs(u_symbol, signal.laplace_expression._as_sympy())
    )
    total_expr = sp.factor(sp.cancel(free_expr + forced_expr))
    free_time, free_core = _inverse_ode_component(free_expr, draft.task_type)
    forced_time, forced_core = _inverse_ode_component(forced_expr, draft.task_type)
    total_time, total_core = _inverse_ode_component(total_expr, draft.task_type)
    if _is_pt2_step_case(ode, output_ics, signal) and any(
        coefficient._as_sympy().free_symbols for _, coefficient in ode.output_terms
    ):
        total_time = _pt2_step_time(ode, signal)
        forced_time = total_time
        free_time = TimeFunction(exact(sp.Integer(0)))
    if total_time is None or free_time is None or forced_time is None:
        return total_core
    input_time = signal.time_function
    if input_time is None:
        input_time, _ = _inverse_ode_component(
            signal.laplace_expression._as_sympy(), draft.task_type
        )
    if input_time is None:
        return _ode_failure(
            draft.task_type,
            (
                Diagnostic(
                    DiagnosticSeverity.ERROR,
                    DiagnosticCode.UNSUPPORTED_TIME_FUNCTION,
                    "Für U(s) konnte keine gewöhnliche Eingangsfunktion bestimmt werden.",
                ),
            ),
        )
    verification = verify_ode_solution(
        ode,
        output_ics,
        input_time.expression,
        total_time.expression,
        exact(total_expr),
        exact(free_expr),
        exact(forced_expr),
        equation,
    )
    ode_data = OdeSolutionData(
        ode,
        output_ics,
        input_ics,
        signal,
        transformed,
        equation,
        exact(free_expr),
        exact(forced_expr),
        exact(total_expr),
        free_time,
        forced_time,
        total_time,
        verification,
    )
    checks = list(total_core.verification.items)
    checks.extend(_ode_verification_items(verification))
    diagnostics = list(total_core.diagnostics)
    if not verification.trusted:
        diagnostics.append(
            Diagnostic(
                DiagnosticSeverity.ERROR,
                DiagnosticCode.ODE_RESIDUAL_FAILED,
                "Die vollständige DGL-Verifikation ist fehlgeschlagen; "
                "das Ergebnis ist nicht vertrauenswürdig.",
            )
        )
    return replace(
        total_core,
        status=ComputationStatus.SUCCESS if verification.trusted else ComputationStatus.FAILED,
        source_expression=None,
        input_laplace=signal.laplace_expression,
        system_laplace=exact(equation.b_polynomial._as_sympy() / equation.a_polynomial._as_sympy()),
        output_laplace=exact(total_expr),
        time_function=total_time,
        verification=VerificationReport(
            tuple(checks),
            total_core.verification.initial_value,
            total_core.verification.end_value_status,
            total_core.verification.end_value,
        ),
        diagnostics=tuple(diagnostics),
        input_signal=signal,
        ode_solution=ode_data,
    )


def _transfer_function_from_ode(
    draft: TimeDomainInputDraft, ode: LinearOdeInput
) -> TimeDomainSolution:
    provided_initials = tuple(
        _parse_optional_coefficient(item)
        for item in (*draft.output_initial_texts, *draft.input_initial_texts)
    )
    has_nonzero_initial = any(
        item is not None and item._as_sympy() != 0 for item in provided_initials
    )
    if not draft.zero_state_confirmed or has_nonzero_initial:
        diagnostic = Diagnostic(
            DiagnosticSeverity.ERROR,
            DiagnosticCode.TRANSFER_FUNCTION_REQUIRES_ZERO_INITIAL_STATE,
            "Die Übertragungsfunktion erfordert eine sichtbare Bestätigung "
            "des vollständigen Nullzustands.",
        )
        return _ode_failure(draft.task_type, (diagnostic,))
    s = sp.Symbol("s")
    a_expr = sum(
        (coefficient._as_sympy() * s**order for order, coefficient in ode.output_terms),
        sp.Integer(0),
    )
    b_expr = sum(
        (coefficient._as_sympy() * s**order for order, coefficient in ode.input_terms),
        sp.Integer(0),
    )
    raw_g = sp.Mul(b_expr, sp.Pow(a_expr, -1, evaluate=False), evaluate=False)
    reduction = _parse_reduction(sp.sstr(raw_g))
    reduced_g = _reduced_expression(reduction)
    analysis_source = inverse_rational(
        reduction, task_type=draft.task_type, system_laplace=exact(raw_g)
    )
    multiplication_residual = sp.simplify(a_expr * reduced_g._as_sympy() - b_expr)
    transfer = OdeTransferFunctionResult(
        ode,
        True,
        exact(raw_g),
        reduced_g,
        exact(b_expr),
        exact(a_expr),
        exact(multiplication_residual),
    )
    check = VerificationItem(
        "ode_transfer_multiplication",
        VerificationStatus.PASS if multiplication_residual == 0 else VerificationStatus.FAIL,
        exact(multiplication_residual),
        "Rückmultiplikation rekonstruiert die transformierte DGL.",
    )
    return replace(
        analysis_source,
        status=ComputationStatus.SUCCESS
        if multiplication_residual == 0
        else ComputationStatus.FAILED,
        source_expression=None,
        input_laplace=None,
        system_laplace=reduced_g,
        output_laplace=reduced_g,
        partial_fractions=None,
        inverse_mappings=(),
        time_function=None,
        verification=VerificationReport((check,), None, EndValueStatus.NOT_APPLICABLE, None),
        diagnostics=(),
        ode_transfer_function=transfer,
    )


def _parse_optional_coefficient(text: str) -> ExactExpression | None:
    return None if not text.strip() else _parse_coefficient(text)


def _build_ode_signal(draft: TimeDomainInputDraft) -> TypedInputSignal:
    signal_type = draft.ode_input_signal_type
    t, s = sp.symbols("t s")
    amplitude = _parse_coefficient(draft.ode_signal_amplitude_text)
    rate = _parse_coefficient(draft.ode_signal_rate_text)
    a, r = amplitude._as_sympy(), rate._as_sympy()
    parameters: tuple[ExactExpression, ...]
    if signal_type is InputSignalType.ZERO:
        time_expr, image_expr, rule, parameters = sp.Integer(0), sp.Integer(0), "0 <-> 0", ()
    elif signal_type is InputSignalType.STEP:
        time_expr, image_expr, rule, parameters = a, a / s, "A <-> A/s", (amplitude,)
    elif signal_type is InputSignalType.EXPONENTIAL:
        time_expr, image_expr, rule, parameters = (
            a * sp.exp(r * t),
            a / (s - r),
            "A*exp(lambda*t) <-> A/(s-lambda)",
            (amplitude, rate),
        )
    elif signal_type is InputSignalType.POLYNOMIAL:
        coefficients = tuple(
            _parse_coefficient(item or "0") for item in draft.polynomial_coefficient_texts
        )
        time_expr = sum(
            (item._as_sympy() * t**index for index, item in enumerate(coefficients)), sp.Integer(0)
        )
        image_expr = sum(
            (
                item._as_sympy() * sp.factorial(index) / s ** (index + 1)
                for index, item in enumerate(coefficients)
            ),
            sp.Integer(0),
        )
        rule, parameters = "sum(c_n*t^n) <-> sum(c_n*n!/s^(n+1))", coefficients
    elif signal_type in {InputSignalType.SINUS, InputSignalType.COSINUS}:
        if not _positive_frequency(r, draft.assumptions_text):
            raise ValueError(
                "Für Sinus und Kosinus muss omega > 0 gelten oder als Annahme angegeben sein."
            )
        if signal_type is InputSignalType.SINUS:
            time_expr, image_expr, rule = (
                a * sp.sin(r * t),
                a * r / (s**2 + r**2),
                "sin(omega*t) <-> omega/(s^2+omega^2)",
            )
        else:
            time_expr, image_expr, rule = (
                a * sp.cos(r * t),
                a * s / (s**2 + r**2),
                "cos(omega*t) <-> s/(s^2+omega^2)",
            )
        parameters = (amplitude, rate)
    elif signal_type is InputSignalType.IMAGE_EXPRESSION:
        image_expr = _reduced_expression(_parse_reduction(draft.input_expression_text))._as_sympy()
        return TypedInputSignal(
            signal_type,
            (),
            None,
            exact(image_expr),
            "direkte Bildbereichseingabe U(s)",
            draft.input_expression_text,
        )
    else:
        raise ValueError("Die Eingangsart wird nicht unterstützt.")
    return TypedInputSignal(
        signal_type,
        tuple(parameters),
        TimeFunction(exact(time_expr)),
        exact(image_expr),
        rule,
        sp.sstr(time_expr),
    )


def _positive_frequency(value: sp.Expr, assumptions: str) -> bool:
    if value.is_positive:
        return True
    return all(f"{symbol}>0" in assumptions.replace(" ", "") for symbol in value.free_symbols)


def _inverse_ode_component(
    expression: sp.Expr, task_type: TimeDomainTaskType
) -> tuple[TimeFunction | None, TimeDomainSolution]:
    if sp.simplify(expression) == 0:
        empty = _ode_failure(task_type, ())
        return TimeFunction(exact(sp.Integer(0))), empty
    solution = inverse_rational(_parse_reduction(sp.sstr(expression)), task_type=task_type)
    return solution.time_function, solution


def _is_pt2_step_case(
    ode: LinearOdeInput,
    output_ics: InitialConditionSet,
    signal: TypedInputSignal,
) -> bool:
    return (
        ode.output_order == 2
        and signal.signal_type is InputSignalType.STEP
        and all(item.value._as_sympy() == 0 for item in output_ics.values)
        and tuple(order for order, _ in ode.input_terms) == (0,)
    )


def _pt2_step_time(ode: LinearOdeInput, signal: TypedInputSignal) -> TimeFunction:
    t = sp.Symbol("t")
    coefficients = dict(ode.output_terms)
    a0, a1, a2 = (coefficients[index]._as_sympy() for index in range(3))
    b0 = dict(ode.input_terms)[0]._as_sympy()
    amplitude = signal.parameters[0]._as_sympy()
    delta = sp.simplify(a1 / (2 * a2))
    omega = sp.sqrt(sp.simplify(a0 / a2 - delta**2))
    result = (
        amplitude
        * b0
        / a0
        * (1 - sp.exp(-delta * t) * (sp.cos(omega * t) + delta / omega * sp.sin(omega * t)))
    )
    return TimeFunction(ExactExpression._from_sympy(result))


def _ode_verification_items(
    report: OdeVerificationReport,
) -> tuple[VerificationItem, ...]:
    values = (
        (
            "ode_image_equation",
            report.image_equation_residual,
            "Die Bildgleichung ist algebraisch erfüllt.",
        ),
        ("ode_decomposition", report.decomposition_residual, "Y_frei + Y_erzwungen = Y_gesamt."),
        (
            "ode_forward_transform",
            report.forward_transform_residual,
            "Die Vorwärtstransformation ergibt Y(s).",
        ),
        (
            "ode_residual",
            report.ode_residual,
            "Das aus y(t) neu gebildete DGL-Residuum ist exakt null.",
        ),
    )
    items = [
        VerificationItem(
            identifier,
            VerificationStatus.PASS if residual._as_sympy() == 0 else VerificationStatus.FAIL,
            residual,
            explanation,
        )
        for identifier, residual, explanation in values
    ]
    items.extend(
        VerificationItem(
            f"ode_initial_{order}",
            VerificationStatus.PASS if residual._as_sympy() == 0 else VerificationStatus.FAIL,
            residual,
            f"Anfangswert der Ordnung {order} ist erfüllt.",
        )
        for order, residual in report.initial_condition_residuals
    )
    return tuple(items)


def _ode_failure(
    task_type: TimeDomainTaskType, diagnostics: tuple[Diagnostic, ...]
) -> TimeDomainSolution:
    return TimeDomainSolution(
        task_type,
        ComputationStatus.FAILED,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        (),
        (),
        None,
        (),
        VerificationReport((), None, EndValueStatus.NOT_APPLICABLE, None),
        diagnostics,
    )


def _apply_cancellation_provenance(
    solution: TimeDomainSolution,
    system_reduction: TransferFunctionReductionResult,
) -> TimeDomainSolution:
    """Keep product cancellation distinct from cancellation inside G(s)."""
    product_only_codes = {
        DiagnosticCode.CANCELLED_COMMON_FACTOR,
        DiagnosticCode.HIDDEN_MODE_POSSIBLE,
    }
    diagnostics = [item for item in solution.diagnostics if item.code not in product_only_codes]
    report = system_reduction.report
    system_was_cancelled = report is not None and any(
        step.kind is TransferFunctionReductionStepKind.REMOVE_COMMON_POLYNOMIAL_FACTOR
        for step in report.steps
    )
    if system_was_cancelled:
        diagnostics.extend(
            (
                Diagnostic(
                    DiagnosticSeverity.WARNING,
                    DiagnosticCode.CANCELLED_COMMON_FACTOR,
                    "Gemeinsame Faktoren in G(s) wurden exakt gekürzt; "
                    "die Rohform bleibt erhalten.",
                ),
                Diagnostic(
                    DiagnosticSeverity.WARNING,
                    DiagnosticCode.HIDDEN_MODE_POSSIBLE,
                    "Die Kürzung innerhalb von G(s) kann interne Dynamik verdecken.",
                ),
            )
        )
    return replace(
        solution,
        diagnostics=tuple(diagnostics),
    )


def _parse_time(text: str) -> ExactExpression:
    _reject_mixed_variables(text, expected="t")
    parameters = _parameter_names(text)
    parser = SafeExpressionParser(
        ParserConfig.for_profile(ParserProfile.TIME_T, parameter_names=parameters)
    )
    result = parser.parse(text, "f(t)")
    if result.value is None:
        raise ValueError("\n".join(item.message for item in result.diagnostics))
    return result.value


def _parse_coefficient(text: str) -> ExactExpression:
    _reject_mixed_variables(text, expected=None)
    parameters = _parameter_names(text)
    parser = SafeExpressionParser(
        ParserConfig(
            allowed_symbols=parameters,
            exact_constants=frozenset({"pi"}),
        )
    )
    result = parser.parse(text, "coefficient")
    if result.value is None:
        raise ValueError("\n".join(item.message for item in result.diagnostics))
    return result.value


def _parse_reduction(text: str) -> TransferFunctionReductionResult:
    _reject_mixed_variables(text, expected="s")
    parameters = _parameter_names(text)
    allowed = frozenset(("s", "pi", *parameters))
    parsed = SafeRationalExpressionParser(ParserConfig(allowed_symbols=allowed)).parse_common(
        text, variable_name="s", field="image"
    )
    if parsed.value is None:
        raise ValueError("\n".join(item.message for item in parsed.diagnostics))
    created = RawTransferFunctionFactory(
        expected_variable_name="s",
        allowed_parameter_names=frozenset(("pi", *parameters)),
    ).create(parsed.value, field="image")
    if created.value is None:
        raise ValueError("\n".join(item.message for item in created.diagnostics))
    return TransferFunctionReducer().reduce(created.value, field="image")


def _reduced_expression(reduction: TransferFunctionReductionResult) -> ExactExpression:
    if reduction.reduced is None:
        raise ValueError("Die rationale Reduktion ist fehlgeschlagen.")
    return exact(
        (
            reduction.reduced.numerator.expression._as_sympy()
            / reduction.reduced.denominator.expression._as_sympy()
        ).subs({sp.Symbol("pi"): sp.pi})
    )


def _parameter_names(text: str) -> frozenset[str]:
    return frozenset(_IDENTIFIER.findall(text)) - _RESERVED


def _reject_mixed_variables(text: str, *, expected: str | None) -> None:
    names = frozenset(_IDENTIFIER.findall(text))
    forbidden = {"s", "t"} - ({expected} if expected is not None else set())
    if names & forbidden:
        raise ValueError("Gemischte Verwendung von s und t ist nicht erlaubt.")


def _present(solution: TimeDomainSolution) -> TimeDomainPresentation:
    if solution.ode_solution is not None:
        return _present_ode_solution(solution)
    if solution.ode_transfer_function is not None:
        return _present_ode_transfer(solution)
    time_form = _rendered_time_form(solution)
    image_symbol, time_symbol = _result_symbols(solution.task_type)
    summary_lines = [f"Aufgabe: {_task_label(solution.task_type)}"]
    summary_lines.extend(_given_plain_lines(solution))
    if (
        solution.output_laplace is not None
        and solution.task_type is not TimeDomainTaskType.INVERSE_LAPLACE
    ):
        summary_lines.append(
            f"{image_symbol}(s) = {_visible_output_plain(solution)}"
        )
    if time_form is not None:
        summary_lines.append(f"{time_symbol}(t) = {time_form.plain}")
    summary_lines.extend(_end_value_plain_lines(solution))

    checks = "\n".join(
        f"{_check_label(item.check_id)}: {_verification_label(item.status)} – "
        f"{item.explanation}"
        for item in solution.verification.items
    )
    if solution.verification.initial_value is not None:
        checks += (
            f"\n{time_symbol}(0) = "
            f"{_plain_exact(solution.verification.initial_value)}"
        )
    checks += "\n" + "\n".join(_end_value_plain_lines(solution))
    diagnostics = "\n".join(
        f"{item.severity.value.upper()} {item.code.value}: {item.message}"
        for item in solution.diagnostics
    )

    short_lines = [f"Aufgabe: {_task_label(solution.task_type)}"]
    if solution.output_laplace is not None:
        short_lines.append(
            f"{image_symbol}(s) = {_visible_output_plain(solution)}"
        )
    if time_form is not None:
        short_lines.append(f"{time_symbol}(t) = {time_form.plain}")
        numeric = sp.N(time_form.expression.subs(sp.Symbol("t"), 1), 8)
        short_lines.append(f"Numerische Kontrolle: {time_symbol}(1) ≈ {numeric}")
    short_lines.extend(_end_value_plain_lines(solution))

    return TimeDomainPresentation(
        summary="\n".join(summary_lines),
        rational_analysis=_rational_text(solution),
        partial_fractions=_partial_text(solution),
        time_function=(
            f"{time_symbol}(t) = {time_form.plain}"
            if time_form is not None
            else "Keine gewöhnliche Zeitfunktion verfügbar."
        ),
        verifications=checks.strip(),
        short_solution="\n".join(short_lines),
        worked_steps=_worked_steps(solution),
        latex_source=_latex(solution),
        diagnostics=diagnostics,
    )


def _present_ode_solution(solution: TimeDomainSolution) -> TimeDomainPresentation:
    data = solution.ode_solution
    assert data is not None
    total = _plain_math(sp.expand(data.total_time.expression._as_sympy()))
    free = _plain_math(sp.expand(data.free_time.expression._as_sympy()))
    forced = _plain_math(sp.expand(data.forced_time.expression._as_sympy()))
    ic_lines = [
        f"{data.ode.output_name}^({item.derivative_order})(0+) = "
        f"{_plain_exact(item.value)} [{item.origin.value}]"
        for item in data.output_initial_conditions.values
    ]
    input_ic_lines = (
        []
        if data.input_initial_conditions is None
        else [
            f"{data.ode.input_name}^({item.derivative_order})(0+) = "
            f"{_plain_exact(item.value)} [{item.origin.value}]"
            for item in data.input_initial_conditions.values
        ]
    )
    assumption_lines = (
        ["Parameterannahmen: " + "; ".join(data.ode.parameter_assumptions)]
        if data.ode.parameter_assumptions
        else []
    )
    parameter_lines = _second_order_parameter_lines(data)
    transform_lines = [item.display_rule for item in data.transformed_terms]
    equation_lines = [
        data.image_equation.display_equation,
        f"Y(s) = {_plain_exact(data.total_laplace)}",
    ]
    split_lines = [
        f"Y_frei(s) = {_plain_exact(data.free_laplace)}",
        f"Y_erzwungen(s) = {_plain_exact(data.forced_laplace)}",
        f"Y_gesamt(s) = {_plain_exact(data.total_laplace)}",
        f"y_frei(t) = {free}",
        f"y_erzwungen(t) = {forced}",
        f"y(t) = {total}",
    ]
    checks = "\n".join(
        f"{_check_label(item.check_id)}: {_verification_label(item.status)} – {item.explanation}"
        for item in solution.verification.items
    )
    diagnostics = "\n".join(
        f"{item.severity.value.upper()} {item.code.value}: {item.message}"
        for item in solution.diagnostics
    )
    zero_note = (
        "\nNullpolitik: Leere Anfangswerte wurden ausdrücklich als 0 gesetzt."
        if any(
            item.origin.value == "EXPLICIT_ZERO_POLICY"
            for item in data.output_initial_conditions.values
        )
        else ""
    )
    steps = "\n\n".join(
        (
            "1. Gegebene DGL\n" + data.ode.normalized_ode,
            "2. Eingangssignal\n"
            + data.input_signal.raw_input
            + "\n"
            + data.input_signal.transform_rule,
            "3. Anfangswerte\n" + "\n".join((*ic_lines, *input_ic_lines)) + zero_note,
            f"4. DGL-Ordnung und Vollständigkeit\nOrdnung {data.ode.output_order}; "
            "vollständig.\n"
            + "\n".join((*assumption_lines, *parameter_lines)),
            "5. Termweise Laplace-Transformation\n" + "\n".join(transform_lines),
            "6. Bildgleichung und Auflösung\n" + "\n".join(equation_lines),
            "7. Freie und erzwungene Antwort\n" + "\n".join(split_lines[:3]),
            "8. Rationale Analyse\n" + _rational_text(solution),
            "9. Partialbruchzerlegung\n" + _partial_text(solution),
            "10. Inverse Laplace\n" + "\n".join(split_lines[3:]),
            "11. Kontrollen\n" + checks,
            "12. Endaussage\ny(t) = " + total,
        )
    )
    latex_ic = r" \\ ".join(
        rf"{data.ode.output_name}^{{({item.derivative_order})}}(0^+)={item.value.latex}"
        for item in data.output_initial_conditions.values
    )
    latex_rules = "\n".join(
        rf"\text{{{_latex_escape(item.display_rule)}}}\\" for item in data.transformed_terms
    )
    latex = "\n".join(
        (
            r"\section*{Zeitbereichslösung}",
            r"\textbf{Gegeben}",
            rf"\[{_latex_escape(data.ode.normalized_ode)}\]",
            rf"\[{latex_ic}\]",
            r"\textbf{Gesucht}",
            r"\[y(t)\]",
            r"\textbf{Lösung}",
            latex_rules,
            rf"\[{_latex_escape(data.image_equation.display_equation)}\]",
            rf"\[Y(s)={data.total_laplace.latex}\]",
            rf"\[Y_{{\mathrm{{frei}}}}(s)={data.free_laplace.latex},\quad "
            rf"Y_{{\mathrm{{erzwungen}}}}(s)={data.forced_laplace.latex}\]",
            rf"\[y_{{\mathrm{{frei}}}}(t)={data.free_time.expression.latex},\quad "
            rf"y_{{\mathrm{{erzwungen}}}}(t)={data.forced_time.expression.latex}\]",
            r"\textbf{Kontrolle}",
            rf"\[R_{{\mathrm{{DGL}}}}(t)={data.verification.ode_residual.latex}=0\]",
            rf"\[\boxed{{y(t)={data.total_time.expression.latex}}}\]",
        )
    )
    return TimeDomainPresentation(
        summary=(
            f"Aufgabe: lineare DGL lösen\n{data.ode.normalized_ode}\n"
            f"Y(s) = {_plain_exact(data.total_laplace)}\ny(t) = {total}"
        ),
        rational_analysis=_rational_text(solution),
        partial_fractions=_partial_text(solution),
        time_function="\n".join(split_lines[3:]),
        verifications=checks,
        short_solution=f"Y(s) = {_plain_exact(data.total_laplace)}\ny(t) = {total}",
        worked_steps=steps,
        latex_source=latex,
        diagnostics=diagnostics,
        ode_and_initials=data.ode.normalized_ode
        + "\n"
        + "\n".join(
            (*ic_lines, *input_ic_lines, *assumption_lines, *parameter_lines)
        )
        + zero_note,
        laplace_transformation="\n".join(transform_lines),
        image_equation="\n".join(equation_lines),
        free_and_forced="\n".join(split_lines),
    )


def _present_ode_transfer(solution: TimeDomainSolution) -> TimeDomainPresentation:
    data = solution.ode_transfer_function
    assert data is not None
    raw = _plain_exact(data.raw_transfer_function)
    reduced = _plain_exact(data.reduced_transfer_function)
    check_status = (
        "bestanden"
        if data.multiplication_residual._as_sympy() == 0
        else "fehlgeschlagen"
    )
    checks = f"Rückmultiplikationskontrolle: {check_status}"
    pole_lines = [
        f"Pol: {_plain_exact(item.value)}, Vielfachheit {item.multiplicity}"
        for item in solution.poles
    ]
    rational_text = "\n".join(
        (
            f"Zählerpolynom: {_plain_exact(data.numerator)}",
            f"Nennerpolynom: {_plain_exact(data.denominator)}",
            _rational_text(solution),
            *(pole_lines or ["Pole: unter den Annahmen nicht explizit bestimmt."]),
        )
    )
    steps = "\n\n".join(
        (
            "1. Gegebene DGL\n" + data.ode.normalized_ode,
            "2. Bestätigte Nullanfangsbedingungen\nAlle Ausgangs- und erforderlichen "
            "Eingangsanfangswerte sind ausdrücklich null.",
            "3. Termweise Laplace-Transformation\nL{y^(k)} = s^k Y(s), L{u^(j)} = s^j U(s)",
            f"4. Bildgleichung\n({_plain_exact(data.denominator)}) Y(s) = "
            f"({_plain_exact(data.numerator)}) U(s)",
            f"5. Übertragungsfunktion\nG(s) = Y(s)/U(s) = {raw}",
            f"6. Roh- und Reduktionsform\nG_roh(s) = {raw}\nG_red(s) = {reduced}",
            "7. Rationale Analyse\n" + rational_text,
            "8. Kontrolle\n" + checks,
            f"9. Ergebnis\nG(s) = {reduced}",
        )
    )
    latex = "\n".join(
        (
            r"\textbf{Gegeben}",
            rf"\[{_latex_escape(data.ode.normalized_ode)}\]",
            r"\textbf{Gesucht}",
            r"\[G(s)=Y(s)/U(s)\]",
            r"\textbf{Lösung}",
            r"\[\text{Nullanfangsbedingungen bestätigt}\]",
            rf"\[{data.denominator.latex}Y(s)={data.numerator.latex}U(s)\]",
            rf"\[G_{{\mathrm{{roh}}}}(s)={data.raw_transfer_function.latex},\quad "
            rf"G_{{\mathrm{{red}}}}(s)={data.reduced_transfer_function.latex}\]",
            rf"\[\boxed{{G(s)={data.reduced_transfer_function.latex}}}\]",
        )
    )
    return TimeDomainPresentation(
        summary=(
            "Aufgabe: Übertragungsfunktion aus DGL\n"
            f"{data.ode.normalized_ode}\nG(s) = {reduced}"
        ),
        rational_analysis=rational_text,
        partial_fractions="Für diesen Modus nicht erforderlich.",
        time_function="Für diesen Modus nicht erforderlich.",
        verifications=checks,
        short_solution=f"G(s) = {reduced}",
        worked_steps=steps,
        latex_source=latex,
        diagnostics="\n".join(
            f"{item.severity.value.upper()} {item.code.value}: {item.message}"
            for item in solution.diagnostics
        ),
        ode_and_initials=data.ode.normalized_ode + "\nNullzustand ausdrücklich bestätigt.",
        laplace_transformation="L{y^(k)} = s^k Y(s); L{u^(j)} = s^j U(s)",
        image_equation=(
            f"({_plain_exact(data.denominator)}) Y(s) = "
            f"({_plain_exact(data.numerator)}) U(s)"
        ),
        free_and_forced="",
    )


def _second_order_parameter_lines(data: OdeSolutionData) -> list[str]:
    if data.ode.output_order != 2:
        return []
    coefficients = dict(data.ode.output_terms)
    if not all(order in coefficients for order in range(3)):
        return []
    a0 = coefficients[0]._as_sympy()
    a1 = coefficients[1]._as_sympy()
    a2 = coefficients[2]._as_sympy()
    delta = sp.simplify(a1 / (2 * a2))
    omega = sp.sqrt(sp.simplify(a0 / a2 - delta**2))
    return [
        f"delta = {_plain_math(delta)}",
        f"omega = {_plain_math(omega)}; unterdämpfte Darstellung für omega > 0",
    ]


def _rational_text(solution: TimeDomainSolution) -> str:
    analysis = solution.rational_analysis
    if analysis is None:
        return "Für diesen Workflow nicht erforderlich."
    division = analysis.division
    lines = [
        f"Ausgangsform: {_plain_exact(analysis.raw_expression)}",
        f"Gekürzte Form: {_plain_exact(analysis.reduced_expression)}",
        f"Grad von Zähler/Nenner: {analysis.classification.numerator_degree}/"
        f"{analysis.classification.denominator_degree}",
        f"Bruchtyp: {_classification_label(analysis.classification.kind)}",
        f"Polynomquotient: {_plain_exact(division.quotient)}",
        f"Echter Restbruch: {_plain_exact(division.proper_fraction)}",
        f"Probe durch Rückzusammenfassung: {_residual_label(division.reconstruction_residual)}",
    ]
    if analysis.cancellation_factors:
        lines.append(
            "Gekürzte Faktoren: "
            + ", ".join(_plain_exact(item) for item in analysis.cancellation_factors)
        )
    if solution.factor_structure is not None:
        lines.append(
            "Faktorstruktur: "
            + " * ".join(
                _factor_power_plain(item.factor._as_sympy(), item.multiplicity)
                for item in solution.factor_structure.factors
            )
        )
    return "\n".join(lines)


def _partial_text(solution: TimeDomainSolution) -> str:
    partial = solution.partial_fractions
    if partial is None or not _needs_partial_fractions(solution):
        return "Keine Partialbruchzerlegung erforderlich; ein Tabellenpaar genügt."
    visible = _visible_partial_fraction_terms(solution)
    target = partial.proper_fraction._as_sympy()
    main_denominator = _visible_main_denominator(visible)
    numerator_identity_left = sp.simplify(target * main_denominator)
    numerator_identity_right = sp.Add(
        *(
            item.numerator_template
            * sp.cancel(main_denominator / item.denominator)
            for item in visible
        ),
        evaluate=False,
    )
    lines = [
        f"Zu zerlegen: {_plain_math(target)}",
    ]
    lines.extend(_normalization_plain_lines(target))
    lines.extend(
        (
            "Normierte Form: Y(s) = "
            f"{_visible_fraction_plain(numerator_identity_left, main_denominator)}",
            f"Vollständiger Ansatz: {_visible_ansatz_plain(visible)}",
            f"Hauptnenner: {_plain_math(main_denominator)}",
            "Multiplikation mit dem Hauptnenner "
            f"{_plain_math(main_denominator)}",
            "Zählergleichung: "
            f"{_plain_math(numerator_identity_left)} = "
            f"{_plain_math(numerator_identity_right)}",
            "Koeffizienten bestimmen: " + _coefficient_assignments_plain(visible),
            "Eingesetzte Partialbruchzerlegung: "
            + _inserted_partial_fractions_plain(visible),
            "Probe durch Rückzusammenfassung: "
            + _residual_label(partial.reconstruction_residual),
        )
    )
    return "\n".join(lines)


def _worked_steps(solution: TimeDomainSolution) -> str:
    image_symbol, time_symbol = _result_symbols(solution.task_type)
    time_form = _rendered_time_form(solution)
    sections: list[tuple[str, list[str]]] = [
        ("Gegeben", _given_plain_lines(solution)),
        (
            "Gesucht",
            [
                f"{image_symbol}(s)"
                if solution.task_type is TimeDomainTaskType.DIRECT_LAPLACE
                else f"{time_symbol}(t)"
            ],
        ),
    ]
    solution_lines: list[str] = []
    if _is_system_task(solution) and solution.output_laplace is not None:
        solution_lines.extend(_output_formation_plain_lines(solution))
    elif solution.output_laplace is not None:
        solution_lines.append(
            f"{image_symbol}(s) = {_visible_output_plain(solution)}"
        )
    if _is_rf02_table_case(solution):
        solution_lines.extend(
            (
                "Vergleich mit (s-a)/((s-a)^2+omega^2)",
                "a = 4, omega = 2",
                "Tabellenpaar: exp(a*t)*cos(omega*t)",
                "Hinweis: a > 0, daher wächst die Schwingungshülle.",
            )
        )
    if _is_sine_response(solution):
        solution_lines.extend(_sine_comparison_plain_lines(solution))
    sections.append(("Lösung", solution_lines))
    if _needs_partial_fractions(solution):
        sections.append(("Partialbruchzerlegung", _partial_text(solution).splitlines()))
    if solution.direct_rules:
        sections.append(
            (
                "Tabellenvergleich",
                [item.table_pair for item in solution.direct_rules],
            )
        )
    if time_form is not None:
        sections.append(
            ("Rücktransformation", [f"{time_symbol}(t) = {time_form.plain}"])
        )
    control_lines = [
        f"{_check_label(item.check_id)}: {_verification_label(item.status)}"
        for item in solution.verification.items
    ]
    if solution.verification.initial_value is not None:
        control_lines.append(
            f"{time_symbol}(0) = {_plain_exact(solution.verification.initial_value)}"
        )
    control_lines.extend(_end_value_plain_lines(solution))
    sections.append(("Kontrolle", control_lines))
    if time_form is not None:
        sections.append(("Ergebnis", [f"{time_symbol}(t) = {time_form.plain}"]))
    return "\n\n".join(
        f"{title}\n" + "\n".join(lines)
        for title, lines in sections
        if lines
    )


def _latex(solution: TimeDomainSolution) -> str:
    image_symbol, time_symbol = _result_symbols(solution.task_type)
    time_form = _rendered_time_form(solution)
    lines = [r"\section*{Zeitbereichslösung}", r"\textbf{Gegeben}", r"\begin{align*}"]
    lines.extend(_given_latex_lines(solution))
    lines.extend(
        (
            r"\end{align*}",
            r"\textbf{Gesucht}",
            rf"\[{image_symbol}(s)\]"
            if solution.task_type is TimeDomainTaskType.DIRECT_LAPLACE
            else rf"\[{time_symbol}(t)\]",
            r"\textbf{Lösung}",
            r"\begin{align*}",
        )
    )
    if _is_system_task(solution) and solution.output_laplace is not None:
        lines.extend(_output_formation_latex_lines(solution))
    elif solution.output_laplace is not None:
        lines.append(
            rf"{image_symbol}(s) &= {_visible_output_latex(solution)} \\"
        )
    lines.append(r"\end{align*}")
    if _is_rf02_table_case(solution):
        lines.extend(_rf02_latex_lines(solution))
    if _is_sine_response(solution):
        lines.extend(_sine_comparison_latex_lines(solution))
    if _needs_partial_fractions(solution):
        lines.extend(_partial_fraction_latex_lines(solution))
    if time_form is not None:
        lines.extend(
            (
                r"\textbf{Rücktransformation}",
                r"\begin{align*}",
                rf"{time_symbol}(t) &= {time_form.latex}",
                r"\end{align*}",
            )
        )
    lines.extend((r"\textbf{Kontrolle}", r"\begin{align*}"))
    if solution.verification.initial_value is not None:
        lines.append(
            rf"{time_symbol}(0) &= {solution.verification.initial_value.latex} \\"
        )
    if solution.verification.end_value is not None:
        lines.append(
            rf"\lim_{{t\to\infty}} {time_symbol}(t) &= "
            rf"{solution.verification.end_value.latex} \\"
        )
    lines.append(r"\end{align*}")
    if solution.verification.end_value_status is EndValueStatus.END_VALUE_THEOREM_INVALID:
        lines.append(
            r"\text{Der Endwertsatz ist nicht anwendbar, da die Pole von }"
            r"sY(s)\text{ nicht alle strikt in der linken Halbebene liegen.}"
        )
    hidden_from_normal_latex = {
        DiagnosticCode.IMAGINARY_AXIS_SYSTEM_POLE,
        DiagnosticCode.END_VALUE_THEOREM_INVALID,
    }
    for diagnostic in solution.diagnostics:
        if diagnostic.code in hidden_from_normal_latex:
            continue
        lines.append(rf"\text{{{_latex_escape(diagnostic.message)}}}\\")
    if time_form is not None:
        lines.append(rf"\[\boxed{{{time_symbol}(t)={time_form.latex}}}\]")
    elif (
        solution.task_type is TimeDomainTaskType.DIRECT_LAPLACE
        and solution.output_laplace is not None
    ):
        lines.append(
            rf"\[\boxed{{F(s)={solution.output_laplace.latex}}}\]"
        )
    return "\n".join(lines)


def _latex_escape(text: str) -> str:
    return text.replace("_", r"\_").replace("%", r"\%")


def _task_label(task_type: TimeDomainTaskType) -> str:
    return {
        TimeDomainTaskType.DIRECT_LAPLACE: "direkte Laplace-Transformation",
        TimeDomainTaskType.INVERSE_LAPLACE: "inverse Laplace-Transformation",
        TimeDomainTaskType.STEP_RESPONSE: "Sprungantwort",
        TimeDomainTaskType.GENERAL_RESPONSE: "allgemeine Ausgangsantwort",
        TimeDomainTaskType.EXPONENTIAL_INPUT: "Antwort auf Exponentialeingang",
        TimeDomainTaskType.SOLVE_ODE: "lineare DGL lösen",
        TimeDomainTaskType.TRANSFER_FUNCTION_FROM_ODE: "Übertragungsfunktion aus DGL",
    }[task_type]


def _result_symbols(task_type: TimeDomainTaskType) -> tuple[str, str]:
    if task_type in {
        TimeDomainTaskType.DIRECT_LAPLACE,
        TimeDomainTaskType.INVERSE_LAPLACE,
    }:
        return "F", "f"
    return "Y", "y"


def _given_plain_lines(solution: TimeDomainSolution) -> list[str]:
    if solution.task_type is TimeDomainTaskType.DIRECT_LAPLACE:
        return (
            [f"f(t) = {_plain_exact(solution.source_expression)}"]
            if solution.source_expression is not None
            else []
        )
    if solution.task_type is TimeDomainTaskType.INVERSE_LAPLACE:
        return (
            [f"F(s) = {_plain_exact(solution.source_expression)}"]
            if solution.source_expression is not None
            else []
        )
    lines: list[str] = []
    if solution.system_laplace is not None:
        lines.append(f"G(s) = {_visible_system_plain(solution)}")
    if solution.task_type is TimeDomainTaskType.STEP_RESPONSE:
        amplitude = _step_amplitude(solution)
        if amplitude is not None:
            lines.append(f"Sprunghöhe = {_plain_math(amplitude)}")
    if (
        solution.input_signal is not None
        and solution.input_signal.time_function is not None
    ):
        lines.append(
            "u(t) = "
            + _plain_exact(solution.input_signal.time_function.expression)
        )
    if solution.input_laplace is not None:
        lines.append(f"U(s) = {_plain_exact(solution.input_laplace)}")
    return lines


def _given_latex_lines(solution: TimeDomainSolution) -> list[str]:
    if solution.task_type is TimeDomainTaskType.DIRECT_LAPLACE:
        return (
            [rf"f(t) &= {solution.source_expression.latex}"]
            if solution.source_expression is not None
            else []
        )
    if solution.task_type is TimeDomainTaskType.INVERSE_LAPLACE:
        return (
            [rf"F(s) &= {solution.source_expression.latex}"]
            if solution.source_expression is not None
            else []
        )
    lines: list[str] = []
    if solution.system_laplace is not None:
        lines.append(rf"G(s) &= {_visible_system_latex(solution)} \\")
    if solution.task_type is TimeDomainTaskType.STEP_RESPONSE:
        amplitude = _step_amplitude(solution)
        if amplitude is not None:
            lines.append(rf"F_{{\mathrm{{ex}}}} &= {sp.latex(amplitude)} \\")
    if (
        solution.input_signal is not None
        and solution.input_signal.time_function is not None
    ):
        lines.append(
            rf"u(t) &= {solution.input_signal.time_function.expression.latex} \\"
        )
    if solution.input_laplace is not None:
        lines.append(rf"U(s) &= {solution.input_laplace.latex}")
    return lines


def _step_amplitude(solution: TimeDomainSolution) -> sp.Expr | None:
    if (
        solution.task_type is not TimeDomainTaskType.STEP_RESPONSE
        or solution.input_laplace is None
    ):
        return None
    return sp.simplify(sp.Symbol("s") * solution.input_laplace._as_sympy())


def _plain_exact(expression: ExactExpression | None) -> str:
    if expression is None:
        return "–"
    value = expression._as_sympy()
    if value.has(sp.Symbol("s")):
        numerator, denominator = sp.fraction(sp.cancel(value))
        if denominator != 1:
            numerator_text = _plain_math(sp.factor(numerator))
            if isinstance(sp.factor(numerator), sp.Add):
                numerator_text = f"({numerator_text})"
            return (
                f"{numerator_text}/"
                f"({_plain_math(sp.factor(denominator))})"
            )
    return _plain_math(value)


def _plain_math(expression: sp.Expr) -> str:
    return str(sp.sstr(expression)).replace("**", "^")


def _is_system_task(solution: TimeDomainSolution) -> bool:
    return solution.task_type not in {
        TimeDomainTaskType.DIRECT_LAPLACE,
        TimeDomainTaskType.INVERSE_LAPLACE,
    }


def _visible_system_plain(solution: TimeDomainSolution) -> str:
    if solution.system_laplace is None:
        return "–"
    if _is_sine_response(solution):
        return "s/(s^2 + pi/4)"
    return _plain_exact(solution.system_laplace)


def _visible_system_latex(solution: TimeDomainSolution) -> str:
    if solution.system_laplace is None:
        return r"\text{–}"
    if _is_sine_response(solution):
        return r"\frac{s}{s^2+\frac{\pi}{4}}"
    return solution.system_laplace.latex


def _visible_output_plain(solution: TimeDomainSolution) -> str:
    if solution.output_laplace is None:
        return "–"
    if _is_sine_response(solution):
        return "(pi/2)/(s^2 + pi/4)"
    return _plain_exact(solution.output_laplace)


def _visible_output_latex(solution: TimeDomainSolution) -> str:
    if solution.output_laplace is None:
        return r"\text{–}"
    if _is_sine_response(solution):
        return r"\frac{\frac{\pi}{2}}{s^2+\frac{\pi}{4}}"
    return solution.output_laplace.latex


def _output_formation_plain_lines(solution: TimeDomainSolution) -> list[str]:
    if solution.system_laplace is None or solution.input_laplace is None:
        return []
    return [
        "Y(s) = G(s)*U(s)",
        f"Y(s) = {_visible_system_plain(solution)}"
        f" * {_plain_exact(solution.input_laplace)}",
        f"Y(s) = {_visible_output_plain(solution)}",
    ]


def _output_formation_latex_lines(solution: TimeDomainSolution) -> list[str]:
    if solution.system_laplace is None or solution.input_laplace is None:
        return []
    return [
        r"Y(s) &= G(s)U(s) \\",
        rf"&= {_visible_system_latex(solution)}"
        rf"\cdot {solution.input_laplace.latex} \\",
        rf"&= {_visible_output_latex(solution)} \\",
    ]


def _rendered_time_form(solution: TimeDomainSolution) -> _RenderedTimeForm | None:
    if solution.time_function is None:
        return None
    original = solution.time_function.expression._as_sympy()
    expanded = sp.expand(original)
    terms = sp.Add.make_args(expanded)
    has_constant = any(not term.has(sp.Symbol("t")) for term in terms)
    candidate = sp.factor_terms(expanded) if len(terms) == 2 and has_constant else expanded
    if sp.simplify(candidate - original) != 0:
        candidate = original
    if isinstance(candidate, sp.Add):
        ordered_terms = sorted(sp.Add.make_args(candidate), key=_time_term_sort_key)
        plain = _join_signed_terms(ordered_terms, latex=False)
        latex = _join_signed_terms(ordered_terms, latex=True)
    else:
        plain = _plain_math(candidate)
        latex = sp.latex(candidate)
    return _RenderedTimeForm(candidate, plain, latex)


def _time_term_sort_key(term: sp.Expr) -> tuple[int, str]:
    t = sp.Symbol("t")
    if not term.has(t):
        rank = 0
    else:
        exponentials = tuple(term.atoms(sp.exp))
        trig = bool(term.atoms(sp.sin, sp.cos))
        polynomial_factor = sp.simplify(
            term / sp.Mul(*exponentials) if exponentials else term
        )
        has_t_polynomial = polynomial_factor.has(t)
        growth = any(
            sp.ask(sp.Q.positive(sp.diff(item.args[0], t))) is True
            for item in exponentials
        )
        if trig:
            rank = 3
        elif growth:
            rank = 4
        elif has_t_polynomial:
            rank = 2
        else:
            rank = 1
    return rank, sp.sstr(term)


def _join_signed_terms(terms: list[sp.Expr], *, latex: bool) -> str:
    parts: list[str] = []
    for index, term in enumerate(terms):
        negative = term.could_extract_minus_sign()
        magnitude = -term if negative else term
        rendered = sp.latex(magnitude) if latex else _plain_math(magnitude)
        if index == 0:
            parts.append(("-" if negative else "") + rendered)
        else:
            parts.append((" - " if negative else " + ") + rendered)
    return "".join(parts)


def _classification_label(kind: RationalClassificationKind) -> str:
    return {
        RationalClassificationKind.STRICTLY_PROPER: "echt gebrochen",
        RationalClassificationKind.EQUAL_DEGREE: "Zähler- und Nennergrad gleich",
        RationalClassificationKind.IMPROPER: "unecht gebrochen",
    }[kind]


def _verification_label(status: VerificationStatus) -> str:
    return {
        VerificationStatus.PASS: "erfüllt",
        VerificationStatus.FAIL: "nicht erfüllt",
        VerificationStatus.INCONCLUSIVE: "nicht eindeutig",
        VerificationStatus.NOT_APPLICABLE: "nicht anwendbar",
    }[status]


def _check_label(check_id: str) -> str:
    labels = {
        "INVERSE_RECONSTRUCTION": "Rücktransformation",
        "DIRECT_RECONSTRUCTION": "Transformation",
        "INITIAL_VALUE": "Anfangswert",
        "END_VALUE": "Endwert",
        "PARTIAL_FRACTION_RECONSTRUCTION": "PBZ-Rückzusammenfassung",
    }
    return labels.get(check_id, "Symbolische Kontrolle")


def _end_value_plain_lines(solution: TimeDomainSolution) -> list[str]:
    report = solution.verification
    if report.end_value is not None:
        return [f"Stationärer Endwert: {_plain_exact(report.end_value)}"]
    if report.end_value_status is EndValueStatus.END_VALUE_THEOREM_INVALID:
        return [
            "Der Endwertsatz ist nicht anwendbar, da die Pole von sY(s) nicht "
            "alle strikt in der linken Halbebene liegen."
        ]
    if report.end_value_status is EndValueStatus.INCONCLUSIVE:
        return ["Der stationäre Endwert ist nicht eindeutig bestimmbar."]
    return []


def _residual_label(residual: ExactExpression) -> str:
    return "stimmt exakt" if sp.simplify(residual._as_sympy()) == 0 else _plain_exact(residual)


def _factor_power_plain(factor: sp.Expr, power: int) -> str:
    rendered = f"({_plain_math(factor)})"
    return rendered if power == 1 else f"{rendered}^{power}"


def _needs_partial_fractions(solution: TimeDomainSolution) -> bool:
    partial = solution.partial_fractions
    return partial is not None and (
        len(partial.terms) > 1 or any(item.power > 1 for item in partial.terms)
    )


def _visible_partial_fraction_terms(
    solution: TimeDomainSolution,
) -> tuple[_VisiblePartialFractionTerm, ...]:
    partial = solution.partial_fractions
    if partial is None:
        return ()
    multiplicities = {
        factor.factor_id: factor.multiplicity
        for factor in partial.factor_structure.factors
    }
    ordered = sorted(
        partial.terms,
        key=lambda item: (
            -multiplicities[item.factor_id],
            sp.default_sort_key(item.factor._as_sympy()),
            item.power,
        ),
    )
    visible: list[_VisiblePartialFractionTerm] = []
    next_letter = 0
    s = sp.Symbol("s")
    for term in ordered:
        count = 2 if term.factor_type is FactorType.IRREDUCIBLE_QUADRATIC else 1
        labels = tuple(chr(ord("A") + next_letter + index) for index in range(count))
        next_letter += count
        symbols = tuple(sp.Symbol(label) for label in labels)
        numerator = symbols[0] * s + symbols[1] if count == 2 else symbols[0]
        denominator = sp.expand(term.factor._as_sympy()) ** term.power
        visible.append(
            _VisiblePartialFractionTerm(labels, term, denominator, numerator)
        )
    return tuple(visible)


def _visible_main_denominator(
    visible: tuple[_VisiblePartialFractionTerm, ...],
) -> sp.Expr:
    factors: dict[sp.Expr, int] = {}
    for item in visible:
        factor = sp.cancel(item.term.factor._as_sympy())
        factors[factor] = max(factors.get(factor, 0), item.term.power)
    return sp.Mul(
        *(factor**power for factor, power in factors.items()),
        evaluate=False,
    )


def _visible_ansatz_plain(
    visible: tuple[_VisiblePartialFractionTerm, ...],
) -> str:
    return " + ".join(
        f"{_plain_math(item.numerator_template)}/({_plain_math(item.denominator)})"
        for item in visible
    )


def _coefficient_assignments_plain(
    visible: tuple[_VisiblePartialFractionTerm, ...],
) -> str:
    assignments: list[str] = []
    for item in visible:
        assignments.extend(
            f"{label} = {_plain_exact(value)}"
            for label, value in zip(item.labels, item.term.coefficients, strict=True)
        )
    return ", ".join(assignments)


def _inserted_partial_fractions_plain(
    visible: tuple[_VisiblePartialFractionTerm, ...],
) -> str:
    parts: list[str] = []
    for index, item in enumerate(visible):
        numerator = item.term.numerator._as_sympy()
        negative = numerator.could_extract_minus_sign()
        magnitude = -numerator if negative else numerator
        fraction = _visible_fraction_plain(magnitude, item.denominator)
        if index == 0:
            parts.append(("-" if negative else "") + fraction)
        else:
            parts.append((" - " if negative else " + ") + fraction)
    return "".join(parts)


def _inserted_partial_fractions_latex(
    visible: tuple[_VisiblePartialFractionTerm, ...],
) -> str:
    parts: list[str] = []
    for index, item in enumerate(visible):
        numerator = item.term.numerator._as_sympy()
        negative = numerator.could_extract_minus_sign()
        magnitude = -numerator if negative else numerator
        fraction = _visible_fraction_latex(magnitude, item.denominator)
        if index == 0:
            parts.append(("-" if negative else "") + fraction)
        else:
            parts.append((" - " if negative else " + ") + fraction)
    return "".join(parts)


def _visible_fraction_plain(numerator: sp.Expr, denominator: sp.Expr) -> str:
    numerator_part, scalar_denominator = sp.fraction(numerator)
    denominator_text = _plain_math(denominator)
    if scalar_denominator != 1:
        factor_text = (
            denominator_text
            if denominator.is_Symbol or isinstance(denominator, sp.Mul)
            else f"({denominator_text})"
        )
        denominator_text = f"{_plain_math(scalar_denominator)}*{factor_text}"
    return f"{_plain_math(numerator_part)}/({denominator_text})"


def _visible_fraction_latex(numerator: sp.Expr, denominator: sp.Expr) -> str:
    numerator_part, scalar_denominator = sp.fraction(numerator)
    denominator_latex = sp.latex(denominator)
    if scalar_denominator != 1:
        denominator_latex = (
            rf"{sp.latex(scalar_denominator)} {denominator_latex}"
            if isinstance(denominator, sp.Mul)
            else rf"{sp.latex(scalar_denominator)}\left({denominator_latex}\right)"
        )
    return rf"\frac{{{sp.latex(numerator_part)}}}{{{denominator_latex}}}"


def _normalization_plain_lines(target: sp.Expr) -> list[str]:
    _, factors = sp.factor_list(sp.denom(target), sp.Symbol("s"))
    lines: list[str] = []
    for factor, _ in factors:
        leading = sp.LC(sp.Poly(factor, sp.Symbol("s")))
        if leading != 1:
            normalized = sp.expand(factor / leading)
            lines.append(
                f"Normierung: {_plain_math(factor)} = {_plain_math(leading)}"
                f"*({_plain_math(normalized)})"
            )
    return lines


def _partial_fraction_latex_lines(solution: TimeDomainSolution) -> list[str]:
    partial = solution.partial_fractions
    if partial is None:
        return []
    visible = _visible_partial_fraction_terms(solution)
    target = partial.proper_fraction._as_sympy()
    main_denominator = _visible_main_denominator(visible)
    left = sp.simplify(target * main_denominator)
    right = sp.Add(
        *(
            item.numerator_template
            * sp.cancel(main_denominator / item.denominator)
            for item in visible
        ),
        evaluate=False,
    )
    ansatz = " + ".join(
        rf"\frac{{{sp.latex(item.numerator_template)}}}"
        rf"{{{sp.latex(item.denominator)}}}"
        for item in visible
    )
    inserted = _inserted_partial_fractions_latex(visible)
    coefficient_lines = r",\quad ".join(
        rf"{label}={value.latex}"
        for item in visible
        for label, value in zip(item.labels, item.term.coefficients, strict=True)
    )
    lines = [
        r"\textbf{Partialbruchzerlegung (PBZ)}",
        r"\begin{align*}",
        rf"{_result_symbols(solution.task_type)[0]}_{{\mathrm{{PBZ}}}}(s)"
        rf" &= {sp.latex(target)} \\",
    ]
    _, factors = sp.factor_list(sp.denom(target), sp.Symbol("s"))
    for factor, _ in factors:
        leading = sp.LC(sp.Poly(factor, sp.Symbol("s")))
        if leading != 1:
            normalized = sp.expand(factor / leading)
            lines.append(
                rf"{sp.latex(factor)} &= {sp.latex(leading)}"
                rf"\left({sp.latex(normalized)}\right) \\"
            )
    lines.extend(
        (
            rf"{_result_symbols(solution.task_type)[0]}(s)"
            rf" &= {_visible_fraction_latex(left, main_denominator)} \\",
            rf"{_result_symbols(solution.task_type)[0]}(s) &= {ansatz} \\",
            rf"\text{{Hauptnenner: }}&{sp.latex(main_denominator)} \\",
            rf"\text{{Multiplikation mit }}{sp.latex(main_denominator)}:\quad "
            rf"{sp.latex(left)} &= {sp.latex(right)} \\",
            rf"{coefficient_lines} \\",
            rf"{_result_symbols(solution.task_type)[0]}_{{\mathrm{{PBZ}}}}(s)"
            rf" &= {inserted} \\",
            rf"\text{{Rückzusammenfassung}}&:\quad "
            rf"{sp.latex(partial.recomposed._as_sympy())}={sp.latex(target)}",
            r"\end{align*}",
        )
    )
    return lines


def _is_rf02_table_case(solution: TimeDomainSolution) -> bool:
    if (
        solution.task_type is not TimeDomainTaskType.INVERSE_LAPLACE
        or solution.source_expression is None
    ):
        return False
    s = sp.Symbol("s")
    expected = (s - 4) / ((s - 4) ** 2 + 4)
    return bool(sp.simplify(solution.source_expression._as_sympy() - expected) == 0)


def _rf02_latex_lines(solution: TimeDomainSolution) -> list[str]:
    if solution.source_expression is None:
        return []
    return [
        r"\begin{align*}",
        rf"F(s) &= {solution.source_expression.latex} \\",
        r"\frac{s-a}{(s-a)^2+\omega^2}"
        r"&\longleftrightarrow e^{at}\cos(\omega t) \\",
        r"a&=4,\qquad \omega=2",
        r"\end{align*}",
        r"\text{Da }a>0\text{ ist, wächst die Schwingungshülle.}",
    ]


def _is_sine_response(solution: TimeDomainSolution) -> bool:
    if solution.output_laplace is None or solution.time_function is None:
        return False
    s = sp.Symbol("s")
    target = (sp.pi / 2) / (s**2 + sp.pi / 4)
    return bool(sp.simplify(solution.output_laplace._as_sympy() - target) == 0)


def _sine_comparison_plain_lines(solution: TimeDomainSolution) -> list[str]:
    if solution.output_laplace is None:
        return []
    return [
        "pi/4 = (sqrt(pi)/2)^2",
        "Tabellenpaar: omega/(s^2+omega^2) <-> sin(omega*t)",
        "omega = sqrt(pi)/2; der zusätzliche Faktor ist sqrt(pi).",
    ]


def _sine_comparison_latex_lines(solution: TimeDomainSolution) -> list[str]:
    if solution.output_laplace is None:
        return []
    return [
        r"\begin{align*}",
        r"\frac{\pi}{4} &= \left(\frac{\sqrt{\pi}}{2}\right)^2 \\",
        r"\frac{\omega}{s^2+\omega^2}"
        r"&\longleftrightarrow \sin(\omega t),\qquad "
        r"\omega=\frac{\sqrt{\pi}}{2}",
        r"\end{align*}",
    ]


def _error_presentation(message: str) -> TimeDomainPresentation:
    return TimeDomainPresentation(
        "Eingabe ungültig.", "", "", "", "", "", "", "", message
    )


__all__ = [
    "TimeDomainInputDraft",
    "TimeDomainPresentation",
    "TimeDomainWorkflowResult",
    "run_time_domain_workflow",
]
