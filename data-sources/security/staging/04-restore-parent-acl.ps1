# Recovery proposal only. Never deletes staging, artifacts, or unrelated files.
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
$backup = Read-S1Backup $plan $ExpectedBackupSha256
foreach ($entry in @($plan.before | Where-Object { $_.Path -in @($plan.paths.repository,$plan.paths.ancestor) })) {
    if ((Get-S1Sddl $entry.Path) -ne $entry.SDDL) { throw 'STOP: drift needs separately reviewed recovery.' }
}
if ((Get-S1TargetFingerprint (Get-S1Sddl $plan.paths.parent)) -ne (Get-S1TargetFingerprint $plan.target_parent_sddl)) { throw 'STOP: parent is not the exact planned after-state.' }
$saved = @($backup.before | Where-Object { $_.Path -eq $plan.paths.parent })
if ($saved.Count -ne 1) { throw 'STOP: missing exact parent backup.' }
$restoreAcl = [Security.AccessControl.DirectorySecurity]::new()
$restoreAcl.SetSecurityDescriptorSddlForm($saved[0].SDDL)
Set-Acl -LiteralPath $plan.paths.parent -AclObject $restoreAcl -ErrorAction Stop
if ((Get-S1Sddl $plan.paths.parent) -ne $saved[0].SDDL) { throw 'STOP: restored parent differs; manual recovery review.' }
[pscustomobject]@{Status='PARENT_RESTORED_STAGING_RETAINED';Parent=$plan.paths.parent}
# Check all child effects before resuming. Staging cleanup requires separate review.
