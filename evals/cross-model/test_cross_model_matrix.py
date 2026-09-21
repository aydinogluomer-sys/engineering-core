from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "evals"))
from cross_model import UNOBSERVED, FAILURE_CLASSES, aggregate_provenance, load_registry, model_provenance, validate_limits, validate_report  # noqa: E402

spec = importlib.util.spec_from_file_location("mode_eval", HERE / "run_mode_selection_eval.py")
mode_eval = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(mode_eval)


class CrossModelTests(unittest.TestCase):
    def setUp(self):
        self.registry = load_registry(HERE / "model_registry.json")

    def test_registry_has_exact_roles(self):
        self.assertEqual(set(self.registry), {"haiku", "sonnet", "opus", "fable"})
        self.assertFalse(self.registry["haiku"]["team_gate_required"])
        self.assertTrue(all(self.registry[name]["team_gate_required"] for name in ("sonnet", "opus", "fable")))

    def test_unobserved_model_is_never_inferred(self):
        value = model_provenance("fable", [], self.registry)
        self.assertEqual(value["effective_model"], UNOBSERVED)
        self.assertFalse(value["effective_model_observed"])
        self.assertEqual(value["fallback_detected"], "unknown")

    def test_observed_fallback_is_explicit(self):
        value = model_provenance("fable", [{"type": "system", "model": "claude-opus-4"}], self.registry)
        self.assertTrue(value["effective_model_observed"])
        self.assertTrue(value["fallback_detected"])

    def test_inconsistent_observed_models_are_unobserved(self):
        events = [{"model": "claude-fable-1"}, {"message": {"model": "claude-opus-4"}}]
        value = model_provenance("fable", events, self.registry)
        self.assertEqual(value["effective_model"], UNOBSERVED)
        self.assertFalse(value["effective_model_observed"])
        self.assertIn("inconsistent", value["fallback_reason"])

    def test_partially_observed_report_is_unobserved(self):
        observed = model_provenance("sonnet", [{"model": "claude-sonnet-5"}], self.registry)
        missing = model_provenance("sonnet", [], self.registry)
        value = aggregate_provenance("sonnet", [observed, missing])
        self.assertFalse(value["effective_model_observed"])
        self.assertEqual(value["effective_model"], UNOBSERVED)
        self.assertEqual(value["fallback_detected"], "unknown")

    def test_report_schema_rejects_provenance_overclaim(self):
        report = {
            "schema_version": 2, "commit_sha": "abc", "dataset_version": "v1",
            "claude_code_version": "x", "os": "test", "requested_model": "fable",
            "effective_model": "claude-fable", "effective_model_observed": False,
            "fallback_detected": "unknown", "fallback_reason": "not observable",
            "evaluation_type": "core", "results": [],
        }
        self.assertTrue(any("UNOBSERVED" in error for error in validate_report(report, self.registry)))

    def test_schema_file_and_failure_taxonomy(self):
        schema = json.loads((HERE / "schemas/cross-model-report.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["schema_version"]["const"], 2)
        self.assertIn("effective_model_unknown", FAILURE_CLASSES)
        self.assertIn("scorer", FAILURE_CLASSES)

    def test_complete_report_passes_validator(self):
        provenance = model_provenance("sonnet", [{"model": "claude-sonnet-5"}], self.registry)
        report = {
            "schema_version": 2, "commit_sha": "abc", "dataset_version": "v1",
            "claude_code_version": "x", "os": "test", "evaluation_type": "mode_selection",
            "results": [{
                "scenario_id": "M-01", "status": "PASS", "activation_tier": "A",
                "selected_mode": "Adaptive Fast-Exit", "expected_mode": "Adaptive Fast-Exit",
                "cost_usd": 0.01, "elapsed_seconds": 1.0, "failure_class": None,
                "evidence": {}, "limitations": [], **provenance,
            }], **provenance,
        }
        self.assertEqual(validate_report(report, self.registry), [])

    def test_mode_dataset_covers_three_modes_and_abort(self):
        rows = json.loads((HERE / "mode-selection.json").read_text(encoding="utf-8"))
        self.assertEqual(len(rows), 10)
        self.assertEqual({row["expected_mode"] for row in rows}, mode_eval.MODES)
        self.assertTrue(any(row["abort"] for row in rows))

    def test_mode_fixture_is_an_isolated_repository(self):
        raw = Path(tempfile.mkdtemp(prefix="mode-fixture-test-"))
        self.addCleanup(lambda: shutil.rmtree(raw, ignore_errors=True))
        fixture = mode_eval.make_fixture(raw)
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=fixture, text=True, capture_output=True, check=True).stdout.strip()
        self.assertEqual(Path(top).resolve(), fixture.resolve())

    def test_mode_tier_a_requires_structured_skill_event(self):
        self.assertFalse(mode_eval.skill_invoked([{"type": "result", "result": "engineering-core"}]))
        events = [{"message": {"content": [{"type": "tool_use", "name": "Skill", "input": {"skill": "engineering-core"}}]}}]
        self.assertTrue(mode_eval.skill_invoked(events))

    def test_mode_scorer_rejects_high_risk_fast_exit(self):
        case = {"expected_mode": "Standard Engineering Mode", "expected_risk": "High", "abort": False}
        failures = mode_eval.score_decision(case, {"selected_mode": "Adaptive Fast-Exit", "risk": "Low", "fast_exit_aborted": False})
        self.assertGreaterEqual(len(failures), 2)

    def test_mode_scorer_accepts_abort(self):
        case = {"expected_mode": "Standard Engineering Mode", "expected_risk": "High", "abort": True}
        decision = {"selected_mode": "Standard Engineering Mode", "risk": "High", "fast_exit_aborted": True}
        self.assertEqual(mode_eval.score_decision(case, decision), [])

    def test_mode_metrics_expose_required_rates(self):
        rows = [
            {"status": "PASS", "expected_mode": "Adaptive Fast-Exit", "selected_mode": "Adaptive Fast-Exit", "evidence": {"abort_expected": False, "abort_observed": False}},
            {"status": "FAIL", "expected_mode": "Standard Engineering Mode", "selected_mode": "Adaptive Fast-Exit", "evidence": {"abort_expected": True, "abort_observed": True}},
            {"status": "FAIL", "expected_mode": "Formal Spec Team Mode", "selected_mode": "Standard Engineering Mode", "evidence": {"abort_expected": False, "abort_observed": False}},
            {"status": "BLOCKED", "expected_mode": "Formal Spec Team Mode", "selected_mode": None, "evidence": {"abort_expected": False, "abort_observed": None}},
        ]
        metrics = mode_eval.mode_metrics(rows)
        self.assertEqual(metrics["mode_accuracy"], 0.3333)
        self.assertEqual(metrics["fast_exit_false_positive_rate"], 0.5)
        self.assertEqual(metrics["team_under_trigger_rate"], 1.0)
        self.assertEqual(metrics["abort_accuracy"], 1.0)

    def test_budget_limits_reject_unbounded_or_invalid_values(self):
        self.assertTrue(validate_limits(0, 1.0, 30))
        self.assertTrue(validate_limits(2.0, 1.0, 30))
        self.assertTrue(validate_limits(0.1, 1.0, 0))
        self.assertEqual(validate_limits(0.1, 1.0, 30), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
