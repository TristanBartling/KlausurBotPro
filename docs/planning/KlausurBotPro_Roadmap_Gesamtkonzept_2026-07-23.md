# KlausurBotPro – Roadmap und Gesamtkonzept für die RT1-Klausur

**Stand:** 23.07.2026  
**Projekt:** KlausurBotPro / RT Tristan  
**Aktueller geprüfter Hauptstand:** `main`, einschließlich AI Operator Manual  
**Aktueller Merge-Commit des Manuals:** `5e9cacb7a226befde554d7a41dc0fdf5e524d146`  
**Planungsgrundlage:** `KlausurBotPro_Abschlussbericht_Gesamtkonzept(1).md`, reale GUI-Tests an Probeklausur, SS 2025 und WS 2025/26  
**Verfügbares Codex-Budget für aktuellen Bugfix-/Releaseblock und alle folgenden Blöcke:** ca. **120 %**

---

# 1. Projektziel

Das Ziel ist kein universelles Mathematikprogramm, sondern ein vollständiges und in der Klausur zuverlässig nutzbares System zur Bearbeitung möglichst aller typischen Aufgaben aus Regelungstechnik 1.

Für jeden Aufgabentyp muss eindeutig feststehen:

1. Wird er vollständig oder teilweise mit KlausurBotPro gelöst?
2. Wird ein vorhandenes externes Werkzeug wie Wolfram|Alpha verwendet?
3. Welche Schritte müssen manuell durchgeführt werden?
4. Welche Grundlagen müssen sicher verstanden oder auswendig verfügbar sein?
5. Welche statischen Unterlagen werden vor der Klausur vorbereitet?
6. Welche Ausgabe ist tatsächlich klausurtauglich und abschreibbar?

KlausurBotPro soll vor allem dort eingesetzt und erweitert werden, wo mindestens eines dieser Kriterien erfüllt ist:

- RT1-spezifischer Rechenweg,
- hoher historischer Klausurpunktwert,
- hohe manuelle Fehlerwahrscheinlichkeit,
- deutliche Zeitersparnis,
- vorhandene App-Kerne können wiederverwendet werden,
- externe CAS liefern keinen ausreichend kurs- und klausurkonformen Rechenweg,
- mehrere Aufgabentypen profitieren von derselben Erweiterung.

---

# 2. Verbindliche Grundstrategie

## 2.1 KlausurBotPro

Primäres Werkzeug für:

- rationale Übertragungsfunktionen,
- rohe und reduzierte Modelle,
- Pole und Nullstellen,
- DGL → Übertragungsfunktion,
- DGL mit Anfangswerten,
- Laplace und inverse Laplace,
- Partialbruchzerlegung,
- Zeitantworten,
- Zustandsraum-Grundaufgaben,
- Hurwitz und Routh,
- Stabilitätsparameterbereiche,
- Bode bei bekannter Übertragungsfunktion,
- Durchtritte und Reserven,
- Nyquist bei bekanntem offenen Kreis,
- Reglerauslegung,
- künftig Linearisierung,
- künftig begrenzte Standardregelkreise,
- künftig ausgewählte Vergleichs- und Plotfunktionen,
- gegebenenfalls später begrenzte MIMO-Zustandsmodelle.

## 2.2 Wolfram|Alpha und andere vorhandene Standardwerkzeuge

Externe Standardwerkzeuge sollen ausdrücklich dort verwendet werden, wo eine Eigenentwicklung im Verhältnis zum Klausurnutzen zu teuer ist.

Primäre Einsatzgebiete von Wolfram|Alpha:

- Jordan-Normalform,
- allgemeine Eigenwerte und charakteristische Polynome als Kontrolle,
- Wurzelortskurven,
- Faktorisierung und Nullstellenkontrolle,
- allgemeine symbolische Gleichungs- und Ungleichungssysteme,
- unabhängige Laplace-/PBZ-Kontrolle,
- Spezialfälle außerhalb des App-Scopes,
- schnelle Kontrollplots.

Wolfram|Alpha ist kein Ersatz für RT1-spezifische Notation, Voraussetzungen und bepunktete Rechenschritte. Es dient als Spezial- und Kontrollwerkzeug.

Vor der Klausur müssen für alle vorgesehenen Wolfram-Workflows konkrete, getestete Eingabebeispiele vorliegen.

## 2.3 Manuelle Bearbeitung

Manuell beherrscht werden müssen insbesondere:

- Aufgabentyp erkennen,
- physikalisches Modell und Vorzeichen verstehen,
- DGL korrekt aufstellen und umformen,
- offene und geschlossene Regelkreisgrößen unterscheiden,
- Nullanfangsbedingungen erkennen,
- sinnvolle Zustände wählen,
- Bode-Diagramme vom Papier rückwärts interpretieren,
- Blockschaltbilder lesen,
- Theorie-/MC-Aussagen bewerten,
- Voraussetzungen und Gültigkeitsbereiche erkennen,
- Ergebnisse plausibilisieren.

## 2.4 GPT-erstellte statische Hilfen

Ohne Codex werden erstellt:

- Theorie-Quick-Reference,
- MC-/Wahr-Falsch-Fallensammlung,
- Entscheidungsbaum für Aufgabentypen,
- KlausurBotPro-Syntaxkarte,
- Wolfram|Alpha-Eingabekarte,
- Methodenübersicht,
- Bedienungsabläufe,
- Auswendig-/Verständnisliste,
- Klausurstrategie,
- kompakte Notfall-Rechenwege.

Diese Hilfen werden vor der Klausur offline gespeichert und sind keine KI-Nutzung während der Prüfung.

---

# 3. Keine separaten selbstgebauten Python-/SymPy-Hilfsprogramme

Es werden keine zusätzlichen eigenen Skripte oder separaten Mini-Programme außerhalb von KlausurBotPro entwickelt.

Begründung:

- zusätzliche Bedienoberfläche oder Kommandozeile,
- eigene Eingabesyntax,
- keine automatische Wiederverwendung vorhandener App-Eingaben,
- getrennte Fehlerbehandlung,
- zusätzliche Start- und Testwege,
- keine einheitliche klausurtaugliche Ausgabe,
- keine automatische Aufnahme in das AI Operator Manual,
- höheres Fehlbedienungsrisiko unter Klausurbedingungen.

Entscheidungsregel:

- Ist eine Funktion klein, häufig nützlich und kann vorhandene App-Daten verwenden, wird sie in KlausurBotPro integriert.
- Ist eine Funktion allgemein, komplex und bereits zuverlässig verfügbar, wird Wolfram|Alpha oder ein anderes vorhandenes Standardwerkzeug verwendet.
- Ein separates eigenes Programm ist für dieses Projekt normalerweise die ungünstigste Zwischenlösung.

---

# 4. Beispielentscheidung: Pol-Nullstellen-Diagramm

## 4.1 Aktuelle technische Ausgangslage

KlausurBotPro berechnet Pole und Nullstellen bereits exakt und numerisch. Die App besitzt außerdem bereits eine eingebettete PySide6-/Matplotlib-Infrastruktur für Bode- und Nyquist-Diagramme.

Damit fehlen für einen einfachen Pol-Nullstellen-Plot nicht mehr:

- Parser,
- Transferfunktionsreduktion,
- Polberechnung,
- Nullstellenberechnung,
- Qt-Grundfenster,
- Matplotlib-Einbettung,
- Packaging und App-Start.

Neu benötigt werden hauptsächlich:

- Plot-View-Modell,
- Darstellung von Polen und Nullstellen,
- Achsenskalierung,
- Stabilitätsgrenze,
- Beschriftung,
- GUI-Einbindung,
- Tests,
- später optional Vergleich zweier Systeme,
- Operator-Manual-Aktualisierung.

## 4.2 Vergleich des Entwicklungsaufwands

Relative Aufwandsschätzung:

| Variante | Relativer Entwicklungsaufwand | Bewertung |
|---|---:|---|
| In KlausurBotPro integrierter PZ-Plot, ein System | **1,0** | sinnvoller Referenzfall |
| Separates eigenes GUI-Programm für denselben Plot | **ca. 1,1–1,4** | kein echter Gewinn; teilweise sogar teurer |
| Einfaches separates Skript ohne GUI | **ca. 0,3–0,5** | nicht gewünscht und in der Klausur unpraktischer |
| Nur Wolfram|Alpha verwenden | **ca. 0,05–0,1** eigener Entwicklungsaufwand | große Ersparnis, aber keine Integration, kein Vergleichsworkflow und keine klausurspezifische Ausgabe |

## 4.3 Schlussfolgerung

Wenn ein eigener GUI-Workflow gewünscht ist, spart eine Nichtintegration praktisch nichts. Ein separates GUI-Programm wäre voraussichtlich gleich teuer oder teurer, weil Infrastruktur dupliziert würde.

Eine echte Ersparnis entsteht nur, wenn vollständig auf Eigenentwicklung verzichtet und Wolfram|Alpha verwendet wird.

Für den Pol-Nullstellen-Plot ist die Integration in KlausurBotPro sinnvoll, weil:

- Pole und Nullstellen bereits vorhanden sind,
- Matplotlib bereits eingebettet ist,
- der Plot mehrere App-Module unterstützt,
- ein Systemvergleich direkt anschließbar ist,
- die Funktion in Klausuraufgaben unmittelbar bepunktet sein kann,
- die qualitative Interpretation mit denselben Daten erzeugt werden kann.

**Entscheidung:** Pol-Nullstellen-Diagramm als kleiner integrierter Featureblock, nicht als externes eigenes Programm.

---

# 5. Zuordnung typischer Klausuraufgaben

| Aufgabentyp | Primäres Werkzeug | Eigenleistung |
|---|---|---|
| Theorie und Multiple Choice | statische Theoriehilfe | Aussage und Voraussetzungen fachlich einordnen |
| DGL → \(G(s)\) | KlausurBotPro | Vorzeichen, Terme und Nullanfangsbedingungen |
| DGL → \(Y(s)\), \(y(t)\) | KlausurBotPro | Koeffizienten und Anfangswerte korrekt zuordnen |
| Laplace/PBZ | KlausurBotPro | Workflow und gesuchte Endstufe bestimmen |
| Pole und Nullstellen | KlausurBotPro | passendes Systemmodell bilden |
| Pol-Nullstellen-Diagramm | künftig KlausurBotPro | qualitative Interpretation kontrollieren |
| Zustandsstabilität | KlausurBotPro | Stabilitätsbegriff und Matrix auswählen |
| Zustandsmodell aufstellen | manuell, App teilweise | Zustände wählen und Gleichungen erster Ordnung bilden |
| Hurwitz/Routh | KlausurBotPro | charakteristisches Polynom und Analyseziel |
| Parametergebiet aus fertigen Bedingungen | künftig KlausurBotPro oder bis dahin Wolfram|Alpha | Bedingungen korrekt übertragen |
| Bode aus bekanntem \(G(s)\) | KlausurBotPro | Frequenzbereich und Standardglieder prüfen |
| Bode aus Papierdiagramm | manuell, danach App-Kontrolle | Pegel, Steigungen, Knicke und Glieder erkennen |
| Nyquist/Reserven | KlausurBotPro | offenen Kreis und Zählkonvention festlegen |
| Reglerauslegung | KlausurBotPro | Verfahren und Kennwerte erkennen |
| Standard-Rückführung | künftig KlausurBotPro | Topologie und Störort erkennen |
| Wurzelortskurve | Wolfram|Alpha | Vorgaben zu Dämpfung, Zeit und Gain interpretieren |
| Linearisierung | künftig KlausurBotPro | Arbeitspunkt und Modellbedeutung |
| Jordan-Normalform | Wolfram|Alpha | Konvention und Ergebnis prüfen |
| allgemeine Spezialalgebra | Wolfram|Alpha | relevante Ausgabe auswählen |

---

# 6. Was sicher verstanden oder auswendig verfügbar sein muss

## 6.1 Unbedingt sicher

1. Aufgabentyp erkennen.
2. Offenen und geschlossenen Kreis unterscheiden.
3. \(G_S(s)\), \(G_R(s)\), \(G_0(s)\), \(G_w(s)\) und Störübertragungsfunktionen unterscheiden.
4. Vorzeichen bei DGL und Rückkopplung kontrollieren.
5. Nullanfangsbedingungen bei Übertragungsfunktionen verstehen.
6. Rohes und reduziertes Modell unterscheiden.
7. Interne, E/A- und Zustandsstabilität unterscheiden.
8. Bode-Grundglieder aus Pegel, Steigung, Knick und Phase erkennen.
9. Nyquist-Grundlogik und Zählkonvention anwenden.
10. Plausibilitätskontrollen durchführen:
    - Realteile,
    - Einheiten,
    - Grenzfälle,
    - Anfangs- und Endwerte,
    - offene und geschlossene Parametergrenzen.

## 6.2 Nachschlagbar

- vollständige Laplace-Tabelle,
- Hurwitz-Matrizen höherer Ordnung,
- Regler-Einstelltabellen,
- Detailformeln der Standardglieder,
- seltene Routh-Sonderfälle,
- spezielle CAS-Syntax,
- seltene Theorieaussagen.

---

# 7. Roadmap

# Phase 1 – Aktuelle App stabilisieren und ersten Prüfungsstand festhalten

**Status bei Erstellung am 23.07.2026:** läuft bereits

**Zielrelease:** `v0.1.1-exam`

## Abschlussstatus vom 24.07.2026

Phase 1 ist fachlich und manuell abgenommen. Die vorgesehenen
Stabilisierungsarbeiten an Zeitbereich, Zustandsraum, Frequenzbereich,
Hurwitz/Routh, Transferfunktion und Reglerauslegung sind im
Release-Kandidaten `v0.1.1-exam` enthalten. KBP-P1-004 wurde nicht
reproduziert; KBP-P1-010 wurde als kein fachlicher Fehler eingeordnet, wobei
eine spätere UX-Verbesserung möglich bleibt. Die nachfolgenden Phasen und
größeren neuen Funktionen sind nicht Bestandteil dieses Releases.

## 1A. Kritische und irreführende Fehler

Zuerst korrigieren:

- falsche oder übertriebene Warnungen zu verborgener Dynamik,
- falsche gesuchte Größe,
- falscher oder unpassender umrahmter Endergebnisblock,
- unklare alte Ergebniszustände,
- unterschiedliche x-Achsenlimits von Bode-Betrag und Phase,
- technische Begriffe in klausurrelevanter Ausgabe,
- nicht verlangte Zusatzresultate als scheinbares Hauptergebnis.

## 1B. Bestehende starke Workflows klausurtauglich machen

### Hurwitz/Routh

- \(Z(s)\)/\(N(s)\),
- charakteristisches Polynom,
- Koeffizientenvergleich,
- notwendige Bedingungen,
- hinreichende Bedingungen,
- Redundanzen,
- Schnittmenge,
- exakte Endmenge,
- klausurtauglicher Ergebnisblock.

### Zeitbereich

- Analyseziel:
  - nur Bildgleichung,
  - nur \(Y(s)\),
  - \(Y(s)\) und PBZ,
  - vollständige Zeitantwort,
- gesuchte Größe korrekt umrahmen,
- unnötige Felder ausblenden,
- Koeffizienten eindeutig beschriften,
- faktorisierte Form bevorzugen,
- allgemeine Laplace-Regel vor dem Einsetzen.

### Zustandsraum

- Analyseziel „Zustandsstabilität“,
- Determinantenschritte,
- explizite Prüfung \(\operatorname{Re}(\lambda_i)<0\),
- Zustandsdefinition,
- Anfangszustand,
- nicht verlangte Übertragungsfunktion nachrangig.

### Frequenzbereich

- gemeinsame Bode-x-Achse,
- identische Frequenzpositionen,
- kompakte Wertetabelle,
- Vollraster nur optional,
- Standardglieder im LaTeX-Bericht,
- verständliche Rasterfehlermeldungen,
- sichere Frequenzvorschläge.

### Transferfunktion

- sinnvolle Rundung,
- qualitative Dynamikaussage,
- technische Zusatzblöcke einklappen,
- Warnungsprovenienz korrekt behandeln,
- Layout schrittweise angleichen.

### Reglerauslegung

- \(K_T\) statt \(L\),
- allgemeine Formel zuerst,
- konkrete Gültigkeitsprüfung,
- exakte Werte vor Näherungswerten,
- Strecke und Reglerverstärkung klar trennen.

## 1C. Referenztests

Erneut testen:

- Probeklausur-DGL mit Anfangswerten,
- SS25 Aufgabe 1d,
- SS25 Aufgabe 4b,
- WS25/26 Aufgabe 4b,
- WS25/26 Aufgabe 1d,
- WS25/26 Aufgabe 2c–2e,
- SS25 Aufgabe 3e,
- Parameter-Nyquist,
- Reglerauslegungsfälle,
- WS25/26 Aufgabe 3d.

## 1D. Releasebedingungen

- keine offenen S0-Probleme,
- keine kritischen S1-Probleme in vorhandenen Hauptworkflows,
- Referenzfälle bestanden,
- AI Operator Manual aktualisiert,
- Release-Commit und Git-Tag,
- lokale Sicherung,
- dokumentierter Startweg.

**Budgetrahmen:** ca. 25–30 von 120 Budgeteinheiten.

---

# Phase 2 – Kleine bis mittlere Erweiterungen mit hohem Nutzen

**Zielrelease:** `v0.2.0-exam`

## 2A. Pol-Nullstellen-Diagramm und qualitativer Vergleich

MVP:

- Pole als \(\times\),
- Nullstellen als \(\circ\),
- Stabilitätsgrenze,
- sinnvolle Achsenskalierung,
- exakte und numerische Werte,
- qualitative Aussage:
  - aperiodisch,
  - gedämpft schwingend,
  - instabil,
  - Integratoranteil,
- zunächst ein System,
- anschließend Vergleich von System A und B.

## 2B. Parametergebiet aus fertigen Bedingungen

Neue Eingabeart:

```text
Bedingungen / Ungleichungssystem
```

Ausgabe:

- kanonische Bedingungen,
- Randgleichungen,
- offene und geschlossene Grenzen,
- Schnittpunkte,
- zulässiges Gebiet,
- Testpunkt,
- Plot,
- LaTeX-Lösung.

Vorhandenen Parameterkern wiederverwenden.

## 2C. Standard-Rückführungsworkflow

Kein grafischer Editor.

Eingaben:

- \(G_R(s)\),
- \(G_S(s)\),
- optional Messglied,
- Rückführzeichen,
- Störort,
- gewünschte Übertragungsfunktion.

Ausgabe:

- allgemeine Formel,
- offener Kreis,
- Führungsübertragungsfunktion,
- relevante Störübertragungsfunktion,
- Einsetzen,
- Reduktion,
- Übergabe an weitere Module.

## 2D. Begrenzte Ergebnisübernahme

Zunächst nur:

- Transferfunktion → Frequenzbereich,
- Transferfunktion → Stabilität,
- Regelkreis → Transferfunktionsanalyse,
- System A und B → Vergleich.

Keine vollständige Sitzungs- oder Projektverwaltung.

**Budgetrahmen:** ca. 20–25 von 120 Budgeteinheiten.

---

# Phase 3 – Linearisierung MVP

**Zielrelease:** `v0.3.0-exam`

Historischer Nutzen:

- SS 2025: 10 Punkte,
- WS 2025/26: 10 Punkte.

## Umfang

Eingaben:

- eine nichtlineare Gleichung oder kleines Gleichungssystem,
- Zustandsvariablen,
- Eingänge,
- Ausgänge,
- Arbeitspunkt,
- Parameterbelegungen,
- Annahmen.

MVP-Grenzen:

- höchstens drei Gleichungen,
- expliziter Arbeitspunkt,
- Taylor-Linearisierung erster Ordnung,
- keine automatische physikalische Modellbildung,
- keine allgemeine DAE-Behandlung.

Ausgabe:

1. nichtlineares Modell,
2. Arbeitspunkt,
3. Abweichungsvariablen,
4. Taylor-/Jacobi-Ansatz,
5. partielle Ableitungen,
6. Auswertung am Arbeitspunkt,
7. linearisierte Gleichung,
8. gegebenenfalls \(A,B,C,D\),
9. Kontrolle am Arbeitspunkt,
10. klausurtauglicher Rechenweg.

**Budgetrahmen:** ca. 25–30 von 120 Budgeteinheiten.

---

# Phase 4 – Genau ein weiterer größerer Block

**Zielrelease:** optional `v0.4.0-exam`

Auswahl erst nach Phase 3 und erneuter Ressourcenprüfung.

## Option A – Begrenzter MIMO-Zustandsmodellassistent

- Nutzer gibt Zustandsreihenfolge an,
- mehrere Gleichungen,
- mehrere Eingänge,
- Gleichungen erster Ordnung,
- \(A,B,C,D\),
- Dimensionskontrolle,
- Vorschau,
- klausurtaugliche Darstellung.

## Option B – Manueller Bode-Diagramm-Deskriptor

Eingaben:

- Startpegel,
- Anfangssteigung,
- Knickfrequenzen,
- Steigungsänderungen,
- Phasenstart und -ende,
- vermutete Standardglieder.

Ausgabe:

- mögliche Standardglieder,
- mögliche Übertragungsfunktion,
- Konsistenzprüfung,
- asymptotische Rekonstruktion,
- Mehrdeutigkeitswarnung.

## Option C – Erweiterter Aufgaben- und Vergleichsworkflow

- Ergebnisse übernehmen,
- offene und geschlossene Systeme gemeinsam verwalten,
- zwei Systeme vergleichen,
- gemeinsame Diagramme,
- qualitative Differenz,
- kontrollierte Weitergabe zwischen Modulen.

**Budgetrahmen:** ca. 15–20 von 120 Budgeteinheiten.

---

# Phase 5 – GPT-Arbeitsstrang ohne Codex

Dieser Strang läuft parallel.

## 5A. Theorie-Quick-Reference

Für jedes Thema:

- Kernaussage,
- Voraussetzungen,
- typische Wahr/Falsch-Falle,
- kurze Begründung,
- genaue Quelle und Fundstelle.

## 5B. Methoden- und Entscheidungskarte

Für jeden Aufgabentyp:

- Erkennungsmerkmale,
- Methode,
- Werkzeug,
- Eingaben,
- typische Fehler,
- Plausibilitätsprüfung.

## 5C. KlausurBotPro-Syntaxkarte

- Transferfunktionen,
- Parameter,
- Annahmen,
- DGL-Koeffizienten,
- Matrizen,
- Frequenzen,
- typische Fehlermeldungen,
- Modulnavigation.

## 5D. Wolfram|Alpha-Karte

Vorbereitete Eingaben für:

- Root Locus,
- Jordanform,
- Eigenwerte,
- charakteristisches Polynom,
- PBZ,
- Laplace,
- Faktorisierung,
- Ungleichungssysteme,
- Kontrollplots.

Je Workflow:

- genaue Eingabe,
- erwartete Ausgabe,
- fachliche Kontrolle,
- mögliche Abweichung von RT1-Konventionen.

## 5E. Auswendig-/Verständnisliste

Entscheidungen, die ohne langes Suchen sicher funktionieren müssen.

---

# 8. Ressourcenplanung für 120 Budgeteinheiten

| Block | Geplanter Rahmen |
|---|---:|
| Phase 1: Bugfixing und `v0.1.1-exam` | 25–30 |
| Phase 2: High-Value-Erweiterungen | 20–25 |
| Phase 3: Linearisierung MVP | 25–30 |
| Phase 4: ein weiterer größerer Block | 15–20 |
| Reserve für Korrekturen, Tests und Releases | 15–20 |

Die Reserve wird nicht vorab als Featurebudget verwendet.

Jeder Entwicklungsblock benötigt:

1. Fachspezifikation durch GPT,
2. Implementierung durch Codex,
3. technische Tests,
4. reale GUI-Prüfung,
5. Korrekturschleife,
6. Operator-Manual-Aktualisierung,
7. Merge und Releasekontrolle.

---

# 9. Verbindlicher Entwicklungsprozess

## Schritt 1 – GPT-Fachspezifikation

Vor jedem Codex-Auftrag:

- reale Klausuraufgaben auswerten,
- Soll-Rechenweg festlegen,
- Eingaben und Ausgaben definieren,
- Scope begrenzen,
- Grenzfälle bestimmen,
- Akzeptanztests formulieren,
- wiederzuverwendende Komponenten identifizieren,
- Nicht-Ziele festlegen.

## Schritt 2 – Codex-Implementierung

Codex erhält nur:

- aktuellen Repository-Stand,
- konkrete Spezifikation,
- relevante Architekturpfade,
- klare Nicht-Ziele,
- Referenztests,
- Manual-Pflegeklausel,
- Stopbedingungen.

## Schritt 3 – Technische Prüfung

- Diff,
- Tests,
- Architekturgrenzen,
- keine unnötigen Nebeneffekte,
- keine unzulässige Scope-Erweiterung,
- Manual aktualisiert.

## Schritt 4 – Reale GUI-Prüfung

- Navigation,
- Eingabe,
- Interpretation,
- Ergebnis,
- Rechenweg,
- Diagramme,
- LaTeX,
- Fehlerzustände,
- Klausurtauglichkeit.

## Schritt 5 – Korrektur

Nur konkrete, reproduzierbare Abweichungen korrigieren.

## Schritt 6 – Merge und Zwischenstand

- PR prüfen,
- mergen,
- `main` aktualisieren,
- Referenztests,
- verbleibendes Kontingent neu bewerten.

---

# 10. Releases

## `v0.1.1-exam`

Stabilisierter heutiger Funktionsumfang.

## `v0.2.0-exam`

Vorgesehen:

- Pol-Nullstellen-Diagramm und Vergleich,
- Parametergebiet aus Bedingungen,
- Standard-Rückführungsworkflow,
- begrenzte Ergebnisübernahme.

## `v0.3.0-exam`

Vorgesehen:

- Linearisierung MVP.

## Optional `v0.4.0-exam`

Genau ein weiterer großer Block:

- MIMO-Assistent,
- Bode-Deskriptor oder
- erweiterter Vergleichsworkflow.

---

# 11. Nicht selbst implementierte Funktionen

Kurzfristig nicht selbst entwickeln:

- allgemeiner Wurzelortskurvenkern,
- universelle Jordan-/Matrix-CAS-Funktionen,
- universeller grafischer Blockschaltbildeditor,
- Foto-/OCR-Auswertung,
- allgemeine symbolische Mathematik,
- universelle MIMO-/DAE-Lösung.

Dafür werden Wolfram|Alpha oder manuelle Methoden verwendet.

---

# 12. Endabnahme

Das vollständige Klausursystem wird geprüft anhand von:

- SS 2025,
- WS 2025/26,
- bisheriger Probeklausur,
- mindestens einer weiteren unbekannten Probeklausur.

Für jede Teilaufgabe wird dokumentiert:

- App vollständig,
- App teilweise,
- Wolfram|Alpha,
- statische Theoriehilfe,
- manuell,
- Kombination.

Schlusskriterien:

- keine kritischen fachlichen Fehler,
- bekannte App-Grenzen dokumentiert,
- jeder häufige Aufgabentyp besitzt einen festen Bearbeitungsweg,
- keine erstmalige Werkzeugnutzung in der Klausur,
- offline verfügbare Kernunterlagen,
- getestete Wolfram-Eingaben,
- geprüfter App-Release,
- aktuelles AI Operator Manual.

---

# 13. Nächster konkreter Schritt

1. Abschlussbericht in ein verbindliches Stabilisierungsbacklog übersetzen.
2. Probleme mit ID, Schweregrad, exakter Reproduktion und Akzeptanzkriterium versehen.
3. Probleme nach gemeinsamer technischer Ursache in PR-Blöcke gruppieren.
4. Phase-1-Codex-Aufträge erstellen.
5. Referenztests erneut ausführen.
6. `v0.1.1-exam` festhalten.
7. Danach Phase 2 mit dem integrierten Pol-Nullstellen-Diagramm beginnen.
