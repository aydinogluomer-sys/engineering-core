import json
import unittest
from pathlib import Path

from evals.run_manifest import validate_run_manifest


class RunManifestTests(unittest.TestCase):
    def test_proposed_manifest_is_concrete_but_not_executable(self):
        path = Path(__file__).with_name("live-run-manifest.template.json")
        manifest = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(validate_run_manifest(manifest), [])
        self.assertFalse(manifest["execution_permitted"])

    def test_authorization_cannot_be_inferred(self):
        manifest = json.loads(Path(__file__).with_name("live-run-manifest.template.json").read_text(encoding="utf-8"))
        manifest.update(status="AUTHORIZED", execution_permitted=True)
        self.assertTrue(validate_run_manifest(manifest))


if __name__ == "__main__":
    unittest.main()
