# Warsztaty: Agenci AI — Dzień 2 (materiały dla uczestników)

Komplet materiałów z warsztatu: slajdy, dema na żywo i aplikacja ćwiczeniowa mini-bank.

## Zawartość

| Folder | Co to jest |
|---|---|
| `slajdy/` | Talia warsztatowa: `slides-pl.pdf` (polska) i `slides-en.pdf` (angielska) |
| `demos/` | Suflerki dem `demo-00.sh` … `demo-17.sh` — numeracja zgodna z kolejnością na slajdach |
| `mini-bank/` | Aplikacja ćwiczeniowa (FastAPI + React) ze stanem startowym do ćwiczeń modułu 4 |

## Szybki start (Ubuntu VM lub własna maszyna)

```bash
git clone https://github.com/sitekwb/warsztaty-dzien-drugi.git
cd warsztaty-dzien-drugi
chmod +x demos/demo-00.sh
bash demos/demo-00.sh    # wykrywa braki i DRUKUJE komendy instalacji; uruchom ponownie po instalacji
```

`demo-00.sh` przeprowadzi Cię przez: instalację narzędzi (Python 3.12, Node 20, Claude Code, gh),
logowanie do Claude Code, build + smoke mini-banku i konfigurację GitHuba z tokenem zawężonym
do jednego repo. Sam też przywróci bit wykonywalności pozostałym skryptom.

## Jak uruchamiać dema

Otwórz **dwa terminale** (dwie sesje SSH na VM):

- **Terminal A** — `cd mini-bank && claude` (tu wklejasz prompty dla agenta),
- **Terminal B** — `bash demos/demo-NN.sh` (suflerka prowadzi krok po kroku; klawisz `c` kopiuje pokazany prompt do schowka przez SSH).

Ikony przy demach na slajdach:

- **TRENER** — pokazywane na żywo przez prowadzącego,
- **WSZYSCY** — ćwiczą wszyscy uczestnicy (dema 14–17, moduł 4),
- **W DOMU** — do samodzielnego wykonania po warsztacie.

## Ćwiczenia modułu 4 (dema 14–17)

Jedna ścieżka, po kolei, każde przez prawdziwy PR na GitHubie: 14 (TDD — błąd odsetek),
15 (systematyczne debugowanie — wyścig w przelewie), 16 (subagenci — eksport CSV),
17 (freestyle — wizualizacja stanu konta). Szczegóły i kryteria akceptacji:
`mini-bank/LAB_BACKLOG.md`. Pełne instrukcje środowiska: `demos/README.md`.
