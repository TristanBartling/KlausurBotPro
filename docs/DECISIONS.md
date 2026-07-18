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
| Ausdrucksparser | Token-Normalisierung, Python-AST-Whitelist und manuelle SymPy-Übersetzung geprüft | Kein `eval`, keine rohe Übergabe an `sympify` oder `parse_expr`; Token-Adjazenz erkennt implizite Multiplikation, und nur unmittelbar zwischen Ziffernfolgen verbrauchte Dezimalkommas sind gültig. |
| Exakte Ausdrücke | Unveränderliches `ExactExpression` kapselt SymPy | Rationale Dezimalwerte, wertbasierte Gleichheit, stabile Darstellung und interne Fachkern-Schnittstelle sind geprüft. |
| Parsergrenzen | Zentraler `ParserLimits`-Vertrag | Standardgrenzen: 1.000 Zeichen, 256 AST-Knoten, Tiefe 32, 16 konfigurierte und verwendete Symbole, 128 Ganzzahlziffern, Exponentenbetrag 32 und 2.048 geschätzte Terme. Die Symbolmenge wird vor der SymPy-Tabelle begrenzt; erwartbare Ressourcenfehler werden als `PARSE_LIMIT_EXCEEDED` diagnostiziert. |
| Polynomialmodell | Factory-only `Polynomial` auf Basis von `ExactExpression` geprüft | Der unveränderliche Wert enthält nur mathematisch verwendete Parameter; unbenutzte Deklarationen verändern weder Gleichheit noch Hash. Nullpolynom, dichte exakte Koeffizienten und kanonische Darstellung sind getestet. |
| Polynomialsemantik | Kanonische Feldsemantik über `QQ` beziehungsweise `QQ.frac_field` geprüft | `Polynomial` speichert keine vollständige Eingabeprovenienz. Vor oder während der Reduktion entfernte Definitionslücken werden nicht rekonstruiert; Bedingungen beziehen sich nur auf Nenner und führende Koeffizienten der kanonisch reduzierten Koeffizientendarstellung. Eine spätere eingabetreue Transferfunktions-Rohdarstellung muss ursprüngliche Faktoren, Bedingungen und Provenienz separat vor der Kürzung erfassen; eine reduzierte Darstellung darf kanonisch sein. Diese Semantik wird nicht nachträglich in `Polynomial` eingebaut. |
| Polynomialgrad | Generischer und garantierter Grad werden getrennt | Unbekannte Nullheit eines symbolischen führenden Koeffizienten erzeugt eine explizite Nichtnullbedingung und niemals eine unbelegte Gradbehauptung. |
| Polynomialkoeffizienten | `QQ` beziehungsweise deterministischer `QQ.frac_field` | Exakte rationale Zahlen, Parameterpolynome und rationale Parameterfunktionen sind erlaubt; `EX`, Float-Atome, Funktionen und algebraische Erweiterungen bleiben ausgeschlossen. Zusammengesetzte Nichtnullbedingungen wie `T**2`, `T1*T2` und `K**2 - 1` sind zulässige Normalformen; eine spätere Faktorisierung ist optional. |
| Polynomialgrenzen | Separater `PolynomialLimits`-Vertrag | Standardgrenzen: Grad 32, 33 Koeffizienten, 33 strukturelle Terme, 16 Parameter, 128 Operationen je Koeffizient und 512 Ausdrucksknoten. Vor SymPy erfolgt eine strukturelle Gradprüfung ohne grobe exponentielle Termschätzung. |
| Rationale Eingabestruktur | Unveränderlicher, SymPy-freier Rohbaum vor jeder Vereinfachung geprüft | Exakte Zahl-, Symbol- und Operatorknoten bewahren Reihenfolge und Verschachtelung. `K/K`, `K-K`, Produkte, Potenzen und verschachtelte Divisionen bleiben strukturell unterscheidbar; nur einzelne Zahlenliterale werden als exakte gekürzte Brüche gespeichert. |
| Rationale Eingabeformen | Getrennte Verträge für zwei Felder und einen gemeinsamen Ausdruck geprüft | `SeparatedTransferFunctionInput` hält Zähler und Nenner separat; `CommonTransferFunctionInput` hält einen vollständigen Baum und verlangt keine Division auf oberster Ebene. Original- und Normalisierungstext sind Metadaten und verändern die strukturelle Wertgleichheit nicht. |
| Rationaler Eingabeparser | Gemeinsame sichere AST-Regeln, direkte Rohbaumübersetzung und gemeinsames Ressourcenbudget geprüft | Der neue Parser verwendet weder SymPy noch `ExactExpression`, vereinfacht nicht und akzeptiert einen syntaktischen Nullnenner für eine spätere Domainvalidierung. `ParserLimits` begrenzt zusätzlich die kombinierte Länge und gesamte Knotenanzahl einer getrennten Eingabe. Das bestehende Verhalten von `SafeExpressionParser` bleibt durch Regressionstests belegt. |
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
