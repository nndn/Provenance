# Core
> Philosophy and identity of the spec: living index, rebuilding test, property graph, query split.

## Constraints

C:no-history: The spec never records how things changed, what was considered, or what was rejected. Git records history; the spec records intent.
  > user: "The spec is always current. A well-maintained spec is indistinguishable from one written in a single session."

C:no-evolutionary-language: The spec never contains "Previously this was...", "Changed from X to Y", "Deprecated", or decision rationale prose. Declarative mutation only — rewrite in place, delete when removed.
  > user: "No tombstones, no deprecated markers. The feature is gone; the spec reflects that."

## Requirements

living-index: The spec is a living requirements index maintained alongside the codebase; it answers what the system does and why at any point in time.
  > user: "The spec is a living requirements index maintained alongside the codebase."
  ~ docs/architecture.md

rebuilding-test: A fresh agent given only the spec and no prior context must be able to build a system that satisfies all user expectations; user-observable behavior would match.
  > user: "Could a fresh agent, given only the spec and no prior context, build a system that satisfies all user expectations?"
  ~ docs/architecture.md

inclusion-test: Four questions govern what belongs in the spec: (1) user explicitly stated → in spec; (2) competent developer default → skip; (3) choice between reasonable options → in spec; (4) derivable from existing entries → do not duplicate.
  > user: "The inclusion test — ask these four questions in order"
  ~ docs/architecture.md

property-graph: The spec is a property graph (literally): node types Requirements, Constraints, Questions, Domains; edge types depends-on, implements, blocked-by, belongs-to; computable from plain text.
  > user: "The spec is a property graph. Not metaphorically — literally."
  ~ src/prov/model.py
  ~ src/prov/indexing.py

single-hop-grep: Single-hop queries (find entry by slug, all entries of a type, direct dependents, code implementing an entry) are covered by grep; no tooling required.
  > user: "Single-hop (grep covers these): Find entry by slug, find all entries of a type, find direct dependents, find what code implements an entry."
  ~ docs/spec-format.md

multi-hop-cli: Multi-hop queries (blast radius, transitive dependency chains, domain coupling, blocked work, orphan detection) are covered by the CLI using an in-memory graph parsed from files.
  > user: "Multi-hop (CLI covers these): Full blast radius of a change, transitive dependency chains, domain coupling analysis, blocked work analysis, orphan detection."
  @ property-graph
  ~ src/prov/commands/impact.py
  ~ src/prov/commands/orient.py

## Out of scope

Changelog, design journal, implementation documentation. External wiki or requirements DB as source of truth.

## Refs

~ docs/architecture.md
~ docs/spec-format.md
