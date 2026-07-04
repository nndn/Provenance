#!/bin/sh
# Build and publish provenance-cli to PyPI with uv.
#
# Usage:
#   UV_PUBLISH_TOKEN=pypi-... sh scripts/publish.sh
#
# To publish to TestPyPI instead, add a [[tool.uv.index]] named "testpypi"
# to pyproject.toml and run: uv publish --index testpypi

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." 2>/dev/null && pwd)"
cd "$REPO_ROOT"

if [ -z "${UV_PUBLISH_TOKEN:-}" ]; then
  echo "Error: UV_PUBLISH_TOKEN is not set."
  echo ""
  echo "Create an API token at https://pypi.org/manage/account/token/ then:"
  echo "  UV_PUBLISH_TOKEN=pypi-... sh scripts/publish.sh"
  exit 1
fi

rm -rf dist
uv build
uv publish
