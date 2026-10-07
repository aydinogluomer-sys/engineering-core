from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from team_trust import begin_stage, end_stage, tree_hash, validate_coverage, validate_findings, validate_stage_authority, validate_stage_chain


class TeamTrustTests(unittest.TestCase):
    def test_stage_chain_requires_distinct_evaluator_records(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "implementation.md").write_text("# Spec", encoding="utf-8")
            start = begin_stage(root, "run-1", "builder", "builder")
            (root / "code.py").write_text("ok = True", encoding="utf-8")
            first = end_stage(start, root, "builder-events.jsonl").to_dict()
            second = dict(first, stage_id="qa", role="qa", started_ns=first["ended_ns"] + 1, ended_ns=first["ended_ns"] + 2, input_candidate_hash=first["output_candidate_hash"], process_identity="fresh")
            self.assertEqual(validate_stage_chain([first, second], ["builder", "qa"], second["output_candidate_hash"]), [])
            second["process_identity"] = first["process_identity"]
            self.assertTrue(any("reused" in error for error in validate_stage_chain([first, second], ["builder", "qa"], second["output_candidate_hash"])))

    def test_forged_booleans_do_not_close_findings(self):
        ledger = {"findings": [{"id":"F-1","source_role":"qa","source_run":"r","severity":"HIGH","linked_requirements":["REQ-1"],"description":"x","evidence":["x"],"state":"VERIFIED_FIXED","disposition_authority":"qa","closure_evidence":{"candidate_hash":"wrong","evidence_pointer":"x"}}]}
        self.assertTrue(validate_findings(ledger, "a" * 64))

    def test_coverage_rows_must_be_executable_and_nonempty(self):
        weak = {"requirements": {"REQ-001": {"status": "VERIFIED"}}}
        self.assertTrue(validate_coverage(weak, {"REQ-001"}))
        placeholders = {"requirements": {"REQ-001": {"acceptance":"x","work_unit":"x","affected_surface":["x"],"implementation":["x"],"evidence":["x"],"independent_review":["x"],"status":"VERIFIED"}}}
        self.assertTrue(validate_coverage(placeholders, {"REQ-001"}))

    def test_finding_closure_pointer_must_resolve(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            ledger = {"findings": [{"id":"FIND-001","source_role":"qa","source_run":"stage-2","severity":"HIGH","linked_requirements":["REQ-001"],"description":"tenant boundary leaked data","evidence":["qa-report.json:1"],"state":"VERIFIED_FIXED","disposition_authority":"reviewer2","closure_evidence":{"evidence_pointer":"missing.json:1"}}]}
            self.assertTrue(validate_findings(ledger, "a" * 64, evaluator_independent_closure=True, expected_requirements={"REQ-001"}, root=root))
            (root / "qa-report.json").write_text("{}\n", encoding="utf-8")
            ledger["findings"][0]["closure_evidence"]["evidence_pointer"] = "qa-report.json:1"
            self.assertEqual(validate_findings(ledger, "a" * 64, evaluator_independent_closure=True, expected_requirements={"REQ-001"}, root=root, closure_artifacts={"qa-report.json"}, closure_role="reviewer2", source_runs_by_role={"qa":{"stage-2"}}), [])

    def test_builder_pointer_cannot_manufacture_independent_closure(self):
        ledger = {"findings": [{"id":"FIND-001","source_role":"qa","source_run":"stage-2","severity":"HIGH","linked_requirements":["REQ-001"],"description":"tenant boundary leaked data","evidence":["negative path failed"],"state":"VERIFIED_FIXED","disposition_authority":"reviewer2","closure_evidence":{"evidence_pointer":"attempts[0].events"}}]}
        errors = validate_findings(ledger, "a" * 64, evaluator_independent_closure=True, expected_requirements={"REQ-001"}, allowed_evidence_pointers={"attempts[2].events"}, closure_role="reviewer2", source_runs_by_role={"qa":{"stage-2"}})
        self.assertTrue(any("closure evidence" in error for error in errors))

    def test_builder_cannot_author_qa_and_reviewer_writer_cannot_close(self):
        base = {"input_candidate_hash":"a" * 64,"output_candidate_hash":"a" * 64,"input_artifact_hashes":{},"output_artifact_hashes":{}}
        builder = {**base,"role":"builder","output_artifact_hashes":{"qa-report.json":"1"}}
        errors, independent = validate_stage_authority([builder], "requirement-change", final_oracle_passed=True)
        self.assertTrue(any("builder" in error for error in errors))
        self.assertFalse(independent)
        qa = {**base,"role":"qa","output_artifact_hashes":{"qa-report.json":"q","finding-ledger.json":"f","team-state.json":"s"}}
        reviewer = {**base,"role":"reviewer2","input_candidate_hash":"a" * 64,"output_candidate_hash":"b" * 64,"input_artifact_hashes":qa["output_artifact_hashes"],"output_artifact_hashes":{"qa-report.json":"q","finding-ledger.json":"f2","team-state.json":"s2"}}
        errors, independent = validate_stage_authority([{**base,"role":"builder"}, qa, reviewer], "two-key-closure", final_oracle_passed=True)
        self.assertTrue(any("cannot self-certify" in error for error in errors))
        self.assertFalse(independent)

    def test_large_spec_requires_qa_authorship_before_auditor(self):
        base = {"input_candidate_hash":"a" * 64,"output_candidate_hash":"a" * 64,"input_artifact_hashes":{},"output_artifact_hashes":{}}
        builder = {**base,"role":"builder"}
        qa = {**base,"role":"qa"}
        auditor = {**base,"role":"auditor","output_artifact_hashes":{"qa-report.json":"q","finding-ledger.json":"f","release-audit.json":"r"}}
        errors, independent = validate_stage_authority([builder, qa, auditor], "large-spec", final_oracle_passed=True)
        self.assertTrue(any("QA stage did not newly author" in error for error in errors))
        self.assertFalse(independent)

    def test_large_spec_auditor_cannot_rewrite_qa_ledger(self):
        base = {"input_candidate_hash":"a" * 64,"output_candidate_hash":"a" * 64,"input_artifact_hashes":{},"output_artifact_hashes":{}}
        builder = {**base,"role":"builder"}
        qa_out = {"qa-report.json":"q","finding-ledger.json":"f"}
        qa = {**base,"role":"qa","output_artifact_hashes":qa_out}
        auditor = {**base,"role":"auditor","input_artifact_hashes":qa_out,"output_artifact_hashes":{"qa-report.json":"q","finding-ledger.json":"forged","release-audit.json":"r"}}
        errors, independent = validate_stage_authority([builder, qa, auditor], "large-spec", final_oracle_passed=True)
        self.assertTrue(any("rewrote the QA finding ledger" in error for error in errors))
        self.assertFalse(independent)


if __name__ == "__main__":
    unittest.main()
