---
description: >
  Core spec-driven development protocol. Always apply. Governs every task —
  new feature, change, fix, refactor, or question — in any project that has
  a prov/, spec/, or specs/ directory. Enforces the six-phase request flow,
  the non-negotiable laws, and the expectation-capture principle.
alwaysApply: true
---

# Spec-Driven Agent Protocol

> Drop this file into `.cursorrules`, `CLAUDE.md`, `AGENTS.md`, `.gemini/GEMINI.md`,
> or any equivalent rules file your agent reads at session start.
> Full instructions: `src/prov/prompts/spec-agent.md`
> Skills directory: `src/prov/skills/`

---

## Core principle

**Every task is a chance to capture user expectations.** The spec is the compiled, correct record of what the system does and why. Complete the task AND keep the spec aligned with user intent. Over time, the spec becomes a reliable memory — not guesses, not implicit assumptions, but what the user actually expects.

The markdown files in `prov/`, `spec/`, or `specs/` are the source of truth. The CLI (`prov`) is a helper. When unavailable, use grep — the spec is always readable.

---

## The laws — apply without exception

1. **Read before write.** Never modify code or spec without first understanding what governs it. Use `prov scope <path>` or `grep -r "~<path>" spec/`.
2. **Every gap gets a `!` line.** Any value, threshold, or choice made on the user's behalf must be marked. "It seemed obvious" is never an excuse.
3. **Every entry needs a `>` line.** No entry exists without provenance. Use a source prefix: `user:`, `inferred:`, `code:`, `regulatory:`, `derived`. Quote the user where possible (`> user: "..."`). For agent interpretation use `> inferred:` with `!`. For code-derived use `> code:` with `!`. See spec-entry-format skill.
4. **Spec and code in the same commit.** Never split them.
5. **No evolutionary language.** The spec is always current. Never write "previously", "changed from", "deprecated". Git records history; the spec records intent.
6. **Never write to `.spec/`.** Machine-generated cache. The pre-commit hook manages it.
7. **Validate before every commit.** `prov validate` — zero errors is the only acceptable state.
8. **Spec before code.** Never write code without proposing the spec change and getting confirmation first.
9. **Capture expectations.** When a task reveals an expectation not in the spec, add or update an entry. Do not leave expectations only in code or conversation.

---

## THE REQUEST FLOW

**This is the protocol. Every task. No exceptions. Never skip a phase. Never swap the order.**

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Phase 1  UNDERSTAND   Read the spec; identify involved entries         │
│  Phase 2  CLARIFY      Ask blocking questions; extract implicit         │
│                        expectations; surface assumptions with !         │
│  Phase 3  PROPOSE      Show what changes and why; get confirmation      │
│  Phase 4  WRITE SPEC   Update spec files; validate; diff                │
│  Phase 5  IMPLEMENT    Write code with spec: backlinks                  │
│  Phase 6  SYNC         Catch drift; validate; diff; commit              │
└─────────────────────────────────────────────────────────────────────────┘
```

Spec updates happen in **Phase 4** and **Phase 6** — proactively, every time.

**Phase 1:** `grep -rh "^>" spec/*.md` · `grep -r "^Q:" spec/` · `grep -r "\[planned\]" spec/` · `grep -r "~<path>" spec/`. If prov available: `prov orient` · `prov scope <path>` · `prov context <slug>` · `prov impact <slug>`. Read code referenced by `~` lines. Do not change yet.

**Phase 2:** Blocking unknown → ask. Non-blocking → proceed with `!` assumption, surface in Phase 3. One question per message. If request contradicts an existing entry, stop and surface: slug + statement + Options (Replace / Add alongside / Out of scope). Wait for choice.

**Phase 3:** Propose only — do not write yet. Tell the user: (1) slugs added/modified/removed + which domain file + before/after, (2) how behavior changes for the user, (3) which flows are affected (`prov impact <slug>`), (4) every `!` assumption in plain language, (5) what is out of scope. Wait for confirmation.

**Phase 4:** Edit domain `.md` files. `prov check-slug <slug>` before writing. New entries get `[planned]` if not yet coded. Every `!` from Phase 3 as sub-line. Every entry has `> provenance` with source prefix per spec-entry-format. Run `prov validate` (zero errors) + `prov diff`. Surface remaining `!` lines before Phase 5.

**Phase 5:** `prov scope <file>` to confirm what governs the code. Implement exactly what the spec says — no extras. Every block that implements a spec entry: `# spec: slug` at the top. Multiple slugs comma-separated.

**Phase 6:** `prov sync <path>`. Fix silent implementations (`mark-implemented`), phantom slugs (`remove-backlink` or add entry), dead refs (`remove-ref` or `update-ref`). Then `prov validate` + `prov diff`. Commit spec + code together: `feat(<domain>): <description>` / `spec: implement <slug>, add <slug>`.

---

## Expectation capture — on every task

Before acting on any request, ask yourself:

1. Is there a behavior implied here that is not yet in the spec?
2. Would a future reader of the spec infer the same thing the user expects?
3. Is there a number, threshold, or edge case to record (with `!` if unconfirmed)?
4. Does this reveal a constraint that should govern an entire domain (`C:slug:`)?

If yes to any — capture it in Phase 3 and write it in Phase 4. Do not leave expectations only in code or conversation.

---

## Variant: Debugging

Phase 1 scoped to the bug: `prov scope <file>` · `prov context <slug>`. Then:
- Code deviates from spec → fix code (Phase 5 → 6). Spec unchanged.
- Spec is wrong → Phase 3 → 4 → 5 → 6.
- Spec has a gap (`!`) → surface assumption; get confirmation; then Phase 5 → 6.

## Variant: Drift / sync session

`prov sync src/`. For each item, present to the user with context. Never apply a fix without explicit confirmation. Apply fixes → `prov validate` → `prov diff` → commit. Read-only check: `prov reconcile src/`.

---

## Skills — load these for detailed guidance

| Situation | Load skill |
|-----------|-----------|
| Any task (detailed phase-by-phase steps) | `spec-request-flow` |
| Task implies unstated expectation; session start | `spec-capture-expectations` |
| Writing or editing spec files; adding backlinks | `spec-entry-format` |
| Resolving drift after bulk changes or refactors | `spec-drift-sync` |

Skills live in `src/prov/skills/<skill-name>/SKILL.md`.
Full agent instructions: `src/prov/prompts/spec-agent.md`.
