from __future__ import annotations

import argparse
import json
import os
import secrets
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from failure_resistance import protected_stack_hash, validate_stack_report


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FIXTURES = HERE / "fixtures"
TYPESCRIPT_VERSION = "7.0.2"
PLAYWRIGHT_VERSION = "1.64.0"
POSTGRES_IMAGE = "postgres:17.6-alpine"


def run(command: list[str], *, input_text: str | None = None, env: dict[str, str] | None = None, timeout: int = 300) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=ROOT,
        input=input_text,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
        env=env,
        timeout=timeout,
    )


def command_version(command: list[str]) -> str:
    result = run(command)
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout).strip())
    return (result.stdout or result.stderr).strip()


def provision_node_tools(tool_cache: Path, npm: str) -> tuple[Path, Path, dict[str, str]]:
    workspace = tool_cache / f"node-ts-{TYPESCRIPT_VERSION}-pw-{PLAYWRIGHT_VERSION}"
    workspace.mkdir(parents=True, exist_ok=True)
    package_json = workspace / "package.json"
    package_json.write_text(json.dumps({"private": True}), encoding="utf-8")
    install = run(
        [npm, "install", "--prefix", str(workspace), "--no-save", "--ignore-scripts", "--no-audit", "--no-fund", f"typescript@{TYPESCRIPT_VERSION}", f"playwright@{PLAYWRIGHT_VERSION}"],
        env={**os.environ, "npm_config_cache": str(tool_cache / "npm-cache")},
        timeout=600,
    )
    if install.returncode:
        raise RuntimeError(f"isolated npm provisioning failed: {install.stderr[-2000:]}")
    typescript = workspace / "node_modules" / "typescript"
    playwright = workspace / "node_modules" / "playwright"
    versions = {
        "typescript": json.loads((typescript / "package.json").read_text(encoding="utf-8"))["version"],
        "playwright": json.loads((playwright / "package.json").read_text(encoding="utf-8"))["version"],
    }
    if versions != {"typescript": TYPESCRIPT_VERSION, "playwright": PLAYWRIGHT_VERSION}:
        raise RuntimeError(f"resolved node tool versions differ from pins: {versions}")
    return typescript, playwright, versions


def typescript_cell(node: str, typescript: Path, integrity_before: str) -> dict:
    tsc = typescript / "bin" / "tsc"
    common = [node, str(tsc), "--strict", "--noEmit", "--pretty", "false", "--skipLibCheck", "false"]
    baseline = run([*common, str(FIXTURES / "typescript" / "baseline.ts")])
    fixed_path = FIXTURES / "typescript" / "fixed.ts"
    fixed_text = fixed_path.read_text(encoding="utf-8")
    fixed = run([*common, str(fixed_path)])
    diagnostic = (baseline.stdout + baseline.stderr).strip()
    suppressed = any(marker in fixed_text for marker in ("@ts-ignore", "@ts-nocheck", "@ts-expect-error"))
    passed = baseline.returncode != 0 and "TS2322" in diagnostic and fixed.returncode == 0 and not suppressed
    return {
        "status": "PASS" if passed else "FAIL",
        "tool_observed": True,
        "tool_version": command_version([node, str(tsc), "--version"]),
        "provision_method": "isolated npm exact-version cache",
        "baseline": {"exit_code": baseline.returncode, "expected_diagnostic": "TS2322", "diagnostic_observed": "TS2322" in diagnostic, "diagnostic_tail": diagnostic[-1000:]},
        "fixed": {"exit_code": fixed.returncode, "suppression_directive": suppressed},
        "integrity": {"before": integrity_before, "after": "PENDING"},
    }


def find_browser(explicit: str | None) -> Path:
    candidates = [
        explicit,
        shutil.which("chrome"),
        shutil.which("chromium"),
        shutil.which("msedge"),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return Path(candidate).resolve()
    raise RuntimeError("no supported browser executable found")


def parse_json_line(text: str) -> dict:
    for line in reversed(text.splitlines()):
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    return {}


def browser_cell(node: str, playwright: Path, browser: Path, integrity_before: str) -> dict:
    oracle = HERE / "browser_oracle.mjs"
    baseline = run([node, str(oracle), str(playwright), str(browser), str(FIXTURES / "browser" / "baseline.html")])
    fixed = run([node, str(oracle), str(playwright), str(browser), str(FIXTURES / "browser" / "fixed.html")])
    baseline_data = parse_json_line(baseline.stdout)
    fixed_data = parse_json_line(fixed.stdout)
    passed = baseline.returncode != 0 and fixed.returncode == 0 and fixed_data.get("passed") is True
    return {
        "status": "PASS" if passed else "FAIL",
        "tool_observed": bool(fixed_data.get("browser_version")),
        "tool_version": f"Playwright {PLAYWRIGHT_VERSION}; Chromium {fixed_data.get('browser_version', 'UNOBSERVED')}",
        "browser_executable": str(browser),
        "provision_method": "isolated npm exact-version Playwright with discovered local browser",
        "baseline": {"exit_code": baseline.returncode, "oracle": baseline_data},
        "fixed": {"exit_code": fixed.returncode, "oracle": fixed_data},
        "integrity": {"before": integrity_before, "after": "PENDING"},
    }


def docker_psql(docker: str, container: str, sql: str) -> subprocess.CompletedProcess[str]:
    return run(
        [docker, "exec", "-i", container, "psql", "-X", "-A", "-t", "-v", "ON_ERROR_STOP=1", "-U", "postgres", "-d", "engineering_core_eval"],
        input_text=sql,
    )


def postgres_cell(docker: str, integrity_before: str) -> dict:
    pull = run([docker, "pull", POSTGRES_IMAGE], timeout=900)
    if pull.returncode:
        raise RuntimeError(f"PostgreSQL image pull failed: {pull.stderr[-2000:]}")
    digest_result = run([docker, "image", "inspect", "--format", "{{index .RepoDigests 0}}", POSTGRES_IMAGE])
    digest = digest_result.stdout.strip() if digest_result.returncode == 0 else "UNOBSERVED"
    container = "engineering-core-eval-" + secrets.token_hex(6)
    started = run([docker, "run", "-d", "--rm", "--name", container, "-e", "POSTGRES_HOST_AUTH_METHOD=trust", POSTGRES_IMAGE])
    if started.returncode:
        raise RuntimeError(f"PostgreSQL container start failed: {started.stderr[-2000:]}")
    try:
        ready = False
        for _ in range(30):
            probe = run([docker, "exec", container, "pg_isready", "-U", "postgres"], timeout=20)
            if probe.returncode == 0:
                ready = True
                break
            time.sleep(1)
        if not ready:
            raise RuntimeError("PostgreSQL container did not become ready")
        created = run([docker, "exec", "-i", container, "createdb", "-U", "postgres", "engineering_core_eval"])
        if created.returncode:
            raise RuntimeError(created.stderr.strip())
        bootstrap = """
CREATE ROLE app_owner NOLOGIN;
CREATE ROLE tenant_a NOLOGIN;
CREATE ROLE tenant_b NOLOGIN;
CREATE ROLE service_role NOLOGIN BYPASSRLS;
GRANT USAGE ON SCHEMA public TO app_owner, tenant_a, tenant_b, service_role;
"""
        if docker_psql(docker, container, bootstrap).returncode:
            raise RuntimeError("PostgreSQL role bootstrap failed")
        oracle = HERE / "postgres_oracle.py"

        baseline_sql = (FIXTURES / "postgresql" / "baseline.sql").read_text(encoding="utf-8")
        if docker_psql(docker, container, baseline_sql).returncode:
            raise RuntimeError("PostgreSQL baseline fixture setup failed")
        docker_psql(docker, container, "INSERT INTO public.tenant_items(tenant_id,payload) VALUES ('tenant-a','protected-a'),('tenant-b','protected-b');")
        baseline = run([sys.executable, "-I", str(oracle), docker, container])
        baseline_data = parse_json_line(baseline.stdout)

        reset = docker_psql(docker, container, "DROP TABLE public.tenant_items CASCADE;")
        if reset.returncode:
            raise RuntimeError("PostgreSQL fixture reset failed")
        fixed_sql = (FIXTURES / "postgresql" / "fixed.sql").read_text(encoding="utf-8")
        if docker_psql(docker, container, fixed_sql).returncode:
            raise RuntimeError("PostgreSQL fixed fixture setup failed")
        docker_psql(docker, container, "INSERT INTO public.tenant_items(tenant_id,payload) VALUES ('tenant-a','protected-a'),('tenant-b','protected-b');")
        fixed = run([sys.executable, "-I", str(oracle), docker, container])
        fixed_data = parse_json_line(fixed.stdout)
        version = docker_psql(docker, container, "SHOW server_version;").stdout.strip().splitlines()[-1]
        passed = baseline.returncode != 0 and fixed.returncode == 0 and fixed_data.get("passed") is True
        return {
            "status": "PASS" if passed else "FAIL",
            "tool_observed": bool(version),
            "tool_version": f"PostgreSQL {version}",
            "provision_method": "disposable Docker container",
            "image": POSTGRES_IMAGE,
            "image_digest": digest,
            "container_port": 5432,
            "host_port": None,
            "database": "engineering_core_eval",
            "baseline": {"exit_code": baseline.returncode, "oracle": baseline_data},
            "fixed": {"exit_code": fixed.returncode, "oracle": fixed_data},
            "integrity": {"before": integrity_before, "after": "PENDING"},
        }
    finally:
        run([docker, "rm", "-f", container], timeout=60)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run real evaluator-owned stack integrations")
    parser.add_argument("--output", type=Path, default=ROOT / "evidence/current/integrations.json")
    parser.add_argument("--tool-cache", type=Path, default=Path(tempfile.gettempdir()) / "engineering-core-eval-tools")
    parser.add_argument("--browser-executable")
    args = parser.parse_args()

    node = shutil.which("node")
    npm = shutil.which("npm.cmd") or shutil.which("npm")
    docker = shutil.which("docker.exe") or shutil.which("docker")
    if not node or not npm or not docker:
        print("BLOCKED: node, npm, and Docker are required for this environment", file=sys.stderr)
        return 2

    integrity_before = protected_stack_hash(ROOT)
    try:
        typescript, playwright, versions = provision_node_tools(args.tool_cache.resolve(), npm)
        browser = find_browser(args.browser_executable)
        cells = {
            "typescript": typescript_cell(node, typescript, integrity_before),
            "postgresql_rls": postgres_cell(docker, integrity_before),
            "browser": browser_cell(node, playwright, browser, integrity_before),
        }
    except (RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    integrity_after = protected_stack_hash(ROOT)
    for cell in cells.values():
        cell["integrity"]["after"] = integrity_after
    head = run(["git", "rev-parse", "HEAD"]).stdout.strip()
    status = run(["git", "status", "--porcelain"]).stdout.strip()
    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "candidate_commit": head,
        "candidate_worktree_clean": not bool(status),
        "protected_inputs_sha256": integrity_after,
        "environment": {
            "node": command_version([node, "--version"]),
            "npm": command_version([npm, "--version"]),
            "typescript": versions["typescript"],
            "playwright": versions["playwright"],
        },
        "cells": cells,
        "all_integrations_passed": all(cell["status"] == "PASS" for cell in cells.values()) and integrity_before == integrity_after,
    }
    errors = validate_stack_report(report)
    report["validation_errors"] = errors
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"output": str(args.output), "all_integrations_passed": report["all_integrations_passed"], "validation_errors": errors}))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
