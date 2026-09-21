from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
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
REPORTS = HERE / "reports"
sys.path.insert(0, str(ROOT / "evals"))
from completion_summary import as_dict, parse_completion_summary  # noqa: E402
from cross_model import aggregate_provenance, load_registry, model_provenance, report_header, validate_limits, validate_report  # noqa: E402

REGISTRY = ROOT / "evals/cross-model/model_registry.json"

DESCRIPTIONS = {
    "baseline": "Core operating policy for software-engineering work across repositories. Use when implementing, debugging, refactoring, removing, reviewing, testing, migrating, or preparing code for release; scale investigation, planning, safety, and verification to the task's actual risk.",
    "candidate1": "Risk-adaptive workflow for repository implementation, debugging, refactoring, removal, migration, testing, review, and release preparation. Use for substantive codebase work that requires evidence, scoped changes, verification, or safety escalation; exclude generic explanations and unrelated writing.",
    "candidate2": "Risk-adaptive operating policy for substantive repository engineering. Use when Claude must inspect or change a codebase to implement, debug, refactor, remove, migrate, test, review and fix, or prepare a release and verify the outcome. Do not use merely for generic technical explanations, summaries, brainstorming, or unrelated writing.",
}
SECRET_RE = re.compile(r"(sk-ant-[A-Za-z0-9_-]+|ghp_[A-Za-z0-9]+|github_pat_[A-Za-z0-9_]+|AKIA[0-9A-Z]{16})")


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


def load_dataset(profile: str, dataset: str = "tuning") -> list[dict]:
    if dataset == "targeted":
        data = json.loads((ROOT / "evals/cross-model/formal-long-horizon.json").read_text(encoding="utf-8"))
        return [{**row, "expected": "positive"} for row in data["cases"]]
    cases: list[dict] = []
    prefix = "holdout-" if dataset == "holdout" else ""
    for label in ("positive", "negative", "ambiguous"):
        rows = json.loads((HERE / f"{prefix}{label}.json").read_text(encoding="utf-8"))
        for row in rows:
            if dataset == "holdout" or profile in row["profiles"]:
                cases.append({**row, "expected": label})
    return cases


def metrics(results: list[dict]) -> dict:
    binary = [row for row in results if row["expected"] in {"positive", "negative"} and row["status"] == "SCORED"]
    confirmed = lambda row: row.get("evidence_tier") == "A"
    named = lambda row: row.get("evidence_tier") in {"A", "B"}
    policy_like = lambda row: row.get("evidence_tier") in {"A", "B", "C"}
    tp = sum(row["expected"] == "positive" and confirmed(row) for row in binary)
    fn = sum(row["expected"] == "positive" and not confirmed(row) for row in binary)
    fp = sum(row["expected"] == "negative" and confirmed(row) for row in binary)
    tn = sum(row["expected"] == "negative" and not confirmed(row) for row in binary)
    ratio = lambda numerator, denominator: round(numerator / denominator, 4) if denominator else None
    category: dict[str, dict[str, int | float | None]] = {}
    for row in binary:
        if row["expected"] != "positive":
            continue
        item = category.setdefault(row.get("category", "uncategorized"), {"confirmed": 0, "total": 0, "recall": None})
        item["total"] += 1
        item["confirmed"] += int(confirmed(row))
    for item in category.values():
        item["recall"] = ratio(item["confirmed"], item["total"])
    return {
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "confirmed_precision": ratio(tp, tp + fp), "confirmed_recall": ratio(tp, tp + fn),
        "false_positive_rate": ratio(fp, fp + tn), "false_negative_rate": ratio(fn, fn + tp),
        "tier_a_count": sum(confirmed(row) for row in binary),
        "tier_b_count": sum(row.get("evidence_tier") == "B" for row in binary),
        "tier_c_count": sum(row.get("evidence_tier") == "C" for row in binary),
        "named_policy_recall": ratio(sum(row["expected"] == "positive" and named(row) for row in binary), sum(row["expected"] == "positive" for row in binary)),
        "policy_like_rate": ratio(sum(policy_like(row) for row in binary), len(binary)),
        "category_recall": category,
        "ambiguous_scored_separately": sum(row["expected"] == "ambiguous" and row["status"] == "SCORED" for row in results),
        "expected_counts": {
            label: sum(row.get("expected") == label for row in results)
            for label in ("positive", "negative", "ambiguous")
        },
        "outcome_counts": {
            label: sum(row.get("status") == label for row in results)
            for label in ("SCORED", "BLOCKED", "NOT_RUN")
        },
        "timeout_count": sum(row.get("failure_class") == "timeout" for row in results),
    }


def final_text(events: list[dict]) -> str:
    for event in reversed(events):
        if event.get("type") == "result" and isinstance(event.get("result"), str):
            return event["result"]
    return ""


def activation_evidence(events: list[dict]) -> tuple[bool, str | None, dict | None, list[str]]:
    for event in events:
        message = event.get("message")
        if not isinstance(message, dict):
            continue
        for block in message.get("content", []):
            if not isinstance(block, dict) or block.get("type") != "tool_use":
                continue
            name = str(block.get("name", "")).lower()
            payload = json.dumps(block.get("input", {}), sort_keys=True).lower()
            if name == "skill" and "engineering-core" in payload:
                return True, "A", None, []
    completion, errors = parse_completion_summary(final_text(events))
    if completion and completion.policy == "engineering-core":
        return True, "B", as_dict(completion), []
    text = final_text(events).lower()
    if "### execution summary" in text and re.search(r"\*{0,2}policy(?::)?\*{0,2}\s*:\s*engineering-core", text):
        return True, "B", None, errors
    markers = ["risk:", "limitations:", "final diff", "negative path", "required verification", "scope"]
    if sum(marker in text for marker in markers) >= 4:
        return True, "C", None, errors
    return False, None, None, errors


def set_description(skill_file: Path, variant: str) -> None:
    if variant == "current":
        return
    text = skill_file.read_text(encoding="utf-8")
    text = re.sub(r"(?m)^description: .*$", "description: " + DESCRIPTIONS[variant], text, count=1)
    skill_file.write_text(text, encoding="utf-8")


def make_fixture(case: dict, base: Path, description: str) -> Path:
    fixture = base / f"{case['id']}-r{case.get('run_index', 1)}"
    fixture.mkdir()
    (fixture / "README.md").write_text("# Activation fixture\n\nA tiny repository for isolated routing evaluation.\n", encoding="utf-8")
    (fixture / "app.py").write_text("def normalize(value):\n    return value.strip() if value is not None else None\n\ndef normalize_count(items):\n    return len(items) - 1\n", encoding="utf-8")
    (fixture / "test_contract.py").write_text("from app import normalize\nassert normalize(' A ') == 'A'\n", encoding="utf-8")
    (fixture / ".gitignore").write_text(".claude/\n__pycache__/\n", encoding="utf-8")
    for command in (["git", "init", "-q"], ["git", "config", "user.email", "eval@example.invalid"], ["git", "config", "user.name", "Activation Eval"], ["git", "add", "."], ["git", "commit", "-qm", "fixture"]):
        result = run(list(command), fixture)
        if result.returncode:
            raise RuntimeError(result.stderr or result.stdout)
    target = fixture / ".claude/skills/engineering-core"
    target.parent.mkdir(parents=True)
    shutil.copytree(ROOT / "engineering-core", target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    set_description(target / "SKILL.md", description)
    return fixture


def evaluate(case: dict, fixture: Path, args) -> dict:
    prompt = case["prompt"]
    if args.mode == "explicit":
        prompt = "/engineering-core\n\n" + prompt
    command = [
        args.claude_executable, "--print", prompt, "--output-format", "stream-json", "--verbose",
        "--model", args.model, "--effort", args.effort, "--max-budget-usd", str(args.per_case_budget),
        "--permission-mode", "acceptEdits", "--permission-prompts", "none", "--no-session-persistence", "--no-chrome",
        "--setting-sources", "project", "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
        "--tools", "Skill,Read,Edit,Write,Bash,Glob,Grep", "--allowedTools", "Skill(engineering-core),Read,Edit,Write,Glob,Grep,Bash(python test_contract.py),Bash(git diff:*),Bash(git status:*)",
    ]
    started = time.monotonic()
    try:
        process = run(command, fixture, args.timeout)
        raw, stderr, exit_code, timed_out = process.stdout, process.stderr, process.returncode, False
    except subprocess.TimeoutExpired as exc:
        raw = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        exit_code, timed_out = None, True
    events, malformed = [], 0
    for line in raw.splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            malformed += 1
    activated, tier, completion, completion_errors = activation_evidence(events)
    provenance = model_provenance(args.model, events, args.model_registry)
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
    else:
        status, failure = "SCORED", None
    return {
        "id": case["id"], "category": case["category"], "expected": case["expected"],
        "run_index": case.get("run_index", 1),
        "mode": args.mode, "description": args.description, "status": status, "failure_class": failure,
        "activated": activated, "evidence_tier": tier, "completion_summary": completion,
        "completion_errors": completion_errors, "exit_code": exit_code, "timed_out": timed_out,
        "cost_usd": cost, "elapsed_seconds": round(time.monotonic() - started, 3),
        "stderr": SECRET_RE.sub("[REDACTED]", stderr),
        "events": json.loads(SECRET_RE.sub("[REDACTED]", json.dumps(events))),
        "availability_is_not_activation": True,
        **provenance,
    }


def standardized_result(row: dict) -> dict:
    tier_a = row.get("evidence_tier") == "A"
    if row.get("status") != "SCORED":
        status = row.get("status") if row.get("status") in {"BLOCKED", "NOT_RUN"} else "BLOCKED"
        failure = row.get("failure_class") if row.get("failure_class") in {"timeout", "budget", "permission", "model_capability", "CLI", "fixture", "environment", "scorer"} else "unknown"
    elif row.get("expected") == "positive":
        status, failure = (("PASS", None) if tier_a else ("FAIL", "activation"))
    elif row.get("expected") == "negative":
        status, failure = (("FAIL", "activation") if tier_a else ("PASS", None))
    else:
        status, failure = "PASS", None
    return {
        "scenario_id": row["id"], "status": status, "activation_tier": row.get("evidence_tier"),
        "selected_mode": None, "expected_mode": None, "cost_usd": row.get("cost_usd"),
        "elapsed_seconds": row.get("elapsed_seconds", 0.0), "failure_class": failure,
        "evidence": {"expected_activation": row.get("expected"), "activated": row.get("activated"), "category": row.get("category")},
        "limitations": (["ambiguous prompt excluded from confusion matrix"] if row.get("expected") == "ambiguous" else []),
        "requested_model": row.get("requested_model"), "effective_model": row.get("effective_model", "UNOBSERVED"),
        "effective_model_observed": row.get("effective_model_observed", False),
        "fallback_detected": row.get("fallback_detected", "unknown"), "fallback_reason": row.get("fallback_reason"),
    }


def repetition_metrics(rows: list[dict]) -> dict:
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        grouped.setdefault(row["id"], []).append(row)
    result = {}
    for case_id, attempts in grouped.items():
        scored = [row for row in attempts if row.get("status") == "SCORED"]
        tier_a = sum(row.get("evidence_tier") == "A" for row in scored)
        result[case_id] = {
            "runs": len(attempts), "scored_runs": len(scored), "tier_a_runs": tier_a,
            "activation_rate": round(tier_a / len(attempts), 4) if attempts else None,
            "statuses": {status: sum(row.get("status") == status for row in attempts) for status in {row.get("status") for row in attempts}},
        }
    return result


def gate_result(model: str, measured: dict) -> dict:
    if model == "haiku":
        return {"role": "degradation", "status": "MEASURED", "primary_gate_required": False}
    precision, recall = measured.get("confirmed_precision"), measured.get("confirmed_recall")
    category = measured.get("category_recall", {})
    critical = {name: category.get(name, {}).get("recall") for name in ("security", "rls-permissions", "billing-idempotency", "formal-spec", "long-horizon")}
    missing = [name for name, value in critical.items() if value is None]
    failed = [name for name, value in critical.items() if value is not None and value < 0.75]
    passed = precision is not None and precision >= 0.95 and recall is not None and recall >= 0.80 and not missing and not failed
    return {"role": "primary", "status": "PASS" if passed else "NOT_VERIFIED", "precision_gate": precision is not None and precision >= 0.95, "recall_gate": recall is not None and recall >= 0.80, "critical_category_failures": failed, "critical_categories_not_measured": missing}


def main() -> int:
    parser = argparse.ArgumentParser(description="Measure explicit or natural engineering-core activation")
    parser.add_argument("--mode", choices=["explicit", "natural"], required=True)
    parser.add_argument("--profile", choices=["smoke", "full"], default="smoke")
    parser.add_argument("--dataset", choices=["tuning", "holdout", "targeted"], default="tuning")
    parser.add_argument("--description", choices=["baseline", "candidate1", "candidate2", "current"], default="current")
    parser.add_argument("--model", default="haiku")
    parser.add_argument("--effort", choices=["low", "medium", "high", "xhigh", "max"], default="low")
    parser.add_argument("--per-case-budget", type=float, default=0.20)
    parser.add_argument("--total-budget", type=float, default=2.80)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--case", action="append", dest="cases", help="Run only the named case ID; repeatable")
    parser.add_argument("--workers", type=int, choices=range(1, 5), default=1)
    parser.add_argument("--repetitions", type=int, choices=range(1, 6), default=1)
    parser.add_argument("--retries", type=int, choices=[0], default=0, help="Automatic retries are disabled")
    args = parser.parse_args()
    limit_errors = validate_limits(args.per_case_budget, args.total_budget, args.timeout)
    if limit_errors:
        parser.error("; ".join(limit_errors))
    args.claude_executable = claude_executable()
    args.model_registry = load_registry(REGISTRY)
    if not args.claude_executable:
        print("BLOCKED: Claude Code CLI is unavailable", file=sys.stderr)
        return 2
    if args.dataset == "holdout" and args.description != "current":
        parser.error("sealed holdout may run only against the frozen current description")
    metadata = json.loads((HERE / "dataset-metadata.json").read_text(encoding="utf-8"))
    dataset_version = metadata["dataset_version"]
    if args.dataset == "targeted":
        dataset_version = json.loads((ROOT / "evals/cross-model/formal-long-horizon.json").read_text(encoding="utf-8"))["dataset_version"]
    current_description = next(line[13:] for line in (ROOT / "engineering-core/SKILL.md").read_text(encoding="utf-8").splitlines() if line.startswith("description: "))
    description_hash = hashlib.sha256(current_description.encode()).hexdigest()
    if args.dataset == "holdout" and description_hash != metadata["frozen_description_sha256"]:
        print("BLOCKED: current description differs from sealed holdout freeze", file=sys.stderr)
        return 2
    source_cases = load_dataset(args.profile, args.dataset)
    if args.cases:
        requested = set(args.cases)
        source_cases = [case for case in source_cases if case["id"] in requested]
        missing = requested - {case["id"] for case in source_cases}
        if missing:
            parser.error("unknown case ID(s): " + ", ".join(sorted(missing)))
    cases = [{**case, "run_index": index} for case in source_cases for index in range(1, args.repetitions + 1)]
    if args.limit is not None:
        cases = cases[:args.limit]
    REPORTS.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    claude_version = run([args.claude_executable, "--version"], ROOT).stdout.strip()
    summary = report_header(ROOT, "activation", args.model, claude_version, dataset_version)
    summary.update({"dataset": args.dataset, "started_at": stamp, "mode": args.mode, "profile": args.profile, "description": args.description, "description_sha256": description_hash, "frozen_at_commit": metadata["frozen_at_commit"], "repository_base_commit": summary["commit_sha"], "model": args.model, "claude_version": claude_version, "repetitions": args.repetitions, "retry_limit": 0, "budget_limits": {"per_case_usd": args.per_case_budget, "total_usd": args.total_budget, "timeout_seconds": args.timeout}, "cases": []})
    capacity = int((args.total_budget + 1e-9) // args.per_case_budget)
    runnable, deferred = cases[:capacity], cases[capacity:]
    with tempfile.TemporaryDirectory(prefix=".tmp-activation-", dir=HERE) as raw:
        base = Path(raw)
        fixtures: dict[str, Path] = {}
        for case in runnable:
            try:
                fixtures[f"{case['id']}:{case['run_index']}"] = make_fixture(case, base, args.description)
            except Exception as exc:
                summary["cases"].append({**case, "mode": args.mode, "description": args.description, "status": "BLOCKED", "failure_class": "fixture", "activated": False, "reason": repr(exc), "cost_usd": 0.0, "elapsed_seconds": 0.0, **model_provenance(args.model, [], args.model_registry)})
        ready = [case for case in runnable if f"{case['id']}:{case['run_index']}" in fixtures]
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {pool.submit(evaluate, case, fixtures[f"{case['id']}:{case['run_index']}"], args): case for case in ready}
            for future in as_completed(futures):
                case = futures[future]
                try:
                    result = future.result()
                except Exception as exc:
                    result = {**case, "mode": args.mode, "description": args.description, "status": "BLOCKED", "failure_class": "environment", "activated": False, "reason": repr(exc), "cost_usd": 0.0, "elapsed_seconds": 0.0, **model_provenance(args.model, [], args.model_registry)}
                summary["cases"].append(result)
                print(f"{case['id']}[r{case['run_index']}]: {result['status']} tier={result.get('evidence_tier')}", flush=True)
    summary["cases"].extend({**case, "status": "BLOCKED", "failure_class": "budget", "activated": False, "cost_usd": 0.0, "elapsed_seconds": 0.0, **model_provenance(args.model, [], args.model_registry)} for case in deferred)
    order = {(case["id"], case["run_index"]): index for index, case in enumerate(cases)}
    summary["cases"].sort(key=lambda row: order[(row["id"], row.get("run_index", 1))])
    summary["metrics"] = metrics(summary["cases"])
    summary["repetition_metrics"] = repetition_metrics(summary["cases"])
    summary["role_aware_gate"] = gate_result(args.model, summary["metrics"])
    summary["results"] = [standardized_result(row) for row in summary["cases"]]
    summary.update(aggregate_provenance(args.model, summary["results"]))
    summary["recorded_cost_usd"] = round(sum(row.get("cost_usd") or 0 for row in summary["cases"]), 6)
    summary["accounted_budget_usd"] = round(sum(row.get("cost_usd") if isinstance(row.get("cost_usd"), (int, float)) else args.per_case_budget for row in summary["cases"] if row["status"] != "NOT_RUN"), 6)
    summary["schema_errors"] = validate_report(summary, args.model_registry)
    report = REPORTS / f"activation-{args.mode}-{args.description}-{stamp}.json"
    report.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary["metrics"], sort_keys=True))
    print(f"Report: {report}")
    return 0 if all(row["status"] == "SCORED" for row in summary["cases"]) and not summary["schema_errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
