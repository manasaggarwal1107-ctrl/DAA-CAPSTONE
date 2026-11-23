<# Rebuilds frontend\dist (needs Node.js 18+). #>
$ErrorActionPreference = 'Stop'
Push-Location (Join-Path (Split-Path -Parent $PSScriptRoot) 'frontend')
try { if (-not (Test-Path node_modules)) { npm install --no-audit --no-fund }; npm run build } finally { Pop-Location }
