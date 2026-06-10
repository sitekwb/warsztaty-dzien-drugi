# Lab issues — mini-bank (Day 2, Moduł 2)

Cztery niezależne ścieżki labu. Każda jest gotowym issue do założenia na GitHubie lub GitLabie *as-is*. Każda na osobnym branchu, każda zatrzymuje się przed `git push`. Pełny lab = 35 minut wykonywania + 5 minut debriefu.

Przed startem każdej ścieżki: skopiuj odpowiedni profil uprawnień do `.claude/settings.json` (przykłady poniżej, w sekcjach „Permissions profile"). Po wykonaniu nie commituj `.claude/settings.json` — to lokalny profil per-ścieżka.

---

## LAB-01 — Fix float-cast in `interest.py` (BUG-03)

**Opis.** W `mini-bank/backend/src/minibank/interest.py` zaplanowany bug BUG-03: odsetki liczone są jako `float` w pętli okresów, co kumuluje błąd zaokrąglenia (~0.01 PLN po 12 okresach, ~0.5 PLN po 60). Istnieje już `xfail` test w `tests/test_interest.py`, który ma się flipnąć na pass po fixie. Pracuj wyłącznie w katalogu `mini-bank/`. Użyj cyklu red-green-refactor: najpierw zdejmij `@pytest.mark.xfail`, potwierdź czerwony test, dopiero potem napraw kod w `interest.py` (kluczowy ruch: `Decimal(str(rate))` per okres, nie `float`), uruchom test ponownie, ostatecznie refaktor.

**Acceptance criteria:**
- [ ] `pytest mini-bank/backend/tests/test_interest.py -v` zielony bez `xfail`
- [ ] Diff dotyka wyłącznie `interest.py` + `test_interest.py` (zdjęty `xfail`)
- [ ] Nowy commit na branchu `fix/lab-01-interest-bug03`, podpisany
- [ ] Nie tknięte: `.env`, `settings.json`, `alembic/`, frontend
- [ ] PR otwarty, ale **nie zmergowany** — to robi trener po sesji

**Suggested skill:** `superpowers:test-driven-development`
**Permissions profile (`.claude/settings.json`):**
```json
{
  "permissions": {
    "defaultMode": "ask",
    "allow": ["Read(./mini-bank/**)", "Edit(./mini-bank/backend/src/minibank/interest.py)", "Edit(./mini-bank/backend/tests/test_interest.py)", "Bash(pytest mini-bank/**)"],
    "deny": ["Bash(git push:*)", "Bash(gh pr merge:*)", "Read(~/.ssh/**)", "Read(~/.aws/**)", "Read(./.env*)"]
  }
}
```
**HITL gates:** (1) approve plan-mode przed wyjściem z planu; (2) review diffu przed `git commit`; (3) review PR przed merge (trener).
**Stop-condition:** zatrzymaj przed `git push`. Trener otwiera issue, agent woła „done", trener manualnie pusha.
**Why safe (OWASP):** LLM06 nadmierna autonomia → deny na `git push`/`gh pr merge`; LLM02 wycieki danych → deny na `.env`/`~/.ssh`. Patch ograniczony do dwóch plików, ryzyko regresji znika strukturalnie.

---

## LAB-02 — Code-review read-only PR

**Opis.** Wybierz jeden otwarty PR z `mini-bank/prs/BAD-PR.patch` (lub aktualny PR w GitHub/GitLab repo). Agent działa w *plan-mode-only* — `ExitPlanMode` nigdy nie woła. Output = markdown z review w `review-output/lab-02-<pr-id>.md`. Sprawdzasz: (1) czy PR wprowadza ryzyko OWASP LLM Top 10; (2) czy są sekrety; (3) czy nie psuje existing testów. Bez edycji kodu, bez Bash, tylko Read + Write do `review-output/`.

**Acceptance criteria:**
- [ ] Plik `review-output/lab-02-<pr-id>.md` ze strukturą: PR summary → flagi OWASP LLM01..LLM10 → konkretne linie kodu → severity (Low/Med/High)
- [ ] Minimum 3 flagi (lub uzasadnione „none" per kategoria)
- [ ] Brak edycji w `src/`, brak żadnego `Bash()` wywołania
- [ ] Plan-mode wskaźnik w sesji pozostaje aktywny do końca
- [ ] Review pomija pliki niewchodzące w diff PR

**Suggested skill:** `superpowers:using-superpowers` + plan-mode only
**Permissions profile (`.claude/settings.json`):**
```json
{
  "permissions": {
    "defaultMode": "deny",
    "allow": ["Read(./mini-bank/**)", "Read(./mini-bank/prs/**)", "Write(./review-output/**)"],
    "deny": ["Edit(*)", "Write(./mini-bank/**)", "Bash(*)", "mcp__*__delete*", "mcp__*__merge*"]
  }
}
```
**HITL gates:** (1) plan zatwierdzony przed produkcją markdown; (2) review markdown czytany przez trenera przed publikacją; (3) komentarz na PR ręcznie wklejony przez attendee.
**Stop-condition:** plik markdown istnieje + plan-mode dalej aktywny. Agent nie woła `gh pr comment`.
**Why safe (OWASP):** LLM06 wymuszone strukturalnie przez `defaultMode: deny` + `Bash(*)` deny; LLM01 prompt injection mityguje plan-mode (każdy ruch widoczny przed wykonaniem).

---

## LAB-03 — Subagent test-gen pass

**Opis.** Dodaj testy property-based (`hypothesis`) do czterech modułów: `fraud_score.py`, `interest.py`, `timezone_check.py`, `transfer_service.py`. Architektura: orchestrator + 4 subagenty, każdy w izolowanym worktree (`worktrees/lab-03-<module>`). Każdy subagent dostaje deny na `src/**` (tylko `tests/**` write), własny token-budget cap, własny PAT scope. Wzorzec evaluator-optimizer: orchestrator zbiera diffy, mergeuje do `tests/B-property` po review.

**Acceptance criteria:**
- [ ] 4 worktree (jeden per moduł), żaden subagent nie pisze do `src/**`
- [ ] Branch coverage `mini-bank/backend/src/minibank/` rośnie z 62% do ≥80%
- [ ] Mutation score (np. `mutmut`) +15 p.p.
- [ ] Zero nowych flaky testów (`pytest --count=5` zielony)
- [ ] Każdy subagent ma własny token-budget cap (np. 80k input tokens) zapisany w jego prompt

**Suggested skill:** `superpowers:subagent-driven-development`
**Permissions profile (`.claude/settings.json`, per-subagent):**
```json
{
  "permissions": {
    "defaultMode": "ask",
    "allow": ["Read(./mini-bank/**)", "Write(./mini-bank/backend/tests/**)", "Bash(pytest mini-bank/**)", "Bash(git worktree:*)"],
    "deny": ["Write(./mini-bank/backend/src/**)", "Bash(git push:*)", "Bash(curl:*)", "Bash(wget:*)"]
  }
}
```
**HITL gates:** (1) plan orchestratora zatwierdzony; (2) per-subagent diff review przed merge do `tests/B-property`; (3) sign-off na delcie coverage przez tech leada.
**Stop-condition:** wszystkie 4 worktree zamknięte, branch `tests/B-property` na review, brak `git push`.
**Why safe (OWASP):** LLM06 → write deny na `src/**` strukturalnie blokuje sabotaż implementacji; LLM10 unbounded consumption → per-subagent token-budget cap.

---

## LAB-04 — Migration planner (plan only)

**Opis.** Zaplanuj zero-downtime dodanie kolumny `transactions.category` do tabeli `transactions`. Agent pisze wyłącznie plan w markdown (`docs/migrations/lab-04-category.md`); SQL/Alembic piszę człowiek po review. Agent NIGDY nie woła `ExitPlanMode` — cała sesja w plan-mode. Wzorzec: expand-contract (1) ADD COLUMN nullable; (2) backfill batch w aplikacji; (3) zmiana defaultu; (4) cleanup. Każdy krok ma swój rollback + lock-impact analysis.

**Acceptance criteria:**
- [ ] Plik `docs/migrations/lab-04-category.md` istnieje
- [ ] Struktura: cel → 4 fazy (expand → backfill → flip → contract) → rollback per faza → lock-impact analysis per faza → freeze-window respect
- [ ] Brak generowania SQL/Alembic Python — tylko prose plan
- [ ] Brak `Edit`/`Write` na `alembic/versions/`, brak `Bash()`
- [ ] Plan ma jawną sekcję „risks + mitigators" z minimum 3 wpisami

**Suggested skill:** `superpowers:writing-plans` + `superpowers:brainstorming`
**Permissions profile (`.claude/settings.json`):**
```json
{
  "permissions": {
    "defaultMode": "deny",
    "allow": ["Read(./mini-bank/**)", "Write(./docs/migrations/lab-04-category.md)"],
    "deny": ["Edit(*)", "Write(./mini-bank/**)", "Write(./alembic/**)", "Bash(*)", "mcp__*"]
  }
}
```
**HITL gates:** (1) review planu przez DBA; (2) SQL pisany przez człowieka; (3) shadow-DB dry-run; (4) zatwierdzenie okna prod.
**Stop-condition:** plik markdown gotowy + plan-mode dalej aktywny. Agent nie woła `ExitPlanMode`, nie generuje kodu.
**Why safe (OWASP):** LLM06 → read-only enforce + plan-mode wymusza, że żaden ruch nie wychodzi poza markdown; LLM02 → schema dump bez wierszy, brak ekspozycji danych klientów.

---

## For your team: GitLab > GitHub

Mini-bank ląduje na publicznym GitHubie wyłącznie w celach treningowych. W zespole **issues labu zakładacie na self-hosted GitLabie**. Dla banku regulowanego (KNF, EBA, DORA) GitLab ma pięć przewag, których GitHub nie domyka:

1. **Self-hosted w VPC** — GitLab Omnibus / Charts pod waszą kontrolą sieciową, w istniejącej landing zone. Audytor KNF ma fizyczny ślad pakietu.
2. **Granularne role permissions** — Guest/Reporter/Developer/Maintainer/Owner per project, per group, per subgroup. GitHub Org permissions są płaskie.
3. **Natywny eksport audit logu** — Audit Events stream → S3/Splunk/SIEM out-of-the-box. GitHub Enterprise Cloud wymaga GitHub Audit Log Streaming API + customowy ETL.
4. **Separation-of-duties w modelu ról** — Maintainer mergeuje, Developer pushuje na feature branch, Owner zarządza protected branches. Z EBA/GL/2019/04 sec. 3.4.4 *separation of duties* dostajecie strukturalne wsparcie.
5. **Precedens KNF/DORA** — mBank, ING, Santander, KIR mają GitLab self-hosted od lat. Audytorzy wiedzą co oglądać. GitHub Enterprise w polskim banku regulowanym to ciągle exception, nie default.

**Mapowanie wzorców z labu 1:1:**

| Wzorzec z LAB-01..04 | GitHub | GitLab |
| --- | --- | --- |
| PAT | Fine-grained Personal Access Token | Project Access Token |
| Branch protection | Ruleset | Protected Branch |
| Transparency log | (brak natywny — Sigstore/Rekor obok) | Audit Events stream |
| Service principal | GitHub App | Bot user / Service Account (Premium) |
| Signed commits | Sigstore/gitsign | GPG / Sigstore (od 16.x natywnie) |

Wszystkie cztery permissions profile z LAB-01..LAB-04 działają na GitLabie identycznie — Claude Code nie rozróżnia hostingu, sprawdza tylko ścieżki, Bash i MCP. Jedyny realny przełącznik to MCP server (`github-mcp` → `gitlab-mcp` w `enabledMcpjsonServers`).
