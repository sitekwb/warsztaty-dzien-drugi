#!/usr/bin/env bash
# audit-log.sh -- B1 bonus hook example.
# Append an audit line for every agent file edit, so there is a durable trail
# of what the agent touched. Demonstrates a hook that ENFORCES (does not just
# suggest) record-keeping: it exits non-zero if the audit log is not writable.
set -euo pipefail

TARGET="${1:-<unknown>}"
LOG="${MINIBANK_AUDIT_LOG:-.claude/audit.log}"

mkdir -p "$(dirname "$LOG")"

if ! touch "$LOG" 2>/dev/null; then
  echo "audit-log.sh: cannot write audit log at $LOG; aborting." >&2
  exit 1
fi

printf '%s\t%s\t%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "${USER:-agent}" "$TARGET" >>"$LOG"
echo "audit-log.sh: recorded edit to $TARGET"
