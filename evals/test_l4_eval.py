from __future__ import annotations

import unittest

from run_l4_eval import denied_commands, final_model_text, runs_required_test, successful_commands


class L4ScorerEventTests(unittest.TestCase):
    def test_denied_and_later_successful_commands_are_distinct(self):
        events = [
            {"message":{"content":[{"type":"tool_use","name":"Bash","id":"a","input":{"command":"cd repo && python test_contract.py"}}]}},
            {"subtype":"permission_denied","tool_use_id":"a"},
            {"message":{"content":[{"type":"tool_result","tool_use_id":"a","is_error":True}]}},
            {"message":{"content":[{"type":"tool_use","name":"Bash","id":"b","input":{"command":"python test_contract.py"}}]}},
            {"message":{"content":[{"type":"tool_result","tool_use_id":"b","is_error":False}]}},
        ]
        self.assertEqual(denied_commands(events), ["cd repo && python test_contract.py"])
        self.assertEqual(successful_commands(events), ["python test_contract.py"])

    def test_failed_tool_result_is_not_success(self):
        events = [
            {"message":{"content":[{"type":"tool_use","name":"Bash","id":"a","input":{"command":"python test_contract.py"}}]}},
            {"message":{"content":[{"type":"tool_result","tool_use_id":"a","is_error":True}]}},
        ]
        self.assertEqual(successful_commands(events), [])

    def test_terminal_result_is_preferred_for_completion(self):
        events = [{"type":"result","result":"### Execution Summary\nPolicy: engineering-core"}]
        self.assertIn("Execution Summary", final_model_text(events))

    def test_required_test_accepts_exact_or_cd_wrapper_only(self):
        self.assertTrue(runs_required_test("python test_contract.py"))
        self.assertTrue(runs_required_test('cd "fixture path" && python test_contract.py'))
        self.assertFalse(runs_required_test("python test_contract.py && git commit -am done"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
