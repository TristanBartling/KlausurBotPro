# KlausurBotPro – Implementierungspaket Polynom- und Parameterkern

**Datei:** `KlausurBotPro_Implementierungspaket_Polynom_Parameterkern.md`  
**Status:** implementierungsfertige, codefreie Fach- und Schnittstellenspezifikation  
**Erster vorgesehener Verbraucher:** Hurwitz  
**Nicht enthalten:** Softwareimplementierung, Codex-Prompt, allgemeines CAS, Erzeugung von Hurwitz-Bedingungen

## Maßgebliche Referenzen

1. `docs/KlausurBotPro_Architekturplan.md`
   - insbesondere Architekturprinzipien, symbolische Stabilitätssäule, gemeinsame Domänenobjekte, Paket 4, Test- und LaTeX-Strategie.
2. `docs/reference/KlausurBotPro_Fachspezifikation_Charakteristische_Polynome_Parameterbedingungen.md`
   - insbesondere Modulgrenze, Polynomvertrag, Parameterbedingungen, exakte 1D-Mengen, begrenzte 2D-Mengen, Diagnosen und MVP-Abgrenzung.
3. `docs/reference/KlausurBotPro_Fachspezifikation_Hurwitz_Routh.md`
   - insbesondere Vorstufenabgrenzung, Übergabevertrag, klausurrelevante Grade und Parametergebiete sowie Schnittstelle zwischen Hurwitz und gemeinsamem Kern.

Die vorhandene Fachspezifikation bleibt fachlich verbindlich. Dieses Dokument präzisiert den wirtschaftlich kleinsten ersten Implementierungszuschnitt und die dafür benötigten Verträge. Es ersetzt keine fachliche Quellenanalyse.

---

# 1. Ausgangspunkt

## 1.1 Vorhandener technischer Stand

Die Frequenzsäule besitzt bereits:

- rationale Übertragungsfunktionen,
- sichere Eingabe und exakte Reduktion,
- rohe und reduzierte Übertragungsfunktion,
- Kürzungsprotokolle,
- Pole und Nullstellen,
- numerischen Frequenzgang,
- Bode-Workflow,
- Standardglieder-MVP,
- Diagnosen,
- Worked Steps,
- LaTeX-Infrastruktur.

Nicht vorhanden ist ein gemeinsamer symbolischer Fachkern für:

- charakteristische Polynome,
- parameterabhängige Gradfälle,
- exakt repräsentierte Gleichungen und Ungleichungen,
- einparametrige Lösungsmengen,
- begrenzte zweiparametrige Gebiete.

## 1.2 Fachlicher Datenfluss

Verbindlich bleibt:

```text
vorgelagerter Fachblock erzeugt charakteristisches Polynom
        ↓
gemeinsamer Polynomkern kanonisiert und erzeugt Gradfälle
        ↓
Fachmodul erzeugt fachliche Bedingungen
        ↓
gemeinsamer Parameterkern löst und repräsentiert das Mengenproblem
        ↓
Fachmodul interpretiert das Ergebnis
        ↓
Worked Steps / LaTeX / GUI
```

Für den ersten Verbraucher gilt konkret:

```text
CharacteristicPolynomialInput
        ↓
Polynomkanonisierung
        ↓
kanonische Gradfälle
        ↓
Hurwitz erzeugt Koeffizienten- und Determinantenbedingungen
        ↓
ParameterConditionProblem
        ↓
exakte 1D- oder begrenzte 2D-Lösung
        ↓
HurwitzResult mit fachlicher Stabilitätsaussage
```

## 1.3 Besitz der fachlichen Interpretation

| Verantwortung | Besitzer |
|---|---|
| Bildung von DGL, Übertragungsfunktion oder Regelkreis | vorgelagerter Fachblock |
| Entscheidung über rohes oder reduziertes Polynom | Orchestrierung beziehungsweise aufrufendes Fachmodul |
| algebraische Kanonisierung und Gradfälle | gemeinsamer Polynomkern |
| Erzeugung von Hurwitz-Determinanten | Hurwitz |
| Bedeutung einer Bedingung als Stabilitätsbedingung | Hurwitz |
| Lösung der bereits erzeugten Bedingungen | gemeinsamer Parameterkern |
| algebraische Randinklusion | gemeinsamer Parameterkern |
| Bezeichnung eines Randes als Stabilitätsgrenze | Hurwitz |
| Darstellung | Presenter/Worked-Steps-/LaTeX-Schicht |

Der gemeinsame Kern darf daher beispielsweise feststellen, dass eine Grenze ausgeschlossen ist. Er darf sie aber nicht selbst als „Hurwitz-Grenze“, „grenzstabil“ oder „instabil“ bezeichnen.

---

# 2. Verbindliche Modulgrenze

## 2.1 Öffentliche Fachoperationen

Der gemeinsame Kern benötigt im ersten Paket nur zwei öffentliche Operationen:

```text
canonicalize_characteristic_polynomial(input)
solve_parameter_conditions(problem)
```

Die endgültigen technischen Namen dürfen an die vorhandene Codebasis angepasst werden. Die fachliche Trennung ist verbindlich.

## 2.2 Der Kern übernimmt

### Polynomseite

- Validierung eines bereits erzeugten Polynoms.
- Rekonstruktion aus Ausdruck und Koeffizienten.
- Kanonisierung in der Hauptvariable.
- Erhaltung von Rolle, Analyseziel und Provenienz.
- Erhaltung von Annahmen, Ausschlussmengen und Kürzungsinformationen.
- Ermittlung des nominellen und effektiven Grades.
- wiederholte Gradreduktion.
- Erkennung von Nullpolynom und konstantem Nichtnullpolynom.
- sichere Skalierung.
- Fallzerlegung bei parameterabhängigem Leitkoeffizienten.
- strukturierte Transformationshistorie.

### Bedingungsseite

- atomare Gleichungen und Ungleichungen,
- strikte und nichtstrikte Relationen,
- Nennerausschlüsse,
- Schnitt und endliche Vereinigung,
- leere Menge,
- vollständig exakte einparametrige Mengen innerhalb des unterstützten Vertrags,
- begrenzte zweiparametrige Mengen für die belegten Hurwitz-Fälle,
- Randobjekte und Randinklusion,
- sichere Testpunkte und numerische Projektionen,
- vollständige, teilweise gelöste und nicht unterstützte Ergebnisse,
- kompakte Worked Steps und LaTeX-fähige Ergebnisobjekte.

## 2.3 Der Kern übernimmt nicht

- DGL- oder Laplace-Transformation,
- Bildung einer Übertragungsfunktion,
- Blockschaltbildreduktion,
- Bildung von \(1+L(s)=0\),
- Entscheidung über Rückkopplungsvorzeichen,
- Kürzung rationaler Übertragungsfunktionen,
- Erzeugung von Hurwitz-Matrix oder Hurwitz-Determinanten,
- Routh-Schema,
- Nyquist-Zählung,
- Wurzelortskurvenlogik,
- Übersetzung von Zeitforderungen in Parameterbedingungen,
- automatische Auswahl des Stabilitätsbegriffs,
- allgemeine Quantorenelimination,
- allgemeine mehrdimensionale semialgebraische Zerlegung,
- numerische Rasterung als Ersatz für eine exakte Menge.

## 2.4 Harte Eingabeablehnungen

Die Kernoperation zur Polynomkanonisierung akzeptiert nicht unmittelbar:

- DGL,
- Zustandsraummatrix ohne bereits gebildetes charakteristisches Polynom,
- offene Übertragungsfunktion,
- getrennte Regler- und Streckenobjekte,
- Blockschaltbild,
- offenen Kreis \(L(s)\),
- unklare rationale Funktion ohne festgelegtes Analyseziel,
- mehr als zwei freie Entscheidungsparameter,
- nicht deklarierte Symbole,
- widersprüchliche Ausdrucks- und Koeffizientendarstellung.

Der übergeordnete Workflow darf solche Eingaben annehmen, muss sie aber zuerst an den zuständigen Fachblock weitergeben.

---

# 3. Wirtschaftliche Paketentscheidung

## 3.1 Vergleich der Varianten

### Variante A – eigener Infrastruktur-PR nur für den gemeinsamen Kern

| Kriterium | Bewertung |
|---|---|
| Codex-Verbrauch | mittel bis hoch; eigener Repository-Kontext, eigene Verträge, eigene Tests, später erneut Integration |
| doppelte Repository-Inspektion | hoch |
| Gefahr ungenutzter Abstraktionen | hoch, da kein realer Verbraucher die Verträge sofort belastet |
| spätere Wiederverwendung | theoretisch sehr gut |
| Testaufwand | hoch; viele synthetische Tests, später zusätzliche Integrations- und Vertragskorrekturen |
| sichtbarer Nutzerwert | zunächst keiner |
| Refactoring-Risiko | mittel; abstrahierte Verträge können am ersten realen Verbraucher scheitern |
| Klausurabdeckung | im Infrastruktur-PR null |

**Bewertung:** sauber auf dem Papier, wirtschaftlich schlecht. Der Branch wäre überwiegend unsichtbare Infrastruktur und widerspricht dem Architekturprinzip der vertikalen, sichtbaren Pakete.

### Variante B – gemeinsamer PR aus kleinem Kern und Hurwitz als erstem Verbraucher

| Kriterium | Bewertung |
|---|---|
| Codex-Verbrauch | mittel bis hoch in einem Durchgang, insgesamt aber am niedrigsten |
| doppelte Repository-Inspektion | niedrig |
| Gefahr ungenutzter Abstraktionen | niedrig; jede Kernfunktion wird sofort von Hurwitz benötigt |
| spätere Wiederverwendung | hoch, sofern interne Grenzen strikt bleiben |
| Testaufwand | effizient; Kerntests und offizielle Hurwitz-Referenzen validieren dieselben Verträge |
| sichtbarer Nutzerwert | hoch |
| Refactoring-Risiko | niedrig bis mittel; reale Nutzung erzwingt brauchbare Verträge |
| Klausurabdeckung | hoch; beide belegten zweiparametrigen Hurwitz-Klausurtypen werden adressiert |

**Bewertung:** bestes Verhältnis aus Klausurnutzen, Codex-Verbrauch und Architekturqualität.

### Variante C – sehr kleiner Kern im Hurwitz-PR, Extraktion erst beim zweiten Verbraucher

| Kriterium | Bewertung |
|---|---|
| Codex-Verbrauch | zunächst niedrig, über zwei Verbraucher voraussichtlich mittel bis hoch |
| doppelte Repository-Inspektion | mittel bis hoch |
| Gefahr ungenutzter Abstraktionen | niedrig |
| spätere Wiederverwendung | zunächst schlecht |
| Testaufwand | zunächst niedrig, später zusätzliche Migrations- und Regressionstests |
| sichtbarer Nutzerwert | hoch |
| Refactoring-Risiko | hoch; Hurwitz-Begriffe können in allgemeine Objekte einsickern |
| Klausurabdeckung | kurzfristig hoch |
| Gefahr fachlicher Kopplung | hoch, besonders bei Randsemantik, Diagnosen und Provenienz |

**Bewertung:** nur sinnvoll, wenn kein zweiter Verbraucher absehbar wäre. Das ist hier falsch: Routh, Nyquist-Parameterfälle und Wurzelortskurve sind bereits konkret vorgesehen.

## 3.2 Verbindliche Empfehlung

\[
\boxed{\text{Variante B}}
\]

Der wirtschaftlich richtige erste Umsetzungszuschnitt ist **ein gemeinsamer vertikaler PR aus kleinem Polynom-/Parameterkern und Hurwitz als erstem sichtbaren Verbraucher**.

Die interne Struktur muss trotzdem zwei fachlich getrennte Bereiche besitzen:

```text
shared polynomial/parameter domain
shared polynomial canonicalization
shared condition solving
        ↑
Hurwitz consumer
```

Nicht zulässig ist ein „Hurwitz-PR“, in dem allgemeine Mengen- oder Polynomlogik ausschließlich in Hurwitz-spezifischen Klassen versteckt wird.

## 3.3 Begründung gegenüber einem isolierten Kernbranch

Die maßgebliche Architektur verlangt sichtbare End-to-End-Pakete und warnt vor vorbereitenden Kernbranches ohne Nutzerwert. Das gemeinsame Paket verhindert:

- zwei Repository-Inventuren,
- zwei GUI- und Presenter-Anbindungen,
- doppelte Testeinrichtung,
- abstrakte Verträge ohne Verbraucherfeedback,
- spätere Reparatur eines falsch zugeschnittenen 2D-Modells.

Hurwitz liefert zugleich den wirtschaftlich wichtigsten ersten Belastungstest:

- Grad 2 bis 4,
- ein und zwei Parameter,
- strikte Grenzen,
- Gradabfälle,
- offene 2D-Parabelgebiete,
- offizielle Klausurreferenzen.

---

# 4. Erster verbindlicher Kernumfang

## 4.1 Muss im ersten gemeinsamen Paket enthalten sein

1. `CharacteristicPolynomialInput`.
2. kanonische Polynomdarstellung.
3. Polynomrollen und Analyseziele.
4. Provenienz, Annahmen und Ausschlussmengen.
5. Kürzungsprotokoll und Transformationshistorie.
6. Gradbestimmung und wiederholte Gradreduktion.
7. Nullpolynom und konstante Fälle.
8. parameterabhängiger Leitkoeffizient.
9. sichere Skalierung und Vorzeichenfälle.
10. atomare Gleichungen und Ungleichungen.
11. strikte und nichtstrikte Relationen.
12. explizite Nennerausschlüsse.
13. Schnitt und endliche Vereinigung.
14. leere Menge.
15. vollständig exakte einparametrige Lösung für unterstützte polynomiale und rationale Bedingungen.
16. zweiparametrige Gebiete in der für die belegten Hurwitz-Fälle nötigen Graphform.
17. Randklassifikation.
18. sichere Kontrollpunkte.
19. strukturierte Diagnosen.
20. kompakte Worked Steps.
21. LaTeX-fähige Ergebnisobjekte.
22. Hurwitz-Vertrag als erster echter Verbraucher.

## 4.2 Exakter 1D-Umfang

Für eine reelle Entscheidungsvariable werden unterstützt:

- endliche boolesche Formeln aus `AND` und `OR`,
- atomare Relationen
  \[
  f=0,\;f\neq0,\;f<0,\;f\le0,\;f>0,\;f\ge0,
  \]
- \(f\) als exaktes univariates Polynom,
- rationale Atome mit explizitem Zähler und Nenner,
- rationale, algebraische und exakt repräsentierbare reelle Nullstellen,
- exakte algebraische Wurzelobjekte, wenn keine einfache Radikaldarstellung vorliegt,
- offene, geschlossene und halboffene Intervalle,
- unbeschränkte Intervalle,
- isolierte Punkte,
- endliche Vereinigungen,
- Ausschlusspunkte,
- leere Menge.

„Vollständig exakt“ bedeutet:

- kein Ersetzen exakter Grenzen durch Gleitkommazahlen,
- keine numerische Rasterung,
- keine ausgelassenen Lösungszweige,
- jede Vereinigung wird kanonisch und disjunkt ausgegeben,
- numerische Werte sind nur zusätzliche Projektionen.

## 4.3 Zwingender 2D-Umfang für den ersten Hurwitz-Verbraucher

Für zwei geordnete reelle Parameter \((x,y)\) muss der erste Kern exakt lösen können:

1. reine \(x\)-Bedingungen:
   \[
   x\;\square\;c,
   \]
2. lineare oder quadratische Graphgrenzen:
   \[
   y\;\square\;f(x),
   \qquad \deg f\le2,
   \]
3. Bänder:
   \[
   f_{\mathrm{lower}}(x)\;\square_1\;y
   \;\square_2\;
   f_{\mathrm{upper}}(x),
   \]
4. endliche Schnitte solcher Bedingungen,
5. endliche Vereinigungen aus Grad- oder Vorzeichenfällen,
6. offene und geschlossene \(x\)- und \(y\)-Grenzen,
7. exakte Schnittpunkte von Geraden und Parabeln,
8. leere Teilzellen,
9. nicht zusammenhängende endliche Vereinigungen solcher Zellen,
10. Randgeraden und Randparabeln mit Inklusionsstatus.

Dies deckt die belegten Hurwitz-Fälle ab:

- lineare \(a\)-Grenze,
- gekoppelte lineare Untergrenze für \(K\),
- quadratische Obergrenze für \(K\),
- strikte Stabilitätsränder.

## 4.4 Nicht zwingend im ersten 2D-Paket

Eine allgemeine rationale 2D-Grenze wie

\[
T_N>\frac{K_R}{1+3K_R}
\]

ist für die beiden belegten zweiparametrigen Hurwitz-Klausurfälle nicht nötig.

Im ersten Paket gilt deshalb:

- Eine rationale 2D-Bedingung darf vollständig gelöst werden, **wenn** ihre Nennerzeichenlage bereits durch Annahmen feststeht und sie sicher auf eine unterstützte lineare oder quadratische Graphgrenze reduziert werden kann.
- Ist das Nennerzeichen nicht geklärt oder bleibt eine echte rationale Randkurve übrig, wird die Bedingung nicht verworfen.
- Das Ergebnis lautet dann `PARTIALLY_SOLVED_SAFE` mit expliziter Restbedingung.

Ein allgemeiner rationaler 2D-Gebietslöser wird auf die zweite Ausbaustufe verschoben.

## 4.5 Begrenzung der Fallzerlegung

Zulässig sind nur endliche, nachvollziehbare Fallzerlegungen aus:

- Leitkoeffizient \(>0\), \(<0\), \(=0\),
- Nennerzeichen \(>0\), \(<0\), sofern nötig,
- Gradabfällen,
- expliziten Vereinigungen des Fachmoduls.

Die Implementierung benötigt eine harte Fallzahlgrenze. Empfohlen wird für das erste Paket eine kleine technische Obergrenze, beispielsweise 32 normalisierte Zweige. Wird sie überschritten, darf kein Zweig stillschweigend entfallen. Das Ergebnis wird `PARTIALLY_SOLVED_SAFE` oder `UNSUPPORTED` mit Diagnose `CASE_SPLIT_LIMIT_EXCEEDED`.

---

# 5. Späterer Erweiterungsumfang

Nicht Bestandteil des ersten wirtschaftlichen Pakets:

- allgemeine rationale 2D-Randkurven,
- beliebige implizite algebraische 2D-Gebiete,
- allgemeine Kurvenanordnungen,
- zylindrische algebraische Zerlegung,
- allgemeine Quantorenelimination,
- mehr als zwei Entscheidungsparameter,
- symbolische Projektion höherdimensionaler Mengen,
- unbeschränkte automatische Fallzerlegung,
- beliebige transzendente Ausgangsungleichungen,
- interaktive 3D-Gebiete,
- allgemeine Optimierung,
- allgemeiner Beweisgenerator,
- allgemeine Polynomgrade ohne fachlichen Verbraucher,
- numerische Approximation als Ersatz für ungelöste exakte Gebiete.

Mögliche spätere Erweiterungen bei realem Verbraucherbedarf:

1. rationale 2D-Graphgrenzen mit vollständiger Nennerfallanalyse,
2. weitere Polynomgrade,
3. zusätzliche 2D-Gleichheitskurven,
4. Routh-spezifische Nennerausschlüsse,
5. Nyquist-Gain-Bereiche,
6. Wurzelortskurven- und Reglerbedingungen,
7. Projektion oder Plot-Hilfen für mehrere Gebiete.

---

# 6. Verträge und Invarianten

## 6.1 Gemeinsame exakte Skalartypen

Alle algebraisch maßgeblichen Felder verwenden eine exakte symbolische Darstellung.

Zulässig:

- ganze Zahlen,
- rationale Zahlen,
- exakte algebraische Zahlen,
- Radikale,
- exakte algebraische Wurzelobjekte,
- deklarierte symbolische Parameter,
- \(\pi\) oder Logarithmen exakter positiver Zahlen, wenn sie bereits vom Fachmodul als isolierte Konstante übergeben werden.

Nicht zulässig für ein Ergebnis mit Status `SOLVED_EXACT`:

- ausschließlich gerundete Gleitkommazahlen,
- numerisch geschätzte Nullstellen ohne exaktes Gegenstück,
- nicht deklarierte Symbole,
- numerische Testpunkte als einzige Lösungsbegründung.

Inexakte Eingaben dürfen erhalten und diagnostiziert werden. Ohne sichere Rationalisierung darf daraus aber kein exakt gelöstes Ergebnis behauptet werden.

---

## 6.2 `SourceProvenance`

### Pflichtfelder

| Feld | Bedeutung |
|---|---|
| `producer` | erzeugender Fachblock oder Eingabemodus |
| `source_kind` | direkte Eingabe, Dokument, upstream result, Herleitung |
| `source_reference` | Dokument/Aufgabe/Abschnitt oder interne Ergebnis-ID |
| `statement_id` | stabile ID des erzeugten Ausdrucks oder der Bedingung |
| `description` | kurze fachliche Beschreibung |

### Optionale Felder

- Quellenseite,
- Aufgabenteil,
- Elternobjekt-ID,
- bekannte Quellenkorrektur,
- Benutzerhinweis.

### Invarianten

- Jede fachlich erzeugte Bedingung besitzt Provenienz.
- Eine Transformation ersetzt Provenienz nicht, sondern referenziert den Ursprung.
- Der Kern erfindet keine fachliche Beschreibung.
- Numerische Kontrollwerte dürfen nicht als neue fachliche Quelle erscheinen.

---

## 6.3 `TransformationRecord`

### Pflichtfelder

| Feld | Bedeutung |
|---|---|
| `operation` | Art der Transformation |
| `before` | exakter Ausgangsausdruck |
| `after` | exakter Ergebnisausdruck |
| `conditions_used` | Bedingungen, unter denen die Transformation äquivalent ist |
| `exact` | muss im ersten Paket wahr sein |
| `reason` | technische/fachliche Begründung |
| `provenance_links` | Ursprung der transformierten Ausdrücke |

### Zulässige Operationen

- `EXPAND`
- `COLLECT_BY_VARIABLE`
- `INSERT_ZERO_COEFFICIENT`
- `RECONSTRUCT_FROM_COEFFICIENTS`
- `REMOVE_NONZERO_CONSTANT_FACTOR`
- `MULTIPLY_BY_MINUS_ONE`
- `DIVIDE_BY_KNOWN_POSITIVE_FACTOR`
- `DIVIDE_BY_KNOWN_NEGATIVE_FACTOR`
- `DEGREE_REDUCTION`
- `NORMALIZE_RELATION`
- `CLEAR_DENOMINATOR_WITH_SIGN_PROOF`
- `BRANCH_ON_SIGN`
- `CANONICALIZE_INTERVAL_UNION`

### Verbotene Zustände

- Division ohne dokumentierte Nichtnullbedingung.
- Kreuzmultiplikation ohne dokumentiertes Nennerzeichen oder vollständige Vorzeichenfallanalyse.
- Transformationsschritt mit nur numerischem Vorher-/Nachher-Vergleich.
- stillschweigende Kürzung eines parameterabhängigen Faktors.

---

## 6.4 `CancellationReport`

Der gemeinsame Kern führt keine Übertragungsfunktionskürzung aus, muss ein upstream erzeugtes Kürzungsprotokoll aber erhalten.

### Pflichtfelder

| Feld | Bedeutung |
|---|---|
| `status` | `NONE`, `FACTORS_REMOVED`, `UNKNOWN_NOT_ALLOWED` |
| `raw_expression_ref` | Referenz auf Rohform |
| `reduced_expression_ref` | Referenz auf reduzierte Form |
| `removed_factors` | exakte Faktoren mit Vielfachheiten |
| `validity_conditions` | Bedingungen der Kürzung |
| `removed_poles_or_holes` | bekannte algebraische Folgen |
| `producer` | upstream Transferfunktionskern |

### Invarianten

- Bei `REDUCED_TRANSFER_DENOMINATOR` ist ein expliziter Bericht Pflicht, auch wenn `status=NONE`.
- Bei nichttrivialer Kürzung darf ein reduziertes Polynom nicht als rohes internes Polynom ausgegeben werden.
- Der Kern entscheidet nicht, welches Polynom fachlich zu prüfen ist.

---

## 6.5 `CharacteristicPolynomialInput`

### Pflichtfelder

| Feld | Bedeutung |
|---|---|
| `polynomial_expr` | exakter Ausdruck |
| `variable` | Hauptvariable, standardmäßig \(s\), alternativ \(\lambda\) |
| `coefficients_desc` | Koeffizienten \([a_n,\ldots,a_0]\) |
| `declared_degree` | höchster übergebener Exponent vor Parameterspezialisierung |
| `decision_parameters` | geordnete Liste mit 0, 1 oder 2 reellen Parametern |
| `fixed_symbols` | alle übrigen Symbole |
| `assumptions` | explizite Grundannahmen |
| `excluded_parameter_sets` | explizite Ausschlussbedingungen |
| `polynomial_role` | Rolle des Polynoms |
| `analysis_target` | fachliches Analyseziel |
| `provenance` | Herkunft |
| `cancellation_report` | explizit vorhanden |
| `transformation_history` | bisherige upstream Transformationen |

### Polynomrollen

- `DIRECT_CHARACTERISTIC_POLYNOMIAL`
- `STATE_CHARACTERISTIC_POLYNOMIAL`
- `RAW_CLOSED_LOOP_CHARACTERISTIC`
- `CLOSED_TRANSFER_DENOMINATOR`
- `REDUCED_TRANSFER_DENOMINATOR`

### Analyseziele

- `STATE_ASYMPTOTIC`
- `INTERNAL_CLOSED_LOOP_ASYMPTOTIC`
- `EXTERNAL_BIBO`
- `DENOMINATOR_ANALYSIS_ONLY`

### Invarianten

1. Rekonstruktion aus `coefficients_desc` ergibt exakt `polynomial_expr`.
2. Fehlende Potenzen erscheinen als Nullkoeffizienten.
3. Alle freien Symbole sind entweder Entscheidungsparameter oder feste Symbole.
4. Höchstens zwei Entscheidungsparameter.
5. Die Hauptvariable ist kein Entscheidungsparameter.
6. `declared_degree = len(coefficients_desc)-1`.
7. Annahmen und Ausschlüsse sind separate, explizite Formeln.
8. Das Analyseziel wird nicht aus der Rolle geraten.
9. Exakte und numerische Repräsentationen sind getrennt.

### Verbotene Mischzustände

- `EXTERNAL_BIBO` mit `RAW_CLOSED_LOOP_CHARACTERISTIC` als einzigem primären Analyseobjekt.
- `INTERNAL_CLOSED_LOOP_ASYMPTOTIC` mit ausschließlich reduziertem Nenner bei nichttrivialer Kürzung.
- `STATE_ASYMPTOTIC` mit einem reduzierten Übertragungsfunktionsnenner.
- `REDUCED_TRANSFER_DENOMINATOR` ohne `CancellationReport`.
- unterschiedliche Ausdrücke in Koeffizienten- und Polynomdarstellung.
- nicht deklarierter parameterabhängiger Leitkoeffizient.

Der Kern darf solche Mischzustände nicht fachlich umdeuten. Er meldet einen Vertragsfehler.

---

## 6.6 `CanonicalCharacteristicPolynomial`

### Pflichtfelder

| Feld | Bedeutung |
|---|---|
| `original_input_ref` | Referenz auf Eingabe |
| `expanded_expr` | ausmultiplizierter exakter Ausdruck |
| `collected_expr` | nach Hauptvariable gesammelte Form |
| `coefficients_desc` | kanonische Koeffizienten |
| `nominal_degree` | Grad vor Fallzerlegung |
| `decision_parameters` | unverändert |
| `assumptions` | unverändert beziehungsweise normalisiert |
| `exclusions` | unverändert beziehungsweise ergänzt |
| `degree_cases` | vollständige Liste der Gradfälle |
| `role` | unverändert |
| `analysis_target` | unverändert |
| `provenance` | unverändert |
| `transformation_history` | ergänzt |
| `diagnostics` | strukturierte Meldungen |

### Invarianten

- Originalinformation bleibt rekonstruierbar.
- Kein parameterabhängiger Faktor wird ohne Bedingung entfernt.
- Jeder als vollständig markierte Fallsatz ist disjunkt und deckt den zulässigen Eingaberaum ab.
- Ein unvollständiger Fallsatz trägt niemals den Status „vollständig“.

---

## 6.7 `PolynomialDegreeCase`

### Pflichtfelder

| Feld | Bedeutung |
|---|---|
| `case_id` | stabile Fall-ID |
| `guard_condition` | exakte Bedingung dieses Falls |
| `effective_expr` | Polynom nach Gradreduktion und sicherer Skalierung |
| `effective_coefficients_desc` | Koeffizienten des effektiven Polynoms |
| `effective_degree` | nichtnegativer Grad oder Sonderstatus |
| `leading_coefficient_original` | ursprünglicher Leitkoeffizient des Falls |
| `scaling_factor` | angewendeter Faktor |
| `scaling_conditions` | Begründung der sicheren Skalierung |
| `case_kind` | regulär, Gradabfall, konstant, Nullpolynom |
| `transformations` | fallbezogene Historie |
| `diagnostics` | fallbezogene Meldungen |

### `case_kind`

- `REGULAR_POLYNOMIAL`
- `DEGREE_REDUCED_POLYNOMIAL`
- `CONSTANT_NONZERO`
- `ZERO_POLYNOMIAL`

### Invarianten

- Bei regulären und reduzierten Polynomfällen ist der Leitkoeffizient nach Normierung positiv.
- `scaling_factor` ist unter `guard_condition` sicher von null verschieden.
- Gradreduktion wird wiederholt, bis der neue Leitkoeffizient unter dem Fall nicht null ist.
- Der Kern bewertet `CONSTANT_NONZERO` und `ZERO_POLYNOMIAL` nicht als stabil oder instabil.
- Hurwitz darf nur unterstützte positive Grade konsumieren.

---

## 6.8 `AtomicParameterCondition`

### Pflichtfelder

| Feld | Bedeutung |
|---|---|
| `condition_id` | stabile ID |
| `left_expr` | exakter Ausdruck |
| `relation` | `EQ`, `NE`, `LT`, `LE`, `GT`, `GE` |
| `right_expr` | exakter Ausdruck |
| `normalized_expr` | Ausdruck in der Form \(f\;\square\;0\) |
| `variables` | verwendete Entscheidungsparameter |
| `condition_kind` | fachliche Herkunftskategorie |
| `strictness` | aus Relation abgeleitet |
| `provenance` | Herkunft |
| `normalization_history` | exakte Umformungen |

### `condition_kind`

Allgemeine Kategorien:

- `ASSUMPTION`
- `EXCLUSION`
- `DEGREE_CASE_GUARD`
- `USER_CONSTRAINT`
- `FACULTY_GENERATED`

Für Hurwitz:

- `HURWITZ_COEFFICIENT_POSITIVITY`
- `HURWITZ_DETERMINANT_POSITIVITY`

Spätere Verbraucher dürfen weitere Kategorien ergänzen, ohne die Solverlogik zu ändern.

### Invarianten

- Ein Nennerausschluss ist ein echtes Atom `denominator != 0`.
- Fachliche Herkunft beeinflusst nicht die algebraische Lösung.
- Der Kern verändert nicht `condition_kind`.
- Eine strikte Relation bleibt strikt.
- Originalrelation und normalisierte Relation bleiben verknüpft.

---

## 6.9 `ConditionFormula`

### Knotenarten

- `ATOM`
- `AND`
- `OR`

### Pflichtfelder

- stabile Formel-ID,
- Kind,
- Kindknoten beziehungsweise Atomreferenz,
- Provenienzverweise,
- Normalisierungsstatus.

### Invarianten

- Keine allgemeinen Quantoren.
- Keine freie `NOT`-Operation; Negationen werden atomar aufgelöst.
- Leere Konjunktion entspricht wahr.
- Leere Disjunktion entspricht falsch.
- Fallverzweigungen bleiben als `OR` sichtbar.
- Der Normalisierer darf keine Zweige stillschweigend entfernen; leere Zweige werden mit Begründung verworfen.

---

## 6.10 `ParameterConditionProblem`

### Pflichtfelder

| Feld | Bedeutung |
|---|---|
| `problem_id` | stabile ID |
| `variables` | eine oder zwei geordnete reelle Variablen |
| `assumptions_formula` | Grundannahmen |
| `exclusions_formula` | Ausschlüsse |
| `generated_formula` | vom Fachmodul erzeugte Bedingungen |
| `combined_formula` | exakter Schnitt der drei Teile |
| `requested_result_kind` | `ONE_DIMENSIONAL` oder `TWO_DIMENSIONAL` |
| `completeness_required` | ja/nein |
| `source_case_id` | zugehöriger Gradfall |
| `provenance` | Aufrufer und Fachkontext |
| `numeric_viewport` | optional, nur Darstellung |
| `case_split_limit` | technische Obergrenze |

### Invarianten

\[
\text{combined}
=
\text{assumptions}
\land
\text{exclusions}
\land
\text{generated}.
\]

- `numeric_viewport` beeinflusst niemals die exakte Lösung.
- Ein `completeness_required=true` darf nicht mit einem teilweise gelösten Ergebnis als Erfolg beendet werden.
- Ein Problem besitzt höchstens zwei Entscheidungsparameter.
- Nicht deklarierte Symbole sind Vertragsfehler.

---

## 6.11 Einparametrige Ergebnisobjekte

### `ExactBoundaryPoint`

Pflichtfelder:

- exakter Wert,
- numerische Projektion optional,
- Inklusionsstatus,
- Ausschlussstatus,
- erzeugende Bedingungen,
- Provenienz.

### `ExactInterval`

Pflichtfelder:

- linke Grenze,
- rechte Grenze,
- linke Offenheit,
- rechte Offenheit,
- Unbeschränktheitsstatus,
- zugehörige Bedingungen,
- optionaler zertifizierter Innenpunkt.

Invarianten:

- linke Grenze ist kleiner als rechte Grenze,
- offene/geschlossene Grenzinformation ist explizit,
- Ausschlusspunkte sind nicht enthalten,
- Intervalle einer kanonischen Vereinigung sind disjunkt und sortiert.

### `OneDimensionalRegionResult`

Pflichtfelder:

- Status,
- exakte Intervallvereinigung,
- isolierte Punkte,
- Ausschlusspunkte,
- leere-Menge-Flag,
- Restbedingungen,
- numerische Projektionen,
- Kontrollpunkte,
- Diagnosen,
- Provenienz.

Verbotene Mischzustände:

- `SOLVED_EXACT` mit Restbedingungen,
- `EMPTY` mit nichtleeren Intervallen,
- nur numerische Grenzen bei behaupteter Exaktheit.

---

## 6.12 Zweiparametrige Ergebnisobjekte

### `BoundaryObject`

Pflichtfelder:

| Feld | Bedeutung |
|---|---|
| `boundary_id` | stabile ID |
| `boundary_kind` | vertikale Linie, Graphkurve, Punkt, Ausschlusskurve |
| `exact_equation` | exakte Gleichung |
| `graph_function` | bei \(y=f(x)\) |
| `x_domain` | exakte 1D-Domäne |
| `included` | enthalten, ausgeschlossen, teilweise enthalten |
| `source_conditions` | erzeugende Atome |
| `provenance` | fachliche Herkunft |
| `numeric_geometry` | optionale Plotprojektion |

### `TwoDimensionalCell`

Pflichtfelder:

- `cell_id`,
- exakte \(x\)-Domäne,
- aktive untere Grenze,
- aktive obere Grenze,
- Offenheit der Grenzen,
- zusätzliche Gleichheits- oder Ausschlussbedingungen,
- exakter zertifizierter Innenpunkt, sofern die Zelle zweidimensional ist,
- numerische Projektion,
- Originalbedingungen,
- Verifikationsstatus.

### `TwoDimensionalRegionResult`

Pflichtfelder:

- Status,
- geordnete Variablen,
- exaktes reduziertes Bedingungssystem,
- endliche Liste disjunkter Zellen,
- Randobjekte,
- exakte Schnittpunkte,
- ausgeschlossene Mengen,
- Restbedingungen,
- Kontrollpunkte,
- numerische Projektion,
- Vollständigkeitsstatus,
- Diagnosen,
- Provenienz.

Verbotene Mischzustände:

- `SOLVED_EXACT` mit ungelösten Restbedingungen.
- behauptete vollständige Zellen ohne nachgewiesene Randordnung.
- `EMPTY` mit Zellen.
- numerisch gerasterte Zelle ohne exakte Beschreibung.
- ausgeschlossene Randkurve gleichzeitig als vollständig enthalten.

---

## 6.13 `PartialRegionResult`

Pflichtfelder:

- sicher gelöster Anteil,
- unveränderte Restformel,
- Grund der Nichtauflösung,
- betroffene Atome,
- bekannte Randobjekte,
- Vollständigkeitsstatus `PARTIAL`,
- Diagnosen,
- Provenienz.

Invarianten:

- Kein ungelöster Teil wird entfernt.
- Ein sicher gelöster Anteil muss logisch aus der Originalformel folgen.
- Die Ausgabe darf keine Gesamtmenge behaupten.
- Presenter müssen „teilweise gelöst“ deutlich anzeigen.

---

## 6.14 `NumericalControlPoint`

### Pflichtfelder

| Feld | Bedeutung |
|---|---|
| `exact_point` | exakter Punkt, sofern konstruierbar |
| `numeric_point` | numerische Projektion |
| `location_kind` | Innenpunkt, Außenpunkt, Randpunkt |
| `condition_results` | Wahrheitswert je Originalbedingung |
| `certification` | `EXACT_VERIFIED`, `NUMERIC_ONLY`, `FAILED` |
| `distance_to_exclusions` | numerischer Kontrollwert |
| `source_cell_or_interval` | Herkunft |
| `diagnostics` | Warnungen |

### Invarianten

- Ein Testpunkt ist niemals der alleinige Beweis einer Zelle.
- `NUMERIC_ONLY` darf nicht als zertifizierter Innenpunkt bezeichnet werden.
- Für `SOLVED_EXACT` soll pro nichtleerer offener Zelle mindestens ein exakt verifizierter Kontrollpunkt vorliegen.
- Numerische Werte werden mit ausreichender Präzision erzeugt, aber nicht in exakte Grenzen zurückgeschrieben.

---

## 6.15 `Diagnostic`

### Pflichtfelder

- Code,
- Schweregrad,
- Phase,
- betroffene Objekt-ID,
- kurze Meldung,
- fachlich sichere Aussage,
- erhaltene Originaldaten,
- empfohlene nächste Aktion,
- Provenienz.

### Schweregrade

- `INFO`
- `WARNING`
- `ERROR`
- `UNSUPPORTED`

### Ergebnisstatus

- `SOLVED_EXACT`
- `EMPTY`
- `PARTIALLY_SOLVED_SAFE`
- `UNSUPPORTED`
- `INVALID_INPUT`
- `INCONSISTENT_ASSUMPTIONS`
- `INDETERMINATE`

---

# 7. Algorithmen

## 7.1 Polynomkanonisierung

### Eingabe

`CharacteristicPolynomialInput`

### Ablauf

1. Hauptvariable validieren.
2. freie und feste Symbole vollständig bestimmen.
3. Parameterzahl prüfen.
4. Ausdruck exakt expandieren.
5. nach Hauptvariable sammeln.
6. Koeffizienten einschließlich fehlender Nullkoeffizienten extrahieren.
7. mit `coefficients_desc` rekonstruieren.
8. Ausdrucks- und Koeffizientenform exakt vergleichen.
9. nominalen Leitkoeffizienten bestimmen.
10. Rollen-/Analyseziel-Kompatibilität prüfen.
11. Kürzungsprotokoll prüfen.
12. Annahmen und Ausschlüsse normalisieren.
13. Gradfallzerlegung starten.
14. Transformationshistorie ergänzen.
15. Rekonstruktionskontrolle ausführen.
16. `CanonicalCharacteristicPolynomial` zurückgeben.

### Fehlerverhalten

Bei einem Rekonstruktionswiderspruch wird keine der beiden Darstellungen bevorzugt. Rückgabe:

- `INVALID_INPUT`,
- Originalausdruck,
- Koeffizientenrekonstruktion,
- Differenzausdruck,
- Diagnose `COEFFICIENT_RECONSTRUCTION_MISMATCH`.

---

## 7.2 Wiederholte Gradreduktion

Für eine Koeffizientenliste

\[
[a_n(\theta),a_{n-1}(\theta),\ldots,a_0(\theta)]
\]

gilt:

1. Prüfe, ob \(a_n\) unter den aktuellen Fallbedingungen sicher positiv, negativ oder null ist.
2. Bei \(a_n>0\): regulärer Gradfall.
3. Bei \(a_n<0\): mit \(-1\) skalieren und regulären Gradfall erzeugen.
4. Bei \(a_n=0\): höchsten Koeffizienten entfernen und mit dem nächsten Koeffizienten wiederholen.
5. Ist auch dieser null, wird erneut reduziert.
6. Bleibt ein konstanter Koeffizient:
   - ungleich null: `CONSTANT_NONZERO`,
   - gleich null: `ZERO_POLYNOMIAL`.
7. Kann die Vorzeichenlage nicht aus Annahmen bestimmt werden, entstehen disjunkte Fallzweige:
   \[
   a_n>0,\quad a_n<0,\quad a_n=0.
   \]
8. Unmögliche Zweige werden nur nach exakter Widerspruchserkennung entfernt.

### Vollständigkeitsregel

Ein Gradfallsatz gilt nur als vollständig, wenn die Guards:

- paarweise disjunkt sind,
- zusammen den zulässigen Parameterraum unter den Eingabeannahmen abdecken,
- keine nicht analysierten Reste besitzen.

---

## 7.3 Sichere Skalierung

Zulässig:

1. Entfernen einer sicher von null verschiedenen parameterfreien Konstanten.
2. Division durch einen unter dem aktuellen Guard sicher positiven Faktor.
3. Division durch einen unter dem aktuellen Guard sicher negativen Faktor mit zusätzlicher Vorzeichenumkehr.
4. Multiplikation mit \(-1\), um positiven Leitkoeffizienten herzustellen.

Nicht zulässig:

- Division durch einen nur vermutlich positiven Ausdruck,
- Entfernen eines parameterabhängigen Faktors ohne Guard,
- Skalierung, die neue Nennerausschlüsse nicht dokumentiert,
- numerische Vorzeichenentscheidung nahe null.

Jede Skalierung erzeugt einen `TransformationRecord`.

---

## 7.4 Normalisierung atomarer Bedingungen

Jedes Atom

\[
L\;\square\;R
\]

wird zu

\[
f=L-R\;\square\;0
\]

normalisiert.

Ablauf:

1. Originalrelation speichern.
2. Differenzausdruck exakt bilden.
3. Ausdruck expandieren und sammeln.
4. sichere gemeinsame Faktoren entfernen:
   - positive Faktoren ohne Relationsänderung,
   - negative Faktoren mit Relationsumkehr,
   - unbekannte Faktoren nur über Fallzerlegung.
5. rationale Struktur explizit erfassen.
6. Nennerausschlüsse erzeugen oder verknüpfen.
7. Normalisierungshistorie speichern.
8. logische Äquivalenz durch symbolische Rekonstruktion prüfen, soweit möglich.

Striktheit darf nie verändert werden, außer wenn eine Multiplikation mit einem negativen Faktor die Relationsrichtung korrekt umkehrt.

---

## 7.5 Nennerzeichen und Nennerausschlüsse

Für

\[
\frac{N(\theta)}{D(\theta)}\;\square\;0
\]

gilt immer:

\[
D(\theta)\neq0.
\]

### Fall A – Nennerzeichen aus Annahmen bewiesen

- Bei \(D>0\): Relation auf \(N\) übertragen.
- Bei \(D<0\): Relationsrichtung umkehren.
- Ausschluss \(D\neq0\) bleibt in Provenienz und Ergebnis erhalten.

### Fall B – einparametrig, Nennerzeichen nicht bekannt

- reelle Nullstellen von \(D\) bestimmen,
- Definitionspunkte ausschließen,
- Vorzeichentabelle gemeinsam mit Zählernullstellen bilden,
- exakte Intervalle lösen.

### Fall C – zweiparametrig, Nennerzeichen nicht bekannt

Im ersten Paket:

- nur lösen, wenn eine endliche Fallzerlegung auf unterstützte lineare/quadratische Graphbedingungen führt,
- andernfalls `PARTIALLY_SOLVED_SAFE`,
- Restbedingung und Ausschlusskurve vollständig erhalten.

Unsicheres Kreuzmultiplizieren ist verboten.

---

## 7.6 Exakte einparametrige Lösung

Für jeden Konjunktionszweig:

1. alle Atome auf eine Variable validieren,
2. Zähler- und Nennerpolynome erfassen,
3. alle reellen kritischen Punkte exakt bestimmen:
   - Nullstellen der Zähler,
   - Nullstellen der Nenner,
   - Gleichheitspunkte,
4. kritische Punkte exakt sortieren,
5. reelle Achse in offene Zellen und Einzelpunkte zerlegen,
6. auf jeder offenen Zelle das Vorzeichen jedes Atoms bestimmen,
7. Randpunkte mit Originalrelationen prüfen,
8. Nennernullstellen entfernen,
9. resultierende Intervalle und Punkte erzeugen,
10. Zweige vereinigen,
11. überlappende Intervalle kanonisch zusammenführen,
12. offene und geschlossene Grenzen erhalten,
13. leere Menge explizit erzeugen,
14. pro nichtleerem Intervall einen Kontrollpunkt konstruieren,
15. alle Originalbedingungen am Kontrollpunkt prüfen.

### Kontrollpunktkonstruktion

- beschränktes Intervall: exakter Mittelpunkt,
- \((-\infty,b)\): \(b-1\) oder sicherer algebraischer Abstand,
- \((a,\infty)\): \(a+1\),
- Intervall mit Ausschlusspunkt: Punkt innerhalb einer disjunkten Teilzelle,
- algebraische Grenzen: exakter algebraischer Mittelpunkt.

Der Kontrollpunkt unterstützt die Verifikation, ersetzt aber nicht die Vorzeichenzellenanalyse.

---

## 7.7 Schnitt und Vereinigung von 1D-Mengen

### Schnitt

- Grenzen über Maximum der unteren und Minimum der oberen Grenze bestimmen.
- Offenheit korrekt kombinieren:
  - gleicher Rand ist nur enthalten, wenn alle beteiligten Bedingungen ihn enthalten.
- Ausschlusspunkte nach dem Schnitt entfernen.
- degeneriertes geschlossenes Intervall kann zu einem Einzelpunkt werden.
- degeneriertes offenes Intervall ist leer.

### Vereinigung

- Intervalle exakt sortieren.
- überlappende oder berührende Intervalle nur dann zusammenführen, wenn der Berührpunkt enthalten ist.
- isolierte Punkte in Intervalle integrieren, wenn enthalten.
- Ausschlusspunkte nicht überdecken.
- Ergebnis als disjunkte kanonische Vereinigung ausgeben.

---

## 7.8 Begrenzte zweiparametrige Lösung

### Unterstützte Normalform

Pro Konjunktionszweig:

\[
x\in X,
\]

\[
y\;\square\;f_i(x),
\qquad \deg f_i\le2,
\]

sowie optionale Graphgleichheiten und explizite Ausschlussgrenzen.

### Ablauf

1. Variablenreihenfolge festlegen.
2. reine \(x\)-Bedingungen mit dem 1D-Solver lösen.
3. alle übrigen Bedingungen als untere Grenze, obere Grenze, Gleichheitsgraph oder Ausschlussgraph klassifizieren.
4. Differenzen aller potenziell konkurrierenden Grenzfunktionen bilden.
5. reelle Schnittstellen exakt bestimmen.
6. \(x\)-Domäne an allen Schnittstellen partitionieren.
7. auf jedem offenen \(x\)-Abschnitt die Reihenfolge der Grenzfunktionen exakt bestimmen.
8. aktive untere Grenze als Maximum aller unteren Grenzen bestimmen.
9. aktive obere Grenze als Minimum aller oberen Grenzen bestimmen.
10. Nichtleerheit exakt prüfen:
    \[
    f_{\mathrm{lower}}<f_{\mathrm{upper}},
    \]
    beziehungsweise nichtstrikt bei enthaltenen Gleichheitsfällen.
11. Offenheit der aktiven Grenzen aus den erzeugenden Atomen bestimmen.
12. Randpunkte und vertikale Randstücke an \(x\)-Grenzen klassifizieren.
13. leere Zellen verwerfen und diagnostizieren.
14. disjunkte Zellen erzeugen.
15. pro 2D-Zelle exakten Innenpunkt konstruieren.
16. alle Originalbedingungen am Punkt exakt prüfen.
17. Grenzen und Schnittpunkte numerisch projizieren.
18. Zellen über `OR` vereinigen.
19. Vollständigkeit prüfen.
20. Plot-fähiges, aber nicht rasterbasiertes Ergebnis liefern.

### Gleichheitsgraphen

Eine Bedingung

\[
y=f(x)
\]

kann als eindimensionale Zelle mit exakter \(x\)-Domäne repräsentiert werden. Sie darf nicht als zweidimensionales Gebiet ausgegeben werden.

### Grenzen des ersten Pakets

Nicht unterstützt:

- allgemeine implizite Kurven,
- Bedingungen quadratisch in \(y\),
- Wurzelfunktionen als automatisch erzeugte Grenzen,
- allgemeine rationale Graphkurven ohne bewiesenes Nennerzeichen,
- unendlich viele Schnittpunkte,
- transzendente Grenzfunktionen.

---

## 7.9 Testpunktverifikation

Ein Kontrollpunkt wird erst `EXACT_VERIFIED`, wenn:

1. er exakt dargestellt ist,
2. er keiner Ausschlussmenge angehört,
3. jede Originalbedingung exakt ausgewertet wurde,
4. das Ergebnis mit der behaupteten Zelle übereinstimmt.

Kann nur numerisch geprüft werden:

- `certification=NUMERIC_ONLY`,
- Warnung,
- Punkt darf nicht als Beweis für Vollständigkeit verwendet werden.

Für Randpunkte werden zusätzlich Residuen der Randgleichungen ausgegeben.

---

## 7.10 Rekonstruktions- und Konsistenzprüfungen

Pflichtprüfungen:

1. Polynom aus Koeffizienten rekonstruieren.
2. kanonisches Polynom mit Eingang vergleichen.
3. jeden Gradfall in das Originalpolynom einsetzen.
4. Skalierungsfaktor und Guard prüfen.
5. normalisierte Bedingung gegen Originalbedingung prüfen.
6. Nennerausschlüsse auf allen Ergebnismengen erhalten.
7. Intervallunion auf Disjunktheit prüfen.
8. 2D-Zellen auf überlappende Innenräume prüfen.
9. Randinklusion gegen Originalrelationen prüfen.
10. jeden Kontrollpunkt in allen Originalbedingungen auswerten.
11. `SOLVED_EXACT` nur ohne Restbedingungen zulassen.
12. numerische Projektion nie in exakte Ausdrücke zurückschreiben.

---

# 8. Grad- und Sonderfälle

## 8.1 Nullpolynom

Ein identisch verschwindendes Polynom ist kein reguläres charakteristisches Polynom.

Rückgabe:

- `case_kind=ZERO_POLYNOMIAL`,
- Guard des Parameterfalls,
- Originalausdruck,
- Diagnose `ZERO_POLYNOMIAL_CASE`,
- keine Stabilitätsaussage.

Hurwitz entscheidet, wie dieser Fall fachlich dargestellt wird.

## 8.2 Konstantes Nichtnullpolynom

Rückgabe:

- `case_kind=CONSTANT_NONZERO`,
- exakter konstanter Wert,
- Guard,
- Diagnose `CONSTANT_POLYNOMIAL_CASE`,
- keine automatische Aussage „stabil“.

## 8.3 Parameterabhängiger Leitkoeffizient

Es entstehen grundsätzlich:

\[
a_n>0,\qquad a_n<0,\qquad a_n=0.
\]

- positive und negative Fälle werden auf positiven Leitkoeffizienten normiert,
- Nullfall wird gradreduziert,
- Guards bleiben Teil des späteren Mengenproblems.

## 8.4 Fehlende Potenzen

Fehlende Potenzen werden explizit mit Nullkoeffizienten ergänzt. Das ist keine Gradreduktion, solange der höchste Koeffizient nicht null ist.

## 8.5 Parameterabhängige Nullkoeffizienten im Inneren

Ein innerer Koeffizient, der auf einer Parameterteilmenge null wird, senkt den Grad nicht. Der Fachverbraucher kann daraus eigene Bedingungen erzeugen.

## 8.6 Ausschlussmengen

Ausschlussmengen werden als Bedingungen erster Klasse behandelt. Sie bleiben erhalten bei:

- Gradfallbildung,
- Skalierung,
- Intervallschnitt,
- Vereinigung,
- 2D-Zellbildung,
- Presenter-Ausgabe.

## 8.7 Leere Fallzweige

Ein Fallzweig wird nur entfernt, wenn seine Guard-Bedingungen zusammen mit Annahmen exakt widersprüchlich sind. Die Diagnose nennt die widersprüchlichen Atome.

---

# 9. 1D- und begrenzte 2D-Mengen

## 9.1 1D-Kanonik

Ein exaktes 1D-Ergebnis wird als

\[
S=P\cup\bigcup_{i=1}^m I_i
\]

repräsentiert, mit:

- endlicher Punktmenge \(P\),
- disjunkten, sortierten Intervallen \(I_i\),
- expliziten Ausschlusspunkten,
- exakter und numerischer Grenzdarstellung.

## 9.2 2D-Kanonik für das erste Paket

Ein exaktes 2D-Ergebnis wird als endliche Vereinigung

\[
S=\bigcup_{j=1}^m C_j
\]

von Zellen dargestellt. Eine 2D-Zelle besitzt die Form

\[
C_j=
\left\{
(x,y)\in\mathbb R^2
\;\middle|\;
x\in X_j,\;
\ell_j(x)\;\square_L\;y\;\square_U\;u_j(x)
\right\},
\]

wobei:

- \(X_j\) eine exakte 1D-Menge ist,
- \(\ell_j,u_j\) Polynome vom Grad höchstens 2 sind,
- \(\square_L,\square_U\) strikt oder nichtstrikt sind,
- zusätzliche Ausschlussränder separat erhalten bleiben.

## 9.3 Randklassifikation

Jeder Rand besitzt:

- exakte Gleichung,
- geometrischen Typ,
- Domäne,
- Inklusionsstatus,
- erzeugende Bedingung,
- fachliche Provenienz,
- numerische Projektion.

Mögliche Inklusionsstatus:

- `INCLUDED`
- `EXCLUDED`
- `PARTIALLY_INCLUDED`

Die fachliche Bezeichnung des Randes bleibt beim Verbraucher.

## 9.4 Kein Rasterersatz

Ein Plot darf das exakte Gebiet visualisieren. Er darf es nicht definieren.

Verboten:

- Pixel-/Rasterklassifikation als Lösung,
- Monte-Carlo-Testpunkte zur Gebietsbestimmung,
- numerisch gefundene Randkurven ohne exakte Bedingung,
- stillschweigendes Abschneiden am Plotfenster.

Unbeschränkte Gebiete bleiben algebraisch unbeschränkt, auch wenn der Plot ein endliches Fenster verwendet.

---

# 10. Schnittstelle zu Hurwitz

## 10.1 Übergabe an Hurwitz

Hurwitz erhält pro analysierbarem `PolynomialDegreeCase`:

- positiven effektiven Leitkoeffizienten,
- effektive Koeffizientenliste,
- effektiven Grad,
- Gradfall-Guard,
- Entscheidungsparameter,
- feste Symbole und Annahmen,
- Ausschlussmengen,
- Polynomrolle,
- Analyseziel,
- Provenienz,
- Transformationshistorie.

Hurwitz erhält keine DGL und keinen offenen Kreis.

## 10.2 Von Hurwitz erzeugte Bedingungen

Hurwitz erzeugt selbst:

### Koeffizientenbedingungen

Für jeden fachlich erforderlichen Koeffizienten:

\[
a_i>0.
\]

Kennzeichnung:

- `condition_kind=HURWITZ_COEFFICIENT_POSITIVITY`,
- Koeffizientenindex,
- Potenz,
- exakter Koeffizient,
- Bezug zum Polynomfall,
- Quellen-/Rechenwegprovenienz.

### Determinantenbedingungen

Für jede erforderliche Hurwitz-Determinante:

\[
\Delta_j>0.
\]

Kennzeichnung:

- `condition_kind=HURWITZ_DETERMINANT_POSITIVITY`,
- Determinantenordnung \(j\),
- exakter Determinantenausdruck,
- Bezug zur Hurwitz-Matrix,
- Bezug zum Polynomfall,
- Quellen-/Rechenwegprovenienz.

Der gemeinsame Kern erzeugt weder \(a_i>0\) noch \(\Delta_j>0\).

## 10.3 Aufbau des `ParameterConditionProblem`

Pro Gradfall wird gebildet:

```text
assumptions_formula
AND excluded_parameter_sets
AND degree_case.guard_condition
AND hurwitz.coefficient_conditions
AND hurwitz.determinant_conditions
```

Jede Bedingung bleibt einzeln adressierbar. Eine algebraische Vereinfachung darf ihre Herkunft nicht zerstören.

## 10.4 Strikte Stabilitätsgrenzen

Hurwitz übergibt für asymptotische Stabilität ausschließlich strikte Bedingungen:

\[
a_i>0,\qquad \Delta_j>0.
\]

Der Kern:

- erhält die Striktheit,
- schließt Gleichheitsränder aus,
- markiert die Randobjekte als `EXCLUDED`,
- darf nicht eigenmächtig `>=` verwenden,
- darf die Gleichheitsgrenze nicht als stabil klassifizieren.

## 10.5 Gradfälle

Ablauf:

1. Kern erzeugt Gradfälle.
2. Hurwitz analysiert jeden unterstützten positiven Grad getrennt.
3. Nicht unterstützte, konstante oder Nullpolynomfälle bleiben separat.
4. Der Parameterkern löst die Bedingungen fallweise.
5. Die Orchestrierung vereinigt mathematisch kompatible Lösungszweige, erhält aber die Fallprovenienz.
6. Das Hurwitz-Ergebnis zeigt:
   - regulären Gradbereich,
   - Gradabfallbereiche,
   - nicht analysierbare Bereiche,
   - leere Fallzweige.

Ein Gradabfall darf nicht als bloßer ausgeschlossener Rand verschwinden.

## 10.6 Rückgabe an Hurwitz

Der Parameterkern liefert pro Gradfall:

- exakte 1D- oder 2D-Menge,
- Randobjekte,
- Ausschlussmengen,
- Kontrollpunkte,
- Vollständigkeitsstatus,
- reduzierte und ursprüngliche Bedingungen,
- Provenienz jeder aktiven Grenze,
- Diagnosen.

Hurwitz ergänzt:

- Stabilitätsbegriff,
- Hurwitz-Matrix,
- Determinanten,
- fachliche Benennung der Bedingungen,
- optionale numerische Polkontrolle,
- fachliche Aussage „asymptotisch stabil für …“.

## 10.7 Herkunft im Rechenweg

Worked Steps müssen bei einer vereinfachten Endbedingung weiterhin zeigen können:

```text
a_2 > 0
a_1 > 0
a_0 > 0
Δ_2 > 0
        ↓ Schnitt und Redundanzprüfung
reduziertes Bedingungssystem
        ↓ exakte Mengenlösung
Parametergebiet
```

Eine Bedingung darf durch Redundanz aus dem minimalen Endsystem verschwinden, ihre Herkunft bleibt aber im vollständigen Rechenweg sichtbar.

---

# 11. Schnittstellen zu späteren Verbrauchern

## 11.1 Routh

Routh erzeugt:

- Bedingungen der ersten Spalte,
- Vorzeichenbedingungen,
- Definitionsbedingungen für symbolische Divisionen,
- Sonderfall-Guards.

Der Kern löst diese Bedingungen. Routh besitzt weiterhin:

- Routh-Tabellenlogik,
- Vorzeichenwechsel,
- RHP-Polzahl,
- Sonderfallinterpretation.

## 11.2 Nyquist-Parameterfälle

Nyquist erzeugt:

- kritische Verstärkungsgleichungen,
- Bereichsbedingungen,
- Annahmen zum Verstärkungsparameter,
- Ausschlüsse aus offenen Kreisparametern.

Der Kern löst nur die resultierenden Gleichungen und Ungleichungen. Er kennt keine Umschlingungen und keinen kritischen Punkt \(-1\).

## 11.3 Wurzelortskurve

Der Wurzelortskurven-/Zeitforderungsblock erzeugt bereits isolierte Bedingungen wie:

\[
k\ge c_1,\qquad k\le c_2.
\]

Der Kern bildet deren exakten Schnitt. Er leitet die Zeitforderungen nicht her.

## 11.4 Spätere Reglerbedingungen

Reglerblöcke dürfen:

- Leistungsbedingungen,
- Parameterausschlüsse,
- Bereichsbedingungen

als `ParameterConditionProblem` übergeben. Fachliche Bezeichnungen und Einheiten bleiben beim Reglerblock.

---

# 12. Diagnosen und sichere Fehlerausgabe

## 12.1 Polynomdiagnosen

| Code | Bedeutung |
|---|---|
| `INVALID_MAIN_VARIABLE` | unzulässige Hauptvariable |
| `UNDECLARED_SYMBOL` | Symbol weder Parameter noch feste Konstante |
| `TOO_MANY_DECISION_PARAMETERS` | mehr als zwei Parameter |
| `COEFFICIENT_RECONSTRUCTION_MISMATCH` | Ausdruck und Koeffizienten widersprechen sich |
| `ROLE_TARGET_CONFLICT` | Rolle und Analyseziel unvereinbar |
| `MISSING_CANCELLATION_REPORT` | reduzierter Nenner ohne Bericht |
| `PARAMETER_DEPENDENT_LEADING_COEFFICIENT` | Fallzerlegung erforderlich |
| `DEGREE_DROP` | effektiver Grad sinkt |
| `CONSTANT_POLYNOMIAL_CASE` | konstanter Nichtnullfall |
| `ZERO_POLYNOMIAL_CASE` | Nullpolynomfall |
| `UNSAFE_SCALING_BLOCKED` | Skalierung nicht sicher |
| `INEXACT_INPUT_NOT_EXACTLY_SOLVABLE` | nur numerische Eingabe |

## 12.2 Bedingungsdiagnosen

| Code | Bedeutung |
|---|---|
| `MISSING_DENOMINATOR_EXCLUSION` | rationales Atom ohne Definitionsbedingung |
| `INCONSISTENT_ASSUMPTIONS` | Annahmen widersprüchlich |
| `EMPTY_SOLUTION` | reguläres Ergebnis leere Menge |
| `CASE_SPLIT_LIMIT_EXCEEDED` | Fallzahlgrenze überschritten |
| `UNSUPPORTED_TRANSCENDENTAL_CONDITION` | nicht isolierte transzendente Bedingung |
| `UNSUPPORTED_TWO_DIMENSIONAL_FORM` | keine unterstützte Graphform |
| `UNSUPPORTED_TWO_DIMENSIONAL_RATIONAL_BOUNDARY` | rationale 2D-Grenze nicht sicher reduzierbar |
| `PARTIAL_REGION_WITH_RESIDUAL_CONDITIONS` | sicherer Teil plus Restformel |
| `BOUNDARY_ORDER_NOT_PROVEN` | Reihenfolge von Randfunktionen nicht exakt nachgewiesen |
| `NUMERIC_CONTROL_NOT_CERTIFIED` | nur numerische Punktprüfung |
| `EXACT_NUMERIC_RECONSTRUCTION_MISMATCH` | Kontrollprojektion widerspricht exakter Form |

## 12.3 Verhalten

Der Kern gibt bei Fehlern oder Nichtunterstützung zurück:

- Status,
- betroffenen Ausdruck,
- erhaltene Originaldaten,
- bis dahin sichere Transformationen,
- unveränderte Restbedingungen,
- fehlende Voraussetzung,
- empfohlene nächste Aktion.

Er darf nie:

- eine Näherung als exakte Lösung ausgeben,
- ungelöste 2D-Teile verschweigen,
- Ausschlussmengen verlieren,
- Gradfälle zusammenwerfen,
- eine Stichprobe als Flächenbeweis ausgeben,
- fachliche Stabilitätsaussagen erfinden.

---

# 13. Worked-Steps- und LaTeX-Anforderungen

## 13.1 Rechenschrittmodell

Der Kern liefert strukturierte Schritte, keine rein fertigen Textblöcke.

Erforderliche Schrittarten:

1. Eingabe und Rolle.
2. Analyseziel.
3. Originalpolynom.
4. kanonische Polynomform.
5. Koeffizientenliste.
6. Annahmen.
7. Ausschlussmengen.
8. Gradfallzerlegung.
9. sichere Skalierung.
10. ursprüngliche Fachbedingungen.
11. normalisierte Bedingungen.
12. Schnitt/Vereinigung.
13. exakte 1D- oder 2D-Menge.
14. Randklassifikation.
15. Kontrollpunkte.
16. Diagnosen und Restbedingungen.

## 13.2 Kompaktheit

Die Standardansicht soll klausurtauglich und kompakt bleiben:

- identische triviale Normalisierungen zusammenfassen,
- keine internen Bibliotheksschritte ausgeben,
- keine unnötige Vollausgabe jeder algebraischen Zwischenform,
- Gradfälle und Vorzeichenwechsel immer sichtbar machen,
- Nennerausschlüsse nie ausblenden,
- Herkunft fachlicher Bedingungen sichtbar halten.

## 13.3 LaTeX-Pflichten

### Polynom

\[
p(s)=a_ns^n+\dots+a_0.
\]

### Gradfall

\[
a_n>0:\ \deg p=n,
\qquad
a_n=0:\ \deg p<n.
\]

### 1D-Menge

\[
K\in(0,20).
\]

### 2D-Menge

\[
S=
\left\{
(a,K)\in\mathbb R^2
\;\middle|\;
a>-\frac{20}{9},
\;
-\frac{20}{9}a<K<a^2+9a+20
\right\}.
\]

### Ausschluss

\[
D(\theta)\neq0.
\]

### Leere Menge

\[
S=\varnothing.
\]

### Teilweise Lösung

LaTeX muss getrennt zeigen:

- sicher gelösten Anteil,
- verbleibende Restbedingung,
- Grund der Nichtauflösung.

## 13.4 Exakt und numerisch

Verbindliche Reihenfolge:

1. exakter Ausdruck,
2. optional numerische Approximation in eigener Zeile oder Klammer,
3. keine Rundung in weiteren symbolischen Schritten.

## 13.5 Keine falschen Rechenschritte

Der Renderer darf nur Schritte darstellen, die als Transformations- oder Solverobjekte tatsächlich vorliegen. Er darf keine plausible, aber intern nicht ausgeführte Herleitung erfinden.

---

# 14. Gezielte Referenztests

Die Testmenge soll klein bleiben. Priorität haben Verträge, Grenzfälle und offizielle Hurwitz-Integration.

## 14.1 Kern-Domain-Tests

### P0 – parameterfreies Polynom

Eingabe:

\[
p(s)=s^3+4s^2+5s+8.
\]

Erwartung:

- Grad 3,
- Koeffizienten \([1,4,5,8]\),
- ein regulärer Gradfall,
- keine Parameterregion,
- exakte Rekonstruktion.

### P1 – einparametriges offenes Intervall

Bedingungen:

\[
K>0,\qquad 20-K>0.
\]

Erwartung:

\[
K\in(0,20).
\]

Prüft:

- Schnitt,
- strikte Grenzen,
- exakten Innenpunkt.

### P2 – leere Menge

Bedingungen:

\[
k>0,\qquad k<-40.
\]

Erwartung:

\[
\varnothing.
\]

Prüft:

- Widerspruchserkennung,
- `EMPTY`,
- Herkunft der widersprüchlichen Atome.

### P3 – Nennerausschluss in 1D

Bedingung:

\[
\frac{K-1}{K+2}>0,
\qquad K\neq-2.
\]

Erwartung:

\[
K\in(-\infty,-2)\cup(1,\infty).
\]

Prüft:

- Vorzeichentabelle,
- Nennerausschluss,
- Intervallvereinigung.

### P4 – Gradabfall

Polynom:

\[
p(s;k)=ks^2+s-10-\frac{k}{4}.
\]

Erwartung:

- \(k>0\): Grad 2, positive Orientierung,
- \(k<0\): Grad 2 nach Multiplikation mit \(-1\),
- \(k=0\): Grad 1 mit
  \[
  p(s)=s-10.
  \]

Prüft:

- Vorzeichenfall,
- sichere Skalierung,
- Gradreduktion,
- Fallprovenienz.

### P5 – zweiparametrige lineare Grenze

Bedingungen:

\[
a>-\frac{20}{9},
\qquad
K>-\frac{20}{9}a.
\]

Erwartung:

- offene vertikale Grenze,
- offene lineare Untergrenze,
- exakte 2D-Zelle,
- zertifizierter Innenpunkt.

### P6 – klausurrelevantes Parabelgebiet

Bedingungen:

\[
a>-\frac{20}{9},
\qquad
-\frac{20}{9}a<K<a^2+9a+20.
\]

Erwartung:

- exakte 2D-Zelle beziehungsweise notwendige \(x\)-Teilzellen,
- ausgeschlossene Randgerade,
- ausgeschlossene Randparabel,
- exakte Schnittpunkte,
- keine Rasterlösung.

### P7 – nichtstrikte Grenze

Bedingungen:

\[
k\ge1,\qquad k<2.
\]

Erwartung:

\[
k\in[1,2).
\]

Prüft Randinklusion.

### P8 – teilweise nicht unterstützter 2D-Fall

Bedingung:

\[
x^2+xy+y^2<1.
\]

Erwartung:

- keine erfundene Zellzerlegung,
- `PARTIALLY_SOLVED_SAFE` oder `UNSUPPORTED`,
- Originalbedingung als Restformel,
- Diagnose `UNSUPPORTED_TWO_DIMENSIONAL_FORM`.

### Rationale 2D-Grenze

Kein vollständiger Lösungstest im ersten Paket, da sie nicht zum zwingenden Hurwitz-MVP gehört.

Optionaler Diagnosevertrag:

\[
T_N>\frac{K_R}{1+3K_R}
\]

ohne bekannte Nennerzeichenlage muss die Bedingung vollständig erhalten und als nicht vollständig gelöst markiert werden.

---

## 14.2 Hurwitz-Vertragstests

### H1 – parameterfreier Verbraucher

- Kern liefert Grad-3-Fall.
- Hurwitz erzeugt Bedingungen und Determinanten.
- Kern löst keine Parameter, erhält aber Bedingungen und Provenienz.
- Presenter zeigt Matrix, Determinanten und Ergebnis.

### H2 – Einparameterfall

Polynom:

\[
p(s)=s^3+4s^2+5s+K_P.
\]

Hurwitz erzeugt:

\[
K_P>0,\qquad 20-K_P>0.
\]

Kern erwartet:

\[
0<K_P<20.
\]

Prüft vollständige Hin- und Rückschnittstelle.

### H3 – SS2025-Parabelgebiet

Polynom:

\[
p(s)=s^3+(9+a)s^2+(20+9a)s+(20a+9K).
\]

Hurwitz erzeugt die fachlichen Bedingungen. Der Kern muss das exakte Gebiet zurückgeben, ohne selbst Determinanten zu erzeugen.

### H4 – Rollen- und Kürzungsvertrag WS25/26

- reduzierter Nenner mit explizitem Kürzungsprotokoll wird für `EXTERNAL_BIBO` akzeptiert,
- rohes charakteristisches Polynom bleibt separat,
- keine stillschweigende Gleichsetzung,
- inkompatibles Analyseziel wird abgelehnt.

### H5 – strikter Rand

Für jede Hurwitz-Gleichheitsgrenze gilt:

- Rand nicht enthalten,
- Kontrollpunkt auf dem Rand erfüllt die strikte Bedingung nicht,
- Presenter verwendet offene Menge.

---

## 14.3 Presenter-/LaTeX-Smoke-Tests

Nur zwei zwingende Smoke-Tests:

1. Einparameterfall \(0<K_P<20\):
   - Originalbedingungen,
   - reduzierte Bedingungen,
   - offenes Intervall,
   - exakter Kontrollpunkt.

2. SS2025-Gebiet:
   - exakte Mengenschreibweise,
   - Randgerade und Randparabel,
   - beide als ausgeschlossen,
   - numerische Projektion getrennt.

Optional dritter Test:

- Gradabfall mit sichtbarer Fallzerlegung.

---

## 14.4 Bewusst nicht notwendige Volltests

Im ersten Paket nicht erforderlich:

- allgemeine Routh-Sonderfälle,
- Nyquist-Umschlingungen,
- Wurzelortskurvenlogik,
- beliebige Polynomgrade,
- allgemeine 2D-rationale Gebiete,
- allgemeine implizite Kurven,
- 3D-Darstellung,
- hunderte zufällige numerische Varianten,
- Tests interner SymPy-Funktionen,
- numerische Rastertests,
- vollständige Testmatrix aller möglichen Relationskombinationen,
- mehrere nahezu identische GUI-End-to-End-Tests.

---

# 15. Codex-Aufwand

## 15.1 Relative Aufwandstreiber

| Bestandteil | Aufwand | Hauptrisiko |
|---|---:|---|
| Verträge und Provenienz | mittel | zu viele oder zu schwache Objekte |
| Polynomrekonstruktion | niedrig bis mittel | Ausdruck/Koeffizienten-Divergenz |
| Gradfalllogik | mittel | Fallabdeckung und sichere Skalierung |
| Condition-AST | mittel | Verlust von Herkunft und Striktheit |
| exakter 1D-Solver | mittel | rationale Vorzeichenfälle |
| begrenzter 2D-Solver | mittel bis hoch | Randordnung und Zellvollständigkeit |
| Hurwitz-Integration | mittel | Fachlogik darf nicht in Kern sickern |
| Worked Steps/LaTeX | mittel | nur reale Schritte darstellen |
| GUI-Anbindung | mittel | vorhandene Infrastruktur korrekt nutzen |
| Referenztests | mittel | Quellenfehler und Rollenunterschiede |

## 15.2 Vergleich zum isolierten Kern

Ein isolierter Kern-PR spart keine wesentliche Mathematik. Er verschiebt nur:

- Hurwitz-Integration,
- reale Vertragstests,
- GUI,
- Presenter,
- Fehlerkorrekturen

in einen zweiten Auftrag. Dadurch steigt der Gesamtverbrauch.

## 15.3 Erwartete Größenordnung

Gesamtaufwand des empfohlenen Pakets:

\[
\boxed{\text{mittel bis hoch}}
\]

Der Aufwand ist gerechtfertigt, weil:

- Hurwitz unmittelbar sichtbar wird,
- die beiden zweiparametrigen Klausurtypen abgedeckt werden,
- der Kern danach von Routh, Nyquist und Wurzelortskurve konsumiert werden kann,
- spätere Verbraucher keine neue Mengenrepräsentation benötigen.

Der 2D-Zellkern ist der teuerste Teil. Er muss bewusst auf lineare und quadratische Graphgrenzen begrenzt bleiben.

---

# 16. Risiken und Gegenmaßnahmen

## 16.1 Schleichender CAS-Ausbau

**Risiko:** Jede neue Bedingung führt zu einer Erweiterung des allgemeinen Solvers.

**Gegenmaßnahme:** Unterstützte Normalformen explizit prüfen. Alles andere liefert sichere Restbedingungen.

## 16.2 Hurwitz-Kopplung im gemeinsamen Kern

**Risiko:** Allgemeine Objekte heißen `HurwitzRegion`, `StabilityBoundary` oder erzeugen Determinanten.

**Gegenmaßnahme:** Nur neutrale Begriffe im Kern. Fachlabels liegen im Verbraucher.

## 16.3 Rohes und reduziertes Polynom verwechselt

**Risiko:** interne und E/A-Stabilität werden vermischt.

**Gegenmaßnahme:** Rollen-/Analyseziel-Matrix, Pflicht-Kürzungsbericht, harte Vertragsfehler.

## 16.4 Gradabfall verloren

**Risiko:** Division durch Leitkoeffizienten entfernt relevante Parameterfälle.

**Gegenmaßnahme:** Gradfallzerlegung vor jeder Normierung, wiederholte Reduktion, Fallprovenienz.

## 16.5 Ausschlussmenge verloren

**Risiko:** Kreuzmultiplikation oder Kürzung schließt Nennernullen versehentlich ein.

**Gegenmaßnahme:** Ausschlüsse als atomare Bedingungen erster Klasse.

## 16.6 Strikte Grenze eingeschlossen

**Risiko:** grafische oder numerische Darstellung verwendet geschlossene Ränder.

**Gegenmaßnahme:** Striktheit im Atom, im Randobjekt, in der Menge und im Renderer speichern.

## 16.7 Testpunkt als Beweis

**Risiko:** ein positiver Punkt wird als Beweis für eine gesamte Zelle behandelt.

**Gegenmaßnahme:** Zellen entstehen nur aus exakter Randpartitionierung. Kontrollpunkte sind zusätzliche Verifikation.

## 16.8 Teilweise Lösung wirkt vollständig

**Risiko:** GUI zeigt sicheren Teil ohne Restbedingung.

**Gegenmaßnahme:** `PARTIALLY_SOLVED_SAFE` verlangt sichtbare Restformel und darf nicht als Erfolg mit vollständigem Gebiet erscheinen.

## 16.9 Ausdrucksexplosion

**Risiko:** Grad-, Nenner- und OR-Fälle vervielfachen sich.

**Gegenmaßnahme:** Fallzahlgrenze, frühe Widerspruchserkennung, keine allgemeine Quantorenelimination.

## 16.10 Inexakte Eingaben

**Risiko:** gerundete Koeffizienten erzeugen scheinbar exakte Grenzen.

**Gegenmaßnahme:** exakte Eingabe priorisieren; ansonsten Diagnose und kein `SOLVED_EXACT`.

## 16.11 Doppelte bestehende Infrastruktur

**Risiko:** Parser, Polynomdarstellung oder LaTeX werden neu implementiert.

**Gegenmaßnahme:** vor Änderung bestehende Domänenobjekte und Renderer inventarisieren und adaptieren.

---

# 17. Empfohlene Implementierungsreihenfolge

Die Reihenfolge gilt innerhalb **eines gemeinsamen vertikalen PRs**. Sie ist keine Aufforderung zu getrennten Infrastrukturbranches.

## Schritt 1 – Repository- und Vertragseinpassung

- bestehende Polynom-, Symbolik-, Diagnose-, Worked-Steps- und LaTeX-Objekte identifizieren,
- neue Verträge auf vorhandene Typen abbilden,
- Duplikate vermeiden,
- Integrationspunkte im Stabilitätsarbeitsbereich festlegen.

## Schritt 2 – neutrale Domänenobjekte

- Provenienz,
- Transformationshistorie,
- Polynomrollen,
- Analyseziele,
- Bedingungen,
- 1D-/2D-Ergebnisobjekte,
- Diagnosen.

Noch keine Fachlogik.

## Schritt 3 – Polynomkanonisierung

- Rekonstruktion,
- Nullkoeffizienten,
- Rollenvalidierung,
- Gradfälle,
- sichere Skalierung,
- Null-/Konstantfälle.

Abnahme mit P0 und P4.

## Schritt 4 – Condition-Normalisierung und 1D-Solver

- atomare Relationen,
- Nennerausschlüsse,
- AND/OR,
- Vorzeichenzellen,
- Intervalloperationen,
- leere Menge.

Abnahme mit P1, P2, P3 und P7.

## Schritt 5 – begrenzter 2D-Solver

- lineare/quadratische Graphgrenzen,
- Schnittpunkte,
- \(x\)-Partitionierung,
- aktive Grenzen,
- Zellen,
- Randobjekte,
- Kontrollpunkte,
- sichere Teilresultate.

Abnahme mit P5, P6 und P8.

## Schritt 6 – Hurwitz als erster Verbraucher

- Hurwitz Grad 2 bis 4,
- Erzeugung der Koeffizienten- und Determinantenbedingungen,
- Aufbau des `ParameterConditionProblem`,
- fallweise Lösung,
- fachliche Rückinterpretation.

Abnahme mit H1 bis H5.

## Schritt 7 – Worked Steps, LaTeX und sichtbare GUI

- kompakte Rechenwege,
- exakte Mengen,
- Ränder,
- Diagnosen,
- Kontrollwerte,
- offizieller Referenzfall in der App.

Keine parallele zweite GUI.

## Schritt 8 – gezielte Regression und Paketabnahme

- Kern-Domain-Tests,
- Hurwitz-Vertragstests,
- zwei Presenter-Smoke-Tests,
- offizielle SS2025- und WS25/26-Referenzfälle,
- vollständiger Testsatz einmal nach den letzten Änderungen.

## Schritt 9 – spätere Extraktion nur bei Bedarf

Nach dem PR sind die Kernmodule bereits intern getrennt. Eine weitere öffentliche Paketextraktion oder größere API-Verallgemeinerung erfolgt erst, wenn Routh, Nyquist oder Wurzelortskurve tatsächlich integriert werden.

---

# 18. Verbindliche Paketabnahme

Das Paket ist abgeschlossen, wenn:

1. Hurwitz als sichtbarer Verbraucher funktioniert.
2. Der gemeinsame Kern keine Hurwitz-Determinanten erzeugt.
3. alle Polynomrollen und Analyseziele erhalten bleiben.
4. rohe und reduzierte Polynome nicht verwechselt werden.
5. Gradabfälle separat zurückgegeben werden.
6. 1D-Bedingungen innerhalb des Vertrags vollständig exakt gelöst werden.
7. die belegten 2D-Hurwitz-Gebiete exakt dargestellt werden.
8. strikte Grenzen ausgeschlossen bleiben.
9. Ausschlussmengen erhalten bleiben.
10. Testpunkte nur als Kontrolle bezeichnet werden.
11. teilweise gelöste Fälle ihre Restbedingungen zeigen.
12. Worked Steps den tatsächlichen Rechenweg abbilden.
13. LaTeX exakte und numerische Werte trennt.
14. die kleinen priorisierten Tests bestehen.
15. keine vorhandene Parser-, Rationalfunktions-, Plot- oder LaTeX-Infrastruktur dupliziert wurde.

---

# 19. Endentscheidung

Der kleinste wirtschaftlich sinnvolle gemeinsame Kern ist **nicht** ein isolierter Infrastrukturbranch und **nicht** ein später aus Hurwitz herauszureißender Hilfscode.

Er ist ein intern sauber getrenntes Teilpaket innerhalb eines gemeinsamen vertikalen Hurwitz-PRs:

\[
\boxed{
\text{kleiner gemeinsamer Polynom-/Parameterkern}
+
\text{Hurwitz als erster Verbraucher}
}
\]

Der erste 2D-Umfang bleibt hart begrenzt auf die exakten, graphförmigen linearen und quadratischen Gebiete der belegten Hurwitz-Aufgaben. Rationale 2D-Grenzen ohne bereits bewiesenes Nennerzeichen, allgemeine implizite Kurven und allgemeine Quantorenelimination bleiben ausdrücklich außerhalb des Pakets.
