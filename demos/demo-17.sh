#!/usr/bin/env bash
# Demo 17 — freestyle: wizualizacja stanu konta na stronie mini-banku (feature).
# Suflerka. M4 cwiczenie 4/4 (feature, OSTATNIE — celowo bardziej swobodne).
# Tym razem sam wybierasz technike (TDD / plan mode / subagenci / spec-driven) —
# suflerka podaje tylko cel, kryteria akceptacji i pomysly na prompt.
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
    say "Demo 17 --check OK."; exit 0 ;;
  --smoke) SMOKE=1; pause() { :; }; runc() { printf '  $ %s\n' "$*"; }; mark_done() { :; }; next_demo() { :; } ;;
  "") : ;;
  *) echo "Nieznana flaga: $1 (użyj --check/--smoke)" >&2; exit 2 ;;
esac

MB="$(find_minibank)"

demo_header "Demo 17 — freestyle: wizualizacja stanu konta" "M4 · ćwiczenie 4/4 · technika: dowolna (Twój wybór)"
two_terminals_banner
progress 4 4 "freestyle: wizualizacja stanu konta"
say "Ostatnie ćwiczenie jest FREESTYLE: cel i kryteria są stałe, technikę prowadzenia agenta wybierasz sam."
say "Cel: strona konta w mini-banku pokazuje aktualny stan wizualnie — np. przebieg salda w czasie,"
say "karta podsumowania (saldo, IBAN, waluta) albo wskaźnik wykorzystania budżetu."
note "Frontend ma już wszystko pod ręką: React + Recharts (AccountDetailPage.tsx rysuje już wykres kołowy"
note "wydatków po kategoriach) + MUI. Dane: accountsApi.getOne(id), summaryApi, historia transakcji."
pause

step "Przygotowanie"
show "cd '$MB' && claude"
show "gh issue list --search 'lab-17'"
pause

step "Wybierz technikę i prowadź agenta (freestyle)"
say "Dowolna technika z tego warsztatu — kilka pomysłów na otwarcie:"
note "· TDD: zacznij od testu komponentu/endpointu, dopiero potem implementacja."
note "· plan mode: najpierw read-only rekonesans frontendu i propozycja planu."
note "· subagenci: osobno wykres / endpoint danych / test."
note "· spec-driven: spisz 5-punktowy spec i dopiero wtedy AFK."
say "Przykładowy prompt otwierający (zmień pod własną technikę):"
paste_block <<'EOF'
Na stronie szczegółów konta w mini-bank (frontend/src/pages/AccountDetailPage.tsx)
dodaj wizualizację przebiegu salda w czasie na podstawie historii transakcji
(wykres liniowy Recharts, jak istniejący wykres kołowy kategorii).
Zaproponuj najpierw plan; saldo licz wstecz od bieżącego, bez zmian w money-math.
EOF
pause

step "Weryfikacja"
runc "cd '$MB/frontend' && npm run build"
note "Podgląd: serwer + tunel SSH jak w demo-02; wejdź na stronę konta i sprawdź wykres."
pause

# ── WŁASNE TEMPO ──────────────────────────────────────────────────────────────
sp_banner
sp "Issue" "gh issue list --search 'lab-17'"
sp "Technika" "dowolna — wybierz świadomie i umiej powiedzieć DLACZEGO ta"
accept "strona konta pokazuje wizualizację stanu (wykres lub karta podsumowania)" \
       "dane liczone z istniejących endpointów — bez zmian w money-math backendu" \
       "npm run build przechodzi; widok działa dla konta z 0 transakcji" \
       "PR otwarty i zmergowany po zielonym CI"
hints "Wzorzec wykresu masz w tym samym pliku: donutData + ResponsiveContainer (AccountDetailPage.tsx)." \
      "Saldo w czasie: posortuj transakcje po dacie i licz saldo wstecz od bieżącego." \
      "Pusty stan: brak transakcji → pokaż kartę z samym saldem zamiast pustego wykresu."
pr_steps "feat/demo-17-wizualizacja-konta" "feat(frontend): wizualizacja stanu konta na stronie szczegółów" "lab-17"
stretch "dodaj przełącznik zakresu (30/90 dni) albo drugą serię: wpływy vs wydatki."
solution_ref "istniejący wykres kategorii w AccountDetailPage.tsx (to greenfield, brak patcha)"
sp_end

mark_done 17
next_demo ""
bye "Demo 17 — gotowe. To ostatnie ćwiczenie: dalej DYSKUSJA (bash demos/m4-debrief.sh)."
