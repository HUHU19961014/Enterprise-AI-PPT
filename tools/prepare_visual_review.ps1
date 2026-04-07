param(
  [string]$Template,
  [string]$ReferenceBody,
  [string]$OutputRoot
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot

if (-not $Template) { $Template = Join-Path $ProjectRoot "assets\templates\sie_template.pptx" }
if (-not $ReferenceBody) { $ReferenceBody = Join-Path $ProjectRoot "samples\input\reference_body_style.pptx" }
if (-not $OutputRoot) { $OutputRoot = Join-Path $ProjectRoot "projects\visual_review" }
$registryPath = Join-Path $ProjectRoot "samples\visual_review_cases.json"

$scriptPath = Join-Path $ProjectRoot "main.py"
if (-not (Test-Path $Template)) { throw "Template not found: $Template" }
if (-not (Test-Path $scriptPath)) { throw "Generator script not found: $scriptPath" }
if (-not (Test-Path $registryPath)) { throw "Visual review registry not found: $registryPath" }

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$reviewDir = Join-Path $OutputRoot "visual_review_$timestamp"
New-Item -ItemType Directory -Path $reviewDir -Force | Out-Null

$cases = Get-Content $registryPath -Raw | ConvertFrom-Json

$summaryLines = New-Object System.Collections.Generic.List[string]
$summaryLines.Add("# Visual Review Batch")
$summaryLines.Add("")
$summaryLines.Add("Generated at: $timestamp")
$summaryLines.Add("Output dir: $reviewDir")
$summaryLines.Add("")
$summaryLines.Add("Global checklist:")
$summaryLines.Add("- Cover, directory, body, and ending slides are in the right order.")
$summaryLines.Add("- Active directory highlight is correct.")
$summaryLines.Add("- Template visual assets are preserved.")
$summaryLines.Add("- No obvious text overflow, overlap, or misalignment.")
$summaryLines.Add("- Both _QA.txt and _QA.json exist.")
$summaryLines.Add("")

foreach ($case in $cases) {
  $htmlPath = Join-Path $ProjectRoot $case.html
  if (-not (Test-Path $htmlPath)) {
    throw "HTML not found: $htmlPath"
  }

  Write-Host ("-- Generating visual review case: {0}" -f $case.name)
  $lines = @(
    python $scriptPath `
      --template "$Template" `
      --html "$htmlPath" `
      --reference-body "$ReferenceBody" `
      --output-name "VisualReview_$($case.name)" `
      --output-dir "$reviewDir" `
      --active-start 0
  ) 2>&1

  if ($LASTEXITCODE -ne 0) {
    throw "Failed to generate visual review case: $($case.name)"
  }

  $cleanLines = @($lines | Where-Object { $_ -and $_.Trim() -ne "" })
  if ($cleanLines.Count -lt 2) {
    throw "Unexpected CLI output for case: $($case.name)"
  }

  $reportPath = $cleanLines[0].Trim()
  $pptxPath = $cleanLines[1].Trim()
  $jsonPath = [System.IO.Path]::ChangeExtension($reportPath, ".json")

  $summaryLines.Add("## $($case.name)")
  $summaryLines.Add("")
  $summaryLines.Add("Label: $($case.label)")
  $summaryLines.Add("")
  $summaryLines.Add("PPT: $pptxPath")
  $summaryLines.Add("QA.txt: $reportPath")
  $summaryLines.Add("QA.json: $jsonPath")
  $summaryLines.Add("Focus checks:")
  foreach ($item in $case.focus) {
    $summaryLines.Add("- $item")
  }
  $summaryLines.Add("")
}

$summaryPath = Join-Path $reviewDir "VISUAL_REVIEW_CHECKLIST.md"
$summaryLines | Set-Content -Path $summaryPath -Encoding UTF8

Write-Host ""
Write-Host "Visual review batch ready:"
Write-Host $reviewDir
Write-Host $summaryPath
