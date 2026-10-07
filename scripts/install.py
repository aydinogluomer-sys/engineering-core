from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


def run(command: list[str], cwd: Path | None = None) -> str:
    result = subprocess.run(command, cwd=cwd, text=True, encoding="utf-8", errors="replace", capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "command failed")
    return result.stdout.strip()


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        rel = path.relative_to(root).as_posix()
        if rel.startswith(".git/") or rel == ".engineering-core-install.json":
            continue
        digest.update(rel.encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def validate_source(checkout: Path) -> Path:
    package = checkout / "engineering-core"
    if not (package / "SKILL.md").is_file() or not (package / "scripts/validate_skill.py").is_file():
        raise RuntimeError("source does not contain the engineering-core package")
    run([os.fspath(Path(os.sys.executable)), os.fspath(package / "scripts/validate_skill.py"), os.fspath(package)], checkout)
    return package


def install(source: str, ref: str, destination: Path, replace_drift: bool) -> str:
    destination = destination.resolve()
    if destination.name != "engineering-core":
        raise RuntimeError("destination must end with engineering-core to prevent nested installation")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="engineering-core-stage-", dir=destination.parent) as raw:
        checkout = Path(raw) / "source"
        run(["git", "clone", "--quiet", "--no-checkout", source, os.fspath(checkout)])
        run(["git", "fetch", "--quiet", "--depth", "1", "origin", ref], checkout)
        run(["git", "checkout", "--quiet", "--detach", "FETCH_HEAD"], checkout)
        resolved = run(["git", "rev-parse", "HEAD"], checkout)
        package = validate_source(checkout)
        incoming = tree_digest(package)
        backup = None
        if destination.exists():
            metadata_path = destination / ".engineering-core-install.json"
            metadata = json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.is_file() else {}
            current = tree_digest(destination)
            if current == incoming:
                expected_metadata = {"source": source, "ref": ref, "resolved_commit": resolved, "content_sha256": incoming}
                if metadata == expected_metadata:
                    return "NO_OP"
                staged_metadata = destination / ".engineering-core-install.json.tmp"
                staged_metadata.write_text(json.dumps(expected_metadata, indent=2), encoding="utf-8")
                os.replace(staged_metadata, metadata_path)
                return "UPDATED_METADATA"
            if current != metadata.get("content_sha256") and not replace_drift:
                raise RuntimeError("destination has local drift; use --replace-drift after review")
            backup = destination.with_name(destination.name + ".backup")
            if backup.exists():
                raise RuntimeError(f"backup already exists: {backup}")
            outcome = "UPDATED"
        else:
            outcome = "INSTALLED"
        staged = Path(raw) / "engineering-core"
        shutil.copytree(package, staged)
        (staged / ".engineering-core-install.json").write_text(json.dumps({"source": source, "ref": ref, "resolved_commit": resolved, "content_sha256": incoming}, indent=2), encoding="utf-8")
        if backup:
            os.replace(destination, backup)
        try:
            os.replace(staged, destination)
        except Exception:
            if backup and backup.exists() and not destination.exists():
                os.replace(backup, destination)
            raise
        return outcome


def rollback(destination: Path) -> str:
    destination = destination.resolve()
    backup = destination.with_name(destination.name + ".backup")
    if not backup.is_dir():
        raise RuntimeError("no rollback backup exists")
    failed = destination.with_name(destination.name + ".failed")
    if failed.exists():
        raise RuntimeError(f"rollback quarantine already exists: {failed}")
    if destination.exists():
        os.replace(destination, failed)
    os.replace(backup, destination)
    return "ROLLED_BACK"


def main() -> int:
    parser = argparse.ArgumentParser(description="Install engineering-core from an explicit Git ref")
    parser.add_argument("--source")
    parser.add_argument("--ref")
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--replace-drift", action="store_true")
    parser.add_argument("--rollback", action="store_true")
    args = parser.parse_args()
    if args.rollback:
        print(rollback(args.destination))
        return 0
    if not args.source or not args.ref:
        parser.error("--source and --ref are required unless --rollback is used")
    print(install(args.source, args.ref, args.destination, args.replace_drift))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
