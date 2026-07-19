"""Structured diagnostics shared by parsers and later application services."""

from dataclasses import dataclass
from enum import StrEnum


class DiagnosticSeverity(StrEnum):
    """Severity understood by application and presentation layers."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class DiagnosticCode(StrEnum):
    """Stable, machine-readable codes for expected validation failures."""

    PARSE_EMPTY_INPUT = "parse.empty_input"
    PARSE_INVALID_SYNTAX = "parse.invalid_syntax"
    PARSE_INVALID_NUMBER = "parse.invalid_number"
    PARSE_UNKNOWN_SYMBOL = "parse.unknown_symbol"
    PARSE_FORBIDDEN_NODE = "parse.forbidden_node"
    PARSE_IMPLICIT_MULTIPLICATION = "parse.implicit_multiplication"
    PARSE_LIMIT_EXCEEDED = "parse.limit_exceeded"
    PARSE_INVALID_EXPONENT = "parse.invalid_exponent"
    RATIONAL_INPUT_EMPTY_NUMERATOR = "rational_input.empty_numerator"
    RATIONAL_INPUT_EMPTY_DENOMINATOR = "rational_input.empty_denominator"
    RATIONAL_INPUT_VARIABLE_NOT_ALLOWED = (
        "rational_input.variable_not_allowed"
    )
    RATIONAL_INPUT_LIMIT_EXCEEDED = "rational_input.limit_exceeded"
    MATH_DIVISION_BY_ZERO = "math.division_by_zero"
    POLYNOMIAL_INVALID_VARIABLE = "polynomial.invalid_variable"
    POLYNOMIAL_VARIABLE_CONFLICT = "polynomial.variable_conflict"
    POLYNOMIAL_UNDECLARED_SYMBOL = "polynomial.undeclared_symbol"
    POLYNOMIAL_NOT_POLYNOMIAL = "polynomial.not_polynomial"
    POLYNOMIAL_NEGATIVE_EXPONENT = "polynomial.negative_exponent"
    POLYNOMIAL_SYMBOLIC_EXPONENT = "polynomial.symbolic_exponent"
    POLYNOMIAL_NONINTEGER_EXPONENT = "polynomial.noninteger_exponent"
    POLYNOMIAL_VARIABLE_IN_DENOMINATOR = (
        "polynomial.variable_in_denominator"
    )
    POLYNOMIAL_FLOAT_NOT_ALLOWED = "polynomial.float_not_allowed"
    POLYNOMIAL_PARAMETER_LIMIT_EXCEEDED = (
        "polynomial.parameter_limit_exceeded"
    )
    POLYNOMIAL_DEGREE_LIMIT_EXCEEDED = "polynomial.degree_limit_exceeded"
    POLYNOMIAL_TERM_LIMIT_EXCEEDED = "polynomial.term_limit_exceeded"
    POLYNOMIAL_COEFFICIENT_LIMIT_EXCEEDED = (
        "polynomial.coefficient_limit_exceeded"
    )
    POLYNOMIAL_COMPLEXITY_LIMIT_EXCEEDED = (
        "polynomial.complexity_limit_exceeded"
    )
    POLYNOMIAL_RESOURCE_LIMIT_EXCEEDED = (
        "polynomial.resource_limit_exceeded"
    )
    POLYNOMIAL_CONDITIONAL_DEGREE = "polynomial.conditional_degree"
    POLYNOMIAL_PARAMETER_DENOMINATOR_NONZERO = (
        "polynomial.parameter_denominator_nonzero"
    )
    POLYNOMIAL_SYMBOL_ASSUMPTION_NOT_ALLOWED = (
        "polynomial.symbol_assumption_not_allowed"
    )
    RAW_TRANSFER_INVALID_TREE = "raw_transfer.invalid_tree"
    RAW_TRANSFER_CYCLIC_TREE = "raw_transfer.cyclic_tree"
    RAW_TRANSFER_LIMIT_EXCEEDED = "raw_transfer.limit_exceeded"
    RAW_TRANSFER_RATIONALIZATION_FAILED = (
        "raw_transfer.rationalization_failed"
    )
    RAW_TRANSFER_NONPOLYNOMIAL_NUMERATOR = (
        "raw_transfer.nonpolynomial_numerator"
    )
    RAW_TRANSFER_NONPOLYNOMIAL_DENOMINATOR = (
        "raw_transfer.nonpolynomial_denominator"
    )
    RAW_TRANSFER_ZERO_DENOMINATOR = "raw_transfer.zero_denominator"
    RAW_TRANSFER_CONDITIONAL_DENOMINATOR = (
        "raw_transfer.conditional_denominator"
    )
    RAW_TRANSFER_VARIABLE_MISMATCH = "raw_transfer.variable_mismatch"
    RAW_TRANSFER_UNDECLARED_SYMBOL = "raw_transfer.undeclared_symbol"
    RAW_TRANSFER_RESOURCE_LIMIT_EXCEEDED = (
        "raw_transfer.resource_limit_exceeded"
    )
    RAW_TRANSFER_ZERO_DIVISOR = "raw_transfer.zero_divisor"
    RAW_TRANSFER_CONDITIONAL_DIVISOR = "raw_transfer.conditional_divisor"
    TRANSFER_REDUCTION_INVALID_RAW_VALUE = (
        "transfer_reduction.invalid_raw_value"
    )
    TRANSFER_REDUCTION_LIMIT_EXCEEDED = "transfer_reduction.limit_exceeded"
    TRANSFER_REDUCTION_COMMON_FACTOR_FAILED = (
        "transfer_reduction.common_factor_failed"
    )
    TRANSFER_REDUCTION_EXACT_DIVISION_FAILED = (
        "transfer_reduction.exact_division_failed"
    )
    TRANSFER_REDUCTION_RESULT_INVALID = (
        "transfer_reduction.result_invalid"
    )
    TRANSFER_REDUCTION_RESOURCE_LIMIT_EXCEEDED = (
        "transfer_reduction.resource_limit_exceeded"
    )
    TRANSFER_REDUCTION_NORMALIZATION_SKIPPED = (
        "transfer_reduction.normalization_skipped"
    )
    ROOT_ANALYSIS_INVALID_TRANSFER_FUNCTION = (
        "root_analysis.invalid_transfer_function"
    )
    ROOT_ANALYSIS_INVALID_SUBSTITUTION = "root_analysis.invalid_substitution"
    ROOT_ANALYSIS_PREREQUISITE_VIOLATED = (
        "root_analysis.prerequisite_violated"
    )
    ROOT_ANALYSIS_MISSING_PARAMETERS = "root_analysis.missing_parameters"
    ROOT_ANALYSIS_DOMAIN_EMPTY = "root_analysis.domain_empty"
    ROOT_ANALYSIS_EXACT_SOLVER_FAILED = "root_analysis.exact_solver_failed"
    ROOT_ANALYSIS_LIMIT_EXCEEDED = "root_analysis.limit_exceeded"
    ROOT_ANALYSIS_RESOURCE_LIMIT_EXCEEDED = (
        "root_analysis.resource_limit_exceeded"
    )
    ROOT_ANALYSIS_SYMBOLIC_UNDETERMINED = (
        "root_analysis.symbolic_undetermined"
    )
    ROOT_ANALYSIS_DEGREE_DROPPED = "root_analysis.degree_dropped"
    ROOT_ANALYSIS_NUMERIC_SOLVER_FAILED = (
        "root_analysis.numeric_solver_failed"
    )
    ROOT_ANALYSIS_RESIDUAL_TOO_LARGE = "root_analysis.residual_too_large"
    ROOT_ANALYSIS_ILL_CONDITIONED = "root_analysis.ill_conditioned"
    ROOT_ANALYSIS_CONJUGATE_MISMATCH = "root_analysis.conjugate_mismatch"
    ROOT_ANALYSIS_ZERO_POLYNOMIAL = "root_analysis.zero_polynomial"
    ROOT_ANALYSIS_NUMERIC_CHECK_SKIPPED = (
        "root_analysis.numeric_check_skipped"
    )
    STABILITY_ANALYSIS_INVALID_ROOT_ANALYSIS = (
        "stability_analysis.invalid_root_analysis"
    )
    STABILITY_ANALYSIS_LIMIT_EXCEEDED = (
        "stability_analysis.limit_exceeded"
    )
    STABILITY_ANALYSIS_RESOURCE_LIMIT_EXCEEDED = (
        "stability_analysis.resource_limit_exceeded"
    )
    STABILITY_ANALYSIS_REAL_PART_UNDETERMINED = (
        "stability_analysis.real_part_undetermined"
    )
    STABILITY_ANALYSIS_SYMBOLIC_UNDETERMINED = (
        "stability_analysis.symbolic_undetermined"
    )
    STABILITY_ANALYSIS_CANCELLED_LOCATION_NONNEGATIVE = (
        "stability_analysis.cancelled_location_nonnegative"
    )
    STABILITY_ANALYSIS_CANCELLED_LOCATION_UNDETERMINED = (
        "stability_analysis.cancelled_location_undetermined"
    )
    STABILITY_ANALYSIS_NUMERIC_CONTRADICTION = (
        "stability_analysis.numeric_contradiction"
    )
    STABILITY_ANALYSIS_BORDERLINE_NOT_EA_STABLE = (
        "stability_analysis.borderline_not_ea_stable"
    )
    STABILITY_ANALYSIS_CANCELLED_LOCATIONS_NOT_EVALUATED = (
        "stability_analysis.cancelled_locations_not_evaluated"
    )
    STABILITY_ANALYSIS_NO_POLES = "stability_analysis.no_poles"
    FREQUENCY_RESPONSE_INVALID_INPUT = "frequency_response.invalid_input"
    FREQUENCY_RESPONSE_CONTEXT_MISMATCH = (
        "frequency_response.context_mismatch"
    )
    FREQUENCY_RESPONSE_INVALID_FREQUENCIES = (
        "frequency_response.invalid_frequencies"
    )
    FREQUENCY_RESPONSE_INVALID_SUBSTITUTIONS = (
        "frequency_response.invalid_substitutions"
    )
    FREQUENCY_RESPONSE_SYMBOLIC_UNDETERMINED = (
        "frequency_response.symbolic_undetermined"
    )
    FREQUENCY_RESPONSE_SINGULAR = "frequency_response.singular"
    FREQUENCY_RESPONSE_ZERO_RESPONSE = "frequency_response.zero_response"
    FREQUENCY_RESPONSE_NUMERIC_UNDETERMINED = (
        "frequency_response.numeric_undetermined"
    )
    FREQUENCY_RESPONSE_LIMIT_EXCEEDED = (
        "frequency_response.limit_exceeded"
    )
    FREQUENCY_RESPONSE_RESOURCE_LIMIT_EXCEEDED = (
        "frequency_response.resource_limit_exceeded"
    )
    LOG_FREQUENCY_GRID_INVALID_REQUEST = "log_frequency_grid.invalid_request"
    LOG_FREQUENCY_GRID_INVALID_BOUNDS = "log_frequency_grid.invalid_bounds"
    LOG_FREQUENCY_GRID_INVALID_EXPLICIT_FREQUENCIES = (
        "log_frequency_grid.invalid_explicit_frequencies"
    )
    LOG_FREQUENCY_GRID_LIMIT_EXCEEDED = "log_frequency_grid.limit_exceeded"
    LOG_FREQUENCY_GRID_CERTIFICATION_FAILED = (
        "log_frequency_grid.certification_failed"
    )
    LOG_FREQUENCY_GRID_PRECISION_COLLISION = (
        "log_frequency_grid.precision_collision"
    )
    LOG_FREQUENCY_GRID_RESOURCE_LIMIT_EXCEEDED = (
        "log_frequency_grid.resource_limit_exceeded"
    )
    BODE_DATA_INVALID_INPUT = "bode_data.invalid_input"
    BODE_DATA_CONTEXT_MISMATCH = "bode_data.context_mismatch"
    BODE_DATA_INVALID_GRID = "bode_data.invalid_grid"
    BODE_DATA_FREQUENCY_ANALYSIS_FAILED = (
        "bode_data.frequency_analysis_failed"
    )
    BODE_DATA_LIMIT_EXCEEDED = "bode_data.limit_exceeded"
    BODE_DATA_NO_PLOTTABLE_DATA = "bode_data.no_plottable_data"
    BODE_DATA_RESOURCE_LIMIT_EXCEEDED = "bode_data.resource_limit_exceeded"
    BODE_PHASE_UNWRAP_INVALID_INPUT = "bode_phase_unwrap.invalid_input"
    BODE_PHASE_UNWRAP_INVALID_SOURCE = "bode_phase_unwrap.invalid_source"
    BODE_PHASE_UNWRAP_CONTEXT_MISMATCH = (
        "bode_phase_unwrap.context_mismatch"
    )
    BODE_PHASE_UNWRAP_LIMIT_EXCEEDED = "bode_phase_unwrap.limit_exceeded"
    BODE_PHASE_UNWRAP_NO_PHASE_DATA = "bode_phase_unwrap.no_phase_data"
    BODE_PHASE_UNWRAP_RESOURCE_LIMIT_EXCEEDED = (
        "bode_phase_unwrap.resource_limit_exceeded"
    )


@dataclass(frozen=True, slots=True)
class Diagnostic:
    """An immutable user-facing error or warning with optional log context."""

    severity: DiagnosticSeverity
    code: DiagnosticCode
    message: str
    field: str | None = None
    technical_details: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not self.message.strip():
            raise ValueError("A diagnostic message must not be empty.")

        immutable_details = tuple(
            (str(key), str(value)) for key, value in self.technical_details
        )
        object.__setattr__(self, "technical_details", immutable_details)
