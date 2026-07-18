# Vorläufige Entscheidungen

Nicht ausdrücklich als geprüft markierte Einträge bleiben vorläufig. Neue
Produktionsabhängigkeiten müssen hier vor ihrer Aufnahme begründet werden.

| Thema | Vorläufige Entscheidung | Begründung / noch zu prüfen |
|---|---|---|
| Hauptsprache | Python ≥ 3.12; Python 3.14 für die aktuelle Entwicklung geprüft | Der Phase-0.5-Stack lief unter CPython 3.14.0 auf Windows 11; Support-Matrix und Packaging bleiben offen. |
| Projektlayout | `src`-Layout mit `pyproject.toml` | Verhindert versehentliche Imports aus dem Arbeitsverzeichnis. |
| GUI | PySide6 6.11.1 als Produktionsabhängigkeit geprüft | Installation, Import, minimales Fenster und sauberes Beenden unter Python 3.14 erfolgreich; Packaging und Lizenzprüfung bleiben offen. |
| Symbolik | SymPy 1.14.0 als symbolischer Kern geprüft | Installation, Import und einfache exakte Faktorisierung erfolgreich; Fachsyntax und Performance bleiben zu validieren. |
| Numerik | NumPy 2.5.1 und SciPy 1.18.0 geprüft | Installation, Import, Eigenwerte und elementare SciPy-Funktion erfolgreich; fachliche Verfahren benötigen eigene Tests. |
| Regelungstechnik | control 0.10.2 ohne Slycot geprüft | SISO-Transferfunktion funktioniert; fortgeschrittene und einzelne MIMO-Verfahren sind ohne Slycot eingeschränkt. |
| Diagramme | Matplotlib 3.11.1 geprüft | Nichtinteraktive Figure mit `Agg` erfolgreich; Qt-Integration und fachliche Diagramme bleiben offen. |
| Original-PDFs | Lokal und unverändert | Nachvollziehbarkeit über Manifest und Prüfsummen. |
| Externe APIs | Austauschbare Adapter | Offline-Fachkern und testbare Fehlerbehandlung erhalten. |
| Schichtengrenze | Fachlogik unabhängig von GUI | Wiederverwendung in Werkzeugen, Workflows und Tests. |
| Ergebnisformat | Strukturierte Objekte | Rechenweg, Provenienz, Warnungen und mehrere Darstellungen ermöglichen. |
| Phase-0.5-Laufzeit | Sechs geprüfte Produktionsabhängigkeiten | Konkrete Versionen und Grenzen sind in `docs/COMPATIBILITY.md` dokumentiert. |
| Build-Trennung | Separater Klausur-Build ohne KI | Technischer Nachweis und konkrete Build-Profile sind noch offen. |

## Aktuelle Entwicklungsabhängigkeiten

- `pytest`: Testausführung
- `ruff`: Linting und Importordnung
- `mypy`: statische Typprüfung
- `hatchling`: schlankes PEP-517-Build-Backend

Sie implementieren keine Produktfunktion. Versionsuntergrenzen werden bei
Einrichtung von CI und unterstützten Python-Versionen erneut geprüft.

## Geprüfte Produktionsabhängigkeiten

- `PySide6`: minimale Windows-Desktopoberfläche
- `SymPy`: geplanter exakter symbolischer Kern
- `NumPy`: numerische Arrays und lineare Algebra
- `SciPy`: ergänzende numerische Verfahren
- `Matplotlib`: nichtinteraktive und spätere eingebettete Diagramme
- `control`: optionale regelungstechnische Rechen- und Kontrollreferenz

Die Aufnahme beruht auf dem dokumentierten Phase-0.5-Kompatibilitätstest. Sie
ist keine fachliche Validierung und nimmt Phase 1 nicht vorweg.
