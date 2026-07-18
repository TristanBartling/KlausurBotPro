# Projektkonzept

## Zweck und Zielgruppe

KlausurBotPro soll Studierende bei Regelungstechnik 1 beim Lernen und beim
strukturierten Bearbeiten zulässiger Aufgaben unterstützen. Die Anwendung soll
fachlich nachvollziehbare, kurze und auf Papier übertragbare Rechenwege liefern.
Voraussetzungen, Formeln, Zwischenschritte, Rundungen und Warnungen bleiben
sichtbar.

Zielgruppe sind primär Studierende, die sich mit offiziellen Vorlesungs-,
Übungs-, Tutoriums- und Klausurunterlagen vorbereiten. Die Anwendung ersetzt
weder fachliches Verständnis noch die Prüfung der jeweils aktuellen
Klausurregeln.

## Zwei gleichwertige Nutzungsarten

### Einzelwerkzeuge

Langfristig sind Werkzeuge für folgende Gebiete vorgesehen:

- Laplace- und inverse Laplace-Transformation sowie Partialbruchzerlegung
- Pole, Nullstellen, Eigenwerte und Eigenvektoren
- Matrixexponential und Transitionsmatrix
- Übertragungsfunktionen und Zustandsraumdarstellungen
- Hurwitz- und Routh-Kriterium
- Bode-, Nyquist-, Pol-Nullstellen- und Wurzelortskurven
- Blockschaltbildreduktion
- Führungs- und Störübertragungsfunktionen
- Reglerauslegung und Linearisierung

### Geführte Aufgabenworkflows

Workflows bilden vollständige, mehrstufige Klausuraufgaben ab. Jeder Schritt
nimmt strukturierte Eingaben entgegen und liefert strukturierte Ergebnisse für
Folgeschritte. Zwischenergebnisse können manuell überschrieben werden. Der
Nutzer kann jederzeit aus einem Workflow in ein Einzelwerkzeug wechseln und
zurückkehren. Beide Nutzungsarten greifen auf denselben Fachkern zu.

## Gemeinsamer Workspace

Ein späterer Workspace hält Matrizen, Polynome, Übertragungsfunktionen,
Zustandsraummodelle, Regler und Berechnungsergebnisse als typisierte Objekte.
Er soll Verlauf, Verzweigungen, Variantenvergleich und automatische Übernahme
von Zwischenergebnissen ermöglichen. Exakte symbolische Darstellungen bleiben
so lange wie möglich erhalten und werden durch numerische Gegenprüfungen
ergänzt.

## Quellenbrowser und Nachschlagewerk

Offizielle PDFs werden lokal und unverändert verwaltet. Ein Quellenbrowser soll
Formeln, Kurzfragen, typische Fehler und vollständig gerechnete Beispiele
auffindbar machen. Fachliche Aussagen sollen zwischen konkreter Quelle,
eigener Herleitung und ergänzendem allgemeinem Fachwissen unterscheiden.

Direkte aktive Links sollen konkrete lokale PDF-Dateien und belegte Seiten
öffnen. Relative Pfade und ein Manifest machen die Sammlung portabel.
Seitenzahlen dürfen nie geraten werden.

## Externe Online-Schnittstellen

Klassische Online-Dienste und Solver wie Wolfram Alpha können später bei
echtem Nutzen über austauschbare Adapter angebunden werden. Offline-Nutzung
bleibt der Grundfall. Fehler, Zeitüberschreitungen und fehlende Zugangsdaten
dürfen den lokalen Fachkern nicht beeinträchtigen. API-Schlüssel werden nur aus
lokaler Konfiguration bezogen und niemals im Quellcode oder in Git gespeichert.

## Lern- und Entwicklungsintegrationen

Optionale KI-Integrationen können Entwicklung und Lernen unterstützen. Sie
müssen technisch und im Build-Prozess klar von einem späteren Klausur-Build
getrennt sein. Der Klausur-Build darf keine KI-Endpunkte, Schlüssel,
Abhängigkeiten oder versteckten KI-Funktionen enthalten.

## Innovationsfunktionen

- Konsistenzprüfung zwischen DGL, Zustandsraum, Übertragungsfunktion, Polen und
  Eigenwerten
- zielorientierter Rechenwegfinder aus gegebenen und gesuchten Größen
- Klausuraufgaben-Templates und automatische Übergabe von Zwischenergebnissen
- Verlauf und Verzweigung bisheriger Berechnungen
- symbolischer und numerischer Doppelcheck
- automatische Parameter- und Stabilitätsbereiche
- Plausibilitätswarnungen und Variantenvergleich mehrerer Systeme oder Regler
- direkte Verlinkung von Formeln und vollständigen Beispielen
- Messung der tatsächlichen Zeitersparnis je Aufgabentyp
- optionale Gegenprüfung über erlaubte Online-Schnittstellen
- visuelle Matrixeingabe in Tabellenform und sinnvolle Folgeaktionen

## Nichtziele

- Kein OCR-, Foto- oder Kamera-Workflow
- Kein ungeprüftes Abschreiben von Musterlösungen
- Kein Internetzwang
- Kein Blockschaltbildeditor in frühen Phasen
- Kein vollständiges Computeralgebrasystem als Eigenentwicklung
- Keine Umgehung geltender Prüfungs- oder Hilfsmittelregeln
- Keine Fachmodule im Projektfundament der Phase 0

## Qualitätsziele

- fachlich korrekte, nachvollziehbare und quellenbewusste Ergebnisse
- klare Trennung von Domain, Mathematik, Anwendung, Quellen, Integrationen,
  Darstellung und UI
- sichere Verarbeitung von Nutzereingaben ohne `eval`
- strukturierte statt rein textuelle Ergebnisse
- reproduzierbare Tests mit analytischen Grenzfällen und offiziellen Aufgaben
- möglichst lange exakte Symbolik plus toleranzbasierte numerische Kontrolle
- robuste Offline-Funktion und transparente Warnungen
- wartbarer, typisierter und modularer Python-Code
