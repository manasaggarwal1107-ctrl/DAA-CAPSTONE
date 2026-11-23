<# Runs the automated test suite (creates the virtual environment and installs pytest on first use). #>
$ErrorActionPreference = 'Stop'
$backend = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) 'backend'
$py = Join-Path $backend '.venv\Scripts\python.exe'
if (-not (Test-Path $py)) { Write-Host 'Run .\start.ps1 once first to create the environment (press Ctrl+C after it starts).'; exit 1 }
& $py -m pip install --disable-pip-version-check -q -r (Join-Path $backend 'requirements-dev.txt')
Push-Location $backend
try { & $py -m pytest } finally { Pop-Location }
exit $LASTEXITCODE
