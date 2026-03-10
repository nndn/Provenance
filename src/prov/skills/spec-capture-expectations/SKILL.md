---
name: spec-capture-expectations
version: "1.0"
triggers:
  - session start or picking up a new task
  - user words imply a behavior, constraint, or rule not yet in the spec
  - request reveals an assumption, edge case, or threshold to write down
  - deciding whether to add or update a spec entry
---

## Mission

On every task, extract implicit user expectations and compile them into the spec so the spec remains the single, correct record of what the user expects — not what was guessed or left in conversation.

---

## Pre-requisites

- **Spec directory** present: `prov/`, `spec/`, or `specs/`.
- **Read access** to existing spec files (to check what is already captured).
- **Write access** to spec files when adding or updating entries (only after user confirms in Phase 3 of the request flow).

---

## Instructions

### Step 1 — Before acting, run the five questions

For the current request, answer (see Reference for detail):

1. Is there a behavior implied here that is not yet in the spec?
2. Would a future reader of the spec infer the same thing the user expects?
3. Is there a number, threshold, limit, or edge case the user assumed?
4. Does this reveal a domain-wide constraint ("always", "never")?
5. Is an existing entry now wrong or incomplete?

### Step 2 — Decide: add, update, or skip

Use the tables in Reference: **When to add a new entry** and **When NOT to add**. Add when user states or implies a behavior, specifies a constraint, an edge case is missing, or a bug fix reveals correct behavior never specified. Do not add for competent-developer defaults, implementation-only details, or duplicates.

### Step 3 — Record implicit expectations in the right form

- User’s words reveal unstated behavior → add requirement with `>` quoting them and `~` when implemented (see Reference example).
- You infer a value they didn’t give (e.g. "keep it fast") → add entry with `> "user quote"` and `  ! assumed <value> — <reason unconfirmed>`. Surface the `!` in Phase 3; user confirms, corrects, or defers (see Reference example).

### Step 4 — Apply assumption discipline

Every gap you fill on the user’s behalf gets a `!` line. When surfacing `!`: **Confirm** → remove `!`; **Correct** → rewrite statement, remove `!`; **Defer** → keep `!` (it will appear in every future diff until confirmed). See Reference → Assumption discipline.

### Step 5 — Feed into the request flow

All new or changed entries are proposed in Phase 3 and written in Phase 4 of the request flow. Do not add entries without going through the flow (propose → confirm → write).

---

## Reference

### The principle

Every task is a chance to compile user intent into the spec. A well-maintained spec is one where a fresh agent, given only the spec and no prior context, would produce a system that matches everything the user actually expects. Never leave expectations only in code or only in conversation — compile them.

### Five questions (detail)

1. **Is there a behavior implied here that is not yet written in the spec?** If the user's request assumes something works a certain way and the spec doesn't say so, that's a missing entry.
2. **Would a future reader of the spec infer the same thing the user expects?** If not, update the entry — wrong statement, missing constraint, wrong scope.
3. **Is there a number, threshold, limit, or edge case the user assumed?** Record in the spec with a `!` line if unconfirmed, or as a confirmed statement if they said it.
4. **Does this reveal a domain-wide constraint?** If the user says "always", "never", or "under no circumstances", that's a `C:slug:` constraint entry, not just a requirement.
5. **Is an existing entry now wrong or incomplete?** The new request may reveal that an old entry was imprecise; update it in the same task.

### When to add a new entry

| Signal | Action |
|--------|--------|
| User states a behavior explicitly | Add requirement entry with `>` quoting their words |
| User implies a behavior ("obviously it should...") | Add entry with `> inferred from: <reasoning>` and `!` line |
| User specifies a constraint ("always", "never", "required") | Add `C:slug:` constraint entry |
| User's request would fail in an edge case not yet covered | Add entry for that edge case |
| Fixing a bug reveals the correct behavior was never specified | Add entry for the correct behavior |
| User corrects the agent's assumption | Remove `!`, update the statement to match the correction |

### When NOT to add a new entry

- Competent-developer defaults (error handling, logging patterns, standard HTTP responses) — skip.
- Implementation details the user never mentioned and that don't affect user-observable behavior — skip.
- Anything already correctly covered by an existing entry — skip; don't duplicate.

### How to record an implicit expectation — examples

**User's words reveal unstated behavior:**

```
user: "make sure the export always includes the full history"
```

→ Add:

```
export-full-history: Exports always include the complete history of the record.
  > "make sure the export always includes the full history"
  ~ src/exports/history.py
```

**You infer a value they didn't give:**

```
user: "keep it fast"
```

→ "Fast" is unspecified. Add:

```
export-performance: Export completes within 5 seconds for records up to 10,000 entries. [planned]
  > "keep it fast"
  ! assumed 5s / 10k entries — "fast" is unconfirmed
```

Surface the `!` in Phase 3. The user either confirms, corrects, or defers.

### Assumption discipline

- `!` = "I decided this; the user has not confirmed it."
- No `!` = "The user said this, or it's an unambiguous default."
- When you surface a `!` to the user: **Confirm** → remove `!` (becomes user-specified). **Correct** → rewrite statement, remove `!`. **Defer** → keep `!`; do not remove it; it will appear in every future diff until the user explicitly confirms. The `!` is the record that this was not their explicit choice.

### The compounding spec

Over time, with every task handled this way, the spec converges on a complete, accurate picture of user intent. Each task adds signal. The spec becomes the memory of the system — not what the agent guessed, not what was obvious in the moment, but what the user actually wants. Never leave an expectation only in code. Never leave it only in conversation. Compile it.

---

## Error Handling

| If this happens | Do this |
|-----------------|--------|
| You're unsure whether something is user expectation or implementation detail | Prefer capturing it with a `!` line so the user can confirm or remove. Do not leave it only in code. |
| User said something vague ("fast", "simple") and you chose a concrete value | Add a `!` line stating the assumed value and that the original was unconfirmed. Surface in Phase 3; do not remove `!` without user action. |
| You find an existing entry that's wrong but the user didn't ask to change it | Include the correction in your Phase 3 proposal ("I'm also updating X because the current spec says Y and the code/behavior is Z"). Get explicit confirmation. |
| You already added an entry and the user says "that's not what I meant" | Treat as correction: update the statement and provenance, remove or adjust `!`. Do not leave the wrong entry in place. |
| Multiple possible interpretations of the user's words | Propose one interpretation with a `!` line; in Phase 3 list the alternatives and ask which one they want. Do not implement until they choose. |
