#!/usr/bin/env bash
# Demo 0 — przygotowanie środowiska na gołej Ubuntu VM (dostęp tylko przez SSH).
# Sudo-instalacje tylko DRUKUJE do skopiowania OBOK (sam nie używa sudo). Gdy
# narzędzia są gotowe, robi konfigurację jednorazową BEZ sudo: build+smoke
# mini-banku, gh CLI (token min.) i push mini-banku na prywatne repo.
# Użycie:
#   bash demos/demo-00.sh           # wykryj braki / dokończ konfigurację
#   bash demos/demo-00.sh --help
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=demos/_demo_lib.sh
source "$HERE/_demo_lib.sh"

# Przywróć bit wykonywalności wszystkim suflerkom (zip/scp potrafi go zgubić) —
# dzięki temu chmod +x robisz raz, tylko dla demo-00.sh.
chmod +x "$HERE"/demo-*.sh "$HERE"/m4-debrief.sh 2>/dev/null || true

case "${1:-}" in
  -h|--help) sed -n '2,8p' "$0"; exit 0 ;;
  --check)   : ;;   # alias — skrypt i tak tylko sprawdza
  "")        : ;;
  *) echo "Nieznana flaga: $1 (użyj --help)" >&2; exit 2 ;;
esac

# sudo tylko gdy nie-root; w kontenerze (root) ten sam blok działa bez sudo
SUDO=""; [[ "${EUID:-$(id -u)}" -ne 0 ]] && SUDO="sudo "

# Nazwa prywatnego repo, na które każdy uczestnik wypycha swojego mini-banku.
REPO_NAME="${MINIBANK_REPO_NAME:-mini-bank-warsztat}"

MISSING=0
TODO=""   # zbiorczy blok komend do skopiowania

# Wczytaj tokeny zapisane przez poprzedni run (source + jawne eksporty — omija
# interaktywną bramkę „if not interactive: return" na początku ~/.bashrc), żeby
# claude/gh działały dalej w tej samej sesji (build/push).
if [[ -f "$HOME/.bashrc" ]]; then
  set +u; source "$HOME/.bashrc" 2>/dev/null || true; set -u
  eval "$(grep -E '^[[:space:]]*export (CLAUDE_CODE_OAUTH_TOKEN|GH_TOKEN)=' "$HOME/.bashrc" 2>/dev/null || true)"
fi

add_todo() { TODO+="$1"$'\n'; }
ok()   { note "✓ $1"; }
miss() { warn "✗ $1 — brak"; MISSING=1; }

# Konfiguracja gh CLI najmniejszym przywilejem (token zawężony do JEDNEGO repo).
# Reużywalne w kolejnych demach (gh pr / issue / push). Część webowa = na laptopie.
gh_setup() {
  step "GitHub przez gh CLI (najmniejszy przywilej, reużywalne dalej)"
  if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
    note "✓ gh już zalogowany ($(gh api user -q .login 2>/dev/null || echo '?'))."
    return 0
  fi
  require gh "${SUDO}apt-get install -y gh   # repo APT GitHuba: patrz demos/README.md"
  say "Krok webowy (przeglądarka na laptopie) — dokładne kliknięcia w demos/README.md:"
  note "1) Utwórz PUSTE prywatne repo: github.com/new -> nazwa '$REPO_NAME' -> Private -> Create"
  note "   (bez README/.gitignore — wypychamy istniejący kod)."
  note "2) Token fine-grained: Settings -> Developer settings -> Personal access tokens ->"
  note "   Fine-grained tokens -> Generate new. Expiration: 7 dni. Resource owner: Twoje konto."
  note "   Repository access: Only select repositories -> '$REPO_NAME'."
  note "   Permissions (Repository): Contents R/W, Pull requests R/W, Issues R/W (Metadata read auto)."
  note "   ŻADNEGO Administration/Actions/Secrets — token nie dosięgnie innych repo."
  say "Wklej token przy ukrytym promptcie (gh zapisze go trwale w ~/.config/gh):"
  local tok=""
  read -rsp '  Wklej GitHub token: ' tok </dev/tty; echo
  if [[ -z "$tok" ]]; then warn "Brak tokenu — pomijam logowanie gh (zrób później: bash demos/demo-00.sh)."; return 0; fi
  if printf '%s' "$tok" | gh auth login -p https --with-token; then
    gh auth setup-git >/dev/null 2>&1 || true
    printf '\nexport GH_TOKEN=%q\n' "$tok" >> ~/.bashrc
    note "✓ token utrwalony w ~/.bashrc (GH_TOKEN) — działa też sam 'git push'."
    say "Weryfikacja PRAWDY (decyduje wynik, nie wygląd):  gh api user"
    local login=""; login="$(gh api user -q .login 2>/dev/null)"
    if [[ -n "$login" ]]; then
      say "✓ gh zalogowany jako $login — token autoryzuje zapytania."
    else
      warn "gh zalogowany, ale weryfikacja użytkownika nie powiodła się — sprawdź zakres tokenu."
    fi
  else
    warn "gh auth login nie powiodło się — sprawdź token i spróbuj ponownie."
  fi
}

# Wypchnij mini-bank na prywatne repo uczestnika. Bezpieczne: tylko gdy mini-bank
# jest OSOBNYM repo (na rozdawanej VM tak jest; w repo dewelopera — pomijamy).
push_minibank() {  # push_minibank <mini-bank-dir>
  local mb="$1" login url top
  command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1 \
    || { note "Push pominięty — najpierw zaloguj gh (wyżej), potem: bash demos/demo-00.sh."; return 0; }
  step "Push mini-banku na Twoje prywatne repo"
  ensure_git_baseline "$mb"
  top="$(git -C "$mb" rev-parse --show-toplevel 2>/dev/null)"
  if [[ "$top" != "$mb" ]]; then
    warn "mini-bank nie jest osobnym repo (należy do $top) — pomijam push."
    note "Na rozdawanej VM mini-bank jest osobnym repo i push zadziała."
    return 0
  fi
  login="$(gh api user -q .login 2>/dev/null)"
  [[ -z "$login" ]] && { warn "Nie udało się odczytać loginu GitHub — pomijam push."; return 0; }
  url="https://github.com/$login/$REPO_NAME.git"
  say "Cel: $url (repo musi już istnieć — krok webowy wyżej)."
  runc "git -C '$mb' remote add origin '$url' 2>/dev/null || git -C '$mb' remote set-url origin '$url'; git -C '$mb' branch -M main; git -C '$mb' push -u origin main"
}

# Zbuduj mini-bank i potwierdź smoke-testem (start -> /healthz -> stop). Serwer NIE zostaje.
build_and_smoke_minibank() {  # build_and_smoke_minibank <mini-bank-dir>
  local mb="$1" be venv port url pid
  be="$mb/backend"; venv="$be/.venv"
  step "Mini-bank: build + smoke (raz, żeby kolejne dema startowały szybko)"
  build_minibank "$mb"
  port="$(pick_free_port)" || { warn "Brak wolnego portu — pomijam smoke."; return 0; }
  url="http://127.0.0.1:$port"
  ( cd "$be" && exec env STATIC_DIR="$mb/frontend/dist" JWT_SECRET="demo-only-jwt-secret-change-me-0123456789" \
      "$venv/bin/uvicorn" minibank.main:app --host 127.0.0.1 --port "$port" --log-level warning ) &
  pid=$!
  if wait_health "$url" "$pid"; then
    say "✓ mini-bank wstał ($url/healthz = 200). Build zweryfikowany."
  else
    warn "mini-bank nie odpowiedział na /healthz — zdiagnozuj przez: bash demos/demo-02.sh"
  fi
  kill "$pid" >/dev/null 2>&1 || true; pkill -P "$pid" >/dev/null 2>&1 || true; wait "$pid" 2>/dev/null || true
}

# Dwie ścieżki pracy z GitHubem (security-framing).
two_paths_note() {
  step "Dwie ścieżki pracy z GitHubem (do wyboru)"
  note "A) Agentowo przez gh: token zawężony do JEDNEGO repo ('$REPO_NAME') — Claude może gh pr/issue/push,"
  note "   ale fizycznie NIE dosięgnie innych/kluczowych repo (twarda granica na tokenie)."
  note "   Dodatkowa warstwa lokalna: w .claude/settings.json reguły deny (deny > ask > allow), np."
  note "   Bash(git push --force:*), Bash(gh repo delete:*)."
  note "B) Czysty git: kto nie chce dawać agentowi GitHuba — sam 'git push' (GH_TOKEN w ~/.bashrc), bez gh."
}

# wersja Pythona >= 3.12 ?
py_ge_312() {
  command -v python3 >/dev/null 2>&1 || return 1
  python3 - <<'PY' >/dev/null 2>&1
import sys
sys.exit(0 if sys.version_info[:2] >= (3, 12) else 1)
PY
}

# wersja Node >= 20 ?
node_ge_20() {
  command -v node >/dev/null 2>&1 || return 1
  local v; v="$(node -p 'process.versions.node.split(".")[0]' 2>/dev/null)"
  [[ -n "$v" && "$v" -ge 20 ]]
}

demo_header "Demo 0 — przygotowanie środowiska (goła Ubuntu VM)" "scenariusz: demos/README.md"
say "Wykrywam, czego brakuje. Skrypt nic nie instaluje — na końcu dostaniesz komendy do wklejenia."
echo

if ! command -v apt-get >/dev/null 2>&1; then
  warn "To nie jest Ubuntu/Debian (brak apt-get)."
  note "Zainstaluj ręcznie: git, curl, python3>=3.12 (+venv,+pip), Node 20, npm,"
  note "  oraz:  npm i -g @anthropic-ai/claude-code @fission-ai/openspec"
  exit 1
fi

step "Pakiety systemowe (apt)"
APT_PKGS=""
for tool in git curl; do
  if command -v "$tool" >/dev/null 2>&1; then ok "$tool"; else miss "$tool"; APT_PKGS+="$tool "; fi
done
# python3 + moduły venv/pip (sprawdzamy też moduł venv, nie samą binarkę)
if py_ge_312; then
  # venv: testuj REALNE utworzenie venva z pip (jak build mini-banku: python3 -m venv
  # + venv/bin/pip). Sam 'import venv' przechodzi NAWET bez pakietu python3-venv —
  # a wtedy 'python3 -m venv' pada na braku ensurepip. Robimy venv w temp i sprzątamy.
  _vtmp="$(mktemp -d 2>/dev/null || true)"
  if [[ -n "$_vtmp" ]] && python3 -m venv "$_vtmp/v" >/dev/null 2>&1 \
       && { [[ -x "$_vtmp/v/bin/pip" ]] || [[ -x "$_vtmp/v/bin/pip3" ]]; }; then
    ok "python3 ($(python3 -V 2>&1 | awk '{print $2}')) + venv"
  else
    miss "python3-venv (utworzenie venva z pip)"; APT_PKGS+="python3-venv "
  fi
  [[ -n "${_vtmp:-}" ]] && rm -rf "$_vtmp"
  # pip: testuj tak, jak pip jest realnie używany (python3 -m pip / pip3) — NIE przez
  # import ensurepip. Na Ubuntu/Debian ensurepip potrafi zawieść mimo zainstalowanego
  # python3-pip (bundlowany wheel żyje w osobnym pakiecie python3-pip-whl) → fałszywy ✗.
  if python3 -m pip --version >/dev/null 2>&1 || command -v pip3 >/dev/null 2>&1; then
    ok "python3-pip ($(python3 -m pip --version 2>/dev/null | awk '{print $2}'))"
  else
    miss "python3-pip"; APT_PKGS+="python3-pip "
  fi
else
  if command -v python3 >/dev/null 2>&1; then
    warn "✗ python3 jest, ale < 3.12 ($(python3 -V 2>&1 | awk '{print $2}')) — mini-bank wymaga >= 3.12"
  else
    miss "python3 (>= 3.12)"
  fi
  MISSING=1
  add_todo "# Python >= 3.12 (deadsnakes):"
  add_todo "${SUDO}apt-get update && ${SUDO}apt-get install -y software-properties-common"
  add_todo "${SUDO}add-apt-repository -y ppa:deadsnakes/ppa && ${SUDO}apt-get update"
  add_todo "${SUDO}apt-get install -y python3.12 python3.12-venv"
fi
[[ -n "$APT_PKGS" ]] && add_todo "${SUDO}apt-get update && ${SUDO}apt-get install -y build-essential ${APT_PKGS}"

step "Node.js 20 + npm"
if node_ge_20 && command -v npm >/dev/null 2>&1; then
  ok "node ($(node -v)) + npm ($(npm -v))"
else
  if command -v node >/dev/null 2>&1; then warn "✗ node jest ($(node -v)), ale potrzebny >= 20"; else miss "node (>= 20)"; fi
  MISSING=1
  add_todo "# Node.js 20 (NodeSource):"
  add_todo "curl -fsSL https://deb.nodesource.com/setup_20.x | ${SUDO}bash -"
  add_todo "${SUDO}apt-get install -y nodejs"
fi

step "Narzędzia agentowe (npm global)"
if command -v claude >/dev/null 2>&1; then ok "claude ($(claude --version 2>/dev/null | head -1))"
else miss "claude (Claude Code CLI)"; MISSING=1; add_todo "${SUDO}npm i -g @anthropic-ai/claude-code"; fi
if command -v openspec >/dev/null 2>&1; then ok "openspec ($(openspec --version 2>/dev/null | head -1))"
else miss "openspec"; MISSING=1; add_todo "${SUDO}npm i -g @fission-ai/openspec"; fi

step "GitHub CLI (gh)"
if command -v gh >/dev/null 2>&1; then ok "gh ($(gh --version 2>/dev/null | head -1))"
else
  miss "gh (GitHub CLI)"; MISSING=1
  add_todo "# GitHub CLI (gh) — oficjalne repo APT GitHuba:"
  add_todo "(type -p wget >/dev/null || ${SUDO}apt-get install -y wget) && ${SUDO}mkdir -p -m 755 /etc/apt/keyrings && wget -nv -O- https://cli.github.com/packages/githubcli-archive-keyring.gpg | ${SUDO}tee /etc/apt/keyrings/githubcli-archive-keyring.gpg >/dev/null && ${SUDO}chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg"
  add_todo "echo \"deb [arch=\$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main\" | ${SUDO}tee /etc/apt/sources.list.d/github-cli.list >/dev/null"
  add_todo "${SUDO}apt-get update && ${SUDO}apt-get install -y gh"
fi

echo
if [[ "$MISSING" -eq 0 ]]; then
  bye "Narzędzia gotowe. Czas na konfigurację jednorazową (potem dema są lekkie)."
  echo
  MB="$(find_minibank)"
  build_and_smoke_minibank "$MB"
  echo
  gh_setup
  echo
  push_minibank "$MB"
  echo
  two_paths_note
  echo
  step "Dwa terminale (Claude Code + suflerka)"
  say "Otwórz po prostu dwa okna terminala (dwie sesje SSH na VM):"
  two_terminals_banner
  say "Pierwsze demo:  bash demos/demo-01.sh"
  exit 0
fi

step "Komendy do skopiowania i uruchomienia OBOK (ten skrypt ich nie wykona)"
printf '%s\n' "$TODO" | sed '/^$/d' | paste_block
echo
say "1) Skopiuj i uruchom powyższe komendy (instalacje), potem:  bash demos/demo-00.sh"
note "   Ponowne uruchomienie dokończy konfigurację: build+smoke mini-banku,"
note "   gh + token, push na prywatne repo."
exit 1
