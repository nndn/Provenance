# Format

> DSL embedded in markdown: column-0 entries, 2-space sub-lines, node types, edge sigils, slug and file-structure rules.

## Constraints

C:column-zero: Every primary entry starts at column 0. Violating this breaks grep-based retrieval and the file parser.

> "Every primary entry starts at column 0"

C:two-space-indent: Every sub-line is indented exactly 2 spaces. Violating this breaks grep-based retrieval and the file parser.

> "Every sub-line is indented exactly 2 spaces"

C:slug-unique: Slugs are globally unique across the entire spec tree. Check with spec check-slug or grep before writing.

> "Slugs are globally unique across the entire specs/ tree"

C:slug-permanent: Once written and referenced in code, a slug does not change; the slug is a stable handle, not a description.

> "Slugs are permanent. Rename cost is high — choose carefully upfront."

## Requirements

requirement-node: Requirement entries use bare slug at column 0, statement, optional [planned]; sub-lines > provenance, ! assumption, ~ code-ref, @ depends-on, ? blocked-by.

> "Requirements — observable behaviors the user expects. Use bare slug:."
> [planned]

constraint-node: Constraint entries use C:slug: prefix at column 0, statement; sub-lines > provenance, optional ! and ~; no [planned]; referenced from requirements via @ C:slug.

> "Constraints — non-negotiable rules that govern all requirements in the domain. Use C:slug: prefix."
> [planned]

question-node: Open-question entries use Q:slug: prefix at column 0, question statement; sub-line > what this blocks; deleted when resolved.

> "Open Questions — unresolved decisions that block implementation. Use Q:slug: prefix. Always include a > line stating what they block."
> [planned]

provenance-required: Every node has a > line (provenance). An entry with no > line is a ghost-scope error.

> "> is required on every node. No exceptions. An entry with no > line is a ghost-scope error."
> [planned]

assumption-disclosure: Whenever the agent fills a gap (number, threshold, choice, unspecified behavior), a ! line is required. "It seemed obvious" is not an excuse.

> "! is required whenever the agent fills a gap. Any detail the agent decided on the user's behalf gets a ! line."
> [planned]

code-ref-sublines: Code refs use ~ on dedicated sub-lines (2-space indent), one per line; never inline in the entry statement.

> "~ moves to sub-lines. Never inline in the entry statement. Multiple code refs are now unambiguous."
> [planned]

planned-marker: Unimplemented requirements carry [planned] until implemented; then add ~ refs, remove [planned], confirm or remove ! lines in one edit.

> "[planned] marks unimplemented requirements. When a requirement is implemented: add ~ ref sub-lines, remove [planned], confirm or remove ! lines. One edit."
> [planned]

slug-format: Slugs are kebab-case, 2–4 words, describing the behavior not the domain. A developer reading only spec: slug in code should understand the constraint without loading the spec.

> "Format: kebab-case, 2–4 words, describing the behavior not the domain. The behavior test."
> @ C:slug-unique
> @ C:slug-permanent
> [planned]

domain-file: Line 2 of every domain file is a > one-line summary (domain identity); appears in spec orient; write so an agent can decide whether to load the file.

> "Line 2 of every file is a > one-line summary. This is the domain's identity string."
> [planned]

domain-split: Split a domain into a folder when any of: more than 15 requirements in one file; a sub-domain has 5+ requirements; one section longer than rest combined; ## Refs lists 3+ distinct source subdirectories. After split: README.md as domain index, sub-domain .md files; slugs travel with content, zero reference updates.

> "Split thresholds — any one triggers a split. Slugs travel with content. IDs are never renumbered — slugs are the identity."
> [planned]

context-file: CONTEXT.md contains project name, one-line summary, purpose, user goals, hard constraints, non-goals, domain map; no requirements; establishes context before loading any domain file.

> "CONTEXT.md contains no requirements. It establishes the context every agent session needs before loading any domain file."
> [planned]

out-of-scope-section: Each domain file has ## Out of scope as a short bullet list to kill incorrect assumptions before they form; constraint on imagination, not documentation.

> "## Out of scope — short bullet list. Its purpose is to kill incorrect assumptions before they form."
> [planned]

refs-section: Each domain file has ## Refs listing primary code paths the domain owns; agents use it for impact analysis without scanning every inline ~.

> "## Refs — the primary code paths this domain owns. An agent doing impact analysis reads this section."
> [planned]

## Open Questions

None.

## Out of scope

Inline code refs in entry statements. Numeric IDs for entries. Domain prefix in slugs.

## Refs

~ sdd/spec-spec.md
