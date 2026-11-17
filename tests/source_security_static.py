"""Offline text-contract checks only. Never connect to or execute SQL Server."""
from __future__ import annotations

import re
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SETUP_PATH = ROOT / "data-sources/security/wwi_extraction_identity_setup.sql"
VERIFY_PATH = ROOT / "data-sources/security/wwi_extraction_identity_verify.sql"
MANIFEST_PATH = ROOT / "data-sources/security/wwi_extraction_execution_manifest.json"
WINDOWS_PRINCIPAL = r"DESKTOP-OBDFK6B\wwi_extract"
DATABASE_USER = "wwi_extract"
WINDOWS_SID_HEX = "0x0105000000000005150000003CF5FF806E0A76B5BDAC3020EF030000"
OPERATOR_PRINCIPAL = r"DESKTOP-OBDFK6B\PC"
OPERATOR_SID_HEX = "0x0105000000000005150000003CF5FF806E0A76B5BDAC3020E9030000"
NEGATIVE_DATABASE = "Retail_EX02_DeniedAccess_20261117"
PACKAGE_ID = "WWI05-EX02-20261117-01"
EXPECTED = {
    ("Sales", "Customers"), ("Sales", "Orders"), ("Sales", "OrderLines"),
    ("Sales", "Invoices"), ("Sales", "InvoiceLines"), ("Sales", "CustomerTransactions"),
    ("Warehouse", "StockItems"), ("Warehouse", "StockItemHoldings"),
    ("Warehouse", "StockItemTransactions"), ("Sales", "Customers_Archive"),
    ("Warehouse", "StockItems_Archive"),
}
SETUP_GUARDS = (
    "DbaReviewed", "OwnerExecutionAuthorized", "WindowsAccountProvisioned",
    "WindowsNonAdminAttested",
)
VERIFY_GUARDS = (
    "VerificationAuthorized", "DbaWindowsGroupReviewComplete",
    "ClientTlsProofReviewed", "NegativeDatabaseExistsAttested",
)


def without_comments(text: str) -> str:
    """Remove comments while preserving SQL string literals and escaped quotes."""
    token = re.compile(r"N?'(?:''|[^'])*'|--[^\n]*|/\*[\s\S]*?\*/", re.IGNORECASE)
    return token.sub(lambda m: "" if m.group().startswith(("--", "/*")) else m.group(), text)


def code_only(text: str) -> str:
    return re.sub(r"N?'(?:''|[^'])*'", "''", without_comments(text), flags=re.IGNORECASE)


def findings(setup: str, verify: str) -> list[str]:
    """Detect selected dangerous regressions; this is NOT a T-SQL parser/proof."""
    errors: list[str] = []
    for label, text, guards, stop in (
        ("setup", setup, SETUP_GUARDS, "51100"),
        ("verify", verify, VERIFY_GUARDS, "51200"),
    ):
        if "DBA REVIEW REQUIRED" not in text or "DO NOT AUTO-EXECUTE" not in text:
            errors.append(label + ": review warning")
        clean = without_comments(text)
        code = code_only(text)
        if re.search(r"(?im)^\s*GO(?:\s|$)|^\s*:", code):
            errors.append(label + ": batch/sqlcmd directive")
        for guard in guards:
            if not re.search(r"DECLARE\s+@" + guard + r"\s+bit\s*=\s*0\s*;", clean, re.I):
                errors.append(label + ": disabled-by-default " + guard)
            if not re.search(r"COALESCE\(@" + guard + r",\s*0\)\s*<>\s*1", clean, re.I):
                errors.append(label + ": positive confirmation " + guard)
        if not re.search(r"THROW\s+" + stop, code, re.I):
            errors.append(label + ": fail-closed stop")
        for name, value in (("WindowsPrincipal", WINDOWS_PRINCIPAL), ("DatabaseUser", DATABASE_USER)):
            if not re.search(r"DECLARE\s+@" + name + r"\s+nvarchar\(256\)\s*=\s*N'" + re.escape(value) + r"';", clean, re.I):
                errors.append(label + ": populated identity " + name)
        if "<APPROVED_" in text:
            errors.append(label + ": unresolved placeholder")
        if not re.search(r"@ExpectedWindowsSid\s+varbinary\(85\)\s*=\s*" + WINDOWS_SID_HEX + r";", clean, re.I):
            errors.append(label + ": pinned Windows SID")
        reference_name = "ChangeReference" if label == "setup" else "VerificationReference"
        reference = PACKAGE_ID if label == "setup" else PACKAGE_ID + "-VERIFY"
        if not re.search(r"@" + reference_name + r"\s+nvarchar\(256\)\s*=\s*N'" + reference + r"';", clean, re.I):
            errors.append(label + ": concrete reference")
        pairs = re.findall(r"\(N'(Sales|Warehouse)',\s*N'([^']+)'\)", clean)
        if len(pairs) != 11 or set(pairs) != EXPECTED:
            errors.append(label + ": eleven-object allowlist")
        if re.search(r"(?i)trustservercertificate\s*=\s*(yes|true)|encrypt\s*=\s*no", text):
            errors.append(label + ": insecure TLS literal")
    setup_code = code_only(setup)
    if setup_code.find("THROW 51100") > setup_code.find("EXEC sys.sp_executesql"):
        errors.append("setup: execution before authority guard")
    for name in ("WindowsPrincipal", "DatabaseUser"):
        if "QUOTENAME(@" + name + ")" not in setup:
            errors.append("setup: unquoted identifier " + name)
    for expected in ("BEGIN TRANSACTION", "COMMIT TRANSACTION", "ROLLBACK TRANSACTION", "XACT_STATE()"):
        if expected not in setup_code:
            errors.append("setup: failure cleanup " + expected)
    connect_batch = (
        r"DECLARE\s+@ConnectSql\s+nvarchar\(max\)\s*=\s*"
        r"N'USE \[master\]; GRANT CONNECT SQL TO '\s*\+\s*@LoginQuoted\s*"
        r"\+\s*N'; USE \[WideWorldImporters\]; GRANT CONNECT TO '\s*"
        r"\+\s*@UserQuoted\s*\+\s*N';';"
    )
    if not re.search(connect_batch, without_comments(setup), re.I):
        errors.append("setup: server/database CONNECT grant contexts")
    setup_clean = without_comments(setup)
    if re.search(r"(?i)GRANT\s+(?:ALL|CONTROL|INSERT|UPDATE|DELETE|VIEW|EXECUTE)|ALTER\s+(?:SERVER\s+)?ROLE|sp_add(?:srv)?rolemember", setup_clean):
        errors.append("setup: grant outside CONNECT/object SELECT package")
    if len(re.findall(r"(?i)\bGRANT\s+SELECT\b", setup_clean)) != 1 or "N'GRANT SELECT ON OBJECT::'" not in setup_clean:
        errors.append("setup: only allowlist-generated object SELECT")
    if len(re.findall(r"(?i)\bGRANT\s+CONNECT\b", setup_clean)) != 2:
        errors.append("setup: only two CONNECT grants")
    if ("N'" + OPERATOR_PRINCIPAL + "';" not in setup_clean
            or OPERATOR_SID_HEX not in setup_clean
            or "ORIGINAL_LOGIN() <> @ExecutionOperator" not in setup_clean
            or "SUSER_SNAME() <> @ExecutionOperator" not in setup_clean
            or "OR SUSER_SID() <> @ExpectedOperatorSid" not in setup_clean):
        errors.append("setup: pinned real execution operator")
    if setup_clean.count("AND sid = @ExpectedWindowsSid") != 2 or setup_clean.count("OR sid = @ExpectedWindowsSid") != 2:
        errors.append("setup: SID mapping and collision checks")
    verify_clean = without_comments(verify)
    if ("OR SUSER_SID() <> @ExpectedWindowsSid" not in verify_clean
            or "AND sid = @ExpectedWindowsSid" not in verify_clean):
        errors.append("verify: SID mapping checks")
    if "@NegativeDatabase nvarchar(256) = N'" + NEGATIVE_DATABASE + "';" not in verify_clean:
        errors.append("verify: exact negative database")
    if "COALESCE(IS_ROLEMEMBER(N'db_datareader'), 1) <> 0" not in verify_clean:
        errors.append("verify: broad reader role rejected")
    if re.search(r"(?i)\b(?:INSERT|UPDATE|DELETE|MERGE|CREATE|ALTER|DROP|GRANT|REVOKE|DENY|EXEC|EXECUTE|BACKUP|RESTORE|TRUNCATE)\b", code_only(verify)):
        errors.append("verify: non-SELECT executable statement")
    probes = re.findall(r"(?is)SELECT TOP \(1\).*?FROM \[([^]]+)\]\.\[([^]]+)\];", without_comments(verify))
    if len(probes) != 11 or set(probes) != EXPECTED:
        errors.append("verify: bounded physical-population probes")
    if "EVIDENCE_ONLY_NOT_G01_G02_PASS" not in verify:
        errors.append("verify: false gate-acceptance risk")
    return errors


def activation_edits(guards: tuple[str, ...], confirmation: str) -> list[dict[str, str]]:
    """Describe the ONLY future activation edits; never write or execute a payload."""
    edits = [{"from": f"DECLARE @{name} bit = 0;", "to": f"DECLARE @{name} bit = 1;"} for name in guards]
    variable = "ExecutionConfirmation" if guards == SETUP_GUARDS else "VerificationConfirmation"
    edits.append({"from": f"DECLARE @{variable} nvarchar(80) = N'DO_NOT_EXECUTE';",
                  "to": f"DECLARE @{variable} nvarchar(80) = N'{confirmation}';"})
    return edits


def activated_text(text: str, edits: list[dict[str, str]]) -> str:
    """Derive bytes in memory for review hashes, without database or file actions."""
    for edit in edits:
        if text.count(edit["from"]) != 1:
            raise ValueError("Activation edit must match exactly once")
        text = text.replace(edit["from"], edit["to"], 1)
    return text


class PreparedSourceSecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.setup = SETUP_PATH.read_text(encoding="utf-8-sig")
        cls.verify = VERIFY_PATH.read_text(encoding="utf-8-sig")
        cls.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    def test_reviewed_package_static_contract(self) -> None:
        self.assertEqual(findings(self.setup, self.verify), [])

    def test_setup_guard_mutations_rejected(self) -> None:
        for flag in SETUP_GUARDS:
            with self.subTest(flag=flag):
                changed = self.setup.replace("@" + flag + " bit = 0", "@" + flag + " bit = 1")
                self.assertTrue(findings(changed, self.verify))

    def test_verify_guard_mutations_rejected(self) -> None:
        for flag in VERIFY_GUARDS:
            with self.subTest(flag=flag):
                changed = self.verify.replace("@" + flag + " bit = 0", "@" + flag + " bit = 1")
                self.assertTrue(findings(self.setup, changed))

    def test_missing_owner_confirmation_rejected(self) -> None:
        self.assertTrue(findings(self.setup.replace("COALESCE(@OwnerExecutionAuthorized, 0) <> 1", "1 = 1"), self.verify))

    def test_missing_archive_rejected(self) -> None:
        for schema, table in (("Sales", "Customers_Archive"), ("Warehouse", "StockItems_Archive")):
            with self.subTest(table=table):
                self.assertTrue(findings(self.setup.replace(f"(N'{schema}', N'{table}')", ""), self.verify))

    def test_extra_object_rejected(self) -> None:
        changed = self.setup.replace("(N'Sales', N'Customers'),", "(N'Sales', N'Customers'),\n(N'Sales', N'Unapproved'),")
        self.assertTrue(findings(changed, self.verify))

    def test_batch_separator_rejected(self) -> None:
        self.assertTrue(findings(self.setup + "\nGO\n", self.verify))

    def test_unquoted_identifier_rejected(self) -> None:
        self.assertTrue(findings(self.setup.replace("QUOTENAME(@WindowsPrincipal)", "@WindowsPrincipal"), self.verify))

    def test_broad_grant_rejected(self) -> None:
        self.assertTrue(findings(self.setup + "\nGRANT CONTROL TO [example];", self.verify))

    def test_mutating_verification_rejected(self) -> None:
        self.assertTrue(findings(self.setup, self.verify + "\nDELETE FROM [Sales].[Orders];"))

    def test_gate_pass_marker_required(self) -> None:
        self.assertTrue(findings(self.setup, self.verify.replace("EVIDENCE_ONLY_NOT_G01_G02_PASS", "SUCCESS")))

    def test_read_only_diagnostic_rights_not_granted(self) -> None:
        self.assertNotRegex(without_comments(self.setup), r"(?i)GRANT\s+VIEW\s+SERVER")

    def test_connect_grant_context_mutations_rejected(self) -> None:
        for old, new in (
            ("USE [master]; GRANT CONNECT SQL", "GRANT CONNECT SQL"),
            ("USE [master]; GRANT CONNECT SQL", "USE [WideWorldImporters]; GRANT CONNECT SQL"),
            ("USE [WideWorldImporters]; GRANT CONNECT TO", "GRANT CONNECT TO"),
            ("USE [WideWorldImporters]; GRANT CONNECT TO", "USE [master]; GRANT CONNECT TO"),
        ):
            with self.subTest(replacement=new):
                self.assertIn(old, self.setup)
                self.assertIn("setup: server/database CONNECT grant contexts",
                              findings(self.setup.replace(old, new), self.verify))

    def test_populated_values_and_sid_mutations_rejected(self) -> None:
        for old in (WINDOWS_PRINCIPAL, WINDOWS_SID_HEX, OPERATOR_PRINCIPAL, OPERATOR_SID_HEX):
            with self.subTest(value=old):
                self.assertIn(old, self.setup)
                self.assertTrue(findings(self.setup.replace(old, "WRONG_VALUE"), self.verify))
        self.assertTrue(findings(self.setup, self.verify.replace(WINDOWS_SID_HEX, "0x00")))
        self.assertTrue(findings(self.setup, self.verify.replace(NEGATIVE_DATABASE, "master")))

    def test_missing_sid_operator_checks_rejected(self) -> None:
        for old in ("OR SUSER_SID() <> @ExpectedOperatorSid", "AND sid = @ExpectedWindowsSid"):
            self.assertTrue(findings(self.setup.replace(old, ""), self.verify))
        self.assertTrue(findings(self.setup, self.verify.replace("OR SUSER_SID() <> @ExpectedWindowsSid", "")))

    def test_extra_select_and_role_grants_rejected(self) -> None:
        for extra in ("GRANT SELECT ON SCHEMA::Sales TO [wwi_extract];",
                      "GRANT SELECT ON OBJECT::Sales.Unapproved TO [wwi_extract];",
                      "GRANT CONNECT ANY DATABASE TO [wwi_extract];",
                      "ALTER SERVER ROLE [sysadmin] ADD MEMBER [wwi_extract];"):
            with self.subTest(statement=extra):
                self.assertTrue(findings(self.setup + "\n" + extra, self.verify))

    def test_manifest_hashes_and_exact_activation_recipe(self) -> None:
        for key, path, text, guards, confirmation in (
            ("setup", SETUP_PATH, self.setup, SETUP_GUARDS, "EXECUTE_APPROVED_WWI_IDENTITY_SETUP"),
            ("verify", VERIFY_PATH, self.verify, VERIFY_GUARDS, "EXECUTE_APPROVED_READ_ONLY_VERIFICATION"),
        ):
            with self.subTest(artifact=key):
                artifact = self.manifest["artifacts"][key]
                edits = activation_edits(guards, confirmation)
                self.assertEqual(artifact["path"], path.relative_to(ROOT).as_posix())
                self.assertEqual(artifact["activation_edits"], edits)
                self.assertEqual(artifact["guarded_sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
                self.assertEqual(artifact["activated_sha256"], hashlib.sha256(activated_text(text, edits).encode("utf-8")).hexdigest())
                self.assertNotEqual(artifact["guarded_sha256"], artifact["activated_sha256"])
                self.assertTrue(findings(activated_text(self.setup, activation_edits(SETUP_GUARDS, "EXECUTE_APPROVED_WWI_IDENTITY_SETUP")), self.verify))

    def test_manifest_identity_scope_and_pending_authority(self) -> None:
        m = self.manifest
        self.assertEqual(m["package_id"], PACKAGE_ID)
        self.assertEqual(m["status"], "PENDING_EXECUTION_AUTHORIZATION")
        self.assertEqual(m["extractor"]["windows_principal"], WINDOWS_PRINCIPAL)
        self.assertEqual(m["extractor"]["sid_hex"], WINDOWS_SID_HEX)
        self.assertEqual(m["extractor"]["database_user"], DATABASE_USER)
        self.assertEqual({tuple(p) for p in m["select_allowlist"]}, EXPECTED)
        self.assertEqual(len(m["select_allowlist"]), 11)
        self.assertEqual(m["proposed_operator"]["windows_principal"], OPERATOR_PRINCIPAL)
        self.assertEqual(m["negative_database"]["name"], NEGATIVE_DATABASE)
        self.assertFalse(m["setup_executed"])
        self.assertFalse(m["verification_executed"])
        self.assertNotRegex(json.dumps(m), r"<APPROVED_[^>]*>")


if __name__ == "__main__":
    unittest.main()
