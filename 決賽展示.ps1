param([int]$Port=8765)
$ErrorActionPreference='Stop'
$taskConfigPath=Join-Path $PSScriptRoot 'config.local.json'
$taskPython=$env:INNOSERVE_PYTHON_EXECUTABLE
if ((-not $taskPython) -and (Test-Path -LiteralPath $taskConfigPath)) {
    $taskPython=(Get-Content -Raw -Encoding UTF8 -LiteralPath $taskConfigPath | ConvertFrom-Json).python_executable
}
if (-not $taskPython) {$taskPython=Join-Path $PSScriptRoot '.venv\Scripts\python.exe'}
if (-not [System.IO.Path]::IsPathRooted($taskPython)) {$taskPython=Join-Path $PSScriptRoot $taskPython}
if (-not (Test-Path -LiteralPath $taskPython)) {throw '請先設定模型Python環境。'}
$host.UI.RawUI.WindowTitle='AI 資安框架｜決賽展示'
function prompt {'展示> '}
Clear-Host
& $taskPython -X utf8 (Join-Path $PSScriptRoot 'scripts/showcase.py') --port $Port
exit $LASTEXITCODE
