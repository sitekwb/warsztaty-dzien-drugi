#!/usr/bin/env bash
# Demo 15 — systematyczne debugowanie wyścigu (BUG-01). Technika: systematic debugging.
# Suflerka. M4 cwiczenie 2/4 (bug).
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
    require gh      "patrz demos/demo-00.sh"
    say "Demo 15 --check OK."; exit 0 ;;
  --smoke) SMOKE=1; pause() { :; }; runc() { printf '  $ %s\n' "$*"; }; mark_done() { :; }; next_demo() { :; } ;;
  "") : ;;
  *) echo "Nieznana flaga: $1 (użyj --check/--smoke)" >&2; exit 2 ;;
esac

MB="$(find_minibank)"
PT="PYTHONPATH=backend/src $(mb_python "$MB") -m pytest"

demo_header "Demo 15 — systematyczne debugowanie wyścigu (BUG-01)" "M4 · ćwiczenie 2/4 · technika: systematic debugging"
two_terminals_banner
progress 2 4 "systematyczny debug wyścigu (BUG-01)"
say "Pointa: nie zgadujemy. Reprodukcja → hipoteza → fix → regresja. Wyścig to TOCTOU → double-spend."
note "Bramką jest wariant JEDNOSTKOWY (niezawodny); wariant e2e bywa flaky (patrz CODE_REVIEW.md)."
pause

step "Przygotowanie"
show "cd '$MB' && claude"
show "gh issue list --search 'lab-15'"
pause

step "Reprodukcja — zobacz, że saldo schodzi pod limit"
runc "cd '$MB' && $PT backend/tests/test_transfers.py -v"
pause

step "Hipoteza PRZED fixem (dyscyplina debugowania)"
say "W Claude Code:"
paste_block <<'EOF'
Zdejmij @pytest.mark.xfail z wariantu jednostkowego w tests/test_transfers.py.
Użyj superpowers:systematic-debugging: nazwij dokładny moment, w którym dwa wątki
widzą to samo saldo (check-then-act). Pokaż mi hipotezę ZANIM zaproponujesz fix.
EOF
pause

step "Fix — uczyń check-then-act atomowym"
say "Dopiero po hipotezie, w Claude Code:"
paste_block <<'EOF'
Zabezpiecz sekwencję czytaj-sprawdź-zapisz zamkiem per-source (threading.Lock na
source_id) albo blokadą wiersza. Sekwencja ma być atomowa; test jednostkowy zielony.
EOF
runc "cd '$MB' && $PT backend/tests/test_transfers.py backend/tests/e2e/test_concurrent_api.py -v"
note "Diff: tylko concurrent_transfer.py / transfer_service.py (+ zdjęty xfail)."
pause

# ── WŁASNE TEMPO ──────────────────────────────────────────────────────────────
sp_banner
sp "Issue" "gh issue list --search 'lab-15'"
sp "Technika" "systematic debugging (skill superpowers:systematic-debugging, /diagnose)"
accept "wariant jednostkowy zielony, bez xfail" \
       "po fixie dwa równoległe przelewy nie schodzą pod limit" \
       "diff tylko w module przelewów (+ test)" \
       "PR otwarty i zmergowany po zielonym CI"
hints "Najpierw reprodukuj i nazwij okno wyścigu — dopiero potem dotykaj kodu." \
      "time.sleep w kodzie poszerza okno — to wskazówka, gdzie jest check-then-act." \
      "Zamek per-source wokół czytaj-sprawdź-zapisz (albo SELECT FOR UPDATE)."
pr_steps "fix/demo-15-bug01" "fix(transfers): atomowy check-then-act per-source (BUG-01)" "lab-15"
stretch "napraw analogiczny wyścig w api/transfers.py::approve_transfer i dopisz test."
solution_ref "mini-bank/solutions/BUG-01.patch"
sp_end

mark_done 15
next_demo "16"
bye "Demo 15 — gotowe (albo dokończ we własnym tempie)."
