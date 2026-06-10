#!/usr/bin/env bash
# Demo 9 — nieoczekiwane wykonanie kodu / ucieczka z piaskownicy.
# Czesc A (zagrozenie): w przestrzeni roboczej (mktemp -d) agent pisze kod, ktory
# (1) zawiera podatnosc (SQL sklejany przez konkatenacje stringow) oraz (2) probuje
# zapisac plik POZA swoja przestrzenia robocza ("ucieczka"). Bez izolacji zapis
# poza workspace SIE UDAJE (symulujemy bezpiecznie: cel to sciezka WEWNATRZ katalogu
# tymczasowego, ale POZA podkatalogiem workspace/ — nic realnego nie jest dotykane).
# Czesc B (dobra praktyka): wpinamy (a) maly inline "workspace jail" w Pythonie,
# ktory pozwala na zapis TYLKO pod korzeniem workspace i ODMAWIA sciezki-ucieczki,
# oraz (b) minimalny czerwony test, ktory OBLEWA na podatnym snippetcie (bramka TDD).
# Pokazujemy: ucieczka odmowiona + czerwony test oblewa -> zmiana zablokowana.
# Slajd: slide:m2-t5-demo.
# Uzycie:
#   bash demos/demo-09.sh            # prowadz demo (czesc A + B) w terminalu
#   bash demos/demo-09.sh --no-open  # bez efektow wizualnych/otwierania (no-op tu)
#   bash demos/demo-09.sh --smoke    # self-test: jail odmawia ucieczki, czerwony test oblewa
#   bash demos/demo-09.sh --check    # tylko weryfikacja: python3
#   bash demos/demo-09.sh --help
set -euo pipefail

NO_OPEN=0; SMOKE=0; CHECK=0
for arg in "$@"; do
  case "$arg" in
    --no-open) NO_OPEN=1 ;;
    --smoke)   SMOKE=1; NO_OPEN=1 ;;
    --check)   CHECK=1 ;;
    -h|--help) sed -n '2,18p' "$0"; exit 0 ;;
    *) echo "Nieznana flaga: $arg (uzyj --help)" >&2; exit 2 ;;
  esac
done

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$HERE/.." && pwd)"
# shellcheck source=demos/_demo_lib.sh
source "$HERE/_demo_lib.sh"

# twarda zaleznosc (brak -> komenda + odeslanie do demo-00)
require python3 "sudo apt-get install -y python3 python3-venv python3-pip"

# Jeden katalog tymczasowy na CALE demo — wszystkie zapisy zamkniete tutaj.
# Layout:
#   $TMP/workspace/        <- dozwolona przestrzen robocza agenta (korzen jaila)
#   $TMP/poza_workspace/   <- "poza piaskownica" agenta, ale wciaz w $TMP (bezpieczne)
TMP=""
cleanup() { [[ -n "$TMP" && -d "$TMP" ]] && rm -rf "$TMP" || true; }
trap cleanup INT TERM EXIT
TMP="$(mktemp -d "${TMPDIR:-/tmp}/demo10.XXXXXX")"
WS="$TMP/workspace"
ESCAPE="$TMP/poza_workspace/skradzione.txt"

# ── Artefakty inline: kod agenta, jail, czerwony test ─────────────────────────

# (A) Podatny kod, ktory "agent wygenerowal": SQL przez konkatenacje + proba
# zapisu POZA workspace. $1 = korzen workspace, $2 = sciezka-ucieczka.
write_agent_code() {  # write_agent_code <ws_root> <escape_path>
  cat > "$WS/agent_payload.py" <<PY
import sqlite3, sys

WS_ROOT = sys.argv[1]
ESCAPE  = sys.argv[2]

# (1) PODATNOSC: zapytanie SQL sklejane z wejscia uzytkownika (SQL injection).
def lookup_user(con, user_id):
    # ZLE: konkatenacja zamiast parametru zwiazanego (?).
    q = "SELECT * FROM users WHERE id = '" + user_id + "'"
    return con.execute(q)

# (2) UCIECZKA: agent probuje zapisac plik POZA swoja przestrzenia robocza.
with open(ESCAPE, "w", encoding="utf-8") as f:
    f.write("dane wyniesione poza workspace przez agenta\n")
print("UCIECZKA: zapisano", ESCAPE)
PY
}

# (B-a) Workspace jail jako prawdziwy plik .py w workspace (widoczny dla widowni).
# Pozwala na zapis TYLKO pod korzeniem WS, odmawia reszty.
# exit 0 = DOZWOLONE, exit 1 = ODMOWA. argv: <ws_root> <target_path>.
write_jail() {  # write_jail <plik>
  cat > "$1" <<'PY'
import os, sys
ws_root = os.path.realpath(sys.argv[1])
target  = os.path.realpath(sys.argv[2])
# Dozwolone tylko, gdy cel lezy WEWNATRZ korzenia workspace.
# realpath() rozwija '..' i dowiazania, wiec proba ucieczki jest wykrywana.
inside = target == ws_root or target.startswith(ws_root + os.sep)
if inside:
    print("JAIL: DOZWOLONE ->", target)
    sys.exit(0)
print("JAIL: ODMOWA (poza workspace) ->", target)
sys.exit(1)
PY
}
# Wygoda: wywolanie jaila przez funkcje (smoke).
jail_check() {  # jail_check <ws_root> <target_path>
  python3 "$WS/jail.py" "$1" "$2"
}

# (B-b) Czerwony test TDD jako prawdziwy plik .py: OBLEWA, gdy snippet sklada SQL
# przez konkatenacje; PRZECHODZI, gdy uzywa parametru zwiazanego (?).
# exit 1 = RED (oblany), exit 0 = GREEN. argv: <plik_z_kodem>.
write_red_test() {  # write_red_test <plik>
  cat > "$1" <<'PY'
import re, sys
src = open(sys.argv[1], encoding="utf-8").read()
# Heurystyka bramki: SELECT/INSERT/UPDATE/DELETE sklejany operatorem '+' = podatne.
bad = re.search(r'(SELECT|INSERT|UPDATE|DELETE)[^"\n]*"\s*\+', src, re.I)
if bad:
    print("RED: test OBLEWA — SQL sklejany przez konkatenacje (wstrzykniecie).")
    sys.exit(1)
print("GREEN: test przechodzi — brak sklejanego SQL (parametry zwiazane).")
sys.exit(0)
PY
}
# Wygoda: uruchom czerwony test na pliku z kodem (smoke).
red_test() {  # red_test <plik_z_kodem>
  python3 "$WS/red_test.py" "$1"
}

# Naprawiony snippet (parametr zwiazany) — pokazuje, ze test przeszedlby na poprawnym kodzie.
write_fixed_code() {  # write_fixed_code <plik>
  cat > "$1" <<'PY'
import sqlite3
def lookup_user(con, user_id):
    return con.execute("SELECT * FROM users WHERE id = ?", (user_id,))
PY
}

# --check: tylko weryfikacja, bez prowadzenia demo
if [[ "$CHECK" == 1 ]]; then
  say "Demo 9 OK: python3 obecny ($(python3 --version 2>&1))."
  exit 0
fi

# ── smoke: NIE-interaktywnie, sprawdz dwie bramki ────────────────────────────
if [[ "$SMOKE" == 1 ]]; then
  mkdir -p "$WS" "$(dirname "$ESCAPE")"
  write_agent_code "$WS" "$ESCAPE"
  write_jail "$WS/jail.py"
  write_red_test "$WS/red_test.py"

  # 1a) jail ODMAWIA sciezki-ucieczki -> exit 1
  set +e; jail_check "$WS" "$ESCAPE" >/dev/null 2>&1; rc_escape=$?; set -e
  # 1b) jail POZWALA na sciezke w workspace -> exit 0
  set +e; jail_check "$WS" "$WS/raport.txt" >/dev/null 2>&1; rc_inside=$?; set -e
  # 2a) czerwony test OBLEWA na podatnym kodzie -> exit 1
  set +e; red_test "$WS/agent_payload.py" >/dev/null 2>&1; rc_red=$?; set -e
  # 2b) czerwony test PRZESZEDLBY na naprawionym kodzie -> exit 0
  write_fixed_code "$WS/agent_fixed.py"
  set +e; red_test "$WS/agent_fixed.py" >/dev/null 2>&1; rc_green=$?; set -e

  if [[ "$rc_escape" == 1 && "$rc_inside" == 0 && "$rc_red" == 1 && "$rc_green" == 0 ]]; then
    say "SMOKE: jail ODMAWIA ucieczki (1) i POZWALA w workspace (0); czerwony test OBLEWA na podatnym (1) i przeszedlby na naprawionym (0) OK."
    exit 0
  fi
  warn "SMOKE FAIL: jail ucieczka=$rc_escape (oczekiwano 1), jail workspace=$rc_inside (0), red podatny=$rc_red (1), red naprawiony=$rc_green (0)."
  exit 1
fi

# ── suflerka (kroki w terminalu) ────────────────────────────────────────────
set +e  # od teraz nie przerywaj na bledzie pojedynczej komendy
demo_header "Demo 9 — nieoczekiwane wykonanie kodu / ucieczka z piaskownicy" "slide:m2-t5-demo"
say "Piaskownica demo (wszystko dzieje sie TYLKO tutaj): $TMP"
say "Layout: $WS  (dozwolona przestrzen robocza)  oraz  $(dirname "$ESCAPE")  (poza nia, ale wciaz w piaskownicy)."
say "Pokazemy dwa swiaty: (A) agent bez izolacji i (B) ten sam agent za workspace jailem + czerwonym testem TDD."
pause

step "Czesc A — zagrozenie: agent pisze podatny kod i ucieka z workspace"
say "Tworze przestrzen robocza agenta i 'kosz' poza nia (oba w piaskownicy):"
runc "mkdir -p \"$WS\" \"$(dirname "$ESCAPE")\" && ls -la \"$TMP\""
say "Agent dostaje zadanie i GENERUJE kod. Zobaczmy, co wyprodukowal:"
write_agent_code "$WS" "$ESCAPE"
runc "cat \"$WS/agent_payload.py\""
note "Dwa problemy naraz: (1) SQL sklejany przez konkatenacje = wstrzykniecie; (2) open() na sciezce POZA workspace."
say "Bez izolacji agent po prostu URUCHAMIA swoj kod — i zapis poza workspace SIE UDAJE:"
runc "python3 \"$WS/agent_payload.py\" \"$WS\" \"$ESCAPE\""
say "Sprawdzmy, czy plik faktycznie wyladowal POZA przestrzenia robocza:"
runc "ls -la \"$(dirname "$ESCAPE")\" && echo '--- tresc ---' && cat \"$ESCAPE\""
note "To bylo bezpieczne: 'poza workspace' to wciaz katalog w piaskownicy $TMP — nic realnego nie tkniete."
say "Puenta czesci A: 'bez izolacji proces agenta moze pisac gdzie chce i wykonac podatny kod — to ucieczka z piaskownicy.'"
pause

step "Czesc B — dobra praktyka: workspace jail + czerwony test TDD"
say "Pieć warstw piaskownicy agenta: FS (gdzie moze pisac), Siec, Proces, Narzedzia/MCP, Tozsamosc."
say "Tu pokazujemy dwie z nich namacalnie: warstwe FS (jail na zapisach) i bramke TDD (czerwony test)."
pause

step "Warstwa FS — workspace jail odmawia ucieczki"
say "Maly straznik (plik jail.py): zapis dozwolony TYLKO pod korzeniem workspace."
write_jail "$WS/jail.py"
runc "cat \"$WS/jail.py\""
say "Najpierw cel-ucieczka (poza workspace) — jail ma ODMOWIC (exit 1):"
runc "python3 \"$WS/jail.py\" \"$WS\" \"$ESCAPE\"; echo \"exit=\$?\""
say "Teraz cel w obrebie workspace — jail ma POZWOLIC (exit 0):"
runc "python3 \"$WS/jail.py\" \"$WS\" \"$WS/raport.txt\"; echo \"exit=\$?\""
note "Jail filtruje po realpath() — odporne na '..' i dowiazania. Ucieczka anulowana ZANIM dojdzie do zapisu."
pause

step "Bramka TDD — czerwony test oblewa na podatnym kodzie"
say "Minimalny czerwony test (Kent Beck: red-green-refactor) sprawdza kod agenta PRZED dopuszczeniem zmiany."
write_red_test "$WS/red_test.py"
runc "cat \"$WS/red_test.py\""
say "Na podatnym snippetcie (SQL sklejany przez '+') test ma OBLAC (exit 1):"
runc "python3 \"$WS/red_test.py\" \"$WS/agent_payload.py\"; echo \"exit=\$?\""
say "Na naprawionym kodzie (parametr zwiazany '?') ten sam test PRZESZEDLBY (exit 0):"
write_fixed_code "$WS/agent_fixed.py"
runc "cat \"$WS/agent_fixed.py\""
runc "python3 \"$WS/red_test.py\" \"$WS/agent_fixed.py\"; echo \"exit=\$?\""
note "Czerwony test = audytowalna bramka: dopoki oblewa, zmiana jest ZABLOKOWANA (nie laczymy podatnego kodu)."
pause

step "Debrief (puenta bezpieczenstwa, 15 s)"
say "Ten sam agent, ten sam wygenerowany kod — roznica to warstwy: jail FS odmawia ucieczki, czerwony test blokuje podatnosc."
note "Piaskownica = FS + Siec + Proces + Narzedzia/MCP + Tozsamosc; TDD (Kent Beck) to audytowalna bramka PRZED merge'em."
say "'Nie pytamy, czy agent napisze bezpieczny kod. Zamykamy mu przestrzen i stawiamy czerwony test, zanim cokolwiek sie wykona.'"
pause

step "Reset po demo"
say "Piaskownica $TMP zniknie automatycznie (trap cleanup). Nic poza nia nie zostalo dotkniete."

bye "Demo 9 zakonczone."
