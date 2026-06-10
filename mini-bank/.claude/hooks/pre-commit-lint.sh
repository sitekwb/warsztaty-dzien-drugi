#!/usr/bin/env bash
# pre-commit-lint.sh -- B1 bonus hook example.
# Refuse a commit if ruff finds lint errors in the staged Python.
# Exits non-zero (blocking the commit) when the tree does not lint clean.
set -euo pipefail

cd "$(git rev-parse --show-toplevel 2>/dev/null || echo .)"

if ! command -v ruff >/dev/null 2>&1; then
  echo "pre-commit-lint.sh: ruff not found; install with 'pip install ruff'." >&2
  exit 1
fi

if ! ruff check src tests; then
  echo "pre-commit-lint.sh: lint errors found; commit blocked." >&2
  exit 1
fi

echo "pre-commit-lint.sh: lint clean."
