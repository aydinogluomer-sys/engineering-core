from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from run_activation_eval import DESCRIPTIONS, activation_evidence, load_dataset, metrics, set_description


class ActivationEvalTests(unittest.TestCase):
    def test_smoke_profile_has_required_balance(self):
        cases = load_dataset("smoke")
        counts = {kind: sum(row["expected"] == kind for row in cases) for kind in ("positive", "negative", "ambiguous")}
        self.assertGreaterEqual(counts["positive"], 8)
        self.assertGreaterEqual(counts["negative"], 4)
        self.assertGreaterEqual(counts["ambiguous"], 2)

    def test_full_dataset_has_unique_ids_and_categories(self):
        cases = load_dataset("full")
        self.assertEqual(len(cases), len({row["id"] for row in cases}))
        self.assertIn("security", {row["category"] for row in cases})
        self.assertIn("non-engineering-writing", {row["category"] for row in cases})

    def test_confusion_metrics_exclude_ambiguous(self):
        rows = [
            {"expected":"positive","activated":True,"status":"SCORED"},
            {"expected":"positive","activated":False,"status":"SCORED"},
            {"expected":"negative","activated":True,"status":"SCORED"},
            {"expected":"negative","activated":False,"status":"SCORED"},
            {"expected":"ambiguous","activated":True,"status":"SCORED"},
        ]
        result = metrics(rows)
        self.assertEqual((result["tp"], result["fp"], result["tn"], result["fn"]), (1, 1, 1, 1))
        self.assertEqual(result["ambiguous_scored_separately"], 1)

    def test_init_availability_alone_is_not_activation(self):
        events = [{"type":"system","subtype":"init","skills":["engineering-core"]}]
        self.assertEqual(activation_evidence(events)[:2], (False, None))

    def test_tool_trace_is_tier_a(self):
        events = [{"message":{"content":[{"type":"tool_use","name":"Skill","input":{"skill":"engineering-core"}}]}}]
        self.assertEqual(activation_evidence(events)[:2], (True, "A"))

    def test_valid_completion_is_tier_b(self):
        text = "### Execution Summary\nPolicy: engineering-core\nRisk: Low\nStatus: NO_CHANGE\nChanged: None\nVerified: Read only\nLimitations: None"
        events = [{"type":"result","result":text}]
        self.assertEqual(activation_evidence(events)[:2], (True, "B"))

    def test_named_policy_is_activation_even_when_contract_is_incomplete(self):
        text = "### Execution Summary\n**Policy**: engineering-core\n**Risk**: Low\n**Status**: VERIFIED"
        activated, tier, _, errors = activation_evidence([{"type":"result","result":text}])
        self.assertEqual((activated, tier), (True, "B"))
        self.assertTrue(errors)

    def test_candidate_descriptions_are_distinct(self):
        self.assertEqual(len(DESCRIPTIONS), len(set(DESCRIPTIONS.values())))

    def test_description_replacement_changes_only_description_line(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "SKILL.md"
            path.write_text("---\nname: engineering-core\ndescription: old\n---\n# Body\n", encoding="utf-8")
            set_description(path, "candidate1")
            text = path.read_text(encoding="utf-8")
            self.assertIn(DESCRIPTIONS["candidate1"], text)
            self.assertIn("# Body", text)

    def test_dataset_json_is_valid(self):
        for name in ("positive", "negative", "ambiguous"):
            rows = json.loads((Path(__file__).parent / f"{name}.json").read_text(encoding="utf-8"))
            self.assertTrue(rows)
            self.assertTrue(all({"id", "category", "profiles", "prompt"} <= set(row) for row in rows))


if __name__ == "__main__":
    unittest.main(verbosity=2)
