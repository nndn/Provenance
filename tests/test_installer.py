"""Tests for prov.installer and the cmd_init agent bootstrap."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from prov import installer
from prov.commands.init import cmd_init

SKILL_NAMES = sorted(installer.load_skills())


def _tree(root: Path) -> "dict[str, str]":
    """Snapshot of every file under root: {relative path: content}."""
    return {
        str(p.relative_to(root)): p.read_text(encoding="utf-8")
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def test_fresh_install_creates_all_asset_sets(tmp_path):
    report = installer.install(tmp_path)

    assert SKILL_NAMES  # packaged skills are readable
    for skills_dir in (".claude/skills", ".agents/skills"):
        for name in SKILL_NAMES:
            dest = tmp_path / skills_dir / name / "SKILL.md"
            assert dest.is_file()
            assert dest.read_text(encoding="utf-8") == installer.load_skills()[name]
    for rules_file in ("CLAUDE.md", "AGENTS.md"):
        text = (tmp_path / rules_file).read_text(encoding="utf-8")
        assert text.count(installer.MARKER_START) == 1
        assert text.count(installer.MARKER_END) == 1
        assert "Self-heal" in text

    actions = {a for items in report.values() for _, a in items}
    assert actions == {"installed", "created"}


def test_rerun_is_idempotent(tmp_path):
    installer.install(tmp_path)
    before = _tree(tmp_path)

    report = installer.install(tmp_path)

    assert _tree(tmp_path) == before
    for items in report.values():
        for _, action in items:
            assert action == "up to date"
    for rules_file in ("CLAUDE.md", "AGENTS.md"):
        text = (tmp_path / rules_file).read_text(encoding="utf-8")
        assert text.count(installer.MARKER_START) == 1
        assert text.count(installer.MARKER_END) == 1


def test_marker_block_replaced_not_duplicated_on_template_change(tmp_path, monkeypatch):
    installer.install(tmp_path)
    old_body = installer.load_rules_template()
    monkeypatch.setattr(installer, "load_rules_template", lambda: "NEW RULES BODY")

    report = installer.install(tmp_path)

    for rules_file in ("CLAUDE.md", "AGENTS.md"):
        text = (tmp_path / rules_file).read_text(encoding="utf-8")
        assert text.count(installer.MARKER_START) == 1
        assert text.count(installer.MARKER_END) == 1
        assert "NEW RULES BODY" in text
        assert old_body.strip("\n") not in text
    rules_actions = {
        action for items in report.values() for path, action in items
        if path in ("CLAUDE.md", "AGENTS.md")
    }
    assert rules_actions == {"updated"}


def test_user_content_around_block_survives(tmp_path, monkeypatch):
    claude = tmp_path / "CLAUDE.md"
    claude.write_text("# My project notes\n\nKeep these.\n", encoding="utf-8")

    installer.install(tmp_path)
    text = claude.read_text(encoding="utf-8")
    assert text.startswith("# My project notes\n\nKeep these.\n")
    assert text.count(installer.MARKER_START) == 1

    # User adds content after the block; a template change must preserve both sides.
    claude.write_text(text + "\n## Trailing notes\n", encoding="utf-8")
    monkeypatch.setattr(installer, "load_rules_template", lambda: "NEW RULES BODY")
    installer.install(tmp_path)
    text = claude.read_text(encoding="utf-8")
    assert text.startswith("# My project notes\n\nKeep these.\n")
    assert text.endswith("\n## Trailing notes\n")
    assert text.count(installer.MARKER_START) == 1
    assert "NEW RULES BODY" in text


def test_check_mode_writes_nothing_and_returns_codes(tmp_path):
    spec_dir = tmp_path / "prov"

    rc = cmd_init(spec_dir, tmp_path, check=True)
    assert rc == 1
    assert _tree(tmp_path) == {}

    assert cmd_init(spec_dir, tmp_path) == 0
    before = _tree(tmp_path)
    rc = cmd_init(spec_dir, tmp_path, check=True)
    assert rc == 0
    assert _tree(tmp_path) == before

    # An outdated skill flips check back to 1 without writes.
    skill = tmp_path / ".claude/skills" / SKILL_NAMES[0] / "SKILL.md"
    skill.write_text("modified\n", encoding="utf-8")
    before = _tree(tmp_path)
    assert cmd_init(spec_dir, tmp_path, check=True) == 1
    assert _tree(tmp_path) == before


def test_force_overwrites_modified_skill(tmp_path):
    installer.install(tmp_path)
    name = SKILL_NAMES[0]
    rel = ".claude/skills/{}/SKILL.md".format(name)
    dest = tmp_path / rel
    dest.write_text("locally modified\n", encoding="utf-8")

    report = installer.install(tmp_path)
    assert dict(report["claude"])[rel] == "outdated (--force to update)"
    assert dest.read_text(encoding="utf-8") == "locally modified\n"

    report = installer.install(tmp_path, force=True)
    assert dict(report["claude"])[rel] == "updated"
    assert dest.read_text(encoding="utf-8") == installer.load_skills()[name]


def test_damaged_markers_never_destroy_user_content(tmp_path):
    claude = tmp_path / "CLAUDE.md"
    damaged = (
        "# Notes\n\n"
        + installer.MARKER_START
        + "\nold block whose end marker was deleted\n\n"
        + "USER CONTENT THAT MUST SURVIVE\n"
    )
    claude.write_text(damaged, encoding="utf-8")

    # Repeated runs (agents self-heal at session start) must refuse to touch
    # the damaged file rather than append a second block and later swallow
    # everything between the two start markers.
    for _ in range(2):
        report = installer.install(tmp_path)
        assert claude.read_text(encoding="utf-8") == damaged
        assert dict(report["claude"])["CLAUDE.md"] == installer.DAMAGED

    assert dict(installer.check_status(tmp_path)["claude"])["CLAUDE.md"] == installer.DAMAGED
    assert cmd_init(tmp_path / "prov", tmp_path, check=True) == 1


def test_cmd_init_scaffold_and_standard_selection(tmp_path, capsys):
    spec_dir = tmp_path / "prov"

    assert cmd_init(spec_dir, tmp_path, open_std=False) == 0
    out = capsys.readouterr().out
    assert "Created CONTEXT.md. Edit it with your project details." in out
    assert (tmp_path / "CLAUDE.md").is_file()
    assert not (tmp_path / "AGENTS.md").exists()
    assert not (tmp_path / ".agents").exists()

    assert cmd_init(spec_dir, tmp_path, open_std=False) == 0
    out = capsys.readouterr().out
    assert "CONTEXT.md already exists." in out
    assert "Next steps:" not in out
