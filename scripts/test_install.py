from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from install import install, rollback, tree_digest
import install as installer


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.raw = Path(tempfile.mkdtemp(prefix="installer-test-"))
        self.addCleanup(lambda: shutil.rmtree(self.raw, ignore_errors=True))
        self.source = self.raw / "source"
        package = self.source / "engineering-core"
        (package / "scripts").mkdir(parents=True)
        (package / "SKILL.md").write_text("---\nname: engineering-core\ndescription: test\n---\n# test\n", encoding="utf-8")
        (package / "scripts/validate_skill.py").write_text("import sys\nraise SystemExit(0)\n", encoding="utf-8")
        for command in (["git","init","-q"],["git","config","user.email","test@example.invalid"],["git","config","user.name","Test"],["git","add","."],["git","commit","-qm","initial"]):
            subprocess.run(command, cwd=self.source, check=True)
        self.ref = subprocess.run(["git","rev-parse","HEAD"], cwd=self.source, text=True, capture_output=True, check=True).stdout.strip()
        self.destination = self.raw / "installed" / "engineering-core"

    def test_fresh_noop_drift_update_and_rollback(self):
        self.assertEqual(install(str(self.source), self.ref, self.destination, False), "INSTALLED")
        self.assertEqual(install(str(self.source), self.ref, self.destination, False), "NO_OP")
        (self.destination / "SKILL.md").write_text("local customization", encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "local drift"):
            install(str(self.source), self.ref, self.destination, False)
        self.assertEqual(install(str(self.source), self.ref, self.destination, True), "UPDATED")
        self.assertEqual(rollback(self.destination), "ROLLED_BACK")
        self.assertEqual((self.destination / "SKILL.md").read_text(encoding="utf-8"), "local customization")

    def test_destination_must_not_create_nested_package(self):
        with self.assertRaisesRegex(RuntimeError, "end with engineering-core"):
            install(str(self.source), self.ref, self.raw / "wrong", False)

    def test_staging_failure_leaves_existing_destination_in_place(self):
        self.assertEqual(install(str(self.source), self.ref, self.destination, False), "INSTALLED")
        before = tree_digest(self.destination)
        (self.source / "engineering-core/SKILL.md").write_text("---\nname: engineering-core\ndescription: changed\n---\n# changed\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=self.source, check=True)
        subprocess.run(["git", "commit", "-qm", "changed"], cwd=self.source, check=True)
        changed_ref = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.source, text=True, capture_output=True, check=True).stdout.strip()
        with mock.patch.object(installer.shutil, "copytree", side_effect=OSError("injected staging failure")):
            with self.assertRaisesRegex(OSError, "injected staging failure"):
                install(str(self.source), changed_ref, self.destination, False)
        self.assertTrue(self.destination.is_dir())
        self.assertEqual(tree_digest(self.destination), before)
        self.assertFalse(self.destination.with_name("engineering-core.backup").exists())

    def test_equal_content_new_ref_refreshes_provenance(self):
        self.assertEqual(install(str(self.source), self.ref, self.destination, False), "INSTALLED")
        subprocess.run(["git", "commit", "--allow-empty", "-qm", "same content new provenance"], cwd=self.source, check=True)
        newer_ref = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.source, text=True, capture_output=True, check=True).stdout.strip()
        self.assertEqual(install(str(self.source), newer_ref, self.destination, False), "UPDATED_METADATA")
        metadata = json.loads((self.destination / ".engineering-core-install.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["resolved_commit"], newer_ref)
        self.assertEqual(metadata["ref"], newer_ref)


if __name__ == "__main__":
    unittest.main()
