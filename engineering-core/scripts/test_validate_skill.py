from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

from validate_skill import validate  # noqa: E402


class ValidatorTests(unittest.TestCase):
    def copy_skill(self) -> Path:
        tmp = Path(tempfile.mkdtemp(prefix="engineering-core-test-"))
        dst = tmp / "engineering-core"
        shutil.copytree(ROOT, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        self.addCleanup(lambda: shutil.rmtree(tmp, ignore_errors=True))
        return dst

    def assert_invalid(self, mutator):
        root = self.copy_skill()
        mutator(root)
        errors = validate(root)
        self.assertTrue(errors, "mutated package unexpectedly passed validation")

    def test_real_package(self):
        self.assertEqual(validate(ROOT), [])

    def test_missing_reference(self):
        self.assert_invalid(lambda r: (r / "references/operating-model.md").unlink())

    def test_broken_local_link(self):
        def mutate(r):
            p = r / "SKILL.md"
            p.write_text(p.read_text(encoding="utf-8") + "\n[broken](references/nope.md)\n", encoding="utf-8")
        self.assert_invalid(mutate)

    def test_oversized_entrypoint(self):
        def mutate(r):
            p = r / "SKILL.md"
            p.write_text(p.read_text(encoding="utf-8") + ("\nextra" * 250), encoding="utf-8")
        self.assert_invalid(mutate)

    def test_external_tool_made_mandatory(self):
        def mutate(r):
            p = r / "references/integrations.md"
            p.write_text(p.read_text(encoding="utf-8") + "\nCodeGraph is a mandatory prerequisite.\n", encoding="utf-8")
        self.assert_invalid(mutate)

    def test_deterministic_safety_guarantee(self):
        def mutate(r):
            p = r / "references/safety-profiles.md"
            p.write_text(p.read_text(encoding="utf-8") + "\nThis skill guarantees prevention of unsafe actions.\n", encoding="utf-8")
        self.assert_invalid(mutate)

    def test_missing_fast_path(self):
        def mutate(r):
            p = r / "SKILL.md"
            text = p.read_text(encoding="utf-8").replace("## Small-task fast path", "## Tiny workflow")
            p.write_text(text, encoding="utf-8")
        self.assert_invalid(mutate)

    def test_missing_high_risk_profile(self):
        def mutate(r):
            p = r / "references/safety-profiles.md"
            text = p.read_text(encoding="utf-8").replace("## 3. Authentication / authorization profile", "## 3. Identity notes")
            p.write_text(text, encoding="utf-8")
        self.assert_invalid(mutate)

    def test_active_mcp_config(self):
        def mutate(r):
            (r / ".mcp.json").write_text("{}", encoding="utf-8")
        self.assert_invalid(mutate)

    def test_invalid_frontmatter(self):
        def mutate(r):
            p = r / "SKILL.md"
            text = p.read_text(encoding="utf-8").replace("name: engineering-core", "name: Engineering Core")
            p.write_text(text, encoding="utf-8")
        self.assert_invalid(mutate)

    def test_over_broad_frontmatter(self):
        def mutate(r):
            p = r / "SKILL.md"
            text = p.read_text(encoding="utf-8").replace("---\n\n# Engineering Core", "allowed-tools: Bash\n---\n\n# Engineering Core", 1)
            p.write_text(text, encoding="utf-8")
        self.assert_invalid(mutate)

    def test_missing_example(self):
        self.assert_invalid(lambda r: (r / "examples/large-spec-execution.md").unlink())

    def test_stale_provenance(self):
        def mutate(r):
            p = r / "references/source-synthesis.md"
            text = p.read_text(encoding="utf-8").replace("kingbootoshi/cartographer", "miltonian/cartographer")
            p.write_text(text, encoding="utf-8")
        self.assert_invalid(mutate)

    def test_activation_guarantee(self):
        def mutate(r):
            p = r / "references/integrations.md"
            p.write_text(p.read_text(encoding="utf-8") + "\nThis guarantees model behavior.\n", encoding="utf-8")
        self.assert_invalid(mutate)

    def test_critical_route_missing(self):
        def mutate(r):
            p = r / "references/verification-review.md"
            text = p.read_text(encoding="utf-8").replace(
                "moderate, high, or critical-risk work",
                "moderate/high-risk work",
            )
            p.write_text(text, encoding="utf-8")
        self.assert_invalid(mutate)

    def test_redundant_confirmation_rule_missing(self):
        def mutate(r):
            p = r / "references/operating-model.md"
            text = p.read_text(encoding="utf-8").replace(
                "proceed without redundant confirmation",
                "request explicit confirmation again",
            )
            p.write_text(text, encoding="utf-8")
        self.assert_invalid(mutate)


if __name__ == "__main__":
    unittest.main(verbosity=2)
