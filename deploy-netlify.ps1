# Deploy frontend to Netlify (run from project root)
# Requires: netlify login (one-time)
# Note: CLI deploy may hit "MissingBlobsEnvironmentError" - use GitHub deploy instead (see DEPLOY.md)

$ErrorActionPreference = "Stop"
$netlify = "D:\pak-bank-discounts-ai\tools\netlify-cli\node_modules\.bin\netlify.cmd"

if (-not (Test-Path $netlify)) {
    Write-Error "Netlify CLI not found. Run: cd tools\netlify-cli && npm install"
    exit 1
}

Write-Host "Deploying frontend to Netlify..."
Push-Location "$PSScriptRoot\frontend"
try {
    & $netlify deploy --prod
} finally {
    Pop-Location
}
Write-Host "If Blobs error: connect via GitHub (Netlify > Import from Git). See DEPLOY.md"
