from __future__ import annotations

import json
import ast
import math
import shutil
import subprocess
import tempfile
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness_core import account_cost, gate_exit_code, parse_jsonl_events, redact, tracked_secret_findings, validate_run_limits, write_redacted_json


class HarnessCoreTests(unittest.TestCase):
    def test_limits_reject_bool_nan_inf_and_bad_bounds(self):
        for value in (True, 0, -1, math.nan, math.inf, -math.inf, "1"):
            with self.subTest(value=value):
                self.assertTrue(validate_run_limits(value, 2.0, 30))
        self.assertTrue(validate_run_limits(1.0, 2.0, True))
        self.assertTrue(validate_run_limits(1.0, 2.0, 30, repetitions=0))
        self.assertTrue(validate_run_limits(1.0, 2.0, 30, workers=9))
        self.assertEqual(validate_run_limits(1.0, 2.0, 30, 2, 2), [])

    def test_unknown_cost_consumes_reserve(self):
        unknown = account_cost(1.5, None)
        self.assertEqual((unknown.observed_usd, unknown.accounted_usd), (None, 1.5))
        known = account_cost(1.5, 0.4)
        self.assertEqual((known.observed_usd, known.accounted_usd), (0.4, 0.4))

    def test_gate_exit_separates_measurement_and_quality(self):
        self.assertEqual(gate_exit_code(evaluation_completed=True, quality_gate_passed=False, require_gate=False), 0)
        self.assertEqual(gate_exit_code(evaluation_completed=True, quality_gate_passed=False, require_gate=True), 1)
        self.assertEqual(gate_exit_code(evaluation_completed=False, quality_gate_passed=None, require_gate=False), 2)

    def test_event_parser_controls_malformed_types_and_conflicts(self):
        raw = "\n".join(("null", "[]", "{bad", json.dumps({"message": {"content": "bad"}}), json.dumps({"type": "result", "terminal_reason": "ok"}), json.dumps({"type": "result", "terminal_reason": "budget_exceeded"})))
        events, errors = parse_jsonl_events(raw)
        self.assertEqual(len(events), 3)
        self.assertTrue(any("event must be an object" in error for error in errors))
        self.assertTrue(any("malformed JSON" in error for error in errors))
        self.assertTrue(any("content must be a list" in error for error in errors))
        self.assertIn("conflicting terminal result events", errors)

    def test_recursive_redaction_covers_synthetic_secret_classes(self):
        private_key = "-----BEGIN PRIVATE " + "KEY-----\nSYNTHETIC\n-----END PRIVATE " + "KEY-----"
        anthropic = "sk" + "-ant-abcdefghijklmnop"
        bearer = "Bearer" + " abcdefghijklmnopqrstuvwxyz"
        database_url = "postgres://u:" + "synthetic-password@localhost/db"
        value = {"nested": [anthropic, bearer, database_url, private_key]}
        rendered = json.dumps(redact(value))
        for secret in ("sk-ant-", "abcdefghijklmnopqrstuvwxyz", "synthetic-password", "SYNTHETIC"):
            self.assertNotIn(secret, rendered)
        self.assertGreaterEqual(rendered.count("[REDACTED]"), 4)

    def test_redacted_writer_never_serializes_nan(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "report.json"
            with self.assertRaises(ValueError):
                write_redacted_json(path, {"cost": math.nan})

    def test_tracked_scan_finds_value_but_not_pattern_definition(self):
        root = Path(tempfile.mkdtemp(prefix="secret-scan-"))
        self.addCleanup(lambda: shutil.rmtree(root, ignore_errors=True))
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        (root / "pattern.py").write_text("TOKEN_RE = r'sk-ant-[A-Za-z0-9_-]{12,}'\n", encoding="utf-8")
        (root / "secret.txt").write_text("sk" + "-ant-abcdefghijklmnop\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=root, check=True)
        self.assertEqual(tracked_secret_findings(root), ["secret.txt"])

    def test_all_runner_gate_calls_use_keyword_only_contract(self):
        root = Path(__file__).resolve().parents[1]
        runners = [root / "evals/run_l4_eval.py", root / "evals/activation/run_activation_eval.py", root / "evals/formal-spec-team/run_team_eval.py", root / "evals/cross-model/run_mode_selection_eval.py"]
        for runner in runners:
            tree = ast.parse(runner.read_text(encoding="utf-8"))
            calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "gate_exit_code"]
            self.assertTrue(calls, runner)
            self.assertTrue(all(not call.args and {item.arg for item in call.keywords} == {"evaluation_completed", "quality_gate_passed", "require_gate"} for call in calls), runner)


if __name__ == "__main__":
    unittest.main(verbosity=2)
