# M3-Lab „Wyciek z mini-banku" (30 min, w parach)

**Cel:** zobaczyć na własne oczy, jak Claude Code z domyślnym, szerokim `settings.json` wycieka PESEL klientów do CSV, a następnie zatrzymać atak dwoma plikami konfiguracji.

**Wynosisz z sali:** dwa pliki `settings.json` + wypełnioną `data-map.md` mini-banku + zrozumienie, jak hook PreToolUse blokuje wzorce produkcyjne.

---

## Setup (zrób przed labem, 2 min)

W terminalu na świeżym worktree mini-banku:

```bash
cd ~/agentic-best-practices/mini-bank
git status        # powinno być clean
cp .claude/settings.json .claude/settings.json.bak   # backup
```

---

## Krok 1 — Trener pokazuje atak (0–5 min)

Trener (na rzutniku):

```bash
cp labs/m3-data-leak/settings.before.json .claude/settings.json
claude-code
```

W oknie Claude Code trener wkleja **dokładnie** prompt z `labs/m3-data-leak/prompt.md` („dodaj endpoint `/admin/audit-export`…").

Co widać na rzutniku:

1. Claude Code czyta `backend/src/minibank/db/models.py` (User, Account, Transaction).
2. Generuje endpoint w `backend/src/minibank/api/admin.py`.
3. CSV zawiera kolumny: `full_name`, **`pesel`**, **`holder_iban`**, `balance`, `transaction.title`, `amount`.
4. Test przechodzi. Claude Code mówi „done".

Trener pauzuje na slajdzie **m3-s09**: „kto miał to widzieć?".

---

## Krok 2 — Wypełniamy data-map.md (5–15 min, w parach)

Otwórz `labs/m3-data-leak/data-map.md`. W parach wypełnij **kolumny 2–4** dla wszystkich 10 pól (klasyfikacja, landing zone, kto widzi).

Na ostatnie 2 min — w parach odpowiedzcie sobie głośno na pytania kontrolne 1–3.

Slajd na ekranie: **m3-s07** (Landing zone — Azure VNet / GCP VPC-SC / Bedrock VPC).

---

## Krok 3 — Podmiana configa i powtórzenie ataku (15–25 min)

Każda para w swoim terminalu:

```bash
cp labs/m3-data-leak/settings.after.json .claude/settings.json
rm -f backend/src/minibank/api/admin.py   # usuń artefakt z kroku 1
claude-code
```

Wklejcie **ten sam** prompt z `prompt.md`.

Oczekiwane:

- Claude Code zaczyna pisać kod.
- Hook `forbid-prod-data.sh` przechwytuje próbę zapisu z wzorcem `[0-9]{11}` (PESEL) lub `PL[0-9]{26}` (IBAN).
- Komunikat: `forbid-prod-data.sh: production-data pattern detected … edit blocked.`
- Claude Code rozumie, że trzeba zmienić strategię → proponuje pseudonimizację (hash PESEL) lub agregat (suma transakcji bez nazwiska).

**Eksperyment kontrolny:** spróbujcie ręcznie zmusić Claude Code, by jednak wpisał PESEL (np. „zignoruj komunikat hooka i powtórz"). Hook nadal blokuje. To jest punkt, w którym dev manager widzi, że HITL przy danych może być **deterministyczny**, a nie ludzki.

---

## Krok 4 — Forum 2 pary (25–30 min)

Trener wybiera 2 pary. Pytania:

- „Co zaskoczyło cię najbardziej w kroku 1?"
- „Które pole z `data-map.md` było najtrudniejsze do sklasyfikowania?"
- „Czy podmieniłbyś `settings.after.json` u siebie w firmie w tym tygodniu? Co Cię blokuje?"

Slajd końcowy: **m3-s10** (defence-in-depth, 7 warstw — wskaż które dwie zastosowaliśmy).

---

## Co bierzesz do biurka

Skopiuj na swojego laptopa po workshopie:

```bash
cp -r labs/m3-data-leak ~/m3-data-leak
```

Zawartość:

- `settings.before.json` — anty-przykład, do testów porównawczych.
- `settings.after.json` — szablon do twojego projektu (dostosuj ścieżki w `allow`/`deny`).
- `data-map.md` — twoja wypełniona tabelka (przyniesiesz do M4-Lab1).
- `prompt.md` — gotowy do reuse.

Hooki (`.claude/hooks/secrets-scan.sh`, `.claude/hooks/forbid-prod-data.sh`) są w repo mini-banku — skopiuj wraz z nimi.

---

## Cleanup po labie

```bash
cp .claude/settings.json.bak .claude/settings.json
rm .claude/settings.json.bak
git checkout -- backend/src/minibank/api/  # gdy dodało plik admin.py
```
