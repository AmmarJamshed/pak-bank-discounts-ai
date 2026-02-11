# Deployment Guide

## Frontend (Netlify)

### Option A: Deploy via GitHub (Recommended – avoids CLI Blobs error)

1. Create a GitHub repo and push:
   ```powershell
   git remote add origin https://github.com/YOUR_USERNAME/pak-bank-discounts-ai.git
   git push -u origin master
   ```

2. Go to [app.netlify.com](https://app.netlify.com) → Add new site → Import from Git
3. Connect your GitHub and select `pak-bank-discounts-ai`
4. Build settings:
   - Base directory: `frontend`
   - Build command: `npm run build`
   - Publish directory: `frontend/.next`

5. After backend is deployed, add env var:
   - `NEXT_PUBLIC_API_BASE_URL` = your backend URL (e.g. `https://pak-bank-backend.onrender.com`)

### Option B: Deploy via CLI (may hit Blobs error)

```powershell
cd frontend
netlify link --name pak-bank-discounts-ai   # if not linked
netlify deploy --prod
```

## Backend (Render)

1. Go to [dashboard.render.com](https://dashboard.render.com) → New → Blueprint
2. Connect your GitHub repo (`pak-bank-discounts-ai`)
3. Render will detect `render.yaml` and create:
   - PostgreSQL database: `pakbank-db`
   - Web service: `pak-bank-backend`

4. In the backend service → Environment, add:
   - `SERP_API_KEY` (from your backend/.env)
   - `GROQ_API_KEY` (from your backend/.env)

5. `DATABASE_URL` is auto-injected from the linked Postgres
6. After deploy, your API URL will be like: `https://pak-bank-backend.onrender.com`

## Link Frontend to Backend

Once the backend is live:

1. Netlify → Your site → Site settings → Environment variables
2. Add `NEXT_PUBLIC_API_BASE_URL` = `https://pak-bank-backend.onrender.com` (use your actual Render URL)
3. Trigger a redeploy (Deploys → Trigger deploy)
