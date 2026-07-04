# Provenance

> Living requirements index + CLI for spec-driven development. Works with any AI agent.

**Provenance** (`prov`) keeps your requirements in plain markdown next to your
code, gives you a CLI to query them, and teaches your AI agent to read before
it writes. The spec files are always the source of truth — everything is plain
text, and grep always works.

## Install

Requires Python 3.9+.

```sh
uv tool install provenance-cli     # recommended
```

Alternates:

```sh
pipx install provenance-cli
pip install provenance-cli
```

## Quick start

```sh
cd /path/to/your-project
prov init          # scaffold prov/CONTEXT.md + install agent skills/rules
# edit prov/CONTEXT.md: project name, purpose, constraints, domain map
prov orient        # verify — start every session here
```

After init:

```
your-project/
  prov/
    CONTEXT.md     ← edit this
    <domain>.md    ← domain specs as you add them
  .claude/skills/  + CLAUDE.md block   ← agent assets (Claude standard)
  .agents/skills/  + AGENTS.md block   ← agent assets (open standard)
```

## CLI

| Command | Purpose |
|---|---|
| `prov orient` | Project overview — start every session here |
| `prov scope <path>` | What governs this file or directory? |
| `prov context <slug>` | Full entry: statement, provenance, deps, code refs |
| `prov impact <slug>` | Blast radius before changing anything |
| `prov find <keywords>` | Search when you don't know the slug |
| `prov domain <name>` | Load a full domain |
| `prov validate` | Run before every commit — zero errors only |
| `prov check-slug <slug>` | Is this slug available? |
| `prov reconcile <path>` | Detect code<->spec drift (read-only) |
| `prov sync [path]` | Drift report + patch sub-commands to fix it |
| `prov rebuild` | Regenerate the optional `.spec/` cache |
| `prov write` | Add entries from JSON (validates before writing) |
| `prov diff [ref]` | Semantic change manifest vs HEAD or any ref |
| `prov init` | Scaffold CONTEXT.md + agent assets |

Full reference with flags and exit codes: [docs/cli.md](docs/cli.md).

## What a spec entry looks like

```
session-expiry: Sessions expire after 30 days of inactivity.
  > inferred: user said "standard session timeout, nothing crazy"
  ! assumed 30 days — unconfirmed
  @ C:jwt-stateless
  ~ src/middleware/session.py:44
```

A slug, a current-state statement, provenance (`>`), agent assumptions (`!`),
dependencies (`@`), and code refs (`~`). Code links back with `# spec:
session-expiry` comments; `prov validate` checks both directions. Full format
— node types, sigils, provenance source types, validation checks, grep
patterns: [docs/spec-format.md](docs/spec-format.md).

## Agent setup

`prov init` installs the same skills and rules for both agent standards:
`.claude/skills/` plus a managed block in `CLAUDE.md` (Claude Code), and
`.agents/skills/` plus a managed block in `AGENTS.md` (Codex/GPT-style and
other skill-aware agents; tools like Cursor can point at `AGENTS.md`). The
rules teach the agent to run `prov scope` before touching code and
`prov validate` before committing, and to self-heal missing skills once per
session. Details, the marker-block behavior, and the optional pre-commit
hook: [docs/agent-setup.md](docs/agent-setup.md).

## Docs

| Page | Contents |
|---|---|
| [docs/cli.md](docs/cli.md) | Full command reference |
| [docs/spec-format.md](docs/spec-format.md) | The spec DSL, validation, grep fallback |
| [docs/agent-setup.md](docs/agent-setup.md) | Agent assets, managed blocks, pre-commit hook |
| [docs/architecture.md](docs/architecture.md) | Complete technical specification |
| [docs/publishing.md](docs/publishing.md) | Release and publishing flow |
| [docs/development.md](docs/development.md) | Contributor setup and repo layout |

## License

MIT — see [LICENSE](LICENSE). Contributing: see
[docs/development.md](docs/development.md).
