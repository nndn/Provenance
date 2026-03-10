"""prov orient — session start."""
from pathlib import Path

from prov.format import (
    BOLD,
    DIM,
    box_header,
    domain_table,
    rule,
    t,
)
from prov.model import Node
from prov.spec_io import load_backend


def cmd_orient(spec_dir: Path, repo_root: Path) -> None:
    nodes, ctx, summaries, refs_by_domain, _ = load_backend(spec_dir)
    by_domain: dict[str, list[Node]] = {}
    for n in nodes:
        by_domain.setdefault(n.domain, []).append(n)

    # Header
    print(t(box_header(" PROV ORIENT "), BOLD))
    print()
    print(t(f"Project: {ctx.title}", BOLD))
    print(t(ctx.purpose, DIM))
    print()
    constraints_str = ", ".join(ctx.hard_constraints) if ctx.hard_constraints else "(none)"
    print(t("Hard constraints: ", DIM) + constraints_str)
    print()

    # DOMAINS table
    table_rows = []
    for domain in sorted(by_domain.keys()):
        reqs = [n for n in by_domain[domain] if n.type == "requirement"]
        planned = sum(1 for n in reqs if n.planned)
        questions = [n for n in by_domain[domain] if n.type == "question"]
        assumptions = sum(len(n.assumptions) for n in by_domain[domain])
        summ = (summaries.get(domain) or "")[:26]
        table_rows.append(
            {
                "domain": domain,
                "summary": summ,
                "reqs": str(len(reqs)),
                "planned": str(planned),
                "qs": str(len(questions)),
                "assumptions": str(assumptions),
            }
        )
    print(domain_table(table_rows))
    print()

    open_q = [n for n in nodes if n.type == "question"]
    if open_q:
        print()
        print(t(f"│ OPEN QUESTIONS ({len(open_q)} total):", BOLD))
        for n in open_q[:20]:
            stmt = (n.statement or "")[:60]
            refs = [x for x in nodes if n.slug in getattr(x, "blocked_by", [])]
            block_slugs = ", ".join(x.slug for x in refs) if refs else ""
            print(f"  {n.slug}  {n.domain}  {stmt}")
            if block_slugs:
                print(t(f"            → blocks: {block_slugs}", DIM))

    unconf = [(n, a) for n in nodes for a in n.assumptions]
    if unconf:
        print()
        print(t(f"│ UNCONFIRMED ASSUMPTIONS ({len(unconf)} total):", BOLD))
        for n, a in unconf[:15]:
            print(f"  {n.slug:20} {n.domain:10} ! {(a or '')[:50]}")

    planned = [n for n in nodes if n.type == "requirement" and n.planned]
    if planned:
        print()
        print(t(f"│ PLANNED ({len(planned)} total):", BOLD))
        for n in planned[:15]:
            print(f"  {n.slug:20} {n.domain:10} {(n.statement or '')[:50]}")

    print()
    print(rule())
    print(t("Next: prov domain <name> | prov context <slug> | prov validate", DIM))
