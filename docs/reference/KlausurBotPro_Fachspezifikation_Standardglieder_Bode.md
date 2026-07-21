# KlausurBotPro – Fachspezifikation

## Standardgliedererkennung, Zerlegung von Übertragungsfunktionen und asymptotische Bode-Synthese

**Status:** Fachspezifikation, keine Implementierung, kein Codex-Prompt  
**Quellenstand:** Sommersemester 2026  
**Ziel:** hohe Klausurpunktabdeckung bei geringem zusätzlichem Entwicklungsaufwand durch Wiederverwendung des vorhandenen Parsers, der exakten Reduktion, der Pol-/Nullstellenberechnung, des numerischen Frequenzgangs und der LaTeX-Infrastruktur.

---

# 1. Quellenbasis und Kennzeichnung

## 1.1 Quellenhierarchie

1. `skript.pdf`
2. `Regelungstechnik_Übung_Aufg-u-Lösungen.pdf`
3. `Regelungstechnik_Tutorium_komplett.pdf`
4. `RT_Klausur_SS2025-komplett.pdf`
5. `RT-Klausur_WS_25_26-komplett.pdf`
6. `Tabelle_Standardglieder.pdf`
7. `RT1_Rechenwege_Master(12).md` nur ergänzend

## 1.2 Kennzeichnung

- **[OFFIZIELL]**: direkt aus Skript, offizieller Übung, offiziellem Tutorium oder Klausur.
- **[HERLEITUNG]**: mathematisch aus offiziellen Angaben hergeleitet.
- **[KORREKTUR]**: offizielle Quelle enthält einen offensichtlichen Widerspruch oder Formel-/Vorzeichenfehler; die Korrektur folgt anderen höherrangigen Quellen und direkter Rechnung.
- **[TECHNISCHE SPEZIFIKATION]**: Festlegung für den späteren Programmblock.
- **[SYNTHETISCHER TEST]**: aus offiziellen Standardformen abgeleiteter Softwaretest, keine originale Aufgabenstellung.

---

# 2. Klausurrelevanz

## 2.1 Sommersemester 2025 – direkte Bode-Aufgabe

**Aufgabe 2:**

- Theorieblock: 6 Punkte.
- Knickfrequenz geometrisch bestimmen: 2 Punkte.
- Basisglieder erkennen, begründen und Gesamtübertragungsfunktion herleiten: 10 Punkte.
- Amplituden- und Phasenreserve grafisch bestimmen: 4 Punkte.
- Zusatzglied zur Erhöhung der Phasenreserve auf 20° auslegen: 8 Punkte.

Damit sind **12 Punkte unmittelbar** der Standardgliedererkennung und Bode-Zerlegung zuzuordnen. Weitere **12 Punkte** werden durch dieselbe Zerlegung indirekt für Reserven und Korrekturgliedauslegung unterstützt.

Die offizielle Lösung erkennt ein I-Glied und ein PT1-Glied:

\[
G_I(s)=\frac{1}{0.01s}=\frac{100}{s},
\qquad
G_{PT1}(s)=\frac{1}{10s+1},
\]

\[
\boxed{
G(s)=\frac{100}{s(10s+1)}
}.
\]

Fundstelle: `RT_Klausur_SS2025-komplett.pdf`, Aufgabenbogen PDF-S. 5–6; Lösung PDF-S. 49–53.

## 2.2 Wintersemester 2025/2026 – direkte Bode-Aufgabe

**Aufgabe 2:**

- Theorieblock: 6 Punkte.
- Übertragungsfunktion aus Diagramm, Basisglied und Knickfrequenz: 4 Punkte.
- Phasenreserve grafisch: Aufgabenbogen 10 Punkte, Lösungsrubrik 2 Punkte.
- PD-Glied \(10(1+0.002s)\) qualitativ einzeichnen: Aufgabenbogen 4 Punkte, Lösungsrubrik 6 Punkte.
- Reihenschaltung beider Glieder qualitativ einzeichnen: Aufgabenbogen 8 Punkte, Lösungsrubrik 10 Punkte.

Der Aufgabenbogen weist somit **32 Punkte**, die spätere Lösungsrubrik **28 Punkte** für Aufgabe 2 aus. Die Klausurhinweise erklären ausdrücklich, dass die angegebenen Punkte nur Richtwerte sind. Für die wirtschaftliche Bewertung ist deshalb eine Bandbreite anzugeben.

Unmittelbar durch diesen Programmblock abdeckbar sind mindestens:

- 4 Punkte für PT1-Erkennung,
- 4–6 Punkte für PD-Synthese,
- 8–10 Punkte für Reihenschaltung und Summen-Bode.

Zusätzlich wird die grafische Phasenreserve unterstützt.

Offizielle Formen:

\[
G_1(s)=\frac{100}{1+2s},
\qquad
\omega_k=0.5\,\mathrm{s^{-1}},
\]

\[
G_2(s)=10(1+0.002s),
\qquad
\omega_z=500\,\mathrm{s^{-1}},
\]

\[
\boxed{
G_{ges}(s)=1000\frac{1+0.002s}{1+2s}
}.
\]

Fundstelle: `RT-Klausur_WS_25_26-komplett.pdf`, Aufgabenbogen PDF-S. 6–7; Lösung PDF-S. 52–57.

## 2.3 Indirekte Klausurverwendung

Die Zerlegung wird außerdem benötigt für:

1. **Amplituden- und Phasenreserve:** Durchtrittsfrequenzen und Phasenlage werden am offenen Kreis bestimmt.
2. **Regler- und Korrekturgliedauslegung:** Lead/Lag/P-Verstärkung verändern Betrag und Phase komponentenweise.
3. **Nyquist-Vorbereitung:** Vorzeichen, Integratoren, Totzeit, nichtminimalphasige Nullstellen und offene Pole beeinflussen Phase und Kurvenverlauf.
4. **Plausibilitätskontrolle von Blockschaltbildreduktionen:** Eine erzeugte Gesamtübertragungsfunktion kann anhand der erwarteten Bode-Steigungen geprüft werden.

## 2.4 Wirtschaftliche Schlussfolgerung

Dieser Block ist **punktestark und billig**, weil der teure mathematische Unterbau bereits vorhanden ist. Benötigt werden primär:

- deterministische Klassifikation vorhandener Pole/Nullstellen,
- Normierung in Bode-Faktorformen,
- Ereignistabelle der Knickfrequenzen,
- asymptotische Addition,
- klausurtaugliche Ausgabe.

Ein neuer CAS, neuer Root-Finder oder neuer numerischer Bode-Plot wäre unnötige Duplikation.

---

# 3. Verbindliche Begriffstrennung

## 3.1 Exakter numerischer Bode-Verlauf

\[
L_{exakt}(\omega)=20\log_{10}|G(j\omega)|,
\qquad
\varphi_{exakt}(\omega)=\arg G(j\omega).
\]

Dieser Verlauf stammt aus dem bereits vorhandenen numerischen Frequenzgang. Er enthält Rundungen an Knickstellen, Resonanzüberhöhungen, Phasenübergänge und Wechselwirkungen exakt im Rahmen der numerischen Genauigkeit.

## 3.2 Asymptotische Bode-Konstruktion

Die asymptotische Amplitude besteht aus Geradenstücken mit diskreten Steigungsänderungen an den Knickfrequenzen. Sie ist eine **Näherung**.

Beispiele:

- PT1 bei der Ecke: asymptotische Linie \(0\,\mathrm{dB}\), exakter Wert \(-3.01\,\mathrm{dB}\).
- Doppeltes PT1 bei der Ecke: asymptotisch \(0\,\mathrm{dB}\), exakt \(-6.02\,\mathrm{dB}\).

Die Ausgabe darf die asymptotische Kurve niemals als „exakten Bode-Verlauf“ bezeichnen.

## 3.3 Einzelbeiträge der Standardglieder

Jeder Faktor liefert separat:

- einen Betragsbeitrag,
- eine asymptotische Steigungsänderung,
- einen Phasenbeitrag.

Bei Reihenschaltung werden Beträge in dB und Phasen addiert.

---

# 4. Grundkonventionen

## 4.1 Eingabeform

Ausgangspunkt ist die bereits exakt reduzierte rationale Übertragungsfunktion

\[
G(s)=\frac{Z(s)}{N(s)}.
\]

Vorhandene Werte, die konsumiert werden müssen:

- reduziertes Zählerpolynom,
- reduziertes Nennerpolynom,
- Pole mit Vielfachheiten,
- Nullstellen mit Vielfachheiten,
- numerischer Frequenzgang,
- Hauptphase und entfaltete Phase.

## 4.2 Keine Partialbruchzerlegung für Reihenschaltung

Für die Bode-Synthese wird die **Faktorzerlegung** verwendet:

\[
G(s)=K\frac{\prod_i Z_i(s)}{\prod_j N_j(s)}.
\]

Eine Partialbruchzerlegung erzeugt Summanden und entspricht einer Parallelzerlegung. Die Aussage im Skript, die Partialbruchzerlegung entspreche einer Reihenschaltung, ist mathematisch falsch und darf nicht in die Spezifikation übernommen werden.

## 4.3 Verstärkung

Für einen reellen konstanten Faktor \(K\neq0\):

\[
L_K=20\log_{10}|K|.
\]

- \(K>0\): Phasenbeitrag \(0^\circ\).
- \(K<0\): Phasenbeitrag konsistent \(-180^\circ\) oder äquivalent \(+180^\circ\).

Der Betrag darf nie mit \(20\log_{10}K\) berechnet werden, wenn \(K<0\).

## 4.4 Frequenzeinheit

Kreisfrequenzen werden grundsätzlich in

\[
\mathrm{rad\,s^{-1}}
\]

beziehungsweise in den Quellen verkürzt als \(\mathrm{s^{-1}}\) ausgegeben. Eine Frequenz \(f\) in Hz darf nur mit expliziter Umrechnung

\[
\omega=2\pi f
\]

verwendet werden.

## 4.5 Knickfrequenz und Grenzfrequenz

Für einen Faktor erster Ordnung \(1+Ts\):

\[
\omega_k=\frac1T.
\]

Beim PT1 fällt diese Knickfrequenz mit der \(-3\,\mathrm{dB}\)-Grenzfrequenz zusammen. Bei I- und D-Gliedern gibt es **keinen geometrischen Knick**; eine mögliche \(0\,\mathrm{dB}\)-Frequenz ist nur eine Referenzfrequenz.

## 4.6 Phasenreserve

Bei entfalteter Phase nahe \(-180^\circ\):

\[
\boxed{
\Delta\varphi=180^\circ+\varphi(\omega_c)
}
\]

mit \(|G(j\omega_c)|=1\). Die Formel \(180^\circ-\varphi\) darf nicht mit einer bereits negativen Phase eingesetzt werden.

---

# 5. Kanonische Gesamtform

## 5.1 Verbindliche interne Darstellung

Die reduzierte Übertragungsfunktion wird als

\[
G(s)=K\,s^{q}
\frac{
\displaystyle\prod_i Z_{1,i}(s)^{m_i}
\prod_r Z_{2,r}(s)^{\mu_r}
}{
\displaystyle\prod_j P_{1,j}(s)^{n_j}
\prod_t P_{2,t}(s)^{\nu_t}
}
\,e^{-sT_t}
\]

dargestellt.

Dabei gilt:

- \(K\in\mathbb R\setminus\{0\}\),
- \(q=n_{z,0}-n_{p,0}\): Nettoanzahl der Nullstellen minus Pole im Ursprung,
- \(Z_1,P_1\): normierte reelle Faktoren erster Ordnung,
- \(Z_2,P_2\): normierte reelle quadratische Faktoren,
- \(m_i,n_j,\mu_r,\nu_t\): Vielfachheiten,
- \(T_t\ge0\): optionale Totzeit.

## 5.2 Reelle stabile Faktoren

LHP-Nullstelle bei \(s=-\omega_z\), \(\omega_z>0\):

\[
Z_1(s)=1+\frac{s}{\omega_z}=1+T_zs.
\]

LHP-Pol bei \(s=-\omega_p\), \(\omega_p>0\):

\[
P_1(s)=1+\frac{s}{\omega_p}=1+T_ps.
\]

## 5.3 Nichtminimalphasige Faktoren

RHP-Nullstelle bei \(s=+\omega_z\):

\[
Z_{RHP}(s)=1-\frac{s}{\omega_z}.
\]

Sie besitzt denselben Betragsgang wie die LHP-Nullstelle, aber den entgegengesetzten Phasenbeitrag.

## 5.4 Quadratische Faktoren

Für ein konjugiert komplexes Polpaar

\[
p_{1,2}=-D\omega_0\pm j\omega_0\sqrt{1-D^2}
\]

lautet der normierte Faktor

\[
P_2(s)=1+2D\frac{s}{\omega_0}+\left(\frac{s}{\omega_0}\right)^2.
\]

Bei \(D\ge1\) sind die Pole reell; dann ist die Zerlegung in zwei reelle PT1-Faktoren für die Bode-Ereignistabelle vorzuziehen.

---

# 6. Deterministischer Zerlegungsablauf

## Schritt 1 – Reduzierte Übertragungsfunktion übernehmen

Keine erneute Parser-, Kürzungs- oder Pol-/Nullstellenlogik. Die vorhandene exakt reduzierte Funktion ist maßgeblich.

## Schritt 2 – Konstantenverstärkung isolieren

Alle normierten Faktoren müssen bei \(s=0\) den Wert 1 besitzen, sofern sie keinen Ursprungspol oder keine Ursprungsnullstelle enthalten. Der verbleibende Rest ist der konstante Faktor \(K\).

Nach der Zerlegung muss gelten:

\[
G_{rekonstruiert}(s)\equiv G_{reduziert}(s).
\]

## Schritt 3 – Pole und Nullstellen im Ursprung erfassen

Vielfachheiten separat zählen:

\[
n_{z,0},\qquad n_{p,0},\qquad q=n_{z,0}-n_{p,0}.
\]

Anfangssteigung:

\[
\boxed{
m_0=20q\;\mathrm{dB/Dekade}
}.
\]

## Schritt 4 – Reelle Faktoren normieren

Für jede reelle Wurzel \(r\neq0\):

- \(r<0\): Faktor \(1+s/|r|\), Knick \(\omega_k=|r|\).
- \(r>0\): Faktor \(1-s/r\), Knick \(\omega_k=r\), Kennzeichnung „RHP/nichtminimalphasig“.

Zähler- und Nennerfaktoren müssen getrennt bleiben.

## Schritt 5 – Komplex konjugierte Wurzeln paaren

Für \(r=a\pm jb\):

\[
\omega_0=\sqrt{a^2+b^2},
\qquad
D=-\frac{a}{\omega_0}
\]

für ein LHP-Paar. Die Rekonstruktion des quadratischen Faktors ist numerisch zu kontrollieren.

## Schritt 6 – Vielfachheiten und gleiche Knickfrequenzen gruppieren

Faktoren mit gleicher exakter Knickfrequenz oder innerhalb einer klar definierten numerischen Toleranz werden als gemeinsames Ereignis ausgegeben. Die einzelnen Faktoren bleiben trotzdem in der Gliedertabelle sichtbar.

## Schritt 7 – Knickfrequenzen sortieren

\[
0<\omega_{k,1}<\omega_{k,2}<\dots<\omega_{k,N}.
\]

## Schritt 8 – Steigungsänderungen addieren

Pro Vielfachheit:

- reelle Zählernullstelle: \(+20\,\mathrm{dB/Dek}\),
- reeller Nennerpol: \(-20\,\mathrm{dB/Dek}\),
- quadratischer Zählerfaktor: \(+40\,\mathrm{dB/Dek}\),
- quadratischer Nennerfaktor: \(-40\,\mathrm{dB/Dek}\).

Für jedes Ereignis:

\[
m_{nach}=m_{vor}+\Delta m.
\]

## Schritt 9 – Asymptotische Amplitude aufbauen

Robuste globale Form:

\[
\begin{aligned}
L_{asym}(\omega)
={}&20\log_{10}|K|+20q\log_{10}\omega\\
&+\sum_i20m_i\log_{10}\max\left(1,\frac{\omega}{\omega_{z,i}}\right)\\
&-\sum_j20n_j\log_{10}\max\left(1,\frac{\omega}{\omega_{p,j}}\right)\\
&+\sum_r40\mu_r\log_{10}\max\left(1,\frac{\omega}{\omega_{0,z,r}}\right)\\
&-\sum_t40\nu_t\log_{10}\max\left(1,\frac{\omega}{\omega_{0,p,t}}\right).
\end{aligned}
\]

Zusätzlich sind die Geradengleichungen intervallweise auszugeben.

## Schritt 10 – Phasenbeiträge addieren

Exakte elementweise Beiträge für \(\omega>0\):

- Ursprungspol: \(-90^\circ\) je Pol.
- Ursprungsnullstelle: \(+90^\circ\) je Nullstelle.
- LHP-Nullstelle: \(+\arctan(\omega/\omega_z)\).
- LHP-Pol: \(-\arctan(\omega/\omega_p)\).
- RHP-Nullstelle: \(-\arctan(\omega/\omega_z)\).
- RHP-Pol: \(+\arctan(\omega/\omega_p)\).
- LHP-Polpaar:

\[
-\operatorname{atan2}\!\left(2D\frac{\omega}{\omega_0},1-\left(\frac{\omega}{\omega_0}\right)^2\right).
\]

- negatives \(K\): zusätzlicher konstanter Zweigversatz von \(-180^\circ\).
- Totzeit: \(-\omega T_t\cdot180^\circ/\pi\).

Die Summe ist mit der bereits vorhandenen entfalteten numerischen Phase abzugleichen.

## Schritt 11 – Quellenübliche Skizzenphase optional erzeugen

Neben der exakten Phasensumme darf eine ausdrücklich als **Näherung** gekennzeichnete Skizzenphase ausgegeben werden:

- Faktor erster Ordnung: Übergang von \(0.1\omega_k\) bis \(10\omega_k\), \(\pm45^\circ\) pro Dekade.
- Faktor zweiter Ordnung: Übergang von \(0.1\omega_0\) bis \(10\omega_0\), insgesamt \(\pm180^\circ\).
- „Phasensprung direkt am Knick“ nur als grobe klausurübliche Alternative, wenn die Aufgabenstellung ausdrücklich qualitative Skizzen zulässt.

## Schritt 12 – Numerische Kontrolle

Pflichtkontrollen:

1. Faktorprodukt rekonstruiert die reduzierte Übertragungsfunktion.
2. Summe der exakten Faktorbeiträge stimmt mit dem vorhandenen numerischen Frequenzgang überein.
3. Ursprungspole/-nullstellen liefern korrekte Anfangssteigung.
4. Hochfrequenzsteigung stimmt mit dem Relativgrad überein:

\[
20(\deg Z-\deg N)\;\mathrm{dB/Dekade}.
\]

5. Die Abweichung der asymptotischen Kurve nahe Knickstellen ist kein Fehler, sondern wird als Näherungsfehler ausgewiesen.

---

# 7. Standardgliederkatalog

## 7.1 P-Glied

**Kanonische Form**

\[
G_P(s)=K.
\]

**Voraussetzungen**

- reeller, von null verschiedener konstanter Faktor.

**Parameterbestimmung**

\[
K=G(s).
\]

**Bode-Beiträge**

\[
L=20\log_{10}|K|,
\qquad
m=0.
\]

\[
\varphi=
\begin{cases}
0^\circ,&K>0,\\
-180^\circ,&K<0.
\end{cases}
\]

**Grenzwerte**

Betrag und Phase sind frequenzunabhängig.

**Typische Fehler**

- negatives \(K\) im Logarithmus ohne Betrag,
- negative Verstärkung nur im Betrag, nicht in der Phase berücksichtigen.

**Quelle**

`skript.pdf`, Kap. 3.4.1, PDF-S. 76–77; `Tabelle_Standardglieder.pdf`, PDF-S. 1.

---

## 7.2 I-Glied

**Vorlesungskonvention**

\[
G_I(s)=\frac{1}{T_Is}.
\]

Das Skript bezeichnet den Parameter teilweise mit \(K_I\); für die Bode-Ausgabe ist die dimensionsklare Bezeichnung \(T_I\) vorzuziehen, solange die Originalnotation zusätzlich angegeben wird.

**Erkennung**

- einfacher Pol im Ursprung,
- keine weitere Dynamik.

**Bode-Beiträge**

\[
L(\omega)=-20\log_{10}(T_I\omega),
\]

Steigung:

\[
-20\,\mathrm{dB/Dekade}.
\]

Phase:

\[
-90^\circ.
\]

**Knickfrequenz**

Keine. Die Frequenz \(\omega=1/T_I\) ist nur die \(0\,\mathrm{dB}\)-Referenz.

**Grenzwerte**

\[
\omega\to0:\ |G|\to\infty,
\qquad
\omega\to\infty:\ |G|\to0.
\]

**Typische Fehler**

- I und D vertauschen,
- eine künstliche Knickfrequenz behaupten,
- Parameter \(T_I\) und Integrationsverstärkung \(1/T_I\) verwechseln.

**Quelle**

`skript.pdf`, Kap. 3.4.2, PDF-S. 77–78; `Tabelle_Standardglieder.pdf`, PDF-S. 1.

---

## 7.3 D-Glied

\[
G_D(s)=T_Ds.
\]

**Erkennung**

- einfache Nullstelle im Ursprung.

**Bode-Beiträge**

\[
L(\omega)=20\log_{10}(T_D\omega),
\]

\[
+20\,\mathrm{dB/Dekade},
\qquad
\varphi=+90^\circ.
\]

**Knickfrequenz**

Keine; \(1/T_D\) ist nur die \(0\,\mathrm{dB}\)-Referenz.

**Grenzwerte**

\[
\omega\to0:\ |G|\to0,
\qquad
\omega\to\infty:\ |G|\to\infty.
\]

**Typische Fehler**

- Vorzeichen von Steigung und Phase vertauschen,
- ideales D-Glied mit realem DT1/Hochpass verwechseln.

**Quelle**

`skript.pdf`, Kap. 3.4.3, PDF-S. 78–79; `Tabelle_Standardglieder.pdf`, PDF-S. 2.

---

## 7.4 PT1-Glied

\[
G_{PT1}(s)=\frac{K}{1+Ts}.
\]

**Voraussetzungen**

- reeller stabiler Pol bei \(-1/T\),
- \(T>0\).

**Parameterbestimmung aus \(as+b\)**

\[
as+b=b\left(1+\frac{a}{b}s\right),
\qquad
T=\frac{a}{b},
\qquad
\omega_k=\frac{b}{a}.
\]

Der Faktor \(b\) geht in die Gesamtverstärkung ein.

**Exakter Betrag und Phase**

\[
|G(j\omega)|=\frac{|K|}{\sqrt{1+(\omega T)^2}},
\]

\[
\varphi(\omega)=\arg K-\arctan(\omega T).
\]

**Asymptote**

- vor \(\omega_k\): Steigung 0,
- nach \(\omega_k\): \(-20\,\mathrm{dB/Dek}\).

**Kontrollpunkt**

\[
L(\omega_k)=20\log_{10}|K|-3.01\,\mathrm{dB},
\qquad
\varphi(\omega_k)=\arg K-45^\circ.
\]

**Quelle**

`skript.pdf`, Kap. 3.4.5 und 3.5.1, PDF-S. 80–81 und 85–87; `Tabelle_Standardglieder.pdf`, PDF-S. 1.

---

## 7.5 Reelle stabile Nullstelle / PD-Faktor

\[
G_Z(s)=1+Ts,
\qquad
G_{PD}(s)=K(1+T_Ds).
\]

**Erkennung**

- reelle LHP-Nullstelle bei \(-1/T\).

**Bode-Beiträge**

- vor \(1/T\): Steigung 0,
- nach \(1/T\): \(+20\,\mathrm{dB/Dek}\),
- Phase \(0^\circ\to+90^\circ\),
- bei der Ecke: \(+3.01\,\mathrm{dB}\) relativ zur Tieffrequenzasymptote und \(+45^\circ\).

**Typische Fehler**

- \(1+Ts\) als D-Glied statt als PD-Faktor bezeichnen,
- Nullstelle im Zähler wie einen Pol behandeln.

**Quelle**

`Tabelle_Standardglieder.pdf`, PDF-S. 2; offizielle Klausur WS25/26 Aufgabe 2d.

---

## 7.6 IT1-Glied

\[
G_{IT1}(s)=\frac{K}{T_Is(1+T_1s)}.
\]

**Zerlegung**

- P-Faktor \(K\),
- I-Glied,
- PT1-Glied.

**Knick**

\[
\omega_1=\frac1{T_1}.
\]

**Steigungen**

\[
-20\to-40\,\mathrm{dB/Dek}.
\]

**Phase**

\[
-90^\circ-\arctan(\omega T_1),
\]

also \(-90^\circ\to-180^\circ\).

**Quelle**

`skript.pdf`, Kap. 3.4.7, PDF-S. 83–84; `Tabelle_Standardglieder.pdf`, PDF-S. 1.

---

## 7.7 DT1-Glied / Hochpass erster Ordnung

\[
G_{DT1}(s)=\frac{T_Ds}{1+T_1s}.
\]

**Zerlegung**

- Nullstelle im Ursprung,
- PT1-Pol bei \(-1/T_1\),
- Verstärkungsparameter \(T_D\).

**Steigungen**

\[
+20\to0\,\mathrm{dB/Dek}.
\]

**Hochfrequenzgrenze**

\[
\lim_{\omega\to\infty}|G(j\omega)|=\frac{T_D}{T_1}.
\]

**Phase**

\[
\varphi=90^\circ-\arctan(\omega T_1),
\]

also \(+90^\circ\to0^\circ\).

**Quelle**

`skript.pdf`, Kap. 3.4.7, PDF-S. 83–84; `Tabelle_Standardglieder.pdf`, PDF-S. 2; offizielle Übung 04.

---

## 7.8 PI-Glied

\[
G_{PI}(s)=K\left(1+\frac1{T_Is}\right)
=K\frac{1+T_Is}{T_Is}.
\]

**Zerlegung**

- Pol im Ursprung,
- reelle Nullstelle bei \(-1/T_I\),
- konstante Verstärkung \(K\).

**Steigungen**

\[
-20\to0\,\mathrm{dB/Dek}.
\]

**Phase**

\[
\varphi=-90^\circ+\arctan(\omega T_I),
\]

also \(-90^\circ\to0^\circ\).

**Grenzwerte**

\[
\omega\to\infty:\ G(j\omega)\to K.
\]

**Typische Fehler**

- \(K\) doppelt in I- und P-Anteil einrechnen,
- \(T_I\) statt \(1/T_I\) als Knickfrequenz verwenden.

**Quelle**

`Tabelle_Standardglieder.pdf`, PDF-S. 2; Reglerdefinition im Skript Kap. 6.1.

---

## 7.9 PD-Glied

\[
G_{PD}(s)=K(1+T_Ds).
\]

**Steigungen**

\[
0\to+20\,\mathrm{dB/Dek}.
\]

**Phase**

\[
\arg K+\arctan(\omega T_D).
\]

**Knick**

\[
\omega_D=\frac1{T_D}.
\]

**Quelle**

`Tabelle_Standardglieder.pdf`, PDF-S. 2; Klausur WS25/26 Aufgabe 2d.

---

## 7.10 PIT1-Glied

\[
G_{PIT1}(s)=K\frac{1+1/(T_Is)}{1+T_1s}
=K\frac{1+T_Is}{T_Is(1+T_1s)}.
\]

**Primitive Zerlegung**

- P,
- Ursprungspol,
- LHP-Nullstelle bei \(1/T_I\),
- LHP-Pol bei \(1/T_1\).

Die Bode-Form hängt von der Reihenfolge der beiden Knickfrequenzen ab. Die Tabelle zeigt den üblichen Fall \(T_1<T_I\), also

\[
\frac1{T_I}<\frac1{T_1}.
\]

Dann:

\[
-20\to0\to-20\,\mathrm{dB/Dek}.
\]

**Technische Festlegung**

Compound-Name nur als zusätzliche Klassifikation. Die Rechenlogik bleibt die primitive Faktorzerlegung.

**Quelle**

`Tabelle_Standardglieder.pdf`, PDF-S. 2.

---

## 7.11 PDT1-Glied / Lead-Lag-Faktor

\[
G_{PDT1}(s)=K\frac{1+T_Ds}{1+T_1s}.
\]

**Primitive Zerlegung**

- P,
- LHP-Nullstelle bei \(1/T_D\),
- LHP-Pol bei \(1/T_1\).

Für den tabellarischen Lead-Fall \(T_1<T_D\):

\[
\frac1{T_D}<\frac1{T_1},
\]

\[
0\to+20\to0\,\mathrm{dB/Dek}.
\]

Hochfrequenzniveau:

\[
20\log_{10}\left|K\frac{T_D}{T_1}\right|.
\]

Phase:

\[
\arg K+\arctan(\omega T_D)-\arctan(\omega T_1).
\]

Bei umgekehrter Reihenfolge entsteht ein Lag-Glied mit negativer Phasenmulde.

**Quelle**

`Tabelle_Standardglieder.pdf`, PDF-S. 2; Skript Kap. 6.1 für Korrekturglieder.

---

## 7.12 PT2-Glied

\[
G_{PT2}(s)=
\frac{K}
{1+2D\frac{s}{\omega_0}+\left(\frac{s}{\omega_0}\right)^2}.
\]

**Parameterbestimmung aus**

\[
a_2s^2+a_1s+a_0
=a_0\left[1+\frac{a_1}{a_0}s+\frac{a_2}{a_0}s^2\right].
\]

Dann:

\[
\omega_0=\sqrt{\frac{a_0}{a_2}},
\qquad
D=\frac{a_1}{2\sqrt{a_0a_2}}.
\]

Der Faktor \(a_0\) geht in die Gesamtverstärkung ein.

**Voraussetzungen**

- \(a_0a_2>0\) für reelles \(\omega_0\),
- für stabiles LHP-PT2: \(D>0\).

**Asymptote**

\[
0\to-40\,\mathrm{dB/Dek}
\]

bei \(\omega_0\).

**Phase**

\[
\varphi=-\operatorname{atan2}\left(2D\frac{\omega}{\omega_0},1-\left(\frac{\omega}{\omega_0}\right)^2\right).
\]

Grenzen:

\[
0^\circ\to-180^\circ,
\qquad
\varphi(\omega_0)=-90^\circ.
\]

**Resonanz**

Bei

\[
D<\frac1{\sqrt2}
\]

kann eine Resonanzüberhöhung auftreten. Sie ist im asymptotischen Verlauf nicht sichtbar und muss aus dem exakten numerischen Verlauf übernommen werden.

**Quelle**

`skript.pdf`, Kap. 3.4.6, PDF-S. 81–83; `Tabelle_Standardglieder.pdf`, PDF-S. 1.

---

## 7.13 PID-Glied

\[
G_{PID}(s)=K\left(1+T_Ds+\frac1{T_Is}\right)
=K\frac{T_IT_Ds^2+T_Is+1}{T_Is}.
\]

**Struktur**

- Pol im Ursprung,
- quadratisches Zählerpolynom.

Diskriminante der Nullstellen:

\[
\Delta=T_I^2-4T_IT_D=T_I(T_I-4T_D).
\]

Fälle:

1. \(T_I>4T_D\): zwei reelle LHP-Nullstellen.
2. \(T_I=4T_D\): doppelte reelle Nullstelle.
3. \(T_I<4T_D\): komplex konjugiertes Nullstellenpaar.

**Asymptotische Grenzsteigungen**

\[
\omega\to0:\ -20\,\mathrm{dB/Dek},
\qquad
\omega\to\infty:\ +20\,\mathrm{dB/Dek}.
\]

**Technische Festlegung**

Das PID-Label ist eine Präsentationsklassifikation. Für die Bode-Rechnung werden Ursprungspol und die tatsächlichen Zählernullstellen verwendet.

**Quelle**

`Tabelle_Standardglieder.pdf`, PDF-S. 3; Skript Kap. 6.1.

---

## 7.14 Totzeitglied

\[
G_T(s)=Ke^{-sT_t}.
\]

**Betrag**

\[
|G_T(j\omega)|=|K|.
\]

**Phase**

\[
\varphi_T(\omega)=\arg K-\omega T_t\frac{180^\circ}{\pi}.
\]

**Knickfrequenz und Steigung**

Keine; Betrag konstant.

**Technische Einschränkung**

Eine Totzeit ist nicht rational und fällt deshalb nicht in den vorhandenen rationalen Parser. Für das MVP nur als separater optionaler Eingabeparameter zulassen, nicht durch eine willkürliche Padé-Approximation vortäuschen.

**Quelle**

`skript.pdf`, Kap. 3.4.4, PDF-S. 79–80; `Tabelle_Standardglieder.pdf`, PDF-S. 3.

---

## 7.15 Nichtminimalphasige Nullstelle

\[
G_{NMP}(s)=1-Ts,
\qquad T>0.
\]

**Betrag**

Identisch zu \(1+Ts\):

\[
|1-j\omega T|=\sqrt{1+(\omega T)^2}.
\]

**Phase**

\[
-\arctan(\omega T)
\]

statt \(+\arctan(\omega T)\).

**Bedeutung**

Eine reine Betragsauswertung kann LHP- und RHP-Nullstelle nicht unterscheiden. Die Pol-/Nullstellenlage aus dem vorhandenen Root-Finder ist daher zwingend zu verwenden.

**Quellenrelevanz**

Nicht zentral in den beiden direkten Bode-Klausuraufgaben, aber in offiziellen Stabilitäts-/Nyquist-Aufgaben vorhanden und für Reserven relevant.

---

# 8. Diagramm-zu-Übertragungsfunktion-Modus

Dieser Modus ist klausurrelevant, weil beide Klausuren vom gegebenen Bode-Diagramm zur Übertragungsfunktion führen. Er benötigt **keine Bild- oder OCR-Erkennung**. Die Eingabe erfolgt über abgelesene Segmente.

## 8.1 Benötigte Eingaben

- Anfangssteigung,
- Liste der Knickfrequenzen,
- Steigung vor und nach jedem Knick,
- mindestens ein Amplitudenwert bei bekannter Frequenz,
- beobachtete Phasen-Grenzwerte beziehungsweise Phasenrichtung,
- optional erkannter Gleichlauf mehrerer Knicke.

## 8.2 Deterministische Rückschlüsse

### Ursprungselemente

\[
q=\frac{m_0}{20}.
\]

- \(q=-1\): ein Integrator,
- \(q=+1\): ein Differenzierer,
- allgemeine ganze Werte: Mehrfachheit.

### Knickereignisse

\[
\Delta n=\frac{\Delta m}{20}.
\]

- \(+1\): eine Zählernullstelle erster Ordnung,
- \(-1\): ein Nennerpol erster Ordnung,
- \(+2\): zwei gleichzeitige Nullstellen oder quadratischer Zählerfaktor,
- \(-2\): zwei gleichzeitige Pole oder PT2-Faktor.

### Verstärkung

Ein abgelesener Punkt \((\omega_r,L_r)\) bestimmt \(|K|\), nachdem alle dynamischen asymptotischen Beiträge bei \(\omega_r\) abgezogen wurden.

## 8.3 Ambiguitäten

Eine Steigungsänderung von \(40\,\mathrm{dB/Dek}\) unterscheidet nicht eindeutig zwischen:

- zwei identischen Faktoren erster Ordnung,
- einem Faktor zweiter Ordnung.

Die Phase, Resonanzform oder Aufgabenangabe muss zur Entscheidung herangezogen werden. Fehlt diese Information, sind mehrere Kandidaten auszugeben. Keine scheinbar eindeutige Klassifikation erfinden.

---

# 9. Klausurtaugliche Ausgabe

## 9.1 Kopfblock

1. Gegebene Übertragungsfunktion.
2. Exakt reduzierte Form.
3. Normierte Faktorzerlegung.
4. Kurzer Satz zur Stabilitäts-/Phasenbesonderheit: negative Verstärkung, Ursprungspole, RHP-Nullstelle, Totzeit.

## 9.2 Gliedertabelle

Pflichtspalten:

| Nr. | Lage | Standardglied/Faktor | kanonische Form | Parameter | Vielfachheit | Knick \(\omega_k\) | Pegelbeitrag | \(\Delta m\) | exakter Phasenbeitrag |
|---:|---|---|---|---|---:|---:|---|---:|---|

„Lage“ bezeichnet Zähler, Nenner oder Ursprung.

## 9.3 Knick- und Steigungstabelle

| Ereignis | \(\omega_k\) | beteiligte Faktoren | Steigung davor | Änderung | Steigung danach |
|---:|---:|---|---:|---:|---:|

Bei gleichen Knicken müssen alle Faktoren in derselben Zeile erscheinen.

## 9.4 Asymptotische Intervallgleichungen

Für jedes Intervall:

\[
L_{asym}(\omega)=L_r+m\log_{10}\left(\frac{\omega}{\omega_r}\right),
\]

wobei \(m\) in dB/Dekade angegeben wird.

## 9.5 Phasentabelle

Separat ausgeben:

1. exakte elementweise Phase,
2. Summe der exakten Phase,
3. optionale Skizzenphase als Näherung.

## 9.6 Kontrollfrequenzen

Mindestens:

- \(0.1\omega_k\),
- \(\omega_k\),
- \(10\omega_k\),
- geometrisches Mittel benachbarter Knickfrequenzen,
- vorhandene Amplituden- und Phasendurchtrittsfrequenzen.

Tabelle:

| \(\omega\) | exakter Betrag [dB] | Asymptote [dB] | Differenz [dB] | exakte Phase [°] |
|---:|---:|---:|---:|---:|

## 9.7 Diagrammanforderungen

- logarithmische Frequenzachse,
- Amplitudengang in dB und Phasengang in Grad,
- Achsen und Einheiten beschriftet,
- vertikale Hilfslinien an allen Knickfrequenzen,
- Anfangs- und Endsteigungen beschriftet,
- exakter numerischer Verlauf und asymptotische Konstruktion klar in der Legende getrennt,
- einzelne Standardgliedbeiträge optional, aber visuell von der Summenkurve getrennt,
- keine asymptotische Linie als exakte Lösung bezeichnen.

## 9.8 LaTeX-Rechenweg

Kompakt und abschreibbar:

1. Normierung.
2. Tabelle der Faktoren.
3. Knickfrequenzen.
4. Steigungsfolge.
5. Phasensumme.
6. Endergebnis.

Keine unnötigen numerischen Rohlisten.

---

# 10. Referenzaufgaben

## Referenz 1 – einzelnes PT1

**Fundstelle:** `Regelungstechnik_Tutorium_komplett.pdf`, Tutorium 04, Aufgabe 1a; ergänzend `RT1_Rechenwege_Master(12).md`.

\[
G(s)=\frac1{1+2s}.
\]

Normierung bereits gegeben:

\[
K=1,
\qquad
T=2,
\qquad
\omega_k=0.5.
\]

Asymptote:

\[
L_{asym}(\omega)=
\begin{cases}
0,&\omega\le0.5,\\
-20\log_{10}(\omega/0.5),&\omega\ge0.5.
\end{cases}
\]

Exakt:

\[
L(\omega)=-10\log_{10}(1+4\omega^2),
\]

\[
\varphi(\omega)=-\arctan(2\omega).
\]

Kontrollpunkt:

\[
L(0.5)=-3.01\,\mathrm{dB},
\qquad
\varphi(0.5)=-45^\circ.
\]

---

## Referenz 2 – zwei identische PT1

**Fundstelle:** `Regelungstechnik_Tutorium_komplett.pdf`, Tutorium 04, Aufgabe 3a.

\[
G(s)=\frac1{(1+0.1s)^2}.
\]

Knick:

\[
\omega_k=10,
\]

Vielfachheit 2.

Steigung:

\[
0\to-40\,\mathrm{dB/Dek}.
\]

Phase:

\[
\varphi=-2\arctan(0.1\omega).
\]

Bei der Ecke:

\[
L(10)=-6.02\,\mathrm{dB},
\qquad
\varphi(10)=-90^\circ.
\]

Der Fall prüft zwingend die Gruppierung gleicher Knickfrequenzen.

---

## Referenz 3 – drei identische PT1

**Fundstelle:** `Regelungstechnik_Tutorium_komplett.pdf`, Tutorium 04, Aufgabe 3b.

\[
G(s)=\frac1{(1+0.1s)^3}.
\]

\[
\omega_k=10,
\qquad
0\to-60\,\mathrm{dB/Dek}.
\]

\[
\varphi=-3\arctan(0.1\omega).
\]

Bei der Ecke:

\[
L(10)=-9.03\,\mathrm{dB},
\qquad
\varphi(10)=-135^\circ.
\]

---

## Referenz 4 – DT1/Hochpass

**Fundstelle:** `Regelungstechnik_Übung_Aufg-u-Lösungen.pdf`, Übung 04, Aufgabe 1.

Für \(R=C=1\):

\[
G(s)=\frac{s}{1+s}.
\]

Zerlegung:

- Nullstelle im Ursprung,
- PT1-Pol bei \(-1\).

Knick:

\[
\omega_k=1.
\]

Steigungen:

\[
+20\to0\,\mathrm{dB/Dek}.
\]

Exakt:

\[
|G(j\omega)|=\frac{\omega}{\sqrt{1+\omega^2}},
\]

\[
\varphi=90^\circ-\arctan\omega.
\]

Bei der Ecke:

\[
L(1)=-3.01\,\mathrm{dB},
\qquad
\varphi(1)=45^\circ.
\]

---

## Referenz 5 – Hochpass und Tiefpass als Bandpass

**Fundstelle:** `Regelungstechnik_Übung_Aufg-u-Lösungen.pdf`, Übung 04, Reihenschaltung; offizielle Variante mit \(\omega_{HP}=1\) und \(\omega_{TP}=100\).

\[
G(s)=\frac{s}{(1+s)(1+0.01s)}.
\]

Ereignisse:

- Ursprung: \(+20\,\mathrm{dB/Dek}\),
- \(\omega=1\): Pol, Änderung \(-20\),
- \(\omega=100\): Pol, Änderung \(-20\).

Steigungen:

\[
+20\to0\to-20\,\mathrm{dB/Dek}.
\]

Phase:

\[
\varphi=90^\circ-\arctan\omega-\arctan(0.01\omega).
\]

Der Durchlassbereich liegt näherungsweise zwischen 1 und \(100\,\mathrm{s^{-1}}\).

---

## Referenz 6 – Klausur SS2025

**Fundstelle:** `RT_Klausur_SS2025-komplett.pdf`, Aufgabe 2b–d.

\[
G(s)=\frac{100}{s(1+10s)}.
\]

Zerlegung:

\[
K=100,
\qquad
\text{I-Glied},
\qquad
\text{PT1 mit }\omega_k=0.1.
\]

Steigungen:

\[
-20\to-40\,\mathrm{dB/Dek}.
\]

Phase:

\[
\varphi=-90^\circ-\arctan(10\omega).
\]

Exakter Amplitudendurchtritt aus

\[
\frac{100}{\omega\sqrt{1+100\omega^2}}=1
\]

liefert

\[
\omega_c\approx3.1615.
\]

Dann:

\[
\varphi(\omega_c)\approx-178.188^\circ,
\]

\[
\boxed{
\Delta\varphi\approx1.812^\circ
}
\]

und damit konsistent zur grafischen Klausurlösung von etwa \(2^\circ\).

**Wichtiger Grenzfall:** Die Phase erreicht \(-180^\circ\) bei diesem exakten Modell erst asymptotisch. Eine endliche exakte Phasendurchtrittsfrequenz existiert nicht; die exakte Verstärkungsreserve ist daher unendlich. Die offizielle grafische Musterlösung liest aus der vorgegebenen Zeichnung \(20\,\mathrm{dB}\) ab. Der Programmblock muss beide Aussagen getrennt ausgeben:

- „grafisch aus Aufgabenabbildung: 20 dB“,
- „aus rekonstruierter exakter Übertragungsfunktion: keine endliche Phasendurchtrittsfrequenz, Verstärkungsreserve \(\infty\)“.

---

## Referenz 7 – Klausur WS25/26, PT1-Erkennung

**Fundstelle:** `RT-Klausur_WS_25_26-komplett.pdf`, Aufgabe 2b–c.

\[
G(s)=\frac{100}{1+2s}.
\]

\[
K=100,
\qquad
\omega_k=0.5.
\]

Asymptote:

- Startniveau \(40\,\mathrm{dB}\),
- ab \(0.5\): \(-20\,\mathrm{dB/Dek}\).

Exakter Amplitudendurchtritt:

\[
\frac{100}{\sqrt{1+4\omega_c^2}}=1
\]

\[
\omega_c=\frac{\sqrt{9999}}2\approx49.9975.
\]

\[
\varphi(\omega_c)=-\arctan(2\omega_c)\approx-89.427^\circ.
\]

Korrekte Phasenreserve:

\[
\boxed{
\Delta\varphi\approx90.573^\circ
}.
\]

Die offizielle Lösung nennt \(270^\circ\); das ist ein Vorzeichenfehler.

---

## Referenz 8 – Klausur WS25/26, PD-Glied

**Fundstelle:** `RT-Klausur_WS_25_26-komplett.pdf`, Aufgabe 2d.

\[
G(s)=10(1+0.002s).
\]

\[
K=10,
\qquad
T_D=0.002,
\qquad
\omega_D=500.
\]

Amplitude:

- Start \(20\,\mathrm{dB}\),
- ab 500: \(+20\,\mathrm{dB/Dek}\).

Phase:

\[
\varphi=\arctan(0.002\omega),
\]

\[
0^\circ\to90^\circ,
\qquad
\varphi(500)=45^\circ.
\]

Exakter Betrag an der Ecke:

\[
L(500)=23.01\,\mathrm{dB}.
\]

---

## Referenz 9 – Klausur WS25/26, Reihenschaltung

**Fundstelle:** `RT-Klausur_WS_25_26-komplett.pdf`, Aufgabe 2e.

\[
G(s)=1000\frac{1+0.002s}{1+2s}.
\]

Knicke:

\[
\omega_p=0.5,
\qquad
\omega_z=500.
\]

Steigungen:

\[
0\to-20\to0\,\mathrm{dB/Dek}.
\]

Pegel:

- Tieffrequenzniveau \(60\,\mathrm{dB}\),
- Hochfrequenzgrenze

\[
20\log_{10}\left(1000\frac{0.002}{2}\right)=0\,\mathrm{dB}.
\]

Phase:

\[
\varphi=\arctan(0.002\omega)-\arctan(2\omega).
\]

Sie beginnt bei \(0^\circ\), besitzt eine negative Phasenmulde und kehrt für \(\omega\to\infty\) zu \(0^\circ\) zurück. Das Minimum liegt bei

\[
\omega=\sqrt{0.5\cdot500}\approx15.811
\]

mit

\[
\varphi_{min}\approx-86.378^\circ.
\]

Der Lösungstext „Ende bei 90°“ ist falsch.

---

## Referenz 10 – negative Verstärkung, I und Nullstelle

**Fundstelle:** `Regelungstechnik_Übung_Aufg-u-Lösungen.pdf`, Übung 06, Aufgabe 1.

\[
G(s)=-\frac{10}{s}(1+s)\frac1{1000}
=-0.01\frac{1+s}{s}.
\]

Zerlegung:

- \(K=-0.01\),
- Pol im Ursprung,
- LHP-Nullstelle bei \(-1\).

Amplitude:

\[
L=20\log_{10}(0.01)-20\log_{10}\omega
+20\log_{10}\sqrt{1+\omega^2}.
\]

Asymptotisch:

- unter 1: \(-20\,\mathrm{dB/Dek}\),
- über 1: \(0\,\mathrm{dB/Dek}\),
- Hochfrequenzniveau \(-40\,\mathrm{dB}\).

Phase kann konsistent als

\[
-180^\circ-90^\circ+\arctan\omega
=-270^\circ+\arctan\omega
\]

entfaltet werden. Die äquivalente Hauptphase ist \(90^\circ+\arctan\omega\) modulo \(360^\circ\).

---

## Referenz 11 – zwei getrennte PT1-Knicke

**Fundstelle:** `Regelungstechnik_Übung_Aufg-u-Lösungen.pdf`, Übung 06, Diagrammrekonstruktion.

\[
G(s)=\frac{10}{(1+0.1s)(1+0.001s)}.
\]

\[
K=10,
\qquad
\omega_{p1}=10,
\qquad
\omega_{p2}=1000.
\]

Steigungen:

\[
0\to-20\to-40\,\mathrm{dB/Dek}.
\]

Phase:

\[
\varphi=-\arctan(0.1\omega)-\arctan(0.001\omega).
\]

Der Fall prüft sortierte Knickereignisse und korrekte Zwischensteigung.

---

## Referenz 12 – PT2 mit Zählernullstelle

**Fundstelle:** `Regelungstechnik_Übung_Aufg-u-Lösungen.pdf`, Übung 04, Einmassenschwinger.

\[
G(s)=\frac{20s+500}{s^2+20s+500}.
\]

Normierung:

\[
G(s)=\frac{1+0.04s}{1+0.04s+0.002s^2}.
\]

Nullstelle:

\[
\omega_z=25.
\]

PT2-Parameter:

\[
\omega_0=\sqrt{500}\approx22.361,
\]

\[
D=\frac{20}{2\sqrt{500}}\approx0.4472.
\]

Steigungen:

- zunächst 0,
- PT2-Ereignis ungefähr bei \(22.36\): \(-40\),
- Nullstelle bei 25: \(+20\),
- endgültig \(-20\,\mathrm{dB/Dek}\).

Exakt bei \(\omega_0\):

\[
|G(j\omega_0)|=1.5,
\qquad
L(\omega_0)\approx3.522\,\mathrm{dB}.
\]

Die asymptotische Kurve bildet diese Resonanzüberhöhung nicht ab.

---

## Referenz 13 – PI-Glied

**Status:** [SYNTHETISCHER TEST] aus der offiziellen Standardform.

\[
G(s)=2\left(1+\frac1{5s}\right)
=0.4\frac{1+5s}{s}.
\]

Zerlegung:

- \(K=0.4\),
- Ursprungspol,
- Nullstelle bei \(\omega_z=0.2\).

Steigungen:

\[
-20\to0\,\mathrm{dB/Dek}.
\]

Hochfrequenzniveau:

\[
20\log_{10}2=6.02\,\mathrm{dB}.
\]

Phase:

\[
-90^\circ+\arctan(5\omega).
\]

---

## Referenz 14 – PID mit zwei reellen Nullstellen

**Status:** [SYNTHETISCHER TEST] aus der offiziellen Standardform.

\[
G(s)=1+0.25s+\frac1{4s}
=\frac{s^2+4s+1}{4s}.
\]

Nullstellen:

\[
s_{z,1/2}=-2\pm\sqrt3.
\]

Knickfrequenzen als Beträge:

\[
\omega_{z1}=2-\sqrt3\approx0.268,
\]

\[
\omega_{z2}=2+\sqrt3\approx3.732.
\]

Steigungen:

\[
-20\to0\to+20\,\mathrm{dB/Dek}.
\]

Der Fall prüft, dass ein PID nicht als unzerlegbarer Spezialblock behandelt wird.

---

# 11. Fehler- und Grenzfallbehandlung

## 11.1 Pol-Nullstellen-Kürzung

Da die Eingabe bereits exakt reduziert ist, dürfen gekürzte Pole und Nullstellen nicht erneut als Bode-Faktoren erscheinen. Andernfalls entstehen falsche Knicke, obwohl sich die exakten Beiträge gegenseitig aufheben würden.

## 11.2 Nullübertragungsfunktion

\[
G(s)\equiv0
\]

hat Betrag \(-\infty\,\mathrm{dB}\), aber keine sinnvoll definierte Phase. Keine Standardgliederzerlegung ausgeben.

## 11.3 Unechte Übertragungsfunktion

Bei \(\deg Z>\deg N\) entstehen positive Hochfrequenzsteigungen. Die Zerlegung bleibt mathematisch möglich, aber die Funktion ist nicht streng echt. Dies muss angezeigt werden.

## 11.4 Wurzeln nahe dem Ursprung

Keine stillschweigende Klassifikation über eine grobe Gleitkommatoleranz. Ursprungsklassifikation nach Möglichkeit aus den exakten Polynomkoeffizienten beziehungsweise symbolischen Faktoren übernehmen.

## 11.5 Fast gleiche Knickfrequenzen

- Gliedertabelle getrennt,
- Ereignistabelle nur dann gruppieren, wenn Gleichheit exakt oder innerhalb einer dokumentierten Toleranz liegt,
- bei bloßer Nähe keine künstliche Vielfachheit erzeugen.

## 11.6 Instabile Pole

Ein RHP-Pol hat denselben Betragsbeitrag wie der entsprechende LHP-Pol, aber einen anderen Phasenbeitrag. Zusätzlich muss „offenes System instabil“ markiert werden, weil dies für Nyquist und Reserven entscheidend ist.

## 11.7 Negative und komplexe Koeffizienten

Für RT1 ist eine reelle Übertragungsfunktion zu erwarten. Nicht reell konjugiert gepaarte Wurzeln oder signifikant komplexe Restverstärkung sind als Eingabe-/Numerikproblem zu melden.

---

# 12. Quellenwidersprüche und verbindliche Korrekturen

## 12.1 Partialbruchzerlegung versus Reihenschaltung

**Betroffene Quelle:** `skript.pdf`, gedruckte S. 53.

Die Aussage, eine Partialbruchzerlegung entspreche einer Reihenschaltung, ist falsch. Reihenschaltung entspricht Multiplikation beziehungsweise Faktorzerlegung; Partialbruchzerlegung entspricht einer Summe.

**Festlegung:** Bode-Synthese ausschließlich aus Faktorzerlegung.

## 12.2 I- und D-Beiträge im Skript vertauscht

**Betroffene Quelle:** `skript.pdf`, gedruckte S. 72, Tabelle/Fließtext zur Zerlegung.

Dort werden I- und D-Steigung beziehungsweise Phase vertauscht. Korrekt:

- I: \(-20\,\mathrm{dB/Dek}\), \(-90^\circ\).
- D: \(+20\,\mathrm{dB/Dek}\), \(+90^\circ\).

**Festlegung:** Standardgliedkapitel, Tabelle der Standardglieder und direkte Rechnung haben Vorrang.

## 12.3 Hochpassphase ohne Arkustangens

**Betroffene Quelle:** `Regelungstechnik_Übung_Aufg-u-Lösungen.pdf`, Übung 04, Lösung PDF-S. 63.

Die ausgeschriebene Endformel lässt den Arkustangens weg. Korrekt:

\[
\varphi=\arctan\left(\frac1{\omega RC}\right)
=90^\circ-\arctan(\omega RC).
\]

Die offizielle Wertetabelle verwendet die korrekten Winkel.

## 12.4 SS2025: grafische und exakte Verstärkungsreserve

Die vorgegebene Grafik/Musterlösung liefert 20 dB. Die aus derselben Lösung rekonstruierte exakte Funktion \(100/[s(1+10s)]\) erreicht \(-180^\circ\) erst im Grenzwert, also ist die exakte Verstärkungsreserve unendlich.

**Festlegung:** grafischen Quellenwert und exakten Modellwert getrennt nennen.

## 12.5 WS25/26: Phasenreserve 270°

Die Musterlösung setzt eine negative Phase falsch in \(180^\circ-\varphi\) ein. Für ein PT1 mit Phase ungefähr \(-90^\circ\) beträgt die Phasenreserve ungefähr \(90^\circ\), nicht 270°.

## 12.6 WS25/26: Endphase der Reihenschaltung

Für

\[
1000\frac{1+0.002s}{1+2s}
\]

gehen Zähler- und Nennerphase beide gegen \(+90^\circ\); die Gesamtphase geht gegen \(0^\circ\). Der Lösungstext „Ende bei 90°“ ist falsch.

## 12.7 WS25/26: Punktverteilung

Aufgabenbogen und Lösungsrubrik stimmen bei den Teilaufgaben c–e nicht überein. Für die Priorisierung ist deshalb eine Punktespanne auszuweisen, keine scheinexakte Summe.

---

# 13. MVP-Priorisierung

## A. Günstiges, punktestarkes MVP

| Funktion | direkte Punkte | indirekt unterstützte Punkte | Codex-Aufwand | Wiederverwendung | benötigte vorhandene Werte |
|---|---:|---:|---|---|---|
| Normierte Faktorzerlegung aus vorhandenen Polen/Nullstellen | SS 10, WS 4 | Reserven, Nyquist, Regler | niedrig–mittel | sehr hoch | reduzierte Polynome, Pole, Nullstellen |
| Ursprungspole/-nullstellen und Anfangssteigung | Teil von SS/WS | Reserven, Plausibilität | niedrig | sehr hoch | Pol-/Nullstellenliste |
| Reelle LHP-Faktoren erster Ordnung und Vielfachheiten | SS/WS Kern | fast alle Frequenzaufgaben | niedrig | sehr hoch | Pole/Nullstellen |
| Knickereignis- und Steigungstabelle | SS 2+10, WS 4+Skizzen | Korrekturglied | niedrig | sehr hoch | normierte Faktoren |
| Asymptotische Amplitudensynthese | WS 4–6 + 8–10 | Reglerauslegung | niedrig–mittel | sehr hoch | Faktoren, K |
| Exakte Phasensumme einfacher Faktoren | unterstützt WS c | Reserven/Nyquist | niedrig | sehr hoch | vorhandene Phase, Faktoren |
| P/I/D/PT1/IT1/DT1/PI/PD/PIT1/PDT1 als Labels | SS/WS | Lernmodus, Ausgabe | niedrig | hoch | primitive Faktoren |
| Manuelle Diagrammsegment-Eingabe zur inversen Erkennung | SS 12, WS 4 | schnelle Klausureingabe | mittel | hoch | Steigungen, Knicke, Referenzpegel |
| Klausurtabelle und LaTeX-Rechenweg | alle direkten Punkte | Abschreibbarkeit | niedrig | sehr hoch | bestehende LaTeX-Infrastruktur |
| Abgleich gegen vorhandenen numerischen Bode | Fehlervermeidung | alle Folgemodule | niedrig | sehr hoch | numerischer Frequenzgang |

**MVP-Abdeckung:**

- SS2025: sichere Unterstützung der 12 direkten Zerlegungspunkte und wesentliche Vorarbeit für weitere 12 Punkte.
- WS25/26: sichere Unterstützung von ungefähr 16 bis 20 direkten Punkten je nach maßgeblicher Punktefassung und Vorarbeit für die Phasenreserve.

## B. Sinnvolle Erweiterungen

| Funktion | Nutzen | Codex-Aufwand | Priorität |
|---|---|---|---|
| PT2-/komplexe Quadratik-Erkennung einschließlich \(D,\omega_0\) | offizielle Übung, Resonanz, allgemeine Strecken | mittel | hoch nach MVP |
| Resonanzdiagnostik und exakter/asymptotischer Fehler | verhindert falsche PT2-Skizzen | mittel | hoch |
| Negative Verstärkung mit konsistenter entfalteter Phase | offizielle Übung, Nyquist | niedrig–mittel | hoch |
| RHP-/nichtminimalphasige Nullstellen | Reserven und Nyquist | mittel | mittel |
| PID-Nullstellenklassifikation | Standardtabelle und Regler | mittel | mittel |
| Quellenübliche lineare Phasennäherung | bessere Handskizzen | niedrig | mittel |
| Grafischer Quellenwert versus exakter Modellwert | behebt Klausurwidersprüche | mittel | hoch |

## C. Teure Spezialfälle

| Funktion | Grund gegen MVP |
|---|---|
| Expliziter Totzeitparser und nicht-rationale Algebra | vorhandener Parser ist rational; zusätzlicher Symboltyp nötig |
| Automatische OCR/Bilderkennung von Bode-Diagrammen | hoher Aufwand, fehleranfällig, für Klausur nicht nötig; manuelle Segmentwerte sind schneller und kontrollierbarer |
| Allgemeine Suche über alle mehrdeutigen Hochordnungszerlegungen | geringe Zusatzpunktabdeckung, hohe kombinatorische Komplexität |
| PIDT1 und beliebige zusammengesetzte Namenshierarchien | primitive Faktoren reichen rechnerisch bereits aus |
| Automatische Reglerauslegung im selben Modul | gehört in separaten Korrekturglied-/Reglerblock und würde Verantwortlichkeiten vermischen |
| Padé-Approximation von Totzeiten ohne ausdrückliche Anforderung | verändert Pole/Nullstellen und kann falsche Klausuraussagen erzeugen |

---

# 14. Schnittstellen und Verantwortungsgrenzen

## 14.1 Dieser Block übernimmt

- Faktor-Normierung,
- Standardgliederklassifikation,
- Knickereignisse,
- asymptotische Amplitude,
- elementweise Phasenbeiträge,
- Klausurtabellen,
- LaTeX-Rechenweg,
- Abgleich mit vorhandenem numerischem Bode.

## 14.2 Dieser Block übernimmt nicht

- Parsing rationaler Funktionen,
- symbolische Kürzung,
- erneute Pol-/Nullstellenberechnung,
- numerischen Frequenzgang,
- allgemeine Diagramm-Engine,
- Reserveberechnung als eigenständiges Modul,
- Lead-/Lag-Auslegung,
- Nyquist-Auswertung,
- OCR.

## 14.3 Übergabewerte an andere Blöcke

Ausgabe für Reserve-/Reglerblock:

- normierte Faktoren,
- Knickfrequenzen,
- genaue und asymptotische Steigungsfolge,
- Ursprungspolzahl,
- RHP-Pole und RHP-Nullstellen,
- negatives Verstärkungsvorzeichen,
- optional Totzeit,
- Kontrollfrequenzen,
- exakte numerische Durchtrittsfrequenzen aus vorhandenem Frequenzgang.

---

# 15. Abnahmekriterien

Der spätere Programmblock ist fachlich abgenommen, wenn er:

1. alle Referenzfälle 1–12 korrekt rekonstruiert,
2. gleiche Pole korrekt als Vielfachheit gruppiert,
3. I und D nicht vertauscht,
4. negative Verstärkung in Betrag und Phase korrekt behandelt,
5. RHP-Nullstellen im Betrag gleich, in der Phase entgegengesetzt behandelt,
6. bei PT2 Resonanz nicht als asymptotische Gerade ausgibt,
7. exakten und asymptotischen Verlauf sichtbar trennt,
8. die SS2025- und WS25/26-Quellenwidersprüche explizit meldet,
9. keine Partialbruchzerlegung als Reihenschaltung verwendet,
10. keine vorhandene Parser-, Root- oder Frequenzganglogik dupliziert,
11. einen vollständig abschreibbaren LaTeX-Rechenweg erzeugt,
12. bei mehrdeutiger Diagrammrekonstruktion mehrere Kandidaten statt einer erfundenen Eindeutigkeit ausgibt.

---

# 16. Gesamtempfehlung

Das MVP sollte zuerst **primitive Bode-Faktoren** statt eines großen Katalogs hart codierter zusammengesetzter Glieder beherrschen. P, I, D, reelle Pole, reelle Nullstellen und Vielfachheiten reichen bereits für beide Klausurkerne. IT1, DT1, PI, PD, PIT1 und PDT1 werden daraus nur als verständliche Labels erkannt.

Der höchste Mehrwert entsteht aus der Kombination:

\[
\boxed{
\text{exakte Faktorzerlegung}
\rightarrow
\text{Knick-/Steigungstabelle}
\rightarrow
\text{asymptotische Summe}
\rightarrow
\text{numerische Kontrolle}
\rightarrow
\text{klausurtaugliches LaTeX}
}
\]

PT2, negative Verstärkung und RHP-Nullstellen sind die nächste Ausbaustufe. Totzeit, OCR und allgemeine nicht-rationale Systeme sind vor der Klausur wirtschaftlich schwach.

---

# 17. Offene Verifikation

--- NOTEBOOKLM-PROMPT ---

Prüfe folgende Widersprüche ausschließlich anhand der hochgeladenen offiziellen Regelungstechnik-Quellen:

1. Im `skript.pdf`, gedruckte Seite 53, wird behauptet, die Partialbruchzerlegung entspreche einer Reihenschaltung. Vergleiche dies mit der Blockrechnung und der Faktor-/Zeitkonstantenform. Ist für eine Bode-Reihenschaltung die Faktorzerlegung oder die Partialbruchzerlegung korrekt?

2. Prüfe im `skript.pdf`, gedruckte Seite 72, die angegebenen Steigungen und Phasen von I- und D-Glied sowie die Parameterzuordnung. Sind I und D dort vertauscht oder inkonsistent zu den Standardgliedkapiteln?

3. Prüfe in `RT-Klausur_WS_25_26-komplett.pdf`, Aufgabe 2, die Musterlösung zur Phasenreserve des PT1-Glieds. Ist der Wert 270° mit der üblichen Definition der Phasenreserve vereinbar? Wie lautet der korrekte Wert aus der angegebenen Übertragungsfunktion?

4. Prüfe in derselben Klausur die Reihenschaltung

\[
1000\frac{1+0.002s}{1+2s}.
\]

Geht die Gesamtphase für \(\omega\to\infty\) gegen 0° oder 90°?

5. Prüfe in `RT_Klausur_SS2025-komplett.pdf`, Aufgabe 2, den Widerspruch zwischen der grafisch angegebenen Verstärkungsreserve von 20 dB und der rekonstruierten exakten Übertragungsfunktion

\[
G(s)=\frac{100}{s(1+10s)}.
\]

Existiert für dieses exakte Modell eine endliche Phasendurchtrittsfrequenz bei \(-180°\)?

Antworte kurz und eindeutig. Belege jede wesentliche Aussage mit:
- kurzem direkten Zitat,
- Dokumentname,
- Seitenzahl oder genauer Fundstelle.

Zeige Widersprüche zwischen Quellen. Wenn keine eindeutige Antwort möglich ist, sage das ausdrücklich und erfinde nichts.

--- ENDE ---
