# SPEC_AGENT.md

> Agent operating instructions for spec-driven development.
> Drop this file into `.cursorrules`, `.claude/CLAUDE.md`, `AGENTS.md`, or any
> equivalent rules file your agent reads at session start.

---

## Core principles

**Every task is a chance to capture user expectations.** The spec is the compiled, correct record of what the system does and why. The agent's job is not only to complete tasks but to keep the spec aligned with user intent — so that over time, expectations are never left implicit.

- **Read specs first.** Before touching any file, grep or use `prov` to understand what governs it. Never act blind.
- **Extract expectations.** From every request, identify which spec entries are involved and whether the request implies new or changed requirements. If a user's words reveal an expectation not yet in the spec, capture it.
- **Update proactively.** Every code change that affects behavior updates the spec in the same commit. Do not wait to be asked.
- **Spec before code.** Never write code without first proposing the spec change and getting confirmation.
- **Validate continuously.** Run `prov validate` before every commit. Zero errors only.

The markdown files in `prov/`, `spec/`, or `specs/` are the source of truth. The CLI is a helper. When the CLI is unavailable, use grep — the spec is always readable.

---

## The laws

These apply in every session without exception.

1. **Read before write.** Never modify code or spec without first understanding what governs it.
2. **Every gap gets a `!` line.** Any value, threshold, or choice you decide on the user's behalf must be marked. "It seemed obvious" is never an excuse.
3. **Every entry needs a `>` line.** No entry exists without provenance. Use a source prefix: `user:`, `inferred:`, `code:`, `regulatory:`, `derived`. Quote the user where possible (`> user: "..."`). For agent interpretation use `> inferred:` with `!`. For code-derived use `> code:` with `!`. See spec-entry-format skill.
4. **Spec and code in the same commit.** Never split them.
5. **No evolutionary language.** The spec is always current. Never write "previously", "changed from", "deprecated". Git records history; the spec records intent.
6. **Never write to `.spec/`.** The cache is machine-generated. The pre-commit hook manages it.
7. **Validate before every commit.** `prov validate` — zero errors is the only acceptable state.
8. **Spec before code.** Never write code without proposing the spec change and getting confirmation first.
9. **Capture expectations.** When a task reveals an expectation not in the spec, add or update an entry. Do not leave expectations only in code or conversation.

---

## THE REQUEST FLOW

**This is the protocol. Follow it on every task — new feature, change, fix, refactor, or question. Never skip a phase. Never swap the order.**

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Phase 1  UNDERSTAND   Read the spec; identify involved entries         │
│  Phase 2  CLARIFY      Ask blocking questions; extract implicit         │
│                        expectations; surface assumptions                │
│  Phase 3  PROPOSE      Show what will change and why; get confirmation  │
│  Phase 4  WRITE SPEC   Update spec files; validate; diff                │
│  Phase 5  IMPLEMENT    Write code with spec: backlinks                  │
│  Phase 6  SYNC         Catch drift; validate; diff; commit              │
└─────────────────────────────────────────────────────────────────────────┘
```

Spec updates happen in **Phase 4** and **Phase 6** — proactively, not only when the user asks.

**The goal:** Over every task, user expectations are extracted, compiled into the spec, and kept correct. The spec becomes a reliable record of what the user actually intends — not what was guessed or remembered.

---

### Phase 1 — Understand

Before touching anything, read the spec. Use grep first:

```bash
# Orient (session start or new task)
grep -rh "^>" spec/*.md spec/*/*.md 2>/dev/null | head -30   # domain summaries
grep -r "^Q:" spec/                                            # open questions
grep -r "\[planned\]" spec/                                    # backlog
grep -r "^  !" spec/                                           # unconfirmed assumptions

# What governs this path?
grep -r "~<path>" spec/        # e.g. grep -r "~src/middleware" spec/
grep -rn "spec: <slug>" src/   # code implementing a slug

# Find entry by slug or keyword
grep -r "^<slug>:" spec/
grep -ri "keyword" spec/
grep -r "^  @ <slug>" spec/    # what depends on this slug
grep -A 25 "^<slug>:" spec/    # full entry context
```

If prov is available:

```bash
prov orient              # formatted surface: domains, questions, backlog
prov find <keywords>     # search entries
prov scope <path>        # what governs this file/dir
prov context <slug>      # full entry + deps
prov impact <slug>       # blast radius before changing anything
```

Then read the code referenced by `~` lines in affected entries. Read only — do not change yet.

---

### Phase 2 — Clarify

Identify everything the user did not specify. For each unknown:

- **Blocking** (you cannot design without it): ask.
- **Non-blocking** (a reasonable default exists): proceed, but mark with `!`. Surface in Phase 3.

**Questioning rules:**

- One question per message. Ask the most decision-blocking question first.
- Do not ask questions the spec already answers.
- Do not ask about competent-developer defaults (error handling, logging, etc.).

**Extract implicit expectations.** Even when the user does not say "add a requirement," infer what the spec should reflect: (1) Does this imply a behavior not yet written? (2) Is there a number, threshold, or edge case the user assumed (record with `!` if unconfirmed)? Capture these in Phase 3 and Phase 4.

**If the request contradicts an existing entry**, stop and surface it:

```
This request conflicts with an existing requirement:

  <slug>: <statement>
  > <provenance>

Options:
  A. Replace <slug> — old behavior removed
  B. Add alongside — requires clarifying scope of <slug>
  C. Out of scope — new behavior goes in ## Out of scope

Which should I do?
```

Wait for the user to choose before proceeding.

---

### Phase 3 — Propose

Propose spec changes. **Do not write anything yet.** Tell the user:

1. **What entries will change** — slugs added/modified/removed, which domain file, before/after for modifications.
2. **How the system behaves differently** — from the user's perspective: what is new, what changes.
3. **Which flows are affected** — use `prov impact <slug>`; be explicit about indirect effects.
4. **What you are assuming** — every `!` assumption in plain language; ask if each is correct.
5. **What is out of scope** — explicitly state what this change does NOT affect.

Wait for confirmation. If the user corrects something, return to Phase 2.

---

### Phase 4 — Write the spec

After confirmation, update the spec.

```bash
grep -r "^<slug>:" spec/   # or: prov check-slug <slug>
# Edit the domain .md file(s) directly
prov validate              # must pass with zero errors before continuing
prov diff                  # show the user what changed
```

Rules:

- New entries go in the correct domain file under the correct section.
- Unimplemented entries get `[planned]`.
- Every `!` assumption from Phase 3 appears as a `  ! assumption text` sub-line.
- Every entry has a `  > provenance` line with source prefix (user, inferred, code, regulatory, derived) per spec-entry-format. No exceptions.

Surface any remaining `!` lines to the user for confirmation before moving to Phase 5.

---

### Phase 5 — Implement

```bash
prov scope <file>        # confirm what governs the code you are about to write
```

- Implement exactly what the spec says. No extras.
- Every function, class, or logical block that implements a spec entry carries `# spec: slug` at the top.
- Multiple slugs comma-separated: `# spec: slug-a, C:slug-b`

---

### Phase 6 — Sync and close

Proactively catch drift between spec and code.

```bash
prov sync <path>         # full drift report
```

Drift types and fixes:

| Drift | Fix |
|-------|-----|
| Silent impl — `[planned]` but code has `spec:` | `prov sync mark-implemented <slug>` |
| Phantom slug — `spec:` in code, no spec entry | `prov sync remove-backlink <file> <line> <slug>` or add the entry |
| Dead ref — `~` path no longer exists | `prov sync remove-ref <slug> <ref>` or `update-ref <slug> <old> <new>` |

Then close:

```bash
prov validate            # zero errors required
prov diff                # final review — show the user what changed
# Commit: spec + code together
# Message: feat(<domain>): <description>
#          spec: implement <slug>, add <slug>
```

---

### Debugging — variant of the flow

Start from Phase 1 scoped to the bug:

```bash
prov scope <file-with-bug>   # what should this file do?
prov context <slug>          # full requirement details
```

Determine root cause, then continue:

- **Code deviates from spec** → fix code (Phase 5 → Phase 6). Spec unchanged.
- **Spec is wrong** → Phase 3 (propose updated spec) → Phase 4 → Phase 5 → Phase 6.
- **Spec has a gap** (`!` assumption) → surface the assumption; get user confirmation before fixing anything. Then Phase 5 → Phase 6.

---

### Sync session — variant for bulk drift

When code and spec have drifted without going through the normal flow (bulk refactor, imported code):

```bash
prov sync src/           # full drift report
```

Present each drift item to the user with context. **Never apply a fix without explicit user confirmation.** Apply confirmed fixes with sync patch sub-commands, then: validate → diff → commit.

Read-only drift report: `prov reconcile src/`

---

## Reference

---

### Session start checklist

At the beginning of every session or when picking up a new task:

1. Resolve spec root: `prov/`, `spec/`, or `specs/`.
2. Read `CONTEXT.md`: purpose, constraints, domain map.
3. Orient: `grep -rh "^>" spec/*.md` · `grep -r "^Q:" spec/` · `grep -r "\[planned\]" spec/`
4. If given a path or slug: grep for what governs it before doing anything.
5. Identify what the user expects and which spec entries are involved — before acting. Extract key specs from the task.

---

### When to read specs

| Trigger | Action |
|---------|--------|
| Session start | Grep domain summaries, questions, assumptions, planned items. |
| Before touching any file | Grep for `~` refs owning that path. |
| Before changing a requirement | Grep for slug, `@` dependents, `~` refs. Understand blast radius. |
| User asks about behavior | Grep by keyword or slug. Read full entry with `-A 20`. |
| Implementing a new feature | Grep for related slugs, constraints, open questions. |
| Debugging | Grep for `~` refs to the buggy file. |

---

### When to update specs

| Trigger | Action |
|---------|--------|
| Implementing a new requirement | Add entry, `[planned]` → implemented, add `~` refs, add `spec:` backlinks. |
| Changing existing behavior | Update entry statement and `~` refs. |
| Adding or removing code paths | Add or remove `~` refs and `spec:` backlinks. |
| Discovering drift | `prov sync`; fix phantom slugs, silent impl, dead refs. |
| Filling a gap with an assumption | Add `!` line. Surface to user for confirmation. |
| Resolving a question | Remove `Q:` entry. Update `? Q:slug` refs. |
| Request implies unstated expectation | Add or update an entry quoting or paraphrasing the user's intent. |

---

### How to read a spec entry

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
| Statement | What the system does for the user. Current state only. |
| `>` | Provenance — use source prefix: user, inferred, code, regulatory, derived. See spec-entry-format. |
| `!` | Agent filled this in; user has not confirmed. |
| `@` | This entry depends on another slug. |
| `~` | Code implementing this entry. One line per ref. |
| `[planned]` | Not yet implemented. No `~` lines. Remove when implemented. |

**Node types at column 0:**

```
slug:    requirement — user-observable behavior
C:slug:  constraint  — non-negotiable rule
Q:slug:  question    — unresolved decision blocking implementation
```

**Sub-lines always 2-space indent. Never anything else.**

---

### How to write a spec entry

Check slug availability first:

```bash
prov check-slug <proposed-slug>
# or: grep -r "^<proposed-slug>:" spec/
```

Slugs: kebab-case, 2–4 words, describing behavior not domain.

```
session-expiry    ✓   describes behavior
guest-access      ✓   clear
auth-session      ✗   domain prefix — don't
limit             ✗   too vague
```

**Entry format — provenance source types:**

| Type | Format | When |
|------|--------|------|
| user | `> user: "exact quote"` | Direct quote |
| inferred | `> inferred: reasoning` + `!` | Agent interpretation |
| code | `> code: path — context` + `!` | From sync/drift |
| regulatory | `> regulatory: source — citation` | Legal/compliance |
| derived | `> derived: slug — reasoning` | Logical consequence |

```
slug: Statement describing observable behavior. [planned if not yet coded]
  > user: "..." | inferred: ... | code: path — context | regulatory: ... | derived: slug — ...
  ! assumption (required for inferred and code)
  @ dependency-slug (if this entry depends on another)
  ? Q:blocking-question (if blocked by an open question)
  ~ src/path/to/file.py:line (one per line, only when implemented)
```

**Constraint format:**

```
C:slug: Non-negotiable rule statement.
  > user: "exact quote" or regulatory: source — citation
```

**Open question format:**

```
Q:slug: Question that must be resolved before implementation?
  > blocks: slug-of-the-requirement-it-blocks
```

**Complete example:**

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

---

### Code backlinks

Every function or class that implements a spec entry carries a `spec:` comment:

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

One comment per logical block. Multiple slugs on one line, comma-separated. Place at the top of the block.

---

### File format invariants — never violate

1. Every primary entry starts at **column 0**. No leading spaces.
2. Every sub-line is indented **exactly 2 spaces**. Not 4. Not a tab.
3. The `~` sigil is on its own sub-line. Never inline in the statement.
4. Each entry has one statement line. Multi-sentence statements on that one line are fine.

Breaking these breaks the file parser and grep-based retrieval.

---

### Assumption confirmation

Every `!` line represents a decision the user has not confirmed. Surface it explicitly:

```
I've written the following spec entries. One assumption needs your confirmation:

  session-expiry: Sessions expire after 30 days of inactivity.
    ! assumed 30 days — you said "standard timeout, nothing crazy"

Is 30 days correct, or should it be different?
```

- **Confirms** → remove `!`. Now reads as user-specified.
- **Corrects** → rewrite statement with correct value; remove `!`.
- **Defers** ("decide for me") → keep `!`. Do not remove. It will appear in every future diff until explicitly confirmed. The `!` is the record that this was not their explicit choice.

---

### What the spec never contains

If you find yourself writing any of these, stop and delete it:

- "Previously this was X"
- "Changed from X to Y on [date]"
- "Deprecated — use `other-slug` instead"
- "We chose X because..."
- Any entry without a `>` line
- Any implementation detail the user did not specify (without a `!` line)

The spec is always current. A well-maintained spec is indistinguishable from one written in a single session with complete knowledge of the system.

---

### Commit message format

```bash
# Spec-only changes
spec(auth): add session-expiry, C:jwt-stateless
spec(auth): implement admin-revoke
spec(auth): close Q:admin-revoke-scope
spec: reconcile src/api/

# Code + spec in same commit
feat(auth): implement session expiry
spec: implement session-expiry, add ! assumption for 30-day value
```

---

### prov CLI reference

```bash
# Session start
prov orient              # full surface: domains, questions, backlog

# Coding entry point
prov scope <path>        # what governs this file or directory?
prov context <slug>      # full entry context
prov impact <slug>       # blast radius before changing anything

# Discovery
prov find <keywords>     # when you don't know the slug
prov domain <name>       # full domain load

# Writing
prov check-slug <slug>   # is this slug available?
prov write               # guided authoring with pre-write validation

# Integrity
prov validate            # run before every commit
prov diff [ref]          # semantic change manifest for human review
prov reconcile <path>    # detect code↔spec drift (read-only)
prov sync [path]         # interactive drift resolution
prov rebuild             # rebuild cache from files
prov init                # scaffold CONTEXT.md (new project)
```

---

### Grep quick reference — primary discovery tool

Works without any CLI. Replace `spec/` with `prov/` or `specs/` as needed.

```bash
# Orient
grep -rh "^>" spec/*.md spec/*/*.md 2>/dev/null
grep -r "^Q:" spec/
grep -r "\[planned\]" spec/
grep -r "^  !" spec/
grep -r "^C:" spec/

# What governs this path?
grep -r "~src/path/to/file" spec/

# Find by slug
grep -A 25 "^session-expiry:" spec/

# Dependents and implementers
grep -r "^  @ session-expiry" spec/
grep -rn "spec: session-expiry" src/

# Keyword search
grep -rEi "session|auth|timeout" spec/

# Slug availability
grep -r "^my-new-slug:" spec/

# Duplicate check
grep -rhE "^[a-z][a-z0-9-]*:|^C:|^Q:" spec/ | cut -d: -f1,2 | sort | uniq -d
```

**When to use which:**
- **Grep**: known slug, known path, structural patterns (`^Q:`, `^  @`, `~path`).
- **Semantic search**: "Where is X behavior specified?" when you don't know the slug.
- **prov find**: keyword search over entries (when prov is available).
- **prov impact/context**: multi-hop traversal (when prov is available).

---

*The markdown files are the truth. The CLI is a convenience.*
