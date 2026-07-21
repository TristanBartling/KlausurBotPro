# KlausurBotPro – Implementierungspaket Frequenzsäule

## Durchtrittsfrequenzen, Reserven und Nyquist

**Status:** implementierungsfertige, codefreie Fach- und Schnittstellenspezifikation  
**Nicht enthalten:** Softwarecode, Codex-Prompt, Reglerentwurf, Wurzelortskurve, allgemeine komplexe Analysis  
**Zielbranch:** ein gemeinsamer, streng intern gestufter Implementierungs-PR für Durchtritte, Reserven und Nyquist  
**Quellenstand:** Sommersemester 2026

---

# 1. Aktueller Ausgangspunkt

Der Standardglieder-/Bode-MVP ist implementiert, geprüft und in `main` gemergt. Der neue Branch baut ausschließlich auf diesem Stand auf.

Bereits vorhanden und zwingend zu konsumieren sind:

- sicherer Parser für rationale Übertragungsfunktionen,
- rohe und reduzierte Übertragungsfunktion einschließlich Kürzungsprovenienz,
- exakte Reduktion,
- Pole und Nullstellen mit Vielfachheiten,
- numerischer komplexer Frequenzgang,
- Betrag und dB-Wert,
- Hauptphase und entfaltete Phase,
- logarithmisches Frequenzraster,
- Singularitätssegmente,
- lokale numerische Verfeinerung beziehungsweise lokale Frequenzauswertung,
- numerische Bode-Diagramme,
- Worked Steps,
- Diagnostik,
- LaTeX-Bericht,
- Standardgliederanalyse im bereits unterstützten Teilbereich,
- sortierte Knickereignisse und asymptotische Betragsinformation.

Der neue Branch ist eine **Auswertungs- und Stabilitätsschicht** über diesen Ergebnissen. Er ist keine zweite Frequenzgang-Engine.

Verbindlicher Workflow:

\[
\boxed{
G_0(s)
\rightarrow
\text{vorhandene Frequenzdaten}
\rightarrow
\text{Durchtritte}
\rightarrow
\text{Reserven}
\rightarrow
\text{Nyquist-Zählung}
\rightarrow
\text{geschlossene Stabilität}
}
\]

---

# 2. Verbindliche Quellen und Fundstellen

## 2.1 Technische Referenzen

1. `docs/KlausurBotPro_Architekturplan.md`
   - gemeinsame Domänenobjekte,
   - Verantwortungsgrenzen von Reserven- und Nyquist-Block,
   - Wiederverwendungsmatrix,
   - GUI-, Test- und LaTeX-Strategie.
2. `docs/reference/KlausurBotPro_Fachspezifikation_Nyquist_Reserven.md`
   - fachliche Konventionen,
   - Durchtritts- und Reservenformeln,
   - Nyquist-Vorzeichen,
   - Quellenfehler,
   - Referenzfälle und Grenzfälle.
3. `docs/reference/KlausurBotPro_Fachspezifikation_Standardglieder_Bode.md`
   - vorhandener Frequenzworkflow,
   - negative Verstärkung,
   - Hauptphase versus entfaltete Phase,
   - Knick- und Asymptotikdaten,
   - bereits implementierte Verantwortungsgrenzen.

Die endgültigen technischen Typ- und Dateinamen richten sich nach dem realen Repository. Dieses Dokument legt nur fachlich notwendige Verträge fest.

## 2.2 Fachliche Primärfundstellen

| Inhalt | Verbindliche Fundstelle |
|---|---|
| Ortskurve/Polargang | `skript.pdf`, PDF-S. 69–71, Abschnitt 3.3.2 |
| Amplitudenreserve | `skript.pdf`, PDF-S. 90–92, Algorithmen 3.45–3.46 |
| Phasenreserve | `skript.pdf`, PDF-S. 93–94, Algorithmen 3.47–3.48 |
| Rückführdifferenzfunktion | `skript.pdf`, PDF-S. 132–133, Definition 5.25 |
| Voraussetzungen für offene und geschlossene Pole | `skript.pdf`, PDF-S. 135, Theorem 5.30 und Bemerkung 5.31 |
| Allgemeines Nyquist-Kriterium | `skript.pdf`, PDF-S. 136, Theorem 5.33 |
| Nyquist am offenen Kreis | `skript.pdf`, PDF-S. 137, Theoreme 5.34–5.35 |
| Allgemeiner Nyquist-Fall mit instabilem offenen Kreis | `Regelungstechnik_Übung_Aufg-u-Lösungen.pdf`, PDF-S. 119–122, Übung 10 Aufgabe 1 |
| Vereinfachtes Nyquist und Reserven | ebenda, PDF-S. 119 und 123–125, Übung 10 Aufgabe 2 |
| Verstärkungsparameter | ebenda, PDF-S. 119 und 125–126, Übung 10 Aufgabe 3 |
| Pol im Ursprung beziehungsweise auf imaginärer Achse | `Regelungstechnik_Tutorium_komplett.pdf`, PDF-S. 60–62, Tutorium 11 Aufgabe 1c–d |
| Klausur SS2025 Reserven | `RT_Klausur_SS2025-komplett.pdf`, Aufgabenbogen PDF-S. 6; Lösung PDF-S. 52 |
| Klausur SS2025 Nyquist | ebenda, Aufgabenbogen PDF-S. 8; Lösung PDF-S. 61–63 |
| Klausur WS25/26 Phasenreserve | `RT-Klausur_WS_25_26-komplett.pdf`, Aufgabenbogen PDF-S. 7; Lösung PDF-S. 55 |
| Klausur WS25/26 Nyquist mit Verstärkung | ebenda, Aufgabenbogen PDF-S. 10; Lösung PDF-S. 64–66 |

## 2.3 Verbindlich nicht als Golden-Ergebnis zu übernehmende Quellenfehler

1. Für
   \[
   G(s)=\frac{100}{1+2s}
   \]
   nennt die WS-Musterlösung eine Phasenreserve von \(270^\circ\). Nach Skriptalgorithmus 3.48 und exakter Rechnung gilt ungefähr
   \[
   \omega_g\approx49.9975\,\mathrm{s^{-1}},
   \qquad
   \Delta P\approx90.573^\circ.
   \]
   Der Wert \(270^\circ\) ist kein zulässiges Golden-Ergebnis.
2. Die Punktangaben zu WS25/26 Aufgabe 2c widersprechen sich zwischen Aufgabenbogen und Lösung. Die Punktzahl darf nicht als technisches Abnahmekriterium verwendet werden.
3. Beim WS-Verstärkungsfall darf \(K_R>0\) nicht stillschweigend vorausgesetzt werden. Ohne explizite Domain lautet der mathematische Bereich
   \[
   -\frac13<K_R<\frac{56}{3}.
   \]
4. Für Pole auf der imaginären Achse ist die naive Standardkontur unzulässig. Solange die vorlesungsspezifische Ausweichkontur nicht eindeutig bestätigt ist, muss das MVP sicher abbrechen statt eine Umschlingungszahl zu erfinden.

---

# 3. Wirtschaftliche Paketentscheidung

## 3.1 Variante A – ein gemeinsamer PR

Umfang:

- Durchtrittserkennung,
- Reserven,
- offene Polklassifikation,
- Nyquist-Kurve,
- Umschlingungszahl,
- Stabilitätsaussage,
- enger skalarer Verstärkungsmodus,
- gemeinsame GUI- und LaTeX-Integration.

## 3.2 Variante B – zwei aufeinanderfolgende PRs

1. PR: Durchtritte und Reserven.
2. PR: Nyquist unter Wiederverwendung der Durchtritte und Reserven.

## 3.3 Kritischer Vergleich

| Kriterium | Variante A: gemeinsamer PR | Variante B: zwei PRs |
|---|---|---|
| Repository-Inspektion | einmal vollständig | mindestens zweimal; zweiter PR muss Verträge und GUI erneut erfassen |
| Vertragsarbeit | ein gemeinsamer Ergebnisschnitt; geringere Gefahr divergierender Statusmodelle | Reservenvertrag wird früh fixiert und später häufig erweitert oder adaptiert |
| GUI-Arbeit | ein zusammenhängender Frequenzworkflow | zwei Anbindungen, zwei Konsolidierungen, mehr Umbauwahrscheinlichkeit |
| LaTeX/Worked Steps | ein durchgängiger Bericht | doppelte Renderer- und Reihenfolgearbeit |
| Testwiederholungen | Domain-Gates intern; Vollsuite einmal am Ende | zwei vollständige Integrations- und Regressionsläufe |
| Branchgröße | mittel bis groß | je Branch kleiner |
| Risiko fachlicher Überladung | mittel | niedrig bis mittel |
| Risiko inkonsistenter Konventionen | niedrig, wenn ein gemeinsamer Vertrag zuerst festgelegt wird | höher, besonders bei Status, Phasenästen und Mehrfachdurchtritten |
| Codex-Kontextverlust | gering | deutlich höher zwischen PRs |
| Codex-Verbrauch | geringer Gesamtverbrauch | höher durch zweite Inspektion, Wiederholung und Integrationskorrekturen |
| Prüfbarkeit | gut, wenn interne Abnahmegates verbindlich sind | sehr gut pro Teil-PR |
| Korrekturschleifen | Risiko einer größeren Schleife, aber nur ein Integrationspunkt | kleinere Einzelschleifen, dafür häufiger und mit zusätzlicher Integrationsschleife |
| spätere Wiederverwendung | gemeinsames stabiles Ergebnisobjekt sofort verfügbar | Reserven früh verfügbar; Nyquist-Verträge können danach Änderungen erzwingen |

## 3.4 Relative Aufwandsschätzung

Die folgenden Werte sind Planungsrelationen, keine gemessenen Codex-Zahlen:

- Variante A: Referenzwert \(1.00\).
- Variante B: voraussichtlich \(1.20\) bis \(1.40\) Gesamtaufwand.

Der Mehrverbrauch von Variante B entsteht nicht primär durch Mathematik, sondern durch wiederholte Repository-Inspektion, Vertragsanpassung, GUI-Anbindung, Testläufe und erneutes Einlesen der Fachkonventionen.

## 3.5 Verbindliche Empfehlung

\[
\boxed{\textbf{Variante A: ein gemeinsamer Implementierungs-PR}}
\]

Begründung:

- Der teure Unterbau ist bereits vorhanden.
- Durchtritte und Reserven sind direkte geometrische Teilinformationen der Nyquist-Kurve.
- Nyquist benötigt dieselben Singularitätssegmente, lokalen Evaluatoren, Phasenäste, Diagrammmarkierungen und Statusregeln.
- Zwei PRs sparen wenig Mathematik, erzeugen aber doppelte Integrationsarbeit.

Die Branchgröße wird nicht durch künstliche Aufteilung, sondern durch **verbindliche interne Implementierungs- und Abnahmegates** kontrolliert. Jeder Gate-Zustand muss separat testbar und commitbar sein. Der PR wird erst eröffnet beziehungsweise finalisiert, wenn alle Gates zusammenarbeiten.

---

# 4. Fachlicher Umfang

## 4.1 Durchtritte

Der Branch muss liefern:

1. alle Amplitudendurchtritte
   \[
   |G_0(j\omega_{g,k})|=1
   \quad\Longleftrightarrow\quad
   L(\omega_{g,k})=0\,\mathrm{dB},
   \]
2. alle relevanten Phasendurchtritte auf der entfalteten Phase
   \[
   \varphi_u(\omega_{p,k})=-180^\circ-360^\circ m_k,
   \qquad m_k\in\mathbb Z,
   \]
3. Kreuzungsrichtung:
   - aufwärts,
   - abwärts,
   - tangentiale Berührung,
4. Residuum und numerische Qualitätsinformation,
5. vollständige geordnete Listen statt eines einzigen Bibliothekswertes,
6. Kennzeichnung, ob die Liste global vollständig oder nur im untersuchten Band vollständig ist.

## 4.2 Reserven

Für jeden Amplitudendurchtritt:

\[
\boxed{\Delta P_k=180^\circ+\varphi_u(\omega_{g,k})}.
\]

Für jeden Phasendurchtritt:

\[
\boxed{\Delta A_{k,\mathrm{dB}}=-L(\omega_{p,k})},
\]

\[
\boxed{A_{R,k}=10^{\Delta A_{k,\mathrm{dB}}/20}
=\frac1{|G_0(j\omega_{p,k})|}}.
\]

Optional, aber eindeutig benannt:

\[
\boxed{\Delta A_{k,\mathrm{add}}=1-|G_0(j\omega_{p,k})|}.
\]

Die additive lineare Reserve darf weder `gain margin` noch `Verstärkungsfaktorreserve` heißen.

Negative Reserven bleiben negativ. Eine negative Phasenreserve darf niemals modulo \(360^\circ\) in einen großen positiven Winkel umgewandelt werden.

Bei mehreren Durchtritten werden alle Einzelwerte gespeichert. Eine zusammenfassende kritische Kennzahl ist nur Zusatzinformation und kein Ersatz für die Liste oder das vollständige Nyquist-Kriterium.

## 4.3 Nyquist

Der Branch muss liefern:

- kritischer Punkt \(-1+j0\),
- Klassifikation der offenen Pole,
- Anzahl offener RHP-Pole \(P\),
- Erkennung von Polen auf der imaginären Achse einschließlich Ursprung,
- vollständige Nyquist-Kurve für unterstützte reelle rationale Systeme,
- positive und negative Frequenzhälfte mit korrekter Orientierung,
- Erhaltung aller Kurvenunterbrechungen,
- Netto-Umschlingungszahl mit Projektkonvention,
- Anzahl geschlossener RHP-Pole \(Z\),
- allgemeines Nyquist-Kriterium,
- vereinfachtes Nyquist-Kriterium nur bei erfüllten Voraussetzungen,
- Stabilitätsaussage des geschlossenen Kreises,
- kritischer Treffer oder numerisch uneindeutige Nähe zu \(-1\),
- Konsistenz mit Bode-Durchtritten und negativen Realachsenschnitten.

## 4.4 Verbindliche Nyquist-Konvention

- \(P\): Anzahl offener Pole mit \(\Re(s)>0\).
- \(N_{\mathrm{cw}}\): Nettozahl der Umschlingungen von \(-1\) im Uhrzeigersinn; Uhrzeigersinn ist positiv.
- \(Z\): Anzahl geschlossener Pole mit \(\Re(s)>0\).

\[
\boxed{Z=P+N_{\mathrm{cw}}}.
\]

Geschlossene asymptotische Stabilität:

\[
\boxed{Z=0\iff N_{\mathrm{cw}}=-P}.
\]

Intern darf gegen den Uhrzeigersinn positiv gezählt werden. Dann ist vor Ausgabe zwingend umzurechnen:

\[
N_{\mathrm{cw}}=-N_{\mathrm{ccw}}.
\]

## 4.5 Vollständiges und vereinfachtes Nyquist-Kriterium

**Vollständig:**

- offene RHP-Pole dürfen vorhanden sein,
- \(P\) muss bekannt sein,
- Kurve darf den kritischen Punkt nicht treffen,
- keine unbehandelten Pole auf der imaginären Achse,
- Stabilität aus \(Z=P+N_{\mathrm{cw}}\).

**Vereinfacht:**

Nur zulässig, wenn:

- \(P=0\),
- keine Pole auf der imaginären Achse,
- Nyquist-Kurve vollständig und eindeutig ist.

Dann gilt:

\[
\boxed{\text{stabil}\iff N_{\mathrm{cw}}=0}
\]

unter zusätzlicher Bedingung, dass \(-1\) nicht getroffen wird.

Ein instabiler offener Kreis darf nicht mit dem vereinfachten Kriterium beurteilt werden.

## 4.6 Enger skalarer Verstärkungsparameter

Der empfohlene Branch enthält einen **engen, wirtschaftlichen Parameterfall**:

\[
G_0(s,K)=K\,\bar G_0(s),
\qquad K\in D_K\subseteq\mathbb R,
\]

mit explizit eingegebener reeller Domain \(D_K\).

Unterstützt werden:

- positive und negative Verstärkung,
- kritische Verstärkungswerte,
- Stabilitätsintervalle auf der vorgegebenen reellen Domain,
- offene Randpunkte bei kritischem Treffer,
- keine unsichtbare Annahme \(K>0\).

Nicht unterstützt werden im Branch:

- Parameter in mehreren Koeffizienten von Zähler und Nenner,
- zwei freie Parameter,
- allgemeine symbolische Ungleichungssysteme,
- Totzeitparameter,
- allgemeine Reglerstrukturparameter.

---

# 5. Nicht-Umfang

Ausdrücklich nicht zu implementieren:

- neuer Parser,
- neue rationale Transferfunktionsklasse,
- erneute exakte Reduktion,
- erneute Pol-/Nullstellenberechnung,
- zweite Frequenzgangberechnung,
- zweite Phasenentfaltung,
- eigenes Bode-Raster,
- künstliche Wiederverbindung von Singularitätssegmenten,
- vollständige Nyquist-Ausweichkontur für imaginärachsige Pole,
- mehrfach eingerückte Konturen,
- allgemeine Totzeit-Stabilitätsintervalle,
- biproperes oder unechtes allgemeines Nyquist mit Hochfrequenzbogen,
- komplexe Systemkoeffizienten ohne Konjugiertensymmetrie,
- MIMO-Nyquist,
- allgemeiner Parameterlöser,
- Reglerauslegung,
- Lead-/Lag-/PID-Auslegung,
- Wurzelortskurve,
- allgemeine Argumentprinzip- oder Residuensatz-Engine,
- interaktiver Ortskurveneditor,
- Animationen oder 3D-Plots.

---

# 6. Eingabe- und Ergebnisverträge

## 6.1 Konsumierte vorhandene Ergebnisse

Der Branch erhält mindestens:

### Transferfunktionsanalyse

- rohe Übertragungsfunktion,
- reduzierte Übertragungsfunktion,
- Zähler und Nenner,
- Kürzungsprotokoll beziehungsweise entfernte Faktoren,
- Pole und Nullstellen mit Vielfachheiten,
- Real-/Komplexkoeffizientenstatus,
- Properness-/Realisierbarkeitsstatus,
- Diagnosen und Annahmen.

### Frequenzantwort

- geordnete stetige Frequenzsegmente,
- Frequenzen \(\omega_i>0\),
- komplexe Werte \(G_0(j\omega_i)\),
- Betrag,
- dB-Wert,
- Hauptphase,
- entfaltete Phase,
- Singularitätsgrenzen,
- verwendetes Frequenzband,
- vorhandene lokale Verfeinerungen,
- aufrufbare lokale Auswertung für zusätzliche Frequenzen.

### Bode-/Standardgliederinformationen

- sortierte Knickereignisse,
- asymptotische Anfangs- und Endsteigungen,
- bekannte Hochfrequenzordnung,
- negative Gesamtverstärkung beziehungsweise tatsächliche komplexe Phasenlage,
- vorhandene Information zur Bandvollständigkeit.

Die Standardgliederanalyse ist Hilfsinformation. Durchtritte werden aus dem exakten numerischen Frequenzgang bestimmt, nicht aus asymptotischen Geraden.

## 6.2 Neue unabhängige Domänenobjekte

Die fachlichen Rollen müssen getrennt gespeichert werden. Ein monolithisches Ergebnisobjekt mit optionalen Zahlenfeldern ist unzulässig.

### A. Durchtrittsobjekt

Pflichtfelder:

- Typ: Amplituden- oder Phasendurchtritt,
- Frequenz \(\omega\),
- Frequenzeinheit,
- Segment-ID,
- komplexer Frequenzwert,
- Betrag und dB,
- Hauptphase,
- entfaltete Phase,
- bei Phasendurchtritt: Astindex \(m\) und Ziellinie,
- Kreuzungsrichtung,
- Erkennungsart: exakter Rastertreffer, Vorzeichenwechsel oder tangential,
- Residuum,
- Verfeinerungsintervall,
- Qualitätsstatus,
- Bandvollständigkeitsstatus,
- Provenienz.

### B. Durchtrittsanalyse

Pflichtfelder:

- geordnete Liste aller Amplitudendurchtritte,
- geordnete Liste aller Phasendurchtritte,
- Anzahl je Typ,
- analysierte Segmente,
- nicht analysierbare Segmente,
- Vollständigkeitsstatus,
- Diagnosen.

### C. Reserveneintrag

Pflichtfelder:

- referenzierter Durchtritt,
- Reserventyp,
- numerischer Wert,
- Einheit,
- Formelrolle,
- Status,
- geometrischer Wert versus Stabilitätsinterpretation,
- zugehöriger komplexer Punkt,
- Qualitätsinformation.

Phasenreserve, Amplitudenreserve in dB, Verstärkungsfaktorreserve und additive lineare Differenz sind getrennte Felder beziehungsweise Einträge.

### D. Reservenanalyse

Pflichtfelder:

- Phasenreserve je Amplitudendurchtritt,
- Amplitudenreserve je Phasendurchtritt,
- Faktorreserve je Phasendurchtritt,
- optionale additive lineare Reserve,
- Mehrfachdurchtrittsstatus,
- geometrisch kritischster Eintrag,
- Interpretierbarkeitsstatus,
- Diagnosen.

### E. Offene Polklassifikation

Pflichtfelder:

- LHP-Pole,
- RHP-Pole,
- imaginärachsige Pole,
- Pole im Ursprung,
- Vielfachheiten,
- \(P\),
- Klassifikationsmethode,
- numerische Abstandsinformation zur imaginären Achse,
- Eindeutigkeitsstatus,
- Kürzungswarnungen.

Ein Pol nahe der imaginären Achse darf nicht zwangsweise als LHP oder RHP klassifiziert werden. In diesem Fall ist die Klassifikation `ambiguous`.

### F. Nyquist-Zählung

Pflichtfelder:

- verwendete Kurvensegmente in Konturreihenfolge,
- kritischer Punkt,
- minimale Distanz zu \(-1\),
- Frequenz beziehungsweise Segment der minimalen Distanz,
- interne Gegen-Uhrzeigersinn-Zahl, falls verwendet,
- ausgegebene Uhrzeigersinn-Zahl \(N_{\mathrm{cw}}\),
- primäre Zählmethode,
- unabhängige Kontrollmethode,
- Differenz beider Methoden,
- Kurvenschlussstatus,
- Bandvollständigkeit,
- kritischer-Treffer-Status,
- numerische Qualität,
- Diagnosen.

### G. Stabilitätsaussage

Pflichtfelder:

- \(P\),
- \(N_{\mathrm{cw}}\),
- \(Z\), sofern bestimmbar,
- verwendetes Kriterium: vollständig oder vereinfacht,
- Voraussetzungen erfüllt/nicht erfüllt,
- Ergebnisstatus,
- Textaussage,
- optional unabhängige Polgegenprobe,
- Widerspruchsdiagnose.

### H. Skalarer Verstärkungsbereich

Pflichtfelder:

- Basisübertragungsfunktion \(\bar G_0\),
- explizite Domain \(D_K\),
- kritische Verstärkungswerte,
- Herkunft jedes Wertes,
- offene/geschlossene Randklassifikation,
- geprüfte Intervalle,
- Testwert je Intervall,
- \(P\), \(N_{\mathrm{cw}}\), \(Z\) je Intervall,
- stabile Intervallvereinigung,
- Vollständigkeitsstatus,
- Diagnosen.

## 6.3 Exakt erforderliche Berechnungen

Soweit Eingabestruktur und vorhandener Kern dies erlauben, sind exakt zu halten:

- rohe und reduzierte Übertragungsfunktion,
- Pol-/Nullstellenprovenienz,
- feste Formeln für Reserven,
- kritischer Punkt \(-1\),
- Phasenlinien \(-180^\circ-360^\circ m\),
- Beziehung \(Z=P+N_{\mathrm{cw}}\),
- exakte RHP-Polzahl bei exakt klassifizierbaren Polen,
- einfache symbolische Durchtrittsgleichungen niedriger Ordnung nur als Zusatz,
- kritische Verstärkungswerte, wenn aus einem exakten Realachsenschnitt direkt ableitbar,
- Intervallgrenzen des engen Skalarparameters, sofern exakt verfügbar.

## 6.4 Numerisch zulässige Berechnungen

Numerisch erfolgen dürfen:

- Durchtrittsfrequenzen,
- lokale Nullstellensuche,
- tangentiale Berührungen,
- Phase und Betrag am verfeinerten Punkt,
- minimale Distanz zu \(-1\),
- Nyquist-Umschlingungszahl,
- Kurvenverfeinerung,
- Intervalleinstufung im Skalarparameterfall,
- Plotkoordinaten.

Numerische Ergebnisse benötigen Residuum, Toleranzbezug und Status. Eine nackte Gleitkommazahl ist kein vollständiges Domänenergebnis.

---

# 7. Algorithmen

# 7.1 Gemeinsame Vorprüfung

1. Übernehme rohe und reduzierte Übertragungsfunktion.
2. Prüfe Realwertigkeit der Koeffizienten.
3. Übernehme Pole und klassifiziere sie in LHP, RHP und imaginäre Achse.
4. Prüfe Pol im Ursprung separat.
5. Prüfe Properness.
6. Prüfe gekürzte RHP- oder imaginärachsige Faktoren in der Rohform.
7. Übernehme Frequenzsegmente unverändert.
8. Prüfe, ob der lokale Evaluator verfügbar ist.
9. Prüfe Frequenzeinheit; intern ausschließlich \(\mathrm{rad/s}\).
10. Prüfe, ob die entfaltete Phase segmentweise vorliegt.
11. Setze die zulässigen Teilfunktionen:
    - Bode-Durchtritte möglich,
    - Reserven geometrisch möglich,
    - Reserven stabilitätsinterpretierbar,
    - Nyquist-Zählung möglich,
    - vereinfachtes Nyquist möglich,
    - Parameteranalyse möglich.

Abbruch vor der eigentlichen Analyse, wenn grundlegende Eingaben inkonsistent sind.

## 7.2 Erkennung von Amplitudendurchtritten

Definiere auf logarithmischer Frequenzachse

\[
x=\ln\omega,
\qquad
f_g(x)=L(e^x).
\]

Für jedes stetige Frequenzsegment separat:

1. **Exakte Rastertreffer:**
   - akzeptiere einen Rasterpunkt als Kandidat, wenn \(|L_i|\le\varepsilon_{\mathrm{hit,dB}}\),
   - erzeuge nicht zusätzlich links und rechts denselben Durchtritt.
2. **Vorzeichenwechsel:**
   - finde jedes benachbarte Paar mit \(L_iL_{i+1}<0\),
   - das Paar bildet eine Klammer.
3. **Tangentiale Kandidaten:**
   - suche lokale Minima von \(|L|\) beziehungsweise \(L^2\),
   - Kandidat nur, wenn das Minimum unter einer großzügigeren Kandidatenschwelle liegt,
   - ein fehlender Vorzeichenwechsel ist kein Grund, den Kandidaten zu verwerfen.
4. **Interpolation:**
   - lineare oder sekantenartige Interpolation auf \(x=\ln\omega\) darf nur einen Startwert liefern,
   - das interpolierte Ergebnis ist nie das Endergebnis.
5. **Geklammerte Verfeinerung:**
   - bei Vorzeichenwechsel robustes geklammertes Nullstellenverfahren,
   - keine ungeklammerte Newton-Iteration als alleiniger Weg.
6. **Tangentiale Verfeinerung:**
   - beschränkte Minimierung von \(f_g^2\),
   - anschließend lokale Frequenzauswertung,
   - Akzeptanz nur bei Residuum innerhalb Endtoleranz.
7. **Verifikation:**
   - Frequenz mit vorhandenem Evaluator neu auswerten,
   - gleichzeitig prüfen:
     \[
     |L(\omega_g)|\le\varepsilon_{\mathrm{dB}},
     \qquad
     \big||G(j\omega_g)|-1\big|\le\varepsilon_{|G|}.
     \]
8. **Richtung:**
   - aus lokalen Werten links/rechts oder lokaler Ableitung bestimmen,
   - `rising`, `falling` oder `tangent`.
9. **Deduplizierung:**
   - Kandidaten mit ausreichend kleiner relativer Frequenzdistanz und gleichem Segment zusammenführen,
   - besseren Residuenkandidaten behalten.
10. **Sortierung:**
    - aufsteigend nach \(\omega\), dann nach Segment.

Durchtritte dürfen niemals über Segmentgrenzen hinweg gesucht werden.

## 7.3 Erkennung von Phasendurchtritten

Für jedes stetige Segment der entfalteten Phase:

1. Bestimme
   \[
   \varphi_{\min},\quad\varphi_{\max}.
   \]
2. Ermittle alle ganzzahligen \(m\), für die
   \[
   \varphi_m=-180^\circ-360^\circ m
   \]
   im segmentweisen Wertebereich liegt.
3. Für jedes Niveau definiere
   \[
   f_{p,m}(x)=\varphi_u(e^x)-\varphi_m.
   \]
4. Erfasse exakte Rastertreffer, Vorzeichenwechsel und tangentiale Kandidaten analog zur Amplitudenanalyse.
5. Verfeinere lokal auf logarithmischer Frequenzachse.
6. Werte den komplexen Frequenzgang erneut aus.
7. Akzeptiere nur, wenn gleichzeitig:
   \[
   |\varphi_u(\omega_p)-\varphi_m|\le\varepsilon_\varphi,
   \]
   \[
   |\Im G(j\omega_p)|\le\varepsilon_I,
   \qquad
   \Re G(j\omega_p)<0.
   \]
8. Ein positiver Realachsenschnitt ist kein Phasendurchtritt im Sinn der Reserve.
9. Phase bei \(G(j\omega)=0\) ist undefiniert; dort kein Durchtritt erzeugen.
10. Asymptotisches Annähern an ein Niveau bei \(\omega\to\infty\) ist keine endliche Phasendurchtrittsfrequenz.

Der Astindex \(m\) ist Pflichtausgabe. Eine Suche nur nach der Hauptphasenlinie \(-180^\circ\) ist unzulässig.

## 7.4 Bandvollständigkeit

Nach jeder Durchtrittssuche ist zu entscheiden:

- `exhaustive`: Weitere Durchtritte außerhalb des Bandes sind fachlich ausgeschlossen.
- `band_limited_not_exhaustive`: Weitere Durchtritte können nicht ausgeschlossen werden.
- `segment_incomplete`: Ein Teil des gewünschten Bands war wegen Singularität oder fehlender Daten nicht analysierbar.

Ein globaler Vollständigkeitsnachweis darf sich stützen auf:

- exakte rationale Hochfrequenzordnung,
- vorhandene Standardglieder-/Asymptotikdaten,
- monotone Endentwicklung, wenn sie zuverlässig nachgewiesen ist,
- automatische Banderweiterung mit dem vorhandenen Evaluator.

Bei Totzeit oder fortgesetzter Phasenrotation ist eine endliche Phasendurchtrittsliste grundsätzlich bandbegrenzt, sofern kein zusätzlicher globaler Beweis geführt wird.

## 7.5 Reservenberechnung

### Phasenreserve

Für jeden Amplitudendurchtritt:

1. übernehme \(\omega_{g,k}\),
2. werte die entfaltete Phase am verfeinerten Punkt aus,
3. berechne
   \[
   \Delta P_k=180^\circ+\varphi_u(\omega_{g,k}),
   \]
4. erhalte das Vorzeichen,
5. speichere geometrischen Wert und Interpretationsstatus getrennt.

### Amplitudenreserve

Für jeden Phasendurchtritt:

1. übernehme \(\omega_{p,k}\),
2. werte \(L_k\) und \(|G_k|\) aus,
3. berechne
   \[
   \Delta A_{k,\mathrm{dB}}=-L_k,
   \]
4. berechne
   \[
   A_{R,k}=10^{\Delta A_{k,\mathrm{dB}}/20},
   \]
5. kontrolliere unabhängig
   \[
   A_{R,k}\approx\frac1{|G_k|},
   \]
6. berechne additive Differenz nur, wenn die Ausgabe dies ausdrücklich vorsieht.

### Mehrfachfälle

- Alle Werte bleiben erhalten.
- `minimum phase margin` und `minimum positive gain factor` sind optionale Zusammenfassungen.
- Bei mehreren Durchtritten ist die Stabilitätsentscheidung zwingend über Nyquist zu führen.

## 7.6 Offene Polklassifikation

1. Übernehme die Pole aus dem vorhandenen Transferfunktionskern.
2. Nutze exakte Klassifikation, wenn Pole symbolisch eindeutig sind.
3. Sonst klassifiziere mit skalierter Toleranz relativ zur Polgröße und Koeffizientenkondition.
4. Pole mit \(|\Re p|\) innerhalb der Achsentoleranz werden nicht in LHP/RHP gezwungen.
5. Zähle RHP-Pole mit Vielfachheit:
   \[
   P=\sum_{\Re p>0}\operatorname{mult}(p).
   \]
6. Pol im Ursprung erhält zusätzlich eigenes Flag.
7. Gekürzte instabile oder imaginärachsige Faktoren der Rohform erzeugen Pflichtwarnung. Eine reduzierte E/A-Ortskurve darf nicht als Beweis interner Stabilität ausgegeben werden.

## 7.7 Aufbau der Nyquist-Kurve

Unterstützter Standardfall:

- reelle Koeffizienten,
- rational,
- echt rational beziehungsweise sicher gegen null schließend,
- keine Pole auf der imaginären Achse,
- vollständig abgedecktes Frequenzband oder zertifizierte Banderweiterung.

Vorgehen:

1. Verwende positive Frequenzsegmente in aufsteigender Reihenfolge \(0\to\infty\).
2. Für reelle Systeme gilt
   \[
   G(-j\omega)=\overline{G(j\omega)}.
   \]
3. Erzeuge den negativen Frequenzast in Konturreihenfolge \(-\infty\to0\) durch konjugierte, umgekehrte positive Werte.
4. Hänge den positiven Ast \(0\to\infty\) an.
5. \(\omega=0\) darf nur einmal enthalten sein.
6. Singularitätssegmente bleiben getrennt. Es wird keine Gerade zwischen den Segmentenden gezeichnet oder gezählt.
7. Bei strikt properem rationalem System darf der Grenzpunkt \(0\) nur dann als Kurvenschluss verwendet werden, wenn der Hochfrequenzschluss fachlich zertifiziert ist.
8. Bei biproperem oder unechtem System ist die Standardzählung im MVP nicht unterstützt.
9. Ergänze Richtungsinformationen durch wenige Pfeile oder nummerierte Frequenzpunkte; keine Pfeilflut.

## 7.8 Lokale Nyquist-Verfeinerung

Zusätzliche Frequenzen sind einzufügen bei:

- hoher Winkeländerung von \(1+G(j\omega)\),
- hoher geometrischer Krümmung,
- großer Segmentlänge relativ zum Abstand von \(-1\),
- Nähe zum kritischen Punkt,
- Einheitskreisschnitt,
- negativem Realachsenschnitt,
- widersprüchlichen Zählmethoden.

Die vorhandene lokale Frequenzauswertung ist zu verwenden. Es darf keine zweite allgemeine Raster-Engine entstehen.

## 7.9 Umschlingungszahl

Primäre robuste Methode:

1. Verschiebe die Kurve:
   \[
   Q=1+G_0.
   \]
2. Prüfe vor Zählung:
   \[
   \min|Q|>\varepsilon_{\mathrm{critical}}.
   \]
3. Berechne segmentweise die kontinuierliche Argumentänderung von \(Q\) in Konturreihenfolge.
4. Summiere nur über tatsächlich verbundene Kurvenstücke.
5. Für eine vollständig geschlossene unterstützte Kurve:
   \[
   N_{\mathrm{ccw}}=\frac{\Delta\arg Q}{2\pi}.
   \]
6. Runde nur, wenn der Abstand zur nächsten ganzen Zahl unter der festgelegten Zähltoleranz liegt und alle Qualitätsprüfungen bestanden sind.
7. Konvertiere:
   \[
   N_{\mathrm{cw}}=-N_{\mathrm{ccw}}.
   \]

Unabhängige Kontrollmethode:

- orientierte Strahl- beziehungsweise Achsenschnittzählung der verschobenen Kurve oder
- robuste polygonale Winding-Number-Methode um \(-1\), die nicht dieselbe Argumententfaltung wiederverwendet.

Beide Methoden müssen denselben ganzzahligen Wert liefern. Bei Abweichung:

1. lokal verfeinern,
2. erneut zählen,
3. bleibt der Widerspruch bestehen: `numerically_ambiguous`, keine Stabilitätsaussage.

## 7.10 Kritischer Treffer und Nähe zu \(-1\)

1. Suche das Minimum von
   \[
   d(\omega)=|1+G(j\omega)|
   \]
   auf jedem Segment.
2. Verfeinere lokale Minima.
3. Klassifiziere:
   - `critical_hit`, wenn Residuen und lokale Auswertung einen Treffer bestätigen,
   - `near_critical`, wenn der Abstand klein, aber nicht eindeutig null ist,
   - `clear`, wenn ausreichender Abstand besteht.
4. Bei `critical_hit` läuft die Rückführdifferenzfunktion durch null. Der geschlossene Kreis ist nicht asymptotisch stabil; eine gewöhnliche Winding-Zahl darf nicht durch blindes Runden erzeugt werden.
5. Bei `near_critical` ist die Stabilitätsaussage bis zur erfolgreichen Verfeinerung auszusetzen.

## 7.11 Stabilitätsaussage

Wenn alle Voraussetzungen erfüllt sind:

1. übernehme \(P\),
2. übernehme \(N_{\mathrm{cw}}\),
3. berechne
   \[
   Z=P+N_{\mathrm{cw}},
   \]
4. prüfe Ganzzahligkeit und \(Z\ge0\),
5. klassifiziere:
   - \(Z=0\): geschlossener Kreis asymptotisch stabil,
   - \(Z>0\): geschlossener Kreis instabil mit \(Z\) RHP-Polen,
   - kritischer Treffer: nicht asymptotisch stabil; genauer Randstatus,
   - fehlende Voraussetzung: keine Aussage.

Das vereinfachte Nyquist-Kriterium darf nur als vereinfachte Darstellung desselben Ergebnisses angeboten werden, nicht als separater widersprüchlicher Rechenweg.

## 7.12 Skalarer Verstärkungsparameter

Für

\[
G_0(s,K)=K\bar G_0(s)
\]

mit expliziter reeller Domain:

1. Klassifiziere die offenen Pole der Basisfunktion. Für \(K\neq0\) bleibt \(P\) unverändert.
2. Erhalte die Basisprovenienz auch für \(K=0\); die rohe Nennerdynamik darf nicht durch Reduktion auf die Nullfunktion verschwinden.
3. Suche alle Frequenzen mit
   \[
   \Im\bar G_0(j\omega)=0,
   \qquad
   \Re\bar G_0(j\omega)\neq0.
   \]
4. Berechne Kandidaten
   \[
   K_{\mathrm{krit}}=-\frac1{\Re\bar G_0(j\omega)}.
   \]
5. Behalte nur Werte in der eingegebenen Domain.
6. Berücksichtige statische und Grenzfälle, insbesondere \(\omega=0\), sofern definiert.
7. Sortiere alle kritischen Werte und schneide die Domain in offene Intervalle.
8. Wähle je Intervall einen sicheren Testwert.
9. Skaliere vorhandene Frequenzwerte mit \(K\); keine neue Frequenzgang-Engine.
10. Bestimme \(N_{\mathrm{cw}}\), \(Z\) und Stabilität je Intervall.
11. Kritische Randwerte sind für asymptotische Stabilität ausgeschlossen.
12. Für unbeschränkte Intervalle geeignete endliche Testwerte wählen; kein numerisches Unendlich.
13. Negative \(K\) werden über die tatsächliche komplexe Multiplikation behandelt. Keine manuelle Hauptphasenregel.
14. Liefert die endliche Frequenzanalyse keinen Vollständigkeitsnachweis, ist das Parameterergebnis `band_limited_not_exhaustive`.

Dieser Modus ist kein allgemeiner Parameterlöser. Er ist eine eindimensionale Nyquist-Skalierungsanalyse.

---

# 8. Diagnosen und Status

## 8.1 Reserve- und Durchtrittsstatus

Verbindliche Bedeutungen:

- `finite`: endlicher, verifizierter Wert.
- `zero_critical`: Reserve exakt beziehungsweise numerisch bestätigt null.
- `no_gain_crossover`: kein Amplitudendurchtritt.
- `no_phase_crossover`: kein endlicher Phasendurchtritt.
- `formally_infinite`: im unterstützten stabilen Standardfall ist keine endliche kritische Verstärkungsgrenze vorhanden.
- `multiple_crossovers`: mehrere relevante Durchtritte; Einzelwerte liegen vor.
- `not_applicable_open_loop_unstable`: geometrischer Wert kann angezeigt werden, aber nicht als selbstständiger Stabilitätsbeweis.
- `not_applicable_imag_axis_pole`: formale Stabilitätsinterpretation ohne modifizierte Kontur unzulässig.
- `band_limited_not_exhaustive`: weitere Durchtritte oder Windungen außerhalb des Bands möglich.
- `numerically_ambiguous`: Verfeinerung oder unabhängige Kontrollen liefern keine eindeutige Klassifikation.

## 8.2 Pflichtdiagnosen

Mindestens folgende Diagnosen sind vorzusehen:

- `IMAG_AXIS_POLE_MODIFIED_CONTOUR_REQUIRED`
- `POLE_AT_ORIGIN_NYQUIST_COUNT_UNSUPPORTED`
- `OPEN_LOOP_UNSTABLE_MARGINS_GEOMETRIC_ONLY`
- `RHP_CANCELLATION_INTERNAL_STABILITY_NOT_PROVEN`
- `NEAR_IMAG_AXIS_POLE_CLASSIFICATION_AMBIGUOUS`
- `MULTIPLE_GAIN_CROSSOVERS`
- `MULTIPLE_PHASE_CROSSOVERS`
- `NO_GAIN_CROSSOVER`
- `NO_PHASE_CROSSOVER`
- `FREQUENCY_BAND_NOT_EXHAUSTIVE`
- `SINGULAR_SEGMENT_NOT_CONNECTED`
- `TANGENTIAL_CROSSOVER_DETECTED`
- `TANGENTIAL_CANDIDATE_REJECTED_BY_RESIDUAL`
- `NYQUIST_CURVE_NOT_CLOSED`
- `NYQUIST_WINDING_METHODS_DISAGREE`
- `NYQUIST_NEAR_CRITICAL_POINT`
- `NYQUIST_CRITICAL_POINT_HIT`
- `SIMPLIFIED_NYQUIST_NOT_APPLICABLE`
- `BIPROPER_OR_IMPROPER_NYQUIST_UNSUPPORTED`
- `COMPLEX_COEFFICIENT_MIRRORING_UNSUPPORTED`
- `PHASE_UNDEFINED_AT_FREQUENCY_ZERO`
- `SCALAR_PARAMETER_DOMAIN_REQUIRED`
- `SCALAR_PARAMETER_RANGE_NOT_EXHAUSTIVE`
- `SOURCE_REFERENCE_VALUE_REJECTED`

## 8.3 Status statt erfundener Zahlen

Verbindliche Regeln:

- keine PM-Zahl ohne Gain-Crossover,
- keine endliche GM-Zahl ohne Phase-Crossover,
- kein \(N\) bei offener Kurve,
- kein \(Z\) bei uneindeutigem \(N\) oder \(P\),
- keine Stabilitätsaussage bei unbehandeltem imaginärachsigen Pol,
- keine einzelne „maßgebliche“ Reserve bei Mehrfachdurchtritten ohne sichtbare Einzelwerte,
- kein Maximalverstärkungswert, wenn der stabile Bereich nach oben unbeschränkt ist,
- kein Golden-Ergebnis aus einer nachgewiesen fehlerhaften Musterlösung.

---

# 9. Schnittstellen zur vorhandenen Frequenzsäule

## 9.1 Zwingende Wiederverwendung

Nicht duplizieren:

- Parser,
- Transferfunktionsnormalisierung,
- Reduktion,
- Roh-/Reduziert-Provenienz,
- Pole und Nullstellen,
- komplexe Frequenzauswertung,
- Betrag und dB,
- Hauptphase,
- entfaltete Phase,
- Frequenzraster,
- Singularitätssegmentierung,
- lokale Auswertung,
- Bode-Plotgrundlage,
- Standardgliederzerlegung,
- Knickereignisse,
- asymptotische Informationen,
- allgemeine Worked-Step-Infrastruktur,
- Diagnosemechanismus,
- LaTeX-Grundrenderer.

## 9.2 Benötigte neue fachliche Operationen

Unabhängig von späteren technischen Namen werden fachlich benötigt:

1. Durchtritte analysieren.
2. Reserven aus verifizierten Durchtritten bilden.
3. offene Pole klassifizieren.
4. Nyquist-Kurve aus bestehenden Frequenzsegmenten aufbauen.
5. Umschlingungszahl verifizieren.
6. geschlossene Stabilität beurteilen.
7. optional skalaren Verstärkungsbereich analysieren.

Diese Operationen sollen getrennt aufrufbar bleiben. Ein Nutzer oder späterer Reglerauslegungsblock muss Durchtritte und Reserven konsumieren können, ohne zwingend eine Nyquist-Zählung anzufordern.

## 9.3 Verträge für spätere Reglerauslegung

Später wiederverwendbar sind:

- vollständige Gain-Crossover-Liste,
- vollständige Phase-Crossover-Liste,
- Phase und Betrag an jedem Durchtritt,
- PM- und GM-Liste,
- kritischer Durchtritt mit expliziter Auswahlregel,
- Bandvollständigkeitsstatus,
- offene Polklassifikation,
- minimale Distanz zu \(-1\),
- kritische Verstärkungswerte,
- stabile Verstärkungsintervalle,
- Qualitäts- und Diagnosestatus.

Der spätere Reglerauslegungsblock darf diese Daten nicht erneut aus einem Plot ablesen oder separat berechnen.

## 9.4 Unabhängige Kontrollen

Pflichtkontrollen:

1. \(L=0\,\mathrm{dB}\) gegen \(|G|=1\).
2. Phasenlinie gegen \(\Im G=0\) und \(\Re G<0\).
3. \(20\log_{10}A_R=\Delta A_{\mathrm{dB}}\).
4. Bode-Gain-Crossover gegen Nyquist-Einheitskreisschnitt.
5. Bode-Phase-Crossover gegen negativen Realachsenschnitt.
6. Argumentänderung gegen unabhängige polygonale/Strahl-Zählung.
7. Optional: \(Z\) gegen geschlossene Polgegenprobe aus vorhandener Transfer-/Polinfrastruktur.
8. Im Parameterfall: repräsentativer Testwert pro Intervall.

Eine optionale Polgegenprobe ist Kontrolle, nicht Ersatz des Nyquist-Rechenwegs.

---

# 10. GUI- und LaTeX-Integration

## 10.1 Arbeitsbereichsentscheidung

Der vorhandene Frequenzarbeitsbereich wird erweitert. Kein neues top-level Werkzeug ist nötig.

Fachlich notwendige Struktur:

```text
Frequenzanalyse
├── Grunddaten
├── Pole / Nullstellen
├── Standardglieder
├── Bode
├── Durchtritte und Reserven
├── Nyquist
└── Bericht / LaTeX
```

**Durchtritte und Reserven** gehören in den bestehenden Bode-Kontext.  
**Nyquist** benötigt einen eigenen Unterbereich beziehungsweise Tab innerhalb derselben Frequenzanalyse, weil die komplexe Ebene, der kritische Punkt und die Umlaufrichtung fachlich nicht sinnvoll in einen Bode-Plot gepresst werden können.

## 10.2 GUI-Eingaben

Zusätzliche Pflichtoptionen:

- Analyse ein/aus für Durchtritte und Reserven,
- Nyquist-Analyse ein/aus,
- Frequenzband und automatische Banderweiterung,
- Anzeigeeinheit rad/s oder explizit Hz mit Umrechnung,
- Rückkopplungsvorzeichen; Standard nur nach sichtbarer Konvention,
- optionaler Skalarparameter \(K\),
- explizite Parameterdomain,
- Analysemodus: einzelne Verstärkung oder Verstärkungsbereich,
- erweiterte numerische Details ein/aus.

Numerische Toleranzen gehören nicht in den normalen Klausurmodus. Sie können in einem Diagnose-/Expertenbereich sichtbar sein.

## 10.3 Ergebnisdarstellung

Priorität:

1. Stabilitätsaussage mit Voraussetzungen.
2. \(P\), \(N_{\mathrm{cw}}\), \(Z\).
3. kritischer Punkt getroffen/nahe/unkritisch.
4. Durchtritts- und Reserventabelle.
5. Warnungen und Vollständigkeitsstatus.
6. Diagramme.
7. Worked Steps und LaTeX.

Tabellenfelder:

### Amplitudendurchtritte

- Index,
- \(\omega_g\),
- \(G(j\omega_g)\),
- \(\varphi_u\),
- \(\Delta P\),
- Richtung,
- Status.

### Phasendurchtritte

- Index,
- Ast \(m\),
- Ziellinie,
- \(\omega_p\),
- \(G(j\omega_p)\),
- \(L\),
- \(\Delta A_{\mathrm{dB}}\),
- \(A_R\),
- Status.

## 10.4 Notwendige Plot-Erweiterungen

### Bode

Pflicht:

- alle 0-dB-Durchtritte markieren,
- alle relevanten Phasendurchtritte markieren,
- zugehörige Phasenlinien anzeigen,
- nummerierte Marker,
- keine Verbindung über Singularitätslücken,
- Reservewerte in Legende oder Ergebnisbereich, nicht als unlesbare Textwand im Plot.

### Nyquist

Pflicht:

- Real- und Imaginärachse,
- kritischer Punkt \(-1\),
- positive und negative Frequenzhälfte unterscheidbar,
- Richtungsinformation,
- Segmentunterbrechungen,
- nummerierte Einheitskreis- und Realachsenschnitte,
- markierter minimaler Abstand zu \(-1\),
- sinnvolle automatische Nahansicht um \(-1\), ohne Gesamtansicht zu verlieren.

Optionaler Komfort:

- Einheitskreis,
- Hoverwerte,
- manuelle Punktliste,
- frei schaltbare Frequenzbeschriftungen.

Nicht nötig:

- Animation,
- interaktiver Kurveneditor,
- automatische Lehrbuchskizze als eigener zweiter Plot,
- 3D-Darstellung.

## 10.5 Worked Steps

Pflichtreihenfolge:

1. offene Übertragungsfunktion und Rückkopplungskonvention,
2. offene Pole und \(P\),
3. Voraussetzungen und Sonderfälle,
4. gefundene Amplitudendurchtritte,
5. Phasenreserve je Durchtritt,
6. gefundene Phasendurchtritte mit Astindex,
7. Amplitudenreserve und Faktorreserve,
8. Aufbau und Orientierung der Nyquist-Kurve,
9. Umschlingungszahl,
10. \(Z=P+N_{\mathrm{cw}}\),
11. Stabilitätsaussage,
12. unabhängige Kontrollen,
13. Diagnosen.

Nicht alle internen Iterationen der Nullstellensuche gehören in den normalen Rechenweg. Im Diagnosemodus dürfen Klammer, Iterationszahl und Residuum erscheinen.

## 10.6 LaTeX-Bericht

Pflichtinhalt:

- \(G_0(s)\),
- kritischer Punkt,
- offene Pole und \(P\),
- Tabelle aller Durchtritte,
- vollständige Reserveformeln mit eingesetzten Vorzeichen,
- eindeutige Nennung der entfalteten Phase,
- Nyquist-Konvention,
- \(N_{\mathrm{cw}}\),
- \(Z=P+N_{\mathrm{cw}}\),
- Stabilitätsaussage,
- Warnungen bei nicht anwendbaren Fällen,
- Parameterintervalle und Randklassifikation, falls verwendet.

Beispielblock:

\[
|G_0(j\omega_g)|=1
\Rightarrow
\omega_g=\ldots
\]

\[
\Delta P
=180^\circ+\varphi_u(\omega_g)
=180^\circ+(\ldots)^\circ
=\ldots^\circ.
\]

\[
\varphi_u(\omega_p)=-180^\circ-360^\circ m,
\qquad
\Delta A_{\mathrm{dB}}=-L(\omega_p)=\ldots\,\mathrm{dB}.
\]

\[
P=\ldots,
\qquad
N_{\mathrm{cw}}=\ldots,
\qquad
Z=P+N_{\mathrm{cw}}=\ldots.
\]

Bei nicht anwendbaren Fällen wird ein fachlicher Statussatz erzeugt, keine leere Formel und keine Ersatznull.

---

# 11. Priorisierte Referenzfälle

Die vollständigen Herleitungen verbleiben in der Nyquist-/Reserven-Fachspezifikation. Für den Implementierungsbranch gelten folgende Fälle als priorisierte Abnahmebasis.

## F1 – einfacher Reserven- und vereinfachter Nyquist-Fall

**Quelle:** Übung 10 Aufgabe 2, `Regelungstechnik_Übung_Aufg-u-Lösungen.pdf`, PDF-S. 119 und 123–125.

\[
G_0(s)=\frac{2.5(1-s)}{s^2+3s+2}.
\]

Erwartet:

\[
P=0,
\qquad
\omega_p=\sqrt5,
\qquad
G_0(j\omega_p)=-\frac56,
\]

\[
A_R=\frac65,
\qquad
\Delta A_{\mathrm{dB}}\approx1.5836\,\mathrm{dB},
\]

\[
\omega_g=\frac32,
\qquad
\Delta P\approx30.5102^\circ,
\]

\[
N_{\mathrm{cw}}=0,
\qquad
Z=0.
\]

Dieser Fall prüft Durchtritte, beide Reserven, RHP-Nullstelle, vereinfachtes Nyquist und Bode-/Nyquist-Konsistenz.

## F2 – allgemeines Nyquist mit instabilem offenen Kreis

**Quelle:** Übung 10 Aufgabe 1, PDF-S. 119–122.

\[
G_0(s)=\frac{6s}{(s-1)(s-2)}.
\]

Erwartet:

\[
P=2,
\qquad
G_0(\pm j\sqrt2)=-2,
\qquad
N_{\mathrm{cw}}=-2,
\qquad
Z=0.
\]

Vereinfachtes Nyquist muss abgelehnt werden. Geschlossene Polgegenprobe: \(-1,-2\).

## F3 – stabiler offener Kreis, instabiler geschlossener Kreis

**Quelle:** Klausur SS2025 Aufgabe 3e, Aufgabenbogen PDF-S. 8; Lösung PDF-S. 61–63.

\[
G_0(s)=\frac2{s^3+2.3s^2+1.6s+2}.
\]

Erwartet:

\[
P=0,
\qquad
\omega_p=\sqrt{\frac85},
\qquad
G_0(j\omega_p)=-\frac{25}{21},
\]

\[
N_{\mathrm{cw}}=2,
\qquad
Z=2.
\]

Der Abstand zu \(-1\) darf nicht fälschlich als kritischer Treffer klassifiziert werden.

## F4 – mehrere Amplitudendurchtritte

**Abgeleiteter Test aus offiziellem PT2-Standardglied:**

\[
G_0(s)=\frac{0.5}{s^2+0.5s+1}.
\]

Erwartet:

\[
\omega_{g,1}=\frac{\sqrt3}{2},
\qquad
\omega_{g,2}=1,
\]

\[
\Delta P_1=120^\circ,
\qquad
\Delta P_2=90^\circ.
\]

Kein endlicher Phasendurchtritt; Amplitudenreserve formal unendlich. Beide Einheitskreisschnitte müssen im Nyquist-Plot erscheinen.

## F5 – keine Durchtritte

**Abgeleiteter Test aus PT1:**

\[
G_0(s)=\frac{0.5}{1+s}.
\]

Erwartet:

- keine Amplitudendurchtritte,
- keine endlichen Phasendurchtritte,
- PM nicht definiert,
- GM formal unendlich beziehungsweise klar als kein Phasendurchtritt gekennzeichnet,
- keine numerische Ersatznull,
- geschlossener Kreis stabil.

## F6 – Pol im Ursprung und negative Reserven

**Quelle:** Tutorium 11 Aufgabe 1c, `Regelungstechnik_Tutorium_komplett.pdf`, PDF-S. 60–62.

\[
G_0(s)=\frac{25s+60}{10s^3+10s^2+25s}.
\]

Erwartet:

- Pol im Ursprung,
- Nyquist-Standardzählung mit Status `IMAG_AXIS_POLE_MODIFIED_CONTOUR_REQUIRED`,
- \(\omega_p=\sqrt{30/7}\),
- \(G_0(j\omega_p)=-1.4\),
- \(A_R=5/7\),
- \(\Delta A\approx-2.92256\,\mathrm{dB}\),
- \(\omega_g\approx2.29948\),
- \(\Delta P\approx-6.706^\circ\),
- niemals Ausgabe \(353.294^\circ\).

Geometrische Reserven dürfen sichtbar sein; vollständige Nyquist-Stabilität nicht behaupten.

## F7 – skalarer Verstärkungsparameter

**Quelle:** Klausur WS25/26 Nyquist-Aufgabe, Aufgabenbogen PDF-S. 10; Lösung PDF-S. 64–66.

Basisrelation aus der Fachspezifikation:

\[
G_0(j\omega_2)=-\frac{3K_R}{56},
\qquad
\omega_2=\frac{\sqrt{19}}3.
\]

Kritischer Wert:

\[
K_R=\frac{56}{3}.
\]

Vollständiger mathematischer Bereich ohne versteckte Positivitätsannahme:

\[
\boxed{-\frac13<K_R<\frac{56}{3}}.
\]

Bei Domain \(K_R>0\):

\[
\boxed{0<K_R<\frac{56}{3}}.
\]

Beide Domains müssen unterschiedliche, korrekte Ergebnisse liefern.

## F8 – Quellenfehler: falsche 270°-Phasenreserve

**Quelle:** Klausur WS25/26 Aufgabe 2c mit fehlerhafter Musterlösung.

\[
G(s)=\frac{100}{1+2s}.
\]

Erwartet:

\[
\omega_g=\frac{\sqrt{9999}}2\approx49.9975,
\]

\[
\Delta P\approx90.573^\circ.
\]

Explizit verbotenes Golden-Ergebnis:

\[
270^\circ.
\]

## F9 – endliche Amplitudenreserve ohne Phasenreserve

**Quelle:** Skript PDF-S. 91–92, Beispiel zu Algorithmus 3.46.

\[
G_0(s)=\frac{0.4}{(s+1)^4}.
\]

Erwartet:

\[
\omega_p=1,
\qquad
A_R=10,
\qquad
\Delta A=20\,\mathrm{dB},
\]

kein Amplitudendurchtritt und keine Phasenreserve.

---

# 12. Gezielte Tests

## 12.1 Zwingende Domain-Tests

Kleine deterministische Tests ohne GUI:

1. Erkennung eines exakten 0-dB-Rastertreffers.
2. Erkennung eines geklammerten 0-dB-Vorzeichenwechsels.
3. Tangentialer Gain-Crossover ohne Vorzeichenwechsel.
4. Zurückweisung eines tangentialen Scheinkandidaten mit zu großem Residuum.
5. Phasendurchtritt auf Ast \(m=0\).
6. Phasendurchtritt auf Ast \(m\neq0\).
7. Zurückweisung eines positiven Realachsenschnitts.
8. Deduplizierung eng identischer Kandidaten.
9. Keine Verbindung über Segmentgrenze.
10. Mehrere Gain-Crossover in korrekter Reihenfolge.
11. Kein Gain-Crossover mit korrektem Status.
12. Kein Phase-Crossover mit korrektem Status.
13. Negative Phasenreserve bleibt negativ.
14. dB-Reserve und Faktorreserve erfüllen die Umrechnungsidentität.
15. RHP-Polzählung mit Vielfachheit.
16. Pol nahe imaginärer Achse wird `ambiguous`.
17. Aufbau der negativen Frequenzhälfte durch Konjugation und Umkehrung.
18. Winding-Zahl für einfache Kreis-/Polygonkurve mit bekannter Orientierung.
19. Umrechnung interner CCW- in Projekt-CW-Konvention.
20. Winding-Methoden stimmen überein.
21. Kritischer Treffer verhindert Rundung der Winding-Zahl.
22. Offene Kurve verhindert Stabilitätsaussage.
23. Skalarparameter mit positiver und negativer Domain.
24. Unbeschränktes stabiles Parameterintervall ohne erfundenes Maximum.

## 12.2 Integrations- und Workflow-Tests

Pflichtfälle:

- F1: vollständiger einfacher Reserven-/Nyquist-Workflow,
- F2: allgemeines Nyquist mit \(P=2\),
- F3: geschlossener Kreis instabil trotz \(P=0\),
- F4: mehrere Amplitudendurchtritte,
- F5: fehlende Durchtritte,
- F6: Pol im Ursprung mit sicherem Nyquist-Abbruch,
- F7: Parameterdomain,
- F8: Quellenfehler nicht übernommen,
- F9: endliche GM ohne PM.

Mindestens eine Integrationsprüfung muss explizit vergleichen:

- Bode-Amplitudendurchtritt \(\leftrightarrow\) Nyquist-Einheitskreisschnitt,
- Bode-Phasendurchtritt \(\leftrightarrow\) negativer Realachsenschnitt.

## 12.3 Presenter-/LaTeX-Smoke-Tests

Nur notwendige Smoke-Tests:

1. Ein Durchtritt je Typ wird korrekt tabellarisch angezeigt.
2. Mehrfachdurchtritte werden nicht abgeschnitten.
3. Negative Reserve erscheint mit Minuszeichen.
4. `not applicable` erzeugt Textstatus statt `NaN`, 0 oder leeres Feld.
5. LaTeX verwendet entfaltete Phase und korrekte Vorzeichen.
6. LaTeX zeigt \(Z=P+N_{\mathrm{cw}}\).
7. Parameterintervall zeigt offene Grenzen.
8. Quellenfehlerfall rendert etwa \(90.6^\circ\), nicht \(270^\circ\).

## 12.4 Bewusst nicht benötigte Volltests

Nicht für jeden Commit erforderlich:

- vollständige Anwendungssuite,
- alle existierenden Standardgliederfälle,
- alle LaTeX-Dokumentvarianten,
- Pixel-Golden-Tests sämtlicher Plots,
- große zufällige Transferfunktionsmengen,
- allgemeine komplexe Polynom-Fuzztests.

Vollsuite einmal vor finalem Merge; vorher gezielte Domain- und Integrationssuiten.

---

# 13. Grenz- und Fehlerfälle

## 13.1 Negative Gesamtverstärkung

- Keine manuelle Phase `+180°` oder `-180°` auf Basis eines Vorzeichensymbols.
- Maßgeblich ist der tatsächliche komplexe Frequenzwert und dessen segmentweise entfaltete Phase.
- Gain-Crossover bleibt betragsbezogen.
- Phase-Crossover und PM verwenden den tatsächlichen entfalteten Ast.
- Im Parameterfall wird negatives \(K\) durch komplexe Skalierung behandelt.

## 13.2 Mehrere Durchtritte

- alle speichern,
- keine Bibliotheksauswahl „erster“ oder „bester“ übernehmen,
- Kreuzungsrichtung ausgeben,
- Stabilität nicht aus einer einzelnen Reserve folgern.

## 13.3 Begrenztes Frequenzband

- keine globale Aussage ohne Vollständigkeitsnachweis,
- Banderweiterung über vorhandenen Evaluator,
- bei fortgesetzter Totzeitphase `band_limited_not_exhaustive`,
- Randtreffer nicht stillschweigend als vollständiger Durchtritt interpretieren.

## 13.4 Singularitäten

- Segmente bleiben getrennt,
- keine Plotlinie und keine Winding-Kante über die Lücke,
- bei imaginärachsigem Pol Nyquist-MVP abbrechen,
- lokale Bode-Reserven können mit Warnung weiterhin geometrisch berechnet werden, sofern die jeweiligen Frequenzen regulär sind.

## 13.5 RHP-Nullstellen

- sind zulässig,
- verändern Phase und Ortskurve,
- nicht mit RHP-Polen verwechseln,
- kein eigener Abbruch,
- F1 deckt einen nichtminimalphasigen Zählerfaktor ab.

## 13.6 Tangentiale Berührungen

- kein Vorzeichenwechsel erforderlich,
- lokale Minimierung plus Residuenprüfung,
- `tangent` als eigene Richtung,
- tangentiale Berührung des kritischen Punkts ist trotzdem kritisch.

## 13.7 Nähe zum kritischen Punkt

- lokale adaptive Verfeinerung,
- minimale Distanz speichern,
- Winding-Zahl nicht blind runden,
- unabhängige Zählmethode,
- optional geschlossene Polgegenprobe,
- verbleibende Uneindeutigkeit führt zu Status, nicht zu einer behaupteten Stabilität.

## 13.8 Pole auf der imaginären Achse

- Ursprung separat markieren,
- Standard-Nyquist nicht anwenden,
- keine künstliche kleine Ausweichkurve ohne bestätigte Vorlesungskonvention,
- Warnstatus mit klarer Begründung,
- formale Erweiterung außerhalb dieses Branches.

## 13.9 Kürzungen

- reduzierte Ortskurve beschreibt E/A-Verhalten,
- gekürzte RHP- oder imaginärachsige Pole in der Rohform verhindern eine unqualifizierte Aussage zur internen Stabilität,
- Provenienz muss im Ergebnis sichtbar bleiben.

## 13.10 Biproper und unecht

- Hochfrequenzgrenzwert beziehungsweise Hochfrequenzbogen ist nicht automatisch durch den Ursprung geschlossen,
- im MVP `unsupported` oder `not exhaustive`,
- keine künstliche Gerade zum Startpunkt.

---

# 14. Erwarteter Codex-Aufwand

## 14.1 Relative Aufwandsblöcke

| Teil | Zusatzaufwand bei vorhandenem Bode-MVP | Risiko |
|---|---:|---:|
| gemeinsame Verträge und Status | mittel | mittel |
| Amplitudendurchtritte | niedrig bis mittel | niedrig |
| Phasendurchtritte mit Astzuordnung | mittel | mittel |
| Reserven | niedrig | niedrig |
| offene Polklassifikation | niedrig | mittel bei Achsennähe |
| Nyquist-Kurvenaufbau | mittel | mittel |
| robuste Umschlingungszahl plus Kontrollmethode | mittel bis hoch | hoch |
| kritische-Punkt-Verfeinerung | mittel | mittel |
| enger Skalarparameter | mittel | mittel |
| GUI-Integration | mittel | mittel |
| Worked Steps/LaTeX | mittel | niedrig bis mittel |
| gezielte Tests | mittel | niedrig |

## 14.2 Gesamtbewertung

Der Branch ist **mittelgroß**, aber wirtschaftlich sinnvoll. Der größte neue Fachkern ist nicht die Frequenzrechnung, sondern:

- vollständige Durchtrittslisten,
- robuste Winding-Zahl,
- Statuslogik bei nicht anwendbaren Fällen,
- konsistente GUI-/LaTeX-Ausgabe.

Im Vergleich zu zwei getrennten PRs ist mit ungefähr 20–40 % weniger Gesamtaufwand zu rechnen, weil Kontext-, Vertrags-, GUI- und Testwiederholung entfallen. Diese Spanne ist eine Planungsabschätzung, keine Messung.

---

# 15. Risiken und offene Punkte

## 15.1 Höchste Risiken

1. Falsche Orientierung beziehungsweise Vorzeichen der Umschlingungszahl.
2. Blindes Verbinden getrennter Segmente.
3. Hauptphase statt entfalteter Phase.
4. Übersehen tangentialer Durchtritte.
5. Unvollständige Durchtrittsliste wegen zu engem Band.
6. Numerisches Runden einer fast ganzzahligen, aber falschen Winding-Zahl.
7. Verwechslung geometrischer Reserven mit Stabilitätsbeweis bei instabilem offenen Kreis.
8. Verdeckte Annahme \(K>0\).
9. Verlust der Rohmodell-Provenienz bei Kürzungen oder \(K=0\).
10. Übernahme des falschen 270°-Quellenwerts.

## 15.2 Offener fachlicher Punkt

Die konkrete vorlesungsspezifische Ausweichkontur bei einem einfachen Pol auf der imaginären Achse ist in den vorhandenen Quellen nicht ausreichend eindeutig für eine verbindliche Implementierung belegt. Deshalb bleibt sie außerhalb dieses Branches.

--- NOTEBOOKLM-PROMPT ---

Prüfe folgende Frage ausschließlich anhand der hochgeladenen offiziellen Regelungstechnik-Quellen:

Welche genaue Nyquist-Ausweichkontur, Orientierung und Vorzeichenkonvention soll in dieser Vorlesung bei einem einfachen Pol auf der imaginären Achse, insbesondere bei einem Pol im Ursprung, verwendet werden?

Unterscheide klar:
1. Kontur in der s-Ebene,
2. Richtung der Einrückung,
3. Bild der Einrückung in der G-Ebene,
4. Auswirkung auf die Umschlingungszahl,
5. verwendete Vorzeichenkonvention für P, N und Z.

Antworte kurz und eindeutig. Belege jede wesentliche Aussage mit kurzem direkten Zitat, Dokumentname und genauer Seite/Fundstelle. Wenn die Quellen keine vollständige eindeutige Regel enthalten, sage das ausdrücklich und erfinde nichts.

--- ENDE ---

---

# 16. Empfohlene Implementierungsreihenfolge innerhalb des Branches

Der Branch bleibt ein PR, wird aber in folgende interne Gates und logisch getrennte Commits geschnitten.

## Gate 0 – Repository-Bestätigung

- reale vorhandene Typen und Erweiterungspunkte feststellen,
- keine Umbenennung großer bestehender Strukturen,
- aktuelle Tests für Frequenzworkflow einmal ausführen,
- technische Dateinamen erst danach wählen.

**Abnahme:** kurzer interner Mapping-Vermerk zwischen vorhandenen Objekten und den Verträgen dieses Dokuments.

## Gate 1 – gemeinsame Domänenverträge und Status

- Durchtrittsobjekte,
- Reservenobjekte,
- offene Polklassifikation,
- Nyquist-Zählung,
- Stabilitätsaussage,
- Diagnosen.

**Abnahme:** Konstruktion und Serialisierung/Präsentation der Objekte ohne Fachrechnung; keine monolithischen optionalen Zahlenfelder.

## Gate 2 – Durchtrittserkennung

- Amplitudendurchtritte,
- Phasendurchtritte,
- Phasenäste,
- Tangentialfälle,
- Segmenttreue,
- Bandstatus,
- Domain-Tests.

**Abnahme:** F4, F5 und gezielte Tangentialtests.

## Gate 3 – Reserven

- PM je Gain-Crossover,
- GM in dB und Faktor je Phase-Crossover,
- additive lineare Reserve nur benannt,
- Mehrfach- und Fehlstatus,
- Bode-Markierungen,
- Worked Steps.

**Abnahme:** F1, F8, F9; negative Reserve aus F6.

## Gate 4 – offene Polklassifikation und Nyquist-Kurve

- \(P\),
- imaginärachsige Pole,
- negative Frequenzhälfte,
- Konturreihenfolge,
- Segmentunterbrechungen,
- Nyquist-Plot.

**Abnahme:** F2-Kurventopologie; F6 muss sicher abbrechen.

## Gate 5 – Umschlingungszahl und Stabilität

- primäre Winding-Methode,
- unabhängige Kontrollmethode,
- kritische-Punkt-Verfeinerung,
- \(N_{\mathrm{cw}}\),
- \(Z=P+N_{\mathrm{cw}}\),
- vollständiges und vereinfachtes Kriterium.

**Abnahme:** F1, F2 und F3 einschließlich optionaler Polgegenprobe.

## Gate 6 – enger Skalarparameter

- explizite Domain,
- positive und negative Werte,
- kritische Verstärkungen,
- Intervalltests,
- offene Randpunkte,
- unbeschränkte Intervalle.

**Abnahme:** F7 und ein Test ohne endliche obere Grenze.

## Gate 7 – GUI- und LaTeX-Konsolidierung

- Frequenzarbeitsbereich erweitern,
- eigener Nyquist-Tab,
- Ergebnistabellen,
- Diagrammmarker,
- Worked Steps,
- vollständiger Bericht.

**Abnahme:** Presenter-/LaTeX-Smoke-Tests.

## Gate 8 – finale Regression

- alle priorisierten Referenzfälle,
- gezielte alte Bode-Regressionen,
- keine Volltestinflation,
- anschließend einmal vollständige Repository-Suite.

**Merge-Kriterium:**

Der PR ist erst fertig, wenn ein Nutzer von einer vorhandenen Übertragungsfunktion ohne manuelles Ablesen zu folgender belastbarer Ausgabe gelangt:

\[
\boxed{
\text{alle Durchtritte}
+\text{alle Reserven}
+P
+N_{\mathrm{cw}}
+Z
+\text{Stabilitätsaussage}
+\text{Diagramme}
+\text{LaTeX}
}
\]

und alle nicht unterstützten Fälle mit einem korrekten Status statt mit erfundenen Zahlen enden.

---

# 17. Verbindliche Endentscheidung

Das wirtschaftlich beste Paket ist ein gemeinsamer Implementierungs-PR mit intern streng getrennten Gates.

\[
\boxed{
\text{Durchtritte}
\rightarrow
\text{Reserven}
\rightarrow
\text{Nyquist}
\rightarrow
\text{Stabilität}
}
\]

Die mathematischen Teilresultate bleiben als unabhängige Domänenobjekte gespeichert. Dadurch erhält der Branch trotz gemeinsamer Lieferung klare Verantwortungsgrenzen, gezielte Tests und spätere Wiederverwendung durch Reglerauslegungs- oder Diagnoseblöcke.
