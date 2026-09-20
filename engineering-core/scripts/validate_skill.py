from __future__ import annotations

import ast
import re
import sys
from pathlib import Path
from typing import Iterable

EXPECTED = {
    "SKILL.md",
    "examples/small-fix.md",
    "examples/normal-feature.md",
    "examples/high-risk-change.md",
    "examples/removal-task.md",
    "examples/large-spec-execution.md",
    "references/operating-model.md",
    "references/repository-investigation.md",
    "references/implementation-debugging.md",
    "references/verification-review.md",
    "references/safety-profiles.md",
    "references/collaboration-state.md",
    "references/integrations.md",
    "references/source-synthesis.md",
    "references/evaluation-scenarios.md",
    "scripts/validate_skill.py",
    "scripts/test_validate_skill.py",
}

FORBIDDEN_ACTIVE_FILES = {
    ".claude/settings.json",
    ".claude/settings.local.json",
    ".mcp.json",
    "plugin.json",
    ".claude-plugin/plugin.json",
    ".claude-plugin/marketplace.json",
    "package.json",
    "requirements.txt",
    "pyproject.toml",
}

MIN_PYTHON = (3, 10)

PLACEHOLDER_PATTERNS = [
    re.compile(r"\bTODO\b"),
    re.compile(r"\bTBD\b"),
    re.compile(r"\bFIXME\b"),
    re.compile(r"\bPLACEHOLDER\b", re.I),
]

REQUIRED_POLICY_OWNERS = {
    "operating-loop": "SKILL.md",
    "risk-model": "references/operating-model.md",
    "fast-path": "SKILL.md",
    "formal-spec-execution": "references/operating-model.md",
    "authorization-semantics": "references/operating-model.md",
    "requirement-change": "references/operating-model.md",
    "blocking-verification": "references/verification-review.md",
    "frontend-verification": "references/verification-review.md",
    "dependency-change": "references/verification-review.md",
    "performance-work": "references/verification-review.md",
    "completion-contract": "SKILL.md",
    "completion-output": "references/verification-review.md",
    "specialist-routing": "references/collaboration-state.md",
    "optional-integrations": "references/integrations.md",
    "deterministic-enforcement": "references/integrations.md",
    "activation-guidance": "references/integrations.md",
}

POLICY_ID_RE = re.compile(r"<!--\s*policy-id:\s*([a-z0-9]+(?:-[a-z0-9]+)*)\s*-->")
POLICY_COMMENT_RE = re.compile(r"<!--\s*policy-id:\s*([^>]*?)\s*-->")
HEADING_RE = re.compile(r"^(#{1,6})\s+\S", re.MULTILINE)

def rel_files(root: Path) -> set[str]:
    return {
        p.relative_to(root).as_posix()
        for p in root.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    }

def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        raise ValueError("SKILL.md must begin with YAML frontmatter delimiter")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError("SKILL.md frontmatter closing delimiter is missing")
    raw = text[4:end]
    body = text[end + 5:]
    data: dict[str, str] = {}
    for line in raw.splitlines():
        if not line.strip():
            continue
        if ":" not in line:
            raise ValueError(f"invalid frontmatter line: {line!r}")
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip()
    return data, body

def markdown_links(path: Path, text: str) -> Iterable[tuple[str, Path]]:
    for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
        if "://" in target or target.startswith("#") or target.startswith("mailto:"):
            continue
        clean = target.split("#", 1)[0]
        if not clean:
            continue
        yield target, (path.parent / clean).resolve()


def parse_markdown_structure(text: str) -> tuple[list[int], list[str], list[str]]:
    """Return heading levels, valid policy IDs, and malformed policy comments."""
    headings = [len(match.group(1)) for match in HEADING_RE.finditer(text)]
    raw_ids = [match.group(1).strip() for match in POLICY_COMMENT_RE.finditer(text)]
    valid_ids = POLICY_ID_RE.findall(text)
    malformed = [raw for raw in raw_ids if raw not in valid_ids]
    return headings, valid_ids, malformed

def classify_import_roots(path: Path) -> dict[str, str]:
    """Classify imports without importing or executing candidate modules."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[tuple[str, bool]] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update((n.name.split(".", 1)[0], False) for n in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                roots.add(((node.module or "").split(".", 1)[0], True))
            elif node.module:
                roots.add((node.module.split(".", 1)[0], False))

    result: dict[str, str] = {}
    script_dir = path.parent
    for root, relative in sorted(roots):
        label = root or "<relative>"
        if relative:
            result[label] = "local"
        elif root == "__future__" or root in sys.builtin_module_names:
            result[root] = "future/builtin"
        elif root in getattr(sys, "stdlib_module_names", frozenset()):
            result[root] = "stdlib"
        elif (script_dir / f"{root}.py").is_file() or (script_dir / root / "__init__.py").is_file():
            result[root] = "local"
        else:
            result[root] = "unknown external"
    return result


def unknown_external_imports(path: Path) -> list[str]:
    return sorted(
        root for root, classification in classify_import_roots(path).items()
        if classification == "unknown external"
    )

def validate(root: Path) -> list[str]:
    errors: list[str] = []
    root = root.resolve()

    if sys.version_info < MIN_PYTHON:
        errors.append(
            "validator requires Python "
            f"{MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ for positive standard-library classification"
        )

    actual = rel_files(root)
    missing = EXPECTED - actual
    extra = actual - EXPECTED
    if missing:
        errors.append("missing files: " + ", ".join(sorted(missing)))
    if extra:
        errors.append("unexpected files: " + ", ".join(sorted(extra)))

    for forbidden in FORBIDDEN_ACTIVE_FILES:
        if (root / forbidden).exists():
            errors.append(f"active integration/dependency file is forbidden in skill package: {forbidden}")

    skill = root / "SKILL.md"
    if skill.exists():
        text = skill.read_text(encoding="utf-8")
        try:
            fm, body = parse_frontmatter(text)
        except ValueError as exc:
            errors.append(str(exc))
        else:
            if set(fm) != {"name", "description"}:
                errors.append("SKILL.md frontmatter must contain only name and description")
            if fm.get("name") != "engineering-core":
                errors.append("frontmatter name must be engineering-core")
            desc = fm.get("description", "")
            if not desc or len(desc) > 1024:
                errors.append("frontmatter description must be present and at most 1024 characters")
            if "disable-model-invocation" in fm:
                errors.append("engineering-core must remain model-invocable")
        if len(text.splitlines()) > 200:
            errors.append("SKILL.md exceeds 200-line budget")

    all_md = [p for p in root.rglob("*.md") if p.is_file()]
    for path in all_md:
        text = path.read_text(encoding="utf-8")
        for target, resolved in markdown_links(path, text):
            try:
                resolved.relative_to(root)
            except ValueError:
                errors.append(f"{path.relative_to(root)} link escapes package: {target}")
                continue
            if not resolved.exists():
                errors.append(f"{path.relative_to(root)} broken local link: {target}")
        for pat in PLACEHOLDER_PATTERNS:
            if pat.search(text):
                errors.append(f"{path.relative_to(root)} contains unfinished scaffold marker matching {pat.pattern}")

    policy_locations: dict[str, list[str]] = {}
    for path in all_md:
        rel = path.relative_to(root).as_posix()
        headings, policy_ids, malformed = parse_markdown_structure(path.read_text(encoding="utf-8"))
        if not headings:
            errors.append(f"{rel} has no Markdown heading")
        for raw in malformed:
            errors.append(f"{rel} has malformed policy-id: {raw}")
        for policy_id in policy_ids:
            policy_locations.setdefault(policy_id, []).append(rel)

    for policy_id, owner in REQUIRED_POLICY_OWNERS.items():
        locations = policy_locations.get(policy_id, [])
        if not locations:
            errors.append(f"missing required policy-id: {policy_id} (owner: {owner})")
        elif len(locations) > 1:
            errors.append(f"duplicate policy-id: {policy_id} in {', '.join(locations)}")
        elif locations[0] != owner:
            errors.append(f"misplaced policy-id: {policy_id} belongs in {owner}, found in {locations[0]}")

    # Narrow policy-lint checks. These are heuristic/static only.
    combined = "\n".join(p.read_text(encoding="utf-8") for p in all_md)
    bad_guarantees = [
        r"\bthis skill guarantees prevention\b",
        r"\bunsafe actions are impossible\b",
        r"\bguarantees model behavior\b",
    ]
    for pat in bad_guarantees:
        if re.search(pat, combined, re.I):
            errors.append(f"deterministic-safety/runtime guarantee detected: {pat}")

    if re.search(r"\b(CodeGraph|Cartographer|Graphify)\b.{0,100}\b(required|mandatory prerequisite)\b", combined, re.I | re.S):
        errors.append("external code-intelligence provider appears mandatory")

    for py in [root / "scripts/validate_skill.py", root / "scripts/test_validate_skill.py"]:
        if py.exists():
            try:
                bad = unknown_external_imports(py)
            except SyntaxError as exc:
                errors.append(f"{py.relative_to(root)} syntax error: {exc}")
            else:
                if bad:
                    errors.append(
                        f"{py.relative_to(root)} imports unknown external package(s): {', '.join(bad)}; "
                        "runtime validation scripts must use only the Python standard library or sibling local modules"
                    )

    return errors

def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    errors = validate(root)
    if errors:
        print("FAIL: Structural and Policy-Lint Validator")
        for err in errors:
            print(f"- {err}")
        return 1
    print("PASS: Structural and Policy-Lint Validator found no configured violations")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
