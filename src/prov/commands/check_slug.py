"""prov check-slug <slug> — is slug available."""
from pathlib import Path

from prov.indexing import nodes_by_slug
from prov.spec_io import load_backend


def cmd_check_slug(spec_dir: Path, slug: str) -> None:
    nodes, _, _, _, _ = load_backend(spec_dir)
    nodes_by_slug_map = nodes_by_slug(nodes)
    full = (
        slug
        if slug in nodes_by_slug_map
        else (slug if slug.startswith("C:") or slug.startswith("Q:") else slug)
    )
    if full in nodes_by_slug_map or slug in nodes_by_slug_map:
        key = full if full in nodes_by_slug_map else slug
        n = nodes_by_slug_map[key]
        print(f"=== CHECK-SLUG: {slug} ===")
        print()
        print(f"TAKEN — {n.file}:")
        print(f"  {n.slug}: {n.statement[:60]}")
        print()
        print("Try: " + slug + "-alt, " + slug + "-v2")
    else:
        print(f"=== CHECK-SLUG: {slug} ===")
        print("Available.")
