"""Token-based normalization for the intentionally small input language."""

import re
import token
import tokenize
from dataclasses import dataclass
from io import StringIO
from keyword import iskeyword

from klausurbotpro.domain.diagnostics import (
    Diagnostic,
    DiagnosticCode,
    DiagnosticSeverity,
)
from klausurbotpro.parsing.contracts import ParseResult, ParserLimits

_INTEGER_PATTERN = re.compile(r"[0-9]+\Z")
_DECIMAL_PATTERN = re.compile(r"[0-9]+\.[0-9]+\Z")
_IGNORED_TOKEN_TYPES = {
    token.ENDMARKER,
    tokenize.ENCODING,
    tokenize.INDENT,
    tokenize.DEDENT,
    tokenize.NEWLINE,
    tokenize.NL,
}


@dataclass(frozen=True, slots=True)
class _NormalizedToken:
    type: int
    text: str
    start: tuple[int, int]
    end: tuple[int, int]


def normalize_expression(
    text: str,
    *,
    limits: ParserLimits,
    allowed_symbols: frozenset[str] = frozenset(),
    field: str | None = None,
) -> ParseResult[str]:
    """Normalize decimal commas and caret powers without evaluating input."""
    if len(text) > limits.max_input_length:
        return _failure(
            DiagnosticCode.PARSE_LIMIT_EXCEEDED,
            "Die Eingabe überschreitet die maximal erlaubte Länge.",
            field,
            (("limit", "max_input_length"),),
        )

    source = text.strip()
    if not source:
        return _failure(
            DiagnosticCode.PARSE_EMPTY_INPUT,
            "Bitte gib einen mathematischen Ausdruck ein.",
            field,
        )

    try:
        raw_tokens = list(tokenize.generate_tokens(StringIO(source).readline))
    except (IndentationError, tokenize.TokenError) as error:
        return _failure(
            DiagnosticCode.PARSE_INVALID_SYNTAX,
            "Der Ausdruck ist syntaktisch unvollständig oder ungültig.",
            field,
            (("exception", type(error).__name__),),
        )

    significant = [
        _NormalizedToken(item.type, item.string, item.start, item.end)
        for item in raw_tokens
        if item.type not in _IGNORED_TOKEN_TYPES
    ]

    output: list[tuple[int, str]] = []
    processed: list[_NormalizedToken] = []
    index = 0

    while index < len(significant):
        current = significant[index]

        if current.type == token.NUMBER:
            if not _is_supported_number(current.text):
                return _invalid_number(current.text, field)
            if _digit_count(current.text) > limits.max_integer_digits:
                return _failure(
                    DiagnosticCode.PARSE_LIMIT_EXCEEDED,
                    "Eine Zahl enthält zu viele Ziffern.",
                    field,
                    (("limit", "max_integer_digits"),),
                )

            if index + 1 < len(significant) and significant[index + 1].text == ",":
                comma = significant[index + 1]
                following = (
                    significant[index + 2]
                    if index + 2 < len(significant)
                    else None
                )
                if (
                    _INTEGER_PATTERN.fullmatch(current.text)
                    and following is not None
                    and following.type == token.NUMBER
                    and _INTEGER_PATTERN.fullmatch(following.text)
                    and current.end == comma.start
                    and comma.end == following.start
                ):
                    decimal = f"{current.text}.{following.text}"
                    if _digit_count(decimal) > limits.max_integer_digits:
                        return _failure(
                            DiagnosticCode.PARSE_LIMIT_EXCEEDED,
                            "Eine Zahl enthält zu viele Ziffern.",
                            field,
                            (("limit", "max_integer_digits"),),
                        )
                    merged = _NormalizedToken(
                        token.NUMBER,
                        decimal,
                        current.start,
                        following.end,
                    )
                    output.append((token.NUMBER, decimal))
                    processed.append(merged)
                    index += 3
                    continue

        if current.text == ",":
            return _invalid_number(current.text, field)

        if current.type == token.ERRORTOKEN and not current.text.isspace():
            return _failure(
                DiagnosticCode.PARSE_INVALID_SYNTAX,
                "Der Ausdruck enthält ein ungültiges Zeichen.",
                field,
                (("token", current.text),),
            )

        normalized_text = "**" if current.type == token.OP and current.text == "^" else current.text
        normalized = _NormalizedToken(
            current.type,
            normalized_text,
            current.start,
            current.end,
        )

        if processed and _is_implicit_multiplication(
            processed,
            normalized,
            allowed_symbols,
        ):
            return _failure(
                DiagnosticCode.PARSE_IMPLICIT_MULTIPLICATION,
                "Implizite Multiplikation ist nicht erlaubt; verwende '*'.",
                field,
            )

        output.append((current.type, normalized_text))
        processed.append(normalized)

        index += 1

    normalized_source = tokenize.untokenize(output).strip()
    return ParseResult(value=normalized_source)


def _is_supported_number(value: str) -> bool:
    return bool(
        _INTEGER_PATTERN.fullmatch(value) or _DECIMAL_PATTERN.fullmatch(value)
    )


def _digit_count(value: str) -> int:
    return sum(character.isdigit() for character in value)


def _is_implicit_multiplication(
    processed: list[_NormalizedToken],
    current: _NormalizedToken,
    allowed_symbols: frozenset[str],
) -> bool:
    previous = processed[-1]
    left_is_factor = (
        previous.type == token.NUMBER
        or (
            previous.type == token.NAME
            and previous.text in allowed_symbols
        )
        or (
            previous.text == ")"
            and _ends_with_math_group(processed, allowed_symbols)
        )
    )
    right_is_factor = (
        current.type == token.NUMBER
        or (
            current.type == token.NAME
            and not iskeyword(current.text)
        )
        or current.text == "("
    )
    return left_is_factor and right_is_factor


def _ends_with_math_group(
    processed: list[_NormalizedToken],
    allowed_symbols: frozenset[str],
) -> bool:
    depth = 0
    opening_index: int | None = None
    for index in range(len(processed) - 1, -1, -1):
        item = processed[index]
        if item.text == ")":
            depth += 1
        elif item.text == "(":
            depth -= 1
            if depth == 0:
                opening_index = index
                break

    if opening_index is None:
        return False

    contents = processed[opening_index + 1 : -1]
    if not contents:
        return False

    allowed_operators = {"+", "-", "*", "/", "**", "(", ")"}
    return all(
        item.type == token.NUMBER
        or (
            item.type == token.NAME
            and item.text in allowed_symbols
        )
        or (
            item.type == token.OP
            and item.text in allowed_operators
        )
        for item in contents
    )


def _invalid_number(value: str, field: str | None) -> ParseResult[str]:
    return _failure(
        DiagnosticCode.PARSE_INVALID_NUMBER,
        "Die Zahl verwendet ein ungültiges oder uneindeutiges Format.",
        field,
        (("token", value),),
    )


def _failure(
    code: DiagnosticCode,
    message: str,
    field: str | None,
    details: tuple[tuple[str, str], ...] = (),
) -> ParseResult[str]:
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
