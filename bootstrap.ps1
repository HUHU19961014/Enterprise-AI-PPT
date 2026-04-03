param(
  [Parameter(Mandatory = $true)]
  [string]$ProjectName,
  [string]$Format = "ppt169"
)

$PPT_MASTER = "C:\Users\1\Documents\Cursor\ppt-master"
$SCRIPT = Join-Path $PPT_MASTER "skills\ppt-master\scripts\project_manager.py"

if (-not (Test-Path $SCRIPT)) {
  Write-Error "未找到脚本: $SCRIPT"
  exit 1
}

Write-Host "初始化项目: $ProjectName ($Format)"
python $SCRIPT init $ProjectName --format $Format
