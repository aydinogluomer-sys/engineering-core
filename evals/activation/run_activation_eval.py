from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
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
REPORTS = HERE / "reports"
sys.path.insert(0, str(ROOT / "evals"))
from completion_summary import as_dict, parse_completion_summary  # noqa: E402

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


def load_dataset(profile: str) -> list[dict]:
    cases: list[dict] = []
    for label in ("positive", "negative", "ambiguous"):
        rows = json.loads((HERE / f"{label}.json").read_text(encoding="utf-8"))
        for row in rows:
            if profile in row["profiles"]:
                cases.append({**row, "expected": label})
    return cases


def metrics(results: list[dict]) -> dict:
    binary = [row for row in results if row["expected"] in {"positive", "negative"} and row["status"] == "SCORED"]
    tp = sum(row["expected"] == "positive" and row["activated"] for row in binary)
    fn = sum(row["expected"] == "positive" and not row["activated"] for row in binary)
    fp = sum(row["expected"] == "negative" and row["activated"] for row in binary)
    tn = sum(row["expected"] == "negative" and not row["activated"] for row in binary)
    ratio = lambda numerator, denominator: round(numerator / denominator, 4) if denominator else None
    return {
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "precision": ratio(tp, tp + fp), "recall": ratio(tp, tp + fn),
        "false_positive_rate": ratio(fp, fp + tn), "false_negative_rate": ratio(fn, fn + tp),
        "ambiguous_scored_separately": sum(row["expected"] == "ambiguous" and row["status"] == "SCORED" for row in results),
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
    fixture = base / case["id"]
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
    terminal = next((event for event in reversed(events) if event.get("type") == "result"), {})
    cost = terminal.get("total_cost_usd") if isinstance(terminal.get("total_cost_usd"), (int, float)) else None
    if timed_out:
        status, failure = "BLOCKED", "timeout"
    elif exit_code != 0:
        status, failure = "BLOCKED", "CLI/model"
    elif malformed:
        status, failure = "BLOCKED", "malformed-stream"
    else:
        status, failure = "SCORED", None
    return {
        "id": case["id"], "category": case["category"], "expected": case["expected"],
        "mode": args.mode, "description": args.description, "status": status, "failure_class": failure,
        "activated": activated, "evidence_tier": tier, "completion_summary": completion,
        "completion_errors": completion_errors, "exit_code": exit_code, "timed_out": timed_out,
        "cost_usd": cost, "elapsed_seconds": round(time.monotonic() - started, 3),
        "stderr": SECRET_RE.sub("[REDACTED]", stderr),
        "events": json.loads(SECRET_RE.sub("[REDACTED]", json.dumps(events))),
        "availability_is_not_activation": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Measure explicit or natural engineering-core activation")
    parser.add_argument("--mode", choices=["explicit", "natural"], required=True)
    parser.add_argument("--profile", choices=["smoke", "full"], default="smoke")
    parser.add_argument("--description", choices=["baseline", "candidate1", "candidate2", "current"], default="current")
    parser.add_argument("--model", default="haiku")
    parser.add_argument("--effort", choices=["low", "medium", "high", "xhigh", "max"], default="low")
    parser.add_argument("--per-case-budget", type=float, default=0.20)
    parser.add_argument("--total-budget", type=float, default=2.80)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--workers", type=int, choices=range(1, 5), default=1)
    args = parser.parse_args()
    args.claude_executable = claude_executable()
    if not args.claude_executable:
        print("BLOCKED: Claude Code CLI is unavailable", file=sys.stderr)
        return 2
    cases = load_dataset(args.profile)
    if args.limit is not None:
        cases = cases[:args.limit]
    REPORTS.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    summary = {"schema_version": 1, "started_at": stamp, "mode": args.mode, "profile": args.profile, "description": args.description, "cases": []}
    capacity = int((args.total_budget + 1e-9) // args.per_case_budget)
    runnable, deferred = cases[:capacity], cases[capacity:]
    with tempfile.TemporaryDirectory(prefix=".tmp-activation-", dir=HERE) as raw:
        base = Path(raw)
        fixtures: dict[str, Path] = {}
        for case in runnable:
            try:
                fixtures[case["id"]] = make_fixture(case, base, args.description)
            except Exception as exc:
                summary["cases"].append({**case, "mode": args.mode, "description": args.description, "status": "BLOCKED", "failure_class": "fixture", "activated": False, "reason": repr(exc)})
        ready = [case for case in runnable if case["id"] in fixtures]
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {pool.submit(evaluate, case, fixtures[case["id"]], args): case for case in ready}
            for future in as_completed(futures):
                case = futures[future]
                try:
                    result = future.result()
                except Exception as exc:
                    result = {**case, "mode": args.mode, "description": args.description, "status": "BLOCKED", "failure_class": "harness", "activated": False, "reason": repr(exc)}
                summary["cases"].append(result)
                print(f"{case['id']}: {result['status']} activation={result.get('activated')} tier={result.get('evidence_tier')}", flush=True)
    summary["cases"].extend({**case, "status": "NOT_RUN", "failure_class": "budget", "activated": False} for case in deferred)
    order = {case["id"]: index for index, case in enumerate(cases)}
    summary["cases"].sort(key=lambda row: order[row["id"]])
    summary["metrics"] = metrics(summary["cases"])
    summary["recorded_cost_usd"] = round(sum(row.get("cost_usd") or 0 for row in summary["cases"]), 6)
    summary["accounted_budget_usd"] = round(sum(row.get("cost_usd") if isinstance(row.get("cost_usd"), (int, float)) else args.per_case_budget for row in summary["cases"] if row["status"] != "NOT_RUN"), 6)
    report = REPORTS / f"activation-{args.mode}-{args.description}-{stamp}.json"
    report.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary["metrics"], sort_keys=True))
    print(f"Report: {report}")
    return 0 if all(row["status"] == "SCORED" for row in summary["cases"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
