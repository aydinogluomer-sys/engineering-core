from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

MIN_PYTHON = (3, 10)
REQUIRED = {
    ".github/workflows/validate.yml",
    ".github/CODEOWNERS",
    ".github/pull_request_template.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "README.md",
    "SECURITY.md",
    "VERSION",
    "docs/governance.md",
    "docs/current-status.md",
    "docs/longitudinal-protocol.md",
    "docs/deterministic-enforcement.md",
    "docs/cross-model-reliability.md",
    "docs/l4-evaluation.md",
    "evals/README.md",
    "evals/activation/README.md",
    "evals/activation/ambiguous.json",
    "evals/activation/dataset-metadata.json",
    "evals/activation/holdout-ambiguous.json",
    "evals/activation/holdout-negative.json",
    "evals/activation/holdout-positive.json",
    "evals/activation/negative.json",
    "evals/activation/positive.json",
    "evals/activation/run_activation_eval.py",
    "evals/activation/test_activation_eval.py",
    "evals/completion_summary.py",
    "evals/cross_model.py",
    "evals/cross-model/README.md",
    "evals/cross-model/formal-long-horizon.json",
    "evals/cross-model/mode-selection.json",
    "evals/cross-model/model_registry.json",
    "evals/cross-model/run_mode_selection_eval.py",
    "evals/cross-model/schemas/cross-model-report.schema.json",
    "evals/cross-model/test_cross_model_matrix.py",
    "evals/evidence_state.py",
    "evals/harness_core.py",
    "evals/team_trust.py",
    "evals/test_evidence_state.py",
    "evals/test_harness_core.py",
    "evals/test_team_trust.py",
    "evals/test_trust.py",
    "evals/trust.py",
    "evals/failure-resistance/README.md",
    "evals/failure-resistance/test_failure_resistance.py",
    "evals/failure-resistance/run_stack_integrations.py",
    "evals/failure-resistance/browser_oracle.mjs",
    "evals/failure-resistance/postgres_oracle.py",
    "evals/failure-resistance/fixtures/typescript/baseline.ts",
    "evals/failure-resistance/fixtures/typescript/fixed.ts",
    "evals/failure-resistance/fixtures/postgresql/baseline.sql",
    "evals/failure-resistance/fixtures/postgresql/fixed.sql",
    "evals/failure-resistance/fixtures/browser/baseline.html",
    "evals/failure-resistance/fixtures/browser/fixed.html",
    "evals/live-run-manifest.template.json",
    "evals/run_manifest.py",
    "evals/sampling.py",
    "evals/test_run_manifest.py",
    "evals/test_sampling.py",
    "evidence/current/evidence.json",
    "evidence/current/SHA256SUMS.json",
    "evidence/current/integrations.json",
    "evidence/current/governance.json",
    "evidence/current/live-campaign-preflight.json",
    "evidence/longitudinal/README.md",
    "evidence/longitudinal/current-run.json",
    "evals/formal-spec-team/README.md",
    "evals/formal-spec-team/run_team_eval.py",
    "evals/formal-spec-team/test_team_eval.py",
    "evals/run_l4_eval.py",
    "evals/pressure_contract.py",
    "evals/test_completion_summary.py",
    "evals/test_l4_eval.py",
    "engineering-core/SKILL.md",
    "scripts/install.py",
    "scripts/install.ps1",
    "scripts/install.sh",
    "scripts/build_evidence_bundle.py",
    "scripts/test_install.py",
    "scripts/test_validate_repository.py",
}
CORE_FAMILIES = {"small", "moderate", "auth", "dirty", "missing-graph", "formal-spec"}
PRESSURE_PROFILES = {"adversarial-decision", "gate-integrity", "stale-evidence", "skip-qa", "release-audit", "sunk-cost", "authority", "orchestration"}
LONGITUDINAL_TASK_FIELDS = {"timestamp", "repository_task", "task_class", "risk", "expected_mode", "observed_mode", "completion_state", "verification_evidence", "regressions", "human_correction_required", "false_completion", "scope_drift", "cost", "notes"}
REQUIRED_CHECK_CONTEXTS = {
    "static-validation (ubuntu-latest, 3.10)",
    "static-validation (ubuntu-latest, 3.14)",
    "static-validation (windows-latest, 3.10)",
    "static-validation (windows-latest, 3.14)",
}


def validate_longitudinal_ledger(data: dict, *, now: datetime | None = None) -> list[str]:
    errors: list[str] = []
    required = {"schema_version", "state", "start_timestamp", "earliest_valid_completion_timestamp", "candidate_sha", "skill_version", "claude_code_version", "models_used", "required_task_fields", "tasks", "independent_final_analysis", "limitations"}
    if not isinstance(data, dict) or not required <= set(data):
        return ["longitudinal ledger is missing required fields"]
    if data["schema_version"] != 1 or data["state"] not in {"IN_PROGRESS", "PASS", "BLOCKED"}:
        errors.append("longitudinal ledger schema/state is invalid")
    try:
        start = datetime.fromisoformat(data["start_timestamp"].replace("Z", "+00:00"))
        earliest = datetime.fromisoformat(data["earliest_valid_completion_timestamp"].replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        errors.append("longitudinal timestamps are invalid")
    else:
        if earliest - start < timedelta(days=7):
            errors.append("longitudinal completion window is shorter than seven elapsed days")
        observed_now = now or datetime.now(timezone.utc)
        if data["state"] == "PASS" and observed_now < earliest:
            errors.append("longitudinal PASS predates the seven-day gate")
    if not re.fullmatch(r"[0-9a-f]{40}", str(data["candidate_sha"])):
        errors.append("longitudinal candidate SHA is invalid")
    if set(data["required_task_fields"]) != LONGITUDINAL_TASK_FIELDS:
        errors.append("longitudinal task field contract is incomplete")
    if not isinstance(data["tasks"], list):
        errors.append("longitudinal tasks must be a list")
    else:
        for index, task in enumerate(data["tasks"]):
            if not isinstance(task, dict) or not LONGITUDINAL_TASK_FIELDS <= set(task):
                errors.append(f"longitudinal task {index} is incomplete")
    if data["state"] == "PASS" and data["independent_final_analysis"] != "PASS":
        errors.append("longitudinal PASS lacks independent final analysis")
    return errors


def validate_governance_report(data: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict) or data.get("schema_version") != 1 or data.get("status") != "APPLIED":
        return ["governance report schema/status is invalid"]
    if data.get("repository") != "aydinogluomer-sys/engineering-core" or data.get("branch") != "main":
        errors.append("governance report targets the wrong repository or branch")
    source = data.get("source_check_run", {})
    if source.get("conclusion") != "success" or not isinstance(source.get("run_id"), int) or not re.fullmatch(r"[0-9a-f]{40}", str(source.get("candidate_sha", ""))):
        errors.append("governance report lacks a successful source check run")
    readback = data.get("readback", {})
    if readback.get("strict") is not True:
        errors.append("branch protection does not require up-to-date checks")
    if set(readback.get("required_status_checks", [])) != REQUIRED_CHECK_CONTEXTS:
        errors.append("branch protection required checks do not match the hosted matrix")
    if readback.get("enforce_admins") is not True:
        errors.append("branch protection is not enforced for administrators")
    if readback.get("required_pull_request_reviews") is not None:
        errors.append("branch protection is not solo-maintainer-safe")
    if readback.get("allow_force_pushes") is not False or readback.get("allow_deletions") is not False:
        errors.append("branch force push or deletion remains enabled")
    return errors


def validate_live_preflight(data: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        return ["live campaign preflight schema is invalid"]
    controls = data.get("cost_controls", {})
    if controls.get("max_total_spend_usd") is None:
        if data.get("status") != "NOT_AUTHORIZED" or data.get("paid_calls_executed") != 0:
            errors.append("unset spend cap must prohibit all paid calls")
        if controls.get("worst_case_within_user_cap") != "UNDETERMINED_CAP_UNSET":
            errors.append("unset spend cap cannot have a budget comparison result")
    elif not isinstance(controls.get("max_total_spend_usd"), (int, float)) or controls["max_total_spend_usd"] <= 0:
        errors.append("live campaign spend cap must be a positive number")
    if controls.get("automatic_retries") != 0 or controls.get("cli_max_budget_flag_observed") is not True:
        errors.append("live campaign cost controls are incomplete")
    if not data.get("claude_code", {}).get("version"):
        errors.append("Claude Code version was not observed")
    if set(data.get("alias_discovery", {}).get("registry_required", [])) != {"haiku", "sonnet", "opus", "fable"}:
        errors.append("live campaign registry aliases are incomplete")
    return errors


def validate_readme(text: str) -> list[str]:
    errors: list[str] = []
    blocks = re.findall(r"```mermaid\s*\n(.*?)```", text, re.DOTALL)
    if len(blocks) != 14:
        errors.append("README must contain exactly fourteen Mermaid system diagrams")
    for index in range(1, 15):
        if not re.search(rf"^### {index}\.\s+\S", text, re.MULTILINE):
            errors.append(f"README is missing numbered diagram heading {index}")
    for index, block in enumerate(blocks, 1):
        if not re.search(r"^(?:flowchart|sequenceDiagram|graph)\b", block.strip()):
            errors.append(f"README Mermaid diagram {index} lacks a supported declaration")
    return errors


def markdown_links(path: Path, text: str):
    for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
        clean = target.split("#", 1)[0]
        if clean and "://" not in clean and not clean.startswith("mailto:"):
            yield target, (path.parent / clean).resolve()


def workflow_structure(text: str) -> dict:
    """Parse only the workflow subset this repository owns; reject structure hidden in comments."""
    result = {"events": set(), "jobs": {}, "permissions": {}}
    section = None
    job = None
    in_steps = False
    current_step: dict | None = None
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        if indent == 0 and line.endswith(":"):
            section, job, in_steps = line[:-1], None, False
            continue
        if section == "on" and indent == 2 and line.endswith(":"):
            result["events"].add(line[:-1])
        elif section == "permissions" and indent == 2 and ":" in line:
            key, value = line.split(":", 1)
            result["permissions"][key.strip()] = value.strip()
        elif section == "jobs":
            if indent == 2 and line.endswith(":"):
                job = line[:-1]
                result["jobs"][job] = {"matrix": {}, "steps": []}
                in_steps = False
            elif job and indent == 4 and line == "steps:":
                in_steps = True
            elif job and indent == 6 and line.startswith("-") and in_steps:
                current_step = {}
                result["jobs"][job]["steps"].append(current_step)
                remainder = line[1:].strip()
                if ":" in remainder:
                    key, value = remainder.split(":", 1)
                    current_step[key.strip()] = value.strip()
            elif job and in_steps and indent >= 8 and ":" in line and current_step is not None:
                key, value = line.split(":", 1)
                current_step[key.strip()] = value.strip()
            elif job and "matrix:" in line:
                result["jobs"][job]["has_matrix"] = True
            elif job and indent >= 8 and not in_steps and ":" in line:
                key, value = line.split(":", 1)
                if value.strip().startswith("["):
                    result["jobs"][job]["matrix"][key.strip()] = value.strip()
    return result


def validate_workflow(text: str) -> list[str]:
    errors: list[str] = []
    parsed = workflow_structure(text)
    if not {"push", "pull_request", "workflow_dispatch"} <= parsed["events"]:
        errors.append("CI workflow is missing required trigger structure")
    if parsed["permissions"].get("contents") != "read":
        errors.append("CI workflow must use read-only contents permission")
    job = parsed["jobs"].get("static-validation")
    if not job:
        return errors + ["CI workflow is missing static-validation job"]
    if not job.get("has_matrix") or "ubuntu-latest" not in job["matrix"].get("os", "") or "windows-latest" not in job["matrix"].get("os", ""):
        errors.append("CI workflow must structurally define the OS matrix")
    if "'3.10'" not in job["matrix"].get("python", "") or "'3.14'" not in job["matrix"].get("python", ""):
        errors.append("CI workflow must structurally define the Python matrix")
    uses = [step.get("uses", "") for step in job["steps"]]
    for action in ("actions/checkout", "actions/setup-python"):
        matching = [value for value in uses if value.startswith(action + "@")]
        if len(matching) != 1 or not re.fullmatch(re.escape(action) + r"@[0-9a-f]{40}(?:\s+#\s+v\d+)?", matching[0]):
            errors.append(f"CI action must be pinned to one immutable SHA: {action}")
    commands = "\n".join(step.get("run", "") for step in job["steps"])
    required_commands = ("test_team_eval.py", "test_cross_model_matrix.py", "evals/failure-resistance", "evals.test_run_manifest", "test_install.py", "test_validate_repository.py", "python scripts/validate_repository.py .")
    for command in required_commands:
        if command not in commands:
            errors.append(f"CI workflow does not execute required validation: {command}")
    return errors


def validate(root: Path) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    if sys.version_info < MIN_PYTHON:
        errors.append("repository validation requires Python 3.10+")
    for rel in sorted(REQUIRED):
        if not (root / rel).is_file():
            errors.append(f"missing repository file: {rel}")

    for path in root.rglob("*.md"):
        if any(part in {".git", "reports"} for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8")
        if "YOUR_GITHUB_USERNAME" in text:
            errors.append(f"placeholder GitHub username in {path.relative_to(root)}")
        for target, resolved in markdown_links(path, text):
            try:
                resolved.relative_to(root)
            except ValueError:
                errors.append(f"link escapes repository in {path.relative_to(root)}: {target}")
            else:
                if not resolved.exists():
                    errors.append(f"broken local link in {path.relative_to(root)}: {target}")

    readme = root / "README.md"
    if readme.exists():
        errors.extend(validate_readme(readme.read_text(encoding="utf-8")))

    workflow = root / ".github/workflows/validate.yml"
    if workflow.exists():
        text = workflow.read_text(encoding="utf-8")
        errors.extend(validate_workflow(text))
        if "secrets." in text:
            errors.append("static CI must not depend on repository secrets")
        if "run_mode_selection_eval.py --model" in text or "run_activation_eval.py --mode" in text:
            errors.append("push CI must not run live cross-model evaluations")

    found: set[str] = set()
    pressure_found: set[str] = set()
    for path in sorted((root / "evals/scenarios").glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            errors.append(f"invalid scenario {path.name}: {exc}")
            continue
        found.add(data.get("family", ""))
        if data.get("pressure_profile"):
            pressure_found.add(data["pressure_profile"])
            if data.get("expected_completion_status") not in {"IMPLEMENTED", "VERIFIED", "NOT_VERIFIED", "BLOCKED"}:
                errors.append(f"pressure scenario {path.name} lacks a controlled expected completion status")
        if data.get("activation") not in {"explicit", "natural"}:
            errors.append(f"scenario {path.name} has invalid activation")
    missing = CORE_FAMILIES - found
    if missing:
        errors.append("missing L4 core families: " + ", ".join(sorted(missing)))
    if pressure_found != PRESSURE_PROFILES:
        errors.append("L4 pressure profiles do not match the required eight-family set")

    scenario_doc = root / "engineering-core/references/evaluation-scenarios.md"
    if scenario_doc.exists():
        rows = {}
        for line in scenario_doc.read_text(encoding="utf-8").splitlines():
            match = re.match(r"\|\s*(\d+)\s*\|", line)
            if match:
                rows[int(match.group(1))] = line
        expected_ids = set(range(38, 138))
        if expected_ids - rows.keys():
            errors.append("adversarial L3 matrices must contain scenarios 38-137")
        for number in expected_ids.intersection(rows):
            if len(rows[number].split("|")) < 10 or "L3" not in rows[number]:
                errors.append(f"L3 scenario {number} lacks required trace fields/evidence level")

    activation_dir = root / "evals/activation"
    activation_ids: set[str] = set()
    expected_counts = {"positive": 12, "negative": 8, "ambiguous": 4}
    for label, minimum in expected_counts.items():
        path = activation_dir / f"{label}.json"
        if not path.exists():
            continue
        try:
            rows = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            errors.append(f"invalid activation dataset {path.name}: {exc}")
            continue
        if not isinstance(rows, list) or len(rows) < minimum:
            errors.append(f"activation dataset {label} requires at least {minimum} cases")
            continue
        for row in rows:
            if not isinstance(row, dict) or not {"id", "category", "profiles", "prompt"} <= set(row):
                errors.append(f"activation dataset {label} has an invalid row")
                continue
            if row["id"] in activation_ids:
                errors.append(f"duplicate activation case id: {row['id']}")
            activation_ids.add(row["id"])
            if "full" not in row["profiles"]:
                errors.append(f"activation case {row['id']} is missing full profile")

    holdout_minimums = {"holdout-positive": 30, "holdout-negative": 20, "holdout-ambiguous": 10}
    for name, minimum in holdout_minimums.items():
        path = activation_dir / f"{name}.json"
        if not path.exists():
            continue
        try:
            rows = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            errors.append(f"invalid sealed activation dataset {path.name}: {exc}")
            continue
        if not isinstance(rows, list) or len(rows) < minimum:
            errors.append(f"sealed activation dataset {name} requires at least {minimum} cases")
        elif not all(isinstance(row, dict) and {"id", "category", "prompt"} <= set(row) for row in rows):
            errors.append(f"sealed activation dataset {name} has an invalid row")

    team_root = root / "evals/formal-spec-team"
    expected_team_scenarios = {"01-large-spec.json", "02-requirement-change.json", "03-cross-session.json", "04-two-key-closure.json", "05-release-auditor.json"}
    found_team_scenarios = {path.name for path in (team_root / "scenarios").glob("*.json")}
    if found_team_scenarios != expected_team_scenarios:
        errors.append("Formal Spec Team Mode scenarios do not match the required five-file set")
    required_fixtures = {"large-spec", "requirement-change", "cross-session-resume", "independent-qa", "release-audit"}
    found_fixtures = {path.name for path in (team_root / "fixtures").iterdir() if path.is_dir()} if (team_root / "fixtures").exists() else set()
    if found_fixtures != required_fixtures:
        errors.append("Formal Spec Team Mode fixtures do not match the required set")

    gitignore = (root / ".gitignore").read_text(encoding="utf-8") if (root / ".gitignore").exists() else ""
    for marker in ("evals/activation/reports/", "evals/formal-spec-team/reports/", "evals/cross-model/reports/", "node_modules/", ".playwright/", ".postgres-data/"):
        if marker not in gitignore:
            errors.append(f"raw report directory is not ignored: {marker}")

    forbidden_parts = {"node_modules", ".playwright", ".postgres-data", "pgdata"}
    for path in root.rglob("*"):
        if path.is_file() and forbidden_parts.intersection(path.parts):
            errors.append(f"generated tool/database artifact in repository: {path.relative_to(root)}")

    integration_path = root / "evidence/current/integrations.json"
    if integration_path.exists():
        try:
            report = json.loads(integration_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"invalid integration evidence: {exc}")
        else:
            sys.path.insert(0, str(root / "evals/failure-resistance"))
            from failure_resistance import protected_stack_hash, validate_stack_report
            errors.extend(f"integration evidence: {error}" for error in validate_stack_report(report))
            if report.get("protected_inputs_sha256") != protected_stack_hash(root):
                errors.append("integration evidence does not match protected fixtures/oracles")

    longitudinal_path = root / "evidence/longitudinal/current-run.json"
    if longitudinal_path.exists():
        try:
            ledger = json.loads(longitudinal_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"invalid longitudinal ledger: {exc}")
        else:
            errors.extend(validate_longitudinal_ledger(ledger))

    governance_path = root / "evidence/current/governance.json"
    if governance_path.exists():
        try:
            governance = json.loads(governance_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"invalid governance evidence: {exc}")
        else:
            errors.extend(validate_governance_report(governance))

    live_preflight_path = root / "evidence/current/live-campaign-preflight.json"
    if live_preflight_path.exists():
        try:
            live_preflight = json.loads(live_preflight_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"invalid live campaign preflight: {exc}")
        else:
            errors.extend(validate_live_preflight(live_preflight))

    registry = root / "evals/cross-model/model_registry.json"
    if registry.exists():
        try:
            models = json.loads(registry.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"invalid cross-model registry: {exc}")
        else:
            if set(models) != {"haiku", "sonnet", "opus", "fable"}:
                errors.append("cross-model registry must contain exactly four stable aliases")

    mode_dataset = root / "evals/cross-model/mode-selection.json"
    if mode_dataset.exists():
        try:
            modes = json.loads(mode_dataset.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"invalid mode-selection dataset: {exc}")
        else:
            if not isinstance(modes, list) or len(modes) < 10 or not any(row.get("abort") for row in modes if isinstance(row, dict)):
                errors.append("mode-selection dataset must contain ten cases including Fast-Exit abort")

    for scan_root in (root / "evals", root / "evidence"):
        for path in scan_root.rglob("*"):
            if path.is_file() and "reports" not in path.parts and "__pycache__" not in path.parts:
                text = path.read_text(encoding="utf-8", errors="ignore")
                if re.search(r"(sk-ant-[A-Za-z0-9_-]+|ghp_[A-Za-z0-9]+|github_pat_[A-Za-z0-9_]+|AKIA[0-9A-Z]{16}|BEGIN (RSA |OPENSSH )?PRIVATE KEY)", text):
                    errors.append(f"secret-like material in {path.relative_to(root)}")
    return errors


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    errors = validate(root)
    if errors:
        print("FAIL: Repository validation")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: Repository validation found no configured violations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
