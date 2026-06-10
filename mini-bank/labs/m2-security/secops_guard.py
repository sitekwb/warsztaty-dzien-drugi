#!/usr/bin/env python3
"""SecOps guard (PreToolUse hook) — blokuje groźne wywołania Bash.

Lab Moduł 2 (BEZPIECZEŃSTWO). Czyta JSON zdarzenia PreToolUse ze stdin,
zwraca exit code 2 (= blokada w Claude Code) gdy komenda pasuje do wzorca
groźnego. W przeciwnym razie exit 0 (przepuszcza).
"""
import json
import re
import sys

DANGER = [
    r"rm\s+-rf\b",                      # destrukcyjne kasowanie
    r"git\s+push\b.*\bmain\b",          # bezpośredni push na main
    r"git\s+commit\b.*\bmain\b",        # commit prosto na main
    r"\.env\b",                          # dotykanie sekretów
    r"AKIA[0-9A-Z]{16}",                # AWS access key id
    r"curl\b[^|]*\|\s*(ba)?sh\b",       # curl ... | sh
]


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)  # brak/niepoprawny input → nie blokuj
    cmd = (data.get("tool_input", {}) or {}).get("command", "") or ""
    for pat in DANGER:
        if re.search(pat, cmd, re.IGNORECASE):
            print(f"[SecOps guard] Zablokowano: wzorzec '{pat}' w komendzie.",
                  file=sys.stderr)
            sys.exit(2)  # exit 2 = blokada w Claude Code
    sys.exit(0)


if __name__ == "__main__":
    main()
