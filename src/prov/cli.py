"""CLI entry point — argument parsing and command dispatch."""
from __future__ import annotations

import sys
from pathlib import Path

from prov.commands import (
    cmd_check_slug,
    cmd_context,
    cmd_diff,
    cmd_domain,
    cmd_find,
    cmd_impact,
    cmd_init,
    cmd_orient,
    cmd_rebuild,
    cmd_reconcile,
    cmd_scope,
    cmd_sync,
    cmd_validate,
    cmd_write,
)
from prov.spec_io import get_repo_root, get_spec_dir


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]

    # Resolve spec dir: entry script's parent dir (e.g. src/ or prov/)
    entry = Path(sys.argv[0]).resolve()
    entry_dir = entry.parent if entry.suffix else Path.cwd()
    spec_dir = get_spec_dir(entry_dir)
    repo_root = get_repo_root(spec_dir)

    if not args:
        print("Usage: prov <command> [args]  (or: python prov/prov.py <command> [args])")
        print(
            "Commands: orient, scope <path>, context <slug>, impact <slug>, find <kw>, domain <name>,"
        )
        print(
            "          validate, check-slug <slug>, reconcile <path>, sync [path],"
        )
        print(
            "          sync mark-implemented <slug>, sync remove-ref <slug> <ref>,"
        )
        print(
            "          sync update-ref <slug> <old> <new>, sync remove-backlink <file> <line> <slug>,"
        )
        print("          write [--yes], diff [ref], rebuild, init")
        return 0

    cmd = args[0].lower()
    rest = args[1:]

    # Commands other than init require an existing spec directory
    if cmd != "init" and not (spec_dir / "CONTEXT.md").exists():
        print("No spec directory found.")
        print("  Run 'prov init' to scaffold one, or cd into a project with prov/, spec/, or specs/.")
        return 1

    if cmd == "orient":
        cmd_orient(spec_dir, repo_root)
    elif cmd == "scope":
        cmd_scope(spec_dir, repo_root, rest[0] if rest else ".")
    elif cmd == "context":
        if not rest:
            print("Usage: prov context <slug>")
            return 1
        cmd_context(spec_dir, repo_root, rest[0])
    elif cmd == "impact":
        if not rest:
            print("Usage: prov impact <slug>")
            return 1
        cmd_impact(spec_dir, repo_root, rest[0])
    elif cmd == "find":
        cmd_find(spec_dir, " ".join(rest) if rest else "")
    elif cmd == "domain":
        if not rest:
            print("Usage: prov domain <name>")
            return 1
        cmd_domain(spec_dir, rest[0])
    elif cmd == "validate":
        return cmd_validate(spec_dir, repo_root)
    elif cmd == "check-slug":
        if not rest:
            print("Usage: prov check-slug <slug>")
            return 1
        cmd_check_slug(spec_dir, rest[0])
    elif cmd == "reconcile":
        cmd_reconcile(spec_dir, repo_root, rest[0] if rest else ".")
    elif cmd == "sync":
        return cmd_sync(spec_dir, repo_root, rest)
    elif cmd in ("rebuild", "rebuild-cache"):
        cmd_rebuild(spec_dir)
    elif cmd == "write":
        return cmd_write(spec_dir, repo_root, rest)
    elif cmd == "diff":
        ref = rest[0] if rest else "HEAD"
        cmd_diff(spec_dir, repo_root, ref)
    elif cmd == "init":
        cmd_init(spec_dir)
    else:
        print(f"Unknown command: {cmd}")
        return 1
    return 0
