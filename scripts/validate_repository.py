from __future__ import annotations

import json
import re
import sys
from pathlib import Path

MIN_PYTHON = (3, 10)
REQUIRED = {
    ".github/workflows/validate.yml",
    "README.md",
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
    "evals/formal-spec-team/README.md",
    "evals/formal-spec-team/run_team_eval.py",
    "evals/formal-spec-team/test_team_eval.py",
    "evals/run_l4_eval.py",
    "evals/test_completion_summary.py",
    "evals/test_l4_eval.py",
    "engineering-core/SKILL.md",
}
CORE_FAMILIES = {"small", "moderate", "auth", "dirty", "missing-graph", "formal-spec"}


def markdown_links(path: Path, text: str):
    for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
        clean = target.split("#", 1)[0]
        if clean and "://" not in clean and not clean.startswith("mailto:"):
            yield target, (path.parent / clean).resolve()


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

    workflow = root / ".github/workflows/validate.yml"
    if workflow.exists():
        text = workflow.read_text(encoding="utf-8")
        for marker in ["push:", "pull_request:", "workflow_dispatch:", "ubuntu-latest", "windows-latest", "'3.10'", "'3.14'", "actions/checkout@v7", "actions/setup-python@v7"]:
            if marker not in text:
                errors.append(f"CI workflow missing marker: {marker}")
        if "secrets." in text:
            errors.append("static CI must not depend on repository secrets")
        if "evals/formal-spec-team/test_team_eval.py" not in text:
            errors.append("CI workflow does not run Formal Spec Team Mode harness tests")
        if "evals/cross-model/test_cross_model_matrix.py" not in text:
            errors.append("CI workflow does not run cross-model provenance/schema tests")
        if "run_mode_selection_eval.py --model" in text or "run_activation_eval.py --mode" in text:
            errors.append("push CI must not run live cross-model evaluations")

    found: set[str] = set()
    for path in sorted((root / "evals/scenarios").glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            errors.append(f"invalid scenario {path.name}: {exc}")
            continue
        found.add(data.get("family", ""))
        if data.get("activation") not in {"explicit", "natural"}:
            errors.append(f"scenario {path.name} has invalid activation")
    missing = CORE_FAMILIES - found
    if missing:
        errors.append("missing L4 core families: " + ", ".join(sorted(missing)))

    scenario_doc = root / "engineering-core/references/evaluation-scenarios.md"
    if scenario_doc.exists():
        rows = {}
        for line in scenario_doc.read_text(encoding="utf-8").splitlines():
            match = re.match(r"\|\s*(\d+)\s*\|", line)
            if match:
                rows[int(match.group(1))] = line
        expected_ids = set(range(38, 114))
        if expected_ids - rows.keys():
            errors.append("adversarial L3 matrices must contain scenarios 38-113")
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
    for marker in ("evals/activation/reports/", "evals/formal-spec-team/reports/", "evals/cross-model/reports/"):
        if marker not in gitignore:
            errors.append(f"raw report directory is not ignored: {marker}")

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

    for path in (root / "evals").rglob("*"):
        if path.is_file() and "reports" not in path.parts:
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
