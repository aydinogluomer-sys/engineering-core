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
    "docs/l4-evaluation.md",
    "evals/README.md",
    "evals/activation/README.md",
    "evals/activation/ambiguous.json",
    "evals/activation/negative.json",
    "evals/activation/positive.json",
    "evals/activation/run_activation_eval.py",
    "evals/activation/test_activation_eval.py",
    "evals/completion_summary.py",
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
        expected_ids = set(range(38, 78))
        if expected_ids - rows.keys():
            errors.append("adversarial L3 matrices must contain scenarios 38-77")
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
