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

MARKERS = {
    "SKILL.md": [
        "CLASSIFY -> DISCOVER -> INVESTIGATE -> PLAN -> IMPLEMENT -> VERIFY -> REVIEW -> COMPLETE",
        "Small-task fast path",
        "exact current authorization",
        "references/operating-model.md",
        "references/verification-review.md",
        "mark affected work/evidence `STALE`",
    ],
    "references/operating-model.md": [
        "Formal specification execution",
        "PHASE_VERIFIED != RELEASE_VERIFIED",
        "verify exact current authorization for the consequential action and target",
        "Mid-execution requirement changes",
        "STALE",
    ],
    "references/repository-investigation.md": [
        "Evidence hierarchy",
        "Optional codebase-intelligence providers",
        "Native fallback",
    ],
    "references/implementation-debugging.md": [
        "Bug-fix protocol",
        "Failure classification",
        "Never test-cheat",
    ],
    "references/verification-review.md": [
        "moderate, high, or critical-risk work",
        "Removal/completeness audit",
        "Evidence-based completion",
        "Frontend / browser verification",
        "Dependency changes",
        "BASELINE -> HYPOTHESIS -> CHANGE -> MEASURE -> COMPARE",
    ],
    "references/safety-profiles.md": [
        "Database profile",
        "Authentication / authorization profile",
        "Billing / payments / side-effect profile",
    ],
    "references/collaboration-state.md": [
        "Delegate only bounded work",
        "Long-horizon state",
        "Specialist routing",
        "User steering and requirement changes",
    ],
    "references/integrations.md": [
        "External integrations are optional",
        "Native fallback",
        "Optional CLAUDE.md routing",
    ],
    "references/source-synthesis.md": [
        "colbymchenry/codegraph",
        "kingbootoshi/cartographer",
        "Graphify-Labs/graphify",
    ],
    "references/evaluation-scenarios.md": [
        "Production-hardening adversarial matrix",
        "Required verifier unavailable",
        "Optimization by intuition",
    ],
}

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
            for word in ["implement", "debug", "refactor", "review", "release"]:
                if word not in desc.lower():
                    errors.append(f"description should discriminate engineering usage; missing concept: {word}")
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

    for rel, markers in MARKERS.items():
        path = root / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker.lower() not in text.lower():
                errors.append(f"{rel} missing required policy marker: {marker}")

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

    # Ambiguous active routing in runtime docs: explicit canonical wording required.
    vr = (root / "references/verification-review.md")
    if vr.exists():
        text = vr.read_text(encoding="utf-8").lower()
        if "moderate, high, or critical-risk work" not in text:
            errors.append("verification-review must explicitly cover Moderate, High, and Critical work")

    op = root / "references/operating-model.md"
    if op.exists():
        text = op.read_text(encoding="utf-8").lower()
        if "proceed without redundant confirmation" not in text:
            errors.append("operating-model missing exact-authorization/no-redundant-confirmation rule")

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
