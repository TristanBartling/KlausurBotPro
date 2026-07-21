# KlausurBotPro – Implementierungspaket Hurwitz/Routh

**Datei:** `KlausurBotPro_Implementierungspaket_Hurwitz_Routh.md`  
**Status:** implementierungsfertige, codefreie Fach- und Schnittstellenspezifikation  
**Erster sichtbarer Verbraucher des gemeinsamen Polynom-/Parameterkerns:** Hurwitz  
**Nicht enthalten:** Softwareimplementierung, Codex-Prompt, DGL-/Laplace-/Regelkreislogik, allgemeines Stabilitäts-CAS

---

## Maßgebliche Referenzen

1. `docs/KlausurBotPro_Architekturplan.md`
2. `docs/reference/KlausurBotPro_Fachspezifikation_Hurwitz_Routh.md`
3. `docs/reference/KlausurBotPro_Fachspezifikation_Charakteristische_Polynome_Parameterbedingungen.md`
4. `KlausurBotPro_Implementierungspaket_Polynom_Parameterkern.md`
5. Fachquellen nur für Referenzfälle und Quellenkontrolle:
   - `skript.pdf`, Kapitel 5.3–5.4
   - `Regelungstechnik_Übung_Aufg-u-Lösungen.pdf`, Übung 09 Aufgabe 3
   - `Regelungstechnik_Tutorium_komplett.pdf`, Tutorium 09 Aufgabe 3
   - `RT_Klausur_SS2025-komplett.pdf`, Aufgabe 4b
   - `RT-Klausur_WS_25_26-komplett.pdf`, Aufgabe 4b

Die Fachspezifikationen bleiben fachlich verbindlich. Dieses Paket entscheidet den kleinsten wirtschaftlichen Implementierungszuschnitt und präzisiert die Verträge zwischen gemeinsamem Kern, Hurwitz, Presenter und GUI.

---

# 1. Endentscheidung

## 1.1 Wirtschaftlich beste Paketform

Die Optionen A und D beschreiben unterschiedliche Ebenen und sind nicht vollständig gegenseitig ausschließend:

- **A** beschreibt den Inhalt des ersten PRs.
- **D** beschreibt die zeitliche Reihenfolge zwischen Hurwitz und Routh.

Die verbindliche Entscheidung lautet daher:

\[
\boxed{
\text{PR 1: kleiner gemeinsamer Polynom-/Parameterkern + Hurwitz}
}
\]

\[
\boxed{
\text{PR 2: Routh später unter Wiederverwendung derselben Verträge}
}
\]

Falls genau eine der vorgegebenen Paketvarianten gewählt werden muss, ist **Variante A** die korrekte Wahl. Die anschließende Roadmap folgt **Variante D**.

## 1.2 Harte Konsequenz

Der erste PR enthält:

- die bereits spezifizierte, klein gehaltene Polynomkanonisierung;
- die für Hurwitz tatsächlich benötigte 0D-/1D-/begrenzte 2D-Bedingungsauswertung;
- Hurwitz Grad 2 bis 4;
- Grad-1-Unterstützung ausschließlich als billigen Gradabfall-Fallback;
- sichtbare GUI-Anbindung;
- Worked Steps und LaTeX;
- gezielte Referenztests.

Der erste PR enthält **kein Routh-Schema**. Es werden auch keine Routh-Platzhalterklassen implementiert. Die gemeinsamen Verträge müssen lediglich methodenneutral bleiben, damit Routh später denselben Polynom- und Parameterkern konsumieren kann.

---

# 2. Kritische Prüfung des Implementierungspakets des gemeinsamen Kerns

## 2.1 Unverändert zu übernehmen

Folgende Festlegungen des Kernpakets sind fachlich und wirtschaftlich richtig:

1. Der gemeinsame Kern besitzt keine Hurwitz-, Routh- oder sonstige Stabilitätslogik.
2. Der Kern kanonisiert nur bereits erzeugte charakteristische Polynome.
3. Hurwitz erzeugt Koeffizienten- und Determinantenbedingungen selbst.
4. Der Parameterkern löst nur bereits erzeugte Gleichungen und Ungleichungen.
5. Polynomrolle, Analyseziel, Annahmen, Ausschlussmengen und Provenienz bleiben erhalten.
6. Gradfälle werden vor einer gefährlichen Division durch einen parameterabhängigen Leitkoeffizienten erzeugt.
7. Exakte Ausdrücke sind primär; numerische Werte dienen nur der Kontrolle und Darstellung.
8. Rohes internes charakteristisches Polynom und reduzierter E/A-Nenner sind getrennte Analyseobjekte.
9. Strikte Stabilitätsgrenzen bleiben strikt offen.
10. Ein gemeinsamer vertikaler PR mit Hurwitz als erstem Verbraucher ist wirtschaftlicher als ein isolierter Infrastruktur-PR.

## 2.2 Notwendige Korrekturen und Präzisierungen

### Korrektur K1 – parameterfreie Fälle benötigen einen echten Kernvertrag

Das Kernpaket beschreibt `ParameterConditionProblem` bisher im Wesentlichen für ein oder zwei Entscheidungsparameter. Hurwitz benötigt aber auch parameterfreie Ergebnisse.

Verbindliche Ergänzung:

```text
requested_result_kind:
- BOOLEAN
- ONE_DIMENSIONAL
- TWO_DIMENSIONAL
```

`variables` darf 0, 1 oder 2 reelle Entscheidungsparameter enthalten.

Für `variables=[]` wird ein `ZeroDimensionalConditionResult` zurückgegeben:

```text
status:
- TRUE
- FALSE
- UNDECIDABLE_UNDER_ASSUMPTIONS
- INVALID
```

Ohne diesen Vertrag wäre der parameterfreie Hurwitz-Fall technisch unsauber zwischen Fachmodul und Kern verteilt.

### Korrektur K2 – das Hurwitz-Modul konsumiert kanonische Gradfälle, nicht erneut Rohpolynome

Der öffentliche Datenfluss lautet:

```text
CharacteristicPolynomialInput
    -> gemeinsamer Kern
CanonicalCharacteristicPolynomial
    -> einzelne PolynomialDegreeCase
    -> Hurwitz
```

Hurwitz darf nicht erneut expandieren, sammeln, den Grad bestimmen oder das Vorzeichen normieren. Es validiert lediglich die vom Kern gelieferten Invarianten.

### Korrektur K3 – keine monische Normierung als Standard

Für Hurwitz ist nur ein sicher positiver Leitkoeffizient erforderlich. Eine Division durch den Leitkoeffizienten ist weder fachlich notwendig noch wirtschaftlich sinnvoll.

Verbindlich:

- Vorzeichennormierung ist erlaubt.
- Entfernung eines nachweislich positiven konstanten Faktors ist erlaubt.
- Monische Normierung ist optional und im ersten PR standardmäßig deaktiviert.
- Parameterabhängige Divisionen dürfen keine zusätzlichen rationalen Bedingungen und Nennerausschlüsse erzeugen, wenn sie für Hurwitz nicht benötigt werden.

Damit werden Ausdrucksexplosion und unnötige Nennerfälle vermieden.

### Korrektur K4 – `CLOSED_TRANSFER_DENOMINATOR` ist zu mehrdeutig

Für Hurwitz werden nur folgende Rollen akzeptiert:

```text
DIRECT_CHARACTERISTIC_POLYNOMIAL
STATE_CHARACTERISTIC_POLYNOMIAL
RAW_CLOSED_LOOP_CHARACTERISTIC
REDUCED_TRANSFER_DENOMINATOR
```

Die unscharfe Rolle `CLOSED_TRANSFER_DENOMINATOR` wird im Hurwitz-MVP nicht akzeptiert. Der Produzent muss explizit angeben, ob der Nenner roh oder reduziert ist.

### Korrektur K5 – Kürzungsbericht nur dort erzwingen, wo er fachlich Sinn ergibt

`CancellationReport` ist Pflicht bei:

- `REDUCED_TRANSFER_DENOMINATOR`;
- transferfunktionsbasierten E/A-Analysen mit möglicher Kürzung.

Für direkte, Zustandsraum- und rohe geschlossene charakteristische Polynome lautet der Wert `NOT_APPLICABLE` oder `null`. Es darf kein künstlicher leerer Transferfunktionsbericht erfunden werden.

### Korrektur K6 – Rollen-/Zielvalidierung gehört vor jede Hurwitz-Aussage

Zulässige Kombinationen:

| Polynomrolle | zulässiges Analyseziel | Hurwitz-Aussage |
|---|---|---|
| `DIRECT_CHARACTERISTIC_POLYNOMIAL` | explizit vom Nutzer gewählt: intern oder E/A | nur entsprechend der gewählten Bedeutung |
| `STATE_CHARACTERISTIC_POLYNOMIAL` | `STATE_ASYMPTOTIC` | asymptotische Zustandsstabilität |
| `RAW_CLOSED_LOOP_CHARACTERISTIC` | `INTERNAL_CLOSED_LOOP_ASYMPTOTIC` | interne asymptotische Stabilität |
| `REDUCED_TRANSFER_DENOMINATOR` | `EXTERNAL_BIBO` | E/A-/BIBO-Stabilität bezüglich des reduzierten Nenners |

`DENOMINATOR_ANALYSIS_ONLY` liefert im ersten PR höchstens Matrix und Bedingungen, aber keine fachliche Stabilitätsaussage. Dieser Modus ist für das sichtbare MVP nicht erforderlich und kann zunächst abgelehnt werden.

### Korrektur K7 – konstante und Nullpolynomfälle nicht als stabil umdeuten

Der gemeinsame Kern bewertet diese Fälle korrekt nicht fachlich. Hurwitz übernimmt diese Zurückhaltung:

- `ZERO_POLYNOMIAL`: ungültige charakteristische Gleichung, Analyse nicht möglich.
- `CONSTANT_NONZERO`: kein Hurwitz-Fall; Ausgabe `NO_DYNAMIC_ROOT_POLYNOMIAL`, keine automatische Aussage „stabil“.

Ein konstantes Nennerpolynom reicht allein nicht aus, um BIBO-Stabilität einer möglicherweise unechten Übertragungsfunktion zu beweisen. Die Realisierbarkeit liegt upstream.

### Korrektur K8 – vollständige und minimale Bedingungen getrennt speichern

Hurwitz muss alle quellenkonformen Bedingungen erzeugen, darf dem Parameterkern aber ein logisch reduziertes System übergeben.

Pflichttrennung:

```text
full_generated_conditions
minimal_solver_conditions
condition_redundancy_records
```

Beispiel Grad 3:

- vollständig: alle `a_i>0`, `Delta_1>0`, `Delta_2>0`, `Delta_3>0`;
- minimal unter positivem Leitkoeffizienten: alle Koeffizienten positiv und `Delta_2>0`;
- `Delta_1` und `Delta_3` bleiben im Rechenweg sichtbar, obwohl sie solverseitig redundant sind.

### Korrektur K9 – erster 2D-Umfang enger als ein allgemeiner Kurvenanordnungs-Solver

Die beiden Klausurfälle ergeben jeweils ein einzelnes exaktes Band:

\[
x>x_{\min},\qquad y>\ell(x),\qquad y<u(x),
\]

mit linearer Untergrenze und quadratischer Obergrenze.

Für den ersten PR genügt:

- exakte Formelrepräsentation;
- exakte vertikale Domäne;
- eine untere Graphgrenze;
- eine obere Graphgrenze;
- Nachweis `lower < upper` auf der Domäne;
- ein `GraphBandCell`;
- exakte ausgeschlossene Ränder;
- numerische Plotgeometrie nur als Darstellung.

Nicht erforderlich ist im ersten PR eine allgemeine Anordnung beliebig vieler impliziter Kurven oder eine vollständige semialgebraische Zellzerlegung.

### Korrektur K10 – feste Symbole benötigen ausreichende Vorzeichenannahmen

Ein parameterfreies oder einparametriges Problem kann weiterhin ungelöste feste Symbole enthalten. Ein Ergebnis darf nur als exakt vollständig gelten, wenn die Annahmen alle für den Vergleich benötigten Vorzeichen und Ordnungen beweisen.

Fehlen solche Annahmen, lautet das Ergebnis:

- `UNDECIDABLE_UNDER_ASSUMPTIONS`, oder
- `PARTIALLY_SOLVED_SAFE` mit sichtbarer Restbedingung.

### Korrektur K11 – Routh nicht als Abnahmekriterium des ersten PRs verwenden

Die bestehende Fachspezifikation nennt Hurwitz/Routh-Gegenprüfung als sinnvoll. Wirtschaftlich ist dies für den ersten PR dennoch falsch, weil dafür der komplette zweite Fachverbraucher eingebaut werden müsste.

Im ersten PR gilt:

- numerische Polkontrolle als unabhängige Kontrolle;
- keine Routh-Implementierung;
- keine Routh-Cross-Tests als Merge-Blocker.

Routh/Hurwitz-Konsistenz wird Abnahmekriterium des späteren Routh-PRs.

---

# 3. Wirtschaftliche Paketentscheidung

## 3.1 Vergleich A–D

Bewertung: 1 = schlecht/niedrig, 5 = gut/hoch. Bei Risiko bedeutet 5 hohes Risiko.

| Kriterium | A: kleiner Kern + Hurwitz in einem PR | B: Kern-PR, danach Hurwitz-PR | C: Kern + Hurwitz + Routh | D: Hurwitz zuerst, Routh später |
|---|---:|---:|---:|---:|
| Codex-Verbrauch gesamt | **4** | 2 | 1 | **4** |
| doppelte Vertragsarbeit | **5** | 2 | 4 | **5** bei Kern im Hurwitz-PR |
| Testwiederholungen | **5** | 2 | 2 | **5** |
| sichtbarer Nutzerwert nach erstem PR | **5** | 1 | 5 | **5** |
| direkte Klausurpunkte | **5** | 1 im ersten PR | 5 | **5** |
| Branch-Risiko | 3 | 2 je Branch, aber 4 gesamt | 5 | 3 |
| spätere Wiederverwendung | **5** | 5 | 5 | **5** |
| Gefahr allgemeiner Abstraktionen | 2 | 5 | 4 | 2 |
| Gefahr späteren Refactorings | 2 | 4 | 3 | 2 |
| GUI-/Presenter-Doppelarbeit | **5** | 2 | 3 | **5** |

## 3.2 Bewertung der einzelnen Varianten

### A. Hurwitz und notwendiger kleiner Parameterkern in einem PR

**Vorteile**

- entspricht dem vertikalen Architekturprinzip;
- belastet die Kernverträge sofort mit einem realen Verbraucher;
- deckt die beiden punktestarken Klausurtypen direkt ab;
- nur eine Repository-Inventur und eine GUI-Anbindung;
- Kern- und Hurwitz-Tests teilen dieselben Referenzfälle.

**Nachteile**

- mittlerer bis hoher PR-Umfang;
- 2D-Bereich und Hurwitz müssen gemeinsam stabilisiert werden.

**Urteil:** wirtschaftlich beste erste Paketform.

### B. Gemeinsamer Kern zuerst, Hurwitz danach

**Vorteile**

- kleinere Einzelbranches;
- scheinbar saubere Infrastrukturtrennung.

**Nachteile**

- erster PR besitzt keinen Nutzerwert und keine Klausurpunkte;
- Verträge werden ohne echten Verbraucher festgelegt;
- erneute Repository-, Test-, Presenter- und Integrationsarbeit;
- wahrscheinlich spätere Korrektur der 0D- und 2D-Verträge.

**Urteil:** technisch sauber wirkend, wirtschaftlich schwach.

### C. Hurwitz und Routh gemeinsam mit Kern

**Vorteile**

- sofortige methodische Gegenprüfung;
- gemeinsamer Stabilitätsarbeitsbereich vollständig.

**Nachteile**

- Routh hat in den untersuchten Klausuren keine direkte Aufgabenfundstelle;
- zusätzliche Tabellen-, Vorzeichenwechsel-, Sonderfall-, GUI- und LaTeX-Logik;
- höheres Branch-Risiko;
- verführt zur Aufnahme schlecht belegter Sonderfälle;
- Hurwitz-Nutzen wird unnötig verzögert.

**Urteil:** schlechtes Nutzen-Aufwand-Verhältnis für den ersten PR.

### D. Hurwitz zuerst, Routh später unter Wiederverwendung der Verträge

**Vorteile**

- korrekte fachliche Priorisierung;
- Routh kann gegen einen stabilen gemeinsamen Kern implementiert werden;
- Sonderfälle lassen sich gezielt nach realem Bedarf ergänzen.

**Nachteile**

- beschreibt allein nicht, ob der Kern gemeinsam mit Hurwitz oder separat gebaut wird.

**Urteil:** richtige Roadmap, aber als Paketentscheidung nur zusammen mit A vollständig.

## 3.3 Verbindliche Empfehlung

```text
PR 1 = Variante A
Gesamtreihenfolge = Variante D
```

---

# 4. Umfang des ersten PRs

## 4.1 Enthalten

### Gemeinsamer Kern

- `CharacteristicPolynomialInput` validieren;
- Polynom exakt kanonisieren;
- vollständige Gradfälle erzeugen;
- sichere Vorzeichennormierung;
- Bedingungen mit 0, 1 oder 2 Entscheidungsparametern auswerten;
- exakte 1D-Intervallvereinigungen;
- begrenzte 2D-Graphbänder für die Klausurfälle;
- Annahmen, Ausschlüsse, Provenienz und Transformationshistorie erhalten;
- strukturierte Diagnosen;
- LaTeX-fähige Ergebnisobjekte.

### Hurwitz

- primäre Grade 2, 3 und 4;
- Grad 1 ausschließlich als Gradabfall-Fallback;
- notwendige Koeffizientenbedingungen;
- Hurwitz-Matrix nach Skriptkonvention;
- führende Hauptminoren;
- exakte Determinanten und Faktorisierungen;
- vollständige und minimale Bedingungssysteme;
- parameterfreie, einparametrige und zweiparametrige Ergebnisse;
- strikte Grenzbehandlung;
- Roh-/reduziert- und Stabilitätszielvalidierung;
- numerische Polkontrolle als Kontrollschritt;
- Worked Steps, GUI und LaTeX.

## 4.2 Nicht enthalten

- DGL- oder Laplace-Transformation;
- Bildung einer Übertragungsfunktion;
- Blockschaltbild- oder Regelkreisreduktion;
- Bildung von `1+L(s)=0`;
- Entscheidung über Rückkopplungsvorzeichen;
- Transferfunktionskürzung;
- allgemeiner 2D-CAS;
- mehr als zwei Entscheidungsparameter;
- beliebige Polynomgrade;
- Routh-Schema;
- Routh-Sonderfälle;
- symbolischer allgemeiner Polklassifikator;
- Grenzstabilitätsbeweis allein aus einer Determinantengleichheit;
- automatische interne Stabilitätsanalyse aus einer reduzierten Übertragungsfunktion ohne Rohpolynom.

---

# 5. Hurwitz-MVP

## 5.1 Eingangspolynom

Für jeden kanonischen Gradfall:

\[
p(s)=a_ns^n+a_{n-1}s^{n-1}+\dots+a_1s+a_0,
\qquad a_n>0
\]

Die Koeffizienten liegen absteigend vor:

\[
[a_n,a_{n-1},\dots,a_0].
\]

Hurwitz erzeugt intern zusätzlich eine indexierte Sicht:

```text
coefficient_by_power[0] = a_0
...
coefficient_by_power[n] = a_n
```

Nicht vorhandene Potenzen wurden bereits vom Kern als Nullkoeffizienten eingefügt.

## 5.2 Notwendige Bedingungen

Nach sicher positiver Normierung:

\[
\boxed{a_i>0\quad\text{für alle }i=0,\dots,n.}
\]

Diese Bedingungen sind für alle unterstützten Grade als einzelne Atome zu erzeugen. Ein identisch positiver numerischer Koeffizient wird nicht aus dem Rechenweg entfernt, kann aber solverseitig als bereits erfüllt markiert werden.

Ein identisch verschwindender Koeffizient macht asymptotische Stabilität unmöglich, sofern nicht gleichzeitig ein vorgelagerter Gradabfall vorliegt.

## 5.3 Hurwitz-Matrix

Verbindliche Skriptkonvention:

\[
H_n=
\begin{bmatrix}
a_1&a_3&a_5&a_7&\cdots\\
a_0&a_2&a_4&a_6&\cdots\\
0&a_1&a_3&a_5&\cdots\\
0&a_0&a_2&a_4&\cdots\\
0&0&a_1&a_3&\cdots\\
\vdots&\vdots&\vdots&\vdots&\ddots
\end{bmatrix}_{n\times n}.
\]

Koeffizienten außerhalb `0..n` werden als exakt null eingesetzt.

Die führenden Hauptminoren sind:

\[
\Delta_k=\det(H_n[1{:}k,1{:}k]),
\qquad k=1,\dots,n.
\]

## 5.4 Grad 2

\[
p(s)=a_2s^2+a_1s+a_0.
\]

\[
H_2=
\begin{bmatrix}
a_1&0\\
a_0&a_2
\end{bmatrix}.
\]

\[
\Delta_1=a_1,
\qquad
\Delta_2=a_1a_2.
\]

Vollständige erzeugte Bedingungen:

\[
a_2>0,\quad a_1>0,\quad a_0>0,
\quad \Delta_1>0,\quad \Delta_2>0.
\]

Minimales Solver-System nach positiver Normierung:

\[
\boxed{a_1>0,\qquad a_0>0.}
\]

## 5.5 Grad 3

\[
p(s)=a_3s^3+a_2s^2+a_1s+a_0.
\]

\[
H_3=
\begin{bmatrix}
a_1&a_3&0\\
a_0&a_2&0\\
0&a_1&a_3
\end{bmatrix}.
\]

\[
\Delta_1=a_1,
\]

\[
\Delta_2=a_1a_2-a_0a_3,
\]

\[
\Delta_3=a_3\Delta_2.
\]

Minimales Solver-System nach positiver Normierung:

\[
\boxed{
a_2>0,\quad a_1>0,\quad a_0>0,
\quad a_1a_2-a_0a_3>0
}.
\]

`Delta_1` und `Delta_3` bleiben als berechnete Determinanten sichtbar und erhalten Redundanzverweise.

## 5.6 Grad 4

\[
p(s)=a_4s^4+a_3s^3+a_2s^2+a_1s+a_0.
\]

\[
H_4=
\begin{bmatrix}
a_1&a_3&0&0\\
a_0&a_2&a_4&0\\
0&a_1&a_3&0\\
0&a_0&a_2&a_4
\end{bmatrix}.
\]

\[
\Delta_1=a_1,
\]

\[
\Delta_2=a_1a_2-a_0a_3,
\]

\[
\Delta_3=a_1a_2a_3-a_1^2a_4-a_0a_3^2,
\]

\[
\Delta_4=a_4\Delta_3.
\]

Minimales Solver-System nach positiver Normierung:

\[
\boxed{
a_3>0,\quad a_2>0,\quad a_1>0,\quad a_0>0,
\quad \Delta_2>0,\quad \Delta_3>0
}.
\]

Die Formel

\[
\Delta_4=a_4\Delta_3
\]

ist verbindlich. Eine Variante `Delta_4=a_0 Delta_3` ist für die verwendete Matrix falsch.

## 5.7 Grad 1 als Gradabfall-Fallback

\[
p(s)=a_1s+a_0,
\qquad a_1>0.
\]

\[
H_1=[a_1],
\qquad \Delta_1=a_1.
\]

Stabilitätsbedingung:

\[
\boxed{a_0>0.}
\]

Dieser Fall wird nicht als eigener Hauptmodus beworben, verhindert aber, dass ein legitimer Gradabfall von Grad 2 oder 3 unnötig unanalysierbar wird.

---

# 6. Stabilitätsbegriffe und Polynomrollen

## 6.1 Zustandsstabilität

Eingang:

```text
polynomial_role = STATE_CHARACTERISTIC_POLYNOMIAL
analysis_target = STATE_ASYMPTOTIC
```

Aussage:

> Alle Eigenwerte der Zustandsmatrix besitzen strikt negative Realteile.

## 6.2 Interne geschlossene Stabilität

Eingang:

```text
polynomial_role = RAW_CLOSED_LOOP_CHARACTERISTIC
analysis_target = INTERNAL_CLOSED_LOOP_ASYMPTOTIC
```

Aussage:

> Alle Wurzeln des rohen charakteristischen Polynoms des geschlossenen Kreises besitzen strikt negative Realteile.

Eine Transferfunktionskürzung darf diesen Eingang nicht ersetzen.

## 6.3 Externe E/A-/BIBO-Stabilität

Eingang:

```text
polynomial_role = REDUCED_TRANSFER_DENOMINATOR
analysis_target = EXTERNAL_BIBO
```

Aussage:

> Alle Pole der vollständig reduzierten rationalen Übertragungsfunktion liegen strikt in der linken Halbebene.

Zusätzliche upstream Voraussetzungen:

- rationale Übertragungsfunktion fachlich gültig;
- Reduktion vollständig dokumentiert;
- Realisierbarkeit/Echtheit nicht vom Hurwitz-Modul beurteilt.

## 6.4 Gleichheitsgrenzen

Für asymptotische und BIBO-Stabilität gilt:

\[
a_i>0,\qquad \Delta_k>0.
\]

Gleichheit ist ausgeschlossen.

Die Bezeichnung `grenzstabil` darf nur nach separater Pol- oder Faktoranalyse erfolgen. Aus `Delta_k=0` allein folgt nicht automatisch ein einfaches imaginäres Polpaar.

---

# 7. Parameterfälle

## 7.1 Parameterfreier Fall

Ablauf:

1. alle Koeffizientenbedingungen exakt auswerten;
2. alle Determinanten exakt auswerten;
3. Annahmen anwenden;
4. geschlossenes Bedingungssystem an den 0D-Kern übergeben;
5. Ergebnis zurückinterpretieren.

Mögliche Ergebnisse:

```text
ASYMPTOTICALLY_STABLE
NOT_ASYMPTOTICALLY_STABLE
UNDECIDABLE_UNDER_ASSUMPTIONS
DEGENERATE_NOT_APPLICABLE
INVALID_INPUT
```

Bei Instabilität werden alle nachweislich verletzten Bedingungen ausgegeben.

## 7.2 Einparametriger Fall

Der Parameterkern liefert eine exakte Vereinigung disjunkter Intervalle und gegebenenfalls isolierte Punkte. Für asymptotische Stabilität sind aktive Hurwitz-Grenzen offen.

Beispiel:

\[
p(s)=s^3+4s^2+5s+K_P
\]

\[
K_P>0,
\qquad 20-K_P>0
\]

\[
\boxed{0<K_P<20.}
\]

## 7.3 Zweiparametriger Fall

Im ersten PR unterstützt:

```text
x in exact open/closed interval or half-line
AND y > linear_or_quadratic_lower(x)
AND y < linear_or_quadratic_upper(x)
AND exact exclusions
```

Primäre Ergebnisform:

- exakte kombinierte Formel;
- exakte `x`-Domäne;
- exakte untere und obere Graphfunktion;
- Offenheit beider Grenzen;
- Nachweis, dass das Band auf der Domäne nicht leer ist;
- ein exakter Innenpunkt, wenn einfach konstruierbar;
- numerische Plotprojektion.

Mehrere disjunkte Bänder oder komplizierte implizite Kurven liefern im ersten PR ein sicheres Teilresultat mit Restbedingungen statt eines erfundenen vollständigen Gebiets.

---

# 8. Gradfälle und Leitkoeffizienten

## 8.1 Reihenfolge

1. Nominelles Polynom kanonisieren.
2. Leitkoeffizient auf `=0`, `>0`, `<0` zerlegen, soweit erforderlich.
3. Bei `=0` nächstniedrigeren Koeffizienten prüfen.
4. Gradreduktion wiederholen.
5. In jedem nichtdegenerierten Fall einen positiven Leitkoeffizienten herstellen.
6. Hurwitz fallweise ausführen.
7. Parameterlösungen fallweise bestimmen.
8. Vereinigen, ohne Fallprovenienz zu verlieren.

## 8.2 Parameterabhängiger Leitkoeffizient

Für

\[
a_n(\theta)
\]

werden grundsätzlich drei Zweige benötigt:

```text
a_n(theta) > 0  -> Polynom unverändert
a_n(theta) < 0  -> Multiplikation mit -1
a_n(theta) = 0  -> Gradabfall
```

Kann das Vorzeichen unter den vorhandenen Annahmen nicht in den unterstützten Parametergrenzen zerlegt werden, wird kein scheinbar vollständiges Ergebnis erzeugt.

## 8.3 Gradabfall ist kein gewöhnlicher Ausschlusspunkt

Ein Gradabfall kann selbst einen stabilen niedrigeren Grad ergeben. Er darf daher nicht pauschal aus der Lösungsmenge entfernt werden.

Beispiel des gezielten Gradfalltests:

\[
p(s;q)=qs^3+s^2+2s+1,
\qquad q\ge0.
\]

- Fall `q>0`, Grad 3:

\[
2-q>0\Rightarrow 0<q<2.
\]

- Fall `q=0`, Grad 2:

\[
s^2+2s+1
\]

ist asymptotisch stabil.

Gesamtergebnis unter `q>=0`:

\[
\boxed{0\le q<2}
\]

mit unterschiedlicher Gradprovenienz für `q=0` und `q>0`.

Dieser Fall ist ein synthetischer Vertragstest, keine originale Klausuraufgabe.

---

# 9. Entscheidung über Routh

## 9.1 Nicht im ersten PR

Routh wird vollständig aus dem ersten PR verschoben.

Begründung:

1. In den untersuchten Klausuren ist Hurwitz direkt mit jeweils 10 Punkten belegt; Routh nicht.
2. Die Standardtabelle wäre zwar relativ billig, erzeugt aber zusätzliche Ergebnisobjekte, GUI-Flächen, LaTeX-Renderer und Tests.
3. Ein gemeinsamer PR würde die wirtschaftlich wichtigste Hurwitz-Funktion verzögern.
4. Die Sonderfälle sind in den offiziellen Primärquellen nicht ausreichend systematisch belegt.
5. Numerische Polkontrolle genügt im ersten PR als unabhängige Plausibilitätskontrolle.

## 9.2 Späterer Routh-PR: sinnvoller MVP

Der spätere PR soll zunächst enthalten:

- Standardschema Grad 2 bis 4;
- exakte Zeilenerzeugung ohne Sonderfall;
- erste Spalte;
- Vorzeichenwechsel bei vollständig bestimmten Vorzeichen;
- Anzahl rechtsseitiger Pole;
- parameterfreie Stabilitätsprüfung;
- einparametrige Bedingungen, sofern keine Sonderfallteilung entsteht;
- Vergleich des Stabilitätsbereichs mit Hurwitz;
- GUI und LaTeX im bestehenden Stabilitätsarbeitsbereich.

## 9.3 Noch spätere Routh-Sonderfälle

Nicht im ersten Routh-MVP:

- isolierte Null in der ersten Spalte;
- Epsilon-Verfahren;
- vollständige Nullzeile;
- Hilfspolynom;
- wiederholte Sonderfallketten;
- symbolische RHP-Polzahl über komplexen Parameterregionen;
- allgemeine grenzstabile Klassifikation.

Die vollständige Nullzeile ist aus offiziellen Randfällen mathematisch relevant. Das Epsilon-Verfahren ist dagegen nicht als klar gelehrter Primärquelleninhalt belegt. Beide werden erst nach einem sauberen Standardschema entschieden.

## 9.4 Kein Platzhaltercode

Im ersten PR werden keine leeren `RouthTable`-Klassen, Feature-Flags oder unbenutzten Interfaces eingebaut. Wiederverwendung wird durch neutrale Kernobjekte erreicht, nicht durch spekulative APIs.

---

# 10. Architektur und Verträge

## 10.1 Exakter Eingang aus dem Polynomkern

Hurwitz erhält nicht `CharacteristicPolynomialInput` direkt, sondern:

```text
HurwitzAnalysisRequest
- canonical_polynomial_ref
- degree_case: PolynomialDegreeCase
- decision_parameters: [] | [p] | [p, q]
- fixed_symbols
- normalized_assumptions
- exclusions
- polynomial_role
- analysis_target
- provenance
- cancellation_report: optional/required by role
- requested_outputs
```

### Invarianten

- `degree_case.effective_degree` ist 1, 2, 3 oder 4.
- `effective_coefficients_desc` rekonstruiert exakt `effective_expr`.
- Leitkoeffizient ist unter dem Fallguard strikt positiv.
- alle freien Symbole sind deklariert;
- höchstens zwei Entscheidungsparameter;
- Rolle und Analyseziel sind kompatibel;
- bei reduziertem Nenner liegt ein gültiger Kürzungsbericht vor.

## 10.2 Validierung der Polynomrolle und des Analyseziels

Validierung erfolgt vor Matrixaufbau.

Harte Ablehnungen:

```text
ROLE_TARGET_MISMATCH
AMBIGUOUS_DENOMINATOR_ROLE
CANCELLATION_REPORT_REQUIRED
RAW_POLYNOMIAL_REQUIRED_FOR_INTERNAL_ANALYSIS
REDUCED_DENOMINATOR_REQUIRED_FOR_BIBO_ANALYSIS
UNSUPPORTED_DECISION_PARAMETER_COUNT
UNDECLARED_SYMBOL
NONPOSITIVE_LEADING_COEFFICIENT_CONTRACT_BROKEN
UNSUPPORTED_EFFECTIVE_DEGREE
```

## 10.3 `HurwitzMatrix`

```text
HurwitzMatrix
- matrix_id
- degree_case_id
- convention = SCRIPT_ODD_COEFFICIENT_FIRST
- degree
- coefficient_refs_by_power
- entries_exact[n][n]
- latex_matrix
- provenance
- diagnostics
```

Jeder Nichtnull-Eintrag referenziert den zugrunde liegenden Koeffizienten. Eingesetzte Nullen erhalten die Herkunft `OUT_OF_RANGE_COEFFICIENT_ZERO` oder `MISSING_POWER_ZERO`.

## 10.4 `HurwitzDeterminant`

```text
HurwitzDeterminant
- determinant_id
- matrix_id
- order k
- principal_submatrix_ref
- raw_determinant_expr
- expanded_expr
- factored_expr
- simplified_expr
- positivity_condition_id
- redundancy_status
- redundancy_reason
- provenance
- transformation_history
```

`raw_determinant_expr`, `expanded_expr` und `factored_expr` dürfen identisch sein. Es werden keine erfundenen Transformationsschritte ausgegeben.

## 10.5 Erzeugte atomare Stabilitätsbedingungen

```text
HurwitzConditionAtom
- condition_id
- degree_case_id
- condition_kind:
    LEADING_COEFFICIENT_POSITIVITY
    COEFFICIENT_POSITIVITY
    DETERMINANT_POSITIVITY
- source_coefficient_power: optional
- source_determinant_order: optional
- exact_relation: expr > 0
- strict = true
- solver_active
- redundancy_status
- provenance
```

Die Bedingungen werden anschließend als allgemeine `AtomicParameterCondition` an den Kern übergeben.

## 10.6 `ConditionRedundancyRecord`

```text
ConditionRedundancyRecord
- condition_id
- status:
    ACTIVE
    PROVED_TRUE_BY_ASSUMPTIONS
    REDUNDANT_GIVEN_OTHER_CONDITIONS
    CONTRADICTORY
- justification_refs
- exact_reason
```

Redundanzprüfung darf nur mit exakten logischen Beziehungen oder den expliziten Gradformeln erfolgen. Numerische Stichproben reichen nicht.

## 10.7 Übergabe an den Parameterkern

Pro Gradfall:

```text
ParameterConditionProblem
- variables: 0..2
- assumptions_formula
- exclusions_formula
- degree_guard_formula
- generated_formula = AND(minimal_solver_conditions)
- full_generated_formula = AND(full_generated_conditions)
- requested_result_kind
- completeness_required = true for official MVP cases
- source_case_id
- provenance
```

Kombination:

\[
\text{combined}
=
\text{assumptions}
\land
\text{exclusions}
\land
\text{degree guard}
\land
\text{minimal Hurwitz conditions}.
\]

## 10.8 Ergebnis für parameterfreie Fälle

```text
ZeroDimensionalConditionResult
- status: TRUE | FALSE | UNDECIDABLE | INVALID
- evaluated_atoms
- violated_atoms
- undecidable_atoms
- assumptions_used
- diagnostics
- provenance
```

Hurwitz übersetzt `TRUE` nur bei gültigem Analyseziel in eine Stabilitätsaussage.

## 10.9 Ergebnis für 1D-Parameterfälle

Verwendung des gemeinsamen `OneDimensionalRegionResult` mit:

- exakter Intervallvereinigung;
- offenen/geschlossenen Grenzen;
- Ausschlusspunkten;
- Fallguard;
- Kontrollpunkten;
- Restbedingungen;
- Vollständigkeitsstatus.

Hurwitz ergänzt die fachliche Bedeutung jeder aktiven Grenze.

## 10.10 Ergebnis für 2D-Parameterfälle

Erster verpflichtender Untertyp:

```text
GraphBandRegionResult
- x_parameter
- y_parameter
- exact_x_domain
- lower_boundary: y = l(x)
- lower_included
- upper_boundary: y = u(x)
- upper_included
- nonempty_proof
- exact_formula
- excluded_boundaries
- interior_control_point
- numeric_plot_geometry
- completeness_status
- diagnostics
- provenance
```

Der allgemeinere `TwoDimensionalRegionResult` kann dieses Objekt kapseln. Im ersten PR muss er nicht beliebige Zellkomplexität unterstützen.

## 10.11 `HurwitzDegreeCaseResult`

```text
HurwitzDegreeCaseResult
- case_id
- degree_case
- validation_status
- coefficient_conditions
- hurwitz_matrix
- determinants
- full_conditions
- minimal_conditions
- redundancy_records
- parameter_problem_ref
- parameter_region_result
- stability_statement
- boundary_classifications
- numerical_pole_checks
- diagnostics
- worked_steps
- latex_fragments
```

## 10.12 `HurwitzAnalysisResult`

```text
HurwitzAnalysisResult
- analysis_id
- input_summary
- polynomial_role
- analysis_target
- nominal_degree
- case_results
- combined_stable_region
- combined_region_completeness
- raw_vs_reduced_notice
- overall_statement
- diagnostics
- worked_steps
- latex_document_model
```

Die kombinierte Region darf nur Zweige vereinigen, deren Stabilitätsziel identisch ist. Interne und externe Ergebnisse werden niemals vereinigt.

## 10.13 Diagnosen

Siehe Abschnitt 13.

## 10.14 Worked Steps

Worked Steps sind strukturierte Daten, keine fertigen Fließtexte.

Zulässige Schrittarten:

```text
INPUT_POLYNOMIAL
ROLE_AND_TARGET_VALIDATION
DEGREE_CASE_SELECTION
COEFFICIENT_MAPPING
NECESSARY_CONDITIONS
HURWITZ_MATRIX
PRINCIPAL_MINOR
DETERMINANT_SIMPLIFICATION
FULL_CONDITION_SYSTEM
REDUNDANCY_REDUCTION
PARAMETER_PROBLEM
PARAMETER_REGION
BOUNDARY_EXCLUSION
NUMERICAL_POLE_CHECK
FINAL_STABILITY_STATEMENT
```

## 10.15 LaTeX-Ausgabe

Der Renderer konsumiert ausschließlich Ergebnis- und Worked-Step-Objekte. Er berechnet keine Determinanten oder Parameterbereiche neu.

## 10.16 Minimale GUI-Anbindung

Siehe Abschnitt 14.

## 10.17 Spätere Übergabe an andere Workflows

Das Hurwitz-Ergebnis darf weitergegeben werden an:

- Parametergebietsplot;
- Reglerparameter-Workflow;
- Vergleichsansicht Hurwitz/Routh;
- Berichtsexport;
- späteren Stabilitätsentscheidungs-Orchestrator.

Übergabeobjekt:

```text
StabilityRegionSummary
- method = HURWITZ
- analysis_target
- polynomial_role
- exact_region
- active_boundaries
- excluded_boundaries
- completeness_status
- source_analysis_id
- diagnostics
```

Es werden keine Regler- oder Streckenobjekte rückwärts rekonstruiert.

---

# 11. Algorithmen

## 11.1 Gesamtalgorithmus

1. `CharacteristicPolynomialInput` upstream erzeugen.
2. Gemeinsamen Kern kanonisieren lassen.
3. Vollständige `PolynomialDegreeCase`-Liste erhalten.
4. Für jeden zulässigen Fall Rolle, Ziel, Grad und positiven Leitkoeffizienten validieren.
5. Koeffizienten nach Potenzen referenzieren.
6. notwendige Koeffizientenbedingungen erzeugen.
7. Hurwitz-Matrix nach Skriptkonvention aufbauen.
8. führende Hauptminoren exakt berechnen.
9. Determinanten expandieren und faktorisieren.
10. vollständige strikte Bedingungen erzeugen.
11. gradabhängig redundante Bedingungen kennzeichnen.
12. minimales Solver-System bilden.
13. `ParameterConditionProblem` an gemeinsamen Kern übergeben.
14. parameterfreie, 1D- oder 2D-Lösung empfangen.
15. leere, partielle und vollständige Regionen unterscheiden.
16. aktive Gleichheitsränder fachlich als ausgeschlossen markieren.
17. geeignete exakte Innenpunkte numerisch durch Polberechnung kontrollieren.
18. Ergebnis über alle Gradfälle vereinigen, ohne Fallprovenienz zu verlieren.
19. Worked Steps und LaTeX-Modell erzeugen.
20. GUI-Ergebnis darstellen.

## 11.2 Koeffizientenextraktion

Die eigentliche Extraktion gehört dem Polynomkern.

Hurwitz führt nur aus:

```text
assert reconstruct(effective_coefficients_desc) == effective_expr
map descending list to a_power indices
```

Bei Abweichung erfolgt `POLYNOMIAL_CONTRACT_INCONSISTENT`. Es gibt keine zweite heuristische Extraktion.

## 11.3 Sichere Normierung

Die Normierung gehört ebenfalls dem Polynomkern.

Hurwitz prüft:

- Leitkoeffizient unter dem Fallguard nachweislich positiv;
- Scaling-Faktor nachweislich ungleich null;
- Gradfall dokumentiert;
- keine nicht dokumentierte parameterabhängige Division.

Hurwitz selbst multipliziert oder dividiert das Polynom nicht mehr.

## 11.4 Matrixaufbau

Für Zeilen- und Spaltenindex `r,c` ab null:

- Zeile 0 enthält `a_(1+2c)`;
- Zeile 1 enthält `a_(0+2c)`;
- jede weitere Zeile ist die zwei Zeilen darüber liegende Koeffizientenfolge um eine Spalte nach rechts verschoben;
- Koeffizienten außerhalb `0..n` sind null.

Eine direkte, gradfeste Konstruktion für 1 bis 4 ist zulässig und wirtschaftlich sinnvoller als eine allgemeine symbolische Matrixbibliothek. Die resultierenden Matrizen müssen trotzdem mit der allgemeinen Skriptdefinition übereinstimmen.

## 11.5 Hauptminorberechnung

Für `k=1..n`:

1. führende `k x k`-Untermatrix referenzieren;
2. Determinante exakt berechnen;
3. expandierte Form erzeugen;
4. faktorisierte Form erzeugen;
5. gegen gradbekannte Identitäten prüfen:
   - Grad 3: `Delta_3 = a_3 Delta_2`;
   - Grad 4: `Delta_4 = a_4 Delta_3`;
6. positivity atom `Delta_k>0` erzeugen.

Eine Identitätsverletzung ist ein interner Fehler und kein Nutzerproblem.

## 11.6 Vereinfachung ohne Verlust von Nennerausschlüssen

Hurwitz-Determinanten aus polynomialen Koeffizienten sind zunächst polynomial. Rationale Ausdrücke können durch upstream Skalierungen oder symbolische Koeffizienten entstehen.

Regeln:

1. Nenner nie stillschweigend verwerfen.
2. Einen nachweislich positiven Nenner nur mit dokumentiertem Vorzeichen entfernen.
3. Bei unbekanntem Nennerzeichen an Parameterkern zur Fallzerlegung übergeben.
4. Nennernullen als `EXCLUSION` erhalten.
5. Eine faktorisierte Form ist Darstellungs- und Solverhilfe, kein Ersatz für die ursprüngliche Bedingung.

## 11.7 Erzeugung strikter Bedingungen

Für asymptotische und BIBO-Stabilität:

```text
coefficient > 0
determinant > 0
```

Keine Toleranz, kein `>=0`, keine automatische Randinklusion.

## 11.8 Redundanzreduktion

Zulässige feste Regeln:

- Grad 1: `Delta_1=a_1` ist durch positiven Leitkoeffizienten erfüllt.
- Grad 2: `Delta_1=a_1`, `Delta_2=a_1a_2`; bei `a_2>0` genügt `a_1>0` plus `a_0>0`.
- Grad 3: `Delta_1=a_1`, `Delta_3=a_3Delta_2`; bei positiven Koeffizienten bleibt `Delta_2>0` aktiv.
- Grad 4: `Delta_1=a_1`, `Delta_4=a_4Delta_3`; bei positiven Koeffizienten bleiben `Delta_2>0` und `Delta_3>0` aktiv.

Weitere Redundanz darf der Parameterkern exakt erkennen. Hurwitz erfindet keine heuristischen Dominanzregeln.

## 11.9 Übergabe an den gemeinsamen Kern

- 0 Parameter -> `BOOLEAN`;
- 1 Parameter -> `ONE_DIMENSIONAL`;
- 2 Parameter -> `TWO_DIMENSIONAL`;
- mehr Parameter -> harte Ablehnung.

Offizielle Referenzfälle verlangen `completeness_required=true`.

## 11.10 Behandlung von Gradabfällen

- jeder Gradfall erhält ein eigenes Hurwitz-Ergebnis;
- Guard-Bedingung wird Teil des Parameterproblems;
- niedrigere Grade 1 bis 4 werden analysiert;
- Grad 0 und Nullpolynom bleiben separat;
- stabile Gradabfallpunkte dürfen in die kombinierte Region aufgenommen werden;
- Darstellung muss den Gradwechsel sichtbar machen.

## 11.11 Abgrenzung der Stabilitätsbegriffe

Vor der finalen Aussage:

1. Rolle/Ziel erneut prüfen;
2. bei reduziertem Nenner Kürzungswarnung anzeigen;
3. bei vorhandener Rohform optional parallele interne Analyse anbieten, aber nicht automatisch vermischen;
4. Endtext explizit mit `Zustands-`, `interne` oder `E/A-Stabilität` beschriften.

## 11.12 Numerische Gegenkontrolle

Nur Kontrolle, kein Beweis.

Für jeden vollständig gelösten nichtleeren Gradfall:

- mindestens einen exakten Innenpunkt wählen;
- Parameter einsetzen;
- Pole numerisch mit vorhandener Polfunktion bestimmen;
- `max(Re(p_i))< -tol` kontrollieren;
- Ergebnis als `CONSISTENT`, `INCONSISTENT` oder `NUMERICALLY_INCONCLUSIVE` speichern.

Zusätzlich sinnvoll:

- ein Punkt außerhalb des stabilen Gebiets;
- ein Punkt auf einer aktiven Grenze mit `Re(p)≈0` oder Gradwechsel.

Bei Widerspruch hat das symbolische Ergebnis nicht automatisch Vorrang. Es wird ein schwerer interner Diagnosefehler ausgegeben und kein vertrauenswürdiges Endergebnis behauptet.

## 11.13 Routh-Zeilenerzeugung

Nicht Bestandteil dieses PRs.

## 11.14 Konsistenzprüfung Hurwitz/Routh

Nicht Bestandteil dieses PRs. Sie wird im späteren Routh-PR eingeführt.

---

# 12. Stabilitäts- und Gradfallstruktur

| Fall | Behandlung | Endstatus |
|---|---|---|
| Grad 4, Leitkoeffizient positiv | vollständiges Hurwitz | solved/partial/empty |
| Grad 3, Leitkoeffizient positiv | vollständiges Hurwitz | solved/partial/empty |
| Grad 2, Leitkoeffizient positiv | vollständiges Hurwitz | solved/partial/empty |
| Grad 1 nach Gradabfall | direkter Hurwitz-Fallback | solved/partial/empty |
| Grad 0, konstantes Nichtnullpolynom | keine Hurwitz-Aussage | degenerate not applicable |
| Nullpolynom | ungültig | invalid |
| Leitkoeffizient negativ, Vorzeichen beweisbar | upstream Multiplikation mit `-1` | normaler Fall |
| Leitkoeffizient Vorzeichen unklar | Fallzerlegung im Kern | mehrere Fälle oder partial |
| innerer Koeffizient identisch null | notwendige Bedingung verletzt | empty/unstable |
| mehr als zwei Entscheidungsparameter | nicht unterstützt | unsupported |
| Grad >4 | nicht im MVP | unsupported |
| Rolle/Ziel unvereinbar | harte Ablehnung | invalid contract |
| reduzierter Nenner ohne Kürzungsbericht | harte Ablehnung | invalid contract |
| interne Analyse nur mit reduziertem Nenner | harte Ablehnung | invalid contract |
| 2D-Form außerhalb Graphband-Vertrag | sichere Restbedingungen | partial/unsupported |

---

# 13. Diagnosen

## 13.1 Schweregrade

```text
INFO
WARNING
ERROR
INTERNAL_ERROR
```

## 13.2 Vertragsdiagnosen

| Code | Schwere | Bedeutung |
|---|---|---|
| `CHARACTERISTIC_POLYNOMIAL_REQUIRED` | ERROR | DGL, offene Kette oder Transferobjekt statt Polynom übergeben |
| `ROLE_TARGET_MISMATCH` | ERROR | Polynomrolle und Analyseziel unvereinbar |
| `AMBIGUOUS_DENOMINATOR_ROLE` | ERROR | roh/reduziert nicht festgelegt |
| `CANCELLATION_REPORT_REQUIRED` | ERROR | reduzierter Nenner ohne Bericht |
| `RAW_POLYNOMIAL_REQUIRED_FOR_INTERNAL_ANALYSIS` | ERROR | interne Analyse mit reduziertem Nenner |
| `UNDECLARED_SYMBOL` | ERROR | freies Symbol nicht deklariert |
| `TOO_MANY_DECISION_PARAMETERS` | ERROR | mehr als zwei Entscheidungsparameter |
| `POLYNOMIAL_CONTRACT_INCONSISTENT` | INTERNAL_ERROR | Ausdruck und Koeffizienten widersprechen sich |
| `LEADING_COEFFICIENT_NOT_POSITIVE_IN_CASE` | INTERNAL_ERROR | Kerninvariante verletzt |

## 13.3 Fachdiagnosen

| Code | Schwere | Bedeutung |
|---|---|---|
| `DEGREE_DROP_ANALYZED_SEPARATELY` | INFO | Gradfall separat berechnet |
| `ZERO_POLYNOMIAL_INVALID` | ERROR | keine charakteristische Gleichung |
| `CONSTANT_POLYNOMIAL_NOT_HURWITZ_CASE` | WARNING | keine Hurwitz-Stabilitätsaussage |
| `COEFFICIENT_POSITIVITY_FAILED` | INFO/ERROR | notwendige Bedingung verletzt |
| `HURWITZ_DETERMINANT_FAILED` | INFO/ERROR | Hauptminor nicht positiv |
| `STABLE_REGION_EMPTY` | INFO | keine zulässige Einstellung |
| `STABLE_REGION_PARTIAL` | WARNING | Restbedingungen ungelöst |
| `BOUNDARY_EXCLUDED_STRICT_STABILITY` | INFO | Gleichheitsrand nicht enthalten |
| `BOUNDARY_CLASSIFICATION_NOT_PROVED` | WARNING | nicht automatisch grenzstabil nennen |
| `RAW_REDUCED_STABILITY_DIFFERENCE_POSSIBLE` | WARNING | Kürzung kann interne Dynamik verdecken |
| `FIXED_SYMBOL_ASSUMPTIONS_INSUFFICIENT` | WARNING | exakte Entscheidung nicht möglich |
| `NUMERICAL_POLE_CHECK_INCONCLUSIVE` | WARNING | numerische Kontrolle nahe Grenze unsicher |
| `SYMBOLIC_NUMERIC_MISMATCH` | INTERNAL_ERROR | symbolisches und numerisches Ergebnis widersprechen sich |

## 13.4 Verhalten bei Fehlern

- Vertragsfehler stoppen den betroffenen Analysezweig.
- Ein einzelner ungültiger Gradfall darf andere disjunkte gültige Gradfälle nicht zerstören.
- `PARTIAL` wird sichtbar und niemals als vollständig gelöst dargestellt.
- Interne Fehler sperren die finale Vertrauensaussage.

---

# 14. GUI- und LaTeX-Integration

## 14.1 Minimale GUI

Bestehenden Arbeitsbereich `Stabilitätsanalyse` erweitern. Kein separater Werkzeugbereich.

### Eingaben

- Polynom oder Übernahme eines upstream `CharacteristicPolynomialInput`;
- Hauptvariable automatisch aus Vertrag;
- Entscheidungsparameter 0 bis 2;
- feste Symbole und Annahmen;
- Analyseziel;
- sichtbare Polynomrolle;
- Auswahl `Hurwitz`;
- optional numerische Polkontrolle ein/aus;
- optional 2D-Plotbereich nur für Darstellung.

### Pflichtanzeige vor Start

- kanonisches Polynom;
- nomineller Grad;
- erkannte Gradfälle;
- Rolle und Analyseziel;
- Roh-/reduziert-Status;
- Annahmen und Ausschlüsse;
- Warnung bei Kürzung.

### Ergebnisbereiche

1. Kurzurteil.
2. Gradfall-Tabs oder aufklappbare Fälle.
3. Koeffiziententabelle.
4. Hurwitz-Matrix.
5. Determinantentabelle.
6. vollständige Bedingungen.
7. minimales Bedingungssystem.
8. exaktes Intervall oder 2D-Gebiet.
9. ausgeschlossene Grenzen.
10. numerische Polkontrolle.
11. Diagnosen.
12. LaTeX-Vorschau/Export.

## 14.2 2D-Plot

Der Plot ist nachgelagert:

- exakte Randfunktionen aus Ergebnisobjekt;
- offene Ränder gestrichelt oder eindeutig markiert;
- numerische Schattierung nur als Darstellung;
- exakte Formel neben dem Plot;
- Viewport ändert niemals die mathematische Region.

## 14.3 Klausurtaugliche Kurzansicht

Beispiel:

```text
Charakteristisches Polynom:
p(s)=s^3+4s^2+5s+K_P

Notwendig:
K_P>0

Hurwitz:
Delta_2=20-K_P>0

Ergebnis:
0<K_P<20

Die Grenzen K_P=0 und K_P=20 sind für asymptotische Stabilität ausgeschlossen.
```

## 14.4 Vollständige LaTeX-Ausgabe

Reihenfolge:

1. Analyseziel und Polynomrolle.
2. Original- und kanonisches Polynom.
3. Gradfall und Normierungsprovenienz.
4. Koeffizientenzuordnung.
5. notwendige Bedingungen.
6. Hurwitz-Matrix.
7. jeder Hauptminor mit exakter Rechnung.
8. vollständiges Bedingungssystem.
9. Redundanzreduktion.
10. Parameterlösung.
11. offene Grenzen und Ausschlüsse.
12. optionale numerische Polkontrolle als Kontrolle.
13. finale Stabilitätsaussage.

LaTeX muss exakte und numerische Werte trennen. Es darf keine Routh-Tabelle zeigen, solange Routh nicht gerechnet wurde.

---

# 15. Referenzfälle

## 15.1 REF-H-PARAM-0 – parameterfreier kubischer Fall

**Quelle:** aus Übung 09 Aufgabe 3 mit `K_P=8` abgeleitet.

\[
p(s)=s^3+4s^2+5s+8.
\]

\[
\Delta_2=5\cdot4-8=12>0.
\]

Erwartung:

```text
parameter-free result = TRUE
asymptotically stable
all numerical poles have Re < 0
```

## 15.2 REF-H-1D-EX09 – offizieller Einparameterfall

**Quelle:** `Regelungstechnik_Übung_Aufg-u-Lösungen.pdf`, Übung 09 Aufgabe 3.

\[
p(s)=s^3+4s^2+5s+K_P.
\]

Bedingungen:

\[
K_P>0,
\qquad
20-K_P>0.
\]

Erwartung:

\[
\boxed{0<K_P<20.}
\]

Randwerte sind ausgeschlossen. Die offizielle Lösung verwendet teilweise nichtstrikte Zeichen; das fachlich korrekte asymptotische Ergebnis ist strikt.

## 15.3 REF-H-2D-SS25 – erster Klausurfall

**Quelle:** `RT_Klausur_SS2025-komplett.pdf`, Aufgabe 4b, Aufgabenbogen PDF-S. 9, Lösung PDF-S. 66.

\[
p(s)=s^3+(9+a)s^2+(20+9a)s+(20a+9K).
\]

Notwendige Bedingungen:

\[
a>-9,
\]

\[
a>-\frac{20}{9},
\]

\[
K>-\frac{20}{9}a.
\]

Dominante `a`-Bedingung:

\[
a>-\frac{20}{9}.
\]

Determinante:

\[
\Delta_2=(20+9a)(9+a)-(20a+9K).
\]

\[
\Delta_2>0
\iff
K<a^2+9a+20.
\]

Erwartung:

\[
\boxed{
a>-\frac{20}{9},
\qquad
-\frac{20}{9}a<K<a^2+9a+20
}.
\]

Beide K-Grenzen sind offen. Auf `a=-20/9` treffen Unter- und Obergrenze zusammen; der Rand ist ausgeschlossen.

## 15.4 REF-H-2D-WS25 – zweiter Klausurfall und Kürzungsvertrag

**Quelle:** `RT-Klausur_WS_25_26-komplett.pdf`, Aufgabe 4b, Aufgabenbogen PDF-S. 11, Lösung PDF-S. 69–70.

Gegeben:

\[
G_W(s)=
\frac{(s+K)^2}
{\left((s+3)(s+2a)(s+5)+8K\right)(s+K)}.
\]

Reduziert:

\[
G_W^{\mathrm{red}}(s)=
\frac{s+K}{(s+3)(s+2a)(s+5)+8K}.
\]

Reduziertes E/A-Nennerpolynom:

\[
p_{\mathrm{BIBO}}(s)
=s^3+(8+2a)s^2+(15+16a)s+(30a+8K).
\]

Bedingungen:

\[
a>-4,
\qquad
a>-\frac{15}{16},
\qquad
K>-\frac{15}{4}a,
\]

\[
\Delta_2>0
\iff
K<4a^2+16a+15.
\]

Erwartung für externe E/A-Stabilität:

\[
\boxed{
a>-\frac{15}{16},
\qquad
-\frac{15}{4}a<K<4a^2+16a+15
}.
\]

Rohes Nennerpolynom:

\[
p_{\mathrm{raw}}(s)=p_{\mathrm{BIBO}}(s)(s+K).
\]

Für interne asymptotische Stabilität ist zusätzlich erforderlich:

\[
K>0.
\]

Pflichttest:

- externe und interne Region dürfen nicht stillschweigend gleichgesetzt werden;
- der Kürzungsbericht enthält den entfernten Faktor `s+K`;
- das Analyseziel entscheidet, welches Polynom primär geprüft wird.

## 15.5 REF-H-4D-TUT09 – offizieller quartischer Fall

**Quelle:** `Regelungstechnik_Tutorium_komplett.pdf`, Tutorium 09 Aufgabe 3d, PDF-S. 57–58.

\[
p(s)=T_1^3T_Is^4+3T_1^2T_Is^3+3T_1T_Is^2+T_Is+4,
\]

\[
T_1>0,
\qquad T_I>0.
\]

Determinanten:

\[
\Delta_2=3T_1T_I(T_I-4T_1),
\]

\[
\Delta_3=4T_1^3T_I^2(2T_I-9T_1).
\]

Erwartung:

\[
\boxed{T_I>\frac92T_1.}
\]

Die schwächere Bedingung `T_I>4T_1` wird durch `T_I>9T_1/2` redundant.

## 15.6 REF-H-GRAD-DROP – synthetischer Vertragsfall

\[
p(s;q)=qs^3+s^2+2s+1,
\qquad q\ge0.
\]

Erwartung:

- `q>0`: Grad 3, stabil für `q<2`;
- `q=0`: Grad 2, stabil;
- Gesamtergebnis `0<=q<2`;
- `q=0` mit eigenem Gradfall und nicht als bloßer Ausschlusspunkt.

## 15.7 REF-H-EMPTY – synthetischer leerer Bereich

\[
p(s;K)=s^3+s^2+s+(K+2),
\qquad K>0.
\]

Hurwitz:

\[
a_0=K+2>0,
\]

\[
\Delta_2=1-(K+2)=-(K+1)>0
\iff K<-1.
\]

Mit `K>0`:

\[
\boxed{\varnothing}.
\]

Erwartung: `STABLE_REGION_EMPTY`, keine Testpunkte im stabilen Gebiet.

## 15.8 REF-H-RAW-REDUCED – Rollenregression

Verwendet denselben WS25/26-Fall.

Prüft getrennt:

1. `REDUCED_TRANSFER_DENOMINATOR + EXTERNAL_BIBO`;
2. `RAW_CLOSED_LOOP_CHARACTERISTIC + INTERNAL_CLOSED_LOOP_ASYMPTOTIC`;
3. Fehlermeldung bei vertauschten Rollen/Zielen;
4. sichtbare Differenz der Parameterregionen durch die Zusatzbedingung `K>0`.

## 15.9 Routh-Vergleichsfall

Nicht im ersten PR, da Routh nicht aufgenommen wird. Im späteren Routh-PR wird `REF-H-1D-EX09` als erster Vergleichsfall verwendet.

---

# 16. Gezielte Tests

## 16.1 Hurwitz-Domain-Tests

| ID | Inhalt | Erwartung |
|---|---|---|
| `HD-01` | Grad-2-Matrix | korrekte Matrix und `Delta_2=a_1a_2` |
| `HD-02` | Grad-3-Matrix | `Delta_2=a_1a_2-a_0a_3`, `Delta_3=a_3Delta_2` |
| `HD-03` | Grad-4-Matrix | korrekte `Delta_3`, `Delta_4=a_4Delta_3` |
| `HD-04` | positive Skalierung | identischer Stabilitätsbereich |
| `HD-05` | negative Skalierung upstream normiert | identischer Stabilitätsbereich |
| `HD-06` | fehlende Potenz | Nullkoeffizient führt zu korrekter Instabilitätsbedingung |
| `HD-07` | parameterfreier stabiler Fall | `TRUE` |
| `HD-08` | parameterfreier instabiler Fall | `FALSE` mit verletzter Bedingung |
| `HD-09` | Grad-1-Fallback | korrekte Bedingung `a_0>0` |
| `HD-10` | Grad 0 | keine falsche Stabilitätsaussage |
| `HD-11` | Nullpolynom | invalid |
| `HD-12` | strikte Grenzen | Gleichheit nicht enthalten |

## 16.2 Parameterkern-Integrationstests

| ID | Fall | Erwartung |
|---|---|---|
| `PKI-00` | 0D-Bedingungen | `ZeroDimensionalConditionResult` |
| `PKI-01` | Übung 09 | `0<K_P<20` |
| `PKI-02` | SS2025 | exaktes Graphband |
| `PKI-03` | WS25/26 | exaktes Graphband |
| `PKI-04` | quartischer Tutoriumsfall | `T_I>9T_1/2` |
| `PKI-05` | Gradabfall | Vereinigung `q=0` und `0<q<2` zu `0<=q<2`, Provenienz erhalten |
| `PKI-06` | leerer Bereich | leere Menge |
| `PKI-07` | unzureichende feste Symbolannahmen | undecidable/partial, nicht scheinbar exact |
| `PKI-08` | 2D außerhalb Graphband-Vertrag | sichtbare Restbedingungen |
| `PKI-09` | Nennerausschluss | Ausschluss bleibt erhalten |

## 16.3 Rollen- und Stabilitätszieltests

| ID | Fall | Erwartung |
|---|---|---|
| `RST-01` | WS reduziert + BIBO | akzeptiert |
| `RST-02` | WS roh + intern | akzeptiert, Zusatzfaktor berücksichtigt |
| `RST-03` | WS reduziert + intern | Ablehnung |
| `RST-04` | WS roh + BIBO als einziges Objekt | Ablehnung oder explizite Auswahl des reduzierten Nenners erforderlich |
| `RST-05` | State polynomial + BIBO | Ablehnung |
| `RST-06` | reduzierter Nenner ohne Kürzungsbericht | Ablehnung |

## 16.4 Routh-Tests

Keine Routh-Tests im ersten PR.

Für den späteren Routh-PR vorzumerken:

- Standardschema Übung 09;
- Vorzeichenwechsel bei `K_P>20`;
- Hurwitz/Routh-Bereichsgleichheit;
- Sonderfälle getrennt und nicht im ersten Routh-MVP.

## 16.5 Presenter-/LaTeX-Smoke-Tests

Zwingend nur drei:

1. Einparameterfall `0<K_P<20`.
2. SS2025-Graphband.
3. WS25/26-Roh-/Reduziert-Warnung.

Optional:

4. Gradabfall mit zwei Fallzweigen.

Zu prüfen:

- Matrix korrekt;
- Determinanten exakt;
- vollständige und minimale Bedingungen getrennt;
- offene Grenzen korrekt;
- Stabilitätsbegriff genannt;
- numerische Pole als Kontrolle beschriftet;
- keine erfundenen Routh-Schritte.

## 16.6 Nicht notwendige Volltests

Im ersten PR ausdrücklich nicht erforderlich:

- allgemeine Grade >4;
- zufällige Polynomfuzzing-Suite mit tausenden Fällen;
- allgemeine semialgebraische 2D-Zellzerlegung;
- Tests interner SymPy-Determinantenalgorithmen;
- Routh-Sonderfälle;
- mehrere nahezu identische GUI-End-to-End-Fälle;
- allgemeine interne Stabilitätsrekonstruktion aus Regler und Strecke;
- DGL-/Laplace-/Regelkreis-End-to-End-Tests im Hurwitz-PR;
- dreidimensionale Parametergebiete;
- numerische Rasterung als mathematischer Regressionstest.

---

# 17. Codex-Aufwand

## 17.1 Aufwandstreiber des empfohlenen PRs

| Bestandteil | Aufwand | Risiko |
|---|---:|---|
| Einpassung in vorhandene Polynomtypen | mittel | Doppeltypen |
| 0D-Ergebnisvertrag | niedrig | bisherige Vertragslücke |
| Gradfalllogik | mittel | Randzweige verlieren |
| Hurwitz-Matrix Grad 1–4 | niedrig | Indexkonvention |
| Determinanten und Provenienz | mittel | falsche Vereinfachung |
| vollständige/minimale Bedingungen | mittel | Herkunft verlieren |
| exakter 1D-Solver | mittel | Nennerzeichen/Ausschlüsse |
| enges 2D-Graphband | mittel | Domäne und Randordnung |
| Roh-/Reduziert-Validierung | mittel | Stabilitätsbegriffe vermischen |
| Worked Steps/LaTeX | mittel | behauptete statt echte Schritte |
| minimale GUI | mittel | parallele Oberfläche |
| offizielle Referenztests | mittel | Quellenrandfehler |

Gesamt:

\[
\boxed{\text{mittel bis hoch}}
\]

## 17.2 Einsparungen gegenüber Variante B

- keine zweite Repository-Inventur;
- keine zweite Vertragsrunde;
- keine doppelte Testeinrichtung;
- keine Backend-only-Abnahme;
- keine spätere Reparatur des parameterfreien Ergebnistyps;
- keine doppelte GUI-/Presenter-Anbindung.

## 17.3 Mehrkosten von Variante C

Zusätzlich erforderlich wären:

- Routh-Tabellenobjekte;
- Zeilenalgorithmus;
- Definitionsbedingungen bei Divisionen;
- Vorzeichenwechselzählung;
- eigener Presenter;
- GUI-Unteransicht;
- Cross-Tests;
- Sonderfallabgrenzung.

Diese Mehrkosten bringen vor der Klausur weniger Nutzen als die Stabilisierung von Hurwitz und den zweiparametrigen Gebieten.

## 17.4 Schätzung in relativen Codex-Paketen

Keine Tokenzahl wird erfunden. Relative Planung:

```text
Repository-/Vertragseinpassung: 1 Paket
Kern 0D/1D/enges 2D + Gradfälle: 2 Pakete
Hurwitz-Domain + Integration: 1 Paket
GUI/LaTeX/Tests/Korrekturen: 1 Paket
```

Routh würde voraussichtlich mindestens ein weiteres eigenständiges Paket plus Korrekturschleife benötigen.

---

# 18. Risiken und Gegenmaßnahmen

## 18.1 Allgemeiner CAS schleicht sich ein

**Risiko:** 2D-Anforderungen wachsen zu allgemeiner Quantorenelimination.

**Gegenmaßnahme:** erster 2D-Vertrag nur exakte Graphbänder; alles andere partial/unsupported.

## 18.2 Hurwitz dupliziert Polynomkanonisierung

**Risiko:** Fachmodul expandiert und normiert erneut.

**Gegenmaßnahme:** Hurwitz konsumiert nur `PolynomialDegreeCase`; Rekonstruktionsassertion statt zweiter Kanonisierung.

## 18.3 Monische Normierung erzeugt rationale Explosion

**Risiko:** Division durch parameterabhängigen Leitkoeffizienten erzeugt Nennerfälle.

**Gegenmaßnahme:** nur sichere Vorzeichennormierung, monische Form standardmäßig aus.

## 18.4 Parameterfreier Vertrag bleibt undefiniert

**Risiko:** Boolean-Ergebnis wird ad hoc im Hurwitz-Modul gelöst.

**Gegenmaßnahme:** `BOOLEAN` und `ZeroDimensionalConditionResult` verbindlich im gemeinsamen Kern.

## 18.5 Rohes und reduziertes Polynom werden verwechselt

**Risiko:** WS25/26 liefert falsche interne Stabilitätsaussage.

**Gegenmaßnahme:** harte Rollen-/Zielmatrix und Kürzungsbericht.

## 18.6 Strikte Grenzen werden eingeschlossen

**Risiko:** offizielle Musterlösungen mit `<=` werden unkritisch übernommen.

**Gegenmaßnahme:** Hurwitz erzeugt ausschließlich `>0`; Presenter übernimmt Striktheit aus Atomen.

## 18.7 Gradabfall wird als Ausschluss behandelt

**Risiko:** stabile niedrigere Gradfälle gehen verloren.

**Gegenmaßnahme:** disjunkte `PolynomialDegreeCase` und getrennte Hurwitz-Ergebnisse.

## 18.8 Bedingungsreduktion zerstört Rechenweg

**Risiko:** Endsystem ist korrekt, aber Punkte bringende Bedingungen fehlen im Bericht.

**Gegenmaßnahme:** `full_conditions`, `minimal_conditions` und Redundanzrecords getrennt.

## 18.9 Numerische Kontrolle wird als Beweis dargestellt

**Risiko:** Raster oder Testpunkt ersetzt exakte Lösung.

**Gegenmaßnahme:** numerische Ergebnisse nur im Abschnitt „Kontrolle“; Vollständigkeitsstatus bleibt symbolisch bestimmt.

## 18.10 Routh wird heimlich mitimplementiert

**Risiko:** Scope wächst über Tabellen- und Sonderfälle.

**Gegenmaßnahme:** kein Routh-Objekt, keine Routh-GUI, keine Routh-Tests im ersten PR.

## 18.11 Quellenfehler werden als Regressionserwartung übernommen

**Risiko:** `K_P=20`, `K_R=23` oder andere Gleichheitsgrenzen werden stabil genannt.

**Gegenmaßnahme:** Skriptkonvention und direkte Polkontrolle haben Vorrang; Quellenabweichung dokumentieren.

## 18.12 Ausdruck und Koeffizienten divergieren

**Risiko:** Matrix basiert auf anderem Polynom als Anzeige.

**Gegenmaßnahme:** exakte Rekonstruktionsinvariante vor Hurwitz.

---

# 19. Empfohlene Implementierungsreihenfolge

Die Schritte liegen innerhalb eines vertikalen PRs. Sie sind keine separaten langfristigen Infrastrukturbranches.

## Schritt 1 – Repository-Einpassung

- vorhandene Polynom-, Diagnose-, Worked-Step- und LaTeX-Typen inventarisieren;
- neue Verträge auf bestehende Typen abbilden;
- keine parallelen Symbolikobjekte erzeugen;
- GUI-Einstiegspunkt festlegen.

## Schritt 2 – Kernvertragslücken schließen

- `variables=[]` zulassen;
- `BOOLEAN`-Ergebnisart;
- `ZeroDimensionalConditionResult`;
- Rollenmenge schärfen;
- Kürzungsbericht rollenspezifisch validieren;
- `GraphBandRegionResult` festlegen.

Abnahme: reine Vertragstests, noch kein eigener Backend-PR.

## Schritt 3 – Polynomkanonisierung und Gradfälle

- vorhandene Kernplanung umsetzen;
- Vorzeichen- und Gradfallzerlegung;
- keine monische Standardnormierung;
- Rekonstruktionsinvarianten.

Abnahme: Gradabfalltest und Rollenvalidierung.

## Schritt 4 – 0D- und 1D-Bedingungsauswertung

- geschlossene Boolesche Bedingungsauswertung;
- exakte Intervallvereinigungen;
- Ausschlusspunkte;
- leere Menge.

Abnahme: parameterfreier Fall, Übung 09, leerer Bereich.

## Schritt 5 – enges 2D-Graphband

- SS2025 und WS25/26 als exakte Bänder;
- Domänen- und Nichtleerheitsnachweis;
- offene Grenzen;
- numerische Plotprojektion getrennt.

Abnahme: beide Klausurfälle.

## Schritt 6 – Hurwitz-Domain Grad 1–4

- Koeffizientenmapping;
- Matrix;
- Hauptminoren;
- Determinantenidentitäten;
- Bedingungen;
- Redundanzrecords.

Abnahme: kleine Domain-Tests.

## Schritt 7 – Hurwitz/Kern-Integration

- `ParameterConditionProblem` pro Gradfall;
- parameterfreie, 1D- und 2D-Ergebnisse;
- Fallvereinigung;
- Roh-/Reduziert-Workflow;
- numerische Polkontrolle.

Abnahme: alle Referenzfälle.

## Schritt 8 – GUI, Worked Steps und LaTeX

- bestehender Stabilitätsarbeitsbereich;
- keine zweite Oberfläche;
- Kurz- und Vollansicht;
- 2D-Plot;
- Diagnoseanzeige;
- LaTeX.

## Schritt 9 – gezielte Regression

- Hurwitz-Domain;
- Kernintegration;
- Rollen/Ziele;
- drei Presenter-Smoke-Tests;
- vollständiger Testsatz einmal nach finalen Änderungen.

## Schritt 10 – Merge und Nutzerprüfung

Manuell prüfen:

1. Übung 09;
2. SS2025;
3. WS25/26 extern und intern;
4. quartischer Tutoriumsfall;
5. Gradabfall;
6. leeres Gebiet.

Erst danach Routh-PR planen.

---

# 20. Paketabnahme

Der erste PR ist abgeschlossen, wenn:

1. Hurwitz über die bestehende GUI erreichbar ist.
2. Der gemeinsame Kern keine Hurwitz-Bedingungen erzeugt.
3. Hurwitz keine Polynomkanonisierung dupliziert.
4. parameterfreie Fälle einen strukturierten 0D-Kernstatus besitzen.
5. Grade 2 bis 4 vollständig unterstützt werden.
6. Grad 1 als Gradabfall-Fallback funktioniert.
7. Gradabfälle nicht pauschal ausgeschlossen werden.
8. alle Matrizen der Skriptkonvention entsprechen.
9. `Delta_4=a_4 Delta_3` korrekt ist.
10. vollständige und minimale Bedingungen getrennt vorliegen.
11. alle Hurwitz-Grenzen strikt offen bleiben.
12. Übung 09 exakt `0<K_P<20` liefert.
13. SS2025 exakt das korrekte Parabelband liefert.
14. WS25/26 externes und internes Ergebnis getrennt behandelt.
15. der quartische Fall `T_I>9T_1/2` liefert.
16. ein leerer Bereich explizit als leer ausgegeben wird.
17. numerische Polwerte nur als Kontrolle erscheinen.
18. partielle 2D-Fälle sichtbar unvollständig bleiben.
19. Worked Steps den tatsächlich ausgeführten Rechenweg zeigen.
20. LaTeX keine erfundenen Schritte enthält.
21. keine DGL-, Laplace-, Regelkreis- oder Transferfunktionslogik dupliziert wurde.
22. kein Routh-Code im ersten PR enthalten ist.
23. keine allgemeine CAS-Abstraktion über den belegten Bedarf hinaus entstanden ist.

---

# 21. Spätere Erweiterungen

## 21.1 Routh-PR

- Standardschema Grad 2 bis 4;
- erste Spalte;
- Vorzeichenwechsel;
- RHP-Polzahl;
- parameterfreie und einfache einparametrige Fälle;
- Hurwitz-Gegenprüfung;
- GUI und LaTeX.

## 21.2 Routh-Sonderfall-PR nur bei Bedarf

- vollständige Nullzeile;
- Hilfspolynom;
- isolierte Null erster Spalte;
- Epsilon-Verfahren;
- wiederholte Sonderfälle;
- Grenzpolklassifikation.

## 21.3 Erweiterter Parameterkern nur durch realen Verbraucher

- mehrere disjunkte 2D-Bänder;
- rationale Graphgrenzen mit bewiesenem Nennerzeichen;
- allgemeine implizite Randkurven;
- mehr Fallzweige;
- zusätzliche Verbraucher wie Nyquist oder Wurzelortskurve.

Keiner dieser Punkte wird vorsorglich im Hurwitz-PR implementiert.

---

# 22. Schlussfolgerung

Das wirtschaftlich richtige Paket ist ein **vertikaler Hurwitz-PR mit dem kleinsten tatsächlich benötigten gemeinsamen Polynom-/Parameterkern**. Routh wird bewusst getrennt nachgelagert.

Der kritische technische Schwerpunkt liegt nicht in der Determinantenberechnung. Er liegt in:

- sauberer Rollen-/Zieltrennung;
- Gradfällen;
- strikten Grenzen;
- parameterfreien sowie 1D-/2D-Ergebnisverträgen;
- Erhaltung von Provenienz;
- Roh-/Reduziert-Unterscheidung;
- sichtbarer klausurtauglicher Ausgabe.

\[
\boxed{
\text{kleiner gemeinsamer Kern}
+
\text{Hurwitz Grad 2–4}
+
\text{exakte Parameterbereiche}
}
\]

\[
\boxed{
\text{Routh danach, nicht gleichzeitig}
}
\]
