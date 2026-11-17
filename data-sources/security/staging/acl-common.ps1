# Prepared only. Functions have no top-level filesystem mutations or SQL actions.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-S1Sha256([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256 -ErrorAction Stop).Hash.ToLowerInvariant()
}

function Get-S1Sddl([string]$Path) {
    return (Get-Acl -LiteralPath $Path -ErrorAction Stop).GetSecurityDescriptorSddlForm(
        [Security.AccessControl.AccessControlSections]'Owner,Group,Access')
}

function Assert-S1NoReparse([string]$Path) {
    $node = [IO.Path]::GetFullPath($Path)
    while ($node) {
        $item = Get-Item -LiteralPath $node -Force -ErrorAction Stop
        if (-not $item.PSIsContainer -or ([int]$item.Attributes -band 1024) -ne 0) {
            throw "STOP: non-directory/reparse path: $node"
        }
        $next = Split-Path -Path $node -Parent
        if (-not $next -or $next -eq $node) { break }
        $node = $next
    }
}

function Read-S1Plan([string]$Path, [string]$ExpectedSha256) {
    if ($ExpectedSha256 -notmatch '^[a-fA-F0-9]{64}$' -or (Get-S1Sha256 $Path) -ne $ExpectedSha256.ToLowerInvariant()) {
        throw 'STOP: plan hash mismatch; approval digest must be supplied independently.'
    }
    $plan = Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($plan.plan_id -ne 'WWI05-EX02-S1-ACL-20261117-01' -or
        $plan.paths.parent -ne 'D:\Code\Retail_Data_Platform' -or
        $plan.paths.repository -ne 'D:\Code\Retail_Data_Platform\project1_Retail_Data_platform' -or
        $plan.paths.staging -ne 'D:\Code\Retail_Data_Platform\Retail_EX02_Protected_Staging' -or
        $plan.paths.ancestor -ne 'D:\Code' -or
        $plan.paths.backup_file -ne 'C:\ProgramData\RetailDataPlatform\AclBackups\WWI05-EX02-S1-20261117.json' -or
        $plan.operator_sid -ne 'S-1-5-21-2164258108-3044412014-540060861-1001') {
        throw 'STOP: exact path/SID allowlist differs from reviewed design.'
    }
    foreach ($name in @('parent','repository','staging','ancestor','backup_file')) {
        if ([IO.Path]::GetFullPath($plan.paths.$name) -ne $plan.paths.$name) { throw 'STOP: non-canonical path.' }
    }
    $expectedBefore = @('D:\',$plan.paths.ancestor,$plan.paths.parent,$plan.paths.repository)
    if (@($plan.before).Count -ne 4 -or
        ((@($plan.before | ForEach-Object { $_.Path } | Sort-Object) -join '|') -ne (($expectedBefore | Sort-Object) -join '|'))) {
        throw 'STOP: before-state path allowlist mismatch.'
    }
    Assert-S1TargetPolicy $plan
    return $plan
}

function Assert-S1TargetPolicy($Plan) {
    $trusted = @('S-1-5-18','S-1-5-32-544','S-1-5-21-2164258108-3044412014-540060861-1001')
    $before = @($Plan.before | Where-Object { $_.Path -eq $Plan.paths.parent })
    if ($before.Count -ne 1) { throw 'STOP: parent baseline missing.' }
    $beforeRaw = [Security.AccessControl.RawSecurityDescriptor]::new($before[0].SDDL)
    foreach ($kind in @('parent','staging')) {
        $sddl = if ($kind -eq 'parent') { $Plan.target_parent_sddl } else { $Plan.target_staging_sddl }
        $raw = [Security.AccessControl.RawSecurityDescriptor]::new($sddl)
        if ($raw.Owner.Value -ne 'S-1-5-32-544' -or ([int]$raw.ControlFlags -band 4096) -eq 0) { throw 'STOP: trusted owner/protected DACL required.' }
        $selfSids = @(); $io = @()
        foreach ($ace in $raw.DiscretionaryAcl) {
            if ($ace.AceType.ToString() -ne 'AccessAllowed') { throw 'STOP: no Deny/unknown ACE in target policy.' }
            if (([int]$ace.AceFlags -band 8) -ne 0) {
                if ($kind -ne 'parent' -or [int]$ace.AceFlags -ne 11) { throw 'STOP: unexpected inherit-only ACE.' }
                $io += '{0}|{1}' -f $ace.SecurityIdentifier.Value,$ace.AccessMask
            } else {
                $flags = if ($kind -eq 'parent') { 0 } else { 3 }
                if ($trusted -notcontains $ace.SecurityIdentifier.Value -or $ace.AccessMask -ne 2032127 -or [int]$ace.AceFlags -ne $flags) { throw 'STOP: target grants exceed trusted principal matrix.' }
                $selfSids += $ace.SecurityIdentifier.Value
            }
        }
        if ((($selfSids | Sort-Object) -join ',') -ne (($trusted | Sort-Object) -join ',')) { throw 'STOP: target trusted ACE set mismatch.' }
        if ($kind -eq 'parent') {
            $originalIo = @(foreach ($ace in $beforeRaw.DiscretionaryAcl) {
                if (([int]$ace.AceFlags -band 8) -ne 0) {
                    if ($ace.AceType.ToString() -ne 'AccessAllowed' -or ([int]$ace.AceFlags -band 15) -ne 11) { throw 'STOP: unsupported legacy inheritance flags.' }
                    '{0}|{1}' -f $ace.SecurityIdentifier.Value,$ace.AccessMask
                }
            })
            if ($io.Count -ne 4 -or ($io -join ';') -ne ($originalIo -join ';') -or $raw.Group.Value -ne $beforeRaw.Group.Value) { throw 'STOP: legacy child-inheritance stream/group changed.' }
        }
    }
}

function Assert-S1Context($Plan) {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    if ($env:COMPUTERNAME -ne 'DESKTOP-OBDFK6B' -or
        (Get-CimInstance Win32_ComputerSystem -ErrorAction Stop).Name -ne 'DESKTOP-OBDFK6B' -or
        $identity.Name -ne 'DESKTOP-OBDFK6B\PC' -or $identity.User.Value -ne $Plan.operator_sid) {
        throw 'STOP: machine/operator/SID mismatch.'
    }
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw 'STOP: elevated PC administrator token required for these future operator scripts.'
    }
    $drive = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='D:'" -ErrorAction Stop
    if ($drive.FileSystem -ne 'NTFS' -or $drive.VolumeSerialNumber -ne $Plan.volume_serial) {
        throw 'STOP: reviewed NTFS volume mismatch.'
    }
    foreach ($path in @($Plan.paths.ancestor,$Plan.paths.parent,$Plan.paths.repository)) { Assert-S1NoReparse $path }
}

function Get-S1UntrustedGrants([string]$Path) {
    $trusted = @('S-1-5-18','S-1-5-32-544','S-1-5-21-2164258108-3044412014-540060861-1001')
    $raw = [Security.AccessControl.RawSecurityDescriptor]::new((Get-S1Sddl $Path))
    if ($trusted -notcontains $raw.Owner.Value) { throw "STOP: untrusted owner: $Path" }
    if ($null -eq $raw.DiscretionaryAcl) { throw 'STOP: null DACL.' }
    foreach ($ace in $raw.DiscretionaryAcl) {
        if (([int]$ace.AceFlags -band 8) -ne 0) { continue } # InheritOnly is not effective here.
        if ($ace.AceType.ToString() -ne 'AccessAllowed') { throw 'STOP: non-Allow/unknown ACE needs effective-access review.' }
        if ($trusted -contains $ace.SecurityIdentifier.Value) { continue }
        $mask = [BitConverter]::ToUInt32([BitConverter]::GetBytes([int]$ace.AccessMask),0)
        if (($mask -band 268435456) -ne 0) { $mask = $mask -bor 2032127 } # GENERIC_ALL.
        if (($mask -band 1073741824) -ne 0) { $mask = $mask -bor 1179926 } # GENERIC_WRITE.
        [pscustomobject]@{
            SID=$ace.SecurityIdentifier.Value; Mask=$mask
            Delete=(($mask -band 65536) -ne 0); DeleteChild=(($mask -band 64) -ne 0)
            WriteDacl=(($mask -band 262144) -ne 0); WriteOwner=(($mask -band 524288) -ne 0)
            WriteContent=(($mask -band 278) -ne 0)
        }
    }
}

function Assert-S1AncestorsSafe($Plan) {
    # Never waive this gate with an acknowledgement switch. Current D:\Code fails.
    foreach ($grant in @(Get-S1UntrustedGrants 'D:\')) {
        if ($grant.DeleteChild -or $grant.WriteDacl -or $grant.WriteOwner) { throw 'STOP: volume-root child replacement path.' }
    }
    foreach ($grant in @(Get-S1UntrustedGrants $Plan.paths.ancestor)) {
        if ($grant.Delete -or $grant.DeleteChild -or $grant.WriteDacl -or $grant.WriteOwner) {
            throw 'STOP: D:\Code ancestor namespace is not protected; separate Owner decision/control required.'
        }
    }
}

function Assert-S1TrustedDirectory([string]$Path) {
    Assert-S1NoReparse $Path
    foreach ($grant in @(Get-S1UntrustedGrants $Path)) {
        if ($grant.Delete -or $grant.DeleteChild -or $grant.WriteDacl -or $grant.WriteOwner -or $grant.WriteContent) {
            throw "STOP: untrusted write/delete on bootstrap/backup location: $Path"
        }
    }
    $ancestor = Split-Path -Path $Path -Parent
    while ($ancestor) {
        foreach ($grant in @(Get-S1UntrustedGrants $ancestor)) {
            if ($grant.DeleteChild -or $grant.WriteDacl -or $grant.WriteOwner -or
                (($ancestor -ne [IO.Path]::GetPathRoot($ancestor)) -and $grant.Delete)) {
                throw "STOP: unsafe bootstrap/backup ancestor: $ancestor"
            }
        }
        $next = Split-Path -Path $ancestor -Parent
        if (-not $next -or $next -eq $ancestor) { break }; $ancestor = $next
    }
}

function Assert-S1Snapshot($Plan) {
    foreach ($entry in $Plan.before) {
        if ((Get-S1Sddl $entry.Path) -ne $entry.SDDL) { throw "STOP: ACL drift: $($entry.Path)" }
    }
    if (Test-Path -LiteralPath $Plan.paths.staging) { throw 'STOP: staging already exists; no overwrite/reuse.' }
}

function Assert-S1MutationReady($Plan, [bool]$OwnerAuthorized, [string]$CodeDirectory) {
    if (-not $OwnerAuthorized) { throw 'STOP: separate exact ACL execution authority required.' }
    Assert-S1TrustedDirectory $CodeDirectory
    Assert-S1AncestorsSafe $Plan
    if (-not $Plan.parent_acl_change_approved -or -not $Plan.repository_inheritance_preservation_verified) {
        throw 'STOP: parent delta/child-inheritance preservation not approved and verified.'
    }
}

function Read-S1Backup($Plan,[string]$ExpectedBackupSha256) {
    Assert-S1TrustedDirectory (Split-Path -Path $Plan.paths.backup_file -Parent)
    if ($ExpectedBackupSha256 -notmatch '^[a-fA-F0-9]{64}$' -or
        (Get-S1Sha256 $Plan.paths.backup_file) -ne $ExpectedBackupSha256.ToLowerInvariant()) {
        throw 'STOP: backup digest mismatch; do not trust an adjacent writable checksum.'
    }
    $backup = Get-Content -LiteralPath $Plan.paths.backup_file -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($backup.plan_id -ne $Plan.plan_id -or $backup.staging_existed -ne $false) { throw 'STOP: wrong backup.' }
    foreach ($entry in $Plan.before) {
        $match = @($backup.before | Where-Object { $_.Path -eq $entry.Path -and $_.SDDL -eq $entry.SDDL })
        if ($match.Count -ne 1) { throw 'STOP: backup path/SDDL differs from pinned before-state.' }
    }
    return $backup
}

function Get-S1TargetFingerprint([string]$Sddl) {
    $raw = [Security.AccessControl.RawSecurityDescriptor]::new($Sddl)
    $aces = foreach($ace in $raw.DiscretionaryAcl) {
        '{0}|{1}|{2}|{3}' -f $ace.AceType,[int]$ace.AceFlags,$ace.AccessMask,$ace.SecurityIdentifier.Value
    }
    return '{0}|{1}|{2}|{3}' -f $raw.Owner.Value,$raw.Group.Value,([int]$raw.ControlFlags -band 4096),($aces -join ';')
}
