"""Shared constructors for the three transfer-function preparation steps."""

from __future__ import annotations

from klausurbotpro.application.transfer_function_workflow_contracts import (
    TransferFunctionWorkflowLimits,
    TransferFunctionWorkflowRequest,
    WorkflowInputForm,
)
from klausurbotpro.domain import (
    RawTransferFunctionFactory,
    TransferFunctionInput,
)
from klausurbotpro.parsing import (
    ParserConfig,
    ParseResult,
    SafeRationalExpressionParser,
)


def parser_for(
    request: TransferFunctionWorkflowRequest,
    limits: TransferFunctionWorkflowLimits,
) -> SafeRationalExpressionParser:
    return SafeRationalExpressionParser(
        ParserConfig(
            frozenset(
                (*request.allowed_parameter_names, request.variable_name)
            ),
            limits.parser,
        )
    )


def parse_request(
    request: TransferFunctionWorkflowRequest,
    limits: TransferFunctionWorkflowLimits,
) -> ParseResult[TransferFunctionInput]:
    parser = parser_for(request, limits)
    if request.input_form is WorkflowInputForm.COMMON:
        assert request.common_expression_text is not None
        return parser.parse_common(
            request.common_expression_text,
            variable_name=request.variable_name,
            field=request.field,
        )
    assert request.numerator_expression_text is not None
    assert request.denominator_expression_text is not None
    return parser.parse_pair(
        request.numerator_expression_text,
        request.denominator_expression_text,
        variable_name=request.variable_name,
        field=request.field,
    )


def raw_factory_for(
    request: TransferFunctionWorkflowRequest,
    limits: TransferFunctionWorkflowLimits,
) -> RawTransferFunctionFactory:
    return RawTransferFunctionFactory(
        expected_variable_name=request.variable_name,
        allowed_parameter_names=frozenset(request.allowed_parameter_names),
        limits=limits.raw,
    )


__all__ = ["parse_request", "parser_for", "raw_factory_for"]
