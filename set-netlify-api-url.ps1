# Set NEXT_PUBLIC_API_BASE_URL in Netlify (run after backend is deployed)
# Usage: .\set-netlify-api-url.ps1 "https://pak-bank-backend.onrender.com"

param([Parameter(Mandatory=$true)][string]$ApiUrl)

$netlify = "D:\pak-bank-discounts-ai\tools\netlify-cli\node_modules\.bin\netlify.cmd"
Push-Location "$PSScriptRoot\frontend"
try {
    & $netlify env:set NEXT_PUBLIC_API_BASE_URL $ApiUrl --context production
    Write-Host "Set NEXT_PUBLIC_API_BASE_URL. Trigger a redeploy in Netlify dashboard for it to take effect."
} finally {
    Pop-Location
}
