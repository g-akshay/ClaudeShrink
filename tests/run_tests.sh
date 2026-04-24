#!/usr/bin/env bash
# tests/run_tests.sh
# Master test runner for ClaudeShrink.
#
# Usage:
#   bash tests/run_tests.sh            # all tests (unit + install)
#   bash tests/run_tests.sh --unit     # unit tests only (no install check)
#   bash tests/run_tests.sh --install  # install verification only

set -euo pipefail

SKILL_DIR="${CLAUDESHRINK_SKILL_DIR:-$HOME/.claude/skills/ClaudeShrink}"
VENV_PYTHON="$SKILL_DIR/.venv/bin/python"
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"

RUN_UNIT=true
RUN_INSTALL=true

for arg in "$@"; do
  case "$arg" in
    --unit)    RUN_INSTALL=false ;;
    --install) RUN_UNIT=false ;;
  esac
done

TOTAL_FAIL=0

# ── Unit tests (pytest, mocked) ───────────────────────────────────────────────
if [ "$RUN_UNIT" = true ]; then
  echo ""
  echo "══════════════════════════════════════════"
  echo " Running unit tests (mocked, no model)"
  echo "══════════════════════════════════════════"

  if [ ! -f "$VENV_PYTHON" ]; then
    echo "❌ venv not found at $VENV_PYTHON — run install.sh first"
    exit 1
  fi

  # Install pytest into venv if missing
  "$VENV_PYTHON" -m pytest --version &>/dev/null || \
    "$SKILL_DIR/.venv/bin/pip" install pytest --quiet

  "$VENV_PYTHON" -m pytest "$REPO_DIR/tests/test_compressor.py" -v || ((TOTAL_FAIL++))
fi

# ── Install verification (bash) ───────────────────────────────────────────────
if [ "$RUN_INSTALL" = true ]; then
  bash "$REPO_DIR/tests/test_install.sh" || ((TOTAL_FAIL++))
fi

# ── Final result ──────────────────────────────────────────────────────────────
echo ""
if [ "$TOTAL_FAIL" -eq 0 ]; then
  echo "✅ All test suites passed."
else
  echo "❌ $TOTAL_FAIL test suite(s) failed."
  exit 1
fi
