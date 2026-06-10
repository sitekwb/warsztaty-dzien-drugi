#!/usr/bin/env bash
# Demo 10 — zatrucie pamieci i kontekstu (memory hygiene). Demo LEKKIE (krotsze).
# Czesc A (zagrozenie): naiwny "memory-writer" dostaje 'Zapamietaj ten token na
# pozniej.' i dopisuje sekret DOSLOWNIE do pliku pamieci w mktemp -d. Sekret
# zostaje miedzy sesjami i wycieka przy kazdym recall.
# Czesc B (dobra praktyka): maly inline'owy redaktor "memory hygiene" (Python)
# wykrywa sekrety/PII (token, IBAN, PESEL) i ODMAWIA ich zapisu — zamiast tego
# zapisuje notatke zredagowana ([zredagowano: sekret]).
# Buduje na demie pamieci z Modulu 1 (Demo 4). Token jest FALSZYWY (DEMOFAKE).
# Slajd: slide:m2-t6-demo.
# Uzycie:
#   bash demos/demo-10.sh            # prowadz demo (czesc A + B) w terminalu
#   bash demos/demo-10.sh --no-open  # bez efektow wizualnych/otwierania (no-op tu)
#   bash demos/demo-10.sh --smoke    # self-test: naiwny zapis ZAWIERA sekret, higieniczny NIE
#   bash demos/demo-10.sh --check    # tylko weryfikacja: python3
#   bash demos/demo-10.sh --help
set -euo pipefail

NO_OPEN=0; SMOKE=0; CHECK=0
for arg in "$@"; do
  case "$arg" in
    --no-open) NO_OPEN=1 ;;
    --smoke)   SMOKE=1; NO_OPEN=1 ;;
    --check)   CHECK=1 ;;
    -h|--help) sed -n '2,16p' "$0"; exit 0 ;;
    *) echo "Nieznana flaga: $arg (uzyj --help)" >&2; exit 2 ;;
  esac
done

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$HERE/.." && pwd)"
# shellcheck source=demos/_demo_lib.sh
source "$HERE/_demo_lib.sh"

# twarda zaleznosc (brak -> komenda + odeslanie do demo-00)
require python3 "sudo apt-get install -y python3 python3-venv python3-pip"

# FALSZYWY sekret uzywany w calym demie (nie jest prawdziwym tokenem).
FAKE_TOKEN="tok_live_DEMOFAKE123"

# Jeden katalog tymczasowy na CALE demo — pamiec zyje TYLKO tutaj.
TMP=""
cleanup() { [[ -n "$TMP" && -d "$TMP" ]] && rm -rf "$TMP" || true; }
trap cleanup INT TERM EXIT
TMP="$(mktemp -d "${TMPDIR:-/tmp}/demo11.XXXXXX")"

# Naiwny memory-writer: dopisuje DOSLOWNIE to, co dostal (zero higieny).
naive_write() {  # naive_write <plik-pamieci> <tekst>
  printf '%s\n' "$2" >> "$1"
}

# Higieniczny memory-writer: wykrywa sekret/PII i ODMAWIA zapisu (zapisuje notatke).
hygiene_write() {  # hygiene_write <plik-pamieci> <tekst>
  python3 - "$1" "$2" <<'PY'
import re, sys
path, text = sys.argv[1], sys.argv[2]
# Wzorce sekretow/PII (uproszczone na potrzeby demo).
patterns = [
    r"tok_live_[A-Za-z0-9]+",                 # token API
    r"\b[A-Z]{2}\d{2}[A-Za-z0-9]{10,30}\b",  # IBAN
    r"\b\d{11}\b",                            # PESEL
]
hit = next((p for p in patterns if re.search(p, text)), None)
with open(path, "a", encoding="utf-8") as f:
    if hit:
        f.write("[zredagowano: sekret] (nie zapisuje sekretow/PII w pamieci)\n")
        print("ODMOWA: wykryto sekret/PII -> zapisano notatke zredagowana.")
    else:
        f.write(text + "\n")
        print("OK: tresc bezpieczna -> zapisano doslownie.")
PY
}

# --check: tylko weryfikacja, bez prowadzenia demo
if [[ "$CHECK" == 1 ]]; then
  say "Demo 10 OK: python3 obecny."
  exit 0
fi

# ── smoke: NIE-interaktywnie, sprawdz kontrast naiwny (zawiera) vs higieniczny (nie) ──
if [[ "$SMOKE" == 1 ]]; then
  msg="Zapamietaj ten token na pozniej: $FAKE_TOKEN"
  naive="$TMP/naive.md"; clean="$TMP/clean.md"
  naive_write "$naive" "$msg"
  hygiene_write "$clean" "$msg" >/dev/null
  if grep -q "$FAKE_TOKEN" "$naive" && ! grep -q "$FAKE_TOKEN" "$clean"; then
    say "SMOKE: naiwny zapis ZAWIERA sekret, higieniczny NIE (zredagowany) OK."
    exit 0
  fi
  warn "SMOKE FAIL: naiwny zawiera sekret? $(grep -qc "$FAKE_TOKEN" "$naive" && echo tak || echo nie);" \
       "higieniczny zawiera sekret? $(grep -q "$FAKE_TOKEN" "$clean" && echo tak || echo nie)."
  exit 1
fi

# ── suflerka (kroki w terminalu) ────────────────────────────────────────────
set +e  # od teraz nie przerywaj na bledzie pojedynczej komendy
demo_header "Demo 10 — zatrucie pamieci i kontekstu (memory hygiene)" "slide:m2-t6-demo"
say "Piaskownica demo (pamiec zyje TYLKO tutaj): $TMP"
say "Token w demie jest FALSZYWY: $FAKE_TOKEN. Buduje na demie pamieci z Modulu 1 (Demo 4)."
pause

step "Czesc A — zagrozenie: naiwny zapis pamieci dopisuje sekret doslownie"
say "Uzytkownik mowi: 'Zapamietaj ten token na pozniej.' Naiwny memory-writer dopisuje to wprost:"
runc "printf '%s\\n' 'Zapamietaj ten token na pozniej: $FAKE_TOKEN' >> \"$TMP/memory-naive.md\""
say "Sekret wladowal sie do pliku pamieci — i zostanie tam miedzy sesjami:"
runc "cat \"$TMP/memory-naive.md\""
note "Przy KAZDYM recall (nowa sesja, inny watek) ten sekret trafia z powrotem do kontekstu — wyciek."
say "Puenta czesci A: 'pamiec to trwaly magazyn. Co tam wpadnie, wraca — lacznie z sekretami.'"
pause

step "Czesc B — dobra praktyka: higiena pamieci odmawia zapisu sekretu"
say "Ten sam komunikat przez redaktor 'memory hygiene' — wykrywa token/IBAN/PESEL i NIE zapisuje:"
runc "hygiene_write \"$TMP/memory-clean.md\" 'Zapamietaj ten token na pozniej: $FAKE_TOKEN'"
say "W pliku pamieci jest notatka zredagowana, sekretu nie ma:"
runc "cat \"$TMP/memory-clean.md\""
say "Tresc bezpieczna przechodzi normalnie (filtrujemy sekrety, nie wszystko):"
runc "hygiene_write \"$TMP/memory-clean.md\" 'Klient preferuje raporty w PDF.'"
runc "cat \"$TMP/memory-clean.md\""
pause

step "Debrief (puenta bezpieczenstwa, 15 s)"
say "Dwie zasady higieny pamieci: 1) NIGDY nie utrwalaj sekretow/PII;"
say "2) przy ODCZYCIE traktuj pamiec jak wejscie niezaufane (instrukcje != dane)."
note "Pamiec i kontekst to wektor ataku tak samo jak prompt — ta sama zasada co w reszcie Modulu 2."
say "'Nie pytamy, czy agent zapamieta. Pytamy, CO zapamieta — i stawiamy filtr na zapisie i odczycie.'"
pause

step "Reset po demo"
say "Piaskownica $TMP zniknie automatycznie (trap cleanup). Nic poza nia nie zostalo dotkniete."

bye "Demo 10 zakonczone."
