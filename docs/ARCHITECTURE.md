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
Kürzungsfaktoren. Die Phase implementiert weder Stabilität, Properness,
Frequenz- oder Zeitbereichsanalyse noch allgemeine symbolische,
Gleitkomma- oder komplexe Parametersubstitutionen.

## Offene Architekturentscheidungen

- genaue Grenzen und Repräsentationen weiterer Domain-Modelle
- Erweiterung der bewusst kleinen Parsergrammatik für spätere Datentypen
- Strategie für unveränderliche Workspace-Versionen und Verzweigungen
- Serialisierungsformat und Migrationskonzept
- Plugin- oder Registry-Modell für Werkzeuge und Workflows
- einheitliches Modell für Rechenweg, Provenienz und Quellenreferenzen
- PySide6-Version, unterstützte Python-Versionen und Packaging
- Prozess- oder Thread-Grenzen für lange Berechnungen
- optionale Abhängigkeit und Rolle von `python-control`
- technisch nachweisbare Trennung des Klausur-Builds von KI-Funktionen
