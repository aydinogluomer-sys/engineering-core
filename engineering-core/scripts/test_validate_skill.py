from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

from validate_skill import classify_import_roots, validate  # noqa: E402


class ValidatorTests(unittest.TestCase):
    def copy_skill(self) -> Path:
        tmp = Path(tempfile.mkdtemp(prefix="engineering-core-test-"))
        self.addCleanup(lambda: shutil.rmtree(tmp, ignore_errors=True))
        dst = tmp / "engineering-core"
        shutil.copytree(ROOT, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        return dst

    def assert_invalid(self, mutator):
        root = self.copy_skill()
        mutator(root)
        errors = validate(root)
        self.assertTrue(errors, "mutated package unexpectedly passed validation")

    def add_validator_import(self, statement: str) -> Path:
        root = self.copy_skill()
        path = root / "scripts/validate_skill.py"
        text = path.read_text(encoding="utf-8")
        anchor = "from __future__ import annotations\n"
        path.write_text(text.replace(anchor, anchor + statement + "\n", 1), encoding="utf-8")
        return root

    def test_real_package(self):
        self.assertEqual(validate(ROOT), [])

    def test_stdlib_and_nested_stdlib_imports_are_accepted(self):
        root = self.add_validator_import("import os\nimport urllib.parse")
        self.assertEqual(validate(root), [])

    def test_future_and_builtin_imports_are_accepted(self):
        classifications = classify_import_roots(ROOT / "scripts/validate_skill.py")
        self.assertEqual(classifications["__future__"], "future/builtin")
        self.assertEqual(classifications["sys"], "future/builtin")

    def test_local_validator_import_is_accepted(self):
        classifications = classify_import_roots(ROOT / "scripts/test_validate_skill.py")
        self.assertEqual(classifications["validate_skill"], "local")

    def test_arbitrary_unknown_external_import_is_rejected(self):
        root = self.add_validator_import("import some_unlisted_external")
        errors = validate(root)
        self.assertTrue(any("some_unlisted_external" in error for error in errors))

    def test_common_external_imports_are_rejected(self):
        for statement, expected in [
            ("import numpy", "numpy"),
            ("import httpx", "httpx"),
            ("from requests import Session", "requests"),
            ("from pydantic import BaseModel", "pydantic"),
        ]:
            with self.subTest(statement=statement):
                root = self.add_validator_import(statement)
                errors = validate(root)
                self.assertTrue(any(expected in error for error in errors))

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

    def test_heading_rename_with_policy_id_passes(self):
        def mutate(r):
            p = r / "SKILL.md"
            text = p.read_text(encoding="utf-8").replace("## Adaptive Fast-Exit", "## Accelerated local workflow")
            p.write_text(text, encoding="utf-8")
        root = self.copy_skill()
        mutate(root)
        self.assertEqual(validate(root), [])

    def test_prose_rewrite_with_policy_id_passes(self):
        def mutate(r):
            p = r / "references/operating-model.md"
            text = p.read_text(encoding="utf-8").replace("Diff size is not a risk proxy.", "Never infer consequence from patch dimensions.")
            p.write_text(text, encoding="utf-8")
        root = self.copy_skill()
        mutate(root)
        self.assertEqual(validate(root), [])

    def test_missing_policy_id_fails(self):
        def mutate(r):
            p = r / "SKILL.md"
            p.write_text(p.read_text(encoding="utf-8").replace("<!-- policy-id: fast-path -->", ""), encoding="utf-8")
        self.assert_invalid(mutate)

    def test_duplicate_policy_id_fails(self):
        def mutate(r):
            p = r / "SKILL.md"
            p.write_text(p.read_text(encoding="utf-8") + "\n<!-- policy-id: fast-path -->\n", encoding="utf-8")
        self.assert_invalid(mutate)

    def test_wrong_policy_owner_fails(self):
        def mutate(r):
            source = r / "SKILL.md"
            target = r / "references/operating-model.md"
            source.write_text(source.read_text(encoding="utf-8").replace("<!-- policy-id: fast-path -->", ""), encoding="utf-8")
            target.write_text(target.read_text(encoding="utf-8") + "\n<!-- policy-id: fast-path -->\n", encoding="utf-8")
        self.assert_invalid(mutate)

    def test_unknown_extra_policy_id_is_allowed(self):
        root = self.copy_skill()
        p = root / "references/operating-model.md"
        p.write_text(p.read_text(encoding="utf-8") + "\n<!-- policy-id: future-extension -->\n", encoding="utf-8")
        self.assertEqual(validate(root), [])

    def test_malformed_policy_id_fails(self):
        def mutate(r):
            p = r / "SKILL.md"
            p.write_text(p.read_text(encoding="utf-8") + "\n<!-- policy-id: Bad ID -->\n", encoding="utf-8")
        self.assert_invalid(mutate)

    def test_missing_team_mode_policy_id_fails(self):
        def mutate(r):
            p = r / "references/formal-spec-team-mode.md"
            p.write_text(p.read_text(encoding="utf-8").replace("<!-- policy-id: spec-compiler -->", ""), encoding="utf-8")
        self.assert_invalid(mutate)

    def test_team_mode_policy_id_wrong_owner_fails(self):
        def mutate(r):
            source = r / "references/formal-spec-team-mode.md"
            target = r / "references/operating-model.md"
            source.write_text(source.read_text(encoding="utf-8").replace("<!-- policy-id: two-key-closure -->", ""), encoding="utf-8")
            target.write_text(target.read_text(encoding="utf-8") + "\n<!-- policy-id: two-key-closure -->\n", encoding="utf-8")
        self.assert_invalid(mutate)

    def test_team_mode_heading_and_prose_rewrite_passes(self):
        root = self.copy_skill()
        p = root / "references/formal-spec-team-mode.md"
        text = p.read_text(encoding="utf-8").replace("## 6. Finding Ledger", "## 6. Findings lifecycle").replace("Plain rejection", "Unsupported rejection")
        p.write_text(text, encoding="utf-8")
        self.assertEqual(validate(root), [])

    def test_eval_tree_cannot_enter_runtime_package(self):
        def mutate(r):
            path = r / "evals/team.json"
            path.parent.mkdir()
            path.write_text("{}", encoding="utf-8")
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

    def test_validator_uses_no_fuzzy_semantics(self):
        text = (ROOT / "scripts/validate_skill.py").read_text(encoding="utf-8").lower()
        for forbidden in ("difflib", "tfidf", "tf-idf", "embedding", "sentence_transformer", "sklearn"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, text)

    def test_activation_guarantee(self):
        def mutate(r):
            p = r / "references/integrations.md"
            p.write_text(p.read_text(encoding="utf-8") + "\nThis guarantees model behavior.\n", encoding="utf-8")
        self.assert_invalid(mutate)


if __name__ == "__main__":
    unittest.main(verbosity=2)
