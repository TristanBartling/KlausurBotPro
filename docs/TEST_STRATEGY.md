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

## Tests der exakten Pol-/Nullstellenanalyse

Phase 2A wird direkt mit validierten `ReducedTransferFunction`-Werten und in
Integrationsfällen mit echten `TransferFunctionReductionResult`-Werten
geprüft. Die Akzeptanzmatrix umfasst lineare, quadratische, kubische,
wiederholte, komplex-konjugierte und höhere irreduzible Wurzeln,
Null- und Konstantpolynome sowie getrennte Zähler-/Nennerfälle. Für jede
vollständige exakte Wurzelliste muss die Summe der Multiplizitäten dem
tatsächlichen Grad entsprechen. Höhere nicht sinnvoll explizite Wurzeln
werden als kanonische, SymPy-freie `RootOfValue`-Werte geprüft.

Substitutionstests decken vollständige rationale Belegungen, fehlende und
zusätzliche Parameter, Gradabfall sowie verletzte `EXPRESSION_NONZERO`- und
`NOT_ALL_ZERO`-Voraussetzungen ab. Ohne Belegung bleibt ein parametrischer Fall
erfolgreich und strukturiert unbestimmt. Gleitkomma-, komplexe und partielle
Belegungen werden nicht durch schwächere Erwartungen simuliert. Manipulierte
Zuweisungen, Bool-Werte, nicht gekürzte Brüche, unsortierte oder doppelte
Parameter und zu große Ganzzahlen werden vor der SymPy-Konstruktion defensiv
abgelehnt.

Definitions- und Integrationstests halten reduzierte Pole/Nullstellen,
erhaltene Ausschlussorte und gekürzte Orte auseinander. Sie prüfen
parameterabhängig konstante und identisch verschwindende Ausschlusspolynome,
leeren Definitionsbereich, Herkunftserhalt sowie die Regel, dass nur
nachgewiesene gemeinsame Polynomfaktor-Schritte Kürzungsorte erzeugen.
Manipulierte reduzierte Werte und lückenhafte Berichte müssen defensiv
scheitern. Das schließt leere oder falschstellige Voraussetzungen,
nichtkanonische Herkunftsangaben, Duplikate und parameterreine
Definitionsausschlüsse ein.

Numerische Tests setzen jede autoritative exakte Wurzel in ihr Polynom ein und
prüfen absolutes und skaliertes Residuum. Weitere Fälle sichern
Konjugiertenprüfung, strukturierte Warnungen für Mehrfachwurzeln und nahe
Cluster sowie deterministische Reihenfolge. Numerische Ergebnisse werden
nicht toleranzbasiert gleichgesetzt und bleiben absichtlich nicht hashbar.
Dezimaltexte werden wertbasiert kanonisiert. Tests unterscheiden außerdem
angeforderte Präzision, Schutzziffern und die maximale temporäre
`evalf`-Arbeitspräzision; letztere ist keine Iterationsgrenze.
Limit- und Ressourcentests prüfen strukturierte Diagnosen, ohne exakte
Erwartungen oder bestehende Tests abzuschwächen.

## Tests der quellengebundenen Stabilitätsklassifikation

Phase 2B wird ausschließlich mit erfolgreichen, strukturellen
`TransferFunctionRootAnalysisResult`-Werten geprüft. Die Akzeptanzmatrix
umfasst strikt linke reelle und komplexe Pole, rechte Pole, einfache und
mehrfache Pole bei null sowie einfache und mehrfache konjugierte Pole auf der
imaginären Achse, polfreie Übertragungsfunktionen, symbolisch unbestimmte
Phase-2A-Ergebnisse und sicher instabile Fälle mit zugleich unbestimmten Polen.
Sie sichert `STABLE` als E/A-stabil und
`BORDERLINE_STABLE` ausdrücklich als nicht E/A-/BIBO-stabil.

Klassifikatortests prüfen explizite rationale und algebraische Wurzeln sowie
`RootOfValue` über exakte SymPy-Prädikate und den öffentlichen zertifizierten
`eval_rational`-Pfad. Ein nach begrenzter Verfeinerung die imaginäre Achse
schneidender Nachweis bleibt konservativ `UNDETERMINED`. Numerische
Phase-2A-Werte werden manipuliert, um zu belegen, dass sie den Status niemals
festlegen, bei deutlichem Widerspruch nur warnen und einen exakt verschwindenden
Realteil nicht umklassifizieren.

Integrations- und Manipulationstests sichern, dass reduzierte Nullstellen,
erhaltene `DomainExclusions` und gekürzte Stellen keinen Einfluss auf den
Gesamtstatus besitzen. Nichtnegative und unbestimmte gekürzte Stellen erhalten
separate Hinweise ohne Behauptung interner Instabilität oder I-Stabilität.
Defensive Revalidierung umfasst Typen, Status, Quellenrollen, zusammenhängende
Indizes, positive Multiplizitäten, vollständige Grade, numerische Zuordnung,
Substitutionen, Gruppen und Diagnosen. Jede `StabilityAnalysisLimits`-Grenze
und erwartbare Ressourcenfehler besitzt einen strukturierten Testpfad.
Zusätzliche Manipulationstests ersetzen Nennerquelle, Polwerte,
Multiplizitäten und RootOf-Werte oder duplizieren gleiche algebraische Wurzeln
auch über verschiedene Darstellungen. Die unabhängige Prüfung muss jeden
solchen Widerspruch exakt erkennen. Korrekte explizite und RootOf-Wurzeln
werden dagegen über Ableitungswerte beziehungsweise irreduzible Polynomreste
bestätigt. Regressionstests sichern außerdem, dass benutzerdefinierte
Phase-2A-Grad- und Substitutionsgrenzen innerhalb des Stability-Vertrags
akzeptiert und zu große Werte vor teurer SymPy-Verarbeitung begrenzt werden.
Vertragstests decken Unveränderlichkeit, kontrollierte Ergebniskonstruktion,
mathematische Gleichheit und Hash sowie die exakten drei offiziellen
Quellenreferenzen und alle öffentlichen Exporte des Domain-Facades ab. Der neue
Fachkern enthält keine Parsing-, UI-, Properness-, Hurwitz-, Routh- oder
Nyquistfunktion und verändert keine globale SymPy-Konfiguration.

## Tests des Transferfunktionsworkflows

Phase 2C.1 wird als UI-unabhängige Integration der bestehenden Parser- und
Domainverträge geprüft. COMMON und SEPARATED müssen für denselben
mathematischen Inhalt denselben reduzierten Wert sowie dieselben reduzierten
Pole und Nullstellen liefern. Parametrisierte Fälle prüfen sowohl erfolgreiches
`SYMBOLIC_UNDETERMINED` ohne Belegung als auch exakte rationale
Substitutionen.

Fehlertests erzwingen Parser-, Raw-, Reduktions-, Root- und
Stabilitätsfehler. Jede spätere Stufe muss `BLOCKED` sein, während sämtliche
vorherigen Teilresultate erhalten bleiben. Diagnoseprüfungen vergleichen die
unveränderten Domainobjekte und ihre feste Aggregationsreihenfolge. Eigene
Tests decken Request-, Diagnose-, Provenienz-, Begründungs- und
Operationssequenzlimits ab.

Override-Tests revalidieren Raw-, Reduced- und Root-Werte unabhängig, lehnen
abweichenden Variablen-, Parameter-, Reduced- oder Substitutionskontext
strukturiert ab und prüfen jede Invalidierungsregel. Ungültige Overrides
dürfen den aktiven mathematischen Zustand nicht verändern. Determinismustests
vergleichen gleiche Runs und Operationsfolgen ohne Zeit-, Zufalls- oder
Objektadressabhängigkeit. Importtests erlauben `application → domain/parsing`,
verbieten `domain → application` und schließen PySide6 sowie rohe SymPy-
Parsingpfade aus.

Manipulationstests verändern Requests und Workflowstates gezielt mit
`object.__setattr__`. Sie prüfen falsche Top-Level-Typen, String-Unterklassen,
Stage-Reihenfolge, Diagnoseaggregation, Operationssequenz, fremde Raw-,
Reduced-, Root- und Stability-Ergebnisse sowie widersprüchliche
Status-/Ergebniskombinationen. Vor einer Folgeoperation muss jeder solche
State strukturiert abgelehnt werden, ohne einen unvalidierten mathematischen
Wert weiterzuverwenden.

Diagnoselimitregressionen erzwingen Überläufe in Parse-, Root- und
Stability-Stufe sowie bei einem abgelehnten Override. Die betroffene Stufe
erhält genau den strukturierten Limitfehler, frühere Teilresultate bleiben
erhalten, spätere Stufen sind blockiert und die aggregierte Anzahl bleibt
innerhalb des konfigurierten Limits.

## Tests des Transferfunktions-Lösungsberichts

Phase 2C.2 wird ausschließlich als Übersetzung vorhandener Workflowwerte
geprüft. Strukturtests sichern unveränderliche, hashbare und SymPy-freie
Zeilen, die feste Abschnittsreihenfolge, exakte Werte vor optionalen
Näherungen sowie deterministische Gleichheit ohne Operations- oder
Diagnoseprovenienzsequenzen.

Die Akzeptanzmatrix umfasst ungekürzte, vollständig und teilweise gekürzte
Funktionen, erhaltene Definitionslücken, Nullzähler, rationale, komplexe und
`RootOf`-Pole, fehlende und vollständige Parameterbelegungen sowie stabile,
grenzstabile, instabile und symbolisch unbestimmte Ergebnisse. Strukturierte
Assertions prüfen Wurzelmultiplizitäten, spezialisierte Polynome,
Reduktionsschritte, Voraussetzungen, Definitionsausschlüsse und die Trennung
gekürzter Stellen von reduzierten Polen.

Override-Tests verlangen sichtbare Raw-, Reduced- und Root-Herkunft. Ein
Reduced-Override darf keinen erfundenen Reduktionsschritt enthalten. Ein
Root-Override muss vor den mathematischen Werten in Nullstellen- und
Polabschnitt sowie in beiden Renderern erscheinen.
Teilberichtstests erzwingen Parser-, Reduktions-, Root- und
Stabilitätsfehler; manipulierte States dürfen keine mathematischen Werte in
den Fehlerbericht übernehmen. Jede Reportgrenze besitzt einen strukturierten
Überlaufpfad ohne stilles Abschneiden.

Rendererprüfungen vergleichen alle strukturierten Gleichungen und Ergebnisse
mit Plaintext und LaTeX, prüfen deterministische Leerzeilen sowie sicheres
Escaping und stellen sicher, dass beide Ausgaben denselben mathematischen
Inhalt besitzen. Quellenzeilen werden exakt gegen die vorhandenen
`StabilitySourceReference`-Werte geprüft; nicht vorhandene Fundstellen werden
nicht ergänzt. Workflowdiagnosen müssen ihre exakte Severity behalten; beide
Renderer geben `INFO`, `WARNUNG` und `FEHLER` identisch aus. Complete-,
fehlgeschlagene und blockierte Stability-Stufen sowie ein erfolgreiches
Ergebnis ohne Quellen sichern den Quellenstatus. Workflowlimit-Tests verwenden
dieselbe Konfiguration in Service und Builder und lehnen denselben State unter
strengeren Buildergrenzen ab. Manipulierte fehlgeschlagene Root- und
Stability-Ergebnisse werden unabhängig revalidiert. Architekturtests schließen
UI-Abhängigkeiten, rohe
SymPy-Stringpfade und Domain→Application-Abhängigkeiten weiterhin aus.

## Tests des Transferfunktions-Desktoparbeitsbereichs

Phase 2D.1 wird ohne neue Testabhängigkeit auf fünf Ebenen geprüft. Die
Qt-unabhängige RequestFactory deckt unbelegte, ganzzahlige und rationale
Parameter, kanonische Kürzung, ungültige Zeilen, doppelte und unsichere Namen,
Variablenkonflikte sowie Parameter- und Ziffernlimits ab. Insbesondere werden
Float-, Dezimal- und Exponentialnotation vor jeder `int`-Konvertierung
abgelehnt und kein Teilrequest erzeugt. Regressionstests gleichen Dunder-,
Schlüsselwort-, Leerzeichen- und sichere Unicode-Identifier mit der
Workflowvalidierung ab. Benutzerdefiniert unterschiedliche Parser-, Raw-,
Wurzel- und Stabilitätsgrenzen sowie große leere Zeilentupel prüfen die
konservative Begrenzung vor Iteration und Konvertierung. String-Unterklassen,
nicht-tupelförmige Zeilen und `bool`-Werte werden defensiv abgelehnt.

Presenter-Tests verwenden einen synchron angeschlossenen Fake-Empfänger. Sie
prüfen unveränderliche View-States, RUNNING-Sperre, strukturierte
Fokuszuordnung, Erhalt vorheriger Resultate bei neuer ungültiger Eingabe,
Berichtsumschaltung, exakten Clipboardinhalt und Reset. Erwartbare
Workflowfehler bleiben strukturierte Ergebnisse; unerwartete Workerfehler
erscheinen ohne Traceback im normalen Ergebnisbereich und entfernen State,
Berichte und kopierbaren Inhalt eines früheren erfolgreichen Laufs.

Workspace-Tests laufen mit dem vorhandenen `QApplication` im Offscreen-Modus.
Sie prüfen COMMON/SEPARATED ohne Textverlust, Parameterzeilen, Buttons,
Feldfokus, fünf textuelle Stufenstatus, Severity ohne reine Farbcodierung,
die zur höchsten Severity gehörende erste Meldung, Teilresultate,
Plaintext-/LaTeX-Tabs, Clipboard und Reset. Ein Fehler-Smoke prüft, dass nach
einem unerwarteten Workerfehler Zusammenfassungen, Stufen, beide Berichte und
die Copy-Aktion zurückgesetzt sind. Importtests
verbieten Domain-Analyzer, Parsing und SymPy in allen UI-Modulen.

Phase 2D.1a ergänzt Regressionen aus dem ersten manuellen Sichttest:
Zusammenfassungen und Renderer dürfen keine internen Rollen- oder Statuswerte
anzeigen, Root-Gleichungen besitzen eindeutige deutsche Bezeichnungen und
leere Abschnitte werden verständlich deutsch dargestellt. RUNNING-Tests
prüfen den leeren Ergebnis-State, „Berechnung läuft“ in allen Stufen sowie die
Sperre sämtlicher Eingaben bei unverändertem Text. Nach dem Ergebnis werden
die Eingaben wieder aktiviert. Weitere Tests decken den
„vorheriges Ergebnis“-Hinweis bei Factoryfehlern, den
„LaTeX-Quelltext“-Tab samt Tooltip, punktbasierte Schriftvergrößerung,
fontmetrische Mindesthöhen und weiterhin verstellbare Splitter ab. Es gibt
keine pixelgenauen Screenshotassertionen.

Wenige echte `QThread`-Integrationstests verwenden `QSignalSpy` zusammen mit
einer endlichen Qt-Eventloop-Grenze statt `sleep()`. Sie prüfen einen
vollständigen Workflow, den unveränderlichen Transportwert, identische
Workflowlimits in Service und Builder, strukturierte unerwartete Fehler und
sauberes Threadende. MainWindow-Tests decken Aufbau, Shortcuts, Leerlauf-
Shutdown und zurückgestelltes Schließen während RUNNING ab. Ein echter
Offscreen-End-to-End-Smoke berechnet `1/(s+1)`, prüft Pol, Stabilität und
Bericht und beendet das Fenster über `shutdown()`.

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
