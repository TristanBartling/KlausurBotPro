# Roadmap

Die Phasen sind eine Planungsgrundlage, keine Zusage endgültiger Architektur.
Eine Phase gilt nur anhand ihrer Abnahmekriterien als abgeschlossen.

## Phase 0 – Projektfundament

**Ziel:** Importierbares Python-Projekt, Arbeitsregeln, Dokumentation und
automatisierbare Qualitätsprüfungen.

**Abnahmekriterien:** `src`-Layout, Metadaten, Smoke-Test, pytest, Ruff und mypy
laufen erfolgreich; Startbefehl zeigt eindeutig den Fundamentstatus.

**Nicht enthalten:** Fachberechnungen, produktive GUI, Workspace, PDFs, APIs.

## Phase 1 – Mathematische Datenmodelle und sicherer Parser

**Ziel:** Minimale typisierte Modelle und eine begrenzte, dokumentierte
Eingabesyntax ohne `eval`.

**Abnahmekriterien:** Parser lehnt unerlaubte Syntax ab; Modelle erhalten exakte
Werte; bekannte Grenzfälle und Fehlereingaben sind getestet.

**Nicht enthalten:** vollständige CAS-Syntax, GUI-Workflow, Online-Solver.

## Phase 2 – Erster vertikaler Workflow

**Ziel:** Übertragungsfunktion → Pole/Nullstellen → Stabilität als erster
durchgängiger Fachkern- und Application-Service-Schnitt.

**Abnahmekriterien:** strukturierte Übergaben, manuell ersetzbare
Zwischenergebnisse, symbolisch-numerische Prüfung und Referenztests.

**Nicht enthalten:** Frequenzdiagramme, allgemeine Workflow-Engine,
Blockschaltbilder.

## Phase 3 – Frequenzanalyse

**Ziel:** Bode- und Nyquist-Grundlagen sowie zugehörige Kennwerte und
Darstellungen.

**Abnahmekriterien:** analytische Beispiele, numerische Referenzvergleiche,
korrekte Einheiten und nachvollziehbare Plotdaten.

**Implementierter Zwischenstand:** Die gemeinsame Phase-3E.1a-Preparation
validiert und verarbeitet Transferfunktionseingaben bis zur exakten
Reduktion. Der bestehende Vollworkflow und der UI-unabhängige
Phase-3E.1b-Frequenzworkflow verwenden dieselbe Pipeline. Der Frequenzworkflow
orchestriert wahlweise einen Einzelpunkt oder zertifizierte Bode-Rasterdaten
mit optionaler Phasenentfaltung, ohne Wurzel- oder Stabilitätsanalyse.
Frequenzbericht, Exporte, Diagramm und GUI sind noch nicht Bestandteil dieses
Zwischenstands.

**Nicht enthalten:** vollständige Reglerauslegung, Wurzelortskurven-Editor,
interaktiver Blockeditor.

## Phase 4 – Stabilitätsverfahren

**Ziel:** Hurwitz- und Routh-Kriterium sowie Parameterbereiche.

**Abnahmekriterien:** Voraussetzungen und Sonderfälle sichtbar; analytische
Grenzfälle und offizielle Aufgaben als Regressionstests.

**Nicht enthalten:** nichtlineare Stabilität, robuste Regelung,
unbelegte automatische Schlussfolgerungen.

## Phase 5 – Laplace und Zeitbereich

**Ziel:** Laplace, inverse Laplace, Partialbrüche und ausgewählte
Zeitbereichsantworten.

**Abnahmekriterien:** Definitionsbereiche und Voraussetzungen dokumentiert;
Rücktransformation und numerische Stichproben prüfen Ergebnisse.

**Nicht enthalten:** beliebige Distributionstheorie, OCR von Aufgaben,
vollständige Symbolikoberfläche.

## Phase 6 – Zustandsraum und Linearisierung

**Ziel:** Zustandsraumdarstellungen, Eigenanalyse, Matrixexponential,
Transitionsmatrix und lokale Linearisierung.

**Abnahmekriterien:** Dimensionen und Voraussetzungen validiert;
Konsistenzchecks mit Übertragungsfunktion, Polen und Eigenwerten.

**Nicht enthalten:** großskalige Simulation, nichtlineare globale Analyse,
automatische Modellidentifikation.

## Phase 7 – Geführte End-to-End-Aufgabenworkflows

**Ziel:** Mehrstufige Klausuraufgaben, Verzweigungen, Verlauf und Wechsel zu
Einzelwerkzeugen.

**Abnahmekriterien:** strukturierte Übergaben, Overrides mit Provenienz,
Wiederaufnahme und End-to-End-Tests mehrerer offizieller Aufgabentypen.

**Nicht enthalten:** Quellen-Volltextsuche, Kollaboration, Cloud-Synchronisation.

## Phase 8 – Quellen- und Nachschlagewerk

**Ziel:** Manifestbasierte lokale Quellen, belegte Seitenlinks, Suche nach
Formeln, Fehlern und Beispielen.

**Abnahmekriterien:** unveränderte PDFs, verifizierte Prüfsummen, relative
Pfade, keine erfundenen Seitenzahlen, klare Herkunft jeder Aussage.

**Nicht enthalten:** OCR/Fotoimport, Veränderung der Original-PDFs,
ungeprüfte automatische Quellenbehauptungen.

## Phase 9 – Blockschaltbildeditor

**Ziel:** Visuelle Eingabe und nachvollziehbare Reduktion einfacher
Blockschaltbilder.

**Abnahmekriterien:** Modell und Ansicht getrennt; Reduktionsschritte
reproduzierbar; typische offizielle Beispiele getestet.

**Nicht enthalten:** universeller CAD-Editor, Hardwaredesign,
unbegrenzte Diagrammnotation.

## Phase 10 – Packaging und Klausur-Build

**Ziel:** Reproduzierbare Desktop-Pakete und ein technisch eingeschränkter,
offlinefähiger Klausur-Build.

**Abnahmekriterien:** dokumentierter Build; unterstützte Plattform geprüft;
Klausur-Artefakt enthält keine KI-Endpunkte, KI-Schlüssel oder versteckten
KI-Funktionen; Installations- und Starttests erfolgreich.

**Nicht enthalten:** Umgehung aktueller Prüfungsregeln, stiller Netzwerkzugriff,
eingebettete persönliche Quellen oder Schlüssel.
