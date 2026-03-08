$ErrorActionPreference = 'Stop'

$RootDir = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $RootDir 'backend'
$FrontendDir = Join-Path $RootDir 'frontend'
$VenvPython = Join-Path $BackendDir '.venv\Scripts\python.exe'

Write-Host 'Setting up backend with Python 3.14 if available...'

if (Get-Command py -ErrorAction SilentlyContinue) {
    py -3.14 -m venv (Join-Path $BackendDir '.venv')
} else {
    python -m venv (Join-Path $BackendDir '.venv')
}

& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -r (Join-Path $BackendDir 'requirements.txt')
& $VenvPython -m pip install -r (Join-Path $BackendDir 'requirements-dev.txt')

Write-Host 'Backend setup complete.'

Push-Location $FrontendDir
npm install
Pop-Location

Write-Host 'Frontend setup complete.'
Write-Host 'Run backend with: backend\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000'
Write-Host 'Run frontend with: cd frontend; npm run dev'
