"""Focused tests for the shared safe LaTeX task-heading helper."""

from klausurbotpro.application import prepend_latex_task_heading


def test_heading_is_normalized_and_safely_escaped() -> None:
    source = "  \\textbf{Gegeben}\n\\[x=1\\]  "

    result = prepend_latex_task_heading(source, "  Aufgabe 1_a &\nKontrolle 20%  ")

    assert result.startswith(r"\section*{Aufgabe 1\_a \& Kontrolle 20\%}" + "\n")
    assert result.removeprefix(result.splitlines()[0] + "\n") == source
    assert result.count(r"\section*{") == 1


def test_empty_heading_preserves_latex_source_and_empty_result_stays_empty() -> None:
    source = "  \\textbf{Gegeben}\n"

    assert prepend_latex_task_heading(source, " \n ") == source
    assert prepend_latex_task_heading("", "Aufgabe 1") == ""
