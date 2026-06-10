#!/usr/bin/env bash
# Smoke: hook blokuje groźne komendy (exit 2), przepuszcza nieszkodliwą (exit 0).
set -u
HOOK="$(dirname "$0")/secops_guard.py"

echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /"}}'        | python3 "$HOOK"; B=$?
echo '{"tool_name":"Bash","tool_input":{"command":"cat .env"}}'        | python3 "$HOOK"; C=$?
echo '{"tool_name":"Bash","tool_input":{"command":"ls -la src/"}}'     | python3 "$HOOK"; A=$?

if [ "$B" -eq 2 ] && [ "$C" -eq 2 ] && [ "$A" -eq 0 ]; then
  echo "GUARD OK (rm -rf blocked=$B, .env blocked=$C, ls allowed=$A)"
else
  echo "GUARD FAIL (rm -rf=$B, .env=$C, ls=$A)"; exit 1
fi
