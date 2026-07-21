"""Visible time-domain workspace with mode-specific safe inputs."""

from __future__ import annotations

from PySide6.QtCore import Slot
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
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

from klausurbotpro.application import InputSignalType, TimeDomainInputDraft, TimeDomainTaskType
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
            ("Lineare DGL lösen", TimeDomainTaskType.SOLVE_ODE),
            ("Übertragungsfunktion aus DGL", TimeDomainTaskType.TRANSFER_FUNCTION_FROM_ODE),
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
        for plain_edit in (
            self.time_edit,
            self.image_edit,
            self.system_edit,
            self.input_edit,
        ):
            plain_edit.setMaximumHeight(68)
        self.step_amplitude_edit = QLineEdit("1")
        self.step_amplitude_edit.setObjectName("timeDomainStepAmplitude")
        self.exponential_amplitude_edit = QLineEdit("1")
        self.exponential_amplitude_edit.setObjectName("timeDomainExponentialAmplitude")
        self.exponential_exponent_edit = QLineEdit("0")
        self.exponential_exponent_edit.setObjectName("timeDomainExponentialExponent")
        self.assumptions_edit = QLineEdit()
        self.assumptions_edit.setObjectName("timeDomainAssumptions")
        self.assumptions_edit.setPlaceholderText("z. B. T > 0; omega > 0")
        self.output_name_edit = QLineEdit("y")
        self.output_name_edit.setObjectName("timeDomainOdeOutputName")
        self.input_name_edit = QLineEdit("u")
        self.input_name_edit.setObjectName("timeDomainOdeInputName")
        self.output_order_combo = QComboBox()
        self.output_order_combo.setObjectName("timeDomainOdeOutputOrder")
        for order in range(1, 5):
            self.output_order_combo.addItem(str(order), order)
        self.output_order_combo.setCurrentIndex(1)
        self.input_order_combo = QComboBox()
        self.input_order_combo.setObjectName("timeDomainOdeInputOrder")
        for order in range(5):
            self.input_order_combo.addItem(str(order), order)
        self.output_coefficient_edits = [QLineEdit("0") for _ in range(5)]
        self.input_coefficient_edits = [QLineEdit("0") for _ in range(5)]
        self.output_initial_edits = [QLineEdit() for _ in range(4)]
        self.input_initial_edits = [QLineEdit() for _ in range(4)]
        output_coefficients = QWidget()
        output_coefficients_form = QFormLayout(output_coefficients)
        input_coefficients = QWidget()
        input_coefficients_form = QFormLayout(input_coefficients)
        output_initials = QWidget()
        output_initials_form = QFormLayout(output_initials)
        input_initials = QWidget()
        input_initials_form = QFormLayout(input_initials)
        for order in range(5):
            self.output_coefficient_edits[order].setObjectName(
                f"timeDomainOutputCoefficient{order}"
            )
            self.input_coefficient_edits[order].setObjectName(f"timeDomainInputCoefficient{order}")
            output_coefficients_form.addRow(
                f"a_{order} für y^({order})(t):", self.output_coefficient_edits[order]
            )
            input_coefficients_form.addRow(
                f"b_{order} für u^({order})(t):", self.input_coefficient_edits[order]
            )
        for order in range(4):
            self.output_initial_edits[order].setObjectName(f"timeDomainOutputInitial{order}")
            self.input_initial_edits[order].setObjectName(f"timeDomainInputInitial{order}")
            output_initials_form.addRow(f"y^({order})(0+):", self.output_initial_edits[order])
            input_initials_form.addRow(f"u^({order})(0+):", self.input_initial_edits[order])
        self.ode_signal_combo = QComboBox()
        self.ode_signal_combo.setObjectName("timeDomainOdeSignalType")
        for label, signal_type in (
            ("Nullsignal", InputSignalType.ZERO),
            ("Sprung", InputSignalType.STEP),
            ("Exponential", InputSignalType.EXPONENTIAL),
            ("Polynom", InputSignalType.POLYNOMIAL),
            ("Sinus", InputSignalType.SINUS),
            ("Kosinus", InputSignalType.COSINUS),
            ("Direkte Eingabe U(s)", InputSignalType.IMAGE_EXPRESSION),
        ):
            self.ode_signal_combo.addItem(label, signal_type.value)
        self.ode_amplitude_edit = QLineEdit("1")
        self.ode_amplitude_edit.setObjectName("timeDomainOdeSignalAmplitude")
        self.ode_rate_edit = QLineEdit("1")
        self.ode_rate_edit.setObjectName("timeDomainOdeSignalRate")
        polynomial_widget = QWidget()
        polynomial_form = QFormLayout(polynomial_widget)
        self.polynomial_coefficient_edits = [QLineEdit("0") for _ in range(5)]
        for order, coefficient_edit in enumerate(self.polynomial_coefficient_edits):
            coefficient_edit.setObjectName(f"timeDomainPolynomialCoefficient{order}")
            polynomial_form.addRow(f"c_{order} für t^{order}:", coefficient_edit)
        self.zero_missing_checkbox = QCheckBox(
            "Nicht angegebene Anfangswerte ausdrücklich als 0 setzen"
        )
        self.zero_missing_checkbox.setObjectName("timeDomainExplicitZeroPolicy")
        self.zero_state_checkbox = QCheckBox("Vollständigen Nullzustand ausdrücklich bestätigen")
        self.zero_state_checkbox.setObjectName("timeDomainZeroStateConfirmed")
        self.ode_preview = QLabel()
        self.ode_preview.setObjectName("timeDomainOdePreview")
        self.ode_preview.setWordWrap(True)
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
            ("output_name", "Ausgangsname:", self.output_name_edit),
            ("input_name", "Eingangsname:", self.input_name_edit),
            ("output_order", "Ausgangsordnung:", self.output_order_combo),
            ("output_coefficients", "Ausgangskoeffizienten:", output_coefficients),
            ("input_order", "Eingangsordnung:", self.input_order_combo),
            ("input_coefficients", "Eingangskoeffizienten:", input_coefficients),
            ("ode_signal", "Eingangsart:", self.ode_signal_combo),
            ("ode_amplitude", "Amplitude A:", self.ode_amplitude_edit),
            ("ode_rate", "lambda / omega:", self.ode_rate_edit),
            ("polynomial", "Polynomkoeffizienten:", polynomial_widget),
            ("output_initials", "Ausgangsanfangswerte:", output_initials),
            ("input_initials", "Eingangsanfangswerte:", input_initials),
            ("zero_policy", "Nullpolitik:", self.zero_missing_checkbox),
            ("zero_state", "Nullzustand:", self.zero_state_checkbox),
            ("ode_preview", "DGL-Vorschau:", self.ode_preview),
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
            ("ode", "DGL und Anfangswerte"),
            ("laplace", "Laplace-Transformation"),
            ("equation", "Bildgleichung"),
            ("split", "Freie und erzwungene Antwort"),
            ("rational", "Rationale Analyse"),
            ("partial", "Partialbruchzerlegung"),
            ("time", "Zeitfunktion"),
            ("checks", "Kontrollen"),
            ("short", "Numerische Kurzlösung"),
            ("steps", "Worked Steps"),
            ("latex", "LaTeX-Lösung"),
            ("diagnostics", "Diagnosen"),
        ):
            result_edit = QPlainTextEdit()
            result_edit.setObjectName(f"timeDomain_{key}")
            result_edit.setReadOnly(True)
            self.result_edits[key] = result_edit
            self.result_tabs.addTab(result_edit, label)
        splitter = QSplitter()
        splitter.addWidget(form_widget)
        splitter.addWidget(self.result_tabs)
        splitter.setSizes((410, 790))
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Laplace, Partialbruchzerlegung und Zeitantworten"))
        layout.addWidget(splitter, 1)
        self.task_combo.currentIndexChanged.connect(self._update_visible_inputs)
        self.output_order_combo.currentIndexChanged.connect(self._update_ode_fields)
        self.input_order_combo.currentIndexChanged.connect(self._update_ode_fields)
        self.ode_signal_combo.currentIndexChanged.connect(self._update_ode_fields)
        for coefficient_edit in (
            *self.output_coefficient_edits,
            *self.input_coefficient_edits,
        ):
            coefficient_edit.textChanged.connect(self._update_ode_preview)
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
                output_name=self.output_name_edit.text(),
                input_name=self.input_name_edit.text(),
                output_order=int(self.output_order_combo.currentData()),
                input_order=int(self.input_order_combo.currentData()),
                output_coefficient_texts=tuple(
                    edit.text()
                    for edit in self.output_coefficient_edits[
                        : int(self.output_order_combo.currentData()) + 1
                    ]
                ),
                input_coefficient_texts=tuple(
                    edit.text()
                    for edit in self.input_coefficient_edits[
                        : int(self.input_order_combo.currentData()) + 1
                    ]
                ),
                output_initial_texts=tuple(
                    edit.text()
                    for edit in self.output_initial_edits[
                        : int(self.output_order_combo.currentData())
                    ]
                ),
                input_initial_texts=tuple(
                    edit.text()
                    for edit in self.input_initial_edits[
                        : int(self.input_order_combo.currentData())
                    ]
                ),
                ode_input_signal_type=InputSignalType(_combo_value(self.ode_signal_combo)),
                ode_signal_amplitude_text=self.ode_amplitude_edit.text(),
                ode_signal_rate_text=self.ode_rate_edit.text(),
                polynomial_coefficient_texts=tuple(
                    edit.text() for edit in self.polynomial_coefficient_edits
                ),
                missing_initials_are_zero=self.zero_missing_checkbox.isChecked(),
                zero_state_confirmed=self.zero_state_checkbox.isChecked(),
            )
        )

    @Slot()
    def reset(self) -> None:
        for plain_edit in (
            self.time_edit,
            self.image_edit,
            self.system_edit,
            self.input_edit,
        ):
            plain_edit.clear()
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
                "system",
                "exp_amp",
                "exp_lambda",
                "assumptions",
            },
            TimeDomainTaskType.SOLVE_ODE: {
                "output_name",
                "input_name",
                "output_order",
                "output_coefficients",
                "input_order",
                "input_coefficients",
                "ode_signal",
                "ode_amplitude",
                "ode_rate",
                "polynomial",
                "input",
                "output_initials",
                "input_initials",
                "zero_policy",
                "assumptions",
                "ode_preview",
            },
            TimeDomainTaskType.TRANSFER_FUNCTION_FROM_ODE: {
                "output_name",
                "input_name",
                "output_order",
                "output_coefficients",
                "input_order",
                "input_coefficients",
                "zero_state",
                "assumptions",
                "ode_preview",
            },
        }[task_type]
        for key, widgets in self._rows.items():
            for widget in widgets:
                widget.setVisible(key in visible)
        ode_mode = task_type in {
            TimeDomainTaskType.SOLVE_ODE,
            TimeDomainTaskType.TRANSFER_FUNCTION_FROM_ODE,
        }
        for key in ("ode", "laplace", "equation"):
            self.result_tabs.setTabVisible(
                self.result_tabs.indexOf(self.result_edits[key]), ode_mode
            )
        self.result_tabs.setTabVisible(
            self.result_tabs.indexOf(self.result_edits["split"]),
            task_type is TimeDomainTaskType.SOLVE_ODE,
        )
        self._update_ode_fields()

    @Slot()
    def _update_ode_fields(self) -> None:
        output_order = int(self.output_order_combo.currentData())
        input_order = int(self.input_order_combo.currentData())
        for order, field in enumerate(self.output_coefficient_edits):
            _set_form_field_visible(field, order <= output_order)
        for order, field in enumerate(self.input_coefficient_edits):
            _set_form_field_visible(field, order <= input_order)
        for order, field in enumerate(self.output_initial_edits):
            _set_form_field_visible(field, order < output_order)
        for order, field in enumerate(self.input_initial_edits):
            _set_form_field_visible(field, order < input_order)
        if TimeDomainTaskType(_combo_value(self.task_combo)) is not TimeDomainTaskType.SOLVE_ODE:
            self._update_ode_preview()
            return
        signal_type = InputSignalType(_combo_value(self.ode_signal_combo))
        self._rows["ode_rate"][0].setVisible(
            signal_type
            in {InputSignalType.EXPONENTIAL, InputSignalType.SINUS, InputSignalType.COSINUS}
        )
        self._rows["ode_rate"][1].setVisible(
            signal_type
            in {InputSignalType.EXPONENTIAL, InputSignalType.SINUS, InputSignalType.COSINUS}
        )
        self._rows["polynomial"][0].setVisible(signal_type is InputSignalType.POLYNOMIAL)
        self._rows["polynomial"][1].setVisible(signal_type is InputSignalType.POLYNOMIAL)
        self._rows["input"][0].setVisible(signal_type is InputSignalType.IMAGE_EXPRESSION)
        self._rows["input"][1].setVisible(signal_type is InputSignalType.IMAGE_EXPRESSION)
        self._update_ode_preview()

    @Slot()
    def _update_ode_preview(self) -> None:
        output_order = int(self.output_order_combo.currentData())
        input_order = int(self.input_order_combo.currentData())
        output_name = self.output_name_edit.text().strip() or "y"
        input_name = self.input_name_edit.text().strip() or "u"

        self.ode_preview.setText(
            self.presenter.ode_preview(
                output_name,
                input_name,
                tuple(
                    edit.text()
                    for edit in self.output_coefficient_edits[: output_order + 1]
                ),
                tuple(
                    edit.text()
                    for edit in self.input_coefficient_edits[: input_order + 1]
                ),
            )
        )

    @Slot(object)
    def render_state(self, state: object) -> None:
        if type(state) is not TimeDomainViewState:
            return
        values = {
            "summary": state.summary,
            "ode": state.ode_and_initials,
            "laplace": state.laplace_transformation,
            "equation": state.image_equation,
            "split": state.free_and_forced,
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


def _set_form_field_visible(field: QLineEdit, visible: bool) -> None:
    field.setVisible(visible)
    parent = field.parentWidget()
    if parent is None:
        return
    layout = parent.layout()
    if not isinstance(layout, QFormLayout):
        return
    label = layout.labelForField(field)
    if label is not None:
        label.setVisible(visible)


__all__ = ["TimeDomainWorkspace"]
