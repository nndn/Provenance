"""prov init — scaffold CONTEXT.md and install agent skills/rules."""
from __future__ import annotations

from pathlib import Path

from prov import installer

CONTEXT_TEMPLATE = """# <Project Name>

> <One sentence. What it does and who uses it.>

## Purpose

<2-3 sentences. The problem being solved.>

## User goals

1. <Primary user goal>
2. <Secondary goal>

## Hard constraints

C:example: <Non-negotiable rule>

> <why>

## Non-goals

- <Explicit out-of-scope items>

## Domain map

<domain> prov/<domain>.md
"""


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _print_rows(rows: "list[tuple[str, str]]") -> None:
    width = max(len(p) for p, _ in rows)
    for path, status in rows:
        print("  {}  {}".format(path.ljust(width), status))


def _scaffold(spec_dir: Path) -> bool:
    """Create CONTEXT.md if absent. Returns True if created."""
    spec_dir.mkdir(parents=True, exist_ok=True)
    ctx_path = spec_dir / "CONTEXT.md"
    if ctx_path.exists():
        print("CONTEXT.md already exists.")
        return False
    ctx_path.write_text(CONTEXT_TEMPLATE, encoding="utf-8")
    print("Created CONTEXT.md. Edit it with your project details.")
    return True


def _check(spec_dir: Path, repo_root: Path) -> int:
    """Report status of everything; write nothing."""
    ctx_path = spec_dir / "CONTEXT.md"
    rows: "list[tuple[str, str]]" = [
        (_rel(ctx_path, repo_root), "present" if ctx_path.is_file() else "missing")
    ]
    status = installer.check_status(repo_root)
    for std in installer.STANDARDS:
        rows.extend(status[std])
    _print_rows(rows)
    ok = all(s in ("present", "up to date") for _, s in rows)
    return 0 if ok else 1


# spec: spec-init
def cmd_init(
    spec_dir: Path,
    repo_root: Path,
    *,
    agents: bool = True,
    claude: bool = True,
    open_std: bool = True,
    check: bool = False,
    force: bool = False,
) -> int:
    """Scaffold the spec dir and install prov agent skills/rules."""
    if check:
        return _check(spec_dir, repo_root)
    fresh = _scaffold(spec_dir)
    if agents and (claude or open_std):
        report = installer.install(
            repo_root, claude=claude, open_std=open_std, force=force
        )
        rows: "list[tuple[str, str]]" = []
        for std in installer.STANDARDS:
            rows.extend(report.get(std, []))
        print("")
        print("Agent assets:")
        _print_rows(rows)
    if fresh:
        print("")
        print("Next steps:")
        print(
            "  1. Edit {} — project name, constraints, domain map.".format(
                _rel(spec_dir / "CONTEXT.md", repo_root)
            )
        )
        print("  2. Create your first domain file: prov domain <name>")
        print("  3. Orient your agent: prov orient")
    return 0
