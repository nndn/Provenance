"""prov sync — drift report and patch sub-commands."""
from pathlib import Path

from prov.indexing import grep_spec_in_code, nodes_by_slug
from prov.model import Node
from prov.spec_io import load_backend
from prov.writer import patch_entry_in_spec, remove_spec_backlink_from_code


def cmd_sync(spec_dir: Path, repo_root: Path, args: list[str]) -> int:
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

    nodes, _, _, _, _ = load_backend(spec_dir)
    nodes_by_slug_map = nodes_by_slug(nodes)
    code_refs = grep_spec_in_code(scan_path, repo_root)

    phantom: list[tuple[str, int, str]] = [
        (f, l, s)
        for f, l, s in code_refs
        if s not in nodes_by_slug_map
        and f"C:{s}" not in nodes_by_slug_map
        and f"Q:{s}" not in nodes_by_slug_map
    ]

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
    sub = args[0]

    if sub == "mark-implemented":
        if len(args) < 2:
            print("Usage: prov sync mark-implemented <slug>")
            return 1
        slug = args[1]
        nodes, _, _, _, _ = load_backend(spec_dir)
        nodes_by_slug_map = nodes_by_slug(nodes)
        if slug not in nodes_by_slug_map:
            print(f"Entry not found: {slug}")
            return 1
        n = nodes_by_slug_map[slug]
        spec_path = Path(n.file)
        code_refs = grep_spec_in_code(repo_root, repo_root)
        found = [(cf, cl) for cf, cl, cs in code_refs if cs == slug]
        patch_entry_in_spec(spec_path, slug, remove_planned=True)
        for cf, _ in found:
            patch_entry_in_spec(spec_path, slug, add_code_ref=cf)
        print(f"✓ {slug}: marked implemented")
        if found:
            for cf, _ in found:
                print(f"  + ~ {cf}")
        else:
            print("  (no spec: backlinks found in code — added no ~ refs)")
        return 0

    if sub == "remove-ref":
        if len(args) < 3:
            print("Usage: prov sync remove-ref <slug> <ref>")
            return 1
        slug, ref = args[1], args[2]
        nodes, _, _, _, _ = load_backend(spec_dir)
        nodes_by_slug_map = nodes_by_slug(nodes)
        if slug not in nodes_by_slug_map:
            print(f"Entry not found: {slug}")
            return 1
        spec_path = Path(nodes_by_slug_map[slug].file)
        if patch_entry_in_spec(spec_path, slug, remove_code_ref=ref):
            print(f"✓ removed ~ {ref} from {slug}")
        else:
            print(f"✗ ref not found in {slug} — check slug and ref path")
            return 1
        return 0

    if sub == "update-ref":
        if len(args) < 4:
            print("Usage: prov sync update-ref <slug> <old-ref> <new-ref>")
            return 1
        slug, old_ref, new_ref = args[1], args[2], args[3]
        nodes, _, _, _, _ = load_backend(spec_dir)
        nodes_by_slug_map = nodes_by_slug(nodes)
        if slug not in nodes_by_slug_map:
            print(f"Entry not found: {slug}")
            return 1
        spec_path = Path(nodes_by_slug_map[slug].file)
        patch_entry_in_spec(spec_path, slug, remove_code_ref=old_ref)
        patch_entry_in_spec(spec_path, slug, add_code_ref=new_ref)
        print(f"✓ updated {slug}: ~ {old_ref}  →  ~ {new_ref}")
        return 0

    if sub == "remove-backlink":
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
        if remove_spec_backlink_from_code(code_path, slug, lno):
            print(f"✓ removed spec:{slug} from {fpath}:{lno}")
        else:
            print(f"✗ backlink not found near {fpath}:{lno} — check file and line")
            return 1
        return 0

    print(f"Unknown sync sub-command: {sub}")
    return 1
