from __future__ import annotations

import argparse
import json
import os
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
sys.path.insert(0, str(ROOT / "evals"))
from cross_model import aggregate_provenance, load_registry, model_provenance, report_header, validate_limits, validate_report  # noqa: E402

REPORTS = HERE / "reports"
REGISTRY = HERE / "model_registry.json"
DATASET = HERE / "mode-selection.json"
MODES = {"Adaptive Fast-Exit", "Standard Engineering Mode", "Formal Spec Team Mode"}
SECRET_RE = re.compile(r"(sk-ant-[A-Za-z0-9_-]+|ghp_[A-Za-z0-9]+|github_pat_[A-Za-z0-9_]+|AKIA[0-9A-Z]{16}|Bearer\s+[A-Za-z0-9._~+/-]{20,})", re.I)


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


def parse_events(raw: str) -> tuple[list[dict], int]:
    events, malformed = [], 0
    for line in raw.splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            malformed += 1
    return events, malformed


def final_text(events: list[dict]) -> str:
    for event in reversed(events):
        if event.get("type") == "result" and isinstance(event.get("result"), str):
            return event["result"]
    return ""


def parse_decision(text: str) -> dict | None:
    candidates = [text]
    candidates.extend(re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S | re.I))
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        candidates.append(match.group(0))
    for candidate in candidates:
        try:
            value = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    return None


def score_decision(case: dict, decision: dict | None) -> list[str]:
    failures: list[str] = []
    if not decision:
        return ["structured mode decision is missing"]
    if decision.get("selected_mode") not in MODES:
        failures.append("selected_mode is not controlled")
    if decision.get("selected_mode") != case["expected_mode"]:
        failures.append("selected mode differs from expected mode")
    if decision.get("risk") != case["expected_risk"]:
        failures.append("risk differs from expected risk")
    if bool(decision.get("fast_exit_aborted")) != case["abort"]:
        failures.append("Fast-Exit abort decision is incorrect")
    return failures


def make_fixture(base: Path) -> Path:
    fixture = base / "routing"
    fixture.mkdir()
    (fixture / "README.md").write_text("# Routing fixture\n", encoding="utf-8")
    (fixture / ".gitignore").write_text(".claude/\n", encoding="utf-8")
    target = fixture / ".claude/skills/engineering-core"
    target.parent.mkdir(parents=True)
    shutil.copytree(ROOT / "engineering-core", target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for command in (["git", "init", "-q"], ["git", "config", "user.email", "eval@example.invalid"], ["git", "config", "user.name", "Mode Eval"], ["git", "add", "."], ["git", "commit", "-qm", "fixture"]):
        result = run(list(command), fixture)
        if result.returncode:
            raise RuntimeError(result.stderr or result.stdout)
    return fixture


def skill_invoked(events: list[dict]) -> bool:
    return any(
        block.get("type") == "tool_use" and str(block.get("name", "")).lower() == "skill" and "engineering-core" in json.dumps(block.get("input", {})).lower()
        for event in events
        for block in (event.get("message", {}).get("content", []) if isinstance(event.get("message"), dict) else [])
        if isinstance(block, dict)
    )


def redact(value):
    if isinstance(value, dict):
        return {key: redact(item) for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, str):
        return SECRET_RE.sub("[REDACTED]", value)
    return value


def mode_metrics(results: list[dict]) -> dict:
    scored = [row for row in results if row.get("status") in {"PASS", "FAIL"}]
    ratio = lambda numerator, denominator: round(numerator / denominator, 4) if denominator else None
    per_mode = {}
    for mode in sorted(MODES):
        rows = [row for row in scored if row.get("expected_mode") == mode]
        per_mode[mode] = {
            "correct": sum(row.get("selected_mode") == mode for row in rows),
            "total": len(rows),
            "accuracy": ratio(sum(row.get("selected_mode") == mode for row in rows), len(rows)),
        }
    non_fast = [row for row in scored if row.get("expected_mode") != "Adaptive Fast-Exit"]
    non_team = [row for row in scored if row.get("expected_mode") != "Formal Spec Team Mode"]
    team = [row for row in scored if row.get("expected_mode") == "Formal Spec Team Mode"]
    abort_rows = [row for row in scored if row.get("evidence", {}).get("abort_expected")]
    return {
        "scored_runs": len(scored),
        "blocked_runs": sum(row.get("status") == "BLOCKED" for row in results),
        "mode_accuracy": ratio(sum(row.get("selected_mode") == row.get("expected_mode") for row in scored), len(scored)),
        "per_expected_mode": per_mode,
        "fast_exit_false_positive_rate": ratio(sum(row.get("selected_mode") == "Adaptive Fast-Exit" for row in non_fast), len(non_fast)),
        "team_over_trigger_rate": ratio(sum(row.get("selected_mode") == "Formal Spec Team Mode" for row in non_team), len(non_team)),
        "team_under_trigger_rate": ratio(sum(row.get("selected_mode") != "Formal Spec Team Mode" for row in team), len(team)),
        "abort_accuracy": ratio(sum(row.get("evidence", {}).get("abort_observed") is True for row in abort_rows), len(abort_rows)),
    }


def evaluate(case: dict, fixture: Path, args, registry: dict) -> dict:
    contract = (
        "Classify this request using engineering-core. Do not implement it. Return only JSON with keys "
        "selected_mode, risk, fast_exit_aborted, and rationale. selected_mode must be exactly one of "
        "Adaptive Fast-Exit, Standard Engineering Mode, or Formal Spec Team Mode.\n\nRequest: " + case["prompt"]
    )
    command = [
        args.claude_executable, "--print", "/engineering-core\n\n" + contract,
        "--output-format", "stream-json", "--verbose", "--model", args.model,
        "--effort", args.effort, "--max-budget-usd", str(args.per_case_budget),
        "--permission-mode", "plan", "--permission-prompts", "none", "--no-session-persistence",
        "--no-chrome", "--setting-sources", "project", "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
        "--tools", "Skill,Read,Glob,Grep", "--allowedTools", "Skill(engineering-core),Read,Glob,Grep",
    ]
    started = time.monotonic()
    try:
        process = run(command, fixture, args.timeout)
        raw, exit_code, timed_out = process.stdout, process.returncode, False
    except subprocess.TimeoutExpired as exc:
        raw = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        exit_code, timed_out = None, True
    events, malformed = parse_events(raw)
    decision = parse_decision(final_text(events))
    failures = score_decision(case, decision)
    provenance = model_provenance(args.model, events, registry)
    terminal = next((event for event in reversed(events) if event.get("type") == "result"), {})
    cost = terminal.get("total_cost_usd") if isinstance(terminal.get("total_cost_usd"), (int, float)) else None
    terminal_reason = terminal.get("terminal_reason")
    permission_denied = any(event.get("subtype") == "permission_denied" for event in events)
    if timed_out:
        status, failure = "BLOCKED", "timeout"
    elif terminal_reason in {"max_budget_exceeded", "budget_exceeded"}:
        status, failure = "BLOCKED", "budget"
    elif permission_denied:
        status, failure = "BLOCKED", "permission"
    elif terminal_reason == "prompt_too_long":
        status, failure = "BLOCKED", "model_capability"
    elif exit_code != 0:
        status, failure = "BLOCKED", "CLI"
    elif malformed:
        status, failure = "BLOCKED", "scorer"
    elif failures:
        status, failure = "FAIL", "mode_selection"
    else:
        status, failure = "PASS", None
    return {
        "scenario_id": case["id"], "status": status, "activation_tier": "A" if skill_invoked(events) else None,
        "selected_mode": decision.get("selected_mode") if decision else None,
        "expected_mode": case["expected_mode"], "cost_usd": cost,
        "elapsed_seconds": round(time.monotonic() - started, 3), "failure_class": failure,
        "evidence": {"decision": decision, "score_failures": failures, "family": case["family"], "abort_expected": case["abort"], "abort_observed": bool(decision.get("fast_exit_aborted")) if decision else None},
        "limitations": [], "run_index": case.get("run_index", 1), **provenance,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Measure engineering-core mode-selection reliability")
    parser.add_argument("--model", choices=["haiku", "sonnet", "opus", "fable"], required=True)
    parser.add_argument("--case", action="append", dest="cases")
    parser.add_argument("--repetitions", type=int, choices=range(1, 6), default=1)
    parser.add_argument("--effort", choices=["low", "medium", "high", "xhigh", "max"], default="low")
    parser.add_argument("--per-case-budget", type=float, default=0.15)
    parser.add_argument("--total-budget", type=float, default=1.50)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--retries", type=int, choices=[0], default=0)
    args = parser.parse_args()
    limit_errors = validate_limits(args.per_case_budget, args.total_budget, args.timeout)
    if limit_errors:
        parser.error("; ".join(limit_errors))
    args.claude_executable = claude_executable()
    if not args.claude_executable:
        print("BLOCKED: Claude Code CLI unavailable", file=sys.stderr)
        return 2
    registry = load_registry(REGISTRY)
    cases = json.loads(DATASET.read_text(encoding="utf-8"))
    if args.cases:
        requested = set(args.cases)
        cases = [case for case in cases if case["id"] in requested]
        if requested - {case["id"] for case in cases}:
            parser.error("unknown mode-selection case")
    cases = [{**case, "run_index": run_index} for case in cases for run_index in range(1, args.repetitions + 1)]
    version = run([args.claude_executable, "--version"], ROOT).stdout.strip()
    report = report_header(ROOT, "mode_selection", args.model, version, "mode-selection-v1")
    report.update({"started_at": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"), "retry_limit": 0, "repetitions": args.repetitions, "budget_limits": {"per_case_usd": args.per_case_budget, "total_usd": args.total_budget, "timeout_seconds": args.timeout}, "results": []})
    capacity = int((args.total_budget + 1e-9) // args.per_case_budget)
    with tempfile.TemporaryDirectory(prefix=".tmp-mode-", dir=HERE) as raw:
        fixture = make_fixture(Path(raw))
        for index, case in enumerate(cases):
            if index >= capacity:
                provenance = model_provenance(args.model, [], registry)
                report["results"].append({
                    "scenario_id": case["id"], "status": "BLOCKED", "activation_tier": None,
                    "selected_mode": None, "expected_mode": case["expected_mode"], "cost_usd": 0.0,
                    "elapsed_seconds": 0.0, "failure_class": "budget", "evidence": {},
                    "limitations": ["total budget reservation exceeded"], "run_index": case["run_index"], **provenance,
                })
                continue
            report["results"].append(evaluate(case, fixture, args, registry))
    report.update(aggregate_provenance(args.model, report["results"]))
    report["metrics"] = mode_metrics(report["results"])
    report["recorded_cost_usd"] = round(sum(row["cost_usd"] for row in report["results"] if isinstance(row.get("cost_usd"), (int, float))), 6)
    report["schema_errors"] = validate_report(report, registry)
    REPORTS.mkdir(exist_ok=True)
    path = REPORTS / f"mode-{args.model}-{report['started_at']}.json"
    path.write_text(json.dumps(redact(report), indent=2), encoding="utf-8")
    for row in report["results"]:
        print(f"{row['scenario_id']}[r{row['run_index']}]: {row['status']}")
    print(f"Report: {path}")
    return 0 if all(row["status"] == "PASS" for row in report["results"]) and not report["schema_errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
