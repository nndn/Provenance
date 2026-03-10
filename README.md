# Provenance

> Living requirements index + CLI for spec-driven development. Works with any AI agent.

**Provenance** (prov) keeps your requirements in plain markdown next to your code, gives you a CLI to query them, and teaches your AI agent to read before it writes.

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
# 1. Clone
git clone <this-repo-url> /tmp/provenance

# 2. Install into your project
cd /path/to/your-project
sh /tmp/provenance/install.sh

# 3. Edit prov/CONTEXT.md, then orient
python prov/prov.py orient
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

```sh
python prov/prov.py orient              # start every session here

python prov/prov.py scope <path>        # what governs this file or directory?
python prov/prov.py context <slug>      # full entry: statement, provenance, deps, code refs
python prov/prov.py impact <slug>       # blast radius before changing anything

python prov/prov.py find <keywords>     # search when you don't know the slug
python prov/prov.py domain <name>       # load a full domain

python prov/prov.py check-slug <slug>   # is this slug available?
python prov/prov.py write               # add entries (JSON input, validates before writing)

python prov/prov.py validate            # run before every commit — zero errors only
python prov/prov.py diff [ref]          # semantic change manifest vs HEAD or any ref
python prov/prov.py reconcile <path>    # detect code↔spec drift
python prov/prov.py rebuild             # rebuild .spec/ cache from files

python prov/prov.py init                # scaffold CONTEXT.md in a new project
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
