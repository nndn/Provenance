---
name: spec-request-flow
version: "1.0"
triggers:
  - user request involving change, feature, fix, refactor, or question
  - starting a task that updates code or spec
  - implementing a requirement
  - debugging spec-related behavior
---

## Mission

Execute the six-phase spec-driven request flow for every task so that spec and code stay aligned and user expectations are captured before implementation.

---

## Pre-requisites

- **Spec directory** present: `prov/`, `spec/`, or `specs/` (or `$SPEC_DIR` set).
- **Read access** to spec markdown files.
- **grep** (or equivalent) — always available; use for orient, scope, slug lookup.
- **prov CLI** (optional): `prov orient`, `prov scope`, `prov context`, `prov impact`, `prov validate`, `prov sync`, `prov check-slug`, `prov diff`. If absent, use grep only; do not assume prov exists.

---

## Instructions

**Never skip a phase. Never swap the order.**

### Step 1 — Understand (Phase 1)

Before touching any file:

1. Orient: run the grep commands in Reference → Phase 1 commands below (domain summaries, open questions, planned, assumptions). If prov available: `prov orient`, `prov scope <path>`, `prov context <slug>`, `prov impact <slug>`.
2. For the path or slug in scope: find what governs it and get full entry context (see Reference).
3. Read code referenced by `~` lines in affected entries. **Read only — do not change yet.**

### Step 2 — Clarify (Phase 2)

1. Identify everything the user did not specify. **Blocking** (cannot design without it): ask the user. **Non-blocking** (reasonable default): proceed but add a `!` assumption; surface it in Step 3.
2. One question per message; ask the most decision-blocking question first. Do not ask what the spec already answers or about competent-developer defaults.
3. Extract implicit expectations: Does this request imply a behavior not in the spec? A number, threshold, or edge case? Capture in Step 3 and Step 4.
4. If the request **contradicts** an existing entry: stop and use the contradiction template in Reference. Wait for user choice (Replace / Add alongside / Out of scope) before proceeding.

### Step 3 — Propose (Phase 3)

1. Propose spec changes only. Do **not** write spec or code yet.
2. Tell the user: (1) slugs added/modified/removed and which domain file, before/after for edits, (2) how the system will behave differently for the user, (3) which flows are affected (use `prov impact <slug>`), (4) every `!` assumption in plain language and ask if each is correct, (5) what is out of scope.
3. Wait for confirmation. If the user corrects something, return to Step 2.

### Step 4 — Write the spec (Phase 4)

1. Run `grep -r "^<slug>:" spec/` or `prov check-slug <slug>` to verify slug availability.
2. Edit the correct domain `.md` file(s): new entries in the right section; unimplemented entries get `[planned]`; every `!` from Phase 3 as a `  ! assumption text` sub-line; **every entry has a `  > provenance` line. No exceptions.**
3. Run `prov validate` — fix until zero errors. Run `prov diff` and show the user. Surface any remaining `!` lines for confirmation before Step 5.

### Step 5 — Implement (Phase 5)

1. Run `prov scope <file>` to confirm what governs the code you are about to write.
2. Implement exactly what the spec says; no extras. Every function/class/logical block that implements a spec entry has `# spec: slug` at the top (multiple: `# spec: slug-a, C:slug-b`).

### Step 6 — Sync and close (Phase 6)

1. Run `prov sync <path>`. For each drift type use the fix from Reference → Drift fixes table. Then run `prov validate` (zero errors), `prov diff`. Commit spec and code together with the message format in Reference.

**Variants:**

- **Debugging:** Start at Step 1 scoped to the bug (`prov scope <file>`, `prov context <slug>`). Code deviates from spec → fix code, then Step 5 → 6. Spec is wrong → Step 3 → 4 → 5 → 6. Spec has a gap (`!`) → surface assumption, get confirmation, then Step 5 → 6.
- **Bulk drift:** Run `prov sync src/`. Present each item to the user with context; **never apply a fix without explicit user confirmation.** Apply confirmed fixes, then validate → diff → commit. Read-only: `prov reconcile src/`.

---

## Reference

### The six phases (reminder)

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

Spec updates happen in Phase 4 and Phase 6 — proactively, not only when asked.

### Phase 1 — Commands to run

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

If prov is available: `prov orient`, `prov find <keywords>`, `prov scope <path>`, `prov context <slug>`, `prov impact <slug>`.

### Contradiction template (Phase 2)

When the request contradicts an existing entry, stop and show:

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

### Phase 4 — Rules

- New entries go in the correct domain file under the correct section (## Constraints, ## Requirements, ## Open Questions).
- Entries not yet implemented get `[planned]`.
- Every `!` assumption from Phase 3 appears as a `  ! assumption text` sub-line.
- Every entry has a `  > provenance` line. No exceptions.

### Phase 6 — Drift fixes

| Drift | Fix |
|-------|-----|
| Silent impl — `[planned]` but code has `spec:` | `prov sync mark-implemented <slug>` |
| Phantom slug — `spec:` in code, no spec entry | `prov sync remove-backlink <file> <line> <slug>` or add the missing entry via request flow |
| Dead ref — `~` path no longer exists | `prov sync remove-ref <slug> <ref>` or `prov sync update-ref <slug> <old> <new>` |

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

## Error Handling

| If this happens | Do this |
|-----------------|--------|
| User request contradicts an existing spec entry | Stop. Surface the conflict using the contradiction template. Offer A. Replace / B. Add alongside / C. Out of scope. Do not proceed until user chooses. |
| User corrects your proposal in Phase 3 | Return to Phase 2 (Clarify). Revise assumptions and proposal; do not go to Phase 4 until user confirms again. |
| `prov validate` reports errors | Fix all errors (dead ref, phantom slug, duplicate slug, cycle, ghost scope, dangling dep). Do not commit until exit code 0. |
| `prov` CLI is not available | Use grep only for orient, scope, slug lookup, and dependents. Skip prov-only steps (impact, sync); document that drift check was skipped. |
| Spec directory not found | Do not guess. Ask user for the spec root path or set `SPEC_DIR`. Do not create a spec dir unless user explicitly asks (e.g. `prov init`). |
| You discover mid-task that you skipped a phase | Stop. Go back to the earliest skipped phase (usually Understand or Clarify), complete it, then continue in order. Do not skip again. |
