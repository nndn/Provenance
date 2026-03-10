"""Spec I/O — parse markdown, load backend, resolve paths."""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

from prov.model import Context, Node


def _find_spec_dir_from_cwd() -> Path | None:
    """Search from cwd upward for prov/, spec/, or specs/ containing spec files."""
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        for name in ("prov", "spec", "specs"):
            cand = parent / name
            if not cand.is_dir():
                continue
            if (cand / "CONTEXT.md").exists():
                return cand
            if any(cand.glob("*.md")):
                return cand
    return None


def get_spec_dir(entry_dir: Path | None = None) -> Path:
    """Resolve spec directory. SPEC_DIR env wins; else entry script's dir; else search cwd."""
    d = os.environ.get("SPEC_DIR")
    if d:
        return Path(d).resolve()
    if entry_dir is not None:
        resolved = entry_dir.resolve() if not entry_dir.is_absolute() else entry_dir
        # Only treat resolved as spec dir if it contains CONTEXT.md (definitive indicator)
        if (resolved / "CONTEXT.md").exists():
            return resolved
        # Otherwise search from cwd for prov/, spec/, or specs/
        found = _find_spec_dir_from_cwd()
        if found is not None:
            return found
        # No spec dir found: default to cwd/prov (for `prov init` in a fresh project)
        return Path.cwd() / "prov"
    # Fallback when called without entry_dir
    return Path(__file__).resolve().parent.parent


def get_repo_root(spec_dir: Path) -> Path:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
            cwd=spec_dir.parent,
        )
        return Path(out.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return spec_dir.parent


def parse_spec_file(path: Path, domain: str) -> tuple[list[Node], str, list[str]]:
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


def parse_context(spec_dir: Path) -> Context:
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


def load_backend(
    spec_dir: Path,
) -> tuple[list[Node], Context, dict[str, str], dict[str, list[str]], dict[str, str]]:
    """Returns (nodes, context, domain_summaries, refs_by_domain, file_by_domain)."""
    ctx = parse_context(spec_dir)
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
        ns, summary, refs = parse_spec_file(path, name)
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
            ns, summary, refs = parse_spec_file(p, domain)
            nodes.extend(ns)
            domain_summaries[domain] = summary
            refs_by_domain[domain] = refs
            file_by_domain[domain] = str(p)

    return nodes, ctx, domain_summaries, refs_by_domain, file_by_domain


def parse_spec_file_from_text(
    text: str, domain: str, ref_path: str
) -> tuple[list[Node], str, list[str]]:
    """Parse spec content from string. Same logic as parse_spec_file but for in-memory text."""
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


def load_nodes_from_ref(spec_dir: Path, repo_root: Path, ref: str) -> list[Node]:
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
        ns, _, _ = parse_spec_file_from_text(content, domain, str(path))
        nodes.extend(ns)
    return nodes
