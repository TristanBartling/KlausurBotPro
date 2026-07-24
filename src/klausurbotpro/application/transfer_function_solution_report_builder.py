"""Build deterministic paper-oriented reports from validated workflow states."""

from __future__ import annotations

from collections.abc import Iterable

from klausurbotpro.application._solution_report_formatting import (
    descriptive_math,
    exact_expression,
    exact_rational,
    exact_root,
    fraction,
    identifier,
    literal_text,
    numerical_root_expression,
    transfer_pair,
)
from klausurbotpro.application._workflow_validation import (
    validate_workflow_state,
)
from klausurbotpro.application.transfer_function_solution_report_contracts import (
    ApproximationLine,
    ConditionLine,
    EquationLine,
    OverrideLine,
    ReportDiagnostic,
    ReportDiagnosticCode,
    ReportMathExpression,
    ResultLine,
    SolutionLine,
    SolutionReportLimits,
    SolutionReportStatus,
    SolutionSection,
    SolutionSectionKind,
    SolutionSectionStatus,
    SourceReferenceLine,
    TransferFunctionSolutionReport,
    TransformationLine,
    WarningLine,
)
from klausurbotpro.application.transfer_function_workflow_contracts import (
    TransferFunctionWorkflowLimits,
    TransferFunctionWorkflowState,
    WorkflowInputForm,
    WorkflowStage,
    WorkflowStageRecord,
    WorkflowStageStatus,
    WorkflowValueOrigin,
)
from klausurbotpro.domain import (
    DiagnosticSeverity,
    ExactExpression,
    PolynomialRootAnalysis,
    PolynomialRootStatus,
    RealPartSign,
    RootAnalysisGroup,
    StabilityReasonCode,
    StabilityStatus,
    TransferFunctionDomainExclusion,
    TransferFunctionPrerequisite,
    TransferFunctionPrerequisiteKind,
    TransferFunctionStabilityAnalysisResult,
)

_RESOURCE_ERRORS = (MemoryError, RecursionError, OverflowError)
_DEFAULT_SOLUTION_REPORT_LIMITS = SolutionReportLimits()
_DEFAULT_WORKFLOW_LIMITS = TransferFunctionWorkflowLimits()


class TransferFunctionSolutionReportBuilder:
    """Translate one existing workflow state without running its mathematics."""

    def __init__(
        self,
        limits: SolutionReportLimits = _DEFAULT_SOLUTION_REPORT_LIMITS,
        *,
        workflow_limits: TransferFunctionWorkflowLimits = _DEFAULT_WORKFLOW_LIMITS,
    ) -> None:
        if type(limits) is not SolutionReportLimits:
            raise TypeError("limits must be a SolutionReportLimits value.")
        if type(workflow_limits) is not TransferFunctionWorkflowLimits:
            raise TypeError(
                "workflow_limits must be a TransferFunctionWorkflowLimits value."
            )
        self._limits = limits
        self._workflow_limits = workflow_limits

    def build(
        self,
        state: TransferFunctionWorkflowState,
    ) -> TransferFunctionSolutionReport:
        """Build a deterministic report from existing structured results."""

        if type(state) is not TransferFunctionWorkflowState:
            raise TypeError("state must be a TransferFunctionWorkflowState.")
        errors = validate_workflow_state(
            state,
            self._workflow_limits,
        )
        if errors:
            return self._apply_limits(self._invalid_state_report(errors))

        try:
            sections = self._build_sections(state)
        except _RESOURCE_ERRORS:
            diagnostic = ReportDiagnostic(
                ReportDiagnosticCode.REPORT_LIMIT_EXCEEDED,
                DiagnosticSeverity.ERROR,
                "Die Berichtserzeugung überschritt verfügbare Ressourcen.",
                details=(("limit", "runtime_resource"),),
            )
            return self._apply_limits(
                self._failed_report(
                    diagnostic,
                    "Die Berichtserzeugung konnte nicht abgeschlossen werden.",
                )
            )
        status = _overall_status(state)
        return self._apply_limits(
            TransferFunctionSolutionReport(status, sections)
        )

    def _build_sections(
        self,
        state: TransferFunctionWorkflowState,
    ) -> tuple[SolutionSection, ...]:
        raw = state.raw_value
        reduced = state.reduced_value
        root = state.root_analysis_result
        stability = state.stability_analysis_result

        given_lines = self._given_lines(state)
        transfer_lines: list[SolutionLine] = []
        active = reduced if reduced is not None else raw
        if active is not None:
            pair = transfer_pair(
                active.numerator.expression,
                active.denominator.expression,
            )
            transfer_lines.append(
                EquationLine(
                    identifier(f"G({state.request.variable_name})"),
                    "=",
                    fraction(pair),
                    "active_transfer_function",
                )
            )
        raw_override = _active_override(state, WorkflowStage.RAW_TRANSFER_FUNCTION)
        if raw_override is not None:
            transfer_lines.append(raw_override)

        pair_lines: list[SolutionLine] = []
        if raw is not None:
            pair_lines.extend(
                (
                    EquationLine(
                        identifier(f"Z_raw({state.request.variable_name})"),
                        "=",
                        exact_expression(raw.numerator.expression),
                        "raw_numerator",
                    ),
                    EquationLine(
                        identifier(f"N_raw({state.request.variable_name})"),
                        "=",
                        exact_expression(raw.denominator.expression),
                        "raw_denominator",
                    ),
                )
            )
        if reduced is not None:
            pair_lines.extend(
                (
                    EquationLine(
                        identifier(f"Z_red({state.request.variable_name})"),
                        "=",
                        exact_expression(reduced.numerator.expression),
                        "reduced_numerator",
                    ),
                    EquationLine(
                        identifier(f"N_red({state.request.variable_name})"),
                        "=",
                        exact_expression(reduced.denominator.expression),
                        "reduced_denominator",
                    ),
                )
            )

        reduction_lines = self._reduction_lines(state)
        prerequisite_lines = (
            self._prerequisite_lines(active.prerequisites)
            if active is not None
            else ()
        )
        exclusion_lines: tuple[SolutionLine, ...] = (
            self._domain_exclusion_lines(active.domain_exclusions)
            if active is not None
            else ()
        )
        if root is not None and root.succeeded:
            exclusion_lines = (
                *exclusion_lines,
                *self._excluded_location_lines(
                    root.retained_domain_exclusions,
                    state.request.variable_name,
                ),
            )

        substitution_lines = self._substitution_lines(state)
        zero_lines = (
            self._root_lines(
                root.reduced_zeros,
                state.request.variable_name,
                "Z",
                "z",
            )
            if root is not None and root.reduced_zeros is not None
            else ()
        )
        root_override = _active_override(state, WorkflowStage.ROOT_ANALYSIS)
        if root_override is not None:
            zero_lines = (root_override, *zero_lines)
        pole_lines = (
            self._root_lines(
                root.reduced_poles,
                state.request.variable_name,
                "N",
                "p",
                source_expression_override=(
                    raw.denominator.expression
                    if raw is not None
                    and state.reduction_result is not None
                    and state.reduction_result.report is not None
                    and any(
                        step.kind.value == "remove_common_numeric_factor"
                        for step in state.reduction_result.report.steps
                    )
                    else None
                ),
            )
            if root is not None and root.reduced_poles is not None
            else ()
        )
        if root_override is not None:
            pole_lines = (root_override, *pole_lines)
        real_part_lines = (
            self._real_part_lines(stability)
            if stability is not None and stability.succeeded
            else ()
        )
        stability_lines = (
            self._stability_lines(stability)
            if stability is not None and stability.succeeded
            else ()
        )
        dynamics_lines = (
            self._dynamics_lines(state, stability)
            if stability is not None and stability.succeeded
            else ()
        )
        source_lines = (
            tuple(
                SourceReferenceLine(
                    reference.document_name,
                    reference.page,
                    reference.location,
                    reference.claim,
                )
                for reference in stability.source_references
            )
            if stability is not None and stability.succeeded
            else ()
        )
        notice_lines = tuple(
            WarningLine(
                entry.diagnostic.code.value,
                entry.diagnostic.severity,
                entry.stage,
                entry.diagnostic.message,
            )
            for entry in state.aggregated_diagnostics
        )

        records = {record.stage: record for record in state.stage_records}
        active_stage = (
            WorkflowStage.REDUCTION
            if reduced is not None
            else WorkflowStage.RAW_TRANSFER_FUNCTION
        )
        active_record = records[active_stage]
        reduction_section = _section(
            SolutionSectionKind.REDUCTION,
            records[WorkflowStage.REDUCTION],
            reduction_lines,
            WorkflowStage.REDUCTION,
        )
        if (
            records[WorkflowStage.REDUCTION].value_origin
            is WorkflowValueOrigin.OVERRIDDEN
        ):
            reduction_section = SolutionSection(
                SolutionSectionKind.REDUCTION,
                SolutionSectionStatus.PARTIAL,
                tuple(reduction_lines),
                WorkflowStage.REDUCTION,
            )
        return (
            _section(
                SolutionSectionKind.GIVEN,
                records[WorkflowStage.PARSE],
                given_lines,
                WorkflowStage.PARSE,
            ),
            _section(
                SolutionSectionKind.TRANSFER_FUNCTION,
                records[WorkflowStage.RAW_TRANSFER_FUNCTION],
                transfer_lines,
                WorkflowStage.RAW_TRANSFER_FUNCTION,
            ),
            _section(
                SolutionSectionKind.NUMERATOR_DENOMINATOR,
                records[WorkflowStage.RAW_TRANSFER_FUNCTION],
                pair_lines,
                WorkflowStage.RAW_TRANSFER_FUNCTION,
            ),
            _section(
                SolutionSectionKind.ZEROS,
                records[WorkflowStage.ROOT_ANALYSIS],
                zero_lines,
                WorkflowStage.ROOT_ANALYSIS,
            ),
            _section(
                SolutionSectionKind.POLES,
                records[WorkflowStage.ROOT_ANALYSIS],
                pole_lines,
                WorkflowStage.ROOT_ANALYSIS,
            ),
            _section(
                SolutionSectionKind.POLE_REAL_PARTS,
                records[WorkflowStage.STABILITY_ANALYSIS],
                real_part_lines,
                WorkflowStage.STABILITY_ANALYSIS,
            ),
            _section(
                SolutionSectionKind.STABILITY,
                records[WorkflowStage.STABILITY_ANALYSIS],
                stability_lines,
                WorkflowStage.STABILITY_ANALYSIS,
            ),
            _section(
                SolutionSectionKind.DYNAMIC_BEHAVIOR,
                records[WorkflowStage.STABILITY_ANALYSIS],
                dynamics_lines,
                WorkflowStage.STABILITY_ANALYSIS,
            ),
            reduction_section,
            _section(
                SolutionSectionKind.DOMAIN_EXCLUSIONS,
                active_record,
                exclusion_lines,
                active_stage,
            ),
            _section(
                SolutionSectionKind.PREREQUISITES,
                active_record,
                prerequisite_lines,
                active_stage,
            ),
            _optional_section(
                SolutionSectionKind.PARAMETER_SUBSTITUTIONS,
                substitution_lines,
                WorkflowStage.ROOT_ANALYSIS,
            ),
            _section(
                SolutionSectionKind.SOURCES,
                records[WorkflowStage.STABILITY_ANALYSIS],
                source_lines,
                WorkflowStage.STABILITY_ANALYSIS,
            ),
            _optional_section(
                SolutionSectionKind.WORKFLOW_NOTICES,
                notice_lines,
                None,
            ),
        )

    def _given_lines(
        self,
        state: TransferFunctionWorkflowState,
    ) -> tuple[SolutionLine, ...]:
        request = state.request
        lines: list[SolutionLine] = [
            ResultLine(
                "Eingabeform",
                descriptive_math(
                    "Gemeinsamer Ausdruck"
                    if request.input_form is WorkflowInputForm.COMMON
                    else "Getrennte Zähler-/Nennereingabe"
                ),
                source_role="input_form",
            ),
            ResultLine(
                "Hauptvariable",
                identifier(request.variable_name),
                source_role="variable",
            ),
            ResultLine(
                "Erlaubte Parameter",
                descriptive_math(
                    ", ".join(request.allowed_parameter_names) or "keine"
                ),
                source_role="allowed_parameters",
            ),
        ]
        if request.input_form is WorkflowInputForm.COMMON:
            assert request.common_expression_text is not None
            lines.append(
                ResultLine(
                    "Originaleingabe",
                    literal_text(request.common_expression_text),
                    source_role="original_input",
                )
            )
        else:
            assert request.numerator_expression_text is not None
            assert request.denominator_expression_text is not None
            lines.extend(
                (
                    ResultLine(
                        "Originalzähler",
                        literal_text(request.numerator_expression_text),
                        source_role="original_numerator",
                    ),
                    ResultLine(
                        "Originalnenner",
                        literal_text(request.denominator_expression_text),
                        source_role="original_denominator",
                    ),
                )
            )
        substitutions = state.substitutions
        if substitutions is not None:
            lines.extend(
                EquationLine(
                    identifier(assignment.parameter_name),
                    "=",
                    exact_rational(assignment.value),
                    "active_parameter_substitution",
                )
                for assignment in substitutions.assignments
            )
        return tuple(lines)

    def _reduction_lines(
        self,
        state: TransferFunctionWorkflowState,
    ) -> tuple[SolutionLine, ...]:
        override = _active_override(state, WorkflowStage.REDUCTION)
        if override is not None:
            return (override,)
        result = state.reduction_result
        if result is None or result.report is None:
            return ()
        exclusions = (
            self._domain_exclusion_lines(result.raw.domain_exclusions)
        )
        lines: list[SolutionLine] = []
        for step in result.report.steps:
            lines.append(
                TransformationLine(
                    transfer_pair(
                        step.numerator_before,
                        step.denominator_before,
                    ),
                    step.kind.value,
                    (
                        None
                        if step.factor is None
                        else exact_expression(step.factor)
                    ),
                    transfer_pair(
                        step.numerator_after,
                        step.denominator_after,
                    ),
                    self._prerequisite_lines(step.prerequisites_used),
                    exclusions,
                )
            )
        root_result = state.root_analysis_result
        if root_result is not None and root_result.succeeded:
            lines.extend(
                self._cancelled_location_lines(
                    root_result.cancelled_locations,
                    state.request.variable_name,
                )
            )
        return tuple(lines)

    @staticmethod
    def _prerequisite_lines(
        prerequisites: Iterable[TransferFunctionPrerequisite],
    ) -> tuple[ConditionLine, ...]:
        lines: list[ConditionLine] = []
        for prerequisite in prerequisites:
            expressions = tuple(
                exact_expression(expression)
                for expression in prerequisite.expressions
            )
            relation = (
                "NOT_ALL_ZERO"
                if prerequisite.kind
                is TransferFunctionPrerequisiteKind.NOT_ALL_ZERO
                else "!= 0"
            )
            lines.append(
                ConditionLine(
                    prerequisite.kind.value,
                    expressions,
                    relation,
                )
            )
        return tuple(lines)

    @staticmethod
    def _domain_exclusion_lines(
        exclusions: Iterable[TransferFunctionDomainExclusion],
    ) -> tuple[ConditionLine, ...]:
        return tuple(
            ConditionLine(
                "domain_exclusion",
                (exact_expression(exclusion.polynomial.expression),),
                "!= 0",
            )
            for exclusion in exclusions
        )

    @staticmethod
    def _excluded_location_lines(
        group: RootAnalysisGroup,
        variable_name: str,
    ) -> tuple[ResultLine, ...]:
        lines: list[ResultLine] = []
        for analysis in group.analyses:
            for root in analysis.roots:
                lines.append(
                    ResultLine(
                        f"s_excluded,{len(lines) + 1}",
                        exact_root(root.value, variable_name),
                        multiplicity=root.multiplicity,
                        source_role="retained_domain_exclusion",
                    )
                )
        return tuple(lines)

    @staticmethod
    def _cancelled_location_lines(
        group: RootAnalysisGroup,
        variable_name: str = "s",
    ) -> tuple[ResultLine, ...]:
        lines: list[ResultLine] = []
        for analysis in group.analyses:
            for root in analysis.roots:
                lines.append(
                    ResultLine(
                        f"s_cancelled,{len(lines) + 1}",
                        exact_root(root.value, variable_name),
                        multiplicity=root.multiplicity,
                        source_role="cancelled_location",
                    )
                )
        return tuple(lines)

    @staticmethod
    def _substitution_lines(
        state: TransferFunctionWorkflowState,
    ) -> tuple[SolutionLine, ...]:
        reduced = state.reduced_value
        used = () if reduced is None else tuple(sorted(reduced.used_parameter_names))
        substitutions = state.substitutions
        assignments = () if substitutions is None else substitutions.assignments
        lines: list[SolutionLine] = [
            EquationLine(
                identifier(assignment.parameter_name),
                "=",
                exact_rational(assignment.value),
                "parameter_substitution",
            )
            for assignment in assignments
        ]
        root_result = state.root_analysis_result
        specialized_numerator = (
            None
            if root_result is None or root_result.reduced_zeros is None
            else root_result.reduced_zeros.source_expression
        )
        specialized_denominator = (
            None
            if root_result is None or root_result.reduced_poles is None
            else root_result.reduced_poles.source_expression
        )
        if (
            assignments
            and specialized_numerator is not None
            and specialized_denominator is not None
        ):
            variable = identifier(state.request.variable_name)
            assignment_plain = ", ".join(
                (
                    f"{assignment.parameter_name}="
                    f"{exact_rational(assignment.value).plaintext}"
                )
                for assignment in assignments
            )
            assignment_latex = r",\,".join(
                (
                    f"{identifier(assignment.parameter_name).latex}="
                    f"{exact_rational(assignment.value).latex}"
                )
                for assignment in assignments
            )
            raw_value = fraction(
                transfer_pair(
                    specialized_numerator,
                    specialized_denominator,
                )
            )
            evaluated_plain = raw_value.plaintext
            evaluated_latex = raw_value.latex
            lines.append(
                EquationLine(
                    descriptive_math(
                        f"G({variable.plaintext})|{assignment_plain}",
                        rf"\left.G({variable.latex})\right|_{{"
                        rf"{assignment_latex}}}",
                    ),
                    "=",
                    descriptive_math(
                        evaluated_plain,
                        evaluated_latex,
                    ),
                    "evaluated_parameter_substitution",
                )
            )
        assigned = {assignment.parameter_name for assignment in assignments}
        missing = tuple(name for name in used if name not in assigned)
        if missing:
            lines.append(
                ConditionLine(
                    "missing_parameter_assignment",
                    tuple(identifier(name) for name in missing),
                    "not assigned",
                )
            )
        return tuple(lines)

    @staticmethod
    def _root_lines(
        analysis: PolynomialRootAnalysis,
        variable_name: str,
        polynomial_label: str,
        root_label: str,
        *,
        source_expression_override: ExactExpression | None = None,
    ) -> tuple[SolutionLine, ...]:
        source_expression = (
            analysis.source_expression
            if source_expression_override is None
            else source_expression_override
        )
        lines: list[SolutionLine] = [
            EquationLine(
                identifier(f"{polynomial_label}({variable_name})"),
                "=",
                exact_expression(source_expression),
                "specialized_polynomial",
            ),
            EquationLine(
                identifier(f"{polynomial_label}({variable_name})"),
                "=",
                descriptive_math("0", "0"),
                "root_equation",
            )
        ]
        if analysis.status is PolynomialRootStatus.COMPLETE:
            estimates = {
                estimate.root_index: estimate
                for estimate in analysis.numerical_estimates
            }
            approximation_lines: list[ApproximationLine] = []
            for root in analysis.roots:
                estimate = estimates.get(root.index)
                exact_value = exact_root(root.value, variable_name)
                lines.append(
                    ResultLine(
                        f"{root_label}_{root.index + 1}",
                        exact_value,
                        multiplicity=root.multiplicity,
                        source_role=root.source.value,
                    )
                )
                if estimate is not None:
                    approximation = numerical_root_expression(
                        estimate.real,
                        estimate.imaginary,
                    )
                    if approximation.plaintext != exact_value.plaintext:
                        approximation_lines.append(
                            ApproximationLine(
                                f"{root_label}_{root.index + 1}",
                                approximation,
                            )
                        )
            lines.extend(approximation_lines)
        elif analysis.status is PolynomialRootStatus.CONSTANT_NONZERO:
            lines.append(
                ResultLine(
                    "Ergebnis",
                    descriptive_math(
                        "keine Nullstellen"
                        if root_label == "z"
                        else "keine Pole"
                    ),
                    source_role=analysis.source.value,
                )
            )
        elif analysis.status is PolynomialRootStatus.ZERO_POLYNOMIAL:
            lines.append(
                ResultLine(
                    "Ergebnis",
                    descriptive_math(
                        "Nullpolynom: keine endliche Einzelliste"
                    ),
                    source_role=analysis.source.value,
                )
            )
        elif analysis.status is PolynomialRootStatus.SYMBOLIC_UNDETERMINED:
            lines.append(
                ResultLine(
                    "Ergebnis",
                    descriptive_math("nicht eindeutig bestimmbar"),
                    source_role=analysis.source.value,
                )
            )
        else:
            lines.append(
                WarningLine(
                    ReportDiagnosticCode.REPORT_MISSING_STAGE_RESULT.value,
                    DiagnosticSeverity.WARNING,
                    WorkflowStage.ROOT_ANALYSIS,
                    "Die Wurzelanalyse wurde nicht ausgewertet.",
                )
            )
        return tuple(lines)

    @staticmethod
    def _dynamics_lines(
        state: TransferFunctionWorkflowState,
        stability: TransferFunctionStabilityAnalysisResult,
    ) -> tuple[SolutionLine, ...]:
        interpretation = stability.pole_dynamics
        model_basis = (
            "Reduzierte E/A-Übertragungsfunktion"
            if interpretation.is_available
            else "Sicher nicht klassifiziert"
        )
        lines: list[SolutionLine] = [
            ResultLine(
                "Aussage",
                descriptive_math(interpretation.statement),
                source_role=interpretation.classification.value,
            ),
            ResultLine(
                "Begründung",
                descriptive_math(interpretation.reason),
                source_role="qualitative_reason",
            ),
            ResultLine(
                "Modellbasis",
                descriptive_math(model_basis),
                source_role=interpretation.model_basis.value,
            ),
        ]
        if (
            state.reduction_result is not None
            and state.reduction_result.report is not None
            and any(
                step.kind.value != "no_reduction"
                for step in state.reduction_result.report.steps
            )
        ):
            lines.append(
                ResultLine(
                    "Hinweis",
                    descriptive_math(
                        "Die qualitative Aussage bezieht sich auf die "
                        "reduzierte E/A-Übertragungsfunktion; entfernte "
                        "Faktoren bleiben im Kürzungsprotokoll dokumentiert."
                    ),
                    source_role="reduced_model_notice",
                )
            )
        return tuple(lines)

    @staticmethod
    def _real_part_lines(
        stability: TransferFunctionStabilityAnalysisResult,
    ) -> tuple[SolutionLine, ...]:
        lines: list[SolutionLine] = []
        for contribution in stability.pole_contributions:
            value = (
                descriptive_math("nicht exakt bestimmbar")
                if contribution.exact_real_part is None
                else exact_expression(contribution.exact_real_part)
            )
            lines.append(
                ResultLine(
                    f"Re(p_{contribution.pole.index + 1})",
                    value,
                    multiplicity=contribution.multiplicity,
                    source_role=contribution.real_part_sign.value,
                )
            )
        if (
            not lines
            and stability.status is StabilityStatus.SYMBOLIC_UNDETERMINED
        ):
            lines.append(
                ResultLine(
                    "Polrealteile",
                    descriptive_math("nicht exakt bestimmbar"),
                    source_role=RealPartSign.UNDETERMINED.value,
                )
            )
        elif not lines:
            lines.append(
                ResultLine(
                    "Polrealteile",
                    descriptive_math("keine reduzierten Pole"),
                    source_role="no_poles",
                )
            )
        return tuple(lines)

    @staticmethod
    def _stability_lines(
        stability: TransferFunctionStabilityAnalysisResult,
    ) -> tuple[SolutionLine, ...]:
        status = stability.status
        assert status is not None
        lines: list[SolutionLine] = []
        if status is StabilityStatus.STABLE:
            lines.append(
                    ConditionLine(
                        "all_pole_real_parts",
                        (
                            descriptive_math(
                                "für alle i: Re(p_i)",
                                r"\forall i:\operatorname{Re}(p_i)",
                            ),
                        ),
                    "< 0",
                )
            )
            conclusion = "Das System ist E/A-asymptotisch stabil."
        elif status is StabilityStatus.BORDERLINE_STABLE:
            lines.extend(
                (
                    ConditionLine(
                        "no_right_half_plane_pole",
                        (
                            descriptive_math(
                                "für alle i: Re(p_i)",
                                r"\forall i:\operatorname{Re}(p_i)",
                            ),
                        ),
                        "<= 0",
                    ),
                    ConditionLine(
                        "simple_imaginary_axis_pole",
                        (
                            descriptive_math(
                                "es gibt ein i: Re(p_i)",
                                r"\exists i:\operatorname{Re}(p_i)",
                            ),
                        ),
                        "= 0, multiplicity = 1",
                    ),
                )
            )
            conclusion = "System ist grenzstabil, aber nicht E/A-stabil."
        elif status is StabilityStatus.UNSTABLE:
            reasons = {
                contribution.reason.code
                for contribution in stability.pole_contributions
            }
            if StabilityReasonCode.RIGHT_HALF_PLANE_POLE in reasons:
                lines.append(
                    ConditionLine(
                        "right_half_plane_pole_exists",
                        (
                            descriptive_math(
                                "es gibt ein i: Re(p_i)",
                                r"\exists i:\operatorname{Re}(p_i)",
                            ),
                        ),
                        "> 0",
                    )
                )
            if StabilityReasonCode.REPEATED_IMAGINARY_AXIS_POLE in reasons:
                lines.append(
                    ConditionLine(
                        "repeated_imaginary_axis_pole_exists",
                        (
                            descriptive_math(
                                "Re(s_i)",
                                r"\mathrm{Re}(s_i)",
                            ),
                        ),
                        "= 0, multiplicity > 1",
                    )
                )
            conclusion = "System ist instabil."
        else:
            lines.append(
                ConditionLine(
                    "undetermined_pole_real_parts",
                    (
                        descriptive_math(
                            "Re(p_i)",
                            r"\operatorname{Re}(p_i)",
                        ),
                    ),
                    "not fully decidable",
                )
            )
            conclusion = "Stabilität nicht eindeutig bestimmbar."
        lines.append(
            ResultLine(
                "Stabilitätsaussage",
                descriptive_math(conclusion),
                source_role=status.value,
            )
        )
        return tuple(lines)

    def _invalid_state_report(
        self,
        errors: tuple[tuple[str, str], ...],
    ) -> TransferFunctionSolutionReport:
        diagnostic = ReportDiagnostic(
            ReportDiagnosticCode.REPORT_INVALID_WORKFLOW_STATE,
            DiagnosticSeverity.ERROR,
            "Der Workflow-State ist inkonsistent oder manipuliert.",
            SolutionSectionKind.WORKFLOW_NOTICES,
            errors,
        )
        return self._failed_report(
            diagnostic,
            "Ungültiger Workflow-State; mathematische Werte wurden verworfen.",
        )

    @staticmethod
    def _failed_report(
        diagnostic: ReportDiagnostic,
        statement: str,
    ) -> TransferFunctionSolutionReport:
        section = SolutionSection(
            SolutionSectionKind.WORKFLOW_NOTICES,
            SolutionSectionStatus.FAILED,
            (
                WarningLine(
                    diagnostic.code.value,
                    diagnostic.severity,
                    None,
                    statement,
                ),
            ),
        )
        return TransferFunctionSolutionReport(
            SolutionReportStatus.FAILED,
            (section,),
            (diagnostic,),
        )

    def _apply_limits(
        self,
        report: TransferFunctionSolutionReport,
    ) -> TransferFunctionSolutionReport:
        overflow = _find_limit_overflow(report.sections, self._limits)
        if overflow is None:
            return report
        index, limit_name = overflow
        accepted = list(report.sections[:index])
        while accepted and (
            len(accepted) + 1 > self._limits.max_sections
            or sum(len(section.lines) for section in accepted) + 1
            > self._limits.max_total_lines
        ):
            accepted.pop()
        diagnostic = ReportDiagnostic(
            ReportDiagnosticCode.REPORT_LIMIT_EXCEEDED,
            DiagnosticSeverity.ERROR,
            "Der Lösungsbericht überschreitet ein konfiguriertes Limit.",
            (
                report.sections[index].kind
                if index < len(report.sections)
                else None
            ),
            (("limit", limit_name),),
        )
        notice = SolutionSection(
            SolutionSectionKind.WORKFLOW_NOTICES,
            SolutionSectionStatus.FAILED,
            (
                WarningLine(
                    diagnostic.code.value,
                    diagnostic.severity,
                    None,
                    "Berichtslimit überschritten; der betroffene Abschnitt "
                    "wurde nicht teilweise ausgegeben.",
                ),
            ),
        )
        if (
            accepted
            and accepted[-1].kind is SolutionSectionKind.WORKFLOW_NOTICES
        ):
            accepted.pop()
        accepted.append(notice)
        has_mathematics = any(
            section.kind
            not in (
                SolutionSectionKind.GIVEN,
                SolutionSectionKind.WORKFLOW_NOTICES,
            )
            and section.lines
            for section in accepted
        )
        diagnostics = (*report.diagnostics, diagnostic)
        return TransferFunctionSolutionReport(
            (
                SolutionReportStatus.PARTIAL
                if has_mathematics
                else SolutionReportStatus.FAILED
            ),
            tuple(accepted),
            diagnostics,
        )


def _active_override(
    state: TransferFunctionWorkflowState,
    stage: WorkflowStage,
) -> OverrideLine | None:
    record = next(record for record in state.stage_records if record.stage is stage)
    provenance = record.override_provenance
    if (
        record.value_origin is not WorkflowValueOrigin.OVERRIDDEN
        or provenance is None
    ):
        return None
    return OverrideLine(
        stage,
        provenance.origin_kind,
        provenance.reason,
    )


def _section(
    kind: SolutionSectionKind,
    record: WorkflowStageRecord,
    lines: Iterable[SolutionLine],
    stage: WorkflowStage,
) -> SolutionSection:
    line_tuple = tuple(lines)
    if record.status is WorkflowStageStatus.SUCCEEDED:
        status = (
            SolutionSectionStatus.COMPLETE
            if line_tuple
            else SolutionSectionStatus.NOT_APPLICABLE
        )
    elif record.status is WorkflowStageStatus.FAILED:
        line_tuple = (
            *line_tuple,
            WarningLine(
                ReportDiagnosticCode.REPORT_MISSING_STAGE_RESULT.value,
                DiagnosticSeverity.ERROR,
                stage,
                "Die Workflow-Stufe ist fehlgeschlagen.",
            ),
        )
        status = (
            SolutionSectionStatus.PARTIAL
            if len(line_tuple) > 1
            else SolutionSectionStatus.FAILED
        )
    elif record.status is WorkflowStageStatus.BLOCKED:
        status = SolutionSectionStatus.BLOCKED
        line_tuple = ()
    else:
        status = SolutionSectionStatus.NOT_APPLICABLE
        line_tuple = ()
    return SolutionSection(kind, status, line_tuple, stage)


def _optional_section(
    kind: SolutionSectionKind,
    lines: Iterable[SolutionLine],
    stage: WorkflowStage | None,
) -> SolutionSection:
    line_tuple = tuple(lines)
    return SolutionSection(
        kind,
        (
            SolutionSectionStatus.COMPLETE
            if line_tuple
            else SolutionSectionStatus.NOT_APPLICABLE
        ),
        line_tuple,
        stage,
    )


def _overall_status(
    state: TransferFunctionWorkflowState,
) -> SolutionReportStatus:
    statuses = tuple(record.status for record in state.stage_records)
    if all(status is WorkflowStageStatus.SUCCEEDED for status in statuses):
        return SolutionReportStatus.COMPLETE
    if statuses[0] is WorkflowStageStatus.FAILED:
        return SolutionReportStatus.FAILED
    return SolutionReportStatus.PARTIAL


def _find_limit_overflow(
    sections: tuple[SolutionSection, ...],
    limits: SolutionReportLimits,
) -> tuple[int, str] | None:
    total_lines = 0
    reduction_steps = 0
    roots = 0
    conditions = 0
    sources = 0
    warnings = 0
    for index, section in enumerate(sections):
        if index + 1 > limits.max_sections:
            return index, "max_sections"
        if len(section.lines) > limits.max_lines_per_section:
            return index, "max_lines_per_section"
        total_lines += len(section.lines)
        if total_lines > limits.max_total_lines:
            return index, "max_total_lines"
        for line in section.lines:
            if any(
                len(expression.plaintext) > limits.max_expression_length
                or len(expression.latex) > limits.max_expression_length
                for expression in _line_expressions(line)
            ):
                return index, "max_expression_length"
            reduction_steps += type(line) is TransformationLine
            conditions += type(line) is ConditionLine
            if type(line) is TransformationLine:
                conditions += len(line.retained_prerequisites)
                conditions += len(line.retained_domain_exclusions)
            sources += type(line) is SourceReferenceLine
            warnings += type(line) is WarningLine
            if type(line) is ResultLine:
                roots += line.source_role in {
                    "numerator",
                    "denominator",
                    "retained_domain_exclusion",
                    "cancelled_location",
                }
        if reduction_steps > limits.max_reduction_steps:
            return index, "max_reduction_steps"
        if roots > limits.max_roots:
            return index, "max_roots"
        if conditions > limits.max_conditions:
            return index, "max_conditions"
        if sources > limits.max_source_references:
            return index, "max_source_references"
        if warnings > limits.max_warning_lines:
            return index, "max_warning_lines"
    return None


def _line_expressions(line: SolutionLine) -> tuple[ReportMathExpression, ...]:
    if type(line) is EquationLine:
        return line.left, line.right
    if type(line) is ResultLine:
        return (line.exact_value,)
    if type(line) is ApproximationLine:
        return (line.value,)
    if type(line) is ConditionLine:
        return line.expressions
    if type(line) is TransformationLine:
        values = (
            line.before.numerator,
            line.before.denominator,
            line.after.numerator,
            line.after.denominator,
        )
        direct = (
            values
            if line.factor_or_operation is None
            else (*values, line.factor_or_operation)
        )
        retained = tuple(
            expression
            for condition in (
                *line.retained_prerequisites,
                *line.retained_domain_exclusions,
            )
            for expression in condition.expressions
        )
        return (*direct, *retained)
    return ()


__all__ = ["TransferFunctionSolutionReportBuilder"]
