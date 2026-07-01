# Storage

> Data model, read-only query backends, and file-as-canonical invariant; mutation only through the file writer.

## Constraints

C:backend-readonly: Query backends are read-only. They have no mutation methods; they never write to any file. Rebuild from files at any time.

> "SpecQueryBackend — reads from files or an index, answers read-only queries, never modifies files."

## Requirements

data-model: The in-memory model includes Node (slug, type, domain, file, statement, planned, provenance, assumptions, code_refs, depends_on, blocked_by), Edge (from_slug, to_slug, type), BlastRadius, ValidationReport.

> "The data model — Node, Edge, BlastRadius, ValidationReport as specified in the architecture."
> [planned]

backend-interface: A SpecQueryBackend protocol defines read-only methods: get_node, get_all_nodes, get_nodes_by_type, get_nodes_by_domain, get_domains; get_edges_from, get_edges_to; get_slugs_for_path, get_paths_for_slug; dependents, dependencies, blast_radius; get_planned, get_open_questions, get_unconfirmed_assumptions, get_orphans, get_domain_coupling; find, check_slug_available; validate; rebuild, is_stale.

> "Query backends are read-only. Any backend that implements this interface can power the CLI."
> [planned]

file-backend: FileQueryBackend parses markdown files on every call; zero infrastructure, zero setup; deterministic; correct for scale up to ~200 requirements (under 100ms per call). Column-0 lines are node declarations; 2-space-indent lines are sub-lines with sigils.

> "FileQueryBackend (default, always available). Parses markdown files on every call. Zero infrastructure, zero setup."
> @ C:column-zero
> @ C:two-space-indent
> [planned]

json-cache-backend: JsonCacheBackend wraps FileQueryBackend; serializes graph to `.spec/graph.json` and code index to `.spec/code-index.json` when explicitly generated. The cache is an optimization for commands such as scope, impact, and orient; markdown remains canonical.

> "JsonCacheBackend serializes the parsed graph to .spec/graph.json and the code-path reverse index to .spec/code-index.json when generated."
> @ file-backend
> [planned]

cache-generated-optional: The `.spec/` cache is generated and optional. It is not the source of truth, is not required by `prov validate`, and is not rebuilt or staged by the pre-commit hook by default. It may be deleted and regenerated with `prov rebuild`.

> "The .spec cache is generated from markdown files. Validate must not depend on it, and pre-commit must not rebuild or stage it by default."
> @ json-cache-backend
> [planned]

graphdb-backend: GraphDbBackend implements the same read-only interface; syncs from files on rebuild(); optional external plugin for 1000+ requirements; swap via SPEC_BACKEND=graphdb; CLI and format unchanged.

> "GraphDbBackend (phase 3, external plugin). Implements the same read-only interface. Optional; team at 50 requirements never needs it."
> @ backend-interface
> [planned]

backend-selection: Backend is chosen via SPEC_BACKEND env (file | json | graphdb), SPEC_DIR for path; get_backend() returns the appropriate implementation.

> "Backend selection — get_backend() uses SPEC_BACKEND, SPEC_DIR; file, json, graphdb."
> [planned]

file-writer-separate: Mutation is only through the file writer. Spec write writes to markdown files; query backends are invalidated after write (cache stale, graph DB incremental update if running). File writer enforces column-0, 2-space indent, pre-write validation (slug availability, dangling deps).

> "When spec write creates or modifies an entry, it writes to the markdown file. It never writes to a query backend. SpecFileWriter is a separate concern from SpecQueryBackend."
> @ C:backend-readonly
> [planned]

rebuild-from-files: Any backend cache can be deleted and rebuilt from spec markdown files; `prov rebuild` regenerates `.spec/` in seconds; no data is at risk.

> "Any generated backend cache can be deleted and rebuilt. If .spec is stale, corrupt, or absent, prov rebuild regenerates it from markdown files."
> [planned]

## Out of scope

Writing directly to .spec/ or any backend. Backends as source of truth. Required external database for small specs. Requiring `.spec/` to be committed as a review artifact.

## Refs

~ sdd/spec-spec.md
