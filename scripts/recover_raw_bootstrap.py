"""New-only Raw recovery A. Default preflight; --apply needs Owner authorization."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Any

from check_raw_connection import load_config, read_env_file

ROOT = Path(__file__).resolve().parents[1]
CONTAINER = "retail-raw-postgres-1"
VOLUME = "retail-raw_pg_data"
INSPECT_FORMAT = (
    '{"id":{{json .Id}},"name":{{json .Name}},"image":{{json .Config.Image}},'
    '"running":{{json .State.Running}},"ports":{{json .NetworkSettings.Ports}},'
    '"project":{{json (index .Config.Labels "com.docker.compose.project")}},'
    '"service":{{json (index .Config.Labels "com.docker.compose.service")}},'
    '"mounts":{{json .Mounts}}}'
)
PREFLIGHT_SQL = """BEGIN READ ONLY;
SET LOCAL statement_timeout = '5s';
SELECT json_build_object(
 'database', current_database(), 'user', current_user,
 'raw_exists', to_regnamespace('raw') IS NOT NULL,
 'metadata_exists', to_regnamespace('ingestion_meta') IS NOT NULL,
 'ingest_role_exists', EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'retail_ingest'),
 'custom_schema_count', (SELECT count(*) FROM pg_namespace
     WHERE nspname NOT IN ('public', 'information_schema') AND nspname !~ '^pg_'),
 'user_relation_count', (SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
     WHERE n.nspname <> 'information_schema' AND n.nspname !~ '^pg_'),
 'custom_role_count', (SELECT count(*) FROM pg_roles WHERE rolname <> 'postgres' AND rolname !~ '^pg_')
);
ROLLBACK;
"""


def run_private(args: list[str], *, data: bytes | None = None,
                environment: dict[str, str] | None = None) -> bytes:
    """Never echo command output: psql diagnostics can contain SQL/password text."""
    result = subprocess.run(args, input=data, env=environment, capture_output=True,
                            timeout=60, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"Operation failed (exit {result.returncode}); no private output logged")
    return result.stdout


def inspect_target() -> str:
    target = json.loads(run_private(["docker", "inspect", CONTAINER, "--format", INSPECT_FORMAT]))
    if not isinstance(target, dict):
        raise ValueError("Invalid Docker target metadata")
    if (target.get("name") != "/" + CONTAINER or target.get("image") != "postgres:18"
            or target.get("project") != "retail-raw" or target.get("service") != "postgres"
            or target.get("running") is not True):
        raise ValueError("Unexpected Docker target or Compose ownership")
    if (target.get("ports") or {}).get("5432/tcp") != [{"HostIp": "127.0.0.1", "HostPort": "55434"}]:
        raise ValueError("Unexpected port binding")
    mounts = [mount for mount in target.get("mounts", [])
              if mount.get("Destination") == "/var/lib/postgresql"]
    if len(mounts) != 1 or mounts[0].get("Type") != "volume" or mounts[0].get("Name") != VOLUME:
        raise ValueError("Unexpected Raw volume")
    container_id = target.get("id", "")
    if not re.fullmatch(r"[0-9a-f]{64}", container_id):
        raise ValueError("Invalid container identity")
    return container_id  # Use immutable ID, not a name that could be reassigned.


def psql_args(container_id: str, *, inject_password: bool = False) -> list[str]:
    args = ["docker", "exec", "-i"]
    if inject_password:
        args += ["--env", "RAW_PG_INGEST_PASSWORD"]  # Value comes from child process env, not argv.
    return args + [container_id, "psql", "-X", "-q", "-A", "-t", "--no-password",
                   "--host", "/var/run/postgresql", "--username", "postgres",
                   "--dbname", "retail_raw", "--set", "ON_ERROR_STOP=1", "--file", "-"]


def assert_new_database(evidence: dict[str, Any]) -> None:
    if (evidence.get("database") != "retail_raw" or evidence.get("user") != "postgres"
            or any(evidence.get(key) is not False for key in
                   ("raw_exists", "metadata_exists", "ingest_role_exists"))
            or any(evidence.get(key) != 0 for key in
                   ("custom_schema_count", "user_relation_count", "custom_role_count"))):
        raise ValueError("Existing or unexpected objects/roles: stop and review, never overwrite")


def recover(env_file: Path, *, apply: bool = False) -> dict[str, object]:
    # Explicit private file is the password authority; stale shell/container values do not override it.
    config = load_config(read_env_file(env_file))
    if config.port != 55434:
        raise ValueError("This bounded recovery targets port 55434 only")
    container_id = inspect_target()
    evidence = json.loads(run_private(psql_args(container_id), data=PREFLIGHT_SQL.encode("utf-8")))
    assert_new_database(evidence)
    if not apply:
        return {"status": "READY_FOR_A_NOT_APPLIED", "container": CONTAINER,
                "volume": VOLUME, "database_mutated": False}
    environment = os.environ.copy()
    environment["RAW_PG_INGEST_PASSWORD"] = config.password
    run_private(psql_args(container_id, inject_password=True),
                data=(ROOT / "storage/raw/bootstrap.sql").read_bytes(), environment=environment)
    return {"status": "BOOTSTRAP_APPLIED_VERIFICATION_REQUIRED", "container": CONTAINER,
            "volume": VOLUME, "database_mutated": True}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", required=True, type=Path)
    parser.add_argument("--apply", action="store_true", help="Database mutation; separate Owner approval required")
    args = parser.parse_args()
    try:
        print(json.dumps(recover(args.env_file, apply=args.apply)))
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(json.dumps({"status": "FAIL_STOP_NO_AUTOMATIC_RETRY", "error_type": type(error).__name__,
                          "message": "Check target/private input locally; no command output or secrets logged"}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
