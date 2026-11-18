"""Offline configuration/bootstrap contracts. Never start Docker or connect to a DB."""
from __future__ import annotations

import ast
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/check_raw_connection.py"
spec = importlib.util.spec_from_file_location("raw_connection_check", SCRIPT)
assert spec and spec.loader
raw = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = raw
spec.loader.exec_module(raw)
recovery_spec = importlib.util.spec_from_file_location("raw_bootstrap_recovery", ROOT / "scripts/recover_raw_bootstrap.py")
assert recovery_spec and recovery_spec.loader
recovery = importlib.util.module_from_spec(recovery_spec)
with patch.dict(sys.modules, {"check_raw_connection": raw}):
    recovery_spec.loader.exec_module(recovery)


def fixture_env() -> dict[str, str]:
    """Synthetic non-runtime secrets, generated in memory only."""
    return {"RAW_PG_PASSWORD": "i" * 24, "RAW_PG_ADMIN_PASSWORD": "a" * 24}


class RawConfigTests(unittest.TestCase):
    def test_valid_isolated_config(self) -> None:
        config = raw.load_config(fixture_env())
        self.assertEqual((config.host, config.port, config.database, config.user),
                         ("127.0.0.1", 55434, "retail_raw", "retail_ingest"))
        self.assertNotIn("i" * 24, repr(config))

    def test_missing_placeholder_or_shared_secrets_rejected(self) -> None:
        for value in ("", "CHANGE_ME_private_password", "example_password_string", "a" * 24):
            with self.subTest(value_kind=len(value)), self.assertRaises(ValueError):
                raw.load_config({**fixture_env(), "RAW_PG_PASSWORD": value})

    def test_native_b9_and_remote_targets_rejected(self) -> None:
        for key, value in (("RAW_PG_PORT", "5432"), ("RAW_PG_PORT", "55433"),
                           ("RAW_PG_HOST", "10.0.0.1"), ("RAW_PG_USER", "postgres"),
                           ("RAW_PG_DATABASE", "b9_precision_poc"), ("RAW_PG_SSLMODE", "prefer")):
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                raw.load_config({**fixture_env(), key: value})

    def test_env_template_complete_and_has_no_credentials(self) -> None:
        values = raw.read_env_file(ROOT / ".env.example")
        self.assertEqual(values["RAW_PG_PASSWORD"], "")
        self.assertEqual(values["RAW_PG_ADMIN_PASSWORD"], "")
        self.assertEqual(values["RAW_PG_PORT"], "55434")
        with self.assertRaises(ValueError):
            raw.load_config(values)

    def test_normal_probe_config_does_not_require_admin_secret(self) -> None:
        values = {"RAW_PG_PASSWORD": "i" * 24}
        self.assertEqual(raw.load_config(values).user, "retail_ingest")
        with self.assertRaises(ValueError):
            raw.load_config(values, require_admin=True)

    def test_dotenv_parser_rejects_duplicate_or_interpolated_raw_settings(self) -> None:
        for text in ("RAW_PG_HOST=x\nRAW_PG_HOST=y", "RAW_PG_PASSWORD=${OTHER}", "not an assignment"):
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "fixture.env"
                path.write_text(text, encoding="utf-8")
                with self.assertRaises(ValueError):
                    raw.read_env_file(path)

    def test_dotenv_preserves_unrelated_source_instance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.env"
            path.write_text("WWI_SQLSERVER_HOST=machine\\instance\nRAW_PG_HOST='127.0.0.1'\n", encoding="utf-8")
            self.assertEqual(raw.read_env_file(path)["WWI_SQLSERVER_HOST"], "machine\\instance")

    def test_check_config_never_calls_probe(self) -> None:
        with patch.dict(os.environ, fixture_env(), clear=True), patch.object(sys, "argv", [str(SCRIPT), "--check-config"]), \
                patch.object(raw, "probe", side_effect=AssertionError("DB access forbidden")), patch("builtins.print") as output:
            self.assertEqual(raw.main(), 0)
            self.assertEqual(json.loads(output.call_args.args[0])["status"], "PASS_CONFIG_ONLY")

    def test_runtime_error_output_omits_driver_message_and_password(self) -> None:
        with patch.dict(os.environ, fixture_env(), clear=True), patch.object(sys, "argv", [str(SCRIPT)]), \
                patch.object(raw, "probe", side_effect=RuntimeError("sensitive-driver-detail")), patch("builtins.print") as output:
            self.assertEqual(raw.main(), 1)
            text = output.call_args.args[0]
            self.assertNotIn("sensitive-driver-detail", text)
            self.assertNotIn("i" * 24, text)

    def test_checker_syntax_and_readonly_transaction(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        ast.parse(source)
        self.assertIn("default_transaction_read_only=on", source)
        self.assertIn("statement_timeout=5000", source)
        self.assertIn("psycopg.sql.Identifier(table)", source)

    def test_probe_checks_identity_and_admin_flags_without_connecting(self) -> None:
        cases = (
            (("retail_raw", "retail_ingest", "retail_ingest"), (False,) * 5, True),
            (("retail_raw", "retail_ingest", "retail_ingest"), (True,) + (False,) * 4, False),
            (("other_database", "retail_ingest", "retail_ingest"), (False,) * 5, False),
        )
        for identity, roles, expected_pass in cases:
            with self.subTest(expected_pass=expected_pass, identity=identity), patch("psycopg.connect") as connect:
                cursor = connect.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value
                cursor.fetchone.side_effect = [(*identity, "fixture-version", "UTF8", "C"), roles, (True, False)]
                config = raw.load_config(fixture_env())
                if expected_pass:
                    self.assertEqual(raw.probe(config)["status"], "PASS_READONLY_CONNECTIVITY")
                    identity_query = cursor.execute.call_args_list[0].args[0]
                    self.assertIn("FROM pg_database", identity_query)
                    self.assertIn("datcollate", identity_query)
                    self.assertNotIn("current_setting('lc_collate')", identity_query)
                else:
                    with self.assertRaises(RuntimeError):
                        raw.probe(config)
                self.assertIn("default_transaction_read_only=on", connect.call_args.kwargs["options"])


class RawBootstrapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sql = (ROOT / "storage/raw/bootstrap.sql").read_text(encoding="utf-8")

    def test_bootstrap_target_role_and_no_destructive_reset(self) -> None:
        for fragment in ("current_database() = 'retail_raw'", "current_user = 'postgres'", "\\set ON_ERROR_STOP on",
                         "\\getenv ingest_password", "PASSWORD %L", "NOSUPERUSER NOCREATEDB NOCREATEROLE",
                         "BEGIN;", "COMMIT;"):
            self.assertIn(fragment, self.sql)
        self.assertNotRegex(self.sql, r"(?im)^\s*(DROP|TRUNCATE|DELETE|ALTER SYSTEM)\b")
        self.assertNotIn("GRANT ALL", self.sql)
        self.assertNotIn("CREATE EXTENSION", self.sql)

    def test_run_identity_and_reconciliation_are_not_fake_publication(self) -> None:
        for fragment in ("run_id uuid PRIMARY KEY", "capture_id uuid NOT NULL", "retry_of_run_id uuid REFERENCES",
                         "DEFAULT 'UNVERIFIED'", "DEFAULT 'NOT_RUN'", "source_row_count IS NOT NULL",
                         "source_row_count = extracted_row_count", "extracted_row_count = loaded_row_count",
                         "status <> 'SUCCEEDED' OR reconciliation_state = 'PASS'", "consistency_evidence_ref"):
            self.assertIn(fragment, self.sql)
        self.assertEqual(self.sql.count("CREATE TABLE "), 2)

    def test_object_allowlist_matches_source_security_package(self) -> None:
        import re
        source = (ROOT / "data-sources/security/wwi_extraction_identity_setup.sql").read_text(encoding="utf-8")
        expected = set(re.findall(r"\(N'(Sales|Warehouse)',\s*N'([^']+)'\)", source))
        actual = re.findall(r"\('(Sales|Warehouse)',\s*'([^']+)'\)", self.sql)
        self.assertEqual(len(actual), 11)
        self.assertEqual(set(actual), expected)

    def test_validation_failure_raises_error_instead_of_successful_quit(self) -> None:
        import re
        prefix = self.sql.split("\nBEGIN;", 1)[0]
        self.assertNotRegex(prefix, r"(?im)^\s*\\(?:quit|q)\b")
        self.assertEqual(len(re.findall(r"RAISE EXCEPTION USING ERRCODE", prefix)), 3)
        self.assertIn("length(:'ingest_password') >= 16", prefix)
        self.assertIn("!~* '^(CHANGE_ME|YOUR_|example)'", prefix)
        self.assertIn("\\set ingest_password ''", prefix)
        self.assertIn("AS new_target \\gset", prefix)
        for block in re.findall(r"DO \$guard\$(.*?)END \$guard\$;", prefix, re.S):
            self.assertNotIn(":'ingest_password'", block)
            self.assertNotIn("%", block)


class RecoveryOfflineTests(unittest.TestCase):
    def ready_database(self) -> dict[str, object]:
        return {"database": "retail_raw", "user": "postgres", "raw_exists": False,
                "metadata_exists": False, "ingest_role_exists": False,
                "custom_schema_count": 0, "user_relation_count": 0, "custom_role_count": 0}

    def target_metadata(self) -> dict[str, object]:
        return {"id": "f" * 64, "name": "/retail-raw-postgres-1", "image": "postgres:18",
                "running": True, "project": "retail-raw", "service": "postgres",
                "ports": {"5432/tcp": [{"HostIp": "127.0.0.1", "HostPort": "55434"}]},
                "mounts": [{"Type": "volume", "Name": "retail-raw_pg_data",
                            "Destination": "/var/lib/postgresql"}]}

    def test_target_rejects_unrelated_name_volume_or_binding(self) -> None:
        cases = ({}, {"name": "/retail-b9-pg-poc"}, {"ports": None}, {"project": "other"},
                 {"mounts": [{"Type": "volume", "Name": "unrelated", "Destination": "/var/lib/postgresql"}]})
        for changes in cases:
            target = {**self.target_metadata(), **changes}
            with patch.object(recovery, "run_private", return_value=json.dumps(target).encode()):
                if changes:
                    with self.assertRaises(ValueError):
                        recovery.inspect_target()
                else:
                    self.assertEqual(recovery.inspect_target(), "f" * 64)

    def test_existing_objects_roles_or_unknown_evidence_block_recovery(self) -> None:
        recovery.assert_new_database(self.ready_database())
        for changes in ({"raw_exists": True}, {"ingest_role_exists": True}, {"user_relation_count": 1},
                        {"custom_role_count": 1}, {"database": "other"}, {"metadata_exists": None}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                recovery.assert_new_database({**self.ready_database(), **changes})

    def test_default_is_preflight_only(self) -> None:
        with patch.object(recovery, "read_env_file", return_value=fixture_env()), \
                patch.object(recovery, "inspect_target", return_value="f" * 64), \
                patch.object(recovery, "run_private", return_value=json.dumps(self.ready_database()).encode()) as execute:
            result = recovery.recover(Path("not-read.env"))
            self.assertFalse(result["database_mutated"])
            self.assertEqual(execute.call_count, 1)
            self.assertIn(b"BEGIN READ ONLY", execute.call_args.kwargs["data"])

    def test_apply_uses_private_child_env_not_password_argv(self) -> None:
        with patch.object(recovery, "read_env_file", return_value=fixture_env()), \
                patch.object(recovery, "inspect_target", return_value="f" * 64), \
                patch.object(recovery, "run_private", side_effect=[json.dumps(self.ready_database()).encode(), b""]) as execute:
            result = recovery.recover(Path("not-read.env"), apply=True)
            self.assertEqual(result["status"], "BOOTSTRAP_APPLIED_VERIFICATION_REQUIRED")
            args = execute.call_args.args[0]
            self.assertNotIn("i" * 24, " ".join(args))
            self.assertIn("f" * 64, args)
            self.assertIn("RAW_PG_INGEST_PASSWORD", args)
            self.assertEqual(execute.call_args.kwargs["environment"]["RAW_PG_INGEST_PASSWORD"], "i" * 24)

    def test_short_password_blocks_before_any_docker_call(self) -> None:
        with patch.object(recovery, "read_env_file", return_value={"RAW_PG_PASSWORD": "short"}), \
                patch.object(recovery, "inspect_target") as inspect:
            with self.assertRaises(ValueError):
                recovery.recover(Path("not-read.env"), apply=True)
            inspect.assert_not_called()

    def test_nonzero_exit_is_not_swallowed_or_logged_with_private_output(self) -> None:
        result = subprocess.CompletedProcess(["fixture"], 3, b"private-output", b"private-output")
        with patch.object(recovery.subprocess, "run", return_value=result), \
                self.assertRaises(RuntimeError) as caught:
            recovery.run_private(["fixture"])
        self.assertIn("exit 3", str(caught.exception))
        self.assertNotIn("private-output", str(caught.exception))


class ComposeOfflineTests(unittest.TestCase):
    def test_real_compose_parser_and_resource_isolation(self) -> None:
        docker = shutil.which("docker")
        if not docker:
            self.skipTest("Docker CLI unavailable; Compose runtime NOT RUN")
        environment = {key: value for key, value in os.environ.items() if not key.startswith("RAW_PG_")}
        environment.update(fixture_env())
        result = subprocess.run(
            [docker, "compose", "-p", "retail-raw", "--env-file", str(ROOT / ".env.example"), "-f",
             str(ROOT / "infrastructure/docker/compose.raw.yaml"), "config", "--format", "json"],
            env=environment, capture_output=True, text=True, timeout=20, check=False,
        )
        self.assertEqual(result.returncode, 0, "Compose offline parser failed; no services started")
        config = json.loads(result.stdout)
        service = config["services"]["postgres"]
        self.assertEqual(config["name"], "retail-raw")
        self.assertEqual(service["image"], "postgres:18")
        self.assertEqual(len(service["ports"]), 1)
        self.assertEqual((service["ports"][0]["host_ip"], str(service["ports"][0]["published"])),
                         ("127.0.0.1", "55434"))
        mounts = {item["target"]: item for item in service["volumes"]}
        self.assertEqual(mounts["/var/lib/postgresql"]["type"], "volume")
        self.assertTrue(mounts["/docker-entrypoint-initdb.d/010-retail-raw.sql"]["read_only"])
        self.assertIn("pg_isready", " ".join(service["healthcheck"]["test"]))
        for fragment in ("psql -X", "ON_ERROR_STOP=1", "to_regclass('ingestion_meta.runs')",
                         "to_regclass('ingestion_meta.object_runs')", "rolname = 'retail_ingest'", ")\" = t"):
            self.assertIn(fragment, service["healthcheck"]["test"][1])
        self.assertEqual(service["restart"], "no")


if __name__ == "__main__":
    unittest.main()
