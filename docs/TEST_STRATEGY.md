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

## Rationale Eingabe- und Strukturtreuetests

Die Phase-1A.3a-Tests prüfen den SymPy-freien Rohbaum unabhängig von späterer
Transferfunktionsmathematik. Strukturtests sichern Operandenreihenfolge,
Klammerung, unäre Vorzeichen und Rechtsassoziativität von Potenzen. Besonders
werden algebraisch verwandte, aber syntaktisch verschiedene Eingaben wie
`K/K` und `1`, `K-K` und `0`, vertauschte Produkte sowie `(K/T)/s` und
`K/(T/s)` als ungleiche Bäume geprüft. Exakte Dezimalpunkt- und
Dezimalkommawerte, deterministische Präfixdarstellung, Symbolmengen,
Knotenzahl, Tiefe, Unveränderlichkeit, Gleichheit, Hash und
Dictionary-Key-Verwendung sind ebenfalls abgedeckt.

Identitätstests variieren den erlaubten Symbolkontext bei unverändertem Baum.
Zusätzliche unbenutzte Freigaben dürfen weder gemeinsame noch getrennte
Eingabewerte oder deren Hash verändern. Eingabeform, Hauptvariable und
Baumstruktur bleiben dagegen identitätsbildend. Tests prüfen außerdem, dass
konkrete Knoten nicht über das öffentliche Domain-Facade exportiert werden;
bewusste interne Konstruktion erfolgt über das konkrete Rohbaummodul.

Parsertests behandeln die getrennte Zähler-/Nennerform und den gemeinsamen
Ausdruck separat. Sie prüfen Original- und Normalisierungstext,
Hauptvariable, erlaubte und verwendete Symbole, feldbezogene Diagnosen,
spezifische Leereingaben sowie kombinierte Längen- und Knotenbudgets. Ein
gemeinsamer Ausdruck ohne Division auf oberster Ebene und ein syntaktischer
Nullnenner sind ausdrücklich gültige Rohstrukturen; fachliche
Nennerbedingungen werden in dieser Phase nicht getestet oder abgeleitet.
Monkeypatching belegt, dass eine bereits überschrittene kombinierte Paarlänge
vor jedem Einzelparse diagnostiziert wird. Metadatentests behandeln
Original- und Normalisierungstexte ausschließlich als Provenienz; spätere
Fachlogik darf daraus keine mathematische Aussage rekonstruieren.

## Raw-Transferfunktions- und Revalidierungstests

Phase 1A.3b wird unabhängig vom Parser mit gemeinsamen und getrennten
Rohverträgen geprüft. Parametrische Regeltests decken Addition, Subtraktion,
Multiplikation, verschachtelte Division sowie positive, negative und
Nullpotenzen ab. Strukturtests sichern, dass `K/K` im Snapshot sichtbar
bleibt, skalierte Zähler-/Nennerpaare nicht gemeinsam gekürzt werden und nur
die einzelne Polynomialseite kanonisiert wird.

Defensive Tests manipulieren frozen Dataclasses über `object.__setattr__` und
prüfen unbekannte Typen und Unterklassen, Zyklen, falsche Kinder, Bool-Werte
in Ganzzahlfeldern, ungekürzte oder zu große exakte Zahlen, unsichere und
nicht deklarierte Symbole, ungültige Exponenten, geteilte Teilbäume und
inkonsistente Metadaten. Der Snapshot muss knotenweise von der Quelle
disjunkt sein. Ressourcenfehler in Revalidierung, Rationalisierung und
kontrollierter Übersetzung werden mit stabilen Codes gekapselt.

Bedingungstests unterscheiden verbindlich reine Parameter-Voraussetzungen von
polynomialen Ausschlüssen der Hauptvariablen. Sie prüfen `1/(s+1)`, `1/K`,
`1/(K*s)`, `1/(K*s+1)` und `1/((K-1)*s+T)`, verschachtelte und wiederholte
Divisoren sowie identische und konditionale Nullnenner. Insbesondere werden
führende Koeffizientenbedingungen nicht pauschal als
Transferfunktionsvoraussetzung übernommen. Sortierung, Deduplizierung,
Herkunft, Unveränderlichkeit, Gleichheit, Hash und Dictionary-Key-Verwendung
sind deterministisch geprüft. Regressionstests vergleichen algebraisch gleiche
Raw-Werte mit unterschiedlicher Eingabeprovenienz. Sie sichern, dass
`used_parameter_names` ausschließlich aus Polynomialpaar, Voraussetzungen und
Ausschlüssen folgt, während nur im Ursprung vorkommende Parameternamen im
Snapshot erhalten bleiben. Für gleiche Raw-Werte müssen sämtliche
mathematischen und daraus abgeleiteten öffentlichen Eigenschaften identisch
sein.

Limitfälle decken Rohknoten, Tiefe, Ganzzahlziffern, Exponenten,
rationalisierte Vorkommen, Zwischenausdrücke, Übersetzungsschritte, Grade,
Parameter, Voraussetzungen und Definitionsausschlüsse ab. Tests prüfen
außerdem die Domain→Parsing-Trennung, das Fehlen eines unsicheren Stringpfads
und das Fehlen gemeinsamer `cancel`-/`together`-Operationen in der neuen
Factory. Properness, Pole, Nullstellen und Stabilität bleiben ausdrücklich
außerhalb dieser Testphase.

## Tests der exakten Transferfunktionsreduktion

Phase 1A.3c wird unabhängig vom Parser mit validierten
`RawTransferFunction`-Werten geprüft. Die Akzeptanzmatrix umfasst vollständige
und partielle gemeinsame Polynomfaktoren, numerische Faktoren,
Parameterfaktoren mit Voraussetzungen, identische parametrische Polynome ohne
zusätzliche Annahmen, den Nullzähler, unveränderte Paare und exakt verschiedene
Dezimalbrüche. Sie sichert insbesondere, dass `1/(T*s+1)` nicht durch `T`
normiert wird, während `1/(K*s+K)` bei bereits vorhandenem `K != 0` sicher
normiert werden darf.

Invarianten- und Werttests prüfen factory-only Konstruktion,
Unveränderlichkeit, Gleichheit, Hash und Dictionary-Schlüssel. Voraussetzungen
und Definitionsausschlüsse müssen nach jeder Kürzung unverändert erhalten
bleiben und identitätsbildend sein; Snapshot, Bericht und Herkunft sind keine
Identität. Öffentliche Verträge dürfen keine SymPy-Typen enthalten.

Berichtstests prüfen stabile Schritttypen, exakte Faktoren,
Vorher-/Nachher-Paare, verwendete Voraussetzungen, Reihenfolge und
Determinismus. Limit- und Fehlertests decken jede
`TransferFunctionReductionLimits`-Grenze, manipulierte Raw-Werte,
Ressourcenfehler und die unabhängige Polynomial-Revalidierung ab. Zusätzlich
bleiben Domain→Parsing-Trennung und globale SymPy-Konfiguration unverändert.

Die vollständige Angriffsmatrix des bestehenden Ausdrucksparsers läuft für
die gemeinsame Form und für jedes einzelne Feld der getrennten Form. Sie
umfasst auch ungültige Kommas, implizite Multiplikation und sonstige
nichtmathematische Syntax. Regressionstests führen parallel die unveränderten
Tests von `SafeExpressionParser` aus, damit die gemeinsam genutzte
AST-Validierung weder Operatorsemantik noch Diagnosecodes verschiebt.

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
