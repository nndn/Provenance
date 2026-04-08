---
description: >
  Skill routing guide for spec-driven development. Tells the agent which skill
  to load for each situation. Use alongside spec-agent-protocol. Load this when
  starting a session or task to know which skill covers the current situation.
alwaysApply: false
---

# Spec Skill Router

> When you are about to start work, use this table to identify which skill
> gives you the detailed guidance you need. Read the SKILL.md at the listed path.
> Skills live in `src/prov/skills/`.

---

## Which skill covers this situation?

| You are about to... | Load skill |
|---------------------|-----------|
| Handle any user request (feature, fix, change, refactor) | **`spec-request-flow`** |
| Start a new session or pick up a new task | **`spec-capture-expectations`** |
| Write or edit spec entries, add `~` refs, format entries correctly | **`spec-entry-format`** |
| Add `spec:` backlinks to code, format commits | **`spec-entry-format`** |
| Resolve drift after a bulk refactor or autonomous code change | **`spec-drift-sync`** |
| Run `prov sync` or `prov reconcile` | **`spec-drift-sync`** |
| A user request implies behavior not yet in the spec | **`spec-capture-expectations`** |

---

## What each skill covers

### `spec-request-flow`
The complete six-phase protocol with exact steps. Phase 1 (orient and read), Phase 2 (clarify and extract), Phase 3 (propose — do not write yet), Phase 4 (write spec), Phase 5 (implement), Phase 6 (sync and close). Also covers debugging and bulk-drift variants.

**Path:** `src/prov/skills/spec-request-flow/SKILL.md`
**Use when:** Any task involving a change. This skill is the main protocol.

---

### `spec-capture-expectations`
How to treat every task as a chance to compile user intent into the spec. Five questions to ask on every task. When to add vs skip entries. How to record implicit expectations with `!` lines. The assumption confirmation loop. The compounding spec principle.

**Path:** `src/prov/skills/spec-capture-expectations/SKILL.md`
**Use when:** Session start, any task where the user's words reveal an unstated expectation, any request that implies behavior not yet in the spec.

---

### `spec-entry-format`
The format reference. Node types (`slug:`, `C:slug:`, `Q:slug:`), sigils (`>`, `!`, `@`, `~`, `?`), provenance source types (user, inferred, code, regulatory, derived), slug rules, file format invariants (column-0, 2-space indent), complete domain file example, code backlink format, commit message format, grep patterns, prov CLI quick reference.

**Path:** `src/prov/skills/spec-entry-format/SKILL.md`
**Use when:** Writing spec entries, adding code backlinks, checking format, reading an unfamiliar entry structure.

---

### `spec-drift-sync`
The drift resolution protocol. Three drift types (silent implementation, phantom slug, dead ref). The sync session steps: run report, present each item to the user, confirm intent, apply patch commands. Resolution decision guide per drift type. What to do after autonomous code changes.

**Path:** `src/prov/skills/spec-drift-sync/SKILL.md`
**Use when:** Running `prov sync`, after bulk refactors, when code and spec are out of alignment, when preparing a PR after autonomous changes.

---

## How to use skills

1. Identify the situation from the table above.
2. Read the skill file: `src/prov/skills/<skill-name>/SKILL.md`.
3. Follow the guidance in the skill for the current task.
4. The skill may reference other skills — load those too if needed.

Skills are loaded on demand. They provide detailed, task-specific guidance that complements the always-on `spec-agent-protocol` rule.

---

## Full references

| Resource | Path | Purpose |
|----------|------|---------|
| Master protocol rule | `src/prov/rules/spec-agent-protocol.md` | Always-on: laws, flow, expectation capture |
| Skill router (this file) | `src/prov/rules/spec-skill-router.md` | When to load which skill |
| Full agent prompt | `src/prov/prompts/spec-agent.md` | Complete instructions for drop-in use |
| Request flow skill | `src/prov/skills/spec-request-flow/SKILL.md` | Detailed phase guidance |
| Capture expectations skill | `src/prov/skills/spec-capture-expectations/SKILL.md` | Expectation extraction |
| Entry format skill | `src/prov/skills/spec-entry-format/SKILL.md` | Format reference |
| Drift sync skill | `src/prov/skills/spec-drift-sync/SKILL.md` | Drift resolution |
