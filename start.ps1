<#
  Mini-Courier Planner - one-command start for Windows 10/11 (PowerShell 5.1+).

    .\start.ps1             install (first run only) and start the app at http://127.0.0.1:8000
    .\start.ps1 -Rebuild    rebuild the React frontend first (needs Node.js 18+)
    .\start.ps1 -Port 9000  use another port
    .\start.ps1 -NoBrowser  do not open the browser

  If scripts are blocked, run once:  Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
  or use start.bat, which bypasses the policy for this one script.
#>
param([int]$Port = 8000, [switch]$Rebuild, [switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = Join-Path $root 'backend'
$venv = Join-Path $backend '.venv'
$py = Join-Path $venv 'Scripts\python.exe'

function Test-Py([string]$exe, [string[]]$pre) {
    try {
        $v = & $exe @pre --version 2>&1 | Out-String
        return ($v -match 'Python 3\.(\d+)' -and [int]$Matches[1] -ge 10)
    } catch { return $false }
}
function Get-PythonCommand {
    if (Test-Py 'py' @('-3')) { return @('py', '-3') }
    if (Test-Py 'python' @()) { return @('python') }
    if (Test-Py 'python3' @()) { return @('python3') }
    throw 'Python 3.10 or newer was not found. Install it from https://www.python.org/downloads/ (tick "Add python.exe to PATH").'
}

if (-not (Test-Path $py)) {
    $sys = @(Get-PythonCommand)
    $sysExe = $sys[0]
    $sysPre = if ($sys.Count -gt 1) { @($sys[1]) } else { @() }
    Write-Host 'Creating virtual environment (first run only)...' -ForegroundColor Cyan
    & $sysExe @sysPre -m venv $venv
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the virtual environment.' }
}
$stamp = Join-Path $venv '.deps-installed'
$req = Join-Path $backend 'requirements.txt'
if (-not (Test-Path $stamp) -or (Get-Item $req).LastWriteTime -gt (Get-Item $stamp).LastWriteTime) {
    Write-Host 'Installing Python packages...' -ForegroundColor Cyan
    & $py -m pip install --disable-pip-version-check -r $req
    if ($LASTEXITCODE -ne 0) { throw 'pip install failed. Check your internet connection.' }
    New-Item -ItemType File -Force $stamp | Out-Null
}

$dist = Join-Path $root 'frontend\dist\index.html'
if ($Rebuild -or -not (Test-Path $dist)) {
    if (-not (Get-Command npm -ErrorAction SilentlyContinue)) { throw 'Node.js is needed to build the frontend. Install it from https://nodejs.org/ or use the prebuilt frontend\dist folder.' }
    Push-Location (Join-Path $root 'frontend')
    try {
        if (-not (Test-Path 'node_modules')) { Write-Host 'Installing frontend packages...' -ForegroundColor Cyan; npm install --no-audit --no-fund; if ($LASTEXITCODE -ne 0) { throw 'npm install failed.' } }
        Write-Host 'Building the frontend...' -ForegroundColor Cyan
        npm run build
        if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed.' }
    } finally { Pop-Location }
}

$url = "http://127.0.0.1:$Port"
Write-Host "Starting Mini-Courier Planner at $url  (press Ctrl+C to stop)" -ForegroundColor Green
if (-not $NoBrowser) { Start-Job { Start-Sleep 2; Start-Process $using:url } | Out-Null }
Push-Location $backend
try { & $py -m uvicorn app.main:app --host 127.0.0.1 --port $Port } finally { Pop-Location }
