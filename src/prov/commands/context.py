"""prov context <slug> — full entry details."""
import sys
from pathlib import Path

from prov.indexing import build_edges, nodes_by_slug
from prov.spec_io import load_backend


def cmd_context(spec_dir: Path, repo_root: Path, slug: str) -> None:
    nodes, _, _, _, file_by_domain = load_backend(spec_dir)
    nodes_by_slug_map = nodes_by_slug(nodes)
    edges = build_edges(nodes)
    n = nodes_by_slug_map.get(slug)
    if not n:
        for k in nodes_by_slug_map:
            if k.replace("C:", "").replace("Q:", "") == slug or k.endswith(":" + slug):
                n = nodes_by_slug_map[k]
                break
    if not n:
        print(f"Entry not found: {slug}")
        sys.exit(1)
    domain_nodes = [x for x in nodes if x.domain == n.domain]
    constraints = [x for x in domain_nodes if x.type == "constraint"]
    deps = [nodes_by_slug_map[d] for d in n.depends_on if d in nodes_by_slug_map]
    dep_by = [x for x in nodes if n.slug in x.depends_on]
    blocked = [
        nodes_by_slug_map[b] for b in getattr(n, "blocked_by", []) if b in nodes_by_slug_map
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
