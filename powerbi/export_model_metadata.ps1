# Offline TMDL parsing with the TOM assembly already bundled with Desktop.
# Does not connect to an engine, process data, or save the model.
$ErrorActionPreference='Stop'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$package=Get-AppxPackage Microsoft.MicrosoftPowerBIDesktop
if(-not $package){throw 'Power BI Desktop TOM is required to parse local TMDL'}
$assembly=Join-Path $package.InstallLocation 'bin\Microsoft.PowerBI.Tabular.dll'
[void][Reflection.Assembly]::LoadFrom($assembly)
$folder=Join-Path $PSScriptRoot 'RetailSalesAnalytics\RetailSalesAnalytics.SemanticModel\definition'
$model=[Microsoft.AnalysisServices.Tabular.TmdlSerializer]::DeserializeModelFromFolder($folder)
[Microsoft.AnalysisServices.Tabular.JsonSerializer]::SerializeObject($model)
