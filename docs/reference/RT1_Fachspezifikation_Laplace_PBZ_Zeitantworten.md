# KlausurBotPro – Fachspezifikation

## Laplace-Transformation, Partialbruchzerlegung, inverse Laplace und Zeitantworten

**Status:** Fachspezifikation, keine Implementierung und kein Codex-Prompt  
**Quellenstand:** Sommersemester 2026  
**Ziel:** Ein nachgelagerter Chat soll daraus einen kurzen, eindeutigen Programmierauftrag erzeugen können.

---

# 1. Verbindliche Quellenbasis

## 1.1 Quellenhierarchie

1. `skript.pdf`
2. `Regelungstechnik_Übung_Aufg-u-Lösungen.pdf`
3. `Regelungstechnik_Tutorium_komplett.pdf`
4. `RT_Klausur_SS2025-komplett.pdf`
5. `RT-Klausur_WS_25_26-komplett.pdf`
6. `Tabelle_Standardglieder.pdf`
7. `RT1_Rechenwege_Master(12).md` nur als Entwicklungsreferenz

## 1.2 Zentrale Fundstellen

| Inhalt | Primärfundstelle |
|---|---|
| Definition Laplace-Transformation | `skript.pdf`, PDF-S. 51, Definition 3.1 |
| Definition inverse Laplace-Transformation | `skript.pdf`, PDF-S. 52, Definition 3.3 |
| Ableitungs-, Integrations-, Dämpfungs-, Verschiebungs- und Faltungssatz | `skript.pdf`, PDF-S. 53–54, Tabelle 3.1 |
| Laplace-Äquivalenztabelle | `skript.pdf`, PDF-S. 54–55, Tabelle 3.2 |
| Anfangswertanteil und erzwungener Anteil im Bildbereich | `skript.pdf`, PDF-S. 56, Gleichung (3.3) |
| Übertragungsfunktion bei verschwindendem Anfangszustand | `skript.pdf`, PDF-S. 56–57, Definition 3.4 und Theorem 3.5 |
| Partialbruchzerlegung, reelle und komplexe Pole, Mehrfachheiten | `skript.pdf`, PDF-S. 57–58, Theorem 3.7 |
| Nicht kürzen gemeinsamer Faktoren ohne Warnung | `skript.pdf`, PDF-S. 58, Bemerkung 3.8 |
| Echte, gleichgradige und nicht realisierbare rationale Funktionen | `skript.pdf`, PDF-S. 59–60, Theorem 3.13 und Korollar 3.14 |
| E/A-Stabilität über Pole | `skript.pdf`, PDF-S. 123, Theorem 5.12 |
| Direkte/inverse Laplace-Aufgaben | `Regelungstechnik_Tutorium_komplett.pdf`, PDF-S. 12–13, Tutorium 03, Aufgabe 2 |
| Bildbereich und Sprungantworten | `Regelungstechnik_Tutorium_komplett.pdf`, PDF-S. 13–14, Tutorium 03, Aufgaben 3–4 |
| DGL mit Anfangsbedingungen, PBZ und Rücktransformation | `Regelungstechnik_Übung_Aufg-u-Lösungen.pdf`, PDF-S. 47 und 50–51, Übung 03, Aufgabe 1 |
| Übertragungsfunktion Feder-Masse-Dämpfer | ebenda, PDF-S. 47–48 und 52, Aufgabe 2 |
| Parameter-Sprungantwort eines Systems 2. Ordnung | ebenda, PDF-S. 48 und 53–55, Aufgabe 3 |
| Endwertsatz im Regelkreis | ebenda, PDF-S. 104–105, Aufgaben 3–4 |
| Klausuraufgabe: DGL → Übertragungsfunktion | `RT_Klausur_SS2025-komplett.pdf`, PDF-S. 4; Musterlösung PDF-S. 46, Aufgabe 1d |
| Theoretische Laplace-/Übertragungsfunktionsfragen | `RT-Klausur_WS_25_26-komplett.pdf`, PDF-S. 15; Musterlösung PDF-S. 43, Aufgabe 1a I |
| Standardglieder und Zeitverhalten | `Tabelle_Standardglieder.pdf`, PDF-S. 1–3 |

---

# 2. Quellenbefund und Klausurrelevanz

## 2.1 Tatsächlich vorkommende Aufgabentypen

| Aufgabentyp | Offizielle Übung/Tutorium | Klausur | Relevanz |
|---|---:|---:|---|
| Direkte Tabellen-Laplace-Transformation | ja | nur Theorie indirekt | mittel |
| Direkte Transformation mit Exponentialfaktor | ja | indirekt | mittel |
| Direkte Transformation mit trigonometrischer Umformung | ja | nicht direkt | niedrig bis mittel |
| Inverse Laplace aus Tabellenform | ja | indirekt | mittel |
| DGL mit Anfangsbedingungen transformieren | ja, ausführlich | prinzipiell klausurnah | hoch |
| DGL bei Nullanfangsbedingungen → Übertragungsfunktion | ja | SS2025, 5 Punkte | sehr hoch |
| Partialbruchzerlegung mit einfachen reellen Polen | ja | als notwendiges Werkzeug möglich | hoch |
| Partialbruchzerlegung mit mehrfachem reellem Pol | ja, Übung 03 A1 | nicht explizit isoliert | hoch |
| Komplex konjugierte Pole / quadratischer Faktor | ja | indirekt über PT2/Stabilität | hoch |
| Sprungantwort im Bildbereich | ja | wiederkehrend in Regelkreisaufgaben | sehr hoch |
| Sprungantwort im Zeitbereich | ja, ausführlich | klausurnah | sehr hoch |
| Allgemeine Standardanregung, z. B. Exponentialsignal | ja | möglich | hoch |
| Impulsantwort | nur direkt aus Skript ableitbar | nicht direkt | Erweiterung |
| Faltung | im Skript begründet, keine Rechenaufgabe gefunden | nicht direkt | Erweiterung |
| Endwertsatz | offizielle Übung | indirekt sehr relevant | hoch |
| Anfangswertsatz als benannter Satz | nicht gefunden | nicht gefunden | nicht als Pflichtfeature |
| Polynomdivision bei unechter rationaler Funktion | nicht als Aufgabe gefunden; Realisierbarkeit behandelt | nicht direkt | Fehler-/Grenzfall |
| Zeitverschobene/stückweise Signale | Satz im Skript, keine Rechenaufgabe gefunden | nicht direkt | spätere Erweiterung |

## 2.2 Harte Schlussfolgerung

Der punkteträchtigste Kern ist nicht das bloße Nachschlagen einzelner Laplace-Paare. Der Kern ist die Kette

\[
\text{DGL/Übertragungsfunktion}
\rightarrow Y(s)
\rightarrow \text{Nenner klassifizieren}
\rightarrow \text{Partialbruchzerlegung}
\rightarrow y(t)
\rightarrow \text{Kontrollen}.
\]

Dieser Ablauf ist zeitaufwendig, vorzeichenanfällig und klar automatisierbar. Er gehört vollständig in das erste produktive Paket.

---

# 3. Fachliche Grundkonventionen

## 3.1 Notation

Zeitbereich:

\[
f(t),\quad u(t),\quad y(t),\qquad t\ge 0.
\]

Bildbereich:

\[
F(s)=\mathcal L\{f(t)\},\quad U(s)=\mathcal L\{u(t)\},\quad Y(s)=\mathcal L\{y(t)\}.
\]

Komplexe Variable:

\[
s=\sigma+j\omega.
\]

Übertragungsfunktion nur bei verschwindendem Anfangszustand:

\[
G(s)=\frac{Y(s)}{U(s)},\qquad x_0=0.
\]

Bei nicht verschwindenden Anfangswerten gilt nicht einfach nur \(Y=GU\). Die Anfangswerte erzeugen einen zusätzlichen freien Anteil.

## 3.2 Exaktheit

- Symbolische Werte werden exakt gehalten: ganze Zahlen, rationale Zahlen, Wurzeln, \(\pi\), Parameter.
- Dezimalzahlen werden intern möglichst in rationale Zahlen umgewandelt, sofern die Eingabe eindeutig ist, z. B. \(0{,}1=1/10\).
- Numerische Näherungen sind separate Kontrollwerte und ersetzen nie das exakte Ergebnis.
- Komplexe Pole werden paarweise und reellwertig ausgegeben.

## 3.3 Kausalität und Heaviside-Faktor

Die Vorlesung verwendet die einseitige Laplace-Transformation für \(t\ge0\). Zeitfunktionen sind formal kausal. In der standardmäßigen Klausurausgabe darf der Faktor \(\eta(t)\) weggelassen werden, wenn die Aufgabe klar auf \(t\ge0\) beschränkt ist. Bei Zeitverschiebungen muss er angezeigt werden.

---

# 4. Gemeinsames Domänenmodell

## 4.1 Eingabewerte

### `SymbolicExpression`

- exakter Ausdruck
- zugelassene Variablen: mindestens \(s,t\), frei benannte reelle Parameter
- Annahmen je Parameter: `real`, optional `positive`, `nonzero`
- keine beliebige Codeausführung

### `PolynomialData`

- Variable, standardmäßig \(s\)
- Koeffizienten in absteigender Potenz
- exakter Grad
- Faktorisierung über \(\mathbb R\)
- optional bekannte Faktoren und Multiplizitäten

### `InitialConditionSet`

Abbildung

\[
k\mapsto y^{(k)}(0^+),\qquad k=0,1,\dots,n-1.
\]

Fehlende Anfangswerte dürfen nicht stillschweigend als null behandelt werden, außer der Nutzer aktiviert ausdrücklich „alle nicht angegebenen Anfangswerte = 0“.

### `InputSignal`

Unterstützte Varianten:

- `step(amplitude)`
- `impulse(amplitude)`
- `exponential(amplitude, exponent)`
- `polynomial(coefficients)`
- `sinus(amplitude, omega, phase=0)`
- `cosinus(amplitude, omega, phase=0)`
- `laplace_expression(U(s))`
- später: `time_shift(signal, delay)` und `piecewise`

### `ResponseRequest`

- `laplace_transform`
- `inverse_laplace`
- `solve_ode`
- `transfer_function`
- `output_laplace`
- `step_response`
- `impulse_response`
- `general_response`
- `final_value`

## 4.2 Ergebniswerte

### `PoleRecord`

- exakter Pol
- numerischer Kontrollwert
- Multiplizität
- Typ: `real` oder `complex_pair`
- Realteil, Imaginärteil
- Stabilitätsklasse: links, imaginäre Achse, rechts

### `PartialFractionTerm`

- Nennerfaktor
- Potenz
- Zählerpolynom
- Koeffizienten
- zugehöriges Zeitbereichsmuster

### `SolutionStep`

- fortlaufende Nummer
- kurzer Titel
- exakte mathematische Aussage
- fertige LaTeX-Zeichenkette
- optionale Quellenreferenz
- Warnungen

### `VerificationReport`

- Rücktransformation/Transformation stimmt
- Anfangsbedingungen erfüllt
- DGL-Residuum ist null
- \(Y=GU\) stimmt
- Endwert konsistent
- Polstabilität
- Einheitenkontrolle, soweit Einheiten vorhanden
- numerische Stichprobe

### `LaplaceSolution`

Enthält unverändert:

- Rohinput
- normalisierten Input
- unreduzierte rationale Darstellung
- reduzierte Darstellung
- Kürzungsbericht
- Polynomdivision
- Pole/Faktoren
- Partialbruchzerlegung
- Zeitfunktion
- nummerierte Schritte
- Verifikationsbericht
- Warn-/Fehlercodes
- LaTeX-Blöcke

---

# 5. Gemeinsame Application-Orchestrierung

## 5.1 Minimaler Ablauf

1. **Parse:** sichere Umwandlung der GUI-Eingabe in Domänenwerte.
2. **Validate:** Variablen, Grade, Anfangswerte, Parameterannahmen und Definitionsbereiche prüfen.
3. **Normalize:** Ausdrücke exakt zusammenfassen, Nenner monisch bzw. für Tabellenform normieren.
4. **Classify:** Aufgabentyp, Rationalität, Grade, Pole und Multiplizitäten bestimmen.
5. **Plan:** passenden klausurtauglichen Lösungsweg auswählen.
6. **Compute:** Transformation, Gleichungsauflösung, Polynomdivision, PBZ oder Rücktransformation durchführen.
7. **Verify:** unabhängige symbolische und gegebenenfalls numerische Kontrollen durchführen.
8. **Present:** aus Domänenergebnissen nummerierte Rechenschritte und fertiges LaTeX erzeugen.
9. **Render:** UI zeigt nur fertige View-Modelle an.

## 5.2 Verbot im UI-Renderer

Im Renderer dürfen keinesfalls stattfinden:

- Parsen mathematischer Eingaben
- Vereinfachen, Expandieren oder Faktorisieren
- Gradbestimmung
- Polynomdivision
- Nullstellen- oder Polberechnung
- Multiplizitätsbestimmung
- Partialbruchzerlegung
- Lösen linearer Gleichungssysteme für PBZ-Koeffizienten
- Laplace- oder inverse Laplace-Transformation
- Einsetzen von Anfangsbedingungen
- Stabilitätsbewertung
- Grenzwertberechnung
- Rundung oder Auswahl numerischer Präzision
- Generierung fachlicher Warnungen
- Entscheidung, welcher Rechenweg klausurtauglich ist

Der Renderer erhält ausschließlich fertige Strings, strukturierte Schritte, Statuswerte und bereits formatierte LaTeX-Blöcke.

---

# 6. Aufgabentyp A – Direkte Laplace-Transformation

## Fundstellen

- `skript.pdf`, PDF-S. 51–55
- `Regelungstechnik_Tutorium_komplett.pdf`, PDF-S. 12–13, Aufgabe 2a–e

## Voraussetzungen

- kausale, stückweise hinreichend reguläre und exponentiell beschränkte Zeitfunktion
- unterstützte Grundbausteine oder daraus ableitbare Kombinationen

## Eingabe

- \(f(t)\)
- Variable \(t\)
- Parameterannahmen, z. B. \(\omega\in\mathbb R\)

## Ausgabe

- \(F(s)=\mathcal L\{f(t)\}\)
- verwendete Tabellenpaare und Sätze
- Existenz-/Definitionshinweis, soweit nötig
- exakte und optionale numerische Kontrollwerte

## Klausurtauglicher Rechenweg

1. Konstanten ausklammern.
2. Summe in Summanden zerlegen.
3. Trigonometrische Potenzen/Produkte zuerst umformen.
4. Grundpaar aus Tabelle 3.2 identifizieren.
5. Dämpfungssatz korrekt anwenden:
   \[
   e^{at}f(t)\longleftrightarrow F(s-a).
   \]
6. Zeitverschiebung nur bei \(f(t-a)\eta(t-a)\) anwenden:
   \[
   f(t-a)\eta(t-a)\longleftrightarrow e^{-as}F(s).
   \]
7. Ergebnis algebraisch vereinfachen, aber Tabellenstruktur sichtbar lassen.

## Kernformeln

\[
1\longleftrightarrow\frac1s,
\qquad
 t^n\longleftrightarrow\frac{n!}{s^{n+1}},
\]

\[
e^{-at}\longleftrightarrow\frac1{s+a},
\qquad
 t^ne^{-at}\longleftrightarrow\frac{n!}{(s+a)^{n+1}},
\]

\[
\sin(\omega t)\longleftrightarrow\frac{\omega}{s^2+\omega^2},
\qquad
\cos(\omega t)\longleftrightarrow\frac{s}{s^2+\omega^2}.
\]

## Sonderfälle

- \(\sin^2t=(1-\cos2t)/2\)
- verschobener Sinus/Kosinus durch Exponentialfaktor
- verzögerte Signale erst in Erweiterung
- nicht unterstützte Spezialfunktionen führen nicht zu einem erfundenen Tabellenpaar

## Typische Fehler

- \(n!\) vergessen
- bei \(e^{-at}\) fälschlich \(s-a\) verwenden
- Dämpfungssatz als Zeitverschiebung bezeichnen
- Sinus und Kosinus im Zähler verwechseln
- \(\sin^2t\) ohne Identität direkt „transformieren“

## Plausibilitätsprüfungen

- Dimension des Nenners steigt bei Ableitungs-/Potenzstruktur plausibel
- Rücktransformation des Ergebnisses ergibt den Input
- numerische Integralprüfung für einen zulässigen reellen Wert \(s=s_0\)

## GUI-Eingaben

- Formelzeile `f(t)`
- Schalter „Rechenweg anzeigen“
- optional Parameterannahmen
- optional numerische Prüfstelle \(s_0\)

## Gewünschte LaTeX-Ausgabe

\[
\begin{aligned}
f(t)&=\dots\\
F(s)&=\mathcal L\{f(t)\}\\
&=\dots\\
&=\boxed{\dots}
\end{aligned}
\]

## Benötigte Domainwerte

`SymbolicExpression`, `SolutionStep`, `VerificationReport`.

## Application-Orchestrierung

`parse_time_expression → classify_laplace_pattern → apply_transform_rules → verify_inverse → build_steps`.

---

# 7. Aufgabentyp B – Inverse Laplace-Transformation ohne PBZ

## Fundstellen

- `skript.pdf`, PDF-S. 52 und 54–55
- `Regelungstechnik_Tutorium_komplett.pdf`, PDF-S. 12–13, Aufgabe 2f–i

## Voraussetzungen

- Bildfunktion entspricht direkt oder nach einfacher Normierung einem Tabellenpaar

## Eingabe

- \(F(s)\)
- Variable \(s\)
- gewünschte Zeitvariable \(t\)

## Ausgabe

- \(f(t)=\mathcal L^{-1}\{F(s)\}\)
- Tabellenabgleich
- Normierungsfaktoren sichtbar

## Klausurtauglicher Rechenweg

1. Ausdruck auf Standardform bringen.
2. Quadrate vervollständigen, falls nötig.
3. Fehlenden Zählerfaktor ergänzen und außerhalb kompensieren.
4. Tabellenpaar identifizieren.
5. Dämpfungssatz rückwärts anwenden.
6. Ergebnis angeben und durch Vorwärtstransformation prüfen.

## Sonderfälle

- \(1/(s^2+\omega^2)=\frac1\omega\cdot\omega/(s^2+\omega^2)\)
- \((s-a)/((s-a)^2+\omega^2)\)
- \(1/(s-a)^n\) erzeugt Potenz mal Exponentialfunktion

## Typische Fehler

- Faktor \(1/\omega\) vergessen
- Vorzeichen der Verschiebung vertauschen
- \((s-a)^2\) nicht als Ganzes erkennen
- bei \(1/s^4\) \(t^3\) statt \(t^3/6\) ausgeben

## Plausibilitätsprüfungen

- Vorwärtstransformation exakt gleich Input
- reelle Bildfunktion mit reellen Koeffizienten muss reelle Zeitfunktion ergeben

## GUI-Eingaben

- Formelzeile `F(s)`
- optional „Tabellenweg erzwingen“

## Gewünschte LaTeX-Ausgabe

\[
\begin{aligned}
F(s)&=\dots\\
&=c\,F_0(s-a)\\
f(t)&=\boxed{c\,e^{at}f_0(t)}.
\end{aligned}
\]

## Domainwerte und Orchestrierung

`SymbolicExpression → normalize_inverse_pattern → lookup_pair → verify_forward → build_steps`.

---

# 8. Aufgabentyp C – DGL mit Anfangsbedingungen lösen

## Fundstellen

- `skript.pdf`, PDF-S. 53, Ableitungssatz
- `skript.pdf`, PDF-S. 56, freier und erzwungener Anteil
- `Regelungstechnik_Übung_Aufg-u-Lösungen.pdf`, PDF-S. 47 und 50–51, Übung 03 Aufgabe 1

## Voraussetzungen

- lineare DGL mit konstanten Koeffizienten
- hinreichend viele Anfangswerte
- transformierbarer Eingang

## Eingabe

- linke und rechte DGL-Seite oder Koeffizientenform
- Ordnung \(n\)
- Anfangswerte \(y^{(k)}(0^+)\), \(k=0,\dots,n-1\)
- Eingang \(u(t)\) oder \(U(s)\)

## Ausgabe

- transformierte DGL
- aufgelöstes \(Y(s)\)
- freie und erzwungene Bestandteile, sofern trennbar
- PBZ
- exakte Zeitlösung \(y(t)\)
- vollständige Verifikation

## Klausurtauglicher Rechenweg

1. DGL in geordnete Form bringen.
2. Jeden Ableitungsterm einzeln transformieren:
   \[
   \mathcal L\{y^{(n)}\}
   =s^nY(s)-\sum_{k=1}^{n}s^{n-k}y^{(k-1)}(0^+).
   \]
3. Anfangswerte sichtbar einsetzen.
4. Eingang transformieren.
5. alle \(Y(s)\)-Terme sammeln.
6. nach \(Y(s)\) auflösen.
7. Rationalität und Grade prüfen.
8. Nenner faktorisieren und PBZ durchführen.
9. jeden Summanden rücktransformieren.
10. Anfangswerte und DGL durch Einsetzen prüfen.

## Sonderfälle

- fehlende Anfangswerte: harter Validierungsfehler oder explizite Nullannahme
- resonante Anregung: erhöhte Polmultiplizität nach Zusammenführen
- nicht rationale Eingänge: nur unterstützte Transformationsregeln
- Parameter können Poltyp abhängig von Diskriminante ändern

## Typische Fehler

- bei \(y''\) den Term \(-\dot y(0)\) vergessen
- Anfangswert mit falscher \(s\)-Potenz versehen
- \(Y(s)\)-Terme falsch sammeln
- die Übertragungsfunktion mit der Gesamtlösung verwechseln
- Anfangsbedingungen nachträglich nicht kontrollieren

## Plausibilitätsprüfungen

- \(y^{(k)}(0^+)\) stimmt für alle vorgegebenen \(k\)
- DGL-Residuum
  \[
  R(t)=\sum a_ky^{(k)}(t)-u(t)
  \]
  vereinfacht sich zu null
- Vorwärtstransformation von \(y(t)\) stimmt mit \(Y(s)\)
- numerische Stichprobe des Residuums

## GUI-Eingaben

- DGL-Editor oder Koeffizientenfelder
- Tabelle der Anfangswerte
- Eingangssignal-Editor
- Schalter „freie/erzwungene Antwort trennen“

## Gewünschte LaTeX-Ausgabe

Muss jeden Anfangswertterm zeigen; keine Black-Box-Zeile „Laplace anwenden“.

## Domainwerte und Orchestrierung

`LinearOdeData`, `InitialConditionSet`, `InputSignal`, `LaplaceSolution`.

`validate_ode → transform_each_term → solve_for_Y → rational_pipeline → inverse_pipeline → verify_ode`.

---

# 9. Aufgabentyp D – Übertragungsfunktion aus DGL

## Fundstellen

- `skript.pdf`, PDF-S. 56–57
- `Regelungstechnik_Übung_Aufg-u-Lösungen.pdf`, PDF-S. 47–48 und 52, Aufgabe 2
- `RT_Klausur_SS2025-komplett.pdf`, PDF-S. 4 und 46, Aufgabe 1d, 5 Punkte

## Voraussetzungen

- LTI-DGL
- Eingang und Ausgang eindeutig
- alle Anfangswerte null

## Eingabe

- DGL
- markierter Eingang \(u(t)\)
- markierter Ausgang \(y(t)\)
- Bestätigung `initial_state_zero=true`

## Ausgabe

- transformierte DGL
- \(G(s)=Y(s)/U(s)\)
- Zähler-/Nennerpolynom
- Grade, Realisierbarkeit, Pole und Nullstellen

## Klausurtauglicher Rechenweg

1. Nullanfangsbedingungen notieren.
2. DGL transformieren.
3. \(Y(s)\)-Terme auf eine Seite bringen.
4. \(U(s)\)-Terme auf die andere Seite bringen.
5. ausklammern.
6. Quotient bilden:
   \[
   G(s)=\frac{Y(s)}{U(s)}.
   \]
7. Vorzeichen, Grade und Einheiten prüfen.

## Sonderfälle

- mehrere Eingänge/Ausgänge: nicht Teil dieses SISO-Moduls
- nichtnull Anfangswerte: keine reine Übertragungsfunktion aus der Gesamtlösung bilden
- gemeinsamer Faktor: Originalform erhalten und Kürzung nur mit Bericht

## Typische Fehler

- Anfangswerte unbemerkt null setzen
- Eingangsvorzeichen verlieren
- \(U/Y\) statt \(Y/U\)
- Dämpfungsterm mit falschem Vorzeichen

## Plausibilitätsprüfungen

- erneutes Multiplizieren ergibt transformierte DGL
- Gradkriterium aus Skript PDF-S. 60
- Pole gegen Stabilitätskriterium aus Skript PDF-S. 123
- DC-Verstärkung \(G(0)\), falls definiert

## GUI-Eingaben

- DGL
- Dropdown Eingang/Ausgang
- Checkbox „alle Anfangswerte null“; standardmäßig nicht vorangekreuzt

## LaTeX-Ausgabe

\[
\begin{aligned}
\mathcal L\{\text{DGL}\}&:\ \dots\\
N(s)Y(s)&=Z(s)U(s)\\
G(s)&=\frac{Y(s)}{U(s)}=\boxed{\frac{Z(s)}{N(s)}}.
\end{aligned}
\]

## Domainwerte und Orchestrierung

`LinearOdeData → zero_ic_transform → solve_transfer_ratio → classify_rational → verify`.

---

# 10. Aufgabentyp E – Rationale Vorverarbeitung und Polynomdivision

## Fundstellen

- `skript.pdf`, PDF-S. 57–60
- keine isolierte offizielle Rechenaufgabe zur Polynomdivision gefunden

## Voraussetzungen

\[
F(s)=\frac{Z(s)}{N(s)}
\]
mit Polynomen über reellen exakten Koeffizienten.

## Eingabe

- Zähler und Nenner oder kompletter rationaler Ausdruck

## Ausgabe

- Grade \(m=\deg Z\), \(n=\deg N\)
- Klassifikation:
  - streng echt: \(m<n\)
  - gleichgradig/realisierbar sprungfähig: \(m=n\)
  - unecht/nicht realisierbar als gewöhnliche Übertragungsfunktion: \(m>n\)
- Quotient und Rest aus Polynomdivision
- Warnung/Fehlerstatus

## Klausurtauglicher Rechenweg

1. Zähler und Nenner ausmultiplizieren und Grad bestimmen.
2. bei \(m>n\): Polynomdivision
   \[
   Z(s)=Q(s)N(s)+R(s),\qquad \deg R<n.
   \]
3. schreiben:
   \[
   F(s)=Q(s)+\frac{R(s)}{N(s)}.
   \]
4. Realisierbarkeit markieren.
5. Nur den echten Restbruch in die PBZ geben.

## Sonderfälle

- \(m=n\): konstanter Direktterm \(c_0\)
- \(m>n\): Quotient mit \(s\)-Potenzen; eine gewöhnliche Zeitfunktion erfordert Distributionen, die in den RT1-Aufgaben nicht als Rechenstoff belegt sind
- Nenner null: harter Fehler

## Typische Fehler

- PBZ direkt auf eine unechte Funktion anwenden
- gleichgradigen Direktterm verlieren
- unechte Übertragungsfunktion als physikalisch realisierbar ausgeben

## Plausibilitätsprüfungen

\[
Q(s)N(s)+R(s)-Z(s)=0.
\]

## GUI-Eingaben

- rationaler Ausdruck
- Ergebnisbereich „Grad/Realiserbarkeit“

## LaTeX-Ausgabe

\[
\frac{Z(s)}{N(s)}=Q(s)+\frac{R(s)}{N(s)},
\qquad \deg R<\deg N.
\]

## Domainwerte und Orchestrierung

`RationalFunctionData → polynomial_division → realizability_classification → warning_policy`.

---

# 11. Aufgabentyp F – Partialbruchzerlegung: einfache reelle Pole

## Fundstellen

- `skript.pdf`, PDF-S. 57–58
- `Regelungstechnik_Tutorium_komplett.pdf`, PDF-S. 14, Aufgabe 4a
- `Regelungstechnik_Übung_Aufg-u-Lösungen.pdf`, PDF-S. 50–51

## Voraussetzungen

- echter Restbruch
- Nenner in verschiedene lineare reelle Faktoren zerlegbar

## Eingabe

\[
F(s)=\frac{Z(s)}{\prod_i(s-p_i)},\qquad p_i\ne p_j.
\]

## Ausgabe

\[
F(s)=\sum_i\frac{A_i}{s-p_i}.
\]

## Klausurtauglicher Rechenweg

1. Nenner faktorisieren.
2. Ansatz mit jedem Faktor genau einmal aufstellen.
3. Hauptnenner multiplizieren.
4. Koeffizienten durch Einsetzen der Pole oder Koeffizientenvergleich bestimmen.
5. Gleichheit durch Rückzusammenfassen prüfen.
6. jeden Term rücktransformieren.

## Formel

Für einen einfachen Pol \(p_i\):

\[
A_i=\lim_{s\to p_i}(s-p_i)F(s).
\]

Diese Abkürzung darf nur verwendet werden, wenn der Rechenweg nachvollziehbar bleibt.

## Sonderfälle

- Parameterpole mit möglicher Koinzidenz: Bedingung \(p_i\ne p_j\) ausgeben
- Faktoren wie \(2s+1\) vor Rücktransformation normieren

## Typische Fehler

- falscher Ansatz
- Faktor vor \(s\) verlieren
- Vorzeichen bei \(s-p\) versus \(s+a\)

## Plausibilitätsprüfungen

- symbolisches Rückzusammenfassen
- Residuen numerisch gegen Original an zwei zulässigen Punkten

## GUI/LaTeX/Domain

GUI zeigt Faktorisierung, Ansatz, Koeffizientengleichungen, Ergebnis.  
Domain: `PoleRecord`, `PartialFractionTerm`, `LinearCoefficientSystem`.

## Orchestrierung

`factor_denominator → build_pf_template → solve_coefficients → verify_recomposition → inverse_terms`.

---

# 12. Aufgabentyp G – Partialbruchzerlegung: mehrfacher reeller Pol

## Fundstellen

- `skript.pdf`, PDF-S. 57–58, Theorem 3.7
- `Regelungstechnik_Übung_Aufg-u-Lösungen.pdf`, PDF-S. 50–51: Pol \(-1\) mit Multiplizität 2

## Voraussetzungen

- Nenner enthält \((s-p)^k\), \(k\ge2\)

## Eingabe

\[
F(s)=\frac{Z(s)}{(s-p)^kR(s)},\qquad R(p)\ne0.
\]

## Ausgabe

\[
\frac{A_1}{s-p}+\frac{A_2}{(s-p)^2}+\dots+\frac{A_k}{(s-p)^k}
\]
plus übrige Faktoren.

## Klausurtauglicher Rechenweg

1. Multiplizität jedes Pols bestimmen.
2. für jede Potenz von 1 bis \(k\) einen Term ansetzen.
3. Hauptnenner beseitigen.
4. Koeffizientenvergleich oder Ableitungsformel durchführen.
5. Rückzusammenfassen.
6. rücktransformieren:
   \[
   \frac{1}{(s-p)^r}
   \longleftrightarrow
   \frac{t^{r-1}}{(r-1)!}e^{pt}.
   \]

## Sonderfälle

- Polmultiplizität steigt durch resonanten Eingang
- Parametergrenze, bei der zwei Pole zusammenfallen: getrennte Fallunterscheidung

## Typische Fehler

- nur höchsten Potenzterm ansetzen
- Faktor \((r-1)!\) vergessen
- mehrfachen Pol numerisch als zwei nahe einfache Pole behandeln

## Plausibilitätsprüfungen

- exakte Multiplizität über \(\gcd(N,N')\)
- Rückzusammenfassen
- Zeitfunktion enthält passende Polynompower \(t^{r-1}\)

## GUI/LaTeX/Domain/Orchestrierung

GUI markiert „mehrfacher Pol“.  
Domain: `PoleRecord(multiplicity=k)`.  
Orchestrierung wie Aufgabentyp F, aber multiplicity-aware.

---

# 13. Aufgabentyp H – Komplex konjugierte Pole

## Fundstellen

- `skript.pdf`, PDF-S. 55 und 57–58
- `Regelungstechnik_Tutorium_komplett.pdf`, PDF-S. 13–14, Aufgaben 3b/4b
- `Regelungstechnik_Übung_Aufg-u-Lösungen.pdf`, PDF-S. 53–55, Aufgabe 3
- `Tabelle_Standardglieder.pdf`, PDF-S. 1, PT2-Glied

## Voraussetzungen

- irreduzibler reeller quadratischer Nenner oder konjugiertes Polpaar

## Eingabe

\[
F(s)=\frac{as+b}{(s-\alpha)^2+\beta^2},\qquad \beta>0.
\]

## Ausgabe

\[
f(t)=e^{\alpha t}\left(a\cos(\beta t)+\frac{b+a\alpha}{\beta}\sin(\beta t)\right)
\]
für passend normalisierte Koeffizienten; in der tatsächlichen Ausgabe wird der Zähler zuerst exakt in \(A(s-\alpha)+B\) zerlegt.

## Klausurtauglicher Rechenweg

1. quadratischen Faktor normieren.
2. Quadrat vervollständigen:
   \[
   s^2+bs+c=(s-\alpha)^2+\beta^2.
   \]
3. Zähler als
   \[
   A(s-\alpha)+B
   \]
   schreiben.
4. Kosinus- und Sinusanteil getrennt rücktransformieren.
5. Realteil \(\alpha\) für Dämpfung/Stabilität interpretieren.

## Sonderfälle

- \(\beta=0\): kein komplexes Paar, sondern mehrfacher reeller Pol
- \(\alpha=0\): ungedämpfte Dauerschwingung
- \(\alpha>0\): anwachsende Schwingung, instabil

## Typische Fehler

- Quadrat falsch vervollständigen
- Sinusfaktor \(1/\beta\) vergessen
- komplexe Zeitfunktion statt reeller Sinus-/Kosinusform ausgeben

## Plausibilitätsprüfungen

- Pole sind \(\alpha\pm j\beta\)
- Zeitfunktion ist reell
- Hüllkurve entspricht \(e^{\alpha t}\)
- Stabilität: \(\alpha<0\)

## GUI/LaTeX/Domain/Orchestrierung

GUI zeigt Quadratvervollständigung und Polpaar.  
Domain: ein `PoleRecord`-Paar mit gemeinsamer Multiplizität.  
`complete_square → split_numerator → inverse_pair → stability_check`.

---

# 14. Aufgabentyp I – Sprungantwort

## Fundstellen

- `Regelungstechnik_Tutorium_komplett.pdf`, PDF-S. 13–14
- `Regelungstechnik_Übung_Aufg-u-Lösungen.pdf`, PDF-S. 48 und 53–55
- `Tabelle_Standardglieder.pdf`, PDF-S. 1–3

## Voraussetzungen

- Übertragungsfunktion bei Ruhezustand
- Sprungamplitude \(F_{\mathrm{ex}}\)

## Eingabe

- \(G(s)\)
- \(F_{\mathrm{ex}}\)
- optional Parameterannahmen

## Ausgabe

- \(U(s)=F_{\mathrm{ex}}/s\)
- \(Y(s)=G(s)F_{\mathrm{ex}}/s\)
- PBZ und \(y(t)\)
- Anfangs-/Endwert, Pole, Stabilität

## Klausurtauglicher Rechenweg

1. sofort
   \[
   U(s)=\frac{F_{\mathrm{ex}}}{s}
   \]
   notieren.
2. \(Y=GU\) bilden.
3. Faktoren und mögliche Kürzungen protokollieren.
4. Rationalität klassifizieren.
5. PBZ oder Tabellenform.
6. rücktransformieren.
7. Anfangswert, Endwert und qualitative Form prüfen.

## Sonderfälle

- Pol bei \(s=0\): Endwert kann nicht endlich sein
- ungedämpftes komplexes Polpaar: kein Endwert
- instabiler Pol: Endwertsatz nicht anwenden
- gleichgradiges \(G(s)\): Ausgang kann springen; Direktterm sichtbar halten

## Typische Fehler

- Faktor \(1/s\) vergessen
- Sprungamplitude vergessen
- Endwertsatz trotz instabiler Pole anwenden
- \(G(0)F_{\mathrm{ex}}\) als Endwert nutzen, obwohl Integrator/Instabilität vorliegt

## Plausibilitätsprüfungen

- für stabiles System ohne Pol bei 0:
  \[
  y(\infty)=F_{\mathrm{ex}}G(0)
  \]
- Endwertsatz nur nach Polprüfung:
  \[
  \lim_{t\to\infty}y(t)=\lim_{s\to0}sY(s)
  \]
- Standardgliedvergleich, z. B. PT1/PT2

## GUI-Eingaben

- \(G(s)\)
- Sprungamplitude
- Ausgabeoption „nur Bildbereich“ oder „vollständige Zeitantwort“

## LaTeX-Ausgabe

Muss \(U(s)\), \(Y(s)\), PBZ und Endergebnis getrennt zeigen.

## Domain/Orchestrierung

`TransferFunctionData + StepSignal → output_laplace → rational_pipeline → inverse_pipeline → final_value_guarded`.

---

# 15. Aufgabentyp J – Impulsantwort

## Fundstellen

- `skript.pdf`, PDF-S. 54: \(\delta(t)\leftrightarrow1\)
- `skript.pdf`, PDF-S. 56–57: \(Y=GU\)
- keine isolierte Rechenaufgabe in Übungen/Klausuren gefunden

## Voraussetzungen

- SISO-LTI-System in Ruhe

## Eingabe

- \(G(s)\)
- Impulsamplitude \(A\)

## Ausgabe

\[
U(s)=A,
\qquad
Y(s)=A G(s),
\qquad
h_A(t)=A\mathcal L^{-1}\{G(s)\}.
\]

## Rechenweg

1. \(u(t)=A\delta(t)\) schreiben.
2. \(U(s)=A\).
3. \(Y(s)=AG(s)\).
4. inverse Laplace durchführen.
5. Pole/Stabilität prüfen.

## Sonderfälle und Grenzen

- nicht streng echte Systeme können Dirac-Anteile in der Impulsantwort besitzen
- solche Distributionsanteile sind in den offiziellen RT1-Rechenaufgaben nicht belegt und gehören nicht in das günstige MVP

## GUI/LaTeX/Domain/Orchestrierung

Wie Sprungantwort, aber `ImpulseSignal`; keine zusätzliche \(1/s\)-Multiplikation.

---

# 16. Aufgabentyp K – Allgemeines Eingangssignal

## Fundstellen

- `Regelungstechnik_Übung_Aufg-u-Lösungen.pdf`, PDF-S. 47 und 50–51: \(u(t)=9e^{2t}\)
- `skript.pdf`, PDF-S. 53–55

## Voraussetzungen

- \(G(s)\) oder DGL
- transformierbares Standardsignal

## Eingabe

- Systembeschreibung
- `InputSignal`
- Anfangsbedingungen

## Ausgabe

- \(U(s)\)
- \(Y(s)\)
- Zeitantwort

## Rechenweg

1. Eingang anhand des Signaltyps transformieren.
2. bei Ruhezustand \(Y=GU\); sonst Anfangswertanteil ergänzen.
3. gemeinsamen Nenner bilden.
4. Pole einschließlich Eingangs-/Resonanzpole bestimmen.
5. PBZ und Rücktransformation.
6. verifizieren.

## Sonderfälle

- Eingangspol fällt mit Systempol zusammen → erhöhte Multiplizität
- Sinus/Kosinus bei Pol auf imaginärer Achse → Resonanz, wachsende Amplitude möglich
- Parameterfall benötigt Annahmen

## Typische Fehler

- nur Systempole betrachten und Eingangspole übersehen
- Resonanz nicht als Mehrfachpol erkennen
- nichtnull Anfangswerte ignorieren

## GUI/LaTeX/Domain/Orchestrierung

Signaltyp-Auswahl plus Parameterfelder; alternativ direkte \(U(s)\)-Eingabe.  
`transform_input → combine_with_system_and_ic → rational_pipeline → inverse → verify`.

---

# 17. Aufgabentyp L – Faltung

## Fundstellen

- `skript.pdf`, PDF-S. 53–54, Faltungssatz
- `skript.pdf`, PDF-S. 57, Begründung von \(Y=GU\)
- keine offizielle numerische Faltungsaufgabe gefunden

## Fachliche Rolle

\[
(f*g)(t)=\int_0^t f(\tau)g(t-\tau)\,\mathrm d\tau
\longleftrightarrow
F(s)G(s).
\]

## Spezifikation

- Als erklärender Alternativweg und Verifikation vorsehen.
- Nicht als primärer Klausurweg im MVP, da die Quellen gerade den Bildbereich als einfachere Alternative zur Integralfaltung darstellen.
- Erweiterung kann für einfache Polynom-/Exponentialsignale die Faltung explizit auswerten.

## GUI

Option „Alternative Faltungsdarstellung anzeigen“, standardmäßig aus.

## Renderergrenze

Das Integral und seine Auswertung werden vollständig in Domain/Application berechnet.

---

# 18. Aufgabentyp M – Endwertsatz

## Fundstellen

- `Regelungstechnik_Übung_Aufg-u-Lösungen.pdf`, PDF-S. 104–105
- Stabilitätsvoraussetzung ergänzend aus `skript.pdf`, PDF-S. 123

## Eingabe

- \(Y(s)\)
- optional System/Input getrennt

## Ausgabe

- Zulässigkeitsprüfung
- exakter Endwert oder begründete Ablehnung

## Rechenweg

1. \(sY(s)\) bilden.
2. Pole von \(sY(s)\) bestimmen.
3. Satz nur anwenden, wenn alle relevanten Pole strikt in der linken Halbebene liegen; zulässige Sonderfälle müssen explizit behandelt werden.
4. Grenzwert
   \[
   \lim_{s\to0}sY(s)
   \]
   berechnen.
5. mit direkter Zeitantwort vergleichen, sofern vorhanden.

## Typische Fehler

- Stabilitätsprüfung auslassen
- bei Dauerschwingung/Instabilität einen endlichen Wert ausgeben
- Sprungfaktor doppelt berücksichtigen

## GUI/LaTeX/Domain/Orchestrierung

Button „stationären Endwert prüfen“.  
`build_sY → pole_guard → exact_limit → compare_time_solution`.

## Anfangswertsatz

Ein benannter Anfangswertsatz wurde in den ausgewerteten RT1-Quellen nicht als Aufgabentyp gefunden. Anfangswerte werden über Ableitungssatz und direkte Prüfung behandelt. Daher nicht als eigenständiges MVP-Feature spezifizieren.

---

# 19. Stabilitäts- und Plausibilitätskontrollen

## 19.1 Pole

Nach `skript.pdf`, PDF-S. 123 ist ein SISO-System E/A-stabil genau dann, wenn alle Pole \(p_i\) erfüllen:

\[
\operatorname{Re}(p_i)<0.
\]

Ausgabe:

- stabil
- grenzstabil/nicht asymptotisch: Pol auf imaginärer Achse
- instabil: mindestens ein Pol mit positivem Realteil
- unbestimmt bei nicht ausreichend spezifizierten Parametern

## 19.2 Anfangswerte

Aus Zeitfunktion direkt auswerten. Bei nicht existierendem endlichen Anfangswert Warnung.

## 19.3 Endwerte

Nur mit Polprüfung. Kein stilles Anwenden.

## 19.4 DGL-Probe

Für gelöste DGL zwingend. Residuum exakt null.

## 19.5 PBZ-Probe

Original minus Summe der Partialbrüche exakt null.

## 19.6 Kürzungsbericht

Wegen `skript.pdf`, PDF-S. 58, Bemerkung 3.8:

- Originalfaktoren speichern
- gemeinsame Faktoren erkennen
- nicht stillschweigend löschen
- reduzierte Form darf zusätzlich angezeigt werden
- Warnung: Pol-Nullstellen-Kürzung kann interne Eigenschaften verdecken

## 19.7 Numerische Kontrolle

- mindestens zwei reguläre Stichstellen im \(s\)-Bereich für rationale Gleichheiten
- mindestens eine Zeitstelle für Zeitantwort
- Prüfpunkte dürfen keine Pole treffen
- numerische Kontrolle ist Zusatz, nicht Beweis

---

# 20. Gewünschte Ausgabestruktur im Programm

## 20.1 Kurzantwort

- Endergebnis
- Aufgabentyp
- Stabilitätsstatus
- wichtigste Warnung

## 20.2 Klausurrechenweg

Nummerierte Blöcke:

1. Eingang/Anfangswerte
2. Transformation
3. algebraisches Auflösen
4. Faktorisierung/PBZ
5. inverse Transformation
6. Kontrollen

## 20.3 LaTeX-Paket

Das Ergebnisobjekt liefert mindestens:

- `latex_problem`
- `latex_steps[]`
- `latex_result`
- `latex_checks[]`
- `latex_full_solution`

Keine LaTeX-Erzeugung im UI-Renderer.

---

# 21. Referenzaufgaben

## R1 – Leicht: direkte Laplace-Transformation

**Fundstelle:** `Regelungstechnik_Tutorium_komplett.pdf`, PDF-S. 12–13, Aufgabe 2b.

### Aufgabe

\[
f(t)=2t e^{-4t}.
\]

### Rechenweg

\[
\mathcal L\{t\}=\frac1{s^2}.
\]

Mit Faktor 2:

\[
\mathcal L\{2t\}=\frac2{s^2}.
\]

Dämpfungssatz mit \(e^{-4t}\): \(s\mapsto s+4\).

\[
\boxed{F(s)=\frac2{(s+4)^2}}.
\]

### Numerische Kontrolle

Bei \(s=2\):

\[
F(2)=\frac2{36}=\frac1{18}.
\]

Direkt:

\[
\int_0^\infty 2t e^{-6t}\,dt=\frac1{18}.
\]

---

## R2 – Leicht bis mittel: inverse Laplace mit komplexem Paar

**Fundstelle:** `Regelungstechnik_Tutorium_komplett.pdf`, PDF-S. 12–13, Aufgabe 2h.

### Aufgabe

\[
F(s)=\frac{s-4}{(s-4)^2+4}.
\]

### Rechenweg

Vergleich mit

\[
e^{at}\cos(\omega t)
\longleftrightarrow
\frac{s-a}{(s-a)^2+\omega^2}
\]

ergibt \(a=4\), \(\omega=2\).

\[
\boxed{f(t)=e^{4t}\cos(2t)}.
\]

### Kontrolle

Vorwärtstransformation liefert exakt den Ausgangsausdruck. Wegen Realteil \(+4\) wächst die Hüllkurve; als Systemmodus wäre dies instabil.

---

## R3 – Schwer: DGL, Anfangsbedingungen, mehrfacher Pol und PBZ

**Fundstelle:** `Regelungstechnik_Übung_Aufg-u-Lösungen.pdf`, PDF-S. 47 und 50–51, Übung 03 Aufgabe 1.

### Aufgabe

\[
y''(t)+2y'(t)+y(t)=9e^{2t},
\qquad y(0)=0,\quad y'(0)=1.
\]

### Transformation

\[
\mathcal L\{y''\}=s^2Y(s)-1,
\qquad
\mathcal L\{2y'\}=2sY(s),
\qquad
\mathcal L\{9e^{2t}\}=\frac9{s-2}.
\]

\[
(s^2+2s+1)Y(s)-1=\frac9{s-2}.
\]

\[
Y(s)=\frac{s+7}{(s+1)^2(s-2)}.
\]

### PBZ

\[
Y(s)=\frac{A}{s+1}+\frac{B}{(s+1)^2}+\frac{C}{s-2}.
\]

Koeffizientenvergleich:

\[
A=-1,\qquad B=-2,\qquad C=1.
\]

\[
Y(s)=-\frac1{s+1}-\frac2{(s+1)^2}+\frac1{s-2}.
\]

### Ergebnis

\[
\boxed{y(t)=-e^{-t}-2te^{-t}+e^{2t}}.
\]

### Kontrollen

\[
y(0)=0,
\qquad
y'(0)=1,
\qquad
y''+2y'+y=9e^{2t}.
\]

Numerisch:

\[
y(1)\approx6.28542.
\]

---

## R4 – Mittel: PT1-Sprungantwort

**Fundstelle:** `Regelungstechnik_Tutorium_komplett.pdf`, PDF-S. 13–14, Aufgaben 3a/4a.

### Aufgabe

\[
G(s)=\frac1{2s+1},
\qquad F_{\mathrm{ex}}=0.1.
\]

### Rechenweg

\[
U(s)=\frac{0.1}{s},
\qquad
Y(s)=\frac{0.1}{s(2s+1)}.
\]

\[
Y(s)=\frac{0.1}{s}-\frac{0.1}{s+0.5}.
\]

\[
\boxed{y(t)=0.1\left(1-e^{-0.5t}\right)}.
\]

### Kontrollen

\[
y(0)=0,
\qquad y(\infty)=0.1,
\qquad T=2.
\]

\[
y(2)=0.1(1-e^{-1})\approx0.0632121.
\]

---

## R5 – Mittel: ungedämpftes komplexes Polpaar

**Fundstelle:** `Regelungstechnik_Tutorium_komplett.pdf`, PDF-S. 13–14, Aufgaben 3b/4b.

### Aufgabe

\[
G(s)=\frac{s}{s^2+\pi/4},
\qquad F_{\mathrm{ex}}=\frac\pi2.
\]

### Rechenweg

\[
U(s)=\frac{\pi}{2s}.
\]

\[
Y(s)=\frac{s}{s^2+\pi/4}\frac{\pi}{2s}
=\frac{\pi/2}{s^2+\pi/4}.
\]

Mit

\[
\omega=\sqrt{\frac\pi4}=\frac{\sqrt\pi}{2}
\]

folgt

\[
\boxed{
y(t)=\sqrt\pi\sin\left(\frac{\sqrt\pi}{2}t\right)
}.
\]

### Kontrollen

\[
y(0)=0,
\qquad y'(0)=\frac\pi2.
\]

Die Pole liegen auf der imaginären Achse; kein stationärer Endwert. Numerisch \(y(1)\approx1.37310\).

---

## R6 – Schwerer Parameterfall: Feder-Masse-Dämpfer-Sprungantwort

**Fundstelle:** `Regelungstechnik_Übung_Aufg-u-Lösungen.pdf`, PDF-S. 47–48 und 52–55, Aufgaben 2–3.

### Aufgabe

\[
M y''+\eta y'+ky=F_{\mathrm{ext}}\Theta(t),
\qquad y(0)=y'(0)=0.
\]

### Übertragungsfunktion

\[
\boxed{G(s)=\frac1{Ms^2+\eta s+k}}.
\]

### Bildantwort

\[
Y(s)=\frac{F_{\mathrm{ext}}}{s(Ms^2+\eta s+k)}.
\]

Definiere für den unterdämpften Fall

\[
\delta=\frac{\eta}{2M},
\qquad
\omega=\sqrt{\frac{k}{M}-\delta^2},
\qquad
\frac{k}{M}>\delta^2.
\]

### Ergebnis

\[
\boxed{
y(t)=\frac{F_{\mathrm{ext}}}{k}
\left[
1-e^{-\delta t}
\left(
\cos(\omega t)+\frac{\delta}{\omega}\sin(\omega t)
\right)
\right]
}.
\]

### Kontrollen

\[
y(0)=0,
\qquad y'(0)=0,
\qquad y(\infty)=\frac{F_{\mathrm{ext}}}{k}
\]
bei \(\delta>0\).

Für \(M=0.2\), \(\eta=0.5\), \(k=150\), \(F_{\mathrm{ext}}=1\):

\[
\delta=1.25,
\qquad
\omega\approx27.3576,
\qquad
y(0.1)\approx0.0119660.
\]

---

## R7 – Klausurfall: DGL zu Übertragungsfunktion mit Vorzeichenkontrolle

**Fundstelle:** `RT_Klausur_SS2025-komplett.pdf`, PDF-S. 4; Musterlösung PDF-S. 46, Aufgabe 1d.

### Aufgabe

\[
\phi_G''(t)=\frac1{m_Kl}
\left(d_K\phi_G'(t)-F_A(t)-g(m_K+m_G)\phi_G(t)\right),
\]

alle Anfangswerte null, Eingang \(F_A\), Ausgang \(\phi_G\).

### Rechenweg

\[
m_Kl\,s^2\Phi_G(s)
=d_Ks\Phi_G(s)-F_A(s)-g(m_K+m_G)\Phi_G(s).
\]

\[
\left[m_Kl\,s^2-d_Ks+g(m_K+m_G)\right]\Phi_G(s)=-F_A(s).
\]

\[
\boxed{
G_S(s)=\frac{\Phi_G(s)}{F_A(s)}
=-\frac1{m_Kl\,s^2-d_Ks+g(m_K+m_G)}
}.
\]

### Kontrolle

Das negative Eingangsvorzeichen und das durch die gegebene DGL entstehende \(-d_Ks\) dürfen nicht „physikalisch plausibel“ umkorrigiert werden. Das Programm muss die Quelle algebraisch korrekt abbilden und separat warnen, wenn positive Parameter instabile Pole erzeugen.

Beispiel \(m_K=2,l=3,d_K=1,g=10,m_G=1\):

\[
N(s)=6s^2-s+30,
\]

dessen Pole den Realteil \(1/12>0\) besitzen. Ergebnis: instabil.

---

## R8 – Fehler-/Grenzfall: unechte rationale Funktion

**Direkt aus den Quellenregeln abgeleitet:** `skript.pdf`, PDF-S. 59–60, Theorem 3.13; PBZ-Grundlage PDF-S. 57–58.

### Aufgabe

\[
F(s)=\frac{s^2+1}{s+1}.
\]

### Rechenweg

\[
\deg Z=2>1=\deg N.
\]

Polynomdivision:

\[
s^2+1=(s-1)(s+1)+2.
\]

\[
\boxed{F(s)=s-1+\frac2{s+1}}.
\]

### Exaktes Fachresultat

- Der Restbruch ist echt.
- Als Übertragungsfunktion ist der Gesamtausdruck nach dem Gradkriterium nicht realisierbar.
- Eine gewöhnliche Tabellen-Rücktransformation des Polynomteils würde distributionsartige Terme benötigen; diese sind nicht Bestandteil der belegten RT1-Rechenaufgaben.
- MVP-Ausgabe: Polynomdivision zeigen und mit `NON_REALIZABLE_IMPROPER` abbrechen, statt eine scheinbar normale Zeitfunktion zu erfinden.

---

## R9 – Endwertsatz

**Fundstelle:** `Regelungstechnik_Übung_Aufg-u-Lösungen.pdf`, PDF-S. 104, Aufgabe 3.

### Aufgabe

Für einen Einheitssprung der Störung gilt

\[
Y(s)=\frac1s\cdot
\frac1{(T_1s+1)(T_2s+1)+K_R(T_2s+1)}.
\]

Bestimme den stationären Wert bei \(K_R=24\).

### Rechenweg

Nach Polprüfung:

\[
\lim_{t\to\infty}y(t)
=\lim_{s\to0}sY(s)
=\frac1{1+K_R}.
\]

\[
\boxed{y(\infty)=\frac1{25}=0.04}.
\]

---

# 22. Testpflichten

## 22.1 Unit-Tests auf Domänenebene

Mindestens:

1. jedes direkte Tabellenpaar aus Tutorium 03 Aufgabe 2
2. inverse Paare Aufgabe 2f–i
3. PBZ mit einfachen Polen
4. PBZ mit doppeltem Pol
5. komplexes Paar mit Zählerzerlegung
6. DGL R3 vollständig
7. PT1-Sprung R4
8. ungedämpfte Antwort R5
9. Parameterantwort R6 mit Annahmeprüfung
10. Klausurvorzeichen R7
11. unechter Grenzfall R8
12. Endwertsatz gültig und ungültig
13. gemeinsame Faktoren mit Kürzungswarnung
14. fehlende Anfangsbedingung
15. Pol auf imaginärer Achse

## 22.2 Golden-Tests für LaTeX

Für R1–R9 müssen stabile Golden-Ausgaben existieren. Insbesondere:

- Dezimalkomma in deutscher Darstellung optional, intern Punkt
- \(\mathcal L\), \(\mathcal L^{-1}\)
- \(\operatorname{Re}\)
- korrekt gesetzte Ableitungen
- keine verlorenen Klammern bei verschobenen Quadraten

## 22.3 Property-Tests

- PBZ rückzusammengefasst = Original
- \(\mathcal L(\mathcal L^{-1}(F))=F\) für unterstützte Klasse
- \(\mathcal L^{-1}(\mathcal L(f))=f\) für unterstützte Klasse
- Polynomdivision rekonstruiert den Zähler
- DGL-Residuum null

---

# 23. MVP-Abgrenzung

## A. Günstiges erstes MVP

| Funktion | Aufwand | Klausurnutzen | Begründung |
|---|---:|---:|---|
| sicherer Formelparser für \(s,t\) und Parameter | mittel | zwingend | Grundlage aller Funktionen |
| direkte/inverse Standard-Laplace-Paare | niedrig | mittel | schnell und einfach |
| DGL mit konstanten Koeffizienten und Anfangswerten bis mindestens Ordnung 4 | mittel | sehr hoch | Übungskern, hohe Fehlerquote |
| Übertragungsfunktion aus SISO-DGL bei Nullanfangswerten | niedrig bis mittel | sehr hoch | direkte SS2025-Klausuraufgabe |
| rationale Klassifikation, Gradprüfung und Polynomdivision | mittel | sehr hoch | Vorstufe der PBZ und sicherer Grenzfall |
| PBZ: einfache und mehrfache reelle Pole | mittel | sehr hoch | zeitaufwendig, offiziell geübt |
| PBZ: irreduzible quadratische Faktoren/komplexe Paare | mittel | sehr hoch | PT2 und Schwingungen |
| Sprungantwort beliebiger unterstützter rationaler SISO-Systeme | mittel | sehr hoch | direkte Übungs- und Regelkreisrelevanz |
| allgemeine Eingänge: Sprung, Exponential, Polynom, Sinus, Kosinus | mittel | hoch | deckt Quellenfälle ab |
| Pflichtkontrollen: PBZ, DGL, Anfangswerte, Pole | mittel | sehr hoch | verhindert falsche sichere Ausgaben |
| klausurtaugliche nummerierte LaTeX-Schritte | mittel | sehr hoch | Ergebnis ohne Rechenweg wird nicht gewertet |

**MVP-Urteil:** Dieser Block ist fachlich kompakt genug und hat ein starkes Verhältnis aus Klausurpunkten zu Entwicklungsaufwand. PBZ inklusive Mehrfachpol und komplexem Paar darf nicht künstlich auf später verschoben werden; sonst ist das MVP für die eigentlichen Zeitantworten zu schwach.

## B. Sinnvolle Erweiterung

| Funktion | Aufwand | Klausurnutzen |
|---|---:|---:|
| Endwertsatz mit strikter Polprüfung | niedrig bis mittel | hoch |
| Impulsantwort streng echter Systeme | niedrig | mittel |
| Zeitverschiebung/Totzeit und verzögerter Sprung | mittel | mittel |
| alternative Faltungsdarstellung | mittel | niedrig bis mittel |
| parameterabhängige Fallunterscheidung über Diskriminanten | mittel bis hoch | mittel bis hoch |
| automatische Standardglied-Erkennung PT1/PT2/I/IT1/DT1 | mittel | hoch |
| Einheitenprüfung bei physikalischen Parametern | mittel | mittel |
| Export einzelner Rechenschritte als kopierbares LaTeX | niedrig | hoch |

## C. Teure Spezialfälle für später

| Funktion | Aufwand | Klausurnutzen | Grund für spätere Umsetzung |
|---|---:|---:|---|
| unechte inverse Laplace mit Dirac-Ableitungen | hoch | niedrig | nicht als RT1-Rechenaufgabe belegt |
| allgemeine stückweise Funktionen | hoch | niedrig bis mittel | großer Parser-/Fallaufwand |
| allgemeine symbolische Parameter-PBZ mit unbekannter Polordnung | sehr hoch | mittel | Fallkombinatorik explodiert |
| numerische inverse Laplace für nicht rationale Funktionen | hoch | niedrig | nicht quellengetrieben |
| MIMO-Invers-Laplace/Matrix-PBZ | sehr hoch | niedrig | Theorem 3.7 ist im Skript auf SISO beschränkt |
| automatische Herleitung aus Bildern/Handschrift | sehr hoch | nicht zulässig/nicht nötig | Fotografieren in Klausur verboten |
| visueller Signal-/Blockeditor | hoch | gering für diesen Block | außerhalb des Rechenkerns |

---

# 24. Fachliche Akzeptanzkriterien

Das Modul ist fachlich akzeptabel, wenn es:

1. alle Referenzaufgaben R1–R9 exakt löst,
2. bei R3 jeden Anfangswertterm sichtbar zeigt,
3. Mehrfachpole nicht in nahe einfache Pole approximiert,
4. komplexe Paare als reelle Sinus-/Kosinusantwort ausgibt,
5. Endwertsatz nur nach Stabilitätsprüfung verwendet,
6. unechte Übertragungsfunktionen erkennt,
7. gemeinsame Faktoren nicht stillschweigend verschwinden lässt,
8. exakte und numerische Ergebnisse trennt,
9. jede Lösung durch mindestens eine unabhängige symbolische Kontrolle absichert,
10. im Renderer keinerlei Fachberechnung ausführt,
11. vollständiges kopierbares LaTeX für den klausurtauglichen Rechenweg liefert,
12. bei unzureichenden Parameterannahmen „nicht eindeutig“ statt einer geratenen Fallauswahl ausgibt.

---

# 25. Offene Quellenunsicherheiten

1. Ein benannter Anfangswertsatz ist in den ausgewerteten Quellen nicht als Rechenverfahren belegt.
2. Faltung ist theoretisch enthalten, aber nicht als konkrete Übungs-/Klausurrechnung gefunden.
3. Polynomdivision ist als mathematische Vorstufe für unechte Funktionen nötig, aber nicht als eigener offizieller Aufgabentyp belegt.
4. Distributionsartige inverse Laplace-Terme über \(\delta'(t)\) sind nicht als RT1-Rechenstoff belegt.
5. Die SS2025-Klausurgleichung in R7 führt mit positiven Parametern wegen des gegebenen Vorzeichens zu einem negativen Dämpfungskoeffizienten im Nenner. Das Programm darf dies nicht stillschweigend korrigieren.

--- NOTEBOOKLM-PROMPT ---

Prüfe folgende Fragen ausschließlich anhand der hochgeladenen offiziellen Regelungstechnik-Quellen:

1. Wird der Anfangswertsatz der Laplace-Transformation irgendwo ausdrücklich eingeführt oder in einer Aufgabe verwendet?
2. Gibt es eine offizielle Rechenaufgabe zur Polynomdivision einer unechten rationalen Funktion oder zur inversen Laplace-Transformation mit Dirac-Ableitungen?
3. Gibt es außer dem Faltungssatz im Skript eine konkrete Übungs- oder Klausuraufgabe, in der eine Faltung im Zeitbereich tatsächlich berechnet werden muss?
4. Ist das Vorzeichen des Terms \(d_K\dot\phi_G\) in SS2025 Aufgabe 1d und der daraus resultierende Nenner \(m_Kls^2-d_Ks+g(m_K+m_G)\) in Aufgabenstellung und Musterlösung identisch?

Antworte kurz und eindeutig. Belege jede Aussage mit kurzem direkten Zitat, Dokumentname und Seitenzahl oder genauer Fundstelle. Zeige Widersprüche. Wenn keine eindeutige Antwort möglich ist, sage das ausdrücklich.

--- ENDE ---
