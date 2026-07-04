# Format
> DSL embedded in markdown: column-0 entries, 2-space sub-lines, node types, edge sigils, slug and file-structure rules.

## Constraints

C:column-zero: Every primary entry starts at column 0. Violating this breaks grep-based retrieval and the file parser.
  > user: "Every primary entry starts at column 0"

C:two-space-indent: Every sub-line is indented exactly 2 spaces. Violating this breaks grep-based retrieval and the file parser.
  > user: "Every sub-line is indented exactly 2 spaces"

C:slug-unique: Slugs are globally unique across the entire spec tree. Check with prov check-slug or grep before writing.
  > user: "Slugs are globally unique across the entire specs/ tree"

C:slug-permanent: Once written and referenced in code, a slug does not change; the slug is a stable handle, not a description.
  > user: "Slugs are permanent. Rename cost is high — choose carefully upfront."

## Requirements

requirement-node: Requirement entries use bare slug at column 0, statement, optional planned marker; sub-lines > provenance, ! assumption, ~ code-ref, @ depends-on, ? blocked-by.
  > user: "Requirements — observable behaviors the user expects. Use bare slug:."
  ~ src/prov/spec_io.py

constraint-node: Constraint entries use C:slug: prefix at column 0, statement; sub-lines > provenance, optional ! and ~; never planned — constraints are active or they don't exist; referenced from requirements via @ C:slug.
  > user: "Constraints — non-negotiable rules that govern all requirements in the domain. Use C:slug: prefix."
  ~ src/prov/spec_io.py

question-node: Open-question entries use Q:slug: prefix at column 0, question statement; sub-line > what this blocks; deleted when resolved.
  > user: "Open Questions — unresolved decisions that block implementation. Use Q:slug: prefix. Always include a > line stating what they block."
  ~ src/prov/spec_io.py

provenance-required: Every node has a > line (provenance). An entry with no > line is a ghost-scope error.
  > user: "> is required on every node. No exceptions. An entry with no > line is a ghost-scope error."
  ~ src/prov/commands/validate.py

assumption-disclosure: Whenever the agent fills a gap (number, threshold, choice, unspecified behavior), a ! line is required. "It seemed obvious" is not an excuse.
  > user: "! is required whenever the agent fills a gap. Any detail the agent decided on the user's behalf gets a ! line."
  ~ src/prov/rules/spec-agent-protocol.md

code-ref-sublines: Code refs use ~ on dedicated sub-lines (2-space indent), one per line; never inline in the entry statement.
  > user: "~ moves to sub-lines. Never inline in the entry statement. Multiple code refs are now unambiguous."
  ~ src/prov/spec_io.py

planned-marker: Unimplemented requirements carry the planned marker on the statement line until implemented; then add ~ refs, remove the marker, confirm or remove ! lines in one edit.
  > user: "[planned] marks unimplemented requirements. When a requirement is implemented: add ~ ref sub-lines, remove [planned], confirm or remove ! lines. One edit."
  ~ src/prov/spec_io.py
  ~ src/prov/commands/sync.py

slug-format: Slugs are kebab-case, 2–4 words, describing the behavior not the domain. A developer reading only spec: slug in code should understand the constraint without loading the spec.
  > user: "Format: kebab-case, 2–4 words, describing the behavior not the domain. The behavior test."
  @ C:slug-unique
  @ C:slug-permanent
  ~ src/prov/commands/check_slug.py

domain-file: Line 2 of every domain file is a > one-line summary (domain identity); appears in prov orient; write so an agent can decide whether to load the file.
  > user: "Line 2 of every file is a > one-line summary. This is the domain's identity string."
  ~ src/prov/spec_io.py

domain-split: Split a domain into a folder when any of: more than 15 requirements in one file; a sub-domain has 5+ requirements; one section longer than rest combined; ## Refs lists 3+ distinct source subdirectories. After split: README.md as domain index, sub-domain .md files; slugs travel with content, zero reference updates.
  > user: "Split thresholds — any one triggers a split. Slugs travel with content. IDs are never renumbered — slugs are the identity."
  ~ docs/architecture.md

context-file: CONTEXT.md contains project name, one-line summary, purpose, user goals, hard constraints, non-goals, domain map; no requirements; establishes context before loading any domain file.
  > user: "CONTEXT.md contains no requirements. It establishes the context every agent session needs before loading any domain file."
  ~ src/prov/spec_io.py

out-of-scope-section: Each domain file has ## Out of scope as a short bullet list to kill incorrect assumptions before they form; constraint on imagination, not documentation.
  > user: "## Out of scope — short bullet list. Its purpose is to kill incorrect assumptions before they form."
  ~ src/prov/commands/domain.py

refs-section: Each domain file has ## Refs listing primary code paths the domain owns; agents use it for impact analysis without scanning every inline ~.
  > user: "## Refs — the primary code paths this domain owns. An agent doing impact analysis reads this section."
  ~ src/prov/spec_io.py
  ~ src/prov/indexing.py

## Out of scope

Inline code refs in entry statements. Numeric IDs for entries. Domain prefix in slugs.

## Refs

~ docs/spec-format.md
~ src/prov/spec_io.py
