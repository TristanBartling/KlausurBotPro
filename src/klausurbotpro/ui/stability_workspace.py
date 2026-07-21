"""Direct characteristic-polynomial Hurwitz workspace."""

from __future__ import annotations

from PySide6.QtCore import Slot
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

from klausurbotpro.application.stability_workflow import (
    AnalysisTarget,
    PolynomialRole,
    StabilityInputDraft,
)
from klausurbotpro.ui.stability_presenter import StabilityPresenter
from klausurbotpro.ui.stability_view_state import StabilityViewState


class StabilityWorkspace(QWidget):
    def __init__(self, presenter: StabilityPresenter, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.presenter = presenter
        self.setObjectName("stabilityWorkspace")
        self._build_ui()
        self.presenter.state_changed.connect(self.render_state)
        self.render_state(self.presenter.state)

    def _build_ui(self) -> None:
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
            self.role_combo.addItem(label, role_value)
        self.target_combo = QComboBox()
        self.target_combo.setObjectName("stabilityAnalysisTarget")
        for label, target_value in (
            ("Interne asymptotische Stabilität", AnalysisTarget.INTERNAL_CLOSED_LOOP_ASYMPTOTIC),
            ("E/A-asymptotische Stabilität", AnalysisTarget.EXTERNAL_BIBO),
            ("Zustandsstabilität", AnalysisTarget.STATE_ASYMPTOTIC),
        ):
            self.target_combo.addItem(label, target_value)
        self.provenance_edit = QLineEdit()
        self.provenance_edit.setObjectName("stabilityProvenance")
        self.cancellation_edit = QLineEdit()
        self.cancellation_edit.setObjectName("stabilityCancellationNote")
        self.analyze_button = QPushButton("Hurwitz analysieren")
        self.analyze_button.setObjectName("analyzeHurwitz")
        self.reset_button = QPushButton("Zurücksetzen")
        actions = QHBoxLayout()
        actions.addWidget(self.analyze_button)
        actions.addWidget(self.reset_button)
        form_widget = QWidget()
        form = QFormLayout(form_widget)
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
        layout.addWidget(QLabel("Direkte charakteristische Polynomeingabe – Hurwitz"))
        layout.addWidget(splitter, 1)
        self.analyze_button.clicked.connect(self.analyze)
        self.reset_button.clicked.connect(self.reset)

    @Slot()
    def analyze(self) -> None:
        self.presenter.analyze(
            StabilityInputDraft(
                polynomial_text=self.polynomial_edit.toPlainText(),
                variable_name=self.variable_edit.text(),
                decision_parameters_text=self.parameters_edit.text(),
                assumptions_text=self.assumptions_edit.toPlainText(),
                role=self.role_combo.currentData(),
                analysis_target=self.target_combo.currentData(),
                provenance_note=self.provenance_edit.text(),
                cancellation_note=self.cancellation_edit.text(),
            )
        )

    @Slot()
    def reset(self) -> None:
        self.polynomial_edit.clear()
        self.parameters_edit.clear()
        self.assumptions_edit.clear()
        self.provenance_edit.clear()
        self.cancellation_edit.clear()
        self.presenter.reset()

    @Slot(object)
    def render_state(self, state: object) -> None:
        if type(state) is not StabilityViewState:
            return
        self.result_edits["summary"].setPlainText(state.summary)
        self.result_edits["cases"].setPlainText(state.canonical_cases)
        self.result_edits["hurwitz"].setPlainText(state.hurwitz_details)
        self.result_edits["region"].setPlainText(state.parameter_region)
        self.result_edits["short"].setPlainText(state.short_solution)
        self.result_edits["steps"].setPlainText(state.worked_steps)
        self.result_edits["latex"].setPlainText(state.latex_source)
        self.result_edits["diagnostics"].setPlainText(state.diagnostics)


__all__ = ["StabilityWorkspace"]
