"""Spec mutation — patch entries, insert, remove backlinks."""
from __future__ import annotations

import re
from pathlib import Path

from prov.model import Node, NodeType


def patch_entry_in_spec(
    spec_path: Path,
    slug: str,
    remove_planned: bool = False,
    add_code_ref: str | None = None,
    remove_code_ref: str | None = None,
) -> bool:
    """In-place patch a spec entry. Returns True if file was modified."""
    text = spec_path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)

    slug_re = re.compile(r"^" + re.escape(slug) + r":")
    entry_idx = next((i for i, l in enumerate(lines) if slug_re.match(l)), -1)
    if entry_idx < 0:
        return False

    modified = False

    if remove_planned:
        old = lines[entry_idx]
        new = re.sub(r"\s*\[planned\]", "", old).rstrip() + "\n"
        if new != old:
            lines[entry_idx] = new
            modified = True
        i = entry_idx + 1
        while i < len(lines):
            l = lines[i]
            stripped = l.strip()
            if stripped == "":
                i += 1
                continue
            is_sub = (l.startswith("  ") and len(l) > 2 and l[2] in ">!~@?") or (
                stripped and stripped[0] in ">!~@?"
            )
            if not is_sub:
                break
            if re.match(r"^\s*>\s*\[planned\]\s*$", l):
                lines.pop(i)
                modified = True
                continue
            i += 1

    sub_end = entry_idx
    j = entry_idx + 1
    while j < len(lines):
        l = lines[j]
        stripped = l.strip()
        if stripped == "":
            j += 1
            continue
        if (l.startswith("  ") and len(l) > 2 and l[2] in ">!~@?") or (
            stripped and stripped[0] in ">!~@?"
        ):
            sub_end = j
            j += 1
        else:
            break

    if remove_code_ref:
        needle = remove_code_ref.strip()
        for i in range(entry_idx + 1, sub_end + 1):
            if i < len(lines) and re.match(r"^\s*~", lines[i]):
                ref_val = lines[i].strip().lstrip("~").strip()
                if ref_val == needle or ref_val.startswith(needle + ":"):
                    lines.pop(i)
                    modified = True
                    sub_end -= 1
                    break

    if add_code_ref:
        already = any(
            add_code_ref in lines[i]
            for i in range(entry_idx + 1, min(sub_end + 2, len(lines)))
            if re.match(r"^\s*~", lines[i])
        )
        if not already:
            lines.insert(sub_end + 1, f"  ~ {add_code_ref}\n")
            modified = True

    if modified:
        spec_path.write_text("".join(lines), encoding="utf-8")
    return modified


def remove_spec_backlink_from_code(
    code_path: Path, slug: str, approx_line: int
) -> bool:
    """Remove or simplify a spec: slug comment near approx_line (1-indexed). Returns True if changed."""
    text = code_path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    spec_re = re.compile(r"spec:\s*" + re.escape(slug), re.I)
    lo = max(0, approx_line - 4)
    hi = min(len(lines), approx_line + 3)
    for i in range(lo, hi):
        if not spec_re.search(lines[i]):
            continue
        raw = lines[i]
        content = raw.strip()
        content = re.sub(r"^[/\*#]+\s*", "", content)
        if not content.lower().startswith("spec:"):
            continue
        all_slugs = [s.strip() for s in content[5:].split(",") if s.strip()]
        remaining = [s for s in all_slugs if s.lower() != slug.lower()]
        indent_str = raw[: len(raw) - len(raw.lstrip())]
        comment_char = "//" if raw.lstrip().startswith("//") else "#"
        if remaining:
            lines[i] = f"{indent_str}{comment_char} spec: {', '.join(remaining)}\n"
        else:
            lines.pop(i)
        code_path.write_text("".join(lines), encoding="utf-8")
        return True
    return False


def node_to_markdown(n: Node) -> str:
    """Serialize a node to spec format (column 0, 2-space sub-lines)."""
    lines: list[str] = []
    if n.type == "requirement":
        head = f"{n.slug}: {n.statement}"
        if n.planned:
            head += " [planned]"
        lines.append(head)
    elif n.type == "constraint":
        lines.append(f"{n.slug}: {n.statement}")
    else:
        lines.append(f"{n.slug}: {n.statement}")
    if n.provenance:
        lines.append(f"  > {n.provenance}")
    for a in n.assumptions:
        lines.append(f"  ! {a}")
    for ref in n.code_refs:
        lines.append(f"  ~ {ref}")
    for dep in n.depends_on:
        lines.append(f"  @ {dep}")
    for q in n.blocked_by:
        lines.append(f"  ? {q}")
    return "\n".join(lines) + "\n"


def section_for_type(t: NodeType) -> str:
    if t == "constraint":
        return "Constraints"
    if t == "question":
        return "Open Questions"
    return "Requirements"


def insert_entry_into_file(path: Path, section_name: str, block: str) -> None:
    """Append entry block to the given section. Creates section if missing."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    target = f"## {section_name}"
    insert_idx = len(lines)
    section_start = -1
    for i, line in enumerate(lines):
        if line.strip() == target:
            section_start = i
        elif section_start >= 0 and line.strip().startswith("## "):
            insert_idx = i
            break
        elif section_start >= 0:
            insert_idx = i + 1
    if section_start < 0:
        insert_idx = len(lines)
        sep = "\n" if lines and not lines[-1].endswith("\n") else ""
        new_section = f"\n## {section_name}\n\n{block}\n"
        path.write_text(text.rstrip() + sep + new_section, encoding="utf-8")
        return
    block_with_nl = block if block.endswith("\n") else block + "\n"
    lines.insert(insert_idx, block_with_nl)
    path.write_text("".join(lines), encoding="utf-8")
