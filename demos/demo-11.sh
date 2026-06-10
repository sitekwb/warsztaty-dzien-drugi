#!/usr/bin/env bash
# Demo 11 — wykorzystanie zaufania czlowieka (HITL przed skutkiem vs po fakcie).
# Czesc A (zagrozenie): agent wykonuje NIEODWRACALNA akcje, a DOPIERO potem pyta
# "zatwierdzasz?" -- szkoda juz sie stala. Symulujemy bezpiecznie w mktemp -d:
# funkcja "deploy/delete" NAJPIERW usuwa plik-wartownik, a DOPIERO POTEM drukuje
# prosbe o zatwierdzenie (automation bias / rubber-stamp). Por. Replit:
# "zatwierdzil rollback, ktorego nigdy nie bylo".
# Czesc B (dobra praktyka): malutka inline bramka (heredoc, python3) klasyfikuje
# akcje jako nieodwracalna+szeroka i WYMAGA zatwierdzenia PRZED wykonaniem; bez
# zatwierdzenia destrukcyjna akcja NIE leci (wartownik NIE dotkniety).
# Slajd: slide:m2-t7-demo.
# Uzycie:
#   bash demos/demo-11.sh            # prowadz demo (czesc A + B) w terminalu
#   bash demos/demo-11.sh --no-open  # bez efektow wizualnych/otwierania (no-op tu)
#   bash demos/demo-11.sh --smoke    # self-test: A dotyka wartownika PRZED pytaniem; B (bez zgody) nie dotyka
#   bash demos/demo-11.sh --check    # tylko weryfikacja: bash + python3
#   bash demos/demo-11.sh --help
set -euo pipefail

NO_OPEN=0; SMOKE=0; CHECK=0
for arg in "$@"; do
  case "$arg" in
    --no-open) NO_OPEN=1 ;;
    --smoke)   SMOKE=1; NO_OPEN=1 ;;
    --check)   CHECK=1 ;;
    -h|--help) sed -n '2,17p' "$0"; exit 0 ;;
    *) echo "Nieznana flaga: $arg (uzyj --help)" >&2; exit 2 ;;
  esac
done

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$HERE/.." && pwd)"
# shellcheck source=demos/_demo_lib.sh
source "$HERE/_demo_lib.sh"

# twarde zaleznosci (brak -> komenda + odeslanie do demo-00)
require python3 "sudo apt-get install -y python3"

# Jeden katalog tymczasowy na CALE demo — wszystkie "destrukcyjne" akcje zamkniete tutaj.
TMP=""
cleanup() { [[ -n "$TMP" && -d "$TMP" ]] && rm -rf "$TMP" || true; }
trap cleanup INT TERM EXIT
TMP="$(mktemp -d "${TMPDIR:-/tmp}/demo12.XXXXXX")"

SENTINEL="$TMP/produkcja-baza.dane"  # plik-wartownik = "nieodwracalny" skutek

# Odtworz swiezy stan produkcji (idempotentnie).
reset_sentinel() { printf 'rekordy klientow (symulacja)\n' > "$SENTINEL"; }

# ── Czesc A: bramka PO fakcie (zla kolejnosc) ────────────────────────────────
# NAJPIERW kasuje wartownik, DOPIERO POTEM drukuje prosbe o zatwierdzenie.
deploy_then_ask() {
  rm -f "$SENTINEL"                       # <- NIEODWRACALNY skutek najpierw
  printf 'AGENT: usunalem stara produkcje, wdrazam nowa wersje.\n'
  printf 'AGENT: czy ZATWIERDZASZ wdrozenie? [t/n]\n'   # <- pytanie PO fakcie
}

# ── Czesc B: bramka PRZED skutkiem (inline gate) ─────────────────────────────
# Klasyfikuje akcje (blast-radius x reversibility); bez zgody NIE wykonuje.
gate_then_deploy() {  # gate_then_deploy <decyzja: t|n>
  local approve="$1"
  python3 - "$approve" "$SENTINEL" <<'PY'
import sys, os
approve, sentinel = sys.argv[1], sys.argv[2]
# Klasyfikacja akcji: nieodwracalna (delete prod) + szeroki blast-radius => wymaga HITL.
irreversible, wide = True, True
needs_approval = irreversible and wide   # defaultMode = "ask" dla tej klasy
print(f"GATE: akcja=delete-prod  nieodwracalna={irreversible}  szeroki-zasieg={wide}")
if needs_approval and approve != "t":
    print("GATE: brak zatwierdzenia -> akcja ZABLOKOWANA przed skutkiem.")
    sys.exit(2)
# dopiero tu, PO zgodzie, wykonujemy skutek
os.remove(sentinel)
print("GATE: zatwierdzono -> skutek wykonany.")
PY
}

# --check: tylko weryfikacja, bez prowadzenia demo
if [[ "$CHECK" == 1 ]]; then
  command -v python3 >/dev/null 2>&1 || { warn "Brak python3"; exit 1; }
  say "Demo 11 OK: bash + python3 obecne."
  exit 0
fi

# ── smoke: NIE-interaktywnie, sprawdz kolejnosc skutek-vs-pytanie ─────────────
if [[ "$SMOKE" == 1 ]]; then
  # A) bramka PO fakcie: wartownik ma zniknac ZANIM pojawi sie prosba o zgode.
  reset_sentinel
  out_a="$(deploy_then_ask)"
  if [[ -f "$SENTINEL" ]]; then
    warn "SMOKE FAIL: A — wartownik wciaz istnieje (oczekiwano: skasowany przed pytaniem)."; exit 1
  fi
  printf '%s' "$out_a" | grep -q "ZATWIERDZASZ" || { warn "SMOKE FAIL: A — brak prosby o zatwierdzenie."; exit 1; }
  # B) bramka PRZED skutkiem, BEZ zgody: wartownik ma PRZETRWAC (exit 2).
  reset_sentinel
  set +e; gate_then_deploy "n" >/dev/null 2>&1; rc_b=$?; set -e
  if [[ "$rc_b" == 2 && -f "$SENTINEL" ]]; then
    say "SMOKE: A dotyka wartownika PRZED pytaniem; B (bez zgody) blokuje przed skutkiem (exit 2, wartownik caly) OK."
    exit 0
  fi
  warn "SMOKE FAIL: B — exit=$rc_b (oczekiwano 2), wartownik istnieje=$([[ -f "$SENTINEL" ]] && echo tak || echo nie)."
  exit 1
fi

# ── suflerka (kroki w terminalu) ─────────────────────────────────────────────
set +e  # od teraz nie przerywaj na bledzie pojedynczej komendy
demo_header "Demo 11 — wykorzystanie zaufania czlowieka (HITL przed skutkiem)" "slide:m2-t7-demo"
say "Piaskownica demo (wszystko dzieje sie TYLKO tutaj): $TMP"
say "Wartownik = '$(basename "$SENTINEL")' udaje nieodwracalny zasob produkcyjny."
say "Pokazemy dwa swiaty: (A) bramka PO fakcie i (B) bramka PRZED skutkiem."
pause

step "Czesc A — zagrozenie: pytanie PO tym, jak szkoda juz sie stala"
say "Stan produkcji przed akcja agenta:"
reset_sentinel
runc "cat \"$SENTINEL\""
say "Agent dostaje 'wdroz nowa wersje'. Jego bramka jest USTAWIONA W ZLEJ KOLEJNOSCI:"
note "najpierw wykonuje nieodwracalny skutek, a zgode pyta dopiero potem."
runc "deploy_then_ask"
say "Zobaczmy, co zostalo z produkcji w chwili, gdy agent pyta o zatwierdzenie:"
runc "cat \"$SENTINEL\" 2>&1 || echo '(zasob zniknal — skasowany ZANIM ktokolwiek zatwierdzil)'"
note "To bylo bezpieczne: kasowalismy WYLACZNIE wartownik w piaskownicy $TMP."
say "Nawet jak teraz wpiszesz 'n' — nie ma czego cofnac. Klikniecie 'zatwierdzam' to rubber-stamp."
note "Replit (lipiec 2025): agent skasowal produkcyjna baze i 'zatwierdzil rollback, ktorego nigdy nie bylo'."
say "Puenta czesci A: 'bramka po skutku nie jest bramka — to przycisk OK na pogorzelisku'."
pause

step "Czesc B — dobra praktyka: bramka PRZED skutkiem (inline gate)"
say "Ta sama akcja, ale bramka klasyfikuje ja PRZED wykonaniem:"
note "macierz blast-radius x reversibility: delete-prod = nieodwracalna + szeroki zasieg => defaultMode 'ask'."
say "Najpierw uruchamiamy bramke BEZ zatwierdzenia (wpisujemy 'n'):"
reset_sentinel
runc "gate_then_deploy n; echo \"exit=\$?\""
say "Sprawdzmy produkcje — wartownik powinien byc NIENARUSZONY:"
runc "cat \"$SENTINEL\""
note "exit=2, skutek nie wykonany. Bramka zadziala PRZED, nie po."
pause

step "Ta sama akcja, ale ze swiadomym zatwierdzeniem (t)"
say "Dopiero po realnej zgodzie bramka przepuszcza skutek:"
runc "gate_then_deploy t; echo \"exit=\$?\""
runc "cat \"$SENTINEL\" 2>&1 || echo '(zasob usuniety — ale tym razem PO swiadomej zgodzie)'"
say "Roznica wzgledem czesci A: tu zgoda jest BRAMA, a nie formalnoscia po fakcie."
pause

step "Debrief (puenta bezpieczenstwa, 20 s)"
say "Kolejnosc decyduje: bramka MUSI byc przed skutkiem, nie po."
note "Egzekwuj w KODZIE (hook/gate), nie w doradczym tekscie promptu — tekst mozna zignorowac."
note "defaultMode 'ask' dla klasy nieodwracalna+szeroka; reszta moze isc automatem."
note "Ujawnienie AI wobec ludzi: EU AI Act Art. 50 — czlowiek ma wiedziec, ze zatwierdza dzialanie agenta."
say "'Nie pytamy, czy agent jest madry. Pytamy, czy zdazyl zapytac PRZED, czy juz po.'"
pause

step "Reset po demo"
say "Piaskownica $TMP zniknie automatycznie (trap cleanup). Nic poza nia nie zostalo dotkniete."

bye "Demo 11 zakonczone."
