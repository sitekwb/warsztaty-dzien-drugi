#!/usr/bin/env bash
# Demo 2 — dekompozycja celu w Claude Code (plan mode /plan).
# Stawia mini-bank NATYWNIE (venv + zbudowany SPA + uvicorn), sam wstrzykuje bug
# logowania (bez zaleznosci od galezi gita), pokazuje dostep (tunel SSH na golej VM)
# i prowadzi przez kolejne kroki w terminalu.
# Slajd: slide:m1-s07-demo.
# Uzycie:
#   bash demos/demo-02.sh            # postaw, pokaz dostep, prowadz demo
#   bash demos/demo-02.sh --fresh    # + przeseeduj baze SQLite
#   bash demos/demo-02.sh --rebuild  # + przebuduj frontend
#   bash demos/demo-02.sh --no-open  # nie pokazuj dostepu/tunelu
#   bash demos/demo-02.sh --smoke    # self-test: sprawdz ze login=401, zglos i wyjdz
#   bash demos/demo-02.sh --check    # tylko weryfikacja zaleznosci + mini-bank
#   bash demos/demo-02.sh --help
set -euo pipefail

FRESH=0; REBUILD=0; NO_OPEN=0; SMOKE=0; CHECK=0
for arg in "$@"; do
  case "$arg" in
    --fresh)   FRESH=1 ;;
    --rebuild) REBUILD=1 ;;
    --no-open) NO_OPEN=1 ;;
    --smoke)   SMOKE=1; NO_OPEN=1 ;;
    --check)   CHECK=1 ;;
    -h|--help) sed -n '2,14p' "$0"; exit 0 ;;
    *) echo "Nieznana flaga: $arg (uzyj --help)" >&2; exit 2 ;;
  esac
done

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$HERE/.." && pwd)"
# shellcheck source=demos/_demo_lib.sh
source "$HERE/_demo_lib.sh"

# twarde zaleznosci (brak -> komenda + odeslanie do demo-00)
require python3 "sudo apt-get install -y python3 python3-venv python3-pip"
require node    "curl -fsSL https://deb.nodesource.com/setup_20.x | sudo bash - && sudo apt-get install -y nodejs"
require npm     "sudo apt-get install -y nodejs"
require curl    "sudo apt-get install -y curl"

# Python >= 3.12 (mini-bank pyproject)
if ! python3 - <<'PY' >/dev/null 2>&1
import sys; sys.exit(0 if sys.version_info[:2] >= (3,12) else 1)
PY
then
  warn "python3 < 3.12 ($(python3 -V 2>&1 | awk '{print $2}')) — mini-bank wymaga >= 3.12."
  note "Zainstaluj Python 3.12:  bash demos/demo-00.sh"
  exit 1
fi

HOST=127.0.0.1
MB="$(find_minibank)"
BE="$MB/backend"
FE="$MB/frontend"
VENV="$BE/.venv"
PY="$VENV/bin/python"
DB="$BE/minibank.db"
AUTH="$BE/src/minibank/services/auth_service.py"

# pick_free_port(), build_minibank(), wait_health() — wspólne w demos/_demo_lib.sh

# --check: tylko weryfikacja, bez stawiania serwera
if [[ "$CHECK" == 1 ]]; then
  [[ -f "$AUTH" ]] || { warn "Nie znaleziono $AUTH"; exit 1; }
  say "Demo 2 OK: python3>=3.12, node, npm, curl obecne; mini-bank w $MB."
  exit 0
fi

# ── bootstrap ───────────────────────────────────────────────────────────────
# 1. wstrzyknij bug logowania LOKALNIE (bez zaleznosci od galezi gita)
require git "sudo apt-get install -y git"
ensure_git_baseline "$MB"
if grep -q 'if verify_password(password, user.password_hash):' "$AUTH" 2>/dev/null; then
  say "Bug juz w kodzie (logowanie zwroci 401) -- OK."
elif grep -q 'if not verify_password(password, user.password_hash):' "$AUTH" 2>/dev/null; then
  say "Wstrzykuje bug do kodu (logowanie zacznie zwracac 401)..."
  backup_file "$AUTH"
  sed -i.sedbak 's/if not verify_password(password, user.password_hash):/if verify_password(password, user.password_hash):/' "$AUTH"
  rm -f "$AUTH.sedbak"
else
  warn "Nie rozpoznano stanu uwierzytelniania -- kontynuuje (moze byc juz naprawione przez agenta)."
fi

# 2-4. build mini-bank: venv + pip -e backend, build frontendu, seed DB (wspólny launcher).
#      build_minibank honoruje globalne REBUILD=1 / FRESH=1 ustawione z flag wyżej.
build_minibank "$MB"

# 5. wolny port + URL
PORT="$(pick_free_port)" || { warn "Brak wolnego portu."; exit 1; }
[[ "$PORT" == "8000" ]] || warn "Port 8000 zajety -- uzywam :$PORT."
URL="http://$HOST:$PORT"

# 6. start serwera (API + SPA) w tle
say "Startuje serwer na $URL ..."
( cd "$BE" && exec env STATIC_DIR="$FE/dist" JWT_SECRET="demo-only-jwt-secret-change-me-0123456789" \
    "$VENV/bin/uvicorn" minibank.main:app \
    --host "$HOST" --port "$PORT" --reload --reload-dir src --log-level warning ) &
SRV_PID=$!
cleanup() {
  restore_file "$AUTH"   # cofnij wstrzyknięty bug przy KAŻDYM wyjściu (też --smoke / Ctrl+C)
  [[ -n "${SRV_PID:-}" ]] || return 0
  kill "$SRV_PID" >/dev/null 2>&1 || true
  pkill -P "$SRV_PID" >/dev/null 2>&1 || true
  wait "$SRV_PID" 2>/dev/null || true
}
trap cleanup INT TERM EXIT

# 7. czekaj na health (max ~30 s)
wait_health "$URL" "$SRV_PID" || { warn "Serwer nie wstal w 30 s."; exit 1; }
say "Serwer gotowy."

# 8a. smoke: sprawdz login i wyjdz
if [[ "$SMOKE" == 1 ]]; then
  good="$(curl -s -o /dev/null -w '%{http_code}' -X POST "$URL/api/auth/login" \
    -H 'Content-Type: application/json' -d '{"email":"customer1@minibank.pl","password":"Demo1234!"}')"
  bad="$(curl -s -o /dev/null -w '%{http_code}' -X POST "$URL/api/auth/login" \
    -H 'Content-Type: application/json' -d '{"email":"customer1@minibank.pl","password":"ZLE"}')"
  if [[ "$good" == "401" ]]; then
    say "SMOKE: poprawne haslo -> 401 (logowanie zepsute) OK."
    if [[ "$bad" == "200" ]]; then say "SMOKE: bledne haslo -> 200 (backdoor obecny -- puenta security) OK."
    else warn "SMOKE: bledne haslo -> $bad (spodziewano 200 dla zaszytego buga)."; fi
    exit 0
  fi
  warn "SMOKE FAIL: poprawne haslo -> $good (spodziewano 401)."; exit 1
fi

# 8b. pokaz dostep (GUI -> otworz; headless VM -> tunel SSH)
if [[ "$NO_OPEN" == 0 ]]; then
  show_access "$URL" "$PORT"
fi

# ── suflerka (kroki w terminalu) ────────────────────────────────────────────
set +e  # od teraz nie przerywaj na bledzie pojedynczej komendy
demo_header "Demo 2 — dekompozycja celu w Claude Code" "slide:m1-s07-demo"
say "mini-bank slucha na $URL (na VM). Dostep z lokalnej maszyny: patrz tunel SSH wyzej."
say "Po tunelu otwierasz lokalnie http://localhost:$PORT   (Ctrl+C konczy i sprzata serwer)"
say "Logowanie (wpisane na stronie): customer1@minibank.pl / Demo1234!"
pause

step "Logowanie nie dziala (~30 s)"
say "W przegladarce kliknij 'Zaloguj sie' -> czerwony komunikat 'Nieprawidlowy email lub haslo' (401)."
say "Haslo jest poprawne, a logowanie odrzucone -- niech agent rozlozy to na czynniki."
pause

step "Plan mode — sedno demo (briefing, potem seed)"
say "Za chwile Claude wystartuje w PLAN MODE z samym OBJAWEM (prompt juz wyslany, zero przeklejania). W plan mode agent TYLKO czyta i odpala read-only — nic nie edytuje. Tak wyglada dekompozycja celu:"
note "1. odtworz blad  2. zlokalizuj winowajce w uwierzytelnianiu  3. test, ktory teraz pada"
note "4. minimalna poprawka  5. uruchom testy  6. sprawdz w aplikacji"
say "Plan zbyt ogolny? Wybierz 'Keep planning' i doprecyzuj (np. 'najpierw test odtwarzajacy 401') — HITL dziala juz na poziomie planu, nie dopiero przy edycji."
say "Zatwierdzenie: 'Approve and review each edit manually' (rekomendowane, wzmacnia HITL). Po naprawie sprawdz logowanie w przegladarce, potem Ctrl+D — wrocisz tu po puente."
note "Prompt podaje tylko OBJAW — nie podpowiadamy agentowi rozwiazania ani pliku."
claude_seed "$MB" --permission-mode plan <<'EOF'
W mini-bank logowanie nie działa: klient customer1@minibank.pl z poprawnym hasłem
Demo1234! dostaje „Nieprawidłowy email lub hasło" (HTTP 401), choć dane są poprawne.
Znajdź przyczynę w backendzie (FastAPI), napraw uwierzytelnianie i dodaj test
regresyjny. Pracuj wyłącznie w tym katalogu (mini-bank).
EOF
note "Bez seeda w realu: Shift+Tab az status = plan mode, potem sam tekst."
say "Opcjonalny zielony test po wyjsciu z Claude:"
runc "cd '$BE' && PYTHONPATH=src $(mb_python "$MB") -m pytest -k auth -q"
pause

step "Puenta bezpieczenstwa (mocny debrief, 15 s)"
say "Ten sam bug akceptowal BLEDNE haslo (200 = backdoor). Po naprawie bledne haslo = 401:"
runc "curl -s -o /dev/null -w 'bledne haslo -> HTTP %{http_code}\\n' -X POST \"$URL/api/auth/login\" -H 'Content-Type: application/json' -d '{\"email\":\"customer1@minibank.pl\",\"password\":\"ZLE-HASLO\"}'"
say "'Jedno brakujace not to nie tylko zepsute logowanie — to dziura, przez ktora wchodzi kazdy.'"
pause

step "Reset po demo"
say "Cofnij bug + zmiany agenta (przywraca tez auth_service.py z backupu):"
restore_file "$AUTH"
runc "reset_minibank \"$MB\""

bye "Demo 2 zakonczone. Ctrl+C zamknie serwer."
say "Serwer dziala dalej na $URL — nacisnij Ctrl+C, gdy skonczysz."
wait "$SRV_PID"
