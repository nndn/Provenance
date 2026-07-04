#!/bin/sh
# Bootstrap Provenance (prov) — spec-driven development — into a project.
#
# Runs from anywhere (no cloned repo needed):
#   sh install.sh [target-dir]
#   curl -fsSL https://raw.githubusercontent.com/nndn/Provenance/main/install.sh | sh
#
# Options:
#   --no-hook     Skip pre-commit hook installation
#   --no-agent    Skip installing agent assets (passed to prov init as --no-agents)
#   --force       Overwrite existing files (passed to prov init)

set -e

REPO_RAW_URL="https://raw.githubusercontent.com/nndn/Provenance/main"
SELF_DIR="$(cd "$(dirname "$0")" 2>/dev/null && pwd)"

TARGET="${PWD}"
INSTALL_HOOK=1
INIT_ARGS=""

for arg in "$@"; do
  case "$arg" in
    --no-hook)  INSTALL_HOOK=0 ;;
    --no-agent) INIT_ARGS="$INIT_ARGS --no-agents" ;;
    --force)    INIT_ARGS="$INIT_ARGS --force" ;;
    -*)         echo "Unknown option: $arg"; exit 1 ;;
    *)          TARGET="$(cd "$arg" && pwd)" ;;
  esac
done

# Ensure the prov CLI is installed.
if ! command -v prov >/dev/null 2>&1; then
  echo "prov not found; installing provenance-cli..."
  if command -v uv >/dev/null 2>&1; then
    uv tool install provenance-cli
  elif command -v pipx >/dev/null 2>&1; then
    pipx install provenance-cli
  elif command -v python3 >/dev/null 2>&1 && python3 -m pip --version >/dev/null 2>&1; then
    python3 -m pip install --user provenance-cli
  else
    echo "Error: no installer found. Install one of:"
    echo "  uv    https://docs.astral.sh/uv/  (then: uv tool install provenance-cli)"
    echo "  pipx  (then: pipx install provenance-cli)"
    echo "  pip   (then: python3 -m pip install --user provenance-cli)"
    exit 1
  fi
  if ! command -v prov >/dev/null 2>&1; then
    echo "Error: provenance-cli installed but 'prov' is not on PATH."
    echo "Add the installer's bin directory to PATH (e.g. 'uv tool update-shell'"
    echo "or 'pipx ensurepath'), then re-run this script."
    exit 1
  fi
fi

echo "Installing Provenance (prov)"
echo "  Target: $TARGET"
echo ""

# prov init handles prov/CONTEXT.md and all agent assets (AGENTS.md, skills, rules).
cd "$TARGET"
# shellcheck disable=SC2086  # INIT_ARGS is intentionally word-split
prov init $INIT_ARGS

# Install pre-commit hook (scripts/install-spec-pre-commit.sh).
if [ "$INSTALL_HOOK" -eq 1 ]; then
  if [ -d "$TARGET/.git" ]; then
    if [ -n "$SELF_DIR" ] && [ -f "$SELF_DIR/scripts/install-spec-pre-commit.sh" ]; then
      ROOT="$TARGET" sh "$SELF_DIR/scripts/install-spec-pre-commit.sh" >/dev/null
      echo "  .git/hooks/pre-commit installed"
    elif command -v curl >/dev/null 2>&1; then
      curl -fsSL "$REPO_RAW_URL/scripts/install-spec-pre-commit.sh" | ROOT="$TARGET" sh >/dev/null
      echo "  .git/hooks/pre-commit installed"
    else
      echo "  .git/hooks/pre-commit skipped (curl not found; run scripts/install-spec-pre-commit.sh manually)"
    fi
  else
    echo "  .git/hooks/pre-commit skipped (not a git repo)"
  fi
fi

echo ""
echo "Done. Next: edit prov/CONTEXT.md, then run 'prov orient'."
