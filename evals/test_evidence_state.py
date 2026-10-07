from __future__ import annotations

import json
import tempfile
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evidence_state import atomic_write_state, claim_owner, evidence_freshness, load_state, manifest_hash, recover_state, stale_closure, validate_dependency_graph, validate_resume_context


def base_state(root: Path) -> dict:
    return {
        "schema_version": 1, "revision": 0, "repo_identity": str(root), "branch": "main", "head": "a" * 40,
        "objective": "test", "authority": "local fixture only",
        "requirements": {"REQ-001": {"depends_on": [], "supersedes": []}}, "decision_locks": {},
        "work_units": {}, "modified_paths": [], "evidence_refs": [], "findings": [], "owners": {}, "next_action": "verify",
    }


class EvidenceStateTests(unittest.TestCase):
    def test_relevant_change_stales_but_unrelated_change_does_not(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "relevant.py").write_text("one", encoding="utf-8")
            (root / "other.py").write_text("one", encoding="utf-8")
            digest, _ = manifest_hash(root, ["relevant.py"])
            evidence = {"evidence_id":"E-1","requirement_ids":["REQ-001"],"actor_role":"qa","actor_run_id":"R-1","command":"test","exit_code":0,"observed_at":"now","source_manifest_hash":digest,"spec_hash":"s","environment_fingerprint":"e","output_artifact_hash":"o","limitations":[],"status":"PASS","source_paths":["relevant.py"]}
            (root / "other.py").write_text("two", encoding="utf-8")
            self.assertEqual(evidence_freshness(evidence, root, spec_hash="s", environment_fingerprint="e")[0], "PASS")
            (root / "relevant.py").write_text("two", encoding="utf-8")
            self.assertEqual(evidence_freshness(evidence, root, spec_hash="s", environment_fingerprint="e")[0], "STALE")

    def test_atomic_cas_conflict_and_backup_recovery(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "state.json"
            first = atomic_write_state(path, base_state(path.parent), expected_revision=0)
            with self.assertRaisesRegex(RuntimeError, "revision conflict"):
                atomic_write_state(path, first, expected_revision=0)
            second = atomic_write_state(path, first, expected_revision=1)
            path.write_text("{bad", encoding="utf-8")
            recovered = recover_state(path)
            self.assertEqual(recovered["revision"], 1)
            self.assertEqual(second["revision"], 2)

    def test_dependency_errors(self):
        rows = {"A": {"depends_on": ["A", "MISSING"], "supersedes": []}, "B": {"depends_on": ["C"], "supersedes": []}, "C": {"depends_on": ["B"], "supersedes": []}}
        errors = validate_dependency_graph(rows)
        self.assertTrue(any("self-loop" in error for error in errors))
        self.assertTrue(any("missing dependency" in error for error in errors))
        self.assertTrue(any("cycle" in error for error in errors))

    def test_owner_transfer_requires_ack_or_isolation(self):
        state = base_state(Path("."))
        claim_owner(state, "WORK-A", "writer-1")
        with self.assertRaisesRegex(RuntimeError, "active writer"):
            claim_owner(state, "WORK-A", "writer-2")
        claim_owner(state, "WORK-A", "writer-2", cancellation_ack=True)
        self.assertEqual(state["owners"]["WORK-A"]["owner_run_id"], "writer-2")

    def test_resume_rejects_wrong_repo_branch_head_and_old_or_corrupt_state(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            state = base_state(root)
            errors = validate_resume_context(state, repo_identity=str(root / "other"), branch="feature", head="b" * 40)
            self.assertTrue(any("repository identity" in error for error in errors))
            self.assertTrue(any("branch" in error for error in errors))
            self.assertTrue(any("HEAD" in error for error in errors))
            path = root / "state.json"
            path.write_text("{bad", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unreadable"):
                load_state(path)
            path.write_text(json.dumps({**state, "schema_version": 0}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "schema_version"):
                load_state(path)

    def test_deleted_evidence_stales_and_requirement_change_is_selective(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "relevant.py").write_text("one", encoding="utf-8")
            digest, _ = manifest_hash(root, ["relevant.py"])
            evidence = {"evidence_id":"E-1","requirement_ids":["REQ-001"],"actor_role":"qa","actor_run_id":"R-1","command":"test","exit_code":0,"observed_at":"now","source_manifest_hash":digest,"spec_hash":"s","environment_fingerprint":"e","output_artifact_hash":"o","limitations":[],"status":"PASS","source_paths":["relevant.py"]}
            self.assertEqual(evidence_freshness(evidence, root, spec_hash="s", environment_fingerprint="e", artifact_exists=False)[0], "STALE")
        graph = {"REQ-1":{"depends_on":[]},"REQ-2":{"depends_on":["REQ-1"]},"REQ-3":{"depends_on":["REQ-2"]},"REQ-X":{"depends_on":[]}}
        self.assertEqual(stale_closure(graph, {"REQ-1"}), {"REQ-1", "REQ-2", "REQ-3"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
