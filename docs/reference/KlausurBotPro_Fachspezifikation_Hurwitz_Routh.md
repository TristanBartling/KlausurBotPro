# KlausurBotPro – Fachspezifikation

## Hurwitz-Kriterium, Routh-Schema und Stabilitätsparameterbereiche

**Status:** Fachspezifikation, keine Implementierung, kein Codex-Prompt  
**Quellenstand:** Sommersemester 2026  
**Ziel:** klausurtaugliche, symbolisch exakte Bearbeitung zeitaufwendiger Stabilitätsaufgaben

---

## 1. Quellenbasis und Kennzeichnung

### Quellenhierarchie

1. `skript.pdf`
2. `Regelungstechnik_Übung_Aufg-u-Lösungen.pdf`
3. `Regelungstechnik_Tutorium_komplett.pdf` und `RT-Tutorien-Mitschrift.pdf`
4. `RT_Klausur_SS2025-komplett.pdf` und `RT-Klausur_WS_25_26-komplett.pdf`
5. `RT1_Rechenwege_Master(12).md` nur ergänzend

### Kennzeichnung

- **[OFFIZIELL]**: direkt aus Skript, offizieller Übung, offiziellem Tutorium oder Klausur.
- **[HERLEITUNG]**: mathematisch aus offiziellen Angaben hergeleitet.
- **[KORREKTUR]**: offizielle Lösung enthält eine unstrenge Randbedingung oder einen Fehler; die Korrektur folgt dem höherrangigen Skript und einer direkten Polprüfung.
- **[ENTWICKLUNGSREFERENZ]**: nur im Rechenwege-Master genannt, nicht in den offiziellen Primärquellen ausgeführt.
- **[SYNTHETISCHER TEST]**: klar aus einem offiziellen Polynom abgeleiteter Softwaretest, aber keine originale Aufgabe.

---

## 2. Klausurrelevanz und Punktegewicht

### Sommersemester 2025

1. Aufgabe 4b: **direkte Hurwitz-Auswertung** eines zweiparametrigen kubischen Nennerpolynoms, **10 Punkte**.  
   Quelle: `RT_Klausur_SS2025-komplett.pdf`, Aufgabenbogen PDF-S. 9; Lösung PDF-S. 66.
2. Aufgabe 4c: **nachgelagerte Darstellung** eines bereits ermittelten Hurwitz-Bedingungssystems in der \((a,K)\)-Ebene, **7 Punkte**. Hier wird Hurwitz nicht erneut berechnet; die Teilaufgabe konsumiert nur die Bedingungen.  
   Quelle: Aufgabenbogen PDF-S. 9; Lösung PDF-S. 67–68.

**Kernmodul Hurwitz:** 10 direkte Punkte.  
**Gesamte Stabilitätspipeline einschließlich Gebietsvisualisierung:** 17 Punkte.

**Routh:** kein direkter Klausurteil gefunden.

### Wintersemester 2025/2026

1. Aufgabe 4b: zweiparametriger Hurwitz-Stabilitätsbereich für ein kubisches Polynom, **10 Punkte**.  
   Quelle: `RT-Klausur_WS_25_26-komplett.pdf`, Aufgabenbogen PDF-S. 11; Lösung PDF-S. 69–70.
2. Aufgabe 4a II: Theorieaussagen zum Hurwitz-Kriterium; laut Lösung zwei korrekte Aussagen und damit **2 Punkte** innerhalb des Multiple-Choice-Blocks.  
   Quelle: Lösungsbogen PDF-S. 35 bzw. Aufgabenblatt „Seite 22“.

**Gesamt:** bis zu 12 ausgewiesene Punkte direkt mit Hurwitz verbunden.

**Routh:** kein direkter Klausurteil gefunden.

### Bewertung

| Verfahren | Klausurauftreten | Typische Punkte | Nutzen |
|---|---:|---:|---|
| Hurwitz, kubisch, zwei Parameter | in beiden Klausuren | 10 | sehr hoch |
| Stabilitätsgebiet aus Ungleichungen | SS2025 | 7 | hoch |
| Hurwitz-Theorie | WS25/26 | 2 | mittel |
| Routh-Standardschema | nur Übung/Tutorium | keine direkte Klausurfundstelle | mittel bis hoch als Alternativ- und Prüfverfahren |
| Routh-Sonderfälle | keine offizielle Klausurfundstelle | unbekannt | gering für erstes MVP |

**Schlussfolgerung:** Der wirtschaftlich wichtigste Kern ist nicht ein allgemeiner Routh-Sonderfallsolver, sondern die fehlerfreie symbolische Ermittlung von Stabilitätsbedingungen kubischer und quartischer Polynome, einschließlich zweiparametriger Bereiche und strenger Randklassifikation.

---

## 2A. Querschnitts- und Vorstufenanalyse

### 2A.1 Abgrenzung der drei Rollen

Für jede Fundstelle werden drei Rollen getrennt:

1. **Direkte Stabilitätsaufgabe:** Hurwitz oder Routh ist ausdrücklich verlangt.
2. **Notwendiger Stabilitäts-Zwischenschritt:** Gesucht ist ein Stabilitätsbereich oder eine Stabilitätsaussage, ohne dass das Verfahren zwingend genannt wird; Hurwitz/Routh kann auf das zuvor gebildete Polynom angewendet werden.
3. **Vorgelagerte Rechenfunktion:** DGL-, Laplace-, Übertragungsfunktions-, Regler- oder Regelkreisrechnung erzeugt erst das charakteristische Polynom. Diese Logik gehört in einen anderen Programmblock.

Eine Fundstelle kann gleichzeitig Rolle 1 und Rolle 3 enthalten: Das Stabilitätsverfahren ist direkt verlangt, aber vorher muss der geschlossene Kreis oder das Nennerpolynom gebildet werden.

### 2A.2 Quellenübergreifende Fundstellenmatrix

| Fundstelle | Rolle Hurwitz/Routh | Vorgelagerte Rechnung | Übergabe an Stabilitätsmodul | Konsequenz |
|---|---|---|---|---|
| `skript.pdf`, Aufgaben 5.13 → 5.19 → 5.22, gedruckte S. 108–115 | 5.19 Hurwitz direkt; 5.22 Routh direkt | Aufgabe 5.13 bildet aus Strecke und P-Glied die geschlossene Übertragungsfunktion | quadratisches charakteristisches Polynom mit Annahmen \(\omega_0>0\), Parameter \(\zeta,K_{P2}\) | klarer mehrstufiger Referenzworkflow; Regelkreisbildung bleibt außerhalb des Moduls |
| `Regelungstechnik_Übung_Aufg-u-Lösungen.pdf`, Übung 09 Aufgabe 3, PDF-S. 116–117 | Hurwitz und Routh direkt verlangt | aus \(G_S(s)\) und \(G_R(s)=K_P\) wird zuerst \(G_W(s)\), danach \(N(s)\) gebildet | \(N(s)=s^3+4s^2+5s+K_P\), Annahmen und gesuchter Parameter | wichtigste Einparameter-Integrationsprüfung |
| `Regelungstechnik_Tutorium_komplett.pdf`, Tutorium 09 Aufgabe 3a–d, PDF-S. 57–58 | Hurwitz direkt; Routh als Prüfung direkt | für vier Regler-/Streckenkombinationen: geschlossenen Kreis bilden, ausmultiplizieren, Parameter in Koeffizienten übernehmen | kanonische Polynome Grad 3 bzw. 4 plus \(K_R,T_N,D,\omega_0,T_1,T_I\)-Annahmen | breiteste offizielle Integrationsfamilie; Vorstufen nicht im Stabilitätskern duplizieren |
| `RT_Klausur_SS2025-komplett.pdf`, Aufgabe 4b, Aufgabenbogen S. 9 | Hurwitz direkt, 10 Punkte | gegebene geschlossene Übertragungsfunktion: Nenner übernehmen und faktorisierte Form ausmultiplizieren | kubisches Nennerpolynom \(s^3+(9+a)s^2+(20+9a)s+(20a+9K)\) | kein Regelkreisaufbau nötig; nur Nennerextraktion und Polynomkanonisierung upstream |
| `RT_Klausur_SS2025-komplett.pdf`, Aufgabe 4c, Aufgabenbogen S. 9 | kein neuer Hurwitz-/Routh-Lauf | bereits gegebene Ungleichungen grafisch schneiden | Bedingungssystem, nicht Polynom | nachgelagerter Visualisierungsblock; nicht als Hurwitz-Rechenpunkt zählen |
| `RT-Klausur_WS_25_26-komplett.pdf`, Aufgabe 4b, Aufgabenbogen S. 11 | Hurwitz direkt, 10 Punkte | gegebene geschlossene Übertragungsfunktion enthält einen gemeinsamen Faktor \((s+K)\); offizielle Lösung kürzt vor der Nennerauswertung | **reduziertes** kubisches Nennerpolynom plus Kürzungsprotokoll | kritischer Vertragsfall: E/A-Nenner und rohes internes charakteristisches Polynom dürfen nicht verwechselt werden |
| `Regelungstechnik_Tutorium_komplett.pdf`, Tutorium 09 Aufgabe 2h | Stabilitätsparameterbereich verlangt, Verfahren nicht genannt | aus vorigem System und negativer P-Rückführung entsteht ein parameterabhängiges Polynom | kanonisches Polynom und Nebenbedingungen | Rolle 2; zeigt, dass das Modul auch unbenannte Stabilitätsfragen bedienen soll. Wegen schlecht lesbarer Formel kein primärer Regressionstest |
| `RT_Klausur_SS2025-komplett.pdf`, Aufgabe 1d, Aufgabenbogen S. 4 | kein Hurwitz/Routh in derselben Teilaufgabe | DGL → Laplace → Übertragungsfunktion | Zähler/Nenner an Übertragungsfunktionsblock; bei späterer Stabilitätsfrage nur kanonisches Nennerpolynom weitergeben | reine Vorstufe; liefert keine zusätzlichen Hurwitz-Punkte |
| `skript.pdf`, Bemerkung 5.16, gedruckte S. 109 | allgemeine fachliche Schnittstelle | charakteristisches Polynom aus \(\det(\lambda I-A)=0\) oder aus dem Nennerpolynom | Zustands- oder Frequenzbereichspolynom mit expliziter Rollenkennzeichnung | Zustandsraumblock ist ein weiterer zulässiger Produzent, auch wenn er nicht Hauptfokus dieses Programmblocks ist |

### 2A.3 Ergebnis der Querschnittsanalyse

Die eigentliche Klausuraufgabe beginnt häufig **nicht** beim bereits sortierten Polynom. Besonders Übung 09 und Tutorium 09 verlangen die gesamte Kette

\[
G_S,G_R
\longrightarrow
G_W
\longrightarrow
N_{\mathrm{char}}(s)
\longrightarrow
\text{Hurwitz/Routh}
\longrightarrow
\text{Parameterbereich}.
\]

Das erhöht den Nutzen einer durchgängigen Orchestrierung, rechtfertigt aber **keine Duplizierung** der vorgelagerten Mathematik im Hurwitz/Routh-Modul.

### 2A.4 Verbindliche Modulgrenze

Das Hurwitz/Routh-Modul besitzt genau einen fachlichen Kerneingang:

\[
\boxed{
\text{kanonisches reelles charakteristisches Polynom}
+
\text{Parameterannahmen}
+
\text{Analyseziel}
}
\]

Es übernimmt **nicht**:

- Laplace-Transformation einer DGL;
- Bestimmung einer Übertragungsfunktion;
- Blockschaltbild- oder Regelkreisreduktion;
- Bildung von \(1+L(s)=0\);
- Entscheidung über das Rückkopplungsvorzeichen;
- Zusammenbau von Strecke und Regler;
- rationale Polynomkürzung zwischen Zähler und Nenner.

Diese Funktionen müssen von den zuständigen Programmblöcken ausgeführt werden. Das Stabilitätsmodul darf deren Ergebnis validieren, aber nicht neu herleiten.

### 2A.5 Eingabe- und Übergabevertrag

Minimaler Übergabegegenstand:

```text
CharacteristicPolynomialInput
- polynomial_expr: exakter Ausdruck in s oder lambda
- coefficients_desc: [a_n, ..., a_0]
- variable: s | lambda
- degree
- parameters: Liste symbolischer Parameter
- assumptions: strikte/nichtstrikte Parameterannahmen
- requested_parameters: gesuchte Stabilitätsparameter
- polynomial_role:
    state_characteristic
    raw_closed_loop_characteristic
    reduced_transfer_denominator
- analysis_target:
    state_asymptotic
    internal_closed_loop_asymptotic
    external_BIBO
- excluded_parameter_sets: Nennernullen, Gradabfälle, unzulässige Kürzungsfälle
- provenance: Dokument/Aufgabe oder erzeugender Programmblock
- cancellation_report: optional, nur bei reduced_transfer_denominator
```

Verbindliche Anforderungen an den Produzenten:

1. Polynom exakt, ausmultipliziert und nach fallenden Potenzen sortiert liefern.
2. Fehlende Potenzen als Nullkoeffizienten kennzeichnen.
3. Alle beim Herleiten entstandenen Definitionsbedingungen weitergeben.
4. Bei Parameterkürzungen die ausgeschlossenen Parameterwerte erhalten.
5. Bei einer gekürzten Übertragungsfunktion sowohl den ursprünglichen als auch den gekürzten Faktorstatus dokumentieren.
6. Keine Dezimalapproximation erzwingen, wenn exakte rationale oder symbolische Koeffizienten vorliegen.

### 2A.6 Verträge der vorgelagerten Blöcke

#### DGL-/Laplace-Block

Liefert eine rationale Übertragungsfunktion oder unmittelbar deren Nennerpolynom sowie Anfangsbedingungs- und Vorzeichenprovenienz. Das Stabilitätsmodul sieht die DGL nicht.

#### Regelkreis-/Blockrechnungsblock

Liefert das rohe charakteristische Polynom des geschlossenen Kreises und dokumentiert Rückkopplungsart, Schleifenstruktur und verwendete Regler-/Streckenparameter. Das Stabilitätsmodul bildet \(1+L(s)=0\) nicht selbst.

#### Übertragungsfunktions-/Kürzungsblock

Liefert für E/A-Stabilität den vollständig reduzierten Nenner und ein Kürzungsprotokoll. Bei möglicher interner Instabilität muss zusätzlich das rohe charakteristische Polynom übergeben werden.

#### Polynom-Kanonisierungsblock

Liefert Koeffizientenliste, Grad, Parameter und ausgeschlossene Sondermengen. Nur Skalierungsnormierung und Stabilitätsprüfung bleiben im Hurwitz/Routh-Modul.

### 2A.7 Harte Ablehnungsfälle der Kern-API

Der Stabilitätskern muss mit einem klaren Vertragsfehler abbrechen, wenn direkt übergeben werden:

- eine DGL;
- ein Blockschaltbild;
- getrennte \(G_R,G_S,H\)-Objekte;
- ein offener Kreis \(L(s)\) ohne bereits gebildetes charakteristisches Polynom;
- eine ungekürzte Übertragungsfunktion ohne angegebenes Analyseziel;
- ein Polynom ohne Parameterannahmen, obwohl sein Grad oder Leitkoeffizient parameterabhängig ist.

Der übergeordnete GUI-Workflow darf solche Eingaben annehmen, muss sie aber zuerst an den zuständigen Vorstufenblock routen.

---

## 3. Tatsächlich verwendete Polynomgrade

| Grad | Fundstelle | Typ |
|---:|---|---|
| 2 | `skript.pdf`, Kap. 5.3–5.4, Feder-Masse-Dämpfer-Beispiel | Hurwitz und Routh ohne schwierige Parameterauflösung |
| 3 | offizielle Übung 09; Tutorium 09 Aufgaben 3a–c; beide Klausuren | dominanter klausurrelevanter Grad |
| 4 | Tutorium 09 Aufgabe 3d | mehrere Zeitkonstanten, stärkere Determinantenbedingung |
| >4 | keine relevante offizielle Aufgabe gefunden | nicht MVP-relevant |

### Konsequenz für KlausurBotPro

Das erste produktive Modul muss Grad 2 bis 4 vollständig und symbolisch exakt beherrschen. Allgemeine Grade sind technisch möglich, bringen aber zunächst wenig zusätzliche Klausurabdeckung.

---

## 4. Grundkonventionen

### 4.1 Charakteristisches Polynom

Verwendet wird die Skriptnotation

\[
N(s)=a_ns^n+a_{n-1}s^{n-1}+\dots+a_1s+a_0.
\]

Die Koeffizientenliste der GUI lautet absteigend:

\[
[a_n,a_{n-1},\dots,a_1,a_0].
\]

Fehlende Potenzen müssen explizit mit Koeffizient null ergänzt werden.

### 4.2 Normierung

Vor der Prüfung:

1. Null-Leitkoeffizienten entfernen und Grad neu bestimmen.
2. Falls der Leitkoeffizient unter allen zulässigen Annahmen negativ ist, das gesamte Polynom mit \(-1\) multiplizieren.
3. Falls das Vorzeichen des Leitkoeffizienten parameterabhängig ist, Fallunterscheidung erzeugen.
4. Eine Division durch einen symbolischen Leitkoeffizienten ist nur unter dokumentierter Bedingung \(a_n\neq0\) zulässig.

### 4.3 Rückkopplungs- und Nennerprovenienz

Die Quellen verwenden überwiegend negative Einheitsrückführung. Die Bildung des geschlossenen Kreises und der charakteristischen Gleichung ist jedoch **upstream-owned**.

Das Hurwitz/Routh-Modul erhält nur das bereits gebildete Polynom und Metadaten:

- `polynomial_role = raw_closed_loop_characteristic`, wenn interne geschlossene Stabilität bewertet wird;
- `polynomial_role = reduced_transfer_denominator`, wenn die E/A-Stabilität einer gekürzten Übertragungsfunktion bewertet wird;
- `polynomial_role = state_characteristic`, wenn das Polynom aus \(\det(\lambda I-A)\) stammt.

Das Modul darf das Rückkopplungsvorzeichen anzeigen und protokollieren, aber nicht aus getrennten Regler-/Streckenobjekten rekonstruieren.

### 4.4 Stabilitätsbegriff

Für die geforderte **asymptotische Stabilität** müssen alle Pole strikt negative Realteile besitzen:

\[
\operatorname{Re}(p_i)<0.
\]

Gleichheit in einer Hurwitz- oder Routh-Bedingung gehört nicht zum asymptotisch stabilen Bereich.

Pole auf der imaginären Achse können im freien Zustandsverhalten grenzstabil sein. Eine rationale Übertragungsfunktion mit solchen Polen ist jedoch nicht BIBO-/E/A-stabil.

---

## 5. Hurwitz-Kriterium

### 5.1 Fundstellen

- `skript.pdf`, Kap. 5.3, gedruckte S. 109–111, Definition 5.17 und Theorem 5.18; PDF-S. 125–127.
- `Regelungstechnik_Übung_Aufg-u-Lösungen.pdf`, Übung 09 Aufgabe 3, PDF-S. 116–117.
- `Regelungstechnik_Tutorium_komplett.pdf`, Tutorium 09 Aufgabe 3, PDF-S. 57–58.
- Klausuren SS2025 Aufgabe 4b/c und WS25/26 Aufgabe 4b.

### 5.2 Voraussetzungen

- reelles charakteristisches Polynom;
- endlicher Grad \(n\ge1\);
- Leitkoeffizient nach Fallbehandlung positiv;
- alle Parameterannahmen und Nennerrestriktionen bekannt;
- Ziel ist strikte Links-Halbebenenstabilität.

### 5.3 Notwendige Koeffizientenbedingungen

Nach positiver Normierung müssen alle Koeffizienten strikt positiv sein:

\[
\boxed{a_i>0\quad\text{für alle }i=0,\dots,n.}
\]

Positive Koeffizienten allein sind ab Grad 3 nicht hinreichend.

### 5.4 Hurwitz-Matrix nach Skriptkonvention

\[
H=
\begin{bmatrix}
a_1&a_3&a_5&a_7&\cdots\\
a_0&a_2&a_4&a_6&\cdots\\
0&a_1&a_3&a_5&\cdots\\
0&a_0&a_2&a_4&\cdots\\
0&0&a_1&a_3&\cdots\\
\vdots&\vdots&\vdots&\vdots&\ddots
\end{bmatrix}_{n\times n}.
\]

Nicht vorhandene Koeffizienten werden als null eingesetzt.

Die führenden Hauptabschnittsdeterminanten sind

\[
\Delta_k=\det(H_{1:k,1:k}).
\]

Stabilität:

\[
\boxed{a_i>0\ \forall i\quad\land\quad\Delta_k>0\ \forall k=1,\dots,n.}
\]

### 5.5 Explizite Formeln für relevante Grade

#### Grad 2

\[
N(s)=a_2s^2+a_1s+a_0.
\]

\[
H=
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

Bei \(a_2>0\):

\[
\boxed{a_1>0,\qquad a_0>0.}
\]

#### Grad 3

\[
N(s)=a_3s^3+a_2s^2+a_1s+a_0.
\]

\[
H=
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

Bei positiven Koeffizienten reduziert sich die zusätzliche Bedingung auf

\[
\boxed{a_1a_2>a_0a_3.}
\]

#### Grad 4

\[
N(s)=a_4s^4+a_3s^3+a_2s^2+a_1s+a_0.
\]

\[
H=
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

Bei positiven Koeffizienten sind die nichtredundanten Zusatzbedingungen

\[
\boxed{\Delta_2>0,\qquad\Delta_3>0.}
\]

**Korrektur zum Rechenwege-Master:** Dort steht für den quartischen Fall stellenweise \(\Delta_4=a_0\Delta_3\). Nach der im Skript definierten Matrix gilt \(\Delta_4=a_4\Delta_3\). Für die behandelte Tutoriumsaufgabe ändert dies den Parameterbereich nicht, da beide Koeffizienten positiv sind.

### 5.6 Nummerierter Rechenweg

1. Kanonischen Polynomvertrag vom Vorstufenblock übernehmen.
2. Übergebenes Polynom, Rolle, Annahmen und Ausschlussmengen validieren.
3. Nach fallender Potenz sortieren und fehlende Potenzen mit null ergänzen, falls dies nur eine harmlose Darstellungsnormalisierung ist.
4. Grad und Leitkoeffizient prüfen.
5. Parameterannahmen erfassen.
6. Alle notwendigen Bedingungen \(a_i>0\) aufstellen.
7. Hurwitz-Matrix in Skriptkonvention erzeugen.
8. \(\Delta_1,\dots,\Delta_n\) exakt berechnen.
9. Determinanten faktorisieren.
10. Strikte Ungleichungen lösen.
11. Alle Bedingungen als Schnittmenge vereinigen.
12. Randflächen durch Gleichsetzen einzelner Bedingungen bestimmen.
13. Randfälle separat klassifizieren: Pol im Ursprung, reeller Nullpol, imaginäres Paar oder Gradabfall.
14. Mindestens einen inneren und einen äußeren Testpunkt numerisch über die Pole prüfen.
15. Endaussage mit Stabilitätsart und offen/geschlossenem Rand ausgeben.

### 5.7 Korrekte Schlussfolgerungen

Zulässig:

- „asymptotisch stabil für \(0<K_P<20\)“;
- „bei \(K_P=20\) grenzstabil im freien Zeitverhalten, aber nicht asymptotisch und nicht E/A-stabil“;
- „für den vorgegebenen Parameterbereich existiert keine stabilisierende Einstellung“.

Nicht zulässig:

- Gleichheitsgrenzen ohne Polprüfung als stabil einzuschließen;
- allein aus positiven Koeffizienten Stabilität zu folgern;
- einen leeren Parameterbereich als gültige Lösung auszugeben;
- „grenzstabil“ ohne Angabe des verwendeten Stabilitätsbegriffs zu schreiben.

### 5.8 Typische Fehler

- \(a_0\) und \(a_n\) vertauscht;
- Hurwitz-Matrix in einer anderen Lehrbuchkonvention aufgebaut, aber mit Skriptformeln vermischt;
- Nenner nicht vollständig ausmultipliziert;
- notwendige Bedingungen vergessen;
- \(\ge0\) statt \(>0\) verwendet;
- stärkere und schwächere Bedingungen nicht reduziert;
- Parameterrestriktionen wie \(T_N>0\), \(0<D<1\) nicht geschnitten;
- gemeinsame Faktoren unkritisch gekürzt;
- Randgleichung nicht klassifiziert.

### 5.9 Plausibilitätsprüfungen

- Grad \(n\) erzeugt eine \(n\times n\)-Matrix und \(n\) Determinanten.
- Bei Grad 3 muss \(\Delta_3=a_3\Delta_2\) gelten.
- Bei Grad 4 muss \(\Delta_4=a_4\Delta_3\) gelten.
- Hurwitz- und Routh-Stabilitätsbereich müssen übereinstimmen.
- Ein Punkt im stabilen Bereich muss numerisch ausschließlich Pole mit negativem Realteil liefern.
- Auf einer aktiven Grenze muss mindestens ein Pol Realteil null besitzen oder der Polynomgrad wechseln.

---

## 6. Routh-Schema

### 6.1 Fundstellen

- `skript.pdf`, Kap. 5.4, gedruckte S. 112–115, Tabellen 5.1–5.4 und Theorem 5.23; PDF-S. 128–131.
- `Regelungstechnik_Übung_Aufg-u-Lösungen.pdf`, Übung 09 Aufgabe 3b, PDF-S. 117.
- `Regelungstechnik_Tutorium_komplett.pdf`, Tutorium 09 Aufgabe 3.
- Sonderfälle „Null in erster Spalte“ und „Nullzeile“ werden in den offiziellen Primärquellen nicht systematisch erklärt; der Rechenwege-Master nennt sie ergänzend.

### 6.2 Standardtabellenaufbau

Für

\[
N(s)=a_ns^n+a_{n-1}s^{n-1}+\dots+a_0
\]

werden die ersten beiden Zeilen gebildet als

\[
\begin{array}{c|cccc}
s^n&a_n&a_{n-2}&a_{n-4}&\cdots\\
s^{n-1}&a_{n-1}&a_{n-3}&a_{n-5}&\cdots
\end{array}
\]

Seien zwei aufeinanderfolgende Zeilen

\[
U=[u_0,u_1,u_2,\dots],
\qquad
L=[\ell_0,\ell_1,\ell_2,\dots].
\]

Die nächste Zeile lautet

\[
E=[e_0,e_1,e_2,\dots]
\]

mit

\[
\boxed{
e_k=\frac{\ell_0u_{k+1}-u_0\ell_{k+1}}{\ell_0}.
}
\]

Dies ist äquivalent zur im Skript verwendeten kondensierten \(r_{jk}\)-Notation.

### 6.3 Kubisches Schema

\[
N(s)=a_3s^3+a_2s^2+a_1s+a_0
\]

\[
\begin{array}{c|cc}
s^3&a_3&a_1\\
s^2&a_2&a_0\\
s^1&\dfrac{a_2a_1-a_3a_0}{a_2}&0\\
s^0&a_0&
\end{array}
\]

### 6.4 Quartisches Schema

\[
N(s)=a_4s^4+a_3s^3+a_2s^2+a_1s+a_0
\]

\[
\begin{array}{c|ccc}
s^4&a_4&a_2&a_0\\
s^3&a_3&a_1&0\\
s^2&b_1&a_0&0\\
s^1&c_1&0&0\\
s^0&a_0&&
\end{array}
\]

mit

\[
b_1=\frac{a_3a_2-a_4a_1}{a_3},
\]

\[
c_1=\frac{b_1a_1-a_3a_0}{b_1}.
\]

### 6.5 Stabilitätsaussage

Bei wohldefiniertem Schema und positivem Leitkoeffizienten gilt:

\[
\boxed{\text{asymptotisch stabil}\iff\text{alle Elemente der ersten Spalte sind strikt positiv}.}
\]

### 6.6 Vorzeichenwechsel und rechtsseitige Pole

**[ENTWICKLUNGSREFERENZ]** Der Rechenwege-Master nennt die Standardaussage:

\[
\boxed{
\text{Anzahl der Vorzeichenwechsel in der ersten Spalte}
=
\text{Anzahl der Pole in der rechten Halbebene}.
}
\]

Diese Funktion ist nützlich, aber nicht direkt in den offiziellen Klausuren geprüft worden.

### 6.7 Nummerierter Rechenweg

1. Polynom normieren und sortieren.
2. Erste Zeile aus \(a_n,a_{n-2},\dots\) bilden.
3. Zweite Zeile aus \(a_{n-1},a_{n-3},\dots\) bilden.
4. Jede weitere Zeile exakt aus den beiden Vorzeilen berechnen.
5. Brüche nicht frühzeitig dezimalisieren.
6. Erste Spalte separat extrahieren.
7. Parameterannahmen einsetzen und alle Elemente auf \(>0\) prüfen.
8. Bei vollständig bekannten Vorzeichen die Vorzeichenwechsel zählen.
9. Bei symbolisch unbestimmten Vorzeichen den Parameterraum in Vorzeichenregionen zerlegen.
10. Null-Sonderfälle erkennen, nicht durch Division verlieren.
11. Resultat mit Hurwitz abgleichen.
12. Randfälle über Faktorisierung oder numerische Pole klassifizieren.

### 6.8 Null in der ersten Spalte, restliche Zeile nicht null

**Quellenstatus:** nicht als vollständiges Verfahren in Skript, offizieller Übung oder Klausur gefunden. Nur ergänzend im Rechenwege-Master erwähnt.

Standardbehandlung für spätere Version:

1. den Null-Eintrag durch \(\varepsilon>0\) ersetzen;
2. Tabelle symbolisch mit \(\varepsilon\) fortsetzen;
3. Vorzeichen der ersten Spalte für \(\varepsilon\to0^+\) bestimmen;
4. Vorzeichenwechsel zählen;
5. Ergebnis numerisch durch Polberechnung verifizieren.

Diese Funktion gehört nicht in das erste günstige MVP.

### 6.9 Vollständige Nullzeile

Eine vollständige Nullzeile tritt an offiziellen Stabilitätsgrenzen klar herleitbar auf, etwa bei

\[
N(s)=s^3+4s^2+5s+20=(s+4)(s^2+5).
\]

Behandlung:

1. Die Zeile oberhalb der Nullzeile entspricht einem geraden oder ungeraden Hilfspolynom.
2. Hilfspolynom aus den dortigen Koeffizienten bilden.
3. Zeile durch die Koeffizienten der Ableitung des Hilfspolynoms ersetzen.
4. Routh-Schema fortsetzen.
5. Nullstellen des Hilfspolynoms separat ausgeben.

Für das Beispiel:

\[
A(s)=4s^2+20,
\]

\[
A'(s)=8s.
\]

Die imaginären Pole sind

\[
\boxed{s=\pm j\sqrt5.}
\]

### 6.10 Grenzstabilität

Eine Gleichheitsgrenze muss separat geprüft werden.

Mögliche Ergebnisse:

- einfacher Pol bei \(s=0\);
- einfaches konjugiert-imaginäres Polpaar;
- mehrfacher Pol auf der imaginären Achse;
- Gradabfall durch verschwindenden Leitkoeffizienten;
- Pol-Nullstellen-Kürzung.

Klausurtaugliche Ausgabe:

> Bei der Gleichheitsgrenze verschwindet eine Routh-Bedingung. Das Polynom faktorisiert zu … . Es liegen Pole bei … . Daher ist der Fall nicht asymptotisch stabil. Im freien Zustandsverhalten ist er bei einfachen imaginären Polen grenzstabil; als Übertragungsfunktion ist er nicht E/A-stabil.

---

## 7. Stabilitätsparameterbereiche

### 7.1 Verlangte Aussagen in den Quellen

- Intervall für einen Verstärkungsparameter;
- Ungleichung zwischen zwei positiven Reglerparametern;
- Kombination aus physikalischer Nebenbedingung und Hurwitz-Bedingung;
- zweidimensionaler Bereich in der \((a,K)\)-Ebene;
- leere Schnittmenge und damit Nichtstabilisierbarkeit;
- Grenzkurven und grenzstabile Randfälle.

### 7.2 Algorithmischer Ablauf

1. Alle Grundannahmen als Menge \(A\) erfassen.
2. Koeffizientenbedingungen als Menge \(C\) erzeugen.
3. Determinanten- oder Routh-Bedingungen als Menge \(H\) erzeugen.
4. Definitionsbedingungen als Menge \(D\) ergänzen.
5. Gesuchte stabile Menge bilden:

\[
\boxed{S=A\cap C\cap H\cap D.}
\]

6. Redundante Bedingungen entfernen.
7. Leere Menge erkennen.
8. Für einen Parameter: exakte Intervallvereinigung ausgeben.
9. Für zwei Parameter: Ungleichungssystem und optional 2D-Gebiet ausgeben.
10. Jede Randkurve als offen markieren.
11. Schnittpunkte der Randkurven exakt berechnen.
12. Mindestens einen Testpunkt pro zusammenhängender Region prüfen.

### 7.3 Klausurformat für zwei Parameter

Ausgabe muss enthalten:

- Bedingungen einzeln nummeriert;
- Angabe, welche Bedingung eine andere ersetzt;
- vereinfachtes Gesamtergebnis;
- Grenzfunktionen \(K=f_i(a)\);
- offene bzw. ausgeschlossene Randlinien;
- stabile Fläche als Schraffur oder logisch eindeutige Beschreibung.

---

## 8. Referenzaufgaben

## Referenz 1 – Hurwitz ohne freien Parameter

**Status:** [HERLEITUNG] aus offizieller Übung 09 mit festem \(K_P=8\).  
**Fundstelle:** `Regelungstechnik_Übung_Aufg-u-Lösungen.pdf`, Übung 09 Aufgabe 3, PDF-S. 116–117.

### Eingabe

\[
N(s)=s^3+4s^2+5s+8.
\]

### Rechenweg

1. Koeffizienten:

\[
a_3=1,\ a_2=4,\ a_1=5,\ a_0=8.
\]

2. Alle Koeffizienten sind positiv.
3. Hurwitz-Matrix:

\[
H=
\begin{bmatrix}
5&1&0\\
8&4&0\\
0&5&1
\end{bmatrix}.
\]

4. Determinanten:

\[
\Delta_1=5,
\]

\[
\Delta_2=5\cdot4-8\cdot1=12,
\]

\[
\Delta_3=1\cdot12=12.
\]

### Ergebnis

\[
\boxed{\text{asymptotisch stabil}.}
\]

### GUI-Eingaben

- Methode: Hurwitz
- Koeffizienten: `[1,4,5,8]`
- Ziel: asymptotische Stabilität

### Ausgaben

- Matrix;
- Determinanten;
- Positivitätsprüfung;
- Endaussage.

### Tests

- numerische Pole müssen Realteil \(<0\) besitzen;
- Routh muss null Vorzeichenwechsel liefern.

---

## Referenz 2 – Hurwitz mit einem Parameter

**Status:** [OFFIZIELL + KORREKTUR]  
**Fundstelle:** offizielle Übung 09 Aufgabe 3.

### Eingabe

\[
N(s)=s^3+4s^2+5s+K_P.
\]

### Rechenweg

1. Koeffizientenbedingungen:

\[
K_P>0.
\]

2. Hurwitz:

\[
\Delta_1=5>0,
\]

\[
\Delta_2=20-K_P>0,
\]

\[
\Delta_3=20-K_P>0.
\]

3. Schnittmenge:

\[
K_P>0,\qquad K_P<20.
\]

### Exaktes Ergebnis

\[
\boxed{0<K_P<20.}
\]

### Randfall

Bei \(K_P=20\):

\[
N(s)=(s+4)(s^2+5),
\]

also Pole \(-4,\pm j\sqrt5\). Nicht asymptotisch und nicht E/A-stabil.

### Quellenwiderspruch

Die offizielle Hurwitz-Lösung verwendet teilweise \(K_P\le20\), während der Routh-Teil \(K_P<20\) ergibt. Das Skripttheorem verlangt strikte Positivität. Der korrekte asymptotische Bereich ist offen.

---

## Referenz 3 – Hurwitz mit mehreren Bedingungen

**Status:** [OFFIZIELL]  
**Fundstelle:** `RT_Klausur_SS2025-komplett.pdf`, Aufgabe 4b, Aufgabenbogen PDF-S. 9, Lösung PDF-S. 66.

### Eingabe

\[
G_W(s)=\frac{K(5s+3a+6)}{(s+4)(s+5)(s+a)+9K}.
\]

Charakteristisches Polynom:

\[
N(s)=s^3+(9+a)s^2+(20+9a)s+(20a+9K).
\]

### Rechenweg

1. Koeffizienten:

\[
a_3=1,
\quad a_2=9+a,
\quad a_1=20+9a,
\quad a_0=20a+9K.
\]

2. Notwendige Bedingungen:

\[
a>-9,
\]

\[
a>-\frac{20}{9},
\]

\[
K>-\frac{20}{9}a.
\]

Die Bedingung \(a>-20/9\) ist stärker als \(a>-9\).

3. Determinante:

\[
\Delta_2=(20+9a)(9+a)-(20a+9K).
\]

\[
\Delta_2=9(a^2+9a+20-K)>0.
\]

Daraus:

\[
K<a^2+9a+20.
\]

4. \(\Delta_3=\Delta_2\), da \(a_3=1\).

### Ergebnis

\[
\boxed{
a>-\frac{20}{9},
\qquad
-\frac{20}{9}a<K<a^2+9a+20.
}
\]

### GUI-Ausgaben

- nummerierte Bedingungen;
- reduzierte Bedingungen;
- Grenzgerade \(K=-20a/9\);
- Grenzparabel \(K=a^2+9a+20\);
- offener stabiler Bereich zwischen beiden Kurven.

---

## Referenz 4 – Routh ohne Sonderfall

**Status:** [HERLEITUNG] aus offizieller Übung 09 mit \(K_P=8\).

### Eingabe

\[
N(s)=s^3+4s^2+5s+8.
\]

### Tabelle

\[
\begin{array}{c|cc}
s^3&1&5\\
s^2&4&8\\
s^1&3&0\\
s^0&8&
\end{array}
\]

Erste Spalte:

\[
[1,4,3,8].
\]

### Ergebnis

Keine Vorzeichenwechsel:

\[
\boxed{0\text{ Pole in der rechten Halbebene; asymptotisch stabil}.}
\]

---

## Referenz 5 – Routh mit Vorzeichenwechseln

**Status:** [HERLEITUNG] aus derselben offiziellen Aufgabenfamilie mit \(K_P=30\).

### Eingabe

\[
N(s)=s^3+4s^2+5s+30.
\]

### Tabelle

\[
\begin{array}{c|cc}
s^3&1&5\\
s^2&4&30\\
s^1&-\frac52&0\\
s^0&30&
\end{array}
\]

Erste Spalte:

\[
+,+,-,+.
\]

### Ergebnis

Zwei Vorzeichenwechsel:

\[
\boxed{2\text{ Pole in der rechten Halbebene; instabil}.}
\]

### Plausibilitätsprüfung

Eine reelle Polynomkoeffizientenmenge erzeugt komplexe Pole paarweise. Zwei rechtsseitige Pole sind daher plausibel.

---

## Referenz 6 – Routh mit Null in der ersten Spalte

**Status:** [SYNTHETISCHER TEST], aus dem offiziellen kubischen Polynom durch Multiplikation mit dem stabilen Faktor \((s+1)\) abgeleitet. Der Sonderfall selbst ist in den offiziellen Primärquellen nicht ausgeführt.

### Eingabe

Aus offizieller Familie bei \(K_P=40\):

\[
(s+1)(s^3+4s^2+5s+40)
\]

\[
N(s)=s^4+5s^3+9s^2+45s+40.
\]

### Unvollständiges Standardschema

\[
\begin{array}{c|ccc}
s^4&1&9&40\\
s^3&5&45&0\\
s^2&0&40&0
\end{array}
\]

Die erste Zahl der \(s^2\)-Zeile ist null, die Zeile aber nicht vollständig null.

### Epsilon-Behandlung

\[
0\mapsto\varepsilon>0.
\]

\[
\begin{array}{c|ccc}
s^4&1&9&40\\
s^3&5&45&0\\
s^2&\varepsilon&40&0\\
s^1&45-\dfrac{200}{\varepsilon}&0&0\\
s^0&40&&
\end{array}
\]

Für \(\varepsilon\to0^+\):

\[
+,+,+,-,+.
\]

### Ergebnis

\[
\boxed{2\text{ Vorzeichenwechsel und damit 2 rechtsseitige Pole}.}
\]

Numerische Verifikation:

\[
-4.7305,\quad -1,\quad 0.3653\pm2.8848j.
\]

### MVP-Entscheidung

Nicht Bestandteil des ersten MVP. Als späterer Regressionstest erforderlich.

---

## Referenz 7 – Routh mit vollständiger Nullzeile

**Status:** [HERLEITUNG] aus offizieller Übung 09 am Rand \(K_P=20\).

### Eingabe

\[
N(s)=s^3+4s^2+5s+20.
\]

### Tabelle bis zum Sonderfall

\[
\begin{array}{c|cc}
s^3&1&5\\
s^2&4&20\\
s^1&0&0
\end{array}
\]

### Hilfspolynom

Aus der \(s^2\)-Zeile:

\[
A(s)=4s^2+20.
\]

\[
A'(s)=8s.
\]

Ersatzzeile:

\[
\begin{array}{c|cc}
s^1&8&0
\end{array}
\]

### Exaktes Ergebnis

\[
N(s)=(s+4)(s^2+5).
\]

\[
\boxed{p_1=-4,\qquad p_{2,3}=\pm j\sqrt5.}
\]

Nicht asymptotisch stabil und nicht E/A-stabil; im freien Zeitverhalten bei einfachen imaginären Polen grenzstabil.

---

## Referenz 8 – separater Grenzstabilitätsfall

**Status:** [OFFIZIELL + KORREKTUR]  
**Fundstelle:** `Regelungstechnik_Tutorium_komplett.pdf`, Tutorium 09 Aufgabe 3a, PDF-S. 57–58.

### Eingabe

\[
N(s)=s^3+8s^2+3s+1+K_R,
\qquad K_R>0.
\]

Strikter stabiler Bereich:

\[
0<K_R<23.
\]

### Grenze

\[
K_R=23.
\]

\[
N(s)=s^3+8s^2+3s+24.
\]

Faktorisierung:

\[
N(s)=(s+8)(s^2+3).
\]

Pole:

\[
\boxed{-8,\quad\pm j\sqrt3.}
\]

### Ergebnis

\[
\boxed{
K_R=23\text{ ist kein asymptotisch stabiler Wert.}
}
\]

Die offizielle Tutoriumslösung gibt \(0<K_R\le23\) an. Nach Skript und Polprüfung muss die obere Grenze offen sein.

---

## 9. Weitere offizielle Aufgabenfamilien

### 9.1 PI-Regler an PT2-Strecke

Quelle: Tutorium 09 Aufgabe 3b.

\[
N(s)=T_Ns^3+3T_Ns^2+T_N(1+3K_R)s+3K_R,
\]

\[
K_R,T_N>0.
\]

Korrekte strikte Bedingung:

\[
\boxed{T_N>\frac{K_R}{1+3K_R}.}
\]

Die offizielle Lösung verwendet \(\ge\); die Gleichheit erzeugt eine Nullzeile und ein imaginäres Polpaar.

### 9.2 PT2-System mit PI-artigem Regler

Quelle: Tutorium 09 Aufgabe 3c.

\[
N(s)=2s^3+4D\omega_0s^2+6\omega_0^2s+\omega_0^2,
\]

\[
\omega_0>0,\qquad0<D<1.
\]

Strikte Stabilität:

\[
\boxed{D>\frac1{12\omega_0}.}
\]

Zusätzlich muss ein zulässiges \(D<1\) existieren, also

\[
\omega_0>\frac1{12}.
\]

### 9.3 I-Regler und drei PT1-Glieder, Grad 4

Quelle: Tutorium 09 Aufgabe 3d.

\[
N(s)=T_1^3T_Is^4+3T_1^2T_Is^3+3T_1T_Is^2+T_Is+4.
\]

Für \(T_1,T_I>0\):

\[
\Delta_2=3T_1T_I(T_I-4T_1),
\]

\[
\Delta_3=4T_1^3T_I^2(2T_I-9T_1).
\]

Damit:

\[
\boxed{T_I>\frac92T_1.}
\]

Routh:

\[
\begin{array}{c|ccc}
s^4&T_1^3T_I&3T_1T_I&4\\
s^3&3T_1^2T_I&T_I&0\\
s^2&\frac83T_1T_I&4&0\\
s^1&T_I-\frac92T_1&0&0\\
s^0&4&&
\end{array}
\]

Grenze:

\[
T_I=\frac92T_1
\]

mit Hilfspolynom

\[
12T_1^2s^2+4,
\]

und imaginären Polen

\[
\boxed{s=\pm\frac{j}{\sqrt3T_1}.}
\]

---

## 10. GUI-Spezifikation

### 10.1 GUI und Orchestrierung

Die sichtbare Gesamt-GUI darf mehrere Startpunkte anbieten, der Hurwitz/Routh-Kern jedoch nur den Polynomvertrag konsumieren.

#### Direkter Stabilitätsmodus

- kanonisches Polynom oder Koeffizientenliste;
- Parameterannahmen;
- gesuchte Parameter;
- Analyseziel;
- Methode: Hurwitz, Routh oder beide.

#### Workflow „Übertragungsfunktion“

Die GUI sendet Zähler und Nenner zuerst an den Übertragungsfunktions-/Kürzungsblock. Erst dessen `CharacteristicPolynomialInput` wird an Hurwitz/Routh weitergereicht.

#### Workflow „Regelkreis“

Die GUI sendet Strecke, Regler, Rückführung und Vorzeichen zuerst an den Regelkreisblock. Hurwitz/Routh erhält ausschließlich dessen rohes charakteristisches Polynom.

#### Workflow „DGL“

Die GUI sendet DGL, Ein-/Ausgangsdefinition und Anfangsbedingungen zuerst an den Laplace-/Übertragungsfunktionsblock. Keine DGL-Verarbeitung im Stabilitätskern.

#### Erforderliche Anzeige vor Start der Stabilitätsprüfung

- erzeugender Vorstufenblock;
- übergebenes Polynom;
- Rolle des Polynoms;
- Kürzungsstatus;
- Parameterannahmen und ausgeschlossene Mengen;
- Analyseziel intern, Zustand oder E/A.

### 10.2 Parameterannahmen

GUI muss mindestens unterstützen:

- \(K>0\), \(K\ge0\);
- Intervall \(0<D<1\);
- \(T_1,T_I>0\);
- reell;
- ungleich null;
- optionale numerische Grenzen.

### 10.3 Notwendige Ausgaben

1. Eingabe in normalisierter Form.
2. Vollständig ausmultipliziertes charakteristisches Polynom.
3. Koeffizientenzuordnung.
4. Verwendete Annahmen.
5. Notwendige Koeffizientenbedingungen.
6. Hurwitz-Matrix.
7. Alle relevanten Determinanten, zunächst unfaktorisiert, dann faktorisiert.
8. Routh-Tabelle mit Potenzbeschriftung.
9. Erste Spalte und Vorzeichenfolge.
10. Anzahl rechtsseitiger Pole, sofern bestimmbar.
11. Stabilitätsbedingungen einzeln.
12. Reduzierter Gesamtbereich.
13. Offene Randbedingungen.
14. Randklassifikation.
15. Exakte LaTeX-Ausgabe.
16. Numerische Kontrollpole für gewählte Testpunkte.
17. Warnungen und Quellenhinweis zum verwendeten Aufgabentyp.

### 10.4 Klausurtaugliches Ausgabeformat

Beispiel:

```latex
\text{Charakteristisches Polynom:}
\quad N(s)=s^3+4s^2+5s+K_P.

\text{Notwendige Bedingungen:}
\quad K_P>0.

\Delta_1=5>0,
\qquad
\Delta_2=20-K_P>0,
\qquad
\Delta_3=20-K_P>0.

\boxed{0<K_P<20}
```

Keine reine Endwertausgabe ohne nachvollziehbaren Rechenweg.

---

## 11. Technische Grenzfälle

1. **Leitkoeffizient null:** Grad reduziert sich; Parameterfall separat lösen.
2. **Leitkoeffizient mit unbekanntem Vorzeichen:** Fallzerlegung.
3. **Fehlende Potenz:** Nullkoeffizient einsetzen.
4. **Konstanter Term null:** Pol bei \(s=0\); keine asymptotische Stabilität.
5. **Koeffizient symbolisch null auf Teilmenge:** Teilmenge separat klassifizieren.
6. **Division durch symbolischen Routh-Eintrag:** Definitionsbedingung speichern.
7. **Vollständige Nullzeile:** Hilfspolynomverfahren.
8. **Isolierte Null in erster Spalte:** Epsilon-Verfahren, späteres Modul.
9. **Mehrere Nullzeilen:** wiederholte Hilfspolynomlogik.
10. **Mehrfacher imaginärer Pol:** nicht einmal grenzstabil im beschränkten freien Sinn; Jordan-/Vielfachheitswarnung.
11. **Polynomgrad >4:** allgemeine Matrix/Tabelle möglich, aber symbolische Ausdrucksexplosion begrenzen.
12. **Floating-Point-Koeffizienten nahe null:** exakte Rationalisierung oder Toleranzwarnung.
13. **Gemeinsame Faktoren:** Kürzung erfolgt upstream; Stabilitätsmodul verlangt rohes und gekürztes Polynom samt Bericht.
14. **Instabile Pol-Nullstellen-Kürzung:** E/A-Stabilität kann interne Instabilität verdecken; Analyseziel entscheidet, welches Polynom geprüft wird.
15. **Leere Parameterregion:** explizit „nicht stabilisierbar unter den Annahmen“.
16. **Nicht zusammenhängende Region:** Intervallvereinigung oder mehrere Flächen ausgeben.
17. **Mehr als zwei freie Parameter:** kein automatisches 2D-Diagramm ohne Projektion.
18. **Ungleichungslöser unsicher:** Bedingungen stehen lassen; keine erfundene Vereinfachung.
19. **Einheiten:** Zeitkonstanten und Frequenzen dürfen nicht dimensionswidrig verglichen werden; dimensionslose Produkte wie \(D\omega_0\) nur mit korrekten Einheiten interpretieren.
20. **Rundung:** Stabilitätsgrenzen exakt halten; Dezimalwerte nur ergänzend.

---

## 12. Erforderliche Tests

### 12.1 Unit-Tests Hurwitz

| ID | Polynom | Erwartung |
|---|---|---|
| H2-1 | \(s^2+2s+3\) | stabil |
| H2-2 | \(s^2+0s+3\) | nicht asymptotisch stabil |
| H3-1 | \(s^3+4s^2+5s+8\) | stabil |
| H3-2 | \(s^3+4s^2+5s+K\) | \(0<K<20\) |
| H3-3 | SS2025-Polynom | offizieller zweiparametriger Bereich |
| H4-1 | Tutorium 09d | \(T_I>9T_1/2\) |
| H4-2 | gleiche Aufgabe an Grenze | imaginäres Paar erkennen |

### 12.2 Unit-Tests Routh

| ID | Fall | Erwartung |
|---|---|---|
| R3-1 | \(K=8\) | 0 Vorzeichenwechsel |
| R3-2 | \(K=30\) | 2 Vorzeichenwechsel |
| R3-3 | \(K=20\) | vollständige Nullzeile, \(\pm j\sqrt5\) |
| R4-1 | isolierte Null erster Spalte | Epsilon-Grenzwert, 2 RHP-Pole |
| R4-2 | Tutorium 09d innen | stabil |
| R4-3 | Tutorium 09d Grenze | Hilfspolynom und imaginäres Paar |

### 12.3 Cross-Checks

- Hurwitz-Bereich = Routh-Bereich.
- Zahl der Routh-Vorzeichenwechsel = Zahl numerischer Pole mit \(\Re p>0\).
- Grenzpolynom-Faktorisierung stimmt mit Hilfspolynom überein.
- Symbolische und numerische Auswertung stimmen bei rationalen Testwerten überein.
- Bedingungen bleiben nach positiver Skalierung des Polynoms unverändert.
- Multiplikation mit \(-1\) vor Normierung ändert das Ergebnis nicht.

### 12.4 Schnittstellen- und Orchestrierungstests

| ID | Eingangsweg | Erwartung |
|---|---|---|
| IF-1 | direktes Polynom \(s^3+4s^2+5s+K_P\) | Kern akzeptiert und löst \(0<K_P<20\) |
| IF-2 | Übung 09: \(G_S\)+P-Regler über Regelkreisblock | upstream erzeugtes Polynom ist exakt identisch zu IF-1 |
| IF-3 | DGL direkt an Kern-API | Ablehnung `UPSTREAM_TRANSFORMATION_REQUIRED` |
| IF-4 | offener Kreis \(L(s)\) direkt an Kern-API | Ablehnung `CHARACTERISTIC_POLYNOMIAL_REQUIRED` |
| IF-5 | WS25/26 Aufgabe 4b, reduzierter Nenner mit Kürzungsbericht | externe E/A-Analyse nutzt kubisches Polynom |
| IF-6 | derselbe Fall als rohes internes Polynom | zusätzliche Faktorinformation bleibt erhalten; keine stillschweigende Gleichsetzung |
| IF-7 | parameterabhängiger Leitkoeffizient ohne Ausschlussmengen | Ablehnung oder explizite Fallanforderung |
| IF-8 | Tutorium 09a–d aus Regelkreisblock | Polynome Grad 3/4 und Annahmen vollständig übertragen |

### 12.5 Regressionstests aus Quellenfehlern

1. \(K_P=20\) darf nicht als asymptotisch stabil ausgegeben werden.
2. \(K_R=23\) darf nicht als asymptotisch stabil ausgegeben werden.
3. \(T_N=K_R/(1+3K_R)\) darf nicht im stabilen Bereich liegen.
4. \(D=1/(12\omega_0)\) darf nicht im stabilen Bereich liegen.
5. Für Grad 4 muss \(\Delta_4=a_4\Delta_3\) nach Skriptmatrix gelten.

---

## 13. MVP-Priorisierung

Bewertungsskala: 1 = niedrig, 5 = hoch.

### A. Erstes günstiges MVP

| Funktion | Klausurnutzen | Codex-Aufwand | Urteil |
|---|---:|---:|---|
| kanonischer `CharacteristicPolynomialInput`-Vertrag | 5 | 2 | zwingend |
| direkte Polynome Grad 2–4 | 5 | 2 | zwingend |
| Validierung von Rolle, Annahmen und Ausschlussmengen | 5 | 2 | zwingend |
| automatische Koeffizientenzuordnung und Normierung | 5 | 2 | zwingend |
| Hurwitz-Matrix und Determinanten | 5 | 2 | zwingend |
| symbolische Einparameterbereiche | 5 | 2 | zwingend |
| zweiparametrige Bedingungen als Ungleichungssystem | 5 | 3 | zwingend |
| Übergabe des Bedingungssystems an 2D-Visualisierung | 4 | 2 | sinnvoll; Plot selbst optional extern |
| Standard-Routh ohne Sonderfall | 3 | 2 | sinnvoll |
| Hurwitz/Routh-Gegenprüfung | 4 | 2 | sehr sinnvoll |
| exakte LaTeX-Rechenwege | 5 | 2 | zwingend |
| numerische Polkontrolle an Testpunkten | 4 | 2 | zwingend |
| Randfaktorisierung für kubische Polynome | 5 | 2 | zwingend |

**MVP-Ziel:** Die beiden Klausuraufgaben SS2025 und WS25/26 sowie Übung 09 vollständig lösen, sofern ein Vorstufenblock das kanonische Polynom liefert. Zusätzlich müssen Tutorium 09a–d über die Verträge ohne duplizierte Regelkreislogik integrierbar sein.

### B. Spätere Sonderfälle

| Funktion | Klausurnutzen | Codex-Aufwand | Urteil |
|---|---:|---:|---|
| vollständige Nullzeile und Hilfspolynom | 3 | 3 | zweite Ausbaustufe |
| isolierte Null in erster Spalte, Epsilon | 2 | 4 | später |
| Anzahl RHP-Pole in symbolischen Regionen | 3 | 4 | später |
| Grad 5–8 numerisch/symbolisch | 2 | 3 | später |
| interne Stabilität trotz Kürzungen | 3 | 4 | später |
| automatische Fallzerlegung bei Leitkoeffizient null | 3 | 4 | später |
| mehrere getrennte 2D-Stabilitätsgebiete | 3 | 4 | später |

### C. Schlechtes Verhältnis von Aufwand zu Klausurpunkten

| Funktion | Grund |
|---|---|
| allgemeine symbolische Hurwitz-Determinanten für beliebig hohen Grad | Ausdrucksexplosion, keine Quellenrelevanz |
| allgemeine semialgebraische Gebiete mit drei oder mehr Parametern | hoher Solver- und GUI-Aufwand |
| interaktiver 3D-Stabilitätsflächenplot | Komfort statt Klausurpunkten |
| vollständiger Beweisgenerator für Hurwitz/Routh | nicht verlangt |
| automatische Erkennung beliebiger Routh-Sonderfallketten | selten und nicht klausurbelegt |
| hochpräzise Root-Locus-Integration | anderer Programmierblock |
| eigene Laplace-, Übertragungsfunktions- oder Regelkreisengine im Hurwitz/Routh-Modul | klare Duplizierung, erhöht Fehler- und Wartungsrisiko |
| automatische Rekonstruktion von \(1+L(s)=0\) im Stabilitätskern | gehört vollständig in den Regelkreisblock |
| visuelle Matrixeditoren | Eingabeaufwand höher als Nutzen |

---

## 14. Verbindliche fachliche Entscheidungen

1. Stabilitätsbereiche sind für asymptotische Stabilität **offen** an Hurwitz-/Routh-Gleichheitsgrenzen.
2. Das Skript hat Vorrang vor offiziellen Musterlösungen mit \(\ge\)-Fehlern.
3. Grad 3 ist der Hauptfall; Grad 4 muss vollständig unterstützt werden.
4. Routh ist im MVP primär Gegenprüfung, nicht Hauptgrund für die Entwicklung.
5. Zweiparametrige Hurwitz-Gebiete sind ein Kernfeature, da sie in beiden Klausuren vorkamen.
6. Sonderfälle dürfen nicht stillschweigend als Standardschema behandelt werden.
7. Jede Endaussage muss den Stabilitätsbegriff nennen.
8. Exakte symbolische Ergebnisse haben Vorrang vor Dezimalwerten.
9. Der Rechenweg muss klausurtauglich sichtbar sein.
10. Bei unklarer symbolischer Vereinfachung werden die gültigen Ungleichungen ausgegeben, nicht geraten.
11. Der Hurwitz/Routh-Kern akzeptiert nur kanonische charakteristische Polynome, keine DGL-, Übertragungsfunktions- oder Regelkreisobjekte.
12. Rohes geschlossenes charakteristisches Polynom und gekürzter E/A-Nenner sind unterschiedliche Analyseobjekte und müssen durch `polynomial_role` getrennt werden.
13. Die 7 Punkte aus SS2025 Aufgabe 4c gehören zur nachgelagerten Gebietsvisualisierung, nicht zur Hurwitz-Berechnung selbst.

---

## 15. Offene Quellenfrage

Die vollständige Behandlung der Routh-Sonderfälle „isolierte Null in der ersten Spalte“ und „Hilfspolynom bei Nullzeile“ ist in den offiziellen Primärquellen nicht als allgemeines Verfahren gefunden worden. Die Nullzeile ist jedoch eindeutig aus offiziellen Stabilitätsgrenzen herleitbar. Das Epsilon-Verfahren bleibt eine ergänzende Standardmethode und sollte nicht als ausdrücklich gelehrter Vorlesungsinhalt ausgegeben werden.

--- NOTEBOOKLM-PROMPT ---

Prüfe folgende Frage ausschließlich anhand der hochgeladenen offiziellen Regelungstechnik-Quellen, insbesondere `skript.pdf`, `Regelungstechnik_Übung_Aufg-u-Lösungen.pdf`, `Regelungstechnik_Tutorium_komplett.pdf`, `RT_Klausur_SS2025-komplett.pdf` und `RT-Klausur_WS_25_26-komplett.pdf`:

Werden beim Routh-Schema die Sonderfälle

1. Null in der ersten Spalte bei nicht vollständig leerer Zeile, einschließlich Epsilon-Verfahren,
2. vollständige Nullzeile,
3. Hilfspolynom und Ableitungszeile

irgendwo ausdrücklich erklärt oder als Aufgabe verwendet?

Antworte kurz und eindeutig. Belege jede Fundstelle mit kurzem direkten Zitat, Dokumentname und genauer Seite. Trenne ausdrücklich zwischen einer direkten offiziellen Erklärung und einem Fall, der nur aus einer offiziellen Stabilitätsgrenze mathematisch hergeleitet werden kann. Wenn das Epsilon-Verfahren nicht vorkommt, sage das ausdrücklich.

--- ENDE ---
