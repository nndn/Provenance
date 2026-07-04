#!/bin/sh
# Install prov globally from local source as a uv tool (for local dev).
# Overwrites any existing provenance-cli tool install.
#
# Usage:
#   sh scripts/dev-install.sh
#
# Uninstall with: uv tool uninstall provenance-cli

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." 2>/dev/null && pwd)"

if ! command -v uv >/dev/null 2>&1; then
  echo "Error: uv required. Install from https://docs.astral.sh/uv/"
  exit 1
fi

echo "Installing provenance-cli from local source as a uv tool..."
uv tool install --force "$REPO_ROOT"
echo "Done. Run 'prov orient' to verify."
