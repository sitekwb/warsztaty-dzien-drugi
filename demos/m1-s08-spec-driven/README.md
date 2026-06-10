# Demo 3 — Planowanie spec-driven (runbook trenera)

Slajd: `m1-s08-spec`. Projekt: `docs/superpowers/specs/2026-06-04-demo3-spec-driven-design.md`.
Nagranie zapasowe: `docs/runbook/m1-s08-demo3-spec-driven-recording.md` → `fallback/`.

Cel: pokazać, że przy precyzyjnym specu agent buduje **AFK** (away-from-keyboard), a
bramką są spec + testy, nie nadzór. Potem drobna poprawka przez `grill-me`.

## Etap 0 — przygotowanie (przed slotem, nie na żywo)

```bash
mkdir demo-kredyt && cd demo-kredyt
git init
npm i -g @fission-ai/openspec    # lub potwierdzić, że już jest
openspec --version
claude                            # Claude Code w katalogu
```

- Sprawdzić sieć i dostęp do modelu.
- Mieć otwarte nagranie zapasowe na wypadek awarii live.

## Etap 1 — spec (na żywo, ~2 min)

```bash
openspec init
```

W Claude Code wkleić intencję z `spec-prompt.md`:

```
/opsx:propose
```

Pokazać wygenerowane: `openspec/changes/<nazwa>/` — proposal + spec + tasks (markdown,
w gicie). Podkreślić: to jest intencja PRZED kodem.

## Etap 2 — build AFK (w tle, bez komentowania)

```
/opsx:apply
```

Agent implementuje wg specu (TDD, sam pisze testy). Trener NIE śledzi linijka-po-linijce
— mówi, dlaczego spec-first zwalnia z pilnowania, albo czeka. Koniec: testy zielone.

## Etap 3 — weryfikacja (na żywo, ~1 min)

```bash
python3 -m pytest -q          # zielony
python3 -m kalkulator         # interaktywnie: kwota / oprocentowanie / raty / typ
```

Pokazać harmonogram + sumę odsetek + RRSO. Potem domknąć zmianę:

```
/opsx:archive
```

## Etap 4 — poprawka przez grill-me (na żywo, ~2 min)

Chciana zmiana: „dodaj jednorazową nadpłatę w wybranej racie". Zamiast od razu kodować:

```
/grill-me
```

`grill-me` przepytuje o intencję / edge-case'y (nadpłata skraca okres czy zmniejsza ratę?
co przy nadpłacie > saldo?). Dopiero po domknięciu intencji — zmiana. Pointa: spec-first
działa też w mikro-skali.

## Timing i fallback

- Część live: ~5 min (+ AFK w tle). 
- Awaria (sieć/agent) → odtworzyć `fallback/` (patrz recording doc).
