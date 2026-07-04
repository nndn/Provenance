# Install
> Distribution and setup: uv-first global install, prov init agent assets, spec-dir resolution, publishing to PyPI, docs.

## Constraints

C:python-39-min: prov runs on Python 3.9 or newer.
  > user: "Any agent or developer can run it without setup beyond Python."
  ~ pyproject.toml

## Requirements

install-uv-tool: The primary install is uv: `uv tool install provenance-cli` puts a global `prov` on PATH; project setup then runs `prov init` from the project root.
  > user: "Make sure we package this as a uv repo and use uv to publish package as a uv tool so that this cli could be installed globally easily"
  ~ README.md
  ~ pyproject.toml

install-pipx: pipx remains a supported fallback for a global install: `pipx install provenance-cli`.
  > user: "pipx isolates the CLI so it doesn't conflict with project dependencies."
  ~ README.md

install-pip: pip works into a virtualenv when uv and pipx are unavailable: `pip install provenance-cli`.
  > user: "pip works for users who manage dependencies with pip/venv."
  ~ README.md

project-bootstrap: `install.sh` is a thin bootstrap: it installs the prov CLI (uv tool, then pipx, then pip fallback), runs `prov init`, and installs the pre-commit hook when the target is a Git repo.
  > user: "install.sh bootstraps repo-local spec and agent files; the CLI itself is the installed prov command."
  @ agent-assets-install
  @ pre-commit-spec-validate
  ~ install.sh

agent-assets-install: `prov init` installs the four spec-* skills and the managed rules block for both agent standards — Claude (`.claude/skills/`, CLAUDE.md) and open (`.agents/skills/`, AGENTS.md) — idempotently, reporting per-file status (installed, up to date, outdated, updated).
  > user: "Install them for both claude standards and open standards that all other tools read"
  ~ src/prov/installer.py

rules-managed-block: Rules are written between `<!-- prov:agent-rules:start -->` / `<!-- prov:agent-rules:end -->` markers in CLAUDE.md and AGENTS.md; re-runs replace only the block, never surrounding user content; files with unbalanced or repeated markers are reported as damaged and never written.
  > inferred: idempotent re-install needs a bounded region to replace so user content in shared rules files stays untouched
  ! marker-block mechanism chosen by the agent during the 0.2 productionization — not explicitly confirmed by the user
  @ agent-assets-install
  ~ src/prov/installer.py

spec-dir-resolution: prov resolves the spec directory in order: (1) `$SPEC_DIR` env var; (2) the entry directory when it contains CONTEXT.md; (3) search upward from cwd for `prov/`, `spec/`, or `specs/` containing CONTEXT.md or .md files; (4) default `cwd/prov` (for `prov init` in a fresh project).
  > user: "Agent and user run prov from project root; spec dir is discovered automatically."
  ~ src/prov/spec_io.py

pypi-package-name: The PyPI package is named `provenance-cli` (the name `provenance` is taken on PyPI); the installed executable is `prov`.
  > user: "provenance is taken; provenance-cli is the published name."
  ~ pyproject.toml

publish-pypi-automated: Publishing to PyPI is automated via GitHub Actions when a release is published: `uv build` + `uv publish` with trusted publishing (no stored secrets).
  > user: "Create a release; the workflow builds and uploads to PyPI."
  ~ .github/workflows/publish-pypi.yml

publish-pypi-setup: One-time PyPI setup: create project `provenance-cli`, add trusted publisher (owner: nndn, repo: Provenance, workflow: publish-pypi.yml).
  > user: "Trusted publishing avoids storing API tokens in CI."
  ~ docs/publishing.md

publish-pypi-manual: Manual publish: `scripts/build.sh` then `scripts/publish.sh` (uv build / uv publish; requires UV_PUBLISH_TOKEN).
  > user: "Fallback when not using GitHub releases."
  ~ scripts/build.sh
  ~ scripts/publish.sh

dev-run-from-repo: Contributors run prov from this repo with `uv run prov <command>` from the repo root; the spec dir prov/ is discovered automatically; tests run with `uv run pytest`.
  > user: "I think we should be renaming specs to prov"
  @ spec-dir-resolution
  ~ docs/development.md

dev-install-local: Contributors install the current local build globally via `scripts/dev-install.sh` (uv tool install from source) so `prov` uses their edits without publishing.
  > user: "Local dev: test CLI changes without publishing to PyPI."
  ~ scripts/dev-install.sh

ci-test-matrix: CI runs the test suite with uv on Python 3.9 through 3.13 on every push and pull request.
  > derived: C:python-39-min — the supported floor must stay tested
  ~ .github/workflows/ci.yml

pre-commit-spec-validate: Projects can install a pre-commit hook via `scripts/install-spec-pre-commit.sh` that runs `prov validate` when staged spec markdown changes or staged `spec:` backlink changes are present; the hook detects the CLI with `prov --version` (bare-run fallback for pre-0.2 installs) and does not rebuild or stage `.spec/`.
  > user: "Validate staged spec markdown and staged spec: backlink changes on commit; do not rebuild or git add .spec by default."
  @ spec-validate
  ~ scripts/install-spec-pre-commit.sh

docs-section: User documentation lives in `docs/` — CLI reference, spec format, agent setup, publishing, development, architecture — with README.md as the uv-first quick start.
  > user: "What i want is a docs section where you can move all the docs"
  ~ docs/
  ~ README.md

## Out of scope

Custom installers (msi, deb, rpm). Homebrew formula. Chocolatey. These can be community-maintained.

## Refs

~ README.md
~ pyproject.toml
~ install.sh
~ scripts/
~ .github/workflows/
~ docs/
