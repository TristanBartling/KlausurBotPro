"""Shared safe presentation helper for optional LaTeX task headings."""

from __future__ import annotations


def prepend_latex_task_heading(latex_source: str, task_title: str) -> str:
    """Prepend one escaped section heading while preserving the solution source."""
    if not latex_source:
        return ""
    normalized_title = " ".join(task_title.split())
    if not normalized_title:
        return latex_source
    return rf"\section*{{{_escape_latex_text(normalized_title)}}}" + "\n" + latex_source


def _escape_latex_text(value: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "{": r"\{",
        "}": r"\}",
        "_": r"\_",
        "&": r"\&",
        "%": r"\%",
        "#": r"\#",
        "$": r"\$",
        "^": r"\textasciicircum{}",
        "~": r"\textasciitilde{}",
    }
    return "".join(replacements.get(character, character) for character in value)


__all__ = ["prepend_latex_task_heading"]
