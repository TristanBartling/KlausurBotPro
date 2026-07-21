# KlausurBotPro – Architektur- und Implementierungsplan

**Status:** Arbeitsgrundlage für die weitere Umsetzung  
**Version:** 1.1 – token- und feedbackoptimierte Umsetzung  
**Stand:** 20.07.2026  
**Zweck:** Zusammenführung der vorhandenen Fachspezifikationen in eine gemeinsame technische Roadmap  
**Wichtig:** Dieses Dokument ersetzt bestehende Roadmaps im Codex-/Repository-Verzeichnis noch nicht. Vor einer Konsolidierung müssen die dort vorhandenen Roadmaps inventarisiert, verglichen und gezielt aktualisiert werden.

---

# 1. Projektziel

KlausurBotPro soll nicht jede mathematische Standardfunktion nachbauen. Das Programm soll vor allem RT1-Aufgaben automatisieren, die

- von Hand zeitaufwendig sind,
- eine hohe Fehlerwahrscheinlichkeit besitzen,
- in den aktuellen Klausuren viele Punkte tragen,
- aus mehreren aufeinanderfolgenden Rechenschritten bestehen,
- mit allgemeinen Werkzeugen wie Wolfram Alpha nur unzureichend klausurtauglich ausgegeben werden,
- vorhandene Parser-, Symbolik-, Frequenzgang-, Diagramm- und LaTeX-Infrastruktur wiederverwenden können.

Die App ist Teil einer Werkzeugstrategie und kein Selbstzweck.

## 1.1 Primäre Ressourcenbeschränkung

Der kritische Engpass ist nicht primär die verbleibende Kalenderzeit, sondern das verfügbare Codex-Tokenkontingent. Die Umsetzung wird deshalb nach **Nutzen pro Codex-Token** optimiert.

Maßgeblich sind:

- hoher Klausurpunktgewinn,
- große Rechenzeitersparnis,
- geringe Fehleranfälligkeit in der Klausur,
- starke Wiederverwendung vorhandener Funktionen,
- möglichst wenig Architekturwechsel,
- möglichst wenige Codex-Rückfragen und Korrekturschleifen,
- keine redundante Fachanalyse oder Dokumentation durch Codex.

Zwei Resets erlauben umfangreiche weitere Implementierung. Sie rechtfertigen aber keine unnötigen Doppelarbeiten, wiederholte Volltests ohne Anlass oder große universelle Abstraktionen ohne unmittelbaren Klausurnutzen.

## 1.2 Werkzeugaufteilung

## 1.2 Werkzeugaufteilung

### KlausurBotPro

- RT1-spezifische Mehrschritt-Workflows
- quellenkonforme Konventionen
- vollständige und nachvollziehbare Rechenwege
- strukturierte LaTeX-Ausgabe
- Diagramme und Tabellen
- automatische Übergabe von Zwischenergebnissen
- Warnungen bei fachlichen Sonderfällen

### Wolfram Alpha oder andere vorhandene Programme

- schnelle Faktorisierung
- einfache Nullstellen
- einfache Eigenwerte
- unabhängige Kontrollrechnung
- Standardableitungen und Integrale
- einfache algebraische Umformungen

### Papierunterlagen

- Formeltabellen
- Laplace-Tabelle
- Standardgliedertabelle
- Theorieübersichten
- Backup bei Softwareproblemen

---

# 2. Verbindliche Quellenbasis

## 2.1 Fachquellen

1. `skript.pdf`
2. `Regelungstechnik_Übung_Aufg-u-Lösungen.pdf`
3. `Regelungstechnik_Tutorium_komplett.pdf`
4. `RT_Klausur_SS2025-komplett.pdf`
5. `RT-Klausur_WS_25_26-komplett.pdf`
6. `Tabelle_Standardglieder.pdf`
7. `RT1_Rechenwege_Master(12).md` ergänzend

## 2.2 Fachspezifikationen

- `KlausurBotPro_Fachspezifikation_Standardglieder_Bode.md`
- `KlausurBotPro_Fachspezifikation_Nyquist_Reserven.md`
- `KlausurBotPro_Fachspezifikation_Hurwitz_Routh.md`
- `KlausurBotPro_Fachspezifikation_Charakteristische_Polynome_Parameterbedingungen.md`
- `RT1_Fachspezifikation_Laplace_PBZ_Zeitantworten.md`

## 2.3 Quellenregel

Jeder Fachblock muss unterscheiden zwischen

- direkter Quellenaussage,
- mathematischer Herleitung,
- technischer Implementierungsentscheidung,
- erkannter Quellenkorrektur,
- noch unsicherer Annahme.

Quellenfehler dürfen nicht stillschweigend in Referenztests übernommen werden.

---

# 3. Aktueller technischer Ausgangspunkt

Nach bisherigem Projektstand vorhanden:

- sicherer Parser für rationale Übertragungsfunktionen
- exakte Reduktion
- Roh- und reduzierte Übertragungsfunktion
- Pole und Nullstellen
- numerischer Frequenzgang
- Betrag und dB
- Hauptphase und entfaltete Phase
- logarithmisches Bode-Raster
- Singularitätssegmente
- lokale numerische Verfeinerung
- numerische Diagramme
- GUI-Grundstruktur
- Diagnosen
- numerische Kurzlösung
- LaTeX-Infrastruktur
- neuer LaTeX-Rechenweg-Renderer im Review

Vor Beginn des nächsten großen Branches ist der aktuelle LaTeX-Branch fachlich zu prüfen und zu mergen.

---

# 4. Architekturprinzipien

## 4.1 Vertikale Fachworkflows statt universeller CAS

Jeder Branch soll einen vollständigen, klausurtauglichen Workflow liefern:

\[
\text{Eingabe}
\rightarrow
\text{Analyse}
\rightarrow
\text{Ergebnis}
\rightarrow
\text{GUI}
\rightarrow
\text{Kontrolle}
\rightarrow
\text{LaTeX}.
\]

Die Reihenfolge bedeutet nicht, dass die GUI mathematisch vor der Kontrolle entsteht. Sie legt fest, dass jedes Feature im selben Branch sichtbar und benutzbar angebunden wird. Eine reine Backend-Funktion gilt nicht als abgeschlossen.

Nicht vorgesehen ist ein allgemeines Computeralgebrasystem.

## 4.2 Keine Doppelimplementierung

Bereits vorhandene Funktionen werden konsumiert, nicht neu geschrieben:

- Parser
- Polynom- und Rationalfunktionsdarstellung
- Pole und Nullstellen
- SymPy-Grundoperationen
- numerischer Frequenzgang
- Plot-Infrastruktur
- LaTeX-Bausteine
- bestehende Diagnostik

## 4.3 Exakt zuerst, numerisch zur Kontrolle

Soweit klausurrelevant:

- symbolische Eingaben exakt halten,
- rationale Werte nicht unnötig in Gleitkommazahlen umwandeln,
- numerische Ergebnisse getrennt als Kontrolle ausgeben,
- Rundung erst in der Darstellung durchführen.

## 4.4 Provenienz erhalten

Zwischenstufen müssen nachvollziehbar bleiben:

- rohe und reduzierte Übertragungsfunktion
- entfernte gemeinsame Faktoren
- charakteristisches Rohpolynom
- reduziertes Nennerpolynom
- Annahmen
- Ausschlussmengen
- Gradfälle
- verwendete Phasenäste
- Herkunft eines Ergebnisses

## 4.5 Kein unnötiger Featureumfang

Nicht vor dem Klausur-MVP priorisieren:

- grafischer Blockschaltbildeditor
- universeller Gleichungslöser
- beliebige Spezialfunktionen
- allgemeiner ODE-Solver
- Animationen
- allgemeine symbolische Matrixbibliothek
- vollständige Behandlung beliebiger Nyquist-Ausweichkonturen
- seltene Routh-Sonderfälle ohne Klausurnachweis


## 4.6 Sichtbarkeit und frühes Nutzerfeedback

Jeder produktive Feature-Branch muss unmittelbar über die vorhandene App erreichbar sein. Pflicht sind:

- eine funktionsfähige Eingabe,
- ein sichtbares fachliches Ergebnis,
- sichtbare Warnungen und Diagnosen,
- erreichbare LaTeX-Ausgabe,
- mindestens ein in der GUI ausführbarer offizieller Referenzfall.

Damit kann der Nutzer nach jedem Branch selbst prüfen:

- ob die Eingabe praktikabel ist,
- ob das Ergebnis fachlich plausibel erscheint,
- ob die Funktion in der Klausur tatsächlich Zeit spart,
- ob die GUI-Struktur verständlich bleibt.

Backend-only-Branches sind nur für sehr kleine, klar abgegrenzte Infrastrukturänderungen zulässig und sollen nach Möglichkeit mit dem ersten konsumierenden Fachfeature zusammengelegt werden.

## 4.7 GUI evolutionär statt spät oder beliebig

Die GUI wird weder vollständig an das Projektende verschoben noch nach jedem Feature improvisiert neu gebaut.

Verbindliches Verfahren:

1. Jedes Feature erhält im selben Branch eine minimale, produktive GUI-Anbindung.
2. Fachlich verwandte Features werden von Beginn an in demselben Arbeitsbereich eingeordnet.
3. Nach zwei bis drei verwandten Features erfolgt eine kurze GUI-Konsolidierung.
4. Erst nach stabilen Ergebnisverträgen wird eine größere Gesamtstruktur neu geordnet.

So bleiben neue Funktionen früh sichtbar, ohne dass die Oberfläche zu einer Sammlung zufälliger Einzelbuttons wird.

## 4.8 Codex-Tokenökonomie

Vor jedem Codex-Auftrag wird festgelegt:

- welche vorhandenen Dateien und Funktionen wiederverwendet werden,
- welche Fachspezifikation verbindlich ist,
- welches kleinste produktive Ergebnis erwartet wird,
- welche GUI-Stelle erweitert wird,
- welche wenigen Referenztests zwingend sind,
- welche Punkte ausdrücklich nicht umgesetzt werden.

Codex soll bestehende Architektur zuerst inspizieren und dann gezielt ändern. Große vorbereitende Kernbranches ohne sichtbaren Nutzerwert sind zu vermeiden, sofern der Kern zusammen mit dem ersten Fachworkflow implementiert werden kann.

---

# 5. Gesamtsystem: drei Rechensäulen

## 5.1 Säule A – Frequenzbereich

```text
Rationale Übertragungsfunktion
        ↓
Reduktion / Pole / Nullstellen
        ↓
Numerischer Frequenzgang
        ↓
Standardgliedererkennung
        ↓
Asymptotische Bode-Synthese
        ↓
Durchtrittsfrequenzen
        ↓
Amplituden- und Phasenreserven
        ↓
Nyquist-Analyse
        ↓
später: Regler- und Korrekturgliedauslegung
```

Diese Säule besitzt aktuell die höchste Wiederverwendung und das beste Verhältnis aus Klausurpunkten zu zusätzlichem Entwicklungsaufwand.

## 5.2 Säule B – Symbolische Stabilität

```text
Polynom aus Fachblock
        ↓
Polynomkanonisierung
        ↓
Grad- und Kürzungsfälle
        ↓
Fachblock erzeugt Bedingungen
        ↓
Parameterbedingungen lösen
        ↓
Intervall / 2D-Gebiet
        ↓
Randklassifikation / Testpunkte / LaTeX
```

Verbraucher:

- Hurwitz
- Routh
- Nyquist-Parameterfälle
- Wurzelortskurve
- spätere Reglerbedingungen

Der gemeinsame Kern kennt keine Stabilitätslogik. Er kanonisiert Polynome und löst bereits erzeugte Bedingungen.

## 5.3 Säule C – Zeitbereich

```text
Zeitfunktion oder DGL
        ↓
direkte Laplace-Transformation
        ↓
Bildbereich
        ↓
Partialbruchzerlegung
        ↓
inverse Laplace-Transformation
        ↓
Zeitantwort
        ↓
Anfangs-/Endwert- und Rücktransformationskontrolle
```

Die einfachen Tabellenfälle sind Bestandteil dieses Blocks. Die Papier-Laplace-Tabelle bleibt nur Backup.

---

# 6. Gemeinsame Domänenobjekte

Die endgültigen Typnamen richten sich nach der vorhandenen Codebasis. Fachlich werden folgende Verträge benötigt.

## 6.1 TransferFunctionAnalysis

Pflichtinhalte:

- rohe Übertragungsfunktion
- reduzierte Übertragungsfunktion
- Zähler und Nenner
- entfernte Faktoren
- Pole und Nullstellen mit Vielfachheiten
- freie Parameter und Annahmen
- Realisierbarkeitsstatus
- numerischer Frequenzworkflow
- Diagnosen

## 6.2 FrequencyResponseResult

- Frequenzsegmente
- komplexe Frequenzwerte
- Betrag
- dB
- Hauptphase
- entfaltete Phase
- Singularitäten
- lokale Verfeinerungen
- verwendeter Frequenzbereich

## 6.3 StandardElementDecomposition

- Gesamtverstärkung
- Ursprungspole
- Ursprungsnullstellen
- reelle Pole
- reelle Nullstellen
- komplexe Polpaare
- komplexe Nullstellenpaare
- Vielfachheiten
- Knickfrequenzen
- abgeleitete Fachlabels wie PT1, IT1, PI, PD, PIT1 oder PDT1
- nicht unterstützte beziehungsweise mehrdeutige Faktoren

Intern sollen primitive Faktoren dominieren. Zusammengesetzte Standardgliednamen sind Ausgabelabel.

## 6.4 CharacteristicPolynomialContract

- Hauptvariable \(s\)
- Koeffizienten in absteigender Reihenfolge
- deklarierter Grad
- mögliche Gradabfälle
- freie Parameter
- feste Konstanten
- Annahmen
- Ausschlussmengen
- Polynomrolle
- Analysebedeutung
- Provenienz
- Transformationshistorie
- entfernte Faktoren

## 6.5 ParameterConditionProblem

- höchstens zwei reelle Entscheidungsparameter
- Gleichungen
- strikte und nichtstrikte Ungleichungen
- Annahmen
- Ausschlussmengen
- Herkunft jeder Bedingung
- gewünschte Ergebnisform
- Vollständigkeitsanforderung

## 6.6 ParameterRegionResult

- exakte 1D-Intervallvereinigung oder beschränktes 2D-Gebiet
- offene und geschlossene Grenzen
- Randpunkte und Randkurven
- ausgeschlossene Mengen
- sichere Testpunkte
- numerische Kontrollwerte
- Vollständigkeitsstatus
- Diagnosen
- LaTeX-Darstellung

## 6.7 LaplaceWorkflowResult

- Originalausdruck
- Transformationsrichtung
- verwendete Regeln
- Bildbereichsausdruck
- Echtheitsprüfung
- Polynomdivision
- Pole und Vielfachheiten
- Partialbruchansatz
- Koeffizienten
- Zeitbereichsergebnis
- Anfangswertanteil
- erzwungener Anteil
- Kontrollen
- Diagnosen
- LaTeX-Rechenweg

---

# 7. Modulschnittstellen und Verantwortlichkeiten

## 7.1 Transferfunktionskern

Verantwortlich für:

- Parsing
- Rohform
- Reduktion
- Kürzungsprotokoll
- Pole und Nullstellen
- charakteristisches Nennerpolynom als Übergabeobjekt

Nicht verantwortlich für:

- Hurwitz-Bedingungen
- Nyquist-Umschlingungen
- Parametergebiete
- inverse Laplace

## 7.2 Standardglieder-/Bode-Block

Verantwortlich für:

- deterministische Faktorzerlegung
- Standardgliederklassifikation
- Knickfrequenzen
- asymptotische Betragssteigungen
- asymptotische Phasenbeiträge
- Summen-Bode
- Vergleich mit numerischem Bode
- klausurtaugliche Tabelle und LaTeX-Ausgabe

Nicht verantwortlich für:

- erneute Polberechnung
- erneuten numerischen Frequenzgang
- Reserven als primäre Aufgabe
- Nyquist-Zählung

## 7.3 Reserven-Block

Verantwortlich für:

- alle 0-dB-Durchtritte
- alle relevanten \(-180^\circ\)-Durchtritte der entfalteten Phase
- lokale Verfeinerung
- Phasenreserve
- Amplitudenreserve in dB
- Verstärkungsfaktorreserve
- additive lineare Reserve, sofern quellenkonform ausgegeben
- Mehrfachdurchtritte
- nicht vorhandene Durchtritte
- Warnungen bei instabilem offenen Kreis oder imaginärachsigen Polen

Nicht verantwortlich für:

- Standardgliedererkennung
- vollständige Nyquist-Umschlingungszählung

## 7.4 Nyquist-Block

Verantwortlich für:

- Polzahl \(P\) des offenen Kreises
- Ortskurve
- kritischen Punkt \(-1\)
- Umlaufsinn und Umschlingungszahl
- Bestimmung von \(Z\)
- allgemeines und vereinfachtes Nyquist-Kriterium
- Parameterfälle, soweit der kritische Wert aus der Ortskurve erzeugt wird
- Übergabe erzeugter Parameterbedingungen an den gemeinsamen Bedingungskern

Nicht verantwortlich für:

- allgemeinen Ungleichungslöser
- erneuten Frequenzgang
- allgemeine symbolische Polynomrechnung

## 7.5 Polynom- und Parameterkern

Benötigt exakt zwei öffentliche Fachoperationen:

```text
canonicalize_characteristic_polynomial(...)
solve_parameter_conditions(...)
```

Verantwortlich für:

- Kanonisierung
- Gradfälle
- Annahmen und Ausschlüsse
- exakte 1D-Mengen
- beschränkte 2D-Gebiete
- Schnitt und Vereinigung
- Redundanz
- offene und geschlossene Grenzen
- Testpunkte
- LaTeX

Nicht verantwortlich für:

- Hurwitz
- Routh
- Nyquist
- Wurzelort
- Regelkreisbildung

## 7.6 Hurwitz-Block

Verantwortlich für:

- notwendige Vorzeichenbedingungen
- Hurwitz-Matrix
- Hurwitz-Determinanten
- Grad 2 bis 4 im MVP
- symbolisch exakte Bedingungen
- strikte Randbedingungen für asymptotische Stabilität
- Übergabe an Parameterkern
- optional numerische Polkontrolle

Nicht verantwortlich für:

- Bildung des Regelkreises
- DGL- oder Laplace-Logik
- allgemeines 2D-CAS

## 7.7 Routh-Block

MVP:

- Standardschema
- Grad 2 bis 4
- erste Spalte
- Vorzeichenwechsel
- Stabilitätsaussage
- Gegenprüfung zu Hurwitz

Später:

- Null in erster Spalte
- vollständige Nullzeile
- Hilfspolynom
- allgemeine Sonderfälle

Routh hat in den analysierten Klausuren geringere direkte Priorität als Hurwitz.

## 7.8 Laplace-/PBZ-/Zeitantwort-Block

Verantwortlich für:

- direkte Standardtransformationen
- Linearität
- Ableitungssatz mit Anfangswerten
- ausgewählte Verschiebungs- und Dämpfungssätze
- rationale Bildbereichsausdrücke
- Polynomdivision
- PBZ mit einfachen und mehrfachen reellen Polen
- komplex konjugierte Pole
- inverse Laplace
- Sprung- und Impulsantwort
- allgemeine quellenrelevante Eingänge
- Anfangswertanteil und erzwungener Anteil
- Rückprüfung

Nicht im ersten MVP:

- beliebige stückweise Funktionen
- allgemeine Distributionen
- exotische Spezialfunktionen
- universelle Faltung
- allgemeiner ODE-Solver

---

# 8. Wiederverwendungsmatrix

| Vorhandene Funktion | Standardglieder/Bode | Reserven | Nyquist | Hurwitz | Parameterkern | Laplace |
|---|---:|---:|---:|---:|---:|---:|
| Parser rationale Funktionen | hoch | hoch | hoch | mittel | gering | hoch |
| Exakte Reduktion | hoch | hoch | hoch | hoch | mittel | hoch |
| Pole/Nullstellen | hoch | hoch | hoch | Kontrolle | gering | hoch |
| Numerischer Frequenzgang | Kontrolle | Kern | Kern | nein | nein | nein |
| Entfaltete Phase | Kontrolle | Kern | Kern | nein | nein | nein |
| Singularitätssegmente | mittel | hoch | hoch | nein | nein | nein |
| Lokale Verfeinerung | gering | Kern | hoch | nein | nein | nein |
| Symbolische Polynome | mittel | gering | mittel | Kern | Kern | hoch |
| LaTeX-Infrastruktur | hoch | hoch | hoch | hoch | hoch | hoch |
| Plot-Infrastruktur | hoch | hoch | hoch | mittel | hoch | mittel |
| Diagnose-System | hoch | hoch | hoch | hoch | hoch | hoch |

---

# 9. Verbindliche Implementierungsreihenfolge

Die Reihenfolge ist langfristig fachlich strukturiert, wird aber in **token-effiziente vertikale Pakete** geschnitten. Ein Paket darf mehrere eng gekoppelte interne Teilmodule enthalten, wenn dadurch Codex-Kontextwechsel und unsichtbare Vorbereitungsbranches entfallen.

## Phase 0 – aktuellen Stand stabilisieren

### Paket 0: aktueller LaTeX-Branch

Aufgaben:

1. wenige repräsentative Fälle manuell prüfen,
2. echte mathematische oder funktionale Fehler sammeln,
3. nur einen gebündelten Fixauftrag erzeugen,
4. Tests einmal vollständig ausführen,
5. mergen.

Keine zwanzig Varianten desselben Falls und keine neue Großfunktion vor dem Merge.

### Paket 0B: Repository- und GUI-Inventur

Ein kompakter Codex-Auftrag soll:

- vorhandene Roadmaps und Statusdateien auflisten,
- aktuelle GUI-Struktur und Erweiterungspunkte beschreiben,
- vorhandene wiederverwendbare Ergebnisansichten identifizieren,
- Widersprüche zum neuen Architekturplan markieren,
- noch nichts groß umbauen.

Ergebnis ist ein kurzer technischer Bericht als Grundlage für die folgenden Pakete.

---

## Phase 1 – Frequenzsäule abschließen

### Paket 1: `feat/standard-elements-bode`

Produktives Ergebnis:

- primitive Faktorzerlegung,
- Gesamtverstärkung,
- Ursprungspole und -nullstellen,
- reelle Pole und Nullstellen,
- klausurrelevante Vielfachheiten,
- zusammengesetzte Fachlabels als Ausgabe,
- Knickfrequenztabelle,
- asymptotischer Betrags- und Phasengang,
- Vergleich beziehungsweise Überlagerung mit dem vorhandenen numerischen Bode,
- vollständige GUI-Anbindung im bestehenden Frequenzarbeitsbereich,
- LaTeX-Rechenweg,
- wenige hochwertige Referenzfälle.

Nicht enthalten:

- Reserven,
- Nyquist-Umschlingungszählung,
- Reglerauslegung,
- neuer numerischer Bode-Kern.

### Paket 2: `feat/frequency-reserves`

Produktives Ergebnis:

- alle Verstärkungsdurchtritte,
- alle relevanten Phasendurchtritte,
- lokale numerische Verfeinerung,
- Phasenreserve,
- Amplitudenreserve in dB,
- Verstärkungsfaktorreserve,
- Behandlung mehrerer oder fehlender Durchtritte,
- Warnungen,
- Diagrammmarkierungen,
- GUI-Anbindung im selben Frequenzarbeitsbereich,
- LaTeX-Ausgabe.

Nach diesem Paket erfolgt eine kurze GUI-Konsolidierung des Frequenzbereichs:

```text
Frequenzanalyse
├── Grunddaten
├── Pole/Nullstellen
├── Standardglieder
├── Bode
├── Reserven
└── LaTeX
```

### Paket 3: `feat/nyquist`

Produktives Ergebnis:

- Ortskurve des offenen Kreises,
- kritischer Punkt \(-1\),
- offene RHP-Polzahl,
- Umschlingungszählung für klausurübliche rationale Fälle,
- allgemeines und vereinfachtes Nyquist-Kriterium,
- Verbindung zu den bereits berechneten Reserven,
- ausgewählte Parameter-Grenzwertfälle,
- Warnstatus für imaginärachsige Pole,
- sichtbare GUI-Anbindung im Frequenzarbeitsbereich,
- LaTeX-Rechenweg.

Spätere Erweiterung:

- vollständig allgemeine Ausweichkonturen,
- beliebig komplizierte Totzeitwindungen,
- exotische Singularitätslagen.

---

## Phase 2 – symbolische Stabilitätssäule

Zur Reduktion des Codex-Aufwands werden Polynomvertrag, notwendiger Parameterkern und Hurwitz zunächst als **ein vertikales Paket** umgesetzt. Die interne Trennung bleibt erhalten, aber der Nutzer wartet nicht mehrere Backend-Branches auf eine sichtbare Funktion.

### Paket 4: `feat/hurwitz-parameter-regions`

Interne Bestandteile:

1. charakteristisches Polynom kanonisieren,
2. Annahmen, Ausschlüsse und Gradfälle erhalten,
3. klausurrelevante einparametrige Bedingungen lösen,
4. die für die Referenzaufgaben notwendigen zweiparametrigen Gebiete lösen,
5. Hurwitz Grad 2 bis 4 auswerten,
6. Parametergebiet darstellen,
7. numerische Polkontrolle anbieten.

Produktives Ergebnis:

- direkte Polynomeingabe,
- optionale Übernahme eines vorhandenen Nennerpolynoms,
- Hurwitz-Matrix und Determinanten,
- exakte Bedingungen,
- Intervall oder 2D-Gebiet,
- offene und geschlossene Grenzen,
- Gebietsplot,
- Warnungen zu Gradabfall und Nennerausschlüssen,
- vollständige GUI-Anbindung,
- LaTeX-Rechenweg,
- SS2025- und WS25/26-Referenzfälle.

Harte Grenze:

- kein allgemeines 2D-CAS,
- nur die in den Fachspezifikationen nachgewiesenen Bedingungstypen,
- keine vorgelagerte DGL-, Laplace- oder Regelkreislogik duplizieren.

Nach erfolgreichem MVP darf der interne Kern später in eigene Module refaktoriert werden, aber nur bei echtem Wiederverwendungsbedarf.

### Paket 5: `feat/routh`

MVP:

- Standardschema Grad 2 bis 4,
- erste Spalte,
- Vorzeichenwechsel,
- Stabilitätsaussage,
- sichtbare GUI im Stabilitätsarbeitsbereich,
- LaTeX,
- Gegenprüfung zu Hurwitz.

Routh-Sonderfälle bleiben nachrangig, da keine direkte Klausurfundstelle vorliegt.

Stabilitätsarbeitsbereich:

```text
Stabilitätsanalyse
├── charakteristisches Polynom
├── Hurwitz
├── Routh
├── Parameterbereich
├── Gebietsplot
└── LaTeX
```

---

## Phase 3 – Zeitbereichssäule

Auch hier wird nicht zuerst ein unsichtbarer allgemeiner Transformationskern gebaut. Das erste Paket soll bereits direkte und inverse Standardfälle sichtbar lösen.

### Paket 6: `feat/laplace-pbz`

Produktives MVP:

- direkte Standardtransformationen,
- Linearität,
- Potenzen,
- Exponentialfunktionen,
- Sinus und Kosinus,
- ausgewählte Verschiebungen,
- Ableitungssatz mit Anfangswerten,
- einfache inverse Tabellenfälle,
- echte und unechte rationale Funktionen,
- Polynomdivision,
- einfache und mehrfache reelle Pole,
- irreduzible quadratische Faktoren,
- komplex konjugierte Pole,
- exakte Partialbruchkoeffizienten,
- Rückprüfung,
- sichtbare GUI,
- LaTeX-Rechenweg.

Diese Zusammenfassung in einem Paket ist token-effizienter als drei getrennte Codex-Kontextwechsel, solange der Auftrag intern klar gegliedert bleibt.

### Paket 7: `feat/time-response`

Produktives Ergebnis:

- \(Y(s)=G(s)U(s)\),
- Sprungantwort,
- Impulsantwort,
- quellenrelevante Exponential- und trigonometrische Eingänge,
- Anfangswertanteil,
- erzwungener Anteil,
- inverse Laplace,
- Endwert- und Plausibilitätskontrolle,
- sichtbarer Zeitbereichsarbeitsbereich,
- vollständiger LaTeX-Rechenweg.

Zeitbereichsarbeitsbereich:

```text
Laplace und Zeitantwort
├── direkte Transformation
├── Bildbereich
├── Partialbruchzerlegung
├── inverse Transformation
├── Zeitantwort
└── LaTeX
```

---

## Flexible Prioritätsentscheidung

Nach jedem produktiven Paket wird neu bewertet:

\[
\text{Nutzen pro verbleibendem Codex-Token}
=
\frac{
\text{Klausurpunkte}
\cdot
\text{Zeitersparnis}
\cdot
\text{Fehlervermeidung}
\cdot
\text{Wiederverwendung}
}{
\text{erwarteter Codex-Aufwand}
}.
\]

Die langfristige Säulenreihenfolge bleibt Orientierung, ist aber keine starre Verpflichtung. Nach Reserven kann beispielsweise Hurwitz vor vollständigem Nyquist vorgezogen werden, falls der erwartete Nutzen pro Token klar höher ist.

# 10. Spätere Fachblöcke

Nach Abschluss der drei Hauptsäulen neu priorisieren:

1. gezielte Zustandsraum- und Matrixworkflows
2. DGL zu Zustandsraum
3. Zustandsraum zu Übertragungsfunktion
4. Regelungs- und Beobachtungsnormalform
5. Eigenwerte, Jordanform und Transitionsmatrix
6. Wurzelortskurve
7. Reglerauslegung
8. Wendetangentenverfahren
9. Blockschaltbildreduktion ohne grafischen Editor
10. grafischer Blockschaltbildeditor nur bei nachgewiesenem Mehrwert

Ein universeller Matrixkern wird nicht neu implementiert. SymPy-/NumPy-Funktionen werden über klausurspezifische Workflows genutzt.

---

# 11. Teststrategie

## 11.1 Testpyramide

### Ebene A – kleine deterministische Kerntests

Nur für:

- Parserverträge
- Faktorzerlegung
- Knickereignisse
- Durchtrittsdetektion
- Polynomkanonisierung
- Intervalloperationen
- PBZ-Koeffizienten

### Ebene B – Fachreferenzfälle

Pro Branch wenige hochwertige Fälle aus:

- Skript
- offizieller Übung
- Tutorium
- SS2025
- WS25/26

### Ebene C – End-to-End-Klausurworkflow

Ein bis drei vollständige Aufgaben pro Modul:

- Eingabe
- Rechnung
- LaTeX
- Plot
- Diagnosen
- Ergebnisvergleich

## 11.2 Keine Testinflation

Nicht sinnvoll:

- dutzende nahezu identische numerische Varianten
- mehrfache Volltests ohne Codeänderung
- Tests für interne Bibliotheksfunktionen, die nicht projektspezifisch sind
- Testduplikate nur zur Erhöhung der Anzahl

## 11.3 Quellenfehler

Bei fehlerhaften Musterlösungen:

- fachlich korrektes Ergebnis testen,
- Quellenabweichung dokumentieren,
- keinen falschen Wert als Regressionserwartung verwenden.

---

# 12. LaTeX-Strategie

Jeder Fachworkflow liefert strukturierte Rechenschritte, nicht nur einen fertigen String.

Empfohlene Schichten:

1. fachliches Ergebnisobjekt
2. Rechenschrittmodell
3. LaTeX-Renderer
4. Kurzansicht
5. vollständige Lösung

Pflicht:

- eingesetzte Werte zeigen
- Vorzeichenkonventionen sichtbar machen
- Annahmen nennen
- offene und geschlossene Grenzen korrekt darstellen
- Näherungswerte von exakten Werten trennen
- keine behaupteten Schritte, die intern nicht gerechnet wurden

---

# 13. GUI-Strategie

## 13.1 GUI ist Bestandteil jedes produktiven Features

Eine Fachfunktion gilt nicht als abgeschlossen, wenn sie nur über Tests, interne APIs oder Kommandozeile erreichbar ist.

Jeder produktive Branch liefert:

- Eingabemöglichkeit,
- Startaktion,
- sichtbare Ergebnisansicht,
- Warnungen und Diagnosen,
- LaTeX-Zugriff,
- mindestens einen manuell prüfbaren Referenzfall.

Dadurch kann der Nutzer den Entwicklungsstand selbst bewerten, ohne auf Codex-Berichte zu vertrauen.

## 13.2 Bestehende GUI erweitern, nicht parallel neu bauen

Vor jeder GUI-Änderung wird geprüft:

- welcher vorhandene Arbeitsbereich fachlich passt,
- welche bestehenden Widgets, Tabellen und Plotflächen wiederverwendet werden können,
- ob ein neuer Tab wirklich nötig ist,
- wie Ergebnisse ohne erneute Eingabe weitergereicht werden.

Kein separater Werkzeugfriedhof und keine zweite parallele Oberfläche.

## 13.3 Fachlich zusammenhängende Arbeitsbereiche

Zielstruktur:

```text
Übertragungsfunktion / Frequenzanalyse
├── Grunddaten
├── Pole/Nullstellen
├── Standardglieder
├── Bode
├── Reserven
├── Nyquist
└── LaTeX
```

```text
Stabilitätsanalyse
├── charakteristisches Polynom
├── Hurwitz
├── Routh
├── Parameterbereich
├── Gebietsplot
└── LaTeX
```

```text
Laplace und Zeitantwort
├── direkte Transformation
├── Bildbereich
├── Partialbruchzerlegung
├── inverse Transformation
├── Zeitantwort
└── LaTeX
```

## 13.4 Konsolidierung in kurzen Intervallen

Nach zwei bis drei eng verwandten Feature-Erweiterungen:

- Navigation ordnen,
- doppelte Eingaben entfernen,
- Ergebnisübergaben vereinfachen,
- Tabellen und Plotflächen vereinheitlichen,
- überfüllte Ansichten reduzieren.

Diese Konsolidierung ist klein und zielgerichtet. Ein vollständiger GUI-Neubau bleibt nur dann gerechtfertigt, wenn die vorhandene Struktur nachweislich nicht mehr tragfähig ist.

## 13.5 Warnungen

Warnungen müssen fachlich klassifiziert sein:

- Eingabefehler,
- nicht unterstützter Fall,
- numerische Unsicherheit,
- Quellenkonflikt,
- Stabilitätsbegriff unklar,
- imaginärachsiger Pol,
- mehrere Durchtritte,
- Gradabfall,
- Nennerausschluss,
- Kürzung mit möglicher interner Dynamik.

# 14. Branch- und Codex-Arbeitsweise

Pro Codex-Paket:

1. Fachspezifikation und konkrete Quellendateien benennen.
2. Bestehenden Code und GUI-Erweiterungspunkt zuerst inspizieren.
3. Vorhandene Funktionen explizit wiederverwenden.
4. Kleinstes produktives, sichtbares MVP definieren.
5. Implementierung, GUI, LaTeX und wenige hochwertige Tests im selben Paket.
6. Keine parallele Ersatzarchitektur aufbauen.
7. Bestehende Tests nur ändern, wenn sich ein Vertrag bewusst ändert.
8. Codex-Bericht auf geänderte Dateien, Verträge, Tests und offene Risiken begrenzen.
9. Manuelle Prüfung mit wenigen offiziellen Referenzaufgaben.
10. Höchstens ein gebündelter Fixauftrag.
11. Merge und Roadmapstatus aktualisieren.

Tokenregeln:

- keine langen Fachanalysen durch Codex,
- keine erneute Zusammenfassung der vollständigen Spezifikationen,
- keine mehrfachen Volltests ohne relevante Codeänderung,
- keine große Dokumentation zusätzlich zu Fachspezifikation und knapper Entwicklernotiz,
- keine universellen Abstraktionen „für später“,
- keine getrennten Vorbereitungsbranches, wenn der Kern im ersten konsumierenden Feature sauber mitgebaut werden kann.

Fachanalyse, Referenzlösungen, Quellenkonflikte und Promptverdichtung werden möglichst in GPT-Chats vorbereitet.

---

# 15. Umgang mit bestehenden Roadmaps im Repository

Im Codex-/Repository-Verzeichnis existieren bereits Roadmaps und Planungsdateien. Diese dürfen nicht ungeprüft überschrieben werden.

## 15.1 Spätere Konsolidierung

Vor dem nächsten größeren Roadmap-Update:

1. alle vorhandenen Roadmap-, Plan- und Statusdateien auflisten,
2. Zweck und Aktualität jeder Datei feststellen,
3. Widersprüche zu diesem Architekturplan markieren,
4. erledigte Punkte aus alten Roadmaps übernehmen,
5. veraltete Architekturannahmen entfernen,
6. eine führende Roadmap festlegen,
7. alte Dokumente entweder archivieren oder eindeutig als historisch markieren,
8. Querverweise aktualisieren.

## 15.2 Vorläufige Dokumentenrollen

- **Dieser Architekturplan:** fachübergreifende technische Zielstruktur und Reihenfolge
- **Fachspezifikationen:** verbindliche Detailanforderungen je Rechenblock
- **Repository-Roadmap:** aktueller Umsetzungs- und Branchstatus
- **Changelog/Statusdatei:** bereits implementierte Änderungen
- **Codex-Berichte:** temporäre Implementierungsnachweise, keine führende Architekturquelle

## 15.3 Offene Repository-Aufgabe

```text
TODO: Bestehende Roadmaps im Codex-Verzeichnis inventarisieren und
gegen KlausurBotPro_Architekturplan.md abgleichen.
```

Sinnvoller Zeitpunkt: direkt nach Merge des aktuellen LaTeX-Branches oder spätestens vor Beginn der Symbolik-Säule.

---

# 16. Abnahmekriterien je Feature

Ein Feature gilt erst als abgeschlossen, wenn:

- Fachresultat korrekt ist,
- es über die normale App sichtbar und ausführbar ist,
- der Nutzer mindestens einen offiziellen Referenzfall selbst ausführen kann,
- Annahmen und Sonderfälle sichtbar sind,
- Quellenreferenz vorhanden ist,
- exakte und numerische Werte korrekt getrennt sind,
- GUI keine irreführenden Zustände zeigt,
- LaTeX den tatsächlichen Rechenweg wiedergibt,
- mindestens ein offizieller Referenzfall automatisiert geprüft wird,
- mindestens ein Grenz- oder Fehlerfall besteht,
- keine vorhandene Kernfunktion dupliziert wurde,
- Dokumentation und Roadmapstatus knapp aktualisiert wurden.

---

# 17. Aktuelle Priorität

## Unmittelbar

1. aktuellen LaTeX-Branch prüfen, gebündelt korrigieren und mergen,
2. bestehende Repository-Roadmaps und GUI-Struktur kompakt inventarisieren,
3. `feat/standard-elements-bode` als sichtbares End-to-End-Paket umsetzen,
4. Reserven in denselben Frequenzarbeitsbereich integrieren,
5. kurze Frequenz-GUI-Konsolidierung.

## Danach nach Nutzen pro Token entscheiden

Voraussichtliche Kandidaten:

1. Hurwitz einschließlich des dafür notwendigen kleinen Parameterkerns,
2. Nyquist auf Basis des vorhandenen Frequenzworkflows,
3. Laplace/PBZ als gemeinsames sichtbares Paket,
4. Routh-MVP,
5. Zeitantworten.

Die Entscheidung wird nach tatsächlichem Codex-Verbrauch und realem Implementierungsfortschritt getroffen, nicht allein nach der kalendarischen Restzeit.

# 18. Fachliche Risikopunkte

## Frequenzbereich

- Hauptphase statt entfalteter Phase
- mehrere Durchtritte
- fehlende Durchtritte
- negative Verstärkung
- instabiler offener Kreis
- Pole auf der imaginären Achse
- Totzeit
- künstliche Verbindung über Singularitäten

## Symbolik

- Roh- und reduziertes Polynom verwechselt
- entfernte Faktoren ignoriert
- Division durch parameterabhängigen Ausdruck
- Gradabfall übersehen
- Nennerausschluss vergessen
- offene Grenze fälschlich eingeschlossen
- Stichprobe als Beweis verwendet
- 2D-Solver wird unkontrolliert zum allgemeinen CAS

## Laplace

- Anfangswerte vergessen
- unechte rationale Funktion nicht dividiert
- falscher PBZ-Ansatz
- Mehrfachpol falsch behandelt
- komplexe Pole nicht reell zusammengeführt
- Übertragungsfunktion trotz nichtverschwindender Anfangswerte gebildet
- Kürzungen ohne Warnung
- fehlende Rückprüfung

---

# 19. Gesamtbewertung

Die wirtschaftlich sinnvollste Reihenfolge bleibt:

\[
\boxed{
\text{Frequenzsäule}
\rightarrow
\text{symbolische Stabilität}
\rightarrow
\text{Zeitbereich}
}
\]

Begründung:

- Der Frequenzbereich nutzt den größten bereits implementierten Unterbau.
- Der Symbolikkern wird von mehreren späteren Fachblöcken gemeinsam verwendet.
- Laplace/PBZ bietet hohe Zeitersparnis, benötigt aber einen größeren neuen Workflow.
- Matrix- und Zustandsraumaufgaben bleiben wichtig, werden aber nach Abschluss der aktuell besser spezifizierten und stärker wiederverwendbaren Säulen neu priorisiert.
- Einfache Einzelrechnungen dürfen weiterhin mit vorhandenen Werkzeugen gelöst werden.

---

# 20. Fortschritts- und Roadmap-Pflege

Nach jedem Merge knapp aktualisieren:

- implementierter Funktionsumfang,
- sichtbarer GUI-Zugang,
- offene Grenzfälle,
- wenige maßgebliche Referenztests,
- bekannte Quellenkonflikte,
- Paket-/Branchstatus,
- nächstes Paket,
- relevante Schnittstellenänderungen,
- grobe Einschätzung des verbleibenden Codex-Budgets,
- Abweichungen von diesem Architekturplan.

Die Roadmap-Pflege darf nicht zu einem eigenen großen Codex-Auftrag werden. Änderungen sollen kurz, konkret und zusammen mit dem Feature-Merge erfolgen.

Dieser Plan ist eine lebende technische Leitlinie. Fachliche Änderungen müssen aus Quellen oder aus eindeutig dokumentierten Implementierungserkenntnissen begründet werden.
