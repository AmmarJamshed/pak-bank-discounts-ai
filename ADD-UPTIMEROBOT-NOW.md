# Add UptimeRobot Monitor (2 minutes)

Keeps your Render backend awake so visitors never wait 50+ seconds for cold start.

## Option A: Via Dashboard (no API key)

1. **Log in** at https://dashboard.uptimerobot.com
2. Click **+ Add New Monitor**
3. Use these values:
   - **Monitor Type:** HTTP(s)
   - **Friendly Name:** Pak Bank Backend
   - **URL:** `https://pak-bank-backend.onrender.com/health`
   - **Monitoring Interval:** 5 minutes
4. Click **Create Monitor** ✓

## Option B: Via Script (with API key)

1. Get API key: https://dashboard.uptimerobot.com → My Settings → Integrations & API → API
2. In PowerShell:
   ```powershell
   cd d:\pak-bank-discounts-ai
   .\tools\add-uptimerobot-monitor.ps1
   ```
3. Paste your API key when prompted
