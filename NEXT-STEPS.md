# Final setup steps

## 1. Add API keys to backend (Render)

The backend will fail to start without these. Add them in Render:

1. Go to https://dashboard.render.com/blueprint/exs-d66d873h46gs739pgb1g/resources
2. Click **pak-bank-backend** (when it appears – it may still be building)
3. **Environment** → **Add environment variable**:
   - `SERP_API_KEY` = (from `backend/.env`)
   - `GROQ_API_KEY` = (from `backend/.env`)
4. **Save changes** – Render will redeploy automatically
5. Wait for deploy to finish; backend URL: **https://pak-bank-backend.onrender.com**

## 2. Connect Netlify to GitHub

1. Go to https://app.netlify.com and log in
2. **Add new site** → **Import an existing project** → **Deploy with GitHub**
3. Choose **AmmarJamshed/pak-bank-discounts-ai**
4. Build settings:
   - Base directory: `frontend`
   - Build command: `npm run build`
   - Publish directory: `frontend/.next`
5. **Add environment variable**:
   - Key: `NEXT_PUBLIC_API_BASE_URL`
   - Value: `https://pak-bank-backend.onrender.com`
6. **Deploy site**

## 3. Done

- Frontend: your Netlify URL (e.g. `https://something.netlify.app`)
- Backend: `https://pak-bank-backend.onrender.com`
