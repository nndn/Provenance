# SPEC_AGENT.md

> Agent operating instructions for spec-driven development.
> Drop this file into .cursorrules, .claude/CLAUDE.md, AGENTS.md, or any
> equivalent rules file your agent reads at session start.

---

## What the spec is

`prov/` contains a living requirements index. At any moment it answers: what
does this system do, and why? It is not a changelog or design journal. It is
the current, complete snapshot of user intent.

The markdown files in `prov/` are always the source of truth. Any tool,
cache, or index is built from those files and can be regenerated at any time.
An agent or developer can always grep the files directly — no tooling required.

Read `prov/CONTEXT.md` (or `spec/CONTEXT.md` or `specs/CONTEXT.md`) first. It contains
the project purpose, hard constraints, non-goals, and domain map. It is the entry
point to every session.

---

## Installing the prov CLI

The agent uses the `prov` CLI to query and validate the spec. Install it once per
machine or per project:

| Platform | Command |
|----------|---------|
| **PyPI (recommended)** | `pipx install provenance-cli` |
| **GitHub** | `pipx install 'provenance-cli @ git+https://github.com/nndn/Provenance.git'` |
| **Project-local** | Run `sh install.sh` from the Provenance repo into your project |

**Resolve spec directory:** `prov` looks for `prov/`, `spec/`, or `specs/` from the
current directory (or `$SPEC_DIR` if set). Run `prov` from the project root.

Commands: `prov orient`, `prov scope <path>`, `prov context <slug>`, `prov validate`, etc.
If `prov` is not installed globally, use `python prov/prov.py <command>` instead.

---

## The non-negotiable rules

These apply in every session, without exception.

**1. Read before write.**
Never modify code or spec without first understanding what governs what you are
about to touch. Use `prov scope` or grep. No exceptions.

**2. Every gap you fill gets a `!` line.**
Any specific value, threshold, choice, or behavior you decide on the user's behalf
— because they did not specify it — must be marked with a `!` assumption line.
This is the integrity mechanism. If you are tempted to skip it because "it seems
obvious," that is precisely when it is required.

**3. Every entry needs a `>` line.**
No entry exists without provenance. If the user said something, quote it. If you
inferred it, write `> inferred from: <reasoning>` and add a `!` line. An entry
with no `>` line will fail validation and must not be committed.

**4. Spec and code change in the same commit.**
Never commit a code change that implements a spec entry without updating the spec
in the same commit. Never commit a spec change without the corresponding code
change (or mark it `[planned]`). They are one artifact.

**5. Never write evolutionary language in the spec.**
The spec describes current state only. Never write "previously", "changed from",
"deprecated", "was replaced by", or anything that describes how the system got to
its current state. Git records history. The spec records intent.

**6. Never write to `.spec/`.**
The `.spec/` directory is machine-generated from the markdown files. Writing to it
directly creates a cache that does not reflect the files. The pre-commit hook
manages it. You never touch it.

**7. Validate before every commit.**
Run `prov validate` (or `python prov/prov.py validate` if using project-local copy)
before committing. Fix all errors. Zero errors is the only acceptable state to commit.

**8. Spec before code. Always.**
Never write a line of code in response to a user request without first proposing
the spec change and getting the user's confirmation. The proposal must describe
what will change, how the system will behave differently, which existing flows are
affected, and what you are assuming. This is non-negotiable. See "The request flow".

---

## How to read a spec entry

```
session-expiry: Sessions expire after 30 days of inactivity.
  > "standard session timeout, nothing crazy"
  ! assumed 30 days — "nothing crazy" is unconfirmed
  @ C:jwt-stateless
  ~ src/middleware/session.py:44
  ~ src/middleware/session.py:101
```

| Part             | What it means                                                                         |
| ---------------- | ------------------------------------------------------------------------------------- |
| `session-expiry` | Slug — permanent, globally unique handle. Used in `spec:` backlinks in code.          |
| Statement        | What the system does for the user. Current state only.                                |
| `>`              | Why this requirement exists. User's words where possible.                             |
| `!`              | Something the agent filled in that the user did not specify. Needs user confirmation. |
| `@`              | This entry's behavior depends on another slug.                                        |
| `~`              | Code that implements this entry. One line per ref.                                    |
| `[planned]`      | Not yet implemented. No `~` lines. Remove when implemented.                           |

**Node types at column 0:**

```
slug:      requirement — user-observable behavior
C:slug:    constraint  — non-negotiable rule (compliance, hard limit, user-specified tech)
Q:slug:    question    — unresolved decision that blocks implementation
```

**Sub-lines always 2-space indent. Never anything else.**

---

## How to write a spec entry

### Before writing any entry

```bash
# Check slug availability — always do this first
prov check-slug <proposed-slug>
# or manually:
grep -r "^<proposed-slug>:" spec/
```

Slugs must be kebab-case, 2–4 words, describing behavior not domain.

```
session-expiry    ✓   describes behavior
guest-access      ✓   clear
auth-session      ✗   domain prefix — don't
limit             ✗   too vague
```

### Entry format

```markdown
slug: Statement describing observable behavior. [planned if not yet coded]

> "user's words" or inferred from: reasoning
> ! assumption if you filled a gap (required when you did)
> @ dependency-slug (if this entry depends on another)
> ? Q:blocking-question (if a question must be resolved before implementation)
> ~ src/path/to/file.py:line (one per line, only when implemented)
```

### Constraint format

```markdown
C:slug: Non-negotiable rule statement.

> "user's words" or regulatory requirement
```

### Open question format

```markdown
Q:slug: Question that must be resolved before implementation?

> blocks: slug-of-the-requirement-it-blocks
```

### Complete example

```markdown
# Auth

> OAuth-based auth and stateless JWT sessions. Two roles: admin/member.

## Constraints

C:oauth-only: OAuth only — no email/password.

> "I don't want to deal with password resets"

C:jwt-stateless: Sessions are stateless JWT — no server-side session store.

> "I don't want to manage session infrastructure"

## Requirements

google-login: Users authenticate via Google OAuth.

> "we'll just do Google login for now"
> @ C:oauth-only
> ~ src/api/auth/google.py
> ~ src/api/auth/callback.py

session-expiry: Sessions expire after 30 days of inactivity.

> "standard session timeout, nothing crazy"
> ! assumed 30 days — "nothing crazy" is unconfirmed
> @ C:jwt-stateless
> ~ src/middleware/session.py:44

admin-revoke: Admins can revoke any user session immediately. [planned]

> "need a kill switch for bad actors"
> ! assumed token blocklist approach — not stated by user
> @ session-expiry
> ? Q:admin-revoke-scope

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

## Code backlinks

Every function or class that implements a spec entry carries a `spec:` comment.
Language-agnostic, always the same format:

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

One comment per logical block. Multiple slugs on one line, comma-separated.
Place at the top of the block.

---

## The request flow

Every user request — new feature, change, fix, refactor — follows the same
sequence. There are no shortcuts. The sequence exists so the user always
understands what their request means in system terms before any code is written,
and so the spec stays accurate after the code is written.

```
Phase 1  Understand   read the spec, read the code if needed
Phase 2  Clarify      ask blocking questions, surface assumptions
Phase 3  Propose      tell the user what will change and why — get confirmation
Phase 4  Write spec   update the spec, validate
Phase 5  Implement    write the code with spec: backlinks
Phase 6  Sync         catch drift, update ~ refs, final validate + diff + commit
```

Never skip a phase. Never swap the order.

---

### Phase 1 — Understand

Before touching anything, read the spec:

```bash
prov orient              # full surface: domains, questions, backlog
prov find <keywords>     # check if related entries already exist
prov scope <path>        # if you know which files are affected
prov context <slug>      # full details on each affected entry
prov impact <slug>       # blast radius before changing anything
```

If you need to understand the current behavior from code, read the code referenced
by `~` lines in the affected entries. Read only — you are not changing anything yet.

---

### Phase 2 — Clarify

Identify everything the user did not specify. For each unknown:

- If it is **blocking** (you cannot design the behavior without it): ask.
- If it is **non-blocking** (you can proceed with a reasonable default): proceed,
  but mark it with a `!` assumption line. You will surface it in Phase 3.

**Questioning rules:**

- One question per message. Wait for the answer.
- Ask the most decision-blocking question first.
- Do not ask questions the spec already answers.
- Do not ask about competent-developer defaults (error handling, logging, etc.).

If the request contradicts an existing entry, stop here and surface it:

```
This request conflicts with an existing requirement:

  <slug>: <statement>
  > <provenance>

Options:
  A. Replace <slug> — the old behavior is removed
  B. Add alongside — requires clarifying the scope of <slug>
  C. Out of scope — this stays as-is, new behavior goes in ## Out of scope

Which should I do?
```

Wait for the user to choose before proceeding.

---

### Phase 3 — Propose

Once you understand the request and have resolved all blocking questions,
**propose the spec changes**. Do not write anything yet.

Tell the user all of the following:

**What entries will change:**
List every slug that will be added, modified, or removed, and which domain file
it lives in. For modifications, show the before and after statement.

**How the system will behave differently:**
Describe the change from the user's perspective. What can a user do now that
they could not before? What existing behavior changes?

**Which existing flows are affected:**
List any slug whose behavior, code refs, or dependencies will be touched — even
indirectly. Use `spec impact <slug>` to find these. Be explicit: "flow X changes
because it depends on <slug> which is being modified."

**What you are assuming:**
Every `!` assumption, stated in plain language. For each one, ask whether it is
correct or whether the user wants to specify the value.

**What is out of scope:**
Explicitly state what this change does NOT affect. This prevents misalignment.

Wait for the user to confirm before writing anything. If the user corrects
something, return to Phase 2 and revise.

---

### Phase 4 — Write the spec

After the user confirms the proposal:

```bash
prov check-slug <slug>   # before each new entry — verify availability
# Edit the spec domain .md file(s) directly
prov validate            # must pass with zero errors before continuing
prov diff                # show the user what changed
```

Rules:

- New entries go in the correct domain file under the correct section.
- Entries not yet implemented get `[planned]`.
- Every `!` assumption from Phase 3 appears as a `! assumption text` sub-line.
- Every entry has a `>` provenance line. No exceptions.

Surface any remaining `!` lines to the user for final confirmation before
moving to implementation.

---

### Phase 5 — Implement

Now write the code:

```bash
prov scope <file>        # confirm what governs the code you are about to write
```

- Implement exactly what the spec now says. No extras.
- Every function, class, or logical block that implements a spec entry carries
  a `spec: slug` comment at the top.
- Multiple slugs on one line, comma-separated: `# spec: slug-a, C:slug-b`

---

### Phase 6 — Sync and close

After implementation, catch any drift between what the spec says and what the
code actually does:

```bash
prov sync <path>         # read the full drift report
```

The sync report will show:

- **Silent implementations** — spec still says `[planned]` but code has `spec:` backlink
- **Phantom slugs** — `spec:` in code with no matching entry
- **Dead refs** — `~` path in spec no longer exists

For each item, apply the appropriate fix:

```bash
prov sync mark-implemented <slug>              # [planned] → implemented
prov sync remove-ref <slug> <ref>              # remove dead ~ ref
prov sync update-ref <slug> <old> <new>        # update moved ~ ref
prov sync remove-backlink <file> <line> <slug> # remove phantom spec: comment
```

Then close the session:

```bash
prov validate            # zero errors required
prov diff                # final review — show the user what changed
# Commit: spec + code together
# Message: feat(<domain>): <description>
#          spec: implement <slug>, add <slug>
```

---

### Debugging session

Debugging follows the same flow but starts from Phase 1 scoped to the bug:

```bash
prov scope <file-with-bug>   # what should this file do?
prov context <slug>          # full requirement details
```

Determine root cause:

- **Code deviates from spec** → fix the code. Spec unchanged.
- **Spec is wrong** → go through Phase 3 (propose updated spec) before fixing.
- **Spec has a gap** (`!` assumption) → surface the assumption first. Ask the user
  to confirm the correct behavior before fixing anything.

Then Phase 5 → Phase 6.

---

### Sync session — code and spec have drifted

When code and spec have drifted without going through the normal flow (e.g.
after a bulk refactor or after importing existing code):

```bash
prov sync src/           # full drift report
```

For each item in the report, present it to the user with context. Never apply
a fix without explicit user confirmation. Apply confirmed fixes with the sync
patch sub-commands above, then validate → diff → commit.

For a read-only drift report: `prov reconcile src/`

---

## CLI quick reference

Run `prov <command>` (or `python prov/prov.py <command>` if using project-local copy).
Always run from the project root; `prov` finds `prov/`, `spec/`, or `specs/` automatically.

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
prov reconcile <path>    # detect code↔spec drift (read-only report)
prov sync [path]         # interactive drift resolution (fix drift in-place)
prov rebuild             # rebuild cache from files
prov init                # scaffold CONTEXT.md (in a new project)
```

---

## Grep quick reference

Use grep directly for fast, simple queries. No CLI startup cost.

```bash
# Orientation
grep -rh "^>" spec/*.md spec/*/README.md   # domain summaries
grep -r "^Q:" spec/                          # open questions
grep -r "\[planned\]" spec/                  # backlog
grep -r "^  !" spec/                         # unconfirmed assumptions
grep -r "^C:" spec/                          # all constraints

# Finding
grep -r "^session-expiry:" spec/             # find entry by slug
grep -r "^  @ session-expiry" spec/          # what depends on this slug
grep -rn "spec: session-expiry" src/          # code implementing this slug
grep -r "~src/api/auth" spec/                # what specs own this code path

# Validation
grep -rh "^[a-z][a-z0-9-]*:\|^C:\|^Q:" spec/ \
  | cut -d: -f1,2 | sort | uniq -d            # find duplicate slugs
```

Use CLI when you need multi-hop traversal, formatted context packages, or
pre-built validation. Use grep when you need a fast existence check or a
single-pass surface scan.

---

## What the spec never contains

If you find yourself writing any of these, stop and delete it:

- "Previously this was X"
- "Changed from X to Y on [date]"
- "Deprecated — use `other-slug` instead"
- "We chose JWT because..."
- "This was decided in the session on..."
- Any description of how the system got to its current state
- Any entry without a `>` line
- Any implementation detail the user did not specify (without a `!` line)

The spec is always current. A well-maintained spec is indistinguishable from
one written in a single session with complete knowledge of the system.

---

## Handling contradictions

When a user request contradicts an existing spec entry, do not silently resolve
it. Surface it explicitly:

```
This request conflicts with an existing requirement:

  <slug>: <statement>
  > <provenance>

Options:
  A. Replace <slug> with the new behavior — the old behavior is removed
  B. Add the new behavior alongside the old — requires clarifying <slug>
  C. Treat this as out of scope — add to ## Out of scope

Which should I do?
```

Wait for the user to choose before acting.

---

## The assumption confirmation loop

Every `!` line represents a decision the user has not confirmed. When surfacing
spec changes to the user, highlight every new `!` line explicitly:

```
I've written the following spec entries. One assumption needs your confirmation:

  session-expiry: Sessions expire after 30 days of inactivity.
    ! assumed 30 days — you said "standard timeout, nothing crazy"

Is 30 days correct, or should it be different?
```

**When the user confirms:** Remove the `!` line. The spec now reads as user-specified.

**When the user corrects:** Rewrite the statement with the correct value. Remove the `!` line.

**When the user defers** ("decide for me" / "whatever is standard"): Keep the `!` line.
Do not remove it. It will appear in every future diff until the user explicitly
confirms the value. The `!` is the record that this was not their explicit choice.

---

## File format invariants — never violate these

1. Every primary entry starts at **column 0**. No leading spaces.
2. Every sub-line is indented **exactly 2 spaces**. Not 4. Not a tab.
3. The `~` sigil appears only on its own sub-line. Never inline in the statement.
4. Each entry has one statement line (the line with `slug: statement`).
   Multi-sentence statements on that one line are fine.

Violating any of these breaks the file parser and grep-based retrieval.

---

## Commit message format

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

---

## Fallback: when prov CLI is unavailable

If `prov` is not installed or `prov/prov.py` is absent, fall back to pure grep.
The spec is always readable without any tooling:

```bash
# orient
grep -rh "^>" spec/*.md spec/*/README.md
grep -r "^Q:" spec/
grep -r "\[planned\]" spec/
grep -r "^  !" spec/

# scope <file>
grep -r "~src/middleware/session" spec/
grep -r "~src/middleware/" spec/

# context <slug>
grep -A 20 "^session-expiry:" spec/

# partial validate
grep -rh "^[a-z][a-z0-9-]*:\|^C:\|^Q:" spec/ | cut -d: -f1,2 | sort | uniq -d
```

The CLI is a convenience layer. The files are always the truth.
