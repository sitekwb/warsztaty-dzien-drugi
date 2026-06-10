#!/usr/bin/env bash
# Demo 14 — TDD na bugu odsetek (BUG-03). Technika: red-green-refactor.
# Suflerka: kolejne kroki w terminalu, pauza na Enter. Pelny scenariusz:
# demos/demo-14-tdd-odsetki.md. M4 cwiczenie 1/4 (bug).
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=demos/_demo_lib.sh
source "$HERE/_demo_lib.sh"

SMOKE=0
case "${1:-}" in
  --check)
    require python3 "sudo apt-get install -y python3 python3-venv python3-pip"
    require claude  "sudo npm i -g @anthropic-ai/claude-code"
    require git     "sudo apt-get install -y git"
    require gh      "patrz demos/demo-00.sh (gh + token na repo mini-bank-warsztat)"
    say "Demo 14 --check OK."; exit 0 ;;
  --smoke) SMOKE=1; pause() { :; }; runc() { printf '  $ %s\n' "$*"; }; mark_done() { :; }; next_demo() { :; } ;;
  "") : ;;
  *) echo "Nieznana flaga: $1 (użyj --check/--smoke)" >&2; exit 2 ;;
esac

MB="$(find_minibank)"
PT="PYTHONPATH=backend/src $(mb_python "$MB") -m pytest"

demo_header "Demo 14 — TDD na bugu odsetek (BUG-03)" "M4 · ćwiczenie 1/4 · technika: TDD"
two_terminals_banner
progress 1 4 "TDD na bugu odsetek (BUG-03)"
say "Pointa: nie zaczynamy od kodu — zaczynamy od CZERWONEGO testu. Dopiero potem minimalny fix."
note "Money-math = integralność: błąd niewidoczny w 3 okresach urasta w 600 (treasury). Commit -> linia Audit-Log."
pause

step "Przygotowanie"
say "Otwórz Claude Code w katalogu mini-bank (drugi terminal):"
show "cd '$MB' && claude"
say "Znajdź swoje issue:"
show "gh issue list --search 'lab-14'"
pause

step "RED — zobacz czerwień (bug aktywny jako xfail)"
runc "cd '$MB' && $PT backend/tests/test_interest.py -v"
say "W Claude Code (NIE naprawiaj jeszcze kodu produkcyjnego):"
paste_block <<'EOF'
Zdejmij @pytest.mark.xfail z testu treasury w tests/test_interest.py, uruchom
go i pokaż, że jest CZERWONY. Nie dotykaj jeszcze interest.py.
EOF
pause

step "GREEN — minimalny fix"
say "Dopiero teraz w Claude Code:"
paste_block <<'EOF'
Napraw interest.py tak, by kapitalizacja szła w całości w Decimal (bez rzutowania
na float per okres). Zmień tylko to, co potrzebne, żeby test był zielony.
EOF
runc "cd '$MB' && $PT backend/tests/test_interest.py -v"
pause

step "REFACTOR — wyczyść bez zmiany zachowania"
say "W Claude Code:"
paste_block <<'EOF'
Test zielony — wyczyść compound() bez zmiany zachowania: jeden tor Decimal,
czytelne nazwy, krótki docstring. Uruchom cały plik testów ponownie.
EOF
note "Diff ma dotykać wyłącznie interest.py (+ zdjęty xfail w teście)."
pause

# ── WŁASNE TEMPO ──────────────────────────────────────────────────────────────
sp_banner
sp "Issue" "gh issue list --search 'lab-14'"
sp "Technika" "TDD red-green-refactor (skill superpowers:test-driven-development)"
accept "test treasury zielony, bez xfail" \
       "diff tylko interest.py (+ test)" \
       "nie tknięte: .env, alembic/, frontend" \
       "PR otwarty i zmergowany po zielonym CI"
hints "RED zanim GREEN — najpierw potwierdź czerwony test, dopiero potem fix." \
      "Błąd siedzi w rzutowaniu float() w pętli okresów — zostań w Decimal." \
      "balance = principal; growth = Decimal(1) + rate; balance *= growth (bez float)."
pr_steps "fix/demo-14-bug03" "fix(interest): kapitalizacja w pełni w Decimal (BUG-03)" "lab-14"
stretch "dopisz test property-based (hipoteza: wynik == oracle Decimal dla losowych stóp/okresów)."
solution_ref "mini-bank/solutions/BUG-03.patch"
sp_end

mark_done 14
next_demo "15"
bye "Demo 14 — gotowe (albo dokończ we własnym tempie wg ramki wyżej)."
