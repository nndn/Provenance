# Development

Contributor setup for the Provenance repo. The project is a uv-managed
package (hatchling build backend, typer CLI). Requires Python 3.9+ at
runtime; dev is pinned to 3.11 via `.python-version`.

## Setup

```sh
git clone https://github.com/nndn/Provenance.git
cd Provenance
uv sync                 # create .venv with the package + dev deps
uv run prov --help      # run the CLI from source
uv run pytest           # run the tests
uv build                # build sdist + wheel into dist/
```

To install your working tree globally as the `prov` tool:

```sh
sh scripts/dev-install.sh          # uv tool install --force <repo>
uv tool uninstall provenance-cli   # undo
```

CI (`.github/workflows/ci.yml`) runs `uv sync`, `uv run pytest`, and
`uv build` on every push and PR to main.

## Repo layout

```
src/prov/               the package
  cli.py                typer app; entry point (prov = prov.cli:main)
  commands/             one module per CLI command
  installer.py          installs packaged agent assets into repos
  spec_io.py            spec dir resolution, parsing, backend loading
  indexing.py           edges, code-backlink grep, reverse indexes
  model.py              Node/Context dataclasses
  format.py, writer.py  output formatting, spec file mutation
  skills/               packaged agent skills (4x SKILL.md)  ─┐
  rules/                packaged rules templates              ├─ installed by `prov init`
  prompts/              spec-agent prompt                    ─┘
tests/                  pytest suite
prov/                   this repo's own meta spec (Provenance documenting itself)
scripts/                build.sh, publish.sh, dev-install.sh, install-spec-pre-commit.sh
docs/                   this documentation
```

The markdown assets under `src/prov/skills/`, `src/prov/rules/`, and
`src/prov/prompts/` ship inside the wheel (hatchling includes package-dir
files by default) and are what `prov init` installs into user repos.

## The meta spec

This repo uses its own system: the spec lives in `prov/`. From the repo
root, `uv run prov orient` loads it. Follow the spec-driven flow when
contributing — `prov scope` before changing code, `prov validate` before
committing.

## Code style

Stdlib + typer only. Type hints throughout, terse docstrings, plain-print
output (no rich formatting in command output).
