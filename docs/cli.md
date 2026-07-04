# prov CLI reference

```
prov [OPTIONS] COMMAND [ARGS]...
```

Running `prov` with no arguments prints help. All command output is plain
structured text designed for direct inclusion in an agent's context window.

## Global options

| Option | Effect |
|---|---|
| `--version` | Print `prov <version>` and exit |
| `--install-completion` | Install shell completion for the current shell |
| `--show-completion` | Print the completion script |
| `--help` | Show help (also per command: `prov <command> --help`) |

## Spec directory resolution

Every invocation resolves the spec directory once:

1. `SPEC_DIR` environment variable, if set.
2. Otherwise, search from the current directory upward for a `prov/`,
   `spec/`, or `specs/` directory containing spec files.
3. Otherwise, default to `./prov` (this is what `prov init` scaffolds).

The repo root is the git toplevel containing the spec directory (its parent
when not a git repo).

Every command except `init` requires `<spec-dir>/CONTEXT.md`. When it is
missing, the command prints:

```
No spec directory found.
  Run 'prov init' to scaffold one, or cd into a project with prov/, spec/, or specs/.
```

and exits 1. `prov <command> --help` works anywhere.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Success (including `validate` with warnings only, and `sync` drift reports) |
| 1 | No spec directory; `validate` with errors; `write` input or validation errors; `sync` patch failures; `init --check` with anything missing or outdated |
| 2 | Usage error — unknown command, missing required argument, unknown option |

---

## Commands

### `prov orient`

```
prov orient
```

Project overview — start every session here. Prints the project purpose,
hard constraints, domain summaries, open questions, unconfirmed assumptions,
and planned work. No arguments. Exit 0.

### `prov scope [PATH]`

```
prov scope [PATH]      # PATH: file or directory, default "."
```

Show which spec entries govern a file or directory — requirements,
constraints, dependents, and blocking questions. Resolves via direct `~`
refs and directory ownership declared in `## Refs`. Exit 0.

### `prov context SLUG`

```
prov context SLUG      # SLUG: entry slug (required)
```

Full entry: statement, provenance, assumptions, code refs, dependencies,
dependents, and blocking questions. Exit 0.

### `prov impact SLUG`

```
prov impact SLUG       # SLUG: entry slug (required)
```

Blast radius before changing an entry: direct and transitive dependents,
all code in the blast radius, assumptions and planned entries in the path.
Exit 0.

### `prov find [KEYWORDS]...`

```
prov find [KEYWORDS]...
```

Search entries by keyword when you don't know the slug. Matches slug names
and statement text. Exit 0 (including no matches).

### `prov domain NAME`

```
prov domain NAME       # NAME: domain name (required)
```

Load a full domain: summary, constraints, requirements, open questions,
out-of-scope list. Exit 0.

### `prov validate`

```
prov validate
```

Validate the spec index — run before every commit. Reports errors,
warnings, and unconfirmed assumptions (see the
[validation checks table](spec-format.md#validation-checks)). Exit 1 if any
errors; warnings alone exit 0.

### `prov check-slug SLUG`

```
prov check-slug SLUG   # SLUG: slug to check (required)
```

Check whether a slug is available before writing a new entry. Prints
`Available.` or the entry that takes it. Exit 0 either way.

### `prov reconcile [PATH]`

```
prov reconcile [PATH]  # PATH: file or directory, default "."
```

Detect code<->spec drift for a path (read-only): phantom slugs, silent
implementations, dead refs. Exit 0.

### `prov sync [ARGS]...`

```
prov sync [PATH]                                # drift report, default "."
prov sync mark-implemented SLUG                 # remove [planned], add ~ refs from code backlinks
prov sync remove-ref SLUG REF                   # remove a ~ ref from an entry
prov sync update-ref SLUG OLD NEW               # replace a ~ ref
prov sync remove-backlink FILE LINE SLUG        # remove a spec: backlink from code
```

Drift report between spec and code, plus patch sub-commands that fix each
drift class. The report groups drift into silent implementations, phantom
slugs, and dead refs, and names the sub-command that fixes each item.

Exit codes: the report form exits 0 even with drift. Patch forms exit 1 on
missing arguments or an unknown slug/ref/backlink; 0 on success. A first
argument that is not one of the four sub-commands is treated as a PATH.

### `prov rebuild`

```
prov rebuild
```

Regenerate the optional `.spec/` cache from spec files. The cache is never
the source of truth; it can always be deleted and rebuilt. Exit 0.
`rebuild-cache` is a hidden alias.

### `prov write [ARGS]...`

```
prov write [--yes|-y] [ARGS]...
```

Add entries from JSON input (validates before writing). Input forms:

- no args — read JSON from stdin
- `prov write '<json-string>'`
- `prov write path/to/entries.json`
- `prov write --json '<json-string>'`

Input schema:

```json
{
  "domain": "auth",
  "entries": [{
    "slug": "mfa-enrollment",
    "type": "requirement",
    "statement": "Users can enroll a TOTP authenticator app.",
    "provenance": "user: \"add MFA support\"",
    "assumptions": ["assumed TOTP only — FIDO2 not mentioned"],
    "planned": true,
    "depends_on": ["google-login"],
    "code_refs": [],
    "blocked_by": []
  }]
}
```

`type` is `requirement` (default), `constraint`, or `question`; the `C:` /
`Q:` prefix is added automatically. `provenance` is required. Slugs must be
kebab-case and available; `depends_on` targets must exist.

Without `--yes`, prints a preview of what would be written and exits 0.
With `--yes` (`-y`), writes the entries into the domain file. Exit 1 on
invalid JSON, missing `domain`/`entries`, unknown domain, or validation
errors.

### `prov diff [REF]`

```
prov diff [REF]        # REF: git ref to compare against, default HEAD
```

Semantic change manifest vs HEAD or any ref — new, modified, implemented,
and removed entries, resolved questions, and assumptions requiring
confirmation. Expressed in spec terms, not line diffs. Exit 0.

### `prov init`

```
prov init [--check] [--force] [--no-agents] [--no-claude] [--no-open]
```

Scaffold `prov/CONTEXT.md` and install agent assets (skills + rules) for
the Claude and open agent standards. The only command that works without an
existing spec directory. See [agent-setup.md](agent-setup.md) for what gets
installed where.

| Flag | Effect |
|---|---|
| `--check` | Report the status of everything (`present` / `up to date` / `outdated` / `missing`); write nothing |
| `--force` | Overwrite locally modified skill files |
| `--no-agents` | Scaffold CONTEXT.md only; skip all agent assets |
| `--no-claude` | Skip `.claude/skills/` and the CLAUDE.md block |
| `--no-open` | Skip `.agents/skills/` and the AGENTS.md block |

Idempotent — re-running reports `up to date` and never touches user content.
Exit 0, except `--check` which exits 1 if anything is missing or outdated.
