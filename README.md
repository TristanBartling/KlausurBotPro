# KlausurBotPro

KlausurBotPro wird eine professionelle Python-Desktopanwendung zum Lernen und
Bearbeiten von Aufgaben aus Regelungstechnik 1. Dieses Repository enthält
derzeit ausschließlich das Projektfundament. Fachmodule, Workflows,
Quellenverwaltung und Online-Integrationen sind noch nicht implementiert.

Das Produktkonzept steht in [docs/PROJECT_CONCEPT.md](docs/PROJECT_CONCEPT.md),
die vorläufige Architektur in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Voraussetzungen

- Python 3.12 oder neuer
- Windows PowerShell

Die Phase-0.5-Anwendung verwendet PySide6 für ein minimales Hauptfenster.
SymPy, NumPy, SciPy, Matplotlib und python-control sind als geprüfte
Produktionsabhängigkeiten aufgenommen, ohne bereits Fachmodule zu
implementieren. Ergebnisse des Technologiechecks stehen in
[docs/COMPATIBILITY.md](docs/COMPATIBILITY.md).

## Installation unter Windows PowerShell

```powershell
py -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Start

```powershell
python -m klausurbotpro
```

Es öffnet sich ein Fenster mit dem Titel `KlausurBotPro` und dem Hinweis
`Projektfundament – noch keine Fachmodule`. Das Schließen des Fensters beendet
die Anwendung sauber.

## Qualitätssicherung

```powershell
python -m pytest
python -m ruff check .
python -m mypy src tests
python -m pip check
python -c "import klausurbotpro; print(klausurbotpro.__version__)"
```

## Projektgrenzen

- Keine Regelungstechnik-Berechnung ist in Phase 0 enthalten.
- Lokale Original-PDFs gehören nach `resources/pdf/` und werden nicht
  eingecheckt.
- Geheimnisse gehören ausschließlich in eine lokale `.env`, niemals in Git.
- KI-gestützte Lern- und Entwicklungsfunktionen müssen von einem späteren
  Klausur-Build technisch getrennt bleiben.

Die geplanten Phasen und ihre Grenzen beschreibt [docs/ROADMAP.md](docs/ROADMAP.md).
