from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evals"))
from harness_core import redact, tracked_secret_findings  # noqa: E402
sys.path.insert(0, str(ROOT / "evals/failure-resistance"))
from failure_resistance import capability_matrix, protected_stack_hash, validate_stack_report  # noqa: E402

COMMANDS = [
    [sys.executable, "engineering-core/scripts/validate_skill.py", "engineering-core"],
    [sys.executable, "engineering-core/scripts/test_validate_skill.py"],
    [sys.executable, "-m", "unittest", "discover", "-s", "evals", "-p", "test_*.py"],
    [sys.executable, "-m", "unittest", "discover", "-s", "evals/activation", "-p", "test_*.py"],
    [sys.executable, "-m", "unittest", "discover", "-s", "evals/formal-spec-team", "-p", "test_*.py"],
    [sys.executable, "-m", "unittest", "discover", "-s", "evals/cross-model", "-p", "test_*.py"],
    [sys.executable, "-m", "unittest", "discover", "-s", "evals/failure-resistance", "-p", "test_*.py"],
    [sys.executable, "scripts/test_install.py"],
    [sys.executable, "scripts/test_validate_repository.py"],
    [sys.executable, "scripts/validate_repository.py", "."],
    [sys.executable, "-m", "compileall", "-q", "engineering-core", "scripts", "evals"],
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def candidate_manifest(output: Path, root: Path = ROOT) -> dict[str, str]:
    rows: dict[str, str] = {}
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        if ".git" in path.parts or "__pycache__" in path.parts or "reports" in path.parts or any(part.startswith(".tmp-") for part in path.parts):
            continue
        try:
            path.relative_to(output)
        except ValueError:
            pass
        else:
            continue
        rows[path.relative_to(root).as_posix()] = sha256(path)
    return rows


def build(output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    command_rows = []
    for command in COMMANDS:
        process = subprocess.run(command, cwd=ROOT, text=True, encoding="utf-8", errors="replace", capture_output=True, check=False)
        command_rows.append({"command": command, "exit_code": process.returncode, "stdout_tail": process.stdout[-4000:], "stderr_tail": process.stderr[-4000:]})
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=False).stdout.strip()
    source_paths = [ROOT / "engineering-core/SKILL.md", *sorted((ROOT / "engineering-core/references").glob("*.md"))]
    manifest = candidate_manifest(output)
    manifest_digest = hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    integration_path = output / "integrations.json"
    integration_report = None
    integration_errors = ["integration report is missing"]
    if integration_path.is_file():
        try:
            integration_report = json.loads(integration_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            integration_errors = [f"integration report is invalid JSON: {exc}"]
        else:
            integration_errors = validate_stack_report(integration_report)
            if integration_report.get("protected_inputs_sha256") != protected_stack_hash(ROOT):
                integration_errors.append("integration report does not match current protected fixtures/oracles")
    cells = {
        "skill_structure": command_rows[0]["exit_code"] == 0 and command_rows[1]["exit_code"] == 0,
        "core_harness": command_rows[2]["exit_code"] == 0,
        "activation_static": command_rows[3]["exit_code"] == 0,
        "team_static": command_rows[4]["exit_code"] == 0,
        "cross_model_static": command_rows[5]["exit_code"] == 0,
        "failure_resistance_static": command_rows[6]["exit_code"] == 0,
        "installer": command_rows[7]["exit_code"] == 0,
        "workflow_mutations": command_rows[8]["exit_code"] == 0,
        "repository_hygiene": command_rows[9]["exit_code"] == 0,
        "compile": command_rows[10]["exit_code"] == 0,
        "stack_integrations": not integration_errors,
    }
    evidence = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repository_commit": head,
        "environment": {"python": platform.python_version(), "platform": platform.platform()},
        "source_manifest": {path.relative_to(ROOT).as_posix(): sha256(path) for path in source_paths},
        "candidate_manifest_sha256": manifest_digest,
        "candidate_manifest": manifest,
        "active_spec_sha256": sha256(ROOT / "implementation-v6.md"),
        "commands": command_rows,
        "local_cells": {name: "PASS" if passed else "FAIL" for name, passed in cells.items()},
        "all_local_commands_passed": all(row["exit_code"] == 0 for row in command_rows),
        "all_current_local_gates_passed": all(row["exit_code"] == 0 for row in command_rows) and not integration_errors,
        "observed_model_identity": "NOT_OBSERVED_NO_LIVE_RUN",
        "stack_capabilities": ({
            name: {
                "status": cell["status"],
                "actual_tool_version": cell["tool_version"],
                "evidence": "evidence/current/integrations.json",
            }
            for name, cell in integration_report["cells"].items()
        } if integration_report and not integration_errors else capability_matrix()),
        "stack_integration_report_sha256": sha256(integration_path) if integration_path.is_file() else None,
        "stack_integration_validation_errors": integration_errors,
        "live_model_matrix": "NOT_RUN",
        "pressure_harness_static": "PASS" if cells["core_harness"] else "FAIL",
        "pressure_live": "NOT_RUN",
        "longitudinal_field": "IN_PROGRESS",
        "github_governance": "NOT_APPLIED",
        "publication": "NOT_AUTHORIZED",
        "limitations": ["live-model campaign is not authorized without MAX_TOTAL_SPEND_USD", "hashes prove integrity, not semantic correctness", "seven-day L5 field evidence is in progress"],
    }
    evidence = redact(evidence)
    evidence_path = output / "evidence.json"
    evidence_path.write_text(json.dumps(evidence, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    manifest = {path.name: sha256(path) for path in sorted(output.glob("*.json")) if path.name != "SHA256SUMS.json"}
    (output / "SHA256SUMS.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    findings = tracked_secret_findings(ROOT)
    if findings:
        print("tracked secret-like material: " + ", ".join(findings), file=sys.stderr)
        return 2
    return 0 if evidence["all_local_commands_passed"] else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "evidence/current")
    args = parser.parse_args()
    return build(args.output.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
