"""Offline ACL package contracts; no ACL writes or operator-script execution."""
from __future__ import annotations

import copy
import hashlib
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "data-sources/security/staging"
PC = "S-1-5-21-2164258108-3044412014-540060861-1001"
PARENT = r"D:\Code\Retail_Data_Platform"
EXPECTED_PATHS = {
    "ancestor": r"D:\Code",
    "parent": PARENT,
    "repository": PARENT + r"\project1_Retail_Data_platform",
    "staging": PARENT + r"\Retail_EX02_Protected_Staging",
    "backup_file": r"C:\ProgramData\RetailDataPlatform\AclBackups\WWI05-EX02-S1-20261117.json",
}
TRUSTED = {"SY", "BA", PC}


def aces(sddl: str) -> list[tuple[str, ...]]:
    return [tuple(part.split(";")) for part in re.findall(r"\(([^()]*)\)", sddl)]


def contract_findings(plan: dict, sources: dict[str, str]) -> list[str]:
    """Selected regressions only; not an effective-access or race-safety proof."""
    errors: list[str] = []
    if plan["paths"] != EXPECTED_PATHS or plan["operator_sid"] != PC:
        errors.append("path/SID allowlist")
    for key in ("parent_acl_change_approved", "repository_inheritance_preservation_verified",
                "acl_changes_executed", "staging_created", "activated_sql_copied"):
        if plan.get(key) is not False:
            errors.append("disabled preparation state: " + key)
    stage = plan["target_staging_sddl"]
    stage_aces = aces(stage)
    if (not stage.startswith("O:BAG:BAD:P") or len(stage_aces) != 3
            or {a[5] for a in stage_aces} != TRUSTED
            or any(a[:5] != ("A", "OICI", "FA", "", "") for a in stage_aces)):
        errors.append("staging protected trusted-only DACL")
    parent_aces = aces(plan["target_parent_sddl"])
    self_aces = [a for a in parent_aces if "IO" not in a[1]]
    streams = [a for a in parent_aces if "IO" in a[1]]
    legacy = [a for a in aces(next(e["SDDL"] for e in plan["before"]
                                  if e["Path"] == PARENT)) if "IO" in a[1]]
    # Compare masks/SIDs semantically (the plan uses full SID/numeric masks).
    aliases = {"BA": "S-1-5-32-544", "SY": "S-1-5-18",
               "AU": "S-1-5-11", "BU": "S-1-5-32-545"}
    rights = {"GA": "0x10000000", "SDGXGWGR": "0xe0010000", "GXGR": "0xa0000000"}
    expected_streams = [(aliases.get(a[5], a[5]), rights.get(a[2], a[2])) for a in legacy]
    if (len(self_aces) != 3 or {a[5] for a in self_aces} != TRUSTED
            or any(a[:5] != ("A", "", "FA", "", "") for a in self_aces)
            or len(streams) != 4 or [(a[5], a[2]) for a in streams] != expected_streams
            or any(a[0] != "A" or a[1] != "OICIIO" for a in streams)
            or "D:P" not in plan["target_parent_sddl"]):
        errors.append("parent self-only/legacy inheritance policy")
    common = sources["acl-common.ps1"]
    for guard in ("Assert-S1Context", "WindowsBuiltInRole]::Administrator", "DESKTOP-OBDFK6B",
                  PC, "VolumeSerialNumber", "'NTFS'", "Assert-S1NoReparse",
                  "Assert-S1AncestorsSafe", "Assert-S1TrustedDirectory", "Assert-S1MutationReady",
                  "repository_inheritance_preservation_verified", "parent_acl_change_approved",
                  "before-state path allowlist mismatch", "independently", "-band 8"):
        if guard not in common:
            errors.append("missing guard: " + guard)
    for name in ("02-create-protected-staging.ps1", "04-restore-parent-acl.ps1"):
        src = sources[name]
        if ("[switch]$OwnerAuthorized" not in src
                or "Assert-S1MutationReady $plan $OwnerAuthorized.IsPresent $PSScriptRoot" not in src
                or src.find("Assert-S1MutationReady") > src.find("Set-Acl")):
            errors.append("mutation before explicit prerequisites: " + name)
    joined = "\n".join(sources.values())
    if re.search(r"(?im)^\s*(?:Remove-Item|Move-Item|Copy-Item|Invoke-Expression|Start-Process|icacls|sqlcmd)\b|\s-Recurse\b", joined):
        errors.append("unexpected destructive/recursive/copy/execution command")
    for name, src in sources.items():
        # Enumerate every Set-Acl target, not just the expected count.
        for line in src.splitlines():
            if re.match(r"\s*Set-Acl\b", line) and not re.match(
                    r"\s*Set-Acl -LiteralPath \$plan\.paths\.parent -AclObject \$(?:parentAcl|restoreAcl) -ErrorAction Stop$", line):
                errors.append("unexpected ACL mutation target: " + name)
    verify = sources["03-verify-acl.ps1"]
    if re.search(r"(?im)^\s*Set-Acl\b|::CreateDirectory|\[IO.File\]::Open", verify):
        errors.append("verification mutation")
    return errors


class StagingAclStaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.plan = json.loads((PACKAGE / "acl-plan.json").read_text(encoding="utf-8"))
        cls.sources = {p.name: p.read_text(encoding="utf-8") for p in PACKAGE.glob("*.ps1")}

    def test_prepared_package_contract(self) -> None:
        self.assertEqual(contract_findings(self.plan, self.sources), [])

    def test_sql_manifest_unchanged(self) -> None:
        manifest = ROOT / self.plan["source_manifest"]["path"]
        self.assertEqual(hashlib.sha256(manifest.read_bytes()).hexdigest(),
                         self.plan["source_manifest"]["sha256"])

    def test_exact_four_before_paths(self) -> None:
        self.assertEqual(len(self.plan["before"]), 4)
        self.assertEqual({e["Path"] for e in self.plan["before"]},
                         {"D:\\", EXPECTED_PATHS["ancestor"], PARENT, EXPECTED_PATHS["repository"]})

    def test_wrong_path_rejected(self) -> None:
        plan = copy.deepcopy(self.plan)
        plan["paths"]["staging"] = r"D:\Other"
        self.assertIn("path/SID allowlist", contract_findings(plan, self.sources))

    def test_extractor_write_rejected(self) -> None:
        plan = copy.deepcopy(self.plan)
        plan["target_staging_sddl"] += "(A;OICI;FA;;;S-1-5-21-2164258108-3044412014-540060861-1007)"
        self.assertIn("staging protected trusted-only DACL", contract_findings(plan, self.sources))

    def test_broad_stage_write_rejected(self) -> None:
        plan = copy.deepcopy(self.plan)
        plan["target_staging_sddl"] += "(A;OICI;FA;;;AU)"
        self.assertIn("staging protected trusted-only DACL", contract_findings(plan, self.sources))

    def test_missing_child_inheritance_stream_rejected(self) -> None:
        plan = copy.deepcopy(self.plan)
        plan["target_parent_sddl"] = re.sub(r"\(A;OICIIO;0xe0010000;;;S-1-5-11\)", "", plan["target_parent_sddl"])
        self.assertIn("parent self-only/legacy inheritance policy", contract_findings(plan, self.sources))

    def test_propagating_self_pc_grant_rejected(self) -> None:
        plan = copy.deepcopy(self.plan)
        plan["target_parent_sddl"] = plan["target_parent_sddl"].replace("(A;;FA;;;" + PC, "(A;OICI;FA;;;" + PC)
        self.assertIn("parent self-only/legacy inheritance policy", contract_findings(plan, self.sources))

    def test_disabled_approval_is_not_runtime_pass(self) -> None:
        plan = copy.deepcopy(self.plan)
        plan["parent_acl_change_approved"] = True
        self.assertTrue(any("disabled preparation state" in e for e in contract_findings(plan, self.sources)))
        self.assertEqual(self.plan["runtime_acl_status"], "NOT_RUN")
        self.assertEqual(self.plan["sql_runtime_status"], "NOT_RUN")

    def test_mutation_gate_removal_rejected(self) -> None:
        sources = dict(self.sources)
        sources["02-create-protected-staging.ps1"] = sources["02-create-protected-staging.ps1"].replace(
            "Assert-S1MutationReady $plan $OwnerAuthorized.IsPresent $PSScriptRoot", "# removed")
        self.assertTrue(any("mutation before" in e for e in contract_findings(self.plan, sources)))

    def test_wrong_acl_target_rejected(self) -> None:
        sources = dict(self.sources)
        sources["02-create-protected-staging.ps1"] = sources["02-create-protected-staging.ps1"].replace(
            "Set-Acl -LiteralPath $plan.paths.parent", "Set-Acl -LiteralPath $plan.paths.repository")
        self.assertTrue(any("unexpected ACL mutation target" in e for e in contract_findings(self.plan, sources)))

    def test_rollback_keeps_staging(self) -> None:
        rollback = self.sources["04-restore-parent-acl.ps1"]
        self.assertIn("parent is not the exact planned after-state", rollback)
        self.assertIn("PARENT_RESTORED_STAGING_RETAINED", rollback)
        self.assertNotRegex(rollback, r"(?i)Remove-Item|Directory\]::Delete|::CreateDirectory")

    def test_no_overwrite_backup_and_no_activation(self) -> None:
        backup = self.sources["01-preflight-backup.ps1"]
        self.assertIn("[IO.FileMode]::CreateNew", backup)
        self.assertIn("backup exists; never overwrite", backup)
        self.assertNotRegex("\n".join(self.sources.values()), r"(?i)\.sql\b|Invoke-Sqlcmd|pyodbc|psycopg")


if __name__ == "__main__":
    unittest.main()
