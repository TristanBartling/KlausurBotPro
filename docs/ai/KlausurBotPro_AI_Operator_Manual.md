# KlausurBotPro AI Operator Manual

## 1. Dokumentstatus

| Merkmal | Wert |
|---|---|
| Repository | `TristanBartling/KlausurBotPro` |
| Geprüfter Baseline-Commit | `093cfba2b1488e7a3455ead8c584c38379d60104` |
| Erfassungsdatum | 2026-07-24 |
| App-Version | `0.1.1` |
| Startart | Nach Installation: `python -m klausurbotpro` oder Konsolenskript `klausurbotpro` |
| Zweck | Technische Arbeitsgrundlage für einen KI-Assistenten, der die vorhandene Desktop-App bedient und Bedienprobleme einordnet |
| Zielgruppe | GPT-/KI-Assistenten, die den implementierten Stand nicht aus der Entwicklung kennen; Menschen ausschließlich als Prüfer oder Maintainer dieser Referenz |
| Grenzen der Verlässlichkeit | Gilt ausschließlich für den genannten Commit; UI-Pfade wurden aus aktueller Verdrahtung im Code oder fokussierten UI-Tests abgeleitet. Dies ist kein Nachweis, dass jedes Element in der real gestarteten Windows-App bei jeder DPI-, Schrift- oder Fensterkonfiguration visuell geprüft wurde. Nicht ausdrücklich nachgewiesene Varianten bleiben unbekannt. |

Dieses Handbuch beschreibt App-Bedienung und implementiertes Verhalten. Es ist keine fachliche Quelle für Regelungstechnik. App-Ergebnisse müssen bei wichtigen Aufgaben unabhängig fachlich geprüft werden. Das Handbuch gilt nur für den angegebenen Softwarestand.

## 2. Statusvokabular

- `UI_VERIFIED`: Der UI-Pfad ist durch aktuelle Verdrahtung im Code oder einen fokussierten UI-Test nachgewiesen. Der Status bestätigt nicht automatisch eine visuelle Prüfung jedes Elements in der real gestarteten Windows-App bei jeder DPI-, Schrift- oder Fensterkonfiguration; reales Rendering und plattformspezifische Bedienbarkeit bleiben Gegenstand der offenen manuellen Validierungen.
- `INTERNAL_ONLY`: Implementiert, aber nicht sicher über die aktuelle Oberfläche erreichbar.
- `PARTIAL`: Nutzbar, jedoch mit dokumentierten Einschränkungen oder manuellen Schritten.
- `UNSUPPORTED`: Vom aktuellen Workflow ausdrücklich abgelehnt oder nachweislich nicht vorhanden.
- `UNKNOWN`: Aus Code und vorhandenen Tests nicht zuverlässig bestimmbar.

## 3. Schnellübersicht

| Aufgabentyp | Modul/Ansicht | Status | Eingabe | Automatisch erledigt | Manuell nötig | Hauptgrenze |
|---|---|---|---|---|---|---|
| Rationale Übertragungsfunktion, Pole, Nullstellen, Stabilität | Transferfunktion | `UI_VERIFIED` | Gemeinsamer Ausdruck oder Zähler/Nenner | Parsen, rohe Form, Kürzung, rohe/reduzierte Wurzeln, Stabilität, Bericht | Modell und Parameterbelegungen korrekt übertragen; fachlich prüfen | Nur sichere rationale Syntax; nicht belegte Parameter können Aussagen unbestimmt lassen |
| Frequenzgang an einem Punkt | Frequenzbereich / Einzelpunkt | `UI_VERIFIED` | Übertragungsfunktion und exakte rationale Kreisfrequenz | `G(jω)`, Real-/Imaginärteil, Betrag, dB, Hauptphase | Einheit und gewünschte Frequenz prüfen | Frequenzfeld akzeptiert keine Dezimalzahl wie `0.5`, sondern z. B. `1/2` |
| Bode, Standardglieder, Reserven, Nyquist | Frequenzbereich / Bode | `PARTIAL` | Übertragungsfunktion, Grenzen, Raster, Phase | Numerisches Raster, Diagramme mit gemeinsamer logarithmischer Frequenzachse, Komponenten, Durchtritte, Reserven, Nyquist | Frequenzgrenzen und alle numerisch benötigten Parameter vorgeben; asymptotische Skizze fachlich beurteilen | Worked Steps sind numerisch; keine vollständige asymptotische Konstruktion |
| Hurwitz und Parameterbereich | Stabilität | `UI_VERIFIED` | Polynom oder Führungsübertragungsfunktion | Kanonisierung, Matrix, Determinanten, Bedingungen, Bereich | Rolle und Analyseziel korrekt wählen | Höchstens zwei Entscheidungsparameter |
| Routh und Parameterbereich | Stabilität | `PARTIAL` | Polynom oder Führungsübertragungsfunktion | Routh-Schema, erste Spalte, Vorzeichenwechsel, Bereich | Sonderfälle fachlich behandeln | Vollständige Nullzeile kann LaTeX-Ausgabe verhindern |
| Direkte Laplace-Transformation | Zeitbereich | `PARTIAL` | Unterstützte Kombinationen in `t` | Tabellenpaar-/Regeltransformation | Prüfen, ob Funktion im begrenzten Regelvorrat liegt | Kein allgemeiner CAS-Laplace-Workflow |
| Inverse Laplace und Partialbruchzerlegung | Zeitbereich | `PARTIAL` | Allgemeine rationale Bildfunktion `F(s)` | Algebraische Reduktion von `F(s)`, Klassifikation, PBZ, Rücktransformation, Kontrollen | Uneigentliche Fälle ggf. nach Polynomdivision manuell weiterführen; Kürzungen ohne Systemkontext nur algebraisch deuten | Uneigentliche rationale Funktionen werden nach Division gestoppt |
| Sprung-, allgemeine und Exponentialantwort | Zeitbereich | `PARTIAL` | Systemübertragungsfunktion `G(s)` plus Eingang | Separate Reduktion von `G(s)`, Produktbildung `Y(s)=G(s)U(s)`, PBZ, Zeitfunktion, Endwertprüfung | Anfangsbedingungen/Modellannahmen prüfen; Provenienz einer Kürzung beachten | Nur Kürzungen innerhalb von `G(s)` begründen eine Warnung vor verdeckter Systemdynamik; reine Produktkürzungen in `Y(s)` nicht |
| Lineare DGL mit Anfangswerten | Zeitbereich | `PARTIAL` | Strukturierte Koeffizienten, Signal, Anfangswerte | Laplace-DGL, freie/erzwungene Antwort, PBZ, Verifikation | Alle benötigten Anfangswerte angeben oder Nullpolitik bestätigen | Ordnung 1 bis 4; zeitvariable Koeffizienten abgelehnt |
| Übertragungsfunktion aus DGL | Zeitbereich | `UI_VERIFIED` | Strukturierte DGL-Koeffizienten | Nullzustands-Laplace und Quotient | Vollständigen Nullzustand sichtbar bestätigen | Nichtnull-Anfangszustand ist für diesen Workflow unzulässig |
| DGL → Regelungsnormalform / Zustandsstabilität | Zustandsraum | `UI_VERIFIED` | DGL-Koeffizienten, Ordnung 1 bis 4, Analyseziel | Normalisierung, Matrizen, Polynom, Eigenwerte; zielabhängig Stabilitäts- oder Vollanalyse | Nur nicht abgeleiteten Eingang verwenden | Unsicherer führender Koeffizient wird abgelehnt |
| Zustandsraum → Vollanalyse / Zustandsstabilität | Zustandsraum | `UI_VERIFIED` | `A`, `b`, `c^T`, `d`, Analyseziel | Zielabhängig Eigenwert-/Stabilitätslösung oder zusätzlich Übertragungsfunktion und verborgene Modi | Matrixdimensionen korrekt eingeben | Zustandsdimension größer als 4; keine Jordanformanalyse |
| P-Auslegung für Phasenreserve | Reglerauslegung | `PARTIAL` | Strecke, Zielreserve, Frequenzbereich | Zielphasensuche, positiver P-Faktor, neue Reserven und Nyquist | Bei mehreren geeigneten Kandidaten auswählen; Ergebnis fachlich prüfen | Numerische Suche; Zielphase muss im Bereich erreicht werden |
| Ziegler–Nichols / Cohen–Coon | Reglerauslegung | `PARTIAL` | Tabellenkennwerte | Allgemeine Formel, konkrete Gültigkeitsprüfung, exakte Tabellenrechnung und Reglerformen | Quellenbereich und Einheiten vor Eingabe prüfen | Kursbereiche `K_T < 0,5 T` bzw. `0 < K_T/T < 2`; reine Zahlen in Sekunden |
| Linearisierung, Wurzelortskurve, Lead/Lag, Padé, OCR, freie Blockbilder | Keine aktuelle Ansicht | `UNSUPPORTED` | — | — | Außerhalb der App bearbeiten | Keine verdrahtete UI nachgewiesen |

## 4. Start und Navigation

Installiere die Abhängigkeiten gemäß Projektkonfiguration und starte mit:

```powershell
python -m klausurbotpro
```

Alternativ stellt `pyproject.toml` das Konsolenskript `klausurbotpro` bereit. Das Hauptfenster heißt exakt `KlausurBotPro`. Es enthält die Top-Level-Tabs `Transferfunktion`, `Frequenzbereich`, `Stabilität`, `Zeitbereich`, `Zustandsraum` und `Reglerauslegung`; der Wechsel erfolgt durch Anklicken des Tabs.

Es gibt keine anwendungsweite Menüleiste für Berechnen, Export oder Öffnen. Aktionen liegen in den Modulen. `Transferfunktion` besitzt zusätzlich die nachgewiesenen Kurzbefehle `Ctrl+Return`/`Ctrl+Enter` (Berechnen), `Ctrl+R` (Zurücksetzen), `Ctrl+Shift+C` (aktiven Bericht kopieren), `Alt+P` (Plaintext) und `Alt+L` (LaTeX-Quelltext). Andere Module bieten sichtbare `LaTeX kopieren`-Schaltflächen. Ein Datei-Export ist nicht nachgewiesen; Kopieren verwendet die Zwischenablage.

Während asynchroner Berechnungen werden die betreffenden Eingaben gesperrt. Wird das Fenster dann geschlossen, zeigt die App sinngemäß `Schließen wird nach Abschluss der laufenden Berechnung fortgesetzt.` und wartet auf den Abschluss.

## 5. Globale Eingaberegeln

### 5.1 Sichere rationale und skalare Ausdrücke

| Regel | Gültig | Ungültig/nicht unterstützt | Korrektur | Geltungsbereich |
|---|---|---|---|---|
| Multiplikation explizit | `2*s`, `K*(s+1)` | `2s`, `2(s+1)`, `(s+1)(s+2)` | `*` ergänzen | Übertragungsfunktion, Frequenzbereich, Stabilität, Bildbereich und viele Koeffizientenfelder |
| Potenzen | `s^2`, `s**2` | Variable Exponenten wie `s^K` | Ganzzahligen, begrenzten Exponenten verwenden | Sichere Ausdrucksparser |
| Klammern/Brüche | `(s+1)/(s+2)`, `1/10` | Unvollständige Klammern | Klammern schließen; Zähler/Nenner eindeutig klammern | Alle mathematischen Ausdrucksfelder |
| Dezimalzahlen | `1.5`, `1,5` | `.5`, `1.`, `1e3` im allgemeinen Parser | `0.5`, `1`, bzw. ausgeschriebenen Wert/Bruch verwenden | Allgemeiner Parser; Ausnahme: Reglerauslegung akzeptiert wissenschaftliche Schreibweise in Skalaren |
| Dezimalkomma | `0,125` ohne Leerzeichen | `1, 5`, `(1,2,3)` | Für Listen Kommas trennen; für Dezimalzahl ohne Leerzeichen oder Punkt schreiben | Ausdrucksfelder, nicht Matrix-/Listenstruktur |
| Symbole | Hauptvariable plus ausdrücklich deklarierte Parameter | Nicht deklarierte Symbole, reservierte Namen als Parameter | Parameter in der sichtbaren Tabelle/Liste deklarieren | Modulabhängig |
| Code/Funktionsaufrufe | — | `open('x')`, `__import__('os')`, Indizierung, Bedingungen | Nur mathematische Sprache verwenden | Überall; Eingaben werden nicht mit `eval` ausgeführt |
| Ressourcen | Bis 1000 Zeichen, 256 AST-Knoten, Tiefe 32, höchstens 16 Symbole | Größere Eingaben | Ausdruck vereinfachen/aufteilen | Gemeinsame Parser-Standardlimits |

### 5.2 Zeit- und Bildprofil

| Regel | Gültig | Ungültig/nicht unterstützt | Korrektur | Geltungsbereich |
|---|---|---|---|---|
| Zeitvariable/Funktionen | `2*t*exp(-4*t) + sin(pi*t)`, `cos(5*t)` | `s+exp(t)`, `log(t)` | Nur `t`, `exp`, `sin`, `cos`, `pi` und deklarierte Parameter verwenden | `f(t)` bei direkter Laplace-Transformation |
| Bildvariable | `(s+1)/(s^2+pi)` | `s+t`, `exp(s)` | Nur rationale Algebra in `s` und `pi` verwenden | `F(s)`, `G(s)`, `U(s)` |
| Gemischte Variablen | — | `t+s` | Passenden Aufgabentyp wählen und nur dessen Variable verwenden | Zeitbereich |

### 5.3 Strukturierte Listen, Parameter und Matrizen

| Regel | Gültig | Ungültig/nicht unterstützt | Korrektur | Geltungsbereich |
|---|---|---|---|---|
| Parameterliste | `K_P` oder `a,K` | Mehr als zwei Parameter in Stabilität | Auf relevante ein oder zwei Parameter begrenzen | Stabilität; andere Module besitzen eigene Grenzen |
| Annahmen | `T1 > 0; TI > 0`, `0 < D < 1` | Nichtrelationale/komplexe Aussagen | Relationen mit `<`, `<=`, `>`, `>=`, `=`, `!=` und `;`/Zeilenumbruch verwenden | Stabilität, DGL, Zustandsraum |
| Exakte Frequenzen | `3`, `1/10`; Liste `1/2, 1, 2` | `0.5` im Frequenz-Request | `1/2` verwenden | Frequenzbereich |
| Matrizen | `0, 1; -2, -3` | Uneinheitliche Zeilenlängen | Zellen mit `,`, Zeilen mit `;` oder Zeilenumbruch trennen | Zustandsraum |
| Zeitwerte der Tabellenverfahren | `12`, `3/2` | `12 s` | Nur Zahlen eingeben; Beschriftung liefert die Einheit Sekunden | Reglerauslegung |

## 6. Module und UI-Elemente

### Transferfunktion

**Status:** `UI_VERIFIED`

**Zweck:** Erstellt eine rohe und reduzierte rationale Übertragungsfunktion und analysiert Nullstellen, Pole, E/A-Stabilität und eine sicher unterstützte qualitative Polinterpretation.

**Navigation:** Startansicht bzw. Tab `Transferfunktion`.

**Interaktive Elemente:**

| Sichtbare Bezeichnung | Typ | Erwartete Eingabe/Auswahl | Wirkung | Aktivierungsbedingung | relevanter Fehlerfall |
|---|---|---|---|---|---|
| `Gemeinsamer Ausdruck` / `Zähler und Nenner getrennt` | Optionsfelder | Eingabeform | Schaltet sichtbare Ausdrucksfelder | Immer außerhalb Berechnung | Nur aktive Form wird ausgewertet |
| `Übertragungsfunktion:` / `Zähler:` / `Nenner:` | Textfelder | Rationale Syntax | Mathematische Quelle | Passende Eingabeform | Leer, ungültige Syntax, implizite Multiplikation |
| `Aufgabenname / LaTeX-Überschrift:` | Textfeld | Freitext | Optionale LaTeX-Überschrift | Außerhalb Berechnung | Keine Fachwirkung |
| `Hauptvariable:` | Textfeld | Üblicherweise `s` | Legt Hauptvariable fest | Außerhalb Berechnung | Variable nicht erlaubt |
| `Parameter und exakte Belegungen:` | Tabelle `Parameter`, `Zähler`, `Nenner` | Name und rationaler Wert als Zähler/Nenner | Deklariert/substituiert Parameter | Zeilen über Schaltflächen | Doppelte/ungültige Namen oder ungültige Bruchteile |
| `Zeile hinzufügen` / `Ausgewählte Zeile entfernen` | Schaltflächen | — | Ändert Parametertabelle | Außerhalb Berechnung | Keine Auswahl beim Entfernen |
| `Berechnen` / `Zurücksetzen` | Schaltflächen | — | Startet bzw. leert Workflow | Nicht laufend | Ungültiger Request wird nicht gestartet |
| `Plaintext` / `LaTeX-Quelltext` | Bericht-Tabs | Auswahl | Wählt kopierbaren Bericht | Nach Ergebnis | LaTeX ist Quelltext, keine Vorschau |
| `Aktiven Bericht kopieren` | Schaltfläche | — | Kopiert aktiven Bericht | Bericht vorhanden | Bei fehlender Ausgabe deaktiviert |
| `Technische Details` | Umschalter | — | Zeigt technische Diagnose | Immer | Nicht mit Fachlösung verwechseln |

**Ausgaben:** Stufenbaum `Parse`, `Raw-Transferfunktion`, `Reduktion`, `Wurzelanalyse`, `Stabilitätsanalyse`; Ergebnisfelder für Übertragungsfunktion, Nullstellen, Pole, Stabilität, dynamisches Verhalten, Voraussetzungen und Definitionsausschlüsse; Plaintext- und LaTeX-Bericht. In der primären Ergebnisfolge stehen Polgleichung und exakte Pole vor den numerischen Polwerten. Numerische Real- und Imaginärteile werden nur für die Darstellung auf höchstens sechs signifikante Stellen gerundet; abschließende Nullen und numerisches `-0` entfallen. Exakte Ausdrücke bleiben unverändert. Die numerische Gegenprüfung ordnet Kandidaten unabhängig von ihrer Lieferreihenfolge und unter Beachtung der Vielfachheiten den exakten Wurzeln zu. Eine Näherungszeile entfällt, wenn sie gegenüber einem bereits exakten gaußschen ganzzahligen Pol keine zusätzliche Information liefert. Identische Workflow-Hinweise erscheinen im Hauptbericht nur einmal; die technischen Details bewahren die vollständigen Einträge.

**Qualitative Polinterpretation:** `Das E/A-Verhalten enthält einen gedämpft schwingenden Anteil.` bedeutet, dass das asymptotisch stabile reduzierte E/A-Modell mindestens ein sicher erkanntes konjugiert-komplexes Polpaar mit negativem Realteil besitzt; bei zusätzlichen stabilen reellen Polen wird damit keine reine Zweipolschwingung behauptet. `Das E/A-Verhalten ist aperiodisch.` wird nur bei einem asymptotisch stabilen reduzierten E/A-Modell mit ausschließlich reellen Polen in der linken Halbebene ausgegeben. Bei instabilen, imaginärachsennahen oder unbestimmten Polstrukturen sowie unbelegten Parametern wird keine dieser stabilen Standardklassifikationen behauptet.

**Grenzen:** Rohe und reduzierte Modelle sind getrennt zu lesen. Eine erfolgreiche Kürzung eines nichtkonstanten gemeinsamen Faktors in der Hauptvariablen kann interne Dynamik entfernen; nur für einen solchen strukturiert dokumentierten Polynomfaktor weist der Bericht darauf hin, dass sich Stabilität und qualitative Aussage auf die reduzierte E/A-Übertragungsfunktion beziehen. Reine Zahlenfaktoren, Vorzeichenwechsel und kanonische Skalierungen lösen diesen Hinweis nicht aus. Ungelöste Parameter können statt einer definitiven Aussage ein unbestimmtes Ergebnis liefern. Das Modul bestimmt keine allgemeinen Zeitkennwerte wie Dämpfungsmaß, Eigenkreisfrequenz, Überschwingweite oder Einschwingzeit und besitzt keinen zustandsbehafteten Zwei-System-Vergleich.

### Frequenzbereich

**Status:** `PARTIAL`

**Zweck:** Berechnet einen Frequenzpunkt oder einen numerischen Bode-Workflow einschließlich Standardgliedzerlegung, Reserven und Nyquist-Auswertung.

**Navigation:** Tab `Frequenzbereich`.

**Interaktive Elemente:**

| Sichtbare Bezeichnung | Typ | Erwartete Eingabe/Auswahl | Wirkung | Aktivierungsbedingung | relevanter Fehlerfall |
|---|---|---|---|---|---|
| Übertragungsfunktions-, Variablen- und Parameterfelder | Wie im Modul Transferfunktion | Rationale Syntax | Bereitet reduzierte Funktion vor | Nicht laufend | Gleiche Parserfehler |
| `Modus:` | Auswahl | `Einzelpunkt`, `Bode` | Schaltet Frequenzfelder und Ergebnistabs | Nicht laufend | Einzelpunkt erzwingt Hauptphase |
| `Kreisfrequenz ω:` | Textfeld | Nichtnegative exakte rationale Zahl | Einzelpunktauswertung | Nur Einzelpunkt | `0.5` wird abgelehnt; `1/2` verwenden |
| `ω_min:` / `ω_max:` | Textfelder | Positive rationale Grenzen | Bode-Bereich | Nur Bode | Es muss `0 < ω_min < ω_max` gelten |
| `Phasendarstellung:` | Auswahl | `Hauptphase`, `Hauptphase und entfaltete Phase` | Zusätzliche kontinuierliche Phase | Nur Bode | Entfaltung ist Zusatzdarstellung, keine neue physikalische Phase |
| `Skalarverstärkungsbereich G₀(s,K)=K·Ḡ(s)` und offene K-Grenzen | Checkbox/Textfelder | Optionaler K-Bereich | Berechnet stabile K-Intervalle im Nyquist-Kontext | Nur Bode, Grenzen bei gesetzter Checkbox | Obere Grenze muss größer sein |
| `Erweiterte Rastereinstellungen` | Gruppe | 1–64 Punkte/Dekade; optionale rationale Frequenzliste | Steuert numerisches Raster | Nur Bode | Max. 256 explizite Punkte; insgesamt begrenzt |
| `Frequenzbereich berechnen` / `Zurücksetzen` | Schaltflächen | — | Start/Reset | Nicht laufend | Requestfehler fokussiert Feld |
| `Darstellung:` | Auswahl | `Exakter Verlauf`, `Asymptotische Näherung`, `Grobe Klausurskizze` | Wählt gezeichnete Kurven | Bode-Ergebnis mit unterstützter Standardgliederzerlegung; sonst auf exakten Verlauf deaktiviert | Näherungen nur aus erkannten Komponenten |
| `Einzelbeiträge anzeigen` / `Gesamtfunktion anzeigen` | Checkboxen | Sichtbarkeit | Blendet Kurven ein/aus | Bode-Ergebnis | Kein neuer Rechenlauf |
| `Tabellenumfang:` | Auswahl | `Kompakt`, `Vollständiges Raster` | Projiziert die sichtbare Wertetabelle und den aktuellen LaTeX-Bericht | Bode-Ergebnis | Standard nach Reset ist `Kompakt`; der Wechsel startet keine neue Berechnung |
| Ergebnis-Tabs | Tabs | `Ergebnisübersicht`, `Wertetabelle`, `Diagramme`, `Durchtritte und Reserven`, `Nyquist`, `Numerische Kurzlösung`, `LaTeX-Lösung`, `Diagnosen` | Wählt Darstellung | Modus-/Ergebnisabhängig | Einzelpunkt blendet Bode-Tabs aus |
| `Technische Details anzeigen` / `LaTeX kopieren` | Checkbox/Schaltfläche | — | Ergänzt Details bzw. kopiert | Ergebnis vorhanden | Technische Details sind nicht der klausurtaugliche Kern |

**Ausgaben:** Exakte/numerische Punktwerte, Ziel- und Auswertungsfrequenzen, standardmäßig kompakte Bode-Tabelle, optionales Vollraster, Betrag/Phase auf derselben logarithmischen Frequenzachse mit identischen Grenzen und Ticks, Standardgliedtabelle, Singularitätslücken, alle erkannten Durchtritte und Reserven, Nyquist-Kriterium, numerische Kurzlösung und LaTeX. Die kompakte Tabelle enthält Randpunkte, den ausgewählten Punkt, explizite und automatisch ergänzte Frequenzen, singuläre/nicht definierte Punkte sowie den jeweils logarithmisch nächsten bereits berechneten Rasterpunkt zu Durchtritten; weitere Zeilen werden repräsentativ verteilt. Ein solcher Rasterpunkt wird nicht als exakter Durchtritt ausgegeben. Amplituden- und Phasendurchtrittsmarker werden einheitlich als `ωg1`, `ωg2`, … beziehungsweise `ωp1`, `ωp2`, … bezeichnet.

**Grenzen:** `ω_min` und `ω_max` werden nicht aus der Aufgabe erfunden. Standardglieder und asymptotische Darstellungen hängen von erkannter Zerlegung ab. Bei einer nicht unterstützten Zerlegung bleibt ausschließlich der exakte Verlauf verfügbar; der Darstellungsumschalter und die nicht vorhandenen Einzelbeiträge werden deaktiviert und die Ursache wird sichtbar genannt. LaTeX nennt das betroffene Glied beziehungsweise den Fall, erklärt den Abbruch der vollständigen Standardgliederanalyse und weist in umbrechbarer Prosa auf weiter verwendbare numerische Frequenzgangresultate hin. Die Frequenz-Wertetabelle verwendet `longtable`; die einbindende LaTeX-Vorlage benötigt deshalb `\usepackage{longtable}`. Definierte Frequenzpunkt-Endergebnisse werden als mehrzeilige `aligned`-Box mit je einer Zeile für \(G(j\omega)\), Betrag, dB-Wert und Phase ausgegeben. Die Ansicht erklärt ausdrücklich, dass die numerischen Worked Steps keine vollständige asymptotische Bode-Konstruktion sind.

### Stabilität

**Status:** `PARTIAL`

**Zweck:** Führt Hurwitz- oder Routh-Analyse für ein charakteristisches Polynom oder den ausgewählten rohen/reduzierten Nenner einer Führungsübertragungsfunktion aus.

**Navigation:** Tab `Stabilität`.

**Interaktive Elemente:**

| Sichtbare Bezeichnung | Typ | Erwartete Eingabe/Auswahl | Wirkung | Aktivierungsbedingung | relevanter Fehlerfall |
|---|---|---|---|---|---|
| `Eingabeart:` | Auswahl | `Charakteristisches Polynom`, `Führungsübertragungsfunktion` | Schaltet Semantik und sichtbare Rolle | Nicht laufend | Zustandsstabilität ist bei TF-Eingabe unzulässig |
| `Verfahren:` | Auswahl | `Hurwitz`, `Routh` | Wählt Analyse | Nicht laufend | Sonderfälle können nur teilweise aufgelöst werden |
| `Polynom:` / `Führungsübertragungsfunktion:` | Textfeld | Polynom bzw. rationale TF | Analysequelle | Nicht laufend | Nicht-rationale TF wird abgelehnt |
| `Variable:` / `Entscheidungsparameter:` | Textfelder | `s`; maximal zwei Namen | Symbolkontext | Nicht laufend | Ungültige Namen/mehr als zwei Parameter |
| `Annahmen:` | Textfeld | Relationen, `;` oder Zeilen | Beschränkt Parameterbereich | Nicht laufend | `Relation nicht unterstützt.` |
| `Polynomrolle:` | Auswahl | Vier sichtbare Rollen | Dokumentiert Modellbedeutung | Direkte Polynomeingabe | Rolle/Analyseziel müssen konsistent sein |
| `Analyseziel:` | Auswahl | intern, E/A, Zustand | Wählt Stabilitätsbegriff | Nicht laufend | Falsches Ziel analysiert falsches Modell |
| `Provenienznotiz:` / `Kürzungsstatus/-hinweis:` | Textfelder | Freitext | Ergänzt Bericht | Modusabhängig | Keine automatische fachliche Verifikation |
| `Hurwitz analysieren` bzw. `Routh analysieren`, `Zurücksetzen`, `LaTeX kopieren` | Schaltflächen | — | Start/Reset/Kopieren | Nicht laufend bzw. LaTeX vorhanden | Bei nicht gelöstem Sonderfall kein kopierbares LaTeX |
| Ergebnis-Tabs | Tabs | Übersicht, Gradfälle, `Hurwitz-Bedingungen und Rechenweg`, Routh, Bedingungen/Bereich, `Kurzlösung`, Worked Steps, LaTeX, Diagnosen | Wählt Ausgabe | Verfahrensabhängig | Nicht verwendetes Verfahren wird ausgeblendet |

**Ausgaben:** Kanonisches Polynom und Gradfälle, bei Hurwitz getrennte notwendige Koeffizienten- und hinreichende Determinantenbedingungen, Redundanzmarkierungen, minimales Bedingungssystem, Schnittmenge und exaktes Gebiet; alternativ ein kompaktes Routh-Schema als zusammenhängende LaTeX-Tabelle, numerische Kontrolle, Worked Steps, LaTeX und Diagnosen. Die Hurwitz-Kurzlösung nennt zuerst notwendige Bedingungen, dann hinreichende Zusatzbedingungen und das exakte Gebiet; die numerische Kontrolle folgt nachrangig. Parameterfreie Hurwitz-Fälle zeigen `Keine zusätzlichen Parameterbedingungen.` statt einer CAS-Wahrheitskonstante.

**Grenzen:** Höchstens zwei Entscheidungsparameter. Direkte Polynomeingabe bildet keinen Regelkreis. Bei Führungsübertragungsfunktion wählt `Interne asymptotische Stabilität` den rohen Nenner, `E/A-asymptotische Stabilität` den reduzierten Nenner. Stabilitätsgrenzen sind strikt offen. Die Redundanzklassifikation beweist nur positive Konstanten, symbolische Gleichheit, sicher positive Proportionalität und unterstützte affine stärkere Grenzen; nicht sicher beweisbare Fälle bleiben aktiv oder werden als sicher ungelöst gekennzeichnet.

### Zeitbereich

**Status:** `PARTIAL`

**Zweck:** Bündelt direkte/inverse Laplace-Transformation, PBZ, Nullzustandsantworten sowie einen strukturierten DGL-/Anfangswertworkflow.

**Navigation:** Tab `Zeitbereich`.

**Interaktive Elemente:**

| Sichtbare Bezeichnung | Typ | Erwartete Eingabe/Auswahl | Wirkung | Aktivierungsbedingung | relevanter Fehlerfall |
|---|---|---|---|---|---|
| `Aufgabentyp:` | Auswahl | Sieben sichtbare Aufgabentypen | Schaltet relevante Felder | Immer | Falscher Typ führt zu falschem Parserprofil |
| `f(t):`, `F(s):`, `G(s):`, `U(s):` | Textfelder | Zeit- bzw. Bildprofil | Quellausdruck | Modusabhängig | Gemischte Variable/Funktion nicht erlaubt |
| `Sprunghöhe A:`, Exponentialamplitude/-exponent | Textfelder | Exakte Skalare | Baut Eingang automatisch | Passender Antwortmodus | Ungültiger Skalar |
| DGL-Namen, Ordnungen, Koeffizienten | Felder/Auswahl | Ordnung Ausgang 1–4, Eingang 0–4 | Baut strukturierte lineare DGL | DGL-Modi | Zeitvariable Koeffizienten abgelehnt |
| `Eingangsart:` | Auswahl | Nullsignal, Sprung, Exponential, Polynom, Sinus, Kosinus, Direkte Eingabe `U(s)` | Baut Eingangssignal | `Lineare DGL lösen` | Für Sinus/Kosinus muss `omega > 0` gelten/angenommen sein |
| `Analyseziel:` | Auswahl | Bildgleichung, `Y(s)`, PBZ von `Y(s)`, vollständige Zeitantwort | Beendet den DGL-Workflow an der gewählten Zielstufe; Standard ist `Vollständige Zeitantwort y(t)` | Nur `Lineare DGL lösen` | Nicht erreichte Folgestufen werden weder berechnet noch angezeigt |
| `Amplitude A:`, `Exponent lambda:`, `Kreisfrequenz omega:`, Polynomkoeffizienten | Textfelder | Exakte signalabhängige Parameter | Baut den gewählten DGL-Eingang | Nur für den jeweiligen Signaltyp | Ausgeblendete Felder werden nicht ausgewertet |
| `Bildbereichseingang U(s):` | Textfeld | Rationaler Ausdruck in `s`, z. B. `1/s` | Direkte DGL-Anregung im Bildbereich | Nur `Direkte Eingabe U(s)` | Kein Amplitudenfeld aktiv; ungültige Eingabe wird feldbezogen gemeldet |
| Anfangswertfelder | Textfelder | Werte bei `0+` | Bestimmt freien Anteil | `Lineare DGL lösen` | Fehlende benötigte Werte blockieren |
| `Nicht angegebene Anfangswerte ausdrücklich als 0 setzen` | Checkbox | Bestätigung | Ergänzt fehlende Anfangswerte als null | `Lineare DGL lösen` | Nicht stillschweigend gesetzt |
| `Vollständigen Nullzustand ausdrücklich bestätigen` | Checkbox | Bestätigung | Erlaubt TF aus DGL | `Übertragungsfunktion aus DGL` | Ohne Bestätigung wird abgelehnt |
| `Zeitbereich berechnen`, `Zurücksetzen`, `LaTeX kopieren` | Schaltflächen | — | Start/Reset/Kopieren | Ergebnisabhängig | Fehlerausgabe ersetzt Resultate |
| Ergebnis-Tabs | Tabs | Übersicht, DGL/Anfangswerte, Laplace, Bildgleichung, freie/erzwungene Antwort, rationale Analyse, PBZ, Zeitfunktion, Kontrollen, Kurzlösung, Worked Steps, LaTeX, Diagnosen | Wählt Ausgabe | Ziel- und ergebnisabhängig | Nur fachlich erreichte Register sind sichtbar; `Zeitfunktion` erst beim vollständigen Zeitziel |

**Ausgaben:** Rationale Klassifikation, Polynomdivision/PBZ, Zeitfunktion, DGL-Transformation, freie und erzwungene Antwort, Endwert- und Residuenkontrollen, Kurzlösung, Worked Steps und LaTeX.

**Grenzen:** Direkte Laplace-Transformation arbeitet mit einem begrenzten Regelvorrat. Uneigentliche inverse Fälle werden nach Polynomdivision als nicht weiter unterstützt markiert. DGL-Koeffizienten müssen zeitunabhängig sein.

### Zustandsraum

**Status:** `PARTIAL`

**Zweck:** Erzeugt eine Regelungsnormalform aus strukturierter DGL und analysiert wahlweise die Zustandsstabilität als Hauptworkflow oder führt die vollständige Zustandsraum- und Übertragungsfunktionsanalyse aus.

**Navigation:** Tab `Zustandsraum`.

**Interaktive Elemente:**

| Sichtbare Bezeichnung | Typ | Erwartete Eingabe/Auswahl | Wirkung | Aktivierungsbedingung | relevanter Fehlerfall |
|---|---|---|---|---|---|
| `Aufgabentyp:` | Auswahl | `DGL → Regelungsnormalform`, `Zustandsraum → Übertragungsfunktion` | Schaltet Eingaben | Immer | — |
| `Analyseziel:` | Auswahl | `Vollständige Analyse`, `Zustandsstabilität` | Projiziert Gesucht, Tabs, Worked Steps und LaTeX auf das gewählte Ziel; Standard nach Reset ist `Vollständige Analyse` | Immer | Das Analyseziel ändert nicht den vorhandenen mathematischen Kern |
| Ausgangs-/Eingangsname, Ausgangsordnung, `a_0…a_4`, `b_0` | Felder/Auswahl | Ordnung 1–4, exakte Koeffizienten | Baut DGL und Normalform | DGL-Modus | Nur nicht abgeleiteter Eingang; führender Koeffizient muss sicher ungleich null sein |
| `Matrix A:`, `Vektor b:`, `Vektor c^T:`, `Skalar d:` | Textfelder | Komma-/Semikolonmatrix | Baut SISO-Modell | Matrixmodus | Dimensionen müssen `n×n`, `n×1`, `1×n`, `1×1` sein |
| `Entscheidungsparameter:` / `Annahmen:` | Textfelder | Namen/Relationen | Parametrische Stabilitätsanalyse | Modusabhängig | Ungültige Namen oder unzureichende Annahmen |
| `Vorschau:` | Anzeige | — | Zeigt DGL bzw. Dimensionen | Eingabeabhängig | Nur Vorschau, keine Berechnung |
| `Zustandsraum analysieren`, `Zurücksetzen`, `LaTeX kopieren` | Schaltflächen | — | Start/Reset/Kopieren | LaTeX nur bei Erfolg | Fehler leert fachliche Ausgabe |
| Ergebnis-Tabs | Tabs | Übersicht, normalisierte DGL/Zustandswahl, Matrizen, charakteristisches Polynom, Eigenwerte/Stabilität, Übertragungsfunktion, Kontrollen, Worked Steps, LaTeX, Diagnosen | Wählt Ausgabe | Ziel- und ergebnisabhängig | Bei `Zustandsstabilität` ist `Übertragungsfunktion` ausgeblendet und nach Erfolg `Eigenwerte und Stabilität` aktiv |

**Ausgaben:** Beide Ziele zeigen die gebildete Matrix, die sichtbare Determinantenbildung, das charakteristische Polynom und exakte Eigenwerte vor einer numerischen Zusatzkontrolle. Direkte Matrixaufgaben verwenden `sI-A`; im Stabilitätsziel des DGL-Pfads wird die Regelungsnormalform als `sI-A_R` bezeichnet. Die konkrete 2×2-Rechnung schreibt Multiplikationen in Plaintext mit `*` und in LaTeX mit `\cdot`; das Polynom wird nach absteigenden Potenzen von `s` geordnet. Konjugierte Paare werden kompakt dargestellt, etwa `λ_{1,2}=±j` statt `0±j1`. Bei `Zustandsstabilität` folgen das strikte Kriterium `Re(λ_i) < 0`, die konkreten Realteilprüfungen, gegebenenfalls eindeutig bezeichnete verletzende Eigenwerte und genau die Zustandsstabilitätsaussage beziehungsweise das Parametergebiet als primäres Endergebnis. Bei freien Entscheidungsparametern weist die Eigenwertausgabe auf die parameterabhängigen Eigenwerte und die Stabilitätsentscheidung mit dem Hurwitz-Kriterium hin; Parameter werden in LaTeX mathematisch gesetzt. Übertragungsfunktion, Resolvente, E/A-Pole/-Nullstellen und verborgene Modi werden in diesem Ziel nicht sichtbar projiziert. `Vollständige Analyse` behält diese E/A-Ausgaben und Kontrollen bei.

**Grenzen:** SISO und Dimension 1–4. Die Matrixeingabe ist keine grafische Blockschaltbildeingabe. E/A-Stabilität der reduzierten Funktion und Zustandsstabilität können wegen verborgener Modi voneinander abweichen. Ein Eigenwert auf der imaginären Achse erfüllt das strikte Kriterium nicht und wird daher als nicht asymptotisch stabil ausgegeben; ohne separate Jordanblockanalyse wird nicht automatisch „grenzstabil“ behauptet. Bei Entscheidungsparametern werden keine numerischen Eigenwerte erfunden, sondern die Bedingungen des vorhandenen Hurwitz-/Parameterkerns ausgegeben. Eine allgemeine Jordanformanalyse erfolgt nicht.

### Reglerauslegung

**Status:** `PARTIAL`

**Zweck:** Berechnet einen P-Faktor für eine Zielphasenreserve oder P/PI/PID-Parameter nach drei sichtbaren Tabellenverfahren.

**Navigation:** Tab `Reglerauslegung`.

**Interaktive Elemente:**

| Sichtbare Bezeichnung | Typ | Erwartete Eingabe/Auswahl | Wirkung | Aktivierungsbedingung | relevanter Fehlerfall |
|---|---|---|---|---|---|
| `Verfahren:` | Auswahl | P-Phasenreserve, Ziegler–Nichols offen/geschlossen, Cohen–Coon | Schaltet Felder | Nicht laufend | Quellenbereich abhängig vom Verfahren |
| `Reglertyp:` | Auswahl | `P`, `PI`, `PID` | Wählt Tabellenzeile | Tabellenverfahren | P-Phasenreserve erzwingt P |
| `Zähler:`, `Nenner:`, `Parameterbelegungen:` | Textfelder | Strecke in getrennter rationaler Form | Frequenzbasierte P-Auslegung | Nur P-Phasenreserve | Ungelöste Parameter unzulässig |
| `Zielphasenreserve [deg]:`, `ω_min`, `ω_max`, `Punkte pro Dekade` | Textfelder | `0 < Φ_R < 180`, positiver Bereich | Numerische Suche und Nachrechnung | Nur P-Phasenreserve | Zielphase nicht erreicht/mehrere Kandidaten |
| `K_S:`, `K_T [s]:`, `T [s]:` | Textfelder | Positive reine Zahlen | Offene ZN/Cohen–Coon | Passendes Verfahren | Keine Einheiten im Feld; Quellenbereich verletzt |
| `K_crit:`, `T_crit [s]:` | Textfelder | Positive reine Zahlen | Geschlossene ZN-Auslegung | Geschlossene ZN | Ungültige/nichtpositive Werte |
| `Vorschau:` | Anzeige | — | Zeigt Zielphase oder Verfahren | Immer | — |
| `Reglerauslegung berechnen`, `Zurücksetzen`, `LaTeX kopieren` | Schaltflächen | — | Start/Reset/Kopieren | Nicht laufend/LaTeX vorhanden | Bei Fehler kein altes LaTeX kopierbar |
| Ergebnis-Tabs | Tabs | Übersicht, Verfahren/Eingaben, Formel und Einsetzen, Reglerparameter, Frequenznachprüfung, Kontrollen, Worked Steps, LaTeX, Diagnosen | Wählt Ausgabe | Ergebnisabhängig | — |

**Ausgaben:** Verfahrensdaten, konkrete Quellenbereichsprüfung mit ausdrücklicher Bewertung, allgemeine Formel vor der Einsetzung, exakte Werte vor optionalen Näherungen, parallele Reglerform als primäres Ergebnis, äquivalente Idealform, vollständige Kandidaten-/Frequenznachprüfung, Kontrollen, Worked Steps und LaTeX. Der Frequenztab zeigt Zielphase, Betrag, eingesetzten P-Faktor, neuen offenen Kreis, Durchtritt, globale Reserve und den tatsächlichen Nyquist-Kontrollstatus. Strukturierte interne Diagnosecodes bleiben im Ergebnisvertrag, die sichtbare Diagnose zeigt ausschließlich die verständliche Nachricht. Symbollegenden sind methodenabhängig; `K_S` bezeichnet die Streckenverstärkung, `k_P` den Proportionalbeiwert des Reglers.

**Grenzen:** P-Phasenreserve ist numerisch und kann eine manuelle Kandidatenauswahl verlangen. Ziegler–Nichols offen gilt hier nur für `K_T/T < 0,5`, Cohen–Coon nur für `0 < K_T/T < 2`. Die App bildet nicht automatisch eine Strecke aus einem Blockschaltbild. Totzeit-Frequenzrechnung und Lead-Auslegung bleiben nicht unterstützt.

## 7. Workflow-Karten

### WF-01: Übertragungsfunktion reduzieren, Pole/Nullstellen und E/A-Stabilität

- **Status:** `UI_VERIFIED`
- **Geeigneter Aufgabentyp:** Rationale SISO-Übertragungsfunktion.
- **Modul/Ansicht:** `Transferfunktion`.
- **Voraussetzungen:** Hauptvariable und verwendete Parameter korrekt deklarieren.
- **Eingaben:** Gemeinsamer Ausdruck oder getrennte Felder; optionale exakte Parameterbelegungen.
- **Akzeptierte Syntax:** Rationale sichere Syntax mit explizitem `*`, `^`/`**`, Klammern und Brüchen.
- **Gültiges Beispiel:** `1/(s+1)`
- **Bedienfolge:** 1. Eingabeform wählen. 2. Ausdruck eingeben. 3. `Berechnen` wählen. 4. Stufen, Ergebnis und Bericht lesen.
- **Interne Interpretation:** Bewahrt rohe Struktur, bildet rohe TF, kürzt algebraisch, analysiert rohe/reduzierte Wurzeln; sichtbare Stabilitäts- und Dynamikaussagen nutzen das reduzierte E/A-Modell.
- **Automatische Schritte:** Parse, Rohmodell, Reduktion, Wurzel- und Stabilitätsanalyse, sichere qualitative Polinterpretation, Plaintext/LaTeX.
- **Sichtbare Ergebnisse:** Rohe/reduzierte TF, Nullstellen, Polgleichung, exakte Pole, kompakte numerische Polwerte, Stabilität, dynamisches Verhalten sowie nachrangig Voraussetzungen, Definitionsausschlüsse und Reduktionsprotokoll.
- **Manuelle Vorarbeit:** Richtige offene/geschlossene Übertragungsfunktion aus der Aufgabe bilden.
- **Manuelle Nacharbeit/Kontrolle:** Kürzungen und verborgene interne Modi gesondert beurteilen.
- **Typische Fehlbedienung:** `2s` statt `2*s`; Parameter benutzt, aber nicht deklariert.
- **Bekannte Grenze:** Interne und E/A-Stabilität sind hier kein auswählbares Paar; dafür `Stabilität` verwenden. Es gibt weder allgemeine Zeitkennwerte noch einen Zwei-System-Vergleich.
- **Nachweis:** `ui/transfer_function_workspace.py`, `application/transfer_function_workflow_service.py`; `tests/ui/test_main_window.py`, `tests/application/test_transfer_function_workflow_service.py`.

### WF-02: Numerischer Frequenzgang an einem Punkt

- **Status:** `UI_VERIFIED`
- **Geeigneter Aufgabentyp:** `G(jω)` bei gegebener Kreisfrequenz.
- **Modul/Ansicht:** `Frequenzbereich`, Modus `Einzelpunkt`.
- **Voraussetzungen:** Vollständig numerisch spezialisierbare TF für Zahlenwerte.
- **Eingaben:** TF und nichtnegative exakte rationale `ω`.
- **Akzeptierte Syntax:** TF wie WF-01; Frequenz z. B. `1`, `3/2`.
- **Gültiges Beispiel:** TF `1/(s+1)`, `ω = 1`.
- **Bedienfolge:** 1. `Einzelpunkt` wählen. 2. TF und `Kreisfrequenz ω` eingeben. 3. `Frequenzbereich berechnen`.
- **Interne Interpretation:** Setzt `s=jω` in die reduzierte TF ein.
- **Automatische Schritte:** Exakte Spezialisierung sowie numerische Betrag-, dB- und Phasendarstellung.
- **Sichtbare Ergebnisse:** `G(jω)`, Realteil, Imaginärteil, Betrag, dB, Hauptphase und Punktstatus.
- **Manuelle Vorarbeit:** Hz gegebenenfalls in rad/s umrechnen.
- **Manuelle Nacharbeit/Kontrolle:** Quadrant und Einheit prüfen.
- **Typische Fehlbedienung:** `0.5` statt `1/2`.
- **Bekannte Grenze:** Unbelegte Parameter erzeugen ggf. `Symbolisch unbestimmt`.
- **Nachweis:** `ui/frequency_domain_workspace.py`, `application/frequency_domain_workflow_service.py`; `tests/ui/test_main_window.py`, `tests/application/test_frequency_domain_workflow_service.py`.

### WF-03: Bode, Standardglieder, Durchtritte, Reserven und Nyquist

- **Status:** `PARTIAL`
- **Geeigneter Aufgabentyp:** Numerische Frequenzanalyse einer rationalen TF.
- **Modul/Ansicht:** `Frequenzbereich`, Modus `Bode`.
- **Voraussetzungen:** Positive Frequenzgrenzen; alle für Bode-Zahlenwerte und Nyquist benötigten Parameter sind numerisch belegt.
- **Eingaben:** TF, `ω_min`, `ω_max`, Raster, Phase; optional K-Bereich.
- **Akzeptierte Syntax:** Exakte rationale Grenzen/Liste; TF wie WF-01.
- **Gültiges Beispiel:** `100/(s*(10*s+1))`, `ω_min=1/10`, `ω_max=10`.
- **Bedienfolge:** 1. `Bode` wählen. 2. TF und Grenzen eingeben. 3. Phase/Raster wählen. 4. Berechnen. 5. Ergebnis-Tabs prüfen. 6. Bei Bedarf unter `Tabellenumfang:` ohne Neuberechnung auf `Vollständiges Raster` wechseln.
- **Interne Interpretation:** Reduziertes Modell; Hauptphase und optional zusätzliche entfaltete Phase.
- **Automatische Schritte:** Lograster, Singularitätsverfeinerung, Bode-Komponenten, Durchtritte/Reserven, Nyquist, Diagramme.
- **Sichtbare Ergebnisse:** Kompakte Wertetabelle (höchstens zwölf Zeilen, solange nicht mehr Pflichtpunkte vorliegen), optionales Vollraster, exakter/asymptotischer/grober Plot mit gemeinsamer logarithmischer Betrag-/Phasenachse, Marker `ωg1`/`ωp1`, Standardgliedtabelle, Reserven, Nyquist und LaTeX-`longtable`.
- **Manuelle Vorarbeit:** Diagrammgrenzen aus Aufgabenstellung bestimmen.
- **Manuelle Nacharbeit/Kontrolle:** Asymptoten und qualitative Skizze fachlich prüfen und papiergerecht zeichnen.
- **Typische Fehlbedienung:** Hauptphase mit entfalteter Phase verwechseln; zu grobes Raster als exakte Kurve interpretieren; einen verwendeten Parameter wie `K` deklarieren, aber für den numerischen Nyquist-Lauf nicht belegen.
- **Fehlende Parameterbelegung:** Die numerische Nyquist-Auswertung und der Nyquist-Plot werden nicht gestartet, es wird kein Ersatzwert für `K` angenommen. Eine Diagnose fordert zur numerischen Belegung auf; bereits mögliche symbolische Bode- und LaTeX-Teilresultate bleiben sichtbar.
- **Bekannte Grenze:** Numerische Kurzlösung ersetzt keine vollständige asymptotische Bode-Konstruktion.
- **Nachweis:** `ui/frequency_domain_workspace.py`, `application/frequency_domain_workflow_service.py`; `tests/ui/test_frequency_domain_workspace.py`, `tests/ui/test_frequency_reserve_presenter_smoke.py`.

### WF-04: Hurwitz aus charakteristischem Polynom

- **Status:** `UI_VERIFIED`
- **Geeigneter Aufgabentyp:** Interne/E/A-/Zustandsstabilität eines bereits hergeleiteten Polynoms.
- **Modul/Ansicht:** `Stabilität`, `Charakteristisches Polynom`, `Hurwitz`.
- **Voraussetzungen:** Polynomrolle und Analyseziel fachlich festlegen.
- **Eingaben:** Polynom, Variable, bis zu zwei Parameter, Annahmen, Rolle und Ziel.
- **Akzeptierte Syntax:** Polynomsyntax; Annahmen z. B. `T1 > 0; TI > 0`.
- **Gültiges Beispiel:** `s^3+4*s^2+5*s+K_P`, Parameter `K_P`.
- **Bedienfolge:** 1. Eingabeart/Verfahren wählen. 2. Felder ausfüllen. 3. `Hurwitz analysieren`.
- **Interne Interpretation:** Kanonisiert Koeffizienten und Gradfälle unter gewählter Semantik.
- **Automatische Schritte:** Koeffizientenvergleich, notwendige Bedingungen mit Einsetzung und Lösung, sichere Redundanzklassifikation, Hurwitz-Matrix, hinreichende Determinantenbedingungen, minimales Bedingungssystem, Schnittmenge, exaktes Gebiet und numerische Kontrolle.
- **Sichtbare Ergebnisse:** Für das Beispiel zunächst `K_P > 0`, dann `20-K_P > 0 ⇔ K_P < 20` und als primäres exaktes Ergebnis strikt `0 < K_P < 20`; Matrix und Determinanten bleiben im Rechenweg sichtbar. Bei positiven Voraussetzungen werden diese unter `Voraussetzungen` dokumentiert, aber nicht unnötig in der primären Endbox wiederholt; im quartischen Referenzfall lautet sie nur `TI > 9*T1/2`.
- **Manuelle Vorarbeit:** Charakteristisches Polynom korrekt herleiten.
- **Manuelle Nacharbeit/Kontrolle:** Gradwechsel und Annahmen gegen Aufgabe prüfen.
- **Typische Fehlbedienung:** Falsche Polynomrolle oder falsches Analyseziel.
- **Bekannte Grenze:** Mehr als zwei Entscheidungsparameter werden abgelehnt; die Redundanzprüfung ist bewusst kein allgemeiner logischer Implikationsbeweiser.
- **Nachweis:** `ui/stability_workspace.py`, `application/stability_workflow.py`; `tests/ui/test_stability_presenter.py`, `tests/domain/test_hurwitz_analyzer.py`, `tests/domain/test_hurwitz_explicit_conditions.py`.

### WF-05: Routh aus charakteristischem Polynom

- **Status:** `PARTIAL`
- **Geeigneter Aufgabentyp:** Routh-Schema, RHP-Polzahl und Parameterbereich.
- **Modul/Ansicht:** `Stabilität`, `Charakteristisches Polynom`, `Routh`.
- **Voraussetzungen:** Wie WF-04.
- **Eingaben:** Wie WF-04.
- **Akzeptierte Syntax:** Wie WF-04.
- **Gültiges Beispiel:** `s^3+4*s^2+5*s+K_P`, Parameter `K_P`.
- **Bedienfolge:** 1. `Routh` wählen. 2. Eingabe setzen. 3. `Routh analysieren`.
- **Interne Interpretation:** Erstes-Spalten-Kriterium und Vorzeichenwechsel auf kanonischem Polynom.
- **Automatische Schritte:** Schema, Zellableitungen, Bedingungen, numerische RHP-Kontrolle.
- **Sichtbare Ergebnisse:** Das Haupt-LaTeX zeigt das Routh-Schema kompakt als eine Tabelle mit den Zeilen `s^n` bis `s^0`, danach die strikt positive erste Spalte, den Bereich und die Polzahlen. Interne Zellindizes wie `r_{i,j}` bleiben aus dem Hauptbericht entfernt; Worked Steps bewahren die nachvollziehbare Rekursion. Für das Beispiel bleibt das Endgebiet strikt `0 < K_P < 20`.
- **Manuelle Vorarbeit:** Polynom herleiten.
- **Manuelle Nacharbeit/Kontrolle:** Nullzeilen-/Nullspalten-Sonderfall fachlich bearbeiten, falls Bericht unvollständig.
- **Typische Fehlbedienung:** Routh-RHP-Polzahl als E/A-Aussage lesen, obwohl rohes internes Polynom gewählt wurde.
- **Bekannte Grenze:** Bei vollständiger Nullzeile kann das Hilfspolynom nur diagnostiziert und LaTeX deaktiviert werden.
- **Nachweis:** `ui/stability_workspace.py`, `application/stability_workflow.py`; `tests/ui/test_stability_presenter.py`, `tests/domain/test_routh_analyzer.py`.

### WF-06: Stabilität aus Führungsübertragungsfunktion

- **Status:** `UI_VERIFIED`
- **Geeigneter Aufgabentyp:** Vergleich interner und E/A-asymptotischer Stabilität bei Kürzungen.
- **Modul/Ansicht:** `Stabilität`, `Führungsübertragungsfunktion`.
- **Voraussetzungen:** Führungs-TF muss bereits gebildet sein.
- **Eingaben:** Rationale TF, Parameter, `Hurwitz`/`Routh`, Analyseziel intern oder E/A.
- **Akzeptierte Syntax:** Rationale Syntax wie WF-01.
- **Gültiges Beispiel:** `(s+1)/(s+2)`.
- **Bedienfolge:** 1. Eingabeart wechseln. 2. TF eingeben. 3. Analyseziel wählen. 4. Verfahren starten.
- **Interne Interpretation:** Intern = roher Nenner; E/A = reduzierter Nenner; gemeinsame Faktoren werden berichtet. In der Kursnotation bezeichnet `Z(s)` den Zähler und `N(s)` den Nenner. Roh- und reduzierte Größen werden als `Z_roh(s)`, `N_roh(s)`, `Z_red(s)` und `N_red(s)` ausgewiesen. Bei exakt protokollierten, sicher analysierbaren linearen Faktoren wird die interne Region als Schnitt aus der Stabilität des verbleibenden Nenners und der Faktorbedingung geschlossen; für den entfernten Faktor `s+K` erscheint ausdrücklich `K > 0`.
- **Automatische Schritte:** TF-Vorbereitung, Kürzung, Nennerauswahl, Stabilitätsworkflow.
- **Sichtbare Ergebnisse:** Roh-/Reduktionsschritte, Kürzungsprotokoll, ausdrücklich gewählter roher oder reduzierter Nenner als Analyseobjekt, bei Hurwitz getrennte notwendige/hinreichende Bedingungen und exaktes Gebiet, sonst Routh-Schema und Bereich.
- **Manuelle Vorarbeit:** Richtige Führungsübertragungsfunktion bilden.
- **Manuelle Nacharbeit/Kontrolle:** Beide Ziele getrennt auswerten, wenn interne Modi relevant sind.
- **Typische Fehlbedienung:** `Zustandsstabilität` bei TF-Eingabe wählen.
- **Bekannte Grenze:** Nicht-rationale Eingabe und Zustandsziel werden abgelehnt. Das Gebiet des reduzierten E/A-Nenners beweist allein keine interne Stabilität; ein entfernter Modus bleibt im Kürzungsprotokoll sichtbar. Nur exakt bekannte, monische lineare Faktoren mit sicher formulierbarer Stabilitätsbedingung werden automatisch ergänzt. Bei anderen entfernten Faktoren bleibt die interne Region ehrlich teilweise gelöst.
- **Nachweis:** `ui/stability_workspace.py`, `application/stability_workflow.py`; `tests/application/test_stability_transfer_function_workflow.py`, `tests/ui/test_stability_presenter.py`.

### WF-07: Direkte Laplace-Transformation

- **Status:** `PARTIAL`
- **Geeigneter Aufgabentyp:** Standardpaare und unterstützte Summen/Produkte in `t`.
- **Modul/Ansicht:** `Zeitbereich`, `Direkte Laplace-Transformation`.
- **Voraussetzungen:** Ausdruck gehört zum implementierten Regelvorrat.
- **Eingaben:** `f(t)`.
- **Akzeptierte Syntax:** Zeitprofil mit `t`, `exp`, `sin`, `cos`, `pi`.
- **Gültiges Beispiel:** `2*t*exp(-4*t)`.
- **Bedienfolge:** 1. Aufgabentyp wählen. 2. `f(t)` eingeben. 3. `Zeitbereich berechnen`.
- **Interne Interpretation:** Exakte Regelzerlegung, kein beliebiger CAS-Aufruf.
- **Automatische Schritte:** Regelzuordnung und Bildfunktion.
- **Sichtbare Ergebnisse:** Laplace-Transformation, Worked Steps und LaTeX.
- **Manuelle Vorarbeit:** Ausdruck in unterstützte Standardform bringen.
- **Manuelle Nacharbeit/Kontrolle:** Konvergenz-/Fachvoraussetzungen unabhängig prüfen.
- **Typische Fehlbedienung:** `log(t)`, `s` oder implizite Multiplikation verwenden.
- **Bekannte Grenze:** Allgemeine Funktionen außerhalb des Regelvorrats nicht nachgewiesen.
- **Nachweis:** `ui/time_domain_workspace.py`, `application/time_domain_workflow.py`; `tests/parsing/test_time_domain_parser_profiles.py`, `tests/application/test_time_domain_workflow.py`.

### WF-08: Inverse Laplace-Transformation und PBZ

- **Status:** `PARTIAL`
- **Geeigneter Aufgabentyp:** Rationale Bildfunktion mit reellen linearen/quadratischen Faktoren.
- **Modul/Ansicht:** `Zeitbereich`, `Inverse Laplace-Transformation`.
- **Voraussetzungen:** Rationale Funktion in `s`.
- **Eingaben:** `F(s)`.
- **Akzeptierte Syntax:** Bildprofil; faktorisierte und ausmultiplizierte rationale Formen.
- **Gültiges Beispiel:** `(s+7)/((s+1)^2*(s-2))`.
- **Bedienfolge:** 1. Aufgabentyp wählen. 2. `F(s)` eingeben. 3. Berechnen. 4. `Partialbruchzerlegung` und `Zeitfunktion` lesen.
- **Interne Interpretation:** Bewahrt rohe und reduzierte algebraische Form von `F(s)` und klassifiziert Echt-/Unechtheit sowie Poltypen. Ohne zusätzlichen Systemkontext ist `F(s)` keine Systemübertragungsfunktion.
- **Automatische Schritte:** Kürzung, Polynomdivision falls nötig, vollständiger Ansatz für wiederholte Pole, Koeffizienten und Rücktransformation.
- **Sichtbare Ergebnisse:** Rationale Analyse, PBZ, Zeitfunktion, Kontrollen und Kürzungsdiagnosen. Eine Kürzung von `F(s)` ist hier nur als algebraische Kürzung zu dokumentieren, nicht als verborgener Systemmodus.
- **Manuelle Vorarbeit:** Keine zwingende Faktorisierung, solange Parser und Faktorisierung den Fall erkennen.
- **Manuelle Nacharbeit/Kontrolle:** Bei gestopptem uneigentlichem Fall Impuls-/Distributionsanteile außerhalb der App behandeln.
- **Typische Fehlbedienung:** `exp(s)` im Bildbereich.
- **Bekannte Grenze:** `(s^2+1)/(s+1)` wird nach Polynomdivision ohne gewöhnliche Zeitfunktion gestoppt.
- **Nachweis:** `ui/time_domain_workspace.py`, `application/time_domain_workflow.py`; `tests/application/test_time_domain_workflow.py`.

### WF-09: Sprungantwort

- **Status:** `UI_VERIFIED`
- **Geeigneter Aufgabentyp:** Nullzustandsantwort einer TF auf Sprunghöhe `A`.
- **Modul/Ansicht:** `Zeitbereich`, `Sprungantwort`.
- **Voraussetzungen:** `G(s)` ist die passende System-TF.
- **Eingaben:** `G(s)` und `Sprunghöhe A`.
- **Akzeptierte Syntax:** Bildprofil und exakter Skalar.
- **Gültiges Beispiel:** `G(s)=1/(2*s+1)`, `A=0.1`.
- **Bedienfolge:** 1. `Sprungantwort` wählen. 2. System und Höhe eingeben. 3. Berechnen.
- **Interne Interpretation:** Reduziert zuerst `G(s)`, baut `U(s)=A/s` und bildet anschließend `Y(s)=G(s)U(s)`. Nur eine Kürzung innerhalb der Systemreduktion von `G(s)` kann als möglicherweise verdeckte Systemdynamik gemeldet werden; eine erst im Produkt `Y(s)` entstehende Kürzung erhält diese Bedeutung nicht.
- **Automatische Schritte:** PBZ, Zeitfunktion und Endwertsatz-Prüfung.
- **Sichtbare Ergebnisse:** `y(t)=(1-exp(-t/2))/10`, stationärer Endwert `1/10` im Testfall.
- **Manuelle Vorarbeit:** Prüfen, ob Nullzustand und Sprungeingang gemeint sind.
- **Manuelle Nacharbeit/Kontrolle:** Endwert nur verwenden, wenn App-Prüfung und unabhängige Polprüfung passen.
- **Typische Fehlbedienung:** Anfangswertproblem in diesem TF-Modus lösen wollen.
- **Bekannte Grenze:** Keine allgemeinen Anfangsbedingungen; dafür WF-12.
- **Nachweis:** `ui/time_domain_workspace.py`, `application/time_domain_workflow.py`; `tests/ui/test_time_domain_workspace.py`, `tests/application/test_time_domain_workflow.py`.

### WF-10: Allgemeine Nullzustandsantwort aus G(s), U(s)

- **Status:** `PARTIAL`
- **Geeigneter Aufgabentyp:** Vorgegebene rationale Eingangsbildfunktion.
- **Modul/Ansicht:** `Zeitbereich`, `Allgemeine Antwort G(s), U(s)`.
- **Voraussetzungen:** Nullzustandsannahme.
- **Eingaben:** `G(s)` und `U(s)`.
- **Akzeptierte Syntax:** Rationale Bildsyntax.
- **Gültiges Beispiel:** `G(s)=1/(s+1)^2`, `U(s)=9/(s-2)`.
- **Bedienfolge:** 1. Aufgabentyp wählen. 2. Beide Funktionen eingeben. 3. Berechnen.
- **Interne Interpretation:** Reduziert `G(s)` und `U(s)` getrennt, multipliziert anschließend zu `Y(s)` und invertiert. Die Implementierung entfernt Kürzungs-/Moduswarnungen, die ausschließlich aus der Reduktion des Produkts stammen, und leitet eine Warnung vor verdeckter Systemdynamik nur aus einer Kürzung innerhalb von `G(s)` ab.
- **Automatische Schritte:** Reduktion, Polrollen, PBZ, Zeitfunktion, Kontrollen.
- **Sichtbare Ergebnisse:** System-/Eingangs-/Ausgangsbild, PBZ und Zeitantwort.
- **Manuelle Vorarbeit:** `U(s)` ggf. selbst aus dem Zeitsignal bilden.
- **Manuelle Nacharbeit/Kontrolle:** Kausalität und Anfangsbedingungen prüfen.
- **Typische Fehlbedienung:** `u(t)` statt `U(s)` eingeben.
- **Bekannte Grenze:** Nur rationale `U(s)`.
- **Nachweis:** `ui/time_domain_workspace.py`, `application/time_domain_workflow.py`; `tests/application/test_time_domain_workflow.py`.

### WF-11: Exponentialeingang

- **Status:** `UI_VERIFIED`
- **Geeigneter Aufgabentyp:** Eingang `A exp(λt)` bei gegebener TF.
- **Modul/Ansicht:** `Zeitbereich`, `Exponentialeingang`.
- **Voraussetzungen:** Nullzustand.
- **Eingaben:** `G(s)`, Exponentialamplitude und Exponentialexponent.
- **Akzeptierte Syntax:** Rationale TF und exakte Skalare.
- **Gültiges Beispiel:** `G(s)=1/(s+1)^2`, Amplitude `9`, Exponent `2`.
- **Bedienfolge:** 1. Modus wählen. 2. Drei Felder füllen. 3. Berechnen.
- **Interne Interpretation:** Reduziert `G(s)`, baut `U(s)=A/(s-λ)` und bildet danach `Y(s)`. Wie bei WF-09 und WF-10 gilt: Nur die Systemreduktion von `G(s)`, nicht eine reine Produktkürzung in `Y(s)`, begründet eine Warnung vor verdeckter Systemdynamik.
- **Automatische Schritte:** Wie WF-10 plus sichtbare Eingangsfunktion.
- **Sichtbare Ergebnisse:** `U(s)`, `Y(s)`, PBZ und Zeitfunktion.
- **Manuelle Vorarbeit:** Vorzeichen von `λ` korrekt übertragen.
- **Manuelle Nacharbeit/Kontrolle:** Wachsend/abklingend fachlich plausibilisieren.
- **Typische Fehlbedienung:** Gesamten Exponentialausdruck in ein Skalarfeld schreiben.
- **Bekannte Grenze:** Nur dieser typisierte Eingang, keine beliebige Zeitfunktion in diesem Modus.
- **Nachweis:** `ui/time_domain_workspace.py`, `application/time_domain_workflow.py`; `tests/application/test_time_domain_workflow.py`.

### WF-12: Lineare DGL mit Anfangswerten lösen

- **Status:** `PARTIAL`
- **Geeigneter Aufgabentyp:** Lineare zeitinvariante DGL Ordnung 1–4 mit strukturierten Anfangswerten.
- **Modul/Ansicht:** `Zeitbereich`, `Lineare DGL lösen`.
- **Voraussetzungen:** Koeffizienten und alle benötigten Werte bei `0+`.
- **Eingaben:** Analyseziel, Ordnungen, eindeutig nach Ableitung beschriftete Koeffizienten `a_i`, `b_i`, Eingangsart, nur die dafür relevanten Signalparameter, Anfangswerte und Annahmen.
- **Akzeptierte Syntax:** Exakte Koeffizienten; Signaltypen über Auswahl; direkte `U(s)` rational.
- **Gültiges Beispiel:** `a_0=1, a_1=2, a_2=1`, `b_0=1`, `y(0+)=0`, `y'(0+)=1`, Eingang `Exponential`, `A=9`, `lambda=2`.
- **Bedienfolge:** 1. Modus, Analyseziel und Ordnungen wählen. 2. Koeffizienten eingeben und Vorschau prüfen. 3. Eingang/Anfangswerte setzen. 4. Berechnen.
- **Interne Interpretation:** Transformiert Ableitungen einschließlich Anfangswerttermen und stoppt echt nach Bildgleichung, aufgelöstem `Y(s)`, PBZ oder vollständiger Zeitantwort. Das Standardziel `Vollständige Zeitantwort y(t)` erhält das bisherige Komplettverhalten.
- **Automatische Schritte:** `Bildgleichung aufstellen`: nur Transformation und Eingangsvorgabe; `Bildbereichslösung Y(s)`: zusätzlich algebraisches Auflösen und Bildgleichungskontrolle; `Partialbruchzerlegung von Y(s)`: zusätzlich rationale Analyse/PBZ und Rückzusammenfassung; `Vollständige Zeitantwort y(t)`: zusätzlich inverse Laplace, Anfangswert-, Vorwärtstransformations- und DGL-Residuenkontrollen.
- **Sichtbare Ergebnisse:** Zielabhängig nur erreichte Register. `Y(s)`-Ziel ergänzt die freie/erzwungene Bildantwort; PBZ ergänzt rationale Analyse und Partialbrüche; nur das Zeitziel zeigt die Zeitfunktion.
- **Manuelle Vorarbeit:** Koeffizienten nach Ableitungsordnung korrekt zuordnen.
- **Manuelle Nacharbeit/Kontrolle:** Rechte/linksseitige Anfangswerte und Signaldefinition prüfen.
- **Typische Fehlbedienung:** Fehlende Werte stillschweigend als null erwarten oder einen Zeitausdruck in `Bildbereichseingang U(s)` eintragen. Parserfehler nennen das sichtbare Feld und ein gültiges Kurzbeispiel.
- **Bekannte Grenze:** Zeitvariable Koeffizienten und nicht gewöhnlich invertierbare `U(s)` werden abgelehnt.
- **Nachweis:** `ui/time_domain_workspace.py`, `application/time_domain_workflow.py`; `tests/ui/test_time_domain_workspace.py`, `tests/application/test_time_domain_ode_workflow.py`.

### WF-13: Übertragungsfunktion aus DGL

- **Status:** `UI_VERIFIED`
- **Geeigneter Aufgabentyp:** Quotient Ausgang/Eingang unter Nullanfangsbedingungen.
- **Modul/Ansicht:** `Zeitbereich`, `Übertragungsfunktion aus DGL`.
- **Voraussetzungen:** Vollständiger Nullzustand.
- **Eingaben:** Namen, Ordnungen, Koeffizienten, Annahmen und sichtbare Nullzustandsbestätigung.
- **Akzeptierte Syntax:** Strukturierte exakte Koeffizienten.
- **Gültiges Beispiel:** `a_0=g*(m_K+m_G)`, `a_1=-d_K`, `a_2=m_K*l`, `b_0=-1`, Annahmen `m_K > 0; l > 0`.
- **Bedienfolge:** 1. Modus wählen. 2. DGL erfassen. 3. `Vollständigen Nullzustand ausdrücklich bestätigen`. 4. Berechnen.
- **Interne Interpretation:** Setzt alle erforderlichen Anfangswerte null und bildet den Bildquotienten.
- **Automatische Schritte:** Normalisierung, Laplace-DGL, Übertragungsfunktion und Kontrollen.
- **Sichtbare Ergebnisse:** Normalisierte DGL, Bildgleichung und `G_S(s)`.
- **Manuelle Vorarbeit:** Vorzeichen/Koeffizienten aus der DGL übertragen.
- **Manuelle Nacharbeit/Kontrolle:** Nullzustandsvoraussetzung im Aufgabenkontext rechtfertigen.
- **Typische Fehlbedienung:** Checkbox nicht setzen oder Nichtnull-Anfangswerte voraussetzen.
- **Bekannte Grenze:** Nichtnull-Anfangszustand ist definitionsgemäß nicht Teil der TF-Bildung.
- **Nachweis:** `ui/time_domain_workspace.py`, `application/time_domain_workflow.py`; `tests/ui/test_time_domain_workspace.py`, `tests/application/test_time_domain_ode_workflow.py`.

### WF-14: DGL in Regelungsnormalform

- **Status:** `PARTIAL`
- **Geeigneter Aufgabentyp:** SISO-DGL mit nicht abgeleitetem Eingang.
- **Modul/Ansicht:** `Zustandsraum`, `DGL → Regelungsnormalform`.
- **Voraussetzungen:** Ordnung 1–4; führender Koeffizient nachweislich ungleich null.
- **Eingaben:** Ausgangs-/Eingangsname, Ordnung, `a_i`, `b_0`, Parameter/Annahmen.
- **Akzeptierte Syntax:** Exakte skalare Ausdrücke.
- **Gültiges Beispiel:** Ordnung 3; `a_0=4, a_1=-8, a_2=0, a_3=2`, `b_0=2`.
- **Bedienfolge:** 1. Modus wählen. 2. Felder setzen. 3. Vorschau prüfen. 4. `Zustandsraum analysieren`.
- **Interne Interpretation:** Zustände sind Ausgang und aufeinanderfolgende Ableitungen.
- **Automatische Schritte:** DGL-Normalisierung, `A_R,b_R,c_R^T,d`, im Stabilitätsziel Bildung von `sI-A_R`, Polynom, Eigenwerte, TF und Kontrollen.
- **Sichtbare Ergebnisse:** Zustandsdefinitionen, Matrizen, Stabilität und Transferfunktion.
- **Manuelle Vorarbeit:** DGL in Koeffizientenform bringen.
- **Manuelle Nacharbeit/Kontrolle:** Gewählte Zustandsdefinition gegen verlangte Form prüfen.
- **Typische Fehlbedienung:** Ableitungen des Eingangs benötigen, obwohl UI nur `b_0` bietet.
- **Bekannte Grenze:** Abgeleiteter Eingang und unsicherer führender Koeffizient werden abgelehnt.
- **Nachweis:** `ui/state_space_workspace.py`, `application/state_space_workflow.py`; `tests/ui/test_state_space_workspace.py`, `tests/domain/test_state_space_workflow.py`.

### WF-15: Zustandsraum in Übertragungsfunktion

- **Status:** `UI_VERIFIED`
- **Geeigneter Aufgabentyp:** SISO-Modell `(A,b,c^T,d)`.
- **Modul/Ansicht:** `Zustandsraum`, `Zustandsraum → Übertragungsfunktion`.
- **Voraussetzungen:** Konsistente Dimension 1–4.
- **Eingaben:** Matrix-/Vektorfelder und optional Parameter/Annahmen.
- **Akzeptierte Syntax:** Zeilen `;`/Zeilenumbruch, Zellen `,`, sichere exakte Zellausdrücke.
- **Gültiges Beispiel:** `A=-1, 0; 0, 1`, `b=1; 0`, `c^T=1, 0`, `d=0`.
- **Bedienfolge:** 1. Modus wählen. 2. Matrizen eingeben. 3. Dimensionsvorschau prüfen. 4. Analysieren.
- **Interne Interpretation:** Berechnet roh `c^T(sI-A)^{-1}b+d`, reduziert und vergleicht mit Zustandsmodi.
- **Automatische Schritte:** Determinante, Resolvente, TF-Reduktion, Eigenwerte, Stabilität, verborgene Modi.
- **Sichtbare Ergebnisse:** Im Beispiel reduzierte TF `1/(s+1)` und Warnung zur verborgenen instabilen Mode `s=1`.
- **Manuelle Vorarbeit:** SISO-Matrizen korrekt anordnen.
- **Manuelle Nacharbeit/Kontrolle:** Zustands- und E/A-Stabilität ausdrücklich getrennt angeben.
- **Typische Fehlbedienung:** `b` als Zeile oder `c^T` als Spalte eingeben.
- **Bekannte Grenze:** Dimension größer als 4 nicht unterstützt.
- **Nachweis:** `ui/state_space_workspace.py`, `application/state_space_workflow.py`; `tests/ui/test_state_space_workspace.py`, `tests/domain/test_state_space_workflow.py`.

### WF-16: P-Verstärkung für gewünschte Phasenreserve

- **Status:** `PARTIAL`
- **Geeigneter Aufgabentyp:** Positiver P-Faktor bei vorgegebener Phasenreserve.
- **Modul/Ansicht:** `Reglerauslegung`, `P-Verstärkung für gewünschte Phasenreserve`.
- **Voraussetzungen:** Offene Strecke als Zähler/Nenner; Ziel `0<Φ_R<180°`; positiver Suchbereich.
- **Eingaben:** Strecke, Parameterbelegungen, Zielreserve, `ω_min`, `ω_max`, Punkte/Dekade.
- **Akzeptierte Syntax:** Rationale Strecke; Skalarfelder akzeptieren rationale/Dezimalwerte und hier wissenschaftliche Schreibweise wie `1e-4`.
- **Gültiges Beispiel:** Zähler `100`, Nenner `s*(10*s+1)`, Ziel `20`, Bereich `1e-4` bis `1e2`, `32` Punkte/Dekade.
- **Bedienfolge:** 1. Verfahren wählen. 2. Strecke/Ziel/Bereich eingeben. 3. `Reglerauslegung berechnen`.
- **Interne Interpretation:** Sucht entfaltete Phase `-180°+Φ_R`, setzt `k_P=1/|G_0(jω*)|` und analysiert neu.
- **Automatische Schritte:** Zielphasensuche, Kandidaten, neue Durchtritte/Reserven und Nyquist. Beim exakt erkannten Referenzmodell `100/(s*(10*s+1))` mit Zielreserve `20°` wird zusätzlich die sichere Beziehung `ω*=tan(70°)/10` vor dem Näherungswert dargestellt; andere Fälle bleiben ausdrücklich numerisch.
- **Sichtbare Ergebnisse:** Zielphase, Zielfrequenz, Betrag am Zielpunkt, allgemeiner und eingesetzter `k_P`-Wert, neuer offener Kreis, Durchtritt, erreichte und globale Reserve, Nyquist-Kontrollstatus und symbolisch gesetztes LaTeX ohne rohe Eingabesterne.
- **Manuelle Vorarbeit:** Offene Strecke bilden und sinnvollen Suchbereich wählen.
- **Manuelle Nacharbeit/Kontrolle:** Bei mehreren erfolgreichen Kandidaten Auswahl treffen; globale Reserve prüfen.
- **Typische Fehlbedienung:** Suchbereich verfehlt Zielphase; ungelöste Parameter.
- **Bekannte Grenze:** Außerhalb der sicher erkannten Referenzstruktur bleibt die Zielphasensuche numerisch; kein Kandidat ergibt keine LaTeX-Lösung.
- **Nachweis:** `ui/controller_design_workspace.py`, `application/controller_design_workflow.py`; `tests/ui/test_controller_design_workspace.py`, `tests/application/test_controller_design_workflow.py`.

### WF-17: Ziegler–Nichols – offener Kreis

- **Status:** `PARTIAL`
- **Geeigneter Aufgabentyp:** Tabellenentwurf aus `K_S`, `K_T`, `T`.
- **Modul/Ansicht:** `Reglerauslegung`, gleichnamiges Verfahren.
- **Voraussetzungen:** Positive Werte und strikt `K_T/T < 0,5`.
- **Eingaben:** Reglertyp P/PI/PID, `K_S`, `K_T [s]`, `T [s]`.
- **Akzeptierte Syntax:** Reine Zahlen; keine Einheiten im Feld.
- **Gültiges Beispiel:** `K_S=1.8`, `K_T=12`, `T=72`, `PID`.
- **Bedienfolge:** 1. Verfahren/Reglertyp wählen. 2. Kennwerte eingeben. 3. Berechnen.
- **Interne Interpretation:** Quellenstrenge Kurskonvention, parallele PID-Form.
- **Automatische Schritte:** Konkrete Gültigkeitsprüfung, allgemeine Formel, Einsetzung, exakte Tabellenrechnung und äquivalente Reglerformen.
- **Sichtbare Ergebnisse:** `k_P,k_I,k_D,T_I,T_D`, exakte Werte vor Näherungen, parallele Form als primäres Ergebnis, Idealform als äquivalente Darstellung, Kontrollen, Worked Steps und LaTeX.
- **Manuelle Vorarbeit:** Kennwerte aus Sprungantwort/Wendetangente bestimmen.
- **Manuelle Nacharbeit/Kontrolle:** Reale Regelgüte und Quellenkonvention prüfen.
- **Typische Fehlbedienung:** `12 s` eingeben oder Grenzbereich verletzen.
- **Bekannte Grenze:** App ermittelt `K_S,K_T,T` nicht aus Messdaten/Plot und rechnet keinen Totzeit-Frequenzgang.
- **Nachweis:** `ui/controller_design_workspace.py`, `application/controller_design_workflow.py`; `tests/application/test_controller_design_workflow.py`, `tests/domain/test_controller_design_analyzer.py`.

### WF-18: Ziegler–Nichols – geschlossener Kreis

- **Status:** `PARTIAL`
- **Geeigneter Aufgabentyp:** Tabellenentwurf aus kritischer Verstärkung/Periode.
- **Modul/Ansicht:** `Reglerauslegung`, gleichnamiges Verfahren.
- **Voraussetzungen:** Positive `K_crit`, `T_crit`.
- **Eingaben:** Reglertyp und beide Kennwerte.
- **Akzeptierte Syntax:** Reine positive Zahlen; Sekunden ohne Einheitentext.
- **Gültiges Beispiel:** `K_crit=1.62`, `T_crit=3`, `PID`.
- **Bedienfolge:** 1. Verfahren/Reglertyp wählen. 2. Werte eingeben. 3. Berechnen.
- **Interne Interpretation:** Exakte Tabellenrechnung.
- **Automatische Schritte:** Reglerparameter und Formen.
- **Sichtbare Ergebnisse:** Parameter, Kontrollen, Worked Steps und LaTeX.
- **Manuelle Vorarbeit:** Kritische Werte experimentell/analytisch außerhalb der App bestimmen.
- **Manuelle Nacharbeit/Kontrolle:** Geschlossenen Kreis unabhängig validieren.
- **Typische Fehlbedienung:** Null/negative oder mit Einheit versehene Zeit.
- **Bekannte Grenze:** Keine automatische Grenzschwingungssuche.
- **Nachweis:** `ui/controller_design_workspace.py`, `application/controller_design_workflow.py`; `tests/application/test_controller_design_workflow.py`, `tests/domain/test_controller_design_analyzer.py`.

### WF-19: Cohen–Coon

- **Status:** `PARTIAL`
- **Geeigneter Aufgabentyp:** Tabellenentwurf aus `K_S`, `K_T`, `T`.
- **Modul/Ansicht:** `Reglerauslegung`, `Cohen–Coon`.
- **Voraussetzungen:** Positive Werte und strikt `0 < r=K_T/T < 2`.
- **Eingaben:** Reglertyp P/PI/PID, `K_S`, `K_T [s]`, `T [s]`.
- **Akzeptierte Syntax:** Wie WF-17.
- **Gültiges Beispiel:** `K_S=1.8`, `K_T=12`, `T=72`, `PID`.
- **Bedienfolge:** 1. Verfahren/Reglertyp wählen. 2. Werte eingeben. 3. Berechnen.
- **Interne Interpretation:** Berechnet zuerst `r=K_T/T`, dann exakte Tabellenwerte.
- **Automatische Schritte:** Reglerparameter, parallele/ideale Form und Kontrollen.
- **Sichtbare Ergebnisse:** Im Testfall u. a. exakte Werte `49/9` und `2107/10692`.
- **Manuelle Vorarbeit:** Prozesskennwerte bestimmen.
- **Manuelle Nacharbeit/Kontrolle:** Quellenkonvention und Regelgüte prüfen.
- **Typische Fehlbedienung:** `K_T/T` außerhalb des Quellenbereichs.
- **Bekannte Grenze:** Keine Identifikation der Strecke aus Daten.
- **Nachweis:** `ui/controller_design_workspace.py`, `application/controller_design_workflow.py`; `tests/ui/test_controller_design_workspace.py`, `tests/application/test_controller_design_workflow.py`.

## 8. Fehlerdiagnose für KI-Assistenten

Entscheidungsbaum:

1. Stimmt das gewählte Modul?
2. Stimmt der erwartete Aufgabentyp?
3. Entspricht die Eingabe dem Parserprofil dieses Moduls?
4. Sind Klammern, Multiplikationszeichen und Potenzen eindeutig?
5. Sind Parameter und Anfangsbedingungen vollständig?
6. Wurde das richtige Analyseziel ausgewählt?
7. Wird das rohe oder reduzierte Modell benötigt?
8. Ist der Fall ausdrücklich nicht unterstützt?
9. Wurde nach einer Fehlermeldung ein altes Ergebnis stehen gelassen?
10. Weicht die Ausgabe fachlich vom unabhängig bestimmten Soll ab?

| Beobachtung | Wahrscheinliche Ursache | Prüfung | Korrektur | Wann als möglicher Bug behandeln |
|---|---|---|---|---|
| Parser meldet implizite Multiplikation | Fehlendes `*` | Nach `2s`, `s(`, `)(` suchen | Explizites `*` setzen | Nur wenn nachweislich gültige explizite Syntax weiter abgelehnt wird |
| Frequenz `0.5` abgelehnt | Feld verlangt exakte rationale Schreibweise | Diagnose nennt rationale Zahl | `1/2` eingeben | Wenn `1/2` reproduzierbar abgelehnt wird |
| Stabilitätsaussage widerspricht Erwartung | Roh/reduziert oder Ziel verwechselt | Rolle, Analyseziel, Kürzungen prüfen | Passendes Ziel wählen und beide Modelle benennen | Wenn dasselbe korrekt gewählte Polynom unabhängig anderes Soll liefert |
| Keine Zeitfunktion nach inverser Laplace | Uneigentliche Funktion oder nicht unterstützter Faktor | Tab `Rationale Analyse` und Diagnosen | Polynomdivision/Distributionsanteile manuell fortsetzen | Wenn ein fokussiert getesteter eigentlicher Fall scheitert |
| Kürzung im Zeitbereich | Provenienz `F(s)`, `G(s)` oder Produkt `Y(s)` verwechselt | Aufgabentyp und rohe/reduzierte Ausdrücke prüfen: allgemeines `F(s)`, Systemreduktion von `G(s)` oder erst Produktbildung | Bei `F(s)` nur algebraische Kürzung benennen; „verborgener Systemmodus“ nur aus einer Kürzung innerhalb von `G(s)` ableiten; reine Produktkürzung in `Y(s)` nicht so deuten | Wenn die App bei WF-09 bis WF-11 trotz unverändertem `G(s)` eine reine Produktkürzung als verdeckte Systemdynamik ausgibt |
| DGL stoppt vor `Y(s)` | Anfangswert fehlt | `Diagnosen` und Felder bei `0+` prüfen | Wert angeben oder Nullpolitik bewusst bestätigen | Wenn vollständige Werte nicht erkannt werden |
| TF aus DGL wird abgelehnt | Nullzustand nicht bestätigt | Checkbox prüfen | Sichtbar bestätigen, sofern fachlich korrekt | Wenn Bestätigung gesetzt und kein Nichtnullzustand vorliegt |
| Zustands-TF stabil, Zustandsmodell instabil | Verborgener gekürzter Modus | Roh-/reduzierte TF und Kürzungsbericht prüfen | E/A- und Zustandsstabilität getrennt berichten | Wenn Modus trotz algebraisch nachweisbarer Beobacht-/Steuerbarkeit falsch klassifiziert wird |
| P-Phasenreserve liefert keine Lösung | Zielphase im Suchbereich nicht erreicht | Bereich/entfaltete Phase unabhängig prüfen | Bereich korrigieren oder Verfahren verwerfen | Wenn nachweisliche Zielwurzel mit gültiger Eingabe nicht gefunden wird |
| Tabellenverfahren liefert keine Ausgabe | Einheitentext oder Quellenbereich | Werte und `K_T/T` prüfen | Nur Zahlen; Bereich einhalten | Wenn gültige positive Werte im Bereich reproduzierbar scheitern |
| Altes Transferfunktionsresultat bleibt sichtbar | Neuer Request scheiterte vor Start | Statuszeile auf `vorherigen Berechnung` prüfen | Eingabe korrigieren und neu rechnen | Wenn altes Ergebnis nicht klar als alt markiert ist |

Ein möglicher Bug darf erst angenommen werden, wenn der richtige Workflow gewählt wurde, die Eingabe nachweislich gültig ist, alle Voraussetzungen erfüllt sind, ein unabhängiges Soll-Ergebnis vorliegt und das Verhalten reproduzierbar ist.

## 9. Sichtbare Fehlermeldungen und Warnungen

| Meldung oder eindeutiger Textanfang | Auslöser | Typischer Eingabefehler | Korrektur | Ergebniszustand danach |
|---|---|---|---|---|
| `Bitte gib einen mathematischen Ausdruck ein.` | Leeres Ausdrucksfeld | Pflichtfeld leer | Ausdruck eingeben | Berechnung blockiert |
| `Implizite Multiplikation ist nicht erlaubt; verwende '*'.` | Aneinanderstehende Faktoren | `2s`, `(s+1)(s+2)` | `2*s`, `(s+1)*(s+2)` | Berechnung blockiert |
| `Die Zahl verwendet ein ungültiges oder uneindeutiges Format.` | Mehrdeutige/unerlaubte Zahl | `.5`, `1, 5` | `0.5` bzw. eindeutige Syntax | Berechnung blockiert |
| `Eingabe ungültig; das angezeigte Ergebnis stammt aus der vorherigen Berechnung.` | Neuer Transferfunktionsrequest fehlerhaft, vorheriges Ergebnis vorhanden | Ungültige Parameterzeile/Syntax | Eingabe korrigieren und erneut starten | Frühere Resultate bleiben sichtbar und werden ausdrücklich als alt markiert |
| `Eine exakte rationale Zahl wie 3 oder 1/10 ist erforderlich.` | Frequenz-/Rasterfeld nicht rational | `0.5` | `1/2` | Frequenzberechnung blockiert; Ergebnisansicht wird auf Fehlerzustand gesetzt |
| `Die obere K-Grenze muss größer als die untere sein.` | Ungültiger K-Bereich | Vertauschte Grenzen | Grenzen korrigieren | Berechnung blockiert |
| `Mit … Punkten pro Dekade … werden … Punkte angefordert; erlaubt sind maximal …` | Frequenzraster überschreitet eine Punkte-, Dichte-, Bereichs- oder Explizitfrequenzgrenze | Zu viele Punkte pro Dekade, zu großer Bereich oder zu viele explizite Frequenzen | Den konkret genannten sicheren Punkte-pro-Dekade-Wert verwenden; falls dieser allein nicht reicht, explizite Frequenzen reduzieren oder Bereich verkleinern | Keine Bode-Auswertung; Diagnose nennt Punktzahl, Grenzwert, Eingaben und Korrektur und fokussiert nach Möglichkeit das betroffene Feld |
| `Die numerische Nyquist-Auswertung wurde nicht gestartet, weil der Parameter K nicht numerisch belegt ist.` | Verwendeter Parameter ohne Zahlenbelegung | `K/(s+1)` mit deklarierter, aber leerer Parameterzeile | `K` in der Parametertabelle numerisch belegen und erneut berechnen | Kein Nyquist-Zahlenlauf und kein Nyquist-Plot; symbolische Teilresultate und konkrete Diagnose bleiben sichtbar |
| `Variable oder Entscheidungsparameter sind ungültig.` | Name/Anzahl ungültig | Drei Parameter oder reservierter Name | Maximal zwei gültige Namen | Stabilitätsanalyse blockiert; neue Ergebnisfelder zeigen Fehler |
| `Annahme …: Relation nicht unterstützt.` | Annahmesyntax unbekannt | Freitext statt Relation | Einfache Relation verwenden | Stabilitätsanalyse blockiert |
| `Vollständige Nullzeile` / `Hilfspolynomverfahren` | Routh-Sonderfall | Kein Bedienfehler | Manuell fachlich fortsetzen | Teilresultate/Diagnose sichtbar; LaTeX-Kopieren kann deaktiviert sein |
| `DGL-Koeffizienten müssen zeitunabhängig sein.` | `t`/`s` in DGL-Koeffizient | Zeitvariable DGL | Nur konstante/parametrische Koeffizienten | Zeitbereich zeigt Fehler statt Lösung |
| `Feld „Bildbereichseingang U(s)“ ist ungültig. …` | Direkte DGL-Eingabe ist nicht rational in `s` | `exp(s)` oder Zeitausdruck | Z. B. `1/s` oder `1/(s+2)` verwenden | Vor der Bildgleichungsauflösung gestoppt |
| `Feld „Koeffizient vor …“ ist ungültig. …` | Ungültiger DGL-Koeffizient | Unvollständiger Ausdruck | Zahl oder zulässigen symbolischen Ausdruck, z. B. `2` oder `k`, verwenden | Vor Aufbau der DGL gestoppt |
| `Fehlende Ausgangsanfangswerte: y…(0+). …` | Benötigter Anfangswert leer | Wert vergessen | Exakten Wert, z. B. `0` oder `y0`, angeben oder Nullpolitik bestätigen | Vor `Y(s)` gestoppt; Fehlerdarstellung |
| `Die Übertragungsfunktion erfordert eine sichtbare Bestätigung …` | TF aus DGL ohne Nullzustandscheckbox | Bestätigung fehlt | Checkbox setzen, sofern fachlich richtig | Vor TF-Bildung gestoppt |
| `Zustandsdimension größer als 4 wird nicht unterstützt.` | Matrixdimension >4 | Zu großes Modell | Außerhalb der App rechnen/reduzieren | Keine fachlichen Resultate, Diagnose sichtbar |
| `A muss quadratisch sein; erhalten: …` / Dimensionsmeldungen für `b`, `c^T`, `d` | Inkonsistente Matrixformen | Zeilen/Spalten vertauscht | Matrixstruktur korrigieren | Keine fachlichen Resultate |
| `Die Zielphase wird im untersuchten Frequenzbereich nicht erreicht.` | P-Auslegung ohne Zielwurzel | Bereich zu klein/falsche Strecke | Bereich/Strecke prüfen | Kein LaTeX; keine kopierbare Lösung |
| `Zeitwerte müssen als reine Zahlen in Sekunden eingegeben werden.` | Einheit im Skalarfeld | `12 s` | `12` | Keine LaTeX-Ausgabe; Diagnose sichtbar |
| `K_T/T < 0,5 ist nicht erfüllt` / `0 < r=K_T/T < 2 ist nicht erfüllt` | Quellenbereich verletzt | Verhältnis erreicht oder überschreitet die strikte Grenze | Anderes Verfahren oder korrekte Werte | Keine LaTeX-Ausgabe; Diagnose sichtbar |

Das Verhalten ist nicht für alle Module einheitlich: Bei `Transferfunktion` löscht ein gültig gestarteter neuer Lauf das alte Resultat. Scheitert dort nur die Request-Erstellung, bleibt das vorherige Resultat sichtbar und wird ausdrücklich als Ergebnis der vorherigen Berechnung markiert; ein unerwarteter Ausführungsfehler entfernt die alte Mathematik. `Frequenzbereich` ersetzt bei einer ungültigen neuen Eingabe die bisherige Ansicht durch einen neuen Fehlerzustand; schlägt nur die optionale Singularitätsverfeinerung fehl, bleibt dagegen das Basisergebnis desselben aktuellen Laufs mit einem Hinweis sichtbar. `Stabilität`, `Zeitbereich`, `Zustandsraum` und `Reglerauslegung` stellen bei den geprüften neuen Berechnungs- und Fehlerpfaden einen neuen Zustand dar und übernehmen kein ausdrücklich als veraltet markiertes Vorresultat. Darüber hinaus besteht keine modulübergreifende Garantie; bei einer nicht dokumentierten Fehlerfolge muss ein KI-Assistent den sichtbaren Status und gegebenenfalls einen aktuellen Screenshot prüfen.

## 10. Bekannte Grenzen und manuelle Schritte

- `UNSUPPORTED`: Keine UI für Linearisierung, Wurzelortskurve, Lead-/Lag-Auslegung, Padé, OCR oder beliebige grafische Blockschaltbilder.
- Parser-Standardgrenzen: 1000 Zeichen, 256 AST-Knoten, Tiefe 32, 16 Symbole, Exponentenbetrag 32. Dies sind Schutzgrenzen, keine fachlichen Leistungszusagen.
- Stabilität: maximal zwei Entscheidungsparameter. Größere symbolische Gebiete müssen manuell zerlegt werden.
- Frequenzraster: maximal 24 Dekaden, 64 Punkte pro Dekade, 2048 Rasterpunkte und 256 explizite Punkte; der Frequenzanalysepfad begrenzt einen Lauf zusätzlich auf 256 Frequenzpunkte. Welche Grenze zuerst greift, hängt vom Request ab. Grenzdiagnosen nennen angeforderte Punktzahl, wirksamen Grenzwert, Rasterdichte, Bereich und Zahl expliziter Frequenzen sowie mindestens eine deterministisch sichere Korrektur.
- Frequenz-Wertetabellen sind nach Reset kompakt. Pflichtpunkte bleiben vollständig erhalten, auch wenn dadurch mehr als zwölf Zeilen nötig sind; das unveränderte Vollraster bleibt über `Tabellenumfang:` sichtbar und wird bei dieser Wahl auch vollständig in die LaTeX-`longtable` übernommen.
- Frequenzresultate kombinieren exakte Spezialisierung mit numerischer Darstellung. Bode, Reserven, Nyquist und P-Phasenreserve sind nicht rein symbolisch.
- Numerische Nyquist-Auswertung startet nur bei vollständig numerisch belegten verwendeten Parametern. Unbelegte Parameter bleiben symbolisch; es gibt keine implizite Annahme für `K`.
- Betrag und Phase verwenden eine gemeinsame logarithmische Frequenzachse. Grenzen sowie Haupt- und Nebenticks werden gemeinsam geführt, damit identische Frequenzen und Marker vertikal übereinanderliegen.
- Hauptphase und entfaltete Phase sind getrennt; die entfaltete Phase ist nur eine kontinuierliche Zusatzdarstellung durch Vielfache von 360°.
- Bode-`Asymptotische Näherung` und `Grobe Klausurskizze` basieren auf erkannten Standardgliedkomponenten. Nicht erkannte Zerlegungen benötigen manuelle Skizzenarbeit.
- Direkte Laplace-Transformation unterstützt einen begrenzten Vorrat aus Konstanten, Potenzen, Exponential-, Sinus-/Kosinusformen und nachgewiesenen Kombinationen.
- Uneigentliche inverse Laplace-Funktionen werden klassifiziert und dividiert, aber eine gewöhnliche Zeitfunktion mit Distributionsanteilen wird nicht fertiggestellt.
- TF-basierte Zeitantworten sind Nullzustandsantworten. Allgemeine Anfangsbedingungen gehören in `Lineare DGL lösen`.
- Im Zeitbereich ist die Kürzungsprovenienz strikt zu trennen: Eine allgemeine inverse Bildfunktion `F(s)` wird ohne Systemaussage nur algebraisch reduziert. In den Antwortmodi wird `G(s)` vor der Produktbildung separat reduziert; nur eine Kürzung innerhalb dieses `G(s)` kann als möglicherweise verdeckte Systemdynamik gelten. Kürzungen, die erst in `Y(s)=G(s)U(s)` entstehen, sind keine verborgenen Systemmoden und ihre entsprechenden Warncodes werden im sichtbaren Antwortworkflow entfernt.
- DGL: Ausgangsordnung 1–4, Eingangsordnung 0–4; Koeffizienten zeitunabhängig. Fehlende Anfangswerte werden bei allen vier Analysezielen niemals ohne gesetzte Nullpolitik angenommen. Die Zielwahl hat bei `Übertragungsfunktion aus DGL` keine Wirkung.
- Zustandsraum: SISO, Dimension 1–4. DGL→Regelungsnormalform unterstützt nur den nicht abgeleiteten Eingang.
- Reglerauslegung ermittelt Prozesskennwerte nicht aus Diagrammen. ZN/Cohen–Coon bleiben Tabellenverfahren in der implementierten Kurskonvention. Totzeit-Frequenzrechnung und Lead-Auslegung sind weiterhin nicht unterstützt.
- Keine Datei-Exportfunktion nachgewiesen; nur Zwischenablage/LaTeX-Quelltext.

## 11. Regeln für einen GPT-Chat

1. Versionsstand zuerst mit dem Baseline-Commit vergleichen. Weicht der getestete App-Commit ab, das Handbuch nur vorläufig verwenden: zuerst prüfen, ob betroffene Module, Eingabeformate oder Workflows seitdem verändert wurden, und bei Unsicherheit aktuelle Screenshots oder eine aktualisierte Handbuchversion verlangen.
2. Keine nicht dokumentierten Buttons, Felder oder Optionen erfinden.
3. Bei unbekannter Ansicht einen Screenshot verlangen.
4. Exakte kopierbare Eingaben bereitstellen, einschließlich `*`, Klammern und passender Bruchsyntax.
5. Das Parserprofil des konkreten Moduls verwenden.
6. Die fachliche Soll-Lösung unabhängig von der App bestimmen.
7. Bedienfehler nicht vorschnell als Softwarefehler einordnen.
8. Rohe und reduzierte Modelle ausdrücklich unterscheiden.
9. Interne, E/A- und Zustandsstabilität nicht gleichsetzen.
10. Manuelle Vor- und Nacharbeiten offen benennen.
11. `UNKNOWN` nicht durch Vermutungen ersetzen.
12. Bei einem möglichen Bug Soll, Ist, exakte Eingabe, Modul, Softwarestand und Reproduktionsschritte erfassen.
13. Steht nach einem Fehler ein Resultat, zuerst prüfen, ob es ausdrücklich als Ergebnis der vorherigen Berechnung markiert ist.
14. Keine App-Ausgabe als fachliche Autorität behandeln.

## 12. Wartungsregel für spätere Änderungen

Jeder spätere PR muss prüfen, ob er mindestens einen dieser Punkte verändert:

- sichtbare Funktion,
- UI-Bezeichnung oder UI-Element,
- Navigation,
- Eingabeformat,
- Parser- oder Validierungsverhalten,
- fachlichen Workflow,
- automatische Umformung,
- Ergebnisdarstellung,
- Rechenweg,
- Diagramm,
- LaTeX-Ausgabe,
- Fehlermeldung,
- bekannte Grenze.

Falls ja, müssen ausschließlich die betroffenen Abschnitte dieses Handbuchs im selben PR aktualisiert werden. Falls nein, muss der Abschlussbericht des PR ausdrücklich enthalten:

`AI Operator Manual geprüft: keine Aktualisierung erforderlich.`

Das Handbuch darf bei kleinen Feature-PRs nicht vollständig neu generiert oder unnötig umformatiert werden.

## 13. Offene manuelle Validierungen

| Bereich | Unklarheit | Warum nicht beweisbar | Benötigter Screenshot oder manueller Test |
|---|---|---|---|
| Windows-Rendering | Ob bei Standard-Windows-Skalierung alle langen Beschriftungen ohne Abschneiden sichtbar sind | Offscreen-Tests prüfen Struktur, nicht jede DPI-/Schriftkombination | Screenshot des Hauptfensters und aller sechs Tabs bei 100 % und verwendeter Systemskalierung |
| Matplotlib-Werkzeugleiste | Ob plattformspezifische Standard-Interaktionen verfügbar/verständlich sind | Die App verdrahtet keine fachliche Toolbar; Backend kann variieren | Manueller Start und Prüfung, ob zusätzliche Plotwerkzeuge erscheinen; nicht als Fachworkflow dokumentieren |
| Große Resultate | Lesbarkeit sehr großer Hurwitz-/Routh-/PBZ-Berichte | Tests belegen Inhalte, nicht alle Scroll-/Layoutfälle | Je ein manueller Lauf am höchsten praktisch verwendeten Grad mit Screenshot der Tabs |
| Zwischenablage außerhalb Tests | Zusammenspiel mit realen Zielprogrammen und Sonderzeichen | Qt-Tests belegen den kopierten String, nicht Word/LaTeX-Editor | LaTeX aus jedem Modul einmal in den vorgesehenen Editor einfügen |

## 14. Technische Nachweiskarte

| Handbuchbereich | maßgebliche Produktionsdateien | maßgebliche Tests |
|---|---|---|
| Start/Navigation | `pyproject.toml`, `src/klausurbotpro/__main__.py`, `src/klausurbotpro/app.py`, `src/klausurbotpro/ui/main_window.py` | `tests/ui/test_main_window.py`, `tests/test_smoke.py` |
| Globale Syntax | `src/klausurbotpro/parsing/contracts.py`, `normalization.py`, `ast_parser.py`, `rational_parser.py` | `tests/parsing/test_normalization.py`, `test_rational_parser.py`, `test_time_domain_parser_profiles.py`, Sicherheits-Parsertests |
| Transferfunktion | `ui/transfer_function_workspace.py`, `ui/transfer_function_presenter.py`, `application/transfer_function_workflow_service.py` | `tests/ui/test_transfer_function_workspace.py`, `tests/application/test_transfer_function_workflow_service.py`, Berichtstests |
| Frequenzbereich | `ui/frequency_domain_workspace.py`, `ui/frequency_domain_presenter.py`, `application/frequency_domain_workflow_service.py` | `tests/ui/test_frequency_domain_workspace.py`, `test_frequency_reserve_presenter_smoke.py`, `tests/application/test_frequency_domain_workflow_service.py` |
| Stabilität | `ui/stability_workspace.py`, `ui/stability_presenter.py`, `application/stability_workflow.py` | `tests/ui/test_stability_presenter.py`, `tests/domain/test_hurwitz_analyzer.py`, `test_routh_analyzer.py`, `tests/application/test_stability_transfer_function_workflow.py` |
| Zeitbereich | `ui/time_domain_workspace.py`, `ui/time_domain_presenter.py`, `application/time_domain_workflow.py` | `tests/ui/test_time_domain_workspace.py`, `tests/application/test_time_domain_workflow.py`, `test_time_domain_ode_workflow.py` |
| Zustandsraum | `ui/state_space_workspace.py`, `ui/state_space_presenter.py`, `application/state_space_workflow.py` | `tests/ui/test_state_space_workspace.py`, `tests/domain/test_state_space_workflow.py` |
| Reglerauslegung | `ui/controller_design_workspace.py`, `ui/controller_design_presenter.py`, `application/controller_design_workflow.py` | `tests/ui/test_controller_design_workspace.py`, `tests/application/test_controller_design_workflow.py`, `tests/domain/test_controller_design_analyzer.py` |
| Fehlerzustände | Die jeweiligen Presenter/View-States und Request-Factories | Fokussierte UI-/Presenter-Fehler- und Resettests der sechs Module |
