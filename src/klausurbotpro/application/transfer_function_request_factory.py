"""Qt-independent request creation from simple desktop input values."""

from __future__ import annotations

from dataclasses import dataclass
from math import gcd

from klausurbotpro.application._workflow_validation import (
    _is_safe_workflow_identifier,
)
from klausurbotpro.application.transfer_function_workflow_contracts import (
    TransferFunctionWorkflowLimits,
    TransferFunctionWorkflowRequest,
    WorkflowInputForm,
)
from klausurbotpro.domain import (
    ExactRationalValue,
    ParameterAssignment,
    ParameterSubstitutions,
)

_DEFAULT_LIMITS = TransferFunctionWorkflowLimits()
_REQUEST_FIELDS = frozenset(
    {
        "common_expression_text",
        "numerator_expression_text",
        "denominator_expression_text",
        "variable_name",
        "parameter_rows",
        "field",
    }
)


@dataclass(frozen=True, slots=True)
class ParameterInputDraft:
    """One untrusted parameter row represented only by strings."""

    parameter_name: str
    numerator_text: str
    denominator_text: str


@dataclass(frozen=True, slots=True)
class TransferFunctionInputDraft:
    """Simple immutable values collected by the desktop UI."""

    input_form: WorkflowInputForm
    common_expression_text: str
    numerator_expression_text: str
    denominator_expression_text: str
    variable_name: str
    parameter_rows: tuple[ParameterInputDraft, ...] = ()
    field: str | None = None


@dataclass(frozen=True, slots=True)
class TransferFunctionRequestFieldError:
    """Stable field attribution for one rejected draft value."""

    field: str
    code: str
    message: str
    row_index: int | None = None

    def __post_init__(self) -> None:
        if type(self.field) is not str or self.field not in _REQUEST_FIELDS:
            raise ValueError("field must identify a supported request field.")
        if type(self.code) is not str or not self.code:
            raise ValueError("code must be a non-empty string.")
        if type(self.message) is not str or not self.message:
            raise ValueError("message must be a non-empty string.")
        if self.row_index is not None and (
            type(self.row_index) is not int or self.row_index < 0
        ):
            raise ValueError("row_index must be a nonnegative real int or None.")


@dataclass(frozen=True, slots=True)
class TransferFunctionRequestCreationResult:
    """All-or-nothing result of converting a desktop draft."""

    request: TransferFunctionWorkflowRequest | None
    errors: tuple[TransferFunctionRequestFieldError, ...] = ()

    def __post_init__(self) -> None:
        errors = tuple(self.errors)
        if self.request is not None and (
            type(self.request) is not TransferFunctionWorkflowRequest
        ):
            raise TypeError("request must be a workflow request or None.")
        if any(
            type(error) is not TransferFunctionRequestFieldError
            for error in errors
        ):
            raise TypeError("errors must contain field errors.")
        if (self.request is None) == (not errors):
            raise ValueError("Exactly one of request or errors must be present.")
        object.__setattr__(self, "errors", errors)

    @property
    def succeeded(self) -> bool:
        """Whether a complete request was created."""

        return self.request is not None


class TransferFunctionRequestFactory:
    """Validate simple UI values and create one exact workflow request."""

    def __init__(
        self,
        limits: TransferFunctionWorkflowLimits = _DEFAULT_LIMITS,
    ) -> None:
        if type(limits) is not TransferFunctionWorkflowLimits:
            raise TypeError("limits must be TransferFunctionWorkflowLimits.")
        self._limits = limits
        self._max_parameters = min(
            limits.parser.max_symbols - 1,
            limits.raw.max_parameters,
            limits.reduction.max_parameters,
            limits.root_analysis.max_parameters,
        )
        self._max_parameter_rows = self._max_parameters
        self._max_integer_digits = min(
            limits.parser.max_integer_digits,
            limits.raw.max_integer_digits,
            limits.root_analysis.max_substitution_integer_digits,
            limits.stability_analysis.max_substitution_integer_digits,
        )

    def create(
        self,
        draft: TransferFunctionInputDraft,
    ) -> TransferFunctionRequestCreationResult:
        """Create a request without parsing mathematical expressions."""

        if type(draft) is not TransferFunctionInputDraft:
            raise TypeError("draft must be a TransferFunctionInputDraft.")
        errors: list[TransferFunctionRequestFieldError] = []
        self._validate_simple_fields(draft, errors)
        parameters, assignments = self._parameter_values(draft, errors)
        if errors:
            return TransferFunctionRequestCreationResult(None, tuple(errors))

        substitutions = (
            ParameterSubstitutions(tuple(assignments))
            if assignments
            else None
        )
        request = TransferFunctionWorkflowRequest(
            draft.input_form,
            common_expression_text=(
                draft.common_expression_text
                if draft.input_form is WorkflowInputForm.COMMON
                else None
            ),
            numerator_expression_text=(
                draft.numerator_expression_text
                if draft.input_form is WorkflowInputForm.SEPARATED
                else None
            ),
            denominator_expression_text=(
                draft.denominator_expression_text
                if draft.input_form is WorkflowInputForm.SEPARATED
                else None
            ),
            variable_name=draft.variable_name,
            allowed_parameter_names=tuple(sorted(parameters)),
            substitutions=substitutions,
            field=draft.field,
        )
        return TransferFunctionRequestCreationResult(request)

    def _validate_simple_fields(
        self,
        draft: TransferFunctionInputDraft,
        errors: list[TransferFunctionRequestFieldError],
    ) -> None:
        if type(draft.input_form) is not WorkflowInputForm:
            errors.append(
                _error("field", "invalid_input_form", "Ungültige Eingabeform.")
            )
        for name in (
            "common_expression_text",
            "numerator_expression_text",
            "denominator_expression_text",
            "variable_name",
        ):
            if type(getattr(draft, name)) is not str:
                errors.append(
                    _error(name, "invalid_type", "Das Feld muss Text enthalten.")
                )
        if type(draft.parameter_rows) is not tuple:
            errors.append(
                _error(
                    "parameter_rows",
                    "invalid_rows",
                    "Die Parameterzeilen besitzen ein ungültiges Format.",
                )
            )
        elif len(draft.parameter_rows) > self._max_parameter_rows:
            errors.append(
                _error(
                    "parameter_rows",
                    "parameter_limit_exceeded",
                    "Es wurden zu viele Parameterzeilen angegeben.",
                )
            )
        elif any(
            type(row) is not ParameterInputDraft
            for row in draft.parameter_rows
        ):
            errors.append(
                _error(
                    "parameter_rows",
                    "invalid_rows",
                    "Die Parameterzeilen besitzen ein ungültiges Format.",
                )
            )
        if draft.field is not None and type(draft.field) is not str:
            errors.append(
                _error("field", "invalid_type", "Das Fachfeld muss Text sein.")
            )
        if errors:
            return
        if not _is_safe_workflow_identifier(draft.variable_name):
            errors.append(
                _error(
                    "variable_name",
                    "unsafe_identifier",
                    "Die Hauptvariable ist kein sicherer Bezeichner.",
                )
            )
        if (
            draft.input_form is WorkflowInputForm.COMMON
            and not draft.common_expression_text.strip()
        ):
            errors.append(
                _error(
                    "common_expression_text",
                    "empty_expression",
                    "Der gemeinsame Ausdruck darf nicht leer sein.",
                )
            )
        if draft.input_form is WorkflowInputForm.SEPARATED:
            if not draft.numerator_expression_text.strip():
                errors.append(
                    _error(
                        "numerator_expression_text",
                        "empty_expression",
                        "Der Zähler darf nicht leer sein.",
                    )
                )
            if not draft.denominator_expression_text.strip():
                errors.append(
                    _error(
                        "denominator_expression_text",
                        "empty_expression",
                        "Der Nenner darf nicht leer sein.",
                    )
                )

    def _parameter_values(
        self,
        draft: TransferFunctionInputDraft,
        errors: list[TransferFunctionRequestFieldError],
    ) -> tuple[set[str], list[ParameterAssignment]]:
        if (
            type(draft.parameter_rows) is not tuple
            or len(draft.parameter_rows) > self._max_parameter_rows
        ):
            return set(), []
        parameters: set[str] = set()
        assignments: list[ParameterAssignment] = []
        for index, row in enumerate(draft.parameter_rows):
            if type(row) is not ParameterInputDraft:
                continue
            if any(
                type(value) is not str
                for value in (
                    row.parameter_name,
                    row.numerator_text,
                    row.denominator_text,
                )
            ):
                errors.append(
                    _row_error(index, "invalid_type", "Parameterwerte müssen Text sein.")
                )
                continue
            raw_name = row.parameter_name
            name = raw_name.strip()
            numerator = row.numerator_text.strip()
            denominator = row.denominator_text.strip()
            if not name:
                if numerator or denominator:
                    errors.append(
                        _row_error(
                            index,
                            "value_without_parameter",
                            "Ein Wert benötigt einen Parameternamen.",
                        )
                    )
                continue
            if raw_name != name or not _is_safe_workflow_identifier(name):
                errors.append(
                    _row_error(
                        index,
                        "unsafe_identifier",
                        "Der Parametername ist kein sicherer Bezeichner.",
                    )
                )
                continue
            if name == draft.variable_name:
                errors.append(
                    _row_error(
                        index,
                        "variable_conflict",
                        "Die Hauptvariable darf kein Parameter sein.",
                    )
                )
                continue
            if name in parameters:
                errors.append(
                    _row_error(
                        index,
                        "duplicate_parameter",
                        "Ein Parameter darf nur einmal vorkommen.",
                    )
                )
                continue
            parameters.add(name)
            if denominator and not numerator:
                errors.append(
                    _row_error(
                        index,
                        "denominator_without_numerator",
                        "Ein Nenner benötigt einen Zähler.",
                    )
                )
                continue
            if not numerator:
                continue
            parsed_numerator = self._integer(
                numerator,
                index,
                "invalid_numerator",
                "Der Zähler muss eine begrenzte ganze Zahl sein.",
                errors,
            )
            parsed_denominator = (
                1
                if not denominator
                else self._integer(
                    denominator,
                    index,
                    "invalid_denominator",
                    "Der Nenner muss eine begrenzte positive ganze Zahl sein.",
                    errors,
                    positive=True,
                )
            )
            if parsed_numerator is None or parsed_denominator is None:
                continue
            divisor = gcd(abs(parsed_numerator), parsed_denominator)
            assignments.append(
                ParameterAssignment(
                    name,
                    ExactRationalValue(
                        parsed_numerator // divisor,
                        parsed_denominator // divisor,
                    ),
                )
            )
        if len(parameters) > self._max_parameters:
            errors.append(
                _error(
                    "parameter_rows",
                    "parameter_limit_exceeded",
                    "Es wurden zu viele Parameter angegeben.",
                )
            )
        return parameters, assignments

    def _integer(
        self,
        text: str,
        row_index: int,
        code: str,
        message: str,
        errors: list[TransferFunctionRequestFieldError],
        *,
        positive: bool = False,
    ) -> int | None:
        digits = text[1:] if text.startswith(("+", "-")) else text
        if (
            not digits
            or not digits.isascii()
            or not digits.isdigit()
            or len(digits) > self._max_integer_digits
        ):
            errors.append(_row_error(row_index, code, message))
            return None
        value = int(text)
        if positive and value <= 0:
            errors.append(_row_error(row_index, code, message))
            return None
        return value


def _error(
    field: str,
    code: str,
    message: str,
) -> TransferFunctionRequestFieldError:
    return TransferFunctionRequestFieldError(field, code, message)


def _row_error(
    row_index: int,
    code: str,
    message: str,
) -> TransferFunctionRequestFieldError:
    return TransferFunctionRequestFieldError(
        "parameter_rows",
        code,
        message,
        row_index,
    )


__all__ = [
    "ParameterInputDraft",
    "TransferFunctionInputDraft",
    "TransferFunctionRequestCreationResult",
    "TransferFunctionRequestFactory",
    "TransferFunctionRequestFieldError",
]
