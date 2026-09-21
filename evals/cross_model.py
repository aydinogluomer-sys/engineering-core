from __future__ import annotations

import json
import platform
import subprocess
from pathlib import Path

UNOBSERVED = "UNOBSERVED"
STATUSES = {"PASS", "FAIL", "BLOCKED", "NOT_RUN"}
FAILURE_CLASSES = {
    "activation", "mode_selection", "policy", "spec_compilation",
    "requirement_omission", "qa", "specialist_routing",
    "premature_closure", "stale_state", "release_audit",
    "effective_model_unknown", "fallback", "model_capability", "timeout",
    "budget", "permission", "CLI", "fixture", "scorer", "environment",
    "unknown",
}


def load_registry(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not data:
        raise ValueError("model registry must be a non-empty object")
    for alias, row in data.items():
        if not isinstance(row, dict) or not {"role", "team_gate_required", "expected_model_tokens"} <= set(row):
            raise ValueError(f"invalid registry row: {alias}")
    return data


def observed_models(events: list[dict]) -> list[str]:
    values: list[str] = []
    for event in events:
        candidates = [event.get("model")]
        message = event.get("message")
        if isinstance(message, dict):
            candidates.append(message.get("model"))
        for value in candidates:
            if isinstance(value, str) and value and value not in values:
                values.append(value)
    return values


def model_provenance(requested_model: str, events: list[dict], registry: dict) -> dict:
    observed = observed_models(events)
    if not observed:
        return {
            "requested_model": requested_model,
            "effective_model": UNOBSERVED,
            "effective_model_observed": False,
            "fallback_detected": "unknown",
            "fallback_reason": "runtime emitted no effective-model field",
        }
    if len(observed) != 1:
        return {
            "requested_model": requested_model,
            "effective_model": UNOBSERVED,
            "effective_model_observed": False,
            "fallback_detected": "unknown",
            "fallback_reason": "runtime emitted inconsistent effective-model values: " + ", ".join(observed),
        }
    effective = observed[0]
    tokens = registry.get(requested_model, {}).get("expected_model_tokens", [])
    matches = any(token.lower() in effective.lower() for token in tokens)
    return {
        "requested_model": requested_model,
        "effective_model": effective,
        "effective_model_observed": True,
        "fallback_detected": not matches if tokens else "unknown",
        "fallback_reason": None if matches else ("observed model differs from registered alias family" if tokens else "requested alias is not registered"),
    }


def aggregate_provenance(requested_model: str, rows: list[dict]) -> dict:
    all_observed = bool(rows) and all(
        row.get("effective_model_observed") is True and row.get("effective_model") not in {None, UNOBSERVED}
        for row in rows
    )
    observed = sorted({row.get("effective_model") for row in rows if row.get("effective_model_observed") and row.get("effective_model")})
    fallbacks = {row.get("fallback_detected") for row in rows}
    if all_observed and len(observed) == 1:
        effective, seen = observed[0], True
    else:
        effective, seen = UNOBSERVED, False
    if all_observed and fallbacks == {False}:
        fallback = False
    elif True in fallbacks:
        fallback = True
    else:
        fallback = "unknown"
    return {
        "requested_model": requested_model,
        "effective_model": effective,
        "effective_model_observed": seen,
        "fallback_detected": fallback,
        "fallback_reason": None if fallback is False else "per-scenario provenance differs, is missing, or indicates fallback",
    }


def report_header(root: Path, evaluation_type: str, requested_model: str, claude_version: str, dataset_version: str | None = None) -> dict:
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True, check=False).stdout.strip()
    return {
        "schema_version": 2,
        "commit_sha": commit,
        "dataset_version": dataset_version or "not-applicable",
        "claude_code_version": claude_version,
        "os": platform.platform(),
        "requested_model": requested_model,
        "effective_model": UNOBSERVED,
        "effective_model_observed": False,
        "fallback_detected": "unknown",
        "fallback_reason": "no scenario-level provenance has been aggregated",
        "evaluation_type": evaluation_type,
    }


def validate_report(report: dict, registry: dict) -> list[str]:
    errors: list[str] = []
    required = {
        "schema_version", "commit_sha", "dataset_version", "claude_code_version",
        "os", "requested_model", "effective_model", "effective_model_observed",
        "fallback_detected", "fallback_reason", "evaluation_type", "results",
    }
    missing = required - set(report)
    if missing:
        errors.append("missing top-level fields: " + ", ".join(sorted(missing)))
        return errors
    if report["schema_version"] != 2:
        errors.append("schema_version must be 2")
    if report["requested_model"] not in registry:
        errors.append("requested_model is not registered")
    if report["effective_model_observed"] is False and report["effective_model"] != UNOBSERVED:
        errors.append("unobserved effective model must be UNOBSERVED")
    if report["fallback_detected"] not in {True, False, "unknown"}:
        errors.append("fallback_detected must be true, false, or unknown")
    if report["fallback_detected"] is not False and not report.get("fallback_reason"):
        errors.append("unknown/true fallback requires fallback_reason")
    if report["evaluation_type"] not in {"activation", "mode_selection", "core", "team"}:
        errors.append("invalid evaluation_type")
    if not isinstance(report["results"], list):
        errors.append("results must be a list")
        return errors
    scenario_required = {
        "scenario_id", "status", "activation_tier", "selected_mode",
        "expected_mode", "cost_usd", "elapsed_seconds", "failure_class",
        "evidence", "limitations", "requested_model", "effective_model",
        "effective_model_observed", "fallback_detected", "fallback_reason",
    }
    for index, row in enumerate(report["results"]):
        if not isinstance(row, dict):
            errors.append(f"result {index} must be an object")
            continue
        absent = scenario_required - set(row)
        if absent:
            errors.append(f"result {index} missing fields: " + ", ".join(sorted(absent)))
        if row.get("status") not in STATUSES:
            errors.append(f"result {index} has invalid status")
        failure = row.get("failure_class")
        if failure is not None and failure not in FAILURE_CLASSES:
            errors.append(f"result {index} has invalid failure_class")
        if row.get("effective_model_observed") is False and row.get("effective_model") != UNOBSERVED:
            errors.append(f"result {index} infers an unobserved effective model")
        if row.get("fallback_detected") is not False and not row.get("fallback_reason"):
            errors.append(f"result {index} requires fallback_reason")
    return errors


def validate_limits(per_call_budget: float, total_budget: float, timeout: int) -> list[str]:
    errors = []
    if per_call_budget <= 0:
        errors.append("per-call budget must be positive")
    if total_budget <= 0:
        errors.append("total budget must be positive")
    if per_call_budget > total_budget:
        errors.append("per-call budget cannot exceed total budget")
    if timeout <= 0:
        errors.append("timeout must be positive")
    return errors
