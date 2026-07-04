# Spec-Driven Agent Rules (prov)

**Core principle:** Every task is a chance to capture user expectations. The spec — markdown in `prov/`, `spec/`, or `specs/` — is the source of truth: the compiled, correct record of what the system does and why. Complete the task AND keep the spec aligned with user intent. The `prov` CLI is a helper; when unavailable, use grep — the spec is always readable.

## The laws — apply without exception

1. **Read before write.** `prov scope <path>` or `grep -r "~ <path>" prov/` before touching code or spec.
2. **Every gap gets a `!` line.** Any value, threshold, or choice made on the user's behalf is marked.
3. **Every entry needs a `>` provenance line.** Source prefix: `user:`, `inferred:`, `code:`, `regulatory:`, `derived:`. Quote the user where possible.
4. **Spec and code in the same commit.** Never split them.
5. **No evolutionary language.** The spec is always current; git records history.
6. **Never write to `.spec/`.** Generated cache; only `prov rebuild` when explicitly asked.
7. **Validate before every commit.** `prov validate` — zero errors only.
8. **Spec before code.** Propose the spec change and get confirmation first.
9. **Capture expectations.** Never leave expectations only in code or conversation.

## The request flow — every task, in order, no skipped phases

| Phase | Name | Action |
|-------|------|--------|
| 1 | UNDERSTAND | Read the spec; identify involved entries (`prov orient`, `prov scope <path>`) |
| 2 | CLARIFY | Ask blocking questions; extract implicit expectations; mark assumptions with `!` |
| 3 | PROPOSE | Show what changes and why; get confirmation before writing |
| 4 | WRITE SPEC | Update domain files; `prov validate`; `prov diff` |
| 5 | IMPLEMENT | Write code with `spec:` backlinks |
| 6 | SYNC | `prov sync`; fix drift; validate; diff; commit spec + code together |

## Skills — load for detailed guidance

Installed at `.claude/skills/<name>/SKILL.md` (Claude) or `.agents/skills/<name>/SKILL.md` (open standard).

| Situation | Load skill |
|-----------|-----------|
| Any task (detailed phase-by-phase steps) | `spec-request-flow` |
| Session start; task implies unstated expectation | `spec-capture-expectations` |
| Writing or editing spec files; adding backlinks | `spec-entry-format` |
| Resolving drift after bulk changes or refactors | `spec-drift-sync` |

## Self-heal

Spec-driven development is enabled in this repo (`prov/` spec directory present). Once per session at session start — never on every turn — verify the prov skills are installed (`.claude/skills/spec-*` or `.agents/skills/spec-*`). If missing, run `prov init` to restore them; if the prov CLI itself is missing, install it with `uv tool install provenance-cli` (or pipx/pip). Then continue with the task.
