"""Smoke tests for the phase-0 package."""

import pytest

import klausurbotpro
from klausurbotpro.app import APP_NAME, FOUNDATION_MESSAGE, main


def test_package_metadata() -> None:
    assert klausurbotpro.__version__ == "0.1.0"
    assert APP_NAME == "KlausurBotPro"
    assert FOUNDATION_MESSAGE == "Projektfundament – noch keine Fachmodule"


def test_minimal_application_starts(capsys: pytest.CaptureFixture[str]) -> None:
    assert main() == 0
    assert capsys.readouterr().out.splitlines() == [APP_NAME, FOUNDATION_MESSAGE]
