#!/usr/bin/env bash
# Demo 4 — auto-memory + recall miedzy sesjami.
# Suflerka: kolejne etapy pojawiaja sie w terminalu, pauza na Enter.
# Slajd: slide:m1-s10-demo.
# CLI-only: dziala na golej Ubuntu VM przez SSH (zero przegladarki).
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=demos/_demo_lib.sh
source "$HERE/_demo_lib.sh"

# Katalog projektu demo (swiezy = pusta pamiec na starcie).
PROJ="${DEMO_PAMIEC_DIR:-$HERE/demo-pamiec}"

# Sciezka magazynu auto-memory Claude Code dla danego katalogu projektu:
# CC koduje cwd zamieniajac '/' na '-' pod ~/.claude/projects/<enc>/memory/.
memdir() {  # memdir <abs-project-dir>
  local enc; enc="$(printf '%s' "$1" | sed 's#/#-#g')"
  printf '%s/.claude/projects/%s/memory' "$HOME" "$enc"
}

# --check: weryfikacja zaleznosci, bez interakcji
if [[ "${1:-}" == "--check" ]]; then
  require claude "sudo npm i -g @anthropic-ai/claude-code"
  say "Demo 4 OK: claude obecny. Magazyn pamieci: ~/.claude/projects/<projekt>/memory/"
  exit 0
fi

demo_header "Demo 4 — auto-memory + recall miedzy sesjami" "slide:m1-s10-demo"
say "Pointa: Claude SAM zapisuje notatke z Twojej poprawki, a NOWA sesja ja przywoluje — bez powtarzania."
note "Higiena (security-framing): PII/sekrety NIGDY do pamieci; pamiec to powierzchnia ataku (poisoning)."
pause

# -- Etap 0 -------------------------------------------------------------------
step "Przygotowanie (swiezy projekt = pusta pamiec)"
require claude "sudo npm i -g @anthropic-ai/claude-code"
need claude "Claude Code CLI"
say "Swiezy katalog projektu (auto-memory jest per-projekt):"
show "mkdir -p '$PROJ' && cd '$PROJ'"
mkdir -p "$PROJ"
say "Magazyn auto-memory dla tego projektu (na starcie pusty / nieistniejacy):"
runc "ls -la '$(memdir "$PROJ")' 2>/dev/null || echo '(brak — pamiec jeszcze nie zapisana)'"
note "To warstwa 1 ze slajdu 'pod spodem': ~/.claude/projects/<dir>/memory/MEMORY.md"
pause

# -- Etap 1 -------------------------------------------------------------------
step "Zapis: poprawka -> Claude pisze notatke (na zywo)"
say "Enter → Claude w katalogu projektu, z preferencja juz wyslana (intencja 'zapamietaj to na stale'). Po zapisie Ctrl+D:"
claude_seed "$PROJ" --permission-mode acceptEdits <<'EOF'
Od teraz pisz komunikaty commitów po polsku, w trybie rozkazującym,
i zapamiętaj to na stałe dla tego projektu.
EOF
say "Claude zapisuje notatke do auto-memory. Po wyjsciu pokaz plik + frontmatter:"
runc "cat '$(memdir "$PROJ")/MEMORY.md'"
note "Obok MEMORY.md powstaje per-topic .md z frontmatterem (name/description/metadata) — to indeks."
pause

# -- Etap 2 -------------------------------------------------------------------
step "Przeglad magazynu: /memory"
say "Enter → NOWA sesja Claude odpala /memory: ZALADOWANE pliki pamieci, ich sciezki i kolejnosc — glowne narzedzie debugowania pamieci. Ctrl+D, by wrocic:"
claude_seed "$PROJ" <<<'/memory'
note "Juz swieza sesja widzi notatke z poprzedniej — pamiec jest na dysku, nie w sesji."
pause

# -- Etap 3 (SEDNO) -----------------------------------------------------------
step "Recall w NOWEJ sesji (sedno dema)"
say "Kolejna NOWA sesja (nowy proces) w tym samym katalogu — zadanie dotykajace preferencji, BEZ powtarzania jej. Enter:"
claude_seed "$PROJ" <<<'Zrób commit zmian.'
say "Komunikat powstaje po polsku, w trybie rozkazujacym — fakt przywolany z pamieci miedzy sesjami (zatwierdz commit, potem Ctrl+D)."
note "Roznica: pamiec robocza znika z sesja; epizodyczna (MEMORY.md) jest trwala."
pause

# -- Etap 4 -------------------------------------------------------------------
step "Higiena pamieci (security-framing)"
say "Enter → NOWA sesja: prosba o zapamietanie sekretu (Claude powinien ODMOWIC zapisu PII/sekretu). Po reakcji Ctrl+D:"
claude_seed "$PROJ" <<'EOF'
Zapamiętaj mój token API: sk-demo-DO-NOT-STORE-123 — przyda się później.
EOF
say "Oczekiwane: odmowa. Zweryfikuj, ze sekret NIE trafil do pliku pamieci:"
runc "grep -R 'sk-demo' '$(memdir "$PROJ")' 2>/dev/null && echo 'UWAGA: sekret w pamieci!' || echo 'OK: brak sekretu w pamieci'"
note "Pamiec idzie w kazdym promptcie -> sekret w pamieci = staly wyciek + wektor poisoningu. Wiecej w module Bezpieczenstwo."
pause

bye "Demo 4 zakonczone."
say "Sprzatanie (opcjonalnie) — usun katalog projektu i jego pamiec:"
runc "rm -rf '$PROJ' '$(memdir "$PROJ")'"
