# KlausurBotPro – Roadmap

**Status:** Phase 1 fachlich und manuell abgenommen; Release-Kandidat
`v0.1.1-exam` in Vorbereitung

**Stand:** 24.07.2026

**Planungsziel:** maximale Klausurpunktabdeckung und Rechenzeitersparnis bei
kontrollierbarem Integrationsrisiko und sparsamer Codex-Nutzung

Diese Datei beschreibt den aktuellen Arbeitsstand und die Reihenfolge der
nächsten Feature-PRs. Fachliche Regeln stehen in `docs/reference/`,
implementierungsfertige Zuschnitte in `docs/implementation/`.

## Release-Status vom 24.07.2026

Phase 1 ist umgesetzt und fachlich sowie manuell abgenommen. Der daraus
entstandene Release-Kandidat ist `v0.1.1-exam`. Die sechs vorhandenen
Hauptworkflows Transferfunktion, Frequenzbereich, Stabilität, Zeitbereich,
Zustandsraum und Reglerauslegung bilden den eingefrorenen Funktionsumfang.

Die nachstehenden früheren Feature-Abschnitte dokumentieren die
Entstehungsplanung. Sie stellen die in Phase 1 abgeschlossenen Pakete nicht
mehr als offene Arbeiten dar. Nachfolgende Phasen und größere neue Funktionen
bleiben ausdrücklich außerhalb von `v0.1.1-exam`.

## 1. Verbindliche Planungsgrundsätze

1. KlausurBotPro automatisiert vorrangig RT1-Aufgaben, die von Hand
   zeitaufwendig, fehleranfällig und punktestark sind.
2. Vorhandene Parser-, Rationalfunktions-, Pol-/Nullstellen-, Frequenzgang-,
   Diagramm-, Diagnose-, Worked-Steps- und LaTeX-Infrastruktur wird
   wiederverwendet und nicht dupliziert.
3. Jeder produktive Feature-PR liefert einen vertikalen, sichtbaren Workflow:

   ```text
   Eingabe
   → Validierung
   → Fachanalyse
   → strukturierte Ergebnisse
   → Kontrollen
   → GUI
   → Worked Steps
   → LaTeX
   ```

4. Ein allgemeines CAS, ein zweiter Parser, eine zweite
   Rationalfunktionsbibliothek und eine zweite Frequenzgang-Engine sind
   ausgeschlossen.
5. Fachliche Quellenfehler werden nicht als Golden-Ergebnisse übernommen.
6. Große Infrastruktur wird nicht isoliert implementiert, wenn sie im selben PR
   durch einen sichtbaren Fachverbraucher geprüft werden kann.
7. Der aktuelle Prozentstand eines Codex-Kontingents ist kein
   Architekturprinzip. Er beeinflusst nur Startzeit, Zuschnitt und
   Testumfang eines konkreten PRs.

## 2. Aktueller nachgewiesener Stand in `main`

### 2.1 Projektfundament und technische Basis

Vorhanden sind insbesondere:

- Python-`src`-Layout und reproduzierbare Entwicklungsumgebung,
- pytest, Ruff und mypy,
- PySide6-GUI-Grundstruktur,
- strukturierte Diagnosen,
- sichere, begrenzte mathematische Eingabe ohne `eval`,
- exakte Ausdrücke und Polynommodelle,
- strukturtreue rohe algebraische Eingaben,
- rohe und reduzierte rationale Übertragungsfunktionen,
- dokumentierte Definitionsbedingungen und Kürzungsprovenienz,
- exakte Pol- und Nullstellenanalyse mit Vielfachheiten,
- numerische Kontrollwerte und Stabilitätsklassifikation,
- Worked Steps und LaTeX-Bericht.

### 2.2 Frequenzbereich

Vorhanden sind:

- numerischer komplexer Frequenzgang,
- Einzelpunkt- und logarithmische Rasterauswertung,
- Betrag, dB, Hauptphase und entfaltete Phase,
- Singularitätssegmente und lokale numerische Verfeinerung,
- numerische Bode-Diagramme,
- Frequenz-GUI und Berichtsweg,
- Standardglieder-/Bode-MVP.

Das Standardglieder-/Bode-MVP wurde mit PR 3 in `main` gemergt. Es unterstützt
den exakt bestätigten MVP aus:

- reellem Gesamtfaktor,
- Polen und Nullstellen im Ursprung,
- reellen LHP-Faktoren erster Ordnung,
- Vielfachheiten,
- exakter Rekonstruktionsprüfung,
- sortierten Knickereignissen,
- Anfangs- und Folgesteigungen,
- einer globalen kompakten Betragsasymptote,
- Worked-Steps- und LaTeX-Ausgabe.

Nicht unterstützte Faktoren erzeugen keine irreführende Teilzerlegung.

## 3. Unmittelbare Dokumentationsarbeit

Erledigt:

1. `docs/README.md` hinzugefügt.
2. Unterordner `docs/implementation/` angelegt.
3. Die vier Implementierungspakete und die Gesamtpriorisierung dorthin
   verschoben.
4. `ROADMAP.md` durch eine aktuelle Fassung ersetzt.
5. Der aktualisierte Architekturplan liegt als aktuelle verbindliche Fassung vor.

Noch zu prüfen:

- interne Links und Dateiverweise nach den Verschiebungen,
- Git-Status und sauberer Dokumentations-Commit,
- keine zusätzlichen Archiv- oder Dublettendateien.

## 4. Neue Intensivkurs-Unterlagen

Aktuell liegt nur Material zur ersten von vier Intensivkurs-Sitzungen vor.

Vorgehen:

1. Jede Sitzung wird nach Erhalt als Delta gegen Skript, Übungen,
   Tutoriumsunterlagen, Fachspezifikationen und Klausuren geprüft.
2. Relevante neue Aussagen werden mit Foliennummer und Kontext dokumentiert.
3. Ein einzelner Termin ändert die Roadmap nur bei einem klaren neuen
   Klausurhinweis, einer abweichenden Konvention oder einem besonders
   gewichteten Aufgabentyp.
4. Die Entwicklung wird nicht bis zum vollständigen Ende aller vier Sitzungen
   blockiert.
5. Vor dem Start eines betroffenen Feature-PRs wird das zu diesem Zeitpunkt
   verfügbare Intensivkursmaterial geprüft.

## 5. Verbindliche Feature-Reihenfolge

```text
F1  Frequenzsäule: Durchtritte, Reserven und Nyquist
↓
S1  kleiner Polynom-/Parameterkern + Hurwitz
↓
T1  Partialbruchzerlegung, inverse Laplace und Zeitantworten
↓
T2  DGL, direkte Laplace und Übertragungsfunktion
↓
S2  Routh
```

Diese Reihenfolge folgt dem erwarteten Klausurnutzen pro
Implementierungsressource, nicht der Reihenfolge der Vorlesung.

## 6. F1 – Durchtrittsfrequenzen, Reserven und Nyquist

### Umsetzungsstand F1A/F1B

F1A „Durchtrittsfrequenzen und Stabilitätsreserven“ ist implementiert: alle
sicher ermittelbaren Amplituden- und Phasendurchtritte im geprüften Band,
segmentlokale Verfeinerung, Phasen- und Amplitudenreserven, Bode-Markierungen,
GUI, Worked Steps und LaTeX. Mehrere und fehlende Durchtritte sowie begrenzte
oder unterbrochene Bänder besitzen explizite Statuswerte.

F1B „Nyquist“ folgt separat. F1A enthält keine Nyquist-Kurve, keine
Umschlingungszählung und keine P/N/Z- oder geschlossene Stabilitätslogik.

### Ziel

Den vorhandenen Frequenzworkflow um eine gemeinsame Auswertungs- und
Stabilitätsschicht ergänzen:

```text
G0(s)
→ vorhandene Frequenzdaten
→ Durchtritte
→ Reserven
→ Nyquist-Zählung
→ geschlossene Stabilitätsaussage
```

### Verbindlicher Umfang

- alle sicher gefundenen Amplitudendurchtritte,
- relevante Phasendurchtritte,
- Phasenreserve mit entfalteter Phase,
- Amplitudenreserve,
- offene Polklassifikation,
- Nyquist-Kurve auf vorhandener Frequenzinfrastruktur,
- Umschlingungszahl mit dokumentierter Vorzeichenkonvention,
- geschlossene Stabilitätsaussage,
- enger skalarer Verstärkungsmodus für belegte Fälle,
- Diagnosen, Worked Steps, GUI und LaTeX,
- offizielle Referenzfälle und analytische Grenzfälle.

### Harte Nichtziele

- kein neuer Frequenzgangsolver,
- kein Reglerentwurf,
- keine Wurzelortskurve,
- keine allgemeine komplexe Analysis,
- keine unbelegte Standardkontur bei Polen auf der imaginären Achse,
- keine Phasenreserve aus ungeeigneter Hauptphase,
- keine automatische Teilantwort mit scheinbarer Sicherheit.

### Abnahme

- fachliche Referenztests aus Skript, Übungen und beiden Klausuren,
- gezielte Unit- und Integrationstests,
- mindestens ein Presenter-/GUI-Smoke-Test,
- Worked-Steps- und LaTeX-Smoke-Test,
- manuelle Prüfung der zentralen Referenzfälle.

## 7. S1 – kleiner Polynom-/Parameterkern + Hurwitz

### Ziel

Einen kleinen gemeinsamen Kern ausschließlich zusammen mit seinem ersten
sichtbaren Verbraucher implementieren:

```text
charakteristisches Polynom
→ Kanonisierung und Gradfälle
→ Hurwitz-Bedingungen
→ exakte Parameterlösung
→ Stabilitätsbereich
```

### Verbindlicher Kernumfang

- bereits erzeugte charakteristische Polynome kanonisieren,
- Rolle, Annahmen, Ausschlüsse, Provenienz und Gradfälle erhalten,
- parameterabhängige Leitkoeffizienten sicher behandeln,
- atomare Gleichungen und Ungleichungen,
- parameterfreie Wahrheitswerte,
- exakte eindimensionale Lösungsmengen,
- begrenzte zweidimensionale Gebiete für belegte Klausurfälle,
- offene und geschlossene Grenzen korrekt darstellen,
- leere, teilweise gelöste und nicht unterstützte Ergebnisse unterscheiden.

### Verbindlicher Hurwitz-Umfang

- Grad 2 bis 4,
- Grad 1 nur als billiger Gradabfall-Fallback,
- Koeffizienten- und Determinantenbedingungen,
- parameterfreie, einparametrige und belegte zweiparametrige Fälle,
- strikte Stabilitätsgrenzen,
- GUI, Worked Steps und LaTeX,
- offizielle Klausurfälle als Regressionstests.

### Harte Nichtziele

- kein isolierter Infrastruktur-PR,
- kein Routh-Schema in S1,
- kein allgemeines semialgebraisches CAS,
- keine DGL-, Laplace- oder Regelkreisbildung im Kern,
- keine automatische fachliche Interpretation durch den Parameterlöser.

## 8. T1 – PBZ, inverse Laplace und Zeitantworten

### Ziel

Zuerst den fachlich unabhängigen rationalen Zeitbereichskern mit sichtbarem
End-to-End-Nutzen implementieren:

```text
F(s) oder G(s), U(s)
→ rationale Klassifikation
→ Polynomdivision
→ Partialbruchzerlegung
→ inverse Laplace
→ Zeitantwort
→ Kontrollen
```

### Verbindlicher Umfang

- echte, gleichgradige und unechte rationale Ausdrücke,
- Polynomdivision vor PBZ,
- einfache und mehrfache reelle Pole,
- irreduzible quadratische Faktoren und komplex konjugierte Pole,
- reelle Sinus-/Kosinusdarstellung,
- Sprung- und ausgewählte Standardantworten,
- Endwertsatz nur nach Polprüfung,
- Rückzusammenfassung jeder PBZ,
- Vorwärtstransformations- und Stichprobenkontrollen,
- GUI, Worked Steps und LaTeX.

### Harte Nichtziele

- kein allgemeiner ODE-Solver,
- keine numerische inverse Laplace-Transformation,
- keine beliebigen Spezialfunktionen,
- keine allgemeine Distributionstheorie,
- keine beliebigen stückweisen Signale.

## 9. T2 – DGL, direkte Laplace und Übertragungsfunktion

### Ziel

Den in T1 verifizierten Zeitbereichskern um strukturierte DGL- und
Eingangsworkflows ergänzen:

```text
lineare DGL + Anfangsbedingungen + Eingang
→ einseitige Laplace-Transformation
→ Y(s)
→ T1-Zeitbereichskern
→ y(t)
```

### Verbindlicher Umfang

- lineare SISO-DGL mit konstanten Koeffizienten,
- explizite Anfangsbedingungen,
- keine stillschweigende Nullannahme,
- direkte Laplace-Transformation der belegten Standardklasse,
- Übertragungsfunktion aus DGL nur bei Nullanfangsbedingungen,
- Bildung von Bildbereichsantworten,
- vollständige Übergabe an T1,
- Prüfung von Anfangsbedingungen, Vorwärtstransformation und DGL-Residuum,
- GUI, Worked Steps und LaTeX.

## 10. S2 – Routh

### Ziel

Routh später unter Wiederverwendung des in S1 implementierten
Polynom-/Parameterkerns ergänzen.

### Verbindlicher Umfang

- klausurrelevantes Standardschema,
- vollständige erste Spalte,
- Vorzeichenwechsel und Anzahl rechter Pole,
- Parameterbedingungen innerhalb des vorhandenen Kernvertrags,
- klar abgegrenzte Sonderfälle,
- GUI, Worked Steps und LaTeX,
- offizielle Übungs- und Tutoriumsreferenzen.

### Prioritätsgrenze

Routh folgt nach Hurwitz und den beiden Zeitbereichspaketen, solange neue
Intensivkurs- oder Klausurhinweise seine direkte Relevanz nicht erhöhen.

## 11. Spätere Kandidaten

Nach den fünf priorisierten Paketen werden neu bewertet:

- Regelkreisbildung und Führungs-/Störübertragungsfunktionen,
- Regler- und Korrekturgliedauslegung,
- Wurzelortskurve,
- Zustandsraum, Matrixexponential und Transitionsmatrix,
- Linearisierung,
- geführte mehrstufige Klausurworkflows,
- Workspace und Ergebnisübergabe,
- Quellenbrowser,
- Packaging und eingeschränkter Klausur-Build.

Ein visueller Blockschaltbildeditor bleibt bis auf Weiteres nachrangig.

## 12. Codex-Strategie

### 12.1 Chat- und Branch-Regel

- Ein neuer Feature-PR erhält einen neuen Codex-Chat.
- Implementierung, Reviewkorrekturen und Bugfixes desselben PRs bleiben im
  selben Codex-Chat.
- Nach dem Merge wird für den nächsten Feature-PR ein neuer Chat begonnen.
- Ein PR bearbeitet genau ein definiertes Roadmap-Paket.

### 12.2 Standardkonfiguration

Für substanzielle Feature-PRs:

```text
Modell: GPT-5.6 Sol
Aufwand: Mittel
Geschwindigkeit: Standard
```

`High` wird nur verwendet, wenn ein konkretes symbolisches,
numerisch-robustes oder architektonisches Problem dies rechtfertigt oder
`Medium` nachweislich nicht ausreicht.

Kleinere mechanische Dokumentations- oder Integrationsänderungen dürfen mit
einer günstigeren Konfiguration erfolgen, sofern keine Fachmathematik
entschieden wird.

### 12.3 Prompt-Regel

Jeder Codex-Prompt ist vollständig und direkt ausführbar. Er enthält:

- maßgebliche Referenzdateien,
- bestätigten Ausgangsstand,
- verbindlichen Umfang,
- harte Nichtziele,
- erwartete Dateien und Schichten,
- Tests und Abnahmekriterien,
- Git- und PR-Anweisungen,
- klare Rückmeldeanforderungen.

Keine nachträglichen fragmentarischen Ergänzungen, sofern nicht lediglich ein
konkret festgestellter Fehler innerhalb desselben PRs korrigiert wird.

### 12.4 Teststrategie pro Feature-PR

Während der Implementierung:

- gezielte Unit- und Integrationstests,
- Ruff und mypy nur auf relevanten Dateien,
- keine reflexartige Vollsuite nach jedem kleinen Schritt.

Vor Merge eines größeren Fachblocks:

- relevante erweiterte Tests,
- Presenter-/GUI-/LaTeX-Smoke-Tests,
- manuelle Referenzfälle.

Vor Klausur-Build oder größerem Release:

- vollständige Testsuite,
- Packaging- und Starttest,
- Offline- und Fehlerfallprüfung.

## 13. Ressourcenplanung

### 13.1 Aktueller Rahmen

Es verbleiben zwei vollständige Codex-Resets. Davon wird zunächst nur einer
für die normale Feature-Entwicklung eingeplant. Der zweite Reset bleibt als
Backup für unerwartete Implementierungsprobleme, Korrekturschleifen,
Integration, Packaging oder den Klausur-Build reserviert.

Zusätzlich steht das aktuelle Restkontingent vor dem nächsten Reset zur
Verfügung.

Verbindlicher Planungsrahmen:

```text
aktuelles Restkontingent
+ 1 Entwicklungs-Reset
+ 1 zunächst gesperrter Backup-Reset
```

Der Backup-Reset wird nicht vorsorglich in die Feature-Planung eingerechnet.
Er darf erst freigegeben werden, wenn ein konkreter Grund vorliegt oder die
priorisierten Pakete mit dem Entwicklungs-Reset nicht ausreichend weit
abgedeckt werden können.

### 13.2 Verwendungsregel

- Das aktuelle Restkontingent kann für Dokumentation, Review, kleine
  Korrekturen und gegebenenfalls einen klar begrenzten nächsten Schritt
  eingesetzt werden.
- Der Entwicklungs-Reset wird auf mehrere klar abgegrenzte Feature-PRs
  verteilt und nicht in einem einzigen Monolithen verbraucht.
- Der Backup-Reset bleibt bis zu einer ausdrücklichen Neubewertung unangetastet.
- Kein Paket erhält vorsorglich eine universelle Erweiterung.
- Bei unerwartet hohem Verbrauch wird zuerst am dokumentierten MVP-Rand
  gekürzt, nicht an fachlicher Korrektheit oder notwendigen Kontrollen.
- Ein funktionsfähiger, gemergter Teilumfang ist wertvoller als ein großer
  unvollständiger Branch.

### 13.3 Planungsrahmen für den Entwicklungs-Reset

| Bereich | relativer Entwicklungsrahmen |
|---|---:|
| F1 Frequenzsäule | hoch |
| S1 Kern + Hurwitz | hoch |
| T1 PBZ/Inverse/Zeitantwort | hoch |
| T2 DGL/Laplace | mittel |
| S2 Routh | niedrig bis mittel |
| Review, Integration und Bugfixes | verbindlicher Reserveanteil |

Die tatsächliche Verteilung wird nach jedem Merge anhand von Verbrauch,
Fehlerlage, Intensivkurs-Deltas und verbleibendem Klausurnutzen neu
entschieden.

### 13.4 Freigabekriterien für den Backup-Reset

Der Backup-Reset wird nur freigegeben, wenn mindestens einer der folgenden
Fälle eintritt:

- ein priorisierter Feature-PR bleibt trotz sauberer Spezifikation
  unvollständig,
- ein gemergter Kern benötigt eine größere fachliche Korrektur,
- Integration oder Packaging zeigt einen klausurrelevanten Blocker,
- der Entwicklungs-Reset reicht nachweislich nicht für die zentralen
  klausurrelevanten Pakete,
- neue offizielle Intensivkurs- oder Klausurhinweise erhöhen die Priorität
  eines bisher nicht eingeplanten Blocks wesentlich.

## 14. Definition of Done für einen Feature-PR

Ein Feature gilt erst als abgeschlossen, wenn:

1. der dokumentierte MVP vollständig implementiert ist,
2. keine verbotene Parallelarchitektur entstanden ist,
3. Voraussetzungen und Nicht-unterstützt-Fälle sichtbar sind,
4. exakte und numerische Kontrollen fachlich getrennt sind,
5. gezielte Tests bestanden sind,
6. GUI, Worked Steps und LaTeX den neuen Fachblock sichtbar verwenden,
7. offizielle Referenzfälle manuell plausibel geprüft wurden,
8. `ARCHITECTURE.md`, `DECISIONS.md`, `TEST_STRATEGY.md` und diese Roadmap
   auf Aktualisierungsbedarf geprüft wurden,
9. der PR klein genug bleibt, um fachlich überprüfbar zu sein,
10. der Branch nach erfolgreichem Merge bereinigt werden kann.

## 15. Nächste konkrete Schritte

1. Dokumentationsverschiebungen und interne Links prüfen.
2. Dokumentationsstand committen und in `main` übernehmen.
3. Material der ersten Intensivkurs-Sitzung als Delta prüfen.
4. F1-Implementierungspaket gegen den aktuellen Code in `main` final
   abgleichen.
5. Einen vollständigen Codex-Prompt für F1 erstellen.
6. F1 in einem neuen Feature-Chat und einem neuen Branch implementieren.
7. Nach gezielten Tests und manueller Prüfung mergen.
8. Ressourcenverbrauch und Roadmap neu bewerten.
9. Danach S1 als neuen Feature-PR starten.
