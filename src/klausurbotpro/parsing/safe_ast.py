"""Shared validation rules for the safe mathematical AST language."""

import ast
from dataclasses import dataclass
from typing import NoReturn

from klausurbotpro.domain.diagnostics import DiagnosticCode
from klausurbotpro.parsing.contracts import ParserConfig

ALLOWED_NODE_TYPES = (
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
class SafeAstFailure(Exception):
    """Internal expected failure mapped to a public parser diagnostic."""

    code: DiagnosticCode
    message: str
    details: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True, slots=True)
class SafeAstInfo:
    """Resource and symbol facts collected during AST validation."""

    node_count: int
    depth: int
    used_symbols: frozenset[str]


def validate_safe_ast(
    tree: ast.Expression,
    config: ParserConfig,
) -> SafeAstInfo:
    """Validate one AST against the shared whitelist and resource policy."""
    limits = config.limits
    nodes = list(ast.walk(tree))
    depth = tree_depth(tree)
    if len(nodes) > limits.max_ast_nodes:
        fail_limit("max_ast_nodes")
    if depth > limits.max_ast_depth:
        fail_limit("max_ast_depth")

    used_symbols: set[str] = set()
    for node in nodes:
        if not isinstance(node, ALLOWED_NODE_TYPES):
            raise SafeAstFailure(
                DiagnosticCode.PARSE_FORBIDDEN_NODE,
                "Der Ausdruck enthält eine nicht erlaubte Sprachstruktur.",
                (("node", type(node).__name__),),
            )

        if isinstance(node, ast.Name):
            if node.id.startswith("__") or node.id.endswith("__"):
                raise SafeAstFailure(
                    DiagnosticCode.PARSE_FORBIDDEN_NODE,
                    "Dunder-Namen sind in mathematischen Ausdrücken verboten.",
                    (("symbol", node.id),),
                )
            if node.id not in config.allowed_symbols:
                raise SafeAstFailure(
                    DiagnosticCode.PARSE_UNKNOWN_SYMBOL,
                    f"Das Symbol '{node.id}' ist nicht freigegeben.",
                    (("symbol", node.id),),
                )
            used_symbols.add(node.id)

        if isinstance(node, ast.Constant):
            validate_constant(node)

        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow):
            exponent = evaluate_integer_expression(
                node.right,
                limits.max_exponent_abs,
            )
            if exponent is None:
                raise SafeAstFailure(
                    DiagnosticCode.PARSE_INVALID_EXPONENT,
                    "Exponenten müssen exakte ganze Zahlen sein.",
                )
            if abs(exponent) > limits.max_exponent_abs:
                fail_limit("max_exponent_abs")

    if len(used_symbols) > limits.max_symbols:
        fail_limit("max_symbols")

    estimated_terms = estimate_terms(
        tree.body,
        limits.max_estimated_terms,
        limits.max_exponent_abs,
    )
    if estimated_terms > limits.max_estimated_terms:
        fail_limit("max_estimated_terms")

    return SafeAstInfo(
        node_count=len(nodes),
        depth=depth,
        used_symbols=frozenset(used_symbols),
    )


def validate_constant(node: ast.Constant) -> None:
    """Accept only integer and decimal numeric AST constants."""
    if isinstance(node.value, bool) or node.value is None:
        raise SafeAstFailure(
            DiagnosticCode.PARSE_FORBIDDEN_NODE,
            "Nur ganze und exakte Dezimalzahlen sind als Literale erlaubt.",
            (("literal", repr(node.value)),),
        )
    if not isinstance(node.value, (int, float)):
        raise SafeAstFailure(
            DiagnosticCode.PARSE_FORBIDDEN_NODE,
            "Nur ganze und exakte Dezimalzahlen sind als Literale erlaubt.",
            (("literal_type", type(node.value).__name__),),
        )


def fail_limit(limit_name: str) -> NoReturn:
    """Raise a consistent parser resource-limit failure."""
    raise SafeAstFailure(
        DiagnosticCode.PARSE_LIMIT_EXCEEDED,
        "Der Ausdruck überschreitet eine konfigurierte Sicherheitsgrenze.",
        (("limit", limit_name),),
    )


def tree_depth(node: ast.AST) -> int:
    maximum = 0
    pending = [(node, 1)]
    while pending:
        current, depth = pending.pop()
        maximum = max(maximum, depth)
        pending.extend(
            (child, depth + 1) for child in ast.iter_child_nodes(current)
        )
    return maximum


def evaluate_integer_expression(node: ast.AST, cap: int) -> int | None:
    """Evaluate only the integer sublanguage used for exponent validation."""
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, int):
            return None
        return node.value if abs(node.value) <= cap else overflow_value(cap)

    if isinstance(node, ast.UnaryOp):
        value = evaluate_integer_expression(node.operand, cap)
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

    left = evaluate_integer_expression(node.left, cap)
    right = evaluate_integer_expression(node.right, cap)
    if left is None or right is None:
        return None
    if abs(left) > cap or abs(right) > cap:
        return overflow_value(cap)

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
            return overflow_value(cap)
        result = pow(left, right)
    else:
        return None

    return result if abs(result) <= cap else overflow_value(cap)


def overflow_value(cap: int) -> int:
    return cap + 1


def estimate_terms(node: ast.AST, cap: int, exponent_cap: int) -> int:
    """Conservatively estimate expansion size without expanding anything."""
    if isinstance(node, (ast.Constant, ast.Name)):
        return 1
    if isinstance(node, ast.UnaryOp):
        return estimate_terms(node.operand, cap, exponent_cap)
    if not isinstance(node, ast.BinOp):
        return cap + 1

    left = estimate_terms(node.left, cap, exponent_cap)
    right = estimate_terms(node.right, cap, exponent_cap)
    if isinstance(node.op, (ast.Add, ast.Sub)):
        return capped_add(left, right, cap)
    if isinstance(node.op, (ast.Mult, ast.Div)):
        return capped_multiply(left, right, cap)
    if isinstance(node.op, ast.Pow):
        exponent = evaluate_integer_expression(node.right, exponent_cap)
        if exponent is None or abs(exponent) > exponent_cap:
            return cap + 1
        return capped_power(left, abs(exponent), cap)
    return cap + 1


def capped_add(left: int, right: int, cap: int) -> int:
    result = left + right
    return result if result <= cap else cap + 1


def capped_multiply(left: int, right: int, cap: int) -> int:
    if left > cap or right > cap or (left and right > cap // left):
        return cap + 1
    return left * right


def capped_power(base: int, exponent: int, cap: int) -> int:
    result = 1
    for _ in range(exponent):
        result = capped_multiply(result, base, cap)
        if result > cap:
            return cap + 1
    return result


__all__ = [
    "SafeAstFailure",
    "SafeAstInfo",
    "evaluate_integer_expression",
    "fail_limit",
    "validate_safe_ast",
]
