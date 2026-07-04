"""Install packaged agent assets (skills + rules) into a repository."""
from __future__ import annotations

from importlib.resources import files
from pathlib import Path

MARKER_START = "<!-- prov:agent-rules:start -->"
MARKER_END = "<!-- prov:agent-rules:end -->"

RULES_TEMPLATE = "project-rules.md"

# Standard name -> install layout, relative to repo root.
# spec: agent-assets-install
STANDARDS: "dict[str, dict[str, str]]" = {
    "claude": {"skills_dir": ".claude/skills", "rules_file": "CLAUDE.md"},
    "open": {"skills_dir": ".agents/skills", "rules_file": "AGENTS.md"},
}


def load_skills() -> "dict[str, str]":
    """Packaged skills: {skill-name: SKILL.md content}."""
    skills: "dict[str, str]" = {}
    root = files("prov").joinpath("skills")
    for entry in sorted(root.iterdir(), key=lambda e: e.name):
        if not entry.is_dir():
            continue
        doc = entry.joinpath("SKILL.md")
        if doc.is_file():
            skills[entry.name] = doc.read_text(encoding="utf-8")
    return skills


def load_rules_template() -> str:
    """Packaged body of the managed rules block."""
    return files("prov").joinpath("rules").joinpath(RULES_TEMPLATE).read_text(encoding="utf-8")


def render_block(body: str) -> str:
    """Wrap a rules body in the managed marker block."""
    return "{}\n{}\n{}".format(MARKER_START, body.strip("\n"), MARKER_END)


DAMAGED = "damaged markers — fix or remove the prov:agent-rules markers, then re-run"


# spec: rules-managed-block
def _find_block(text: str) -> "tuple[int, int] | None":
    """Span (start, end) of the marker block in text, or None if absent.

    Raises ValueError on unbalanced or repeated markers — writing anything
    around a damaged block risks destroying user content.
    """
    starts = text.count(MARKER_START)
    ends = text.count(MARKER_END)
    if starts == 0 and ends == 0:
        return None
    if starts != 1 or ends != 1:
        raise ValueError("unbalanced prov:agent-rules markers")
    start = text.find(MARKER_START)
    end = text.find(MARKER_END)
    if end < start:
        raise ValueError("prov:agent-rules end marker precedes start marker")
    return start, end + len(MARKER_END)


def _skill_status(dest: Path, content: str) -> str:
    if not dest.is_file():
        return "missing"
    if dest.read_text(encoding="utf-8") == content:
        return "up to date"
    return "outdated"


def _rules_status(dest: Path, block: str) -> str:
    if not dest.is_file():
        return "missing"
    text = dest.read_text(encoding="utf-8")
    try:
        span = _find_block(text)
    except ValueError:
        return DAMAGED
    if span is None:
        return "missing"
    if text[span[0]:span[1]] == block:
        return "up to date"
    return "outdated"


def _apply_skill(dest: Path, content: str, force: bool) -> str:
    if not dest.is_file():
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
        return "installed"
    if dest.read_text(encoding="utf-8") == content:
        return "up to date"
    if force:
        dest.write_text(content, encoding="utf-8")
        return "updated"
    return "outdated (--force to update)"


def _apply_rules(dest: Path, block: str) -> str:
    if not dest.is_file():
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(block + "\n", encoding="utf-8")
        return "created"
    text = dest.read_text(encoding="utf-8")
    try:
        span = _find_block(text)
    except ValueError:
        return DAMAGED
    if span is None:
        if text.strip():
            new = text.rstrip("\n") + "\n\n" + block + "\n"
        else:
            new = block + "\n"
        dest.write_text(new, encoding="utf-8")
        return "rules block added"
    new = text[: span[0]] + block + text[span[1]:]
    if new == text:
        return "up to date"
    dest.write_text(new, encoding="utf-8")
    return "updated"


def check_status(repo_root: Path) -> "dict[str, list[tuple[str, str]]]":
    """Status of agent assets per standard: {standard: [(relative path, status), ...]}.

    Statuses: 'up to date', 'outdated', 'missing'. Writes nothing.
    """
    skills = load_skills()
    block = render_block(load_rules_template())
    report: "dict[str, list[tuple[str, str]]]" = {}
    for std, layout in STANDARDS.items():
        items: "list[tuple[str, str]]" = []
        for name, content in skills.items():
            rel = "{}/{}/SKILL.md".format(layout["skills_dir"], name)
            items.append((rel, _skill_status(repo_root / rel, content)))
        rules_rel = layout["rules_file"]
        items.append((rules_rel, _rules_status(repo_root / rules_rel, block)))
        report[std] = items
    return report


def install(
    repo_root: Path,
    claude: bool = True,
    open_std: bool = True,
    force: bool = False,
) -> "dict[str, list[tuple[str, str]]]":
    """Install agent assets. Returns {standard: [(relative path, action), ...]}.

    Actions: 'installed', 'created', 'rules block added', 'updated',
    'up to date', 'outdated (--force to update)', DAMAGED (never writes
    to a file with unbalanced markers). Idempotent.
    """
    skills = load_skills()
    block = render_block(load_rules_template())
    selected = [s for s, on in (("claude", claude), ("open", open_std)) if on]
    report: "dict[str, list[tuple[str, str]]]" = {}
    for std in selected:
        layout = STANDARDS[std]
        items: "list[tuple[str, str]]" = []
        for name, content in skills.items():
            rel = "{}/{}/SKILL.md".format(layout["skills_dir"], name)
            items.append((rel, _apply_skill(repo_root / rel, content, force)))
        rules_rel = layout["rules_file"]
        items.append((rules_rel, _apply_rules(repo_root / rules_rel, block)))
        report[std] = items
    return report
