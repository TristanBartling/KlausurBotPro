"""Direct characteristic-polynomial stability workspace."""

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

from klausurbotpro.application import prepend_latex_task_heading
from klausurbotpro.application.stability_workflow import (
    AnalysisTarget,
    PolynomialRole,
    StabilityInputDraft,
    StabilityMethod,
)
from klausurbotpro.ui.stability_presenter import StabilityPresenter
from klausurbotpro.ui.stability_view_state import StabilityViewState


class StabilityWorkspace(QWidget):
    def __init__(self, presenter: StabilityPresenter, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.presenter = presenter
        self._latex_task_title = ""
        self.setObjectName("stabilityWorkspace")
        self._build_ui()
        self.presenter.state_changed.connect(self.render_state)
        self.render_state(self.presenter.state)

    def _build_ui(self) -> None:
        self.method_combo = QComboBox()
        self.method_combo.setObjectName("stabilityMethod")
        self.method_combo.addItem("Hurwitz", StabilityMethod.HURWITZ.value)
        self.method_combo.addItem("Routh", StabilityMethod.ROUTH.value)
        self.polynomial_edit = QPlainTextEdit()
        self.polynomial_edit.setObjectName("stabilityPolynomial")
        self.polynomial_edit.setPlaceholderText("z. B. s^3 + 4*s^2 + 5*s + K_P")
        self.polynomial_edit.setMaximumHeight(80)
        self.variable_edit = QLineEdit("s")
        self.variable_edit.setObjectName("stabilityVariable")
        self.parameters_edit = QLineEdit()
        self.parameters_edit.setObjectName("stabilityParameters")
        self.parameters_edit.setPlaceholderText("maximal zwei, z. B. a, K")
        self.assumptions_edit = QPlainTextEdit()
        self.assumptions_edit.setObjectName("stabilityAssumptions")
        self.assumptions_edit.setPlaceholderText("z. B. T1 > 0; TI > 0 oder 0 < D < 1")
        self.assumptions_edit.setMaximumHeight(70)
        self.role_combo = QComboBox()
        self.role_combo.setObjectName("stabilityPolynomialRole")
        for label, role_value in (
            ("Rohes charakteristisches Polynom", PolynomialRole.DIRECT_CHARACTERISTIC_POLYNOMIAL),
            ("Reduzierter E/A-Nenner", PolynomialRole.REDUCED_TRANSFER_DENOMINATOR),
            ("Rohes geschlossenes Polynom", PolynomialRole.RAW_CLOSED_LOOP_CHARACTERISTIC),
            ("Zustandsraum-Charakteristik", PolynomialRole.STATE_CHARACTERISTIC_POLYNOMIAL),
        ):
            self.role_combo.addItem(label, role_value.value)
        self.target_combo = QComboBox()
        self.target_combo.setObjectName("stabilityAnalysisTarget")
        for label, target_value in (
            ("Interne asymptotische Stabilität", AnalysisTarget.INTERNAL_CLOSED_LOOP_ASYMPTOTIC),
            ("E/A-asymptotische Stabilität", AnalysisTarget.EXTERNAL_BIBO),
            ("Zustandsstabilität", AnalysisTarget.STATE_ASYMPTOTIC),
        ):
            self.target_combo.addItem(label, target_value.value)
        self.provenance_edit = QLineEdit()
        self.provenance_edit.setObjectName("stabilityProvenance")
        self.cancellation_edit = QLineEdit()
        self.cancellation_edit.setObjectName("stabilityCancellationNote")
        self.task_title_edit = QLineEdit()
        self.task_title_edit.setObjectName("stabilityTaskTitle")
        self.task_title_edit.setPlaceholderText("z. B. Aufgabe 1a – Regelungsnormalform")
        self.analyze_button = QPushButton("Hurwitz analysieren")
        self.analyze_button.setObjectName("analyzeHurwitz")
        self.reset_button = QPushButton("Zurücksetzen")
        self.copy_latex_button = QPushButton("LaTeX kopieren")
        self.copy_latex_button.setObjectName("copyStabilityLatex")
        actions = QHBoxLayout()
        actions.addWidget(self.analyze_button)
        actions.addWidget(self.reset_button)
        actions.addWidget(self.copy_latex_button)
        form_widget = QWidget()
        form = QFormLayout(form_widget)
        form.addRow("Verfahren:", self.method_combo)
        form.addRow("Aufgabenname / LaTeX-Überschrift:", self.task_title_edit)
        form.addRow("Polynom:", self.polynomial_edit)
        form.addRow("Variable:", self.variable_edit)
        form.addRow("Entscheidungsparameter:", self.parameters_edit)
        form.addRow("Annahmen:", self.assumptions_edit)
        form.addRow("Polynomrolle:", self.role_combo)
        form.addRow("Analyseziel:", self.target_combo)
        form.addRow("Provenienznotiz:", self.provenance_edit)
        form.addRow("Kürzungsstatus/-hinweis:", self.cancellation_edit)
        form.addRow(actions)

        self.result_tabs = QTabWidget()
        self.result_tabs.setObjectName("stabilityResultTabs")
        self.result_edits: dict[str, QPlainTextEdit] = {}
        for key, label in (
            ("summary", "Übersicht"),
            ("cases", "Kanonisches Polynom und Gradfälle"),
            ("hurwitz", "Hurwitz-Matrix und Determinanten"),
            ("routh", "Routh-Schema"),
            ("region", "Stabilitätsbedingungen und Parameterbereich"),
            ("short", "Numerische Kurzlösung"),
            ("steps", "Worked Steps"),
            ("latex", "LaTeX-Lösung"),
            ("diagnostics", "Diagnosen"),
        ):
            edit = QPlainTextEdit()
            edit.setObjectName(f"stability_{key}")
            edit.setReadOnly(True)
            self.result_edits[key] = edit
            self.result_tabs.addTab(edit, label)
        splitter = QSplitter()
        splitter.addWidget(form_widget)
        splitter.addWidget(self.result_tabs)
        splitter.setSizes((410, 790))
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Direkte charakteristische Polynomeingabe – Stabilität"))
        layout.addWidget(splitter, 1)
        self.analyze_button.clicked.connect(self.analyze)
        self.reset_button.clicked.connect(self.reset)
        self.copy_latex_button.clicked.connect(self.copy_latex)
        self.method_combo.currentIndexChanged.connect(self._method_changed)
        self._method_changed()

    @Slot()
    def analyze(self) -> None:
        self._latex_task_title = self.task_title_edit.text()
        try:
            method = StabilityMethod(_combo_value(self.method_combo))
            role = PolynomialRole(_combo_value(self.role_combo))
            analysis_target = AnalysisTarget(_combo_value(self.target_combo))
        except (TypeError, ValueError):
            self.result_edits["summary"].setPlainText("Eingabe ungültig.")
            self.result_edits["diagnostics"].setPlainText(
                "Polynomrolle oder Analyseziel fehlt oder ist ungültig."
            )
            self.result_edits["latex"].clear()
            self.copy_latex_button.setEnabled(False)
            return
        self.presenter.analyze(
            StabilityInputDraft(
                polynomial_text=self.polynomial_edit.toPlainText(),
                variable_name=self.variable_edit.text(),
                decision_parameters_text=self.parameters_edit.text(),
                assumptions_text=self.assumptions_edit.toPlainText(),
                role=role,
                analysis_target=analysis_target,
                provenance_note=self.provenance_edit.text(),
                cancellation_note=self.cancellation_edit.text(),
                method=method,
            )
        )

    @Slot()
    def reset(self) -> None:
        self.polynomial_edit.clear()
        self.parameters_edit.clear()
        self.assumptions_edit.clear()
        self.provenance_edit.clear()
        self.cancellation_edit.clear()
        self.method_combo.setCurrentIndex(0)
        self.task_title_edit.clear()
        self._latex_task_title = ""
        self.presenter.reset()

    @Slot()
    def copy_latex(self) -> None:
        text = self.result_edits["latex"].toPlainText()
        if text:
            QApplication.clipboard().setText(text)

    @Slot(object)
    def render_state(self, state: object) -> None:
        if type(state) is not StabilityViewState:
            return
        self.result_edits["summary"].setPlainText(state.summary)
        self.result_edits["cases"].setPlainText(state.canonical_cases)
        self.result_edits["hurwitz"].setPlainText(state.hurwitz_details)
        self.result_edits["routh"].setPlainText(state.routh_details)
        self.result_edits["region"].setPlainText(state.parameter_region)
        self.result_edits["short"].setPlainText(state.short_solution)
        self.result_edits["steps"].setPlainText(state.worked_steps)
        latex_source = prepend_latex_task_heading(state.latex_source, self._latex_task_title)
        self.result_edits["latex"].setPlainText(latex_source)
        self.result_edits["diagnostics"].setPlainText(state.diagnostics)
        self.copy_latex_button.setEnabled(bool(latex_source))
        self._set_method_tabs(state.method)

    @Slot()
    def _method_changed(self) -> None:
        try:
            method = StabilityMethod(_combo_value(self.method_combo))
        except (TypeError, ValueError):
            return
        self.analyze_button.setText(
            "Hurwitz analysieren" if method is StabilityMethod.HURWITZ else "Routh analysieren"
        )
        self._set_method_tabs(method.value)

    def _set_method_tabs(self, method: str) -> None:
        hurwitz_index = self.result_tabs.indexOf(self.result_edits["hurwitz"])
        routh_index = self.result_tabs.indexOf(self.result_edits["routh"])
        self.result_tabs.setTabVisible(hurwitz_index, method == StabilityMethod.HURWITZ.value)
        self.result_tabs.setTabVisible(routh_index, method == StabilityMethod.ROUTH.value)


def _combo_value(combo: QComboBox) -> str:
    value = combo.currentData()
    if type(value) is not str or not value:
        raise ValueError("ComboBox data must be a non-empty enum value.")
    return value


__all__ = ["StabilityWorkspace"]
