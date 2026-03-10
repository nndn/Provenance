"""prov rebuild — regenerate .spec/ cache."""
import json
from datetime import datetime, timezone
from pathlib import Path

from prov.indexing import build_edges
from prov.spec_io import load_backend


def cmd_rebuild(spec_dir: Path) -> None:
    cache_dir = spec_dir / ".spec"
    cache_dir.mkdir(exist_ok=True)
    nodes, ctx, summaries, refs_by_domain, file_by_domain = load_backend(spec_dir)

    data = {
        "generated": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "spec_files": list(file_by_domain.values()),
        "nodes": {
            n.slug: {
                "type": n.type,
                "domain": n.domain,
                "file": n.file,
                "statement": n.statement,
                "planned": getattr(n, "planned", False),
                "provenance": n.provenance,
                "assumptions": n.assumptions,
                "code_refs": n.code_refs,
                "depends_on": n.depends_on,
                "blocked_by": getattr(n, "blocked_by", []),
            }
            for n in nodes
        },
        "edges": [],
    }
    edges = build_edges(nodes)
    for e in edges:
        if "src/" in e.to_slug or "/" in e.to_slug:
            data["edges"].append({"from": e.from_slug, "to": e.to_slug, "type": e.type})
        else:
            data["edges"].append(
                {"from": e.from_slug, "to": e.to_slug, "type": "depends-on"}
            )
    by_file: dict[str, list[str]] = {}
    for n in nodes:
        for ref in n.code_refs:
            fp = ref.split(":")[0]
            by_file.setdefault(fp, []).append(n.slug)
    code_index = {
        "generated": data["generated"],
        "by_file": by_file,
        "by_dir": dict(refs_by_domain),
    }
    (cache_dir / "graph.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    (cache_dir / "code-index.json").write_text(
        json.dumps(code_index, indent=2), encoding="utf-8"
    )
    print("Cache rebuilt.")
