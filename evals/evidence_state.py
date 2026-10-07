from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

STATE_SCHEMA_VERSION = 1
EVIDENCE_STATUSES = {"PASS", "FAIL", "BLOCKED", "NOT_RUN", "STALE"}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest_hash(root: Path, paths: list[str]) -> tuple[str, dict[str, str | None]]:
    entries = {rel: sha256_file(root / rel) if (root / rel).is_file() else None for rel in sorted(set(paths))}
    digest = hashlib.sha256(json.dumps(entries, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return digest, entries


def validate_evidence(evidence: dict) -> list[str]:
    required = {"evidence_id", "requirement_ids", "actor_role", "actor_run_id", "command", "exit_code", "observed_at", "source_manifest_hash", "spec_hash", "environment_fingerprint", "output_artifact_hash", "limitations", "status", "source_paths"}
    if not isinstance(evidence, dict):
        return ["evidence must be an object"]
    errors = ["missing evidence fields: " + ", ".join(sorted(required - set(evidence)))] if required - set(evidence) else []
    if errors:
        return errors
    for field in ("evidence_id", "actor_role", "actor_run_id", "command", "observed_at", "source_manifest_hash", "spec_hash", "environment_fingerprint", "output_artifact_hash"):
        if not isinstance(evidence[field], str) or not evidence[field].strip():
            errors.append(f"{field} must be nonempty")
    if not isinstance(evidence["requirement_ids"], list) or not evidence["requirement_ids"] or not all(isinstance(item, str) and item for item in evidence["requirement_ids"]):
        errors.append("requirement_ids must be a nonempty string list")
    if isinstance(evidence["exit_code"], bool) or not isinstance(evidence["exit_code"], int):
        errors.append("exit_code must be an integer")
    if evidence["status"] not in EVIDENCE_STATUSES:
        errors.append("invalid evidence status")
    if not isinstance(evidence["limitations"], list) or not all(isinstance(item, str) for item in evidence["limitations"]):
        errors.append("limitations must be a string list")
    if not isinstance(evidence["source_paths"], list) or not all(isinstance(item, str) and item for item in evidence["source_paths"]):
        errors.append("source_paths must be a string list")
    return errors


def evidence_freshness(evidence: dict, root: Path, *, spec_hash: str, environment_fingerprint: str, artifact_exists: bool = True) -> tuple[str, list[str]]:
    errors = validate_evidence(evidence)
    if errors:
        return "BLOCKED", errors
    current_hash, _ = manifest_hash(root, evidence["source_paths"])
    reasons: list[str] = []
    if current_hash != evidence["source_manifest_hash"]:
        reasons.append("relevant source manifest changed")
    if spec_hash != evidence["spec_hash"]:
        reasons.append("specification hash changed")
    if environment_fingerprint != evidence["environment_fingerprint"]:
        reasons.append("relevant environment changed")
    if not artifact_exists:
        reasons.append("evidence artifact is missing")
    return ("STALE", reasons) if reasons else (evidence["status"], [])


def validate_dependency_graph(requirements: dict[str, dict]) -> list[str]:
    errors: list[str] = []
    if not isinstance(requirements, dict):
        return ["requirements must be an object"]
    for requirement_id, row in requirements.items():
        if not isinstance(row, dict):
            errors.append(f"{requirement_id} must be an object")
            continue
        dependencies = row.get("depends_on", [])
        if not isinstance(dependencies, list) or not all(isinstance(item, str) for item in dependencies):
            errors.append(f"{requirement_id} dependencies must be strings")
            continue
        if requirement_id in dependencies:
            errors.append(f"self-loop: {requirement_id}")
        for dependency in dependencies:
            if dependency not in requirements:
                errors.append(f"missing dependency: {requirement_id} -> {dependency}")
        supersedes = row.get("supersedes", [])
        if not isinstance(supersedes, list) or not all(isinstance(item, str) and item != requirement_id for item in supersedes):
            errors.append(f"{requirement_id} supersedes must contain distinct prior IDs")
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str, trail: list[str]) -> None:
        if node in visiting:
            errors.append("dependency cycle: " + " -> ".join(trail + [node]))
            return
        if node in visited or node not in requirements or not isinstance(requirements[node], dict):
            return
        visiting.add(node)
        for dependency in requirements[node].get("depends_on", []):
            visit(dependency, trail + [node])
        visiting.remove(node)
        visited.add(node)

    for node in requirements:
        visit(node, [])
    return sorted(set(errors))


def validate_state(state: dict) -> list[str]:
    required = {"schema_version", "revision", "repo_identity", "branch", "head", "objective", "authority", "requirements", "decision_locks", "work_units", "modified_paths", "evidence_refs", "findings", "owners", "next_action"}
    if not isinstance(state, dict):
        return ["state must be an object"]
    missing = required - set(state)
    if missing:
        return ["missing state fields: " + ", ".join(sorted(missing))]
    errors: list[str] = []
    if state["schema_version"] != STATE_SCHEMA_VERSION:
        errors.append("unsupported state schema_version")
    if isinstance(state["revision"], bool) or not isinstance(state["revision"], int) or state["revision"] < 0:
        errors.append("revision must be a nonnegative integer")
    for field in ("repo_identity", "branch", "head", "objective", "authority", "next_action"):
        if not isinstance(state[field], str) or not state[field].strip():
            errors.append(f"{field} must be nonempty")
    errors.extend(validate_dependency_graph(state["requirements"]))
    if not isinstance(state["owners"], dict):
        errors.append("owners must be an object")
    else:
        for unit_id, owner in state["owners"].items():
            if not isinstance(owner, dict) or owner.get("unit_id") != unit_id or not isinstance(owner.get("owner_run_id"), str) or owner.get("state") not in {"ACTIVE", "CANCELLED", "RELEASED", "STALE"}:
                errors.append(f"invalid owner record: {unit_id}")
    return errors


def load_state(path: Path) -> dict:
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"state is unreadable: {exc}") from exc
    errors = validate_state(state)
    if errors:
        raise ValueError("; ".join(errors))
    return state


def atomic_write_state(path: Path, state: dict, *, expected_revision: int | None) -> dict:
    existing = load_state(path) if path.exists() else None
    actual_revision = existing["revision"] if existing else 0
    if expected_revision != actual_revision:
        raise RuntimeError(f"state revision conflict: expected {expected_revision}, found {actual_revision}")
    candidate = dict(state)
    candidate["schema_version"] = STATE_SCHEMA_VERSION
    candidate["revision"] = actual_revision + 1
    errors = validate_state(candidate)
    if errors:
        raise ValueError("; ".join(errors))
    path.parent.mkdir(parents=True, exist_ok=True)
    if existing:
        shutil.copy2(path, path.with_suffix(path.suffix + ".bak"))
    handle = tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=path.parent, prefix=path.name + ".", suffix=".tmp")
    temp = Path(handle.name)
    try:
        with handle:
            json.dump(candidate, handle, indent=2, sort_keys=True)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
        if hasattr(os, "O_DIRECTORY"):
            directory_fd = os.open(path.parent, os.O_DIRECTORY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
    finally:
        if temp.exists():
            temp.unlink()
    return candidate


def recover_state(path: Path) -> dict:
    try:
        return load_state(path)
    except ValueError:
        backup = path.with_suffix(path.suffix + ".bak")
        return load_state(backup)


def claim_owner(state: dict, unit_id: str, owner_run_id: str, *, cancellation_ack: bool = False, isolated: bool = False) -> None:
    owners = state.setdefault("owners", {})
    current = owners.get(unit_id)
    if current and current.get("state") == "ACTIVE" and current.get("owner_run_id") != owner_run_id:
        if not (cancellation_ack or isolated):
            raise RuntimeError("active writer must acknowledge cancellation or prove isolation before transfer")
        current["state"] = "CANCELLED" if cancellation_ack else "STALE"
    owners[unit_id] = {"unit_id": unit_id, "owner_run_id": owner_run_id, "revision": state.get("revision", 0), "state": "ACTIVE", "claimed_at": datetime.now(timezone.utc).isoformat()}


def validate_resume_context(state: dict, *, repo_identity: str, branch: str, head: str) -> list[str]:
    errors = validate_state(state)
    if errors:
        return errors
    if Path(state["repo_identity"]).resolve() != Path(repo_identity).resolve():
        errors.append("repository identity differs from continuation state")
    if state["branch"] != branch:
        errors.append("branch differs from continuation state")
    if state["head"] != head:
        errors.append("HEAD differs from continuation state")
    return errors


def stale_closure(requirements: dict[str, dict], changed_ids: set[str]) -> set[str]:
    """Return changed requirements and all transitive dependents without reopening unrelated work."""
    stale = set(changed_ids)
    changed = True
    while changed:
        changed = False
        for requirement_id, row in requirements.items():
            dependencies = row.get("depends_on", []) if isinstance(row, dict) else []
            if requirement_id not in stale and stale.intersection(dependencies):
                stale.add(requirement_id)
                changed = True
    return stale
