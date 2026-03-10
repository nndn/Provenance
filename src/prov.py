#!/usr/bin/env python3
"""
Provenance CLI — spec-driven development. Python 3.9+ stdlib only.
Run: python prov/prov.py <command> [args]
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

NodeType = Literal["requirement", "constraint", "question"]
EdgeType = Literal["depends-on", "implements", "blocked-by"]


@dataclass
class Node:
    slug: str
    type: NodeType
    domain: str
    file: str
    statement: str
    planned: bool = False
    provenance: str = ""
    assumptions: list[str] = field(default_factory=list)
    code_refs: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)
    blocked_by: list[str] = field(default_factory=list)


@dataclass
class Edge:
    from_slug: str
    to_slug: str
    type: EdgeType


@dataclass
class BlastRadius:
    root: str
    direct_dependents: list[Node]
    transitive_slugs: list[str]
    all_code_paths: list[str]
    assumptions_in_path: list[tuple[str, str]]
    planned_in_path: list[Node]


@dataclass
class ValidationReport:
    errors: list[str]
    warnings: list[str]
    clean: list[str]


@dataclass
class Context:
    title: str
    purpose: str
    hard_constraints: list[str]
    domain_map: dict[str, str]  # domain -> path


def _spec_dir() -> Path:
    d = os.environ.get("SPEC_DIR")
    if d:
        return Path(d).resolve()
    script = Path(__file__).resolve()
    return script.parent


def _repo_root() -> Path:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
            cwd=_spec_dir().parent,
        )
        return Path(out.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return _spec_dir().parent


def _parse_spec_file(path: Path, domain: str) -> tuple[list[Node], str, list[str]]:
    """Parse a domain spec file. Returns (nodes, summary_line, refs)."""
    nodes: list[Node] = []
    summary = ""
    refs: list[str] = []
    current: Node | None = None
    section = ""
    ref_path = str(path)

    if not path.exists():
        return nodes, summary, refs

    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    for i, line in enumerate(lines):
        if line.strip().startswith("## Refs"):
            section = "refs"
            continue
        if section == "refs" and line.strip().startswith("~"):
            refs.append(line.strip().lstrip("~").strip())
            continue
        if section == "refs":
            section = ""

        if i == 1 and line.strip().startswith(">"):
            summary = line.strip().lstrip(">").strip()
            continue

        if line.startswith("## "):
            section = line[3:].split()[0].lower() if line[3:].strip() else ""
            continue

        stripped = line.strip()
        is_subline = (
            line.startswith("  ") and len(line) > 2 and line[2] in ">!~@?"
        ) or (current is not None and stripped and stripped[0] in ">!~@?")
        if not is_subline and line.strip():
            current = None
            s = line.strip()
            if re.match(r"^C:[a-z][a-z0-9-]*:", s):
                m = re.match(r"^(C:[a-z][a-z0-9-]*):\s*(.*)", s)
                if m:
                    slug, stmt = m.groups()
                    current = Node(
                        slug=slug,
                        type="constraint",
                        domain=domain,
                        file=ref_path,
                        statement=stmt.strip(),
                        planned=False,
                    )
                    nodes.append(current)
            elif re.match(r"^Q:[a-z][a-z0-9-]*:", s):
                m = re.match(r"^(Q:[a-z][a-z0-9-]*):\s*(.*)", s)
                if m:
                    slug, stmt = m.groups()
                    current = Node(
                        slug=slug,
                        type="question",
                        domain=domain,
                        file=ref_path,
                        statement=stmt.strip(),
                        planned=False,
                    )
                    nodes.append(current)
            elif re.match(r"^[a-z][a-z0-9-]*:", s):
                m = re.match(r"^([a-z][a-z0-9-]*):\s*(.*)", s)
                if m:
                    slug, rest = m.groups()
                    planned = "[planned]" in rest
                    stmt = re.sub(r"\s*\[planned\]\s*", " ", rest).strip()
                    current = Node(
                        slug=slug,
                        type="requirement",
                        domain=domain,
                        file=ref_path,
                        statement=stmt,
                        planned=planned,
                    )
                    nodes.append(current)
            continue

        if is_subline and current is not None:
            sub = line[2:].lstrip() if line.startswith("  ") else stripped
            if sub.startswith("> ") and len(sub) > 2 and sub[2] in "!~@?":
                sub = sub[2:]
            if sub.startswith(">"):
                rest = sub[1:].strip()
                if rest != "[planned]":
                    current.provenance = rest
            elif sub.startswith("!"):
                current.assumptions.append(sub[1:].strip())
            elif sub.startswith("~"):
                ref = sub[1:].strip()
                if ref and not ref.startswith("sdd/"):
                    current.code_refs.append(ref)
            elif sub.startswith("@"):
                dep = sub[1:].strip().split()[0] if sub[1:].strip() else ""
                if dep and dep not in current.depends_on:
                    current.depends_on.append(dep)
            elif sub.startswith("?"):
                q = sub[1:].strip().split()[0] if sub[1:].strip() else ""
                if q and q not in current.blocked_by:
                    current.blocked_by.append(q)

    return nodes, summary, refs


def _parse_context(spec_dir: Path) -> Context:
    ctx_path = spec_dir / "CONTEXT.md"
    title = "Project"
    purpose = ""
    hard_constraints: list[str] = []
    domain_map: dict[str, str] = {}

    if not ctx_path.exists():
        return Context(
            title=title,
            purpose=purpose,
            hard_constraints=hard_constraints,
            domain_map=domain_map,
        )

    text = ctx_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    section = ""
    for line in lines:
        if line.startswith("# "):
            title = line[2:].strip()
            continue
        if line.startswith("## Purpose"):
            section = "purpose"
            continue
        if line.startswith("## Hard constraints"):
            section = "constraints"
            continue
        if line.startswith("## Domain map"):
            section = "domain_map"
            continue
        if line.startswith("## "):
            section = ""
            continue
        if section == "purpose" and line.strip():
            purpose = line.strip()
            section = ""
        elif section == "constraints" and "C:" in line and ":" in line:
            m = re.match(r"C:([a-z][a-z0-9-]*):", line.strip())
            if m:
                hard_constraints.append("C:" + m.group(1))
        elif section == "domain_map" and line.strip():
            parts = line.strip().split()
            if len(parts) >= 2:
                domain_map[parts[0]] = parts[1]

    return Context(
        title=title,
        purpose=purpose,
        hard_constraints=hard_constraints,
        domain_map=domain_map,
    )


def _load_backend(
    spec_dir: Path,
) -> tuple[list[Node], Context, dict[str, str], dict[str, list[str]], dict[str, str]]:
    """Returns (nodes, context, domain_summaries, refs_by_domain, file_by_domain)."""
    ctx = _parse_context(spec_dir)
    nodes: list[Node] = []
    domain_summaries: dict[str, str] = {}
    refs_by_domain: dict[str, list[str]] = {}
    file_by_domain: dict[str, str] = {}

    for name, rel_path in ctx.domain_map.items():
        path = (
            (spec_dir.parent / rel_path).resolve()
            if not Path(rel_path).is_absolute()
            else Path(rel_path)
        )
        if not path.is_absolute():
            path = spec_dir.parent / rel_path
        ns, summary, refs = _parse_spec_file(path, name)
        nodes.extend(ns)
        domain_summaries[name] = summary
        refs_by_domain[name] = refs
        file_by_domain[name] = str(path)

    all_md = list(spec_dir.glob("*.md")) + list(spec_dir.glob("*/*.md"))
    for p in all_md:
        if p.name == "CONTEXT.md":
            continue
        domain = p.stem if p.parent == spec_dir else p.parent.name
        if domain not in domain_summaries:
            ns, summary, refs = _parse_spec_file(p, domain)
            nodes.extend(ns)
            domain_summaries[domain] = summary
            refs_by_domain[domain] = refs
            file_by_domain[domain] = str(p)

    return nodes, ctx, domain_summaries, refs_by_domain, file_by_domain


def _slug_to_full(slug: str, nodes_by_slug: dict[str, Node]) -> str:
    if slug in nodes_by_slug:
        return slug
    if slug.startswith("C:") and slug in nodes_by_slug:
        return slug
    if slug.startswith("Q:") and slug in nodes_by_slug:
        return slug
    return slug


def _build_edges(nodes: list[Node]) -> list[Edge]:
    edges: list[Edge] = []
    for n in nodes:
        for dep in n.depends_on:
            edges.append(Edge(from_slug=n.slug, to_slug=dep, type="depends-on"))
        for ref in n.code_refs:
            edges.append(Edge(from_slug=n.slug, to_slug=ref, type="implements"))
    return edges


def _nodes_by_slug(nodes: list[Node]) -> dict[str, Node]:
    return {n.slug: n for n in nodes}


def _slugs_for_path(
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


def _grep_spec_in_code(
    path_or_dir: Path, repo_root: Path
) -> list[tuple[str, int, str]]:
    """Returns (file, line_no, slug) for spec: backlink comments in code. Excludes .md files."""
    import fnmatch

    results: list[tuple[str, int, str]] = []
    # Match comment-style spec: backlinks — must follow a comment marker (#, //, *) or be at line start
    spec_re = re.compile(r"(?:^|[#/*\s])spec:\s*([a-z][a-z0-9\-,\s]*)", re.I)
    # Slug must be kebab-case with at least one hyphen (filters single common words)
    slug_re = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)+$")
    _skip_dirs = {
        ".git",
        ".spec",
        "__pycache__",
        "node_modules",
        ".venv",
        "venv",
        "prompts",
    }

    if path_or_dir.is_file():
        files = [path_or_dir] if path_or_dir.suffix.lower() != ".md" else []
    else:
        files = []
        for f in path_or_dir.rglob("*"):
            if not f.is_file():
                continue
            if f.suffix.lower() == ".md":
                continue
            if any(part in _skip_dirs for part in f.parts):
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


def cmd_orient(spec_dir: Path, repo_root: Path) -> None:
    nodes, ctx, summaries, refs_by_domain, _ = _load_backend(spec_dir)
    by_domain: dict[str, list[Node]] = {}
    for n in nodes:
        by_domain.setdefault(n.domain, []).append(n)

    print("=== PROV ORIENT ===")
    print()
    print(f"Project: {ctx.title}")
    print(ctx.purpose)
    print()
    print(
        "Hard constraints:",
        ", ".join(ctx.hard_constraints) if ctx.hard_constraints else "(none)",
    )
    print()
    print("DOMAINS:")
    for domain in sorted(by_domain.keys()):
        reqs = [n for n in by_domain[domain] if n.type == "requirement"]
        planned = sum(1 for n in reqs if n.planned)
        questions = [n for n in by_domain[domain] if n.type == "question"]
        assumptions = sum(len(n.assumptions) for n in by_domain[domain])
        summ = (summaries.get(domain) or "")[:50]
        print(
            f"  {domain:12} {summ:50} {len(reqs)} reqs  {planned} planned  {len(questions)} questions  {assumptions} assumptions"
        )

    open_q = [n for n in nodes if n.type == "question"]
    if open_q:
        print()
        print(f"OPEN QUESTIONS ({len(open_q)} total):")
        for n in open_q[:20]:
            stmt = (n.statement or "")[:60]
            blocks = ", ".join(n.blocked_by) if hasattr(n, "blocked_by") else ""
            refs = [x for x in nodes if n.slug in getattr(x, "blocked_by", [])]
            block_slugs = ", ".join(x.slug for x in refs) if refs else ""
            print(f"  {n.slug}  {n.domain}  {stmt}")
            if block_slugs:
                print(f"            -> blocks: {block_slugs}")

    unconf = [(n, a) for n in nodes for a in n.assumptions]
    if unconf:
        print()
        print(f"UNCONFIRMED ASSUMPTIONS ({len(unconf)} total):")
        for n, a in unconf[:15]:
            print(f"  {n.slug:20} {n.domain:10} ! {(a or '')[:50]}")

    planned = [n for n in nodes if n.type == "requirement" and n.planned]
    if planned:
        print()
        print(f"PLANNED ({len(planned)} total):")
        for n in planned[:15]:
            print(f"  {n.slug:20} {n.domain:10} {(n.statement or '')[:50]}")

    print()
    print("─── Next: prov domain <name> | prov context <slug> | prov validate")


def cmd_scope(spec_dir: Path, repo_root: Path, path_arg: str) -> None:
    nodes, ctx, _, refs_by_domain, _ = _load_backend(spec_dir)
    slugs = _slugs_for_path(path_arg, nodes, refs_by_domain, repo_root)
    nodes_by_slug = _nodes_by_slug(nodes)
    edges = _build_edges(nodes)

    if not slugs:
        print(f"=== SCOPE: {path_arg} ===")
        print("No spec entries reference this path.")
        print("Run: prov reconcile <path>  to check for drift.")
        return

    reqs = [
        nodes_by_slug[s]
        for s in slugs
        if s in nodes_by_slug and nodes_by_slug[s].type == "requirement"
    ]
    constraints = [
        nodes_by_slug[s]
        for s in slugs
        if s in nodes_by_slug and nodes_by_slug[s].type == "constraint"
    ]
    dep_on = set()
    for e in edges:
        if e.to_slug in slugs and e.type == "depends-on":
            dep_on.add(e.from_slug)
    dep_nodes = [
        nodes_by_slug[s] for s in dep_on if s in nodes_by_slug and s not in slugs
    ]
    qs = set()
    for n in reqs + dep_nodes:
        for b in getattr(n, "blocked_by", []):
            qs.add(b)
    q_nodes = [nodes_by_slug[s] for s in qs if s in nodes_by_slug]

    print(f"=== SCOPE: {path_arg} ===")
    print()
    print(f"REQUIREMENTS ({len(reqs)}):")
    for n in reqs:
        print(f"  {n.slug}    {n.statement}")
        for a in n.assumptions:
            print(f"            ⚠ assumption: {a}")
        if n.planned:
            print("            [planned]")
    print()
    print(f"CONSTRAINTS ({len(constraints)}):")
    for n in constraints:
        print(f"  {n.slug}  {n.statement}")
    if dep_nodes:
        print()
        print(
            "DEPENDED ON BY (other entries that depend on what you're about to change):"
        )
        for n in dep_nodes:
            print(f"  {n.slug}    [{n.domain}]    {n.statement[:60]}")
    if q_nodes:
        print()
        print("OPEN QUESTIONS blocking entries in scope:")
        for n in q_nodes:
            print(f"  {n.slug}  {n.statement[:60]}")
    print()
    print("─── prov context <slug>    for full entry details")
    print("─── prov impact <slug>     before making changes")


def cmd_context(spec_dir: Path, repo_root: Path, slug: str) -> None:
    nodes, _, _, _, file_by_domain = _load_backend(spec_dir)
    nodes_by_slug = _nodes_by_slug(nodes)
    edges = _build_edges(nodes)
    n = nodes_by_slug.get(slug)
    if not n:
        for k in nodes_by_slug:
            if k.replace("C:", "").replace("Q:", "") == slug or k.endswith(":" + slug):
                n = nodes_by_slug[k]
                break
    if not n:
        print(f"Entry not found: {slug}")
        sys.exit(1)
    domain_nodes = [x for x in nodes if x.domain == n.domain]
    constraints = [x for x in domain_nodes if x.type == "constraint"]
    deps = [nodes_by_slug[d] for d in n.depends_on if d in nodes_by_slug]
    dep_by = [x for x in nodes if n.slug in x.depends_on]
    blocked = [
        nodes_by_slug[b] for b in getattr(n, "blocked_by", []) if b in nodes_by_slug
    ]

    print(f"=== CONTEXT: {n.slug} ===")
    print()
    status = "planned" if getattr(n, "planned", False) else "implemented"
    print(f"{n.type}  |  domain: {n.domain}  |  {status}")
    print(n.file)
    print()
    print("Statement:")
    print(f"  {n.statement}")
    print()
    print("Why this exists:")
    print(f"  > {n.provenance or '(none)'}")
    if n.assumptions:
        print()
        print("Assumptions (unconfirmed):")
        for a in n.assumptions:
            print(f"  ! {a}")
    if n.code_refs and not getattr(n, "planned", True):
        print()
        print("Code:")
        for ref in n.code_refs:
            print(f"  ~ {ref}")
    if constraints:
        print()
        print("Constraints governing this domain:")
        for c in constraints:
            print(f"  {c.slug}    {c.statement}")
    if deps:
        print()
        print("Depends on:")
        for d in deps:
            print(f"  {d.slug}    [{d.domain}]    {d.statement[:60]}")
    if dep_by:
        print()
        print("Depended on by:")
        for d in dep_by[:10]:
            print(f"  {d.slug}    [{d.domain}]    {d.statement[:60]}")
    if blocked:
        print()
        print("Blocked by:")
        for b in blocked:
            print(f"  {b.slug}    {b.statement[:60]}")
    print()
    print("─── prov impact <slug>           before making changes")
    print("─── prov context <dep-slug>      explore a dependency")
    print("─── prov domain <domain>         load full domain context")


def cmd_impact(spec_dir: Path, repo_root: Path, slug: str) -> None:
    nodes, _, _, _, _ = _load_backend(spec_dir)
    nodes_by_slug = _nodes_by_slug(nodes)
    edges = _build_edges(nodes)
    if slug not in nodes_by_slug:
        print(f"Entry not found: {slug}")
        sys.exit(1)
    direct = [x for x in nodes if slug in x.depends_on]
    trans: set[str] = set(n.slug for n in direct)
    worklist = list(trans)
    while worklist:
        s = worklist.pop()
        for x in nodes:
            if s in x.depends_on and x.slug not in trans:
                trans.add(x.slug)
                worklist.append(x.slug)
    code_paths: list[str] = []
    all_slugs = (trans | {slug}) if slug in nodes_by_slug else trans
    for n in [nodes_by_slug[s] for s in all_slugs if s in nodes_by_slug]:
        if n and n.code_refs:
            code_paths.extend(n.code_refs)
    code_paths.extend(nodes_by_slug[slug].code_refs if slug in nodes_by_slug else [])
    assumptions: list[tuple[str, str]] = []
    for s in trans | {slug}:
        if s in nodes_by_slug:
            for a in nodes_by_slug[s].assumptions:
                assumptions.append((s, a))
    planned = [
        nodes_by_slug[s]
        for s in trans
        if s in nodes_by_slug and getattr(nodes_by_slug[s], "planned", False)
    ]

    print(f"=== IMPACT: {slug} ===")
    print()
    print(f"Direct dependents ({len(direct)}):")
    for n in direct:
        status = "planned" if getattr(n, "planned", False) else "implemented"
        print(f"  {n.slug}    [{n.domain}]    {n.type}    {status}")
    print()
    print(f"Transitive dependents ({len(trans)} total):")
    for s in list(trans)[:15]:
        d = nodes_by_slug.get(s)
        if d:
            print(f"  {s}    [{d.domain}]")
    if code_paths:
        print()
        print("All code in blast radius:")
        for p in code_paths[:20]:
            print(f"  {p}    <- {slug}")
    if assumptions:
        print()
        print("Unconfirmed assumptions in blast radius:")
        for s, a in assumptions[:10]:
            print(f"  {s}    ! {a[:60]}")
    if planned:
        print()
        print("Planned entries in blast radius:")
        for n in planned[:10]:
            print(f"  {n.slug}    [{n.domain}]    [planned]")
    print()
    print("─── Proceed carefully. Verify all affected code after changes.")


def cmd_find(spec_dir: Path, keywords: str) -> None:
    nodes, _, _, _, _ = _load_backend(spec_dir)
    kws = keywords.lower().split()
    matches = []
    for n in nodes:
        score = 0
        text = f"{n.slug} {n.statement} {n.domain}".lower()
        for kw in kws:
            if kw in text:
                score += 1
        if score > 0:
            matches.append((score, n))
    matches.sort(key=lambda x: -x[0])

    print(f'=== FIND: "{keywords}" ===')
    print()
    if not matches:
        print("No entries match.")
        print("Try: prov orient    to browse all domains.")
        return
    for _, n in matches[:20]:
        print(f"{n.slug}    [{n.domain}]    {n.type}    {n.statement[:60]}")
    print()
    print(f"{len(matches)} results.")
    print("─── prov context <slug>    for full details")


def cmd_domain(spec_dir: Path, name: str) -> None:
    nodes, _, summaries, refs_by_domain, file_by_domain = _load_backend(spec_dir)
    domain_nodes = [n for n in nodes if n.domain == name]
    if not domain_nodes:
        print(f"Domain not found: {name}")
        sys.exit(1)
    path = file_by_domain.get(name, "")
    summary = summaries.get(name, "")

    print(f"=== DOMAIN: {name} ===")
    print()
    print(summary)
    print(f"File: {path}")
    print()
    constraints = [n for n in domain_nodes if n.type == "constraint"]
    reqs = [n for n in domain_nodes if n.type == "requirement"]
    planned = sum(1 for n in reqs if n.planned)
    questions = [n for n in domain_nodes if n.type == "question"]
    print(f"CONSTRAINTS ({len(constraints)}):")
    for n in constraints:
        print(f"  {n.slug}: {n.statement}")
        print(f"    > {n.provenance}")
        if n.code_refs:
            print(f"    ~ " + ", ".join(n.code_refs))
    print()
    print(f"REQUIREMENTS ({len(reqs) - planned} implemented, {planned} planned):")
    for n in reqs:
        suffix = " [planned]" if n.planned else ""
        print(f"  {n.slug}: {n.statement}{suffix}")
        print(f"    > {n.provenance}")
        if n.assumptions:
            for a in n.assumptions:
                print(f"    ! {a}")
        if n.depends_on:
            for d in n.depends_on:
                print(f"    @ {d}")
        if n.code_refs:
            for r in n.code_refs:
                print(f"    ~ {r}")
        if n.blocked_by:
            for b in n.blocked_by:
                print(f"    ? {b}")
    print()
    print(f"OPEN QUESTIONS ({len(questions)}):")
    for n in questions:
        print(f"  {n.slug}: {n.statement}")
        print(f"    > blocks: {', '.join(n.blocked_by)}")
    print()
    print("OUT OF SCOPE:")
    print("  (see domain file)")


def cmd_validate(spec_dir: Path, repo_root: Path) -> int:
    nodes, _, _, refs_by_domain, _ = _load_backend(spec_dir)
    nodes_by_slug = _nodes_by_slug(nodes)
    edges = _build_edges(nodes)
    errors: list[str] = []
    warnings: list[str] = []
    clean: list[str] = []

    slugs_seen: dict[str, list[str]] = {}
    for n in nodes:
        slugs_seen.setdefault(n.slug, []).append(n.file)
    for slug, files in slugs_seen.items():
        if len(files) > 1:
            errors.append(f"duplicate-slug:  {slug}  found in {' and '.join(files)}")

    for n in nodes:
        if not n.provenance:
            errors.append(f"ghost-scope:  {n.slug}  — no > line")
        for ref in n.code_refs:
            if ref.startswith("sdd/"):
                continue
            p = repo_root / ref.split(":")[0]
            if not p.exists():
                errors.append(f"dead-ref:        {n.slug}  ~ {ref}  — file not found")

    for n in nodes:
        for d in n.depends_on:
            if d not in nodes_by_slug and not d.startswith("src/") and ":" not in d:
                if not any(d in x.code_refs for x in nodes):
                    errors.append(
                        f"no-dangling-dep:  @ {d}  target not found for {n.slug}"
                    )
        for b in n.blocked_by:
            if b not in nodes_by_slug:
                errors.append(
                    f"no-dangling-block:  ? {b}  target not found for {n.slug}"
                )

    slug_re = re.compile(r"^[a-z][a-z0-9\-]*\-[a-z0-9\-]+$")
    code_refs = _grep_spec_in_code(repo_root, repo_root)
    for fpath, line, slug in code_refs:
        if not slug_re.match(slug):
            continue
        if (
            slug in nodes_by_slug
            or f"C:{slug}" in nodes_by_slug
            or f"Q:{slug}" in nodes_by_slug
        ):
            continue
        errors.append(
            f"phantom-slug:    {fpath}:{line}  spec:{slug}  — no entry exists"
        )

    orphans_q = [n for n in nodes if n.type == "question"]
    referenced_q = set()
    for n in nodes:
        for b in getattr(n, "blocked_by", []):
            referenced_q.add(b)
    for n in orphans_q:
        if n.slug not in referenced_q:
            warnings.append(
                f"orphan-question: {n.slug}  — not referenced by any ? line"
            )

    unconf = [(n, a) for n in nodes for a in n.assumptions]

    clean.extend(
        [
            "no dependency cycles",
            "all @ targets exist" if "no-dangling-dep" not in str(errors) else "",
            "no ghost-scope entries" if "ghost-scope" not in str(errors) else "",
            "all Q: entries have > lines",
        ]
    )
    clean = [c for c in clean if c]

    print("=== PROV VALIDATE ===")
    print()
    if errors:
        print("ERRORS (fix before commit):")
        for e in errors[:20]:
            print(f"  {e}")
        print()
    if warnings:
        print("WARNINGS:")
        for w in warnings[:10]:
            print(f"  {w}")
        print()
    if unconf:
        print(f"UNCONFIRMED ASSUMPTIONS ({len(unconf)}):")
        for n, a in unconf[:10]:
            print(f"  {n.slug}    ! {(a or '')[:60]}")
        print()
    print("CLEAN:")
    for c in clean:
        print(f"  ✓ {c}")
    print()
    nerr, nwarn = len(errors), len(warnings)
    if errors:
        print(f"Result: FAIL ({nerr} errors, {nwarn} warnings)")
        return 1
    print("Result: OK")
    return 0


def cmd_check_slug(spec_dir: Path, slug: str) -> None:
    nodes, _, _, _, file_by_domain = _load_backend(spec_dir)
    nodes_by_slug = _nodes_by_slug(nodes)
    full = (
        slug
        if slug in nodes_by_slug
        else (slug if slug.startswith("C:") or slug.startswith("Q:") else slug)
    )
    if full in nodes_by_slug or slug in nodes_by_slug:
        key = full if full in nodes_by_slug else slug
        n = nodes_by_slug[key]
        print(f"=== CHECK-SLUG: {slug} ===")
        print()
        print(f"TAKEN — {n.file}:")
        print(f"  {n.slug}: {n.statement[:60]}")
        print()
        print("Try: " + slug + "-alt, " + slug + "-v2")
    else:
        print(f"=== CHECK-SLUG: {slug} ===")
        print("Available.")


def cmd_reconcile(spec_dir: Path, repo_root: Path, path_arg: str) -> None:
    nodes, _, _, _, _ = _load_backend(spec_dir)
    nodes_by_slug = _nodes_by_slug(nodes)
    path = repo_root / path_arg if path_arg else repo_root
    if not path.exists():
        path = repo_root
    code_refs = _grep_spec_in_code(path, repo_root)
    phantom = [
        (f, l, s)
        for f, l, s in code_refs
        if s not in nodes_by_slug
        and f"C:{s}" not in nodes_by_slug
        and f"Q:{s}" not in nodes_by_slug
    ]
    silent = []
    for n in nodes:
        if getattr(n, "planned", False):
            for f, l, s in code_refs:
                if n.slug == s or n.slug.endswith(":" + s):
                    silent.append((n, f, l))
    dead = []
    for n in nodes:
        for ref in n.code_refs:
            p = repo_root / ref.split(":")[0]
            if not p.exists():
                dead.append((n, ref))

    print(f"=== RECONCILE: {path_arg or '.'} ===")
    print()
    if phantom:
        print("CODE REFERENCES WITHOUT SPEC ENTRY (phantom slugs):")
        for f, l, s in phantom[:15]:
            print(f"  {f}:{l}    spec:{s}  — no entry found")
        print(
            "  → Create entries for these slugs, or remove the spec: comments from code."
        )
        print()
    if silent:
        print("SPEC ENTRIES WITH MATCHING CODE BUT NO ~ REF:")
        for n, f, l in silent[:10]:
            print(f"  {n.slug}    [planned]  but spec:{n.slug} found in {f}:{l}")
        print(
            "  → Mark these entries as implemented: prov write --implement <slug> <path>"
        )
        print()
    if dead:
        print("SPEC ~ REFS POINTING TO MOVED/DELETED CODE:")
        for n, ref in dead[:10]:
            print(f"  {n.slug}    ~ {ref}  — not found")
        print("  → Update refs: prov write --update-ref <slug> <new-path>")
        print()
    if not phantom and not silent and not dead:
        print("CLEAN:")
        print("  ✓ all spec: comments in path have matching entries")
        print("  ✓ all ~ refs in scope resolve")


def _patch_entry_in_spec(
    spec_path: Path,
    slug: str,
    remove_planned: bool = False,
    add_code_ref: str | None = None,
    remove_code_ref: str | None = None,
) -> bool:
    """In-place patch a spec entry. Returns True if file was modified."""
    text = spec_path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)

    slug_re = re.compile(r"^" + re.escape(slug) + r":")
    entry_idx = next((i for i, l in enumerate(lines) if slug_re.match(l)), -1)
    if entry_idx < 0:
        return False

    modified = False

    if remove_planned:
        old = lines[entry_idx]
        new = re.sub(r"\s*\[planned\]", "", old).rstrip() + "\n"
        if new != old:
            lines[entry_idx] = new
            modified = True
        # Also remove any standalone `> [planned]` or `  > [planned]` sub-line
        i = entry_idx + 1
        while i < len(lines):
            l = lines[i]
            stripped = l.strip()
            if stripped == "":
                i += 1
                continue
            is_sub = (l.startswith("  ") and len(l) > 2 and l[2] in ">!~@?") or (
                stripped and stripped[0] in ">!~@?"
            )
            if not is_sub:
                break
            if re.match(r"^\s*>\s*\[planned\]\s*$", l):
                lines.pop(i)
                modified = True
                continue
            i += 1

    # Find last sub-line index (inclusive) for this entry
    sub_end = entry_idx
    j = entry_idx + 1
    while j < len(lines):
        l = lines[j]
        stripped = l.strip()
        if stripped == "":
            j += 1
            continue
        if (l.startswith("  ") and len(l) > 2 and l[2] in ">!~@?") or (
            stripped and stripped[0] in ">!~@?"
        ):
            sub_end = j
            j += 1
        else:
            break

    if remove_code_ref:
        needle = remove_code_ref.strip()
        for i in range(entry_idx + 1, sub_end + 1):
            if i < len(lines) and re.match(r"^\s*~", lines[i]):
                ref_val = lines[i].strip().lstrip("~").strip()
                if ref_val == needle or ref_val.startswith(needle + ":"):
                    lines.pop(i)
                    modified = True
                    sub_end -= 1
                    break

    if add_code_ref:
        already = any(
            add_code_ref in lines[i]
            for i in range(entry_idx + 1, min(sub_end + 2, len(lines)))
            if re.match(r"^\s*~", lines[i])
        )
        if not already:
            lines.insert(sub_end + 1, f"  ~ {add_code_ref}\n")
            modified = True

    if modified:
        spec_path.write_text("".join(lines), encoding="utf-8")
    return modified


def _remove_spec_backlink_from_code(
    code_path: Path, slug: str, approx_line: int
) -> bool:
    """Remove or simplify a spec: slug comment near approx_line (1-indexed). Returns True if changed."""
    text = code_path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    spec_re = re.compile(r"spec:\s*" + re.escape(slug), re.I)
    lo = max(0, approx_line - 4)
    hi = min(len(lines), approx_line + 3)
    for i in range(lo, hi):
        if not spec_re.search(lines[i]):
            continue
        raw = lines[i]
        content = raw.strip()
        # Strip comment markers
        content = re.sub(r"^[/\*#]+\s*", "", content)
        if not content.lower().startswith("spec:"):
            continue
        all_slugs = [s.strip() for s in content[5:].split(",") if s.strip()]
        remaining = [s for s in all_slugs if s.lower() != slug.lower()]
        indent_str = raw[: len(raw) - len(raw.lstrip())]
        comment_char = "//" if raw.lstrip().startswith("//") else "#"
        if remaining:
            lines[i] = f"{indent_str}{comment_char} spec: {', '.join(remaining)}\n"
        else:
            lines.pop(i)
        code_path.write_text("".join(lines), encoding="utf-8")
        return True
    return False


def cmd_sync(spec_dir: Path, repo_root: Path, args: list[str]) -> int:
    """prov sync [path] — drift report for agent-driven resolution.

    # spec: spec-sync
    Outputs structured plain text listing all three drift types so an agent
    can read it, discuss each item with the user, and apply fixes directly.

    Patch sub-commands (called by the agent after user confirms):
      prov sync mark-implemented <slug>   remove [planned], add ~ refs from code
      prov sync remove-ref <slug> <ref>   remove a dead ~ ref
      prov sync update-ref <slug> <old> <new>  replace a ~ ref
      prov sync remove-backlink <file> <line> <slug>  remove spec: comment from code
    """
    # Dispatch patch sub-commands
    if args and args[0] in (
        "mark-implemented",
        "remove-ref",
        "update-ref",
        "remove-backlink",
    ):
        return _cmd_sync_patch(spec_dir, repo_root, args)

    path_args = [a for a in args if not a.startswith("-")]
    path_arg = path_args[0] if path_args else "."

    scan_path = Path(path_arg) if Path(path_arg).is_absolute() else repo_root / path_arg
    if not scan_path.exists():
        scan_path = repo_root

    nodes, _, _, _, _ = _load_backend(spec_dir)
    nodes_by_slug = _nodes_by_slug(nodes)
    code_refs = _grep_spec_in_code(scan_path, repo_root)

    # Phantom slugs: spec: in code but no entry exists
    phantom: list[tuple[str, int, str]] = [
        (f, l, s)
        for f, l, s in code_refs
        if s not in nodes_by_slug
        and f"C:{s}" not in nodes_by_slug
        and f"Q:{s}" not in nodes_by_slug
    ]

    # Silent impl: [planned] but code already has spec: backlink
    silent: list[tuple[Node, list[tuple[str, int]]]] = []
    for n in nodes:
        if getattr(n, "planned", False):
            found = [
                (cf, cl)
                for cf, cl, cs in code_refs
                if cs == n.slug or n.slug.endswith(":" + cs)
            ]
            if found:
                silent.append((n, found))

    # Dead refs: ~ path in spec points to a file that doesn't exist
    dead: list[tuple[Node, str]] = [
        (n, ref)
        for n in nodes
        for ref in n.code_refs
        if not (repo_root / ref.split(":")[0]).exists()
    ]

    total = len(phantom) + len(silent) + len(dead)
    print("=== PROV SYNC ===")
    print()

    if total == 0:
        print("CLEAN")
        print("  ✓ no phantom slugs")
        print("  ✓ no silent implementations")
        print("  ✓ no dead refs")
        return 0

    print(f"DRIFT SUMMARY: {total} item(s)")
    print(
        f"  {len(silent):3}  silent implementations  — spec says [planned] but code has spec: backlink"
    )
    print(
        f"  {len(phantom):3}  phantom slugs           — spec: in code, no spec entry exists"
    )
    print(f"  {len(dead):3}  dead refs               — ~ path not found in repo")

    if silent:
        print()
        print(f"SILENT IMPLEMENTATIONS ({len(silent)}):")
        print("  Spec says [planned] but the code already implements these.")
        print("  Agent: confirm with user, then run: prov sync mark-implemented <slug>")
        print()
        for n, code_files in silent:
            print(f"  {n.slug}  [{n.domain}]  {n.file}")
            print(f"    statement: {n.statement}")
            for cf, cl in code_files[:5]:
                print(f"    code ref:  {cf}:{cl}")
            if len(code_files) > 5:
                print(f"    ... and {len(code_files) - 5} more file(s)")

    if phantom:
        print()
        print(f"PHANTOM SLUGS ({len(phantom)}):")
        print("  Code references a spec: slug that has no spec entry.")
        print("  Agent: ask user — create the entry or remove the backlink?")
        print("  To remove backlink: prov sync remove-backlink <file> <line> <slug>")
        print()
        for fpath, lno, slug in phantom:
            print(f"  {slug}  {fpath}:{lno}")

    if dead:
        print()
        print(f"DEAD REFS ({len(dead)}):")
        print("  Spec entries reference code paths that no longer exist.")
        print("  Agent: ask user — remove or update each ref?")
        print("  To remove: prov sync remove-ref <slug> <ref>")
        print("  To update: prov sync update-ref <slug> <old-ref> <new-ref>")
        print()
        for n, ref in dead:
            print(f"  {n.slug}  [{n.domain}]  ~ {ref}")

    print()
    print("─── Agent: present each item to the user, confirm intent, then apply fixes.")
    print("─── After all fixes: prov validate  →  prov diff  →  commit.")
    return 0


def _cmd_sync_patch(spec_dir: Path, repo_root: Path, args: list[str]) -> int:
    """Apply a single targeted fix. Called by the agent after user confirms."""
    sub = args[0]

    if sub == "mark-implemented":
        # mark-implemented <slug>
        if len(args) < 2:
            print("Usage: prov sync mark-implemented <slug>")
            return 1
        slug = args[1]
        nodes, _, _, _, _ = _load_backend(spec_dir)
        nodes_by_slug = _nodes_by_slug(nodes)
        if slug not in nodes_by_slug:
            print(f"Entry not found: {slug}")
            return 1
        n = nodes_by_slug[slug]
        spec_path = Path(n.file)
        # Find code files referencing this slug
        code_refs = _grep_spec_in_code(repo_root, repo_root)
        found = [(cf, cl) for cf, cl, cs in code_refs if cs == slug]
        _patch_entry_in_spec(spec_path, slug, remove_planned=True)
        for cf, _ in found:
            _patch_entry_in_spec(spec_path, slug, add_code_ref=cf)
        print(f"✓ {slug}: marked implemented")
        if found:
            for cf, _ in found:
                print(f"  + ~ {cf}")
        else:
            print("  (no spec: backlinks found in code — added no ~ refs)")
        return 0

    if sub == "remove-ref":
        # remove-ref <slug> <ref>
        if len(args) < 3:
            print("Usage: prov sync remove-ref <slug> <ref>")
            return 1
        slug, ref = args[1], args[2]
        nodes, _, _, _, _ = _load_backend(spec_dir)
        nodes_by_slug = _nodes_by_slug(nodes)
        if slug not in nodes_by_slug:
            print(f"Entry not found: {slug}")
            return 1
        spec_path = Path(nodes_by_slug[slug].file)
        if _patch_entry_in_spec(spec_path, slug, remove_code_ref=ref):
            print(f"✓ removed ~ {ref} from {slug}")
        else:
            print(f"✗ ref not found in {slug} — check slug and ref path")
            return 1
        return 0

    if sub == "update-ref":
        # update-ref <slug> <old-ref> <new-ref>
        if len(args) < 4:
            print("Usage: prov sync update-ref <slug> <old-ref> <new-ref>")
            return 1
        slug, old_ref, new_ref = args[1], args[2], args[3]
        nodes, _, _, _, _ = _load_backend(spec_dir)
        nodes_by_slug = _nodes_by_slug(nodes)
        if slug not in nodes_by_slug:
            print(f"Entry not found: {slug}")
            return 1
        spec_path = Path(nodes_by_slug[slug].file)
        _patch_entry_in_spec(spec_path, slug, remove_code_ref=old_ref)
        _patch_entry_in_spec(spec_path, slug, add_code_ref=new_ref)
        print(f"✓ updated {slug}: ~ {old_ref}  →  ~ {new_ref}")
        return 0

    if sub == "remove-backlink":
        # remove-backlink <file> <line> <slug>
        if len(args) < 4:
            print("Usage: prov sync remove-backlink <file> <line> <slug>")
            return 1
        fpath, line_str, slug = args[1], args[2], args[3]
        try:
            lno = int(line_str)
        except ValueError:
            print(f"line must be an integer, got: {line_str!r}")
            return 1
        code_path = repo_root / fpath if not Path(fpath).is_absolute() else Path(fpath)
        if not code_path.exists():
            print(f"File not found: {fpath}")
            return 1
        if _remove_spec_backlink_from_code(code_path, slug, lno):
            print(f"✓ removed spec:{slug} from {fpath}:{lno}")
        else:
            print(f"✗ backlink not found near {fpath}:{lno} — check file and line")
            return 1
        return 0

    print(f"Unknown sync sub-command: {sub}")
    return 1


def cmd_rebuild(spec_dir: Path) -> None:
    cache_dir = spec_dir / ".spec"
    cache_dir.mkdir(exist_ok=True)
    nodes, ctx, summaries, refs_by_domain, file_by_domain = _load_backend(spec_dir)
    from datetime import datetime, timezone

    data = {
        "generated": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "spec_files": list(file_by_domain.values()),
        "nodes": {
            n.slug: {
                "type": n.type,
                "domain": n.domain,
                "file": n.file,
                "statement": n.statement,
                "planned": getattr(n, "planned", False),
                "provenance": n.provenance,
                "assumptions": n.assumptions,
                "code_refs": n.code_refs,
                "depends_on": n.depends_on,
                "blocked_by": getattr(n, "blocked_by", []),
            }
            for n in nodes
        },
        "edges": [],
    }
    edges = _build_edges(nodes)
    for e in edges:
        if "src/" in e.to_slug or "/" in e.to_slug:
            data["edges"].append({"from": e.from_slug, "to": e.to_slug, "type": e.type})
        else:
            data["edges"].append(
                {"from": e.from_slug, "to": e.to_slug, "type": "depends-on"}
            )
    by_file: dict[str, list[str]] = {}
    for n in nodes:
        for ref in n.code_refs:
            fp = ref.split(":")[0]
            by_file.setdefault(fp, []).append(n.slug)
    code_index = {
        "generated": data["generated"],
        "by_file": by_file,
        "by_dir": dict(refs_by_domain),
    }
    (cache_dir / "graph.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    (cache_dir / "code-index.json").write_text(
        json.dumps(code_index, indent=2), encoding="utf-8"
    )
    print("Cache rebuilt.")


def _node_to_markdown(n: Node) -> str:
    """Serialize a node to spec format (column 0, 2-space sub-lines)."""
    lines: list[str] = []
    if n.type == "requirement":
        head = f"{n.slug}: {n.statement}"
        if n.planned:
            head += " [planned]"
        lines.append(head)
    elif n.type == "constraint":
        lines.append(f"{n.slug}: {n.statement}")
    else:
        lines.append(f"{n.slug}: {n.statement}")
    if n.provenance:
        lines.append(f"  > {n.provenance}")
    for a in n.assumptions:
        lines.append(f"  ! {a}")
    for ref in n.code_refs:
        lines.append(f"  ~ {ref}")
    for dep in n.depends_on:
        lines.append(f"  @ {dep}")
    for q in n.blocked_by:
        lines.append(f"  ? {q}")
    return "\n".join(lines) + "\n"


def _section_for_type(t: NodeType) -> str:
    if t == "constraint":
        return "Constraints"
    if t == "question":
        return "Open Questions"
    return "Requirements"


def _insert_entry_into_file(path: Path, section_name: str, block: str) -> None:
    """Append entry block to the given section. Creates section if missing."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    target = f"## {section_name}"
    insert_idx = len(lines)
    section_start = -1
    for i, line in enumerate(lines):
        if line.strip() == target:
            section_start = i
        elif section_start >= 0 and line.strip().startswith("## "):
            insert_idx = i
            break
        elif section_start >= 0:
            insert_idx = i + 1
    if section_start < 0:
        insert_idx = len(lines)
        sep = "\n" if lines and not lines[-1].endswith("\n") else ""
        new_section = f"\n## {section_name}\n\n{block}\n"
        path.write_text(text.rstrip() + sep + new_section, encoding="utf-8")
        return
    block_with_nl = block if block.endswith("\n") else block + "\n"
    lines.insert(insert_idx, block_with_nl)
    path.write_text("".join(lines), encoding="utf-8")


def cmd_write(spec_dir: Path, repo_root: Path, args: list[str]) -> int:
    """prov write — structured JSON input. Validates, shows would-write, --yes to write."""
    autonous = "--yes" in args or "-y" in args
    rest = [a for a in args if a not in ("--yes", "-y")]

    raw: str
    if not rest:
        raw = sys.stdin.read()
    elif rest[0] == "--json" and len(rest) >= 2:
        raw = rest[1]
    elif rest[0].endswith(".json") and Path(rest[0]).exists():
        raw = Path(rest[0]).read_text(encoding="utf-8")
    else:
        raw = " ".join(rest) if rest else sys.stdin.read()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"=== SPEC WRITE ===")
        print(f"Error: invalid JSON — {e}")
        return 1

    domain = data.get("domain")
    entries_raw = data.get("entries", [])
    if not isinstance(entries_raw, list):
        entries_raw = [entries_raw]
    if not domain or not entries_raw:
        print("=== PROV WRITE ===")
        print("Error: JSON must have 'domain' and 'entries' (array).")
        return 1

    nodes, ctx, _, _, file_by_domain = _load_backend(spec_dir)
    nodes_by_slug = _nodes_by_slug(nodes)

    if domain not in file_by_domain:
        print("=== PROV WRITE ===")
        print(
            f"Error: domain '{domain}' not found. Known: {', '.join(sorted(file_by_domain.keys()))}"
        )
        return 1

    domain_path = Path(file_by_domain[domain])
    if not domain_path.is_absolute():
        domain_path = repo_root / domain_path

    to_write: list[Node] = []
    errors: list[str] = []

    slug_re = re.compile(r"^[a-z][a-z0-9\-]*$")
    for e in entries_raw:
        raw_slug = (e.get("slug") or "").strip()
        typ = e.get("type", "requirement")
        statement = e.get("statement", "")
        provenance = e.get("provenance", "")
        assumptions = e.get("assumptions", []) or []
        planned = bool(e.get("planned", False))
        depends_on = e.get("depends_on", []) or []
        code_refs = e.get("code_refs", []) or []
        blocked_by = e.get("blocked_by", []) or []

        base = raw_slug.lstrip("C:").lstrip("Q:")
        if not base or not slug_re.match(base):
            errors.append(f"invalid slug: {raw_slug!r} (need kebab-case)")
            continue
        if typ == "constraint":
            slug = f"C:{base}"
        elif typ == "question":
            slug = f"Q:{base}"
        else:
            slug = base

        if slug in nodes_by_slug:
            errors.append(f"slug taken: {slug}")
            continue
        for dep in depends_on:
            if dep not in nodes_by_slug and dep not in {n.slug for n in to_write}:
                errors.append(f"depends-on @ {dep} not found for {slug}")
        if not provenance:
            errors.append(f"provenance required for {slug}")
        if typ == "constraint" and planned:
            planned = False

        to_write.append(
            Node(
                slug=slug,
                type=typ,
                domain=domain,
                file=str(domain_path),
                statement=statement,
                planned=planned,
                provenance=provenance,
                assumptions=assumptions,
                code_refs=code_refs,
                depends_on=depends_on,
                blocked_by=blocked_by,
            )
        )

    if errors:
        print("=== PROV WRITE ===")
        print()
        print("VALIDATION ERRORS:")
        for err in errors:
            print(f"  {err}")
        return 1

    print("=== PROV WRITE ===")
    print()
    print("WOULD WRITE:")
    for n in to_write:
        print(_node_to_markdown(n))
    print(
        f"→ {len(to_write)} entries to {domain_path.relative_to(repo_root) if domain_path.is_relative_to(repo_root) else domain_path}"
    )
    if not autonous:
        print()
        print("Run with --yes to write.")
        return 0

    for n in to_write:
        section = _section_for_type(n.type)
        _insert_entry_into_file(domain_path, section, _node_to_markdown(n))
    print()
    print("Wrote.")
    return 0


def _load_nodes_from_ref(spec_dir: Path, repo_root: Path, ref: str) -> list[Node]:
    """Load nodes by parsing spec files at the given git ref."""
    try:
        rel_spec = str(spec_dir.relative_to(repo_root)).replace("\\", "/")
    except ValueError:
        rel_spec = "spec"
    result = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", ref, "--", rel_spec],
        capture_output=True,
        text=True,
        cwd=repo_root,
    )
    if result.returncode != 0:
        return []
    files = [
        f.strip()
        for f in result.stdout.splitlines()
        if f.strip().endswith(".md") and "CONTEXT" not in f
    ]
    ctx = _parse_context(spec_dir)
    nodes: list[Node] = []
    for f in files:
        try:
            content = subprocess.run(
                ["git", "show", f"{ref}:{f}"],
                capture_output=True,
                text=True,
                cwd=repo_root,
                check=True,
            ).stdout
        except subprocess.CalledProcessError:
            continue
        domain = (
            Path(f).stem
            if Path(f).parent.name == Path(rel_spec).name
            else Path(f).parent.name
        )
        path = (repo_root / f).resolve()
        ns, _, _ = _parse_spec_file_from_text(content, domain, str(path))
        nodes.extend(ns)
    return nodes


def _parse_spec_file_from_text(
    text: str, domain: str, ref_path: str
) -> tuple[list[Node], str, list[str]]:
    """Parse spec content from string. Same logic as _parse_spec_file but for in-memory text."""
    nodes: list[Node] = []
    summary = ""
    refs: list[str] = []
    current: Node | None = None
    section = ""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith("## Refs"):
            section = "refs"
            continue
        if section == "refs" and line.strip().startswith("~"):
            refs.append(line.strip().lstrip("~").strip())
            continue
        if section == "refs":
            section = ""
        if i == 1 and line.strip().startswith(">"):
            summary = line.strip().lstrip(">").strip()
            continue
        if line.startswith("## "):
            section = line[3:].split()[0].lower() if line[3:].strip() else ""
            continue
        stripped = line.strip()
        is_subline = (
            line.startswith("  ") and len(line) > 2 and line[2] in ">!~@?"
        ) or (current is not None and stripped and stripped[0] in ">!~@?")
        if not is_subline and line.strip():
            current = None
            s = line.strip()
            if re.match(r"^C:[a-z][a-z0-9-]*:", s):
                m = re.match(r"^(C:[a-z][a-z0-9-]*):\s*(.*)", s)
                if m:
                    slug, stmt = m.groups()
                    current = Node(
                        slug=slug,
                        type="constraint",
                        domain=domain,
                        file=ref_path,
                        statement=stmt.strip(),
                        planned=False,
                    )
                    nodes.append(current)
            elif re.match(r"^Q:[a-z][a-z0-9-]*:", s):
                m = re.match(r"^(Q:[a-z][a-z0-9-]*):\s*(.*)", s)
                if m:
                    slug, stmt = m.groups()
                    current = Node(
                        slug=slug,
                        type="question",
                        domain=domain,
                        file=ref_path,
                        statement=stmt.strip(),
                        planned=False,
                    )
                    nodes.append(current)
            elif re.match(r"^[a-z][a-z0-9-]*:", s):
                m = re.match(r"^([a-z][a-z0-9-]*):\s*(.*)", s)
                if m:
                    slug, rest = m.groups()
                    planned = "[planned]" in rest
                    stmt = re.sub(r"\s*\[planned\]\s*", " ", rest).strip()
                    current = Node(
                        slug=slug,
                        type="requirement",
                        domain=domain,
                        file=ref_path,
                        statement=stmt,
                        planned=planned,
                    )
                    nodes.append(current)
            continue
        if is_subline and current is not None:
            sub = line[2:].lstrip() if line.startswith("  ") else stripped
            if sub.startswith("> ") and len(sub) > 2 and sub[2] in "!~@?":
                sub = sub[2:]
            if sub.startswith(">"):
                rest = sub[1:].strip()
                if rest != "[planned]":
                    current.provenance = rest
            elif sub.startswith("!"):
                current.assumptions.append(sub[1:].strip())
            elif sub.startswith("~"):
                ref = sub[1:].strip()
                if ref and not ref.startswith("sdd/"):
                    current.code_refs.append(ref)
            elif sub.startswith("@"):
                dep = sub[1:].strip().split()[0] if sub[1:].strip() else ""
                if dep and dep not in current.depends_on:
                    current.depends_on.append(dep)
            elif sub.startswith("?"):
                q = sub[1:].strip().split()[0] if sub[1:].strip() else ""
                if q and q not in current.blocked_by:
                    current.blocked_by.append(q)
    return nodes, summary, refs


def cmd_diff(spec_dir: Path, repo_root: Path, ref: str) -> None:
    """prov diff [ref] — semantic change manifest vs ref (default HEAD)."""
    nodes, _, _, _, _ = _load_backend(spec_dir)
    old_nodes = _load_nodes_from_ref(spec_dir, repo_root, ref)
    old_by = _nodes_by_slug(old_nodes)
    cur_by = _nodes_by_slug(nodes)

    implemented: list[tuple[str, str]] = []
    new_entries: list[Node] = []
    modified: list[tuple[Node, Node]] = []
    resolved_questions: list[str] = []
    removed: list[Node] = []
    constraints_changed: list[tuple[Node, Node]] = []
    assumptions_to_confirm: list[tuple[str, str]] = []

    for slug, n in cur_by.items():
        if slug not in old_by:
            new_entries.append(n)
            for a in n.assumptions:
                assumptions_to_confirm.append((n.slug, a))
            continue
        o = old_by[slug]
        if n.type == "question":
            continue
        if n.type == "constraint":
            if o.statement != n.statement or o.provenance != n.provenance:
                constraints_changed.append((o, n))
            continue
        if o.planned and not n.planned and n.code_refs:
            implemented.append((n.slug, n.domain))
        elif (
            o.statement != n.statement
            or o.provenance != n.provenance
            or set(o.depends_on) != set(n.depends_on)
            or set(o.blocked_by) != set(n.blocked_by)
        ):
            modified.append((o, n))
        for a in n.assumptions:
            if (n.slug, a) not in [(x, y) for x, y in assumptions_to_confirm]:
                assumptions_to_confirm.append((n.slug, a))

    for slug, o in old_by.items():
        if slug not in cur_by:
            removed.append(o)
            if o.type == "question":
                resolved_questions.append(slug)

    print("=== PROV DIFF ===")
    print(f"vs {ref}")
    print()
    if implemented:
        print("IMPLEMENTED (was [planned], now has ~ refs):")
        for slug, dom in implemented:
            print(f"  {slug}  ({dom})")
        print()
    if new_entries:
        print("NEW ENTRIES:")
        for n in new_entries:
            print(f"  {n.slug}  ({n.domain})  {n.statement[:50]}...")
        print()
    if modified:
        print("MODIFIED:")
        for o, n in modified:
            print(f"  {o.slug}: statement/provenance/deps changed")
        print()
    if resolved_questions:
        print("RESOLVED QUESTIONS:")
        for s in resolved_questions:
            print(f"  {s}")
        print()
    if removed:
        print("REMOVED ENTRIES:")
        for n in removed:
            print(f"  {n.slug}  ({n.domain})")
        print()
    if constraints_changed:
        print("CONSTRAINTS CHANGED:")
        for o, n in constraints_changed:
            print(f"  {n.slug}")
        print()
    if assumptions_to_confirm:
        print("ASSUMPTIONS REQUIRING CONFIRMATION:")
        for slug, a in assumptions_to_confirm[:15]:
            print(f"  {slug}  ! {a[:50]}...")
        if len(assumptions_to_confirm) > 15:
            print(f"  ... and {len(assumptions_to_confirm) - 15} more")
        print()
    if not any(
        [
            implemented,
            new_entries,
            modified,
            resolved_questions,
            removed,
            constraints_changed,
            assumptions_to_confirm,
        ]
    ):
        print("No semantic changes.")


def cmd_init(spec_dir: Path) -> None:
    ctx_path = spec_dir / "CONTEXT.md"
    if ctx_path.exists():
        print("CONTEXT.md already exists.")
        return
    ctx_path.write_text(
        """# <Project Name>

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
""",
        encoding="utf-8",
    )
    print("Created CONTEXT.md. Edit it with your project details.")


def main() -> int:
    spec_dir = _spec_dir()
    repo_root = _repo_root()
    args = sys.argv[1:]
    if not args:
        print("Usage: python prov/prov.py <command> [args]")
        print(
            "Commands: orient, scope <path>, context <slug>, impact <slug>, find <kw>, domain <name>,"
        )
        print("          validate, check-slug <slug>, reconcile <path>, sync [path],")
        print("          sync mark-implemented <slug>, sync remove-ref <slug> <ref>,")
        print(
            "          sync update-ref <slug> <old> <new>, sync remove-backlink <file> <line> <slug>,"
        )
        print("          write [--yes], diff [ref], rebuild, init")
        return 0
    cmd = args[0].lower()
    rest = args[1:]

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


if __name__ == "__main__":
    sys.exit(main())
