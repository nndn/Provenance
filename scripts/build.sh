#!/bin/sh
# Build sdist + wheel into dist/ with uv.
#
# Usage:
#   sh scripts/build.sh

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." 2>/dev/null && pwd)"
cd "$REPO_ROOT"

rm -rf dist
uv build

echo ""
echo "Artifacts:"
ls -l dist
