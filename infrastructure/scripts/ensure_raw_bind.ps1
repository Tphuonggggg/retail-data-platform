param([switch]$Apply)
$ErrorActionPreference = 'Stop'
$repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$target = [IO.Path]::GetFullPath((Join-Path $repoRoot 'infrastructure\postgres'))
$alias = [IO.Path]::GetFullPath((Join-Path $repoRoot 'storage\raw'))
if (-not $target.StartsWith($repoRoot + '\',[StringComparison]::OrdinalIgnoreCase) -or
    -not $alias.StartsWith($repoRoot + '\',[StringComparison]::OrdinalIgnoreCase) -or
    -not (Test-Path -LiteralPath (Join-Path $target 'bootstrap.sql') -PathType Leaf)) {
    throw 'Invalid workspace/bootstrap target'
}
if (Test-Path -LiteralPath $alias) {
    $item = Get-Item -LiteralPath $alias
    if ($item.LinkType -ne 'Junction' -or @($item.Target).Count -ne 1 -or
        [IO.Path]::GetFullPath($item.Target[0]) -ne $target) {
        throw 'Existing compatibility path is not the expected junction; inspect without overwriting'
    }
    Write-Output 'PASS: original container bind resolves to canonical PostgreSQL scripts'
} elseif ($Apply) {
    New-Item -ItemType Directory -Path (Split-Path -Parent $alias) -Force | Out-Null
    New-Item -ItemType Junction -Path $alias -Target $target | Out-Null
    Write-Output 'Created runtime-only compatibility junction; no database/container changes'
} else {
    Write-Output 'NOT RUN: missing junction; use -Apply only to restore the original bind path'
}
