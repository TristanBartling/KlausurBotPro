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

- tokenbasierte Normalisierung von Dezimalpunkt, Dezimalkomma und `^` sowie
  vollständige Adjazenztests gegen implizite Multiplikation
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
AST-Größe und -Tiefe, konfigurierte und verwendete Symbolanzahl,
Ganzzahlziffern, Exponenten und geschätzte Termanzahl. Regressionstests prüfen,
dass jedes nicht unmittelbar als Dezimaltrenner verbrauchte Komma auch in
Klammern als ungültige Zahl abgelehnt wird. Kein Sicherheitstest darf echte
Dateisystem-, Prozess- oder Netzwerkoperationen ausführen.

Exaktheitstests stellen sicher, dass Dezimalpunkt und Dezimalkomma denselben
rationalen Wert liefern und `ExactExpression` keine SymPy-Float-Atome enthält.
Fehlertests prüfen deterministische Codes. Gezieltes Monkeypatching stellt für
Normalisierung, `ast.parse`, Validierung, Übersetzung und
`ExactExpression`-/SymPy-Erzeugung sicher, dass `MemoryError`,
`RecursionError` und `OverflowError` als `PARSE_LIMIT_EXCEEDED` gekapselt
werden. Andere interne Programmierfehler werden nicht pauschal verschleiert.

## Polynomial- und Domainvalidierungstests

Das Phase-1A.2-Modell wird unabhängig vom Parser mit kontrolliert erzeugten
`ExactExpression`-Werten geprüft. Parametrische Tests decken Null- und
Konstantenpolynome, dichte Koeffizienten, rationale Parameterfunktionen,
kanonische Wertgleichheit, Hashbarkeit und tatsächlich verwendete Parameter
ab. Unbenutzte deklarierte Parameter dürfen weder Wertidentität noch internen
SymPy-Domainkontext verändern.

Gradtests unterscheiden `generic_degree` und `guaranteed_degree`. Symbolische
führende Koeffizienten mit unbekannter Nullheit erzeugen
Nichtnullbedingungen; `None` wird niemals als nachweislich ungleich null
interpretiert. Definitionsbedingungen aus Parameternennern und
Gradbedingungen aus normalisierten Zählern werden getrennt, dedupliziert und
deterministisch sortiert geprüft.

Regressionstests sichern die kanonische Feldsemantik auch bei algebraischer
Kürzung. Sie prüfen, dass bereits entfernte Definitionslücken nicht
rekonstruiert werden, verbleibende Nenner Bedingungen erzeugen und
algebraisch gleiche Polynomialwerte dieselbe Gleichheit und denselben Hash
besitzen. Zusammengesetzte Nichtnullbedingungen wie `T**2`, `T1*T2` und
`K**2 - 1` bleiben zulässige Normalformen. Numerische Faktoren und globale
Vorzeichen werden entfernt; eine Faktorisierung in einzelne Bedingungen ist
für Phase 1A.2 nicht vorgesehen.

Fehlertests umfassen ungültige Namen, Symbolkonflikte, nicht deklarierte oder
annahmebehaftete Symbole, negative, nichtganzzahlige und symbolische
Hauptvariablenexponenten, Hauptvariablen im Nenner, Funktionen, Float-Atome,
nicht rationale Koeffizienten und jede `PolynomialLimits`-Grenze. Große
univariate Potenzen werden anhand von Grad und maximaler dichter
Koeffizientenzahl begrenzt, nicht durch eine unnötig exponentielle
Termabschätzung. Gezieltes Monkeypatching prüft die Kapselung erwartbarer
SymPy-, Speicher-, Rekursions- und Überlauffehler, ohne sonstige
Programmierfehler zu verschleiern.

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
