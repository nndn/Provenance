"""prov orient — session start."""
from pathlib import Path

from prov.model import Node
from prov.spec_io import load_backend


def cmd_orient(spec_dir: Path, repo_root: Path) -> None:
    nodes, ctx, summaries, refs_by_domain, _ = load_backend(spec_dir)
    by_domain: dict[str, list[Node]] = {}
    for n in nodes:
        by_domain.setdefault(n.domain, []).append(n)

    print("=== PROV ORIENT ===")
    print()
    print(f"Project: {ctx.title}")
    print(ctx.purpose)
    print()
    print(
        "Hard constraints:",
        ", ".join(ctx.hard_constraints) if ctx.hard_constraints else "(none)",
    )
    print()
    print("DOMAINS:")
    for domain in sorted(by_domain.keys()):
        reqs = [n for n in by_domain[domain] if n.type == "requirement"]
        planned = sum(1 for n in reqs if n.planned)
        questions = [n for n in by_domain[domain] if n.type == "question"]
        assumptions = sum(len(n.assumptions) for n in by_domain[domain])
        summ = (summaries.get(domain) or "")[:50]
        print(
            f"  {domain:12} {summ:50} {len(reqs)} reqs  {planned} planned  {len(questions)} questions  {assumptions} assumptions"
        )

    open_q = [n for n in nodes if n.type == "question"]
    if open_q:
        print()
        print(f"OPEN QUESTIONS ({len(open_q)} total):")
        for n in open_q[:20]:
            stmt = (n.statement or "")[:60]
            refs = [x for x in nodes if n.slug in getattr(x, "blocked_by", [])]
            block_slugs = ", ".join(x.slug for x in refs) if refs else ""
            print(f"  {n.slug}  {n.domain}  {stmt}")
            if block_slugs:
                print(f"            -> blocks: {block_slugs}")

    unconf = [(n, a) for n in nodes for a in n.assumptions]
    if unconf:
        print()
        print(f"UNCONFIRMED ASSUMPTIONS ({len(unconf)} total):")
        for n, a in unconf[:15]:
            print(f"  {n.slug:20} {n.domain:10} ! {(a or '')[:50]}")

    planned = [n for n in nodes if n.type == "requirement" and n.planned]
    if planned:
        print()
        print(f"PLANNED ({len(planned)} total):")
        for n in planned[:15]:
            print(f"  {n.slug:20} {n.domain:10} {(n.statement or '')[:50]}")

    print()
    print("─── Next: prov domain <name> | prov context <slug> | prov validate")
