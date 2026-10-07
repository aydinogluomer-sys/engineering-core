from __future__ import annotations

import hashlib
import json
import time
import uuid
import re
from dataclasses import asdict, dataclass
from pathlib import Path

EVIDENCE_ARTIFACTS = {
    "section-inventory.json", "coverage.json", "team-state.json", "finding-ledger.json",
    "qa-report.json", "release-audit.json", "requirement-change-evidence.json",
    "continuation-state.json", "resume-evidence.json", "stage-records.json",
}


def tree_hash(root: Path, *, excluded: set[str] | None = None) -> str:
    excluded = EVIDENCE_ARTIFACTS | (excluded or set())
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        rel = path.relative_to(root).as_posix()
        if rel.startswith(".git/") or rel.startswith(".claude/") or rel in excluded:
            continue
        digest.update(rel.encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


@dataclass(frozen=True)
class StageRecord:
    run_id: str
    stage_id: str
    role: str
    process_identity: str
    started_ns: int
    ended_ns: int
    input_spec_hash: str
    input_candidate_hash: str
    output_candidate_hash: str
    input_artifact_hashes: dict[str, str]
    output_artifact_hashes: dict[str, str]
    evidence_pointer: str

    def to_dict(self) -> dict:
        return asdict(self)


def begin_stage(fixture: Path, run_id: str, stage_id: str, role: str) -> dict:
    spec = fixture / "implementation.md"
    return {
        "run_id": run_id,
        "stage_id": stage_id,
        "role": role,
        "process_identity": str(uuid.uuid4()),
        "started_ns": time.time_ns(),
        "input_spec_hash": hashlib.sha256(spec.read_bytes()).hexdigest(),
        "input_candidate_hash": tree_hash(fixture),
        "input_artifact_hashes": artifact_hashes(fixture),
    }


def end_stage(start: dict, fixture: Path, evidence_pointer: str) -> StageRecord:
    return StageRecord(
        **start,
        ended_ns=time.time_ns(),
        output_candidate_hash=tree_hash(fixture),
        output_artifact_hashes=artifact_hashes(fixture),
        evidence_pointer=evidence_pointer,
    )


def validate_stage_chain(records: list[dict], expected_roles: list[str], final_hash: str, allowed_drift_before: set[int] | None = None) -> list[str]:
    errors: list[str] = []
    required = set(StageRecord.__dataclass_fields__)
    if len(records) != len(expected_roles):
        errors.append("stage record count differs from scenario stages")
        return errors
    identities: set[str] = set()
    run_ids: set[str] = set()
    for index, (record, expected_role) in enumerate(zip(records, expected_roles)):
        if not isinstance(record, dict) or required - set(record):
            errors.append(f"stage {index + 1} record is incomplete")
            continue
        if record["role"] != expected_role:
            errors.append(f"stage {index + 1} role differs from evaluator contract")
        if not isinstance(record["process_identity"], str) or not record["process_identity"] or record["process_identity"] in identities:
            errors.append(f"stage {index + 1} process identity is missing or reused")
        identities.add(record.get("process_identity"))
        run_ids.add(record.get("run_id"))
        if type(record["started_ns"]) is not int or type(record["ended_ns"]) is not int or record["ended_ns"] <= record["started_ns"]:
            errors.append(f"stage {index + 1} timestamps are invalid")
        for field in ("input_spec_hash", "input_candidate_hash", "output_candidate_hash"):
            if not isinstance(record[field], str) or len(record[field]) != 64:
                errors.append(f"stage {index + 1} {field} is invalid")
        for field in ("input_artifact_hashes", "output_artifact_hashes"):
            values = record[field]
            if not isinstance(values, dict) or not all(isinstance(name, str) and isinstance(digest, str) and len(digest) == 64 for name, digest in values.items()):
                errors.append(f"stage {index + 1} {field} is invalid")
        if not isinstance(record["evidence_pointer"], str) or not record["evidence_pointer"]:
            errors.append(f"stage {index + 1} evidence pointer is missing")
        if index and index not in (allowed_drift_before or set()) and record.get("input_candidate_hash") != records[index - 1].get("output_candidate_hash"):
            errors.append(f"stage {index + 1} input does not chain from prior output")
    if len(run_ids) != 1:
        errors.append("stage records do not share one evaluator run id")
    if records and records[-1].get("output_candidate_hash") != final_hash:
        errors.append("final candidate hash differs from last stage record")
    return errors


def validate_stage_authority(records: list[dict], scenario_id: str, *, final_oracle_passed: bool) -> tuple[list[str], bool]:
    errors: list[str] = []
    if not records:
        return ["stage authority records are missing"], False
    for record in records:
        role = record.get("role")
        produced = set(record.get("output_artifact_hashes", {}))
        if role == "builder" and produced.intersection({"qa-report.json", "finding-ledger.json", "release-audit.json"}):
            errors.append("builder produced independent QA/audit artifacts")
        if role in {"qa", "reviewer2"} and "release-audit.json" in produced:
            errors.append(f"{role} produced the fresh release-audit artifact")
    if scenario_id == "two-key-closure" and len(records) >= 3:
        qa_out = records[1].get("output_artifact_hashes", {})
        review_in = records[2].get("input_artifact_hashes", {})
        review_out = records[2].get("output_artifact_hashes", {})
        if not {"qa-report.json", "finding-ledger.json"} <= set(qa_out):
            errors.append("QA stage did not author its required artifacts")
        if review_in.get("finding-ledger.json") != qa_out.get("finding-ledger.json"):
            errors.append("reviewer2 did not receive the QA finding ledger")
        if review_out.get("finding-ledger.json") == review_in.get("finding-ledger.json") or review_out.get("team-state.json") == review_in.get("team-state.json"):
            errors.append("reviewer2 did not author closure and phase-transition evidence")
        if records[2].get("input_candidate_hash") != records[2].get("output_candidate_hash"):
            errors.append("reviewer2 changed the candidate and cannot self-certify that version")
    if scenario_id == "large-spec" and len(records) >= 3:
        qa_in, qa_out = records[1].get("input_artifact_hashes", {}), records[1].get("output_artifact_hashes", {})
        audit_in, audit_out = records[2].get("input_artifact_hashes", {}), records[2].get("output_artifact_hashes", {})
        for name in ("qa-report.json", "finding-ledger.json"):
            if name not in qa_out or qa_in.get(name) == qa_out.get(name):
                errors.append(f"QA stage did not newly author {name}")
            if audit_in.get(name) != qa_out.get(name):
                errors.append(f"auditor did not receive QA-authored {name}")
        if audit_out.get("qa-report.json") != audit_in.get("qa-report.json"):
            errors.append("auditor rewrote the independent QA report")
        if audit_out.get("finding-ledger.json") != audit_in.get("finding-ledger.json"):
            errors.append("auditor rewrote the QA finding ledger")
    if records[-1].get("role") == "auditor":
        before, after = records[-1].get("input_artifact_hashes", {}), records[-1].get("output_artifact_hashes", {})
        if "release-audit.json" not in after or before.get("release-audit.json") == after.get("release-audit.json"):
            errors.append("auditor did not author a fresh release-audit artifact")
    independent = bool(
        not errors
        and final_oracle_passed
        and records[-1].get("role") in {"qa", "reviewer2", "auditor"}
        and (records[-1].get("role") != "reviewer2" or records[-1].get("input_candidate_hash") == records[-1].get("output_candidate_hash"))
    )
    return errors, independent


def artifact_hashes(root: Path) -> dict[str, str]:
    return {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in sorted(EVIDENCE_ARTIFACTS) if (root / name).is_file()}


def _meaningful_text(value: object, minimum: int = 6) -> bool:
    return isinstance(value, str) and len(value.strip()) >= minimum and bool(re.search(r"[A-Za-z0-9]{3}", value))


def _nonempty_strings(value: object) -> bool:
    return isinstance(value, list) and bool(value) and all(_meaningful_text(item, 3) for item in value)


def _resolves_evidence_pointer(pointer: object, root: Path | None, allowed: set[str], closure_artifacts: set[str]) -> bool:
    if not isinstance(pointer, str) or not pointer.strip():
        return False
    pointer = pointer.strip()
    if pointer in allowed:
        return True
    match = re.fullmatch(r"([^:\n]+):(\d+)", pointer)
    if root is None or not match or match.group(1) not in closure_artifacts:
        return False
    candidate = (root / match.group(1)).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return False
    if not candidate.is_file():
        return False
    line = int(match.group(2))
    return line > 0 and line <= len(candidate.read_text(encoding="utf-8", errors="replace").splitlines())


def validate_findings(
    ledger: object,
    final_hash: str,
    *,
    evaluator_independent_closure: bool = False,
    expected_requirements: set[str] | None = None,
    root: Path | None = None,
    allowed_evidence_pointers: set[str] | None = None,
    closure_artifacts: set[str] | None = None,
    closure_role: str | None = None,
    source_runs_by_role: dict[str, set[str]] | None = None,
) -> list[str]:
    errors: list[str] = []
    findings = ledger.get("findings") if isinstance(ledger, dict) else None
    if not isinstance(findings, list):
        return ["finding ledger must contain a findings list"]
    required = {"id", "source_role", "source_run", "severity", "linked_requirements", "description", "evidence", "state", "disposition_authority"}
    valid_severity = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
    valid_state = {"OPEN", "ACCEPTED", "FIXED", "VERIFIED_FIXED", "REJECTED_WITH_EVIDENCE", "DEFERRED_AUTHORIZED"}
    valid_roles = {"qa", "reviewer2", "auditor", "security-reviewer", "specialist"}
    allowed_pointers = allowed_evidence_pointers or set()
    closure_artifacts = closure_artifacts or set()
    source_runs_by_role = source_runs_by_role or {}
    for index, row in enumerate(findings):
        if not isinstance(row, dict) or required - set(row):
            errors.append(f"finding {index + 1} is incomplete")
            continue
        if not isinstance(row["id"], str) or not re.fullmatch(r"FIND-\d{3}", row["id"]):
            errors.append(f"finding {index + 1} has an invalid id")
        if row["source_role"] not in valid_roles or not isinstance(row["source_run"], str) or row["source_run"] not in source_runs_by_role.get(row["source_role"], set()):
            errors.append(f"finding {index + 1} has invalid source authority")
        if not _meaningful_text(row["description"], 8):
            errors.append(f"finding {index + 1} has an empty or placeholder description")
        linked = row["linked_requirements"]
        if not _nonempty_strings(linked) or (expected_requirements is not None and not set(linked) <= expected_requirements):
            errors.append(f"finding {index + 1} has invalid requirement linkage")
        if not _nonempty_strings(row["evidence"]):
            errors.append(f"finding {index + 1} has empty evidence")
        if not isinstance(row["disposition_authority"], str) or row["disposition_authority"] not in valid_roles or row["disposition_authority"] != closure_role:
            errors.append(f"finding {index + 1} has invalid disposition authority")
        if row["severity"] not in valid_severity or row["state"] not in valid_state:
            errors.append(f"finding {index + 1} has uncontrolled severity/state")
        if row["state"] in {"OPEN", "ACCEPTED", "FIXED"}:
            errors.append(f"finding {row['id']} is not independently closed")
        if row["state"] in {"REJECTED_WITH_EVIDENCE", "DEFERRED_AUTHORIZED"} and not row.get("disposition_evidence"):
            errors.append(f"finding {row['id']} lacks disposition evidence")
        if row["state"] == "VERIFIED_FIXED":
            closure = row.get("closure_evidence")
            if not isinstance(closure, dict) or not _resolves_evidence_pointer(closure.get("evidence_pointer"), root, allowed_pointers, closure_artifacts):
                errors.append(f"finding {row['id']} lacks current-hash closure evidence")
            elif closure.get("candidate_hash") is None and not evaluator_independent_closure:
                errors.append(f"finding {row['id']} lacks candidate-hash or evaluator closure binding")
            elif closure.get("candidate_hash") is not None and closure.get("candidate_hash") != final_hash:
                errors.append(f"finding {row['id']} cites a stale candidate hash")
    return errors


def validate_coverage(coverage: object, expected_ids: set[str]) -> list[str]:
    if not isinstance(coverage, dict) or not isinstance(coverage.get("requirements"), dict):
        return ["coverage artifact must contain a requirements object"]
    rows = coverage["requirements"]
    errors = []
    if set(rows) != expected_ids:
        errors.append("coverage artifact does not reconcile all requirements")
    required = {"acceptance", "work_unit", "affected_surface", "implementation", "evidence", "independent_review", "status"}
    valid_status = {"NOT_STARTED", "IN_PROGRESS", "IMPLEMENTED", "VERIFIED", "BLOCKED", "DEFERRED_AUTHORIZED"}
    for req_id, row in rows.items():
        if not isinstance(row, dict) or required - set(row):
            errors.append(f"coverage row {req_id} is incomplete")
        elif any(row[field] in (None, "", [], {}) for field in required):
            errors.append(f"coverage row {req_id} contains empty evidence")
        else:
            if not isinstance(row["acceptance"], str) or len(row["acceptance"].strip()) < 8:
                errors.append(f"coverage row {req_id} has placeholder acceptance")
            if not isinstance(row["work_unit"], str) or not re.fullmatch(r"WORK-\d{3}", row["work_unit"]):
                errors.append(f"coverage row {req_id} has invalid work-unit linkage")
            for field in ("affected_surface", "implementation", "evidence", "independent_review"):
                if not _nonempty_strings(row[field]):
                    errors.append(f"coverage row {req_id} has invalid {field} linkage")
            if row["status"] not in valid_status:
                errors.append(f"coverage row {req_id} has uncontrolled status")
            if row["status"] == "VERIFIED" and len(row["independent_review"]) < 1:
                errors.append(f"coverage row {req_id} lacks independent verification")
    return errors


def validate_sections(inventory: object, spec_path: Path) -> list[str]:
    source = spec_path.read_text(encoding="utf-8")
    headings = [match.group(1).strip() for match in re.finditer(r"^#{1,6}\s+(.+?)\s*$", source, re.M)]
    source_rows = {(heading, hashlib.sha256(heading.encode()).hexdigest()) for heading in headings}
    rows = inventory.get("sections") if isinstance(inventory, dict) else None
    if not isinstance(rows, list):
        return ["section inventory must contain a sections list"]
    observed: list[tuple[str, str]] = []
    errors: list[str] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or not isinstance(row.get("source_heading"), str) or not isinstance(row.get("source_hash"), str) or type(row.get("executable")) is not bool:
            errors.append(f"section inventory row {index + 1} is incomplete")
            continue
        observed.append((row["source_heading"], row["source_hash"]))
    if len(observed) != len(set(observed)) or set(observed) != source_rows:
        errors.append("section inventory does not exactly match unique source headings and hashes")
    return errors


def dump_records(path: Path, records: list[dict]) -> None:
    path.write_text(json.dumps(records, indent=2, sort_keys=True), encoding="utf-8")
