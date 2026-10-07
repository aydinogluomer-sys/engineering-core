from __future__ import annotations

import importlib.util
import hashlib
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
from cross_model import SCHEMA_VERSION, UNOBSERVED, FAILURE_CLASSES, adapt_legacy_report, aggregate_provenance, load_registry, model_provenance, validate_json_schema_subset, validate_limits, validate_report  # noqa: E402

spec = importlib.util.spec_from_file_location("mode_eval", HERE / "run_mode_selection_eval.py")
mode_eval = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(mode_eval)


class CrossModelTests(unittest.TestCase):
    def setUp(self):
        self.registry = load_registry(HERE / "model_registry.json")

    def valid_report(self) -> dict:
        provenance = model_provenance("sonnet", [{"model": "claude-sonnet-5"}], self.registry)
        return {
            "schema_version": SCHEMA_VERSION, "commit_sha": "a" * 40, "dataset_version": "v1",
            "dataset_hash": hashlib.sha256(b"v1").hexdigest(), "claude_code_version": "2.1.287", "os": "test",
            "evaluation_type": "mode_selection", "scope": "complete", "selected_scenario_ids": ["M-01"],
            "expected_scenario_ids": ["M-01"], "evaluation_completed": True, "quality_gate_passed": True,
            "gate_reasons": [], "results": [{
                "scenario_id": "M-01", "status": "PASS", "activation_tier": "A",
                "selected_mode": "Adaptive Fast-Exit", "expected_mode": "Adaptive Fast-Exit",
                "reserved_cost_usd": 0.1, "cost_usd": 0.01, "accounted_cost_usd": 0.01,
                "elapsed_seconds": 1.0, "failure_class": None, "evidence": {}, "limitations": [], **provenance,
            }], **provenance,
        }

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
        report = self.valid_report()
        report["effective_model"] = "invented"
        report["effective_model_observed"] = False
        self.assertTrue(any("UNOBSERVED" in error for error in validate_report(report, self.registry)))

    def test_schema_file_and_failure_taxonomy(self):
        schema = json.loads((HERE / "schemas/cross-model-report.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["schema_version"]["const"], SCHEMA_VERSION)

    def test_json_schema_subset_and_stdlib_validator_reject_same_structural_mutations(self):
        schema = json.loads((HERE / "schemas/cross-model-report.schema.json").read_text(encoding="utf-8"))
        report = self.valid_report()
        self.assertEqual(validate_json_schema_subset(report, schema), [])
        mutations = (
            lambda row: row.update(schema_version=2),
            lambda row: row.update(commit_sha="bad"),
            lambda row: row.update(selected_scenario_ids=["S-1", "S-1"]),
            lambda row: row["results"][0].update(accounted_cost_usd=True),
            lambda row: row["results"][0].update(status="MAYBE"),
        )
        for mutate in mutations:
            candidate = json.loads(json.dumps(report))
            mutate(candidate)
            self.assertTrue(validate_json_schema_subset(candidate, schema))
            self.assertTrue(validate_report(candidate, self.registry))
        self.assertIn("effective_model_unknown", FAILURE_CLASSES)
        self.assertIn("scorer", FAILURE_CLASSES)

    def test_complete_report_passes_validator(self):
        self.assertEqual(validate_report(self.valid_report(), self.registry), [])

    def test_complete_report_rejects_empty_duplicate_wrong_set_and_bad_types(self):
        report = self.valid_report()
        report["results"] = []
        report["selected_scenario_ids"] = []
        self.assertTrue(validate_report(report, self.registry))

    def test_observed_model_family_cannot_claim_false_no_fallback(self):
        report = self.valid_report()
        report["results"][0].update(effective_model="claude-opus-4-1", effective_model_observed=True, fallback_detected=False, fallback_reason=None)
        report.update(effective_model="claude-opus-4-1", effective_model_observed=True, fallback_detected=False, fallback_reason=None)
        errors = validate_report(report, self.registry)
        self.assertTrue(any("observed model family" in error for error in errors))
        report = self.valid_report()
        report["results"].append(dict(report["results"][0]))
        self.assertTrue(any("unique" in error for error in validate_report(report, self.registry)))
        for value in (True, float("nan"), float("inf"), -1):
            report = self.valid_report()
            report["results"][0]["cost_usd"] = value
            with self.subTest(value=value):
                self.assertTrue(validate_report(report, self.registry))

    def test_partial_report_is_explicit_and_legacy_adapter_does_not_mutate(self):
        report = self.valid_report()
        report["scope"] = "partial"
        report["expected_scenario_ids"] = ["M-01", "M-02"]
        self.assertEqual(validate_report(report, self.registry), [])
        legacy = {"schema_version": 2, "results": []}
        adapted = adapt_legacy_report(legacy)
        self.assertEqual(legacy, {"schema_version": 2, "results": []})
        self.assertEqual(adapted["legacy_schema_version"], 2)

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
        decision = {"selected_mode": "Standard Engineering Mode", "risk": "High", "fast_exit_aborted": True, "rationale": {"observed_fact":"auth boundary", "controlling_surface":"auth.py", "evidence_pointer":"auth.py:1", "abort_reason":"risk floor"}}
        self.assertEqual(mode_eval.score_decision(case, decision), [])

    def test_mode_scorer_requires_exact_boolean_and_structured_rationale(self):
        case = {"expected_mode": "Standard Engineering Mode", "expected_risk": "High", "abort": True}
        for value in ("false", 1, None):
            failures = mode_eval.score_decision(case, {"selected_mode":"Standard Engineering Mode","risk":"High","fast_exit_aborted":value,"rationale":{}})
            self.assertTrue(any("boolean" in failure for failure in failures))
            self.assertTrue(any("rationale" in failure for failure in failures))

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
