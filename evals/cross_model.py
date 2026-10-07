from __future__ import annotations

import copy
import hashlib
import json
import platform
import re
import subprocess
from pathlib import Path

from harness_core import finite_number, validate_run_limits

UNOBSERVED = "UNOBSERVED"
SCHEMA_VERSION = 3
STATUSES = {"PASS", "FAIL", "BLOCKED", "NOT_RUN"}
FAILURE_CLASSES = {
    "activation", "mode_selection", "policy", "spec_compilation", "requirement_omission",
    "qa", "specialist_routing", "premature_closure", "stale_state", "release_audit",
    "effective_model_unknown", "fallback", "model_capability", "timeout", "budget",
    "permission", "CLI", "fixture", "scorer", "environment", "unknown",
}
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SCHEMA_PATH = Path(__file__).resolve().parent / "cross-model/schemas/cross-model-report.schema.json"


def dataset_digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def validate_json_schema_subset(instance: object, schema: dict, path: str = "$") -> list[str]:
    """Validate the deterministic JSON-Schema subset used by the report contract."""
    errors: list[str] = []
    expected_type = schema.get("type")
    accepted = expected_type if isinstance(expected_type, list) else [expected_type] if expected_type else []
    checkers = {
        "object": lambda value: isinstance(value, dict),
        "array": lambda value: isinstance(value, list),
        "string": lambda value: isinstance(value, str),
        "boolean": lambda value: type(value) is bool,
        "number": lambda value: finite_number(value),
        "null": lambda value: value is None,
    }
    if accepted and not any(kind in checkers and checkers[kind](instance) for kind in accepted):
        return [f"{path}: type must be {' or '.join(accepted)}"]
    if "const" in schema and instance != schema["const"]:
        errors.append(f"{path}: value differs from const")
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: value is outside enum")
    if isinstance(instance, str):
        if len(instance) < schema.get("minLength", 0):
            errors.append(f"{path}: string is too short")
        if "pattern" in schema and re.fullmatch(schema["pattern"], instance) is None:
            errors.append(f"{path}: string does not match pattern")
    if finite_number(instance) and "minimum" in schema and float(instance) < float(schema["minimum"]):
        errors.append(f"{path}: number is below minimum")
    if isinstance(instance, dict):
        missing = set(schema.get("required", [])) - set(instance)
        if missing:
            errors.append(f"{path}: missing required fields: {', '.join(sorted(missing))}")
        for key, child_schema in schema.get("properties", {}).items():
            if key in instance:
                errors.extend(validate_json_schema_subset(instance[key], child_schema, f"{path}.{key}"))
    if isinstance(instance, list):
        if schema.get("uniqueItems") and len({json.dumps(item, sort_keys=True, allow_nan=False) for item in instance}) != len(instance):
            errors.append(f"{path}: items must be unique")
        child_schema = schema.get("items")
        if isinstance(child_schema, dict):
            for index, item in enumerate(instance):
                errors.extend(validate_json_schema_subset(item, child_schema, f"{path}[{index}]"))
    return errors


def load_registry(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not data:
        raise ValueError("model registry must be a non-empty object")
    for alias, row in data.items():
        if not isinstance(alias, str) or not alias or not isinstance(row, dict) or not {"role", "team_gate_required", "expected_model_tokens"} <= set(row):
            raise ValueError(f"invalid registry row: {alias}")
        if type(row["team_gate_required"]) is not bool or not isinstance(row["expected_model_tokens"], list) or not all(isinstance(token, str) and token for token in row["expected_model_tokens"]):
            raise ValueError(f"invalid registry types: {alias}")
    return data


def observed_models(events: list[dict]) -> list[str]:
    values: list[str] = []
    for event in events:
        if not isinstance(event, dict):
            continue
        candidates = [event.get("model")]
        message = event.get("message")
        if isinstance(message, dict):
            candidates.append(message.get("model"))
        for value in candidates:
            if isinstance(value, str) and value and value not in values:
                values.append(value)
    return values


def model_provenance(requested_model: str, events: list[dict], registry: dict) -> dict:
    if requested_model not in registry:
        return {"requested_model": requested_model, "effective_model": UNOBSERVED, "effective_model_observed": False, "fallback_detected": "unknown", "fallback_reason": "requested alias is not registered"}
    observed = observed_models(events)
    if not observed:
        return {"requested_model": requested_model, "effective_model": UNOBSERVED, "effective_model_observed": False, "fallback_detected": "unknown", "fallback_reason": "runtime emitted no effective-model field"}
    if len(observed) != 1:
        return {"requested_model": requested_model, "effective_model": UNOBSERVED, "effective_model_observed": False, "fallback_detected": "unknown", "fallback_reason": "runtime emitted inconsistent effective-model values: " + ", ".join(observed)}
    effective = observed[0]
    matches = any(token.lower() in effective.lower() for token in registry[requested_model]["expected_model_tokens"])
    return {"requested_model": requested_model, "effective_model": effective, "effective_model_observed": True, "fallback_detected": not matches, "fallback_reason": None if matches else "observed model differs from registered alias family"}


def aggregate_provenance(requested_model: str, rows: list[dict]) -> dict:
    all_observed = bool(rows) and all(row.get("effective_model_observed") is True and isinstance(row.get("effective_model"), str) and row.get("effective_model") not in {"", UNOBSERVED} for row in rows)
    observed = sorted({row.get("effective_model") for row in rows if row.get("effective_model_observed") is True})
    fallbacks = {row.get("fallback_detected") for row in rows}
    effective, seen = (observed[0], True) if all_observed and len(observed) == 1 else (UNOBSERVED, False)
    if all_observed and fallbacks == {False}:
        fallback = False
    elif True in fallbacks:
        fallback = True
    else:
        fallback = "unknown"
    return {"requested_model": requested_model, "effective_model": effective, "effective_model_observed": seen, "fallback_detected": fallback, "fallback_reason": None if fallback is False else "per-scenario provenance differs, is missing, or indicates fallback"}


def provenance_gate_reasons(rows: list[dict]) -> list[str]:
    reasons: list[str] = []
    for row in rows:
        scenario = row.get("scenario_id", "unknown")
        if row.get("effective_model_observed") is not True:
            reasons.append(f"{scenario}: effective model identity was not observed")
        elif row.get("fallback_detected") is not False:
            reasons.append(f"{scenario}: requested model family was not served")
    return reasons


def report_header(root: Path, evaluation_type: str, requested_model: str, claude_version: str, dataset_version: str | None = None) -> dict:
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True, check=False).stdout.strip()
    version = dataset_version or "not-applicable"
    return {
        "schema_version": SCHEMA_VERSION, "commit_sha": commit, "dataset_version": version,
        "dataset_hash": hashlib.sha256(version.encode()).hexdigest(), "claude_code_version": claude_version,
        "os": platform.platform(), "requested_model": requested_model, "effective_model": UNOBSERVED,
        "effective_model_observed": False, "fallback_detected": "unknown",
        "fallback_reason": "no scenario-level provenance has been aggregated", "evaluation_type": evaluation_type,
        "scope": "partial", "selected_scenario_ids": [], "expected_scenario_ids": [],
        "evaluation_completed": False, "quality_gate_passed": None, "gate_reasons": [],
    }


def finalize_report(report: dict, *, expected_ids: list[str], selected_ids: list[str], quality_gate_passed: bool | None, gate_reasons: list[str], completed: bool = True) -> None:
    report["expected_scenario_ids"] = list(expected_ids)
    report["selected_scenario_ids"] = list(selected_ids)
    report["scope"] = "complete" if len(selected_ids) == len(expected_ids) and set(selected_ids) == set(expected_ids) else "partial"
    report["evaluation_completed"] = bool(completed)
    report["quality_gate_passed"] = quality_gate_passed
    report["gate_reasons"] = list(gate_reasons)


def adapt_legacy_report(report: dict) -> dict:
    adapted = copy.deepcopy(report)
    version = adapted.get("schema_version")
    if version == SCHEMA_VERSION:
        return adapted
    if version not in {1, 2}:
        raise ValueError("unsupported historical schema version")
    adapted["legacy_schema_version"] = version
    adapted["schema_version"] = SCHEMA_VERSION
    dataset = adapted.get("dataset_version") or "legacy-unknown"
    adapted.setdefault("dataset_version", dataset)
    adapted.setdefault("dataset_hash", hashlib.sha256(str(dataset).encode()).hexdigest())
    results = adapted.get("results") if isinstance(adapted.get("results"), list) else []
    ids = [row.get("scenario_id") for row in results if isinstance(row, dict) and isinstance(row.get("scenario_id"), str)]
    adapted.setdefault("scope", "partial")
    adapted.setdefault("selected_scenario_ids", ids)
    adapted.setdefault("expected_scenario_ids", ids)
    adapted.setdefault("evaluation_completed", bool(results))
    adapted.setdefault("quality_gate_passed", None)
    adapted.setdefault("gate_reasons", ["historical report adapted read-only; current quality gate not inferred"])
    return adapted


def _nonempty_string(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_report(report: dict, registry: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(report, dict):
        return ["report must be an object"]
    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        errors.extend("schema: " + error for error in validate_json_schema_subset(report, schema))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"report schema is unreadable: {exc}")
    required = {"schema_version", "commit_sha", "dataset_version", "dataset_hash", "claude_code_version", "os", "requested_model", "effective_model", "effective_model_observed", "fallback_detected", "fallback_reason", "evaluation_type", "scope", "selected_scenario_ids", "expected_scenario_ids", "evaluation_completed", "quality_gate_passed", "gate_reasons", "results"}
    missing = required - set(report)
    if missing:
        return ["missing top-level fields: " + ", ".join(sorted(missing))]
    if report["schema_version"] != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    if not _nonempty_string(report["commit_sha"]) or not SHA_RE.fullmatch(report["commit_sha"]):
        errors.append("commit_sha must be a 40-character lowercase hex SHA")
    for field in ("dataset_version", "claude_code_version", "os"):
        if not _nonempty_string(report[field]):
            errors.append(f"{field} must be nonempty")
    if not isinstance(report["dataset_hash"], str) or not re.fullmatch(r"[0-9a-f]{64}", report["dataset_hash"]):
        errors.append("dataset_hash must be a SHA-256 hex digest")
    if report["requested_model"] not in registry:
        errors.append("requested_model is not registered")
    if type(report["effective_model_observed"]) is not bool:
        errors.append("effective_model_observed must be boolean")
    elif report["effective_model_observed"] is False and report["effective_model"] != UNOBSERVED:
        errors.append("unobserved effective model must be UNOBSERVED")
    elif report["effective_model_observed"] is True and not _nonempty_string(report["effective_model"]):
        errors.append("observed effective model must be nonempty")
    if report["fallback_detected"] not in {True, False, "unknown"}:
        errors.append("fallback_detected must be true, false, or unknown")
    if report["fallback_detected"] is not False and not _nonempty_string(report.get("fallback_reason")):
        errors.append("unknown/true fallback requires fallback_reason")
    if report["evaluation_type"] not in {"activation", "mode_selection", "core", "team"}:
        errors.append("invalid evaluation_type")
    if report["scope"] not in {"complete", "partial"}:
        errors.append("scope must be complete or partial")
    for field in ("selected_scenario_ids", "expected_scenario_ids"):
        value = report[field]
        if not isinstance(value, list) or not all(_nonempty_string(item) for item in value) or len(value) != len(set(value)):
            errors.append(f"{field} must contain unique nonempty strings")
    if type(report["evaluation_completed"]) is not bool:
        errors.append("evaluation_completed must be boolean")
    if report["quality_gate_passed"] is not None and type(report["quality_gate_passed"]) is not bool:
        errors.append("quality_gate_passed must be boolean or null")
    if not isinstance(report["gate_reasons"], list) or not all(_nonempty_string(item) for item in report["gate_reasons"]):
        errors.append("gate_reasons must be a list of nonempty strings")
    if not isinstance(report["results"], list):
        errors.append("results must be a list")
        return errors
    result_ids: list[str] = []
    scenario_required = {"scenario_id", "status", "activation_tier", "selected_mode", "expected_mode", "reserved_cost_usd", "cost_usd", "accounted_cost_usd", "elapsed_seconds", "failure_class", "evidence", "limitations", "requested_model", "effective_model", "effective_model_observed", "fallback_detected", "fallback_reason"}
    for index, row in enumerate(report["results"]):
        if not isinstance(row, dict):
            errors.append(f"result {index} must be an object")
            continue
        absent = scenario_required - set(row)
        if absent:
            errors.append(f"result {index} missing fields: " + ", ".join(sorted(absent)))
            continue
        scenario_id = row["scenario_id"]
        if not _nonempty_string(scenario_id):
            errors.append(f"result {index} scenario_id must be nonempty")
        else:
            result_ids.append(scenario_id)
        if row["status"] not in STATUSES:
            errors.append(f"result {index} has invalid status")
        if row["failure_class"] is not None and row["failure_class"] not in FAILURE_CLASSES:
            errors.append(f"result {index} has invalid failure_class")
        for field in ("reserved_cost_usd", "accounted_cost_usd", "elapsed_seconds"):
            if not finite_number(row[field], nonnegative=True):
                errors.append(f"result {index} {field} must be finite and nonnegative")
        if row["cost_usd"] is not None and not finite_number(row["cost_usd"], nonnegative=True):
            errors.append(f"result {index} cost_usd must be null or finite and nonnegative")
        required_accounted = float(row["cost_usd"]) if finite_number(row["cost_usd"], nonnegative=True) else float(row["reserved_cost_usd"]) if finite_number(row["reserved_cost_usd"], nonnegative=True) else 0.0
        if finite_number(row["accounted_cost_usd"], nonnegative=True) and float(row["accounted_cost_usd"]) + 1e-12 < required_accounted:
            errors.append(f"result {index} accounted cost is below observed/reserved cost")
        if not isinstance(row["evidence"], dict) or not isinstance(row["limitations"], list) or not all(isinstance(item, str) for item in row["limitations"]):
            errors.append(f"result {index} evidence/limitations types are invalid")
        if row["requested_model"] != report["requested_model"]:
            errors.append(f"result {index} requested model differs from report")
        if type(row["effective_model_observed"]) is not bool:
            errors.append(f"result {index} effective_model_observed must be boolean")
        elif row["effective_model_observed"] is False and row["effective_model"] != UNOBSERVED:
            errors.append(f"result {index} infers an unobserved effective model")
        elif row["effective_model_observed"] is True:
            tokens = registry.get(row["requested_model"], {}).get("expected_model_tokens", [])
            family_matches = isinstance(row["effective_model"], str) and any(token.lower() in row["effective_model"].lower() for token in tokens)
            if row["fallback_detected"] is not (not family_matches):
                errors.append(f"result {index} fallback_detected conflicts with observed model family")
        if row["fallback_detected"] not in {True, False, "unknown"}:
            errors.append(f"result {index} has invalid fallback_detected")
        elif row["effective_model_observed"] is False and row["fallback_detected"] != "unknown":
            errors.append(f"result {index} cannot decide fallback without observed model identity")
        if row["fallback_detected"] is not False and not _nonempty_string(row.get("fallback_reason")):
            errors.append(f"result {index} requires fallback_reason")
    if len(result_ids) != len(set(result_ids)):
        errors.append("scenario_id values must be unique")
    selected, expected = report["selected_scenario_ids"], report["expected_scenario_ids"]
    if isinstance(selected, list) and set(result_ids) != set(selected):
        errors.append("result scenario IDs must equal selected_scenario_ids")
    if report["scope"] == "complete" and (not expected or set(selected) != set(expected) or len(selected) != len(expected)):
        errors.append("complete report must include every expected scenario exactly once")
    if not report["results"] and report["evaluation_completed"]:
        errors.append("empty report cannot be evaluation_completed")
    recomputed = aggregate_provenance(report["requested_model"], [row for row in report["results"] if isinstance(row, dict)])
    for field in ("effective_model", "effective_model_observed", "fallback_detected"):
        if report[field] != recomputed[field]:
            errors.append(f"top-level {field} does not match scenario provenance")
    if report["quality_gate_passed"] is True:
        if not report["evaluation_completed"] or any(row.get("status") != "PASS" for row in report["results"] if isinstance(row, dict)):
            errors.append("quality gate cannot pass with incomplete or non-PASS results")
        if provenance_gate_reasons([row for row in report["results"] if isinstance(row, dict)]):
            errors.append("quality gate cannot pass with fallback or unobserved model identity")
    return errors


def validate_limits(per_call_budget: float, total_budget: float, timeout: int, repetitions: int = 1, workers: int = 1) -> list[str]:
    return validate_run_limits(per_call_budget, total_budget, timeout, repetitions, workers)
