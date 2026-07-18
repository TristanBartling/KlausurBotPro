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
