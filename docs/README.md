# KlausurBotPro – Dokumentationsübersicht

Diese Datei beschreibt die Rollen der Dokumente unter `docs/` und legt fest,
welche Datei bei Widersprüchen maßgeblich ist. Sie enthält keine fachliche
Regelungstechnik-Spezifikation und keinen Implementierungsauftrag.

## 1. Grundsatz

Die Dokumentation ist nach Verantwortung getrennt:

- Der aktuelle Code bestimmt, was technisch tatsächlich implementiert ist.
- `ARCHITECTURE.md`, `DECISIONS.md` und `TEST_STRATEGY.md` dokumentieren den
  nachgewiesenen Ist-Zustand und seine technischen Invarianten.
- `KlausurBotPro_Architekturplan.md` beschreibt den verbindlichen Zielrahmen
  und die fachübergreifende Umsetzungsstrategie.
- `ROADMAP.md` beschreibt den aktuellen Arbeitsstand, die Reihenfolge der
  nächsten Feature-PRs und die Ressourcenplanung.
- `reference/` enthält fachlich verbindliche Spezifikationen.
- `implementation/` enthält implementierungsfertige, aber codefreie
  Fach- und Schnittstellenpakete für zukünftige Feature-PRs.

Eine Datei darf nicht gleichzeitig Ist-Dokumentation, Fachreferenz,
Implementierungspaket und kurzfristige Aufgabenliste sein.

## 2. Empfohlene Verzeichnisstruktur

```text
docs/
├── README.md
├── ARCHITECTURE.md
├── COMPATIBILITY.md
├── DECISIONS.md
├── KlausurBotPro_Architekturplan.md
├── PROJECT_CONCEPT.md
├── ROADMAP.md
├── SOURCE_POLICY.md
├── TEST_STRATEGY.md
│
├── reference/
│   ├── KlausurBotPro_Fachspezifikation_Standardglieder_Bode.md
│   ├── KlausurBotPro_Fachspezifikation_Nyquist_Reserven.md
│   ├── KlausurBotPro_Fachspezifikation_Charakteristische_Polynome_Parameterbedingungen.md
│   ├── KlausurBotPro_Fachspezifikation_Hurwitz_Routh.md
│   └── RT1_Fachspezifikation_Laplace_PBZ_Zeitantworten.md
│
└── implementation/
    ├── KlausurBotPro_Implementierungspaket_Frequenzsaeule_Nyquist_Reserven.md
    ├── KlausurBotPro_Implementierungspaket_Polynom_Parameterkern.md
    ├── KlausurBotPro_Implementierungspaket_Hurwitz_Routh.md
    ├── KlausurBotPro_Implementierungspaket_Zeitbereich_Laplace_PBZ_Zeitantworten.md
    └── KlausurBotPro_Implementierungspriorisierung_nach_Expertenpaketen.md
```

## 3. Rollen der Dokumente im Hauptverzeichnis

### `PROJECT_CONCEPT.md`

Dauerhaftes Produktkonzept:

- Zweck und Zielgruppe,
- Einzelwerkzeuge und geführte Aufgabenworkflows,
- Workspace- und Quellenidee,
- optionale externe Integrationen,
- Nichtziele und Qualitätsziele.

Die Datei beschreibt das Produkt, nicht den aktuellen Implementierungsstand.

### `ARCHITECTURE.md`

Technische Ist-Dokumentation der implementierten Architektur:

- vorhandene Schichten und Abhängigkeitsrichtungen,
- tatsächlich implementierte Domain- und Application-Verträge,
- sichere Eingabe- und Symbolikpfade,
- nachgewiesene Invarianten und technische Grenzen.

Neue Abschnitte werden erst ergänzt, nachdem die betreffende Architektur
implementiert und geprüft wurde.

### `DECISIONS.md`

Entscheidungsregister für bestätigte technische Festlegungen:

- Produktionsabhängigkeiten und geprüfte Versionen,
- Domain- und Identitätssemantik,
- Ressourcenlimits,
- Schnittstellen- und Sicherheitsentscheidungen,
- bewusst ausgeschlossene Varianten.

Vorläufige Aussagen bleiben als vorläufig gekennzeichnet. Neue
Produktionsabhängigkeiten werden vor ihrer Aufnahme begründet.

### `COMPATIBILITY.md`

Reproduzierbarer Kompatibilitätsnachweis:

- getestetes Betriebssystem und Python-Version,
- geprüfte Bibliotheksversionen,
- bekannte Windows-, Qt-, Matplotlib- und Slycot-Grenzen,
- noch offene Packaging- und Supportfragen.

Ein erfolgreicher Grundtest ist kein pauschaler Nachweis für jede spätere
Fachfunktion.

### `TEST_STRATEGY.md`

Verbindliche Teststrategie für den aktuellen Code:

- Unit-, Integrations-, Presenter-, GUI- und Berichtstests,
- exakte symbolische Vergleiche,
- numerische Toleranzen,
- Sicherheits- und Ressourcenfälle,
- offizielle Aufgaben und analytische Grenzfälle als Regressionstests.

Die Datei wird mit jedem implementierten Fachblock erweitert.

### `SOURCE_POLICY.md`

Quellen- und Provenienzregeln:

- Quellenhierarchie,
- Umgang mit fehlerhaften oder widersprüchlichen Musterlösungen,
- verifizierte Dokument- und Seitenreferenzen,
- Trennung von Quellenaussage, Herleitung und allgemeinem Fachwissen,
- lokale, unveränderte Original-PDFs.

Originale Lehrunterlagen werden standardmäßig nicht in Git eingecheckt.

### `KlausurBotPro_Architekturplan.md`

Verbindlicher fachübergreifender Ziel- und Implementierungsrahmen:

- Projektziel und Ressourcenprinzip,
- Wiederverwendung vorhandener Infrastruktur,
- Modulgrenzen und gemeinsame Verträge,
- vertikale Fachworkflows,
- langfristige Zielarchitektur.

Die Datei ersetzt frühere Fassungen des Architekturplans. Kurzfristige
Prozentstände, aktuelle Branch-Namen und einzelne Codex-Läufe gehören nicht
hierher, sondern in `ROADMAP.md`.

### `ROADMAP.md`

Aktuelle operative Planung:

- nachgewiesener Stand in `main`,
- offene Integrations- und Dokumentationsarbeiten,
- Reihenfolge der nächsten Feature-PRs,
- Abnahmekriterien je Paket,
- Codex- und Reviewstrategie,
- aktueller Ressourcenrahmen.

Die Roadmap darf häufiger geändert werden als die Fachspezifikationen.

## 4. Fachspezifikationen unter `reference/`

Fachspezifikationen beantworten:

- Welche RT1-Aufgabentypen werden unterstützt?
- Welche Formeln, Konventionen und Voraussetzungen gelten?
- Welche Quellen und Referenzfälle sind maßgeblich?
- Welche Grenzfälle sind unterstützt, teilweise unterstützt oder abgelehnt?
- Welche fachlichen Fehler in offiziellen Unterlagen dürfen nicht als
  Golden-Ergebnis übernommen werden?

Sie enthalten keinen Softwarecode und grundsätzlich keinen fertigen
Codex-Prompt.

Bei fachlichen Aussagen gilt innerhalb des Projekts folgende Rangfolge:

1. aktuelle offizielle Klausur- und Hilfsmittelregeln,
2. offizielles Skript,
3. offizielle Übungen und Musterlösungen,
4. offizielle Tutoriums- und Praxisunterlagen,
5. aktuelle und frühere Klausuren,
6. ergänzende Tabellen und Übersichten,
7. eigene Mitschriften und ausgefüllte Unterlagen nur ergänzend,
8. gekennzeichnetes allgemeines Fachwissen.

## 5. Implementierungspakete unter `implementation/`

Implementierungspakete übersetzen die Fachspezifikationen in einen
implementierungsfertigen, codefreien Zuschnitt:

- wirtschaftlicher MVP-Umfang,
- öffentliche Fachoperationen und Ergebnisverträge,
- Besitz und Grenzen der Module,
- Wiederverwendung vorhandener Komponenten,
- konkrete Referenz- und Regressionstests,
- GUI-, Worked-Steps- und LaTeX-Anbindung,
- harte Nichtziele.

Sie bleiben getrennt, damit ein Codex-Chat nur die für seinen Feature-PR
notwendigen Unterlagen erhält.

Die Gesamtpriorisierung bewertet die Pakete gegeneinander. Sie ersetzt die
einzelnen Pakete nicht.

## 6. Konfliktregel

Bei einem Widerspruch gilt:

1. aktueller Code und bestandene Tests für den technischen Ist-Zustand,
2. `DECISIONS.md` für bestätigte technische Entscheidungen,
3. jeweilige Fachspezifikation unter `reference/` für fachliche Regeln,
4. jeweiliges Implementierungspaket unter `implementation/` für den
   zugeschnittenen zukünftigen PR,
5. `KlausurBotPro_Architekturplan.md` für den fachübergreifenden Zielrahmen,
6. `ROADMAP.md` für Reihenfolge und aktuellen Arbeitsstatus.

Ein niedriger priorisiertes Dokument darf ein höher priorisiertes Dokument
nicht stillschweigend überschreiben. Der Widerspruch wird ausdrücklich
dokumentiert und anschließend an der richtigen Stelle bereinigt.

## 7. Änderungsregeln

### Nach einem Feature-Merge

Mindestens prüfen und gegebenenfalls aktualisieren:

- `ARCHITECTURE.md`,
- `DECISIONS.md`,
- `TEST_STRATEGY.md`,
- `ROADMAP.md`.

### Nach einer fachlichen Korrektur

Mindestens prüfen und gegebenenfalls aktualisieren:

- betroffene Datei unter `reference/`,
- davon abhängige Datei unter `implementation/`,
- betroffene Regressionstests,
- dokumentierte Quellenkorrekturen.

### Nach neuen Intensivkurs- oder Klausurhinweisen

Die neuen Unterlagen werden zunächst als Delta gegen die bestehenden
Fachspezifikationen geprüft. Eine einzelne Intensivkurs-Sitzung ersetzt nicht
automatisch Skript, Übungen oder bereits bestätigte Referenzfälle. Relevante
neue Aussagen werden mit genauer Folie beziehungsweise Fundstelle dokumentiert.

## 8. Git- und PR-Regeln für Dokumentation

- Dokumentationsverschiebungen und inhaltliche Fachänderungen möglichst trennen.
- Dateien über Git verschieben, damit die Historie erkennbar bleibt.
- Keine Archivkopien bereits ersetzter Dateien anlegen; Git enthält die Historie.
- Keine Original-PDFs oder persönlichen Unterlagen in das öffentliche
  Repository übernehmen.
- Interne Links nach Verschiebungen prüfen.
- Ein Dokumentations-PR darf keinen fachlichen Produktionscode ändern.
