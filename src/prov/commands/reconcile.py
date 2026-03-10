"""prov reconcile <path> — detect code↔spec drift."""
from pathlib import Path

from prov.indexing import grep_spec_in_code, nodes_by_slug
from prov.spec_io import load_backend


def cmd_reconcile(spec_dir: Path, repo_root: Path, path_arg: str) -> None:
    nodes, _, _, _, _ = load_backend(spec_dir)
    nodes_by_slug_map = nodes_by_slug(nodes)
    path = repo_root / path_arg if path_arg else repo_root
    if not path.exists():
        path = repo_root
    code_refs = grep_spec_in_code(path, repo_root)
    phantom = [
        (f, l, s)
        for f, l, s in code_refs
        if s not in nodes_by_slug_map
        and f"C:{s}" not in nodes_by_slug_map
        and f"Q:{s}" not in nodes_by_slug_map
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
