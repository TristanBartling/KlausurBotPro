"""Validation helpers for workflow requests, substitutions, and overrides."""

from __future__ import annotations

from keyword import iskeyword

from klausurbotpro.application.transfer_function_workflow_contracts import (
    OverrideProvenance,
    TransferFunctionWorkflowLimits,
    TransferFunctionWorkflowRequest,
    WorkflowInputForm,
    WorkflowOverrideOriginKind,
    WorkflowStage,
)
from klausurbotpro.domain import ParameterSubstitutions


def validate_request(
    request: TransferFunctionWorkflowRequest,
    limits: TransferFunctionWorkflowLimits,
) -> tuple[tuple[str, str], ...]:
    errors: list[tuple[str, str]] = []
    if type(request) is not TransferFunctionWorkflowRequest:
        return (("request", "invalid_type"),)
    if type(request.input_form) is not WorkflowInputForm:
        errors.append(("input_form", "invalid"))
    if not _safe_name(request.variable_name):
        errors.append(("variable_name", "invalid"))
    if request.field is not None and not isinstance(request.field, str):
        errors.append(("field", "invalid"))
    names = request.allowed_parameter_names
    if not isinstance(names, tuple) or any(
        not isinstance(name, str) for name in names
    ):
        errors.append(("allowed_parameter_names", "invalid_type"))
    else:
        if names != tuple(sorted(set(names))):
            errors.append(("allowed_parameter_names", "not_sorted_unique"))
        if any(not _safe_name(name) for name in names):
            errors.append(("allowed_parameter_names", "unsafe_identifier"))
        if request.variable_name in names:
            errors.append(("allowed_parameter_names", "contains_variable"))
        if len(names) > limits.parser.max_symbols - 1:
            errors.append(("allowed_parameter_names", "parser_limit"))
        if len(names) > limits.raw.max_parameters:
            errors.append(("allowed_parameter_names", "raw_limit"))

    common_set = request.common_expression_text is not None
    numerator_set = request.numerator_expression_text is not None
    denominator_set = request.denominator_expression_text is not None
    if request.input_form is WorkflowInputForm.COMMON:
        if not common_set or numerator_set or denominator_set:
            errors.append(("input_form", "common_fields_mismatch"))
    elif (
        request.input_form is WorkflowInputForm.SEPARATED
        and (common_set or not numerator_set or not denominator_set)
    ):
        errors.append(("input_form", "separated_fields_mismatch"))
    for name, value in (
        ("common_expression_text", request.common_expression_text),
        ("numerator_expression_text", request.numerator_expression_text),
        ("denominator_expression_text", request.denominator_expression_text),
    ):
        if value is not None and not isinstance(value, str):
            errors.append((name, "invalid_type"))
    if request.substitutions is not None and (
        type(request.substitutions) is not ParameterSubstitutions
    ):
        errors.append(("substitutions", "invalid_type"))
    return tuple(errors)


def validate_provenance(
    provenance: OverrideProvenance,
    *,
    expected_stage: WorkflowStage,
    expected_sequence: int,
    limits: TransferFunctionWorkflowLimits,
) -> tuple[tuple[str, str], ...]:
    errors: list[tuple[str, str]] = []
    if type(provenance) is not OverrideProvenance:
        return (("provenance", "invalid_type"),)
    if provenance.target_stage is not expected_stage:
        errors.append(("target_stage", "mismatch"))
    if type(provenance.origin_kind) is not WorkflowOverrideOriginKind:
        errors.append(("origin_kind", "invalid"))
    if (
        isinstance(provenance.sequence_number, bool)
        or provenance.sequence_number != expected_sequence
    ):
        errors.append(("sequence_number", "mismatch"))
    if not isinstance(provenance.reason, str) or not provenance.reason.strip():
        errors.append(("reason", "empty_or_invalid"))
    elif len(provenance.reason) > limits.max_override_reason_length:
        errors.append(("reason", "max_override_reason_length"))
    return tuple(errors)


def next_sequence(
    current: int,
    limits: TransferFunctionWorkflowLimits,
) -> int | None:
    value = current + 1
    return value if value <= limits.max_operation_sequence else None


def _safe_name(value: object) -> bool:
    return (
        isinstance(value, str)
        and value.isidentifier()
        and not iskeyword(value)
        and not value.startswith("__")
        and not value.endswith("__")
    )


__all__ = ["next_sequence", "validate_provenance", "validate_request"]
