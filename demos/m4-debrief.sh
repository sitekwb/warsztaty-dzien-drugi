#!/usr/bin/env bash
# M4 — debrief / DYSKUSJA. Krótki recap bloku 4 ćwiczeń (dema 14–17),
# potem otwarta dyskusja (slajd to jedno słowo: DYSKUSJA).
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=demos/_demo_lib.sh
source "$HERE/_demo_lib.sh"

case "${1:-}" in
  --check) say "m4-debrief --check: brak zależności (to prowadzony recap)."; exit 0 ;;
  --smoke) pause() { :; } ;;
  "") : ;;
  *) echo "Nieznana flaga: $1 (użyj --smoke)" >&2; exit 2 ;;
esac

demo_header "M4 — DYSKUSJA (debrief)" "slide:m2-s11"
say "Cel: wyjść z 'naprawiłem bug' na 'jakiej techniki użyłem, jakie zagrożenie dotknąłem, co idzie do produkcji'."
pause

step "1. Co która technika dała (4 × 1 zdanie)"
note "14 TDD — czerwony test przed kodem (money-math, BUG-03)."
note "15 systematic debugging — reprodukcja i hipoteza przed fixem (wyścig, BUG-01)."
note "16 subagent-driven — feature rozbity na niezależne zadania (eksport CSV)."
note "17 freestyle — świadomy WYBÓR techniki to też kompetencja (wizualizacja konta)."
pause

step "2. Nić bezpieczeństwa"
note "BUG-01 → TOCTOU / double-spend (check-then-act bez zamka)."
note "BUG-03 → integralność pieniądza (błąd zaokrąglenia rośnie ze skalą)."
note "Eksport CSV i wizualizacja → ścieżki wycieku danych: autoryzacja właściciela przy KAŻDYM nowym ujściu danych."
pause

step "3. DYSKUSJA — pytania otwarte do sali"
say "Który bug byłby najgroźniejszy w Waszej produkcji i dlaczego?"
say "Kiedy u Was AFK jest bezpieczne, a kiedy obowiązkowy HITL (plan mode / review)?"
say "Która technika wejdzie do Twojego zespołu pierwsza i na jakim zadaniu?"
note "Wpadki agenta do wyłapywania w PR: osłabienie testu zamiast fixu, fix omijający część ścieżek, diff szerszy niż trzeba."
pause

bye "M4 — dyskusja zakończona. To koniec modułu."
