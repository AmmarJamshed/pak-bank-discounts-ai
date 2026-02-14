# Run the scraper LOCALLY to populate Neon with 4000+ deals
# Render free tier times out; local run completes fully (same as localhost setup)
#
# IMPORTANT: Use the SAME DATABASE_URL as Render (from Render Dashboard -> pak-bank-backend -> Environment)
#
# 1. Get DATABASE_URL from Render
# 2. Run: $env:DATABASE_URL='postgresql+asyncpg://...'; .\run-scraper-to-neon.ps1
#    Or set it in backend\.env (Neon URL, not localhost)

$backend = Join-Path $PSScriptRoot "backend"
if (-not (Test-Path $backend)) {
    Write-Host "backend folder not found" -ForegroundColor Red
    exit 1
}

$dbUrl = $env:DATABASE_URL
if (-not $dbUrl -or $dbUrl -match "localhost|postgres:5432") {
    Write-Host ""
    Write-Host "DATABASE_URL must point to Neon (not localhost)." -ForegroundColor Yellow
    Write-Host "1. Go to Render Dashboard -> pak-bank-backend -> Environment" -ForegroundColor Gray
    Write-Host "2. Copy DATABASE_URL (postgresql+asyncpg://...@...neon.tech/...)" -ForegroundColor Gray
    Write-Host "3. Run: " -ForegroundColor Gray
    Write-Host '   $env:DATABASE_URL="your-neon-url"; .\run-scraper-to-neon.ps1' -ForegroundColor White
    Write-Host ""
    Write-Host "Or add it to backend\.env and run: .\run-scraper-to-neon.ps1" -ForegroundColor Gray
    exit 1
}

Write-Host ""
Write-Host "Running scraper locally (populates Neon, 4000+ deals in 5-15 min)..." -ForegroundColor Cyan
Write-Host ""

Push-Location $backend
try {
    python scripts/run_scrape_deals_only.py
    $code = $LASTEXITCODE
    Write-Host ""
    if ($code -eq 0) {
        Write-Host "Done. Refresh pak-bank-discounts-ai.netlify.app to see the deals." -ForegroundColor Green
    } else {
        Write-Host "Scraper exited with code $code. Check errors above." -ForegroundColor Red
    }
    exit $code
} finally {
    Pop-Location
}
