"""prov init — scaffold CONTEXT.md."""
from pathlib import Path


def cmd_init(spec_dir: Path) -> None:
    spec_dir.mkdir(parents=True, exist_ok=True)
    ctx_path = spec_dir / "CONTEXT.md"
    if ctx_path.exists():
        print("CONTEXT.md already exists.")
        return
    ctx_path.write_text(
        """# <Project Name>

> <One sentence. What it does and who uses it.>

## Purpose

<2-3 sentences. The problem being solved.>

## User goals

1. <Primary user goal>
2. <Secondary goal>

## Hard constraints

C:example: <Non-negotiable rule>

> <why>

## Non-goals

- <Explicit out-of-scope items>

## Domain map

<domain> prov/<domain>.md
""",
        encoding="utf-8",
    )
    print("Created CONTEXT.md. Edit it with your project details.")
