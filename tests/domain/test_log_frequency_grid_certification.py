"""Exact proof obligations for rationalized logarithmic targets."""

from fractions import Fraction

import pytest

import klausurbotpro.domain.log_frequency_grid_generator as generator_module
from klausurbotpro.domain import (
    DiagnosticCode,
    ExactRationalValue,
    LogFrequencyGridGenerator,
    LogFrequencyGridLimits,
    LogFrequencyGridRequest,
    LogFrequencyGridStatus,
    ScientificDecimal,
)
from klausurbotpro.domain._log_frequency_grid_certification import (
    certifies_relative_error,
    relative_error_limit,
)
from klausurbotpro.domain._log_frequency_grid_validation import (
    CertificationBudget,
)


def test_generated_candidates_satisfy_the_exact_relative_error_proof() -> None:
    limits = LogFrequencyGridLimits(grid_precision_digits=18)
    result = LogFrequencyGridGenerator(limits).generate(
        LogFrequencyGridRequest(
            ExactRationalValue(1),
            ExactRationalValue(10),
            2,
        )
    )
    point = result.points[1]
    candidate = Fraction(
        point.evaluation_frequency.numerator,
        point.evaluation_frequency.denominator,
    )

    assert point.maximum_relative_error == ExactRationalValue(
        1,
        2 * 10**17,
    )
    assert certifies_relative_error(
        candidate=candidate,
        omega_min=Fraction(1),
        ratio=Fraction(10),
        target_index=1,
        interval_count=2,
        epsilon=relative_error_limit(18),
        budget=CertificationBudget(2),
    )


def test_certification_failure_is_bounded_and_structured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def wrong_candidate(
        *args: object,
        **kwargs: object,
    ) -> tuple[ScientificDecimal, Fraction]:
        return ScientificDecimal(1, 0), Fraction(1)

    monkeypatch.setattr(
        generator_module,
        "approximate_logarithmic_target",
        wrong_candidate,
    )
    result = LogFrequencyGridGenerator(
        LogFrequencyGridLimits(max_certification_attempts=2)
    ).generate(
        LogFrequencyGridRequest(
            ExactRationalValue(1),
            ExactRationalValue(10),
            2,
        )
    )

    assert result.status is LogFrequencyGridStatus.FAILED
    assert result.request is None
    assert result.points == ()
    assert result.diagnostics[0].code is (
        DiagnosticCode.LOG_FREQUENCY_GRID_CERTIFICATION_FAILED
    )
    assert result.diagnostics[0].technical_details == (
        ("target_index", "1"),
        ("attempts", "2"),
    )


def test_certification_step_budget_is_enforced() -> None:
    result = LogFrequencyGridGenerator(
        LogFrequencyGridLimits(max_certification_steps=1)
    ).generate(
        LogFrequencyGridRequest(
            ExactRationalValue(1),
            ExactRationalValue(10),
            10,
        )
    )

    assert result.status is LogFrequencyGridStatus.FAILED
    assert result.diagnostics[0].code is (
        DiagnosticCode.LOG_FREQUENCY_GRID_LIMIT_EXCEEDED
    )
    assert result.diagnostics[0].technical_details == (
        ("limit", "max_certification_steps"),
    )
