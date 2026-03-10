# Install

> How to install the prov CLI, resolve the spec directory, and publish to PyPI.

## Constraints

C:python-39-min: prov requires Python 3.9+ standard library only; no external dependencies.

> "Any agent or developer can run it without setup beyond Python."

## Requirements

install-pipx: Users can install prov via pipx for isolated global install. Command: `pipx install provenance-cli` (PyPI) or `pipx install 'provenance-cli @ git+https://github.com/nndn/Provenance.git'` (GitHub).

> "pipx isolates the CLI so it doesn't conflict with project dependencies."
> ~ src/prov/spec_io.py
> ~ pyproject.toml

install-pip: Users can install prov via pip into a virtualenv or system. Command: `pip install provenance-cli` or `pip install 'provenance-cli @ git+https://github.com/nndn/Provenance.git'`.

> "pip works for users who manage dependencies with pip/venv."
> ~ pyproject.toml

install-project-local: Users can copy prov into a project via `install.sh`; creates `prov/prov.py` and `prov/CONTEXT.md`. Run with `python prov/prov.py <command>`.

> "Some users prefer to ship prov with the project; no global install."
> ~ install.sh

spec-dir-resolution: prov resolves the spec directory in order: (1) `$SPEC_DIR` env var; (2) entry script's parent if it contains CONTEXT.md or .md files; (3) search upward from cwd for `prov/`, `spec/`, or `specs/` containing CONTEXT.md or .md files; (4) default `cwd/prov` for `prov init`.

> "Agent and user run prov from project root; spec dir is discovered automatically."
> ~ src/prov/spec_io.py

pypi-package-name: The PyPI package is named `provenance-cli` (the name `provenance` is taken on PyPI).

> "provenance is taken; provenance-cli is the published name."

publish-pypi-automated: Publishing to PyPI is automated via GitHub Actions when a release is published. Workflow: `.github/workflows/publish-pypi.yml`. Uses trusted publishing (no stored secrets).

> "Create a release; the workflow builds and uploads to PyPI."

publish-pypi-setup: One-time PyPI setup: create account, create project `provenance-cli`, add trusted publisher (owner: nndn, repo: Provenance, workflow: publish-pypi.yml).

> "Trusted publishing avoids storing API tokens in CI."

publish-pypi-manual: Manual publish: `python -m build` then `twine upload dist/*`. Requires TWINE_USERNAME and TWINE_PASSWORD or API token.

> "Fallback when not using GitHub releases."

dev-run-from-repo: Contributors run prov from this repo by setting SPEC_DIR=specs and running `python src/prov.py <command>`, or by using install-pipx-local then `prov`.

> "Run from repo root; spec dir is specs/. Documented for contributors."
> ~ README.md

install-pipx-local: Contributors can install the current local build into pipx via `sh scripts/install-pipx-local.sh` (from repo root) so `prov` uses their edits without publishing.

> "Local dev: test CLI changes without publishing to PyPI."
> ~ scripts/install-pipx-local.sh

pre-commit-spec-validate: Projects can install a pre-commit hook via `scripts/install-spec-pre-commit.sh` that runs prov validate when files under prov/, spec/, or specs/ change; prevents committing with invalid spec.

> "Validate on commit so spec and code stay consistent."
> ~ scripts/install-spec-pre-commit.sh

## Out of scope

Custom installers (msi, deb, rpm). Homebrew formula. Chocolatey. These can be community-maintained.

## Refs

~ README.md
~ pyproject.toml
~ install.sh
~ .github/workflows/publish-pypi.yml
~ scripts/install-pipx-local.sh
~ scripts/install-spec-pre-commit.sh
