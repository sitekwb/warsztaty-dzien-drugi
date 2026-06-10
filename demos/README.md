# demos/ — dema na żywo (numerowane)

Numeracja jest **dwucyfrowa i zgodna z kolejnością prezentacji**: `demo-NN.sh`
(suflerka — kolejne kroki pojawiają się w terminalu z pauzą na Enter, wspólny
helper `_demo_lib.sh`). Suflerki `.sh` są jedynym źródłem scenariusza.
Na slajdach demo jest wyróżnione **bursztynową obwódką + plakietką „DEMO N"**.

| Demo | Moduł | Slajd (label) | Temat |
|---|---|---|---|
| **00** | — | — | Konfiguracja: narzędzia, login Claude/gh, build+smoke + push mini-banku |
| **01** | M1 | `m1-s02-demo` | Szybka zmiana w kodzie (antywzorzec) |
| **02** | M1 | `m1-s07-demo` | Dekompozycja celu w Claude Code (`/plan`) |
| **03** | M1 | `m1-s08-spec` | Planowanie spec-driven (OpenSpec → AFK → grill-me) |
| **04** | M1 | `m1-s10-demo` | Auto-memory + recall między sesjami |
| **05** | M2 | `m2-t1-demo` | Przejęcie celu agenta (prompt injection) |
| **06** | M2 | `m2-t2-demo` | Nadużycie narzędzi (surowa powłoka vs hook) |
| **07** | M2 | `m2-t3-demo` | Uprawnienia: odczyt sekretów vs deny-lista |
| **08** | M2 | `m2-t4-demo` | Łańcuch dostaw (złośliwy skill / MCP) |
| **09** | M2 | `m2-t5-demo` | Nieoczekiwane wykonanie kodu / piaskownica |
| **10** | M2 | `m2-t6-demo` | Zatrucie pamięci i kontekstu |
| **11** | M2 | `m2-t7-demo` | HITL: przed skutkiem vs po fakcie |
| **12** | M2 | `m2-t8-demo` | Ryzyka wieloagentowe / denial-of-wallet |
| **13** | M3 | `m3-s08` | Triage pomysłu na żywo (JiraMock: read-only klient z OpenAPI) |
| **14** | M4 | `m4-demo-14` | TDD na bugu odsetek (BUG-03) |
| **15** | M4 | `m4-demo-15` | Systematyczne debugowanie wyścigu (BUG-01) |
| **16** | M4 | `m4-demo-19` | Subagent-driven: eksport CSV transakcji (feature) |
| **17** | M4 | `m4-demo-viz` | Freestyle: wizualizacja stanu konta (feature) |
| **debrief** | M4 | `m2-s11` | DYSKUSJA — debrief warsztatu |

### M4 — jedna ścieżka: 4 ćwiczenia po kolei (dema 14–17)
**Jedna ścieżka**: przechodzisz demo-14 → demo-17 **po kolei** (2 bugi + 2 feature'y),
każde przez **prawdziwy PR GitHub** (`gh` skonfigurowany w demo-00). Każde demo
uruchamiasz bezpośrednio: `bash demos/demo-14.sh` itd.

**Dwa terminale w VM** (po prostu dwie sesje SSH): **A** = `cd mini-bank && claude`
(tu wklejasz prompty), **B** = `bash demos/demo-NN.sh` (suflerka podaje kroki).
W suflerce klawisz **`[c]`** kopiuje pokazany prompt do schowka **laptopa** przez
OSC 52 (działa przez SSH) — wklejasz w terminalu A jednym `Cmd/Ctrl+V`.

Backlog i issues: `mini-bank/LAB_BACKLOG.md` + `bash scripts/create_lab_issues.sh`
(`--dry-run`, by podejrzeć). Każda suflerka kończy się blokiem **dokończenia w swoim tempie**
(akceptacja, git+PR, podpowiedzi schodkowe, stretch, wzorzec) i wskazuje **następne** ćwiczenie.

| Demo | Typ | Item | Technika nacisku |
|---|---|---|---|
| 14 | bug | BUG-03 odsetki/float | TDD red-green-refactor |
| 15 | bug | BUG-01 wyścig | systematic debugging |
| 16 | feature | eksport CSV | subagent-driven development |
| 17 | feature | wizualizacja stanu konta | freestyle (sam wybierasz technikę) |

Rejestr numeracji slajdów: komentarz w `slides/seg-macros.tex` (makra `\demoborder`, `\demobadge`).

## Kontrakt: dwa foldery, goła Ubuntu VM (dostęp tylko przez SSH)

Dema są **self-contained**: kursant dostaje tylko dwa foldery — `demos/` i `mini-bank/`
**leżące obok siebie** (rodzeństwo) — i z samych skryptów stawia całe demo. Maszyna to goła
Ubuntu VM na Azure, dostępna **wyłącznie przez CLI (SSH)**, bez pulpitu i przeglądarki.

```
~/parent/
├── demos/        # skrypty dem
└── mini-bank/    # aplikacja (build+smoke w demo-00, serwowana natywnie w demo-02)
```

Wgranie na VM (z lokalnej maszyny), np.:
```bash
scp -r demos mini-bank user@vm:~/parent/        # albo: git clone na VM
```

### Krok 0 — duża konfiguracja raz na maszynę (potem dema są lekkie)
```bash
bash demos/demo-00.sh        # wykrywa braki i DRUKUJE komendy instalacji (sam nie używa sudo)
# skopiuj je do DRUGIEGO terminala i uruchom (git, curl, Python 3.12, Node 20, claude, openspec, gh)
bash demos/demo-00.sh        # uruchom PONOWNIE, gdy narzędzia są już zainstalowane
```
Gdy narzędzia są gotowe, `demo-00.sh` robi resztę **bez sudo**: login Claude Code, **build + smoke
mini-banku** (żeby kolejne dema startowały szybko), konfigurację **gh CLI** i **push mini-banku na
Twoje prywatne repo**. Reguła w suflerkach: komenda **bez sudo** rusza **Enterem**; komenda **z sudo**
pojawia się jako blok „↪ skopiuj do drugiego terminala".

**Logowanie do Claude Code na headless VM (bez przeglądarki).** Interaktywne `claude`
wypisuje długi URL OAuth, który w terminalu bywa ucinany → błąd „Missing scope parameter”.
Zamiast tego używamy długożyciowego tokenu — **jedyny krok ręczny robisz na laptopie** (wymaga
przeglądarki), resztę `demo-00.sh` wykonuje automatycznie (kroki bez sudo lecą we flow skryptu):
```bash
# na maszynie Z PRZEGLĄDARKĄ (Twój laptop):
claude setup-token          # ukończ OAuth w przeglądarce, skopiuj wypisany token (~1 rok)
```
Potem `demo-00.sh` poprosi o token przy **ukrytym promptcie** (`read -rsp` — token zostaje prywatny,
nie trzeba go przeklejać do skryptu) i sam: wyeksportuje `CLAUDE_CODE_OAUTH_TOKEN`, zdejmie klucze
o wyższym priorytecie (`ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`), utrwali token w `~/.bashrc`
(kolejne sesje SSH), pominie ekran powitalny TUI (`hasCompletedOnboarding`) i zweryfikuje
PRAWDĘ: `claude -p 'powiedz: ok'` musi wypisać `ok`. W bieżącej powłoce token wczytasz przez
`source ~/.bashrc` (lub nową sesję SSH); pierwsze wejście do mini-bank poprosi raz o zaufanie
katalogu („yes”).

Alternatywnie klucz API: `export ANTHROPIC_API_KEY=sk-ant-...` (rozlicza credits API, nie subskrypcję).

### GitHub przez gh CLI — najmniejszy przywilej (token do JEDNEGO repo)

Cel: każdy wypycha swojego mini-banku na **własne prywatne repo**, a token dajemy tak wąski, żeby
agent (Claude przez `gh`) **nie dosięgnął żadnego innego/kluczowego repo**. `demo-00.sh` przeprowadza
przez to interaktywnie; poniżej co dokładnie kliknąć w przeglądarce na laptopie.

**1) Utwórz puste prywatne repo** (na laptopie):
- Wejdź na **github.com/new**.
- **Repository name:** `mini-bank-warsztat`.
- Zaznacz **Private**.
- **NIE** zaznaczaj „Add a README" ani `.gitignore` (wypychamy istniejący kod).
- Kliknij **Create repository**. (Tworzymy klikiem, nie tokenem — dzięki temu token nie potrzebuje
  uprawnienia `Administration` i można go zawęzić do tego jednego repo.)

**2) Wygeneruj token fine-grained o minimalnym zakresie** (na laptopie):
- **Settings** (menu pod awatarem) → **Developer settings** → **Personal access tokens** →
  **Fine-grained tokens** → **Generate new token**.
- **Token name:** np. `warsztat-mbank`. **Expiration:** 7 dni.
- **Resource owner:** Twoje konto.
- **Repository access:** **Only select repositories** → wybierz **`mini-bank-warsztat`**.
- **Permissions → Repository permissions** (reszta „No access"):
  - **Contents:** Read and write (push / commit),
  - **Pull requests:** Read and write,
  - **Issues:** Read and write,
  - **Metadata:** Read-only (zaznacza się automatycznie).
  - Zostaw **Administration, Actions, Secrets, Workflows = No access**.
- **Generate token** → skopiuj (widoczny tylko raz).

**3) Zaloguj gh na VM tym tokenem** (token zapisuje się trwale w `~/.config/gh`):
```bash
read -rsp 'Wklej GitHub token: ' GH_TOKEN; echo
printf '%s' "$GH_TOKEN" | gh auth login -p https --with-token   # protokół HTTPS, nie SSH
gh auth setup-git                                               # git push przez poświadczenia gh
printf '\nexport GH_TOKEN=%q\n' "$GH_TOKEN" >> ~/.bashrc        # utrwal (działa też sam 'git push')
```

**4) Wypchnij mini-bank** (na VM mini-bank jest osobnym repo):
```bash
git -C mini-bank remote add origin https://github.com/<login>/mini-bank-warsztat.git
git -C mini-bank branch -M main && git -C mini-bank push -u origin main
```

**Dwie ścieżki pracy (do wyboru, security-framing):**
- **A — agentowo przez gh:** token zawężony do jednego repo → Claude może `gh pr/issue/push`, ale
  fizycznie nie sięgnie innych repo (twarda granica na tokenie). Dodatkowa warstwa lokalna: reguły
  `deny` w `.claude/settings.json` (kolejność **deny > ask > allow**), np. `Bash(git push --force:*)`,
  `Bash(gh repo delete:*)`.
- **B — czysty git:** kto nie chce dawać agentowi GitHuba, używa samego `git push` (token w `GH_TOKEN`),
  bez `gh auth`.

## Jak uruchomić dema

```bash
bash demos/demo-01.sh        # antywzorzec — szybka zmiana bez nadzoru
bash demos/demo-02.sh        # /plan na bugu logowania (bug wstrzykiwany lokalnie)
bash demos/demo-03.sh        # spec-driven (OpenSpec/Spec Kit)
bash demos/demo-04.sh        # auto-memory + recall między sesjami (tylko claude, CLI-only)
bash demos/demo-13.sh        # triage pomysłu: read-only klient z OpenAPI JiraMocka
```

### Demo 13 — wyjątek od „dwóch folderów" (zewnętrzne API)
Demo 13 jako jedyne sięga **poza VM** — do JiraMocka drugiego prowadzącego (Azure).
Wymaga klucza API i (opcjonalnie) sieci:
```bash
# klucz jmk_ generujesz w UI JiraMocka: /Account/Profile (hasło demo: demo)
export JIRAMOCK_API_KEY='jmk_...'
# zalecane przed slotem: odśwież lokalny fallback realnym kluczem
curl -s -H "X-API-Key: $JIRAMOCK_API_KEY" \
  'https://mbank-jiramock-szkolenie.azurewebsites.net/api/v1/issues?limit=5' \
  > demos/m3-jira-mock/fallback/issues-sample.json
```
Bez sieci/klucza demo działa **offline** na `demos/m3-jira-mock/fallback/issues-sample.json`
(klient czyta plik jak odpowiedź API). `bash demos/demo-13.sh --check` raportuje stan.

Każdy skrypt ma `--check` (sama weryfikacja zależności + mini-bank, bez interakcji).
`demo-02.sh` dodatkowo: `--fresh` (reseed) / `--rebuild` (przebuduj frontend) /
`--no-open` (nie pokazuj dostępu) / `--smoke` (self-test: poprawne hasło → 401, błędne → 200).
Demo 02 **samo wstrzykuje bug logowania** — nie wymaga żadnej gałęzi gita.

### Demo 02 — dostęp do aplikacji przez tunel SSH
mini-bank słucha na `127.0.0.1:<port>` **na VM**. Bez przeglądarki na VM dostęp robisz tunelem
z **lokalnej** maszyny (`demo-02.sh` wypisze gotową komendę z właściwym portem):

```bash
ssh -L 8000:127.0.0.1:8000 user@vm     # na lokalnej maszynie
# potem w lokalnej przeglądarce: http://localhost:8000
```

Jedna sesja SSH wystarcza: `demo-02.sh` stawia serwer i prowadzi kroki, a krok z Claude Code
suflerka odpala sama (`claude_seed`) — jej terminal staje się TUI Claude na czas tego kroku.
Tunel SSH puszczasz z lokalnego terminala (osobna sesja tylko dla tunelu).

W suflerce: **Enter** = następny krok, w `runc` **s** = pomiń komendę.

**Krok z Claude Code (dema 01–13).** Suflerka odpala Claude Code sama — bez przeklejania promptu
do drugiego terminala:
- `claude_seed <katalog> [flagi]` — **interaktywnie z promptem już wysłanym** (seed): naciskasz
  Enter, Claude otwiera się już pracując nad promptem (np. `--permission-mode plan`/`acceptEdits`,
  a w demo-01 `--dangerously-skip-permissions` = antywzorzec pełnej autonomii),
  Ty robisz część interaktywną (przegląd planu, grill-me, podgląd AFK, recall pamięci) i wychodzisz
  **Ctrl+D** — wtedy suflerka idzie dalej. To **jeden terminal** (jego okno staje się TUI Claude na
  czas kroku), nie model dwóch terminali + schowek. (Labowe ćwiczenia 14–17 celowo trzymają
  przepływ z przeklejaniem — uczą uczestnika samodzielnego prowadzenia agenta.)
