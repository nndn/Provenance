"""Indexing — nodes by slug, edges, slugs for path, grep spec in code."""
from __future__ import annotations

import re
from pathlib import Path

from prov.model import Edge, Node


_SPEC_COMMENT_RE = re.compile(r"(?:^|[#/*])\s*spec:\s*([^#/*\n]*)", re.I)
_SPEC_BACKLINK_TOKEN_RE = re.compile(
    r"^(?:[CQ]:)?[a-z][a-z0-9]*(?:-[a-z0-9]+)+$"
)


def _parse_spec_backlink_token(token: str) -> str | None:
    """Return a valid spec backlink token with surrounding punctuation removed."""
    token = token.strip().strip("`'\"").rstrip(".,;")
    if not token or not _SPEC_BACKLINK_TOKEN_RE.match(token):
        return None
    return token


def slug_to_full(slug: str, nodes_by_slug: dict[str, Node]) -> str:
    if slug in nodes_by_slug:
        return slug
    if slug.startswith("C:") and slug in nodes_by_slug:
        return slug
    if slug.startswith("Q:") and slug in nodes_by_slug:
        return slug
    return slug


def build_edges(nodes: list[Node]) -> list[Edge]:
    edges: list[Edge] = []
    for n in nodes:
        for dep in n.depends_on:
            edges.append(Edge(from_slug=n.slug, to_slug=dep, type="depends-on"))
        for ref in n.code_refs:
            edges.append(Edge(from_slug=n.slug, to_slug=ref, type="implements"))
    return edges


def nodes_by_slug(nodes: list[Node]) -> dict[str, Node]:
    return {n.slug: n for n in nodes}


def slugs_for_path(
    path_str: str,
    nodes: list[Node],
    refs_by_domain: dict[str, list[str]],
    repo_root: Path,
) -> set[str]:
    """Find slugs governing a code path (direct ~ refs or dir ownership in ## Refs)."""
    slugs: set[str] = set()
    path = Path(path_str)
    if not path.is_absolute():
        path = repo_root / path_str
    try:
        path_str_norm = str(path.relative_to(repo_root)).replace("\\", "/")
    except ValueError:
        path_str_norm = str(path).replace("\\", "/")

    for n in nodes:
        for ref in n.code_refs:
            ref_file = ref.split(":")[0].strip()
            if not ref_file:
                continue
            if path_str_norm == ref_file or path_str_norm.startswith(
                ref_file.rstrip("/") + "/"
            ):
                slugs.add(n.slug)
            elif ref_file.endswith("/") and path_str_norm.startswith(
                ref_file.rstrip("/")
            ):
                slugs.add(n.slug)

    for domain, refs in refs_by_domain.items():
        for r in refs:
            rp = r.strip().rstrip("/")
            if not rp:
                continue
            if path_str_norm == rp or path_str_norm.startswith(rp + "/"):
                for n in nodes:
                    if n.domain == domain:
                        slugs.add(n.slug)

    return slugs


def grep_spec_in_code(
    path_or_dir: Path, repo_root: Path
) -> list[tuple[str, int, str]]:
    """Returns (file, line_no, slug) for spec: backlink comments in code. Excludes .md files."""
    results: list[tuple[str, int, str]] = []
    _skip_dirs = {
        ".git",
        ".spec",
        "__pycache__",
        "node_modules",
        ".venv",
        "venv",
        "prompts",
        "egg-info",
        "dist",
        "build",
        ".cursor",
        ".agents",  # agent skill/workflow documentation — not code
    }
    # Agent config files at repo root that contain spec: examples in documentation
    _skip_filenames = {
        ".cursorrules",
        "AGENTS",
        "AGENTS.md",
        "CLAUDE",
        "CLAUDE.md",
        "GEMINI",
        "GEMINI.md",
        "agent.md",
    }

    def should_skip_file(path: Path) -> bool:
        if any(part in _skip_dirs or part.endswith(".egg-info") for part in path.parts):
            return True
        if path.name in _skip_filenames:
            return True
        return path.suffix.lower() == ".md"

    if path_or_dir.is_file():
        files = [] if should_skip_file(path_or_dir) else [path_or_dir]
    else:
        files = []
        try:
            all_entries = list(path_or_dir.rglob("*"))
        except (PermissionError, OSError):
            all_entries = []
        for f in all_entries:
            # Skip entries whose path contains a skip dir (check before is_file to avoid
            # PermissionError on broken symlinks inside node_modules etc.)
            if should_skip_file(f):
                continue
            try:
                if not f.is_file():
                    continue
            except (PermissionError, OSError):
                continue
            files.append(f)

    for f in files:
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        rel = str(f.relative_to(repo_root)) if f.is_relative_to(repo_root) else str(f)
        for i, line in enumerate(text.splitlines(), 1):
            for m in _SPEC_COMMENT_RE.finditer(line):
                for part in m.group(1).replace(",", " ").split():
                    slug = _parse_spec_backlink_token(part)
                    if slug:
                        results.append((rel, i, slug))
    return results
