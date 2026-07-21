# KlausurBotPro – Implementierungspriorisierung nach Expertenpaketen

**Datei:** `KlausurBotPro_Implementierungspriorisierung_nach_Expertenpaketen.md`  
**Status:** Gesamtpriorisierung, keine Implementierung, kein Codex-Prompt  
**Stand:** 21.07.2026  
**Entscheidungsziel:** maximale Klausurpunktabdeckung und Rechenzeitersparnis pro Codex-Ressource bei kontrollierbarem Integrationsrisiko

---

# 1. Verbindliche Ausgangslage

## 1.1 Aktueller technischer Stand in `main`

Bereits vorhanden und nicht erneut zu implementieren:

- sichere Eingabe rationaler Übertragungsfunktionen,
- rohe und reduzierte Übertragungsfunktion,
- exakte Reduktion und Kürzungsprovenienz,
- Pole und Nullstellen mit Vielfachheiten,
- numerischer komplexer Frequenzgang,
- logarithmisches Bode-Raster,
- Betrag und dB,
- Hauptphase und entfaltete Phase,
- Singularitätssegmente,
- lokale numerische Verfeinerung,
- numerische Diagramme,
- Worked Steps,
- LaTeX-Bericht,
- Standardglieder-/Bode-MVP.

Die Gesamtpriorisierung setzt voraus, dass dieser Stand stabil bleibt. Kein neues Paket darf einen zweiten Parser, eine zweite Rationalfunktionsbibliothek, eine zweite Frequenzgang-Engine oder eine parallele LaTeX-Infrastruktur einführen.

## 1.2 Geprüfte Eingangspakete

Geprüft wurden:

1. `docs/KlausurBotPro_Architekturplan.md`
2. `KlausurBotPro_Implementierungspaket_Frequenzsaeule_Nyquist_Reserven.md`
3. `KlausurBotPro_Implementierungspaket_Polynom_Parameterkern.md`
4. `KlausurBotPro_Implementierungspaket_Hurwitz_Routh.md`
5. `KlausurBotPro_Implementierungspaket_Zeitbereich_Laplace_PBZ_Zeitantworten.md`

Zusätzlich herangezogen wurden die zugehörigen Fachspezifikationen und die offiziellen Klausur-, Übungs- und Tutoriumsquellen.

Mehrfachuploads einzelner Paketdateien existieren. Für die Bewertung wurden die neuesten verfügbaren Fassungen verwendet. Die Priorisierung übernimmt keine Einzelentscheidung blind, sondern bewertet die Pakete gegeneinander.

## 1.3 Bewertungsregel für Klausurpunkte

Die Punkte sind historische Unterstützungswerte aus den Klausuren SS 2025 und WS 2025/26, keine Prognose für die nächste Klausur.

- **Direkte Punkte:** Das Paket liefert unmittelbar die verlangte Lösung einer bepunkteten Teilaufgabe.
- **Indirekte Folgepunkte:** Das Paket erzeugt notwendige oder stark wiederverwendbare Zwischenergebnisse für andere Teilaufgaben.
- Indirekte Punkte dürfen nicht über Pakete addiert werden, weil mehrere Pakete dieselbe Aufgabe unterstützen können.
- Widersprüchliche Punktangaben werden als Bereich dargestellt.
- Multiple-Choice-Punkte werden nur getrennt genannt, wenn sie aus den Quellen eindeutig zuordenbar sind.

---

# 2. Gesamtentscheidung

## 2.1 Empfohlene Reihenfolge

\[
\boxed{
\text{Frequenzsäule vollständig}
\rightarrow
\text{kleiner Polynom-/Parameterkern + Hurwitz}
\rightarrow
\text{Zeitbereich PR 1: PBZ/Inverse/Zeitantwort}
\rightarrow
\text{Zeitbereich PR 2: DGL/Laplace}
\rightarrow
\text{Routh}
}
\]

Die Reihenfolge folgt nicht der theoretischen Systematik der Vorlesung, sondern dem wirtschaftlichen Grenznutzen der noch fehlenden Software.

## 2.2 Harte Kernaussagen

1. **Die Frequenzsäule ist der nächste Feature-PR.** Sie besitzt die größte direkte historische Punktabdeckung, die höchste Wiederverwendung des vorhandenen Codes und den geringsten neuen Architekturanteil.
2. **Der Polynom-/Parameterkern darf nicht allein implementiert werden.** Er wird im selben PR wie Hurwitz gebaut und sofort durch offizielle Klausurfälle belastet.
3. **Hurwitz und Routh gehören nicht in denselben ersten PR.** Routh hatte in beiden Klausuren keine direkte Rechenfundstelle und würde den wichtigsten Stabilitäts-PR unnötig vergrößern.
4. **Der Zeitbereich darf nicht als Monolith umgesetzt werden.** Die technisch richtige Teilung ist PBZ/Inverse/Zeitantwort zuerst, DGL/Laplace danach.
5. **Ein unvollständiger Großbranch ist schlechter als ein späterer sauber gestarteter Branch.** Die aktuelle Restquote rechtfertigt keine künstliche Aufteilung des Frequenzpakets.

---

# 3. Abhängigkeitsgrafik

```text
main
│
├── vorhandener Rational-/Transferfunktionskern
│   ├── Pole / Nullstellen
│   ├── Reduktion / Kürzungsprovenienz
│   ├── numerischer Frequenzgang
│   └── Worked Steps / LaTeX / GUI-Grundstruktur
│
├── vorhandenes Standardglieder-/Bode-MVP
│   │
│   └── FEATURE-PR F1: Frequenzsäule
│       ├── alle Amplitudendurchtritte
│       ├── alle relevanten Phasendurchtritte
│       ├── Phasen- und Amplitudenreserven
│       ├── offene Polklassifikation
│       ├── Nyquist-Kurve und Umschlingungszahl
│       ├── geschlossene Stabilitätsaussage
│       └── enger skalarer Verstärkungsmodus
│           └── späterer Verbraucher: Regler-/Korrekturgliedauslegung
│
├── FEATURE-PR S1: kleiner gemeinsamer Polynom-/Parameterkern + Hurwitz
│   ├── Polynomkanonisierung und Gradfälle
│   ├── 0D-/1D-/enges 2D-Bedingungsproblem
│   ├── Hurwitz Grad 2–4
│   ├── Stabilitätsintervalle und Graphbänder
│   └── spätere Verbraucher
│       ├── FEATURE-PR S2: Routh
│       ├── optionaler Adapter für Nyquist-Parameterfälle
│       ├── Wurzelortskurvenbedingungen
│       └── spätere Regler- und Zustandsraumworkflows
│
└── FEATURE-PR T1: Zeitbereich PBZ-/Inverse-Kern
    ├── rationale Klassifikation
    ├── Polynomdivision
    ├── PBZ
    ├── inverse Laplace
    ├── Sprung- und allgemeine Ausgangsantwort
    └── FEATURE-PR T2: DGL-/Laplace-Orchestrierung
        ├── strukturierte lineare DGL
        ├── Anfangsbedingungen
        ├── Ableitungssatz
        ├── Bildung von Y(s)
        ├── Übertragungsfunktion bei Nullanfangswerten
        └── DGL-Residuum und Rückprüfung
```

## 3.1 Keine zwingende Abhängigkeit zwischen den drei Säulen

- Die Frequenzsäule benötigt den neuen Polynom-/Parameterkern **nicht** für ihren Grundumfang.
- Der enge skalare Nyquist-Verstärkungsmodus darf keine allgemeine Parameter-CAS-Schicht vorwegnehmen.
- Der Zeitbereich benötigt den neuen Stabilitätskern nicht.
- Hurwitz benötigt keine neue DGL-, Laplace- oder Regelkreislogik; es erhält ein bereits gebildetes Polynom.
- Routh hängt zwingend vom gemeinsamen Polynom-/Parameterkern ab.

---

# 4. Widersprüche zwischen den Expertenpaketen

## 4.1 Vollständiger Frequenz-PR oder zwei Teil-PRs

**Frequenzpaket:** empfiehlt einen gemeinsamen PR für Durchtritte, Reserven und Nyquist.  
**Allgemeines Risikoargument:** kleinere PRs sind leichter zu reviewen.

### Auflösung

Der gemeinsame Frequenz-PR bleibt richtig. Die Teilfunktionen verwenden dieselben:

- Frequenzsegmente,
- lokalen Evaluatoren,
- Phasenäste,
- Singularitätsgrenzen,
- Diagrammmarker,
- Statusmodelle,
- Presenter- und LaTeX-Strukturen.

Eine Aufteilung in Reserven und Nyquist erhöht laut Paket den Gesamtaufwand voraussichtlich auf das 1,20- bis 1,40-Fache. Die Branchgröße wird durch interne Gates kontrolliert, nicht durch zwei künstliche PRs.

**Konfliktstatus:** aufgelöst zugunsten eines vollständigen Frequenz-PRs.

## 4.2 Isolierter Polynomkern oder gemeinsamer PR mit Hurwitz

**Polynomkernpaket:** beschreibt einen neutralen gemeinsamen Kern.  
**Architekturplan:** warnt vor unsichtbaren Infrastruktur-PRs ohne ersten Verbraucher.  
**Hurwitzpaket:** verlangt kleinen Kern und Hurwitz in einem PR.

### Auflösung

Der Kern wird fachlich getrennt, aber technisch gemeinsam mit Hurwitz geliefert:

```text
shared polynomial/parameter domain
shared canonicalization and condition solving
        ↑
Hurwitz consumer
```

Ein isolierter Kern-PR hätte null direkte Klausurpunkte, doppelte Repository-Inspektion, abstrakte Testfälle und hohe spätere Vertragskorrekturwahrscheinlichkeit.

**Konfliktstatus:** aufgelöst zugunsten `Kern + Hurwitz` in einem vertikalen PR.

## 4.3 Hurwitz und Routh gemeinsam oder getrennt

**Architektur:** nennt beide Verfahren in derselben Stabilitätssäule.  
**Hurwitzpaket:** schließt Routh ausdrücklich aus dem ersten PR aus.

### Auflösung

Hurwitz und Routh teilen den Kern, aber nicht den ersten Feature-PR.

- Hurwitz besitzt direkte historische Klausurpunkte.
- Routh besitzt keine direkte Rechenfundstelle in den beiden Klausuren.
- Routh benötigt eigene Tabellenobjekte, Divisionsbedingungen, Vorzeichenwechselzählung, GUI und Cross-Tests.
- Eine gemeinsame Umsetzung würde den wichtigsten Stabilitätsbranch unnötig vergrößern.

**Konfliktstatus:** aufgelöst; Hurwitz zuerst, Routh später.

## 4.4 Zeitbereich als Monolith oder als zwei PRs

**Architekturprinzip:** bevorzugt vollständige vertikale Workflows.  
**Zeitbereichspaket:** lehnt sowohl den Monolithen als auch „DGL zuerst“ ab und empfiehlt PBZ/Inverse zuerst.

### Auflösung

Die Teilung ist nicht künstlich, sondern folgt der technischen Abhängigkeit:

```text
PBZ/Inverse-Kern
        ↓
DGL/Laplace-Orchestrierung
```

PR T1 ist bereits sichtbar und vollständig ab \(F(s)\), \(G(s)\) oder \(G(s),U(s)\). PR T2 konsumiert danach einen verifizierten inversen Kern. Ein Gesamtmonolith hätte zu viele neue Verträge und eine zu große Korrekturfläche.

**Konfliktstatus:** aufgelöst zugunsten von zwei produktiven Zeitbereichs-PRs.

## 4.5 Nyquist-Parametermodus versus gemeinsamer Parameterkern

**Frequenzpaket:** enthält einen engen skalaren Verstärkungsmodus.  
**Polynomkernpaket:** sieht Nyquist-Parameterfälle als späteren Verbraucher des allgemeinen 1D-Kerns.

### Offener Konflikt und verbindliche Zwischenlösung

Der Frequenz-PR darf vor dem gemeinsamen Kern:

- kritische skalare Verstärkungswerte,
- offene beziehungsweise geschlossene Intervalle,
- explizite Domain,
- unbeschränkte Intervalle

als **Nyquist-spezifisches Ergebnis** liefern.

Er darf nicht:

- ein allgemeines Condition-AST,
- einen allgemeinen 1D-Ungleichungslöser,
- allgemeine 2D-Parametergebiete,
- Hurwitz-/Routh-unabhängige Mengenalgebra

einführen.

Nach Implementierung des gemeinsamen Kerns kann ein Adapter geprüft werden. Eine sofortige Migration ist nur erlaubt, wenn sie echte Doppelarbeit entfernt und keine stabile Frequenzschnittstelle aufbricht.

**Konfliktstatus:** fachlich offen, technisch begrenzt und beherrscht.

## 4.6 Vollsuite versus sparsamer Testbetrieb

**Paketdokumente:** sehen eine vollständige Suite am Ende großer PRs vor.  
**Aktueller Budgetkontext:** verbietet Volltests nach kleinen Änderungen.

### Auflösung

- interne Gates: nur betroffene Unit- und Integrationsprüfungen,
- nach einer tiefen zentralen Vertragsänderung: gezielte Querschnittsregression,
- genau einmal vor Merge eines großen PRs: vollständige Repository-Suite,
- keine Vollsuite nach jedem Commit oder Fix.

**Konfliktstatus:** aufgelöst.

---

# 5. Vergleichsmatrix der empfohlenen PR-Einheiten

Skalen:

- Rechenzeitersparnis, Handfehler, vorhandene Wiederverwendung und spätere Wiederverwendung: 1 = niedrig, 5 = sehr hoch.
- Architekturaufwand, Codex-Verbrauch, Test-/Review-Risiko: 1 = niedrig, 5 = sehr hoch.
- Codex-Verbrauch ist relativ. Es werden keine Tokenzahlen behauptet.

| Rang | PR-Einheit | Direkte historische Punkte | Indirekt unterstützte Folgepunkte | Rechenzeit | Handfehler | vorhandene Wiederverwendung | neuer Architekturaufwand | erwarteter Codex-Verbrauch | Test-/Review-Risiko | Korrekturschleifen | Abhängigkeit | spätere Wiederverwendung | vollständiger gegenüber geteiltem Branch |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---:|---|
| 1 | **F1 Frequenzsäule: Durchtritte, Reserven, Nyquist** | **30–38** über beide Klausuren | mindestens **8** für Korrekturgliedauslegung; weitere Diagnose-/Reglerworkflows nicht sicher bepunktbar | 5 | 5 | **5** | 2–3 | 3–4 | 4 | mittel bis hoch | Standardglieder-/Bode-MVP | **5** | vollständiger PR klar günstiger; Teilung ca. 1,20–1,40 Gesamtaufwand |
| 2 | **S1 kleiner Polynom-/Parameterkern + Hurwitz** | **27** Nicht-MC; zusätzlich bis zu **2 MC** | technisch bis zu **17** historische Punkte in späteren Nyquist-/WOK-Adaptern, nicht automatisch realisiert | 5 | 5 | 3 | **5** | **4–5** | **5** | hoch | keine neue Fachabhängigkeit; benötigt Vertragsfreeze | **5** | Kern allein wirtschaftlich schlecht; Hurwitz+Routh dagegen zu groß |
| 3 | **T1 PBZ-/Inverse-Laplace-/Zeitantwort-Kern** | in den zwei Klausuren kein isolierter sicherer Punktblock | unterstützt unmittelbar T2 und damit mindestens den verifizierten 5-Punkte-DGL-Pfad; hohe Übungsrelevanz | **5** | **5** | 4–5 | 4 | **4–5** | **5** | hoch | vorhandener Rationalkern | **5** | als vollständiger PBZ-Workflow sinnvoll; nicht auf einfache Pole verkleinern |
| 4 | **T2 DGL-/Laplace-Orchestrierung** | **5** sicher verifizierte Punkte; MC-Anteil nicht separat zuordenbar | Zeitantwort-, Anfangswert- und Übertragungsfunktionsworkflows; keine weitere sichere Punktzahl aus den zwei Klausuren | 4 | 4 | 4 | 3–4 | 3–4 | 4 | mittel bis hoch | zwingend T1 | 5 | eigenständiger zweiter PR ist natürliche Teilung |
| 5 | **S2 Routh** | **0** direkte Rechenpunkte in den zwei Klausuren | Kontrolle und Alternativlösung zu Hurwitz; keine zusätzlichen historischen Punkte | 4 | 4 | 4 nach S1 | 3 | 2–3 | 3–4 | mittel | zwingend S1 | 4 | eigener späterer PR; nicht in S1 hineinziehen |
| – | **isolierter Polynom-/Parameterkern ohne Verbraucher** | 0 | potenziell hoch, aber zunächst unsichtbar | 0 | 0 | 3 | 5 | 3–4 | 5 | hoch | keine | 5 theoretisch | **nicht durchführen** |

## 5.1 Punktableitung Frequenzsäule

Historisch direkt unterstützt:

- SS 2025 Reserven: 4 Punkte,
- SS 2025 Nyquist: 12 Punkte,
- WS 2025/26 Phasenreserve: 2 bis 10 Punkte wegen widersprüchlicher Unterlagen,
- WS 2025/26 Nyquist: 12 Punkte.

\[
4+12+(2\ldots10)+12
=
\boxed{30\ldots38}
\]

Die 8 Punkte für das SS-Korrekturglied werden nur indirekt unterstützt, da Reglerauslegung ausdrücklich nicht zum Frequenzpaket gehört.

## 5.2 Punktableitung Kern + Hurwitz

Historisch direkt beziehungsweise als vollständige Stabilitätspipeline unterstützt:

- SS 2025 Hurwitz: 10 Punkte,
- SS 2025 Parametergebiet: 7 Punkte,
- WS 2025/26 Hurwitz: 10 Punkte,
- zusätzlich bis zu 2 Punkte Hurwitz-Theorie im MC-Block.

\[
10+7+10
=
\boxed{27}
\]

Die 7 Gebietspunkte rechtfertigen den engen 2D-Graphbandkern. Sie rechtfertigen kein allgemeines 2D-CAS.

## 5.3 Punktableitung Zeitbereich

Direkt sicher gefunden:

- SS 2025 DGL \(\rightarrow\) Übertragungsfunktion: 5 Punkte.

PBZ, inverse Laplace und explizite Zeitantworten sind in den offiziellen Übungen und Tutorien stark vertreten, aber in den beiden Klausuren nicht als eigenständiger sicher bepunkteter Rechenteil nachgewiesen. Der hohe Nutzen beruht deshalb primär auf Rechenzeitersparnis, Fehlervermeidung und zukünftiger Klausurrobustheit, nicht auf einer höheren historischen Punktzahl.

---

# 6. Empfohlene vollständige Feature-PR-Reihenfolge

## PR F1 – Frequenzsäule vollständig

**Branch-Ziel:** Durchtritte, Reserven und Nyquist in einem gemeinsamen, intern gegateten PR.

### Pflichtumfang

- alle Amplitudendurchtritte,
- alle relevanten Phasendurchtritte der entfalteten Phase,
- Kreuzungsrichtung und Residuen,
- Mehrfachdurchtritte,
- Phasenreserve je Amplitudendurchtritt,
- Amplitudenreserve in dB und als Faktor,
- offene RHP-Polzahl mit Vielfachheit,
- vollständige Nyquist-Kurve innerhalb der unterstützten Kontur,
- primäre und unabhängige Winding-Kontrolle,
- \(N_{\mathrm{cw}}\), \(P\), \(Z\),
- vollständiges und vereinfachtes Nyquist-Kriterium,
- enger skalarer Verstärkungsmodus,
- GUI, Diagramme, Worked Steps und LaTeX,
- sichere Abbrüche bei nicht unterstützten Konturen.

### Interne Gates

1. Durchtrittsobjekte und lokale Verfeinerung.
2. Reserven und Mehrfachdurchtritte.
3. offene Polklassifikation.
4. Nyquist-Kurvenaufbau.
5. Winding und Stabilitätsaussage.
6. enger Skalarparameter.
7. GUI-/LaTeX-Konsolidierung.
8. finale Regression.

### Warum nicht teilen

Eine Teilung würde dieselben Verträge, Phasenregeln, Diagramme und Presenter zweimal öffnen. Das wäre Kleinst-PR-Formalismus statt Ressourceneffizienz.

## PR S1 – kleiner Polynom-/Parameterkern + Hurwitz

**Branch-Ziel:** erster sichtbarer Verbraucher des gemeinsamen symbolischen Kerns.

### Pflichtumfang des neutralen Kerns

- Polynomrolle, Analyseziel und Provenienz,
- Kanonisierung und Rekonstruktionsprüfung,
- nominale und effektive Grade,
- wiederholter Gradabfall,
- Null- und konstante Fälle,
- Vorzeichennormierung ohne unnötige monische Division,
- parameterfreier 0D-Vertrag,
- exakter 1D-Löser für den belegten Umfang,
- enges 2D-Graphband:
  - \(x>x_{\min}\),
  - lineare Untergrenze,
  - quadratische Obergrenze,
  - offene/geschlossene Ränder,
  - sichere Testpunkte,
- vollständige, teilweise sichere und nicht unterstützte Zustände.

### Pflichtumfang Hurwitz

- Grade 2–4,
- Grad 1 nur als billiger Gradabfall-Fallback,
- Hurwitz-Matrix,
- Determinanten,
- vollständige und minimale Bedingungslisten getrennt,
- interne, Zustands- und externe E/A-Rollen sauber trennen,
- exakte Parameterbereiche,
- Gebietsplot,
- offizielle SS- und WS-Referenzfälle,
- numerische Polgegenprüfung,
- GUI, Worked Steps und LaTeX.

### Nicht enthalten

- Routh,
- allgemeine semialgebraische 2D-Zerlegung,
- rationale 2D-Kurven ohne sichere Reduktion,
- DGL-/Laplace-/Regelkreisbildung,
- allgemeine Stabilitätslogik im neutralen Kern.

## PR T1 – PBZ-/Inverse-Laplace-/Zeitantwort-Kern

**Branch-Ziel:** vollständiger sichtbarer Workflow ab rationalem Bildbereichsausdruck oder Übertragungsfunktion.

### Pflichtumfang

- direkte und inverse Standardpaare im belegten Umfang,
- rollenbezogene Rationalklassifikation,
- Polynomdivision,
- einfache reelle Pole,
- mehrfache reelle Pole,
- irreduzible quadratische Faktoren,
- komplex konjugierte Pole mit reeller Sinus-/Kosinusausgabe,
- exakter PBZ-Ansatz,
- exakte Koeffizientenbestimmung,
- Rückzusammenfassung,
- inverse Laplace aus \(F(s)\),
- Sprungantwort aus \(G(s)\),
- allgemeine Ausgangsantwort aus \(G(s)\) und direktem \(U(s)\),
- mindestens ein Exponentialeingang,
- Anfangs- und Endwertkontrollen,
- Pol- und Kürzungswarnungen,
- Vorwärtstransformationskontrolle,
- GUI, Worked Steps und LaTeX.

### Nicht verkleinern auf

- nur einfache Pole,
- nur numerische PBZ,
- Black-Box-`apart` ohne nachvollziehbaren Ansatz,
- Black-Box-Inverse ohne Rückprüfung.

## PR T2 – DGL-/Laplace-Orchestrierung

**Branch-Ziel:** vollständiger Workflow ab strukturierter linearer SISO-DGL.

### Pflichtumfang

- strukturierte Koeffizienteneingabe,
- Anfangsbedingungen bis zur notwendigen Ordnung,
- fehlende Anfangswerte als Fehler,
- Ableitungssatz termweise,
- Bildgleichung,
- Auflösung nach \(Y(s)\),
- freie und erzwungene Anteile,
- Übertragungsfunktion nur bei expliziten Nullanfangswerten,
- Polynom-, Sinus- und Kosinuseingänge,
- Übergabe an T1,
- Anfangsbedingungsprüfung,
- Vorwärtstransformation,
- DGL-Residuum,
- GUI und LaTeX.

### Nicht enthalten

- freier universeller DGL-Textparser,
- nichtlineare DGL,
- variable Koeffizienten,
- MIMO,
- numerische ODE-Integration.

## PR S2 – Routh

**Branch-Ziel:** wirtschaftliche Ergänzung nach stabilem gemeinsamen Kern.

### Pflichtumfang

- Standardschema Grad 2–4,
- erste Spalte,
- Vorzeichenwechsel,
- Anzahl RHP-Wurzeln,
- Stabilitätsaussage,
- Definitionsbedingungen bei Divisionen,
- Standardparameterfälle,
- Gegenprüfung zu Hurwitz,
- GUI und LaTeX.

### Zunächst ausgeschlossen

- umfangreiche Sonderfallbibliothek,
- beliebige Nullzeilen- und Epsilon-Kaskaden ohne Quellenbedarf,
- Routh als Merge-Blocker für S1.

---

# 7. Alternative Reihenfolge bei geringerem Codex-Budget

## 7.1 Minimalstrategie

Bei deutlich geringerem Budget werden nur die beiden stärksten Pakete umgesetzt:

1. **F1 Frequenzsäule vollständig**
2. **S1 Kern + Hurwitz**
3. Danach Stopp und Stabilisierung.

Zeitbereich und Routh werden dann bewusst auf Wolfram Alpha und Papierunterlagen verlagert.

## 7.2 Was nicht als Sparmaßnahme zulässig ist

Nicht zulässig:

- Frequenz nur bis zu einem einzelnen Durchtritt implementieren,
- Nyquist ohne unabhängige Winding-Kontrolle,
- Hurwitz ohne 2D-Graphband trotz der 7 Gebietspunkte,
- PBZ nur für einfache reelle Pole,
- Zeitbereich mit DGL zuerst und ohne inverse Kette,
- allgemeiner Kern ohne sichtbaren Verbraucher,
- Routh vor Hurwitz.

## 7.3 Budgetarme Rangfolge

```text
F1 vollständig
    ↓
S1 vollständig
    ↓
optional T1
    ↓
T2 nur bei ausreichender Reserve
    ↓
Routh zuletzt
```

Routh wird unter Budgetdruck vollständig gestrichen, nicht vorgezogen.

---

# 8. Budgetkorridore

## 8.1 Definition

Die folgenden Angaben sind **relative Planungsbereiche**, keine Tokenzusagen.

- Ein frisches Reset-Kontingent wird als `100 RE` bezeichnet.
- `RE` bedeutet relative Reset-Einheiten.
- Die Schätzung basiert auf Paketumfang, vorhandener Wiederverwendung, Zahl neuer Verträge und erwartetem Fixrisiko.
- Der tatsächliche Verbrauch kann erst nach Repository-Inspektion und erstem Implementierungsgate besser eingegrenzt werden.

## 8.2 Geschätzte Korridore

| PR | Implementierung | Review/Fix | Gesamtbedarf vor sicherem Start |
|---|---:|---:|---:|
| F1 Frequenzsäule | 35–50 RE | 12–18 RE | **mindestens 55–65 RE verfügbar** |
| S1 Kern + Hurwitz | 45–60 RE | 15–20 RE | **mindestens 65–75 RE verfügbar** |
| T1 PBZ-/Inverse-Kern | 40–55 RE | 15–20 RE | **mindestens 60–70 RE verfügbar** |
| T2 DGL-/Laplace | 25–40 RE | 12–18 RE | **mindestens 45–55 RE verfügbar** |
| S2 Routh | 15–25 RE | 8–12 RE | **mindestens 30–40 RE verfügbar** |

Diese Werte sind bewusst Korridore. Sie dürfen nicht als gemessener Verbrauch oder Garantie behandelt werden.

## 8.3 Aktuelles Restbudget

Der letzte dokumentierte Projektstand nennt ungefähr **16 % Restbudget**. Es liegt keine Live-Telemetrie im Analysechat vor.

### Verbindliche Entscheidung

Mit ungefähr 16 RE darf begonnen werden:

- gezieltes PR-Review,
- ein gebündelter Bugfixlauf,
- kleine Integrationskorrekturen,
- Dokumentations- und Testfallvorbereitung durch normale GPT-Chats,
- keine neue Facharchitektur.

Nicht begonnen werden darf:

- F1,
- S1,
- T1,
- T2,
- S2.

Ein Branchstart unterhalb des Mindestkorridors erzeugt einen halbfertigen Branch, Kontextverlust und später doppelte Integrationsarbeit.

---

# 9. Plan für das nächste Reset-Kontingent

## 9.1 Primärplan

### Phase A – Preflight, 0–5 RE

Nur eine begrenzte Repository-Inspektion:

- aktuelle Frequenzverträge nach dem Standardglieder-Merge,
- vorhandene Presenter-/Plot-/LaTeX-Einstiegspunkte,
- vorhandene Test-Helfer,
- genaue Liste der zu ändernden Module.

Keine breite Architekturinventur.

### Phase B – F1 Implementierung, 35–50 RE

Interne Gates einzeln implementieren und gezielt testen.

### Phase C – Review- und Fixpuffer, 12–18 RE

- mathematische Prüfung,
- GitHub-Diff-Review,
- manueller GUI-Durchlauf,
- genau ein gebündelter Fixauftrag, soweit möglich.

### Phase D – finale Integration, 5–8 RE

- gezielte Bode-Regressionen,
- einmal vollständige Suite,
- Merge-Entscheidung,
- kurze Dokumentationskorrektur.

### Reserve

Mindestens 15 RE bleiben ungebunden, bis F1 tatsächlich gemergt und manuell geprüft ist.

## 9.2 Entscheidung nach F1

Nach sauberem Merge:

- verbleiben **mindestens 65 RE**: S1 darf begonnen werden;
- verbleiben **40–64 RE**: kein S1; nur weitere Fehlerkorrektur oder Reserve;
- verbleiben **unter 40 RE**: keine neue Fachfunktion.

Es ist ausdrücklich besser, ungenutztes Kontingent zu verlieren als einen großen Querschnittsbranch unvollständig zu hinterlassen.

## 9.3 Nachfolgende Reset-Planung

```text
nächstes Reset: F1 Frequenzsäule
darauffolgendes Reset: S1 Kern + Hurwitz
weiteres Reset: T1 PBZ-/Inverse-Kern
danach: T2 DGL-/Laplace
zuletzt und nur bei Reserve: S2 Routh
```

---

# 10. Separater Bugfix- und Integrationspuffer

## 10.1 Pflichtreserve

Für jeden großen PR werden **15–20 % des erwarteten Gesamtbudgets** nicht für Neufunktion verplant.

Der Puffer deckt ab:

- mathematische Vorzeichenfehler,
- Phasenastfehler,
- Roh-/Reduziert-Verwechslungen,
- Provenienzverlust,
- GUI-/Presenter-Fehler,
- LaTeX-Abweichungen,
- unerwartete Regressionen,
- Testkorrekturen bei fehlerhaften offiziellen Lösungen.

## 10.2 Verwendungsregeln

- Kein Pufferverbrauch für Kosmetik.
- Kein allgemeines Refactoring.
- Kein zweiter unabhängiger Featureumfang.
- Fixes werden nach Review gebündelt.
- Nach einer gebündelten Korrekturschleife erfolgt eine neue Merge-Entscheidung.
- Eine zweite große Korrekturschleife ist ein Replanungs- und gegebenenfalls Abbruchsignal.

## 10.3 Paketabhängige Puffer

| PR | Mindestpuffer | Begründung |
|---|---:|---|
| F1 | 15 RE | numerische Kreuzungen, Winding, Phasenäste |
| S1 | 18–20 RE | neue Kernverträge, 2D-Gebiet, Stabilitätsrollen |
| T1 | 18–20 RE | Faktorisierung, Mehrfachpole, komplexe Paare, Rückprüfung |
| T2 | 12–15 RE | Anfangsbedingungen und DGL-Zeichen |
| S2 | 8–12 RE | Tabellen- und Divisionssonderfälle |

---

# 11. Abbruch- und Replanungkriterien

## 11.1 Allgemeine Kriterien

Ein Feature-PR wird gestoppt und neu zugeschnitten, wenn mindestens eines gilt:

1. Der Branch benötigt einen neuen allgemeinen CAS, allgemeinen ODE-Solver oder zweiten Parser.
2. Ein bereits vorhandener zentraler Kern müsste vollständig ersetzt statt erweitert werden.
3. Nach einem internen Gate ist kein sichtbarer oder testbarer Zwischenstand vorhanden.
4. Mehr als zwei zentrale öffentliche Verträge müssen nach Beginn grundlegend neu entworfen werden.
5. Offizielle Hauptreferenzfälle können nur durch Erweiterung in ausdrücklich ausgeschlossene Spezialfälle gelöst werden.
6. Die Implementierung liefert numerische Näherungen, obwohl das Paket exakte Ergebnisse verlangt.
7. Roh- und reduzierte Formen, Annahmen oder Provenienz gehen verloren.
8. Nach einer gebündelten Fixrunde bestehen weiterhin fachliche Kernfehler.
9. Der verbleibende Codex-Puffer sinkt unter den für Review und Integration reservierten Mindestwert.
10. Der Branch beginnt zusätzlich Komfort-, Packaging- oder allgemeine GUI-Arbeiten.
11. Nicht unterstützte Fälle erzeugen Zahlen statt eines sicheren Status.
12. Die vollständige Suite zeigt ungeklärte Regressionen außerhalb des betroffenen Bereichs.

## 11.2 Frequenzspezifische Kriterien

F1 wird gestoppt oder begrenzt, wenn:

- die offizielle Hauptabdeckung eine allgemeine Nyquist-Ausweichkontur um imaginäre Achsenpole erzwingt;
- primäre und unabhängige Winding-Methode für Referenzfälle nicht konsistent werden;
- Mehrfachdurchtritte nur durch globale Black-Box-Optimierung beherrschbar wären;
- Phasenreserven wieder auf Hauptphasen statt entfalteter Phase beruhen;
- der enge Skalarparameter zu einem allgemeinen Parametersolver anwächst.

Für Pole auf der imaginären Achse gilt im MVP: sicherer Abbruch statt erfundener Umschlingungszahl.

## 11.3 Kern-/Hurwitz-spezifische Kriterien

S1 wird gestoppt oder reduziert, wenn:

- der 2D-Solver über Graphbänder mit linearen/quadratischen Grenzen hinauswächst;
- allgemeine Quantorenelimination oder Kurvenanordnung erforderlich wird;
- Hurwitz Polynomkanonisierung dupliziert;
- der gemeinsame Kern Stabilitätsbegriffe enthält;
- internes Rohpolynom und reduzierter E/A-Nenner nicht sicher getrennt werden können;
- Gradabfälle durch Division verloren gehen.

Nicht unterstützte 2D-Fälle müssen `PARTIALLY_SOLVED_SAFE` oder `UNSUPPORTED` liefern.

## 11.4 Zeitbereichsspezifische Kriterien

T1/T2 werden gestoppt oder begrenzt, wenn:

- ein zweites Parser-Frontend mit eigener Sicherheitslogik entsteht;
- \(s\)- und \(t\)-Ausdrücke nicht hart getrennt sind;
- offizielle Mehrfachpol- oder PT2-Fälle nur numerisch statt exakt behandelt werden;
- gewöhnliche Zeitfunktionen stillschweigend Distributionsterme verlieren;
- T2 einen freien universellen DGL-Parser benötigt;
- Anfangswerte stillschweigend null gesetzt werden;
- die PBZ nicht exakt rückzusammengefasst wird.

---

# 12. GPT-Vorarbeiten vor jedem Codex-Branch

Diese Arbeiten sollen normale GPT-Chats übernehmen. Codex soll keine lange Fachanalyse oder Dokumentinventur wiederholen.

## 12.1 Gemeinsame Pflichtvorarbeiten

Vor jedem Branch müssen vorliegen:

1. verbindlicher MVP-Umfang,
2. explizite Nichtziele,
3. genaue vorhandene Wiederverwendung,
4. Liste betroffener öffentlicher Verträge,
5. Eingabe- und Ergebnisobjekte,
6. Diagnose- und Unsupported-Zustände,
7. offizielle Golden-Fälle,
8. bekannte Quellenfehler und korrigierte Erwartungswerte,
9. Testmatrix,
10. minimale GUI-Stelle,
11. Worked-Step-Reihenfolge,
12. LaTeX-Pflichtinhalt,
13. Merge-Kriterien,
14. Abbruchkriterien,
15. zulässige maximale Fixrunde.

## 12.2 Noch fehlende Vorarbeiten für F1

- endgültige Richtungskonvention für \(N_{\mathrm{cw}}\) in einer kompakten Tabelle festhalten;
- vollständige Liste der Phasenäste und Deduplizierungsregeln;
- Suchband-Vollständigkeitsstatus definieren;
- Grenzfalltabelle für fehlende, multiple und tangentiale Durchtritte;
- exakte Definition des engen Skalarparameter-Ergebnisses;
- GUI-Feld- und Tabellenlayout ohne neues allgemeines Workspace-Konzept;
- Golden-Ledger für F1–F9 mit Quellenkorrekturen;
- manuelle Kontrollwerte für die zwei Klausurfälle und die allgemeinen Übungsfälle.

## 12.3 Noch fehlende Vorarbeiten für S1

- Kernverträge nach den Hurwitz-Korrekturen K1–K11 konsolidieren;
- 0D-/1D-/2D-Ergebnisstatus final festlegen;
- Rollen-/Analyseziel-Matrix verbindlich einfrieren;
- exakte Graphband-Normalform definieren;
- Regeln für `full_generated_conditions` und `minimal_solver_conditions`;
- Grenze der Fallzerlegung festlegen;
- zwei Klausurgebiete als vollständige Golden-Objekte dokumentieren;
- Entscheidung, wie Gebietsplot und exakte Region getrennt werden;
- vorhandene Repository-Polynomtypen auf Doppeltyp-Risiko prüfen.

## 12.4 Noch fehlende Vorarbeiten für T1

- Parser-Modusprofile \(s\), \(t\), Koeffizient final beschreiben;
- Faktorobjekte und Multiplizitäten festlegen;
- PBZ-Ansatzobjekte für lineare Mehrfachfaktoren und Quadrate;
- gewöhnliche versus distributionsartige inverse Ergebnisse trennen;
- direkte/inverse Regel-IDs und Quellenreferenzen;
- DGL-Verträge bereits vor T1 einfrieren, ohne DGL sichtbar zu implementieren;
- Golden-Ledger RF-06 bis RF-13;
- GUI-Einstiege \(F(s)\), \(G(s)\), \(G(s),U(s)\) festlegen.

## 12.5 Noch fehlende Vorarbeiten für T2

- strukturierte DGL-Koeffizientenform finalisieren;
- Anfangsbedingungsindexierung und Fehlermeldungen;
- Regeln für Eingangsableitungen;
- freie und erzwungene Antwort fachlich und technisch trennen;
- Übertragungsfunktionsbildung nur bei expliziten Nullanfangswerten;
- DGL-Residuum und Anfangswertprüfung definieren;
- Golden-Ledger RF-03, RF-04, RF-05 und RF-14;
- GUI ohne freien DGL-Textparser planen.

## 12.6 Noch fehlende Vorarbeiten für S2

- Routh-Tabellenschema Grad 2–4 eindeutig transkribieren;
- Divisions- und Nennerausschlüsse definieren;
- Standardfälle und bewusst ausgeschlossene Sonderfälle;
- Vorzeichenwechselkonvention;
- Hurwitz-/Routh-Cross-Testmatrix;
- GUI-Erweiterung im bestehenden Stabilitätsarbeitsbereich.

---

# 13. Codex-Aufgabenklassen

Keine dieser Klassen ist ein Codex-Prompt. Sie dienen der Aufwands- und Verantwortungsplanung.

## Klasse A – begrenzte Repository-Einpassung

- relevante Dateien und öffentliche Verträge identifizieren,
- vorhandene Helfer und Testfixtures zuordnen,
- Doppelimplementierung ausschließen.

**Umfang:** klein und einmalig pro PR.

## Klasse B – Domänen- und Ergebnisverträge

- unveränderliche Fachobjekte,
- Invarianten,
- Statusmodelle,
- Provenienz,
- exakte/numerische Trennung.

**Risiko:** hoch bei S1, mittel bei F1 und T1.

## Klasse C – mathematischer Kern

- Durchtrittssuche und Winding,
- Polynom-/Bedingungskern und Hurwitz,
- PBZ und inverse Termabbildung,
- DGL-Transformation,
- Routh-Tabelle.

**Risiko:** fachlich hoch.

## Klasse D – Orchestrierung

- vorhandene Ergebnisse konsumieren,
- Stufen in korrekter Reihenfolge ausführen,
- Teilresultate erhalten,
- Unsupported-Zustände durchreichen.

## Klasse E – sichtbare Integration

- Presenter,
- GUI,
- Diagramme,
- Worked Steps,
- LaTeX.

Keine Neugestaltung der Gesamtoberfläche.

## Klasse F – gezielte Tests

- Domain-Tests,
- offizielle Golden-Fälle,
- ein bis zwei Workflow-Tests,
- Presenter-/LaTeX-Smokes,
- gezielte alte Regressionen.

## Klasse G – gebündelter Fixlauf

- ausschließlich reviewte Fehler,
- keine neuen Features,
- keine allgemeine Bereinigung,
- danach erneute Merge-Entscheidung.

---

# 14. Teststrategie

## 14.1 Testpyramide

### Ebene 1 – Invarianten und Unit-Tests

Prüfen:

- exakte Rekonstruktion,
- Vorzeichen und Striktheit,
- Mehrfachheiten,
- Residuen,
- Domain-Grenzen,
- Unsupported-Zustände.

Diese Tests laufen pro internem Gate.

### Ebene 2 – offizielle Referenzfälle

Jeder PR benötigt mindestens:

- einen einfachen offiziellen Fall,
- einen schwierigen offiziellen Fall,
- einen Parameter- oder Grenzfall,
- einen gezielten Quellenfehlerfall,
- einen Unsupported-Fall.

### Ebene 3 – Workflow-Integration

Je PR nur wenige End-to-End-Fälle:

- Eingabe,
- Fachberechnung,
- Resultat,
- Presenter,
- GUI-Smoke,
- LaTeX.

### Ebene 4 – Querschnittsregression

Nur gezielt:

- F1 gegen bestehende Bode-Ergebnisse,
- S1 gegen vorhandene Polberechnung,
- T1/T2 gegen Rationalreduktion und Pole,
- S2 gegen Hurwitz.

### Ebene 5 – vollständige Suite

Genau einmal vor Merge eines großen PRs oder nach tiefen zentralen Vertragsänderungen.

## 14.2 Keine blinde Golden-Übernahme

Bekannte Quellenfehler dürfen nicht als Softwareerwartung festgeschrieben werden:

- falsche \(270^\circ\)-Phasenreserve,
- unstrenge Hurwitz-Ränder,
- widersprüchliche Punktangaben,
- unklare Verstärkungsdomains,
- fehlerhafte Formeln oder Mitschriftzwischenwerte.

Jeder korrigierte Golden-Fall benötigt:

- Quelle,
- Gegenquelle oder direkte Rechnung,
- kurze Korrekturbegründung.

## 14.3 Semantische statt fragile Darstellungstests

Bevorzugt prüfen:

- richtige Gleichung,
- richtige Vorzeichen,
- richtige Reihenfolge der Fachschritte,
- richtige Statuswerte,
- richtige offene/geschlossene Grenzen.

Nicht priorisieren:

- pixelgenaue GUI-Snapshots,
- vollständige LaTeX-Stringgleichheit bei rein kosmetischen Abständen,
- redundante Tests derselben SymPy-Grundoperation.

---

# 15. Integrationsstrategie

## 15.1 Nur ein großer aktiver Feature-Branch

Keine parallele Entwicklung an:

- Frequenzverträgen,
- allgemeinem Parameterkern,
- Rationalfunktionskern,
- LaTeX-Grundstruktur.

Parallele Branches würden Konflikte und doppelte Reviewarbeit erzeugen.

## 15.2 Reihenfolge pro PR

1. GPT-Vertragsfreeze.
2. begrenzte Codex-Repository-Einpassung.
3. Domain-Gates.
4. Fachalgorithmus.
5. Workflow.
6. GUI/Presenter/LaTeX.
7. gezielte Tests.
8. GitHub-Review.
9. gebündelter Fixlauf.
10. vollständige Suite.
11. Merge oder Abbruch.

## 15.3 Nach jedem Merge

- manueller Referenzfall in der App,
- kurze Regression des vorherigen Arbeitsbereichs,
- Entscheidung, ob Verträge stabil genug für den nächsten Verbraucher sind,
- keine sofortige allgemeine Refaktorierung.

## 15.4 Gemeinsame Kerne nur bei realem Verbraucher extrahieren

- Polynom-/Parameterkern wird sofort durch Hurwitz verbraucht.
- PBZ-Kern wird sofort durch sichtbare Zeitantworten verbraucht.
- Nyquist-Skalarintervalle bleiben zunächst fachmodulspezifisch.
- Spätere Extraktion oder Adapter nur bei nachgewiesener Doppelarbeit.

---

# 16. Hauptrisiken

## 16.1 Frequenzsäule

- falscher Phasenast,
- tangentiale Scheindurchtritte,
- unvollständige Frequenzbänder,
- falsche Winding-Orientierung,
- offene Kurve,
- kritischer Treffer nahe \(-1\),
- imaginäre Achsenpole,
- fälschlich verallgemeinerter Parametersolver.

## 16.2 Polynom-/Parameterkern + Hurwitz

- schleichender allgemeiner CAS,
- Hurwitz-Begriffe im neutralen Kern,
- Gradabfallverlust,
- Roh-/Reduziert-Verwechslung,
- falsche Stabilitätsrolle,
- unvollständige 2D-Zellen,
- stillschweigend gerundete Grenzen,
- unnötige monische Normierung,
- zu frühe Routh-Erweiterung.

## 16.3 Zeitbereich

- Parserduplikation,
- Vermischung von \(s\) und \(t\),
- Verlust von Rohform und Kürzungswarnung,
- numerische statt exakte Mehrfachpole,
- falsche PBZ-Templates,
- verlorener Polynomanteil,
- Distributionen als gewöhnliche Funktion ausgegeben,
- Endwertsatz ohne Polprüfung,
- fehlende Anfangswerte als null,
- DGL-Residuum nicht geprüft.

## 16.4 Prozessrisiken

- aktuelle Budgetquote ungeprüft,
- zu großer Scope im ersten Codex-Auftrag,
- zu viele kleine PRs,
- Volltests nach jedem Commit,
- kosmetische Fixschleifen,
- unvollständige Branches über Resetgrenzen,
- parallele Änderungen zentraler Verträge.

---

# 17. Funktionen, die bewusst Wolfram Alpha überlassen werden

Wolfram Alpha bleibt sinnvoll für:

- schnelle unabhängige Faktorisierung,
- einfache Nullstellen und Eigenwerte,
- Kontrolle einzelner Determinanten,
- Standardableitungen und Integrale,
- einfache algebraische Umformungen,
- unabhängige Prüfung eines PBZ-Ergebnisses,
- hochgradige oder ungewöhnliche symbolische Ausdrücke außerhalb des MVP,
- einmalige Kontrollrechnung bei `PARTIALLY_SOLVED_SAFE`,
- numerische Kontrolle ungewöhnlicher Parameterwerte.

Wolfram Alpha soll nicht den klausurtauglichen Rechenweg des Programms ersetzen, wenn der Aufgabentyp zum implementierten MVP gehört.

---

# 18. Funktionen, die bewusst Papierunterlagen überlassen werden

Papier bleibt zuständig für:

- Theorie- und Multiple-Choice-Fragen,
- Formeltabellen,
- Laplace-Tabelle als Backup,
- Standardgliedertabelle als Backup,
- handgeforderte qualitative Skizzen,
- Blockschaltbildzeichnen,
- visuelle Aufgabeninterpretation,
- seltene Routh-Sonderfälle,
- Nyquist-Ausweichkonturen außerhalb des sicheren MVP,
- distributionsartige inverse Laplace,
- stückweise oder zeitverschobene Signale außerhalb des MVP,
- Reglerentwurfsformeln, solange kein eigener Reglerblock implementiert ist,
- Wurzelortskurven-Spezialkonstruktionen,
- Prüfungsvorgehen bei Softwareausfall.

Nicht programmiert werden sollen vor der Klausur:

- visueller Blockschaltbildeditor,
- universeller CAS,
- allgemeiner ODE-Solver,
- allgemeine Quantorenelimination,
- beliebige 2D-/3D-Parametergebiete,
- beliebige Nyquist-Konturen,
- allgemeine Distributionstheorie,
- allgemeiner Aufgaben- oder Bildparser,
- Komfort- und Cloudfunktionen.

---

# 19. Klare nächste Entscheidung für den Masterchat

## 19.1 Sofortentscheidung

1. Den aktuellen Codex-Budgetstand in der Oberfläche verifizieren.
2. Liegt er ungefähr beim zuletzt dokumentierten Wert von 16 %, wird **kein Feature-Branch gestartet**.
3. Das Restbudget bleibt Bugfix-, Review- und Integrationspuffer.
4. Normale GPT-Chats schließen vor dem Reset die F1-Vorarbeiten ab.
5. Nach dem Reset wird genau ein neuer Branch freigegeben:

\[
\boxed{\text{F1: vollständige Frequenzsäule – Durchtritte, Reserven und Nyquist}}
\]

## 19.2 Nach F1

Erst nach:

- fachlichem Review,
- manuellem GUI-Test,
- gebündeltem Fixlauf,
- vollständiger Suite,
- sauberem Merge

wird S1 freigegeben.

## 19.3 Nicht nächste Entscheidung

Nicht freigeben:

- isolierter Parameterkern,
- Routh,
- Zeitbereichsmonolith,
- PBZ-Minimalversion nur mit einfachen Polen,
- allgemeines Refactoring,
- visueller Blockeditor.

---

# 20. Kurzfassung der Priorisierung

| Priorität | Feature-PR | Entscheidung |
|---:|---|---|
| 1 | F1 Frequenzsäule | nächster Branch nach Reset |
| 2 | S1 Kern + Hurwitz | nächster großer Querschnittsbranch |
| 3 | T1 PBZ/Inverse/Zeitantwort | danach, vollständig und exakt |
| 4 | T2 DGL/Laplace | konsumiert T1 |
| 5 | S2 Routh | nur bei verbleibender Reserve |
| nicht bauen | isolierter Kern, allgemeiner CAS, visueller Blockeditor | vor der Klausur verwerfen |

**Endurteil:**  
Der stärkste nächste Schritt ist nicht der theoretisch allgemeinste Kern, sondern die vollständige Frequenzsäule auf dem bereits vorhandenen Bode-Unterbau. Der erste neue allgemeine Kern wird erst danach gemeinsam mit Hurwitz implementiert. Zeitbereich folgt in zwei technisch natürlichen PRs. Routh bleibt bewusst nachrangig.
