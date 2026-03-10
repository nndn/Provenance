#!/bin/sh
# Install spec pre-commit hook.
#
# Detects Python automatically. Supports spec/ and specs/ directories.
# Idempotent — safe to run multiple times.
#
# Usage:
#   ./scripts/install-spec-pre-commit.sh
#
# Override Python:
#   PYTHON=python3 ./scripts/install-spec-pre-commit.sh
#
# Override target repo root (used by install.sh):
#   ROOT=/path/to/project ./scripts/install-spec-pre-commit.sh

ROOT="${ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
PY="${PYTHON:-python3}"

# Fallback to python if python3 not found
if ! command -v "$PY" >/dev/null 2>&1; then
  PY="python"
fi

HOOK="$ROOT/.git/hooks/pre-commit"

if [ ! -d "$ROOT/.git" ]; then
  echo "Error: $ROOT is not a git repository."
  exit 1
fi

mkdir -p "$ROOT/.git/hooks"

# Preserve any existing hook content by prepending
EXISTING=""
if [ -f "$HOOK" ]; then
  # Check if spec hook is already installed
  if grep -q "spec-driven development" "$HOOK" 2>/dev/null; then
    echo "Spec pre-commit hook already installed at $HOOK"
    exit 0
  fi
  EXISTING=$(cat "$HOOK")
fi

cat > "$HOOK" << HOOKSCRIPT
#!/bin/sh
# spec-driven development: validate and rebuild cache when spec files change.
# Installed by scripts/install-spec-pre-commit.sh

_spec_validate() {
  root=\$(git rev-parse --show-toplevel)
  cd "\$root" || exit 1

  if git diff --cached --name-only | grep -qE '^(spec|specs)/'; then
    if [ -f spec/spec.py ]; then
      spec_py="spec/spec.py"
      spec_dir=""
    elif [ -f specs/spec.py ]; then
      spec_py="specs/spec.py"
      spec_dir=""
    elif [ -f src/spec.py ]; then
      spec_py="src/spec.py"
      spec_dir="SPEC_DIR=specs"
    else
      return 0
    fi

    py="${PY}"
    if ! command -v "\$py" >/dev/null 2>&1; then
      py="python"
    fi

    printf "Running spec validate... "
    if ! eval \${spec_dir} "\$py" "\$spec_py" validate; then
      echo ""
      echo "spec validate failed — fix all errors before committing."
      exit 1
    fi

    eval \${spec_dir} "\$py" "\$spec_py" rebuild >/dev/null 2>&1 || true
    git add spec/.spec/ specs/.spec/ 2>/dev/null || true
  fi
}

_spec_validate
HOOKSCRIPT

# Re-append any pre-existing hook content
if [ -n "$EXISTING" ]; then
  printf "\n%s\n" "$EXISTING" >> "$HOOK"
fi

chmod +x "$HOOK"
echo "Installed spec pre-commit hook at $HOOK"
