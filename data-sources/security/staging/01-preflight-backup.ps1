# PREPARED ONLY. Default is read-only; no self-elevation or SQL execution.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-fA-F0-9]{64}$')][string]$ExpectedPlanSha256,
    [string]$PlanPath = "$PSScriptRoot\acl-plan.json",
    [switch]$WriteBackup,
    [switch]$OwnerAuthorized
)
. "$PSScriptRoot\acl-common.ps1"
$plan = Read-S1Plan $PlanPath $ExpectedPlanSha256
Assert-S1Context $plan
Assert-S1Snapshot $plan
$report = [ordered]@{plan_id=$plan.plan_id;observed_at_utc=[DateTime]::UtcNow.ToString('o');staging_existed=$false;before=$plan.before}
if ($WriteBackup) {
    if (-not $OwnerAuthorized) { throw 'STOP: backup write authority required.' }
    Assert-S1TrustedDirectory $PSScriptRoot
    Assert-S1TrustedDirectory (Split-Path -Path $plan.paths.backup_file -Parent)
    if (Test-Path -LiteralPath $plan.paths.backup_file) { throw 'STOP: backup exists; never overwrite.' }
    $bytes = [Text.UTF8Encoding]::new($false).GetBytes(($report | ConvertTo-Json -Depth 8))
    $stream = [IO.File]::Open($plan.paths.backup_file,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
    try { $stream.Write($bytes,0,$bytes.Length); $stream.Flush($true) } finally { $stream.Dispose() }
    [pscustomobject]@{Backup=$plan.paths.backup_file;SHA256=(Get-S1Sha256 $plan.paths.backup_file)}
}
$report | ConvertTo-Json -Depth 8
# Inspection/backup is not approval of the unsafe ancestor or parent mutation.
