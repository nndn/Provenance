"""prov domain <name> — full domain load."""
import sys
from pathlib import Path

from prov.spec_io import load_backend


def cmd_domain(spec_dir: Path, name: str) -> None:
    nodes, _, summaries, refs_by_domain, file_by_domain = load_backend(spec_dir)
    domain_nodes = [n for n in nodes if n.domain == name]
    if not domain_nodes:
        print(f"Domain not found: {name}")
        sys.exit(1)
    path = file_by_domain.get(name, "")
    summary = summaries.get(name, "")

    print(f"=== DOMAIN: {name} ===")
    print()
    print(summary)
    print(f"File: {path}")
    print()
    constraints = [n for n in domain_nodes if n.type == "constraint"]
    reqs = [n for n in domain_nodes if n.type == "requirement"]
    planned = sum(1 for n in reqs if n.planned)
    questions = [n for n in domain_nodes if n.type == "question"]
    print(f"CONSTRAINTS ({len(constraints)}):")
    for n in constraints:
        print(f"  {n.slug}: {n.statement}")
        print(f"    > {n.provenance}")
        if n.code_refs:
            print(f"    ~ " + ", ".join(n.code_refs))
    print()
    print(f"REQUIREMENTS ({len(reqs) - planned} implemented, {planned} planned):")
    for n in reqs:
        suffix = " [planned]" if n.planned else ""
        print(f"  {n.slug}: {n.statement}{suffix}")
        print(f"    > {n.provenance}")
        if n.assumptions:
            for a in n.assumptions:
                print(f"    ! {a}")
        if n.depends_on:
            for d in n.depends_on:
                print(f"    @ {d}")
        if n.code_refs:
            for r in n.code_refs:
                print(f"    ~ {r}")
        if n.blocked_by:
            for b in n.blocked_by:
                print(f"    ? {b}")
    print()
    print(f"OPEN QUESTIONS ({len(questions)}):")
    for n in questions:
        print(f"  {n.slug}: {n.statement}")
        print(f"    > blocks: {', '.join(n.blocked_by)}")
    print()
    print("OUT OF SCOPE:")
    print("  (see domain file)")
