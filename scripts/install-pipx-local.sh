#!/bin/sh
# spec: install-pipx-local
# Install current local build into pipx (for local dev). Overwrites any existing prov.
#
# Usage (from repo root or scripts/):
#   sh scripts/install-pipx-local.sh

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." 2>/dev/null && pwd)"

if ! command -v pipx >/dev/null 2>&1; then
  echo "Error: pipx required. Install with: brew install pipx && pipx ensurepath"
  exit 1
fi

echo "Installing provenance-cli from local source into pipx..."
pipx install -e "$REPO_ROOT" --force
echo "Done. Run 'prov orient' to verify."
