#!/bin/sh
# spec: pre-commit-spec-validate
# Install Provenance (prov) pre-commit hook.
#
# Validates when staged spec markdown changes or staged code diffs contain
# spec: backlinks. The hook never rebuilds or stages .spec/ cache files.
# Idempotent; safe to run multiple times.
#
# Usage:
#   ./scripts/install-spec-pre-commit.sh
#
# Override Python used by project-local/source fallbacks:
#   PYTHON=python3 ./scripts/install-spec-pre-commit.sh
#
# Override target repo root (used by install.sh):
#   ROOT=/path/to/project ./scripts/install-spec-pre-commit.sh

ROOT="${ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
HOOK="$ROOT/.git/hooks/pre-commit"

if [ ! -d "$ROOT/.git" ]; then
  echo "Error: $ROOT is not a git repository."
  exit 1
fi

mkdir -p "$ROOT/.git/hooks"

SHEBANG="#!/bin/sh"
EXISTING=""
if [ -f "$HOOK" ]; then
  first_line=$(sed -n '1p' "$HOOK")
  case "$first_line" in
    '#!'*) SHEBANG="$first_line" ;;
  esac

  # Preserve user hook content, but replace any Provenance-managed block from
  # this installer. The old_call branch removes legacy unmarked variants.
  EXISTING=$(
    awk '
      NR == 1 && $0 ~ /^#!/ { next }
      $0 == "# BEGIN Provenance pre-commit hook" { skip = 1; next }
      $0 == "# END Provenance pre-commit hook" { skip = 0; next }
      skip { next }
      old {
        if ($0 == "_prov_validate") {
          old = 0
          next
        }
        if ($0 == "if ! _prov_validate; then") {
          old_call = 1
          next
        }
        if (old_call && $0 == "fi") {
          old = 0
          old_call = 0
          next
        }
        next
      }
      /^# Provenance \(prov\):/ {
        first = $0
        if ((getline second) > 0) {
          if (second == "# Installed by scripts/install-spec-pre-commit.sh") {
            old = 1
            next
          }
          print first
          print second
          next
        }
        print first
        next
      }
      { print }
    ' "$HOOK"
  )
fi

printf '%s\n' "$SHEBANG" > "$HOOK"
cat >> "$HOOK" <<'HOOKSCRIPT'
# BEGIN Provenance pre-commit hook
# Provenance (prov): validate relevant staged spec/code changes.
# Installed by scripts/install-spec-pre-commit.sh

_prov_is_generated_spec_path() {
  case "$1" in
    prov/.spec/*|spec/.spec/*|specs/.spec/*) return 0 ;;
    *) return 1 ;;
  esac
}

_prov_is_spec_markdown_path() {
  _prov_is_generated_spec_path "$1" && return 1
  case "$1" in
    prov/*.md|spec/*.md|specs/*.md|prov/*.markdown|spec/*.markdown|specs/*.markdown)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

_prov_has_staged_spec_markdown() {
  git diff --cached --name-only -- |
    grep -E '^(prov|spec|specs)/.*\.(md|markdown)$' |
    grep -vE '^(prov|spec|specs)/\.spec/' >/dev/null 2>&1
}

_prov_has_staged_code_backlink_diff() {
  git diff --cached --name-only -- | (
    found=1
    while IFS= read -r path; do
      _prov_is_generated_spec_path "$path" && continue
      _prov_is_spec_markdown_path "$path" && continue

      if git diff --cached --unified=0 -- "$path" |
        grep -E '^[+-].*[sS][pP][eE][cC]:' |
        grep -vE '^(---|\+\+\+)' >/dev/null 2>&1
      then
        found=0
        break
      fi
    done
    exit "$found"
  )
}

_prov_should_validate() {
  _prov_has_staged_spec_markdown || _prov_has_staged_code_backlink_diff
}

_prov_find_python() {
  if [ -n "${PYTHON:-}" ] && command -v "$PYTHON" >/dev/null 2>&1; then
    command -v "$PYTHON"
    return 0
  fi
  if command -v python3 >/dev/null 2>&1; then
    command -v python3
    return 0
  fi
  if command -v python >/dev/null 2>&1; then
    command -v python
    return 0
  fi
  return 1
}

_prov_find_cli() {
  PROV_MODE=""
  PROV_CMD=""
  PROV_PYTHON=""
  PROV_SCRIPT=""

  if command -v prov >/dev/null 2>&1; then
    PROV_CMD=$(command -v prov)
    if "$PROV_CMD" >/dev/null 2>&1; then
      PROV_MODE="cmd"
      return 0
    fi
  fi

  if [ -x "$root/.venv/bin/prov" ] && "$root/.venv/bin/prov" >/dev/null 2>&1; then
    PROV_CMD="$root/.venv/bin/prov"
    PROV_MODE="cmd"
    return 0
  fi

  py=$(_prov_find_python) || return 1
  for script in \
    "$root/prov/prov.py" \
    "$root/prov/spec.py" \
    "$root/spec/prov.py" \
    "$root/spec/spec.py" \
    "$root/specs/prov.py" \
    "$root/specs/spec.py" \
    "$root/src/prov.py" \
    "$root/src/spec.py"
  do
    [ -f "$script" ] || continue
    if "$py" "$script" >/dev/null 2>&1; then
      PROV_PYTHON="$py"
      PROV_SCRIPT="$script"
      PROV_MODE="python"
      return 0
    fi
  done

  return 1
}

_prov_run_validate() {
  case "$PROV_MODE" in
    cmd)
      "$PROV_CMD" validate
      ;;
    python)
      "$PROV_PYTHON" "$PROV_SCRIPT" validate
      ;;
    *)
      return 127
      ;;
  esac
}

_prov_validate() {
  root=$(git rev-parse --show-toplevel)
  cd "$root" || exit 1

  _prov_should_validate || return 0

  if ! _prov_find_cli; then
    echo "prov validate is required for staged spec/backlink changes, but no runnable prov CLI was found." >&2
    echo "Checked: prov on PATH, $root/.venv/bin/prov, and project-local/source fallbacks." >&2
    exit 1
  fi

  echo "Running prov validate..."
  if ! _prov_run_validate; then
    echo "prov validate failed; fix all errors before committing." >&2
    exit 1
  fi
}

_prov_validate
# END Provenance pre-commit hook
HOOKSCRIPT

# Re-append any pre-existing hook content.
if [ -n "$EXISTING" ]; then
  printf "\n%s\n" "$EXISTING" >> "$HOOK"
fi

chmod +x "$HOOK"
echo "Installed Provenance pre-commit hook at $HOOK"
