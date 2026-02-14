# Fix: Render Showing 1,247 Instead of 5,452 Deals

## Root Cause

**Render is using a different database** than the one we populated. We have **5,452 deals** in Neon, but Render's `DATABASE_URL` points to another DB with only 1,247.

## Fix (2 minutes)

1. Go to **Render Dashboard**: https://dashboard.render.com
2. Open **pak-bank-backend**
3. Go to **Environment**
4. Find **DATABASE_URL** and set it to this exact value (same DB we populated):

```
postgresql://neondb_owner:npg_cP9qE5XafIvW@ep-lingering-credit-ai6ydlsd-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require
```

Or if Render expects the asyncpg format:

```
postgresql+asyncpg://neondb_owner:npg_cP9qE5XafIvW@ep-lingering-credit-ai6ydlsd-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require
```

5. Click **Save**
6. Render will auto-redeploy (~3–5 min)
7. Refresh https://pak-bank-discounts-ai.netlify.app — you should see **5,452+ deals**

## Verify

After redeploy, check:
- https://pak-bank-backend.onrender.com/admin/analytics → `total_discounts` should be **5,452+**
- https://pak-bank-discounts-ai.netlify.app → banner should show **5,452+ deals**

## If You See 502 After Redeploy

1. **Check Render logs** (Dashboard → pak-bank-backend → Logs) for startup errors.
2. **Skip bootstrap** if the DB is already populated:
   - Environment → set `SKIP_BOOTSTRAP` = `true`
   - This prevents scrape+RAG on every deploy; use GitHub Actions / cron for scraping.
3. **Confirm env vars**: `DATABASE_URL`, `SERP_API_KEY`, `GROQ_API_KEY` must be set.
