"""Immutable configuration and result contracts for safe parsers."""

from dataclasses import dataclass
from keyword import iskeyword

from klausurbotpro.domain.diagnostics import Diagnostic, DiagnosticSeverity


@dataclass(frozen=True, slots=True)
class ParserLimits:
    """Central resource limits applied before symbolic processing."""

    max_input_length: int = 1_000
    max_ast_nodes: int = 256
    max_ast_depth: int = 32
    max_symbols: int = 16
    max_integer_digits: int = 128
    max_exponent_abs: int = 32
    max_estimated_terms: int = 2_048

    def __post_init__(self) -> None:
        for name in self.__dataclass_fields__:
            value = getattr(self, name)
            if value <= 0:
                raise ValueError(f"{name} must be greater than zero.")


@dataclass(frozen=True, slots=True)
class ParserConfig:
    """Allowed symbol names and resource limits for one parser."""

    allowed_symbols: frozenset[str]
    limits: ParserLimits = ParserLimits()

    def __post_init__(self) -> None:
        symbols = frozenset(self.allowed_symbols)
        if len(symbols) > self.limits.max_symbols:
            raise ValueError(
                "allowed_symbols exceeds limits.max_symbols."
            )
        for name in symbols:
            if (
                not name.isidentifier()
                or iskeyword(name)
                or name.startswith("__")
                or name.endswith("__")
            ):
                raise ValueError(f"Invalid allowed symbol name: {name!r}")
        object.__setattr__(self, "allowed_symbols", symbols)


@dataclass(frozen=True, slots=True)
class ParseResult[ValueT]:
    """Success or structured diagnostics for an expected parser outcome."""

    value: ValueT | None
    diagnostics: tuple[Diagnostic, ...] = ()

    def __post_init__(self) -> None:
        diagnostics = tuple(self.diagnostics)
        object.__setattr__(self, "diagnostics", diagnostics)
        has_error = any(
            diagnostic.severity is DiagnosticSeverity.ERROR
            for diagnostic in diagnostics
        )
        if self.value is None and not has_error:
            raise ValueError("A failed ParseResult requires an error diagnostic.")
        if self.value is not None and has_error:
            raise ValueError("A successful ParseResult cannot contain an error.")

    @property
    def succeeded(self) -> bool:
        """Return whether parsing produced a value without an error."""
        return self.value is not None
