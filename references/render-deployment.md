# OpenClaw Superswarm v3.0 — Render Deployment Guide

## Quick Deploy (60 seconds)

### 1. Push to GitHub
```bash
git clone https://github.com/d74117157-create/openclaw-bot.git
cd openclaw-bot
cp -r /path/to/superswarm-v3/* .
git add .
git commit -m "Superswarm v3.0 — JWT Empire API + Multi-Platform Bots"
git push origin main
```

### 2. Render Dashboard Setup
1. Go to [dashboard.render.com](https://dashboard.render.com)
2. Click **New +** → **Web Service**
3. Connect `d74117157-create/openclaw-bot`
4. Select branch: `main`
5. Render will auto-detect `render.yaml` (Blueprint)

### 3. Environment Variables
Paste these EXACT values in Render → Environment:

```
JWT_SECRET_KEY=<YOUR-STRONG-32-BYTE-SECRET-HERE>
EMPIRE_PASSWORD=<YOUR-COLONEL-PASSWORD-HERE>
EMPIRE_STATE_PATH=/data/empire-state.json
XAI_API_KEY=<YOUR-XAI-GROK-KEY-HERE>
GROQ_API_KEY=<YOUR-GROQ-KEY-HERE>
PORT=10000
DISCORD_TOKEN=<YOUR-DISCORD-BOT-TOKEN>
TELEGRAM_BOT1_TOKEN=<YOUR-TELEGRAM-BOT1-TOKEN>
TELEGRAM_BOT2_TOKEN=<YOUR-TELEGRAM-BOT2-TOKEN>
TELEGRAM_BOT3_TOKEN=<YOUR-TELEGRAM-BOT3-TOKEN>
SLACK_BOT_TOKEN=<YOUR-SLACK-BOT-TOKEN>
SLACK_APP_TOKEN=<YOUR-SLACK-APP-TOKEN>
GOOGLE_API_KEY=<YOUR-GOOGLE-API-KEY>
BINANCE_API_KEY=<YOUR-BINANCE-KEY>
BINANCE_SECRET_KEY=<YOUR-BINANCE-SECRET>
```

**⚠️ CRITICAL:** Change `JWT_SECRET_KEY` and `EMPIRE_PASSWORD` to strong, unique values BEFORE deploying.

### 4. Add 1GB Disk
- Render → Settings → Disks
- Name: `empire-data`
- Mount Path: `/data`
- Size: `1 GB`

### 5. Deploy
Click **Deploy**. Render will:
1. Install requirements
2. Mount `/data` disk
3. Start `master_orchestrator.py`
4. Expose FastAPI on port 10000

## Post-Deploy Verification

```bash
# Health check
curl https://your-service.onrender.com/health

# Login (get JWT token)
curl -X POST https://your-service.onrender.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"password": "<YOUR-COLONEL-PASSWORD>"}'

# Empire status (use token from above)
curl https://your-service.onrender.com/empire/status \
  -H "Authorization: Bearer <token>"
```

## Architecture
- **master_orchestrator.py** — Entry point, boots all engines
- **fastapi_superswarm_api.py** — JWT-secured REST API
- **superswarm.py** — 7-agent swarm core
- **product_factory.py** — Digital product generation
- **platform_engine.py** — Discord + 3x Telegram + Slack + YouTube
- **marketing_engine.py** — Content factories + revenue tracking

## Files Generated
All files are in the repo root and `assets/` / `references/` directories.
