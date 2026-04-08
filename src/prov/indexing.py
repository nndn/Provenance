"""Indexing — nodes by slug, edges, slugs for path, grep spec in code."""
from __future__ import annotations

import re
from pathlib import Path

from prov.model import Edge, Node


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
    spec_re = re.compile(r"(?:^|[#/*\s])spec:\s*([a-z][a-z0-9\-,\s]*)", re.I)
    slug_re = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)+$")
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
    _skip_filenames = {".cursorrules", "agent.md", "GEMINI.md", "CLAUDE.md", "AGENTS.md"}

    if path_or_dir.is_file():
        files = [path_or_dir] if path_or_dir.suffix.lower() != ".md" else []
    else:
        files = []
        try:
            all_entries = list(path_or_dir.rglob("*"))
        except (PermissionError, OSError):
            all_entries = []
        for f in all_entries:
            # Skip entries whose path contains a skip dir (check before is_file to avoid
            # PermissionError on broken symlinks inside node_modules etc.)
            if any(
                part in _skip_dirs or part.endswith(".egg-info") for part in f.parts
            ):
                continue
            if f.name in _skip_filenames:
                continue
            try:
                if not f.is_file():
                    continue
            except (PermissionError, OSError):
                continue
            if f.suffix.lower() == ".md":
                continue
            files.append(f)

    for f in files:
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        rel = str(f.relative_to(repo_root)) if f.is_relative_to(repo_root) else str(f)
        for i, line in enumerate(text.splitlines(), 1):
            for m in spec_re.finditer(line):
                for part in m.group(1).replace(",", " ").split():
                    slug = part.strip().rstrip(".")
                    if slug and slug_re.match(slug):
                        results.append((rel, i, slug))
    return results
