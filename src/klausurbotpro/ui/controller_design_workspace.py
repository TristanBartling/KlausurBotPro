"""Controller-design top-level workspace."""

from __future__ import annotations

from PySide6.QtCore import Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from klausurbotpro.application import (
    ControllerDesignInputDraft,
    ControllerDesignMethod,
    ControllerType,
    ParameterInputDraft,
    controller_design_candidate_status_text,
    controller_design_method_text,
)
from klausurbotpro.ui.controller_design_presenter import ControllerDesignPresenter
from klausurbotpro.ui.controller_design_view_state import (
    ControllerDesignUiRunStatus,
    ControllerDesignViewState,
)

_METHODS = (
    ("P-Verstärkung für gewünschte Phasenreserve", ControllerDesignMethod.P_PHASE_MARGIN),
    ("Ziegler–Nichols – offener Kreis", ControllerDesignMethod.ZIEGLER_NICHOLS_OPEN_LOOP),
    ("Ziegler–Nichols – geschlossener Kreis", ControllerDesignMethod.ZIEGLER_NICHOLS_CLOSED_LOOP),
    ("Cohen–Coon", ControllerDesignMethod.COHEN_COON),
)


class ControllerDesignWorkspace(QWidget):
    def __init__(self, presenter: ControllerDesignPresenter) -> None:
        super().__init__()
        self.presenter = presenter
        self.setObjectName("controllerDesignWorkspace")
        self.task_name_edit = _line("", "controllerDesignTaskName")
        self.method_combo = _combo("controllerDesignMethod")
        for label, method in _METHODS:
            self.method_combo.addItem(label, method)
        self.controller_type_combo = _combo("controllerDesignType")
        for label, value in (
            ("P", ControllerType.P),
            ("PI", ControllerType.PI),
            ("PID", ControllerType.PID),
        ):
            self.controller_type_combo.addItem(label, value)
        self.controller_type_combo.setCurrentIndex(2)
        self.numerator_edit = _line("100", "controllerDesignNumerator")
        self.denominator_edit = _line("s*(10*s+1)", "controllerDesignDenominator")
        self.parameters_edit = _line("", "controllerDesignParameters")
        self.target_margin_edit = _line("20", "controllerDesignTargetMargin")
        self.omega_min_edit = _line("1e-4", "controllerDesignOmegaMin")
        self.omega_max_edit = _line("1e2", "controllerDesignOmegaMax")
        self.points_per_decade_edit = _line("32", "controllerDesignPointsPerDecade")
        self.process_gain_edit = _line("1.8", "controllerDesignProcessGain")
        self.dead_time_edit = _line("12", "controllerDesignDeadTime")
        self.lag_time_edit = _line("72", "controllerDesignLagTime")
        self.critical_gain_edit = _line("1.62", "controllerDesignCriticalGain")
        self.critical_period_edit = _line("3", "controllerDesignCriticalPeriod")
        self.preview_label = QLabel()
        self.preview_label.setObjectName("controllerDesignPreview")
        form = QFormLayout()
        form.addRow("Aufgabenname / LaTeX-Überschrift:", self.task_name_edit)
        form.addRow("Verfahren:", self.method_combo)
        form.addRow("Reglertyp:", self.controller_type_combo)
        self.rows: dict[str, tuple[QLabel, QWidget]] = {}
        for key, label, widget in (
            ("numerator", "Zähler:", self.numerator_edit),
            ("denominator", "Nenner:", self.denominator_edit),
            ("parameters", "Parameterbelegungen:", self.parameters_edit),
            ("margin", "Zielphasenreserve [deg]:", self.target_margin_edit),
            ("omega_min", "ω_min [rad/s]:", self.omega_min_edit),
            ("omega_max", "ω_max [rad/s]:", self.omega_max_edit),
            ("points", "Punkte pro Dekade:", self.points_per_decade_edit),
            ("process_gain", "K_S:", self.process_gain_edit),
            ("dead_time", "L [s]:", self.dead_time_edit),
            ("lag_time", "T [s]:", self.lag_time_edit),
            ("critical_gain", "K_crit:", self.critical_gain_edit),
            ("critical_period", "T_crit [s]:", self.critical_period_edit),
        ):
            label_widget = QLabel(label)
            form.addRow(label_widget, widget)
            self.rows[key] = (label_widget, widget)
        form.addRow("Vorschau:", self.preview_label)
        self.calculate_button = _button("Reglerauslegung berechnen", "controllerDesignCalculate")
        self.reset_button = _button("Zurücksetzen", "controllerDesignReset")
        self.copy_button = _button("LaTeX kopieren", "controllerDesignCopyLatex")
        self.copy_button.setEnabled(False)
        buttons = QHBoxLayout()
        for button in (self.calculate_button, self.reset_button, self.copy_button):
            buttons.addWidget(button)
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.addLayout(form)
        left_layout.addLayout(buttons)
        left_layout.addStretch(1)
        self.result_tabs = QTabWidget()
        self.result_tabs.setObjectName("controllerDesignResultTabs")
        self.outputs: dict[str, QPlainTextEdit] = {}
        for key, label in (
            ("overview", "Übersicht"),
            ("inputs", "Verfahren und Eingaben"),
            ("formula", "Tabellenformel / Zielphasensuche"),
            ("parameters", "Reglerparameter"),
            ("frequency", "Frequenznachprüfung"),
            ("controls", "Kontrollen"),
            ("steps", "Worked Steps"),
            ("latex", "LaTeX-Lösung"),
            ("diagnostics", "Diagnosen"),
        ):
            output = QPlainTextEdit()
            output.setReadOnly(True)
            output.setObjectName(f"controllerDesign{key.title()}Output")
            self.outputs[key] = output
            self.result_tabs.addTab(output, label)
        self.latex_output = self.outputs["latex"]
        splitter = QSplitter()
        splitter.addWidget(left)
        splitter.addWidget(self.result_tabs)
        splitter.setSizes((390, 810))
        layout = QVBoxLayout(self)
        layout.addWidget(splitter)
        self.method_combo.currentIndexChanged.connect(self._method_changed)
        self.calculate_button.clicked.connect(self._calculate)
        self.reset_button.clicked.connect(self._reset)
        self.copy_button.clicked.connect(self._copy)
        presenter.state_changed.connect(self._render)
        self._method_changed()

    @Slot()
    def _method_changed(self) -> None:
        method = ControllerDesignMethod(self.method_combo.currentData())
        phase = method is ControllerDesignMethod.P_PHASE_MARGIN
        closed = method is ControllerDesignMethod.ZIEGLER_NICHOLS_CLOSED_LOOP
        table_open = method in (
            ControllerDesignMethod.ZIEGLER_NICHOLS_OPEN_LOOP,
            ControllerDesignMethod.COHEN_COON,
        )
        for key in (
            "numerator",
            "denominator",
            "parameters",
            "margin",
            "omega_min",
            "omega_max",
            "points",
        ):
            _visible(self.rows[key], phase)
        for key in ("process_gain", "dead_time", "lag_time"):
            _visible(self.rows[key], table_open)
        for key in ("critical_gain", "critical_period"):
            _visible(self.rows[key], closed)
        self.controller_type_combo.setVisible(not phase)
        self.preview_label.setText(
            "Zielphase = -180° + Φ_R,soll" if phase else self.method_combo.currentText()
        )

    @Slot()
    def _calculate(self) -> None:
        method = ControllerDesignMethod(self.method_combo.currentData())
        controller_type = (
            ControllerType.P
            if method is ControllerDesignMethod.P_PHASE_MARGIN
            else ControllerType(self.controller_type_combo.currentData())
        )
        self.presenter.calculate(
            ControllerDesignInputDraft(
                method,
                controller_type,
                self.task_name_edit.text(),
                self.numerator_edit.text(),
                self.denominator_edit.text(),
                _parameter_rows(self.parameters_edit.text()),
                self.target_margin_edit.text(),
                self.omega_min_edit.text(),
                self.omega_max_edit.text(),
                self.points_per_decade_edit.text(),
                self.process_gain_edit.text(),
                self.dead_time_edit.text(),
                self.lag_time_edit.text(),
                self.critical_gain_edit.text(),
                self.critical_period_edit.text(),
            )
        )

    @Slot(object)
    def _render(self, value: object) -> None:
        if type(value) is not ControllerDesignViewState:
            return
        running = value.run_status is ControllerDesignUiRunStatus.RUNNING
        self._set_inputs_enabled(not running)
        if value.result is None:
            for output in self.outputs.values():
                output.clear()
            self.copy_button.setEnabled(False)
            if value.message:
                self.outputs["diagnostics"].setPlainText(value.message)
                self.result_tabs.setCurrentWidget(self.outputs["diagnostics"])
            return
        result = value.result
        parameters = result.controller_parameters
        self.outputs["overview"].setPlainText(
            f"Verfahren: {controller_design_method_text(result.method)}\n"
            f"Status: {'Lösung erstellt' if result.has_copyable_solution else 'Keine Lösung'}"
        )
        self.outputs["inputs"].setPlainText(
            "\n".join(f"{key}: {item}" for key, item in result.normalized_parameters)
        )
        self.outputs["formula"].setPlainText(result.formula_or_target)
        self.outputs["parameters"].setPlainText(
            ""
            if parameters is None
            else (
                f"{parameters.canonical_transfer_function}\n"
                f"{parameters.parallel_latex}\n{parameters.ideal_latex}"
            )
        )
        self.outputs["frequency"].setPlainText(
            "\n".join(
                f"Kandidat {item.candidate_index}: ω={item.target_frequency:.12g} rad/s, "
                f"k_P={item.positive_k_p:.12g}, "
                f"Φ_R={item.achieved_phase_margin_degrees:.8g}°, "
                f"Status: {controller_design_candidate_status_text(item.status)}"
                for item in result.candidates
            )
        )
        self.outputs["controls"].setPlainText(
            "\n".join(
                f"{'✓' if item.passed else '✗'} {item.label}: {item.message}"
                for item in result.controls
            )
        )
        self.outputs["steps"].setPlainText(
            "\n".join(f"{index}. {item}" for index, item in enumerate(result.worked_steps, 1))
        )
        self.outputs["latex"].setPlainText(result.latex)
        self.outputs["diagnostics"].setPlainText(
            "\n".join(f"{item.code}: {item.message}" for item in result.diagnostics)
        )
        self.copy_button.setEnabled(result.has_copyable_solution)
        if result.has_copyable_solution:
            self.result_tabs.setCurrentWidget(self.outputs["latex"])
        else:
            self.result_tabs.setCurrentWidget(self.outputs["diagnostics"])

    @Slot()
    def _reset(self) -> None:
        self.presenter.reset()
        self.task_name_edit.clear()
        self.method_combo.setCurrentIndex(0)
        self.controller_type_combo.setCurrentIndex(2)
        self.numerator_edit.setText("100")
        self.denominator_edit.setText("s*(10*s+1)")
        self.parameters_edit.clear()
        self.target_margin_edit.setText("20")
        self.omega_min_edit.setText("1e-4")
        self.omega_max_edit.setText("1e2")
        self.points_per_decade_edit.setText("32")
        self.process_gain_edit.setText("1.8")
        self.dead_time_edit.setText("12")
        self.lag_time_edit.setText("72")
        self.critical_gain_edit.setText("1.62")
        self.critical_period_edit.setText("3")
        self._method_changed()

    def _set_inputs_enabled(self, enabled: bool) -> None:
        for widget in (
            self.task_name_edit,
            self.method_combo,
            self.controller_type_combo,
            *(row[1] for row in self.rows.values()),
            self.calculate_button,
            self.reset_button,
        ):
            widget.setEnabled(enabled)

    @Slot()
    def _copy(self) -> None:
        if self.copy_button.isEnabled():
            QGuiApplication.clipboard().setText(self.latex_output.toPlainText())


def _visible(row: tuple[QLabel, QWidget], visible: bool) -> None:
    row[0].setVisible(visible)
    row[1].setVisible(visible)


def _line(text: str, name: str) -> QLineEdit:
    widget = QLineEdit(text)
    widget.setObjectName(name)
    return widget


def _combo(name: str) -> QComboBox:
    widget = QComboBox()
    widget.setObjectName(name)
    return widget


def _button(text: str, name: str) -> QPushButton:
    widget = QPushButton(text)
    widget.setObjectName(name)
    return widget


def _parameter_rows(text: str) -> tuple[ParameterInputDraft, ...]:
    rows: list[ParameterInputDraft] = []
    for item in text.replace(";", ",").split(","):
        if not item.strip() or "=" not in item:
            continue
        name, value = (part.strip() for part in item.split("=", 1))
        fraction = value.split("/", 1)
        rows.append(
            ParameterInputDraft(
                name,
                fraction[0].strip(),
                fraction[1].strip() if len(fraction) == 2 else "1",
            )
        )
    return tuple(rows)


__all__ = ["ControllerDesignWorkspace"]
