# spec

> Living requirements index + CLI for spec-driven development. Works with any AI agent.

`spec` keeps your requirements in plain markdown next to your code, gives you a CLI to query them, and teaches your AI agent to read before it writes.

---

## What you get

| File | Purpose |
|---|---|
| `spec/spec.py` | CLI — scope, context, impact, validate, diff, write, reconcile |
| `agent.md` | Agent rules — drop into Cursor, Claude, or any agent config |
| `scripts/install-spec-pre-commit.sh` | Git hook — validates spec on every commit |

No external dependencies. Python 3.9+. Everything is plain text — grep always works.

**Repo structure (for contributors):** CLI source lives in `src/spec.py`. This repo's own spec (meta) is in `specs/`. After install, user projects get `spec/spec.py` (copied from `src/spec.py`) and use `spec/` for their spec files. To run the CLI from this repo: `SPEC_DIR=specs python src/spec.py <command>`.

---

## Quick start

```sh
# 1. Clone
git clone <this-repo-url> /tmp/spec-kit

# 2. Install into your project
cd /path/to/your-project
sh /tmp/spec-kit/install.sh

# 3. Edit spec/CONTEXT.md, then orient
python spec/spec.py orient
```

After install:

```
your-project/
  spec/
    CONTEXT.md    ← edit this: project name, purpose, domain map
    spec.py       ← the CLI
  agent.md        ← copy to your AI agent config
```

---

## Set up your AI agent

Copy `agent.md` to wherever your agent reads rules:

| Agent | Location |
|---|---|
| Cursor | `.cursorrules` or `.cursor/rules/spec.md` |
| Claude Code | `CLAUDE.md` |
| Codex / GPT | `AGENTS.md` |
| Any | append to your existing rules file |

Once the agent reads `agent.md`, it will automatically call `spec scope` before touching code, `spec validate` before committing, and `spec diff` for human review.

---

## CLI

```sh
python spec/spec.py orient              # start every session here

python spec/spec.py scope <path>        # what governs this file or directory?
python spec/spec.py context <slug>      # full entry: statement, provenance, deps, code refs
python spec/spec.py impact <slug>       # blast radius before changing anything

python spec/spec.py find <keywords>     # search when you don't know the slug
python spec/spec.py domain <name>       # load a full domain

python spec/spec.py check-slug <slug>   # is this slug available?
python spec/spec.py write               # add entries (JSON input, validates before writing)

python spec/spec.py validate            # run before every commit — zero errors only
python spec/spec.py diff [ref]          # semantic change manifest vs HEAD or any ref
python spec/spec.py reconcile <path>    # detect code↔spec drift
python spec/spec.py rebuild             # rebuild .spec/ cache from files

python spec/spec.py init                # scaffold CONTEXT.md in a new project
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

`spec validate` checks that every `spec:` slug in code has a matching entry. `spec reconcile` surfaces drift when code and spec get out of sync.

---

## Pre-commit hook

```sh
./scripts/install-spec-pre-commit.sh
```

When spec files are staged, the hook:
1. Runs `spec validate` — blocks commit on any error
2. Runs `spec rebuild` — regenerates `.spec/` cache
3. Stages `.spec/` automatically

---

## Adding a new domain

1. Create `spec/<domain>.md` with the standard structure (see above)
2. Add it to the `## Domain map` in `spec/CONTEXT.md`:
   ```
   auth  spec/auth.md
   ```
3. Run `python spec/spec.py orient` to verify it loads

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
}' | python spec/spec.py write --yes
```

### Directly in markdown

Edit the domain file. Follow the format above. Run `python spec/spec.py validate` when done.

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

auth    spec/auth.md
billing spec/billing.md
```

---

## Commit message format

```sh
# Spec-only
spec(auth): add session-expiry requirement
spec(auth): implement admin-revoke, close Q:admin-scope
spec: reconcile src/api/

# Code + spec together (required)
feat(auth): implement session expiry
spec: implement session-expiry
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
grep -rh "^>" spec/*.md         # domain summaries
grep -r "^Q:" spec/             # open questions
grep -r "\[planned\]" spec/     # backlog
grep -r "^  !" spec/            # unconfirmed assumptions
grep -r "^C:" spec/             # all constraints
grep -A 20 "^session-expiry:" spec/  # entry by slug
grep -r "~src/api/auth" spec/   # what owns this path
```
