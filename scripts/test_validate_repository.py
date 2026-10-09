from __future__ import annotations

import unittest
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from validate_repository import integration_binding_scope_errors, validate_governance_report, validate_live_preflight, validate_longitudinal_ledger, validate_readme, validate_workflow
from build_evidence_bundle import candidate_manifest


VALID = """name: Validate
on:
  push:
  pull_request:
  workflow_dispatch:
permissions:
  contents: read
jobs:
  static-validation:
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest]
        python: ['3.10', '3.14']
    steps:
      - uses: actions/checkout@1111111111111111111111111111111111111111 # v7
      - uses: actions/setup-python@2222222222222222222222222222222222222222 # v7
      - run: python evals/formal-spec-team/test_team_eval.py
      - run: python evals/cross-model/test_cross_model_matrix.py
      - run: python -m unittest discover -s evals/failure-resistance -p "test_*.py"
      - run: python -m unittest evals.test_run_manifest
      - run: python scripts/test_install.py
      - run: python scripts/test_validate_repository.py
      - run: python scripts/validate_repository.py .
"""


class WorkflowStructureTests(unittest.TestCase):
    def test_supported_structure_passes(self):
        self.assertEqual(validate_workflow(VALID), [])

    def test_comments_cannot_fake_required_execution(self):
        mutated = VALID.replace("      - run: python scripts/validate_repository.py .", "      # run: python scripts/validate_repository.py .")
        self.assertTrue(any("python scripts/validate_repository.py ." in error for error in validate_workflow(mutated)))

    def test_floating_action_is_rejected(self):
        self.assertTrue(any("immutable SHA" in error for error in validate_workflow(VALID.replace("actions/checkout@1111111111111111111111111111111111111111 # v7", "actions/checkout@v7"))))

    def test_matrix_values_must_be_structural(self):
        mutated = VALID.replace("        os: [ubuntu-latest, windows-latest]", "        # os: [ubuntu-latest, windows-latest]")
        self.assertTrue(any("OS matrix" in error for error in validate_workflow(mutated)))


class ReadmeStructureTests(unittest.TestCase):
    def valid(self) -> str:
        return "\n".join(f"### {i}. Diagram {i}\n\n```mermaid\nflowchart LR\nA --> B\n```" for i in range(1, 15))

    def test_fourteen_numbered_mermaid_diagrams_pass(self):
        self.assertEqual(validate_readme(self.valid()), [])

    def test_removed_diagram_fails(self):
        self.assertTrue(validate_readme(self.valid().replace("```mermaid\nflowchart LR\nA --> B\n```", "", 1)))

    def test_prose_cannot_fake_mermaid_declaration(self):
        self.assertTrue(validate_readme(self.valid().replace("flowchart LR", "this is prose", 1)))


class EvidenceManifestTests(unittest.TestCase):
    def test_ignored_temporary_evaluation_trees_are_excluded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "evidence/current"
            output.mkdir(parents=True)
            (root / "tracked.txt").write_text("kept", encoding="utf-8")
            transient = root / "evals/activation/.tmp-activation-case"
            transient.mkdir(parents=True)
            (transient / "copied-runtime.md").write_text("ignored", encoding="utf-8")
            manifest = candidate_manifest(output, root)
            self.assertEqual(set(manifest), {"tracked.txt"})


class LongitudinalLedgerTests(unittest.TestCase):
    def ledger(self) -> dict:
        fields = {"timestamp", "repository_task", "task_class", "risk", "expected_mode", "observed_mode", "completion_state", "verification_evidence", "regressions", "human_correction_required", "false_completion", "scope_drift", "cost", "notes"}
        return {
            "schema_version": 1, "state": "IN_PROGRESS",
            "start_timestamp": "2026-10-08T00:00:00+00:00", "earliest_valid_completion_timestamp": "2026-10-15T00:00:00+00:00",
            "candidate_sha": "a" * 40, "skill_version": "0.1.0-rc.1", "claude_code_version": "UNAVAILABLE",
            "models_used": [], "required_task_fields": sorted(fields), "tasks": [],
            "independent_final_analysis": "NOT_RUN", "limitations": ["in progress"],
        }

    def test_in_progress_seven_day_contract_is_valid(self):
        self.assertEqual(validate_longitudinal_ledger(self.ledger(), now=datetime(2026, 10, 8, tzinfo=timezone.utc)), [])

    def test_early_pass_and_short_window_are_rejected(self):
        ledger = self.ledger()
        ledger["state"] = "PASS"
        ledger["earliest_valid_completion_timestamp"] = "2026-10-14T23:59:59+00:00"
        errors = validate_longitudinal_ledger(ledger, now=datetime(2026, 10, 9, tzinfo=timezone.utc))
        self.assertTrue(any("shorter" in error for error in errors))
        self.assertTrue(any("predates" in error for error in errors))
        self.assertTrue(any("independent" in error for error in errors))


class GovernanceReportTests(unittest.TestCase):
    def report(self) -> dict:
        return {
            "schema_version": 1, "status": "APPLIED", "repository": "aydinogluomer-sys/engineering-core", "branch": "main",
            "source_check_run": {"run_id": 1, "candidate_sha": "a" * 40, "conclusion": "success"},
            "readback": {
                "strict": True, "enforce_admins": True, "required_pull_request_reviews": None,
                "allow_force_pushes": False, "allow_deletions": False,
                "required_status_checks": [
                    "static-validation (ubuntu-latest, 3.10)", "static-validation (ubuntu-latest, 3.14)",
                    "static-validation (windows-latest, 3.10)", "static-validation (windows-latest, 3.14)",
                ],
            },
        }

    def test_applied_readback_is_valid(self):
        self.assertEqual(validate_governance_report(self.report()), [])

    def test_weakened_protection_is_rejected(self):
        report = self.report()
        report["readback"]["allow_force_pushes"] = True
        report["readback"]["required_status_checks"].pop()
        errors = validate_governance_report(report)
        self.assertTrue(any("required checks" in error for error in errors))
        self.assertTrue(any("force push" in error for error in errors))


class LivePreflightTests(unittest.TestCase):
    def test_unset_cap_prohibits_calls(self):
        report = {
            "schema_version": 1, "status": "NOT_AUTHORIZED", "paid_calls_executed": 0,
            "claude_code": {"version": "2.1.289"},
            "alias_discovery": {"registry_required": ["haiku", "sonnet", "opus", "fable"]},
            "cost_controls": {"max_total_spend_usd": None, "worst_case_within_user_cap": "UNDETERMINED_CAP_UNSET", "automatic_retries": 0, "cli_max_budget_flag_observed": True},
        }
        self.assertEqual(validate_live_preflight(report), [])
        report["paid_calls_executed"] = 1
        self.assertTrue(any("prohibit" in error for error in validate_live_preflight(report)))


class IntegrationBindingTests(unittest.TestCase):
    def test_only_evidence_and_reconciliation_paths_may_follow_candidate(self):
        allowed = ["evidence/current/integrations.json", "docs/current-status.md", "README.md", "implementation-v6.md", "scripts/validate_repository.py"]
        self.assertEqual(integration_binding_scope_errors(allowed), [])
        changed = [*allowed, "engineering-core/SKILL.md", "evals/failure-resistance/browser_oracle.mjs"]
        self.assertEqual(integration_binding_scope_errors(changed), ["engineering-core/SKILL.md", "evals/failure-resistance/browser_oracle.mjs"])


if __name__ == "__main__":
    unittest.main()
