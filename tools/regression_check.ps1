param(
  [string]$TemplatePath,
  [string]$HtmlPath,
  [string]$OutputDir
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot

if (-not $TemplatePath) { $TemplatePath = Join-Path $ProjectRoot "assets\templates\sie_template.pptx" }
if (-not $HtmlPath) { $HtmlPath = Join-Path $ProjectRoot "input\uat_plan_sample.html" }
if (-not $OutputDir) { $OutputDir = Join-Path $ProjectRoot "projects\generated" }

Write-Host "== SIE-autoppt Regression Check =="

function Assert-Path($path, $name) {
  if (-not (Test-Path $path)) {
    throw "$name not found: $path"
  }
  Write-Host "[OK] $name exists: $path"
}

Assert-Path $TemplatePath "Template"
Assert-Path $HtmlPath "HTML input"
Assert-Path (Join-Path $ProjectRoot "tools\sie_autoppt_cli.py") "CLI entry"

python --version | Out-Null
python -c "import pptx; print('python-pptx ok')" | Out-Null
Write-Host "[OK] Python and python-pptx available"

python -m py_compile (Join-Path $ProjectRoot "tools\sie_autoppt_cli.py")
python -m py_compile (Join-Path $ProjectRoot "tools\sie_autoppt\generator.py")
Write-Host "[OK] Python files compiled"

New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
python (Join-Path $ProjectRoot "tools\sie_autoppt_cli.py") `
  --template "$TemplatePath" `
  --html "$HtmlPath" `
  --output-name "SIE_Regression" `
  --output-dir "$OutputDir" `
  --chapters 3 `
  --active-start 0
Write-Host "[OK] Generation command executed"
Write-Host "== Regression check passed =="

