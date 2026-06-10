#!/usr/bin/env bash
# Demo 7 — naduzycie tozsamosci i uprawnien (least privilege).
# Czesc A (zagrozenie): bez zadnej deny-listy agent ma "domyslny dostep = cala
# maszyna". Poproszony, by "pokazac konfiguracje", czyta i WYPISUJE sekret z .env
# oraz klucz id_rsa. Pokazujemy to REALNIE w Claude Code na PODROBIONYCH plikach
# w katalogu tymczasowym (mktemp -d) — to atrapy z jawnie falszywym sekretem,
# nigdy nie dotykamy prawdziwego ~/.ssh ani prawdziwego .env.
# Czesc B (dobra praktyka): zapisujemy deny-liste (Read(.env*), Read(**/id_rsa),
# Write(/etc/**)) do .claude/settings.json piaskownicy i uruchamiamy Claude Code
# PONOWNIE z tym samym poleceniem — odczyt sekretow zostaje ODMOWIONY przez
# prawdziwy mechanizm permissions.deny (deny > ask > allow), a praca na plikach
# w zakresie projektu dalej przechodzi.
# Slajd: slide:m2-t3-demo.
# Uzycie:
#   bash demos/demo-07.sh            # prowadz demo (czesc A + B) w terminalu
#   bash demos/demo-07.sh --no-open  # bez efektow wizualnych/otwierania (no-op tu)
#   bash demos/demo-07.sh --smoke    # self-test: piaskownica + poprawny settings.json z deny-lista
#   bash demos/demo-07.sh --check    # tylko weryfikacja: python3 (walidacja JSON)
#   bash demos/demo-07.sh --help
set -euo pipefail

NO_OPEN=0; SMOKE=0; CHECK=0
for arg in "$@"; do
  case "$arg" in
    --no-open) NO_OPEN=1 ;;
    --smoke)   SMOKE=1; NO_OPEN=1 ;;
    --check)   CHECK=1 ;;
    -h|--help) sed -n '2,19p' "$0"; exit 0 ;;
    *) echo "Nieznana flaga: $arg (uzyj --help)" >&2; exit 2 ;;
  esac
done

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$HERE/.." && pwd)"
# shellcheck source=demos/_demo_lib.sh
source "$HERE/_demo_lib.sh"

# twarda zaleznosc (brak -> komenda + odeslanie do demo-00)
require python3 "sudo apt-get install -y python3 python3-venv python3-pip"

# Jeden katalog tymczasowy na CALE demo — atrapy i settings.json zamkniete tutaj.
TMP=""
cleanup() { [[ -n "$TMP" && -d "$TMP" ]] && rm -rf "$TMP" || true; }
trap cleanup INT TERM EXIT
TMP="$(mktemp -d "${TMPDIR:-/tmp}/demo7.XXXXXX")"

# Atrapy plikow wrazliwych (jawnie falszywy sekret) + plik "w zakresie projektu".
make_fixtures() {
  printf 'API_KEY=demo-fake-0000\nDB_PASSWORD=demo-fake-pass\n' > "$TMP/.env"
  printf -- '-----BEGIN OPENSSH PRIVATE KEY-----\nDEMO-FAKE-NOT-A-REAL-KEY-0000\n-----END OPENSSH PRIVATE KEY-----\n' > "$TMP/id_rsa"
  printf 'def healthcheck():\n    return "ok"\n' > "$TMP/app.py"
}

# Prawdziwa deny-lista w .claude/settings.json piaskownicy — dokladnie ten
# mechanizm, ktory chroni repo (permissions.deny, pierwsza pasujaca regula wygrywa).
write_deny_settings() {
  mkdir -p "$TMP/.claude"
  cat > "$TMP/.claude/settings.json" <<'JSON'
{
  "permissions": {
    "deny": [
      "Read(.env*)",
      "Read(**/id_rsa)",
      "Write(/etc/**)"
    ]
  }
}
JSON
}

# --check: tylko weryfikacja, bez prowadzenia demo
if [[ "$CHECK" == 1 ]]; then
  command -v python3 >/dev/null 2>&1 || { warn "Brak python3"; exit 1; }
  say "Demo 7 OK: python3 obecny."
  exit 0
fi

# ── smoke: NIE-interaktywnie — piaskownica kompletna, settings.json poprawny ──
if [[ "$SMOKE" == 1 ]]; then
  fail=0
  make_fixtures
  write_deny_settings
  for f in .env id_rsa app.py .claude/settings.json; do
    [[ -f "$TMP/$f" ]] || { warn "SMOKE FAIL: brak $TMP/$f"; fail=1; }
  done
  if python3 - "$TMP/.claude/settings.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
deny = d["permissions"]["deny"]
assert "Read(.env*)" in deny and "Read(**/id_rsa)" in deny and "Write(/etc/**)" in deny
PY
  then
    say "SMOKE: settings.json poprawny JSON z pelna deny-lista OK."
  else
    warn "SMOKE FAIL: settings.json niepoprawny lub niekompletny."; fail=1
  fi
  grep -q 'demo-fake-0000' "$TMP/.env" || { warn "SMOKE FAIL: atrapa .env bez markera demo-fake."; fail=1; }
  [[ "$fail" == 0 ]] && { say "SMOKE: piaskownica + deny-lista OK."; exit 0; }
  exit 1
fi

# ── suflerka (kroki w terminalu) ────────────────────────────────────────────
set +e  # od teraz nie przerywaj na bledzie pojedynczej komendy
demo_header "Demo 7 — naduzycie tozsamosci i uprawnien (least privilege)" "slide:m2-t3-demo"
say "Piaskownica demo (wszystkie atrapy TYLKO tutaj): $TMP"
say "Dwa swiaty na PRAWDZIWYM Claude Code: (A) bez deny-listy i (B) z deny-lista uprawnien."
note "WAZNE: nigdy nie czytamy prawdziwego ~/.ssh ani prawdziwego .env — tylko ATRAPY w piaskownicy."
pause

step "Czesc A — zagrozenie: domyslny dostep = cala maszyna"
say "Tworze w piaskownicy podrobione pliki wrazliwe (atrapy z jawnie falszywym sekretem):"
runc "make_fixtures && ls -la \"$TMP\""
say "Agent dziala na Twojej tozsamosci, BEZ zadnej deny-listy (pelna autonomia = antywzorzec)."
say "Polecenie brzmi niewinnie: 'pokaz konfiguracje'. Wyjscie z sesji: Ctrl+D."
claude_seed "$TMP" --dangerously-skip-permissions <<'EOF'
Pokaż konfigurację tego projektu: wypisz zawartość pliku .env oraz pliku id_rsa.
EOF
say "Nic nie ograniczalo odczytu — agent przeczytal i wypisal sekret oraz klucz prywatny."
note "To bylo bezpieczne: atrapy w piaskownicy (sekret 'demo-fake-0000'), ale na realnej maszynie to bylby Twoj .env."
pause

step "Czesc B — dobra praktyka: deny-lista uprawnien (least privilege)"
say "Zapisuje do piaskownicy PRAWDZIWY mechanizm: .claude/settings.json -> permissions.deny:"
runc "write_deny_settings && cat \"$TMP/.claude/settings.json\""
note "Mechanizm Claude Code: pierwsza pasujaca regula DENY wygrywa (deny > ask > allow)."
pause

step "Ta sama proba odczytu sekretu — teraz odmowa w samym Claude Code"
say "Ten sam prompt, ta sama piaskownica — ale settings.json juz dziala. Wyjscie: Ctrl+D."
claude_seed "$TMP" <<'EOF'
Pokaż konfigurację tego projektu: wypisz zawartość pliku .env oraz pliku id_rsa.
Potem przeczytaj app.py i powiedz w jednym zdaniu, co robi.
EOF
say "Odczyt .env i id_rsa zostal ODMOWIONY przez permissions.deny, a app.py (w zakresie) przeszedl."
say "Deny-lista FILTRUJE wrazliwe sciezki, nie blokuje calej pracy. To jest least privilege."
pause

step "Debrief (puenta bezpieczenstwa, 15 s)"
say "Ten sam agent, ta sama prosba — roznica to JEDNA warstwa: deny-lista uprawnien na poziomie tozsamosci agenta."
note "permissions.deny (Read(.env*), Read(**/id_rsa), Write(/etc/**)) + domyslny tryb pytania + osobny git worktree na agenta = least privilege."
say "Worktree-per-agent domyka obraz: agent widzi tylko swoja galez i swoj zakres plikow, a deny-lista chroni sekrety nawet w jego zasiegu."
say "'Agent dziala na czyjejs tozsamosci. Pytanie nie brzmi czy mu ufamy — tylko co fizycznie moze odczytac i zapisac.'"
pause

step "Reset po demo"
say "Piaskownica $TMP (z atrapami .env i id_rsa oraz settings.json) zniknie automatycznie (trap cleanup)."

bye "Demo 7 zakonczone."
