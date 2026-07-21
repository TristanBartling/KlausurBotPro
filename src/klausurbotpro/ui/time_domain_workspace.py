"""Visible time-domain workspace with mode-specific safe inputs."""

from __future__ import annotations

from PySide6.QtCore import Slot
from PySide6.QtWidgets import (
    QApplication,
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

from klausurbotpro.application import TimeDomainInputDraft, TimeDomainTaskType
from klausurbotpro.ui.time_domain_presenter import TimeDomainPresenter
from klausurbotpro.ui.time_domain_view_state import TimeDomainViewState


class TimeDomainWorkspace(QWidget):
    def __init__(self, presenter: TimeDomainPresenter, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.presenter = presenter
        self.setObjectName("timeDomainWorkspace")
        self._build_ui()
        self.presenter.state_changed.connect(self.render_state)
        self.render_state(self.presenter.state)

    def _build_ui(self) -> None:
        self.task_combo = QComboBox()
        self.task_combo.setObjectName("timeDomainTaskType")
        for label, value in (
            ("Direkte Laplace-Transformation", TimeDomainTaskType.DIRECT_LAPLACE),
            ("Inverse Laplace-Transformation", TimeDomainTaskType.INVERSE_LAPLACE),
            ("Sprungantwort", TimeDomainTaskType.STEP_RESPONSE),
            ("Allgemeine Antwort G(s), U(s)", TimeDomainTaskType.GENERAL_RESPONSE),
            ("Exponentialeingang", TimeDomainTaskType.EXPONENTIAL_INPUT),
        ):
            self.task_combo.addItem(label, value.value)
        self.time_edit = QPlainTextEdit()
        self.time_edit.setObjectName("timeDomainTimeExpression")
        self.time_edit.setPlaceholderText("z. B. 2*t*exp(-4*t)")
        self.image_edit = QPlainTextEdit()
        self.image_edit.setObjectName("timeDomainImageExpression")
        self.image_edit.setPlaceholderText("z. B. (s-4)/((s-4)^2+4)")
        self.system_edit = QPlainTextEdit()
        self.system_edit.setObjectName("timeDomainSystemExpression")
        self.system_edit.setPlaceholderText("G(s), z. B. 1/(2*s+1)")
        self.input_edit = QPlainTextEdit()
        self.input_edit.setObjectName("timeDomainInputExpression")
        self.input_edit.setPlaceholderText("U(s), z. B. 9/(s-2)")
        for edit in (self.time_edit, self.image_edit, self.system_edit, self.input_edit):
            edit.setMaximumHeight(68)
        self.step_amplitude_edit = QLineEdit("1")
        self.step_amplitude_edit.setObjectName("timeDomainStepAmplitude")
        self.exponential_amplitude_edit = QLineEdit("1")
        self.exponential_amplitude_edit.setObjectName("timeDomainExponentialAmplitude")
        self.exponential_exponent_edit = QLineEdit("0")
        self.exponential_exponent_edit.setObjectName("timeDomainExponentialExponent")
        self.assumptions_edit = QLineEdit()
        self.assumptions_edit.setObjectName("timeDomainAssumptions")
        self.assumptions_edit.setPlaceholderText("z. B. T > 0; omega > 0")
        form_widget = QWidget()
        form = QFormLayout(form_widget)
        form.addRow("Aufgabentyp:", self.task_combo)
        self._rows: dict[str, tuple[QLabel, QWidget]] = {}
        for key, label, widget in (
            ("time", "f(t):", self.time_edit),
            ("image", "F(s):", self.image_edit),
            ("system", "G(s):", self.system_edit),
            ("input", "U(s):", self.input_edit),
            ("step", "Sprunghöhe A:", self.step_amplitude_edit),
            ("exp_amp", "Exponentialamplitude:", self.exponential_amplitude_edit),
            ("exp_lambda", "Exponentialexponent:", self.exponential_exponent_edit),
            ("assumptions", "Parameterannahmen:", self.assumptions_edit),
        ):
            label_widget = QLabel(label)
            form.addRow(label_widget, widget)
            self._rows[key] = (label_widget, widget)
        self.calculate_button = QPushButton("Zeitbereich berechnen")
        self.calculate_button.setObjectName("calculateTimeDomain")
        self.reset_button = QPushButton("Zurücksetzen")
        self.copy_latex_button = QPushButton("LaTeX kopieren")
        self.copy_latex_button.setObjectName("copyTimeDomainLatex")
        actions = QHBoxLayout()
        actions.addWidget(self.calculate_button)
        actions.addWidget(self.reset_button)
        actions.addWidget(self.copy_latex_button)
        form.addRow(actions)
        self.result_tabs = QTabWidget()
        self.result_tabs.setObjectName("timeDomainResultTabs")
        self.result_edits: dict[str, QPlainTextEdit] = {}
        for key, label in (
            ("summary", "Übersicht"),
            ("rational", "Rationale Analyse"),
            ("partial", "Partialbruchzerlegung"),
            ("time", "Zeitfunktion"),
            ("checks", "Kontrollen"),
            ("short", "Numerische Kurzlösung"),
            ("steps", "Worked Steps"),
            ("latex", "LaTeX-Lösung"),
            ("diagnostics", "Diagnosen"),
        ):
            edit = QPlainTextEdit()
            edit.setObjectName(f"timeDomain_{key}")
            edit.setReadOnly(True)
            self.result_edits[key] = edit
            self.result_tabs.addTab(edit, label)
        splitter = QSplitter()
        splitter.addWidget(form_widget)
        splitter.addWidget(self.result_tabs)
        splitter.setSizes((410, 790))
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Laplace, Partialbruchzerlegung und Zeitantworten"))
        layout.addWidget(splitter, 1)
        self.task_combo.currentIndexChanged.connect(self._update_visible_inputs)
        self.calculate_button.clicked.connect(self.calculate)
        self.reset_button.clicked.connect(self.reset)
        self.copy_latex_button.clicked.connect(self.copy_latex)
        self._update_visible_inputs()

    @Slot()
    def calculate(self) -> None:
        try:
            task_type = TimeDomainTaskType(_combo_value(self.task_combo))
        except (TypeError, ValueError):
            self.render_state(
                TimeDomainViewState(
                    summary="Eingabe ungültig.",
                    diagnostics="Der Aufgabentyp ist ungültig.",
                    failed=True,
                )
            )
            return
        self.presenter.calculate(
            TimeDomainInputDraft(
                task_type=task_type,
                time_expression_text=self.time_edit.toPlainText(),
                image_expression_text=self.image_edit.toPlainText(),
                system_expression_text=self.system_edit.toPlainText(),
                input_expression_text=self.input_edit.toPlainText(),
                step_amplitude_text=self.step_amplitude_edit.text(),
                exponential_amplitude_text=self.exponential_amplitude_edit.text(),
                exponential_exponent_text=self.exponential_exponent_edit.text(),
                assumptions_text=self.assumptions_edit.text(),
            )
        )

    @Slot()
    def reset(self) -> None:
        for edit in (self.time_edit, self.image_edit, self.system_edit, self.input_edit):
            edit.clear()
        self.step_amplitude_edit.setText("1")
        self.exponential_amplitude_edit.setText("1")
        self.exponential_exponent_edit.setText("0")
        self.assumptions_edit.clear()
        self.presenter.reset()

    @Slot()
    def copy_latex(self) -> None:
        text = self.result_edits["latex"].toPlainText()
        if text:
            QApplication.clipboard().setText(text)

    @Slot()
    def _update_visible_inputs(self) -> None:
        try:
            task_type = TimeDomainTaskType(_combo_value(self.task_combo))
        except (TypeError, ValueError):
            return
        visible = {
            TimeDomainTaskType.DIRECT_LAPLACE: {"time", "assumptions"},
            TimeDomainTaskType.INVERSE_LAPLACE: {"image", "assumptions"},
            TimeDomainTaskType.STEP_RESPONSE: {"system", "step", "assumptions"},
            TimeDomainTaskType.GENERAL_RESPONSE: {"system", "input", "assumptions"},
            TimeDomainTaskType.EXPONENTIAL_INPUT: {
                "system", "exp_amp", "exp_lambda", "assumptions"
            },
        }[task_type]
        for key, widgets in self._rows.items():
            for widget in widgets:
                widget.setVisible(key in visible)

    @Slot(object)
    def render_state(self, state: object) -> None:
        if type(state) is not TimeDomainViewState:
            return
        values = {
            "summary": state.summary,
            "rational": state.rational_analysis,
            "partial": state.partial_fractions,
            "time": state.time_function,
            "checks": state.verifications,
            "short": state.short_solution,
            "steps": state.worked_steps,
            "latex": state.latex_source,
            "diagnostics": state.diagnostics,
        }
        for key, value in values.items():
            self.result_edits[key].setPlainText(value)
        self.copy_latex_button.setEnabled(bool(state.latex_source))


def _combo_value(combo: QComboBox) -> str:
    value = combo.currentData()
    if type(value) is not str or not value:
        raise ValueError("ComboBox data must be a non-empty enum value.")
    return value


__all__ = ["TimeDomainWorkspace"]
