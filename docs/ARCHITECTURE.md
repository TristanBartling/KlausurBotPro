# Architekturhypothese

Dieses Dokument beschreibt eine erste, bewusst vorläufige Hypothese. Die
Schichten werden erst angelegt, wenn ein vertikaler Anwendungsfall sie benötigt.
Die Verzeichnisstruktur soll keine noch nicht belegten Abstraktionen vortäuschen.

## Geplante Schichten

1. **Domain-Modelle:** unveränderliche oder kontrolliert veränderbare,
   fachliche Datentypen für Polynome, Matrizen, Systeme und Ergebnisse.
2. **Mathematische Fachlogik:** symbolische und numerische Operationen ohne
   Kenntnis von GUI, Dateien oder Netzwerk.
3. **Application Services und Workflows:** Orchestrierung von Fachoperationen,
   Validierung von Arbeitsschritten und Übergabe strukturierter Ergebnisse.
4. **Workspace und Historie:** benannte Objekte, Provenienz, Versionen,
   Überschreibungen, Verlauf und Verzweigungen.
5. **Quellen- und PDF-Verwaltung:** Manifest, Referenzen, Suche und Öffnen
   belegter PDF-Seiten.
6. **Externe Integrationen:** Adapter für optionale Solver und andere Dienste.
7. **Reporting:** fachlich kompakte Rechenwege und unterschiedliche
   Darstellungsformen auf Basis strukturierter Ergebnisse.
8. **Benutzeroberfläche:** PySide6-Desktopoberfläche, Eingabe und Darstellung.

## Abhängigkeitsrichtung

Abhängigkeiten zeigen nach innen: UI und Integrationsadapter dürfen Application
Services verwenden; diese verwenden Domain und Fachlogik. Der Fachkern kennt
weder PySide6 noch Netzwerkclients, PDFs oder konkrete Persistenz. Reporting
liest strukturierte Ergebnisse, verändert aber nicht deren mathematische
Bedeutung.

## Fachkern und UI

UI-Callbacks nehmen Eingaben entgegen und rufen Application Services auf. Sie
enthalten keine Formeln oder Rechenalgorithmen. Dadurch können Einzelwerkzeuge,
Workflows, Tests und eine spätere Stapelverarbeitung denselben Fachkern nutzen.

## Adapterprinzip

Externe Dienste werden über kleine, fachlich benannte Schnittstellen
abstrahiert. Konkrete Adapter kapseln Authentifizierung, Transport,
Zeitüberschreitungen und Antwortformate. Ein fehlender Adapter oder
Netzwerkfehler darf lokale Berechnungen nicht blockieren. Zugangsdaten kommen
aus lokaler Laufzeitkonfiguration.

## Strukturierte Ergebnisobjekte

Ergebnisse sollen Werte, Voraussetzungen, Zwischenschritte, verwendete
Methoden, Rundungsinformationen, Warnungen, Quellenreferenzen und
Prüfergebnisse getrennt speichern. Text und Formeln werden daraus gerendert,
nicht als alleinige Wahrheit gespeichert. Das konkrete Modell wird in Phase 1
an einem realen vertikalen Anwendungsfall entworfen.

## Implementierter Ausdrucksparser (Phase 1A.1)

Der sichere Ausdrucksparser ist in zwei nach innen gerichtete Pakete getrennt:

- `domain` enthält unveränderliche Diagnosen und `ExactExpression`.
- `parsing` enthält Konfiguration, Ressourcenlimits, Normalisierung und die
  AST-Übersetzung. Es darf `domain` importieren; die umgekehrte Richtung ist
  ausgeschlossen.

Rohe Nutzereingaben werden tokenbasiert normalisiert und mit
`ast.parse(..., mode="eval")` in eine kontrollierte Zwischendarstellung
überführt. Die erlaubte Ausdruckssprache besteht ausschließlich aus Zahlen,
freigegebenen Symbolen, Klammern, unären Vorzeichen und den Operatoren
`+`, `-`, `*`, `/` und Potenzen. Python ergänzt Namen intern um den passiven
AST-Kontext `Load`; er trägt keine ausführbare Semantik. Alle anderen
Sprachkonstrukte werden durch eine explizite Whitelist abgelehnt.

Die Normalisierung fügt unmittelbar benachbarte Ziffernfolgen um ein
Dezimalkomma zuerst zu einem Zahlentoken zusammen. Jedes danach verbleibende
Komma ist unabhängig von der Klammertiefe ungültig. Eine vollständige
Token-Adjazenzprüfung erkennt implizite Multiplikation zwischen Zahlen,
freigegebenen Symbolen und mathematischen Klammergruppen; Multiplikation muss
immer mit `*` geschrieben werden. Unbekannte Funktionsnamen werden dadurch
nicht freigegeben, und Funktionsaufrufe bleiben verboten.

Erlaubte AST-Knoten werden manuell in SymPy-Objekte übersetzt. Weder `eval`
noch `sympify` oder `parse_expr` erhalten Nutzereingaben. Dezimalzahlen werden
direkt aus ihrem geprüften Token als rationale Werte konstruiert, sodass keine
binären Float-Zwischenwerte entstehen.

`ExactExpression` kapselt den SymPy-Ausdruck und stellt der späteren
Anwendungsschicht nur Symbolnamen sowie kanonische Text- und
LaTeX-Darstellungen bereit. Die interne Fachkern-Schnittstelle `_as_sympy()`
ist ausschließlich für kontrollierte mathematische Domain-Module vorgesehen,
nicht für rohe Eingaben oder GUI-Code.

Vor symbolischer Verarbeitung gelten zentral konfigurierbare Grenzen für
Eingabelänge, AST-Größe und -Tiefe, konfigurierte und verwendete Symbole,
Ganzzahlziffern, Exponenten und geschätzte Termanzahl. Eine zu große
`allowed_symbols`-Menge wird bereits bei der Konfiguration abgelehnt, bevor
SymPy-Symbole entstehen. Erwartbare `MemoryError`, `RecursionError` und
`OverflowError` aus Normalisierung, Parsing, Validierung und kontrollierter
SymPy-Erzeugung werden als `PARSE_LIMIT_EXCEEDED` gekapselt. Diese Grenzen
reduzieren Denial-of-Service-Risiken, ersetzen aber keinen harten
Prozess-Timeout.

## Implementiertes Polynomial-Domainmodell (Phase 1A.2)

`Polynomial` ist ein unveränderliches, ausschließlich durch
`PolynomialFactory` erzeugbares Wertobjekt auf Basis von `ExactExpression`.
Rohe Strings und Parserfunktionen sind nicht Teil dieser Domain-Schnittstelle.
Die öffentliche API liefert keine SymPy-Typen. Sie stellt die Hauptvariable,
tatsächlich verwendete Parameter, den kanonischen exakten Ausdruck, dichte
Koeffizienten, Termanzahl, Null- und Konstantensemantik sowie explizite
Bedingungen bereit.

Die mathematische Wertidentität enthält keinen Deklarationskontext:
Unbenutzte erlaubte Parameter werden weder im Wert noch im internen
Koeffizientenkörper gespeichert und beeinflussen Gleichheit und Hash nicht.
Verwendet werden ausschließlich kanonische, annahmenfreie Symbole mit
eindeutigen Namen. Globale SymPy-Annahmen werden nicht verändert.

`Polynomial` verwendet verbindlich kanonische Feldsemantik. Es repräsentiert
den kanonischen mathematischen Wert über `QQ` beziehungsweise
`QQ.frac_field`, nicht die vollständige Provenienz der ursprünglichen Eingabe.
Definitionslücken, die vor oder während der kanonischen algebraischen
Reduktion verschwinden, können aus dem Polynomialwert nicht rekonstruiert
werden. So werden `(K/K)*s + 1`, `((K-1)/(K-1))*s` und
`(K*T/K)*s + 1` zu `s + 1`, `s` beziehungsweise `T*s + 1`; die
ursprünglichen Bedingungen `K != 0`, `K - 1 != 0` und `K != 0` sind nicht
Bestandteil des jeweiligen `Polynomial`.

`PolynomialDegreeInfo` trennt den generischen strukturellen Grad vom
bedingungslos garantierten Grad. Ist die Nullheit des führenden symbolischen
Koeffizienten unbekannt, bleibt `guaranteed_degree` leer und eine
`LEADING_COEFFICIENT_NONZERO`-Bedingung nennt den normalisierten Zähler.
Definitionsbedingungen für rationale Parameterkoeffizienten nennen getrennt
den normalisierten Nenner der kanonisch reduzierten Koeffizientendarstellung.
Bedingungen werden dedupliziert und deterministisch sortiert. Zusammengesetzte
Ausdrücke wie `T**2`, `T1*T2` oder `K**2 - 1` sind dabei zulässige
Nichtnull-Normalformen; numerische Faktoren und globale Vorzeichen werden
entfernt. Eine spätere Zerlegung in faktorisierte Einzelbedingungen wäre eine
Verbesserung der Darstellung, ist aber keine Voraussetzung für die
mathematische Korrektheit.

Eine spätere eingabetreue Rohdarstellung einer `TransferFunction` muss
ursprüngliche Faktoren, Definitionsbedingungen und Provenienz vor der
algebraischen Kürzung separat erfassen. Eine davon getrennte reduzierte
Darstellung darf kanonische Feldsemantik verwenden. Diese eingabetreue
Semantik wird nicht nachträglich in `Polynomial` eingebaut; ein solches
Transferfunktionsmodell ist in Phase 1A.2 noch nicht implementiert.

Vor der kontrollierten SymPy-Konvertierung prüft die Fabrik Namen, Symbole,
Ausdrucksknoten, Float-Atome, Funktionen, Hauptvariablenpotenzen, Nenner und
einen sicheren maximalen Grad. Danach begrenzen eigene `PolynomialLimits`
Grad, dichte Koeffizienten, strukturelle Terme, Parameter und
Koeffizientenkomplexität. Ohne Parameter wird `QQ`, mit tatsächlich
verwendeten Parametern ein alphabetisch aufgebauter `QQ.frac_field`
verwendet. Erwartbare Domain-, SymPy- und Ressourcenfehler werden als
strukturierte Diagnosen gekapselt.

## Implementierte rationale Eingaberepräsentation (Phase 1A.3a)

Vor jeder algebraischen Vereinfachung steht jetzt ein unveränderlicher,
nicht ausführbarer Rohbaum. Seine Knotentypen bilden exakte Zahlen, Symbole,
unäre Vorzeichen, Addition, Subtraktion, Multiplikation, Division und Potenz
direkt ab. Operandenreihenfolge und Verschachtelung bleiben erhalten:
`K/K`, `K-K`, `(K/T)/s` und `K/(T/s)` werden weder ausgewertet noch
untereinander oder mit reduzierten Werten gleichgesetzt. Ausschließlich ein
Zahlenliteral wird exakt als vollständig gekürzter Bruch mit positivem Nenner
gespeichert. Der Baum enthält keine SymPy- oder Python-AST-Typen und bietet
eine deterministische Präfixdarstellung, strukturelle Gleichheit und
Hashbarkeit, Symbolnamen, Knotenzahl und Tiefe.

Die Eingabeform ist durch zwei getrennte Verträge diskriminiert:
`SeparatedTransferFunctionInput` speichert Zähler- und Nennerbaum aus zwei
Feldern, `CommonTransferFunctionInput` genau einen vollständigen Baum. Die
gemeinsame Form verlangt keine Division auf oberster Ebene. Beide Verträge
halten Hauptvariable, freigegebene und tatsächlich verwendete Symbolnamen
sowie Original- und Normalisierungstexte fest. Quelltexte gehören nicht zur
strukturellen Wertgleichheit. Auch die freigegebenen Symbolnamen sind nur
Validierungskontext: Die Wertidentität besteht ausschließlich aus konkreter
Eingabeform, Hauptvariable und vollständigem Rohbaum beziehungsweise beiden
Rohbäumen. Zusätzliche unbenutzte Freigaben ändern Gleichheit und Hash nicht.
Ein mathematisches `TransferFunction`-Modell, Definitionsbedingungen,
Polynome, Kürzung und reduzierte Darstellung sind bewusst noch nicht Teil
dieser Schicht.

Das öffentliche Domain-Facade exportiert `RawAlgebraicExpression` als
Lesetyp, die beiden konkreten Eingabeverträge und ihren gemeinsamen
Union-Typ. Konkrete Knoten wie `Add`, `Divide` oder `Symbol` werden dort nicht
als allgemeine Konstruktions-API angeboten; Parser und kontrollierte interne
Domainmodule importieren sie direkt aus `raw_algebraic_expression`. Dies ist
eine API- und Vertrauensgrenze, keine durch Python-Privatheit erzwungene
Sicherheitsgrenze.

Die Eingabeverträge bleiben frei konstruierbar, weil eine zusätzliche Factory
in dieser Phase nur kosmetische Zugriffskontrolle liefern würde. Ihre lokalen
Invarianten prüfen Typen, Namen und deklarierte Symbole, jedoch keine
`ParserLimits`. Nur parsererzeugte Werte sind nachweislich durch
Normalisierung, AST-Whitelist und Parserlimits gelaufen. Manuell erzeugte
Rohbäume gelten als nicht vertrauenswürdig; eine spätere
`RawTransferFunctionFactory` muss Struktur, Symbole und Ressourcen defensiv
erneut validieren. Sie darf Original- oder Normalisierungstexte niemals als
mathematische Wahrheit auswerten. Fachliche Verarbeitung basiert
ausschließlich auf dem validierten Rohbaum; Texte dienen Anzeige,
Rückverfolgung und späterer Workspace-Provenienz. Bei parsererzeugten Werten
garantiert der Parser die Zuordnung: Originaltexte sind die unveränderten
Eingaben, Normalisierungstexte stammen jeweils aus genau deren erfolgreichem
Normalisierungslauf. Frei konstruierte Werte besitzen diese Garantie nicht.

`SafeExpressionParser` und `SafeRationalExpressionParser` verwenden dieselbe
interne AST-Whitelist, Exponentenprüfung, Komplexitätsschätzung und
Ressourcenpolitik. Der bestehende Parser übersetzt danach weiterhin manuell
nach SymPy und behält seine öffentliche Semantik. Der neue Parser übersetzt
dagegen direkt in den Rohbaum; er durchläuft nie `ExactExpression` oder
SymPy. Deshalb ist beispielsweise ein syntaktischer Nenner `0` in dieser
Phase zulässig und kann erst durch ein späteres Domainmodell fachlich
abgelehnt werden.

Für die getrennte Form gelten `ParserLimits` sowohl je Teilausdruck als auch
als gemeinsames Budget: Die Summe der Eingabelängen und die gesamte AST- und
Rohknotenzahl dürfen die jeweiligen konfigurierten Einzelgrenzen nicht
überschreiten. Die kombinierte rohe Länge wird nach Typ-, Variablen- und
Leerprüfung, aber vor Normalisierung und AST-Erzeugung der Teilfelder
abgelehnt. Gesamte AST- und Rohknotenzahl werden zusätzlich nach beiden
Einzelparsings geprüft. Damit entsteht kein zweiter, abweichender
Sicherheitsvertrag.

## Implementierte validierte RawTransferFunction (Phase 1A.3b)

`RawTransferFunctionFactory` bildet ausschließlich bereits strukturierte
`CommonTransferFunctionInput`- oder `SeparatedTransferFunctionInput`-Werte auf
ein unveränderliches, factory-only `RawTransferFunction` ab. Die
Factorykonfiguration für Hauptvariable und Parameter ist maßgeblich;
Parsermetadaten und Provenienztexte sind keine mathematische Vertrauensquelle.
Der Domainkern importiert dafür weder Parsing noch UI.

Vor jeder mathematischen Übersetzung revalidiert ein internes Modul jeden
logisch auftretenden Rohknoten. Nur exakt bekannte Knotentypen, sichere Felder,
gekürzte exakte Zahlen, sichere deklarierte Symbole und rein numerische,
ganzzahlige, begrenzte Exponenten werden akzeptiert. Zyklische, manipulierte
oder zu große Strukturen werden diagnostiziert. Geteilte Teilbäume sind
zulässig, zählen aber pro logischem Vorkommen. Der erfolgreiche Snapshot
besteht vollständig aus neuen Knoten und besitzt keine Aliasbeziehung zur
Eingabe.

Die interne Rationalisierung folgt mechanisch den Bruchrechenregeln. Sie
erzeugt getrennte Zähler- und Nennerbäume und zeichnet die rationalisierten
Zähler ursprünglicher Divisoren auf. Vor jedem wachsenden Baum werden
Vorkommen, Zwischenausdrücke und Übersetzungsschritte gekappt geschätzt. Es
gibt keine gemeinsame Kürzung, Faktorisierung, GGT-, monische oder skalare
Paar-Normalisierung. Erst anschließend werden beide Seiten getrennt und ohne
Stringpfad in kontrollierte, annahmenfreie SymPy-Ausdrücke übersetzt und
jeweils durch `PolynomialFactory` kanonisiert.

Parameter-Voraussetzungen und Definitionsausschlüsse der Hauptvariablen sind
getrennte öffentliche Prädikate. `EXPRESSION_NONZERO` und `NOT_ALL_ZERO`
betreffen ausschließlich parameterabhängige Koeffizienten. Ein
`TransferFunctionDomainExclusion` enthält dagegen ein validiertes Polynom mit
Hauptvariable, dessen Nullstellen aus ursprünglichen Divisoren oder dem
finalen Nenner ausgeschlossen sind. So erzeugt `1/K` nur `K != 0`,
`1/(s+1)` nur den Ausschluss `s + 1 != 0`, und `1/(K*s)` beides. Die
Gradbedingung eines führenden Polynomialkoeffizienten wird nicht automatisch
zur Gültigkeitsvoraussetzung der Transferfunktion.

Die mathematische Raw-Identität besteht aus Hauptvariable, geordnetem
Zähler-/Nennerpolynom, Voraussetzungen und Definitionsausschlüssen.
Provenienztexte, Eingabeform, Quellpfade, unbenutzte Freigaben und interne
Schritte beeinflussen Gleichheit und Hash nicht. Deshalb können getrennte und
gemeinsame Eingaben denselben Wert erzeugen. Skalare Vielfache bleiben vor
einer späteren Reduktion ungleich. `used_parameter_names` wird ausschließlich
aus dem Polynomialpaar, den Voraussetzungen und den Definitionsausschlüssen
abgeleitet; nur im Ursprungsausdruck vorkommende Parameternamen bleiben über
`input_snapshot.used_symbol_names` zugänglich. Gleiche Raw-Werte besitzen
damit dieselben mathematischen und abgeleiteten Eigenschaften, dürfen aber
unterschiedliche Provenienz-Snapshots besitzen. Properness, Pole, Nullstellen
und Stabilität sind noch nicht implementiert.

## Implementierte exakte Transferfunktionsreduktion (Phase 1A.3c)

`TransferFunctionReducer` überführt ausschließlich eine defensiv erneut
geprüfte `RawTransferFunction` in eine factory-only
`ReducedTransferFunction`. Die Reduktion arbeitet exakt und begrenzt mit einer
multivariaten Polynomdarstellung über `QQ`; sie verwendet weder Parser noch
Strings als mathematische Quelle. Das Ergebnis wird unabhängig durch
`PolynomialFactory` revalidiert.

Die reduzierte Wertidentität besteht aus Hauptvariable, geordnetem reduziertem
Zähler-/Nennerpaar sowie den unverändert übernommenen Voraussetzungen und
Definitionsausschlüssen. Eingabesnapshot, Reduktionsbericht, Diagnosen,
Darstellungstexte und Herkunftsangaben gehören nicht zur Identität.
`used_parameter_names` und `is_zero` werden aus diesen mathematischen Feldern
abgeleitet. Dadurch verschwinden Parameter nicht aus der Semantik, wenn ihr
Faktor zwar gekürzt wurde, aber eine ursprüngliche Voraussetzung oder ein
Ausschluss fortbesteht.

Gemeinsame Polynomfaktoren und gemeinsame rationale Zahlenfaktoren werden
exakt entfernt; das Vorzeichen wird deterministisch normalisiert. Ein
Nullzähler wird zu `0/1`, ohne die Raw-Bedingungen zu verlieren. Eine Division
durch einen symbolischen Skalenfaktor erfolgt nur, wenn eine bereits
vorhandene `EXPRESSION_NONZERO`-Voraussetzung dessen Nichtnullheit beweist.
Insbesondere bleibt `1/(T*s+1)` ohne Voraussetzung `T != 0` unverändert.
Monische Normierung erzeugt keine künstlichen Annahmen. Parameternenner werden
nur unter bereits abgesicherten Definitionen beseitigt.

Jede tatsächliche Transformation wird als geordneter,
`ExactExpression`-basierter Schritt mit Faktor, Vorher-/Nachher-Paar und
gegebenenfalls verwendeter Voraussetzung berichtet. Auch eine unveränderte
Reduktion erhält einen strukturierten `NO_REDUCTION`-Schritt. Eigene Limits
begrenzen Eingabe, multivariate Zwischenrepräsentation, Faktoren, Ergebnis und
Schrittzahl. Erwartbare Limit-, SymPy-, Divisions-, Ergebnis- und
Ressourcenfehler werden als strukturierte Diagnosen gekapselt.

Die Reduktion bestimmt noch keine Properness, Pole, Nullstellen, Stabilität
oder regelungstechnische Analysegrößen.

## Implementierte exakte Pol-/Nullstellenanalyse (Phase 2A)

`TransferFunctionRootAnalyzer` analysiert ausschließlich defensiv
revalidierte `ReducedTransferFunction`-Werte. Parameterfreie Polynome und
vollständig mit gekürzten rationalen Werten belegte Parameter werden über
`QQ` spezialisiert. Fehlende Belegungen erzeugen ein erfolgreiches,
strukturiertes `SYMBOLIC_UNDETERMINED`; partielle oder zusätzliche Belegungen
sind Fehler. Erhaltene `EXPRESSION_NONZERO`- und `NOT_ALL_ZERO`-Prädikate
werden vor der Wurzelbestimmung exakt ausgewertet. Ein Gradabfall bleibt als
strukturierte Warnung sichtbar.

Die exakte Wurzelliste ist fachlich autoritativ. Rationale Faktorisierung,
explizite lineare und quadratische Wurzeln sowie kanonische
`RootOfValue`-Werte für verbleibende höhere irreduzible Faktoren liefern eine
vollständige Liste mit exakten Multiplizitäten. Öffentliche Verträge enthalten
keine SymPy-Objekte. Numerische Real-/Imaginärteile und Residuen sind
ausschließlich nachgelagerte, nicht hashbare Prüfwerte; sie bestimmen weder
Identität noch Multiplizität der exakten Wurzeln. Mehrfachwurzeln, nahe Cluster,
zu große Residuen und fehlende konjugierte Gegenstücke erzeugen strukturierte
Warnungen.

Reduzierte Nullstellen, reduzierte Pole und Nullstellen jedes erhaltenen
Definitionsausschlusses bleiben getrennt. Gleiche Ausschlussorte werden
deterministisch dedupliziert, ohne ihre Herkunft zu verlieren. Die normale
`analyze`-Operation rekonstruiert keine Kürzungen und meldet dafür
`NOT_EVALUATED`. Nur `analyze_reduction` darf aus einem lückenlos
revalidierten `TransferFunctionReductionResult` Orte der ausdrücklichen
`REMOVE_COMMON_POLYNOMIAL_FACTOR`-Schritte ableiten. Parameterreine
Kürzungsfaktoren erzeugen keine Orte der Hauptvariablen.

Eigene Grenzen beschränken Grad, Parameter, Ausdrucks- und Faktorknoten,
RootOf-Anzahl, Ergebniszahl, Substitutionen, Definitionsausschlüsse und
Kürzungsfaktoren. Exakt rationale Substitutionen werden vor jeder
SymPy-Konstruktion einschließlich ihrer Ganzzahlziffern revalidiert.
Numerische `evalf`-Prüfungen verwenden 40 Ergebnisziffern, 12 Schutzziffern
und höchstens 160 temporäre Arbeitsziffern; diese Grenze ist ausdrücklich
keine Iterationsgrenze. Die Phase implementiert weder Stabilität, Properness,
Frequenz- oder Zeitbereichsanalyse noch allgemeine symbolische,
Gleitkomma- oder komplexe Parametersubstitutionen.

## Implementierte quellengebundene Stabilitätsklassifikation (Phase 2B)

`TransferFunctionStabilityAnalyzer` verarbeitet ausschließlich ein bereits
erfolgreiches, defensiv revalidiertes
`TransferFunctionRootAnalysisResult`. Er berechnet keine Wurzeln neu und nutzt
für den Gesamtstatus ausschließlich die reduzierten exakten Pole. `STABLE`
bedeutet, dass alle reduzierten Pole strikt negativen Realteil besitzen, und
entspricht damit E/A-Stabilität. `BORDERLINE_STABLE` verlangt mindestens einen
einfachen Pol auf der imaginären Achse, keinen Pol in der rechten Halbebene und
keinen mehrfachen imaginären Pol; dieser Status ist ausdrücklich nicht
E/A-/BIBO-stabil. Positive Pole und Pole auf der imaginären Achse mit
algebraischer Multiplizität größer als eins führen zu `UNSTABLE`. Nicht exakt
oder zertifiziert entscheidbare Realteilzeichen führen, sofern keine sicher
erkannte Instabilität vorliegt, zu `SYMBOLIC_UNDETERMINED`.

Die öffentliche Phase-2B-API wird vollständig über das Domain-Facade
`klausurbotpro.domain` exportiert; interne Validierungs- und
Klassifikationshelfer bleiben privat. Vor der Klassifikation rekonstruiert die
Stabilitätsanalyse aus reduziertem Nenner und exakten Parametersubstitutionen
mit der vorhandenen Phase-2A-Spezialisierung das erwartete Nennerpolynom. Sie
vergleicht dessen exakten Ausdruck und Grad mit dem Polergebnis und beweist für
jeden gemeldeten Pol Nullstelleneigenschaft, algebraische Multiplizität und
Verschiedenheit der Einträge. Explizite Wurzeln werden durch exakte
Ableitungsauswertung geprüft; bei irreduziblen `RootOfValue`-Polynomen erfolgt
derselbe Nachweis exakt über Polynomreste. Diese Prüfung verändert weder
Wurzeln noch Multiplizitäten und führt keine neue Wurzelsuche aus.

Die defensive Revalidierung verwendet nicht die Standardwerte eines neuen
`RootAnalysisLimits`-Objekts. Endliche interne Phase-2A-Grenzen werden
stattdessen aus `StabilityAnalysisLimits` abgeleitet. Neben Pol-, Ergebnis-,
Ausdrucks- und Evidenzgrenzen beschränken eigene Stabilitätslimits den
Quellpolynomgrad, die Ziffern seiner exakten Ganzzahlen und die Ziffern exakter
Substitutionen. Damit bleiben Ergebnisse mit bewusst erhöhten
Phase-2A-Grenzen zulässig, sofern sie innerhalb des Stabilitätsvertrags liegen.
Ein harter Prozess-Timeout wird weiterhin nicht behauptet.

Explizite Wurzeln werden über den exakten SymPy-Realteil und ausschließlich
dessen exakte Vorzeichenprädikate klassifiziert. `RootOfValue` wird intern aus
seinem primitiven ganzzahligen Polynom und Index rekonstruiert. Nach exakten
öffentlichen Prädikaten darf ein öffentlicher `eval_rational`-Nachweis mit
exakten rationalen Fehlergrenzen das Vorzeichen zertifizieren; schneidet das
begrenzte Intervall beziehungsweise Rechteck weiterhin die imaginäre Achse,
bleibt das Ergebnis unbestimmt. Numerische Phase-2A-Schätzwerte treffen niemals
die Entscheidung. Sie dürfen lediglich einen deutlichen Vorzeichenwiderspruch
zur exakten Klassifikation melden; ein numerischer Rest bei exakt verschwindendem
Realteil wird nicht umklassifiziert.

Erhaltene `DomainExclusions` bleiben unverändert referenziert und sind keine
reduzierten Pole. Nachgewiesene `cancelled_locations` werden getrennt
klassifiziert und können Hinweise auf mögliche verborgene interne Dynamik
erzeugen, verändern aber den Gesamtstatus nicht. Aus dieser
Übertragungsfunktionsanalyse wird keine I-Stabilität des gesamten Regelkreises
abgeleitet.

Die fachliche Semantik ist an drei offizielle Fundstellen gebunden:
`skript.pdf`, Seite 107, Theorem 5.12 für das strikte Polkriterium der
E/A-Stabilität; `skript.pdf`, Seite 102, Korollar 5.5 für die Bedeutung
einfacher Jordanblöcke bei nichtpositiven Realteilen; sowie
`Regelungstechnik_Tutorium_komplett.pdf`, Tutorium 09 – Stabilität I,
Aufgabe 2 für einfache Pole bei null beziehungsweise auf der imaginären Achse
als grenzstabile Fälle. Quellenreferenzen gehören zum Ergebnisnachweis, nicht
zur mathematischen Statusidentität.

## Implementierte punktweise Frequenzganganalyse (Phase 3A.1)

`TransferFunctionFrequencyResponseAnalyzer` verarbeitet ausschließlich eine
defensiv revalidierte `ReducedTransferFunction`, eine endliche streng
aufsteigende Liste nichtnegativer `ExactRationalValue`-Frequenzen und optionale
exakte Parametersubstitutionen. Die Auswertung setzt intern ausschließlich
`s = i*omega` ein. Sie führt weder Parser noch Reduktion, Wurzelsuche oder
Stabilitätsentscheidung erneut aus.

Für jeden Frequenzpunkt werden Zähler und Nenner getrennt exakt spezialisiert.
Erst nach einer exakten Nennernullprüfung entstehen der komplexe Wert, sein
Real- und Imaginärteil sowie das Betragsquadrat
`Re(G)**2 + Im(G)**2`. Erhaltene Voraussetzungen und
Definitionsausschlüsse bleiben wirksam. Ein Nullnenner oder ein bei dieser
Frequenz verschwindender Definitionsausschluss wird als `SINGULAR`
klassifiziert und erzeugt keine erfundenen endlichen Werte. Eine exakte
Nullantwort besitzt den eigenen Status `ZERO_RESPONSE`, Betrag null, einen
strukturierten dB-Wert minus unendlich und keine definierte Phase.

Unvollständige exakte Parameterbelegungen werden punktweise konservativ
behandelt. Verschwindet ein unbelegter Parameter durch die konkrete
Frequenzeinsetzung nachweislich, darf der Punkt vollständig bestimmt werden;
andernfalls bleibt er `SYMBOLIC_UNDETERMINED`. Unbekannte, komplexe,
Gleitkomma- oder nichtkanonische Parameterwerte werden nicht geschätzt.

Numerische Dezimalstrings werden ausschließlich aus den exakten
parameterfreien Ergebnissen abgeleitet und sind keine binäre
Gleitkomma-Identität. Der Betrag wird aus dem exakten Betragsquadrat berechnet,
der dB-Wert numerisch als `20*log10(abs(G))` und die Hauptphase mit
quadrantenrichtiger `atan2`-Semantik im Bereich `(-180°, 180°]`. Es findet
keine Phasenentfaltung statt. Ein numerischer Darstellungsfehler erhält
`NUMERIC_UNDETERMINED`, ohne die exakten Punktwerte zu verwerfen.

Eigene positive Grenzen beschränken Frequenzpunkte und -ziffern, Parameter,
Polynomgrad, Definitionsausschlüsse, Ausdrucksknoten, kumulierte
Zwischenoperationen, numerische Präzision und Dezimalexponenten. Alle
Frequenzen und der vollständige Kontext werden vor der ersten Punktrechnung
validiert. Erwartbare Speicher-, Rekursions- und Überlauffehler werden
strukturiert gekapselt; ein harter In-Process-Timeout wird nicht behauptet.

Die gesamte verschachtelte Eingangsprüfung liegt innerhalb einer klaren
defensiven Validierungsgrenze. Manipulierte Ausdrücke, Polynome,
Voraussetzungen, Definitionsausschlüsse und abgeleitete Kontextfelder können
keine erwartbaren Attribut-, Index-, Typ- oder Wertfehler nach außen tragen.
Ein `FAILED`-Ergebnis enthält ausschließlich seine Fehlerdiagnose; reduzierte
Funktion, Frequenzen, Substitutionen und Punkte bleiben leer, damit keine
ungeprüften Eingaben als vertrauenswürdiger Snapshot erscheinen.

Auch `FrequencyResponsePoint` ist analyzerkontrolliert. Punktstatus,
Wertvollständigkeit und erforderlicher Diagnosecode werden bei der internen
Erzeugung und erneut durch das Gesamtergebnis geprüft. Die Ergebnisdiagnosen
sind exakt die geordnete Konkatenation der Punktdiagnosen. Eine einzige
Statusableitung gilt für Analyzer und Ergebnisvertrag: Nur vollständig
definierte Punkte einschließlich Nullantworten ergeben `COMPLETE`.
`SYMBOLIC_UNDETERMINED` verlangt mindestens einen symbolisch unbestimmten
Punkt und zugleich weder einen vollständig numerischen noch einen
`NUMERIC_UNDETERMINED`-Punkt; bekannte Singularitäten dürfen daneben stehen.
Jede andere erfolgreiche Mischung ist `PARTIAL`, insbesondere ausschließlich
singuläre oder numerisch unbestimmte Ergebnisse.

Die fachliche Grundlage sind `skript.pdf`, Abschnitt 3.3.1, Definition 3.19
für Amplituden- und Phasengang sowie
`Regelungstechnik_Tutorium_komplett.pdf`, Tutorium 04 für `s = i*omega`,
Betrag, Phase, `20*log10(abs(G))` und Ortskurven. Tutorium 06 begründet den
späteren Ausbau. Phase 3A.1 enthält ausdrücklich noch keine automatischen
Frequenzraster, Plotdaten, asymptotischen Bode-Geraden, Standardgliederkennung,
Reserven, Nyquist-Umschlingungen oder Stabilitätsaussagen.

## Implementiertes zertifiziertes logarithmisches Raster (Phase 3A.2a)

`LogFrequencyGridGenerator` verarbeitet ausschließlich exakte positive
`ExactRationalValue`-Grenzen, eine positive ganzzahlige Punktdichte und
optionale streng aufsteigende exakte Zusatzfrequenzen. Er kennt weder eine
`ReducedTransferFunction` noch den Frequenzganganalyzer. Phase 3A.2a erzeugt
deshalb ausschließlich Frequenzkoordinaten und führt keine Betrags-, dB-,
Phasen- oder sonstige Systemauswertung aus.

Für das exakte Verhältnis `r = omega_max / omega_min` und die Punktdichte
`m` ist die Intervallzahl der kleinste positive Integer `N` mit
`r**m <= 10**N`. Die Suche verwendet nur begrenzte rationale Potenzen und
Vergleiche; weder binäre Floats noch Decimal- oder andere numerische
Logarithmen entscheiden über `N`. Die erzeugten Zielpunkte werden durch
Grenzen, Index `k` und Intervallzahl `N` als
`omega_min * r**(k/N)` beschrieben. Innere Ziele sind im Allgemeinen
irrational und werden öffentlich nicht als exakte rationale Werte
ausgegeben.

Eine lokale, explizit gerundete Decimal-Rechnung liefert pro innerem Ziel
einen `ScientificDecimal` mit konfigurierbarer signifikanter Präzision und
Schutzziffern. Dieser kanonische Dezimalwert wird exakt als rationale
`evaluation_frequency` interpretiert. Seine relative Fehlergrenze
`epsilon = 5 * 10**(-grid_precision_digits)` gilt nicht allein aufgrund der
Rundung: Beide Schranken werden nach Potenzieren mit `N` tatsächlich durch
exakte rationale Vergleiche zertifiziert. Zusätzliche Versuche erhöhen nur
begrenzt die internen Schutzziffern; sie verändern nicht die öffentliche
Zielpräzision. Ohne Nachweis entsteht ein strukturiertes Fehlerresultat.

Die beiden Grenzen bleiben als exakte Requestwerte erhalten und besitzen
Fehlergrenze null. Explizite rationale Frequenzen werden ebenfalls exakt
eingefügt. Mathematisch identische Grenz- oder innere Zielpunkte vereinigen
ihre Herkunft deterministisch. Treffen dagegen verschiedene Ziele nach
Rundung auf dieselbe Auswertungsfrequenz oder fällt ein nicht identischer
expliziter Punkt auf einen Kandidaten, scheitert das gesamte Raster
strukturiert; es gibt keine stille Deduplizierung.

Request, Punkte und Ergebnis werden defensiv revalidiert. Erfolgreiche
Ergebnisse besitzen einen vom Eingang disjunkten exakten Requestsnapshot,
vollständige Zielindizes `0..N` und streng aufsteigende rationale
Auswertungsfrequenzen. Fehlerresultate enthalten keine ungeprüften
Requestwerte oder Teilpunkte. Grenzen beschränken Dekaden, Punktdichte,
Gesamt- und Zusatzpunkte, rationale Ziffern, Decimal-Präzision,
Zertifizierungsversuche und -schritte sowie Diagnosen. Ein harter
In-Process-Timeout wird nicht behauptet.

Eine eigene interne Resultatgrenze revalidiert das fertige Raster unabhängig
vom vorangegangenen Generatorlauf. Sie bestimmt die Intervallzahl erneut
exakt, gleicht jeden Ziel- und Zusatzpunkt mit dem Request ab, prüft
Monotonie, Herkunft, Punktzahl, Dezimaldarstellung und Limits und führt für
jeden approximierten inneren Punkt die rationale Fehlerzertifizierung erneut
aus. Manipulierte verschachtelte Werte werden dabei in strukturierte
Rasterfehler übersetzt. Diese Grenze ist für spätere Domainkonsumenten
wiederverwendbar, aber keine neue öffentliche API.

Ist ein inneres logarithmisches Ziel nachweislich rational und zugleich als
exakte Zusatzfrequenz vorhanden, bleibt seine rationale Frequenz unverändert.
Die Herkunft lautet dann `GENERATED` und `EXPLICIT`, die Fehlergrenze ist
exakt null. Nur tatsächlich approximierte innere Ziele besitzen die positive
zertifizierte Schranke. Vollständige Raster besitzen in dieser Phase keine
Punkt- oder globalen Diagnosen; Fehlerresultate enthalten höchstens die
begrenzte strukturierte Fehlerdiagnose. Dadurch wird `max_diagnostics`
tatsächlich an der Resultatgrenze geprüft, obwohl Generatorergebnisse die
Standardgrenze konstruktiv unterschreiten.

Phase 3A.2a enthält ausdrücklich noch keinen Aufruf der punktweisen
Frequenzganganalyse, keine Bode-Plotdaten oder -serien, keine Segmentierung,
keine Phasenentfaltung, keine Reserven, keine Nyquist-Auswertung und keine
Application- oder GUI-Integration.

## Implementierte strukturierte Bode-Plotdaten (Phase 3A.2b)

`TransferFunctionBodeDataAnalyzer` verbindet ein defensiv revalidiertes
logarithmisches Raster mit einer revalidierten `ReducedTransferFunction` und
exakten Parametersubstitutionen. Aus allen geordneten
`evaluation_frequency`-Werten entsteht genau ein `FrequencySampleSet`; der
Analyzer ruft `TransferFunctionFrequencyResponseAnalyzer` genau einmal für
dieses vollständige Tupel auf. Phase 3A.1 bleibt damit die einzige Quelle für
`G(i*omega)`, Real- und Imaginärteil, Betrag, dB und Hauptphase. Phase 3A.2b
führt keine zweite Frequenzgangrechnung aus.

Jeder analyzerkontrollierte `BodePlotPoint` verknüpft den ursprünglichen
`LogFrequencyGridPoint` direkt mit dem zugehörigen
`FrequencyResponsePoint`. Die strukturierte Zielkoordinate
`target_decimal` bleibt von der tatsächlich ausgewerteten exakten rationalen
Frequenz getrennt. Numerischer dB-Wert und Hauptphase werden unverändert
übernommen; insbesondere findet keine Phasenentfaltung statt. Nullantworten
behalten den vorhandenen strukturierten dB-Wert minus unendlich und erzeugen
keine endliche Ersatzkoordinate.

Betrags- und Phasenserien werden unabhängig und ausschließlich in
Rasterreihenfolge segmentiert. Jeder nicht plotbare Punkt beendet das offene
Segment. Dadurch entstehen keine Linien über Nullantworten, Singularitäten
oder symbolisch beziehungsweise numerisch unbestimmte Stellen. Es gibt weder
Interpolation noch asymptotische Bode-Geraden. Ein-Punkt-Segmente bleiben als
fachlich gültige zusammenhängende Bereiche erhalten.

Die unveränderlichen Achsenmetadaten legen Kreisfrequenz in rad/s auf
logarithmischer Skala, Betrag in dB sowie die Hauptphase in Grad im Bereich
`(-180°, 180°]` fest. `BodeDataLimits` begrenzen Rasterpunkte, getrennte
Segmentzahlen, Diagnosen und die akzeptierte bereits vorhandene
Dezimaldarstellung. Die Dezimalgrenze rundet oder kürzt keine
Phase-3A.1-Werte. Vor der Punktanalyse gilt die kleinere Grenze aus
`max_grid_points` und `max_frequency_points`; bei gleichen Werten wird
deterministisch `max_grid_points` als aktive Grenze gemeldet.

Eine interne Vertrauensgrenze revalidiert Raster, vollständiges
Phase-3A.1-Ergebnis, geordnete Punktidentitäten, Statusmatrix, Segmente,
Metadaten, Diagnoseaggregation und alle drei expliziten Limitverträge.
Jeder Segmentpunkt muss dabei durch Objektidentität direkt aus dem durch seine
inklusiven Grenzen bezeichneten Ausschnitt der übergeordneten Punktfolge
stammen; wertgleiche Kopien werden nicht akzeptiert.
Fehlerhafte Kontexte und manipulierte Zwischenergebnisse liefern ein
wertfreies `FAILED`; erfolgreiche Diagnosen folgen Raster, Phase 3A.1,
punktbezogenen Bode-Diagnosen und globalen Bode-Diagnosen in dieser festen
Reihenfolge.

Die eingebetteten Raster- und Frequenzantwortpunkte erhalten bereits alle
strukturierten Werte für einen späteren Rechenweg von `G(s)` über
`s = i*omega`, Punktwert, Real- und Imaginärteil, Betrag, dB und Hauptphase
bis zu charakteristischen Punkten, Unterbrechungen und zusammenhängenden
Bereichen. Phase 3A.2b erzeugt selbst keinen Bericht. Sie enthält außerdem
keine GUI, Plotbibliothek, Phasenentfaltung, Reserven, Nyquist-Auswertung,
Stabilitätsentscheidung oder automatische asymptotische Geraden.

## Implementierte optionale Bode-Phasenentfaltung (Phase 3A.2c)

`BodePhaseUnwrapAnalyzer` projiziert ausschließlich die bereits vorhandenen
Hauptphasensegmente eines defensiv revalidierten
`TransferFunctionBodeDataResult`. Er ruft keine Frequenzganganalyse auf,
verändert keinen `BodePlotPoint` und berechnet weder Betrag noch dB neu. Jeder
entfaltete Punkt und jedes Segment referenziert sein Quellobjekt durch
Identität; die Hauptphase bleibt unverändert erhalten.

Innerhalb jedes Quellsegments wählt eine exakte endliche Dezimalarithmetik den
ganzzahligen 360°-Offset mit dem kleinsten Abstand zur vorherigen entfalteten
Phase. Kandidaten entstehen begrenzt aus Abrunden und Aufrunden des exakten
Quotienten sowie dem vorherigen Offset. Bei einem exakten 180°-Gleichstand
bleibt der vorherige Offset erhalten; der defensive Fallback bevorzugt danach
den kleineren absoluten und schließlich den kleineren ganzzahligen Offset.
Diese Regel ist eine Darlegungskonvention und behauptet keine physikalisch
eindeutige Drehrichtung.

Jedes neue Quellsegment beginnt unabhängig mit Offset null. Unterbrechungen
durch Nullantwort, Singularität oder symbolisch beziehungsweise numerisch
unbestimmte Punkte werden weder verbunden noch interpoliert. Daher entstehen
die Statuswerte `COMPLETE`, `PARTIAL` und `NO_PHASE_DATA` ausschließlich aus
der revalidierten Bode-Quelle und ihren vorhandenen Phasensegmenten.

`BodePhaseUnwrapLimits` begrenzt Segmente, Punkte, absoluten Offset,
Dezimalziffern und Diagnosen ohne Rundung oder Kürzung. Die interne
Resultatgrenze reproduziert Status, Metadaten, Segment- und Punktidentitäten,
Indizes, Offsetrekurrenz, Dezimalwerte und Diagnoseaggregation. Ungültige
Quellen, Manipulationen, Limit- und Ressourcenfehler liefern ein wertfreies
`FAILED`.

Die Projektion kann reale Phasenänderungen von mehr als 180° zwischen zwei
Abtastpunkten nicht eindeutig erkennen. Sie enthält keine Reserven,
Durchtrittsfrequenzen, Nyquist-Auswertung, GUI, Plot- oder Berichtserzeugung.

## Implementierte gemeinsame Transferfunktionsvorbereitung (Phase 3E.1a)

`TransferFunctionPreparationService` bildet die gemeinsame
Application-Pipeline für Requestvalidierung, sicheres Parsing,
`RawTransferFunction`-Erzeugung und exakte Reduktion. Die Pipeline besitzt
eine einzige autoritative Implementierung und führt je Serviceaufruf einen
produktiven Durchlauf aus. Die interne Vertrauensgrenze reproduziert Parsing,
Raw-Erzeugung und Reduktion anschließend defensiv; dies ist keine zweite
konkurrierende Fachimplementierung. Der Service verwendet den
bestehenden `TransferFunctionWorkflowRequest` einschließlich unverändert
erhaltener Parametersubstitutionen, wendet diese während der Vorbereitung
aber nicht an. COMMON und SEPARATED laufen weiterhin ausschließlich über den
vorhandenen `SafeRationalExpressionParser`; es gibt keinen zweiten Parser-,
Raw- oder Reduktionsweg.

Das servicekontrollierte `TransferFunctionPreparationResult` besitzt genau
drei feste Records in der Reihenfolge `PARSE`, `RAW_TRANSFER_FUNCTION`,
`REDUCTION`. Parsefehler ergeben `FAILED`. Raw- und Reduktionsfehler ergeben
`PARTIAL`, weil validierte vorgelagerte Ergebnisse erhalten bleiben. Jede
fehlgeschlagene Stufe blockiert sämtliche Nachfolger. `raw_value` und
`reduced_value` sind ausschließlich abgeleitete Zugriffe auf die vorhandenen
Domainresultate und werden nicht doppelt gespeichert.

Eine interne Vertrauensgrenze revalidiert Requestkontext, Stufenfolge,
Statusmatrix, Teilresultate und Wertherkunft vollständig feldweise.
Parsertexte, normalisierte Texte, erlaubte Symbole und Rohbäume werden nicht
über die bewusst provenanceblinde Eingabegleichheit geprüft. Der erfolgreiche
Raw-Wert referenziert seinen gespeicherten `input_snapshot` identisch als
Preparation-`parsed_input`; Raw-Metadaten, Voraussetzungen und
Definitionsausschlüsse schließen ihre Herkunft ein. Das ReductionResult
referenziert den Raw-Wert identisch; reduzierter Wert und vollständiger
geordneter Bericht einschließlich Faktoren und verwendeter Voraussetzungen
werden streng reproduziert. Zusätzlich prüft die Grenze Diagnoseaggregation
und die bestehenden `TransferFunctionWorkflowLimits`.
Domain-Diagnosen bleiben unverändert in Stufenreihenfolge; genau eine
Application-Diagnose ergänzt einen erwartbaren Stufenfehler. Speicher-,
Rekursions- und Überlauffehler werden an der betroffenen Stufe strukturiert
abgebildet. Interne Programmierfehler werden nicht pauschal maskiert.

`TransferFunctionWorkflowService.run()` verwendet die Preparation genau
einmal und setzt nur bei vollständiger Vorbereitung mit Wurzel- und
Stabilitätsanalyse fort. Overrides und Substitutionsupdates behalten ihre
bisherige Semantik. Ein späterer Frequenzbereichsworkflow kann dieselbe
Vorbereitung verwenden, ohne für reine Bode-Aufgaben unnötig Wurzeln oder
Stabilität zu analysieren.

Phase 3E.1a enthält noch keine Frequenzgang-, Raster-, Bode- oder
Phasenentfaltungsorchestrierung im Application-Layer und keinen Bericht,
Diagramm-, GUI-, Overleaf-, Reserven- oder Nyquist-Ausbau.

Die vollständige defensive Reproduktion verursacht zusätzliche Rechenkosten.
Vor Abschluss der Frequenz-GUI werden diese mit realen Aufgaben und
Laufzeitmessungen geprüft. Die Vertrauensgrenze wird nicht ohne gemessenen
Grund reduziert; Unit-Tests enthalten keine zeitabhängigen Laufzeitgrenzen.

## Implementierter Frequenzbereichs-Application-Workflow (Phase 3E.1b)

`FrequencyDomainWorkflowService` orchestriert vorhandene Domainanalysen ohne
UI-, Bericht- oder Plotabhängigkeit. Der verschachtelte
`TransferFunctionWorkflowRequest` wird unverändert durch genau einen
`TransferFunctionPreparationService` verarbeitet. Root- und
Stabilitätsanalyse gehören nicht zu diesem Workflow.

Der explizite Modus `SINGLE_POINT` wertet genau eine nichtnegative rationale
Kreisfrequenz über genau einen
`TransferFunctionFrequencyResponseAnalyzer`-Aufruf aus. Raster, Bode-Daten
und Phasenentfaltung sind dabei `NOT_APPLICABLE`. Der Modus `BODE` erzeugt
zuerst genau ein zertifiziertes logarithmisches Raster und übergibt es genau
einmal an `TransferFunctionBodeDataAnalyzer`. Nur dieser vorhandene
Phase-3A.2b-Analyzer orchestriert die Bode-Punktwerte über Phase 3A.1; der
Application-Service führt keine zusätzliche Punktanalyse aus.

Die Phasendarstellung ist kein boolesches Merkmal. `PRINCIPAL_ONLY` behält die
vorhandene Hauptphase und markiert die Unwrap-Stufe als `NOT_APPLICABLE`.
`PRINCIPAL_AND_UNWRAPPED` ruft nach erfolgreichen Bode-Daten genau einmal
`BodePhaseUnwrapAnalyzer` auf. Die Entfaltung bleibt eine optionale
Darstellungsprojektion und verändert die Hauptphase nicht.

Jeder gültige Request besitzt fünf Records in der festen Reihenfolge
`PREPARATION`, `SINGLE_POINT_RESPONSE`, `LOG_FREQUENCY_GRID`, `BODE_DATA`,
`PHASE_UNWRAP`. Angeforderte Nachfolger eines Fehlers werden `BLOCKED`;
modusfremde Stufen bleiben `NOT_APPLICABLE`. Applicationstatus und
Domainstatus sind getrennt: singuläre, symbolisch oder numerisch unbestimmte
Einzelpunkte sowie `NO_PLOTTABLE_DATA` und `NO_PHASE_DATA` sind vollständig
ausgeführte Domainresultate und deshalb kein Applicationfehler.

Die interne Vertrauensgrenze revalidiert Requestkombination, Preparation,
Stage-Matrix, explizite Limits und jede Domainübergabe. Reduced-Wert,
Raster-, Bode- und Unwrap-Quellen werden an den erforderlichen Stellen durch
Objektidentität gebunden. Ein ungültiger Frequenzrequest liefert keinen
Requestsnapshot und keine Domainwerte.

Diagnosen gehören jeweils der ersten Application-Stufe, die sie sichtbar
macht. Preparation- und Einzelpunktdiagnosen werden direkt übernommen.
Rasterdiagnosen gehören der Rasterstufe. Da das Bode-Ergebnis Raster- und
Punktdiagnosen bereits einbettet, entfernt die Applicationaggregation genau
den verifizierten Rasterpräfix. Entsprechend besitzt die Unwrap-Stufe nur den
verifizierten Zusatz gegenüber den Bode-Diagnosen. Dadurch bleibt die
Gesamtreihenfolge deterministisch, ohne eingebettete Meldungen doppelt zu
zählen.

Phase 3E.1b implementiert keine Berichte, Renderer, Exporte, Diagramme, GUI,
Overleaf-Struktur, Reserven, Durchtrittsfrequenzen oder Nyquist-Auswertung.

## Implementierter Transferfunktionsworkflow (Phase 2C.1)

Die UI-unabhängige Application-Schicht orchestriert den vorhandenen sicheren
Parser und die vier Domainstufen Raw-Erzeugung, Reduktion, Wurzelanalyse und
Stabilitätsanalyse. Die ersten drei Schritte werden durch die gemeinsame
Preparation-Pipeline bereitgestellt. COMMON- und SEPARATED-Eingaben verwenden
ausschließlich `SafeRationalExpressionParser`; es existiert kein zweiter
Parser- oder String-zu-SymPy-Pfad. Parser-, Domain- und
Application-Diagnosen bleiben als strukturierte Objekte erhalten.

Jeder unveränderliche Workflowzustand enthält fünf Records in fester
Stufenreihenfolge. Der Endstatus `NOT_EVALUATED`, `SUCCEEDED`, `FAILED` oder
`BLOCKED` ist von der Wertherkunft `COMPUTED` oder `OVERRIDDEN` getrennt.
Invalidierung ist ausschließlich ein interner Übergang: gespeichert wird nach
der synchronen Neuberechnung nur der neue Endzustand. Ein fachlich
erfolgreiches `SYMBOLIC_UNDETERMINED` bleibt deshalb `SUCCEEDED`.

Schlägt eine Stufe fehl, bleiben alle davor entstandenen Parser- und
Domainteilresultate referenziert; spätere Stufen sind `BLOCKED`. Diagnosen
werden primär je StageRecord gehalten und daraus ohne Umformulierung,
Deduplizierung oder Umsortierung aggregiert. Eine nichtnegative,
deterministische Operationssequenz ersetzt Zeitstempel und Zufallskennungen.

Raw-, Reduced- und Root-Overrides besitzen explizite Provenienz. Ein
Raw-Override verwirft Reduced- und Root-Overrides, ein Reduced-Override erhält
Raw und verwirft Root, ein Root-Override erhält beide Upstream-Overrides.
Substitutionsänderungen erhalten Raw und Reduced und berechnen Root und
Stabilität neu. Jeder Override wird durch die vorhandenen defensiven
Domainpfade revalidiert. Ein unabhängiger Reduced-Override wird als aktiver
Wert geführt, ohne fälschlich einen Reduktionsbericht oder eine Herleitung aus
dem Raw-Wert zu behaupten. Stabilität ist nicht direkt überschreibbar.

Phase 2C.1 führt keine Revisionen, Wiederherstellung, Serialisierung,
Persistenz, GUI, PDF-/Quellenfunktionen oder neue Fachverfahren ein.

Follow-up-Operationen behandeln einen vorhandenen Workflowzustand als neue
Vertrauensgrenze. Vor Substitutionsänderungen und Overrides werden Request,
Operationssequenz, fünf StageRecords, Diagnoseaggregation sowie sämtliche
Parser- und Domainresultate unabhängig revalidiert. Manipulierte oder fremde
Zwischenwerte werden nicht weiterberechnet; der Rückgabestate enthält dann
keinen aktiven mathematischen Wert. Falsche Top-Level-Python-Typen werden
dagegen unmittelbar mit `TypeError` abgelehnt.

Das aggregierte Diagnoselimit reserviert deterministisch einen Platz für den
Application-Limitfehler. Bei einem Überlauf bleiben alle vollständig
abgeschlossenen früheren Stufen und Teilresultate erhalten. Nur die zuerst
betroffene Stufe wird als fehlgeschlagen markiert und noch nicht ausgeführte
Folgestufen werden blockiert. Abgelehnte Folgeoperationen verändern ihre
bereits revalidierten mathematischen Werte auch bei Diagnoseüberlauf nicht.

## Implementierter Transferfunktions-Lösungsbericht (Phase 2C.2)

Ein UI-unabhängiger Application-Builder übersetzt einen defensiv validierten
`TransferFunctionWorkflowState` in einen unveränderlichen, SymPy-freien und
papierübertragbaren Bericht. Er führt den Workflow nicht erneut aus und
berechnet weder Reduktionen noch Wurzeln, Realteile oder Stabilität neu.
Autoritativ sind ausschließlich die bereits vorhandenen Raw-, Reduced-,
Root- und Stability-Verträge.

Der Builder erhält seine `TransferFunctionWorkflowLimits` explizit als
Konfiguration und revalidiert den State ausschließlich unter diesen Grenzen.
Service und Builder können dadurch denselben Limitvertrag verwenden.
Fehlgeschlagene Domainresultate werden mit denselben Grenzen unabhängig
revalidiert; der Stage-Status unterdrückt keinen Validierungsfehler.

Die feste Abschnittsfolge reicht von Eingabe und Übertragungsfunktion über
Reduktionsschritte, Voraussetzungen, Definitionsausschlüsse, Substitutionen,
Nullstellen und Pole bis zu Realteilen, Stabilitätsaussage, Quellen und
Workflowhinweisen. Exakte Werte stehen stets vor optionalen numerischen
Näherungen. Jeder vorhandene Reduktionsschritt wird mit Vorher-/Nachher-Paar,
Operation, Faktor, verwendeten Voraussetzungen und erhaltenen
Definitionsausschlüssen abgebildet. Eine vollständig gekürzte
Definitionslücke bleibt dadurch sichtbar.

Aktive Raw-, Reduced- und Root-Overrides erscheinen mit Ziel, Herkunftsart und
sichtbarem Grund. Ein Reduced-Override ohne Reduktionsbericht wird ausdrücklich
nicht als Herleitung aus dem Raw-Wert dargestellt. Ein Root-Override steht in
den Nullstellen- und Polabschnitten jeweils vor den übernommenen Ergebnissen.
Fehlgeschlagene und
blockierte Workflowstufen erzeugen einen Teilbericht bis zur letzten
erfolgreichen Fachstufe. `SYMBOLIC_UNDETERMINED` bleibt dagegen ein
vollständiges fachliches Ergebnis.

Plaintext/Unicode und ein LaTeX-Fragment werden ausschließlich aus demselben
strukturierten Bericht gerendert. Beide Renderer sind rein darstellend und
verändern den Bericht nicht. Workflowdiagnosen behalten ihre strukturierte
Severity; beide Renderer kennzeichnen `INFO`, `WARNUNG` und `FEHLER`
deterministisch. Quellen werden nur aus vorhandenen
`StabilitySourceReference`-Werten übernommen; der Builder führt keine
Dateisuche aus und enthält keine zweite Quellenliste. Der Quellenabschnitt
folgt dem Status der Stability-Stufe und unterscheidet vollständig, nicht
anwendbar, fehlgeschlagen und blockiert. Eigene positive
Darstellungslimits verhindern stille Kürzung einzelner Ausdrücke oder
mathematischer Aussagen. Phase 2C.2 führt keine GUI, PDF-Erzeugung,
Dateispeicherung, Serialisierung oder neue Fachrechnung ein.

## Implementierter Transferfunktions-Arbeitsbereich (Phase 2D.1)

Das PySide6-Hauptfenster enthält genau einen Transferfunktions-Arbeitsbereich.
Widgets sammeln ausschließlich einfache Rohwerte und zeigen vorhandene
Application-Verträge an. Sie importieren weder Domain-Analyzer, Parsing noch
SymPy und führen keine mathematische Operation aus.

Eine Qt-unabhängige `TransferFunctionRequestFactory` bildet unveränderliche
`TransferFunctionInputDraft`- und `ParameterInputDraft`-Werte auf einen
vollständigen `TransferFunctionWorkflowRequest` ab. Exakte rationale
Parameterwerte werden vor jeder `int`-Konvertierung begrenzt, ohne Float- oder
Ausdrucksparsing erstellt und bei Fehlern vollständig verworfen.
`TransferFunctionRequestFieldError` erhält eine stabile Feld- und
Zeilenzuordnung für den UI-Fokus.
RequestFactory und autoritative Workflowvalidierung verwenden dieselbe
private Application-Prüfung für sichere Identifier: exakter `str`-Typ,
`isidentifier()`, kein Python-Schlüsselwort und weder beginnendes noch
endendes `__`. Die effektive Parametergrenze ist die kleinste direkt
einschlägige Parser-, Raw-, Reduktions- und Wurzelanalysegrenze. Auch die
Tabellenzeilenzahl wird vor ihrer Verarbeitung durch diese endliche Grenze
beschränkt. Für rationale Substitutionen gilt konservativ die kleinste
Ganzzahlzifferngrenze aus Parser, Raw-, Wurzel- und Stabilitätsanalyse.

Ein Presenter besitzt den unveränderlichen, widgetfreien
`TransferFunctionViewState`. Er koordiniert RequestFactory, RUNNING-Sperre,
Workerergebnisse, Berichtsansicht, Fehlerfokus und Clipboardinhalt, rechnet
aber keine fachliche Aussage neu. Teilresultate bleiben über den vorhandenen
Workflow-State und `TransferFunctionSolutionReport` sichtbar.

Ein persistenter `QObject`-Worker läuft in genau einem dedizierten `QThread`
pro MainWindow. Er verwendet dieselben `TransferFunctionWorkflowLimits` für
WorkflowService und ReportBuilder sowie dieselben expliziten
`SolutionReportLimits` für den Bericht. Requests und unveränderliche
`TransferFunctionWorkflowExecutionResult`-Werte passieren die Threadgrenze
über Qt-Signale; Widgets werden ausschließlich im GUI-Thread verändert.
Während einer Berechnung wird keine zweite Ausführung angenommen.

Beim Schließen während einer laufenden Berechnung wird der Vorgang nicht
gewaltsam abgebrochen. Das Fenster bleibt mit sichtbarem Hinweis offen und
schließt nach dem Ergebnis automatisch über `thread.quit()` und
`thread.wait()`. `terminate()` wird nicht verwendet. Die In-Process-Grenzen
behaupten weder einen harten Timeout noch sichere Unterbrechbarkeit laufender
SymPy-Arbeit.

Die GUI zeigt die fünf Workflowstufen mit Textstatus und unveränderter
DiagnosticSeverity. Severitysymbol, Severitytext und Meldung stammen
deterministisch aus der ersten Diagnose der höchsten vorhandenen Severity.
Strukturierte Kernergebnisse sowie die exakten Plaintext- und
LaTeX-Renderergebnisse bleiben unverändert. Ein unerwarteter Workerfehler
verwirft State, Zusammenfassungen und Berichte des vorherigen Laufs, während
ein Requestfehler vor Workerstart das klar gekennzeichnete vorherige Ergebnis
weiter anzeigen darf. Phase 2D.1 enthält weiterhin keine Overrides, Historie,
Persistenz, Dateien, PDFs, Quellenbrowser oder Diagramme.

Die Darstellungshärtung aus Phase 2D.1a übersetzt interne Abschnittsstatus,
Workflowstufen und Override-Herkünfte über explizite typbezogene Tabellen.
`source_role` bleibt Bestandteil des strukturierten Berichts, wird aber weder
im papierorientierten Renderer noch in der Ergebniszusammenfassung
ungefiltert angezeigt. Root-Gleichungen erhalten die fachlichen Bezeichnungen
„Nullstellenbedingung“ und „Polgleichung“. Leere Voraussetzungen und
Definitionsausschlüsse erscheinen als „keine“.

Beim Start eines gültigen Requests erzeugt der Presenter einen frischen
RUNNING-State ohne frühere Workflow- oder Berichtswerte. Alle Eingabewidgets
bleiben inhaltlich unverändert, werden aber bis zum Ergebnis deaktiviert.
Stufen zeigen währenddessen ausschließlich „Berechnung läuft“. Punktbasierte
Qt-Schriftgrößen, fontmetrisch abgeleitete Zeilenhöhen, inhaltsbezogene
Tabellenspalten und verstellbare Splitter verbessern die DPI-taugliche
Lesbarkeit. Der zweite Berichtstab ist ausdrücklich als
„LaTeX-Quelltext“ ohne Vorschaufunktion gekennzeichnet.

## Offene Architekturentscheidungen

- genaue Grenzen und Repräsentationen weiterer Domain-Modelle
- Erweiterung der bewusst kleinen Parsergrammatik für spätere Datentypen
- Strategie für unveränderliche Workspace-Versionen und Verzweigungen
- Serialisierungsformat und Migrationskonzept
- Plugin- oder Registry-Modell für Werkzeuge und Workflows
- Erweiterung des Lösungsberichts auf spätere fachliche Workflows
- PySide6-Version, unterstützte Python-Versionen und Packaging
- Prozess- oder Thread-Grenzen für lange Berechnungen
- optionale Abhängigkeit und Rolle von `python-control`
- technisch nachweisbare Trennung des Klausur-Builds von KI-Funktionen
