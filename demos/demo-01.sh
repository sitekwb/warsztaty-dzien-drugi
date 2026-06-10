#!/usr/bin/env bash
# Demo 1 — szybka zmiana w kodzie (antywzorzec).
# Suflerka: kolejne kroki pojawiają się w terminalu, pauza na Enter.
# Slajdy: slide:m1-s02-setup (uruchomienie środowiska) -> slide:m1-s02-demo.
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$HERE/.." && pwd)"
# shellcheck source=demos/_demo_lib.sh
source "$HERE/_demo_lib.sh"

MB="$(find_minibank)"

# --check: weryfikacja zależności + obecności mini-bank, bez interakcji
if [[ "${1:-}" == "--check" ]]; then
  require git "sudo apt-get install -y git"
  say "Demo 1 OK: git obecny, mini-bank w $MB."
  exit 0
fi

demo_header "Demo 1 — szybka zmiana w kodzie (antywzorzec)" "slide:m1-s02-demo"
say "To demo pokazuje ZŁĄ praktykę. Wszystko lokalnie, dane syntetyczne, reset na końcu."
pause

# ── Krok 1 ─────────────────────────────────────────────────────────────────
step "Uruchom środowisko pracy (slajd: Uruchomienie środowiska)"
say "Stanowisko ze slajdu 2 — otwórz po kolei:"
note "VS Code (web)  → edytor w przeglądarce, katalog mini-bank"
note "Azure          → chmurowy host środowiska (konto szkoleniowe, nie prod)"
note "Claude Code    → terminal: cd mini-bank && claude  (hook forbid-prod-data aktywny)"
note "mini-bank      → aplikacja FastAPI + SPA, dane syntetyczne (SQLite)"
note "GitHub         → repo dema, PR-y, historia"
echo
say "Lokalny pre-flight prereków (brak czegoś → bash demos/demo-00.sh):"
need git
need python3
need node
need claude "Claude Code CLI"
echo
say "Postaw mini-bank lokalnie (potrzebny, żeby agent miał co 'szybko zmienić'):"
runc "build_minibank \"$MB\""        # venv + pip -e backend + build frontu + seed DB (idempotentnie)
require git "sudo apt-get install -y git"
ensure_git_baseline "$MB"            # czysty baseline PRZED zmianą → reset w Kroku 4 zadziała wszędzie
pause

# ── Krok 2 ─────────────────────────────────────────────────────────────────
step "Szybka poprawka BEZ nadzoru (antywzorzec)"
say "Scenariusz: błąd na produkcji, presja czasu — agent w PEŁNEJ autonomii, bez bramek."
say "Enter otworzy Claude Code INTERAKTYWNIE z promptem już wysłanym, bez bramek"
say "(--dangerously-skip-permissions) — to właśnie antywzorzec. Po edycji Ctrl+D wraca tu:"
claude_seed "$MB" --dangerously-skip-permissions <<'EOF'
To lokalny bank DEMONSTRACYJNY na danych syntetycznych (nie produkcja). Zespół
produktowy zatwierdził podniesienie standardowego limitu debetu. Zmień w kodzie
domyślną wartość overdraft_limit (teraz 0) na 100000 i od razu zapisz plik.
Bez testów i bez tłumaczenia — śpieszę się.
EOF
say "Agent zmienił plik reguł i skończył. BRAK: planu, testu, review, śladu w PR."
pause

# ── Krok 3 ─────────────────────────────────────────────────────────────────
step "Puenta ryzyka (1:1 z bulletami slajdu)"
say "Czego zabrakło:"
note "1. Błąd na produkcji — punkt wyjścia, presja realna"
note "2. Presja czasu — wymówka, która wyłącza dyscyplinę"
note "3. Agent bez nadzoru w środowisku produkcyjnym — brak człowieka w pętli"
note "4. Agent bez kontroli wykonania — brak bramek/hooków/uprawnień"
note "5. 'Szybka' 'poprawka' — zmiana reguły pieniężnej bez testu i śladu"
note "6. Duże ryzyko poważnych konsekwencji — limit 100 000 to realna strata"
echo
say "Pomost do Dema 2: 'A teraz to samo, ale poprawnie — niech agent rozłoży cel"
say "na kroki i nic nie ruszy, zanim zatwierdzę plan.'"
pause

# ── Krok 4 ─────────────────────────────────────────────────────────────────
step "Reset po demo"
say "Cofnij 'szybką poprawkę' (mini-bank: $MB):"
runc "reset_minibank \"$MB\""

bye "Demo 1 zakończone."
