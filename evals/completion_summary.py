from __future__ import annotations

import re
from dataclasses import dataclass

ANCHOR_RE = re.compile(r"^### Execution Summary\s*$")
FIELD_RE = re.compile(r"^\s*(?:[-*]\s+)?(Policy|Risk|Status|Changed|Verified|Limitations|Blockers)\s*:\s*(.*?)\s*$", re.IGNORECASE)
TABLE_FIELD_RE = re.compile(r"^\s*\|\s*(Policy|Risk|Status|Changed|Verified|Limitations|Blockers)\s*\|\s*(.*?)\s*\|\s*$", re.IGNORECASE)
RISKS = {"Low", "Moderate", "High", "Critical"}
STATUSES = {"NO_CHANGE", "IMPLEMENTED", "VERIFIED", "NOT_VERIFIED", "BLOCKED"}
EMPTY_VALUES = {"", "none", "n/a", "not applicable", "no blockers"}


@dataclass(frozen=True)
class CompletionSummary:
    policy: str
    risk: str
    status: str
    changed: str
    verified: str
    limitations: str
    blockers: str | None = None


def parse_completion_summary(text: str) -> tuple[CompletionSummary | None, list[str]]:
    """Parse the final Execution Summary without claiming its fields are true."""
    anchors: list[int] = []
    in_fence = False
    offset = 0
    lines = text.splitlines(keepends=True)
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
        elif not in_fence and ANCHOR_RE.match(line.rstrip("\r\n")):
            anchors.append(offset + len(line.rstrip("\r\n")))
        offset += len(line)
    if not anchors:
        return None, ["missing ### Execution Summary anchor"]
    section = text[anchors[-1]:]
    fields: dict[str, str] = {}
    errors: list[str] = []
    current: str | None = None
    for raw_line in section.splitlines():
        table_match = TABLE_FIELD_RE.match(raw_line.replace("**", ""))
        if table_match:
            key = table_match.group(1).lower()
            if key in fields:
                errors.append(f"duplicate completion field: {key}")
            fields[key] = table_match.group(2).strip().strip("`")
            current = None
            continue
        for raw_segment in raw_line.split("|"):
            segment = raw_segment.replace("**", "").strip()
            if segment.startswith("#"):
                current = None
                continue
            match = FIELD_RE.match(segment)
            if match:
                key = match.group(1).lower()
                if key in fields:
                    errors.append(f"duplicate completion field: {key}")
                fields[key] = match.group(2).strip().strip("`")
                current = key
            elif current and segment:
                fields[current] = (fields[current] + " " + segment.lstrip("-* ")).strip()

    for required in ("policy", "risk", "status", "changed", "verified", "limitations"):
        if required not in fields:
            errors.append(f"missing completion field: {required}")
        elif not fields[required].strip():
            errors.append(f"empty completion field: {required}")
    if fields.get("policy") is not None and fields["policy"] != "engineering-core":
        errors.append("Policy must be engineering-core")
    risk_match = re.match(r"^(Low|Moderate|High|Critical)(?:\s|$|[-—:])", fields.get("risk", ""))
    if fields.get("risk") is not None:
        if not risk_match:
            errors.append(f"unknown Risk: {fields['risk']}")
        else:
            fields["risk"] = risk_match.group(1)
    if fields.get("status") is not None and fields["status"] not in STATUSES:
        errors.append(f"unknown Status: {fields['status']}")
    blockers = fields.get("blockers")
    if fields.get("status") == "VERIFIED" and blockers is not None and blockers.lower() not in EMPTY_VALUES:
        errors.append("VERIFIED cannot coexist with a declared blocker")
    if errors:
        return None, errors
    return CompletionSummary(
        policy=fields["policy"], risk=fields["risk"], status=fields["status"],
        changed=fields["changed"], verified=fields["verified"],
        limitations=fields["limitations"], blockers=blockers,
    ), []


def as_dict(summary: CompletionSummary | None) -> dict | None:
    if summary is None:
        return None
    return {
        "policy": summary.policy, "risk": summary.risk, "status": summary.status,
        "changed": summary.changed, "verified": summary.verified,
        "limitations": summary.limitations, "blockers": summary.blockers,
    }
