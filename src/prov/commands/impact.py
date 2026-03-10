"""prov impact <slug> — blast radius before changing."""
import sys
from pathlib import Path

from prov.indexing import build_edges, nodes_by_slug
from prov.spec_io import load_backend


def cmd_impact(spec_dir: Path, repo_root: Path, slug: str) -> None:
    nodes, _, _, _, _ = load_backend(spec_dir)
    nodes_by_slug_map = nodes_by_slug(nodes)
    build_edges(nodes)
    if slug not in nodes_by_slug_map:
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
    all_slugs = (trans | {slug}) if slug in nodes_by_slug_map else trans
    for n in [nodes_by_slug_map[s] for s in all_slugs if s in nodes_by_slug_map]:
        if n and n.code_refs:
            code_paths.extend(n.code_refs)
    code_paths.extend(nodes_by_slug_map[slug].code_refs if slug in nodes_by_slug_map else [])
    assumptions: list[tuple[str, str]] = []
    for s in trans | {slug}:
        if s in nodes_by_slug_map:
            for a in nodes_by_slug_map[s].assumptions:
                assumptions.append((s, a))
    planned = [
        nodes_by_slug_map[s]
        for s in trans
        if s in nodes_by_slug_map and getattr(nodes_by_slug_map[s], "planned", False)
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
        d = nodes_by_slug_map.get(s)
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
