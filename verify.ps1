$ErrorActionPreference = 'Stop'

$projectRoot = $PSScriptRoot
$pythonPath = Join-Path $projectRoot 'backend\.venv\Scripts\python.exe'

if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw 'Backend virtual environment is missing. Create backend\.venv and install requirements first.'
}

Write-Host 'Running backend lint and format checks...'
& $pythonPath -m ruff check (Join-Path $projectRoot 'backend\app') (Join-Path $projectRoot 'backend\tests')
if ($LASTEXITCODE -ne 0) { throw 'Backend lint failed.' }
& $pythonPath -m ruff format --check (Join-Path $projectRoot 'backend\app') (Join-Path $projectRoot 'backend\tests')
if ($LASTEXITCODE -ne 0) { throw 'Backend format check failed.' }

Write-Host 'Running backend type checks...'
Push-Location (Join-Path $projectRoot 'backend')
try {
    & $pythonPath -m mypy app
    if ($LASTEXITCODE -ne 0) { throw 'Backend typecheck failed.' }
}
finally {
    Pop-Location
}

Write-Host 'Running backend tests with coverage...'
& $pythonPath -m pytest -q --cov=app --cov-report=term-missing --cov-fail-under=80 (Join-Path $projectRoot 'backend\tests')
if ($LASTEXITCODE -ne 0) { throw 'Backend tests failed.' }

Write-Host 'Auditing backend production dependencies...'
& $pythonPath -m pip_audit -r (Join-Path $projectRoot 'backend\requirements.txt')
if ($LASTEXITCODE -ne 0) { throw 'Backend dependency audit failed.' }

Push-Location (Join-Path $projectRoot 'frontend')
try {
    Write-Host 'Running frontend tests...'
    & npm.cmd run test:coverage
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

    Write-Host 'Checking frontend bundle budget...'
    & npm.cmd run check:bundle
    if ($LASTEXITCODE -ne 0) { throw 'Frontend bundle budget failed.' }

    Write-Host 'Auditing frontend production dependencies...'
    & npm.cmd audit --omit=dev
    if ($LASTEXITCODE -ne 0) { throw 'Frontend dependency audit failed.' }
}
finally {
    Pop-Location
}

Write-Host 'MindMate verification completed successfully.' -ForegroundColor Green
