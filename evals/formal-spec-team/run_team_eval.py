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
from cross_model import aggregate_provenance, load_registry, model_provenance, report_header, validate_limits, validate_report  # noqa: E402

REGISTRY = ROOT / "evals/cross-model/model_registry.json"
SECRET_RE = re.compile(r"(sk-ant-[A-Za-z0-9_-]+|ghp_[A-Za-z0-9]+|github_pat_[A-Za-z0-9_]+|AKIA[0-9A-Z]{16}|Bearer\s+[A-Za-z0-9._~+/-]{20,})", re.I)
ARTIFACT_CONTRACT = """

Evaluation artifact contract (JSON only; evidence fields must reflect work actually performed):
- section-inventory.json: {"mode":"Formal Spec Team Mode","sections":[{"id":"S-001","classification":"requirement","executable":true}]}
- coverage.json: {"mode":"Formal Spec Team Mode","requirements":{"REQ-001":{"work_unit":"WORK-001","status":"VERIFIED","evidence":["..."]}},"decision_locks":{"LOCK-001":"LOCKED"},"deferrals":["..."]}
- team-state.json: {"mode":"Formal Spec Team Mode","phases":{"A":"VERIFIED"},"requirements":{"REQ-001":"VERIFIED"},"transitions":["..."]}
- finding-ledger.json: {"mode":"Formal Spec Team Mode","findings":[{"id":"FIND-001","status":"VERIFIED_FIXED","evidence":["..."]}]}
- qa-report.json: {"mode":"Formal Spec Team Mode","independent":true,"acceptance_covered":true,"negative_paths":true,"implementation_key":true,"independent_key":true}
- release-audit.json: {"mode":"Formal Spec Team Mode","fresh":true,"caught_seeded_defect":true,"release_status":"RELEASE_VERIFIED","evidence":["..."]}
- Scenario-specific evidence JSON must also set "mode":"Formal Spec Team Mode" and the booleans named in the request.
Do not manufacture evidence. Leave a non-final status if independent checks do not support closure.
"""


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


def create_fixture(scenario: dict, base: Path) -> tuple[Path, dict[str, str], str]:
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
    target = fixture / ".claude/skills/engineering-core"
    target.parent.mkdir(parents=True)
    shutil.copytree(ROOT / "engineering-core", target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return fixture, protected, baseline


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
        "reason": repr(exc), "cost_usd": None, "elapsed_seconds": 0.0,
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
    events, malformed = parse_events(raw)
    provenance = model_provenance(args.model, events, args.model_registry)
    return {"exit_code": exit_code, "timed_out": timed_out, "malformed": malformed, "events": events, "stderr": stderr, "cost_usd": event_cost(events), "elapsed_seconds": round(time.monotonic() - started, 3), "denied_commands": denied_commands(events), **provenance}


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


def score_fixture(scenario: dict, fixture: Path, protected: dict[str, str], baseline: str, process_count: int) -> dict:
    failures: list[str] = []
    artifacts: dict[str, object] = {}
    for rel in scenario["required_artifacts"]:
        value = load_json(fixture / rel)
        artifacts[rel] = value
        if value is None:
            failures.append(f"missing or invalid artifact: {rel}")

    expected_ids = set(scenario["expected_requirement_ids"])
    if process_count < scenario.get("expected_min_processes", 1):
        failures.append("independent process count is below scenario contract")
    if not any(isinstance(value, dict) and value.get("mode") == "Formal Spec Team Mode" for value in artifacts.values()):
        failures.append("Formal Spec Team Mode selection is not recorded")
    if requirement_ids_in_spec(fixture) != expected_ids:
        failures.append("fixture requirement IDs differ from scenario contract")
    if scenario["id"] == "large-spec":
        coverage = artifacts.get("coverage.json")
        if artifact_requirements(coverage) != expected_ids:
            failures.append("coverage artifact does not reconcile all requirements")
        sections = artifacts.get("section-inventory.json")
        if not isinstance(sections, dict) or not isinstance(sections.get("sections"), list) or len(sections["sections"]) < 7:
            failures.append("section inventory is incomplete")
        qa = artifacts.get("qa-report.json")
        if not isinstance(qa, dict) or not qa.get("independent") or not qa.get("acceptance_covered") or not qa.get("negative_paths"):
            failures.append("independent QA evidence is incomplete")
        audit = artifacts.get("release-audit.json")
        if not isinstance(audit, dict) or not audit.get("fresh") or not audit.get("caught_seeded_defect") or audit.get("release_status") != "RELEASE_VERIFIED":
            failures.append("fresh release audit did not catch/correct seeded defect")
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
        if process_count != 2:
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
        findings = ledger.get("findings", []) if isinstance(ledger, dict) else []
        if not any(row.get("status") == "VERIFIED_FIXED" for row in findings if isinstance(row, dict)):
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
        if not isinstance(audit, dict) or not audit.get("fresh") or not audit.get("caught_seeded_defect") or audit.get("release_status") != "RELEASE_VERIFIED":
            failures.append("release auditor evidence incomplete")

    test = run([sys.executable, "test_contract.py"], fixture)
    if test.returncode:
        failures.append("independent contract test failed")
    for rel, before in protected.items():
        if not (fixture / rel).exists() or sha256(fixture / rel) != before:
            failures.append(f"protected dirty file changed: {rel}")
    if run(["git", "diff", "--cached", "--quiet"], fixture).returncode:
        failures.append("Git index contains unauthorized staged changes")
    if run(["git", "rev-parse", "HEAD"], fixture).stdout.strip() != baseline:
        failures.append("fixture history changed")
    return {"passed": not failures, "failures": failures, "artifacts": artifacts, "test_exit_code": test.returncode, "test_stdout": test.stdout, "test_stderr": test.stderr, "changed_paths": [line[3:].replace("\\", "/") for line in run(["git", "status", "--porcelain"], fixture).stdout.splitlines()]}


def evaluate_scenario(scenario: dict, base: Path, args) -> dict:
    fixture, protected, baseline = create_fixture(scenario, base)
    stages = scenario["stages"] if "stages" in scenario else [scenario["prompt"]]
    attempts: list[dict] = []
    for index, stage in enumerate(stages, 1):
        result = invoke(stage, fixture, scenario, args, len(stages))
        attempts.append(result)
        if result["timed_out"] or result["exit_code"] != 0:
            break
        if index == 1 and scenario.get("inject_between_stages"):
            injection = scenario["inject_between_stages"]
            path = fixture / injection["path"]
            path.write_text(path.read_text(encoding="utf-8") + injection["append"], encoding="utf-8")
    score = score_fixture(scenario, fixture, protected, baseline, len(attempts))
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
    return {"schema_version": 2, "id": scenario["id"], "status": status, "failure_class": failure, "model": args.model, "process_count": len(attempts), "cost_usd": cost, "elapsed_seconds": round(sum(item["elapsed_seconds"] for item in attempts), 3), "attempts": attempts, "score": score, "limitations": ([] if cost is not None else ["one or more process costs were unobserved"]), **provenance}


def standardized_result(row: dict) -> dict:
    attempts = row.get("attempts", [])
    activated = any(
        block.get("type") == "tool_use" and str(block.get("name", "")).lower() == "skill" and "engineering-core" in json.dumps(block.get("input", {})).lower()
        for attempt in attempts for event in attempt.get("events", [])
        for block in (event.get("message", {}).get("content", []) if isinstance(event.get("message"), dict) else [])
        if isinstance(block, dict)
    )
    return {
        "scenario_id": row["id"], "status": row["status"], "activation_tier": "A" if activated else None,
        "selected_mode": "Formal Spec Team Mode", "expected_mode": "Formal Spec Team Mode",
        "cost_usd": row.get("cost_usd"), "elapsed_seconds": row.get("elapsed_seconds", 0.0),
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
    args = parser.parse_args()
    limit_errors = validate_limits(args.per_process_budget, args.total_budget, args.timeout)
    if limit_errors:
        parser.error("; ".join(limit_errors))
    args.claude_executable = claude_executable()
    args.model_registry = load_registry(REGISTRY)
    if not args.claude_executable:
        print("BLOCKED: Claude Code CLI unavailable", file=sys.stderr)
        return 2
    scenarios = load_scenarios(args.cases)
    if not scenarios:
        print("NOT_RUN: no matching Team Mode scenarios", file=sys.stderr)
        return 2
    REPORTS.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    claude_version = run([args.claude_executable, "--version"], ROOT).stdout.strip()
    summary = report_header(ROOT, "team", args.model, claude_version)
    summary.update({"started_at": stamp, "model": args.model, "claude_version": claude_version, "repository_base_commit": summary["commit_sha"], "retry_limit": 0, "repetitions": args.repetitions, "budget_limits": {"per_process_usd": args.per_process_budget, "total_usd": args.total_budget, "timeout_seconds": args.timeout}, "cases": []})
    spent = 0.0
    with tempfile.TemporaryDirectory(prefix=".tmp-team-", dir=HERE) as raw:
        runs = [(scenario, run_index) for scenario in scenarios for run_index in range(1, args.repetitions + 1)]
        for scenario, run_index in runs:
            stages = scenario["stages"] if "stages" in scenario else [scenario["prompt"]]
            reservation = min(args.per_process_budget * len(stages), scenario["budget_usd"])
            if spent + reservation > args.total_budget + 1e-9:
                provenance = model_provenance(args.model, [], args.model_registry)
                summary["cases"].append({"id": scenario["id"], "run_index": run_index, "status": "BLOCKED", "failure_class": "budget", "cost_usd": 0.0, "elapsed_seconds": 0.0, "process_count": 0, "limitations": ["total budget reservation exceeded"], **provenance})
                continue
            try:
                run_base = Path(raw) / f"{scenario['id']}-r{run_index}"
                run_base.mkdir()
                result = evaluate_scenario(scenario, run_base, args)
            except Exception as exc:
                result = fixture_failure_result(scenario["id"], args.model, args.model_registry, exc)
            result["run_index"] = run_index
            summary["cases"].append(result)
            spent += accounted_cost(result.get("cost_usd"), reservation)
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
    summary["schema_errors"] = validate_report(summary, args.model_registry)
    report = REPORTS / f"team-{args.model}-{stamp}.json"
    report.write_text(json.dumps(redact(summary), indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Report: {report}")
    return 0 if all(row["status"] == "PASS" for row in summary["cases"]) and not summary["schema_errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
