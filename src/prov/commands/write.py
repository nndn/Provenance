"""prov write — add entries from JSON."""
import json
import re
import sys
from pathlib import Path

from prov.model import Node
from prov.spec_io import load_backend
from prov.writer import insert_entry_into_file, node_to_markdown, section_for_type


def cmd_write(spec_dir: Path, repo_root: Path, args: list[str]) -> int:
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
        print("=== SPEC WRITE ===")
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

    nodes, ctx, _, _, file_by_domain = load_backend(spec_dir)
    nodes_by_slug_map = {n.slug: n for n in nodes}

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

        if slug in nodes_by_slug_map:
            errors.append(f"slug taken: {slug}")
            continue
        for dep in depends_on:
            if dep not in nodes_by_slug_map and dep not in {n.slug for n in to_write}:
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
        print(node_to_markdown(n))
    print(
        f"→ {len(to_write)} entries to {domain_path.relative_to(repo_root) if domain_path.is_relative_to(repo_root) else domain_path}"
    )
    if not autonous:
        print()
        print("Run with --yes to write.")
        return 0

    for n in to_write:
        section = section_for_type(n.type)
        insert_entry_into_file(domain_path, section, node_to_markdown(n))
    print()
    print("Wrote.")
    return 0
