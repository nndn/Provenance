"""prov scope <path> — what governs this file or directory."""
from pathlib import Path

from prov.indexing import build_edges, nodes_by_slug, slugs_for_path
from prov.spec_io import load_backend


def cmd_scope(spec_dir: Path, repo_root: Path, path_arg: str) -> None:
    nodes, ctx, _, refs_by_domain, _ = load_backend(spec_dir)
    slugs = slugs_for_path(path_arg, nodes, refs_by_domain, repo_root)
    nodes_by_slug_map = nodes_by_slug(nodes)
    edges = build_edges(nodes)

    if not slugs:
        print(f"=== SCOPE: {path_arg} ===")
        print("No spec entries reference this path.")
        print("Run: prov reconcile <path>  to check for drift.")
        return

    reqs = [
        nodes_by_slug_map[s]
        for s in slugs
        if s in nodes_by_slug_map and nodes_by_slug_map[s].type == "requirement"
    ]
    constraints = [
        nodes_by_slug_map[s]
        for s in slugs
        if s in nodes_by_slug_map and nodes_by_slug_map[s].type == "constraint"
    ]
    dep_on = set()
    for e in edges:
        if e.to_slug in slugs and e.type == "depends-on":
            dep_on.add(e.from_slug)
    dep_nodes = [
        nodes_by_slug_map[s] for s in dep_on if s in nodes_by_slug_map and s not in slugs
    ]
    qs = set()
    for n in reqs + dep_nodes:
        for b in getattr(n, "blocked_by", []):
            qs.add(b)
    q_nodes = [nodes_by_slug_map[s] for s in qs if s in nodes_by_slug_map]

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
