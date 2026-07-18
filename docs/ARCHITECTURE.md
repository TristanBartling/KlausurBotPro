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

## Implementierter Ausdrucksparser (Phase 1A.1)

Der sichere Ausdrucksparser ist in zwei nach innen gerichtete Pakete getrennt:

- `domain` enthält unveränderliche Diagnosen und `ExactExpression`.
- `parsing` enthält Konfiguration, Ressourcenlimits, Normalisierung und die
  AST-Übersetzung. Es darf `domain` importieren; die umgekehrte Richtung ist
  ausgeschlossen.

Rohe Nutzereingaben werden tokenbasiert normalisiert und mit
`ast.parse(..., mode="eval")` in eine kontrollierte Zwischendarstellung
überführt. Die erlaubte Ausdruckssprache besteht ausschließlich aus Zahlen,
freigegebenen Symbolen, Klammern, unären Vorzeichen und den Operatoren
`+`, `-`, `*`, `/` und Potenzen. Python ergänzt Namen intern um den passiven
AST-Kontext `Load`; er trägt keine ausführbare Semantik. Alle anderen
Sprachkonstrukte werden durch eine explizite Whitelist abgelehnt.

Die Normalisierung fügt unmittelbar benachbarte Ziffernfolgen um ein
Dezimalkomma zuerst zu einem Zahlentoken zusammen. Jedes danach verbleibende
Komma ist unabhängig von der Klammertiefe ungültig. Eine vollständige
Token-Adjazenzprüfung erkennt implizite Multiplikation zwischen Zahlen,
freigegebenen Symbolen und mathematischen Klammergruppen; Multiplikation muss
immer mit `*` geschrieben werden. Unbekannte Funktionsnamen werden dadurch
nicht freigegeben, und Funktionsaufrufe bleiben verboten.

Erlaubte AST-Knoten werden manuell in SymPy-Objekte übersetzt. Weder `eval`
noch `sympify` oder `parse_expr` erhalten Nutzereingaben. Dezimalzahlen werden
direkt aus ihrem geprüften Token als rationale Werte konstruiert, sodass keine
binären Float-Zwischenwerte entstehen.

`ExactExpression` kapselt den SymPy-Ausdruck und stellt der späteren
Anwendungsschicht nur Symbolnamen sowie kanonische Text- und
LaTeX-Darstellungen bereit. Die interne Fachkern-Schnittstelle `_as_sympy()`
ist ausschließlich für kontrollierte mathematische Domain-Module vorgesehen,
nicht für rohe Eingaben oder GUI-Code.

Vor symbolischer Verarbeitung gelten zentral konfigurierbare Grenzen für
Eingabelänge, AST-Größe und -Tiefe, konfigurierte und verwendete Symbole,
Ganzzahlziffern, Exponenten und geschätzte Termanzahl. Eine zu große
`allowed_symbols`-Menge wird bereits bei der Konfiguration abgelehnt, bevor
SymPy-Symbole entstehen. Erwartbare `MemoryError`, `RecursionError` und
`OverflowError` aus Normalisierung, Parsing, Validierung und kontrollierter
SymPy-Erzeugung werden als `PARSE_LIMIT_EXCEEDED` gekapselt. Diese Grenzen
reduzieren Denial-of-Service-Risiken, ersetzen aber keinen harten
Prozess-Timeout.

## Implementiertes Polynomial-Domainmodell (Phase 1A.2)

`Polynomial` ist ein unveränderliches, ausschließlich durch
`PolynomialFactory` erzeugbares Wertobjekt auf Basis von `ExactExpression`.
Rohe Strings und Parserfunktionen sind nicht Teil dieser Domain-Schnittstelle.
Die öffentliche API liefert keine SymPy-Typen. Sie stellt die Hauptvariable,
tatsächlich verwendete Parameter, den kanonischen exakten Ausdruck, dichte
Koeffizienten, Termanzahl, Null- und Konstantensemantik sowie explizite
Bedingungen bereit.

Die mathematische Wertidentität enthält keinen Deklarationskontext:
Unbenutzte erlaubte Parameter werden weder im Wert noch im internen
Koeffizientenkörper gespeichert und beeinflussen Gleichheit und Hash nicht.
Verwendet werden ausschließlich kanonische, annahmenfreie Symbole mit
eindeutigen Namen. Globale SymPy-Annahmen werden nicht verändert.

`Polynomial` verwendet verbindlich kanonische Feldsemantik. Es repräsentiert
den kanonischen mathematischen Wert über `QQ` beziehungsweise
`QQ.frac_field`, nicht die vollständige Provenienz der ursprünglichen Eingabe.
Definitionslücken, die vor oder während der kanonischen algebraischen
Reduktion verschwinden, können aus dem Polynomialwert nicht rekonstruiert
werden. So werden `(K/K)*s + 1`, `((K-1)/(K-1))*s` und
`(K*T/K)*s + 1` zu `s + 1`, `s` beziehungsweise `T*s + 1`; die
ursprünglichen Bedingungen `K != 0`, `K - 1 != 0` und `K != 0` sind nicht
Bestandteil des jeweiligen `Polynomial`.

`PolynomialDegreeInfo` trennt den generischen strukturellen Grad vom
bedingungslos garantierten Grad. Ist die Nullheit des führenden symbolischen
Koeffizienten unbekannt, bleibt `guaranteed_degree` leer und eine
`LEADING_COEFFICIENT_NONZERO`-Bedingung nennt den normalisierten Zähler.
Definitionsbedingungen für rationale Parameterkoeffizienten nennen getrennt
den normalisierten Nenner der kanonisch reduzierten Koeffizientendarstellung.
Bedingungen werden dedupliziert und deterministisch sortiert. Zusammengesetzte
Ausdrücke wie `T**2`, `T1*T2` oder `K**2 - 1` sind dabei zulässige
Nichtnull-Normalformen; numerische Faktoren und globale Vorzeichen werden
entfernt. Eine spätere Zerlegung in faktorisierte Einzelbedingungen wäre eine
Verbesserung der Darstellung, ist aber keine Voraussetzung für die
mathematische Korrektheit.

Eine spätere eingabetreue Rohdarstellung einer `TransferFunction` muss
ursprüngliche Faktoren, Definitionsbedingungen und Provenienz vor der
algebraischen Kürzung separat erfassen. Eine davon getrennte reduzierte
Darstellung darf kanonische Feldsemantik verwenden. Diese eingabetreue
Semantik wird nicht nachträglich in `Polynomial` eingebaut; ein solches
Transferfunktionsmodell ist in Phase 1A.2 noch nicht implementiert.

Vor der kontrollierten SymPy-Konvertierung prüft die Fabrik Namen, Symbole,
Ausdrucksknoten, Float-Atome, Funktionen, Hauptvariablenpotenzen, Nenner und
einen sicheren maximalen Grad. Danach begrenzen eigene `PolynomialLimits`
Grad, dichte Koeffizienten, strukturelle Terme, Parameter und
Koeffizientenkomplexität. Ohne Parameter wird `QQ`, mit tatsächlich
verwendeten Parametern ein alphabetisch aufgebauter `QQ.frac_field`
verwendet. Erwartbare Domain-, SymPy- und Ressourcenfehler werden als
strukturierte Diagnosen gekapselt.

## Offene Architekturentscheidungen

- genaue Grenzen und Repräsentationen weiterer Domain-Modelle
- Erweiterung der bewusst kleinen Parsergrammatik für spätere Datentypen
- Strategie für unveränderliche Workspace-Versionen und Verzweigungen
- Serialisierungsformat und Migrationskonzept
- Plugin- oder Registry-Modell für Werkzeuge und Workflows
- einheitliches Modell für Rechenweg, Provenienz und Quellenreferenzen
- PySide6-Version, unterstützte Python-Versionen und Packaging
- Prozess- oder Thread-Grenzen für lange Berechnungen
- optionale Abhängigkeit und Rolle von `python-control`
- technisch nachweisbare Trennung des Klausur-Builds von KI-Funktionen
