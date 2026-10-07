from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def run_git(root: Path, args: list[str]) -> bytes:
    result = subprocess.run(["git", *args], cwd=root, capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError(f"git {' '.join(args)} failed: " + result.stderr.decode("utf-8", errors="replace"))
    return result.stdout


def git_inventory(root: Path) -> list[dict]:
    raw = run_git(root, ["status", "--porcelain=v1", "-z", "--untracked-files=all", "--ignored=matching"])
    fields = raw.split(b"\0")
    entries: list[dict] = []
    index = 0
    while index < len(fields):
        item = fields[index]
        index += 1
        if not item:
            continue
        text = item.decode("utf-8", errors="surrogateescape")
        if len(text) < 4:
            raise RuntimeError("malformed git status record")
        status, path = text[:2], text[3:]
        entry = {"status": status, "path": path.replace("\\", "/")}
        if "R" in status or "C" in status:
            if index >= len(fields) or not fields[index]:
                raise RuntimeError("rename/copy status lacks source path")
            entry["source_path"] = fields[index].decode("utf-8", errors="surrogateescape").replace("\\", "/")
            index += 1
        entries.append(entry)
    return entries


def filesystem_manifest(root: Path, *, excluded_prefixes: tuple[str, ...] = (".git/", ".claude/", "__pycache__/")) -> dict[str, str]:
    manifest: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if rel == ".git" or any(rel.startswith(prefix) for prefix in excluded_prefixes):
            continue
        manifest[rel] = sha256_file(path)
    return manifest


@dataclass(frozen=True)
class ScopeManifest:
    head: str
    index_tree: str
    baseline_files: dict[str, str]
    protected_files: dict[str, str]
    allowed_changed_paths: frozenset[str]
    expected_changed_paths: frozenset[str]
    allowed_artifacts: frozenset[str]
    forbidden_paths: frozenset[str]


def capture_scope(root: Path, *, protected_paths: list[str], allowed_changed_paths: list[str], expected_changed_paths: list[str], allowed_artifacts: list[str] | None = None, forbidden_paths: list[str] | None = None) -> ScopeManifest:
    protected = {rel: sha256_file(root / rel) for rel in protected_paths}
    return ScopeManifest(
        head=run_git(root, ["rev-parse", "HEAD"]).decode().strip(),
        index_tree=run_git(root, ["write-tree"]).decode().strip(),
        baseline_files=filesystem_manifest(root), protected_files=protected,
        allowed_changed_paths=frozenset(path.replace("\\", "/") for path in allowed_changed_paths),
        expected_changed_paths=frozenset(path.replace("\\", "/") for path in expected_changed_paths),
        allowed_artifacts=frozenset((allowed_artifacts or [])),
        forbidden_paths=frozenset((forbidden_paths or [])),
    )


def validate_scope(root: Path, manifest: ScopeManifest) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    try:
        head = run_git(root, ["rev-parse", "HEAD"]).decode().strip()
        index_tree = run_git(root, ["write-tree"]).decode().strip()
        inventory = git_inventory(root)
    except RuntimeError as exc:
        return [str(exc)], []
    if head != manifest.head:
        failures.append("repository HEAD changed")
    if index_tree != manifest.index_tree:
        failures.append("Git index changed")
    current = filesystem_manifest(root)
    changed = sorted({path for path in set(manifest.baseline_files) | set(current) if manifest.baseline_files.get(path) != current.get(path)})
    allowed = manifest.allowed_changed_paths | manifest.allowed_artifacts
    for path in changed:
        if path not in allowed:
            failures.append(f"out-of-scope path changed: {path}")
    for path in manifest.expected_changed_paths:
        if path not in changed:
            failures.append(f"expected changed path missing: {path}")
    for path in manifest.forbidden_paths:
        if path in changed or path in current and path not in manifest.baseline_files:
            failures.append(f"forbidden path changed: {path}")
    for path, digest in manifest.protected_files.items():
        if not (root / path).is_file() or sha256_file(root / path) != digest:
            failures.append(f"protected file changed: {path}")
    if any(entry["path"] == ".gitignore" and entry["status"] != "  " for entry in inventory):
        failures.append(".gitignore changed")
    return failures, changed


@dataclass(frozen=True)
class TrustedOracle:
    path: Path
    sha256: str


def materialize_oracle(directory: Path, name: str, source: str) -> TrustedOracle:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{name}.py"
    path.write_text(source, encoding="utf-8")
    return TrustedOracle(path, sha256_file(path))


def run_trusted_oracle(oracle: TrustedOracle, candidate_root: Path, *, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    if not oracle.path.is_file() or sha256_file(oracle.path) != oracle.sha256:
        raise RuntimeError("trusted oracle integrity changed")
    # Keep the candidate environment narrow, but retain the Windows variables
    # CPython 3.10 needs to locate system components and temporary storage.
    allowed_environment = {"PATH", "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT", "TEMP", "TMP"}
    env = {key: value for key, value in os.environ.items() if key.upper() in allowed_environment}
    env.update({"PYTHONNOUSERSITE": "1", "PYTHONDONTWRITEBYTECODE": "1"})
    result = subprocess.run([sys.executable, "-I", str(oracle.path), str(candidate_root.resolve())], cwd=candidate_root, env=env, text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=timeout, check=False)
    if sha256_file(oracle.path) != oracle.sha256:
        raise RuntimeError("trusted oracle changed during execution")
    return result
