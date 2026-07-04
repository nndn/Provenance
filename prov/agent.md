# Agent
> Code-spec backlinks, agent integration rules, session protocols (coding, maintain, new feature, debugging, sync), validation rules, human review, and reconciliation.

## Constraints

C:scope-before-code: The agent always calls prov scope before touching code.
  > user: "The agent always calls prov scope before touching code."

C:validate-before-commit: The agent always calls prov validate before committing.
  > user: "The agent always calls prov validate before committing."

C:no-silent-gaps: Every detail the agent decides on the user's behalf (number, threshold, choice) gets a ! line; "it seemed obvious" is not an excuse.
  > user: "Never silently fill a gap. Every specific detail the agent decided on the user's behalf gets a ! line."

C:spec-code-same-commit: One commit contains both the spec change and the code change; never split them.
  > user: "One commit contains both the spec change and the code change. Never split them."

C:no-direct-cache-write: The agent never writes to `.spec/` directly. `.spec/` is a generated optional cache from markdown files; only explicit cache commands such as `prov rebuild` write it, and agents do not stage it unless the user asks.
  > user: "Never write to .spec/ directly. The .spec/ directory is generated from markdown files and is optional."

## Requirements

change-flow: Every user request is handled in six ordered phases — understand (read spec and code), clarify (ask blocking questions, assume non-blocking with ! lines), propose (tell the user what will change and confirm before writing anything), write spec (edit domain files, validate, diff), implement (code with spec: backlinks), sync (prov sync, apply drift fixes, validate, diff, commit); phases must not be skipped or reordered.
  > user: "Whenever a user asks for any new change, first we should be looking at this current spec, then looking at the references in the code if needed, and coming up with QA if necessary. First suggest an update to the spec, and the agent should tell how the system will change, what flows will change. Once the agent confirms the changes, the specs are updated and the code is updated subsequently."
  ~ src/prov/rules/spec-agent-protocol.md
  ~ src/prov/prompts/spec-agent.md

spec-backlink: Every function, class, or logical block that implements a spec entry carries a spec: comment at the top of the block; language-agnostic; one comment per block; multiple slugs comma-separated; slugs only, no description or file paths.
  > user: "Every function, class, or logical block that implements a spec entry carries a spec: comment. Language-agnostic, always the same format."
  ~ src/prov/indexing.py

coding-session-protocol: Coding session (consume mode): (1) prov scope <file>, (2) prov context <slug> if needed, (3) prov impact <slug> before significant changes, (4) make code changes, (5) prov validate, (6) prov diff, (7) commit spec + code together.
  > user: "Coding session (consume mode): prov scope, context, impact, make changes, validate, diff, commit together."
  @ spec-scope
  @ spec-validate
  ~ src/prov/rules/spec-agent-protocol.md

maintain-session-protocol: Maintain session: (1) prov orient, (2) prov domain <name>, (3) write or update spec entries, (4) prov validate, (5) prov diff, (6) commit.
  > user: "Spec maintenance session (maintain mode): orient, domain, write/update, validate, diff, commit."
  ~ src/prov/rules/spec-agent-protocol.md

new-feature-session-protocol: New feature session: (1) prov orient, (2) prov find <keywords>, (3) prov domain <affected-domain>, (4) clarify with user, (5) prov write, (6) prov validate, (7) prov diff, (8) implement code, (9) prov validate, (10) prov diff, (11) commit spec + code together.
  > user: "New feature session: orient, find, domain, clarify, write, validate, diff, implement, validate, diff, commit."
  ~ src/prov/skills/spec-request-flow/SKILL.md

debugging-session-protocol: Debugging session: (1) prov scope <file-with-bug>, (2) prov context <relevant-slug>, (3) debug and fix, (4) prov validate, (5) commit if spec needed updating.
  > user: "Debugging session: scope, context, debug and fix, validate, commit if spec updated."
  ~ src/prov/rules/spec-agent-protocol.md

assumption-confirmation: Human review of ! assumptions: confirm (remove !), correct (rewrite statement, remove !), or defer (keep !). prov diff is the primary surface; new ! always requires human review.
  > user: "The assumption confirmation flow. When a human sees ! assumed X in a diff, they have three options: Confirm, Correct, Defer."
  ~ src/prov/commands/diff.py

contradiction-surfacing: Before touching spec or code, if the request contradicts an existing entry, stop and surface: Understood, Contradiction (slug + statement), Options (Replace / Add variant / Out-of-scope reject), Question.
  > user: "If the request contradicts an existing entry, stop and surface the contradiction with options."
  ~ src/prov/rules/spec-agent-protocol.md

pre-commit-hook: Pre-commit hook: when staged spec markdown under prov/, spec/, or specs/ changes, or staged code changes add/remove `spec:` backlinks, run `prov validate` (exit 1 on errors). The hook does not rebuild or stage `.spec/` by default.
  > user: "If staged changes include spec markdown or spec: backlink changes, run prov validate. Do not rebuild or git add .spec by default."
  @ spec-validate
  @ cache-generated-optional
  ~ scripts/install-spec-pre-commit.sh

drift-reconciliation: prov reconcile <path> or --since <ref> surfaces phantom slugs, silent implementation, dead refs; output includes resolution hints. After autonomous code changes, run reconcile, validate, diff and include in PR description.
  > user: "Reconciliation handles the case where code diverged from spec. When an agent modifies code autonomously, run reconcile, validate, diff; include in PR description."
  ~ src/prov/commands/reconcile.py

sync-session-protocol: Sync session — agent-driven drift resolution: (1) prov sync <path> — read the full output; (2) present each drift item to the user with context; (3) ask the user what to do for each item (confirm intent before touching anything); (4) apply fixes via prov sync patch sub-commands or direct file edits; (5) prov validate; (6) prov diff; (7) commit spec + code together.
  > user: "All drift resolution should be handled by the agent. The agent reads the sync report, explains each item to the user, asks clarifying questions, and applies the agreed fixes."
  @ drift-reconciliation
  ~ src/prov/skills/spec-drift-sync/SKILL.md
  ~ src/prov/commands/sync.py

rules-self-heal: The installed rules instruct the agent, once per session at session start — never on every turn — to verify the prov skills are installed; if missing, run prov init to restore them; if the prov CLI itself is missing, install it with uv tool install provenance-cli (or pipx/pip), then continue with the task.
  > user: "Also make sure the rules/agents.md ask the agent to install the skill if not available when spec driven development is enabled in this repo (Ofcourse this shouldn't be done through tool calls every turn that will be bad experience)"
  @ agent-assets-install
  ~ src/prov/rules/project-rules.md

no-dead-ref: prov validate reports ERROR when a ~ path in the spec does not resolve to a real file or directory.
  > user: "Every ~ path in specs resolves to a real file or directory. dead-ref blocks commit."
  ~ src/prov/commands/validate.py

no-phantom-slug: prov validate reports ERROR when spec: slug in code has no matching entry in the spec.
  > user: "Every spec: in code has a matching entry in specs. phantom-slug blocks commit."
  ~ src/prov/commands/validate.py

no-duplicate-slug: prov validate reports ERROR when two entries share the same slug anywhere in the tree.
  > user: "All slugs are globally unique across the specs tree. duplicate-slug blocks commit."
  ~ src/prov/commands/validate.py

no-cycle: prov validate reports ERROR when a dependency chain forms a cycle. [planned]
  > user: "No dependency chain forms a cycle. dependency-cycle blocks commit."

no-ghost-scope: prov validate reports ERROR when an entry has no > line.
  > user: "Every node has a > line. ghost-scope blocks commit."
  ~ src/prov/commands/validate.py

no-dangling-dep: prov validate reports ERROR when an @ target does not exist as a slug in the spec tree.
  > user: "Every @ target exists as a slug in the specs tree. no-dangling-dep blocks commit."
  ~ src/prov/commands/validate.py

no-dangling-block: prov validate reports ERROR when a ? Q:slug target does not exist as a question node.
  > user: "Every ? Q:slug target exists as a question node. no-dangling-block blocks commit."
  ~ src/prov/commands/validate.py

validation-warnings: prov validate reports WARN for orphan-question (Q: not referenced by any ? line); warnings do not fail the build. Silent implementations and other drift are surfaced by prov reconcile and prov sync rather than validate.
  > user: "Warnings do not fail the build."
  ~ src/prov/commands/validate.py

## Out of scope

Enforcing protocols by tooling (agent follows protocol). MCP server (future). Evolutionary or historical language in spec entries.

## Refs

~ src/prov/rules/
~ src/prov/skills/
~ src/prov/prompts/
~ docs/agent-setup.md
