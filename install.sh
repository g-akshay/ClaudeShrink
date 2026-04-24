#!/usr/bin/env bash
set -e

SKILL_DIR="$HOME/.claude/skills/ClaudeShrink"
REPO_URL="https://github.com/g-akshay/ClaudeShrink.git"
VENV_DIR="$SKILL_DIR/.venv"

# ── 0. Detect OS ─────────────────────────────────────────────────────────────
OS="$(uname -s)"
case "$OS" in
  Darwin) OS_NAME="macOS" ;;
  Linux)  OS_NAME="Linux" ;;
  *)
    echo "ERROR: Unsupported OS '$OS'. ClaudeShrink supports macOS and Linux only." >&2
    echo "       Windows users: run this inside WSL (Ubuntu recommended)." >&2
    exit 1
    ;;
esac

echo "==> ClaudeShrink installer ($OS_NAME)"

# ── 1. Check Python 3 ────────────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
  echo "ERROR: python3 not found." >&2
  if [ "$OS_NAME" = "macOS" ]; then
    echo "       Install via Homebrew:  brew install python" >&2
    echo "       Or download from:      https://www.python.org/downloads/" >&2
  else
    echo "       Install via apt:       sudo apt install python3" >&2
    echo "       Or via dnf:            sudo dnf install python3" >&2
  fi
  exit 1
fi

PY_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')
PY_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
if [ "$PY_MAJOR" -lt 3 ] || [ "$PY_MINOR" -lt 9 ]; then
  echo "ERROR: Python 3.9+ required (found $(python3 --version))." >&2
  exit 1
fi

echo "    Python $(python3 --version) ✓"

# ── 1b. Ensure python3-venv and rsync are available (Linux gaps) ─────────────
if [ "$OS_NAME" = "Linux" ]; then
  MISSING_PKGS=""
  python3 -m venv --help &>/dev/null || MISSING_PKGS="$MISSING_PKGS python3-venv python3-pip"
  command -v rsync &>/dev/null        || MISSING_PKGS="$MISSING_PKGS rsync"

  if [ -n "$MISSING_PKGS" ]; then
    echo "==> Installing missing packages:$MISSING_PKGS"
    if command -v apt-get &>/dev/null; then
      sudo apt-get install -y $MISSING_PKGS
    elif command -v dnf &>/dev/null; then
      echo "ERROR: Run 'sudo dnf install$MISSING_PKGS' and retry." >&2; exit 1
    elif command -v pacman &>/dev/null; then
      echo "ERROR: Run 'sudo pacman -S$MISSING_PKGS' and retry." >&2; exit 1
    else
      echo "ERROR: Cannot install missing packages automatically. Install manually:$MISSING_PKGS" >&2; exit 1
    fi
  fi
fi

# ── 2. Clone or update skill (additive, never destructive) ───────────────────
mkdir -p "$HOME/.claude/skills"

if [ -d "$SKILL_DIR/.git" ]; then
  # Case A: already a git repo — just pull latest
  echo "==> Updating existing install at $SKILL_DIR"
  git -C "$SKILL_DIR" pull --ff-only

elif [ -d "$SKILL_DIR" ]; then
  # Case B: dir exists but is not a git repo (e.g. manually created)
  # Clone to a temp dir, copy skill files in additively, skip .venv
  echo "==> Directory exists without git. Merging latest files into $SKILL_DIR"
  TMP_DIR=$(mktemp -d)
  git clone --quiet "$REPO_URL" "$TMP_DIR"
  # rsync: update skill files, but never delete existing files or touch .venv
  rsync -a --exclude='.venv' --exclude='.git' "$TMP_DIR/" "$SKILL_DIR/"
  rm -rf "$TMP_DIR"

else
  # Case C: fresh install
  echo "==> Cloning into $SKILL_DIR"
  git clone "$REPO_URL" "$SKILL_DIR"
fi

# ── 3. Create isolated venv (skip if already exists) ─────────────────────────
if [ -d "$VENV_DIR" ]; then
  echo "==> Venv already exists at $VENV_DIR — skipping creation"
else
  echo "==> Creating virtual environment at $VENV_DIR"
  python3 -m venv "$VENV_DIR"
fi

# ── 4. Install dependencies ───────────────────────────────────────────────────
echo "==> Installing dependencies (this may take a while on first run)"
"$VENV_DIR/bin/pip" install --upgrade pip --quiet
"$VENV_DIR/bin/pip" install -r "$SKILL_DIR/requirements.txt"

echo ""
echo "✅ ClaudeShrink installed successfully."
echo "   Note: The phi-2 model (~5 GB) will be downloaded on first use."
echo "   Skill path:   $SKILL_DIR"
echo "   Script path:  $SKILL_DIR/scripts/compressor.py"
echo "   Venv path:    $VENV_DIR"
