# LAB_BACKLOG — M4: 4 ćwiczenia na mini-banku (2 bugi + 2 feature'y)

Backlog warsztatowy modułu M4 — **jedna ścieżka, 4 zadania po kolei** (demo-14 → demo-17, nie „wybór
ścieżek"). Każde robisz samodzielnie w Claude Code przez **prawdziwy PR na GitHubie**; każde uczy
**innej techniki** pracy z agentem (ostatnie — freestyle: technikę wybierasz sam). Każde ćwiczenie
uruchamiasz bezpośrednio: `bash demos/demo-NN.sh` (skrót `[c]` = prompt do schowka).
Slajdy: `m4-demo-14`, `m4-demo-15`, `m4-demo-19`, `m4-demo-viz` (obwódka DEMO + plakietka).

## Jak to działa

1. Środowisko i `gh` skonfigurujesz raz: `bash demos/demo-00.sh` (token na prywatne repo
   `mini-bank-warsztat`).
2. Issues w Twoim repo utworzysz jednym poleceniem: `bash scripts/create_lab_issues.sh`
   (lub `--dry-run`, żeby zobaczyć listę bez tworzenia).
3. Każde ćwiczenie prowadzi suflerka: `bash demos/demo-NN.sh`. Na końcu suflerki jest blok
   **WŁASNE TEMPO** (akceptacja, komendy git+PR, podpowiedzi schodkowe, stretch, wzorzec).
4. Wzorzec workflow (każde zadanie): `git switch -c <branch>` → praca techniką danego dema →
   commit (skill `polish-bank-commit-msg`) → `gh pr create` (linkuj issue) → `/code-review` →
   `gh pr merge` po zielonym CI.
5. Bugi mają **czerwony test** jako bramkę (zdejmij `xfail` → red → fix → green). Feature'y są
   greenfield — zaczynasz od testu opisującego kontrakt.

Stan startowy: `PYTHONPATH=backend/src python3 -m pytest -m planted` pokazuje 11 zaplanowanych
pułapek (M4 używa dwóch: BUG-03 i BUG-01; pozostałe zostają w kodzie jako materiał na przyszłość).
Szczegóły jakości pułapek: `CODE_REVIEW.md`.

## Bugi (2)

| # | Tag | Tytuł | Technika | Akceptacja (skrót) |
|---|---|---|---|---|
| 14 | lab-14 | BUG-03: odsetki gubione przy rzutowaniu na float | TDD red-green-refactor | test treasury zielony bez xfail; diff tylko `interest.py` |
| 15 | lab-15 | BUG-01: wyścig w przelewie schodzi pod limit | systematic debugging | wariant jednostkowy zielony; dwa równoległe przelewy nie schodzą pod limit |

## Feature'y (2)

| # | Tag | Tytuł | Technika | Akceptacja (skrót) |
|---|---|---|---|---|
| 16 | lab-16 | Eksport CSV transakcji | subagent-driven development | `GET /accounts/{id}/transactions.csv` (text/csv); odrzuca nie-właściciela |
| 17 | lab-17 | Wizualizacja stanu konta na stronie mini-banku | freestyle (technika do wyboru) | wykres/karta na stronie konta; dane z istniejących endpointów; `npm run build` zielony |

## Backlog przyszłych ćwiczeń (nieużywane w M4, pułapki zostają w kodzie)

| Item | Pułapka / typ | Dawna technika |
|---|---|---|
| BUG-08: kod SCA nie jest związany z kwotą/IBAN | bug (xfail) | security-review |
| BUG-09: idempotency po samym kluczu | bug (xfail) | integracja z mockiem Jiry |
| BUG-06: wygasły grant JIT pozostaje aktywny | bug (xfail) | plan mode first |
| Przelew zbiorczy z 2+ kont | feature (greenfield) | równoległe git worktrees |
| Alert przekroczenia budżetu kategorii | feature (greenfield) | spec-driven |
| Przelew zaplanowany (CRUD) | feature (greenfield) | konwencje repo (.claude/) |
| Eksport logu audytu dla supervisora | feature (greenfield) | pełna pętla PR |

## Debrief

Po przejściu (choćby części) ćwiczeń: `bash demos/m4-debrief.sh` — krótki recap technik i wątków
bezpieczeństwa (TOCTOU, integralność pieniądza, autoryzacja nowych ujść danych), a potem otwarta
DYSKUSJA (slajd `m2-s11`).
