# CLI
> The prov command: typer app, structured queries, formatted context packages. Consume mode (scope, context, impact, find) and maintain mode (orient, domain, validate, diff, write, reconcile, sync, check-slug, rebuild, init).

## Constraints

C:minimal-deps: The prov CLI keeps runtime dependencies minimal — typer is the only runtime dependency; everything else is Python 3.9+ standard library.
  > user: "Use proper libraries etc (maybe typer etc)"

C:output-compat: Command stdout, stderr, and exit codes are user-facing behavior; refactors keep them byte-identical for existing commands, verified by golden-output diffing.
  > user: "I've used this for a while and I know it works. So keep the functionality the same."

## Requirements

cli-typer-interface: prov is a typer application: bare prov prints help, every command exposes --help, --version prints the installed package version, and completion install commands are available.
  > user: "REview the cli and make it proper full version with all the expected commands like --help etc. Use proper libraries etc (maybe typer etc)."
  ! usage errors exit 2 and command names are case-sensitive — typer defaults accepted as deviations from 0.1, not individually confirmed
  ~ src/prov/cli.py

structured-output: Every CLI command outputs structured plain text for direct inclusion in an agent's context window — formatted, labeled, actionable; not JSON or raw file content.
  > user: "Every command outputs structured plain text designed for direct inclusion in an agent's context window. Not JSON. Not raw file content."
  ~ src/prov/commands/
  ~ src/prov/format.py

backend-agnostic-output: CLI produces identical output regardless of which query backend (file, json, graphdb) is active. [planned]
  > user: "The CLI produces identical output regardless of which query backend is active."
  @ backend-interface

spec-orient: prov orient — start of maintain-mode session; output: === SPEC ORIENT ===, project/purpose from CONTEXT, hard constraints, DOMAINS table, OPEN QUESTIONS, UNCONFIRMED ASSUMPTIONS, PLANNED, DOMAIN COUPLING, next-step hint.
  > user: "Start of every maintain-mode session. Full product surface in a single structured package."
  ~ src/prov/commands/orient.py

spec-scope: prov scope <path> — before code work; input: file, directory, or file:line; output: every spec entry governing path (REQUIREMENTS, CONSTRAINTS, DEPENDED ON BY, OPEN QUESTIONS); or "No spec entries reference this path" with reconcile hint.
  > user: "An agent is about to read or modify code. Called before any code work. Compact; under 400 tokens."
  ~ src/prov/commands/scope.py

spec-context: prov context <slug> — full context for one entry; output: type, domain, implemented|planned, file path, statement, provenance, assumptions, code refs, constraints governing domain, depends on, depended on by, blocked by.
  > user: "Agent needs to deeply understand a single entry — before implementing, modifying, or reasoning about its behavior."
  ~ src/prov/commands/context.py

spec-impact: prov impact <slug> — before changing an entry or its code; output: direct dependents, transitive dependents, all code in blast radius, unconfirmed assumptions in path, planned entries in path.
  > user: "Before modifying, deleting, or significantly changing an entry or its code. Surfaces the full blast radius."
  ~ src/prov/commands/impact.py

spec-find: prov find <keywords> — free-text search when slug unknown; output: ranked matches (slug, domain, type, statement) or "No entries match" with orient hint.
  > user: "Agent doesn't know the slug. Searching by concept or description."
  ~ src/prov/commands/find.py

spec-domain: prov domain <name> — full domain load for editing; output: domain summary, file path, CONSTRAINTS, REQUIREMENTS (implemented/planned), OPEN QUESTIONS, OUT OF SCOPE.
  > user: "Maintain-mode agent loading a full domain to edit, review, or understand completely."
  ~ src/prov/commands/domain.py

spec-validate: prov validate — before every commit; non-zero exit on errors; reads canonical markdown and code backlinks directly and does not depend on `.spec/`. ERROR checks: dead-ref, phantom-slug, duplicate-slug, ghost-scope, dangling @ dep, dangling ? block. WARN: orphan-question. Unconfirmed ! assumptions are listed for review. Output: ERRORS, WARNINGS, UNCONFIRMED ASSUMPTIONS, CLEAN, Result. Exit 0 only when zero errors.
  > user: "Before every commit. Non-zero exit code if any errors are found. Exit code 0 only when zero errors. Validate must not require a generated .spec cache."
  ~ src/prov/commands/validate.py

spec-diff: prov diff [ref] — after writing/modifying specs; default ref HEAD. Output: semantic change manifest — IMPLEMENTED, NEW ENTRIES, MODIFIED, RESOLVED QUESTIONS, REMOVED ENTRIES, CONSTRAINTS CHANGED; assumptions requiring confirmation.
  > user: "After an agent writes or modifies specs. Produces the human review artifact."
  ~ src/prov/commands/diff.py

spec-write: prov write — structured input (JSON stdin or args): domain, entries (slug, type, statement, provenance, assumptions, planned, depends_on). Validates (slug available, deps exist, domain exists) then shows would-write block and Confirm; in autonomous mode agent writes and records in prov diff.
  > user: "Agent is capturing new requirements from a user conversation or request. Takes structured input, validates before writing."
  ~ src/prov/commands/write.py
  ~ src/prov/writer.py

spec-reconcile: prov reconcile <path> or --since <ref> — surfaces drift: phantom slugs (spec: in code, no entry), silent impl (planned in spec but code has spec:), dead refs (~ path not found). Output: sections for each drift type, CLEAN if none.
  > user: "Code has changed without the spec being updated. Surfaces drift between what the spec says and what the code contains."
  ~ src/prov/commands/reconcile.py

spec-sync: prov sync [path] — agent-facing drift report; detects phantom slugs, silent implementations, and dead refs; outputs structured plain text with resolution hints so the agent can discuss each item with the user and apply targeted fixes via patch sub-commands: mark-implemented <slug>, remove-ref <slug> <ref>, update-ref <slug> <old> <new>, remove-backlink <file> <line> <slug>; agent calls sub-commands after user confirms.
  > user: "Check the current spec and check the code. Understand drifts, ask clarifying questions to the user, and make sure we update the spec if required or update the code if required. All this should be handled by the agent."
  @ spec-reconcile
  ~ src/prov/commands/sync.py

spec-check-slug: prov check-slug <slug> — before writing new entry; output: TAKEN with file and entry snippet plus suggestions, or Available.
  > user: "Before writing any new entry, to verify the slug is available."
  ~ src/prov/commands/check_slug.py

rebuild-command: prov rebuild regenerates the optional `.spec/` cache from spec markdown files when explicitly requested; validate and the default pre-commit hook do not require it.
  > user: "prov rebuild regenerates .spec from markdown files when the user wants the optional cache."
  @ rebuild-from-files
  ~ src/prov/commands/rebuild.py

spec-init: prov init scaffolds CONTEXT.md in the spec directory (when absent) and installs the prov agent skills and rules; flags: --check (report per-file status, exit 1 if anything is missing or outdated, write nothing), --force (refresh modified skills), --no-agents / --no-claude / --no-open (skip asset classes).
  > user: "Give ways to init a repo where you can check if relevant skills and rules/agents,md are installed if not install them (prov related skills)"
  @ agent-assets-install
  ~ src/prov/commands/init.py

## Out of scope

Interactive terminal prompts for any command (agent drives the conversation). JSON output mode. Replacing grep for simple existence checks.

## Refs

~ src/prov/cli.py
~ src/prov/commands/
~ docs/cli.md
