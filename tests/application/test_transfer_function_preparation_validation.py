"""Defensive revalidation tests for preparation results."""

from __future__ import annotations

from copy import copy

import pytest

from klausurbotpro.application import (
    TransferFunctionPreparationResult,
    TransferFunctionPreparationService,
    TransferFunctionPreparationStageStatus,
    TransferFunctionPreparationStatus,
    TransferFunctionWorkflowLimits,
    TransferFunctionWorkflowRequest,
    WorkflowInputForm,
)
from klausurbotpro.application._transfer_function_preparation_validation import (
    TransferFunctionPreparationFailure,
    validate_transfer_function_preparation_result,
)
from klausurbotpro.domain import (
    SeparatedTransferFunctionInput,
    TransferFunctionReductionLimits,
)


def _request(text: str = "1/(s+1)") -> TransferFunctionWorkflowRequest:
    return TransferFunctionWorkflowRequest(
        WorkflowInputForm.COMMON,
        common_expression_text=text,
    )


def _separated_request() -> TransferFunctionWorkflowRequest:
    return TransferFunctionWorkflowRequest(
        WorkflowInputForm.SEPARATED,
        numerator_expression_text="s+1",
        denominator_expression_text="s+2",
    )


def _result(
    text: str = "1/(s+1)",
) -> TransferFunctionPreparationResult:
    return TransferFunctionPreparationService().prepare(_request(text))


def _rich_result() -> TransferFunctionPreparationResult:
    request = TransferFunctionWorkflowRequest(
        WorkflowInputForm.COMMON,
        common_expression_text="(K/T*s+1)/(K*(s+2))",
        allowed_parameter_names=("K", "T"),
    )
    return TransferFunctionPreparationService().prepare(request)


def _validate(result: object) -> None:
    validate_transfer_function_preparation_result(
        result,  # type: ignore[arg-type]
        TransferFunctionWorkflowLimits(),
    )


def _assert_rejected(result: TransferFunctionPreparationResult) -> None:
    with pytest.raises(TransferFunctionPreparationFailure):
        _validate(result)


def _clone_controlled[T](value: T) -> T:
    clone = object.__new__(type(value))
    fields = type(value).__dataclass_fields__  # type: ignore[attr-defined]
    for name in fields:
        object.__setattr__(clone, name, getattr(value, name))
    return clone


def test_unmodified_complete_and_partial_results_revalidate() -> None:
    _validate(_result())
    _validate(_result("1/0"))


def test_wrong_top_level_result_type_raises_type_error() -> None:
    with pytest.raises(TypeError):
        _validate(object())


@pytest.mark.parametrize(
    ("attribute", "replacement"),
    [
        ("status", TransferFunctionPreparationStatus.PARTIAL),
        ("parsed_input", None),
        ("raw_result", None),
        ("reduction_result", None),
        ("diagnostics", (object(),)),
    ],
)
def test_manipulated_complete_result_is_rejected(
    attribute: str,
    replacement: object,
) -> None:
    result = _result()
    object.__setattr__(result, attribute, replacement)
    with pytest.raises(TransferFunctionPreparationFailure):
        _validate(result)


def test_manipulated_request_is_rejected() -> None:
    result = _result()
    object.__setattr__(
        result.request,
        "common_expression_text",
        "1/(s+2)",
    )
    with pytest.raises(TransferFunctionPreparationFailure):
        _validate(result)


@pytest.mark.parametrize(
    ("attribute", "replacement"),
    [
        ("original_text", " 1/(s+1) "),
        ("normalized_text", "1 / (s + 1)"),
        ("allowed_symbol_names", frozenset({"s", "T"})),
        ("variable_name", "z"),
    ],
)
def test_common_parser_provenance_fields_are_strict(
    attribute: str,
    replacement: object,
) -> None:
    result = _result()
    assert result.parsed_input is not None
    object.__setattr__(result.parsed_input, attribute, replacement)
    _assert_rejected(result)


def test_mathematically_equal_foreign_parser_value_is_rejected() -> None:
    result = _result()
    foreign = TransferFunctionPreparationService().prepare(
        _request("1 / (s + 1)")
    )
    object.__setattr__(result, "parsed_input", foreign.parsed_input)
    _assert_rejected(result)


def test_manipulated_parser_expression_tree_is_rejected() -> None:
    result = _result()
    foreign = _result("1/(1+s)")
    assert result.parsed_input is not None
    assert foreign.parsed_input is not None
    object.__setattr__(
        result.parsed_input,
        "expression",
        foreign.parsed_input.expression,  # type: ignore[union-attr]
    )
    _assert_rejected(result)


@pytest.mark.parametrize(
    "attribute",
    [
        "original_numerator_text",
        "original_denominator_text",
        "normalized_numerator_text",
        "normalized_denominator_text",
    ],
)
def test_separated_parser_text_provenance_is_strict(attribute: str) -> None:
    result = TransferFunctionPreparationService().prepare(
        _separated_request()
    )
    assert result.parsed_input is not None
    assert type(result.parsed_input) is SeparatedTransferFunctionInput
    replacement = (
        result.parsed_input.original_denominator_text
        if "numerator" in attribute
        else result.parsed_input.original_numerator_text
    )
    object.__setattr__(result.parsed_input, attribute, replacement)
    _assert_rejected(result)


def test_foreign_raw_and_reduction_results_are_rejected() -> None:
    first = _result("1/(s+1)")
    second = _result("1/(s+2)")
    object.__setattr__(first, "raw_result", second.raw_result)
    with pytest.raises(TransferFunctionPreparationFailure):
        _validate(first)

    first = _result("1/(s+1)")
    object.__setattr__(first, "reduction_result", second.reduction_result)
    with pytest.raises(TransferFunctionPreparationFailure):
        _validate(first)


def test_raw_input_snapshot_requires_direct_parsed_identity() -> None:
    result = _result()
    assert result.raw_value is not None
    cloned = copy(result.raw_value.input_snapshot)
    assert cloned == result.parsed_input
    object.__setattr__(result.raw_value, "input_snapshot", cloned)
    _assert_rejected(result)


@pytest.mark.parametrize(
    ("attribute", "replacement"),
    [
        ("used_parameter_names", frozenset()),
        ("is_zero", True),
        ("numerator_conditions", ()),
        ("denominator_conditions", ()),
    ],
)
def test_raw_derived_metadata_is_strict(
    attribute: str,
    replacement: object,
) -> None:
    result = _rich_result()
    assert result.raw_value is not None
    object.__setattr__(result.raw_value, attribute, replacement)
    _assert_rejected(result)


def test_raw_prerequisite_and_exclusion_origins_are_strict() -> None:
    result = _rich_result()
    assert result.raw_value is not None
    prerequisite = copy(result.raw_value.prerequisites[0])
    object.__setattr__(prerequisite, "origins", ("foreign",))
    object.__setattr__(
        result.raw_value,
        "prerequisites",
        (prerequisite, *result.raw_value.prerequisites[1:]),
    )
    _assert_rejected(result)

    result = _rich_result()
    assert result.raw_value is not None
    exclusion = copy(result.raw_value.domain_exclusions[0])
    object.__setattr__(exclusion, "origins", ("foreign",))
    object.__setattr__(
        result.raw_value,
        "domain_exclusions",
        (exclusion, *result.raw_value.domain_exclusions[1:]),
    )
    _assert_rejected(result)


def test_foreign_raw_diagnostic_is_rejected() -> None:
    result = _result("1/0")
    assert result.raw_result is not None
    foreign = copy(result.raw_result.diagnostics[0])
    object.__setattr__(foreign, "message", "Fremde Raw-Diagnose.")
    object.__setattr__(
        result.raw_result,
        "diagnostics",
        (foreign,),
    )
    _assert_rejected(result)


def test_mathematically_equal_raw_from_other_parser_context_is_rejected() -> None:
    result = _result()
    foreign_request = TransferFunctionWorkflowRequest(
        WorkflowInputForm.COMMON,
        common_expression_text="1/(s+1)",
        allowed_parameter_names=("T",),
    )
    foreign = TransferFunctionPreparationService().prepare(foreign_request)
    assert result.raw_value == foreign.raw_value
    object.__setattr__(result, "raw_result", foreign.raw_result)
    _assert_rejected(result)


@pytest.mark.parametrize(
    ("attribute", "replacement"),
    [
        ("used_parameter_names", frozenset()),
        ("is_zero", True),
    ],
)
def test_reduced_derived_metadata_is_strict(
    attribute: str,
    replacement: object,
) -> None:
    result = _rich_result()
    assert result.reduced_value is not None
    object.__setattr__(result.reduced_value, attribute, replacement)
    _assert_rejected(result)


def test_reduced_origins_are_strict() -> None:
    result = _rich_result()
    assert result.reduced_value is not None
    prerequisite = copy(result.reduced_value.prerequisites[0])
    object.__setattr__(prerequisite, "origins", ("foreign",))
    object.__setattr__(
        result.reduced_value,
        "prerequisites",
        (prerequisite, *result.reduced_value.prerequisites[1:]),
    )
    _assert_rejected(result)


def test_reduction_step_factor_order_and_report_are_strict() -> None:
    result = _rich_result()
    assert result.reduction_result is not None
    assert result.reduction_result.report is not None
    step = result.reduction_result.report.steps[0]
    object.__setattr__(step, "factor", None)
    _assert_rejected(result)

    result = _result("(-2*(s+1))/(4*(s+1)*(s+2))")
    assert result.reduction_result is not None
    assert result.reduction_result.report is not None
    steps = result.reduction_result.report.steps
    assert len(steps) >= 2
    object.__setattr__(
        result.reduction_result.report,
        "steps",
        tuple(reversed(steps)),
    )
    _assert_rejected(result)

    result = _rich_result()
    foreign = _result("(s+1)/(s+2)")
    assert result.reduction_result is not None
    assert foreign.reduction_result is not None
    object.__setattr__(
        result.reduction_result,
        "report",
        foreign.reduction_result.report,
    )
    _assert_rejected(result)


def test_reduction_requires_identical_raw_even_when_value_is_equal() -> None:
    result = _result()
    assert result.reduction_result is not None
    assert result.raw_value is not None
    cloned_raw = _clone_controlled(result.raw_value)
    assert cloned_raw == result.raw_value
    object.__setattr__(result.reduction_result, "raw", cloned_raw)
    _assert_rejected(result)


def test_foreign_mathematically_equal_reduced_value_is_rejected() -> None:
    result = _rich_result()
    assert result.reduced_value is not None
    foreign = _clone_controlled(result.reduced_value)
    exclusion = copy(foreign.domain_exclusions[0])
    object.__setattr__(exclusion, "origins", ("foreign",))
    object.__setattr__(
        foreign,
        "domain_exclusions",
        (exclusion, *foreign.domain_exclusions[1:]),
    )
    assert result.reduced_value == foreign
    assert result.reduction_result is not None
    object.__setattr__(
        result.reduction_result,
        "reduced",
        foreign,
    )
    _assert_rejected(result)


def test_manipulated_stage_order_and_status_are_rejected() -> None:
    result = _result()
    object.__setattr__(
        result,
        "stage_records",
        tuple(reversed(result.stage_records)),
    )
    with pytest.raises(TransferFunctionPreparationFailure):
        _validate(result)

    result = _result()
    object.__setattr__(
        result.stage_records[1],
        "status",
        TransferFunctionPreparationStageStatus.FAILED,
    )
    with pytest.raises(TransferFunctionPreparationFailure):
        _validate(result)


def test_result_after_blocked_stage_cannot_retain_values() -> None:
    result = _result("1/0")
    object.__setattr__(result, "reduction_result", _result().reduction_result)
    with pytest.raises(TransferFunctionPreparationFailure):
        _validate(result)


def test_validation_uses_explicit_limits() -> None:
    result = _result()
    with pytest.raises(TransferFunctionPreparationFailure):
        validate_transfer_function_preparation_result(
            result,
            TransferFunctionWorkflowLimits(
                reduction=TransferFunctionReductionLimits(max_input_terms=1)
            ),
        )
