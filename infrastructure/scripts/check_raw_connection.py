"""Validate local Raw settings or perform an explicitly invoked read-only probe."""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import re
from typing import Mapping


@dataclass(frozen=True)
class RawConfig:
    host: str
    port: int
    database: str
    user: str
    password: str = field(repr=False)
    sslmode: str = "disable"


def read_env_file(path: Path) -> dict[str, str]:
    """Read a deliberately small dotenv subset; never execute/interpolate values."""
    values: dict[str, str] = {}
    for number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, separator, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if not separator or not re.fullmatch(r"[A-Z][A-Z0-9_]*", key) or key in values:
            raise ValueError(f"Invalid or duplicate environment key on line {number}")
        if value[:1] in {"'", '"'}:
            if len(value) < 2 or value[-1] != value[0]:
                raise ValueError(f"Unclosed environment value on line {number}")
            value = value[1:-1]
        if key.startswith("RAW_PG_") and any(
            character in value for character in ("\x00", "\r", "\n", "$", "#", "\\")
        ):
            raise ValueError(f"Unsupported dotenv value on line {number}; use simple random secrets")
        values[key] = value
    return values


def load_config(values: Mapping[str, str], *, require_admin: bool = False) -> RawConfig:
    password = values.get("RAW_PG_PASSWORD", "")
    admin_password = values.get("RAW_PG_ADMIN_PASSWORD", "")
    required_secrets = (password, admin_password) if require_admin else (password,)
    for secret in required_secrets:
        if len(secret) < 16 or secret.lower().startswith(("change_me", "your_", "example")):
            raise ValueError("Set distinct private Raw passwords of at least 16 characters")
    if admin_password and password == admin_password:
        raise ValueError("Bootstrap and ingestion passwords must differ")
    host = values.get("RAW_PG_HOST", "127.0.0.1")
    port = int(values.get("RAW_PG_PORT", "55434"))
    database = values.get("RAW_PG_DATABASE", "retail_raw")
    user = values.get("RAW_PG_USER", "retail_ingest")
    sslmode = values.get("RAW_PG_SSLMODE", "disable")
    if host != "127.0.0.1" or not 1024 <= port <= 65535 or port in (5432, 55433):
        raise ValueError("Use isolated IPv4 loopback Raw target; native/B9 ports are excluded")
    if database != "retail_raw" or user != "retail_ingest":
        raise ValueError("This checker targets only retail_raw with the non-admin ingestion role")
    if sslmode not in {"disable", "verify-full"}:
        raise ValueError("Use documented loopback-only disable or explicitly configured verify-full")
    return RawConfig(host, port, database, user, password, sslmode)


def probe(config: RawConfig) -> dict[str, object]:
    """Connect only when explicitly called; never print driver exception text/DSNs."""
    import psycopg  # Existing approved 3.3.9 in the local venv; no auto-install.

    with psycopg.connect(
        host=config.host, port=config.port, dbname=config.database, user=config.user,
        password=config.password, sslmode=config.sslmode, connect_timeout=5,
        options="-c default_transaction_read_only=on -c statement_timeout=5000",
        application_name="retail_raw_readonly_check",
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
            SELECT
                current_database(),
                current_user,
                session_user,
                version(),
                current_setting('server_encoding'),
                (
                    SELECT datcollate
                    FROM pg_database
                    WHERE datname = current_database()
                )
            """)
            database, user, session_user, version, encoding, collation = cursor.fetchone()
            if (database, user, session_user) != (config.database, config.user, config.user):
                raise RuntimeError("Unexpected target identity")
            cursor.execute("SELECT rolsuper, rolcreatedb, rolcreaterole, rolreplication, rolbypassrls "
                           "FROM pg_roles WHERE rolname = current_user")
            roles = cursor.fetchone()
            if roles is None or any(roles):
                raise RuntimeError("Unexpected administrative role")
            cursor.execute("SELECT has_schema_privilege(current_user, 'raw', 'USAGE'), "
                           "has_schema_privilege(current_user, 'raw', 'CREATE')")
            if cursor.fetchone() != (True, False):
                raise RuntimeError("Unexpected Raw schema privileges")
            for table in ("runs", "object_runs"):
                cursor.execute(psycopg.sql.SQL("SELECT 1 FROM ingestion_meta.{} LIMIT 0").format(
                    psycopg.sql.Identifier(table)))
            return {"status": "PASS_READONLY_CONNECTIVITY", "database": database, "user": user,
                    "version": version, "encoding": encoding, "collation": collation,
                    "sslmode": config.sslmode, "full_load_executed": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--check-config", action="store_true", help="Offline only; no connection")
    args = parser.parse_args()
    try:
        values = read_env_file(args.env_file) if args.env_file else {}
        values.update(os.environ)
        config = load_config(values, require_admin=args.check_config)
        result = ({"status": "PASS_CONFIG_ONLY", "host": config.host, "port": config.port,
                   "database": config.database, "user": config.user, "runtime_tested": False}
                  if args.check_config else probe(config))
        print(json.dumps(result))
        return 0
    except (OSError, ValueError, ImportError) as error:
        print(json.dumps({"status": "FAIL", "error_type": type(error).__name__,
                          "message": "Check private configuration/dependencies; no secrets logged"}))
        return 1
    except Exception as error:
        # Preserve a nonzero outcome without leaking driver messages or credentials.
        print(json.dumps({"status": "FAIL", "error_type": type(error).__name__,
                          "message": "Raw probe failed; inspect target and permissions locally"}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
