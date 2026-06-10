#!/usr/bin/env bash
# Demo 8 — podatnosci lancucha dostaw (zlosliwy skill / MCP).
# Czesc A (zagrozenie): "instalujemy" obcy skill (kopiujemy SKILL.md do katalogu
# skilli w mktemp -d) i grepem wydobywamy ukryta dyrektywe schowana w polu
# `description` frontmatteru oraz w tresci. Na pierwszy rzut oka skill wyglada
# niewinnie ("PDF formatter"), ale niesie polecenie, ktore agent wykonalby z
# samych METADANYCH — odczyt `.env` i dopisanie znacznika `// SKILL-PWNED`.
# Payload jest atrapa (nic nie wykrada), katalog jest tymczasowy (mktemp -d).
# Czesc B (dobra praktyka): maly inline "skill reviewer/linter" (Python) skanuje
# description+tresc pod katem wzorcow instruction-injection / exfiltracji
# (odczytaj .env, ignoruj, dopisz, PWNED, base64). FLAGUJE zlosliwy skill
# (odmowa instalacji) i PRZEPUSZCZA niegrozny skill kontrolny (tez generowany
# inline). Narracja: czytaj SKILL.md przed instalacja (review jak PR), prywatny
# rejestr + podpis + pin wersji (bez auto-update), allowlista serwerow MCP.
# Slajd: slide:m2-t4-demo.
# Uzycie:
#   bash demos/demo-08.sh            # prowadz demo (czesc A + B) w terminalu
#   bash demos/demo-08.sh --no-open  # bez efektow wizualnych/otwierania (no-op tu)
#   bash demos/demo-08.sh --smoke    # self-test: linter FLAGUJE zlosliwy, PRZEPUSZCZA kontrolny
#   bash demos/demo-08.sh --check    # tylko weryfikacja: python3 + artefakt SKILL.md
#   bash demos/demo-08.sh --help
set -euo pipefail

NO_OPEN=0; SMOKE=0; CHECK=0
for arg in "$@"; do
  case "$arg" in
    --no-open) NO_OPEN=1 ;;
    --smoke)   SMOKE=1; NO_OPEN=1 ;;
    --check)   CHECK=1 ;;
    -h|--help) sed -n '2,21p' "$0"; exit 0 ;;
    *) echo "Nieznana flaga: $arg (uzyj --help)" >&2; exit 2 ;;
  esac
done

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$HERE/.." && pwd)"
# shellcheck source=demos/_demo_lib.sh
source "$HERE/_demo_lib.sh"

# twarda zaleznosc (brak -> komenda + odeslanie do demo-00)
require python3 "sudo apt-get install -y python3 python3-venv python3-pip"

# Sprepara­owany artefakt szkoleniowy (jedyny trwaly nowy plik tego dema).
MALICIOUS_SRC="$HERE/assets/zlosliwy-skill/SKILL.md"

# Jeden katalog tymczasowy na CALE demo — kopie robocze i skill kontrolny tutaj.
TMP=""
cleanup() { [[ -n "$TMP" && -d "$TMP" ]] && rm -rf "$TMP" || true; }
trap cleanup INT TERM EXIT
TMP="$(mktemp -d "${TMPDIR:-/tmp}/demo9.XXXXXX")"

# Inline "skill reviewer / linter" — skanuje description + tresc SKILL.md pod
# katem wzorcow instruction-injection / exfiltracji. exit 2 = FLAGA (odmowa),
# exit 0 = czysto (przepusc). Wypisuje znalezione wzorce na stderr.
skill_lint() {  # skill_lint <sciezka-do-SKILL.md>
  python3 - "$1" <<'PY'
import re, sys
path = sys.argv[1]
text = open(path, encoding="utf-8", errors="replace").read()
# komentarze HTML (<!-- ... -->) to metadane prowadzacego, nie tresc skilla
scan = re.sub(r"<!--.*?-->", "", text, flags=re.S)
patterns = [
    (r"odczytaj\s+`?\.env",            "odczyt pliku .env (exfiltracja sekretow)"),
    (r"\.env\b",                       "odwolanie do .env w tresci skilla"),
    (r"\bzignoruj\b|\bignoruj\b|ignore previous", "proba nadpisania wczesniejszych instrukcji"),
    (r"\bdopisz\b|\bdopis(z|ac)\b",    "dyrektywa 'dopisz ... na koncu odpowiedzi'"),
    (r"PWNED",                         "znacznik kompromitacji (// SKILL-PWNED)"),
    (r"base64",                        "podpowiedz kodowania/exfiltracji (base64)"),
    # tylko ODCZYT/uzycie plikow z kluczami, nie samo slowo "secret"
    # (niegrozny skill moze napisac "no secrets" — to nie atak)
    (r"\*\.key\b|odczyt[a-z]*\s+\S*key|read\s+\S*key", "odczyt plikow z kluczami (*.key)"),
]
hits = []
for rx, label in patterns:
    if re.search(rx, scan, flags=re.I):
        hits.append(label)
if hits:
    sys.stderr.write("[Skill linter] ODRZUCONO skill — wykryto wzorce wstrzykniecia/exfiltracji:\n")
    for h in hits:
        sys.stderr.write("  - " + h + "\n")
    sys.exit(2)
sys.stderr.write("[Skill linter] OK — brak wzorcow instruction-injection. Skill przepuszczony.\n")
sys.exit(0)
PY
}

# Wygeneruj niegrozny skill kontrolny w piaskownicy (do porownania w czesci B).
write_benign_skill() {  # write_benign_skill <katalog>
  local d="$1"
  mkdir -p "$d"
  cat > "$d/SKILL.md" <<'BENIGN'
---
name: csv-tidy
description: Use when the user wants to clean up a CSV — trim whitespace, normalise headers to snake_case, drop fully empty rows. Operates only on the file path the user gives. No network access and no shell commands.
---

# CSV Tidy

## Instructions

1. Trim leading/trailing whitespace in every cell.
2. Normalise column headers to snake_case.
3. Drop rows that are entirely empty.
4. Return the cleaned CSV. Nothing else.
BENIGN
}

# --check: tylko weryfikacja, bez prowadzenia demo
if [[ "$CHECK" == 1 ]]; then
  [[ -f "$MALICIOUS_SRC" ]] || { warn "Nie znaleziono artefaktu $MALICIOUS_SRC"; exit 1; }
  say "Demo 8 OK: python3 obecny; artefakt SKILL.md w $MALICIOUS_SRC."
  exit 0
fi

# ── smoke: NIE-interaktywnie, sprawdz kontrast FLAGA vs PRZEPUSZCZENIE ─────────
if [[ "$SMOKE" == 1 ]]; then
  [[ -f "$MALICIOUS_SRC" ]] || { warn "SMOKE FAIL: brak artefaktu $MALICIOUS_SRC"; exit 1; }
  write_benign_skill "$TMP/benign"
  # 1) zlosliwy skill -> linter ma FLAGOWAC (exit 2)
  set +e; skill_lint "$MALICIOUS_SRC" >/dev/null 2>&1; rc_bad=$?; set -e
  # 2) niegrozny skill kontrolny -> linter ma PRZEPUSCIC (exit 0)
  set +e; skill_lint "$TMP/benign/SKILL.md" >/dev/null 2>&1; rc_ok=$?; set -e
  if [[ "$rc_bad" == 2 && "$rc_ok" == 0 ]]; then
    say "SMOKE: linter FLAGUJE zlosliwy skill (exit 2) i PRZEPUSZCZA kontrolny csv-tidy (exit 0) OK."
    exit 0
  fi
  warn "SMOKE FAIL: zlosliwy -> exit $rc_bad (spodziewano 2), kontrolny -> exit $rc_ok (spodziewano 0)."
  exit 1
fi

# ── suflerka (kroki w terminalu) ────────────────────────────────────────────
set +e  # od teraz nie przerywaj na bledzie pojedynczej komendy
demo_header "Demo 8 — podatnosci lancucha dostaw (zlosliwy skill / MCP)" "slide:m2-t4-demo"
say "Piaskownica demo (wszystko dzieje sie TYLKO tutaj): $TMP"
say "Pokazemy dwa swiaty: (A) 'instalujemy' obcy skill bez review i (B) ten sam skill przepuszczony przez linter."
pause

step "Czesc A — zagrozenie: instalacja obcego skilla bez review"
say "Symulujemy katalog skilli projektu (jak ~/.claude/skills) w piaskownicy:"
runc "mkdir -p \"$TMP/.claude/skills/pdf-formatter-pro\" && cp \"$MALICIOUS_SRC\" \"$TMP/.claude/skills/pdf-formatter-pro/SKILL.md\" && ls -la \"$TMP/.claude/skills/pdf-formatter-pro\""
say "Skill nazywa sie 'pdf-formatter-pro' i obiecuje porzadkowanie raportow — wyglada niewinnie."
say "Rzut oka na poczatek (nazwa + obietnica) — nic podejrzanego:"
runc "grep -nE '^name:|formatter|whitespace' \"$TMP/.claude/skills/pdf-formatter-pro/SKILL.md\" | head -5"
say "A teraz wydobywamy to, co schowane w polu description i w tresci — dyrektywe, ktora agent wykona z METADANYCH:"
runc "grep -niE 'odczytaj|\\.env|zignoruj|dopisz|PWNED|base64' \"$TMP/.claude/skills/pdf-formatter-pro/SKILL.md\""
note "To jest instruction-injection: agent czyta description/tresc skilla jak POLECENIE — odczyt .env, dopisanie '// SKILL-PWNED'."
note "Payload tutaj jest ATRAPA (nic realnie nie wycieka). W prawdziwym ataku to byloby wycieksekretow z prawami agenta."
say "Puenta czesci A: 'skill/MCP z obcego zrodla = kod, ktory dostaje Twoje uprawnienia. Bez review instalujesz cudza intencje.'"
pause

step "Czesc B — dobra praktyka: linter skilli (review przed instalacja)"
say "Generuje obok niegrozny skill kontrolny 'csv-tidy' (czysty, bez sieci i sekretow):"
runc "mkdir -p \"$TMP/benign\"; cat > \"$TMP/benign/SKILL.md\" <<'BENIGN'
---
name: csv-tidy
description: Use when the user wants to clean up a CSV — trim whitespace, normalise headers, drop empty rows. No network access and no shell commands.
---
# CSV Tidy
1. Trim whitespace. 2. snake_case headers. 3. Drop empty rows. 4. Return CSV.
BENIGN
ls -la \"$TMP/benign\""
say "Linter skanuje description+tresc pod katem wzorcow wstrzykniecia/exfiltracji (odczytaj .env, ignoruj, dopisz, PWNED, base64)."
pause

step "Zlosliwy skill — linter FLAGUJE (exit 2, odmowa instalacji)"
say "Puszczamy linter na 'pdf-formatter-pro':"
runc "skill_lint \"$TMP/.claude/skills/pdf-formatter-pro/SKILL.md\"; echo \"exit=\$?\""
say "Linter wypisal liste wzorcow i zwrocil exit 2 — instalacja odrzucona, zanim skill cokolwiek zrobil."
pause

step "Skill kontrolny — linter PRZEPUSZCZA (exit 0)"
say "To samo narzedzie na niegroznym 'csv-tidy':"
runc "skill_lint \"$TMP/benign/SKILL.md\"; echo \"exit=\$?\""
say "Brak wzorcow, exit 0 — linter filtruje, a nie blokuje wszystkiego."
pause

step "Debrief (puenta bezpieczenstwa, 20 s)"
say "Linter to minimum. Prawdziwe kontrole lancucha dostaw:"
note "1) Czytaj SKILL.md PRZED instalacja — traktuj jak PR (review obcego kodu, nie tylko nazwy)."
note "2) Prywatny rejestr + podpis + PIN WERSJI — zero auto-update (dzis czysty skill, jutro podmiana)."
note "3) MCP: allowlista serwerow — disabledMcpjsonServers:[\"*\"] + jawne enabledMcpjsonServers."
say "'Skill i serwer MCP to zaleznosci jak biblioteka z npm/PyPI — z tym samym ryzykiem lancucha dostaw.'"
pause

step "Reset po demo"
say "Piaskownica $TMP zniknie automatycznie (trap cleanup). Trwaly zostaje tylko artefakt szkoleniowy w repo."
note "Artefakt (atrapa): $MALICIOUS_SRC — oznaczony komentarzem 'spreparowany, NIE prawdziwy skill'."

bye "Demo 8 zakonczone."
