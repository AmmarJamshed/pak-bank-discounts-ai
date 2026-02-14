# Deploy Backend to Render (bypasses PythonAnywhere CPU limit)

Your PythonAnywhere CPU quota is used up. Deploy to Render instead — free, no CPU limit.

## 1. Create Web Service on Render

1. Go to **https://dashboard.render.com** → Sign in with GitHub
2. Click **New +** → **Web Service**
3. Connect repository: **AmmarJamshed/pak-bank-discounts-ai**
4. Configure:
   - **Name:** `pak-bank-backend`
   - **Region:** Oregon
   - **Branch:** main
   - **Root Directory:** (leave empty)
   - **Runtime:** Docker
   - **Dockerfile Path:** `backend/Dockerfile`
   - **Docker Build Context Path:** `backend`

## 2. Add Environment Variables

In **Environment** section, add:

| Key | Value |
|-----|-------|
| `DATABASE_URL` | `postgresql+asyncpg://neondb_owner:npg_cP9qE5XafIvW@ep-lingering-credit-ai6ydlsd-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require` |
| `SERP_API_KEY` | (your key from .env) |
| `GROQ_API_KEY` | (your key from .env) |
| `FAISS_INDEX_PATH` | `/tmp/faiss.index` |
| `FAISS_METADATA_PATH` | `/tmp/faiss_meta.json` |
| `SKIP_BOOTSTRAP` | `false` |
| `DISABLE_SCHEDULER` | `true` |

## 3. Deploy

Click **Create Web Service**. Wait 5–10 min for build + deploy.

## 4. Trigger Scraper (after deploy)

Once live, run scraper:
```bash
curl -X POST https://pak-bank-backend-637y.onrender.com/admin/trigger-scrape
```

## 5. Frontend (Netlify)

`netlify.toml` already sets `NEXT_PUBLIC_API_BASE_URL = "https://pak-bank-backend-637y.onrender.com"`.
Push to GitHub and Netlify will auto-redeploy, or trigger a manual deploy.

---

**Live backend:** https://pak-bank-backend-637y.onrender.com
