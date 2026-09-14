$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$backendPath = Join-Path $projectRoot 'backend'
$frontendPath = Join-Path $projectRoot 'frontend'

$backendJob = Start-Job -ArgumentList $backendPath -ScriptBlock {
    param($workingPath)
    Set-Location $workingPath
    & '.\.venv\Scripts\python.exe' -m uvicorn app.main:app --reload --port 8000
}
$frontendJob = Start-Job -ArgumentList $frontendPath -ScriptBlock {
    param($workingPath)
    Set-Location $workingPath
    $env:TARO_APP_API_BASE = 'http://127.0.0.1:8000/api/v1'
    npm run dev:h5
}

try {
    Receive-Job -Job $backendJob, $frontendJob -Wait
} finally {
    Stop-Job -Job $backendJob, $frontendJob
    Remove-Job -Job $backendJob, $frontendJob
}
