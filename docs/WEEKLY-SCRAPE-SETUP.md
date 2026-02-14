# Weekly Scrape Setup

The backend scrapes deals every week via **GitHub Actions** (free). During the scrape, the site shows a "Website in weekly maintenance" banner. Scrapes run in under 1 hour.

## One-time: Add GitHub secret

1. Go to your repo → **Settings** → **Secrets and variables** → **Actions**
2. New repository secret:
   - Name: `RENDER_TRIGGER_SCRAPE_URL`
   - Value: `https://pak-bank-backend-637y.onrender.com/admin/trigger-scrape`  
     (or your Render backend URL + `/admin/trigger-scrape`)

## Schedule

- **Automatic**: Every Sunday at 02:00 UTC (~07:00 Pakistan time)
- **Manual**: Repo → Actions → "Weekly Scrape" → Run workflow

## First-time data

On a fresh deploy, the database is empty. Either:

1. Manually run the workflow (Actions → Weekly Scrape → Run workflow), or  
2. Use the Admin page to trigger a scrape, or  
3. `curl -X POST https://YOUR_BACKEND/admin/trigger-scrape`

## Caching

The frontend caches the last successful deals response in `localStorage` for 7 days. Visitors see cached deals immediately (no wait), then fresh data loads in the background.
