# Spec format

The spec is plain markdown in a `prov/` directory (`spec/` and `specs/` are
also recognized). The files are always the source of truth — every query
backend is a disposable read-acceleration layer, and everything is greppable
without tooling. Two invariants must never be violated:

1. Every primary entry starts at **column 0**.
2. Every sub-line is indented **exactly 2 spaces** (not 4, not a tab).

Violating either breaks the parser and grep-based retrieval.

## Entry anatomy

```
session-expiry: Sessions expire after 30 days of inactivity.
  > inferred: user said "standard session timeout, nothing crazy" — interpreted as 30 days
  ! assumed 30 days — "nothing crazy" is unconfirmed
  @ C:jwt-stateless
  ~ src/middleware/session.py:44
  ~ src/middleware/session.py:101
```

| Part | Meaning |
|---|---|
| `session-expiry` | Slug — permanent, globally unique, used in `spec:` backlinks in code |
| Statement | What the system does. Current state only. Never "previously", "changed from". |
| `>` | Provenance — where the entry came from. Required on every entry. |
| `!` | Assumption the agent filled in — needs user confirmation before removing. |
| `@` | This entry depends on another slug. One per line. |
| `?` | This entry is blocked by an open question (`? Q:slug`). |
| `~` | Code implementing this entry. One line per ref. |
| `[planned]` | Not yet coded. Remove when implemented, add `~` lines. |

Slugs are kebab-case, 2–4 words, describing the behavior, not the domain:
`session-expiry` ✓, `auth-session` ✗ (domain prefix), `limit` ✗ (vague).
Once referenced in code, a slug never changes.

## Node types

Type is encoded in the column-0 prefix, not inferred from section headers:

```
slug:      requirement — user-observable behavior
C:slug:    constraint  — non-negotiable rule governing a domain
Q:slug:    question    — unresolved decision blocking implementation
```

Constraints never carry `[planned]` — they are active or they don't exist.
Questions always carry a `> blocks: <slug>` line and are deleted when
resolved.

## Provenance source types

Every `>` line identifies its source with exactly one of these prefixes:

| Type | Format | When used | `!` required? |
|---|---|---|---|
| user | `> user: "exact words"` | Direct quote from user | No |
| inferred | `> inferred: reasoning` | Agent interpretation of user intent | Yes |
| code | `> code: path — context` | Discovered during sync/drift/reverse-engineering | Yes |
| regulatory | `> regulatory: source — citation` | Legal, compliance, platform requirement | No |
| derived | `> derived: slug — reasoning` | Logical consequence of another entry | No |

For `Q:` nodes, `> blocks: slug` remains valid.

## Domain file structure

```markdown
# Auth

> OAuth-based auth and stateless JWT sessions.

## Constraints

C:oauth-only: OAuth only — no email/password.
  > user: "I don't want to deal with password resets"

## Requirements

google-login: Users authenticate via Google OAuth.
  > user: "we'll just do Google login for now"
  @ C:oauth-only
  ~ src/api/auth/google.py

session-expiry: Sessions expire after 30 days of inactivity.
  > inferred: user said "standard session timeout, nothing crazy" — interpreted as 30 days
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

Line 2 of every file is a `>` one-line summary — the domain's identity
string in `prov orient` output. `## Refs` declares the code territory the
domain owns; it powers `prov scope` for paths without a direct `~` ref.

To add a new domain: create `prov/<domain>.md` with this structure, add it
to the `## Domain map` in `prov/CONTEXT.md`, then run `prov orient` to
verify it loads.

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

CONTEXT.md contains no requirements. It establishes the context every agent
session needs before loading any domain file.

## Code backlinks

Every function or block that implements a spec entry carries a `spec:`
comment — one per logical block, at the top of the block, multiple slugs
comma-separated:

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

`prov validate` checks both directions: every `~` ref resolves to a real
path, and every `spec:` slug in code has a matching entry. `prov reconcile`
and `prov sync` surface drift when they fall out of sync.

## Commit message format

```sh
# Spec-only
prov(auth): add session-expiry requirement
prov(auth): implement admin-revoke, close Q:admin-scope
prov: reconcile src/api/

# Code + spec together (required — same commit, always)
feat(auth): implement session expiry
prov: implement session-expiry
```

## Validation checks

`prov validate` runs these checks; all ERRORs must be zero before committing
(exit 1 otherwise). Warnings surface but do not fail.

| Severity | Check | Meaning |
|---|---|---|
| ERROR | `ghost-scope` | Entry has no `>` line |
| ERROR | `dead-ref` | `~` path doesn't exist |
| ERROR | `phantom-slug` | `spec:` in code, no entry |
| ERROR | `duplicate-slug` | Same slug in two files |
| ERROR | `no-dangling-dep` | `@` target doesn't exist |
| ERROR | `no-dangling-block` | `? Q:slug` target doesn't exist |
| WARN | `orphan-question` | `Q:` not referenced by any `?` line |

Unconfirmed assumptions (`!` lines) are always listed for human review.
Silent implementations — `[planned]` entries whose slug already appears in
code — are surfaced by `prov reconcile` and `prov sync`.

## Grep fallback

The spec is always greppable without any tooling:

```sh
grep -rh "^>" prov/*.md         # domain summaries
grep -r "^Q:" prov/             # open questions
grep -r "\[planned\]" prov/     # backlog
grep -r "^  !" prov/            # unconfirmed assumptions
grep -r "^C:" prov/             # all constraints
grep -A 20 "^session-expiry:" prov/  # entry by slug
grep -r "^  @ session-expiry" prov/  # what depends on this slug
grep -rn "spec: session-expiry" src/ # code implementing this slug
grep -r "~ src/api/auth" prov/  # what owns this path
```
