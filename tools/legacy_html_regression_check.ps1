param(
  [string]$TemplatePath,
  [string]$HtmlPath,
  [string]$InputDir,
  [string]$OutputDir
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$scriptPath = Join-Path $ProjectRoot "tools\regression_check.ps1"

if (-not (Test-Path $scriptPath)) {
  throw "Legacy regression wrapper target not found: $scriptPath"
}

powershell -ExecutionPolicy Bypass -File $scriptPath `
  -TemplatePath $TemplatePath `
  -HtmlPath $HtmlPath `
  -InputDir $InputDir `
  -OutputDir $OutputDir
