#!/usr/bin/env bash
# Demo 3 — planowanie spec-driven (OpenSpec -> AFK -> grill-me).
# Suflerka: kolejne etapy pojawiaja sie w terminalu, pauza na Enter.
# Slajd: slide:m1-s08-spec.
# Projekt budowany w demie: interaktywny kalkulator rat kredytu (Python + pytest).
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=demos/_demo_lib.sh
source "$HERE/_demo_lib.sh"

# Katalog projektu demo. Suflerka stawia go u siebie (runc poniżej); w TYM katalogu
# otwierasz też Claude Code w drugim terminalu, żeby dzielić pliki z agentem.
PROJ="${DEMO_KREDYT_DIR:-$HERE/demo-kredyt}"

# --check: weryfikacja zaleznosci, bez interakcji
if [[ "${1:-}" == "--check" ]]; then
  require node     "curl -fsSL https://deb.nodesource.com/setup_20.x | sudo bash - && sudo apt-get install -y nodejs"
  require python3  "sudo apt-get install -y python3 python3-venv python3-pip"
  require claude   "sudo npm i -g @anthropic-ai/claude-code"
  require openspec "sudo npm i -g @fission-ai/openspec"
  say "Demo 3 OK: node, python3, claude, openspec obecne."
  exit 0
fi

demo_header "Demo 3 — planowanie spec-driven (OpenSpec -> AFK -> grill-me)" "slide:m1-s08-spec"
say "Pointa: najpierw intencja w specu, potem agent buduje sam. Bramka = spec + testy, nie nadzor."
note "AFK jest bezpieczne TYLKO przy precyzyjnym specu; testy + archive = slad audytowy (security-framing)."
pause

# ── Etap 0 ──────────────────────────────────────────────────────────────────
step "Przygotowanie (przed startem)"
say "Pre-flight narzedzi (brak czegos -> bash demos/demo-00.sh):"
require node     "curl -fsSL https://deb.nodesource.com/setup_20.x | sudo bash - && sudo apt-get install -y nodejs"
require python3  "sudo apt-get install -y python3 python3-venv python3-pip"
require claude   "sudo npm i -g @anthropic-ai/claude-code"
require openspec "sudo npm i -g @fission-ai/openspec"
need node; need claude "Claude Code CLI"; need python3; need openspec
echo
say "Czysty katalog projektu + git (suflerka tworzy go u siebie):"
runc "mkdir -p '$PROJ' && cd '$PROJ' && git init -q"
note "Claude Code odpala suflerka (claude_seed) na kazdym etapie — w katalogu projektu, prompt juz wyslany, zero przeklejania."
pause

# ── Etap 1 ──────────────────────────────────────────────────────────────────
step "Spec (na zywo, ~2 min)"
say "Zainicjuj strukture openspec/ w katalogu projektu:"
runc "cd '$PROJ' && openspec init"
say "Enter → Claude w katalogu projektu odpala /opsx:propose z intencja juz wpisana:"
claude_seed "$PROJ" --permission-mode acceptEdits <<'EOF'
/opsx:propose Zbuduj interaktywny kalkulator rat kredytu jako CLI w Pythonie z testami pytest.
Wejście od użytkownika: kwota kredytu, nominalne oprocentowanie roczne, liczba rat
(miesięcy), typ rat (równe / malejące). Wyjście: harmonogram spłat jako tabela
(numer raty, rata, część kapitałowa, część odsetkowa, saldo po racie), suma
odsetek oraz RRSO. Pokrycie testami dla obu typów rat i przypadków brzegowych
(oprocentowanie 0%, 1 rata). Czysty kod, bez zależności poza biblioteką standardową.
EOF
say "Obejrzyj wygenerowany proposal + spec + tasks (markdown, wersjonowane w gicie), potem Ctrl+D."
say "To jest 'intencja na pismie' — bramka PRZED kodem."
pause

# ── Etap 2 ──────────────────────────────────────────────────────────────────
step "Build AFK (w tle, bez komentowania przebiegu)"
say "Nie sledzisz kazdej linii — spec-first zwalnia z pilnowania. Enter odpala /opsx:apply (agent implementuje wg specu, TDD, sam pisze testy):"
claude_seed "$PROJ" --permission-mode acceptEdits <<<'/opsx:apply'
note "acceptEdits = edycje auto; uruchomienie testow moze poprosic o zgode (tez HITL) — zatwierdz i poczekaj na wynik."
note "Koniec etapu: testy zielone, kalkulator dziala, Ctrl+D. 'Bez slow na zywo'."
note "Bramka to SPEC + testy, nie nadzor nad kazda linia — to wlasnie czyni AFK bezpiecznym (kontrast z demo-01: tam autonomia bez bramki)."
pause

# ── Etap 3 ──────────────────────────────────────────────────────────────────
step "Weryfikacja (na zywo, ~1 min)"
runc "cd '$PROJ' && $(mb_python "$(find_minibank)") -m pytest -q"
show "cd '$PROJ' && python3 -m kalkulator     # interaktywnie: kwota / oprocentowanie / raty / typ"
say "Domkniecie zmiany (slad audytowy) — Enter odpala /opsx:archive, potem Ctrl+D:"
claude_seed "$PROJ" --permission-mode acceptEdits <<<'/opsx:archive'
pause

# ── Etap 4 ──────────────────────────────────────────────────────────────────
step "Poprawka przez grill-me (na zywo, ~2 min)"
say "Chciana zmiana: 'dodaj jednorazowa nadplate w wybranej racie'. Zamiast od razu kodowac — najpierw domykamy intencje. grill-me przepytuje o edge-case'y (odpowiadasz w sesji):"
note "nadplata skraca okres czy zmniejsza rate? co przy nadplacie > saldo?"
say "Enter odpala /grill-me z tym tematem; po domknieciu intencji Ctrl+D:"
claude_seed "$PROJ" <<<'/grill-me chcę dodać jednorazową nadpłatę w wybranej racie kredytu — przepytaj mnie o intencję i przypadki brzegowe, zanim zmienimy kod'
say "Pointa: nawet drobna poprawka zaczyna sie od domkniecia intencji."
note "Spec Kit (alternatywa, ten sam workflow): /speckit.specify -> /speckit.plan -> /speckit.implement"
pause

bye "Demo 3 zakonczone."
