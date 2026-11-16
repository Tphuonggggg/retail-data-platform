"""Offline text-contract checks only. Never connect to or execute SQL Server."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SETUP_PATH = ROOT / "data-sources/security/wwi_extraction_identity_setup.sql"
VERIFY_PATH = ROOT / "data-sources/security/wwi_extraction_identity_verify.sql"
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
        for name in ("WindowsPrincipal", "DatabaseUser"):
            if not re.search(r"@" + name + r"\s+nvarchar\(256\)\s*=\s*N'<APPROVED_", clean, re.I):
                errors.append(label + ": identity placeholder " + name)
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
    if re.search(r"(?i)GRANT\s+(?:ALL|CONTROL|INSERT|UPDATE|DELETE|VIEW|EXECUTE)|ALTER\s+ROLE|sp_addrolemember", without_comments(setup)):
        errors.append("setup: grant outside CONNECT/object SELECT package")
    if re.search(r"(?i)\b(?:INSERT|UPDATE|DELETE|MERGE|CREATE|ALTER|DROP|GRANT|REVOKE|DENY|EXEC|EXECUTE|BACKUP|RESTORE|TRUNCATE)\b", code_only(verify)):
        errors.append("verify: non-SELECT executable statement")
    probes = re.findall(r"(?is)SELECT TOP \(1\).*?FROM \[([^]]+)\]\.\[([^]]+)\];", without_comments(verify))
    if len(probes) != 11 or set(probes) != EXPECTED:
        errors.append("verify: bounded physical-population probes")
    if "EVIDENCE_ONLY_NOT_G01_G02_PASS" not in verify:
        errors.append("verify: false gate-acceptance risk")
    return errors


class PreparedSourceSecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.setup = SETUP_PATH.read_text(encoding="utf-8-sig")
        cls.verify = VERIFY_PATH.read_text(encoding="utf-8-sig")

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
        self.assertTrue(findings(self.setup.replace("(N'Sales', N'Customers_Archive'),", ""), self.verify))

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


if __name__ == "__main__":
    unittest.main()
