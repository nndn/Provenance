#!/bin/sh
# Install spec-driven development into a project.
#
# Usage (from cloned repo):
#   sh /path/to/spec-kit/install.sh [target-dir]
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

# Locate source files (source repo: src/spec.py; fallback for legacy layout)
if [ -f "$SELF_DIR/src/spec.py" ]; then
  SOURCE_SPEC_PY="$SELF_DIR/src/spec.py"
elif [ -f "$SELF_DIR/spec/spec.py" ]; then
  SOURCE_SPEC_PY="$SELF_DIR/spec/spec.py"
else
  echo "Error: Run install.sh from the cloned spec-kit repository."
  echo ""
  echo "  git clone <repo-url> /tmp/spec-kit"
  echo "  sh /tmp/spec-kit/install.sh [target-dir]"
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

echo "Installing spec-driven development"
echo "  Target:  $TARGET"
echo "  Python:  $($PY --version 2>&1)"
echo ""

# Create spec/ directory
mkdir -p "$TARGET/spec"

# Install spec.py
DEST_SPEC_PY="$TARGET/spec/spec.py"
if [ -f "$DEST_SPEC_PY" ] && [ "$FORCE" -eq 0 ]; then
  echo "  spec/spec.py        already exists (--force to overwrite)"
else
  cp "$SOURCE_SPEC_PY" "$DEST_SPEC_PY"
  chmod +x "$DEST_SPEC_PY"
  echo "  spec/spec.py        installed"
fi

# Initialize CONTEXT.md
DEST_CONTEXT="$TARGET/spec/CONTEXT.md"
if [ -f "$DEST_CONTEXT" ] && [ "$FORCE" -eq 0 ]; then
  echo "  spec/CONTEXT.md     already exists (--force to overwrite)"
else
  cd "$TARGET" && "$PY" spec/spec.py init >/dev/null 2>&1 || true
  if [ -f "$DEST_CONTEXT" ]; then
    echo "  spec/CONTEXT.md     created (edit this next)"
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
    SPEC_DIR="spec" ROOT="$TARGET" PYTHON="$PY" sh "$SOURCE_HOOK_SCRIPT" >/dev/null 2>&1
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
echo "  1. Edit spec/CONTEXT.md"
echo "       Add your project name, one-line summary, hard constraints, and domain map."
echo ""
echo "  2. Add agent.md to your AI agent config"
echo "       Cursor:     cp agent.md .cursorrules"
echo "                   or: cp agent.md .cursor/rules/spec.md"
echo "       Claude:     cp agent.md CLAUDE.md"
echo "       Gemini:     cp agent.md .gemini/GEMINI.md"
echo "       Any agent:  append agent.md to your AGENTS.md"
echo ""
echo "     The canonical source lives at prompts/spec-agent.md in the spec-kit repo."
echo ""
echo "  3. Run the CLI"
echo "       $PY spec/spec.py orient"
echo ""
echo "  4. Create your first domain file"
echo "       $PY spec/spec.py domain <name>    # after adding it to CONTEXT.md"
echo ""
