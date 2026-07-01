import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from prov.commands.validate import cmd_validate
from prov.indexing import grep_spec_in_code


class SpecBacklinkTests(unittest.TestCase):
    def test_grep_spec_in_code_captures_requirement_constraint_and_question(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            backlink = "spe" + "c:"
            (root / "src" / "feature.py").write_text(
                f"# {backlink} feature-ready, C:security-boundary, Q:scope-question\n",
                encoding="utf-8",
            )
            (root / "AGENTS.md").write_text(
                f"# {backlink} ignored-agent-doc\n",
                encoding="utf-8",
            )
            (root / ".agents" / "skills").mkdir(parents=True)
            (root / ".agents" / "skills" / "SKILL.md").write_text(
                f"# {backlink} ignored-skill-doc\n",
                encoding="utf-8",
            )

            refs = grep_spec_in_code(root, root)

        self.assertEqual(
            refs,
            [
                ("src/feature.py", 1, "feature-ready"),
                ("src/feature.py", 1, "C:security-boundary"),
                ("src/feature.py", 1, "Q:scope-question"),
            ],
        )

    def test_validate_reports_missing_constraint_backlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec_dir = root / "prov"
            src_dir = root / "src"
            spec_dir.mkdir()
            src_dir.mkdir()
            (spec_dir / "CONTEXT.md").write_text(
                "# Test\n\n> test\n\n## Domain map\n\ncore prov/core.md\n",
                encoding="utf-8",
            )
            (spec_dir / "core.md").write_text(
                "# Core\n\n> core domain\n\n## Constraints\n\n"
                "C:known-rule: Known rule.\n"
                "  > user: \"known\"\n",
                encoding="utf-8",
            )
            backlink = "spe" + "c:"
            (src_dir / "feature.py").write_text(
                f"# {backlink} C:missing-rule\n",
                encoding="utf-8",
            )

            out = io.StringIO()
            with redirect_stdout(out):
                exit_code = cmd_validate(spec_dir, root)

        self.assertEqual(exit_code, 1)
        self.assertIn("phantom-slug", out.getvalue())
        self.assertIn("spec:C:missing-rule", out.getvalue())


if __name__ == "__main__":
    unittest.main()
