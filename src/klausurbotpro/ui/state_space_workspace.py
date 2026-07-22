"""Visible state-space bridge workspace."""

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

from klausurbotpro.application import StateSpaceInputDraft, StateSpaceTaskType
from klausurbotpro.ui.state_space_presenter import StateSpacePresenter
from klausurbotpro.ui.state_space_view_state import StateSpaceViewState


class StateSpaceWorkspace(QWidget):
    def __init__(self, presenter: StateSpacePresenter, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.presenter = presenter
        self.setObjectName("stateSpaceWorkspace")
        self._build_ui()
        presenter.state_changed.connect(self.render_state)
        self.render_state(presenter.state)

    def _build_ui(self) -> None:
        self.task_combo = QComboBox()
        self.task_combo.setObjectName("stateSpaceTaskType")
        self.task_combo.addItem(
            "DGL → Regelungsnormalform", StateSpaceTaskType.ODE_TO_CONTROLLABLE_CANONICAL.value
        )
        self.task_combo.addItem(
            "Zustandsraum → Übertragungsfunktion",
            StateSpaceTaskType.STATE_SPACE_TO_TRANSFER_FUNCTION.value,
        )
        self.output_name_edit = QLineEdit("y")
        self.output_name_edit.setObjectName("stateSpaceOutputName")
        self.input_name_edit = QLineEdit("u")
        self.input_name_edit.setObjectName("stateSpaceInputName")
        self.order_combo = QComboBox()
        self.order_combo.setObjectName("stateSpaceOdeOrder")
        for order in range(1, 5):
            self.order_combo.addItem(str(order), order)
        self.order_combo.setCurrentIndex(1)
        coefficients = QWidget()
        coefficient_form = QFormLayout(coefficients)
        self.coefficient_edits = [QLineEdit("0") for _ in range(5)]
        for index, edit in enumerate(self.coefficient_edits):
            edit.setObjectName(f"stateSpaceOdeCoefficient{index}")
            coefficient_form.addRow(f"a_{index}:", edit)
        self.input_factor_edit = QLineEdit("1")
        self.input_factor_edit.setObjectName("stateSpaceOdeInputFactor")
        coefficient_form.addRow("b_0:", self.input_factor_edit)
        self.matrix_a_edit = QPlainTextEdit("0, 1; -2, -3")
        self.matrix_a_edit.setObjectName("stateSpaceMatrixA")
        self.vector_b_edit = QPlainTextEdit("0; 1")
        self.vector_b_edit.setObjectName("stateSpaceVectorB")
        self.vector_c_edit = QPlainTextEdit("1, 0")
        self.vector_c_edit.setObjectName("stateSpaceVectorC")
        self.scalar_d_edit = QLineEdit("0")
        self.scalar_d_edit.setObjectName("stateSpaceScalarD")
        self.parameters_edit = QLineEdit()
        self.parameters_edit.setObjectName("stateSpaceParameters")
        self.assumptions_edit = QLineEdit()
        self.assumptions_edit.setObjectName("stateSpaceAssumptions")
        self.preview_label = QLabel()
        self.preview_label.setObjectName("stateSpaceInputPreview")
        self.preview_label.setWordWrap(True)
        form_widget = QWidget()
        form = QFormLayout(form_widget)
        form.addRow("Aufgabentyp:", self.task_combo)
        self._rows: dict[str, tuple[QLabel, QWidget]] = {}
        for key, label, widget in (
            ("output", "Ausgangsname:", self.output_name_edit),
            ("input", "Eingangsname:", self.input_name_edit),
            ("order", "Ausgangsordnung:", self.order_combo),
            ("coefficients", "DGL-Koeffizienten:", coefficients),
            ("a", "Matrix A:", self.matrix_a_edit),
            ("b", "Vektor b:", self.vector_b_edit),
            ("c", "Vektor c^T:", self.vector_c_edit),
            ("d", "Skalar d:", self.scalar_d_edit),
            ("parameters", "Entscheidungsparameter:", self.parameters_edit),
            ("assumptions", "Annahmen:", self.assumptions_edit),
            ("preview", "Vorschau:", self.preview_label),
        ):
            label_widget = QLabel(label)
            form.addRow(label_widget, widget)
            self._rows[key] = (label_widget, widget)
        self.calculate_button = QPushButton("Zustandsraum analysieren")
        self.calculate_button.setObjectName("analyzeStateSpace")
        self.reset_button = QPushButton("Zurücksetzen")
        self.copy_latex_button = QPushButton("LaTeX kopieren")
        self.copy_latex_button.setObjectName("copyStateSpaceLatex")
        actions = QHBoxLayout()
        actions.addWidget(self.calculate_button)
        actions.addWidget(self.reset_button)
        actions.addWidget(self.copy_latex_button)
        form.addRow(actions)
        self.result_tabs = QTabWidget()
        self.result_tabs.setObjectName("stateSpaceResultTabs")
        self.result_edits: dict[str, QPlainTextEdit] = {}
        for key, label in (
            ("summary", "Übersicht"),
            ("ode", "Normalisierte DGL und Zustandswahl"),
            ("matrices", "Zustandsraummatrizen"),
            ("characteristic", "Charakteristisches Polynom"),
            ("eigen", "Eigenwerte und Stabilität"),
            ("transfer", "Übertragungsfunktion"),
            ("checks", "Kontrollen"),
            ("steps", "Worked Steps"),
            ("latex", "LaTeX-Lösung"),
            ("diagnostics", "Diagnosen"),
        ):
            result_edit = QPlainTextEdit()
            result_edit.setReadOnly(True)
            result_edit.setObjectName(f"stateSpace_{key}")
            self.result_edits[key] = result_edit
            self.result_tabs.addTab(result_edit, label)
        splitter = QSplitter()
        splitter.addWidget(form_widget)
        splitter.addWidget(self.result_tabs)
        splitter.setSizes((410, 790))
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Zustandsraum – Regelungsnormalform und Übertragungsfunktion"))
        layout.addWidget(splitter, 1)
        self.task_combo.currentIndexChanged.connect(self._update_mode)
        self.order_combo.currentIndexChanged.connect(self._update_mode)
        for line_edit in (
            *self.coefficient_edits,
            self.input_factor_edit,
            self.output_name_edit,
            self.input_name_edit,
            self.parameters_edit,
        ):
            line_edit.textChanged.connect(self._update_preview)
        for plain_edit in (
            self.matrix_a_edit,
            self.vector_b_edit,
            self.vector_c_edit,
        ):
            plain_edit.textChanged.connect(self._update_preview)
        self.calculate_button.clicked.connect(self.calculate)
        self.reset_button.clicked.connect(self.presenter.reset)
        self.copy_latex_button.clicked.connect(self.copy_latex)
        self._update_mode()

    def _draft(self) -> StateSpaceInputDraft:
        task = StateSpaceTaskType(str(self.task_combo.currentData()))
        order = int(self.order_combo.currentData())
        return StateSpaceInputDraft(
            task_type=task,
            output_name=self.output_name_edit.text(),
            input_name=self.input_name_edit.text(),
            output_order=order,
            output_coefficient_texts=tuple(
                edit.text() for edit in self.coefficient_edits[: order + 1]
            ),
            input_coefficient_texts=(self.input_factor_edit.text(),),
            matrix_a_text=self.matrix_a_edit.toPlainText(),
            vector_b_text=self.vector_b_edit.toPlainText(),
            vector_c_text=self.vector_c_edit.toPlainText(),
            scalar_d_text=self.scalar_d_edit.text(),
            decision_parameters_text=self.parameters_edit.text(),
            assumptions_text=self.assumptions_edit.text(),
        )

    @Slot()
    def calculate(self) -> None:
        self._clear_results()
        self.presenter.calculate(self._draft())

    @Slot()
    def copy_latex(self) -> None:
        text = self.result_edits["latex"].toPlainText()
        if text:
            QApplication.clipboard().setText(text)

    @Slot()
    def _update_mode(self) -> None:
        ode_mode = (
            StateSpaceTaskType(str(self.task_combo.currentData()))
            is StateSpaceTaskType.ODE_TO_CONTROLLABLE_CANONICAL
        )
        for key, widgets in self._rows.items():
            visible = key not in ({"a", "b", "c", "d"} if ode_mode else {"order", "coefficients"})
            for widget in widgets:
                widget.setVisible(visible)
        order = int(self.order_combo.currentData())
        for index, edit in enumerate(self.coefficient_edits):
            edit.setVisible(index <= order)
            parent = edit.parentWidget()
            layout = parent.layout() if parent is not None else None
            label = layout.labelForField(edit) if isinstance(layout, QFormLayout) else None
            if label is not None:
                label.setVisible(index <= order)
        self.result_tabs.setTabVisible(self.result_tabs.indexOf(self.result_edits["ode"]), ode_mode)
        self._update_preview()

    @Slot()
    def _update_preview(self) -> None:
        if (
            StateSpaceTaskType(str(self.task_combo.currentData()))
            is StateSpaceTaskType.ODE_TO_CONTROLLABLE_CANONICAL
        ):
            self.preview_label.setText(self.presenter.ode_preview(self._draft()))
        else:
            self.preview_label.setText(
                self.presenter.matrix_preview(
                    self.matrix_a_edit.toPlainText(),
                    self.vector_b_edit.toPlainText(),
                    self.vector_c_edit.toPlainText(),
                )
            )

    def _clear_results(self) -> None:
        for edit in self.result_edits.values():
            edit.clear()
        self.copy_latex_button.setEnabled(False)

    @Slot(object)
    def render_state(self, state: object) -> None:
        if type(state) is not StateSpaceViewState:
            return
        values = {
            "summary": state.summary,
            "ode": state.normalized_ode,
            "matrices": state.matrices,
            "characteristic": state.characteristic,
            "eigen": state.eigenvalues_stability,
            "transfer": state.transfer_function,
            "checks": state.checks,
            "steps": state.worked_steps,
            "latex": state.latex_source,
            "diagnostics": state.diagnostics,
        }
        for key, value in values.items():
            self.result_edits[key].setPlainText(value)
        self.copy_latex_button.setEnabled(bool(state.latex_source))
        target = (
            "diagnostics"
            if state.failed and state.diagnostics
            else "latex"
            if state.latex_source
            else "summary"
        )
        self.result_tabs.setCurrentWidget(self.result_edits[target])


__all__ = ["StateSpaceWorkspace"]
