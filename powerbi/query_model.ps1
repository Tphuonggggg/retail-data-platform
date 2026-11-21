param(
    [Parameter(Mandatory=$true)][int]$DesktopPid,
    [string]$OutputFile=(Join-Path $PSScriptRoot 'dax-runtime-results.json')
)
# Read-only, real Analysis Services DAX execution. Never changes model or credentials.
$ErrorActionPreference='Stop'
$package=Get-AppxPackage Microsoft.MicrosoftPowerBIDesktop
[void][Reflection.Assembly]::LoadFrom((Join-Path $package.InstallLocation 'bin\Microsoft.PowerBI.AdomdClient.dll'))
$engine=@(Get-CimInstance Win32_Process -Filter "Name='msmdsrv.exe'"|Where-Object {$_.ParentProcessId -eq $DesktopPid})
if($engine.Count -ne 1){throw 'Expected exactly one selected Desktop engine'}
$match=[regex]::Match($engine[0].CommandLine,'-s "([^"]+)"')
if(-not $match.Success){throw 'Workspace directory not discovered'}
$port=[IO.File]::ReadAllText((Join-Path $match.Groups[1].Value 'msmdsrv.port.txt'),[Text.Encoding]::Unicode).Trim([char]0).Trim()
if($port -notmatch '^\d+$'){throw 'Invalid engine port'}
$connection=New-Object Microsoft.AnalysisServices.AdomdClient.AdomdConnection('Data Source=localhost:'+$port+';Application Name=RetailSalesValidation;Timeout=15')
$queries=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'dax-validation-queries.json') -Raw -Encoding UTF8|ConvertFrom-Json
$results=@()
try {
    $connection.Open()
    foreach($query in $queries) {
        if($query.dax -notmatch '^EVALUATE '){throw 'Only reviewed EVALUATE queries allowed'}
        $command=$connection.CreateCommand();$command.CommandText=$query.dax;$command.CommandTimeout=60
        $timer=[Diagnostics.Stopwatch]::StartNew()
        $reader=$command.ExecuteReader();$rows=@()
        while($reader.Read()) {
            $row=[ordered]@{}
            for($i=0;$i -lt $reader.FieldCount;$i++) {
                $value=$reader.GetValue($i)
                if($value -is [DBNull]){$value=$null}
                $row[$reader.GetName($i)]=$value
            }
            $rows+=,$row
        }
        $reader.Close();$timer.Stop()
        $results+=@{id=$query.id;rows=$rows;milliseconds=$timer.Elapsed.TotalMilliseconds;status='EXECUTED_NOT_YET_RECONCILED'}
        if($query.id -eq 'baseline' -and $null -eq $rows[0]['[Sales]']) {
            $results[-1].status='BLOCKED_MODEL_HAS_NO_IMPORTED_DATA'
            break
        }
    }
} finally {$connection.Close()}
$results|ConvertTo-Json -Depth 15|Set-Content -LiteralPath $OutputFile -Encoding UTF8
Write-Output ('DAX_QUERIES_EXECUTED '+$results.Count+'; requires SQL reconciliation before PASS')
