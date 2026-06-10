#!/usr/bin/env bash
# Demo 16 — subagent-driven development: eksport CSV transakcji (feature).
# Suflerka. M4 cwiczenie 3/4 (feature).
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=demos/_demo_lib.sh
source "$HERE/_demo_lib.sh"

SMOKE=0
case "${1:-}" in
  --check)
    require python3 "sudo apt-get install -y python3 python3-venv python3-pip"
    require node    "curl -fsSL https://deb.nodesource.com/setup_20.x | sudo bash - && sudo apt-get install -y nodejs"
    require claude  "sudo npm i -g @anthropic-ai/claude-code"
    require git     "sudo apt-get install -y git"
    require gh      "patrz demos/demo-00.sh"
    say "Demo 16 --check OK."; exit 0 ;;
  --smoke) SMOKE=1; pause() { :; }; runc() { printf '  $ %s\n' "$*"; }; mark_done() { :; }; next_demo() { :; } ;;
  "") : ;;
  *) echo "Nieznana flaga: $1 (użyj --check/--smoke)" >&2; exit 2 ;;
esac

MB="$(find_minibank)"
PT="PYTHONPATH=backend/src $(mb_python "$MB") -m pytest"

demo_header "Demo 16 — subagent-driven: eksport CSV transakcji" "M4 · ćwiczenie 3/4 · technika: subagent-driven development"
two_terminals_banner
progress 3 4 "subagent-driven: eksport CSV"
say "Pointa: feature rozbijamy na niezależne zadania i zlecamy subagentom (test / serwis / endpoint / front)."
note "Eksport danych = ścieżka wycieku: endpoint MUSI sprawdzać właściciela konta i nagłówki, jak list_my_transactions."
pause

step "Przygotowanie"
show "cd '$MB' && claude"
show "gh issue list --search 'lab-16'"
pause

step "Rozbij feature na subagentów"
say "W Claude Code:"
paste_block <<'EOF'
Użyj superpowers:subagent-driven-development. Rozbij feature GET
/accounts/{id}/transactions.csv na niezależne zadania i zleć subagentom:
(a) test integracyjny: autoryzacja właściciela + nagłówek text/csv + Content-Disposition,
(b) funkcja serwisowa generująca CSV z list_account_transactions_bidirectional,
(c) endpoint w api/accounts.py,
(d) przycisk "Pobierz CSV" w frontend/src/pages/AccountDetailPage.tsx.
Zsyntetyzuj wynik; test (a) najpierw czerwony, potem zielony.
EOF
pause

step "Weryfikacja"
runc "cd '$MB' && $PT backend/tests/integration -k csv -v"
note "Front: build + tunel SSH jak w demo-02 (przycisk pobiera plik)."
show "cd '$MB/frontend' && npm run build"
pause

# ── WŁASNE TEMPO ──────────────────────────────────────────────────────────────
sp_banner
sp "Issue" "gh issue list --search 'lab-16'"
sp "Technika" "subagent-driven development (skill superpowers:subagent-driven-development)"
accept "GET /accounts/{id}/transactions.csv zwraca text/csv + Content-Disposition" \
       "endpoint odrzuca konto nie-właściciela (404/403), jak list_my_transactions" \
       "test integracyjny zielony; front ma przycisk pobierania" \
       "PR otwarty i zmergowany po zielonym CI"
hints "Zacznij od subagenta-testera — test definiuje kontrakt endpointu." \
      "Autoryzację skopiuj z istniejącego list_my_transactions (owner_user_id == user.id)." \
      "Serwis: stdlib csv + StringIO; endpoint zwraca StreamingResponse/Response(media_type='text/csv')."
pr_steps "feat/demo-16-csv-export" "feat(accounts): eksport CSV transakcji właściciela" "lab-16"
stretch "dodaj filtr ?from=&to= po dacie i kolumnę 'saldo po transakcji'."
solution_ref "wzorzec autoryzacji: api/accounts.py::list_my_transactions (to greenfield, brak patcha)"
sp_end

mark_done 16
next_demo "17"
bye "Demo 16 — gotowe (albo dokończ we własnym tempie)."
