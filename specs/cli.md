# CLI

> prov.py: structured queries, formatted context packages, and backend-agnostic command output. Consume mode (scope, context, impact, find) and maintain mode (orient, domain, validate, diff, write, reconcile, check-slug).

## Constraints

C:cli-stdlib-only: prov.py requires only Python 3.9+ standard library; no external dependencies.

> "It requires only Python 3.9+ standard library. No external dependencies."

## Requirements

structured-output: Every CLI command outputs structured plain text for direct inclusion in an agent's context window — formatted, labeled, actionable; not JSON or raw file content.

> "Every command outputs structured plain text designed for direct inclusion in an agent's context window. Not JSON. Not raw file content."
> [planned]

backend-agnostic-output: CLI produces identical output regardless of which query backend (file, json, graphdb) is active.

> "The CLI produces identical output regardless of which query backend is active."
> @ backend-interface
> [planned]

spec-orient: prov orient — start of maintain-mode session; output: === SPEC ORIENT ===, project/purpose from CONTEXT, hard constraints, DOMAINS table, OPEN QUESTIONS, UNCONFIRMED ASSUMPTIONS, PLANNED, DOMAIN COUPLING, next-step hint.

> "Start of every maintain-mode session. Full product surface in a single structured package."
> [planned]

spec-scope: prov scope <path> — before code work; input: file, directory, or file:line; output: every spec entry governing path (REQUIREMENTS, CONSTRAINTS, DEPENDED ON BY, OPEN QUESTIONS); or "No spec entries reference this path" with reconcile hint.

> "An agent is about to read or modify code. Called before any code work. Compact; under 400 tokens."
> [planned]

spec-context: prov context <slug> — full context for one entry; output: type, domain, implemented|planned, file path, statement, provenance, assumptions, code refs, constraints governing domain, depends on, depended on by, blocked by.

> "Agent needs to deeply understand a single entry — before implementing, modifying, or reasoning about its behavior."
> [planned]

spec-impact: prov impact <slug> — before changing an entry or its code; output: direct dependents, transitive dependents, all code in blast radius, unconfirmed assumptions in path, planned entries in path.

> "Before modifying, deleting, or significantly changing an entry or its code. Surfaces the full blast radius."
> [planned]

spec-find: prov find <keywords> — free-text search when slug unknown; output: ranked matches (slug, domain, type, statement) or "No entries match" with orient hint.

> "Agent doesn't know the slug. Searching by concept or description."
> [planned]

spec-domain: prov domain <name> — full domain load for editing; output: domain summary, file path, CONSTRAINTS, REQUIREMENTS (implemented/planned), OPEN QUESTIONS, OUT OF SCOPE.

> "Maintain-mode agent loading a full domain to edit, review, or understand completely."
> [planned]

spec-validate: prov validate — before every commit; non-zero exit on errors. Checks: dead-ref, phantom-slug, duplicate-slug, dependency-cycle, ghost-scope (ERROR); silent-impl, orphan-question, orphan-entry (WARN); unconfirmed-assumption (INFO). Output: ERRORS, WARNINGS, UNCONFIRMED ASSUMPTIONS, CLEAN, Result. Exit 0 only when zero errors.

> "Before every commit. Non-zero exit code if any errors are found. Exit code 0 only when zero errors."
> [planned]

spec-diff: prov diff [ref] — after writing/modifying specs; default ref HEAD. Output: semantic change manifest — IMPLEMENTED, NEW ENTRIES, MODIFIED, RESOLVED QUESTIONS, REMOVED ENTRIES, CONSTRAINTS CHANGED; assumptions requiring confirmation.

> "After an agent writes or modifies specs. Produces the human review artifact."
  ~ src/prov.py:1134

spec-write: prov write — structured input (JSON stdin or args): domain, entries (slug, type, statement, provenance, assumptions, planned, depends_on). Validates (slug available, deps exist, domain exists) then shows would-write block and Confirm; in autonomous mode agent writes and records in prov diff.

> "Agent is capturing new requirements from a user conversation or request. Takes structured input, validates before writing."
  ~ src/prov.py:914

spec-reconcile: prov reconcile <path> or --since <ref> — surfaces drift: phantom slugs (spec: in code, no entry), silent impl ([planned] but code has spec:), dead refs (~ path not found). Output: sections for each drift type, CLEAN if none.

> "Code has changed without the spec being updated. Surfaces drift between what the spec says and what the code contains."
> [planned]

spec-sync: prov sync [path] — agent-facing drift report; detects phantom slugs, silent implementations, and dead refs; outputs structured plain text with resolution hints so the agent can discuss each item with the user and apply targeted fixes via patch sub-commands: mark-implemented <slug>, remove-ref <slug> <ref>, update-ref <slug> <old> <new>, remove-backlink <file> <line> <slug>; agent calls sub-commands after user confirms.

> "Check the current spec and check the code. Understand drifts, ask clarifying questions to the user, and make sure we update the spec if required or update the code if required. All this should be handled by the agent."
> @ spec-reconcile
  ~ src/prov.py

spec-check-slug: prov check-slug <slug> — before writing new entry; output: TAKEN with file and entry snippet plus suggestions, or Available.

> "Before writing any new entry, to verify the slug is available."
> [planned]

rebuild-command: spec rebuild (or equivalent) regenerates cache from spec files when stale, corrupt, or absent.

> "python prov/prov.py rebuild regenerates it from the files in seconds."
> @ rebuild-from-files
  ~ src/prov.py:809

## Out of scope

Interactive terminal prompts for any command (agent drives the conversation). JSON output mode. Replacing grep for simple existence checks.

## Refs

~ ARCHITECTURE.md
