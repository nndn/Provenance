#!/bin/sh
# Install Provenance (prov) — spec-driven development — into a project.
#
# Usage (from cloned repo):
#   sh /path/to/provenance/install.sh [target-dir]
#
# Options:
#   --no-hook     Skip pre-commit hook installation
#   --no-agent    Skip copying agent.md
#   --force       Overwrite existing files

set -e

SELF_DIR="$(cd "$(dirname "$0")" 2>/dev/null && pwd)"

TARGET="${PWD}"
INSTALL_HOOK=1
INSTALL_AGENT=1
FORCE=0

for arg in "$@"; do
  case "$arg" in
    --no-hook)  INSTALL_HOOK=0 ;;
    --no-agent) INSTALL_AGENT=0 ;;
    --force)    FORCE=1 ;;
    -*)         echo "Unknown option: $arg"; exit 1 ;;
    *)          TARGET="$(cd "$arg" && pwd)" ;;
  esac
done

# Locate source files (source repo: src/prov.py; fallback for legacy layout)
if [ -f "$SELF_DIR/src/prov.py" ]; then
  SOURCE_PROV_PY="$SELF_DIR/src/prov.py"
elif [ -f "$SELF_DIR/src/spec.py" ]; then
  SOURCE_PROV_PY="$SELF_DIR/src/spec.py"
elif [ -f "$SELF_DIR/spec/spec.py" ]; then
  SOURCE_PROV_PY="$SELF_DIR/spec/spec.py"
else
  echo "Error: Run install.sh from the cloned Provenance repository."
  echo ""
  echo "  git clone <repo-url> /tmp/provenance"
  echo "  sh /tmp/provenance/install.sh [target-dir]"
  exit 1
fi
if [ -f "$SELF_DIR/prompts/spec-agent.md" ]; then
  SOURCE_AGENT_MD="$SELF_DIR/prompts/spec-agent.md"
else
  SOURCE_AGENT_MD="$SELF_DIR/agent.md"
fi
SOURCE_HOOK_SCRIPT="$SELF_DIR/scripts/install-spec-pre-commit.sh"

# Require Python 3.9+
PY="${PYTHON:-python3}"
if ! command -v "$PY" >/dev/null 2>&1; then
  PY="python"
fi
if ! "$PY" -c "import sys; assert sys.version_info >= (3,9)" 2>/dev/null; then
  echo "Error: Python 3.9+ required. Set PYTHON= to override."
  exit 1
fi

echo "Installing Provenance (prov)"
echo "  Target:  $TARGET"
echo "  Python:  $($PY --version 2>&1)"
echo ""

# Create prov/ directory
mkdir -p "$TARGET/prov"

# Install prov.py
DEST_PROV_PY="$TARGET/prov/prov.py"
if [ -f "$DEST_PROV_PY" ] && [ "$FORCE" -eq 0 ]; then
  echo "  prov/prov.py        already exists (--force to overwrite)"
else
  cp "$SOURCE_PROV_PY" "$DEST_PROV_PY"
  chmod +x "$DEST_PROV_PY"
  echo "  prov/prov.py        installed"
fi

# Initialize CONTEXT.md
DEST_CONTEXT="$TARGET/prov/CONTEXT.md"
if [ -f "$DEST_CONTEXT" ] && [ "$FORCE" -eq 0 ]; then
  echo "  prov/CONTEXT.md     already exists (--force to overwrite)"
else
  cd "$TARGET" && "$PY" prov/prov.py init >/dev/null 2>&1 || true
  if [ -f "$DEST_CONTEXT" ]; then
    echo "  prov/CONTEXT.md     created (edit this next)"
  fi
fi

# Install agent prompt
if [ "$INSTALL_AGENT" -eq 1 ]; then
  DEST_AGENT="$TARGET/agent.md"
  if [ -f "$DEST_AGENT" ] && [ "$FORCE" -eq 0 ]; then
    echo "  agent.md            already exists (--force to overwrite)"
  else
    cp "$SOURCE_AGENT_MD" "$DEST_AGENT"
    echo "  agent.md            installed  (source: prompts/spec-agent.md)"
  fi
fi

# Install pre-commit hook
if [ "$INSTALL_HOOK" -eq 1 ]; then
  if [ -d "$TARGET/.git" ]; then
    SPEC_DIR="prov" ROOT="$TARGET" PYTHON="$PY" sh "$SOURCE_HOOK_SCRIPT" >/dev/null 2>&1
    echo "  .git/hooks/pre-commit installed"
  else
    echo "  .git/hooks/pre-commit skipped (not a git repo)"
  fi
fi

echo ""
echo "Done."
echo ""
echo "Next steps:"
echo ""
echo "  1. Edit prov/CONTEXT.md"
echo "       Add your project name, one-line summary, hard constraints, and domain map."
echo ""
echo "  2. Add agent.md to your AI agent config"
echo "       Cursor:     cp agent.md .cursorrules"
echo "                   or: cp agent.md .cursor/rules/prov.md"
echo "       Claude:     cp agent.md CLAUDE.md"
echo "       Gemini:     cp agent.md .gemini/GEMINI.md"
echo "       Any agent:  append agent.md to your AGENTS.md"
echo ""
echo "     The canonical source lives at prompts/spec-agent.md in the Provenance repo."
echo ""
echo "  3. Run the CLI"
echo "       $PY prov/prov.py orient"
echo ""
echo "  4. Create your first domain file"
echo "       $PY prov/prov.py domain <name>    # after adding it to CONTEXT.md"
echo ""
