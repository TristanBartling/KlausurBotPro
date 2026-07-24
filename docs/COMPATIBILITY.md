# Technologie- und Kompatibilitätstest

Stand: 18. Juli 2026. Geprüft wurde eine lokale 64-Bit-Windows-11-Umgebung mit
CPython 3.14.0 und `pip` 26.1.2. Alle Pakete wurden gemeinsam in der
Repository-`.venv` installiert. `slycot` wurde weder installiert noch zu
installieren versucht.

## Geprüfte Versionen

| Komponente | Version | Ergebnis unter Python 3.14 |
|---|---:|---|
| PySide6 / Qt | 6.11.1 / 6.11.1 | Wheel installiert; Fenster im Offscreen- und Desktop-Test startbar |
| SymPy | 1.14.0 | Import und symbolische Faktorisierung erfolgreich |
| NumPy | 2.5.1 | CPython-3.14-Wheel; Eigenwertberechnung erfolgreich |
| SciPy | 1.18.0 | CPython-3.14-Wheel; `scipy.special.expit` erfolgreich |
| Matplotlib | 3.11.1 | CPython-3.14-Wheel; Figure mit nichtinteraktivem `Agg`-Backend erzeugt |
| control | 0.10.2 | Import und SISO-Transferfunktion ohne Slycot erfolgreich |

Zusätzlich liefen pytest, Ruff, mypy und `pip check` gemeinsam erfolgreich.
Diese Prüfung belegt den verwendeten Stack und die getesteten Grundoperationen,
nicht jede Funktion oder jede zukünftige Paketkombination.

## Windows-Beobachtungen

- Für alle direkten Produktionsabhängigkeiten waren passende Wheels verfügbar;
  Compiler oder Systembibliotheken waren nicht erforderlich.
- PySide6 bringt große Qt-Binärpakete mit. Downloadgröße, Installationsgröße und
  späteres Deployment bleiben vor einer Paketierung gesondert zu bewerten.
- Headless-Tests benötigen `QT_QPA_PLATFORM=offscreen`. Der normale Desktopstart
  verwendet das Windows-Qt-Backend. Weil `control` Matplotlib importiert, wird
  für Tests zusätzlich `MPLBACKEND=Agg` vor allen Bibliotheksimports gesetzt.
- Beim ersten Matplotlib-Import kann lokal ein Font-Cache aufgebaut werden.
- SymPy, SciPy und control stellen in den getesteten Versionen keine für den
  strikten mypy-Lauf vollständig nutzbaren Typinformationen bereit. Die
  mypy-Konfiguration ignoriert deshalb ausschließlich fehlende Imports dieser
  Drittanbieterpakete; eigener Code und Tests bleiben strikt geprüft.
- Die offizielle python-control-Dokumentation weist darauf hin, dass eine
  Slycot-Installation per `pip` insbesondere unter Windows wegen C- und
  Fortran-Compileranforderungen schwierig sein kann. Ein solcher Versuch war
  ausdrücklich nicht Teil dieser Prüfung.

## python-control ohne Slycot

Die getestete Basisfunktion `control.tf` arbeitet ohne Slycot. python-control
verwendet für mehrere Routinen SciPy-Fallbacks, jedoch nicht für alle
fortgeschrittenen Verfahren. In control 0.10.2 sind ohne Slycot insbesondere
folgende Bereiche nicht oder nur eingeschränkt verfügbar:

- balancierte Modellreduktion (`balanced_reduction` / `balred`)
- robuste H₂- und H∞-Synthese (`h2syn`, `hinfsyn`, damit auch entsprechende
  `mixsyn`-Pfade)
- Varga-Polplatzierung (`place_varga`)
- bestimmte Gramians und zustandsraumbasierte Minimalrealisierungen
- MIMO-`disk_margins`
- Transferfunktion-zu-Zustandsraum-Konvertierung über den SciPy-Fallback nur
  für SISO; andere Konvertierungen besitzen teilweise SciPy-Fallbacks
- einzelne Systemnorm-, Riccati-, Lyapunov- und verallgemeinerte
  Gleichungspfade, abhängig von Problemtyp und gewählter Methode

Maßgeblich sind die
[Installationshinweise von python-control 0.10.2](https://python-control.readthedocs.io/en/0.10.2/intro.html)
und die jeweilige Funktionsdokumentation. Vor Nutzung eines solchen Verfahrens
muss dessen konkreter No-Slycot-Pfad separat getestet werden.

## Releasevalidierung `v0.1.1-exam`

Am 24.07.2026 wurde der Release-Kandidat unter 64-Bit-Windows 11 mit CPython
3.14.0 vollständig geprüft:

- `1824` pytest-Tests bestanden,
- Ruff und MyPy 2.3.0 bestanden,
- `pip check` und Versionssynchronität bestanden,
- Wheel und Source Distribution mit Version `0.1.1` gebaut,
- Wheel mit allen deklarierten Produktionsabhängigkeiten in einer neuen,
  nicht erbenden virtuellen Umgebung installiert,
- Import sowie Offscreen-Initialisierung aller sechs Haupttabs mit sauberem
  Shutdown bestanden,
- Archive auf Paketquellen und notwendige Metadaten begrenzt; keine
  repositoryweiten Dokumente, Tests, PDFs oder lokalen Artefakte enthalten.

## Bewertung von Python 3.14

Python 3.14 kann für die aktuelle Entwicklungsphase beibehalten werden. Die
sechs geplanten Bibliotheken ließen sich gemeinsam installieren und die
geforderten Grundoperationen sowie das Packaging für `v0.1.1-exam` liefen
erfolgreich. Dies ist keine plattformübergreifende Supportzusage:
Langzeitbetrieb, Performance, Drittanbieter-Plugins sowie macOS und Linux
benötigen eigene Validierung.
