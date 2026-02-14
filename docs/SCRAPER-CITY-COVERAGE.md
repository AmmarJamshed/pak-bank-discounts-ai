# Scraper City Coverage – Not Limited to Karachi

## Summary

**The scraper does NOT only explore Karachi.** It covers all of Pakistan.

## Current City Distribution (Neon)

| City        | Deals |
|------------|-------|
| Karachi     | 1,228 |
| Lahore      | 552   |
| Islamabad   | 184   |
| Multan      | 72    |
| Faisalabad  | 57    |
| Peshawar    | 16    |
| Rawalpindi  | 14    |
| Gujranwala  | 13    |
| Sialkot     | 13    |
| Hyderabad   | 8     |
| Quetta      | 4     |
| **Total**   | **2,161** |

Karachi has the most because:
1. **Peekaboo** (HBL, Meezan, Bank Alfalah, BOP): Fetches per city; Karachi has the largest merchant set.
2. **Text extraction** (non-Peekaboo banks): `_guess_city(line)` defaults to Karachi when no city is in the text.

## How It Works

### Peekaboo banks (4 banks)
- Iterate over `KNOWN_CITIES` (20 cities after expansion).
- Each city is queried separately.
- Deals are tagged with the correct city.

### Non-Peekaboo banks (SERP + HTML)
- Parse bank pages for deals.
- City inferred from text; if missing → default Karachi.
- Total deal count is not reduced; only city assignment changes.

## Changes Made

1. **City list** – Expanded from 11 to 20 cities:
   - Added: Bahawalpur, Sargodha, Sukkur, Larkana, Mingora, Muzaffarabad, Mirpur, Abbottabad, Dera Ismail Khan

2. **Peekaboo fix** – Ignore non-dict responses (`if not isinstance(entity, dict): continue`).

3. **City aliases** – Extended `CITY_ALIASES` in `normalizer.py` for the new cities.

## Why Under 4,000 Deals?

- **Peekaboo data**: Per-city data may be limited; new cities may have few merchants.
- **Local DB**: The ~4,000 deals were in local Postgres; production uses Neon.
- **Migration**: Requires Docker to copy local Postgres → Neon.

## Reaching 4,000+

1. **Docker + migration** (if local still has ~4,000 deals):
   ```powershell
   docker compose up -d postgres
   .\run-diagnose-and-migrate.ps1 -Migrate
   ```

2. **Redeploy backend** – Ensure Render runs the latest scraper and fixes.

3. **Run scraper locally** – Use `.\run-scraper-to-neon.ps1` with Neon `DATABASE_URL` for full runs.
