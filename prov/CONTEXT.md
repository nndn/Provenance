# Provenance

> A living requirements index maintained alongside the codebase; agents and developers use it to understand what the system does and why.

## Purpose

The spec answers one question at any point in time: what does this system do, and why? It is a precise, current snapshot of user intent — everything a fresh agent or developer needs to understand required behavior without reading code. It lives in the repository so every clone carries the full spec; there is no external system to sync, no wiki to go stale.

## User goals

1. Maintain a single source of truth for requirements that ships with the code.
2. Enable agents to write and query specs without ambiguity; support grep and CLI for retrieval.
3. Keep spec and code bidirectionally linked and detectable when broken.

## Hard constraints

C:files-canonical: Markdown files in the spec directory are the spec — the actual spec, not a representation. Every query backend is a read-acceleration layer built from those files.

> "The markdown files in specs/ are the spec. Not a representation of the spec, not a serialization format."

C:minimal-deps: The prov CLI keeps runtime dependencies minimal — typer is the only runtime dependency; everything else is Python 3.9+ standard library.

> "Any agent or developer can run it without setup beyond Python."

C:output-compat: Command stdout, stderr, and exit codes are user-facing behavior; refactors keep them byte-identical for existing commands.

> "I've used this for a while and I know it works. So keep the functionality the same."

## Non-goals

Changelog, design journal, documentation of implementation. Decision rationale prose. Semantic search (optional at all scales). External wiki or requirements database.

## Domain map

core prov/core.md
format prov/format.md
storage prov/storage.md
cli prov/cli.md
agent prov/agent.md
install prov/install.md
