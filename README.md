# 🐾 OpenClaw Elite - Complete Swarm Documentation

**Your AI Swarm. Your Empire. Your Documentation.**

---

## 📁 Repository Structure

```
openclaw-bot/
├── victor.py                  ← 🧠 MASTER ORCHESTRATOR (talk to this)
├── main.py                    ← 🚀 Entry point for Render (starts everything)
├── automation/
│   ├── youtube_pipeline.py    ← 📹 YouTube content creation
│   └── trading_signals.py     ← 📈 Crypto trading signals
├── agents/
│   ├── victor.py              ← Victor orchestrator agent
│   ├── claude.py              ← Claude coder agent
│   └── ...                    ← Other agent personalities
├── memory/                    ← Swarm memory & state
├── scripts/
│   ├── start.sh               ← Render start script
│   └── test_imports.py        ← Import verification
├── terraform/                 ← OCI VM provisioning
├── .github/workflows/         ← Auto-deploy pipelines
├── logs/                      ← Runtime logs
├── data/                      ← Data storage
└── requirements.txt           ← Python dependencies
```

---

## 🗣️ HOW TO TALK TO YOUR SWARM

### Method 1: Direct Command (Terminal/SSH)
```bash
python3 victor.py "make a youtube video about crypto"
python3 victor.py "check the markets"
python3 victor.py "health check"
python3 victor.py "broadcast hello world"
```

### Method 2: Telegram (Bots 1, 2, 3, Super)
Just message any of your bots naturally:
- "make me a video"
- "what are the trading signals"
- "status report"

### Method 3: Discord
Tag your bot or use the configured channel. Same natural language.

### Method 4: Slack
DM the bot or post in the integrated channel.

### Method 5: Render Dashboard (Manual Trigger)
Go to your Render dashboard → Shell → run:
```bash
cd /app && python3 victor.py "your command here"
```

---

## 🎬 YOUTUBE CONTENT PIPELINE

### What It Does
1. **Fetches trending topics** from YouTube API (using your GOOGLE_API_KEY)
2. **Generates a script** with hook, body, CTA
3. **Creates a project folder** with all instructions ready

### How to Run
```bash
python3 automation/youtube_pipeline.py [NICHE] [REGION]
```

**Examples:**
```bash
python3 automation/youtube_pipeline.py tech US
python3 automation/youtube_pipeline.py crypto US
python3 automation/youtube_pipeline.py gaming GB
```

### Output
Creates a folder in `/tmp/youtube_projects/project_YYYYMMDD_HHMMSS/` containing:
- `script.json` — the full script
- `INSTRUCTIONS.txt` — step-by-step rendering guide

### Next Steps (Manual for now)
1. Read the script
2. Use CapCut, Canva, or Pictory to create the video
3. Upload to YouTube

**Future:** Auto-render with ffmpeg + text-to-speech (coming in v2)

---

## 📈 TRADING SIGNALS PIPELINE

### What It Does
1. **Scans Binance** for BTC, ETH, SOL, DOGE, ADA, XRP, DOT
2. **Analyzes momentum** (24h change + volume)
3. **Generates signals**: STRONG_BUY, BUY, STRONG_SELL, SELL, HOLD
4. **Posts to all platforms** automatically

### How to Run
```bash
# Scan all symbols
python3 automation/trading_signals.py

# Get top opportunity only
python3 automation/trading_signals.py --top
```

### No Account Needed
Uses free Binance public API. No API keys required.

---

## 🧠 VICTOR ORCHESTRATOR COMMANDS

Victor understands natural language. Just say what you want:

| What You Say | What Happens |
|---|---|
| "make a youtube video" | Runs YouTube pipeline, posts to all platforms |
| "check the markets" | Runs trading signals, posts top opportunity |
| "health check" | System status report to all platforms |
| "broadcast [message]" | Posts your message everywhere |
| "help" | Shows all available commands |
| "create content about [topic]" | YouTube pipeline with custom niche |

---

## ⚙️ ENVIRONMENT VARIABLES (Render)

Set these in your Render dashboard → Environment:

| Variable | What It Is | Where to Get It |
|---|---|---|
| `DISCORD_TOKEN` | Your Discord bot token | Discord Developer Portal |
| `TELEGRAM_BOT_TOKEN_1` | Bot 1 token | @BotFather |
| `TELEGRAM_BOT_TOKEN_2` | Bot 2 token | @BotFather |
| `TELEGRAM_BOT_TOKEN_3` | Bot 3 token | @BotFather |
| `TELEGRAM_BOT_TOKEN_SUPER` | Super bot token | @BotFather |
| `SLACK_APP_TOKEN` | Slack app token | Slack API |
| `SLACK_BOT_TOKEN` | Slack bot token | Slack API |
| `GOOGLE_API_KEY` | YouTube Data API | Google Cloud Console |
| `DISCORD_WEBHOOK_URL` | Discord webhook | Server Settings → Integrations |
| `SLACK_WEBHOOK_URL` | Slack webhook | Slack App → Incoming Webhooks |
| `GITHUB_TOKEN` | GitHub PAT | GitHub Settings → Developer |
| `RENDER_API_KEY` | Render API key | Render Dashboard |
| `OCI_HOST` | Oracle VM IP | OCI Console |
| `OCI_USER` | Oracle VM user | Usually `opc` |
| `OCI_SSH_KEY` | SSH private key | Generated during VM setup |

---

## 🚀 HOW TO DEPLOY

### Auto-Deploy (GitHub → Render)
1. Push code to GitHub: `d74117157-create/openclaw-bot`
2. Render auto-deploys from `main` branch
3. Check: https://openclaw-bot.onrender.com

### Manual Deploy (Render Dashboard)
1. Go to https://dashboard.render.com
2. Select service: `srv-d978fh6puehc73fkq60g`
3. Click "Manual Deploy" → "Deploy Latest Commit"

### Deploy Hook (Fastest)
```bash
curl https://api.render.com/deploy/srv-d978fh6puehc73fkq60g?key=YOUR_DEPLOY_HOOK_KEY
```

### Deploy to Oracle Cloud (Backup)
```bash
# GitHub Actions runs automatically on push
# Or manually:
terraform apply terraform/oci-vm.tf
```

---

## 📊 MONITORING & LOGS

### Check Logs
```bash
# Render logs (web dashboard)
# Or SSH into Render shell:
tail -f logs/orchestrator.log
```

### Health Check
```bash
python3 victor.py "health check"
```

### FastAPI Health Server
```bash
curl https://openclaw-bot.onrender.com/health
```

---

## 🔄 AUTOMATION SCHEDULE (Cron Jobs)

Your swarm can run on a schedule. Edit `main.py` or use Render Cron:

| Time | Task |
|---|---|
| Every 6 hours | Trading signal scan |
| Daily 9am | YouTube content generation |
| Daily 12pm | Health check broadcast |
| Weekly | Full system report |

To set up: Add cron jobs in Render or use the built-in scheduler in `main.py`.

---

## 🆘 TROUBLESHOOTING

### "Import Error"
```bash
pip install -r requirements.txt
```

### "No Telegram chat IDs found"
Send a message to your bot first, then run again.

### "Discord webhook failed"
Check `DISCORD_WEBHOOK_URL` is set correctly in Render env.

### "YouTube API error"
Verify `GOOGLE_API_KEY` is set and has YouTube Data API v3 enabled.

### Bot not responding
Check Render service is running: https://openclaw-bot.onrender.com

---

## 🎯 YOUR NEXT STEPS

1. **Set all env vars** in Render dashboard
2. **Send a test message** to each Telegram bot
3. **Run**: `python3 victor.py "health check"`
4. **Run**: `python3 victor.py "make a youtube video"`
5. **Run**: `python3 victor.py "check the markets"`
6. **Watch your platforms** — signals and content will appear

---

## 🏗️ ARCHITECTURE

```
┌─────────────────┐
│   YOU (Human)   │
└────────┬────────┘
         │ Talk naturally
         ▼
┌─────────────────┐
│  VICTOR (Brain) │ ← Parses intent, routes commands
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌──────────┐
│YouTube │ │ Trading  │ ← Pipelines do the work
│Pipeline│ │ Signals  │
└───┬────┘ └────┬─────┘
    │           │
    └─────┬─────┘
          ▼
┌─────────────────┐
│  ALL PLATFORMS  │ ← Discord, Telegram, Slack
│  (Auto-post)    │
└─────────────────┘
```

---

**Built by you. Run by Victor. Owned by the swarm.**

*Last updated: 2026-07-11*
