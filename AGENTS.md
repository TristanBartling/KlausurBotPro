# Dauerhafte Arbeitsregeln

- Vor Änderungen relevante Dokumentation lesen und den Auftragsumfang strikt einhalten.
- Keine zukünftigen Roadmap-Punkte ungefragt implementieren.
- Fachlogik, Application Services, Integrationen und UI strikt trennen; Fachlogik gehört nie in UI-Callbacks.
- Keine Fachformeln erfinden und Musterlösungen nicht ungeprüft übernehmen.
- Jede mathematische Funktion benötigt Unit-Tests; offizielle Referenzaufgaben später als Regressionstests verwenden.
- Exakte symbolische Ergebnisse bevorzugen; numerische Ergebnisse toleranzbasiert prüfen.
- Nutzereingaben nie unsicher auswerten, insbesondere nicht mit `eval`.
- Keine globalen veränderlichen Zustände, God Classes oder vermischten Verantwortlichkeiten einführen.
- Keine Produktionsabhängigkeit ohne Begründung in `docs/DECISIONS.md` ergänzen.
- Keine API-Schlüssel, Geheimnisse, lokalen Datenbanken oder persönlichen Daten committen.
- Vor Abschluss Tests, Linter und Typprüfung ausführen; Fehler beheben statt Prüfungen abzuschwächen.
- Keine Dateien außerhalb dieses Repositorys verändern.
- Keine Commits oder Pushes ohne ausdrücklichen Auftrag ausführen.
- Nach jedem Auftrag geänderte Dateien, Befehle, Prüfergebnisse und verbleibende Risiken nennen.

## Fachliche Quellenhierarchie

Bei fachlichen Entscheidungen gilt in absteigender Priorität:

1. aktuelle offizielle Klausur- und Hilfsmittelregeln;
2. offizielles Skript und Vorlesungsunterlagen;
3. offizielle Übungen und Musterlösungen;
4. Tutoriums- und Praxisunterlagen;
5. aktuelle und frühere Klausuren;
6. Tabellen und Übersichten;
7. `docs/reference/RT1_Rechenwege_Master.md` als abgeleitete Entwicklungsreferenz;
8. allgemeines Fachwissen, das ausdrücklich als solches gekennzeichnet ist.

Bei Widersprüchen gelten die höher priorisierten offiziellen Quellen.
`docs/reference/RT1_Rechenwege_Master.md` ist bei neuen Aufgabenworkflows,
aufgabentypspezifischen Application-Workflows, Rechenweg- und Lösungsberichten,
GUI-Ausgaben mathematischer Rechenschritte sowie Plausibilitäts- und
Fehlermeldungen verbindlich heranzuziehen. Sie dient der Erkennung von
Aufgabentypen, der Reihenfolge klausurtauglicher Rechenschritte, typischen
Fehlern und Plausibilitätsprüfungen.

Kennzeichnungen sind dabei strikt zu beachten:

- `[OFFIZIELL]`: nach Prüfung als offizielle Aussage nutzbar;
- `[MITSCHRIFT]`: nur Hinweis auf ein Tutoriumsvorgehen;
- `[HERLEITUNG]`: mathematisch prüfen;
- `[KORRIGIERT]`: gegen eine offizielle Quelle verifizieren;
- `[UNKLAR]`: niemals stillschweigend als feste Programmregel übernehmen.

Die Markdown-Referenz ist keine Laufzeitquelle und wird von der Anwendung
weder geladen noch interpretiert.
