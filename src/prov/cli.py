"""CLI entry point — typer app wiring the commands in prov.commands."""
from __future__ import annotations

import sys
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as pkg_version
from pathlib import Path
from typing import List, Optional

import typer

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

# spec: cli-typer-interface
app = typer.Typer(
    no_args_is_help=True,
    add_completion=True,
    help="Living requirements index + CLI for spec-driven development.",
)

_dirs: tuple[Path, Path] | None = None


def _resolve_dirs() -> tuple[Path, Path]:
    """Resolve (spec_dir, repo_root) from the entry script's dir or cwd."""
    entry = Path(sys.argv[0]).resolve()
    entry_dir = entry.parent if entry.suffix else Path.cwd()
    spec_dir = get_spec_dir(entry_dir)
    repo_root = get_repo_root(spec_dir)
    return spec_dir, repo_root


def _get_dirs() -> tuple[Path, Path]:
    """Return the shared (spec_dir, repo_root) resolved for this invocation."""
    global _dirs
    if _dirs is None:
        _dirs = _resolve_dirs()
    return _dirs


def _require_spec(spec_dir: Path) -> None:
    """Exit 1 with guidance if no spec directory exists."""
    if not (spec_dir / "CONTEXT.md").exists():
        print("No spec directory found.")
        print("  Run 'prov init' to scaffold one, or cd into a project with prov/, spec/, or specs/.")
        raise typer.Exit(1)


def _version_callback(value: bool) -> None:
    """Print 'prov <version>' and exit."""
    if not value:
        return
    try:
        v = pkg_version("provenance-cli")
    except PackageNotFoundError:
        v = "dev (package metadata not found)"
    print(f"prov {v}")
    raise typer.Exit()


@app.callback()
def _root(
    version: bool = typer.Option(
        False,
        "--version",
        help="Show the prov version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    global _dirs
    _dirs = _resolve_dirs()


@app.command("orient")
def orient() -> None:
    """Project overview — start every session here."""
    spec_dir, repo_root = _get_dirs()
    _require_spec(spec_dir)
    cmd_orient(spec_dir, repo_root)


@app.command("scope")
def scope(path: str = typer.Argument(".", help="File or directory to look up.")) -> None:
    """Show which spec entries govern a file or directory."""
    spec_dir, repo_root = _get_dirs()
    _require_spec(spec_dir)
    cmd_scope(spec_dir, repo_root, path)


@app.command("context")
def context(slug: str = typer.Argument(..., help="Entry slug.")) -> None:
    """Full entry: statement, provenance, deps, code refs."""
    spec_dir, repo_root = _get_dirs()
    _require_spec(spec_dir)
    cmd_context(spec_dir, repo_root, slug)


@app.command("impact")
def impact(slug: str = typer.Argument(..., help="Entry slug.")) -> None:
    """Blast radius before changing an entry."""
    spec_dir, repo_root = _get_dirs()
    _require_spec(spec_dir)
    cmd_impact(spec_dir, repo_root, slug)


@app.command("find")
def find(
    keywords: Optional[List[str]] = typer.Argument(None, help="Keywords to search for."),
) -> None:
    """Search entries when you don't know the slug."""
    spec_dir, _ = _get_dirs()
    _require_spec(spec_dir)
    cmd_find(spec_dir, " ".join(keywords or []))


@app.command("domain")
def domain(name: str = typer.Argument(..., help="Domain name.")) -> None:
    """Load a full domain."""
    spec_dir, _ = _get_dirs()
    _require_spec(spec_dir)
    cmd_domain(spec_dir, name)


@app.command("validate")
def validate() -> None:
    """Validate the spec index — run before every commit; zero errors only."""
    spec_dir, repo_root = _get_dirs()
    _require_spec(spec_dir)
    raise typer.Exit(cmd_validate(spec_dir, repo_root))


@app.command("check-slug")
def check_slug(slug: str = typer.Argument(..., help="Slug to check.")) -> None:
    """Check whether a slug is available."""
    spec_dir, _ = _get_dirs()
    _require_spec(spec_dir)
    cmd_check_slug(spec_dir, slug)


@app.command("reconcile")
def reconcile(path: str = typer.Argument(".", help="File or directory to scan.")) -> None:
    """Detect code<->spec drift for a path."""
    spec_dir, repo_root = _get_dirs()
    _require_spec(spec_dir)
    cmd_reconcile(spec_dir, repo_root, path)


@app.command("sync", context_settings={"ignore_unknown_options": True})
def sync(
    args: Optional[List[str]] = typer.Argument(
        None, help="[PATH] or a sub-command with its arguments."
    ),
) -> None:
    """Drift report between spec and code, plus patch sub-commands.

    Forms: sync [PATH] | sync mark-implemented SLUG | sync remove-ref SLUG REF |
    sync update-ref SLUG OLD NEW | sync remove-backlink FILE LINE SLUG
    """
    spec_dir, repo_root = _get_dirs()
    _require_spec(spec_dir)
    raise typer.Exit(cmd_sync(spec_dir, repo_root, list(args or [])))


@app.command("rebuild")
def rebuild() -> None:
    """Regenerate the optional .spec/ cache from spec files."""
    spec_dir, _ = _get_dirs()
    _require_spec(spec_dir)
    cmd_rebuild(spec_dir)


@app.command("rebuild-cache", hidden=True)
def rebuild_cache() -> None:
    """Alias for 'rebuild'."""
    rebuild()


@app.command("write", context_settings={"ignore_unknown_options": True})
def write(
    args: Optional[List[str]] = typer.Argument(
        None,
        help="JSON string, path to a .json file, or '--json <string>'; reads stdin if omitted.",
    ),
    yes: bool = typer.Option(False, "--yes", "-y", help="Write without confirmation."),
) -> None:
    """Add entries from JSON input (validates before writing)."""
    spec_dir, repo_root = _get_dirs()
    _require_spec(spec_dir)
    rest = list(args or [])
    if yes:
        rest.append("--yes")
    raise typer.Exit(cmd_write(spec_dir, repo_root, rest))


@app.command("diff")
def diff(ref: str = typer.Argument("HEAD", help="Git ref to compare against.")) -> None:
    """Semantic change manifest vs HEAD or any ref."""
    spec_dir, repo_root = _get_dirs()
    _require_spec(spec_dir)
    cmd_diff(spec_dir, repo_root, ref)


@app.command("init")
def init(
    check: bool = typer.Option(False, "--check", help="Report what would change; write nothing."),
    force: bool = typer.Option(False, "--force", help="Overwrite existing files."),
    no_agents: bool = typer.Option(False, "--no-agents", help="Skip agent assets."),
    no_claude: bool = typer.Option(False, "--no-claude", help="Skip Claude-standard assets."),
    no_open: bool = typer.Option(False, "--no-open", help="Skip open-standard assets."),
) -> None:
    """Scaffold CONTEXT.md and agent assets in a new project."""
    spec_dir, repo_root = _get_dirs()
    raise typer.Exit(
        cmd_init(
            spec_dir,
            repo_root,
            agents=not no_agents,
            claude=not no_claude,
            open_std=not no_open,
            check=check,
            force=force,
        )
    )


def main(argv: list[str] | None = None) -> int:
    """Run the prov CLI; return the exit code."""
    global _dirs
    _dirs = None
    try:
        app(args=argv, prog_name="prov")
    except SystemExit as e:
        code = e.code
        if code is None:
            return 0
        return code if isinstance(code, int) else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
