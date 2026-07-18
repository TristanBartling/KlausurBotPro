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

Die Bootstrap-Anwendung benötigt keine Produktionsabhängigkeiten. PySide6 ist
als optionale GUI-Abhängigkeit vorgesehen, aber in der aktuell geprüften
Python-3.14-Umgebung nicht installiert. Bis die GUI-Entscheidung validiert ist,
startet die Anwendung bewusst als minimale Konsolenausgabe. Es wird kein
Ersatz-Webstack verwendet.

## Installation unter Windows PowerShell

```powershell
py -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

PySide6 wird erst aufgenommen, wenn die vorläufige GUI-Entscheidung validiert
ist und eine tatsächlich verwendete Desktop-Oberfläche implementiert wird.

## Start

```powershell
python -m klausurbotpro
```

Erwartete Ausgabe:

```text
KlausurBotPro
Projektfundament – noch keine Fachmodule
```

## Qualitätssicherung

```powershell
python -m pytest
python -m ruff check .
python -m mypy src tests
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
