"""Input-faithful contracts for separated and common rational expressions."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import StrEnum
from keyword import iskeyword

from klausurbotpro.domain.raw_algebraic_expression import (
    RawAlgebraicExpression,
)


class TransferFunctionInputForm(StrEnum):
    """Supported syntactic input forms."""

    SEPARATED = "separated"
    COMMON = "common"


class _TransferFunctionInputValue:
    __slots__ = ()

    @property
    def _structural_identity(self) -> str:
        raise NotImplementedError

    def __eq__(self, other: object) -> bool:
        return (
            type(self) is type(other)
            and isinstance(other, _TransferFunctionInputValue)
            and self._structural_identity == other._structural_identity
        )

    def __hash__(self) -> int:
        digest = hashlib.sha256(
            self._structural_identity.encode("utf-8")
        ).digest()
        return int.from_bytes(digest[:8], byteorder="big", signed=True)


@dataclass(frozen=True, slots=True, eq=False)
class SeparatedTransferFunctionInput(_TransferFunctionInputValue):
    """A numerator and denominator entered in distinct input fields."""

    numerator: RawAlgebraicExpression
    denominator: RawAlgebraicExpression
    variable_name: str
    allowed_symbol_names: frozenset[str]
    original_numerator_text: str = field(compare=False, hash=False)
    original_denominator_text: str = field(compare=False, hash=False)
    normalized_numerator_text: str = field(compare=False, hash=False)
    normalized_denominator_text: str = field(compare=False, hash=False)

    def __post_init__(self) -> None:
        _validate_common_fields(
            self.numerator,
            self.variable_name,
            self.allowed_symbol_names,
        )
        _require_expression(self.denominator, "denominator")
        _require_declared_symbols(
            self.denominator,
            self.allowed_symbol_names,
        )
        _require_texts(
            self.original_numerator_text,
            self.original_denominator_text,
            self.normalized_numerator_text,
            self.normalized_denominator_text,
        )
        object.__setattr__(
            self,
            "allowed_symbol_names",
            frozenset(self.allowed_symbol_names),
        )

    @property
    def input_form(self) -> TransferFunctionInputForm:
        return TransferFunctionInputForm.SEPARATED

    @property
    def used_symbol_names(self) -> frozenset[str]:
        return self.numerator.symbol_names | self.denominator.symbol_names

    @property
    def total_node_count(self) -> int:
        return self.numerator.node_count + self.denominator.node_count

    @property
    def _structural_identity(self) -> str:
        allowed = ",".join(sorted(self.allowed_symbol_names))
        return (
            f"{self.input_form.value}|{self.variable_name}|{allowed}|"
            f"{self.numerator.canonical_tree}|"
            f"{self.denominator.canonical_tree}"
        )


@dataclass(frozen=True, slots=True, eq=False)
class CommonTransferFunctionInput(_TransferFunctionInputValue):
    """One complete rational expression retained as a single tree."""

    expression: RawAlgebraicExpression
    variable_name: str
    allowed_symbol_names: frozenset[str]
    original_text: str = field(compare=False, hash=False)
    normalized_text: str = field(compare=False, hash=False)

    def __post_init__(self) -> None:
        _validate_common_fields(
            self.expression,
            self.variable_name,
            self.allowed_symbol_names,
        )
        _require_texts(self.original_text, self.normalized_text)
        object.__setattr__(
            self,
            "allowed_symbol_names",
            frozenset(self.allowed_symbol_names),
        )

    @property
    def input_form(self) -> TransferFunctionInputForm:
        return TransferFunctionInputForm.COMMON

    @property
    def used_symbol_names(self) -> frozenset[str]:
        return self.expression.symbol_names

    @property
    def total_node_count(self) -> int:
        return self.expression.node_count

    @property
    def _structural_identity(self) -> str:
        allowed = ",".join(sorted(self.allowed_symbol_names))
        return (
            f"{self.input_form.value}|{self.variable_name}|{allowed}|"
            f"{self.expression.canonical_tree}"
        )


type TransferFunctionInput = (
    SeparatedTransferFunctionInput | CommonTransferFunctionInput
)


def _validate_common_fields(
    expression: RawAlgebraicExpression,
    variable_name: str,
    allowed_symbol_names: frozenset[str],
) -> None:
    _require_expression(expression, "expression")
    if not isinstance(variable_name, str):
        raise TypeError("variable_name must be a str.")
    if not isinstance(allowed_symbol_names, frozenset):
        raise TypeError("allowed_symbol_names must be a frozenset.")
    if (
        not variable_name.isidentifier()
        or iskeyword(variable_name)
        or variable_name.startswith("__")
        or variable_name.endswith("__")
    ):
        raise ValueError("variable_name must be a safe identifier.")
    if variable_name not in allowed_symbol_names:
        raise ValueError("variable_name must be an allowed symbol.")
    for name in allowed_symbol_names:
        if not isinstance(name, str):
            raise TypeError("allowed_symbol_names must contain only strings.")
        if (
            not name.isidentifier()
            or iskeyword(name)
            or name.startswith("__")
            or name.endswith("__")
        ):
            raise ValueError(f"Invalid allowed symbol name: {name!r}")
    _require_declared_symbols(expression, allowed_symbol_names)


def _require_declared_symbols(
    expression: RawAlgebraicExpression,
    allowed_symbol_names: frozenset[str],
) -> None:
    undeclared = expression.symbol_names - allowed_symbol_names
    if undeclared:
        names = ", ".join(sorted(undeclared))
        raise ValueError(f"Expression contains undeclared symbols: {names}.")


def _require_expression(
    value: RawAlgebraicExpression,
    field_name: str,
) -> None:
    if not isinstance(value, RawAlgebraicExpression):
        raise TypeError(f"{field_name} must be a RawAlgebraicExpression.")


def _require_texts(*values: str) -> None:
    if any(not isinstance(value, str) for value in values):
        raise TypeError("Source texts must be strings.")


__all__ = [
    "CommonTransferFunctionInput",
    "SeparatedTransferFunctionInput",
    "TransferFunctionInput",
    "TransferFunctionInputForm",
]
