# KlausurBotPro

KlausurBotPro ist eine lokale Python-Desktopanwendung für Regelungstechnik 1.
Sie erzeugt klausurtaugliche Rechenwege mit strukturierten Kontrollen sowie
Plaintext- und LaTeX-Ausgaben. Die Anwendung enthält keine KI- oder
Kommunikationsfunktion.

## Implementierte Hauptbereiche

- **Transferfunktionen:** sichere rationale Eingabe, rohe und reduzierte Form,
  Pole und Nullstellen, Stabilität und qualitative Polinterpretation.
- **Frequenzbereich:** Frequenzgang, Bode, Standardglieder-MVP, Durchtritte und
  Reserven sowie Nyquist.
- **Stabilität:** Hurwitz, Routh und Parameterbedingungen im unterstützten
  Umfang.
- **Zeitbereich:** Laplace, lineare DGL, Partialbruchzerlegung, inverse Laplace
  und Zeitantworten im unterstützten Umfang.
- **Zustandsraum:** charakteristisches Polynom, Eigenwerte,
  Zustandsstabilität und SISO-Übertragungsfunktion.
- **Reglerauslegung:** P-Auslegung über Phasenreserve, Ziegler–Nichols offen
  und geschlossen, Cohen–Coon sowie P-, PI- und PID-Regler im unterstützten
  Umfang.

## Systemanforderungen

- Python 3.12 oder neuer gemäß `pyproject.toml`.
- Geprüfte Releaseumgebung: 64-Bit-Windows 11 mit CPython 3.14.0.
- Für macOS und Linux liegt keine bestätigte Releaseprüfung vor.
- Dieser Release enthält keinen Standalone-Installer.

Details zum geprüften Stack stehen in
[docs/COMPATIBILITY.md](docs/COMPATIBILITY.md).

## Installation unter Windows PowerShell

```powershell
py -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Start

```powershell
python -m klausurbotpro
```

Nach der Installation ist alternativ das Konsolenskript verfügbar:

```powershell
klausurbotpro
```

Bedienung, Eingabeformate und Workflowgrenzen beschreibt das
[AI Operator Manual](docs/ai/KlausurBotPro_AI_Operator_Manual.md).

## Qualitätssicherung

```powershell
python -m pytest
python -m ruff check .
python -m mypy src tests
python -m pip check
python -c "import klausurbotpro; print(klausurbotpro.__version__)"
```

## Wichtige Grenzen

KlausurBotPro ist kein allgemeines CAS, kein beliebiger MIMO-Solver und keine
allgemeine symbolische Parameteralgebra. Lead-/Lag-Auslegung,
Totzeit-Frequenzrechnung und ein Standalone-Windows-Installer gehören nicht zu
diesem Release. Ergebnisse müssen weiterhin gegen Aufgabenstellung, Modellart,
Voraussetzungen und Einheiten geprüft werden.
