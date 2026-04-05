param()

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot

Write-Host "== SIE-autoppt Unit Tests =="
python -m pytest "$ProjectRoot/tests" -q
