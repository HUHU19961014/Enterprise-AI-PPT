param(
  [string]$RegressionDir,
  [string]$OutputDir,
  [string[]]$Case
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot

if (-not $RegressionDir) { $RegressionDir = Join-Path $ProjectRoot "regression" }
if (-not $OutputDir) { $OutputDir = Join-Path $ProjectRoot "output\v2_regression" }

$args = @(
  (Join-Path $ProjectRoot "run_regression.py"),
  "--regression-dir", "$RegressionDir",
  "--output-dir", "$OutputDir"
)

foreach ($item in $Case) {
  if ($item) {
    $args += @("--case", "$item")
  }
}

python @args
