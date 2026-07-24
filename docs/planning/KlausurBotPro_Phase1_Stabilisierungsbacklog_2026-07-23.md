# KlausurBotPro – Phase-1-Stabilisierungsbacklog

**Stand:** 23.07.2026  
**Zielrelease:** `v0.1.1-exam`  
**Ausgangsstand:** `main` nach Merge des AI Operator Manuals  
**Planungsquelle:** `KlausurBotPro_Abschlussbericht_Gesamtkonzept(1).md`  
**Zweck:** Vor neuen Funktionen die vorhandenen klausurrelevanten Workflows stabilisieren, irreführende Ausgaben korrigieren und einen belastbaren Prüfungsstand festhalten.

---

# 1. Scope von Phase 1

Phase 1 enthält ausschließlich:

- bestätigte oder gezielt zu reproduzierende Fehler,
- klausurrelevante Ausgabekorrekturen bestehender Workflows,
- begrenzte Eingabe- und Zielsteuerung,
- Referenztests,
- Aktualisierung des AI Operator Manuals,
- Release `v0.1.1-exam`.

Nicht Teil von Phase 1:

- Pol-Nullstellen-Diagramm,
- Parametergebiet aus fertigen Bedingungen,
- Standard-Rückführungsworkflow,
- Linearisierung,
- MIMO-Assistent,
- Bode-Diagramm-Deskriptor,
- allgemeine Ergebnis- oder Projektverwaltung.

---

# 2. Schweregrade

- **S0:** fachlich falsches oder gefährlich irreführendes Ergebnis.
- **S1:** wichtiger Klausurworkflow nicht zuverlässig oder nicht sicher abschreibbar.
- **S2:** deutlicher Mangel bei Rechenweg, Bedienung, LaTeX oder Darstellung.
- **S3:** geringer Komfort- oder Darstellungsfehler.

# 3. Statusbegriffe

- **BESTÄTIGT:** im GUI-Abnahmetest beobachtet und im Bericht eindeutig beschrieben.
- **REPRO NÖTIG:** Bericht nennt das Problem, aber exakte Eingabe oder Screenshot muss vor Codex-Auftrag noch zugeordnet werden.
- **VERBESSERUNG:** kein mathematischer Fehler, aber klar definierte klausurrelevante Anforderung.
- **ZURÜCKGESTELLT:** nicht Teil des ersten Releases.

---

# 4. Referenzfälle

| Test-ID | Quelle | Aufgabe / Fall | Hauptworkflow |
|---|---|---|---|
| REF-TD-01 | Probeklausur | \(2\ddot y+4\dot y=u\), Anfangswerte, \(u(t)=te^{8t}\) | Zeitbereich |
| REF-DGL-01 | SS 2025 | Aufgabe 1d | DGL → Übertragungsfunktion |
| REF-SS-01 | WS 2025/26 | Aufgabe 1d | Zustandsstabilität |
| REF-HUR-01 | SS 2025 | Aufgabe 4b | Hurwitz, zwei Parameter |
| REF-HUR-02 | WS 2025/26 | Aufgabe 4b | Hurwitz, zwei Parameter |
| REF-FREQ-01 | WS 2025/26 | Aufgabe 2c–2e | Bode / Standardglieder |
| REF-NYQ-01 | SS 2025 | Aufgabe 3e | Nyquist |
| REF-NYQ-02 | WS 2025/26 | Parameter-Nyquist | Nyquist / Verstärkungsbereich |
| REF-REG-01 | SS 2025 | Aufgabe 2e | P-Auslegung über Phasenreserve |
| REF-REG-02 | SS 2025 | Aufgabe 4d | Ziegler–Nichols offen |
| REF-REG-03 | WS 2025/26 | Aufgabe 4c | Cohen–Coon |
| REF-TF-01 | WS 2025/26 | Aufgabe 3d | Pole, Nullstellen, Systemvergleich |

---

# 5. Backlog

## KBP-P1-001 – Zeitbereich: Analyseziel und primäres Endergebnis

**Status:** BESTÄTIGT  
**Schweregrad:** S1  
**Modul:** Zeitbereich  
**Referenz:** REF-TD-01

### Ist

- Die App rechnet weiter bis \(y(t)\), obwohl in der Aufgabe nur \(Y(s)\) verlangt sein kann.
- Die angezeigte gesuchte Größe kann von der Aufgabenstellung abweichen.
- \(Y(s)\) wird nicht zuverlässig als primäres Endergebnis umrahmt.
- Nicht verlangte Folgeschritte verdrängen die bepunktete Zielgröße.

### Soll

Der Nutzer kann mindestens zwischen folgenden Analysezielen wählen:

1. nur transformierte Bildgleichung,
2. nur \(Y(s)\),
3. \(Y(s)\) und Partialbruchzerlegung,
4. vollständige Zeitantwort.

### Akzeptanzkriterien

- Bei Analyseziel „nur \(Y(s)\)“ endet der Hauptrechenweg nach dem Auflösen nach \(Y(s)\).
- \(Y(s)\) ist eindeutig als Endergebnis markiert.
- PBZ und \(y(t)\) werden nicht als Hauptlösung ausgegeben.
- Gegeben, Gesucht und Endergebnis stimmen überein.
- Bestehende vollständige Zeitantwort bleibt bei entsprechendem Ziel verfügbar.
- REF-TD-01 besteht in beiden Modi:
  - nur \(Y(s)\),
  - vollständige Zeitantwort.

### Vermutete Ursache

Workflow liefert einen vollständigen Ergebnisbaum, Presenter priorisiert jedoch nicht nach gewähltem Analyseziel.

---

## KBP-P1-002 – Zeitbereich: dynamische Eingabefelder und eindeutige Koeffizienten

**Status:** BESTÄTIGT  
**Schweregrad:** S2  
**Modul:** Zeitbereich  
**Referenz:** REF-TD-01, REF-DGL-01

### Ist

- Bei direkter Eingabe von \(U(s)\) bleibt ein irreführendes Amplitudenfeld sichtbar.
- Das eigentliche Feld für \(U(s)\) ist nicht eindeutig genug.
- \(a_1\) und \(a_2\) sind leicht vertauschbar.
- Ungültige Eingaben führen nur zu „Eingabe ungültig“.

### Soll

- Nicht benötigte Felder werden im gewählten Modus ausgeblendet oder deaktiviert.
- Beschriftungen nennen die physikalische Bedeutung:
  - \(a_1\): Koeffizient vor \(y'(t)\),
  - \(a_2\): Koeffizient vor \(y''(t)\).
- Direkte Bildbereichseingabe heißt sichtbar „Bildbereichseingang \(U(s)\)“.
- Fehlermeldungen nennen Feld, Problem und ein gültiges Beispiel.

### Akzeptanzkriterien

- Im Modus „Direkte Eingabe \(U(s)\)“ ist kein irrelevantes Amplitudenfeld aktiv.
- REF-TD-01 ist ohne Kenntnis interner Feldlogik eindeutig eingebbar.
- Vertauschte oder ungültige Koeffizienten erzeugen eine feldbezogene Meldung.
- Operator Manual beschreibt die aktualisierte Eingabe.

---

## KBP-P1-003 – Zustandsraum: aufgabenspezifische Stabilitätsausgabe

**Status:** BESTÄTIGT  
**Schweregrad:** S1  
**Modul:** Zustandsraum  
**Referenz:** REF-SS-01

### Ist

- Bei einer reinen Stabilitätsaufgabe werden zusätzliche Größen als „Gesucht“ aufgelistet.
- \(G(s)\) kann am Ende prominenter erscheinen als die Stabilitätsaussage.
- Die explizite Prüfung \(\operatorname{Re}(\lambda_i)<0\) fehlt.
- Der Determinantenschritt ist nicht ausreichend sichtbar.

### Soll

Für Analyseziel „Zustandsstabilität“:

1. \(p_A(s)=\det(sI-A)\),
2. sichtbare Determinantenbildung,
3. Eigenwerte,
4. allgemeines Kriterium,
5. konkrete Realteilprüfung,
6. eindeutige Stabilitätsaussage.

### Akzeptanzkriterien

Für REF-SS-01 wird sichtbar ausgegeben:

\[
p_A(s)=s^2+\frac16s+\frac52
\]

\[
\lambda_{1,2}=-\frac1{12}\pm j\frac{\sqrt{359}}{12}
\]

\[
\operatorname{Re}(\lambda_{1,2})=-\frac1{12}<0
\]

und danach:

\[
\text{asymptotisch stabil}
\]

Nicht verlangte Übertragungsfunktionen erscheinen höchstens als eingeklappte Zusatzanalyse.

---

## KBP-P1-004 – Transferfunktion: Warnungsprovenienz bei Kürzungen

**Status:** REPRO NÖTIG  
**Schweregrad:** vorläufig S1  
**Modul:** Transferfunktion / Zeitbereich  
**Referenz:** Bericht, Kürzungs- und Dynamikwarnungen

### Ist

Warnungen zu „verborgener interner Dynamik“ können auch dann alarmierend erscheinen, wenn Faktoren nur in algebraischen Hilfsausdrücken oder erst im Produkt \(Y(s)=G(s)U(s)\) gekürzt werden.

### Soll

Strikte Unterscheidung:

1. Kürzung innerhalb des Systemmodells \(G(s)\),
2. Kürzung nur in \(Y(s)=G(s)U(s)\),
3. algebraische Reduktion eines allgemeinen Ausdrucks \(F(s)\).

Nur eine Kürzung im Systemmodell darf ohne weitere Prüfung als möglicher verborgener Systemmodus bezeichnet werden.

### Vor Codex noch erforderlich

- exakte Eingabe,
- Screenshot,
- betroffener Workflow,
- tatsächlicher Warntext.

### Akzeptanzkriterien

- Warnung nennt die Herkunft der Kürzung.
- Bei reiner Produkt- oder Hilfsausdruckskürzung wird kein verborgener Systemmodus behauptet.
- Bestehende echte Systemkürzungen bleiben erkennbar.

---

## KBP-P1-005 – Transferfunktion: Rundung und qualitative Polinterpretation

**Status:** BESTÄTIGT / VERBESSERUNG  
**Schweregrad:** S2  
**Modul:** Transferfunktion  
**Referenz:** REF-TF-01

### Ist

- Numerische komplexe Pole können mit unpraktisch vielen Nachkommastellen erscheinen.
- Qualitative Aussagen wie „gedämpft schwingend“ oder „aperiodisch“ fehlen.
- Kurze Aufgaben werden durch technische Zusatzblöcke überladen.

### Soll

- Exakte Pole zuerst.
- Numerische Näherung mit einheitlicher sinnvoller Rundung.
- Kurze, vorsichtige qualitative Interpretation aus der Polstruktur.
- Technische Zusatzinformationen nachrangig.

### Akzeptanzkriterien

Für REF-TF-01:

- Strecke:
  \[
  p_{1,2}=-1\pm j\sqrt2
  \]
  qualitative Aussage: „gedämpft schwingender Anteil“.
- Geschlossener Kreis:
  \[
  p_1=-1,\quad p_2=-3
  \]
  qualitative Aussage: „aperiodisches Verhalten“.
- Vergleich:
  \[
  \text{gedämpft schwingend} \rightarrow \text{aperiodisch}
  \]
- Näherungswerte besitzen keine absurd lange Dezimaldarstellung.

---

## KBP-P1-006 – Bode: gemeinsame logarithmische x-Achse

**Status:** BESTÄTIGT  
**Schweregrad:** S1  
**Modul:** Frequenzbereich  
**Referenz:** REF-FREQ-01

### Ist

Betrags- und Phasendiagramm verwenden teilweise unterschiedliche x-Achsenlimits. Dadurch erscheinen identische Knickfrequenzen an unterschiedlichen horizontalen Positionen.

### Soll

- gemeinsame Frequenzgrenzen,
- identische logarithmische Skalierung,
- identische Ticks,
- identische Pixelposition derselben Frequenz,
- gemeinsames Autoscaling.

### Akzeptanzkriterien

- Betrag und Phase besitzen nach jedem Rechenlauf dieselben x-Grenzen.
- Alle Knick- und Durchtrittsfrequenzen liegen in beiden Plots vertikal übereinander.
- Automatisch ergänzte Frequenzen verändern die beiden Plots konsistent.
- REF-FREQ-01 besteht visuell und in einem automatisierten UI-/Plot-Test.

---

## KBP-P1-007 – Frequenzbereich: kompakte Tabellen und sichere Rasterfehler

**Status:** BESTÄTIGT  
**Schweregrad:** S2  
**Modul:** Frequenzbereich / LaTeX  
**Referenz:** REF-FREQ-01, REF-NYQ-01, REF-NYQ-02

### Ist

- LaTeX kann fast das vollständige numerische Raster exportieren.
- Tabellen laufen über Seiten und sind nicht klausurtauglich.
- Bei zu vielen Rasterpunkten erscheint nur eine technische Fehlermeldung.

### Soll

Standardmäßig nur:

- explizit geforderte Frequenzen,
- Knickfrequenzen,
- Achsenschnittpunkte,
- Durchtritte,
- weitere markante automatisch erkannte Punkte.

Vollraster nur optional.

Fehlermeldung nennt:

- berechnete Punktanzahl,
- Grenzwert,
- problematische Eingabe,
- sicheren Vorschlagswert.

### Akzeptanzkriterien

- Standard-LaTeX enthält eine kompakte Tabelle.
- Vollraster kann optional exportiert werden, verdrängt aber nicht die Hauptlösung.
- Fehlerfall mit zu großem Raster enthält eine konkrete Korrekturanweisung.
- Keine interne Stufenbezeichnung wie `bode_data` im Nutzertext.

---

## KBP-P1-008 – Hurwitz: notwendige und hinreichende Bedingungen explizit

**Status:** BESTÄTIGT  
**Schweregrad:** S1  
**Modul:** Stabilität / Hurwitz  
**Referenz:** REF-HUR-01, REF-HUR-02

### Ist

Die Mathematik ist korrekt, die Ausgabe zeigt aber zu stark Matrix und Determinanten, ohne die explizit bepunktete Trennung der Bedingungen ausreichend hervorzuheben.

### Soll

Verbindliche Reihenfolge:

1. charakteristisches Polynom,
2. Koeffizienten,
3. notwendige Bedingungen,
4. jede notwendige Bedingung einsetzen und lösen,
5. Redundanzen markieren,
6. hinreichende Bedingungen,
7. Determinanten auswerten,
8. Schnittmenge,
9. exaktes Gebiet.

### Akzeptanzkriterien

REF-HUR-01 endet mit:

\[
a>-\frac{20}{9},
\qquad
-\frac{20a}{9}<K<(a+4)(a+5)
\]

REF-HUR-02 endet mit:

\[
a>-\frac{15}{16},
\qquad
-\frac{15a}{4}<K<(2a+3)(2a+5)
\]

Zusätzlich:

- notwendige und hinreichende Bedingungen besitzen eigene Überschriften,
- Redundanzen werden kenntlich gemacht,
- Kursnotation \(Z(s)\), \(N(s)\) wird sichtbar verwendet.

---

## KBP-P1-009 – Reglerauslegung: Kursnotation, Tabellenformel und Gültigkeit

**Status:** BESTÄTIGT / VERBESSERUNG  
**Schweregrad:** S2  
**Modul:** Reglerauslegung  
**Referenz:** REF-REG-01 bis REF-REG-03

### Ist

- Teilweise \(L\) statt \(K_T\).
- Allgemeine Tabellenformel und konkrete Gültigkeitsprüfung sind nicht immer ausreichend sichtbar.
- Strecke und Reglerverstärkung können begrifflich zu nah beieinander liegen.

### Soll

- \(K_T\) als sichtbare Kursnotation.
- Allgemeine Formel vor dem Einsetzen.
- Gültigkeitsbedingung:
  - Formel,
  - Werte,
  - erfüllt / nicht erfüllt.
- \(K_S\) und \(K_{P,R}\) klar getrennt.
- Exakte Form vor Näherungswert.

### Akzeptanzkriterien

- REF-REG-01 bis REF-REG-03 liefern dieselben fachlich korrekten Werte wie bisher.
- Keine Zwischenrundung.
- Kursnotation ist in GUI und LaTeX konsistent.
- Der gesuchte Regler erscheint vor optionalen Zusatzparametern.

---

## KBP-P1-010 – Veralteter Ergebniszustand

**Status:** REPRO NÖTIG  
**Schweregrad:** vorläufig S1  
**Modul:** modulübergreifend

### Ist

Der Abschlussbericht nennt das Risiko, dass alte oder fachlich unpassende Zusatzresultate wie aktuelle Hauptergebnisse wirken können. Der genaue reproduzierbare Fall ist noch nicht im Bericht ausreichend spezifiziert.

### Soll

Nach jeder relevanten Eingabeänderung gilt eindeutig:

- Ergebnis ist aktuell,
- Ergebnis ist veraltet und sichtbar markiert,
- Ergebnis wird gelöscht.

### Vor Codex noch erforderlich

- betroffener Tab,
- genaue Eingabeänderung,
- alter sichtbarer Wert,
- erwartete Reaktion,
- Screenshot.

### Akzeptanzkriterien

- Kein veraltetes Ergebnis kann ohne Warnung als aktuelles Resultat erscheinen.
- Verhalten ist im Operator Manual dokumentiert.

---

## KBP-P1-011 – Globale klausurtaugliche Ergebnisstruktur als begrenzter Pilot

**Status:** VERBESSERUNG  
**Schweregrad:** S2  
**Module:** zunächst Hurwitz und Zeitbereich

### Ziel

Kein sofortiger globaler Presenter-Umbau. Zunächst wird ein kleiner gemeinsamer Ausgabevertrag in zwei starken Workflows erprobt.

### Reihenfolge

1. Gegeben
2. Gesucht
3. Methode
4. Voraussetzungen
5. allgemeine Formel
6. Einsetzen
7. Umformen
8. exaktes Ergebnis
9. numerische Näherung
10. Kontrolle
11. Endergebnisblock

### Akzeptanzkriterien

- Hurwitz und Zeitbereich verwenden dieselbe übergeordnete Struktur.
- Modulspezifische Inhalte bleiben erhalten.
- Keine vollständige Neuschreibung aller Presenter.
- Die Pilotstruktur wird erst nach bestandenen Referenztests auf weitere Module übertragen.

---

## KBP-P1-012 – Transferfunktionstab: Layoutangleichung

**Status:** VERBESSERUNG  
**Schweregrad:** S3  
**Modul:** Transferfunktion

### Ist

Der Tab besitzt andere Abstände, Feldanordnung und Ergebnisstruktur als die übrigen Werkzeuge.

### Soll

Schrittweise Angleichung:

- Eingabekarte,
- Feldbreiten,
- Abstände,
- Aktionsleiste,
- Ergebnisnavigation.

### Akzeptanzkriterien

- Keine Funktionsänderung.
- Keine Regression in Eingabe oder Ergebnisdarstellung.
- Layout wirkt erkennbar konsistenter.
- Nur umsetzen, wenn nach S1-/S2-Punkten ausreichend Budget verbleibt.

---

# 6. Empfohlene PR-Gruppierung

## PR 1 – Zeitbereich: Zielsteuerung und Eingabeklarheit

Enthält:

- KBP-P1-001
- KBP-P1-002
- Pilotanteil von KBP-P1-011

Begründung: gemeinsame UI-, Workflow- und Presenter-Ursache.

## PR 2 – Zustandsraum: Stabilitätsausgabe

Enthält:

- KBP-P1-003

Begründung: klar begrenzter Workflow mit eindeutiger Referenzaufgabe.

## PR 3 – Frequenzbereich: Plotachsen, Tabellen und Fehlertexte

Enthält:

- KBP-P1-006
- KBP-P1-007

Begründung: gemeinsamer Frequenz- und Plot-/Exportbereich.

## PR 4 – Hurwitz: klausurtauglicher Rechenweg

Enthält:

- KBP-P1-008
- Pilotanteil von KBP-P1-011

Begründung: mathematischer Kern bleibt unverändert; Präsentation und Worked Steps werden verbessert.

## PR 5 – Transferfunktion: Warnungen, Rundung und Interpretation

Enthält:

- KBP-P1-004 nach Reproduktion,
- KBP-P1-005

Begründung: gemeinsamer Umgang mit rohem/reduziertem Modell, Polen und Kürzungen.

## PR 6 – Reglerauslegung: Notation und Gültigkeitsprüfung

Enthält:

- KBP-P1-009

## PR 7 – Ergebniszustand

Enthält:

- KBP-P1-010 nach Reproduktion.

## PR 8 – optionale Layoutangleichung

Enthält:

- KBP-P1-012

Nur nach Abschluss aller höheren Prioritäten.

---

# 7. Reihenfolge

1. PR 1 – Zeitbereich
2. PR 3 – Frequenzbereich
3. PR 2 – Zustandsraum
4. PR 4 – Hurwitz
5. Reproduktion KBP-P1-004 und KBP-P1-010
6. PR 5 und PR 7 nur bei bestätigter Reproduktion
7. PR 6 – Reglerauslegung
8. vollständiger Referenztest
9. optional PR 8
10. Release `v0.1.1-exam`

---

# 8. Release-Abnahme

`v0.1.1-exam` wird nur erstellt, wenn:

- keine offenen S0-Probleme bestehen,
- keine bestätigten kritischen S1-Probleme in den getesteten Workflows bestehen,
- alle Referenzfälle erneut geprüft wurden,
- die reale GUI gestartet und bedient wurde,
- LaTeX-Ausgaben stichprobenartig geprüft wurden,
- das AI Operator Manual aktualisiert ist,
- bekannte Restgrenzen dokumentiert sind,
- ein Git-Tag und eine lokale Sicherung existieren.

---

# 9. Noch benötigte Informationen vor den ersten Codex-Aufträgen

Für KBP-P1-004:

- Screenshot der Warnung,
- exakte Eingabe,
- Modul,
- gewünschte fachliche Einordnung.

Für KBP-P1-010:

- Screenshot des veralteten Ergebnisses,
- Eingabe vor und nach der Änderung,
- Modul,
- erwartete Aktualisierung.

Für alle übrigen ersten PRs reichen die im Abschlussbericht dokumentierten Referenzfälle als Spezifikationsbasis; die konkreten GUI-Eingaben werden im jeweiligen GPT-Fachspezifikationsschritt festgeschrieben.

---

# 10. Abschlussstatus vom 24.07.2026

Phase 1 ist fachlich und manuell abgenommen. Der Release-Kandidat heißt
`v0.1.1-exam`. Die Statusangaben in den ursprünglichen Backlog-Einträgen
dokumentieren den Planungsstand vom 23.07.2026; für den Abschluss gilt folgende
Einordnung:

| Einordnung | Punkte | Abschluss |
|---|---|---|
| umgesetzt und abgenommen | KBP-P1-001, -002, -003, -005, -006, -007, -008, -009 und der begrenzte Pilot -011 | In den Phase-1-PRs umgesetzt und anhand der zentralen Referenzfälle in GUI und PDF geprüft. |
| reproduziert und als Nichtfehler eingeordnet | KBP-P1-010 | Kein fachlicher Fehler; eine spätere UX-Verbesserung bleibt möglich. |
| nicht reproduziert | KBP-P1-004 | Die vermutete falsche Warnungsprovenienz wurde nicht reproduziert; ohne reproduzierbaren Fehler erfolgte keine Änderung. |
| bewusst zurückgestellt | KBP-P1-012 und größere neue Funktionen | Eine weitergehende Layoutangleichung sowie neue Workflows bleiben außerhalb von `v0.1.1-exam`. |

Damit werden keine abgeschlossenen Phase-1-Punkte mehr als offen geführt.
Nachfolgende Phasen bleiben fachlich und releasebezogen getrennt.
