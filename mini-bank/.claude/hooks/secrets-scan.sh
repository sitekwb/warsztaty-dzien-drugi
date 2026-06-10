#!/usr/bin/env bash
# Refuse edits if a candidate string smells like a secret.
# Demonstrated in B1 as a hook-vs-text-rule example.
set -e
if grep -E '(api[_-]?key|secret|password|token)[[:space:]]*[:=][[:space:]]*["'\''"][^"'\''"]+["'\''"]' "$1" 2>/dev/null; then
  echo "secrets-scan.sh: candidate secret detected; aborting." >&2
  exit 1
fi
