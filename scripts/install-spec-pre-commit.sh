#!/bin/sh
# Install Provenance (prov) pre-commit hook.
#
# Validates spec files when prov/, spec/, or specs/ change.
# Detects Python automatically. Supports prov/ and spec/ directories.
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
  if grep -q "Provenance\|spec-driven development" "$HOOK" 2>/dev/null; then
    echo "Provenance pre-commit hook already installed at $HOOK"
    exit 0
  fi
  EXISTING=$(cat "$HOOK")
fi

cat > "$HOOK" << HOOKSCRIPT
#!/bin/sh
# Provenance (prov): validate and rebuild cache when spec files change.
# Installed by scripts/install-spec-pre-commit.sh

_prov_validate() {
  root=\$(git rev-parse --show-toplevel)
  cd "\$root" || exit 1

  if git diff --cached --name-only | grep -qE '^(prov|spec|specs)/'; then
    if [ -f prov/prov.py ]; then
      prov_py="prov/prov.py"
      prov_dir=""
    elif [ -f spec/prov.py ]; then
      prov_py="spec/prov.py"
      prov_dir=""
    elif [ -f spec/spec.py ]; then
      prov_py="spec/spec.py"
      prov_dir=""
    elif [ -f specs/prov.py ]; then
      prov_py="specs/prov.py"
      prov_dir=""
    elif [ -f specs/spec.py ]; then
      prov_py="specs/spec.py"
      prov_dir=""
    elif [ -f src/prov.py ]; then
      prov_py="src/prov.py"
      prov_dir="SPEC_DIR=specs"
    elif [ -f src/spec.py ]; then
      prov_py="src/spec.py"
      prov_dir="SPEC_DIR=specs"
    else
      return 0
    fi

    py="${PY}"
    if ! command -v "\$py" >/dev/null 2>&1; then
      py="python"
    fi

    printf "Running prov validate... "
    if ! eval \${prov_dir} "\$py" "\$prov_py" validate; then
      echo ""
      echo "prov validate failed — fix all errors before committing."
      exit 1
    fi

    eval \${prov_dir} "\$py" "\$prov_py" rebuild >/dev/null 2>&1 || true
    git add prov/.spec/ spec/.spec/ specs/.spec/ 2>/dev/null || true
  fi
}

_prov_validate
HOOKSCRIPT

# Re-append any pre-existing hook content
if [ -n "$EXISTING" ]; then
  printf "\n%s\n" "$EXISTING" >> "$HOOK"
fi

chmod +x "$HOOK"
echo "Installed Provenance pre-commit hook at $HOOK"
