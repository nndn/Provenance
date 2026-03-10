# Agent

> Code-spec backlinks, agent integration rules, session protocols (coding, maintain, new feature, debugging), validation rules, human review, and reconciliation.

## Constraints

C:scope-before-code: The agent always calls spec scope before touching code.

> "The agent always calls spec scope before touching code."

C:validate-before-commit: The agent always calls spec validate before committing.

> "The agent always calls spec validate before committing."

C:no-silent-gaps: Every detail the agent decides on the user's behalf (number, threshold, choice) gets a ! line; "it seemed obvious" is not an excuse.

> "Never silently fill a gap. Every specific detail the agent decided on the user's behalf gets a ! line."

C:spec-code-same-commit: One commit contains both the spec change and the code change; never split them.

> "One commit contains both the spec change and the code change. Never split them."

C:no-direct-cache-write: The agent never writes to .spec/ directly; the cache is machine-generated from the markdown files; CLI and pre-commit hook manage it.

> "Never write to .spec/ directly. The .spec/ directory is machine-generated from the markdown files."

## Requirements

change-flow: Every user request is handled in six ordered phases — understand (read spec and code), clarify (ask blocking questions, assume non-blocking with ! lines), propose (tell the user what will change and confirm before writing anything), write spec (edit domain files, validate, diff), implement (code with spec: backlinks), sync (spec sync, apply drift fixes, validate, diff, commit); phases must not be skipped or reordered.

> "Whenever a user asks for any new change, first we should be looking at this current spec, then looking at the references in the code if needed, and coming up with QA if necessary. First suggest an update to the spec, and the agent should tell how the system will change, what flows will change. Once the agent confirms the changes, the specs are updated and the code is updated subsequently."
  ~ prompts/spec-agent.md

spec-backlink: Every function, class, or logical block that implements a spec entry carries a spec: comment at the top of the block; language-agnostic; one comment per block; multiple slugs comma-separated; slugs only, no description or file paths.

> "Every function, class, or logical block that implements a spec entry carries a spec: comment. Language-agnostic, always the same format."
> [planned]

coding-session-protocol: Coding session (consume mode): (1) spec scope <file>, (2) spec context <slug> if needed, (3) spec impact <slug> before significant changes, (4) make code changes, (5) spec validate, (6) spec diff, (7) commit spec + code together.

> "Coding session (consume mode): spec scope, context, impact, make changes, validate, diff, commit together."
> @ spec-scope
> @ spec-validate
> [planned]

maintain-session-protocol: Maintain session: (1) spec orient, (2) spec domain <name>, (3) write or update spec entries, (4) spec validate, (5) spec diff, (6) commit.

> "Spec maintenance session (maintain mode): orient, domain, write/update, validate, diff, commit."
> [planned]

new-feature-session-protocol: New feature session: (1) spec orient, (2) spec find <keywords>, (3) spec domain <affected-domain>, (4) clarify with user, (5) spec write, (6) spec validate, (7) spec diff, (8) implement code, (9) spec validate, (10) spec diff, (11) commit spec + code together.

> "New feature session: orient, find, domain, clarify, write, validate, diff, implement, validate, diff, commit."
> [planned]

debugging-session-protocol: Debugging session: (1) spec scope <file-with-bug>, (2) spec context <relevant-slug>, (3) debug and fix, (4) spec validate, (5) commit if spec needed updating.

> "Debugging session: scope, context, debug and fix, validate, commit if spec updated."
> [planned]

assumption-confirmation: Human review of ! assumptions: confirm (remove !), correct (rewrite statement, remove !), or defer (keep !). spec diff is the primary surface; new ! always requires human review.

> "The assumption confirmation flow. When a human sees ! assumed X in a diff, they have three options: Confirm, Correct, Defer."
> [planned]

contradiction-surfacing: Before touching spec or code, if the request contradicts an existing entry, stop and surface: Understood, Contradiction (slug + statement), Options (Replace / Add variant / Out-of-scope reject), Question.

> "If the request contradicts an existing entry, stop and surface the contradiction with options."
> [planned]

pre-commit-hook: Pre-commit hook: when specs/ (or spec/) files are staged, run spec validate (exit 1 on errors), then rebuild cache and git add .spec/.

> "If git diff --cached includes spec files, run spec validate; on success run rebuild and git add .spec/."
> @ spec-validate
> @ cache-committed
> [planned]

drift-reconciliation: spec reconcile <path> or --since <ref> surfaces phantom slugs, silent implementation, dead refs; output includes resolution hints. After autonomous code changes, run reconcile, validate, diff and include in PR description.

> "Reconciliation handles the case where code diverged from spec. When an agent modifies code autonomously, run reconcile, validate, diff; include in PR description."
> [planned]

sync-session-protocol: Sync session — agent-driven drift resolution: (1) spec sync <path> — read the full output; (2) present each drift item to the user with context; (3) ask the user what to do for each item (confirm intent before touching anything); (4) apply fixes via spec sync patch sub-commands or direct file edits; (5) spec validate; (6) spec diff; (7) commit spec + code together.

> "All drift resolution should be handled by the agent. The agent reads the sync report, explains each item to the user, asks clarifying questions, and applies the agreed fixes."
> @ drift-reconciliation
  ~ src/spec.py

no-dead-ref: spec validate reports ERROR when a ~ path in specs does not resolve to a real file or directory.

> "Every ~ path in specs resolves to a real file or directory. dead-ref blocks commit."
> [planned]

no-phantom-slug: spec validate reports ERROR when spec: slug in code has no matching entry in specs.

> "Every spec: in code has a matching entry in specs. phantom-slug blocks commit."
> [planned]

no-duplicate-slug: spec validate reports ERROR when two entries share the same slug anywhere in the tree.

> "All slugs are globally unique across the specs tree. duplicate-slug blocks commit."
> [planned]

no-cycle: spec validate reports ERROR when a dependency chain forms a cycle.

> "No dependency chain forms a cycle. dependency-cycle blocks commit."
> [planned]

no-ghost-scope: spec validate reports ERROR when an entry has no > line.

> "Every node has a > line. ghost-scope blocks commit."
> [planned]

no-dangling-dep: spec validate reports ERROR when an @ target does not exist as a slug in the specs tree.

> "Every @ target exists as a slug in the specs tree. no-dangling-dep blocks commit."
> [planned]

no-dangling-block: spec validate reports ERROR when a ? Q:slug target does not exist as a question node.

> "Every ? Q:slug target exists as a question node. no-dangling-block blocks commit."
> [planned]

validation-warnings: spec validate reports WARN for silent-impl ([planned] but code has spec:), orphan-question (Q: not referenced by any ?), orphan-entry (no ~ refs, no @ dependents, not planned); warnings do not fail the build.

> "Warnings: silent-impl, orphan-question, orphan-entry. Warnings do not fail the build."
> [planned]

## Out of scope

Enforcing protocols by tooling (agent follows protocol). MCP server (future). Evolutionary or historical language in spec entries.

## Refs

~ sdd/spec-spec.md
