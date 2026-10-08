from __future__ import annotations

import json
import subprocess
import sys


def psql(docker: str, container: str, sql: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [docker, "exec", "-i", container, "psql", "-X", "-A", "-t", "-v", "ON_ERROR_STOP=1", "-U", "postgres", "-d", "engineering_core_eval"],
        input=sql,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )


def scalar(docker: str, container: str, sql: str) -> tuple[int, str]:
    result = psql(docker, container, sql)
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return result.returncode, lines[-1] if lines else ""


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: postgres_oracle.py <docker> <container>", file=sys.stderr)
        return 2
    docker, container = sys.argv[1:]
    checks: dict[str, object] = {}

    code, value = scalar(docker, container, "SET ROLE tenant_a; SET app.tenant_id='tenant-a'; SELECT count(*) FROM public.tenant_items WHERE tenant_id='tenant-a';")
    checks["tenant_a_reads_own"] = code == 0 and value.endswith("1")

    own_write = psql(docker, container, "SET ROLE tenant_a; SET app.tenant_id='tenant-a'; INSERT INTO public.tenant_items(tenant_id,payload) VALUES ('tenant-a','allowed-write');")
    checks["tenant_a_writes_own"] = own_write.returncode == 0

    code, value = scalar(docker, container, "SET ROLE tenant_b; SET app.tenant_id='tenant-b'; SELECT count(*) FROM public.tenant_items WHERE tenant_id='tenant-a';")
    checks["tenant_b_cannot_read_a"] = code == 0 and value.endswith("0")

    bad_write = psql(docker, container, "SET ROLE tenant_b; SET app.tenant_id='tenant-b'; INSERT INTO public.tenant_items(tenant_id,payload) VALUES ('tenant-a','forbidden-write');")
    checks["tenant_b_cannot_write_a"] = bad_write.returncode != 0 and "row-level security" in bad_write.stderr.lower()

    code, value = scalar(docker, container, "SELECT relrowsecurity::text || ':' || relforcerowsecurity::text FROM pg_class WHERE oid='public.tenant_items'::regclass;")
    checks["rls_enabled_and_forced"] = code == 0 and value.endswith("true:true")

    code, value = scalar(docker, container, "SELECT count(*) FROM pg_policies WHERE schemaname='public' AND tablename='tenant_items' AND policyname='tenant_isolation' AND roles @> ARRAY['tenant_a','tenant_b']::name[] AND cmd='ALL' AND qual IS NOT NULL AND with_check IS NOT NULL;")
    checks["policy_complete"] = code == 0 and value.endswith("1")

    code, value = scalar(docker, container, "SELECT count(*) FROM information_schema.role_table_grants WHERE table_schema='public' AND table_name='tenant_items' AND grantee='PUBLIC';")
    checks["public_grants_absent"] = code == 0 and value.endswith("0")

    code, value = scalar(docker, container, "SET ROLE app_owner; SELECT count(*) FROM public.tenant_items;")
    checks["owner_subject_to_force_rls"] = code == 0 and value.endswith("0")

    code, value = scalar(docker, container, "SET ROLE service_role; SELECT count(*) FROM public.tenant_items;")
    checks["authorized_service_reads_all"] = code == 0 and value.isdigit() and int(value) >= 3

    service_write = psql(docker, container, "SET ROLE service_role; INSERT INTO public.tenant_items(tenant_id,payload) VALUES ('tenant-b','authorized-service-write');")
    checks["authorized_service_writes"] = service_write.returncode == 0

    passed = all(checks.values())
    print(json.dumps({"passed": passed, "checks": checks}, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
