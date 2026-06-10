#!/usr/bin/env bash
# forbid-prod-data.sh -- B1 bonus hook example.
# Block any edit whose content looks like real production banking data:
# full 26-digit Polish IBANs, PESEL national-IDs, or a prod-connection marker.
# Exits non-zero (blocking the edit) when such a pattern is found.
set -euo pipefail

FILE="${1:?usage: forbid-prod-data.sh <file>}"

if [ ! -f "$FILE" ]; then
  exit 0
fi

# PL IBAN (PL + 26 digits), 11-digit PESEL, or an explicit prod DSN marker.
if grep -E -q '(PL[0-9]{26})|([^0-9][0-9]{11}[^0-9])|(prod[-_]?(db|dsn|conn))' "$FILE"; then
  echo "forbid-prod-data.sh: production-data pattern detected in $FILE; edit blocked." >&2
  echo "Use synthetic fixtures, never real customer data, in the workshop repo." >&2
  exit 1
fi

echo "forbid-prod-data.sh: no production-data pattern in $FILE."
