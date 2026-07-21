"""Immutable configuration and result contracts for safe parsers."""

from dataclasses import dataclass
from enum import StrEnum
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


class ParserProfile(StrEnum):
    """Small, explicit languages used by mathematical input workflows."""

    IMAGE_S = "image_s"
    TIME_T = "time_t"


_DEFAULT_PARSER_LIMITS = ParserLimits()


@dataclass(frozen=True, slots=True)
class ParserConfig:
    """Allowed symbol names and resource limits for one parser."""

    allowed_symbols: frozenset[str]
    limits: ParserLimits = ParserLimits()
    allowed_functions: frozenset[str] = frozenset()
    exact_constants: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        symbols = frozenset(self.allowed_symbols)
        functions = frozenset(self.allowed_functions)
        constants = frozenset(self.exact_constants)
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
        if functions - {"exp", "sin", "cos"}:
            raise ValueError("Only exp, sin and cos may be enabled.")
        if constants - {"pi"}:
            raise ValueError("Only pi may be enabled as an exact constant.")
        if (functions | constants) & symbols:
            raise ValueError("Functions/constants cannot also be symbols.")
        object.__setattr__(self, "allowed_symbols", symbols)
        object.__setattr__(self, "allowed_functions", functions)
        object.__setattr__(self, "exact_constants", constants)

    @classmethod
    def for_profile(
        cls,
        profile: ParserProfile,
        *,
        parameter_names: frozenset[str] = frozenset(),
        limits: ParserLimits = _DEFAULT_PARSER_LIMITS,
    ) -> "ParserConfig":
        """Build one of the bounded time/image parser profiles."""
        if type(profile) is not ParserProfile:
            raise TypeError("profile must be a ParserProfile.")
        if {"s", "t", "pi", "exp", "sin", "cos"} & parameter_names:
            raise ValueError("A reserved profile name cannot be a parameter.")
        main = "s" if profile is ParserProfile.IMAGE_S else "t"
        return cls(
            allowed_symbols=frozenset((main, *parameter_names)),
            allowed_functions=(
                frozenset({"exp", "sin", "cos"})
                if profile is ParserProfile.TIME_T
                else frozenset()
            ),
            exact_constants=frozenset({"pi"}),
            limits=limits,
        )


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
