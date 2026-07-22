"""The first usable transfer-function desktop workspace."""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Slot
from PySide6.QtGui import QFontDatabase, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QSplitter,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QToolButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from klausurbotpro.application import (
    ConditionLine,
    EquationLine,
    OverrideLine,
    ParameterInputDraft,
    ResultLine,
    SolutionSection,
    SolutionSectionKind,
    SolutionSectionStatus,
    TransferFunctionInputDraft,
    WarningLine,
    WorkflowInputForm,
    WorkflowStage,
    prepend_latex_task_heading,
)
from klausurbotpro.ui.transfer_function_presenter import (
    TransferFunctionPresenter,
)
from klausurbotpro.ui.transfer_function_view_state import (
    TransferFunctionReportView,
    TransferFunctionUiRunStatus,
    TransferFunctionViewState,
)

_STAGE_LABELS = {
    WorkflowStage.PARSE: "Parse",
    WorkflowStage.RAW_TRANSFER_FUNCTION: "Raw-Transferfunktion",
    WorkflowStage.REDUCTION: "Reduktion",
    WorkflowStage.ROOT_ANALYSIS: "Wurzelanalyse",
    WorkflowStage.STABILITY_ANALYSIS: "Stabilitätsanalyse",
}
_STATUS_LABELS = {
    "not_evaluated": "Nicht ausgewertet",
    "succeeded": "Erfolgreich",
    "failed": "Fehlgeschlagen",
    "blocked": "Nicht berechnet (vorherige Stufe fehlgeschlagen)",
}
_SEVERITY_LABELS = {
    "info": "ℹ INFO",
    "warning": "⚠ WARNUNG",
    "error": "✖ FEHLER",
}
_SEVERITY_RANK = {"info": 1, "warning": 2, "error": 3}
_SECTION_STATUS_LABELS = {
    SolutionSectionStatus.COMPLETE: "vollständig",
    SolutionSectionStatus.PARTIAL: "teilweise verfügbar",
    SolutionSectionStatus.FAILED: "fehlgeschlagen",
    SolutionSectionStatus.BLOCKED: (
        "nicht berechnet, da eine vorherige Stufe fehlgeschlagen ist"
    ),
    SolutionSectionStatus.NOT_APPLICABLE: "keine",
}
_REAL_PART_RELATIONS = {
    "negative": "< 0",
    "zero": "= 0",
    "positive": "> 0",
}
_FIELD_LABELS = {
    "common_expression_text": "Gemeinsamer Ausdruck",
    "numerator_expression_text": "Zähler",
    "denominator_expression_text": "Nenner",
    "variable_name": "Hauptvariable",
    "parameter_rows": "Parametertabelle",
    "field": "Allgemeine Eingabe",
}


class TransferFunctionWorkspace(QWidget):
    """Collect raw UI values and render presenter-owned structured state."""

    def __init__(
        self,
        presenter: TransferFunctionPresenter,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        if type(presenter) is not TransferFunctionPresenter:
            raise TypeError("presenter has an invalid type.")
        self.presenter = presenter
        self._latex_task_title = ""
        self.setObjectName("transferFunctionWorkspace")
        self._configure_base_font()
        self._build_ui()
        self._connect_ui()
        self._set_tab_order()
        self.render_state(presenter.state)

    def _build_ui(self) -> None:
        line_height = self.fontMetrics().lineSpacing()
        self.common_radio = QRadioButton("Gemeinsamer Ausdruck")
        self.common_radio.setObjectName("commonInputForm")
        self.separated_radio = QRadioButton("Zähler und Nenner getrennt")
        self.separated_radio.setObjectName("separatedInputForm")
        self.common_radio.setChecked(True)
        form_switch = QHBoxLayout()
        form_switch.addWidget(self.common_radio)
        form_switch.addWidget(self.separated_radio)

        self.common_expression_edit = QPlainTextEdit()
        self.common_expression_edit.setObjectName("commonExpression")
        self.common_expression_edit.setPlaceholderText("z. B. 1/(s+1)")
        self.common_expression_edit.setMaximumHeight(90)
        common_page = QWidget()
        common_layout = QFormLayout(common_page)
        common_layout.addRow("Übertragungsfunktion:", self.common_expression_edit)

        self.numerator_edit = QPlainTextEdit()
        self.numerator_edit.setObjectName("numeratorExpression")
        self.numerator_edit.setMaximumHeight(65)
        self.denominator_edit = QPlainTextEdit()
        self.denominator_edit.setObjectName("denominatorExpression")
        self.denominator_edit.setMaximumHeight(65)
        separated_page = QWidget()
        separated_layout = QFormLayout(separated_page)
        separated_layout.addRow("Zähler:", self.numerator_edit)
        separated_layout.addRow("Nenner:", self.denominator_edit)

        self.input_stack = QStackedWidget()
        self.input_stack.addWidget(common_page)
        self.input_stack.addWidget(separated_page)
        self.variable_edit = QLineEdit("s")
        self.variable_edit.setObjectName("mainVariable")
        self.task_title_edit = QLineEdit()
        self.task_title_edit.setObjectName("transferFunctionTaskTitle")
        self.task_title_edit.setPlaceholderText(
            "z. B. Aufgabe 1a – Regelungsnormalform"
        )

        self.parameter_table = QTableWidget(0, 3)
        self.parameter_table.setObjectName("parameterTable")
        self.parameter_table.setHorizontalHeaderLabels(
            ("Parameter", "Zähler", "Nenner")
        )
        self.parameter_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.parameter_table.setMinimumHeight(120)
        self.parameter_table.verticalHeader().setDefaultSectionSize(
            round(line_height * 1.8)
        )
        self.parameter_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.add_parameter_button = QPushButton("Zeile hinzufügen")
        self.add_parameter_button.setObjectName("addParameterRow")
        self.remove_parameter_button = QPushButton("Ausgewählte Zeile entfernen")
        self.remove_parameter_button.setObjectName("removeParameterRow")
        parameter_actions = QHBoxLayout()
        parameter_actions.addWidget(self.add_parameter_button)
        parameter_actions.addWidget(self.remove_parameter_button)

        self.calculate_button = QPushButton("Berechnen")
        self.calculate_button.setObjectName("calculateTransferFunction")
        self.calculate_button.setDefault(True)
        self.reset_button = QPushButton("Zurücksetzen")
        self.reset_button.setObjectName("resetTransferFunction")
        input_actions = QHBoxLayout()
        input_actions.addWidget(self.calculate_button)
        input_actions.addWidget(self.reset_button)

        input_group = QGroupBox("Eingabe")
        input_layout = QVBoxLayout(input_group)
        input_layout.addLayout(form_switch)
        input_layout.addWidget(self.input_stack)
        variable_layout = QFormLayout()
        variable_layout.addRow(
            "Aufgabenname / LaTeX-Überschrift:", self.task_title_edit
        )
        variable_layout.addRow("Hauptvariable:", self.variable_edit)
        input_layout.addLayout(variable_layout)
        input_layout.addWidget(QLabel("Parameter und exakte Belegungen:"))
        input_layout.addWidget(self.parameter_table)
        input_layout.addLayout(parameter_actions)
        input_layout.addLayout(input_actions)

        self.stage_tree = QTreeWidget()
        self.stage_tree.setObjectName("workflowStages")
        self.stage_tree.setHeaderLabels(("Stufe", "Status", "Severity", "Meldung"))
        self.stage_tree.setRootIsDecorated(False)
        self.stage_tree.setMinimumHeight(round(line_height * 9))
        stage_header = self.stage_tree.header()
        stage_header.setMinimumSectionSize(
            self.fontMetrics().horizontalAdvance("WARNUNG") + line_height
        )
        stage_header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        stage_header.setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        stage_header.setSectionResizeMode(
            2,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        stage_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        for stage in WorkflowStage:
            item = QTreeWidgetItem(
                self.stage_tree,
                (_STAGE_LABELS[stage], "Nicht ausgewertet", "—", ""),
            )
            item.setSizeHint(0, QSize(0, round(line_height * 1.8)))

        self.summary_edits: dict[SolutionSectionKind, QPlainTextEdit] = {}
        summary_widget = QWidget()
        summary_layout = QGridLayout(summary_widget)
        for index, (kind, label) in enumerate((
            (SolutionSectionKind.TRANSFER_FUNCTION, "Übertragungsfunktion:"),
            (SolutionSectionKind.ZEROS, "Nullstellen:"),
            (SolutionSectionKind.POLES, "Pole:"),
            (SolutionSectionKind.STABILITY, "Stabilität:"),
            (SolutionSectionKind.PREREQUISITES, "Voraussetzungen:"),
            (SolutionSectionKind.DOMAIN_EXCLUSIONS, "Definitionsausschlüsse:"),
        )):
            edit = QPlainTextEdit()
            edit.setObjectName(f"summary_{kind.value}")
            edit.setReadOnly(True)
            edit.setMinimumHeight(round(line_height * 4.5))
            self.summary_edits[kind] = edit
            summary_layout.addWidget(QLabel(label), index // 2 * 2, index % 2)
            summary_layout.addWidget(edit, index // 2 * 2 + 1, index % 2)
            summary_layout.setColumnStretch(index % 2, 1)
        result_group = QGroupBox("Ergebnis")
        result_layout = QVBoxLayout(result_group)
        result_layout.addWidget(self.stage_tree)
        result_layout.addWidget(summary_widget, 1)

        self.top_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.top_splitter.addWidget(input_group)
        self.top_splitter.addWidget(result_group)
        self.top_splitter.setSizes((410, 690))

        fixed_font = QFontDatabase.systemFont(
            QFontDatabase.SystemFont.FixedFont
        )
        if fixed_font.pointSizeF() > 0:
            fixed_font.setPointSizeF(
                max(fixed_font.pointSizeF(), self.font().pointSizeF())
            )
        self.plaintext_report_edit = QPlainTextEdit()
        self.plaintext_report_edit.setObjectName("plaintextReport")
        self.plaintext_report_edit.setReadOnly(True)
        self.plaintext_report_edit.setFont(fixed_font)
        self.latex_report_edit = QPlainTextEdit()
        self.latex_report_edit.setObjectName("latexReport")
        self.latex_report_edit.setReadOnly(True)
        self.latex_report_edit.setFont(fixed_font)
        self.report_tabs = QTabWidget()
        self.report_tabs.setObjectName("reportTabs")
        self.report_tabs.addTab(self.plaintext_report_edit, "Plaintext")
        latex_index = self.report_tabs.addTab(
            self.latex_report_edit,
            "LaTeX-Quelltext",
        )
        self.report_tabs.setTabToolTip(
            latex_index,
            "Quelltext zum Kopieren in ein LaTeX-Dokument; keine Vorschau.",
        )
        self.copy_button = QPushButton("Aktiven Bericht kopieren")
        self.copy_button.setObjectName("copyActiveReport")
        report_group = QGroupBox("Papierübertragbarer Bericht")
        report_layout = QVBoxLayout(report_group)
        report_layout.addWidget(self.report_tabs)
        report_layout.addWidget(self.copy_button)

        self.main_splitter = QSplitter(Qt.Orientation.Vertical)
        self.main_splitter.addWidget(self.top_splitter)
        self.main_splitter.addWidget(report_group)
        self.main_splitter.setSizes((500, 280))

        self.status_label = QLabel()
        self.status_label.setObjectName("workspaceStatus")
        self.status_label.setWordWrap(True)
        self.details_toggle = QToolButton()
        self.details_toggle.setText("Technische Details")
        self.details_toggle.setCheckable(True)
        self.details_edit = QPlainTextEdit()
        self.details_edit.setObjectName("technicalDetails")
        self.details_edit.setReadOnly(True)
        self.details_edit.setVisible(False)
        self.details_edit.setMaximumHeight(100)
        status_layout = QHBoxLayout()
        status_layout.addWidget(self.status_label, 1)
        status_layout.addWidget(self.details_toggle)

        layout = QVBoxLayout(self)
        layout.addWidget(self.main_splitter, 1)
        layout.addLayout(status_layout)
        layout.addWidget(self.details_edit)

    def _connect_ui(self) -> None:
        self.common_radio.toggled.connect(self._switch_input_form)
        self.add_parameter_button.clicked.connect(self.add_parameter_row)
        self.remove_parameter_button.clicked.connect(
            self.remove_selected_parameter_row
        )
        self.calculate_button.clicked.connect(self.calculate)
        self.reset_button.clicked.connect(self.reset_workspace)
        self.report_tabs.currentChanged.connect(self._report_tab_changed)
        self.copy_button.clicked.connect(self.copy_active_report)
        self.details_toggle.toggled.connect(self.details_edit.setVisible)
        self.presenter.state_changed.connect(self.render_state)
        self._shortcuts = (
            QShortcut(QKeySequence("Ctrl+Return"), self),
            QShortcut(QKeySequence("Ctrl+Enter"), self),
            QShortcut(QKeySequence("Ctrl+R"), self),
            QShortcut(QKeySequence("Ctrl+Shift+C"), self),
            QShortcut(QKeySequence("Alt+P"), self),
            QShortcut(QKeySequence("Alt+L"), self),
        )
        self._shortcuts[0].activated.connect(self.calculate)
        self._shortcuts[1].activated.connect(self.calculate)
        self._shortcuts[2].activated.connect(self.reset_workspace)
        self._shortcuts[3].activated.connect(self.copy_active_report)
        self._shortcuts[4].activated.connect(
            lambda: self.report_tabs.setCurrentIndex(0)
        )
        self._shortcuts[5].activated.connect(
            lambda: self.report_tabs.setCurrentIndex(1)
        )

    def _set_tab_order(self) -> None:
        chain = (
            self.common_radio,
            self.separated_radio,
            self.common_expression_edit,
            self.numerator_edit,
            self.denominator_edit,
            self.variable_edit,
            self.parameter_table,
            self.add_parameter_button,
            self.remove_parameter_button,
            self.calculate_button,
            self.reset_button,
            self.stage_tree,
            self.report_tabs,
            self.copy_button,
        )
        for first, second in zip(chain, chain[1:], strict=False):
            QWidget.setTabOrder(first, second)

    @Slot()
    def add_parameter_row(self) -> None:
        row = self.parameter_table.rowCount()
        self.parameter_table.insertRow(row)
        for column in range(3):
            self.parameter_table.setItem(row, column, QTableWidgetItem(""))
        self.parameter_table.setCurrentCell(row, 0)

    @Slot()
    def remove_selected_parameter_row(self) -> None:
        row = self.parameter_table.currentRow()
        if row >= 0:
            self.parameter_table.removeRow(row)

    def input_draft(self) -> TransferFunctionInputDraft:
        """Read simple raw UI values without interpreting mathematics."""

        rows = tuple(
            ParameterInputDraft(
                self._cell_text(row, 0),
                self._cell_text(row, 1),
                self._cell_text(row, 2),
            )
            for row in range(self.parameter_table.rowCount())
        )
        form = (
            WorkflowInputForm.COMMON
            if self.common_radio.isChecked()
            else WorkflowInputForm.SEPARATED
        )
        return TransferFunctionInputDraft(
            form,
            self.common_expression_edit.toPlainText(),
            self.numerator_edit.toPlainText(),
            self.denominator_edit.toPlainText(),
            self.variable_edit.text(),
            rows,
            "transfer_function",
        )

    def _cell_text(self, row: int, column: int) -> str:
        item = self.parameter_table.item(row, column)
        return "" if item is None else item.text()

    @Slot()
    def calculate(self) -> None:
        self._latex_task_title = self.task_title_edit.text()
        self.presenter.submit(self.input_draft())

    @Slot()
    def reset_workspace(self) -> None:
        if not self.presenter.reset():
            return
        self.common_radio.setChecked(True)
        self.common_expression_edit.clear()
        self.numerator_edit.clear()
        self.denominator_edit.clear()
        self.variable_edit.setText("s")
        self.parameter_table.setRowCount(0)
        self.task_title_edit.clear()
        self._latex_task_title = ""

    @Slot(int)
    def _report_tab_changed(self, index: int) -> None:
        self.presenter.select_report_view(
            TransferFunctionReportView.PLAINTEXT
            if index == 0
            else TransferFunctionReportView.LATEX
        )

    @Slot()
    def copy_active_report(self) -> None:
        text = (
            self.plaintext_report_edit.toPlainText()
            if self.report_tabs.currentIndex() == 0
            else self.latex_report_edit.toPlainText()
        )
        if not text:
            return
        clipboard = QApplication.clipboard()
        assert clipboard is not None
        clipboard.setText(text)
        self.presenter.report_copied()

    @Slot(object)
    def render_state(self, value: object) -> None:
        if type(value) is not TransferFunctionViewState:
            raise TypeError("value must be a TransferFunctionViewState.")
        running = value.run_status is TransferFunctionUiRunStatus.RUNNING
        for widget in (
            self.common_radio,
            self.separated_radio,
            self.common_expression_edit,
            self.numerator_edit,
            self.denominator_edit,
            self.variable_edit,
            self.parameter_table,
            self.add_parameter_button,
            self.remove_parameter_button,
            self.calculate_button,
            self.reset_button,
        ):
            widget.setEnabled(not running)
        self.copy_button.setEnabled(
            not running and bool(self.presenter.active_report_text())
        )
        self.status_label.setText(value.general_message)
        self.plaintext_report_edit.setPlainText(value.plaintext_report)
        self.latex_report_edit.setPlainText(
            prepend_latex_task_heading(value.latex_report, self._latex_task_title)
        )
        expected_index = (
            0
            if value.active_report_view is TransferFunctionReportView.PLAINTEXT
            else 1
        )
        if self.report_tabs.currentIndex() != expected_index:
            self.report_tabs.setCurrentIndex(expected_index)
        self._render_stages(value)
        self._render_summary(value)
        self._render_details(value)
        self._focus_field(value.focused_field)

    def _render_stages(self, state: TransferFunctionViewState) -> None:
        workflow = state.workflow_state
        for index, _stage in enumerate(WorkflowStage):
            item = self.stage_tree.topLevelItem(index)
            assert item is not None
            if state.run_status is TransferFunctionUiRunStatus.RUNNING:
                item.setText(1, "Berechnung läuft")
                item.setText(2, "—")
                item.setText(3, "")
                continue
            if workflow is None:
                item.setText(1, "Nicht ausgewertet")
                item.setText(2, "—")
                item.setText(3, "")
                continue
            record = workflow.stage_records[index]
            primary_diagnostic = max(
                record.diagnostics,
                key=lambda diagnostic: _SEVERITY_RANK[
                    diagnostic.severity.value
                ],
                default=None,
            )
            item.setText(1, _STATUS_LABELS[record.status.value])
            item.setText(
                2,
                (
                    "—"
                    if primary_diagnostic is None
                    else _SEVERITY_LABELS[
                        primary_diagnostic.severity.value
                    ]
                ),
            )
            item.setText(
                3,
                (
                    ""
                    if primary_diagnostic is None
                    else primary_diagnostic.message
                ),
            )

    def _render_summary(self, state: TransferFunctionViewState) -> None:
        for kind, edit in self.summary_edits.items():
            if state.solution_report is None:
                edit.clear()
                continue
            section = state.solution_report.section(kind)
            if kind is SolutionSectionKind.STABILITY:
                real_parts = state.solution_report.section(
                    SolutionSectionKind.POLE_REAL_PARTS
                )
                edit.setPlainText(_stability_summary(real_parts, section))
            else:
                edit.setPlainText(_section_summary(section))

    def _render_details(self, state: TransferFunctionViewState) -> None:
        lines = [
            f"{_FIELD_LABELS[error.field]}"
            + (
                ""
                if error.row_index is None
                else f"[Zeile {error.row_index + 1}]"
            )
            + f": {error.message}"
            for error in state.request_errors
        ]
        if state.workflow_state is not None:
            lines.extend(
                f"{_STAGE_LABELS[entry.stage]}: "
                f"{entry.diagnostic.message}"
                for entry in state.workflow_state.aggregated_diagnostics
            )
        self.details_edit.setPlainText("\n".join(lines))
        self.details_toggle.setEnabled(bool(lines))
        if not lines:
            self.details_toggle.setChecked(False)

    def _focus_field(self, field: str | None) -> None:
        targets = {
            "common_expression_text": self.common_expression_edit,
            "numerator_expression_text": self.numerator_edit,
            "denominator_expression_text": self.denominator_edit,
            "variable_name": self.variable_edit,
            "parameter_rows": self.parameter_table,
        }
        target: QWidget | None = None if field is None else targets.get(field)
        if target is not None:
            target.setFocus()

    @Slot(bool)
    def _switch_input_form(self, common_checked: bool) -> None:
        self.input_stack.setCurrentIndex(0 if common_checked else 1)

    def _configure_base_font(self) -> None:
        font = self.font()
        if font.pointSizeF() > 0:
            font.setPointSizeF(font.pointSizeF() + 1.25)
        self.setFont(font)


def _section_summary(section: SolutionSection | None) -> str:
    if section is None:
        return ""
    if not section.lines:
        return _SECTION_STATUS_LABELS[section.status]
    return "\n".join(
        _summary_line(line, section.kind) for line in section.lines
    )


def _summary_line(line: object, section_kind: SolutionSectionKind) -> str:
    if type(line) is EquationLine:
        equation = (
            f"{line.left.plaintext} {line.relation} {line.right.plaintext}"
        )
        if line.identifier == "root_equation":
            label = (
                "Nullstellenbedingung"
                if section_kind is SolutionSectionKind.ZEROS
                else "Polgleichung"
            )
            return f"{label}: {equation}"
        return equation
    if type(line) is ResultLine:
        if line.label == "Stabilitätsaussage":
            return f"⇒ {line.exact_value.plaintext}"
        if (
            line.label == "Ergebnis"
            and section_kind is SolutionSectionKind.ZEROS
        ):
            return f"⇒ {line.exact_value.plaintext}"
        return (
            f"{_summary_result_label(line.label)} = "
            f"{line.exact_value.plaintext}"
        )
    if type(line) is ConditionLine:
        values = ", ".join(value.plaintext for value in line.expressions)
        if line.relation == "NOT_ALL_ZERO":
            return f"Nicht alle gleichzeitig null: {values}"
        return f"{values} {line.relation}"
    if type(line) is WarningLine:
        return f"{_SEVERITY_LABELS[line.severity.value]} {line.statement}"
    if type(line) is OverrideLine:
        return f"[Manuelle Vorgabe] {line.reason}"
    return "Strukturiertes Ergebnis im Bericht verfügbar."


def _stability_summary(
    real_parts: SolutionSection | None,
    stability: SolutionSection | None,
) -> str:
    lines: list[str] = []
    if real_parts is not None and real_parts.lines:
        for line in real_parts.lines:
            if type(line) is not ResultLine:
                continue
            relation = (
                None
                if line.source_role is None
                else _REAL_PART_RELATIONS.get(line.source_role)
            )
            rendered = (
                f"{line.label} = {line.exact_value.plaintext}"
            )
            lines.append(
                rendered if relation is None else f"{rendered} {relation}"
            )
    if stability is None:
        return "\n".join(lines)
    if not stability.lines:
        lines.append(_SECTION_STATUS_LABELS[stability.status])
    else:
        conclusions = [
            _summary_line(line, SolutionSectionKind.STABILITY)
            for line in stability.lines
            if type(line) is ResultLine
        ]
        lines.extend(conclusions)
    return "\n".join(lines)


def _summary_result_label(label: str) -> str:
    for prefix, replacement in (
        ("s_excluded,", "Ausgeschlossene Stelle s_"),
        ("s_cancelled,", "Gekürzte Stelle s_"),
    ):
        if label.startswith(prefix) and label[len(prefix) :].isdigit():
            return f"{replacement}{label[len(prefix):]}"
    return label


__all__ = ["TransferFunctionWorkspace"]
