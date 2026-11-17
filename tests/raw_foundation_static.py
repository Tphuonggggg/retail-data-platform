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
        self.assertEqual(service["restart"], "no")


if __name__ == "__main__":
    unittest.main()
