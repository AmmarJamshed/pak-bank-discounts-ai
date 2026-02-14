# Root Cause: Why 4,000+ Deals Don't Show in Production

## Summary

**Local (localhost)** had 4,000+ deals because it used **Docker Postgres** — a completely separate database.  
**Production (Render)** uses **Neon** — which only has ~1,230 deals. They are different databases. The 4,000+ deals were never in Neon.

## Database Layout

| Environment | Database          | Connection                                                                 |
|-------------|-------------------|----------------------------------------------------------------------------|
| Local       | Docker Postgres   | `postgresql+asyncpg://postgres:postgres@localhost:5432/pakbank`            |
| Production  | Neon (Render)     | `postgresql+asyncpg://neondb_owner:...@ep-lingering-credit-ai6ydlsd-pooler...neon.tech/neondb` |

- `.env` in backend uses `postgres:5432` when running inside Docker (service name `postgres`)
- When running scripts from the host, use `localhost:5432` to reach the same Postgres

## Why Production Has Fewer Deals

1. **Render scrapes time out** — Free tier sleeps after inactivity; long scrapes fail.
2. **Local scraper was never run against Neon** — Or was run with a different `DATABASE_URL`.
3. **Local Postgres accumulated deals** — From many successful local scrapes.

## Fix: Migrate Local Data to Neon

### 1. Start local Postgres

```powershell
docker compose up -d postgres
```

### 2. Diagnose (verify local has 4,000+)

```powershell
.\run-diagnose-and-migrate.ps1
```

Or manually:

```powershell
cd backend
$env:SOURCE_DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/pakbank"
$env:TARGET_DATABASE_URL="postgresql+asyncpg://neondb_owner:npg_cP9qE5XafIvW@ep-lingering-credit-ai6ydlsd-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require"
python scripts/diagnose_db.py
```

### 3. Migrate local → Neon

```powershell
.\run-diagnose-and-migrate.ps1 -Migrate
```

Or manually:

```powershell
cd backend
$env:SOURCE_DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/pakbank"
$env:TARGET_DATABASE_URL="postgresql+asyncpg://neondb_owner:npg_cP9qE5XafIvW@ep-lingering-credit-ai6ydlsd-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require"
python scripts/migrate_local_to_neon.py
```

### 4. Verify production

Visit https://pak-bank-discounts-ai.netlify.app — deal count should increase.

## Sync Sources (Banks) for Future Fetching

Sources are now persisted in `scrape_sources`. When populated, the scraper uses them instead of hardcoded SOURCES.

**From local** (copy only banks that had deals):
```powershell
.\run-diagnose-and-migrate.ps1 -SyncSources
```

**Seed all** 14 sources (no local needed):
```powershell
.\run-diagnose-and-migrate.ps1 -SeedAllSources
```

Or directly:
```powershell
cd backend
$env:TARGET_DATABASE_URL="postgresql+asyncpg://neondb_owner:...@ep-xxx.neon.tech/neondb?sslmode=require"
python scripts/sync_sources_to_neon.py --seed-all
```

Already run: all 14 sources are saved in Neon.

## If Local Postgres Has No Data

If Docker was recreated or volumes were removed, the local DB may be empty. Then:

1. Run full scrape locally against **Neon** (so production gets the data):

   ```powershell
   $env:DATABASE_URL="postgresql+asyncpg://neondb_owner:npg_cP9qE5XafIvW@ep-lingering-credit-ai6ydlsd-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require"
   .\run-scraper-to-neon.ps1
   ```

2. This populates Neon directly. Render will read the same data.

## API Limitation Check

The `/discounts` API has `limit=5000` and filters out deals with unreadable merchant names (`_is_readable`). That can reduce the displayed count slightly, but the main gap is database content, not API limits.
