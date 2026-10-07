from __future__ import annotations

import unittest

from validate_repository import validate_workflow


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


if __name__ == "__main__":
    unittest.main()
