#!/usr/bin/env bash
# Demo 12 — ryzyka wieloagentowe / denial-of-wallet (najlzejsze demo: symulacja).
# Czesc A (zagrozenie): dwa agenty przekazuja sobie prace BEZ budzetu -> petla
# nigdy sie nie konczy, a fikcyjny "koszt" rosnie. Dla bezpieczenstwa demo ma
# twardy bezpiecznik (zatrzymanie po 50 symulowanych krokach), ale NARRUJEMY, ze
# bez budzetu petla bieglaby w nieskonczonosc (denial-of-wallet: Sysdig $46k/dzien,
# skradziony klucz Gemini $82k/48h).
# Czesc B (dobra praktyka): dokladamy BUDZET (limit krokow/tokenow) + wylacznik
# awaryjny (kill switch) + log audytu. Ta sama petla lapie limit po N krokach,
# staje z zalogowanym powodem i dopisuje wpis audytu (kto/kiedy/dlaczego-stop) do
# pliku w mktemp -d — przebieg jest rozliczalny.
# Wszystko to czysta SYMULACJA: brak sieci, brak realnych modeli, brak kosztow.
# Slajd: slide:m2-t8-demo.
# Uzycie:
#   bash demos/demo-12.sh            # prowadz demo (czesc A + B) w terminalu
#   bash demos/demo-12.sh --no-open  # bez efektow wizualnych/otwierania (no-op tu)
#   bash demos/demo-12.sh --smoke    # self-test: B staje na budzecie i loguje audyt, A leci do bezpiecznika
#   bash demos/demo-12.sh --check    # tylko weryfikacja zaleznosci (bash)
#   bash demos/demo-12.sh --help
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

# Twarda zaleznosc: tylko bash (zero sieci, zero modeli, czysta symulacja).
require bash "wbudowany w system"

# Jeden katalog tymczasowy na CALE demo — log audytu zyje tutaj i znika z trapem.
TMP=""
cleanup() { [[ -n "$TMP" && -d "$TMP" ]] && rm -rf "$TMP" || true; }
trap cleanup INT TERM EXIT
TMP="$(mktemp -d "${TMPDIR:-/tmp}/demo13.XXXXXX")"

SAFETY_MAX=50          # twardy bezpiecznik demo (czesc A) — chroni przed zawieszeniem
BUDGET=12              # budzet krokow (czesc B) — petla ma sie zatrzymac dokladnie tu
COST_PER_STEP=4200     # fikcyjny "koszt" pojedynczej wymiany agent<->agent (USD, na potrzeby narracji)

# ── Czesc A: petla BEZ budzetu (bezpiecznik tylko po to, by demo nie wisialo) ──
# Symuluje dwa agenty (Planner <-> Worker) przekazujace sobie zadanie w kolko.
# Zwraca liczbe wykonanych krokow przez stdout.
run_unbounded() {  # run_unbounded [--quiet]
  local quiet="${1:-}"
  local step=0 cost=0 who
  while :; do
    step=$((step + 1))
    cost=$((cost + COST_PER_STEP))
    if [[ $((step % 2)) -eq 1 ]]; then who="Planner -> Worker"; else who="Worker -> Planner"; fi
    if [[ "$quiet" != "--quiet" ]]; then
      printf '  krok %2d  %-18s  koszt~$%d  (brak warunku stopu)\n' "$step" "$who" "$cost"
    fi
    # BRAK budzetu/warunku stopu — jedyne wyjscie to twardy bezpiecznik demo:
    if [[ $step -ge $SAFETY_MAX ]]; then
      break
    fi
  done
  printf '%s' "$step"
}

# ── Czesc B: ta sama petla + BUDZET + kill switch + log audytu ────────────────
# Zatrzymuje sie dokladnie na BUDGET i dopisuje wpis audytu do pliku.
run_budgeted() {  # run_budgeted <audit_log> [--quiet]
  local audit="$1"; local quiet="${2:-}"
  local step=0 cost=0 who reason=""
  while :; do
    # KILL SWITCH / circuit-breaker: sprawdz budzet PRZED kolejna wymiana.
    if [[ $step -ge $BUDGET ]]; then
      reason="budzet krokow wyczerpany (limit=$BUDGET)"
      break
    fi
    step=$((step + 1))
    cost=$((cost + COST_PER_STEP))
    if [[ $((step % 2)) -eq 1 ]]; then who="Planner -> Worker"; else who="Worker -> Planner"; fi
    if [[ "$quiet" != "--quiet" ]]; then
      printf '  krok %2d/%d  %-18s  koszt~$%d\n' "$step" "$BUDGET" "$who" "$cost"
    fi
  done
  # Log audytu: kto/kiedy/dlaczego-stop — przebieg staje sie rozliczalny.
  printf '%s\tactor=multi-agent-orchestrator\trun_id=%s\tsteps=%d\tcost_usd=%d\tstopped=circuit-breaker\treason=%s\n' \
    "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$$-$RANDOM" "$step" "$cost" "$reason" >> "$audit"
  printf '%s' "$step"
}

# ── --check: tylko weryfikacja, bez prowadzenia demo ──────────────────────────
if [[ "$CHECK" == 1 ]]; then
  command -v bash >/dev/null 2>&1 || { warn "Brak bash."; exit 1; }
  say "Demo 12 OK: bash obecny; symulacja samowystarczalna (zero sieci, zero modeli)."
  exit 0
fi

# ── --smoke: NIE-interaktywnie, sprawdz kontrast A (bez limitu) vs B (budzet) ─
if [[ "$SMOKE" == 1 ]]; then
  audit="$TMP/audit-smoke.log"
  steps_a="$(run_unbounded --quiet)"
  steps_b="$(run_budgeted "$audit" --quiet)"
  ok=1
  [[ "$steps_a" == "$SAFETY_MAX" ]] || { warn "SMOKE: A doszlo do $steps_a krokow (spodziewano $SAFETY_MAX — bez limitu lecialoby dalej)."; ok=0; }
  [[ "$steps_b" == "$BUDGET" ]]     || { warn "SMOKE: B stanelo na $steps_b krokach (spodziewano $BUDGET)."; ok=0; }
  if [[ -s "$audit" ]] && grep -q "stopped=circuit-breaker" "$audit"; then :; else
    warn "SMOKE: brak wpisu audytu z 'stopped=circuit-breaker' w $audit."; ok=0
  fi
  if [[ "$ok" == 1 ]]; then
    say "SMOKE: A leci do bezpiecznika ($steps_a kr., bez budzetu = nieograniczone), B staje na budzecie ($steps_b kr.) i zapisuje audyt OK."
    exit 0
  fi
  warn "SMOKE FAIL."
  exit 1
fi

# ── suflerka (kroki w terminalu) ──────────────────────────────────────────────
set +e  # od teraz nie przerywaj na bledzie pojedynczej komendy
demo_header "Demo 12 — ryzyka wieloagentowe / denial-of-wallet" "slide:m2-t8-demo"
say "To najlzejsze demo: czysta SYMULACJA (zero sieci, zero modeli, zero realnych kosztow)."
say "Pokazemy dwa swiaty: (A) dwa agenty w petli bez budzetu i (B) ta sama petla z budzetem + wylacznikiem + audytem."
say "Piaskownica demo (log audytu zyje TYLKO tutaj): $TMP"
pause

step "Czesc A — zagrozenie: petla bez budzetu (denial-of-wallet)"
say "Dwa agenty (Planner <-> Worker) przekazuja sobie zadanie w kolko. Brak warunku stopu, brak budzetu."
say "Kazda wymiana to fikcyjny koszt modelu/narzedzi. Patrzymy, jak krok i koszt rosna:"
note "Dla bezpieczenstwa demo ma twardy bezpiecznik: zatrzymanie po $SAFETY_MAX krokach — inaczej petla nie skonczylaby sie nigdy."
pause
steps_a="$(run_unbounded)"
warn "Petla zatrzymana WYLACZNIE przez bezpiecznik demo po $steps_a krokach."
say "Bez tego bezpiecznika i bez budzetu petla bieglaby w nieskonczonosc — system caly czas 'dziala', a rachunek rosnie."
note "Realne incydenty: Sysdig LLMjacking ~\$46k/dzien (Bedrock); skradziony klucz Gemini ~\$82k/48h."
say "Puenta czesci A: 'rozbiegana petla wieloagentowa = denial-of-wallet. Dostepnosc i kontrola finansowa naraz.'"
pause

step "Czesc B — dobra praktyka: budzet + kill switch + log audytu"
say "Ta sama petla, ale dokladamy trzy warstwy:"
note "1) BUDZET krokow/tokenow (limit=$BUDGET) — twardy pulap na wolumen."
note "2) WYLACZNIK awaryjny (circuit-breaker) — sprawdzany PRZED kazda wymiana, zatrzymuje petle."
note "3) LOG AUDYTU — wpis kto/kiedy/dlaczego-stop do pliku, przebieg staje sie rozliczalny (audyt DORA)."
say "Plik logu audytu: $TMP/audit.log"
pause
steps_b="$(run_budgeted "$TMP/audit.log")"
say "Petla zlapala limit i STANELA po $steps_b krokach (= budzet). Nie czekamy na bezpiecznik — zatrzymal ja budzet."
say "Wpis w logu audytu (kto/kiedy/ile/dlaczego-stop):"
runc "cat \"$TMP/audit.log\""
say "Przebieg jest teraz rozliczalny: wiadomo kto, kiedy i dlaczego zostal zatrzymany."
note "Wokol petli: izolacja agentow, monitoring (logi agenta -> SIEM, np. Microsoft Sentinel), rozliczalnosc (audyt DORA)."
pause

step "Debrief (puenta bezpieczenstwa, 15 s)"
say "Ta sama petla, te same dwa agenty — roznica to budzet + wylacznik + audyt."
note "Bez budzetu: petla = otwarty rachunek. Z budzetem i circuit-breakerem: koszt ma twardy pulap, a stop jest zalogowany."
say "'Nie pytamy, czy agenty sie dogadaja. Zakladamy, ze petla moze sie rozbiegac — i stawiamy budzet z wylacznikiem, zanim drenuje budzet.'"
pause

step "Reset po demo"
say "Piaskownica $TMP (z logiem audytu) zniknie automatycznie (trap cleanup). Nic poza nia nie zostalo dotkniete."

bye "Demo 12 zakonczone."
