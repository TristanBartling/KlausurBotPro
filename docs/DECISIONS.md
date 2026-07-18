# Vorläufige Entscheidungen

Alle Einträge sind in Phase 0 vorläufig, solange keine Validierung und kein
förmlicher Entscheidungsdatensatz etwas anderes festhalten. Neue
Produktionsabhängigkeiten müssen hier vor ihrer Aufnahme begründet werden.

| Thema | Vorläufige Entscheidung | Begründung / noch zu prüfen |
|---|---|---|
| Hauptsprache | Python ≥ 3.12 | Gute Mathematikbibliotheken; konkrete Support-Matrix vor Packaging prüfen. |
| Projektlayout | `src`-Layout mit `pyproject.toml` | Verhindert versehentliche Imports aus dem Arbeitsverzeichnis. |
| GUI | PySide6 wahrscheinlich | Professionelle Desktop-GUI; Python-3.14-Kompatibilität, Lizenz, Paketgröße und Deployment noch prüfen. |
| Symbolik | SymPy als geplanter Kern | Exakte Resultate; Syntax, Performance und Domänenannahmen validieren. |
| Numerik | NumPy/SciPy geplant | Gegenprüfungen und numerische Verfahren; erst bei konkretem Bedarf hinzufügen. |
| Regelungstechnik | `python-control` optional | Nur als Rechen- oder Kontrollreferenz nach fachlicher Validierung. |
| Diagramme | Matplotlib geplant | Desktopintegration und Exportanforderungen noch prüfen. |
| Original-PDFs | Lokal und unverändert | Nachvollziehbarkeit über Manifest und Prüfsummen. |
| Externe APIs | Austauschbare Adapter | Offline-Fachkern und testbare Fehlerbehandlung erhalten. |
| Schichtengrenze | Fachlogik unabhängig von GUI | Wiederverwendung in Werkzeugen, Workflows und Tests. |
| Ergebnisformat | Strukturierte Objekte | Rechenweg, Provenienz, Warnungen und mehrere Darstellungen ermöglichen. |
| Phase-0-Laufzeit | Keine Pflichtabhängigkeiten | Das Fundament bleibt unter Python 3.14 importierbar; PySide6 ist aktuell nicht installiert. |
| Build-Trennung | Separater Klausur-Build ohne KI | Technischer Nachweis und konkrete Build-Profile sind noch offen. |

## Aktuelle Entwicklungsabhängigkeiten

- `pytest`: Testausführung
- `ruff`: Linting und Importordnung
- `mypy`: statische Typprüfung
- `hatchling`: schlankes PEP-517-Build-Backend

Sie implementieren keine Produktfunktion. Versionsuntergrenzen werden bei
Einrichtung von CI und unterstützten Python-Versionen erneut geprüft.
