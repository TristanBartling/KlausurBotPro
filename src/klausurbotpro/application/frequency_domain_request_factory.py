"""Qt-independent creation of exact frequency-domain workflow requests."""

from __future__ import annotations

from dataclasses import dataclass
from math import gcd

from klausurbotpro.application.frequency_domain_workflow_contracts import (
    FrequencyDomainWorkflowLimits,
    FrequencyDomainWorkflowMode,
    FrequencyDomainWorkflowRequest,
    FrequencyPhasePresentation,
)
from klausurbotpro.application.transfer_function_request_factory import (
    TransferFunctionInputDraft,
    TransferFunctionRequestFactory,
)
from klausurbotpro.domain import ExactRationalValue, LogFrequencyGridRequest

_DEFAULT_LIMITS = FrequencyDomainWorkflowLimits()
_FREQUENCY_FIELDS = frozenset(
    {
        "common_expression_text",
        "numerator_expression_text",
        "denominator_expression_text",
        "variable_name",
        "parameter_rows",
        "field",
        "single_angular_frequency",
        "omega_min",
        "omega_max",
        "points_per_decade",
        "explicit_frequencies",
        "phase_presentation",
    }
)


@dataclass(frozen=True, slots=True)
class FrequencyDomainInputDraft:
    """Untrusted strings collected by the frequency GUI."""

    preparation: TransferFunctionInputDraft
    mode: FrequencyDomainWorkflowMode
    single_angular_frequency_text: str = ""
    omega_min_text: str = ""
    omega_max_text: str = ""
    points_per_decade_text: str = ""
    explicit_frequencies_text: str = ""
    phase_presentation: FrequencyPhasePresentation = (
        FrequencyPhasePresentation.PRINCIPAL_ONLY
    )


@dataclass(frozen=True, slots=True)
class FrequencyDomainRequestFieldError:
    """One stable GUI field error for frequency request creation."""

    field: str
    code: str
    message: str
    row_index: int | None = None

    def __post_init__(self) -> None:
        if type(self.field) is not str or self.field not in _FREQUENCY_FIELDS:
            raise ValueError("field must identify a supported frequency field.")
        if type(self.code) is not str or not self.code:
            raise ValueError("code must be a non-empty string.")
        if type(self.message) is not str or not self.message:
            raise ValueError("message must be a non-empty string.")
        if self.row_index is not None and (
            type(self.row_index) is not int or self.row_index < 0
        ):
            raise ValueError("row_index must be nonnegative or None.")


@dataclass(frozen=True, slots=True)
class FrequencyDomainRequestCreationResult:
    """All-or-nothing frequency request creation result."""

    request: FrequencyDomainWorkflowRequest | None
    errors: tuple[FrequencyDomainRequestFieldError, ...] = ()

    def __post_init__(self) -> None:
        if self.request is not None and (
            type(self.request) is not FrequencyDomainWorkflowRequest
        ):
            raise TypeError("request has an invalid type.")
        if type(self.errors) is not tuple or any(
            type(error) is not FrequencyDomainRequestFieldError
            for error in self.errors
        ):
            raise TypeError("errors have an invalid type.")
        if (self.request is None) == (not self.errors):
            raise ValueError("Exactly one of request or errors must be present.")

    @property
    def succeeded(self) -> bool:
        return self.request is not None


class FrequencyDomainRequestFactory:
    """Reuse transfer-function validation and parse exact frequency strings."""

    def __init__(
        self,
        limits: FrequencyDomainWorkflowLimits = _DEFAULT_LIMITS,
    ) -> None:
        if type(limits) is not FrequencyDomainWorkflowLimits:
            raise TypeError("limits must be FrequencyDomainWorkflowLimits.")
        self._limits = limits
        self._preparation_factory = TransferFunctionRequestFactory(
            limits.preparation
        )
        self._max_integer_digits = min(
            limits.frequency_response.max_frequency_integer_digits,
            limits.grid.max_rational_integer_digits,
        )

    @property
    def limits(self) -> FrequencyDomainWorkflowLimits:
        """Return the exact limits shared with created workflow requests."""

        return self._limits

    def create(
        self,
        draft: FrequencyDomainInputDraft,
    ) -> FrequencyDomainRequestCreationResult:
        if type(draft) is not FrequencyDomainInputDraft:
            raise TypeError("draft must be FrequencyDomainInputDraft.")
        errors: list[FrequencyDomainRequestFieldError] = []
        preparation = self._preparation_factory.create(draft.preparation)
        errors.extend(
            FrequencyDomainRequestFieldError(
                error.field,
                error.code,
                error.message,
                error.row_index,
            )
            for error in preparation.errors
        )
        if type(draft.mode) is not FrequencyDomainWorkflowMode:
            errors.append(_error("field", "invalid_mode", "Ungültiger Modus."))
        if type(draft.phase_presentation) is not FrequencyPhasePresentation:
            errors.append(
                _error(
                    "phase_presentation",
                    "invalid_phase_presentation",
                    "Ungültige Phasendarstellung.",
                )
            )

        single_frequency: ExactRationalValue | None = None
        grid_request: LogFrequencyGridRequest | None = None
        if draft.mode is FrequencyDomainWorkflowMode.SINGLE_POINT:
            single_frequency = self._rational(
                draft.single_angular_frequency_text,
                "single_angular_frequency",
                errors,
                nonnegative=True,
            )
            if (
                draft.phase_presentation
                is not FrequencyPhasePresentation.PRINCIPAL_ONLY
            ):
                errors.append(
                    _error(
                        "phase_presentation",
                        "unwrap_not_supported",
                        "Die Phasenentfaltung ist nur im Bode-Modus verfügbar.",
                    )
                )
        elif draft.mode is FrequencyDomainWorkflowMode.BODE:
            omega_min = self._rational(
                draft.omega_min_text,
                "omega_min",
                errors,
                positive=True,
            )
            omega_max = self._rational(
                draft.omega_max_text,
                "omega_max",
                errors,
                positive=True,
            )
            points_per_decade = self._positive_int(
                draft.points_per_decade_text,
                "points_per_decade",
                self._limits.grid.max_points_per_decade,
                errors,
            )
            explicit = self._explicit_frequencies(
                draft.explicit_frequencies_text,
                errors,
            )
            if (
                omega_min is not None
                and omega_max is not None
                and points_per_decade is not None
                and explicit is not None
            ):
                grid_request = LogFrequencyGridRequest(
                    omega_min,
                    omega_max,
                    points_per_decade,
                    explicit,
                )

        if errors:
            return FrequencyDomainRequestCreationResult(None, tuple(errors))
        assert preparation.request is not None
        return FrequencyDomainRequestCreationResult(
            FrequencyDomainWorkflowRequest(
                preparation.request,
                draft.mode,
                single_angular_frequency=single_frequency,
                grid_request=grid_request,
                phase_presentation=draft.phase_presentation,
                include_reserves=draft.mode is FrequencyDomainWorkflowMode.BODE,
            )
        )

    def _explicit_frequencies(
        self,
        text: str,
        errors: list[FrequencyDomainRequestFieldError],
    ) -> tuple[ExactRationalValue, ...] | None:
        if type(text) is not str:
            errors.append(
                _error(
                    "explicit_frequencies",
                    "invalid_type",
                    "Explizite Frequenzen müssen Text sein.",
                )
            )
            return None
        normalized = text.replace(";", ",").strip()
        if not normalized:
            return ()
        parts = tuple(part.strip() for part in normalized.split(","))
        if (
            any(not part for part in parts)
            or len(parts) > self._limits.grid.max_explicit_points
        ):
            errors.append(
                _error(
                    "explicit_frequencies",
                    "invalid_list",
                    "Explizite Frequenzen als kommagetrennte rationale Werte eingeben.",
                )
            )
            return None
        values: list[ExactRationalValue] = []
        for part in parts:
            value = self._rational(
                part,
                "explicit_frequencies",
                errors,
                positive=True,
            )
            if value is not None:
                values.append(value)
        return tuple(values) if len(values) == len(parts) else None

    def _rational(
        self,
        text: str,
        field: str,
        errors: list[FrequencyDomainRequestFieldError],
        *,
        positive: bool = False,
        nonnegative: bool = False,
    ) -> ExactRationalValue | None:
        if type(text) is not str:
            errors.append(_error(field, "invalid_type", "Ein Textwert ist erforderlich."))
            return None
        parts = text.strip().split("/")
        if len(parts) not in (1, 2):
            errors.append(_rational_error(field))
            return None
        numerator = self._bounded_int(parts[0])
        denominator = 1 if len(parts) == 1 else self._bounded_int(parts[1])
        if (
            numerator is None
            or denominator is None
            or denominator <= 0
            or (positive and numerator <= 0)
            or (nonnegative and numerator < 0)
        ):
            errors.append(_rational_error(field))
            return None
        divisor = gcd(abs(numerator), denominator)
        return ExactRationalValue(
            numerator // divisor,
            denominator // divisor,
        )

    def _positive_int(
        self,
        text: str,
        field: str,
        maximum: int,
        errors: list[FrequencyDomainRequestFieldError],
    ) -> int | None:
        value = self._bounded_int(text.strip()) if type(text) is str else None
        if value is None or value <= 0 or value > maximum:
            errors.append(
                _error(
                    field,
                    "invalid_positive_integer",
                    f"Eine ganze Zahl zwischen 1 und {maximum} ist erforderlich.",
                )
            )
            return None
        return value

    def _bounded_int(self, text: str) -> int | None:
        stripped = text.strip()
        digits = stripped[1:] if stripped.startswith(("+", "-")) else stripped
        if (
            not digits
            or not digits.isascii()
            or not digits.isdigit()
            or len(digits) > self._max_integer_digits
        ):
            return None
        return int(stripped)


def _error(
    field: str,
    code: str,
    message: str,
) -> FrequencyDomainRequestFieldError:
    return FrequencyDomainRequestFieldError(field, code, message)


def _rational_error(field: str) -> FrequencyDomainRequestFieldError:
    return _error(
        field,
        "invalid_rational",
        "Eine exakte rationale Zahl wie 3 oder 1/10 ist erforderlich.",
    )


__all__ = [
    "FrequencyDomainInputDraft",
    "FrequencyDomainRequestCreationResult",
    "FrequencyDomainRequestFactory",
    "FrequencyDomainRequestFieldError",
]
