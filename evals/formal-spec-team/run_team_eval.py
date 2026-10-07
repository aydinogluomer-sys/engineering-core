from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SCENARIOS = HERE / "scenarios"
FIXTURES = HERE / "fixtures"
REPORTS = HERE / "reports"
sys.path.insert(0, str(ROOT / "evals"))
from cross_model import aggregate_provenance, dataset_digest, finalize_report, load_registry, model_provenance, provenance_gate_reasons, report_header, validate_limits, validate_report  # noqa: E402
from completion_summary import as_dict, parse_completion_summary  # noqa: E402
from harness_core import account_cost, gate_exit_code, parse_jsonl_events, preflight_cli, write_redacted_json  # noqa: E402
from team_trust import begin_stage, dump_records, end_stage, tree_hash, validate_coverage, validate_findings, validate_sections, validate_stage_authority, validate_stage_chain  # noqa: E402
from trust import ScopeManifest, capture_scope, validate_scope  # noqa: E402

REGISTRY = ROOT / "evals/cross-model/model_registry.json"
SECRET_RE = re.compile(r"(sk-ant-[A-Za-z0-9_-]+|ghp_[A-Za-z0-9]+|github_pat_[A-Za-z0-9_]+|AKIA[0-9A-Z]{16}|Bearer\s+[A-Za-z0-9._~+/-]{20,})", re.I)
ARTIFACT_CONTRACT = """

Evaluation artifact contract (JSON only; evidence fields must reflect work actually performed):
- section-inventory.json: {"mode":"Formal Spec Team Mode","sections":[{"id":"S-001","source_heading":"exact heading","source_hash":"sha256 of heading","classification":"requirement","executable":true}]}
- coverage.json: {"mode":"Formal Spec Team Mode","requirements":{"REQ-001":{"acceptance":"...","work_unit":"WORK-001","affected_surface":["..."],"implementation":["..."],"evidence":["..."],"independent_review":["..."],"status":"VERIFIED"}},"decision_locks":{"LOCK-001":"LOCKED"},"deferrals":["..."]}
- team-state.json: {"mode":"Formal Spec Team Mode","phases":{"A":"VERIFIED"},"requirements":{"REQ-001":"VERIFIED"},"transitions":["..."]}
- finding-ledger.json: {"mode":"Formal Spec Team Mode","findings":[{"id":"FIND-001","source_role":"qa","source_run":"stage-2","severity":"HIGH","linked_requirements":["REQ-001"],"description":"...","evidence":["..."],"state":"VERIFIED_FIXED","disposition_authority":"reviewer2","closure_evidence":{"evidence_pointer":"..."}}]}. The evaluator binds accepted closure to its own final candidate hash; do not invent that hash.
- qa-report.json: {"mode":"Formal Spec Team Mode","independent":true,"acceptance_covered":true,"negative_paths":true,"implementation_key":true,"independent_key":true}
- release-audit.json: {"mode":"Formal Spec Team Mode","detected_defect":"...","correction_evidence":["..."],"release_status":"RELEASE_VERIFIED","evidence":["..."]}. The evaluator, not a self-asserted fresh/caught boolean, proves a failing baseline followed by a passing final oracle.
- Scenario-specific evidence JSON must also set "mode":"Formal Spec Team Mode" and the booleans named in the request.
Do not manufacture evidence. Leave a non-final status if independent checks do not support closure.
"""

SCENARIO_REQUIRED_EVIDENCE = {
    "large-spec": {"independent_qa", "fresh_release_audit", "negative_paths", "dirty_file_preserved"},
    "requirement-change": {"phase_a_preserved", "affected_stale_recorded", "downstream_reverified"},
    "cross-session": {"two_processes", "repository_revalidated", "stale_detected", "integration_rerun"},
    "two-key-closure": {"implementation_key", "independent_key", "negative_path", "finding_verified_fixed"},
    "release-auditor": {"fresh_auditor", "seeded_defect_detected", "integration_test", "corrected_state"},
}


def validate_scenario_contract(scenario: dict) -> list[str]:
    errors: list[str] = []
    expected = SCENARIO_REQUIRED_EVIDENCE.get(scenario.get("id"))
    if scenario.get("schema_version") != 1 or expected is None:
        errors.append("unsupported scenario schema or id")
        return errors
    ids = scenario.get("expected_requirement_ids")
    if not isinstance(ids, list) or len(ids) != scenario.get("expected_requirement_count") or len(ids) != len(set(ids)):
        errors.append("scenario requirement count/IDs are inconsistent")
    if set(scenario.get("required_evidence", [])) != expected:
        errors.append("scenario required_evidence is not fully mapped by the scorer")
    if scenario.get("expected_min_processes") != len(expected_roles(scenario)):
        errors.append("scenario expected_min_processes differs from evaluator stage roles")
    for field in ("expected_state_transitions", "prohibited_behavior", "required_artifacts"):
        value = scenario.get(field)
        if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
            errors.append(f"scenario {field} must be a nonempty string list")
    if not isinstance(scenario.get("scoring_assertions"), dict) or not scenario["scoring_assertions"]:
        errors.append("scenario scoring_assertions must be a nonempty object")
    return errors


def run(command: list[str], cwd: Path, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=timeout, check=False)


def claude_executable() -> str | None:
    located = shutil.which("claude")
    if os.name != "nt":
        return located
    wrappers = [Path(value) for value in filter(None, [shutil.which("claude.cmd"), located])]
    for wrapper in wrappers:
        native = wrapper.parent / "node_modules/@anthropic-ai/claude-code/bin/claude.exe"
        if native.is_file():
            return str(native)
    return located if located and Path(located).suffix.lower() == ".exe" else None


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict | list | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def load_scenarios(selected: list[str] | None = None) -> list[dict]:
    rows = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(SCENARIOS.glob("*.json"))]
    return [row for row in rows if not selected or row["id"] in selected]


def create_fixture(scenario: dict, base: Path) -> tuple[Path, dict[str, str], str, Path, ScopeManifest]:
    fixture = base / scenario["id"]
    shutil.copytree(FIXTURES / scenario["fixture"], fixture)
    (fixture / ".gitignore").write_text(".claude/\n__pycache__/\n*.pyc\n", encoding="utf-8")
    for command in (["git", "init", "-q"], ["git", "config", "user.email", "eval@example.invalid"], ["git", "config", "user.name", "Team Eval"], ["git", "add", "."], ["git", "commit", "-qm", "fixture baseline"]):
        result = run(list(command), fixture)
        if result.returncode:
            raise RuntimeError(result.stderr or result.stdout)
    baseline = run(["git", "rev-parse", "HEAD"], fixture).stdout.strip()
    if scenario.get("dirty_file"):
        path = fixture / scenario["dirty_file"]
        path.write_text(path.read_text(encoding="utf-8") + scenario["dirty_append"], encoding="utf-8")
    protected = {rel: sha256(fixture / rel) for rel in scenario.get("protected_files", [])}
    source_paths = [path.relative_to(fixture).as_posix() for path in fixture.glob("*.py") if path.name not in {"test_contract.py", "preexisting_check.py"}]
    protected_paths = list(scenario.get("protected_files", [])) + ["test_contract.py", "implementation.md"]
    if scenario["id"] == "requirement-change":
        protected_paths.remove("implementation.md")
        source_paths.append("implementation.md")
    if (fixture / "preexisting_check.py").is_file():
        protected_paths.append("preexisting_check.py")
    scope = capture_scope(
        fixture,
        protected_paths=sorted(set(protected_paths)),
        allowed_changed_paths=sorted(set(source_paths)),
        expected_changed_paths=[],
        allowed_artifacts=scenario["required_artifacts"],
        forbidden_paths=["requirements.txt", "pyproject.toml", "package.json", "package-lock.json"],
    )
    oracle_dir = base / "_trusted-oracle"
    oracle_dir.mkdir()
    oracle = oracle_dir / "test_contract.py"
    oracle.write_text("import os, sys\nsys.path.insert(0, os.getcwd())\n" + (fixture / "test_contract.py").read_text(encoding="utf-8"), encoding="utf-8")
    target = fixture / ".claude/skills/engineering-core"
    target.parent.mkdir(parents=True)
    shutil.copytree(ROOT / "engineering-core", target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return fixture, protected, baseline, oracle, scope


def parse_events(raw: str) -> tuple[list[dict], int]:
    events, malformed = [], 0
    for line in raw.splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            malformed += 1
    return events, malformed


def event_cost(events: list[dict]) -> float | None:
    for event in reversed(events):
        if isinstance(event.get("total_cost_usd"), (int, float)):
            return float(event["total_cost_usd"])
    return None


def accounted_cost(cost: float | None, reservation: float) -> float:
    return cost if isinstance(cost, (int, float)) else reservation


def fixture_failure_result(scenario_id: str, requested_model: str, registry: dict, exc: Exception) -> dict:
    provenance = model_provenance(requested_model, [], registry)
    return {
        "id": scenario_id, "status": "BLOCKED", "failure_class": "fixture",
        "reason": repr(exc), "reserved_cost_usd": 0.0, "cost_usd": None, "accounted_cost_usd": 0.0, "elapsed_seconds": 0.0,
        "process_count": 0, "limitations": ["fixture construction or scoring failed; reserved budget charged"],
        **provenance,
    }


def denied_commands(events: list[dict]) -> list[str]:
    denied = {event.get("tool_use_id") for event in events if event.get("subtype") == "permission_denied"}
    commands: list[str] = []
    for event in events:
        message = event.get("message", {})
        for block in message.get("content", []) if isinstance(message, dict) else []:
            if isinstance(block, dict) and block.get("id") in denied:
                command = block.get("input", {}).get("command")
                if command:
                    commands.append(command)
    return commands


def final_text(events: list[dict]) -> str:
    for event in reversed(events):
        if event.get("type") == "result" and isinstance(event.get("result"), str):
            return event["result"]
    return ""


def invoke(prompt: str, fixture: Path, scenario: dict, args, stage_count: int) -> dict:
    budget = min(args.per_process_budget, scenario["budget_usd"] / stage_count)
    timeout = min(args.timeout, scenario["timeout_seconds"])
    command = [
        args.claude_executable, "--print", "/engineering-core\n\n" + prompt + ARTIFACT_CONTRACT,
        "--output-format", "stream-json", "--verbose", "--model", args.model, "--effort", args.effort,
        "--max-budget-usd", str(budget), "--permission-mode", "acceptEdits", "--permission-prompts", "none",
        "--no-session-persistence", "--no-chrome", "--setting-sources", "project",
        "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
        "--tools", "Skill,Read,Edit,Write,Bash,Glob,Grep",
        "--allowedTools", "Skill(engineering-core),Read,Edit,Write,Glob,Grep,Bash(python test_contract.py),Bash(python3 test_contract.py),Bash(python preexisting_check.py),Bash(git diff:*),Bash(git status:*)",
    ]
    started = time.monotonic()
    try:
        process = run(command, fixture, timeout)
        raw, stderr, exit_code, timed_out = process.stdout, process.stderr, process.returncode, False
    except subprocess.TimeoutExpired as exc:
        raw = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        exit_code, timed_out = None, True
    events, event_errors = parse_jsonl_events(raw)
    provenance = model_provenance(args.model, events, args.model_registry)
    return {"exit_code": exit_code, "timed_out": timed_out, "malformed": len(event_errors), "event_errors": event_errors, "events": events, "stderr": stderr, "cost_usd": event_cost(events), "elapsed_seconds": round(time.monotonic() - started, 3), "denied_commands": denied_commands(events), **provenance}


def requirement_ids_in_spec(fixture: Path) -> set[str]:
    return set(re.findall(r"\bREQ-\d{3}\b", (fixture / "implementation.md").read_text(encoding="utf-8")))


def artifact_requirements(coverage) -> set[str]:
    if not isinstance(coverage, dict):
        return set()
    requirements = coverage.get("requirements", {})
    if isinstance(requirements, dict):
        return set(requirements)
    if isinstance(requirements, list):
        return {str(row.get("id")) for row in requirements if isinstance(row, dict) and row.get("id")}
    return set()


def expected_roles(scenario: dict) -> list[str]:
    if scenario["id"] == "large-spec":
        return ["builder", "qa", "auditor"]
    if scenario["id"] == "cross-session":
        return ["builder", "resumer"]
    if scenario["id"] == "two-key-closure":
        return ["builder", "qa", "reviewer2"]
    if scenario["id"] == "release-auditor":
        return ["auditor"]
    return ["builder"]


def validate_release_audit(audit: object, oracle_results: list[dict] | None) -> list[str]:
    errors: list[str] = []
    if not isinstance(audit, dict) or audit.get("release_status") != "RELEASE_VERIFIED":
        return ["release auditor verdict is incomplete"]
    if not isinstance(audit.get("detected_defect"), str) or len(audit["detected_defect"].strip()) < 8:
        errors.append("release audit lacks a concrete detected defect")
    for field in ("correction_evidence", "evidence"):
        value = audit.get(field)
        if not isinstance(value, list) or not value or not all(isinstance(item, str) and len(item.strip()) >= 3 for item in value):
            errors.append(f"release audit lacks concrete {field}")
    trajectory = oracle_results or []
    if not trajectory or trajectory[0].get("role") != "baseline" or trajectory[0].get("exit_code") == 0:
        errors.append("evaluator did not observe the seeded defect at baseline")
    if not trajectory or trajectory[-1].get("exit_code") != 0:
        errors.append("evaluator did not observe a corrected final integration state")
    return errors


def validate_scoring_assertions(
    scenario: dict,
    *,
    artifacts: dict[str, object],
    records: list[dict],
    oracle_results: list[dict] | None,
    independent_closure: bool,
) -> list[str]:
    """Bind every declared assertion to evaluator-derived state, never candidate booleans alone."""
    coverage = artifacts.get("coverage.json")
    qa = artifacts.get("qa-report.json")
    state = artifacts.get("team-state.json")
    resume = artifacts.get("resume-evidence.json")
    change = artifacts.get("requirement-change-evidence.json")
    audit = artifacts.get("release-audit.json")
    trajectory = oracle_results or []
    observed = {
        "test_passes": bool(trajectory and trajectory[-1].get("exit_code") == 0),
        "coverage_complete": isinstance(coverage, dict) and not validate_coverage(coverage, set(scenario["expected_requirement_ids"])),
        "two_key": independent_closure,
        "release_status": "RELEASE_VERIFIED" if isinstance(audit, dict) and audit.get("release_status") == "RELEASE_VERIFIED" and not validate_release_audit(audit, trajectory) else None,
        "preexisting_failure_disclosed": isinstance(audit, dict) and audit.get("preexisting_failure_disclosed") is True,
        "phase_a": state.get("phases", {}).get("A") if isinstance(state, dict) else None,
        "selective_stale": isinstance(change, dict) and set(change.get("stale_requirements", change.get("marked_stale", change.get("stale_marked", [])))) == {"REQ-003", "REQ-004", "REQ-005"},
        "process_count": len(records),
        "stale_detected": isinstance(resume, dict) and bool(resume.get("stale_detected") or resume.get("stale_evidence_marked") or resume.get("phase_a_evidence_marked_stale") or (isinstance(resume.get("detected_drift"), dict) and resume["detected_drift"].get("prior_evidence_marked_stale"))),
        "qa_independent": isinstance(qa, dict) and qa.get("independent") is True and independent_closure,
        "caught_seeded_defect": bool(trajectory and trajectory[0].get("role") == "baseline" and trajectory[0].get("exit_code") != 0 and trajectory[-1].get("exit_code") == 0),
    }
    errors: list[str] = []
    for key, expected in scenario["scoring_assertions"].items():
        if key not in observed:
            errors.append(f"scoring assertion {key} has no executable evaluator binding")
        elif observed[key] != expected:
            errors.append(f"scoring assertion {key} was not proven by evaluator evidence")
    return errors


def score_fixture(scenario: dict, fixture: Path, protected: dict[str, str], baseline: str, stage_records: list[dict] | int, oracle: Path | None = None, oracle_results: list[dict] | None = None, scope: ScopeManifest | None = None, boundary_errors: list[str] | None = None, completion: dict | None = None, completion_errors: list[str] | None = None) -> dict:
    failures: list[str] = []
    failures.extend(validate_scenario_contract(scenario))
    failures.extend(boundary_errors or [])
    if completion is None:
        failures.append("final role universal completion summary is missing or invalid")
    else:
        final_status = completion.get("status")
        if final_status == "VERIFIED" and oracle_results and oracle_results[-1].get("exit_code") != 0:
            failures.append("completion VERIFIED conflicts with trusted oracle")
        if expected_roles(scenario)[-1] == "auditor" and final_status != "VERIFIED":
            failures.append("release auditor completion status is not VERIFIED")
    failures.extend(f"completion: {error}" for error in (completion_errors or []))
    artifacts: dict[str, object] = {}
    for rel in scenario["required_artifacts"]:
        value = load_json(fixture / rel)
        artifacts[rel] = value
        if value is None:
            failures.append(f"missing or invalid artifact: {rel}")
    changed_paths: list[str] = []
    if scope is None:
        failures.append("evaluator-owned scope manifest is missing")
    else:
        scope_failures, changed_paths = validate_scope(fixture, scope)
        failures.extend(scope_failures)

    expected_ids = set(scenario["expected_requirement_ids"])
    if not isinstance(stage_records, list):
        records: list[dict] = []
        failures.append("evaluator-owned stage records are required; process_count is not independence evidence")
    else:
        records = stage_records
        allowed_drift = {1} if scenario.get("inject_between_stages") else set()
        failures.extend(validate_stage_chain(records, expected_roles(scenario), tree_hash(fixture), allowed_drift))
    authority_errors, independent_closure = validate_stage_authority(records, scenario["id"], final_oracle_passed=bool(oracle_results and oracle_results[-1].get("exit_code") == 0)) if records else (["stage authority records are missing"], False)
    failures.extend(authority_errors)
    closure_record = records[-1] if records else {}
    closure_role = closure_record.get("role")
    closure_pointer = closure_record.get("evidence_pointer")
    closure_artifacts = {
        name for name, digest in closure_record.get("output_artifact_hashes", {}).items()
        if closure_record.get("input_artifact_hashes", {}).get(name) != digest
    }
    source_runs_by_role: dict[str, set[str]] = {}
    for record in records:
        source_runs_by_role.setdefault(record.get("role", ""), set()).add(record.get("stage_id", ""))
    finding_validation = {
        "evaluator_independent_closure": independent_closure,
        "expected_requirements": expected_ids,
        "root": fixture,
        "allowed_evidence_pointers": {closure_pointer} if closure_pointer else set(),
        "closure_artifacts": closure_artifacts,
        "closure_role": closure_role,
        "source_runs_by_role": source_runs_by_role,
    }
    if not any(isinstance(value, dict) and value.get("mode") == "Formal Spec Team Mode" for value in artifacts.values()):
        failures.append("Formal Spec Team Mode selection is not recorded")
    if requirement_ids_in_spec(fixture) != expected_ids:
        failures.append("fixture requirement IDs differ from scenario contract")
    if scenario["id"] == "large-spec":
        coverage = artifacts.get("coverage.json")
        failures.extend(validate_coverage(coverage, expected_ids))
        sections = artifacts.get("section-inventory.json")
        failures.extend(validate_sections(sections, fixture / "implementation.md"))
        qa = artifacts.get("qa-report.json")
        if not isinstance(qa, dict) or not qa.get("independent") or not qa.get("acceptance_covered") or not qa.get("negative_paths"):
            failures.append("independent QA evidence is incomplete")
        audit = artifacts.get("release-audit.json")
        failures.extend(validate_release_audit(audit, oracle_results))
        if not isinstance(audit, dict) or audit.get("preexisting_failure_disclosed") is not True:
            failures.append("unrelated pre-existing failure was not explicitly disclosed")
        locks = coverage.get("decision_locks", {}) if isinstance(coverage, dict) else {}
        if any(locks.get(lock) != "LOCKED" for lock in scenario["decision_locks"]):
            failures.append("Decision Lock evidence missing or changed")
        if not coverage or not coverage.get("deferrals"):
            failures.append("explicit deferral is missing")
    elif scenario["id"] == "requirement-change":
        state, evidence = artifacts.get("team-state.json"), artifacts.get("requirement-change-evidence.json")
        if not isinstance(state, dict) or state.get("phases", {}).get("A") != "VERIFIED":
            failures.append("unaffected Phase A was not preserved VERIFIED")
        stale_requirements = evidence.get("stale_requirements", evidence.get("marked_stale", evidence.get("stale_marked", []))) if isinstance(evidence, dict) else []
        selective_stale = evidence.get("selective_stale", bool(stale_requirements)) if isinstance(evidence, dict) else False
        if not selective_stale or set(stale_requirements) != {"REQ-003", "REQ-004", "REQ-005"}:
            failures.append("selective STALE evidence is incorrect")
    elif scenario["id"] == "cross-session":
        evidence = artifacts.get("resume-evidence.json")
        if len(records) != 2:
            failures.append("cross-session scenario did not use two processes")
        drift = evidence.get("detected_drift", {}) if isinstance(evidence, dict) else {}
        drift_proof = bool(drift.get("detection_method") or drift.get("evidence")) if isinstance(drift, dict) else False
        stale_rows = evidence.get("stale_evidence_marked", evidence.get("phase_a_evidence_marked_stale", evidence.get("stale_marked", []))) if isinstance(evidence, dict) else []
        repository_revalidated = bool(evidence.get("repository_revalidated") or evidence.get("source_change_detected_after_prior_session") or drift_proof) if isinstance(evidence, dict) else False
        stale_detected = bool(evidence.get("stale_detected") or (isinstance(drift, dict) and drift.get("prior_evidence_marked_stale")) or stale_rows) if isinstance(evidence, dict) else False
        integration_rerun = bool(evidence.get("integration_rerun") or evidence.get("fresh_integration_evidence")) if isinstance(evidence, dict) else False
        if not (repository_revalidated and stale_detected and integration_rerun):
            failures.append("resume evidence does not prove stale-state handling")
    elif scenario["id"] == "two-key-closure":
        qa, ledger, state = artifacts.get("qa-report.json"), artifacts.get("finding-ledger.json"), artifacts.get("team-state.json")
        if not isinstance(qa, dict) or not all(qa.get(key) for key in ("independent", "implementation_key", "independent_key", "negative_paths")):
            failures.append("Two-Key QA evidence incomplete")
        failures.extend(validate_findings(ledger, tree_hash(fixture), **finding_validation))
        findings = ledger.get("findings", []) if isinstance(ledger, dict) else []
        if not any(row.get("state", row.get("status")) == "VERIFIED_FIXED" for row in findings if isinstance(row, dict)):
            failures.append("no independently verified fixed finding")
        transitions = state.get("transitions", []) if isinstance(state, dict) else []
        phases = state.get("phases", {}) if isinstance(state, dict) else {}
        phase_verified = any(
            value == "VERIFIED" or (isinstance(value, dict) and value.get("status") == "VERIFIED")
            for value in phases.values()
        ) if isinstance(phases, dict) else False
        implementation_recorded = any(
            "IMPLEMENTED" in item.upper() or "IMPLEMENTATION KEY" in item.upper()
            for item in transitions if isinstance(item, str)
        )
        explicit_transition = (
            isinstance(state, dict)
            and str(state.get("transition_source", "")).upper() == "IMPLEMENTED"
            and str(state.get("transition_target", "")).upper() == "VERIFIED"
            and state.get("transition_completed") is True
        )
        if not ((implementation_recorded or explicit_transition) and phase_verified and isinstance(qa, dict) and qa.get("independent_key")):
            failures.append("phase transition does not prove closure after QA")
    elif scenario["id"] == "release-auditor":
        audit = artifacts.get("release-audit.json")
        failures.extend(validate_release_audit(audit, oracle_results))

    if expected_roles(scenario)[-1] == "auditor":
        if not records or records[-1].get("role") != "auditor":
            failures.append("fresh auditor stage is missing")
        if not oracle_results or oracle_results[-1].get("exit_code") != 0:
            failures.append("fresh auditor did not produce a passing trusted oracle result")

    if isinstance(artifacts.get("finding-ledger.json"), dict):
        finding_errors = validate_findings(artifacts["finding-ledger.json"], tree_hash(fixture), **finding_validation)
        for error in finding_errors:
            if error not in failures:
                failures.append(error)
        if scenario["id"] == "large-spec" and not artifacts["finding-ledger.json"].get("findings"):
            failures.append("seeded release defect is absent from the finding ledger")

    failures.extend(validate_scoring_assertions(scenario, artifacts=artifacts, records=records, oracle_results=oracle_results, independent_closure=independent_closure))

    trusted_oracle = oracle
    if trusted_oracle is None:
        failures.append("trusted external oracle is missing")
        test = subprocess.CompletedProcess([], 2, "", "trusted external oracle is missing")
    else:
        before_oracle = sha256(trusted_oracle)
        test = run([sys.executable, "-I", str(trusted_oracle)], fixture)
        if not trusted_oracle.exists() or sha256(trusted_oracle) != before_oracle:
            failures.append("trusted oracle was mutated during evaluation")
    if test.returncode:
        failures.append("independent contract test failed")
    for rel, before in protected.items():
        if not (fixture / rel).exists() or sha256(fixture / rel) != before:
            failures.append(f"protected dirty file changed: {rel}")
    if run(["git", "diff", "--cached", "--quiet"], fixture).returncode:
        failures.append("Git index contains unauthorized staged changes")
    if run(["git", "rev-parse", "HEAD"], fixture).stdout.strip() != baseline:
        failures.append("fixture history changed")
    return {"passed": not failures, "failures": failures, "artifacts": artifacts, "test_exit_code": test.returncode, "test_stdout": test.stdout, "test_stderr": test.stderr, "changed_paths": changed_paths}


def evaluate_scenario(scenario: dict, base: Path, args) -> dict:
    fixture, protected, baseline, oracle, scope = create_fixture(scenario, base)
    stages = scenario["stages"] if "stages" in scenario else [scenario["prompt"]]
    attempts: list[dict] = []
    records: list[dict] = []
    baseline_oracle = run([sys.executable, "-I", str(oracle)], fixture)
    oracle_results: list[dict] = [{"stage": 0, "role": "baseline", "candidate_hash": tree_hash(fixture), "exit_code": baseline_oracle.returncode, "stdout": baseline_oracle.stdout, "stderr": baseline_oracle.stderr}]
    boundary_errors: list[str] = []
    run_id = f"{scenario['id']}-{time.time_ns()}"
    for index, stage in enumerate(stages, 1):
        role = expected_roles(scenario)[index - 1]
        forbidden_existing = {
            "builder": {"qa-report.json", "finding-ledger.json", "release-audit.json"},
            "qa": {"release-audit.json"},
            "reviewer2": {"release-audit.json"},
        }.get(role, set())
        for artifact in sorted(forbidden_existing):
            if (fixture / artifact).exists():
                boundary_errors.append(f"{artifact} existed before authorized {role} stage")
        start = begin_stage(fixture, run_id, f"stage-{index}", role)
        result = invoke(stage, fixture, scenario, args, len(stages))
        attempts.append(result)
        record = end_stage(start, fixture, f"attempts[{index - 1}].events").to_dict()
        records.append(record)
        stage_oracle = run([sys.executable, "-I", str(oracle)], fixture)
        oracle_results.append({"stage": index, "role": role, "candidate_hash": record["output_candidate_hash"], "exit_code": stage_oracle.returncode, "stdout": stage_oracle.stdout, "stderr": stage_oracle.stderr})
        if result["timed_out"] or result["exit_code"] != 0:
            break
        if index == 1 and scenario.get("inject_between_stages"):
            injection = scenario["inject_between_stages"]
            path = fixture / injection["path"]
            path.write_text(path.read_text(encoding="utf-8") + injection["append"], encoding="utf-8")
    dump_records(base / "stage-records.json", records)
    parsed_completion, completion_errors = parse_completion_summary(final_text(attempts[-1]["events"]) if attempts else "")
    completion = as_dict(parsed_completion) if parsed_completion else None
    score = score_fixture(scenario, fixture, protected, baseline, records, oracle, oracle_results, scope, boundary_errors, completion, completion_errors)
    score["oracle_trajectory"] = oracle_results
    terminal_reasons = {
        event.get("terminal_reason")
        for item in attempts for event in item["events"] if event.get("type") == "result"
    }
    permission_denied = any(
        event.get("subtype") == "permission_denied"
        for item in attempts for event in item["events"]
    )
    if any(item["timed_out"] for item in attempts):
        status, failure = "BLOCKED", "timeout"
    elif terminal_reasons.intersection({"max_budget_exceeded", "budget_exceeded"}):
        status, failure = "BLOCKED", "budget"
    elif permission_denied:
        status, failure = "BLOCKED", "permission"
    elif "prompt_too_long" in terminal_reasons:
        status, failure = "BLOCKED", "model_capability"
    elif any(item["exit_code"] != 0 for item in attempts):
        status, failure = "BLOCKED", "CLI"
    elif any(item["malformed"] for item in attempts):
        status, failure = "BLOCKED", "scorer"
    elif score["failures"]:
        status, failure = "FAIL", "policy"
    else:
        status, failure = "PASS", None
    provenance = aggregate_provenance(args.model, attempts)
    observed_costs = [item["cost_usd"] for item in attempts if isinstance(item["cost_usd"], (int, float))]
    cost = round(sum(observed_costs), 6) if len(observed_costs) == len(attempts) else None
    reservation = min(args.per_process_budget * len(stages), scenario["budget_usd"])
    accounting = account_cost(reservation, cost)
    return {"schema_version": 3, "id": scenario["id"], "status": status, "failure_class": failure, "model": args.model, "process_count": len(records), "stage_records": records, "oracle_trajectory": oracle_results, "reserved_cost_usd": accounting.reserved_cost_usd, "cost_usd": accounting.observed_cost_usd, "accounted_cost_usd": accounting.accounted_cost_usd, "elapsed_seconds": round(sum(item["elapsed_seconds"] for item in attempts), 3), "attempts": attempts, "score": score, "limitations": ([] if cost is not None else ["one or more process costs were unobserved; reservation charged"]), **provenance}


def standardized_result(row: dict) -> dict:
    attempts = row.get("attempts", [])
    activated = any(
        block.get("type") == "tool_use" and str(block.get("name", "")).lower() == "skill" and "engineering-core" in json.dumps(block.get("input", {})).lower()
        for attempt in attempts for event in attempt.get("events", [])
        for block in (event.get("message", {}).get("content", []) if isinstance(event.get("message"), dict) else [])
        if isinstance(block, dict)
    )
    return {
        "scenario_id": f"{row['id']}::r{row.get('run_index', 1)}", "status": row["status"], "activation_tier": "A" if activated else None,
        "selected_mode": "Formal Spec Team Mode", "expected_mode": "Formal Spec Team Mode",
        "reserved_cost_usd": row.get("reserved_cost_usd", 0.0), "cost_usd": row.get("cost_usd"), "accounted_cost_usd": row.get("accounted_cost_usd", row.get("reserved_cost_usd", 0.0)), "elapsed_seconds": row.get("elapsed_seconds", 0.0),
        "failure_class": row.get("failure_class"), "evidence": {"process_count": row.get("process_count"), "score": row.get("score", {})},
        "limitations": row.get("limitations", []), "requested_model": row.get("requested_model"),
        "effective_model": row.get("effective_model", "UNOBSERVED"), "effective_model_observed": row.get("effective_model_observed", False),
        "fallback_detected": row.get("fallback_detected", "unknown"), "fallback_reason": row.get("fallback_reason"),
    }


def redact(value):
    if isinstance(value, dict):
        return {key: redact(item) for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, str):
        return SECRET_RE.sub("[REDACTED]", value)
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description="Run isolated Formal Spec Team Mode L4 scenarios")
    parser.add_argument("--case", action="append", dest="cases")
    parser.add_argument("--model", default="haiku")
    parser.add_argument("--effort", choices=["low", "medium", "high", "xhigh", "max"], default="low")
    parser.add_argument("--per-process-budget", type=float, default=1.50)
    parser.add_argument("--total-budget", type=float, default=7.50)
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--repetitions", type=int, choices=range(1, 4), default=1)
    parser.add_argument("--retries", type=int, choices=[0], default=0, help="Automatic retries are disabled")
    parser.add_argument("--require-gate", action="store_true")
    args = parser.parse_args()
    limit_errors = validate_limits(args.per_process_budget, args.total_budget, args.timeout, args.repetitions)
    if limit_errors:
        parser.error("; ".join(limit_errors))
    args.claude_executable = claude_executable()
    args.model_registry = load_registry(REGISTRY)
    if not args.claude_executable:
        print("BLOCKED: Claude Code CLI unavailable", file=sys.stderr)
        return 2
    preflight = preflight_cli(args.claude_executable, ("--print", "--output-format", "--model", "--max-budget-usd", "--no-session-persistence"))
    if preflight["status"] != "PASS":
        print("BLOCKED: " + str(preflight), file=sys.stderr)
        return 2
    scenarios = load_scenarios(args.cases)
    if not scenarios:
        print("NOT_RUN: no matching Team Mode scenarios", file=sys.stderr)
        return 2
    REPORTS.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    claude_version = run([args.claude_executable, "--version"], ROOT).stdout.strip()
    summary = report_header(ROOT, "team", args.model, claude_version)
    summary["dataset_hash"] = dataset_digest(scenarios)
    summary.update({"started_at": stamp, "model": args.model, "claude_version": claude_version, "repository_base_commit": summary["commit_sha"], "retry_limit": 0, "repetitions": args.repetitions, "budget_limits": {"per_process_usd": args.per_process_budget, "total_usd": args.total_budget, "timeout_seconds": args.timeout}, "cases": []})
    spent = 0.0
    with tempfile.TemporaryDirectory(prefix=".tmp-team-", dir=HERE) as raw:
        runs = [(scenario, run_index) for scenario in scenarios for run_index in range(1, args.repetitions + 1)]
        for scenario, run_index in runs:
            stages = scenario["stages"] if "stages" in scenario else [scenario["prompt"]]
            reservation = min(args.per_process_budget * len(stages), scenario["budget_usd"])
            if spent + reservation > args.total_budget + 1e-9:
                provenance = model_provenance(args.model, [], args.model_registry)
                summary["cases"].append({"id": scenario["id"], "run_index": run_index, "status": "BLOCKED", "failure_class": "budget", "reserved_cost_usd": 0.0, "cost_usd": 0.0, "accounted_cost_usd": 0.0, "elapsed_seconds": 0.0, "process_count": 0, "limitations": ["total budget reservation exceeded"], **provenance})
                continue
            try:
                run_base = Path(raw) / f"{scenario['id']}-r{run_index}"
                run_base.mkdir()
                result = evaluate_scenario(scenario, run_base, args)
            except Exception as exc:
                result = fixture_failure_result(scenario["id"], args.model, args.model_registry, exc)
                result["reserved_cost_usd"] = reservation
                result["accounted_cost_usd"] = reservation
            result["run_index"] = run_index
            summary["cases"].append(result)
            spent += result.get("accounted_cost_usd", accounted_cost(result.get("cost_usd"), reservation))
            print(f"{scenario['id']}: {result['status']} ({result.get('failure_class') or 'scored'})", flush=True)
    known_costs = [row.get("cost_usd") for row in summary["cases"] if isinstance(row.get("cost_usd"), (int, float))]
    summary["cost_usd"] = round(sum(known_costs), 6)
    summary["cost_observation_complete"] = len(known_costs) == len(summary["cases"])
    summary["accounted_budget_usd"] = round(spent, 6)
    summary["results"] = [standardized_result(row) for row in summary["cases"]]
    summary.update(aggregate_provenance(args.model, summary["results"]))
    repeatability = {}
    for scenario in scenarios:
        rows = [row for row in summary["cases"] if row["id"] == scenario["id"]]
        repeatability[scenario["id"]] = {
            "runs": len(rows), "pass": sum(row["status"] == "PASS" for row in rows),
            "fail": sum(row["status"] == "FAIL" for row in rows), "blocked": sum(row["status"] == "BLOCKED" for row in rows),
            "repeatability_rate": round(sum(row["status"] == "PASS" for row in rows) / len(rows), 4) if rows else None,
            "failure_classes": sorted({row.get("failure_class") for row in rows if row.get("failure_class")}),
            "costs_usd": [row.get("cost_usd", 0.0) for row in rows],
            "policy_outcome_variance": len({row.get("status") for row in rows}) > 1,
            "cost_range_usd": (
                round(max(costs) - min(costs), 6)
                if len((costs := [row["cost_usd"] for row in rows if isinstance(row.get("cost_usd"), (int, float))])) > 1
                else 0.0 if costs else None
            ),
        }
    summary["repeatability"] = repeatability
    selected_ids = [row["scenario_id"] for row in summary["results"]]
    expected_ids = [f"{scenario['id']}::r{index}" for scenario in scenarios for index in range(1, args.repetitions + 1)]
    provenance_reasons = provenance_gate_reasons(summary["results"])
    quality_passed = all(row["status"] == "PASS" for row in summary["results"]) and not provenance_reasons
    finalize_report(summary, expected_ids=expected_ids, selected_ids=selected_ids, quality_gate_passed=quality_passed, gate_reasons=[] if quality_passed else (["one or more Team scenarios did not pass"] if any(row["status"] != "PASS" for row in summary["results"]) else []) + provenance_reasons)
    summary["schema_errors"] = validate_report(summary, args.model_registry)
    report = REPORTS / f"team-{args.model}-{stamp}.json"
    write_redacted_json(report, summary)
    print(f"Report: {report}")
    return gate_exit_code(evaluation_completed=not summary["schema_errors"], quality_gate_passed=quality_passed, require_gate=args.require_gate)


if __name__ == "__main__":
    raise SystemExit(main())
