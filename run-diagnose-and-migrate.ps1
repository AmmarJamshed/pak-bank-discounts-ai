# Diagnose local vs Neon DB and optionally migrate deals
# The 4000+ deals were in LOCAL Docker Postgres; production uses Neon. They're different DBs.

param(
    [switch]$Migrate = $false,
    [switch]$Diagnose = $true,
    [switch]$SyncSources = $false,
    [switch]$SeedAllSources = $false
)

$local = "postgresql+asyncpg://postgres:postgres@localhost:5432/pakbank"
$neon = $env:TARGET_DATABASE_URL
if (-not $neon) {
    $neon = "postgresql+asyncpg://neondb_owner:npg_cP9qE5XafIvW@ep-lingering-credit-ai6ydlsd-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require"
}

Write-Host "Local DB: localhost:5432/pakbank (Docker must be running)" -ForegroundColor Cyan
Write-Host "Neon DB:  ep-lingering-credit-ai6ydlsd.neon.tech" -ForegroundColor Cyan
Write-Host ""

if ($Diagnose) {
    Write-Host "=== Running diagnosis ===" -ForegroundColor Yellow
    $env:SOURCE_DATABASE_URL = $local
    $env:TARGET_DATABASE_URL = $neon
    Push-Location backend
    python scripts/diagnose_db.py
    Pop-Location
}

if ($Migrate) {
    Write-Host ""
    Write-Host "=== Running migration (local -> Neon) ===" -ForegroundColor Yellow
    $env:SOURCE_DATABASE_URL = $local
    $env:TARGET_DATABASE_URL = $neon
    Push-Location backend
    python scripts/migrate_local_to_neon.py
    Pop-Location
    Write-Host ""
    Write-Host "Done. Refresh the site to see updated deal count." -ForegroundColor Green
}

if ($SyncSources) {
    Write-Host ""
    Write-Host "=== Syncing sources (local banks with deals -> Neon) ===" -ForegroundColor Yellow
    $env:SOURCE_DATABASE_URL = $local
    $env:TARGET_DATABASE_URL = $neon
    Push-Location backend
    python scripts/sync_sources_to_neon.py
    Pop-Location
}

if ($SeedAllSources) {
    Write-Host ""
    Write-Host "=== Seeding all SOURCES into Neon ===" -ForegroundColor Yellow
    $env:TARGET_DATABASE_URL = $neon
    Push-Location backend
    python scripts/sync_sources_to_neon.py --seed-all
    Pop-Location
}
