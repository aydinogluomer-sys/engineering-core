from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from trust import capture_scope, git_inventory, materialize_oracle, run_trusted_oracle, validate_scope


class TrustBoundaryTests(unittest.TestCase):
    def repo(self) -> Path:
        root = Path(tempfile.mkdtemp(prefix="trust-test-"))
        self.addCleanup(lambda: shutil.rmtree(root, ignore_errors=True))
        (root / "app.py").write_text("def allowed(x):\n    return True\n", encoding="utf-8")
        (root / "test_contract.py").write_text("assert True\n", encoding="utf-8")
        (root / "protected user file.txt").write_text("keep\n", encoding="utf-8")
        (root / ".gitignore").write_text("ignored.txt\n", encoding="utf-8")
        for command in (["git", "init", "-q"], ["git", "config", "user.email", "eval@example.invalid"], ["git", "config", "user.name", "Eval"], ["git", "add", "."], ["git", "commit", "-qm", "baseline"]):
            subprocess.run(command, cwd=root, check=True, capture_output=True)
        return root

    def test_candidate_visible_test_cannot_replace_trusted_oracle(self):
        root = self.repo()
        oracle = materialize_oracle(root.parent / (root.name + "-oracle"), "acceptance", "import pathlib, runpy, sys\nroot=pathlib.Path(sys.argv[1]); candidate=runpy.run_path(str(root/'app.py'))\nassert candidate['allowed']('denied') is False\n")
        (root / "test_contract.py").write_text("pass\n", encoding="utf-8")
        result = run_trusted_oracle(oracle, root)
        self.assertNotEqual(result.returncode, 0)
        (root / "app.py").write_text("def allowed(x):\n    return x != 'denied'\n", encoding="utf-8")
        self.assertEqual(run_trusted_oracle(oracle, root).returncode, 0)

    def test_scope_rejects_unrelated_staged_ignored_and_protected_changes(self):
        root = self.repo()
        manifest = capture_scope(root, protected_paths=["protected user file.txt", "test_contract.py"], allowed_changed_paths=["app.py"], expected_changed_paths=["app.py"], forbidden_paths=["requirements.txt"])
        (root / "app.py").write_text("def allowed(x):\n    return x != 'denied'\n", encoding="utf-8")
        self.assertEqual(validate_scope(root, manifest)[0], [])
        (root / "ignored.txt").write_text("hidden\n", encoding="utf-8")
        (root / "protected user file.txt").write_text("changed\n", encoding="utf-8")
        subprocess.run(["git", "add", "app.py"], cwd=root, check=True)
        failures, _ = validate_scope(root, manifest)
        self.assertTrue(any("index" in item for item in failures))
        self.assertTrue(any("ignored.txt" in item for item in failures))
        self.assertTrue(any("protected file" in item for item in failures))

    def test_git_inventory_supports_spaces_and_rename(self):
        root = self.repo()
        subprocess.run(["git", "mv", "protected user file.txt", "renamed user file.txt"], cwd=root, check=True)
        entries = git_inventory(root)
        self.assertTrue(any(entry["path"] == "renamed user file.txt" and entry.get("source_path") == "protected user file.txt" for entry in entries))

    def test_oracle_hash_change_is_blocking(self):
        root = self.repo()
        oracle = materialize_oracle(root.parent / (root.name + "-oracle"), "acceptance", "assert True\n")
        oracle.path.write_text("assert False\n", encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "integrity"):
            run_trusted_oracle(oracle, root)


if __name__ == "__main__":
    unittest.main(verbosity=2)
