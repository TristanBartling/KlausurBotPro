# RT1 – Rechenwege-Master

## Bearbeitungsstand

- [x] Tutorium 01 – Modellbildung
- [x] Tutorium 02 – Zeitliches Verhalten linearer Systeme
- [x] Tutorium 03 – Regelungsnormalform und Übertragungsfunktionen
- [x] Tutorium 04 – Darstellungen im Frequenzbereich
- [x] Tutorium 05 – Grundlegende Übertragungselemente und Blockschaltbilder
- [x] Tutorium 06 – Frequenzganganalyse
- [x] Tutorium 07 – Einführung in den Regelkreis
- [x] Tutorium 09 – Stabilität I
- [x] Tutorium 11 – Stabilität II und Reglerentwurf I
- [x] Tutorium 12 – Reglerentwurf II und Wurzelortskurve
- [x] Alle in RT-Tutorien-Mitschrift.pdf enthaltenen Tutorien ausgewertet
- [x] Quellenübergreifender Übungs- und Klausurabgleich

## Kennzeichnung

- **[OFFIZIELL]**: direkt aus offizieller Aufgabenstellung oder Musterlösung.
- **[MITSCHRIFT]**: aus der handschriftlichen Tutoriumsmitschrift transkribiert.
- **[KORRIGIERT]**: Mitschrift enthielt einen Fehler oder eine unsaubere Notation; hier fachlich berichtigt.
- **[HERLEITUNG]**: sauber aus den Quellenangaben mathematisch hergeleitet.
- **[UNKLAR]**: Quelle ist nicht eindeutig; keine stillschweigende Festlegung.

---

# Tutorium 01 – Modellbildung

## 1. Quellen und Seitenbereich

### Primärquellen

1. **RT-Tutorien-Mitschrift.pdf**, PDF-Seiten 1–17  
   - S. 1–4: Theoriefragen und Aufgabe 1  
   - S. 5: leer  
   - S. 6–9: Aufgabe 2 – Linearisierung  
   - S. 10–11: Aufgabe 3 – DC-Motor  
   - S. 12–13: Aufgabe 4 – Bike  
   - S. 14–16: kurze Wiederholungsrechnungen zu Aufgabe 2b, Aufgabe 3 und Aufgabe 4  
   - S. 17: leer  
   - Tutorium 02 beginnt auf PDF-Seite 18.

2. **Regelungstechnik_Tutorium_komplett.pdf**, Tutorium 01, Blattseiten 1/5–5/5  
   Offizielle Aufgaben und Endergebnisse.

3. **skript.pdf**  
   - PDF-S. 26: Definition 1.11 „Zustand“ und Definition 1.12 „LTI-System“  
   - PDF-S. 27: Linearisierung nichtlinearer Systeme über Jacobi-Matrizen  
   - PDF-S. 30: Definition 1.19 „Steuerung“ und Definition 1.20 „Regelung“

---

# 2. Theoriefragen

## 2.1 Warum müssen Kräfte projiziert werden, bevor Newton angewendet wird?

### Saubere Antwort

Newton gilt als Vektorgleichung

\[
\sum \mathbf F = m\mathbf a.
\]

Für eine skalare Bewegungsgleichung in \(x\)- oder \(y\)-Richtung müssen alle Kräfte zuerst in **dasselbe Koordinatensystem** zerlegt werden:

\[
\sum F_x = m\ddot x,
\qquad
\sum F_y = m\ddot y.
\]

Eine schräg angreifende Kraft darf nicht direkt als vollständiger Betrag in beide Gleichungen eingesetzt werden. Es dürfen jeweils nur ihre Komponenten verwendet werden.

### Wiedererkennung

- Kräfte sind schräg zur globalen \(x\)- oder \(y\)-Achse eingezeichnet.
- Das System besitzt einen Winkel \(\psi\), \(\delta\), \(\varphi\) usw.
- Kräfte sind im körperfesten System gegeben, die Bewegung aber im Inertialsystem gesucht.

### Typischer Fehler

Sinus und Kosinus werden mechanisch vertauscht. Entscheidend ist nicht eine Merkhilfe, sondern:

- Welche Komponente liegt **an** dem betrachteten Winkel? → Kosinus.
- Welche Komponente liegt **gegenüber**? → Sinus.
- Danach Vorzeichen aus der tatsächlichen Pfeilrichtung bestimmen.

---

## 2.2 Unterschied zwischen Steuerung und Regelung

### [OFFIZIELL]

- **Steuerung:** Eingang \(u\) ist eine Funktion der Zeit, also \(u:T\to U\). Es gibt keine Rückführung des aktuellen Systemzustands oder Ausgangs.
- **Regelung:** Eingang \(u\) wird aus dem aktuellen Zustand bzw. der Regelabweichung gebildet. Das System besitzt eine Rückführung.

### Klausurtaugliche Kurzfassung

- **Steuerung:** keine Rückführung; Störungen werden nicht automatisch korrigiert.
- **Regelung:** Rückführung; Soll- und Istwert werden verglichen und Abweichungen beeinflussen die Stellgröße.

Quelle: `skript.pdf`, PDF-S. 30, Definitionen 1.19 und 1.20.

---

## 2.3 Was beschreibt der Zustand eines Systems? Warum braucht man Zustandsvariablen?

### [OFFIZIELL + HERLEITUNG]

Der Zustand \(x(t_0)\) enthält genau die interne Information, die zusammen mit dem Eingang ab \(t_0\) benötigt wird, um den zukünftigen Ausgang eindeutig zu bestimmen.

Zustandsvariablen werden benötigt, um

1. Anfangsbedingungen und gespeicherte Energie zu erfassen,
2. Differentialgleichungen höherer Ordnung in ein System erster Ordnung umzuschreiben,
3. das System in der Form

\[
\dot x(t)=Ax(t)+Bu(t),
\qquad
y(t)=Cx(t)+Du(t)
\]

darzustellen.

Beispiel für eine DGL zweiter Ordnung:

\[
\ddot q=f(q,\dot q,u).
\]

Wahl der Zustände:

\[
x_1=q,\qquad x_2=\dot q.
\]

Dann:

\[
\dot x_1=x_2,
\qquad
\dot x_2=f(x_1,x_2,u).
\]

Quelle: `skript.pdf`, PDF-S. 26, Definitionen 1.11 und 1.12.

---

## 2.4 Idee der Linearisierung und sinnvoller Einsatz

### Saubere Antwort

Eine nichtlineare Funktion wird in der Nähe eines Arbeitspunkts durch ihre Tangente bzw. ihre Taylorentwicklung erster Ordnung ersetzt:

\[
h(x)\approx h(x_0)+h'(x_0)(x-x_0).
\]

Für mehrere Variablen:

\[
f(x,u)\approx f(x_0,u_0)
+\frac{\partial f}{\partial x}\bigg|_{(x_0,u_0)}(x-x_0)
+\frac{\partial f}{\partial u}\bigg|_{(x_0,u_0)}(u-u_0).
\]

Die Näherung ist nur in einer Umgebung des Arbeitspunkts zuverlässig. Weit davon entfernt kann sie schlecht oder unbrauchbar sein.

### Sinnvoll bei

- kleinen Abweichungen um einen stationären Betriebspunkt,
- nichtlinearen Termen wie \(x^2\), \(e^x\), \(\sqrt{x}\), \(\sin x\), \(x/u\),
- anschließender Analyse mit linearen Methoden.

Quelle: `skript.pdf`, PDF-S. 27, Bemerkung 1.14; Tutoriumsmitschrift, PDF-S. 3.

---

## 2.5 Warum benutzt man Hilfsfunktionen?

Hilfsfunktionen isolieren genau den nichtlinearen Teil:

\[
h(z)=\text{nichtlinearer Term}.
\]

Dann wird nur dieser Term linearisiert:

\[
h(z)\approx h(z_0)+h'(z_0)(z-z_0).
\]

Das reduziert Ableitungsfehler, hält lineare Terme unverändert und macht bei mehreren nichtlinearen Termen die Rechnung kontrollierbar.

---

# 3. Allgemeines Schema: Modellbildung aus Kräften und Momenten

## Schritt 1: Koordinatensystem und positive Richtungen festlegen

Beispiel:

- globale \(x\)-Achse nach rechts,
- globale \(y\)-Achse nach oben,
- positiver Drehwinkel gegen den Uhrzeigersinn.

Ohne klare Konvention sind Vorzeichen nicht kontrollierbar.

## Schritt 2: Jede Kraft in globale Komponenten zerlegen

Für eine Kraft \(F\), deren Richtung den Winkel \(\alpha\) zur positiven \(x\)-Achse besitzt:

\[
F_x=F\cos\alpha,
\qquad
F_y=F\sin\alpha.
\]

Ist die Kraft um \(90^\circ\) gedreht:

\[
F_x=-F\sin\alpha,
\qquad
F_y=F\cos\alpha.
\]

## Schritt 3: Translation

\[
\sum F_x=m\ddot x,
\qquad
\sum F_y=m\ddot y.
\]

## Schritt 4: Rotation

\[
\sum M_S=I\ddot\psi.
\]

Vorzeichen des Moments über die gewünschte positive Drehrichtung bestimmen.

## Schritt 5: Einheitenkontrolle

- Kraftgleichung: jede Seite in \(\mathrm N\).
- Momentengleichung: jede Seite in \(\mathrm{N\,m}\).
- Ein Term ohne passende Einheit ist sicher falsch.

---

# 4. Aufgabe 1 – Einspurmodell des Fahrzeugs

## 4.1 Aufgabenart erkennen

Gesucht sind Bewegungsgleichungen für

\[
x(t),\qquad y(t),\qquad \psi(t).
\]

Damit sind drei Gleichungen erforderlich:

\[
\sum F_x=m\ddot x,
\qquad
\sum F_y=m\ddot y,
\qquad
\sum M_S=I\ddot\psi.
\]

---

## 4.2 Kraftprojektionen

### Hinterrad

Umfangskraft:

\[
\mathbf F_{uh}
=
F_{uh}
\begin{bmatrix}
\cos\psi\\
\sin\psi
\end{bmatrix}.
\]

Seitenkraft:

\[
\mathbf F_{sh}
=
F_{sh}
\begin{bmatrix}
-\sin\psi\\
\cos\psi
\end{bmatrix}.
\]

### Vorderrad

Das Vorderrad ist zusätzlich um \(\delta\) eingeschlagen.

Umfangskraft:

\[
\mathbf F_{uv}
=
F_{uv}
\begin{bmatrix}
\cos(\psi+\delta)\\
\sin(\psi+\delta)
\end{bmatrix}.
\]

Seitenkraft:

\[
\mathbf F_{sv}
=
F_{sv}
\begin{bmatrix}
-\sin(\psi+\delta)\\
\cos(\psi+\delta)
\end{bmatrix}.
\]

---

## 4.3 Bewegungsgleichung in \(x\)-Richtung

\[
m\ddot x
=
F_{uh}\cos\psi
-F_{sh}\sin\psi
+F_{uv}\cos(\psi+\delta)
-F_{sv}\sin(\psi+\delta).
\]

Mit den Additionstheoremen:

\[
\cos(\psi+\delta)
=
\cos\psi\cos\delta-\sin\psi\sin\delta,
\]

\[
\sin(\psi+\delta)
=
\sin\psi\cos\delta+\cos\psi\sin\delta.
\]

Einsetzen und nach \(\cos\psi\) und \(\sin\psi\) sortieren:

\[
\boxed{
m\ddot x
=
\left(F_{uh}+F_{uv}\cos\delta-F_{sv}\sin\delta\right)\cos\psi
-
\left(F_{sh}+F_{uv}\sin\delta+F_{sv}\cos\delta\right)\sin\psi
}
\]

---

## 4.4 Bewegungsgleichung in \(y\)-Richtung

\[
m\ddot y
=
F_{uh}\sin\psi
+F_{sh}\cos\psi
+F_{uv}\sin(\psi+\delta)
+F_{sv}\cos(\psi+\delta).
\]

Nach Anwendung der Additionstheoreme:

\[
\boxed{
m\ddot y
=
\left(F_{uh}+F_{uv}\cos\delta-F_{sv}\sin\delta\right)\sin\psi
+
\left(F_{sh}+F_{uv}\sin\delta+F_{sv}\cos\delta\right)\cos\psi
}
\]

---

## 4.5 Momentengleichung um den Schwerpunkt

Die Hinterrad-Seitenkraft erzeugt mit Hebelarm \(l_h\) ein negatives Moment:

\[
M_{sh}=-l_hF_{sh}.
\]

Am Vorderrad tragen die zur Fahrzeuglängsachse senkrechten Anteile zum Moment bei:

\[
M_{sv}=l_vF_{sv}\cos\delta,
\]

\[
M_{uv}=l_vF_{uv}\sin\delta.
\]

Somit:

\[
\boxed{
I\ddot\psi
=
-l_hF_{sh}
+l_vF_{sv}\cos\delta
+l_vF_{uv}\sin\delta
}
\]

---

## 4.6 Bewertung der Mitschrift

### [MITSCHRIFT, PDF-S. 4]

Die Mitschrift zeigt das richtige Vorgehen:

1. Kräfte in Komponenten zerlegen.
2. \(\sum F_x=m\ddot x\).
3. \(\sum F_y=m\ddot y\).
4. \(\sum M_S=I\ddot\psi\).

### [KORRIGIERT]

In der handschriftlichen Zwischenrechnung auf PDF-S. 4 stehen einzelne falsche oder vertauschte Symbole:

- Bei der hinteren Seitenkraft erscheint in einer Zeile ein Kosinus statt des korrekten Sinus in der \(x\)-Komponente.
- Front- und Hinterradindizes werden teilweise verwechselt.
- Die Momentengleichung ist handschriftlich unvollständig abgebrochen.

Diese Zeilen dürfen nicht als Endlösung übernommen werden. Die oben stehenden Gleichungen entsprechen der offiziellen Musterlösung.

Quelle: `Regelungstechnik_Tutorium_komplett.pdf`, Tutorium 01, Blattseite 2/5.

---

# 5. Allgemeines Schema: Linearisierung

## 5.1 Eine Variable

Für einen nichtlinearen Term \(h(z)\):

\[
h(z)
\approx
h(z_0)+h'(z_0)(z-z_0).
\]

Prüfschema:

1. Nichtlinearen Term markieren.
2. Hilfsfunktion \(h\) definieren.
3. \(h(z_0)\) bestimmen.
4. \(h'(z)\) berechnen.
5. \(h'(z_0)\) einsetzen.
6. Ausmultiplizieren.
7. Lineare und konstante Terme sammeln.

## 5.2 Mehrere Variablen

\[
f(x,u)
\approx
f(x_0,u_0)
+
f_x(x_0,u_0)(x-x_0)
+
f_u(x_0,u_0)(u-u_0).
\]

Bei mehreren Zuständen wird entsprechend der Gradient bzw. die Jacobi-Matrix verwendet.

## 5.3 Plausibilitätsprüfung

- Nach der Linearisierung dürfen keine Produkte variabler Größen übrig bleiben.
- Terme wie \(x^2\), \(xu\), \(1/u\), \(e^x\), \(\sqrt{x}\), \(\sin x\) dürfen nicht unverändert variabel bleiben.
- Setzt man den Arbeitspunkt ein, muss die linearisierte Funktion denselben Funktionswert wie die ursprüngliche Funktion besitzen.

---

# 6. Aufgabe 2a – Linearisierung von \(\dot x^2\)

## Gegeben

\[
K_1\dot x(t)^2-K_2(x(t)-K_3)=u(t),
\qquad
\dot x_0=3.
\]

## Schritt 1: Nichtlinearen Term isolieren

\[
h(\dot x)=K_1\dot x^2.
\]

## Schritt 2: Taylorentwicklung

\[
h(\dot x)
\approx
h(\dot x_0)
+
h'(\dot x_0)(\dot x-\dot x_0).
\]

Mit

\[
h(\dot x_0)=K_1\dot x_0^2,
\qquad
h'(\dot x)=2K_1\dot x,
\]

folgt

\[
h(\dot x)
\approx
K_1\dot x_0^2
+
2K_1\dot x_0(\dot x-\dot x_0).
\]

Ausmultiplizieren:

\[
h(\dot x)
\approx
2K_1\dot x_0\dot x-K_1\dot x_0^2.
\]

Mit \(\dot x_0=3\):

\[
h(\dot x)\approx 6K_1\dot x-9K_1.
\]

## Schritt 3: In die DGL einsetzen

\[
u(t)
=
6K_1\dot x(t)-9K_1-K_2x(t)+K_2K_3.
\]

Ergebnis:

\[
\boxed{
u(t)
=
6K_1\dot x(t)
-K_2x(t)
+K_2K_3
-9K_1
}
\]

### Bewertung der Mitschrift

Die Rechnung auf PDF-S. 7 ist fachlich korrekt. Die Zwischenschritte sind vollständig nachvollziehbar.

---

# 7. Aufgabe 2b – Linearisierung von \(e^{\dot x}\) und \(\sqrt x\)

## Gegeben

\[
\frac{\ddot x(t)}{3}
-
2e^{\dot x(t)}
+
\sqrt{x(t)}
=
u(t),
\]

\[
x_0=1,
\qquad
\dot x_0=0.
\]

Der Term \(\ddot x/3\) ist bereits linear. Es werden nur die beiden nichtlinearen Terme ersetzt.

---

## 7.1 Exponentialterm

\[
h_1(\dot x)=e^{\dot x}.
\]

Taylorentwicklung um \(\dot x_0=0\):

\[
e^{\dot x}
\approx
e^0+e^0(\dot x-0)
=
1+\dot x.
\]

---

## 7.2 Wurzelterm

\[
h_2(x)=\sqrt x.
\]

Ableitung:

\[
h_2'(x)=\frac{1}{2\sqrt x}.
\]

Taylorentwicklung um \(x_0=1\):

\[
\sqrt x
\approx
\sqrt1+\frac{1}{2\sqrt1}(x-1).
\]

\[
\sqrt x
\approx
1+\frac12(x-1)
=
\frac12x+\frac12.
\]

---

## 7.3 Einsetzen

\[
u(t)
=
\frac{\ddot x(t)}{3}
-
2(1+\dot x(t))
+
\frac12x(t)+\frac12.
\]

Ausmultiplizieren:

\[
u(t)
=
\frac{\ddot x(t)}{3}
-
2\dot x(t)
+
\frac12x(t)
-
\frac32.
\]

Ergebnis:

\[
\boxed{
u(t)
=
\frac13\ddot x(t)
-
2\dot x(t)
+
\frac12x(t)
-
\frac32
}
\]

### Bewertung der Mitschrift

- PDF-S. 7–8: vollständige und richtige Herleitung.
- PDF-S. 14: kurze Kontrollrechnung mit demselben Ergebnis.
- Keine fachliche Korrektur nötig.

---

# 8. Aufgabe 2c – \(\sin x=3u^2\)

## Gegeben

\[
\sin(x(t))=3u(t)^2,
\qquad
x_0=\frac{\pi}{2}.
\]

## Schritt 1: Sinusterm linearisieren

\[
h(x)=\sin x,
\qquad
h'(x)=\cos x.
\]

\[
\sin x
\approx
\sin x_0+\cos x_0(x-x_0).
\]

Mit \(x_0=\pi/2\):

\[
\sin x
\approx
1+0\cdot\left(x-\frac{\pi}{2}\right)
=
1.
\]

## Schritt 2: Gleichung lösen

\[
1=3u^2.
\]

\[
u^2=\frac13.
\]

Mathematisch:

\[
u=\pm\frac{1}{\sqrt3}.
\]

Die offizielle Lösung wählt den positiven Ast:

\[
\boxed{
u(t)=\sqrt{\frac13}
}
\]

## Kritische Bewertung

### [UNKLAR]

Die Aufgabenstellung gibt keinen Arbeitspunkt \(u_0\) und keine Bedingung \(u\ge0\) an. Daher sind rein algebraisch beide Vorzeichen möglich.

Außerdem bleibt \(u^2\) nichtlinear. Die Musterlösung ist deshalb keine vollständige Linearisierung der gesamten impliziten Gleichung in \((x,u)\), sondern:

1. Linearisierung von \(\sin x\) am angegebenen \(x_0\),
2. anschließende algebraische Bestimmung eines konstanten Eingangswerts.

Für die Klausur ist die offizielle positive Lösung zu verwenden, sofern keine zusätzliche Information gegeben wird.

### NotebookLM-Prüffrage

--- NOTEBOOKLM-PROMPT ---

Prüfe ausschließlich anhand der hochgeladenen offiziellen Regelungstechnik-Unterlagen die Aufgabe 2c aus „Tutorium 01 – Modellbildung“:

\[
\sin(x(t))=3u(t)^2,\qquad x_0=\pi/2.
\]

1. Warum wird offiziell nur \(u=\sqrt{1/3}\) angegeben, obwohl algebraisch auch \(u=-\sqrt{1/3}\) möglich ist?
2. Ist hier tatsächlich die gesamte Gleichung linearisiert oder nur der Term \(\sin x\)?
3. Gibt es in den Quellen eine Annahme \(u\ge0\) oder einen fehlenden Arbeitspunkt \(u_0\)?

Belege jede Aussage mit Dokumentname und genauer Seite/Fundstelle. Wenn die Quellen keine eindeutige Begründung enthalten, sage das ausdrücklich.

--- ENDE ---

---

# 9. Aufgabe 2d – Mehrvariablen-Linearisierung

## Gegeben

\[
\ddot x(t)
=
\frac{x(t)}{u(t)}
-
3\sqrt{\sin(x(t))-\cos(x(t))},
\]

\[
x_0=\pi,
\qquad
u_0=2.
\]

Definiere

\[
f(x,u)
=
\frac{x}{u}
-
3\sqrt{\sin x-\cos x}.
\]

Gesucht ist die lineare Näherung

\[
\ddot x\approx
f(x_0,u_0)
+
f_x(x_0,u_0)(x-x_0)
+
f_u(x_0,u_0)(u-u_0).
\]

---

## 9.1 Funktionswert am Arbeitspunkt

\[
f(\pi,2)
=
\frac{\pi}{2}
-
3\sqrt{\sin\pi-\cos\pi}.
\]

Mit \(\sin\pi=0\), \(\cos\pi=-1\):

\[
f(\pi,2)
=
\frac{\pi}{2}-3.
\]

---

## 9.2 Partielle Ableitung nach \(x\)

\[
f_x(x,u)
=
\frac1u
-
3\cdot
\frac{1}{2\sqrt{\sin x-\cos x}}
(\cos x+\sin x).
\]

Am Arbeitspunkt:

\[
f_x(\pi,2)
=
\frac12
-
\frac{3}{2\sqrt{1}}(-1+0).
\]

\[
f_x(\pi,2)
=
\frac12+\frac32
=
2.
\]

---

## 9.3 Partielle Ableitung nach \(u\)

\[
f_u(x,u)
=
-\frac{x}{u^2}.
\]

Am Arbeitspunkt:

\[
f_u(\pi,2)
=
-\frac{\pi}{4}.
\]

---

## 9.4 Tayloransatz

\[
\ddot x
\approx
\left(\frac{\pi}{2}-3\right)
+
2(x-\pi)
-
\frac{\pi}{4}(u-2).
\]

Ausmultiplizieren:

\[
\ddot x
=
\frac{\pi}{2}-3+2x-2\pi-\frac{\pi}{4}u+\frac{\pi}{2}.
\]

Konstanten sammeln:

\[
\frac{\pi}{2}-2\pi+\frac{\pi}{2}
=
-\pi.
\]

Ergebnis:

\[
\boxed{
\ddot x(t)
=
2x(t)
-
\frac{\pi}{4}u(t)
-
\pi
-
3
}
\]

gleichwertig:

\[
\boxed{
\ddot x(t)
=
-\pi-3-\frac{\pi}{4}u(t)+2x(t)
}
\]

### Bewertung der Mitschrift

Die Herleitung auf PDF-S. 8–9 ist korrekt. Besonders wichtig:

- \(\frac{\mathrm d}{\mathrm dx}[-\cos x]=+\sin x\),
- \(\frac{\mathrm d}{\mathrm du}(x/u)=-x/u^2\),
- die Verschiebungsterme \((x-\pi)\) und \((u-2)\) müssen vollständig ausmultipliziert werden.

---

# 10. Allgemeines Schema: DGL in Zustandsraumform

## Ziel

\[
\dot x=Ax+Bu,
\qquad
y=Cx+Du.
\]

## Vorgehen

1. DGL nach der höchsten Ableitung auflösen.
2. Zustände wählen.
3. Zustandsableitungen hinschreiben.
4. Alle rechten Seiten nur durch Zustände und Eingänge ausdrücken.
5. Koeffizienten zeilenweise in \(A\) und \(B\) eintragen.
6. Ausgangsgleichung in \(C\) und \(D\) ablesen.
7. Dimensionen kontrollieren.

## Standardwahl für eine DGL \(n\)-ter Ordnung

\[
x_1=q,\quad
x_2=\dot q,\quad
\dots,\quad
x_n=q^{(n-1)}.
\]

Dann:

\[
\dot x_1=x_2,\quad
\dot x_2=x_3,\quad
\dots,\quad
\dot x_n=q^{(n)}.
\]

## Dimensionskontrolle

Für \(n\) Zustände, \(m\) Eingänge und \(p\) Ausgänge:

\[
A\in\mathbb R^{n\times n},
\quad
B\in\mathbb R^{n\times m},
\quad
C\in\mathbb R^{p\times n},
\quad
D\in\mathbb R^{p\times m}.
\]

---

# 11. Aufgabe 3 – Gleichstrommotor

## 11.1 Gegebene Gleichungen

\[
Ri(t)+L\dot i(t)+k_M\omega(t)=u(t),
\]

\[
k_Ti(t)=J\dot\omega(t)+k_R\omega(t).
\]

## 11.2 Zustände, Eingang und Ausgang

Sinnvolle Zustände sind die Größen mit eigener Dynamik bzw. Energiespeicherung:

\[
x_1=i(t),
\qquad
x_2=\omega(t).
\]

Also:

\[
x=
\begin{bmatrix}
i\\
\omega
\end{bmatrix}.
\]

Eingang:

\[
u=u(t).
\]

Ausgang laut Aufgabe:

\[
y=\omega=x_2.
\]

---

## 11.3 Erste Gleichung nach \(\dot i\) auflösen

\[
Ri+L\dot i+k_M\omega=u.
\]

\[
L\dot i=u-Ri-k_M\omega.
\]

\[
\boxed{
\dot i
=
-\frac RL i
-\frac{k_M}{L}\omega
+\frac1L u
}
\]

---

## 11.4 Zweite Gleichung nach \(\dot\omega\) auflösen

\[
k_Ti=J\dot\omega+k_R\omega.
\]

\[
J\dot\omega=k_Ti-k_R\omega.
\]

\[
\boxed{
\dot\omega
=
\frac{k_T}{J}i
-
\frac{k_R}{J}\omega
}
\]

---

## 11.5 Matrixform

\[
\boxed{
\dot x
=
\begin{bmatrix}
-\frac RL & -\frac{k_M}{L}\\
\frac{k_T}{J} & -\frac{k_R}{J}
\end{bmatrix}
x
+
\begin{bmatrix}
\frac1L\\
0
\end{bmatrix}
u
}
\]

Ausgang:

\[
\boxed{
y=
\begin{bmatrix}
0&1
\end{bmatrix}x
}
\]

und damit

\[
D=0.
\]

### Dimensionsprüfung

- \(A:2\times2\)
- \(B:2\times1\)
- \(C:1\times2\)
- \(D:1\times1\)

### Bewertung der Mitschrift

- PDF-S. 11: vollständige Rechnung und korrekte Matrixform.
- PDF-S. 15: verkürzte Wiederholungsrechnung; ebenfalls korrekt.
- Schreibweise \(k_T\), \(k_M\), \(k_R\) muss sauber getrennt werden.

Quelle: `Regelungstechnik_Tutorium_komplett.pdf`, Tutorium 01, Blattseite 4/5.

---

# 12. Aufgabe 4 – Fahrradmodell

## 12.1 Gegebene DGL

\[
C_1\ddot\Phi
-
C_2\Phi
-
C_3(-\dot\Phi-C_4\Phi+C_5T)
=
0.
\]

## 12.2 Klammer korrekt auflösen

\[
-C_3(-\dot\Phi-C_4\Phi+C_5T)
=
+C_3\dot\Phi
+C_3C_4\Phi
-C_3C_5T.
\]

Damit:

\[
C_1\ddot\Phi
-
C_2\Phi
+
C_3\dot\Phi
+
C_3C_4\Phi
-
C_3C_5T
=
0.
\]

Nach \(\ddot\Phi\) auflösen:

\[
C_1\ddot\Phi
=
C_2\Phi
-
C_3\dot\Phi
-
C_3C_4\Phi
+
C_3C_5T.
\]

\[
\boxed{
\ddot\Phi
=
\frac{C_2-C_3C_4}{C_1}\Phi
-
\frac{C_3}{C_1}\dot\Phi
+
\frac{C_3C_5}{C_1}T
}
\]

---

## 12.3 Zustände, Eingang und Ausgang

\[
x_1=\Phi,
\qquad
x_2=\dot\Phi.
\]

\[
u=T,
\qquad
y=\Phi=x_1.
\]

Die Zustandsableitungen:

\[
\dot x_1=x_2,
\]

\[
\dot x_2
=
\frac{C_2-C_3C_4}{C_1}x_1
-
\frac{C_3}{C_1}x_2
+
\frac{C_3C_5}{C_1}u.
\]

---

## 12.4 Matrixform

\[
\boxed{
\dot x
=
\begin{bmatrix}
0&1\\
\frac{C_2-C_3C_4}{C_1}&-\frac{C_3}{C_1}
\end{bmatrix}
x
+
\begin{bmatrix}
0\\
\frac{C_3C_5}{C_1}
\end{bmatrix}
u
}
\]

\[
\boxed{
y=
\begin{bmatrix}
1&0
\end{bmatrix}x
}
\]

und

\[
D=0.
\]

### Bewertung der Mitschrift

- PDF-S. 13: vollständige und korrekte Herleitung.
- PDF-S. 16: Beginn einer Kurzfassung, aber unvollständig.
- Kritischer Schritt ist die äußere Minusklammer vor \(C_3\). Ein Vorzeichenfehler dort zerstört die gesamte \(A\)- und \(B\)-Matrix.

Quelle: `Regelungstechnik_Tutorium_komplett.pdf`, Tutorium 01, Blattseite 5/5.

---

# 13. Klausurstrategie für diese Aufgabentypen

## 13.1 Modellbildung

1. Koordinaten und positive Drehrichtung einzeichnen.
2. Jede Kraft mit eigener Komponentenzerlegung notieren.
3. Erst danach Summengleichungen aufstellen.
4. Momentengleichung separat behandeln.
5. Vorzeichen und Einheiten kontrollieren.

## 13.2 Linearisierung

1. Alle nichtlinearen Terme farbig oder durch Unterstreichen markieren.
2. Pro Term eine Hilfsfunktion.
3. Arbeitspunkt direkt neben die Hilfsfunktion schreiben.
4. Ableitung erst allgemein, dann am Arbeitspunkt auswerten.
5. Taylorform vor dem Ausmultiplizieren vollständig hinschreiben.
6. Am Ende prüfen, ob wirklich nur lineare variable Terme übrig sind.

## 13.3 Zustandsraum

1. Höchste Ableitung isolieren.
2. Zustände festlegen.
3. \(\dot x_1,\dot x_2,\dots\) einzeln hinschreiben.
4. Erst danach Matrix bilden.
5. Ausgang nicht vergessen.
6. \(D=0\) explizit angeben, wenn keine direkte Eingang-Ausgang-Kopplung besteht.

---

# 14. Typische Fehler aus Tutorium 01

1. Kraftkomponenten ohne einheitliches Koordinatensystem addieren.
2. Sinus und Kosinus nur nach Gefühl wählen.
3. Vorzeichen der Seitenkräfte ignorieren.
4. Bei Taylor \(h(x_0)\) oder den Verschiebungsterm \((x-x_0)\) vergessen.
5. Bereits lineare Terme unnötig verändern.
6. Bei mehreren Variablen nur nach einer Variablen ableiten.
7. Minusklammern in DGLs falsch auflösen.
8. Zustände wählen, aber die DGL nicht nach deren Ableitungen auflösen.
9. \(C\)- und \(D\)-Matrix vergessen.
10. Eine handschriftliche Zwischenzeile ungeprüft als Endergebnis übernehmen.

---

# 15. Ergebnis der Qualitätsprüfung

## Sicher lesbar und fachlich bestätigt

- Theorie-Grundschemata auf PDF-S. 3.
- Linearisierungen 2a, 2b und 2d.
- DC-Motor.
- Fahrradmodell.

## Lesbar, aber mit fachlicher Einschränkung

- Aufgabe 2c: positive Wurzel in offizieller Lösung nicht vollständig begründet.
- Aufgabe 1: handschriftliche Zwischenrechnung enthält Symbol- und Projektionsfehler; offizielle Lösung ist eindeutig.

## Nicht inhaltstragend

- PDF-S. 5 und 17 sind leer.
- PDF-S. 14–16 enthalten nur verkürzte Wiederholungen bereits vollständig vorhandener Rechnungen.

---

# 16. Kompaktformelsammlung Tutorium 01

## Newton und Drallsatz

\[
\sum F_x=m\ddot x,
\qquad
\sum F_y=m\ddot y,
\qquad
\sum M_S=I\ddot\psi.
\]

## Taylor, eine Variable

\[
h(x)\approx h(x_0)+h'(x_0)(x-x_0).
\]

## Taylor, zwei Variablen

\[
f(x,u)\approx f_0+f_{x,0}(x-x_0)+f_{u,0}(u-u_0).
\]

## Zustandsraum

\[
\dot x=Ax+Bu,
\qquad
y=Cx+Du.
\]

## Zweite Ordnung

\[
x_1=q,\qquad x_2=\dot q,
\]

\[
\dot x_1=x_2,\qquad \dot x_2=\ddot q.
\]

---

# Tutorium 02 – Zeitliches Verhalten linearer Systeme

## 1. Quellen und Seitenbereich

### Primärquellen

1. **RT-Tutorien-Mitschrift.pdf**, PDF-Seiten 18–27
   - S. 18–20: offizielle Aufgaben und Endergebnisse
   - S. 21: Theorie, Transitionsmatrix, Diagonal- und Jordanform
   - S. 22–23: Zustandstransformation von System a) und Beginn von d)
   - S. 24: Abschluss von d) und komplexe Transformation von g)
   - S. 25–26: Transitionsmatrix und vollständige Systemlösung für a)
   - S. 27: leer
   - Tutorium 03 beginnt auf PDF-Seite 28.

2. **Regelungstechnik_Tutorium_komplett.pdf**, Tutorium 02, Blattseiten 1/3–3/3  
   Offizielle Aufgaben und Endergebnisse.

3. **skript.pdf**
   - PDF-S. 37: Definition 2.4 „Transitionsmatrix“
   - PDF-S. 38: Theorem 2.7 „Lösung autonomer LTI-Systeme“
   - PDF-S. 40–41: Theorem 2.10 „Lösung von LTI-Systemen“
   - PDF-S. 43–44: Koordinatentransformation und kanonische Normalform
   - PDF-S. 44–45: komplexe kanonische Normalform
   - PDF-S. 45: Theorem 2.16 „Jordansche Normalform“

---

# 2. Zentrale Grundformeln

## 2.1 Homogenes und inhomogenes System

Homogen:

\[
\dot x(t)=Ax(t).
\]

Inhomogen:

\[
\dot x(t)=Ax(t)+Bu(t).
\]

Die Mitschrift trennt diese beiden Fälle auf PDF-S. 21 ausdrücklich.

---

## 2.2 Matrixexponential und Transitionsmatrix

Die Matrixexponentialfunktion ist definiert durch

\[
e^{At}
=
\sum_{k=0}^{\infty}\frac{(At)^k}{k!}.
\]

Die Transitionsmatrix lautet

\[
\boxed{\Phi(t)=e^{At}}.
\]

Für das homogene System gilt

\[
\boxed{x(t)=\Phi(t)x_0=e^{At}x_0}.
\]

### Bedeutung

\(\Phi(t)\) beschreibt, wie sich ein Anfangszustand \(x_0\) unter der freien Systemdynamik bis zum Zeitpunkt \(t\) entwickelt.

Quelle: `skript.pdf`, PDF-S. 37–38, Definition 2.4 und Theorem 2.7.

---

## 2.3 Lösung des inhomogenen LTI-Systems

Für

\[
\dot x(t)=Ax(t)+Bu(t),
\qquad
x(0)=x_0
\]

gilt

\[
\boxed{
x(t)
=
\Phi(t)x_0
+
\int_0^t
\Phi(t-\tau)Bu(\tau)\,\mathrm d\tau
}.
\]

Dabei ist

\[
\underbrace{\Phi(t)x_0}_{\text{freier/homogener Anteil}}
\]

der Anteil aus der Anfangsbedingung und

\[
\underbrace{
\int_0^t\Phi(t-\tau)Bu(\tau)\,\mathrm d\tau
}_{\text{erzwungener/inhomogener Anteil}}
\]

der durch den Eingang verursachte Anteil.

Quelle: `skript.pdf`, PDF-S. 40, Theorem 2.10.

---

## 2.4 Zustandstransformation

Es werde eine neue Koordinate \(z\) durch

\[
x=Vz
\]

eingeführt. Da \(V\) konstant ist,

\[
\dot x=V\dot z.
\]

Aus

\[
\dot x=Ax
\]

folgt

\[
V\dot z=AVz.
\]

Multiplikation mit \(V^{-1}\):

\[
\dot z=V^{-1}AVz.
\]

Damit

\[
\boxed{\tilde A=V^{-1}AV}.
\]

Umgekehrt gilt

\[
A=V\tilde A V^{-1}.
\]

Für die Transitionsmatrix:

\[
\boxed{
\Phi(t)
=
Ve^{\tilde A t}V^{-1}
}.
\]

---

# 3. Theoriefragen

## 3.1 Was ist die Transitionsmatrix und wofür benutzt man sie?

Die Transitionsmatrix ist

\[
\Phi(t)=e^{At}.
\]

Sie wird benutzt, um

1. die freie Zustandsentwicklung zu berechnen,
2. die vollständige Lösung eines Systems mit Eingang zu bilden,
3. zeitliches Verhalten und Stabilität aus den Eigenwerten bzw. Normalformen abzulesen.

---

## 3.2 Was bedeutet \(e^{At}\)?

\(e^{At}\) ist keine komponentenweise Exponentialfunktion. Es ist die Matrixreihe

\[
e^{At}
=
I+At+\frac{A^2t^2}{2!}+\frac{A^3t^3}{3!}+\cdots.
\]

Sie erfüllt

\[
\frac{\mathrm d}{\mathrm dt}e^{At}=Ae^{At}
\]

und

\[
e^{A\cdot0}=I.
\]

### Extrem wichtige Kontrollbedingung

Jede korrekt berechnete Transitionsmatrix muss erfüllen:

\[
\boxed{\Phi(0)=I}.
\]

Zusätzlich:

\[
\boxed{\dot\Phi(0)=A}.
\]

Diese Tests decken mehrere Fehler der offiziellen Lösungsseite unmittelbar auf.

---

## 3.3 Wann ist ein System diagonalisierbar?

Eine \(n\times n\)-Matrix ist diagonalisierbar, wenn sie \(n\) linear unabhängige Eigenvektoren besitzt.

Für jeden Eigenwert \(\lambda\) muss gelten:

\[
\boxed{
\text{geometrische Vielfachheit}
=
\text{algebraische Vielfachheit}
}
\]

bzw. insgesamt müssen genügend unabhängige Eigenvektoren vorliegen.

Die geometrische Vielfachheit ist

\[
\rho(\lambda)
=
\dim\ker(A-\lambda I)
=
n-\operatorname{rang}(A-\lambda I).
\]

### Sofortregel

Sind alle Eigenwerte verschieden, ist die Matrix sicher diagonalisierbar.

---

## 3.4 Unterschied zwischen Diagonalform und Jordanform

### Diagonalform

\[
\tilde A
=
\operatorname{diag}(\lambda_1,\ldots,\lambda_n).
\]

Alle Zustände sind entkoppelt:

\[
\dot z_i=\lambda_i z_i.
\]

Daraus folgt direkt

\[
e^{\tilde At}
=
\operatorname{diag}
(e^{\lambda_1t},\ldots,e^{\lambda_nt}).
\]

### Jordanform

Ist eine Matrix nicht diagonalisierbar, werden Eigenvektoren und Hauptvektoren zu Jordanketten kombiniert:

\[
J=
\begin{bmatrix}
\lambda&1&0\\
0&\lambda&1\\
0&0&\lambda
\end{bmatrix}.
\]

Die Zustände sind innerhalb eines Jordanblocks gekoppelt. Dadurch entstehen zusätzliche Faktoren \(t,t^2,\ldots\).

---

## 3.5 Bedeutung komplexer Eigenwerte im Zeitverlauf

Für

\[
\lambda_{1,2}=\alpha\pm j\beta
\]

entstehen reelle Lösungen der Form

\[
e^{\alpha t}
\left(
c_1\cos(\beta t)
+
c_2\sin(\beta t)
\right).
\]

Interpretation:

- \(\alpha\): Wachstum bzw. Abklingen der Hüllkurve,
- \(|\beta|\): Kreisfrequenz der Schwingung.

Damit:

- \(\alpha<0\): abklingende Schwingung,
- \(\alpha=0\): ungedämpfte Dauerschwingung,
- \(\alpha>0\): anwachsende Schwingung.

Die Skizze auf Mitschrift-PDF-S. 21 zeigt genau eine Schwingung unter einer exponentiellen Hüllkurve.

---

## 3.6 Warum taucht bei Jordanblöcken ein Faktor \(t\) auf?

Ein Jordanblock lässt sich schreiben als

\[
J=\lambda I+N,
\]

wobei \(N\) nilpotent ist.

Für einen \(2\times2\)-Jordanblock

\[
N=
\begin{bmatrix}
0&1\\
0&0
\end{bmatrix},
\qquad
N^2=0.
\]

Dann

\[
e^{Jt}
=
e^{\lambda t}e^{Nt}.
\]

Wegen \(N^2=0\) bricht die Reihe ab:

\[
e^{Nt}
=
I+Nt.
\]

Somit

\[
\boxed{
e^{Jt}
=
e^{\lambda t}
\begin{bmatrix}
1&t\\
0&1
\end{bmatrix}
}.
\]

Der Faktor \(t\) entsteht also direkt aus dem nilpotenten Anteil des Jordanblocks.

Für einen Block der Länge 3:

\[
e^{Jt}
=
e^{\lambda t}
\begin{bmatrix}
1&t&\frac{t^2}{2}\\
0&1&t\\
0&0&1
\end{bmatrix}.
\]

Quelle: `skript.pdf`, PDF-S. 45, Theorem 2.16.

---

# 4. Allgemeines Rechenschema: Zustandstransformation

## Fall A: reelle, linear unabhängige Eigenvektoren

1. Charakteristisches Polynom:

\[
\det(A-\lambda I)=0.
\]

2. Eigenwerte bestimmen.

3. Für jeden Eigenwert:

\[
(A-\lambda_iI)v_i=0.
\]

4. Transformationsmatrix:

\[
V=
\begin{bmatrix}
v_1&v_2&\cdots&v_n
\end{bmatrix}.
\]

5. Kontrollrechnung:

\[
\tilde A=V^{-1}AV
\]

oder rechnerisch meist einfacher:

\[
\boxed{AV=V\tilde A}.
\]

---

## Fall B: nicht diagonalisierbare Matrix

Für eine Jordankette zum Eigenwert \(\lambda\):

\[
(A-\lambda I)v_1=0,
\]

\[
(A-\lambda I)v_2=v_1,
\]

\[
(A-\lambda I)v_3=v_2,
\]

usw.

Dann werden die Vektoren in dieser Reihenfolge in \(V\) eingetragen:

\[
V=
\begin{bmatrix}
v_1&v_2&v_3&\cdots
\end{bmatrix}.
\]

---

## Fall C: komplex konjugiertes Eigenwertpaar

Sei

\[
\lambda=\alpha+j\beta
\]

mit komplexem Eigenvektor

\[
v=p+jq.
\]

Dann kann eine reelle Transformationsmatrix über

\[
V=
\begin{bmatrix}
p&q
\end{bmatrix}
\]

gebildet werden. Der zugehörige reelle Block lautet bei dieser Konvention

\[
\boxed{
\tilde A_{\mathrm c}
=
\begin{bmatrix}
\alpha&\beta\\
-\beta&\alpha
\end{bmatrix}
}.
\]

Andere Spaltenreihenfolgen oder Vorzeichen sind ebenfalls zulässig und ändern entsprechend die Vorzeichen im Block.

---

# 5. Aufgabe 1a – drei verschiedene reelle Eigenwerte

## Gegeben

\[
A=
\begin{bmatrix}
4&1&0\\
0&3&0\\
0&0&2
\end{bmatrix}.
\]

## 5.1 Eigenwerte

Da \(A\) obere Dreiecksgestalt besitzt:

\[
\det(A-\lambda I)
=
(4-\lambda)(3-\lambda)(2-\lambda).
\]

Damit:

\[
\lambda_1=4,
\qquad
\lambda_2=3,
\qquad
\lambda_3=2.
\]

Drei verschiedene Eigenwerte bedeuten: \(A\) ist diagonalisierbar.

---

## 5.2 Eigenvektor zu \(\lambda_1=4\)

\[
A-4I
=
\begin{bmatrix}
0&1&0\\
0&-1&0\\
0&0&-2
\end{bmatrix}.
\]

Aus

\[
(A-4I)v_1=0
\]

folgt

\[
v_{1,2}=0,
\qquad
v_{1,3}=0.
\]

Wahl:

\[
v_1=
\begin{bmatrix}
1\\0\\0
\end{bmatrix}.
\]

---

## 5.3 Eigenvektor zu \(\lambda_2=3\)

\[
A-3I
=
\begin{bmatrix}
1&1&0\\
0&0&0\\
0&0&-1
\end{bmatrix}.
\]

Damit

\[
v_{2,1}+v_{2,2}=0,
\qquad
v_{2,3}=0.
\]

Wahl:

\[
v_2=
\begin{bmatrix}
-1\\1\\0
\end{bmatrix}.
\]

---

## 5.4 Eigenvektor zu \(\lambda_3=2\)

\[
A-2I
=
\begin{bmatrix}
2&1&0\\
0&1&0\\
0&0&0
\end{bmatrix}.
\]

Damit

\[
v_{3,1}=0,
\qquad
v_{3,2}=0.
\]

Wahl:

\[
v_3=
\begin{bmatrix}
0\\0\\1
\end{bmatrix}.
\]

---

## 5.5 Transformation

\[
\boxed{
V=
\begin{bmatrix}
1&-1&0\\
0&1&0\\
0&0&1
\end{bmatrix}
}
\]

und

\[
\boxed{
\tilde A=
\begin{bmatrix}
4&0&0\\
0&3&0\\
0&0&2
\end{bmatrix}
}.
\]

Die Mitschrift auf PDF-S. 22–23 enthält diesen Rechenweg vollständig und korrekt.

---

# 6. Aufgabe 1b – mehrfacher Eigenwert, trotzdem diagonalisierbar

## Gegeben

\[
A=
\begin{bmatrix}
6&0&1\\
0&6&0\\
0&0&3
\end{bmatrix}.
\]

## 6.1 Eigenwerte

\[
\det(A-\lambda I)
=
(6-\lambda)^2(3-\lambda).
\]

Damit:

\[
\lambda_{1,2}=6,
\qquad
\lambda_3=3.
\]

---

## 6.2 Eigenraum zu \(\lambda=6\)

\[
A-6I
=
\begin{bmatrix}
0&0&1\\
0&0&0\\
0&0&-3
\end{bmatrix}.
\]

Es folgt

\[
v_3=0,
\]

während \(v_1\) und \(v_2\) frei sind. Der Eigenraum besitzt Dimension 2 und entspricht der algebraischen Vielfachheit 2.

Wahl:

\[
v_1=
\begin{bmatrix}
1\\0\\0
\end{bmatrix},
\qquad
v_2=
\begin{bmatrix}
0\\1\\0
\end{bmatrix}.
\]

---

## 6.3 Eigenvektor zu \(\lambda=3\)

\[
A-3I
=
\begin{bmatrix}
3&0&1\\
0&3&0\\
0&0&0
\end{bmatrix}.
\]

Damit

\[
3v_1+v_3=0,
\qquad
v_2=0.
\]

Wahl:

\[
v_3=
\begin{bmatrix}
1\\0\\-3
\end{bmatrix}.
\]

---

## 6.4 Transformation

\[
\boxed{
V=
\begin{bmatrix}
1&0&1\\
0&1&0\\
0&0&-3
\end{bmatrix}
}
\]

\[
\boxed{
\tilde A=
\operatorname{diag}(6,6,3)
}.
\]

---

# 7. Aufgabe 1c – Vorzeichenfehler in der offiziellen Lösung

## Gegeben

\[
A=
\begin{bmatrix}
4&0&-1\\
0&4&0\\
0&0&5
\end{bmatrix}.
\]

## 7.1 Eigenwerte

\[
\det(A-\lambda I)
=
(4-\lambda)^2(5-\lambda).
\]

Damit:

\[
\lambda_{1,2}=4,
\qquad
\lambda_3=5.
\]

---

## 7.2 Eigenraum zu \(\lambda=4\)

\[
A-4I
=
\begin{bmatrix}
0&0&-1\\
0&0&0\\
0&0&1
\end{bmatrix}.
\]

Daraus:

\[
v_3=0.
\]

Wahl:

\[
v_1=
\begin{bmatrix}
1\\0\\0
\end{bmatrix},
\qquad
v_2=
\begin{bmatrix}
0\\1\\0
\end{bmatrix}.
\]

---

## 7.3 Eigenvektor zu \(\lambda=5\)

\[
A-5I
=
\begin{bmatrix}
-1&0&-1\\
0&-1&0\\
0&0&0
\end{bmatrix}.
\]

Damit:

\[
-v_1-v_3=0,
\qquad
v_2=0.
\]

Also

\[
v_1=-v_3.
\]

Wahl:

\[
v_3=
\begin{bmatrix}
-1\\0\\1
\end{bmatrix}.
\]

---

## 7.4 Korrekte Transformation

\[
\boxed{
V_{\mathrm{korrekt}}
=
\begin{bmatrix}
1&0&-1\\
0&1&0\\
0&0&1
\end{bmatrix}
}
\]

\[
\boxed{
\tilde A=
\operatorname{diag}(4,4,5)
}.
\]

### [KORRIGIERT – OFFIZIELLE LÖSUNG FEHLERHAFT]

Auf der offiziellen Lösungsseite steht in der dritten Spalte fälschlich

\[
\begin{bmatrix}
1\\0\\1
\end{bmatrix}.
\]

Dieser Vektor ist kein Eigenvektor zu \(\lambda=5\), denn

\[
A
\begin{bmatrix}
1\\0\\1
\end{bmatrix}
=
\begin{bmatrix}
3\\0\\5
\end{bmatrix}
\neq
5
\begin{bmatrix}
1\\0\\1
\end{bmatrix}.
\]

Mit dem gedruckten \(V\) entsteht daher keine Diagonalmatrix. Das Minuszeichen ist zwingend.

Quelle des Widerspruchs: `Regelungstechnik_Tutorium_komplett.pdf`, Tutorium 02, Blattseite 2/3.

---

# 8. Aufgabe 1d – defekter Eigenwert und Hauptvektor

## Gegeben

\[
A=
\begin{bmatrix}
1&2&2\\
0&1&-1\\
0&0&2
\end{bmatrix}.
\]

## 8.1 Eigenwerte

\[
\det(A-\lambda I)
=
(1-\lambda)^2(2-\lambda).
\]

Damit:

\[
\lambda_{1,2}=1
\]

mit algebraischer Vielfachheit 2 und

\[
\lambda_3=2.
\]

---

## 8.2 Geometrische Vielfachheit von \(\lambda=1\)

\[
A-I
=
\begin{bmatrix}
0&2&2\\
0&0&-1\\
0&0&1
\end{bmatrix}.
\]

Der Rang beträgt 2. Damit:

\[
\rho(1)
=
3-2
=
1.
\]

Es existiert nur ein Eigenvektor, obwohl die algebraische Vielfachheit 2 beträgt. Die Matrix ist nicht diagonalisierbar.

---

## 8.3 Eigenvektor zu \(\lambda=1\)

\[
(A-I)v_1=0.
\]

Aus der zweiten Zeile:

\[
-v_{1,3}=0.
\]

Aus der ersten Zeile:

\[
2v_{1,2}+2v_{1,3}=0.
\]

Somit

\[
v_{1,2}=v_{1,3}=0.
\]

Wahl:

\[
v_1=
\begin{bmatrix}
1\\0\\0
\end{bmatrix}.
\]

---

## 8.4 Hauptvektor zu \(\lambda=1\)

Gesucht ist \(v_2\) mit

\[
(A-I)v_2=v_1.
\]

Also

\[
\begin{bmatrix}
0&2&2\\
0&0&-1\\
0&0&1
\end{bmatrix}
\begin{bmatrix}
a\\b\\c
\end{bmatrix}
=
\begin{bmatrix}
1\\0\\0
\end{bmatrix}.
\]

Aus Zeile 2 und 3:

\[
c=0.
\]

Aus Zeile 1:

\[
2b=1
\quad\Rightarrow\quad
b=\frac12.
\]

\(a\) ist frei; einfachste Wahl \(a=0\):

\[
v_2=
\begin{bmatrix}
0\\\frac12\\0
\end{bmatrix}.
\]

### Wichtige Regel

Die rechte Seite der Hauptvektorgleichung ist der vorherige Eigen- bzw. Hauptvektor und nicht der Nullvektor.

---

## 8.5 Eigenvektor zu \(\lambda=2\)

\[
A-2I
=
\begin{bmatrix}
-1&2&2\\
0&-1&-1\\
0&0&0
\end{bmatrix}.
\]

Aus der zweiten Zeile:

\[
-v_2-v_3=0
\quad\Rightarrow\quad
v_2=-v_3.
\]

Aus der ersten Zeile:

\[
-v_1+2(-v_3)+2v_3=0
\quad\Rightarrow\quad
v_1=0.
\]

Wahl \(v_3=1\):

\[
v_3=
\begin{bmatrix}
0\\-1\\1
\end{bmatrix}.
\]

---

## 8.6 Transformation und Jordanform

\[
\boxed{
V=
\begin{bmatrix}
1&0&0\\
0&\frac12&-1\\
0&0&1
\end{bmatrix}
}
\]

\[
\boxed{
\tilde A=
\begin{bmatrix}
1&1&0\\
0&1&0\\
0&0&2
\end{bmatrix}
}.
\]

Die Mitschrift auf PDF-S. 23–24 ist korrekt. Die Bemerkung „Eigenvektor nicht 0“ bedeutet: Die rechte Seite bei der Hauptvektorgleichung ist der bereits bestimmte Eigenvektor.

---

# 9. Aufgabe 1e – Jordanblock der Länge 3

## Gegeben

\[
A=
\begin{bmatrix}
5&4&2\\
0&5&1\\
0&0&5
\end{bmatrix}.
\]

## 9.1 Eigenwert und Eigenraum

\[
\det(A-\lambda I)
=
(5-\lambda)^3.
\]

Es existiert nur der Eigenwert

\[
\lambda=5
\]

mit algebraischer Vielfachheit 3.

\[
A-5I
=
\begin{bmatrix}
0&4&2\\
0&0&1\\
0&0&0
\end{bmatrix}.
\]

Aus

\[
(A-5I)v_1=0
\]

folgt

\[
v_{1,3}=0,
\qquad
v_{1,2}=0.
\]

Der Eigenraum ist eindimensional. Die Matrix benötigt daher eine Jordankette der Länge 3.

---

## 9.2 Geeignet skalierter Eigenvektor

Wahl:

\[
v_1=
\begin{bmatrix}
4\\0\\0
\end{bmatrix}.
\]

Die Skalierung 4 wird gewählt, damit die folgenden Hauptvektoren einfache ganzzahlige Einträge besitzen.

---

## 9.3 Hauptvektor zweiter Stufe

Gesucht:

\[
(A-5I)v_2=v_1.
\]

Die Wahl

\[
v_2=
\begin{bmatrix}
2\\1\\0
\end{bmatrix}
\]

liefert

\[
(A-5I)v_2
=
\begin{bmatrix}
4\\0\\0
\end{bmatrix}
=
v_1.
\]

---

## 9.4 Hauptvektor dritter Stufe

Gesucht:

\[
(A-5I)v_3=v_2.
\]

Die Wahl

\[
v_3=
\begin{bmatrix}
0\\0\\1
\end{bmatrix}
\]

liefert

\[
(A-5I)v_3
=
\begin{bmatrix}
2\\1\\0
\end{bmatrix}
=
v_2.
\]

---

## 9.5 Transformation

\[
\boxed{
V=
\begin{bmatrix}
4&2&0\\
0&1&0\\
0&0&1
\end{bmatrix}
}
\]

\[
\boxed{
\tilde A=
\begin{bmatrix}
5&1&0\\
0&5&1\\
0&0&5
\end{bmatrix}
}.
\]

---

# 10. Aufgabe 1f – ein Eigenwert 0 und eine Jordankette der Länge 3

## Gegeben

\[
A=
\begin{bmatrix}
0&0&1&0\\
0&0&0&1\\
-1&1&-2&1\\
1&-1&1&-1
\end{bmatrix}.
\]

## 10.1 Charakteristisches Polynom

\[
\boxed{
\det(\lambda I-A)
=
\lambda(\lambda+1)^3
}.
\]

Damit:

\[
\lambda_1=0,
\qquad
\lambda_{2,3,4}=-1.
\]

---

## 10.2 Eigenvektor zu \(\lambda=0\)

Eine mögliche Wahl:

\[
v_1=
\begin{bmatrix}
1\\1\\0\\0
\end{bmatrix}.
\]

Kontrolle:

\[
Av_1=0.
\]

---

## 10.3 Eigenvektor zu \(\lambda=-1\)

Gesucht:

\[
(A+I)v_2=0.
\]

Eine mögliche Wahl:

\[
v_2=
\begin{bmatrix}
1\\0\\-1\\0
\end{bmatrix}.
\]

---

## 10.4 Hauptvektoren

Zweiter Vektor der Kette:

\[
(A+I)v_3=v_2.
\]

Wahl:

\[
v_3=
\begin{bmatrix}
1\\1\\0\\-1
\end{bmatrix}.
\]

Kontrolle:

\[
(A+I)v_3
=
\begin{bmatrix}
1\\0\\-1\\0
\end{bmatrix}
=
v_2.
\]

Dritter Vektor der Kette:

\[
(A+I)v_4=v_3.
\]

Wahl:

\[
v_4=
\begin{bmatrix}
1\\2\\0\\-1
\end{bmatrix}.
\]

Kontrolle:

\[
(A+I)v_4
=
\begin{bmatrix}
1\\1\\0\\-1
\end{bmatrix}
=
v_3.
\]

---

## 10.5 Transformation

\[
\boxed{
V=
\begin{bmatrix}
1&1&1&1\\
1&0&1&2\\
0&-1&0&0\\
0&0&-1&-1
\end{bmatrix}
}
\]

\[
\boxed{
\tilde A=
\begin{bmatrix}
0&0&0&0\\
0&-1&1&0\\
0&0&-1&1\\
0&0&0&-1
\end{bmatrix}
}.
\]

Der erste Block gehört zu \(\lambda=0\), der \(3\times3\)-Jordanblock zu \(\lambda=-1\).

---

# 11. Aufgabe 1g – komplex konjugiertes Eigenwertpaar

## Gegeben

\[
A=
\begin{bmatrix}
2&-5\\
1&2
\end{bmatrix}.
\]

## 11.1 Eigenwerte

\[
\det(A-\lambda I)
=
\begin{vmatrix}
2-\lambda&-5\\
1&2-\lambda
\end{vmatrix}.
\]

\[
(2-\lambda)^2+5=0.
\]

Damit:

\[
\boxed{
\lambda_{1,2}=2\pm j\sqrt5
}.
\]

---

## 11.2 Komplexer Eigenvektor

Für

\[
\lambda_1=2+j\sqrt5
\]

gilt

\[
(A-\lambda_1I)v=0.
\]

Eine mögliche Wahl ist

\[
v=
\begin{bmatrix}
j\sqrt5\\
1
\end{bmatrix}.
\]

Zerlegung:

\[
v=p+jq
\]

mit

\[
p=
\begin{bmatrix}
0\\1
\end{bmatrix},
\qquad
q=
\begin{bmatrix}
\sqrt5\\0
\end{bmatrix}.
\]

---

## 11.3 Reelle Transformation

\[
\boxed{
V=
\begin{bmatrix}
0&\sqrt5\\
1&0
\end{bmatrix}
}
\]

\[
\boxed{
\tilde A
=
\begin{bmatrix}
2&\sqrt5\\
-\sqrt5&2
\end{bmatrix}
}.
\]

Interpretation:

- Realteil \(2\): exponentiell anwachsende Hüllkurve \(e^{2t}\),
- Imaginärteil \(\sqrt5\): Schwingungsfrequenz \(\sqrt5\).

Die Mitschrift auf PDF-S. 24 ist fachlich korrekt.

---

# 12. Aufgabe 1h – fehlender Skalierungsfaktor in der offiziellen Lösung

## Gegeben

\[
A=
\begin{bmatrix}
1&-4&0\\
2&1&0\\
0&0&5
\end{bmatrix}.
\]

## 12.1 Eigenwerte

Für den oberen \(2\times2\)-Block:

\[
(1-\lambda)^2+8=0.
\]

Damit:

\[
\lambda_{1,2}
=
1\pm j2\sqrt2.
\]

Zusätzlich:

\[
\lambda_3=5.
\]

---

## 12.2 Komplexer Eigenvektor

Für

\[
\lambda_1=1+j2\sqrt2
\]

ist eine mögliche Wahl

\[
v=
\begin{bmatrix}
j\sqrt2\\
1\\
0
\end{bmatrix}.
\]

Damit:

\[
p=
\begin{bmatrix}
0\\1\\0
\end{bmatrix},
\qquad
q=
\begin{bmatrix}
\sqrt2\\0\\0
\end{bmatrix}.
\]

Zum Eigenwert 5:

\[
v_3=
\begin{bmatrix}
0\\0\\1
\end{bmatrix}.
\]

---

## 12.3 Korrekte Transformation

\[
\boxed{
V_{\mathrm{korrekt}}
=
\begin{bmatrix}
0&\sqrt2&0\\
1&0&0\\
0&0&1
\end{bmatrix}
}
\]

\[
\boxed{
\tilde A=
\begin{bmatrix}
1&2\sqrt2&0\\
-2\sqrt2&1&0\\
0&0&5
\end{bmatrix}
}.
\]

### [KORRIGIERT – OFFIZIELLE LÖSUNG INKONSISTENT]

Gedruckt ist

\[
V_{\mathrm{offiziell}}
=
\begin{bmatrix}
0&1&0\\
1&0&0\\
0&0&1
\end{bmatrix},
\]

gleichzeitig aber der symmetrisch skalierte komplexe Block mit \(2\sqrt2\).

Mit dem gedruckten \(V\) ergibt sich tatsächlich

\[
V_{\mathrm{offiziell}}^{-1}AV_{\mathrm{offiziell}}
=
\begin{bmatrix}
1&2&0\\
-4&1&0\\
0&0&5
\end{bmatrix},
\]

nicht die gedruckte \(\tilde A\).

Der Faktor \(\sqrt2\) in der zweiten Spalte von \(V\) fehlt.

---

# 13. Aufgabe 1i – falsche Transformationsmatrix in der offiziellen Lösung

## Gegeben

\[
A=
\begin{bmatrix}
0&-3&0\\
3&0&0\\
1&2&4
\end{bmatrix}.
\]

## 13.1 Eigenwerte

\[
\det(A-\lambda I)
=
(4-\lambda)(\lambda^2+9).
\]

Damit:

\[
\lambda_{1,2}=\pm3j,
\qquad
\lambda_3=4.
\]

---

## 13.2 Komplexer Eigenvektor

Für

\[
\lambda_1=3j
\]

ist beispielsweise

\[
v=
\begin{bmatrix}
-2-j\\
-1+2j\\
1
\end{bmatrix}.
\]

Damit:

\[
p=
\begin{bmatrix}
-2\\-1\\1
\end{bmatrix},
\qquad
q=
\begin{bmatrix}
-1\\2\\0
\end{bmatrix}.
\]

Zum Eigenwert 4:

\[
v_3=
\begin{bmatrix}
0\\0\\1
\end{bmatrix}.
\]

---

## 13.3 Korrekte Transformation

\[
\boxed{
V_{\mathrm{korrekt}}
=
\begin{bmatrix}
-2&-1&0\\
-1&2&0\\
1&0&1
\end{bmatrix}
}
\]

\[
\boxed{
\tilde A=
\begin{bmatrix}
0&3&0\\
-3&0&0\\
0&0&4
\end{bmatrix}
}.
\]

### [KORRIGIERT – OFFIZIELLE LÖSUNG FEHLERHAFT]

Gedruckt ist lediglich die Vertauschungsmatrix

\[
V_{\mathrm{offiziell}}
=
\begin{bmatrix}
0&1&0\\
1&0&0\\
0&0&1
\end{bmatrix}.
\]

Mit ihr erhält man

\[
V_{\mathrm{offiziell}}^{-1}AV_{\mathrm{offiziell}}
=
\begin{bmatrix}
0&3&0\\
-3&0&0\\
2&1&4
\end{bmatrix}.
\]

Die Kopplung in der dritten Zeile verschwindet also nicht. Das gedruckte \(V\) kann nicht zur gedruckten \(\tilde A\) gehören.

---

# 14. Aufgabe 2 – allgemeines Schema zur Transitionsmatrix

## Schritt 1: System transformieren

\[
\tilde A=V^{-1}AV.
\]

## Schritt 2: Exponentialmatrix in Normalform berechnen

Diagonal:

\[
e^{\tilde At}
=
\operatorname{diag}
(e^{\lambda_1t},\ldots,e^{\lambda_nt}).
\]

Jordanblock:

\[
e^{Jt}
=
e^{\lambda t}
\begin{bmatrix}
1&t&\frac{t^2}{2!}&\cdots\\
0&1&t&\cdots\\
\vdots&&\ddots&\\
0&\cdots&0&1
\end{bmatrix}.
\]

Komplexer reeller Block

\[
R=
\begin{bmatrix}
\alpha&\beta\\
-\beta&\alpha
\end{bmatrix}
\]

führt zu

\[
e^{Rt}
=
e^{\alpha t}
\begin{bmatrix}
\cos(\beta t)&\sin(\beta t)\\
-\sin(\beta t)&\cos(\beta t)
\end{bmatrix}.
\]

## Schritt 3: Rücktransformieren

\[
\boxed{
\Phi(t)=Ve^{\tilde At}V^{-1}
}.
\]

## Schritt 4: Pflichtkontrollen

\[
\Phi(0)=I,
\]

\[
\dot\Phi(t)=A\Phi(t),
\]

\[
\dot\Phi(0)=A.
\]

---

# 15. Aufgabe 2 – System a): Transitionsmatrix

## 15.1 Ausgangsdaten

\[
V=
\begin{bmatrix}
1&-1&0\\
0&1&0\\
0&0&1
\end{bmatrix},
\]

\[
V^{-1}
=
\begin{bmatrix}
1&1&0\\
0&1&0\\
0&0&1
\end{bmatrix},
\]

\[
\tilde A
=
\operatorname{diag}(4,3,2).
\]

Damit:

\[
e^{\tilde At}
=
\begin{bmatrix}
e^{4t}&0&0\\
0&e^{3t}&0\\
0&0&e^{2t}
\end{bmatrix}.
\]

---

## 15.2 Rücktransformation

\[
\Phi(t)
=
Ve^{\tilde At}V^{-1}.
\]

\[
\Phi(t)
=
\begin{bmatrix}
1&-1&0\\
0&1&0\\
0&0&1
\end{bmatrix}
\begin{bmatrix}
e^{4t}&0&0\\
0&e^{3t}&0\\
0&0&e^{2t}
\end{bmatrix}
\begin{bmatrix}
1&1&0\\
0&1&0\\
0&0&1
\end{bmatrix}.
\]

Ergebnis:

\[
\boxed{
\Phi_a(t)
=
\begin{bmatrix}
e^{4t}&e^{4t}-e^{3t}&0\\
0&e^{3t}&0\\
0&0&e^{2t}
\end{bmatrix}
}.
\]

Kontrolle:

\[
\Phi_a(0)
=
I.
\]

Die Mitschrift auf PDF-S. 25 ist korrekt.

---

# 16. Aufgabe 2 – System a): vollständige Lösung mit Eingang

## Gegeben

\[
B=
\begin{bmatrix}
0\\0\\1
\end{bmatrix},
\qquad
u(t)=1+t,
\qquad
x_0=
\begin{bmatrix}
1\\0\\0
\end{bmatrix}.
\]

Gesamtlösung:

\[
x(t)
=
\Phi_a(t)x_0
+
\int_0^t
\Phi_a(t-\tau)B(1+\tau)\,\mathrm d\tau.
\]

---

## 16.1 Homogener Anteil

\[
\Phi_a(t)x_0
=
\begin{bmatrix}
e^{4t}\\0\\0
\end{bmatrix}.
\]

---

## 16.2 Inhomogener Anteil

Da \(B\) die dritte Einheitsrichtung ist, wird nur die dritte Spalte von \(\Phi_a\) benötigt:

\[
\Phi_a(t-\tau)B
=
\begin{bmatrix}
0\\0\\e^{2(t-\tau)}
\end{bmatrix}.
\]

Damit:

\[
x_{\mathrm{inh}}(t)
=
\begin{bmatrix}
0\\
0\\
\displaystyle
\int_0^t
e^{2(t-\tau)}(1+\tau)\,\mathrm d\tau
\end{bmatrix}.
\]

Berechnung des Integrals:

\[
\int_0^t
e^{2(t-\tau)}(1+\tau)\,\mathrm d\tau
=
e^{2t}
\int_0^t
e^{-2\tau}(1+\tau)\,\mathrm d\tau.
\]

Eine Stammfunktion ist

\[
\int e^{-2\tau}(1+\tau)\,\mathrm d\tau
=
-\left(
\frac{\tau}{2}
+
\frac34
\right)e^{-2\tau}.
\]

Damit:

\[
e^{2t}
\left[
-\left(
\frac{\tau}{2}
+
\frac34
\right)e^{-2\tau}
\right]_0^t
=
\frac34e^{2t}
-\frac12t
-\frac34.
\]

Also

\[
x_{\mathrm{inh}}(t)
=
\begin{bmatrix}
0\\
0\\
\frac34(e^{2t}-1)-\frac12t
\end{bmatrix}.
\]

---

## 16.3 Gesamtergebnis

\[
\boxed{
x_a(t)
=
\begin{bmatrix}
e^{4t}\\
0\\
\frac34(e^{2t}-1)-\frac12t
\end{bmatrix}
}.
\]

Kontrolle der Anfangsbedingung:

\[
x_a(0)
=
\begin{bmatrix}
1\\0\\0
\end{bmatrix}
=x_0.
\]

---

# 17. Aufgabe 2 – System d): Transitionsmatrix

## 17.1 Ausgangsdaten

\[
V=
\begin{bmatrix}
1&0&0\\
0&\frac12&-1\\
0&0&1
\end{bmatrix},
\]

\[
V^{-1}
=
\begin{bmatrix}
1&0&0\\
0&2&2\\
0&0&1
\end{bmatrix},
\]

\[
\tilde A=
\begin{bmatrix}
1&1&0\\
0&1&0\\
0&0&2
\end{bmatrix}.
\]

Für den \(2\times2\)-Jordanblock:

\[
e^{Jt}
=
e^t
\begin{bmatrix}
1&t\\
0&1
\end{bmatrix}.
\]

Somit:

\[
e^{\tilde At}
=
\begin{bmatrix}
e^t&te^t&0\\
0&e^t&0\\
0&0&e^{2t}
\end{bmatrix}.
\]

---

## 17.2 Rücktransformation

\[
\Phi_d(t)
=
Ve^{\tilde At}V^{-1}.
\]

Nach der Matrixmultiplikation:

\[
\boxed{
\Phi_d(t)
=
\begin{bmatrix}
e^t&2te^t&2te^t\\
0&e^t&e^t-e^{2t}\\
0&0&e^{2t}
\end{bmatrix}
}.
\]

Kontrolle:

\[
\Phi_d(0)=I.
\]

Der Faktor \(t\) in der ersten Zeile stammt direkt aus dem Jordanblock.

---

# 18. Aufgabe 2 – System d): vollständige Lösung mit Eingang

## Gegeben

\[
B=
\begin{bmatrix}
0\\0\\1
\end{bmatrix},
\qquad
u(t)=1+t,
\qquad
x_0=
\begin{bmatrix}
1\\0\\0
\end{bmatrix}.
\]

---

## 18.1 Homogener Anteil

Die erste Spalte von \(\Phi_d(t)\) liefert

\[
\Phi_d(t)x_0
=
\begin{bmatrix}
e^t\\0\\0
\end{bmatrix}.
\]

---

## 18.2 Inhomogener Anteil

Da \(B=e_3\), wird die dritte Spalte benötigt:

\[
\Phi_d(t-\tau)B
=
\begin{bmatrix}
2(t-\tau)e^{t-\tau}\\
e^{t-\tau}-e^{2(t-\tau)}\\
e^{2(t-\tau)}
\end{bmatrix}.
\]

Damit:

\[
x_{\mathrm{inh}}(t)
=
\begin{bmatrix}
I_1(t)\\
I_2(t)\\
I_3(t)
\end{bmatrix},
\]

wobei

\[
I_1(t)
=
\int_0^t
2(t-\tau)e^{t-\tau}(1+\tau)\,\mathrm d\tau,
\]

\[
I_2(t)
=
\int_0^t
\left(
e^{t-\tau}-e^{2(t-\tau)}
\right)(1+\tau)\,\mathrm d\tau,
\]

\[
I_3(t)
=
\int_0^t
e^{2(t-\tau)}(1+\tau)\,\mathrm d\tau.
\]

Auswertung:

\[
I_1(t)
=
4te^t+2t-6e^t+6,
\]

\[
I_2(t)
=
-\frac12t
-\frac34e^{2t}
+2e^t
-\frac54,
\]

\[
I_3(t)
=
-\frac12t
+\frac34e^{2t}
-\frac34.
\]

---

## 18.3 Gesamtergebnis

Erste Komponente:

\[
x_1(t)
=
e^t+I_1(t)
=
(4t-5)e^t+2t+6.
\]

Zweite Komponente:

\[
x_2(t)
=
I_2(t)
=
\frac{-3e^{2t}+8e^t-2t-5}{4}.
\]

Dritte Komponente:

\[
x_3(t)
=
I_3(t)
=
\frac{3e^{2t}-2t-3}{4}.
\]

Damit:

\[
\boxed{
x_d(t)
=
\begin{bmatrix}
(4t-5)e^t+2t+6\\[1mm]
\dfrac{-3e^{2t}+8e^t-2t-5}{4}\\[3mm]
\dfrac{3e^{2t}-2t-3}{4}
\end{bmatrix}
}.
\]

Kontrolle:

\[
x_d(0)
=
\begin{bmatrix}
1\\0\\0
\end{bmatrix}.
\]

Die offizielle Endlösung ist korrekt. In der Mitschrift wurde dieser inhomogene Rechenweg nur für System a) vollständig ausgeführt.

---

# 19. Aufgabe 2 – System g): korrekte Transitionsmatrix

## 19.1 Reeller Normalformblock

\[
\tilde A
=
\begin{bmatrix}
2&\sqrt5\\
-\sqrt5&2
\end{bmatrix}
=
2I+
\begin{bmatrix}
0&\sqrt5\\
-\sqrt5&0
\end{bmatrix}.
\]

Daraus:

\[
e^{\tilde At}
=
e^{2t}
\begin{bmatrix}
\cos(\sqrt5t)&\sin(\sqrt5t)\\
-\sin(\sqrt5t)&\cos(\sqrt5t)
\end{bmatrix}.
\]

Mit

\[
V=
\begin{bmatrix}
0&\sqrt5\\
1&0
\end{bmatrix},
\qquad
V^{-1}
=
\begin{bmatrix}
0&1\\
\frac1{\sqrt5}&0
\end{bmatrix}
\]

folgt

\[
\Phi_g(t)
=
Ve^{\tilde At}V^{-1}.
\]

Ergebnis:

\[
\boxed{
\Phi_g(t)
=
e^{2t}
\begin{bmatrix}
\cos(\sqrt5t)&-\sqrt5\sin(\sqrt5t)\\[1mm]
\frac1{\sqrt5}\sin(\sqrt5t)&\cos(\sqrt5t)
\end{bmatrix}
}.
\]

---

## 19.2 Direkte Alternativherleitung

Schreibe

\[
A=2I+N,
\qquad
N=
\begin{bmatrix}
0&-5\\
1&0
\end{bmatrix}.
\]

Dann:

\[
N^2=-5I.
\]

Daher:

\[
e^{Nt}
=
I\cos(\sqrt5t)
+
\frac{N}{\sqrt5}\sin(\sqrt5t).
\]

Somit direkt:

\[
e^{At}
=
e^{2t}
\left[
I\cos(\sqrt5t)
+
\frac{N}{\sqrt5}\sin(\sqrt5t)
\right],
\]

was zum gleichen Ergebnis führt.

---

## 19.3 [KORRIGIERT – OFFIZIELLE TRANSITIONSMATRIX FALSCH]

Die auf Blattseite 3/3 gedruckte Matrix erfüllt bereits die notwendige Bedingung

\[
\Phi(0)=I
\]

nicht. Bei \(t=0\) liefert sie eine Diagonalmatrix mit negativen Skalierungsfaktoren statt der Einheitsmatrix.

Damit kann sie unmöglich \(e^{At}\) sein.

Die oben angegebene Matrix erfüllt:

\[
\Phi_g(0)=I
\]

und

\[
\dot\Phi_g(0)=A.
\]

---

# 20. Schnelle Kontrollmethoden

## 20.1 Transformation prüfen

Statt \(V^{-1}AV\) vollständig auszurechnen:

\[
\boxed{AV=V\tilde A}.
\]

Diese Gleichung ist häufig schneller und weniger fehleranfällig.

---

## 20.2 Eigenvektor prüfen

Für jeden Eigenvektor:

\[
Av=\lambda v.
\]

Ein einzelner Vergleich reicht oft, um einen Vorzeichenfehler zu erkennen.

---

## 20.3 Jordankette prüfen

\[
(A-\lambda I)v_1=0,
\]

\[
(A-\lambda I)v_2=v_1,
\]

\[
(A-\lambda I)v_3=v_2.
\]

---

## 20.4 Transitionsmatrix prüfen

Pflicht:

\[
\Phi(0)=I.
\]

Zusätzlich:

\[
\dot\Phi(0)=A.
\]

Bei einer vorgeschlagenen Matrix, die \(\Phi(0)\neq I\) liefert, muss keine weitere Rechnung mehr geprüft werden: Sie ist sicher falsch.

---

## 20.5 Systemlösung prüfen

1. Anfangsbedingung:

\[
x(0)=x_0.
\]

2. Differentialgleichung:

\[
\dot x(t)\stackrel{?}{=}Ax(t)+Bu(t).
\]

Beide Bedingungen müssen erfüllt sein.

---

# 21. Typische Fehler in Tutorium 02

1. Algebraische und geometrische Vielfachheit verwechseln.
2. Bei wiederholten Eigenwerten automatisch Diagonalisierbarkeit annehmen.
3. Hauptvektor wieder mit rechter Seite 0 berechnen.
4. Vektoren einer Jordankette in falscher Reihenfolge in \(V\) eintragen.
5. Bei komplexen Eigenvektoren Real- und Imaginärteil falsch anordnen.
6. Skalierungsfaktoren von Real- und Imaginärteil vergessen.
7. \(e^{At}\) komponentenweise statt als Matrixexponential behandeln.
8. Bei der Rücktransformation \(V^{-1}\) vergessen.
9. Im Faltungsintegral \(u(t)\) statt \(u(\tau)\) einsetzen.
10. \(\Phi(t-\tau)\) fälschlich durch \(\Phi(t)\) ersetzen.
11. Anfangswertanteil und Eingangsanteil vermischen.
12. Ergebnisse nicht mit \(\Phi(0)=I\) bzw. \(x(0)=x_0\) prüfen.

---

# 22. Qualitätsprüfung der Quellen

## Handschriftlich vollständig vorhanden

- Theorie und zentrale Formeln: PDF-S. 21–22.
- Vollständige Diagonalisierung von a): PDF-S. 22–23.
- Vollständige Jordanzerlegung von d): PDF-S. 23–24.
- Komplexe reelle Transformation von g): PDF-S. 24.
- Transitionsmatrix und Eingangslösung von a): PDF-S. 25–26.

## Nur als offizielles Endergebnis vorhanden

- Systeme b), c), e), f), h), i).
- Transitionsmatrix und Eingangslösung von d).
- Transitionsmatrix von g).

Die fehlenden Rechenwege wurden oben aus den Aufgabenstellungen vollständig hergeleitet und algebraisch kontrolliert.

## Nachgewiesene Fehler der offiziellen Lösungsseite

1. **Aufgabe 1c:** falsches Vorzeichen in der dritten Spalte von \(V\).
2. **Aufgabe 1h:** fehlender Faktor \(\sqrt2\) in \(V\).
3. **Aufgabe 1i:** gedrucktes \(V\) entkoppelt die dritte Zustandskomponente nicht.
4. **Aufgabe 2g:** gedruckte Transitionsmatrix verletzt \(\Phi(0)=I\).

Diese Aussagen folgen durch direkte Matrixmultiplikation und sind keine bloßen Vermutungen.

---

# 23. NotebookLM-Verifikation der offiziellen Widersprüche

--- NOTEBOOKLM-PROMPT ---

Prüfe ausschließlich anhand der hochgeladenen offiziellen Regelungstechnik-Unterlagen und durch direkte Matrixrechnung die folgenden Angaben aus „Tutorium 02 – Zeitliches Verhalten linearer Systeme“:

1. Aufgabe 1c:
\[
A=
\begin{bmatrix}
4&0&-1\\
0&4&0\\
0&0&5
\end{bmatrix}.
\]
Ist die gedruckte dritte Spalte \((1,0,1)^T\) wirklich ein Eigenvektor zu \(\lambda=5\), oder muss sie \((-1,0,1)^T\) lauten?

2. Aufgabe 1h:
Prüfe, ob das gedruckte
\[
V=
\begin{bmatrix}
0&1&0\\
1&0&0\\
0&0&1
\end{bmatrix}
\]
tatsächlich zur gedruckten Normalform mit Einträgen \(\pm2\sqrt2\) führt. Berechne \(V^{-1}AV\).

3. Aufgabe 1i:
Prüfe durch \(V^{-1}AV\), ob das gedruckte \(V\) die dritte Zustandskomponente wirklich entkoppelt.

4. Aufgabe 2g:
Setze \(t=0\) in die gedruckte Transitionsmatrix ein. Erfüllt sie die zwingende Bedingung \(\Phi(0)=I\)? Leite anschließend die korrekte Matrix \(e^{At}\) her.

Antworte für jeden Punkt getrennt. Belege die gedruckte Angabe mit Dokumentname und genauer Fundstelle. Unterscheide zwischen Quellenaussage und eigener Matrixrechnung.

--- ENDE ---

---

# 24. Kompaktformelsammlung Tutorium 02

## Transitionsmatrix

\[
\Phi(t)=e^{At}.
\]

## Homogene Lösung

\[
x(t)=\Phi(t)x_0.
\]

## Inhomogene Lösung

\[
x(t)
=
\Phi(t)x_0
+
\int_0^t
\Phi(t-\tau)Bu(\tau)\,\mathrm d\tau.
\]

## Zustandstransformation

\[
x=Vz,
\qquad
\tilde A=V^{-1}AV.
\]

## Rücktransformation der Transitionsmatrix

\[
\Phi(t)=Ve^{\tilde At}V^{-1}.
\]

## Diagonalisierbarkeit

\[
\sum_\lambda \dim\ker(A-\lambda I)=n.
\]

## Hauptvektorkette

\[
(A-\lambda I)v_1=0,
\]

\[
(A-\lambda I)v_{k+1}=v_k.
\]

## Komplexes Eigenwertpaar

\[
\lambda=\alpha\pm j\beta
\]

führt zu

\[
e^{\alpha t}
\cos(\beta t),
\qquad
e^{\alpha t}
\sin(\beta t).
\]

## Pflichtkontrollen

\[
\Phi(0)=I,
\qquad
\dot\Phi(0)=A,
\qquad
x(0)=x_0.
\]

---

# Tutorium 03 – Regelungsnormalform und Übertragungsfunktionen

## 1. Quellen und Seitenbereich

### Primärquellen

1. **RT-Tutorien-Mitschrift.pdf**, PDF-Seiten 28–38
   - S. 28: Theoriefragen und Aufgabe 1
   - S. 29: Regelungsnormalform, Laplace-Grundlagen, Transformationssätze und Übertragungsfunktion
   - S. 30–31: Sprunganregung und vollständige Rechnung zu Aufgabe 1a
   - S. 32: offizielle Lösungen zu Aufgabe 1 und Aufgabenstellung zu Aufgabe 2
   - S. 33: handschriftliche Rechnungen zu Aufgabe 2a und 2b
   - S. 34: offizielle Lösungen zu Aufgabe 2 und Aufgabe 3
   - S. 35: handschriftliche Rechnungen zu Aufgabe 3a und 3b
   - S. 36–37: Partialbruchzerlegung und Rücktransformation zu Aufgabe 4a
   - S. 38: leer
   - Tutorium 04 beginnt auf PDF-Seite 39.

2. **Regelungstechnik_Tutorium_komplett.pdf**, Tutorium 03, Blattseiten 1/4–4/4  
   Offizielle Aufgaben und Endergebnisse.

3. **skript.pdf**
   - PDF-S. 46: Definition 2.17 „Regelungsnormalform“
   - PDF-S. 53: Laplace-Rechenregeln, Dämpfungs- und Verschiebungssatz
   - PDF-S. 54–55: Äquivalenztabelle zur Laplace-Transformation
   - PDF-S. 56: Definition 3.4 und Theorem 3.5 „Übertragungsfunktion“
   - PDF-S. 57–58: Theorem 3.7 „Partialbruchzerlegung“

---

# 2. Zentrale Begriffe und Voraussetzungen

## 2.1 Laplace-Notation

Für eine Zeitfunktion \(f(t)\) wird die Laplace-Transformierte in den Unterlagen als

\[
\hat f(s)=\mathcal L\{f(t)\}
\]

bezeichnet. In Rechnungen wird oft verkürzt

\[
F(s)=\mathcal L\{f(t)\}
\]

geschrieben.

Für Ein- und Ausgang:

\[
U(s)=\mathcal L\{u(t)\},
\qquad
Y(s)=\mathcal L\{y(t)\}.
\]

---

## 2.2 Übertragungsfunktion

Für ein LTI-System mit **verschwindendem Anfangszustand**

\[
x_0=0
\]

gilt

\[
\boxed{Y(s)=G(s)U(s)}.
\]

Damit:

\[
\boxed{G(s)=\frac{Y(s)}{U(s)}}.
\]

### Wichtige Einschränkung

Die reine Beziehung

\[
Y(s)=G(s)U(s)
\]

beschreibt die durch den Eingang erzwungene Bewegung. Bei nicht verschwindenden Anfangsbedingungen kommt zusätzlich ein homogener Anteil hinzu.

Quelle: `skript.pdf`, PDF-S. 56, Definition 3.4 und Theorem 3.5.

---

## 2.3 Sprunganregung

Ein Sprung der Amplitude \(F_{\mathrm{ex}}\) ist

\[
u(t)=F_{\mathrm{ex}}\,\eta(t),
\]

wobei \(\eta(t)\) die Heaviside-Funktion ist.

Da

\[
\mathcal L\{\eta(t)\}=\frac1s,
\]

folgt

\[
\boxed{
U(s)=\frac{F_{\mathrm{ex}}}{s}
}.
\]

Daher liefert ein Sprung im Bildbereich immer einen zusätzlichen Faktor \(1/s\):

\[
\boxed{
Y(s)=G(s)\frac{F_{\mathrm{ex}}}{s}
}.
\]

Die Mitschrift stellt dieses Schema auf PDF-S. 30 grafisch und rechnerisch dar.

---

# 3. Theoriefragen

## 3.1 Warum steht die wesentliche Systeminformation in der letzten Zeile der Regelungsnormalform?

Die Regelungsnormalform eines SISO-Systems lautet

\[
A_R=
\begin{bmatrix}
0&1&0&\cdots&0\\
0&0&1&\cdots&0\\
\vdots&&&\ddots&\vdots\\
0&0&0&\cdots&1\\
-a_0&-a_1&-a_2&\cdots&-a_{n-1}
\end{bmatrix},
\]

\[
B_R=
\begin{bmatrix}
0\\
0\\
\vdots\\
0\\
b_0
\end{bmatrix},
\qquad
C_R=
\begin{bmatrix}
1&0&\cdots&0
\end{bmatrix},
\qquad
D=0.
\]

Die oberen Zeilen von \(A_R\) bilden lediglich die Ableitungskette ab:

\[
\dot x_1=x_2,\qquad
\dot x_2=x_3,\qquad
\dots,\qquad
\dot x_{n-1}=x_n.
\]

Erst die letzte Zeile enthält die dynamischen Koeffizienten:

\[
\dot x_n
=
-a_0x_1-a_1x_2-\dots-a_{n-1}x_n+b_0u.
\]

Diese Koeffizienten sind gleichzeitig die Koeffizienten der skalaren Differentialgleichung und des charakteristischen Polynoms.

Quelle: `skript.pdf`, PDF-S. 46, Definition 2.17.

---

## 3.2 Wann benutzt man den Verschiebungssatz der Laplace-Transformation?

### Tatsächlicher Verschiebungssatz im Skript

Für ein zeitlich verzögertes Signal

\[
f(t-a)\eta(t-a)
\]

gilt

\[
\boxed{
\mathcal L\{f(t-a)\eta(t-a)\}
=
e^{-as}F(s)
}.
\]

Er wird verwendet, wenn ein Signal erst bei \(t=a\) beginnt oder zeitlich verschoben wird.

Beispiele:

- verzögerter Sprung,
- verzögerter Impuls,
- stückweise definierte Eingangssignale,
- Totzeit.

### [KORRIGIERT] Verwechslung in der Mitschrift

Auf PDF-S. 29 steht unter der Überschrift „Verschiebungssatz“ die Formel

\[
\mathcal L\{e^{at}f(t)\}=F(s-a).
\]

Im offiziellen Skript heißt diese Regel jedoch **Dämpfungssatz**, nicht Verschiebungssatz.

Es sind zwei verschiedene Regeln:

\[
\boxed{
e^{at}f(t)
\longleftrightarrow
F(s-a)
}
\qquad
\text{Dämpfungssatz/Frequenzverschiebung}
\]

und

\[
\boxed{
f(t-a)\eta(t-a)
\longleftrightarrow
e^{-as}F(s)
}
\qquad
\text{Zeitverschiebung}.
\]

Quelle: `skript.pdf`, PDF-S. 53, Tabelle 3.1.

---

## 3.3 Wie erkennt man Sinus und Kosinus im \(s\)-Bereich?

Grundpaare:

\[
\boxed{
\mathcal L\{\sin(\omega t)\}
=
\frac{\omega}{s^2+\omega^2}
}
\]

\[
\boxed{
\mathcal L\{\cos(\omega t)\}
=
\frac{s}{s^2+\omega^2}
}
\]

Merksatz:

- Sinus: im Zähler steht die Frequenz \(\omega\).
- Kosinus: im Zähler steht \(s\).

Mit Exponentialfaktor:

\[
e^{at}\sin(\omega t)
\longleftrightarrow
\frac{\omega}{(s-a)^2+\omega^2},
\]

\[
e^{at}\cos(\omega t)
\longleftrightarrow
\frac{s-a}{(s-a)^2+\omega^2}.
\]

Für \(e^{-at}\) wird entsprechend \(s+a\) eingesetzt.

Quelle: `skript.pdf`, PDF-S. 55, Tabelle 3.2.

---

## 3.4 Warum ist die Laplace-Transformation für die Regelungstechnik hilfreich?

Sie ersetzt lineare Differentialgleichungen durch algebraische Gleichungen im \(s\)-Bereich.

Beispielsweise gilt bei passenden Anfangsbedingungen:

\[
\mathcal L\{\dot y(t)\}
=
sY(s)-y(0),
\]

\[
\mathcal L\{\ddot y(t)\}
=
s^2Y(s)-sy(0)-\dot y(0).
\]

Damit wird aus Ableiten und Integrieren im Zeitbereich hauptsächlich Multiplizieren und Dividieren mit \(s\).

Zusätzlich:

- Faltungen im Zeitbereich werden Produkte im Bildbereich.
- Reihen- und Parallelschaltungen lassen sich algebraisch behandeln.
- Die Systemantwort ergibt sich über \(Y=GU\).
- Pole und Nullstellen werden direkt sichtbar.

---

## 3.5 Warum gilt bei einer Sprunganregung \(U(s)=F_{\mathrm{ex}}/s\)?

Weil der Sprung geschrieben wird als

\[
u(t)=F_{\mathrm{ex}}\eta(t)
\]

und

\[
\mathcal L\{\eta(t)\}=\frac1s.
\]

Mit Linearität:

\[
\mathcal L\{F_{\mathrm{ex}}\eta(t)\}
=
F_{\mathrm{ex}}\mathcal L\{\eta(t)\}
=
\boxed{\frac{F_{\mathrm{ex}}}{s}}.
\]

---

## 3.6 Vorteil von \(Y(s)=G(s)U(s)\) gegenüber dem Zeitbereich

Im Zeitbereich müsste die Differentialgleichung gelöst oder eine Faltung berechnet werden. Im Bildbereich genügt zunächst die algebraische Multiplikation

\[
Y(s)=G(s)U(s).
\]

Danach wird nur noch rücktransformiert.

Das ist insbesondere bei

- höheren Systemordnungen,
- verschachtelten Blockschaltbildern,
- Standardanregungen,
- rationalen Übertragungsfunktionen

deutlich einfacher.

Quelle: `skript.pdf`, PDF-S. 57, Erläuterung nach Theorem 3.5.

---

## 3.7 Wann braucht man eine Partialbruchzerlegung?

Eine Partialbruchzerlegung wird benötigt, wenn eine rationale Bildfunktion

\[
Y(s)=\frac{Z(s)}{N(s)}
\]

nicht unmittelbar in einer Laplace-Tabelle vorkommt.

Sie wird in eine Summe bekannter Grundformen zerlegt:

\[
\frac{Z(s)}{N(s)}
=
\frac{A}{s-p_1}
+
\frac{B}{s-p_2}
+\dots
\]

oder bei mehrfachen Polen:

\[
\frac{A_1}{s-p}
+
\frac{A_2}{(s-p)^2}
+\dots
\]

oder bei irreduziblen quadratischen Faktoren:

\[
\frac{Cs+D}{s^2+as+b}.
\]

Danach kann jeder Summand einzeln rücktransformiert werden.

Quelle: `skript.pdf`, PDF-S. 57–58, Theorem 3.7.

---

# 4. Regelungsnormalform: allgemeines Rechenschema

## 4.1 Ausgangspunkt

Gegeben sei die skalare Differentialgleichung

\[
y^{(n)}
+
a_{n-1}y^{(n-1)}
+\dots+
a_1\dot y
+a_0y
=
b_0u.
\]

Zustände:

\[
x_1=y,
\qquad
x_2=\dot y,
\qquad
\dots,
\qquad
x_n=y^{(n-1)}.
\]

Dann:

\[
\dot x_1=x_2,
\qquad
\dot x_2=x_3,
\qquad
\dots,
\qquad
\dot x_{n-1}=x_n.
\]

Die letzte Zustandsgleichung ist

\[
\dot x_n
=
-a_0x_1
-a_1x_2
-\dots
-a_{n-1}x_n
+b_0u.
\]

Damit lassen sich \(A_R,B_R,C_R,D\) direkt ablesen.

---

## 4.2 Vorzeichenregel

Die Differentialgleichung wird zuerst in die Form

\[
y^{(n)}
+
a_{n-1}y^{(n-1)}
+\dots+
a_0y
=
b_0u
\]

gebracht.

In der letzten Zeile von \(A_R\) stehen dann die **negativen** Koeffizienten:

\[
[-a_0,\,-a_1,\dots,-a_{n-1}].
\]

Beispiel:

\[
\ddot y-3\dot y+2y=u.
\]

Hier:

\[
a_1=-3,
\qquad
a_0=2.
\]

Daher:

\[
[-a_0,-a_1]=[-2,3].
\]

---

## 4.3 Kontrollmöglichkeiten

1. Aus \(A_R\) wieder die DGL aufstellen.
2. Das charakteristische Polynom prüfen:

\[
\det(\lambda I-A_R)
=
\lambda^n+a_{n-1}\lambda^{n-1}+\dots+a_0.
\]

3. Dimensionen prüfen:

\[
A_R\in\mathbb R^{n\times n},
\quad
B_R\in\mathbb R^{n\times1},
\quad
C_R\in\mathbb R^{1\times n}.
\]

---

# 5. Aufgabe 1a – Regelungsnormalform aus einer DGL zweiter Ordnung

## Gegeben

\[
\ddot y(t)-3\dot y(t)+2y(t)=u(t).
\]

## 5.1 Koeffizienten identifizieren

Vergleich mit

\[
\ddot y+a_1\dot y+a_0y=b_0u
\]

liefert

\[
a_1=-3,
\qquad
a_0=2,
\qquad
b_0=1.
\]

## 5.2 Zustände

\[
x_1=y,
\qquad
x_2=\dot y.
\]

Daraus:

\[
\dot x_1=x_2.
\]

Aus der DGL:

\[
\ddot y
=
3\dot y-2y+u.
\]

Also:

\[
\dot x_2
=
-2x_1+3x_2+u.
\]

## 5.3 Matrixform

\[
\boxed{
A_R=
\begin{bmatrix}
0&1\\
-2&3
\end{bmatrix}
}
\]

\[
\boxed{
B_R=
\begin{bmatrix}
0\\
1
\end{bmatrix}
}
\]

\[
\boxed{
C_R=
\begin{bmatrix}
1&0
\end{bmatrix}
}
\]

\[
\boxed{D=0}.
\]

Die handschriftliche Rechnung auf PDF-S. 30–31 ist vollständig und korrekt.

---

# 6. Aufgabe 1b – Regelungsnormalform dritter Ordnung

## Gegeben

\[
y^{(3)}(t)+4\ddot y(t)+5\dot y(t)+2y(t)=u(t).
\]

## 6.1 Koeffizienten

\[
a_2=4,
\qquad
a_1=5,
\qquad
a_0=2,
\qquad
b_0=1.
\]

## 6.2 Zustände

\[
x_1=y,
\qquad
x_2=\dot y,
\qquad
x_3=\ddot y.
\]

Dann:

\[
\dot x_1=x_2,
\qquad
\dot x_2=x_3.
\]

Aus der DGL:

\[
y^{(3)}
=
-2y-5\dot y-4\ddot y+u.
\]

Somit:

\[
\dot x_3
=
-2x_1-5x_2-4x_3+u.
\]

## 6.3 Matrixform

\[
\boxed{
A_R=
\begin{bmatrix}
0&1&0\\
0&0&1\\
-2&-5&-4
\end{bmatrix}
}
\]

\[
\boxed{
B_R=
\begin{bmatrix}
0\\
0\\
1
\end{bmatrix}
}
\]

\[
\boxed{
C_R=
\begin{bmatrix}
1&0&0
\end{bmatrix}
}
\]

\[
\boxed{D=0}.
\]

---

# 7. Aufgabe 1c – bereits vorliegende Begleitmatrix zweiter Ordnung

## Gegeben

\[
A=
\begin{bmatrix}
0&1\\
-8&-6
\end{bmatrix}.
\]

Die Matrix besitzt bereits die Struktur der Regelungsnormalform:

\[
A_R=
\begin{bmatrix}
0&1\\
-a_0&-a_1
\end{bmatrix}.
\]

Daher:

\[
a_0=8,
\qquad
a_1=6.
\]

Die zugehörige skalare DGL lautet unter der offiziellen Standardannahme

\[
\boxed{
\ddot y+6\dot y+8y=u
}.
\]

Offizielle Ergänzung:

\[
\boxed{
B_R=
\begin{bmatrix}
0\\
1
\end{bmatrix},
\qquad
C_R=
\begin{bmatrix}
1&0
\end{bmatrix},
\qquad
D=0
}.
\]

### [UNKLAR] Streng mathematische Einschränkung

Aus der Matrix \(A\) allein lassen sich \(B\), \(C\) und \(D\) nicht eindeutig bestimmen. Die offizielle Lösung unterstellt stillschweigend das standardisierte SISO-System der Regelungsnormalform.

Für die Klausur ist diese offizielle Annahme zu verwenden.

---

# 8. Aufgabe 1d – bereits vorliegende Begleitmatrix dritter Ordnung

## Gegeben

\[
A=
\begin{bmatrix}
0&1&0\\
0&0&1\\
-1&-3&-2
\end{bmatrix}.
\]

Vergleich mit

\[
[-a_0,-a_1,-a_2]
\]

liefert

\[
a_0=1,
\qquad
a_1=3,
\qquad
a_2=2.
\]

Die zugehörige DGL lautet unter der offiziellen Standardannahme

\[
\boxed{
y^{(3)}+2\ddot y+3\dot y+y=u
}.
\]

Offizielle Ergänzung:

\[
\boxed{
B_R=
\begin{bmatrix}
0\\
0\\
1
\end{bmatrix},
\qquad
C_R=
\begin{bmatrix}
1&0&0
\end{bmatrix},
\qquad
D=0
}.
\]

Auch hier gilt: \(B,C,D\) sind nicht aus \(A\) allein ableitbar, sondern folgen aus der beabsichtigten Standardform.

---

# 9. Laplace-Transformation: allgemeines Schema

## 9.1 Direkte Tabellenform

Zuerst prüfen, ob die Funktion direkt in der Äquivalenztabelle steht.

Wichtige Paare:

\[
1
\longleftrightarrow
\frac1s,
\]

\[
t^n
\longleftrightarrow
\frac{n!}{s^{n+1}},
\]

\[
e^{-at}
\longleftrightarrow
\frac1{s+a},
\]

\[
t^ne^{-at}
\longleftrightarrow
\frac{n!}{(s+a)^{n+1}},
\]

\[
\sin(\omega t)
\longleftrightarrow
\frac{\omega}{s^2+\omega^2},
\]

\[
\cos(\omega t)
\longleftrightarrow
\frac{s}{s^2+\omega^2}.
\]

---

## 9.2 Exponentialfaktor

Ist

\[
f(t)=e^{at}g(t),
\]

und

\[
G(s)=\mathcal L\{g(t)\},
\]

dann

\[
\boxed{
\mathcal L\{e^{at}g(t)\}=G(s-a)
}.
\]

Für \(e^{-at}\):

\[
\boxed{
\mathcal L\{e^{-at}g(t)\}=G(s+a)
}.
\]

---

## 9.3 Potenzen trigonometrischer Funktionen

Bei \(\sin^2t\), \(\cos^2t\) oder Produkten zuerst trigonometrische Identitäten verwenden.

Beispiel:

\[
\sin^2t
=
\frac{1-\cos(2t)}{2}.
\]

Erst danach einzeln transformieren.

---

# 10. Aufgabe 2a – \(\cos(\omega t)\)

Direktes Tabellenpaar:

\[
\boxed{
\mathcal L\{\cos(\omega t)\}
=
\frac{s}{s^2+\omega^2}
}.
\]

Die Mitschrift auf PDF-S. 33 verwendet korrekt Tabelle 3.2 des Skripts.

---

# 11. Aufgabe 2b – \(2te^{-4t}\)

## 11.1 Ausgangspaar

\[
\mathcal L\{t\}
=
\frac1{s^2}.
\]

Mit Faktor 2:

\[
\mathcal L\{2t\}
=
\frac2{s^2}.
\]

## 11.2 Exponentialverschiebung

Wegen \(e^{-4t}\) wird \(s\) durch \(s+4\) ersetzt:

\[
\boxed{
\mathcal L\{2te^{-4t}\}
=
\frac2{(s+4)^2}
}.
\]

Die farbigen Markierungen auf PDF-S. 33 trennen korrekt den Exponentialfaktor und die Grundfunktion.

---

# 12. Aufgabe 2c – \(e^{-3t}\sin(\omega t)\)

Aus

\[
\sin(\omega t)
\longleftrightarrow
\frac{\omega}{s^2+\omega^2}
\]

und der Verschiebung \(s\mapsto s+3\) folgt

\[
\boxed{
\mathcal L\{e^{-3t}\sin(\omega t)\}
=
\frac{\omega}{(s+3)^2+\omega^2}
}.
\]

---

# 13. Aufgabe 2d – \(t^3\)

Allgemein:

\[
\mathcal L\{t^n\}
=
\frac{n!}{s^{n+1}}.
\]

Mit \(n=3\):

\[
\boxed{
\mathcal L\{t^3\}
=
\frac{3!}{s^4}
=
\frac6{s^4}
}.
\]

---

# 14. Aufgabe 2e – \(\sin^2t\)

## 14.1 Trigonometrische Umformung

\[
\sin^2t
=
\frac{1-\cos(2t)}{2}.
\]

## 14.2 Transformieren

\[
\mathcal L\{\sin^2t\}
=
\frac12\mathcal L\{1\}
-
\frac12\mathcal L\{\cos(2t)\}.
\]

\[
=
\frac1{2s}
-
\frac12\frac{s}{s^2+4}.
\]

Auf gemeinsamen Nenner bringen:

\[
\frac1{2s}
-
\frac{s}{2(s^2+4)}
=
\frac{s^2+4-s^2}{2s(s^2+4)}.
\]

\[
=
\frac4{2s(s^2+4)}.
\]

Ergebnis:

\[
\boxed{
\mathcal L\{\sin^2t\}
=
\frac2{s(s^2+4)}
=
\frac2{s^3+4s}
}.
\]

---

# 15. Aufgabe 2f – Rücktransformation von \(1/(s-8)\)

Grundpaar:

\[
e^{at}
\longleftrightarrow
\frac1{s-a}.
\]

Mit \(a=8\):

\[
\boxed{
\mathcal L^{-1}
\left\{
\frac1{s-8}
\right\}
=
e^{8t}
}.
\]

---

# 16. Aufgabe 2g – Rücktransformation von \(1/s^4\)

Aus

\[
t^n
\longleftrightarrow
\frac{n!}{s^{n+1}}
\]

folgt bei \(n+1=4\):

\[
n=3.
\]

Da

\[
t^3
\longleftrightarrow
\frac6{s^4},
\]

muss durch 6 geteilt werden:

\[
\boxed{
\mathcal L^{-1}
\left\{
\frac1{s^4}
\right\}
=
\frac{t^3}{6}
}.
\]

---

# 17. Aufgabe 2h – verschobener Kosinus

## Gegeben

\[
\hat f(s)
=
\frac{s-4}{(s-4)^2+4}.
\]

Vergleich mit

\[
e^{at}\cos(\omega t)
\longleftrightarrow
\frac{s-a}{(s-a)^2+\omega^2}
\]

liefert

\[
a=4,
\qquad
\omega^2=4
\Rightarrow
\omega=2.
\]

Damit:

\[
\boxed{
f(t)=e^{4t}\cos(2t)
}.
\]

---

# 18. Aufgabe 2i – Rücktransformation von \(1/(s^2+25)\)

Grundpaar:

\[
\sin(\omega t)
\longleftrightarrow
\frac{\omega}{s^2+\omega^2}.
\]

Hier:

\[
\omega=5.
\]

Im Zähler fehlt der Faktor 5:

\[
\frac1{s^2+25}
=
\frac15
\frac5{s^2+25}.
\]

Daher:

\[
\boxed{
\mathcal L^{-1}
\left\{
\frac1{s^2+25}
\right\}
=
\frac15\sin(5t)
}.
\]

---

# 19. Systemantwort im Bildbereich: allgemeines Schema

## Gegeben

- Übertragungsfunktion \(G(s)\)
- Sprungamplitude \(F_{\mathrm{ex}}\)

## Vorgehen

1. Eingang transformieren:

\[
U(s)=\frac{F_{\mathrm{ex}}}{s}.
\]

2. Systemantwort bilden:

\[
Y(s)=G(s)U(s).
\]

3. Kürzen, aber keine dynamisch relevanten Faktoren unkritisch entfernen.

Ergebnis:

\[
\boxed{
Y(s)=G(s)\frac{F_{\mathrm{ex}}}{s}
}.
\]

---

# 20. Aufgabe 3a – Bildbereich eines PT1-ähnlichen Systems

## Gegeben

\[
G(s)=\frac1{2s+1},
\qquad
F_{\mathrm{ex}}=0{,}1.
\]

## Eingang

\[
U(s)=\frac{0{,}1}{s}.
\]

## Ausgang

\[
Y(s)
=
G(s)U(s).
\]

\[
Y(s)
=
\frac1{2s+1}
\frac{0{,}1}{s}.
\]

Ergebnis:

\[
\boxed{
Y(s)
=
\frac{0{,}1}{s(2s+1)}
}.
\]

Die Mitschrift auf PDF-S. 35 ist vollständig und korrekt.

---

# 21. Aufgabe 3b – Kürzung des Sprungfaktors mit einem Zähler-\(s\)

## Gegeben

\[
G(s)
=
\frac{s}{s^2+\frac{\pi}{4}},
\qquad
F_{\mathrm{ex}}
=
\frac{\pi}{2}.
\]

## Eingang

\[
U(s)
=
\frac{\pi}{2s}.
\]

## Ausgang

\[
Y(s)
=
\frac{s}{s^2+\frac{\pi}{4}}
\frac{\pi}{2s}.
\]

Der Faktor \(s\) kürzt sich:

\[
Y(s)
=
\frac{\pi}{2}
\frac1{s^2+\frac{\pi}{4}}.
\]

Ergebnis:

\[
\boxed{
Y(s)
=
\frac{\pi}{2\left(s^2+\frac{\pi}{4}\right)}
}.
\]

Die handschriftliche Rechnung auf PDF-S. 35 ist korrekt.

---

# 22. Aufgabe 3c – allgemeine rationale Übertragungsfunktion

## Gegeben

\[
G(s)
=
\frac{C}{As^2+Bs-1},
\qquad
F_{\mathrm{ex}}=D.
\]

## Eingang

\[
U(s)=\frac Ds.
\]

## Ausgang

\[
Y(s)
=
\frac{C}{As^2+Bs-1}
\frac Ds.
\]

Ergebnis:

\[
\boxed{
Y(s)
=
\frac{CD}{s(As^2+Bs-1)}
}.
\]

Eine Rücktransformation ist in Aufgabe 3 nicht verlangt.

---

# 23. Sprungantwort im Zeitbereich: allgemeines Schema

1. Sprung im Bildbereich bilden:

\[
Y(s)=G(s)\frac{F_{\mathrm{ex}}}{s}.
\]

2. \(Y(s)\) vereinfachen.

3. Falls nötig Partialbruchzerlegung durchführen.

4. Jeden Summanden mit der Laplace-Tabelle rücktransformieren.

5. Anfangs- und Endwert prüfen.

---

# 24. Aufgabe 4a – Partialbruchzerlegung und Rücktransformation

## 24.1 Bildfunktion

Aus Aufgabe 3a:

\[
Y(s)
=
\frac{0{,}1}{s(2s+1)}.
\]

Ansatz:

\[
\frac{0{,}1}{s(2s+1)}
=
\frac As+\frac B{2s+1}.
\]

Multiplikation mit \(s(2s+1)\):

\[
0{,}1
=
A(2s+1)+Bs.
\]

Ausmultiplizieren:

\[
0{,}1
=
(2A+B)s+A.
\]

Koeffizientenvergleich:

\[
A=0{,}1,
\]

\[
2A+B=0.
\]

Damit:

\[
B=-0{,}2.
\]

Also:

\[
Y(s)
=
\frac{0{,}1}{s}
-
\frac{0{,}2}{2s+1}.
\]

Den zweiten Bruch normieren:

\[
\frac{-0{,}2}{2s+1}
=
-\frac{0{,}1}{s+\frac12}.
\]

Somit:

\[
Y(s)
=
\frac{0{,}1}{s}
-
\frac{0{,}1}{s+\frac12}.
\]

---

## 24.2 Rücktransformation

\[
\mathcal L^{-1}
\left\{
\frac1s
\right\}
=
1,
\]

\[
\mathcal L^{-1}
\left\{
\frac1{s+a}
\right\}
=
e^{-at}.
\]

Daher:

\[
y(t)
=
0{,}1
-
0{,}1e^{-\frac12t}.
\]

Ergebnis:

\[
\boxed{
y(t)
=
0{,}1\left(1-e^{-0{,}5t}\right)
}.
\]

Die handschriftliche Rechnung auf PDF-S. 36–37 ist vollständig und korrekt.

---

## 24.3 Plausibilitätskontrolle

Anfangswert:

\[
y(0)
=
0{,}1(1-1)
=
0.
\]

Endwert:

\[
\lim_{t\to\infty}y(t)
=
0{,}1.
\]

Das passt zur statischen Verstärkung

\[
G(0)=1
\]

und zur Sprungamplitude \(0{,}1\).

Zeitkonstante:

\[
2s+1
=
1+2s
\Rightarrow
T=2.
\]

Daher:

\[
e^{-t/T}=e^{-t/2}.
\]

---

# 25. Aufgabe 4b – sinusförmige Sprungantwort

Aus Aufgabe 3b:

\[
Y(s)
=
\frac{\pi}{2}
\frac1{s^2+\frac{\pi}{4}}.
\]

Setze

\[
a^2=\frac{\pi}{4}.
\]

Dann:

\[
a=\sqrt{\frac{\pi}{4}}
=
\frac{\sqrt\pi}{2}.
\]

Grundpaar:

\[
\mathcal L^{-1}
\left\{
\frac1{s^2+a^2}
\right\}
=
\frac1a\sin(at).
\]

Damit:

\[
y(t)
=
\frac{\pi}{2}
\frac1a
\sin(at).
\]

Einsetzen von \(a=\sqrt\pi/2\):

\[
\frac{\pi/2}{\sqrt\pi/2}
=
\sqrt\pi.
\]

Ergebnis:

\[
\boxed{
y(t)
=
\sqrt\pi
\sin\left(
\frac{\sqrt\pi}{2}t
\right)
}
\]

gleichwertig:

\[
\boxed{
y(t)
=
\sqrt\pi
\sin\left(
\sqrt{\frac{\pi}{4}}\,t
\right)
}.
\]

---

## 25.1 Interpretation

Die Pole liegen bei

\[
s_{1,2}
=
\pm j\frac{\sqrt\pi}{2}.
\]

Sie besitzen keinen negativen Realteil. Daher klingt die Antwort nicht ab, sondern schwingt dauerhaft.

Kontrolle bei \(t=0\):

\[
y(0)=0.
\]

---

# 26. Qualitätsprüfung der Mitschrift

## Vollständig und fachlich bestätigt

- allgemeine Struktur der Regelungsnormalform auf PDF-S. 29
- Sprunganregung \(U(s)=F_{\mathrm{ex}}/s\) auf PDF-S. 30
- Aufgabe 1a auf PDF-S. 30–31
- Aufgabe 2a und 2b auf PDF-S. 33
- Aufgabe 3a und 3b auf PDF-S. 35
- Aufgabe 4a auf PDF-S. 36–37

## Nur als offizielle Endergebnisse vorhanden

Die Mitschrift enthält keine vollständigen handschriftlichen Rechenwege für:

- Aufgabe 1b–d
- Aufgabe 2c–i
- Aufgabe 3c
- Aufgabe 4b

Diese Rechenwege wurden oben vollständig aus den Aufgabenstellungen, den offiziellen Ergebnissen und den Skriptregeln hergeleitet.

## Nachgewiesene begriffliche Verwechslung

Auf PDF-S. 29 wird

\[
\mathcal L\{e^{at}f(t)\}=F(s-a)
\]

als „Verschiebungssatz“ überschrieben. Im offiziellen Skript heißt diese Regel **Dämpfungssatz**. Der eigentliche Verschiebungssatz betrifft eine Zeitverschiebung.

## Unvollständige Aufgabenangabe

Bei Aufgabe 1c und 1d ist nur \(A\) gegeben. \(B,C,D\) sind daraus nicht eindeutig bestimmbar. Die offizielle Lösung ergänzt stillschweigend die Standardwerte der Regelungsnormalform.

---

# 27. Typische Fehler in Tutorium 03

1. Die letzte Zeile der Regelungsnormalform ohne Vorzeichenwechsel übernehmen.
2. Zustandsreihenfolge \(y,\dot y,\ddot y,\dots\) vertauschen.
3. Bei einem Sprung den Faktor \(1/s\) vergessen.
4. \(Y=GU\) trotz nicht verschwindender Anfangsbedingungen ohne Zusatzterm verwenden.
5. Dämpfungssatz und Zeitverschiebungssatz verwechseln.
6. Bei \(e^{-at}\) fälschlich \(s-a\) statt \(s+a\) einsetzen.
7. Sinus und Kosinus anhand des Nenners statt des Zählers unterscheiden.
8. Bei \(t^n\) den Faktor \(n!\) vergessen.
9. Bei der Rücktransformation fehlende Zählerfaktoren nicht ausgleichen.
10. \(\sin^2t\) direkt transformieren, ohne die Doppelwinkelformel zu verwenden.
11. Partialbruchansatz mit falschen Nennern wählen.
12. Den Faktor vor \(s\) nicht normieren, bevor rücktransformiert wird.
13. Bei \(1/(s^2+a^2)\) den Faktor \(1/a\) vergessen.
14. Keine Anfangs- und Endwertkontrolle durchführen.

---

# 28. Klausurstrategie

## 28.1 Regelungsnormalform

1. DGL nach der höchsten Ableitung ordnen.
2. Koeffizienten \(a_0,\dots,a_{n-1}\) markieren.
3. Zustände als Ableitungskette definieren.
4. Schiebestruktur der oberen Matrixzeilen eintragen.
5. Letzte Zeile mit negativen Koeffizienten eintragen.
6. \(B_R,C_R,D\) ergänzen.
7. DGL aus der Matrix zurücklesen und kontrollieren.

## 28.2 Direkte Laplace-Transformation

1. Funktion in bekannte Grundbausteine zerlegen.
2. Tabelle prüfen.
3. Exponentialfaktor über \(s\)-Verschiebung behandeln.
4. Trigonometrische Potenzen vorher umformen.
5. Konstanten nicht verlieren.

## 28.3 Sprungantwort

1. Sofort hinschreiben:

\[
U(s)=\frac{F_{\mathrm{ex}}}{s}.
\]

2. Multiplizieren:

\[
Y(s)=G(s)U(s).
\]

3. Kürzen und Nenner faktorisieren.
4. Partialbruchzerlegung.
5. Rücktransformation.
6. \(y(0)\) und \(y(\infty)\) prüfen.

---

# 29. NotebookLM-Verifikation

--- NOTEBOOKLM-PROMPT ---

Prüfe ausschließlich anhand der hochgeladenen offiziellen Regelungstechnik-Unterlagen zwei Unklarheiten aus „Tutorium 03 – Regelungsnormalform und Übertragungsfunktionen“:

1. In der Mitschrift steht
\[
\mathcal L\{e^{at}f(t)\}=F(s-a)
\]
unter der Überschrift „Verschiebungssatz“. Wie heißt diese Regel im offiziellen Skript? Stelle sie dem eigentlichen Zeitverschiebungssatz gegenüber und belege beides mit Dokumentname und genauer Seite.

2. In Aufgabe 1c und 1d ist nur die Matrix \(A\) gegeben. Die Musterlösung ergänzt trotzdem \(B_R,C_R\) und implizit \(D=0\). Wird in den offiziellen Quellen ausdrücklich erklärt, dass bei solchen Aufgaben automatisch die Standardwerte der Regelungsnormalform anzunehmen sind? Falls nicht, benenne die mathematische Mehrdeutigkeit.

Antworte kurz. Trenne direkte Quellenaussagen von eigener Schlussfolgerung. Erfinde keine Begründung.

--- ENDE ---

---

# 30. Kompaktformelsammlung Tutorium 03

## Regelungsnormalform

\[
A_R=
\begin{bmatrix}
0&1&0&\cdots&0\\
0&0&1&\cdots&0\\
\vdots&&&\ddots&\vdots\\
-a_0&-a_1&-a_2&\cdots&-a_{n-1}
\end{bmatrix},
\]

\[
B_R=
\begin{bmatrix}
0\\\vdots\\0\\b_0
\end{bmatrix},
\qquad
C_R=
\begin{bmatrix}
1&0&\cdots&0
\end{bmatrix},
\qquad
D=0.
\]

## Übertragungsfunktion

\[
G(s)=\frac{Y(s)}{U(s)}
\qquad
(x_0=0).
\]

## Sprung

\[
u(t)=F_{\mathrm{ex}}\eta(t)
\]

\[
U(s)=\frac{F_{\mathrm{ex}}}{s}.
\]

## Systemantwort

\[
Y(s)=G(s)U(s).
\]

## Potenz

\[
t^n
\longleftrightarrow
\frac{n!}{s^{n+1}}.
\]

## Exponentialfaktor

\[
e^{at}f(t)
\longleftrightarrow
F(s-a).
\]

## Zeitverschiebung

\[
f(t-a)\eta(t-a)
\longleftrightarrow
e^{-as}F(s).
\]

## Sinus und Kosinus

\[
\sin(\omega t)
\longleftrightarrow
\frac{\omega}{s^2+\omega^2},
\]

\[
\cos(\omega t)
\longleftrightarrow
\frac{s}{s^2+\omega^2}.
\]

## Rücktransformation

\[
\frac1{s+a}
\longleftrightarrow
e^{-at},
\]

\[
\frac1{s^2+a^2}
\longleftrightarrow
\frac1a\sin(at).
\]

---

# Tutorium 04 – Darstellungen im Frequenzbereich

## 1. Quellen und Seitenbereich

### Primärquellen

1. **RT-Tutorien-Mitschrift.pdf**, PDF-Seiten 39–57
   - S. 39: Theoriefragen, Aufgabe 1 und offizielle Endergebnisse
   - S. 40–41: Frequenzgang, Betrag/Phase, dB-Rechnung, Reihenschaltung, Ortskurve sowie Pole und Nullstellen
   - S. 42: vollständige Rechnungen zu Aufgabe 1a und 1b
   - S. 43–47: Aufgabe 2 und handschriftliche Herleitungen für I-Glied und PT1-Glied
   - S. 48: offizielle Bode-Gesamtlösung zu Aufgabe 2
   - S. 49–50: Aufgabe 3 und offizielle Bode-Gesamtlösung
   - S. 51–54: Aufgabe 4 sowie handschriftliche Rechnungen zu 4a und 4b
   - S. 55–57: offizielle Ortskurven und Pol-Nullstellen-Diagramme zu 4a–g
   - Tutorium 05 beginnt auf PDF-Seite 58.

2. **Regelungstechnik_Tutorium_komplett.pdf**, PDF-Seiten 16–27  
   Tutorium 04, Blattseiten 1/12–12/12, offizielle Aufgaben und Diagrammlösungen.

3. **skript.pdf**
   - PDF-S. 61: Definition 3.15 „E/A-Verhalten“ und Theorem 3.16 „Betrag und Phase“
   - PDF-S. 63: Definition 3.18 „Frequenzgang“ und Definition 3.19 „Bode-Diagramm“
   - PDF-S. 64–65: Betrag und Phase des PT1-/Tiefpass-Beispiels
   - PDF-S. 65–67: Grenzfrequenz, Dezibel und Reihenschaltung
   - PDF-S. 69–71: Ortskurve
   - PDF-S. 71–73: Pole, Nullstellen und Pol-Nullstellen-Diagramm

---

# 2. Frequenzgang, Betrag und Phase

## 2.1 Vom \(s\)-Bereich zum Frequenzgang

Für eine Übertragungsfunktion

\[
G(s)
\]

wird der Frequenzgang durch Einsetzen

\[
\boxed{s=j\omega}
\]

gebildet:

\[
\boxed{G(j\omega)}.
\]

Dabei gilt:

\[
j^2=-1.
\]

Der Frequenzgang ist komplex und lässt sich schreiben als

\[
G(j\omega)
=
\operatorname{Re}\{G(j\omega)\}
+
j\operatorname{Im}\{G(j\omega)\}.
\]

Oder in Polarform:

\[
\boxed{
G(j\omega)
=
|G(j\omega)|e^{j\varphi(\omega)}
}.
\]

---

## 2.2 Betrag

Für

\[
z=a+jb
\]

gilt

\[
\boxed{|z|=\sqrt{a^2+b^2}}.
\]

Daher:

\[
\boxed{
|G(j\omega)|
=
\sqrt{
\operatorname{Re}\{G(j\omega)\}^2+
\operatorname{Im}\{G(j\omega)\}^2
}
}.
\]

Wichtige Betragsregeln:

\[
|z_1z_2|
=
|z_1||z_2|,
\]

\[
\left|
\frac{z_1}{z_2}
\right|
=
\frac{|z_1|}{|z_2|}.
\]

---

## 2.3 Phase

\[
\boxed{
\varphi(\omega)
=
\arg G(j\omega)
}.
\]

Formal:

\[
\varphi(\omega)
=
\operatorname{atan2}
\left(
\operatorname{Im}G(j\omega),
\operatorname{Re}G(j\omega)
\right).
\]

Die einfache Formel

\[
\arctan\left(\frac{\operatorname{Im}G}{\operatorname{Re}G}\right)
\]

reicht nur, wenn der richtige Quadrant zusätzlich berücksichtigt wird.

---

# 3. Theoriefragen

## 3.1 Wie erkennt man Resonanzen oder starke Peaks?

Eine Resonanz erscheint im Amplitudengang als deutliches lokales Maximum von

\[
|G(j\omega)|.
\]

Je näher ein schwach gedämpftes komplexes Polpaar an der imaginären Achse liegt, desto ausgeprägter ist typischerweise der Peak.

Im Extremfall liegt ein Pol direkt auf der imaginären Achse. Dann kann der Betrag bei der zugehörigen Frequenz gegen unendlich gehen.

Beispiel aus Aufgabe 1b:

\[
G(s)
=
\frac{s}{s^2+\frac{\pi}{4}}.
\]

Die Pole liegen bei

\[
s_{1,2}
=
\pm j\sqrt{\frac{\pi}{4}}
=
\pm j\frac{\sqrt\pi}{2}.
\]

Daher wird der Nenner für

\[
\omega
=
\frac{\sqrt\pi}{2}
\]

null und der ideale Betrag besitzt dort eine Polstelle.

---

## 3.2 Warum wird mit \(20\log_{10}\) und nicht mit \(10\log_{10}\) gerechnet?

Für Leistungen gilt die Bel-/Dezibeldefinition

\[
L_P
=
10\log_{10}
\left(
\frac{P_2}{P_1}
\right).
\]

Leistung ist bei gleicher Impedanz proportional zum Quadrat einer Amplitude:

\[
P\propto A^2.
\]

Daher:

\[
10\log_{10}
\left(
\frac{A_2^2}{A_1^2}
\right)
=
20\log_{10}
\left(
\frac{A_2}{A_1}
\right).
\]

Für den Betragsgang einer Übertragungsfunktion gilt deshalb:

\[
\boxed{
L(\omega)
=
20\log_{10}|G(j\omega)|
}.
\]

Quelle: `skript.pdf`, PDF-S. 66, Definition 3.24.

---

## 3.3 Warum können bei Produkten die dB-Werte addiert werden?

Bei einer Reihenschaltung:

\[
G(j\omega)
=
G_1(j\omega)G_2(j\omega).
\]

Dann:

\[
|G|
=
|G_1||G_2|.
\]

In dB:

\[
20\log_{10}|G|
=
20\log_{10}
\left(
|G_1||G_2|
\right).
\]

Mit

\[
\log(ab)=\log a+\log b
\]

folgt:

\[
\boxed{
L(\omega)
=
L_1(\omega)+L_2(\omega)
}.
\]

Das ist der zentrale Grund, weshalb Bode-Diagramme für faktorisierte Übertragungsfunktionen so effizient sind.

---

## 3.4 Was ist die Eckfrequenz?

Bei einem Faktor erster Ordnung

\[
1+Ts
\]

oder

\[
\frac1{1+Ts}
\]

ist die charakteristische Eckfrequenz

\[
\boxed{
\omega_E=\frac1T
}.
\]

Bei dieser Frequenz gilt

\[
T\omega_E=1.
\]

Für ein PT1-Glied:

\[
\left|
\frac1{1+j}
\right|
=
\frac1{\sqrt2},
\]

also

\[
20\log_{10}\frac1{\sqrt2}
\approx
-3.01\,\mathrm{dB}
\]

und

\[
\varphi(\omega_E)=-45^\circ.
\]

### Präzise Begriffstrennung

- **Eckfrequenz:** Stelle, an der sich die asymptotische Steigung ändert.
- **Grenzfrequenz:** häufig die \(-3\,\mathrm{dB}\)-Stelle.

Für ein PT1-Glied fallen beide zusammen. Bei I- und D-Gliedern gibt es keinen Knick; dort ist \(\omega=1/T\) nur die charakteristische \(0\,\mathrm{dB}\)-Frequenz.

---

## 3.5 Warum addieren sich Phasen bei Reihenschaltung?

Schreibe:

\[
G_1
=
|G_1|e^{j\varphi_1},
\qquad
G_2
=
|G_2|e^{j\varphi_2}.
\]

Dann:

\[
G_1G_2
=
|G_1||G_2|
e^{j(\varphi_1+\varphi_2)}.
\]

Somit:

\[
\boxed{
\arg(G_1G_2)
=
\arg G_1+\arg G_2
}.
\]

---

## 3.6 Was ist die Ortskurve?

Die Ortskurve ist die Menge der komplexen Werte

\[
\boxed{
\{G(j\omega)\mid \omega\ge0\}
}
\]

in der komplexen Ebene.

Sie kombiniert Betrag und Phase in einer einzigen Darstellung:

- Abstand vom Ursprung: Betrag,
- Winkel zur positiven reellen Achse: Phase.

Im Tutorium wird nur der positive Frequenzbereich gezeichnet. Für Systeme mit reellen Koeffizienten ist der negative Frequenzbereich die Spiegelung an der reellen Achse.

---

## 3.7 Warum sind \(\omega\to0\) und \(\omega\to\infty\) wichtig?

Diese Grenzfälle liefern Start- und Endpunkt der Ortskurve:

\[
G(j0)
\]

und

\[
\lim_{\omega\to\infty}G(j\omega).
\]

Damit ist die grobe Lage der Kurve oft bereits festgelegt.

Zusätzliche charakteristische Frequenzen wie

\[
\omega=\frac1T
\]

liefern Zwischenpunkte und die Durchlaufrichtung.

---

## 3.8 Unterschied zwischen Polen und Nullstellen

Für

\[
G(s)=\frac{Z(s)}{N(s)}
\]

gelten:

Nullstellen:

\[
Z(s_0)=0.
\]

Pole:

\[
N(s_p)=0.
\]

Interpretation:

- Nullstellen können bestimmte Frequenzanteile abschwächen oder vollständig unterdrücken und prägen die Form des Frequenzgangs.
- Pole bestimmen wesentlich die Eigenmoden, die Zeitdynamik und die Stabilität.

Im Pol-Nullstellen-Diagramm:

- Pole: \(\times\)
- Nullstellen: \(\circ\)

Quelle: `skript.pdf`, PDF-S. 71–73, Definitionen 3.32 und 3.34.

---

## 3.9 Physikalische Bedeutung eines Pols bei \(s=-a\), \(a>0\)

Ein Pol

\[
s=-a
\]

erzeugt im Zeitbereich einen Anteil

\[
e^{-at}.
\]

Dieser klingt exponentiell ab.

Die Zeitkonstante ist

\[
\boxed{
T=\frac1a
}.
\]

Nach der Zeit \(T\) ist der Anteil auf

\[
e^{-1}\approx36.8\%
\]

des Anfangswerts gefallen.

---

# 4. Aufgabe 1 – Amplitudenverhalten

## 4.1 Allgemeines Schema

1. \(s=j\omega\) einsetzen.
2. Real- und Imaginärteil bestimmen.
3. Betrag bilden:

\[
|G(j\omega)|
=
\sqrt{(\operatorname{Re}G)^2+(\operatorname{Im}G)^2}.
\]

4. Grenzfälle und Singularitäten prüfen.
5. Erst danach graphisch skizzieren.

---

# 5. Aufgabe 1a – PT1-Glied

## Gegeben

\[
G(s)
=
\frac1{2s+1}.
\]

## Einsetzen von \(s=j\omega\)

\[
G(j\omega)
=
\frac1{1+j2\omega}.
\]

Der Nennerbetrag lautet:

\[
|1+j2\omega|
=
\sqrt{1+(2\omega)^2}.
\]

Damit:

\[
\boxed{
|G(j\omega)|
=
\frac1{\sqrt{1+4\omega^2}}
}.
\]

## Grenzfälle

\[
|G(j0)|=1.
\]

\[
\lim_{\omega\to\infty}|G(j\omega)|=0.
\]

Der Betrag fällt monoton.

Eckfrequenz:

\[
2\omega_E=1
\quad\Rightarrow\quad
\boxed{\omega_E=0.5\,\mathrm{s^{-1}}}.
\]

Dort:

\[
|G(j\omega_E)|
=
\frac1{\sqrt2}.
\]

Die handschriftliche Herleitung auf `RT-Tutorien-Mitschrift.pdf`, PDF-S. 42, ist korrekt.

---

# 6. Aufgabe 1b – ungedämpftes System mit Resonanzpolen

## Gegeben

\[
G(s)
=
\frac{s}{s^2+\frac{\pi}{4}}.
\]

## Einsetzen

\[
G(j\omega)
=
\frac{j\omega}{(j\omega)^2+\frac{\pi}{4}}.
\]

Da

\[
(j\omega)^2=-\omega^2,
\]

folgt:

\[
G(j\omega)
=
\frac{j\omega}
{\frac{\pi}{4}-\omega^2}.
\]

Der Nenner ist reell. Daher:

\[
\boxed{
|G(j\omega)|
=
\left|
\frac{\omega}
{\frac{\pi}{4}-\omega^2}
\right|
}.
\]

## Charakteristische Punkte

\[
|G(j0)|=0.
\]

Der Nenner verschwindet bei

\[
\omega_R
=
\sqrt{\frac{\pi}{4}}
=
\frac{\sqrt\pi}{2}
\approx0.886.
\]

Somit:

\[
\lim_{\omega\to\omega_R}|G(j\omega)|
=
\infty.
\]

Für hohe Frequenzen:

\[
|G(j\omega)|
\sim
\frac1{\omega}
\to0.
\]

### Interpretation

Das System besitzt Pole direkt auf der imaginären Achse und keine Dämpfung. Der unendliche Peak ist ein Idealmodell; reale Systeme besitzen typischerweise Dämpfung und daher einen endlichen Resonanzpeak.

Die Mitschrift auf PDF-S. 42 erkennt korrekt:

- Betrag bei \(\omega=0\): 0,
- Singularität bei \(\omega=\sqrt{\pi}/2\),
- Betrag gegen 0 für \(\omega\to\infty\).

---

# 7. Aufgabe 1c – allgemeines System zweiter Ordnung

## Gegeben

\[
G(s)
=
\frac{C}{As^2+Bs-1}.
\]

## Einsetzen

\[
G(j\omega)
=
\frac{C}
{-A\omega^2+jB\omega-1}.
\]

Zusammenfassen:

\[
G(j\omega)
=
\frac{C}
{-(A\omega^2+1)+jB\omega}.
\]

Der Nennerbetrag ist:

\[
\sqrt{
(A\omega^2+1)^2+B^2\omega^2
}.
\]

Ausmultiplizieren:

\[
(A\omega^2+1)^2+B^2\omega^2
=
A^2\omega^4
+
(2A+B^2)\omega^2
+
1.
\]

Damit:

\[
\boxed{
|G(j\omega)|
=
\frac{|C|}
{\sqrt{
A^2\omega^4+
(B^2+2A)\omega^2+
1
}}
}.
\]

### [KORRIGIERT]

Die offizielle Lösung schreibt im Zähler \(C\) statt \(|C|\). Das ist nur unter der stillschweigenden Annahme

\[
C\ge0
\]

korrekt. Ein Betrag kann nicht negativ sein.

---

# 8. Aufgabe 2 – Bode-Diagramme einzelner Glieder

## 8.1 PT1-Glied

\[
G(s)=\frac1{1+Ts}.
\]

Betrag:

\[
|G(j\omega)|
=
\frac1{\sqrt{1+(T\omega)^2}}.
\]

dB:

\[
\boxed{
L(\omega)
=
-10\log_{10}
\left(
1+(T\omega)^2
\right)
}.
\]

Phase:

\[
\boxed{
\varphi(\omega)
=
-\arctan(T\omega)
}.
\]

Eckfrequenz:

\[
\boxed{
\omega_E=\frac1T
}.
\]

Asymptoten:

- \(\omega\ll\omega_E\): \(0\,\mathrm{dB}\)
- \(\omega\gg\omega_E\): \(-20\,\mathrm{dB/Dekade}\)

Für die Aufgabe:

\[
T=0.1
\Rightarrow
\omega_E=10,
\]

\[
T=1
\Rightarrow
\omega_E=1.
\]

---

## 8.2 I-Glied

\[
G(s)=\frac1{Ts}.
\]

\[
G(j\omega)
=
-\frac{j}{T\omega}.
\]

Betrag:

\[
\boxed{
|G(j\omega)|
=
\frac1{T\omega}
}.
\]

dB:

\[
\boxed{
L(\omega)
=
-20\log_{10}(T\omega)
}.
\]

Phase:

\[
\boxed{
\varphi=-90^\circ
}.
\]

Steigung:

\[
-20\,\mathrm{dB/Dekade}
\]

über den gesamten Frequenzbereich.

Es gibt keinen Knick. Die charakteristische \(0\,\mathrm{dB}\)-Frequenz ist:

\[
\omega_0=\frac1T.
\]

Für die Aufgabe:

\[
T=0.2
\Rightarrow
\omega_0=5,
\]

\[
T=10
\Rightarrow
\omega_0=0.1.
\]

Die Mitschrift auf PDF-S. 43–45 enthält diese Herleitung weitgehend vollständig.

---

## 8.3 D-Glied

\[
G(s)=Ts.
\]

\[
G(j\omega)=jT\omega.
\]

Betrag:

\[
\boxed{
|G(j\omega)|
=
T\omega
}.
\]

dB:

\[
\boxed{
L(\omega)
=
20\log_{10}(T\omega)
}.
\]

Phase:

\[
\boxed{
\varphi=+90^\circ
}.
\]

Steigung:

\[
+20\,\mathrm{dB/Dekade}.
\]

Auch hier gibt es keinen Knick. Die \(0\,\mathrm{dB}\)-Frequenz ist:

\[
\omega_0=\frac1T.
\]

Für die Aufgabe:

\[
T=1
\Rightarrow
\omega_0=1,
\]

\[
T=10
\Rightarrow
\omega_0=0.1.
\]

---

## 8.4 Nullstelle erster Ordnung / PD-Faktor

\[
G(s)=1+Ts.
\]

Betrag:

\[
\boxed{
|G(j\omega)|
=
\sqrt{1+(T\omega)^2}
}.
\]

dB:

\[
\boxed{
L(\omega)
=
10\log_{10}
\left(
1+(T\omega)^2
\right)
}.
\]

Phase:

\[
\boxed{
\varphi(\omega)
=
\arctan(T\omega)
}.
\]

Eckfrequenz:

\[
\boxed{
\omega_E=\frac1T
}.
\]

Asymptoten:

- unterhalb: \(0\,\mathrm{dB}\)
- oberhalb: \(+20\,\mathrm{dB/Dekade}\)

Für die Aufgabe:

\[
T=0.5
\Rightarrow
\omega_E=2,
\]

\[
T=2
\Rightarrow
\omega_E=0.5.
\]

---

## 8.5 IT1-Glied

\[
G(s)
=
\frac1{T_1s(T_2s+1)}.
\]

Betrag:

\[
\boxed{
|G(j\omega)|
=
\frac1{
T_1\omega
\sqrt{1+(T_2\omega)^2}
}
}.
\]

dB:

\[
\boxed{
L(\omega)
=
-20\log_{10}(T_1\omega)
-
10\log_{10}
\left(
1+(T_2\omega)^2
\right)
}.
\]

Phase:

\[
\boxed{
\varphi(\omega)
=
-90^\circ-\arctan(T_2\omega)
}.
\]

Eckfrequenz des PT1-Anteils:

\[
\boxed{
\omega_E=\frac1{T_2}
}.
\]

Asymptotische Steigung:

- unterhalb der Ecke: \(-20\,\mathrm{dB/Dekade}\)
- oberhalb der Ecke: \(-40\,\mathrm{dB/Dekade}\)

Phase:

- niedrige Frequenzen: \(-90^\circ\)
- bei \(\omega_E\): \(-135^\circ\)
- hohe Frequenzen: \(-180^\circ\)

Für die Aufgabe:

\[
T_1=T_2=0.5
\Rightarrow
\omega_E=2,
\]

\[
T_1=T_2=5
\Rightarrow
\omega_E=0.2.
\]

---

# 9. Aufgabe 3 – Kombination von Übertragungsfunktionen

## 9.1 Allgemeines Vorgehen

Bei Reihenschaltung:

\[
G_{\mathrm{ges}}
=
\prod_k G_k.
\]

Im Bode-Diagramm:

\[
L_{\mathrm{ges}}
=
\sum_k L_k,
\]

\[
\varphi_{\mathrm{ges}}
=
\sum_k\varphi_k.
\]

Gleiche Faktoren vervielfachen also Steigung und Phase.

---

## 9.2 Aufgabe 3a – zwei gleiche PT1-Glieder

\[
G_{\mathrm{ges}}(s)
=
\left(
\frac1{1+0.1s}
\right)^2.
\]

Eckfrequenz:

\[
\omega_E=10.
\]

Betrag:

\[
|G|
=
\frac1{1+(0.1\omega)^2}.
\]

dB:

\[
\boxed{
L(\omega)
=
-20\log_{10}
\left(
1+(0.1\omega)^2
\right)
}.
\]

Phase:

\[
\boxed{
\varphi(\omega)
=
-2\arctan(0.1\omega)
}.
\]

Asymptoten:

- unterhalb \(10\): \(0\,\mathrm{dB}\)
- oberhalb \(10\): \(-40\,\mathrm{dB/Dekade}\)

Bei der Ecke:

\[
|G|=\frac12,
\]

\[
L=-6.02\,\mathrm{dB},
\]

\[
\varphi=-90^\circ.
\]

---

## 9.3 Aufgabe 3b – drei gleiche PT1-Glieder

\[
G_{\mathrm{ges}}(s)
=
\left(
\frac1{1+0.1s}
\right)^3.
\]

Betrag:

\[
|G|
=
\frac1{
\left(
1+(0.1\omega)^2
\right)^{3/2}
}.
\]

dB:

\[
\boxed{
L(\omega)
=
-30\log_{10}
\left(
1+(0.1\omega)^2
\right)
}.
\]

Phase:

\[
\boxed{
\varphi(\omega)
=
-3\arctan(0.1\omega)
}.
\]

Asymptoten:

- unterhalb \(10\): \(0\,\mathrm{dB}\)
- oberhalb \(10\): \(-60\,\mathrm{dB/Dekade}\)

Grenzphase:

\[
\varphi(\infty)=-270^\circ.
\]

Bei der Ecke:

\[
L=-9.03\,\mathrm{dB},
\qquad
\varphi=-135^\circ.
\]

---

## 9.4 Aufgabe 3c – PT1 und D-Glied

\[
G_1(s)
=
\frac1{1+0.1s},
\]

\[
G_2(s)=s.
\]

Gesamt:

\[
\boxed{
G_{\mathrm{ges}}(s)
=
\frac{s}{1+0.1s}
}.
\]

Betrag:

\[
\boxed{
|G(j\omega)|
=
\frac{\omega}{
\sqrt{1+(0.1\omega)^2}
}
}.
\]

dB:

\[
\boxed{
L(\omega)
=
20\log_{10}\omega
-
10\log_{10}
\left(
1+(0.1\omega)^2
\right)
}.
\]

Phase:

\[
\boxed{
\varphi(\omega)
=
90^\circ-\arctan(0.1\omega)
}.
\]

Asymptoten:

- \(\omega<10\): \(+20\,\mathrm{dB/Dekade}\)
- \(\omega>10\): \(0\,\mathrm{dB/Dekade}\)

Hochfrequenzverstärkung:

\[
\lim_{\omega\to\infty}|G(j\omega)|
=
\frac1{0.1}
=
10.
\]

In dB:

\[
20\log_{10}(10)=20\,\mathrm{dB}.
\]

Phase:

- niedrige Frequenzen: \(+90^\circ\)
- bei \(\omega=10\): \(+45^\circ\)
- hohe Frequenzen: \(0^\circ\)

---

# 10. Aufgabe 4 – Ortskurven und Pol-Nullstellen-Diagramme

## 10.1 Allgemeines Rechenschema

1. \(s=j\omega\) einsetzen.
2. Bruch mit dem komplex konjugierten Nenner erweitern.
3. Form

\[
G(j\omega)
=
u(\omega)+jv(\omega)
\]

bestimmen.
4. Grenzwerte \(\omega\to0^+\) und \(\omega\to\infty\) berechnen.
5. Charakteristische Frequenzen einsetzen.
6. Durchlaufrichtung mit wachsendem \(\omega\) markieren.
7. Pole aus dem Nenner und Nullstellen aus dem Zähler bestimmen.

---

## 10.2 Aufgabe 4a – PT1

\[
G(s)
=
\frac1{1+Ts}.
\]

Frequenzgang:

\[
G(j\omega)
=
\frac1{1+jT\omega}.
\]

Mit konjugiertem Nenner:

\[
G(j\omega)
=
\frac{1-jT\omega}{
1+(T\omega)^2
}.
\]

Damit:

\[
\boxed{
\operatorname{Re}G
=
\frac1{
1+(T\omega)^2
}
}
\]

\[
\boxed{
\operatorname{Im}G
=
-\frac{T\omega}{
1+(T\omega)^2
}
}.
\]

Elimination von \(\omega\):

\[
\boxed{
\left(
\operatorname{Re}G-\frac12
\right)^2
+
\left(
\operatorname{Im}G
\right)^2
=
\left(
\frac12
\right)^2
}.
\]

Die Ortskurve ist für \(\omega\ge0\) der untere Halbkreis:

\[
G(j0)=1,
\]

\[
G\left(j\frac1T\right)
=
\frac12-\frac j2,
\]

\[
G(j\infty)=0.
\]

### Einfluss von \(T\)

Die geometrische Kurve ist unabhängig von \(T\). Nur die Frequenzmarkierungen auf der Kurve ändern sich.

Pole:

\[
\boxed{s_1=-\frac1T}.
\]

Nullstellen: keine.

Für die Aufgabe:

\[
T=1
\Rightarrow
s_1=-1,
\]

\[
T=0.1
\Rightarrow
s_1=-10.
\]

Die handschriftliche Rechnung auf PDF-S. 52 ist korrekt.

---

## 10.3 Aufgabe 4b – I-Glied

\[
G(s)
=
\frac1{Ts}.
\]

\[
G(j\omega)
=
-\frac j{T\omega}.
\]

Damit:

\[
\boxed{\operatorname{Re}G=0}
\]

\[
\boxed{
\operatorname{Im}G
=
-\frac1{T\omega}
}.
\]

Ortskurve:

- negative imaginäre Achse,
- \(\omega\to0^+\): \(-j\infty\),
- \(\omega\to\infty\): \(0\).

Pole:

\[
\boxed{s_1=0}.
\]

Nullstellen: keine.

### [KORRIGIERT]

Der offizielle Hinweis auf Blattseite 10/12, der Verlauf könne je nach Zeitkonstante stärker in den negativen Realteil reichen, passt nicht zu

\[
G(s)=\frac1{Ts}.
\]

Für dieses reine I-Glied ist der Realteil unabhängig von \(T\) exakt null. Die Zeitkonstante verändert nur die Skalierung entlang der imaginären Achse.

---

## 10.4 Aufgabe 4c – D-Glied

\[
G(s)=Ts.
\]

\[
G(j\omega)
=
jT\omega.
\]

Damit:

\[
\operatorname{Re}G=0,
\qquad
\operatorname{Im}G=T\omega.
\]

Ortskurve:

- positive imaginäre Achse,
- Start bei \(0\),
- Ende bei \(+j\infty\).

Nullstelle:

\[
\boxed{s_{0,1}=0}.
\]

Pole: keine.

Das ideale D-Glied ist nicht echt gebrochen und physikalisch nur idealisiert realisierbar.

---

## 10.5 Aufgabe 4d – Nullstelle erster Ordnung

\[
G(s)=1+Ts.
\]

\[
G(j\omega)
=
1+jT\omega.
\]

Daher:

\[
\boxed{\operatorname{Re}G=1}
\]

\[
\boxed{\operatorname{Im}G=T\omega}.
\]

Ortskurve:

- vertikale Gerade bei \(\operatorname{Re}=1\),
- Start \(G(j0)=1\),
- für \(\omega\to\infty\) nach \(+j\infty\).

Nullstelle:

\[
1+Ts=0
\]

\[
\boxed{
s_{0,1}
=
-\frac1T
}.
\]

Für die Aufgabe:

\[
T=0.5
\Rightarrow
s_0=-2,
\]

\[
T=2
\Rightarrow
s_0=-0.5.
\]

Pole: keine.

---

## 10.6 Aufgabe 4e – IT1-Glied

\[
G(s)
=
\frac1{T_1s(T_2s+1)}.
\]

Einsetzen:

\[
G(j\omega)
=
\frac1{
jT_1\omega(1+jT_2\omega)
}.
\]

Nach Rationalisierung:

\[
\boxed{
\operatorname{Re}G
=
-\frac{T_2}{
T_1\left(
1+(T_2\omega)^2
\right)
}
}
\]

\[
\boxed{
\operatorname{Im}G
=
-\frac1{
T_1\omega
\left(
1+(T_2\omega)^2
\right)
}
}.
\]

Grenzwerte:

\[
\omega\to0^+:
\quad
\operatorname{Re}G
\to
-\frac{T_2}{T_1},
\qquad
\operatorname{Im}G
\to
-\infty.
\]

\[
\omega\to\infty:
\quad
G(j\omega)\to0
\]

aus dem dritten Quadranten.

Für die gegebenen Fälle gilt \(T_1=T_2\), also:

\[
\operatorname{Re}G(\omega\to0^+)\to-1.
\]

Pole:

\[
\boxed{s_1=0}
\]

\[
\boxed{
s_2=-\frac1{T_2}
}.
\]

Für:

\[
T_2=0.5
\Rightarrow
s_2=-2,
\]

\[
T_2=5
\Rightarrow
s_2=-0.2.
\]

Nullstellen: keine.

---

## 10.7 Aufgabe 4f – zwei gleiche PT1-Faktoren

\[
G(s)
=
\frac1{(1+Ts)^2},
\qquad
T=0.1.
\]

Setze

\[
x=T\omega.
\]

Dann:

\[
G(j\omega)
=
\frac1{(1+jx)^2}
=
\frac{(1-jx)^2}{
(1+x^2)^2
}.
\]

Damit:

\[
\boxed{
\operatorname{Re}G
=
\frac{1-x^2}{
(1+x^2)^2
}
}
\]

\[
\boxed{
\operatorname{Im}G
=
-\frac{2x}{
(1+x^2)^2
}
}.
\]

Charakteristische Punkte:

\[
\omega=0:
\quad
G=1.
\]

Bei

\[
x=1
\quad\Leftrightarrow\quad
\omega=\frac1T=10
\]

gilt:

\[
G=-\frac j2.
\]

Für

\[
\omega\to\infty:
\quad
G\to0
\]

aus dem negativen Realbereich.

Pole:

\[
\boxed{s_{1,2}=-\frac1T=-10}.
\]

Nullstellen: keine.

### Genaues Minimum des Imaginärteils

Der tiefste Punkt liegt nicht exakt bei \(\omega=4\), sondern bei:

\[
x=\frac1{\sqrt3}.
\]

Damit:

\[
\boxed{
\omega_{\min}
=
\frac1{T\sqrt3}
\approx5.77
}.
\]

Die in der offiziellen Skizze markierte Frequenz \(\omega=4\) ist damit nur ein Beispielpunkt, nicht der exakte Tiefpunkt.

---

## 10.8 Aufgabe 4g – DT1-/Hochpass-Faktor

## Gegeben

\[
G(s)
=
\frac{T_1s}{T_2s+1},
\]

\[
T_1=1,
\qquad
T_2=0.1.
\]

Einsetzen:

\[
G(j\omega)
=
\frac{jT_1\omega}{
1+jT_2\omega
}.
\]

Rationalisieren:

\[
G(j\omega)
=
\frac{
T_1T_2\omega^2+jT_1\omega
}{
1+(T_2\omega)^2
}.
\]

Damit:

\[
\boxed{
\operatorname{Re}G
=
\frac{
T_1T_2\omega^2
}{
1+(T_2\omega)^2
}
}
\]

\[
\boxed{
\operatorname{Im}G
=
\frac{
T_1\omega
}{
1+(T_2\omega)^2
}
}.
\]

Setze:

\[
K=\frac{T_1}{T_2}.
\]

Dann erfüllt die Ortskurve:

\[
\boxed{
\left(
\operatorname{Re}G-\frac K2
\right)^2
+
\left(
\operatorname{Im}G
\right)^2
=
\left(
\frac K2
\right)^2
}.
\]

Sie ist für \(\omega\ge0\) der obere Halbkreis von \(0\) bis \(K\).

Mit:

\[
K=\frac1{0.1}=10
\]

folgt:

\[
G(j0)=0,
\]

\[
G\left(j\frac1{T_2}\right)
=
5+j5,
\]

\[
G(j\infty)=10.
\]

Pole:

\[
\boxed{
s_1=-\frac1{T_2}=-10
}.
\]

Nullstelle:

\[
\boxed{s_{0,1}=0}.
\]

---

# 11. Qualitätsprüfung der Mitschrift

## Vollständig und fachlich brauchbar

- Definition und Zerlegung des Frequenzgangs auf PDF-S. 40
- dB-Addition und Phasenaddition bei Reihenschaltung auf PDF-S. 40–41
- Grundidee von Polen und Nullstellen auf PDF-S. 41
- Amplitudenrechnung zu Aufgabe 1a und 1b auf PDF-S. 42
- vollständige I-Glied-Herleitung auf PDF-S. 43–45
- PT1-Eckfrequenz und asymptotische Steigung auf PDF-S. 46–47
- Ortskurven-Grundrechnungen zu Aufgabe 4a und 4b auf PDF-S. 52–53

## Nur als Diagramm oder Aufgabenstellung vorhanden

Für große Teile von Aufgabe 2, Aufgabe 3 und Aufgabe 4c–g sind keine vollständigen handschriftlichen Herleitungen vorhanden. Die Rechenwege wurden oben aus den offiziellen Funktionen und den Skriptdefinitionen vollständig rekonstruiert.

## Korrekturen und Unklarheiten

1. **Aufgabe 1c:** Im Betrag muss allgemein \(|C|\) stehen.
2. **Aufgabe 4b:** Der offizielle Hinweis auf einen negativen Realteil ist für ein reines I-Glied mathematisch falsch.
3. **Aufgabe 4f:** Die eingezeichnete Frequenz \(\omega=4\) ist nicht der exakte tiefste Punkt der Ortskurve.
4. **Eckfrequenz bei I- und D-Glied:** Es existiert kein geometrischer Knick. \(\omega=1/T\) ist dort die \(0\,\mathrm{dB}\)-Frequenz.

---

# 12. Typische Fehler in Tutorium 04

1. \(j^2=+1\) statt \(j^2=-1\) einsetzen.
2. Betrag eines Bruchs nicht als Quotient der Beträge behandeln.
3. Betrag und Phase verwechseln.
4. Phase nur mit \(\arctan(\operatorname{Im}/\operatorname{Re})\) bestimmen und den Quadranten ignorieren.
5. Im dB-Maß mit \(10\log_{10}\) statt \(20\log_{10}\) rechnen.
6. Produkte im linearen Maß addieren statt multiplizieren.
7. Phasen bei Reihenschaltung nicht addieren.
8. \(\omega_E=1/T\) falsch herum bestimmen.
9. Bei mehreren gleichen Polen die Steigung nicht vervielfachen.
10. Bei Ortskurven nur Start- und Endpunkt zeichnen, aber die Durchlaufrichtung vergessen.
11. Pole und Nullstellen vertauschen.
12. Eine Nullstelle bei \(s=0\) als Pol markieren.
13. Negative und positive imaginäre Achse bei I- und D-Glied vertauschen.
14. Bei PT1 annehmen, dass verschiedene \(T\) verschiedene geometrische Ortskurven erzeugen.
15. Bei \(G=1/(1+Ts)^2\) den doppelten Pol nicht kennzeichnen.
16. Frequenzmarkierungen aus einer qualitativen Skizze als exakte Extremstellen interpretieren.

---

# 13. Klausurstrategie

## 13.1 Amplitudenverhalten

1. \(s=j\omega\).
2. \(j^2=-1\) sofort einsetzen.
3. Real- und Imaginärteil trennen.
4. Betrag bilden.
5. \(\omega=0\), \(\omega\to\infty\) und Nennernullstellen prüfen.

## 13.2 Bode-Diagramm

1. Funktion vollständig faktorisieren.
2. Jeden Faktor einem Standardglied zuordnen.
3. Verstärkungsfaktor in dB bestimmen.
4. Eckfrequenzen \(1/T\) markieren.
5. Steigungen der Faktoren addieren.
6. Phasen addieren.
7. Exakte Werte an den Ecken prüfen.

## 13.3 Ortskurve

1. \(G(j\omega)=u(\omega)+jv(\omega)\).
2. Start- und Endpunkt berechnen.
3. Mindestens einen charakteristischen Zwischenpunkt einsetzen.
4. Vorzeichen von Real- und Imaginärteil prüfen.
5. Durchlaufrichtung einzeichnen.
6. Pole und Nullstellen separat aus \(G(s)\) bestimmen.

---

# 14. NotebookLM-Verifikation

--- NOTEBOOKLM-PROMPT ---

Prüfe ausschließlich anhand der hochgeladenen offiziellen Regelungstechnik-Unterlagen die folgenden Auffälligkeiten aus „Tutorium 04 – Darstellungen im Frequenzbereich“:

1. Aufgabe 1c:
Für
\[
G(s)=\frac{C}{As^2+Bs-1}
\]
steht in der Musterlösung im Zähler des Betrags \(C\). Muss allgemein \(|C|\) stehen, oder wird in den Quellen ausdrücklich \(C>0\) vorausgesetzt?

2. Aufgabe 4b:
Für
\[
G(s)=\frac1{Ts}
\]
steht nach der offiziellen Ortskurve ein Hinweis, die Kurve könne je nach Zeitkonstante stärker in den negativen Realteil verlaufen. Prüfe, ob dieser Hinweis zu dieser Aufgabe gehört. Berechne dafür Real- und Imaginärteil von \(G(j\omega)\).

3. Aufgabe 4f:
Für
\[
G(s)=\frac1{(Ts+1)^2},\qquad T=0.1
\]
ist in der offiziellen Skizze \(\omega=4\) nahe dem tiefsten Punkt markiert. Ist das nur ein Beispielpunkt oder wird behauptet, dort liege das Minimum? Bestimme die Frequenz des tatsächlichen Minimums des Imaginärteils.

Belege jede direkte Quellenaussage mit Dokumentname und genauer Seite. Trenne Quellenaussage und eigene mathematische Prüfung.

--- ENDE ---

---

# 15. Kompaktformelsammlung Tutorium 04

## Frequenzgang

\[
s=j\omega.
\]

## Betrag

\[
|a+jb|
=
\sqrt{a^2+b^2}.
\]

## Phase

\[
\varphi
=
\arg G(j\omega).
\]

## dB

\[
L(\omega)
=
20\log_{10}|G(j\omega)|.
\]

## Reihenschaltung

\[
G_{\mathrm{ges}}
=
\prod_kG_k,
\]

\[
L_{\mathrm{ges}}
=
\sum_kL_k,
\]

\[
\varphi_{\mathrm{ges}}
=
\sum_k\varphi_k.
\]

## Eckfrequenz eines Faktors \(1+Ts\)

\[
\omega_E=\frac1T.
\]

## PT1

\[
G(s)=\frac1{1+Ts},
\]

\[
|G|
=
\frac1{\sqrt{1+(T\omega)^2}},
\]

\[
\varphi
=
-\arctan(T\omega).
\]

## I-Glied

\[
G(s)=\frac1{Ts},
\]

\[
|G|
=
\frac1{T\omega},
\]

\[
\varphi=-90^\circ.
\]

## D-Glied

\[
G(s)=Ts,
\]

\[
|G|=T\omega,
\]

\[
\varphi=+90^\circ.
\]

## Nullstelle erster Ordnung

\[
G(s)=1+Ts,
\]

\[
|G|
=
\sqrt{1+(T\omega)^2},
\]

\[
\varphi
=
\arctan(T\omega).
\]

## Ortskurve PT1

\[
\left(
\operatorname{Re}G-\frac12
\right)^2
+
(\operatorname{Im}G)^2
=
\frac14.
\]

## Pole und Nullstellen

\[
G(s)=\frac{Z(s)}{N(s)}.
\]

\[
Z(s_0)=0
\quad\Rightarrow\quad
\text{Nullstelle}.
\]

\[
N(s_p)=0
\quad\Rightarrow\quad
\text{Pol}.
\]

---

# Tutorium 05 – Grundlegende Übertragungselemente und Blockschaltbilder

## 1. Quellen und Seitenbereich

### Primärquellen

1. **RT-Tutorien-Mitschrift.pdf**, PDF-Seiten 59–66
   - S. 59: Theoriefragen und Beginn von Aufgabe 1
   - S. 60: handschriftliche Übersicht zu P-, I-, D-, PT1- und PT2-Glied
   - S. 61: Totzeitglied
   - S. 62–63: offizielle Aufgaben 1 und 2
   - S. 64: Grundregeln der Blockrechnung und vollständige Rechnung zu Aufgabe 2a
   - S. 65: Rechnungen zu Aufgabe 2b und 2c
   - S. 66: leer
   - Tutorium 06 beginnt auf PDF-Seite 67.

2. **Regelungstechnik_Tutorium_komplett.pdf**, PDF-Seiten 29–32  
   Tutorium 05, Blattseiten 1/4–4/4, offizielle Aufgaben und Endergebnisse.

3. **skript.pdf**
   - PDF-S. 74–75: Korollar 3.35 „Blockrechnung“
   - PDF-S. 76–80: P-, I-, D- und Totzeitglied
   - PDF-S. 80–83: PT1- und PT2-Glied
   - PDF-S. 84: IT1- und DT1-Glied

---

# 2. Theoriefrage 1 – Viertelfahrzeug qualitativ klassifizieren

## 2.1 Physikalische Elemente

Das dargestellte Viertelfahrzeug enthält:

- Masse \(m\),
- Feder \(c\),
- Dämpfer \(d\),
- Straßenanregung \(u(t)\),
- relativen Abstand \(y(t)\) zwischen Fahrzeugmasse und Straße.

Die Elemente besitzen qualitativ folgende Eigenschaften:

### Feder

\[
F_c=c\,y.
\]

Die Kraft ist proportional zur Auslenkung. Die Feder wirkt daher als **P-Glied** zwischen Auslenkung und Federkraft.

### Dämpfer

\[
F_d=d\,\dot y.
\]

Die Kraft ist proportional zur Geschwindigkeit. Der Dämpfer wirkt als **D-Glied** zwischen Auslenkung und Dämpfungskraft.

### Masse

\[
m\ddot x=F.
\]

Von Kraft zu Beschleunigung liegt ein P-Zusammenhang vor. Von Kraft zu Geschwindigkeit wird einmal integriert und von Kraft zu Position zweimal:

\[
\frac{X(s)}{F(s)}
=
\frac1{ms^2}.
\]

Die Masse wirkt von Kraft zu Position wie ein **doppeltes I-Glied**.

---

## 2.2 Systemordnung

Es gibt zwei unabhängige Energiespeicher:

1. kinetische Energie der Masse,
2. potenzielle Energie der Feder.

Der Dämpfer speichert keine Energie, sondern dissipiert sie.

Daher ist das System im vereinfachten Modell **zweiter Ordnung**.

---

## 2.3 Bewegungsgleichung bei relativer Ausgangsgröße

Sei \(x(t)\) die absolute Position der Masse und

\[
y(t)=x(t)-u(t)
\]

die relative Auslenkung gegenüber der Straße.

Dann:

\[
x(t)=y(t)+u(t)
\]

und

\[
\ddot x(t)=\ddot y(t)+\ddot u(t).
\]

Kräftegleichgewicht:

\[
m\ddot x+d\dot y+cy=0.
\]

Einsetzen:

\[
m\left(\ddot y+\ddot u\right)
+d\dot y
+cy
=
0.
\]

Damit:

\[
m\ddot y+d\dot y+cy=-m\ddot u.
\]

Bei verschwindenden Anfangsbedingungen:

\[
\left(ms^2+ds+c\right)Y(s)
=
-ms^2U(s).
\]

Übertragungsfunktion:

\[
\boxed{
\frac{Y(s)}{U(s)}
=
-\frac{ms^2}{ms^2+ds+c}
}.
\]

Qualitativ besteht das System aus:

- einem D-Anteil zweiter Ordnung im Zähler,
- einem PT2-Verhalten im Nenner.

Es ist damit ein dynamischer Hochpass zweiter Ordnung und kein reines P-, I- oder D-Glied.

### Hinweis zur Modellinterpretation

Diese Übertragungsfunktion folgt daraus, dass die Aufgabe ausdrücklich den **Abstand zur Straßenoberfläche** als Ausgang nennt. Bei Wahl der absoluten Fahrzeugposition als Ausgang entstünde eine andere Zählerstruktur.

---

## 2.4 Schwingungsfähigkeit

Das charakteristische Polynom lautet:

\[
ms^2+ds+c.
\]

Die Pole sind:

\[
s_{1,2}
=
\frac{-d\pm\sqrt{d^2-4mc}}{2m}.
\]

Das System ist schwingungsfähig, wenn die Pole komplex konjugiert sind:

\[
d^2-4mc<0.
\]

Also:

\[
\boxed{
d^2<4mc
}.
\]

Äquivalent mit Dämpfungsgrad

\[
D=\frac{d}{2\sqrt{mc}}
\]

gilt:

\[
\boxed{D<1}.
\]

- \(D<1\): schwingfähiges, unterdämpftes System,
- \(D=1\): aperiodischer Grenzfall,
- \(D>1\): überdämpft, keine Schwingung.

### Quellenstatus

Die Elementzuordnung und Systemordnung sind aus dem dargestellten Ersatzmodell hergeleitet. Eine ausformulierte offizielle Musterantwort zu den Theoriefragen ist in den Tutoriumsunterlagen nicht enthalten.

---

# 3. Theoriefrage 2 – Warum werden Reihen multipliziert und Parallelen addiert?

## 3.1 Reihenschaltung

Für zwei hintereinander geschaltete Systeme gilt:

\[
X(s)=G_1(s)U(s),
\]

\[
Y(s)=G_2(s)X(s).
\]

Einsetzen:

\[
Y(s)
=
G_2(s)G_1(s)U(s).
\]

Damit:

\[
\boxed{
G_{\mathrm{ges}}(s)
=
\frac{Y(s)}{U(s)}
=
G_1(s)G_2(s)
}.
\]

Die Reihenfolge ist bei skalaren Übertragungsfunktionen algebraisch egal, weil Multiplikation kommutativ ist. Bei Zustandsraummodellen oder Mehrgrößensystemen darf diese Aussage nicht blind übertragen werden.

---

## 3.2 Parallelschaltung

Beide Zweige erhalten denselben Eingang:

\[
Y_1(s)=G_1(s)U(s),
\]

\[
Y_2(s)=G_2(s)U(s).
\]

Bei addierender Zusammenführung:

\[
Y(s)=Y_1(s)+Y_2(s).
\]

Also:

\[
Y(s)
=
\left(G_1(s)+G_2(s)\right)U(s).
\]

Damit:

\[
\boxed{
G_{\mathrm{ges}}(s)
=
G_1(s)+G_2(s)
}.
\]

Bei einem Minuszeichen am Summationspunkt wird entsprechend subtrahiert:

\[
G_{\mathrm{ges}}=G_1-G_2.
\]

---

## 3.3 Rückkopplung

Sei \(G\) der Vorwärtszweig und \(H\) der Rückführzweig.

### Negative Rückkopplung

\[
E=U-HY,
\]

\[
Y=GE.
\]

Einsetzen:

\[
Y=G(U-HY).
\]

\[
Y+GHY=GU.
\]

\[
Y(1+GH)=GU.
\]

Damit:

\[
\boxed{
\frac YU
=
\frac G{1+GH}
}.
\]

### Positive Rückkopplung

\[
E=U+HY.
\]

Dann:

\[
Y=G(U+HY).
\]

\[
Y-GHY=GU.
\]

Damit:

\[
\boxed{
\frac YU
=
\frac G{1-GH}
}.
\]

### Sichere Vorzeichenregel

- Minus am Summationspunkt \(\Rightarrow\) Plus im Nenner.
- Plus am Summationspunkt \(\Rightarrow\) Minus im Nenner.

Quelle: `skript.pdf`, PDF-S. 74–75, Korollar 3.35. Das Skript zeigt dort die negative Standardrückkopplung.

---

# 4. Grundlegende Übertragungselemente

## 4.1 P-Glied

\[
\boxed{
G(s)=K_P
}.
\]

Zeitbereich:

\[
y(t)=K_Pu(t).
\]

Eigenschaften:

- sofortige proportionale Reaktion,
- keine Verzögerung,
- kein Energiespeicher,
- Amplitudengang konstant:

\[
20\log_{10}|K_P|,
\]

- Phase bei positivem \(K_P\):

\[
0^\circ.
\]

Die Mitschrift auf PDF-S. 60 nennt korrekt:

\[
G(s)=K.
\]

---

## 4.2 I-Glied

\[
\boxed{
G(s)=\frac1{T_Is}
=
\frac{K_I}{s}
}.
\]

Zeitbereich:

\[
y(t)
=
\frac1{T_I}
\int u(t)\,\mathrm dt.
\]

Eigenschaften:

- integriert den Eingang,
- Sprungantwort ist eine Rampe,
- Pol bei \(s=0\),
- Steigung im Bode-Diagramm:

\[
-20\,\mathrm{dB/Dekade},
\]

- Phase:

\[
-90^\circ.
\]

---

## 4.3 D-Glied

\[
\boxed{
G(s)=T_Ds
=
K_Ds
}.
\]

Zeitbereich:

\[
y(t)=T_D\dot u(t).
\]

Eigenschaften:

- differenziert den Eingang,
- ideale Sprungantwort ist ein Dirac-Impuls,
- Nullstelle bei \(s=0\),
- Steigung:

\[
+20\,\mathrm{dB/Dekade},
\]

- Phase:

\[
+90^\circ.
\]

Das ideale D-Glied ist nicht echt gebrochen und physikalisch nur idealisiert realisierbar.

---

## 4.4 Totzeitglied

\[
\boxed{
G(s)=e^{-T_ts}
}.
\]

Zeitbereich:

\[
\boxed{
y(t)=u(t-T_t)
}.
\]

Frequenzgang:

\[
G(j\omega)
=
e^{-j\omega T_t}.
\]

Betrag:

\[
\boxed{|G(j\omega)|=1}.
\]

Phase:

\[
\boxed{
\varphi(\omega)
=
-\omega T_t
}
\]

in Radiant.

Das Totzeitglied verändert also nicht die Amplitude, sondern erzeugt eine frequenzabhängige negative Phase.

### [KORRIGIERT]

In der Mitschrift auf PDF-S. 61 steht sinngemäß eine verschobene Ausgangsfunktion. Präzise muss bei kausaler Betrachtung gegebenenfalls zusätzlich eine Heaviside-Funktion berücksichtigt werden:

\[
y(t)=u(t-T_t)\eta(t-T_t).
\]

---

## 4.5 PT1-Glied

\[
\boxed{
G(s)
=
\frac{K_P}{Ts+1}
}.
\]

Differentialgleichung:

\[
T\dot y+y=K_Pu.
\]

Sprungantwort bei Einheitssprung:

\[
\boxed{
y(t)
=
K_P
\left(
1-e^{-t/T}
\right)
}.
\]

Eigenschaften:

- ein dominanter Energiespeicher,
- ein Pol:

\[
s_1=-\frac1T,
\]

- Eckfrequenz:

\[
\omega_E=\frac1T,
\]

- oberhalb der Ecke:

\[
-20\,\mathrm{dB/Dekade},
\]

- Phase von \(0^\circ\) nach \(-90^\circ\).

Die qualitative Ortskurve und Bode-Skizze auf Mitschrift-PDF-S. 60 sind korrekt.

---

## 4.6 PT2-Glied

Faktorisierte Form:

\[
\boxed{
G(s)
=
\frac{K_P}
{(T_1s+1)(T_2s+1)}
}.
\]

Schwingungsform:

\[
\boxed{
G(s)
=
\frac{K_P\omega_0^2}
{s^2+2D\omega_0s+\omega_0^2}
}.
\]

Eigenschaften:

- zwei dynamische Zustände bzw. Energiespeicher,
- zwei Pole,
- kann je nach Dämpfung monoton oder schwingend einschwingen,
- Hochfrequenzsteigung:

\[
-40\,\mathrm{dB/Dekade}.
\]

### [KORRIGIERT]

Die handschriftliche Skizze auf PDF-S. 60 zeichnet mehrere nachklingende Schwingungen und eine monotone Kurve. Inhaltlich ist das richtig, aber die Beschriftung der Standardform ist schwer lesbar. Verwendet werden sollte eine der beiden obigen eindeutigen Formen.

---

## 4.7 IT1-Glied

\[
\boxed{
G(s)
=
\frac1{T_1s(T_2s+1)}
}.
\]

Es ist die Reihenschaltung aus:

- I-Glied,
- PT1-Glied.

Eigenschaften:

- Pol im Ursprung,
- zusätzlicher reeller Pol,
- niedrige Frequenzen:

\[
-20\,\mathrm{dB/Dekade},
\]

- hohe Frequenzen:

\[
-40\,\mathrm{dB/Dekade},
\]

- Phase von \(-90^\circ\) nach \(-180^\circ\).

---

## 4.8 DT1-Glied

\[
\boxed{
G(s)
=
\frac{T_1s}{T_2s+1}
}.
\]

Es ist die Reihenschaltung aus:

- D-Glied,
- PT1-Glied.

Eigenschaften:

- Nullstelle im Ursprung,
- reeller Pol bei

\[
s=-\frac1{T_2},
\]

- niedrige Frequenzen:

\[
+20\,\mathrm{dB/Dekade},
\]

- hohe Frequenzen: konstanter Betrag

\[
\lim_{\omega\to\infty}|G(j\omega)|
=
\frac{T_1}{T_2},
\]

- Phase von \(+90^\circ\) nach \(0^\circ\).

Quelle: `skript.pdf`, PDF-S. 84.

---

# 5. Aufgabe 1 – Elemente a bis g klassifizieren

## 5.1 Aufgabe 1a

\[
G(s)
=
\frac1{Ts+1}.
\]

Klassifikation:

\[
\boxed{\text{PT1-Glied}}.
\]

Für:

\[
T=0.1
\Rightarrow
s_1=-10,
\qquad
\omega_E=10.
\]

Für:

\[
T=1
\Rightarrow
s_1=-1,
\qquad
\omega_E=1.
\]

---

## 5.2 Aufgabe 1b

\[
G(s)
=
\frac1{Ts}.
\]

Klassifikation:

\[
\boxed{\text{I-Glied}}.
\]

Für \(T=0.2\):

\[
G(s)=\frac5s.
\]

Für \(T=10\):

\[
G(s)=\frac{0.1}{s}.
\]

Beide besitzen einen Pol im Ursprung. Die Zeitkonstante ändert nur die Verstärkung.

---

## 5.3 Aufgabe 1c

\[
G(s)=Ts.
\]

Klassifikation:

\[
\boxed{\text{D-Glied}}.
\]

Für \(T=1\):

\[
G(s)=s.
\]

Für \(T=10\):

\[
G(s)=10s.
\]

Beide besitzen eine Nullstelle im Ursprung.

---

## 5.4 Aufgabe 1d

\[
G(s)=1+Ts.
\]

Zerlegung:

\[
G(s)=1+Ts.
\]

Dies ist eine Parallelschaltung aus:

- P-Glied mit \(K_P=1\),
- D-Glied mit \(T_D=T\).

Klassifikation:

\[
\boxed{\text{PD-Glied}}.
\]

Die offizielle Lösung nennt getrennt „P-Glied, D-Glied“.

Nullstelle:

\[
\boxed{
s_0=-\frac1T
}.
\]

---

## 5.5 Aufgabe 1e

\[
G(s)
=
\frac1{T_1s(T_2s+1)}.
\]

Zerlegung:

\[
G(s)
=
\frac1{T_1s}
\cdot
\frac1{T_2s+1}.
\]

Klassifikation:

\[
\boxed{\text{IT1-Glied}}.
\]

Die offizielle Lösung nennt „PT1-Glied, I-Glied“.

Pole:

\[
s_1=0,
\]

\[
s_2=-\frac1{T_2}.
\]

---

## 5.6 Aufgabe 1f

\[
G(s)
=
\frac1{(Ts+1)^2}.
\]

Zerlegung:

\[
G(s)
=
\frac1{Ts+1}
\cdot
\frac1{Ts+1}.
\]

Klassifikation laut offizieller Lösung:

\[
\boxed{\text{zwei identische PT1-Glieder}}.
\]

Äquivalent:

\[
(Ts+1)^2
=
T^2s^2+2Ts+1.
\]

Dies entspricht einem PT2-Glied mit doppeltem reellem Pol:

\[
s_{1,2}=-\frac1T.
\]

In normierter Schwingungsform entspricht dies dem aperiodischen Grenzfall:

\[
\boxed{D=1}.
\]

---

## 5.7 Aufgabe 1g

\[
G(s)
=
\frac{T_1s}{T_2s+1}.
\]

Zerlegung:

\[
G(s)
=
T_1s
\cdot
\frac1{T_2s+1}.
\]

Klassifikation:

\[
\boxed{\text{DT1-Glied}}.
\]

Die offizielle Lösung nennt „D-Glied, PT1-Glied“.

Nullstelle:

\[
s_0=0.
\]

Pol:

\[
s_1=-\frac1{T_2}.
\]

---

# 6. Blockschaltbilder systematisch zusammenfassen

## 6.1 Sicheres Vorgehen

1. Alle Summationszeichen und Vorzeichen markieren.
2. Signalrichtungen prüfen.
3. Kleine innere Schleifen zuerst zusammenfassen.
4. Reihen- und Parallelschaltungen bilden.
5. Danach äußere Rückkopplungen schließen.
6. Ergebnis alternativ mit Signalgleichungen kontrollieren.

### Wichtiger Grundsatz

Ein Block darf nur dann direkt verschoben oder zusammengefasst werden, wenn die Signalbeziehungen an Abzweig- und Summationspunkten erhalten bleiben.

---

# 7. Aufgabe 2a – innere positive und äußere negative Rückkopplung

## 7.1 Struktur erkennen

Das Blockschaltbild enthält:

1. eine Reihenschaltung \(G_1G_2\),
2. eine **positive** innere Rückkopplung über \(G_4\),
3. eine Parallelschaltung \(G_3+G_5\),
4. eine **negative** äußere Rückkopplung über \(G_6\).

---

## 7.2 Innere Schleife über \(G_4\)

Sei \(e_0\) das Signal nach der äußeren Summationsstelle und \(x\) der Ausgang von \(G_2\).

Die innere Summationsstelle addiert positiv:

\[
q=e_0+G_4x.
\]

Vorwärtszweig:

\[
x=G_1G_2q.
\]

Einsetzen:

\[
x
=
G_1G_2
\left(
e_0+G_4x
\right).
\]

\[
x-G_1G_2G_4x
=
G_1G_2e_0.
\]

\[
x
\left(
1-G_1G_2G_4
\right)
=
G_1G_2e_0.
\]

Damit:

\[
\boxed{
\frac{x}{e_0}
=
\frac{G_1G_2}
{1-G_1G_2G_4}
}.
\]

Das Minus im Nenner folgt aus der positiven inneren Rückkopplung.

---

## 7.3 Paralleler Ausgangszweig

Nach \(G_2\) wird das Signal parallel durch \(G_3\) und \(G_5\) geführt und addiert:

\[
Y
=
(G_3+G_5)x.
\]

Damit lautet die innere Vorwärtsübertragung:

\[
H
=
\frac{G_1G_2(G_3+G_5)}
{1-G_1G_2G_4}.
\]

---

## 7.4 Äußere negative Rückkopplung

Äußere Summationsstelle:

\[
e_0
=
U-G_6Y.
\]

Ausgang:

\[
Y=He_0.
\]

Einsetzen:

\[
Y=H(U-G_6Y).
\]

\[
Y+HG_6Y=HU.
\]

\[
\frac YU
=
\frac H{1+HG_6}.
\]

Einsetzen von \(H\):

\[
G(s)
=
\frac{
\dfrac{G_1G_2(G_3+G_5)}
{1-G_1G_2G_4}
}{
1+
\dfrac{G_1G_2(G_3+G_5)}
{1-G_1G_2G_4}
G_6
}.
\]

Mit dem Hauptnenner multiplizieren:

\[
\boxed{
G(s)
=
\frac{
G_1G_2(G_3+G_5)
}{
1-G_1G_2G_4
+
G_6G_1G_2(G_3+G_5)
}
}.
\]

Dies stimmt mit der offiziellen Lösung überein.

---

## 7.5 Bewertung der Mitschrift

Die farbige Gruppierung auf PDF-S. 64 ist sinnvoll:

- \(G_1G_2\) als Reihenschaltung,
- \(G_3+G_5\) als Parallelschaltung,
- \(G_4\) als innere positive Rückführung,
- \(G_6\) als äußere negative Rückführung.

### [KORRIGIERT]

In einer handschriftlichen Zwischenzeile erscheint kurzzeitig ein Pluszeichen im Nenner der inneren Schleife. Korrekt ist:

\[
1-G_1G_2G_4.
\]

Das handschriftliche Endergebnis ist dennoch korrekt.

---

# 8. Aufgabe 2b – Differenz zweier Rückführzweige

## 8.1 Struktur

Vorwärtszweig:

\[
U
\rightarrow
\text{Summationsstelle}
\rightarrow
G_1
\rightarrow
Y.
\]

Rückführung:

\[
Y
\rightarrow
G_2
\rightarrow
\begin{cases}
G_3\\
G_4
\end{cases}
\rightarrow
\text{Summationsstellen}.
\]

Die Beiträge von \(G_3\) und \(G_4\) besitzen an der inneren Summationsstelle entgegengesetzte Vorzeichen.

---

## 8.2 Rückführsignal bestimmen

Ausgang von \(G_2\):

\[
r=G_2Y.
\]

Oberer Zweig:

\[
r_3=G_3r=G_2G_3Y.
\]

Unterer Zweig:

\[
r_4=G_4r=G_2G_4Y.
\]

Am inneren Summationspunkt:

\[
h=r_3-r_4.
\]

Somit:

\[
\boxed{
h
=
G_2(G_3-G_4)Y
}.
\]

---

## 8.3 Äußere negative Rückkopplung

\[
e=U-h.
\]

\[
Y=G_1e.
\]

Einsetzen:

\[
Y
=
G_1
\left[
U-G_2(G_3-G_4)Y
\right].
\]

\[
Y
+
G_1G_2(G_3-G_4)Y
=
G_1U.
\]

Ergebnis:

\[
\boxed{
G(s)
=
\frac YU
=
\frac{G_1}
{1+G_1G_2(G_3-G_4)}
}.
\]

Dies stimmt mit der offiziellen Lösung überein.

---

## 8.4 Bewertung der Mitschrift

Auf PDF-S. 65 ist in der farbigen Vorgruppierung zunächst

\[
G_3+G_4
\]

notiert. Das ist falsch, weil die beiden Rückführzweige am linken Summationspunkt unterschiedliche Vorzeichen besitzen.

Die darunterstehende Endformel verwendet korrekt:

\[
G_3-G_4.
\]

---

# 9. Aufgabe 2c – zwei verschachtelte negative Rückkopplungen

## 9.1 Signale definieren

Sei:

- \(e_1\): Ausgang der ersten Summationsstelle,
- \(x_1\): Ausgang von \(G_1\),
- \(e_2\): Ausgang der zweiten Summationsstelle,
- \(x_2\): Ausgang von \(G_2\),
- \(Y\): Ausgang von \(G_3\).

Dann:

\[
e_1
=
U-G_5x_2,
\]

\[
x_1
=
G_1e_1,
\]

\[
e_2
=
x_1-G_4Y,
\]

\[
x_2
=
G_2e_2,
\]

\[
Y
=
G_3x_2.
\]

---

## 9.2 Innere Rückkopplung über \(G_4\)

Aus:

\[
e_2=x_1-G_4Y
\]

und

\[
Y=G_3x_2
\]

folgt:

\[
e_2
=
x_1-G_4G_3x_2.
\]

Mit:

\[
x_2=G_2e_2
\]

erhält man:

\[
x_2
=
G_2
\left(
x_1-G_4G_3x_2
\right).
\]

\[
x_2+G_2G_3G_4x_2
=
G_2x_1.
\]

\[
\boxed{
\frac{x_2}{x_1}
=
\frac{G_2}
{1+G_2G_3G_4}
}.
\]

Die innere Schleife ist negativ, daher steht ein Plus im Nenner.

---

## 9.3 Äußere Rückkopplung über \(G_5\)

Mit:

\[
x_1=G_1e_1
\]

folgt für den Vorwärtsweg von \(e_1\) nach \(x_2\):

\[
H
=
\frac{G_1G_2}
{1+G_2G_3G_4}.
\]

Die äußere Schleife lautet:

\[
e_1=U-G_5x_2.
\]

Damit:

\[
x_2=H(U-G_5x_2).
\]

\[
x_2+HG_5x_2=HU.
\]

\[
\frac{x_2}{U}
=
\frac H{1+HG_5}.
\]

Einsetzen:

\[
\frac{x_2}{U}
=
\frac{
\dfrac{G_1G_2}
{1+G_2G_3G_4}
}{
1+
\dfrac{G_1G_2G_5}
{1+G_2G_3G_4}
}.
\]

Somit:

\[
\frac{x_2}{U}
=
\frac{G_1G_2}
{1+G_2G_3G_4+G_1G_2G_5}.
\]

Da:

\[
Y=G_3x_2,
\]

folgt:

\[
\boxed{
G(s)
=
\frac YU
=
\frac{
G_1G_2G_3
}{
1+G_2G_3G_4+G_1G_2G_5
}
}.
\]

---

## 9.4 Form der offiziellen Lösung

Die offizielle Lösung schreibt:

\[
G(s)
=
\frac{
G_1G_2G_3
}{
1+
G_1G_2G_3
\left(
\frac{G_5}{G_3}
+
\frac{G_4}{G_1}
\right)
}.
\]

Ausmultiplizieren:

\[
G_1G_2G_3
\frac{G_5}{G_3}
=
G_1G_2G_5,
\]

\[
G_1G_2G_3
\frac{G_4}{G_1}
=
G_2G_3G_4.
\]

Damit sind beide Darstellungen identisch.

### Klausurtauglichere Form

\[
\boxed{
G(s)
=
\frac{
G_1G_2G_3
}{
1+G_1G_2G_5+G_2G_3G_4
}
}.
\]

Diese Form enthält keine Quotienten und ist weniger fehleranfällig.

---

## 9.5 Bewertung der Mitschrift

Die Farbcodierung auf PDF-S. 65 zeigt korrekt, dass Rückführblöcke beim Verschieben über Vorwärtsblöcke durch entsprechende Quotienten angepasst werden müssen.

Die handschriftliche Endformel ist korrekt. Für die Klausur ist die direkte Signalglichungs-Methode jedoch robuster als das Verschieben von Abzweig- und Summationspunkten.

---

# 10. Alternative Methode – Blockbild nie umzeichnen, sondern Signalglichungen aufstellen

Bei komplexen Blockbildern ist folgende Methode oft sicherer:

1. Jeden Summationspunkt mit einer Variablen benennen.
2. Jeden Block als Gleichung schreiben.
3. Alle inneren Signale eliminieren.
4. Am Ende \(Y/U\) bilden.

Beispiel:

\[
x_1=G_1e_1,
\qquad
e_2=x_1-G_4Y,
\qquad
x_2=G_2e_2,
\qquad
Y=G_3x_2.
\]

Diese Methode verhindert Fehler durch:

- falsch verschobene Abzweigpunkte,
- vergessene Faktoren,
- veränderte Vorzeichen,
- falsche Rückführsignale.

---

# 11. Typische Fehler in Tutorium 05

1. Positive und negative Rückkopplung verwechseln.
2. Minus am Summationspunkt nicht in die Parallelzusammenfassung übernehmen.
3. Bei positiver Rückkopplung fälschlich \(1+GH\) verwenden.
4. Bei negativer Rückkopplung fälschlich \(1-GH\) verwenden.
5. Eine innere Schleife schließen, ohne die äußeren Abzweigpunkte zu beachten.
6. Rückführblöcke beim Verschieben über einen Vorwärtsblock nicht anpassen.
7. Parallelzweige addieren, obwohl einer negativ eingespeist wird.
8. \(1/(Ts)\) als PT1 statt als I-Glied klassifizieren.
9. \(1+Ts\) nur als D-Glied statt als PD-Glied erkennen.
10. \(1/(Ts+1)^2\) nicht als zwei PT1 bzw. PT2 mit Doppelpol erkennen.
11. \(T_1s/(T_2s+1)\) nicht als DT1 erkennen.
12. Beim Viertelfahrzeug den Dämpfer als Energiespeicher zählen.
13. „Zwei physikalische Bauteile“ mit „System zweiter Ordnung“ gleichsetzen, ohne die tatsächlich unabhängigen Speicher zu prüfen.
14. Das Blockbild nur visuell vereinfachen, ohne das Ergebnis durch Signalglichungen zu kontrollieren.

---

# 12. Klausurstrategie

## 12.1 Elementklassifikation

1. Funktion vollständig faktorisieren.
2. Konstanten ausklammern.
3. Faktoren einzeln zuordnen:
   - \(K\): P,
   - \(1/s\): I,
   - \(s\): D,
   - \(e^{-T_ts}\): Totzeit,
   - \(1/(Ts+1)\): PT1.
4. Kombination benennen:
   - I + PT1 in Reihe: IT1,
   - D + PT1 in Reihe: DT1,
   - P + D parallel: PD,
   - zwei PT1: PT2 bzw. PT1-Kaskade.
5. Pole und Nullstellen als Kontrolle bestimmen.

## 12.2 Blockschaltbilder

1. Vorzeichen an jedem Summationspunkt markieren.
2. Innere Schleife suchen.
3. Innere Schleife mit

\[
\frac G{1\pm GH}
\]

zusammenfassen.
4. Reihen multiplizieren.
5. Parallelen mit Vorzeichen addieren.
6. Äußere Schleife schließen.
7. Ergebnis mit Signalglichungen kontrollieren.
8. Doppelbrüche beseitigen.

---

# 13. Qualitätsprüfung der Quellen

## Fachlich korrekt und vollständig

- offizielle Klassifikation von Aufgabe 1a–g,
- offizielle Endergebnisse von Aufgabe 2a–c,
- handschriftliche Endformeln zu Aufgabe 2a–c.

## Handschriftliche Zwischenfehler

1. Aufgabe 2a:
   In einer Zwischenzeile ist das Vorzeichen des inneren Rückkopplungsnenners kurzzeitig falsch. Endergebnis korrekt.

2. Aufgabe 2b:
   Die farbige Vorgruppierung schreibt \(G_3+G_4\). Korrekt ist wegen der Summationszeichen:

\[
G_3-G_4.
\]

3. Aufgabe 2c:
   Die Quotientenschreibweise ist korrekt, aber unnötig kompliziert. Die vollständig ausmultiplizierte Nennerform ist sicherer.

## Ergänzende Herleitung

Die Theoriefrage zum Viertelfahrzeug besitzt keine offizielle Musterlösung. Die obige Antwort ist eine physikalische Herleitung aus dem abgebildeten Masse-Feder-Dämpfer-Modell und wird nicht als direktes Zitat der Vorlesung ausgegeben.

---

# 14. NotebookLM-Verifikation

--- NOTEBOOKLM-PROMPT ---

Prüfe ausschließlich anhand der hochgeladenen offiziellen Regelungstechnik-Unterlagen die folgenden Punkte aus „Tutorium 05 – Grundlegende Übertragungselemente und Rechnen mit Blockschaltbildern“:

1. Theoriefrage Viertelfahrzeug:
Gibt es in den Quellen eine offizielle Musterantwort zur qualitativen Klassifikation des Masse-Feder-Dämpfer-Systems mit Straßenoberfläche als Eingang und Stoßstangenabstand als Ausgang? Falls ja, gib die genaue Systemordnung, Elementklassifikation und Bedingung für Schwingungsfähigkeit an. Falls keine Musterantwort existiert, sage das ausdrücklich.

2. Aufgabe 2a:
Prüfe anhand der Summationszeichen, ob die innere Rückkopplung über \(G_4\) positiv ist und deshalb der Nenner
\[
1-G_1G_2G_4
\]
lauten muss.

3. Aufgabe 2b:
Prüfe, ob die Rückführzweige \(G_3\) und \(G_4\) am linken Summationspunkt addiert oder subtrahiert werden. Begründe dies ausschließlich mit den eingezeichneten Vorzeichen.

4. Aufgabe 2c:
Zeige algebraisch, dass
\[
1+G_1G_2G_3
\left(
\frac{G_5}{G_3}
+
\frac{G_4}{G_1}
\right)
\]
identisch ist mit
\[
1+G_1G_2G_5+G_2G_3G_4.
\]

Belege jede Quellenaussage mit Dokumentname und genauer Seite. Trenne Quellenaussage und eigene algebraische Prüfung.

--- ENDE ---

---

# 15. Kompaktformelsammlung Tutorium 05

## Reihenschaltung

\[
\boxed{
G_{\mathrm{ges}}
=
G_1G_2
}.
\]

## Parallelschaltung

\[
\boxed{
G_{\mathrm{ges}}
=
G_1\pm G_2
}.
\]

## Negative Rückkopplung

\[
\boxed{
G_{\mathrm{ges}}
=
\frac G{1+GH}
}.
\]

## Positive Rückkopplung

\[
\boxed{
G_{\mathrm{ges}}
=
\frac G{1-GH}
}.
\]

## P-Glied

\[
G(s)=K_P.
\]

## I-Glied

\[
G(s)=\frac1{T_Is}.
\]

## D-Glied

\[
G(s)=T_Ds.
\]

## Totzeitglied

\[
G(s)=e^{-T_ts}.
\]

## PT1

\[
G(s)=\frac{K_P}{Ts+1}.
\]

## PT2

\[
G(s)
=
\frac{K_P}{(T_1s+1)(T_2s+1)}.
\]

## IT1

\[
G(s)
=
\frac1{T_1s(T_2s+1)}.
\]

## DT1

\[
G(s)
=
\frac{T_1s}{T_2s+1}.
\]

## Schwingungsbedingung Masse-Feder-Dämpfer

\[
\boxed{
d^2<4mc
}.
\]

---

# Tutorium 06 – Frequenzganganalyse

## 1. Quellen und Seitenbereich

### Primärquellen

1. **RT-Tutorien-Mitschrift.pdf**, PDF-Seiten 67–81
   - S. 67: Theoriefragen
   - S. 68: Aufgabe 1 – vorgegebene Übertragungsfunktionen
   - S. 69–73: Aufgabe 2 – Bode-Diagramme, Reserven und handschriftliche Auswertung
   - S. 74–75: ausführliche Theorie zu Durchtrittsfrequenzen, Reserven und offenem Kreis
   - S. 75–77: Rechenwege zu Aufgabe 1a–c
   - S. 78–79: Fotos der Tafelbilder zu den kombinierten Bode-Diagrammen
   - S. 80–81: leer
   - Tutorium 07 beginnt auf PDF-Seite 82.

2. **Regelungstechnik_Tutorium_komplett.pdf**, PDF-Seiten 33–45  
   Tutorium 06, Blattseiten 1/13–13/13, offizielle Aufgaben, Bode-Diagramme und Endlösungen.

3. **skript.pdf**
   - PDF-S. 90–92: Amplitudenreserve und Berechnungsalgorithmus
   - PDF-S. 93–94: Phasenreserve und Berechnungsalgorithmus

---

# 2. Grundidee der Frequenzganganalyse

Für eine offene Kreisübertragungsfunktion

\[
G_0(s)
\]

wird der Frequenzgang

\[
G_0(j\omega)
\]

untersucht.

Bei negativer Einheitsrückführung lautet die geschlossene Übertragungsfunktion

\[
\boxed{
G_{\mathrm{cl}}(s)
=
\frac{G_0(s)}{1+G_0(s)}
}.
\]

Die Stabilität des geschlossenen Kreises hängt damit wesentlich vom Nenner

\[
1+G_0(s)
\]

ab.

Kritisch wird der Punkt

\[
\boxed{
G_0(j\omega)=-1
}
\]

denn dann gilt

\[
1+G_0(j\omega)=0.
\]

Der Punkt \(-1\) entspricht gleichzeitig:

\[
|G_0(j\omega)|=1
\]

und

\[
\arg G_0(j\omega)=-180^\circ.
\]

Im Bode-Diagramm bedeutet das:

\[
\boxed{
|G_0(j\omega)|_{\mathrm{dB}}=0\,\mathrm{dB}
}
\]

und

\[
\boxed{
\varphi(\omega)=-180^\circ
}.
\]

---

# 3. Theoriefragen

## 3.1 Warum wird die Stabilität bei \(-180^\circ\) kritisch?

Bei einer normalen negativen Rückkopplung wird das Ausgangssignal am Summationspunkt subtrahiert.

Erzeugt die offene Kette zusätzlich eine Phasenverschiebung von

\[
-180^\circ,
\]

kehrt sich das rückgeführte Signal nochmals um. Die negative Rückkopplung wirkt dadurch effektiv wie eine positive Rückkopplung.

Entscheidend ist zusätzlich der Betrag:

### Fall 1: Betrag kleiner als 1

\[
|G_0(j\omega)|<1.
\]

Das rückgeführte Signal wird bei jedem Umlauf abgeschwächt. Die Störung klingt ab.

### Fall 2: Betrag gleich 1

\[
|G_0(j\omega)|=1.
\]

Das Signal kommt mit gleicher Stärke und entgegengesetzter Phase zurück. Der Kreis ist kritisch bzw. grenzstabil.

### Fall 3: Betrag größer als 1

\[
|G_0(j\omega)|>1.
\]

Das Signal wird bei jedem Umlauf verstärkt. Schwingungen können anwachsen und der Kreis instabil werden.

Klausurtaugliche Kurzantwort:

\[
\boxed{
-180^\circ
\text{ macht die negative Rückkopplung zur positiven Rückkopplung.}
}
\]

Instabilitätskritisch wird dies zusammen mit

\[
|G_0| \ge 1.
\]

Die Mitschrift erläutert dieses Prinzip auf PDF-S. 74–75.

---

## 3.2 Warum braucht man Phasenreserve und Amplitudenreserve?

Beide Reserven messen unterschiedliche Robustheitsrichtungen.

### Phasenreserve

Sie beantwortet:

> Wie viel zusätzliche Phasenverzögerung darf auftreten, bevor der kritische Punkt erreicht wird?

Typische Ursachen für zusätzliche negative Phase:

- Totzeiten,
- Filter,
- nicht modellierte Dynamik,
- höhere Pole,
- Abtast- und Rechenverzögerungen.

### Amplitudenreserve

Sie beantwortet:

> Um welchen Faktor bzw. um wie viele dB darf die Kreisverstärkung steigen, bevor der kritische Punkt erreicht wird?

Typische Ursachen für Verstärkungsänderungen:

- Parameterstreuungen,
- Arbeitspunktänderungen,
- Laständerungen,
- falsch geschätzte statische Verstärkung.

Ein System kann eine große Phasenreserve, aber eine geringe Amplitudenreserve besitzen oder umgekehrt. Nur eine Reserve zu betrachten ist daher unvollständig.

---

## 3.3 Warum untersucht man die Reserven im offenen Kreis?

Die geschlossene Kreisübertragungsfunktion besitzt den Nenner

\[
1+G_0(s).
\]

Der kritische Zustand entsteht daher, wenn

\[
G_0(s)=-1.
\]

Genau dieser Abstand zum kritischen Punkt lässt sich aus dem offenen Kreis direkt mit Bode- oder Nyquist-Diagramm untersuchen.

Vorteile:

1. Die offenen Teilglieder können einfach multipliziert werden.
2. Beträge in dB und Phasen können addiert werden.
3. Die geschlossene Stabilität wird über den Abstand von \(G_0\) zum kritischen Punkt beurteilt.
4. Regler- und Streckenänderungen lassen sich getrennt analysieren.

### Einschränkung

Positive Reserven sind kein universeller Stabilitätsbeweis für beliebige Systeme mit instabilen offenen Polen oder mehreren Durchtritten. In solchen Fällen ist das vollständige Nyquist-Kriterium maßgeblich.

---

# 4. Definitionen der Durchtrittsfrequenzen

## 4.1 Gain-Durchtrittsfrequenz

Die Gain-Durchtrittsfrequenz \(\omega_g\) erfüllt

\[
\boxed{
|G_0(j\omega_g)|=1
}
\]

bzw.

\[
\boxed{
|G_0(j\omega_g)|_{\mathrm{dB}}=0\,\mathrm{dB}
}.
\]

---

## 4.2 Phasen-Durchtrittsfrequenz

Die Phasen-Durchtrittsfrequenz \(\omega_p\) erfüllt

\[
\boxed{
\varphi(\omega_p)=-180^\circ
}.
\]

---

# 5. Phasenreserve

An der Gain-Durchtrittsfrequenz wird die vorhandene Phase bestimmt.

\[
\boxed{
\Delta\varphi
=
180^\circ+\varphi(\omega_g)
}.
\]

Beispiel:

\[
\varphi(\omega_g)=-150^\circ
\]

liefert

\[
\Delta\varphi
=
180^\circ-150^\circ
=
30^\circ.
\]

Interpretation:

- \(\Delta\varphi>0\): positiver Abstand zur kritischen Phase,
- \(\Delta\varphi=0\): Grenzfall,
- \(\Delta\varphi<0\): nach der einfachen Bode-Betrachtung kritisch bzw. instabil.

Quelle: `skript.pdf`, PDF-S. 93–94, Algorithmus 3.48.

---

# 6. Amplitudenreserve

An der Phasen-Durchtrittsfrequenz wird der Amplitudengang bestimmt.

In dB:

\[
\boxed{
\Delta A
=
-|G_0(j\omega_p)|_{\mathrm{dB}}
}.
\]

Im linearen Maß:

\[
\boxed{
A_R
=
\frac1{|G_0(j\omega_p)|}
}.
\]

Zusammenhang:

\[
\Delta A
=
20\log_{10}(A_R).
\]

Beispiel:

\[
|G_0(j\omega_p)|_{\mathrm{dB}}
=
-20\,\mathrm{dB}
\]

liefert

\[
\Delta A=20\,\mathrm{dB}.
\]

Interpretation:

- \(\Delta A>0\): Verstärkung darf noch steigen,
- \(\Delta A=0\): Grenzfall,
- \(\Delta A<0\): kritischer Punkt wurde bereits überschritten.

Quelle: `skript.pdf`, PDF-S. 90–92, Algorithmus 3.46.

---

# 7. Wann ist eine Reserve nicht definiert?

## Amplitudenreserve

Wenn der Phasengang

\[
-180^\circ
\]

bei keiner endlichen Frequenz erreicht, existiert keine endliche Phasen-Durchtrittsfrequenz.

Dann ist die Amplitudenreserve nach der Terminologie des Tutoriums:

\[
\boxed{\text{nicht definiert}}.
\]

In anderer Literatur wird teilweise von einer unendlichen Amplitudenreserve gesprochen. In dieser Veranstaltung sollte die Formulierung der offiziellen Unterlagen verwendet werden.

## Phasenreserve

Wenn der Amplitudengang nie

\[
0\,\mathrm{dB}
\]

schneidet, ist keine endliche Gain-Durchtrittsfrequenz vorhanden und die Phasenreserve entsprechend nicht definiert.

---

# 8. Übertragungsfunktion aus einem Bode-Diagramm rekonstruieren

## Schritt 1: Anfangssteigung bestimmen

- \(0\,\mathrm{dB/Dekade}\): P-Verhalten
- \(-20\,\mathrm{dB/Dekade}\): ein I-Anteil oder ein aktiver Pol
- \(+20\,\mathrm{dB/Dekade}\): ein D-Anteil oder eine aktive Nullstelle
- \(-40\,\mathrm{dB/Dekade}\): zwei mehr Pole als Nullstellen

## Schritt 2: Steigungsänderungen auswerten

- Änderung um \(-20\,\mathrm{dB/Dekade}\): zusätzlicher PT1-Pol
- Änderung um \(+20\,\mathrm{dB/Dekade}\): zusätzliche Nullstelle bzw. PD-Faktor

## Schritt 3: Eckfrequenzen ablesen

Für einen Faktor

\[
1+Ts
\]

gilt

\[
\boxed{
T=\frac1{\omega_E}
}.
\]

## Schritt 4: Verstärkung bestimmen

- konstantes Niveau bei niedrigen Frequenzen,
- \(0\,\mathrm{dB}\Rightarrow K=1\),
- \(20\,\mathrm{dB}\Rightarrow K=10\),
- \(-20\,\mathrm{dB}\Rightarrow K=0.1\).

## Schritt 5: Phase als Kontrolle verwenden

- I-Glied: \(-90^\circ\)
- D-Glied: \(+90^\circ\)
- PT1-Pol: \(0^\circ\to-90^\circ\)
- Nullstelle: \(0^\circ\to+90^\circ\)
- negatives P-Glied: zusätzlicher Phasensprung um \(180^\circ\)

---

# 9. Aufgabe 1a – \(F(s)=1000/s\)

## 9.1 Glied erkennen

\[
F(s)
=
\frac{1000}{s}.
\]

Dies ist ein I-Glied mit Verstärkung

\[
K_I=1000.
\]

---

## 9.2 Frequenzgang

\[
F(j\omega)
=
\frac{1000}{j\omega}
=
-j\frac{1000}{\omega}.
\]

Betrag:

\[
\boxed{
|F(j\omega)|
=
\frac{1000}{\omega}
}.
\]

Phase:

\[
\boxed{
\varphi(\omega)=-90^\circ
}.
\]

---

## 9.3 dB-Darstellung

\[
L(\omega)
=
20\log_{10}\left(\frac{1000}{\omega}\right).
\]

\[
L(\omega)
=
20\log_{10}(1000)-20\log_{10}\omega.
\]

Da

\[
20\log_{10}(1000)=60\,\mathrm{dB},
\]

folgt:

\[
\boxed{
L(\omega)
=
60-20\log_{10}\omega
}.
\]

Steigung:

\[
\boxed{-20\,\mathrm{dB/Dekade}}.
\]

---

## 9.4 Gain-Durchtrittsfrequenz

\[
\frac{1000}{\omega_g}=1.
\]

\[
\boxed{
\omega_g=1000\,\mathrm{s^{-1}}
}.
\]

Die Mitschrift auf PDF-S. 76 enthält diesen Rechenweg vollständig und korrekt.

---

# 10. Aufgabe 1b – \(F(s)=1/(1+100s)\)

## 10.1 Glied erkennen

\[
F(s)
=
\frac1{1+100s}.
\]

PT1-Glied mit

\[
K=1,
\qquad
T=100.
\]

Eckfrequenz:

\[
\boxed{
\omega_E=\frac1{100}=0.01\,\mathrm{s^{-1}}
}.
\]

---

## 10.2 Betrag und Phase

\[
F(j\omega)
=
\frac1{1+j100\omega}.
\]

\[
\boxed{
|F(j\omega)|
=
\frac1{\sqrt{1+(100\omega)^2}}
}.
\]

\[
\boxed{
\varphi(\omega)
=
-\arctan(100\omega)
}.
\]

dB:

\[
\boxed{
L(\omega)
=
-10\log_{10}
\left[
1+(100\omega)^2
\right]
}.
\]

Asymptoten:

- \(\omega<0.01\): ungefähr \(0\,\mathrm{dB}\)
- \(\omega>0.01\): \(-20\,\mathrm{dB/Dekade}\)

Phase:

- niedrige Frequenzen: \(0^\circ\)
- bei \(\omega_E\): \(-45^\circ\)
- hohe Frequenzen: \(-90^\circ\)

Die Mitschrift auf PDF-S. 76–77 ist korrekt.

---

# 11. Aufgabe 1c – \(F(s)=\frac{100}{s}\frac1{1+10s}\)

## 11.1 Zerlegung

\[
F(s)
=
\underbrace{\frac{100}{s}}_{\text{I-Glied}}
\cdot
\underbrace{\frac1{1+10s}}_{\text{PT1-Glied}}.
\]

PT1-Eckfrequenz:

\[
\boxed{
\omega_E=\frac1{10}=0.1\,\mathrm{s^{-1}}
}.
\]

---

## 11.2 Betrag

\[
\boxed{
|F(j\omega)|
=
\frac{100}
{\omega\sqrt{1+(10\omega)^2}}
}.
\]

dB:

\[
\boxed{
L(\omega)
=
40
-
20\log_{10}\omega
-
10\log_{10}
\left[
1+(10\omega)^2
\right]
}.
\]

Asymptotische Steigungen:

- unterhalb \(0.1\): \(-20\,\mathrm{dB/Dekade}\)
- oberhalb \(0.1\): \(-40\,\mathrm{dB/Dekade}\)

---

## 11.3 Phase

\[
\boxed{
\varphi(\omega)
=
-90^\circ-\arctan(10\omega)
}.
\]

Damit:

- niedrige Frequenzen: \(-90^\circ\)
- bei \(\omega_E\): \(-135^\circ\)
- hohe Frequenzen: \(-180^\circ\)

Die Mitschrift auf PDF-S. 77 beschreibt die Addition der I- und PT1-Beiträge korrekt.

---

# 12. Aufgabe 1d – \(F(s)=\frac1{10s}(100s+1)\)

## 12.1 Zerlegung

\[
F(s)
=
\underbrace{\frac1{10s}}_{\text{I-Glied}}
\cdot
\underbrace{(1+100s)}_{\text{PD-/Nullstellenfaktor}}.
\]

Nullstellen-Eckfrequenz:

\[
\boxed{
\omega_E=\frac1{100}=0.01\,\mathrm{s^{-1}}
}.
\]

---

## 12.2 Betrag

\[
\boxed{
|F(j\omega)|
=
\frac{\sqrt{1+(100\omega)^2}}
{10\omega}
}.
\]

dB:

\[
\boxed{
L(\omega)
=
-20\log_{10}(10\omega)
+
10\log_{10}
\left[
1+(100\omega)^2
\right]
}.
\]

Asymptoten:

- unterhalb \(0.01\): \(-20\,\mathrm{dB/Dekade}\)
- oberhalb \(0.01\): \(0\,\mathrm{dB/Dekade}\)

Hochfrequenzverstärkung:

\[
\lim_{\omega\to\infty}|F(j\omega)|
=
\frac{100}{10}
=
10.
\]

Also:

\[
\boxed{
L(\infty)=20\,\mathrm{dB}
}.
\]

---

## 12.3 Phase

\[
\boxed{
\varphi(\omega)
=
-90^\circ+\arctan(100\omega)
}.
\]

Damit:

- niedrige Frequenzen: \(-90^\circ\)
- hohe Frequenzen: \(0^\circ\)

---

# 13. Aufgabe 1e – negatives P-, I- und PT1-Glied

## Gegeben

\[
F(s)
=
-0.1
\cdot
\frac1s
\cdot
\frac1{1+10s}.
\]

Zerlegung:

- negatives P-Glied \(K=-0.1\),
- I-Glied,
- PT1-Glied mit \(T=10\).

Eckfrequenz:

\[
\boxed{
\omega_E=0.1\,\mathrm{s^{-1}}
}.
\]

---

## 13.1 Betrag

Das negative Vorzeichen beeinflusst den Betrag nicht:

\[
\boxed{
|F(j\omega)|
=
\frac{0.1}
{\omega\sqrt{1+(10\omega)^2}}
}.
\]

dB:

\[
\boxed{
L(\omega)
=
-20
-
20\log_{10}\omega
-
10\log_{10}
\left[
1+(10\omega)^2
\right]
}.
\]

Asymptoten:

- unterhalb \(0.1\): \(-20\,\mathrm{dB/Dekade}\)
- oberhalb \(0.1\): \(-40\,\mathrm{dB/Dekade}\)

---

## 13.2 Phase und Phasenwicklung

Beiträge:

- negatives P-Glied: \(180^\circ\),
- I-Glied: \(-90^\circ\),
- PT1-Glied: \(-\arctan(10\omega)\).

Damit in einer passenden Hauptwertdarstellung:

\[
\boxed{
\varphi(\omega)
=
90^\circ-\arctan(10\omega)
}.
\]

Die Phase läuft daher von

\[
+90^\circ
\]

gegen

\[
0^\circ.
\]

Äquivalent kann dieselbe Phase um \(360^\circ\) verschoben als negativer Verlauf dargestellt werden. Beim Addieren von Phasen muss daher auf die gewählte Phasenwicklung geachtet werden.

Die offizielle Diagrammlösung zeigt den Gesamtverlauf gewickelt von \(+90^\circ\) nach \(0^\circ\).

---

# 14. Aufgabe 2a – PD-Glied aus dem Bode-Diagramm

## 14.1 Struktur ablesen

Amplitudengang:

- niedrige Frequenzen: \(0\,\mathrm{dB}\)
- ab \(\omega=10^3\): \(+20\,\mathrm{dB/Dekade}\)

Phase:

- \(0^\circ\)
- danach Übergang gegen \(+90^\circ\)

Daraus:

\[
K=1,
\]

\[
\omega_E=1000.
\]

\[
T=\frac1{1000}.
\]

Übertragungsfunktion:

\[
\boxed{
F(s)
=
1+\frac{s}{1000}
}.
\]

---

## 14.2 Reserven

Der Phasengang erreicht \(-180^\circ\) nicht.

\[
\boxed{
\Delta A
\text{ ist nicht definiert}
}.
\]

Der \(0\,\mathrm{dB}\)-Durchtritt wird in der asymptotischen Darstellung bei Phase \(0^\circ\) angesetzt.

\[
\boxed{
\Delta\varphi=180^\circ
}.
\]

Die handschriftliche Herleitung auf PDF-S. 69 ist korrekt.

---

# 15. Aufgabe 2b – PT1-Glied aus dem Bode-Diagramm

## 15.1 Struktur

- Anfangsniveau: \(0\,\mathrm{dB}\Rightarrow K=1\)
- Knick bei

\[
\omega_E=0.1
\]

- danach \(-20\,\mathrm{dB/Dekade}\)
- Phase \(0^\circ\to-90^\circ\)

Damit:

\[
T=\frac1{0.1}=10.
\]

Übertragungsfunktion:

\[
\boxed{
F(s)
=
\frac1{1+10s}
}.
\]

---

## 15.2 Reserven

Die Phase erreicht \(-180^\circ\) nicht.

\[
\boxed{
\Delta A
\text{ ist nicht definiert}
}.
\]

Der asymptotische \(0\,\mathrm{dB}\)-Bereich besitzt Phase \(0^\circ\).

\[
\boxed{
\Delta\varphi=180^\circ
}.
\]

### [KORRIGIERT]

Auf PDF-S. 70 stehen nebeneinander zunächst

\[
\Delta A=0
\]

und anschließend „nicht definiert“. Fachlich und offiziell korrekt ist ausschließlich:

\[
\boxed{
\Delta A
\text{ nicht definiert}
}.
\]

---

# 16. Aufgabe 2c – zwei PT1-Glieder

## 16.1 Struktur aus den Knicken

Amplitudengang:

- bis \(10^{-2}\): \(0\,\mathrm{dB}\)
- ab \(10^{-2}\): \(-20\,\mathrm{dB/Dekade}\)
- ab \(10^0\): \(-40\,\mathrm{dB/Dekade}\)

Somit zwei PT1-Glieder mit

\[
\omega_{E1}=10^{-2},
\qquad
\omega_{E2}=1.
\]

Zeitkonstanten:

\[
T_1=100,
\qquad
T_2=1.
\]

Übertragungsfunktion:

\[
\boxed{
F(s)
=
\frac1{(1+100s)(1+s)}
}.
\]

---

## 16.2 Offizielle grafisch-asymptotische Reserven

Die offizielle Lösung nimmt einen Phasendurchtritt von

\[
-180^\circ
\]

bei

\[
\omega=100
\]

an.

Dort beträgt der asymptotische Amplitudengang:

\[
-40\,\mathrm{dB}.
\]

Daher:

\[
\boxed{
\Delta A=40\,\mathrm{dB}
}
\]

unter dieser ausdrücklich genannten Annahme.

Die offizielle Phasenreserve lautet:

\[
\boxed{
\Delta\varphi=180^\circ
}.
\]

---

## 16.3 Exakte mathematische Einordnung

Für die exakte Funktion gilt:

\[
\varphi(\omega)
=
-\arctan(100\omega)
-\arctan(\omega).
\]

Für jede endliche Frequenz ist

\[
\varphi(\omega)>-180^\circ.
\]

Die Phase nähert sich \(-180^\circ\) nur asymptotisch für

\[
\omega\to\infty.
\]

Damit existiert streng mathematisch keine endliche Phasen-Durchtrittsfrequenz.

Die offizielle Reserve von \(40\,\mathrm{dB}\) ist daher eine Auswertung der idealisierten asymptotischen Bode-Skizze und kein exakter Frequenzgangwert.

Diese Unterscheidung muss in einer Klausur beachtet werden:

- Wird ausdrücklich **grafisch aus der gegebenen asymptotischen Skizze** abgelesen, der offiziellen Konvention folgen.
- Wird die exakte Funktion analysiert, ist kein endlicher \(-180^\circ\)-Durchtritt vorhanden.

---

# 17. Aufgabe 2d – PD- und PT1-Glied

## 17.1 Struktur

Amplitudengang:

- bis \(\omega=1\): \(0\,\mathrm{dB}\)
- von \(1\) bis \(100\): \(+20\,\mathrm{dB/Dekade}\)
- ab \(100\): konstant \(40\,\mathrm{dB}\)

Phase:

- \(0^\circ\)
- nach der Nullstelle \(+90^\circ\)
- nach dem Pol wieder \(0^\circ\)

Nullstelle:

\[
\omega_z=1
\Rightarrow
T_z=1.
\]

Pol:

\[
\omega_p=100
\Rightarrow
T_p=0.01.
\]

Übertragungsfunktion:

\[
\boxed{
F(s)
=
\frac{1+s}{1+0.01s}
}.
\]

Gleichwertig zur offiziellen Schreibweise:

\[
F(s)
=
(s+1)
\cdot
\frac1{1+\frac1{100}s}.
\]

---

## 17.2 Reserven

Die Phase erreicht \(-180^\circ\) nicht:

\[
\boxed{
\Delta A
\text{ nicht definiert}
}.
\]

Bei der asymptotischen \(0\,\mathrm{dB}\)-Stelle ist die Phase \(0^\circ\):

\[
\boxed{
\Delta\varphi=180^\circ
}.
\]

Die Mitschrift auf PDF-S. 72 identifiziert die Teilglieder korrekt.

---

# 18. Aufgabe 2e – I-, PT1- und PD-Glied

## 18.1 Struktur aus dem Diagramm

Amplitudengang:

- niedrige Frequenzen: \(-20\,\mathrm{dB/Dekade}\)
- ab \(\omega=1\): \(-40\,\mathrm{dB/Dekade}\)
- ab \(\omega=100\): wieder \(-20\,\mathrm{dB/Dekade}\)

Daraus:

1. I-Glied,
2. PT1-Pol bei \(\omega=1\),
3. Nullstelle bei \(\omega=100\).

Der I-Anteil besitzt aus dem Niveau die Verstärkung

\[
\frac1{0.1s}
=
\frac{10}{s}.
\]

Somit:

\[
\boxed{
F(s)
=
\frac1{0.1s}
\cdot
\frac1{1+s}
\cdot
(1+0.01s)
}.
\]

Zusammengefasst:

\[
\boxed{
F(s)
=
\frac{10(1+0.01s)}
{s(1+s)}
}.
\]

---

## 18.2 Offizielle Lösung

Die offizielle Lösung nennt:

\[
\Delta\varphi=0^\circ
\]

und

\[
\Delta A=-20\,\mathrm{dB}
\]

unter Annahme eines \(-180^\circ\)-Durchtritts bei

\[
\omega=100.
\]

---

## 18.3 Widerspruch in der offiziellen Lösung

Diese Angaben passen nicht zum gezeichneten asymptotischen Diagramm:

### Problem 1: falsches Vorzeichen

Bei einem Amplitudenwert von

\[
-20\,\mathrm{dB}
\]

würde nach der offiziellen Definition gelten:

\[
\Delta A
=
-(-20\,\mathrm{dB})
=
+20\,\mathrm{dB}.
\]

Nicht:

\[
-20\,\mathrm{dB}.
\]

### Problem 2: falsche Frequenz

Im Diagramm beträgt der asymptotische Amplitudenwert bei

\[
\omega=100
\]

etwa

\[
-60\,\mathrm{dB},
\]

nicht \(-20\,\mathrm{dB}\).

Der Wert

\[
-20\,\mathrm{dB}
\]

liegt bei ungefähr

\[
\omega=10.
\]

### Handschriftliche Korrektur

Die Mitschrift auf PDF-S. 73 verwendet:

\[
\omega=10,
\]

\[
L(\omega)=-20\,\mathrm{dB},
\]

und folgert:

\[
\boxed{
\Delta A=20\,\mathrm{dB}
}
\]

sowie

\[
\boxed{
\Delta\varphi=0^\circ
}
\]

für die idealisierte asymptotische Darstellung.

Diese handschriftliche Auswertung ist mit der gezeichneten asymptotischen Kurve konsistenter als die gedruckte Endlösung.

---

## 18.4 Exakte Frequenzganganalyse

Exakter Betrag:

\[
|F(j\omega)|
=
\frac{10\sqrt{1+(0.01\omega)^2}}
{\omega\sqrt{1+\omega^2}}.
\]

Exakte Phase:

\[
\boxed{
\varphi(\omega)
=
-90^\circ
-\arctan(\omega)
+\arctan(0.01\omega)
}.
\]

Die minimale Phase liegt bei

\[
\omega=10.
\]

Dann:

\[
\varphi(10)
=
-90^\circ
-\arctan(10)
+\arctan(0.1).
\]

Numerisch:

\[
\boxed{
\varphi_{\min}
\approx
-168.58^\circ
}.
\]

Die exakte Phase erreicht also niemals

\[
-180^\circ.
\]

Daher ist die exakte Amplitudenreserve:

\[
\boxed{
\text{nicht definiert}
}.
\]

---

## 18.5 Exakte Phasenreserve

Die Gain-Durchtrittsfrequenz folgt aus:

\[
|F(j\omega_g)|=1.
\]

Quadratisch umgeformt:

\[
100
\left(
1+0.0001\omega_g^2
\right)
=
\omega_g^2
\left(
1+\omega_g^2
\right).
\]

Mit

\[
x=\omega_g^2
\]

ergibt sich:

\[
x^2+0.99x-100=0.
\]

Positive Lösung:

\[
x\approx9.5172.
\]

Daher:

\[
\boxed{
\omega_g\approx3.085\,\mathrm{s^{-1}}
}.
\]

Phase dort:

\[
\varphi(\omega_g)
\approx
-160.27^\circ.
\]

Somit:

\[
\boxed{
\Delta\varphi
\approx
19.73^\circ
}.
\]

### Konsequenz

Für Aufgabe 2e existieren drei Ebenen:

1. **gedruckte offizielle Endlösung:** intern widersprüchlich,
2. **handschriftlich-asymptotische Auswertung:** \(\Delta A=20\,\mathrm{dB}\), \(\Delta\varphi=0^\circ\),
3. **exakte Analyse:** keine endliche Amplitudenreserve, \(\Delta\varphi\approx19.7^\circ\).

In einer Aufgabe mit vorgegebenem asymptotischem Diagramm ist die grafische Methode gemeint. Der Widerspruch in der gedruckten Lösung darf aber nicht unkommentiert übernommen werden.

---

# 19. Mehrere Durchtritte und kritische Reserve

Wenn ein Bode-Diagramm mehrere \(0\,\mathrm{dB}\)- oder \(-180^\circ\)-Durchtritte besitzt:

1. alle Durchtritte bestimmen,
2. zu jedem Durchtritt die zugehörige Reserve berechnen,
3. den kritischsten, also kleinsten positiven Abstand verwenden.

Ein einzelner willkürlich gewählter Durchtritt kann zu einer falschen Stabilitätsbewertung führen.

---

# 20. Qualitätsprüfung der Mitschrift

## Sicher lesbar und fachlich korrekt

- Definition von \(\omega_g\) und \(\omega_p\) auf PDF-S. 74
- Formeln für Phasen- und Amplitudenreserve auf PDF-S. 74
- Erklärung der kritischen Rückkopplung bei \(-180^\circ\) auf PDF-S. 74–75
- Begründung der offenen Kreisbetrachtung auf PDF-S. 75
- vollständige Rechnung zu Aufgabe 1a auf PDF-S. 75–76
- PT1-Auswertung zu Aufgabe 1b auf PDF-S. 76–77
- qualitative Addition von I- und PT1-Anteil zu Aufgabe 1c auf PDF-S. 77

## Diagrammbezogene Auswertungen

- Aufgabe 2a: PDF-S. 69
- Aufgabe 2b: PDF-S. 70
- Aufgabe 2c: PDF-S. 71
- Aufgabe 2d: PDF-S. 72
- Aufgabe 2e: PDF-S. 73

## Nicht inhaltstragend

- PDF-S. 78–79 enthalten Tafelbilder ohne zusätzliche neue Endformeln.
- PDF-S. 80–81 sind leer.

---

# 21. Festgestellte Fehler und Unklarheiten

1. **Aufgabe 2b, Mitschrift:**  
   Kurzzeitig steht \(\Delta A=0\), danach korrekt „nicht definiert“.

2. **Aufgabe 2c, offizielle Lösung:**  
   Die Amplitudenreserve von \(40\,\mathrm{dB}\) beruht ausdrücklich auf einer asymptotischen Annahme. Exakt existiert kein endlicher \(-180^\circ\)-Durchtritt.

3. **Aufgabe 2e, offizielle Lösung:**  
   Vorzeichen, Frequenz und Amplitudenwert sind untereinander inkonsistent.

4. **Aufgabe 2e, asymptotische gegen exakte Analyse:**  
   Die stückweise asymptotische Phase erreicht \(-180^\circ\); die exakte Phase nur ungefähr \(-168.6^\circ\).

5. **Phasenwicklung bei negativem P-Glied:**  
   \(+90^\circ\) und \(-270^\circ\) beschreiben denselben komplexen Winkel. Diagramme müssen mit einer konsistenten Phasenwicklung gelesen werden.

---

# 22. Klausurstrategie

## 22.1 Reserven aus einem Bode-Diagramm

### Phasenreserve

1. \(0\,\mathrm{dB}\)-Linie suchen.
2. Gain-Durchtritt \(\omega_g\) markieren.
3. Senkrecht zum Phasengang gehen.
4. Phase \(\varphi(\omega_g)\) ablesen.
5. Rechnen:

\[
\Delta\varphi
=
180^\circ+\varphi(\omega_g).
\]

### Amplitudenreserve

1. Im Phasengang \(-180^\circ\) suchen.
2. Phasen-Durchtritt \(\omega_p\) markieren.
3. Senkrecht zum Amplitudengang gehen.
4. dB-Wert \(L(\omega_p)\) ablesen.
5. Rechnen:

\[
\Delta A=-L(\omega_p).
\]

---

## 22.2 Übertragungsfunktion aus einer asymptotischen Skizze

1. Anfangssteigung bestimmen.
2. Jede Steigungsänderung markieren.
3. Eckfrequenzen ablesen.
4. Pole und Nullstellen zuordnen.
5. Verstärkungsfaktor aus dem Niveau bestimmen.
6. Phase als Kontrolle verwenden.
7. Funktion faktorisieren.
8. Mit Grenzfällen kontrollieren.

---

# 23. Typische Fehler in Tutorium 06

1. Gain- und Phasen-Durchtrittsfrequenz vertauschen.
2. Phasenreserve am \(-180^\circ\)-Durchtritt ablesen.
3. Amplitudenreserve am \(0\,\mathrm{dB}\)-Durchtritt ablesen.
4. Das Minuszeichen in

\[
\Delta A=-L(\omega_p)
\]

vergessen.
5. Bei negativer Phase

\[
180^\circ-\varphi
\]

statt

\[
180^\circ+\varphi
\]

rechnen.
6. Eine Reserve als 0 angeben, obwohl der benötigte Durchtritt gar nicht existiert.
7. Asymptotische Bode-Linien mit dem exakten Frequenzgang verwechseln.
8. Negative Verstärkung im Betrag berücksichtigen, aber den Phasensprung vergessen.
9. Bei mehreren Knicken Zeitkonstanten falsch herum bestimmen.
10. Nur die Amplitude zur Rekonstruktion verwenden und die Phase nicht kontrollieren.
11. Positive Reserven ungeprüft als universellen Stabilitätsbeweis behandeln.
12. Bei mehreren Durchtritten nicht den kritischsten auswählen.

---

# 24. NotebookLM-Verifikation

--- NOTEBOOKLM-PROMPT ---

Prüfe ausschließlich anhand der hochgeladenen offiziellen Regelungstechnik-Unterlagen die Widersprüche in „Tutorium 06 – Frequenzganganalyse“, Aufgabe 2e.

Gegeben ist laut Musterlösung:

\[
F(s)
=
\frac1{0.1s}
\cdot
\frac1{1+s}
\cdot
(1+0.01s).
\]

Die gedruckte Lösung nennt:
- Amplitudenreserve \(\Delta A=-20\,\mathrm{dB}\),
- angenommenen Phasendurchtritt bei \(\omega=100\),
- Phasenreserve \(\Delta\varphi=0^\circ\).

Prüfe:

1. Welchen Amplitudenwert zeigt die offizielle asymptotische Bode-Skizze bei \(\omega=10\) und bei \(\omega=100\)?
2. Muss aus einem Amplitudenwert von \(-20\,\mathrm{dB}\) nach der offiziellen Definition \(\Delta A=+20\,\mathrm{dB}\) folgen?
3. Erreicht die exakte Phase
\[
-90^\circ-\arctan(\omega)+\arctan(0.01\omega)
\]
bei einer endlichen Frequenz tatsächlich \(-180^\circ\)?
4. Welche Werte ergeben sich exakt für Gain-Durchtrittsfrequenz und Phasenreserve?
5. Ist die gedruckte Lösung ein Fehler oder beruht sie auf einer ausdrücklich genannten asymptotischen Konvention?

Belege jede Quellenaussage mit Dokumentname und genauer Seite. Trenne direkte Quelle, grafisches Ablesen und eigene mathematische Herleitung.

--- ENDE ---

---

# 25. Kompaktformelsammlung Tutorium 06

## Gain-Durchtritt

\[
|G_0(j\omega_g)|=1
\]

\[
|G_0(j\omega_g)|_{\mathrm{dB}}=0.
\]

## Phasen-Durchtritt

\[
\varphi(\omega_p)=-180^\circ.
\]

## Phasenreserve

\[
\boxed{
\Delta\varphi
=
180^\circ+\varphi(\omega_g)
}.
\]

## Amplitudenreserve in dB

\[
\boxed{
\Delta A
=
-|G_0(j\omega_p)|_{\mathrm{dB}}
}.
\]

## Amplitudenreserve linear

\[
\boxed{
A_R
=
\frac1{|G_0(j\omega_p)|}
}.
\]

## Eckfrequenz

\[
\omega_E=\frac1T.
\]

## Geschlossener Kreis

\[
\boxed{
G_{\mathrm{cl}}
=
\frac{G_0}{1+G_0}
}.
\]

## Kritischer Punkt

\[
\boxed{
G_0(j\omega)=-1
}.
\]

---

# Tutorium 07 – Einführung in den Regelkreis

## 1. Quellen und Seitenbereich

### Primärquellen

1. **RT-Tutorien-Mitschrift.pdf**, PDF-Seiten 82–98
   - S. 82: Theoriefragen, Aufgabe 1a–b und offizielle Endergebnisse
   - S. 83–85: Tafelbilder und Mitschrift zu Theorie, Führungs-/Störübertragungen und Endwertsatz
   - S. 86: offizielle Endergebnisse zu Aufgabe 1c–e
   - S. 87–89: vollständige Rechnungen zu Aufgabe 1a–e
   - S. 90: Aufgabe 2 mit verschachteltem Lage- und Drehzahlregelkreis
   - S. 91–93: Aufgabe 3, Übertragungsfunktionen, Sprungantworten und qualitative Bewertung
   - S. 93–95: Aufgabe 4, vollständige Herleitung des geschlossenen PT2-Systems und Parameterrechnungen
   - S. 96–97: Aufgabe 5 und Herleitung zur stationären Regelabweichung
   - S. 98: leer
   - Danach folgt direkt Tutorium 09; Tutorium 08 ist in dieser Sammlung nicht als eigenes Theorietutorium enthalten.

2. **Regelungstechnik_Tutorium_komplett.pdf**, PDF-Seiten 48–54  
   Tutorium 07, Blattseiten 1/6–6/6, offizielle Aufgaben und Endergebnisse.

3. **skript.pdf**
   - Kapitel 4, gedruckte S. 80–81: allgemeiner Regelkreis mit \(d_1\) und \(d_2\)
   - Kapitel 4.1.2, gedruckte S. 88–90: Führungs- und Störübertragungsfunktionen
   - Kapitel 4.2–4.3, gedruckte S. 90–95: Anforderungen, stationäre Genauigkeit und Beurteilungskriterien

---

# 2. Allgemeiner Regelkreis mit zwei Störungen

## 2.1 Struktur

Betrachtet wird der negative Einheitsregelkreis

\[
w
\longrightarrow
\Sigma
\longrightarrow
G_R
\longrightarrow
\oplus d_1
\longrightarrow
G_S
\longrightarrow
\oplus d_2
\longrightarrow
y,
\]

mit Rückführung

\[
e=w-y.
\]

Dabei gilt:

- \(w\): Führungsgröße bzw. Sollwert,
- \(e\): Regelabweichung,
- \(G_R\): Regler,
- \(G_S\): Strecke,
- \(d_1\): Störung vor der Strecke bzw. am Stellglied,
- \(d_2\): Störung nach der Strecke bzw. am Ausgang/Messglied.

Die Mitschrift skizziert diese Struktur auf PDF-S. 83 und 85.

---

## 2.2 Offener Kreis

\[
\boxed{
G_0(s)=G_R(s)G_S(s)
}.
\]

Bei allgemeiner Rückführung \(G_M\) wäre die Schleifenübertragung

\[
G_0=G_RG_SG_M.
\]

Im Tutorium gilt Einheitsrückführung:

\[
G_M=1.
\]

---

## 2.3 Signalgleichung

Aus dem Blockbild:

\[
e=w-y.
\]

Reglerausgang:

\[
u_R=G_Re.
\]

Ausgang:

\[
y=G_S(u_R+d_1)+d_2.
\]

Einsetzen:

\[
y
=
G_SG_R(w-y)+G_Sd_1+d_2.
\]

\[
y+G_RG_Sy
=
G_RG_Sw+G_Sd_1+d_2.
\]

Damit:

\[
\boxed{
y
=
\frac{G_RG_S}{1+G_RG_S}w
+
\frac{G_S}{1+G_RG_S}d_1
+
\frac1{1+G_RG_S}d_2
}.
\]

---

# 3. Führungs- und Störübertragungsfunktionen

## 3.1 Führungsübertragungsfunktion

Bei

\[
d_1=d_2=0
\]

gilt:

\[
\boxed{
G_w(s)
=
\frac{Y(s)}{W(s)}
=
\frac{G_R(s)G_S(s)}
{1+G_R(s)G_S(s)}
=
\frac{G_0(s)}{1+G_0(s)}
}.
\]

Diese Funktion wird auch komplementäre Sensitivität genannt:

\[
T(s)=\frac{G_0}{1+G_0}.
\]

---

## 3.2 Störübertragung für \(d_1\)

Die Störung wird vor der Strecke eingespeist.

Bei

\[
w=d_2=0
\]

gilt:

\[
\boxed{
G_{d1}(s)
=
\frac{Y(s)}{D_1(s)}
=
\frac{G_S(s)}
{1+G_R(s)G_S(s)}
}.
\]

Die Störung durchläuft die Strecke, bevor sie am Ausgang erscheint.

---

## 3.3 Störübertragung für \(d_2\)

Die Störung wird nach der Strecke eingespeist.

Bei

\[
w=d_1=0
\]

gilt:

\[
\boxed{
G_{d2}(s)
=
\frac{Y(s)}{D_2(s)}
=
\frac1{1+G_R(s)G_S(s)}
}.
\]

Diese Funktion ist die Sensitivität:

\[
\boxed{
S(s)=\frac1{1+G_0(s)}
}.
\]

Zusammenhang:

\[
\boxed{
S(s)+T(s)=1
}.
\]

---

## 3.4 Merksatz zur Störstelle

- Störung **vor der Strecke**:

\[
G_{d1}=G_SS.
\]

- Störung **nach der Strecke**:

\[
G_{d2}=S.
\]

Die handschriftliche Mitschrift auf PDF-S. 83 und 85 formuliert dies als:

- „Störung geht vor der Strecke ein“
- „Störung geht nach der Strecke ein“.

---

# 4. Stationäre Regelabweichung und Endwertsatz

## 4.1 Regelabweichung

\[
e(t)=w(t)-y(t).
\]

Bei Einheitssprung:

\[
w(t)=1.
\]

Stationär:

\[
\boxed{
e_\infty
=
1-y_\infty
}.
\]

---

## 4.2 Endwertsatz

Für ein stabiles System gilt:

\[
\boxed{
\lim_{t\to\infty}f(t)
=
\lim_{s\to0}sF(s)
}.
\]

Voraussetzung:

Alle Pole von

\[
sF(s)
\]

müssen in der offenen linken Halbebene liegen; Pole auf oder rechts der imaginären Achse machen die Anwendung im Allgemeinen unzulässig.

Die Mitschrift vermerkt auf PDF-S. 85 ausdrücklich „nach Endwertsatz“.

---

## 4.3 Stationärer Ausgang bei Einheitssprung

Mit

\[
W(s)=\frac1s
\]

gilt:

\[
Y(s)=G_w(s)\frac1s.
\]

Daher:

\[
y_\infty
=
\lim_{s\to0}sY(s)
=
\lim_{s\to0}G_w(s).
\]

Somit:

\[
\boxed{
e_\infty
=
1-\lim_{s\to0}G_w(s)
}.
\]

---

# 5. Theoriefragen

## 5.1 Warum reduziert eine hohe Verstärkung die Regelabweichung?

Für die Führungsübertragung gilt:

\[
G_w
=
\frac{G_0}{1+G_0}.
\]

Die Fehlerübertragung ist:

\[
\frac EW
=
1-G_w
=
\frac1{1+G_0}.
\]

Für einen Einheitssprung ist die stationäre Regelabweichung bei stabilem Kreis:

\[
\boxed{
e_\infty
=
\frac1{1+G_0(0)}
}.
\]

Wird die Niederfrequenzverstärkung \(G_0(0)\) groß, dann:

\[
e_\infty\to0.
\]

Bei endlicher P-Verstärkung wird der Fehler nur verkleinert, nicht grundsätzlich exakt eliminiert.

Die Mitschrift auf PDF-S. 84 schreibt sinngemäß:

\[
G_RG_S\ \text{sehr groß}
\Rightarrow
G_w\to1
\Rightarrow
\text{Abweichung wird klein}.
\]

---

## 5.2 Warum eliminiert ein I-Regler den stationären Fehler bei einer Sprungführung?

Ein I-Regler besitzt

\[
G_R(s)=\frac{K_I}{s}.
\]

Damit enthält der offene Kreis einen Pol bei

\[
s=0.
\]

Falls die Strecke bei \(s=0\) einen endlichen, von null verschiedenen Wert besitzt:

\[
|G_0(s)|\to\infty
\qquad
\text{für }
s\to0.
\]

Damit:

\[
G_w(0)
=
\lim_{s\to0}
\frac{G_0(s)}{1+G_0(s)}
=
1.
\]

Für einen Einheitssprung:

\[
\boxed{
e_\infty=1-G_w(0)=0
}.
\]

Physikalisch integriert der Regler eine konstante Regelabweichung weiter. Solange ein Fehler besteht, wächst der Reglerausgang. Ein stationärer Zustand ist daher nur bei verschwindender Regelabweichung möglich.

### Voraussetzungen

- geschlossener Kreis ist stabil,
- der Integrator wird nicht durch eine Nullstelle bei \(s=0\) gekürzt,
- keine Sättigung oder Begrenzung verhindert die notwendige Stellgröße.

---

## 5.3 Warum beeinflusst ein D-Regler die stationäre Genauigkeit nicht?

Ein D-Regler besitzt:

\[
G_R(s)=K_Ds.
\]

Für stationäre Signale gilt:

\[
s\to0.
\]

Dann:

\[
G_R(0)=0.
\]

Im Zeitbereich:

\[
u_R(t)=K_D\dot e(t).
\]

Bei einer konstanten Regelabweichung ist:

\[
\dot e(t)=0.
\]

Damit erzeugt der D-Anteil im stationären Zustand keine Stellgröße.

\[
\boxed{
\text{Der D-Anteil beeinflusst Transienten, aber nicht die statische Genauigkeit.}
}
\]

Die Mitschrift auf PDF-S. 84 notiert korrekt:

\[
G_R(0)=0.
\]

---

# 6. Aufgabe 1 – PT1-Strecke mit P-Regler

## 6.1 Gegeben

\[
G_R(s)=K_P,
\]

\[
G_S(s)=\frac{K_S}{1+sT_1},
\]

\[
K_P,K_S,T_1>0.
\]

---

## 6.2 Offener Kreis

\[
G_0(s)
=
G_R(s)G_S(s).
\]

\[
\boxed{
G_0(s)
=
\frac{K_PK_S}{1+sT_1}
}.
\]

---

## 6.3 Führungsübertragungsfunktion

\[
G_w(s)
=
\frac{G_0(s)}{1+G_0(s)}.
\]

Einsetzen:

\[
G_w(s)
=
\frac{
\dfrac{K_PK_S}{1+sT_1}
}{
1+
\dfrac{K_PK_S}{1+sT_1}
}.
\]

Mit \(1+sT_1\) erweitern:

\[
\boxed{
G_w(s)
=
\frac{K_PK_S}
{1+sT_1+K_PK_S}
}.
\]

---

## 6.4 Störübertragung \(d_1\)

\[
G_{d1}(s)
=
\frac{G_S(s)}
{1+G_0(s)}.
\]

\[
G_{d1}(s)
=
\frac{
\dfrac{K_S}{1+sT_1}
}{
1+
\dfrac{K_PK_S}{1+sT_1}
}.
\]

Ergebnis:

\[
\boxed{
G_{d1}(s)
=
\frac{K_S}
{1+sT_1+K_PK_S}
}.
\]

---

## 6.5 Störübertragung \(d_2\)

\[
G_{d2}(s)
=
\frac1{1+G_0(s)}.
\]

\[
G_{d2}(s)
=
\frac1{
1+
\dfrac{K_PK_S}{1+sT_1}
}.
\]

Erweitern:

\[
\boxed{
G_{d2}(s)
=
\frac{1+sT_1}
{1+sT_1+K_PK_S}
}.
\]

Die Rechnungen auf Mitschrift-PDF-S. 87 sind vollständig und korrekt.

---

# 7. Aufgabe 1b – geschlossener Kreis als PT1-Glied

## 7.1 Ausgangsfunktion

\[
G_w(s)
=
\frac{K_PK_S}
{1+K_PK_S+sT_1}.
\]

Faktorisieren:

\[
1+K_PK_S+sT_1
=
(1+K_PK_S)
\left(
1+
s\frac{T_1}{1+K_PK_S}
\right).
\]

Damit:

\[
G_w(s)
=
\frac{
\dfrac{K_PK_S}{1+K_PK_S}
}{
1+
s\dfrac{T_1}{1+K_PK_S}
}.
\]

Vergleich mit:

\[
G_{PT1}(s)=\frac K{1+sT}.
\]

Ergebnis:

\[
\boxed{
K
=
\frac{K_PK_S}
{1+K_PK_S}
}
\]

und

\[
\boxed{
T
=
\frac{T_1}
{1+K_PK_S}
}.
\]

---

## 7.2 Interpretation

Durch Erhöhung von \(K_P\):

1. steigt die geschlossene statische Verstärkung gegen 1,

\[
K\to1,
\]

2. sinkt die Zeitkonstante,

\[
T\to0,
\]

3. wird der Kreis schneller,

4. sinkt die stationäre Regelabweichung.

Für dieses spezielle PT1-P-Modell bleibt der geschlossene Kreis erster Ordnung und überschwingt nicht. Diese Aussage gilt nicht pauschal für höherordentliche Strecken.

---

# 8. Aufgabe 1c – Sprungführung

## 8.1 Eingang

\[
w(t)=1
\quad\Rightarrow\quad
W(s)=\frac1s.
\]

\[
d_1=d_2=0.
\]

Ausgang:

\[
Y(s)=G_w(s)W(s).
\]

\[
Y(s)
=
\frac{K_PK_S}
{s(1+K_PK_S+sT_1)}.
\]

Mit den PT1-Parametern:

\[
K
=
\frac{K_PK_S}
{1+K_PK_S},
\]

\[
T
=
\frac{T_1}
{1+K_PK_S}
\]

gilt:

\[
Y(s)=\frac K{s(1+sT)}.
\]

---

## 8.2 Partialbruchzerlegung

\[
\frac K{s(1+sT)}
=
\frac Ks
-
\frac{KT}{1+sT}.
\]

Rücktransformation:

\[
\boxed{
y(t)
=
K\left(
1-e^{-t/T}
\right)
}.
\]

Einsetzen:

\[
\boxed{
y(t)
=
\frac{K_PK_S}
{1+K_PK_S}
\left[
1-
\exp\left(
-\frac{1+K_PK_S}{T_1}t
\right)
\right]
}.
\]

Die handschriftliche Rechnung auf PDF-S. 88 ist korrekt.

---

## 8.3 Stationärer Wert und Regelabweichung

\[
y_\infty
=
\frac{K_PK_S}
{1+K_PK_S}.
\]

\[
\boxed{
e_\infty
=
1-y_\infty
=
\frac1{1+K_PK_S}
}.
\]

---

# 9. Aufgabe 1d – Sprungstörung vor der Strecke

## 9.1 Eingang

\[
d_1(t)=1
\quad\Rightarrow\quad
D_1(s)=\frac1s.
\]

\[
w=d_2=0.
\]

\[
Y(s)=G_{d1}(s)D_1(s).
\]

\[
Y(s)
=
\frac{K_S}
{s(1+K_PK_S+sT_1)}.
\]

---

## 9.2 Zeitantwort

Geschlossene Verstärkung für diesen Störpfad:

\[
K_{d1}
=
\frac{K_S}
{1+K_PK_S}.
\]

Zeitkonstante:

\[
T
=
\frac{T_1}
{1+K_PK_S}.
\]

Damit:

\[
\boxed{
y(t)
=
\frac{K_S}
{1+K_PK_S}
\left[
1-
\exp\left(
-\frac{1+K_PK_S}{T_1}t
\right)
\right]
}.
\]

Stationärer Restfehler:

\[
\boxed{
y_\infty
=
\frac{K_S}
{1+K_PK_S}
}.
\]

Eine größere P-Verstärkung reduziert die Auswirkung, eliminiert sie aber bei endlichem \(K_P\) nicht vollständig.

---

# 10. Aufgabe 1e – Sprungstörung nach der Strecke

## 10.1 Eingang

\[
d_2(t)=1
\quad\Rightarrow\quad
D_2(s)=\frac1s.
\]

\[
w=d_1=0.
\]

\[
Y(s)
=
G_{d2}(s)D_2(s).
\]

\[
Y(s)
=
\frac{1+sT_1}
{s(1+K_PK_S+sT_1)}.
\]

---

## 10.2 Zerlegung

Setze:

\[
a=K_PK_S.
\]

Gesucht:

\[
\frac{1+sT_1}
{s(1+a+sT_1)}
=
\frac A{s}
+
\frac B{1+a+sT_1}.
\]

Multiplikation:

\[
1+sT_1
=
A(1+a+sT_1)+Bs.
\]

Für \(s=0\):

\[
1=A(1+a).
\]

\[
A=\frac1{1+a}.
\]

Koeffizient von \(s\):

\[
T_1
=
AT_1+B.
\]

\[
B
=
T_1(1-A)
=
\frac{aT_1}{1+a}.
\]

Damit:

\[
Y(s)
=
\frac1{1+a}\frac1s
+
\frac{aT_1}{1+a}
\frac1{1+a+sT_1}.
\]

Normieren:

\[
\frac1{1+a+sT_1}
=
\frac1{T_1}
\frac1{
s+\dfrac{1+a}{T_1}
}.
\]

Rücktransformation:

\[
\boxed{
y(t)
=
\frac1{1+a}
+
\frac a{1+a}
\exp\left(
-\frac{1+a}{T_1}t
\right)
}.
\]

Mit \(a=K_PK_S\):

\[
\boxed{
y(t)
=
\frac1{1+K_PK_S}
+
\frac{K_PK_S}
{1+K_PK_S}
\exp\left(
-\frac{1+K_PK_S}{T_1}t
\right)
}.
\]

---

## 10.3 Interpretation

Unmittelbar nach dem Störungssprung:

\[
y(0^+)=1.
\]

Die Störung wird direkt nach der Strecke addiert und erzeugt deshalb einen sofortigen Ausgangssprung.

Stationär:

\[
\boxed{
y_\infty
=
\frac1{1+K_PK_S}
}.
\]

Der Regler reduziert die Störung anschließend auf einen Restwert.

Die Mitschrift auf PDF-S. 89 bricht die Detailrechnung ab, nennt aber korrekt die Superpositionsstruktur:

\[
Y
=
G_wW
+
G_{d1}D_1
+
G_{d2}D_2.
\]

---

# 11. Aufgabe 2 – verschachtelter Lage- und Drehzahlregelkreis

## 11.1 Struktur

Der dargestellte Regelkreis besteht aus:

### Innerer Drehzahlregelkreis

Vorwärtsweg:

\[
G_{R1}(s)
\cdot
\frac1{1+s\tau_{el}}
\cdot
\frac1{1+s\tau_m}.
\]

Einheitsrückführung um Regler und Motor.

### Äußerer Lageregelkreis

- P-Lageregler \(K_R\),
- geschlossener Drehzahlregelkreis,
- Spindelintegrator

\[
\frac{K_I}{s},
\]

- Einheitsrückführung der Position.

Gegeben:

\[
\tau_{el}=0.05,
\qquad
\tau_m=0.2.
\]

---

## 11.2 Motorübertragung

Definiere:

\[
G_M(s)
=
\frac1{
(1+s\tau_{el})(1+s\tau_m)
}.
\]

Mit den Zahlenwerten:

\[
(1+0.05s)(1+0.2s)
=
1+0.25s+0.01s^2.
\]

Damit:

\[
G_M(s)
=
\frac1{
1+0.25s+0.01s^2
}.
\]

---

## 11.3 Geschlossener innerer Drehzahlregelkreis

Offener innerer Kreis:

\[
G_{0,n}(s)
=
G_{R1}(s)G_M(s).
\]

Geschlossene Führungsübertragung:

\[
G_n(s)
=
\frac{
G_{R1}(s)G_M(s)
}{
1+G_{R1}(s)G_M(s)
}.
\]

Mit \(G_M\):

\[
\boxed{
G_n(s)
=
\frac{
G_{R1}(s)
}{
G_{R1}(s)
+
(1+s\tau_{el})(1+s\tau_m)
}
}.
\]

---

## 11.4 Aufgabe 2a – Gesamtübertragungsfunktion

Der äußere offene Kreis lautet:

\[
G_{0,L}(s)
=
K_R
\cdot
G_n(s)
\cdot
\frac{K_I}{s}.
\]

\[
G_{0,L}(s)
=
\frac{
K_RG_{R1}(s)K_I
}{
s\left[
G_{R1}(s)
+
(1+s\tau_{el})(1+s\tau_m)
\right]
}.
\]

Der geschlossene äußere Kreis ist:

\[
G(s)
=
\frac{
G_{0,L}(s)
}{
1+G_{0,L}(s)
}.
\]

Ergebnis:

\[
\boxed{
G(s)
=
\frac{
K_RG_{R1}(s)K_I
}{
s\left[
G_{R1}(s)
+
(1+s\tau_{el})(1+s\tau_m)
\right]
+
K_RG_{R1}(s)K_I
}
}.
\]

Dies entspricht der offiziellen Lösung.

---

## 11.5 Aufgabe 2b – Drehzahlkreis bei Einheitssprung

Die Führungsübertragungsfunktion des inneren Drehzahlkreises ist:

\[
\boxed{
G_{w,n}(s)
=
\frac{
G_{R1}(s)
}{
G_{R1}(s)
+
(1+s\tau_{el})(1+s\tau_m)
}
}.
\]

Für einen Einheitssprung:

\[
W_n(s)=\frac1s.
\]

Daher lautet die Ausgangsgröße:

\[
\boxed{
Y_R(s)
=
\frac1s
\frac{
G_{R1}(s)
}{
G_{R1}(s)
+
(1+s\tau_{el})(1+s\tau_m)
}
}.
\]

### Notationshinweis

Die offizielle Lösung nennt \(Y_R(s)\), nicht nur die Übertragungsfunktion. Der Faktor \(1/s\) gehört zur Sprunganregung und nicht zur Führungsübertragungsfunktion selbst.

---

## 11.6 Aufgabe 2c – Impulsstörung zwischen Regler und Motor

Die Störung wirkt am Eingang des Motors.

Für den inneren Kreis gilt bei ausgeschalteter Führung:

\[
Y(s)
=
\frac{
G_M(s)
}{
1+G_{R1}(s)G_M(s)
}
D(s).
\]

Störübertragungsfunktion:

\[
G_d(s)
=
\frac{
G_M(s)
}{
1+G_{R1}(s)G_M(s)
}.
\]

Einsetzen:

\[
\boxed{
G_d(s)
=
\frac1{
G_{R1}(s)
+
(1+s\tau_{el})(1+s\tau_m)
}
}.
\]

Bei Einheitsimpuls:

\[
D(s)=1.
\]

Damit:

\[
\boxed{
Y(s)
=
\frac1{
G_{R1}(s)
+
(1+s\tau_{el})(1+s\tau_m)
}
}.
\]

Auch dies stimmt mit der offiziellen Lösung überein.

---

# 12. Aufgabe 3 – PT1-Strecke mit P-, I- und D-Regler

## 12.1 Gegeben

Strecke:

\[
G_S(s)
=
\frac1{s+2}.
\]

Regler:

\[
G_{R1}(s)=4,
\]

\[
G_{R2}(s)=\frac5s,
\]

\[
G_{R3}(s)=\frac32s.
\]

---

## 12.2 Klassifikation

\[
G_S:
\quad
\boxed{\text{PT1-Glied}}
\]

denn:

\[
\frac1{s+2}
=
\frac{1/2}{1+s/2}.
\]

\[
G_{R1}:
\quad
\boxed{\text{P-Regler}}
\]

\[
G_{R2}:
\quad
\boxed{\text{I-Regler}}
\]

\[
G_{R3}:
\quad
\boxed{\text{D-Regler}}.
\]

---

# 13. Aufgabe 3 – P-Regler

## 13.1 Führungsübertragungsfunktion

Offener Kreis:

\[
G_{0,P}
=
4\frac1{s+2}.
\]

Geschlossen:

\[
G_{w,P}
=
\frac{
\dfrac4{s+2}
}{
1+\dfrac4{s+2}
}.
\]

Ergebnis:

\[
\boxed{
G_{w,P}(s)
=
\frac4{s+6}
}.
\]

Die Mitschrift auf PDF-S. 92 ist korrekt.

---

## 13.2 Sprungantwort

\[
W(s)=\frac1s.
\]

\[
Y_P(s)
=
\frac4{s(s+6)}.
\]

Partialbruchzerlegung:

\[
\frac4{s(s+6)}
=
\frac{2/3}{s}
-
\frac{2/3}{s+6}.
\]

Damit:

\[
\boxed{
y_P(t)
=
\frac23
\left(
1-e^{-6t}
\right)
}.
\]

---

## 13.3 Bewertung

Stationär:

\[
y_P(\infty)=\frac23.
\]

\[
\boxed{
e_{\infty,P}
=
1-\frac23
=
\frac13
}.
\]

Eigenschaften:

- sehr schnelle Reaktion,
- kein Überschwingen,
- stationäre Regelabweichung von \(33.3\%\).

Zeitkonstante:

\[
T_P=\frac16.
\]

---

# 14. Aufgabe 3 – I-Regler

## 14.1 Führungsübertragungsfunktion

Offener Kreis:

\[
G_{0,I}
=
\frac5{s(s+2)}.
\]

Geschlossen:

\[
G_{w,I}
=
\frac{
\dfrac5{s(s+2)}
}{
1+\dfrac5{s(s+2)}
}.
\]

\[
\boxed{
G_{w,I}(s)
=
\frac5{s^2+2s+5}
}.
\]

---

## 14.2 PT2-Parameter

Vergleich mit:

\[
s^2+2D\omega_0s+\omega_0^2.
\]

Es gilt:

\[
\omega_0^2=5
\quad\Rightarrow\quad
\omega_0=\sqrt5.
\]

\[
2D\omega_0=2.
\]

\[
D
=
\frac1{\sqrt5}
\approx0.447.
\]

Gedämpfte Kreisfrequenz:

\[
\omega_d
=
\omega_0\sqrt{1-D^2}
=
2.
\]

---

## 14.3 Sprungantwort

\[
Y_I(s)
=
\frac5{s(s^2+2s+5)}.
\]

Partialbruchzerlegung:

\[
\frac5{s(s^2+2s+5)}
=
\frac1s
-
\frac{s+2}{s^2+2s+5}.
\]

Mit:

\[
s^2+2s+5
=
(s+1)^2+4
\]

und

\[
s+2=(s+1)+1
\]

folgt:

\[
\boxed{
y_I(t)
=
1
-
e^{-t}\cos(2t)
-
\frac12e^{-t}\sin(2t)
}.
\]

Dies entspricht der offiziellen Lösung.

---

## 14.4 Bewertung

Stationär:

\[
\boxed{
y_I(\infty)=1
}
\]

und:

\[
\boxed{
e_{\infty,I}=0
}.
\]

Überschwingverhältnis:

\[
M_p
=
\exp\left(
-\frac{\pi D}{\sqrt{1-D^2}}
\right).
\]

Mit \(D=1/\sqrt5\):

\[
\boxed{
M_p=e^{-\pi/2}\approx0.208
}.
\]

Also ungefähr:

\[
\boxed{20.8\%}
\]

Überschwingen.

Zeit des ersten Maximums:

\[
t_p
=
\frac\pi{\omega_d}
=
\frac\pi2
\approx1.57.
\]

Der I-Regler beseitigt den stationären Fehler, erzeugt hier aber eine deutlich langsamere und überschwingende Antwort.

---

# 15. Aufgabe 3 – D-Regler

## 15.1 Führungsübertragungsfunktion

Offener Kreis:

\[
G_{0,D}
=
\frac32s\frac1{s+2}.
\]

\[
G_{0,D}
=
\frac{3s}{2(s+2)}.
\]

Geschlossen:

\[
G_{w,D}
=
\frac{
\dfrac{3s}{2(s+2)}
}{
1+\dfrac{3s}{2(s+2)}
}.
\]

Nenner zusammenfassen:

\[
2(s+2)+3s
=
5s+4.
\]

Damit:

\[
\boxed{
G_{w,D}(s)
=
\frac{3s}{5s+4}
}.
\]

Die Mitschrift auf PDF-S. 92 ist korrekt.

---

## 15.2 Sprungantwort

\[
W(s)=\frac1s.
\]

\[
Y_D(s)
=
\frac{3s}{5s+4}
\frac1s.
\]

Der Faktor \(s\) kürzt sich:

\[
Y_D(s)
=
\frac3{5s+4}.
\]

\[
Y_D(s)
=
\frac35
\frac1{s+4/5}.
\]

Damit:

\[
\boxed{
y_D(t)
=
\frac35e^{-4t/5}
}.
\]

---

## 15.3 Bewertung

Unmittelbar nach dem Sprung:

\[
y_D(0^+)=\frac35.
\]

Stationär:

\[
\boxed{
y_D(\infty)=0
}.
\]

Damit:

\[
\boxed{
e_{\infty,D}=1
}.
\]

Ein D-Regler reagiert nur auf die Sollwertänderung. Sobald der Sollwert konstant ist, verschwindet sein Ausgang. Als alleiniger Regler ist er für eine konstante Führungsgröße ungeeignet.

### Direktdurchgriff

Da Zähler- und Nennergrad von \(G_{w,D}\) gleich sind, besitzt die geschlossene Übertragungsfunktion einen direkten Durchgriff. Deshalb beginnt die Sprungantwort bei \(0.6\) statt bei 0.

---

# 16. Aufgabe 3d – Vergleich der drei Reglertypen

## P-Regler

- schnellste monotone Annäherung,
- kein Überschwingen,
- stationärer Fehler:

\[
33.3\%.
\]

## I-Regler

- langsamer,
- überschwingt ungefähr \(20.8\%\),
- stationärer Fehler:

\[
0.
\]

## D-Regler

- reagiert sofort auf die Sollwertänderung,
- Ausgang klingt wieder auf 0 ab,
- stationärer Fehler:

\[
100\%.
\]

### Ergebnis

Für gute stationäre Genauigkeit wird ein I-Anteil benötigt. Ein P-Anteil verbessert Geschwindigkeit und reduziert den Fehler. Ein D-Anteil beeinflusst nur das transiente Verhalten und ist allein kein brauchbarer Führungsregler.

---

# 17. Aufgabe 4 – PT2-Strecke mit P-Regler

## 17.1 Gegeben

\[
G_R(s)=K_R,
\]

\[
G_S(s)
=
\frac4{(1+5s)(1+s)},
\]

\[
K_R>0.
\]

---

## 17.2 Strecke ausmultiplizieren

\[
(1+5s)(1+s)
=
1+6s+5s^2.
\]

Damit:

\[
G_S(s)
=
\frac4{5s^2+6s+1}.
\]

Normieren durch 5:

\[
G_S(s)
=
\frac{4/5}
{s^2+\frac65s+\frac15}.
\]

Vergleich mit:

\[
\frac{K\omega_0^2}
{s^2+2D\omega_0s+\omega_0^2}.
\]

---

# 18. Aufgabe 4a – Dämpfung der Strecke

\[
\omega_0^2=\frac15.
\]

\[
\omega_0=\frac1{\sqrt5}.
\]

\[
2D\omega_0=\frac65.
\]

\[
D
=
\frac{6/5}
{2/\sqrt5}.
\]

\[
\boxed{
D
=
\frac3{\sqrt5}
\approx1.342
}.
\]

Die offene Strecke ist überdämpft und überschwingt nicht.

Die handschriftliche Rechnung auf PDF-S. 94 ist korrekt.

---

# 19. Geschlossener Kreis mit \(K_R\)

## 19.1 Führungsübertragungsfunktion

Offener Kreis:

\[
G_0(s)
=
\frac{4K_R}
{(1+5s)(1+s)}.
\]

Geschlossen:

\[
G_w(s)
=
\frac{
\dfrac{4K_R}
{(1+5s)(1+s)}
}{
1+
\dfrac{4K_R}
{(1+5s)(1+s)}
}.
\]

\[
\boxed{
G_w(s)
=
\frac{4K_R}
{5s^2+6s+1+4K_R}
}.
\]

Normieren:

\[
G_w(s)
=
\frac{4K_R/5}
{
s^2+\frac65s+\frac{1+4K_R}{5}
}.
\]

---

## 19.2 Geschlossene PT2-Parameter

\[
\boxed{
\omega_0^2
=
\frac{1+4K_R}{5}
}
\]

\[
\boxed{
\omega_0
=
\sqrt{
\frac{1+4K_R}{5}
}
}
\]

und:

\[
2D\omega_0=\frac65.
\]

Daher:

\[
D
=
\frac3{5\omega_0}.
\]

Einsetzen:

\[
\boxed{
D(K_R)
=
\frac3{
\sqrt{
5(1+4K_R)
}
}
}.
\]

Mit größerem \(K_R\):

- steigt \(\omega_0\),
- sinkt \(D\),
- steigt die Überschwingneigung.

---

# 20. Aufgabe 4b – gerade kein Überschwingen

Für eine PT2-Sprungantwort ohne Nullstellen gilt:

- \(D<1\): Überschwingen,
- \(D=1\): aperiodischer Grenzfall,
- \(D>1\): kein Überschwingen.

„Gerade nicht überschwingen“ bedeutet:

\[
D=1.
\]

\[
1
=
\frac3{
\sqrt{
5(1+4K_R)
}
}.
\]

Quadrieren:

\[
5(1+4K_R)=9.
\]

\[
1+4K_R=\frac95.
\]

\[
4K_R=\frac45.
\]

\[
\boxed{
K_R=0.2
}.
\]

Für:

\[
0<K_R\le0.2
\]

tritt kein Überschwingen auf. \(K_R=0.2\) ist der größte Grenzwert.

---

# 21. Aufgabe 4c – stationäre Regelabweichung bei \(K_R=0.2\)

Statische geschlossene Verstärkung:

\[
G_w(0)
=
\frac{4K_R}
{1+4K_R}.
\]

Bei Einheitssprung:

\[
y_\infty=G_w(0).
\]

Regelabweichung:

\[
e_\infty
=
1-y_\infty.
\]

\[
e_\infty
=
1-
\frac{4K_R}
{1+4K_R}.
\]

\[
\boxed{
e_\infty
=
\frac1{1+4K_R}
}.
\]

Für \(K_R=0.2\):

\[
e_\infty
=
\frac1{1.8}
=
\frac59.
\]

\[
\boxed{
e_\infty
\approx55.56\%
}.
\]

Die Mitschrift auf PDF-S. 95 ist korrekt.

---

# 22. Aufgabe 4d – \(29\%\) Überschwingen

## 22.1 Überschwingformel

Für ein unterdämpftes PT2-System:

\[
\boxed{
M_p
=
\exp\left(
-\frac{\pi D}
{\sqrt{1-D^2}}
\right)
}.
\]

Gegeben:

\[
M_p=0.29.
\]

Nach \(D\) aufgelöst:

\[
\boxed{
D
=
\frac{
-\ln(M_p)
}{
\sqrt{
\pi^2+\ln^2(M_p)
}
}
}.
\]

Einsetzen:

\[
D
\approx0.3666.
\]

---

## 22.2 Reglerverstärkung

Aus:

\[
D
=
\frac3{
\sqrt{
5(1+4K_R)
}
}
\]

folgt:

\[
D^2
=
\frac9{
5(1+4K_R)
}.
\]

\[
1+4K_R
=
\frac9{5D^2}.
\]

\[
\boxed{
K_R
=
\frac14
\left(
\frac9{5D^2}-1
\right)
}.
\]

Mit \(D\approx0.3666\):

\[
\boxed{
K_R
\approx3.10
}.
\]

Dies stimmt mit der offiziellen Lösung \(K_R=3.1\) überein.

---

# 23. Aufgabe 4e – stationärer Fehler bei \(K_R=3.1\)

\[
e_\infty
=
\frac1{1+4K_R}.
\]

\[
e_\infty
=
\frac1{1+12.4}.
\]

\[
e_\infty
=
\frac1{13.4}.
\]

\[
\boxed{
e_\infty
\approx0.0746
=
7.46\%
}.
\]

Gerundet:

\[
\boxed{7.5\%}.
\]

---

# 24. Aufgabe 4f – stationärer Fehler von \(1\%\)

Gefordert:

\[
e_\infty=0.01.
\]

\[
\frac1{1+4K_R}
=
0.01.
\]

\[
1+4K_R=100.
\]

\[
4K_R=99.
\]

\[
\boxed{
K_R=24.75
}.
\]

---

# 25. Aufgabe 4g – Überschwingen für \(K_R=24.75\)

Dämpfung:

\[
D
=
\frac3{
\sqrt{
5(1+4K_R)
}
}.
\]

Mit:

\[
1+4K_R=100
\]

folgt:

\[
D
=
\frac3{\sqrt{500}}
\approx0.1342.
\]

Überschwingverhältnis:

\[
M_p
=
\exp\left(
-\frac{\pi D}
{\sqrt{1-D^2}}
\right).
\]

\[
\boxed{
M_p
\approx0.653
}.
\]

Also:

\[
\boxed{
65.3\%
}
\]

Überschwingen relativ zum stationären Endwert.

### Zielkonflikt

Die Forderung nach nur \(1\%\) stationärem Fehler erzwingt eine sehr hohe P-Verstärkung. Dadurch sinkt die Dämpfung massiv und die Sprungantwort überschwingt stark.

---

# 26. Aufgabe 5 – PT1-Strecke mit I-Regler

## 26.1 Gegeben

\[
G_R(s)
=
\frac1{sT_I},
\]

\[
G_S(s)
=
\frac5{1+3s},
\]

\[
T_I>0.
\]

---

## 26.2 Offener Kreis

\[
G_0(s)
=
G_R(s)G_S(s).
\]

\[
\boxed{
G_0(s)
=
\frac5{
T_Is(1+3s)
}
}.
\]

---

## 26.3 Geschlossene Führungsübertragungsfunktion

\[
G_w(s)
=
\frac{G_0(s)}
{1+G_0(s)}.
\]

\[
G_w(s)
=
\frac{
\dfrac5{T_Is(1+3s)}
}{
1+
\dfrac5{T_Is(1+3s)}
}.
\]

Mit dem Hauptnenner erweitern:

\[
\boxed{
G_w(s)
=
\frac5{
T_Is(1+3s)+5
}
}.
\]

Ausmultiplizieren:

\[
\boxed{
G_w(s)
=
\frac5{
3T_Is^2+T_Is+5
}
}.
\]

Die handschriftliche Rechnung auf PDF-S. 96 ist korrekt.

---

# 27. Aufgabe 5a – stationäre Regelabweichung

Für einen Einheitssprung:

\[
W(s)=\frac1s.
\]

\[
Y(s)=G_w(s)\frac1s.
\]

Endwert:

\[
y_\infty
=
\lim_{s\to0}sY(s).
\]

\[
y_\infty
=
\lim_{s\to0}G_w(s).
\]

\[
y_\infty
=
\frac55
=
1.
\]

Damit:

\[
\boxed{
e_\infty
=
1-y_\infty
=
0
}.
\]

Der Integrator im offenen Kreis eliminiert den stationären Fehler der Sprungführung, sofern der geschlossene Kreis stabil ist.

---

# 28. Aufgabe 5b – höchstens \(8.4\%\) Überschwingen

## 28.1 PT2-Normalform

Geschlossene Funktion:

\[
G_w(s)
=
\frac5{
3T_Is^2+T_Is+5
}.
\]

Durch \(3T_I\) teilen:

\[
G_w(s)
=
\frac{
\dfrac5{3T_I}
}{
s^2+\frac13s+\dfrac5{3T_I}
}.
\]

Vergleich mit:

\[
\frac{
\omega_0^2
}{
s^2+2D\omega_0s+\omega_0^2
}.
\]

Daraus:

\[
\boxed{
\omega_0^2
=
\frac5{3T_I}
}
\]

\[
\boxed{
\omega_0
=
\sqrt{
\frac5{3T_I}
}
}
\]

und:

\[
2D\omega_0=\frac13.
\]

Damit:

\[
D
=
\frac1{6\omega_0}.
\]

Einsetzen von \(\omega_0\):

\[
D
=
\frac16
\sqrt{
\frac{3T_I}{5}
}.
\]

\[
\boxed{
D
=
\sqrt{
\frac{T_I}{60}
}
}.
\]

---

## 28.2 Dämpfung aus der Überschwingvorgabe

Gefordert:

\[
M_p\le0.084.
\]

Grenzfall:

\[
M_p=0.084.
\]

\[
D_{\min}
=
\frac{
-\ln(0.084)
}{
\sqrt{
\pi^2+\ln^2(0.084)
}
}.
\]

\[
D_{\min}
\approx0.61914.
\]

Mit:

\[
D^2=\frac{T_I}{60}
\]

folgt:

\[
T_I=60D^2.
\]

\[
T_I
\approx60\cdot0.61914^2.
\]

\[
\boxed{
T_I
\approx23.0
}.
\]

Damit gilt für höchstens \(8.4\%\) Überschwingen:

\[
\boxed{
T_I\ge23
}
\]

solange die PT2-Auswertung verwendet wird.

Die offizielle Lösung gibt den Grenzwert an:

\[
\boxed{
T_I=23
}.
\]

### Präzisierung

Die Formulierung „höchstens“ erlaubt auch größere \(T_I\). Größere Werte erhöhen die Dämpfung und verringern das Überschwingen, reduzieren aber gleichzeitig die Eigenkreisfrequenz und machen das System träger.

---

# 29. Qualitätsprüfung der Mitschrift

## Sicher lesbar und fachlich bestätigt

- allgemeine Führungs- und Störübertragungen auf PDF-S. 83 und 85,
- Theorie zu P-, I- und D-Anteil auf PDF-S. 84,
- vollständige Aufgabe 1a–b auf PDF-S. 87,
- Sprungantwort Aufgabe 1c auf PDF-S. 88,
- Führungsübertragungen Aufgabe 3 auf PDF-S. 92,
- PT2-Parameter und \(K_R=0.2\) auf PDF-S. 94,
- stationäre Fehler und Überschwingformel auf PDF-S. 95,
- stationäre Fehlerfreiheit des I-Reglers auf PDF-S. 96.

## Unvollständig in der Mitschrift, sauber ergänzt

- Aufgabe 1d–e: Endergebnisse vorhanden, Detailrechnung teilweise abgebrochen,
- Aufgabe 2: keine handschriftliche vollständige Herleitung,
- Aufgabe 3: Sprungantworten und qualitative Bewertung nicht vollständig hergeleitet,
- Aufgabe 4d–g: nur Formeln und Ergebnisse angedeutet,
- Aufgabe 5b: \(T_I=23\) nicht vollständig hergeleitet.

Diese fehlenden Rechenwege wurden oben aus den offiziellen Aufgabenstellungen vollständig rekonstruiert.

---

# 30. Festgestellte Präzisierungen

1. **Aufgabe 2b:**  
   Die offizielle Größe \(Y_R(s)\) enthält wegen des Einheitssprungs den Faktor \(1/s\). Die reine Führungsübertragungsfunktion enthält diesen Faktor nicht.

2. **Aufgabe 3, D-Regler:**  
   Die Sprungantwort beginnt wegen des direkten Durchgriffs bei \(0.6\) und fällt auf 0. Ein D-Regler allein hat somit \(100\%\) stationäre Regeldifferenz.

3. **Aufgabe 4b:**  
   \(K_R=0.2\) ist der Grenzwert. Für alle \(0<K_R\le0.2\) überschwingt das Modell nicht.

4. **Aufgabe 4g:**  
   Der offizielle Wert \(0.653\) ist das relative Überschwingverhältnis, also \(65.3\%\), nicht der absolute Spitzenwert des Ausgangs.

5. **Aufgabe 5b:**  
   Wegen „höchstens \(8.4\%\)“ lautet die vollständige Bedingung \(T_I\ge23\). \(T_I=23\) ist der Grenzfall.

---

# 31. Typische Fehler in Tutorium 07

1. \(G_w\), \(G_{d1}\) und \(G_{d2}\) vertauschen.
2. Bei \(d_1\) den zusätzlichen Streckenfaktor \(G_S\) vergessen.
3. Bei \(d_2\) fälschlich ebenfalls \(G_S\) in den Zähler setzen.
4. \(W(s)=1/s\) mit der Führungsübertragungsfunktion verwechseln.
5. Den Endwertsatz anwenden, ohne die Stabilitätsvoraussetzung zu prüfen.
6. Bei P-Regelung behaupten, der stationäre Fehler werde immer vollständig eliminiert.
7. Beim I-Regler den Pol im Ursprung durch unzulässiges Kürzen verlieren.
8. Dem D-Regler eine Verbesserung der stationären Genauigkeit zuschreiben.
9. Den sofortigen Sprung bei einer Ausgangsstörung \(d_2\) übersehen.
10. Einen verschachtelten Regelkreis in einem Schritt zusammenfassen und dabei die innere Schleife falsch behandeln.
11. Bei Aufgabe 3 die Sprungantwort von \(G_w\) statt von \(G_w/s\) rücktransformieren.
12. Beim D-Regler den gekürzten \(s\)-Faktor und den Direktdurchgriff nicht erkennen.
13. PT2-Nenner nicht normieren, bevor \(\omega_0\) und \(D\) verglichen werden.
14. Überschwingverhältnis und absoluten Spitzenwert verwechseln.
15. Aus „höchstens“ einen einzigen exakten Parameterwert statt einer Ungleichung machen.

---

# 32. Klausurstrategie

## 32.1 Führungs- und Störübertragungen

1. Alle Eingangssignale im Blockbild markieren.
2. Signalgleichung für \(y\) aufstellen.
3. Alle \(y\)-Terme auf eine Seite bringen.
4. Superpositionsform schreiben:

\[
Y=G_wW+G_{d1}D_1+G_{d2}D_2.
\]

5. Für jede gesuchte Übertragung alle anderen Eingänge auf 0 setzen.
6. Doppelbrüche vollständig beseitigen.

---

## 32.2 Stationärer Fehler

1. Eingang identifizieren:

\[
W(s)=\frac1s
\]

bei Einheitssprung.

2. Ausgang bilden:

\[
Y=G_wW.
\]

3. Endwertsatz:

\[
y_\infty
=
\lim_{s\to0}sY(s).
\]

4. Regelabweichung:

\[
e_\infty
=
1-y_\infty.
\]

5. Stabilität des geschlossenen Kreises prüfen.

---

## 32.3 PT2-Parameteraufgaben

1. Geschlossene Übertragungsfunktion bilden.
2. Nenner normieren.
3. Mit

\[
s^2+2D\omega_0s+\omega_0^2
\]

vergleichen.
4. Erst \(\omega_0\), dann \(D\) bestimmen.
5. Überschwingen:

\[
M_p
=
e^{-\pi D/\sqrt{1-D^2}}.
\]

6. Stationäre Genauigkeit separat über \(G_w(0)\) bestimmen.

---

# 33. NotebookLM-Verifikation

--- NOTEBOOKLM-PROMPT ---

Prüfe ausschließlich anhand der hochgeladenen offiziellen Regelungstechnik-Unterlagen drei Präzisierungen aus „Tutorium 07 – Einführung in den Regelkreis“:

1. Aufgabe 2b:
Unterscheide die reine Führungsübertragungsfunktion des inneren Drehzahlkreises von der Ausgangsgröße \(Y_R(s)\) bei Einheitssprung. Gehört der Faktor \(1/s\) zur Übertragungsfunktion oder zur Eingangsgröße?

2. Aufgabe 3 mit D-Regler:
Für
\[
G_S(s)=\frac1{s+2},
\qquad
G_R(s)=\frac32s
\]
prüfe die offizielle Sprungantwort
\[
y(t)=\frac35e^{-4t/5}.
\]
Bestimme \(y(0^+)\), \(y(\infty)\) und die stationäre Regeldifferenz.

3. Aufgabe 5b:
Die offizielle Lösung nennt \(T_I=23\), obwohl „höchstens \(8.4\%\) Überschwingen“ gefordert ist. Prüfe, ob mathematisch \(T_I\ge23\) gilt und \(T_I=23\) nur den Grenzfall beschreibt.

Belege jede direkte Quellenaussage mit Dokumentname und genauer Seite. Trenne Quellenaussage und eigene mathematische Herleitung.

--- ENDE ---

---

# 34. Kompaktformelsammlung Tutorium 07

## Offener Kreis

\[
\boxed{
G_0=G_RG_S
}.
\]

## Führungsübertragung

\[
\boxed{
G_w
=
\frac{G_RG_S}
{1+G_RG_S}
}.
\]

## Störung vor der Strecke

\[
\boxed{
G_{d1}
=
\frac{G_S}
{1+G_RG_S}
}.
\]

## Störung nach der Strecke

\[
\boxed{
G_{d2}
=
\frac1{1+G_RG_S}
}.
\]

## Sensitivität

\[
\boxed{
S=\frac1{1+G_0}
}.
\]

## Komplementäre Sensitivität

\[
\boxed{
T=\frac{G_0}{1+G_0}
}.
\]

## Zusammenhang

\[
\boxed{
S+T=1
}.
\]

## Endwertsatz

\[
\boxed{
f_\infty
=
\lim_{s\to0}sF(s)
}.
\]

## Stationäre Regelabweichung bei Einheitssprung

\[
\boxed{
e_\infty
=
1-G_w(0)
}.
\]

## PT2-Normalform

\[
\boxed{
s^2+2D\omega_0s+\omega_0^2
}.
\]

## Überschwingverhältnis

\[
\boxed{
M_p
=
\exp\left(
-\frac{\pi D}
{\sqrt{1-D^2}}
\right)
}.
\]

## Dämpfung aus Überschwingen

\[
\boxed{
D
=
\frac{
-\ln M_p
}{
\sqrt{
\pi^2+\ln^2M_p
}
}
}.
\]

---

# Tutorium 09 – Stabilität I

## 1. Quellen und Seitenbereich

### Primärquellen

1. **RT-Tutorien-Mitschrift.pdf**, PDF-Seiten 99–110
   - S. 99: offizielles Aufgabenblatt 1/4
   - S. 100–102: Theorie, Aufgabe 1a–c und handschriftliche Eigenwertrechnungen
   - S. 103: offizielles Aufgabenblatt 2/4
   - S. 104–105: Aufgabe 2a, 2c und 2h
   - S. 106: offizielles Aufgabenblatt 3/4
   - S. 107–108: handschriftliche Ansätze zu Aufgabe 3b und 3d
   - S. 109: offizielles Aufgabenblatt 4/4
   - S. 110: leer

2. **RT-Tutorien-Mitschrift.pdf**, PDF-Seiten 111–122  
   Diese Seiten sind eine vollständige Dublette der Seiten 99–110. Sie enthalten keine zusätzlichen Rechenwege.

3. **Regelungstechnik_Tutorium_komplett.pdf**, Tutorium 09, Blattseiten 1/4–4/4  
   Offizielle Aufgaben und Endergebnisse.

4. **skript.pdf**
   - gedruckte S. 99–104: Stabilität im Zeitbereich
   - gedruckte S. 104–109: E/A-Stabilität
   - gedruckte S. 109–112: Hurwitz-Kriterium
   - gedruckte S. 112–115: Routh-Kriterium

---

# 2. Begriffe sauber trennen

## 2.1 Stabilität im Zustandsraum

Für

\[
\dot x=Ax
\]

bestimmen die Eigenwerte von \(A\) das freie Zeitverhalten.

### Asymptotische Stabilität

\[
\boxed{
\operatorname{Re}\lambda_i<0
\quad
\text{für alle }i
}
\]

Dann gilt:

\[
x(t)\to0.
\]

### Instabilität

Sobald mindestens ein Eigenwert

\[
\operatorname{Re}\lambda_i>0
\]

besitzt, wächst mindestens ein Eigenvorgang exponentiell.

### Grenz- bzw. marginale Stabilität

Eigenwerte auf der imaginären Achse können beschränkte Dauerschwingungen oder konstante Zustände erzeugen. Dafür müssen diese Eigenwerte semisimpel sein, also keine wachsenden Jordanterme erzeugen.

Klausurtauglich:

- alle Realteile negativ: asymptotisch stabil,
- mindestens ein Realteil positiv: instabil,
- Realteile höchstens null und einfache/semisimple imaginäre Eigenwerte: grenzstabil.

Quelle: `skript.pdf`, gedruckte S. 102, Korollar 5.5.

---

## 2.2 Mathematische Präzisierung zur Jordanform

Ein Jordanblock zu einem Eigenwert mit

\[
\operatorname{Re}\lambda=0
\]

und Blocklänge größer 1 erzeugt Faktoren wie

\[
te^{j\omega t},
\]

die unbeschränkt wachsen. Das System ist dann instabil.

Bei

\[
\operatorname{Re}\lambda<0
\]

klingen dagegen auch Terme

\[
t^ke^{\lambda t}
\]

gegen null. Für asymptotische Stabilität reicht daher mathematisch, dass sämtliche Eigenwerte strikt negative Realteile besitzen; Diagonalisierbarkeit ist dafür nicht erforderlich.

Diese Präzisierung ist allgemeines lineares Systemwissen. Für Klausurantworten ist die sichere Kernaussage:

\[
\operatorname{Re}\lambda_i<0
\Rightarrow
\text{asymptotisch stabil}.
\]

---

## 2.3 E/A- bzw. BIBO-Stabilität

Ein System ist E/A-stabil, wenn jeder beschränkte Eingang einen beschränkten Ausgang erzeugt.

Für eine rationale, gekürzte Übertragungsfunktion gilt:

\[
\boxed{
\operatorname{Re}p_i<0
\quad
\text{für alle Pole}
}
\]

genau dann, wenn das System E/A-stabil ist.

Quelle: `skript.pdf`, gedruckte S. 107, Theorem 5.12.

### Konsequenz

Pole auf der imaginären Achse sind **nicht** E/A-stabil. Ein Resonanzeingang kann einen unbeschränkt wachsenden Ausgang erzeugen.

---

## 2.4 Interne Stabilität und E/A-Stabilität sind nicht identisch

Eine instabile interne Mode kann durch eine Pol-Nullstellen-Kürzung in der Übertragungsfunktion unsichtbar werden.

Daher:

- Eigenwerte von \(A\): interne bzw. Zustandsstabilität,
- Pole der gekürzten Übertragungsfunktion: E/A-Stabilität.

Ohne vollständige Steuer- und Beobachtbarkeit darf man beide Begriffe nicht blind gleichsetzen.

---

# 3. Theoriefragen

## 3.1 Woran erkennt man Stabilität im Zustandsraum?

An den Eigenwerten der Systemmatrix \(A\):

\[
\det(\lambda I-A)=0.
\]

- alle \(\operatorname{Re}\lambda_i<0\): asymptotisch stabil,
- mindestens ein \(\operatorname{Re}\lambda_i>0\): instabil,
- Pole auf der imaginären Achse: Grenzfall; Jordanstruktur prüfen.

Die handschriftliche Zusammenfassung steht auf Mitschrift-PDF-S. 100–101.

---

## 3.2 Welche Rolle spielen Pole und Nullstellen?

### Pole

Pole bestimmen die Exponentialanteile des Zeitverhaltens:

\[
p=\sigma+j\omega
\quad\Rightarrow\quad
e^{\sigma t}
\left(
C_1\cos\omega t+C_2\sin\omega t
\right).
\]

Daher:

- \(\sigma<0\): abklingend,
- \(\sigma=0\): dauerhaft bzw. grenzstabil,
- \(\sigma>0\): anwachsende Mode.

### Nullstellen

Nullstellen beeinflussen:

- Form und Vorzeichen der Antwort,
- Frequenzabschwächung,
- Überschwingen und inverse Antwort,
- Steuer- und Beobachtbarkeit bei Kürzungen.

Sie bestimmen die E/A-Stabilität nicht direkt. Entscheidend sind die Pole der gekürzten Übertragungsfunktion.

Die Mitschrift formuliert auf PDF-S. 101 korrekt: „Stabilität wird durch Pole bestimmt, Nullstellen nicht.“

---

## 3.3 Was bedeutet ein Pol bei \(s=0\)?

Ein Pol im Ursprung entspricht einem Integrator:

\[
G(s)=\frac K{s}.
\]

Bei einem Einheitssprung:

\[
U(s)=\frac1s
\]

folgt:

\[
Y(s)=\frac K{s^2}
\]

und damit:

\[
y(t)=Kt.
\]

Der Ausgang wächst unbeschränkt.

Daher:

- nicht asymptotisch stabil,
- nicht E/A-stabil,
- im freien Zustandsverhalten eventuell grenzstabil, wenn der Null-Eigenwert einfach bzw. semisimpel ist.

Die pauschale Aussage „Pol bei \(s=0\) ist grenzstabil“ gilt nur für die interne freie Dynamik, nicht für BIBO-Stabilität.

---

## 3.4 Warum braucht man Hurwitz und Routh?

Bei Polynomen höherer Ordnung ist eine explizite Polberechnung:

- aufwendig,
- fehleranfällig,
- bei Parameterpolynomen oft unbrauchbar.

Hurwitz und Routh liefern Stabilitätsbedingungen direkt aus den Koeffizienten des charakteristischen Polynoms.

Zusätzlich kann das Routh-Schema die Anzahl der Pole in der rechten Halbebene über Vorzeichenwechsel der ersten Spalte bestimmen.

Die Mitschrift auf PDF-S. 100–101 nennt genau diesen Vorteil.

---

# 4. Hurwitz-Kriterium

## 4.1 Ausgangspolynom

\[
N(s)
=
a_ns^n+a_{n-1}s^{n-1}+\dots+a_1s+a_0.
\]

Zuerst wird zweckmäßig auf

\[
a_n>0
\]

normiert.

---

## 4.2 Notwendige Bedingung

Für strikt negative Realteile aller Nullstellen müssen sämtliche Koeffizienten positiv sein:

\[
\boxed{
a_i>0
}.
\]

Positive Koeffizienten allein reichen ab Ordnung 3 nicht aus.

---

## 4.3 Hurwitz-Matrix

Nach Skriptkonvention:

\[
H=
\begin{bmatrix}
a_1&a_3&a_5&\cdots\\
a_0&a_2&a_4&\cdots\\
0&a_1&a_3&\cdots\\
0&a_0&a_2&\cdots\\
\vdots&\vdots&\vdots&\ddots
\end{bmatrix}.
\]

Alle führenden Hauptabschnittsdeterminanten müssen strikt positiv sein:

\[
\boxed{
D_i>0
}.
\]

Quelle: `skript.pdf`, gedruckte S. 110–111, Definition 5.17 und Theorem 5.18.

---

## 4.4 Schnellbedingungen

### Zweite Ordnung

\[
a_2s^2+a_1s+a_0.
\]

Für \(a_2>0\):

\[
\boxed{
a_1>0,\qquad a_0>0
}.
\]

### Dritte Ordnung

\[
a_3s^3+a_2s^2+a_1s+a_0.
\]

Für positive Koeffizienten zusätzlich:

\[
\boxed{
a_2a_1>a_3a_0
}.
\]

### Vierte Ordnung

Zusätzlich zu positiven Koeffizienten:

\[
D_2=a_1a_2-a_0a_3>0,
\]

\[
D_3=a_1a_2a_3-a_1^2a_4-a_0a_3^2>0.
\]

---

# 5. Routh-Kriterium

## 5.1 Standardtabelle für ein kubisches Polynom

Für

\[
a_3s^3+a_2s^2+a_1s+a_0
\]

gilt:

\[
\begin{array}{c|cc}
s^3&a_3&a_1\\
s^2&a_2&a_0\\
s^1&\dfrac{a_2a_1-a_3a_0}{a_2}&0\\
s^0&a_0&
\end{array}
\]

Asymptotische Stabilität liegt genau dann vor, wenn alle Einträge der ersten Spalte dasselbe positive Vorzeichen besitzen.

---

## 5.2 Aussage über instabile Pole

Die Anzahl der Vorzeichenwechsel in der ersten Spalte entspricht der Anzahl der Nullstellen in der rechten Halbebene.

---

## 5.3 Randfälle

### Null in der ersten Spalte

Ein Hilfsparameter oder eine geeignete Grenzwertbetrachtung ist nötig.

### Ganze Nullzeile

Es existiert ein symmetrisches Wurzelpaar, typischerweise auf der imaginären Achse. Das Hilfspolynom aus der darüberliegenden Zeile wird verwendet.

In diesem Tutorium treten solche Nullzeilen an den Stabilitätsgrenzen auf.

---

# 6. Aufgabe 1a – \(\dot x=x\)

## Systemmatrix

\[
A=[1].
\]

Eigenwert:

\[
\boxed{\lambda=1}.
\]

Da:

\[
\operatorname{Re}\lambda=1>0
\]

gilt:

\[
\boxed{\text{instabil}}.
\]

Lösung:

\[
x(t)=e^tx_0.
\]

Die Mitschrift auf PDF-S. 101 ist korrekt.

---

# 7. Aufgabe 1b – dreidimensionales System

## Gegeben

\[
A=
\begin{bmatrix}
0&1&0\\
-5&-4&1\\
0&0&-1
\end{bmatrix}.
\]

Die Matrix ist blockobere Dreiecksmatrix. Daher besteht das Spektrum aus:

1. den Eigenwerten des Blocks

\[
A_{2\times2}
=
\begin{bmatrix}
0&1\\
-5&-4
\end{bmatrix},
\]

2. dem Eigenwert

\[
\lambda_3=-1.
\]

---

## 7.1 Eigenwerte des \(2\times2\)-Blocks

\[
\det(\lambda I-A_{2\times2})
=
\begin{vmatrix}
\lambda&-1\\
5&\lambda+4
\end{vmatrix}.
\]

\[
=
\lambda(\lambda+4)+5.
\]

\[
=
\lambda^2+4\lambda+5.
\]

Nullstellen:

\[
\lambda_{1,2}
=
-2\pm\sqrt{4-5}.
\]

\[
\boxed{
\lambda_{1,2}
=
-2\pm j
}.
\]

Zusammen:

\[
\boxed{
\lambda_{1,2}=-2\pm j,\qquad \lambda_3=-1
}.
\]

Alle Realteile sind negativ:

\[
\boxed{\text{asymptotisch stabil}}.
\]

Die Rechnung auf Mitschrift-PDF-S. 101–102 ist korrekt.

---

# 8. Aufgabe 1c – Feder-Masse-Dämpfer-System

## Gegeben

\[
A=
\begin{bmatrix}
0&1\\
-\dfrac{k}{m}&-\dfrac{d}{m}
\end{bmatrix},
\qquad
m>0.
\]

Charakteristisches Polynom:

\[
\det(\lambda I-A)
=
\begin{vmatrix}
\lambda&-1\\
\dfrac{k}{m}&\lambda+\dfrac{d}{m}
\end{vmatrix}.
\]

\[
=
\lambda
\left(
\lambda+\frac dm
\right)
+\frac km.
\]

\[
\boxed{
N(\lambda)
=
\lambda^2+\frac dm\lambda+\frac km
}.
\]

---

## 8.1 Stabilitätsbedingung

Für ein Polynom zweiter Ordnung müssen die normierten Koeffizienten positiv sein:

\[
\frac dm>0,
\qquad
\frac km>0.
\]

Mit \(m>0\):

\[
\boxed{
d>0,\qquad k>0
}.
\]

Damit sind beide Eigenwerte strikt in der linken Halbebene.

---

## 8.2 Eigenwerte

\[
\lambda_{1,2}
=
-\frac d{2m}
\pm
\sqrt{
\left(
\frac d{2m}
\right)^2
-\frac km
}.
\]

### Schwingungsfall

\[
\left(
\frac d{2m}
\right)^2-\frac km<0.
\]

\[
\boxed{
k>\frac{d^2}{4m}
}.
\]

### Aperiodischer Grenzfall

\[
\boxed{
k=\frac{d^2}{4m}
}.
\]

### Reelle Pole ohne Schwingung

\[
\boxed{
0<k<\frac{d^2}{4m}
}.
\]

Alle drei Fälle sind bei \(d>0,k>0\) asymptotisch stabil.

---

## 8.3 [UNKLAR – OFFIZIELLER ZUSATZ]

Die offizielle Lösung ergänzt:

\[
k<\frac{5d^2}{16m}
\]

„bei Randbedingungen“.

Diese Ungleichung folgt weder aus der Stabilitätsbedingung noch aus der üblichen Grenze zwischen reellen und komplexen Polen. Diese Grenze lautet:

\[
k=\frac{d^2}{4m}.
\]

Die handschriftliche Rechnung auf PDF-S. 102 erhält korrekt nur:

\[
d>0,\qquad k>0.
\]

Der Faktor \(5/16\) bleibt durch die verfügbaren Aufgabenangaben unbegründet und wird nicht stillschweigend übernommen.

---

# 9. Aufgabe 2a – Pole und Nullstellen

## Gegeben

\[
G(s)
=
\frac{s^2-\frac14}{s-10}.
\]

Zähler faktorisieren:

\[
s^2-\frac14
=
\left(
s-\frac12
\right)
\left(
s+\frac12
\right).
\]

Nullstellen:

\[
\boxed{
n_{1,2}=\pm\frac12
}.
\]

Pol:

\[
\boxed{
p_1=10
}.
\]

Da:

\[
\operatorname{Re}p_1>0
\]

ist das System:

\[
\boxed{\text{E/A-instabil}}.
\]

Die Rechnung auf Mitschrift-PDF-S. 104 ist korrekt.

---

# 10. Aufgabe 2b – allgemeines System zweiter Ordnung

## Gegeben

\[
G(s)
=
\frac{es^2+fs+g}{as^2+bs+c},
\qquad
a\neq0,\ e\neq0.
\]

## 10.1 Nullstellen

\[
es^2+fs+g=0.
\]

\[
\boxed{
n_{1,2}
=
-\frac f{2e}
\pm
\sqrt{
\left(
\frac f{2e}
\right)^2
-\frac ge
}
}.
\]

---

## 10.2 Pole

\[
as^2+bs+c=0.
\]

\[
\boxed{
p_{1,2}
=
-\frac b{2a}
\pm
\sqrt{
\left(
\frac b{2a}
\right)^2
-\frac ca
}
}.
\]

---

## 10.3 Stabilitätsbedingung

Nach Normierung auf positiven Leitkoeffizienten:

\[
\boxed{
\frac ba>0,
\qquad
\frac ca>0
}.
\]

Die offizielle Form

\[
\frac b{2a}>0
\]

ist dazu äquivalent.

Die Nullstellen beeinflussen die E/A-Stabilität nicht, sofern keine instabile Pol-Nullstellen-Kürzung verborgen wird.

---

# 11. Aufgabe 2c – ungedämpfter Schwinger

## Gegeben

\[
\ddot y(t)+9y(t)=5x(t).
\]

Bei verschwindenden Anfangsbedingungen:

\[
s^2Y(s)+9Y(s)=5X(s).
\]

\[
Y(s)(s^2+9)=5X(s).
\]

Übertragungsfunktion:

\[
\boxed{
G(s)
=
\frac{Y(s)}{X(s)}
=
\frac5{s^2+9}
}.
\]

Nullstellen: keine.

Pole:

\[
s^2+9=0.
\]

\[
\boxed{
p_{1,2}=\pm3j
}.
\]

---

## 11.1 Stabilitätsbewertung

### Freie Zustandsdynamik

Die Pole sind einfach und liegen auf der imaginären Achse. Das System zeigt eine ungedämpfte Dauerschwingung und ist marginal bzw. grenzstabil.

### E/A-Stabilität

Da die Pole nicht strikt in der linken Halbebene liegen:

\[
\boxed{
\text{nicht E/A-stabil}
}.
\]

Ein sinusförmiger Eingang mit Frequenz \(3\,\mathrm{rad/s}\) erzeugt Resonanz und einen unbeschränkt wachsenden Ausgang.

### [KORRIGIERT]

Die Aufgabe trägt die Überschrift „E/A-Stabilität“, die offizielle Lösung nennt das System jedoch „grenzstabil“. Das ist nur als Aussage zur freien Zustandsdynamik korrekt, nicht als BIBO-Aussage.

Die handschriftliche Rechnung auf PDF-S. 104 ist rechnerisch korrekt.

---

# 12. Aufgabe 2d–g – Stabilität und Schwingungsverhalten

## 12.1 Aufgabe 2d

\[
p_1=1,\qquad p_2=-4.
\]

Ein Pol liegt rechts:

\[
\boxed{\text{instabil}}.
\]

Beide Pole sind reell:

\[
\boxed{\text{keine Schwingung}}.
\]

---

## 12.2 Aufgabe 2e

\[
p_{1,2}=1\pm j,
\qquad
p_3=10.
\]

Positive Realteile:

\[
\boxed{\text{instabil}}.
\]

Das komplexe Paar erzeugt Schwingungsanteile:

\[
\boxed{\text{instabil und schwingend}}.
\]

---

## 12.3 Aufgabe 2f

\[
p_1=0.
\]

Freies Verhalten:

\[
e^{0t}=1.
\]

Bei einfachem Pol:

\[
\boxed{\text{grenzstabil im Zustandsraum}}.
\]

Als Übertragungsfunktion mit Pol bei null:

\[
\boxed{\text{nicht E/A-stabil}}.
\]

---

## 12.4 Aufgabe 2g

\[
p_{1,2}=\pm2j.
\]

Freies Verhalten:

\[
\cos(2t),\qquad \sin(2t).
\]

\[
\boxed{\text{grenzstabil mit Dauerschwingung}}.
\]

E/A-Bewertung:

\[
\boxed{\text{nicht BIBO-stabil}}.
\]

---

# 13. Aufgabe 2h – Stabilisierung durch einen P-Regler

## 13.1 Strecke

\[
G_S(s)
=
\frac{s^2-\frac14}{s-10}.
\]

Regler:

\[
G_R(s)=k_p.
\]

Negative Einheitsrückführung:

\[
G_w(s)
=
\frac{k_pG_S(s)}
{1+k_pG_S(s)}.
\]

---

## 13.2 Geschlossene Übertragungsfunktion

\[
G_w(s)
=
\frac{
k_p\left(s^2-\frac14\right)
}{
s-10+k_p\left(s^2-\frac14\right)
}.
\]

Charakteristisches Polynom:

\[
\boxed{
N(s)
=
k_ps^2+s-10-\frac{k_p}{4}
}.
\]

Koeffizienten:

\[
a_2=k_p,
\qquad
a_1=1,
\qquad
a_0=-10-\frac{k_p}{4}.
\]

---

## 13.3 Stabilitätsbedingungen

Für \(a_2>0\):

\[
k_p>0.
\]

Zusätzlich:

\[
a_0>0.
\]

\[
-10-\frac{k_p}{4}>0.
\]

\[
-\frac{k_p}{4}>10.
\]

\[
\boxed{
k_p<-40
}.
\]

Die Bedingungen

\[
k_p>0
\]

und

\[
k_p<-40
\]

können nicht gleichzeitig erfüllt werden.

Ergebnis:

\[
\boxed{
\text{Die Strecke ist mit einem reinen P-Regler nicht stabilisierbar.}
}
\]

Die handschriftliche Rechnung auf PDF-S. 105 ist korrekt.

---

# 14. Aufgabe 3a – P-Regler an einer Strecke dritter Ordnung

## 14.1 Gegeben

\[
G_S(s)
=
\frac1{s^3+8s^2+3s+1},
\]

\[
G_R(s)=K_R,
\qquad
K_R>0.
\]

---

## 14.2 Geschlossener Kreis

\[
G_w(s)
=
\frac{K_R}
{s^3+8s^2+3s+1+K_R}.
\]

Charakteristisches Polynom:

\[
\boxed{
N(s)
=
s^3+8s^2+3s+1+K_R
}.
\]

Koeffizienten:

\[
a_3=1,\quad
a_2=8,\quad
a_1=3,\quad
a_0=1+K_R.
\]

---

## 14.3 Hurwitz-Prüfung

Notwendige Bedingung:

\[
K_R>-1.
\]

Mit der Vorgabe \(K_R>0\) ist dies erfüllt.

Hurwitz-Matrix:

\[
H=
\begin{bmatrix}
3&1&0\\
1+K_R&8&0\\
0&3&1
\end{bmatrix}.
\]

Determinanten:

\[
D_1=3>0.
\]

\[
D_2
=
3\cdot8-(1+K_R)\cdot1.
\]

\[
D_2
=
23-K_R.
\]

\[
D_3
=
1\cdot D_2
=
23-K_R.
\]

Strikte Stabilitätsbedingung:

\[
\boxed{
0<K_R<23
}.
\]

---

## 14.4 Routh-Schema

\[
\begin{array}{c|cc}
s^3&1&3\\
s^2&8&1+K_R\\
s^1&\dfrac{23-K_R}{8}&0\\
s^0&1+K_R&
\end{array}
\]

Erste Spalte positiv:

\[
1>0,\quad
8>0,\quad
\frac{23-K_R}{8}>0,\quad
1+K_R>0.
\]

Daraus erneut:

\[
\boxed{
0<K_R<23
}.
\]

---

## 14.5 [KORRIGIERT – OFFIZIELLE GRENZE]

Die offizielle Lösung nennt:

\[
0<K_R\le23.
\]

Bei

\[
K_R=23
\]

gilt:

\[
N(s)
=
s^3+8s^2+3s+24.
\]

Faktorisieren:

\[
N(s)
=
(s+8)(s^2+3).
\]

Pole:

\[
-8,\qquad \pm j\sqrt3.
\]

Der Kreis ist an dieser Grenze nicht asymptotisch und nicht E/A-stabil, sondern nur grenzstabil in der freien Dynamik.

Für Hurwitz- bzw. E/A-Stabilität ist daher die strikte Bedingung korrekt:

\[
\boxed{
0<K_R<23
}.
\]

---

# 15. Aufgabe 3b – PI-Regler an einer PT2-Strecke

## 15.1 Gegeben

\[
G_S(s)
=
\frac3{s^2+3s+1},
\]

\[
G_R(s)
=
K_R
\frac{1+sT_N}{sT_N},
\]

\[
K_R,T_N>0.
\]

---

## 15.2 Geschlossener Kreis

Offener Kreis:

\[
G_0(s)
=
\frac{
3K_R(1+sT_N)
}{
sT_N(s^2+3s+1)
}.
\]

Geschlossene Führungsübertragung:

\[
\boxed{
G_w(s)
=
\frac{
3K_R(1+sT_N)
}{
T_Ns^3+3T_Ns^2+T_N(1+3K_R)s+3K_R
}
}.
\]

Charakteristisches Polynom:

\[
\boxed{
N(s)
=
T_Ns^3
+
3T_Ns^2
+
T_N(1+3K_R)s
+
3K_R
}.
\]

---

## 15.3 Hurwitz-Prüfung

Koeffizienten:

\[
a_3=T_N,
\]

\[
a_2=3T_N,
\]

\[
a_1=T_N(1+3K_R),
\]

\[
a_0=3K_R.
\]

Bei \(K_R,T_N>0\) sind alle positiv.

Entscheidende Determinante:

\[
D_2
=
a_1a_2-a_0a_3.
\]

\[
D_2
=
T_N(1+3K_R)\cdot3T_N
-
3K_R T_N.
\]

\[
D_2
=
3T_N
\left[
T_N(1+3K_R)-K_R
\right].
\]

Daher:

\[
T_N(1+3K_R)-K_R>0.
\]

\[
\boxed{
T_N
>
\frac{K_R}{1+3K_R}
}.
\]

---

## 15.4 Routh-Schema

\[
\begin{array}{c|cc}
s^3&T_N&T_N(1+3K_R)\\
s^2&3T_N&3K_R\\
s^1&T_N(1+3K_R)-K_R&0\\
s^0&3K_R&
\end{array}
\]

Alle Einträge der ersten Spalte müssen positiv sein. Damit erneut:

\[
\boxed{
K_R,T_N>0,
\qquad
T_N>
\frac{K_R}{1+3K_R}
}.
\]

---

## 15.5 [KORRIGIERT – OFFIZIELLE GRENZE]

Die offizielle Lösung verwendet:

\[
T_N\ge
\frac{K_R}{1+3K_R}.
\]

Bei Gleichheit verschwindet die \(s^1\)-Zeile des Routh-Schemas. Es entsteht ein imaginäres Polpaar. Die Grenze ist nicht asymptotisch bzw. E/A-stabil.

Daher muss für strikte Hurwitz-Stabilität gelten:

\[
\boxed{
T_N>
\frac{K_R}{1+3K_R}
}.
\]

Die handschriftliche Rechnung auf PDF-S. 107 erhält im Wesentlichen dieselbe Bedingung, behandelt den Rand aber nicht sauber.

---

# 16. Aufgabe 3c – PI-Regler am PT2-System

## 16.1 Gegeben

\[
G_S(s)
=
\frac{\omega_0^2}
{s^2+2D\omega_0s+\omega_0^2},
\]

\[
G_R(s)
=
\frac{1+4s}{2s},
\]

\[
\omega_0>0,
\qquad
0<D<1.
\]

---

## 16.2 Geschlossener Kreis

Offener Kreis:

\[
G_0(s)
=
\frac{
\omega_0^2(1+4s)
}{
2s
\left(
s^2+2D\omega_0s+\omega_0^2
\right)
}.
\]

Geschlossene Führungsübertragung:

\[
\boxed{
G_w(s)
=
\frac{
\omega_0^2(1+4s)
}{
2s^3
+
4D\omega_0s^2
+
6\omega_0^2s
+
\omega_0^2
}
}.
\]

Charakteristisches Polynom:

\[
\boxed{
N(s)
=
2s^3
+
4D\omega_0s^2
+
6\omega_0^2s
+
\omega_0^2
}.
\]

---

## 16.3 Hurwitz-Prüfung

Koeffizienten:

\[
a_3=2,
\]

\[
a_2=4D\omega_0,
\]

\[
a_1=6\omega_0^2,
\]

\[
a_0=\omega_0^2.
\]

Bei den Vorgaben sind alle positiv.

Entscheidende Bedingung:

\[
a_2a_1>a_3a_0.
\]

\[
4D\omega_0\cdot6\omega_0^2
>
2\omega_0^2.
\]

\[
24D\omega_0^3
>
2\omega_0^2.
\]

Da \(\omega_0>0\):

\[
12D\omega_0>1.
\]

\[
\boxed{
D>
\frac1{12\omega_0}
}.
\]

Zusammen mit \(D<1\) existiert nur dann ein zulässiger Bereich, wenn:

\[
\omega_0>\frac1{12}.
\]

---

## 16.4 Routh-Schema

\[
\begin{array}{c|cc}
s^3&2&6\omega_0^2\\
s^2&4D\omega_0&\omega_0^2\\
s^1&
\dfrac{
\omega_0(12D\omega_0-1)
}{
2D
}
&0\\
s^0&\omega_0^2&
\end{array}
\]

Erste Spalte positiv:

\[
\boxed{
D>
\frac1{12\omega_0}
}.
\]

---

## 16.5 [KORRIGIERT – OFFIZIELLE GRENZE]

Offiziell steht:

\[
D\ge
\frac1{12\omega_0}.
\]

Bei Gleichheit verschwindet die \(s^1\)-Zeile. Der Kreis besitzt ein imaginäres Polpaar und ist nicht asymptotisch bzw. E/A-stabil.

Die strikte Stabilitätsbedingung lautet:

\[
\boxed{
D>
\frac1{12\omega_0}
}.
\]

---

# 17. Aufgabe 3d – I-Regler und drei PT1-Glieder

## 17.1 Gegeben

\[
G_S(s)
=
\frac4{(1+sT_1)^3},
\]

\[
G_R(s)
=
\frac1{sT_I},
\]

\[
T_1,T_I>0.
\]

---

## 17.2 Geschlossener Kreis

Offener Kreis:

\[
G_0(s)
=
\frac4{
sT_I(1+sT_1)^3
}.
\]

Geschlossene Führungsübertragung:

\[
\boxed{
G_w(s)
=
\frac4{
sT_I(1+sT_1)^3+4
}
}.
\]

Binomische Entwicklung:

\[
(1+sT_1)^3
=
1+3sT_1+3s^2T_1^2+s^3T_1^3.
\]

Multiplikation mit \(sT_I\):

\[
sT_I(1+sT_1)^3
=
T_Is
+
3T_1T_Is^2
+
3T_1^2T_Is^3
+
T_1^3T_Is^4.
\]

Charakteristisches Polynom:

\[
\boxed{
N(s)
=
T_1^3T_Is^4
+
3T_1^2T_Is^3
+
3T_1T_Is^2
+
T_Is
+
4
}.
\]

---

## 17.3 Hurwitz-Prüfung

Koeffizienten:

\[
a_4=T_1^3T_I,
\]

\[
a_3=3T_1^2T_I,
\]

\[
a_2=3T_1T_I,
\]

\[
a_1=T_I,
\]

\[
a_0=4.
\]

Alle Koeffizienten sind positiv.

### Erste Determinante

\[
D_1=a_1=T_I>0.
\]

### Zweite Determinante

\[
D_2=a_1a_2-a_0a_3.
\]

\[
D_2
=
T_I\cdot3T_1T_I
-
4\cdot3T_1^2T_I.
\]

\[
D_2
=
3T_1T_I(T_I-4T_1).
\]

Daraus:

\[
T_I>4T_1.
\]

### Dritte Determinante

\[
D_3
=
a_1a_2a_3-a_1^2a_4-a_0a_3^2.
\]

Einsetzen:

\[
D_3
=
T_I(3T_1T_I)(3T_1^2T_I)
-
T_I^2(T_1^3T_I)
-
4(3T_1^2T_I)^2.
\]

\[
D_3
=
9T_1^3T_I^3
-
T_1^3T_I^3
-
36T_1^4T_I^2.
\]

\[
D_3
=
4T_1^3T_I^2(2T_I-9T_1).
\]

Damit:

\[
T_I>\frac92T_1.
\]

Diese Bedingung ist stärker als \(T_I>4T_1\).

### Vierte Determinante

\[
D_4=a_0D_3=4D_3.
\]

Daher keine zusätzliche Bedingung.

Ergebnis:

\[
\boxed{
T_1,T_I>0,
\qquad
T_I>\frac92T_1
}.
\]

---

## 17.4 Routh-Schema

\[
\begin{array}{c|ccc}
s^4&T_1^3T_I&3T_1T_I&4\\
s^3&3T_1^2T_I&T_I&0\\
s^2&\dfrac83T_1T_I&4&0\\
s^1&T_I-\dfrac92T_1&0&0\\
s^0&4&&
\end{array}
\]

Alle Einträge der ersten Spalte sind positiv genau dann, wenn:

\[
\boxed{
T_I>\frac92T_1
}.
\]

Die handschriftlichen Seiten 107–108 erkennen das charakteristische Polynom, führen die vollständige Hurwitz- und Routh-Auswertung jedoch nicht zu Ende.

---

# 18. Grenzen der Stabilitätsgebiete

## Aufgabe 3a

\[
K_R=23
\]

führt zu:

\[
p=-8,\quad p=\pm j\sqrt3.
\]

## Aufgabe 3b

\[
T_N=
\frac{K_R}{1+3K_R}
\]

führt zu einer Nullzeile im Routh-Schema und einem imaginären Polpaar.

## Aufgabe 3c

\[
D=
\frac1{12\omega_0}
\]

führt ebenfalls zu einem imaginären Polpaar.

## Aufgabe 3d

\[
T_I=\frac92T_1
\]

führt zu einer Nullzeile. Aus der \(s^2\)-Zeile folgt das Hilfspolynom:

\[
\frac83T_1T_Is^2+4=0.
\]

Am Grenzwert \(T_I=\frac92T_1\):

\[
12T_1^2s^2+4=0.
\]

\[
s^2=-\frac1{3T_1^2}.
\]

\[
\boxed{
s=\pm\frac j{\sqrt3T_1}
}.
\]

Alle Gleichheitsgrenzen sind damit keine strikte Hurwitz-/E/A-Stabilität.

---

# 19. Qualitätsprüfung der Mitschrift

## Sicher lesbar und fachlich bestätigt

- Stabilitätsübersicht auf PDF-S. 100–101,
- Aufgabe 1a und 1b auf PDF-S. 101–102,
- Aufgabe 1c auf PDF-S. 102,
- Aufgabe 2a und 2c auf PDF-S. 104,
- Aufgabe 2h auf PDF-S. 105,
- Bildung der charakteristischen Polynome bei Aufgabe 3b und 3d auf PDF-S. 107–108.

## Nicht vollständig handschriftlich ausgeführt

- Aufgabe 2b sowie 2d–g,
- Hurwitz- und Routh-Schemata zu Aufgabe 3a–d,
- genaue Behandlung der Stabilitätsgrenzen.

Diese Rechenwege wurden vollständig aus den offiziellen Aufgabenstellungen und den Skriptdefinitionen hergeleitet.

---

# 20. Festgestellte Fehler und Widersprüche

1. **Aufgabe 1c:**  
   Der Zusatz

\[
k<\frac{5d^2}{16m}
\]

ist aus der Aufgabe nicht herleitbar. Stabilität verlangt nur \(d>0,k>0\).

2. **Aufgabe 2c, 2f und 2g:**  
   Die offizielle Bezeichnung „grenzstabil“ ist als interne Zustandsaussage brauchbar, aber nicht als E/A-Stabilität. Pole auf der imaginären Achse sind nicht BIBO-stabil.

3. **Aufgabe 3a:**  
   Offiziell \(\le23\), für asymptotische/E/A-Stabilität korrekt \(<23\).

4. **Aufgabe 3b:**  
   Offiziell \(\ge\), korrekt für Hurwitz-Stabilität \(>\).

5. **Aufgabe 3c:**  
   Offiziell \(\ge\), korrekt für Hurwitz-Stabilität \(>\).

6. **Skriptformulierung zur Jordanform:**  
   Die Forderung nach ausschließlich eindimensionalen Jordanblöcken ist für negative Eigenwerte mathematisch zu streng. Für strikt negative Realteile klingen auch Jordanterme ab.

---

# 21. Typische Fehler in Tutorium 09

1. Zustandsstabilität und E/A-Stabilität gleichsetzen.
2. Nullstellen statt Pole zur Stabilitätsentscheidung verwenden.
3. Einen Pol bei null als BIBO-stabil bezeichnen.
4. Bei komplexen Polen nur den Imaginärteil betrachten und den Realteil ignorieren.
5. Das charakteristische Polynom aus dem Zähler statt aus dem Nenner nehmen.
6. Beim geschlossenen Kreis den Term \(1+G_RG_S\) nicht auf gemeinsamen Nenner bringen.
7. Koeffizienten nicht in absteigender Potenzreihenfolge zuordnen.
8. Negative Leitkoeffizienten nicht zuerst normieren.
9. Positive Koeffizienten bereits als hinreichend ansehen.
10. Hurwitz-Determinanten mit nicht-strikten Ungleichungen prüfen.
11. Im Routh-Schema nicht nur die erste Spalte auswerten.
12. Gleichheitsfälle als asymptotisch stabil übernehmen.
13. Bei Parameterbedingungen die bereits gegebenen Voraussetzungen vergessen.
14. Pole auf der imaginären Achse nicht gesondert prüfen.
15. Pol-Nullstellen-Kürzungen ungeprüft akzeptieren.

---

# 22. Klausurstrategie

## 22.1 Zustandsraum

1. Charakteristisches Polynom:

\[
\det(\lambda I-A)=0.
\]

2. Dreiecks- und Blockstruktur zuerst ausnutzen.
3. Realteile sämtlicher Eigenwerte prüfen.
4. Bei \(\operatorname{Re}\lambda=0\) Jordanstruktur prüfen.
5. Ergebnis klar als asymptotisch, grenzstabil oder instabil benennen.

---

## 22.2 E/A-Stabilität

1. Übertragungsfunktion vollständig kürzen.
2. Nenner gleich null setzen.
3. Pole bestimmen.
4. Nur strikte linke Halbebene bedeutet E/A-stabil.
5. Pole auf der imaginären Achse ausdrücklich als nicht BIBO-stabil kennzeichnen.

---

## 22.3 Hurwitz

1. Geschlossene Führungsübertragungsfunktion bilden.
2. Charakteristisches Nennerpolynom sauber sortieren.
3. Leitkoeffizient positiv normieren.
4. Alle Koeffizienten strikt positiv prüfen.
5. Hurwitz-Matrix aufstellen.
6. Hauptdeterminanten strikt positiv prüfen.
7. Alle Bedingungen schneiden.
8. Gleichheitsgrenzen separat als Grenzfälle analysieren.

---

## 22.4 Routh

1. Erste zwei Zeilen mit geraden und ungeraden Potenzen füllen.
2. Jede weitere Zeile aus den zwei vorherigen bilden.
3. Nur erste Spalte für Stabilitätsbedingung auswerten.
4. Vorzeichenwechsel zählen.
5. Nullzeile als Hinweis auf imaginäre bzw. symmetrische Pole behandeln.
6. Ergebnis mit Hurwitz vergleichen.

---

# 23. NotebookLM-Verifikation

--- NOTEBOOKLM-PROMPT ---

Prüfe ausschließlich anhand der hochgeladenen offiziellen Regelungstechnik-Unterlagen die folgenden Widersprüche aus „Tutorium 09 – Stabilität I“:

1. Aufgabe 1c:
Woher stammt der Zusatz
\[
k<\frac{5d^2}{16m}?
\]
Ist er aus weiteren Randbedingungen herleitbar, oder ist für asymptotische Stabilität des Feder-Masse-Dämpfer-Systems nur
\[
d>0,\quad k>0
\]
erforderlich? Vergleiche zusätzlich mit der Grenze für reelle/komplexe Pole.

2. Aufgabe 2c:
Die Aufgabe steht unter „E/A-Stabilität“, die Musterlösung bezeichnet Pole
\[
\pm3j
\]
als „grenzstabil“. Unterscheide anhand des Skripts Zustandsstabilität und E/A-Stabilität. Ist das System BIBO-stabil?

3. Aufgabe 3a:
Die Musterlösung nennt
\[
0<K_R\le23.
\]
Prüfe die Pole bei \(K_R=23\) und entscheide, ob der Kreis dort asymptotisch bzw. E/A-stabil oder nur grenzstabil ist.

4. Aufgabe 3b und 3c:
Prüfe, ob die offiziellen Bedingungen mit \(\ge\) oder für strikte Hurwitz-Stabilität mit \(>\) gelten müssen.

Belege jede direkte Quellenaussage mit Dokumentname und genauer Seite. Trenne Quellenaussage und eigene mathematische Herleitung.

--- ENDE ---

---

# 24. Kompaktformelsammlung Tutorium 09

## Zustandsstabilität

\[
\operatorname{Re}\lambda_i<0
\Rightarrow
\text{asymptotisch stabil}.
\]

## E/A-Stabilität

\[
\operatorname{Re}p_i<0
\quad
\text{für alle Pole}.
\]

## Polynom zweiter Ordnung

\[
a_2s^2+a_1s+a_0.
\]

Bei \(a_2>0\):

\[
a_1>0,\qquad a_0>0.
\]

## Polynom dritter Ordnung

\[
a_3s^3+a_2s^2+a_1s+a_0.
\]

\[
a_i>0,
\qquad
a_2a_1>a_3a_0.
\]

## Hurwitz-Matrix

\[
H=
\begin{bmatrix}
a_1&a_3&a_5&\cdots\\
a_0&a_2&a_4&\cdots\\
0&a_1&a_3&\cdots\\
0&a_0&a_2&\cdots\\
\vdots&\vdots&\vdots&\ddots
\end{bmatrix}.
\]

## Routh-Stabilität

\[
\boxed{
\text{Alle Einträge der ersten Spalte besitzen dasselbe positive Vorzeichen.}
}
\]

## Anzahl instabiler Pole

\[
\boxed{
\text{Anzahl der Vorzeichenwechsel in der ersten Routh-Spalte.}
}
\]

---

# Tutorium 11 – Stabilität II und Reglerentwurf I

## 1. Quellen und Seitenbereich

### Primärquellen

1. **RT-Tutorien-Mitschrift.pdf**, PDF-Seiten 123–150
   - S. 123–125: Aufgaben 1 und 2; Nyquist-Ortskurven mit Frequenzmarkierungen
   - S. 126: Foto der überlagerten Ortskurven
   - S. 127–128: Bode-Diagramm und Aufgabenstellung zum phasenanhebenden Korrekturglied
   - S. 129–130: Aufgaben 3a–d zu Ziegler–Nichols
   - S. 131–133: Aufgaben 4a–b zu Cohen–Coon und Tabellen
   - S. 134: allgemeines Wendetangentenverfahren und vollständige Rechnung zu Aufgabe 3a
   - S. 135: Tafelbild zur PT1Tt-Auswertung
   - S. 136–137: vollständige Rechnung zu Aufgabe 3b
   - S. 138: leer
   - S. 139–141: weiterführende Diagramme und Herleitung des Lead-Gliedes
   - S. 142–144: Nyquist-Theorie und Rechnung zu Aufgabe 1a und 1d
   - S. 145–147: vollständige Auslegung des Korrekturgliedes
   - S. 148–149: Tafelbilder zu kompensierten Bode-Diagrammen
   - S. 150: leer
   - Tutorium 12 beginnt auf PDF-Seite 151.

2. **Regelungstechnik_Tutorium_komplett.pdf**, PDF-Seiten 60–83  
   Tutorium 11, Blattseiten 1/23–23/23, offizielle Aufgaben, Lösungen und Herleitungen.

3. **skript.pdf**
   - gedruckte S. 116–121: Nyquist-Kriterium
   - gedruckte S. 128–131: Reglerstruktur und Korrekturglieder
   - gedruckte S. 132–137: Ziegler–Nichols
   - gedruckte S. 137–138: Cohen–Coon

---

# 2. Theoriefragen

## 2.1 Welche Rolle spielt die offene Kette beim Nyquist-Kriterium?

Die offene Kreisübertragungsfunktion lautet allgemein

\[
\boxed{
G_0(s)=G_R(s)G_S(s)G_M(s)
}.
\]

Bei Einheitsrückführung gilt \(G_M=1\).

Die Polstellen des geschlossenen Kreises werden durch die Rückführdifferenzfunktion

\[
\boxed{
F(s)=1+G_0(s)
}
\]

bestimmt. Das Nyquist-Kriterium beurteilt daher die Stabilität des geschlossenen Kreises allein aus

1. den instabilen Polen der offenen Kette und
2. den Umschlingungen des kritischen Punkts

\[
\boxed{-1+j0}
\]

durch die Nyquist-Ortskurve der offenen Kette.

Kernaussage:

\[
\boxed{
\text{Nyquist bestimmt die Stabilität des geschlossenen Kreises aus dem offenen Kreis.}
}
\]

Nach der Vorzeichenkonvention des Skripts muss die vollständige Nyquistkurve den Punkt \(-1\) in einer durch die Anzahl \(n_+\) der offenen RHP-Pole festgelegten Richtung und Anzahl umschließen. Ist der offene Kreis bereits stabil, darf \(-1\) nicht umschlossen werden.

Quelle: `skript.pdf`, gedruckte S. 116–121, Theoreme 5.33–5.35.

---

## 2.2 Warum verbessert ein I-Anteil die stationäre Genauigkeit, kann aber die Stabilität verschlechtern?

Ein I-Anteil besitzt

\[
G_I(s)=\frac{K_I}{s}.
\]

### Vorteil bei kleinen Frequenzen

Für

\[
s\to0
\]

wird die Kreisverstärkung sehr groß:

\[
|G_I(s)|\to\infty.
\]

Bei einem stabilen geschlossenen Kreis folgt für eine Sprungführung:

\[
e_\infty
=
\lim_{s\to0}
\frac{1}{1+G_0(s)}
=
0.
\]

Der I-Anteil eliminiert damit die bleibende Regelabweichung.

### Nachteil für die Stabilität

Der Integrator

- fügt einen Pol im Ursprung hinzu,
- liefert über den gesamten Frequenzbereich eine Phase von \(-90^\circ\),
- senkt typischerweise die Phasenreserve,
- erhöht die Systemordnung,
- kann Überschwingen und Schwingneigung verstärken.

Klausurtauglich:

\[
\boxed{
\text{I-Anteil: hohe Niederfrequenzverstärkung verbessert Genauigkeit, }-90^\circ
\text{ Phase verschlechtert Stabilitätsreserve.}
}
\]

---

## 2.3 Warum nutzt man Korrekturglieder statt idealer I- oder D-Anteile?

### Ideales D-Glied

\[
G_D(s)=K_Ds.
\]

Sein Betrag wächst für hohe Frequenzen unbegrenzt:

\[
|G_D(j\omega)|=K_D\omega.
\]

Dadurch werden Messrauschen und nicht modellierte Hochfrequenzdynamiken stark verstärkt.

### Ideales I-Glied

\[
G_I(s)=\frac{K_I}{s}.
\]

Sein Betrag wird für kleine Frequenzen unbegrenzt groß. Das kann langsames Verhalten, Sättigung und Integrator-Windup begünstigen.

### Phasenanhebendes Korrekturglied

\[
\boxed{
G_K(s)=\frac{T_Ds+1}{T_Ss+1},
\qquad
T_S<T_D
}
\]

wirkt nur in einem begrenzten Frequenzbereich differenzierend. Seine Hochfrequenzverstärkung bleibt endlich:

\[
\lim_{\omega\to\infty}|G_K(j\omega)|
=
\frac{T_D}{T_S}.
\]

### Phasenabsenkendes Korrekturglied

Bei

\[
T_S>T_D
\]

wirkt das Glied in einem begrenzten Bereich integrierend, ohne bei \(\omega\to0\) unendlich große Verstärkung zu besitzen.

Kernaussage:

\[
\boxed{
\text{Korrekturglieder formen Betrag und Phase gezielt in einem Frequenzband und begrenzen Extremverstärkungen.}
}
\]

Quelle: `skript.pdf`, gedruckte S. 128–131, Definition 6.5.

---

## 2.4 Experimenteller Erstentwurf eines PID-Reglers

### Offener Versuch: Wendetangentenverfahren

Nur verwenden, wenn die Strecke gefahrlos offen betrieben werden kann.

1. Strecke in einen stationären Anfangszustand bringen.
2. Definierten Einheitssprung aufschalten.
3. Ausgang \(y(t)\) messen.
4. Wendetangente im Punkt maximaler Steigung einzeichnen.
5. Bestimmen:
   - statische Verstärkung \(K_S\),
   - Totzeit \(K_T\),
   - Zeitkonstante \(T\).
6. PT1Tt-Modell bilden:

\[
G_S(s)
\approx
\frac{K_S}{Ts+1}e^{-K_Ts}.
\]

7. Parameter mit Ziegler–Nichols oder Cohen–Coon berechnen.
8. Regler vorsichtig erproben und nach Gütekriterien nachstellen.

### Geschlossener Versuch: kritische Verstärkung

Nur verwenden, wenn eine Dauerschwingung gefahrlos erzeugt werden kann.

1. Nur P-Anteil aktivieren.
2. \(K_P\) schrittweise erhöhen.
3. Bei gerade dauerhafter Schwingung ablesen:
   - \(K_{\mathrm{krit}}\),
   - \(T_{\mathrm{krit}}\).
4. Ziegler–Nichols-Tabelle für den geschlossenen Entwurf anwenden.
5. Parameter danach konservativ validieren.

---

# 3. Nyquist-Kriterium – Rechenschema

## Schritt 1: Offene Kette bilden

Bei Reihenschaltung:

\[
\boxed{
G_0(s)=G_R(s)G_S(s)
}.
\]

## Schritt 2: Offene RHP-Pole bestimmen

Nenner von \(G_0(s)\) faktorisieren und Zahl \(P\) der Pole mit

\[
\operatorname{Re}(p)>0
\]

bestimmen. Pole auf der imaginären Achse benötigen eine besondere Nyquist-Kontur.

## Schritt 3: Frequenzgang

\[
s=j\omega.
\]

Dann:

\[
G_0(j\omega)
=
\operatorname{Re}G_0(j\omega)
+
j\operatorname{Im}G_0(j\omega).
\]

## Schritt 4: Ortskurve

- positive und negative Frequenzen berücksichtigen,
- Richtung mit wachsendem \(\omega\) markieren,
- Verhalten bei \(\omega=0\) und \(|\omega|\to\infty\) prüfen,
- kritischen Punkt \(-1\) markieren.

## Schritt 5: Umschlingungen auswerten

Mit der im Skript verwendeten Nyquist-Konvention muss die Anzahl der Umschlingungen zu den offenen RHP-Polen passen. Stabil ist der geschlossene Kreis nur, wenn keine geschlossenen RHP-Pole verbleiben.

## Schritt 6: Gegenprobe

Charakteristisches Polynom des geschlossenen Kreises:

\[
1+G_0(s)=0.
\]

Hurwitz, Routh oder direkte Polberechnung liefern eine unabhängige Kontrolle.

---

# 4. Aufgabe 1a – offene Kette aus PT1-Strecke und D-Regler

## Gegeben

\[
G_S(s)=\frac{K_1}{1+sT_1},
\]

\[
G_R(s)=sK_R.
\]

Da beide Glieder in Reihe liegen:

\[
G_0(s)=G_R(s)G_S(s).
\]

Einsetzen:

\[
\boxed{
G_0(s)
=
\frac{K_1K_Rs}{1+sT_1}
}.
\]

Die handschriftliche Rechnung auf PDF-S. 142 ist korrekt.

### Hochfrequenzverhalten

\[
\lim_{\omega\to\infty}
G_0(j\omega)
=
\frac{K_1K_R}{T_1}.
\]

Der ideale D-Anteil wird durch den PT1-Pol begrenzt; die offene Kette ist ein DT1-Glied.

---

# 5. Aufgabe 1b – zusammengesetzte Strecke und PD-Regler

## Gegeben

\[
G_S(s)
=
K_1\frac{K_2}{1+sT_2}
+
\frac{K_3}{(s-T_3)s},
\]

\[
G_R(s)
=
K_D(1+sT_V).
\]

## 5.1 Saubere faktorierte Form

\[
G_0(s)
=
K_D(1+sT_V)
\left[
\frac{K_1K_2}{1+sT_2}
+
\frac{K_3}{s(s-T_3)}
\right].
\]

Auf gemeinsamen Nenner bringen:

\[
\boxed{
G_0(s)
=
K_D(1+sT_V)
\frac{
K_1K_2s(s-T_3)+K_3(1+sT_2)
}{
(1+sT_2)s(s-T_3)
}
}.
\]

Diese Form ist übersichtlicher und weniger fehleranfällig als die vollständig ausmultiplizierte Form.

## 5.2 Ausmultiplizierter Zähler

Der Klammerterm ist

\[
K_1K_2s^2
+
(-K_1K_2T_3+K_3T_2)s
+
K_3.
\]

Multiplikation mit \(K_D(1+sT_V)\) ergibt:

\[
\boxed{
\begin{aligned}
Z(s)=K_D\big[
& T_VK_1K_2s^3\\
& +(K_1K_2-T_VK_1K_2T_3+T_VK_3T_2)s^2\\
& +(-K_1K_2T_3+K_3T_2+T_VK_3)s\\
& +K_3
\big].
\end{aligned}
}
\]

Nenner:

\[
\boxed{
N(s)=(1+sT_2)s(s-T_3)
}.
\]

---

# 6. Aufgabe 1c – Real- und Imaginärteil

## Gegeben

\[
G_0(s)
=
\frac{25s+60}
{10s^3+10s^2+25s}.
\]

## 6.1 Einsetzen von \(s=j\omega\)

Zähler:

\[
25j\omega+60.
\]

Nenner:

\[
10(j\omega)^3+10(j\omega)^2+25j\omega.
\]

Mit

\[
(j\omega)^2=-\omega^2,
\qquad
(j\omega)^3=-j\omega^3
\]

folgt:

\[
N(j\omega)
=
-10\omega^2
+
j(25\omega-10\omega^3).
\]

---

## 6.2 Rationalisieren

Mit dem konjugierten Nenner erhält man:

\[
G_0(j\omega)
=
\frac{
(60+j25\omega)
\left[
-10\omega^2-j(25\omega-10\omega^3)
\right]
}{
100\omega^4+(25\omega-10\omega^3)^2
}.
\]

Damit:

\[
\boxed{
\operatorname{Re}G_0(j\omega)
=
\frac{
25\omega^2-250\omega^4
}{
100\omega^4+(25\omega-10\omega^3)^2
}
}
\]

und

\[
\boxed{
\operatorname{Im}G_0(j\omega)
=
\frac{
350\omega^3-1500\omega
}{
100\omega^4+(25\omega-10\omega^3)^2
}
}.
\]

Für \(\omega\neq0\) kann der gemeinsame Faktor \(\omega^2\) gekürzt werden. Bei \(\omega=0\) ist die ursprüngliche Funktion wegen des Pols im Ursprung nicht definiert.

---

## 6.3 Kontrollwerte

\[
\begin{array}{c|cc}
\omega&\operatorname{Re}G_0&\operatorname{Im}G_0\\
\hline
2&-1.56&-0.08\\
2.5&-0.757&0.135\\
3&-0.434&0.107\\
4&-0.201&0.052
\end{array}
\]

Diese Werte stimmen mit der offiziellen Tabelle überein.

---

# 7. Aufgabe 1d – Real- und Imaginärteil

## Gegeben

\[
G_0(s)
=
\frac{3}{(s+1)(s-2)}.
\]

## 7.1 Einsetzen

\[
G_0(j\omega)
=
\frac{3}
{(j\omega+1)(j\omega-2)}.
\]

Nenner:

\[
(j\omega+1)(j\omega-2)
=
-(\omega^2+2)-j\omega.
\]

Rationalisieren:

\[
G_0(j\omega)
=
3
\frac{
-(\omega^2+2)+j\omega
}{
(\omega^2+2)^2+\omega^2
}.
\]

Damit:

\[
\boxed{
\operatorname{Re}G_0(j\omega)
=
-\frac{
3(\omega^2+2)
}{
(\omega^2+2)^2+\omega^2
}
}
\]

\[
\boxed{
\operatorname{Im}G_0(j\omega)
=
\frac{
3\omega
}{
(\omega^2+2)^2+\omega^2
}
}.
\]

Die handschriftliche Herleitung auf PDF-S. 143 ist korrekt.

---

## 7.2 Kontrollwerte

\[
\begin{array}{c|cc}
\omega&\operatorname{Re}G_0&\operatorname{Im}G_0\\
\hline
0&-1.5&0\\
1&-0.9&0.3\\
2&-0.45&0.15\\
-1&-0.9&-0.3\\
-2&-0.45&-0.15
\end{array}
\]

### [KORRIGIERT]

In der per Textextraktion erfassten offiziellen Tabelle erscheint bei \(\omega=-1\) teilweise ein positives Vorzeichen. Aus der Formel und der gezeichneten Ortskurve folgt eindeutig:

\[
\operatorname{Im}G_0(-1)=-0.3.
\]

---

# 8. Aufgabe 1e – Stabilität des Systems c)

## 8.1 Offene Pole

Nenner:

\[
10s^3+10s^2+25s
=
5s(2s^2+2s+5).
\]

Pole:

\[
p_1=0,
\]

\[
p_{2,3}
=
-\frac12\pm\frac32j.
\]

Der offene Kreis besitzt einen Pol auf der imaginären Achse und keinen Pol in der offenen rechten Halbebene.

---

## 8.2 Offizielle Nyquist-Auswertung

Die offizielle Lösung bewertet den geschlossenen Kreis als

\[
\boxed{\text{instabil}}.
\]

Die gezeichnete Ortskurve passiert den kritischen Bereich so, dass das vereinfachte Nyquistkriterium nicht erfüllt ist.

---

## 8.3 Algebraische Gegenprobe

Geschlossene charakteristische Gleichung:

\[
1+G_0(s)=0.
\]

\[
10s^3+10s^2+25s+25s+60=0.
\]

\[
\boxed{
10s^3+10s^2+50s+60=0
}.
\]

Normiert:

\[
s^3+s^2+5s+6.
\]

Routh-Schema:

\[
\begin{array}{c|cc}
s^3&1&5\\
s^2&1&6\\
s^1&-1&0\\
s^0&6&
\end{array}
\]

Die erste Spalte besitzt zwei Vorzeichenwechsel. Somit liegen zwei geschlossene Pole in der rechten Halbebene:

\[
\boxed{\text{instabil}}.
\]

---

# 9. Aufgabe 1f – Stabilität des Systems d)

## 9.1 Offene Pole

\[
G_0(s)=\frac3{(s+1)(s-2)}.
\]

Pole:

\[
p_1=-1,
\qquad
p_2=2.
\]

Damit besitzt der offene Kreis einen RHP-Pol:

\[
P=1.
\]

Das vollständige Nyquist-Kriterium muss verwendet werden.

---

## 9.2 Offizielle Bewertung

Die offizielle Lösung lautet:

\[
\boxed{\text{instabil}}.
\]

Die Umschlingung des Punkts \(-1\) kompensiert den offenen RHP-Pol nicht in der für Stabilität notwendigen Weise.

---

## 9.3 Algebraische Gegenprobe

\[
1+G_0(s)=0.
\]

\[
(s+1)(s-2)+3=0.
\]

\[
s^2-s-2+3=0.
\]

\[
\boxed{
s^2-s+1=0
}.
\]

Pole:

\[
s_{1,2}
=
\frac12
\pm
j\frac{\sqrt3}{2}.
\]

Beide besitzen:

\[
\operatorname{Re}s_{1,2}=\frac12>0.
\]

Damit:

\[
\boxed{\text{instabil}}.
\]

---

# 10. Aufgabe 1g – Amplituden- und Phasenreserve für System c)

## 10.1 Phasendurchtritt

Der Imaginärteil verschwindet für \(\omega>0\), wenn

\[
350\omega^3-1500\omega=0.
\]

\[
50\omega(7\omega^2-30)=0.
\]

Damit:

\[
\boxed{
\omega_\pi
=
\sqrt{\frac{30}{7}}
\approx2.0702\,\mathrm{s^{-1}}
}.
\]

An dieser Frequenz:

\[
G_0(j\omega_\pi)=-1.4.
\]

Betrag:

\[
|G_0|=1.4.
\]

Lineare Amplitudenreserve:

\[
\boxed{
A_R
=
\frac1{1.4}
=
0.7143
}.
\]

In dB:

\[
\boxed{
\Delta A
=
20\log_{10}(0.7143)
\approx-2.92\,\mathrm{dB}
}.
\]

Eine negative dB-Reserve bedeutet, dass der kritische Betrag bereits überschritten ist.

---

## 10.2 Gain-Durchtritt

Aus

\[
|G_0(j\omega_d)|=1
\]

folgt numerisch:

\[
\boxed{
\omega_d
\approx2.2995\,\mathrm{s^{-1}}
}.
\]

Die kontinuierlich abgewickelte Phase beträgt dort:

\[
\varphi(\omega_d)
\approx-186.71^\circ.
\]

Damit:

\[
\boxed{
\Delta\varphi
=
180^\circ+\varphi(\omega_d)
\approx-6.71^\circ
}.
\]

Die offizielle grafische Lösung rundet auf ungefähr:

\[
\omega_d\approx2.3,
\qquad
\Delta\varphi\approx-7.6^\circ.
\]

Beide Reserven bestätigen die Instabilitätsnähe bzw. Instabilität.

---

# 11. Phasenanhebendes Korrekturglied

## 11.1 Definition

\[
\boxed{
G_K(s)
=
\frac{T_Ds+1}{T_Ss+1},
\qquad
T_S<T_D
}.
\]

Definiere:

\[
\boxed{
\alpha
=
\frac{T_S}{T_D}
},
\qquad
0<\alpha<1.
\]

Dann:

\[
G_K(s)
=
\frac{T_Ds+1}{\alpha T_Ds+1}.
\]

---

## 11.2 Phase

\[
\varphi_K(\omega)
=
\arctan(\omega T_D)
-
\arctan(\omega T_S).
\]

Die maximale Phasenanhebung liegt bei:

\[
\boxed{
\omega_{\max}
=
\frac1{\sqrt{T_DT_S}}
=
\frac1{T_D\sqrt\alpha}
}.
\]

---

## 11.3 Maximale Phasenanhebung

\[
\boxed{
\sin(\Delta\varphi_{\max})
=
\frac{T_D-T_S}{T_D+T_S}
=
\frac{1-\alpha}{1+\alpha}
}.
\]

Nach \(\alpha\) aufgelöst:

\[
\boxed{
\alpha
=
\frac{
1-\sin(\Delta\varphi_{\max})
}{
1+\sin(\Delta\varphi_{\max})
}
}.
\]

---

## 11.4 Betrag bei maximaler Phasenanhebung

\[
\boxed{
|G_K(j\omega_{\max})|
=
\frac1{\sqrt\alpha}
}.
\]

In dB:

\[
\boxed{
20\log_{10}|G_K(j\omega_{\max})|
=
-10\log_{10}\alpha
}.
\]

Damit der kompensierte Kreis bei \(\omega_{\max}\) gerade \(0\,\mathrm{dB}\) besitzt, muss der unkompensierte Kreis dort erfüllen:

\[
\boxed{
20\log_{10}|G_0(j\omega_{\max})|
=
10\log_{10}\alpha
}.
\]

Quelle: offizielle Herleitung auf Tutorium-11-Blattseiten 22/23–23/23; Mitschrift-PDF-S. 139–141.

---

# 12. Aufgabe 2a – vollständiger Regelkreis mit Korrekturglied

## Strecke und P-Regler

\[
G_S(s)
=
\frac{1.5s+3}
{\frac34s^3+4s^2+2s+0.5},
\]

\[
K_P=54.42.
\]

Unkompensierte offene Kette:

\[
\boxed{
G_0(s)=54.42\,G_S(s)
}.
\]

Korrekturglied:

\[
G_K(s)
=
\frac{T_Ds+1}{T_Ss+1}.
\]

Kompensierte offene Kette:

\[
\boxed{
G_0^\ast(s)
=
G_K(s)K_PG_S(s)
}.
\]

Ausgeschrieben:

\[
\boxed{
G_0^\ast(s)
=
\frac{T_Ds+1}{T_Ss+1}
\cdot
54.42
\cdot
\frac{1.5s+3}
{\frac34s^3+4s^2+2s+0.5}
}.
\]

Bei negativer Einheitsrückführung:

\[
\boxed{
G_W^\ast(s)
=
\frac{G_0^\ast(s)}
{1+G_0^\ast(s)}
}.
\]

Sichere faktorierte Form:

\[
\boxed{
G_W^\ast(s)
=
\frac{
54.42(T_Ds+1)(1.5s+3)
}{
(T_Ss+1)
\left(
\frac34s^3+4s^2+2s+0.5
\right)
+
54.42(T_Ds+1)(1.5s+3)
}
}.
\]

Die Mitschrift auf PDF-S. 145 zeigt diesen Aufbau korrekt.

---

# 13. Aufgabe 2b – unkompensierte Phasenreserve

Aus dem Bode-Diagramm:

\[
\omega_c\approx10\,\mathrm{s^{-1}}.
\]

Gemessene Phase:

\[
\angle G_0(j\omega_c)
=
-162.59^\circ.
\]

Damit:

\[
\boxed{
\varphi_R
=
180^\circ-162.59^\circ
=
17.41^\circ
}.
\]

Gefordert:

\[
\varphi_{R,\mathrm{soll}}=60^\circ.
\]

Benötigte reine Anhebung:

\[
60^\circ-17.41^\circ
=
42.59^\circ.
\]

Da die neue Durchtrittsfrequenz nach rechts wandert und die Streckenphase dort negativer wird, wird ein Sicherheitszuschlag verwendet:

\[
\boxed{
\Delta\varphi_{\max}=50^\circ
}.
\]

---

# 14. Aufgabe 2c – neue Entwurfsfrequenz

## 14.1 Verhältnis \(\alpha\)

\[
\alpha
=
\frac{1-\sin50^\circ}{1+\sin50^\circ}.
\]

\[
\boxed{
\alpha
\approx0.1325
}.
\]

## 14.2 Benötigtes unkompensiertes Betragsniveau

\[
10\log_{10}\alpha
\approx-8.78\,\mathrm{dB}.
\]

Im unkompensierten Amplitudengang wird die Frequenz gesucht, bei der:

\[
|G_0|_{\mathrm{dB}}
\approx-8.78\,\mathrm{dB}.
\]

Aus dem Diagramm:

\[
\boxed{
\omega_{\max}
\approx17.02\,\mathrm{s^{-1}}
}.
\]

Diese wird als neue Durchtrittsfrequenz angesetzt:

\[
\boxed{
\omega_c^\ast
\approx17.02\,\mathrm{s^{-1}}
}.
\]

---

# 15. Aufgabe 2d – Zeitkonstanten des Korrekturgliedes

\[
T_D
=
\frac1{
\omega_{\max}\sqrt\alpha
}.
\]

Einsetzen:

\[
T_D
=
\frac1{
17.02\sqrt{0.1325}
}.
\]

\[
\boxed{
T_D\approx0.1614\,\mathrm{s}
}.
\]

Mit:

\[
T_S=\alpha T_D
\]

folgt:

\[
T_S
=
0.1325\cdot0.1614.
\]

\[
\boxed{
T_S\approx0.0214\,\mathrm{s}
}.
\]

Korrekturglied:

\[
\boxed{
G_K(s)
=
\frac{0.1614s+1}
{0.0214s+1}
}.
\]

Kontrolle aus der offiziellen Lösung:

\[
\boxed{
\omega_c^\ast\approx17.02\,\mathrm{s^{-1}}
}
\]

\[
\boxed{
\varphi_R^\ast\approx60.85^\circ
}.
\]

Die Zielreserve wird erreicht.

---

# 16. Wirkung des Korrekturgliedes

Verglichen werden:

1. Strecke ohne Regler,
2. geschlossener Kreis mit P-Regler,
3. geschlossener Kreis mit P-Regler und Lead-Glied.

### P-Regler allein

\[
\omega_c\approx10,
\qquad
\varphi_R\approx17.41^\circ.
\]

Erwartung:

- starkes Überschwingen,
- schwache Dämpfung,
- geringe Robustheit.

### P-Regler mit Lead-Glied

\[
\omega_c^\ast\approx17.02,
\qquad
\varphi_R^\ast\approx60.85^\circ.
\]

Erwartung:

- größere Bandbreite,
- deutlich bessere Dämpfung,
- weniger Überschwingen,
- stabileres Einschwingen.

Die Hochfrequenzverstärkung des Lead-Gliedes bleibt endlich:

\[
\frac{T_D}{T_S}
=
\frac1\alpha
\approx7.55.
\]

---

# 17. Übungsaufgaben zum Lead-Entwurf

## Übungsaufgabe 1

Offizielle mögliche Lösung:

\[
\boxed{
G_K(s)
=
\frac{0.1845s+1}
{0.0366s+1}
}.
\]

## Übungsaufgabe 2

Offizielle mögliche Lösung:

\[
\boxed{
G_K(s)
=
\frac{0.1269s+1}
{0.0276s+1}
}.
\]

Die Unterlagen liefern hier nur die Endwerte. Das Rechenschema ist identisch zu Aufgabe 2b–d.

---

# 18. Ziegler–Nichols im offenen Kreis

## 18.1 PT1Tt-Approximation

\[
\boxed{
G_S(s)
\approx
\frac{K_S}{Ts+1}e^{-K_Ts}
}.
\]

Für einen Einheitssprung:

- \(K_S\): stationärer Endwert,
- \(K_T\): Totzeit,
- \(T\): Zeit zwischen Totzeitpunkt und dem Erreichen von \(0.63K_S\).

Es gilt:

\[
y(K_T+T)\approx0.63K_S.
\]

### Gültigkeitshinweis des Skripts

Ziegler–Nichols im offenen Kreis setzt ungefähr voraus:

\[
\boxed{
K_T<0.5T
}.
\]

---

## 18.2 Einstellregeln

### P-Regler

\[
K_P
=
\frac1{K_S}\frac{T}{K_T}.
\]

### PI-Regler

\[
K_P
=
\frac{0.9}{K_S}\frac{T}{K_T},
\]

\[
K_I
=
\frac{K_P}{3.33K_T}.
\]

### PID-Regler

\[
\boxed{
K_P
=
\frac{1.2}{K_S}\frac{T}{K_T}
}
\]

\[
\boxed{
K_I
=
\frac{K_P}{2K_T}
}
\]

\[
\boxed{
K_D
=
0.5K_PK_T
}.
\]

Reglerdarstellung:

\[
\boxed{
G_R(s)
=
K_P+\frac{K_I}{s}+K_Ds
}.
\]

Quelle: `skript.pdf`, gedruckte S. 133–134, Tabelle 6.1.

---

# 19. Aufgabe 3a – Ziegler–Nichols aus der Sprungantwort

Aus dem Diagramm:

\[
\boxed{K_S=2}
\]

\[
\boxed{K_T=0.5\,\mathrm{s}}
\]

und:

\[
0.63K_S=1.26
\]

wird bei ungefähr

\[
t=5.5\,\mathrm{s}
\]

erreicht.

Damit:

\[
K_T+T=5.5.
\]

\[
\boxed{
T=5.0\,\mathrm{s}
}.
\]

---

## 19.1 PID-Parameter

\[
K_P
=
\frac{1.2}{2}
\frac5{0.5}.
\]

\[
\boxed{
K_P=6.0
}.
\]

\[
K_I
=
\frac6{2\cdot0.5}.
\]

\[
\boxed{
K_I=6.0
}.
\]

\[
K_D
=
0.5\cdot6\cdot0.5.
\]

\[
\boxed{
K_D=1.5
}.
\]

Ergebnis:

\[
\boxed{
G_R(s)
=
6+\frac6s+1.5s
}.
\]

Die Mitschrift auf PDF-S. 134 ist vollständig und korrekt.

---

# 20. Ziegler–Nichols im geschlossenen Kreis

## 20.1 Versuch

1. P-Regler verwenden.
2. \(K_P\) erhöhen.
3. Bei gerade dauerhafter Schwingung:

\[
K_P=K_{\mathrm{krit}}.
\]

4. Periodendauer messen:

\[
T_{\mathrm{krit}}
=
t_{\max,2}-t_{\max,1}.
\]

### Sicherheitsproblem

Das Verfahren bringt den Kreis gezielt an die Stabilitätsgrenze. Es darf nur bei Anlagen verwendet werden, die diesen Versuch gefahrlos verkraften.

---

## 20.2 Einstellregeln

### P-Regler

\[
K_P=0.5K_{\mathrm{krit}}.
\]

### PI-Regler

\[
K_P=0.45K_{\mathrm{krit}},
\]

\[
K_I
=
\frac{K_P}{0.85T_{\mathrm{krit}}}.
\]

### PID-Regler

\[
\boxed{
K_P=0.6K_{\mathrm{krit}}
}
\]

\[
\boxed{
K_I
=
\frac{K_P}{0.5T_{\mathrm{krit}}}
}
\]

\[
\boxed{
K_D
=
0.12K_PT_{\mathrm{krit}}
}.
\]

Quelle: `skript.pdf`, gedruckte S. 136–137, Tabelle 6.2.

---

# 21. Aufgabe 3b – PID aus kritischer Schwingung

Aus der Aufgabenstellung:

\[
\boxed{
K_{\mathrm{krit}}=1.62
}.
\]

Aus zwei aufeinanderfolgenden Maxima:

\[
t_1\approx0.75\,\mathrm{s},
\]

\[
t_2\approx3.75\,\mathrm{s}.
\]

Damit:

\[
\boxed{
T_{\mathrm{krit}}
=
3.0\,\mathrm{s}
}.
\]

---

## 21.1 PID-Parameter

\[
K_P=0.6\cdot1.62.
\]

\[
\boxed{
K_P=0.972
}.
\]

\[
K_I
=
\frac{0.972}{0.5\cdot3}.
\]

\[
\boxed{
K_I=0.648
}.
\]

\[
K_D
=
0.12\cdot0.972\cdot3.
\]

\[
\boxed{
K_D\approx0.350
}.
\]

Regler:

\[
\boxed{
G_R(s)
=
0.972
+
\frac{0.648}{s}
+
0.350s
}.
\]

Die Mitschrift auf PDF-S. 136–137 ist korrekt.

---

# 22. Aufgabe 3c – PI-Regler aus offener Sprungantwort

Aus dem Diagramm werden näherungsweise abgelesen:

\[
\boxed{
K_S\approx3.5
}
\]

\[
\boxed{
K_T\approx1.5\,\mathrm{s}
}
\]

\[
\boxed{
T\approx6.0\,\mathrm{s}
}.
\]

Kontrolle:

\[
K_T+T\approx7.5\,\mathrm{s},
\]

an dieser Stelle liegt die Antwort bei ungefähr

\[
0.63K_S\approx2.205.
\]

---

## 22.1 PI-Parameter

\[
K_P
=
\frac{0.9}{3.5}
\frac6{1.5}.
\]

\[
\boxed{
K_P\approx1.029
}.
\]

\[
K_I
=
\frac{1.029}{3.33\cdot1.5}.
\]

\[
\boxed{
K_I\approx0.206
}.
\]

\[
K_D=0.
\]

Regler:

\[
\boxed{
G_R(s)
=
1.029+\frac{0.206}{s}
}.
\]

Diese Werte entsprechen der offiziellen Lösung. Die Rohwerte \(K_S,K_T,T\) sind aus dem Diagramm rekonstruiert.

---

# 23. Aufgabe 3d – PID aus Dauerschwingung

Aus dem Diagramm:

\[
\boxed{
K_{\mathrm{krit}}\approx2.0
}
\]

\[
\boxed{
T_{\mathrm{krit}}\approx1.5\,\mathrm{s}
}.
\]

Damit:

\[
K_P
=
0.6\cdot2
=
1.2.
\]

\[
K_I
=
\frac{1.2}{0.5\cdot1.5}
=
1.6.
\]

\[
K_D
=
0.12\cdot1.2\cdot1.5
=
0.216.
\]

Ergebnis:

\[
\boxed{
G_R(s)
=
1.2+\frac{1.6}{s}+0.216s
}.
\]

---

# 24. Cohen–Coon-Methode

## 24.1 Voraussetzungen

Auch Cohen–Coon verwendet die Approximation:

\[
G_S(s)
\approx
\frac{K_S}{Ts+1}e^{-K_Ts}.
\]

Im Unterschied zu Ziegler–Nichols toleriert das Verfahren gemäß Skript Totzeiten bis ungefähr:

\[
\boxed{
K_T<2T
}.
\]

Es wird daher häufig bei verfahrenstechnischen Anlagen mit größeren Totzeiten verwendet.

---

## 24.2 PID-Regeln

Mit

\[
r=\frac{K_T}{T}
\]

gilt:

\[
\boxed{
K_P
=
\frac{1.2}{K_S}
\frac{T}{K_T}
\left(
1.35+\frac{K_T}{15T}
\right)
}
\]

\[
\boxed{
K_I
=
\frac{
K_P
\left(
13+8\frac{K_T}{T}
\right)
}{
K_T
\left(
32+6\frac{K_T}{T}
\right)
}
}
\]

\[
\boxed{
K_D
=
K_PK_T
\frac4{
11+2\frac{K_T}{T}
}
}.
\]

Quelle: `skript.pdf`, gedruckte S. 137–138, Tabelle 6.3.

---

# 25. Aufgabe 4a – Cohen–Coon mit \(K_S=2\), \(K_T=2\), \(T=3\)

Aus dem Diagramm:

\[
\boxed{
K_S=2,
\qquad
K_T=2\,\mathrm{s},
\qquad
T=3\,\mathrm{s}
}.
\]

PT1Tt-Modell:

\[
\boxed{
G_S(s)
\approx
\frac2{3s+1}e^{-2s}
}.
\]

---

## 25.1 P-Anteil

\[
K_P
=
\frac{1.2}{2}
\frac32
\left(
1.35+\frac2{45}
\right).
\]

\[
\boxed{
K_P\approx1.255
}.
\]

---

## 25.2 I-Anteil

\[
K_I
=
\frac{
1.255
\left(
13+8\cdot\frac23
\right)
}{
2
\left(
32+6\cdot\frac23
\right)
}.
\]

\[
\boxed{
K_I\approx0.320
}.
\]

---

## 25.3 D-Anteil

\[
K_D
=
1.255\cdot2
\frac4{
11+2\cdot\frac23
}.
\]

\[
\boxed{
K_D\approx0.82
}.
\]

Regler:

\[
\boxed{
G_R(s)
=
1.255+\frac{0.320}{s}+0.82s
}.
\]

Die Mitschrift auf PDF-S. 132 stimmt mit der offiziellen Lösung überein.

---

## 25.4 Vergleich mit Ziegler–Nichols

Für dieselben Messwerte ergäbe Ziegler–Nichols im offenen Kreis:

\[
K_{P,\mathrm{ZN}}
=
\frac{1.2}{2}\frac32
=
0.9,
\]

\[
K_{I,\mathrm{ZN}}
=
\frac{0.9}{4}
=
0.225,
\]

\[
K_{D,\mathrm{ZN}}
=
0.5\cdot0.9\cdot2
=
0.9.
\]

Vergleich:

\[
\begin{array}{c|ccc}
&K_P&K_I&K_D\\
\hline
\text{Ziegler--Nichols}&0.900&0.225&0.900\\
\text{Cohen--Coon}&1.255&0.320&0.820
\end{array}
\]

Für dieses konkrete Beispiel ist Cohen–Coon im P- und I-Anteil aggressiver; der D-Anteil ist geringfügig kleiner.

---

# 26. Aufgabe 4b – Cohen–Coon bei größerer Totzeit

Aus dem Diagramm werden abgelesen:

\[
\boxed{
K_S=2,
\qquad
K_T=5\,\mathrm{s},
\qquad
T=3\,\mathrm{s}
}.
\]

Verhältnis:

\[
\frac{K_T}{T}
=
\frac53
\approx1.67.
\]

Damit liegt das System außerhalb der empfohlenen Ziegler–Nichols-Bedingung

\[
K_T<0.5T,
\]

aber noch innerhalb der Cohen–Coon-Bedingung

\[
K_T<2T.
\]

---

## 26.1 Parameter

\[
\boxed{
K_P\approx0.526
}
\]

\[
\boxed{
K_I\approx0.066
}
\]

\[
\boxed{
K_D\approx0.734
}.
\]

Regler:

\[
\boxed{
G_R(s)
=
0.526+\frac{0.066}{s}+0.734s
}.
\]

Diese Werte entsprechen der offiziellen Lösung.

---

# 27. Typische Fehler in Tutorium 11

1. Nyquist-Ortskurve des geschlossenen statt des offenen Kreises zeichnen.
2. Offene RHP-Pole nicht zählen.
3. Nur positive Frequenzen zeichnen, aber die vollständige Nyquist-Symmetrie nicht berücksichtigen.
4. Den Punkt \(0\) statt \(-1\) als kritischen Punkt verwenden.
5. Umschlingungsrichtung und Vorzeichenkonvention vermischen.
6. Pole auf der imaginären Achse ohne angepasste Kontur behandeln.
7. Bei \(s=j\omega\) das Vorzeichen von \(j^2=-1\) verlieren.
8. Real- und Imaginärteil ohne komplex-konjugierte Erweiterung bestimmen.
9. Lineare und dB-Amplitudenreserve verwechseln.
10. Eine negative Phasenreserve durch falsche Phasenwicklung als große positive Reserve lesen.
11. Beim Lead-Glied \(T_S>T_D\) wählen und damit ein Lag-Glied erzeugen.
12. Nur die fehlende Phasenreserve addieren, ohne Sicherheitszuschlag für die neue Durchtrittsfrequenz.
13. Bei der Bedingung \(20\log|G_0|=10\log\alpha\) das Vorzeichen vertauschen.
14. \(T_S=\alpha/T_D\) statt \(T_S=\alpha T_D\) rechnen.
15. \(K_S\), \(K_T\) und \(T\) aus der Sprungantwort verwechseln.
16. \(0.63K_S\) ab dem Zeitpunkt \(0\) statt ab \(K_T\) auswerten.
17. Beim geschlossenen Ziegler–Nichols-Verfahren \(K_{\mathrm{krit}}\) mit dem Regler-\(K_P\) des fertigen Reglers verwechseln.
18. Die Periodendauer aus Nulldurchgängen statt aus gleichartigen Maxima bestimmen.
19. Cohen–Coon trotz zu großer Totzeit außerhalb des Gültigkeitsbereichs blind anwenden.
20. Empirische Erstparameter als endgültig optimal ansehen.

---

# 28. Qualitätsprüfung der Mitschrift

## Sicher lesbar und fachlich bestätigt

- Nyquist-Grundidee und offene Kette: PDF-S. 142–143,
- vollständige Rechnung Aufgabe 1a: PDF-S. 142,
- vollständige Rechnung Aufgabe 1d: PDF-S. 143,
- Ortskurven und Frequenzmarkierungen: PDF-S. 123–126 und 144,
- Lead-Auslegung: PDF-S. 145–147,
- Ziegler–Nichols offen Aufgabe 3a: PDF-S. 134–135,
- Ziegler–Nichols geschlossen Aufgabe 3b: PDF-S. 136–137,
- Cohen–Coon Aufgabe 4a: PDF-S. 131–132.

## Nur teilweise handschriftlich vorhanden

- Aufgabe 1b und 1c,
- genaue Nyquist-Umschlingungszählung,
- Übungsaufgaben zum Korrekturglied,
- Aufgabe 3c und 3d,
- Cohen–Coon Aufgabe 4b.

Diese Rechenwege wurden aus den offiziellen Aufgaben und Tabellen vollständig ergänzt.

---

# 29. Festgestellte Präzisierungen und Unklarheiten

1. **Aufgabe 1d:**  
   Für negative Frequenzen muss der Imaginärteil wegen der Konjugiertsymmetrie das Vorzeichen wechseln.

2. **Aufgabe 1g:**  
   Die offizielle Phasenreserve ist grafisch gerundet. Die exakte Rechnung ergibt ungefähr \(-6.71^\circ\).

3. **Lead-Entwurf:**  
   Die sichere geschlossene Übertragungsfunktion sollte in faktorisierter Form geschrieben werden. Dadurch werden Vertauschungen von \(T_D\) und \(T_S\) vermieden.

4. **Aufgabe 3c:**  
   Die Messwerte \(K_S\approx3.5\), \(K_T\approx1.5\), \(T\approx6\) sind aus Diagramm und offiziellen Endparametern rekonstruiert.

5. **Aufgabe 3d:**  
   Die Messwerte \(K_{\mathrm{krit}}\approx2\), \(T_{\mathrm{krit}}\approx1.5\) sind aus Diagramm und offiziellen Endparametern rekonstruiert.

6. **Cohen–Coon:**  
   Die Parameter sind empirische Startwerte und kein mathematischer Optimalitätsbeweis.

---

# 30. NotebookLM-Verifikation

--- NOTEBOOKLM-PROMPT ---

Prüfe ausschließlich anhand der hochgeladenen offiziellen Regelungstechnik-Unterlagen folgende Punkte aus „Tutorium 11 – Stabilität II und Reglerentwurf I“:

1. Aufgabe 1g:
Bestimme für
\[
G_0(s)=\frac{25s+60}{10s^3+10s^2+25s}
\]
die exakte Phasendurchtrittsfrequenz, Amplitudenreserve, Gain-Durchtrittsfrequenz und Phasenreserve. Vergleiche mit den grafisch gerundeten offiziellen Werten.

2. Aufgabe 1d:
Prüfe die Vorzeichen des Imaginärteils für negative Frequenzen bei
\[
G_0(s)=\frac3{(s+1)(s-2)}.
\]

3. Aufgabe 3c und 3d:
Gibt die offizielle Quelle die abgelesenen Rohwerte \(K_S,K_T,T\) bzw. \(K_{\mathrm{krit}},T_{\mathrm{krit}}\) ausdrücklich an, oder nur die fertigen Reglerparameter? Prüfe, ob die rekonstruierten Werte
\[
K_S=3.5,\ K_T=1.5,\ T=6
\]
und
\[
K_{\mathrm{krit}}=2,\ T_{\mathrm{krit}}=1.5
\]
die offiziellen Ergebnisse exakt erzeugen.

Belege jede direkte Quellenaussage mit Dokumentname und genauer Seite. Trenne direkte Quelle, Diagrammablesung und eigene mathematische Herleitung.

--- ENDE ---

---

# 31. Kompaktformelsammlung Tutorium 11

## Offene Kette

\[
\boxed{
G_0=G_RG_SG_M
}.
\]

## Rückführdifferenz

\[
\boxed{
F(s)=1+G_0(s)
}.
\]

## Kritischer Nyquist-Punkt

\[
\boxed{-1+j0}.
\]

## Lead-Glied

\[
\boxed{
G_K(s)
=
\frac{T_Ds+1}{T_Ss+1},
\qquad
T_S<T_D
}.
\]

## Verhältnis

\[
\boxed{
\alpha=\frac{T_S}{T_D}
}.
\]

## Maximale Phasenanhebung

\[
\boxed{
\alpha
=
\frac{
1-\sin\Delta\varphi_{\max}
}{
1+\sin\Delta\varphi_{\max}
}
}.
\]

## Frequenz maximaler Phasenanhebung

\[
\boxed{
\omega_{\max}
=
\frac1{\sqrt{T_DT_S}}
=
\frac1{T_D\sqrt\alpha}
}.
\]

## Betrag bei \(\omega_{\max}\)

\[
\boxed{
|G_K(j\omega_{\max})|
=
\frac1{\sqrt\alpha}
}.
\]

## Ziegler–Nichols offen, PID

\[
\boxed{
K_P=\frac{1.2T}{K_SK_T}
}
\]

\[
\boxed{
K_I=\frac{K_P}{2K_T}
}
\]

\[
\boxed{
K_D=0.5K_PK_T
}.
\]

## Ziegler–Nichols geschlossen, PID

\[
\boxed{
K_P=0.6K_{\mathrm{krit}}
}
\]

\[
\boxed{
K_I=\frac{K_P}{0.5T_{\mathrm{krit}}}
}
\]

\[
\boxed{
K_D=0.12K_PT_{\mathrm{krit}}
}.
\]

## PT1Tt-Modell

\[
\boxed{
G_S(s)
\approx
\frac{K_S}{Ts+1}e^{-K_Ts}
}.
\]

---

# Tutorium 12 – Reglerentwurf II und Wurzelortskurve

## 1. Quellen und Seitenbereich

### Primärquellen

1. **RT-Tutorien-Mitschrift.pdf**, PDF-Seiten 151–158
   - S. 151: offizielles Aufgabenblatt zu Aufgabe 1
   - S. 152–153: Theoriefragen und Beginn der Herleitung
   - S. 154–155: Aufgabe 1, Polstellen, Wertetabelle und Beschränkungen
   - S. 156–158: Aufgabe 2, Polstellen, Wertetabelle und Beschränkungen

2. **Regelungstechnik_Tutorium_komplett.pdf**, PDF-Seiten 84–85  
   Tutorium 12, Blattseiten 1/2–2/2. Die offizielle Datei enthält nur Aufgabenstellungen, keine Musterlösung.

3. **skript.pdf**
   - gedruckte S. 141–145: komplex konjugierte dominante Pole
   - gedruckte S. 142–145: Überschwingweite, Überschwingzeit und Ausregelzeit
   - gedruckte S. 147–151: Definition und Entwurf mit der Wurzelortskurve

---

# 2. Theoriefragen

## 2.1 Was beschreibt die Wurzelortskurve?

Die offene Kette werde zerlegt als

\[
G_0(s)=k\,\bar G_0(s),
\qquad k\ge0.
\]

Bei negativer Rückkopplung lautet die charakteristische Gleichung:

\[
\boxed{
1+k\bar G_0(s)=0
}.
\]

Die Wurzelortskurve ist die Menge aller geschlossenen Polstellen, die beim Variieren von \(k\) entstehen:

\[
\boxed{
\mathcal W
=
\left\{
s\in\mathbb C
\mid
1+k\bar G_0(s)=0
\text{ für ein }k\ge0
\right\}
}.
\]

Sie zeigt damit direkt, wie ein Verstärkungsparameter die Stabilität und das Zeitverhalten des geschlossenen Kreises verändert.

Quelle: `skript.pdf`, gedruckte S. 148, Definition 6.29.

---

## 2.2 Warum sind Polstellen für das Zeitverhalten wichtig?

Ein komplexes Polpaar

\[
s_{1,2}
=
-\alpha\pm j\omega,
\qquad
\alpha>0
\]

erzeugt Zeitanteile der Form

\[
e^{-\alpha t}
\left[
C_1\cos(\omega t)
+
C_2\sin(\omega t)
\right].
\]

Damit bestimmt:

- der Realteil \(-\alpha\) die Abklinggeschwindigkeit,
- der Imaginärteil \(\omega\) die Schwingungsfrequenz.

Ein positiver Realteil führt zu exponentiellem Wachstum und damit zu Instabilität.

Die handschriftliche Antwort auf PDF-S. 153 ist fachlich korrekt.

---

## 2.3 Wie erkennt man in der \(s\)-Ebene schnelles Ausregeln?

Je weiter links ein stabiler Pol liegt, desto größer ist

\[
\alpha=-\operatorname{Re}s
\]

und desto schneller klingt

\[
e^{-\alpha t}
\]

ab.

Klausurtauglich:

\[
\boxed{
\text{Stärker negativer Realteil}
\Rightarrow
\text{schnelleres Ausregeln}.
}
\]

Ein großer Imaginärteil allein bedeutet dagegen nur eine höhere Schwingungsfrequenz, nicht automatisch schnelleres Einschwingen.

---

## 2.4 Was bedeutet dominantes Polpaar?

Das dominante Polpaar ist das komplex konjugierte Polpaar, dessen Realteil am nächsten an der imaginären Achse liegt und dessen Beiträge deshalb am langsamsten abklingen.

Nichtdominante Pole liegen deutlich weiter links und verschwinden schneller aus der Zeitantwort.

\[
\boxed{
\text{Dominante Pole prägen das sichtbare Einschwingverhalten.}
}
\]

Bei einem System zweiter Ordnung sind die beiden Pole automatisch dominant.

---

# 3. Zeitkriterien aus der Pollage

## 3.1 Polparameter

Für

\[
s_{1,2}
=
-\alpha\pm j\omega
\]

gilt:

\[
\omega_0
=
\sqrt{\alpha^2+\omega^2},
\]

\[
\zeta
=
\frac{\alpha}{\omega_0}.
\]

Der Winkel \(\varphi_\zeta\) wird im Skript von der negativen reellen Achse zum Pol gemessen:

\[
\boxed{
\cos\varphi_\zeta=\zeta
}.
\]

---

## 3.2 Maximale Überschwingweite

Für ein normiertes PT2-System:

\[
\boxed{
\varepsilon_{\max}
=
\exp\left(
-\frac{\pi\zeta}
{\sqrt{1-\zeta^2}}
\right)
}
\]

oder über den Polwinkel:

\[
\boxed{
\varepsilon_{\max}
=
\exp\left(
-\pi\cot\varphi_\zeta
\right)
}.
\]

Daraus folgt für eine Obergrenze \(M\):

\[
\boxed{
\varphi_\zeta
\le
\arctan\left(
\frac{\pi}{-\ln M}
\right)
}.
\]

Wichtige Werte:

\[
M=10\%
\Rightarrow
\varphi_\zeta
\le
53.76^\circ,
\]

\[
M=5\%
\Rightarrow
\varphi_\zeta
\le
46.36^\circ.
\]

Die erlaubten Pole liegen innerhalb des entsprechenden Sektors um die negative reelle Achse.

---

## 3.3 Überschwingzeit

\[
\boxed{
t_{\max}
=
\frac{\pi}{|\omega|}
}.
\]

Aus

\[
t_{\max}\le t_{\max,\mathrm{zul}}
\]

folgt zwingend:

\[
\boxed{
|\omega|
\ge
\frac{\pi}{t_{\max,\mathrm{zul}}}
}.
\]

### Kritische Vorzeichenregel

Kürzere Überschwingzeit verlangt einen **größeren** Imaginärteil. Der erlaubte Bereich liegt daher außerhalb eines horizontalen Streifens um die reelle Achse.

---

## 3.4 Ausregelzeit

Nach der im Skript verwendeten PT2-Hüllkurve:

\[
\boxed{
t_\varepsilon
\ge
\frac{
\ln\left(
\varepsilon\sqrt{1-\zeta^2}
\right)
}{
-\alpha
}
}.
\]

Mit fest vorgegebenem \(\zeta\) und \(\varepsilon\) erzeugt eine Forderung

\[
t_\varepsilon\in[t_{\min},t_{\max}]
\]

einen vertikalen Streifen für den Realteil.

### Quellenpräzisierung

In den beiden Tutoriumsaufgaben wird ein fester Dämpfungswert \(\zeta\) vorgegeben und zur Berechnung der Ausregelzeitgrenzen benutzt. Die tatsächliche Dämpfung der geschlossenen Pole ändert sich jedoch grundsätzlich mit \(k\).

Das Verfahren ist daher eine vorgegebene Entwurfsapproximation. Es darf nicht unbemerkt mit einer exakt aus den jeweiligen Polen berechneten Dämpfung gleichgesetzt werden.

---

# 4. Ergänzendes allgemeines Rechenschema der Wurzelortskurve

Die folgenden Regeln folgen aus

\[
1+k\bar G_0(s)=0
\]

und ergänzen das tabellarische Vorgehen des Tutoriums.

## 4.1 Betragsbedingung

\[
k\bar G_0(s)=-1.
\]

Daher:

\[
\boxed{
k=\frac1{|\bar G_0(s)|}
}.
\]

## 4.2 Winkelbedingung

\[
\boxed{
\arg\bar G_0(s)
=
(2q+1)\pi,
\qquad
q\in\mathbb Z
}.
\]

## 4.3 Start und Ende

- Für \(k=0\) beginnt jede Wurzelortskurvenbranche an einem offenen Pol.
- Für \(k\to\infty\) endet sie an einer offenen Nullstelle oder im Unendlichen.

## 4.4 Reelle Achse

Ein Punkt auf der reellen Achse gehört zur Wurzelortskurve, wenn rechts von ihm eine ungerade Anzahl reeller offener Pole und Nullstellen liegt.

## 4.5 Aus- und Eintrittspunkte

Mit

\[
k=k(s)
\]

werden mögliche Verzweigungspunkte über

\[
\boxed{
\frac{\mathrm dk}{\mathrm ds}=0
}
\]

bestimmt.

Diese Regeln sind ergänzendes allgemeines Fachwissen und werden im Tutorium selbst nicht vollständig als Algorithmus angegeben.

---

# 5. Aufgabe 1 – PI-Regler an einer PT1-Strecke

## 5.1 Gegeben

\[
G_S(s)
=
\frac1{s+2},
\]

\[
G_R(s)
=
k
\frac{T_Is+1}{T_Is},
\]

\[
T_I=0.3\,\mathrm{s}.
\]

---

## 5.2 Offene Kette

\[
G_0(s)
=
G_R(s)G_S(s).
\]

\[
\boxed{
G_0(s)
=
k
\frac{T_Is+1}
{T_Is(s+2)}
}.
\]

Offene Pole:

\[
p_1=0,
\qquad
p_2=-2.
\]

Offene Nullstelle:

\[
z_1=-\frac1{T_I}
=
-\frac{10}{3}
\approx-3.333.
\]

---

# 6. Aufgabe 1a – geschlossene Polstellen

Charakteristische Gleichung:

\[
1+
k
\frac{T_Is+1}
{T_Is(s+2)}
=
0.
\]

Mit dem Nenner multiplizieren:

\[
T_Is(s+2)+k(T_Is+1)=0.
\]

Ausmultiplizieren:

\[
T_Is^2+(2T_I+kT_I)s+k=0.
\]

Durch \(T_I>0\) teilen:

\[
s^2+(2+k)s+\frac{k}{T_I}=0.
\]

Mit \(T_I=0.3\):

\[
\boxed{
s^2+(2+k)s+\frac{10}{3}k=0
}.
\]

Polstellen:

\[
\boxed{
s_{1,2}(k)
=
-\frac{2+k}{2}
\pm
\sqrt{
\left(
\frac{2+k}{2}
\right)^2
-
\frac{k}{0.3}
}
}.
\]

Für einen negativen Radikanden:

\[
s_{1,2}
=
-\frac{2+k}{2}
\pm
j
\sqrt{
\frac{k}{0.3}
-
\left(
\frac{2+k}{2}
\right)^2
}.
\]

Die Herleitung auf Mitschrift-PDF-S. 153–154 ist korrekt.

---

# 7. Aufgabe 1b – Wertetabelle

\[
\begin{array}{c|c}
k&\text{Polstellen}\\
\hline
0&0,\;-2\\
0.1&-0.173,\;-1.927\\
0.2&-0.363,\;-1.837\\
0.3&-0.582,\;-1.718\\
0.4&-0.873,\;-1.527\\
0.5&-1.250\pm0.323j\\
0.6&-1.300\pm0.557j\\
0.7&-1.350\pm0.715j\\
0.8&-1.400\pm0.841j\\
0.9&-1.450\pm0.947j\\
1.0&-1.500\pm1.041j
\end{array}
\]

Die eingeklebte Tabelle auf PDF-S. 154 stimmt mit diesen Werten überein.

---

## 7.1 Verzweigungspunkte

Komplexe Pole entstehen, wenn die Diskriminante negativ wird.

Grenzfälle:

\[
\left(
\frac{2+k}{2}
\right)^2
-
\frac{k}{0.3}
=
0.
\]

Daraus:

\[
3k^2-28k+12=0.
\]

\[
\boxed{
k_{\mathrm{V},1}
=
\frac{14-4\sqrt{10}}{3}
\approx0.4503
}
\]

\[
\boxed{
k_{\mathrm{V},2}
=
\frac{14+4\sqrt{10}}{3}
\approx8.8830
}.
\]

Zugehörige reelle Polstellen:

\[
\boxed{
s_{\mathrm{V},1}
=
-\frac{10-2\sqrt{10}}{3}
\approx-1.225
}
\]

\[
\boxed{
s_{\mathrm{V},2}
=
-\frac{10+2\sqrt{10}}{3}
\approx-5.442
}.
\]

Im tabellierten Bereich \(0\le k\le1\) ist nur der erste Verzweigungspunkt relevant.

---

# 8. Aufgabe 1c – Zeitbereichsanforderungen

## 8.1 Überschwingweite höchstens \(10\%\)

\[
\varepsilon_{\max}\le0.10.
\]

Daraus:

\[
\boxed{
\varphi_\zeta
\le53.76^\circ
}.
\]

Im für die übrigen Anforderungen relevanten Bereich ist diese Bedingung nicht begrenzend.

---

## 8.2 Überschwingzeit höchstens \(5\,\mathrm{s}\)

\[
t_{\max}
=
\frac{\pi}{|\omega|}
\le5.
\]

Daher:

\[
\boxed{
|\omega|
\ge
\frac{\pi}{5}
\approx0.6283.
}
\]

Für die komplexen Pole aus Aufgabe 1 gilt:

\[
\omega^2
=
\frac{k}{0.3}
-
\left(
\frac{2+k}{2}
\right)^2.
\]

Bedingung:

\[
\frac{k}{0.3}
-
\left(
\frac{2+k}{2}
\right)^2
\ge
\left(
\frac{\pi}{5}
\right)^2.
\]

Lösung:

\[
\boxed{
0.6419
\lesssim k
\lesssim
8.6914
}.
\]

---

## 8.3 Ausregelzeit \(t_\varepsilon\in[1,2]\,\mathrm{s}\)

Die Mitschrift verwendet:

\[
\zeta=0.2,
\qquad
\varepsilon=0.10.
\]

Damit:

\[
\ln\left(
0.10\sqrt{1-0.2^2}
\right)
\approx-2.3230.
\]

Die geschlossenen komplexen Pole besitzen:

\[
\operatorname{Re}s
=
-\frac{2+k}{2}.
\]

Aus der vorgegebenen Ausregelzeitkonstruktion folgt:

\[
\boxed{
-2.323
\lesssim
\operatorname{Re}s
\lesssim
-1.1615
}.
\]

Damit:

\[
\boxed{
0.323
\lesssim k
\lesssim
2.646
}.
\]

---

## 8.4 Zulässiger Bereich nach dem im Tutorium verwendeten Näherungsverfahren

Schnitt aller Bedingungen:

\[
\boxed{
0.6419
\lesssim
k
\lesssim
2.646
}.
\]

Da die vorgegebene Wertetabelle nur

\[
0\le k\le1
\]

enthält, ist innerhalb dieser Tabelle zulässig:

\[
\boxed{
0.642
\lesssim
k
\le1.
}
\]

---

## 8.5 [KORRIGIERT – HANDSCHRIFTLICHES ENDERGEBNIS FALSCH]

Auf Mitschrift-PDF-S. 155 wird aus

\[
t_{\max}\le5
\]

zunächst korrekt

\[
|\omega|\ge\frac{\pi}{5}
\]

hergeleitet. Anschließend wird die Ungleichung jedoch fälschlich zu

\[
|\omega|\le0.62
\]

umgedreht.

Dadurch entsteht das handschriftliche Endergebnis:

\[
0.5\le k\le0.6.
\]

Dieses Intervall erfüllt die Überschwingzeit nicht:

\[
k=0.5
\Rightarrow
t_{\max}
=
\frac{\pi}{0.323}
\approx9.73\,\mathrm{s},
\]

\[
k=0.6
\Rightarrow
t_{\max}
=
\frac{\pi}{0.557}
\approx5.64\,\mathrm{s}.
\]

Beide Werte sind größer als \(5\,\mathrm{s}\).

Das handschriftliche Endergebnis darf daher nicht übernommen werden.

---

# 9. Aufgabe 2 – P-Regler an einer doppelten PT1-Strecke

## 9.1 Gegeben

\[
G_S(s)
=
\frac1{s^2+2s+1}
=
\frac1{(s+1)^2},
\]

\[
G_R(s)=k.
\]

Offene Kette:

\[
\boxed{
G_0(s)
=
\frac{k}{(s+1)^2}
}.
\]

Offene Pole:

\[
p_{1,2}=-1.
\]

Offene Nullstellen: keine.

---

# 10. Aufgabe 2a – geschlossene Polstellen

Charakteristische Gleichung:

\[
1+\frac{k}{s^2+2s+1}=0.
\]

Mit dem Nenner multiplizieren:

\[
s^2+2s+1+k=0.
\]

Mit der quadratischen Lösungsformel:

\[
s_{1,2}
=
-1\pm\sqrt{-k}.
\]

Für \(k\ge0\):

\[
\boxed{
s_{1,2}(k)
=
-1\pm j\sqrt{k}.
}
\]

Die Wurzelortskurve ist damit eine vertikale Gerade:

\[
\boxed{
\operatorname{Re}s=-1.
}
\]

---

# 11. Aufgabe 2b – Wertetabelle

\[
\begin{array}{c|c}
k&\text{Polstellen}\\
\hline
0&-1,\;-1\\
0.1&-1\pm0.316j\\
0.2&-1\pm0.447j\\
0.3&-1\pm0.548j\\
0.4&-1\pm0.632j\\
0.5&-1\pm0.707j\\
0.6&-1\pm0.775j\\
0.7&-1\pm0.837j\\
0.8&-1\pm0.894j\\
0.9&-1\pm0.949j\\
1.0&-1\pm1.000j\\
1.1&-1\pm1.049j
\end{array}
\]

Die eingeklebte Tabelle auf PDF-S. 157 ist korrekt.

---

# 12. Aufgabe 2c – Zeitbereichsanforderungen

## 12.1 Überschwingweite höchstens \(5\%\)

Für:

\[
s_{1,2}=-1\pm j\sqrt{k}
\]

gilt:

\[
\alpha=1,
\qquad
\omega=\sqrt{k}.
\]

Die maximale Überschwingweite lautet:

\[
\varepsilon_{\max}
=
\exp\left(
-\frac{\pi\alpha}{\omega}
\right)
=
\exp\left(
-\frac{\pi}{\sqrt{k}}
\right).
\]

Forderung:

\[
\exp\left(
-\frac{\pi}{\sqrt{k}}
\right)
\le0.05.
\]

Damit:

\[
\boxed{
k
\le
\left(
\frac{\pi}{\ln20}
\right)^2
\approx1.09975.
}
\]

Der zugehörige maximale Polwinkel beträgt:

\[
\boxed{
\varphi_\zeta
\le46.36^\circ.
}
\]

---

## 12.2 Überschwingzeit höchstens \(3\,\mathrm{s}\)

\[
t_{\max}
=
\frac{\pi}{\sqrt{k}}
\le3.
\]

Daraus:

\[
\boxed{
k
\ge
\left(
\frac{\pi}{3}
\right)^2
\approx1.09662.
}
\]

---

## 12.3 Ausregelzeit \(t_\varepsilon\in[3,4]\,\mathrm{s}\)

Die Mitschrift verwendet:

\[
\zeta=0.6,
\qquad
\varepsilon=0.05.
\]

\[
\ln\left(
0.05\sqrt{1-0.6^2}
\right)
=
\ln(0.04)
\approx-3.21888.
\]

Daraus ergibt sich der zulässige Realteil:

\[
\boxed{
-1.073
\lesssim
\operatorname{Re}s
\lesssim
-0.805.
}
\]

Die gesamte Wurzelortskurve besitzt:

\[
\operatorname{Re}s=-1
\]

und erfüllt diese Bedingung daher vollständig.

---

## 12.4 Zulässiger Bereich

Schnitt aus Überschwingweite und Überschwingzeit:

\[
\boxed{
1.09662
\lesssim
k
\lesssim
1.09975.
}
\]

In der gerundeten Wertetabelle ist damit praktisch nur:

\[
\boxed{k\approx1.10}
\]

zulässig.

---

## 12.5 [KORRIGIERT – HANDSCHRIFTLICHES ENDERGEBNIS FALSCH]

Auf Mitschrift-PDF-S. 158 wird aus

\[
t_{\max}\le3
\]

fälschlich der Bereich

\[
|\omega|\le\frac{\pi}{3}
\]

gebildet.

Korrekt ist:

\[
\boxed{
|\omega|\ge\frac{\pi}{3}.
}
\]

Das handschriftliche Ergebnis

\[
k\le1
\]

ist daher falsch.

Für \(k=1\):

\[
t_{\max}
=
\pi
\approx3.142\,\mathrm{s}
>
3\,\mathrm{s}.
\]

Erst ungefähr \(k=1.10\) erfüllt die Zeitforderung und liegt gleichzeitig noch knapp innerhalb der \(5\%\)-Überschwinggrenze.

---

# 13. Vergleich beider Wurzelortskurven

## Aufgabe 1

- Startpole:

\[
0,\;-2
\]

- endliche Nullstelle:

\[
-\frac{10}{3}
\]

- zunächst reeller Verlauf,
- Verzweigung bei:

\[
k\approx0.4503,
\]

- danach komplex konjugierte Pole.

## Aufgabe 2

- doppelter Startpol:

\[
-1
\]

- keine endlichen Nullstellen,
- beide Äste verlaufen exakt vertikal,
- Realteil und damit grundlegende Abklingrate bleiben konstant,
- nur die Schwingungsfrequenz wächst mit \(\sqrt{k}\).

---

# 14. Qualitätsprüfung der Mitschrift

## Sicher lesbar und korrekt

- Definition und Grundidee der Wurzelortskurve auf PDF-S. 152,
- Bedeutung von Real- und Imaginärteil auf PDF-S. 152–153,
- Begriff des dominanten Polpaars auf PDF-S. 153,
- charakteristische Gleichung und Polformel zu Aufgabe 1 auf PDF-S. 153–154,
- beide Wertetabellen,
- charakteristische Gleichung und Polformel zu Aufgabe 2 auf PDF-S. 156–157,
- Ausregelzeitstreifen in beiden Aufgaben.

## Nachgewiesene Fehler

1. Bei beiden Aufgaben wird die Ungleichung aus

\[
t_{\max}=\frac{\pi}{|\omega|}
\]

am Ende in die falsche Richtung übernommen.

2. Dadurch sind beide handschriftlichen \(k\)-Bereiche falsch:

\[
0.5\le k\le0.6
\]

und

\[
k\le1.
\]

3. Die handschriftlichen Winkelwerte \(55^\circ\) und \(43^\circ\) sind nur grobe grafische Näherungen. Exakt gelten ungefähr:

\[
53.76^\circ
\]

und:

\[
46.36^\circ.
\]

4. Die Aufgabe verwendet fest vorgegebene Dämpfungswerte für die Ausregelzeitkonstruktion, obwohl sich die tatsächliche geschlossene Dämpfung mit \(k\) verändert. Das ist als Entwurfsapproximation zu kennzeichnen.

---

# 15. Typische Fehler in Tutorium 12

1. Den offenen Kreis statt des geschlossenen charakteristischen Polynoms null setzen.
2. Den PI-Regler ohne den Faktor \(T_Is\) im Nenner schreiben.
3. Vor dem Teilen durch \(T_I\) Terme verlieren.
4. Reelle und komplexe Fälle der quadratischen Lösungsformel nicht unterscheiden.
5. Den Realteil eines konjugierten Polpaares mit dem Imaginärteil vertauschen.
6. Aus \(t_{\max}\le T\) fälschlich \(|\omega|\le\pi/T\) folgern.
7. Überschwingwinkel von der positiven statt von der negativen reellen Achse messen.
8. Prozentwerte in der Exponentialformel als 5 statt 0.05 einsetzen.
9. Ausregelzeitstreifen und Überschwingsektor verwechseln.
10. Einen tabellarisch groben \(k\)-Wert als exakte Grenze angeben.
11. Die Schnittmenge aller Anforderungen nicht bilden.
12. Eine handschriftliche grafische Lösung ohne algebraische Kontrolle übernehmen.

---

# 16. Klausurstrategie für Wurzelortskurven-Aufgaben

1. Regler in die Form

\[
G_R=k\bar G_R
\]

bringen.

2. Offene Kette:

\[
G_0=k\bar G_0.
\]

3. Charakteristische Gleichung:

\[
1+G_0=0.
\]

4. Nenner beseitigen und Polynom nach \(s\) ordnen.

5. Polformel in Abhängigkeit von \(k\) bestimmen.

6. Wertetabelle berechnen.

7. Startpole und offene Nullstellen markieren.

8. Kurvenverlauf einzeichnen.

9. Zeitforderungen getrennt übersetzen:
   - Überschwingen \(\to\) Winkelsektor,
   - Überschwingzeit \(\to\) Mindestabstand zur reellen Achse,
   - Ausregelzeit \(\to\) vertikaler Realteilbereich.

10. Schnitt mit der Wurzelortskurve bestimmen.

11. \(k\)-Bereich algebraisch kontrollieren.

12. Mindestens einen Randwert in die ursprünglichen Zeitformeln einsetzen.

---

# 17. NotebookLM-Verifikation

--- NOTEBOOKLM-PROMPT ---

Prüfe ausschließlich anhand der hochgeladenen offiziellen Regelungstechnik-Unterlagen und der handschriftlichen Mitschrift die beiden Aufgaben aus „Tutorium 12 – Reglerentwurf II“.

1. Aufgabe 1:
Aus
\[
t_{\max}=\frac{\pi}{|\omega|}
\le5
\]
folgt entweder
\[
|\omega|\ge\frac{\pi}{5}
\]
oder
\[
|\omega|\le\frac{\pi}{5}.
\]
Prüfe die korrekte Richtung und anschließend den zulässigen Bereich von \(k\) für
\[
s_{1,2}(k)
=
-\frac{2+k}{2}
\pm
j\sqrt{
\frac{k}{0.3}
-
\left(
\frac{2+k}{2}
\right)^2
}.
\]

2. Aufgabe 2:
Prüfe für
\[
s_{1,2}=-1\pm j\sqrt{k}
\]
gleichzeitig:
- \(\varepsilon_{\max}\le5\%\),
- \(t_{\max}\le3\,\mathrm{s}\),
- \(t_\varepsilon\in[3,4]\,\mathrm{s}\).

Bestimme den exakten zulässigen \(k\)-Bereich.

3. Prüfe, ob die handschriftlichen Ergebnisse
\[
0.5\le k\le0.6
\]
und
\[
k\le1
\]
mit den Zeitforderungen vereinbar sind.

4. Kläre, wie die in der Aufgabe vorgegebenen Dämpfungswerte \(\zeta=0.2\) und \(\zeta=0.6\) verwendet werden sollen, obwohl sich die Dämpfung der geschlossenen Pole mit \(k\) verändert.

Belege jede direkte Quellenaussage mit Dokumentname und genauer Seite. Trenne Quellenaussage, handschriftlichen Rechenweg und eigene mathematische Kontrolle.

--- ENDE ---

---

# 18. Kompaktformelsammlung Tutorium 12

## Charakteristische Gleichung

\[
\boxed{
1+k\bar G_0(s)=0
}.
\]

## Komplexe Pole

\[
\boxed{
s_{1,2}=-\alpha\pm j\omega
}.
\]

## Dämpfung

\[
\boxed{
\zeta
=
\frac{\alpha}
{\sqrt{\alpha^2+\omega^2}}
}.
\]

## Polwinkel

\[
\boxed{
\cos\varphi_\zeta=\zeta
}.
\]

## Überschwingweite

\[
\boxed{
\varepsilon_{\max}
=
\exp\left(
-\frac{\pi\zeta}
{\sqrt{1-\zeta^2}}
\right)
=
\exp\left(
-\frac{\pi\alpha}{|\omega|}
\right)
}.
\]

## Überschwingzeit

\[
\boxed{
t_{\max}
=
\frac{\pi}{|\omega|}
}.
\]

## Ausregelzeit-Hüllkurve

\[
\boxed{
t_\varepsilon
\ge
\frac{
\ln\left(
\varepsilon\sqrt{1-\zeta^2}
\right)
}{
-\alpha
}
}.
\]

---

# Abschlussstatus der Tutoriumsmitschrift

Die Datei **RT-Tutorien-Mitschrift.pdf** umfasst 158 PDF-Seiten. Sämtliche darin enthaltenen fachlichen Tutorien wurden ausgewertet:

- Tutorium 01
- Tutorium 02
- Tutorium 03
- Tutorium 04
- Tutorium 05
- Tutorium 06
- Tutorium 07
- Tutorium 09
- Tutorium 11
- Tutorium 12

In dieser Datei existieren keine eigenständigen Theorieblöcke mit den Bezeichnungen Tutorium 08 oder Tutorium 10. Die Nummernsprünge hängen mit dem Veranstaltungsablauf, Praxisversuchen bzw. anderen Terminen zusammen.

Damit ist die **Tutoriums-Transkription vollständig**.

---

# Noch offene sinnvolle Erweiterungen des Rechenwege-Masters

Die vollständige Tutoriumsauswertung deckt noch nicht automatisch alle Varianten des gesamten Moduls ab. Für eine klausurorientierte Vollabdeckung sollten anschließend folgende Ergänzungen erfolgen:

## 1. Quellenübergreifende Aufgabentyp-Matrix

Für jeden Aufgabentyp:

- Master-Kapitel,
- offizielles Skript,
- offizielle Übung,
- Tutorium,
- Altklausur SS 2025,
- Altklausur WS 2025/26,
- bekannte Varianten.

Ziel: fehlende Aufgabentypen und Doppelungen systematisch erkennen.

## 2. Offizielle Übungen gegen den Master prüfen

Primär:

- `Regelungstechnik_Übung_Aufg-u-Lösungen.pdf`
- danach `RT_Übungen-ausgefüllt-komplett.pdf`

Es sollen nur Rechenwege ergänzt werden, die im Tutorium fehlen oder wesentlich anders gelöst werden.

## 3. Altklausurvarianten aufnehmen

Aus:

- `RT_Klausur_SS2025-komplett.pdf`
- `RT-Klausur_WS_25_26-komplett.pdf`

Zu ergänzen sind:

- klausurspezifische Varianten,
- typische Punktverteilung,
- wiederkehrende Fallstricke,
- schnellster zulässiger Lösungsweg,
- Aufgaben, die nicht durch Tutorien abgedeckt sind.

## 4. Fehler- und Widerspruchsregister

Alle bereits gefundenen Quellenfehler sollten zusätzlich in einer kompakten Tabelle zusammengeführt werden:

- Dokument,
- Seite/Aufgabe,
- fehlerhafte Angabe,
- korrigierte Angabe,
- Sicherheitsgrad,
- NotebookLM-Verifikationsstatus.

## 5. Entscheidungsbäume

Kurze Klausurabläufe für:

- Zustandsraum bestimmen,
- Laplace und Partialbruchzerlegung,
- Bode-Diagramm,
- Blockschaltbild,
- Führungs-/Störübertragung,
- Hurwitz/Routh,
- Nyquist,
- Reglerauslegung,
- Wurzelortskurve.

## 6. Standardglieder-Index

Die Datei `Tabelle_Standardglieder.pdf` sollte nicht vollständig dupliziert werden. Sinnvoll ist ein Index:

\[
\text{Aufgabensignal}
\rightarrow
\text{erkanntes Glied}
\rightarrow
\text{passende Tabellenzeile}.
\]

## 7. Praxis- und EVA-Inhalte getrennt halten

`Regelungstechnik_Praxisversuche_aufgabe_u_lösung.pdf` und der EVA-Fragenkatalog sollten nur aufgenommen werden, wenn die Inhalte für die schriftliche Prüfung oder die bereits erhaltenen Praxispunkte relevant sind. Reine Versuchsfragen gehören besser in einen eigenen Praxis-Master.

---

# Empfohlener nächster Arbeitsschritt

\[
\boxed{
\text{Offizielle Übungen und Altklausuren gegen den Tutoriums-Master abgleichen}
}
\]

Nicht erneut alles transkribieren, sondern:

1. Aufgabentypen inventarisieren,
2. vorhandene Kapitel zuordnen,
3. nur echte Lücken und Klausurvarianten ergänzen,
4. anschließend einen klausurrelevanten Gesamtindex erzeugen.

---

# Quellenübergreifender Übungs- und Klausurabgleich

## 1. Bearbeitete Quellen

Der Tutoriums-Master wurde mit folgenden Quellen abgeglichen:

1. **Regelungstechnik_Übung_Aufg-u-Lösungen.pdf**, 152 PDF-Seiten  
   Offizielle Übungsaufgaben und Musterlösungen.

2. **RT_Übungen-ausgefüllt-komplett.pdf**, 370 PDF-Seiten  
   Ausgefüllte Übungsfolien des Sommersemesters 2026. Die handschriftliche Annotationsebene wurde für alle elf enthaltenen Übungsblöcke separat extrahiert und visuell geprüft.

3. **RT_Klausur_SS2025-komplett.pdf**, 68 PDF-Seiten  
   Aufgabenbogen, Lösungsbogen und offizielle Musterlösung der Klausur vom 29.07.2025.

4. **RT-Klausur_WS_25_26-komplett.pdf**, 82 PDF-Seiten  
   Aufgabenbogen, Lösungsbogen und offizielle Musterlösung der Klausur vom 12.02.2026.

5. **Tabelle_Standardglieder.pdf**, 3 PDF-Seiten  
   Offizielle Übersicht der Standardglieder.

### Arbeitsprinzip

Nicht erneut vollständig dupliziert wurden Inhalte, die im Tutoriums-Master bereits mit gleichem Rechenweg vorhanden sind. Ergänzt wurden:

- neue Aufgabentypen,
- wesentlich andere Varianten,
- klausurspezifische Kombinationen,
- zusätzliche Kontrollmethoden,
- Fehler und Widersprüche der offiziellen Lösungen.

---

# 2. Quellenübergreifende Abdeckungsmatrix

| Themenblock | Offizielle Übung | Ausgefüllte Übung | Tutoriums-Master | SS 2025 | WS 2025/26 | Ergebnis |
|---|---:|---:|---|---|---|---|
| Modellbildung und Linearisierung | PDF-S. 1–31 | PDF-S. 1–27 | Tutorium 01 | A1 | A1 | abgedeckt; Arbeitspunktverschiebung und UAV-MIMO ergänzt |
| Zeitverhalten, Matrixexponential, Normalformen | PDF-S. 32–46 | PDF-S. 28–76 | Tutorium 02 | MC in A1 | A1d | abgedeckt |
| Laplace und Übertragungsfunktionen | PDF-S. 47–56 | PDF-S. 77–107 | Tutorium 03 | A1d | indirekt | abgedeckt |
| Frequenzdarstellung, Bode, Ortskurve | PDF-S. 57–73 | PDF-S. 108–142 | Tutorium 04 | A2 | A2 | RC-Hochpass, Bandpass und Einmassenschwinger ergänzt |
| Blockschaltbilder und Standardglieder | PDF-S. 74–89 | PDF-S. 143–184 | Tutorium 05 | A3 | A3 | DC-Motor-Blockbild und Gesamtübertragung ergänzt |
| Frequenzganganalyse und Reserven | PDF-S. 90–99 | PDF-S. 185–216 | Tutorium 06 | A2 | A2 | abgedeckt; Klausurfehler ergänzt |
| Führungs-/Störverhalten | PDF-S. 100–111 | PDF-S. 217–239 | Tutorium 07 | A3 | A3 | abgedeckt |
| Stabilität I, Hurwitz, Routh | PDF-S. 112–118 | PDF-S. 240–269 | Tutorium 09 | A4 | A1d/A4 | abgedeckt |
| Stabilität II, Nyquist | PDF-S. 119–127 | PDF-S. 270–296 | Tutorium 11 | A3e | A3e | zusätzliche offizielle Nyquist-Varianten ergänzt |
| Reglerentwurf I, PID, Lead, ZN, Cohen–Coon | PDF-S. 128–143 | PDF-S. 297–343 | Tutorium 11 | A2e/A4d | A4c | PID-Diagnose und Klausurvarianten ergänzt |
| Reglerentwurf II, Lag und Wurzelortskurve | PDF-S. 144–152 | PDF-S. 344–370 | Tutorium 12 | Theorie-MC | A4d | Lag-Glied und korrigierte offizielle WOK ergänzt |

## Ergebnis

Alle wesentlichen schriftlichen Aufgabentypen der offiziellen Übungen und der beiden aktuellen Altklausuren sind nun im Master vertreten.

---

# 3. Ergänzung aus der ausgefüllten Übung: Arbeitspunktverschiebung

## 3.1 Affines linearisiertes Modell

Eine Linearisierung kann zunächst die Form

\[
\dot x=Ax+Bu+e
\]

besitzen. Der konstante Term \(e\) entsteht, wenn die linearisierte Gleichung nicht bereits in Abweichungsgrößen geschrieben wird.

Für einen konstanten Gleichgewichtszustand \(x_{\mathrm{eq}}\) bei \(u=0\) gilt:

\[
0=Ax_{\mathrm{eq}}+e.
\]

Falls \(A\) invertierbar ist:

\[
\boxed{
x_{\mathrm{eq}}=-A^{-1}e
}.
\]

Definiere die Abweichungskoordinate:

\[
\tilde x=x-x_{\mathrm{eq}}.
\]

Dann:

\[
x=\tilde x+x_{\mathrm{eq}},
\qquad
\dot x=\dot{\tilde x}.
\]

Einsetzen:

\[
\dot{\tilde x}
=
A(\tilde x+x_{\mathrm{eq}})+Bu+e.
\]

Mit

\[
Ax_{\mathrm{eq}}+e=0
\]

folgt:

\[
\boxed{
\dot{\tilde x}=A\tilde x+Bu
}.
\]

### Bedeutung

Die Arbeitspunktverschiebung beseitigt den konstanten affinen Term und erzeugt ein homogenes lineares Zustandsmodell in Abweichungsgrößen.

Quelle: `RT_Übungen-ausgefüllt-komplett.pdf`, insbesondere handschriftliche Annotationen auf PDF-S. 22–23.

---

# 4. Neue Übungsvariante: RC-Hochpass

Quelle: `Regelungstechnik_Übung_Aufg-u-Lösungen.pdf`, Übung 04, PDF-S. 57–64.

## 4.1 Übertragungsfunktion

Für den RC-Hochpass gilt:

\[
\boxed{
G_{\mathrm{HP}}(s)
=
\frac{RCs}{1+RCs}
}.
\]

Frequenzgang:

\[
G_{\mathrm{HP}}(j\omega)
=
\frac{j\omega RC}{1+j\omega RC}.
\]

Rationalisiert:

\[
G_{\mathrm{HP}}(j\omega)
=
\frac{(\omega RC)^2}
{1+(\omega RC)^2}
+
j
\frac{\omega RC}
{1+(\omega RC)^2}.
\]

Damit:

\[
\boxed{
\operatorname{Re}G_{\mathrm{HP}}
=
\frac{(\omega RC)^2}
{1+(\omega RC)^2}
}
\]

\[
\boxed{
\operatorname{Im}G_{\mathrm{HP}}
=
\frac{\omega RC}
{1+(\omega RC)^2}
}.
\]

---

## 4.2 Betrag und Phase

\[
\boxed{
|G_{\mathrm{HP}}(j\omega)|
=
\frac{\omega RC}
{\sqrt{1+(\omega RC)^2}}
}
\]

\[
\boxed{
\varphi_{\mathrm{HP}}(\omega)
=
\arctan\left(
\frac{1}{\omega RC}
\right)
=
90^\circ-\arctan(\omega RC)
}
\]

für \(\omega>0\).

Grenzfälle:

\[
\omega\to0:
\quad
|G|\to0,
\quad
\varphi\to90^\circ.
\]

\[
\omega\to\infty:
\quad
|G|\to1,
\quad
\varphi\to0^\circ.
\]

Grenzfrequenz:

\[
\boxed{
\omega_g=\frac1{RC}
}.
\]

Dort:

\[
|G(j\omega_g)|=\frac1{\sqrt2},
\qquad
L(\omega_g)=-3.01\,\mathrm{dB},
\qquad
\varphi(\omega_g)=45^\circ.
\]

---

## 4.3 [KORRIGIERT – OFFIZIELLER FORMELFEHLER]

In der offiziellen Lösung auf PDF-S. 63 endet die Phasenrechnung mit

\[
\varphi=\frac1{\omega RC}.
\]

Korrekt ist:

\[
\boxed{
\varphi
=
\arctan\left(
\frac1{\omega RC}
\right)
}.
\]

Die offizielle Wertetabelle verwendet die korrekten Winkelwerte; betroffen ist die ausgeschriebene Formel.

---

# 5. Neue Übungsvariante: Hochpass und Tiefpass als Bandpass

Quelle: `Regelungstechnik_Übung_Aufg-u-Lösungen.pdf`, Übung 04, PDF-S. 59 und 65–67.

## 5.1 Reihenschaltung

\[
G_{\mathrm{ges}}(s)
=
G_{\mathrm{HP}}(s)G_{\mathrm{TP}}(s).
\]

Mit

\[
G_{\mathrm{HP}}(s)
=
\frac{T_Hs}{1+T_Hs},
\]

\[
G_{\mathrm{TP}}(s)
=
\frac1{1+T_Ls}
\]

folgt:

\[
\boxed{
G_{\mathrm{ges}}(s)
=
\frac{T_Hs}
{(1+T_Hs)(1+T_Ls)}
}.
\]

## 5.2 Sinnvoller Bandpass

Ein echter Durchlassbereich entsteht, wenn:

\[
\boxed{
\omega_{g,\mathrm{HP}}
<
\omega_{g,\mathrm{TP}}
}.
\]

Dann werden

- tiefe Frequenzen durch den Hochpass,
- hohe Frequenzen durch den Tiefpass

gedämpft.

Für die offizielle Variante:

\[
\omega_{g,\mathrm{HP}}=1\,\mathrm{s^{-1}},
\]

\[
\omega_{g,\mathrm{TP}}=100\,\mathrm{s^{-1}}.
\]

Damit liegt der Durchlassbereich ungefähr zwischen:

\[
\boxed{
1
\lesssim
\omega
\lesssim
100\,\mathrm{s^{-1}}
}.
\]

Sind die Ecken umgekehrt angeordnet, existiert praktisch kein sinnvoller Durchlassbereich.

---

# 6. Neue Übungsvariante: Einmassenschwinger im Frequenzbereich

Quelle: `Regelungstechnik_Übung_Aufg-u-Lösungen.pdf`, Übung 04, PDF-S. 59 und 68–73.

## 6.1 Übertragungsfunktion

\[
\boxed{
G(s)
=
\frac{ds+c}
{ms^2+ds+c}
}.
\]

Für:

\[
m=1,
\qquad
c=500,
\qquad
d=20
\]

gilt:

\[
G(s)
=
\frac{20s+500}
{s^2+20s+500}.
\]

Nullstelle:

\[
20s+500=0
\]

\[
\boxed{
s_0=-25
}.
\]

Pole:

\[
s^2+20s+500=0.
\]

\[
\boxed{
s_{1,2}
=
-10\pm20j
}.
\]

Das System ist asymptotisch stabil und schwingfähig.

---

# 7. Neue Übungsvariante: Blockschaltbild des Gleichstrommotors

Quellen:

- `Regelungstechnik_Übung_Aufg-u-Lösungen.pdf`, Übung 05, PDF-S. 76–89
- `RT_Übungen-ausgefüllt-komplett.pdf`, handschriftliche Herleitung auf PDF-S. 172–178

## 7.1 Grundgleichungen

Elektrischer Kreis:

\[
u_A(t)
=
R_Ai_A(t)
+
L_A\dot i_A(t)
+
k_M\omega(t).
\]

Mechanik:

\[
J\dot\omega(t)+k_L\omega(t)=k_Ti_A(t).
\]

Ausgangsdrehzahl:

\[
n(t)=\frac{\omega(t)}{2\pi}.
\]

---

## 7.2 Teilblöcke

Aus dem elektrischen Kreis:

\[
I_A(s)
=
\frac{
U_A(s)-k_M\Omega(s)
}{
L_As+R_A
}.
\]

Mechanischer Block:

\[
\Omega(s)
=
\frac{k_T}
{Js+k_L}
I_A(s).
\]

Ausgang:

\[
N(s)
=
\frac1{2\pi}\Omega(s).
\]

---

## 7.3 Gesamtübertragungsfunktion

Einsetzen und Auflösen nach \(\Omega/U_A\):

\[
\boxed{
\frac{\Omega(s)}{U_A(s)}
=
\frac{k_T}
{
(L_As+R_A)(Js+k_L)+k_Mk_T
}
}.
\]

Ausmultipliziert:

\[
\boxed{
\frac{\Omega(s)}{U_A(s)}
=
\frac{k_T}
{
L_AJs^2
+
(L_Ak_L+R_AJ)s
+
R_Ak_L+k_Mk_T
}
}.
\]

Für die Drehzahl \(n\):

\[
\boxed{
\frac{N(s)}{U_A(s)}
=
\frac{k_T}
{
2\pi
\left[
L_AJs^2
+
(L_Ak_L+R_AJ)s
+
R_Ak_L+k_Mk_T
\right]
}
}.
\]

### Struktur

- Rückführung der Gegen-EMK \(k_M\omega\),
- elektrisches PT1-Teilglied,
- mechanisches PT1-Teilglied,
- Gesamtverhalten zweiter Ordnung.

---

# 8. Offizielle Übung 10: zusätzliche Nyquist-Varianten

Quelle: `Regelungstechnik_Übung_Aufg-u-Lösungen.pdf`, PDF-S. 119–126.

## 8.1 Allgemeines Nyquist-Kriterium mit instabiler offener Kette

\[
G_0(s)
=
\frac{6s}
{(s-1)(s-2)}.
\]

Offene Pole:

\[
p_1=1,
\qquad
p_2=2.
\]

Damit besitzt der offene Kreis zwei Pole in der rechten Halbebene.

Die vollständige Nyquistkurve umschließt den kritischen Punkt in der zur Skriptkonvention passenden Anzahl und Richtung. Algebraische Gegenprobe:

\[
1+G_0(s)=0.
\]

\[
(s-1)(s-2)+6s=0.
\]

\[
s^2+3s+2=0.
\]

\[
\boxed{
s_1=-1,
\qquad
s_2=-2
}.
\]

Der geschlossene Kreis ist stabil, obwohl der offene Kreis instabil ist.

### Klausurlehre

\[
\boxed{
\text{Ein instabiler offener Kreis kann durch Rückkopplung stabil werden.}
}
\]

---

## 8.2 Vereinfachtes Nyquist-Kriterium

\[
G_0(s)
=
\frac{2.5(1-s)}
{s^2+3s+2}.
\]

Offene Pole:

\[
-1,\;-2.
\]

Der offene Kreis ist stabil; deshalb darf das vereinfachte Nyquist-Kriterium verwendet werden.

Die Nullstelle:

\[
s=1
\]

liegt in der rechten Halbebene. Das System ist nicht-minimalphasig, aber die offene Polstabilität bleibt gegeben.

---

## 8.3 Verstärkungsparameter

\[
G_0(s)
=
\frac{K}
{(s+1)(s+2)}.
\]

Geschlossene charakteristische Gleichung:

\[
(s+1)(s+2)+K=0.
\]

\[
\boxed{
s^2+3s+2+K=0
}.
\]

Für ein Polynom zweiter Ordnung gilt:

\[
3>0,
\qquad
2+K>0.
\]

Daher:

\[
\boxed{
K>-2
}.
\]

Grenzfall:

\[
K=-2
\Rightarrow
s(s+3)=0.
\]

Bei der üblichen Vorgabe \(K\ge0\) ist der Kreis für jeden Verstärkungswert stabil.

### [KORRIGIERT – AUFGABENFORMULIERUNG]

Die Aufgabe fragt nach dem „maximal zulässigen“ \(K\). Es existiert jedoch keine endliche obere Stabilitätsgrenze:

\[
\boxed{
K\in(-2,\infty)
}.
\]

Die offizielle Rechnung ist im Ergebnis \(K>-2\) korrekt; die Formulierung „maximal“ ist unpassend.

---

# 9. Neue Übungsvariante: PID-Anteile aus Zeitantworten auswählen

Quelle: `Regelungstechnik_Übung_Aufg-u-Lösungen.pdf`, Übung 11 Reglerentwurf I, PDF-S. 128 und 133.

| Beobachtetes Problem | Geeignete Änderung | Begründung |
|---|---|---|
| bleibende Regelabweichung | I-Anteil ergänzen/erhöhen | erhöht Niederfrequenzverstärkung |
| zu großes Überschwingen | D-Anteil ergänzen/erhöhen, P ggf. reduzieren | erhöht Dämpfung |
| System zu langsam, aber gut gedämpft | P-Anteil erhöhen | erhöht Geschwindigkeit/Bandbreite |
| Schwingungen und langsames Verhalten | P- und D-Anteil gezielt anpassen | P beschleunigt, D dämpft |

### Einschränkung

Diese Regeln sind qualitative Startentscheidungen. Eine Erhöhung von \(P\) kann abhängig von Strecke und Phasenreserve auch das Überschwingen vergrößern.

---

# 10. Neue Lücke geschlossen: phasenabsenkendes Korrekturglied

Quelle: `Regelungstechnik_Übung_Aufg-u-Lösungen.pdf`, Übung 11 Reglerentwurf II, PDF-S. 144–150.

## 10.1 Form

\[
\boxed{
G_{\mathrm{Lag}}(s)
=
K_c
\frac{T_Ds+1}
{Ts+1},
\qquad
T>T_D
}.
\]

Definiere:

\[
\boxed{
\beta=\frac{T}{T_D}>1
}.
\]

Dann:

\[
G_{\mathrm{Lag}}(s)
=
K_c
\frac{T_Ds+1}
{\beta T_Ds+1}.
\]

---

## 10.2 Wirkung

Niederfrequent:

\[
\lim_{\omega\to0}|G_{\mathrm{Lag}}(j\omega)|
=
K_c.
\]

Hochfrequent:

\[
\lim_{\omega\to\infty}|G_{\mathrm{Lag}}(j\omega)|
=
\frac{K_c}{\beta}.
\]

Das Glied kann daher die Niederfrequenzverstärkung erhöhen, ohne die Hochfrequenzverstärkung im gleichen Maß anzuheben.

Die Phase ist im Übergangsbereich negativ:

\[
\varphi_{\mathrm{Lag}}(\omega)
=
\arctan(\omega T_D)
-
\arctan(\omega T)
<0.
\]

---

## 10.3 Offizielle Auslegung für \(6\,\mathrm{dB}\) Niederfrequenzanhebung

Gefordert:

\[
A_{\mathrm{NF}}=6\,\mathrm{dB}.
\]

Daraus:

\[
K_c
=
10^{6/20}
\approx2.
\]

Hochfrequent sollen \(0\,\mathrm{dB}\) verbleiben:

\[
\frac{K_c}{\beta}=1.
\]

Somit:

\[
\boxed{
\beta=K_c\approx2
}.
\]

Übergangsbereich:

\[
f_p=20\,\mathrm{Hz},
\qquad
f_z=40\,\mathrm{Hz}.
\]

Zeitkonstanten:

\[
T
=
\frac1{2\pi f_p}
\approx0.00796\,\mathrm{s},
\]

\[
T_D
=
\frac1{2\pi f_z}
\approx0.00398\,\mathrm{s}.
\]

Ergebnis:

\[
\boxed{
G_{\mathrm{Lag}}(s)
=
2
\frac{0.00398s+1}
{0.00796s+1}
}.
\]

Die offizielle Diagrammauswertung bestätigt näherungsweise:

\[
\boxed{
PM^\ast\ge30^\circ
}.
\]

---

# 11. Offizielle Übungs-Wurzelortskurve: korrigierte Auswertung

Quelle: `Regelungstechnik_Übung_Aufg-u-Lösungen.pdf`, PDF-S. 144–145 und 151–152.

## 11.1 System

\[
G_S(s)
=
\frac1{(s+1)(s+2)},
\]

\[
G_R(s)=k.
\]

Charakteristische Gleichung:

\[
1+\frac{k}{(s+1)(s+2)}=0.
\]

\[
s^2+3s+2+k=0.
\]

Pole:

\[
\boxed{
s_{1,2}
=
-1.5
\pm
\sqrt{0.25-k}
}.
\]

Für \(k>0.25\):

\[
\boxed{
s_{1,2}
=
-1.5
\pm
j\sqrt{k-0.25}
}.
\]

---

## 11.2 Überschwingweite höchstens \(5\%\)

Mit:

\[
\alpha=1.5,
\qquad
\omega=\sqrt{k-0.25}
\]

gilt:

\[
\varepsilon_{\max}
=
\exp\left(
-\frac{1.5\pi}{\sqrt{k-0.25}}
\right)
\le0.05.
\]

Daraus:

\[
\boxed{
k
\le
0.25+
\left(
\frac{1.5\pi}{\ln20}
\right)^2
\approx2.7244
}.
\]

---

## 11.3 Überschwingzeit höchstens \(5\,\mathrm{s}\)

\[
\frac{\pi}{\sqrt{k-0.25}}
\le5.
\]

Daraus:

\[
\boxed{
k
\ge
0.25+
\left(
\frac{\pi}{5}
\right)^2
\approx0.6448
}.
\]

---

## 11.4 Ausregelzeit

Die offizielle Aufgabe verwendet:

\[
\zeta=0.9,
\qquad
t_\varepsilon\in[2,10]\,\mathrm{s}.
\]

Der daraus konstruierte Realteilbereich enthält:

\[
\operatorname{Re}s=-1.5.
\]

Diese Bedingung begrenzt \(k\) für diese Wurzelortskurve nicht weiter.

---

## 11.5 Korrigierter Bereich

Kontinuierlich:

\[
\boxed{
0.6448
\lesssim
k
\lesssim
2.7244
}.
\]

Innerhalb der vorgegebenen Tabelle \(0\le k\le1\) in Schritten von \(0.1\):

\[
\boxed{
k\in\{0.7,0.8,0.9,1.0\}
}.
\]

### [KORRIGIERT – OFFIZIELLE LÖSUNG FALSCH]

Die offizielle Lösung auf PDF-S. 152 verwendet aus

\[
t_{\max}\le5
\]

den Bereich:

\[
|\omega|\le0.63.
\]

Korrekt ist:

\[
\boxed{
|\omega|\ge0.63.
}
\]

Dadurch ist auch der offizielle \(k\)-Bereich bis \(0.6\) falsch.

Dieser Fehler entspricht genau dem bereits im handschriftlichen Tutorium 12 gefundenen Richtungsfehler.

---

# 12. Struktur der beiden aktuellen Altklausuren

## 12.1 Wiederkehrender Aufbau

Beide Klausuren besitzen:

- 120 Minuten,
- vier große Aufgaben,
- je einen Multiple-Choice-Block am Beginn jeder Aufgabe,
- insgesamt ungefähr 120 reguläre Punkte.

Die fachliche Struktur ist bemerkenswert konstant:

| Großaufgabe | Typischer Inhalt |
|---|---|
| Aufgabe 1 | Modellbildung, Linearisierung, Zustandsraum, Zeitbereich |
| Aufgabe 2 | Bode-Diagramm, Standardglieder, Reserven, Korrekturglied |
| Aufgabe 3 | Blockschaltbild, Führungs-/Störübertragung, Pole, Nyquist |
| Aufgabe 4 | Hurwitz/Routh und Reglerentwurf oder Wurzelortskurve |

Diese Struktur ist für die Klausurvorbereitung wichtiger als einzelne Zahlenwerte.

---

# 13. Klausur SS 2025 – Variantenübersicht

Quelle: `RT_Klausur_SS2025-komplett.pdf`.

## Aufgabe 1 – Verladebrücke

- MC zu Transitionsmatrix, Sprungfähigkeit und Regelungsnormalform
- Linearisierung eines nichtlinearen Laufkatzenmodells
- Zustandsraummodell mit gekoppelter Laufkatze und Greifer
- Übertragungsfunktion aus einer Differentialgleichung

### Neue Variante

Die Linearisierung enthält Produkte aus:

\[
\sin\varphi\cos\varphi
\]

und:

\[
\sin\varphi\,\dot\varphi^2.
\]

Bei der Ruhelage \(\varphi_0=\dot\varphi_0=0\) gilt:

\[
\sin\varphi\cos\varphi
\approx
\varphi,
\]

während der zweite Term in erster Ordnung verschwindet.

---

## Aufgabe 2 – Bode und Korrekturglied

- Bode-Diagramm in Basisglieder zerlegen
- Knickfrequenz geometrisch bestimmen
- Amplituden- und Phasenreserve ablesen
- Phasenreserve von \(2^\circ\) auf \(20^\circ\) erhöhen

### Zwei offiziell akzeptierte Strategien

1. P-Glied zur Verschiebung des \(0\,\mathrm{dB}\)-Durchtritts,
2. phasenanhebendes Korrekturglied.

Die Aufgabe zeigt, dass eine Phasenreserve nicht ausschließlich durch ein Lead-Glied verbessert werden muss. Eine Verstärkungsreduktion kann die Durchtrittsfrequenz in einen Bereich mit günstigerer Phase verschieben.

---

## Aufgabe 3 – Blockschaltbild und Nyquist

- komplexes Blockschaltbild zusammenfassen
- Führungs- und Störübertragung mit P-Regler
- Pol-Nullstellen-Vergleich offen/geschlossen
- Nyquist-Auswertung eines Systems dritter Ordnung

### Klausurfallstrick

Bei der Nyquist-Aufgabe werden Betrag und Phase sowie eine Wertetabelle verlangt. Der sichere Rechenweg ist:

\[
G_0(j\omega)
\rightarrow
\operatorname{Re}G_0,\operatorname{Im}G_0
\rightarrow
|G_0|,\varphi
\rightarrow
\text{Stützstellen}
\rightarrow
\text{Ortskurve}.
\]

---

## Aufgabe 4 – Hurwitz und Ziegler–Nichols

- Stabilitätsgebiet in zwei Parametern \(a,K\)
- grafische Schnittmenge mehrerer Ungleichungen
- PID-Auslegung aus einem gegebenen PT1Tt-Modell

### Neue Variante

Nach der algebraischen Hurwitz-Auswertung muss ein zweidimensionales Stabilitätsgebiet gezeichnet werden. Deshalb müssen alle Bedingungen als Funktionen

\[
K=f(a)
\]

in derselben Ebene dargestellt und geschnitten werden.

---

# 14. Klausur WS 2025/26 – Variantenübersicht

Quelle: `RT-Klausur_WS_25_26-komplett.pdf`.

## Aufgabe 1 – UAV

- nichtlineare MIMO-Linearisierung mit vier Rotorkräften
- Zustandsraum mit mehreren Eingängen
- Stabilitätsnachweis eines Greifermodells über Eigenwerte

### Neue Variante

Bei mehreren Eingängen gilt:

\[
\dot x=Ax+Bu
\]

mit:

\[
u=
\begin{bmatrix}
\Delta F_1&
\Delta F_2&
\Delta F_3&
\Delta F_4
\end{bmatrix}^{\!T}.
\]

Die Matrix \(B\) besitzt daher mehrere Spalten. Ein skalarer \(b\)-Vektor reicht nicht.

---

## Aufgabe 2 – Bode-Kombination

- PT1-Glied aus einem Bode-Diagramm erkennen
- Phasenreserve bestimmen
- PD-Faktor

\[
10(1+0.002s)
\]

einzeichnen
- beide Funktionen in Reihe kombinieren

### Klausurfallstrick

Bei der Reihenschaltung werden

- dB-Beträge,
- Phasen

addiert. Die Knickfrequenzen bleiben als getrennte Steigungsänderungen sichtbar.

---

## Aufgabe 3 – Blockschaltbild und Nyquist mit Parameter

- Blockschaltbild reduzieren
- Führungs- und Störübertragung
- Pole und Zeitverhalten vergleichen
- Nyquist-Ortskurve in Abhängigkeit von \(K_R\)
- zulässigen Verstärkungsbereich bestimmen

---

## Aufgabe 4 – Hurwitz, Cohen–Coon, Wurzelortskurve

- zweidimensionales Hurwitz-Gebiet
- Cohen–Coon aus einem PT1Tt-Modell
- \(k\)-Auswahl aus einer vorgegebenen Wurzelortskurve

Diese Aufgabe kombiniert drei eigentlich getrennte Entwurfsverfahren. In der Klausur muss daher schnell erkannt werden, welches Formelschema zu welchem Unterpunkt gehört.

---

# 15. Fehler in der Musterlösung WS 2025/26

## 15.1 Aufgabe 2c – Phasenreserve

Aus der Musterlösung ergibt sich ein PT1-Glied:

\[
G(s)
=
\frac{100}{1+2s}.
\]

Die Gain-Durchtrittsfrequenz erfüllt:

\[
\frac{100}
{\sqrt{1+4\omega_g^2}}
=
1.
\]

Daraus:

\[
\omega_g
=
\frac{\sqrt{9999}}{2}
\approx49.9975.
\]

Phase:

\[
\varphi(\omega_g)
=
-\arctan(2\omega_g)
\approx-89.43^\circ.
\]

Phasenreserve:

\[
\boxed{
\Delta\varphi
=
180^\circ+\varphi(\omega_g)
\approx90.57^\circ
}.
\]

Grafisch ungefähr:

\[
\boxed{
90^\circ
}.
\]

### [KORRIGIERT – OFFIZIELLE LÖSUNG FALSCH]

Die Musterlösung nennt:

\[
270^\circ.
\]

Das entsteht durch:

\[
180^\circ-(-90^\circ).
\]

Die standardmäßige Phasenreserve ist jedoch der Abstand von \(-180^\circ\):

\[
\boxed{
180^\circ+(-90^\circ)=90^\circ.
}
\]

Quelle: `RT-Klausur_WS_25_26-komplett.pdf`, Musterlösung, gedruckte S. 15.

---

## 15.2 Aufgabe 4d – Wurzelortskurve

Aus der Wertetabelle folgt für die komplexen Pole:

\[
s_{1,2}
=
-0.5
\pm
j\sqrt{k-0.25}.
\]

### Überschwingzeit

\[
\frac{\pi}{\sqrt{k-0.25}}
\le7.
\]

\[
\boxed{
k
\ge
0.25+
\left(
\frac{\pi}{7}
\right)^2
\approx0.4514
}.
\]

### Überschwingweite \(5\%\)

\[
\exp\left(
-\frac{0.5\pi}{\sqrt{k-0.25}}
\right)
\le0.05.
\]

\[
\boxed{
k
\le
0.25+
\left(
\frac{0.5\pi}{\ln20}
\right)^2
\approx0.5249
}.
\]

Die vorgegebene Ausregelzeitbegrenzung enthält den konstanten Realteil \(-0.5\).

Damit kontinuierlich:

\[
\boxed{
0.4514
\lesssim
k
\lesssim
0.5249
}.
\]

Bei den tabellierten Schritten von \(0.1\) bleibt nur:

\[
\boxed{k=0.5}.
\]

### [KORRIGIERT – OFFIZIELLE LÖSUNG FALSCH]

Die Musterlösung verwendet für \(t_{\max}\le7\):

\[
|\omega|\le0.45
\]

statt:

\[
\boxed{
|\omega|\ge0.45.
}
\]

Der offizielle Bereich \(0.3\le k\le0.4\) ist daher nicht mit der Überschwingzeit vereinbar.

Quelle: `RT-Klausur_WS_25_26-komplett.pdf`, Musterlösung, gedruckte S. 31–32.

---

# 16. Klausurrelevante Aufgabentyp-Matrix

| Aufgabensignal | Gesuchtes Verfahren | Master-Kapitel |
|---|---|---|
| nichtlineare DGL + Arbeitspunkt | Taylor-/Jacobi-Linearisierung | Tutorium 01 |
| DGL \(n\)-ter Ordnung | Regelungsnormalform | Tutorium 01/03 |
| \(x'=Ax+Bu\) | Eigenwerte, Matrixexponential, Normalform | Tutorium 02 |
| \(Y/U\), Anfangswerte null | Laplace und Übertragungsfunktion | Tutorium 03 |
| Sprungantwort | \(U=1/s\), Partialbruchzerlegung | Tutorium 03 |
| \(s=j\omega\) | Frequenzgang, Betrag, Phase | Tutorium 04 |
| Bode-Linien | Standardglieder und Eckfrequenzen | Tutorium 04/06 |
| verschachteltes Blockbild | Signalgleichungen oder innere Schleife zuerst | Tutorium 05 |
| \(G_w,G_{d1},G_{d2}\) | Sensitivitätsfunktionen | Tutorium 07 |
| Parameterpolynom | Hurwitz/Routh | Tutorium 09 |
| Ortskurve und \(-1\) | Nyquist | Tutorium 11 |
| Phasenreserve erhöhen | Lead oder Durchtritt verschieben | Tutorium 11 |
| Niederfrequenzgenauigkeit ohne HF-Anhebung | Lag-Glied | Quellenabgleich, Kapitel 10 |
| PT1Tt-Sprungantwort | Ziegler–Nichols/Cohen–Coon | Tutorium 11 |
| Pole als Funktion von \(k\) | Wurzelortskurve | Tutorium 12 |
| \(a,K\)-Gebiet | Ungleichungen bestimmen und graphisch schneiden | Klausurvarianten |

---

# 17. Entscheidungsbäume für die Klausur

## 17.1 Modellbildung und Linearisierung

1. Koordinaten und positive Richtungen festlegen.
2. Kräfte/Momente vollständig aufstellen.
3. DGL nach höchsten Ableitungen lösen.
4. Arbeitspunkt einsetzen.
5. Nichtlineare Terme mit partiellen Ableitungen linearisieren.
6. Abweichungsgrößen definieren.
7. Zustände nach minimaler Ableitungskette wählen.
8. \(A,B,C,D\) einsetzen.
9. Dimensionen und Arbeitspunkt kontrollieren.

---

## 17.2 Laplace und Übertragungsfunktion

1. Anfangsbedingungen prüfen.
2. DGL transformieren.
3. alle \(Y(s)\)-Terme sammeln.
4. nach \(Y/U\) auflösen.
5. Zähler-/Nennergrad prüfen.
6. bei Eingangssignal \(Y=GU\) bilden.
7. Partialbruchzerlegung.
8. Anfangs- und Endwert prüfen.

---

## 17.3 Bode-Diagramm

1. Funktion faktorisieren.
2. Verstärkung separat in dB.
3. Pole/Nullstellen im Ursprung erfassen.
4. Eckfrequenzen \(1/T\) markieren.
5. Steigungsänderungen addieren.
6. Phasenbeiträge addieren.
7. Gain- und Phasendurchtritt markieren.
8. Reserven mit Vorzeichen kontrollieren.

---

## 17.4 Blockschaltbild

1. Summationsvorzeichen markieren.
2. innere Schleife identifizieren.
3. Reihen multiplizieren.
4. Parallelen mit Vorzeichen addieren.
5. Rückkopplung mit \(G/(1\pm GH)\).
6. alternativ alle Signale algebraisch benennen.
7. Doppelbrüche beseitigen.
8. Grenzfälle einzelner Blöcke prüfen.

---

## 17.5 Stabilität

1. geschlossenes charakteristisches Polynom bilden.
2. Grad und Koeffizienten sortieren.
3. einfache Pole direkt berechnen.
4. Parameterfall: Hurwitz oder Routh.
5. strikte Ungleichungen verwenden.
6. Gleichheitsgrenzen separat prüfen.
7. Zustands- und E/A-Stabilität unterscheiden.

---

## 17.6 Nyquist

1. offene Kette bilden.
2. offene RHP-Pole zählen.
3. \(G_0(j\omega)\) bestimmen.
4. Real-/Imaginärteil oder Betrag/Phase berechnen.
5. markante Frequenzen bestimmen.
6. vollständige Kurve und Richtung zeichnen.
7. Umschlingung von \(-1\) auswerten.
8. mit geschlossenem Polynom gegenprüfen.

---

## 17.7 Korrekturglied

### Lead

- Ziel: Phase erhöhen, Dynamik verbessern.
- \(T_S<T_D\).
- \(\alpha=T_S/T_D<1\).
- Sicherheitszuschlag zur benötigten Phase.
- neue Durchtrittsfrequenz bestimmen.

### Lag

- Ziel: Niederfrequenzverstärkung erhöhen, Hochfrequenzniveau begrenzen.
- \(T>T_D\).
- \(\beta=T/T_D>1\).
- Phasenreserve nach Einbau kontrollieren.

---

## 17.8 Wurzelortskurve

1. \(1+k\bar G_0(s)=0\).
2. Pole in Abhängigkeit von \(k\).
3. Startpole und Nullstellen.
4. Wertetabelle.
5. Überschwingsektor.
6. Mindest-Imaginärteil aus \(t_{\max}\).
7. Realteilstreifen aus \(t_\varepsilon\).
8. Schnittbereich bestimmen.
9. Randwerte in Zeitformeln einsetzen.

---

# 18. Index zur Tabelle der Standardglieder

Quelle: `Tabelle_Standardglieder.pdf`.

| Erkennungsform | Glied | Tabellenfundstelle |
|---|---|---|
| \(K\) | P | PDF-S. 1 |
| \(K/(1+Ts)\) | PT1 | PDF-S. 1 |
| \(K\omega_0^2/(s^2+2D\omega_0s+\omega_0^2)\) | PT2 | PDF-S. 1 |
| \(1/(T_Is)\) | I | PDF-S. 1 |
| \(1/[T_Is(1+T_1s)]\) | IT1 | PDF-S. 1 |
| \(T_Ds\) | D | PDF-S. 2 |
| \(T_Ds/(1+T_1s)\) | DT1 | PDF-S. 2 |
| \(K(1+1/(T_Is))\) | PI | PDF-S. 2 |
| PI mit zusätzlichem PT1-Nenner | PIT1 | PDF-S. 2 |
| \(K(1+T_Ds)\) | PD | PDF-S. 2 |
| PD mit zusätzlichem PT1-Nenner | PDT1 | PDF-S. 2 |
| \(K(1+1/(T_Is)+T_Ds)\) | PID | PDF-S. 3 |
| PID mit zusätzlichem PT1-Nenner | PIDT1 | PDF-S. 3 |
| \(Ke^{-T_ts}\) | Totzeit | PDF-S. 3 |

### Verwendung

Die Tabelle dient vor allem zum schnellen Erkennen und Skizzieren. Für Vorzeichen, Stabilität und Kombinationen bleibt die eigene Rechnung maßgeblich.

---

# 19. Kompaktes Fehler- und Widerspruchsregister

| Quelle | Fundstelle | Problem | Korrektur | Status |
|---|---|---|---|---|
| RT-Tutorien-Mitschrift | Tut. 01, Aufgabe 1 | Komponenten/Indizes in Fahrzeuggleichung vertauscht | offizielle Kraftzerlegung verwenden | mathematisch geklärt |
| Tutorium offiziell | Tut. 02, 1c | falsches Vorzeichen im Eigenvektor | \((-1,0,1)^T\) | mathematisch geklärt |
| Tutorium offiziell | Tut. 02, 1h | Faktor \(\sqrt2\) in \(V\) fehlt | skalierte Spalte verwenden | mathematisch geklärt |
| Tutorium offiziell | Tut. 02, 1i | falsche Transformationsmatrix | Real-/Imaginärteile des Eigenvektors verwenden | mathematisch geklärt |
| Tutorium offiziell | Tut. 02, 2g | Transitionsmatrix verletzt \(\Phi(0)=I\) | korrigiertes \(e^{At}\) im Kapitel | mathematisch geklärt |
| Tutorium/Mitschrift | Tut. 03 | Dämpfungssatz als Verschiebungssatz bezeichnet | Begriffe trennen | Skriptabgleich |
| Tutorium offiziell | Tut. 04, 1c | Betrag mit \(C\) statt \(|C|\) | \(|C|\) | mathematisch geklärt |
| Tutorium offiziell | Tut. 04, 4b | negatives Realteilverhalten beim I-Glied behauptet | \(\operatorname{Re}G=0\) | mathematisch geklärt |
| Tutorium offiziell | Tut. 06, 2e | Reserve, Frequenz und Vorzeichen inkonsistent | exakte/asymptotische Werte getrennt | NotebookLM-Prompt vorhanden |
| Tutorium offiziell | Tut. 09, 1c | Zusatz \(k<5d^2/(16m)\) unbegründet | Stabilität: \(d>0,k>0\) | NotebookLM-Prompt vorhanden |
| Tutorium offiziell | Tut. 09, 3a–c | Gleichheitsgrenzen als stabil eingeschlossen | strikte Ungleichungen | mathematisch geklärt |
| Mitschrift | Tut. 12, beide Aufgaben | Ungleichung aus \(t_{\max}\) umgedreht | \(|\omega|\ge\pi/t_{\max}\) | mathematisch geklärt |
| Offizielle Übung | PDF-S. 63 | Hochpassphase ohne \(\arctan\) | \(\arctan(1/\omega RC)\) | visuell bestätigt |
| Offizielle Übung | PDF-S. 126 | „maximales“ \(K\), obwohl keine obere Grenze | \(K>-2\) | mathematisch geklärt |
| Offizielle Übung | PDF-S. 152 | WOK-Zeitbedingung umgedreht | \(k\ge0.6448\) | mathematisch geklärt |
| Klausur WS 25/26 | Musterlösung S. 15 | Phasenreserve \(270^\circ\) | ca. \(90^\circ\) | mathematisch geklärt |
| Klausur WS 25/26 | Musterlösung S. 31 | WOK-Zeitbedingung umgedreht | \(0.4514\lesssim k\lesssim0.5249\) | mathematisch geklärt |

## Verwendung des Registers

Bei einer Klausuraufgabe ist stets zuerst die Aufgabenstellung zu lösen. Eine bekannte fehlerhafte Musterlösung darf nicht als Begründung übernommen werden.

---

# 20. Priorisierung nach Klausurrelevanz

Auf Grundlage beider Altklausuren ist die höchste Priorität:

1. **Linearisierung und Zustandsraum**
2. **Bode-Diagramm und Reserven**
3. **Blockschaltbild, Führungs- und Störübertragung**
4. **Nyquist**
5. **Hurwitz/Routh mit Parametern**
6. **Reglerentwurf: Lead, Ziegler–Nichols, Cohen–Coon**
7. **Wurzelortskurve**
8. **Matrixexponential und Normalformen**
9. **Laplace/Partialbruch als notwendiges Werkzeug**

Die Rangfolge bedeutet nicht, dass die unteren Themen unwichtig sind. Sie beschreibt die Wiederholung in den beiden jüngsten vollständigen Klausuren.

---

# 21. Abschlussstatus des Rechenwege-Masters

## Vollständig integriert

- offizielles Skript als Theoriegrundlage,
- sämtliche Tutoriumsmitschriften,
- offizielle Tutoriumsaufgaben,
- offizielle Übungen und Musterlösungen,
- ausgefüllte Übungsfolien einschließlich handschriftlicher Annotationen,
- Klausur SS 2025,
- Klausur WS 2025/26,
- Standardgliedertabelle.

## Bewusst getrennt

Nicht in diesen schriftlichen Rechenwege-Master integriert wurden:

- reine Praxisversuchsabläufe,
- EVA-Prüfungsfragen,
- versuchsspezifische Bedien- und Messdetails.

Diese Inhalte sollten in einem eigenen Praxis-/EVA-Master bleiben, damit die schriftliche Klausurquelle nicht unnötig aufgebläht wird.

## Nächster sinnvoller Lernschritt

Die Quellenanalyse ist abgeschlossen. Der nächste Schritt ist keine weitere Transkription, sondern:

1. diagnostische Aufgaben je Hauptthema,
2. Fehlerprofil erstellen,
3. gezielte Wiederholung der schwächsten Aufgabentypen,
4. anschließend vollständige Probeklausur unter Zeitdruck.

