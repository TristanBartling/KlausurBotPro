# Teststrategie

## Unit-Tests

Jede mathematische Funktion erhält kleine, deterministische Unit-Tests für
Normalfälle, Fehlereingaben, Voraussetzungen und analytisch bekannte
Grenzfälle. Exakte symbolische Ergebnisse werden möglichst exakt verglichen;
numerische Resultate mit fachlich begründeten absoluten und relativen
Toleranzen.

## Integrationstests

Integrationstests prüfen das Zusammenspiel von Parser, Domain-Modellen,
Fachlogik, Application Services, Workspace und Reporting an klar begrenzten
Schnittstellen. GUI und externe Dienste werden dabei durch kontrollierbare
Adapter ersetzt, sofern nicht gerade deren Integration geprüft wird.

## Parser- und Sicherheitstests

Der Phase-1A.1-Parser wird unabhängig in vier Stufen geprüft:

- tokenbasierte Normalisierung von Dezimalpunkt, Dezimalkomma und `^`
- AST-Whitelist und standardmäßige Ablehnung unbekannter Knoten
- manuelle, exakte Übersetzung erlaubter Knoten
- öffentliche Ergebnisse mit stabilen Diagnosecodes

Parametrische Tests decken gültige Ganzzahlen, Brüche, Dezimalzahlen, Symbole,
Klammern, Vorzeichen und Potenzen ab. Priorität und Rechtsassoziativität werden
explizit für `-s^2`, `(-s)^2` und `s^2^3` geprüft.

Angriffstests umfassen unter anderem Aufrufe, Imports, Attribute, Subscripts,
Container, Comprehensions, Generatoren, Lambda-Ausdrücke, Strings,
boolesche Ausdrücke, Vergleiche, Walrus-Ausdrücke, komplexe Literale und
Dunder-Namen. Ressourcenprüfungen erzwingen Grenzen für Eingabelänge,
AST-Größe und -Tiefe, Symbolanzahl, Ganzzahlziffern, Exponenten und geschätzte
Termanzahl. Kein Sicherheitstest darf echte Dateisystem-, Prozess- oder
Netzwerkoperationen ausführen.

Exaktheitstests stellen sicher, dass Dezimalpunkt und Dezimalkomma denselben
rationalen Wert liefern und `ExactExpression` keine SymPy-Float-Atome enthält.
Fehlertests prüfen deterministische Codes und stellen sicher, dass keine rohe
Syntax- oder Drittanbieterexception die Parser-Fassade verlässt.

## Regressionstests mit offiziellen Aufgaben

Verifizierte Aufgaben aus offiziellen Unterlagen werden später als
Regressionstests erfasst. Testdaten dokumentieren Quelle und belegte Seite,
Voraussetzungen, erwartete Zwischenschritte und unabhängig geprüfte Ergebnisse.
Musterlösungen gelten nicht ungeprüft als Testorakel.

## End-to-End-Tests

End-to-End-Tests decken wenige repräsentative Nutzerwege ab: Eingabe, Workflow,
manuelle Überschreibung, Folgeaktion, Rechenweg und Quellenlink. Sie ergänzen,
aber ersetzen keine Unit- und Integrationstests.

## Mathematische Gegenprüfungen

- Null-, Einheits-, Symmetrie- und Dimensionsfälle
- bekannte stabile, grenzstabile und instabile Systeme
- wiederholte und komplex konjugierte Pole
- singuläre oder schlecht konditionierte Fälle
- Rückeinsetzen und inverse Operationen, soweit mathematisch zulässig
- Vergleich exakter Symbolik mit numerischen Stichproben
- unabhängige Verfahren oder Bibliotheken als Kontrollinstanz

Tests dürfen bei Abweichungen nicht bloß durch größere Toleranzen oder
schwächere Assertions beruhigt werden. Ursache, Konditionierung und fachlich
vertretbare Genauigkeit sind zuerst zu klären.

## Externe APIs

Adaptertests simulieren Erfolg, ungültige Antworten, fehlende Schlüssel,
Zeitüberschreitungen, Rate Limits, Netzwerkfehler und Dienst-Ausfälle. Kein Test
der Standardsuite benötigt echtes Internet oder echte Zugangsdaten. Ausfälle
externer Dienste müssen transparent bleiben und lokale Funktionen unberührt
lassen.

## Qualitätspipeline

Die lokale Mindestpipeline ist:

```powershell
python -m pytest
python -m ruff check .
python -m mypy src tests
```

Mit wachsenden Fachmodulen kommen Coverage-Ziele und plattformübergreifende CI
erst nach einer dokumentierten Entscheidung hinzu.
