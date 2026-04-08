---
name: spec-entry-format
version: "1.0"
triggers:
  - writing or editing spec files
  - adding or updating ~ code refs or spec: backlinks
  - reading an unfamiliar spec entry
  - checking commit or entry format
---

## Mission

Apply the correct spec entry format (node types, sigils, invariants, backlinks, commit messages) so the parser and grep-based retrieval work and the spec stays valid.

---

## Pre-requisites

- **Spec directory** present: `prov/`, `spec/`, or `specs/`.
- **grep** (or equivalent) for slug checks and pattern search.
- **prov CLI** (optional): `prov check-slug`, `prov validate`. If absent, use `grep -r "^<slug>:" spec/` for slug availability.

---

## Instructions

### Step 1 — Before writing any entry: check slug

Run `prov check-slug <proposed-slug>` or `grep -r "^<proposed-slug>:" spec/`. If the slug exists, pick a different one or edit the existing entry. Slugs: kebab-case, 2–4 words, describe **behavior** not domain (see Reference → Slug rules).

### Step 2 — Use the correct node type and structure

Use **Requirement**, **Constraint**, or **Question** format from Reference. Each has a statement line and sub-lines with `  >`, `  !`, `  @`, `  ?`, `  ~` (each on its own line, exactly 2-space indent).

### Step 3 — Enforce file invariants

Every primary entry at **column 0**. Every sub-line **exactly 2 spaces** (not 4, not tab). Sigils only on their own sub-lines; never inline in the statement. One statement line per entry. See Reference → File format invariants.

### Step 4 — Add code backlinks when implementing

In code, at the top of each function/class/block that implements a spec entry: `# spec: slug` (or `// spec: slug`). Multiple slugs: `# spec: slug-a, C:slug-b`. One comment per logical block. See Reference → Code backlinks.

### Step 5 — Use the correct commit format

See Reference → Commit format. Spec-only vs code+spec; always include the `spec: ...` line when code and spec change together.

---

## Reference

### Reading an entry — anatomy

```
session-expiry: Sessions expire after 30 days of inactivity.
  > inferred: user said "standard session timeout, nothing crazy" — interpreted as 30 days
  ! assumed 30 days — "nothing crazy" is unconfirmed
  @ C:jwt-stateless
  ~ src/middleware/session.py:44
  ~ src/middleware/session.py:101
```

| Part | Meaning |
|------|---------|
| `session-expiry` | Slug — permanent, globally unique. Used in `spec:` backlinks in code. |
| Statement | What the system does. Current state only. |
| `>` | Provenance — use source prefix: user, inferred, code, regulatory, derived. See Provenance source types below. |
| `!` | Agent filled this in; user has not confirmed it. |
| `@` | This entry depends on another slug. |
| `~` | Code implementing this entry. One line per ref. |
| `[planned]` | Not yet implemented. No `~` lines. Remove when implemented. |

### Provenance source types

Every `>` line must identify where the entry came from. Use exactly one of these — do not invent new types.

| Type | Format | When used | `!` required? |
|------|--------|-----------|---------------|
| user | `> user: "exact words"` | Direct quote from user | No |
| inferred | `> inferred: reasoning` | Agent interpretation of user intent | Yes |
| code | `> code: path — context` | Discovered during sync, drift, reverse-engineering | Yes |
| regulatory | `> regulatory: source — citation` | Legal, compliance, platform requirement | No |
| derived | `> derived: slug — reasoning` | Logical consequence of another entry | No |

For Q nodes: `> blocks: slug` remains valid.

Examples:

```
> user: "we'll just do Google login for now"

> inferred: user said "nothing crazy" for timeout — interpreted as 30 days
! assumed 30 days — not confirmed

> code: src/auth/google.py — phantom slug, prov sync 2026-03-10
! statement inferred from implementation — user confirmed after sync

> regulatory: GDPR Article 17 — right to erasure within 30 days

> derived: C:jwt-stateless — stateless tokens can't maintain server-side revocation list
```

### Node types at column 0

```
slug:    requirement — user-observable behavior
C:slug:  constraint  — non-negotiable rule governing a domain
Q:slug:  question    — unresolved decision blocking implementation
```

Sub-lines always 2-space indent. Never 4 or tab.

### Slug rules

- kebab-case, 2–4 words, describe **behavior** not domain.
- Good: `session-expiry`, `guest-access`. Bad: `auth-session` (domain prefix), `limit` (too vague).

### Requirement format

```
slug: Statement describing user-observable behavior. [planned if not yet coded]
  > user: "exact quote" | inferred: reasoning | code: path — context | regulatory: source — citation | derived: slug — reasoning
  ! assumption (required for inferred and code; only when agent filled a gap)
  @ dependency-slug (if this entry depends on another slug)
  ? Q:blocking-question (if blocked by an open question)
  ~ src/path/to/file.py:line (one per line, only when implemented)
```

### Constraint format

```
C:slug: Non-negotiable rule statement.
  > user: "exact quote" or regulatory: source — citation
```

### Open question format

```
Q:slug: Question that must be resolved before implementation?
  > blocks: slug-of-the-requirement-it-blocks
```

### File format invariants — never violate

1. Every primary entry starts at **column 0**. No leading spaces.
2. Every sub-line is indented **exactly 2 spaces**. Not 4. Not a tab.
3. The `~` sigil appears only on its own sub-line. Never inline in the statement.
4. Each entry has one statement line (the line with `slug: statement`). Multi-sentence statements on that one line are fine.

Violating these breaks the parser and grep-based retrieval.

### Complete domain file example

```markdown
# Auth

> OAuth-based auth and stateless JWT sessions. Two roles: admin/member.

## Constraints

C:oauth-only: OAuth only — no email/password.
  > user: "I don't want to deal with password resets"

C:jwt-stateless: Sessions are stateless JWT — no server-side session store.
  > user: "I don't want to manage session infrastructure"

## Requirements

google-login: Users authenticate via Google OAuth.
  > user: "we'll just do Google login for now"
  @ C:oauth-only
  ~ src/api/auth/google.py
  ~ src/api/auth/callback.py

session-expiry: Sessions expire after 30 days of inactivity.
  > inferred: user said "standard session timeout, nothing crazy" — interpreted as 30 days
  ! assumed 30 days — "nothing crazy" is unconfirmed
  @ C:jwt-stateless
  ~ src/middleware/session.py:44

admin-revoke: Admins can revoke any user session immediately. [planned]
  > user: "need a kill switch for bad actors"
  ! assumed token blocklist approach — not stated by user
  @ session-expiry
  ? Q:admin-revoke-scope

## Open Questions

Q:admin-revoke-scope: Does admin-revoke apply to one session or all sessions?
  > blocks: admin-revoke

## Out of scope

MFA, SSO/SAML.

## Refs

~ src/api/auth/
~ src/middleware/session.py
~ src/models/user.py
```

### Code backlinks

Every function or class that implements a spec entry carries a `spec:` comment. One per logical block; multiple slugs comma-separated. Place at top of block.

```python
# spec: session-expiry
def refresh_session(token: str) -> Session:

# spec: billing-session-sync, C:usage-cap
class PlanLimitMiddleware:
```

```typescript
// spec: admin-revoke
async function revokeSession(userId: string): Promise<void>;
```

### What the spec never contains

Do not write: "Previously this was X", "Changed from X to Y", "Deprecated — use other-slug", "We chose JWT because...", or any description of how the system got to its current state. No entry without a `>` line. No implementation detail the user did not specify without a `!` line. The spec is always current state only.

### Commit format

```bash
# Spec-only changes
spec(auth): add session-expiry, C:jwt-stateless
spec(auth): implement admin-revoke
spec(auth): close Q:admin-revoke-scope
spec(billing): update plan-limits statement
spec: reconcile src/api/

# Code + spec in same commit
feat(auth): implement session expiry
spec: implement session-expiry, add ! assumption for 30-day value
```

### Grep quick reference

Replace `spec/` with `prov/` or `specs/` if that is your spec root.

```bash
# Orient
grep -rh "^>" spec/*.md spec/*/*.md 2>/dev/null
grep -r "^Q:" spec/
grep -r "\[planned\]" spec/
grep -r "^  !" spec/
grep -r "^C:" spec/

# What governs this path?
grep -r "~src/path/to/file" spec/
grep -r "~src/path/" spec/

# Find by slug
grep -r "^session-expiry:" spec/
grep -A 25 "^session-expiry:" spec/

# Dependents and implementers
grep -r "^  @ session-expiry" spec/
grep -rn "spec: session-expiry" src/

# Keyword search
grep -rEi "session|auth|timeout" spec/

# Slug availability (before writing)
grep -r "^my-new-slug:" spec/

# Duplicate check
grep -rhE "^[a-z][a-z0-9-]*:|^C:|^Q:" spec/ | cut -d: -f1,2 | sort | uniq -d
```

### prov CLI — quick reference

```bash
prov orient              # session start
prov scope <path>        # what governs this file/dir
prov context <slug>      # full entry + deps
prov impact <slug>       # blast radius
prov find <keywords>     # search entries
prov domain <name>       # full domain
prov check-slug <slug>   # slug availability
prov validate            # before every commit
prov diff [ref]          # semantic change manifest
prov reconcile <path>    # drift detection (read-only)
prov sync [path]         # interactive drift resolution
prov rebuild             # rebuild cache
prov init                # scaffold CONTEXT.md
```

---

## Error Handling

| If this happens | Do this |
|-----------------|--------|
| `prov validate` reports "ghost-scope" or "no > line" | Add a `  > ` line with appropriate source prefix (user, inferred, code, regulatory, derived). Do not commit without it. |
| `prov validate` reports "dead-ref" | Remove the `~` line or update the path to the real file. Do not leave a `~` pointing to a missing path. |
| `prov validate` reports "phantom-slug" | Either add the missing spec entry for that slug or remove the `spec: slug` backlink from code. Do not leave a backlink with no entry. |
| You accidentally used 4 spaces or tab for sub-lines | Change to exactly 2 spaces. Parser and grep rely on 2-space indent. |
| You put `~` or `@` inline in the statement | Move them to separate sub-lines with 2-space indent. One ref per line. |
| Slug already exists elsewhere | Choose a different slug or update the existing entry; do not create a duplicate. Use `prov check-slug` or grep before writing. |
