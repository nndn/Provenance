---
name: spec-drift-sync
version: "1.0"
triggers:
  - running prov sync or prov reconcile
  - after bulk refactors, large merges, or importing existing code
  - user asks to reconcile spec and code
  - after autonomous code changes that may have left spec out of date
---

## Mission

Resolve drift between spec and code by running the sync protocol, presenting each drift item to the user with context, and applying only user-confirmed fixes so that spec and code match.

---

## Pre-requisites

- **prov CLI** with `prov sync` and `prov reconcile` (and patch subcommands: `mark-implemented`, `remove-ref`, `update-ref`, `remove-backlink`). If prov is not available, document that drift resolution was skipped.
- **Spec directory** and **codebase** in the same repo (or paths known).
- **Read access** to spec files and code; **write access** to spec files (and optionally code for removing backlinks) after user confirms.

---

## Instructions

### Step 1 — Run the drift report

Run `prov sync <path>` (e.g. `prov sync src/`) or `prov reconcile <path>` for read-only. Read the full output. Identify each reported item by type (silent implementation, phantom slug, dead ref). See Reference → What drift is.

### Step 2 — Present each item to the user

For each drift item: state type, slug, and location (file, line or path). State what the spec currently says vs what the code currently does. Offer the resolution options from Reference → Resolution by type. Ask: "What should I do?" Do not apply any fix until the user answers. Use the example presentation format in Reference if helpful.

### Step 3 — Apply only confirmed fixes

Use the exact commands in Reference → Patch commands. For silent implementation: `mark-implemented` or `remove-backlink`. For phantom slug: add entry via request flow or `remove-backlink`. For dead ref: `update-ref` or `remove-ref` (and consider `[planned]` or removing the entry). Only after user confirms each item.

### Step 4 — Validate and commit

Run `prov validate` (zero errors). Run `prov diff`. Commit spec (and any code changes) with a message such as `spec: reconcile src/<path>`.

### Step 5 — After autonomous code changes

When the agent made code changes without the normal request flow (e.g. bulk refactor, automated migration), run `prov sync src/` before committing and include a short drift summary in the PR description. See Reference → After autonomous code changes.

---

## Reference

### What drift is

Drift is a gap between what the spec says and what the code does. Three types:

| Type | Description | Detected by |
|------|-------------|-------------|
| **Silent implementation** | `[planned]` entry but code already has `spec:` backlink | `prov sync` |
| **Phantom slug** | `spec:` in code references a slug with no spec entry | `prov sync` |
| **Dead ref** | `~` path in spec no longer exists as a file or directory | `prov sync` |

### Example presentation to the user

```
SILENT IMPLEMENTATION: session-expiry
  Spec says: [planned]
  Code has:  # spec: session-expiry  in src/middleware/session.py:44

  Options:
    A. Mark as implemented — remove [planned], the code ref counts
    B. Remove the backlink — code shouldn't claim to implement this yet
    C. Skip — leave it as-is for now

  What should I do?
```

### Patch commands (apply only after user confirms)

```bash
# Silent implementation → mark as implemented
prov sync mark-implemented <slug>

# Phantom slug → remove the backlink (if the slug shouldn't exist)
prov sync remove-backlink <file> <line> <slug>
# or → add the missing spec entry via request flow (if the code is correct)

# Dead ref → remove the stale path
prov sync remove-ref <slug> <ref>
# or → update to the new path
prov sync update-ref <slug> <old-path> <new-path>
```

### Resolution decisions by drift type

**Silent implementation** — Spec says `[planned]` but the code already implements it.

- **Mark implemented** (`prov sync mark-implemented <slug>`): The implementation is correct and complete. Remove `[planned]`, add `~` ref.
- **Remove backlink** (`prov sync remove-backlink ...`): The code should not claim to implement this yet. The spec's `[planned]` is correct.

**Phantom slug** — Code has `# spec: some-slug` but `some-slug` doesn't exist in the spec.

- **Add the spec entry**: The code is right; the spec is missing the entry. Go through request flow Phase 3 → 4 to add it properly.
- **Remove the backlink**: The `spec:` comment is wrong or outdated.

**Dead ref** — A `~` path in the spec no longer exists.

- **Update the ref** (`prov sync update-ref ...`): The file moved or was renamed. Update to the new path.
- **Remove the ref** (`prov sync remove-ref ...`): The code was deleted. The implementation is gone; the entry may need `[planned]` restored or be removed entirely.

### After autonomous code changes

When the agent has made code changes without going through the normal request flow (e.g. bulk refactor, automated migration), always run reconcile before committing:

```bash
prov sync src/        # full drift report
prov validate         # confirm zero errors
prov diff             # review spec changes
```

Include the drift summary in the PR description so the human reviewer can see what changed in the spec alongside the code.

### Read-only drift check

To see drift without applying any fixes:

```bash
prov reconcile src/              # full read-only report
prov reconcile src/ --since HEAD  # since last commit (if supported)
```

Output sections: PHANTOM SLUGS, SILENT IMPLEMENTATIONS, DEAD REFS, CLEAN (if none).

---

## Error Handling

| If this happens | Do this |
|-----------------|--------|
| **Silent implementation** — spec has `[planned]` but code has `spec:` | Present options: A. Mark implemented (update spec, add `~`). B. Remove backlink (code shouldn't claim it yet). C. Skip. Do not choose for the user. |
| **Phantom slug** — `spec:` in code but no spec entry | Present options: A. Add the spec entry (via request flow). B. Remove the backlink. Do not add an entry without user confirmation. |
| **Dead ref** — `~` path in spec does not exist | Present options: A. Update ref to new path. B. Remove ref (and possibly set entry back to `[planned]` or remove entry). Do not leave a `~` pointing at a missing file. |
| User says "skip" or "leave it for now" for an item | Do not apply any fix for that item. Move to the next item. You may note in the commit message that some drift was left unresolved. |
| `prov sync` or `prov reconcile` is not available | Do not invent patch commands. Tell the user that drift was detected but prov sync is required to fix it; list the drift items you can infer from grep/code inspection if possible. |
| After applying fixes, `prov validate` still reports errors | Fix the new errors (e.g. duplicate slug, missing `>`, dangling ref). Do not commit until validate passes. |
