# Architekturhypothese

Dieses Dokument beschreibt eine erste, bewusst vorläufige Hypothese. Die
Schichten werden erst angelegt, wenn ein vertikaler Anwendungsfall sie benötigt.
Die Verzeichnisstruktur soll keine noch nicht belegten Abstraktionen vortäuschen.

## Geplante Schichten

1. **Domain-Modelle:** unveränderliche oder kontrolliert veränderbare,
   fachliche Datentypen für Polynome, Matrizen, Systeme und Ergebnisse.
2. **Mathematische Fachlogik:** symbolische und numerische Operationen ohne
   Kenntnis von GUI, Dateien oder Netzwerk.
3. **Application Services und Workflows:** Orchestrierung von Fachoperationen,
   Validierung von Arbeitsschritten und Übergabe strukturierter Ergebnisse.
4. **Workspace und Historie:** benannte Objekte, Provenienz, Versionen,
   Überschreibungen, Verlauf und Verzweigungen.
5. **Quellen- und PDF-Verwaltung:** Manifest, Referenzen, Suche und Öffnen
   belegter PDF-Seiten.
6. **Externe Integrationen:** Adapter für optionale Solver und andere Dienste.
7. **Reporting:** fachlich kompakte Rechenwege und unterschiedliche
   Darstellungsformen auf Basis strukturierter Ergebnisse.
8. **Benutzeroberfläche:** PySide6-Desktopoberfläche, Eingabe und Darstellung.

## Abhängigkeitsrichtung

Abhängigkeiten zeigen nach innen: UI und Integrationsadapter dürfen Application
Services verwenden; diese verwenden Domain und Fachlogik. Der Fachkern kennt
weder PySide6 noch Netzwerkclients, PDFs oder konkrete Persistenz. Reporting
liest strukturierte Ergebnisse, verändert aber nicht deren mathematische
Bedeutung.

## Fachkern und UI

UI-Callbacks nehmen Eingaben entgegen und rufen Application Services auf. Sie
enthalten keine Formeln oder Rechenalgorithmen. Dadurch können Einzelwerkzeuge,
Workflows, Tests und eine spätere Stapelverarbeitung denselben Fachkern nutzen.

## Adapterprinzip

Externe Dienste werden über kleine, fachlich benannte Schnittstellen
abstrahiert. Konkrete Adapter kapseln Authentifizierung, Transport,
Zeitüberschreitungen und Antwortformate. Ein fehlender Adapter oder
Netzwerkfehler darf lokale Berechnungen nicht blockieren. Zugangsdaten kommen
aus lokaler Laufzeitkonfiguration.

## Strukturierte Ergebnisobjekte

Ergebnisse sollen Werte, Voraussetzungen, Zwischenschritte, verwendete
Methoden, Rundungsinformationen, Warnungen, Quellenreferenzen und
Prüfergebnisse getrennt speichern. Text und Formeln werden daraus gerendert,
nicht als alleinige Wahrheit gespeichert. Das konkrete Modell wird in Phase 1
an einem realen vertikalen Anwendungsfall entworfen.

## Offene Architekturentscheidungen

- genaue Grenzen und Repräsentationen der Domain-Modelle
- sicherer Parser und erlaubte mathematische Syntax
- Strategie für unveränderliche Workspace-Versionen und Verzweigungen
- Serialisierungsformat und Migrationskonzept
- Plugin- oder Registry-Modell für Werkzeuge und Workflows
- einheitliches Modell für Rechenweg, Provenienz und Quellenreferenzen
- PySide6-Version, unterstützte Python-Versionen und Packaging
- Prozess- oder Thread-Grenzen für lange Berechnungen
- optionale Abhängigkeit und Rolle von `python-control`
- technisch nachweisbare Trennung des Klausur-Builds von KI-Funktionen
