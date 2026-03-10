# Spec-Driven Development — Architecture

> The complete technical specification for the spec system.
> This document is the source of truth for anyone building,
> extending, or integrating with the spec system.

---

## Table of contents

1. What this is and why
2. Core philosophy
3. The spec as a knowledge graph
4. Repository layout
5. File format — the DSL
6. Node types
7. Edge types
8. Slug conventions
9. File structure and scaling
10. Storage layer — pluggable interface
11. The CLI — spec.py
12. CLI command reference
13. Code-spec bidirectionality
14. Agent integration
15. The development workflow
16. Human review model
17. Reconciliation
18. Validation rules
19. Grep grammar reference
20. Bootstrap guide

---

## 1. What this is and why

The spec is a **living requirements index** maintained alongside the codebase. It
answers one question at any point in time: what does this system do, and why?

It is not a changelog. It is not a design journal. It is not documentation of the
implementation. It is a precise, current snapshot of user intent — everything a
fresh agent or developer needs to understand the system's required behavior without
reading any code.

**Why it lives in the repository:**
Every clone carries the full spec. Every branch carries its spec state. Git diffs
show spec and code changing together. There is no external system to sync with, no
wiki to go out of date, no separate onboarding step. The spec ships with the code.

**Why it is maintained by agents:**
Agents are the primary writers and consumers. The format is designed to be written
by an agent without ambiguity and read by an agent without inference. Humans can
read it directly — it is plain text optimized for prose — but the structural
invariants exist to serve agent parsing and grep-based retrieval.

**Why query backends are pluggable:**
The markdown files are the spec. Always. No exception. Any query backend — an
in-memory parser, a JSON cache, a graph database — is a read-acceleration layer
built from those files. It is never the source of truth. It can always be deleted
and rebuilt from scratch in seconds. Agents and developers can grep the files
directly without any tooling. The CLI adds speed and structure on top of what is
already there; it does not replace it.

---

## 2. Core philosophy

**The rebuilding test.** Could a fresh agent, given only the spec and no prior
context, build a system that satisfies all user expectations? It might make
different implementation choices, but every user-observable behavior would match.
If yes, the spec is doing its job.

**The spec is always current.** It never records how things changed, what was
considered, or what was rejected. Git records history. The spec records intent.
A well-maintained spec is indistinguishable from one written in a single session.

**The inclusion test — ask these four questions in order:**

1. Did the user explicitly state this?
   Yes → always in spec.

2. Would a competent developer do this by default without being told?
   Yes → skip it. Standard validation, obvious defaults, conventional patterns
   do not belong in the spec.

3. Does this reflect a choice between two reasonable options?
   Yes → in spec, regardless of how obvious the code looks. Single vs multiple
   assignees. Optional vs required field. Fixed vs configurable statuses. The
   code implements the choice; the spec records that a choice was made.

4. Is this derivable from spec entries already present?
   Yes → do not duplicate it. Write the pattern once as a constraint; apply it
   in code everywhere.

**What belongs in the spec vs code:**

| Spec                                        | Code                             |
| ------------------------------------------- | -------------------------------- |
| What the system does for the user           | How it does it                   |
| Non-obvious constraints and product choices | Obvious defaults and conventions |
| Technologies the user specified             | Technologies the developer chose |
| What is explicitly out of scope             | Inferred edge cases              |
| Why a requirement exists (user's words)     | Why an implementation works      |

**Declarative mutation.** The spec is not append-only. When a requirement changes,
rewrite it in place. When a requirement is removed, delete it — no tombstones, no
deprecated markers. The feature is gone; the spec reflects that.

The spec never contains:

- "Previously this was..."
- "Changed from X to Y"
- "Deprecated, use slug instead"
- Decision rationale prose ("we chose JWT because...")
- Anything describing the spec's own evolution

---

## 3. The spec as a knowledge graph

The spec is a property graph. Not metaphorically — literally.

**Node types:** Requirements, Constraints, Questions, Domains
**Edge types:** depends-on, implements, blocked-by, belongs-to

Every design decision in this system — slugs, column-0 invariant, sub-line sigils
— is a hand-rolled graph serialization format designed so the graph is computable
from plain text without any external tooling.

This matters because the spec supports two query classes:

**Single-hop (grep covers these):**
Find entry by slug, find all entries of a type, find direct dependents,
find what code implements an entry.

**Multi-hop (CLI covers these):**
Full blast radius of a change, transitive dependency chains, domain coupling
analysis, blocked work analysis, orphan detection.

The CLI bridges the two classes. It uses grep for single-hop and an in-memory
graph (parsed from files) for multi-hop. A graph database can replace the in-memory
graph later by implementing the same interface.

---

## 4. Repository layout

**Spec-kit source repo** (this repository):

```
<repo-root>/
  src/
    spec.py             ← CLI source (installed into user projects as spec/spec.py)
  specs/                ← this repo's own spec (meta: spec-kit documenting itself)
    CONTEXT.md
    <domain>.md
    .spec/
  ARCHITECTURE.md       ← this document
```

**User project after install** (target of install.sh):

```
<repo-root>/
  spec/                 ← or specs/; installer creates spec/ by default
    spec.py             ← copied from src/spec.py
    CONTEXT.md
    <domain>.md
    .spec/
```

**spec.py is self-contained.** It requires only Python 3.9+ standard library.
No external dependencies. Any agent or developer can run it without setup.
It is the only file that needs to be copied when bootstrapping a new project.

**`.spec/` is committed.** The cache is part of the repository so that `spec scope`
and `spec impact` resolve instantly from the index without a build step.
Its diff in pull requests is machine-readable evidence of what the spec changed.

---

## 5. File format — the DSL

The spec uses a lightweight domain-specific language embedded in markdown. The
format has two invariants that must never be violated:

1. Every primary entry starts at column 0
2. Every sub-line is indented exactly 2 spaces

Violating either breaks grep-based retrieval and the file parser.

### Complete annotated example

```markdown
# Auth

> OAuth-based auth and stateless JWT sessions. Two roles: admin/member.

## Constraints

C:oauth-only: OAuth only — no email/password.

> "I don't want to deal with password resets"

C:jwt-stateless: Sessions are stateless JWT — no server-side session store.

> "I don't want to manage session infrastructure"

## Requirements

google-login: Users authenticate via Google OAuth.

> "we'll just do Google login for now"
> ~ src/api/auth/google.py
> ~ src/api/auth/callback.py

session-expiry: Sessions expire after 30 days of inactivity.

> "standard session timeout, nothing crazy"
> ! assumed 30 days — "nothing crazy" is unconfirmed
> @ C:jwt-stateless
> ~ src/middleware/session.py:44
> ~ src/middleware/session.py:101

admin-revoke: Admins can revoke any user session immediately. [planned]

> "need a kill switch for bad actors"
> ! assumed token blocklist approach — not stated
> @ session-expiry
> ? Q:admin-revoke-scope

guest-access: Read-only access without sign-in. [planned]

> "I want people to browse without signing up"
> ? Q:guest-access-expiry

## Open Questions

Q:guest-access-expiry: Does a guest session expire or persist indefinitely?

> blocks guest-access implementation

Q:admin-revoke-scope: Does admin-revoke apply to a single session or all sessions
for the user?

> blocks admin-revoke implementation

## Out of scope

MFA, SSO/SAML, remember-me across devices.

## Refs

~ src/api/auth/
~ src/middleware/session.py
~ src/models/user.py
```

### Rules

**Line 2 of every file** is a `>` one-line summary. This is the domain's identity
string. It appears in `spec orient` output. Write it so an agent reading only this
line can decide whether to load the file.

**`## Constraints`** — non-negotiable rules that govern all requirements in the
domain. Use `C:slug:` prefix. Referenced from requirements via `@ C:slug`.

**`## Requirements`** — observable behaviors the user expects. Use bare `slug:`.

**`## Open Questions`** — unresolved decisions that block implementation.
Use `Q:slug:` prefix. Always include a `>` line stating what they block.

**`## Out of scope`** — short bullet list. Its purpose is to kill incorrect
assumptions before they form. Not documentation — a constraint on imagination.

**`## Refs`** — the primary code paths this domain owns. An agent doing impact
analysis reads this section to understand the domain's code territory without
scanning every inline `~` across the file.

**`[planned]`** marks unimplemented requirements. When a requirement is implemented:
add `~ ref` sub-lines, remove `[planned]`, confirm or remove `!` lines. One edit.

---

## 6. Node types

Three node types. Self-describing at column 0. Type is encoded in the slug prefix,
not inferred from section headers.

### Requirement

```
slug: <statement> [planned]
  > <provenance>
  ! <assumption>     (when agent filled a gap)
  ~ <code-ref>       (one per line, when implemented)
  @ <slug>           (depends-on edge)
  ? <Q:slug>         (blocked-by edge)
```

- Slug has no prefix
- Most common node type — minimal syntax
- `[planned]` present until implemented, then removed
- Multiple `~` lines for multiple code refs
- Multiple `@` lines for multiple dependencies
- Multiple `!` lines for multiple assumptions

### Constraint

```
C:slug: <statement>
  > <provenance>
  ! <assumption>     (rare — constraints are usually fully specified by user)
  ~ <code-ref>       (when enforced in code)
```

- `C:` prefix at column 0
- Non-negotiable rule: compliance, hard limit, platform requirement, user-specified
  technology choice
- No `[planned]` — constraints are either active or they don't exist
- Referenced from requirements via `@ C:slug`

### Open Question

```
Q:slug: <question statement>
  > <what this blocks>
```

- `Q:` prefix at column 0
- Always includes a `>` line stating which requirement it blocks
- Deleted when resolved — the answer becomes part of the requirement it blocked
- Referenced from requirements via `? Q:slug`

---

## 7. Edge types

Five edge types. Every edge is on its own dedicated sub-line (2-space indent).
Never inline in the entry statement.

| Sigil | Edge type  | From → To        | Meaning                                                    |
| ----- | ---------- | ---------------- | ---------------------------------------------------------- |
| `>`   | provenance | node → user      | Why this entry exists                                      |
| `!`   | assumption | node → agent     | What the agent filled in                                   |
| `~`   | implements | node → code path | Code that implements this entry                            |
| `@`   | depends-on | node → node      | This entry's behavior depends on that slug                 |
| `?`   | blocked-by | node → Q:slug    | This requirement cannot be implemented until Q is resolved |

**`>` is required on every node.** No exceptions. An entry with no `>` line is a
ghost-scope error — the agent added something the user never asked for.

**`!` is required whenever the agent fills a gap.** A specific number, a threshold,
a binary choice, a behavior the user left unspecified — any detail the agent decided
on the user's behalf gets a `!` line. "It seemed obvious" is not an excuse.

**`~` moves to sub-lines.** Never inline in the entry statement. This is a breaking
change from early versions. Multiple code refs are now unambiguous:

```
✓  session-expiry: Sessions expire after 30 days of inactivity.
     ~ src/middleware/session.py:44
     ~ src/middleware/session.py:101

✗  session-expiry: Sessions expire after 30 days. ~src/middleware/session.py:44
```

**`@` is slug-only.** No file paths. The slug resolves anywhere in the tree via
grep. This is what makes file splits zero-cost — `@ session-expiry` resolves
regardless of which file the entry moved to.

---

## 8. Slug conventions

Every requirement and constraint has a slug — a permanent, globally unique handle
used for all cross-referencing.

**Format:** `kebab-case`, 2–4 words, describing the behavior not the domain.

```
session-expiry       ✓  describes the behavior
guest-access         ✓  clear and specific
file-size-limit      ✓  precise
auth-session-expiry  ✗  domain prefix — couples slug to file location
limit                ✗  too vague — signals an under-specified requirement
```

**The behavior test:** A developer reading only `spec: session-expiry` in a code
comment should understand what constraint governs that code without loading the spec.

**Slugs are permanent.** Once written and referenced in code, a slug does not
change even if the requirement content is rewritten entirely. The slug is a stable
handle, not a description. Rename cost is high — choose carefully upfront.

**Slugs are globally unique** across the entire `specs/` tree. Before writing any
new requirement:

```bash
# Check for collision
python specs/spec.py check-slug <proposed-slug>
# or manually:
grep -rh "^[a-z][a-z0-9-]*:\|^C:[a-z]\|^Q:[a-z]" specs/ | cut -d: -f1 | sort | uniq -d
```

**When similar slugs arise across domains** (`session-expiry` vs `token-expiry`),
make them more specific: `user-session-expiry` vs `api-token-expiry`. If the
behaviors are genuinely identical, merge into one entry with a cross-domain `@`
reference.

**Q: slugs** describe the question: `Q:guest-access-expiry`, `Q:proration-downgrade`.
They follow the same uniqueness and permanence rules.

---

## 9. File structure and scaling

### Phase 1: single file per domain (default)

```
specs/
  CONTEXT.md
  auth.md
  billing.md
  data-model.md
```

Start here. Do not create folders preemptively.

### Split thresholds — any one triggers a split

1. More than 15 requirements in a single file
2. A natural sub-domain has 5+ requirements of its own
3. One section is longer than the rest of the file combined
4. `## Refs` lists 3+ distinct source subdirectories

### After split

```
specs/
  auth/
    README.md     ← domain index: summary line, sub-spec map, constraints, open Qs
    oauth.md      ← sub-domain entries
    sessions.md
    rbac.md
```

**Slugs travel with content.** Moving `session-expiry` from `auth.md` to
`auth/sessions.md` requires zero reference updates anywhere. Every `spec: session-expiry`
in code and every `@ session-expiry` in other spec files resolves by the same grep:

```bash
grep -r "^session-expiry:" specs/
```

**IDs are never renumbered.** There are no IDs — slugs are the identity. This is
why splits are zero-cost.

### CONTEXT.md format

```markdown
# <Project Name>

> <One sentence. What it does and who uses it.>

## Purpose

<2-3 sentences. The problem being solved.>

## User goals

1. <Primary user goal>
2. <Secondary goal>

## Hard constraints

C:constraint-slug: <Non-negotiable rule>

> <why>

## Non-goals

- <Explicit out-of-scope items>

## Domain map

auth specs/auth.md
billing specs/billing.md
data-model specs/data-model.md
```

CONTEXT.md contains no requirements. It establishes the context every agent session
needs before loading any domain file. The domain map lists the primary file for each
domain — the first file an agent loads when working in that domain.

---

## 10. Source of truth and query backends

### The invariant: files are always canonical

The markdown files in `specs/` are the spec. Not a representation of the spec,
not a serialization format, not a sync target — the actual spec. This is
unconditional and permanent.

Every query backend — the file parser, the JSON cache, a graph database — is a
read-acceleration layer built from those files. It can always be deleted and
rebuilt from the files. It is never written to directly. The relationship is
strictly one-directional:

```
specs/*.md  ──(parsed by)──►  query backend  ──(answers)──►  CLI commands
     ▲                                                              │
     └────────────────── all writes go here ◄──────────────────────┘
```

**Consequences of this invariant:**

Every clone gets the complete spec with zero setup. `git clone` is the only
onboarding step. No external service to configure, no index to rebuild, no
database to populate.

Every git operation works naturally. `git diff`, `git log`, `git blame`, `git
bisect` — they all work on the spec exactly as they work on code. The spec's
history is the repository's history.

Grep always works. Any agent, CI pipeline, editor plugin, or developer can query
the spec using nothing but standard Unix tools. The CLI adds speed and structure
on top of what is always directly accessible.

Any backend can be deleted and rebuilt. If the cache is stale, corrupt, or absent,
`python specs/spec.py rebuild` regenerates it from the files in seconds. No data
is at risk. No state is lost.

### Mutation: always through the file writer

When `spec write` creates or modifies an entry, it writes to the markdown file.
It never writes to a query backend. After the file is written, the relevant
query backends are invalidated (cache is marked stale, graph DB is updated
incrementally if running).

The file writer module is a separate concern from the query backends:

```
SpecFileWriter       writes entries to markdown files, handles formatting,
                     enforces structural invariants (column 0, 2-space indent),
                     runs pre-write validation (slug availability, dangling deps)

SpecQueryBackend     reads from files or an index, answers read-only queries,
                     never modifies files
```

### The data model

```python
from typing import Protocol, Literal
from dataclasses import dataclass, field

NodeType = Literal["requirement", "constraint", "question"]
EdgeType = Literal["depends-on", "implements", "blocked-by"]

@dataclass
class Node:
    slug:        str
    type:        NodeType
    domain:      str
    file:        str          # repo-relative path to the owning spec file
    statement:   str
    planned:     bool         = False
    provenance:  str          = ""
    assumptions: list[str]    = field(default_factory=list)
    code_refs:   list[str]    = field(default_factory=list)
    depends_on:  list[str]    = field(default_factory=list)  # slugs
    blocked_by:  list[str]    = field(default_factory=list)  # Q:slugs

@dataclass
class Edge:
    from_slug: str
    to_slug:   str
    type:      EdgeType

@dataclass
class BlastRadius:
    root:                str
    direct_dependents:   list[Node]
    transitive_slugs:    list[str]
    all_code_paths:      list[str]
    assumptions_in_path: list[tuple[str, str]]   # (slug, assumption text)
    planned_in_path:     list[Node]

@dataclass
class ValidationReport:
    errors:   list[str]
    warnings: list[str]
    clean:    list[str]
```

### Query backend interface

Query backends are **read-only**. They have no mutation methods. Any backend that
implements this interface can power the CLI.

```python
class SpecQueryBackend(Protocol):
    """
    Read-only interface for querying spec data.
    Implementations parse, cache, or index the markdown files.
    Never writes to any file. Never is the source of truth.
    Rebuild from files at any time with: backend.rebuild()
    """

    # ── Node access ──────────────────────────────────────────────────────────
    def get_node(self, slug: str) -> Node | None: ...
    def get_all_nodes(self) -> list[Node]: ...
    def get_nodes_by_type(self, node_type: NodeType) -> list[Node]: ...
    def get_nodes_by_domain(self, domain: str) -> list[Node]: ...
    def get_domains(self) -> list[str]: ...

    # ── Edge access ──────────────────────────────────────────────────────────
    def get_edges_from(self, slug: str,
                       edge_type: EdgeType | None = None) -> list[Edge]: ...
    def get_edges_to(self, slug: str,
                     edge_type: EdgeType | None = None) -> list[Edge]: ...

    # ── Code-spec index ───────────────────────────────────────────────────────
    def get_slugs_for_path(self, path: str) -> list[str]: ...
    def get_paths_for_slug(self, slug: str) -> list[str]: ...

    # ── Graph traversal ───────────────────────────────────────────────────────
    def dependents(self, slug: str) -> list[Node]: ...
    def dependencies(self, slug: str) -> list[Node]: ...
    def blast_radius(self, slug: str) -> BlastRadius: ...

    # ── Surface queries ───────────────────────────────────────────────────────
    def get_planned(self) -> list[Node]: ...
    def get_open_questions(self) -> list[Node]: ...
    def get_unconfirmed_assumptions(self) -> list[tuple[Node, str]]: ...
    def get_orphans(self) -> list[Node]: ...
    def get_domain_coupling(self) -> dict[str, set[str]]: ...

    # ── Search ────────────────────────────────────────────────────────────────
    def find(self, query: str) -> list[Node]: ...
    def check_slug_available(self, slug: str) -> bool: ...

    # ── Integrity ─────────────────────────────────────────────────────────────
    def validate(self) -> ValidationReport: ...

    # ── Lifecycle ─────────────────────────────────────────────────────────────
    def rebuild(self) -> None: ...          # rebuild from files; always safe to call
    def is_stale(self) -> bool: ...         # true if any spec file is newer than index
```

### Backend implementations

**FileQueryBackend** (default, always available)

Parses markdown files on every call. Zero infrastructure, zero setup.
Deterministic because of the structural invariants. Correct for any scale up
to ~200 requirements (under 100ms per call). This is all that is needed to start.

The parser is simple because the format is strictly regular:

- Column-0 non-whitespace lines are node declarations
- `C:` prefix → constraint, `Q:` prefix → question, bare slug → requirement
- 2-space-indent lines are sub-lines of the preceding node
- Sub-line first character is always the sigil: `>`, `!`, `~`, `@`, `?`

**JsonCacheBackend** (phase 2, committed to repo)

Wraps FileQueryBackend. Serializes the parsed graph to `.spec/graph.json` and
the code-path reverse index to `.spec/code-index.json`. Checks file mtimes on
every call. If any spec file is newer than the cache, transparently rebuilds.

The cache files are committed to the repository:

- Their `git diff` in a PR is the machine-readable record of what the spec changed
- CI can fail fast on stale cache rather than rebuilding at query time
- A fresh clone already has an up-to-date index; no build step needed

`spec scope` resolves via code-index lookup (O(1)).
`spec impact` traverses the in-memory JSON graph.
`spec orient` aggregates from pre-computed domain summaries.

**GraphDbBackend** (phase 3, external plugin)

Implements the same read-only interface. Syncs from files on `rebuild()`.
Between rebuilds, receives incremental updates when the file writer notifies
it of changes. Enables Cypher queries, full-text search, and GraphRAG retrieval.

This backend is an **optional external plugin**. It is never required. A team
running at 1000+ requirements can opt in; a team at 50 requirements never needs
it. The CLI, the format, and the agent commands are identical either way.

Swap in by setting `SPEC_BACKEND=graphdb` and configuring the plugin. Everything
else — the files, the format, the CLI commands — is unchanged.

### Backend selection

```python
def get_backend() -> SpecQueryBackend:
    backend = os.getenv("SPEC_BACKEND", "file")
    specs_dir = os.getenv("SPEC_DIR", "specs")
    if backend == "file":
        return FileQueryBackend(specs_dir)
    if backend == "json":
        return JsonCacheBackend(specs_dir,
                                cache_dir=os.path.join(specs_dir, ".spec"))
    if backend == "graphdb":
        plugin = os.getenv("SPEC_GRAPHDB_PLUGIN")
        return load_plugin(plugin, specs_dir)   # third-party plugin
    raise ValueError(f"Unknown SPEC_BACKEND: {backend}")
```

### What the JSON cache looks like

The cache is two files, both human-readable and git-diffable.

**`.spec/graph.json`** — the full node and edge graph:

```json
{
  "generated": "2026-03-10T07:18:35Z",
  "spec_files": ["specs/auth.md", "specs/billing.md"],
  "nodes": {
    "session-expiry": {
      "type": "requirement",
      "domain": "auth",
      "file": "specs/auth.md",
      "statement": "Sessions expire after 30 days of inactivity.",
      "planned": false,
      "provenance": "standard session timeout, nothing crazy",
      "assumptions": ["assumed 30 days — nothing crazy unconfirmed"],
      "code_refs": [
        "src/middleware/session.py:44",
        "src/middleware/session.py:101"
      ],
      "depends_on": ["C:jwt-stateless"],
      "blocked_by": []
    }
  },
  "edges": [
    { "from": "session-expiry", "to": "C:jwt-stateless", "type": "depends-on" },
    {
      "from": "session-expiry",
      "to": "src/middleware/session.py:44",
      "type": "implements"
    }
  ]
}
```

**`.spec/code-index.json`** — reverse lookup from code paths to slugs:

```json
{
  "generated": "2026-03-10T07:18:35Z",
  "by_file": {
    "src/middleware/session.py": ["session-expiry", "admin-revoke"],
    "src/api/auth/google.py": ["google-login"]
  },
  "by_dir": {
    "src/middleware/": ["session-expiry", "admin-revoke", "C:jwt-stateless"],
    "src/api/auth/": ["google-login", "C:oauth-only"]
  }
}
```

The `by_dir` index is what makes `spec scope src/api/auth/signup.py` work even
when `signup.py` has no direct `~` ref — it falls back to directory ownership
declared in `## Refs`.

### Grep vs CLI — when to use which

The CLI is not a replacement for grep. Both are always valid. The CLI adds
multi-hop traversal and formatted context packages that grep cannot produce.

| Query                                       | Tool              | Why                      |
| ------------------------------------------- | ----------------- | ------------------------ |
| Does `session-expiry` exist?                | grep              | Instant, no parse needed |
| What are all open questions?                | grep              | Single-pass, O(lines)    |
| What governs `src/middleware/session.py`?   | CLI `spec scope`  | Needs code-index         |
| What breaks if I change `session-expiry`?   | CLI `spec impact` | Needs graph traversal    |
| What did this codebase look like last week? | git + grep        | Standard git workflow    |
| What assumptions are unconfirmed?           | grep or CLI       | Either works             |

Agents should use the CLI for commands that need structured output or graph traversal,
and can use grep directly for simple existence checks or surface-level orientation
when startup cost matters.

---

## 11. The CLI — spec.py

`spec.py` is the primary interface for structured queries and formatted context
packages. Agents can also read spec files directly with grep or a file reader —
the CLI is not a gate, it is a convenience layer.

**Use the CLI when:**

- You need structured context packages (formatted, labeled, ready for an LLM's
  context window)
- You need multi-hop graph traversal (`spec impact`, `spec scope` with directory
  ownership fallback)
- You need pre-built validation (`spec validate`)
- You need a change manifest (`spec diff`)

**Use grep/file reads directly when:**

- Checking existence of a slug
- Quick orientation (domain list, open questions, assumptions)
- Building your own tooling on top of the format
- Verifying the spec independently of any tooling

The CLI produces identical output regardless of which query backend is active.
An agent using the CLI does not need to know or care whether it is talking to
the file parser, the JSON cache, or a graph database.

Every command outputs structured plain text designed for direct inclusion in an
agent's context window. Not JSON. Not raw file content. Formatted, labeled,
actionable text that reads like a briefing.

### Running

```bash
# Direct
python specs/spec.py <command> [args]

# Shorthand (after adding to PATH or aliasing)
spec <command> [args]
```

### Mode selection

Commands group naturally into two agent modes:

**Consume mode** — coding, debugging, reviewing:

```
spec scope <path>      entry point from a code path
spec context <slug>    full context for a specific entry
spec impact <slug>     blast radius before making changes
spec find <keywords>   discover entries without knowing the slug
```

**Maintain mode** — writing and updating specs:

```
spec orient            full surface summary, session start
spec domain <name>     full domain load for editing
spec validate          integrity check before committing
spec diff [ref]        human-review change manifest
spec write             guided authoring of new entries
spec reconcile <path>  detect code→spec drift
spec check-slug <slug> verify a slug is available
```

---

## 12. CLI command reference

Each command is specified with its signature, when to use it, and its exact output
format. The output format is a contract — backends must produce identical output.

---

### `spec orient`

**When:** Start of every maintain-mode session. Fresh agent with no prior context.

**Output:** Full product surface in a single structured package. Sized for
maintain mode — includes domain summaries, all open questions, all planned work,
and all unconfirmed assumptions.

```
=== SPEC ORIENT ===

Project: <from CONTEXT.md title>
<from CONTEXT.md purpose>

Hard constraints: C:slug1, C:slug2, C:slug3

DOMAINS:
  <name>    <one-line summary>    <N> reqs  <P> planned  <Q> questions  <A> assumptions
  ...

OPEN QUESTIONS (<N> total):
  Q:slug    domain    question statement (truncated to 60 chars)
            → blocks: req-slug
  ...

UNCONFIRMED ASSUMPTIONS (<N> total):
  slug      domain    ! assumption text (truncated)
  ...

PLANNED (<N> total):
  slug      domain    statement (truncated)
  ...

DOMAIN COUPLING:
  auth      → billing (via billing-session-sync)
  ...        (omitted if none)

─── Next: spec domain <name> | spec context <slug> | spec validate
```

---

### `spec scope <path>`

**When:** An agent is about to read or modify code. Called before any code work.

**Input:** Any code path — file, directory, or file:line.

**Output:** Every spec entry governing that code path. Compact. Designed to fit
in a coding agent's context budget (under 400 tokens).

```
=== SCOPE: <path> ===

REQUIREMENTS (<N>):
  <slug>    <statement>
            ⚠ assumption: <assumption text>    (if ! lines exist)
            [planned]                           (if planned)
  ...

CONSTRAINTS (<N>):
  C:<slug>  <statement>
  ...

DEPENDED ON BY (other entries that depend on what you're about to change):
  <slug>    [<domain>]    <statement>
  ...

OPEN QUESTIONS blocking entries in scope:
  Q:<slug>  <question>
  ...        (omitted if none)

─── spec context <slug>    for full entry details
─── spec impact <slug>     before making changes
```

If no spec entries govern the path, returns:

```
=== SCOPE: <path> ===
No spec entries reference this path.
Run: spec reconcile <path>  to check for drift.
```

---

### `spec context <slug>`

**When:** Agent needs to deeply understand a single entry — before implementing,
modifying, or reasoning about its behavior.

**Output:** Complete node data plus one-hop neighborhood.

```
=== CONTEXT: <slug> ===

<type>  |  domain: <domain>  |  <implemented | planned>
<file path>

Statement:
  <full statement>

Why this exists:
  > <provenance>

Assumptions (unconfirmed):                    (omitted if none)
  ! <assumption text>
  ...

Code:                                          (omitted if planned)
  ~ <path>[:line]    <annotation if any>
  ...

Constraints governing this domain:
  C:<slug>    <statement>
  ...

Depends on:                                    (omitted if none)
  <slug>    [<domain>]    <statement>
  ...

Depended on by:                                (omitted if none)
  <slug>    [<domain>]    <statement>
  ...

Blocked by:                                    (omitted if none)
  Q:<slug>    <question>
  ...

─── spec impact <slug>           before making changes
─── spec context <dep-slug>      explore a dependency
─── spec domain <domain>         load full domain context
```

---

### `spec impact <slug>`

**When:** Before modifying, deleting, or significantly changing an entry or its
code. Surfaces the full blast radius so nothing is missed.

**Output:** Transitive dependency analysis built from the graph.

```
=== IMPACT: <slug> ===

Direct dependents (<N>):
  <slug>    [<domain>]    <type>    <implemented | planned>
  ...

Transitive dependents (<N> total):
  <slug> → <slug> → ...    [<domain>]
  ...

All code in blast radius:
  <path>[:line]    ← <slug>
  ...

Unconfirmed assumptions in blast radius:
  <slug>    ! <assumption text>
  ...                                          (omitted if none)

Planned entries in blast radius:               (omitted if none)
  <slug>    [<domain>]    [planned]
  ...

─── Proceed carefully. Verify all affected code after changes.
```

---

### `spec find <keywords>`

**When:** Agent doesn't know the slug. Searching by concept or description.

**Input:** Free text keywords (not a slug).

**Output:** Ranked matches against slug names and statement text.

```
=== FIND: "<keywords>" ===

<slug>    [<domain>]    <type>    <statement>
<slug>    [<domain>]    <type>    <statement>
...

<N> results.
─── spec context <slug>    for full details
```

If no results:

```
=== FIND: "<keywords>" ===
No entries match.
Try: spec orient    to browse all domains.
```

---

### `spec domain <name>`

**When:** Maintain-mode agent loading a full domain to edit, review, or understand
completely.

**Output:** Full domain content — all nodes, all edges, all metadata — structured
for comprehensive reading.

```
=== DOMAIN: <name> ===

<domain summary line>
File: <path>

CONSTRAINTS (<N>):

  C:<slug>: <statement>
    > <provenance>
    ~ <code-refs>

REQUIREMENTS (<N> implemented, <N> planned):

  <slug>: <statement>    [planned if applicable]
    > <provenance>
    ! <assumptions>      (if any)
    @ <dependencies>     (if any)
    ~ <code-refs>        (if implemented)
    ? <blocked-by>       (if any)

OPEN QUESTIONS (<N>):

  Q:<slug>: <question>
    > <blocks>

OUT OF SCOPE:
  <items>
```

---

### `spec validate`

**When:** Before every commit. Non-zero exit code if any errors are found.

**Checks:**

| Check                  | Level | Description                                                       |
| ---------------------- | ----- | ----------------------------------------------------------------- |
| dead-ref               | ERROR | A `~` path in specs does not resolve to a real file               |
| phantom-slug           | ERROR | `spec: slug` in code has no matching entry in specs               |
| duplicate-slug         | ERROR | Two entries share the same slug anywhere in the tree              |
| dependency-cycle       | ERROR | A dependency chain forms a cycle                                  |
| ghost-scope            | ERROR | An entry has no `>` line                                          |
| silent-impl            | WARN  | `[planned]` entry but code references its slug                    |
| orphan-question        | WARN  | A `Q:` entry is not referenced by any `?` line                    |
| orphan-entry           | WARN  | An entry has no `~` refs and no `@` dependents and is not planned |
| unconfirmed-assumption | INFO  | `!` lines present — surface for human review                      |

**Output:**

```
=== SPEC VALIDATE ===

ERRORS (fix before commit):
  dead-ref:        <slug>  ~ <path>  — file not found
  phantom-slug:    <path>:<line>  spec:<slug>  — no entry exists
  duplicate-slug:  <slug>  found in <file1> and <file2>

WARNINGS:
  silent-impl:     <slug>  [planned] but spec:<slug> found in <path>:<line>
  orphan-question: Q:<slug>  — not referenced by any ? line

UNCONFIRMED ASSUMPTIONS (<N>):
  <slug>    ! <assumption>
  ...

CLEAN:
  ✓ no dependency cycles
  ✓ all @ targets exist
  ✓ no ghost-scope entries
  ✓ all Q: entries have > lines

Result: FAIL (<N> errors, <N> warnings)
```

Exit code 0 only when zero errors. Warnings do not fail the build.

---

### `spec diff [ref]`

**When:** After an agent writes or modifies specs. Produces the human review
artifact. Default ref is `HEAD` (staged changes vs last commit).

**Input:** Optional git ref. Defaults to `HEAD` (shows staged + unstaged changes).

**Output:** Semantic change manifest — what changed in spec terms, not line diffs.

```
=== SPEC DIFF: <ref>..HEAD ===

IMPLEMENTED (<N>):
  <slug>    [planned → implemented]
    + ~ <new-code-ref>
    + ~ <new-code-ref>
    ✓ assumption confirmed: <assumption text removed>   (if ! removed)
    ✗ assumption remains:   <assumption text>           (if ! still present)

NEW ENTRIES (<N>):
  <slug>    [<domain>]    [planned | implemented]
    <full entry block as it would appear in context output>
    ⚠ NEW ASSUMPTION: ! <assumption text>              (requires confirmation)

MODIFIED (<N>):
  <slug>    [<domain>]
    statement: <old> → <new>                           (if statement changed)
    assumption added: ! <text>
    assumption removed: ! <text>
    ref added: ~ <path>
    ref removed: ~ <path>

RESOLVED QUESTIONS (<N>):
  Q:<slug>  → closed
    resolved to: <how it was resolved>

REMOVED ENTRIES (<N>):
  <slug>    [<domain>]    <statement>
    ⚠ code refs remain: spec:<slug> found in <N> files  (if backlinks exist)

CONSTRAINTS CHANGED (<N>):
  C:<slug>  <change description>
  ⚠ constraint changes affect all requirements in domain

NOTHING CHANGED: <categories if some are empty>

─── Assumptions requiring confirmation:
    <slug>    ! <assumption>    → confirm or specify
    ...
```

The diff is the primary human review surface. Assumptions added (`!`) are the
items requiring human confirmation. Constraint changes are flagged specially
because they affect all downstream requirements.

---

### `spec write`

**When:** Agent is capturing new requirements from a user conversation or request.

**Interaction:** The command guides the agent through a structured authoring flow.
It is not interactive — it takes a structured input describing what to write and
validates it before writing.

**Input (as JSON on stdin or as arguments):**

```json
{
  "domain": "auth",
  "entries": [
    {
      "slug": "mfa-enrollment",
      "type": "requirement",
      "statement": "Users can enroll a TOTP authenticator app.",
      "provenance": "user said 'add MFA support'",
      "assumptions": ["assumed TOTP only — FIDO2 not mentioned"],
      "planned": true,
      "depends_on": ["google-login"]
    }
  ]
}
```

**Output:**

```
=== SPEC WRITE ===

Validation:
  ✓ slug mfa-enrollment available
  ✓ dependency google-login exists
  ✓ domain auth exists

Would write to specs/auth.md:

  mfa-enrollment: Users can enroll a TOTP authenticator app. [planned]
    > user said "add MFA support"
    ! assumed TOTP only — FIDO2 not mentioned
    @ google-login

Collision check: clean
Impact on existing entries: none

─── Confirm? (y/n):
```

In autonomous mode (no human present), the agent writes and records the write
in `spec diff` output for later human review.

---

### `spec reconcile <path>`

**When:** Code has changed without the spec being updated. Surfaces drift between
what the spec says and what the code contains.

**Input:** A code path (file or directory) or `--since <git-ref>`.

**Output:**

```
=== RECONCILE: <path> ===

CODE REFERENCES WITHOUT SPEC ENTRY (phantom slugs):
  <path>:<line>    spec:<slug>  — no entry found
  ...
  → Create entries for these slugs, or remove the spec: comments from code.

SPEC ENTRIES WITH MATCHING CODE BUT NO ~ REF:
  <slug>    [planned]  but spec:<slug> found in <path>:<line>
  ...
  → Mark these entries as implemented: spec write --implement <slug> <path>

SPEC ~ REFS POINTING TO MOVED/DELETED CODE:
  <slug>    ~ <old-path>  — not found
            code may have moved to: <suggested-path>   (if detectable)
  ...
  → Update refs: spec write --update-ref <slug> <new-path>

CLEAN:
  ✓ all spec: comments in <path> have matching entries
  ✓ all ~ refs in scope resolve
```

---

### `spec check-slug <slug>`

**When:** Before writing any new entry, to verify the slug is available.

```
=== CHECK-SLUG: session-expiry ===

TAKEN — specs/auth/sessions.md:
  session-expiry: Sessions expire after 30 days of inactivity.

Try: session-expiry-idle, user-session-expiry
```

or:

```
=== CHECK-SLUG: mfa-enrollment ===
Available.
```

---

## 13. Code-spec bidirectionality

The relationship between code and spec must be navigable in both directions with
zero ambiguity and detectable when broken.

### Code → spec (backlinks in source)

Every function, class, or logical block that implements a spec entry carries a
`spec:` comment. Language-agnostic, always the same format.

```python
# spec: session-expiry
def refresh_session(token: str) -> Session:
    ...

# spec: billing-session-sync, C:usage-cap
class PlanLimitMiddleware:
    ...
```

```typescript
// spec: admin-revoke
async function revokeSession(userId: string): Promise<void> {
```

```go
// spec: session-expiry
func RefreshSession(token string) (*Session, error) {
```

```java
// spec: session-expiry
public Session refreshSession(String token) {
```

**Rules:**

- One `spec:` comment per logical block — function, class, or file-level
- Multiple slugs comma-separated on the same line
- Place at the top of the block, not inline with logic
- Slugs only — no description, no file paths

### Spec → code (refs in spec entries)

```
session-expiry: Sessions expire after 30 days of inactivity.
  ~ src/middleware/session.py:44
  ~ src/middleware/session.py:101
```

**Ref formats:**

```
~ src/path/to/file.py             whole file
~ src/path/to/file.py:44         specific line
~ src/path/to/file.py:44-67      line range
~ src/path/to/dir/               directory (domain owns this area)
~ ClassName.method_name          symbolic ref (language-agnostic)
```

**Domain ownership refs:** In `## Refs`, use directory-level refs to declare what
code territory a domain owns. This powers `spec scope src/billing/` — the
domain's `## Refs` establishes that `src/billing/` belongs to billing.

### Integrity guarantees

`spec validate` checks both directions:

- Every `~` in specs resolves to a real path on disk
- Every `spec:` in code has a matching entry in specs
- `spec reconcile` surfaces drift when code changes without spec updates

---

## 14. Agent integration

The spec system is agent-agnostic. It integrates with any agent that can run
shell commands or read files. Integration means one thing: **the agent always
calls `spec scope` before touching code, and always calls `spec validate` before
committing.**

### Integration patterns

#### Pattern A: Rules file (Cursor rules / .claude / agent instructions)

Add to `.cursorrules`, `.claude/CLAUDE.md`, or equivalent:

```markdown
## Spec-driven development

This repository uses spec-driven development. The spec lives in specs/.
The markdown files in specs/ are always the source of truth.

Before modifying any code:

1. Run: python specs/spec.py scope <file-you-are-changing>
2. Read the output completely. Understand what specs govern this code.
3. If you need more context: python specs/spec.py context <slug>
4. If your change affects multiple files: python specs/spec.py impact <slug>

You can also grep specs/ directly:
grep -r "^session-expiry:" specs/ # find an entry
grep -r "^ !" specs/ # see all unconfirmed assumptions
grep -r "\[planned\]" specs/ # see the full backlog

Before every commit:

1. Run: python specs/spec.py validate
2. Fix all errors. Review all warnings.
3. If spec entries need updating, update them in the same commit as the code.

When writing or modifying spec entries:

1. Use: python specs/spec.py write (validates before writing)
2. Or edit the markdown files directly — the format is documented in specs/SPEC-ARCHITECTURE.md
3. Never write to .spec/ (the cache) — it is machine-generated from the files
4. Always run spec validate after any manual file edit

Spec and code changes go in the same commit, always.
```

#### Pattern B: SPEC_AGENT.md (the agent's operating manual)

`specs/SPEC_AGENT.md` is a dedicated file the agent loads at the start of every
session. It contains the operating rules, the command reference summary, and the
workflow it must follow. It is part of the repository.

See the companion document `SPEC_AGENT.md` for the full agent operating rules.
This architecture document explains the system. `SPEC_AGENT.md` tells the agent
what to do.

#### Pattern C: MCP server (future)

The CLI commands map cleanly to MCP tools. A spec MCP server exposes each command
as a tool with structured input/output, enabling agents that support MCP to call
spec operations as first-class tool calls rather than shell commands.

Tool names map directly: `spec_orient`, `spec_scope`, `spec_context`, `spec_impact`,
`spec_find`, `spec_validate`, `spec_diff`, `spec_write`, `spec_reconcile`.

Input/output schemas match the CLI command signatures exactly. The MCP server is
a thin wrapper around the same `SpecStore` interface.

### Agent session protocols

**Coding session (consume mode):**

```
1. spec scope <file-being-modified>
2. spec context <slug>             if needed
3. spec impact <slug>              before significant changes
4. [make code changes]
5. spec validate
6. spec diff                       review what changed
7. commit: spec + code together
```

**Spec maintenance session (maintain mode):**

```
1. spec orient                     understand current state
2. spec domain <relevant-domain>   load domain to understand existing entries
3. [write or update spec entries]
4. spec validate
5. spec diff                       produce human review manifest
6. commit
```

**New feature session:**

```
1. spec orient                     understand current state
2. spec find <feature-keywords>    check if anything related exists
3. spec domain <affected-domain>   understand the domain
4. [clarify requirements with user — ask questions]
5. spec write                      capture requirements
6. spec validate
7. spec diff                       show human what will change
8. [implement code]
9. spec validate
10. spec diff                      final review
11. commit: spec + code together
```

**Debugging session:**

```
1. spec scope <file-with-bug>      understand what specs govern this
2. spec context <relevant-slug>    understand the expected behavior
3. [debug and fix]
4. spec validate                   check nothing drifted
5. commit if spec needed updating
```

### Agent rules for spec maintenance

These rules are absolute. No exceptions.

**Never silently fill a gap.** Every specific detail the agent decides on the
user's behalf — a number, a threshold, a binary choice — gets a `!` line. The
`!` line is what makes the spec auditable.

**Never write evolutionary language.** No "previously", "changed from", "was
replaced by", "deprecated". The spec describes current state only.

**Always check slug availability** before writing a new entry.

**Never write to `.spec/` directly.** The `.spec/` directory is machine-generated
from the markdown files. Writing to it directly would create a cache that does
not reflect the files, which breaks the foundational invariant. The CLI and the
pre-commit hook manage the cache.

**Never write a spec entry without a `>` line.** If you cannot find user provenance,
use `> inferred from: <reasoning>` and always pair with a `!` line.

**One commit contains both the spec change and the code change.** Never split them.

**Never write an entry without a `>` line.** If you cannot find user provenance,
use `> inferred from: <reasoning>` and always pair with a `!` line.

---

## 15. The development workflow

New requests follow a structured flow. This is not enforced by tooling — it is
enforced by the agent following the protocol.

### Step 1: Orient

```
spec orient
```

Understand the current state of the spec before engaging with the request.
What domains exist? What is currently planned? What is unresolved?

### Step 2: Understand the request

Before touching any spec or code, the agent must understand:

- What is the user actually asking for?
- Does this contradict any existing requirement or constraint?
- Which domains are affected?
- Are there open questions that are relevant?

If the request contradicts an existing entry, stop and surface the contradiction:

```
Understood: <what I understood the request to be>
Contradiction: this conflicts with <slug>: <statement>
Options:
  A. Replace <slug> with the new behavior
  B. Add the new behavior as a variant (requires clarifying <slug>)
  C. Add to out-of-scope and reject the request
Question: which option should I take?
```

### Step 3: Clarify with questions

Before writing anything, ask questions that close open assumptions. One question
at a time. Contradictions first.

Questions target assumptions that would otherwise need a `!` line. Every question
answered is one fewer `!` in the spec.

```
Understood: <summary>
I need to clarify one thing before writing the spec:

<single question>

Assumption if you want me to proceed without answering:
<what I'd assume, which I'll flag with !>
```

### Step 4: Write spec entries

After clarification:

```
spec check-slug <proposed-slug>
spec write
```

Show the agent what it would write using `spec diff` before writing:

```
I'll add the following to specs/auth.md:

  mfa-enrollment: Users can enroll a TOTP authenticator app. [planned]
    > "add MFA support"
    ! assumed TOTP only — FIDO2 not mentioned
    @ google-login

One assumption remains: TOTP vs FIDO2. Confirm TOTP only?
```

### Step 5: Plan the implementation

After spec is written, derive the implementation plan from the spec diff:

```
Based on the spec changes, here is the implementation plan:

1. Create mfa-enrollment UI   ← mfa-enrollment requirement
2. Create TOTP setup API      ← mfa-enrollment requirement
3. Update login flow          ← mfa-login-required requirement
4. Update session middleware  ← mfa-session-flag requirement (depends on session-expiry)

Files affected (from spec scope):
  src/api/auth/      ← auth domain owns this
  src/middleware/    ← session-expiry is referenced here
```

### Step 6: Implement

Code, with `spec:` backlinks at every implementation site.

### Step 7: Validate and commit

```
spec validate
spec diff
# commit: spec + code in same commit
```

---

## 16. Human review model

The human's primary interface to the spec is `spec diff`. It is designed to be
reviewed in under a minute for typical changes.

**What makes something reviewable:**

- Changes are expressed in behavior terms, not file diffs
- Assumptions (`!`) are the explicit review surface — these are what the agent
  decided on the human's behalf
- Constraint changes are flagged specially — they have broad impact
- Removed entries with remaining code backlinks are flagged — potential orphaned code

**What does not require human review:**

- `~` ref additions when marking an entry implemented
- `!` removal when an assumption was confirmed
- `Q:` deletion when a question was resolved

**What always requires human review:**

- New `!` assumptions — the human confirms or corrects
- Statement changes — the behavior changed
- Constraint changes — non-negotiable rules changed
- Entry deletions — behavior was removed

**The assumption confirmation flow:**

When a human sees `! assumed X` in a diff, they have three options:

1. Confirm: "yes, X is correct" → agent removes the `!` line, spec reads as
   user-specified
2. Correct: "no, it should be Y" → agent rewrites the statement with Y, removes `!`
3. Defer: "not decided yet, keep the assumption" → `!` remains, appears in every
   future diff until confirmed

---

## 17. Reconciliation

Reconciliation handles the case where code diverged from spec — either code was
written without updating the spec, or spec was updated without updating the code.

### Detecting drift

```bash
spec reconcile src/          # full codebase
spec reconcile src/billing/  # specific directory
spec reconcile --since HEAD~5  # changes since a git ref
```

### Types of drift

**Phantom slug:** `spec: slug` in code but no entry in specs.
The code was written without creating a spec entry.
Resolution: Create the spec entry, or remove the `spec:` comment from code.

**Silent implementation:** `[planned]` in spec but code implements it.
The code was written before the spec was updated.
Resolution: Mark the spec entry as implemented with `~` refs.

**Dead ref:** `~` in spec but file doesn't exist.
Code was refactored or deleted without updating the spec.
Resolution: Update the `~` ref to the new path, or remove it if the code is gone.

**Missing backlink:** `~` in spec points to a file but the file has no `spec:`
comment back. Not an error — but worth adding for full bidirectionality.

### Reconciliation after autonomous code changes

When an agent modifies code autonomously (e.g., automated PR), run:

```bash
spec reconcile --since <base-branch>
spec validate
spec diff <base-branch>
```

The diff shows what the agent changed. The reconcile shows if code and spec are
still aligned. Both outputs are included in the PR description for human review.

---

## 18. Validation rules

Complete list of all invariants. `spec validate` checks all of these.

### Errors (block commit)

| Rule              | Check                                                        |
| ----------------- | ------------------------------------------------------------ |
| no-dead-ref       | Every `~` path in specs resolves to a real file or directory |
| no-phantom-slug   | Every `spec:` in code has a matching entry in specs          |
| no-duplicate-slug | All slugs are globally unique across the specs tree          |
| no-cycle          | No dependency chain forms a cycle                            |
| no-ghost-scope    | Every node has a `>` line                                    |
| no-dangling-dep   | Every `@` target exists as a slug in the specs tree          |
| no-dangling-block | Every `? Q:slug` target exists as a question node            |

### Warnings (surface, don't block)

| Rule             | Check                                                         |
| ---------------- | ------------------------------------------------------------- |
| silent-impl      | `[planned]` node but `spec:` comment found in code            |
| orphan-question  | `Q:` node not referenced by any `?` line                      |
| orphan-entry     | Node with no `~` refs, no `@` dependents, not `[planned]`     |
| stale-assumption | `!` lines that have existed unchanged for more than N commits |

### Info (always surface)

| Rule                    | Output                                 |
| ----------------------- | -------------------------------------- |
| unconfirmed-assumptions | List all `!` lines for human awareness |

---

## 19. Grep grammar reference

All primary entries at column 0. All sub-lines indented exactly 2 spaces.
This is structural — never deviate.

```
Pattern                      Matches
────────────────────────────────────────────────────────────
^[a-z][a-z0-9-]*:            requirement (col 0, no prefix)
^C:[a-z][a-z0-9-]*:          constraint (col 0, C: prefix)
^Q:[a-z][a-z0-9-]*:          open question (col 0, Q: prefix)
^  >                          provenance (2-space indent)
^  !                          assumption (2-space indent)
^  ~                          code ref (2-space indent)
^  @                          depends-on (2-space indent)
^  ?                          blocked-by (2-space indent)
\[planned\]                   unimplemented requirement
spec: [a-z]                   code backlink (in source files)
```

**Key queries:**

```bash
# Orientation
grep -rh "^>" specs/*.md specs/*/README.md       # all domain summaries
grep -r "^Q:" specs/                             # all open questions
grep -r "\[planned\]" specs/                     # full backlog
grep -r "^  !" specs/                            # all unconfirmed assumptions
grep -r "^  @" specs/                            # all cross-spec dependencies
grep -r "^C:" specs/                             # all constraints

# Finding entries
grep -r "^session-expiry:" specs/                # find entry by slug
grep -r "^[a-z][a-z0-9-]*:" specs/auth.md       # all entries in a file

# Dependency queries
grep -r "^  @ session-expiry" specs/             # what depends on this slug
grep -r "^  ? Q:guest-access-expiry" specs/      # what is blocked by this question
grep -rn "spec: session-expiry" src/             # code implementing this slug

# Code-spec queries
grep -r "~src/api/auth" specs/                   # specs touching a code path
grep -rn "spec: " src/middleware/session.py      # what slugs does this file implement

# Collision and integrity
grep -rh "^[a-z][a-z0-9-]*:\|^C:\|^Q:" specs/ | cut -d: -f1,2 | sort | uniq -d
grep -rh "spec: " src/ | sed 's/.*spec: //' | tr ',' '\n' | tr -d ' ' | sort -u
```

---

## 20. Bootstrap guide

Setting up spec-driven development in a new repository.

### Step 1: Add spec.py to the repository

```bash
mkdir -p specs
curl -o specs/spec.py https://raw.githubusercontent.com/<org>/spec-system/main/spec.py
chmod +x specs/spec.py
```

Or copy `spec.py` directly from this document's companion code.

### Step 2: Create CONTEXT.md

```bash
python specs/spec.py init
```

This starts an interactive session to create `specs/CONTEXT.md` from a description
of the project. Alternatively, create it manually following the format in Section 9.

### Step 3: Add agent integration rules

Copy the appropriate integration file for your agent:

**Cursor:**

```bash
cat >> .cursorrules << 'EOF'
<paste Pattern A from Section 14>
EOF
```

**Claude / Claude Code:**

```bash
mkdir -p .claude
cat > .claude/CLAUDE.md << 'EOF'
<paste Pattern A from Section 14>
EOF
```

**Generic (any agent that reads a rules file):**

```bash
cp specs/SPEC_AGENT.md .agent-rules.md
```

### Step 4: Add pre-commit hook

```bash
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/sh
if git diff --cached --name-only | grep -q "^specs/"; then
  python specs/spec.py validate
  if [ $? -ne 0 ]; then
    echo "spec validate failed — fix errors before committing"
    exit 1
  fi
  python specs/spec.py rebuild-cache
  git add specs/.spec/
fi
EOF
chmod +x .git/hooks/pre-commit
```

### Step 5: Write the first domain

```bash
python specs/spec.py orient    # see the empty state
python specs/spec.py write     # guided authoring
```

Or create `specs/auth.md` manually following the format in Section 5.

### Step 6: Add spec: backlinks to existing code

This can be done incrementally. Run `spec reconcile src/` to see the full picture
of what code exists without spec coverage, then add entries as you understand the
system.

---

## Appendix A: Environment variables

| Variable         | Default       | Description                                |
| ---------------- | ------------- | ------------------------------------------ |
| `SPEC_BACKEND`   | `file`        | Storage backend: `file`, `cached`, `neo4j` |
| `SPEC_DIR`       | `specs`       | Path to the specs directory                |
| `NEO4J_URI`      | —             | Neo4j connection URI (Phase 3 only)        |
| `NEO4J_USER`     | —             | Neo4j username                             |
| `NEO4J_PASS`     | —             | Neo4j password                             |
| `SPEC_CACHE_DIR` | `specs/.spec` | Cache directory for CachedSpecStore        |

---

## Appendix B: File format quick reference

```
# Domain Name
> One-line summary (shown in spec orient output)

## Constraints

C:slug: Constraint statement.
  > user provenance (required)
  ! agent assumption (when applicable)
  ~ code-ref (when enforced in code)

## Requirements

slug: Requirement statement. [planned if not implemented]
  > user provenance (required)
  ! agent assumption (required when filling gaps)
  @ slug-or-C:slug (depends-on, one per line)
  ? Q:slug (blocked-by, one per line)
  ~ src/path/file.py:line (code ref, one per line when implemented)

## Open Questions

Q:slug: Question statement?
  > what this blocks

## Out of scope
Item one.
Item two.

## Refs
~ src/domain-directory/
~ src/other-owned-file.py
```

---

## Appendix C: Commit message conventions

```
spec(<domain>): add <slug>
spec(<domain>): implement <slug>
spec(<domain>): update <slug>
spec(<domain>): close Q:<slug>
spec(<domain>): resolve ! <assumption-slug>
spec: split <domain> into folder
spec: reconcile src/<path>
```

Spec and code changes in the same commit use:

```
feat(<domain>): <description>

spec: add <slug>, implement <slug>
```

The `spec:` trailer line lists what spec changes were made alongside the code
change. This makes the spec history greppable from git log.

---

## Appendix D: Scaling thresholds

| Scale   | Requirements | Domains | Backend         | Cache                        | Semantic search |
| ------- | ------------ | ------- | --------------- | ---------------------------- | --------------- |
| Phase 1 | < 200        | < 15    | FileSpecStore   | none                         | not needed      |
| Phase 2 | 200–1000     | 15–50   | CachedSpecStore | graph.json + code-index.json | not needed      |
| Phase 3 | 1000+        | 50+     | Neo4jSpecStore  | native graph DB              | optional        |

Semantic search (`spec find` via embeddings) is optional at all scales. The spec
is authored — slugs are human-chosen and descriptive. An LLM can match natural
language queries to slug names without vector embeddings. Add semantic search
when `spec find` returns too many false positives or too many misses.
