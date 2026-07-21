# KlausurBotPro – Fach- und Schnittstellenspezifikation

## Charakteristische Polynome und Parameterbedingungen bis zwei Variablen

**Status:** Fachspezifikation  
**Nicht enthalten:** Implementierung, Codex-Prompt, universelles CAS

## 1. Verbindliche Kernaussage

Der gemeinsame Kern benötigt exakt zwei fachliche Funktionen:

1. Ein charakteristisches Polynom kanonisieren, ohne Herkunft, Gradbedingungen oder Kürzungen zu verlieren.
2. Ein bereits erzeugtes Gleichungs- und Ungleichungssystem über höchstens zwei reellen Parametern exakt auswerten.

Hurwitz, Nyquist und Wurzelortskurve erzeugen ihre Bedingungen selbst. Der gemeinsame Kern kennt keine Stabilitätslogik.

\[
\boxed{
\text{Fachblock erzeugt Bedingungen}
\longrightarrow
\text{gemeinsamer Kern löst Mengenproblem}
}
\]

---

# 2. Quellenbefund

## 2.1 Tatsächlich auftretende Bedingungstypen

| Typ | Quellenbeispiel | Ergebnisform |
|---|---|---|
| Lineare Ungleichung | \(a>-20/9\) | Halbachse |
| Lineare Parameterkopplung | \(K>-20a/9\) | offene Halbebene |
| Quadratische Grenze | \(K<a^2+9a+20\) | Gebiet unter einer Parabel |
| Rationaler Vergleich | \(T_N>K_R/(1+3K_R)\) | 2D-Gebiet mit Nennerbedingung |
| Einparametriger Stabilitätsbereich | \(0<K_P<20\) | offenes Intervall |
| Nyquist-Verstärkungsbereich | \(-1/3<K_R<56/3\) | offenes Intervall |
| Leistungsbedingung | \(k\ge c_1,\;k\le c_2\) | geschlossenes Intervall |
| Widersprüchliche Bedingungen | \(k_p>0\land k_p<-40\) | leere Menge |
| Gleichheitsrand | \(\Delta_2=0\) | ausgeschlossene Stabilitätsgrenze |
| Gradwechsel | Leitkoeffizient \(=0\) | separate Fallunterscheidung |

In den untersuchten Klausuren treten höchstens zwei freie reelle Parameter auf:

- \((a,K)\) bei Hurwitz,
- \((K_R,T_N)\) in Tutoriumsaufgaben,
- ein einzelner Verstärkungsparameter bei Nyquist und Wurzelortskurven.

Die charakteristische Gleichung kann laut Skript aus \(\det(\lambda I-A)=0\) oder aus einem Nennerpolynom stammen. Die Wurzelortskurve basiert auf den Nullstellen von \(1+k\widetilde G_R(s)G_S(s)=0\). Diese vorgelagerten Rechnungen gehören nicht in den gemeinsamen Kern. fileciteturn1file6 fileciteturn1file1

## 2.2 Offene und geschlossene Grenzen

Verbindliche Regel:

- Hurwitz-, Routh- und Nyquist-Grenzen für **asymptotische Stabilität** sind strikt und damit offen.
- Anforderungen mit \(\le\) oder \(\ge\), etwa maximale Überschwingweite oder maximale Überschwingzeit, dürfen geschlossene Randpunkte erzeugen.
- Nennernullstellen bleiben immer ausgeschlossen.
- Ein verschwindender Leitkoeffizient ist kein gewöhnlicher ausgeschlossener Rand, sondern ein eigener Gradfall.
- Eine Gleichheitsgrenze darf nicht automatisch als „grenzstabil“ bezeichnet werden. Der erzeugende Fachblock muss den Randfall fachlich klassifizieren.

Diese Trennung entspricht bereits den verbindlichen Entscheidungen der Hurwitz/Routh-Spezifikation v2. fileciteturn8file16

---

# 3. Modulgrenze

## 3.1 Der gemeinsame Kern übernimmt

- Kanonisierung eines bereits erzeugten Polynoms in \(s\),
- Erfassung von Grad- und Leitkoeffizientenfällen,
- Erhaltung von Annahmen und Ausschlussmengen,
- Normalisierung von Gleichungen und Ungleichungen,
- Schnitt und Vereinigung,
- Erkennung der leeren Menge,
- exakte einparametrige Intervallmengen,
- beschränkte zweidimensionale Gebiete,
- Randpunkte und Randkurven,
- sichere Testpunkte in nachgewiesenen Gebieten,
- numerische Kontrollwerte,
- LaTeX-Darstellung.

## 3.2 Der gemeinsame Kern übernimmt nicht

- DGL- oder Laplace-Rechnung,
- Bildung einer Übertragungsfunktion,
- Blockschaltbildreduktion,
- Bildung von \(1+G_0(s)\),
- Hurwitz-Matrix oder Routh-Schema,
- Nyquist-Umschlingungen,
- Frequenzgangrechnung,
- Übersetzung von Zeitforderungen in Polbedingungen,
- automatische Auswahl des richtigen Stabilitätsbegriffs,
- Polberechnung als primären Lösungsweg.

---

# 4. Kanonischer Vertrag für charakteristische Polynome

## 4.1 Grundobjekt

Ein übergebenes Polynom besitzt die Form

\[
p(s;\theta)
=
a_n(\theta)s^n+a_{n-1}(\theta)s^{n-1}
+\dots+a_1(\theta)s+a_0(\theta),
\]

mit höchstens zwei freien reellen Entscheidungsparametern

\[
\theta=(\theta_1)
\quad\text{oder}\quad
\theta=(\theta_1,\theta_2).
\]

## 4.2 Pflichtfelder

| Feld | Bedeutung |
|---|---|
| Hauptvariable | exakt \(s\) |
| Koeffizienten | absteigend \([a_n,\ldots,a_0]\) |
| deklarierter Grad | Grad vor Parameterspezialisierung |
| freie Parameter | geordnete Liste mit maximal zwei reellen Variablen |
| feste Konstanten | Parameter, die nicht gelöst werden und vollständig spezifiziert sein müssen |
| Annahmen | etwa \(K_R>0,\;T_N>0,\;\omega_0>0\) |
| Ausschlussmengen | etwa \(1+3K_R\neq0\) |
| Polynomrolle | fachliche Bedeutung des Polynoms |
| Analysebedeutung | interne Stabilität, E/A-Stabilität oder reine Nenneranalyse |
| Provenienz | Dokument, Seite/Aufgabe, erzeugender Fachblock |
| Transformationshistorie | Ausmultiplizieren, Skalieren, Kürzungen |
| entfernte Faktoren | bei Pol-Nullstellen-Kürzungen zwingend |
| erwartete Gradfälle | regulärer Grad und mögliche Gradabfälle |

## 4.3 Zulässige Polynomrollen

1. `DIRECT_CHARACTERISTIC_POLYNOMIAL`  
   Direkt eingegebenes charakteristisches Polynom.

2. `CLOSED_TRANSFER_DENOMINATOR`  
   Nenner einer bereits gegebenen geschlossenen Übertragungsfunktion.

3. `RAW_CLOSED_LOOP_CHARACTERISTIC`  
   Rohes internes charakteristisches Polynom vor einer E/A-Kürzung.

4. `REDUCED_TRANSFER_DENOMINATOR`  
   Gekürzter Nenner zur E/A- beziehungsweise BIBO-Analyse.

5. `STATE_CHARACTERISTIC_POLYNOMIAL`  
   Polynom aus \(\det(sI-A)\).

Die Rollen `RAW_CLOSED_LOOP_CHARACTERISTIC` und `REDUCED_TRANSFER_DENOMINATOR` sind nicht austauschbar.

## 4.4 Kürzungen

Eine Kürzung muss als strukturierte Information erhalten bleiben:

\[
p_{\mathrm{raw}}(s)
=
q(s)\,p_{\mathrm{red}}(s).
\]

Zu speichern sind:

- entfernter Faktor \(q(s)\),
- Bedingungen, unter denen die Kürzung algebraisch zulässig war,
- dadurch entfernte Pole beziehungsweise Definitionslücken,
- Analyseziel des reduzierten Polynoms.

Der Kern darf nicht selbst entscheiden, ob das rohe oder reduzierte Polynom für eine Stabilitätsaussage maßgeblich ist.

## 4.5 Skalierungsregeln

Eine Multiplikation mit einer sicher von null verschiedenen Konstanten ändert die Nullstellen nicht.

Eine Division durch einen parameterabhängigen Leitkoeffizienten \(a_n(\theta)\) ist nur zulässig, wenn

\[
a_n(\theta)\neq0
\]

als Bedingung erhalten bleibt.

Ist das Vorzeichen nicht bekannt, entstehen Fallzweige:

\[
a_n>0,\qquad a_n<0,\qquad a_n=0.
\]

Der Fall \(a_n=0\) ist ein Gradabfall und darf nicht entfernt werden.

## 4.6 Degenerationen

- Nullpolynom: kein gültiges charakteristisches Polynom.
- Konstantes Nichtnullpolynom: degenerierter Fall ohne Nullstellen; kein gewöhnliches dynamisches System.
- Verschwindender Leitkoeffizient: Grad neu bestimmen.
- Mehrere führende Koeffizienten null: wiederholt reduzieren.
- Alle Koeffizienten null: strukturierter Fehler, keine erfundene Lösung.

---

# 5. Vertrag für Parameterbedingungen

## 5.1 Eingabe

Ein `ParameterConditionProblem` enthält:

| Feld | Bedeutung |
|---|---|
| Variablen | eine oder zwei reelle Variablen |
| Grundannahmen | physikalische oder aufgabenspezifische Bedingungen |
| Ausschlüsse | Nennernullstellen und sonstige verbotene Werte |
| logische Formel | Baum aus atomaren Bedingungen, Schnitt und Vereinigung |
| Provenienz je Atom | erzeugender Fachblock und fachliche Bedeutung |
| gewünschte Ergebnisform | 1D-Intervallmenge oder 2D-Bedingungsmenge |
| numerisches Darstellungsfenster | optional, ohne Einfluss auf das exakte Ergebnis |

## 5.2 Atomare Bedingungen

Unterstützt werden:

\[
f=0,\quad f\neq0,
\]

\[
f<0,\quad f\le0,\quad f>0,\quad f\ge0.
\]

Dabei ist \(f\):

- ein einfaches Polynom,
- oder ein rationaler Ausdruck mit explizitem Zähler, Nenner und Nennerausschluss.

Ein rationales Atom wird nicht als undurchsichtiger Quotient gespeichert, sondern als

\[
\frac{N(\theta)}{D(\theta)}\;\square\;0,
\qquad D(\theta)\neq0.
\]

## 5.3 Logik

Erforderlich sind:

\[
A\land B,
\qquad
A\lor B.
\]

Eine allgemeine Negationslogik ist nicht nötig. Negationen werden vorab auf atomare Relationen zurückgeführt, beispielsweise

\[
\neg(x<0)\equiv x\ge0.
\]

Mehrere Fachbedingungen werden grundsätzlich als Schnitt behandelt:

\[
S
=
S_{\mathrm{Annahmen}}
\cap
S_{\mathrm{Fachbedingungen}}
\cap
S_{\mathrm{Definition}}
.
\]

Vereinigungen entstehen insbesondere durch:

- unterschiedliche Nenner-Vorzeichen,
- Gradfälle,
- mehrere getrennte stabile Intervalle,
- explizite Alternativen eines Fachblocks.

---

# 6. Exakte Darstellung

## 6.1 Zulässige Konstanten

Primär exakt:

- ganze Zahlen,
- rationale Zahlen,
- algebraische Zahlen und Wurzeln,
- \(\pi\) und Logarithmen exakter positiver Zahlen als bereits isolierte Konstanten.

Der Kern darf beispielsweise lösen:

\[
k\ge \frac14+\left(\frac{\pi}{7}\right)^2.
\]

Er soll dagegen nicht selbst die transzendente Ausgangsungleichung

\[
\frac{\pi}{\sqrt{k-1/4}}\le7
\]

herleiten und umformen. Diese Übersetzung gehört zum Wurzelortskurven- beziehungsweise Zeitforderungblock.

## 6.2 Einparametrige Ausgabe

Vollständig unterstützt:

- offene, geschlossene und halboffene Intervalle,
- unbeschränkte Intervalle,
- endliche Vereinigungen,
- einzelne Punkte,
- Punktmengen,
- leere Menge.

Beispiel:

\[
(-\infty,-2)\cup(1,\infty).
\]

## 6.3 Zweiparametrige Ausgabe

Das exakte Hauptergebnis ist eine Bedingungsmenge:

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

Zusätzlich:

- Randkurven,
- Randinklusion,
- Schnittpunkte,
- Ausschlusskurven,
- zertifizierte Testpunkte,
- numerische Approximationen.

---

# 7. Normalisierung

## 7.1 Allgemein

Jedes Atom wird in die Form

\[
f(\theta)\;\square\;0
\]

gebracht.

Dabei werden erhalten:

- ursprüngliches Atom,
- normalisiertes Atom,
- verwendete Annahmen,
- Multiplikationen oder Divisionen,
- Herkunft.

## 7.2 Polynome

- Terme ausmultiplizieren oder kanonisch sammeln.
- Gemeinsame sicher positive Faktoren dürfen entfernt werden.
- Bei Faktoren unbekannten Vorzeichens ist eine Falltrennung nötig.
- Faktorisierte und expandierte Form werden beide erhalten:
  - expandiert für Koeffizientenvergleich,
  - faktorisiert für Nullstellen und Vorzeichenwechsel.

## 7.3 Rationale Bedingungen

Für

\[
\frac{N}{D}>0
\]

gelten drei getrennte Aspekte:

\[
N\cdot D>0,
\qquad
D\neq0,
\]

oder eine explizite Vorzeichentabelle.

Unsicheres Kreuzmultiplizieren ist verboten.

Ist durch Annahmen bewiesen, dass \(D>0\), darf sicher zu

\[
N>0
\]

beziehungsweise zur kreuzmultiplizierten Form übergegangen werden. Die ursprüngliche Nennerbedingung bleibt trotzdem in der Provenienz.

## 7.4 Vereinfachung

Zulässig:

- identische Bedingungen zusammenfassen,
- stärkere lineare Bedingungen erkennen,
- offensichtlich wahre Bedingungen entfernen,
- direkte Widersprüche erkennen,
- leere Zweige eliminieren.

Beispiel:

\[
a>-5\land a>-\frac65
\]

reduziert sich zu

\[
a>-\frac65.
\]

Keine aggressive symbolische Vereinfachung, deren Äquivalenz nicht sicher nachgewiesen ist.

---

# 8. Lösungsumfang

## 8.1 Ein Parameter: vollständig

Für polynomiale und rationale Bedingungen:

1. Nullstellen aller relevanten Zähler und Nenner bestimmen.
2. Reelle kritische Punkte sortieren.
3. Reelle Achse in Zellen zerlegen.
4. Vorzeichen exakt oder über sichere Testpunkte feststellen.
5. strikte und nichtstrikte Randwerte anwenden.
6. Ausschlusspunkte entfernen.
7. Zweige vereinigen.

Dies deckt die klausurrelevanten einparametrigen Bereiche vollständig ab.

## 8.2 Zwei Parameter: bewusst beschränkt

Vollständig unterstützt werden Systeme, die auf folgende Formen gebracht werden können:

\[
x\;\square\;c,
\]

\[
y\;\square\;f(x),
\]

\[
f_1(x)\;\square\;y\;\square\;f_2(x),
\]

mit einfachen linearen, quadratischen oder sicher rationalen Grenzfunktionen.

Dies umfasst die Klausurgebiete zwischen Geraden und Parabeln.

Für die Gebietserkennung:

1. Randkurven bestimmen.
2. relevante Schnittpunkte exakt berechnen.
3. Grundachse in Abschnitte zerlegen.
4. Reihenfolge der Grenzfunktionen feststellen.
5. Zellen erzeugen.
6. pro Zelle einen Testpunkt auswählen.
7. alle Originalbedingungen am Testpunkt prüfen.
8. nur dann einen zusammenhängenden Bereich behaupten, wenn keine Randkurve die Zelle schneidet.

Ein zufälliger Testpunkt allein ist kein Beweis für ein gesamtes Gebiet.

## 8.3 Teilweise unterstützte 2D-Fälle

Bei nicht isolierbaren oder komplizierten impliziten Kurven darf der Kern liefern:

- normalisiertes exaktes Ungleichungssystem,
- gefundene Randkurven,
- einzelne Schnittpunkte,
- Status `PARTIALLY_SOLVED_SAFE`.

Er darf keine vollständige Gebietszerlegung behaupten.

---

# 9. Ergebnisvertrag

## 9.1 Gemeinsame Statuswerte

- `SOLVED_EXACT`
- `EMPTY`
- `PARTIALLY_SOLVED_SAFE`
- `UNSUPPORTED`
- `INVALID_INPUT`
- `INCONSISTENT_ASSUMPTIONS`
- `INDETERMINATE`

Zusätzlich muss ein Vollständigkeitsmerkmal ausgegeben werden:

- vollständig,
- teilweise,
- keine Lösungsauswertung.

## 9.2 Einparametriges Ergebnis

- exakte Intervallvereinigung,
- isolierte Punkte,
- offene/geschlossene Randpunkte,
- Ausschlusspunkte,
- numerische Randwerte,
- Testpunkte je Intervall,
- Wahrheitswerte aller Eingabebedingungen,
- verwendete Annahmen,
- Provenienz.

## 9.3 Zweiparametriges Ergebnis

- exaktes reduziertes Bedingungssystem,
- Randkurven,
- Randstatus:
  - enthalten,
  - ausgeschlossen,
  - nur teilweise enthalten,
- exakte Schnittpunkte,
- numerische Schnittpunkte,
- zertifizierte Gebietszellen,
- ein Testpunkt je Zelle,
- Wahrheitsvektor der Bedingungen,
- nicht aufgelöste Restbedingungen,
- Vollständigkeitsstatus.

## 9.4 Leere Menge

Eine leere Menge ist ein reguläres mathematisches Ergebnis:

\[
\boxed{S=\varnothing}.
\]

Sie ist kein Solverfehler.

Die Ausgabe muss die widersprüchlichen Bedingungen nennen.

---

# 10. Numerische Kontrollen

Exakte Ergebnisse sind maßgeblich. Numerik dient nur der Kontrolle und Darstellung.

Pflichtkontrollen:

- Residuum bei Randgleichungen,
- Auswertung jedes Randpunkts in den Originalbedingungen,
- mindestens ein innerer Testpunkt pro Intervall oder Gebiet,
- nach Möglichkeit ein äußerer Gegenpunkt,
- Abstand eines Testpunkts von Nennernullstellen,
- Vergleich normalisierte gegen ursprüngliche Bedingung,
- Warnung bei fast zusammenfallenden Randpunkten.

Für stabilitätsspezifische Kontrollen kann der erzeugende Fachblock die Testpunkte weiterverwenden:

- Hurwitz: Pole beziehungsweise Determinanten numerisch kontrollieren,
- Nyquist: \(1+G_0(j\omega)=0\) am kritischen Rand prüfen,
- Wurzelortskurve: Pol- und Zeitforderungen prüfen.

Diese fachlichen Prüfungen sind nicht Teil des gemeinsamen Kerns.

---

# 11. Referenzfälle

## 11.1 Hurwitz SS2025

Gegeben:

\[
p(s)=
s^3+(9+a)s^2+(20+9a)s+(20a+9K).
\]

Der Hurwitz-Block erzeugt:

\[
a>-\frac{20}{9},
\]

\[
K>-\frac{20}{9}a,
\]

\[
K<a^2+9a+20.
\]

Der gemeinsame Kern liefert:

\[
\boxed{
S=
\left\{
(a,K)\in\mathbb R^2
\;\middle|\;
a>-\frac{20}{9},
\;
-\frac{20}{9}a<K<a^2+9a+20
\right\}.
}
\]

Randgerade und Randparabel sind ausgeschlossen. Die Klausur verwendet genau dieses kubische Polynom und diese zweiparametrige Struktur. fileciteturn6file0 fileciteturn6file2

**Aufgabenteilung**

- Übertragungsfunktionsblock: Nenner übernehmen und ausmultiplizieren.
- Hurwitz-Block: Bedingungen erzeugen.
- gemeinsamer Kern: 2D-Menge reduzieren und strukturieren.

---

## 11.2 Hurwitz WS25/26

Offizielle Lösung nach Kürzung:

\[
p_{\mathrm{red}}(s)
=
s^3+(8+2a)s^2+(15+16a)s+(30a+8K).
\]

Hurwitz-Bedingungen:

\[
a>-\frac{15}{16},
\]

\[
K>-\frac{15}{4}a,
\]

\[
K<4a^2+16a+15.
\]

Gemeinsames Ergebnis:

\[
\boxed{
S_{\mathrm{red}}
=
\left\{
(a,K)\in\mathbb R^2
\;\middle|\;
a>-\frac{15}{16},
\;
-\frac{15}{4}a<K<4a^2+16a+15
\right\}.
}
\]

Die ursprüngliche Übertragungsfunktion enthält zusätzlich einen gemeinsamen Faktor \((s+K)\). Daher muss der Vertrag parallel erhalten:

\[
p_{\mathrm{raw}}(s)
=
(s+K)p_{\mathrm{red}}(s).
\]

Die offizielle Lösung analysiert den reduzierten Nenner. Für interne asymptotische Stabilität darf der entfernte Faktor nicht stillschweigend ignoriert werden. fileciteturn7file8 fileciteturn7file11

**Aufgabenteilung**

- Transferfunktionsblock: Roh- und reduzierte Form sowie Kürzungsprotokoll.
- Orchestrierung: Analysebedeutung auswählen.
- Hurwitz-Block: Bedingungen für das ausgewählte Polynom.
- gemeinsamer Kern: 2D-Menge.

---

## 11.3 Stabilitätsgebiet SS2025

Gegeben sind bereits:

\[
a>-5,
\qquad
a>-\frac65,
\]

\[
K>-6a,
\qquad
K<5a^2+25a+30.
\]

Der gemeinsame Kern entfernt die schwächere Bedingung \(a>-5\) und liefert:

\[
\boxed{
a>-\frac65,
\qquad
-6a<K<5a^2+25a+30.
}
\]

Beide Grenzkurven sind offen. Das grafische Zeichnen kann ein nachgelagerter Plotblock übernehmen. fileciteturn7file5 fileciteturn7file6

**Aufgabenteilung**

- Hurwitz-Block: keine neue Rechnung; Bedingungen liegen bereits vor.
- gemeinsamer Kern: Redundanz, Gebiet, Randkurven, Testpunkte.
- Plotblock: Darstellung.

---

## 11.4 Nyquist-Verstärkungsbereich WS25/26

Offener Kreis:

\[
G_0(s,K_R)
=
\frac{3K_R}{9s^3+27s^2+19s+1}.
\]

Nyquist liefert den kritischen oberen Wert

\[
K_R=\frac{56}{3}.
\]

Das geschlossene Polynom lautet:

\[
9s^3+27s^2+19s+1+3K_R.
\]

Unter vollständiger mathematischer Auswertung entsteht:

\[
\boxed{
-\frac13<K_R<\frac{56}{3}.
}
\]

Bei zusätzlicher Annahme \(K_R>0\):

\[
\boxed{
0<K_R<\frac{56}{3}.
}
\]

Die offizielle Musterlösung behandelt nur die positive obere Grenze; eine ausdrückliche positive Parameterannahme ist in der Quellenlage nicht eindeutig. fileciteturn5file0 fileciteturn5file13

**Aufgabenteilung**

- Nyquist-Block: kritische Gleichung und kritischer Verstärkungswert.
- optional Hurwitz-Gegenprüfung: untere und obere Bedingungen.
- gemeinsamer Kern: Annahmen schneiden und exaktes Intervall ausgeben.

---

## 11.5 Wurzelortskurven-Parameterfall

Für den korrigierten WS25/26-Fall:

\[
s_{1,2}
=
-\frac12
\pm j\sqrt{k-\frac14}.
\]

Der Wurzelortskurven-/Zeitforderungsblock erzeugt:

\[
k\ge
\frac14+\left(\frac{\pi}{7}\right)^2,
\]

\[
k\le
\frac14+
\left(\frac{\pi}{2\ln20}\right)^2.
\]

Der gemeinsame Kern liefert:

\[
\boxed{
k\in
\left[
\frac14+\left(\frac{\pi}{7}\right)^2,
\;
\frac14+\left(\frac{\pi}{2\ln20}\right)^2
\right].
}
\]

Numerisch:

\[
\boxed{
k\in[0.4514,\;0.5249].
}
\]

Die Grenzen sind geschlossen, weil die Leistungsanforderungen mit \(\le\) formuliert sind. Die offizielle Musterlösung enthält bei der Überschwingzeit eine umgekehrte Ungleichungsrichtung. fileciteturn8file19

**Aufgabenteilung**

- Wurzelortskurvenblock: Pole und Zeitbedingungen herleiten.
- gemeinsamer Kern: Intervallschnitt.
- Tabellenblock: bei Schrittweite \(0.1\) nur \(k=0.5\) auswählen.

---

## 11.6 Gradabfall

Aus einer Tutoriumsaufgabenfamilie:

\[
p(s;k_p)
=
k_ps^2+s-10-\frac{k_p}{4}.
\]

Gradfälle:

\[
k_p\neq0
\Rightarrow
\deg p=2,
\]

\[
k_p=0
\Rightarrow
p(s)=s-10,
\quad
\deg p=1.
\]

Der gemeinsame Kern muss beide Fälle ausgeben. Er darf nicht vorab durch \(k_p\) dividieren.

**Aufgabenteilung**

- Polynomkern: Gradfälle erzeugen.
- Hurwitz-Block: jeden Fall mit dem passenden Grad analysieren.
- Bedingungskern: resultierende Mengen wieder vereinigen.

---

## 11.7 Nennerausschluss

Aus dem PI-Regler-Fall:

\[
T_N>
\frac{K_R}{1+3K_R},
\qquad
K_R>0,
\qquad
T_N>0.
\]

Explizit gilt:

\[
1+3K_R\neq0.
\]

Aus \(K_R>0\) folgt sicher

\[
1+3K_R>0.
\]

Daher darf der gemeinsame Kern äquivalent schreiben:

\[
\boxed{
T_N(1+3K_R)-K_R>0.
}
\]

Die Nennerbedingung bleibt im Protokoll, auch wenn sie durch \(K_R>0\) redundant wird. fileciteturn1file9

Ohne Vorzeichenannahme müsste um

\[
K_R=-\frac13
\]

in getrennte Fälle zerlegt werden.

---

## 11.8 Leere Lösungsmenge

Für dasselbe Polynom aus Abschnitt 11.6 erzeugt eine quadratische Hurwitz-Auswertung unter der Annahme \(k_p>0\):

\[
k_p>0,
\]

\[
-10-\frac{k_p}{4}>0
\Longrightarrow
k_p<-40.
\]

Damit:

\[
\boxed{
\{k_p\in\mathbb R\mid k_p>0\land k_p<-40\}
=
\varnothing.
}
\]

Der gemeinsame Kern meldet die leere Menge und nennt die widersprüchlichen Bedingungen. fileciteturn1file19

---

# 12. Sichere Fehlerausgabe

## 12.1 Polynomfehler

- falsche Hauptvariable,
- mehr als zwei freie Entscheidungsparameter,
- Nullpolynom,
- unbekannte Koeffizientensymbole,
- fehlende Polynomrolle,
- unklare Roh-/Reduziert-Zuordnung,
- Kürzung ohne Provenienz,
- nicht behandelter Gradabfall,
- Division durch möglicherweise null werdenden Faktor.

## 12.2 Bedingungsfehler

- nichtreelle Parameterdomäne,
- fehlender Nennerausschluss,
- nicht unterstützte transzendente Ungleichung,
- allgemeine implizite 2D-Geometrie,
- zu große Fallverzweigung,
- widersprüchliche Annahmen,
- exakte Randpunkte nicht bestimmbar,
- numerische Kontrolle widerspricht der behaupteten Normalisierung.

## 12.3 Verhalten bei Fehlern

Der Kern gibt immer zurück:

- verständlichen Fehlercode,
- betroffenen Ausdruck,
- erhaltene Originalbedingungen,
- bis dahin sichere Normalisierung,
- fehlende Voraussetzung,
- Vollständigkeitsstatus.

Er darf niemals:

- eine numerische Näherung als exakte Lösung ausgeben,
- einen nicht gelösten 2D-Fall als vollständiges Gebiet darstellen,
- Nennerausschlüsse vergessen,
- eine Bedingung stillschweigend streichen,
- eine Fallgrenze willkürlich einer Seite zuordnen.

---

# 13. LaTeX-Ausgabe

## 13.1 Charakteristisches Polynom

```latex
\[
p(s)
=
a_ns^n+a_{n-1}s^{n-1}+\dots+a_0
\]
```

Bei Gradfall:

```latex
\[
k\neq0:\quad \deg p=2,
\qquad
k=0:\quad p(s)=s-10,\;\deg p=1.
\]
```

## 13.2 Einparametrige Menge

```latex
\[
K_R\in\left(-\frac13,\frac{56}{3}\right).
\]
```

## 13.3 Zweiparametrige Menge

```latex
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
```

## 13.4 Rationaler Ausschluss

```latex
\[
1+3K_R\neq0.
\]
```

## 13.5 Leere Menge

```latex
\[
K>0\land K<-40
\quad\Longrightarrow\quad
S=\varnothing.
\]
```

Randkurven müssen zusätzlich als „enthalten“ oder „nicht enthalten“ gekennzeichnet werden. Eine gestrichelte Darstellung für strikte Grenzen ist nur eine Darstellungsinformation des Plotblocks.

---

# 14. Nicht unterstützte Fälle

Nicht im MVP:

- mehr als zwei freie Parameter,
- allgemeine Quantorenelimination,
- vollständige zylindrische algebraische Zerlegung,
- beliebige implizite algebraische Kurvenanordnungen,
- beliebige transzendente Ungleichungen,
- automatische Umformung komplexer Zeitbereichsformeln,
- allgemeine Optimierung,
- interaktive 3D-Gebiete,
- allgemeine Beweiserzeugung,
- automatische Regelkreisbildung,
- Hurwitz-, Nyquist- oder Wurzelortskurvenlogik,
- freie Texteingabe als mathematischer Parser,
- vollständige Fallanalyse beliebig hoher Polynomgrade.

---

# 15. Minimale wiederverwendbare Schnittstelle

Es reichen zwei Operationen.

## A. Polynomkanonisierung

\[
\boxed{
\operatorname{canonicalize\_characteristic\_polynomial}
:
\text{Polynomvertrag}
\rightarrow
\text{kanonischer Polynomvertrag mit Gradfällen}
}
\]

Ergebnis:

- geordnete Koeffizienten,
- Rollen- und Provenienzerhaltung,
- Gradfälle,
- Skalierungsbedingungen,
- Kürzungsinformationen,
- Diagnosen.

## B. Parameterbereich lösen

\[
\boxed{
\operatorname{solve\_parameter\_conditions}
:
\text{Bedingungsproblem}
\rightarrow
\text{exakte Mengenlösung}
}
\]

Ergebnis:

- 1D-Intervallvereinigung oder
- beschränkte 2D-Bedingungsmenge,
- Grenzen,
- Testpunkte,
- numerische Kontrollen,
- Vollständigkeitsstatus.

Keine fachblockspezifischen Methoden wie `solve_hurwitz` oder `solve_nyquist_gain` gehören in diesen Kern.

---

# 16. Codex-Aufwand

| Teil | Aufwand | Risiko |
|---|---:|---|
| Polynomvertrag und Provenienz | niedrig bis mittel | Roh-/Reduziert-Semantik |
| Grad- und Skalierungsfälle | mittel | parameterabhängige Leitkoeffizienten |
| exakter 1D-Solver | mittel | rationale Vorzeichenfälle |
| eingeschränkter 2D-Solver | mittel bis hoch | korrekte Gebietszellen |
| Testpunkte und Verifikation | mittel | keine Stichprobe als Beweis missbrauchen |
| LaTeX und Diagnoseausgabe | niedrig bis mittel | Offenheit der Grenzen erhalten |
| Regressionstests | mittel | Quellenfehler bewusst abbilden |

Gesamtbewertung:

\[
\boxed{\text{mittlerer Codex-Aufwand bei sehr hoher Wiederverwendung}}
\]

Sinnvolle Zerlegung in vier bis sechs klar begrenzte spätere Programmierinkremente:

1. Verträge und Kanonisierung,
2. exakte 1D-Bedingungen,
3. rationale Bedingungen und Ausschlüsse,
4. eingeschränkte 2D-Gebiete,
5. Ergebnis-/LaTeX-Schicht,
6. Regressionstests der Referenzfälle.

Der gefährlichste Teil ist nicht das charakteristische Polynom, sondern der Versuch, aus dem 2D-Kern schleichend ein allgemeines CAS zu machen. Das muss hart verhindert werden.

---

# 17. Verbindliche MVP-Entscheidungen

1. Höchstens zwei freie reelle Parameter.
2. Charakteristische Polynome werden ausschließlich bereits erzeugt übernommen.
3. Rohes internes Polynom und reduzierter E/A-Nenner bleiben getrennt.
4. Gradabfälle sind echte Fallzweige.
5. Nennerausschlüsse sind eigenständige Bedingungen.
6. Asymptotische Stabilitätsgrenzen sind offen.
7. Leistungsgrenzen behalten ihre ursprüngliche Striktheit.
8. 1D-Bedingungen werden vollständig exakt gelöst.
9. 2D wird auf graphisch auflösbare Geraden-, Parabel- und einfache rationale Grenzen beschränkt.
10. Nicht vollständig gelöste Fälle werden offen als teilweise gelöst gekennzeichnet.
11. Exakte Mengen sind maßgeblich; Dezimalwerte dienen nur der Kontrolle.
12. Der gemeinsame Kern erzeugt keine fachlichen Stabilitätsbedingungen.

---

--- NOTEBOOKLM-PROMPT ---

Prüfe folgende Fragen ausschließlich anhand der hochgeladenen offiziellen Regelungstechnik-Quellen:

1. Klausur WS 2025/26, Aufgabe 4b:  
   Die gegebene geschlossene Übertragungsfunktion besitzt vor der Kürzung einen gemeinsamen Faktor \((s+K)\). Soll die verlangte „asymptotische Stabilität“ nach den offiziellen Vorlesungskonventionen anhand
   - des rohen geschlossenen charakteristischen Polynoms einschließlich \((s+K)\) oder
   - des gekürzten E/A-Nenners
   beurteilt werden?

2. Klausur WS 2025/26, Aufgabe 3e:  
   Wird für den Verstärkungsparameter \(K_R\) ausdrücklich oder stillschweigend \(K_R>0\) vorausgesetzt? Ist der vollständige mathematische Stabilitätsbereich
   \[
   -\frac13<K_R<\frac{56}{3}
   \]
   oder nur
   \[
   0<K_R<\frac{56}{3}
   \]
   als klausurgemäß anzusehen?

3. Klausur WS 2025/26, Wurzelortskurvenaufgabe:  
   Prüfe die Ungleichungsrichtung aus
   \[
   t_{\max}
   =
   \frac{\pi}{\sqrt{k-1/4}}
   \le7
   \]
   und bestätige oder widerlege den Bereich
   \[
   \frac14+\left(\frac{\pi}{7}\right)^2
   \le k\le
   \frac14+\left(\frac{\pi}{2\ln20}\right)^2.
   \]

Antworte kurz und eindeutig. Belege jede wesentliche Aussage mit kurzem direkten Zitat, Dokumentname und genauer Seite oder Aufgabe. Zeige verbleibende Widersprüche ausdrücklich und erfinde keine Annahmen.

--- ENDE ---
