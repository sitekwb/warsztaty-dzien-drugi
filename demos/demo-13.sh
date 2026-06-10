#!/usr/bin/env bash
# Demo 13 — triage pomyslu na zywo (JiraMock: bootstrap read-only klienta z OpenAPI).
# Suflerka: kolejne etapy pojawiaja sie w terminalu, pauza na Enter.
# Slajd: slide:m3-s08.
# Pomysl klasyfikowany: "agent czyta tickety z Jiry i je streszcza/kategoryzuje".
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=demos/_demo_lib.sh
source "$HERE/_demo_lib.sh"

JIRA_HOST="https://mbank-jiramock-szkolenie.azurewebsites.net"
SPEC_URL="$JIRA_HOST/openapi/v1.json"
FALLBACK="$HERE/m3-jira-mock/fallback/issues-sample.json"
PROJ="${DEMO_JIRA_DIR:-$HERE/demo-jira}"

# weryfikacja srodowiska: narzedzia + (miekko) siec/klucz; brak -> fallback
check_env() {
  require python3 "sudo apt-get install -y python3 python3-venv python3-pip"
  require claude  "sudo npm i -g @anthropic-ai/claude-code"
  require curl    "sudo apt-get install -y curl"
  if [[ -n "${JIRAMOCK_API_KEY:-}" ]]; then
    note "JIRAMOCK_API_KEY: ustawiony."
  else
    warn "JIRAMOCK_API_KEY: brak — demo pojdzie z fallbackiem (offline)."
    note "Klucz jmk_ generujesz w UI: $JIRA_HOST/Account/Profile (haslo demo: demo)."
  fi
  if curl -fsS --max-time 5 -o /dev/null "$SPEC_URL" 2>/dev/null; then
    note "Siec do JiraMock: OK ($SPEC_URL)."
  else
    warn "Brak sieci do JiraMock — demo pojdzie z fallbackiem: $FALLBACK"
  fi
  [[ -f "$FALLBACK" ]] && note "Fallback obecny: $FALLBACK" || warn "Brak pliku fallback: $FALLBACK"
}

# --check: sama weryfikacja, bez interakcji
if [[ "${1:-}" == "--check" ]]; then
  check_env
  say "Demo 13 --check zakonczony."
  exit 0
fi

demo_header "Demo 13 — triage pomyslu na zywo (JiraMock)" "slide:m3-s08"
say "Pointa: pomysl 'agent czyta nasza Jire' przepuszczamy przez 5 tematow modulu."
note "Werdykt 'wymaga refinementu' to nie 'nie' — to nazwane warunki wejscia w scope."
pause

# -- Etap 0 ------------------------------------------------------------------
step "Przygotowanie (przed startem)"
check_env
echo
say "Klucz API + odswiezenie fallbacku (zalecane przed slotem):"
show "export JIRAMOCK_API_KEY='jmk_...'   # z UI: $JIRA_HOST/Account/Profile"
show "curl -s -H \"X-API-Key: \$JIRAMOCK_API_KEY\" '$JIRA_HOST/api/v1/issues?limit=5' > demos/m3-jira-mock/fallback/issues-sample.json"
echo
say "Czysty katalog projektu (suflerka tworzy go u siebie); Claude Code odpali claude_seed:"
runc "mkdir -p '$PROJ' && cd '$PROJ' && git init -q"
note "Prompt bootstrapu pojdzie do Claude juz wyslany (zero przeklejania), w katalogu projektu."
pause

# -- Etap 1 ------------------------------------------------------------------
step "Bootstrap klienta z OpenAPI (AFK, ~1-2 min)"
say "Enter → Claude w katalogu projektu, z promptem bootstrapu juz wyslanym (read-only klient z OpenAPI). Po zbudowaniu Ctrl+D:"
claude_seed "$PROJ" --permission-mode acceptEdits <<EOF
Mam OpenAPI nieswojego API ticketowego (JiraMock): $SPEC_URL
Autoryzacja: naglowek X-API-Key z \$JIRAMOCK_API_KEY. Przy braku sieci/klucza uzyj
lokalnego pliku $FALLBACK jako odpowiedzi GET /issues.
Zbuduj WYLACZNIE read-only klient CLI w Pythonie (tylko stdlib, urllib), ktory:
- pobiera GET /api/v1/issues?limit=5 oraz GET /api/v1/issues/{id} dla pierwszego,
- pobiera slowniki /statuses /priorities /types,
- wypisuje surowe payloady (pretty JSON).
Zero metod zapisujacych. Klucz tylko ze zmiennej srodowiskowej, nie w kodzie.
Najpierw krotki plan, potem implementacja.
EOF
note "Pelny prompt: demos/m3-jira-mock/spec-prompt.md. Trener nie sledzi linijka po linijce."
pause

# -- Etap 2 ------------------------------------------------------------------
step "Odczyt + inspekcja payloadu (na zywo, ~1 min)"
runc "cd '$PROJ' && python3 client.py        # surowe payloady ticketow + slowniki"
say "Wskaz trzy rzeczy w payloadzie (mapuja sie na modul):"
note "PII w free-text (description, comments[].body): nazwiska, PESEL, IBAN, karta -> S05."
note "Brak schematu odpowiedzi w specu (tylko request bodies) -> S04 / data contract."
note "Strukturalne (status/priority/type) vs free-text (summary/description) -> S03."
pause

# -- Etap 3 ------------------------------------------------------------------
step "Werdykt klasyfikacji (na zywo, ~1 min)"
say "Enter → Claude (nowa sesja, ten sam katalog) wyda jednozdaniowy werdykt + warunki wejscia w scope. Oczekiwane:"
note "WYKONALNE, ale wymaga refinementu — wchodzi w scope po:"
note "  1) pseudonimizacja/minimalizacja na ingest (RODO 5(1)(c), 4(5); S05),"
note "  2) data contract dla nietypowanego API (S04),"
note "  3) custody = system zewnetrzny -> licencja/DPA (S06),"
note "  4) routing wywolania modelu przez landing zone (S07)."
say "Te same 5 kryteriow co na slajdach, uzyte jako filtr 'scope / refinement'. Po werdykcie Ctrl+D:"
claude_seed "$PROJ" <<'EOF'
Pomysl: "agent czyta tickety z naszej Jiry i je streszcza/kategoryzuje". Na podstawie
zbudowanego klienta (client.py) i payloadow wydaj JEDNOZDANIOWY werdykt: czy to WYKONALNE
i pod jakimi warunkami wejscia w scope? Odnies sie do: PII w free-text (RODO,
pseudonimizacja na ingest), kontraktu danych dla nietypowanego API, custody danych w
systemie zewnetrznym (licencja/DPA) oraz routingu wywolan modelu przez landing zone.
EOF
pause

bye "Demo 13 zakonczone."
