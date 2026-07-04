# Agent setup

`prov init` teaches your AI agent spec-driven development by installing the
same assets for two agent standards. Everything is installed from files
packaged inside `provenance-cli` — no network access, no cloned repo needed.

## What gets installed

| Standard | Skills | Rules |
|---|---|---|
| Claude (Claude Code) | `.claude/skills/<name>/SKILL.md` | Managed block in `CLAUDE.md` |
| Open (Codex/GPT-style, skill-aware agents) | `.agents/skills/<name>/SKILL.md` | Managed block in `AGENTS.md` |

Both standards receive identical content. Four skills are installed:

| Skill | Purpose |
|---|---|
| `spec-request-flow` | The six-phase request flow — understand, clarify, propose, write spec, implement, sync |
| `spec-capture-expectations` | Extract implicit user expectations and compile them into the spec |
| `spec-entry-format` | Node types, sigils, provenance, backlinks, commit messages |
| `spec-drift-sync` | Resolve spec<->code drift with user-confirmed fixes |

The rules block gives the agent the core laws (read before write, `!` for
every filled gap, `>` provenance on every entry, spec and code in the same
commit, validate before commit) and a routing table pointing at the
installed skills.

## The managed rules block

Rules are written between HTML-comment markers:

```
<!-- prov:agent-rules:start -->
...managed content...
<!-- prov:agent-rules:end -->
```

- If `CLAUDE.md` / `AGENTS.md` does not exist, it is created with the block.
- If it exists without markers, the block is appended after your content.
- If markers exist, only the content between them is replaced in place.

User content outside the markers is never touched. Rules block updates never
require `--force` — the block is managed content. `--force` applies only to
skill files: a locally modified skill reports `outdated (--force to update)`
and is left alone unless forced.

## Flags

```
prov init                 # scaffold prov/CONTEXT.md + install both standards
prov init --check         # status report, writes nothing; exit 1 if anything missing/outdated
prov init --force         # overwrite locally modified skill files
prov init --no-agents     # CONTEXT.md only
prov init --no-claude     # skip .claude/skills/ and CLAUDE.md
prov init --no-open       # skip .agents/skills/ and AGENTS.md
```

Re-running `prov init` is idempotent — up-to-date assets report `up to date`
and after a `prov` upgrade it refreshes the rules block and reports which
skills are outdated.

## Self-heal

The installed rules include a self-heal instruction: once per session at
session start — never on every turn — the agent verifies the prov skills
are installed (`.claude/skills/spec-*` or `.agents/skills/spec-*`). If
missing, it runs `prov init` to restore them; if the `prov` CLI itself is
missing, it installs it with `uv tool install provenance-cli` (or
pipx/pip), then continues with the task.

## Other tools

Any tool that reads `AGENTS.md` picks the rules up directly. For tools with
their own rules location (e.g. Cursor's `.cursorrules` or
`.cursor/rules/`), point them at `AGENTS.md` or copy the managed block into
the tool's rules file.

Once the agent reads the rules, it calls `prov scope` before touching code,
`prov validate` before committing, and `prov diff` for human review.

## Pre-commit hook

```sh
./scripts/install-spec-pre-commit.sh
```

Installs a `pre-commit` hook that runs `prov validate` when the staged
changes are relevant — staged spec markdown under `prov/`, `spec/`, or
`specs/`, or staged code diffs containing `spec:` backlinks — and blocks
the commit on any error. Irrelevant commits are untouched.

- Idempotent; safe to run multiple times. Existing hook content is preserved
  and the Provenance-managed block is replaced on reinstall.
- The hook never rebuilds or stages `.spec/` — run `prov rebuild` explicitly
  when you want to refresh the optional cache.
- `ROOT=/path/to/project` overrides the target repo; `PYTHON=python3`
  overrides the interpreter used by fallbacks.

## One-shot bootstrap

`install.sh` (runnable from anywhere, including `curl | sh`) installs the
`prov` CLI if missing (uv, then pipx, then pip), runs `prov init` in the
target directory, and installs the pre-commit hook when the target is a git
repo:

```sh
curl -fsSL https://raw.githubusercontent.com/nndn/Provenance/main/install.sh | sh
```

Options: `--no-hook`, `--no-agent`, `--force`.
