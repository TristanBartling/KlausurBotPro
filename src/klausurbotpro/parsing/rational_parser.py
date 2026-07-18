"""Safe parser for input-faithful rational-expression syntax trees."""

import ast
import re
from dataclasses import dataclass
from fractions import Fraction
from typing import NoReturn

from klausurbotpro.domain.diagnostics import (
    Diagnostic,
    DiagnosticCode,
    DiagnosticSeverity,
)
from klausurbotpro.domain.raw_algebraic_expression import (
    Add,
    Divide,
    ExactNumber,
    Multiply,
    Power,
    RawAlgebraicExpression,
    Subtract,
    Symbol,
    UnaryMinus,
    UnaryPlus,
)
from klausurbotpro.domain.transfer_function_input import (
    CommonTransferFunctionInput,
    SeparatedTransferFunctionInput,
    TransferFunctionInput,
)
from klausurbotpro.parsing.contracts import ParserConfig, ParseResult
from klausurbotpro.parsing.normalization import normalize_expression
from klausurbotpro.parsing.safe_ast import (
    SafeAstFailure,
    SafeAstInfo,
    validate_safe_ast,
)

_INTEGER_PATTERN = re.compile(r"[0-9]+\Z")
_DECIMAL_PATTERN = re.compile(r"[0-9]+\.[0-9]+\Z")
_RESOURCE_ERRORS = (MemoryError, RecursionError, OverflowError)


@dataclass(frozen=True, slots=True)
class _ParsedRawExpression:
    expression: RawAlgebraicExpression
    normalized_text: str
    ast_info: SafeAstInfo


class SafeRationalExpressionParser:
    """Parse rational input without evaluating or simplifying its structure."""

    def __init__(self, config: ParserConfig) -> None:
        if not isinstance(config, ParserConfig):
            raise TypeError("config must be a ParserConfig.")
        self._config = config

    def parse_pair(
        self,
        numerator_text: str,
        denominator_text: str,
        *,
        variable_name: str = "s",
        field: str | None = None,
    ) -> ParseResult[TransferFunctionInput]:
        """Parse separately entered numerator and denominator expressions."""
        self._require_text(numerator_text, "numerator_text")
        self._require_text(denominator_text, "denominator_text")
        self._require_variable_type(variable_name)
        self._require_field_type(field)

        variable_failure = self._validate_variable(variable_name, field)
        if variable_failure is not None:
            return variable_failure
        if not numerator_text.strip():
            return self._failure(
                DiagnosticCode.RATIONAL_INPUT_EMPTY_NUMERATOR,
                "Bitte gib einen Zählerausdruck ein.",
                field,
                (("part", "numerator"),),
            )
        if not denominator_text.strip():
            return self._failure(
                DiagnosticCode.RATIONAL_INPUT_EMPTY_DENOMINATOR,
                "Bitte gib einen Nennerausdruck ein.",
                field,
                (("part", "denominator"),),
            )
        numerator = self._parse_raw(
            numerator_text,
            self._part_field(field, "numerator"),
        )
        if not numerator.succeeded:
            return ParseResult(value=None, diagnostics=numerator.diagnostics)
        denominator = self._parse_raw(
            denominator_text,
            self._part_field(field, "denominator"),
        )
        if not denominator.succeeded:
            return ParseResult(value=None, diagnostics=denominator.diagnostics)
        assert numerator.value is not None
        assert denominator.value is not None

        if (
            len(numerator_text) + len(denominator_text)
            > self._config.limits.max_input_length
        ):
            return self._combined_limit_failure(
                "max_combined_input_length",
                field,
            )
        total_ast_nodes = (
            numerator.value.ast_info.node_count
            + denominator.value.ast_info.node_count
        )
        total_raw_nodes = (
            numerator.value.expression.node_count
            + denominator.value.expression.node_count
        )
        if total_ast_nodes > self._config.limits.max_ast_nodes:
            return self._combined_limit_failure("max_total_ast_nodes", field)
        if total_raw_nodes > self._config.limits.max_ast_nodes:
            return self._combined_limit_failure("max_total_raw_nodes", field)

        value = SeparatedTransferFunctionInput(
            numerator=numerator.value.expression,
            denominator=denominator.value.expression,
            variable_name=variable_name,
            allowed_symbol_names=self._config.allowed_symbols,
            original_numerator_text=numerator_text,
            original_denominator_text=denominator_text,
            normalized_numerator_text=numerator.value.normalized_text,
            normalized_denominator_text=denominator.value.normalized_text,
        )
        return ParseResult(value=value)

    def parse_common(
        self,
        text: str,
        *,
        variable_name: str = "s",
        field: str | None = None,
    ) -> ParseResult[TransferFunctionInput]:
        """Parse one complete expression and retain its top-level structure."""
        self._require_text(text, "text")
        self._require_variable_type(variable_name)
        self._require_field_type(field)

        variable_failure = self._validate_variable(variable_name, field)
        if variable_failure is not None:
            return variable_failure
        parsed = self._parse_raw(text, field)
        if not parsed.succeeded:
            return ParseResult(value=None, diagnostics=parsed.diagnostics)
        assert parsed.value is not None

        value = CommonTransferFunctionInput(
            expression=parsed.value.expression,
            variable_name=variable_name,
            allowed_symbol_names=self._config.allowed_symbols,
            original_text=text,
            normalized_text=parsed.value.normalized_text,
        )
        return ParseResult(value=value)

    def _parse_raw(
        self,
        text: str,
        field: str | None,
    ) -> ParseResult[_ParsedRawExpression]:
        try:
            normalized = normalize_expression(
                text,
                limits=self._config.limits,
                allowed_symbols=self._config.allowed_symbols,
                field=field,
            )
        except _RESOURCE_ERRORS as error:
            return self._resource_failure(error, field)
        if not normalized.succeeded:
            return ParseResult(value=None, diagnostics=normalized.diagnostics)
        assert normalized.value is not None

        try:
            tree = ast.parse(normalized.value, mode="eval")
            ast_info = validate_safe_ast(tree, self._config)
            expression = self._translate(tree.body, normalized.value)
        except _RESOURCE_ERRORS as error:
            return self._resource_failure(error, field)
        except SafeAstFailure as failure:
            return self._failure(
                failure.code,
                failure.message,
                field,
                failure.details,
            )
        except (SyntaxError, ValueError) as error:
            return self._failure(
                DiagnosticCode.PARSE_INVALID_SYNTAX,
                "Der Ausdruck ist syntaktisch ungültig.",
                field,
                (("exception", type(error).__name__),),
            )

        return ParseResult(
            value=_ParsedRawExpression(
                expression=expression,
                normalized_text=normalized.value,
                ast_info=ast_info,
            )
        )

    def _translate(
        self,
        node: ast.AST,
        source: str,
    ) -> RawAlgebraicExpression:
        if isinstance(node, ast.Constant):
            token_text = ast.get_source_segment(source, node)
            if token_text is None:
                raise SafeAstFailure(
                    DiagnosticCode.PARSE_INVALID_NUMBER,
                    "Das Zahlentoken konnte nicht eindeutig gelesen werden.",
                )
            if not (
                _INTEGER_PATTERN.fullmatch(token_text)
                or _DECIMAL_PATTERN.fullmatch(token_text)
            ):
                raise SafeAstFailure(
                    DiagnosticCode.PARSE_INVALID_NUMBER,
                    "Die Zahl verwendet ein nicht unterstütztes Format.",
                    (("token", token_text),),
                )
            value = Fraction(token_text)
            return ExactNumber(value.numerator, value.denominator)

        if isinstance(node, ast.Name):
            return Symbol(node.id)

        if isinstance(node, ast.UnaryOp):
            operand = self._translate(node.operand, source)
            if isinstance(node.op, ast.UAdd):
                return UnaryPlus(operand)
            if isinstance(node.op, ast.USub):
                return UnaryMinus(operand)
            self._fail_forbidden(node.op)

        if isinstance(node, ast.BinOp):
            left = self._translate(node.left, source)
            right = self._translate(node.right, source)
            if isinstance(node.op, ast.Add):
                return Add(left, right)
            if isinstance(node.op, ast.Sub):
                return Subtract(left, right)
            if isinstance(node.op, ast.Mult):
                return Multiply(left, right)
            if isinstance(node.op, ast.Div):
                return Divide(left, right)
            if isinstance(node.op, ast.Pow):
                return Power(left, right)
            self._fail_forbidden(node.op)

        self._fail_forbidden(node)

    def _validate_variable(
        self,
        variable_name: str,
        field: str | None,
    ) -> ParseResult[TransferFunctionInput] | None:
        if (
            not variable_name.isidentifier()
            or variable_name.startswith("__")
            or variable_name.endswith("__")
            or variable_name not in self._config.allowed_symbols
        ):
            return self._failure(
                DiagnosticCode.RATIONAL_INPUT_VARIABLE_NOT_ALLOWED,
                "Die Hauptvariable ist nicht als sicheres Symbol freigegeben.",
                field,
                (("variable", variable_name),),
            )
        return None

    @staticmethod
    def _require_text(value: object, parameter_name: str) -> None:
        if not isinstance(value, str):
            raise TypeError(f"{parameter_name} must be a str.")

    @staticmethod
    def _require_variable_type(variable_name: object) -> None:
        if not isinstance(variable_name, str):
            raise TypeError("variable_name must be a str.")

    @staticmethod
    def _require_field_type(field: object) -> None:
        if field is not None and not isinstance(field, str):
            raise TypeError("field must be a str or None.")

    @staticmethod
    def _part_field(field: str | None, part: str) -> str:
        return f"{field}.{part}" if field else part

    @staticmethod
    def _fail_forbidden(node: ast.AST) -> NoReturn:
        raise SafeAstFailure(
            DiagnosticCode.PARSE_FORBIDDEN_NODE,
            "Der Ausdruck enthält eine nicht erlaubte Sprachstruktur.",
            (("node", type(node).__name__),),
        )

    @staticmethod
    def _combined_limit_failure(
        limit_name: str,
        field: str | None,
    ) -> ParseResult[TransferFunctionInput]:
        return SafeRationalExpressionParser._failure(
            DiagnosticCode.RATIONAL_INPUT_LIMIT_EXCEEDED,
            "Die Gesamteingabe überschreitet eine Sicherheitsgrenze.",
            field,
            (("limit", limit_name),),
        )

    @staticmethod
    def _resource_failure(
        error: MemoryError | RecursionError | OverflowError,
        field: str | None,
    ) -> ParseResult[_ParsedRawExpression]:
        return SafeRationalExpressionParser._failure(
            DiagnosticCode.PARSE_LIMIT_EXCEEDED,
            "Der Ausdruck überschreitet die verfügbaren Ressourcen.",
            field,
            (("exception", type(error).__name__),),
        )

    @staticmethod
    def _failure[ValueT](
        code: DiagnosticCode,
        message: str,
        field: str | None,
        details: tuple[tuple[str, str], ...] = (),
    ) -> ParseResult[ValueT]:
        return ParseResult(
            value=None,
            diagnostics=(
                Diagnostic(
                    severity=DiagnosticSeverity.ERROR,
                    code=code,
                    message=message,
                    field=field,
                    technical_details=details,
                ),
            ),
        )


__all__ = ["SafeRationalExpressionParser"]
