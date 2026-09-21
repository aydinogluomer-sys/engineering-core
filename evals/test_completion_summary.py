from __future__ import annotations

import unittest

from completion_summary import parse_completion_summary


def report(risk: str = "Low", status: str = "VERIFIED", extra: str = "") -> str:
    return f"""Work notes.

### Execution Summary
Policy: engineering-core
Risk: {risk}
Status: {status}
Changed: Localized behavior.
Verified: `python test_contract.py` passed.
Limitations: None
{extra}"""


class CompletionSummaryTests(unittest.TestCase):
    def test_low_compact(self):
        parsed, errors = parse_completion_summary(report())
        self.assertEqual(errors, [])
        self.assertEqual(parsed.status, "VERIFIED")
        summary = report().split("### Execution Summary", 1)[1]
        self.assertEqual(
            [line.split(":", 1)[0] for line in summary.splitlines() if ":" in line],
            ["Policy", "Risk", "Status", "Changed", "Verified", "Limitations"],
        )

    def test_moderate_with_relevant_section(self):
        parsed, errors = parse_completion_summary(report("Moderate") + "\n#### Negative Paths\nInvalid input rejected.\n")
        self.assertEqual(errors, [])
        self.assertEqual(parsed.risk, "Moderate")

    def test_bold_fields_and_multiline_values(self):
        text = """### Execution Summary
**Policy:** engineering-core | **Risk:** Low — local and reversible
**Status:** VERIFIED
**Changed:** Local fix
**Verified:**
- Focused test passed
- Diff inspected
**Limitations:** None
"""
        parsed, errors = parse_completion_summary(text)
        self.assertEqual(errors, [])
        self.assertEqual(parsed.risk, "Low")
        self.assertIn("Focused test", parsed.verified)

    def test_high_and_critical_are_valid(self):
        for risk in ("High", "Critical"):
            with self.subTest(risk=risk):
                self.assertEqual(parse_completion_summary(report(risk))[1], [])

    def test_non_verified_statuses_are_valid(self):
        for status in ("NO_CHANGE", "IMPLEMENTED", "NOT_VERIFIED", "BLOCKED"):
            with self.subTest(status=status):
                parsed, errors = parse_completion_summary(report(status=status))
                self.assertEqual(errors, [])
                self.assertEqual(parsed.status, status)

    def test_missing_anchor_fails(self):
        self.assertIn("missing", parse_completion_summary("Policy: engineering-core")[1][0])

    def test_missing_policy_fails(self):
        text = report().replace("Policy: engineering-core\n", "")
        self.assertTrue(any("policy" in error for error in parse_completion_summary(text)[1]))

    def test_missing_status_fails(self):
        text = report().replace("Status: VERIFIED\n", "")
        self.assertTrue(any("status" in error for error in parse_completion_summary(text)[1]))

    def test_unknown_risk_fails(self):
        self.assertTrue(any("Risk" in error for error in parse_completion_summary(report("Tiny"))[1]))

    def test_unknown_status_fails(self):
        self.assertTrue(any("Status" in error for error in parse_completion_summary(report(status="COMPLETE"))[1]))

    def test_reports_missing_and_invalid_fields_together(self):
        text = report("Medium").replace("Limitations: None\n", "")
        errors = parse_completion_summary(text)[1]
        self.assertTrue(any("limitations" in error for error in errors))
        self.assertTrue(any("Risk" in error for error in errors))

    def test_markdown_table_fields(self):
        text = """### Execution Summary
| Field | Value |
|---|---|
| **Policy** | engineering-core |
| **Risk** | High |
| **Status** | VERIFIED |
| **Changed** | auth.py |
| **Verified** | python test_contract.py passed |
| **Limitations** | None |
"""
        parsed, errors = parse_completion_summary(text)
        self.assertEqual(errors, [])
        self.assertEqual((parsed.risk, parsed.status), ("High", "VERIFIED"))

    def test_verified_with_blocker_fails(self):
        self.assertTrue(any("blocker" in error for error in parse_completion_summary(report(extra="Blockers: Required test failed\n"))[1]))

    def test_last_anchor_controls(self):
        parsed, errors = parse_completion_summary(report(status="BLOCKED") + "\n" + report(status="VERIFIED"))
        self.assertEqual(errors, [])
        self.assertEqual(parsed.status, "VERIFIED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
