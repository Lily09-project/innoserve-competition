param([int]$Port = 8765, [switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$taskConfigPath = Join-Path $PSScriptRoot 'config.local.json'
$taskConfiguredPython = $env:INNOSERVE_PYTHON_EXECUTABLE
if ((-not $taskConfiguredPython) -and (Test-Path -LiteralPath $taskConfigPath)) {
    $taskConfiguredPython = (Get-Content -Raw -Encoding UTF8 -LiteralPath $taskConfigPath | ConvertFrom-Json).python_executable
}
$taskPython = $taskConfiguredPython
if (-not $taskPython) { $taskPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe' }
if (-not (Test-Path -LiteralPath $taskPython)) { throw '請安裝requirements.txt，並設定config.local.json中的python_executable。' }
$taskUrl = "http://127.0.0.1:$Port"
try {
    $taskStatus = Invoke-RestMethod -Uri "$taskUrl/api/status" -TimeoutSec 2
    if ($taskStatus.product -eq 'ai-security-demo.v3') { Write-Host "本機 API 已啟動：$taskUrl/api/status"; exit 0 }
    throw '此連接埠已有其他服務。'
} catch { if ($_.Exception.Message -eq '此連接埠已有其他服務。') { throw } }
$taskLogDir = Join-Path $PSScriptRoot 'runtime\service_logs'
New-Item -ItemType Directory -Path $taskLogDir -Force | Out-Null
$taskLogName = Get-Date -Format 'yyyyMMdd-HHmmss'
$taskServerPath = Join-Path $PSScriptRoot 'app\server.py'
$taskHelper = Start-Process -FilePath $taskPython -ArgumentList "-X utf8 `"$taskServerPath`" --port $Port" -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $taskLogDir "$taskLogName.stdout.log") -RedirectStandardError (Join-Path $taskLogDir "$taskLogName.stderr.log")
for ($taskAttempt = 0; $taskAttempt -lt 30; $taskAttempt++) {
    Start-Sleep -Milliseconds 500
    if ($taskHelper.HasExited) { throw '服務啟動失敗，請查看runtime/service_logs。' }
    try {
        $taskStatus = Invoke-RestMethod -Uri "$taskUrl/api/status" -TimeoutSec 1
        if ($taskStatus.product -eq 'ai-security-demo.v3') { Write-Host "本機 API 已啟動：$taskUrl/api/status"; exit 0 }
    } catch { }
}
throw '服務啟動逾時。'
