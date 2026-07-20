"""Small local-widget workspace for the existing frequency workflow."""

from __future__ import annotations

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFormLayout,
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
    QVBoxLayout,
    QWidget,
)

from klausurbotpro.application import (
    FrequencyDomainInputDraft,
    FrequencyDomainWorkflowMode,
    FrequencyPhasePresentation,
    ParameterInputDraft,
    TransferFunctionInputDraft,
    WorkflowInputForm,
)
from klausurbotpro.ui.frequency_domain_presenter import (
    FrequencyDomainPresenter,
)
from klausurbotpro.ui.frequency_domain_view_state import (
    FrequencyDomainUiRunStatus,
    FrequencyDomainViewState,
)

_SUMMARY_FIELDS = (
    ("workflow_status", "Workflowstatus"),
    ("mode", "Modus"),
    ("reduced_transfer_function", "Reduzierte Übertragungsfunktion"),
    ("substitutions", "Parameterbelegungen"),
    ("frequency_count", "Ausgewertete Frequenzen"),
    ("domain_status", "Fachstatus"),
    ("magnitude_segment_count", "Magnitudensegmente"),
    ("phase_segment_count", "Phasensegmente"),
    ("phase_unwrap", "Phasenentfaltung"),
)
_SINGLE_FIELDS = (
    ("omega", "ω"),
    ("status", "Punktstatus"),
    ("complex_value", "G(jω)"),
    ("real_part", "Realteil"),
    ("imaginary_part", "Imaginärteil"),
    ("magnitude", "Betrag"),
    ("decibel", "dB"),
    ("principal_phase", "Hauptphase"),
)
_TABLE_HEADERS = (
    "Index",
    "Ziel-ω",
    "Auswertungs-ω",
    "Status",
    "Realteil",
    "Imaginärteil",
    "Betrag",
    "dB",
    "Hauptphase",
    "Entfaltete Phase",
)
_FIELD_LABELS = {
    "common_expression_text": "Gemeinsamer Ausdruck",
    "numerator_expression_text": "Zähler",
    "denominator_expression_text": "Nenner",
    "variable_name": "Hauptvariable",
    "parameter_rows": "Parametertabelle",
    "single_angular_frequency": "Kreisfrequenz ω",
    "omega_min": "ω_min",
    "omega_max": "ω_max",
    "points_per_decade": "Punkte pro Dekade",
    "explicit_frequencies": "Explizite Frequenzen",
    "phase_presentation": "Phasendarstellung",
    "field": "Allgemeine Eingabe",
}


class FrequencyDomainWorkspace(QWidget):
    """Collect frequency strings and render presenter-owned display values."""

    def __init__(
        self,
        presenter: FrequencyDomainPresenter,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        if type(presenter) is not FrequencyDomainPresenter:
            raise TypeError("presenter has an invalid type.")
        self.presenter = presenter
        self.setObjectName("frequencyDomainWorkspace")
        self._build_ui()
        self._connect_ui()
        self.render_state(presenter.state)

    def _build_ui(self) -> None:
        self.common_radio = QRadioButton("Gemeinsamer Ausdruck")
        self.common_radio.setObjectName("frequencyCommonInputForm")
        self.separated_radio = QRadioButton("Zähler und Nenner getrennt")
        self.separated_radio.setObjectName("frequencySeparatedInputForm")
        self.common_radio.setChecked(True)
        form_switch = QHBoxLayout()
        form_switch.addWidget(self.common_radio)
        form_switch.addWidget(self.separated_radio)

        self.common_expression_edit = QPlainTextEdit()
        self.common_expression_edit.setObjectName("frequencyCommonExpression")
        self.common_expression_edit.setPlaceholderText("z. B. 1/(s+1)")
        self.common_expression_edit.setMaximumHeight(72)
        common_page = QWidget()
        common_layout = QFormLayout(common_page)
        common_layout.addRow("Übertragungsfunktion:", self.common_expression_edit)

        self.numerator_edit = QPlainTextEdit()
        self.numerator_edit.setObjectName("frequencyNumeratorExpression")
        self.numerator_edit.setMaximumHeight(52)
        self.denominator_edit = QPlainTextEdit()
        self.denominator_edit.setObjectName("frequencyDenominatorExpression")
        self.denominator_edit.setMaximumHeight(52)
        separated_page = QWidget()
        separated_layout = QFormLayout(separated_page)
        separated_layout.addRow("Zähler:", self.numerator_edit)
        separated_layout.addRow("Nenner:", self.denominator_edit)

        self.input_stack = QStackedWidget()
        self.input_stack.addWidget(common_page)
        self.input_stack.addWidget(separated_page)
        self.variable_edit = QLineEdit("s")
        self.variable_edit.setObjectName("frequencyMainVariable")

        self.parameter_table = QTableWidget(0, 3)
        self.parameter_table.setObjectName("frequencyParameterTable")
        self.parameter_table.setHorizontalHeaderLabels(
            ("Parameter", "Zähler", "Nenner")
        )
        self.parameter_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.parameter_table.setMinimumHeight(100)
        self.add_parameter_button = QPushButton("Parameterzeile hinzufügen")
        self.remove_parameter_button = QPushButton("Parameterzeile entfernen")
        parameter_actions = QHBoxLayout()
        parameter_actions.addWidget(self.add_parameter_button)
        parameter_actions.addWidget(self.remove_parameter_button)

        self.mode_combo = QComboBox()
        self.mode_combo.setObjectName("frequencyMode")
        self.mode_combo.addItems(("Einzelpunkt", "Bode"))
        self.single_frequency_edit = QLineEdit("1")
        self.single_frequency_edit.setObjectName("singleAngularFrequency")
        self.omega_min_edit = QLineEdit("1/10")
        self.omega_min_edit.setObjectName("bodeOmegaMin")
        self.omega_max_edit = QLineEdit("10")
        self.omega_max_edit.setObjectName("bodeOmegaMax")
        self.points_per_decade_edit = QLineEdit("4")
        self.points_per_decade_edit.setObjectName("bodePointsPerDecade")
        self.explicit_frequencies_edit = QLineEdit()
        self.explicit_frequencies_edit.setObjectName("bodeExplicitFrequencies")
        self.explicit_frequencies_edit.setPlaceholderText(
            "optional, z. B. 1/2, 1, 2"
        )
        self.phase_combo = QComboBox()
        self.phase_combo.setObjectName("frequencyPhasePresentation")
        self.phase_combo.addItems(
            ("Hauptphase", "Hauptphase und entfaltete Phase")
        )

        frequency_form = QFormLayout()
        frequency_form.addRow("Modus:", self.mode_combo)
        frequency_form.addRow("Kreisfrequenz ω:", self.single_frequency_edit)
        frequency_form.addRow("ω_min:", self.omega_min_edit)
        frequency_form.addRow("ω_max:", self.omega_max_edit)
        frequency_form.addRow(
            "Punkte pro Dekade:",
            self.points_per_decade_edit,
        )
        frequency_form.addRow(
            "Explizite Frequenzen:",
            self.explicit_frequencies_edit,
        )
        frequency_form.addRow("Phasendarstellung:", self.phase_combo)

        self.calculate_button = QPushButton("Frequenzbereich berechnen")
        self.calculate_button.setObjectName("calculateFrequencyDomain")
        self.reset_button = QPushButton("Zurücksetzen")
        input_actions = QHBoxLayout()
        input_actions.addWidget(self.calculate_button)
        input_actions.addWidget(self.reset_button)

        input_group = QGroupBox("Frequenzbereichseingabe")
        input_layout = QVBoxLayout(input_group)
        input_layout.addLayout(form_switch)
        input_layout.addWidget(self.input_stack)
        base_form = QFormLayout()
        base_form.addRow("Hauptvariable:", self.variable_edit)
        input_layout.addLayout(base_form)
        input_layout.addWidget(QLabel("Parameter und exakte Belegungen:"))
        input_layout.addWidget(self.parameter_table)
        input_layout.addLayout(parameter_actions)
        input_layout.addLayout(frequency_form)
        input_layout.addLayout(input_actions)

        self.summary_labels: dict[str, QLabel] = {}
        summary_group = QGroupBox("Ergebnisübersicht")
        summary_layout = QFormLayout(summary_group)
        for name, label in _SUMMARY_FIELDS:
            value = QLabel()
            value.setObjectName(f"frequencySummary_{name}")
            value.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )
            value.setWordWrap(True)
            self.summary_labels[name] = value
            summary_layout.addRow(f"{label}:", value)

        self.single_labels: dict[str, QLabel] = {}
        self.single_group = QGroupBox("Einzelpunkt")
        single_layout = QFormLayout(self.single_group)
        for name, label in _SINGLE_FIELDS:
            value = QLabel()
            value.setObjectName(f"singlePoint_{name}")
            value.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )
            self.single_labels[name] = value
            single_layout.addRow(f"{label}:", value)

        self.value_table = QTableWidget(0, len(_TABLE_HEADERS))
        self.value_table.setObjectName("frequencyValueTable")
        self.value_table.setHorizontalHeaderLabels(_TABLE_HEADERS)
        self.value_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.value_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.value_table.setSortingEnabled(False)
        self.value_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Interactive
        )
        self.value_table.horizontalHeader().setStretchLastSection(True)
        self.value_table.setMinimumHeight(220)

        self.diagnostic_table = QTableWidget(0, 3)
        self.diagnostic_table.setObjectName("frequencyDiagnostics")
        self.diagnostic_table.setHorizontalHeaderLabels(
            ("Severity", "Meldung", "Feld")
        )
        self.diagnostic_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.diagnostic_table.horizontalHeader().setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        self.diagnostic_table.horizontalHeader().setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.Stretch,
        )
        self.diagnostic_table.horizontalHeader().setSectionResizeMode(
            2,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        diagnostics_group = QGroupBox("Diagnosen")
        diagnostics_layout = QVBoxLayout(diagnostics_group)
        diagnostics_layout.addWidget(self.diagnostic_table)

        result_widget = QWidget()
        result_layout = QVBoxLayout(result_widget)
        result_layout.addWidget(summary_group)
        result_layout.addWidget(self.single_group)
        result_layout.addWidget(self.value_table, 1)
        result_layout.addWidget(diagnostics_group)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.addWidget(input_group)
        self.splitter.addWidget(result_widget)
        self.splitter.setSizes((380, 720))
        self.status_label = QLabel("Bereit.")
        self.status_label.setObjectName("frequencyWorkspaceStatus")
        self.status_label.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.addWidget(self.splitter, 1)
        layout.addWidget(self.status_label)

    def _connect_ui(self) -> None:
        self.common_radio.toggled.connect(self._switch_input_form)
        self.mode_combo.currentIndexChanged.connect(self._mode_changed)
        self.add_parameter_button.clicked.connect(self.add_parameter_row)
        self.remove_parameter_button.clicked.connect(
            self.remove_selected_parameter_row
        )
        self.calculate_button.clicked.connect(self.calculate)
        self.reset_button.clicked.connect(self.reset_workspace)
        self.presenter.state_changed.connect(self.render_state)
        self._shortcuts = (
            QShortcut(QKeySequence("Ctrl+Return"), self),
            QShortcut(QKeySequence("Ctrl+Enter"), self),
        )
        for shortcut in self._shortcuts:
            shortcut.activated.connect(self.calculate)

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

    def input_draft(self) -> FrequencyDomainInputDraft:
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
        preparation = TransferFunctionInputDraft(
            form,
            self.common_expression_edit.toPlainText(),
            self.numerator_edit.toPlainText(),
            self.denominator_edit.toPlainText(),
            self.variable_edit.text(),
            rows,
            "frequency",
        )
        mode = (
            FrequencyDomainWorkflowMode.SINGLE_POINT
            if self.mode_combo.currentIndex() == 0
            else FrequencyDomainWorkflowMode.BODE
        )
        phase = (
            FrequencyPhasePresentation.PRINCIPAL_ONLY
            if self.phase_combo.currentIndex() == 0
            else FrequencyPhasePresentation.PRINCIPAL_AND_UNWRAPPED
        )
        return FrequencyDomainInputDraft(
            preparation,
            mode,
            self.single_frequency_edit.text(),
            self.omega_min_edit.text(),
            self.omega_max_edit.text(),
            self.points_per_decade_edit.text(),
            self.explicit_frequencies_edit.text(),
            phase,
        )

    def _cell_text(self, row: int, column: int) -> str:
        item = self.parameter_table.item(row, column)
        return "" if item is None else item.text()

    @Slot()
    def calculate(self) -> None:
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
        self.mode_combo.setCurrentIndex(0)
        self.single_frequency_edit.setText("1")
        self.omega_min_edit.setText("1/10")
        self.omega_max_edit.setText("10")
        self.points_per_decade_edit.setText("4")
        self.explicit_frequencies_edit.clear()
        self.phase_combo.setCurrentIndex(0)

    @Slot(object)
    def render_state(self, value: object) -> None:
        if type(value) is not FrequencyDomainViewState:
            raise TypeError("value must be FrequencyDomainViewState.")
        running = value.run_status is FrequencyDomainUiRunStatus.RUNNING
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
            self.mode_combo,
            self.calculate_button,
            self.reset_button,
        ):
            widget.setEnabled(not running)
        self.status_label.setText(value.general_message)
        self._update_mode_fields(running)
        for name, _label in _SUMMARY_FIELDS:
            self.summary_labels[name].setText(getattr(value.summary, name))
        for name, _label in _SINGLE_FIELDS:
            self.single_labels[name].setText(getattr(value.single_point, name))
        self.single_group.setVisible(bool(value.single_point.status))
        self._render_rows(value)
        self._render_diagnostics(value)
        self._focus_field(value.focused_field)

    def _render_rows(self, state: FrequencyDomainViewState) -> None:
        self.value_table.setUpdatesEnabled(False)
        self.value_table.setRowCount(len(state.rows))
        for row_index, row in enumerate(state.rows):
            for column, name in enumerate(row.__dataclass_fields__):
                self.value_table.setItem(
                    row_index,
                    column,
                    QTableWidgetItem(getattr(row, name)),
                )
        self.value_table.setUpdatesEnabled(True)

    def _render_diagnostics(self, state: FrequencyDomainViewState) -> None:
        rows = tuple(
            (
                diagnostic.severity.upper(),
                diagnostic.message,
                diagnostic.field,
            )
            for diagnostic in state.diagnostics
        ) + tuple(
            (
                "ERROR",
                error.message,
                _FIELD_LABELS.get(error.field, error.field),
            )
            for error in state.request_errors
        )
        self.diagnostic_table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column, text in enumerate(row):
                self.diagnostic_table.setItem(
                    row_index,
                    column,
                    QTableWidgetItem(text),
                )

    def _focus_field(self, field: str | None) -> None:
        targets = {
            "common_expression_text": self.common_expression_edit,
            "numerator_expression_text": self.numerator_edit,
            "denominator_expression_text": self.denominator_edit,
            "variable_name": self.variable_edit,
            "parameter_rows": self.parameter_table,
            "single_angular_frequency": self.single_frequency_edit,
            "omega_min": self.omega_min_edit,
            "omega_max": self.omega_max_edit,
            "points_per_decade": self.points_per_decade_edit,
            "explicit_frequencies": self.explicit_frequencies_edit,
            "phase_presentation": self.phase_combo,
        }
        if field is not None and field in targets:
            targets[field].setFocus()

    @Slot(bool)
    def _switch_input_form(self, common_checked: bool) -> None:
        self.input_stack.setCurrentIndex(0 if common_checked else 1)

    @Slot(int)
    def _mode_changed(self, _index: int) -> None:
        if self.mode_combo.currentIndex() == 0:
            self.phase_combo.setCurrentIndex(0)
        self._update_mode_fields(
            self.presenter.state.run_status is FrequencyDomainUiRunStatus.RUNNING
        )

    def _update_mode_fields(self, running: bool) -> None:
        single = self.mode_combo.currentIndex() == 0
        self.single_frequency_edit.setEnabled(not running and single)
        for widget in (
            self.omega_min_edit,
            self.omega_max_edit,
            self.points_per_decade_edit,
            self.explicit_frequencies_edit,
            self.phase_combo,
        ):
            widget.setEnabled(not running and not single)


__all__ = ["FrequencyDomainWorkspace"]
