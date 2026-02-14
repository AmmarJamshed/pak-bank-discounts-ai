# Scale to 4000+ Deals (Sellable Volume)

You had 4000+ deals on localhost because the scraper runs to completion there. **Render free tier times out** mid-scrape. The fix: **run the scraper locally** against the same Neon DB that Render uses.

## Run Scraper Locally (Restores 4000+)

```powershell
# 1. Get DATABASE_URL from Render: Dashboard -> pak-bank-backend -> Environment
# 2. Run (use YOUR Render's Neon URL):
$env:DATABASE_URL="postgresql+asyncpg://...@...neon.tech/neondb?sslmode=require"
$env:SERP_API_KEY="your-key"
$env:GROQ_API_KEY="your-key"
.\run-scraper-to-neon.ps1
```

Or: `cd backend && python scripts/run_scrape_deals_only.py` with those env vars set.

Takes 10–20 minutes. Once done, refresh the site — deals come from Neon.

---

## Banks Added (14 total, was 10)

- **MCB Bank** – mcb.com.pk
- **Allied Bank** – abl.com
- **Askari Bank** – askaribank.com
- **Faysal Bank** – digimall.faysalbank.com

## 3-Process Weekly Sync (new + expired + updated)

Each weekly scrape now runs three operations per bank in one pass:

1. **NEW** – Insert deals not previously cached  
2. **EXPIRED** – Remove deals no longer on the bank’s website  
3. **UPDATED** – Replace deals where percent/conditions changed (e.g. 25% → 30%)

## Scraper Code Changes (already in codebase)

1. **Peekaboo** (Meezan, Bank Alfalah, HBL, BOP):
   - Page size: 12 → **50** entities per request
   - Pagination: 3 → **30** pages per city
   - 9 cities × 30 pages × 50 = up to 13,500 deals per bank

2. **SERP** (UBL, Standard Chartered, BankIslami, etc.):
   - Search results: 10 → **100** URLs per bank for discovery

## After Backend Deploys

1. **Trigger a full scrape:**
   ```powershell
   Invoke-RestMethod -Uri "https://pak-bank-backend.onrender.com/admin/trigger-scrape" -Method Post
   ```
   Or: [Admin page](https://pak-bank-discounts-ai.netlify.app/admin) → trigger scrape (if available)

2. **Or use GitHub Actions:** Repo → Actions → "Weekly Scrape" → Run workflow

3. **Wait 15–45 minutes** for the scrape to complete (depends on SERP API + Peekaboo latency)

4. **Verify:** [pak-bank-discounts-ai.netlify.app](https://pak-bank-discounts-ai.netlify.app) — deal count should increase

## If Still Under 4000

- **Add more banks** to `backend/app/services/scraper.py` SOURCES
- **Check Peekaboo**: Some banks may cap API responses; review logs in Render
- **SERP API**: 100 searches/week free tier; paid plan for higher volume
