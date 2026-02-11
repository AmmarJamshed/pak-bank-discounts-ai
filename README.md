# Pak Bank Discounts Intelligence Platform

Pakistan's first unified bank discount intelligence portal. It scrapes live deals using SERP API, ranks them with a hybrid recommendation engine, and powers a Groq-based AI concierge.

## Stack

- **Frontend:** Next.js 14 (App Router) + Tailwind CSS (Netlify-ready)
- **Backend:** FastAPI + Async scraping engine + PostgreSQL
- **AI:** Groq LLM API + SERP API + RAG with FAISS

## Project Structure

```
D:\pak-bank-discounts-ai
  backend/
    app/
      core/
      db/
      routers/
      services/
      tasks/
    data/
  frontend/
    app/
    components/
    lib/
    styles/
```

## Environment Variables

Backend uses `backend/.env`:

```
SERP_API_KEY=your_serp_api_key
GROQ_API_KEY=your_groq_api_key
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/pakbank
FAISS_INDEX_PATH=D:\pak-bank-discounts-ai\backend\data\faiss.index
FAISS_METADATA_PATH=D:\pak-bank-discounts-ai\backend\data\faiss_metadata.json
SCRAPE_INTERVAL_HOURS=12
```

Frontend uses `frontend/.env.local`:

```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## Local Development

### 1) Start PostgreSQL + Backend

```
cd D:\pak-bank-discounts-ai
docker compose up --build
```

FastAPI runs at `http://localhost:8000`.

### 2) Start Frontend

```
cd D:\pak-bank-discounts-ai\frontend
npm install
npm run dev
```

Next.js runs at `http://localhost:3000`.

## Backend API Endpoints

- `GET /discounts` – filter by city, category, bank, card_type, intent
- `GET /banks` – list banks
- `GET /banks/{bank_id}` – bank + cards
- `POST /ai/chat` – AI assistant response
- `GET /ai/stream?query=...` – streaming AI response (SSE)
- `GET /admin/analytics` – dashboard analytics
- `GET /admin/trends` – discount trend + forecast
- `GET /admin/insights` – bank-wise insights + affiliate readiness

## AI Pipeline

User query → FAISS vector search → SQL discounts → SERP API fallback → Groq reasoning → response

## Scraping Engine

- SERP API discovers new discount pages
- Async fetch + parsing
- Normalization, de-duplication, and expiry handling
- Runs every 12 hours via scheduler

## Deployment

### Backend (Railway / Fly.io)

- Build from `backend/Dockerfile`
- Set environment variables from `backend/.env`

### Frontend (Netlify)

- Build command: `npm run build`
- Base directory: `frontend`
- Publish directory: `.next`
- Netlify plugin: `@netlify/plugin-nextjs`

## Notes

- First startup triggers initial scrape and FAISS index build.
- Admin dashboard is under `/admin` on the frontend.
