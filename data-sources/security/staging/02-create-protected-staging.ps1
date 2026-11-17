# PREPARED ONLY. Do not execute from writable development folders as administrator.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-fA-F0-9]{64}$')][string]$ExpectedPlanSha256,
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-fA-F0-9]{64}$')][string]$ExpectedBackupSha256,
    [string]$PlanPath = "$PSScriptRoot\acl-plan.json",
    [switch]$OwnerAuthorized
)
. "$PSScriptRoot\acl-common.ps1"
$plan = Read-S1Plan $PlanPath $ExpectedPlanSha256
Assert-S1Context $plan
Assert-S1MutationReady $plan $OwnerAuthorized.IsPresent $PSScriptRoot
Assert-S1Snapshot $plan
$null = Read-S1Backup $plan $ExpectedBackupSha256
$parentAcl = [Security.AccessControl.DirectorySecurity]::new()
$parentAcl.SetSecurityDescriptorSddlForm($plan.target_parent_sddl)
$stageAcl = [Security.AccessControl.DirectorySecurity]::new()
$stageAcl.SetSecurityDescriptorSddlForm($plan.target_staging_sddl)
try {
    # Only this approved boundary; never set repository or D:\Code ACLs.
    Set-Acl -LiteralPath $plan.paths.parent -AclObject $parentAcl -ErrorAction Stop
    if ((Get-S1TargetFingerprint (Get-S1Sddl $plan.paths.parent)) -ne (Get-S1TargetFingerprint $plan.target_parent_sddl)) {
        throw 'STOP: parent owner/DACL does not match planned target.'
    }
    foreach ($entry in @($plan.before | Where-Object { $_.Path -in @($plan.paths.repository,$plan.paths.ancestor) })) {
        if ((Get-S1Sddl $entry.Path) -ne $entry.SDDL) { throw 'STOP: unexpected child/ancestor ACL propagation.' }
    }
    if (Test-Path -LiteralPath $plan.paths.staging) { throw 'STOP: staging appeared concurrently.' }
    # NTFS creation with the protected descriptor; no initially broad inherited DACL.
    $null = [IO.Directory]::CreateDirectory($plan.paths.staging,$stageAcl)
    Assert-S1NoReparse $plan.paths.staging
    if ((Get-S1TargetFingerprint (Get-S1Sddl $plan.paths.staging)) -ne (Get-S1TargetFingerprint $plan.target_staging_sddl)) {
        throw 'STOP: final staging owner/DACL differs.'
    }
    [pscustomobject]@{Status='ACL_CREATED_NOT_SQL_EXECUTION_READY';Staging=$plan.paths.staging;SDDL=(Get-S1Sddl $plan.paths.staging)}
} catch {
    Write-Warning 'Partial failure possible. Keep evidence; do not delete/recreate staging or alter repository ACLs. Use reviewed recovery procedure.'
    throw
}
