"""Focused profile tests for safe time/image expression parsing."""

from klausurbotpro.parsing import (
    ParserConfig,
    ParserProfile,
    SafeExpressionParser,
)


def test_time_profile_accepts_only_bounded_standard_functions() -> None:
    parser = SafeExpressionParser(ParserConfig.for_profile(ParserProfile.TIME_T))

    assert parser.parse("2*t*exp(-4*t) + sin(pi*t)").succeeded
    assert not parser.parse("s + exp(t)").succeeded
    assert not parser.parse("log(t)").succeeded


def test_image_profile_rejects_time_and_function_calls() -> None:
    parser = SafeExpressionParser(ParserConfig.for_profile(ParserProfile.IMAGE_S))

    assert parser.parse("(s+1)/(s^2+pi)").succeeded
    assert not parser.parse("s+t").succeeded
    assert not parser.parse("exp(s)").succeeded
