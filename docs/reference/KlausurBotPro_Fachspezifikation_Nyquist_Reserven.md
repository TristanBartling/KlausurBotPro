# KlausurBotPro - Fachspezifikation

## Nyquist-Kriterium, Ortskurve, Durchtrittsfrequenzen, Amplituden- und Phasenreserve

**Status:** Fachspezifikation; keine Implementierung; kein Codex-Prompt  
**Quellenstand:** Sommersemester 2026  
**Ziel:** Klausurtaugliche, numerisch robuste Bearbeitung zeitaufwendiger Frequenzbereichs- und Stabilitätsaufgaben unter konsequenter Wiederverwendung des vorhandenen Frequenzgang-/Bode-Workflows.

---

# 1. Quellenbasis, Kennzeichnung und Grenzen

## 1.1 Verbindliche Quellenhierarchie

1. `skript.pdf`
2. `Regelungstechnik_Übung_Aufg-u-Lösungen.pdf`
3. `Regelungstechnik_Tutorium_komplett.pdf`
4. `RT_Klausur_SS2025-komplett.pdf` und `RT-Klausur_WS_25_26-komplett.pdf`
5. `Tabelle_Standardglieder.pdf`
6. `RT1_Rechenwege_Master(12).md` nur ergänzend

## 1.2 Kennzeichnung

- **[OFFIZIELL]**: direkte Aussage oder Aufgabe aus Skript, offizieller Übung, Tutorium oder Klausur.
- **[HERLEITUNG]**: mathematisch aus offiziellen Angaben abgeleitet.
- **[KORREKTUR]**: offizielle Quelle enthält einen nachweisbaren Vorzeichen-, Phasen-, Punkte- oder Formulierungsfehler.
- **[TECHNISCHE SPEZIFIKATION]**: numerische oder GUI-Anforderung für den späteren Programmblock.
- **[ABGELEITETER REGRESSIONSTEST]**: kein originaler Aufgabentext, aber klar aus einem offiziellen Standardglied oder Verfahren abgeleitet.
- **[UNKLAR]**: Quellenlage reicht für eine verbindliche Festlegung nicht aus.

## 1.3 Zentrale Fundstellen

| Inhalt | Fundstelle |
|---|---|
| Ortskurve/Polargang | `skript.pdf`, PDF-S. 69-71, Abschnitt 3.3.2 |
| Totzeitglied | `skript.pdf`, PDF-S. 79-80, Abschnitt 3.4.4 |
| Amplitudenreserve | `skript.pdf`, PDF-S. 90-92, Algorithmen 3.45-3.46 |
| Phasenreserve | `skript.pdf`, PDF-S. 93-94, Algorithmen 3.47-3.48 |
| Rückführdifferenzfunktion | `skript.pdf`, PDF-S. 132-133, Definition 5.25 |
| Hsu-Chen-Voraussetzung und offene/geschlossene Pole | `skript.pdf`, PDF-S. 135, Theorem 5.30 und Bemerkung 5.31 |
| Allgemeines Nyquist-Kriterium | `skript.pdf`, PDF-S. 136, Theorem 5.33 |
| Nyquist auf dem offenen Kreis | `skript.pdf`, PDF-S. 137, Theoreme 5.34-5.35 |
| Allgemeines Nyquist-Beispiel, instabiler offener Kreis | `Regelungstechnik_Übung_Aufg-u-Lösungen.pdf`, PDF-S. 119-122, Übung 10 Aufgabe 1 |
| Vereinfachtes Nyquist und Reserven | ebenda, PDF-S. 119 sowie 123-125, Übung 10 Aufgabe 2 |
| Verstärkungsparameter mit Nyquist | ebenda, PDF-S. 119 und 125-126, Übung 10 Aufgabe 3 |
| Pol auf imaginärer Achse und instabiler offener Kreis | `Regelungstechnik_Tutorium_komplett.pdf`, PDF-S. 60-62, Tutorium 11 Aufgabe 1c-d |
| Klausur SS2025: Reserven | `RT_Klausur_SS2025-komplett.pdf`, Aufgabenbogen PDF-S. 6; Lösung PDF-S. 52 |
| Klausur SS2025: Nyquist | ebenda, Aufgabenbogen PDF-S. 8; Lösung PDF-S. 61-63 |
| Klausur WS25/26: Phasenreserve | `RT-Klausur_WS_25_26-komplett.pdf`, Aufgabenbogen PDF-S. 7; Lösung PDF-S. 55 |
| Klausur WS25/26: Nyquist mit Parameter | ebenda, Aufgabenbogen PDF-S. 10; Lösung PDF-S. 64-66 |
| Standard-Ortskurven/Bode-Formen | `Tabelle_Standardglieder.pdf`, PDF-S. 1-3 |

## 1.4 Nachweisbare Quellenfehler und Widersprüche

### Fehler A - falsche Phasenreserve in WS25/26

Für

\[
G(s)=\frac{100}{1+2s}
\]

liest die offizielle Lösung ungefähr \(\varphi=-90^\circ\) ab und berechnet fälschlich

\[
\Delta P=180^\circ+90^\circ=270^\circ.
\]

Richtig nach Algorithmus 3.48 des Skripts ist

\[
\Delta P=180^\circ+\varphi(\omega_g)\approx 90^\circ,
\]

exakt

\[
\omega_g=\frac{\sqrt{9999}}2\approx49.9975\,\mathrm{s^{-1}},
\qquad
\Delta P\approx90.573^\circ.
\]

Quelle: `RT-Klausur_WS_25_26-komplett.pdf`, Aufgabenbogen PDF-S. 7, Lösung PDF-S. 55; Gegenquelle: `skript.pdf`, PDF-S. 94, Algorithmus 3.48. **[KORREKTUR]**

### Fehler B - widersprüchliche Punkte in WS25/26

Der Aufgabenbogen weist für Aufgabe 2c **10 Punkte** aus, die Musterlösung dagegen **2 Punkte**. Deshalb darf die Gesamtpunktzahl dieses Moduls für diese Klausur nur als Bereich angegeben werden. Quelle: Aufgabenbogen PDF-S. 7; Lösung PDF-S. 55. **[UNKLAR]**

### Fehler C - Symbolfehler in Theoremen 5.34/5.35

Die Theoreme sprechen vom offenen Kreis \(G_0(s)\), schreiben im Satztext aber die Ortskurve \(F(i\omega)\), obwohl die Verschiebung auf den kritischen Punkt \(-1\) die Ortskurve von \(G_0(i\omega)\) betrifft. Der Begründungssatz bestätigt diese Verschiebung. Für den Programmblock gilt daher:

\[
\boxed{\text{Nyquist-Ortskurve des offenen Kreises }G_0(i\omega)\text{ um }-1.}
\]

Quelle: `skript.pdf`, PDF-S. 137, Theoreme 5.34-5.35. **[KORREKTUR]**

### Fehler D - unbrauchbare Hauptphasenreserve in Übung 06 Aufgabe 1

Die offizielle Lösung behandelt den negativen Vorfaktor über die Hauptphase und nennt eine Phasenreserve von \(270^\circ\). Der geschlossene Kreis der angegebenen Übertragungsfunktion besitzt jedoch einen Pol in der rechten Halbebene. Diese Aufgabe zeigt, dass eine modulo-\(360^\circ\)-Phase keine verlässliche Stabilitätsreserve liefert. Im Modul ist die **entfaltete Phase** zu verwenden; Reserven ersetzen bei instabilem offenem Kreis nicht das vollständige Nyquist-Kriterium. Quelle: `Regelungstechnik_Übung_Aufg-u-Lösungen.pdf`, PDF-S. 90 und 93-95. **[KORREKTUR]**

### Fehler E - lineare Amplitudenreserve im Skript

Algorithmus 3.45 definiert grafisch im linearen Maß

\[
\Delta A=1-|G(i\omega_p)|.
\]

Dies ist eine additive Betragsdifferenz, nicht der übliche zulässige Verstärkungsfaktor. Der Programmblock muss deshalb getrennt ausgeben:

\[
\Delta A_{\mathrm{dB}}=-L(\omega_p),
\qquad
A_R=\frac1{|G(i\omega_p)|},
\qquad
\Delta A_{\mathrm{add}}=1-|G(i\omega_p)|.
\]

Nur \(\Delta A_{\mathrm{dB}}\) entspricht direkt Algorithmus 3.46. \(A_R\) ist zusätzlich und eindeutig als **Verstärkungsfaktorreserve** zu beschriften. Quelle: `skript.pdf`, PDF-S. 91-92. **[TECHNISCHE SPEZIFIKATION]**

---

# 2. Klausurrelevanz und Punkte

## 2.1 Sommersemester 2025

| Fundstelle | Inhalt | Direkte Punkte | Indirekt unterstützt |
|---|---|---:|---:|
| Aufgabe 2d, Aufgabenbogen PDF-S. 6 | Amplituden- und Phasenreserve aus Bode | 4 | - |
| Aufgabe 2e, PDF-S. 6 | Glied zur Erhöhung der Phasenreserve | - | 8 |
| Aufgabe 3a III, Lösung PDF-S. 55 | Nyquist-Theorie | 2 | - |
| Aufgabe 3e, Aufgabenbogen PDF-S. 8 | Betrag, Phase, Stützpunkte, Ortskurve, Nyquist-Stabilität | 12 | - |
| **Summe** | | **18** | **8** |

**Bewertung:** Der Block unterstützt mindestens 18 direkte und weitere 8 anschließende Auslegungspunkte. Der größte Einzelgewinn ist die 12-Punkte-Ortskurven-/Nyquistaufgabe.

## 2.2 Wintersemester 2025/2026

| Fundstelle | Inhalt | Punkte laut Lösung | Punkte laut Aufgabenbogen |
|---|---|---:|---:|
| Aufgabe 2a III, Lösung PDF-S. 53 | Theorie zur Phasenreserve | 2 | Teil des 6-Punkte-MC-Blocks |
| Aufgabe 2c, Aufgabenbogen PDF-S. 7 / Lösung PDF-S. 55 | Phasenreserve | 2 | 10 |
| Aufgabe 3e, Aufgabenbogen PDF-S. 10 / Lösung PDF-S. 64-66 | parameterabhängige Ortskurve und Stabilitätsbereich | 12 | 12 |
| Aufgabe 4a I, Lösung PDF-S. 67 | Nyquist-Theorie | 2 | Teil des 6-Punkte-MC-Blocks |
| **Summe** | | **18** | **bis 26** |

**Bewertung:** Wegen des offiziellen Punktewiderspruchs ist nur der Bereich **18-26 direkt unterstützte Punkte** belastbar.

## 2.3 Auftretende Systemklassen

- IT1-Systeme und Produkte mehrerer PT1-Faktoren bei Reserven.
- Stabile offene Kreise dritter Ordnung mit P-Regler.
- Instabile offene Kreise mit zwei Polen in der rechten Halbebene.
- Nicht-minimalphasiger offener Kreis mit Nullstelle in der rechten Halbebene.
- Offener Kreis mit Integrator/Pol im Ursprung.
- Parameterabhängiger positiver oder formal auch negativer Verstärkungsfaktor.
- PT1- und PT2-Standardglieder als grafische Grundlage.
- Totzeit ist im Skript als Standardglied enthalten, aber in den beiden analysierten Klausuren nicht direkt als Nyquist-Aufgabe aufgetreten.

---

# 3. Modulgrenze und Wiederverwendung

## 3.1 Bereits vorhandene Ergebnisse - zwingend wiederverwenden

Der neue Block darf keine zweite Frequenzgang-Engine enthalten. Er übernimmt vom vorhandenen Frequenzgang-/Bode-Workflow:

1. \(G_0(j\omega_k)\) als komplexe Werte,
2. \(|G_0(j\omega_k)|\),
3. \(L(\omega_k)=20\log_{10}|G_0(j\omega_k)|\),
4. Hauptphase \(\varphi_{\mathrm{H}}(\omega_k)\),
5. entfaltete Phase \(\varphi_{\mathrm{u}}(\omega_k)\),
6. logarithmisches Bode-Raster,
7. erkannte Singularitätssegmente,
8. optional symbolische Übertragungsfunktion, Zähler/Nenner und Pole/Nullstellen,
9. einen Evaluator für zusätzliche Frequenzen, damit nach einer Nullstellensuche nur an \(\omega_*\) erneut ausgewertet wird.

## 3.2 Tatsächlich neue Berechnungen

- Ermittlung aller Amplitudendurchtritte.
- Ermittlung aller Phasendurchtritte auf der entfalteten Phase.
- Phasenreserve je Amplitudendurchtritt.
- Amplitudenreserve je Phasendurchtritt.
- Zählung offener Pole in der rechten Halbebene.
- Erkennung von Polen auf der imaginären Achse.
- Aufbau der vollständigen Nyquist-Kurve aus vorhandenen Frequenzwerten.
- Netto-Umschlingungszahl des kritischen Punkts.
- Anzahl instabiler geschlossener Pole über Nyquist.
- Stabilitätsaussage des geschlossenen Kreises.
- Kritische Verstärkungswerte und Stabilitätsintervalle bei reellem Skalarparameter.
- Diagrammannotation, Rechenweg- und LaTeX-Ausgabe.

## 3.3 Nicht Bestandteil dieses Moduls

- Parsen oder Herleiten von \(G_0(s)\) aus DGL/Blockschaltbild.
- Multiplikation der Regelkreisglieder.
- allgemeine Frequenzgangberechnung.
- Bode-Asymptoten oder Knickfrequenzlogik.
- Hurwitz-/Routh-Berechnung; sie darf nur als unabhängige Gegenprobe über eine bestehende Schnittstelle aufgerufen werden.
- Reglerentwurf mit Lead/Lag/PID; der Block liefert dafür Reserven und kritische Frequenzen.

---

# 4. Verbindliche Konventionen

## 4.1 Rückkopplung und kritischer Punkt

Standard ist negative Rückkopplung:

\[
F(s)=1+G_0(s).
\]

Der kritische Punkt der Ortskurve von \(G_0\) ist

\[
\boxed{-1+j0}.
\]

Andere Rückkopplungsvorzeichen müssen explizit eingegeben werden; keine automatische Vermutung.

## 4.2 Frequenz- und Phaseneinheiten

- Standard: \(\omega\) in \(\mathrm{rad/s}=\mathrm{s^{-1}}\).
- Hz nur nach expliziter Auswahl:
  \[
  \omega=2\pi f.
  \]
- Interne Phase in Radiant, Anzeige standardmäßig in Grad.
- Hauptphase:
  \[
  \varphi_{\mathrm H}\in(-180^\circ,180^\circ].
  \]
- Reserven benutzen die kontinuierlich entfaltete Phase \(\varphi_{\mathrm u}\), nicht eine modulo-\(360^\circ\)-Darstellung.
- Komplexes Argument ausschließlich über \(\operatorname{atan2}(\Im,\Re)\), niemals über einen einargumentigen Arkustangens.

## 4.3 Nyquist-Vorzeichen

Es gilt:

- \(P\): Anzahl offener Pole mit \(\Re(s)>0\).
- \(N_{\mathrm{cw}}\): Nettozahl der Umschlingungen von \(-1\) im Uhrzeigersinn; Uhrzeigersinn positiv.
- \(Z\): Anzahl geschlossener Pole mit \(\Re(s)>0\).

Verbindliche Ausgabegleichung:

\[
\boxed{Z=P+N_{\mathrm{cw}}}.
\]

Geschlossene Stabilität:

\[
\boxed{Z=0\iff N_{\mathrm{cw}}=-P.}
\]

Dies entspricht der Skriptaussage „\(-n^+\)-mal im Uhrzeigersinn“. Intern darf alternativ gegen den Uhrzeigersinn positiv gezählt werden, aber Benutzer- und LaTeX-Ausgabe müssen die obige Konvention verwenden.

## 4.4 Durchtrittsfrequenzen und Reserven

Amplitudendurchtritt:

\[
\boxed{|G_0(j\omega_{g,k})|=1}
\quad\Longleftrightarrow\quad
\boxed{L(\omega_{g,k})=0\,\mathrm{dB}}.
\]

Phasendurchtritt auf der entfalteten Phase:

\[
\boxed{\varphi_{\mathrm u}(\omega_{p,k})=-180^\circ-360^\circ m_k},
\qquad m_k\in\mathbb Z.
\]

Phasenreserve je Amplitudendurchtritt:

\[
\boxed{\Delta P_k=180^\circ+\varphi_{\mathrm u}(\omega_{g,k})}.
\]

Amplitudenreserve je Phasendurchtritt:

\[
\boxed{\Delta A_{k,\mathrm{dB}}=-L(\omega_{p,k})},
\qquad
\boxed{A_{R,k}=10^{\Delta A_{k,\mathrm{dB}}/20}=\frac1{|G_0(j\omega_{p,k})|}}.
\]

Negative Reserven bleiben negativ. Es erfolgt keine Abbildung auf \([0,360^\circ)\).

## 4.5 Status statt erfundener Zahlen

Jede Reserve erhält einen Status:

- `finite`
- `zero_critical`
- `no_gain_crossover`
- `no_phase_crossover`
- `formally_infinite`
- `multiple_crossovers`
- `not_applicable_open_loop_unstable`
- `not_applicable_imag_axis_pole`
- `band_limited_not_exhaustive`
- `numerically_ambiguous`

„Nicht vorhanden“, „nicht definiert“ und „formal unendlich“ sind nicht dasselbe.

---

# 5. Gemeinsame Vorprüfung

Vor jeder Aufgabe ist folgender Prüfblock auszuführen und im Rechenweg sichtbar zu machen:

1. Offenen Kreis \(G_0(s)\) bestätigen.
2. Rückkopplungsvorzeichen bestätigen.
3. Zähler- und Nennergrad prüfen.
4. Pole des offenen Kreises bestimmen oder übernehmen.
5. \(P=\#\{p_i:\Re p_i>0\}\) bestimmen.
6. Pole mit \(|\Re p_i|\le\varepsilon_p\) als imaginärachsennah markieren.
7. Rechtsseitige Pol-Nullstellen-Kürzungen vor Reduktion prüfen.
8. Reelle Koeffizienten und damit Konjugiertensymmetrie prüfen.
9. Frequenzbereich und Singularitätssegmente validieren.
10. Entscheiden:
   - vereinfachtes Nyquist zulässig,
   - allgemeines Nyquist erforderlich,
   - modifizierte Kontur erforderlich,
   - Standardverfahren nicht belastbar.

Plausibilitäts-Gegenprobe, sofern rational und ohne Totzeit:

\[
1+G_0(s)=0
\]

bildet das charakteristische Polynom des geschlossenen Kreises. Dessen Polzahl in der rechten Halbebene muss mit \(Z\) aus Nyquist übereinstimmen.

---

# 6. Fachspezifikation nach Aufgabentyp

## 6.1 Nyquist-Ortskurve nur zeichnen oder auswerten

**Fundstellen:** `skript.pdf`, PDF-S. 69-71 und 137-139; `Regelungstechnik_Übung_Aufg-u-Lösungen.pdf`, PDF-S. 119-126; beide Klausuren, jeweilige Nyquist-Aufgabe.

**Voraussetzungen**

- \(G_0(s)\) liegt vor.
- Frequenzgangwerte und Singularitätssegmente kommen aus dem bestehenden Workflow.
- Für Spiegelung über die reelle Achse müssen reelle Koeffizienten bestätigt sein.

**GUI-Eingaben**

- Auswahl der vorhandenen Transferfunktion/Open-Loop-ID.
- Frequenzband \([\omega_{\min},\omega_{\max}]\), automatisch vorgeschlagen.
- Modus: nur positive Frequenzen / vollständige Nyquist-Kurve.
- Markierungen: Start, Ende, Richtung, Achsenschnitte, \(-1\), Einheitskreis, Durchtritte.

**Ausgaben**

- parametrisierte Punkte \((\Re G_0(j\omega),\Im G_0(j\omega))\),
- Richtungspfeile und Frequenzlabels,
- Anfangs- und Endverhalten,
- Achsenschnittpunkte,
- Liste markanter Frequenzen,
- qualitative Beschreibung der Kurve.

**Klausurtauglicher Rechenweg**

1. Setze \(s=j\omega\).
2. Bringe \(G_0(j\omega)\) in die Form
   \[
   G_0(j\omega)=R(\omega)+jI(\omega).
   \]
3. Bestimme \(\omega=0\), \(\omega\to\infty\) und alle definierten Grenzwerte.
4. Löse \(I(\omega)=0\) für Realachsenschnitte.
5. Löse \(R(\omega)=0\) für Imaginärachsenschnitte.
6. Ergänze Stützpunkte aus dem vorhandenen Raster.
7. Zeichne den Ast für \(\omega>0\) mit Richtung wachsender Frequenz.
8. Bei reellen Koeffizienten ergänze
   \[
   G_0(-j\omega)=\overline{G_0(j\omega)}.
   \]
9. Markiere \(-1+j0\), ohne bereits eine Stabilitätsaussage zu erzwingen.

**Exakte und numerische Form**

- Exakt: rationale Ausdrücke für \(R(\omega)\), \(I(\omega)\), algebraische Achsenschnitte.
- Numerisch: adaptiv ausgewertete Punkte mit Frequenzlabel und Residuum der Schnittbedingung.

**Typische Fehler**

- geschlossenen statt offenen Kreis zeichnen,
- nur Hauptphase betrachten,
- negative Frequenzen vergessen,
- Spiegelung trotz komplexer Koeffizienten,
- Singularität durch eine Gerade verbinden,
- Richtungspfeile vertauschen,
- \(0\) statt \(-1\) markieren.

**Plausibilitätsprüfungen**

- Konjugiertensymmetriefehler
  \[
  \epsilon_{\mathrm{sym}}=\max_k|G_0(-j\omega_k)-\overline{G_0(j\omega_k)}|.
  \]
- Grenzwert muss zum Relativgrad passen.
- Achsenschnittresiduen müssen unter Toleranz liegen.
- Keine Verbindung über erkannte Singularitätssegmente.

**Diagrammanforderungen**

- gleiche Skalierung auf Real- und Imaginärachse als Option,
- automatische Detailansicht um \(-1\),
- Frequenzrichtung klar sichtbar,
- positive und negative Frequenzen unterscheidbar,
- kritischer Punkt und Einheitskreis nicht mit Kurve verwechselbar,
- Tabellenexport der markanten Punkte.

**Gewünschte LaTeX-Ausgabe**

```latex
\[
G_0(j\omega)=R(\omega)+jI(\omega)
\]
\[
I(\omega)=0\Rightarrow \omega=\omega_{R,1},\ldots
\]
\[
R(\omega)=0\Rightarrow \omega=\omega_{I,1},\ldots
\]
```

**Technische Grenzfälle**

- unendlicher Startwert durch Integrator,
- biproperes System mit endlichem Hochfrequenzgrenzwert,
- Totzeit mit unendlich vielen Windungen,
- Kurve berührt Achse tangential,
- Kurve passiert exakt \(-1\).

**Regressionstests:** R01, R02, R03, R05, R09, R10.

---

## 6.2 Stabilitätsaussage aus dem Nyquist-Kriterium

**Fundstellen:** `skript.pdf`, PDF-S. 132-139, insbesondere Theoreme 5.30 und 5.33-5.35; Übung 10, PDF-S. 119-126.

**Voraussetzungen**

- vollständige, geschlossene Nyquist-Kontur oder eine nachweisbar zulässige Vereinfachung,
- bekannte Zahl \(P\),
- kein ungeklärter Pol auf der Kontur,
- keine nicht dokumentierte instabile Pol-Nullstellen-Kürzung.

**Eingabe**

- offene Pole oder \(P\),
- vollständige Nyquist-Punktfolge,
- gewählte Umschlingungskonvention.

**Ausgabe**

- \(P\), \(N_{\mathrm{cw}}\), \(Z\),
- stabil / instabil / kritisch / Verfahren nicht anwendbar,
- textliche Begründung in einem Satz.

**Rechenweg**

1. Bestimme \(P\).
2. Bestimme die Netto-Umschlingung \(N_{\mathrm{cw}}\) um \(-1\).
3. Berechne
   \[
   Z=P+N_{\mathrm{cw}}.
   \]
4. Entscheide:
   \[
   Z=0\Rightarrow\text{keine geschlossenen RHP-Pole},
   \]
   \[
   Z>0\Rightarrow\text{geschlossener Kreis instabil}.
   \]
5. Falls die Kurve \(-1\) trifft oder ein geschlossener Pol auf der imaginären Achse liegt: **kritischer/grenzstabiler Fall**, nicht asymptotisch stabil.

**Numerisch robuste Umschlingungsbestimmung**

Auf der verschobenen Kurve

\[
H=1+G_0
\]

wird die gesamte Argumentänderung bestimmt:

\[
N_{\mathrm{ccw}}=\frac{1}{2\pi}\Delta\arg H,
\qquad
N_{\mathrm{cw}}=-N_{\mathrm{ccw}}.
\]

Zwischen zwei Punkten ist die lokale Winkeländerung über Skalar- und Kreuzprodukt zu bestimmen:

\[
\Delta\theta_k=
\operatorname{atan2}
\left(
\Im(\overline{H_k}H_{k+1}),
\Re(\overline{H_k}H_{k+1})
\right).
\]

Nur runden, wenn Abschlussfehler, Minimalabstand und Ganzzahlnähe die Toleranzen erfüllen.

**Typische Fehler**

- geometrische Anzahl statt Nettoanzahl,
- Richtung ohne Vorzeichen,
- \(P\) ignorieren,
- nur positive Frequenzen zählen,
- Kurve trifft \(-1\), trotzdem auf Ganzzahl runden,
- positive Reserven als Ersatzbeweis bei instabilem offenen Kreis.

**Plausibilitätsprüfungen**

- \(Z\) muss nichtnegativ ganzzahlig sein.
- Gegenprobe durch geschlossene Pole, wenn verfügbar.
- Für \(P=0\): stabil genau dann, wenn keine Netto-Umschlingung vorliegt und kein kritischer Treffer existiert.

**GUI/Diagramm**

- Karte mit \(P\), \(N_{\mathrm{cw}}\), \(Z\), Status.
- Umschlungene Teilkurve hervorheben.
- Bei Unsicherheit keine grüne/rote Endaussage, sondern Warnstatus.

**LaTeX**

```latex
\[
P=\ldots,\qquad N_{\mathrm{cw}}=\ldots
\]
\[
Z=P+N_{\mathrm{cw}}=\ldots
\]
\[
\boxed{\text{Der geschlossene Regelkreis ist ...}}
\]
```

**Grenzfälle:** Kurvenberührung, Selbstschnitt, mehrfacher Umlauf, Pol auf Kontur, nicht geschlossene numerische Kurve.  
**Regressionstests:** R01, R03, R04, R05.

---

## 6.3 Kritischer Punkt

**Fundstellen:** `skript.pdf`, PDF-S. 133 und 137; beide Klausuren und Übung 10.

**Definition**

Bei negativer Rückkopplung ist der kritische Punkt

\[
\boxed{G_0=-1+j0},
\]

weil

\[
1+G_0=0
\]

die charakteristische Gleichung erzeugt.

**Eingabe:** Rückkopplungsvorzeichen, Ortskurvenwerte.  
**Ausgabe:** kritischer Punkt, minimaler Abstand, Frequenz des nächsten Punkts, Trefferstatus.

**Rechenweg**

1. Setze den kritischen Punkt gemäß Rückkopplung.
2. Minimiere
   \[
   d(\omega)=|1+G_0(j\omega)|.
   \]
3. Prüfe zusätzlich alle Achsenschnittpunkte.
4. Klassifiziere:
   - \(d_{\min}>\varepsilon_c\): kein kritischer Treffer,
   - \(d_{\min}\le\varepsilon_c\): kritisch/numerisch nahe kritisch.

**Plausibilität:** Ein exakter Treffer muss gleichzeitig Betrag \(1\) und Phase \(-180^\circ-360^\circ m\) erfüllen.  
**GUI:** numerisches Feld \(d_{\min}\), Frequenz, Zoom-Schaltfläche.  
**Diagramm:** Fadenkreuz und Distanzsegment zum nächsten Kurvenpunkt.  
**LaTeX:** \(d_{\min}=\min_{\omega}|1+G_0(j\omega)|\).  
**Grenzfälle:** Tangentiale Berührung ohne Vorzeichenwechsel; mehrere gleich nahe Punkte; Totzeitwindungen.  
**Regressionstests:** R03, R04, R05, R10.

---

## 6.4 Anzahl instabiler Pole des offenen Kreises

**Fundstellen:** `skript.pdf`, PDF-S. 135-137; Übung 10 Aufgabe 1; Tutorium 11 Aufgabe 1d.

**Voraussetzungen:** ungekürzter offener Kreis oder explizit dokumentierte Kürzungen.  
**Eingabe:** offene Pole oder Nennerpolynom.  
**Ausgabe:** Pole nach LHP/RHP/Imaginärachse sortiert; \(P\).

**Rechenweg**

1. Bestimme alle Nennernullstellen einschließlich Vielfachheit.
2. Teile ein:
   \[
   \Re p_i>\varepsilon_p:\mathrm{RHP},\quad
   \Re p_i<-\varepsilon_p:\mathrm{LHP},\quad
   |\Re p_i|\le\varepsilon_p:\mathrm{j\omega\mbox{-}Achse}.
   \]
3. Zähle nur RHP-Pole in
   \[
   P=\sum_i \operatorname{mult}(p_i).
   \]
4. Pole auf der imaginären Achse separat ausgeben; sie gehören nicht stillschweigend zu \(P\).

**Exakt/numerisch**

- Exakt bei faktorisierbaren/symbolischen Polynomen.
- Numerisch mit Residuum \(|N(p_i)|\), Konditionswarnung und Clustering mehrfacher Pole.

**Typische Fehler:** RHP-Nullstellen statt Pole zählen; gekürzte instabile Pole verlieren; Vielfachheiten ignorieren.  
**Plausibilität:** Summe aller Polvielfachheiten entspricht Nennergrad nach dokumentierter Reduktion.  
**GUI:** Poltabelle mit Re, Im, Vielfachheit, Klasse.  
**LaTeX:** \(P=\#\{p_i\mid\Re(p_i)>0\}\).  
**Grenzfälle:** fast imaginäre Pole, symbolische Parameter, exakte RHP-Kürzung.  
**Regressionstests:** R01, R04, R05.

---

## 6.5 Umschlingungszahl

**Fundstellen:** `skript.pdf`, PDF-S. 136-137; Übung 10 Aufgabe 1.

**Eingabe:** geschlossene, geordnete Kurve \(G_{0,k}\), kritischer Punkt.  
**Ausgabe:** \(N_{\mathrm{cw}}\), Qualitätskennzahlen, Richtung.

**Rechenweg**

1. Verschiebe \(H_k=1+G_{0,k}\).
2. Prüfe \(\min|H_k|\) gegen kritische Toleranz.
3. Summiere die lokal eindeutigen Winkeländerungen \(\Delta\theta_k\).
4. Ergänze den letzten zum ersten Punkt.
5. Berechne
   \[
   q=\frac{\sum_k\Delta\theta_k}{2\pi}.
   \]
6. Falls \(|q-\operatorname{round}(q)|\le\varepsilon_N\), setze
   \[
   N_{\mathrm{cw}}=-\operatorname{round}(q).
   \]
7. Sonst adaptiv verfeinern oder `numerically_ambiguous` ausgeben.

**Robustheitsbedingungen**

- maximaler Winkelschritt pro Segment begrenzen, z. B. \(<30^\circ\),
- bei kleinem Abstand zu \(-1\) lokal verfeinern,
- Singularitätssegmente nicht linear überbrücken,
- Abschlussdefekt dokumentieren.

**Typische Fehler:** nur Schnittzahl mit negativer Realachse; Doppelzählung an Selbstschnitten; ungeschlossene Kurve.  
**Plausibilität:** Ganzzahlnähe, Reversierung der Kurvenrichtung ändert Vorzeichen, Spiegelung allein darf nicht als zweiter Umlauf missverstanden werden.  
**GUI:** Vorzeichenkonvention sichtbar; optional CCW- und CW-Wert nebeneinander.  
**LaTeX:** \(N_{\mathrm{cw}}=-\Delta\arg(1+G_0)/(2\pi)\).  
**Regressionstests:** R01, R03, R04.

---

## 6.6 Geschlossene Stabilität

**Fundstellen:** `skript.pdf`, PDF-S. 132-139; SS2025 Aufgabe 3e; WS25/26 Aufgabe 3e.

**Eingabe:** \(P\), \(N_{\mathrm{cw}}\), kritischer Status.  
**Ausgabe:** asymptotisch stabil / instabil / grenzkritisch / nicht entscheidbar.

**Rechenweg**

1. Wenn kritischer Treffer: `grenzkritisch`, keine normale Nyquist-Ganzzahlentscheidung.
2. Wenn Kontur ungültig: `nicht entscheidbar`.
3. Sonst \(Z=P+N_{\mathrm{cw}}\).
4. \(Z=0\): keine geschlossenen RHP-Pole.
5. Zusätzlich imaginärachsige geschlossene Pole prüfen, soweit charakteristisches Polynom verfügbar ist.
6. Nur wenn keine RHP- und keine imaginärachsigen Pole vorliegen: `asymptotisch stabil`.

**Typische Fehler:** E/A-Stabilität mit interner Stabilität gleichsetzen; versteckte instabile Kürzungen ignorieren.  
**Plausibilität:** Vergleich mit Polen von \(1+G_0\).  
**GUI:** Endstatus plus einzeilige Begründung, kein bloßes „ja/nein“.  
**LaTeX:** Box mit \(Z\) und Ergebnis.  
**Regressionstests:** R01, R03, R04, R05.

---

## 6.7 Amplitudendurchtrittsfrequenz

**Fundstellen:** `skript.pdf`, PDF-S. 93-94; beide Klausuren mit Reserveaufgaben.

**Eingabe:** vorhandenes \(L(\omega)\)-Raster und Frequenzgang-Evaluator.  
**Ausgabe:** vollständige geordnete Liste \(\{\omega_{g,k}\}\), Residuen, Kreuzungsrichtung.

**Rechenweg**

1. Definiere
   \[
   f_g(x)=L(e^x),\qquad x=\ln\omega.
   \]
2. Suche alle Vorzeichenwechsel im vorhandenen Raster.
3. Suche zusätzlich tangentiale Berührungen durch lokale Minima von \(|f_g|\).
4. Verfeinere jedes Intervall adaptiv.
5. Löse mit einem geklammerten Verfahren auf der logarithmischen Frequenzachse.
6. Werte \(G_0(j\omega_{g,k})\) mit dem bestehenden Evaluator nach.
7. Akzeptiere nur
   \[
   |L(\omega_{g,k})|\le\varepsilon_{\mathrm{dB}}.
   \]
8. Fasse numerisch doppelte Wurzeln über relative Frequenznähe zusammen.

**Exakte Variante**

Bei rationalem \(G_0\):

\[
|Z(j\omega)|^2-|N(j\omega)|^2=0.
\]

Nach \(x=\omega^2\) kann bei niedrigen Ordnungen eine exakte Polynomgleichung entstehen.

**Typische Fehler:** nur erster Durchtritt; lineare Interpolation über Dekaden; asymptotische Bode-Linie als exakter Frequenzgang.  
**Plausibilität:** \(|G|=1\) und \(L=0\) gleichzeitig; alle Rastersegmente abgearbeitet.  
**GUI:** Liste statt Einzelfeld; Auswahl „alle/maßgeblicher“.  
**Diagramm:** senkrechte Linien in Bode und markierte Einheitskreisschnitte in Nyquist.  
**LaTeX:** \(|G_0(j\omega_{g,k})|=1\Rightarrow\omega_{g,k}=\ldots\).  
**Grenzfälle:** tangentiale Berührung, \(\omega=0\), sehr flacher Verlauf, unendliche Zahl durch spezielle nicht-rationale Modelle.  
**Regressionstests:** R02, R06, R07, R09, R10.

---

## 6.8 Phasendurchtrittsfrequenz

**Fundstellen:** `skript.pdf`, PDF-S. 90-92; SS2025 Aufgabe 2d.

**Eingabe:** entfaltete Phase und Evaluator.  
**Ausgabe:** alle \(\omega_{p,k}\), zugehöriges Phasenniveau \(-180^\circ-360^\circ m_k\), Residuum.

**Rechenweg**

1. Bestimme den Wertebereich der entfalteten Phase in jedem stetigen Segment.
2. Ermittle alle ganzen \(m\), deren Niveau
   \[
   \varphi_m=-180^\circ-360^\circ m
   \]
   im Segment liegt.
3. Suche Vorzeichenwechsel von
   \[
   f_{p,m}(x)=\varphi_{\mathrm u}(e^x)-\varphi_m.
   \]
4. Erfasse tangentiale Berührungen über lokale Minima des Absolutresiduums.
5. Verfeinere und verifiziere mit dem komplexen Wert:
   \[
   |\Im G_0(j\omega_p)|\le\varepsilon_I,
   \qquad
   \Re G_0(j\omega_p)<0.
   \]

**Typische Fehler:** nur \(-180^\circ\) der Hauptphase; positiver Realachsenschnitt als Phasendurchtritt; asymptotisches Erreichen bei \(\omega\to\infty\) als endliche Frequenz.  
**Plausibilität:** negativer Realachsenschnitt und passende entfaltete Phase.  
**GUI:** Niveauindex \(m\) anzeigen.  
**Diagramm:** horizontale Phasenlinien und Realachsenschnitte links vom Ursprung.  
**Grenzfälle:** Totzeit mit vielen/ungezählten Durchtritten; Phasen-Sprung an Nullstelle; Phase undefiniert bei \(G=0\).  
**Regressionstests:** R03, R05, R08, R10.

---

## 6.9 Phasenreserve

**Fundstellen:** `skript.pdf`, PDF-S. 93-94; SS2025 Aufgabe 2d; WS25/26 Aufgabe 2c mit korrigierter Lösung.

**Voraussetzungen**

- mindestens ein Amplitudendurchtritt,
- entfaltete Phase eindeutig,
- bei Stabilitätsinterpretation: stabiler offener Kreis ohne Pol auf der imaginären Achse.

**Eingabe:** \(\omega_{g,k}\), \(\varphi_{\mathrm u}(\omega_{g,k})\).  
**Ausgabe:** \(\Delta P_k\) je Durchtritt; optional kritische Reserve.

**Rechenweg**

1. Bestimme alle \(\omega_{g,k}\).
2. Werte die entfaltete Phase an jedem Durchtritt aus.
3. Berechne
   \[
   \Delta P_k=180^\circ+\varphi_{\mathrm u}(\omega_{g,k}).
   \]
4. Gib negative Werte unverändert aus.
5. Bei mehreren Durchtritten: alle Werte; als diagnostisch kritisch
   \[
   \Delta P_{\min}=\min_k\Delta P_k.
   \]
6. Bei instabilem offenem Kreis: Werte nur als geometrische Diagnostik kennzeichnen, nicht als Stabilitätsbeweis.

**Typische Fehler:** \(180^\circ-\varphi\) bei negativer Phase falsch einsetzen; \(270^\circ\) durch Hauptphase; ersten statt gefährlichsten Durchtritt verwenden.  
**Plausibilität:** geometrischer Winkelabstand am Einheitskreis; Bode- und Nyquistwert müssen übereinstimmen.  
**GUI:** Tabelle Frequenz/Phase/Reserve/Status.  
**Diagramm:** Winkelbogen von negativer Realachse zum Kurvenpunkt am Einheitskreis.  
**LaTeX:** vollständiges Einsetzen mit Vorzeichen.  
**Grenzfälle:** kein Durchtritt -> nicht definiert; exakt \(-180^\circ\) -> 0; Mehrfachdurchtritt; instabiler offener Kreis.  
**Regressionstests:** R02, R05, R06, R07, R09, R10.

---

## 6.10 Amplitudenreserve

**Fundstellen:** `skript.pdf`, PDF-S. 90-92; SS2025 Aufgabe 2d; Übung 10 Aufgabe 2.

**Voraussetzungen:** mindestens ein endlicher negativer Realachsenschnitt.  
**Eingabe:** \(\omega_{p,k}\), Betrag/dB-Wert.  
**Ausgabe:** \(\Delta A_{k,\mathrm{dB}}\), \(A_{R,k}\), optional additive Skriptreserve.

**Rechenweg**

1. Bestimme alle Phasendurchtritte.
2. Werte \(L_k=L(\omega_{p,k})\) aus.
3. Berechne
   \[
   \Delta A_{k,\mathrm{dB}}=-L_k.
   \]
4. Berechne getrennt
   \[
   A_{R,k}=10^{\Delta A_{k,\mathrm{dB}}/20}=\frac1{|G_0(j\omega_{p,k})|}.
   \]
5. Optional:
   \[
   \Delta A_{k,\mathrm{add}}=1-|G_0(j\omega_{p,k})|.
   \]
6. Bei mehreren Durchtritten alle Werte; konservative positive Faktorreserve ist der kleinste Faktor \(>1\), sofern die einfache Reserveinterpretation zulässig ist.

**Typische Fehler:** dB und Faktor addieren; \(20\log_{10}|G|\) mit \(10\log_{10}|G|\) verwechseln; positiver Realachsenschnitt.  
**Plausibilität:** \(20\log_{10}A_R=\Delta A_{\mathrm{dB}}\).  
**GUI:** dB und Faktor getrennte Felder, keine unbeschriftete „Amplitude“.  
**Diagramm:** radialer Abstand auf negativer Realachse und vertikale dB-Differenz.  
**Grenzfälle:** kein endlicher Phasendurchtritt; mehrere Durchtritte; negativer Faktor; kritischer Treffer.  
**Regressionstests:** R03, R05, R08, R10.

---

## 6.11 Mehrere Durchtritte

**Fundstelle:** in den beiden Klausuren nicht als explizite Mehrfachfallfrage; aus allgemeiner Definition und PT2-Verhalten klar ableitbar. **[ABGELEITETER REGRESSIONSTEST]**

**Eingabe:** vollständige Listen aus 6.7 und 6.8.  
**Ausgabe:** keine erzwungene Einzelreserve; sortierte Liste und kritische Kennzahl mit Einschränkung.

**Rechenweg**

1. Finde sämtliche Durchtritte im analysierten Band.
2. Bestimme je Durchtritt Reserve und Kreuzungsrichtung.
3. Prüfe, ob weitere Durchtritte außerhalb des Bandes aufgrund des asymptotischen Verlaufs ausgeschlossen sind.
4. Kennzeichne den Datensatz als `multiple_crossovers`.
5. Verwende für Stabilität das vollständige Nyquist-Kriterium, nicht nur den kleinsten Marginwert.

**Typische Fehler:** Bibliotheksfunktion übernehmen, die nur den ersten oder „besten“ Wert liefert.  
**Plausibilität:** Anzahl der Bode-Durchtritte entspricht Einheitskreis-/Realachsenschnitten der Ortskurve.  
**GUI:** aufklappbare Liste und explizite Auswahl des betrachteten Durchtritts.  
**Diagramm:** alle Durchtritte nummerieren.  
**Grenzfälle:** tangentiale Doppelwurzel; eng benachbarte Durchtritte; bandbegrenzte Totzeit.  
**Regressionstests:** R07, R10.

---

## 6.12 Fehlende Durchtritte

**Fundstellen:** Skriptbeispiele implizieren die Definition; Übung 06 diskutiert nicht vorhandenen Phasendurchtritt; Standardglieder PT1/P.

**Regeln**

- Kein Amplitudendurchtritt:
  \[
  \Delta P\text{ ist nicht definiert.}
  \]
- Kein endlicher Phasendurchtritt:
  \[
  \Delta A\text{ ist als endliche Reserve nicht definiert.}
  \]
  Bei stabilem offenen Kreis und sicherem asymptotischem Ausschluss kann zusätzlich `formal unendlich` ausgegeben werden.

**Rechenweg**

1. Prüfe das gesamte Band plus asymptotisches Verhalten.
2. Unterscheide „nicht im Band gefunden“ von „global ausgeschlossen“.
3. Gib Status statt Ersatzwert aus.

**Typische Fehler:** \(0\), \(\infty\) oder \(180^\circ\) ohne Begründung einsetzen.  
**GUI:** Textstatus; numerisches Feld leer/`n. d.`.  
**Diagramm:** keine künstliche Durchtrittslinie.  
**Regressionstests:** R06, R08.

---

## 6.13 Pole auf der imaginären Achse

**Fundstellen:** `Regelungstechnik_Tutorium_komplett.pdf`, PDF-S. 60-62, Aufgabe 1c; Integratorbeispiele im Skript.

**Voraussetzungen:** genaue Polklassifikation und Singularitätssegmente.  
**Ausgabe:** erkannte Pole, benötigte Konturmodifikation, Zulässigkeitsstatus.

**MVP-Rechenweg**

1. Erkenne alle Pole mit \(|\Re p|\le\varepsilon_p\).
2. Trenne das Frequenzraster an jeder Singularität.
3. Verbinde die beiden Seiten nicht numerisch direkt.
4. Gib aus:
   \[
   \boxed{\text{Standard-Nyquistzählung ohne Ausweichkontur nicht zulässig.}}
   \]
5. Reserven dürfen als lokale Bode-Geometrie berechnet werden, müssen aber mit Warnung versehen sein.
6. Optional Gegenprobe über charakteristisches Polynom.

**Erweiterung**

- Einrückung der Kontur um jeden imaginärachsigen Pol,
- analytische oder hochpräzise Abbildung des kleinen Halbkreises,
- Grenzwert \(\varepsilon\to0^+\),
- korrekte Zusatzbögen in der Ortskurve.

**Typische Fehler:** Integrator wie normalen Startpunkt bei \(\omega=0\) behandeln; über \(\infty\) verbinden; \(P\) einfach erhöhen.  
**Plausibilität:** Werte beiderseits der Singularität divergieren entsprechend der Polordnung.  
**GUI:** rote Warnkarte; Option „nur lokale Reserven“ oder „modifizierte Kontur“.  
**Diagramm:** Lücke/Ausweichbogen statt falscher Verbindungsstrecke.  
**Regressionstests:** R05, R09.

---

## 6.14 Totzeit

**Fundstelle:** `skript.pdf`, PDF-S. 79-80; `Tabelle_Standardglieder.pdf`, Totzeitzeile. In den analysierten Klausuren keine direkte Nyquist-Totzeitaufgabe.

Für

\[
G_T(s)=K_Te^{-T_ts}
\]

gilt

\[
|G_T(j\omega)|=|K_T|,
\qquad
\varphi_T(\omega)=\arg K_T-\omega T_t.
\]

**Wiederverwendung:** komplexe Werte, Betrag und entfaltete Phase kommen aus dem Frequenzworkflow.  
**Neue Berechnung:** mehrere Phasendurchtritte und Windungen innerhalb des gewählten Frequenzbands.

**Rechenweg**

1. Totzeitparameter und Einheit prüfen.
2. Entfaltete Phase verwenden.
3. Alle Niveaus \(-180^\circ-360^\circ m\) im Band suchen.
4. Nyquistkurve mit adaptiver Phasenauflösung abtasten.
5. Falls keine analytische Ausschlussaussage vorliegt, Ergebnis als
   `band_limited_not_exhaustive` kennzeichnen.

**Typische Fehler:** Totzeitbetrag dämpfen; Phase modulo \(360^\circ\); nur ersten Phasendurchtritt.  
**Plausibilität:** Betrag des reinen Totzeitglieds konstant, Phasensteigung \(-T_t\) in rad/(rad/s).  
**GUI:** Totzeit explizit anzeigen; maximale analysierte Windungszahl.  
**Diagramm:** genügende Punktdichte pro Umdrehung; kein Polygon mit langen Sehnen.  
**Regressionstests:** R10.

---

## 6.15 Parameterabhängige Verstärkung

**Fundstellen:** Übung 10 Aufgabe 3; WS25/26 Aufgabe 3e; Skript Aufgabe 5.36.

Betrachtet wird zunächst

\[
G_0(s,K)=K\,\bar G_0(s),
\qquad K\in\mathbb R.
\]

**GUI-Eingaben**

- Parametersymbol und Definitionsbereich,
- Vorgabe \(K>0\), \(K\ge0\), \(K\in\mathbb R\) oder eigenes Intervall,
- Ausgabe gewünschter Grenzwerte und Stabilitätsintervalle.

**Ausgaben**

- kritische Verstärkungen,
- Grenzfrequenzen,
- Stabilitätsintervalle mit offenen/geschlossenen Randpunkten,
- Ortskurvenfamilie oder radial skalierbare Grundkurve,
- Randfallfaktorisierung, soweit möglich.

**Klausurtauglicher Rechenweg**

1. Bestimme offene Pole von \(\bar G_0\); reine Skalierung ändert sie für \(K\ne0\) nicht.
2. Suche negative Realachsenschnitte der Grundkurve:
   \[
   \Im \bar G_0(j\omega)=0,
   \qquad
   \Re \bar G_0(j\omega)<0.
   \]
3. Aus dem kritischen Treffer
   \[
   K\bar G_0(j\omega)=-1
   \]
   folgt
   \[
   \boxed{K_{\mathrm{krit}}=-\frac1{\Re \bar G_0(j\omega)}}.
   \]
4. Ergänze Parameterwerte, bei denen Grad, Polzahl oder statischer Nennerterm wechseln.
5. Sortiere alle kritischen Parameter.
6. Teste je offenes Intervall einen Repräsentanten mit Nyquist; optional mit vorhandenem Hurwitz/Routh- oder Polmodul gegenprüfen.
7. Prüfe Randpunkte auf imaginärachsige geschlossene Pole.
8. Schneide das Ergebnis mit dem vom Benutzer vorgegebenen Parameterbereich.

**Negative Verstärkung**

Für \(K<0\) wird die Ortskurve um \(180^\circ\) gedreht. Der Block darf nicht stillschweigend \(K>0\) annehmen. In der WS-Klausur ist wahrscheinlich eine positive Reglerverstärkung gemeint; mathematisch ergibt sich ein größerer Bereich.

**Typische Fehler:** nur maximale positive Verstärkung; unteren Rand bei konstantem Term vergessen; Werte aus einer einzelnen Ortskurve extrapolieren; \(K=0\) mit generischem Grad behandeln.  
**Plausibilität:** Randwert muss \(1+G_0(j\omega)=0\) erfüllen; Intervallprobe muss konstanten Stabilitätsstatus besitzen.  
**Diagramm:** Slider nur ergänzend; exakte Grenzkurven und kritische Punkte müssen beschriftet sein.  
**LaTeX:** kritische Gleichung, Parameterwerte, Intervallschreibweise.  
**Grenzfälle:** mehrere kritische Frequenzen, negative Parameter, Gradabfall, Parameter in Zähler und Nenner, offene Polzahl ändert sich.  
**Regressionstests:** R04, R11.


---

# 7. Numerische Robustheit und technische Anforderungen

## 7.1 Adaptives Frequenzraster

Das vorhandene Bode-Raster ist Startpunkt, nicht endgültiger Beweis. Der neue Block fordert lokale Verfeinerung an, wenn mindestens eines gilt:

- Vorzeichenwechsel von \(L(\omega)\),
- Vorzeichenwechsel zu einem Phasenniveau,
- großer Winkelunterschied benachbarter Nyquist-Punkte,
- geringer Abstand zu \(-1\),
- starke Krümmung,
- Nähe zu einer Singularität,
- möglicher tangentialer Durchtritt.

Empfohlene Kriterien:

\[
|\Delta\arg(1+G_0)|<30^\circ
\]

pro Segment und deutlich kleiner nahe dem kritischen Punkt. Toleranzen sind konfigurierbar und werden im Ergebnisprotokoll gespeichert.

## 7.2 Nullstellensuche

- Primärvariable: \(x=\ln\omega\).
- Geklammertes Verfahren, bevorzugt Brent.
- Newton nur als Beschleunigung innerhalb eines sicheren Intervalls.
- Jede gefundene Wurzel wird durch direkte Frequenzgangauswertung verifiziert.
- Tangentiale Wurzeln erfordern Minimierung des Absolutresiduums; ein reiner Vorzeichenwechseltest reicht nicht.

## 7.3 Winding-Number-Qualität

Zusätzlich zu \(N\) sind auszugeben:

- minimaler Abstand \(d_{\min}\),
- maximaler lokaler Winkelschritt,
- Abschlussfehler der Kurve,
- Abstand des Rohwertes zur nächsten Ganzzahl,
- Anzahl adaptiver Verfeinerungen,
- Warnung bei nicht erschöpftem Frequenzband.

## 7.4 Toleranzklassen

Keine feste absolute Toleranz für alle Systeme. Toleranzen skalieren mit

\[
S_G=\max(1,\max_k|G_0(j\omega_k)|).
\]

Empfohlene Kategorien:

- Polklassifikation \(\varepsilon_p\),
- kritischer Abstand \(\varepsilon_c S_G\),
- dB-Residuum \(\varepsilon_{\mathrm{dB}}\),
- Phasenresiduum \(\varepsilon_\varphi\),
- Ganzzahlnähe \(\varepsilon_N\),
- Symmetrie \(\varepsilon_{\mathrm{sym}}S_G\).

Die Spezifikation legt keine Bibliothekswerte fest; die spätere Implementierung muss sie durch die Regressionstests kalibrieren.

## 7.5 Symbolisch vor numerisch

Symbolisch/exakt bevorzugen bei:

- niedrigen rationalen Ordnungen,
- Achsenschnitten,
- Durchtrittsgleichungen in \(x=\omega^2\),
- kritischen Verstärkungen,
- Randfallfaktorisierungen.

Numerisch verwenden bei:

- hohen Ordnungen,
- Totzeit,
- nicht algebraischen Gliedern,
- nicht geschlossenen symbolischen Lösungen.

Die Ausgabe soll beide Ebenen trennen:

\[
\text{exaktes Ergebnis}
\quad\longrightarrow\quad
\text{numerischer Kontrollwert}.
\]

## 7.6 Unzulässige Vereinfachungen

- Keine Rundung vor Abschluss der Stabilitätsentscheidung.
- Keine Hauptphasenmodulo-Rechnung für Reserven.
- Keine lineare Interpolation von Frequenzen auf einer logarithmischen Achse.
- Keine Kurvenverbindung über Singularitäten.
- Keine automatische Auswahl nur eines Durchtritts.
- Keine vollständige Stabilitätsaussage nur aus positivem Margin.
- Keine Pol-Nullstellen-Kürzung in der rechten Halbebene ohne Warnung.

---

# 8. Daten- und Ausgabeschnittstelle

## 8.1 Eingangsdaten aus dem Frequenzworkflow

```text
OpenLoopFrequencyData
- system_id
- omega[]
- G_complex[]
- magnitude[]
- magnitude_db[]
- phase_principal_rad[]
- phase_unwrapped_rad[]
- continuity_segment_id[]
- singularity_segments[]
- real_coefficients_confirmed
- numerator / denominator / delays, falls vorhanden
- evaluate(omega[]) -> dieselben Frequenzgrößen
```

Dies ist eine Schnittstellenbeschreibung, keine Implementierung.

## 8.2 Ergebnisobjekt

```text
NyquistMarginResult
- convention
- open_loop_poles[]
- P
- imaginary_axis_poles[]
- gain_crossovers[]
- phase_crossovers[]
- phase_margins[]
- gain_margins_db[]
- gain_margin_factors[]
- critical_distance
- critical_distance_frequency
- winding_clockwise
- Z_closed_rhp
- closed_loop_status
- numerical_quality
- warnings[]
- latex_steps[]
- diagram_annotations[]
```

## 8.3 Pflichtwarnungen

Warnungen müssen maschinenlesbar und als Klartext vorliegen:

- `OPEN_LOOP_UNSTABLE_SIMPLE_MARGIN_NOT_PROOF`
- `IMAG_AXIS_POLE_MODIFIED_CONTOUR_REQUIRED`
- `CRITICAL_POINT_HIT`
- `MULTIPLE_GAIN_CROSSOVERS`
- `MULTIPLE_PHASE_CROSSOVERS`
- `NO_GAIN_CROSSOVER`
- `NO_PHASE_CROSSOVER`
- `FREQUENCY_BAND_NOT_EXHAUSTIVE`
- `RHP_CANCELLATION_DETECTED`
- `NONPROPER_NYQUIST_CLOSURE_REQUIRED`
- `PHASE_UNWRAP_AMBIGUOUS`
- `WINDING_NOT_INTEGER_WITHIN_TOLERANCE`
- `SOURCE_CONVENTION_CONFLICT`

---

# 9. GUI-Spezifikation

## 9.1 Klausurmodus

Minimaler Ablauf:

1. Offenen Kreis aus vorherigem Workflow übernehmen.
2. Schaltfläche **Nyquist + Reserven analysieren**.
3. Nur bei Bedarf Parameterbereich oder Frequenzband anpassen.
4. Ausgabe in vier kompakten Bereichen:
   - Voraussetzungen,
   - Durchtritte/Reserven,
   - Nyquist-Zählung,
   - abschreibbarer Rechenweg.

Keine erneute Eingabe von Zähler, Nenner oder Standardgliedern, wenn diese bereits vorhanden sind.

## 9.2 Lern-/Prüfmodus

Zusätzlich:

- Real-/Imaginärteil-Herleitung,
- markante Punkte,
- vollständige Polklassifikation,
- alternative Gegenprobe,
- Quellenhinweise,
- sichtbare Warnung bei offiziellen Quellenfehlern.

## 9.3 Eingabefelder

| Feld | Pflicht | Standard |
|---|---:|---|
| offener Kreis | ja | letzter Frequenzworkflow |
| Rückkopplung | ja | negativ |
| Frequenzeinheit | ja | rad/s |
| Frequenzband | automatisch | aus Polen/Nullstellen/Knickfrequenzen |
| Parameterbereich | nur Parameteraufgabe | keine Annahme; Benutzer muss Domain bestätigen |
| vollständiges/vereinfachtes Nyquist | automatisch | aus Polprüfung |
| Diagrammgenauigkeit | nein | klausurtauglich |
| exakte Rechnung | nein | automatisch, wenn möglich |

## 9.4 Ergebnispriorität

Oben stehen immer:

1. \(P\), \(N_{\mathrm{cw}}\), \(Z\), Stabilität,
2. Durchtrittsfrequenzen und Reserven,
3. Warnungen,
4. Diagramm,
5. Rechenweg.

Ein hübsches Diagramm ohne belastbare Zählung ist wertlos und darf nicht als Hauptergebnis erscheinen.

---

# 10. Diagrammanforderungen

## 10.1 Nyquist-Diagramm

Pflicht:

- Real- und Imaginärachse beschriftet,
- \(-1+j0\) deutlich markiert,
- Richtung wachsender \(\omega\),
- getrennte Kennzeichnung \(\omega>0\) und \(\omega<0\),
- markante Frequenzen,
- Einheitskreis optional,
- automatische Detailansicht um \(-1\),
- keine Linie über Singularitäten,
- kritische Distanz visualisierbar.

## 10.2 Bode-Diagramm

Pflicht:

- 0-dB-Linie,
- alle Amplitudendurchtritte,
- alle relevanten \(-180^\circ-360^\circ m\)-Linien,
- alle Phasendurchtritte,
- Reservepfeile und numerische Labels,
- entfaltete Phase als Grundlage; Hauptphase optional zusätzlich.

## 10.3 Konsistenz zwischen Diagrammen

- Jeder Amplitudendurchtritt entspricht einem Schnitt der Nyquist-Kurve mit dem Einheitskreis.
- Jeder Phasendurchtritt entspricht einem Schnitt mit der negativen Realachse.
- Die Reservewerte müssen in beiden Darstellungen identisch sein.

---

# 11. LaTeX-Ausgabe

## 11.1 Kompakter Klausurblock - allgemeines Nyquist

```latex
\[
G_0(s)=\ldots
\]
Die Pole des offenen Kreises sind
\[
p_{1,\ldots,n}=\ldots,\qquad P=\ldots
\]
Aus der vollständigen Nyquist-Ortskurve folgt
\[
N_{\mathrm{cw}}=\ldots
\]
Damit gilt
\[
Z=P+N_{\mathrm{cw}}=\ldots
\]
\[
\boxed{\text{Der geschlossene Regelkreis ist ...}}
\]
```

## 11.2 Ortskurven-Herleitung

```latex
\[
G_0(j\omega)=\frac{Z(j\omega)}{N(j\omega)}
\frac{\overline{N(j\omega)}}{\overline{N(j\omega)}}
=R(\omega)+jI(\omega)
\]
\[
I(\omega)=0\Rightarrow\omega=\ldots,
\qquad
R(\omega)=0\Rightarrow\omega=\ldots
\]
```

## 11.3 Reserven

```latex
\[
|G_0(j\omega_g)|=1
\Rightarrow
\omega_g=\ldots
\]
\[
\Delta P=180^\circ+\varphi_{\mathrm u}(\omega_g)
=\ldots
\]
\[
\varphi_{\mathrm u}(\omega_p)=-180^\circ-360^\circ m
\Rightarrow
\omega_p=\ldots
\]
\[
\Delta A_{\mathrm{dB}}=-20\log_{10}|G_0(j\omega_p)|=\ldots
\]
\[
A_R=\frac1{|G_0(j\omega_p)|}=\ldots
\]
```

## 11.4 Mehrfachfälle

LaTeX muss Listen/Tabelle ausgeben, nicht den ersten Wert unterschlagen:

```latex
\[
\begin{array}{c|c|c}
k&\omega_{g,k}&\Delta P_k\\\hline
1&\ldots&\ldots\\
2&\ldots&\ldots
\end{array}
\]
```

## 11.5 Warntexte

- „Die angegebene Phasenreserve ist nur eine geometrische Kenngröße; der offene Kreis ist instabil. Für die Stabilitätsaussage wird das vollständige Nyquist-Kriterium verwendet.“
- „Der offene Kreis besitzt einen Pol auf der imaginären Achse. Eine Standardumschlingungszählung ohne modifizierte Kontur ist nicht zulässig.“
- „Im analysierten Frequenzband wurde kein Durchtritt gefunden; globales Nichtvorhandensein ist nicht nachgewiesen.“


---

# 12. Referenzaufgaben und Regressionserwartungen

## R01 - Instabiler offener Kreis, geschlossener Kreis stabil

**Status:** [OFFIZIELL]  
**Fundstelle:** `Regelungstechnik_Übung_Aufg-u-Lösungen.pdf`, PDF-S. 119-122, Übung 10 Aufgabe 1.

### Aufgabenstellung

\[
G_0(s)=\frac{6s}{(s-1)(s-2)}.
\]

Beurteile offenen und geschlossenen Kreis mit allgemeinem Nyquist und durch Polgegenprobe.

### Rechenweg

1. Offene Pole:
   \[
   p_1=1,\qquad p_2=2\Rightarrow P=2.
   \]
2. Frequenzgang:
   \[
   G_0(j\omega)
   =\frac{-18\omega^2}{(2-\omega^2)^2+9\omega^2}
   +j\frac{6\omega(2-\omega^2)}{(2-\omega^2)^2+9\omega^2}.
   \]
3. Realachsenschnitt:
   \[
   \omega=\pm\sqrt2,
   \qquad
   G_0(\pm j\sqrt2)=-2.
   \]
4. Vollständige Ortskurve: zwei Umläufe gegen den Uhrzeigersinn, also
   \[
   N_{\mathrm{cw}}=-2.
   \]
5. Nyquist:
   \[
   Z=P+N_{\mathrm{cw}}=2-2=0.
   \]
6. Polgegenprobe:
   \[
   1+G_0(s)=0
   \Rightarrow(s-1)(s-2)+6s=0
   \Rightarrow s^2+3s+2=0,
   \]
   \[
   s_{1,2}=-1,-2.
   \]

### Ergebnis

\[
\boxed{\text{Offener Kreis instabil, geschlossener Kreis asymptotisch stabil.}}
\]

### Erwartete Ortskurve

- Start und Ende im Ursprung.
- Durchgang durch \(-2\) bei beiden Frequenzrichtungen.
- Netto zwei gegen den Uhrzeigersinn gerichtete Umschlingungen von \(-1\).

### Regression

- `P=2`
- `N_cw=-2`
- `Z=0`
- geschlossene Pole \(-1,-2\)
- vereinfachtes Nyquist muss abgelehnt werden.

---

## R02 - Stabiler offener Kreis, endliche Phasen- und Amplitudenreserve

**Status:** [OFFIZIELL + HERLEITUNG]  
**Fundstelle:** `Regelungstechnik_Übung_Aufg-u-Lösungen.pdf`, PDF-S. 119 und 123-125, Übung 10 Aufgabe 2.

### Aufgabenstellung

\[
G_S(s)=\frac{2.5}{s^2+3s+2},
\qquad
G_R(s)=1-s,
\]

\[
G_0(s)=\frac{2.5(1-s)}{s^2+3s+2}.
\]

Bestimme Nyquist-Stabilität sowie Reserven.

### Rechenweg

1. Offene Pole:
   \[
   -1,-2\Rightarrow P=0.
   \]
2. Real- und Imaginärteil:
   \[
   \Re G_0(j\omega)=
   \frac{-10\omega^2+5}{(2-\omega^2)^2+9\omega^2},
   \]
   \[
   \Im G_0(j\omega)=
   \frac{\omega(2.5\omega^2-12.5)}{(2-\omega^2)^2+9\omega^2}.
   \]
3. Phasendurchtritt/negativer Realachsenschnitt:
   \[
   \omega_p=\sqrt5,
   \qquad
   G_0(j\sqrt5)=-\frac56.
   \]
4. Amplitudenreserve:
   \[
   A_R=\frac65=1.2,
   \]
   \[
   \Delta A_{\mathrm{dB}}=20\log_{10}\frac65
   \approx1.5836\,\mathrm{dB}.
   \]
5. Amplitudendurchtritt:
   \[
   \omega_g=\frac32.
   \]
6. Komplexer Wert:
   \[
   G_0\!\left(j\frac32\right)
   =-\frac{56}{65}-j\frac{33}{65}.
   \]
7. Phase und Phasenreserve:
   \[
   \varphi(\omega_g)\approx-149.4898^\circ,
   \]
   \[
   \Delta P\approx30.5102^\circ.
   \]
8. Die Ortskurve umschließt \(-1\) nicht:
   \[
   N_{\mathrm{cw}}=0,
   \qquad Z=0.
   \]

### Ergebnis

\[
\boxed{\text{Geschlossener Kreis stabil, }\Delta P\approx30.51^\circ,
\ \Delta A\approx1.584\,\mathrm{dB}.}
\]

### Erwartete Diagrammaussage

- Ein Einheitskreisschnitt bei \(\omega=1.5\).
- Negativer Realachsenschnitt rechts vom kritischen Punkt bei \(-5/6\).
- Keine Umschlingung von \(-1\).

### Regression

Exakte Frequenzen und Brüche müssen erkannt werden; numerische Werte mit mindestens vier gültigen Stellen.

---

## R03 - Stabiler offener Kreis, geschlossener Kreis instabil

**Status:** [OFFIZIELL + HERLEITUNG]  
**Fundstelle:** `RT_Klausur_SS2025-komplett.pdf`, Aufgabenbogen PDF-S. 8; Lösung PDF-S. 61-63, Aufgabe 3e, 12 Punkte.

### Aufgabenstellung

\[
G_S(s)=\frac1{(s+2)(s^2+0.3s+1)},
\qquad
G_R(s)=2,
\]

\[
G_0(s)=\frac2{s^3+2.3s^2+1.6s+2}.
\]

Ermittle Betrag/Phase beziehungsweise Real-/Imaginärteil, zeichne die Ortskurve und entscheide die Stabilität.

### Rechenweg

1. Der offene Nenner ist Hurwitz; damit \(P=0\).
2. Mit
   \[
   a(\omega)=2-2.3\omega^2,
   \qquad
   b(\omega)=1.6\omega-\omega^3
   \]
   gilt
   \[
   G_0(j\omega)=\frac{2(a-jb)}{a^2+b^2}.
   \]
3. Somit
   \[
   \Re G_0=\frac{2(2-2.3\omega^2)}{(2-2.3\omega^2)^2+(1.6\omega-\omega^3)^2},
   \]
   \[
   \Im G_0=\frac{-2(1.6\omega-\omega^3)}{(2-2.3\omega^2)^2+(1.6\omega-\omega^3)^2}.
   \]
4. Realachsenschnitt:
   \[
   1.6\omega-\omega^3=0
   \Rightarrow
   \omega=\sqrt{1.6}=\sqrt{\frac85}.
   \]
5. Dort:
   \[
   G_0\!\left(j\sqrt{\frac85}\right)
   =-\frac{25}{21}\approx-1.19048.
   \]
6. Die vollständige Ortskurve umschließt \(-1\) zweimal im Uhrzeigersinn:
   \[
   N_{\mathrm{cw}}=2.
   \]
7. Nyquist:
   \[
   Z=P+N_{\mathrm{cw}}=2.
   \]
8. Gegenprobe:
   \[
   s^3+2.3s^2+1.6s+4=0
   \]
   besitzt näherungsweise
   \[
   s=-2.34507,
   \qquad
   s=0.022537\pm j1.30583.
   \]

### Ergebnis

\[
\boxed{\text{Der geschlossene Kreis ist instabil und besitzt zwei RHP-Pole.}}
\]

### Erwartete Ortskurve

- \(G_0(0)=1\).
- Ast für \(\omega>0\) zunächst in der unteren Halbebene.
- Schnitt der negativen Realachse links von \(-1\).
- Danach Annäherung an den Ursprung aus der oberen Halbebene.
- Zusammen mit dem gespiegelten Ast entstehen zwei Uhrzeigersinn-Umschlingungen.

### Regression

- exakter Schnitt \(-25/21\),
- `P=0`, `N_cw=2`, `Z=2`,
- Minimalabstand zum kritischen Punkt darf nicht fälschlich als Treffer klassifiziert werden.

---

## R04 - Parameterabhängige Verstärkung aus WS25/26

**Status:** [OFFIZIELL + KORREKTUR]  
**Fundstelle:** `RT-Klausur_WS_25_26-komplett.pdf`, Aufgabenbogen PDF-S. 10; Lösung PDF-S. 64-66, Aufgabe 3e, 12 Punkte.

### Aufgabenstellung

\[
G_0(s,K_R)=\frac{3K_R}{(s+1)(9s^2+18s+1)}
=\frac{3K_R}{9s^3+27s^2+19s+1}.
\]

Bestimme Real-/Imaginärteil, markante Punkte, Ortskurvenfamilie und Stabilitätsbereich.

### Rechenweg

1. Für \(K_R\ne0\) bleiben die offenen Pole unabhängig von \(K_R\) und liegen links; \(P=0\).
2. Mit
   \[
   a=1-27\omega^2,
   \qquad b=\omega(19-9\omega^2)
   \]
   gilt
   \[
   \Re G_0=\frac{3K_R(1-27\omega^2)}{(1-27\omega^2)^2+\omega^2(19-9\omega^2)^2},
   \]
   \[
   \Im G_0=\frac{-3K_R\omega(19-9\omega^2)}{(1-27\omega^2)^2+\omega^2(19-9\omega^2)^2}.
   \]
3. Startpunkt:
   \[
   G_0(0)=3K_R.
   \]
4. Imaginärachsenschnitt:
   \[
   1-27\omega^2=0
   \Rightarrow
   \omega_1=\frac1{3\sqrt3}.
   \]
5. Negativer Realachsenschnitt:
   \[
   19-9\omega^2=0
   \Rightarrow
   \omega_2=\frac{\sqrt{19}}3.
   \]
6. Dort:
   \[
   G_0(j\omega_2)=-\frac{3K_R}{56}.
   \]
7. Kritischer positiver Verstärkungswert:
   \[
   -\frac{3K_R}{56}=-1
   \Rightarrow
   \boxed{K_R=\frac{56}{3}}.
   \]
8. Geschlossenes Polynom:
   \[
   9s^3+27s^2+19s+1+3K_R.
   \]
9. Vollständige mathematische Stabilitätsbedingungen:
   \[
   1+3K_R>0,
   \qquad
   27\cdot19>9(1+3K_R).
   \]
   Also
   \[
   \boxed{-\frac13<K_R<\frac{56}{3}}.
   \]
10. Unter der üblichen, aber explizit zu bestätigenden Vorgabe \(K_R>0\):
    \[
    \boxed{0<K_R<\frac{56}{3}}.
    \]
11. Randfälle:
    \[
    K_R=\frac{56}{3}:
    \quad
    9s^3+27s^2+19s+57=(s+3)(9s^2+19),
    \]
    also \(s=\pm j\sqrt{19}/3\).
    \[
    K_R=-\frac13:
    \quad
    s(9s^2+27s+19)=0.
    \]

### Ergebnis

Die offizielle Lösung nennt nur die positive obere Grenze. Der Programmblock muss den Parameterbereich aus der GUI berücksichtigen und darf \(K_R>0\) nicht unsichtbar voraussetzen.

### Erwartete Ortskurve

Für positives \(K_R\) ist die Grundkurve radial skaliert; bei \(K_R=56/3\) trifft sie \(-1\).

### Regression

- exakte Werte \(\omega_1,\omega_2,K_{\mathrm{krit}}\),
- beide mathematischen Randwerte,
- für Domain `K_R>0` korrekt beschnittenes Intervall.

---

## R05 - Pol im Ursprung und negative Reserven

**Status:** [OFFIZIELL + HERLEITUNG]  
**Fundstelle:** `Regelungstechnik_Tutorium_komplett.pdf`, PDF-S. 60-62, Tutorium 11 Aufgabe 1c.

### Aufgabenstellung

\[
G_0(s)=\frac{25s+60}{10s^3+10s^2+25s}.
\]

Erstelle die Ortskurve, beurteile Stabilität und bestimme Reserven.

### Rechenweg

1. Der offene Kreis hat einen Pol bei \(s=0\). Standard-Nyquist ohne Ausweichkontur ist nicht zulässig.
2. Real-/Imaginärteil gemäß offizieller Lösung:
   \[
   \Re G_0(j\omega)=
   \frac{25\omega^2-250\omega^4}
   {100\omega^4+(25\omega-10\omega^3)^2},
   \]
   \[
   \Im G_0(j\omega)=
   \frac{350\omega^3-1500\omega}
   {100\omega^4+(25\omega-10\omega^3)^2}.
   \]
3. Phasendurchtritt:
   \[
   \omega_p=\sqrt{\frac{30}{7}}\approx2.07020,
   \]
   \[
   G_0(j\omega_p)=-1.4.
   \]
4. Amplitudenreserve:
   \[
   A_R=\frac1{1.4}=\frac57\approx0.714286,
   \]
   \[
   \Delta A_{\mathrm{dB}}=20\log_{10}\frac57
   \approx-2.92256\,\mathrm{dB}.
   \]
5. Amplitudendurchtritt numerisch:
   \[
   \omega_g\approx2.29948.
   \]
6. Entfaltete Phase:
   \[
   \varphi_{\mathrm u}(\omega_g)\approx-186.706^\circ,
   \]
   \[
   \Delta P\approx-6.706^\circ.
   \]
7. Geschlossene Gegenprobe:
   \[
   10s^3+10s^2+50s+60=0
   \]
   mit
   \[
   s\approx-1.15772,
   \qquad
   s\approx0.078860\pm j2.27517.
   \]

### Ergebnis

\[
\boxed{\text{Geschlossener Kreis instabil; beide Reserven negativ.}}
\]

### Erwartete Ausgabe

- Warnung `IMAG_AXIS_POLE_MODIFIED_CONTOUR_REQUIRED`.
- Lokale Reserven dürfen angezeigt werden, aber nicht als eigenständiger Nyquist-Beweis.
- Keine Gerade über \(\omega=0\).

### Regression

Negative Phasenreserve darf nicht als \(353.294^\circ\) oder ähnlich ausgegeben werden.

---

## R06 - Keine Durchtrittsfrequenz

**Status:** [ABGELEITETER REGRESSIONSTEST aus PT1-Standardglied]  
**Fundstellenbasis:** `skript.pdf`, PT1 Abschnitt; `Tabelle_Standardglieder.pdf`, PDF-S. 1.

### Aufgabenstellung

\[
G_0(s)=\frac{0.5}{1+s}.
\]

### Rechenweg und Ergebnis

\[
|G_0(j\omega)|=\frac{0.5}{\sqrt{1+\omega^2}}<1
\quad\forall\omega\ge0.
\]

Daher kein Amplitudendurchtritt und

\[
\boxed{\Delta P\text{ nicht definiert}.}
\]

Die Phase liegt in \((-90^\circ,0]\); kein endlicher Phasendurchtritt. Bei stabilem offenem Kreis kann die Amplitudenreserve als formal unendlich bezeichnet werden.

Geschlossen:

\[
1+G_0=0\Rightarrow s+1.5=0.
\]

\[
\boxed{\text{Geschlossener Kreis stabil}.}
\]

### Erwartete Diagrammaussage

Ortskurve liegt vollständig innerhalb des Einheitskreises und erreicht die negative Realachse nicht.

### Regression

- leere Crossover-Listen,
- PM-Status `no_gain_crossover`,
- GM-Status `formally_infinite` oder `no_phase_crossover`, je gewählter Ausgabekonvention,
- niemals numerischer Wert 0.

---

## R07 - Mehrere Amplitudendurchtritte

**Status:** [ABGELEITETER REGRESSIONSTEST aus PT2-Standardglied]  
**Fundstellenbasis:** `skript.pdf`, PT2 Abschnitt; `Tabelle_Standardglieder.pdf`, PDF-S. 1.

### Aufgabenstellung

\[
G_0(s)=\frac{0.5}{s^2+0.5s+1}.
\]

### Rechenweg

1. Offene Pole liegen links; \(P=0\).
2. Durchtrittsgleichung:
   \[
   (1-\omega^2)^2+0.25\omega^2=0.25.
   \]
3. Mit \(x=\omega^2\):
   \[
   x^2-1.75x+0.75=0
   \Rightarrow x\in\left\{\frac34,1\right\}.
   \]
4. Somit
   \[
   \omega_{g,1}=\frac{\sqrt3}{2},
   \qquad
   \omega_{g,2}=1.
   \]
5. Phasen:
   \[
   \varphi(\omega_{g,1})=-60^\circ,
   \qquad
   \varphi(\omega_{g,2})=-90^\circ.
   \]
6. Reserven:
   \[
   \Delta P_1=120^\circ,
   \qquad
   \Delta P_2=90^\circ.
   \]
7. Kein endlicher \(-180^\circ\)-Durchtritt; Amplitudenreserve formal unendlich.
8. Geschlossen:
   \[
   s^2+0.5s+1.5=0
   \]
   ist stabil.

### Erwartete Diagrammaussage

Die resonante Betragskurve überschreitet 0 dB und schneidet sie zweimal; die Nyquist-Kurve schneidet den Einheitskreis zweimal.

### Regression

Der Block muss beide Frequenzen ausgeben und darf keine einzelne „Standard-Phasenreserve“ erzwingen.

---

## R08 - Endliche Amplitudenreserve, keine Phasenreserve

**Status:** [OFFIZIELL]  
**Fundstelle:** `skript.pdf`, PDF-S. 91-92, Beispiel zu Algorithmus 3.46.

### Aufgabenstellung

\[
G_0(s)=\frac{0.4}{(s+1)^4}.
\]

### Rechenweg

1. Phase:
   \[
   \varphi(\omega)=-4\arctan\omega.
   \]
2. Phasendurchtritt:
   \[
   -4\arctan\omega_p=-180^\circ
   \Rightarrow\omega_p=1.
   \]
3. Betrag:
   \[
   |G_0(j)|=\frac{0.4}{(1+1^2)^2}=0.1.
   \]
4. Amplitudenreserve:
   \[
   A_R=10,
   \qquad
   \Delta A_{\mathrm{dB}}=20\,\mathrm{dB}.
   \]
5. Da \(|G_0(0)|=0.4<1\) und der Betrag monoton fällt, existiert kein Amplitudendurchtritt; Phasenreserve nicht definiert.
6. Geschlossene Pole näherungsweise:
   \[
   -1.56234\pm j0.56234,
   \qquad
   -0.437659\pm j0.56234.
   \]

### Ergebnis

\[
\boxed{\Delta A=20\,\mathrm{dB},\quad \Delta P\text{ nicht definiert},\quad\text{stabil}.}
\]

### Regression

Exakt \(\omega_p=1\), Faktor 10, keine erfundene PM.

---

## R09 - Ein Amplitudendurchtritt mit Integrator

**Status:** [OFFIZIELL + EXAKTISIERUNG]  
**Fundstelle:** `skript.pdf`, PDF-S. 93-94, Beispiel zu Algorithmus 3.48.

### Aufgabenstellung

\[
G_0(s)=\frac{10}{s(s+1)}.
\]

### Rechenweg

1. Betrag:
   \[
   |G_0(j\omega)|=\frac{10}{\omega\sqrt{1+\omega^2}}.
   \]
2. Durchtritt:
   \[
   \omega^2(1+\omega^2)=100.
   \]
3. Mit \(x=\omega^2\):
   \[
   x^2+x-100=0,
   \qquad
   x=\frac{-1+\sqrt{401}}2.
   \]
4. Exakt:
   \[
   \boxed{\omega_g=
   \sqrt{\frac{-1+\sqrt{401}}2}}
   \approx3.08423.
   \]
5. Phase:
   \[
   \varphi_{\mathrm u}=-90^\circ-\arctan\omega_g
   \approx-162.0358^\circ.
   \]
6. Phasenreserve:
   \[
   \boxed{\Delta P\approx17.9642^\circ}.
   \]
7. Geschlossen:
   \[
   s^2+s+10=0
   \]
   ist stabil.

### Besonderheit

Der offene Kreis besitzt einen Pol im Ursprung. Die Bode-Phasenreserve ist klausurrelevant und im Skript ausdrücklich berechnet. Eine vollständige Nyquist-Umschlingungszählung benötigt dennoch die modifizierte Kontur.

### Regression

- exakte Wurzelform,
- Skriptrundung \(3.1\) und \(17.9^\circ\) als akzeptierte Darstellung,
- Warnung wegen Pol im Ursprung.

---

## R10 - Totzeit, mehrere Phasendurchtritte

**Status:** [ABGELEITETER REGRESSIONSTEST aus Totzeit- und PT1-Glied]  
**Fundstellenbasis:** `skript.pdf`, PDF-S. 79-80; PT1-Abschnitt; `Tabelle_Standardglieder.pdf`.

### Aufgabenstellung

\[
G_0(s)=\frac{2e^{-s}}{1+s}.
\]

### Rechenweg

1. Betrag:
   \[
   |G_0(j\omega)|=\frac2{\sqrt{1+\omega^2}}.
   \]
2. Amplitudendurchtritt:
   \[
   \omega_g=\sqrt3\approx1.73205.
   \]
3. Entfaltete Phase:
   \[
   \varphi_{\mathrm u}(\omega)=-\omega-\arctan\omega
   \quad\text{[rad]}.
   \]
4. Phasenreserve:
   \[
   \Delta P=\pi-\left(\sqrt3+\frac\pi3\right)
   =\frac{2\pi}{3}-\sqrt3
   \]
   \[
   \boxed{\Delta P\approx20.7608^\circ}.
   \]
5. Erster Phasendurchtritt:
   \[
   \omega_p+\arctan\omega_p=\pi
   \Rightarrow
   \omega_p\approx2.02876.
   \]
6. Dort:
   \[
   |G_0(j\omega_p)|\approx0.884241,
   \]
   \[
   A_R\approx1.13091,
   \qquad
   \Delta A\approx1.06859\,\mathrm{dB}.
   \]
7. Für größere Frequenzen existieren weitere Phasendurchtritte. Eine endliche Rasteranalyse muss dies als bandbegrenzt kennzeichnen.

### Erwartete Ortskurve

Spiralförmige, weiter rotierende Annäherung an den Ursprung; ausreichend feine Abtastung pro Umlauf erforderlich.

### Regression

- kein Hauptphasenfehler,
- alle Durchtritte im gewählten Band,
- Status `band_limited_not_exhaustive`, falls kein globaler Ausschluss geführt wird.

---

## R11 - Parameteraufgabe ohne endliche obere positive Grenze

**Status:** [OFFIZIELL + KORREKTUR DER AUFGABENFORMULIERUNG]  
**Fundstelle:** `Regelungstechnik_Übung_Aufg-u-Lösungen.pdf`, PDF-S. 119 und 125-126, Übung 10 Aufgabe 3.

### Aufgabenstellung

\[
G_0(s,K)=\frac{K}{(s+1)(s+2)}.
\]

Bestimme den zulässigen Verstärkungsbereich.

### Rechenweg

1. Geschlossene Gleichung:
   \[
   (s+1)(s+2)+K=0
   \Rightarrow
   s^2+3s+2+K=0.
   \]
2. Stabilität zweiter Ordnung:
   \[
   3>0,
   \qquad
   2+K>0.
   \]
3. Daher:
   \[
   \boxed{K>-2}.
   \]
4. Randfall:
   \[
   K=-2\Rightarrow s(s+3)=0.
   \]
5. Für die übliche Domain \(K\ge0\):
   \[
   \boxed{\text{alle }K\ge0\text{ sind stabil; keine endliche obere Grenze}.}
   \]

### Regression

Die spätere Software darf wegen der Formulierung „maximal zulässig“ keinen erfundenen Maximalwert erzeugen.


---

# 13. Regressionstest-Matrix

| ID | Kernfall | Pflichtprüfungen |
|---|---|---|
| R01 | instabiler offener Kreis, durch Rückkopplung stabil | Polzählung, allgemeines Nyquist, Vorzeichen der Umläufe, geschlossene Polgegenprobe |
| R02 | stabiler offener Kreis, endliche beide Reserven | Real/Imaginärteil, Einheitskreis- und Realachsenschnitt, Bode/Nyquist-Konsistenz |
| R03 | stabiler offener Kreis, geschlossener Kreis instabil | zwei RHP-Pole, kritischer Realachsenschnitt links von -1, zwei CW-Umläufe |
| R04 | Parametergrenze | exakte Achsenschnitte, positiver und negativer Rand, Domain-Beschneidung |
| R05 | Pol im Ursprung | Singularitätserkennung, negative Reserven, keine Hauptphasenmodulo-Ausgabe |
| R06 | keine Durchtritte | Statuswerte statt 0/180, formal unendliche GM nur mit Begründung |
| R07 | mehrere Amplitudendurchtritte | vollständige Root-Liste, zwei PM-Werte, tangential-/Mehrfachlogik |
| R08 | endliche GM, keine PM | \(\omega_p=1\), 20 dB, leere Gain-Crossover-Liste |
| R09 | Integrator und eine PM | exakte \(\omega_g\), Skriptrundung, Warnstatus |
| R10 | Totzeit | entfaltete Phase, viele Phasendurchtritte, bandbegrenzter Status |
| R11 | kein endliches positives Maximum | Parameterdomain, kein erfundener Höchstwert |

## 13.1 Zusätzliche generische Tests

1. **Skalierungsinvarianz der Umschlingung:** identische Kurve mit anderer Punktdichte liefert dieselbe Ganzzahl.
2. **Orientierungswechsel:** umgekehrte Punktreihenfolge ändert nur das Vorzeichen der Umschlingungszahl.
3. **Konjugiertensymmetrie:** reelle Koeffizienten liefern Spiegelungsfehler unter Toleranz.
4. **Kritischer Treffer:** \(G_0=-1\) wird als kritisch erkannt; keine Rundung auf eine normale Umlaufzahl.
5. **Tangentendurchtritt:** Betrag berührt 1 ohne Vorzeichenwechsel und wird trotzdem erkannt.
6. **Nahe Mehrfachpole:** Polklassifikation meldet Konditionswarnung.
7. **RHP-Kürzung:** ungekürztes Modell erzeugt Pflichtwarnung; reduzierte Darstellung darf keine interne Stabilität behaupten.
8. **Biproperer Kreis:** Hochfrequenzgrenzwert ungleich null löst Schließungswarnung aus.
9. **Komplexe Koeffizienten:** automatische Spiegelung wird deaktiviert.
10. **Einheitenfehler:** Hz-Eingabe ohne Umrechnung muss durch Test scheitern; korrekte Umrechnung reproduziert rad/s-Ergebnis.

## 13.2 Akzeptanzkriterien

Ein Test gilt nur als bestanden, wenn gleichzeitig stimmen:

- exakter/symbolischer Ausdruck, soweit vorgegeben,
- numerischer Wert innerhalb der festgelegten Toleranz,
- Status und Warnungen,
- Diagrammtopologie,
- LaTeX-Vorzeichen,
- Gegenprobe durch geschlossene Pole, soweit vorhanden.

---

# 14. MVP-Priorisierung

Bewertungsskala: **hoch / mittel / niedrig**. Aufwand bezieht sich auf den zusätzlichen Modulaufwand bei vorhandenem Frequenzgang-/Bode-Workflow.

## A. Günstiges erstes MVP

| Funktion | Direkte Klausurpunkte | Indirekte Punkte | Codex-Aufwand | Wiederverwendung | Handfehler-Risiko | Begründung |
|---|---|---|---|---|---|---|
| alle Amplitudendurchtritte | hoch | hoch | niedrig-mittel | sehr hoch | hoch | Grundlage jeder PM-Aufgabe; vorhandene dB-Werte nutzbar |
| alle Phasendurchtritte | hoch | hoch | mittel | sehr hoch | hoch | Grundlage jeder GM- und Realachsenschnittaufgabe |
| Phasenreserve mit entfalteter Phase | hoch | hoch | niedrig | sehr hoch | sehr hoch | offizieller 270°-Fehler zeigt Notwendigkeit |
| Amplitudenreserve in dB und Faktor | hoch | mittel | niedrig | sehr hoch | hoch | häufige dB/Faktor-Verwechslung |
| Nyquist-Diagramm für reelle, echt rationale Systeme ohne j-Achsenpole | hoch | mittel | mittel | sehr hoch | hoch | 12-Punkte-Aufgaben in beiden Klausuren |
| offene RHP-Pole zählen | hoch | mittel | niedrig | hoch | hoch | zwingend für allgemeines Nyquist |
| robuste Umschlingungszahl | hoch | mittel | mittel | hoch | sehr hoch | Kern der Stabilitätsentscheidung |
| \(Z=P+N_{\mathrm{cw}}\) und Stabilitätsstatus | hoch | hoch | niedrig | hoch | hoch | klausurtaugliche Endaussage |
| markante Achsenschnitte | hoch | mittel | mittel | hoch | hoch | direkt in Klausurwertetabellen verlangt |
| scalarer positiver Verstärkungsparameter \(K\bar G_0\) | hoch | hoch | mittel | hoch | sehr hoch | WS-Aufgabe mit 12 Punkten |
| kompakter LaTeX-Rechenweg | hoch | hoch | mittel | sehr hoch | mittel | Rechenweg ist laut Klausurregeln bewertungsrelevant |
| Bode-/Nyquist-Konsistenzprüfung | mittel | hoch | niedrig | sehr hoch | hoch | fängt falsche Phasen- und Durchtrittsauswahl ab |

### MVP-Grenzen

Das erste MVP unterstützt:

- reelle SISO-LTI-Übertragungsfunktionen,
- negative Rückkopplung,
- echt rationale offene Kreise,
- stabile und instabile offene Kreise,
- keine Pole auf der imaginären Achse für die vollständige Nyquist-Zählung,
- beliebig viele numerisch erfassbare Durchtritte,
- reellen positiven Skalarparameter mit explizitem Bereich.

Bei Polen auf der imaginären Achse muss das MVP sicher erkennen und abbrechen, nicht falsch rechnen.

## B. Sinnvolle Erweiterungen

| Funktion | Direkte Punkte | Aufwand | Nutzen |
|---|---|---|---|
| vollständige reelle Parameterintervalle einschließlich \(K<0\) | hoch | mittel | beseitigt versteckte Domain-Annahmen und deckt WS-Aufgabe mathematisch vollständig ab |
| symbolisch exakte Real-/Imaginärteile und niedrige Polynomwurzeln | mittel-hoch | mittel | bessere LaTeX-Ausgabe und genaue Klausurwerte |
| modifizierte Nyquist-Kontur für einfache j-Achsenpole | mittel | hoch | deckt Tutorium 11 und Integratoren formal korrekt ab |
| automatische lokale Kurvenverfeinerung nach Krümmung | mittel | mittel | verhindert falsche Umlaufzahlen nahe -1 |
| Totzeit mit bandbegrenzter Mehrfachdurchtrittsanalyse | mittel | mittel-hoch | quellenrelevant, hohe Robustheitsbedeutung |
| Parameter in Zähler und Nenner | mittel | hoch | allgemeinere Regleraufgaben |
| alternative Gegenprobe über vorhandenes Hurwitz/Routh-Modul | hoch indirekt | niedrig-mittel | sehr hoher Fehlerschutz |
| Hauptphase und entfaltete Phase parallel anzeigen | mittel | niedrig | didaktisch und zur Fehlerdiagnose wertvoll |

## C. Teure oder seltene Sonderfälle

| Funktion | Gründe für spätere Priorität |
|---|---|
| mehrfache Pole auf der imaginären Achse mit vollständigen Einrückungsbögen | mathematisch und numerisch heikel; in beiden Klausuren nicht direkt aufgetreten |
| biproperes oder unechtes Nyquist mit expliziter Hochfrequenzbogenabbildung | Skripttheorem 5.34 ist für nicht-sprungfähige Systeme formuliert; hoher Zusatzaufwand |
| komplexe Systemkoeffizienten ohne Konjugiertensymmetrie | nicht in den analysierten RT1-Aufgaben erkennbar |
| MIMO-Nyquist | außerhalb der Veranstaltung RT1 |
| symbolische Totzeit-Stabilitätsintervalle über unendlich viele Durchtritte | teuer und nicht klausurnah |
| allgemeine mehrdimensionale Parameterregionen | besser vom Hurwitz/Routh-Modul oder späterer Speziallogik bearbeiten |
| interaktiver grafischer Ortskurveneditor | hoher UI-Aufwand, geringe zusätzliche Punktwirkung |

---

# 15. Funktionsbewertung im Überblick

| Funktion | Direkte Punkte | Indirekt | Aufwand | Wiederverwendung | Fehleranfälligkeit Hand |
|---|---|---|---|---|---|
| Ortskurve aus vorhandenen Frequenzwerten | hoch | mittel | mittel | sehr hoch | hoch |
| markante Punkte/Achsenschnitte | hoch | mittel | mittel | hoch | hoch |
| allgemeines Nyquist | hoch | hoch | mittel | hoch | sehr hoch |
| vereinfachtes Nyquist | hoch | mittel | niedrig | hoch | mittel |
| Polzählung \(P\) | hoch | mittel | niedrig | hoch | hoch |
| Winding Number | hoch | mittel | mittel | hoch | sehr hoch |
| geschlossene RHP-Polzahl \(Z\) | hoch | hoch | niedrig | hoch | hoch |
| Gain-Crossover-Liste | hoch | hoch | niedrig-mittel | sehr hoch | hoch |
| Phase-Crossover-Liste | hoch | hoch | mittel | sehr hoch | hoch |
| PM-Liste | hoch | hoch | niedrig | sehr hoch | sehr hoch |
| GM-dB/Faktor-Liste | hoch | mittel | niedrig | sehr hoch | hoch |
| kein/mehrere Durchtritte | mittel | hoch | niedrig-mittel | hoch | sehr hoch |
| positive Skalarverstärkung | hoch | hoch | mittel | hoch | sehr hoch |
| negative Skalarverstärkung | mittel | mittel | mittel | hoch | hoch |
| j-Achsenpole nur erkennen | mittel | hoch | niedrig | hoch | sehr hoch |
| j-Achsenpole formal behandeln | mittel | mittel | hoch | mittel | sehr hoch |
| Totzeit | niedrig-mittel direkt | hoch indirekt | mittel-hoch | hoch | sehr hoch |

---

# 16. Verbindlicher Entscheidungsbaum

1. **Liegt \(G_0(s)\) bereits vor?**  
   Nein: an vorgeschalteten Regelkreis-/Transferfunktionsblock zurückgeben.  
   Ja: weiter.

2. **Sind Frequenzdaten vorhanden?**  
   Nein: vorhandenen Frequenzworkflow aufrufen.  
   Ja: übernehmen, nicht neu berechnen.

3. **Polprüfung:**  
   - j-Achsenpol -> Warn-/Sonderpfad.  
   - sonst \(P\) bestimmen.

4. **Echt rational/proper?**  
   - ja -> Standard-Nyquist.  
   - nein -> Sonderfallwarnung oder erweiterte Kontur.

5. **Durchtritte:**  
   alle Gain- und Phase-Crossover bestimmen.

6. **Reserven:**  
   je Durchtritt berechnen; Statusregeln anwenden.

7. **Nyquist:**  
   vollständige Kurve aufbauen, \(-1\) prüfen, Umschlingung bestimmen.

8. **Stabilität:**  
   \(Z=P+N_{\mathrm{cw}}\), kritische Fälle separat.

9. **Parameter vorhanden?**  
   kritische Werte bestimmen, Intervalle testen, Domain schneiden.

10. **Ausgabe:**  
    Ergebnis, Warnungen, Diagramme, LaTeX, Gegenprobe.

---

# 17. Offene Quellenfragen

## 17.1 Modifizierte Kontur bei j-Achsenpolen

Das Skript definiert die Standard-Nyquistkontur und die Übungen enthalten einen Pol im Ursprung, führen aber in den vorliegenden Fundstellen keine vollständige, eindeutige Einrückungsregel mit Vorzeichenkonvention aus. Deshalb ist nur die **Erkennung und sichere Ablehnung der naiven Kontur** vollständig quellengebunden. Die formale Implementierung der Ausweichkontur ist als Erweiterung zu behandeln und vor Programmierung nochmals zu verifizieren.

## 17.2 Parameterdomain in WS25/26

Die Klausur nennt \(K_R\), ohne im Aufgabentext sichtbar ausdrücklich \(K_R>0\) festzulegen. Die Musterlösung behandelt nur die positive obere Grenze. Mathematisch ist der Stabilitätsbereich \(-1/3<K_R<56/3\). Der Programmblock muss den Parameterbereich explizit verlangen oder beide Interpretationen ausgeben.

## 17.3 Punkte und Phasenreserve in WS25/26

Die Punkte und die Musterlösung widersprechen sich. Für Priorisierung ist die Aufgabe trotzdem eindeutig hochrelevant; für eine exakte historische Punktstatistik bleibt die Quelle widersprüchlich.

--- NOTEBOOKLM-PROMPT ---

Prüfe folgende Fragen ausschließlich anhand der hochgeladenen offiziellen Regelungstechnik-Quellen:

1. Welche genaue Nyquist-Ausweichkontur und welche Vorzeichenkonvention soll bei einem einfachen Pol auf der imaginären Achse, insbesondere bei einem Pol im Ursprung, in dieser Vorlesung verwendet werden?
2. Wird in der Klausur WS 2025/26 Aufgabe 3e stillschweigend \(K_R>0\) vorausgesetzt, oder ist der vollständige Stabilitätsbereich einschließlich negativer Werte gefragt?
3. Wie viele Punkte besitzt Aufgabe 2c der Klausur WS 2025/26 verbindlich: 10 laut Aufgabenbogen oder 2 laut Musterlösung?
4. Bestätige anhand des Skripts, dass die Phasenreserve für \(G(s)=100/(1+2s)\) ungefähr \(90.6^\circ\) und nicht \(270^\circ\) beträgt.

Antworte kurz und eindeutig. Belege jede wesentliche Aussage mit:
- kurzem direkten Zitat,
- Dokumentname,
- Seitenzahl oder genauer Fundstelle.

Zeige Widersprüche zwischen Quellen. Wenn keine eindeutige Antwort möglich ist, sage das ausdrücklich und erfinde nichts.

--- ENDE ---

---

# 18. Endempfehlung

Der wirtschaftlich stärkste erste Block ist **kein neuer Frequenzrechner**, sondern eine Auswertungs- und Beweisschicht über den bereits vorhandenen Frequenzdaten:

\[
\boxed{
\text{Durchtritte}
\rightarrow
\text{Reserven}
\rightarrow
\text{Nyquist-Umschlingung}
\rightarrow
\text{geschlossene Stabilität}
}
\]

Das MVP muss die beiden häufigsten Fehlerklassen kompromisslos verhindern:

1. falsche Phase durch Hauptwert/Modulo-\(360^\circ\),
2. falsche Stabilitätsaussage durch Ignorieren offener RHP- oder j-Achsenpole.

Mit den MVP-Funktionen werden in den beiden analysierten Klausuren ungefähr **18 direkte Punkte je Klausur**, im WS aufgrund widersprüchlicher Bewertung möglicherweise bis zu **26 Punkte**, sowie weitere nachgelagerte Reglerauslegungspunkte unterstützt. Die Wiederverwendung des bestehenden Frequenzworkflows ist sehr hoch; der zusätzliche Aufwand liegt überwiegend in Root-Finding, Polklassifikation, Winding Number, Statuslogik und sauberer Ausgabe.
