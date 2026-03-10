"""prov diff [ref] — semantic change manifest vs ref."""
from pathlib import Path

from prov.indexing import nodes_by_slug
from prov.model import Node
from prov.spec_io import load_backend, load_nodes_from_ref


def cmd_diff(spec_dir: Path, repo_root: Path, ref: str) -> None:
    nodes, _, _, _, _ = load_backend(spec_dir)
    old_nodes = load_nodes_from_ref(spec_dir, repo_root, ref)
    old_by = nodes_by_slug(old_nodes)
    cur_by = nodes_by_slug(nodes)

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
            if (n.slug, a) not in assumptions_to_confirm:
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
