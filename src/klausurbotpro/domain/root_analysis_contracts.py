"""Public, SymPy-free contracts for exact transfer-function root analysis."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from math import gcd

from klausurbotpro.domain.diagnostics import Diagnostic, DiagnosticSeverity
from klausurbotpro.domain.expression import ExactExpression
from klausurbotpro.domain.parameter_substitutions import (
    ParameterSubstitutions,
)
from klausurbotpro.domain.reduced_transfer_function import (
    ReducedTransferFunction,
)


class PolynomialRootStatus(StrEnum):
    """Outcome of analyzing one exact polynomial."""

    COMPLETE = "complete"
    CONSTANT_NONZERO = "constant_nonzero"
    ZERO_POLYNOMIAL = "zero_polynomial"
    SYMBOLIC_UNDETERMINED = "symbolic_undetermined"
    NOT_EVALUATED = "not_evaluated"


class RootSource(StrEnum):
    """Mathematical role of a reported root."""

    NUMERATOR = "numerator"
    DENOMINATOR = "denominator"
    DOMAIN_EXCLUSION = "domain_exclusion"
    CANCELLED_FACTOR = "cancelled_factor"


class ConjugateStatus(StrEnum):
    """Result of the numerical conjugate-pair consistency check."""

    REAL = "real"
    CONFIRMED = "confirmed"
    MISSING = "missing"


class NumericalRootWarning(StrEnum):
    """Structured numerical caveat attached to a root estimate."""

    MULTIPLE_ROOT = "multiple_root"
    CLOSE_CLUSTER = "close_cluster"
    RESIDUAL_TOO_LARGE = "residual_too_large"
    CONJUGATE_MISMATCH = "conjugate_mismatch"


@dataclass(frozen=True, slots=True)
class ExplicitExactRootValue:
    """An exact explicit root such as ``-1`` or ``I``."""

    expression: ExactExpression

    def __post_init__(self) -> None:
        if type(self.expression) is not ExactExpression:
            raise TypeError("An explicit root must be an ExactExpression.")
        if self.expression.symbol_names:
            raise ValueError("An explicit exact root must be parameter-free.")


@dataclass(frozen=True, slots=True)
class RootOfValue:
    """A canonical algebraic root defined by a primitive integer polynomial."""

    defining_coefficients: tuple[int, ...]
    root_index: int

    def __post_init__(self) -> None:
        coefficients = tuple(self.defining_coefficients)
        if (
            len(coefficients) < 2
            or any(isinstance(value, bool) or not isinstance(value, int) for value in coefficients)
            or coefficients[0] <= 0
        ):
            raise ValueError(
                "RootOf coefficients must define a positive-leading primitive polynomial."
            )
        if not isinstance(self.root_index, int) or isinstance(self.root_index, bool):
            raise TypeError("A RootOf index must be an integer.")
        if not 0 <= self.root_index < len(coefficients) - 1:
            raise ValueError("A RootOf index must address a root of its polynomial.")
        common = 0
        for coefficient in coefficients:
            common = gcd(common, abs(coefficient))
        if common != 1:
            raise ValueError("A RootOf defining polynomial must be primitive.")
        object.__setattr__(self, "defining_coefficients", coefficients)


type ExactRootValue = ExplicitExactRootValue | RootOfValue


@dataclass(frozen=True, slots=True)
class RootOccurrence:
    """One distinct exact root and its algebraic multiplicity."""

    value: ExactRootValue
    multiplicity: int
    source: RootSource
    index: int

    def __post_init__(self) -> None:
        if type(self.value) not in (ExplicitExactRootValue, RootOfValue):
            raise TypeError("A root occurrence requires a supported exact root value.")
        if (
            isinstance(self.multiplicity, bool)
            or not isinstance(self.multiplicity, int)
            or self.multiplicity <= 0
        ):
            raise ValueError("A root multiplicity must be a positive integer.")
        if type(self.source) is not RootSource:
            raise TypeError("A root source must be a RootSource.")
        if isinstance(self.index, bool) or not isinstance(self.index, int) or self.index < 0:
            raise ValueError("A root index must be a non-negative integer.")


@dataclass(frozen=True, slots=True, eq=False)
class NumericalRootEstimate:
    """A non-hashable numerical check belonging to one exact root occurrence."""

    root_index: int
    real: str
    imaginary: str
    precision_digits: int
    absolute_residual: str
    scaled_residual: str
    conjugate_status: ConjugateStatus
    warnings: tuple[NumericalRootWarning, ...] = ()

    def __post_init__(self) -> None:
        if (
            isinstance(self.root_index, bool)
            or not isinstance(self.root_index, int)
            or self.root_index < 0
        ):
            raise ValueError("A numerical root index must be non-negative.")
        if (
            isinstance(self.precision_digits, bool)
            or not isinstance(self.precision_digits, int)
            or self.precision_digits < 2
        ):
            raise ValueError("Numerical precision must contain at least two digits.")
        for value in (
            self.real,
            self.imaginary,
            self.absolute_residual,
            self.scaled_residual,
        ):
            try:
                decimal = Decimal(value)
            except (InvalidOperation, ValueError) as error:
                raise ValueError("Numerical values must be canonical decimal strings.") from error
            if not decimal.is_finite():
                raise ValueError("Numerical values must be finite.")
        if type(self.conjugate_status) is not ConjugateStatus:
            raise TypeError("Invalid conjugate status.")
        normalized_warnings = tuple(dict.fromkeys(self.warnings))
        if any(type(item) is not NumericalRootWarning for item in normalized_warnings):
            raise TypeError("Invalid numerical root warning.")
        object.__setattr__(self, "warnings", normalized_warnings)

    def __eq__(self, other: object) -> bool:
        if type(other) is not NumericalRootEstimate:
            return NotImplemented
        return (
            self.root_index,
            self.real,
            self.imaginary,
            self.precision_digits,
            self.absolute_residual,
            self.scaled_residual,
            self.conjugate_status,
            self.warnings,
        ) == (
            other.root_index,
            other.real,
            other.imaginary,
            other.precision_digits,
            other.absolute_residual,
            other.scaled_residual,
            other.conjugate_status,
            other.warnings,
        )

    __hash__ = None  # type: ignore[assignment]


@dataclass(frozen=True, slots=True)
class PolynomialRootAnalysis:
    """Exact roots and numerical verification for one source polynomial."""

    status: PolynomialRootStatus
    source: RootSource
    source_expression: ExactExpression
    roots: tuple[RootOccurrence, ...] = ()
    numerical_estimates: tuple[NumericalRootEstimate, ...] = ()
    original_degree: int | None = None
    actual_degree: int | None = None
    origins: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if type(self.status) is not PolynomialRootStatus:
            raise TypeError("Invalid polynomial root status.")
        if type(self.source) is not RootSource:
            raise TypeError("Invalid root source.")
        if type(self.source_expression) is not ExactExpression:
            raise TypeError("A source expression must be exact.")
        roots = tuple(self.roots)
        estimates = tuple(self.numerical_estimates)
        origins = tuple(self.origins)
        if any(type(item) is not RootOccurrence for item in roots):
            raise TypeError("Invalid exact root occurrence.")
        if any(type(item) is not NumericalRootEstimate for item in estimates):
            raise TypeError("Invalid numerical root estimate.")
        if any(
            value is not None and (isinstance(value, bool) or value < 0)
            for value in (self.original_degree, self.actual_degree)
        ):
            raise ValueError("Polynomial degrees must be non-negative.")
        if any(item.source is not self.source for item in roots):
            raise ValueError("Every root must use the analysis source.")
        if tuple(item.index for item in roots) != tuple(range(len(roots))):
            raise ValueError("Exact root indices must be contiguous and ordered.")
        if self.status is PolynomialRootStatus.COMPLETE:
            if (
                self.actual_degree is None
                or self.actual_degree <= 0
                or sum(item.multiplicity for item in roots)
                != self.actual_degree
            ):
                raise ValueError(
                    "A complete analysis must cover its positive actual degree."
                )
        elif roots or estimates:
            raise ValueError("Only a complete analysis may contain roots.")
        if estimates and (
            len(estimates) != len(roots)
            or tuple(item.root_index for item in estimates)
            != tuple(item.index for item in roots)
        ):
            raise ValueError(
                "Numerical estimates must correspond to every exact root."
            )
        if any(type(item) is not str for item in origins):
            raise TypeError("Analysis origins must be strings.")
        if any(not item for item in origins):
            raise ValueError("Analysis origins must not be empty.")
        object.__setattr__(self, "roots", roots)
        object.__setattr__(self, "numerical_estimates", estimates)
        object.__setattr__(self, "origins", origins)


@dataclass(frozen=True, slots=True)
class RootAnalysisGroup:
    """A deterministic collection of independently retained location sources."""

    status: PolynomialRootStatus
    analyses: tuple[PolynomialRootAnalysis, ...] = ()

    def __post_init__(self) -> None:
        if type(self.status) is not PolynomialRootStatus:
            raise TypeError("Invalid root group status.")
        analyses = tuple(self.analyses)
        if any(type(item) is not PolynomialRootAnalysis for item in analyses):
            raise TypeError("Invalid root group member.")
        object.__setattr__(self, "analyses", analyses)


@dataclass(frozen=True, slots=True)
class RootAnalysisLimits:
    """Explicit resource boundaries for exact and numerical analysis."""

    max_polynomial_degree: int = 32
    max_parameters: int = 8
    max_expression_nodes: int = 2048
    max_exact_rootof_count: int = 32
    numeric_precision_digits: int = 40
    numeric_guard_digits: int = 12
    max_numeric_iterations: int = 100
    max_results: int = 256
    max_factor_nodes: int = 1024
    max_substitution_nodes: int = 2048
    max_domain_exclusions: int = 64
    max_cancelled_factors: int = 64

    def __post_init__(self) -> None:
        for name in self.__dataclass_fields__:
            value = getattr(self, name)
            minimum = 2 if name == "numeric_precision_digits" else 1
            if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
                raise ValueError(f"{name} must be an integer >= {minimum}.")


@dataclass(frozen=True, slots=True)
class TransferFunctionRootAnalysisResult:
    """Complete result of a transfer-function root analysis attempt."""

    reduced_transfer_function: ReducedTransferFunction | None
    substitutions: ParameterSubstitutions | None
    reduced_zeros: PolynomialRootAnalysis | None
    reduced_poles: PolynomialRootAnalysis | None
    retained_domain_exclusions: RootAnalysisGroup
    cancelled_locations: RootAnalysisGroup
    diagnostics: tuple[Diagnostic, ...] = ()

    def __post_init__(self) -> None:
        if self.reduced_transfer_function is not None and type(
            self.reduced_transfer_function
        ) is not ReducedTransferFunction:
            raise TypeError("Invalid reduced transfer function.")
        if self.substitutions is not None and type(
            self.substitutions
        ) is not ParameterSubstitutions:
            raise TypeError("Invalid parameter substitutions.")
        if self.reduced_zeros is not None and type(
            self.reduced_zeros
        ) is not PolynomialRootAnalysis:
            raise TypeError("Invalid reduced-zero analysis.")
        if self.reduced_poles is not None and type(
            self.reduced_poles
        ) is not PolynomialRootAnalysis:
            raise TypeError("Invalid reduced-pole analysis.")
        if type(self.retained_domain_exclusions) is not RootAnalysisGroup:
            raise TypeError("Invalid retained-domain analysis.")
        if type(self.cancelled_locations) is not RootAnalysisGroup:
            raise TypeError("Invalid cancelled-location analysis.")
        diagnostics = tuple(self.diagnostics)
        if any(type(item) is not Diagnostic for item in diagnostics):
            raise TypeError("Invalid root-analysis diagnostic.")
        has_error = any(
            item.severity is DiagnosticSeverity.ERROR for item in diagnostics
        )
        if self.reduced_transfer_function is None:
            if self.reduced_zeros is not None or self.reduced_poles is not None:
                raise ValueError("A failed analysis cannot contain reduced roots.")
            if not has_error:
                raise ValueError("A failed analysis requires an error diagnostic.")
        elif (
            self.reduced_zeros is None
            or self.reduced_poles is None
            or has_error
        ):
            raise ValueError(
                "A successful analysis requires reduced roots and no errors."
            )
        object.__setattr__(self, "diagnostics", diagnostics)

    @property
    def succeeded(self) -> bool:
        """Whether no error diagnostic was produced."""

        return (
            self.reduced_transfer_function is not None
            and all(item.severity is not DiagnosticSeverity.ERROR for item in self.diagnostics)
        )
