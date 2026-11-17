# Read-only future operator verification. Does not activate or copy SQL artifacts.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-fA-F0-9]{64}$')][string]$ExpectedPlanSha256,
    [string]$PlanPath = "$PSScriptRoot\acl-plan.json"
)
. "$PSScriptRoot\acl-common.ps1"
$plan = Read-S1Plan $PlanPath $ExpectedPlanSha256
Assert-S1Context $plan
Assert-S1AncestorsSafe $plan
foreach ($entry in @($plan.before | Where-Object { $_.Path -in @($plan.paths.repository,$plan.paths.ancestor) })) {
    if ((Get-S1Sddl $entry.Path) -ne $entry.SDDL) { throw 'STOP: repository/ancestor ACL drift.' }
}
foreach ($pair in @(@($plan.paths.parent,$plan.target_parent_sddl),@($plan.paths.staging,$plan.target_staging_sddl))) {
    Assert-S1NoReparse $pair[0]
    if ((Get-S1TargetFingerprint (Get-S1Sddl $pair[0])) -ne (Get-S1TargetFingerprint $pair[1])) { throw 'STOP: target DACL mismatch.' }
    foreach ($grant in @(Get-S1UntrustedGrants $pair[0])) {
        if ($grant.Delete -or $grant.DeleteChild -or $grant.WriteDacl -or $grant.WriteOwner -or $grant.WriteContent) { throw 'STOP: untrusted effective mutation grant.' }
    }
}
[pscustomobject]@{Status='ACL_METADATA_MATCH_NOT_EX02_RUNTIME_PASS';ParentSDDL=(Get-S1Sddl $plan.paths.parent);StagingSDDL=(Get-S1Sddl $plan.paths.staging)}
