from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from run_team_eval import FIXTURES, load_scenarios, requirement_ids_in_spec, score_fixture  # noqa: E402


class TeamEvalTests(unittest.TestCase):
    def copy_fixture(self, name: str) -> Path:
        raw = Path(tempfile.mkdtemp(prefix="team-eval-test-"))
        self.addCleanup(lambda: shutil.rmtree(raw, ignore_errors=True))
        target = raw / name
        shutil.copytree(FIXTURES / name, target)
        for command in (["git", "init", "-q"], ["git", "config", "user.email", "eval@example.invalid"], ["git", "config", "user.name", "Test"], ["git", "add", "."], ["git", "commit", "-qm", "baseline"]):
            import subprocess
            subprocess.run(command, cwd=target, check=True, capture_output=True)
        return target

    def test_required_scenarios_have_complete_contract(self):
        scenarios = load_scenarios()
        self.assertEqual([row["id"] for row in scenarios], ["large-spec", "requirement-change", "cross-session", "two-key-closure", "release-auditor"])
        required = {"objective","fixture","expected_phases","expected_requirement_count","expected_min_processes","protected_files","decision_locks","expected_state_transitions","required_evidence","prohibited_behavior","scoring_assertions","budget_usd","timeout_seconds"}
        for row in scenarios:
            self.assertTrue(required <= set(row), row["id"])

    def test_large_spec_is_realistic(self):
        scenario = load_scenarios(["large-spec"])[0]
        self.assertGreaterEqual(scenario["expected_requirement_count"], 15)
        self.assertLessEqual(scenario["expected_requirement_count"], 25)
        self.assertGreaterEqual(scenario["expected_phases"], 4)
        self.assertEqual(requirement_ids_in_spec(FIXTURES / "large-spec"), set(scenario["expected_requirement_ids"]))
        text = (FIXTURES / "large-spec/implementation.md").read_text(encoding="utf-8")
        for marker in ("High risk", "Decision Locks", "Deferral", "dirty", "release"):
            self.assertIn(marker.lower(), text.lower())

    def test_all_fixture_baselines_fail_contract(self):
        import subprocess
        for fixture in sorted(FIXTURES.iterdir()):
            with self.subTest(fixture=fixture.name):
                result = subprocess.run([sys.executable, "test_contract.py"], cwd=fixture, capture_output=True)
                self.assertNotEqual(result.returncode, 0)

    def test_large_spec_known_unrelated_failure_is_seeded(self):
        import subprocess
        result = subprocess.run([sys.executable, "preexisting_check.py"], cwd=FIXTURES / "large-spec", capture_output=True)
        self.assertNotEqual(result.returncode, 0)

    def test_two_key_scorer_rejects_missing_artifacts(self):
        scenario = load_scenarios(["two-key-closure"])[0]
        fixture = self.copy_fixture("independent-qa")
        baseline = __import__("subprocess").run(["git", "rev-parse", "HEAD"], cwd=fixture, text=True, capture_output=True).stdout.strip()
        result = score_fixture(scenario, fixture, {}, baseline, 1)
        self.assertFalse(result["passed"])
        self.assertTrue(any("artifact" in item for item in result["failures"]))

    def test_scorer_requires_mode_selection_and_independent_processes(self):
        scenario = load_scenarios(["two-key-closure"])[0]
        fixture = self.copy_fixture("independent-qa")
        baseline = __import__("subprocess").run(["git", "rev-parse", "HEAD"], cwd=fixture, text=True, capture_output=True).stdout.strip()
        result = score_fixture(scenario, fixture, {}, baseline, 1)
        self.assertIn("independent process count is below scenario contract", result["failures"])
        self.assertIn("Formal Spec Team Mode selection is not recorded", result["failures"])

    def test_release_scorer_rejects_prose_free_false_claim(self):
        scenario = load_scenarios(["release-auditor"])[0]
        fixture = self.copy_fixture("release-audit")
        (fixture / "release-audit.json").write_text(json.dumps({"fresh":True,"caught_seeded_defect":False,"release_status":"RELEASE_VERIFIED"}), encoding="utf-8")
        baseline = __import__("subprocess").run(["git", "rev-parse", "HEAD"], cwd=fixture, text=True, capture_output=True).stdout.strip()
        result = score_fixture(scenario, fixture, {}, baseline, 1)
        self.assertFalse(result["passed"])
        self.assertIn("release auditor evidence incomplete", result["failures"])

    def test_cross_session_requires_two_processes(self):
        scenario = load_scenarios(["cross-session"])[0]
        fixture = self.copy_fixture("cross-session-resume")
        (fixture / "continuation-state.json").write_text("{}", encoding="utf-8")
        (fixture / "resume-evidence.json").write_text(json.dumps({"repository_revalidated":True,"stale_detected":True,"integration_rerun":True}), encoding="utf-8")
        baseline = __import__("subprocess").run(["git", "rev-parse", "HEAD"], cwd=fixture, text=True, capture_output=True).stdout.strip()
        result = score_fixture(scenario, fixture, {}, baseline, 1)
        self.assertIn("cross-session scenario did not use two processes", result["failures"])

    def test_selective_stale_accepts_structured_marked_stale_evidence(self):
        scenario = load_scenarios(["requirement-change"])[0]
        fixture = self.copy_fixture("requirement-change")
        (fixture / "pipeline.py").write_text("def deliver(send):\n    for attempt in range(3):\n        try:\n            return send()\n        except RuntimeError:\n            if attempt == 2:\n                raise\n", encoding="utf-8")
        (fixture / "implementation.md").write_text((fixture / "implementation.md").read_text(encoding="utf-8").replace("at most two total attempts", "at most three total attempts"), encoding="utf-8")
        (fixture / "team-state.json").write_text(json.dumps({"mode":"Formal Spec Team Mode","phases":{"A":"VERIFIED"}}), encoding="utf-8")
        (fixture / "requirement-change-evidence.json").write_text(json.dumps({"mode":"Formal Spec Team Mode","marked_stale":["REQ-003","REQ-004","REQ-005"]}), encoding="utf-8")
        baseline = __import__("subprocess").run(["git", "rev-parse", "HEAD"], cwd=fixture, text=True, capture_output=True).stdout.strip()
        result = score_fixture(scenario, fixture, {}, baseline, 1)
        self.assertNotIn("selective STALE evidence is incorrect", result["failures"])

    def test_resume_accepts_structured_drift_and_integration_evidence(self):
        scenario = load_scenarios(["cross-session"])[0]
        fixture = self.copy_fixture("cross-session-resume")
        (fixture / "pipeline.py").write_text("def normalize(value):\n    return value.strip().lower()\n\ndef render(value):\n    return 'item:' + normalize(value)\n", encoding="utf-8")
        (fixture / "continuation-state.json").write_text(json.dumps({"mode":"Formal Spec Team Mode"}), encoding="utf-8")
        (fixture / "resume-evidence.json").write_text(json.dumps({"mode":"Formal Spec Team Mode","source_change_detected_after_prior_session":True,"stale_marked":["REQ-001"],"integration_rerun":True}), encoding="utf-8")
        baseline = __import__("subprocess").run(["git", "rev-parse", "HEAD"], cwd=fixture, text=True, capture_output=True).stdout.strip()
        result = score_fixture(scenario, fixture, {}, baseline, 2)
        self.assertNotIn("resume evidence does not prove stale-state handling", result["failures"])

    def test_two_key_transition_accepts_separate_implementation_and_qa_evidence(self):
        scenario = load_scenarios(["two-key-closure"])[0]
        fixture = self.copy_fixture("independent-qa")
        (fixture / "auth.py").write_text(
            "def read_export(user_tenant, record_tenant, payload):\n"
            "    if user_tenant != record_tenant:\n        raise PermissionError('Access denied')\n"
            "    return payload\n",
            encoding="utf-8",
        )
        common = {"mode": "Formal Spec Team Mode"}
        (fixture / "qa-report.json").write_text(json.dumps({**common,"independent":True,"acceptance_covered":True,"negative_paths":True,"implementation_key":True,"independent_key":True}), encoding="utf-8")
        (fixture / "finding-ledger.json").write_text(json.dumps({**common,"findings":[{"id":"FIND-001","status":"VERIFIED_FIXED"}]}), encoding="utf-8")
        (fixture / "team-state.json").write_text(json.dumps({**common,"phases":{"Authorization":{"status":"VERIFIED"}},"transitions":["Implementation key acquired", "PHASE_VERIFIED after independent QA"]}), encoding="utf-8")
        baseline = __import__("subprocess").run(["git", "rev-parse", "HEAD"], cwd=fixture, text=True, capture_output=True).stdout.strip()
        result = score_fixture(scenario, fixture, {}, baseline, 2)
        self.assertNotIn("phase transition does not prove closure after QA", result["failures"])

    def test_two_key_transition_accepts_explicit_source_target_fields(self):
        scenario = load_scenarios(["two-key-closure"])[0]
        fixture = self.copy_fixture("independent-qa")
        (fixture / "auth.py").write_text(
            "def read_export(user_tenant, record_tenant, payload):\n"
            "    if user_tenant != record_tenant:\n        raise PermissionError('Access denied')\n"
            "    return payload\n",
            encoding="utf-8",
        )
        common = {"mode": "Formal Spec Team Mode"}
        (fixture / "qa-report.json").write_text(json.dumps({**common,"independent":True,"acceptance_covered":True,"negative_paths":True,"implementation_key":True,"independent_key":True}), encoding="utf-8")
        (fixture / "finding-ledger.json").write_text(json.dumps({**common,"findings":[{"id":"FIND-001","status":"VERIFIED_FIXED"}]}), encoding="utf-8")
        (fixture / "team-state.json").write_text(json.dumps({**common,"phases":{"authorization":"VERIFIED"},"transition_source":"IMPLEMENTED","transition_target":"VERIFIED","transition_completed":True}), encoding="utf-8")
        baseline = __import__("subprocess").run(["git", "rev-parse", "HEAD"], cwd=fixture, text=True, capture_output=True).stdout.strip()
        result = score_fixture(scenario, fixture, {}, baseline, 2)
        self.assertNotIn("phase transition does not prove closure after QA", result["failures"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
