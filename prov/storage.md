# Storage
> Data model, file parsing as the query layer, optional generated cache, and file-as-canonical invariant; mutation only through the file writer.

## Constraints

C:files-canonical: Markdown files in the spec directory are the spec — the actual spec, not a representation. Every derived index is a read-acceleration layer rebuilt from those files.
  > user: "The markdown files in specs/ are the spec. Not a representation of the spec, not a serialization format."

C:backend-readonly: Query reads are read-only. No query path writes to any file; caches can be deleted and rebuilt from files at any time.
  > user: "SpecQueryBackend — reads from files or an index, answers read-only queries, never modifies files."

## Requirements

data-model: The in-memory model includes Node (slug, type, domain, file, statement, planned, provenance, assumptions, code_refs, depends_on, blocked_by), Edge (from_slug, to_slug, type), BlastRadius, ValidationReport, Context.
  > user: "The data model — Node, Edge, BlastRadius, ValidationReport as specified in the architecture."
  ~ src/prov/model.py

file-backend: Every command parses the spec markdown files on each invocation; zero infrastructure, zero setup; deterministic; correct for scale up to ~200 requirements. Column-0 lines are node declarations; 2-space-indent lines are sub-lines with sigils.
  > user: "FileQueryBackend (default, always available). Parses markdown files on every call. Zero infrastructure, zero setup."
  @ C:files-canonical
  @ C:column-zero
  @ C:two-space-indent
  ~ src/prov/spec_io.py

backend-interface: A SpecQueryBackend protocol defines read-only methods (get_node, get_all_nodes, edges, blast_radius, find, validate, rebuild, is_stale, and the rest) so any conforming backend can power the CLI. [planned]
  > user: "Query backends are read-only. Any backend that implements this interface can power the CLI."

json-cache-backend: prov rebuild serializes the parsed graph to `.spec/graph.json` and the code index to `.spec/code-index.json` when explicitly requested; the cache is for external consumers and inspection — CLI commands read the markdown directly and never require it.
  > user: "JsonCacheBackend serializes the parsed graph to .spec/graph.json and the code-path reverse index to .spec/code-index.json when generated."
  @ file-backend
  ~ src/prov/commands/rebuild.py

cache-generated-optional: The `.spec/` cache is generated and optional. It is not the source of truth, is not required by `prov validate`, and is not rebuilt or staged by the pre-commit hook by default. It may be deleted and regenerated with `prov rebuild`.
  > user: "The .spec cache is generated from markdown files. Validate must not depend on it, and pre-commit must not rebuild or stage it by default."
  @ json-cache-backend
  ~ src/prov/commands/rebuild.py
  ~ scripts/install-spec-pre-commit.sh

graphdb-backend: GraphDbBackend implements the same read-only interface; syncs from files on rebuild(); optional external plugin for 1000+ requirements; swap via SPEC_BACKEND=graphdb; CLI and format unchanged. [planned]
  > user: "GraphDbBackend (phase 3, external plugin). Implements the same read-only interface. Optional; team at 50 requirements never needs it."
  @ backend-interface

backend-selection: Backend is chosen via SPEC_BACKEND env (file | json | graphdb); get_backend() returns the appropriate implementation. [planned]
  > user: "Backend selection — get_backend() uses SPEC_BACKEND, SPEC_DIR; file, json, graphdb."
  @ backend-interface

file-writer-separate: Mutation is only through the file writer: prov write writes to markdown files, enforces column-0 and 2-space indent, and validates before writing (slug availability, dangling deps); query reads never mutate.
  > user: "When spec write creates or modifies an entry, it writes to the markdown file. It never writes to a query backend. SpecFileWriter is a separate concern from SpecQueryBackend."
  @ C:backend-readonly
  ~ src/prov/writer.py

rebuild-from-files: Any generated cache can be deleted and rebuilt from spec markdown files; `prov rebuild` regenerates `.spec/` in seconds; no data is at risk.
  > user: "Any generated backend cache can be deleted and rebuilt. If .spec is stale, corrupt, or absent, prov rebuild regenerates it from markdown files."
  @ C:files-canonical
  ~ src/prov/commands/rebuild.py

## Out of scope

Writing directly to .spec/ or any backend. Backends as source of truth. Required external database for small specs. Requiring `.spec/` to be committed as a review artifact.

## Refs

~ src/prov/model.py
~ src/prov/spec_io.py
~ src/prov/indexing.py
~ src/prov/commands/rebuild.py
