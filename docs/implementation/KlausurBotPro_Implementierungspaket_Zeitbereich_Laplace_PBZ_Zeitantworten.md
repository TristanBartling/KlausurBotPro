# KlausurBotPro – Implementierungspaket Zeitbereich

## Laplace-Transformation, Partialbruchzerlegung und Zeitantworten

**Status:** implementierungsfertige Fach- und Schnittstellenspezifikation, codefrei  
**Nicht enthalten:** Softwareimplementierung, Codex-Prompt, allgemeine ODE- oder CAS-Engine  
**Maßgebliche Referenzen:**

- `docs/KlausurBotPro_Architekturplan.md`
- `docs/reference/RT1_Fachspezifikation_Laplace_PBZ_Zeitantworten.md`

**Verbindliche Leitlinie:** Die vorhandene Fachspezifikation bleibt fachlich maßgeblich. Dieses Dokument verdichtet sie zu einer wirtschaftlichen Paketentscheidung, stabilen Verträgen, Modulgrenzen, Algorithmen, Referenzfällen und einer gezielten Teststrategie.

---

# 1. Ausgangspunkt

## 1.1 Ziel des Implementierungspakets

Die Zeitbereichssäule soll den klausurrelevanten Rechenweg

\[
\text{DGL oder Übertragungsfunktion}
\rightarrow
\text{Bildbereich}
\rightarrow
\text{rationale Klassifikation}
\rightarrow
\text{Polynomdivision}
\rightarrow
\text{Partialbruchzerlegung}
\rightarrow
\text{inverse Laplace-Transformation}
\rightarrow
\text{Zeitantwort}
\rightarrow
\text{symbolische Kontrollen}
\]

vollständig, exakt und nachvollziehbar abbilden.

Der Block ist kein allgemeiner ODE-Solver. Er löst ausschließlich die in RT1 benötigte Klasse:

- einseitige Laplace-Transformation für \(t\ge 0\),
- lineare SISO-Differentialgleichungen mit konstanten Koeffizienten,
- rationale Bildbereichsausdrücke,
- Standardanregungen,
- exakte Partialbruchzerlegung über reellen linearen und irreduziblen quadratischen Faktoren,
- klausurtaugliche reelle Zeitfunktionen.

## 1.2 Bereits vorhandener Unterbau

Folgende Fähigkeiten sind zu konsumieren und nicht neu zu implementieren:

- sichere mathematische Eingabelogik für rationale Ausdrücke,
- exakte symbolische Ausdrücke und Parameterannahmen,
- Zähler-/Nennerdarstellung,
- rohe und reduzierte rationale Funktionen,
- exakte Kürzung und Protokollierung gemeinsamer Faktoren,
- Pole und Nullstellen mit Vielfachheiten,
- strukturierte Diagnosen,
- Worked Steps,
- LaTeX-Bericht,
- Presenter- und GUI-Grundstruktur.

Die Zeitbereichssäule darf daraus weder einen zweiten allgemeinen Parser noch eine zweite Rationalfunktionsbibliothek noch eine parallele LaTeX-Infrastruktur erzeugen.

## 1.3 Fachliche Kernentscheidungen aus der Referenz

Verbindlich übernommen werden:

1. Eine Übertragungsfunktion darf aus einer DGL nur unter Nullanfangsbedingungen gebildet werden.
2. Fehlende Anfangsbedingungen werden nicht stillschweigend als null interpretiert.
3. Rohe und reduzierte rationale Formen bleiben gleichzeitig erhalten.
4. Gemeinsame Faktoren werden dokumentiert und erzeugen eine Warnung.
5. Unechte rationale Funktionen werden vor einer PBZ dividiert.
6. Mehrfache reelle Pole und komplex konjugierte Pole gehören in den ersten produktiven PBZ-Kern.
7. Komplexe Paare werden standardmäßig als reelle Sinus-/Kosinusantwort ausgegeben.
8. Der Endwertsatz wird nur nach einer Polprüfung angewendet.
9. Jede PBZ wird durch Rückzusammenfassung geprüft.
10. Jede gelöste DGL wird durch Anfangsbedingungen, Vorwärtstransformation und DGL-Residuum geprüft.

## 1.4 Harte Nichtziele

Nicht spezifiziert werden:

- beliebige nichtlineare DGL,
- variable Koeffizienten,
- MIMO-Systeme,
- allgemeine Randwertprobleme,
- numerische ODE-Integration,
- numerische inverse Laplace-Transformation,
- beliebige Spezialfunktionen,
- allgemeine Distributionstheorie,
- allgemeine stückweise Signale,
- ein universeller symbolischer Gleichungslöser,
- automatische Fallkombinatorik für beliebig viele symbolische Parameter.

---

# 2. Wirtschaftliche Paketentscheidung

## 2.1 Bewertete Varianten

### Variante A – ein großer PR

Ein gemeinsamer PR enthält direkte Laplace-Transformation, DGL, Übertragungsfunktion, rationale Vorverarbeitung, PBZ, inverse Laplace und sämtliche Zeitantworten.

**Vorteile**

- nur eine Vertrags- und GUI-Runde,
- keine temporären Übergabeschnittstellen,
- keine Wiederholung von Presenter- und LaTeX-Arbeit,
- vollständiger End-to-End-Nutzen nach einem Merge.

**Nachteile**

- sehr großer Codex-Kontext,
- hohe Zahl gleichzeitig neuer Verträge,
- große Fehler- und Korrekturfläche,
- schwer lokalisierbare Regressionen zwischen Parser, DGL, PBZ und Presenter,
- lange Branch-Lebensdauer,
- spätes Nutzerfeedback,
- bei einem blockierenden Sonderfall bleibt der gesamte Nutzen ungemergt.

### Variante B – zuerst DGL/Laplace/Übertragungsfunktion, danach PBZ/Zeitantwort

PR 1 erzeugt Bildbereichsausdrücke und Übertragungsfunktionen. PR 2 ergänzt PBZ, inverse Laplace und Zeitantworten.

**Vorteile**

- natürliche Leserichtung der Mathematik,
- geringerer Einzelumfang als Variante A,
- DGL-zu-Übertragungsfunktion ist bereits nach PR 1 nutzbar.

**Nachteile**

- schlechte technische Abhängigkeitsrichtung: PR 1 erzeugt Ergebnisse, die ohne PR 2 häufig nicht bis zur gesuchten Zeitantwort führen,
- erster Merge endet bei den zeitaufwendigen Aufgaben genau vor dem eigentlichen Engpass,
- Presenter und LaTeX müssten für eine Zwischenansicht und später für die vollständige Ansicht erneut angefasst werden,
- Tests für Bildbereichsausdrücke werden im zweiten PR großteils erneut durchlaufen,
- DGL-Fehler sind ohne unabhängigen inversen Kern schlechter end-to-end prüfbar,
- hohe Gefahr eines dauerhaft unvollständigen Zwischenstands.

### Variante C – zuerst PBZ-/inverse-Laplace-Kern mit sichtbarem Zeitantwort-Workflow, danach DGL- und Eingangsvarianten

PR 1 implementiert den gemeinsamen rationalen Kern und einen vollständigen sichtbaren Workflow ab \(F(s)\), \(G(s)\) oder \(G(s),U(s)\). PR 2 ergänzt strukturierte DGL-Eingabe, Anfangsbedingungen, Bildung von \(Y(s)\), Übertragungsfunktion aus DGL und die restlichen Eingangssignalvarianten.

**Vorteile**

- technisch richtige Abhängigkeitsrichtung: DGL-Orchestrierung konsumiert später einen bereits verifizierten PBZ-/Inverse-Kern,
- nach PR 1 bereits hoher sichtbarer Klausurnutzen durch inverse Laplace, PBZ und Sprungantworten,
- Mehrfachpole und komplexe Paare werden früh belastbar,
- PR 2 kann DGL-Ergebnisse unmittelbar end-to-end verifizieren,
- keine zweite Rationalfunktionsbibliothek,
- geringe Wiederholung von Parser, Presenter und LaTeX, sofern die Verträge vor PR 1 festgelegt werden,
- begrenzte Branch-Risiken bei weiterhin produktivem Zwischenstand,
- hohe Wiederverwendung für spätere Zustandsraum-, Regelkreis- und Reglerworkflows.

**Nachteile**

- PR 1 beginnt nicht mit freier DGL-Eingabe,
- Verträge für DGL und Anfangsbedingungen müssen trotzdem vor PR 1 festgelegt werden, damit keine spätere Schnittstellenkorrektur entsteht,
- GUI muss von Beginn an den späteren DGL-Pfad vorsehen, ohne bereits leere oder irreführende Funktionen zu zeigen.

## 2.2 Vergleichsmatrix

Bewertung: 1 = schlecht, 5 = sehr gut.

| Kriterium | A: ein PR | B: DGL zuerst | C: PBZ-Kern zuerst |
|---|---:|---:|---:|
| Vermeidung doppelter Parserarbeit | 5 | 3 | 5 |
| Vermeidung doppelter Vertragsarbeit | 4 | 2 | 5 bei Vertragsfreeze vor PR 1 |
| Vermeidung von Presenter-/LaTeX-Wiederholung | 4 | 2 | 4 |
| Saubere Abhängigkeitsrichtung | 4 | 2 | 5 |
| Wenige Testwiederholungen | 3 | 2 | 4 |
| Geringes Branch-Risiko | 1 | 4 | 4 |
| Geringer Codex-Kontext pro PR | 1 | 4 | 4 |
| Sichtbarer Nutzen nach erstem Merge | 5, aber spät | 3 | 5 |
| Schutz vor unvollständigem Dauerzustand | 3 | 1 | 5 |
| Spätere Wiederverwendung | 5 | 4 | 5 |
| Einfache fachliche End-to-End-Prüfung | 3 | 2 | 5 |

## 2.3 Verbindliche Empfehlung

\[
\boxed{\text{Variante C ist wirtschaftlich die beste Paketierung.}}
\]

Die Umsetzung wird in zwei produktive PRs geteilt:

### PR 1 – `feat/time-domain-pbz-core`

Gemeinsamer PBZ-/Inverse-Laplace-Kern mit sichtbaren Workflows:

- direkte und inverse Standardpaare,
- rationale Klassifikation,
- Polynomdivision,
- PBZ mit einfachen reellen, mehrfachen reellen und irreduziblen quadratischen Faktoren,
- reelle inverse Laplace,
- inverse Laplace aus \(F(s)\),
- Sprungantwort aus \(G(s)\),
- allgemeine Ausgangsantwort aus \(G(s)\) und direkter \(U(s)\)-Eingabe,
- mindestens Exponentialeingang als erster allgemeiner Signaltyp,
- Anfangs- und Endwertkontrollen,
- Rücktransformations- und PBZ-Kontrollen,
- Kürzungs- und Polwarnungen,
- GUI, Worked Steps und LaTeX.

### PR 2 – `feat/time-domain-ode-laplace`

DGL- und Eingangserweiterung auf dem stabilen Kern:

- strukturierte lineare DGL mit konstanten Koeffizienten,
- Anfangsbedingungen bis zur benötigten Ordnung,
- Ableitungssatz,
- Bildung und Auflösung von \(Y(s)\),
- freie und erzwungene Antwort,
- Übertragungsfunktion nur bei expliziten Nullanfangswerten,
- fehlende Anfangswerte als Fehler,
- Polynom-, Sinus- und Kosinuseingang,
- vollständige DGL-Residuen- und Anfangsbedingungsprüfung,
- vollständige GUI-Integration des DGL-Pfads.

## 2.4 Warum Variante C nicht zu klein geschnitten werden darf

PR 1 darf nicht auf einfache reelle Pole reduziert werden. Dann wäre er zwar kleiner, aber fachlich schwach und würde gerade die zeitaufwendigen Fälle aussparen.

Verbindlich in PR 1:

- Mehrfachpole,
- komplex konjugierte Paare,
- irreduzible quadratische Faktoren,
- Polynomdivision,
- vollständige Rückprüfung.

Diese Fälle teilen denselben Faktorisierungs-, PBZ-, Invers- und Verifikationsunterbau. Eine Verschiebung würde im zweiten PR dieselben Kernverträge, Presenter und Tests erneut öffnen. Der geringe kurzfristige Umfangsvorteil wäre wirtschaftlich schlechter als die zusätzliche Branch- und Korrekturarbeit.

## 2.5 Relative Codex-Aufwandsbewertung

Die Werte sind relative Planungsgrößen, keine Zusage für konkrete Tokenzahlen.

| Variante | Implementierungsaufwand | erwartete Korrekturschleifen | Gesamtrisiko | wirtschaftlicher Gesamtaufwand |
|---|---:|---:|---:|---:|
| A | 1,00 | hoch | sehr hoch | ca. 1,25–1,45 |
| B | 1,15–1,25 | mittel bis hoch | mittel | ca. 1,35–1,55 |
| C | 1,05–1,15 | niedrig bis mittel | niedrig bis mittel | ca. 1,10–1,25 |

Variante C ist nicht die kleinste Menge an Fachfunktion. Sie ist die günstigste Reihenfolge derselben fachlich nötigen Funktion.

---

# 3. Erster vollständiger Workflow

## 3.1 Definition „vollständig“

Ein Workflow ist vollständig, wenn er:

1. über die normale GUI erreichbar ist,
2. einen fachlich sinnvollen Startwert akzeptiert,
3. alle mathematischen Zwischenobjekte bis zur gesuchten Zeitfunktion erzeugt,
4. keine Black-Box-Transformation ohne Worked Steps verwendet,
5. die wesentlichen symbolischen Kontrollen ausführt,
6. Warnungen und Nicht-unterstützt-Zustände sichtbar macht,
7. ein vollständiges LaTeX-Ergebnis erzeugt.

PR 1 liefert einen vollständigen Workflow ab rationaler Bildfunktion oder Übertragungsfunktion. PR 2 ergänzt den vollständigen Start ab DGL.

## 3.2 Verbindlicher Umfang je Funktion

| Funktion | PR 1 | PR 2 | später |
|---|---:|---:|---:|
| Direkte Standard-Laplace-Paare | Pflicht | Erweiterung der Regelkombinationen | – |
| Inverse Standardpaare | Pflicht | – | – |
| DGL mit konstanten Koeffizienten | – | Pflicht | – |
| Anfangswerte bis zur DGL-Ordnung | Vertrag vorab, Verarbeitung noch nicht sichtbar | Pflicht | – |
| fehlende Anfangswerte als Fehler | Vertrag vorab | Pflicht | – |
| Übertragungsfunktion nur bei Nullanfangswerten | Vertrag vorab | Pflicht | – |
| rationale Klassifikation | Pflicht | Wiederverwendung | – |
| streng echte Funktion | Pflicht | Wiederverwendung | – |
| gleichgradige Funktion | Pflicht | Wiederverwendung | – |
| unechte Funktion | Pflicht | Wiederverwendung | – |
| Polynomdivision | Pflicht | Wiederverwendung | – |
| einfache reelle Pole | Pflicht | Wiederverwendung | – |
| mehrfache reelle Pole | Pflicht | Wiederverwendung | – |
| irreduzible quadratische Faktoren | Pflicht | Wiederverwendung | – |
| komplex konjugierte Pole, reelle Ausgabe | Pflicht | Wiederverwendung | – |
| inverse Laplace der PBZ-Terme | Pflicht | Wiederverwendung | – |
| Einheitssprung | Pflicht | Wiederverwendung | – |
| Exponentialeingang | Pflicht | Wiederverwendung | – |
| Polynom-, Sinus-, Kosinuseingang | optional nur bei praktisch kostenfreier Regelwiederverwendung | Pflicht | – |
| Sprungantwort | Pflicht | Wiederverwendung | – |
| allgemeine Ausgangsantwort aus \(G,U\) | Pflicht | Wiederverwendung | – |
| allgemeine DGL-Antwort | – | Pflicht | – |
| Endwertsatz mit Gültigkeitsprüfung | Pflicht | Wiederverwendung | – |
| Anfangswertkontrolle der Zeitantwort | Pflicht | Erweiterung auf alle vorgegebenen Ableitungswerte | – |
| Vorwärts-/Rücktransformation | Pflicht | Pflicht | – |
| DGL-Residuum | – | Pflicht | – |
| Kürzungswarnungen | Pflicht | Pflicht | – |
| Stabilitäts- und Polhinweise | Pflicht | Pflicht | – |
| Impulsantwort streng echter Systeme | – | – | sinnvolle Erweiterung |
| explizite Faltung | – | – | Erweiterung |
| Zeitverschiebung und stückweise Signale | – | – | Erweiterung |
| distributionsartige inverse Laplace | – | – | teurer Spezialfall |

## 3.3 PR-1-End-to-End-Workflow

### Einstieg A – inverse Laplace

\[
F(s)
\rightarrow
\text{Rationalanalyse}
\rightarrow
\text{Polynomdivision}
\rightarrow
\text{Faktorisierung}
\rightarrow
\text{PBZ}
\rightarrow
f(t)
\rightarrow
\text{Vorwärtstransformationsprüfung}.
\]

### Einstieg B – Sprungantwort

\[
G(s),\ A
\rightarrow
U(s)=\frac{A}{s}
\rightarrow
Y(s)=G(s)U(s)
\rightarrow
\text{Rationalanalyse/PBZ}
\rightarrow
y(t)
\rightarrow
\text{Anfangs-/Endwert- und Polprüfung}.
\]

### Einstieg C – allgemeine Ausgangsantwort

\[
G(s),\ U(s)
\rightarrow
Y(s)=G(s)U(s)
\rightarrow
\text{Rationalanalyse/PBZ}
\rightarrow
y(t)
\rightarrow
\text{Kontrollen}.
\]

Der direkte \(U(s)\)-Einstieg verhindert, dass PR 1 bereits einen vollständigen allgemeinen Zeitbereichsparser benötigt. Mindestens ein typisiertes Exponentialsignal wird dennoch unterstützt, damit der Signalvertrag praktisch erprobt wird.

## 3.4 PR-2-End-to-End-Workflow

\[
\text{DGL, Eingang, Anfangswerte}
\rightarrow
\text{Laplace-Regeln je Term}
\rightarrow
\text{Bildgleichung}
\rightarrow
Y(s)
\rightarrow
\text{PR-1-Kern}
\rightarrow
y(t)
\rightarrow
\text{Anfangsbedingungen, DGL-Residuum, Rücktransformation}.
\]

## 3.5 Kritische Entscheidung zu Mehrfachpolen und komplexen Paaren

Die Position der Fachspezifikation bleibt bestehen.

**Keine Verschiebung auf später.**

Begründung:

- Der offizielle DGL-Referenzfall enthält einen doppelten Pol.
- PT2- und Schwingungsantworten benötigen irreduzible quadratische Faktoren.
- Die zusätzliche Kernlogik ist eng mit der ohnehin nötigen Faktorisierungs- und PBZ-Struktur gekoppelt.
- Ein MVP nur mit einfachen reellen Polen würde bei relevanten Aufgaben abbrechen und den wirtschaftlichen Hauptnutzen verfehlen.
- Das spätere Nachrüsten würde erneut Verträge, LaTeX und Golden-Tests öffnen.

---

# 4. Späterer Erweiterungsumfang

## 4.1 Sinnvolle Erweiterungen nach den zwei PRs

- Impulsantwort streng echter Übertragungsfunktionen,
- Impulsantwort gleichgradiger Systeme mit explizitem Hinweis auf nicht unterstützten Dirac-Direktanteil,
- verzögerter Sprung und Dämpfungs-/Verschiebungssatz,
- einfache explizite Faltung als Alternativdarstellung,
- parameterabhängige Fallunterscheidung für quadratische Diskriminanten,
- automatische Übernahme von Übertragungsfunktionen aus Frequenz- und Regelkreismodulen,
- automatische Standardgliedlabels PT1, PT2, I, IT1 als zusätzliche Interpretation,
- Einheitenmetadaten und Dimensionskontrollen,
- Diagramm der Zeitantwort auf Basis des exakten Ergebnisses.

## 4.2 Teure Spezialfälle

- unechte inverse Laplace mit \(\delta\)-Ableitungen,
- allgemeine stückweise Signale,
- allgemeine Zeitverschiebung verschachtelter Ausdrücke,
- numerische inverse Laplace für nicht rationale Funktionen,
- allgemeine symbolische Parameter-PBZ mit unbekannter Polordnung,
- MIMO- oder Matrix-PBZ,
- beliebige lineare DGL-Systeme,
- nichtlineare DGL,
- automatische Erkennung beliebiger handschriftlicher DGL-Notation.

## 4.3 Abbruchregel

Ein nicht unterstützter Fall erzeugt ein strukturiertes Ergebnis mit:

- normalisiertem Eingabeausdruck,
- bereits sicher bestimmten Zwischenwerten,
- präzisem Grund des Abbruchs,
- fehlender Annahme oder nicht unterstützter Funktion,
- keiner erfundenen Zeitfunktion.

---

# 5. Modulgrenzen

## 5.1 Gemeinsame Ausdrucksinfrastruktur

Die vorhandene sichere Ausdrucksinfrastruktur wird um **Modusprofile** erweitert. Es wird kein zweiter Parser gebaut.

### Profil `IMAGE_S`

- Hauptvariable: ausschließlich \(s\),
- reelle Parameter nach bestehendem Parametervertrag,
- rationale Ausdrücke als primärer Fall,
- keine Zeitfunktionen,
- keine gemischte Verwendung von \(t\).

### Profil `TIME_T`

- Hauptvariable: ausschließlich \(t\),
- erlaubte Funktionen im ersten Umfang: Polynom, `exp`, `sin`, `cos`, Konstanten,
- reelle Parameter nach demselben Parametervertrag,
- keine Verwendung von \(s\),
- keine frei eingebetteten Ableitungsoperatoren,
- kein beliebiger Funktionsaufruf.

### Profil `COEFFICIENT`

- keine Hauptvariable \(s\) oder \(t\),
- nur Parameter und exakte Zahlen,
- für DGL-Koeffizienten und Anfangswerte.

Die Lexer-, Whitelist-, Parameter- und Fehlerlogik bleibt gemeinsam. Nur die zulässigen Symbole und Funktionen unterscheiden sich.

## 5.2 DGL-Eingabe

Im ersten DGL-PR wird kein freier universeller DGL-Textparser verlangt. Primär wird eine strukturierte SISO-Koeffizienteneingabe verwendet:

\[
\sum_{k=0}^{n} a_k y^{(k)}(t)
=
\sum_{j=0}^{m} b_j u^{(j)}(t)
\]

oder

\[
\sum_{k=0}^{n} a_k y^{(k)}(t)=r(t)
\]

mit konstanten symbolischen Koeffizienten.

Ein kontrollierter Gleichungseditor darf diese Struktur darstellen, muss intern aber in denselben Vertrag übersetzen. Er ist kein eigener Rechenkern.

## 5.3 Rationalfunktionskern

Der vorhandene Rationalfunktionskern ist allein verantwortlich für:

- Rohform und reduzierte Form,
- Zähler und Nenner,
- Kürzungsbericht,
- Pole und Nullstellen,
- Parameterannahmen,
- Gradbestimmung,
- exakte algebraische Gleichheit.

Die Zeitbereichssäule ergänzt nur rollenbezogene Metadaten:

- `INPUT_LAPLACE`,
- `OUTPUT_LAPLACE`,
- `TRANSFER_FUNCTION`,
- `INVERSE_LAPLACE_TARGET`,
- `END_VALUE_TARGET`.

## 5.4 PBZ-Kern

Der PBZ-Kern übernimmt:

- Echtheitsprüfung des Restbruchs,
- Nennerfaktorisierung über den reellen Zahlen,
- Multiplizitäten,
- PBZ-Ansatz,
- exakte Koeffizientenbestimmung,
- Rückzusammenfassung.

Er übernimmt nicht:

- Eingabeparsing,
- DGL-Transformation,
- Stabilitätsentscheidung des Systems,
- UI-Formatierung,
- allgemeine Faktorisierung nichtpolynomieller Ausdrücke.

## 5.5 Transformationsregelwerk

Direkte Tabellenpaare und algorithmische PBZ bleiben getrennt.

### Tabellenregelwerk

Verantwortlich für:

- bekannte direkte und inverse Grundpaare,
- Linearität,
- Dämpfungssatz für die belegten Klassen,
- Normierungsfaktoren,
- Quellen- und Regel-IDs.

### Algorithmischer PBZ-Pfad

Verantwortlich für:

- rationale Ausdrücke,
- Faktorstruktur,
- Koeffizientenbestimmung,
- inverse Abbildung der einzelnen PBZ-Terme.

Ein allgemeiner CAS-Aufruf darf höchstens eine unabhängige Verifikation liefern. Er darf nicht den klausurtauglichen Rechenplan ersetzen.

## 5.6 Zeitantwort-Orchestrator

Verantwortlich für:

- Auswahl des Einstiegspfads,
- Transformation des Eingangssignals,
- Kombination \(Y=GU\) bei zulässigem Ruhezustand,
- Ergänzung des Anfangswertanteils im DGL-Pfad,
- Aufruf des rationalen Kerns,
- inverse Laplace,
- Verifikationen,
- Aufbau fachlicher Ergebnisobjekte.

## 5.7 Presenter und Renderer

Der Presenter erzeugt aus Domainwerten:

- Kurzantwort,
- Worked Steps,
- Tabellenzeilen,
- Warnungen,
- LaTeX-Blöcke.

Der UI-Renderer zeigt ausschließlich fertige View-Modelle. Er führt keine Fachberechnung aus.

---

# 6. Verträge

Die konkreten Klassennamen dürfen an die bestehende Codebasis angepasst werden. Die fachlichen Felder und Invarianten sind verbindlich.

## 6.1 `TimeDomainExpression`

### Pflichtfelder

| Feld | Bedeutung |
|---|---|
| `raw_text` | unveränderte Benutzereingabe |
| `expression` | sicher geparster exakter Ausdruck |
| `time_symbol` | exakt \(t\) |
| `parameters` | geordnete Parameterliste |
| `assumptions` | reell/positiv/nichtnull soweit angegeben |
| `causality` | im MVP `CAUSAL_T_GE_0` |
| `normalization_history` | nachvollziehbare Umformungen |

### Invarianten

- \(s\) kommt nicht vor.
- Nur zugelassene Funktionen sind enthalten.
- Parameterannahmen sind widerspruchsfrei oder der Vertrag ist ungültig.
- Keine Ableitung wird als freier symbolischer Funktionsaufruf eingebettet.

### Verbotene Mischzustände

- `time_symbol=t` und Ausdruck enthält \(s\),
- kausaler Status fehlt,
- ungeprüfter Funktionsaufruf,
- numerische Gleitkommazahl ohne dokumentierte Normalisierung, wenn eine exakte rationale Darstellung möglich ist.

## 6.2 `ImageDomainExpression`

### Pflichtfelder

| Feld | Bedeutung |
|---|---|
| `raw_text` | Rohinput |
| `expression` | exakter Ausdruck |
| `image_symbol` | exakt \(s\) |
| `role` | fachliche Rolle des Ausdrucks |
| `parameters` | geordnete Parameterliste |
| `assumptions` | Parameterannahmen |
| `rational_status` | rational/nicht rational/unbestimmt |

### Invarianten

- \(t\) kommt nicht vor.
- Die Rolle ist gesetzt.
- Ein rationaler Status wird nicht behauptet, bevor Zähler und Nenner sicher extrahiert wurden.

## 6.3 `LinearOdeInput`

### Pflichtfelder

| Feld | Bedeutung |
|---|---|
| `output_name` | z. B. \(y\) |
| `input_name` | optional \(u\), wenn ein symbolischer Kanal verwendet wird |
| `output_terms` | Abbildung Ordnung \(k\mapsto a_k\) |
| `input_terms` | optional Ordnung \(j\mapsto b_j\) |
| `forcing_expression` | optional explizites \(r(t)\) |
| `declared_order` | höchste Ausgangsableitung |
| `coefficient_assumptions` | Annahmen und Ausschlüsse |
| `source_form` | Rohdarstellung für Provenienz |

### Invarianten

- mindestens ein Ausgangsterm,
- Leitkoeffizient der deklarierten Ordnung ist unter den Annahmen nicht null,
- alle Koeffizienten sind zeitinvariant,
- genau einer der Pfade ist aktiv: symbolischer Eingangskanal oder explizites forcing, sofern keine bewusst unterstützte Summe spezifiziert ist,
- SISO: genau ein Ausgang und höchstens ein Eingang.

### Verbotene Mischzustände

- nichtlineare Produkte wie \(y\dot y\),
- zeitabhängige Koeffizienten,
- Ableitungsordnung kleiner als ein vorhandener Term,
- gleichzeitig `input_terms` und unmarkiertes forcing ohne definierte Semantik,
- fehlender Leitkoeffizient.

## 6.4 `InitialConditionSet`

### Pflichtfelder

| Feld | Bedeutung |
|---|---|
| `variable` | abhängige Variable, z. B. \(y\) |
| `required_orders` | \(0,\dots,n-1\) |
| `values` | Ordnung \(k\mapsto\) exakter Wert |
| `origin` | `USER_PROVIDED`, `EXPLICIT_ZERO_POLICY` oder `DERIVED` |
| `completeness` | vollständig/unvollständig |

### Invarianten

- für eine DGL-Lösung sind alle Ordnungen \(0,\dots,n-1\) vorhanden,
- eine Nullannahme ist nur gültig, wenn der Nutzer sie ausdrücklich aktiviert hat,
- ein fehlender Wert besitzt einen eigenen Status und niemals implizit den Zahlenwert null.

### Verbotene Mischzustände

- `completeness=COMPLETE` bei fehlender Ordnung,
- derselbe Anfangswert gleichzeitig bereitgestellt und abweichend als null angenommen,
- Übertragungsfunktionsanforderung bei nicht vollständig bestätigtem Nullzustand.

## 6.5 `InputSignal`

### Varianten im Gesamt-MVP

- `STEP(amplitude)`
- `EXPONENTIAL(amplitude, exponent)`
- `POLYNOMIAL(coefficients)`
- `SINUS(amplitude, omega, phase)`
- `COSINUS(amplitude, omega, phase)`
- `IMAGE_EXPRESSION(U_s)`

### Pflichtfelder

- `signal_type`,
- exakte Parameter,
- Parameterannahmen,
- Zeit- oder Bildbereichsrepräsentation,
- Transformationsstatus.

### Invarianten

- genau eine Primärrepräsentation ist benutzereingegeben,
- eine abgeleitete zweite Repräsentation ist als berechnet markiert,
- Frequenzparameter für Sinus/Kosinus ist reell; für die Standardausgabe wird \(\omega>0\) verlangt oder eine Fallklärung erzeugt.

## 6.6 `ResponseRequest`

### Varianten

- `DIRECT_LAPLACE`
- `INVERSE_LAPLACE`
- `SOLVE_ODE`
- `TRANSFER_FUNCTION_FROM_ODE`
- `OUTPUT_RESPONSE`
- `STEP_RESPONSE`
- `FINAL_VALUE_CHECK`

### Pflichtfelder

- Operation,
- gewünschter Ausgang,
- Genauigkeitsmodus `EXACT_FIRST`,
- gewünschte Kontrollen,
- gewünschte Darstellungsstufe.

### Invarianten

- die Operation passt zu den vorhandenen Eingabeverträgen,
- `TRANSFER_FUNCTION_FROM_ODE` verlangt expliziten Nullzustand,
- `SOLVE_ODE` verlangt vollständige Anfangsbedingungen.

## 6.7 `RationalAnalysisSnapshot`

Dieser Vertrag ist ein Adapter auf das vorhandene Rationalfunktionsobjekt, kein zweiter Kern.

### Pflichtfelder

- rohe rationale Funktion,
- roher Zähler und Nenner,
- reduzierte rationale Funktion,
- reduzierter Zähler und Nenner,
- gemeinsame Faktoren mit Vielfachheiten,
- Normalisierungsfaktoren,
- Pole und Nullstellen der Roh- und reduzierten Form,
- Parameterannahmen,
- fachliche Rolle.

### Invarianten

- Rohform wird nie durch die reduzierte Form überschrieben,
- jede Kürzung ist rekonstruierbar,
- Pole der reduzierten Form und entfernte Polfaktoren sind getrennt,
- der Nenner ist nicht null.

## 6.8 `RationalClassification`

### Pflichtfelder

- Zählergrad \(m\),
- Nennergrad \(n\),
- Klasse `STRICTLY_PROPER`, `EQUAL_DEGREE`, `IMPROPER`,
- Realisierbarkeitsinterpretation für die Rolle,
- Bedarf an Polynomdivision,
- Hinweis auf mögliche distributionsartige inverse Terme.

### Invarianten

- Gradwerte beziehen sich auf die für den aktuellen Rechenschritt verwendete Form,
- Roh- und reduzierte Klassifikation dürfen getrennt vorliegen,
- eine gleichgradige Übertragungsfunktion wird nicht als grundsätzlich ungültig bezeichnet,
- eine inverse Laplace eines verbleibenden Polynomteils wird ohne Distributionsunterstützung nicht als gewöhnliche Zeitfunktion ausgegeben.

## 6.9 `PolynomialDivisionResult`

### Pflichtfelder

- Dividend \(Z(s)\),
- Divisor \(N(s)\),
- Quotient \(Q(s)\),
- Rest \(R(s)\),
- echter Restbruch \(R/N\),
- Rekonstruktionsresiduum,
- Status `NOT_REQUIRED`, `SUCCESS`, `FAILED`,
- Auswirkung auf inverse Laplace.

### Invarianten

\[
Z(s)=Q(s)N(s)+R(s),\qquad \deg R<\deg N.
\]

Bei `SUCCESS` muss das Rekonstruktionsresiduum exakt null sein.

## 6.10 `PoleFactorStructure`

### Pflichtfelder

- normalisierter Nenner,
- Gesamtfaktor vor dem Nenner,
- Liste reeller linearer Faktoren,
- Liste irreduzibler reeller quadratischer Faktoren,
- Multiplizität jedes Faktors,
- zugeordnete Pole,
- Faktorisierungsbereich `REAL_EXACT`,
- Vollständigkeitsstatus,
- notwendige Annahmen.

### Invarianten

- Produkt aller Faktoren einschließlich Gesamtfaktor rekonstruiert den Nenner,
- lineare Faktoren sind eindeutig normiert,
- quadratische Faktoren haben negative Diskriminante unter den dokumentierten Annahmen,
- bei nicht entscheidbarer Diskriminante wird keine Faktorart geraten.

## 6.11 `PartialFractionTerm`

### Pflichtfelder

| Feld | Bedeutung |
|---|---|
| `factor_id` | Verweis auf Nennerfaktor |
| `factor_type` | linear oder quadratisch |
| `power` | \(1,\dots,m\) |
| `numerator` | Grad kleiner als Faktorgrad |
| `coefficients` | exakte Koeffizienten |
| `display_basis` | z. B. \(s-p\) oder \(s-\alpha\) |
| `inverse_pattern_id` | zugehörige inverse Regel |

### Invarianten

- für einen linearen Faktor ist der Zähler konstant,
- für einen quadratischen Faktor ist der Zähler höchstens linear,
- für jede Potenz von 1 bis zur Multiplizität existiert genau ein Term,
- kein Term besitzt eine höhere Zählerordnung als zulässig.

## 6.12 `PartialFractionResult`

### Pflichtfelder

- echter Eingangsbruch,
- Faktorstruktur,
- Ansatz,
- exaktes Koeffizientensystem,
- gelöste Koeffizienten,
- geordnete PBZ-Terme,
- rückzusammengefasster Ausdruck,
- Rekonstruktionsresiduum,
- Status.

### Invarianten

- bei `SUCCESS` ist das Residuum exakt null,
- die Termordnung ist deterministisch,
- komplexe Einzelresiduen werden nicht als Standardausgabe gespeichert, wenn eine reelle quadratische Darstellung möglich ist.

## 6.13 `InverseLaplaceResult`

### Pflichtfelder

- Bildbereichseingang,
- Polynomanteil und dessen Unterstützungsstatus,
- Tabellenanteile,
- PBZ-Anteile,
- reelle Zeitfunktion,
- kausale Konvention,
- Vorwärtstransformationsprüfung,
- Status.

### Invarianten

- bei erfolgreicher gewöhnlicher Zeitfunktion enthält das Ergebnis keine nicht dargestellten Distributionsterme,
- eine reelle Bildfunktion mit reellen Koeffizienten liefert eine reelle Zeitfunktion,
- komplexe Paare sind reell zusammengeführt.

## 6.14 `TimeResponseResult`

### Pflichtfelder

- Systembeschreibung,
- Eingangssignal,
- Anfangsbedingungen oder expliziter Ruhezustand,
- \(U(s)\),
- Anfangswertanteil im Bildbereich,
- erzwungener Anteil im Bildbereich,
- Gesamt-\(Y(s)\),
- rationale Analyse,
- inverse Laplace,
- Zeitfunktion,
- Systempole, Eingangspole und Ausgangspole getrennt,
- Stabilitäts- und Endwertstatus.

### Invarianten

- \(Y=GU\) wird nur beim zulässigen Ruhezustand als vollständige Gleichung verwendet,
- Systempole werden nicht mit Eingangspolen verwechselt,
- die Zeitfunktion ist mit \(Y(s)\) konsistent,
- Anfangswertanteil und erzwungener Anteil summieren sich zur Gesamtlösung, sofern beide vorhanden sind.

## 6.15 `VerificationItem` und `VerificationReport`

### `VerificationItem`

- `check_id`,
- Status `PASS`, `FAIL`, `INCONCLUSIVE`, `NOT_APPLICABLE`,
- geprüfte linke und rechte Seite,
- exaktes Residuum oder Differenz,
- verwendete Annahmen,
- kurze fachliche Begründung,
- optionale numerische Kontrolle.

### `VerificationReport`

Mögliche Prüfungen:

- Polynomdivision rekonstruiert den Zähler,
- Faktorprodukt rekonstruiert den Nenner,
- PBZ rekonstruiert den Restbruch,
- Vorwärtstransformation rekonstruiert \(F(s)\) oder \(Y(s)\),
- Anfangswerte werden erfüllt,
- DGL-Residuum ist null,
- Endwertsatz ist zulässig,
- direkter Zeitendwert stimmt mit Satzwert überein,
- \(Y=GU\) ist im Ruhezustand erfüllt,
- Kürzungsbericht vollständig.

### Invarianten

- `PASS` wird nur bei symbolischem Nullresiduum oder eindeutig bewiesener Gleichheit vergeben,
- eine numerische Stichprobe allein darf höchstens `INCONCLUSIVE` zu `plausibel` ergänzen, nicht `PASS` erzeugen,
- nicht erfüllte Annahmen werden sichtbar.

## 6.16 `Diagnostic` und Nicht-unterstützt-Status

### Schweregrade

- `INFO`,
- `WARNING`,
- `ERROR`,
- `UNSUPPORTED`.

### Mindestens erforderliche Codes

- `TIME_IMAGE_VARIABLE_MIXED`
- `UNSUPPORTED_TIME_FUNCTION`
- `NONLINEAR_ODE_UNSUPPORTED`
- `TIME_VARYING_COEFFICIENT_UNSUPPORTED`
- `MISSING_INITIAL_CONDITION`
- `TRANSFER_FUNCTION_REQUIRES_ZERO_INITIAL_STATE`
- `DENOMINATOR_ZERO`
- `NON_RATIONAL_IMAGE_EXPRESSION`
- `POLYNOMIAL_DIVISION_FAILED`
- `DISTRIBUTIONAL_INVERSE_UNSUPPORTED`
- `FACTORIZATION_INCOMPLETE`
- `PARAMETER_ASSUMPTIONS_INSUFFICIENT`
- `PBZ_COEFFICIENT_SYSTEM_SINGULAR`
- `PBZ_RECOMPOSITION_FAILED`
- `FORWARD_TRANSFORM_CHECK_FAILED`
- `INITIAL_CONDITION_CHECK_FAILED`
- `ODE_RESIDUAL_FAILED`
- `END_VALUE_THEOREM_INVALID`
- `NO_FINITE_END_VALUE`
- `CANCELLED_COMMON_FACTOR`
- `HIDDEN_MODE_POSSIBLE`
- `UNSTABLE_SYSTEM_POLE`
- `IMAGINARY_AXIS_SYSTEM_POLE`

## 6.17 `WorkedStep`

Der bestehende Vertrag wird wiederverwendet und höchstens um fachliche Metadaten ergänzt:

- stabile Schritt-ID,
- Reihenfolge,
- Titel,
- fachliche Operation,
- Eingabeobjekt-IDs,
- exakte Gleichung,
- kurze Erklärung,
- Quellenhinweis,
- zugehörige Diagnosen,
- LaTeX-Fragment.

Keine fachliche Rechnung im Renderer.

## 6.18 `LatexOutput`

### Pflichtfelder

- `latex_problem`,
- `latex_assumptions`,
- `latex_steps`,
- `latex_result`,
- `latex_verifications`,
- `latex_warnings`,
- `latex_full_solution`.

### Invarianten

- exakte Werte stehen vor Näherungswerten,
- alle Anfangswertterme werden sichtbar,
- keine intern nicht ausgeführte Rechnung wird behauptet,
- rohe und reduzierte Form werden bei Kürzungen unterscheidbar ausgegeben,
- komplexe Paare erscheinen in reeller Form.

---

# 7. Algorithmen

## 7.1 Sichere Variablentrennung und Parsing

1. Der Benutzer wählt oder der Workflow bestimmt den Eingabemodus.
2. Das gemeinsame Parser-Frontend wird mit einem Modusprofil aufgerufen.
3. Für `TIME_T` ist \(t\) die einzige unabhängige Variable; \(s\) ist verboten.
4. Für `IMAGE_S` ist \(s\) die einzige unabhängige Variable; \(t\) ist verboten.
5. Parameternamen werden über den vorhandenen Parametervertrag registriert.
6. Nicht zugelassene Funktionen oder gemischte Variablen brechen vor jeder Fachrechnung ab.
7. Der Rohtext bleibt für Provenienz erhalten.

## 7.2 Direkte Laplace-Regelanwendung

Der direkte Regelpfad ist deterministisch:

1. Ausdruck exakt normalisieren, ohne ihn unnötig zu expandieren.
2. Linearität anwenden: Summe in unabhängige Summanden zerlegen, konstante Faktoren ausklammern.
3. Für jeden Summanden einen unterstützten Strukturtyp bestimmen:
   - Konstante,
   - Potenz \(t^n\),
   - Exponentialfunktion,
   - Potenz mal Exponentialfunktion,
   - Sinus,
   - Kosinus,
   - Exponentialfunktion mal Sinus/Kosinus,
   - einfache trigonometrische Vorumformung aus der Referenzklasse.
4. Grundregel aus dem Regelregister wählen.
5. Dämpfungssatz als Verschiebung \(s\mapsto s-a\) anwenden.
6. Alle Bildterme zusammenfassen.
7. Ergebnis in einen `ImageDomainExpression` überführen.
8. Soweit rational: vorhandenen Rationalfunktionskern aufrufen.
9. Durch inverse Transformation oder Tabellenrückprüfung verifizieren.

Nicht unterstützte Strukturtypen werden nicht an eine allgemeine Black-Box-Transformation delegiert.

## 7.3 Ableitungssatz mit Anfangswerten

Für eine Ausgangsableitung der Ordnung \(n\):

\[
\mathcal L\{y^{(n)}(t)\}
=
s^nY(s)-\sum_{k=0}^{n-1}s^{n-1-k}y^{(k)}(0^+).
\]

Algorithmus:

1. Erforderliche Anfangswertordnungen aus der höchsten Ausgangsableitung bestimmen.
2. Vollständigkeit des `InitialConditionSet` prüfen.
3. Für jeden DGL-Term \(a_n y^{(n)}\) einen eigenen Transformationsbeitrag erzeugen.
4. Anfangswertterme mit korrekter \(s\)-Potenz explizit speichern.
5. Koeffizient \(a_n\) auf den vollständigen Transformationsbeitrag anwenden.
6. Beiträge nach \(Y(s)\), \(U(s)\) und konstanten Anfangswerttermen gruppieren.
7. Worked Steps zeigen jeden Ableitungsterm mindestens einmal vollständig; zusammenfassende Darstellung ist erst danach zulässig.

## 7.4 DGL-Normalisierung

1. Ausgangs- und Eingangsterme nach Ableitungsordnung sortieren.
2. Fehlende Potenzen intern mit Koeffizient null darstellen.
3. Alle Ausgangsterme auf eine Seite, alle Eingangs-/forcing-Terme auf die andere Seite bringen.
4. Leitkoeffizient und DGL-Ordnung prüfen.
5. Parameterabhängigen Gradabfall nicht stillschweigend behandeln; Annahme oder Fallabbruch erzeugen.
6. Nichtlineare oder zeitvariable Terme ablehnen.
7. Normalisierte DGL und Transformationshistorie speichern.

Eine Division durch den Leitkoeffizienten ist nur unter dokumentierter Bedingung \(a_n\ne0\) zulässig.

## 7.5 Bildung von \(Y(s)\)

Nach Transformation entsteht allgemein:

\[
A(s)Y(s)-I_y(s)=B(s)U(s)+R(s),
\]

wobei \(I_y(s)\) die aus Anfangswerten entstehenden Terme bezeichnet.

Dann:

\[
Y(s)=\frac{B(s)U(s)+R(s)+I_y(s)}{A(s)}.
\]

Algorithmus:

1. \(A(s)\), \(B(s)\), forcing und Anfangswertanteil getrennt bilden.
2. Vorzeichen der auf die Gegenseite verschobenen Anfangswertterme dokumentieren.
3. Nach \(Y(s)\) auflösen.
4. Optional zerlegen in:
   \[
   Y(s)=Y_{\mathrm{frei}}(s)+Y_{\mathrm{erzwungen}}(s).
   \]
5. Jede Komponente und die Summe als Bildbereichsobjekt speichern.
6. Für jede rationale Komponente denselben Rational-/PBZ-Kern verwenden.

## 7.6 Bildung von \(G(s)\)

Nur wenn:

- ein eindeutiger symbolischer Eingangskanal vorhanden ist,
- alle erforderlichen Anfangswerte explizit null sind,
- kein zusätzliches forcing außerhalb des Eingangskanals vorhanden ist.

Dann:

\[
A(s)Y(s)=B(s)U(s),
\qquad
G(s)=\frac{Y(s)}{U(s)}=\frac{B(s)}{A(s)}.
\]

Algorithmus:

1. Nullzustandsprädikat prüfen.
2. Transformierte Gleichung anzeigen.
3. \(Y\)- und \(U\)-Faktoren ausklammern.
4. Quotient bilden.
5. Rohform in den bestehenden Rationalfunktionskern geben.
6. Reduktion, Kürzungsbericht, Pole, Nullstellen und Grade übernehmen.
7. Durch Rückmultiplikation gegen die transformierte DGL prüfen.

Bei nichtnull oder fehlenden Anfangswerten wird kein Quotient aus der Gesamtlösung gebildet.

## 7.7 Rationale Gradklassifikation

Für \(F(s)=Z(s)/N(s)\):

1. Zähler und Nenner exakt als Polynome in \(s\) extrahieren.
2. Nullpolynome und parameterabhängige Leitkoeffizienten prüfen.
3. Grade \(m=\deg Z\), \(n=\deg N\) bestimmen.
4. Klassifizieren:
   - \(m<n\): streng echt,
   - \(m=n\): gleichgradig,
   - \(m>n\): unecht.
5. Rolle berücksichtigen:
   - gleichgradiges \(G(s)\) ist sprungfähig und darf weiterverarbeitet werden,
   - gleichgradiges endgültiges Inversziel \(F(s)\) enthält grundsätzlich einen konstanten Polynomanteil und damit einen Distributionsanteil,
   - bei einer Sprungantwort wird erst \(Y=G/s\) gebildet und danach die inverse Klassifikation durchgeführt.
6. Roh- und reduzierte Klassifikation getrennt ausgeben, wenn Kürzungen den Grad ändern.

## 7.8 Polynomdivision

Wenn \(m\ge n\):

1. exakte Division \(Z=QN+R\) durchführen,
2. \(Q\), \(R\) und \(R/N\) speichern,
3. Rekonstruktionsresiduum \(Z-(QN+R)\) exakt vereinfachen,
4. nur den echten Restbruch der PBZ zuführen,
5. den Polynomanteil nach Rolle behandeln:
   - bei Übertragungsfunktionen als Direkt-/Differenzieranteil dokumentieren,
   - bei endgültiger inverser Laplace ohne Distributionsunterstützung `DISTRIBUTIONAL_INVERSE_UNSUPPORTED` ausgeben,
   - bei \(Q=0\) normal fortfahren.

Die Berechnung darf nicht den Polynomanteil verlieren, selbst wenn nur der Restbruch rücktransformierbar ist.

## 7.9 Behandlung gemeinsamer Faktoren

1. Rohzähler und Rohnenner faktorisieren beziehungsweise vorhandenen Kürzungsbericht übernehmen.
2. Gemeinsame Faktoren mit Multiplizitäten bestimmen.
3. Roh- und reduzierte Form parallel speichern.
4. Alle nachfolgenden externen Ein-/Ausgangsrechnungen verwenden die reduzierte Form.
5. Entfernte Pole werden als mögliche verborgene interne Modi getrennt gelistet.
6. Bei Endwert- und Stabilitätshinweisen wird klar unterschieden:
   - externe reduzierte Antwort,
   - mögliche verborgene Dynamik durch Kürzung.
7. Keine Warnung darf die mathematisch korrekte reduzierte Ein-/Ausgangsantwort verhindern; sie muss aber sichtbar bleiben.

## 7.10 Faktorisierung des Nenners

1. Den echten Restbruch verwenden.
2. Nenner über reellen exakten Koeffizienten normieren.
3. Gesamtfaktor ausklammern.
4. Reelle lineare Faktoren und ihre Multiplizitäten bestimmen.
5. Verbleibende quadratische Faktoren bestimmen.
6. Für jeden quadratischen Faktor die Diskriminante unter den Annahmen prüfen.
7. Nur bei nachweisbar negativer Diskriminante als irreduzibel quadratisch klassifizieren.
8. Faktorprodukt gegen den Nenner prüfen.
9. Bei höhergradigen nicht zerlegten Faktoren abbrechen, sofern keine unterstützte exakte Faktorstruktur vorliegt.

Numerische Näherungswurzeln dürfen nicht verwendet werden, um symbolische Mehrfachpole in mehrere nahe Pole zu zerlegen.

## 7.11 Multiplikitätsbestimmung

- Primär aus der exakten Faktorisierung.
- Sekundär kontrollierbar über \(\gcd(N,N')\).
- Eine Multiplizität ist ein ganzzahliger exakter Wert.
- Parameterwerte, bei denen Faktoren zusammenfallen, verlangen eine dokumentierte Fallunterscheidung oder einen Nicht-eindeutig-Status.

## 7.12 PBZ-Ansatz

### Einfacher reeller Faktor

Für \((s-p)\):

\[
\frac{A}{s-p}.
\]

### Mehrfacher reeller Faktor

Für \((s-p)^m\):

\[
\sum_{k=1}^{m}\frac{A_k}{(s-p)^k}.
\]

### Irreduzibler quadratischer Faktor

Für \(q(s)^m\), \(\deg q=2\):

\[
\sum_{k=1}^{m}\frac{A_k s+B_k}{q(s)^k}.
\]

Im ersten produktiven Umfang muss der allgemeine Vertrag quadratische Multiplizitäten darstellen können. Die verpflichtenden Referenzfälle benötigen mindestens einfache quadratische Faktoren. Höhere quadratische Multiplizitäten dürfen bei fehlender offizieller Relevanz als unterstützt-durch-Vertrag, aber nicht zwingend als eigener Presenter-Sonderweg behandelt werden.

## 7.13 Exakte Koeffizientenbestimmung

1. Ansatz auf gemeinsamen Nenner bringen.
2. Zählergleichheit erzeugen.
3. Koeffizienten nach Potenzen von \(s\) vergleichen.
4. Exaktes lineares Gleichungssystem aufstellen.
5. System exakt lösen.
6. Eindeutigkeit prüfen.
7. Bei singulärem System Annahmen beziehungsweise Faktorisierung prüfen.
8. PBZ-Terme deterministisch sortieren.
9. Rückzusammenfassung durchführen.

Einsetzverfahren an einfachen Polen darf als verkürzter Worked Step verwendet werden. Intern bleibt die vollständige Rekonstruktionsprüfung Pflicht.

## 7.14 Inverse Laplace der PBZ-Terme

### Reeller linearer Faktor

\[
\frac{A}{(s-p)^k}
\longleftrightarrow
A\frac{t^{k-1}}{(k-1)!}e^{pt}.
\]

### Irreduzibler quadratischer Faktor

1. Faktor in die Form
   \[
   (s-\alpha)^2+\beta^2,
   \qquad \beta>0
   \]
   bringen.
2. Zähler schreiben als
   \[
   C(s-\alpha)+D.
   \]
3. Rücktransformieren:
   \[
   \frac{C(s-\alpha)}{(s-\alpha)^2+\beta^2}
   \longleftrightarrow
   Ce^{\alpha t}\cos(\beta t),
   \]
   \[
   \frac{D}{(s-\alpha)^2+\beta^2}
   \longleftrightarrow
   \frac{D}{\beta}e^{\alpha t}\sin(\beta t).
   \]
4. Terme mit gleichem Polpaar zusammenfassen.

## 7.15 Reelle Zusammenfassung komplexer Paare

Standardausgabe ist nie eine Summe nicht offensichtlich reeller komplexer Exponentialterme, sofern eine reelle Form existiert.

Ausgabeform:

\[
e^{\alpha t}\left(C\cos(\beta t)+D\sin(\beta t)\right).
\]

Komplexe Pole dürfen zusätzlich als Diagnose erscheinen:

\[
p_{1,2}=\alpha\pm j\beta.
\]

## 7.16 Aufbau der Zeitantwort

1. Eingang transformieren oder direktes \(U(s)\) übernehmen.
2. Zulässigkeit von \(Y=GU\) prüfen.
3. Bei DGL den Anfangswertanteil ergänzen.
4. Rohes \(Y(s)\) speichern.
5. Rationalen Kern aufrufen.
6. Polynomdivision, PBZ und inverse Laplace ausführen.
7. Zeitfunktion exakt zusammenfassen.
8. System-, Eingangs- und Ausgangspole getrennt klassifizieren.
9. Kontrollen ausführen.
10. Presenter-Modell erzeugen.

## 7.17 Anfangsbedingungsprüfung

Bei vorhandener Zeitfunktion:

1. Rechtsgrenzwert \(t\to0^+\) von \(y(t)\) bestimmen.
2. Für jede geforderte Ordnung \(k\) die Zeitfunktion symbolisch \(k\)-mal ableiten.
3. Rechtsgrenzwert \(t\to0^+\) bestimmen.
4. Mit dem vorgegebenen Anfangswert vergleichen.
5. Differenz exakt vereinfachen.
6. Nur bei Null `PASS` vergeben.

Dies ist eine direkte Kontrolle. Ein eigenständiger Anfangswertsatz wird nicht als separates Quellenverfahren behauptet.

## 7.18 DGL-Residuum

Für die berechnete Zeitfunktion:

1. alle benötigten Ableitungen bilden,
2. in die normalisierte Original-DGL einsetzen,
3. Eingang beziehungsweise forcing einsetzen,
4. Residuum bilden,
5. unter den Annahmen exakt vereinfachen,
6. bei Null `PASS`, sonst `FAIL` oder `INCONCLUSIVE`,
7. optional numerische Stichstellen verwenden, aber nicht als Beweis.

## 7.19 Vorwärts-/Rücktransformationsprüfung

- Bei inverser Laplace: \(\mathcal L\{f(t)\}\) mit dem Regelwerk rekonstruieren und mit \(F(s)\) vergleichen.
- Bei direkter Laplace: unterstützte inverse Regel anwenden und mit \(f(t)\) vergleichen.
- Bei zusammengesetzten DGL-Antworten darf alternativ die exakte transformierte DGL plus DGL-Residuum die Verifikation ergänzen.
- Ein allgemeiner CAS darf nur als zusätzliche Vergleichsquelle dienen.

## 7.20 Endwertsatz

Für ein vorhandenes \(Y(s)\):

1. \(sY(s)\) bilden.
2. Exakt reduzieren und Kürzungen dokumentieren.
3. Pole des reduzierten \(sY(s)\) bestimmen.
4. Prüfen, ob alle Pole strikt in der linken Halbebene liegen.
5. Bei imaginärachsigen oder rechten Polen Satz ablehnen.
6. Bei unentscheidbaren Parameterannahmen `INCONCLUSIVE` ausgeben.
7. Nur bei gültiger Voraussetzung berechnen:
   \[
   y(\infty)=\lim_{s\to0}sY(s).
   \]
8. Wenn eine Zeitfunktion vorhanden ist, direkten Grenzwert vergleichen.
9. Verborgene gekürzte Modi separat warnen.

## 7.21 Stabilitäts- und Polhinweise

Es werden vier Polmengen unterschieden:

1. Systempole aus \(G(s)\),
2. Eingangspole aus \(U(s)\),
3. Ausgangspole aus reduziertem \(Y(s)\),
4. entfernte gemeinsame Faktoren.

Nur Systempole begründen die E/A-Stabilitätsaussage zum System. Ausgangspole erklären die konkrete Antwort und die Endwertsatzgültigkeit. Eingangspole dürfen nicht als instabile Systempole ausgegeben werden.

## 7.22 Abbruch bei nicht unterstützten oder uneindeutigen Fällen

Abbruch statt Raten bei:

- gemischten Variablen \(s,t\),
- nichtlinearen oder zeitvarianten DGL,
- fehlenden Anfangsbedingungen,
- unbestimmtem Leitkoeffizienten,
- nicht rationalem endgültigem Bildausdruck ohne direktes Tabellenpaar,
- nicht entscheidbarer Faktorart,
- höhergradigem irreduziblem Faktor außerhalb des Umfangs,
- singulärem PBZ-Koeffizientensystem,
- verbleibendem Polynomanteil bei gewünschter gewöhnlicher inverser Laplace,
- widersprüchlichen Parameterannahmen.

Der Abbruch erhält alle bis dahin sicheren Zwischenwerte.

---

# 8. Sonder- und Fehlerfälle

## 8.1 Gleichgradige Übertragungsfunktion

Ein gleichgradiges \(G(s)\) darf für eine Sprungantwort weiterverarbeitet werden:

\[
Y(s)=G(s)\frac{A}{s}.
\]

Erst \(Y(s)\) wird auf ordinary-time inverse Laplace geprüft.

Für eine Impulsantwort würde der Direktterm einen Dirac-Anteil erzeugen. Dieser Fall ist nicht Teil des ersten Umfangs.

## 8.2 Unechte endgültige Bildfunktion

Wenn nach Bildung des endgültigen \(Y(s)\) ein nichtnull Polynomquotient bleibt, wird die Division vollständig gezeigt. Die gewöhnliche inverse Laplace bricht mit `DISTRIBUTIONAL_INVERSE_UNSUPPORTED` ab.

## 8.3 Gemeinsame Faktoren

Beispiel:

\[
G_{\mathrm{roh}}(s)=\frac{s+1}{(s+1)(s+2)}.
\]

Ausgabe:

\[
G_{\mathrm{red}}(s)=\frac1{s+2},
\]

zusätzlich:

- entfernte Nullstelle/Polfaktor \(s+1\),
- Warnung zu möglicher verborgener Dynamik,
- externe Antwort aus der reduzierten Form.

## 8.4 Resonanz und erhöhte Multiplizität

Fällt ein Eingangspol mit einem Systempol zusammen, steigt die Multiplizität im Ausgang. Der PBZ-Kern behandelt dies exakt als Mehrfachpol. Es wird keine Sonderformel außerhalb des gemeinsamen Kerns benötigt.

## 8.5 Parameterabhängige Pole

Kann ohne zusätzliche Annahme nicht entschieden werden, ob ein quadratischer Faktor zwei reelle Pole, einen doppelten Pol oder ein komplexes Paar besitzt, wird keine Darstellung ausgewählt.

Ergebnis:

- erforderliche Diskriminantenbedingung,
- Status `PARAMETER_ASSUMPTIONS_INSUFFICIENT`,
- mögliche Falltypen,
- kein erfundener Rechenweg.

## 8.6 Pol auf der imaginären Achse

- Systemstatus: nicht asymptotisch stabil beziehungsweise E/A-instabil nach der verwendeten strikten Polbedingung,
- Zeitantwort kann eine Dauerschwingung besitzen,
- Endwertsatz in der Regel unzulässig,
- kein endlicher Endwert behaupten.

## 8.7 Instabiler Pol

- explizite Warnung,
- inverse Laplace wird trotzdem berechnet, sofern mathematisch unterstützt,
- Endwertsatz wird abgelehnt,
- wachsender Modus wird im Zeitbereich hervorgehoben.

## 8.8 Fehlende Anfangswerte

Eine DGL \(n\)-ter Ordnung verlangt \(n\) Anfangswerte \(y^{(0)}(0^+),\dots,y^{(n-1)}(0^+)\).

Bei Lücke:

- kein Transformationsschritt mit stiller Null,
- genaue fehlende Ordnung nennen,
- Nutzer kann Wert ergänzen oder explizite Nullpolitik aktivieren.

## 8.9 Numerische Dezimalwerte

- Eingaben wie `0.1` werden nach bestehender Parserpolitik möglichst exakt als \(1/10\) gespeichert,
- originale Texteingabe bleibt erhalten,
- numerische Näherungen sind sekundäre View-Werte,
- keine Float-Faktorisierung für symbolische PBZ.

## 8.10 Nicht unterstützte direkte Funktionen

Bei Funktionen außerhalb des Regelregisters:

- keine freie CAS-Inversion als scheinbar gesicherte Lösung,
- genaue Funktion benennen,
- bereits mögliche Linearitätszerlegung anzeigen,
- Status `UNSUPPORTED_TIME_FUNCTION`.

---

# 9. Verifikationen

## 9.1 Pflichtprüfungen je Workflow

| Workflow | Pflichtprüfungen |
|---|---|
| direkte Laplace | inverse Regel-/Tabellenprüfung, Variablentrennung |
| inverse Standardpaar | Vorwärtstransformation |
| PBZ | Faktorrekonstruktion, PBZ-Rückzusammenfassung |
| Polynomdivision | \(Z=QN+R\) |
| Sprungantwort | \(Y=GU\), inverse/vorwärts, Anfangswert, Endwertguard |
| allgemeine Antwort | \(Y=GU\), PBZ, Vorwärtstransformation, Polrollen |
| DGL-Lösung | transformierte DGL, Anfangswerte, DGL-Residuum, Vorwärtstransformation |
| Übertragungsfunktion aus DGL | Nullzustand, Rückmultiplikation, Grad-/Kürzungsbericht |

## 9.2 Verifikationsbericht

Der Bericht wird in drei Ebenen angezeigt:

1. **Kurzstatus:** bestanden, teilweise geprüft, fehlgeschlagen, nicht anwendbar.
2. **Einzelprüfungen:** je Prüfung Status und kurze Begründung.
3. **Details:** exakte Residuen, Annahmen und numerische Kontrollwerte.

## 9.3 Keine falsche Sicherheit

- Numerische Stichproben sind keine symbolischen Beweise.
- Ein CAS-Vergleich ist keine alleinige Abnahme.
- Nicht entscheidbare Parameterfälle werden nicht grün markiert.
- Eine reduzierte Ein-/Ausgangsantwort beweist keine interne Stabilität bei gekürzten Faktoren.

---

# 10. Schnittstellen zu vorhandenen Modulen

## 10.1 Transferfunktions- und Frequenzmodul

### Eingang in die Zeitbereichssäule

Übernahme eines vorhandenen `TransferFunctionAnalysis` beziehungsweise äquivalenten Objekts mit:

- Roh- und reduzierter Übertragungsfunktion,
- Zähler/Nenner,
- Pole/Nullstellen,
- Kürzungsbericht,
- Parameterannahmen.

Keine erneute Texteingabe und kein erneutes Parsing nötig.

### Rückgabe

- Zeitantwort,
- Ausgangs-\(Y(s)\),
- stationärer Wert,
- Polrollen,
- Warnungen.

Diese Ergebnisse dürfen im Frequenzmodul angezeigt, aber nicht dort neu berechnet werden.

## 10.2 Stabilitätsmodule

Die Zeitbereichssäule kann übergeben:

- Nennerpolynom einer rohen oder reduzierten Übertragungsfunktion mit klarer Rolle,
- Systempole,
- Annahmen,
- entfernte Faktoren,
- Stabilitätsstatus als Hinweis.

Hurwitz, Routh oder Nyquist bleiben für ihre eigene fachliche Stabilitätsanalyse verantwortlich. Die Zeitbereichssäule dupliziert deren Verfahren nicht.

## 10.3 Charakteristischer Polynomkern

Bei späterer DGL- oder Regelkreisintegration kann der Nenner als `CharacteristicPolynomialContract` übergeben werden. Der Zeitbereichsblock erzeugt keine Parameterregionen.

## 10.4 Standardglieder/Bode

Erkannte Zeitantworten dürfen optional mit vorhandenen Standardgliedlabels verknüpft werden. Die primäre PBZ darf davon nicht abhängen.

## 10.5 Worked Steps und LaTeX

- vorhandenes Schrittemodell konsumieren,
- keine zweite Schrittlistenstruktur,
- fachliche Operationen als neue Schrittarten ergänzen,
- vorhandene Gleichungs-, Tabellen- und Warnungsrenderer nutzen,
- neue LaTeX-Bausteine nur für Laplace-, PBZ- und Zeitantwortnotation ergänzen.

## 10.6 Diagnoseinfrastruktur

Neue Diagnosecodes werden in das vorhandene System eingebunden. Es wird kein paralleles Fehlerobjekt eingeführt.

---

# 11. GUI- und LaTeX-Integration

## 11.1 Arbeitsbereich

```text
Laplace und Zeitantwort
├── direkte Transformation
├── Bildbereich / inverse Transformation
├── Partialbruchzerlegung
├── Systemantwort
├── DGL und Anfangswerte        [ab PR 2]
├── Kontrollen
└── LaTeX
```

Die GUI bleibt ein gemeinsamer Arbeitsbereich. Keine Sammlung unabhängiger Einzelwerkzeuge mit redundanter Eingabe.

## 11.2 Zwingende GUI-Eingaben in PR 1

### Direkte Transformation

- Eingabefeld \(f(t)\),
- Parameterannahmen,
- Aktion „transformieren“.

### Inverse/PBZ

- Eingabefeld \(F(s)\) oder Übernahme aus vorherigem Schritt,
- Aktion „inverse Laplace/PBZ“,
- optional Anzeige Roh-/Reduktionsform.

### Systemantwort

- \(G(s)\) oder Übernahme aus Frequenzmodul,
- Signaltyp Einheitssprung, Exponential oder direkte \(U(s)\)-Eingabe,
- Amplitude beziehungsweise Signalparameter,
- Aktion „Zeitantwort berechnen“.

### Kontrollen

- Auswahl der anzuzeigenden Kontrolldetails,
- keine Schalter, die fachliche Voraussetzungen umgehen.

## 11.3 Zwingende GUI-Eingaben in PR 2

- Ausgangskoeffizienten nach Ableitungsordnung,
- optional Eingangskoeffizienten nach Ableitungsordnung,
- Eingangssignal oder forcing,
- Tabelle der Anfangswerte,
- explizite Aktion „alle fehlenden Anfangswerte auf null setzen“,
- Antwortanforderung: DGL lösen oder Übertragungsfunktion bilden,
- Nullzustandsbestätigung für Übertragungsfunktion.

## 11.4 Komfortfunktionen, nicht Pflicht

- freie textuelle DGL-Notation,
- automatisch generierte Koeffizientenfelder aus einem Text,
- Favoriten für Standardglieder,
- Zeitantwortplot,
- Kopieren einzelner Zwischenschritte,
- automatische Beispielbefüllung,
- erweiterte Parameterverwaltung,
- alternative komplexe Exponentialdarstellung,
- explizite Faltungsansicht.

## 11.5 Verbotene Berechnungen im UI-Renderer

- Ausdruck parsen,
- Variablen oder Parameter erkennen,
- DGL normalisieren,
- Anfangsbedingungen ergänzen,
- \(Y(s)\) oder \(G(s)\) bilden,
- Grad bestimmen,
- Polynomdivision,
- Faktorisierung,
- Multiplikitäten,
- PBZ-Ansatz,
- Koeffizientensystem lösen,
- inverse Laplace,
- Grenzwerte,
- Stabilitätsklassifikation,
- Warnungen ableiten,
- numerische Rundung festlegen,
- fachliche LaTeX-Gleichungen zusammensetzen.

## 11.6 Klausurtaugliche LaTeX-Struktur

### Direkte Transformation

\[
\begin{aligned}
f(t)&=\dots\\
F(s)&=\mathcal L\{f(t)\}\\
&=\dots\\
&=\boxed{\dots}
\end{aligned}
\]

### DGL

1. Ausgangs-DGL,
2. Transformationsregel je Ableitungsordnung,
3. eingesetzte Anfangswerte,
4. gesammelte Bildgleichung,
5. aufgelöstes \(Y(s)\),
6. Faktorisierung/PBZ,
7. Zeitfunktion,
8. Kontrollen.

### PBZ

- Nennerfaktorisierung,
- vollständiger Ansatz,
- Koeffizientengleichungen oder Einsetzschritte,
- PBZ-Ergebnis,
- Rücktransformation jedes Termtyps.

### Kürzungen

\[
G_{\mathrm{roh}}(s)=\dots,
\qquad
G_{\mathrm{red}}(s)=\dots
\]

mit explizitem Faktorbericht.

---

# 12. Referenzfälle

Die folgenden Fälle stammen vorrangig aus der bestehenden Fachspezifikation. Neue synthetische Fälle dienen nur der Vertrags- und Fehlerprüfung.

## RF-01 – direktes Laplace-Paar

**Quelle:** Tutorium 03, Aufgabe 2b.

\[
f(t)=2te^{-4t}
\]

Erwartet:

\[
F(s)=\frac{2}{(s+4)^2}.
\]

Pflichtschritte:

- \(t\leftrightarrow1/s^2\),
- Faktor 2,
- Dämpfungssatz \(s\mapsto s+4\),
- inverse Kontrolle.

## RF-02 – inverses Standardpaar mit komplexem Paar

**Quelle:** Tutorium 03, Aufgabe 2h.

\[
F(s)=\frac{s-4}{(s-4)^2+4}
\]

Erwartet:

\[
f(t)=e^{4t}\cos(2t).
\]

Zusatzhinweis: wachsender Modus wegen Realteil \(+4\).

## RF-03 – DGL mit Anfangswerten und Mehrfachpol

**Quelle:** Übung 03, Aufgabe 1.

\[
y''+2y'+y=9e^{2t},
\qquad y(0)=0,
\qquad y'(0)=1.
\]

Erwartet:

\[
Y(s)=\frac{s+7}{(s+1)^2(s-2)}
\]

und

\[
Y(s)=-\frac1{s+1}-\frac2{(s+1)^2}+\frac1{s-2},
\]

\[
y(t)=-e^{-t}-2te^{-t}+e^{2t}.
\]

Pflichtkontrollen:

- beide Anfangswerte,
- DGL-Residuum,
- PBZ-Rückzusammenfassung,
- Vorwärtstransformation.

## RF-04 – DGL zu Übertragungsfunktion bei Nullanfangswerten

**Quelle:** SS2025, Aufgabe 1d.

\[
\phi_G''(t)=\frac1{m_Kl}
\left(d_K\phi_G'(t)-F_A(t)-g(m_K+m_G)\phi_G(t)\right).
\]

Erwartet:

\[
G_S(s)=\frac{\Phi_G(s)}{F_A(s)}
=-\frac1{m_Kl\,s^2-d_Ks+g(m_K+m_G)}.
\]

Pflicht: Vorzeichen nicht „physikalisch“ korrigieren.

## RF-05 – fehlende Anfangsbedingung

Aus RF-03 abgeleitet, aber nur \(y(0)=0\) angegeben.

Erwartet:

- `MISSING_INITIAL_CONDITION`,
- fehlende Ordnung \(1\),
- kein stilles \(y'(0)=0\),
- kein \(Y(s)\)-Endergebnis.

## RF-06 – einfache reelle PBZ und PT1-Sprungantwort

**Quelle:** Tutorium 03, Aufgaben 3a/4a.

\[
G(s)=\frac1{2s+1},
\qquad A=0.1.
\]

Erwartet:

\[
Y(s)=\frac{0.1}{s(2s+1)}
=\frac{0.1}{s}-\frac{0.1}{s+0.5},
\]

\[
y(t)=0.1\left(1-e^{-0.5t}\right).
\]

Endwert:

\[
y(\infty)=0.1.
\]

## RF-07 – mehrfacher reeller Pol

PBZ-Teil aus RF-03:

\[
\frac{s+7}{(s+1)^2(s-2)}.
\]

Pflicht: Ansatz enthält \(1/(s+1)\) und \(1/(s+1)^2\).

## RF-08 – komplexes Paar ohne Endwert

**Quelle:** Tutorium 03, Aufgaben 3b/4b.

\[
G(s)=\frac{s}{s^2+\pi/4},
\qquad A=\frac\pi2.
\]

Erwartet:

\[
y(t)=\sqrt\pi\sin\left(\frac{\sqrt\pi}{2}t\right).
\]

Pflicht:

- reelle Ausgabe,
- Pole auf der imaginären Achse,
- Endwertsatz ungültig,
- kein stationärer Endwert.

## RF-09 – unechte rationale Funktion

**Aus Quellenregel abgeleitet.**

\[
F(s)=\frac{s^2+1}{s+1}.
\]

Erwartet:

\[
F(s)=s-1+\frac2{s+1}.
\]

Pflicht:

- Klassifikation `IMPROPER`,
- erfolgreiche Polynomdivision,
- Rekonstruktion,
- Abbruch der gewöhnlichen inversen Laplace wegen Polynomanteil.

## RF-10 – allgemeiner Exponentialeingang

Verwendung des Systems

\[
G(s)=\frac1{(s+1)^2}
\]

und

\[
u(t)=9e^{2t},
\qquad U(s)=\frac9{s-2}.
\]

Erwartet:

\[
Y(s)=\frac9{(s+1)^2(s-2)}
=-\frac1{s+1}-\frac3{(s+1)^2}+\frac1{s-2},
\]

\[
y(t)=-e^{-t}-3te^{-t}+e^{2t}.
\]

Der Fall prüft Eingangspol, Systemmehrfachpol und gemeinsame PBZ-Orchestrierung. Die Zeitantwort wird durch Vorwärtstransformation geprüft.

## RF-11 – gültiger Endwertsatz

**Quelle:** Übung zum Endwertsatz.

\[
Y(s)=\frac1s\cdot
\frac1{(T_1s+1)(T_2s+1)+K_R(T_2s+1)},
\qquad K_R=24.
\]

Unter gültiger Polbedingung:

\[
y(\infty)=\frac1{25}=0.04.
\]

## RF-12 – ungültiger Endwertsatz

Verwendung von RF-08.

Erwartet:

- Pole von \(sY(s)\) nicht strikt links,
- `END_VALUE_THEOREM_INVALID`,
- kein algebraischer Grenzwert als stationärer Wert ausgeben.

## RF-13 – gemeinsame Faktoren

Synthetischer Regressionstest:

\[
G_{\mathrm{roh}}(s)=\frac{s+1}{(s+1)(s+2)}.
\]

Erwartet:

\[
G_{\mathrm{red}}(s)=\frac1{s+2}.
\]

Pflicht:

- Faktor \(s+1\) im Kürzungsbericht,
- `CANCELLED_COMMON_FACTOR`,
- `HIDDEN_MODE_POSSIBLE`,
- externe Antwort mit reduzierter Form.

## RF-14 – vollständige Rückprüfung PT2-Parameterfall

**Quelle:** Übung 03, Feder-Masse-Dämpfer.

\[
G(s)=\frac1{Ms^2+\eta s+k},
\qquad U(s)=\frac{F_{\mathrm{ext}}}{s}.
\]

Unter

\[
\delta=\frac{\eta}{2M},
\qquad
\omega=\sqrt{\frac{k}{M}-\delta^2},
\qquad
\omega>0,
\]

Erwartet:

\[
y(t)=\frac{F_{\mathrm{ext}}}{k}
\left[
1-e^{-\delta t}
\left(
\cos(\omega t)+\frac{\delta}{\omega}\sin(\omega t)
\right)
\right].
\]

Pflicht:

- Annahme für unterdämpften Fall,
- Anfangswerte null,
- DGL-Residuum,
- Endwert \(F_{\mathrm{ext}}/k\),
- reelle Polpaarform.

---

# 13. Gezielte Tests

## 13.1 Domain-Tests

Kleine deterministische Tests ohne GUI und ohne vollständigen Workflow:

1. Parserprofile trennen \(s\) und \(t\).
2. `InitialConditionSet` erkennt fehlende Ordnung.
3. `RationalClassification` unterscheidet streng echt, gleichgradig und unecht.
4. Polynomdivision rekonstruiert den Dividend.
5. Faktorstruktur erkennt einfache und mehrfache lineare Faktoren.
6. Faktorstruktur erkennt irreduzibles Quadrat.
7. Parameterabhängige Diskriminante erzeugt `INCONCLUSIVE` statt geratenem Faktor.
8. PBZ-Template enthält alle Potenzen eines Mehrfachfaktors.
9. Quadratischer PBZ-Zähler hat Grad höchstens eins.
10. Exaktes Koeffizientensystem liefert eindeutige Koeffizienten.
11. PBZ-Rückzusammenfassung ist exakt null.
12. Inverse Regel für \((s-p)^{-k}\) enthält \((k-1)!\).
13. Komplexe Paare werden reell zusammengeführt.
14. Kürzungsbericht erhält Roh- und Reduktionsform.
15. Polrollen System/Eingang/Ausgang bleiben getrennt.
16. Endwertguard lehnt imaginärachsige Pole ab.

## 13.2 Workflow-Tests

Priorisierte End-to-End-Tests:

| Priorität | Fall | Ziel |
|---:|---|---|
| P0 | RF-06 | erster sichtbarer Sprungantwort-Workflow |
| P0 | RF-07 | Mehrfachpol-PBZ |
| P0 | RF-08 | komplexes Paar und ungültiger Endwert |
| P0 | RF-09 | unechte Funktion/Polynomdivision |
| P0 | RF-03 | vollständiger DGL-Workflow nach PR 2 |
| P0 | RF-04 | Übertragungsfunktion aus DGL |
| P0 | RF-05 | fehlende Anfangsbedingung |
| P1 | RF-01 | direkte Transformation |
| P1 | RF-02 | inverse Standardform |
| P1 | RF-10 | allgemeiner Eingang |
| P1 | RF-11 | gültiger Endwert |
| P1 | RF-13 | Kürzungswarnung |
| P1 | RF-14 | vollständige Rückprüfung und Parameterannahme |

## 13.3 Presenter-/LaTeX-Smoke-Tests

Nur wenige stabile Tests:

1. RF-01: \(\mathcal L\)-Notation und Dämpfungssatz.
2. RF-03: alle Anfangswertterme sichtbar.
3. RF-07: vollständiger Mehrfachpolansatz.
4. RF-08: reelle Sinus-/Kosinusform.
5. RF-09: Polynomdivision plus Unsupported-Hinweis.
6. RF-13: Roh-/Reduktionsform und Warnung.

Keine Golden-Tests für jede numerische Variante.

## 13.4 Nicht benötigte Volltests

Nicht erforderlich:

- erneute Volltests des bestehenden Frequenzgangs,
- erneute Volltests aller vorhandenen Pole-/Nullstellenfunktionen,
- Tests interner SymPy-Standardfunktionen,
- dutzende Koeffizientenvarianten desselben PBZ-Musters,
- GUI-Pixeltests jeder Formel,
- Volltest der gesamten App nach jeder kleinen Domainänderung.

Ein vollständiger Regressionstest der App ist vor Merge jedes PR einmal erforderlich.

## 13.5 Abnahmeregel je PR

### PR 1

Muss bestehen:

- RF-01, RF-02, RF-06, RF-07, RF-08, RF-09, RF-10, RF-11, RF-12, RF-13,
- alle zugehörigen Domain-Tests,
- Presenter-Smoke-Tests,
- ein manueller GUI-Durchlauf von RF-06 und RF-08.

### PR 2

Muss zusätzlich bestehen:

- RF-03, RF-04, RF-05, RF-14,
- vollständige Anfangswert- und DGL-Residuenprüfung,
- manueller GUI-Durchlauf von RF-03 und RF-04.

---

# 14. Codex-Aufwand

## 14.1 Aufwand je PR

### PR 1 – PBZ-/Inverse-Kern

**Größe:** groß, aber intern kohärent.  
**Anteil am Gesamtaufwand:** ungefähr 55–65 %.

Hauptaufwand:

- Vertragsadapter zum vorhandenen Rationalfunktionskern,
- exakte Faktorstruktur und Multiplizitäten,
- PBZ-Template und Koeffizientensystem,
- inverse Termabbildung,
- Verifikationsberichte,
- erster GUI-/Presenter-/LaTeX-Workflow.

### PR 2 – DGL/Laplace-Orchestrierung

**Größe:** mittel bis groß.  
**Anteil am Gesamtaufwand:** ungefähr 35–45 %.

Hauptaufwand:

- strukturierte DGL-Eingabe,
- Anfangsbedingungsvertrag,
- Ableitungssatz,
- Bildung von \(Y(s)\) und \(G(s)\),
- Signaltypen,
- DGL-Residuum,
- GUI-Erweiterung.

## 14.2 Tokenökonomische Regeln

- Vor Implementierung vorhandene Parser-, Rational-, Diagnose-, Worked-Step- und LaTeX-Schnittstellen einmal inventarisieren.
- Keine neue generische Symbolikschicht einführen.
- Keine lange Fachanalyse durch Codex erzeugen lassen.
- Pro PR nur die hier definierten Referenzfälle implementieren und prüfen.
- Korrekturen nach manueller Prüfung bündeln.
- Volltests nur vor Merge oder nach einer tiefen Vertragsänderung.
- Keine vorzeitige Refaktorierung des gesamten Projekts.

---

# 15. Risiken

## 15.1 Parserduplikation

**Risiko:** Ein neuer Zeitparser entwickelt eigene Whitelists, Parameterregeln und Fehlermeldungen.  
**Gegenmaßnahme:** gemeinsames Parser-Frontend mit Modusprofilen.

## 15.2 Vermischung von \(s\) und \(t\)

**Risiko:** Ausdrücke werden im falschen Bereich interpretiert.  
**Gegenmaßnahme:** Hauptvariable ist Vertragsbestandteil; Mischzustand ist harter Validierungsfehler.

## 15.3 Verlust der Rohform

**Risiko:** Kürzungen verschwinden vor PBZ, Stabilitäts- oder Warnungsanalyse.  
**Gegenmaßnahme:** `RationalAnalysisSnapshot` hält Roh- und Reduktionsform unveränderlich.

## 15.4 Falsche Behandlung gleichgradiger Funktionen

**Risiko:** gleichgradiges \(G(s)\) wird zu früh abgelehnt oder der Direktterm geht verloren.  
**Gegenmaßnahme:** Klassifikation immer rollenbezogen; erst endgültiges Inversziel auf Distributionsterme prüfen.

## 15.5 Numerische statt exakte Mehrfachpole

**Risiko:** ein doppelter Pol wird als zwei nahe Pole behandelt.  
**Gegenmaßnahme:** exakte Faktorisierung und Multiplizitätsprüfung; keine Float-Root-Zerlegung für PBZ.

## 15.6 Parameterabhängige Faktorart

**Risiko:** ein quadratischer Faktor wird ohne Annahmen als reell oder komplex klassifiziert.  
**Gegenmaßnahme:** Diskriminantenbedingung und `INCONCLUSIVE`.

## 15.7 Allgemeine CAS-Abhängigkeit

**Risiko:** Black-Box-Ergebnis ohne klausurtauglichen Rechenweg.  
**Gegenmaßnahme:** Regelregister und algorithmischer PBZ-Pfad sind autoritativ; CAS nur als Kontrolle.

## 15.8 Fehlende Anfangswerte

**Risiko:** Bibliotheksstandard setzt sie auf null.  
**Gegenmaßnahme:** Vollständigkeitsprüfung vor Transformation, explizite Nullpolitik.

## 15.9 Verwechslung von System- und Eingangspolen

**Risiko:** ein wachsender Eingang wird als instabiles System gemeldet.  
**Gegenmaßnahme:** getrennte Polrollen im Ergebnisvertrag.

## 15.10 Endwertsatz ohne Gültigkeitsprüfung

**Risiko:** algebraisch endlicher Wert trotz Dauerschwingung oder Instabilität.  
**Gegenmaßnahme:** Polguard ist zwingender Vorgänger des Grenzwerts.

## 15.11 Presenter berechnet Fachlogik

**Risiko:** andere Ergebnisse in GUI und LaTeX.  
**Gegenmaßnahme:** Presenter konsumiert ein vollständiges Domainergebnis; Renderer rechnet nichts.

## 15.12 Zu großer erster PR

**Risiko:** Variante C wird faktisch zu Variante A erweitert.  
**Gegenmaßnahme:** PR 1 beginnt nur bei \(F(s)\), \(G(s)\) oder direktem \(U(s)\); strukturierte DGL bleibt PR 2.

## 15.13 Zu kleiner erster PR

**Risiko:** nur einfache Pole und Tabellenfälle; geringer Klausurnutzen.  
**Gegenmaßnahme:** Mehrfachpole, komplexe Paare, Polynomdivision und Sprungantwort sind harte PR-1-Abnahmekriterien.

---

# 16. Empfohlene Implementierungsreihenfolge

## 16.1 Vorbereitende Inventur

1. Vorhandene Parserprofile, Symbolregistrierung und Parameterannahmen lokalisieren.
2. Vorhandenes Rationalfunktionsobjekt und Kürzungsprotokoll dokumentieren.
3. Vorhandene Pole-/Nullstellen- und Vielfachheitsdarstellung prüfen.
4. Worked-Step-, Diagnose-, Presenter- und LaTeX-Verträge prüfen.
5. GUI-Erweiterungspunkt für den Arbeitsbereich „Laplace und Zeitantwort“ bestimmen.
6. Keine Fachfunktion implementieren, bevor die Wiederverwendungspunkte feststehen.

## 16.2 Vertragsfreeze vor PR 1

Die Verträge aus Abschnitt 6 werden gegen die tatsächliche Codebasis gemappt. Besonders vorab festlegen:

- Rollen rationaler Ausdrücke,
- Roh-/Reduktionsform,
- Polynomdivision,
- Faktorstruktur,
- PBZ-Term,
- Verifikationsitem,
- `InitialConditionSet` und `LinearOdeInput`, auch wenn sie erst PR 2 konsumiert.

Ziel: PR 2 darf den PBZ-Kern erweitern, aber nicht dessen öffentliche Verträge brechen.

## 16.3 PR 1 – Domainkern

1. Parser-Modusprofile für \(s\) und \(t\) ergänzen.
2. Adapter auf vorhandene rationale Analyse einführen.
3. Rollenbezogene Gradklassifikation implementieren.
4. Polynomdivision und Rekonstruktionsprüfung anbinden.
5. Reelle Faktorstruktur und Multiplizitäten erzeugen.
6. PBZ-Ansatz aus der Faktorstruktur generieren.
7. Exaktes Koeffizientensystem lösen.
8. PBZ-Rückzusammenfassung prüfen.
9. Inverse Regeln für lineare Mehrfachpole und quadratische Faktoren anwenden.
10. Komplexe Paare reell zusammenfassen.

## 16.4 PR 1 – Workflows und Integration

11. Direkte Standard-Laplace-Regeln anbinden.
12. Inverse Standardpaare vor dem PBZ-Pfad erkennen.
13. Inverse-Laplace-Workflow aus \(F(s)\) erstellen.
14. Sprungantwort aus \(G(s)\) erstellen.
15. allgemeine Antwort aus \(G(s),U(s)\) erstellen.
16. Exponentialeingang als typisierten Signalpfad anbinden.
17. Anfangswert-, Endwert-, Pol- und Kürzungskontrollen anbinden.
18. Worked Steps und LaTeX erzeugen.
19. Minimale GUI im gemeinsamen Zeitbereichsarbeitsbereich anbinden.
20. PR-1-Referenz- und Smoke-Tests ausführen.
21. Manuell RF-06 und RF-08 prüfen.
22. Gebündelte Korrektur, Volltest, Merge.

## 16.5 PR 2 – DGL-Kern

1. Strukturierte DGL-Eingabe auf `LinearOdeInput` abbilden.
2. `InitialConditionSet` mit Vollständigkeits- und Nullzustandspolitik anbinden.
3. DGL normalisieren und Ordnung prüfen.
4. Ableitungssatz je Term anwenden.
5. Bildgleichung und Anfangswertanteil erzeugen.
6. Nach \(Y(s)\) auflösen.
7. freie und erzwungene Antwort trennen.
8. Übertragungsfunktion nur bei zulässigem Nullzustand bilden.
9. PR-1-Rational-/PBZ-/Inverse-Kern konsumieren.

## 16.6 PR 2 – Eingänge, Kontrollen und GUI

10. Polynom-, Sinus- und Kosinuseingänge ergänzen.
11. vollständige Anfangsbedingungsprüfung implementieren.
12. DGL-Residuum implementieren.
13. Vorwärts-/Rücktransformationsbericht vervollständigen.
14. DGL- und Anfangswertansicht in denselben GUI-Arbeitsbereich integrieren.
15. LaTeX für DGL-Schritte ergänzen.
16. RF-03, RF-04, RF-05 und RF-14 ausführen.
17. Manuell RF-03 und RF-04 prüfen.
18. Gebündelte Korrektur, Volltest, Merge.

## 16.7 Nach beiden PRs

1. GUI kurz konsolidieren und redundante Eingaben entfernen.
2. Direkte Übergabe aus Frequenz- und Regelkreismodulen prüfen.
3. Roadmapstatus knapp aktualisieren.
4. Erst danach Impulsantwort, Zeitverschiebung oder Faltung neu priorisieren.

---

# Verbindliche Schlussentscheidung

Die Zeitbereichssäule wird nicht als ein riesiger Branch und nicht in der fachlich ungünstigen Reihenfolge „DGL zuerst, inverse Lösung später“ umgesetzt.

\[
\boxed{
\text{PR 1: PBZ/inverse Laplace + sichtbare Zeitantwort}
\rightarrow
\text{PR 2: DGL/Anfangswerte/weitere Eingänge}
}
\]

Mehrfachpole und komplexe Paare bleiben Bestandteil des ersten PBZ-Kerns. Der erste Merge liefert bereits einen vollständigen klausurtauglichen Workflow ab \(F(s)\) oder \(G(s)\); der zweite Merge schließt den DGL-Einstieg und die vollständige Zeitbereichssäule.
