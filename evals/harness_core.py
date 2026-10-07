from __future__ import annotations

import json
import math
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


SECRET_PATTERNS = (
    re.compile(r"sk-ant-[A-Za-z0-9_-]{12,}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"Bearer\s+[A-Za-z0-9._~+/-]{20,}", re.I),
    re.compile(r"(?i)\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?)://[^\s:/]+:[^\s/@]+@[^\s]+"),
    re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----[\s\S]*?-----END (?:RSA |OPENSSH |EC )?PRIVATE KEY-----"),
)


def redact(value):
    """Recursively redact recognized secret values; this is not a complete DLP system."""
    if isinstance(value, dict):
        return {key: redact(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact(item) for item in value]
    if isinstance(value, str):
        for pattern in SECRET_PATTERNS:
            value = pattern.sub("[REDACTED]", value)
    return value


def finite_number(value, *, positive: bool = False, nonnegative: bool = False) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    number = float(value)
    if not math.isfinite(number):
        return False
    if positive and number <= 0:
        return False
    if nonnegative and number < 0:
        return False
    return True


def bounded_int(value, *, minimum: int, maximum: int) -> bool:
    return not isinstance(value, bool) and isinstance(value, int) and minimum <= value <= maximum


def validate_run_limits(per_call_budget, total_budget, timeout, repetitions=1, workers=1) -> list[str]:
    errors: list[str] = []
    if not finite_number(per_call_budget, positive=True):
        errors.append("per-call budget must be a finite positive number")
    if not finite_number(total_budget, positive=True):
        errors.append("total budget must be a finite positive number")
    if not bounded_int(timeout, minimum=1, maximum=86_400):
        errors.append("timeout must be an integer from 1 to 86400")
    if not bounded_int(repetitions, minimum=1, maximum=20):
        errors.append("repetitions must be an integer from 1 to 20")
    if not bounded_int(workers, minimum=1, maximum=8):
        errors.append("workers must be an integer from 1 to 8")
    if not errors and float(per_call_budget) > float(total_budget):
        errors.append("per-call budget cannot exceed total budget")
    return errors


def parse_jsonl_events(raw: str) -> tuple[list[dict], list[str]]:
    events: list[dict] = []
    errors: list[str] = []
    for line_number, line in enumerate(raw.splitlines(), 1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"line {line_number}: malformed JSON: {exc.msg}")
            continue
        if not isinstance(event, dict):
            errors.append(f"line {line_number}: event must be an object")
            continue
        message = event.get("message")
        if message is not None and not isinstance(message, dict):
            errors.append(f"line {line_number}: message must be an object")
        elif isinstance(message, dict) and "content" in message and not isinstance(message["content"], list):
            errors.append(f"line {line_number}: message.content must be a list")
        if event.get("type") == "result":
            for field in ("total_cost_usd", "cost_usd"):
                if field in event and event[field] is not None and not finite_number(event[field], nonnegative=True):
                    errors.append(f"line {line_number}: {field} must be finite and nonnegative")
        events.append(event)
    terminal = [event for event in events if event.get("type") == "result"]
    if len(terminal) > 1:
        signatures = {(event.get("subtype"), event.get("terminal_reason"), event.get("is_error")) for event in terminal}
        if len(signatures) > 1:
            errors.append("conflicting terminal result events")
    return events, errors


@dataclass(frozen=True)
class CostAccounting:
    reserved_usd: float
    observed_usd: float | None
    accounted_usd: float


def account_cost(reserved_usd, observed_usd) -> CostAccounting:
    if not finite_number(reserved_usd, positive=True):
        raise ValueError("reserved cost must be finite and positive")
    observed = float(observed_usd) if finite_number(observed_usd, nonnegative=True) else None
    return CostAccounting(float(reserved_usd), observed, observed if observed is not None else float(reserved_usd))


def gate_exit_code(*, evaluation_completed: bool, quality_gate_passed: bool | None, require_gate: bool) -> int:
    if not evaluation_completed:
        return 2
    if require_gate and quality_gate_passed is not True:
        return 1
    return 0


def preflight_cli(executable: str | None, required_flags: tuple[str, ...]) -> dict:
    resolved = shutil.which(executable) if executable else None
    if not executable or (not Path(executable).exists() and not resolved):
        return {"status": "BLOCKED", "failure_class": "environment", "version": None, "missing_flags": list(required_flags), "reason": "CLI executable unavailable"}
    try:
        command = resolved or executable
        version = subprocess.run([command, "--version"], text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=15, check=False)
        help_result = subprocess.run([command, "--help"], text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=15, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"status": "BLOCKED", "failure_class": "environment", "version": None, "missing_flags": list(required_flags), "reason": repr(exc)}
    help_text = help_result.stdout + "\n" + help_result.stderr
    missing = [flag for flag in required_flags if flag not in help_text]
    ok = version.returncode == 0 and help_result.returncode == 0 and not missing
    return {
        "status": "PASS" if ok else "BLOCKED",
        "failure_class": None if ok else "environment",
        "version": version.stdout.strip() or version.stderr.strip() or None,
        "missing_flags": missing,
        "reason": None if ok else "CLI version/help capability preflight failed",
    }


def write_redacted_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(redact(value), indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")


def tracked_secret_findings(root: Path, *, excluded_prefixes: tuple[str, ...] = ()) -> list[str]:
    result = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=root, capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError("git ls-files failed during secret scan")
    findings: list[str] = []
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        rel = raw.decode("utf-8", errors="surrogateescape").replace("\\", "/")
        if rel.startswith(excluded_prefixes):
            continue
        path = root / rel
        try:
            data = path.read_bytes()
        except OSError:
            continue
        if b"\0" in data:
            continue
        text = data.decode("utf-8", errors="replace")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(rel)
                break
    return sorted(set(findings))
