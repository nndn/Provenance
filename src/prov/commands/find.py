"""prov find <keywords> — search entries."""
from pathlib import Path

from prov.spec_io import load_backend


def cmd_find(spec_dir: Path, keywords: str) -> None:
    nodes, _, _, _, _ = load_backend(spec_dir)
    kws = keywords.lower().split()
    matches = []
    for n in nodes:
        score = 0
        text = f"{n.slug} {n.statement} {n.domain}".lower()
        for kw in kws:
            if kw in text:
                score += 1
        if score > 0:
            matches.append((score, n))
    matches.sort(key=lambda x: -x[0])

    print(f'=== FIND: "{keywords}" ===')
    print()
    if not matches:
        print("No entries match.")
        print("Try: prov orient    to browse all domains.")
        return
    for _, n in matches[:20]:
        print(f"{n.slug}    [{n.domain}]    {n.type}    {n.statement[:60]}")
    print()
    print(f"{len(matches)} results.")
    print("─── prov context <slug>    for full details")
