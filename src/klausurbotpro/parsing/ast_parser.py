"""Whitelist-based AST parser with manual exact SymPy translation."""

import ast
import re
from typing import NoReturn

import sympy as sp

from klausurbotpro.domain.diagnostics import (
    Diagnostic,
    DiagnosticCode,
    DiagnosticSeverity,
)
from klausurbotpro.domain.expression import ExactExpression
from klausurbotpro.parsing.contracts import ParserConfig, ParseResult
from klausurbotpro.parsing.normalization import normalize_expression
from klausurbotpro.parsing.safe_ast import (
    SafeAstFailure,
    evaluate_integer_expression,
    fail_limit,
    validate_constant,
    validate_safe_ast,
)

_INTEGER_PATTERN = re.compile(r"[0-9]+\Z")
_DECIMAL_PATTERN = re.compile(r"[0-9]+\.[0-9]+\Z")
_RESOURCE_ERRORS = (MemoryError, RecursionError, OverflowError)
_ParseFailure = SafeAstFailure


class SafeExpressionParser:
    """Parse a deliberately small expression language without code execution."""

    def __init__(self, config: ParserConfig) -> None:
        self._config = config
        self._symbols = {
            name: sp.Symbol(name) for name in sorted(config.allowed_symbols)
        }
        self._constants: dict[str, sp.Expr] = {"pi": sp.pi}
        self._functions = {"exp": sp.exp, "sin": sp.sin, "cos": sp.cos}

    def parse(
        self,
        text: str,
        field: str | None = None,
    ) -> ParseResult[ExactExpression]:
        """Return an exact expression or deterministic structured diagnostics."""
        try:
            normalized = normalize_expression(
                text,
                limits=self._config.limits,
                allowed_symbols=self._config.allowed_symbols,
                field=field,
            )
        except _RESOURCE_ERRORS as error:
            return self._resource_failure_result(error, field)
        if not normalized.succeeded:
            return ParseResult(value=None, diagnostics=normalized.diagnostics)
        assert normalized.value is not None

        try:
            tree = ast.parse(normalized.value, mode="eval")
        except _RESOURCE_ERRORS as error:
            return self._resource_failure_result(error, field)
        except (SyntaxError, ValueError) as error:
            return self._failure_result(
                DiagnosticCode.PARSE_INVALID_SYNTAX,
                "Der Ausdruck ist syntaktisch ungültig.",
                field,
                (("exception", type(error).__name__),),
            )

        try:
            self._validate_tree(tree)
            expression = self._translate(tree.body, normalized.value)
            exact = ExactExpression._from_sympy(expression)
        except _RESOURCE_ERRORS as error:
            return self._resource_failure_result(error, field)
        except _ParseFailure as failure:
            return self._failure_result(
                failure.code,
                failure.message,
                field,
                failure.details,
            )
        except (ArithmeticError, TypeError, ValueError) as error:
            return self._failure_result(
                DiagnosticCode.PARSE_INVALID_SYNTAX,
                "Der Ausdruck konnte nicht sicher mathematisch erzeugt werden.",
                field,
                (("exception", type(error).__name__),),
            )

        return ParseResult(value=exact)

    def _validate_tree(self, tree: ast.Expression) -> None:
        validate_safe_ast(tree, self._config)

    def _validate_constant(self, node: ast.Constant) -> None:
        validate_constant(node)

    def _translate(self, node: ast.AST, source: str) -> sp.Expr:
        if isinstance(node, ast.Constant):
            token_text = ast.get_source_segment(source, node)
            if token_text is None:
                raise _ParseFailure(
                    DiagnosticCode.PARSE_INVALID_NUMBER,
                    "Das Zahlentoken konnte nicht eindeutig gelesen werden.",
                )
            if _INTEGER_PATTERN.fullmatch(token_text):
                if len(token_text) > self._config.limits.max_integer_digits:
                    self._fail_limit("max_integer_digits")
                return sp.Integer(token_text)
            if _DECIMAL_PATTERN.fullmatch(token_text):
                digits = token_text.replace(".", "")
                if len(digits) > self._config.limits.max_integer_digits:
                    self._fail_limit("max_integer_digits")
                return sp.Rational(token_text)
            raise _ParseFailure(
                DiagnosticCode.PARSE_INVALID_NUMBER,
                "Die Zahl verwendet ein nicht unterstütztes Format.",
                (("token", token_text),),
            )

        if isinstance(node, ast.Name):
            if node.id in self._config.exact_constants:
                return self._constants[node.id]
            return self._symbols[node.id]

        if isinstance(node, ast.Call):
            if (
                not isinstance(node.func, ast.Name)
                or node.func.id not in self._config.allowed_functions
                or len(node.args) != 1
                or node.keywords
            ):
                self._fail_forbidden(node)
            return self._functions[node.func.id](
                self._translate(node.args[0], source)
            )

        if isinstance(node, ast.UnaryOp):
            operand = self._translate(node.operand, source)
            if isinstance(node.op, ast.UAdd):
                return operand
            if isinstance(node.op, ast.USub):
                return -operand
            self._fail_forbidden(node.op)

        if isinstance(node, ast.BinOp):
            left = self._translate(node.left, source)
            right = self._translate(node.right, source)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Div):
                if right == 0:
                    raise _ParseFailure(
                        DiagnosticCode.MATH_DIVISION_BY_ZERO,
                        "Division durch null ist nicht definiert.",
                    )
                return left / right
            if isinstance(node.op, ast.Pow):
                exponent = evaluate_integer_expression(
                    node.right,
                    self._config.limits.max_exponent_abs,
                )
                if exponent is None:
                    raise _ParseFailure(
                        DiagnosticCode.PARSE_INVALID_EXPONENT,
                        "Exponenten müssen exakte ganze Zahlen sein.",
                    )
                if left == 0 and exponent < 0:
                    raise _ParseFailure(
                        DiagnosticCode.MATH_DIVISION_BY_ZERO,
                        "Eine negative Potenz von null ist nicht definiert.",
                    )
                return sp.Pow(left, exponent)
            self._fail_forbidden(node.op)

        self._fail_forbidden(node)

    def _fail_limit(self, limit_name: str) -> NoReturn:
        fail_limit(limit_name)

    def _fail_forbidden(self, node: ast.AST) -> NoReturn:
        raise _ParseFailure(
            DiagnosticCode.PARSE_FORBIDDEN_NODE,
            "Der Ausdruck enthält eine nicht erlaubte Sprachstruktur.",
            (("node", type(node).__name__),),
        )

    @staticmethod
    def _resource_failure_result(
        error: MemoryError | RecursionError | OverflowError,
        field: str | None,
    ) -> ParseResult[ExactExpression]:
        return SafeExpressionParser._failure_result(
            DiagnosticCode.PARSE_LIMIT_EXCEEDED,
            "Der Ausdruck überschreitet die verfügbaren Ressourcen.",
            field,
            (("exception", type(error).__name__),),
        )

    @staticmethod
    def _failure_result(
        code: DiagnosticCode,
        message: str,
        field: str | None,
        details: tuple[tuple[str, str], ...] = (),
    ) -> ParseResult[ExactExpression]:
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
