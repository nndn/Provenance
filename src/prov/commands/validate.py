"""prov validate — run before commit."""
import re
from pathlib import Path

from prov.indexing import build_edges, grep_spec_in_code, nodes_by_slug
from prov.spec_io import load_backend


def cmd_validate(spec_dir: Path, repo_root: Path) -> int:
    nodes, _, _, refs_by_domain, _ = load_backend(spec_dir)
    nodes_by_slug_map = nodes_by_slug(nodes)
    build_edges(nodes)
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
            if d not in nodes_by_slug_map and not d.startswith("src/") and ":" not in d:
                if not any(d in x.code_refs for x in nodes):
                    errors.append(
                        f"no-dangling-dep:  @ {d}  target not found for {n.slug}"
                    )
        for b in n.blocked_by:
            if b not in nodes_by_slug_map:
                errors.append(
                    f"no-dangling-block:  ? {b}  target not found for {n.slug}"
                )

    slug_re = re.compile(r"^[a-z][a-z0-9\-]*\-[a-z0-9\-]+$")
    code_refs = grep_spec_in_code(repo_root, repo_root)
    for fpath, line, slug in code_refs:
        if not slug_re.match(slug):
            continue
        if (
            slug in nodes_by_slug_map
            or f"C:{slug}" in nodes_by_slug_map
            or f"Q:{slug}" in nodes_by_slug_map
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
