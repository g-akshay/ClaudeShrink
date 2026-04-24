#!/usr/bin/env bash
# tests/test_install.sh
# Verifies that the ClaudeShrink install is structurally correct.
# Run after install.sh completes. No model download triggered.
#
# Usage:
#   bash tests/test_install.sh
#   bash tests/test_install.sh --skill-dir /custom/path   # override path

set -euo pipefail

SKILL_DIR="${CLAUDESHRINK_SKILL_DIR:-$HOME/.claude/skills/ClaudeShrink}"
VENV_PYTHON="$SKILL_DIR/.venv/bin/python"
SCRIPT="$SKILL_DIR/scripts/compressor.py"

PASS=0
FAIL=0
FAILURES=()

pass() { echo "  ✅ $1"; PASS=$((PASS+1)); true; }
fail() { echo "  ❌ $1"; FAILURES+=("$1"); FAIL=$((FAIL+1)); true; }

echo ""
echo "══════════════════════════════════════════"
echo " ClaudeShrink Install Verification"
echo " Skill dir: $SKILL_DIR"
echo "══════════════════════════════════════════"
echo ""

# ── Structure ────────────────────────────────────────────────────────────────
echo "▶ Structure"

[ -d "$SKILL_DIR" ]                    && pass "Skill dir exists"          || fail "Skill dir missing: $SKILL_DIR"
[ -f "$SKILL_DIR/SKILL.md" ]           && pass "SKILL.md present"          || fail "SKILL.md missing"
[ -f "$SKILL_DIR/install.sh" ]         && pass "install.sh present"        || fail "install.sh missing"
[ -f "$SKILL_DIR/requirements.txt" ]   && pass "requirements.txt present"  || fail "requirements.txt missing"
[ -f "$SCRIPT" ]                       && pass "compressor.py present"     || fail "compressor.py missing at $SCRIPT"

# ── Venv ─────────────────────────────────────────────────────────────────────
echo ""
echo "▶ Virtual Environment"

[ -d "$SKILL_DIR/.venv" ]              && pass ".venv dir exists"          || fail ".venv missing — run install.sh"
[ -f "$VENV_PYTHON" ]                  && pass "venv python executable"    || fail "venv python not found at $VENV_PYTHON"
[ -x "$VENV_PYTHON" ]                  && pass "venv python is executable" || fail "venv python not executable"

# ── Dependencies ──────────────────────────────────────────────────────────────
echo ""
echo "▶ Python Dependencies"

check_import() {
  local pkg="$1"
  if "$VENV_PYTHON" -c "import $pkg" 2>/dev/null; then
    pass "$pkg importable"
  else
    fail "$pkg not installed in venv"
  fi
}

check_import llmlingua
check_import torch
check_import transformers
check_import accelerate

# ── Script smoke test ─────────────────────────────────────────────────────────
echo ""
echo "▶ Script Smoke Test"

# Missing file → should exit 1 with error on stderr
MISSING_OUTPUT=$("$VENV_PYTHON" "$SCRIPT" /nonexistent/path/file.txt 2>&1 || true)
if echo "$MISSING_OUTPUT" | grep -qi "error\|not found"; then
  pass "Missing file → non-zero exit with error message"
else
  fail "Missing file → unexpected output: $MISSING_OUTPUT"
fi

# Empty input → should exit 1 with error
EMPTY_OUTPUT=$(echo "" | "$VENV_PYTHON" "$SCRIPT" 2>&1 || true)
if echo "$EMPTY_OUTPUT" | grep -qi "error"; then
  pass "Empty stdin → non-zero exit with error message"
else
  fail "Empty stdin → unexpected output: $EMPTY_OUTPUT"
fi

# ── SKILL.md frontmatter ──────────────────────────────────────────────────────
echo ""
echo "▶ SKILL.md Frontmatter"

SKILL_FILE="$SKILL_DIR/SKILL.md"
grep -q "^name:" "$SKILL_FILE"        && pass "name field present"        || fail "name field missing in SKILL.md"
grep -q "^version:" "$SKILL_FILE"     && pass "version field present"     || fail "version field missing in SKILL.md"
grep -q "^author:" "$SKILL_FILE"      && pass "author field present"      || fail "author field missing in SKILL.md"
grep -q "^description:" "$SKILL_FILE" && pass "description field present" || fail "description field missing in SKILL.md"
grep -q "^tags:" "$SKILL_FILE"        && pass "tags field present"        || fail "tags field missing in SKILL.md"
grep -q "allowed-tools:" "$SKILL_FILE" && pass "allowed-tools present"    || fail "allowed-tools missing in SKILL.md"

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "══════════════════════════════════════════"
if [ $FAIL -eq 0 ]; then
  echo " ✅ All $PASS checks passed."
else
  echo " ❌ $FAIL check(s) failed, $PASS passed."
  echo ""
  for f in "${FAILURES[@]}"; do
    echo "    - $f"
  done
  exit 1
fi
echo "══════════════════════════════════════════"
echo ""
