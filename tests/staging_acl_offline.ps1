# Offline only: AST parsing, descriptor objects and synthetic access fixtures.
# Never invokes 01/02/03/04 operator scripts, Set-Acl or CreateDirectory.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$package = Join-Path (Split-Path -Parent $PSScriptRoot) 'data-sources\security\staging'
$syntaxCount = 0
foreach ($file in @(Get-ChildItem -LiteralPath $package -Filter '*.ps1' -File)) {
    $tokens = $null; $parseErrors = $null
    $null = [Management.Automation.Language.Parser]::ParseFile($file.FullName,[ref]$tokens,[ref]$parseErrors)
    if ($parseErrors.Count -ne 0) { throw "STOP: syntax error: $($file.Name)" }
    $syntaxCount++
}
if ($syntaxCount -ne 5) { throw 'STOP: expected five prepared PowerShell artifacts.' }
. (Join-Path $package 'acl-common.ps1')
$planPath = Join-Path $package 'acl-plan.json'
$plan = Read-S1Plan $planPath (Get-S1Sha256 $planPath)
$script:rejectedCases = 0
function Expect-S1Rejection([scriptblock]$Action) {
    $rejected = $false
    try { $null = & $Action } catch { $rejected = $true }
    if (-not $rejected) { throw 'STOP: unsafe fixture was not rejected.' }
    $script:rejectedCases++
}
Assert-S1TargetPolicy $plan
Expect-S1Rejection { Read-S1Plan $planPath ('0' * 64) }
Expect-S1Rejection { Assert-S1MutationReady $plan $false $package }
foreach ($mutation in @('broad-stage','deny-stage','unprotected-stage','missing-stream','broad-parent')) {
    $altered = $plan | ConvertTo-Json -Depth 12 | ConvertFrom-Json
    switch ($mutation) {
        'broad-stage' { $altered.target_staging_sddl += '(A;OICI;FA;;;AU)' }
        'deny-stage' { $altered.target_staging_sddl = $altered.target_staging_sddl.Replace('D:P','D:P(D;;FA;;;AU)') }
        'unprotected-stage' { $altered.target_staging_sddl = $altered.target_staging_sddl.Replace('D:P','D:') }
        'missing-stream' { $altered.target_parent_sddl = $altered.target_parent_sddl.Replace('(A;OICIIO;0xe0010000;;;S-1-5-11)','') }
        'broad-parent' { $altered.target_parent_sddl += '(A;;FA;;;AU)' }
    }
    Expect-S1Rejection { Assert-S1TargetPolicy $altered }
}
# Override only the filesystem read helper with synthetic descriptors in this process.
# This exercises actual mask/IO handling and ancestor guards without probing real rights.
$script:fixtureSddl = @{}
function Get-S1Sddl([string]$Path) { return $script:fixtureSddl[$Path] }
$script:fixtureSddl['D:\'] = 'O:SYG:SYD:(A;;0x1301bf;;;AU)(A;;FA;;;SY)'
$script:fixtureSddl[$plan.paths.ancestor] = 'O:SYG:SYD:(A;;0x1301bf;;;AU)(A;OICIIO;GA;;;AU)'
$grants = @(Get-S1UntrustedGrants $plan.paths.ancestor)
if ($grants.Count -ne 1 -or -not $grants[0].Delete -or $grants[0].DeleteChild) {
    throw 'STOP: Modify/Delete/IO fixture result differs.'
}
Expect-S1Rejection { Assert-S1AncestorsSafe $plan }
$script:fixtureSddl[$plan.paths.ancestor] = 'O:SYG:SYD:(A;;0x1200a9;;;BU)'
Assert-S1AncestorsSafe $plan
$script:fixtureSddl[$plan.paths.ancestor] = 'O:SYG:SYD:(A;;0x40;;;BU)'
Expect-S1Rejection { Assert-S1AncestorsSafe $plan }
$script:fixtureSddl[$plan.paths.ancestor] = 'O:SYG:SYD:(A;;0x1200a9;;;BU)'
$script:fixtureSddl['D:\'] = 'O:SYG:SYD:(A;;0x40;;;AU)'
Expect-S1Rejection { Assert-S1AncestorsSafe $plan }
$script:fixtureSddl[$plan.paths.ancestor] = 'O:SYG:SYD:(A;;GW;;;AU)'
$writeGrant = @(Get-S1UntrustedGrants $plan.paths.ancestor)
if ($writeGrant.Count -ne 1 -or -not $writeGrant[0].WriteContent) { throw 'STOP: generic-write mapping failed.' }
[pscustomobject]@{
    Status='PASS_OFFLINE_ONLY'; ParsedOperatorFiles=$syntaxCount; RejectedUnsafeFixtures=$script:rejectedCases
    AccessRulesWritten=$false; OperatorEntryScriptsExecuted=$false; RuntimeAclVerified=$false
} | ConvertTo-Json -Compress
