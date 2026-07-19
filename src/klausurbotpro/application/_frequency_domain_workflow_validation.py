"""Defensive trust boundary for frequency-domain workflow results."""

from __future__ import annotations

from math import gcd
from typing import NoReturn, TypeGuard, cast

from klausurbotpro.application._frequency_domain_workflow_diagnostics import (
    owned_diagnostics,
)
from klausurbotpro.application._transfer_function_preparation_validation import (
    TransferFunctionPreparationFailure,
    validate_transfer_function_preparation_result,
)
from klausurbotpro.application._workflow_validation import validate_request
from klausurbotpro.application.frequency_domain_workflow_contracts import (
    FREQUENCY_DOMAIN_STAGE_ORDER,
    FrequencyDomainWorkflowDiagnosticCode,
    FrequencyDomainWorkflowLimits,
    FrequencyDomainWorkflowMode,
    FrequencyDomainWorkflowRequest,
    FrequencyDomainWorkflowResult,
    FrequencyDomainWorkflowStage,
    FrequencyDomainWorkflowStageRecord,
    FrequencyDomainWorkflowStageStatus,
    FrequencyDomainWorkflowStatus,
    FrequencyPhasePresentation,
)
from klausurbotpro.application.transfer_function_preparation_contracts import (
    TransferFunctionPreparationStatus,
)
from klausurbotpro.application.transfer_function_workflow_contracts import (
    TransferFunctionWorkflowRequest,
    WorkflowDiagnosticCode,
)
from klausurbotpro.domain import (
    Diagnostic,
    DiagnosticCode,
    DiagnosticSeverity,
    ExactRationalValue,
    LogFrequencyGridRequest,
)
from klausurbotpro.domain._bode_data_validation import (
    BodeDataFailure,
    validate_bode_data_result,
)
from klausurbotpro.domain._bode_phase_unwrap_validation import (
    BodePhaseUnwrapFailure,
    validate_bode_phase_unwrap_result,
)
from klausurbotpro.domain._frequency_response_result_validation import (
    validate_frequency_response_result,
)
from klausurbotpro.domain._frequency_response_validation import (
    FrequencyResponseFailure,
)
from klausurbotpro.domain._log_frequency_grid_result_validation import (
    validate_log_frequency_grid_result,
)
from klausurbotpro.domain._log_frequency_grid_validation import (
    LogFrequencyGridFailure,
)

_NESTED_ERRORS = (AttributeError, AssertionError, IndexError, TypeError, ValueError)
_MISSING_RESULT_CODES = {
    FrequencyDomainWorkflowDiagnosticCode.LIMIT_EXCEEDED.value,
    FrequencyDomainWorkflowDiagnosticCode.RESOURCE_LIMIT_EXCEEDED.value,
}


class FrequencyDomainWorkflowFailure(ValueError):
    """A frequency-domain workflow result violates its trust contract."""


def validate_frequency_domain_request(
    request: FrequencyDomainWorkflowRequest,
    limits: FrequencyDomainWorkflowLimits,
) -> tuple[tuple[str, str], ...]:
    errors: list[tuple[str, str]] = []
    if type(request.preparation_request) is not TransferFunctionWorkflowRequest:
        errors.append(
            ("preparation_request", "Ungültiger Transferfunktionsauftrag.")
        )
    else:
        errors.extend(
            (f"preparation_request.{field}", reason)
            for field, reason in validate_request(
                request.preparation_request,
                limits.preparation,
            )
        )
    if type(request.mode) is not FrequencyDomainWorkflowMode:
        errors.append(("mode", "Ungültiger Frequenzworkflowmodus."))
    if type(request.phase_presentation) is not FrequencyPhasePresentation:
        errors.append(("phase_presentation", "Ungültige Phasendarstellung."))
    if request.mode is FrequencyDomainWorkflowMode.SINGLE_POINT:
        if not _is_canonical_rational(request.single_angular_frequency):
            errors.append(
                (
                    "single_angular_frequency",
                    "Eine exakte Kreisfrequenz ist erforderlich.",
                )
            )
        elif request.single_angular_frequency.numerator < 0:
            errors.append(
                (
                    "single_angular_frequency",
                    "Die Kreisfrequenz darf nicht negativ sein.",
                )
            )
        if request.grid_request is not None:
            errors.append(("grid_request", "SINGLE_POINT verwendet kein Raster."))
        if (
            request.phase_presentation
            is not FrequencyPhasePresentation.PRINCIPAL_ONLY
        ):
            errors.append(
                (
                    "phase_presentation",
                    "SINGLE_POINT unterstützt keine Phasenentfaltung.",
                )
            )
    elif request.mode is FrequencyDomainWorkflowMode.BODE:
        if request.single_angular_frequency is not None:
            errors.append(
                (
                    "single_angular_frequency",
                    "BODE verwendet keine Einzelkreisfrequenz.",
                )
            )
        if type(request.grid_request) is not LogFrequencyGridRequest:
            errors.append(("grid_request", "BODE benötigt einen Rasterauftrag."))
        elif not _has_valid_grid_structure(request.grid_request):
            errors.append(
                ("grid_request", "Das BODE-Raster ist strukturell ungültig.")
            )
    return tuple(errors)


def _has_valid_grid_structure(request: LogFrequencyGridRequest) -> bool:
    return (
        _is_canonical_rational(request.omega_min)
        and _is_canonical_rational(request.omega_max)
        and type(request.points_per_decade) is int
        and type(request.explicit_frequencies) is tuple
        and all(
            _is_canonical_rational(value)
            for value in request.explicit_frequencies
        )
    )


def _is_canonical_rational(value: object) -> TypeGuard[ExactRationalValue]:
    return (
        type(value) is ExactRationalValue
        and type(value.numerator) is int
        and type(value.denominator) is int
        and value.denominator > 0
        and gcd(abs(value.numerator), value.denominator) == 1
    )


def validate_frequency_domain_workflow_result(
    result: FrequencyDomainWorkflowResult,
    limits: FrequencyDomainWorkflowLimits,
) -> None:
    if type(result) is not FrequencyDomainWorkflowResult:
        raise TypeError("result must be FrequencyDomainWorkflowResult.")
    if type(limits) is not FrequencyDomainWorkflowLimits:
        raise TypeError("limits must be FrequencyDomainWorkflowLimits.")
    try:
        _validate_result(result, limits)
    except FrequencyDomainWorkflowFailure:
        raise
    except (
        TransferFunctionPreparationFailure,
        FrequencyResponseFailure,
        LogFrequencyGridFailure,
        BodeDataFailure,
        BodePhaseUnwrapFailure,
        *_NESTED_ERRORS,
    ) as error:
        raise FrequencyDomainWorkflowFailure(
            f"Manipulated frequency workflow: {type(error).__name__}."
        ) from error


def _validate_result(
    result: FrequencyDomainWorkflowResult,
    limits: FrequencyDomainWorkflowLimits,
) -> None:
    result._validate_local()
    if result.request is None:
        _validate_invalid_request_result(result)
        return
    request_errors = validate_frequency_domain_request(result.request, limits)
    if request_errors:
        _fail("A retained frequency request must be valid.")
    records = result.stage_records
    if (
        len(records) != len(FREQUENCY_DOMAIN_STAGE_ORDER)
        or tuple(item.stage for item in records) != FREQUENCY_DOMAIN_STAGE_ORDER
    ):
        _fail("A valid request requires five ordered stage records.")
    for record in records:
        _validate_record(record)
    _validate_stage_matrix(result.request, records)
    expected_diagnostics = tuple(
        diagnostic for record in records for diagnostic in record.diagnostics
    )
    if result.diagnostics != expected_diagnostics:
        _fail("Workflow diagnostics are not the ordered stage aggregation.")
    if len(result.diagnostics) > limits.max_aggregated_diagnostics:
        _fail("Workflow diagnostics exceed their explicit limit.")

    _validate_preparation(result, limits)
    if result.request.mode is FrequencyDomainWorkflowMode.SINGLE_POINT:
        _validate_single_point(result, limits)
    else:
        _validate_bode_path(result, limits)
    expected_status = _derive_status(result)
    if result.status is not expected_status:
        _fail("Workflow status contradicts the requested stage outcomes.")


def _validate_invalid_request_result(
    result: FrequencyDomainWorkflowResult,
) -> None:
    values = (
        result.preparation_result,
        result.single_point_result,
        result.grid_result,
        result.bode_data_result,
        result.phase_unwrap_result,
    )
    if (
        result.status is not FrequencyDomainWorkflowStatus.FAILED
        or any(value is not None for value in values)
        or result.stage_records
        or len(result.diagnostics) != 1
    ):
        _fail("An invalid request requires one value-free failure diagnostic.")
    diagnostic = result.diagnostics[0]
    diagnostic_code = cast(object, diagnostic.code)
    if (
        type(diagnostic) is not Diagnostic
        or diagnostic.severity is not DiagnosticSeverity.ERROR
        or type(diagnostic_code) is not FrequencyDomainWorkflowDiagnosticCode
        or diagnostic_code
        is not FrequencyDomainWorkflowDiagnosticCode.INVALID_REQUEST
        or type(diagnostic.message) is not str
        or not diagnostic.message.strip()
        or diagnostic.field is not None
        or type(diagnostic.technical_details) is not tuple
        or not diagnostic.technical_details
        or any(
            type(item) is not tuple
            or len(item) != 2
            or any(type(value) is not str or not value for value in item)
            for item in diagnostic.technical_details
        )
    ):
        _fail("The invalid-request diagnostic is manipulated.")


def _validate_record(record: FrequencyDomainWorkflowStageRecord) -> None:
    if type(record) is not FrequencyDomainWorkflowStageRecord:
        _fail("A stage record has an invalid type.")
    if (
        type(record.stage) is not FrequencyDomainWorkflowStage
        or type(record.status) is not FrequencyDomainWorkflowStageStatus
        or type(record.diagnostics) is not tuple
        or any(type(item) is not Diagnostic for item in record.diagnostics)
    ):
        _fail("A stage record is structurally invalid.")
    for diagnostic in record.diagnostics:
        _validate_diagnostic(diagnostic)
    has_error = any(
        item.severity is DiagnosticSeverity.ERROR
        for item in record.diagnostics
    )
    if record.status is FrequencyDomainWorkflowStageStatus.FAILED:
        if not has_error:
            _fail("A failed stage requires an error diagnostic.")
    elif has_error:
        _fail("Only a failed stage may contain an error diagnostic.")
    if record.status in (
        FrequencyDomainWorkflowStageStatus.BLOCKED,
        FrequencyDomainWorkflowStageStatus.NOT_APPLICABLE,
    ) and record.diagnostics:
        _fail("Unavailable stages cannot contain diagnostics.")


def _validate_diagnostic(diagnostic: Diagnostic) -> None:
    if (
        type(diagnostic.severity) is not DiagnosticSeverity
        or type(diagnostic.code)
        not in (
            DiagnosticCode,
            WorkflowDiagnosticCode,
            FrequencyDomainWorkflowDiagnosticCode,
        )
        or type(diagnostic.message) is not str
        or not diagnostic.message.strip()
        or (diagnostic.field is not None and type(diagnostic.field) is not str)
        or type(diagnostic.technical_details) is not tuple
        or any(
            type(item) is not tuple
            or len(item) != 2
            or any(type(value) is not str for value in item)
            for item in diagnostic.technical_details
        )
    ):
        _fail("A workflow diagnostic is manipulated.")


def _validate_stage_matrix(
    request: FrequencyDomainWorkflowRequest,
    records: tuple[FrequencyDomainWorkflowStageRecord, ...],
) -> None:
    failure_seen = False
    for record in records:
        requested = _is_requested(request, record.stage)
        if not requested:
            if (
                record.status
                is not FrequencyDomainWorkflowStageStatus.NOT_APPLICABLE
            ):
                _fail("An unrequested stage must remain NOT_APPLICABLE.")
            continue
        if failure_seen:
            if record.status is not FrequencyDomainWorkflowStageStatus.BLOCKED:
                _fail("Requested stages after a failure must be blocked.")
            continue
        if record.status is FrequencyDomainWorkflowStageStatus.BLOCKED:
            _fail("A blocked stage requires an earlier requested failure.")
        if record.status is FrequencyDomainWorkflowStageStatus.NOT_APPLICABLE:
            _fail("A requested stage cannot be NOT_APPLICABLE.")
        if record.status is FrequencyDomainWorkflowStageStatus.FAILED:
            failure_seen = True


def _validate_preparation(
    result: FrequencyDomainWorkflowResult,
    limits: FrequencyDomainWorkflowLimits,
) -> None:
    assert result.request is not None
    record = result.stage_records[0]
    preparation = result.preparation_result
    if preparation is None:
        _validate_missing_failure(record)
        return
    validate_transfer_function_preparation_result(
        preparation,
        limits.preparation,
    )
    if preparation.request is not result.request.preparation_request:
        _fail("Preparation retained a foreign request.")
    if preparation.succeeded:
        if (
            record.status is not FrequencyDomainWorkflowStageStatus.SUCCEEDED
            or record.diagnostics != preparation.diagnostics
        ):
            _fail("A complete preparation requires a successful stage.")
    else:
        _validate_failed_record(
            record,
            preparation.diagnostics,
            FrequencyDomainWorkflowDiagnosticCode.PREPARATION_FAILED,
        )


def _validate_single_point(
    result: FrequencyDomainWorkflowResult,
    limits: FrequencyDomainWorkflowLimits,
) -> None:
    assert result.request is not None
    if (
        result.grid_result is not None
        or result.bode_data_result is not None
        or result.phase_unwrap_result is not None
    ):
        _fail("SINGLE_POINT cannot retain Bode-path values.")
    record = result.stage_records[1]
    response = result.single_point_result
    if record.status is FrequencyDomainWorkflowStageStatus.BLOCKED:
        if response is not None:
            _fail("A blocked single-point stage cannot retain a result.")
        return
    if response is None:
        _validate_missing_failure(record)
        return
    validate_frequency_response_result(
        response,
        limits.frequency_response,
    )
    if response.succeeded:
        preparation = result.preparation_result
        assert preparation is not None
        assert preparation.reduced_value is not None
        requested_frequency = result.request.single_angular_frequency
        if (
            response.reduced_transfer_function
            is not preparation.reduced_value
            or response.frequencies is None
            or response.frequencies.frequencies != (requested_frequency,)
            or response.substitutions != preparation.request.substitutions
            or record.status
            is not FrequencyDomainWorkflowStageStatus.SUCCEEDED
            or record.diagnostics != response.diagnostics
        ):
            _fail("The single-point handoff is inconsistent.")
    else:
        _validate_failed_record(
            record,
            response.diagnostics,
            FrequencyDomainWorkflowDiagnosticCode.SINGLE_POINT_FAILED,
        )


def _validate_bode_path(
    result: FrequencyDomainWorkflowResult,
    limits: FrequencyDomainWorkflowLimits,
) -> None:
    assert result.request is not None
    if result.single_point_result is not None:
        _fail("BODE cannot retain a separate single-point result.")
    grid_record = result.stage_records[2]
    grid = result.grid_result
    if grid_record.status is FrequencyDomainWorkflowStageStatus.BLOCKED:
        if any(
            value is not None
            for value in (
                grid,
                result.bode_data_result,
                result.phase_unwrap_result,
            )
        ):
            _fail("A blocked Bode path cannot retain downstream values.")
        return
    if grid is None:
        _validate_missing_failure(grid_record)
        return
    validate_log_frequency_grid_result(grid, limits.grid)
    if grid.succeeded:
        if (
            grid.request is None
            or result.request.grid_request is None
            or not _strict_grid_request_matches(
                grid.request,
                result.request.grid_request,
            )
            or grid_record.status
            is not FrequencyDomainWorkflowStageStatus.SUCCEEDED
            or grid_record.diagnostics != grid.diagnostics
        ):
            _fail("The logarithmic grid handoff is inconsistent.")
    else:
        _validate_failed_record(
            grid_record,
            grid.diagnostics,
            FrequencyDomainWorkflowDiagnosticCode.GRID_FAILED,
        )
        if (
            result.bode_data_result is not None
            or result.phase_unwrap_result is not None
        ):
            _fail("A failed grid cannot retain downstream results.")
        return

    _validate_bode_result(result, limits)


def _validate_bode_result(
    result: FrequencyDomainWorkflowResult,
    limits: FrequencyDomainWorkflowLimits,
) -> None:
    assert result.request is not None
    record = result.stage_records[3]
    bode = result.bode_data_result
    if record.status is FrequencyDomainWorkflowStageStatus.BLOCKED:
        if bode is not None or result.phase_unwrap_result is not None:
            _fail("A blocked Bode stage cannot retain downstream values.")
        return
    if bode is None:
        _validate_missing_failure(record)
        return
    validate_bode_data_result(
        bode,
        frequency_limits=limits.frequency_response,
        grid_limits=limits.grid,
        bode_limits=limits.bode,
    )
    if bode.succeeded:
        preparation = result.preparation_result
        assert preparation is not None
        assert preparation.reduced_value is not None
        if (
            bode.grid is not result.grid_result
            or bode.frequency_response_result is None
            or bode.frequency_response_result.reduced_transfer_function
            is not preparation.reduced_value
            or bode.frequency_response_result.substitutions
            != preparation.request.substitutions
        ):
            _fail("The Bode handoff contains foreign context.")
        expected = owned_diagnostics(
            bode.diagnostics,
            result.grid_result.diagnostics,  # type: ignore[union-attr]
        )
        if (
            record.status is not FrequencyDomainWorkflowStageStatus.SUCCEEDED
            or record.diagnostics != expected
        ):
            _fail("Bode diagnostic ownership is inconsistent.")
    else:
        _validate_failed_record(
            record,
            bode.diagnostics,
            FrequencyDomainWorkflowDiagnosticCode.BODE_DATA_FAILED,
        )
        if result.phase_unwrap_result is not None:
            _fail("A failed Bode result cannot retain an unwrap result.")
        return
    _validate_unwrap_result(result, limits)


def _validate_unwrap_result(
    result: FrequencyDomainWorkflowResult,
    limits: FrequencyDomainWorkflowLimits,
) -> None:
    assert result.request is not None
    record = result.stage_records[4]
    unwrap = result.phase_unwrap_result
    if (
        result.request.phase_presentation
        is FrequencyPhasePresentation.PRINCIPAL_ONLY
    ):
        if (
            record.status
            is not FrequencyDomainWorkflowStageStatus.NOT_APPLICABLE
            or unwrap is not None
        ):
            _fail("Principal-only Bode requests cannot retain unwrap values.")
        return
    if record.status is FrequencyDomainWorkflowStageStatus.BLOCKED:
        if unwrap is not None:
            _fail("A blocked unwrap stage cannot retain a result.")
        return
    if unwrap is None:
        _validate_missing_failure(record)
        return
    validate_bode_phase_unwrap_result(
        unwrap,
        frequency_limits=limits.frequency_response,
        grid_limits=limits.grid,
        bode_limits=limits.bode,
        unwrap_limits=limits.phase_unwrap,
    )
    if unwrap.succeeded:
        if unwrap.source_bode_data is not result.bode_data_result:
            _fail("The unwrap result references foreign Bode data.")
        expected = owned_diagnostics(
            unwrap.diagnostics,
            result.bode_data_result.diagnostics,  # type: ignore[union-attr]
        )
        if (
            record.status is not FrequencyDomainWorkflowStageStatus.SUCCEEDED
            or record.diagnostics != expected
        ):
            _fail("Unwrap diagnostic ownership is inconsistent.")
    else:
        _validate_failed_record(
            record,
            unwrap.diagnostics,
            FrequencyDomainWorkflowDiagnosticCode.PHASE_UNWRAP_FAILED,
        )


def _validate_missing_failure(
    record: FrequencyDomainWorkflowStageRecord,
) -> None:
    if (
        record.status is not FrequencyDomainWorkflowStageStatus.FAILED
        or len(record.diagnostics) != 1
        or record.diagnostics[0].severity is not DiagnosticSeverity.ERROR
        or record.diagnostics[0].code.value not in _MISSING_RESULT_CODES
    ):
        _fail("A missing stage result requires one resource or limit failure.")


def _validate_failed_record(
    record: FrequencyDomainWorkflowStageRecord,
    source: tuple[Diagnostic, ...],
    code: FrequencyDomainWorkflowDiagnosticCode,
) -> None:
    if (
        record.status is not FrequencyDomainWorkflowStageStatus.FAILED
        or record.diagnostics[: len(source)] != source
        or len(record.diagnostics) != len(source) + 1
        or record.diagnostics[-1].severity is not DiagnosticSeverity.ERROR
        or record.diagnostics[-1].code.value != code.value
    ):
        _fail("A failed stage does not preserve its owned diagnostics.")


def _strict_grid_request_matches(
    actual: LogFrequencyGridRequest,
    expected: LogFrequencyGridRequest,
) -> bool:
    return (
        type(actual) is LogFrequencyGridRequest
        and type(actual.omega_min) is ExactRationalValue
        and actual.omega_min == expected.omega_min
        and type(actual.omega_max) is ExactRationalValue
        and actual.omega_max == expected.omega_max
        and type(actual.points_per_decade) is int
        and actual.points_per_decade == expected.points_per_decade
        and type(actual.explicit_frequencies) is tuple
        and actual.explicit_frequencies == expected.explicit_frequencies
    )


def _derive_status(
    result: FrequencyDomainWorkflowResult,
) -> FrequencyDomainWorkflowStatus:
    if not any(
        item.status is FrequencyDomainWorkflowStageStatus.FAILED
        for item in result.stage_records
    ):
        return FrequencyDomainWorkflowStatus.COMPLETE
    preparation = result.preparation_result
    if (
        preparation is None
        or preparation.status is TransferFunctionPreparationStatus.FAILED
    ):
        return FrequencyDomainWorkflowStatus.FAILED
    return FrequencyDomainWorkflowStatus.PARTIAL


def _is_requested(
    request: FrequencyDomainWorkflowRequest,
    stage: FrequencyDomainWorkflowStage,
) -> bool:
    if stage is FrequencyDomainWorkflowStage.PREPARATION:
        return True
    if request.mode is FrequencyDomainWorkflowMode.SINGLE_POINT:
        return stage is FrequencyDomainWorkflowStage.SINGLE_POINT_RESPONSE
    if stage in (
        FrequencyDomainWorkflowStage.LOG_FREQUENCY_GRID,
        FrequencyDomainWorkflowStage.BODE_DATA,
    ):
        return True
    return (
        stage is FrequencyDomainWorkflowStage.PHASE_UNWRAP
        and request.phase_presentation
        is FrequencyPhasePresentation.PRINCIPAL_AND_UNWRAPPED
    )


def _fail(message: str) -> NoReturn:
    raise FrequencyDomainWorkflowFailure(message)


__all__ = [
    "FrequencyDomainWorkflowFailure",
    "validate_frequency_domain_request",
    "validate_frequency_domain_workflow_result",
]
