#!/usr/bin/env bash
# Wspólna suflerka dem — sourcowana przez demos/demo-N.sh.
# Drukuje kolejne kroki w terminalu, pauzuje na Enter, pokazuje/uruchamia komendy.
# Czyta wejście z /dev/tty, więc działa nawet gdy stdout jest przekierowany.

# kolory tylko w terminalu interaktywnym
if [[ -t 1 ]]; then
  _c_step=$'\033[1;38;5;208m'; _c_say=$'\033[0;36m'; _c_cmd=$'\033[1;37m'
  _c_warn=$'\033[1;33m'; _c_dim=$'\033[2m'; _c_off=$'\033[0m'
else
  _c_step=""; _c_say=""; _c_cmd=""; _c_warn=""; _c_dim=""; _c_off=""
fi

_DEMO_STEP=0

# Nagłówek dema (tytuł + slajd).
demo_header() {  # demo_header "Demo 1 — ..." "slide:m1-s02-demo"
  printf '\n%s════════════════════════════════════════════════════%s\n' "$_c_step" "$_c_off"
  printf '%s %s%s\n' "$_c_step" "$1" "$_c_off"
  [[ $# -ge 2 ]] && printf '%s slajd: %s%s\n' "$_c_dim" "$2" "$_c_off"
  printf '%s════════════════════════════════════════════════════%s\n' "$_c_step" "$_c_off"
}

step() {  # numerowany nagłówek kroku
  _DEMO_STEP=$((_DEMO_STEP + 1))
  printf '\n%s━━ Krok %d ── %s%s\n' "$_c_step" "$_DEMO_STEP" "$*" "$_c_off"
}

say()  { printf '%s%s%s\n' "$_c_say" "$*" "$_c_off"; }
note() { printf '%s· %s%s\n'  "$_c_dim"  "$*" "$_c_off"; }
warn() { printf '%s! %s%s\n'  "$_c_warn" "$*" "$_c_off" >&2; }

pause() {  # czeka na Enter; jeśli tuż przed był paste_block — oferuje [c] kopiuj do schowka
  if [[ -n "${_LAST_BLOCK:-}" && -t 1 && -r /dev/tty ]]; then
    printf '%s▸ %s[c]%s schowek · %s[Enter]%s dalej… ' "$_c_dim" "$_c_cmd" "$_c_off" "$_c_dim" "$_c_off"
    local a; read -r a </dev/tty || a=""
    [[ "$a" == "c" ]] && { copy_clip "$_LAST_BLOCK"; note "skopiowano — wklej w Terminalu A (Cmd/Ctrl+V)"; }
    _LAST_BLOCK=""
    printf '\r\033[K'
    return 0
  fi
  printf '%s▸ Enter, aby kontynuować…%s' "$_c_dim" "$_c_off"
  read -r _ </dev/tty || true
  printf '\r\033[K'
}

# Blok do skopiowania (prompt do Terminala A) — treść z heredoc na stdin.
# Treść jest zapamiętywana w _LAST_BLOCK, więc kolejne `pause` oferuje skopiowanie do schowka (OSC 52).
paste_block() {
  local content; content="$(cat)"
  printf '%s┌─ skopiuj do Terminala A (Claude Code) ────────────%s\n' "$_c_dim" "$_c_off"
  printf '%s' "$content" | sed 's/^/  /'; printf '\n'
  printf '%s└───────────────────────────────────────────────────%s\n' "$_c_dim" "$_c_off"
  _LAST_BLOCK="$content"
}

show() {  # pokaż komendę bez uruchamiania
  printf '  %s$ %s%s\n' "$_c_cmd" "$*" "$_c_off"
}

runc() {  # pokaż i (po Enterze) uruchom komendę; 's' = pomiń
  printf '  %s$ %s%s   %s[Enter=uruchom · s=pomiń]%s ' \
    "$_c_cmd" "$*" "$_c_off" "$_c_dim" "$_c_off"
  local a; read -r a </dev/tty || a=""
  [[ "$a" == "s" ]] && { note "pominięto"; return 0; }
  eval "$*"
}

# Uruchom Claude Code INTERAKTYWNIE z promptem JUŻ WYSŁANYM (seed) — zero przeklejania.
# Prompt z heredoc (stdin); ewentualne flagi (np. --permission-mode plan / acceptEdits)
# jako argumenty po <dir>. Sesja przejmuje terminal aż do wyjścia (Ctrl+D); człowiek
# nadal steruje interakcją (plan mode, grill-me, podgląd) — automatyzujemy tylko wpisanie
# promptu, nie samą lekcję. Enter = uruchom · s = pomiń (prompt trafia do _LAST_BLOCK,
# więc kolejne `pause` zaoferuje [c] = kopiuj do schowka jako fallback ręczny).
claude_seed() {  # claude_seed <katalog-roboczy> [flagi-claude…]   (prompt na stdin, np. z heredoc)
  local dir="$1"; shift
  local prompt a; prompt="$(cat)"
  printf '%s┌─ Claude Code otworzy się INTERAKTYWNIE (prompt już wysłany) ─%s\n' "$_c_dim" "$_c_off"
  printf '%s' "$prompt" | sed 's/^/  /'; printf '\n'
  local shown; shown="$(printf '%s' "$prompt" | tr '\n' ' ' | sed 's/  */ /g')"
  printf '  %s$ claude %s "%s"%s   %s[Enter=uruchom · s=pomiń]%s ' \
    "$_c_cmd" "$*" "$shown" "$_c_off" "$_c_dim" "$_c_off"
  read -r a </dev/tty || a=""
  if [[ "$a" == "s" ]]; then
    _LAST_BLOCK="$prompt"; note "pominięto — wklej prompt ręcznie do Claude Code (pause: [c] = schowek)"
    return 0
  fi
  if ! command -v claude >/dev/null 2>&1; then
    _LAST_BLOCK="$prompt"; warn "brak 'claude' — najpierw bash demos/demo-00.sh (claude_login). Wklej prompt ręcznie."
    return 0
  fi
  # Heredoc zajął stdin funkcji → wejście sesji bierzemy z /dev/tty; flagi przed promptem pozycyjnym (seed).
  ( cd "$dir" && claude "$@" "$prompt" </dev/tty )
}

# Komenda wymagająca sudo/uprawnień — NIE uruchamiamy jej w skrypcie; pokazujemy
# do skopiowania w DRUGIM terminalu (z sudo). Każdy argument = osobna linia.
sudo_block() {  # sudo_block "<komenda>" ["<komenda2>" ...]
  printf '%s↪ skopiuj do DRUGIEGO terminala (wymaga sudo):%s\n' "$_c_warn" "$_c_off"
  local line
  for line in "$@"; do printf '  %s$ %s%s\n' "$_c_cmd" "$line" "$_c_off"; done
}

# Miękki check obecności komendy (nie przerywa dema, gdy brak).
need() {  # need <komenda> [etykieta]
  if command -v "$1" >/dev/null 2>&1; then
    note "✓ $1 — $($1 --version 2>/dev/null | head -1 || echo obecne)"
  else
    warn "brak: $1 ${2:+($2)}"
  fi
}

bye() { printf '\n%s✓ %s%s\n' "$_c_step" "$*" "$_c_off"; }

# ── Przenośność: lokalizacja mini-bank, twarde zależności, dostęp, reset ──────

# Znajdź katalog mini-bank (foldery demos/ i mini-bank/ jako rodzeństwo).
# Kolejność: $MINIBANK_DIR -> obok demos/ -> $REPO_ROOT/mini-bank.
find_minibank() {
  local here repo c
  here="${HERE:-$(cd "$(dirname "${BASH_SOURCE[1]:-$0}")" && pwd)}"
  repo="${REPO_ROOT:-$(cd "$here/.." && pwd)}"
  for c in "${MINIBANK_DIR:-}" "$here/../mini-bank" "$repo/mini-bank"; do
    [[ -n "$c" && -d "$c" ]] && { (cd "$c" && pwd); return 0; }
  done
  warn "Nie znaleziono katalogu mini-bank."
  warn "  Foldery 'demos/' i 'mini-bank/' muszą leżeć obok siebie (rodzeństwo),"
  warn "  albo wskaż ścieżkę: MINIBANK_DIR=/sciezka/do/mini-bank bash $0"
  exit 1
}

# Twardy check zależności. Brak -> komenda instalacji + odesłanie do demo-00 + exit 1.
require() {  # require <komenda> [podpowiedz-instalacji]
  command -v "$1" >/dev/null 2>&1 && return 0
  warn "Brak wymaganej komendy: $1"
  [[ -n "${2:-}" ]] && sudo_block "$2"
  note "Najpierw przygotuj środowisko:  bash demos/demo-00.sh"
  exit 1
}

# Czy mamy graficzną przeglądarkę (GUI), czy headless (VM przez SSH)?
_has_gui() {
  [[ -n "${DISPLAY:-}" || "$(uname -s)" == "Darwin" ]] \
    && { command -v xdg-open >/dev/null 2>&1 || command -v open >/dev/null 2>&1; }
}

# Pokaż dostęp do aplikacji: GUI -> otwórz lokalnie; headless -> instrukcja tunelu SSH.
show_access() {  # show_access <url> <port>
  local url="$1" port="$2"
  if _has_gui; then
    if command -v xdg-open >/dev/null 2>&1; then xdg-open "$url" >/dev/null 2>&1 &
    elif command -v open >/dev/null 2>&1; then open "$url" >/dev/null 2>&1 & fi
    say "Otwieram w przeglądarce: $url"
    return 0
  fi
  # headless: zbuduj podpowiedź tunelu na podstawie sesji SSH
  local user host
  user="$(whoami)"
  host="$(printf '%s' "${SSH_CONNECTION:-}" | awk '{print $3}')"
  [[ -z "$host" ]] && host="<adres-VM>"
  warn "Brak przeglądarki na VM (headless) — użyj tunelu SSH z LOKALNEJ maszyny:"
  paste_block <<EOF
ssh -L $port:127.0.0.1:$port $user@$host
# a potem otwórz w LOKALNEJ przeglądarce:
$url
EOF
}

# Zagwarantuj, że <dir> to repo gita z czystym baseline (żeby reset działał wszędzie).
ensure_git_baseline() {  # ensure_git_baseline <dir>
  local dir="$1"
  git -C "$dir" rev-parse --is-inside-work-tree >/dev/null 2>&1 && return 0
  say "Inicjuję baseline gita w $dir (potrzebne do resetu po demie)..."
  if [[ ! -f "$dir/.gitignore" ]]; then
    cat > "$dir/.gitignore" <<'GI'
__pycache__/
*.pyc
*.egg-info/
.pytest_cache/
*.db
*.db-journal
node_modules/
dist/
.env
.venv/
.coverage
GI
  fi
  git -C "$dir" init -q
  git -C "$dir" add -A
  git -C "$dir" -c user.email=demo@local -c user.name=demo commit -q -m "baseline demo" || true
}

# Reset mini-bank do baseline: cofnij zmiany śledzone + usuń nowe pliki (respektuje .gitignore).
reset_minibank() {  # reset_minibank <dir>
  local dir="$1"
  git -C "$dir" restore . 2>/dev/null || git -C "$dir" checkout -- . 2>/dev/null || true
  git -C "$dir" clean -fd >/dev/null 2>&1 || true
  git -C "$dir" status --short
}

# Snapshot pojedynczego pliku (reset bez polegania na gicie).
backup_file()  { [[ -f "$1" && ! -f "$1.demo-bak" ]] && cp "$1" "$1.demo-bak" || true; }
restore_file() { [[ -f "$1.demo-bak" ]] && { mv -f "$1.demo-bak" "$1"; } || true; }

# ── Stawianie mini-bank (wspólne dla demo-00 build+smoke i demo-02 serwowania) ──

# Pierwszy WOLNY port — chroni przed cichą kolizją (np. stary Docker).
pick_free_port() {
  local p
  for p in 8000 8001 8002 8003 8080 8088; do
    if python3 - "$p" >/dev/null 2>&1 <<'PY'
import socket, sys
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.bind(("127.0.0.1", int(sys.argv[1]))); s.close()
except OSError:
    sys.exit(1)
PY
    then printf '%s' "$p"; return 0; fi
  done
  return 1
}

# Buduje mini-bank idempotentnie: venv + pip -e backend, build frontendu, seed DB.
# Honoruje globalne REBUILD=1 (przebuduj front) i FRESH=1 (przeseeduj DB), jeśli ustawione.
build_minibank() {  # build_minibank <mini-bank-dir>
  local mb="$1" be fe venv py db
  be="$mb/backend"; fe="$mb/frontend"; venv="$be/.venv"; py="$venv/bin/python"; db="$be/minibank.db"
  if [[ ! -d "$venv" ]]; then say "Tworzę venv backendu..."; python3 -m venv "$venv"; fi
  # extra [dev] = pytest (+pytest-asyncio, ruff). Guard sprawdza też pytest, więc
  # istniejący venv bez pytest też go doinstaluje (idempotentnie).
  if ! "$py" -c "import minibank, pytest" >/dev/null 2>&1; then
    say "Instaluję zależności backendu (pip install -e .[dev] — z pytest)..."
    "$venv/bin/pip" install -q --upgrade pip
    "$venv/bin/pip" install -q -e "${be}[dev]"
  fi
  # Frontend: zależności Z devDependencies (tsc, vite). Bramka na binarce .bin/tsc
  # (łapie niepełny node_modules); --include=dev wymusza devDeps nawet przy NODE_ENV=production.
  if [[ "${REBUILD:-0}" == 1 || ! -x "$fe/node_modules/.bin/tsc" || ! -x "$fe/node_modules/.bin/vite" ]]; then
    say "Instaluję zależności frontendu (npm ci --include=dev)..."
    ( cd "$fe" && { npm ci --include=dev || npm install --include=dev; } )
  fi
  if [[ "${REBUILD:-0}" == 1 || ! -f "$fe/dist/index.html" ]]; then
    say "Buduję frontend (npm run build)..."; ( cd "$fe" && npm run build )
    [[ -f "$fe/dist/index.html" ]] || warn "Build frontu nie wytworzył dist/index.html — sprawdź log npm wyżej."
  fi
  if [[ "${FRESH:-0}" == 1 ]]; then rm -f "$db"; fi
  if [[ ! -f "$db" ]]; then
    say "Seeduję bazę SQLite (40 klientów, 3 agentów)..."
    ( cd "$be" && "$py" -m minibank.db.seed )
  fi
}

# Python z venv mini-banku (po build_minibank ma deps + pytest). Fallback: python3.
mb_python() {  # mb_python <mini-bank-dir>
  local p="$1/backend/.venv/bin/python"
  [[ -x "$p" ]] && printf '%s' "$p" || printf 'python3'
}

# Czeka aż serwer odpowie na /healthz (max ~30 s). Opcjonalny <pid> — przerwij, gdy padł.
# Zwraca 0 = zdrowy, 1 = nie wstał.
wait_health() {  # wait_health <url> [server-pid]
  local url="$1" pid="${2:-}" i
  for i in $(seq 1 60); do
    curl -fsS "$url/healthz" >/dev/null 2>&1 && return 0
    [[ -n "$pid" ]] && { kill -0 "$pid" 2>/dev/null || return 1; }
    sleep 0.5
  done
  curl -fsS "$url/healthz" >/dev/null 2>&1
}

# ── Blok „WŁASNE TEMPO" (drukowany na końcu każdego demo-05..15.sh) ────────────
# Każdy uczestnik dokańcza ćwiczenie sam, po części live. Sekcja zawiera: issue,
# kryteria akceptacji, jednolite komendy git+PR, schodkowe podpowiedzi, stretch,
# odsyłacz do wzorca. Helpery, by 10 skryptów nie duplikowało tekstu.

sp_banner() {  # sp_banner [etykieta] — otwiera sekcję (domyślnie: dokończ w swoim tempie)
  local label="${1:-Dokończ ćwiczenie w swoim tempie}"
  printf '\n%s┏━━ %s ━━━━━━━━━━━%s\n' "$_c_step" "$label" "$_c_off"
}
sp_end() { printf '%s┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━%s\n\n' "$_c_step" "$_c_off"; }

sp() {  # sp <etykieta> <treść...> — wiersz z wyróżnioną etykietą wewnątrz ramki
  local label="$1"; shift
  printf '%s┃%s %s%s:%s %s\n' "$_c_step" "$_c_off" "$_c_say" "$label" "$_c_off" "$*"
}
spl() { printf '%s┃%s   %s\n' "$_c_step" "$_c_off" "$*"; }  # wcięty wiersz w ramce

# Kryteria akceptacji jako checklista.
accept() {  # accept "punkt 1" "punkt 2" ...
  sp "Akceptacja (definition of done)"
  local p; for p in "$@"; do printf '%s┃%s   ☐ %s\n' "$_c_step" "$_c_off" "$p"; done
}

# Schodkowe podpowiedzi: od nakierowania (1) do prawie-rozwiązania (ostatnia).
hints() {  # hints "poziom1" "poziom2" ["poziom3"]
  sp "Podpowiedzi (odsłaniaj po kolei, dopiero gdy utkniesz)"
  local i=1 h
  for h in "$@"; do printf '%s┃%s   %s%d.%s %s\n' "$_c_step" "$_c_off" "$_c_dim" "$i" "$_c_off" "$h"; i=$((i+1)); done
}

stretch() {  # stretch "co dalej, gdy skończysz wcześniej"
  sp "Idź dalej (gdy skończysz przed czasem)" "$*"
}

# Odsyłacz do wzorca — zawsze z notką „po własnej próbie".
solution_ref() {  # solution_ref "<gdzie>"
  sp "Wzorzec" "$* — zajrzyj DOPIERO po własnej próbie."
}

# Jednolity workflow git + PR GitHub (ten sam w każdym demie; PR-y są prawdziwe,
# gh skonfigurowany w demo-00 na prywatne repo 'mini-bank-warsztat').
pr_steps() {  # pr_steps <branch> <commit-subject> [issue-search-tag]
  local br="$1" subj="$2" tag="${3:-}"
  sp "git + PR (uruchom w katalogu mini-bank; gh skonfigurowany w demo-00 na repo mini-bank-warsztat)"
  [[ -n "$tag" ]] && show "gh issue list --search '$tag'     # numer Twojego issue (N) — w świeżym repo issues numerowane od 1"
  show "git switch -c $br"
  spl "# … praca w Claude Code techniką tego demo …"
  show "git add -A && git commit -m \"$subj\""
  spl "# commit prowadź skillem 'polish-bank-commit-msg' (Conventional Commits; money-math → linia Audit-Log)"
  show "git push -u origin $br"
  if [[ -n "$tag" ]]; then
    show "gh pr create --fill --base main --body 'Closes #N'    # N = numer issue z listy wyżej"
  else
    show "gh pr create --fill --base main"
  fi
  spl "# w Claude Code:  /code-review   — przejrzyj własną zmianę PRZED mergem"
  show "gh pr checks --watch && gh pr merge --squash --delete-branch   # dopiero po zielonym CI"
}

# ── UI ścieżki M4: schowek (OSC 52), pasek postępu, dwa terminale, stan ────────
# Wszystkie funkcje są bezpieczne w trybie nie-TTY (--smoke): interaktywne fragmenty
# są strzeżone przez [[ -t 1 && -r /dev/tty ]], więc smoke leci bez blokady.

# Kopiuj tekst do schowka LOKALNEJ maszyny przez OSC 52 — działa przez SSH,
# więc prompt z headless VM ląduje w schowku laptopa (wklejasz w Terminalu A: Cmd/Ctrl+V).
copy_clip() {  # copy_clip "<tekst>"
  local b64; b64="$(printf '%s' "$1" | base64 | tr -d '\n')"
  printf '\033]52;c;%s\007' "$b64" > /dev/tty 2>/dev/null || true
}

# Pasek postępu ścieżki: progress <n> <total> <tytuł…>
progress() {  # progress 3 10 "TDD na bugu odsetek"
  local n="$1" total="$2"; shift 2
  local bar="" i
  for ((i=1; i<=total; i++)); do [[ $i -le $n ]] && bar+="▰" || bar+="▱"; done
  printf '\n%s━━ Ćwiczenie %d/%d  %s  %s ━━%s\n' "$_c_step" "$n" "$total" "$bar" "$*" "$_c_off"
}

# Przypomnienie układu dwóch terminali (A: Claude Code, B: suflerka demo).
two_terminals_banner() {
  printf '%s┌─ dwa terminale w VM ──────────────────────────────%s\n' "$_c_dim" "$_c_off"
  printf '%s│%s  %sA%s  cd mini-bank && claude           %swklejasz tu prompty / komendy agenta%s\n' \
    "$_c_dim" "$_c_off" "$_c_cmd" "$_c_off" "$_c_dim" "$_c_off"
  printf '%s│%s  %sB%s  bash demos/demo-NN.sh (suflerka) %spodaje kroki krok po kroku%s\n' \
    "$_c_dim" "$_c_off" "$_c_cmd" "$_c_off" "$_c_dim" "$_c_off"
  printf '%s└───────────────────────────────────────────────────%s\n' "$_c_dim" "$_c_off"
}

# Stan ścieżki: które ćwiczenia ukończone (zasila pasek postępu).
_LAB_STATE="${MBANK_LAB_STATE:-$HOME/.mbank-lab-progress}"
mark_done() {  # mark_done <NN>
  local nn="${1:-}"; [[ -z "$nn" ]] && return 0
  touch "$_LAB_STATE" 2>/dev/null || return 0
  grep -qx "$nn" "$_LAB_STATE" 2>/dev/null || printf '%s\n' "$nn" >> "$_LAB_STATE"
}
is_done() { [[ -f "$_LAB_STATE" ]] && grep -qx "${1:-}" "$_LAB_STATE" 2>/dev/null; }

# Stopka dema: wskaż następne ćwiczenie ścieżki (+ skrót do schowka). Pusty arg = koniec ścieżki.
next_demo() {  # next_demo <NN>
  local nn="${1:-}"
  if [[ -z "$nn" ]]; then
    printf '%s▸ To ostatnie ćwiczenie ścieżki. Debrief:%s %sbash demos/m4-debrief.sh%s\n' \
      "$_c_step" "$_c_off" "$_c_cmd" "$_c_off"; return 0
  fi
  local cmd="bash demos/demo-$nn.sh"
  printf '%s▸ Następne ćwiczenie:%s %s%s%s\n' "$_c_step" "$_c_off" "$_c_cmd" "$cmd" "$_c_off"
  if [[ -t 1 && -r /dev/tty ]]; then
    printf '  %s[c]%s skopiuj komendę · %s[Enter]%s zakończ ' "$_c_cmd" "$_c_off" "$_c_dim" "$_c_off"
    local a; read -r a </dev/tty || a=""
    [[ "$a" == "c" ]] && { copy_clip "$cmd"; note "skopiowano"; }
    printf '\r\033[K'
  fi
}
