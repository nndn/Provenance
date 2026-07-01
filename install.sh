#!/bin/sh
# Install Provenance (prov) — spec-driven development — into a project.
#
# Usage (from cloned repo):
#   sh /path/to/provenance/install.sh [target-dir]
#
# Options:
#   --no-hook     Skip pre-commit hook installation
#   --no-agent    Skip installing AGENTS.md and .agents/skills
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

if [ ! -f "$SELF_DIR/src/prov/cli.py" ]; then
  echo "Error: Run install.sh from the cloned Provenance repository."
  echo ""
  echo "  git clone <repo-url> /tmp/provenance"
  echo "  sh /tmp/provenance/install.sh [target-dir]"
  exit 1
fi
if [ -f "$SELF_DIR/src/prov/prompts/spec-agent.md" ]; then
  SOURCE_AGENT_MD="$SELF_DIR/src/prov/prompts/spec-agent.md"
else
  SOURCE_AGENT_MD="$SELF_DIR/agent.md"
fi
SOURCE_SKILLS_DIR="$SELF_DIR/src/prov/skills"
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

# Initialize CONTEXT.md
DEST_CONTEXT="$TARGET/prov/CONTEXT.md"
if [ -f "$DEST_CONTEXT" ] && [ "$FORCE" -eq 0 ]; then
  echo "  prov/CONTEXT.md     already exists (--force to overwrite)"
else
  cd "$TARGET" && PYTHONPATH="$SELF_DIR/src${PYTHONPATH:+:$PYTHONPATH}" "$PY" -m prov.cli init >/dev/null
  if [ -f "$DEST_CONTEXT" ]; then
    echo "  prov/CONTEXT.md     created (edit this next)"
  fi
fi

# Install agent prompt and skills
if [ "$INSTALL_AGENT" -eq 1 ]; then
  DEST_AGENT="$TARGET/AGENTS.md"
  if [ -f "$DEST_AGENT" ] && [ "$FORCE" -eq 0 ]; then
    echo "  AGENTS.md           already exists (--force to overwrite)"
  else
    cp "$SOURCE_AGENT_MD" "$DEST_AGENT"
    echo "  AGENTS.md           installed  (source: src/prov/prompts/spec-agent.md)"
  fi

  if [ -d "$SOURCE_SKILLS_DIR" ]; then
    DEST_SKILLS="$TARGET/.agents/skills"
    mkdir -p "$DEST_SKILLS"
    for skill_dir in "$SOURCE_SKILLS_DIR"/*; do
      [ -d "$skill_dir" ] || continue
      skill_name="$(basename "$skill_dir")"
      if [ -e "$DEST_SKILLS/$skill_name" ] && [ "$FORCE" -eq 0 ]; then
        echo "  .agents/skills/$skill_name already exists (--force to overwrite)"
      else
        rm -rf "$DEST_SKILLS/$skill_name"
        cp -R "$skill_dir" "$DEST_SKILLS/$skill_name"
        echo "  .agents/skills/$skill_name installed"
      fi
    done
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
echo "  2. Add AGENTS.md to your AI agent config"
echo "       Codex/GPT:  AGENTS.md is already installed"
echo "       Cursor:     use AGENTS.md or copy it into .cursor/rules/prov.md"
echo "       Claude:     copy or append AGENTS.md into CLAUDE.md"
echo "       Gemini:     copy or append AGENTS.md into .gemini/GEMINI.md"
echo ""
echo "     The canonical source lives at src/prov/prompts/spec-agent.md in the Provenance repo."
echo ""
echo "  3. Install/run the CLI"
if command -v prov >/dev/null 2>&1; then
  echo "       prov orient"
else
  echo "       pipx install provenance-cli"
  echo "       prov orient"
  echo ""
  echo "       From this cloned repo during development:"
  echo "       PYTHONPATH=\"$SELF_DIR/src\" $PY -m prov.cli orient"
fi
echo ""
echo "  4. Create your first domain file"
echo "       prov domain <name>    # after adding it to prov/CONTEXT.md"
echo ""
