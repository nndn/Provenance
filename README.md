# Provenance

> Living requirements index + CLI for spec-driven development. Works with any AI agent.

**Provenance** (prov) keeps your requirements in plain markdown next to your code, gives you a CLI to query them, and teaches your AI agent to read before it writes.

---

## Installation

**Requirements:** Python 3.9+

### Install the `prov` CLI

The primary supported path for new projects is a global `prov` command installed with `pipx`.

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
prov
```

Then initialize specs in a project:

```sh
cd /path/to/your-project
prov init
prov orient
```

To install a specific version:

```sh
pipx install 'provenance-cli==0.1.0'   # from PyPI
pipx install 'provenance-cli @ git+https://github.com/nndn/Provenance.git@v0.1.0'   # from GitHub
```

### Optional project bootstrap

After installing the global CLI, you can bootstrap a repository with the spec scaffold, agent instructions, skills, and pre-commit hook:

```sh
git clone https://github.com/nndn/Provenance.git /tmp/provenance
cd /path/to/your-project
sh /tmp/provenance/install.sh
```

This creates `prov/CONTEXT.md`, `AGENTS.md`, `.agents/skills/`, and the pre-commit hook when the target is a Git repo. Run with:

```sh
prov orient
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
| `prov` | Global CLI — scope, context, impact, validate, diff, write, reconcile |
| `prov/CONTEXT.md` | Project spec root — purpose, constraints, and domain map |
| `AGENTS.md` | Agent rules installed by `install.sh` for Codex/GPT-style agents |
| `.agents/skills/` | Agent skill instructions installed by `install.sh` |
| `scripts/install-spec-pre-commit.sh` | Optional Git hook — validates relevant staged changes |

No external dependencies. Python 3.9+. Everything is plain text — grep always works.

**Repo structure (for contributors):** CLI source lives in `src/prov/`, with a compatibility shim at `src/prov.py`. This repo's own spec (meta) is in `specs/`. User projects normally keep spec files in `prov/` and run the globally installed `prov`. For local dev with pipx: `sh scripts/install-pipx-local.sh` — installs current build into pipx so `prov` uses your edits.

---

## Quick start

```sh
# Install CLI globally
pipx install provenance-cli

# Initialize specs in your project
cd /path/to/your-project
prov init

# Then edit prov/CONTEXT.md and run
prov orient
```

After install:

```
your-project/
  prov/
    CONTEXT.md    ← edit this: project name, purpose, domain map
    <domain>.md   ← domain specs as you add them
```

If you use the optional project bootstrap, it also creates `AGENTS.md`, `.agents/skills/`, and the pre-commit hook when the target is a Git repo.

---

## Set up your AI agent

`install.sh` creates `AGENTS.md` for Codex/GPT-style agents and `.agents/skills/` for skill-aware agents. For other tools, copy or append `AGENTS.md` wherever the tool reads project instructions:

| Agent | Location |
|---|---|
| Cursor | `.cursorrules` or `.cursor/rules/prov.md` |
| Claude Code | `CLAUDE.md` |
| Codex / GPT | `AGENTS.md` |
| Any | append to your existing rules file |

Once the agent reads `AGENTS.md`, it will call `prov scope` before touching code, `prov validate` before committing, and `prov diff` for human review.

---

## CLI

Run `prov <command>`.

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
prov rebuild                   # regenerate optional .spec/ cache from files

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

When relevant changes are staged, the hook:
1. Detects staged spec markdown changes and staged `spec:` backlink changes
2. Runs `prov validate` — blocks commit on any error

The hook does not rebuild or stage `.spec/` by default. `.spec/` is a generated, optional cache; run `prov rebuild` explicitly when you want to refresh it.

---

## Adding a new domain

1. Create `prov/<domain>.md` with the standard structure (see above)
2. Add it to the `## Domain map` in `prov/CONTEXT.md`:
   ```
   auth  prov/auth.md
   ```
3. Run `prov orient` to verify it loads

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
}' | prov write --yes
```

### Directly in markdown

Edit the domain file. Follow the format above. Run `prov validate` when done.

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
