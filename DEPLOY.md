# Deployment Guide

## Frontend (Netlify)

### Link to GitHub (site `pak-bank-discounts-ai` exists, manual deploys)

1. **Grant Netlify access to the repo** (required if repo doesn’t appear in the list):
   - Open [GitHub App settings](https://github.com/settings/installations)
   - Find **Netlify** → Configure
   - Under “Repository access”, add `AmmarJamshed/pak-bank-discounts-ai`
   - Save

2. **Link repository**:
   - [Netlify project](https://app.netlify.com/projects/pak-bank-discounts-ai) → **Build & deploy** → **Link repository**
   - Choose **GitHub** and select `AmmarJamshed/pak-bank-discounts-ai`
   - Build settings (from `netlify.toml`):
     - Base directory: `frontend`
     - Build command: `npm run build`
     - Publish directory: `.next` (handled by `@netlify/plugin-nextjs`)

3. **Environment variable** (already set):
   - `NEXT_PUBLIC_API_BASE_URL` = `https://pak-bank-backend.onrender.com`

4. First deploy runs automatically after linking. For later deploys, push to `main` to trigger builds.

### Option B: Deploy via CLI (may hit Blobs error)

```powershell
cd frontend
netlify link --name pak-bank-discounts-ai   # if not linked
netlify deploy --prod
```

## Backend (Render) – Deployed

Blueprint `pak-bank-discounts` is deployed at [Render](https://dashboard.render.com/blueprint/exs-d66d873h46gs739pgb1g/resources).

**Required: add env vars to `pak-bank-backend` service**

1. Open [Blueprint Resources](https://dashboard.render.com/blueprint/exs-d66d873h46gs739pgb1g/resources)
2. Click `pak-bank-backend` (or find it under the main dashboard)
3. Go to **Environment** and add:
   - `SERP_API_KEY` (from your `backend/.env`)
   - `GROQ_API_KEY` (from your `backend/.env`)
4. Save and redeploy. `DATABASE_URL` is already provided by the blueprint.
5. API URL: `https://pak-bank-backend.onrender.com`

## Link Frontend to Backend

Once the backend is live:

1. Netlify → Your site → Site settings → Environment variables
2. Add `NEXT_PUBLIC_API_BASE_URL` = `https://pak-bank-backend.onrender.com` (use your actual Render URL)
3. Trigger a redeploy (Deploys → Trigger deploy)
