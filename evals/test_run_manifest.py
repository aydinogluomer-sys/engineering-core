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

    def test_pressure_categories_cannot_be_removed(self):
        manifest = json.loads(Path(__file__).with_name("live-run-manifest.template.json").read_text(encoding="utf-8"))
        manifest["pressure_campaign"]["categories"].pop()
        self.assertTrue(any("pressure categories" in error for error in validate_run_manifest(manifest)))

    def test_activation_threshold_cannot_be_weakened(self):
        manifest = json.loads(Path(__file__).with_name("live-run-manifest.template.json").read_text(encoding="utf-8"))
        manifest["activation_gate"]["recall_min"] = 0.5
        self.assertTrue(any("activation thresholds" in error for error in validate_run_manifest(manifest)))

    def test_budget_caps_must_be_positive(self):
        manifest = json.loads(Path(__file__).with_name("live-run-manifest.template.json").read_text(encoding="utf-8"))
        manifest["per_suite_budget_caps_usd"]["pressure_l4"] = 0
        self.assertTrue(any("per_suite_budget_caps_usd" in error for error in validate_run_manifest(manifest)))

    def test_category_and_team_names_are_frozen(self):
        manifest = json.loads(Path(__file__).with_name("live-run-manifest.template.json").read_text(encoding="utf-8"))
        manifest["activation_gate"]["critical_categories"] = ["bogus"] * 5
        manifest["team_gate"]["scenarios"] = ["bogus"] * 5
        errors = validate_run_manifest(manifest)
        self.assertTrue(any("category gates" in error for error in errors))
        self.assertTrue(any("Team gate" in error for error in errors))

    def test_pressure_gate_and_provenance_cannot_be_empty(self):
        manifest = json.loads(Path(__file__).with_name("live-run-manifest.template.json").read_text(encoding="utf-8"))
        manifest["pressure_campaign"]["quality_gate"] = ""
        manifest["pressure_campaign"]["provenance"] = ""
        self.assertTrue(any("pressure gate and provenance" in error for error in validate_run_manifest(manifest)))

    def test_status_and_budget_cap_maps_are_exactly_frozen(self):
        manifest = json.loads(Path(__file__).with_name("live-run-manifest.template.json").read_text(encoding="utf-8"))
        manifest["status"] = "GARBAGE"
        manifest["per_model_budget_caps_usd"] = {"haiku": 1}
        manifest["per_suite_budget_caps_usd"] = {"pressure_l4": 1}
        errors = validate_run_manifest(manifest)
        self.assertTrue(any("status must be exactly" in error for error in errors))
        self.assertTrue(any("per_model_budget" in error for error in errors))
        self.assertTrue(any("per_suite_budget" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
