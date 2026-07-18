"""Whitelist-based AST parser with manual exact SymPy translation."""

import ast
import re
from dataclasses import dataclass
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

_INTEGER_PATTERN = re.compile(r"[0-9]+\Z")
_DECIMAL_PATTERN = re.compile(r"[0-9]+\.[0-9]+\Z")
_ALLOWED_NODE_TYPES = (
    ast.Expression,
    ast.Constant,
    ast.Name,
    ast.BinOp,
    ast.UnaryOp,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Pow,
    ast.UAdd,
    ast.USub,
    ast.Load,
)


@dataclass(frozen=True, slots=True)
class _ParseFailure(Exception):
    code: DiagnosticCode
    message: str
    details: tuple[tuple[str, str], ...] = ()


class SafeExpressionParser:
    """Parse a deliberately small expression language without code execution."""

    def __init__(self, config: ParserConfig) -> None:
        self._config = config
        self._symbols = {
            name: sp.Symbol(name) for name in sorted(config.allowed_symbols)
        }

    def parse(
        self,
        text: str,
        field: str | None = None,
    ) -> ParseResult[ExactExpression]:
        """Return an exact expression or deterministic structured diagnostics."""
        normalized = normalize_expression(
            text,
            limits=self._config.limits,
            field=field,
        )
        if not normalized.succeeded:
            return ParseResult(value=None, diagnostics=normalized.diagnostics)
        assert normalized.value is not None

        try:
            tree = ast.parse(normalized.value, mode="eval")
        except (SyntaxError, ValueError, MemoryError, RecursionError) as error:
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
        limits = self._config.limits
        nodes = list(ast.walk(tree))
        if len(nodes) > limits.max_ast_nodes:
            self._fail_limit("max_ast_nodes")
        if _tree_depth(tree) > limits.max_ast_depth:
            self._fail_limit("max_ast_depth")

        used_symbols: set[str] = set()
        for node in nodes:
            if not isinstance(node, _ALLOWED_NODE_TYPES):
                raise _ParseFailure(
                    DiagnosticCode.PARSE_FORBIDDEN_NODE,
                    "Der Ausdruck enthält eine nicht erlaubte Sprachstruktur.",
                    (("node", type(node).__name__),),
                )

            if isinstance(node, ast.Name):
                if node.id.startswith("__") or node.id.endswith("__"):
                    raise _ParseFailure(
                        DiagnosticCode.PARSE_FORBIDDEN_NODE,
                        "Dunder-Namen sind in mathematischen Ausdrücken verboten.",
                        (("symbol", node.id),),
                    )
                if node.id not in self._config.allowed_symbols:
                    raise _ParseFailure(
                        DiagnosticCode.PARSE_UNKNOWN_SYMBOL,
                        f"Das Symbol '{node.id}' ist nicht freigegeben.",
                        (("symbol", node.id),),
                    )
                used_symbols.add(node.id)

            if isinstance(node, ast.Constant):
                self._validate_constant(node)

            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow):
                exponent = _evaluate_integer_expression(
                    node.right,
                    limits.max_exponent_abs,
                )
                if exponent is None:
                    raise _ParseFailure(
                        DiagnosticCode.PARSE_INVALID_EXPONENT,
                        "Exponenten müssen exakte ganze Zahlen sein.",
                    )
                if abs(exponent) > limits.max_exponent_abs:
                    self._fail_limit("max_exponent_abs")

        if len(used_symbols) > limits.max_symbols:
            self._fail_limit("max_symbols")

        estimated_terms = _estimate_terms(
            tree.body,
            limits.max_estimated_terms,
            limits.max_exponent_abs,
        )
        if estimated_terms > limits.max_estimated_terms:
            self._fail_limit("max_estimated_terms")

    def _validate_constant(self, node: ast.Constant) -> None:
        if isinstance(node.value, bool) or node.value is None:
            raise _ParseFailure(
                DiagnosticCode.PARSE_FORBIDDEN_NODE,
                "Nur ganze und exakte Dezimalzahlen sind als Literale erlaubt.",
                (("literal", repr(node.value)),),
            )
        if not isinstance(node.value, (int, float)):
            raise _ParseFailure(
                DiagnosticCode.PARSE_FORBIDDEN_NODE,
                "Nur ganze und exakte Dezimalzahlen sind als Literale erlaubt.",
                (("literal_type", type(node.value).__name__),),
            )

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
            return self._symbols[node.id]

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
                exponent = _evaluate_integer_expression(
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
        raise _ParseFailure(
            DiagnosticCode.PARSE_LIMIT_EXCEEDED,
            "Der Ausdruck überschreitet eine konfigurierte Sicherheitsgrenze.",
            (("limit", limit_name),),
        )

    def _fail_forbidden(self, node: ast.AST) -> NoReturn:
        raise _ParseFailure(
            DiagnosticCode.PARSE_FORBIDDEN_NODE,
            "Der Ausdruck enthält eine nicht erlaubte Sprachstruktur.",
            (("node", type(node).__name__),),
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


def _tree_depth(node: ast.AST) -> int:
    maximum = 0
    pending = [(node, 1)]
    while pending:
        current, depth = pending.pop()
        maximum = max(maximum, depth)
        pending.extend(
            (child, depth + 1) for child in ast.iter_child_nodes(current)
        )
    return maximum


def _evaluate_integer_expression(node: ast.AST, cap: int) -> int | None:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, int):
            return None
        return node.value if abs(node.value) <= cap else _overflow_value(cap)

    if isinstance(node, ast.UnaryOp):
        value = _evaluate_integer_expression(node.operand, cap)
        if value is None:
            return None
        if abs(value) > cap:
            return value
        if isinstance(node.op, ast.UAdd):
            return value
        if isinstance(node.op, ast.USub):
            return -value
        return None

    if not isinstance(node, ast.BinOp):
        return None

    left = _evaluate_integer_expression(node.left, cap)
    right = _evaluate_integer_expression(node.right, cap)
    if left is None or right is None:
        return None
    if abs(left) > cap or abs(right) > cap:
        return _overflow_value(cap)

    if isinstance(node.op, ast.Add):
        result = left + right
    elif isinstance(node.op, ast.Sub):
        result = left - right
    elif isinstance(node.op, ast.Mult):
        result = left * right
    elif isinstance(node.op, ast.Div):
        if right == 0 or left % right != 0:
            return None
        result = left // right
    elif isinstance(node.op, ast.Pow):
        if right < 0:
            return None
        if abs(left) > 1 and right > cap:
            return _overflow_value(cap)
        result = pow(left, right)
    else:
        return None

    return result if abs(result) <= cap else _overflow_value(cap)


def _overflow_value(cap: int) -> int:
    return cap + 1


def _estimate_terms(node: ast.AST, cap: int, exponent_cap: int) -> int:
    if isinstance(node, (ast.Constant, ast.Name)):
        return 1
    if isinstance(node, ast.UnaryOp):
        return _estimate_terms(node.operand, cap, exponent_cap)
    if not isinstance(node, ast.BinOp):
        return cap + 1

    left = _estimate_terms(node.left, cap, exponent_cap)
    right = _estimate_terms(node.right, cap, exponent_cap)
    if isinstance(node.op, (ast.Add, ast.Sub)):
        return _capped_add(left, right, cap)
    if isinstance(node.op, (ast.Mult, ast.Div)):
        return _capped_multiply(left, right, cap)
    if isinstance(node.op, ast.Pow):
        exponent = _evaluate_integer_expression(node.right, exponent_cap)
        if exponent is None or abs(exponent) > exponent_cap:
            return cap + 1
        return _capped_power(left, abs(exponent), cap)
    return cap + 1


def _capped_add(left: int, right: int, cap: int) -> int:
    result = left + right
    return result if result <= cap else cap + 1


def _capped_multiply(left: int, right: int, cap: int) -> int:
    if left > cap or right > cap or (left and right > cap // left):
        return cap + 1
    return left * right


def _capped_power(base: int, exponent: int, cap: int) -> int:
    result = 1
    for _ in range(exponent):
        result = _capped_multiply(result, base, cap)
        if result > cap:
            return cap + 1
    return result
