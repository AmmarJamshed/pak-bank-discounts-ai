# Remaining Steps — Do These Now

**Quick link:** Open `docs/pythonanywhere-setup-wizard.html` for a step-by-step wizard with copy buttons.

---

## 1. Pull latest code (if you cloned before)

```bash
cd ~/pak-bank-discounts-ai
git pull
```

---

## 2. Create Web App

### Option A: CLI (recommended)

1. Get API token: [Account → API Token](https://www.pythonanywhere.com/account/)
2. Run:

```bash
cd ~/pak-bank-discounts-ai/backend
source venv/bin/activate
pip install a2wsgi
export PYTHONANYWHERE_API_TOKEN=YOUR_TOKEN
pa website create --domain ammarjamshed123.pythonanywhere.com --command '/home/ammarjamshed123/pak-bank-discounts-ai/backend/venv/bin/uvicorn --app-dir /home/ammarjamshed123/pak-bank-discounts-ai/backend --uds ${DOMAIN_SOCKET} app.main:app'
```

### Option B: Manual (if CLI fails)

1. [Web tab](https://www.pythonanywhere.com/user/ammarjamshed123/webapps/) → Add a new web app
2. Manual configuration → Python 3.10
3. Source code: `/home/ammarjamshed123/pak-bank-discounts-ai/backend`
4. WSGI file: `/home/ammarjamshed123/pak-bank-discounts-ai/backend/wsgi.py`
5. Reload

---

## 3. Run Scraper (load deals)

```bash
cd ~/pak-bank-discounts-ai/backend
source venv/bin/activate
python scripts/run_scrape.py
```

Wait 2–5 minutes.

---

## 4. Verify

- **Backend:** https://ammarjamshed123.pythonanywhere.com/health
- **Deals:** https://ammarjamshed123.pythonanywhere.com/discounts?limit=10
- **Frontend:** https://pak-bank-discounts-ai.netlify.app
