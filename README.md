# Provenance

> Living requirements index + CLI for spec-driven development. Works with any AI agent.

**Provenance** (prov) keeps your requirements in plain markdown next to your code, gives you a CLI to query them, and teaches your AI agent to read before it writes.

---

## Installation

**Requirements:** Python 3.9+

### Install the `prov` CLI (recommended)

Install from PyPI (after release) or GitHub:

| Platform | Command |
|----------|---------|
| **macOS / Linux / Windows (PyPI)** | `pipx install provenance-cli` |
| **macOS / Linux (GitHub)** | `pipx install 'provenance-cli @ git+https://github.com/nndn/Provenance.git'` |
| **Any (pip)** | `pip install provenance-cli` or `pip install 'provenance-cli @ git+https://github.com/nndn/Provenance.git'` |

**Recommendation:** Use [pipx](https://pypa.github.io/pipx/) for CLI tools — it installs `prov` in an isolated environment without affecting your project dependencies.

```sh
# Install pipx first (if needed)
# macOS:   brew install pipx && pipx ensurepath
# Linux:   apt install pipx  # or your package manager
# Windows: pip install pipx && pipx ensurepath

pipx install provenance-cli    # from PyPI (recommended)
# or, before release:
pipx install 'provenance-cli @ git+https://github.com/nndn/Provenance.git'
prov --help
```

To install a specific version:

```sh
pipx install 'provenance-cli==0.1.0'   # from PyPI
pipx install 'provenance-cli @ git+https://github.com/nndn/Provenance.git@v0.1.0'   # from GitHub
```

### Install into a project (copy prov into your repo)

If you prefer to copy the CLI into your project instead of a global install:

```sh
git clone https://github.com/nndn/Provenance.git /tmp/provenance
cd /path/to/your-project
sh /tmp/provenance/install.sh
```

This creates `prov/prov.py` and `prov/CONTEXT.md` in your project. Run with:

```sh
python prov/prov.py orient
```

---

## Publishing to PyPI

Releases are published automatically when you create a GitHub release. One-time setup:

1. Create an account at [pypi.org](https://pypi.org) and [test.pypi.org](https://test.pypi.org) (optional, for test releases).

2. Enable trusted publishing on PyPI:
   - Create a new project at pypi.org (name: `provenance-cli`) or use an existing one.
   - Go to **Your project** → **Publishing** → **Add a new pending publisher**.
   - Owner: `nndn`, Repository: `Provenance`, Workflow: `publish-pypi.yml`.

3. Create a release:
   ```sh
   git tag v0.1.0
   git push origin v0.1.0
   ```
   Then create the release on GitHub ( Releases → Create a new release → Choose the tag).

The workflow builds and publishes to PyPI on release publish.

**Manual publish:**
```sh
pip install build twine
python -m build
twine upload dist/*
```
(requires `TWINE_USERNAME` and `TWINE_PASSWORD` or API token.)

---

## What you get

| File | Purpose |
|---|---|
| `prov/prov.py` | CLI — scope, context, impact, validate, diff, write, reconcile |
| `agent.md` | Agent rules — drop into Cursor, Claude, or any agent config |
| `scripts/install-spec-pre-commit.sh` | Git hook — validates spec on every commit |

No external dependencies. Python 3.9+. Everything is plain text — grep always works.

**Repo structure (for contributors):** CLI source lives in `src/prov.py`. This repo's own spec (meta) is in `specs/`. After install, user projects get `prov/prov.py` (copied from `src/prov.py`) and use `prov/` for their spec files. To run the CLI from this repo: `SPEC_DIR=specs python src/prov.py <command>`.

---

## Quick start

```sh
# Option A: Install CLI globally (from GitHub)
pipx install provenance-cli

# Option B: Install into your project
git clone https://github.com/nndn/Provenance.git /tmp/provenance
cd /path/to/your-project
sh /tmp/provenance/install.sh

# Then: edit prov/CONTEXT.md (or prov/CONTEXT.md) and run
prov orient                    # if installed globally
# or
python prov/prov.py orient     # if using project-local copy
```

After install:

```
your-project/
  prov/
    CONTEXT.md    ← edit this: project name, purpose, domain map
    prov.py       ← the CLI
  agent.md        ← copy to your AI agent config
```

---

## Set up your AI agent

Copy `agent.md` to wherever your agent reads rules:

| Agent | Location |
|---|---|
| Cursor | `.cursorrules` or `.cursor/rules/prov.md` |
| Claude Code | `CLAUDE.md` |
| Codex / GPT | `AGENTS.md` |
| Any | append to your existing rules file |

Once the agent reads `agent.md`, it will automatically call `prov scope` before touching code, `prov validate` before committing, and `prov diff` for human review.

---

## CLI

Run `prov <command>` (if installed globally) or `python prov/prov.py <command>` (project-local).

```sh
prov orient                    # start every session here

prov scope <path>              # what governs this file or directory?
prov context <slug>            # full entry: statement, provenance, deps, code refs
prov impact <slug>             # blast radius before changing anything

prov find <keywords>           # search when you don't know the slug
prov domain <name>             # load a full domain

prov check-slug <slug>         # is this slug available?
prov write                     # add entries (JSON input, validates before writing)

prov validate                  # run before every commit — zero errors only
prov diff [ref]                # semantic change manifest vs HEAD or any ref
prov reconcile <path>          # detect code↔spec drift
prov rebuild                   # rebuild .spec/ cache from files

prov init                      # scaffold CONTEXT.md in a new project
```

---

## What a spec entry looks like

```
session-expiry: Sessions expire after 30 days of inactivity.
  > "standard session timeout, nothing crazy"
  ! assumed 30 days — "nothing crazy" is unconfirmed
  @ C:jwt-stateless
  ~ src/middleware/session.py:44
  ~ src/middleware/session.py:101
```

| Part | Meaning |
|---|---|
| `session-expiry` | Slug — permanent, globally unique, used in `spec:` backlinks in code |
| Statement | What the system does. Current state only. Never "previously", "changed from". |
| `>` | Provenance — user's words where possible. Required on every entry. |
| `!` | Assumption the agent filled in — needs user confirmation before removing. |
| `@` | This entry depends on another slug. |
| `~` | Code file implementing this. One line per file. |
| `[planned]` | Not yet coded. Remove when implemented, add `~` lines. |

**Node types (column 0):**

```
slug:      requirement — observable behavior
C:slug:    constraint  — non-negotiable rule
Q:slug:    question    — unresolved decision blocking implementation
```

### Domain file structure

```markdown
# Auth

> OAuth-based auth and stateless JWT sessions.

## Constraints

C:oauth-only: OAuth only — no email/password.

  > "I don't want to deal with password resets"

## Requirements

google-login: Users authenticate via Google OAuth.

  > "we'll just do Google login for now"
  > @ C:oauth-only
  > ~ src/api/auth/google.py

session-expiry: Sessions expire after 30 days of inactivity.

  > "standard session timeout, nothing crazy"
  ! assumed 30 days — unconfirmed
  @ C:jwt-stateless
  ~ src/middleware/session.py:44

## Open Questions

Q:admin-scope: Does admin-revoke apply to one session or all user sessions?

  > blocks: admin-revoke

## Out of scope

MFA, SSO/SAML.

## Refs

~ src/api/auth/
~ src/middleware/session.py
```

---

## Code backlinks

Every function or block that implements a spec entry carries a `spec:` comment:

```python
# spec: session-expiry
def refresh_session(token: str) -> Session: ...

# spec: billing-cap, C:usage-hard-limit
class PlanLimitMiddleware: ...
```

```typescript
// spec: admin-revoke
async function revokeSession(userId: string): Promise<void>
```

`prov validate` checks that every `spec:` slug in code has a matching entry. `prov reconcile` surfaces drift when code and spec get out of sync.

---

## Pre-commit hook

```sh
./scripts/install-spec-pre-commit.sh
```

When spec files are staged, the hook:
1. Runs `prov validate` — blocks commit on any error
2. Runs `prov rebuild` — regenerates `.spec/` cache
3. Stages `.spec/` automatically

---

## Adding a new domain

1. Create `prov/<domain>.md` with the standard structure (see above)
2. Add it to the `## Domain map` in `prov/CONTEXT.md`:
   ```
   auth  prov/auth.md
   ```
3. Run `python prov/prov.py orient` to verify it loads

---

## Writing new entries

### Via CLI (validated, shows preview)

```sh
echo '{
  "domain": "auth",
  "entries": [{
    "slug": "password-reset",
    "type": "requirement",
    "statement": "Users can reset their password via email link.",
    "provenance": "\"I need a forgot password flow\"",
    "planned": true
  }]
}' | python prov/prov.py write --yes
```

### Directly in markdown

Edit the domain file. Follow the format above. Run `python prov/prov.py validate` when done.

---

## CONTEXT.md structure

```markdown
# <Project Name>

> One sentence: what it does and who uses it.

## Purpose

2-3 sentences on the problem being solved.

## User goals

1. Primary goal
2. Secondary goal

## Hard constraints

C:example: Non-negotiable rule.

  > "why"

## Non-goals

- Explicit out-of-scope items

## Domain map

auth    prov/auth.md
billing prov/billing.md
```

---

## Commit message format

```sh
# Spec-only
prov(auth): add session-expiry requirement
prov(auth): implement admin-revoke, close Q:admin-scope
prov: reconcile src/api/

# Code + spec together (required)
feat(auth): implement session expiry
prov: implement session-expiry
```

---

## Validation checks

| Severity | Check | Meaning |
|---|---|---|
| ERROR | `ghost-scope` | Entry has no `>` line |
| ERROR | `dead-ref` | `~` path doesn't exist |
| ERROR | `phantom-slug` | `spec:` in code, no entry |
| ERROR | `duplicate-slug` | Same slug in two files |
| ERROR | `no-dangling-dep` | `@` target doesn't exist |
| WARN | `silent-impl` | `[planned]` but code has `spec:` |
| WARN | `orphan-question` | `Q:` not referenced by any `?` |

All ERRORs must be zero before committing.

---

## Fallback (no Python)

The spec is always greppable without any tooling:

```sh
grep -rh "^>" prov/*.md         # domain summaries
grep -r "^Q:" prov/             # open questions
grep -r "\[planned\]" prov/     # backlog
grep -r "^  !" prov/            # unconfirmed assumptions
grep -r "^C:" prov/             # all constraints
grep -A 20 "^session-expiry:" prov/  # entry by slug
grep -r "~src/api/auth" prov/   # what owns this path
```
