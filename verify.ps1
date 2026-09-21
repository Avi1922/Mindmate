$ErrorActionPreference = 'Stop'

$projectRoot = $PSScriptRoot
$pythonPath = Join-Path $projectRoot 'backend\.venv\Scripts\python.exe'

if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw 'Backend virtual environment is missing. Create backend\.venv and install requirements first.'
}

Write-Host 'Running backend tests...'
& $pythonPath -m pytest -q (Join-Path $projectRoot 'backend\tests')
if ($LASTEXITCODE -ne 0) { throw 'Backend tests failed.' }

Push-Location (Join-Path $projectRoot 'frontend')
try {
    Write-Host 'Running frontend tests...'
    & npm.cmd run test
    if ($LASTEXITCODE -ne 0) { throw 'Frontend tests failed.' }

    Write-Host 'Running TypeScript checks...'
    & npm.cmd run typecheck
    if ($LASTEXITCODE -ne 0) { throw 'Frontend typecheck failed.' }

    Write-Host 'Running frontend lint...'
    & npm.cmd run lint
    if ($LASTEXITCODE -ne 0) { throw 'Frontend lint failed.' }

    Write-Host 'Building production frontend...'
    & npm.cmd run build
    if ($LASTEXITCODE -ne 0) { throw 'Frontend production build failed.' }
}
finally {
    Pop-Location
}

Write-Host 'MindMate verification completed successfully.' -ForegroundColor Green
